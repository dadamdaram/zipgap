# 집값추적기 v24

> 국토교통부 실거래가 공공 API 기반 전국 아파트 매매 탐색·분석 도구

---

## 스택

| 레이어 | 기술 |
|---|---|
| 백엔드 | Python 3.11 · FastAPI · SQLite |
| 프론트엔드 | Vanilla JS · Chart.js 4 · Plotly.js 2 |
| 데이터 | 국토교통부 실거래가 공공 API (data.go.kr) · XML |
| 배포 | Docker · Render · Railway |

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

| 탭 | 내용 |
|---|---|
| 가설 검증 | H1·H2·H3 채택/기각 판정 + 근거 차트 4종 |
| 지역 트렌드 | 월별 평균가 추이 · 산점도 · 누적 분위 바 |
| 전체 데이터 | 계층형 필터 + 정렬 가능 테이블 |
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

| 가설 | 검증 기준 | 핵심 차트 |
|---|---|---|
| **H1** 예산 20% 증가 시 매물이 임계치(+20%) 이상 증가하는가? | 0.8×, 1.0×, 1.2× 구간 매물 수 비교 | 구간별 막대 + 증가율 꺾은선 |
| **H2** 신축(10년 이내)이 구축 대비 10% 이상 비싼가? | 신축/구축 평균가 차이 % | 구축·신축 바 + 프리미엄 % 라인 |
| **H3** 같은 예산으로 지방 5대광역시에서 서울보다 1.5배 넓은 면적을 살 수 있는가? | 중위 면적 배율 | 서울·지방 면적 바 + 배율 라인 |

---

## 시각화 설계

### 사용 라이브러리

| 용도 | 라이브러리 | 이유 |
|---|---|---|
| 기본 차트 (막대·꺾은선·산점도) | Chart.js 4 | 경량, CDN 즉시 사용, tooltip 커스텀 용이 |
| 고급 차트 (트리맵·바이올린·선버스트) | Plotly.js 2 | 계층형·통계 시각화 내장, interactive zoom |

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
  paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
  font: { color: '#cbd5e1', family: "'DM Mono', monospace", size: 13 },
  margin: { l:10, r:10, t:55, b:10 },
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
const months = [...new Set(base.map(t => t.deal_year + '-' + t.deal_month))].sort();

// 수정 후: '2024-09' < '2024-10' 정확한 정렬
const months = [...new Set(
  base.map(t => t.deal_year + '-' + String(t.deal_month).padStart(2, '0'))
)].sort().slice(-24);
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
    x: { ticks: { color: 'var(--ink2)', font: { size: 11 } } },
    y: { ticks: { color: 'var(--ink2)', font: { size: 11 } } }
  }
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

## 주요 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/status` | 수집 진행률 · 총 건수 |
| GET | `/api/data` | 필터·정렬·페이지네이션 거래 목록 |
| GET | `/api/complex/{apt_name}` | 단지 거래 이력 + 통계 |
| GET | `/api/affordable` | 예산 범위 내 매물 |
| POST | `/api/crawl/auto` | 백그라운드 수집 시작 |
| POST | `/api/key/update` | API 키 갱신 + 재수집 |

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

---

MIT License
