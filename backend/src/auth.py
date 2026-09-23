import re
import secrets
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr
from pwdlib import PasswordHash

from src.database import get_connection


# ============================================
# 1. 建立 Router
# ============================================

router = APIRouter(
    prefix="/auth",
    tags=["會員驗證"]
)


# ============================================
# 2. 建立密碼雜湊工具
# ============================================

password_hash = PasswordHash.recommended()


# ============================================
# 3. 建立簡單 Session Token 儲存區
# ============================================

sessions = {}


# ============================================
# 4. 定義「會員註冊」收到的資料格式
# ============================================

class RegisterRequest(BaseModel):

    username: str

    nickname: str

    email: EmailStr

    password: str

    phone: str | None = None


# ============================================
# 5. 定義「會員登入」收到的資料格式
# ============================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# ============================================
# 6. 取得目前登入會員的 user_id
# ============================================

def get_current_user_id(
    authorization: Optional[str] = Header(default=None)
):

    # ----------------------------------------
    # 6-1. 檢查是否有 Authorization Header
    # ----------------------------------------

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="請先登入會員"
        )


    # ----------------------------------------
    # 6-2. 確認格式是否為 Bearer Token
    #
    # 正確格式：
    # Authorization: Bearer xxxxx
    # ----------------------------------------

    if not authorization.startswith("Bearer "):

        raise HTTPException(
            status_code=401,
            detail="登入驗證格式錯誤"
        )


    # ----------------------------------------
    # 6-3. 取出真正的 Token
    # ----------------------------------------

    token = authorization[7:]


    # ----------------------------------------
    # 6-4. 確認 Token 是否存在於 sessions
    # ----------------------------------------

    user_id = sessions.get(token)


    if user_id is None:

        raise HTTPException(
            status_code=401,
            detail="登入狀態已失效，請重新登入"
        )


    # ----------------------------------------
    # 6-5. 驗證成功
    #
    # 回傳目前登入會員的 user_id
    # ----------------------------------------

    return user_id


# ============================================
# 7. 取得目前登入會員資料
#
# 這個函式可以被其他 API 使用
# ============================================

def get_current_user(
    user_id: int = Depends(get_current_user_id)
):

    with get_connection() as conn:

        with conn.cursor() as cur:

            # --------------------------------
            # 7-1. 查詢會員基本資料
            # --------------------------------

            cur.execute(
                """
                SELECT
                    user_id,
                    username,
                    nickname,
                    email,
                    phone,
                    member_level,
                    is_active,
                    created_at
                FROM users
                WHERE user_id = %s
                """,
                (user_id,)
            )

            user = cur.fetchone()


            # --------------------------------
            # 7-2. 找不到會員
            # --------------------------------

            if user is None:

                raise HTTPException(
                    status_code=401,
                    detail="找不到會員資料"
                )


            # --------------------------------
            # 7-3. 檢查會員是否啟用
            # --------------------------------

            if not user["is_active"]:

                raise HTTPException(
                    status_code=403,
                    detail="此會員帳號已停用"
                )


            return user


# ============================================
# 8. 取得會員功能
# ============================================

def get_user_features(
    user_id: int
):

    with get_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    ml.level_id,
                    ml.level_name,
                    f.feature_id,
                    f.feature_name,
                    f.feature_code
                FROM users u

                INNER JOIN member_levels ml
                    ON u.member_level = ml.level_id

                LEFT JOIN member_levels_features mlf
                    ON ml.level_id = mlf.level_id

                LEFT JOIN features f
                    ON mlf.feature_id = f.feature_id

                WHERE u.user_id = %s
                  AND ml.is_active = TRUE
                  AND (f.is_active = TRUE OR f.feature_id IS NULL)

                ORDER BY f.feature_id
                """,
                (user_id,)
            )

            rows = cur.fetchall()


    # ----------------------------------------
    # 8-1. 如果沒有功能
    # ----------------------------------------

    if not rows:

        return {
            "level_id": None,
            "level_name": None,
            "features": []
        }


    # ----------------------------------------
    # 8-2. 取得會員等級
    # ----------------------------------------

    level_id = rows[0]["level_id"]

    level_name = rows[0]["level_name"]


    # ----------------------------------------
    # 8-3. 建立功能清單
    # ----------------------------------------

    features = []

    for row in rows:

        if row["feature_id"] is None:

            continue

        features.append(
            {
                "feature_id": row["feature_id"],
                "feature_name": row["feature_name"],
                "feature_code": row["feature_code"]
            }
        )


    return {
        "level_id": level_id,
        "level_name": level_name,
        "features": features
    }


# ============================================
# 9. 檢查會員是否具有指定功能
#
# 使用方式：
#
# Depends(require_feature("stock_history"))
# ============================================

def require_feature(feature_code: str):

    def feature_checker(
        user_id: int = Depends(get_current_user_id)
    ):

        with get_connection() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT 1
                    FROM users u

                    INNER JOIN member_levels_features mlf
                        ON u.member_level = mlf.level_id

                    INNER JOIN features f
                        ON mlf.feature_id = f.feature_id

                    WHERE u.user_id = %s
                      AND f.feature_code = %s
                      AND f.is_active = TRUE
                    """,
                    (
                        user_id,
                        feature_code
                    )
                )

                feature = cur.fetchone()


        # ------------------------------------
        # 沒有這項功能
        # ------------------------------------

        if feature is None:

            raise HTTPException(
                status_code=403,
                detail=f"會員沒有使用 {feature_code} 功能的權限"
            )


        # ------------------------------------
        # 有功能權限
        #
        # 回傳 user_id
        # ------------------------------------

        return user_id


    return feature_checker


# ============================================
# 10. 會員註冊 API
# ============================================

@router.post("/register")
def register_user(
    data: RegisterRequest
):

    # ----------------------------------------
    # 10-1. 取得前端傳入的資料
    # ----------------------------------------

    username = data.username

    nickname = data.nickname

    email = str(data.email)

    password = data.password

    phone = data.phone


    # ----------------------------------------
    # 10-2. username 檢查
    # ----------------------------------------

    if not username.strip():

        raise HTTPException(
            status_code=400,
            detail="username can not be empty."
        )


    if len(username) >= 20:

        raise HTTPException(
            status_code=400,
            detail="username length must be less than 20 characters."
        )


    if any(
        "\uff01" <= char <= "\uff5e"
        for char in username
    ):

        raise HTTPException(
            status_code=400,
            detail="username can not use full-width characters."
        )


    # ----------------------------------------
    # 10-3. nickname 檢查
    # ----------------------------------------

    if not nickname.strip():

        raise HTTPException(
            status_code=400,
            detail="nickname can not be empty."
        )


    if len(nickname) >= 20:

        raise HTTPException(
            status_code=400,
            detail="nickname length must be less than 20 characters."
        )


    if any(
        "\uff01" <= char <= "\uff5e"
        for char in nickname
    ):

        raise HTTPException(
            status_code=400,
            detail="nickname can not use full-width ASCII characters."
        )


    # ----------------------------------------
    # 10-4. password 檢查
    # ----------------------------------------

    if len(password) < 8 or len(password) > 20:

        raise HTTPException(
            status_code=400,
            detail="password length must be between 8-20 characters long."
        )


    # 至少一個大寫英文字母

    if not re.search(
        r"[A-Z]",
        password
    ):

        raise HTTPException(
            status_code=400,
            detail="password must contain at least one uppercase English letter."
        )


    # 至少一個符號

    if not re.search(
        r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>/?\\|`~]",
        password
    ):

        raise HTTPException(
            status_code=400,
            detail="password must contain at least one symbol."
        )


    # 只能使用半形英文字母、數字、半形符號

    if not re.fullmatch(
        r"[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};:'\",.<>/?\\|`~]+",
        password
    ):

        raise HTTPException(
            status_code=400,
            detail="密碼只能使用半形英文字母、數字及半形符號"
        )


    # ----------------------------------------
    # 10-5. phone 檢查
    #
    # phone 是選填
    # ----------------------------------------

    if phone is not None:

        if len(phone) > 10:

            raise HTTPException(
                status_code=400,
                detail="phone length must less than 10 characters."
            )


        if not phone.isascii() or not phone.isdigit():

            raise HTTPException(
                status_code=400,
                detail="phone can only contain half-width digits."
            )


    # ----------------------------------------
    # 10-6. 將原始密碼轉成雜湊值
    # ----------------------------------------

    hashed_password = password_hash.hash(
        password
    )


    # ----------------------------------------
    # 10-7. 連接 PostgreSQL
    # ----------------------------------------

    with get_connection() as conn:

        with conn.cursor() as cur:

            # --------------------------------
            # 10-8. 檢查 email 是否已經存在
            # --------------------------------

            cur.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            existing_user = cur.fetchone()


            if existing_user is not None:

                raise HTTPException(
                    status_code=400,
                    detail="Email already exists."
                )


            # --------------------------------
            # 10-9. 寫入會員資料
            #
            # 不指定 member_level
            #
            # PostgreSQL 會使用：
            #
            # DEFAULT 1
            #
            # 因此新會員自動成為：
            #
            # level_id = 1
            # 一般會員
            # --------------------------------

            cur.execute(
                """
                INSERT INTO users (
                    username,
                    nickname,
                    email,
                    password_hash,
                    phone
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                RETURNING user_id
                """,
                (
                    username,
                    nickname,
                    email,
                    hashed_password,
                    phone
                )
            )


            # --------------------------------
            # 10-10. 取得新會員 user_id
            # --------------------------------

            new_user = cur.fetchone()

            user_id = new_user["user_id"]


        # ------------------------------------
        # 10-11. 提交交易
        # ------------------------------------

        conn.commit()


    # ----------------------------------------
    # 10-12. 回傳註冊成功
    # ----------------------------------------

    return {
        "message": "註冊成功",
        "user_id": user_id,
        "member_level": "一般會員"
    }


# ============================================
# 11. 會員登入 API
# ============================================

@router.post("/login")
def login_user(
    data: LoginRequest
):

    # ----------------------------------------
    # 11-1. 取得登入資料
    # ----------------------------------------

    email = str(data.email)

    password = data.password


    # ----------------------------------------
    # 11-2. 連接 PostgreSQL
    # ----------------------------------------

    with get_connection() as conn:

        with conn.cursor() as cur:

            # --------------------------------
            # 11-3. 根據 email 查詢會員
            # --------------------------------

            cur.execute(
                """
                SELECT
                    user_id,
                    username,
                    nickname,
                    email,
                    password_hash,
                    member_level,
                    is_active
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cur.fetchone()


    # ----------------------------------------
    # 11-4. 如果找不到會員
    # ----------------------------------------

    if user is None:

        raise HTTPException(
            status_code=401,
            detail="Wrong EMAIL or PASSWORD"
        )


    # ----------------------------------------
    # 11-5. 取得會員資料
    # ----------------------------------------

    user_id = user["user_id"]

    username = user["username"]

    nickname = user["nickname"]

    user_email = user["email"]

    stored_password_hash = user["password_hash"]

    is_active = user["is_active"]


    # ----------------------------------------
    # 11-6. 檢查會員是否啟用
    # ----------------------------------------

    if not is_active:

        raise HTTPException(
            status_code=403,
            detail="此會員帳號目前已停用"
        )


    # ----------------------------------------
    # 11-7. 驗證密碼
    # ----------------------------------------

    is_password_valid = password_hash.verify(
        password,
        stored_password_hash
    )


    # ----------------------------------------
    # 11-8. 密碼錯誤
    # ----------------------------------------

    if not is_password_valid:

        raise HTTPException(
            status_code=401,
            detail="Wrong Password"
        )


    # ----------------------------------------
    # 11-9. 取得會員功能
    # ----------------------------------------

    membership = get_user_features(
        user_id
    )


    # ----------------------------------------
    # 11-10. 登入成功後產生 Session Token
    # ----------------------------------------

    token = secrets.token_urlsafe(32)


    # ----------------------------------------
    # 11-11. Token 與 user_id 建立關聯
    # ----------------------------------------

    sessions[token] = user_id


    # ----------------------------------------
    # 11-12. 回傳登入成功
    # ----------------------------------------

    return {

        "message": "登入成功",

        "token": token,

        "user": {

            "user_id": user_id,

            "username": username,

            "nickname": nickname,

            "email": user_email,

            "member_level": membership["level_id"],

            "member_level_name": membership["level_name"],

            "features": membership["features"]
        }
    }


# ============================================
# 12. 取得目前登入會員資訊
# ============================================

@router.get("/user_profile")
def user_profile(
    user_id: int = Depends(get_current_user_id)
):

    # ----------------------------------------
    # 12-1. 查詢會員基本資料
    # ----------------------------------------

    user = get_current_user(
        user_id
    )


    # ----------------------------------------
    # 12-2. 取得會員功能
    # ----------------------------------------

    membership = get_user_features(
        user_id
    )


    # ----------------------------------------
    # 12-3. 回傳完整會員資訊
    # ----------------------------------------

    return {

        "user_id": user["user_id"],

        "username": user["username"],

        "nickname": user["nickname"],

        "email": user["email"],

        "phone": user["phone"],

        "is_active": user["is_active"],

        "created_at": user["created_at"],

        "member_level": membership["level_id"],

        "member_level_name": membership["level_name"],

        "features": membership["features"]
    }


# ============================================
# 13. 會員登出 API
# ============================================

@router.post("/logout")
def logout_user(
    authorization: Optional[str] = Header(default=None)
):

    # ----------------------------------------
    # 13-1. 檢查 Authorization Header
    # ----------------------------------------

    if authorization is None:

        raise HTTPException(
            status_code=401,
            detail="尚未登入"
        )


    # ----------------------------------------
    # 13-2. 檢查格式
    # ----------------------------------------

    if not authorization.startswith("Bearer "):

        raise HTTPException(
            status_code=401,
            detail="Authorization 格式錯誤"
        )


    # ----------------------------------------
    # 13-3. 取出 Token
    # ----------------------------------------

    token = authorization[7:]


    # ----------------------------------------
    # 13-4. 檢查 Token 是否存在
    # ----------------------------------------

    if token not in sessions:

        raise HTTPException(
            status_code=401,
            detail="登入狀態已失效"
        )


    # ----------------------------------------
    # 13-5. 從 sessions 移除 Token
    # ----------------------------------------

    del sessions[token]


    # ----------------------------------------
    # 13-6. 回傳登出成功
    # ----------------------------------------

    return {
        "message": "登出成功"
    }
