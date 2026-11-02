#!/usr/bin/env python3
"""check_one_path.py — ToDo の「作った後の確認」を、走らせて 通る・通らない・未作 で出す。

まこさんの許可（2026-11-02・ToDo の207番の宣言に「ok」・恒久の決まり78番）。
まこさん指示（逐語 2026-11-02）「todoには、機能構築後の確認を毎回入れるようにしてほしい」。

なぜ要るか
  確認が ToDo の文だけだと、走らせずに進める。試験ごとに同じ形で打てる口を1本にする。
  検索は、まず1通りの条件（req_trace_src.json の「通す条件」）で通す。

使い方
  python3 .claude/tools/check_one_path.py --test T05       # 試験1件
  python3 .claude/tools/check_one_path.py --todo 171       # その ToDo に結び付けた試験の全部
  python3 .claude/tools/check_one_path.py --work <工事名>   # その工事の ToDo の試験の全部（元データの「工事の名前」）
  python3 .claude/tools/check_one_path.py --all            # 全部の試験
  python3 .claude/tools/check_one_path.py --selftest

結果
  ✅ 通る／❌ 通らない（理由つき）／⬜ 未作（測る処理がまだ無い。作る ToDo の番号つき）。
  ★未作は通らないと数える。全部 通ったときだけ終了コード 0。
  試験を作る ToDo で、下の CHECKS に関数を足す。

限り（正直に）
  ①通ることは、完成の判定ではない（恒久の決まり64番）。試験が要件の行を測っているかは監査が見る。
  ②T04 は監査に出す前のチェックの結果の記録（--verify）を見る。走らせ直すのは pre_audit_check.py --run。
  ③T02 が呼ぶ数える道具は、ss_outside_probe.json と直す相手の一覧 fix_inventory_20261024.md を作り直す（行番号が新しくなる）。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
SCRIPTS = SDK / "scripts" / "priority_rebuild"
SRC = ROOT / ".claude" / "state" / "req_trace_src.json"
PASS, FAIL, TODO = "通る", "通らない", "未作"


def load_src(path: pathlib.Path = SRC) -> dict:
    if not path.exists():
        raise SystemExit(f"[check_one_path] 元データが無い: {path}（fail-closed）")
    return json.loads(path.read_text(encoding="utf-8"))


def _run(cmd: list, timeout: int = 300) -> tuple:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr).strip()


def _reader():
    sys.path.insert(0, str(SCRIPTS / "indicators"))
    import indicators as ind                             # 読む口（indicators.json を開くのは、読む口だけ）
    return ind, ind.load()


def t02(src: dict) -> tuple:
    """数える道具が0件を出す。"""
    rc, out = _run([sys.executable, str(ROOT / ".claude/state/indicator_review/ss_outside_probe.py")])
    if rc != 0:
        return FAIL, f"数える道具が止まった（rc={rc}）"
    hits = json.loads((ROOT / ".claude/state/indicator_review/ss_outside_probe.json").read_text(encoding="utf-8"))
    n = hits["total"]                                    # 数える道具自身の合計（完成＝0）
    return (PASS, "0件") if n == 0 else (FAIL, f"{n} 件が記録の外に在る")


def t04(src: dict) -> tuple:
    """監査に出す前のチェックの結果の記録が、新しく全部 rc=0。"""
    rc, out = _run([sys.executable, str(ROOT / ".claude/tools/pre_audit_check.py"), "--verify"])
    last = out.splitlines()[-1][:100] if out else ""
    return (PASS, last) if rc == 0 else (FAIL, last)


def _blank(v) -> bool:
    return v in (None, "", [], {}) or (isinstance(v, str) and v.startswith("まだ決めていない"))


def t05(src: dict) -> tuple:
    """1通りの条件の分の、空の要素が0件。"""
    ind, r = _reader()
    path = src["通す条件"]
    style, side, scene = path["売買スタイル"], path["玉の向き"], path["場面"]
    miss = []
    for nm in path["指標"]:
        if nm in r.records["部品の記録"]:
            kind, th = "部品の記録", "閾値"
        elif nm in r.records["指標の記録"]:
            kind, th = "指標の記録", "閾値の範囲"
        else:
            miss.append(f"{nm}＝記録が無い")
            continue
        if not r.is_on(nm):
            miss.append(f"{nm}＝オフ")
        role = r.element(nm, "教科書の役割", kind)
        if _blank(role) or (isinstance(role, dict) and _blank(role.get("区分"))):
            miss.append(f"{nm}＝役割")
        for ax in r.axes(nm) or []:
            if _blank((ax.get("代表の値") or {}).get(style)):
                miss.append(f"{nm}＝{ax.get('名前')} の代表の値")
            if _blank(ax.get("範囲")):
                miss.append(f"{nm}＝{ax.get('名前')} の範囲")
        if _blank(r.element(nm, th, kind)):
            miss.append(f"{nm}＝{th}")
        uses = [u for u in r.records["使い方の記録"]
                if nm in (u.get("指す物") or {}).values() and u.get("玉の向き") in (side, "両方")
                and scene in json.dumps(u.get("場面と型"), ensure_ascii=False)]
        if not uses:
            miss.append(f"{nm}＝{scene}・{side}の使い方")
    return (PASS, "空の要素 0件") if not miss else (FAIL, f"空の要素 {len(miss)} 件: " + "・".join(miss))


def t11(src: dict) -> tuple:
    """案を作るプログラムの乱数の呼び出しが0件。"""
    n = len(re.findall(r"\brng\.", (SCRIPTS / "engine_tuner_gen.py").read_text(encoding="utf-8")))
    return (PASS, "0件") if n == 0 else (FAIL, f"engine_tuner_gen.py に乱数の呼び出しが {n} 件")


def t15(src: dict) -> tuple:
    """いまの形の設計書の監査の問い（_design_five_questions の中）に、目標の問いと確認の問いが在る。
    ★文が在ることしか見ない＝依頼書を実際に作って見るのは、設計書の監査を出す最初の工事。"""
    txt = (ROOT / ".claude/tools/gen_audit_docs.py").read_text(encoding="utf-8")
    m = re.search(r"def _design_five_questions.*?(?=\ndef )", txt, flags=re.S)
    body = m.group(0) if m else ""
    need = ["目標に近づく工事になっているか", "作った後の確認は、要件の行を測っているか"]
    lack = [x for x in need if x not in body]
    return (PASS, "問いが2つとも在る") if not lack else (FAIL, "問いが無い: " + "・".join(lack))


def t19(src: dict) -> tuple:
    """読む口の自己テスト（選べる値に無い値と、決まりに合わない値で止まる）が通る。"""
    rc, out = _run([sys.executable, str(SCRIPTS / "indicators" / "indicators.py"), "--selftest"])
    last = out.splitlines()[-1][:100] if out else ""
    return (PASS, last) if rc == 0 else (FAIL, last)


def t28(src: dict) -> tuple:
    """確認の無い機能の ToDo で、対応表の道具が止まる形が動いている。"""
    tool = str(ROOT / ".claude/tools/gen_req_trace.py")
    rc1, out1 = _run([sys.executable, tool, "--selftest"])
    rc2, out2 = _run([sys.executable, tool, "--check"])
    if rc1 != 0:
        return FAIL, "自己テストが落ちた"
    if rc2 != 0:
        return FAIL, out2.splitlines()[0][:100]
    return PASS, out2.splitlines()[0][:100]


# 測る処理が在る試験。無い試験は「未作」と出す（作る ToDo で足す）
CHECKS = {"T02": t02, "T04": t04, "T05": t05, "T11": t11, "T15": t15, "T19": t19, "T28": t28}


def run_test(no: str, src: dict) -> tuple:
    tests = src.get("試験") or {}
    if no not in tests:
        raise SystemExit(f"[check_one_path] 元データの「試験」に無い: {no}（fail-closed）")
    fn = CHECKS.get(no)
    if fn is None:
        return TODO, f"測る処理がまだ無い（作る ToDo＝{(src.get('試験を作る番号') or {}).get(no) or '未定'}）"
    return fn(src)


def report(nos: list, src: dict) -> int:
    marks = {PASS: "✅", FAIL: "❌", TODO: "⬜"}
    count = {PASS: 0, FAIL: 0, TODO: 0}
    for no in nos:
        st, why = run_test(no, src)
        count[st] += 1
        print(f"{marks[st]} {no} {st}｜{src['試験'][no]['中身']}｜{why}")
    print(f"通る {count[PASS]} 件・通らない {count[FAIL]} 件・未作 {count[TODO]} 件（全 {len(nos)} 件）")
    return 0 if count[PASS] == len(nos) else 1


def tests_of_todo(no: str, src: dict) -> list:
    got = (src.get("確認") or {}).get(str(no))
    if not got:
        why = (src.get("確認が要らない行") or {}).get(str(no))
        raise SystemExit(f"[check_one_path] ToDo {no} に確認が無い" + (f"（要らない理由＝{why}）" if why else "（fail-closed）"))
    return list(got)


def selftest() -> int:
    ok = True
    def t(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  {'✅' if cond else '❌'} {name}")
    src = {"試験": {"T00": {"中身": "見本"}}, "試験を作る番号": {"T00": "1"}, "確認": {"1": ["T00"]}, "確認が要らない行": {"2": "文書"}}
    t("S1 測る処理の無い試験は未作", run_test("T00", src)[0] == TODO)
    t("S2 未作だけなら終了コード 1", report(["T00"], src) == 1)
    t("S3 ToDo の試験を読む", tests_of_todo("1", src) == ["T00"])
    for name, fn in (("S4 確認が要らない行は止まる", lambda: tests_of_todo("2", src)),
                     ("S5 一覧に無い試験は止まる", lambda: run_test("T99", src))):
        try:
            fn()
            t(name, False)
        except SystemExit:
            t(name, True)
    print("selftest:", "ok" if ok else "NG")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--test", default="")
    p.add_argument("--todo", default="")
    p.add_argument("--work", default="")
    p.add_argument("--all", action="store_true")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    src = load_src()
    if a.test:
        return report([a.test], src)
    if a.todo:
        return report(tests_of_todo(a.todo, src), src)
    if a.work:
        nums = (src.get("工事の名前") or {}).get(a.work)
        if not nums:
            raise SystemExit(f"[check_one_path] 元データの「工事の名前」に無い: {a.work}（fail-closed）")
        return report(list(dict.fromkeys(x for n in nums for x in tests_of_todo(n, src))), src)
    if a.all:
        return report(list(src["試験"]), src)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
