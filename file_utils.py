"""Safe file writing shared by plan storage and user preferences."""

import json
import os
import shutil
import tempfile
from pathlib import Path


def backup_path(filepath):
    """Where the previous version of a file is kept: <name>.bak next to it."""
    filepath = Path(filepath)
    return filepath.with_name(filepath.name + '.bak')


def _is_valid_json(filepath):
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True
    except (OSError, ValueError):
        return False


def _new_file_mode():
    umask = os.umask(0)
    os.umask(umask)
    return 0o666 & ~umask


def write_atomically(filepath, text, backup=False):
    """
    Replace filepath with text without ever leaving a half-written file.

    The text goes to a temporary file in the same directory, is flushed to
    disk, and then renamed over the target in one step (os.replace). If
    anything fails, the old file is untouched and the temporary file removed.

    With backup=True, the previous version is copied to <name>.bak first,
    unless it isn't valid JSON (so a good backup is never replaced by a
    corrupt file).
    """
    filepath = Path(filepath)
    exists = filepath.exists()
    mode = (filepath.stat().st_mode & 0o777) if exists else _new_file_mode()

    fd, tmp_name = tempfile.mkstemp(dir=filepath.parent, prefix=f".{filepath.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_name, mode)
        if backup and exists and _is_valid_json(filepath):
            shutil.copy2(filepath, backup_path(filepath))
        os.replace(tmp_name, filepath)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
