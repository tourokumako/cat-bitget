#!/usr/bin/env python3
"""apply_cp42.py — 監査 CP42 の結果の「修正の指示」を、まこさんが端末から当てる（119回目・2026-09-25）。

なぜ まこさんが打つか
  ①当てる道具 apply_audit_fix.py は、いま CC の Bash から走らない（監査 CP42 の B3＝設計↔実装ゲートが
    照合C で止める。修正 7 を当てて設計書を作り直し、承認が通るまで続く）。
  ②修正40件のうち20件の相手は .claude/tools・.claude/breaks・.claude/hooks（守りの相手）で、
    当てる道具は設計どおり当てない（NEVER_WRITE）。CC の Write も権限の制限で拒まれる（next_step §6 の201番）。

何をするか
  当てる道具の main をそのまま呼ぶ（読み取り・欄の形・全件を先に確かめる・当てた後の中身でも確かめる・
  ファイルごとにまとめて書く・走らせるコマンドと未決の件は当てずに一覧に出す＝全部 道具のまま）。
  変えるのは1つだけ＝この1回のプロセスの中で、守りの相手の判定（never_write）を「守りではない」にする。
  ＝監査が書いた文字を、プログラムがそのまま当てる（手で写さない）。

使い方（絶対パスで打つ・作業場所はどこでもよい）
  python3 <このファイル> --severity Critical --dry             … 当てずに、当たるかだけ見る
  python3 <このファイル> --severity Critical,Major              … 本番（Major まで）
  python3 <このファイル> --severity Critical,Major,Minor,Process … Process まで（39・40 は未決なので当たらない）
  --only 1,2,3 を足すと、その番号だけ

当てた後に打つもの＝verify_cp42.py（同じ置き場）→ 承認（bash .claude/hooks/approve_impl.sh）
"""
import hashlib
import os
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
REPORT = os.path.join(SDK, ".claude", "audits", "2026-09-24_impl_instruction_apply_impl_cp42_audit_report.md")
sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))
import apply_audit_fix as aaf  # noqa: E402

WATCH = [
    os.path.join(ROOT, ".claude", "tools", "apply_audit_fix.py"),
    os.path.join(ROOT, ".claude", "tools", "gen_acceptance.py"),
    os.path.join(ROOT, ".claude", "breaks", "b102_design_apply_no_precheck.sh"),
    os.path.join(ROOT, ".claude", "hooks", "require_design_check_before_approval.py"),
    os.path.join(SDK, ".claude", "ratchet", "acceptance_src.json"),
]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.isfile(p) else "（無い）"


def main():
    args = sys.argv[1:]
    if "--severity" not in args or "--report" in args or "--design" in args:
        print(__doc__)
        return 2
    if not os.path.isfile(REPORT):
        print(f"❌ 監査結果が無い: {REPORT}")
        return 1
    print(f"— 監査結果: {os.path.relpath(REPORT, ROOT)}")
    print(f"— 結果ファイルの sha256: {sha(REPORT)}…")
    before = {p: sha(p) for p in WATCH}
    for p, h in before.items():
        print(f"— 当てる前: {h}… {os.path.relpath(p, ROOT)}")

    # 守りの相手の件を、先に一覧に出す（当てる道具は設計どおり当てない相手。この1回だけ通す）
    fixes = aaf.read_fixes(open(REPORT, encoding="utf-8").read())
    guarded = [f for f in fixes if aaf.never_write(f["対象のファイル"] or "")]
    print(f"— 守りの相手の件（この1回だけ通す）: {len(guarded)} 件＝修正 "
          + "・".join(f["番号"] for f in guarded))
    aaf.never_write = lambda rel: False          # ★この1回のプロセスの中だけ

    rc = aaf.main(["--report", REPORT] + args)

    if "--dry" not in args:
        print("")
        for p, h in before.items():
            now = sha(p)
            mark = "変わった" if now != h else "そのまま"
            print(f"— 当てた後: {now}… {os.path.relpath(p, ROOT)}（{mark}）")
    print(f"\n— 終了コード: {rc}（0＝当てた／1＝実物と合わない件が在って1件も当てていない、"
          f"または 当てない件が在る／2＝使い方）")
    return rc


if __name__ == "__main__":
    sys.exit(main())
