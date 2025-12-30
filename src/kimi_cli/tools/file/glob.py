"""FindFiles tool implementation."""

from pathlib import Path
from typing import override

from kaos.path import KaosPath
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnValue
from pydantic import BaseModel, Field

from kimi_cli.soul.agent import BuiltinSystemPromptArgs
from kimi_cli.tools.utils import load_desc
from kimi_cli.utils.path import is_within_directory, list_directory

MAX_MATCHES = 1000


class Params(BaseModel):
    pattern: str = Field(description=("Efficiently finds files matching specific glob patterns (i.e. `src/**/*.ts`, `**.md`), returning paths sorted by modification time (newest first). Returns relative paths for files within the working directory, or absolute paths for files outside. Ideal for quickly locating files based on their name or path structure, especially in large codebases."))
    directory: str | None = Field(
        description=(
            "Optional: Absolute path to the directory to search in. Defaults to working directory."
        ),
        default=None,
    )
    include_dirs: bool = Field(
        description="Whether to include directories in results.",
        default=True,
    )


class Glob(CallableTool2[Params]):
    name: str = "FindFiles"
    description: str = load_desc(
        Path(__file__).parent / "glob.md",
        {
            "MAX_MATCHES": str(MAX_MATCHES),
        },
    )
    params: type[Params] = Params

    def __init__(self, builtin_args: BuiltinSystemPromptArgs) -> None:
        super().__init__()
        self._work_dir = builtin_args.KIMI_WORK_DIR

    async def _validate_directory(self, directory: KaosPath) -> ToolError | None:
        """Validate that the directory is safe to search."""
        resolved_dir = directory.canonical()

        # Ensure the directory is within work directory
        if not is_within_directory(resolved_dir, self._work_dir):
            return ToolError(
                message=(
                    f"`{directory}` is outside the working directory. "
                    "You can only search within the working directory."
                ),
                brief="Directory outside working directory",
            )
        return None

    @override
    async def __call__(self, params: Params) -> ToolReturnValue:
        try:
            dir_path = KaosPath(params.directory) if params.directory else self._work_dir

            if not dir_path.is_absolute():
                return ToolError(
                    message=(
                        f"`{dir_path}` is not an absolute path. "
                        "You must provide an absolute path to search."
                    ),
                    brief="Invalid directory",
                )

            # Validate directory safety
            dir_error = await self._validate_directory(dir_path)
            if dir_error:
                return dir_error

            if not await dir_path.exists():
                return ToolError(
                    message=f"`{dir_path}` does not exist.",
                    brief="Directory not found",
                )
            if not await dir_path.is_dir():
                return ToolError(
                    message=f"`{dir_path}` is not a directory.",
                    brief="Invalid directory",
                )

            # Perform the glob search - users can use ** directly in pattern
            matches: list[KaosPath] = []
            async for match in dir_path.glob(params.pattern):
                matches.append(match)

            # Filter out directories if not requested
            if not params.include_dirs:
                matches = [p for p in matches if await p.is_file()]

            # Sort by modification time (newest first)
            matches_with_mtime: list[tuple[KaosPath, float]] = []
            for p in matches:
                try:
                    stat_result = await p.stat()
                    matches_with_mtime.append((p, stat_result.st_mtime))
                except OSError:
                    # If stat fails, use epoch time (will sort to beginning)
                    matches_with_mtime.append((p, 0.0))
            matches_with_mtime.sort(key=lambda x: x[1], reverse=True)
            matches = [p for p, _ in matches_with_mtime]

            # Limit matches
            message = (
                f"Found {len(matches)} matches for pattern `{params.pattern}`."
                if len(matches) > 0
                else f"No matches found for pattern `{params.pattern}`."
            )
            if len(matches) > MAX_MATCHES:
                matches = matches[:MAX_MATCHES]
                message += (
                    f" Only the first {MAX_MATCHES} matches are returned. "
                    "You may want to use a more specific pattern."
                )

            # Return absolute paths if above CWD, relative if inside
            def path_to_output(p: KaosPath) -> str:
                """Return absolute path if above CWD, relative if inside."""
                try:
                    relative = p.relative_to(self._work_dir)
                    # Use relative path for files within work directory
                    return str(relative)
                except ValueError:
                    # Path is outside work directory, use absolute
                    return str(p)

            return ToolOk(
                output="\n".join(path_to_output(p) for p in matches),
                message=message,
            )

        except Exception as e:
            return ToolError(
                message=f"Failed to search for pattern {params.pattern}. Error: {e}",
                brief="FindFiles failed",
            )
