"""Core module containing base classes, interfaces, and foundational components."""

from eclipse.core.config import ProcessorConfig
from eclipse.core.exceptions import (
    ConfigurationError,
    MyPackageError,
    ProcessingError,
    ValidationError,
)
from eclipse.core.interfaces import Configurable, Serializable, Validatable

__all__ = [
    "ProcessorConfig",
    "MyPackageError",
    "ValidationError",
    "ConfigurationError",
    "ProcessingError",
    "Serializable",
    "Validatable",
    "Configurable",
]
