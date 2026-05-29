"""
Server-Sent Events endpoint for live alert streaming.
Token is passed as query param (EventSource API doesn't support headers).
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse

from app.security_auth.utils import verify_token

logger = logging.getLogger(__name__)

sse_router = APIRouter(prefix="/api/sse", tags=["SSE"])


async def _event_stream(user_id: str):
    """Yield SSE events: connected ping, then heartbeat every 30s."""
    try:
        # Initial connected event
        yield f"event: connected\ndata: {json.dumps({'user_id': user_id, 'ts': datetime.now(timezone.utc).isoformat()})}\n\n"

        # Heartbeat loop — browser keeps connection alive
        while True:
            await asyncio.sleep(30)
            yield f"event: heartbeat\ndata: {json.dumps({'ts': datetime.now(timezone.utc).isoformat()})}\n\n"
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.debug("SSE stream closed: %s", exc)


@sse_router.get("/alerts")
async def sse_alerts(token: str = Query(..., description="JWT access token")):
    """
    Stream live alerts via Server-Sent Events.
    Authenticated via ?token= query param (EventSource limitation).
    """
    try:
        token_data = verify_token(token, token_type="access")
        user_id = str(token_data.user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return StreamingResponse(
        _event_stream(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
