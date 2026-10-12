document.addEventListener("DOMContentLoaded", () => {
    if (!checkAuth("admin")) return;
    loadAnalytics();
    loadUsers();
    loadTopics();
    loadSessions();
    loadBookings();
    loadFeedback();
});

function switchTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));
    
    event.target.classList.add("active");
    document.getElementById(tabId).classList.add("active");

    if (tabId === "analyticsTab") loadAnalytics();
    else if (tabId === "usersTab") loadUsers();
    else if (tabId === "topicsTab") loadTopics();
    else if (tabId === "sessionsTab") loadSessions();
    else if (tabId === "bookingsTab") loadBookings();
    else if (tabId === "feedbackTab") loadFeedback();
}

async function loadAnalytics() {
    const res = await apiCall("/analytics/dashboard");
    if (!res.ok) return;

    const data = res.data;
    document.getElementById("statUsers").textContent = data.total_users;
    document.getElementById("statMentors").textContent = data.total_mentors;
    document.getElementById("statSchools").textContent = data.total_schools;
    document.getElementById("statSessions").textContent = data.total_sessions;
    document.getElementById("statCompleted").textContent = data.completed_sessions;
    document.getElementById("statPending").textContent = data.pending_bookings;

    // Popular topics
    const topicsEl = document.getElementById("popularTopicsList");
    if (data.popular_topics.length === 0) topicsEl.textContent = "No data available";
    else {
        topicsEl.innerHTML = data.popular_topics.map(t => 
            `<div style="display:flex; justify-content:space-between; margin-bottom:6px;"><span>${t.topic_name}</span><strong>${t.session_count} sessions</strong></div>`
        ).join("");
    }

    // Bookings by school
    const schoolEl = document.getElementById("schoolBookingsList");
    if (data.bookings_by_school.length === 0) schoolEl.textContent = "No data available";
    else {
        schoolEl.innerHTML = data.bookings_by_school.map(s => 
            `<div style="display:flex; justify-content:space-between; margin-bottom:6px;"><span>${s.organization_name}</span><strong>${s.booking_count} bookings</strong></div>`
        ).join("");
    }
}

async function loadUsers() {
    const res = await apiCall("/admin/users");
    const tbody = document.getElementById("usersTableBody");
    if (!res.ok) { tbody.innerHTML = `<tr><td colspan="6" class="message error">${res.error}</td></tr>`; return; }

    tbody.innerHTML = res.data.map(u => `
        <tr>
            <td>${u.user_id}</td>
            <td><strong>${u.username}</strong></td>
            <td>${u.email || '-'}</td>
            <td><span class="badge badge-completed">${u.role}</span></td>
            <td><span class="badge badge-${u.is_active ? 'active' : 'inactive'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button class="btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-success'}" onclick="toggleUserStatus(${u.user_id}, ${u.is_active ? 'false' : 'true'})">
                    ${u.is_active ? 'Deactivate' : 'Activate'}
                </button>
            </td>
        </tr>
    `).join("");
}

async function toggleUserStatus(userId, newStatus) {
    const res = await apiCall(`/admin/users/${userId}/status`, "PUT", { is_active: newStatus });
    if (!res.ok) alert(res.error);
    else loadUsers();
}

async function loadTopics() {
    const res = await apiCall("/topics");
    const tbody = document.getElementById("topicsTableBody");
    const select = document.getElementById("sessTopic");
    if (!res.ok) return;

    select.innerHTML = '<option value="">Select Topic</option>' + res.data.map(t => `<option value="${t.topic_id}">${t.name}</option>`).join("");

    tbody.innerHTML = res.data.map(t => `
        <tr>
            <td>${t.topic_id}</td>
            <td><strong>${t.name}</strong></td>
            <td>${t.description || '-'}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteTopic(${t.topic_id})">Delete</button>
            </td>
        </tr>
    `).join("");
}

document.getElementById("createTopicForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const name = document.getElementById("topicName").value.trim();
    const description = document.getElementById("topicDesc").value.trim();

    const res = await apiCall("/topics", "POST", { name, description });
    if (!res.ok) alert(res.error);
    else {
        document.getElementById("createTopicForm").reset();
        loadTopics();
    }
});

async function deleteTopic(topicId) {
    if (!confirm("Are you sure you want to delete this topic?")) return;
    const res = await apiCall(`/topics/${topicId}`, "DELETE");
    if (!res.ok) alert(res.error);
    else loadTopics();
}

let mentorsListCache = [];

async function loadSessions() {
    // Also fetch mentors list for assignment dropdown
    const mentRes = await apiCall("/admin/mentors");
    if (mentRes.ok) mentorsListCache = mentRes.data;

    const res = await apiCall("/sessions");
    const tbody = document.getElementById("sessionsTableBody");
    if (!res.ok) return;

    tbody.innerHTML = res.data.map(s => `
        <tr>
            <td>${s.session_id}</td>
            <td><strong>${s.title}</strong></td>
            <td>${s.topic_name || '-'}</td>
            <td>${s.session_date}<br><small>${s.start_time} - ${s.end_time}</small></td>
            <td>${s.mode}</td>
            <td><span class="badge badge-pending">${s.status}</span></td>
            <td id="sessionMentorsCell_${s.session_id}">Loading...</td>
            <td>
                <button class="btn btn-sm" onclick="promptAssignMentor(${s.session_id})">Assign Mentor</button>
                <button class="btn btn-danger btn-sm" onclick="deleteSession(${s.session_id})">Delete</button>
            </td>
        </tr>
    `).join("");

    // Load assigned mentors for each session
    res.data.forEach(s => fetchSessionMentors(s.session_id));
}

async function fetchSessionMentors(sessionId) {
    const cell = document.getElementById(`sessionMentorsCell_${sessionId}`);
    const res = await apiCall(`/sessions/${sessionId}/mentors`);
    if (res.ok) {
        if (res.data.length === 0) cell.innerHTML = '<em>None</em>';
        else {
            cell.innerHTML = res.data.map(m => `
                <span class="badge badge-approved">${m.name} 
                    <a href="#" onclick="removeMentorFromSession(${sessionId}, ${m.mentor_id}); return false;" style="color:red; text-decoration:none; margin-left:4px;">&times;</a>
                </span>
            `).join(" ");
        }
    }
}

document.getElementById("createSessionForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const body = {
        title: document.getElementById("sessTitle").value.trim(),
        topic_id: document.getElementById("sessTopic").value,
        session_date: document.getElementById("sessDate").value,
        start_time: document.getElementById("sessStart").value,
        end_time: document.getElementById("sessEnd").value,
        mode: document.getElementById("sessMode").value,
        location: document.getElementById("sessLocation").value.trim(),
        description: document.getElementById("sessDesc").value.trim()
    };

    const res = await apiCall("/sessions", "POST", body);
    if (!res.ok) alert(res.error);
    else {
        document.getElementById("createSessionForm").reset();
        loadSessions();
    }
});

async function promptAssignMentor(sessionId) {
    if (mentorsListCache.length === 0) {
        alert("No mentors available to assign.");
        return;
    }
    const options = mentorsListCache.map(m => `${m.mentor_id}: ${m.name} (${m.expertise})`).join("\n");
    const mentorIdStr = prompt(`Enter Mentor ID to assign to session #${sessionId}:\n\n${options}`);
    if (!mentorIdStr) return;
    const mentor_id = parseInt(mentorIdStr.trim());
    if (isNaN(mentor_id)) return;

    const res = await apiCall(`/sessions/${sessionId}/mentors`, "POST", { mentor_id });
    if (!res.ok) alert(res.error);
    else fetchSessionMentors(sessionId);
}

async function removeMentorFromSession(sessionId, mentorId) {
    const res = await apiCall(`/sessions/${sessionId}/mentors/${mentorId}`, "DELETE");
    if (!res.ok) alert(res.error);
    else fetchSessionMentors(sessionId);
}

async function deleteSession(sessionId) {
    if (!confirm("Are you sure you want to delete this session?")) return;
    const res = await apiCall(`/sessions/${sessionId}`, "DELETE");
    if (!res.ok) alert(res.error);
    else loadSessions();
}

async function loadBookings() {
    const res = await apiCall("/bookings");
    const tbody = document.getElementById("bookingsTableBody");
    if (!res.ok) return;

    tbody.innerHTML = res.data.map(b => `
        <tr>
            <td>${b.booking_id}</td>
            <td><strong>${b.school_name || 'School'}</strong></td>
            <td>${b.session_title || 'Session'}</td>
            <td>${b.session_date}<br><small>${b.start_time || ''} - ${b.end_time || ''}</small></td>
            <td><span class="badge badge-${b.status}">${b.status}</span></td>
            <td>
                ${b.status === 'pending' ? `
                    <button class="btn btn-success btn-sm" onclick="updateBookingStatus(${b.booking_id}, 'approved')">Approve</button>
                    <button class="btn btn-danger btn-sm" onclick="updateBookingStatus(${b.booking_id}, 'rejected')">Reject</button>
                ` : b.status === 'approved' ? `
                    <button class="btn btn-secondary btn-sm" onclick="updateBookingStatus(${b.booking_id}, 'completed')">Mark Completed</button>
                ` : '-'}
            </td>
        </tr>
    `).join("");
}

async function updateBookingStatus(bookingId, status) {
    const res = await apiCall(`/bookings/${bookingId}/status`, "PUT", { status });
    if (!res.ok) alert(res.error);
    else loadBookings();
}

async function loadFeedback() {
    const res = await apiCall("/admin/feedback");
    const tbody = document.getElementById("feedbackTableBody");
    if (!res.ok) return;

    tbody.innerHTML = res.data.map(f => `
        <tr>
            <td>${f.feedback_id}</td>
            <td><strong>${f.school_name || '-'}</strong></td>
            <td>${f.session_title || '-'}</td>
            <td><strong style="color:#d97706;">${'★'.repeat(f.rating)} (${f.rating}/5)</strong></td>
            <td>${f.comments || '-'}</td>
            <td>${f.created_at ? f.created_at.split("T")[0] : '-'}</td>
        </tr>
    `).join("");
}
