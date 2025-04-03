# safe-result

A Python package for elegant error handling, inspired by Rust's Result type.

## Installation

```bash
pip install safe-result
```

## Overview

`safe-result` provides type-safe objects that represent either success (`Ok`) or failure (`Err`). This approach enables more explicit error handling without relying on try/catch blocks, making your code more predictable and easier to reason about.

Key features:

- 100% test coverage
- Type-safe result handling with full generics support
- Pattern matching support for elegant error handling
- Type guards for safe access and type narrowing
- Decorators to automatically wrap function returns in `Result` objects
- Methods for transforming and chaining results (`map`, `map_async`, `and_then`, `and_then_async`, `flatten`)
- Methods for accessing values, providing defaults or propagating errors within a `@safe` context
- Handy traceback capture for comprehensive error information

## Usage

### Basic Usage

Create `Result` objects directly or use the provided decorators.

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
#         ^^^^^^^^^ Type checker indicates the error:
# "Operator '+' not supported for types 'Literal[1]' and 'float | None'"

# Safe access pattern using the type guard function
if ok(foo):  # Verifies foo is an Ok result and enables type narrowing
    bar = 1 + foo.value  # Safe! Type checker knows the value is a float here
else:
    # Handle error case with full type information about the error
    print(f"Error: {foo.error}")

# Pattern matching is also a great way to handle results
match foo:
    case Ok(value):
        print(f"Success: {value}")
    case Err(ZeroDivisionError() as e):
        print(f"Division Error: {e}")
```

### Using Decorators

Decorators simplify wrapping existing functions.

**`@safe`**: Catches _any_ `Exception` and returns `Result[ReturnType, Exception]`.

```python
from safe_result import ok, safe

@safe
def may_fail(data: str) -> int:
    return int(data)

def do_something():
    result1 = may_fail("123")  # -> Ok(123)
    result2 = may_fail("abc")  # -> Err(ValueError("invalid literal for int() with base 10: 'abc'"))

    if ok(result1):
        do_something_else(result1.value)
    else:
        print(f"Caught error: {result1.error}")
        return result1

    # Or even better by inverting the condition
    if not ok(result2):
        print(f"Caught error: {result2.error}")
        return result2

    # Continue with the rest of the function
    do_something_else(result2.value)
```

**`@safe_with(*ExceptionTypes)`**: Catches only the specified exception types, returning `Result[ReturnType, Union[ExceptionTypes]]`. Other exceptions are raised normally.

```python
from typing import Any
from safe_result import err_type, safe_with

@safe_with(ValueError, TypeError)
def process_input(data: Any) -> str:
    if not isinstance(data, str):
        raise TypeError("Input must be a string")
    if not data:
        raise ValueError("Input cannot be empty")
    return f"Processed: {data}"

res1 = process_input("hello")  # -> Ok('Processed: hello')
res2 = process_input("")       # -> Err(ValueError('Input cannot be empty'))
res3 = process_input(123)      # -> Err(TypeError('Input must be a string'))
res4 = process_input(None)     # -> Raises TypeError (caught by decorator)

# Use err_type for specific error handling
if err_type(res2, ValueError):
    print("ValueError occurred!")
```

### Async Support

`@safe_async` and `@safe_async_with` work identically for asynchronous functions. `asyncio.CancelledError` is never caught and always re-raised.

```python
import asyncio
from safe_result import Err, Ok, safe_async, safe_async_with

@safe_async
async def fetch_data(url: str) -> str:
    await asyncio.sleep(0.1)  # Simulate network
    if "invalid" in url:
        raise ValueError("Invalid URL")
    return f"Data from {url}"

@safe_async_with(ConnectionError)
async def fetch_specific(url: str) -> str:
    await asyncio.sleep(0.1)
    if "timeout" in url:
        raise ConnectionError("Timeout")
    return f"Data from {url}"

async def main():
    result1 = await fetch_data("valid-url")    # -> Ok('Data from valid-url')
    result2 = await fetch_data("invalid-url")  # -> Err(ValueError('Invalid URL'))
    result3 = await fetch_specific("ok")       # -> Ok('Data from ok')
    result4 = await fetch_specific("timeout")  # -> Err(ConnectionError('Timeout'))
    # result5 = await fetch_specific(123)      # -> Raises TypeError (not caught)

    # Handle the result
    match result1:
        case Ok(v):
            print(f"Fetched data: {v}")
        case Err(ValueError() as e):
            print(f"Invalid URL error: {e}")
        case Err(e):
            print(f"Some other error occurred with fetch_data: {e}")
```

### Working with Results

`Ok` and `Err` provide methods for transforming and accessing the contained values.

**`unwrap()`**: Returns the value if `Ok`, otherwise raises the contained error. Use cautiously, often within functions already decorated with `@safe` variants for automatic error propagation.

```python
from safe_result import Err, Ok, Result, safe

ok_res = Ok(42)
err_res = Err(ValueError("Bad data"))

print(ok_res.unwrap())  # -> 42
# err_res.unwrap()      # -> Raises ValueError: Bad data

@safe
def combined_op(res1: Result[int, Exception], res2: Result[int, Exception]) -> int:
    # unwrap() propagates errors automatically within @safe context
    val1 = res1.unwrap()
    val2 = res2.unwrap()
    return val1 + val2

print(combined_op(Ok(10), Ok(5)))                    # -> Ok(15)
print(combined_op(Ok(10), Err(ValueError("Fail"))))  # -> Err(ValueError('Fail'))
```

**`unwrap_or(default)`**: Returns the value if `Ok`, otherwise returns the `default` value.

```python
print(Ok(42).unwrap_or(0))        # -> 42
print(Err("Error").unwrap_or(0))  # -> 0
```

**`map(func)`**: Applies `func` to the value if `Ok`, returns a new `Ok` with the result. If `Err`, returns the original `Err` unchanged.

```python
print(Ok(5).map(lambda x: x * 2))        # -> Ok(10)
print(Err("Fail").map(lambda x: x * 2))  # -> Err('Fail')
```

**`map_async(async_func)`**: Applies `async_func` if `Ok`. Returns `await Ok(await async_func(value))`. If `Err`, returns the original `Err`.

```python
async def double_async(x):
    await asyncio.sleep(0)
    return x * 2

async def run_map_async():
    print(await Ok(5).map_async(double_async))        # -> Ok(10)
    print(await Err("Fail").map_async(double_async))  # -> Err('Fail')
```

**`and_then(func)`**: Calls `func` with the value if `Ok`. `func` _must_ return a `Result`. Useful for chaining operations that can fail. If `Err`, returns the original `Err`.

```python
def check_positive(n): return Ok(n) if n > 0 else Err("Not positive")

print(Ok(5).and_then(check_positive))        # -> Ok(5)
print(Ok(-1).and_then(check_positive))       # -> Err('Not positive')
print(Err("Fail").and_then(check_positive))  # -> Err('Fail')
```

**`and_then_async(async_func)`**: Calls `async_func` with the value if `Ok`. `async_func` _must_ return an `Awaitable[Result]`. If `Err`, returns the original `Err`.

```python
async def check_positive_async(n):
    await asyncio.sleep(0)
    return Ok(n) if n > 0 else Err("Not positive async")

async def run_and_then_async():
    print(await Ok(5).and_then_async(check_positive_async))        # -> Ok(5)
    print(await Ok(-1).and_then_async(check_positive_async))       # -> Err('Not positive async')
    print(await Err("Fail").and_then_async(check_positive_async))  # -> Err('Fail')
```

**`flatten()`**: Converts `Result[Result[T, E], E]` to `Result[T, E]`. Flattens nested `Ok(Ok(value))` to `Ok(value)` and `Ok(Err(error))` to `Err(error)`. Has no effect on non-nested `Result` or `Err`.

```python
print(Ok(Ok(42)).flatten())        # -> Ok(42)
print(Ok(Err("Inner")).flatten())  # -> Err('Inner')
print(Err("Outer").flatten())      # -> Err('Outer')
print(Ok(10).flatten())            # -> Ok(10)
```

### Helper Functions

**`err_type(result, ExceptionType)`**: Type guard that checks if a `Result` is an `Err` containing a specific exception type (or subtype).

```python
from safe_result import err_type

result = Err(ValueError("Invalid input"))

if err_type(result, ValueError):
    print("It's a ValueError!")  # -> True
if err_type(result, TypeError):
    print("It's a TypeError!")   # -> False (doesn't print)
if err_type(result, Exception):
    print("It's an Exception!")  # -> True
```

**`traceback_of(result)`**: Returns the formatted traceback string if the `Result` is an `Err` containing an `Exception`, otherwise returns an empty string.

```python
from safe_result import safe, traceback_of

@safe
def cause_error():
    return 1 / 0

error_result = cause_error()  # -> Err(ZeroDivisionError('division by zero'))

if not ok(error_result):
    tb = traceback_of(error_result)
    print(f"Error occurred:\n{tb}")
    # Prints the full traceback leading to the ZeroDivisionError
```

### Real-world example

Here's a practical example using `httpx` for HTTP requests with proper error handling:

```python
import asyncio
import httpx
from safe_result import safe_async_with, Ok, Err, err_type, traceback_of

# Only catch specific network/HTTP errors
@safe_async_with(httpx.TimeoutException, httpx.HTTPStatusError, ConnectionError)
async def fetch_api_data(url: str, timeout: float = 5.0) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=timeout)
        response.raise_for_status()  # Raises HTTPStatusError for 4XX/5XX responses
        return response.json()

async def main():
    # Example with timeout
    result_timeout = await fetch_api_data("https://httpbin.org/delay/10", timeout=2.0)
    match result_timeout:
        case Ok(data):
            print(f"Data received: {data}")
        case Err(httpx.TimeoutException):
            print("Request timed out - the server took too long to respond")
        case Err(httpx.HTTPStatusError as e):
            print(f"HTTP Error: {e.response.status_code} for URL: {e.request.url}")
        case Err(e):  # Catch other specified errors like ConnectionError
             print(f"Network error: {e}")
             print(traceback_of(result_timeout))  # Print traceback for unexpected errors

    # Example with success
    result_ok = await fetch_api_data("https://httpbin.org/json")
    if ok(result_ok):
        print(f"Successfully fetched JSON data: {result_ok.value.get('slideshow', {}).get('title')}")
```

## License

MIT
