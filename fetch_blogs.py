"""PostTitleListAsync API로 네이버 블로그 전날 게시글 수집"""

import json
import re
import sys
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote

from config import BLOGS, RSS_URL_TEMPLATE, REQUEST_DELAY, HEADERS

OUTPUT_DIR = Path("output")
KST = timezone(timedelta(hours=9))

POST_LIST_URL = (
    "https://blog.naver.com/PostTitleListAsync.naver"
    "?blogId={blog_id}&viewdate={date}&currentPage={page}&countPerPage=30"
)


def get_yesterday_kst():
    """KST 기준 어제 날짜 반환"""
    now_kst = datetime.now(KST)
    yesterday = now_kst - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def fetch_blog_name(blog_id):
    """RSS 피드에서 블로그 실제 이름 추출"""
    url = RSS_URL_TEMPLATE.format(blog_id=blog_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is not None:
            title_el = channel.find("title")
            if title_el is not None and title_el.text:
                return title_el.text.strip()
    except Exception:
        pass
    return blog_id


def parse_post_list_response(text):
    """PostTitleListAsync 응답 JSON 파싱 (pagingHtml 필드의 잘못된 이스케이프 우회)"""
    idx = text.find(',"pagingHtml"')
    if idx < 0:
        idx = text.find('"pagingHtml"')
        if idx > 0:
            idx = text.rfind(',', 0, idx)
    if idx > 0:
        text = text[:idx] + '}'
    return json.loads(text)


def is_target_date(add_date, target_date_str):
    """addDate 값이 수집 대상 날짜인지 판별.

    addDate 형식:
    - 상대시간: "X분 전", "X시간 전" (당일 = viewdate 날짜)
    - 절대날짜: "2026. 3. 31." (viewdate 이전 날짜들)

    target_date_str: "2026-03-31" 형식
    """
    add_date = add_date.strip()

    # 상대시간 ("X분 전", "X시간 전") → viewdate 당일
    if re.search(r'[분시간].*전', add_date):
        return True

    # 절대날짜 "YYYY. M. D." 파싱
    match = re.match(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?', add_date)
    if match:
        y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
        date_str = f"{y}-{m:02d}-{d:02d}"
        return date_str == target_date_str

    return False


def is_before_target_date(add_date, target_date_str):
    """addDate가 수집 대상 날짜보다 이전인지 판별 (페이지네이션 중단 조건)."""
    add_date = add_date.strip()
    match = re.match(r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?', add_date)
    if match:
        y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
        date_str = f"{y}-{m:02d}-{d:02d}"
        return date_str < target_date_str
    return False


def fetch_blog_posts(blog_id, target_date, target_date_compact):
    """PostTitleListAsync API로 특정 날짜의 블로그 글 목록 수집"""
    all_posts = []
    page = 1

    while True:
        url = POST_LIST_URL.format(blog_id=blog_id, date=target_date_compact, page=page)
        req_headers = {**HEADERS, "Referer": f"https://blog.naver.com/{blog_id}"}

        try:
            resp = requests.get(url, headers=req_headers, timeout=15)
            resp.raise_for_status()
            data = parse_post_list_response(resp.text)
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"  [{blog_id}] API 요청/파싱 실패 (page {page}): {e}")
            break

        post_list = data.get("postList", [])
        if not post_list:
            break

        found_older = False
        for p in post_list:
            add_date = p.get("addDate", "")

            if is_target_date(add_date, target_date):
                title = unquote(p.get("title", "").replace("+", " "))
                log_no = p.get("logNo", "")
                link = f"https://blog.naver.com/{blog_id}/{log_no}"
                all_posts.append({
                    "title": title,
                    "link": link,
                    "logNo": log_no,
                })
            elif is_before_target_date(add_date, target_date):
                found_older = True
                break

        # 대상 날짜보다 이전 글이 나왔으면 더 이상 페이지 탐색 불필요
        if found_older:
            break

        # 30개 미만이면 마지막 페이지
        if len(post_list) < 30:
            break

        page += 1
        time.sleep(0.3)

    return all_posts


def main():
    yesterday = get_yesterday_kst()
    date_compact = yesterday.replace("-", "")
    print(f"수집 대상 날짜: {yesterday}")
    print(f"블로그 {len(BLOGS)}개 채널 스캔 시작...\n")

    all_posts = []
    blog_names = {}

    for blog_name, blog_id in BLOGS:
        print(f"[{blog_id}] 글 목록 확인 중...")
        posts = fetch_blog_posts(blog_id, yesterday, date_compact)

        if posts:
            # 블로그 실제 이름 가져오기 (글이 있는 블로그만)
            real_name = fetch_blog_name(blog_id)
            blog_names[blog_id] = real_name
            for p in posts:
                all_posts.append({
                    "blog_name": real_name,
                    "blog_id": blog_id,
                    "title": p["title"],
                    "link": p["link"],
                    "published": yesterday,
                })
            print(f"  → {len(posts)}개 글 발견")
        else:
            print(f"  → 전일 게시글 없음")

        time.sleep(REQUEST_DELAY)

    # 결과 저장
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"blogs_{date_compact}.json"

    result = {
        "date": yesterday,
        "crawled_at": datetime.now(KST).isoformat(),
        "channels_checked": len(BLOGS),
        "total": len(all_posts),
        "posts": all_posts,
    }

    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n총 {len(all_posts)}개 글 수집 → {output_path}")

    if len(all_posts) == 0:
        print("어제 게시된 글이 없습니다.")
        sys.exit(0)


if __name__ == "__main__":
    main()
