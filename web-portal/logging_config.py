#!/usr/bin/env python3
"""
Logging Configuration
Sets up structured logging for the application
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logging(log_level=logging.INFO, log_dir=None):
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (default: INFO)
        log_dir: Directory for log files (default: logs/ in web-portal directory)
    """
    if log_dir is None:
        log_dir = Path(__file__).parent / 'logs'
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for application logs (INFO and above)
    app_log_file = log_dir / 'app.log'
    app_file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_file_handler.setLevel(logging.INFO)
    app_file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app_file_handler.setFormatter(app_file_formatter)
    root_logger.addHandler(app_file_handler)
    
    # File handler for errors (ERROR and above)
    error_log_file = log_dir / 'errors.log'
    error_file_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    error_file_handler.setFormatter(error_file_formatter)
    root_logger.addHandler(error_file_handler)
    
    # File handler for security events (WARNING and above)
    security_log_file = log_dir / 'security.log'
    security_file_handler = RotatingFileHandler(
        security_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10  # Keep more security logs
    )
    security_file_handler.setLevel(logging.WARNING)
    security_file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    security_file_handler.setFormatter(security_file_formatter)
    
    # Security logger
    security_logger = logging.getLogger('phazevpn.security')
    security_logger.addHandler(security_file_handler)
    security_logger.setLevel(logging.WARNING)
    
    # System logger
    system_logger = logging.getLogger('phazevpn.system')
    system_logger.addHandler(app_file_handler)
    system_logger.setLevel(logging.INFO)
    
    # Suppress noisy loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def get_logger(name):
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
