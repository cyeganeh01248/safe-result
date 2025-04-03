import asyncio
from typing import Any

import pytest

from safe_result import (
    Err,
    Ok,
    Result,
    err_type,
    ok,
    safe,
    safe_async,
    safe_async_with,
    safe_with,
    traceback_of,
)


def test_ok_creation_and_unwrap():
    result = Ok(42)
    assert result.value == 42
    assert result.unwrap() == 42
    assert not result.is_err()
    assert result.unwrap_or(0) == 42


def test_err_creation_and_unwrap():
    error = ValueError("test error")
    result = Err(error)
    assert result.error == error
    assert result.is_err()
    with pytest.raises(ValueError):
        result.unwrap()
    assert result.unwrap_or(42) == 42


def test_result_str_repr():
    ok_result = Ok(42)
    err_result = Err(ValueError("test error"))

    assert str(ok_result) == "Ok(42)"
    assert "Err" in str(err_result)
    assert "Ok(42)" == repr(ok_result)
    assert repr(err_result) == "Err(ValueError('test error'))"


def test_result_error_type_checking():
    result = Err(ValueError("test error"))
    assert err_type(result, ValueError)
    assert not err_type(result, TypeError)


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
    assert result2.is_err()
    assert err_type(result2, ZeroDivisionError)


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
    assert result2.is_err()
    assert err_type(result2, ZeroDivisionError)

    # Test catching ValueError
    @safe_with(ValueError)
    def convert_to_int(s: str) -> int:
        return int(s)

    result3 = convert_to_int("not a number")
    assert result3.is_err()
    assert err_type(result3, ValueError)

    # Test that other exceptions are not caught
    @safe_with(ValueError)
    def raise_type_error():
        raise TypeError("type error")

    with pytest.raises(TypeError):
        raise_type_error()


def test_result_traceback():
    # Test with Err
    try:
        raise ValueError("test error")
    except ValueError as e:
        err_result = Err(e)
        assert traceback_of(err_result) is not None
        assert "ValueError: test error" in traceback_of(err_result)

    # Test with Ok
    ok_result = Ok(42)
    assert traceback_of(ok_result) == ""


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
    assert result2.is_err()
    assert err_type(result2, ZeroDivisionError)

    # Test with asyncio.CancelledError
    @safe_async
    async def cancellable_operation() -> int:
        raise asyncio.CancelledError()
        return 42  # This line will never be reached

    # CancelledError should always be re-raised
    with pytest.raises(asyncio.CancelledError):
        await cancellable_operation()


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
    assert result2.is_err()
    assert err_type(result2, ZeroDivisionError)

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
    assert not result.is_err()
    assert result.unwrap_or(0) == 42

    # Error case with type annotation
    err_result: Result[str, ValueError] = Err(ValueError("error"))
    assert err_result.is_err()
    assert isinstance(err_result.error, ValueError)
    with pytest.raises(ValueError):
        err_result.unwrap()

    # Function return type annotations
    def func() -> Result[int, ValueError]:
        return Ok(42)

    assert func().value == 42

    def err_func() -> Result[str, TypeError]:
        return Err(TypeError("type error"))

    assert err_func().is_err()

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

    assert multi_error().is_err()

    # Type covariance
    class CustomError(ValueError):
        pass

    def covariant_func() -> Result[int, ValueError]:
        return Err(CustomError("custom error"))  # Should work due to covariance

    result = covariant_func()
    assert result.is_err()
    assert isinstance(result.error, CustomError)

    # Complex nested types
    complex_result: Result[dict[str, list[int]], Exception] = Ok({"nums": [1, 2, 3]})
    assert complex_result.unwrap()["nums"] == [1, 2, 3]

    # Optional types
    optional_result: Result[int | None, ValueError] = Ok(None)
    assert optional_result.unwrap() is None


def test_ok_properties():
    ok_result = Ok(42)
    assert ok_result.value == 42
    assert ok_result.error is None
    assert ok_result.is_ok() is True
    assert ok_result.is_err() is False


def test_ok_map():
    ok_result = Ok(42)
    mapped_result = ok_result.map(lambda x: x + 1)
    assert ok(mapped_result)
    assert mapped_result.unwrap() == 43


@pytest.mark.asyncio
async def test_ok_map_async():
    ok_result = Ok(42)

    async def async_add_one(x: int) -> int:
        await asyncio.sleep(0)  # Simulate async work
        return x + 1

    mapped_result = await ok_result.map_async(async_add_one)
    assert ok(mapped_result)
    assert mapped_result.unwrap() == 43


def test_ok_and_then():
    ok_result = Ok(42)

    def process(x: int) -> Result[str, ValueError]:
        if x > 0:
            return Ok(f"Positive: {x}")
        return Err(ValueError("Value must be positive"))

    result1 = ok_result.and_then(process)
    assert ok(result1)
    assert result1.unwrap() == "Positive: 42"

    ok_result_neg = Ok(-1)
    result2 = ok_result_neg.and_then(process)
    assert result2.is_err()
    assert err_type(result2, ValueError)


@pytest.mark.asyncio
async def test_ok_and_then_async():
    ok_result = Ok(42)

    async def async_process(x: int) -> Result[str, ValueError]:
        await asyncio.sleep(0)
        if x > 0:
            return Ok(f"Positive: {x}")
        return Err(ValueError("Value must be positive"))

    result1 = await ok_result.and_then_async(async_process)
    assert ok(result1)
    assert result1.unwrap() == "Positive: 42"

    ok_result_neg = Ok(-1)
    result2 = await ok_result_neg.and_then_async(async_process)
    assert result2.is_err()
    assert err_type(result2, ValueError)


def test_ok_flatten():
    result1 = Ok(Ok(42))
    assert result1.flatten() == Ok(42)

    result2 = Ok(Err(ValueError("inner")))
    assert result2.flatten() == Err(ValueError("inner"))

    result3 = Ok(Ok(Ok("deep")))
    assert result3.flatten() == Ok("deep")

    result4 = Ok(42)  # Non-nested Ok
    assert result4.flatten() == Ok(42)

    result5 = Ok(Ok(Err(ValueError("nested err"))))
    assert result5.flatten() == Err(ValueError("nested err"))


def test_ok_equality_and_hash():
    ok1 = Ok(42)
    ok2 = Ok(42)
    ok3 = Ok(99)
    err1 = Err(ValueError("error"))

    assert ok1 == ok2
    assert ok1 != ok3
    assert ok1 != err1
    assert ok1 != 42  # Different types
    assert hash(ok1) == hash(ok2)
    assert hash(ok1) != hash(ok3)


def test_err_properties():
    error = ValueError("test error")
    err_result = Err(error)
    assert err_result.error == error
    assert err_result.value is None
    assert err_result.is_ok() is False
    assert err_result.is_err() is True


def test_err_map():
    error = ValueError("test error")
    err_result = Err(error)
    mapped_result = err_result.map(lambda x: x + 1)  # type: ignore # Function should not be called
    assert err_result == mapped_result  # Should return self


@pytest.mark.asyncio
async def test_err_map_async():
    error = ValueError("test error")
    err_result = Err(error)

    async def async_add_one(x: int) -> int:
        await asyncio.sleep(0)
        pytest.fail("Async map function should not be called on Err")
        return x + 1

    mapped_result = await err_result.map_async(async_add_one)  # type: ignore # Function should not be called
    assert err_result == mapped_result  # Should return self


def test_err_and_then():
    error = ValueError("test error")
    err_result = Err(error)

    def process(x: int) -> Result[str, ValueError]:
        pytest.fail("and_then function should not be called on Err")
        return Ok(f"Processed: {x}")

    result = err_result.and_then(process)
    assert err_result == result  # Should return self


@pytest.mark.asyncio
async def test_err_and_then_async():
    error = ValueError("test error")
    err_result = Err(error)

    async def async_process(x: int) -> Result[str, ValueError]:
        await asyncio.sleep(0)
        pytest.fail("Async and_then function should not be called on Err")
        return Ok(f"Processed: {x}")

    result = await err_result.and_then_async(async_process)
    assert err_result == result  # Should return self


def test_err_flatten():
    result1 = Err(ValueError("outer"))
    assert result1.flatten() == Err(ValueError("outer"))

    # Flatten should not affect Err, even if nested within Ok conceptually
    # (though type system prevents Ok(Err(...)))
    # Let's test Err directly
    # result2 = Err(Err(ValueError("inner"))) # This shouldn't happen with current types but test logic
    # assert result2.flatten() == Err(Err(ValueError("inner")))


def test_err_equality_and_hash():
    err1 = Err(ValueError("error"))
    err2 = Err(ValueError("error"))
    err3 = Err(ValueError("different"))
    err4 = Err(TypeError("error"))
    ok1 = Ok(42)

    assert err1 == err2
    assert err1 != err3
    assert err1 != err4  # Different error types
    assert err1 != ok1
    assert err1 != ValueError("error")  # Different types
    assert hash(err1) == hash(err2)
    assert hash(err1) != hash(err3)
    assert hash(err1) != hash(err4)
