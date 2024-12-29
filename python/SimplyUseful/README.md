# Simply Useful

A Python module providing a collection of reusable utility functions, classes, and decorators to simplify development.

## Features

- Dependency Management
  - dependency_checker: Check for and install missing Python modules.

- Terminal Utilities
  - clear_term: Clears the terminal screen.

- Formatting Utilities
  - format_bytes: Converts bytes into a human-readable string.
  - format_uptime: Formats uptime in seconds into a readable string.
  - format_number: Formats large numbers into a readable string.

- Signal Handling
  - handle_interrupt: Handles interrupt signals and executes a specified action.

- Decorators
  - timeit: Logs the execution time of a function.
  - retry: Retries a function with exponential backoff.
  - cache_results: Caches the results of a function to avoid recomputation.
  - measure_memory: Measures the peak memory usage of a function.
  - async_retry: Retries an async function with exponential backoff.

## Installation

Simply clone the repository and import the module into your Python project.
```bash
git clone https://github.com/your-username/simply_useful.git
```
## Usage

### Importing the Module
```python
import simply_useful as SU
```
### Examples

#### Dependency Checker
```python
from simply_useful import dependency_checker

REQUIRED = ['boto3', 'botocore']
checker = dependency_checker(REQUIRED)
checker.check_dependencies()
status = checker.get_status()
print(f"Installed: {status['exist']}")
print(f"Missing: {status['missing']}")
```
#### Format Bytes
```python
from simply_useful import format_bytes

print(format_bytes(1024)) 
```
#### Retry Decorator
```python
from simply_useful import retry

@retry(max_retries=3, backoff=2.0)
def fetch_data():
    # Simulate a transient error
    if random.random() < 0.8:
        raise ValueError("Temporary failure")
    return "Success!"

print(fetch_data())
```
#### Async Retry
```python
from simply_useful import async_retry

@async_retry(max_retries=3, backoff=2.0)
async def async_fetch_data():
    # Simulate a transient error
    if random.random() < 0.8:
        raise ValueError("Temporary failure")
    return "Success!"

asyncio.run(async_fetch_data())
```
## Testing

The module includes a comprehensive suite of unit tests. To run the tests:

1. Install pytest and pytest-asyncio:
```bash
pip install pytest pytest-asyncio
```
2. Execute the tests:
```bash
pytest unit_tests/
```
## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements.

## License

This project is licensed under the MIT License.

