# 집값추적기 

> 국토교통부 실거래가 공공 API 기반 전국 아파트 매매 탐색·분석 도구

---

## 📊 그래프 분석 상세 가이드

> 집값추적기의 모든 시각화 그래프에 대한 분석 방법과 용어 해설

### 그래프 개요

집값추적기는 **국토교통부 실거래가 공공 API** 기반의 전국 아파트 매매 데이터를 다차원적으로 분석합니다. 총 4개의 탭에서 15종류의 그래프를 제공하며, 각 그래프는 특정 가설 검증이나 시장 인사이트 제공을 목적으로 설계되었습니다.

---

## 스택

| 레이어     | 기술                                            |
| ---------- | ----------------------------------------------- |
| 백엔드     | Python 3.11 · FastAPI · SQLite                  |
| 프론트엔드 | Vanilla JS · Chart.js 4 · Plotly.js 2           |
| 데이터     | 국토교통부 실거래가 공공 API (data.go.kr) · XML |
| 배포       | Docker · Render · Railway                       |

## 디렉토리 구조

```
.
├── frontend/
│   ├── index.html        # 메인 탐색 (필터·카드·단지 상세)
│   └── analysis.html     # 가설 분석 대시보드
├── backend/
│   ├── main.py           # FastAPI 라우터 + 백그라운드 수집
│   ├── crawler.py        # API 호출 · XML 파싱 · 전처리 · 샘플 생성
│   ├── database.py       # SQLite 초기화 · 쿼리
│   ├── regions.py        # 전국 지역코드 · 광역시도 그룹
│   └── config.py         # .env 로드 · API 키 설정
├── Dockerfile · docker-compose.yml · run.sh
└── deploy/               # Render · Railway · nginx 설정
```
## 주요 API

| 메서드 | 경로                      | 설명                             |
| ------ | ------------------------- | -------------------------------- |
| GET    | `/api/status`             | 수집 진행률 · 총 건수            |
| GET    | `/api/data`               | 필터·정렬·페이지네이션 거래 목록 |
| GET    | `/api/complex/{apt_name}` | 단지 거래 이력 + 통계            |
| GET    | `/api/affordable`         | 예산 범위 내 매물                |
| POST   | `/api/crawl/auto`         | 백그라운드 수집 시작             |
| POST   | `/api/key/update`         | API 키 갱신 + 재수집             |



**📋 분석된 그래프 종류**

| 탭 | 그래프 종류 | 목적 |
|----|------------|------|
| **가설 검증** | 예산별 매물 수 분포 | 예산 민감도 분석 |
| | 건축연도별 평균가 | 신축 프리미엄 파악 |
| | 서울 vs 지방 면적대별 비교 | 지역별 수급 비교 |
| | 가설 근거 차트 (H1/H2/H3) | 3대 가설 검증 |
| **지역 트렌드** | 월별 평균가 추이 | 시계열 트렌드 |
| | 면적 vs 평당가 산점도 | 지역별 가격 구조 |
| | 지역별 누적 분위 바 | 시장 규모와 성격 |
| **전체 데이터** | 계층형 필터 시스템 | 개별 매물 탐색 |
| **심화 그래프** | 트리맵 | 지역별 거래 비중 |
| | 바이올린 플롯 | 가격 분포 |
| | 선버스트 차트 | 계층적 데이터 |
| | 지역별 박스플롯 | 통계적 분포 |
| | 건축연도별 평당가 | 신축 프리미엄 |

**🎯 핵심 분석 철학**
- **가설 기반 분석**: 3대 핵심 가설(H1, H2, H3)을 데이터로 검증
- **지역 비교 중심**: 서울 vs 지방, 광역시도 간 가격 구조 비교
- **시계열 트렌드**: 월별/연식별 가격 변화 추이 파악
- **분포 이해**: 가격/면적/연식별 데이터 분포와 이상치 패턴 분석

**📈 3대 핵심 가설**

- **H1: 예산 비선형 증가** - "예산을 올릴수록 매물 수는 예산 증가율보다 빠르게 늘어난다"
- **H2: 신축 프리미엄** - "신축 아파트는 구축 대비 10% 이상 높은 거래가를 형성한다"  
- **H3: 지역별 면적 배율** - "동일 예산 기준, 지방 5대광역시의 구매 가능 면적이 서울의 1.5배 이상"

**🔍 핵심 용어 사전**

| 용어 | 의미 | 활용 |
|------|------|------|
| **평당가** | 가격 ÷ (전용면적 ÷ 3.3) | 효율성 지표, 지역별 비교 |
| **IQR** | 제3사분위수 - 제1사분위수 | 이상치 탐지, 데이터 퍼짐 정도 |
| **신축 프리미엄** | 신축의 추가적 가치 | 연식별 가격 차이 분석 |
| **예산 민감도** | 예산 변화에 따른 선택지 변화 | 시장 유연성 측정 |
| **층화 샘플링** | 그룹별 균등 표본 추출 | 소수 지역 가시성 확보 |

**📊 실전 활용 가이드**

**투자자를 위한 활용법**
- **가성비 매물 발굴**: 평당가 낮은순 정렬 + 예산 필터
- **신축 프리미엄 분석**: 신축순 정렬 + 건축연도별 차트
- **지역 선정 전략**: 지역 필터 + 평당가 분석

**실수요자를 위한 활용법**
- **예산 내 최적 면적**: 예산 필터 + 면적 넓은순 정렬
- **시장 타이밍**: 월별 추이 차트 관찰
- **지역별 가격 비교**: 산점도에서 상대적 위치 파악

**⚠️ 데이터 품질과 한계**

- **데이터 소스**: 국토교통부 실거래가 공공 API
- **수집 범위**: 전국 아파트 매매 실거래 (최근 3개월)
- **전처리**: IQR 기반 이상치 제거, 결측값 처리
- **분석적 한계**: 표본 편향, 시차 효과, 비표준 요인 미반영

> 📖 **더 상세한 분석**: [GRAPH_ANALYSIS.md](./GRAPH_ANALYSIS.md)에서 모든 그래프의 상세 분석 방법과 용어 해설을 확인하세요.

> 🔧 **구현 코드**: [GRAPH_IMPLEMENTATION_CODE.md](./GRAPH_IMPLEMENTATION_CODE.md)에서 모든 그래프의 상세 구현 코드를 확인하세요.

---

## 빠른 시작

```bash
cp .env.example .env
# MOLIT_KEY=인증키 입력 (없으면 샘플 데이터로 동작)
chmod +x run.sh && ./run.sh
# → http://localhost:8000
```

```bash
docker-compose up -d   # Docker
```

**API 키 발급**: [data.go.kr](https://www.data.go.kr) → 「국토교통부 아파트매매 실거래 상세자료」 활용신청 → 일반 인증키 복사 → `.env`에 `MOLIT_KEY=키` 입력
또는 앱 내 ⚙️ 버튼으로 런타임 주입 가능.

---

## 화면 구성

### 메인 탐색 (`index.html`)

- **필터**: 예산(억 단위), 전용면적, 지역(광역시도·시군구)
- **카드 목록**: 서버사이드 필터·정렬·페이지네이션
- **단지 상세 패널**: 거래 이력 추이 차트, 지역 평당가 산점도, 매물 체크리스트, 유사 매물

### 가설 분석 (`analysis.html`)

| 탭          | 내용                                           |
| ----------- | ---------------------------------------------- |
| 가설 검증   | H1·H2·H3 채택/기각 판정 + 근거 차트 4종        |
| 지역 트렌드 | 월별 평균가 추이 · 산점도 · 누적 분위 바       |
| 전체 데이터 | 계층형 필터 + 정렬 가능 테이블                 |
| 심화 그래프 | Plotly 트리맵 · 선버스트 · 바이올린 · 박스플롯 |

---

## 주제 및 가설 선정 이유

### 왜 아파트 실거래가인가

부동산 투자·실거주 의사결정에서 가장 자주 제기되는 질문은 세 가지다.

1. **예산을 조금 늘리면 선택지가 얼마나 늘어나는가** — 예산 민감도
2. **신축을 사야 하는가, 구축을 사야 하는가** — 건축 연식 프리미엄
3. **지방에서 같은 돈으로 훨씬 넓은 집을 살 수 있는가** — 지역 간 면적 효율

이 세 가지는 언론·커뮤니티에서 반복 언급되지만 정량적 근거 없이 통용된다.
공공 데이터로 직접 검증 가능하고, 결과가 사용자 의사결정에 즉각적인 실용 가치를 갖기 때문에 가설로 채택했다.

### 3가지 투자 가설

1. H1 - 예산 비선형 증가: 예산 구간을 80%, 100%, 120%로 나누어 각 구간별 매물 수 증가율($\Delta$) 계산. 증가율이 예산 증가폭(20%)을 상회할 경우 비선형적 선택지 확장으로 판정.
2. H2 - 신축 프리미엄: 건축연도 상위 25%(신축)와 하위 25%(구축)의 평균 거래가를 비교. 가격 차이가 10%를 초과할 경우 신축 프리미엄 가설 채택.
3. H3 - 지역별 면적 배율: 동일 예산 기준, 서울 vs 지방 5대 광역시의 평균 전용면적을 비교. 지방의 구매 가능 면적이 서울의 1.5배 이상일 경우 가설 채택.

---

## 시각화 설계

### 사용 라이브러리

| 용도                                 | 라이브러리  | 이유                                      |
| ------------------------------------ | ----------- | ----------------------------------------- |
| 기본 차트 (막대·꺾은선·산점도)       | Chart.js 4  | 경량, CDN 즉시 사용, tooltip 커스텀 용이  |
| 고급 차트 (트리맵·바이올린·선버스트) | Plotly.js 2 | 계층형·통계 시각화 내장, interactive zoom |

🛠 핵심 기술 스택 및 처리 로직

1. Backend: 성능 최적화 및 안정성
   비동기 병렬 크롤링 (crawler.py): ThreadPoolExecutor(max_workers=20)를 활용하여 전국 수십 개 지역의 실거래 데이터를 동시에 수집합니다.

점진적 DB 반영 (main.py): 전체 수집 완료를 기다리지 않고, 200건 단위로 SQLite에 즉시 저장하여 사용자에게 실시간 진행률과 부분 데이터를 제공합니다.

데이터 클리닝:

이상치 제거: 전용면적 1.0㎡ 이하/500㎡ 초과, 비현실적인 거래가(1천만 원 미만 등) 자동 필터링.

IQR 통계 필터링: 평당 가격(per_pyeong) 기준 상하위 3\*IQR 범위를 벗어나는 극단적 데이터 제거로 통계 신뢰도 확보.


실거래 데이터 특성상 발생하는 '직거래', '특수관계인 거래' 등 시장가격을 왜곡하는 이상치를 제거하기 위해 IQR(Interquartile Range) 방식을 채택했습니다.

$$IQR = Q_3 - Q_1$$

$$Lower\ Bound = Q_1 - 3 \times IQR$$

$$Upper\ Bound = Q_3 + 3 \times IQR$$

일반적인 $1.5 \times IQR$보다 보수적인 $3 \times IQR$을 적용하여, 유의미한 고가/저가 거래는 유지하면서 극단적인 데이터 오류만 정밀하게 필터링했습니다.

⚡ 성능 최적화: 병렬 크롤링 성과

Before: 전국 데이터 수집 시 약 120초 소요 (Blocking 발생)

After: ThreadPoolExecutor (Max Workers 15) 적용 및 점진적 DB 반영 루틴 도입으로 최초 응답 속도 1초 미만, 전체 수집 시간 15초 내외로 87.5% 단축.


2. Frontend: 인터랙티브 분석 환경
   캔버스 관리 및 메모리 최적화: Chart.js 인스턴스 생성 전 기존 차트를 파괴(destroy())하여 캔버스 재사용 에러 및 메모리 누수를 방지합니다.

다차원 시각화:

Plotly.js: 지역별 거래 비중을 보여주는 Treemap, 가격 분포를 보여주는 Violin Chart, 드릴다운이 가능한 Sunburst Chart 구현.

Chart.js: 가격 분포 바 차트, 연도별 가격 추이 라인 차트, 면적 vs 평당가 산점도(Scatter) 구현.

🗝 데이터 수집 및 보안
API 키 관리: 사용자가 브라우저 설정창에서 직접 data.go.kr 인증키를 입력하면 백엔드 세션에 반영되며, .env 파일을 통한 서버 측 키 관리도 지원합니다.

샘플 데이터 모드: API 키가 없는 사용자를 위해 실제 부동산 시장의 가격 분포(Gaussian Noise 적용)를 모사한 샘플 데이터 생성 엔진을 탑재하고 있습니다.

### 전역 옵션 객체

```javascript
// 기본 차트용 (탭 0·1)
const CO = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: 'var(--ink3)', font: { size: 8 } }, ... },
    y: { ticks: { color: 'var(--ink3)', font: { size: 9 } }, ... }
  }
};

// 심화 그래프 전용 — 폰트 크게, 대비 강화
const ADV_CO = {
  responsive: true, maintainAspectRatio: false,
  scales: {
    x: { ticks: { color: 'var(--ink2)', font: { size: 11 } }, ... },
    y: { ticks: { color: 'var(--ink2)', font: { size: 11 } }, ... }
  }
};
```

심화 그래프는 `CO` 대신 `ADV_CO`를 사용해 폰트 크기(8→11px),
색상 대비(`--ink3`→`--ink2`), 투명도(.35~.55 → .70~.88)를 모두 상향한다.

### Plotly 다크 레이아웃

```javascript
const darkLayout = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: { color: "#cbd5e1", family: "'DM Mono', monospace", size: 13 },
  margin: { l: 10, r: 10, t: 55, b: 10 },
};
```

`paper_bgcolor: 'transparent'`로 앱 배경과 통합하고, `font.size: 13`으로 기본 텍스트 크기를 보장한다.

---

## 핵심 문제와 해결

### 문제 1 — 수백 개 API 조합 직렬 처리 → 서버 블로킹

공공 API는 **지역코드 × 연월** 단위 XML이므로 전국 데이터 수집에 수백 번 호출 필요. 직렬 처리 시 수십 초 블로킹.

**관련 키워드**: `ThreadPoolExecutor` · `concurrent.futures` · `daemon thread` · `background collection`
**코드 내 키워드**: `_bg_collect` · `clear_and_insert` · `generate_sample_data` · `max_workers=15`

**해결**: 서버 시작 시 샘플 데이터 즉시 적재 후, 실거래 수집은 별도 daemon 스레드로 분리.
200건 누적마다 DB 반영 → 수집 중에도 UI가 점진적으로 채워진다.

```python
# startup: 샘플 데이터로 즉시 응답 가능하게 확보
clear_and_insert(generate_sample_data())
# 백그라운드 스레드에서 실 데이터 수집
threading.Thread(target=_bg_collect, args=(_current_key,), daemon=True).start()
```

**로직**: `_bg_collect` → `regions.py` 전국 지역코드 순회 → `fetch_molit()` 병렬 호출(max 15) →
200건 배치마다 `clear_and_insert(batch)` → `/api/status`의 `collected` 카운트 실시간 증가.

---

### 문제 2 — 한글·영문 XML 태그 혼재

API 버전에 따라 동일 필드의 태그명이 달라진다.

```xml
<!-- 영문 버전 -->                      <!-- 한글 버전 -->
<dealAmount>85,000</dealAmount>         <거래금액>85,000</거래금액>
<excluUseAr>84.99</excluUseAr>         <전용면적>84.99</전용면적>
```

**관련 키워드**: `xml.etree.ElementTree` · `findtext` · `or chaining` · `dual fallback`
**코드 내 키워드**: `g = lambda tag: item.findtext(tag)` · `raw_price` · `raw_area`

**해결**: `or` 체이닝으로 영문 태그를 먼저 시도, 없으면 한글 태그로 폴백.

```python
raw_price = g("dealAmount") or g("거래금액")
raw_area  = g("excluUseAr") or g("전용면적")
```

---

### 문제 3 — 이상치·결측값

면적 0㎡, 평당가 0원, 단지명 공백, 극단값 등 데이터 품질 문제.

**관련 키워드**: `IQR` · `interquartile range` · `outlier removal` · `data validation`
**코드 내 키워드**: `q1` · `q3` · `iqr` · `per_pyeong` · `_parse_xml`

**해결**: 파싱 단계에서 레코드 단위 필터 → 배치 전체 IQR×3 이상치 제거 2단계 처리.

```python
# 1단계: 레코드 단위 검증
if not apt_name: continue
if not (1.0 <= area <= 500.0): continue
if price < 1_000 or price > 1_000_000: continue

# 2단계: 배치 IQR 이상치 제거
q1, q3 = pps[len(pps)//4], pps[len(pps)*3//4]
iqr = q3 - q1
items = [i for i in items if q1 - 3*iqr <= i["per_pyeong"] <= q3 + 3*iqr]
```

---

### 문제 4 — 산점도에서 광주·대전·울산 미표시

**증상**: 면적 vs 평당가 산점도에서 광주·대전·울산 데이터 포인트가 보이지 않음.

**원인 ①**: `base.slice(0, 800)` 이후 그룹 필터 적용 → 앞 800건이 서울·경기 위주라 지방 그룹이 0건이 됨.
**원인 ②**: Canvas 렌더링 특성상 나중에 그린 레이어가 위에 표시됨. 소수 그룹이 배열 뒤에 있어야 위 레이어에 올라오는데, 데이터가 아예 없으면 렌더링 자체가 안 됨.

**관련 키워드**: `stratified sampling` · `Canvas layer order` · `z-index` · `pointRadius`
**코드 내 키워드**: `SCAT_GROUPS` · `MAX_PER_GRP` · `step` · `sampled` · `filter(d => d.data.length > 0)`

**해결**: 그룹별 층화 샘플링 + datasets 배열을 "다수 그룹 먼저, 소수 그룹 마지막" 순서로 고정.

```javascript
// 배열 순서 = Canvas 렌더링 순서
// 다수(서울·경기) 먼저 → 하위 레이어, 소수(광주·대전·울산) 마지막 → 상위 레이어
const SCAT_GROUPS = [
  { label: '서울',           color: 'rgba(232,90,90,.55)' },    // 불투명도 낮춤
  { label: '경기/인천',      color: 'rgba(167,139,250,.52)' },
  { label: '기타 지방',      color: 'rgba(184,224,74,.60)' },
  { label: '부산/대구',      color: 'rgba(249,115,22,.90)' },
  { label: '광주/대전/울산', color: 'rgba(20,220,180,1.00)' }, // 불투명도 최대
];

const MAX_PER_GRP = 300;
const scatDatasets = SCAT_GROUPS.map(g => {
  const gPts = base.filter(g.filter);
  const step = gPts.length > MAX_PER_GRP ? Math.ceil(gPts.length / MAX_PER_GRP) : 1;
  const sampled = gPts.filter((_, i) => i % step === 0).slice(0, MAX_PER_GRP);
  // 소수 그룹(80건 미만)은 포인트를 7px로 키워 가시성 추가 확보
  const r = sampled.length < 80 ? 7 : sampled.length < 150 ? 5 : 4;
  return { label: g.label, data: sampled.map(...), pointRadius: r };
}).filter(d => d.data.length > 0);
```

---

### 문제 5 — 월별 추이 차트 정렬 오류

**증상**: 월별 평균 거래가 꺾은선이 렌더링되지 않거나 데이터가 뒤섞임.

**원인**: `'2024-9'.sort()` > `'2024-10'` — 사전순(lexicographic) 정렬 시 한 자리 월이 두 자리 월보다 뒤에 와서 데이터 매핑이 어긋남.

**관련 키워드**: `lexicographic sort` · `zero-padding` · `padStart` · `ISO 8601`
**코드 내 키워드**: `deal_month` · `padStart(2, '0')` · `months` · `slice(-24)`

**해결**: 월을 `padStart(2, '0')`으로 2자리 패딩 후 정렬.

```javascript
// 수정 전: '2024-9' > '2024-10' 오정렬
const months = [
  ...new Set(base.map((t) => t.deal_year + "-" + t.deal_month)),
].sort();

// 수정 후: '2024-09' < '2024-10' 정확한 정렬
const months = [
  ...new Set(
    base.map((t) => t.deal_year + "-" + String(t.deal_month).padStart(2, "0")),
  ),
]
  .sort()
  .slice(-24);
```

선 두께 `borderWidth: 1` → `2.5`, 포인트 반지름 2 → 3으로 가시성 개선.

---

### 문제 6 — 심화 그래프 가독성 저하

**증상**: 심화 그래프 탭의 폰트가 작고 색상 대비가 낮아 레이블·축 수치 판독 불가.

**원인**: 전역 `CO` 옵션(폰트 8~9px, 투명도 .35~.55)을 심화 탭에서도 그대로 사용.

**관련 키워드**: `font.size` · `rgba opacity` · `contrast ratio` · `insidetextfont` · `outsidetextfont`
**코드 내 키워드**: `ADV_CO` · `darkLayout` · `renderAdvBoxLocal` · `renderAdvYrPyeong` · `texttemplate`

**해결 A — Chart.js**: 심화 전용 `ADV_CO` 객체, 폰트 11px, 투명도 .70~.88.

```javascript
const ADV_CO = {
  scales: {
    x: { ticks: { color: "var(--ink2)", font: { size: 11 } } },
    y: { ticks: { color: "var(--ink2)", font: { size: 11 } } },
  },
};
```

**해결 B — Plotly 트리맵**: `insidetextfont`/`outsidetextfont` 명시 + `texttemplate`으로 굵은 지역명과 평균가를 함께 표시.

```javascript
{
  type: 'treemap',
  texttemplate: '<b>%{label}</b><br>%{customdata}',  // 굵은 지역명 + 평균가
  insidetextfont:  { color: '#ffffff', size: 13 },    // 셀 내부: 흰색 13px
  outsidetextfont: { color: '#e2e8f0', size: 12 },   // 셀 외부: 밝은 회색 12px
  marker: {
    colorbar: {
      title: { text: '평균가(억)', font: { color: '#e2e8f0', size: 12 } },
      tickfont: { color: '#e2e8f0', size: 11 }
    }
  }
}
```

---

## 데이터 파이프라인

```
국토부 XML API
  ↓  fetch_molit()       지역코드 × 연월, ThreadPoolExecutor 병렬
  ↓  _parse_xml()        영문/한글 이중 폴백 + 결측·이상치 필터
  ↓  clear_and_insert()  SQLite trades 테이블, 200건 배치 점진 반영
  ↓  GET /api/data       서버사이드 필터·정렬·페이지네이션
  ↓  Chart.js / Plotly   클라이언트 렌더링
```


---

MIT License
