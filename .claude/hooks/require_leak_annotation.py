#!/usr/bin/env python3
"""require_leak_annotation.py — PreToolUse(Write|Edit) 戦略実装への leak パターン書き込みゲート（2026-07-04 まこさん承認）

目的: H2（Prime Directive・未来参照禁止）の物理化が「実装者が自分で assert を書く」頼みだった穴を塞ぐ。
scripts/priority_rebuild/ 配下の .py に、未来参照の典型パターン（.shift(- ／ center=True）を含む行を
書こうとした瞬間、その行に明示アノテーション「# H2OK: <理由>」が無ければブロックする。
＝未来参照を書くこと自体は禁止しない（ラベル/教師生成は学習窓内で正当・H8）が、
**全ての未来参照サイトを書く瞬間に明示宣言させ、レビュー可能にする**（false_positive §0-1 の
「t 時点で取得可能と判定した根拠を1行で明示する義務」の書き込み時強制）。

対象外: basename が build_labels で始まるファイル（ラベル生成の正本＝shift(-K) が本業）・archive/ 配下・
サブエージェント。既存戦略（e35/e36/e37/strat_base）は 2026-07-04 時点で該当パターン 0 件を確認済み＝
本 hook は既存コードを壊さない（新たに書く時だけ効く）。
限界: パターン網羅ではない（rolling の窓ずれ・index 演算等は検出外）＝関所 B（変数の因果性宣言）と
score.py・レビューが引き続き担保。
"""
import sys, json, re, os

ERRLOG = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/require_leak_annotation_error.log"
PAT = re.compile(r"\.shift\(\s*-|center\s*=\s*True")


def main():
    d = json.load(sys.stdin)
    if d.get("agent_type"):
        return 0
    ti = d.get("tool_input", {}) or {}
    fp = ti.get("file_path", "")
    if "scripts/priority_rebuild/" not in fp or not fp.endswith(".py"):
        return 0
    if "/archive/" in fp or os.path.basename(fp).startswith("build_labels"):
        return 0
    c = ti.get("content")
    if c is None:  # Edit＝新しく書く断片（new_string）だけを検査（既存行の再保存で誤発火しない）
        c = ti.get("new_string") or ""
    if not c:
        return 0
    bad = []
    for i, line in enumerate(c.splitlines(), 1):
        if PAT.search(line) and "H2OK:" not in line:
            bad.append((i, line.strip()[:120]))
    if not bad:
        return 0
    sys.stderr.write("🔒 [H2 leak アノテーションゲート] 未来参照の典型パターン（.shift(- / center=True）を含む行に「# H2OK: <理由>」がありません:\n")
    for i, line in bad[:5]:
        sys.stderr.write("  L%d: %s\n" % (i, line))
    sys.stderr.write("  → 各行に『# H2OK: <この未来参照が本番再現可能/学習窓に閉じる理由>』を付けてください（false_positive §0-1 の因果性宣言の書き込み時強制）。\n")
    sys.stderr.write("  → 理由を書けない未来参照は H2 違反＝設計から直してください（cat_requirements §4.6 H2・関所B）。\n")
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        try:
            with open(ERRLOG, "a") as f:
                f.write(repr(e) + "\n")
        except Exception:
            pass
        sys.exit(0)
