#!/usr/bin/env python3
# list_banned_words.py — 文書を書く前に「その文書のゲート要件」を出す read-only ツール。
#   ① 必須見出し（書かないとブロック＝pdca_gate/require_analysis の厳密一致トークン・コピペ用）
#   ② 禁止ワード/形式（書いたらブロック）＋正しい書き方
#
# なぜ:
#   ledger/next_step/acceptance/improvement_plan/analysis_block を書く時、
#   ・禁止ワード hook にブロックされてから直す（2026-07-05 まこさん・20回手戻り）
#   ・必須見出しの厳密一致ズレで PDCA が閉じない（2026-07-06 まこさん・【問1 レバー】でないと通らない）
#   の両方でトークンを浪費した。＝書く前にこれを1回走らせ、見出しをコピペし、禁止語を避ける。
#
# 設計（腐らせない）:
#   語も見出しも【持たず】、各 hook の「どの行が要件か」を対応づけた地図（REQUIRED / SOURCES）だけを持ち、
#   実行時に hook を読んで【今の要件を live 抽出】する。hook を直しても再実行で追従（腐らない）。
#   hook の構造（変数名・格納形）を書き換えた時だけ地図を直す＝抽出が空になり ⚠️ で気づける（drift 検出）。
#
# 使い方:
#   python3 .claude/tools/list_banned_words.py                # 全部
#   python3 .claude/tools/list_banned_words.py ledger         # ledger の必須見出し＋禁止語だけ
#   （引数＝ledger / next_step / acceptance / improvement_plan / analysis_block）
#
# read-only: hook を読むだけ・何も書かない・戦略/score.py に触れない。

import re
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"

# ── ① 必須見出しの在りか地図（書かないとブロック・厳密一致トークンを live 抽出） ─────────────
#   mode: "quoted"      = 捕捉群の中の "..." を全部（python リスト/タプルの要素）
#         "findall"     = 捕捉正規表現を text 全体に findall（group1 のリスト）
#         "first"       = findall の先頭ユニーク
REQUIRED = [
    # ★2026-08-22（50回目）＝読む先を pdca_gate.sh から pdca_gate_body.py に移した。
    #   理由＝同日に、pdca_gate.sh の中に埋め込まれていた判定を pdca_gate_body.py へ出したため
    #   （直したあとに走らせて確かめられるようにする・pdca_flow.md の「hook の python は別ファイル」）。
    #   移す前は、この地図が pdca_gate.sh から見出しを取れず「drift（地図と実体のズレ）」を4件 出していた。
    {"doc": "ledger", "file": "pdca_gate_body.py",
     "label": "6つの問い（最新 ## エントリに厳密一致で全部必須・そのままコピペ）",
     "capture": r'TOKS\s*=\s*\[([^\]]*)\]', "mode": "quoted",
     "note": "pdca_need_5q。見出しが1字でも違うと旗が残る（2026-07-06 事案）。下をコピペして各問の見出しにする。"},
    {"doc": "ledger", "file": "pdca_gate_body.py",
     "label": "方針（下のいずれか1語を含む見出しが必須・例『【方針/狙い】』）",
     "capture": r'in latest for k in \(([^)]*)\)', "mode": "quoted",
     "note": "pdca_need_5q。方針/狙い/目的 のどれかを含む見出し。"},
    {"doc": "ledger", "file": "pdca_gate_body.py",
     "label": "主張（必須・厳密一致）",
     "capture": r'return "([^"]+)" in latest', "mode": "first",
     "note": "pdca_need_claim。【主張】1行（件数/日 と net を含む結論）。"},
    {"doc": "next_step", "file": "pdca_gate_body.py",
     "label": "必須見出し（4つ・厳密一致。★本筋 と 次にやること は どちらか1つで満たす）",
     "capture": r'NS_HEAD_WORDS\s*=\s*\[([^\]]*)\]', "mode": "quoted",
     "note": "pdca_need_next_step。＋改善の経緯の表は『python3 .claude/ratchet/gen_improvement_arc.py --write』で作る（improvement_arc.md の1行目の印 ARC_DOC hash と本文の一致が必須・手書き禁止・2026-08-22 に判定を実物へ合わせた）。"},
    {"doc": "analysis_block", "file": "require_analysis_before_proposal.sh",
     "label": "必須見出し（B完了ゲート・9+）",
     "capture": r'grep -q "([^"]+)"\s+"\$BLOCK"', "mode": "findall",
     "note": "acceptance を書く前に analysis_block に全部必須。⑧経緯照合は E番号/iter番号 の引用も必須。"},
    {"doc": "improvement_plan", "file": "require_analysis_before_proposal.sh",
     "label": "STEP3/3.5/4 必須トークン",
     "capture": r'grep -q "([^"]+)"\s+"\$PLAN"', "mode": "findall",
     "note": "＋LEVER『<!-- LEVER: X -->』・異手法2種以上・件数/前後比較（enforce_pdca_chain）。STEP3.5 は各行『出典: N番号』5つ以上。"},
]
# ── ★2026-08-26（63回目・まこさん指示）＝設計書（acceptance）の必須見出しを、名前で出す ─────
#
# なぜ直したか:
#   直す前、この道具は設計書のときだけ「必須見出しは acceptance_checklist.md が正本」としか出さず、
#   見出しの名前を1つも出していなかった（ほかの文書はコピペできる形で出していた）。
#   ＝私（CC）は設計書を白紙から書き、必須の見出しを落とした（2026-08-26 に実際に4つ落として hook に止められた）。
#   実測＝承認済みの控え66本のうち、深掘り4点がそろっていないものが3本。
#
# まこさんの指示（逐語 2026-08-26）:
#   「見出しを2つの群に分け、道具が相手を見て、要る方だけを出します。
#     →このようにして、acceptanceを書くときに、見出しを読み込める状態に修正して」
#
# 作り（腐らせない・この道具の元からの思想と同じ）:
#   ・hook が止める見出し（TARGET / DESIGN_CONTRACT / 深掘り4点 / 疑似シミュ由来の固定値ゼロ）は
#     hook の実物から live 抽出する（下の REQUIRED_ACC）。
#   ・照合の項目（30件）と その群（【群1】【群2】）は acceptance_checklist.md から読む（正本はあちら）。
#   ・どちらの群を出すかは、いまの設計書の TARGET を見て決める。
REQUIRED_ACC = [
    {"file": "require_acceptance_before_impl.sh",
     "label": "深掘り4点（hook が語で止める・見出しに入れる）",
     "capture": r'for kw in ((?:"[^"]+"\s*)+); do', "mode": "quoted"},
    {"file": "require_acceptance_before_impl.sh",
     "label": "機械照合の部品リスト（無いと止まる）",
     "capture": r'grep -q "(DESIGN_CONTRACT)" "\$LIST"', "mode": "first"},
    {"file": "require_acceptance_before_impl.sh",
     "label": "疑似シミュ由来の固定値ゼロ宣言（無いと止まる・どちらの言い方でもよい）",
     "capture": r'grep -qE "([^"]*固定値ゼロ[^"]*)" "\$LIST"', "mode": "first"},
]

CHECKLIST = (Path(__file__).resolve().parent.parent.parent
             / "v3-bitget-api-sdk" / "bitget-python-sdk-api" / ".claude" / "rules" / "acceptance_checklist.md")
ACCEPTANCE_MD = Path(__file__).resolve().parent.parent / "state" / "acceptance.md"

# 群2（売買のロジック・審判）を1件ずつ照合する相手＝TARGET の名前がこれで始まる/一致するとき。
#   正本＝acceptance_checklist.md の「★項目の群」。ここは判定だけを持つ。
G2_PREFIX = ("e35_", "e36_", "e37_", "e38_", "strat_", "measure_")
G2_EXACT = ("score.py", "eval_engine.py", "report.py", "analyze.py", "precheck.py")


def acceptance_target(path=None):
    """いまの設計書の TARGET（直す相手のファイル）を返す。無ければ None。"""
    p = Path(path) if path else ACCEPTANCE_MD
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s.startswith("TARGET:"):
            return s[len("TARGET:"):].strip()
    return None


def needs_group2(target):
    """その相手が『売買のロジックか審判』かを判定する（群2 を1件ずつ照合するか）。"""
    if not target:
        return True                     # 分からないときは広い方＝群2 も出す（安全側）
    name = target.replace("\\", "/").split("/")[-1]
    return name in G2_EXACT or name.startswith(G2_PREFIX)


def checklist_items():
    """acceptance_checklist.md から（群, 見出しの文）の一覧を読む。"""
    if not CHECKLIST.exists():
        return []
    out = []
    for line in CHECKLIST.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s.startswith("- ☐"):
            continue
        g = "群1" if "【群1】" in s else ("群2" if "【群2】" in s else "印なし")
        body = re.sub(r"^- ☐\s*【群[12]】\s*|^- ☐\s*", "", s)
        body = body.replace("**", "")
        out.append((g, body))
    return out

# ── ② 禁止ワード/形式の在りか地図（書いたらブロック） ──────────────────────────
SOURCES = [
    {"file": "block_uchikiri.sh", "kind": "禁止語（打ち切り思考）",
     "targets": "ledger.md / next_step.md / acceptance.md",
     "capture": r'HIT=\$\(printf.*?grep -oE "([^"]*)"',
     "guidance": "1回の悪化で方向を閉じない。「採用せず（地面は ratchet で維持）＋次の作り込み案」と書く。leak/cap/degenerate/配管捨て駒 の即不採用は「即不採用（§8.4 理由=…）」と明記する。"},
    {"file": "block_premature_giveup.sh", "kind": "禁止語（中身の事前却下）",
     "targets": "ledger.md / next_step.md / forward_action.md / acceptance.md",
     "capture": r'HIT=\$\(printf.*?grep -oE "([^"]*)"',
     "guidance": "分析をしつくす前に潰さない。exhaustion_check.md（## 試した分析角度／## 未試行の分析角度／『未試行: なし』）＋『いい面・活かし方』の併記が要る。"},
    {"file": "block_premature_giveup.sh", "kind": "禁止語（戦略の打ち切り・no-edge 断定）",
     "targets": "ledger.md / next_step.md / forward_action.md / acceptance.md",
     "capture": r'DEADEND=\$\(printf.*?grep -oE "([^"]*)"',
     "guidance": "戦略を『エッジ無し/死に枠』と結論するなら probe でなく score.py 両窓の数字＋『## 方法軸』（データ源/ラベリング/特徴/horizon/モデルを複数跨ぐ）が要る。"},
    {"file": "doc_map_guard.sh", "kind": "禁止語（経緯・失敗の物語）",
     "targets": "ledger.md / strat_v9ml_design.md（設計書）",
     "capture": r'ng\s*=\s*\[([^\]]*)\]', "pylist": True,
     "guidance": "ledger は 結果/原因3分類/改善/採用or不採用 だけ・設計書は 決定事項 だけ。経緯・失敗の物語は session_log へ、教訓は lessons_active へ。"},
    {"file": "require_analysis_before_proposal.sh", "kind": "禁止形式（線引きの手置き）",
     "targets": "improvement_plan.md",
     "capture": r'if grep -Eq "([^"]*)" "\$PLAN"',
     "guidance": "「閾値 X→Y」「○帯を除外」は禁止＝線引きはモデルに学習させる。分離指標を木(LightGBM)に特徴量として渡す形で書く（L-267）。前後比較は『A から B』と書く。"},
    {"file": "enforce_role_criteria.sh", "kind": "禁止語（scalp 尻すぼみ容認 / daytrade スキャル化）",
     "targets": "acceptance.md（TARGET が e37=scalp / e36=daytrade の時）",
     "capture": r"grep -oE '([^']*)'", "multi": True,
     "guidance": "e37(scalp) は『件数/日が増える（高頻度＝役割）』合格基準が必須・件数±0/頻度は次iter は禁止。e36(daytrade) はスキャル化/高頻度化 が禁止（1ポジを伸ばす）。"},
    {"file": "enforce_strategy_anchor.py", "kind": "禁止語（戦略からの逃げ文言）",
     "targets": "acceptance.md / improvement_plan.md",
     "capture": r'bad = re\.search\(r"([^"]*)"', "dedupe": True,
     "guidance": "『レンジ判定なし/暗黙に学ぶ/レンジゲート撤去』は禁止。入口を担当局面の判定で制約する識別子を GATE_IDENT= で宣言する（§1.2.1 係留）。"},
    {"file": "forbid_fixed_value_tuning.sh", "kind": "禁止構造（語でない）",
     "targets": "scripts/priority_rebuild/*.py", "capture": None,
     "note": "大文字定数に『数値2個以上のタプル/リスト』を手置きしてスイープ（例 K_SL = (1.0, 1.5, 2.0)）＝禁止。",
     "guidance": "レバーは ML 場面別学習で値・切れ目を出す。ML(lightgbm)が選ぶ離散メニューは対象外。正当な非戦略定数は小文字に。まこさん明示 GO 後のみ # fixed-value-approved マーカーで通る。"},
]

_META = set("()[].*?+^${}\\")


def _split_pattern(pat):
    if any(ch in _META for ch in pat):
        return None
    return [w for w in pat.split("|") if w]


def _extract_banned(text, cap, multi=False, dedupe=False):
    if cap is None:
        return []
    rx = re.compile(cap, re.DOTALL)
    found = rx.findall(text) if multi else ([m.group(1)] if (m := rx.search(text)) else [])
    if dedupe:
        seen, out = set(), []
        for f in found:
            if f not in seen:
                seen.add(f); out.append(f)
        found = out
    return found


def _extract_required(text, entry):
    rx = re.compile(entry["capture"], re.DOTALL)
    mode = entry["mode"]
    if mode == "quoted":
        m = rx.search(text)
        return re.findall(r'"([^"]+)"', m.group(1)) if m else []
    if mode == "findall":
        seen, out = set(), []
        for g in rx.findall(text):
            if g not in seen:
                seen.add(g); out.append(g)
        return out
    if mode == "first":
        for g in rx.findall(text):
            return [g]
    return []


def skeleton():
    """設計書の骨組み（見出しだけ）を出す（★2026-08-26 新設・まこさん指示）。

    ★白紙から書くのをやめるための口。中身は1文字も書かない＝私が埋める。
      群2 を1件ずつ照合するかどうかは、いまの設計書の TARGET で決める。
    """
    target = acceptance_target()
    g2 = needs_group2(target)
    items = checklist_items()
    g1 = [b for g, b in items if g == "群1"]
    g2list = [b for g, b in items if g == "群2"]
    L = []
    L.append("# 設計書｜<何を作るか>")
    L.append("")
    L.append(f"TARGET: {target or 'scripts/priority_rebuild/<直す相手>.py'}")
    L.append("")
    L.append("REQUIREMENTS: <要件の番号（例 R17）>")
    L.append("")
    L.append("**承認の状態＝未承認。**実装はまだ1行も入れていません。")
    L.append("")
    L.append('<!-- ARC order=1 iter="<意味のある名前>" 前提="" 採否="未定" 狙い="" 内容="" 方法="" -->')
    L.append("")
    L.append("## 0｜まこさんの決定（逐語）")
    L.append("")
    L.append("## 1｜いまの状態（実測）")
    L.append("")
    L.append("★走らせたもの・走らせた場所・除外設定の影響 を先に書く。")
    L.append("")
    L.append("## 2｜深掘り4点")
    L.append("")
    L.append("### ① 真因（root cause）")
    L.append("")
    L.append("### ② 期待値分解")
    L.append("")
    L.append("### ③ root を直すか symptom か")
    L.append("")
    L.append("### ④ ベースアップ（参照した証跡）")
    L.append("")
    L.append("## 3｜何を作るか")
    L.append("")
    L.append("## 4｜★疑似シミュ由来の固定値ゼロ宣言")
    L.append("")
    L.append("## 5｜わざと壊して止まるか試すテスト")
    L.append("")
    L.append("## 6｜何ができたら完成か（★目的の欄つき）")
    L.append("")
    L.append("## 7｜既存を壊さないこと（副作用）")
    L.append("")
    L.append(f"## 8｜照合（群2＝{'1件ずつ' if g2 else 'まとめて非該当の1行でよい'}）")
    L.append("")
    for b in g1:
        L.append(f"- [ ] 【群1】{b[:110]}")
    if g2:
        for b in g2list:
            L.append(f"- [ ] 【群2】{b[:110]}")
    else:
        L.append(f"- [ ] 【群2・{len(g2list)}件】まとめて非該当（理由＝<売買のロジックにも審判にも触れないため>）")
    L.append("")
    L.append("## 9｜限界（隠さない）")
    L.append("")
    L.append("## 10｜SPEC（★手書きしない＝verify_design_contract.py --write の出力を写す）")
    L.append("")
    L.append("DESIGN_CONTRACT")
    L.append("")
    L.append("```json")
    L.append('{"impl_file": "scripts/priority_rebuild/<直す相手>.py", "self_check_calls": []}')
    L.append("```")
    print("\n".join(L))


def main():
    if "--skeleton" in sys.argv:
        skeleton()
        return
    filt = sys.argv[1].lower() if len(sys.argv) > 1 else None
    print("=" * 70)
    print("文書ゲート要件（hook 実体から live 抽出・書く前に確認）")
    if filt:
        print(f"絞り込み: {filt}")
    print("=" * 70)

    drift = []

    # ── ① 必須見出し（書かないとブロック） ──
    print("\n【① 必須見出し＝書かないとブロック（コピペ用・厳密一致）】")
    req_shown = 0
    for r in REQUIRED:
        if filt and filt not in r["doc"]:
            continue
        fp = HOOKS / r["file"]
        if not fp.exists():
            drift.append(f"{r['file']}: ファイルが無い"); continue
        items = _extract_required(fp.read_text(encoding="utf-8", errors="replace"), r)
        req_shown += 1
        print(f"\n■ [{r['doc']}] {r['label']}")
        print(f"  hook  : {r['file']}")
        if not items:
            drift.append(f"{r['file']}: 『{r['label']}』の抽出が空（構造が変わった＝地図要更新）")
            print("  ⚠️ 抽出できず＝hook の構造が変わった可能性（地図を要更新）")
        else:
            print(f"  必須  : {' / '.join(items)}")
        print(f"  → {r['note']}")
    if (not filt) or ("acceptance" in filt):
        req_shown += 1
        target = acceptance_target()
        g2 = needs_group2(target)
        print(f"\n■ [acceptance] 設計書の必須見出し")
        print(f"  いまの相手（TARGET）: {target or '（設計書がまだ無い）'}")
        print(f"  群2（売買のロジック・審判の照合 18件）: "
              f"{'1件ずつ照合する' if g2 else 'まとめて非該当の1行でよい（相手が戦略でも審判でもない）'}")
        for r in REQUIRED_ACC:
            fp = HOOKS / r["file"]
            if not fp.exists():
                drift.append(f"{r['file']}: ファイルが無い"); continue
            items = _extract_required(fp.read_text(encoding="utf-8", errors="replace"), r)
            if not items:
                drift.append(f"{r['file']}: 『{r['label']}』の抽出が空（構造が変わった＝地図要更新）")
                print(f"  ⚠️ {r['label']}: 抽出できず（地図を要更新）")
            else:
                print(f"  必須  : {' / '.join(items)}   ← {r['label']}")
        items = checklist_items()
        if not items:
            drift.append("acceptance_checklist.md: 項目（- ☐ の行）が読めない")
        else:
            g1 = [b for g, b in items if g == "群1"]
            g2list = [b for g, b in items if g == "群2"]
            none_mark = [b for g, b in items if g == "印なし"]
            print(f"\n  【群1＝どんな設計でも書く（{len(g1)}件）】")
            for b in g1:
                print(f"    ・{b[:110]}")
            if g2:
                print(f"\n  【群2＝1件ずつ照合する（{len(g2list)}件）】")
                for b in g2list:
                    print(f"    ・{b[:110]}")
            else:
                print(f"\n  【群2（{len(g2list)}件）＝この設計書では1件ずつ書かない。"
                      f"『H1〜H16 と審判整合は 非該当（理由）』の1行でよい】")
            if none_mark:
                drift.append(f"acceptance_checklist.md: 群の印が無い項目 {len(none_mark)}件")
        print(f"  → 正本＝acceptance_checklist.md（群の印もあちらが正本）。"
              f"骨組みが要るときは『python3 .claude/tools/list_banned_words.py --skeleton』。")
    if req_shown == 0:
        print("  （この絞り込みに該当する必須見出しなし）")

    # ── ② 禁止（書いたらブロック） ──
    print("\n\n【② 禁止＝書いたらブロック（言い換えを先に選ぶ）】")
    ban_shown = 0
    for s in SOURCES:
        if filt and filt not in s["targets"].lower():
            continue
        fp = HOOKS / s["file"]
        if not fp.exists():
            drift.append(f"{s['file']}: ファイルが無い"); continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        ban_shown += 1
        print(f"\n■ {s['kind']}")
        print(f"  hook  : {s['file']}")
        print(f"  対象  : {s['targets']}")
        if s["capture"] is None:
            print(f"  内容  : {s.get('note','')}")
        else:
            found = _extract_banned(text, s["capture"], s.get("multi"), s.get("dedupe"))
            if not found:
                drift.append(f"{s['file']}: 『{s['kind']}』の抽出が空（構造が変わった＝地図要更新）")
                print("  ⚠️ 抽出できず（地図を要更新）")
            for pat in found:
                if s.get("pylist"):
                    print(f"  禁止語 : {' / '.join(re.findall(chr(34) + '([^' + chr(34) + ']+)' + chr(34), pat))}")
                    continue
                words = _split_pattern(pat)
                print(f"  {'禁止語' if words else '形式  '} : {' / '.join(words) if words else pat}")
        print(f"  → 正しい書き方: {s['guidance']}")
    if ban_shown == 0:
        print("  （この絞り込みに該当する禁止語なし）")

    print("\n" + "-" * 70)
    if drift:
        print("⚠️ drift（地図と hook 実体のズレ・要更新）:")
        for d in drift:
            print(f"   - {d}")
    else:
        print("✅ 全項目で抽出成功（地図と hook 実体は一致）")


if __name__ == "__main__":
    main()
