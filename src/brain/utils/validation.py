import json
import jsonschema
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_config(config: dict):
    """
    Validate task configuration against JSON schema.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValidationError: If configuration is invalid
    """
    schema_path = Path("config/schema.json")

    if not schema_path.exists():
        logger.warning("Config schema not found, skipping validation")
        return

    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load schema: {e}")
        return

    try:
        jsonschema.validate(config, schema)
        logger.info("Configuration validation passed")
    except jsonschema.ValidationError as e:
        logger.error(f"Configuration validation failed: {e.message}")
        raise
