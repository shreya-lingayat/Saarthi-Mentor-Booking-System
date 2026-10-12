const roleSelect = document.getElementById("role");
const schoolFields = document.getElementById("schoolFields");
const mentorFields = document.getElementById("mentorFields");

roleSelect.addEventListener("change", function() {
    if (this.value === "school") {
        schoolFields.style.display = "block";
        mentorFields.style.display = "none";
    } else if (this.value === "mentor") {
        schoolFields.style.display = "none";
        mentorFields.style.display = "block";
    } else {
        schoolFields.style.display = "none";
        mentorFields.style.display = "none";
    }
});

document.getElementById("registerForm").addEventListener("submit", async function(event) {
    event.preventDefault();

    const role = roleSelect.value;
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const messageEl = document.getElementById("message");

    messageEl.textContent = "Registering...";
    messageEl.className = "message";

    const body = { role, username, email, password };

    if (role === "school") {
        body.organization_name = document.getElementById("organization_name").value.trim();
    } else if (role === "mentor") {
        body.name = document.getElementById("mentor_name").value.trim();
        body.expertise = document.getElementById("expertise").value.trim();
        body.qualifications = document.getElementById("qualifications").value.trim();
    }

    const res = await apiCall("/auth/register", "POST", body);

    if (!res.ok) {
        messageEl.textContent = res.error;
        messageEl.className = "message error";
        return;
    }

    messageEl.textContent = "Registration successful! Redirecting to login...";
    messageEl.className = "message success";

    setTimeout(() => {
        window.location.href = "login.html";
    }, 1200);
});
