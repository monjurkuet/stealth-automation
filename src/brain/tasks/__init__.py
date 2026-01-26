from src.brain.base import BaseAutomation
from src.brain.tasks.duckduckgo import DuckDuckGoTask
from src.brain.factory import AutomationFactory

AutomationFactory.register("duckduckgo", DuckDuckGoTask)

__all__ = ["BaseAutomation", "DuckDuckGoTask", "AutomationFactory"]
