#!/usr/bin/env python3
"""test_precheck_band_known_answers.py — precheck --target 帯別証跡（v17）の既知答えテスト＋番人。

E37 v17 acceptance（2026-07-07 承認）やること6＝判定器 precheck.py の変更に伴う既知答え（H13 の流儀）:
  T1: 帯別 be の計算が数学的既知答えと一致（SHORT・entry100/exit99・maker往復 fee=0.027860 → be=35.89）
  T2: 番人＝ドリフト≥20pt ∩ 低ボラ2帯が赤字（補填構造）→ 従来どおり FAIL・マーカーを書かない（弱体化していない証明）
  T3: ドリフト≥20pt ∩ 低ボラ2帯 be≥1.0 ∩ 採点候補の支配帯を含む → WARN-PASS（authorize・マーカー作成）
  T4: --target なし（従来経路）は本変更の影響を受けない（回帰なし）
使い方: python3 test_precheck_band_known_answers.py  （全 pass で exit 0）
"""
from __future__ import annotations
import os, subprocess, sys, tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import report                                      # noqa: E402
import precheck as pc                              # noqa: E402

STATE = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state")


def _rows(n, gross_sign, atr, t0="2021-01-01"):
    """SHORT・entry 100 固定・exit 99(勝ち)/101(負け)・TP_FILLED(maker)・size 1.0 の合成行。"""
    ts = pd.date_range(t0, periods=n, freq="5min")
    exit_px = 99.0 if gross_sign > 0 else 101.0
    return pd.DataFrame({
        "entry_time": ts, "exit_time": ts + pd.Timedelta(minutes=5), "side": "SHORT", "priority": 37,
        "regime": "range", "position_id": [f"S_{i}" for i in range(n)], "add_count": 1, "size_btc": 1.0,
        "entry_price": 100.0, "exit_price": exit_px, "exit_reason": "TP_FILLED", "hold_min": 5,
        "atr_14": atr, "adx_at_entry": 25.0, "stoch_k_at_entry": 50.0, "box_W_pct_at_entry": 1.0,
        "entry_hour": 0, "entry_weekday": 0, "mfe_usd": 1.0, "mae_usd": -0.5,
        "gross_usd": gross_sign * 1.0, "fee_usd": 0.03, "net_usd": gross_sign * 1.0 - 0.03,
    })


def _run_precheck(train_csv, target_csv, auth):
    cmd = [sys.executable, str(HERE / "precheck.py"), str(train_csv), "--authorize", auth]
    if target_csv is not None:
        cmd += ["--target", str(target_csv)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    ok = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # T1: 帯別 be の既知答え（直接呼び・数学的事実）: SHORT 100→99 勝ち・maker往復 fee=(100+99)*0.00014=0.027860
        #     be = 1.0 / 0.027860 = 35.894...（帯0=atr_pct 0.1%）
        d = report._judge_cols(_rows(60, +1, 0.1))
        d["atr_pct"] = d["atr_14"] / d["entry_price"] * 100
        tgt = _rows(50, +1, 0.1).drop(columns=[c for c in pc.PNL_COLS if c in _rows(1, 1, 0.1).columns])
        tgt["atr_pct"] = tgt["atr_14"] / tgt["entry_price"] * 100
        auth1, msg1 = pc._band_evidence(d, tgt)
        assert auth1, f"T1: 低ボラ全勝の証跡が authorize されない: {msg1}"
        assert "be 35.89" in msg1, f"T1: be 既知答え 35.89 と不一致: {msg1}"
        print("  T1 ✅ 帯別 be 既知答え（35.89・authorize）")
        ok += 1

        # 共通: ドリフト≥20pt を作る（train=低ボラ23%/高ボラ77%・target=低ボラ100% → 差 77pt）
        def _mk_train(low_sign):
            tr = pd.concat([_rows(60, low_sign, 0.1, "2021-01-01"), _rows(200, +1, 0.5, "2021-02-01")], ignore_index=True)
            p = td / f"trades_ban_train_{'w' if low_sign > 0 else 'l'}.csv"
            tr.to_csv(p, index=False)
            return p

        tgt_p = td / "trades_ban_target.csv"
        _rows(120, +1, 0.1, "2025-06-01").to_csv(tgt_p, index=False)

        # T2: 番人＝低ボラ赤字（補填構造）→ FAIL 維持・マーカーなし
        auth_name = "testban_v17_known.csv"
        marker = STATE / f"precheck_pass_{auth_name}"
        marker.unlink(missing_ok=True)
        rc, out = _run_precheck(_mk_train(-1), tgt_p, auth_name)
        assert rc != 0, "T2: 低ボラ赤字なのに precheck が通った（番人破れ＝弱体化）"
        assert not marker.exists(), "T2: FAIL なのにマーカーが書かれた"
        assert "帯別証跡なし" in out, f"T2: 証跡なしの表示がない\n{out[-800:]}"
        print("  T2 ✅ 番人＝低ボラ赤字は FAIL 維持（マーカーなし）")
        ok += 1

        # T3: 低ボラ be≥1.0 ∩ 支配帯を含む → WARN-PASS（authorize・マーカー作成）
        rc, out = _run_precheck(_mk_train(+1), tgt_p, auth_name)
        assert rc == 0, f"T3: 帯別証跡ありなのに FAIL\n{out[-800:]}"
        assert marker.exists(), "T3: authorize なのにマーカーが無い"
        assert "authorize" in out, f"T3: authorize 表示がない\n{out[-800:]}"
        marker.unlink(missing_ok=True)
        print("  T3 ✅ 帯別証跡あり＝WARN-PASS（authorize・マーカー作成）")
        ok += 1

        # T4: --target なし（従来経路）＝ドリフト検査なしで従来どおり（回帰なし）
        rc, out = _run_precheck(_mk_train(+1), None, auth_name)
        assert rc == 0, f"T4: 従来経路が壊れた\n{out[-800:]}"
        marker.unlink(missing_ok=True)
        print("  T4 ✅ --target なしの従来経路 回帰なし")
        ok += 1
    print(f"[test_precheck_band_known_answers] {ok}/4 pass")


if __name__ == "__main__":
    main()
