document.addEventListener("DOMContentLoaded", () => {
    if (!checkAuth("school")) return;
    loadProfile();
    loadSessions();
    loadMyBookings();
});

function switchTab(tabId) {
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));
    
    event.target.classList.add("active");
    document.getElementById(tabId).classList.add("active");

    if (tabId === "sessionsTab") loadSessions();
    else if (tabId === "myBookingsTab") loadMyBookings();
    else if (tabId === "profileTab") loadProfile();
}

async function loadProfile() {
    const res = await apiCall("/school/profile");
    if (!res.ok) return;

    const p = res.data;
    document.getElementById("schoolOrgName").textContent = p.organization_name || "School / NGO";
    document.getElementById("profUsername").value = p.username || "";
    document.getElementById("profEmail").value = p.email || "";
    document.getElementById("profOrgName").value = p.organization_name || "";
}

document.getElementById("profileForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const organization_name = document.getElementById("profOrgName").value.trim();
    const msg = document.getElementById("profMessage");

    const res = await apiCall("/school/profile", "PUT", { organization_name });
    if (!res.ok) {
        msg.textContent = res.error;
        msg.className = "message error";
    } else {
        msg.textContent = "Profile updated successfully!";
        msg.className = "message success";
        loadProfile();
    }
});

async function loadSessions() {
    const res = await apiCall("/school/sessions");
    const tbody = document.getElementById("availableSessionsBody");
    if (!res.ok) { tbody.innerHTML = `<tr><td colspan="6" class="message error">${res.error}</td></tr>`; return; }

    tbody.innerHTML = res.data.map(s => `
        <tr>
            <td><strong>${s.title}</strong><br><small>${s.description || ''}</small></td>
            <td>${s.topic_name || '-'}</td>
            <td>${s.session_date}<br><small>${s.start_time} - ${s.end_time}</small></td>
            <td><span class="badge badge-completed">${s.mode}</span> ${s.location ? `(${s.location})` : ''}</td>
            <td>${s.max_participants || 50}</td>
            <td>
                <button class="btn btn-sm" onclick="requestBooking(${s.session_id})">Request Booking</button>
            </td>
        </tr>
    `).join("");
}

async function requestBooking(sessionId) {
    if (!confirm("Are you sure you want to request a booking for this session?")) return;
    const res = await apiCall("/school/bookings", "POST", { session_id: sessionId });
    if (!res.ok) alert(res.error);
    else {
        alert("Booking request submitted successfully!");
        loadMyBookings();
        switchTab("myBookingsTab");
    }
}

async function loadMyBookings() {
    const res = await apiCall("/school/bookings");
    const tbody = document.getElementById("myBookingsBody");
    if (!res.ok) { tbody.innerHTML = `<tr><td colspan="6" class="message error">${res.error}</td></tr>`; return; }

    tbody.innerHTML = res.data.map(b => `
        <tr>
            <td>${b.booking_id}</td>
            <td><strong>${b.session_title || 'Session'}</strong><br><small>${b.topic_name || ''}</small></td>
            <td>${b.session_date || ''}<br><small>${b.start_time || ''} - ${b.end_time || ''}</small></td>
            <td><span class="badge badge-${b.status}">${b.status}</span></td>
            <td>
                ${b.rating ? `<strong style="color:#d97706;">${'★'.repeat(b.rating)} (${b.rating}/5)</strong>` : 
                  b.status === 'completed' ? `<button class="btn btn-sm btn-success" onclick="openFeedbackModal(${b.booking_id})">Submit Feedback</button>` : '-'}
            </td>
            <td>
                ${b.status === 'pending' || b.status === 'approved' ? `
                    <button class="btn btn-danger btn-sm" onclick="cancelBooking(${b.booking_id})">Cancel</button>
                ` : '-'}
            </td>
        </tr>
    `).join("");
}

async function cancelBooking(bookingId) {
    if (!confirm("Are you sure you want to cancel this booking?")) return;
    const res = await apiCall(`/school/bookings/${bookingId}/cancel`, "PUT");
    if (!res.ok) alert(res.error);
    else loadMyBookings();
}

function openFeedbackModal(bookingId) {
    document.getElementById("fbBookingId").value = bookingId;
    document.getElementById("fbComments").value = "";
    document.getElementById("feedbackModal").style.display = "flex";
}

function closeFeedbackModal() {
    document.getElementById("feedbackModal").style.display = "none";
}

document.getElementById("feedbackForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const booking_id = parseInt(document.getElementById("fbBookingId").value);
    const rating = parseInt(document.getElementById("fbRating").value);
    const comments = document.getElementById("fbComments").value.trim();

    const res = await apiCall("/school/feedback", "POST", { booking_id, rating, comments });
    if (!res.ok) alert(res.error);
    else {
        alert("Feedback submitted successfully!");
        closeFeedbackModal();
        loadMyBookings();
    }
});
