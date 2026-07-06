from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello():
    return {"msg": "hello"}
# 檢查Deploy後, API是否正常運作
@app.get("/health")
def health():
    return {"status": "ok"}