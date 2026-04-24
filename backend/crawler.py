"""
크롤러 v4 — config.py 의 API 키를 자동으로 사용
"""
import requests
import random
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
from typing import Optional

from backend.config import MOLIT_API_KEY
from backend.regions import REGION_CODES, METRO_GROUPS

MOLIT_URL = (
    "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev"
    "/getRTMSDataSvcAptTradeDev"
)


# ── 국토부 실거래가 API ──────────────────────────────────────────
def fetch_molit(
    region_code: str,
    ym: str,
    api_key: str | None = None,
) -> list[dict]:
    """
    국토부 아파트 실거래가 API 호출.
    api_key 생략 시 config.py 의 MOLIT_API_KEY 자동 사용.
    """
    key = api_key or MOLIT_API_KEY
    params = {
        "serviceKey": key,
        "LAWD_CD":    region_code,
        "DEAL_YMD":   ym,
        "numOfRows":  100,
        "pageNo":     1,
    }
    try:
        res = requests.get(MOLIT_URL, params=params, timeout=10)
        res.raise_for_status()
        return _parse_xml(res.text)
    except Exception as e:
        print(f"[API Error] {region_code} {ym}: {e}")
        return []


def _parse_xml(xml_text: str) -> list[dict]:
    """
    국토부 실거래가 API는 영문 태그로 응답합니다.
    dealAmount, excluUseAr, aptNm, floor, buildYear, dealYear, dealMonth, dealDay, umdNm
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        print(f"[XML ParseError] 응답 앞부분: {xml_text[:300]}")
        return []

    # 에러 응답 체크
    result_code = root.findtext(".//resultCode") or root.findtext(".//errCd") or ""
    result_msg  = root.findtext(".//resultMsg") or root.findtext(".//errMsg") or ""
    if result_code and result_code not in ("00", "0", "000", ""):
        print(f"[API 에러] code={result_code} msg={result_msg} xml앞부분={xml_text[:200]}")
        return []

    items = []
    for item in root.iter("item"):
        def g(tag):
            el = item.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        try:
            # ── 영문 태그 우선, 한글 태그 폴백 ──────────────────
            raw_price = g("dealAmount") or g("거래금액")
            raw_area  = g("excluUseAr") or g("전용면적")

            if not raw_price or not raw_area:
                continue

            price = int(raw_price.replace(",", "").replace(" ", ""))
            area  = float(raw_area)
            if price <= 0 or area <= 0:
                continue

            apt_name = g("aptNm") or g("아파트")
            if not apt_name:            # 단지명 결측 → 스킵
                continue
            if not (1.0 <= area <= 500.0):  # 비현실적 면적 이상치 제거
                continue
            if price < 1_000 or price > 1_000_000:  # 100만~100억 범위 외 스킵
                continue

            items.append({
                "apt_name":   apt_name,
                "area":       area,
                "floor":      g("floor")     or g("층"),
                "price":      price,
                "year_built": g("buildYear") or g("건축년도"),
                "deal_year":  g("dealYear")  or g("년"),
                "deal_month": g("dealMonth") or g("월"),
                "deal_day":   g("dealDay")   or g("일"),
                "dong":       g("umdNm")     or g("법정동"),
                "per_pyeong": round(price / (area / 3.3)),
            })
        except Exception as e:
            print(f"[item 파싱 오류] {e}")
            continue

    # IQR 기반 per_pyeong 이상치 제거 (±3 IQR 초과 제거)
    if len(items) >= 10:
        pps = sorted(i["per_pyeong"] for i in items)
        q1, q3 = pps[len(pps)//4], pps[len(pps)*3//4]
        iqr = q3 - q1
        lo, hi = q1 - 3 * iqr, q3 + 3 * iqr
        items = [i for i in items if lo <= i["per_pyeong"] <= hi]

    return items


# ── 전국 자동 수집 (병렬) ────────────────────────────────────────
def fetch_all(
    metros: list[str] | None = None,
    months: int = 3,
    api_key: str | None = None,
) -> list[dict]:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    target_metros = metros or list(METRO_GROUPS.keys())
    target_regions: list[str] = []
    for m in target_metros:
        target_regions.extend(METRO_GROUPS.get(m, []))

    now = datetime.now()
    tasks: list[tuple[str, str, str]] = []
    for region in target_regions:
        code = REGION_CODES.get(region)
        if not code:
            continue
        for i in range(months):
            month_offset = now.month - i
            year_offset  = now.year + (month_offset - 1) // 12
            month_val    = ((month_offset - 1) % 12) + 1
            ym = f"{year_offset}{str(month_val).zfill(2)}"
            tasks.append((region, code, ym))

    results: list[dict] = []

    def _fetch(task):
        region, code, ym = task
        trades = fetch_molit(code, ym, api_key)
        for t in trades:
            t["region"] = region
        print(f"  [{region}] {ym} -> {len(trades)}건")
        return trades

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(_fetch, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                print(f"[fetch 오류] {futures[future]}: {e}")

    return results


# ── 샘플 데이터 (API 키 없을 때 fallback) ───────────────────────
REGION_BASE_PYEONG: dict[str, int] = {
    "서울 강남구":8500,"서울 서초구":8200,"서울 송파구":7000,"서울 용산구":7500,
    "서울 성동구":6500,"서울 마포구":5800,"서울 광진구":5200,"서울 영등포구":4800,
    "서울 강서구":4200,"서울 양천구":4500,"서울 동작구":5000,"서울 관악구":3800,
    "서울 종로구":5500,"서울 중구":5200,"서울 은평구":3600,"서울 서대문구":4000,
    "서울 노원구":3000,"서울 도봉구":2800,"서울 강북구":2700,"서울 성북구":3200,
    "서울 중랑구":2900,"서울 동대문구":3400,"서울 금천구":3200,"서울 구로구":3400,
    "서울 강동구":5500,
    # 경기 전체
    "경기 수원시 장안구":2200,"경기 수원시 권선구":2000,"경기 수원시 팔달구":2100,
    "경기 수원시 영통구":2500,"경기 성남시 수정구":2800,"경기 성남시 중원구":2600,
    "경기 성남시 분당구":4800,"경기 의정부시":1600,"경기 안양시 만안구":2200,
    "경기 안양시 동안구":2600,"경기 부천시":1800,"경기 광명시":2800,"경기 평택시":1400,
    "경기 동두천시":900,"경기 안산시 상록구":1500,"경기 안산시 단원구":1400,
    "경기 고양시 덕양구":2000,"경기 고양시 일산동구":2300,"경기 고양시 일산서구":2100,
    "경기 과천시":5500,"경기 구리시":2200,"경기 남양주시":1700,"경기 오산시":1300,
    "경기 시흥시":1500,"경기 군포시":2000,"경기 의왕시":2400,"경기 하남시":3500,
    "경기 용인시 처인구":1600,"경기 용인시 기흥구":2400,"경기 용인시 수지구":2800,
    "경기 파주시":1400,"경기 이천시":1100,"경기 안성시":900,"경기 김포시":1600,
    "경기 화성시":2000,"경기 광주시":1800,"경기 양주시":1100,"경기 포천시":800,
    # 인천 전체
    "인천 중구":1500,"인천 동구":1200,"인천 미추홀구":1400,"인천 연수구":2200,
    "인천 남동구":1700,"인천 부평구":1500,"인천 계양구":1400,"인천 서구":1600,"인천 강화군":700,
    # 부산 전체
    "부산 중구":1500,"부산 서구":1300,"부산 동구":1200,"부산 영도구":1100,
    "부산 부산진구":1600,"부산 동래구":2000,"부산 남구":1800,"부산 북구":1200,
    "부산 해운대구":3000,"부산 사하구":1300,"부산 금정구":1400,"부산 강서구":1000,
    "부산 연제구":1700,"부산 수영구":2500,"부산 사상구":1200,"부산 기장군":1100,
    # 대구 전체
    "대구 중구":1600,"대구 동구":1400,"대구 서구":1100,"대구 남구":1200,
    "대구 북구":1300,"대구 수성구":2500,"대구 달서구":1500,"대구 달성군":1000,
    # 광주 전체
    "광주 동구":1000,"광주 서구":1200,"광주 남구":1100,"광주 북구":1100,"광주 광산구":1200,
    # 대전 전체
    "대전 동구":1000,"대전 중구":1100,"대전 서구":1300,"대전 유성구":1500,"대전 대덕구":1000,
    # 울산 전체
    "울산 중구":1100,"울산 남구":1300,"울산 동구":1000,"울산 북구":900,"울산 울주군":900,
    "세종 세종시":1800,
    # 충북 전체
    "충북 청주시 상당구":1000,"충북 청주시 서원구":1000,
    "충북 청주시 흥덕구":1100,"충북 청주시 청원구":900,"충북 충주시":800,"충북 제천시":700,
    # 충남 전체
    "충남 천안시 동남구":950,"충남 천안시 서북구":1000,"충남 공주시":700,"충남 아산시":900,
    # 전남 전체
    "전남 순천시":700,"전남 여수시":750,"전남 목포시":650,
    # 경북 전체
    "경북 포항시 남구":800,"경북 포항시 북구":750,"경북 경주시":700,"경북 구미시":750,
    # 경남 전체
    "경남 창원시 의창구":900,"경남 창원시 성산구":950,"경남 창원시 마산합포구":750,
    "경남 창원시 진해구":800,"경남 진주시":800,"경남 김해시":900,"경남 양산시":950,
    # 제주
    "제주 제주시":1500,"제주 서귀포시":1200,
    # 강원 전체 (신규 추가)
    "강원 춘천시":900,"강원 원주시":850,"강원 강릉시":800,"강원 동해시":650,
    "강원 태백시":550,"강원 속초시":900,"강원 삼척시":600,
}

AREA_BUCKETS = [
    (20,.04),(33,.08),(40,.06),(49,.10),(59,.18),(66,.10),
    (74,.12),(84,.16),(101,.08),(115,.04),(135,.02),(165,.015),(200,.005),
]

def _wa() -> float:
    areas, weights = zip(*AREA_BUCKETS)
    return float(random.choices(areas, weights=weights, k=1)[0])

def generate_sample_data(regions: list[str] | None = None, n: int = 35) -> list[dict]:
    if regions is None:
        regions = list(REGION_BASE_PYEONG.keys())
    apts = ["래미안","자이","힐스테이트","푸르지오","롯데캐슬","아이파크",
            "e편한세상","디에이치","더샵","호반베르디움","SK뷰","현대"]
    dongs = ["중앙동","신도시","중심지","신흥동","번동","주공","한빛마을","미사동","판교동"]
    results = []
    now = datetime.now()
    for region in regions:
        base = REGION_BASE_PYEONG.get(region, 1000)
        for _ in range(n):
            area      = _wa()
            yr        = random.randint(1992, 2024)
            fl        = random.randint(1, 40)
            af        = 1.0 - max(0.0, (2024-yr)/100*0.5)
            ff        = 1.0 + min(0.05, fl/1000)
            aaf       = 1.0 - max(0.0, (area-59)/1000*0.3)
            noise     = random.gauss(1.0, 0.09)
            price     = max(3_000, round(base*af*ff*aaf*noise*(area/3.3)/100)*100)
            mo        = random.randint(0, 23)
            d         = datetime(now.year, now.month, 1) - timedelta(days=mo*30)
            results.append({
                "apt_name":   f"{random.choice(apts)} {random.randint(1,20)}차",
                "area":       round(area, 2),
                "floor":      str(fl),
                "price":      price,
                "year_built": str(yr),
                "deal_year":  str(d.year),
                "deal_month": str(d.month).zfill(2),
                "deal_day":   str(random.randint(1,28)).zfill(2),
                "region":     region,
                "dong":       random.choice(dongs),
                "per_pyeong": round(price/(area/3.3)),
            })
    return sorted(results, key=lambda x: x["price"])
