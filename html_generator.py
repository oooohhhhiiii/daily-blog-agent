"""요약 텍스트를 HTML 뉴스레터로 변환"""

import re
import sys
import html
from pathlib import Path

OUTPUT_DIR = Path("output")


def parse_newsletter_text(text):
    """newsletter_YYYYMMDD.txt 파싱 → 구조화된 데이터"""
    lines = text.strip().split("\n")

    # 첫 줄에서 날짜 추출
    date_str = ""
    date_match = re.search(r"\((\d{4}-\d{2}-\d{2})\)", lines[0] if lines else "")
    if date_match:
        date_str = date_match.group(1)

    blogs = []
    current_blog = None
    current_article = None

    for line in lines:
        line = line.rstrip()

        # 블로그 섹션 헤더: [블로그명]
        blog_match = re.match(r"^\[(.+)\]$", line)
        if blog_match:
            if current_article and current_blog:
                current_blog["articles"].append(current_article)
                current_article = None
            if current_blog:
                blogs.append(current_blog)
            current_blog = {"name": blog_match.group(1), "articles": []}
            continue

        # 글 번호: "1. 제목" 또는 "2. 제목"
        article_match = re.match(r"^(\d+)\.\s+(.+)$", line)
        if article_match:
            if current_article and current_blog:
                current_blog["articles"].append(current_article)
            current_article = {
                "title": article_match.group(2),
                "summary": "",
                "link": "",
            }
            continue

        # 링크
        link_match = re.match(r"^https?://", line)
        if link_match and current_article:
            current_article["link"] = line.strip()
            continue

        # 요약 텍스트
        if current_article and line.strip():
            if current_article["summary"]:
                current_article["summary"] += "\n" + line.strip()
            else:
                current_article["summary"] = line.strip()

    # 마지막 항목 추가
    if current_article and current_blog:
        current_blog["articles"].append(current_article)
    if current_blog:
        blogs.append(current_blog)

    return date_str, blogs


def render_html(date_str, blogs):
    """구조화된 데이터를 HTML로 렌더링"""
    total_articles = sum(len(b["articles"]) for b in blogs)
    title = f"블로그 데일리 브리핑 ({date_str})"
    title_html = html.escape(title)

    blog_sections = []
    article_num = 0

    for blog in blogs:
        blog_name_html = html.escape(blog["name"])

        article_blocks = []
        for article in blog["articles"]:
            article_num += 1
            a_title = html.escape(article["title"])
            a_summary = html.escape(article["summary"]).replace("\n", "<br>")
            a_link = html.escape(article["link"])

            link_html = ""
            if a_link:
                link_html = f'\n        <a href="{a_link}" style="display:inline-block; margin-top:8px; font-size:13px; color:#4a90d9; text-decoration:none;">&#128279; 원문 보기</a>'

            block = f"""      <div style="border-bottom:1px solid #f0f0f0; padding:14px 0;">
        <h3 style="margin:0 0 6px; font-size:15px; color:#1a1a2e; line-height:1.4;">{article_num}. {a_title}</h3>
        <p style="margin:0; font-size:14px; color:#444; line-height:1.7;">{a_summary}</p>{link_html}
      </div>"""
            article_blocks.append(block)

        articles_html = "\n".join(article_blocks)
        section = f"""    <div style="margin-bottom:8px;">
      <div style="background:#f8f9fa; padding:10px 24px; border-left:4px solid #2ecc71;">
        <h2 style="margin:0; font-size:16px; color:#1a1a2e;">&#128221; {blog_name_html}</h2>
      </div>
      <div style="padding:0 24px;">
{articles_html}
      </div>
    </div>"""
        blog_sections.append(section)

    sections_html = "\n".join(blog_sections)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_html}</title>
</head>
<body style="margin:0; padding:16px; background:#f5f5f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans KR',sans-serif;">
  <div style="max-width:640px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
    <div style="background:#1a1a2e; color:#fff; padding:20px 24px;">
      <h1 style="margin:0; font-size:20px;">&#128221; {title_html}</h1>
      <p style="margin:6px 0 0; font-size:14px; color:rgba(255,255,255,0.7);">{len(blogs)}개 블로그 &middot; {total_articles}개 글 요약</p>
    </div>
{sections_html}
    <div style="padding:12px 24px; text-align:center; font-size:12px; color:#999; border-top:1px solid #eee;">
      Daily Blog Agent
    </div>
  </div>
</body>
</html>"""


def find_latest_newsletter_file():
    """가장 최근 newsletter_*.txt 파일 반환"""
    files = sorted(OUTPUT_DIR.glob("newsletter_*.txt"), reverse=True)
    return files[0] if files else None


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--input":
        input_path = Path(sys.argv[2])
    else:
        input_path = find_latest_newsletter_file()

    if not input_path or not input_path.exists():
        print("newsletter_*.txt 파일을 찾을 수 없습니다.")
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    date_str, blogs = parse_newsletter_text(text)

    if not blogs:
        print("파싱된 블로그 데이터가 없습니다.")
        sys.exit(1)

    total_articles = sum(len(b["articles"]) for b in blogs)
    html_content = render_html(date_str, blogs)

    date_compact = date_str.replace("-", "")[2:]  # YYMMDD
    output_path = OUTPUT_DIR / f"BlogDigest_{date_compact}.html"
    output_path.write_text(html_content, encoding="utf-8")
    print(f"HTML 뉴스레터 생성 완료: {output_path} ({len(blogs)}개 블로그, {total_articles}개 글)")


if __name__ == "__main__":
    main()
