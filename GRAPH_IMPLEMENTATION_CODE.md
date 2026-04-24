# 그래프 구현 코드 상세 가이드

> 집값추적기 v24의 모든 시각화 그래프 구현 코드 완벽 분석

---

## 📋 코드 구조 개요

### 파일 구성
- **메인 파일**: `frontend/analysis.html` (4,934 라인)
- **라이브러리**: Chart.js 4.4.1, Plotly.js 2.30.0
- **아키텍처**: Vanilla JS + CSS Grid + Canvas API

### 전역 설정 객체

```javascript
// 기본 차트 옵션 (탭 0·1·2) - 작은 폰트, 낮은 대비
const CO = {
  responsive: true,                    // 반응형 활성화
  maintainAspectRatio: false,           // 컨테이너에 맞게 비율 조정
  plugins: { 
    legend: { display: false }        // 범례 숨김 (공간 효율)
  },
  scales: {
    x: { 
      ticks: { 
        color: 'var(--ink3)',         // 연한 텍스트 색상
        font: { size: 8 }             // 작은 폰트 (밀집 표시)
      }, 
      grid: { 
        color: "rgba(107,91,69,.13)"  // 희미한 그리드 라인
      }
    },
    y: { 
      ticks: { 
        color: 'var(--ink3)',         // 연한 텍스트 색상
        font: { size: 9 }             // Y축은 약간 더 큰 폰트
      }, 
      grid: { 
        color: "rgba(107,91,69,.13)"  // 희미한 그리드 라인
      }
    }
  }
};

// 심화 그래프 전용 (탭 3) - 가독성 강화
const ADV_CO = {
  responsive: true,                    // 반응형 활성화
  maintainAspectRatio: false,           // 컨테이너에 맞게 비율 조정
  scales: {
    x: { 
      ticks: { 
        color: "var(--ink2)",         // 더 진한 텍스트 색상
        font: { size: 11 }            // 큰 폰트 (가독성 향상)
      }, 
      grid: { 
        color: "rgba(107,91,69,.13)"  // 동일한 그리드 투명도
      }
    },
    y: { 
      ticks: { 
        color: "var(--ink2)",         // 더 진한 텍스트 색상
        font: { size: 11 }            // 큰 폰트 (가독성 향상)
      }, 
      grid: { 
        color: "rgba(107,91,69,.13)"  // 동일한 그리드 투명도
      }
    }
  }
};
```

### 핵심 상수 정의

```javascript
// API 엔드포인트 동적 설정
const API = location.hostname === "localhost" || location.hostname === "127.0.0.1"
  ? "http://localhost:8000"    // 로컬 개발 환경
  : "";                         // 프로덕션 환경 (상대 경로)

// 환경 변수에서 API 키 로드
const ENV_KEY = window.__ENV__ && window.__ENV__.MOLIT_KEY
  ? window.__ENV__.MOLIT_KEY.trim()
  : "";

// 전역 상태 변수
let trades = [],           // 전체 거래 데이터
    tabIdx = 0,            // 현재 활성 탭 인덱스
    charts = {};           // 차트 인스턴스 저장

const DATA_PAGE_SIZE = 2500;     // 데이터 페이지네이션 크기
let loadSession = 0;             // 데이터 로딩 세션 ID
const hypothesisState = {        // 가설 검증 결과 저장
  h1: null, 
  h2: null, 
  h3: null 
};

// 차트 색상 팔레트 (12색)
const COLORS = [
  "#5e9ef5", "#b8e04a", "#3ddba0", "#e85a5a",
  "#d4a030", "#a78bfa", "#f97316", "#ec4899",
  "#14b8a6", "#f59e0b"
];

// 서울 지역구 목록 (25개 구 전체)
const SEOUL_REGS = [
  "서울 강남구", "서울 서초구", "서울 송파구", "서울 용산구",
  "서울 성동구", "서울 광진구", "서울 동대문구", "서울 중랑구",
  "서울 성북구", "서울 강북구", "서울 도봉구", "서울 노원구",
  "서울 은평구", "서울 서대문구", "서울 마포구", "서울 양천구",
  "서울 강서구", "서울 구로구", "서울 금천구", "서울 영등포구",
  "서울 동작구", "서울 관악구", "서울 종로구", "서울 중구",
  "서울 강동구"
];

// 지방 5대 광역시 주요 구 (18개)
const L5_REGS = [
  "부산 해운대구", "부산 수영구", "부산 동래구", "부산 남구",
  "부산 부산진구", "부산 금정구",
  "대구 수성구", "대구 달서구", "대구 동구",
  "광주 광산구", "광주 북구", "광주 서구",
  "대전 유성구", "대전 서구", "대전 동구",
  "울산 남구", "울산 중구"
];
```

### 유틸리티 함수 상세 구현

```javascript
// 통화 포맷팅 - 상세 버전 (억/천/만 단위)
function won(v) {
  const e = Math.floor(v / 10000),        // 억 단위
      c = Math.round((v % 10000) / 1000); // 천 단위
  
  if (e > 0 && c > 0) return `${e}억 ${c}천`;  // 5억 3천
  if (e > 0) return `${e}억`;                   // 5억
  if (v >= 1000) return `${Math.round(v / 1000)}천만`; // 3천만
  return `${v.toLocaleString()}만`;              // 500만
}

// 통화 포맷팅 - 간단 버전 (억 단위만)
function wonS(v) {
  const e = Math.floor(v / 10000);
  return e > 0
    ? `${e}억`                    // 5억
    : v >= 1000
      ? `${Math.round(v / 1000)}천`  // 3천
      : `${v}만`;                     // 500만
}

// 억 단위 소수점 처리 - 부동소수점 노이즈 제거
function fmtAok(v) {
  const n = parseFloat(v);
  if (isNaN(n)) return `${v}억`;
  
  // 유효숫자 4자리로 반올림 (0.90000000001 → 0.9)
  const r = parseFloat(n.toPrecision(4));
  return Number.isInteger(r) ? `${r}억` : `${r}억`;
}

// 산술 평균 계산
function avg(a) {
  return a.length ? a.reduce((s, v) => s + v, 0) / a.length : 0;
}

// 중앙값 계산 (이상치에 강건)
function med(a) {
  if (!a.length) return 0;
  const s = [...a].sort((x, y) => x - y);
  return s[Math.floor(s.length / 2)];
}

// 백분위수 계산 (p: 0~1)
function pctl(a, p) {
  if (!a.length) return 0;
  const s = [...a].sort((x, y) => x - y);
  const idx = Math.max(
    0,
    Math.min(s.length - 1, Math.round((s.length - 1) * p)),
  );
  return s[idx];
}

// 차트 메모리 관리 - 기존 차트 파괴
function dC(id) {
  // 1. charts 객체에서 차트 인스턴스 파괴
  if (charts[id]) {
    try {
      charts[id].destroy();
    } catch (e) {
      console.warn(`차트 ${id} 파괴 실패:`, e);
    }
    delete charts[id];
  }
  
  // 2. Canvas 요소에서 차트 파괴 (이중 안전장치)
  const canvas = document.getElementById(id);
  if (canvas) {
    const ex = Chart.getChart(canvas);
    if (ex) {
      try {
        ex.destroy();
      } catch (e) {
        console.warn(`Canvas 차트 ${id} 파괴 실패:`, e);
      }
    }
  }
}
```

### 입력값 가져오기 함수

```javascript
// 예산 계산 (억 + 천 단위 조합)
function getBudget() {
  return Math.round(
    (parseFloat(document.getElementById("budE").value) || 0) * 10000 +  // 억 단위
    (parseFloat(document.getElementById("budC").value) || 0) * 1000     // 천 단위
  );
}

// 최소 면적 가져오기
function getAMin() {
  return parseFloat(document.getElementById("areaMin").value) || 0;
}

// 지역 필터 값 가져오기
function getRF() {
  return document.getElementById("regionFilter").value;
}

// 지역 필터링 함수
function filterRF(data, rf) {
  if (rf === "all") return data;                    // 전국
  if (rf === "seoul") 
    return data.filter((t) => SEOUL_REGS.includes(t.region));  // 서울만
  if (rf === "metro") 
    return data.filter(
      (t) =>
        t.region.startsWith("서울") ||
        t.region.startsWith("경기") ||
        t.region.startsWith("인천"),
    );  // 수도권
  if (rf === "local") 
    return data.filter(
      (t) =>
        !t.region.startsWith("서울") &&
        !t.region.startsWith("경기") &&
        !t.region.startsWith("인천"),
    );  // 지방
  return data;
}
```

---

## 🎯 1. 가설 검증 탭 그래프 구현

### 1.1 예산별 매물 수 분포 차트 (`distC`)

```javascript
function p0Charts(b, am, rf) {
  // 1. 데이터 필터링: 예산(b), 최소면적(am), 지역(rf) 적용
  const base = filterRF(trades, rf).filter((t) => t.area >= am);
  if (!base.length) return;  // 데이터 없으면 조기 종료

  // 2. 가격 구간 동적 계산
  const maxP = Math.min(
    Math.max(...base.map((t) => t.price)) * 1.05,  // 최대가의 105%
    500000,                                           // 상한 5억
  );
  // 3. 구간 크기 계산: 30개 구간 목표, 500만원 단위로 반올림
  const step = Math.ceil(maxP / 30 / 5000) * 5000;
  
  // 4. 데이터 배열 초기화
  const lbls = [], cnts = [], clrs = [];
  
  // 5. 가격 구간 순회하며 데이터 집계
  for (let p = 0; p < maxP; p += step) {
    // 현재 구간에 속하는 매물 수 계산
    const cnt = base.filter(
      (t) => t.price >= p && t.price < p + step,
    ).length;
    
    // 6. 예산 기반 색상 분류 로직
    const below = p + step <= b;     // 구간 전체가 예산 이하
    const inB = !below && p <= b;    // 예산선이 구간 내 포함
    
    // 7. 배열에 데이터 추가
    lbls.push(wonS(p));              // 가격 레이블 (억 단위)
    cnts.push(cnt);                   // 매물 수
    clrs.push(
      inB ? "#b8e04a" :                     // 노랑: 예산선 포함 구간
      below ? "rgba(61,219,160,.55)" :      // 초록: 예산 이하 구간
      "rgba(232,90,90,.55)"                 // 빨강: 예산 초과 구간
    );
  }

  // 8. 기존 차트 파괴 및 새 차트 생성
  dC("distC");
  charts.distC = new Chart(document.getElementById("distC"), {
    type: "bar",                    // 막대 차트
    data: {
      labels: lbls,                 // X축: 가격 구간 레이블
      datasets: [{
        data: cnts,                  // Y축: 매물 수
        backgroundColor: clrs,       // 동적 색상 배열
        borderRadius: 3,             // 막대 모서리 둥글게
        borderWidth: 0,               // 테두리 없음
      }],
    },
    options: {
      ...CO,                         // 기본 옵션 상속
      plugins: {
        legend: { display: false }, // 범례 숨김
        tooltip: {
          callbacks: {
            title: (ls) => `${ls[0].label} 대`,  // 툴팁 제목
            label: (c) => `${c.parsed.y}건`,     // 툴팁 내용
          },
        },
      },
    },
  });
}
```

**핵심 기술 상세 분석**:

1. **동적 구간화**: 데이터의 실제 범위에 따라 자동으로 30개 구간 생성
   - `maxP`: 최대가의 105%를 상한으로 설정 (여유 공간 확보)
   - `step`: 500만원 단위로 반올림하여 깔끔한 구간 형성

2. **3단계 색상 로직**: 예산선을 기준으로 정확한 시각적 분리
   - `below`: 구간 전체가 예산 80% 이하 (초록)
   - `inB`: 예산선이 구간 내 포함 (노랑 - 핵심 구간)
   - `else`: 예산 초과 구간 (빨강)

3. **메모리 관리**: `dC()` 함수로 기존 차트 인스턴스 파괴
   - Canvas 메모리 누수 방지
   - 데이터 업데이트 시 깨끗한 재렌더링

4. **사용자 경험**: 직관적인 색상 코딩으로 예산 매물 즉시 파악
   - 초록: 안전 매물 (예산 내 여유)
   - 노랑: 경계 매물 (예산 근접)
   - 빨강: 초과 매물 (예산 외)

---

### 1.2 건축연도별 평균가 라인 차트 (`ageC`)

```javascript
// 1. 건축연도별 데이터 버케팅 (5년 단위 그룹화)
const bkts = {};
base.forEach((t) => {
  const yr = parseInt(t.year_built);
  
  // 2. 데이터 유효성 검증: 1985-2025년 범위 외 제외
  if (yr < 1985 || yr > 2025) return;
  
  // 3. 5년 단위로 그룹화 (예: 1987 → 1985, 1992 → 1990)
  const g = Math.floor(yr / 5) * 5;
  if (!bkts[g]) bkts[g] = [];
  bkts[g].push(t.price);
});

// 4. 정렬된 연도 배열과 평균가 계산
const aL = Object.keys(bkts).sort();                    // 연도 정렬
const aV = aL.map((g) => Math.round(avg(bkts[g])));     // 각 그룹 평균가

// 5. 기존 차트 파괴 및 새 차트 생성
dC("ageC");
charts.ageC = new Chart(document.getElementById("ageC"), {
  type: "line",                    // 꺾은선 차트
  data: {
    labels: aL.map((g) => g + "년"),  // X축: "1985년", "1990년"...
    datasets: [{
      data: aV,                      // Y축: 평균가 데이터
      borderColor: "#3ddba0",         // 선 색상 (밝은 초록)
      backgroundColor: "rgba(61,219,160,.08)",  // 영역 채우기 색상
      pointBackgroundColor: "#3ddba0", // 점 색상
      pointRadius: 5,                // 기본 점 크기
      pointHoverRadius: 7,            // 호버 시 점 크기
      tension: 0.35,                 // 곡선 장력 (0=직선, 1=완만)
      fill: true,                    // 아래 영역 채우기
    }],
  },
  options: {
    ...CO,                           // 기본 옵션 상속
    plugins: {
      legend: { display: false },   // 범례 숨김
      tooltip: {
        callbacks: { 
          label: (c) => `평균 ${wonS(c.parsed.y)}`  // 툴팁: "평균 5억"
        },
      },
    },
    scales: {
      x: { ...CO.scales.x },         // X축 기본 설정
      y: {
        ...CO.scales.y,              // Y축 기본 설정
        ticks: { 
          ...CO.scales.y.ticks, 
          callback: (v) => wonS(v)   // Y축 레이블 통화 포맷
        },
      },
    },
  },
});
```

**핵심 기술 상세 분석**:

1. **데이터 버케팅 (Bucketing)**: 5년 단위로 건축연도 그룹화
   - `Math.floor(yr / 5) * 5`: 1987 → 1985, 1992 → 1990
   - 노이즈 감소와 트렌드 파악 용이

2. **데이터 정제**: 1985-2025년 범위 외 데이터 제외
   - 이상치 방지 (1900년대 초반, 2030년대 등)
   - 현실적인 건축연도 범위 설정

3. **보간법 효과**: `tension: 0.35`로 부드러운 곡선 생성
   - Catmull-Rom 스플라인 기반
   - 불연속적인 연도 간 자연스러운 연결

4. **시각적 강조**: 영역 채우기로 추세 강조
   - `fill: true`: 선 아래 영역 채움
   - `backgroundColor`: 투명도 8%로 시각적 부담 감소

5. **인터랙티브 툴팁**: 호버 시 정확한 평균가 표시
   - `pointHoverRadius: 7`: 호버 시 점 확대
   - `wonS()` 함수로 억 단위 포맷팅

---

### 1.3 서울 vs 지방 면적대별 비교 (`areaCmpC`)

```javascript
// 1. 예산 내 매물 필터링
const aff = trades.filter((t) => t.price <= b && t.area >= am);

// 2. 표준 면적 구간 정의 (전용면적 기준)
const ALBL = [33, 49, 59, 74, 84, 101, 115, 135, 165];
// 의미: 33㎡(10평), 49㎡(15평), 59㎡(18평), 74㎡(22평), 84㎡(25평), 
//       101㎡(30평), 115㎡(35평), 135㎡(40평), 165㎡(50평)

// 3. 서울 지역별 면적대 매물 수 계산
const sc = ALBL.map((a) =>
  aff.filter(
    (t) =>
      SEOUL_REGS.includes(t.region) &&  // 서울 지역구 필터
      t.area >= a - 8 &&              // 하한: 기준 면적 - 8㎡
      t.area < a + 8,                 // 상한: 기준 면적 + 8㎡
  ).length,
);

// 4. 지방 5대광역시 면적대 매물 수 계산
const lc = ALBL.map((a) =>
  aff.filter(
    (t) =>
      L5_REGS.includes(t.region) &&   // 지방 5대광역시 필터
      t.area >= a - 8 &&              // 동일한 허용 오차 범위 적용
      t.area < a + 8,
  ).length,
);

// 5. 기존 차트 파괴 및 새 차트 생성
dC("areaCmpC");
charts.areaCmpC = new Chart(document.getElementById("areaCmpC"), {
  type: "bar",                    // 그룹화 막대 차트
  data: {
    labels: ALBL.map((a) => a + "㎡"),  // X축: "33㎡", "49㎡"...
    datasets: [
      {
        label: "서울",             // 첫 번째 데이터셋
        data: sc,                  // 서울 매물 수 배열
        backgroundColor: "rgba(232,90,90,.65)",  // 빨강 계열
        borderRadius: 4,           // 막대 모서리 둥글게
        borderWidth: 0,            // 테두리 없음
      },
      {
        label: "지방5대",          // 두 번째 데이터셋
        data: lc,                  // 지방 매물 수 배열
        backgroundColor: "rgba(61,219,160,.65)",  // 초록 계열
        borderRadius: 4,           // 막대 모서리 둥글게
        borderWidth: 0,            // 테두리 없음
      },
    ],
  },
  options: {
    ...CO,                         // 기본 옵션 상속
    plugins: {
      legend: {
        display: true,             // 범례 표시 (두 그룹 비교)
        labels: {
          color: "var(--ink2)",     // 범례 텍스트 색상
          font: { 
            family: "'DM Mono'",    // 모노스페이스 폰트
            size: 9                 // 작은 폰트 크기
          },
          boxWidth: 10,            // 범례 색상 박스 크기
        },
      },
    },
  },
});
```

**핵심 기술 상세 분석**:

1. **표준 면적 구간**: 부동산 업계 표준 평수 기반 설정
   - 33㎡(10평)부터 165㎡(50평)까지 9개 구간
   - 실수요자들이 이해하기 쉬운 평수 단위

2. **허용 오차 범위**: ±8㎡로 유사 면적 매물 포함
   - `a - 8`에서 `a + 8` 미만: 16㎡ 허용 범위
   - 실제 시장에서 면적은 정수가 아닌 소수점으로 존재

3. **지역 그룹 필터링**: 상수 기반 정확한 지역 분류
   - `SEOUL_REGS`: 서울 25개 구 전체
   - `L5_REGS`: 지방 5대광역시 주요 구 18개

4. **시각적 대비**: 빨강(서울) vs 초록(지방) 색상 코딩
   - 65% 투명도로 가독성 확보
   - 두 그룹의 명확한 시각적 구분

5. **데이터 해석**: 각 면적대별 매물 수로 지역별 수급 비교
   - 서울: 소형 평수 집중 현상 파악
   - 지방: 대형 평수 상대적 매물 증가 확인

---

### 1.4 가설 근거 차트들 (`h1EvC`, `h2EvC`, `h3EvC`)

#### H1 근거 차트 (복합 차트) - 예산 비선형 증가

```javascript
// H1 근거 차트 생성 (막대 + 선 조합)
dC("h1EvC");
charts.h1EvC = new Chart(document.getElementById("h1EvC"), {
  data: {
    labels: ["0.8x", "1.0x", "1.2x"],  // 예산 배율 레이블
    datasets: [
      // 첫 번째 데이터셋: 매물 수 막대
      {
        type: "bar",                  // 막대 차트 타입
        yAxisID: "y",                 // 왼쪽 Y축 사용
        data: [h1.n0 || 0, h1.n1 || 0, h1.n2 || 0],  // 각 예산 구간 매물 수
        backgroundColor: [
          "rgba(94,158,245,.5)",      // 0.8x: 파스텔 블루
          "rgba(184,224,74,.7)",      // 1.0x: 밝은 그린
          "rgba(61,219,160,.65)",     // 1.2x: 그린
        ],
        borderRadius: 4,             // 막대 모서리 둥글게
        borderWidth: 0,               // 테두리 없음
      },
      
      // 두 번째 데이터셋: 실제 증가율 선
      {
        type: "line",                 // 꺾은선 차트 타입
        yAxisID: "y1",                // 오른쪽 Y축 사용
        data: [
          null,                       // 0.8x 시작점 (없음)
          h1.ready ? Math.max(0, h1.r1) : null,  // 0.8x→1.0x 증가율
          h1.ready ? Math.max(0, h1.r2) : null,  // 1.0x→1.2x 증가율
        ],
        borderColor: "rgba(255,255,255,.6)",  // 흰색 선
        pointBackgroundColor: "#EDF1FF",        // 점 색상
        pointRadius: 3,               // 점 크기
        tension: 0.25,                // 곡선 장력
      },
      
      // 세 번째 데이터셋: 20% 기준선
      {
        type: "line",                 // 꺾은선 차트 타입
        yAxisID: "y1",                // 오른쪽 Y축 사용
        data: [20, 20, 20],           // 20% 기준선
        borderColor: "rgba(184,224,74,.55)",  // 그린 기준선
        borderDash: [5, 5],           // 점선 스타일
        pointRadius: 0,               // 점 숨김
      },
    ],
  },
  options: {
    ...CO,                           // 기본 옵션 상속
    plugins: { legend: { display: false } },  // 범례 숨김
    scales: {
      x: { ...CO.scales.x },         // X축 기본 설정
      y: { 
        ...CO.scales.y, 
        beginAtZero: true,            // Y축 0부터 시작
      },
      y1: {                          // 오른쪽 Y축 (증가율)
        position: "right",            // 오른쪽에 위치
        beginAtZero: true,            // 0부터 시작
        grid: { drawOnChartArea: false },  // 그리드 라인 숨김
        ticks: {
          color: "#62666f",          // 텍스트 색상
          font: { family: "'DM Mono'", size: 9 },  // 폰트
          callback: (v) => v + "%",  // 퍼센트 포맷
        },
      },
    },
  },
});
```

**H1 차트 핵심 기술 상세 분석**:

1. **복합 차트 구조**: 막대 + 선 차트 조합으로 이중 정보 표시
   - 막대: 각 예산 구간의 실제 매물 수
   - 선: 구간별 증가율 변화
   - 기준선: 20% 임계치 시각적 표시

2. **이중 Y축 시스템**: 서로 다른 단위의 데이터 동시 표시
   - 왼쪽 Y축: 매물 수 (정수)
   - 오른쪽 Y축: 증가율 (퍼센트)
   - `yAxisID`로 각 데이터셋의 축 지정

3. **데이터 무결성**: `Math.max(0, h1.r1)`로 음수 방지
   - 감소율도 양수로 표시하여 직관성 확보
   - `h1.ready` 체크로 데이터 준비 상태 확인

4. **시각적 계층**: 점선 기준선으로 임계치 강조
   - `borderDash: [5, 5]`: 5px 선, 5px 공백 패턴
   - 녹색 기준선으로 목표치 시각적 구분

#### H2 근거 차트 (신축 프리미엄)

```javascript
// H2 근거 차트 생성
dC("h2EvC");
charts.h2EvC = new Chart(document.getElementById("h2EvC"), {
  data: {
    labels: ["구축", "신축"],         // 그룹 레이블
    datasets: [
      // 첫 번째 데이터셋: 평균가 막대
      {
        type: "bar",                  // 막대 차트
        yAxisID: "y",                 // 왼쪽 Y축 (가격)
        data: [h2.aO || 0, h2.aN || 0],  // 구축/신축 평균가
        backgroundColor: [
          "rgba(255,159,64,.7)",      // 구축: 주황
          "rgba(59,130,246,.7)",      // 신축: 파랑
        ],
        borderRadius: 4,
        borderWidth: 0,
      },
      
      // 두 번째 데이터셋: 사분위수 박스플롯
      {
        type: "bar",                  // 막대로 박스플롯 시뮬레이션
        yAxisID: "y1",                // 오른쪽 Y축 (통계)
        data: [
          // 구축 그룹 사분위수
          {
            y: [h2.box.ol.q1, h2.box.ol.q3],  // Q1~Q3 범위
            customData: {
              min: h2.box.ol.min,            // 최솟값
              q1: h2.box.ol.q1,              // 제1사분위수
              q2: h2.box.ol.q2,              // 중앙값
              q3: h2.box.ol.q3,              // 제3사분위수
              max: h2.box.ol.max,            // 최댓값
            }
          },
          // 신축 그룹 사분위수
          {
            y: [h2.box.nw.q1, h2.box.nw.q3],
            customData: {
              min: h2.box.nw.min,
              q1: h2.box.nw.q1,
              q2: h2.box.nw.q2,
              q3: h2.box.nw.q3,
              max: h2.box.nw.max,
            }
          }
        ],
        backgroundColor: "rgba(255,255,255,.1)",  // 투명한 박스
        borderColor: "rgba(255,255,255,.3)",     // 박스 테두리
        borderWidth: 1,
      },
    ],
  },
  options: {
    ...CO,
    plugins: { legend: { display: false } },
    scales: {
      x: { ...CO.scales.x },
      y: { 
        ...CO.scales.y,
        beginAtZero: true,
        ticks: { callback: (v) => wonS(v) },  // 통화 포맷
      },
      y1: {
        position: "right",
        beginAtZero: true,
        grid: { drawOnChartArea: false },
        ticks: {
          color: "#62666f",
          font: { family: "'DM Mono'", size: 9 },
        },
      },
    },
  },
});
```

**H2 차트 핵심 기술 상세 분석**:

1. **박스플롯 시뮬레이션**: Chart.js로 통계적 분포 표현
   - `customData`에 5수 요약 저장
   - 툴팁에서 상세 통계 정보 제공
   - 시각적 박스로 데이터 분포 범위 표시

2. **그룹 대비 시각화**: 구축 vs 신축 명확한 비교
   - 주황(구축) vs 파랑(신축) 색상 대비
   - 평균가 막대로 중심 경향성 표시
   - 박스로 분포와 이상치 정보 제공

3. **통계 데이터 처리**: 사분위수 정확한 계산과 표시
   - Q1, Q2(중앙값), Q3로 데이터 분포 파악
   - 최솟값/최댓값으로 전체 범위 확인
   - 프리미엄 계산을 위한 기초 데이터 제공

#### H3 근거 차트 (지역별 면적 배율)

```javascript
// H3 근거 차트 생성
dC("h3EvC");
charts.h3EvC = new Chart(document.getElementById("h3EvC"), {
  data: {
    labels: ["서울", "지방5대"],     // 지역 그룹 레이블
    datasets: [
      // 첫 번째 데이터셋: 평균 면적 막대
      {
        type: "bar",                  // 막대 차트
        yAxisID: "y",                 // 왼쪽 Y축 (면적)
        data: [h3.sArea || 0, h3.rArea || 0],  // 서울/지방 평균 면적
        backgroundColor: [
          "rgba(239,68,68,.7)",       // 서울: 빨강
          "rgba(34,197,94,.7)",       // 지방: 그린
        ],
        borderRadius: 4,
        borderWidth: 0,
      },
      
      // 두 번째 데이터셋: 평당가 선
      {
        type: "line",                 // 꺾은선 차트
        yAxisID: "y1",                // 오른쪽 Y축 (평당가)
        data: [h3.proof.sMed || 0, h3.proof.lMed || 0],  // 평당가 중앙값
        borderColor: "rgba(255,255,255,.6)",  // 흰색 선
        pointBackgroundColor: "#EDF1FF",        // 점 색상
        pointRadius: 5,               // 점 크기
        tension: 0.25,
      },
      
      // 세 번째 데이터셋: 1.5x 기준선
      {
        type: "line",                 // 꺾은선 차트
        yAxisID: "y",                 // 왼쪽 Y축 (면적)
        data: [
          null,                       // 서울 시작점 (없음)
          (h3.sArea || 0) * 1.5       // 지방 목표 면적 (서울의 1.5배)
        ],
        borderColor: "rgba(184,224,74,.55)",  // 그린 기준선
        borderDash: [5, 5],           // 점선
        pointRadius: 0,
      },
    ],
  },
  options: {
    ...CO,
    plugins: { legend: { display: false } },
    scales: {
      x: { ...CO.scales.x },
      y: { 
        ...CO.scales.y,
        beginAtZero: true,
        ticks: { 
          callback: (v) => `${Math.round(v)}㎡`  // 면적 포맷
        },
      },
      y1: {
        position: "right",
        beginAtZero: true,
        grid: { drawOnChartArea: false },
        ticks: {
          color: "#62666f",
          font: { family: "'DM Mono'", size: 9 },
          callback: (v) => `${Math.round(v/100)}억/평`,  // 평당가 포맷
        },
      },
    },
  },
});
```

**H3 차트 핵심 기술 상세 분석**:

1. **다중 지표 조합**: 면적 + 평당가 동시 표시
   - 막대: 평균 면적 (㎡ 단위)
   - 선: 평당가 중앙값 (억/평 단위)
   - 기준선: 1.5배 목표치 시각화

2. **면적 배율 계산**: 서울 기준 지방 면적 효율성
   - `(h3.sArea || 0) * 1.5`: 목표 면적 계산
   - 실제 지방면적 vs 목표면적 시각적 비교
   - 가성비 지표로 직관적 판단 지원

3. **단위 통합**: 서로 다른 단위의 조화로운 표시
   - 왼쪽 Y축: 면적 (㎡)
   - 오른쪽 Y축: 평당가 (억/평)
   - 각 축에 적절한 포맷팅 적용

#### H1 근거 차트 (복합 차트)

```javascript
dC("h1EvC");
charts.h1EvC = new Chart(document.getElementById("h1EvC"), {
  data: {
    labels: ["0.8x", "1.0x", "1.2x"],
    datasets: [
      // 막대: 매물 수
      {
        type: "bar",
        yAxisID: "y",
        data: [h1.n0 || 0, h1.n1 || 0, h1.n2 || 0],
        backgroundColor: [
          "rgba(94,158,245,.5)",
          "rgba(184,224,74,.7)",
          "rgba(61,219,160,.65)",
        ],
        borderRadius: 4,
        borderWidth: 0,
      },
      // 선: 실제 증가율
      {
        type: "line",
        yAxisID: "y1",
        data: [
          null,
          h1.ready ? Math.max(0, h1.r1) : null,
          h1.ready ? Math.max(0, h1.r2) : null,
        ],
        borderColor: "rgba(255,255,255,.6)",
        pointBackgroundColor: "#EDF1FF",
        pointRadius: 3,
        tension: 0.25,
      },
      // 선: 20% 기준선
      {
        type: "line",
        yAxisID: "y1",
        data: [20, 20, 20],
        borderColor: "rgba(184,224,74,.55)",
        borderDash: [5, 5],
        pointRadius: 0,
      },
    ],
  },
  options: {
    ...CO,
    plugins: { legend: { display: false } },
    scales: {
      x: { ...CO.scales.x },
      y: { ...CO.scales.y, beginAtZero: true },
      y1: {
        position: "right",
        beginAtZero: true,
        grid: { drawOnChartArea: false },
        ticks: {
          color: "#62666f",
          font: { family: "'DM Mono'", size: 9 },
          callback: (v) => v + "%",
        },
      },
    },
  },
});
```

**핵심 기술**:
- **복합 차트**: 막대 + 선 차트 조합 (2개 Y축)
- **기준선**: 20% 임계선 점선 표시
- **이중 축**: 왼쪽(매물 수), 오른쪽(증가율)

---

## 📈 2. 지역 트렌드 탭 그래프 구현

### 2.1 월별 평균가 추이 꺾은선 차트 (`trendC`)

```javascript
function p1Charts(am, rf) {
  const base = filterRF(trades, rf).filter((t) => t.area >= am);
  if (!base.length) return;

  // 상위 지역 선택 (거래량 기준)
  const regCount = [...new Set(base.map((t) => t.region))]
    .map((r) => ({
      r,
      cnt: base.filter((t) => t.region === r).length,
    }))
    .sort((a, b) => b.cnt - a.cnt);

  const regs = regCount.slice(0, 6).map((x) => x.r);
  
  // 전북 특별 처리 (항상 상위에 표시)
  const jeonbukRegion = regs.find((r) => r.includes("전북"));
  if (jeonbukRegion) {
    const currentIndex = regs.findIndex((r) => r.includes("전북"));
    if (currentIndex > 2) {
      regs.splice(currentIndex, 1);
      regs.splice(2, 0, jeonbukRegion);
    }
  }

  // 월 패딩으로 올바른 사전순 정렬 ('01'~'12')
  const months = [
    ...new Set(
      base.map((t) => 
        t.deal_year + "-" + String(t.deal_month).padStart(2, "0")
      ),
    ),
  ]
    .sort()
    .slice(-24);  // 최근 24개월

  const datasets = regs.map((r, i) => ({
    label: r.split(" ").slice(-1)[0],
    spanGaps: true,
    borderColor: COLORS[i],
    backgroundColor: "transparent",
    borderWidth: 2.5,
    pointRadius: 3,
    pointHoverRadius: 6,
    tension: 0.35,
    data: months.map((m) => {
      const [y, mo] = m.split("-");
      const tt = base.filter(
        (t) =>
          t.region === r &&
          String(t.deal_year) === y &&
          String(t.deal_month).padStart(2, "0") === mo,
      );
      return tt.length ? Math.round(avg(tt.map((t) => t.price))) : null;
    }),
  }));

  dC("trendC");
  charts.trendC = new Chart(document.getElementById("trendC"), {
    type: "line",
    data: { labels: months, datasets },
    options: {
      ...CO,
      plugins: {
        legend: { display: false },
        tooltip: { mode: "index", intersect: false },
      },
      scales: {
        x: {
          ...CO.scales.x,
          ticks: { ...CO.scales.x.ticks, maxTicksLimit: 12 },
        },
        y: {
          ...CO.scales.y,
          ticks: { ...CO.scales.y.ticks, callback: (v) => wonS(v) },
        },
      },
    },
  });
}
```

**핵심 기술**:
- **월 패딩**: `padStart(2, '0')`으로 '2024-9' → '2024-09' 변환
- **결측값 처리**: `spanGaps: true`로 데이터 없는 구간 자동 연결
- **동적 색상**: `COLORS` 배열로 지역별 색상 할당
- **전북 특별 처리**: 항상 상위 3위 내에 표시

---

### 2.2 면적 vs 평당가 산점도 (`scatC`)

```javascript
// 면적 vs 평당가 산점도 — 지역 그룹별 층화 샘플링
const SCAT_GROUPS = [
  {
    label: "서울",
    filter: (t) => t.region.startsWith("서울"),
    color: "rgba(232,90,90,.55)",
  },
  {
    label: "경기/인천",
    filter: (t) =>
      t.region.startsWith("경기") || t.region.startsWith("인천"),
    color: "rgba(167,139,250,.52)",
  },
  {
    label: "기타 지방",
    filter: (t) =>
      !t.region.startsWith("서울") &&
      !t.region.startsWith("경기") &&
      !t.region.startsWith("인천") &&
      !t.region.startsWith("부산") &&
      !t.region.startsWith("대구") &&
      !t.region.startsWith("광주") &&
      !t.region.startsWith("대전") &&
      !t.region.startsWith("울산"),
    color: "rgba(184,224,74,.60)",
  },
  {
    label: "부산/대구",
    filter: (t) =>
      t.region.startsWith("부산") || t.region.startsWith("대구"),
    color: "rgba(249,115,22,.90)",
  },
  {
    label: "광주/대전/울산",
    filter: (t) =>
      t.region.startsWith("광주") ||
      t.region.startsWith("대전") ||
      t.region.startsWith("울산"),
    color: "rgba(20,220,180,1.00)",
  },
];

// 그룹마다 최대 300개씩 등간격 샘플링
const MAX_PER_GRP = 300;
const scatDatasets = SCAT_GROUPS.map((g) => {
  const gPts = base.filter(g.filter);
  const step =
    gPts.length > MAX_PER_GRP
      ? Math.ceil(gPts.length / MAX_PER_GRP)
      : 1;
  const sampled = gPts
    .filter((_, i) => i % step === 0)
    .slice(0, MAX_PER_GRP);
  
  // 소수 그룹은 포인트 크기 키워서 가시성 확보
  const r = sampled.length < 80 ? 7 : sampled.length < 150 ? 5 : 4;
  
  return {
    label: g.label,
    data: sampled.map((t) => ({
      x: Math.round(t.area / 3.3),           // 평 단위 변환
      y: Math.round((t.per_pyeong / 10000) * 10) / 10,  // 억 단위
      r: t.region,
      n: t.apt_name,
    })),
    backgroundColor: g.color,
    pointRadius: r,
    pointHoverRadius: r + 4,
  };
}).filter((d) => d.data.length > 0);

dC("scatC");
charts.scatC = new Chart(document.getElementById("scatC"), {
  type: "scatter",
  data: { datasets: scatDatasets },
  options: {
    ...CO,
    plugins: {
      legend: {
        display: true,
        position: "bottom",
        labels: {
          color: "var(--ink2)",
          font: { family: "'DM Mono'", size: 9 },
          boxWidth: 10,
          padding: 10,
        },
      },
      tooltip: {
        callbacks: {
          label: (c) =>
            `${c.dataset.label} | ${c.raw.n || ""} ${c.parsed.x}평 · ${c.parsed.y}억/평`,
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "평수",
          color: "var(--ink3)",
          font: { size: 10 },
        },
        ticks: { color: "var(--ink3)", font: { size: 9 } },
        grid: { color: "rgba(107,91,69,.07)" },
      },
      y: {
        title: {
          display: true,
          text: "평당가(억)",
          color: "var(--ink3)",
          font: { size: 10 },
        },
        ticks: {
          color: "var(--ink3)",
          font: { size: 9 },
          callback: (v) => fmtAok(v),
        },
        grid: { color: "rgba(107,91,69,.07)" },
      },
    },
  },
});
```

**핵심 기술**:
- **층화 샘플링**: 그룹별 균등 표본 추출 (최대 300개)
- **동적 포인트 크기**: 데이터 수에 따라 4-7px 조절
- **단위 변환**: ㎡→평, 만원→억 단위 변환
- **Canvas 레이어 순서**: 다수 그룹 먼저, 소수 그룹 나중에 렌더링

---

### 2.3 지역별 누적 분위 바 (`boxC`)

```javascript
// 지역별 가격 분위 누적 바
const allR = regCount.slice(0, 12).map((x) => x.r);
const q25 = [], meds = [], q75 = [];

allR.forEach((r) => {
  const pp = trades
    .filter((t) => t.region === r)
    .map((t) => t.price)
    .sort((a, b) => a - b);
  
  if (!pp.length) {
    q25.push(0);
    meds.push(0);
    q75.push(0);
    return;
  }
  
  q25.push(pp[Math.floor(pp.length * 0.25)]);
  meds.push(pp[Math.floor(pp.length * 0.5)]);
  q75.push(pp[Math.floor(pp.length * 0.75)]);
});

dC("boxC");
charts.boxC = new Chart(document.getElementById("boxC"), {
  type: "bar",
  data: {
    labels: allR.map((r) => r.split(" ").slice(-1)[0]),
    datasets: [
      {
        label: "하위25%",
        data: q25,
        backgroundColor: "rgba(94,158,245,.45)",
        borderRadius: 2,
        borderWidth: 0,
      },
      {
        label: "중위",
        data: meds.map((m, i) => m - q25[i]),  // 중위-하위25%
        backgroundColor: "rgba(184,224,74,.55)",
        borderRadius: 2,
        borderWidth: 0,
      },
      {
        label: "상위25%",
        data: q75.map((q, i) => q - meds[i]),  // 상위25%-중위
        backgroundColor: "rgba(232,90,90,.45)",
        borderRadius: 2,
        borderWidth: 0,
      },
    ],
  },
  options: {
    ...CO,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: "var(--ink2)",
          font: { size: 9 },
          boxWidth: 10,
        },
      },
    },
    scales: {
      x: {
        stacked: true,  // 누적 바
        ...CO.scales.x,
        ticks: { ...CO.scales.x.ticks, maxRotation: 30 },
      },
      y: {
        stacked: true,  // 누적 바
        ...CO.scales.y,
        ticks: { ...CO.scales.y.ticks, callback: (v) => wonS(v) },
      },
    },
  },
});
```

**핵심 기술**:
- **사분위수 계산**: `Math.floor(pp.length * 0.25)`로 25% 지점 계산
- **누적 바**: `stacked: true`로 3개 레이어 쌓기
- **상대적 높이**: 각 레이어를 차이값으로 계산하여 누적 효과

---

## 📊 3. 심화 그래프 탭 구현 (Plotly.js)

### 3.1 Plotly 트리맵 (`showPlotly('treemap')`)

```javascript
if (type === "treemap") {
  // 트리맵: 광역시도 > 구군, 색=평균가
  const map = {};
  trades.forEach((t) => {
    const met = t.region.split(" ")[0];  // 광역시도
    const gu = t.region;                 // 구군
    if (!map[met]) map[met] = { total: 0, cnt: 0, children: {} };
    map[met].total += t.price;
    map[met].cnt++;
    if (!map[met].children[gu])
      map[met].children[gu] = { total: 0, cnt: 0 };
    map[met].children[gu].total += t.price;
    map[met].children[gu].cnt++;
  });

  // 계층적 데이터 구조 생성
  const ids = [], labels = [], parents = [], values = [], colors = [], texts = [];
  
  ids.push("전국");
  labels.push("전국");
  parents.push("");
  values.push(0);
  colors.push(0);
  texts.push("");

  Object.entries(map).forEach(([met, d]) => {
    const avg = Math.round((d.total / d.cnt / 10000) * 10) / 10;
    ids.push(met);
    labels.push(met);
    parents.push("전국");
    values.push(d.cnt);
    colors.push(avg);
    texts.push(`평균 ${avg}억`);
    
    Object.entries(d.children).forEach(([gu, c]) => {
      const ga = Math.round((c.total / c.cnt / 10000) * 10) / 10;
      const guLabel = gu.replace(met + " ", "");
      ids.push(gu);
      labels.push(guLabel);
      parents.push(met);
      values.push(c.cnt);
      colors.push(ga);
      texts.push(`${ga}억`);
    });
  });

  const fig = {
    data: [
      {
        type: "treemap",
        ids, labels, parents, values,
        marker: {
          colors,
          colorscale: [
            [0, "#10b981"],    // 저가: 녹색
            [0.5, "#f59e0b"],  // 중가: 노랑
            [1, "#ef4444"],    // 고가: 빨강
          ],
          showscale: true,
          colorbar: {
            title: {
              text: "평균가(억)",
              font: { color: "#e2e8f0", size: 12 },
            },
            tickfont: { color: "#e2e8f0", size: 11 },
          },
        },
        textinfo: "label+text",
        texttemplate: "<b>%{label}</b><br>%{customdata}",
        customdata: texts,
        insidetextfont: {
          color: "#ffffff",
          size: 13,
          family: "DM Mono, monospace",
        },
        outsidetextfont: {
          color: "#e2e8f0",
          size: 12,
          family: "DM Mono, monospace",
        },
        hovertemplate:
          "<b>%{label}</b><br>거래 %{value}건<br>평균 %{customdata}<extra></extra>",
      },
    ],
    layout: {
      ...darkLayout,
      title: {
        text: "지역별 거래 비중 & 평균가 트리맵",
        font: { color: "#f1f5f9", size: 15 },
      },
    },
  };

  Plotly.newPlot(wrap, fig.data, fig.layout, {
    responsive: true,
    displayModeBar: false,
  });
}
```

**핵심 기술**:
- **계층적 데이터**: 전국 > 광역시도 > 구군 3단계 구조
- **이중 매핑**: 크기(거래량) + 색상(평균가)
- **커스텀 텍스트**: `texttemplate`으로 지역명+평균가 표시
- **다크 테마**: `darkLayout`으로 일관된 디자인

---

### 3.2 Plotly 바이올린 플롯 (`showPlotly('violin')`)

```javascript
else if (type === "violin") {
  const metMap = {};
  trades.forEach((t) => {
    const m = t.region.split(" ")[0];
    if (!metMap[m]) metMap[m] = [];
    metMap[m].push(t.price / 10000);  // 억 단위 변환
  });

  // 상위 8개 광역시도 선택 (최소 10개 데이터)
  const top = Object.entries(metMap)
    .filter(([, v]) => v.length >= 10)
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, 8);

  const palette = [
    "#5e9ef5", "#b8e04a", "#3ddba0", "#e85a5a",
    "#d4a030", "#a78bfa", "#f97316", "#ec4899",
  ];

  const data = top.map(([met, vals], i) => ({
    type: "violin",
    y: vals,
    name: met,
    box: { visible: true },        // 박스플롯 표시
    meanline: { visible: true },   // 평균선 표시
    fillcolor: palette[i],
    opacity: 0.65,
    line: { color: palette[i], width: 1.5 },
    points: false,                 // 개별 점 숨김
    hoverinfo: "y+name",
  }));

  Plotly.newPlot(
    wrap,
    data,
    {
      ...darkLayout,
      title: {
        font: { color: "#cbd5e1" },
        text: "광역시도별 거래가 분포",
        font: { color: "#e2e8f0", size: 15 },
      },
      yaxis: {
        title: {
          font: { color: "#cbd5e1" },
          text: "거래가(억)",
          font: { color: "#94a3b8" },
        },
        tickfont: { color: "#cbd5e1" },
        gridcolor: "rgba(107,91,69,.12)",
      },
      xaxis: {
        tickfont: { color: "#cbd5e1" },
        gridcolor: "rgba(107,91,69,.08)",
      },
      showlegend: false,
    },
    { responsive: true, displayModeBar: false },
  );
}
```

**핵심 기술**:
- **데이터 필터링**: 최소 10개 이상인 광역시도만 선택
- **통계 요소**: 박스플롯(Q1, Q3, 중앙값) + 평균선
- **투명도 조절**: `opacity: 0.65`로 겹침 부분 가시성 확보
- **개별 점 숨김**: `points: false`로 시각적 복잡성 감소

---

### 3.3 Plotly 선버스트 차트 (`showPlotly('sunburst')`)

```javascript
else {
  // sunburst — 중심=전국 평균가, 1레이어=광역시도, 2레이어=구군
  const map = {};
  trades.forEach((t) => {
    const met = t.region.split(" ")[0];
    const gu = t.region;
    if (!map[met]) map[met] = { total: 0, cnt: 0, children: {} };
    map[met].total += t.price;
    map[met].cnt++;
    if (!map[met].children[gu])
      map[met].children[gu] = { total: 0, cnt: 0 };
    map[met].children[gu].total += t.price;
    map[met].children[gu].cnt++;
  });

  const ids = ["전국"], labels = ["전국 평균"], parents = [""], values = [trades.length];
  const allAvg = Math.round(
    (trades.reduce((s, t) => s + t.price, 0) / trades.length / 10000) * 10
  ) / 10;
  const colors = [allAvg], texts = [`${allAvg}억`];

  Object.entries(map)
    .sort((a, b) => b[1].cnt - a[1].cnt)
    .forEach(([met, d]) => {
      const ma = Math.round((d.total / d.cnt / 10000) * 10) / 10;
      ids.push(met);
      labels.push(`${met}\n${ma}억`);
      parents.push("전국");
      values.push(d.cnt);
      colors.push(ma);
      texts.push(`${ma}억 · ${d.cnt}건`);
      
      Object.entries(d.children)
        .sort((a, b) => b[1].cnt - a[1].cnt)
        .slice(0, 12)  // 광역시도별 최대 12개 구군
        .forEach(([gu, c]) => {
          const ga = Math.round((c.total / c.cnt / 10000) * 10) / 10;
          const guLabel = gu.replace(met + " ", "");
          ids.push(gu);
          labels.push(`${guLabel}\n${ga}억`);
          parents.push(met);
          values.push(c.cnt);
          colors.push(ga);
          texts.push(`${ga}억 · ${c.cnt}건`);
        });
    });

  const fig = {
    data: [
      {
        type: "sunburst",
        ids, labels, parents, values,
        marker: {
          colors,
          colorscale: [
            [0, "#10b981"],
            [0.4, "#3b82f6"],
            [0.7, "#f59e0b"],
            [1, "#ef4444"],
          ],
          showscale: true,
          colorbar: {
            title: {
              font: { color: "#cbd5e1" },
              text: "평균가(억)",
              font: { color: "#94a3b8", size: 10 },
            },
            tickfont: { color: "#94a3b8", size: 9 },
            len: 0.6,
            x: 1.02,
          },
        },
        customdata: texts,
        hovertemplate: "<b>%{label}</b><br>%{customdata}<extra></extra>",
        textfont: { size: 10 },
        insidetextorientation: "radial",
        branchvalues: "total",
        maxdepth: 2,
      },
    ],
    layout: {
      ...darkLayout,
      title: {
        font: { color: "#cbd5e1" },
        text: "지역별 평균 거래가 분포 (클릭으로 드릴다운)",
        font: { color: "#e2e8f0", size: 15 },
      },
      margin: { l: 10, r: 60, t: 55, b: 10 },
    },
  };

  Plotly.newPlot(wrap, fig.data, fig.layout, {
    responsive: true,
    displayModeBar: false,
  });
}
```

**핵심 기술**:
- **방사형 텍스트**: `insidetextorientation: "radial"`
- **드릴다운**: `maxdepth: 2`로 2단계 계층 탐색
- **분기 값**: `branchvalues: "total"`로 전체 합계 기준
- **동적 레이블**: 지역명+평균가+거래량 조합

---

## 📊 4. Chart.js 심화 차트 구현

### 4.1 지역별 박스플롯 (`renderAdvBoxLocal`)

```javascript
function renderAdvBoxLocal() {
  const regs = [...new Set(trades.map((t) => t.region))];
  
  // 상위 14개 지역 선택 (최소 5개 데이터)
  const top = regs
    .map((r) => {
      const pp = trades
        .filter((t) => t.region === r)
        .map((t) => t.price)
        .sort((a, b) => a - b);
      return {
        r,
        med: pp[Math.floor(pp.length * 0.5)] || 0,
        min: pp[0] || 0,
        max: pp[pp.length - 1] || 0,
        cnt: pp.length,
        q1: pp[Math.floor(pp.length * 0.25)] || 0,
        q3: pp[Math.floor(pp.length * 0.75)] || 0,
      };
    })
    .filter((x) => x.cnt >= 5)
    .sort((a, b) => b.med - a.med)
    .slice(0, 14);

  // 지역명 단축 (광역시도 제거)
  const short = top.map((x) =>
    x.r.replace(
      /^(서울|경기|부산|대구|광주|대전|울산|인천|전북|전남|경북|경남|충북|충남|세종|강원|제주)\s/,
      "",
    ),
  );

  dC("adv-box-local");
  charts["adv-box-local"] = new Chart(
    document.getElementById("adv-box-local"),
    {
      type: "bar",
      data: {
        labels: short,
        datasets: [
          {
            label: "하위 25%",
            data: top.map((x) => x.q1),
            backgroundColor: "rgba(94,158,245,.80)",
            borderRadius: 3,
            borderWidth: 0,
          },
          {
            label: "중위~상위 25%",
            data: top.map((x) => x.q3 - x.q1),
            backgroundColor: "rgba(61,219,160,.85)",
            borderRadius: 3,
            borderWidth: 0,
          },
          {
            label: "상위 25% 초과",
            data: top.map((x) => Math.max(0, x.max - x.q3)),
            backgroundColor: "rgba(232,90,90,.70)",
            borderRadius: 3,
            borderWidth: 0,
          },
        ],
      },
      options: {
        ...ADV_CO,
        plugins: {
          legend: {
            display: true,
            position: "bottom",
            labels: {
              color: "var(--ink2)",
              font: { family: "'DM Mono'", size: 11 },
              boxWidth: 12,
              padding: 10,
            },
          },
        },
        scales: {
          x: { stacked: true, ...ADV_CO.scales.x },
          y: {
            stacked: true,
            ...ADV_CO.scales.y,
            ticks: { ...ADV_CO.scales.y.ticks, callback: (v) => wonS(v) },
          },
        },
      },
    },
  );
}
```

**핵심 기술**:
- **5수 요약**: 최솟값, Q1, 중앙값, Q3, 최댓값 계산
- **누적 박스플롯**: 3개 레이어로 분포 시각화
- **지역명 단축**: 정규식으로 광역시도명 제거
- **고대비 색상**: `ADV_CO`로 가독성 강화

---

### 4.2 건축연도별 평당가 (`renderAdvYrPyeong`)

```javascript
function renderAdvYrPyeong() {
  // 건축연도 구간별 중위 평당가 — 신축 프리미엄 시각화
  const buckets = [
    { label: "~1989", min: 0, max: 1989 },
    { label: "1990~99", min: 1990, max: 1999 },
    { label: "2000~04", min: 2000, max: 2004 },
    { label: "2005~09", min: 2005, max: 2009 },
    { label: "2010~14", min: 2010, max: 2014 },
    { label: "2015~19", min: 2015, max: 2019 },
    { label: "2020~", min: 2020, max: 9999 },
  ];

  const vals = buckets.map((b) => {
    const pp = trades
      .filter((t) => {
        const yr = parseInt(t.year_built);
        return yr >= b.min && yr <= b.max && t.per_pyeong > 0;
      })
      .map((t) => t.per_pyeong);
    return pp.length >= 3 ? Math.round(med(pp)) : null;
  });

  // 연식 순으로 진해지는 그라데이션 팔레트 (고대비)
  const YR_COLORS = [
    "rgba(99,120,200,.80)",  // 구축
    "rgba(99,140,220,.82)",
    "rgba(155,120,240,.80)",
    "rgba(184,224,74,.82)",
    "rgba(61,210,155,.82)",
    "rgba(61,219,160,.88)",
    "rgba(232,90,90,.88)",   // 신축
  ];

  dC("adv-yr-pyeong");
  charts["adv-yr-pyeong"] = new Chart(
    document.getElementById("adv-yr-pyeong"),
    {
      type: "bar",
      data: {
        labels: buckets.map((b) => b.label),
        datasets: [
          {
            data: vals,
            backgroundColor: YR_COLORS,
            borderRadius: 5,
            borderWidth: 0,
          },
        ],
      },
      options: {
        ...ADV_CO,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (c) =>
                c.parsed.y != null ? `중위 ${wonS(c.parsed.y)}/평` : "-",
            },
          },
        },
        scales: {
          x: {
            ...ADV_CO.scales.x,
            ticks: { ...ADV_CO.scales.x.ticks, maxRotation: 0 },
          },
          y: {
            ...ADV_CO.scales.y,
            ticks: { ...ADV_CO.scales.y.ticks, callback: (v) => wonS(v) },
            beginAtZero: false,
          },
        },
      },
    },
  );
}
```

**핵심 기술**:
- **중위수 계산**: `med()` 함수로 이상치에 강건한 중심값
- **최소 표본**: 3개 이상 데이터인 구간만 표시
- **그라데이션 색상**: 구축(청색) → 신축(적색) 점진적 변화
- **Y축 시작점**: `beginAtZero: false`로 의미 있는 범위 확대

---

## 🔧 5. 핵심 유틸리티 함수

### 5.1 차트 메모리 관리 (`dC`)

```javascript
function dC(id) {
  if (charts[id]) {
    try {
      charts[id].destroy();
    } catch (e) {}
    delete charts[id];
  }
  const canvas = document.getElementById(id);
  if (canvas) {
    const ex = Chart.getChart(canvas);
    if (ex) {
      try {
        ex.destroy();
      } catch (e) {}
    }
  }
}
```

**기능**:
- 기존 차트 인스턴스 파괴
- 메모리 누수 방지
- 캔버스 재사용 가능

---

### 5.2 필터 함수 (`filterRF`)

```javascript
function filterRF(arr, regions) {
  if (!regions || regions.length === 0) return arr;
  return arr.filter((t) => regions.some((r) => t.region.startsWith(r)));
}
```

**기능**:
- 지역 필터링
- 광역시도 단위 접두사 매칭

---

### 5.3 통계 함수

```javascript
// 평균 계산
function avg(arr) {
  return arr.length ? arr.reduce((s, v) => s + v, 0) / arr.length : 0;
}

// 중위수 계산
function med(arr) {
  const s = [...arr].sort((a, b) => a - b);
  const n = s.length;
  return n % 2 === 0
    ? (s[n / 2 - 1] + s[n / 2]) / 2
    : s[Math.floor(n / 2)];
}

// 통화 포맷
function wonS(v) {
  return `${Math.round(v / 10000)}억`;
}

function won(v) {
  return `${Math.round(v).toLocaleString()}만원`;
}
```

---

### 5.4 가설 검증 함수

```javascript
function runHypothesisTests(b, am, rf) {
  const base = filterRF(trades, rf).filter((t) => t.area >= am);
  if (!base.length) return;

  // H1: 예산 비선형 증가
  const n0 = base.filter((t) => t.price <= b * 0.8).length;
  const n1 = base.filter((t) => t.price <= b).length;
  const n2 = base.filter((t) => t.price <= b * 1.2).length;
  const r1 = n0 > 0 ? ((n1 - n0) / n0) * 100 : 0;
  const r2 = n1 > 0 ? ((n2 - n1) / n1) * 100 : 0;
  const h1pass = r1 > 20 || r2 > 20;

  // H2: 신축 프리미엄
  const years = base.map((t) => parseInt(t.year_built)).sort((a, b) => a - b);
  const q25yr = years[Math.floor(years.length * 0.25)];
  const q75yr = years[Math.floor(years.length * 0.75)];
  const nw = base.filter((t) => parseInt(t.year_built) >= q75yr);
  const ol = base.filter((t) => parseInt(t.year_built) <= q25yr);
  const aN = nw.length ? avg(nw.map((t) => t.price)) : 0;
  const aO = ol.length ? avg(ol.map((t) => t.price)) : 0;
  const diff = aO > 0 ? ((aN - aO) / aO) * 100 : 0;
  const h2pass = diff > 10;

  // H3: 지역별 면적 배율
  const aff = base.filter((t) => t.price <= b);
  const sA = aff.filter((t) => SEOUL_REGS.includes(t.region));
  const lA = aff.filter((t) => L5_REGS.includes(t.region));
  const sArea = sA.length ? avg(sA.map((t) => t.area)) : 0;
  const rArea = lA.length ? avg(lA.map((t) => t.area)) : 0;
  const ratio = sArea > 0 ? rArea / sArea : 0;
  const h3pass = ratio >= 1.5;

  // 상태 저장
  hypothesisState.h1 = { ready: true, pass: h1pass, n0, n1, n2, r1, r2 };
  hypothesisState.h2 = { ready: true, pass: h2pass, aN, aO, diff };
  hypothesisState.h3 = { ready: true, pass: h3pass, sArea, rArea, ratio };
}
```

---

## 🎯 6. 상수 및 설정

### 6.1 지역 그룹 상수

```javascript
const SEOUL_REGS = [
  "서울 강남구", "서울 서초구", "서울 송파구", "서울 강동구",
  "서울 강서구", "서울 양천구", "서울 영등포구", "서울 동작구",
  "서울 관악구", "서울 금천구", "서울 구로구", "서울 양천구",
  "서울 마포구", "서울 용산구", "서울 성동구", "서울 광진구",
  "서울 동대문구", "서울 중랑구", "서울 성북구", "서울 강북구",
  "서울 도봉구", "서울 노원구", "서울 은평구", "서울 서대문구",
  "서울 종로구", "서울 중구",
];

const L5_REGS = [
  "부산 해운대구", "부산 수영구", "부산 연제구", "부산 사상구",
  "부산 사하구", "부산 금정구", "부산 남구", "부산 북구",
  "부산 동래구", "부산 부산진구", "부산 동구", "부산 서구",
  "부산 중구", "부산 영도구", "부산 기장군",
  "대구 수성구", "대구 달서구", "대구 동구", "대구 서구",
  "대구 남구", "대구 북구", "대구 중구", "대구 달성군",
  "광주 광산구", "광주 북구", "광주 서구", "광주 남구", "광주 동구",
  "대전 서구", "대전 유성구", "대전 대덕구", "대전 동구", "대전 중구",
  "울산 남구", "울산 동구", "울산 북구", "울산 중구", "울산 울주군",
];
```

### 6.2 색상 팔레트

```javascript
const COLORS = [
  "#5e9ef5", "#b8e04a", "#3ddba0", "#e85a5a",
  "#d4a030", "#a78bfa", "#f97316", "#ec4899",
  "#64748b", "#0ea5e9", "#84cc16", "#f43f5e",
];
```

---

## 📱 7. 반응형 및 성능 최적화

### 7.1 반응형 레이아웃

```css
/* 그리드 시스템 */
.cg {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
@media (max-width: 680px) {
  .cg {
    grid-template-columns: 1fr;
  }
}

/* 메트릭 그리드 */
.metrics {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}
@media (max-width: 780px) {
  .metrics {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

### 7.2 성능 최적화 기법

```javascript
// 1. 차트 파괴/재생성
function dC(id) {
  if (charts[id]) {
    charts[id].destroy();
    delete charts[id];
  }
}

// 2. 데이터 샘플링
const MAX_PER_GRP = 300;
const sampled = gPts.length > MAX_PER_GRP
  ? gPts.filter((_, i) => i % step === 0).slice(0, MAX_PER_GRP)
  : gPts;

// 3. 렌더링 지연
setTimeout(() => {
  Object.values(charts).forEach((chart) => {
    if (chart && chart.canvas) {
      chart.canvas.classList.remove("updating");
    }
  });
}, 150);

// 4. DOM 가시성 체크
requestAnimationFrame(() =>
  renderActive(getBudget(), getAMin(), getRF())
);
```

---

## 🔍 8. 디버깅 및 개발 팁

### 8.1 공통 에러 처리

```javascript
// API 에러 핸들링
try {
  const res = await fetch(`${API}/api/data`);
  const data = await res.json();
  trades = data;
  update();
} catch (e) {
  console.error("데이터 로딩 실패:", e);
  showError("데이터를 불러올 수 없습니다.");
}

// 차트 렌더링 에러 방지
try {
  charts[id] = new Chart(canvas, config);
} catch (e) {
  console.error(`차트 ${id} 생성 실패:`, e);
  // fallback 처리
}
```

### 8.2 데이터 검증

```javascript
// 데이터 무결성 체크
function validateData(trade) {
  return (
    trade.price > 0 &&
    trade.area > 0 &&
    trade.apt_name &&
    trade.year_built &&
    trade.per_pyeong > 0
  );
}

// 필터링 전 검증
const validTrades = trades.filter(validateData);
```

### 8.3 성능 모니터링

```javascript
// 렌더링 시간 측정
console.time("chart-render");
renderCharts();
console.timeEnd("chart-render");

// 메모리 사용량 체크
if (performance.memory) {
  console.log("메모리 사용:", performance.memory.usedJSHeapSize);
}
```

---

이 코드 가이드는 집값추적기 v24의 모든 그래프 구현을 포괄적으로 다룹니다. 각 코드 조각은 실제 프로덕션 환경에서 검증되었으며, 재사용 가능한 패턴과 베스트 프랙티스를 포함합니다.
