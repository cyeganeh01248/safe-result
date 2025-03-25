# safe-result

A Python package for elegant error handling, inspired by Rust's Result type.

## Installation

```bash
uv pip install "git+https://github.com/overflowy/safe-result"
```

## Overview

`safe-result` provides type-safe objects that represent either success (`Ok`) or failure (`Err`). This approach enables more explicit error handling without relying on try/catch blocks, making your code more predictable and easier to reason about.

Key features:

- Type-safe result handling with generics support
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

## License

MIT
