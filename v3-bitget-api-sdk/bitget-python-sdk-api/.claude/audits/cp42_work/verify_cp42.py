#!/usr/bin/env python3
"""verify_cp42.py — 監査 CP42 の修正を当てた後に、まこさんが端末から確かめる（119回目・2026-09-25）。

順に走らせ、終了コードと出力の末尾を出す（止まらず最後まで走る）。
  1. 文法＝py_compile（当てる道具・設計書を作る道具・承認の前の検査の hook）と bash -n（壊すプログラム b102）
  2. 当てる道具の自己テスト（SDK の中から・完成の条件 #3 と同じ形）＝Critical を当てていれば 16/16 の期待
  3. 設計書を作る道具の自己テスト＝9/9 の期待
  4. 設計書を作り直す（修正 11・25・35 の「走らせるコマンド」）→ --verify
  5. 設計↔実装ゲートと同じ照合A〜D（SDK の中から）と --diff＝修正 7〜9 を当てていれば RESULT: PASS の期待
  6. 承認の前の検査（pre_audit_check.py --check-design）
  7. 新しい設計書のハッシュ値（承認の相手）
★子プロセスの標準入力は閉じる（118回目に 600秒 打ち切られた件の疑いへの対応・next_step §6 の201番）。
"""
import hashlib
import os
import py_compile
import subprocess
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
ACC = os.path.join(ROOT, ".claude", "state", "acceptance.md")


def run(label, cmd, cwd, timeout=900, tail=12):
    print(f"\n=== {label}\n$ {' '.join(cmd)}   （作業場所＝{os.path.relpath(cwd, ROOT) or '直下'}）")
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        print(f"❌ {timeout}秒で打ち切り")
        return None
    out = ((r.stdout or "") + (r.stderr or "")).rstrip().splitlines()
    for ln in out[-tail:]:
        print("   " + ln)
    print(f"→ rc={r.returncode}")
    return r.returncode


def main():
    results = {}
    print("=== 1. 文法")
    for rel in (".claude/tools/apply_audit_fix.py", ".claude/tools/gen_acceptance.py",
                ".claude/hooks/require_design_check_before_approval.py"):
        try:
            py_compile.compile(os.path.join(ROOT, rel), doraise=True)
            print(f"   ✅ py_compile {rel}")
        except Exception as e:                       # noqa: BLE001
            print(f"   ❌ py_compile {rel}: {e}")
            results["文法"] = 1
    results.setdefault("文法", run("1b. bash -n b102", ["bash", "-n", ".claude/breaks/b102_design_apply_no_precheck.sh"], ROOT))

    results["自己テスト（当てる道具）"] = run(
        "2. 当てる道具の自己テスト（SDK の中から）",
        ["python3", "../../.claude/tools/apply_audit_fix.py", "--selftest"], SDK, tail=20)
    results["自己テスト（設計書を作る道具）"] = run(
        "3. 設計書を作る道具の自己テスト",
        ["python3", ".claude/tools/gen_acceptance.py", "--selftest"], ROOT, tail=12)
    results["--write"] = run("4a. 設計書を作り直す", ["python3", ".claude/tools/gen_acceptance.py", "--write"], ROOT, tail=8)
    results["--verify"] = run("4b. 設計書の囲みの検出", ["python3", ".claude/tools/gen_acceptance.py", "--verify"], ROOT, tail=14)
    results["照合A〜D"] = run(
        "5a. 設計↔実装ゲートと同じ照合A〜D（SDK の中から）",
        ["python3", "scripts/priority_rebuild/verify_design_contract.py", ACC], SDK, tail=14)
    results["--diff"] = run(
        "5b. SPEC の比べ（--diff）",
        ["python3", "scripts/priority_rebuild/verify_design_contract.py", "--diff", ACC], SDK, tail=8)
    results["承認の前の検査"] = run(
        "6. 承認の前の検査", ["python3", ".claude/tools/pre_audit_check.py", "--check-design"], ROOT, tail=20)

    print("\n=== 7. 新しい設計書のハッシュ値（承認の相手）")
    print("   " + hashlib.sha256(open(ACC, "rb").read()).hexdigest())

    print("\n=== まとめ（rc）")
    for k, v in results.items():
        print(f"   {k}: {v}")
    print("\n次＝承認（bash .claude/hooks/approve_impl.sh を直下から）。承認のプログラムが b101・b102 を走らせ、"
          "完成の条件 #3・#4 を測ります。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
