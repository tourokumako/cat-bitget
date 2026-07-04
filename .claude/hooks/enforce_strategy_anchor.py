#!/usr/bin/env python3
"""enforce_strategy_anchor.py — PreToolUse(Write|Edit) acceptance.md 戦略係留ゲート（2026-07-04 まこさん承認）

目的: acceptance を書く瞬間に、TARGET 戦略の「担当局面・方向・頻度」（台帳 STRATEGY_ANCHOR マーカー＝
cat_requirements §1.2.1 全体戦略の機械可読形）との照合を物理強制する。
背景: E37 が5段階のドリフト（MVP で両側化・v2/v3 でレンジ判定撤去・v5 で教師を「学習窓で儲かったか」に
すり替え・v6 でトレンドイベントを母数に追加）で §1.2.1（ショートのみ・レンジ・スキャル）違反のまま
8イテレーション走った事案（ledger ARC11〜23・2026-07-04 まこさん監査で発覚・L-322）。
既存の局所連結の強制（enforce_pdca_chain・改善アーク）は「前の iter との連結」しか守らず、
鎖全体が戦略から漂流しても検出できない＝「戦略への係留」を acceptance の瞬間に足す。

汎用設計: hook に戦略名を焼かない＝台帳マーカー追従（PORTFOLIO_CHECK/ROLE_CHECK と同型）。
  マーカー: <!-- STRATEGY_ANCHOR: e37=range,short_only,scalp ; e36=range,short_only,daytrade ; ... -->
  未定義 token はスルー。局面 none・方向 both は該当軸スルー（誤発火しない）。

検査（軸ごと）:
  共通: 見出し「★戦略照合」＋台帳マーカー逐語（token=局面,方向,頻度）の再掲（古い写し＝台帳更新後は不一致でブロック）。
  局面(range 等): GATE_IDENT=<識別子> 宣言（入口を担当局面の判定で制約する列/関数名）＋識別子が
    DESIGN_CONTRACT の fenced json 内に在ること（→ 既存 require_design_contract_before_run が実行前に
    実装ソースとの実在照合を行う＝設計に書いた・実装に無い、を実行前に止める）＋逃げ文言ブロック。
  方向(short_only/long_only): SIDE_IDENT=<識別子> 宣言＋DESIGN_CONTRACT 内在（例: short_only フラグ＝E36 が手本）。
  頻度(scalp/daytrade): 既存 enforce_role_criteria.sh（ROLE_CHECK）が担当＝本 hook は重複検査しない。

限界（正直に）: 識別子が実装で形だけ（入口条件に AND されていない）までは見抜けない＝score.py の数字と
まこさんの目が最終担保（既存 hook 群と同じ限界）。
"""
import sys, json, re, os

ADOPTED = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/adopted_strategies.md"
LEDGER = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/ledger.md"
ERRLOG = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/enforce_strategy_anchor_error.log"


def main():
    d = json.load(sys.stdin)
    if d.get("agent_type"):
        return 0  # サブエージェントは通す（デッドロック回避・他 hook と同型）
    ti = d.get("tool_input", {}) or {}
    fp = ti.get("file_path", "")
    if os.path.basename(fp) != "acceptance.md":
        return 0
    c = ti.get("content")
    if c is None:  # Edit＝現ファイルに old→new を適用した実効内容で判定
        old = ti.get("old_string")
        new = ti.get("new_string") or ""
        try:
            cur = open(fp).read()
        except Exception:
            cur = ""
        c = cur.replace(old, new) if old else (cur + new)
    if not c:
        return 0

    try:
        adopted = open(ADOPTED).read()
    except Exception:
        return 0
    m = re.search(r"STRATEGY_ANCHOR:\s*([^>]*?)-->", adopted)
    if not m:
        return 0
    anchors = {}
    for part in m.group(1).split(";"):
        mm = re.match(r"\s*([a-z0-9_]+)=([a-z_-]+),([a-z_-]+),([a-z_-]+)\s*$", part)
        if mm:
            anchors[mm.group(1)] = (mm.group(2), mm.group(3), mm.group(4))
    if not anchors:
        return 0

    # TARGET 行の token を優先（無ければ本文から）
    token = None
    tl = re.search(r"^TARGET:\s*(.+)$", c, re.M)
    hay = os.path.basename(tl.group(1).strip()) if tl else c
    for k in anchors:
        if re.search(r"(^|[^a-z0-9])" + re.escape(k) + r"([^0-9]|$)", hay):
            token = k
            break
    if token is None:
        return 0
    situ, direc, freq = anchors[token]
    if situ in ("none", "-") and not direc.endswith("_only"):
        return 0  # 係留の定義なし＝スルー

    def fail(msg, fix):
        sys.stderr.write("🔒 [戦略係留ゲート: %s=%s,%s,%s（台帳 STRATEGY_ANCHOR＝§1.2.1 の機械可読形）]\n" % (token, situ, direc, freq))
        sys.stderr.write("  " + msg + "\n  → " + fix + "\n")
        sys.stderr.write("  背景: E37 が両側化・レンジ判定撤去のドリフトで §1.2.1 違反のまま8イテレーション走った事案（ledger ARC11〜23・L-322）。\n")
        return 2

    anchor_str = "%s=%s,%s,%s" % (token, situ, direc, freq)
    if "★戦略照合" not in c:
        return fail("見出し「★戦略照合」がありません（戦略との照合を提示せず設計を書くのは禁止）。",
                    "acceptance に『## ★戦略照合（STRATEGY_ANCHOR: %s）』の節を立て、局面ゲート/方向機構の識別子を明記してください。" % anchor_str)
    if anchor_str not in c:
        return fail("台帳 STRATEGY_ANCHOR の逐語（%s）が再掲されていません。" % anchor_str,
                    "adopted_strategies.md のマーカーから逐語でコピーしてください（不一致＝台帳か理解が古い＝先に照合）。")

    # 経緯の係留（2026-07-04 まこさん承認＝「ledger 必読が部分読で通る」穴の対策）:
    #   対象戦略の ledger 直近 ARC エントリの iter 名の逐語引用を要求＝直近の経緯を特定・参照せずに設計を書けない。
    #   （ARC マーカーは ledger の各エントリ末尾に在る機械可読行＝token を含む最大 order のものが直近）
    try:
        led = open(LEDGER).read()
    except Exception:
        led = ""
    cand = []
    for mo in re.finditer(r'<!-- ARC order=(\d+) iter="([^"]+)".*?-->', led):
        if token in mo.group(0).lower():
            cand.append((int(mo.group(1)), mo.group(2)))
    if cand:
        latest = max(cand)[1]
        if latest not in c:
            return fail("対象戦略の ledger 直近エントリ（iter=\"%s\"）への言及がありません（経緯を読まない設計の禁止）。" % latest,
                        "ledger.md の該当エントリ（ARC order=%d）を Read で開き、acceptance に『直近 iter: %s（ledger 読了）』と逐語で書いてください。" % (max(cand)[0], latest))

    # DESIGN_CONTRACT の fenced json を抽出
    dc = ""
    dm = re.search(r"DESIGN_CONTRACT.*?```(?:json)?\s*\n(.*?)```", c, re.S)
    if dm:
        dc = dm.group(1)

    if situ not in ("none", "-"):
        bad = re.search(r"レンジ判定なし|レンジ判定は不要|暗黙に学ぶ|レンジゲートを外す|レンジゲート撤去|局面判定なし|レンジ判定を外す|局面判定を外す", c)
        if bad:
            return fail("局面(%s)の判定を外す/持たない趣旨の文言があります: 「%s」" % (situ, bad.group(0)),
                        "§1.2.1 の担当局面でだけエントリーする実装が必須です。局面を判定して入口を制約する機構を設計してください。")
        gm = re.search(r"GATE_IDENT\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", c)
        if not gm:
            return fail("局面(%s)ゲートの識別子宣言（GATE_IDENT=<列/関数名>）がありません。" % situ,
                        "入口を %s 判定で制約する実装機構の識別子を GATE_IDENT= で宣言してください（『検出器が暗黙に学ぶ』は不可）。" % situ)
        if gm.group(1) not in dc:
            return fail("GATE_IDENT=%s が DESIGN_CONTRACT の json 内にありません。" % gm.group(1),
                        "self_check_calls に %s を含めてください（require_design_contract_before_run が実行前に実装ソースと機械照合します）。" % gm.group(1))
    if direc.endswith("_only"):
        sm = re.search(r"SIDE_IDENT\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", c)
        if not sm:
            return fail("方向(%s)機構の識別子宣言（SIDE_IDENT=<識別子>）がありません。" % direc,
                        "%s を実装で保証する機構（例: short_only フラグ＝E36 が手本）の識別子を SIDE_IDENT= で宣言してください。" % direc)
        if sm.group(1) not in dc:
            return fail("SIDE_IDENT=%s が DESIGN_CONTRACT の json 内にありません。" % sm.group(1),
                        "self_check_calls に %s を含めてください。" % sm.group(1))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:
        # 無言死防止（pdca_mark 2026-07-03 事案と同型の対策）: エラーはログへ可視化し fail-open
        try:
            with open(ERRLOG, "a") as f:
                f.write(repr(e) + "\n")
        except Exception:
            pass
        sys.exit(0)
