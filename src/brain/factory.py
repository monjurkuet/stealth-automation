import logging
from typing import Dict, Type
from src.brain.base import BaseAutomation
from src.brain.utils.validation import validate_config

logger = logging.getLogger(__name__)


class AutomationFactory:
    """
    Factory for creating automation task instances.
    Uses explicit task registration for control and clarity.
    """

    _tasks: Dict[str, Type[BaseAutomation]] = {}

    @classmethod
    def register(cls, platform: str, task_class: Type[BaseAutomation]):
        """Register a task class for a platform."""
        if platform in cls._tasks:
            logger.warning(f"Platform '{platform}' already registered, overwriting")

        cls._tasks[platform] = task_class
        logger.info(f"Registered platform: {platform}")

    @classmethod
    def create(cls, platform: str, bridge, **kwargs) -> BaseAutomation:
        """Create a task instance for given platform."""
        if platform not in cls._tasks:
            available = ", ".join(cls.list_available())
            raise ValueError(f"Unknown platform: '{platform}'. Available: {available}")

        task_class = cls._tasks[platform]
        instance = task_class(bridge, platform, **kwargs)
        return instance

    @classmethod
    def list_available(cls) -> list:
        """List all registered platforms."""
        return list(cls._tasks.keys())

    @classmethod
    def get_platform_info(cls, platform: str) -> Dict:
        """Get information about a platform."""
        if platform not in cls._tasks:
            raise ValueError(f"Unknown platform: {platform}")

        from pathlib import Path
        import yaml

        config_path = Path(f"config/{platform}.yaml")
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            return {
                "platform": platform,
                "task_class": cls._tasks[platform].__name__,
                "iteration_type": config["settings"]["iteration"]["type"],
                "requires_auth": config.get("auth", {}).get("required", False),
            }

        return {
            "platform": platform,
            "task_class": cls._tasks[platform].__name__,
            "config_not_found": True,
        }
