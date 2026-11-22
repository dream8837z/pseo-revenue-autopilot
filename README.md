# 핀툴랩(FinToolLab) — 6대 공공데이터 · 금융 · 세금 · 부동산 · 웹 유틸리티 505종 자동화 허브

**사람 상대 영업·CS 0%, 호스팅 비용 0원, 매일 무인 자동 갱신·배포**를 목표로 설계된 프로그래매틱 SEO(pSEO) 수익화 파이프라인입니다.

## 왜 이 니치인가?
1. **고단가 애드센스 + 고단가 제휴(CPA) 이중 수익**: 금융(예금·적금·주담대·전세대출)은 한국 애드센스 최상위 CPC 구간이며, 보조금24는 대량 검색 트래픽 유입 엔진 역할을 합니다.
2. **구글 스팸(Thin Content) 페널티 구조적 회피**: 단순 텍스트 치환이 아니라 모든 페이지에 **실시간 인터랙티브 JS 계산기/자가진단기 + 공식 공공 API 비교표 + JSON-LD(`WebApplication`·`FAQPage`) + YMYL 출처 고지**가 내장됩니다.
3. **100% 무료 공식 데이터 + 무료 호스팅**: 금융감독원 「금융상품한눈에」 API + 행정안전부 「보조금24」 API + GitHub Actions & GitHub Pages(또는 Cloudflare Pages) 무료 자동 배포.

## 즉시 실행 (API 키 없이 3초 만에 체험)

```bash
cd /home/dream8837/.gemini/antigravity/scratch/pseo-revenue-autopilot

# 1. 전체 파이프라인 실행 (데이터 수집 -> 63개 SEO 페이지 빌드 -> SEO 품질 감사)
python3 -m pseo_engine run

# 2. 빌드된 웹앱 로컬 미리보기 (브라우저에서 http://127.0.0.1:8080/index.html 열기)
python3 -m pseo_engine serve --port 8080

# 3. 트래픽별 예상 월수익 시뮬레이션 확인
python3 -m pseo_engine revenue-sim

# 4. 단위·E2E 테스트 실행
python3 -m unittest discover -s tests -v
```

## 생성되는 페이지 구성 (기본 63페이지, 매트릭스 확장 시 수백~수천 페이지)
- **정기예금 계산기** (`dist/deposit/`): 금액(1천만/3천만/5천만/1억) × 기간(6/12/24개월) = 12페이지
- **적금 계산기** (`dist/saving/`): 월납입(30만/50만/100만/200만) × 기간(12/24/36개월) = 12페이지
- **주담대·전세대출 계산기** (`dist/loan/`): 대출금 × 기간 조합 = 16페이지
- **보조금24 지역·대상 진단기** (`dist/subsidy/`): 전국/서울/경기/인천/부산 × 청년/신혼부부·출산/소상공인/주거·생활 = 20페이지
- **필수 허브 및 애드센스 심사 페이지**: `index.html`, `privacy.html`, `disclaimer.html`
- **SEO 기술 파일**: `sitemap.xml`, `robots.txt`, `ads.txt`, `rss.xml`, IndexNow 키 파일

실전 배포 및 주 1회 10분 운영 방법은 [LAUNCH_GUIDE.md](LAUNCH_GUIDE.md)를 참고하세요.
