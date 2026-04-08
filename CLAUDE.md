# Claude.md

## Overview

This document provides standard specifications and code examples for Claude-related development and usage. All code comments are written in English, and the document follows clean Markdown format without emojis or special symbols. Python is used as the primary programming language for demonstrations.

## Code Specification

- All code comments must be written in English
- Use Python as the preferred programming language
- No emojis, icons, or special symbolic characters in code or documentation
- Maintain consistent indentation and readable structure

## Python Code Example

```python
# This is a sample utility class demonstrating standard code format
class SampleUtility:
    # Initialize basic attributes
    def __init__(self):
        self.data = []

    # Add an element to the internal data list
    def add_element(self, element):
        if element not in self.data:
            self.data.append(element)
        return self.data

    # Remove a specific element from the list
    def remove_element(self, element):
        if element in self.data:
            self.data.remove(element)
        return self.data

    # Get the current list content
    def get_content(self):
        return self.data

# Create instance and test functions
if __name__ == "__main__":
    util = SampleUtility()
    util.add_element("Claude")
    util.add_element("Documentation")
    print(util.get_content())
    util.remove_element("Documentation")
    print(util.get_content())
```

## Usage Instructions

1. Ensure all code comments are in English
2. Follow Python syntax standards to avoid runtime errors
3. Keep the document structure clean and readable
4. Do not use decorative symbols, emojis, or non-text elements
5. Run scripts using Python 3.8 or higher for compatibility

## Huawei Cloud CLI (hcloud) Notes

When checking if hcloud CLI is installed, use `hcloud --help` instead of `hcloud --version`.
The hcloud CLI does not support the `--version` flag.

Correct verification command:
```bash
hcloud --help > /dev/null 2>&1 && echo "hcloud installed" || echo "hcloud not found"
```

## File Structure Suggestion

- Store code files in a dedicated `src` directory
- Place documentation files in the root directory as `.md` files
- Use consistent naming conventions for all files
- Maintain version control for code and documentation updates
