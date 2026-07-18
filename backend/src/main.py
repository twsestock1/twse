from fastapi import FastAPI
from src.database import get_connection
from src.parameter_store import get_parameters

app = FastAPI()

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
            FROM stockslist;
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