Searches for a regular expression pattern within the content of files in a specified directory (or current working directory). Can filter files by a glob pattern. Returns the lines containing matches, along with their file paths and line numbers.

**Tips:**
- Use the ripgrep pattern syntax, not grep syntax. E.g. you need to escape braces like `\\{` to search for `{`.
- Hidden files (dotfiles like `.gitlab-ci.yml`, `.eslintrc.json`) are always searched. To also search files excluded by `.gitignore` (e.g. `node_modules`, build outputs), set `include_ignored` to `true`. Sensitive files (such as `.env`) are still skipped for safety, even when `include_ignored` is `true`.
