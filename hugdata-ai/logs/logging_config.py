import logging
import logging.config
import os
from typing import Dict, Any

def setup_logging():
    """Configure logging for the FastAPI AI service."""
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    environment = os.getenv('ENVIRONMENT', 'development')
    
    config: Dict[str, Any] = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '[%(asctime)s] %(levelname)s %(name)s:%(lineno)d - %(funcName)s() - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
                'datefmt': '%Y-%m-%dT%H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'json' if environment == 'production' else 'detailed',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'json' if environment == 'production' else 'detailed',
                'filename': '/app/logs/hugdata-ai.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json' if environment == 'production' else 'detailed',
                'filename': '/app/logs/hugdata-ai-error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            'hugdata': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'uvicorn': {
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'sqlalchemy.engine': {
                'level': 'WARNING' if environment == 'production' else 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'celery': {
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'dagster': {
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file']
        }
    }
    
    # Create logs directory if it doesn't exist
    os.makedirs('/app/logs', exist_ok=True)
    
    logging.config.dictConfig(config)
    
    # Set up logger for the application
    logger = logging.getLogger('hugdata')
    logger.info(f"Logging configured for environment: {environment}, level: {log_level}")
    
    return logger