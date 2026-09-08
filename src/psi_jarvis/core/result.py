from dataclasses import dataclass


@dataclass(frozen=True)
class Result[T]:
    """Representa el resultado de una operación del sistema."""

    success: bool
    data: T | None = None
    message: str | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str | None = None) -> "Result[T]":
        """Crea un resultado exitoso."""
        return cls(
            success=True,
            data=data,
            message=message,
        )

    @classmethod
    def fail(cls, message: str) -> "Result[T]":
        """Crea un resultado fallido."""
        return cls(
            success=False,
            data=None,
            message=message,
        )
