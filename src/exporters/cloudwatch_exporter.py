import logging
import os

logger = logging.getLogger(__name__)


class CloudWatchExporter:
    def __init__(self):
        self._enabled = os.getenv("CLOUDWATCH_ENABLED", "false").lower() == "true"
        self._client = None
        if not self._enabled:
            return
        try:
            import boto3

            self._client = boto3.client(
                "cloudwatch",
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )
        except Exception as e:
            logger.warning("CloudWatch client init failed: %s", e)
            self._enabled = False

    def update(self, system_metrics: dict, container_metrics: list[dict]) -> None:
        if not self._enabled or not self._client:
            return
        try:
            metric_data = []
            timestamp = system_metrics.get("timestamp", 0)

            if "cpu_percent_total" in system_metrics:
                metric_data.append(
                    {
                        "MetricName": "SystemCpuAverage",
                        "Value": system_metrics["cpu_percent_total"],
                        "Unit": "Percent",
                    }
                )
            if "memory_percent" in system_metrics:
                metric_data.append(
                    {
                        "MetricName": "SystemMemoryPercent",
                        "Value": system_metrics["memory_percent"],
                        "Unit": "Percent",
                    }
                )

            metric_data.append(
                {
                    "MetricName": "ContainerCount",
                    "Value": len(container_metrics),
                    "Unit": "Count",
                }
            )

            if metric_data:
                self._client.put_metric_data(
                    Namespace="CloudInfraMonitor",
                    MetricData=metric_data,
                )
        except Exception:
            logger.exception("Failed to publish CloudWatch metrics")
