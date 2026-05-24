#!/usr/bin/env python3
"""
Enhanced health check script for NETA AI services.

Checks:
- API service availability
- Database connectivity
- Redis connectivity
- Celery worker status
- System resources (CPU, memory, disk)
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

import asyncpg
import redis
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_URL = os.getenv('API_URL', 'http://localhost:8000')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://netaai_app:netaai_password@localhost:5432/netaai_prod')
REDIS_URL = os.getenv('REDIS_URL', 'redis://:redis_password@localhost:6379/0')
HEALTHCHECK_TIMEOUT = int(os.getenv('HEALTHCHECK_TIMEOUT', '10'))


class HealthChecker:
    """Comprehensive health checker for all NETA AI services."""

    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.healthy = True

    async def check_api(self) -> bool:
        """Check API service availability."""
        logger.info("Checking API service...")
        try:
            async with httpx.AsyncClient(timeout=HEALTHCHECK_TIMEOUT) as client:
                response = await client.get(f'{API_URL}/api/health')
                if response.status_code == 200:
                    data = response.json()
                    self.results['api'] = {
                        'status': 'healthy',
                        'url': API_URL,
                        'details': data,
                    }
                    logger.info("✓ API service is healthy")
                    return True
                else:
                    self.results['api'] = {
                        'status': 'unhealthy',
                        'url': API_URL,
                        'http_status': response.status_code,
                    }
                    logger.warning(f"✗ API returned status {response.status_code}")
                    self.healthy = False
                    return False
        except Exception as e:
            self.results['api'] = {
                'status': 'unreachable',
                'error': str(e),
            }
            logger.error(f"✗ API check failed: {e}")
            self.healthy = False
            return False

    async def check_database(self) -> bool:
        """Check PostgreSQL database connectivity."""
        logger.info("Checking PostgreSQL database...")
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            version = await conn.fetchval('SELECT version()')
            await conn.close()

            self.results['database'] = {
                'status': 'healthy',
                'version': version.split(',')[0] if version else 'unknown',
            }
            logger.info("✓ Database is healthy")
            return True
        except Exception as e:
            self.results['database'] = {
                'status': 'unhealthy',
                'error': str(e),
            }
            logger.error(f"✗ Database check failed: {e}")
            self.healthy = False
            return False

    async def check_redis(self) -> bool:
        """Check Redis connectivity."""
        logger.info("Checking Redis...")
        try:
            # Parse Redis URL
            redis_kwargs = {}
            if REDIS_URL.startswith('redis://'):
                parts = REDIS_URL.replace('redis://', '').split('@')
                if len(parts) == 2:
                    password = parts[0].split(':')[-1]
                    host_port = parts[1].split(':')
                    redis_kwargs = {
                        'host': host_port[0],
                        'port': int(host_port[1]) if len(host_port) > 1 else 6379,
                        'password': password if password else None,
                    }

            r = redis.Redis(**redis_kwargs, socket_connect_timeout=HEALTHCHECK_TIMEOUT)
            pong = r.ping()

            if pong:
                info = r.info()
                self.results['redis'] = {
                    'status': 'healthy',
                    'version': info.get('redis_version', 'unknown'),
                    'memory_mb': round(info.get('used_memory', 0) / 1024 / 1024, 2),
                }
                logger.info("✓ Redis is healthy")
                return True
        except Exception as e:
            self.results['redis'] = {
                'status': 'unhealthy',
                'error': str(e),
            }
            logger.error(f"✗ Redis check failed: {e}")
            self.healthy = False
            return False

    async def check_celery_worker(self) -> bool:
        """Check Celery worker status."""
        logger.info("Checking Celery worker...")
        try:
            result = subprocess.run(
                ['celery', '-A', 'app.whatsapp_integration.celery_tasks', 'inspect', 'ping'],
                capture_output=True,
                text=True,
                timeout=HEALTHCHECK_TIMEOUT,
            )

            if result.returncode == 0:
                self.results['celery_worker'] = {
                    'status': 'healthy',
                }
                logger.info("✓ Celery worker is healthy")
                return True
            else:
                self.results['celery_worker'] = {
                    'status': 'unhealthy',
                    'error': result.stderr,
                }
                logger.warning("✗ Celery worker not responding")
                self.healthy = False
                return False
        except FileNotFoundError:
            self.results['celery_worker'] = {
                'status': 'skipped',
                'reason': 'celery command not found',
            }
            logger.info("⊘ Celery check skipped (celery not installed)")
            return True
        except Exception as e:
            self.results['celery_worker'] = {
                'status': 'unhealthy',
                'error': str(e),
            }
            logger.error(f"✗ Celery worker check failed: {e}")
            self.healthy = False
            return False

    def check_system_resources(self) -> bool:
        """Check system resources (CPU, memory, disk)."""
        logger.info("Checking system resources...")
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            self.results['system'] = {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
            }

            if cpu_percent > 90:
                logger.warning(f"⚠ High CPU usage: {cpu_percent}%")
            if memory.percent > 90:
                logger.warning(f"⚠ High memory usage: {memory.percent}%")
            if disk.percent > 90:
                logger.warning(f"⚠ High disk usage: {disk.percent}%")

            logger.info("✓ System resources check completed")
            return True
        except ImportError:
            self.results['system'] = {
                'status': 'skipped',
                'reason': 'psutil not installed',
            }
            logger.info("⊘ System resources check skipped (psutil not installed)")
            return True
        except Exception as e:
            self.results['system'] = {
                'status': 'unhealthy',
                'error': str(e),
            }
            logger.error(f"✗ System resources check failed: {e}")
            return False

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        logger.info("Starting comprehensive health check...")

        # Run async checks
        await asyncio.gather(
            self.check_api(),
            self.check_database(),
            self.check_redis(),
            self.check_celery_worker(),
        )

        # Run sync checks
        self.check_system_resources()

        # Build summary
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy' if self.healthy else 'unhealthy',
            'checks': self.results,
        }

        return summary


async def main():
    """Main entry point."""
    checker = HealthChecker()
    summary = await checker.run_all_checks()

    # Print summary
    print(json.dumps(summary, indent=2))

    # Exit with appropriate code
    sys.exit(0 if checker.healthy else 1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Health check interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
