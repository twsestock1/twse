from fastapi import FastAPI
from database import get_connection

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

    try:

        conn = get_connection()

        cur = conn.cursor()

        # 測試資料庫是否成功連線
        cur.execute("SELECT version();")

        version = cur.fetchone()[0]

        cur.close()
        conn.close()

        return {
            "status": "success",
            "postgres_version": version
        }

    except Exception as e:

        if conn:
            conn.close()

        return {
            "status": "failed",
            "error": str(e)
        }