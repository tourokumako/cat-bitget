"""
ratchet_guards.py — ① 普遍的に常にダメ（正しさ・正直さ）を機械で自動中断する番人。

設計根拠: まこさん確定の ①/② 区別（2026-06-08）
  ① 普遍的に常にダメ（leak / cap超 / コスト控除漏れ / 勘の数値 / 虚偽完了 / 異常値 / 移植不一致）
     → どのルートでも絶対ダメ＝凍結しても良いルートを塞がない。本ファイルで raise（自動中断）。
  ② ルート依存（○× / magnitude / θ / サイジング順序 / ボラの役割）
     → 凍結しない。明示フォーム＋まこさん承認で扱う。ボラは report_vol_importance で「見える化」のみ（raise しない）。

使い方: train スクリプトが各工程でこれらを呼ぶ。違反は RatchetGuardError で止まる＝偽の成功数字が出ない。
既知答えテスト: 本ファイルを直接実行（python3 ratchet_guards.py）すると全番人の既知答えテストが走る。
"""
from __future__ import annotations
import os
import re


class RatchetGuardError(Exception):
    """① 番人が違反を検出したときに投げる。これが出たら学習/採点は成功数字を出せない。"""
    pass


# ① leak（未来参照）— 特徴量計算コードの静的検査
#   ⚠ 散文/コメント/docstring の「説明文字」に誤反応しないよう、実コードのパターンのみ厳密一致:
#     ・.shift(-数字)        … 負方向シフト（散文の shift(-N) は N=文字なので不一致）
#     ・( または , の直後の center=True … 呼び出しの kwarg（散文の ・center=True は不一致）
#   ＋行内コメント(# 以降)は除去してから判定。
def assert_no_future_ref(source: str) -> bool:
    bad = []
    for line in source.splitlines():
        code = line.split("#", 1)[0]                       # 行内コメント除去
        if re.search(r"\.shift\(\s*-\s*\d", code):         # .shift(-1) 等（数字必須＝実コード）
            bad.append(f".shift(-N): {line.strip()[:50]}")
        if re.search(r"[(,]\s*center\s*=\s*True", code):   # rolling(..., center=True) 等（kwarg）
            bad.append(f"center=True: {line.strip()[:50]}")
    if bad:
        raise RatchetGuardError(f"leak(類型A): 特徴量に未来参照 {bad}")
    return True


# ① leak（期間分割）— 学習末 < 採点始
def assert_period_split(train_end, score_start) -> bool:
    if not (train_end < score_start):
        raise RatchetGuardError(f"期間侵入(類型B/H8): 学習末 {train_end} >= 採点始 {score_start}")
    return True


# ① cap — 任意の時点で同時保有合計 <= 0.12 BTC
def assert_cap(positions, cap: float = 0.12) -> float:
    """positions = [(entry_ts, exit_ts, size_btc), ...]。最大同時保有合計を返す。超過は raise。"""
    events = []
    for e, x, s in positions:
        events.append((e, +float(s)))
        events.append((x, -float(s)))
    events.sort(key=lambda z: (z[0], z[1]))  # 同時刻は決済(-)を先に
    cur = 0.0
    mx = 0.0
    for _, d in events:
        cur += d
        mx = max(mx, cur)
    if mx > cap + 1e-9:
        raise RatchetGuardError(f"cap違反(類型H): 同時保有合計 max {mx:.4f} > {cap} BTC")
    return mx


# ① コスト — net はコスト控除後（net < gross）。net>=gross は手数料未控除疑い
def assert_cost_applied(total_gross: float, total_net: float) -> bool:
    if total_net >= total_gross:
        raise RatchetGuardError(f"コスト控除漏れ(類型E): net {total_net} >= gross {total_gross}（手数料未控除疑い）")
    return True


# ① 勘の数値 — コード中の定数に出典(# src:)が無ければ止める
def assert_constants_sourced(source: str) -> bool:
    violations = []
    for line in source.splitlines():
        m = re.match(r"\s*([A-Z][A-Z0-9_]*)\s*=\s*-?\d", line)  # 大文字定数 = 数値
        if m and ("# src:" not in line and "#src:" not in line):
            violations.append(m.group(1))
    if violations:
        raise RatchetGuardError(f"勘の数値(feedback定量比較): 出典(# src:)なし定数 {violations}")
    return True


# ① 虚偽完了 — 「採点済」と言うには出力ファイルが実在すること
def assert_output_exists(path: str) -> bool:
    if not os.path.exists(path):
        raise RatchetGuardError(f"虚偽完了(類型G): 出力 {path} が無いのに完了主張は不可")
    return True


# ① 異常値 — 出来すぎを「合格」と誤認しない（要調査で止める）
def assert_no_anomaly(win_rate: float, monthly_net: float, max_dd: float | None) -> bool:
    flags = []
    if win_rate > 0.70:
        flags.append(f"勝率 {win_rate:.2f} > 0.70")
    if monthly_net > 3800:
        flags.append(f"月NET {monthly_net} > 3800")
    if max_dd is not None and monthly_net > 0 and max_dd < 0.10 * monthly_net:
        flags.append(f"最大DD {max_dd} < 月NETの10%")
    if flags:
        raise RatchetGuardError(f"異常値・要調査(関所A): {flags}")
    return True


# ① 自己検査 — 連続モード sim が replay_csv.run() と件数・net 一致
def assert_selfcheck_match(n_a: int, net_a: float, n_b: int, net_b: float, tol: float = 0.01) -> bool:
    if n_a != n_b or abs(net_a - net_b) > tol:
        raise RatchetGuardError(f"自己検査(移植ミス): 連続モード({n_a}件 {net_a}) != replay({n_b}件 {net_b})")
    return True


# ② ボラの役割 — 凍結しない。feature importance を「見える化」するだけ（raise しない）
def report_vol_importance(importance: dict, top_k: int = 5) -> dict:
    """ボラ系(atr/bb_width/realized_vol)の重要度シェアと上位を返す。判定はしない（②・まこさんが見る）。"""
    total = sum(importance.values()) or 1.0
    vol_keys = ("atr", "bb_width", "realized_vol", "vol_")
    vol_share = sum(g for f, g in importance.items() if any(k in f.lower() for k in vol_keys)) / total
    top = sorted(importance, key=importance.get, reverse=True)[:top_k]
    top_is_vol = [f for f in top if any(k in f.lower() for k in vol_keys)]
    return {"vol_share": round(vol_share, 3), "top": top, "top_vol": top_is_vol}


# ===== 既知答えテスト（番人が壊れていない証明・python3 ratchet_guards.py で実行）=====
def _selftest() -> bool:
    import datetime as _dt
    ok = True

    def chk(name, fn_violation, fn_clean):
        nonlocal ok
        # 違反ケース: raise するのが正解
        try:
            fn_violation()
            print(f"  {name}: ❌ 違反を見逃した")
            ok = False
            return
        except RatchetGuardError:
            pass
        # 正常ケース: 通るのが正解
        try:
            fn_clean()
            print(f"  {name}: ✅")
        except RatchetGuardError as e:
            print(f"  {name}: ❌ 正常を誤検出 {e}")
            ok = False

    d1 = _dt.date(2024, 12, 31)
    d2 = _dt.date(2025, 4, 1)
    chk("leak未来参照",
        lambda: assert_no_future_ref("x = c.shift(-1)"),
        lambda: assert_no_future_ref("x = c.shift(1)"))
    chk("期間分割",
        lambda: assert_period_split(d2, d1),
        lambda: assert_period_split(d1, d2))
    chk("cap",
        lambda: assert_cap([(0, 10, 0.06), (5, 15, 0.06), (6, 12, 0.06)]),  # 5-10で0.18
        lambda: assert_cap([(0, 10, 0.06), (10, 20, 0.06)]))                # 重ならず0.06
    chk("コスト控除",
        lambda: assert_cost_applied(100.0, 100.0),   # net==gross=未控除
        lambda: assert_cost_applied(100.0, 96.0))    # net<gross=控除済
    chk("勘の数値",
        lambda: assert_constants_sourced("K_BARRIER = 1.5"),
        lambda: assert_constants_sourced("K_BARRIER = 1.5  # src: KB§3較正(0.9/1.83)"))
    chk("虚偽完了",
        lambda: assert_output_exists("/no/such/file_xyz.csv"),
        lambda: assert_output_exists(__file__))
    chk("異常値",
        lambda: assert_no_anomaly(0.85, 5000, 100),
        lambda: assert_no_anomaly(0.37, 102, 752))
    chk("自己検査",
        lambda: assert_selfcheck_match(100, 925.0, 99, 925.0),
        lambda: assert_selfcheck_match(265, 925.73, 265, 925.73))

    # ② ボラ report は raise しない（見える化のみ）の確認
    r = report_vol_importance({"atr_pct_7": 111939, "bb_slope_pct_20": 5000, "adx_14": 4000})
    print(f"  ②ボラreport(raiseしない): vol_share={r['vol_share']} top_vol={r['top_vol']}")
    return ok


if __name__ == "__main__":
    print("=== ratchet_guards ① 番人 既知答えテスト ===")
    result = _selftest()
    print("結果:", "全番人 PASS ✅" if result else "FAIL ❌")
    import sys
    sys.exit(0 if result else 1)
