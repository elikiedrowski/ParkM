"""
Database layer for ParkM analytics persistence.

Supports PostgreSQL (Railway prod) and falls back gracefully to JSONL
if DATABASE_URL is not set or SQLAlchemy is unavailable.

Usage:
    from src.db.database import get_engine, init_db

    # On startup:
    init_db()

    # In loggers:
    engine = get_engine()
    if engine:
        # write to DB
    else:
        # write to JSONL
"""
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Graceful import — if SQLAlchemy isn't installed, everything degrades to JSONL
try:
    from sqlalchemy import (
        create_engine, MetaData, Table, Column,
        Integer, Float, String, Boolean, DateTime, Text,
        select, and_, or_,
    )
    _SA_AVAILABLE = True
except ImportError:
    _SA_AVAILABLE = False
    logger.warning("SQLAlchemy not installed — analytics will use JSONL fallback")


# ── Schema ────────────────────────────────────────────────────────────────

if _SA_AVAILABLE:
    _metadata = MetaData()

    classifications = Table("classifications", _metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("timestamp", DateTime, nullable=False),
        Column("ticket_id", String(50), nullable=True),
        Column("department_id", String(50), nullable=True),
        Column("intent", String(50), nullable=True),
        Column("confidence", Float, nullable=True),
        Column("complexity", String(20), nullable=True),
        Column("urgency", String(20), nullable=True),
        Column("language", String(20), nullable=True),
        Column("requires_refund", Boolean, default=False),
        Column("requires_human_review", Boolean, default=False),
        Column("routing_queue", String(100), nullable=True),
        Column("entities_json", Text, nullable=True),
        Column("processing_time_seconds", Float, nullable=True),
        Column("tagging_success", Boolean, default=False),
        Column("error", Text, nullable=True),
    )

    corrections = Table("corrections", _metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("timestamp", DateTime, nullable=False),
        Column("ticket_id", String(50), nullable=True),
        Column("department_id", String(50), nullable=True),
        Column("original_intent", String(50), nullable=False),
        Column("corrected_intent", String(50), nullable=False),
        Column("confidence", Integer, nullable=True),
        Column("is_misclassification", Boolean, default=False),
    )

    api_usage = Table("api_usage", _metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("timestamp", DateTime, nullable=False),
        Column("provider", String(20), nullable=False),
        Column("call_type", String(50), nullable=False),
        Column("model", String(50), nullable=True),
        Column("prompt_tokens", Integer, nullable=True),
        Column("completion_tokens", Integer, nullable=True),
        Column("total_tokens", Integer, nullable=True),
        Column("estimated_cost_usd", Float, nullable=True),
        Column("ticket_id", String(50), nullable=True),
        Column("success", Boolean, default=True),
        Column("error", Text, nullable=True),
    )

    template_usage = Table("template_usage", _metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("timestamp", DateTime, nullable=False),
        Column("template_file", String(100), nullable=False),
        Column("ticket_id", String(50), nullable=True),
        Column("intent", String(50), nullable=True),
    )

    error_logs = Table("error_logs", _metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("timestamp", DateTime, nullable=False),
        Column("level", String(20), nullable=False),
        Column("component", String(100), nullable=False),
        Column("ticket_id", String(50), nullable=True),
        Column("message", Text, nullable=False),
        Column("details", Text, nullable=True),  # JSON string
    )
else:
    _metadata = None
    classifications = None
    corrections = None
    api_usage = None
    template_usage = None
    error_logs = None


# ── Engine singleton ──────────────────────────────────────────────────────

_engine = None


def get_engine():
    """Return a SQLAlchemy engine, or None if DB is not configured."""
    global _engine
    if not _SA_AVAILABLE:
        return None
    if _engine is not None:
        return _engine

    url = os.environ.get("DATABASE_URL")
    if not url:
        return None

    # Railway provides postgres:// which SQLAlchemy 2.x requires as postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    try:
        _engine = create_engine(url, pool_pre_ping=True)
        logger.info("Database engine initialized")
        return _engine
    except Exception as e:
        logger.error(f"Failed to initialize database engine: {e}")
        return None


def init_db() -> bool:
    """Create all tables if they do not exist. Returns True if DB is available."""
    engine = get_engine()
    if not engine:
        logger.info("No DATABASE_URL set — analytics will use JSONL fallback")
        return False
    try:
        _metadata.create_all(engine)
        logger.info("Database tables created / verified")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


# ── Filter helper ─────────────────────────────────────────────────────────

def _apply_filters(stmt, table, days: Optional[int], department_id: Optional[str] = None):
    """Apply timestamp and optional department_id filters to a SELECT statement."""
    filters = []
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        filters.append(table.c.timestamp >= cutoff)
    if department_id and hasattr(table.c, "department_id"):
        # Mirror JSONL behaviour: rows with NULL department_id always pass
        filters.append(
            or_(table.c.department_id == department_id, table.c.department_id == None)
        )
    if filters:
        stmt = stmt.where(and_(*filters))
    return stmt


# ── Read helpers (return JSONL-compatible dicts) ──────────────────────────

def read_classifications(engine, days: Optional[int] = None, department_id: Optional[str] = None) -> List[Dict]:
    stmt = _apply_filters(select(classifications), classifications, days, department_id)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    result = []
    for row in rows:
        entities = {}
        if row["entities_json"]:
            try:
                entities = json.loads(row["entities_json"])
            except (json.JSONDecodeError, TypeError):
                pass
        ts = row["timestamp"]
        result.append({
            "timestamp": ts.isoformat() + "Z" if isinstance(ts, datetime) else str(ts),
            "ticket_id": row["ticket_id"],
            "department_id": row["department_id"],
            "intent": row["intent"],
            "confidence": row["confidence"],
            "complexity": row["complexity"],
            "urgency": row["urgency"],
            "language": row["language"],
            "requires_refund": row["requires_refund"],
            "requires_human_review": row["requires_human_review"],
            "routing_queue": row["routing_queue"],
            "entities": entities,
            "processing_time_seconds": row["processing_time_seconds"],
            "tagging_success": row["tagging_success"],
            "error": row["error"],
        })
    return result


def read_corrections(engine, days: Optional[int] = None, department_id: Optional[str] = None) -> List[Dict]:
    stmt = _apply_filters(select(corrections), corrections, days, department_id)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    result = []
    for row in rows:
        ts = row["timestamp"]
        result.append({
            "timestamp": ts.isoformat() + "Z" if isinstance(ts, datetime) else str(ts),
            "ticket_id": row["ticket_id"],
            "department_id": row["department_id"],
            "original_intent": row["original_intent"],
            "corrected_intent": row["corrected_intent"],
            "confidence": row["confidence"],
            "is_misclassification": row["is_misclassification"],
        })
    return result


def read_api_usage(engine, days: Optional[int] = None) -> List[Dict]:
    stmt = _apply_filters(select(api_usage), api_usage, days)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    result = []
    for row in rows:
        ts = row["timestamp"]
        result.append({
            "timestamp": ts.isoformat() + "Z" if isinstance(ts, datetime) else str(ts),
            "provider": row["provider"],
            "call_type": row["call_type"],
            "model": row["model"],
            "prompt_tokens": row["prompt_tokens"],
            "completion_tokens": row["completion_tokens"],
            "total_tokens": row["total_tokens"],
            "estimated_cost_usd": row["estimated_cost_usd"],
            "ticket_id": row["ticket_id"],
            "success": row["success"],
            "error": row["error"],
        })
    return result


def read_template_usage(engine, days: Optional[int] = None) -> List[Dict]:
    stmt = _apply_filters(select(template_usage), template_usage, days)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    result = []
    for row in rows:
        ts = row["timestamp"]
        result.append({
            "timestamp": ts.isoformat() + "Z" if isinstance(ts, datetime) else str(ts),
            "template_file": row["template_file"],
            "ticket_id": row["ticket_id"],
            "intent": row["intent"],
        })
    return result


def read_error_logs(engine, days: Optional[int] = None, level: Optional[str] = None, limit: int = 200) -> List[Dict]:
    """Read error_logs rows, newest first."""
    stmt = select(error_logs)
    filters = []
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        filters.append(error_logs.c.timestamp >= cutoff)
    if level:
        filters.append(error_logs.c.level == level.upper())
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(error_logs.c.timestamp.desc()).limit(limit)
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
    result = []
    for row in rows:
        ts = row["timestamp"]
        details = None
        if row["details"]:
            try:
                details = json.loads(row["details"])
            except (json.JSONDecodeError, TypeError):
                details = row["details"]
        result.append({
            "id": row["id"],
            "timestamp": ts.isoformat() + "Z" if isinstance(ts, datetime) else str(ts),
            "level": row["level"],
            "component": row["component"],
            "ticket_id": row["ticket_id"],
            "message": row["message"],
            "details": details,
        })
    return result
