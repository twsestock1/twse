import psycopg

from src.parameter_store import get_parameters


def get_connection():
    """
    建立 PostgreSQL 連線
    """

    db = get_parameters("/stock/prod/db")

    conn = psycopg.connect(
        host=db["host"],
        port=db["port"],
        database=db["name"],
        user=db["user"],
        password=db["password"]
    )

    return conn