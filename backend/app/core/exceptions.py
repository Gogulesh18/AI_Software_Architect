"""Shared application exceptions, mapped to HTTP responses in app/api."""


class AppError(Exception):
    """Base class for all expected application errors."""

    status_code = 500

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class RepoIngestError(AppError):
    """Cloning/unzipping/reading the repository failed."""

    status_code = 400


class JobNotFoundError(AppError):
    status_code = 404


class RepositoryNotFoundError(AppError):
    status_code = 404


class InvalidJobStateError(AppError):
    """Requested an artifact (report/diagram/etc.) before the job produced it."""

    status_code = 409
