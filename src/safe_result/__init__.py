import asyncio
import traceback
from functools import wraps
from typing import (
    Awaitable,
    Callable,
    Generic,
    Optional,
    ParamSpec,
    Type,
    TypeGuard,
    TypeVar,
    cast,
)

T = TypeVar("T")
E = TypeVar("E", bound=Exception)
P = ParamSpec("P")
R = TypeVar("R")
ExcType = TypeVar("ExcType", bound=Exception)


class Result(Generic[T, E]):
    """A class that represents the result of an operation."""

    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        self.value = value
        self.error = error
        self.traceback: Optional[str] = None

        # Capture traceback if there's an error
        if error is not None:
            self.traceback = "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )

    def is_error(self) -> bool:
        """Check if this Result contains an error."""
        return self.error is not None

    def unwrap(self) -> T:
        """Return the value or raise the error."""
        if self.error:
            raise self.error
        return cast(T, self.value)

    def unwrap_or(self, default: T) -> T:
        """Return the value or a default if there's an error."""
        if self.error:
            return default
        return cast(T, self.value)

    # Using TypeGuard to fix the type checking issue
    def is_error_of_type(self, exc_type: Type[ExcType]) -> TypeGuard[ExcType]:
        """Check if the error is of a specific type."""
        return isinstance(self.error, exc_type)

    def __str__(self) -> str:
        if self.is_error():
            return f"Error: {self.error}"
        return str(self.value)

    def __repr__(self) -> str:
        if self.is_error():
            return f"Result(error={self.error})"
        return f"Result(value={self.value})"

    @staticmethod
    def safe(func: Callable[P, R]) -> Callable[P, "Result[R, Exception]"]:
        """
        Decorator that wraps a synchronous function to return a Result.
        The decorated function will never raise exceptions.

        Example:
            >>> @Result.safe
            ... def divide(a: int, b: int) -> float:
            ...     return a / b
            ...
            >>> result = divide(10, 0)  # Returns Result with ZeroDivisionError
        """

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> "Result[R, Exception]":
            try:
                return Result(value=func(*args, **kwargs))
            except Exception as e:
                return Result(error=e)

        return wrapper

    @staticmethod
    def safe_with(
        *exc_types: Type[ExcType],
    ) -> Callable[[Callable[P, R]], Callable[P, "Result[R, ExcType]"]]:
        """
        Decorator factory that wraps a synchronous function to return a Result.
        The decorated function will only catch the specified exception types.

        Example:
            >>> @Result.safe_with(ZeroDivisionError, ValueError)
            ... def divide(a: int, b: int) -> float:
            ...     return a / b
            ...
            >>> result = divide(10, 0)  # Returns Result with ZeroDivisionError
            >>> result = divide("10", 2)  # Returns Result with ValueError
            >>> result = divide(10, 2)  # Returns Result with value 5.0
        """

        def decorator(func: Callable[P, R]) -> Callable[P, "Result[R, ExcType]"]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> "Result[R, ExcType]":
                try:
                    return Result(value=func(*args, **kwargs))
                except exc_types as e:
                    return Result(error=cast(ExcType, e))
                # Re-raise other exceptions
                except Exception as e:
                    raise e

            return wrapper

        return decorator

    @staticmethod
    def safe_async(
        func: Callable[P, Awaitable[R]],
    ) -> Callable[P, Awaitable["Result[R, Exception]"]]:
        """
        Decorator that wraps an asynchronous function to return a Result.
        The decorated function will never raise exceptions.

        Example:
            >>> @Result.safe_async
            ... async def async_divide(a: int, b: int) -> float:
            ...     return a / b
            ...
            >>> result = await async_divide(10, 0)  # Returns Result with ZeroDivisionError
        """

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> "Result[R, Exception]":
            try:
                value = await func(*args, **kwargs)
                return Result(value=value)
            except asyncio.CancelledError as e:
                return Result(error=cast(E, e))
            except Exception as e:
                return Result(error=e)

        return wrapper

    @staticmethod
    def safe_async_with(
        *exc_types: Type[ExcType],
    ) -> Callable[
        [Callable[P, Awaitable[R]]], Callable[P, Awaitable["Result[R, ExcType]"]]
    ]:
        """
        Decorator factory that wraps an asynchronous function to return a Result.
        The decorated function will only catch the specified exception types.

        Example:
            >>> @Result.safe_async_with(ZeroDivisionError, ValueError)
            ... async def async_divide(a: int, b: int) -> float:
            ...     return a / b
            ...
            >>> result = await async_divide(10, 0)  # Returns Result with ZeroDivisionError
            >>> result = await async_divide("10", 2)  # Returns Result with ValueError
            >>> result = await async_divide(10, 2)  # Returns Result with value 5.0
        """

        def decorator(
            func: Callable[P, Awaitable[R]],
        ) -> Callable[P, Awaitable["Result[R, ExcType]"]]:
            @wraps(func)
            async def wrapper(
                *args: P.args, **kwargs: P.kwargs
            ) -> "Result[R, ExcType]":
                try:
                    value = await func(*args, **kwargs)
                    return Result(value=value)
                except asyncio.CancelledError:
                    raise  # Always re-raise CancelledError
                except exc_types as e:
                    return Result(error=cast(ExcType, e))
                # Re-raise other exceptions
                except Exception as e:
                    raise e

            return wrapper

        return decorator
