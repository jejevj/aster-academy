"""Read models for student learning progress and tryout summaries."""

import json


def _percentage(score, maximum):
    return round(100 * score / max(maximum, 1))


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
            "percentage": _percentage(row["score"], row["total"]),
            "finished_at": row["finished_at"],
        }
        for row in rows
    ]


def category_learning_analysis(conn, user_id):
    """Return deterministic guidance from the latest scored tryout.

    This is a training evaluation, not a selection prediction. Historical
    breakdown snapshots are used so later question/category edits do not alter
    a student's past result.
    """
    rows = conn.execute(
        """
        SELECT id, score, total, score_breakdown_snapshot
        FROM attempts
        WHERE user_id = ? AND finished_at IS NOT NULL
        ORDER BY finished_at DESC, id DESC
        LIMIT 2
        """,
        (user_id,),
    ).fetchall()
    if not rows:
        return None

    latest = rows[0]
    try:
        breakdown = json.loads(latest["score_breakdown_snapshot"] or "{}")
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(breakdown, dict):
        return None

    category_ids = []
    for key, value in breakdown.items():
        if not isinstance(value, dict):
            continue
        try:
            category_id = int(key)
            score = float(value["score"])
            maximum = float(value["max_score"])
        except (KeyError, TypeError, ValueError):
            continue
        if maximum <= 0:
            continue
        category_ids.append((category_id, score, maximum))
    if not category_ids:
        return None

    names = {
        row["id"]: row["name"]
        for row in conn.execute(
            "SELECT id, name FROM question_categories WHERE id IN (%s)"
            % ",".join("?" for _ in category_ids),
            [item[0] for item in category_ids],
        ).fetchall()
    }
    categories = [
        {
            "id": category_id,
            "name": names.get(category_id, "Kategori"),
            "score": score,
            "max_score": maximum,
            "percentage": _percentage(score, maximum),
        }
        for category_id, score, maximum in category_ids
    ]
    weakest = min(categories, key=lambda item: (item["percentage"], item["id"]))
    previous_percentage = None
    if len(rows) > 1:
        previous_percentage = _percentage(rows[1]["score"], rows[1]["total"])

    return {
        "latest_attempt_id": latest["id"],
        "latest_percentage": _percentage(latest["score"], latest["total"]),
        "previous_percentage": previous_percentage,
        "weakest": weakest,
        "categories": sorted(categories, key=lambda item: (item["percentage"], item["id"])),
    }
