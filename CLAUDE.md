# Daily Blog Agent

구독 네이버 블로그 채널의 전날 게시글을 수집하고, 본문을 추출하여 요약한 뒤 뉴스레터로 텔레그램에 전달하는 자동화 에이전트.

## 대상 블로그

config.py의 BLOGS 리스트 참조. 현재 20개 채널:
sungdory, jelkajelka, onion_asset, hodolry, bigpicture-storage, freebutdeep2, crush212121, travelingcompanion, luy1978, tosoha1, ranto28, richyun0108, limsk1212, mlyuri, firetiger580, hardark, tmdejr1267, stockinvcowcow, studying-investor, a463508

## 일일 워크플로우

### Step 1: 블로그 글 수집
```bash
python fetch_blogs.py
```
- config.py에 등록된 블로그의 네이버 RSS 피드를 조회
- 전날(KST 기준) 게시된 글을 필터링
- 결과: `output/blogs_YYYYMMDD.json`
- **글이 0개인 경우**: 텔레그램으로 알림 후 종료
```bash
python telegram_send.py --message "📝 Daily Blog Agent: 어제 게시된 블로그 글이 없습니다."
```

### Step 2: 본문 추출
```bash
python fetch_content.py
```
- 수집된 글의 본문 텍스트를 추출 (PostView API로 iframe 우회)
- 전체 본문을 추출하며 글자 수 제한 없음
- 본문 추출 실패한 글은 건너뛰고 계속 진행
- 결과: `output/contents_YYYYMMDD.json`
- **모든 본문 추출 실패 시**: 텔레그램 알림 후 종료
```bash
python telegram_send.py --message "📝 Daily Blog Agent: 모든 글의 본문 추출에 실패했습니다."
```

### Step 3: 블로그 요약 (Claude Code 내부 LLM 활용)
- `output/contents_YYYYMMDD.json` 파일을 읽는다
- 본문이 있는 각 글에 대해 2~3줄 한국어 요약을 작성한다
- 블로그별로 그룹화하여 텍스트 파일로 저장한다
- 결과를 `output/newsletter_YYYYMMDD.txt` 파일로 저장한다

**newsletter 텍스트 형식:**
```
📝 블로그 데일리 브리핑 (YYYY-MM-DD)

[블로그명1]

1. 글 제목
요약 내용 2~3줄. 핵심 내용을 간결하게 전달.
https://blog.naver.com/...

2. 글 제목
요약 내용 2~3줄.
https://blog.naver.com/...

[블로그명2]

1. 글 제목
요약 내용 2~3줄.
https://blog.naver.com/...
```

**요약 작성 규칙:**
- 각 글의 핵심 주장, 결론, 핵심 데이터를 포함
- 한국어로 작성
- 블로그별로 그룹화 (블로그명은 RSS에서 가져온 실제 블로그 이름 사용)
- 글 번호는 각 블로그 섹션 내에서 1부터 시작
- 원문 링크는 각 요약 바로 아래에 배치

### Step 4: HTML 뉴스레터 생성
```bash
python html_generator.py
```
- 요약 텍스트를 HTML 뉴스레터로 변환
- 블로그별 섹션, 글별 카드, 원문 링크 버튼 포함
- 결과: `output/BlogDigest_YYMMDD.html`

### Step 5: Telegram 전송
HTML 뉴스레터 파일을 텔레그램으로 전송:
```bash
python telegram_send.py --document output/BlogDigest_YYMMDD.html "📝 블로그 데일리 브리핑"
```

### Step 6: GitHub Pages 배포
```bash
python publish_ghpages.py
```
- `output/BlogDigest_YYMMDD.html` 파일을 gh-pages 브랜치에 push
- 날짜별 폴더 구조로 정리 (`YYYY/MM/DD/`)
- 실행 결과로 GitHub Pages URL이 JSON으로 출력됨
- URL 형식: `https://oooohhhhiiii.github.io/daily-blog-agent/YYYY/MM/DD/BlogDigest_YYMMDD.html`

### Step 7: Notion 아카이브 저장
- `.env` 파일에서 `NOTION_PAGE_ID`를 읽는다
- Step 6의 JSON 출력에서 URL을 파싱한다
- Notion MCP의 `notion-create-pages` 도구를 사용하여 NOTION_PAGE_ID 페이지 아래에 서브 페이지 생성:
  - **페이지 제목**: "YYYY-MM-DD Blog Digest" (전날 날짜 기준)
  - **페이지 내용**: 블로그 다이제스트 링크

#### Notion 페이지 내용 형식:
```
- [블로그 데일리 브리핑](GitHub Pages URL)
```

#### 주의사항:
- GitHub Pages 배포 실패 시 오류를 콘솔에 출력하되 Notion 저장은 건너뛴다
- Notion 저장 실패 시 오류를 콘솔에 출력하되 전체 워크플로우는 중단하지 않음
- **일회성 설정 필요**: GitHub repo Settings > Pages > Source에서 `gh-pages` 브랜치, `/ (root)` 선택하여 활성화

## 주의사항
- 모든 스크립트는 프로젝트 루트 디렉토리에서 실행
- 뉴스레터 요약은 한국어로 작성
- 본문 추출 실패한 글은 건너뛰고 로그에 기록
- 오류 발생 시 텔레그램으로 알림 보내고 다음 단계로 진행
- 글이 0개인 날은 Step 1 이후 파이프라인 종료
