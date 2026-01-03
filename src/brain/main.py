import logging
from typing import Dict

# Import tasks to register them in the factory
import src.brain.tasks  # noqa: F401
from src.brain.factory import AutomationFactory
from src.bridge.native import NativeBridge

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrates automation tasks.
    Dispatches to appropriate platform tasks using factory.
    """

    def __init__(self, bridge: NativeBridge):
        self.bridge = bridge
        self.factory = AutomationFactory()

    async def dispatch(self, message: Dict) -> Dict:
        """
        Dispatch a message to appropriate task.

        Args:
            message: {
                "action": "start_search" | "start_task",
                "platform": "duckduckgo" | "google" | "facebook",
                "query": "search query or URL",
                ...
            }

        Returns:
            Standardized result from task
        """
        platform = message.get("platform")
        query = message.get("query")

        if not platform:
            platform = "duckduckgo"
            logger.info(f"No platform specified, defaulting to: {platform}")

        if not query:
            return {"status": "error", "message": "Query is required"}

        try:
            task = self.factory.create(platform, self.bridge)
            logger.info(f"Executing {platform} task: {query}")

            # Pass only relevant kwargs, excluding the ones used for orchestration
            kwargs_for_task = {
                k: v
                for k, v in message.items()
                if k not in ["action", "platform", "query"]
            }
            result = await task.execute(query, **kwargs_for_task)
            logger.info(f"Task completed: {result.get('status')}")
            return result

        except ValueError as e:
            logger.error(f"Invalid platform: {e}")
            return {
                "status": "error",
                "error": {"code": "INVALID_PLATFORM", "message": str(e)},
            }
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "status": "error",
                "error": {"code": "EXECUTION_ERROR", "message": str(e)},
            }

    async def list_platforms(self) -> Dict:
        """List all available platforms."""
        platforms = self.factory.list_available()
        platform_info = {}

        for platform in platforms:
            try:
                platform_info[platform] = self.factory.get_platform_info(platform)
            except Exception as e:
                platform_info[platform] = {f"error:{e}"}

        return {"status": "success", "platforms": platform_info}
