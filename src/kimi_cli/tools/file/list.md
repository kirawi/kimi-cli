List directory contents given an absolute path to the directory.

**Tips:**
- ALWAYS use the `ListDirectory` tool instead of running the `ls` command with the Bash tool
- The `ListDirectory` tool only works on Unix
- It is the equivalent of `ls -la`
- The maximum number of items that can be shown at once is ${MAX_FILE_DESCRIPTORS}
- The system will notify you when there is any limitation hit when reading the directory
