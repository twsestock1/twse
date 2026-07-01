from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def say_hello(name: str):

    if name.strip() == "":
        return {
            "error": "名字不能為空"
        }

    return {
        "message": f"Hello, {name}"
    }