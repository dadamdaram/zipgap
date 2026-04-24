"""SQLite 데이터베이스 관리 v3"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "realestate.db"


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                apt_name    TEXT,
                area        REAL,
                floor       TEXT,
                price       INTEGER,
                year_built  TEXT,
                deal_year   TEXT,
                deal_month  TEXT,
                deal_day    TEXT,
                region      TEXT,
                dong        TEXT,
                per_pyeong  REAL,
                created_at  TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_price  ON trades(price);
            CREATE INDEX IF NOT EXISTS idx_region ON trades(region);
            CREATE INDEX IF NOT EXISTS idx_area   ON trades(area);
            CREATE INDEX IF NOT EXISTS idx_deal   ON trades(deal_year, deal_month);

            CREATE TABLE IF NOT EXISTS watchlist (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                label      TEXT,
                budget_min INTEGER DEFAULT 0,
                budget_max INTEGER,
                area_min   REAL,
                area_max   REAL,
                regions    TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
    print(f"[DB] Initialized: {DB_PATH}")


def clear_and_insert(trades: list[dict]):
    with get_conn() as conn:
        conn.execute("DELETE FROM trades")
        conn.executemany("""
            INSERT INTO trades
              (apt_name,area,floor,price,year_built,deal_year,deal_month,deal_day,region,dong,per_pyeong)
            VALUES
              (:apt_name,:area,:floor,:price,:year_built,:deal_year,:deal_month,:deal_day,:region,:dong,:per_pyeong)
        """, trades)
    print(f"[DB] Inserted {len(trades)} records")


def query_all(limit: int = 5000) -> list[dict]:
    """분석에 충분한 수준으로 limit 적용 (기본 5000건, 0이면 전체)"""
    with get_conn() as conn:
        if limit and limit > 0:
            rows = conn.execute(
                "SELECT * FROM trades ORDER BY RANDOM() LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM trades ORDER BY price").fetchall()
    return [dict(r) for r in rows]


def query_affordable(
    budget_min: int, budget_max: int,
    area_min: float, area_max: float,
    regions: list[str] | None = None,
    limit: int = 200,
) -> list[dict]:
    params: list = [budget_min, budget_max, area_min, area_max]
    region_clause = ""
    if regions:
        placeholders = ",".join("?" * len(regions))
        region_clause = f"AND region IN ({placeholders})"
        params += regions
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(f"""
            SELECT * FROM trades
            WHERE price BETWEEN ? AND ?
              AND area BETWEEN ? AND ?
              {region_clause}
            ORDER BY price ASC
            LIMIT ?
        """, params).fetchall()
    return [dict(r) for r in rows]


def query_summary(budget_max: int, area_min: float = 0) -> dict:
    with get_conn() as conn:
        row = conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN price <= :b THEN 1 ELSE 0 END) AS affordable,
                ROUND(AVG(price), 0)      AS avg_price,
                MIN(price)                AS min_price,
                MAX(price)                AS max_price,
                ROUND(AVG(per_pyeong),0)  AS avg_per_pyeong
            FROM trades WHERE area >= :a
        """, {"b": budget_max, "a": area_min}).fetchone()
    return dict(row) if row else {}
