"""
Kronvel GPU Cluster Simulator — entrypoint.

Exposes synthetic, fault-injectable GPU telemetry in Prometheus exposition format.
"""

import logging
import os
import time

from prometheus_client import start_http_server

from scenarios import ClusterSimulator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("kronvel.simulator")

DEFAULT_METRICS_PORT = 9400
DEFAULT_NODE_COUNT = 6
DEFAULT_SCENARIO = "normal"
DEFAULT_TICK_INTERVAL = 2.0


def _get_int_env(name: str, default: int) -> int:
    """Read an integer environment variable with a safe fallback."""

    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Invalid value for %s=%r. Using default: %d",
            name,
            value,
            default,
        )
        return default


def _get_float_env(name: str, default: float) -> float:
    """Read a float environment variable with a safe fallback."""

    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        logger.warning(
            "Invalid value for %s=%r. Using default: %.1f",
            name,
            value,
            default,
        )
        return default


def main() -> None:
    """Start the simulator and continuously publish telemetry."""

    port = _get_int_env("SIM_METRICS_PORT", DEFAULT_METRICS_PORT)
    node_count = _get_int_env("SIM_NODE_COUNT", DEFAULT_NODE_COUNT)
    tick_interval = _get_float_env(
        "SIM_TICK_INTERVAL_SECONDS",
        DEFAULT_TICK_INTERVAL,
    )
    scenario = os.getenv("SIM_SCENARIO", DEFAULT_SCENARIO)

    if not (1024 <= port <= 65535):
        logger.warning(
            "Invalid metrics port %d. Using default: %d",
            port,
            DEFAULT_METRICS_PORT,
        )
        port = DEFAULT_METRICS_PORT

    if node_count < 1:
        logger.warning(
            "Invalid node count %d. Using default: %d",
            node_count,
            DEFAULT_NODE_COUNT,
        )
        node_count = DEFAULT_NODE_COUNT

    if tick_interval <= 0:
        logger.warning(
            "Invalid tick interval %.2f. Using default: %.1f",
            tick_interval,
            DEFAULT_TICK_INTERVAL,
        )
        tick_interval = DEFAULT_TICK_INTERVAL

    logger.info(
        "Starting Kronvel simulator: nodes=%d scenario=%s port=%d interval=%.1fs",
        node_count,
        scenario,
        port,
        tick_interval,
    )

    simulator = ClusterSimulator(
        node_count=node_count,
        initial_scenario=scenario,
    )

    try:
        start_http_server(port)
    except OSError:
        logger.exception(
            "Failed to start Prometheus metrics server on port %d",
            port,
        )
        raise

    logger.info("Metrics exposed at http://0.0.0.0:%d/metrics", port)

    try:
        while True:
            simulator.tick()
            time.sleep(tick_interval)
    except KeyboardInterrupt:
        logger.info("Simulator shutting down")


if __name__ == "__main__":
    main()

    