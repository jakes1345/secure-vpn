"""
Improved Logging Configuration

Provides centralized, structured logging with proper formatting,
rotation, and different log levels for different components.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
import os


class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter for console output
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors"""
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname:8}"
                f"{self.RESET}"
            )
        
        return super().format(record)


def setup_logging(
    log_level: str = 'INFO',
    log_file: Optional[Path] = None,
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/web-portal.log)
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        format_string: Custom format string
    
    Returns:
        Configured logger instance
    """
    # Get root logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Default format string
    if format_string is None:
        format_string = (
            '%(asctime)s | %(levelname)s | %(name)s | '
            '%(filename)s:%(lineno)d | %(message)s'
        )
    
    # Console handler with colors
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Use colored formatter for console
        if sys.stdout.isatty():  # Only use colors if outputting to terminal
            console_formatter = ColoredFormatter(
                format_string,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            console_formatter = logging.Formatter(
                format_string,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        # Default log file location
        if log_file is None:
            log_dir = Path(__file__).parent.parent / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'web-portal.log'
        else:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8',
        )
        file_handler.setLevel(level)
        
        # Plain formatter for file (no colors)
        file_formatter = logging.Formatter(
            format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Log initial message
    logger.info(f"Logging initialized at {log_level} level")
    if log_to_file:
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: str):
    """
    Change log level for all loggers
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)
    
    for handler in logging.getLogger().handlers:
        handler.setLevel(log_level)


def log_exception(logger: logging.Logger, message: str = "An error occurred"):
    """
    Log exception with full traceback
    
    Args:
        logger: Logger instance
        message: Error message
    """
    logger.exception(message)


def log_request(logger: logging.Logger, request):
    """
    Log HTTP request details
    
    Args:
        logger: Logger instance
        request: Flask request object
    """
    logger.info(
        f"Request: {request.method} {request.path} "
        f"from {request.remote_addr} "
        f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )


def log_response(logger: logging.Logger, response, duration_ms: float):
    """
    Log HTTP response details
    
    Args:
        logger: Logger instance
        response: Flask response object
        duration_ms: Request duration in milliseconds
    """
    logger.info(
        f"Response: {response.status_code} "
        f"({duration_ms:.2f}ms)"
    )


# Module-level logger for this file
logger = get_logger(__name__)


# Example usage and testing
if __name__ == '__main__':
    # Setup logging
    setup_logging(
        log_level='DEBUG',
        log_to_console=True,
        log_to_file=True,
    )
    
    # Test different log levels
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception:
        log_exception(logger, "Test exception occurred")
