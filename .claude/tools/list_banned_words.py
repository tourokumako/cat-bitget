#!/usr/bin/env python3
# list_banned_words.py — 文書を書く前に「今この瞬間に有効な禁止ワード/禁止形式」を一覧する read-only ツール。
#
# なぜ:
#   acceptance / improvement_plan / analysis_block / ledger / next_step を書く時、禁止ワード hook に
#   ブロックされてから直す試行錯誤でトークンを浪費した（2026-07-05 まこさん指摘・20回手戻り）。
#   ＝書く前にこれを1回走らせて「何が禁止か・正しい書き方」を確認し、言い換えを先に選ぶ。
#
# 設計（腐らせない）:
#   禁止ワードは各 hook の実体（.sh/.py）に散在し格納形もバラバラ（grep 選択肢／python リスト／構造正規表現）。
#   本ツールは【語そのものは持たず】、各 hook の「どの行が禁止語か」を対応づけた地図（SOURCES）だけを持ち、
#   実行時に hook を読んで【今の語を live 抽出】する。hook の語を直しても再実行で追従する。
#   hook の構造（変数名・格納形）を書き換えた時だけ SOURCES を直す＝その時は抽出が空になり ⚠️ で気づける（drift 検出）。
#
#   ⚠️ 落とし穴（重要）: 同じ hook 内に「禁止（書いたら×）」と「必須（書かないと×）」の grep が混在する
#   （例 block_premature_giveup は「いい面/活かし方」を書けと要求）。本ツールは SOURCES で禁止行だけを指す
#   ＝必須語を禁止語として誤表示しない。必須項目は acceptance_checklist.md / pdca_flow §1 を見る。
#
# 使い方:
#   python3 .claude/tools/list_banned_words.py            # 全部
#   python3 .claude/tools/list_banned_words.py acceptance # 対象ファイル名で絞り込み（acceptance/improvement_plan/ledger/next_step/design/strategy）
#
# read-only: hook を読むだけ・何も書かない・戦略/score.py に触れない。

import re
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"

# ── 禁止ワード/形式の在りか地図（語は持たない・行の指し先だけ） ──────────────────
# capture: hook 本文（全文）に対して適用する正規表現。group(1) が禁止パターン文字列。
#          findall で複数マッチしうるものは matches を全部出す。
# quote  : 抽出パターンを囲む引用符（display の整形用・情報のみ）。
SOURCES = [
    {
        "file": "block_uchikiri.sh",
        "kind": "禁止語（打ち切り思考）",
        "targets": "ledger.md / next_step.md / acceptance.md",
        "capture": r'HIT=\$\(printf.*?grep -oE "([^"]*)"',
        "guidance": "1回の悪化で方向を閉じない。「採用せず（地面は ratchet で維持）＋次の作り込み案」と書く。"
                    "leak/cap/degenerate/配管捨て駒 の即不採用は「即不採用（§8.4 理由=…）」と明記する。",
    },
    {
        "file": "block_premature_giveup.sh",
        "kind": "禁止語（中身の事前却下）",
        "targets": "ledger.md / next_step.md / forward_action.md / acceptance.md",
        "capture": r'HIT=\$\(printf.*?grep -oE "([^"]*)"',
        "guidance": "分析をしつくす前に潰さない。exhaustion_check.md（## 試した分析角度／## 未試行の分析角度／『未試行: なし』）"
                    "＋『いい面・活かし方』の併記が要る。",
    },
    {
        "file": "block_premature_giveup.sh",
        "kind": "禁止語（戦略の打ち切り・no-edge 断定）",
        "targets": "ledger.md / next_step.md / forward_action.md / acceptance.md",
        "capture": r'DEADEND=\$\(printf.*?grep -oE "([^"]*)"',
        "guidance": "戦略を『エッジ無し/死に枠』と結論するなら probe でなく score.py 両窓の数字＋『## 方法軸』（データ源/ラベリング/特徴/horizon/モデルを複数跨ぐ）が要る。",
    },
    {
        "file": "doc_map_guard.sh",
        "kind": "禁止語（経緯・失敗の物語）",
        "targets": "ledger.md / strat_v9ml_design.md（設計書）",
        "capture": r'ng\s*=\s*\[([^\]]*)\]',
        "pylist": True,
        "guidance": "ledger は 結果/原因3分類/改善/採用or不採用 だけ・設計書は 決定事項 だけ。経緯・失敗の物語は session_log へ、教訓は lessons_active へ。",
    },
    {
        "file": "require_analysis_before_proposal.sh",
        "kind": "禁止形式（線引きの手置き）",
        "targets": "improvement_plan.md",
        "capture": r'if grep -Eq "([^"]*)" "\$PLAN"',
        "guidance": "「閾値 X→Y」「○帯を除外」は禁止＝線引きはモデルに学習させる。分離指標を木(LightGBM)に特徴量として渡す形で書く（L-267）。前後比較は『A から B』と書く。",
    },
    {
        "file": "enforce_role_criteria.sh",
        "kind": "禁止語（scalp 尻すぼみ容認 / daytrade スキャル化）",
        "targets": "acceptance.md（TARGET が e37=scalp / e36=daytrade の時）",
        "capture": r"grep -oE '([^']*)'",
        "multi": True,
        "guidance": "e37(scalp) は『件数/日が増える（高頻度＝役割）』合格基準が必須・件数±0/頻度は次iter は禁止。e36(daytrade) はスキャル化/高頻度化 が禁止（1ポジを伸ばす）。",
    },
    {
        "file": "enforce_strategy_anchor.py",
        "kind": "禁止語（戦略からの逃げ文言）",
        "targets": "acceptance.md / improvement_plan.md",
        "capture": r'bad = re\.search\(r"([^"]*)"',
        "dedupe": True,
        "guidance": "『レンジ判定なし/暗黙に学ぶ/レンジゲート撤去』は禁止。入口を担当局面の判定で制約する識別子を GATE_IDENT= で宣言する（§1.2.1 係留）。",
    },
    {
        "file": "forbid_fixed_value_tuning.sh",
        "kind": "禁止構造（語でない）",
        "targets": "scripts/priority_rebuild/*.py",
        "capture": None,
        "note": "大文字定数に『数値2個以上のタプル/リスト』を手置きしてスイープ（例 K_SL = (1.0, 1.5, 2.0)）＝禁止。",
        "guidance": "レバーは ML 場面別学習で値・切れ目を出す。ML(lightgbm)が選ぶ離散メニューは対象外。正当な非戦略定数は小文字に。まこさん明示 GO 後のみ # fixed-value-approved マーカーで通る。",
    },
]

_META = set("()[].*?+^${}\\")


def _split_pattern(pat):
    """正規表現メタが無ければ | で綺麗に分割・あれば生パターンを返す。"""
    if any(ch in _META for ch in pat):
        return None  # 生パターン表示
    return [w for w in pat.split("|") if w]


def _extract(text, cap, multi=False, dedupe=False):
    if cap is None:
        return []
    rx = re.compile(cap, re.DOTALL)
    if multi:
        found = rx.findall(text)
    else:
        m = rx.search(text)
        found = [m.group(1)] if m else []
    if dedupe:
        seen, out = set(), []
        for f in found:
            if f not in seen:
                seen.add(f); out.append(f)
        found = out
    return found


def main():
    filt = sys.argv[1].lower() if len(sys.argv) > 1 else None
    print("=" * 70)
    print("禁止ワード/形式 一覧（hook 実体から live 抽出・書く前に確認する）")
    if filt:
        print(f"絞り込み: 対象ファイルに『{filt}』を含む hook のみ")
    print("=" * 70)

    drift = []
    shown = 0
    for s in SOURCES:
        if filt and filt not in s["targets"].lower():
            continue
        fp = HOOKS / s["file"]
        if not fp.exists():
            drift.append(f"{s['file']}: ファイルが無い")
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")

        shown += 1
        print(f"\n■ {s['kind']}")
        print(f"  hook   : {s['file']}")
        print(f"  対象   : {s['targets']}")

        if s["capture"] is None:
            print(f"  内容   : {s.get('note','')}")
        else:
            found = _extract(text, s["capture"], s.get("multi"), s.get("dedupe"))
            if not found:
                drift.append(f"{s['file']}: 『{s['kind']}』の抽出が空（構造が変わった＝SOURCES 要更新）")
                print("  ⚠️ 抽出できず＝hook の構造が変わった可能性（source map を要更新）")
            for pat in found:
                if s.get("pylist"):
                    items = re.findall(r'"([^"]+)"', pat)
                    print(f"  禁止語 : {' / '.join(items)}")
                    continue
                words = _split_pattern(pat)
                if words is None:
                    print(f"  形式   : {pat}")
                else:
                    print(f"  禁止語 : {' / '.join(words)}")
        print(f"  → 正しい書き方: {s['guidance']}")

    print("\n" + "-" * 70)
    print(f"表示 {shown} 件 ／ 全 {len(SOURCES)} 源")
    if drift:
        print("⚠️ drift（source map と hook 実体のズレ・要更新）:")
        for d in drift:
            print(f"   - {d}")
    else:
        print("✅ 全源で抽出成功（source map と hook 実体は一致）")
    print("補足: これは【禁止】だけの一覧。【必須項目】は acceptance_checklist.md / pdca_flow §1 を見る。")


if __name__ == "__main__":
    main()
