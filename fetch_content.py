"""블로그 게시글 본문 추출"""

import json
import re
import sys
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

from config import REQUEST_DELAY, HEADERS

OUTPUT_DIR = Path("output")


def extract_post_content(url):
    """네이버 블로그 게시글 본문 텍스트 추출"""
    # 네이버 블로그 URL에서 blog_id와 post_no 추출
    # 형식: https://blog.naver.com/{blog_id}/{post_no}
    match = re.search(r"blog\.naver\.com/([^/]+)/(\d+)", url)
    if not match:
        return None, "URL 파싱 실패"

    blog_id = match.group(1)
    post_no = match.group(2)

    # PostView URL로 직접 접근 (iframe 우회)
    postview_url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={post_no}"

    try:
        resp = requests.get(postview_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 본문 컨테이너 탐색 (여러 셀렉터 시도)
        selectors = [
            "div.se-main-container",       # 스마트에디터 3 (최신)
            "div#postViewArea",            # 구버전 에디터
            "div.se_component_wrap",       # 스마트에디터 2
            "div.__se_component_area",     # 또 다른 변형
        ]

        content_div = None
        for selector in selectors:
            content_div = soup.select_one(selector)
            if content_div:
                break

        if not content_div:
            return None, "본문 컨테이너를 찾을 수 없음"

        # 텍스트 추출
        # 불필요한 요소 제거
        for tag in content_div.find_all(["script", "style", "iframe"]):
            tag.decompose()

        text = content_div.get_text(separator="\n", strip=True)

        # 빈 줄 정리
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)

        if not text:
            return None, "본문 텍스트 비어있음"

        return text, None

    except requests.RequestException as e:
        return None, f"요청 실패: {e}"


def find_latest_blogs_file():
    """가장 최근 blogs_*.json 파일 반환"""
    files = sorted(OUTPUT_DIR.glob("blogs_*.json"), reverse=True)
    return files[0] if files else None


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--input":
        input_path = Path(sys.argv[2])
    else:
        input_path = find_latest_blogs_file()

    if not input_path or not input_path.exists():
        print("blogs_*.json 파일을 찾을 수 없습니다.")
        sys.exit(1)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    posts = data.get("posts", [])
    date_str = data.get("date", "")

    print(f"본문 추출 시작: {len(posts)}개 글")

    results = []
    success_count = 0

    for i, post in enumerate(posts, 1):
        print(f"[{i}/{len(posts)}] {post['blog_id']} - {post['title'][:40]}...")

        content, error = extract_post_content(post["link"])

        results.append({
            "blog_name": post["blog_name"],
            "blog_id": post["blog_id"],
            "title": post["title"],
            "link": post["link"],
            "published": post["published"],
            "content": content,
            "error": error,
        })

        if content:
            success_count += 1
            print(f"  → {len(content)}자 추출 완료")
        else:
            print(f"  → 실패: {error}")

        if i < len(posts):
            time.sleep(REQUEST_DELAY)

    # 결과 저장
    date_compact = date_str.replace("-", "")
    output_path = OUTPUT_DIR / f"contents_{date_compact}.json"

    output_data = {
        "date": date_str,
        "total": len(results),
        "success": success_count,
        "posts": results,
    }

    output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n본문 추출 완료: {success_count}/{len(results)}개 성공 → {output_path}")

    if success_count == 0:
        print("본문을 추출한 글이 없습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
