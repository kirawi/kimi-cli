from pathlib import Path
from typing import override

from kaos.path import KaosPath
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnValue
from pydantic import BaseModel, Field

from kimi_cli.soul.agent import Runtime
from kimi_cli.tools.file.utils import MEDIA_SNIFF_BYTES, detect_file_type
from kimi_cli.tools.utils import load_desc, truncate_line
from kimi_cli.utils.path import is_within_directory

MAX_LINES = 1000
MAX_LINE_LENGTH = 2000
MAX_BYTES = 100 << 10  # 100KB


class Params(BaseModel):
    path: str = Field(
        description=(
            "The path of the file to read. For files above the current working directory, you **must** use absolute paths."
        )
    )
    line_offset: int = Field(
        description=(
            "Optional: The 1-indexed line number to start reading from. "
            "By default, it is set to `1` to read from the beginning of the file. "
            "Set this value when the file is too large to read at once."
            "Use with `n_lines` for paginating through large files."
        ),
        default=1,
        ge=1,
    )
    n_lines: int = Field(
        description=(
            "Optional: The maximum number of lines to read. "
            f"By default, it will read up to a maximum of {MAX_LINES} lines. "
            "Set this value when the file is too large to read at once. "
            "Use with `line_offset` for paginating through large files."
        ),
        default=MAX_LINES,
        ge=1,
    )


class ReadFile(CallableTool2[Params]):
    name: str = "ReadFile"
    params: type[Params] = Params

    def __init__(self, runtime: Runtime) -> None:
        description = load_desc(
            Path(__file__).parent / "read.md",
            {
                "MAX_LINES": MAX_LINES,
                "MAX_LINE_LENGTH": MAX_LINE_LENGTH,
                "MAX_BYTES": MAX_BYTES,
            },
        )
        super().__init__(description=description)
        self._runtime = runtime
        self._work_dir = runtime.builtin_args.KIMI_WORK_DIR

    async def _validate_path(self, path: KaosPath) -> ToolError | None:
        """Validate that the path is safe to read."""
        resolved_path = path.canonical()

        if not is_within_directory(resolved_path, self._work_dir) and not path.is_absolute():
            # Outside files can only be read with absolute paths
            return ToolError(
                message=(
                    f"`{path}` points to a file above the working directory but it is not an absolute path. "
                    "You must provide an absolute path to read a file "
                    "above the current working directory."
                ),
                brief="Used a relative path to a file outside CWD",
            )
        return None

    @override
    async def __call__(self, params: Params) -> ToolReturnValue:
        # TODO: checks:
        # - check if the path may contain secrets

        if not params.path:
            return ToolError(
                message="File path cannot be empty.",
                brief="Empty file path",
            )

        try:
            p = KaosPath(params.path).expanduser()
            if err := await self._validate_path(p):
                return err
            p = p.canonical()

            if not await p.exists():
                return ToolError(
                    message=f"`{params.path}` does not exist.",
                    brief="File not found",
                )
            if not await p.is_file():
                return ToolError(
                    message=f"`{params.path}` is not a file.",
                    brief="Invalid path",
                )

            header = await p.read_bytes(MEDIA_SNIFF_BYTES)
            file_type = detect_file_type(str(p), header=header)
            if file_type.kind in ("image", "video"):
                return ToolError(
                    message=(
                        f"`{params.path}` is a {file_type.kind} file. "
                        "Use other appropriate tools to read image or video files."
                    ),
                    brief="Unsupported file type",
                )

            if file_type.kind == "unknown":
                return ToolError(
                    message=(
                        f"`{params.path}` may not be a readable text file. "
                        "You may need to read it with proper shell commands, Python tools "
                        "or MCP tools if available. "
                        "If you read/operate it with Python, you **MUST** ensure that any "
                        "third-party packages are installed in a virtual environment (venv)."
                    ),
                    brief="File not readable",
                )

            assert params.line_offset >= 1
            assert params.n_lines >= 1

            lines: list[str] = []
            n_bytes = 0
            max_lines_reached = False
            max_bytes_reached = False
            current_line_no = 0
            is_truncated = False
            async for line in p.read_lines(errors="replace"):
                current_line_no += 1
                if current_line_no < params.line_offset:
                    continue

                if len(lines) >= params.n_lines:
                    is_truncated = True
                    max_lines_reached = True
                    break
                elif n_bytes >= MAX_BYTES:
                    is_truncated = True
                    max_bytes_reached = True
                    break

                lines.append(line)
                n_bytes += len(line.encode("utf-8"))

            # Format output with line numbers like `cat -n`
            lines_with_no: list[str] = []
            for line_num, line in zip(
                range(params.line_offset, params.line_offset + len(lines)), lines, strict=True
            ):
                # Use 6-digit line number width, right-aligned, with tab separator
                lines_with_no.append(f"{line_num:6d}\t{line}")

            content_str = "".join(lines_with_no)
            if is_truncated and lines:
                start = params.line_offset
                end = params.line_offset + len(lines) - 1
                next_offset = end + 1

                header = (
                    "\nIMPORTANT: The file content is truncated.\n"
                    f"Status: Showing lines {start}-{end}.\n"
                    "Action: To read more of the file, paginate with the 'line_offset' and 'n_lines' "
                    "parameters in a subsequent 'ReadFile' call. "
                    f"For example, to read the next section of the file, use line_offset={next_offset}.\n\n"
                    "--- FILE CONTENT (truncated) ---\n"
                )
                output_str = header + content_str
            else:
                output_str = content_str

            message = (
                f"{len(lines)} lines read from file starting from line {params.line_offset}."
                if len(lines) > 0
                else "No lines read from file."
            )

            if max_lines_reached:
                message += f" Max {params.n_lines} lines reached."
            elif max_bytes_reached:
                message += f" Max {MAX_BYTES} bytes reached."
            elif not is_truncated:
                message += " End of file reached."

            return ToolOk(
                output=output_str,  # lines already contain \n, just join them
                message=message,
            )
        except Exception as e:
            return ToolError(
                message=f"Failed to read {params.path}. Error: {e}",
                brief="Failed to read file",
            )
