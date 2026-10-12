const API_BASE_URL = "http://localhost:5000/api";

async function apiCall(endpoint, method = "GET", body = null) {
    const headers = {};
    
    const token = localStorage.getItem("token");
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    if (body) {
        headers["Content-Type"] = "application/json";
    }

    const config = {
        method: method,
        headers: headers
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        const data = await response.json();

        if (response.status === 401) {
            // Expired or invalid token
            localStorage.removeItem("token");
            localStorage.removeItem("role");
            localStorage.removeItem("user_id");
            if (!window.location.pathname.endsWith("login.html") && !window.location.pathname.endsWith("register.html")) {
                window.location.href = "login.html";
            }
        }

        return {
            ok: response.ok,
            status: response.status,
            data: data,
            error: response.ok ? null : (data.error || "Request failed")
        };
    } catch (err) {
        console.error("API Call Error:", err);
        return {
            ok: false,
            status: 0,
            data: null,
            error: "Cannot connect to server. Please ensure Flask backend is running."
        };
    }
}
