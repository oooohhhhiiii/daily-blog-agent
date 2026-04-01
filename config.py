"""Daily Blog Agent 설정"""

# 구독 블로그 목록: (블로그명, blog_id)
BLOGS = [
    ("sungdory", "sungdory"),
    ("jelkajelka", "jelkajelka"),
    ("onion_asset", "onion_asset"),
    ("hodolry", "hodolry"),
    ("bigpicture-storage", "bigpicture-storage"),
    ("freebutdeep2", "freebutdeep2"),
    ("crush212121", "crush212121"),
    ("travelingcompanion", "travelingcompanion"),
    ("luy1978", "luy1978"),
    ("tosoha1", "tosoha1"),
    ("ranto28", "ranto28"),
    ("richyun0108", "richyun0108"),
    ("limsk1212", "limsk1212"),
    ("mlyuri", "mlyuri"),
    ("firetiger580", "firetiger580"),
    ("hardark", "hardark"),
    ("tmdejr1267", "tmdejr1267"),
    ("stockinvcowcow", "stockinvcowcow"),
    ("studying-investor", "studying-investor"),
    ("a463508", "a463508"),
]

# RSS 피드 URL 템플릿
RSS_URL_TEMPLATE = "https://rss.blog.naver.com/{blog_id}.xml"

# 요청 설정
REQUEST_DELAY = 1.0  # 요청 간 딜레이 (초)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# GitHub Pages
GHPAGES_BASE_URL = "https://oooohhhhiiii.github.io/daily-blog-agent"
