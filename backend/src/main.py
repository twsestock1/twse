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

# 測試新資料庫連線狀態
@app.get("/stocks/search")
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
        FROM public.stocklist
        WHERE
            "證券代號" ILIKE %s
            OR "證券名稱" ILIKE %s
        ORDER BY "證券代號";
    """

    search_keyword = f"%{keyword}%"

    with get_connection() as conn:

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