import logging
import sys
from app.core.config import settings

def setup_logging():
    level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger = logging.getLogger("saleszy")
    logger.info(f"Logging configured for environment: {settings.ENVIRONMENT}")