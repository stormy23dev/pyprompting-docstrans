"""Custom exceptions for docstrans."""

from docstrans.constants import (
    EXIT_AUTH,
    EXIT_BAD_REQUEST,
    EXIT_CONFIG,
    EXIT_CONFLICT,
    EXIT_FILE,
    EXIT_INTERNAL,
    EXIT_NETWORK,
    EXIT_NOT_FOUND,
    EXIT_RATE_LIMIT,
    EXIT_SERVER,
)


class DocstransError(Exception):
    """Base error with an exit code."""

    exit_code: int = EXIT_INTERNAL

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigError(DocstransError):
    exit_code = EXIT_CONFIG


class NotFoundError(DocstransError):
    exit_code = EXIT_NOT_FOUND


class FileError(DocstransError):
    exit_code = EXIT_FILE


class ConflictError(DocstransError):
    exit_code = EXIT_CONFLICT


class NetworkError(DocstransError):
    exit_code = EXIT_NETWORK


class AuthError(DocstransError):
    exit_code = EXIT_AUTH


class RateLimitError(DocstransError):
    exit_code = EXIT_RATE_LIMIT


class BadRequestError(DocstransError):
    exit_code = EXIT_BAD_REQUEST


class ServerError(DocstransError):
    exit_code = EXIT_SERVER
