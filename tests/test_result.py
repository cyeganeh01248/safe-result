import asyncio
from typing import Any

import pytest

from safe_result import (
    Err,
    Ok,
    Result,
    ok,
    safe,
    safe_async,
    safe_async_with,
    safe_with,
)


def test_ok_creation_and_unwrap():
    result = Ok(42)
    assert result.value == 42
    assert result.unwrap() == 42
    assert not result.is_error()
    assert result.unwrap_or(0) == 42


def test_err_creation_and_unwrap():
    error = ValueError("test error")
    result = Err(error)
    assert result.error == error
    assert result.is_error()
    with pytest.raises(ValueError):
        result.unwrap()
    assert result.unwrap_or(42) == 42


def test_result_str_repr():
    ok_result = Ok(42)
    err_result = Err(ValueError("test error"))

    assert str(ok_result) == "Ok(42)"
    assert "Err" in str(err_result)
    assert "Ok(42)" == repr(ok_result)
    assert "Err(test error)" == repr(err_result)


def test_result_error_type_checking():
    result = Err(ValueError("test error"))
    assert result.is_error_of_type(ValueError)
    assert not result.is_error_of_type(TypeError)


def test_ok_type_guard():
    ok_result = Ok(42)
    err_result = Err(ValueError("test error"))

    assert ok(ok_result)
    assert not ok(err_result)


def test_safe_decorator():
    @safe
    def divide(a: int, b: int) -> float:
        return a / b

    result1 = divide(10, 2)
    assert ok(result1)
    assert result1.unwrap() == 5.0

    result2 = divide(10, 0)
    assert result2.is_error()
    assert result2.is_error_of_type(ZeroDivisionError)


def test_safe_with_decorator():
    @safe_with(ZeroDivisionError, ValueError)
    def divide(a: int, b: int) -> float:
        return a / b

    # Test successful case
    result1 = divide(10, 2)
    assert ok(result1)
    assert result1.unwrap() == 5.0

    # Test catching ZeroDivisionError
    result2 = divide(10, 0)
    assert result2.is_error()
    assert result2.is_error_of_type(ZeroDivisionError)

    # Test catching ValueError
    @safe_with(ValueError)
    def convert_to_int(s: str) -> int:
        return int(s)

    result3 = convert_to_int("not a number")
    assert result3.is_error()
    assert result3.is_error_of_type(ValueError)

    # Test that other exceptions are not caught
    @safe_with(ValueError)
    def raise_type_error():
        raise TypeError("type error")

    with pytest.raises(TypeError):
        raise_type_error()


def test_result_traceback():
    try:
        raise ValueError("test error")
    except ValueError as e:
        result = Err(e)
        assert result.traceback is not None
        assert "ValueError: test error" in result.traceback


def test_ok_pattern_matching():
    result = Ok(42)
    match result:
        case Ok(value):
            assert value == 42
        case _:  # type: ignore
            pytest.fail("Should match Ok pattern")


def test_err_pattern_matching():
    error = ValueError("test error")
    result = Err(error)
    match result:
        case Err(err):
            assert err == error
        case _:  # type: ignore
            pytest.fail("Should match Err pattern")


@pytest.mark.asyncio  # type: ignore
async def test_safe_async_decorator():
    @safe_async
    async def async_divide(a: int, b: int) -> float:
        return a / b

    # Test successful case
    result1 = await async_divide(10, 2)
    assert ok(result1)
    assert result1.unwrap() == 5.0

    # Test error case
    result2 = await async_divide(10, 0)
    assert result2.is_error()
    assert result2.is_error_of_type(ZeroDivisionError)

    # Test with asyncio.CancelledError
    @safe_async
    async def cancellable_operation() -> int:
        raise asyncio.CancelledError()
        return 42  # This line will never be reached

    result3 = await cancellable_operation()
    assert result3.is_error()
    # We can't use is_error_of_type here since CancelledError doesn't inherit from Exception
    assert isinstance(result3.error, asyncio.CancelledError)


@pytest.mark.asyncio  # type: ignore
async def test_safe_async_with_decorator():
    @safe_async_with(ZeroDivisionError, ValueError)
    async def async_divide(a: int, b: int) -> float:
        return a / b

    # Test successful case
    result1 = await async_divide(10, 2)
    assert ok(result1)
    assert result1.unwrap() == 5.0

    # Test catching ZeroDivisionError
    result2 = await async_divide(10, 0)
    assert result2.is_error()
    assert result2.is_error_of_type(ZeroDivisionError)

    # Test that other exceptions are not caught
    @safe_async_with(ValueError)
    async def raise_type_error() -> None:
        raise TypeError("type error")

    with pytest.raises(TypeError):
        await raise_type_error()

    # Test that CancelledError is always re-raised
    @safe_async_with(ValueError)  # CancelledError will always be re-raised
    async def cancellable_operation() -> int:
        raise asyncio.CancelledError()
        return 42

    with pytest.raises(asyncio.CancelledError):
        await cancellable_operation()


def test_complex_pattern_matching():
    # Test with multiple error types
    def create_error(error_type: str) -> Result[int, Exception]:
        match error_type:
            case "value":
                return Err(ValueError("Invalid value"))
            case "type":
                return Err(TypeError("Invalid type"))
            case "zero":
                return Err(ZeroDivisionError("Division by zero"))
            case _:
                return Ok(42)

    # Test pattern matching with multiple error types
    def handle_result(result: Result[Any, Exception]) -> str:
        match result:
            case Ok(value):
                return f"Success: {value}"
            case Err(ValueError() as e):
                return f"Value Error: {e}"
            case Err(TypeError() as e):
                return f"Type Error: {e}"
            case Err(ZeroDivisionError() as e):
                return f"Zero Division: {e}"
            case Err(e):
                return f"Unknown Error: {e}"
            case _:
                return "Unreachable"

    # Test different error scenarios
    value_error_result = create_error("value")
    assert handle_result(value_error_result) == "Value Error: Invalid value"

    type_error_result = create_error("type")
    assert handle_result(type_error_result) == "Type Error: Invalid type"

    zero_div_result = create_error("zero")
    assert handle_result(zero_div_result) == "Zero Division: Division by zero"

    success_result = create_error("success")
    assert handle_result(success_result) == "Success: 42"

    # Test nested pattern matching
    def nested_error_handler(result: Result[Any, Exception]) -> str:
        match result:
            case Ok(value) if isinstance(value, int) and value > 0:
                return "Positive integer"
            case Ok(value) if isinstance(value, int):
                return "Non-positive integer"
            case Ok(_):
                return "Non-integer value"
            case Err(e) if isinstance(e, (ValueError, TypeError)):
                return "Validation error"
            case Err(_):
                return "Other error"
            case _:
                return "Unreachable"

    assert nested_error_handler(Ok(42)) == "Positive integer"
    assert nested_error_handler(Ok(-1)) == "Non-positive integer"
    assert nested_error_handler(Ok("string")) == "Non-integer value"
    assert nested_error_handler(Err(ValueError())) == "Validation error"
    assert nested_error_handler(Err(ZeroDivisionError())) == "Other error"


def test_type_annotations():
    # Basic type annotations
    result: Result[int, ValueError] = Ok(42)
    assert result.value == 42
    assert result.unwrap() == 42
    assert not result.is_error()
    assert result.unwrap_or(0) == 42

    # Error case with type annotation
    err_result: Result[str, ValueError] = Err(ValueError("error"))
    assert err_result.is_error()
    assert isinstance(err_result.error, ValueError)
    with pytest.raises(ValueError):
        err_result.unwrap()

    # Function return type annotations
    def func() -> Result[int, ValueError]:
        return Ok(42)

    assert func().value == 42

    def err_func() -> Result[str, TypeError]:
        return Err(TypeError("type error"))

    assert err_func().is_error()

    # Nested type annotations
    nested: Result[list[int], Exception] = Ok([1, 2, 3])
    assert nested.unwrap() == [1, 2, 3]

    # Generic type parameters
    from typing import TypeVar

    T = TypeVar("T")

    def generic_func(value: T) -> Result[T, ValueError]:
        return Ok(value)

    str_result = generic_func("hello")
    assert str_result.unwrap() == "hello"
    int_result = generic_func(42)
    assert int_result.unwrap() == 42

    # Multiple error types
    def multi_error() -> Result[int, ValueError | TypeError]:
        if True:
            return Err(ValueError("value error"))
        return Err(TypeError("type error"))

    assert multi_error().is_error()

    # Type covariance
    class CustomError(ValueError):
        pass

    def covariant_func() -> Result[int, ValueError]:
        return Err(CustomError("custom error"))  # Should work due to covariance

    result = covariant_func()
    assert result.is_error()
    assert isinstance(result.error, CustomError)

    # Complex nested types
    complex_result: Result[dict[str, list[int]], Exception] = Ok({"nums": [1, 2, 3]})
    assert complex_result.unwrap()["nums"] == [1, 2, 3]

    # Optional types
    optional_result: Result[int | None, ValueError] = Ok(None)
    assert optional_result.unwrap() is None
