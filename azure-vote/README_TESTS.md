# Test Suite for Azure Vote Application

This directory contains comprehensive test cases for the Azure Voting Application (`main.py`) using the pytest framework.

## Running the Tests

### Prerequisites
Make sure you have the required dependencies installed:
```bash
pip install pytest flask redis pytest-mock
```

### Running All Tests
```bash
cd azure-vote
python -m pytest test_main.py -v
```

### Running Specific Test Classes
```bash
# Test environment variable configuration
python -m pytest test_main.py::TestEnvironmentVariables -v

# Test Redis connection setup
python -m pytest test_main.py::TestRedisConnectionSetup -v

# Test Flask routes
python -m pytest test_main.py::TestFlaskRouteHandling -v
```

## Test Coverage

The test suite covers the following areas:

1. **Environment Variable Configuration** (`TestEnvironmentVariables`)
   - Tests that environment variables override config file values
   
2. **Redis Connection Setup** (`TestRedisConnectionSetup`)
   - Tests Redis connection without password
   - Tests Redis connection with password authentication

3. **Redis Initialization** (`TestRedisInitialization`)
   - Tests that vote counters are initialized to zero when they don't exist

4. **Flask Route Handling** (`TestFlaskRouteHandling`)
   - Tests GET route returns correct vote counts
   - Tests POST route increments vote counters
   - Tests POST route with reset functionality

5. **Error Handling** (`TestErrorHandling`)
   - Tests that Redis connection failures cause graceful application exit

6. **ShowHost Configuration** (`TestShowHostConfiguration`)
   - Tests SHOWHOST configuration that changes title to hostname

7. **Configuration Logic** (`TestConfigurationLogic`)
   - Tests environment variable precedence over configuration file

## Test Design

- All tests use mocking to avoid dependencies on external services (Redis, file system)
- Tests are isolated and can run independently
- Each test resets the module state to ensure clean testing environment
- Tests cover both positive and negative scenarios