# Copyright 2025 Matias Piipari
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import ops
import ops.pebble
from ops import testing

from charm import CharmCharm


def test_config():
    """Return a dictionary with the test configuration."""
    return {
        "log-level": "debug",
        "openapi-schema-url": "https://example.com/schema",
        "origin-base-url": "https://example.com",
        "fixed-request-headers": "Authorization:Bearer token|X-Custom-Header:Value",
        "auth-endpoint-url": "https://auth.example.com/o/token/",
        "client-id": "example-client-id",
        "client-secret": "example-client-secret",
        "auth-scope": "example-scope",
    }


def test_proxy_pebble_ready():
    # Arrange:
    ctx = testing.Context(CharmCharm)
    container = testing.Container("proxy", can_connect=True)
    state_in = testing.State(containers={container}, config=test_config())

    # Act:
    state_out = ctx.run(ctx.on.pebble_ready(container), state_in)

    # Assert:
    assert (
        state_out.get_container(container.name).service_statuses["proxy"]
        == ops.pebble.ServiceStatus.ACTIVE
    )
    assert state_out.unit_status == testing.ActiveStatus()


def test_config_changed_valid_can_connect():
    """Test a config-changed event when the config is valid and the container can be reached."""
    # Arrange:
    ctx = testing.Context(CharmCharm)  # The default config will be read from charmcraft.yaml
    container = testing.Container("proxy", can_connect=True)
    state_in = testing.State(containers={container}, config=test_config())

    # Act:
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert:
    updated_plan = state_out.get_container(container.name).plan
    env = updated_plan.services["proxy"].environment
    assert env["LOG_LEVEL"] == "debug"
    assert env["OPENAPI_SCHEMA_URL"] == "https://example.com/schema"
    assert env["ORIGIN_BASE_URL"] == "https://example.com"
    assert env["FIXED_REQUEST_HEADERS"] == "Authorization:Bearer token|X-Custom-Header:Value"
    assert env["AUTH_ENDPOINT_URL"] == "https://auth.example.com/o/token/"
    assert env["CLIENT_ID"] == "example-client-id"
    assert env["CLIENT_SECRET"] == "example-client-secret"
    assert env["AUTH_SCOPE"] == "example-scope"
    assert state_out.unit_status == testing.ActiveStatus()

    # Check environment keys against charmcraft.yaml
    env_keys = env.keys()
    expected_keys = {
        "LOG_LEVEL",
        "OPENAPI_SCHEMA_URL",
        "ORIGIN_BASE_URL",
        "FIXED_REQUEST_HEADERS",
        "AUTH_ENDPOINT_URL",
        "CLIENT_ID",
        "CLIENT_SECRET",
        "AUTH_SCOPE",
    }
    assert env_keys == expected_keys


def test_config_changed_valid_cannot_connect():
    """Test a config-changed event when the config is valid but the container cannot be reached.

    We expect to end up in MaintenanceStatus waiting for the deferred event to
    be retried.
    """
    # Arrange:
    ctx = testing.Context(CharmCharm)
    container = testing.Container("proxy", can_connect=False)
    state_in = testing.State(containers={container}, config=test_config())

    # Act:
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert:
    assert isinstance(state_out.unit_status, testing.MaintenanceStatus)


def test_config_changed_invalid():
    """Test a config-changed event when the config is invalid."""
    # Arrange:
    ctx = testing.Context(CharmCharm)
    container = testing.Container("proxy", can_connect=True)
    invalid_level = "foobar"
    config = test_config()
    config["log-level"] = invalid_level
    state_in = testing.State(containers={container}, config=config)

    # Act:
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert:
    assert isinstance(state_out.unit_status, testing.BlockedStatus)
    assert invalid_level in state_out.unit_status.message
