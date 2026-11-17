# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vince Bono
"""Spans of time in one app (and, if allowed, one window title), kept in a local SQLite file."""

from __future__ import annotations

import sqlite3
from pathlib import Path

MAX_ROWS = 50  # keeps one answer inside an agent's context


class Store:
    # shortcut: the file is not encrypted, so anyone signed in as you can read it;
    # put it on an encrypted drive (BitLocker) if that matters.
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        # the MCP server runs tools on worker threads; sqlite serializes access to one connection itself
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS spans (id INTEGER PRIMARY KEY, start REAL, end REAL, app TEXT, title TEXT)"
        )
        self.db.execute("CREATE INDEX IF NOT EXISTS spans_end ON spans (end)")
        self.db.commit()

    def add(self, app: str, title: str, now: float, max_gap: float) -> None:
        """Extend the last span if nothing changed; a gap (sleep, pause, recorder off) starts a new one."""
        last = self.db.execute("SELECT id, end, app, title FROM spans ORDER BY id DESC LIMIT 1").fetchone()
        if last and (last[2], last[3]) == (app, title) and 0 <= now - last[1] <= max_gap:
            self.db.execute("UPDATE spans SET end = ? WHERE id = ?", (now, last[0]))
        else:
            self.db.execute("INSERT INTO spans (start, end, app, title) VALUES (?, ?, ?, ?)", (now, now, app, title))
        self.db.commit()

    def search(self, text: str, since: float) -> list[tuple[float, float, str, str]]:
        """Newest spans whose app or title contains the text, ignoring case."""
        return self.db.execute(
            "SELECT start, end, app, title FROM spans WHERE end >= ? "
            "AND (instr(lower(app), lower(?)) OR instr(lower(title), lower(?))) ORDER BY start DESC LIMIT ?",
            (since, text, text, MAX_ROWS),
        ).fetchall()

    def time_by_app(self, since: float) -> list[tuple[str, float]]:
        return self.db.execute(
            "SELECT app, SUM(end - MAX(start, ?)) AS seconds FROM spans WHERE end >= ? "
            "GROUP BY app ORDER BY seconds DESC LIMIT ?",
            (since, since, MAX_ROWS),
        ).fetchall()

    def prune(self, before: float) -> int:
        return self._delete("end < ?", (before,))

    def forget(self, app: str | None = None) -> int:
        """Delete everything, or everything recorded for one app."""
        return self._delete("app = ?", (app.lower(),)) if app else self._delete("1", ())

    def _delete(self, where: str, args: tuple) -> int:
        count = self.db.execute(f"DELETE FROM spans WHERE {where}", args).rowcount  # `where` is fixed text above
        self.db.commit()
        self.db.execute("VACUUM")  # deleted rows otherwise stay readable in the file
        return count
