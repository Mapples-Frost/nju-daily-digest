from __future__ import annotations

import json
import sqlite3
from datetime import timedelta

from config import Config
from utils.text_utils import title_fingerprint
from utils.time_utils import now_local, sort_items


class SQLiteStorage:
    def __init__(self, config: Config, logger) -> None:
        self.config = config
        self.logger = logger
        self.config.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.config.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    url TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    title_fingerprint TEXT,
                    source TEXT,
                    source_type TEXT,
                    published_at TEXT,
                    published_at_text TEXT,
                    category TEXT,
                    category_hint TEXT,
                    matched_keywords TEXT,
                    summary TEXT,
                    preview TEXT,
                    detail_text TEXT,
                    list_page TEXT,
                    first_seen_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    sent_at TEXT
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_items_sent_at ON items(sent_at)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_items_title_fp ON items(title_fingerprint)")

    def upsert_item(self, item: dict) -> bool:
        url = item["url"]
        fingerprint = title_fingerprint(item.get("title"))
        now_iso = now_local(self.config.timezone).isoformat()

        with self._connect() as connection:
            existing = connection.execute("SELECT url FROM items WHERE url = ?", (url,)).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE items
                    SET title = ?, source = ?, source_type = ?, published_at = ?, published_at_text = ?,
                        category = ?, category_hint = ?, matched_keywords = ?, summary = ?, preview = ?,
                        detail_text = ?, list_page = ?, title_fingerprint = ?, last_seen_at = ?
                    WHERE url = ?
                    """,
                    (
                        item.get("title"),
                        item.get("source"),
                        item.get("source_type"),
                        item.get("published_at"),
                        item.get("published_at_text"),
                        item.get("category"),
                        item.get("category_hint"),
                        json.dumps(item.get("matched_keywords", []), ensure_ascii=False),
                        item.get("summary"),
                        item.get("preview"),
                        item.get("detail_text"),
                        item.get("list_page"),
                        fingerprint,
                        now_iso,
                        url,
                    ),
                )
                return False

            if fingerprint:
                duplicate = connection.execute(
                    "SELECT url FROM items WHERE title_fingerprint = ? AND source_type = ?",
                    (fingerprint, item.get("source_type")),
                ).fetchone()
                if duplicate:
                    connection.execute(
                        """
                        UPDATE items
                        SET last_seen_at = ?, summary = COALESCE(summary, ?), detail_text = COALESCE(detail_text, ?)
                        WHERE url = ?
                        """,
                        (now_iso, item.get("summary"), item.get("detail_text"), duplicate["url"]),
                    )
                    return False

            connection.execute(
                """
                INSERT INTO items (
                    url, title, title_fingerprint, source, source_type, published_at, published_at_text,
                    category, category_hint, matched_keywords, summary, preview, detail_text, list_page,
                    first_seen_at, last_seen_at, sent_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    url,
                    item.get("title"),
                    fingerprint,
                    item.get("source"),
                    item.get("source_type"),
                    item.get("published_at"),
                    item.get("published_at_text"),
                    item.get("category"),
                    item.get("category_hint"),
                    json.dumps(item.get("matched_keywords", []), ensure_ascii=False),
                    item.get("summary"),
                    item.get("preview"),
                    item.get("detail_text"),
                    item.get("list_page"),
                    now_iso,
                    now_iso,
                ),
            )
            return True

    def get_unsent_items(self) -> list[dict]:
        cutoff = (now_local(self.config.timezone) - timedelta(days=self.config.unsent_lookback_days)).isoformat()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM items
                WHERE sent_at IS NULL AND last_seen_at >= ?
                """,
                (cutoff,),
            ).fetchall()
        items = [self._row_to_item(row) for row in rows]
        return sort_items(items, self.config.timezone)

    def mark_sent(self, urls: list[str]) -> None:
        if not urls:
            return
        now_iso = now_local(self.config.timezone).isoformat()
        with self._connect() as connection:
            connection.executemany("UPDATE items SET sent_at = ? WHERE url = ?", [(now_iso, url) for url in urls])

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> dict:
        return {
            "url": row["url"],
            "title": row["title"],
            "source": row["source"],
            "source_type": row["source_type"],
            "published_at": row["published_at"],
            "published_at_text": row["published_at_text"],
            "category": row["category"],
            "category_hint": row["category_hint"],
            "matched_keywords": json.loads(row["matched_keywords"] or "[]"),
            "summary": row["summary"],
            "preview": row["preview"],
            "detail_text": row["detail_text"],
            "list_page": row["list_page"],
        }
