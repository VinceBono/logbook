# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Vince Bono
"""What gets recorded. By default only app names; window titles are opt-in per app."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, fields
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    title_apps: frozenset[str] = frozenset()  # apps whose window titles are stored, e.g. "code.exe"
    exclude_apps: frozenset[str] = frozenset()  # apps that are not recorded at all
    retention_days: int = 30
    interval_seconds: int = 5
    database: Path = Path("~/.logbook/logbook.db").expanduser()
    pause_file: Path = Path("~/.logbook/PAUSE").expanduser()

    @classmethod
    def load(cls, path: Path) -> Settings:
        with path.open("rb") as f:
            raw = tomllib.load(f)
        unknown = set(raw) - {f.name for f in fields(cls)}
        if unknown:  # a typo such as "exclude_app" must not silently record what was meant to be excluded
            raise ValueError(f"{path}: unknown setting(s) {', '.join(sorted(unknown))}")
        default = cls()
        retention = raw.get("retention_days", default.retention_days)
        interval = raw.get("interval_seconds", default.interval_seconds)
        if type(retention) is not int or retention < 1 or type(interval) is not int or interval < 1:
            raise ValueError(f"{path}: retention_days and interval_seconds must be whole numbers of 1 or more")
        return cls(
            title_apps=frozenset(str(a).lower() for a in raw.get("title_apps", [])),
            exclude_apps=frozenset(str(a).lower() for a in raw.get("exclude_apps", [])),
            retention_days=retention,
            interval_seconds=interval,
            database=Path(raw.get("database", default.database)).expanduser(),
            pause_file=Path(raw.get("pause_file", default.pause_file)).expanduser(),
        )
