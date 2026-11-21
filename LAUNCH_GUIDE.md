# 20분 무료 런칭 & 주 1회 10분 무인 운영 가이드

## 1단계: 무료 공공 오픈 API 키 2개 발급 (최초 1회, 약 10분)
1. **금융감독원 「금융상품한눈에」**: [finlife.fss.or.kr](https://finlife.fss.or.kr) 회원가입 → 우측 상단 `[오픈 API]` → 인증키 즉시 발급 → `FINLIFE_API_KEY`
2. **공공데이터포털 「보조금24」**: [data.go.kr](https://www.data.go.kr) 로그인 → *"행정안전부_대한민국 공공서비스(혜택) 정보"* 검색 → 활용신청 → `DATA_GO_KR_API_KEY`

*(API 키가 없어도 내장 시드 데이터로 100% 정상 빌드되므로 먼저 배포부터 끝내고 나중에 키를 넣어도 됩니다.)*

## 2단계: GitHub Pages 또는 Cloudflare Pages 무료 무인 배포 (약 10분)
1. 이 폴더를 새 GitHub 저장소에 Push 합니다.
2. GitHub 저장소 `Settings → Pages → Source`를 **GitHub Actions**로 선택합니다.
3. `Settings → Secrets and variables → Actions`에 아래 값을 등록합니다:
   - **Variables**: `SITE_URL`(내 도메인 또는 `https://<아이디>.github.io/<저장소명>`), `SITE_NAME`, `ENABLE_INDEXNOW=true`
   - **Secrets**: `FINLIFE_API_KEY`, `DATA_GO_KR_API_KEY`, `ADSENSE_CLIENT_ID`(승인 후), `AFFILIATE_DEPOSIT_URL`, `AFFILIATE_LOAN_URL`, `AFFILIATE_SUBSIDY_URL`, `INDEXNOW_KEY`
4. `Actions` 탭에서 **Daily pSEO Data Sync & Deploy**를 1회 수동 실행(`Run workflow`)하면 이후 **매일 새벽 04:00 KST에 완전 무인 자동 갱신·배포**됩니다.

## 3단계: 검색엔진 등록 및 수익화 연결 (최초 1회)
1. **Google Search Console** & **네이버 서치어드바이저**에 사이트 등록 후 `sitemap.xml` 제출
2. 배포 후 2~4주간 색인이 쌓이면 **Google AdSense** 신청 (`privacy.html`, `disclaimer.html`, `ads.txt` 자동 구비 완료)
3. 애드센스 승인 후 `ADSENSE_CLIENT_ID`를 GitHub Secrets에 입력하면 전 페이지 광고 슬롯 + `ads.txt`가 자동 활성화됩니다.
4. **제휴(CPA) 연결**: 디비센스·텐핑·금융비교 제휴 링크를 `AFFILIATE_*_URL`에 등록하면 모든 계산기 결과 하단에 표시광고법 고지와 함께 자동 노출됩니다.

## 4단계: 주 1회 10분 운영 루틴 (하루 평균 2분 미만)
- **월요일 오전 (5분)**: Google Search Console에서 노출·클릭이 급상승하는 롱테일 키워드 확인
- **월요일 오전 (5분)**: `pseo_engine/generator.py`의 금액·기간·지역 배열에 수요 높은 조합 2~3개 추가 후 Push → GitHub Actions가 자동으로 수십 페이지 확장 배포
