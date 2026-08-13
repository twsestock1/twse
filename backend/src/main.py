from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.database import get_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kuguge.com",
        "http://kuguge.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def hello():
    return {"msg": "hello"}
# 檢查Deploy後, API是否正常運作
@app.get("/health")
def health():
    return {"status": "ok"}
# 測試後端可不可以呼叫PostgreSQL資料庫
@app.get("/db-test")
def db_test():

    conn = None
    cur = None

    try:
        conn = get_connection()

        cur = conn.cursor()

        cur.execute("""
            SELECT *
            FROM stocklist;
        """)

        rows = cur.fetchall()

        return {
            "status": "success",
            "data": rows
        }

    except Exception as e:

        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()

@app.get("/stocks")
def search_stock(keyword: str = Query(..., description="股票代號或名稱")):

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        sql = """
        SELECT
            "證券代號",
            "證券名稱",
            "市場別",
            "有價證券別",
            "產業別",
            "上市日期"
        FROM stocklist
        WHERE
            "證券代號" = %s
            OR
            "證券名稱" ILIKE %s
        ORDER BY "證券代號";
        """

        cur.execute(
            sql,
            (
                keyword,
                f"{keyword}%"
            )
        )

        rows = cur.fetchall()

        data = []

        for row in rows:

            data.append({

                "stock_code": row[0],
                "stock_name": row[1],
                "market": row[2],
                "security_type": row[3],
                "industry": row[4],
                "listed_date": str(row[5]) if row[5] else None

            })

        return {

            "count": len(data),
            "data": data

        }

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

@app.get("/stocks/{stock_code}")
def get_stock(stock_code: str):

    conn = None
    cur = None

    try:

        conn = get_connection()
        cur = conn.cursor()

        sql = """
        SELECT
            "證券代號",
            "證券名稱",
            "市場別",
            "有價證券別",
            "產業別",
            "上市日期"
        FROM stocklist
        WHERE
            "證券代號" = %s
        """

        cur.execute(sql, (stock_code,))

        row = cur.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Stock not found"
            )

        return {

            "stock_code": row[0],
            "stock_name": row[1],
            "market": row[2],
            "security_type": row[3],
            "industry": row[4],
            "listed_date": str(row[5]) if row[5] else None

        }

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()

# 測試新資料庫連線狀態
@app.get("/api/stocks/search")
def search_stocks(
    keyword: str = Query(..., min_length=1)
):

    sql = """
        SELECT
            "證券代號",
            "證券名稱",
            "市場別",
            "有價證券別",
            "產業別",
            "上市日期"
        FROM stocklist
        WHERE
            "證券代號" ILIKE %s
            OR "證券名稱" ILIKE %s
        ORDER BY "證券代號";
    """

    search_keyword = f"%{keyword}%"

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                sql,
                (search_keyword, search_keyword)
            )

            rows = cur.fetchall()

    return [
        {
            "證券代號": row[0],
            "證券名稱": row[1],
            "市場別": row[2],
            "有價證券別": row[3],
            "產業別": row[4],
            "上市日期": row[5]
        }
        for row in rows
    ]