function getUser() {
    return {
        token: localStorage.getItem("token"),
        role: localStorage.getItem("role"),
        userId: localStorage.getItem("user_id")
    };
}

function checkAuth(requiredRole = null) {
    const user = getUser();
    if (!user.token) {
        window.location.href = "login.html";
        return false;
    }

    if (requiredRole && user.role !== requiredRole) {
        // Redirect user to their own dashboard
        if (user.role === "admin") window.location.href = "admin.html";
        else if (user.role === "school") window.location.href = "school.html";
        else if (user.role === "mentor") window.location.href = "mentor.html";
        else window.location.href = "login.html";
        return false;
    }

    return true;
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    localStorage.removeItem("user_id");
    window.location.href = "login.html";
}
