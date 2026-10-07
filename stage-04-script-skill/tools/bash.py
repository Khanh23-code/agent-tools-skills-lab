"""Bash tool: chạy `bash -c` đồng bộ trong workspace, timeout ngắn, env tối thiểu.

Giới hạn: cwd và env tối thiểu KHÔNG phải sandbox. Lệnh bash vẫn có thể đọc/ghi ngoài workspace
với quyền của user đang chạy app. Chỉ dùng trong môi trường lab với dữ liệu giả.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

from langchain_core.tools import tool

import paths

DEFAULT_TIMEOUT_SECONDS = 10
MAX_OUTPUT_CHARS = 20_000
SYSTEM_PATH = "/usr/local/bin:/usr/bin:/bin"


def _find_bash() -> str:
    found = shutil.which("bash")
    if found:
        return found
    if sys.platform == "win32":
        for candidate in [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ]:
            if os.path.exists(candidate):
                return candidate
    return "bash"


def minimal_env(workspace: Path) -> dict[str, str]:
    """PATH trỏ venv của project trước, locale UTF-8. Không truyền API key hay biến môi trường khác."""
    venv_bin = str(Path(sys.executable).parent)
    locale = os.environ.get("LANG", "")
    if sys.platform == "win32":
        git_dirs = []
        for d in [r"C:\Program Files\Git\bin", r"C:\Program Files\Git\usr\bin", r"C:\Program Files\Git\cmd"]:
            if os.path.isdir(d):
                git_dirs.append(d)
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        sys_dirs = [system_root + r"\system32", system_root]
        path_val = ";".join([venv_bin] + git_dirs + sys_dirs)
    else:
        path_val = f"{venv_bin}:{SYSTEM_PATH}"

    return {
        "PATH": path_val,
        "HOME": str(workspace),
        "LANG": locale if "UTF-8" in locale.upper() else "C.UTF-8",
        "LC_ALL": locale if "UTF-8" in locale.upper() else "C.UTF-8",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _clip(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text, False
    return text[:MAX_OUTPUT_CHARS] + f"\n…[đã cắt, tổng {len(text)} ký tự]", True


def _run_bash(command: str, workspace: Path, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict:
    if not command.strip():
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": "", "timed_out": False,
                "error": {"code": "EMPTY_COMMAND", "message": "Command rỗng."}}
    bash_executable = _find_bash()
    try:
        process = subprocess.Popen(
            [bash_executable, "-c", command],  # không login shell, không đọc profile
            cwd=workspace,
            env=minimal_env(workspace),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=True if sys.platform != "win32" else False,
        )
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
            "error": {"code": "BASH_NOT_FOUND", "message": f"Không tìm thấy bash: {exc}"},
        }

    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
        stdout, out_clipped = _clip(stdout or "")
        stderr, err_clipped = _clip(stderr or "")
        return {
            "ok": False,
            "exit_code": None,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": True,
            "truncated": out_clipped or err_clipped,
            "error": {"code": "TIMEOUT", "message": f"Command chạy quá {timeout} giây, đã dừng. stdout/stderr là output một phần."},
        }
    stdout, out_clipped = _clip(stdout)
    stderr, err_clipped = _clip(stderr)
    return {
        "ok": True,
        "exit_code": process.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "timed_out": False,
        "truncated": out_clipped or err_clipped,
    }


@tool
def bash(command: str) -> str:
    """Chạy một lệnh bash ngắn (bash -c) trong thư mục workspace và trả về JSON.

    cwd là workspace, nên dùng đường dẫn tương đối như data/tasks.csv. `python` là Python của project.
    Timeout 10 giây; không chạy tiến trình nền hay lệnh tương tác.
    Kết quả: {"ok": true, "exit_code": 0, "stdout": "...", "stderr": "", "timed_out": false}.
    ok=true nghĩa là lệnh đã chạy xong và có kết quả; exit_code khác 0 nghĩa là chương trình báo lỗi.
    Timeout: {"ok": false, "exit_code": null, "timed_out": true, ...} kèm output một phần nếu có.
    """
    return json.dumps(_run_bash(paths.WORKSPACE_DIR, command) if False else _run_bash(command, paths.WORKSPACE_DIR), ensure_ascii=False)
