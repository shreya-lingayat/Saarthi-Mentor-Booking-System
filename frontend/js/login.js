document.getElementById("loginForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const messageEl = document.getElementById("message");

    messageEl.textContent = "Logging in...";
    messageEl.className = "message";

    const res = await apiCall("/auth/login", "POST", { username, password });

    if (!res.ok) {
        messageEl.textContent = res.error;
        messageEl.className = "message error";
        return;
    }

    messageEl.textContent = "Login successful! Redirecting...";
    messageEl.className = "message success";

    localStorage.setItem("token", res.data.token);
    localStorage.setItem("role", res.data.role);
    localStorage.setItem("user_id", res.data.user_id);

    setTimeout(() => {
        if (res.data.role === "admin") {
            window.location.href = "admin.html";
        } else if (res.data.role === "school") {
            window.location.href = "school.html";
        } else if (res.data.role === "mentor") {
            window.location.href = "mentor.html";
        } else {
            messageEl.textContent = "Unknown user role";
            messageEl.className = "message error";
        }
    }, 500);
});