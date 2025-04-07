import logging
from app.config import settings

def setup_logging():
    logging.basicConfig(
        filename=settings.LOG_FILE,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logging.getLogger().addHandler(logging.StreamHandler())  # Also log to console
    return logging.getLogger(__name__)

logger = setup_logging()