import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logger = logging.getLogger(__name__)

app = FastAPI(title="Stealth Automation HTTP Bridge")

_bridge = None
_orchestrator = None


class ExecuteRequest(BaseModel):
    action: str
    query: Optional[str] = None
    platform: Optional[str] = None
    selector: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
    kwargs: Optional[Dict[str, Any]] = None


def set_bridge_and_orchestrator(bridge, orchestrator):
    global _bridge, _orchestrator
    _bridge = bridge
    _orchestrator = orchestrator


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/list_platforms")
async def list_platforms() -> Dict[str, Any]:
    try:
        if not _orchestrator:
            raise HTTPException(status_code=503, detail="Orchestrator not initialized")
        result = await _orchestrator.list_platforms()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List platforms failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get_command")
async def get_command() -> Dict[str, Any]:
    """Get the next pending command for the extension to execute."""
    try:
        if not _bridge:
            raise HTTPException(status_code=503, detail="Bridge not initialized")
        command = _bridge.get_pending_command()
        if command:
            return {"status": "success", "command": command}
        return {"status": "idle"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get command failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/command_result")
async def command_result(result: Dict[str, Any]) -> Dict[str, str]:
    """Receive result from extension for a command."""
    try:
        if not _bridge:
            raise HTTPException(status_code=503, detail="Bridge not initialized")
        command_id = result.get("id")
        if command_id:
            _bridge.set_command_result(command_id, result)
            logger.info(f"Received result for command {command_id}")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Command result failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute(request: ExecuteRequest) -> Dict[str, Any]:
    try:
        if not _bridge or not _orchestrator:
            raise HTTPException(status_code=503, detail="Bridge not initialized")

        msg = {
            "action": request.action,
        }

        if request.query:
            msg["query"] = request.query

        if request.platform:
            msg["platform"] = request.platform

        if request.selector:
            msg["selector"] = request.selector

        if request.url:
            msg["url"] = request.url

        if request.text:
            msg["text"] = request.text

        if request.kwargs:
            msg.update(request.kwargs)

        _bridge.incoming_message(msg)

        if request.action in ["start_search", "start_task"]:
            result = await _orchestrator.dispatch(msg)
        elif request.action == "list_platforms":
            result = await _orchestrator.list_platforms()
        elif request.action == "ping":
            result = {"status": "success", "message": "pong"}
        else:
            raise HTTPException(
                status_code=400, detail=f"Invalid action: {request.action}"
            )

        logger.info(f"Execution completed: {request.action}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=9427, log_level="info")
