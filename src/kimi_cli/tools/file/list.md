List directory contents given an absolute path to the directory.

**Tips:**
- ALWAYS call the `ListDirectory` tool instead of executing `ls -la` with the `Shell` tool
- The `ListDirectory` tool only works on Unix
- The maximum number of items that can be shown at once is ${MAX_FILE_DESCRIPTORS}
- The system will notify you when there is any limitation hit when reading the directory
