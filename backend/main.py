"""
집값추적기 FastAPI 서버 v5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
성능 개선:
  - 시작 시 블로킹 없이 백그라운드로 데이터 수집
  - /api/status 로 진행률 실시간 조회
  - 결과 즉시 캐싱, 추가 수집 완료 시 점진 교체
"""
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import sys, asyncio, time, threading

sys.path.append(str(Path(__file__).parent.parent))

from backend.config import MOLIT_API_KEY, DEFAULT_MONTHS, DEFAULT_METROS
from backend.database import init_db, clear_and_insert, query_all, query_affordable, query_summary
from backend.crawler import generate_sample_data, fetch_all, fetch_molit
from backend.regions import REGION_CODES, METRO_GROUPS, AREA_TYPES

app = FastAPI(title="집값추적기 API v5", version="5.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# ── 전역 상태 ──────────────────────────────────────────────────
_state = {
    "loading": False,
    "progress": 0,          # 0~100
    "progress_msg": "",
    "has_real_key": False,
    "key_preview": "",
    "total_trades": 0,
    "error": "",
}
_current_key: str = MOLIT_API_KEY


def _validate_key(key: str) -> bool:
    if not key or key == "여기에_발급받은_인증키_입력":
        return False
    stripped = key.strip()
    return len(stripped) >= 20 and " " not in stripped


def _update_trade_count():
    from backend.database import get_conn
    try:
        with get_conn() as conn:
            c = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        _state["total_trades"] = c
    except:
        pass


# ── 백그라운드 수집 (논블로킹) ─────────────────────────────────
def _bg_collect(api_key: str, metros=None, months=3, replace=True):
    """별도 스레드에서 실행 — ThreadPoolExecutor로 병렬 수집"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime
    global _current_key
    _state["loading"] = True
    _state["progress"] = 5
    _state["progress_msg"] = "API 연결 중..."
    _state["error"] = ""

    try:
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
                year_offset = now.year + (month_offset - 1) // 12
                month_val = ((month_offset - 1) % 12) + 1
                ym = f"{year_offset}{str(month_val).zfill(2)}"
                tasks.append((region, code, ym))

        total = len(tasks)
        done = 0
        collected = []
        lock = threading.Lock()

        def _fetch(task):
            region, code, ym = task
            trades = fetch_molit(code, ym, api_key)
            for t in trades:
                t["region"] = region
            print(f"  [{region}] {ym} -> {len(trades)}건")
            return trades

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {executor.submit(_fetch, t): t for t in tasks}
            for future in as_completed(futures):
                try:
                    batch = future.result()
                    with lock:
                        collected.extend(batch)
                        done += 1
                        pct = int(10 + done / total * 85)
                        _state["progress"] = min(pct, 95)
                        _state["progress_msg"] = f"{done}/{total} 완료 ({len(collected):,}건 수집됨)"
                        # 200건 이상이면 즉시 DB 반영 (점진적 UI 업데이트)
                        if len(collected) >= 200 and done % 10 == 0:
                            clear_and_insert(collected[:])
                            _update_trade_count()
                except Exception as e:
                    print(f"[fetch 오류] {futures[future]}: {e}")

        if collected:
            clear_and_insert(collected)
            _update_trade_count()
            _current_key = api_key
            _state["has_real_key"] = True
            _state["key_preview"] = api_key[:8] + "…"
        else:
            _state["error"] = "수집된 데이터가 없습니다. API 키를 확인하세요."

    except Exception as e:
        _state["error"] = str(e)
        print(f"[BG collect error] {e}")
    finally:
        _state["loading"] = False
        _state["progress"] = 100
        _state["progress_msg"] = f"완료 — {_state['total_trades']:,}건"


# ── 시작 이벤트 ────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()
    _update_trade_count()

    if _validate_key(_current_key):
        print(f"[Startup] 실거래 API 키 감지 → 샘플 먼저 로드 후 백그라운드 전국 수집 시작")
        # 샘플 먼저 로드 → 서버 즉시 응답 가능
        sample = generate_sample_data()
        clear_and_insert(sample)
        _update_trade_count()
        _state["progress_msg"] = "샘플 데이터 로드됨, 실거래 수집 중..."
        # 백그라운드에서 전국 실거래 수집 (무조건 실행 — 기존 데이터 여부 무관)
        t = threading.Thread(target=_bg_collect, args=(_current_key,), daemon=True)
        t.start()
    else:
        print("[Startup] API 키 없음 → 샘플 데이터 로드")
        if _state["total_trades"] == 0:
            sample = generate_sample_data()
            clear_and_insert(sample)
            _update_trade_count()
        _state["progress"] = 100
        _state["progress_msg"] = f"샘플 데이터 {_state['total_trades']}건"


# ── 상태 ───────────────────────────────────────────────────────
@app.get("/api/status")
def status():
    _update_trade_count()
    return {**_state, "total_trades": _state["total_trades"]}


# ── 메타 ───────────────────────────────────────────────────────
@app.get("/api/meta")
def get_meta():
    return {
        "region_codes": REGION_CODES,
        "metro_groups": METRO_GROUPS,
        "area_types": AREA_TYPES,
        "has_real_key": _state["has_real_key"],
    }


# ── 데이터 (페이지네이션 지원) ──────────────────────────────────
@app.get("/api/data")
def get_data(
    limit: int = Query(40),
    offset: int = Query(0),
    price_min: int = Query(0),
    price_max: int = Query(999999999),
    area_min: float = Query(0),
    area_max: float = Query(9999),
    regions: str = Query(""),
    sort: str = Query("price_asc"),
    q: str = Query(""),
    year_min: int = Query(0),
    months: int = Query(0)
):
    """서버사이드 필터링 + 정렬 + 페이지네이션"""
    from backend.database import get_conn
    
    region_list = [r.strip() for r in regions.split(",") if r.strip()] if regions else None
    
    where = ["price BETWEEN ? AND ?", "area BETWEEN ? AND ?", "CAST(year_built AS INTEGER) >= ?"]
    params: list = [price_min, price_max, area_min, area_max, year_min]
    
    if q:
        where.append("(apt_name LIKE ? OR region LIKE ? OR dong LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
        
    if region_list:
        ph = ",".join("?" * len(region_list))
        where.append(f"region IN ({ph})")
        params.extend(region_list)
        
    if months > 0:
        import datetime
        now = datetime.datetime.now()
        y, m = now.year, now.month - months
        while m <= 0:
            m += 12
            y -= 1
        ym = f"{y}{m:02d}"
        where.append("printf('%04d%02d', deal_year, deal_month) >= ?")
        params.append(ym)

    where_str = " AND ".join(where)
    sort_map = {
        "price_asc": "price ASC",
        "price_desc": "price DESC",
        "area_desc": "area DESC",
        "pyeong_asc": "per_pyeong ASC",
        "year_desc": "year_built DESC",
        "date_desc": "deal_year DESC, deal_month DESC, deal_day DESC",
    }
    order = sort_map.get(sort, "price ASC")
    
    with get_conn() as conn:
        stats = conn.execute(f"SELECT COUNT(*), AVG(price), MIN(price), AVG(per_pyeong) FROM trades WHERE {where_str}", params).fetchone()
        
        region_stats_rows = conn.execute(f"SELECT region, COUNT(*), AVG(price), MIN(price), AVG(per_pyeong) FROM trades WHERE {where_str} GROUP BY region", params).fetchall()
        region_stats = [
            {"region": r[0], "count": r[1] or 0, "avg_price": r[2] or 0, "min_price": r[3] or 0, "avg_pyeong": r[4] or 0}
            for r in region_stats_rows
        ]
        
        if limit == 0:
            rows = conn.execute(f"SELECT * FROM trades WHERE {where_str} ORDER BY {order}", params).fetchall()
        else:
            rows = conn.execute(f"SELECT * FROM trades WHERE {where_str} ORDER BY {order} LIMIT ? OFFSET ?", params + [limit, offset]).fetchall()
            
    return {
        "trades": [dict(r) for r in rows],
        "stats": {
            "count": stats[0] or 0,
            "avg_price": stats[1] or 0,
            "min_price": stats[2] or 0,
            "avg_pyeong": stats[3] or 0
        },
        "region_stats": region_stats,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/summary")
def get_summary(budget: int = Query(...), area_min: float = Query(0)):
    return query_summary(budget, area_min)


@app.get("/api/affordable")
def get_affordable(
    budget_min: int = Query(0),
    budget_max: int = Query(...),
    area_min: float = Query(0),
    area_max: float = Query(9999),
    regions: str = Query(""),
    limit: int = Query(200),
):
    rl = [r.strip() for r in regions.split(",") if r.strip()] if regions else None
    items = query_affordable(budget_min, budget_max, area_min, area_max, rl, limit)
    return {"count": len(items), "items": items}


# ── 단지 상세 ──────────────────────────────────────────────────
@app.get("/api/complex/{apt_name}")
def get_complex(apt_name: str, region: str = Query("")):
    """단지명으로 해당 단지의 전체 거래 이력 조회"""
    from backend.database import get_conn
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM trades
            WHERE apt_name = ?
            AND (? = '' OR region = ?)
            ORDER BY deal_year DESC, deal_month DESC
            LIMIT 100
        """, (apt_name, region, region)).fetchall()
    trades_list = [dict(r) for r in rows]
    if not trades_list:
        return {"apt_name": apt_name, "trades": [], "stats": {}}
    
    prices = [t["price"] for t in trades_list]
    areas = [t["area"] for t in trades_list]
    return {
        "apt_name": apt_name,
        "region": region,
        "trades": trades_list,
        "stats": {
            "trade_count": len(trades_list),
            "price_min": min(prices),
            "price_max": max(prices),
            "price_avg": round(sum(prices) / len(prices)),
            "area_min": min(areas),
            "area_max": max(areas),
            "latest_deal": f"{trades_list[0]['deal_year']}.{trades_list[0]['deal_month']}.{trades_list[0]['deal_day']}",
        }
    }


# ── 크롤링 ─────────────────────────────────────────────────────
@app.post("/api/crawl/auto")
def crawl_auto(
    metros: str = Query(""),
    months: int = Query(DEFAULT_MONTHS),
    api_key: str = Query(""),
):
    global _current_key
    key = api_key.strip() or (_current_key if _state["has_real_key"] else None)
    
    if not key or not _validate_key(key):
        return {"message": "유효한 API 키가 없습니다.", "count": 0, "ok": False}
    
    # 동일 키로 이미 수집 중이면 중복 실행 방지
    if _state["loading"] and key == _current_key:
        return {"message": "이미 수집 중입니다.", "count": _state["total_trades"], "ok": True}
    
    mts = [m.strip() for m in metros.split(",") if m.strip()] or None
    _current_key = key
    
    t = threading.Thread(target=_bg_collect, args=(key, mts, months), daemon=True)
    t.start()
    
    # 2초 대기 후 현재까지 수집된 건수 반환 (빠른 응답)
    import time; time.sleep(2)
    _update_trade_count()
    return {
        "message": f"수집 시작됨 ({_state['total_trades']:,}건 로드)",
        "count": _state["total_trades"],
        "ok": True,
        "loading": _state["loading"],
    }


@app.post("/api/crawl/sample")
def crawl_sample():
    data = generate_sample_data()
    clear_and_insert(data)
    _update_trade_count()
    _state["has_real_key"] = False
    _state["key_preview"] = ""
    return {"message": f"샘플 {_state['total_trades']}건 로드", "count": _state["total_trades"]}


@app.post("/api/key/update")
def update_key(new_key: str = Query(...)):
    global _current_key
    if not _validate_key(new_key.strip()):
        return {"ok": False, "message": "유효하지 않은 키 형식 (20자 이상)"}
    
    key = new_key.strip()
    _current_key = key
    
    if _state["loading"]:
        return {"ok": False, "message": "현재 수집 중입니다. 잠시 후 시도하세요."}
    
    t = threading.Thread(target=_bg_collect, args=(key,), daemon=True)
    t.start()
    
    import time; time.sleep(2)
    _update_trade_count()
    return {
        "ok": True,
        "message": f"수집 시작됨 ({_state['total_trades']:,}건)",
        "count": _state["total_trades"],
        "key_preview": key[:8] + "…",
        "loading": _state["loading"],
    }



# ── 프론트엔드 서빙 ────────────────────────────────────────────
fp = Path(__file__).parent.parent / "frontend"
if fp.exists():
    app.mount("/", StaticFiles(directory=str(fp), html=True), name="static")
