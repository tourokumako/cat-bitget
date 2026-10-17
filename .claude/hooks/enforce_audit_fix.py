#!/usr/bin/env python3
# enforce_audit_fix.py — hook 12 の本体（2026-09-16 まこさん承認・設計書 audit-autofix-apply-20260916）
#
# まこさんの指示（逐語 2026-09-14）
#   「今後はそのテンプレ以外では監査結果を書けないように強制してほしい」
#   流れの「強制hook作成✕３ … 3.監査結果のテンプレから自動生成で修正する」の3本目。
#
# まこさんが決めた線引き（2026-09-16・逐語「１の線引は提案のものでOK」）
#   1. 監査結果には、直す相手のファイルの名前が書いてある。
#   2. その修正を当て終わるまでは、CC はそのファイルを手で直せない（プログラムだけが直せる）。
#   3. 当て終わったら、そのファイルは普通に直せる。
#
# 何を見るか
#   ①`SDK/.claude/audits/*_audit_report.md` を全部 読む（作業場 *_work の中は除く＝試し用）。
#   ②状態が「確定」で、まだ当たっていない修正（＝直す前の文字が実物にまだ在る）の
#     「対象のファイル」を集める。
#   ③Write・Edit・MultiEdit の相手がその一覧に在れば止める。
#   ④当て終わった（直す前の文字が実物に無い）ファイルは、一覧に入らない＝普通に直せる。
#   ⑤★2026-09-30（設計書 point1-one-way-20260930-2・まこさん決定「案A」）＝当てる道具が当てた記録
#     （SDK/.claude/audits/applied_fixes.json・apply_audit_fix.applied_keys）に在る修正は、当て済みとして飛ばす。
#     なぜ＝文字が残っているかだけで見ると、監査の直しを当てた後に別の工事でその文字を変えると、
#     そのファイルがずっと止まった（worklog 20260930 §20・§22）。記録に無い修正は今までどおり文字で見る。
#
# 通すもの
#   ・当てる道具（apply_audit_fix.py）からの書き込み＝この hook は Bash を見ないので、そもそも通る。
#   ・監査と関係のないファイル（一覧に無いもの）。
#   ・守りの仕組み（hook・道具・承認の印）＝当てる道具が書かない相手なので、私が直す。
#
# 解除: 無し（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」で全廃）。
#
# 限界（正直に）
#   ①別の名前のファイルに書く道は塞げない（止めるのは「対象のファイル」の欄に在るパスだけ）。
#   ②Bash で書き替える道は見ない（土台ゲートと hook 10・11 が別に見る）。
#   ③この hook 自体を書き換えれば無効にできる（明示の違反・git diff には出る）。
#   ④監査結果が増えるほど、読む本数が増える（いまは全部で数十本・読むだけなので速い）。
#
# 試し方: python3 .claude/hooks/enforce_audit_fix.py --try <hook の入力の json を書いたファイル>

import glob
import json
import os
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = os.path.join(ROOT, "v3-bitget-api-sdk", "bitget-python-sdk-api")
REPORTS = os.path.join(SDK, ".claude", "audits", "*_audit_report.md")
sys.path.insert(0, os.path.join(ROOT, ".claude", "tools"))


def _applied(f: dict, before: str, text: str) -> bool:
    """当て終わっているか＝当てる道具（apply_audit_fix.apply_one）と同じ形で見る（2026-09-24 に直した）。

    直す前＝「直す前の文字が実物に無い」だけで見ていた。「足す文字」の修正は当てた後も
    直す前の文字が残るので、永久に「まだ」になり、対象のファイルを手で直せなくなった（CP41 で実測）。
    """
    plans = f.get("4つ目") or []
    if not plans:
        return before not in text
    for _a, kind, body in plans:
        if kind == "足す文字" and (before + body) in text:
            return True
        if kind == "直した後の文字" and (body in text or before not in text):
            return True
        if kind == "消す文字" and before not in text:
            return True
    return False


def pending() -> dict:
    """まだ当たっていない修正の「対象のファイル」→ [(監査結果, 修正の番号), …]。"""
    try:
        import apply_audit_fix as a
    except Exception:                                        # noqa: BLE001
        return {}                                            # 道具が読めないときは止めない（fail-open）
    out = {}
    done = a.applied_keys()                                  # ★当てた記録（案A）
    # ★2026-09-30（設計書 point2-design-to-impl-20260930・2点目）＝承認済みの設計書に実装の指示（4-20）が在る間は、
    #   その設計書の TARGET と NEW_FILE を CC の手で直させない（実装は当てる道具だけが書く）。
    #   直しが要るときは、案の【4-20】に足して設計書を作り直し、承認を通して当てる。
    try:
        dtext = open(a.DESIGN, encoding="utf-8").read()
        if a.approved_ok(a.DESIGN)[0] and a.read_design_fixes(dtext):
            key = a.design_key(dtext, a.DESIGN)
            # ★2026-09-30（138回目・まこさん指示「早く直して」）＝実装の指示を全件 当て終わった（当てた記録に在る）
            #   設計書は守らない＝まこさんが決めた線引き 3「当て終わったら、そのファイルは普通に直せる」に合わせた。
            #   直す前は当て終わった後も守り続け、次の工事の試しの検査（A2）が必ず落ちた（next_step の知っている弱い所6）。
            nums = {str(f.get("番号")) for f in a.read_design_fixes(dtext)}
            if not all((key, n) in done for n in nums):
                for p in a.design_targets(dtext):
                    out.setdefault(p, []).append((key, "（設計書の実装の指示）", None))
    except Exception:                                        # noqa: BLE001
        pass                                                 # 設計書が読めないときは止めない（fail-open・上と同じ）
    for rep in glob.glob(REPORTS):
        try:
            text = open(rep, encoding="utf-8").read()
            fixes = a.read_fixes(text)
        except Exception:                                    # noqa: BLE001
            continue
        for f in fixes:
            if f.get("状態") != "確定":
                continue
            if (os.path.basename(rep), str(f.get("番号"))) in done:
                continue                                     # 当てる道具が当てた記録に在る＝当て済み
            rel, before = f.get("対象のファイル"), f.get("直す前の文字")
            if not rel or not before or before.strip() == "なし":
                continue
            # ★2026-09-30（設計書 audit-fix-tools-target-20260930）＝承認と TARGET がそろった道具のファイルは、
            #   当てる道具が書ける＝当てる前は CC の手の直しを止める（まこさん指示 2026-09-30「手書きをせざるを得ないもの以外は、すべて自動生成」）。
            if a.never_write(rel) and not a.tool_target_ok(rel):
                continue                                     # 守りの仕組み＝当てる道具が書かない＝CC が直す
            path = a.repo_path(rel)
            if not os.path.isfile(path):
                continue
            try:
                text = open(path, encoding="utf-8").read()
            except Exception:                                # noqa: BLE001
                continue
            if _applied(f, before, text):
                continue                                     # 当て終わっている＝もう止めない
            out.setdefault(os.path.realpath(path), []).append(
                (os.path.basename(rep), f.get("番号"), before))
    return out


def _spans(text: str, s: str) -> list:
    """text の中で s が出てくる範囲 [(始め, 終わり), …]。"""
    out, i = [], text.find(s) if s else -1
    while i >= 0:
        out.append((i, i + len(s)))
        i = text.find(s, i + 1)
    return out


def blocking(hits: list, fp: str, tool: str, ti: dict, text: str = None) -> list:
    """★2026-10-17（184回目・まこさん「CC の案：要として、不具合1と2を直す」「修正進めて良い」）＝止める理由のうち、
    この書き込みに当たる物だけを返す。Write＝ファイル全体を書き替えるので全部。Edit・MultiEdit＝直す文字（old_string）の
    範囲が、当たっていない修正の「直す前の文字」の範囲と重なる（触れるも含む）物だけ。設計書の実装の指示（直す前の文字が
    None）は、いままでどおり全部。直す文字がファイルに見つからない・ファイルが読めないときは、止める側に倒す（全部）。
    直す前は、ファイル全体を止めたので、修正と関係のない行の直しまで止めた（30日で7回）。"""
    if tool == "Write" or not hits:
        return hits
    olds = [e.get("old_string") or "" for e in ti.get("edits") or []] if tool == "MultiEdit" else [ti.get("old_string") or ""]
    if text is None:
        try:
            text = open(fp, encoding="utf-8").read()
        except Exception:                                    # noqa: BLE001
            return hits
    if not olds or any(not o for o in olds):
        return hits
    mine = [sp for o in olds for sp in _spans(text, o)]
    if not mine:
        return hits
    out = []
    for h in hits:
        before = h[2]
        theirs = _spans(text, before) if before is not None else []
        if before is None or not theirs or any(a0 <= b1 and b0 <= a1 for a0, a1 in mine for b0, b1 in theirs):
            out.append(h)                                    # 重なる・触れる・直す前の文字が見つからない＝止める側
    return out


def selftest() -> int:
    """★2026-10-17＝blocking を見本の文と見本の止める理由で試す（本物の監査結果は読まない・何も書かない）。"""
    text = "一行目\n直す前の文字\n三行目\n"
    hit = [("x_cp1_audit_report.md", "1", "直す前の文字")]
    design = [("design:x", "（設計書の実装の指示）", None)]
    E = lambda o: {"old_string": o}                        # noqa: E731
    cases = [
        ("H1 Write → 止まる", blocking(hit, "", "Write", {}, text), True),
        ("H2 Edit の直す文字が「直す前の文字」と重なる → 止まる", blocking(hit, "", "Edit", E("前の文字\n三"), text), True),
        ("H3 Edit の直す文字が別の行（重ならない）→ 通る", blocking(hit, "", "Edit", E("一行"), text), False),
        ("H4 Edit の直す文字が「直す前の文字」のすぐ後ろに触れる → 止まる", blocking(hit, "", "Edit", E("\n三行目"), text), True),
        ("H5 MultiEdit の1つが重なる → 止まる",
         blocking(hit, "", "MultiEdit", {"edits": [E("一行"), E("直す前")]}, text), True),
        ("H6 設計書の実装の指示（直す前の文字が None）→ Edit でも止まる", blocking(design, "", "Edit", E("一行"), text), True),
        ("H7 直す文字がファイルに無い → 止まる（止める側）", blocking(hit, "", "Edit", E("どこにも無い"), text), True),
    ]
    ng = 0
    for nm, got, want in cases:
        ok = bool(got) == want
        ng += not ok
        print(f"  {'✅' if ok else '❌'} {nm}")
    print(f"自己テスト {len(cases) - ng}/{len(cases)}")
    return 1 if ng else 0


def main(raw: str) -> int:
    try:
        data = json.loads(raw)
    except Exception:                                        # noqa: BLE001
        return 0
    if data.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        return 0
    fp = str((data.get("tool_input") or {}).get("file_path") or "")
    if not fp:
        return 0
    hit = blocking(pending().get(os.path.realpath(fp)) or [], fp, data.get("tool_name", ""), data.get("tool_input") or {})
    if not hit:
        return 0
    e = sys.stderr
    print("🔒 [hook 12・監査の修正は当てる道具でしか書けない] このファイルには、"
          "まだ当てていない監査の修正が在ります"
          "（まこさん指示 2026-09-14「テンプレ以外では書けないように強制」）。", file=e)
    for rep, num, _b in hit[:8]:
        print(f"   ❌ {rep} の 修正 {num}", file=e)
    print("   ＝先に当ててください（設計書の実装の指示なら python3 .claude/tools/apply_audit_fix.py --design）:", file=e)
    print("     python3 .claude/tools/apply_audit_fix.py --report <上の監査結果> "
          "--severity <まこさんが決めた重さ>", file=e)
    print("   ★当て終わると、このファイルは普通に直せます（まこさん決定 2026-09-16 の線引き）。", file=e)
    return 2


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    if len(sys.argv) == 3 and sys.argv[1] == "--try":
        sys.exit(main(open(sys.argv[2], encoding="utf-8").read()))
    sys.exit(main(sys.stdin.read()))
