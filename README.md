# safe-result

A Python library providing a Result type for elegant error handling, inspired by Rust's Result type.

## Installation

```bash
uv pip install "git+https://github.com/overflowy/safe-result"
```

## Overview

`safe-result` provides a `Result` type that represents either success (`value`) or failure (`error`). This allows for more explicit error handling without relying on exceptions, making your code more predictable and easier to reason about.

Key features:

- Type-safe result handling with generics support
- Decorators for automatically wrapping function returns in Result objects
- Support for both synchronous and asynchronous functions
- Built-in traceback capture for errors

## Advantages Over Traditional Try/Catch

Using `safe_result` offers several benefits over traditional try/catch exception handling:

1. **Explicitness**: Forces error handling to be explicit rather than implicit, preventing overlooked exceptions
2. **Function Composition**: Makes it easier to compose functions that might fail without nested try/except blocks
3. **Predictable Control Flow**: Code execution becomes more predictable without exception-based control flow jumps
4. **Error Propagation**: Simplifies error propagation through call stacks without complex exception handling chains
5. **Traceback Preservation**: Automatically captures and preserves tracebacks while allowing normal control flow
6. **Separation of Concerns**: Cleanly separates error handling logic from business logic
7. **Testing**: Makes testing error conditions more straightforward since errors are just values

## Comparative Examples

### Explicitness

Traditional approach:

```python
def process_data(data):
    # This might raise various exceptions, but it's not obvious from the signature
    processed = data.process()
    return processed

# Caller might forget to handle exceptions
result = process_data(data)  # Could raise exceptions!
```

With `safe_result`:

```python
@Result.safe
def process_data(data):
    processed = data.process()
    return processed

# Type signature makes it clear this returns a Result that might contain an error
result = process_data(data)
if not result.is_error():
    # Safe to use the value
    use_result(result.value)
else:
    # Handle the error case explicitly
    handle_error(result.error)
```

### Function Composition

Traditional approach:

```python
def get_user(user_id):
    try:
        return database.fetch_user(user_id)
    except DatabaseError as e:
        raise UserNotFoundError(f"Failed to fetch user: {e}")

def get_user_settings(user_id):
    try:
        user = get_user(user_id)
        return database.fetch_settings(user)
    except (UserNotFoundError, DatabaseError) as e:
        raise SettingsNotFoundError(f"Failed to fetch settings: {e}")

# Nested error handling becomes complex and error-prone
try:
    settings = get_user_settings(user_id)
    # Use settings
except SettingsNotFoundError as e:
    # Handle error
```

With `safe_result`:

```python
@Result.safe
def get_user(user_id):
    return database.fetch_user(user_id)

@Result.safe
def get_user_settings(user_id):
    user_result = get_user(user_id)
    if user_result.is_error():
        return user_result  # Simply pass through the error

    return database.fetch_settings(user_result.value)

# Clear composition
settings_result = get_user_settings(user_id)
if not settings_result.is_error():
    # Use settings
    process_settings(settings_result.value)
else:
    # Handle error once at the end
    handle_error(settings_result.error)
```

### Error Propagation

Traditional approach:

```python
def api_call():
    try:
        # Multiple things that could fail
        conn = create_connection()
        auth = authenticate()
        result = make_request(conn, auth)
        return process_result(result)
    except ConnectionError:
        # Log and handle connection error
        logging.error("Connection failed")
        raise APIError("Connection failed")
    except AuthError:
        # Log and handle auth error
        logging.error("Authentication failed")
        raise APIError("Authentication failed")
    except RequestError:
        # Log and handle request error
        logging.error("Request failed")
        raise APIError("Request failed")
```

With `safe_result`:

```python
@Result.safe
def api_call():
    conn_result = create_connection()
    if conn_result.is_error():
        return conn_result  # Original error and traceback preserved

    auth_result = authenticate()
    if auth_result.is_error():
        return auth_result  # Original error and traceback preserved

    request_result = make_request(conn_result.value, auth_result.value)
    if request_result.is_error():
        return request_result  # Original error and traceback preserved

    return process_result(request_result.value)

# Usage
result = api_call()
if result.is_error():
    # Original error with full context is available
    logging.error(f"API call failed: {result.error}")
    logging.debug(f"Traceback: {result.traceback}")
```

### Testing

Traditional approach:

```python
# Hard to test exception paths
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

    # Testing the error message or doing anything with the error is cumbersome
    try:
        divide(10, 0)
    except ZeroDivisionError as e:
        assert str(e) == "division by zero"
```

With `safe_result`:

```python
# Much cleaner testing of error conditions
def test_division_by_zero():
    result = divide(10, 0)
    assert result.is_error()
    assert isinstance(result.error, ZeroDivisionError)
    assert str(result.error) == "division by zero"

    # Can also test the happy path in a clean way
    result = divide(10, 2)
    assert not result.is_error()
    assert result.value == 5.0
```

## Usage

### Basic Usage

```python
from safe_result import Result

# Success case
success = Result(value=42)
if not success.is_error():
    print(success.value)  # 42

# Error case
error = Result(error=ValueError("something went wrong"))
if error.is_error():
    print(f"Error occurred: {error.error}")
```

### Using the Decorator

The `@Result.safe` decorator wraps function returns in a Result object:

```python
from safe_result import Result

@Result.safe
def divide(a: int, b: int) -> float:
    return a / b

# Success case
result = divide(10, 2)
if not result.is_error():
    print(result.value)  # 5.0

# Error case
result = divide(10, 0)
if result.is_error():
    print(f"Error: {result.error}")  # Error: division by zero
```

### Using the Typed Error Decorator

The `@Result.safe_with` decorator lets you specify which exception types to catch, providing better type hints:

```python
from safe_result import Result

@Result.safe_with(ZeroDivisionError, ValueError)
def divide(a: int, b: int) -> float:
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise ValueError("Inputs must be numbers")
    return a / b

# Success case
result = divide(10, 2)
if not result.is_error():
    print(result.value)  # 5.0

# Error case - ZeroDivisionError is caught and wrapped
result = divide(10, 0)
if result.is_error():
    # Type checker knows this is either ZeroDivisionError or ValueError
    print(f"Error: {result.error}")  # Error: Cannot divide by zero

# Error case - ValueError is caught and wrapped
try:
    result = divide("10", 2)  # Will raise TypeError
except TypeError:
    # TypeError is not caught by safe_with, so it's raised normally
    print("TypeError was raised as expected")

# You can check for specific error types
result = divide(10, 0)
if result.is_error_of_type(ZeroDivisionError):
    # Type checker knows error is a ZeroDivisionError inside this block
    print(f"Division error: {result.error}")
```

### Async Functions

The `@Result.safe_async` decorator wraps async functions in a Result object:

```python
import asyncio
from safe_result import Result

@Result.safe_async
async def async_operation(value: int) -> int:
    await asyncio.sleep(0.1)
    if value == 0:
        raise ValueError("Cannot process zero")
    return value * 2

async def main():
    # Success case
    result = await async_operation(5)
    print(result.unwrap())  # 10

    # Error case
    result = await async_operation(0)
    print(result.unwrap_or(42))  # 42

asyncio.run(main())
```

### Async Functions with Typed Errors

The `@Result.safe_async_with` decorator wraps async functions and catches only specified errors:

```python
import asyncio
from safe_result import Result

@Result.safe_async_with(ValueError, ConnectionError)
async def fetch_data(url: str) -> dict:
    await asyncio.sleep(0.1)
    if not url:
        raise ValueError("URL cannot be empty")
    if url == "invalid":
        raise ConnectionError("Could not connect to server")
    if url == "timeout":
        raise TimeoutError("Connection timed out")  # Not caught by the decorator
    return {"data": "success"}

async def main():
    # Success case
    result = await fetch_data("https://example.com")
    if not result.is_error():
        print(result.value)  # {"data": "success"}

    # Error case - ValueError is caught
    result = await fetch_data("")
    if result.is_error_of_type(ValueError):
        print(f"Validation error: {result.error}")  # Validation error: URL cannot be empty

    # Error case - ConnectionError is caught
    result = await fetch_data("invalid")
    if result.is_error_of_type(ConnectionError):
        print(f"Connection failed: {result.error}")  # Connection failed: Could not connect to server

    try:
        # Error case - TimeoutError is NOT caught and will be raised normally
        result = await fetch_data("timeout")
    except TimeoutError as e:
        print(f"Timeout error was raised normally: {e}")

asyncio.run(main())
```

### Unwrapping Results

```python
from safe_result import Result

# Get value or raise the stored exception
result = Result(value="hello")
value = result.unwrap()  # "hello"

# Get value or return a default
error_result = Result(error=ValueError("oops"))
value = error_result.unwrap_or("default")  # "default"
```

## License

MIT
