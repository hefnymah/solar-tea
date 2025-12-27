"""Custom exception hierarchy for the package."""

from typing import Optional


class MyPackageError(Exception):
    """Base exception for all package errors.

    All custom exceptions in this package inherit from this class,
    allowing users to catch all package-specific errors with a single
    except clause.

    Attributes:
        message: Human-readable error description.
        code: Optional error code for programmatic handling.
    """

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __repr__(self) -> str:
        if self.code:
            return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"
        return f"{self.__class__.__name__}(message={self.message!r})"


class ValidationError(MyPackageError):
    """Raised when validation of input data fails.

    This exception is raised when:
    - Entity data fails validation rules
    - Input parameters are out of acceptable ranges
    - Required fields are missing or invalid
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[object] = None,
    ) -> None:
        super().__init__(message, code="VALIDATION_ERROR")
        self.field = field
        self.value = value


class ConfigurationError(MyPackageError):
    """Raised when configuration is invalid or missing.

    This exception is raised when:
    - Required configuration options are missing
    - Configuration values are invalid
    - Configuration file cannot be parsed
    """

    def __init__(self, message: str, config_key: Optional[str] = None) -> None:
        super().__init__(message, code="CONFIGURATION_ERROR")
        self.config_key = config_key


class ProcessingError(MyPackageError):
    """Raised when processing fails.

    This exception wraps underlying errors that occur during
    processing operations, preserving the original error for debugging.

    Attributes:
        original_error: The underlying exception that caused this error.
    """

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(message, code="PROCESSING_ERROR")
        self.original_error = original_error

    def __repr__(self) -> str:
        base = super().__repr__()
        if self.original_error:
            return f"{base}, original_error={self.original_error!r})"
        return base


class NotFoundError(MyPackageError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, identifier: str) -> None:
        message = f"{resource_type} with identifier '{identifier}' not found"
        super().__init__(message, code="NOT_FOUND")
        self.resource_type = resource_type
        self.identifier = identifier
