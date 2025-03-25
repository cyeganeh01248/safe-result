# safe-result

A Python package for elegant error handling, inspired by Rust's Result type.

## Installation

```bash
uv pip install "git+https://github.com/overflowy/safe-result"
```

## Overview

`safe-result` provides type-safe objects that represents either success (`Ok`) or failure (`Err`). This allows for more explicit error handling without relying on try/catch blocks, making your code more predictable and easier to reason about.

Key features:

- Type-safe result handling with generics support
- Type guards when accessing result values
- Decorators for automatically wrapping function returns in `Result` objects
- Pattern matching support
- Built-in traceback capture for errors

## Usage

### Basic Usage

```python
from safe_result import Err, Ok, Result, ok


def divide(a: int, b: int) -> Result[float, ZeroDivisionError]:
    if b == 0:
        return Err(ZeroDivisionError("Cannot divide by zero"))  # Failure case
    return Ok(a / b)  # Success case


# Because of the improved function signature, we now know that the function can throw
foo = divide(10, 0)  # -> Result[float, ZeroDivisionError]

bar = 1 + foo.value  # Accessing the value directly will make the IDE unhappy
#             ^
#             Operator "+" not supported for types "Literal[1]" and "float | None"

if ok(foo):  # Use ok() to check if foo is successful
    bar = 1 + foo.value  # Now we can access the value
else:
    # Do something with foo.error
    pass
```

### Using the decorators

The `safe` decorator automatically wraps function returns in an `Ok` or `Err` object.

```python
from safe_result import Err, Ok, ok, safe


@safe
def divide(a: int, b: int) -> float:
    return a / b


# The function can throw an unspecified Exception, so the return type is Result[float, Exception]
foo = divide(10, 0)

if ok(foo):
    print(foo)
else:
    print(foo)  # -> Err(division by zero)
    print(type(foo.error))  # -> <class 'ZeroDivisionError'>

# We can also use pattern matching to handle the result:
match foo:
    case Ok(value):
        bar = 1 + value
    case Err(ZeroDivisionError):
        print("Division by zero")
    case Err(TypeError):
        print("Type error")
    case Err(ValueError):
        print("Value error")
    case _ as e:
        print(f"Unknown error: {e}")
```

The `safe_with` decorator lets you specify which exception types to catch, providing better type hints. Exceptions not handled by the decorator will be re-raised.

```python
from safe_result import ok, safe_with


@safe_with(ZeroDivisionError)
def divide(a: int, b: int) -> float:
    return a / b


foo = divide(10, 0)  # -> Result[float, ZeroDivisionError]

if not ok(foo):
    print(foo)  # -> Err(division by zero)
    print(type(foo.error))  # -> <class 'ZeroDivisionError'>


foo = divide(10, "2")  # ! Will raise a TypeError because it's not handled by the decorator
```

## License

MIT
