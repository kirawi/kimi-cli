List directory contents given a path to the directory.

**Tips:**
- ALWAYS use the `ReadDirectory` tool **instead** of calling the `Shell` tool for reading a directory
- The maximum number of items that can be shown at once is ${MAX_FILE_DESCRIPTORS}
- The system will notify you when there is any limitation hit when reading the directory
