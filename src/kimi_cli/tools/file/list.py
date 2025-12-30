from kaos.path import KaosPath
from pathlib import Path
from typing import override

import os
import stat
from datetime import datetime

# Unix-specific imports
try:
    import pwd
    import grp
except ImportError:
    pwd = None
    grp = None

import aiofiles
from kosong.tooling import CallableTool2, ToolError, ToolOk, ToolReturnValue
from pydantic import BaseModel, Field

from kimi_cli.soul.agent import BuiltinSystemPromptArgs
from kimi_cli.tools.utils import load_desc, truncate_line
from kimi_cli.utils.path import is_within_directory

MAX_FD = 1000
IS_WINDOWS = os.name == 'nt'

class Params(BaseModel):
    path: str = Field(description="The path of the directory to list. For directories outside of the current working directory, you **must** use absolute paths.")
    n_lines: int = Field(
        description=(
            "Optional: The maximum number of file descriptors to list. "
            f"By default, it will show up to `{MAX_FD}` file descriptors."
        ),
        default=MAX_FD,
        ge=1,
    )

class ReadDirectory(CallableTool2[Params]):
    name: str = "ReadDirectory"
    description: str = load_desc(
        Path(__file__).parent / "list.md",
        {
            "MAX_FILE_DESCRIPTORS": str(MAX_FD)
        },
    )
    params: type[Params] = Params

    def __init__(self, builtin_args: BuiltinSystemPromptArgs) -> None:
        super().__init__()
        self._work_dir = builtin_args.KIMI_WORK_DIR

    @override
    async def __call__(self, params: Params) -> ToolReturnValue:
        try:
            p = Path(params.path)

            # Validate that the path is safe to read
            # Check for path traversal attempts
            try:
                resolved_path = p.resolve()
            except Exception:
                # If resolution fails (e.g. path too long), fall back to checking absolute directly
                resolved_path = p

            resolved_path = KaosPath.unsafe_from_local_path(resolved_path)

            if not is_within_directory(resolved_path, self._work_dir) and not p.is_absolute():
                # Outside directories can only be read with absolute paths
                return ToolError(
                    message=(
                        f"`{params.path}` points to a directory above the working directory but it is not an absolute path. "
                        "You must provide an absolute path to list a directory "
                        "above the current working directory."
                    ),
                    brief="Used a relative path to a directory outside CWD",
                )

            if not p.exists():
                return ToolError(
                    message=f"`{params.path}` does not exist.",
                    brief="Directory not found",
                )

            if not p.is_dir():
                return ToolError(
                    message=f"`{params.path}` is not a directory.",
                    brief="Invalid path",
                )

            assert params.n_lines >= 1
            try:
                entries = os.listdir(p)
            except PermissionError:
                return ToolError(
                    message=f"Encountered a permission error while trying to read `{params.path}`.",
                    brief="Permission denied",
                )

            output_entries = []
            max_fd_reached = False
            for entry in entries:
                if len(output_entries) >= MAX_FD:
                    max_fd_reached = True
                    break

                full_path = os.path.join(p, entry)
                entry_p = Path(full_path)

                try:
                    # On Windows, we might want lstat to avoid following symlinks for size/mode
                    # but keeping stat for consistency with original code logic unless it fails
                    stats = entry_p.stat()
                except:
                    continue

                mode = stats.st_mode
                size = stats.st_size
                mtime = datetime.fromtimestamp(stats.st_mtime)
                time_str = mtime.strftime('%b %d %H:%M')

                name = entry
                if entry_p.is_dir():
                    name += "/"
                elif entry_p.is_symlink():
                    try:
                        target = os.readlink(full_path)
                        name += " -> " + target
                    except OSError:
                        # Fallback if readlink fails
                        name += " -> ?"
                elif mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                    # On Windows, Python sets execution bits based on file extension (.exe, .bat, etc)
                    name += "*"

                if IS_WINDOWS:
                    # Windows Format: <DIR/TYPE> [Size] [Time] [Name]
                    # Mimics 'dir' content but 'ls' layout
                    type_str = ""
                    if entry_p.is_dir():
                        type_str = "<DIR>"
                    elif entry_p.is_symlink():
                        type_str = "<LNK>"

                    output_entries.append(
                        f"{type_str:<6} {size:>12} {time_str:<12} {name}\n"
                    )
                else:
                    # Unix Format: [Perms] [Links] [User] [Group] [Size] [Time] [Name]
                    perms = []
                    # User permissions
                    perms.append('r' if mode & stat.S_IRUSR else '-')
                    perms.append('w' if mode & stat.S_IWUSR else '-')
                    perms.append('x' if mode & stat.S_IXUSR else '-')
                    # Group permissions
                    perms.append('r' if mode & stat.S_IRGRP else '-')
                    perms.append('w' if mode & stat.S_IWGRP else '-')
                    perms.append('x' if mode & stat.S_IXGRP else '-')
                    # Other permissions
                    perms.append('r' if mode & stat.S_IROTH else '-')
                    perms.append('w' if mode & stat.S_IWOTH else '-')
                    perms.append('x' if mode & stat.S_IXOTH else '-')
                    perms_str = "".join(perms)

                    links = stats.st_nlink

                    try:
                        user = entry_p.owner()
                        group = entry_p.group()
                    except (KeyError, AttributeError, ImportError):
                        # Fallback for systems where owner/group fails or modules missing
                        user = stats.st_uid
                        group = stats.st_gid

                    output_entries.append(
                        f"{perms_str:<10} {links:>2} {str(user):<8} {str(group):<8} {size:>8} {time_str:<12} {name}\n"
                    )

            message = f"{len(output_entries)} file descriptors read from directory."

            if max_fd_reached:
                message += f" Max of {MAX_FD} file descriptors reached."

            return ToolOk(
                output="".join(output_entries),
                message=message,
            )

        except Exception as e:
            return ToolError(
                message=f"Failed to read the directory `{params.path}`. Error: {e}",
                brief="Failed to read directory",
            )
