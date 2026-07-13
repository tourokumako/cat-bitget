#!/usr/bin/env python3
# enforce_ml_wiring.py — PreToolUse on Bash（2026-07-13 まこさん指示・機械学習の不正防止の【2枚目＝実行前コード照合】）
#
# 位置づけ: 1枚目 enforce_ml_honesty（doc 層＝acceptance の宣言を書かせ P0〜P4 の構造インチキを弾く）の限界
#   ＝「宣言に嘘を書けばすり抜ける」を、実行前の実装コード照合で塞ぐ2枚目。まこさん設計の「ML が飾りでないかを
#   DESIGN_CONTRACT で実行前にコード照合」の実体。
#
# 何を照合するか（機械で robust にできる範囲）:
#   acceptance.md の機械可読 ML_CONTRACT（fenced json）= {impl_file, self_report, predict_symbol, decision_symbols}。
#   自己申告が『本物のML設計』の戦略を python で実行する前に、実装を AST 解析し
#     ① predict_symbol（ML 予測を入れる変数）が実際に代入されている ② 実装に .predict( 由来の予測がある
#     ③ decision_symbols（入口/出口/レバーの決定）が多段依存で predict_symbol に配線されている
#   を検査。配線が無い＝ML 予測が決定に流れていない＝飾り(疑似ML)なのに『本物』を名乗る詐称 → 実行ブロック(exit 2)。
#   自己申告が『疑似ML』なら配線は要求しない（正直な自己申告・1枚目が『機械学習と呼ぶな』を担保）。
#
# ★限界（正直に・隠さない）: これはコードの「配線」までを機械照合する。教師ラベルの中身（取り逃し[機会損失]を
#   見るか・目的と一致するか）の意味判定は AST では不可能＝【3枚目＝非同型 Web Claude レビュー】＋まこさんの目で補う。
#   多段依存の追跡も max_depth で有限（関数境界を跨ぐ dataflow は追い切れない）＝配線を跨がせる巧妙な偽装は残る。
#   ＝この2枚目単独でも「本物のML」は保証しない。1枚目(doc)＋2枚目(配線)＋3枚目(Web レビュー)＋まこさんの目 の重ね。

import sys, os, json, re, ast

BASE = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api"
PR = os.path.join(BASE, "scripts", "priority_rebuild")
ACC = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md"


def assign_map(tree):
    m = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            names = set()
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Name):
                    names.add(sub.id)
                elif isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                    names.add(sub.func.id)
            for t in node.targets:
                if isinstance(t, ast.Name):
                    m.setdefault(t.id, set()).update(names)
    return m


def depends_on(amap, target, source, max_depth=6):
    seen, frontier = set(), {target}
    for _ in range(max_depth):
        nxt = set()
        for sym in frontier:
            deps = amap.get(sym, set())
            if source in deps:
                return True
            for d in deps:
                if d not in seen:
                    seen.add(d)
                    nxt.add(d)
        frontier = nxt
        if not frontier:
            break
    return False


def extract_ml_contract(md_text):
    idx = md_text.find("ML_CONTRACT")
    if idx < 0:
        return None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", md_text[idx:], re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def resolve_impl(impl_file):
    if os.path.isabs(impl_file):
        return impl_file if os.path.exists(impl_file) else None
    for cand in (os.path.join(PR, impl_file), os.path.join(PR, os.path.basename(impl_file))):
        if os.path.exists(cand):
            return cand
    return None


def run_pys(cmd):
    return set(os.path.basename(m.group(1))
               for m in re.finditer(r'python[0-9.]*\s+(?:-[A-Za-z]\S*\s+)*([^\s|&;><]+\.py)', cmd))


def check(contract, impl_path):
    """返り値: (ok, messages)。"""
    report = str(contract.get("self_report", ""))
    if "疑似" in report:
        return True, ["[INFO] ML_CONTRACT self_report=疑似ML＝ML 予測を決定に使わない（配線照合は要求しない・正直な自己申告）"]
    if "本物" not in report:
        return False, [f"[FAIL] ML_CONTRACT self_report は『本物のML設計』か『疑似ML』を明記（現在='{report}'）"]
    predict = contract.get("predict_symbol", "")
    decisions = contract.get("decision_symbols", []) or []
    if not predict or not decisions:
        return False, ["[FAIL] 本物を名乗るなら predict_symbol と decision_symbols の宣言が必須"]
    try:
        src = open(impl_path, encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception as e:
        return False, [f"[FAIL] 実装を解析できない: {impl_path} ({e})"]
    amap = assign_map(tree)
    ok, msg = True, []
    if predict not in amap:
        ok = False
        msg.append(f"[FAIL] 予測変数 '{predict}' が実装で代入されていない（ML 予測が存在しない＝飾り）")
    if "predict(" not in src:
        ok = False
        msg.append("[FAIL] 実装に .predict( 由来の予測が無い（学習器の予測が使われていない＝飾り）")
    for dsym in decisions:
        if depends_on(amap, dsym, predict):
            msg.append(f"[PASS] 決定 '{dsym}' が ML 予測 '{predict}' に配線されている（飾りでない）")
        else:
            ok = False
            msg.append(f"[FAIL] 決定 '{dsym}' が ML 予測 '{predict}' に配線されていない＝飾り(疑似ML)なのに『本物』を名乗る詐称")
    return ok, msg


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if d.get("agent_type"):
        sys.exit(0)
    cmd = (d.get("tool_input", {}) or {}).get("command", "") or ""
    pys = run_pys(cmd)
    if not pys:
        sys.exit(0)
    try:
        contract = extract_ml_contract(open(ACC, encoding="utf-8").read())
    except Exception:
        contract = None
    if not contract:
        sys.exit(0)  # ML_CONTRACT が無い＝ML を名乗らない戦略の実行は本 hook の対象外
    impl_file = contract.get("impl_file", "")
    if os.path.basename(impl_file) not in pys:
        sys.exit(0)  # 実行しているのは contract の対象実装ではない
    impl_path = resolve_impl(impl_file)
    if not impl_path:
        sys.stderr.write(f"🔒 [ML 配線ゲート] ML_CONTRACT の impl_file が見つからない: {impl_file}\n")
        sys.exit(2)
    ok, msg = check(contract, impl_path)
    if not ok:
        sys.stderr.write("🔒 [ML 配線ゲート・2枚目] ML の予測が決定に配線されていません＝飾り(疑似ML)なのに『本物のML』を名乗る詐称（まこさん 2026-07-13）\n")
        for m in msg:
            sys.stderr.write("  " + m + "\n")
        sys.stderr.write(
            "  → ML 予測を実際に入口/出口/レバーの決定に使うよう実装を直すか、self_report を『疑似ML』に正す。\n"
            "     限界: 配線までを機械照合＝教師の中身(取り逃しを見るか)は非同型 Web Claude レビュー＋まこさんの目で補う。\n"
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
