from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
import asyncio
from dashboard.backend.services.csv_reader import read_latest

router = APIRouter(prefix="/stream")

@router.get("/telemetry")
async def stream_telemetry():
    async def event_generator():
        while True:
            latest = read_latest()
            yield {"data": latest.model_dump_json()}
            await asyncio.sleep(5)

    return EventSourceResponse(event_generator())
