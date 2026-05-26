"""
Celery configuration for NETA AI background task processing.

Configures:
- Message broker (Redis)
- Result backend (Redis)
- Task routing and queues
- Celery Beat scheduler
- Worker and task timeouts
- Task serialization
"""

import os
from celery import Celery
from celery.schedules import crontab

# Initialize Celery app
app = Celery(__name__)

# Auto-discover tasks from app modules
app.autodiscover_tasks(['app.whatsapp_integration'])

# ============================================================================
# Broker and Backend Configuration
# ============================================================================

app.conf.broker_url = os.getenv(
    'CELERY_BROKER_URL',
    'redis://:password@localhost:6379/0'
)

app.conf.result_backend = os.getenv(
    'CELERY_RESULT_BACKEND',
    'redis://:password@localhost:6379/1'
)

# ============================================================================
# Task Configuration
# ============================================================================

# Serialization (JSON for interoperability)
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Timezone and time handling
app.conf.timezone = 'Asia/Kolkata'
app.conf.enable_utc = True

# Task acknowledgment (ensure task is complete before removing from queue)
app.conf.task_acks_late = True

# Reject tasks if worker is lost (prevent task loss)
app.conf.task_reject_on_worker_lost = True

# ============================================================================
# Worker Configuration
# ============================================================================

# Prefetch multiplier (number of unacked tasks per worker)
app.conf.worker_prefetch_multiplier = 4

# Max tasks per child process (prevents memory leaks)
app.conf.worker_max_tasks_per_child = 100

# Result backend settings
app.conf.result_expires = 3600  # Results expire after 1 hour

# ============================================================================
# Task Timeout Configuration
# ============================================================================

# Soft timeout (raises SoftTimeLimitExceeded exception)
app.conf.task_soft_time_limit = 600  # 10 minutes

# Hard timeout (kills the task)
app.conf.task_time_limit = 900  # 15 minutes

# Default task timeout
app.conf.task_default_timeout = 300  # 5 minutes

# ============================================================================
# Retry Configuration
# ============================================================================

# Automatically retry failed tasks
app.conf.task_autoretry_for = (Exception,)
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_max_retries = 3

# ============================================================================
# Task Routing (Queue Assignment)
# ============================================================================

# Define task routes for queue assignment
app.conf.task_routes = {
    # Alert generation tasks (high priority)
    'app.whatsapp_integration.celery_tasks.generate_opposition_alert': {
        'queue': 'alerts',
        'priority': 10,
    },
    'app.whatsapp_integration.celery_tasks.generate_booth_alert': {
        'queue': 'alerts',
        'priority': 10,
    },

    # WhatsApp delivery tasks (medium priority)
    'app.whatsapp_integration.celery_tasks.send_whatsapp_message': {
        'queue': 'notifications',
        'priority': 5,
    },

    # Monitoring tasks (lower priority)
    'app.whatsapp_integration.celery_tasks.check_delivery_status': {
        'queue': 'monitoring',
        'priority': 1,
    },

    # Maintenance tasks (lowest priority)
    'app.whatsapp_integration.celery_tasks.cleanup_old_alerts': {
        'queue': 'maintenance',
        'priority': 0,
    },
}

# ============================================================================
# Celery Beat Scheduler (Periodic Tasks)
# ============================================================================

app.conf.beat_schedule = {
    # Check delivery status every 5 minutes
    'check-delivery-status': {
        'task': 'app.whatsapp_integration.celery_tasks.check_delivery_status',
        'schedule': 300.0,  # Every 5 minutes
        'options': {
            'queue': 'monitoring',
            'priority': 1,
        }
    },

    # Clean up old alerts daily at 2 AM UTC
    'cleanup-old-alerts': {
        'task': 'app.whatsapp_integration.celery_tasks.cleanup_old_alerts',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM UTC
        'options': {
            'queue': 'maintenance',
            'priority': 0,
        }
    },
}

# ============================================================================
# Queue Configuration
# ============================================================================

# Define queues with routing
app.conf.task_default_queue = 'default'
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
        'priority': 5,
    },
    'alerts': {
        'exchange': 'alerts',
        'routing_key': 'alert.*',
        'priority': 10,
    },
    'notifications': {
        'exchange': 'notifications',
        'routing_key': 'notification.*',
        'priority': 5,
    },
    'monitoring': {
        'exchange': 'monitoring',
        'routing_key': 'monitor.*',
        'priority': 1,
    },
    'maintenance': {
        'exchange': 'maintenance',
        'routing_key': 'maintenance.*',
        'priority': 0,
    },
}

# ============================================================================
# Result Backend Configuration
# ============================================================================

# Redis result backend settings
app.conf.redis_max_connections = 10
app.conf.redis_socket_keepalive = True
app.conf.redis_socket_keepalive_interval = 60

# ============================================================================
# Logging Configuration
# ============================================================================

# Log level
app.conf.loglevel = os.getenv('CELERY_LOG_LEVEL', 'info')

# ============================================================================
# Environment-Specific Configuration
# ============================================================================

# Production overrides
if os.getenv('ENVIRONMENT') == 'production':
    # Stricter timeouts in production
    app.conf.task_soft_time_limit = 600  # 10 minutes
    app.conf.task_time_limit = 900  # 15 minutes

    # More aggressive prefetch multiplier
    app.conf.worker_prefetch_multiplier = 8

    # Disable task results in production (save Redis memory)
    app.conf.task_ignore_result = False
    app.conf.result_expires = 1800  # 30 minutes

# Development/Staging overrides
elif os.getenv('ENVIRONMENT') in ['development', 'staging']:
    # Relaxed timeouts for development
    app.conf.task_soft_time_limit = 900  # 15 minutes
    app.conf.task_time_limit = 1200  # 20 minutes

    # Prefetch fewer tasks for development
    app.conf.worker_prefetch_multiplier = 2

    # Keep results longer for debugging
    app.conf.result_expires = 7200  # 2 hours
    app.conf.loglevel = 'debug'


# ============================================================================
# Health Check Configuration
# ============================================================================

# Worker health check settings
app.conf.worker_disable_rate_limits = False
app.conf.worker_max_memory_per_child = 200000  # 200MB max per child process

# ============================================================================
# Exception Handling
# ============================================================================

# Default exception handlers
def on_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **kwds):
    """Handle task failures with logging."""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(
        f"Task {task_id} failed with exception: {exception}",
        exc_info=einfo
    )


def on_task_success(sender, result, task_id, args, kwargs, **kwds):
    """Handle task success."""
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Task {task_id} succeeded with result: {result}")


# Register signal handlers
from celery.signals import task_failure, task_success

task_failure.connect(on_task_failure)
task_success.connect(on_task_success)
