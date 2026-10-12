document.addEventListener("DOMContentLoaded", () => {
    if (!checkAuth("mentor")) return;
    loadProfile();
    loadAssignedSessions();
    loadAvailability();
});

function switchTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));
    
    event.target.classList.add("active");
    document.getElementById(tabId).classList.add("active");

    if (tabId === "assignedTab") loadAssignedSessions();
    else if (tabId === "availabilityTab") loadAvailability();
    else if (tabId === "profileTab") loadProfile();
}

async function loadProfile() {
    const res = await apiCall("/mentor/profile");
    if (!res.ok) return;

    const p = res.data;
    document.getElementById("mentorName").textContent = p.name || "Mentor";
    document.getElementById("profUsername").value = p.username || "";
    document.getElementById("profEmail").value = p.email || "";
    document.getElementById("profName").value = p.name || "";
    document.getElementById("profExpertise").value = p.expertise || "";
    document.getElementById("profQualifications").value = p.qualifications || "";
}

document.getElementById("profileForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const body = {
        name: document.getElementById("profName").value.trim(),
        expertise: document.getElementById("profExpertise").value.trim(),
        qualifications: document.getElementById("profQualifications").value.trim()
    };
    const msg = document.getElementById("profMessage");

    const res = await apiCall("/mentor/profile", "PUT", body);
    if (!res.ok) {
        msg.textContent = res.error;
        msg.className = "message error";
    } else {
        msg.textContent = "Profile updated successfully!";
        msg.className = "message success";
        loadProfile();
    }
});

async function loadAssignedSessions() {
    const res = await apiCall("/mentor/sessions");
    const tbody = document.getElementById("assignedSessionsBody");
    if (!res.ok) { tbody.innerHTML = `<tr><td colspan="6" class="message error">${res.error}</td></tr>`; return; }

    if (res.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No sessions currently assigned to you.</td></tr>';
        return;
    }

    tbody.innerHTML = res.data.map(s => `
        <tr>
            <td>${s.session_id}</td>
            <td><strong>${s.title}</strong><br><small>${s.description || ''}</small></td>
            <td>${s.topic_name || '-'}</td>
            <td>${s.session_date}<br><small>${s.start_time} - ${s.end_time}</small></td>
            <td><span class="badge badge-completed">${s.mode}</span> ${s.location ? `(${s.location})` : ''}</td>
            <td><span class="badge badge-${s.status}">${s.status}</span></td>
        </tr>
    `).join("");
}

async function loadAvailability() {
    const res = await apiCall("/mentor/availability");
    const tbody = document.getElementById("availabilityBody");
    if (!res.ok) { tbody.innerHTML = `<tr><td colspan="4" class="message error">${res.error}</td></tr>`; return; }

    if (res.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No availability slots set. Add your available time above.</td></tr>';
        return;
    }

    tbody.innerHTML = res.data.map(slot => `
        <tr>
            <td>${slot.availability_id}</td>
            <td>${slot.available_date || slot.date}</td>
            <td>${slot.start_time}</td>
            <td>${slot.end_time}</td>
        </tr>
    `).join("");
}

document.getElementById("addAvailabilityForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const body = {
        available_date: document.getElementById("availDate").value,
        start_time: document.getElementById("availStart").value,
        end_time: document.getElementById("availEnd").value
    };

    const res = await apiCall("/mentor/availability", "POST", body);
    if (!res.ok) alert(res.error);
    else {
        document.getElementById("addAvailabilityForm").reset();
        loadAvailability();
    }
});
