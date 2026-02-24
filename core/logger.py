import logging
import sys
from pythonjsonlogger import jsonlogger
from core.config import settings

def setup_logger(name: str = "brs_sasa", level: str = None) -> logging.Logger:
    """
    Set up a logger with structured JSON logging for production
    """
    if level is None:
        level = settings.LOG_LEVEL
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Use JSON formatter for structured logging in production
    if settings.DEBUG:
        # Human-readable format for development
        formatter = logging.Formatter(settings.LOG_FORMAT)
    else:
        # JSON format for production (better for log aggregation)
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={'timestamp': '@timestamp', 'level': 'severity'}
        )
    
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger