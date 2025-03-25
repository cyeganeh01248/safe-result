# safe-result

A Python package for elegant error handling, inspired by Rust's Result type.

## Installation

```bash
uv pip install "git+https://github.com/overflowy/safe-result"
```

## Overview

`safe-result` provides type-safe objects that represent either success (`Ok`) or failure (`Err`). This approach enables more explicit error handling without relying on try/catch blocks, making your code more predictable and easier to reason about.

Key features:

- Type safe result handling with generics support
- Type guards to safely access result values
- Decorators to automatically wrap function returns in `Result` objects
- Pattern matching support for elegant error handling
- Built-in traceback capture for comprehensive error information

## Usage

### Basic Usage

```python
from safe_result import Err, Ok, Result, ok


def divide(a: int, b: int) -> Result[float, ZeroDivisionError]:
    if b == 0:
        return Err(ZeroDivisionError("Cannot divide by zero"))  # Failure case
    return Ok(a / b)  # Success case


# Function signature clearly communicates potential failure modes
foo = divide(10, 0)  # -> Result[float, ZeroDivisionError]

# Type checking will prevent unsafe access to the value
bar = 1 + foo.value
#         ^^^^^^^^^ Pylance/mypy indicates error:
# "Operator '+' not supported for types 'Literal[1]' and 'float | None'"

# Safe access pattern using the type guard function
if ok(foo):  # Verifies foo is an Ok result and enables type narrowing
    bar = 1 + foo.value  # Safe! - type system knows the value is a float here
else:
    # Handle error case with full type information about the error
    print(f"Error: {foo.error}")
```

### Using the Decorators

The `safe` decorator automatically wraps function returns in an `Ok` or `Err` object. Any exception is caught and wrapped in an `Err` result.

```python
from safe_result import Err, Ok, ok, safe


@safe
def divide(a: int, b: int) -> float:
    return a / b


# Return type is inferred as Result[float, Exception]
foo = divide(10, 0)

if ok(foo):
    print(f"Result: {foo.value}")
else:
    print(f"Error: {foo}")  # -> Err(division by zero)
    print(f"Error type: {type(foo.error)}")  # -> <class 'ZeroDivisionError'>

# Python's pattern matching provides elegant error handling
match foo:
    case Ok(value):
        bar = 1 + value
    case Err(ZeroDivisionError):
        print("Cannot divide by zero")
    case Err(TypeError):
        print("Type mismatch in operation")
    case Err(ValueError):
        print("Invalid value provided")
    case _ as e:
        print(f"Unexpected error: {e}")
```

The `safe_with` decorator provides more precise control by specifying which exception types to catch, improving type hints and safety.

```python
from safe_result import ok, safe_with


@safe_with(ZeroDivisionError)
def divide(a: int, b: int) -> float:
    return a / b


foo = divide(10, 0)  # -> Result[float, ZeroDivisionError]

if not ok(foo):
    print(f"Error: {foo}")  # -> Err(division by zero)
    print(f"Error type: {type(foo.error)}")  # -> <class 'ZeroDivisionError'>


# Other exceptions are not caught, maintaining expected behavior
# foo = divide(10, "2")  # Will raise a TypeError since it's not handled by the decorator
```

### Async Support

The `safe_async` and `safe_async_with` decorators provide the same functionality for async functions:

```python
from safe_result import ok, safe_async, safe_async_with
import asyncio


@safe_async
async def fetch_data(url: str) -> str:
    # Simulating an HTTP request that might fail
    if "invalid" in url:
        raise ValueError("Invalid URL")
    return f"Data from {url}"


async def main():
    # Result type is inferred as Result[str, Exception]
    result = await fetch_data("invalid-url.com")

    if ok(result):
        print(f"Received: {result.value}")
    else:
        print(f"Failed to fetch data: {result.error}")

    # With pattern matching
    match result:
        case Ok(value):
            print(f"Success: {value}")
        case Err(ValueError):
            print("Invalid URL provided")
        case Err():
            print(f"Unknown error: {result.error}")


@safe_async_with(ValueError, ConnectionError)
async def fetch_with_specific_errors(url: str) -> str:
    if "invalid" in url:
        raise ValueError("Invalid URL")
    if "timeout" in url:
        raise ConnectionError("Connection timed out")
    return f"Data from {url}"
```

### Unwrapping Results

The `unwrap` method allows you to extract the value from a `Result` or propagate the error automatically when used within `@safe` functions:

```python
from safe_result import Err, Ok, Result, ok, safe


@safe
def divide(a: int, b: int) -> float:
    return a / b


@safe
def calculate_ratio(x: int, y: int, z: int) -> float:
    # Unwrap the first result or propagate the error automatically
    division_result = divide(x, y)
    first_value = division_result.unwrap()

    # Do another operation that might fail
    return first_value / z  # If z is 0, this will be wrapped in Err


# Usage with error propagation
result = calculate_ratio(10, 5, 2)  # -> Ok(1.0)
if ok(result):
    print(f"Calculation successful: {result.value}")

result = calculate_ratio(10, 0, 2)  # -> Err(division by zero)
# The ZeroDivisionError from divide() is propagated through calculate_ratio()
if not ok(result):
    print(f"First division failed: {result.error}")

result = calculate_ratio(10, 5, 0)  # -> Err(division by zero)
# The ZeroDivisionError from the final division is captured
if not ok(result):
    print(f"Second division failed: {result.error}")


# For cases where you want a default value instead of propagating errors
@safe
def calculate_ratio_with_default(x: int, y: int, z: int) -> float:
    # Use unwrap_or to provide a default value instead of propagating errors
    division_result = divide(x, y)
    first_value = division_result.unwrap_or(0)

    # Even if the first division fails, we continue with the default value
    return first_value / z if z != 0 else 0
```

### Real-world example

Here's a practical example using `httpx` for HTTP requests with proper error handling:

```python
import asyncio
import httpx
from safe_result import safe_async_with, Ok, Err


@safe_async_with(httpx.TimeoutException, httpx.HTTPError)
async def fetch_api_data(url: str, timeout: float = 30.0) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=timeout)
        response.raise_for_status()  # Raises HTTPError for 4XX/5XX responses
        return response.json()


async def main():
    result = await fetch_api_data("https://httpbin.org/delay/10", timeout=2.0)
    match result:
        case Ok(data):
            print(f"Data received: {data}")
        case Err(httpx.TimeoutException):
            print("Request timed out - the server took too long to respond")
        case Err(httpx.HTTPStatusError as e):
            print(f"HTTP Error: {e.response.status_code}")
        case _ as e:
            print(f"Unknown error: {e.error}")
```

## License

MIT
