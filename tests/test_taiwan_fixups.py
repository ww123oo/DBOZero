"""Tests for Taiwan Traditional preference fixups."""

from __future__ import annotations

from hanhua_v3.runtime.install_hanhua import (
    apply_traditional_fixups,
    apply_taiwan_fixups,
)
from hanhua_v3.runtime.taiwan_fixups import TAIWAN_SIMPLIFY_FIXUPS


def test_fixups_table_nonempty_and_has_core_pairs() -> None:
    assert len(TAIWAN_SIMPLIFY_FIXUPS) >= 50
    trads = {pair[0] for pair in TAIWAN_SIMPLIFY_FIXUPS}
    simps = {pair[1] for pair in TAIWAN_SIMPLIFY_FIXUPS}
    assert "登錄" in trads
    assert "帳號" in trads
    assert "伺服器" in trads
    assert "登录" in simps
    assert "账号" in simps or "帐号" in simps


def test_apply_traditional_fixups_login_account() -> None:
    out = apply_traditional_fixups("请登录账号连接服务器")
    assert "登錄" in out
    assert "帳號" in out
    assert "伺服器" in out
    assert "登录" not in out
    assert "账号" not in out
    assert "服务器" not in out


def test_apply_taiwan_fixups_maps_back_toward_simplified() -> None:
    out = apply_taiwan_fixups("請登錄帳號")
    assert "登录" in out
    assert "账号" in out or "帐号" in out
