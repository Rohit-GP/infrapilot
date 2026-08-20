"""
WebSocket endpoint for real-time DiagnosisJob status updates
(the "websocket" module from the backend README).

Design note: `notify_job_status()` is called from job_service's background
task, which FastAPI runs in a worker thread (BackgroundTasks uses a
threadpool for sync callables) - not on the event loop that owns the
WebSocket connections. To safely push a message from that thread, the
main event loop is captured at app startup (see main.py) and the broadcast
coroutine is scheduled onto it with `asyncio.run_coroutine_threadsafe`.

No auth on the socket itself in this prototype (see docs/backend.md -
"Known simplifications"); a production version would validate a JWT
passed as a query param before accepting the connection.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.database import SessionLocal
from src.services import job_service
from src.services.job_service import JobNotFoundError

logger = logging.getLogger("job_status_ws")

router = APIRouter()

_connections: dict[str, list[WebSocket]] = {}
_main_loop: asyncio.AbstractEventLoop | None = None


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Called once from main.py's startup event."""
    global _main_loop
    _main_loop = loop


@router.websocket("/ws/jobs/{job_id}")
async def job_status_socket(websocket: WebSocket, job_id: str):
    await websocket.accept()
    _connections.setdefault(job_id, []).append(websocket)

    # Send the current status immediately on connect, not just on the next change.
    await _send_current_status(websocket, job_id)

    try:
        while True:
            # This endpoint is push-only; we still need to await something
            # so the connection stays open and disconnects are detected.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _connections.get(job_id, []).remove(websocket)
        if not _connections.get(job_id):
            _connections.pop(job_id, None)


async def _send_current_status(websocket: WebSocket, job_id: str) -> None:
    db = SessionLocal()
    try:
        job = job_service.get_job(db, job_id)
        await websocket.send_json(job_service.to_job_response(job).model_dump(mode="json"))
    except JobNotFoundError:
        await websocket.send_json({"error": "job not found", "job_id": job_id})
    finally:
        db.close()


async def _broadcast(job_id: str) -> None:
    sockets = _connections.get(job_id, [])
    if not sockets:
        return

    db = SessionLocal()
    try:
        job = job_service.get_job(db, job_id)
        payload = job_service.to_job_response(job).model_dump(mode="json")
    except JobNotFoundError:
        return
    finally:
        db.close()

    stale: list[WebSocket] = []
    for ws in sockets:
        try:
            await ws.send_json(payload)
        except Exception:  # noqa: BLE001 - connection may have dropped
            stale.append(ws)
    for ws in stale:
        sockets.remove(ws)


def notify_job_status(job_id: str) -> None:
    """Sync entry point - safe to call from a worker thread (see
    job_service.run_job_in_background, and the AI reasoning layer's
    persistence step which calls the equivalent Postgres update)."""
    if _main_loop is None:
        logger.warning("notify_job_status called before main loop was set; dropping notification for job %s", job_id)
        return
    asyncio.run_coroutine_threadsafe(_broadcast(job_id), _main_loop)
