#!/usr/bin/env python3
# check_all_before_handoff.py — まこさんに何かをお願いする前に、後で走る検査を全部 1回で走らせ、落ちた所を全部 一度に出す
#
# まこさん指示（2026-09-30・逐語）＝「すべて当てずっぽうで当たるまでやり続けるから遅いんだよ。わかる？」
#   「なんでそんな非効率なことやってんの？」「一回の確認ですべて完全に修正できるように強制しろ」
#   「承認後に修正が発生しないように、事前にミスが無いよう確認をしろ」「矮小化するな」
#
# なぜ要るか（worklog 20260930 §44〜§50）＝私は1つ出しては止められ、1つ直しては次で止められる、を繰り返した。
#   検査はどれも在ったのに、出す前に全部を1回で走らせていなかった。
#
# 何を走らせるか（直しかけの物＝git の差分と、まだ登録していない新しいファイルの全部）
#   ① .py ＝ py_compile。中に「--selftest」の口が在れば --selftest（終了コード 0 でなければ落ちる）
#   ② .sh ＝ bash -n（文法）
#   ③ 作った文書の照らし＝gen_hook_list.py --verify・tidy_next_step.py --verify
#   ④ 設計書（acceptance.md）＝承認の印と違う（承認の前）なら、gen_acceptance.py --verify と
#      承認の前の検査 require_design_check_before_approval.check_all（A1〜A13＝承認の後に起きること全部の仮通しを含む）
#      ★案の OK 待ち（_draft_*.txt が在り、試しの設計書が ok で設計書より新しい）のときは、どちらも試しの設計書で見る
#   ⑤ 案の試し＝.claude/state/_draft_*.txt が在れば、最後の trial_design の記録が ok か
# 結果を .claude/state/sessions/<セッション>/handoff_check.json に書く＝require_full_check_before_handoff が読む。
#
# 使い方: python3 .claude/hooks/check_all_before_handoff.py --session <id>
# 限界（正直に）＝検査が見る所しか見ない（中身の正しさは全行を読む私と まこさんの目）。検査が無い物は走らせられない。
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = ROOT + "/v3-bitget-api-sdk/bitget-python-sdk-api"
WATCH = (".claude/tools/", ".claude/hooks/", ".claude/breaks/", "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/")
SKIP_SELFTEST = {"check_all_before_handoff.py"}


def run(cmd, timeout=600, cwd=ROOT):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:                                   # noqa: BLE001
        return None, f"走らせられない（{e}）"


def tail(s, n=6):
    ls = [l for l in (s or "").splitlines() if l.strip()]
    return "\n".join("      " + l for l in ls[-n:])


def changed_files():
    rc, out = run(["git", "status", "--porcelain", "--untracked-files=all"])
    files = []
    for ln in (out or "").splitlines():
        p = ln[3:].strip().split(" -> ")[-1].strip('"')
        if p.endswith((".py", ".sh")) and any(p.startswith(w) for w in WATCH) and os.path.isfile(os.path.join(ROOT, p)):
            files.append(p)
    return sorted(set(files))


def check(session: str) -> dict:
    fails, done = [], []
    files = changed_files()
    for p in files:
        full = os.path.join(ROOT, p)
        if p.endswith(".py"):
            rc, out = run(["python3", "-m", "py_compile", full])
            done.append(f"py_compile {p}")
            if rc != 0:
                fails.append(f"py_compile が落ちる: {p}\n{tail(out)}")
                continue
            src = open(full, encoding="utf-8").read()
            if '"--selftest"' in src and os.path.basename(p) not in SKIP_SELFTEST:
                cwd = SDK if "priority_rebuild" in p else ROOT
                rc, out = run(["python3", full, "--selftest"], timeout=900, cwd=cwd)
                done.append(f"--selftest {p}")
                if rc != 0:
                    fails.append(f"自己テストが落ちる（rc={rc}）: {p}\n{tail(out)}")
        else:
            rc, out = run(["bash", "-n", full])
            done.append(f"bash -n {p}")
            if rc != 0:
                fails.append(f"bash の文法が落ちる: {p}\n{tail(out)}")
    for tool, arg in ((".claude/tools/gen_hook_list.py", "--verify"), (".claude/tools/tidy_next_step.py", "--verify")):
        if os.path.isfile(os.path.join(ROOT, tool)):
            rc, out = run(["python3", tool, arg])
            done.append(f"{arg} {tool}")
            if rc != 0:
                fails.append(f"作った文書の照らしが落ちる: {tool} {arg}\n{tail(out)}")
    acc = ROOT + "/.claude/state/acceptance.md"
    mark = ROOT + "/.claude/state/acceptance.approved"
    if os.path.isfile(acc):
        now = hashlib.sha256(open(acc, "rb").read()).hexdigest()
        approved = open(mark, encoding="utf-8").read().strip() if os.path.isfile(mark) else ""
        if now != approved:
            sys.path.insert(0, ROOT + "/.claude/hooks")
            import require_design_check_before_approval as rd
            # ★案の下書き（OK 待ち）が在り、その試しの設計書が設計書より新しいときは、試しの設計書を照らす
            #   （OK をいただいた後に設計書はその中身になる。古い設計書を照らすと、案の OK を待つ返信が出せない行き止まりになる）
            #   ★2026-09-30＝gen_acceptance.py --verify も同じ条件で分ける（直す前は、OK 待ちの案で直す前の
            #     工事のフォルダを本物の設計書で照らして止まった・fix_plan）。試しの設計書は trial_design.py が
            #     道具で作ったばかりで、その ok が記録に在る。
            trial = ROOT + "/.claude/state/_trial_acceptance.md"
            rp0 = os.path.join(ROOT, ".claude/state/sessions", session or "_nosession", "trial_last.json")
            use = acc
            if any(f.startswith("_draft_") and f.endswith(".txt") for f in os.listdir(ROOT + "/.claude/state")) \
                    and os.path.isfile(trial) and os.path.isfile(rp0) and json.load(open(rp0, encoding="utf-8")).get("ok") \
                    and os.path.getmtime(trial) >= os.path.getmtime(acc):
                use = trial
                done.append("（案の OK 待ち＝試しの設計書を照らした・作ったままかは試しの記録の ok で見た）")
            else:
                rc, out = run(["python3", ".claude/tools/gen_acceptance.py", "--verify"])
                done.append("gen_acceptance.py --verify")
                if rc != 0:
                    fails.append(f"設計書が道具の作ったままでない: gen_acceptance.py --verify\n{tail(out)}")
            a_bad, _b = rd.check_all(acc=use, transcript=None, split=True)
            done.append("承認の前の検査 A1〜A13")
            fails += [f"承認の前の検査: {x}" for x in a_bad]
    drafts = [f for f in os.listdir(ROOT + "/.claude/state") if f.startswith("_draft_") and f.endswith(".txt")]
    if drafts:
        rp = os.path.join(ROOT, ".claude/state/sessions", session or "_nosession", "trial_last.json")
        done.append("案の試しの記録")
        if not os.path.isfile(rp) or not json.load(open(rp, encoding="utf-8")).get("ok"):
            fails.append("案の下書きが在るのに、試しの設計書が検査を通っていない（trial_design.py を走らせる）")
    return {"time": time.time(), "at": datetime.datetime.now().isoformat(), "ok": not fails,
            "files": files, "done": done, "fails": fails}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--session", default="")
    a = p.parse_args()
    res = check(a.session)
    rp = os.path.join(ROOT, ".claude/state/sessions", a.session or "_nosession", "handoff_check.json")
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    json.dump(res, open(rp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"走らせた検査 {len(res['done'])} 件（直しかけの .py・.sh {len(res['files'])} 本）")
    for x in res["fails"]:
        print("   ❌ " + x)
    print(f"{'✅ 全部 通った' if res['ok'] else '❌ 落ちた ' + str(len(res['fails'])) + ' 件（全部 直してから、もう1回 走らせる）'}＝記録 {rp}")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
