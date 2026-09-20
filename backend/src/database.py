import psycopg
from psycopg.rows import dict_row
import os
from src.parameter_store import get_parameters


def get_connection():
    """
    建立 PostgreSQL 連線
    """

    # 本機開發環境
    if os.getenv("APP_ENV") == "local":

        return psycopg.connect(
            host="127.0.0.1",
            port=5432,
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            row_factory = dict_row
        )

    # 正式環境
    db = get_parameters("/stock/prod/db")

    return psycopg.connect(
        host=db["host"],
        port=db["port"],
        dbname=db["name"],
        user=db["user"],
        password=db["password"],
        row_factory = dict_row
    )