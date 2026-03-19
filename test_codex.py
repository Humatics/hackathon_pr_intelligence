def greet(name: str):
    # This is a test function for Codex PR Review
    print(f"Hello, {name}!")

def add_numbers(a, b):
    # Intentional lack of type hints to see if Codex catches it
    return a + b

def subtract(a, b):
    # intentional typo
    retrun a - b
