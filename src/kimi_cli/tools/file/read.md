Reads and returns the content of a specified text file.

**Tips:**
- A `<system>` tag will be given before the read file content.
- Content will be returned with a line number before each line like `cat -n` format.
- If the file is large, the content will be truncated. The tool's response will clearly indicate if truncation has occurred and will provide details on how to read more of the file using the 'line_offset' and 'n_lines' parameters.
- This tool can only handle text files.
- The system will notify you when there is any limitation hit when reading the file.
- This tool is a tool that you typically want to use in parallel. Always read multiple files in one response when possible.
