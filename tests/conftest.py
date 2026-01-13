"""Pytest configuration and fixtures."""

import pytest
import os


@pytest.fixture(scope="session")
def api_key():
    """Get API key from environment."""
    return os.getenv("ANTHROPIC_API_KEY")


@pytest.fixture
def example_python_code():
    """Provide example Python code for testing."""
    return """
class Calculator:
    '''A simple calculator class.'''

    def __init__(self):
        self.result = 0

    def add(self, a: int, b: int) -> int:
        '''Add two numbers.'''
        self.result = a + b
        return self.result

    def multiply(self, a: int, b: int) -> int:
        '''Multiply two numbers.'''
        self.result = a * b
        return self.result


def main():
    '''Main entry point.'''
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.multiply(4, 7))


if __name__ == "__main__":
    main()
"""
