from __future__ import annotations

import json
import struct
import time

try:
    import pysqlite3 as sqlite3
except ImportError:
    import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import sqlite_vec


@dataclass(frozen=True)
class MemoryRecord:
    id: int
    kind: str
    key: str
    value: dict[str, Any]
    created_at: float
    score: float | None = None


def _serialize_vector(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


class MemoryStore:
    """Three-tier memory: semantic (facts), episodic (events), vector (recall)."""

    def __init__(self, db_path: Path, vector_dim: int) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.enable_load_extension(True)
        sqlite_vec.load(self._conn)
        self._conn.enable_load_extension(False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._vector_dim = vector_dim
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            f"""
            CREATE TABLE IF NOT EXISTS semantic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS episodic (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_episodic_kind_created ON episodic(kind, created_at);
            CREATE INDEX IF NOT EXISTS idx_episodic_key ON episodic(key);
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                evidence TEXT NOT NULL,
                repro TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS http_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_id TEXT NOT NULL,
                method TEXT NOT NULL,
                url TEXT NOT NULL,
                status INTEGER,
                request_headers TEXT,
                request_body TEXT,
                response_headers TEXT,
                response_body TEXT,
                elapsed_ms REAL,
                created_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_http_url ON http_log(url);
            CREATE VIRTUAL TABLE IF NOT EXISTS episodic_vec USING vec0(
                embedding float[{self._vector_dim}]
            );
            """
        )

    def note(self, key: str, value: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO semantic(key,value,updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",
            (key, json.dumps(value, default=str), time.time()),
        )

    def get_note(self, key: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT value FROM semantic WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def list_notes(self, prefix: str = "") -> list[MemoryRecord]:
        rows = self._conn.execute(
            "SELECT id,key,value,updated_at FROM semantic WHERE key LIKE ? ORDER BY updated_at DESC",
            (f"{prefix}%",),
        ).fetchall()
        return [
            MemoryRecord(id=r[0], kind="semantic", key=r[1], value=json.loads(r[2]), created_at=r[3])
            for r in rows
        ]

    def record_event(self, kind: str, key: str, value: dict[str, Any], embedding: list[float] | None = None) -> int:
        cur = self._conn.execute(
            "INSERT INTO episodic(kind,key,value,created_at) VALUES(?,?,?,?)",
            (kind, key, json.dumps(value, default=str), time.time()),
        )
        rowid = cur.lastrowid
        if embedding is not None:
            if len(embedding) != self._vector_dim:
                raise ValueError(
                    f"embedding dim {len(embedding)} != configured {self._vector_dim}"
                )
            self._conn.execute(
                "INSERT INTO episodic_vec(rowid,embedding) VALUES(?,?)",
                (rowid, _serialize_vector(embedding)),
            )
        return rowid

    def recall(self, embedding: list[float], k: int = 5) -> list[MemoryRecord]:
        if len(embedding) != self._vector_dim:
            raise ValueError(
                f"embedding dim {len(embedding)} != configured {self._vector_dim}"
            )
        rows = self._conn.execute(
            """
            SELECT e.id, e.kind, e.key, e.value, e.created_at, v.distance
            FROM episodic_vec v
            JOIN episodic e ON e.id = v.rowid
            WHERE v.embedding MATCH ? AND k = ?
            ORDER BY v.distance
            """,
            (_serialize_vector(embedding), k),
        ).fetchall()
        return [
            MemoryRecord(
                id=r[0], kind=r[1], key=r[2], value=json.loads(r[3]),
                created_at=r[4], score=r[5],
            )
            for r in rows
        ]

    def recent_events(self, kind: str | None = None, limit: int = 20) -> list[MemoryRecord]:
        if kind:
            rows = self._conn.execute(
                "SELECT id,kind,key,value,created_at FROM episodic WHERE kind=? ORDER BY created_at DESC LIMIT ?",
                (kind, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id,kind,key,value,created_at FROM episodic ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            MemoryRecord(id=r[0], kind=r[1], key=r[2], value=json.loads(r[3]), created_at=r[4])
            for r in rows
        ]

    def log_http(
        self,
        actor_id: str,
        method: str,
        url: str,
        status: int | None,
        request_headers: dict[str, str],
        request_body: Any,
        response_headers: dict[str, str],
        response_body: Any,
        elapsed_ms: float,
    ) -> int:
        cur = self._conn.execute(
            """
            INSERT INTO http_log(
                actor_id, method, url, status,
                request_headers, request_body, response_headers, response_body,
                elapsed_ms, created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                actor_id, method, url, status,
                json.dumps(request_headers, default=str),
                json.dumps(request_body, default=str),
                json.dumps(response_headers, default=str),
                json.dumps(response_body, default=str),
                elapsed_ms, time.time(),
            ),
        )
        return cur.lastrowid

    def get_http(self, request_id: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT actor_id,method,url,status,request_headers,request_body,response_headers,response_body,elapsed_ms,created_at "
            "FROM http_log WHERE id=?",
            (request_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "actor_id": row[0], "method": row[1], "url": row[2], "status": row[3],
            "request_headers": json.loads(row[4]),
            "request_body": json.loads(row[5]),
            "response_headers": json.loads(row[6]),
            "response_body": json.loads(row[7]),
            "elapsed_ms": row[8], "created_at": row[9],
        }

    def record_finding(
        self,
        endpoint: str,
        severity: str,
        title: str,
        evidence: dict[str, Any],
        repro: str,
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO findings(endpoint,severity,title,evidence,repro,created_at) VALUES(?,?,?,?,?,?)",
            (endpoint, severity, title, json.dumps(evidence, default=str), repro, time.time()),
        )
        return cur.lastrowid

    def list_findings(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id,endpoint,severity,title,evidence,repro,created_at FROM findings ORDER BY created_at DESC"
        ).fetchall()
        return [
            {
                "id": r[0], "endpoint": r[1], "severity": r[2], "title": r[3],
                "evidence": json.loads(r[4]), "repro": r[5], "created_at": r[6],
            }
            for r in rows
        ]

    def prune_episodic(self, older_than_seconds: float) -> int:
        cutoff = time.time() - older_than_seconds
        cur = self._conn.execute("DELETE FROM episodic WHERE created_at < ?", (cutoff,))
        return cur.rowcount

    def close(self) -> None:
        self._conn.close()
