#!/usr/bin/env python3
"""block_long_background.py — 裏で走らせる仕組み（Bash の run_in_background）の上限2時間を超える走らせ方を、走らせる前に止める（PreToolUse・Bash）。

なぜ要るか（2026-10-02・147回目・まこさん「修正しろ」）
  成績表の全走（observe_diag.py --rank-regime・約2時間15分）を run_in_background で走らせ、timeout に 10,800,000 ミリ秒（3時間）を渡した。
  run_in_background の上限は 7,200,000 ミリ秒（2時間）で、それより大きい値は黙って2時間に切り詰められる（道具の説明に記載）。
  走行は 23:29 に「background time limit」で止められ、残り約18分で、2時間ぶんの計算が全部 消えた（成績表は最後にまとめて書く作り）。
  ＝私（CC）は上限を確かめずに走らせた。確かめ忘れても走らせられない形にする。

何を止めるか（run_in_background が true のときだけ見る）
  A: timeout が 7,200,000 ミリ秒（2時間）を超える＝その値は効かない（2時間で止まる）
  B: 成績表の全走（observe_diag.py の --rank-regime で、--cols・--rank-tf を付けない形）＝前の全走の実測は 129〜132分で、
     今日の2回目は 120分で止められた＝2時間を超える＝裏で走らせる仕組みでは終わらない
通し方（止めたときに出す）
  run_in_background を使わず、ふつうの呼び出しの中で、出力を記録のファイルに書き、末尾に & を付けて切り離す。
  見張りは Monitor で記録のファイルを読む（memory の feedback_check_tool_limits_and_records_before_long_run）。
限界（正直に）
  ・成績表の全走のほかの長い走行は、名前を知らないので B では止めない（A だけが効く）。
  ・& で切り離した走行が2時間を超えて生き残るかは、この hook では見ない。
番人: python3 .claude/hooks/block_long_background.py --selftest
"""
import json
import re
import sys

LIMIT_MS = 7_200_000
FULL_RANK = re.compile(r"observe_diag\.py\b[^;&|\n]*--rank-regime")
NARROW = re.compile(r"--cols\b|--rank-tf\b|--add-demand\b|--help\b|--selftest\b")


def check(tool_input: dict) -> list:
    ng = []
    if not tool_input.get("run_in_background"):
        return ng
    t = tool_input.get("timeout")
    try:
        t = int(t) if t is not None else None
    except (TypeError, ValueError):
        t = None
    if t is not None and t > LIMIT_MS:
        ng.append(f"A: timeout {t:,} ミリ秒は、裏で走らせる仕組みの上限 {LIMIT_MS:,} ミリ秒（2時間）を超えている"
                  "＝黙って2時間に切り詰められ、2時間で止められる")
    cmd = str(tool_input.get("command") or "")
    for seg in re.split(r"[;\n]|&&|\|\|", cmd):
        if FULL_RANK.search(seg) and not NARROW.search(seg):
            ng.append("B: 成績表の全走（observe_diag.py --rank-regime）は約2時間15分かかる（前の全走 129〜132分・"
                      "results/priority_rebuild/ratchet/observe/archive）＝裏で走らせる仕組みの上限2時間では終わらない")
            break
    return ng


def selftest() -> int:
    bad = []
    full = "cd SDK && python3 scripts/priority_rebuild/observe_diag.py --rank-regime data/x.csv 2>&1"
    cases = [
        ("1 上限を超える timeout", {"command": "echo hi", "run_in_background": True, "timeout": 10_800_000}, True),
        ("2 上限ちょうど", {"command": "echo hi", "run_in_background": True, "timeout": 7_200_000}, False),
        ("3 全走を裏で", {"command": full, "run_in_background": True, "timeout": 7_200_000}, True),
        ("4 全走を & で切り離す（裏で走らせない）", {"command": full + " > log.txt &"}, False),
        ("5 列を絞った走行を裏で", {"command": full.replace("--rank-regime", "--rank-regime --cols ATR"), "run_in_background": True}, False),
        ("6 需給の足し直しを裏で", {"command": full.replace("--rank-regime", "--rank-regime --add-demand"), "run_in_background": True}, False),
        ("7 裏でない上限超え（foreground の上限は別）", {"command": "echo hi", "timeout": 10_800_000}, False),
        ("8 timeout が文字", {"command": "echo hi", "run_in_background": True, "timeout": "x"}, False),
    ]
    for name, ti, want_block in cases:
        got = bool(check(ti))
        if got != want_block:
            bad.append(f"{name}: 止める={got}（期待 {want_block}）")
    for b in bad:
        print(f"❌ {b}")
    print(f"{'❌' if bad else '✅'} わざと壊して止まるか試すテスト {len(cases) - len(bad)}/{len(cases)} pass")
    return 1 if bad else 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    try:
        d = json.load(sys.stdin)
    except Exception:
        return 0
    if d.get("tool_name") != "Bash":
        return 0
    ng = check(d.get("tool_input") or {})
    if not ng:
        return 0
    print("🔒 [裏の走行の上限・Bash] 裏で走らせる仕組み（run_in_background）の上限は2時間です。"
          "2時間を超える走行は、この形では途中で止められ、結果が残りません（2026-10-02 に2時間を失った）。", file=sys.stderr)
    for x in ng:
        print(f"   ❌ {x}", file=sys.stderr)
    print("   通し方＝run_in_background を使わず、出力を記録のファイルに書き、末尾に & を付けて切り離す。"
          "見張りは Monitor で記録のファイルを読む。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
