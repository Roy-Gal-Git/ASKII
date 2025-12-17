# Example Queries and Answers

This document provides example questions and expected answer formats for the CLI Repo Analyst Tool.

## Example 1: Understanding a Function

**Question:**
```
How does the calculate_average function work?
```

**Expected Answer Format:**
```
The `calculate_average` function in `calculator.py:85-95` calculates the average
of a list of numbers by summing all values and dividing by the count. If the list
is empty, it returns 0.0.

The function signature is:
```python
def calculate_average(numbers: list[float]) -> float:
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)
```

[calculator.py:85-95]
```

## Example 2: Class Overview

**Question:**
```
What does the Calculator class do?
```

**Expected Answer Format:**
```
The Calculator class in `calculator.py:37-75` provides basic arithmetic operations.
It includes:

- An `__init__` method that initializes an empty history list
- An `add` method that adds two numbers and records the operation in history
- A `subtract` method that subtracts two numbers and records the operation
- A `multiply` method that multiplies two numbers

The class maintains a history of operations for tracking purposes.

[calculator.py:37-75]
```

## Example 3: Configuration Questions

**Question:**
```
What are the default configuration settings?
```

**Expected Answer Format:**
```
The default configuration settings are defined in `config.py:5-8`:

- DEFAULT_TIMEOUT: 30 seconds
- MAX_RETRIES: 3 attempts
- DEBUG_MODE: False

These settings are used throughout the application for timeout handling and
retry logic.

[config.py:5-8]
```

## Example 4: No Relevant Results

**Question:**
```
How does quantum computing work?
```

**Expected Answer Format:**
```
I couldn't find relevant code in the repository to answer this question.

I searched through calculator.py, config.py, README.md, but the code snippets
found were not sufficiently relevant to provide a reliable answer.

Try rephrasing your question or asking about a different aspect of the codebase.
```

## Example 5: Partial Evidence

**Question:**
```
How does the code handle errors?
```

**Expected Answer Format (if evidence is weak):**
```
Based on the available code, it appears that error handling is implemented in
the Calculator class. The `add` method includes validation, but the full error
handling strategy is not clear from the retrieved code snippets.

What is clear:
- The `add` method validates input [calculator.py:45-67]

What is NOT clear:
- Overall error handling strategy
- Error recovery mechanisms
- Error logging

[calculator.py:45-67]
```

## Example 6: Multiple Files

**Question:**
```
How is the timeout configured?
```

**Expected Answer Format:**
```
Timeout configuration is handled in multiple places:

1. Default timeout is set in `config.py:5-6`:
   ```python
   DEFAULT_TIMEOUT = 30
   ```

2. The Calculator class uses this in its initialization [calculator.py:10-15]

[config.py:5-6, calculator.py:10-15]
```

## Citation Format

All answers include inline citations in the format:
```
[file_path:line_range]
```

For example:
- `[calculator.py:45-67]` - Lines 45 to 67 in calculator.py
- `[src/client.py:10-25]` - Lines 10 to 25 in src/client.py
- `[README.md:1-10]` - Lines 1 to 10 in README.md

**Citation Guidelines:**
- Use square brackets `[]` for better visual distinction from regular text
- Include one citation per sentence when possible for clarity
- When multiple files support a claim, group them: `[file1.py:10-20, file2.py:5-15]`
- Place citations immediately after the statement they support

## Answer Quality Indicators

### Strong Evidence
- Multiple relevant chunks found
- High similarity scores (>= 0.7)
- Clear, confident answers

### Weak Evidence
- Few relevant chunks
- Moderate similarity scores (0.5-0.7)
- Hedged answers with explicit uncertainties

### No Evidence
- Low similarity scores (< 0.5)
- No relevant chunks
- Clear message that relevant code wasn't found
