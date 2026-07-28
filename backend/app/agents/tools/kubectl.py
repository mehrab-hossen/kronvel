"""
Agent tool: scoped, policy-relevant Kubernetes actions.

SECURITY-SENSITIVE — see SECURITY.md. This tool intentionally exposes only an
explicit allowlist of safe, reversible actions (cordon/uncordon a node). No
delete, no exec, no arbitrary kubectl passthrough. The credentials used here
must be the scoped kronvel-agent ServiceAccount from Task 1 — never a
cluster-admin context. Any expansion of ALLOWED_ACTIONS requires explicit
security review per SECURITY.md, not routine approval.

Defaults to dry_run=True. The policy gate that decides when dry_run may be
overridden is built Day 5-6 (agents/policy.py) — this tool itself has no
opinion on whether an action *should* run, only on whether it's allowed to
exist at all and what happens when it's told to actually execute.
"""

import logging
import os

from kubernetes import client as k8s_client
from kubernetes import config as k8s_config
from kubernetes.client.rest import ApiException

logger = logging.getLogger("kronvel.agents.tools.kubectl")

ALLOWED_ACTIONS = {"cordon", "uncordon"}

# Temporary MVP mapping.
#
# The simulator exposes six logical GPU nodes while the local Kind cluster
# contains a single Kubernetes node.
NODE_NAME_MAP = {
    # "gpu-node-1": "kronvel-dev-control-plane",
    # "gpu-node-2": "kronvel-dev-control-plane",
    # "gpu-node-3": "kronvel-dev-control-plane",
    # "gpu-node-4": "kronvel-dev-control-plane",
    # "gpu-node-5": "kronvel-dev-control-plane",
    # Only gpu-node-6 represents the real Kubernetes node.
    "gpu-node-6": "kronvel-dev-control-plane",
}

K8S_NODE_NAME = "kronvel-dev-control-plane"


class KubectlTool:
    name = "kubectl_action"

    description = (
        "Execute a scoped, allowlisted Kubernetes action "
        "(cordon or uncordon a node). Defaults to dry_run=True."
    )

    def __init__(
        self,
        kubeconfig_path: str | None = None,
        in_cluster: bool = False,
    ):
        if in_cluster:
            k8s_config.load_incluster_config()
        else:
            kubeconfig_path = kubeconfig_path or os.getenv("KUBECONFIG")

            if kubeconfig_path:
                k8s_config.load_kube_config(config_file=kubeconfig_path)
            else:
                k8s_config.load_kube_config()

        self._api = k8s_client.CoreV1Api()

    def _resolve_node_name(self, node: str) -> str:
        """Translate simulator node names into Kubernetes node names."""
        return NODE_NAME_MAP.get(node, node)

    # async def ensure_uncordoned(self) -> None:
    #     """Ensure the Kubernetes node starts in a schedulable state."""

    #     body = {"spec": {"unschedulable": False}}

    #     try:
    #         self._api.patch_node(K8S_NODE_NAME, body)
    #         logger.info(
    #             "Reset Kubernetes node '%s' to schedulable.",
    #             K8S_NODE_NAME,
    #         )
    #     except ApiException:
    #         logger.exception(
    #             "Failed to reset Kubernetes node '%s'.",
    #             K8S_NODE_NAME,
    #         )
    #         raise

    # async def is_cordoned(self, node: str) -> bool:
    #     """
    #     Return True if the Kubernetes node is currently cordoned.
    #     """

    #     k8s_node = self._resolve_node_name(node)

    #     try:
    #         node_obj = self._api.read_node(k8s_node)
    #     except ApiException as exc:
    #         logger.error(
    #             "Failed reading simulator node '%s' (k8s node '%s'): %s",
    #             node,
    #             k8s_node,
    #             exc,
    #         )
    #         return False

    #     return bool(node_obj.spec.unschedulable)

    async def is_cordoned(self, node: str) -> bool:
        k8s_node = NODE_NAME_MAP.get(node)

        # Simulator-only nodes are never considered cordoned.
        if k8s_node is None:
            return False

        try:
            node_obj = self._api.read_node(k8s_node)
            return bool(node_obj.spec.unschedulable)
        except ApiException:
            logger.exception("Failed to read Kubernetes node '%s'", k8s_node)
            return False

    async def run(
        self,
        action: str,
        node: str,
        dry_run: bool = True,
    ) -> dict:
        if action not in ALLOWED_ACTIONS:
            raise ValueError(
                f"Action '{action}' is not in the allowlist {ALLOWED_ACTIONS}"
            )

        k8s_node = self._resolve_node_name(node)
        k8s_node = NODE_NAME_MAP.get(node)

        if k8s_node is None:
            raise ValueError(
                f"Simulator node '{node}' has no Kubernetes mapping."
            )

        unschedulable = action == "cordon"

        if dry_run:
            logger.info(
                "[DRY RUN] Would set node '%s' (k8s='%s') unschedulable=%s",
                node,
                k8s_node,
                unschedulable,
            )
            return {
                "node": node,
                "action": action,
                "dry_run": True,
                "executed": False,
            }

        body = {
            "spec": {
                "unschedulable": unschedulable,
            }
        }

        try:
            self._api.patch_node(k8s_node, body)
        except ApiException as exc:
            logger.error(
                "kubectl action '%s' failed for simulator node '%s' "
                "(k8s node '%s'): %s",
                action,
                node,
                k8s_node,
                exc,
            )
            raise

        logger.info(
            "Executed '%s' on simulator node '%s' (k8s node '%s')",
            action,
            node,
            k8s_node,
        )

        return {
            "node": node,
            "action": action,
            "dry_run": False,
            "executed": True,
        }
    