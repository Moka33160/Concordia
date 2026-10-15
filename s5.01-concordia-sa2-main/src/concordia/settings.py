"""
File: settings.py
Authors: SA2 | Eugene--Combette Talina, Fessenmeyer Noa, Gesson Mathis,
               Grosset-Janin Evan, Herbillon Anaee, Kuvan-Gee Cedric, Laurent
               Paco
Date: 03-09-2026
Description: Oracle connection settings read from the environment.
"""
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE_NAME = ".env"
PROJECT_MARKER = "pyproject.toml"

DEFAULT_PORT = 1521
REQUIRED_VARIABLES = (
    "ORACLE_HOSTNAME",
    "ORACLE_SERVICE_NAME",
    "ORACLE_USERNAME",
    "ORACLE_PASSWORD",
)


class ConfigurationError(RuntimeError):
    """Raised when the Oracle configuration is missing or unusable."""


@dataclass(frozen=True)
class OracleSettings:
    """Everything needed to open a connection to the Oracle database."""

    hostname: str
    port: int
    service_name: str
    username: str
    password: str = field(repr=False)

    @property
    def dsn(self) -> str:
        """Easy Connect string understood by the Oracle driver."""
        return f"{self.hostname}:{self.port}/{self.service_name}"

    @classmethod
    def from_env(
            cls, env: Mapping[str, str] | None = None
    ) -> "OracleSettings":
        """Build settings from `env`, defaulting to the process environment."""
        env = os.environ if env is None else env
        values = {
            name: (env.get(name) or "").strip() for name in REQUIRED_VARIABLES
        }

        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ConfigurationError(
                "Missing Oracle configuration: " + ", ".join(missing)
            )

        return cls(
            hostname=values["ORACLE_HOSTNAME"],
            port=cls._read_port(env),
            service_name=values["ORACLE_SERVICE_NAME"],
            username=values["ORACLE_USERNAME"],
            password=values["ORACLE_PASSWORD"],
        )

    @staticmethod
    def _read_port(env: Mapping[str, str]) -> int:
        raw_port = (env.get("ORACLE_PORT") or "").strip()
        if not raw_port:
            return DEFAULT_PORT
        try:
            return int(raw_port)
        except ValueError as error:
            raise ConfigurationError(
                f"ORACLE_PORT must be a whole number, got {raw_port!r}"
            ) from error


def find_env_file(start: Path | str = __file__) -> Path:
    """
    Look for the .env file, walking up from `start` without leaving the
    project.
    """
    for directory in Path(start).resolve().parents:
        candidate = directory / ENV_FILE_NAME
        if candidate.is_file():
            return candidate
        if (directory / PROJECT_MARKER).is_file():
            break
    return Path(ENV_FILE_NAME)


def load_oracle_settings(env_file: Path | str | None = None) -> OracleSettings:
    """
    Read the settings from `env_file`, completed by the process environment.
    """
    env_file = find_env_file() if env_file is None else env_file
    return OracleSettings.from_env({**os.environ, **dotenv_values(env_file)})
