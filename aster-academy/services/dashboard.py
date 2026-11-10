"""Read models for student learning progress and tryout summaries."""


def recent_attempt_summaries(conn, user_id, limit=3):
    """Return the newest completed tryouts with safe display metadata."""
    rows = conn.execute(
        """
        SELECT a.id, a.score, a.total, a.finished_at, s.title
        FROM attempts a
        JOIN question_sets s ON s.id = a.set_id
        WHERE a.user_id = ? AND a.finished_at IS NOT NULL
        ORDER BY a.finished_at DESC, a.id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "score": row["score"],
            "total": row["total"],
            "percentage": round(100 * row["score"] / max(row["total"], 1)),
            "finished_at": row["finished_at"],
        }
        for row in rows
    ]
