#!/usr/bin/env python3
# Copyright 2025 Matias Piipari
# See LICENSE file for licensing details.
#
# Learn more at: https://juju.is/docs/sdk

"""Charm the service.

Refer to the following tutorial that will help you
develop a new k8s charm using the Operator Framework:

https://juju.is/docs/sdk/create-a-minimal-kubernetes-charm
"""

import logging
from typing import cast

import ops
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route

# Log messages can be retrieved using juju debug-log
logger = logging.getLogger(__name__)

VALID_LOG_LEVELS = ["info", "debug", "warning", "error", "critical"]
HOST = "0.0.0.0"
PORT = "8000"


class CharmCharm(ops.CharmBase):
    """Charm the service."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self._require_nginx_route()
        framework.observe(self.on["proxy"].pebble_ready, self._on_proxy_pebble_ready)
        framework.observe(self.on.config_changed, self._on_config_changed)

    def _on_proxy_pebble_ready(self, event: ops.PebbleReadyEvent):
        """Define and start a workload using the Pebble API.

        Change this example to suit your needs. You'll need to specify the right entrypoint and
        environment configuration for your specific workload.

        Learn more about interacting with Pebble at at https://juju.is/docs/sdk/pebble.
        """
        container = event.workload
        container.add_layer("proxy", self._pebble_layer, combine=True)
        container.replan()
        self.unit.status = ops.ActiveStatus()

    def _require_nginx_route(self):
        require_nginx_route(
            charm=self,
            service_hostname=self.model.config.get("hostname", self.app.name),
            service_name=self.app.name,
            service_port=PORT,
        )

    def _on_config_changed(self, event: ops.ConfigChangedEvent):
        """Handle changed configuration.

        Change this example to suit your needs. If you don't need to handle config, you can remove
        this method.

        Learn more about config at https://juju.is/docs/sdk/config
        """
        # Fetch the new config value
        log_level = cast(str, self.model.config["log-level"]).lower()

        if log_level in VALID_LOG_LEVELS:
            container = self.unit.get_container("proxy")
            try:
                container.add_layer("proxy", self._pebble_layer, combine=True)
                container.replan()
            except ops.pebble.ConnectionError:
                self.unit.status = ops.MaintenanceStatus("waiting for Pebble API")
                event.defer()
                return

            logger.debug("Log level changed to '%s'", log_level)
            self.unit.status = ops.ActiveStatus()
        else:
            self.unit.status = ops.BlockedStatus(f"invalid log level: '{log_level}'")

    @property
    def _pebble_layer(self) -> ops.pebble.LayerDict:
        """Return a dictionary representing a Pebble layer."""
        return {
            "summary": "proxy layer",
            "description": "pebble config layer for openapi-rest-proxy",
            "services": {
                "proxy": {
                    "override": "replace",
                    "summary": "proxy",
                    "command": f"uv run uvicorn proxy.app:app --host {HOST} --port {PORT}",
                    "startup": "enabled",
                    "environment": {
                        "LOG_LEVEL": self.model.config["log-level"],
                        "OPENAPI_SCHEMA_URL": self.model.config["openapi-schema-url"],
                        "ORIGIN_BASE_URL": self.model.config["origin-base-url"],
                        "FIXED_REQUEST_HEADERS": self.model.config["fixed-request-headers"],
                        "AUTH_ENDPOINT_URL": self.model.config["auth-endpoint-url"],
                        "CLIENT_ID": self.model.config["client-id"],
                        "CLIENT_SECRET": self.model.config["client-secret"],
                        "AUTH_SCOPE": self.model.config["auth-scope"],
                        "ENDPOINT_ALLOW_LIST": self.model.config.get("endpoint-allow-list", ""),
                    },
                }
            },
        }


if __name__ == "__main__":  # pragma: nocover
    ops.main(CharmCharm)
