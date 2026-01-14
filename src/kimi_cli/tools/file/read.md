Reads and returns the content of a specified text file.

**Tips:**
- A `<system>` tag will be given before the read file content.
- Content will be returned with a line number before each line like `cat -n` format.
- If the file is large, the content will be truncated. The tool's response will clearly indicate if truncation has occurred and will provide details on how to read more of the file using the 'line_offset' and 'n_lines' parameters.
- This tool can handle text files.
- The system will notify you when there is any limitation hit when reading the file.
- This tool is a tool that you typically want to use in parallel. Always read multiple files in one response when possible.
{% if "image_in" in capabilities and "video_in" in capabilities %}
- For image and video files:
  - Content will be returned in a form that you can view and understand. Feel confident to read image/video files with this tool.
  - The maximum size that can be read is ${MAX_MEDIA_BYTES} bytes. An error will be returned if the file is larger than this limit.
{% elif "image_in" in capabilities %}
- For image files:
  - Content will be returned in a form that you can view and understand. Feel confident to read image files with this tool.
  - The maximum size that can be read is ${MAX_MEDIA_BYTES} bytes. An error will be returned if the file is larger than this limit.
- Other media files (e.g., video, PDFs) are not supported by this tool. Use other proper tools to process them.
{% elif "video_in" in capabilities %}
- For video files:
  - Content will be returned in a form that you can view and understand. Feel confident to read video files with this tool.
  - The maximum size that can be read is ${MAX_MEDIA_BYTES} bytes. An error will be returned if the file is larger than this limit.
- Other media files (e.g., image, PDFs) are not supported by this tool. Use other proper tools to process them.
{% else %}
- Media files (e.g., image, video, PDFs) are not supported by this tool. Use other proper tools to process them.
{% endif %}
