"""
Application metrics and health monitoring utilities.
"""
import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HealthChecker:
    """
    Performs health checks for various application components.
    """

    def __init__(self, repo=None, external_services=None):
        self.repo = repo
        self.external_services = external_services or {}
        self.start_time = time.time()

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the application.

        Returns:
            Dictionary containing health status information
        """
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "checks": {}
        }

        try:
            # System health
            health_data["checks"]["system"] = self._check_system_health()

            # Database health
            if self.repo:
                health_data["checks"]["database"] = self._check_database_health()

            # External services health
            for service_name, service_config in self.external_services.items():
                health_data["checks"][f"external_{service_name}"] = self._check_external_service(
                    service_name, service_config
                )

            # Determine overall health status
            failed_checks = [
                check_name for check_name, check_result in health_data["checks"].items()
                if not check_result.get("healthy", False)
            ]

            if failed_checks:
                health_data["status"] = "degraded" if len(failed_checks) == 1 else "unhealthy"
                health_data["failed_checks"] = failed_checks

        except Exception as e:
            logger.error("Health check failed", extra={"error": str(e)}, exc_info=True)
            health_data["status"] = "unhealthy"
            health_data["error"] = str(e)

        return health_data

    def _check_system_health(self) -> Dict[str, Any]:
        """Check system resource health."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            system_health = {
                "healthy": True,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "disk_percent": round((disk.used / disk.total) * 100, 2)
            }

            # Define health thresholds
            if (cpu_percent > 90 or
                memory.percent > 90 or
                system_health["disk_percent"] > 90):
                system_health["healthy"] = False
                system_health["warning"] = "High resource usage detected"

            return system_health

        except Exception as e:
            logger.warning("System health check failed", extra={"error": str(e)})
            return {
                "healthy": False,
                "error": str(e)
            }

    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and basic operations."""
        try:
            # Test basic database operations
            start_time = time.time()

            # Try a simple query
            test_docs, total = self.repo.query("users", {}, limit=1, offset=0)

            response_time = round((time.time() - start_time) * 1000, 2)

            return {
                "healthy": True,
                "response_time_ms": response_time,
                "connection_status": "connected"
            }

        except Exception as e:
            logger.error("Database health check failed", extra={"error": str(e)})
            return {
                "healthy": False,
                "connection_status": "failed",
                "error": str(e)
            }

    def _check_external_service(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check external service health."""
        try:
            # This is a placeholder - would implement actual service checks
            # based on service type (HTTP, database, message queue, etc.)

            return {
                "healthy": True,
                "service": service_name,
                "status": "available"
            }

        except Exception as e:
            logger.error(
                "External service health check failed",
                extra={"service": service_name, "error": str(e)}
            )
            return {
                "healthy": False,
                "service": service_name,
                "status": "unavailable",
                "error": str(e)
            }


class MetricsCollector:
    """
    Collects and manages application metrics.
    """

    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_failed": 0,
            "response_times": [],
            "active_users": set(),
            "content_operations": {
                "imports": 0,
                "exports": 0,
                "vocab_operations": 0
            }
        }
        self.start_time = time.time()

    def record_request(self, method: str, path: str, status_code: int, response_time: float, user_id: str = None):
        """Record request metrics."""
        self.metrics["requests_total"] += 1

        if status_code >= 400:
            self.metrics["requests_failed"] += 1

        self.metrics["response_times"].append(response_time)

        # Keep only last 1000 response times to prevent memory issues
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

        if user_id:
            self.metrics["active_users"].add(user_id)

    def record_content_operation(self, operation_type: str):
        """Record content operation metrics."""
        if operation_type in self.metrics["content_operations"]:
            self.metrics["content_operations"][operation_type] += 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary."""
        response_times = self.metrics["response_times"]

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        error_rate = (self.metrics["requests_failed"] / max(self.metrics["requests_total"], 1)) * 100

        return {
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "requests": {
                "total": self.metrics["requests_total"],
                "failed": self.metrics["requests_failed"],
                "error_rate_percent": round(error_rate, 2)
            },
            "performance": {
                "avg_response_time_ms": round(avg_response_time * 1000, 2),
                "recent_response_times_count": len(response_times)
            },
            "users": {
                "active_users_count": len(self.metrics["active_users"])
            },
            "content_operations": self.metrics["content_operations"].copy()
        }

    def reset_metrics(self):
        """Reset accumulated metrics (useful for testing)."""
        self.metrics = {
            "requests_total": 0,
            "requests_failed": 0,
            "response_times": [],
            "active_users": set(),
            "content_operations": {
                "imports": 0,
                "exports": 0,
                "vocab_operations": 0
            }
        }
        self.start_time = time.time()


# Global metrics collector instance
metrics_collector = MetricsCollector()