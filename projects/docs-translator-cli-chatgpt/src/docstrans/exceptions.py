from __future__ import annotations

from dataclasses import dataclass

from docstrans import constants


@dataclass
class DocstransError(Exception):
    message: str
    exit_code: int = constants.EXIT_INTERNAL

    def __str__(self) -> str:
        return self.message


class ConfigError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_CONFIG)


class LocalNotFoundError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_NOT_FOUND)


class FileOperationError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_FILE)


class LocalConflictError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_CONFLICT)


class NetworkError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_NETWORK)


class ApiAuthError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_AUTH)


class ApiRateLimitError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_RATE_LIMIT)


class ApiBadRequestError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_BAD_REQUEST)


class ApiServerError(DocstransError):
    def __init__(self, message: str) -> None:
        super().__init__(message, constants.EXIT_SERVER)
