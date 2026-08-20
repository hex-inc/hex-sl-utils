"""Connection configuration shared by test-only SQL drivers."""

from __future__ import annotations

import os


class ConnectionVarsNotSetError(RuntimeError):
    """Raised when an explicitly requested driver is missing configuration."""

    def __init__(self, variable_name: str, driver_name: str) -> None:
        super().__init__(
            f"Connection environment variable {variable_name} is not set for "
            f"the {driver_name} driver."
        )
        self.variable_name = variable_name
        self.driver_name = driver_name


def get_env_var(name: str, driver_name: str) -> str:
    """Read a required connection setting when its driver is constructed."""
    value = os.environ.get(name)
    if value is None:
        raise ConnectionVarsNotSetError(name, driver_name)
    return value


def get_env_port(name: str, driver_name: str) -> int:
    """Read a required TCP port from the environment."""
    return _parse_port(get_env_var(name, driver_name), name)


def get_local_port(dialect_name: str, default: int) -> int:
    """Read the loopback port for a local Compose-backed dialect."""
    variable_name = f"HEX_SL_UTILS_DATABASE_{dialect_name.upper()}_PORT"
    value = os.environ.get(variable_name)
    if value is None:
        return default
    return _parse_port(value, variable_name)


def _parse_port(value: str, variable_name: str) -> int:
    """Validate and convert an environment port value."""
    try:
        port = int(value)
    except ValueError as error:
        msg = f"{variable_name} must be an integer port"
        raise ValueError(msg) from error
    if not 1 <= port <= 65_535:
        msg = f"{variable_name} must be between 1 and 65535"
        raise ValueError(msg)
    return port
