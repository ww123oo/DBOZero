"""Per-user local configuration for the dboc CLI.

Configuration lives in ``dboc.toml`` at the repository root (gitignored).
Only a tiny ``key = "value"`` subset is supported so the module stays
stdlib-only and works on Python 3.9+ (no tomllib dependency).

Game directory resolution order:

1. ``--game-dir`` CLI argument
2. ``DBOC_GAME_DIR`` environment variable
3. ``game_dir`` in ``dboc.toml``
4. Auto-detection of common install locations
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path


__all__ = [
    "CONFIG_PATH",
    "ConfigError",
    "ENV_GAME_DIR",
    "ROOT",
    "autodetect_game_dir",
    "load_config",
    "resolve_game_dir",
    "save_game_dir",
]

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "dboc.toml"
ENV_GAME_DIR = "DBOC_GAME_DIR"

_KEY_VALUE_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*("(?:[^"\\]|\\.)*")\s*(?:#.*)?$')

# Common install locations probed in order. The check is existence of
# pack/lang0.pak, so entries may point either at the game root or at the
# inner DBOZero directory.
_AUTODETECT_ROOTS = (
    "DBO Zero 2.0",
    "Games/DBO Zero 2.0",
    "Program Files/DBO Zero 2.0",
    "Program Files (x86)/DBO Zero 2.0",
)


class ConfigError(RuntimeError):
    pass


def load_config(path: Path = CONFIG_PATH) -> dict[str, str]:
    """Parse the small ``key = "value"`` subset used by dboc.toml."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("["):
                continue
            match = _KEY_VALUE_RE.match(line)
            if not match:
                raise ConfigError(f"{path.name}:{line_no}: 無法解析的設定行：{stripped}")
            try:
                values[match.group(1)] = json.loads(match.group(2))
            except json.JSONDecodeError as exc:
                raise ConfigError(f"{path.name}:{line_no}: 字串跳脫無效：{stripped}") from exc
    return values


def save_game_dir(game_dir: Path, path: Path = CONFIG_PATH) -> None:
    """Write game_dir into dboc.toml, preserving unrelated keys if present."""
    existing = load_config(path)
    existing["game_dir"] = str(game_dir.expanduser().resolve())
    lines = [
        "# dboc 本機設定（按使用者機器區分，已加入 .gitignore，請勿提交）",
        "# 遊戲目錄，指向 DBOZero 資源目錄或其上一級遊戲根目錄",
    ]
    for key, value in existing.items():
        lines.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _looks_like_game_dir(path: Path) -> bool:
    return (path / "pack" / "lang0.pak").is_file() or (path / "DBOZero" / "pack" / "lang0.pak").is_file()


def autodetect_game_dir() -> Path | None:
    """Probe common install locations; return the first match or None."""
    candidates: list[Path] = []
    if os.name == "nt":
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:/")
            if not drive.exists():
                continue
            for relative in _AUTODETECT_ROOTS:
                candidates.append(drive / relative)
    else:
        home = Path.home()
        for relative in _AUTODETECT_ROOTS:
            candidates.append(home / relative)
            candidates.append(home / "Games" / Path(relative).name)
    seen: set[str] = set()
    for candidate in candidates:
        try:
            key = str(candidate.resolve()).lower()
        except OSError:
            key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if _looks_like_game_dir(candidate):
            return candidate
    return None


def resolve_game_dir(cli_value: Path | None, *, config_path: Path = CONFIG_PATH) -> Path:
    """Resolve the game directory from CLI arg, env var, config, or autodetect."""
    if cli_value is not None:
        return cli_value
    env_value = os.environ.get(ENV_GAME_DIR, "").strip()
    if env_value:
        return Path(env_value)
    configured = load_config(config_path).get("game_dir", "").strip()
    if configured:
        return Path(configured)
    detected = autodetect_game_dir()
    if detected is not None:
        return detected
    raise ConfigError(
        "未找到遊戲目錄。請任選一種方式設定：\n"
        "  1. dboc config --game-dir \"<遊戲目錄>\"\n"
        f"  2. 在 {CONFIG_PATH.name} 中寫入 game_dir = \"<遊戲目錄>\"\n"
        f"  3. 設定環境變數 {ENV_GAME_DIR}\n"
        "  4. 在命令中加 --game-dir \"<遊戲目錄>\"\n"
        "遊戲目錄指向 DBOZero 資源目錄或其上一級（需包含 pack/lang0.pak）。"
    )
