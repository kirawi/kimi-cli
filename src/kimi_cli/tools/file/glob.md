Find files and directories using glob patterns. This tool supports standard glob syntax like `*`, `?`, and `**` for recursive searches.

**When to use:**
- Prefer calling the `FindFiles` tool over running `find` or `fd` via the `Shell` tool
- Find files matching specific patterns (e.g., all Python files: `*.py`)
- Search for files recursively in subdirectories (e.g., `src/**/*.js`)
- Locate configuration files (e.g., `*.config.*`, `*.json`)
- Find test files (e.g., `test_*.py`, `*_test.go`)

**Example patterns:**
- `*.py` - All Python files in current directory
- `src/**/*.js` - All JavaScript files in src directory recursively
- `test_*.py` - Python test files starting with "test_"
- `*.config.{js,ts}` - Config files with .js or .ts extension

**Usage notes:**
- Be cautious with `**` at the start of patterns as it may yield many results in large projects
- The tool returns a maximum of {MAX_MATCHES} matches
- Avoid recursively searching in directories known to contain many files (e.g., `node_modules`, `venv`, `.venv`, `__pycache__`, `target`). If you need to search in a dependency, use more specific patterns like `node_modules/react/src/*` instead
