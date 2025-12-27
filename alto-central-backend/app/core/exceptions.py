"""Custom exception classes for the application."""

from typing import Any, Dict, Optional


class AltoException(Exception):
    """Base exception for Alto Central application."""

    def __init__(
        self,
        message: str,
        code: str = "ALTO_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AltoException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": str(identifier)},
        )


class DatabaseException(AltoException):
    """Database operation exception."""

    def __init__(self, message: str, source: str = "unknown"):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"source": source},
        )


class ValidationException(AltoException):
    """Validation error exception."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field} if field else {},
        )


class ExternalServiceException(AltoException):
    """External service (Supabase, TimescaleDB) exception."""

    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


class AuthenticationException(AltoException):
    """Authentication exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
        )


class AuthorizationException(AltoException):
    """Authorization exception."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
        )
