from datetime import datetime, timedelta

def parse_time(time_str):
    """
    Parses time string (HH:MM or HH:MM:SS or timedelta) to string 'HH:MM:SS'.
    """
    if isinstance(time_str, timedelta):
        total_seconds = int(time_str.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    time_str = str(time_str).strip()
    parts = time_str.split(":")
    if len(parts) == 2:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
    elif len(parts) == 3:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"
    return time_str

def is_valid_time_range(start_time_str, end_time_str):
    """
    Returns True if start_time < end_time.
    """
    try:
        st = parse_time(start_time_str)
        et = parse_time(end_time_str)
        return st < et
    except Exception:
        return False

def check_mentor_conflict(conn, mentor_id, session_date, start_time_str, end_time_str, exclude_session_id=None):
    """
    Checks if a mentor is already booked or assigned to a session that overlaps
    with (session_date, start_time, end_time).
    Returns (has_conflict, message).
    """
    st = parse_time(start_time_str)
    et = parse_time(end_time_str)

    cursor = conn.cursor(dictionary=True)
    try:
        # Check sessions table through session_mentors
        query = """
            SELECT s.session_id, s.title, s.start_time, s.end_time
            FROM sessions s
            JOIN session_mentors sm ON s.session_id = sm.session_id
            WHERE sm.mentor_id = %s
              AND s.session_date = %s
              AND s.status != 'cancelled'
              AND (%s < s.end_time AND %s > s.start_time)
        """
        params = [mentor_id, session_date, st, et]
        if exclude_session_id:
            query += " AND s.session_id != %s"
            params.append(exclude_session_id)

        cursor.execute(query, tuple(params))
        conflict_session = cursor.fetchone()
        if conflict_session:
            return True, f"Mentor is already assigned to session '{conflict_session['title']}' at this overlapping time."

        return False, None
    finally:
        cursor.close()
