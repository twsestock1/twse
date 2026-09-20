from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

from datetime import date, timedelta
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.database import get_connection


# 建立 FastAPI App
app = FastAPI()

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://kuguge.com",
        "http://kuguge.com",
        #"http://localhost:5500",
        #"http://127.0.0.1:5500",
    ],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
    )

# 個股歷史股價查詢
@app.get("/stocks/history")
def stockprice_history(
        keyword: str = Query(...,min_length=1,max_length=50,description="輸入證券代號"),
        start_date: date | None = None,
        end_date: date | None = None
        ):
    # ---------------------------
    # 日期設定
    # ---------------------------
    if end_date is None :
        end_date = date.today()
    if start_date is None :
        start_date = end_date - timedelta(days=365)
    if start_date > end_date :
        raise HTTPException(
            status_code = 400,
            detail = "開始日期不能晚於結束日期"
        )
    
    # 建立模糊搜尋關鍵字
    search_keyword = f"%{keyword}%"

    with get_connection() as conn:
        with conn.cursor() as cur:
            #------------------------
            # 查詢證券代號 / 證券名稱
            #------------------------
            stock_sql = """
                SELECT "證券系統編碼","證券代號","證券名稱" FROM public.stocklist
                WHERE "證券代號" ILIKE %s OR "證券名稱" ILIKE %s
                ORDER BY "證券代號"
            """
            cur.execute(stock_sql,(search_keyword, search_keyword))
            stock = cur.fetchone()
            if stock is None:
                raise HTTPException(
                    status_code = 404,
                    detail = "沒有證券資料"
                )
            #------------------------
            # 查詢歷史股價
            #------------------------
            history_price_sql = """
            SELECT * FROM public.stockprice
            WHERE "證券系統編碼" = %s AND "交易日期" BETWEEN %s AND %s
            ORDER BY "交易日期" DESC
            """
            cur.execute(history_price_sql,(stock["證券系統編碼"],start_date,end_date))
            rows = cur.fetchall()
            result = [
                {
                    "交易日期": row["交易日期"].isoformat(),
                    "證券系統編碼": row["證券系統編碼"],
                    "證券代號": row["證券代號"],
                    "證券名稱": row["證券名稱"],
                    "開盤價": float(row["開盤價"]) if row["開盤價"] is not None else None,
                    "最高價": float(row["最高價"]) if row["最高價"] is not None else None,
                    "最低價": float(row["最低價"]) if row["最低價"] is not None else None,
                    "收盤價": float(row["收盤價"]) if row["收盤價"] is not None else None,
                    "成交金額": int(row["成交金額"]) if row["成交金額"] is not None else None,
                    "成交股數": int(row["成交股數"]) if row["成交股數"] is not None else None
                }
                for row in rows
            ]
            # --------------------------------------
            # 回傳結果
            # --------------------------------------

            return {

                "股票": {
                    "證券系統編碼": stock["證券系統編碼"],
                    "證券代號": stock["證券代號"],
                    "證券名稱": stock["證券名稱"]
                },

                "日期區間": {
                    "開始日期": start_date.isoformat(),
                    "結束日期": end_date.isoformat()
                },

                "資料筆數": len(result),

                "資料": result
            }