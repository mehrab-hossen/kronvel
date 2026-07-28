"""
Kronvel GPU Cluster Simulator — metric definitions and fault-injection scenarios.
"""

import logging
import random
from typing import Literal

from prometheus_client import Gauge

logger = logging.getLogger("kronvel.simulator")

# --- Prometheus metric definitions (DCGM-exporter-style naming) ---
GPU_TEMP = Gauge(
    "DCGM_FI_DEV_GPU_TEMP", "GPU temperature in Celsius", ["node", "gpu"]
)
GPU_UTIL = Gauge(
    "DCGM_FI_DEV_GPU_UTIL", "GPU utilization percent", ["node", "gpu"]
)
GPU_MEM_USED = Gauge(
    "DCGM_FI_DEV_FB_USED", "GPU framebuffer memory used (MiB)", ["node", "gpu"]
)
GPU_POWER = Gauge(
    "DCGM_FI_DEV_POWER_USAGE", "GPU power usage (Watts)", ["node", "gpu"]
)
GPU_XID_ERROR = Gauge(
    "DCGM_FI_DEV_XID_ERRORS", "Most recent XID error code (0 = none)", ["node", "gpu"]
)
GPU_ECC_SBE = Gauge(
    "DCGM_FI_DEV_ECC_SBE_VOL_TOTAL",
    "Cumulative single-bit volatile ECC errors",
    ["node", "gpu"],
)

Scenario = Literal["normal", "thermal_spike", "xid_error", "ecc_error"]

SCENARIOS = frozenset(
    {
        "normal",
        "thermal_spike",
        "xid_error",
        "ecc_error",
    }
)

# Real-world XID error codes used for realism (not exhaustive):
# 79 = GPU has fallen off the bus
# 63 = Row remapping event (memory degradation)
# 13 = Graphics engine exception
_XID_CODES = [79, 63, 13]


def _clamp(value: float, low: float, high: float) -> float:
    """Clamp a value to the inclusive range [low, high]."""
    return max(low, min(value, high))


class GPUState:
    """Tracks and drifts the simulated telemetry for a single GPU."""

    def __init__(self, node: str, gpu_index: str):
        self.node = node
        self.gpu_index = gpu_index

        self.temp = random.uniform(45, 55)
        self.util = random.uniform(10, 40)
        self.mem_used = random.uniform(2000, 6000)
        self.power = random.uniform(80, 150)

        self.xid = 0
        self.ecc_sbe = 0

    def apply_normal_drift(self) -> None:
        """Apply natural random-walk drift to GPU telemetry.

        This models normal hardware fluctuations without forcing the GPU back
        into a healthy operating range. Fault injection scenarios (e.g.
        thermal_spike) are therefore allowed to accumulate over time.
        """

        # Allow temperatures to drift across the full physical operating range.
        # Healthy temperatures naturally remain around 45–55°C because the random
        # walk is centered near the initial value, while injected thermal faults
        # can continue rising toward the maximum.
        self.temp = _clamp(
            self.temp + random.uniform(-1.0, 1.0),
            35.0,
            98.0,
        )

        self.util = _clamp(
            self.util + random.uniform(-5.0, 5.0),
            0.0,
            95.0,
        )

        self.mem_used = _clamp(
            self.mem_used + random.uniform(-200, 200),
            500.0,
            15000.0,
        )

        self.power = _clamp(
            75 + (self.util / 100.0) * 225 + random.uniform(-5.0, 5.0),
            50.0,
            400.0,
        )

        # Transient XID errors clear each tick unless re-triggered.
        self.xid = 0

    def apply_thermal_spike(self) -> None:
        """Inject a sustained thermal anomaly."""

        self.temp = _clamp(
            self.temp + random.uniform(1.0, 5.5),
            35.0,
            98.0,
        )
        self.power = _clamp(
            self.power + random.uniform(10.0, 20.0),
            50.0,
            400.0,
        )
        self.util = _clamp(
            self.util + random.uniform(2.0, 8.0),
            0.0,
            100.0,
        )

        logger.info("Thermal spike injected on %s (GPU %s)", self.node, self.gpu_index)

    def apply_xid_error(self) -> None:
        """Inject a transient GPU XID error."""

        self.xid = random.choice(_XID_CODES)
        self.util = max(self.util - random.uniform(20.0, 40.0), 0.0)

        logger.info(
            "Injected XID %d on %s (GPU %s)",
            self.xid,
            self.node,
            self.gpu_index,
        )

    def apply_ecc_error(self) -> None:
        """Inject cumulative single-bit ECC errors."""

        self.ecc_sbe += random.randint(1, 5)
        self.temp = _clamp(
            self.temp + random.uniform(0.5, 1.5),
            35.0,
            98.0,
        )

        logger.info(
            "Injected %d ECC error(s) on %s (GPU %s)",
            self.ecc_sbe,
            self.node,
            self.gpu_index,
        )

    def publish(self) -> None:
        """Publish the current telemetry snapshot to Prometheus."""

        labels = {"node": self.node, "gpu": self.gpu_index}

        GPU_TEMP.labels(**labels).set(round(self.temp, 2))
        GPU_UTIL.labels(**labels).set(round(self.util, 2))
        GPU_MEM_USED.labels(**labels).set(round(self.mem_used, 2))
        GPU_POWER.labels(**labels).set(round(self.power, 2))
        GPU_XID_ERROR.labels(**labels).set(self.xid)
        GPU_ECC_SBE.labels(**labels).set(self.ecc_sbe)


class ClusterSimulator:
    """Owns all simulated GPU nodes and drives fault injection."""

    def __init__(
        self,
        node_count: int,
        initial_scenario: Scenario = "normal",
    ):
        if initial_scenario not in SCENARIOS:
            logger.warning(
                "Unknown scenario '%s', defaulting to 'normal'",
                initial_scenario,
            )
            initial_scenario = "normal"

        self.scenario: Scenario = initial_scenario

        self.nodes: list[GPUState] = [
            GPUState(
                node=f"gpu-node-{i + 1}",
                gpu_index="0",
            )
            for i in range(node_count)
        ]

        # Keep faults isolated to one node for a clearer demo.
        self.fault_target = self.nodes[-1] if self.nodes else None
        self.tick_count = 0

    def set_scenario(self, scenario: Scenario) -> None:
        """Switch the active fault-injection scenario."""

        if scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}")

        logger.info("Scenario changed: %s -> %s", self.scenario, scenario)
        self.scenario = scenario

    def tick(self) -> None:
        """Advance the simulator by one time step."""

        self.tick_count += 1

        for node in self.nodes:
            node.apply_normal_drift()

        if self.fault_target and self.scenario != "normal":
            if self.scenario == "thermal_spike":
                self.fault_target.apply_thermal_spike()
            elif self.scenario == "xid_error" and self.tick_count % 5 == 0:
                self.fault_target.apply_xid_error()
            elif self.scenario == "ecc_error" and self.tick_count % 3 == 0:
                self.fault_target.apply_ecc_error()

        for node in self.nodes:
            node.publish()

    