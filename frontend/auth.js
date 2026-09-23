// ========================================
// API 基本網址
// ========================================

// 本機開發時使用
//const API_BASE_URL = "http://127.0.0.1:8000";

// 正式環境
const API_BASE_URL = "/stocks";

// ========================================
// 儲存登入 Token
// ========================================

function saveToken(token) {

    localStorage.setItem("access_token", token);

}


// ========================================
// 取得登入 Token
// ========================================

function getToken() {

    return localStorage.getItem("access_token");

}


// ========================================
// 清除登入 Token
// ========================================

function removeToken() {

    localStorage.removeItem("access_token");

}


// ========================================
// 呼叫登入 API
// ========================================

async function loginUser(email, password) {

    const response = await fetch(
        `${API_BASE_URL}/auth/login`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                email: email,
                password: password
            })
        }
    );


    const data = await response.json();


    if (!response.ok) {

        throw new Error(
            data.detail || "登入失敗"
        );

    }


    return data;

}


// ========================================
// 呼叫註冊 API
// ========================================

async function registerUser(
    username,
    nickname,
    email,
    password,
    phone
) {

    const response = await fetch(
        `${API_BASE_URL}/auth/register`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                username: username,

                nickname: nickname,

                email: email,

                password: password,

                phone: phone || null

            })
        }
    );


    const data = await response.json();


    if (!response.ok) {

        throw new Error(
            data.detail || "註冊失敗"
        );

    }


    return data;

}


// ========================================
// 取得目前登入會員資料
// ========================================

async function getCurrentUser() {

    const token = getToken();


    if (!token) {

        throw new Error("尚未登入");

    }


    const response = await fetch(
        `${API_BASE_URL}/auth/user_profile`,
        {
            method: "GET",

            headers: {

                "Authorization": `Bearer ${token}`

            }
        }
    );


    const data = await response.json();


    if (!response.ok) {

        // Token 無效或過期時清除
        removeToken();

        throw new Error(
            data.detail || "登入狀態已失效"
        );

    }


    return data;

}


// ========================================
// 呼叫登出 API
// ========================================

async function logoutUser() {

    const token = getToken();


    if (!token) {

        return;

    }


    const response = await fetch(
        `${API_BASE_URL}/auth/logout`,
        {
            method: "POST",

            headers: {

                "Authorization": `Bearer ${token}`

            }
        }
    );


    // 不論 API 結果如何
    // 前端都清除 Token
    removeToken();


    if (!response.ok) {

        throw new Error("登出失敗");

    }


    return await response.json();

}