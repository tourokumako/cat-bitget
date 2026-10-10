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
#   ⑥ 監査依頼の手書きの文書（工事のフォルダの「監査依頼の手書き（…）.md」）＝依頼書を作る道具と同じ読み方で照らす（書かない）
#   ⑦ 作った監査の依頼書（audits/inputs の *_audit_request.md）＝見直し表（gen_review.py --check）
#      ★⑥⑦は 2026-10-10 に足した。相手は、その監査の結果ファイルがまだ無い分だけ（audit_request_checks）
# 結果を .claude/state/sessions/<セッション>/handoff_check.json に書く＝require_full_check_before_handoff が読む。
#
# 使い方: python3 .claude/hooks/check_all_before_handoff.py --session <id>
# 限界（正直に）＝検査が見る所しか見ない（中身の正しさは全行を読む私と まこさんの目）。検査が無い物は走らせられない。
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = ROOT + "/v3-bitget-api-sdk/bitget-python-sdk-api"
WATCH =(".claude/tools/", ".claude/hooks/", ".claude/breaks/", "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/")
SKIP_SELFTEST = {"check_all_before_handoff.py"}


def _rd():
    """承認の前の検査（require_design_check_before_approval.py）を読み込んで返す（判定を書き写さず、同じ物を呼ぶため）。"""
    sys.path.insert(0, ROOT + "/.claude/hooks")
    import require_design_check_before_approval as rd
    return rd


def selftest_arg(name: str) -> str:
    """その .py に掛ける自己テストの口。承認の前の検査 A12 の一覧（A12_SELFTESTS）に同じ名前が在れば、その口を使う。

    ★2026-10-11（166回目・next_step の「お願いの前の検査の限りの直し」・worklog 20261010 §47）
      直す前＝engine_tuner_gen.py を書き替えている間は、全体の自己テスト（--selftest）を走らせていた。全体の自己テストは
        M2-E-8 で直すまで終了コード 1 のまま（T6・T29・T10・T12・T13）なので、必ず1件 落ちた。約9分 使って、新しい情報は出なかった。
      直した後＝A12 と同じ口（engine_tuner_gen.py は --selftest-extra-gate）を走らせる。落ちを許すかも A12 の許し
        （a12_fail_allowed＝gen_materials.py の T6 だけ）を呼ぶ＝判定は2か所に書き写さない。
      限り（正直に）＝engine_tuner_gen.py の全体の自己テストは、ここでは走らない（監査に出す前のチェック pre_audit_check.py は
        今までどおり走らせる）。A12 の一覧に無い .py は、今までどおり --selftest。"""
    for n, arg in _rd().A12_SELFTESTS:
        if n == name and arg.startswith("--selftest"):
            return arg
    return "--selftest"


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


def open_drafts(acc: str) -> list:
    """OK 待ちの案の下書き＝.claude/state/_draft_*.txt のうち、設計書（acc）より新しいものだけ。
    ★2026-10-01（まこさん指示「以下強制を早急に修正しろ」「強制の不具合で進行が妨げられている」）
      直す前＝_draft_*.txt が1本でも在れば「案の OK 待ち」と見た。OK をもらって設計書を作り、承認まで終わった
      工事の下書き（8本・2026-09-30〜10-01）が残っていたので、新しいセッションは全部「試しの設計書が検査を
      通っていない」で止まった（試しの記録はセッションごと＝新しいセッションには無い）。監査のセッション 7b5dce33 と
      このセッション 10472f77 で実測。
      直した後＝設計書より古い下書きは、もう設計書になった案なので数えない。"""
    st = ROOT + "/.claude/state"
    t_acc = os.path.getmtime(acc) if os.path.isfile(acc) else 0.0
    return [f for f in os.listdir(st) if f.startswith("_draft_") and f.endswith(".txt")
            and os.path.getmtime(os.path.join(st, f)) > t_acc]


def audit_request_checks() -> tuple:
    """⑥監査依頼の手書きの文書を、依頼書を作る道具と同じ読み方で照らす（依頼書は書かない）。⑦作った依頼書の見直し表を照らす。

    ★2026-10-10（165回目・まこさん「結論、どうしたらミスを無くせる？」「だから、どうすんの？」）
      直す前＝この2つは、まこさんに出した後に初めて検査が走った。
        ・手書きの文書に OK をいただいた後、依頼書を作る道具（gen_audit_docs.py の read_hand）が、出どころの番号で止めた。
        ・依頼書のリンクを返信に出した後、ターンの終わりの検査（require_read_used）が、見直し表が無いと止めた。
      直した後＝お願いの前に走らせるこの道具が、同じ判定を先に走らせる（判定は書き写さず、同じ道具を呼ぶ）。
    相手＝git に登録していない物・書き替えた物のうち、その監査の結果ファイルがまだ無い分だけ（済んだ監査の物は見ない）。
    戻り＝(落ちた所の一覧, 走らせた検査の一覧)。"""
    fails, done = [], []
    rc, out = run(["git", "-c", "core.quotepath=false", "status", "--porcelain", "--untracked-files=all"])
    paths = sorted({ln[3:].strip().split(" -> ")[-1].strip('"') for ln in (out or "").splitlines() if ln.strip()})
    aud = SDK + "/.claude/audits"
    inputs = os.path.join(aud, "inputs")
    if not os.path.isdir(inputs):
        return fails, done

    def answered(cp: str) -> bool:
        """その番号の監査の結果ファイルが、もう在るか。"""
        return any(n.endswith(f"_cp{cp}_audit_report.md") for n in os.listdir(aud))

    sys.path.insert(0, ROOT + "/.claude/tools")
    try:
        import gen_audit_docs as gad
    except Exception as e:                                   # noqa: BLE001
        return [f"依頼書を作る道具（gen_audit_docs.py）を読み込めない（{e}）"], done
    for p in paths:
        full = os.path.join(ROOT, p)
        name = os.path.basename(p)
        if not os.path.isfile(full):
            continue
        # ⑦ 作った依頼書＝見直し表が全部 埋まっているか（リンクで渡す前に要る）
        m = re.search(r"_cp(\d+)_audit_request\.md$", name)
        if m and os.path.dirname(full) == inputs and not answered(m.group(1)):
            rc, o = run(["python3", ".claude/tools/gen_review.py", "--check", p])
            done.append(f"gen_review.py --check {name}")
            if rc != 0:
                fails.append(f"監査の依頼書の見直し表が通らない（リンクで渡す前に作って埋める）: {p}\n{tail(o)}")
        # ⑥ 監査依頼の手書きの文書＝依頼書を作る道具が読めるか（まこさんに OK をお願いする前に要る）
        if "/verbatim/" in p and name.startswith("監査依頼の手書き（") and name.endswith("）.md"):
            work = os.path.basename(os.path.dirname(full))
            for kind, (label, suffix) in gad.KINDS.items():
                if name != gad.HAND_MD.format(label=label):
                    continue
                task = work.replace("-", "_") + suffix
                cps = [x.group(1) for x in (re.search(rf"_{re.escape(task)}_cp(\d+)_audit_request\.md$", n)
                                            for n in os.listdir(inputs)) if x]
                if cps and all(answered(c) for c in cps):
                    continue                                 # その工事の監査は、もう結果が出ている
                acc = ROOT + "/.claude/state/acceptance.md"
                arch = SDK + f"/.claude/ratchet/acceptance_archive/{work}.md"
                cur = open(acc, encoding="utf-8").read() if os.path.isfile(acc) else ""
                dp = None if f'iter="{work}"' in cur else (arch if os.path.isfile(arch) else None)
                done.append(f"監査依頼の手書きの文書の照らし（{work}・{label}）")
                try:
                    gad.build_design_src(kind, 0, work=work, design_path=dp, show_path=dp)
                except SystemExit as e:
                    fails.append(f"監査依頼の手書きの文書を、依頼書を作る道具が読めない（OK をお願いする前に直す）: {p}\n      {e}")
                except Exception as e:                       # noqa: BLE001
                    fails.append(f"監査依頼の手書きの文書の照らしが走らない: {p}\n      {type(e).__name__} {e}")
    return fails, done


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
                arg = selftest_arg(os.path.basename(p))          # ★2026-10-11＝A12 と同じ口（上の selftest_arg）
                rc, out = run(["python3", full, arg], timeout=900, cwd=cwd)
                done.append(f"{arg} {p}")
                if rc != 0 and not _rd().a12_fail_allowed(os.path.basename(p), rc, out):
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
            if open_drafts(acc) \
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
    drafts = open_drafts(acc)                               # ★2026-10-01＝設計書より新しい下書きだけ（上の open_drafts）
    if drafts:
        rp = os.path.join(ROOT, ".claude/state/sessions", session or "_nosession", "trial_last.json")
        done.append("案の試しの記録")
        if not os.path.isfile(rp) or not json.load(open(rp, encoding="utf-8")).get("ok"):
            fails.append("案の下書きが在るのに、試しの設計書が検査を通っていない（trial_design.py を走らせる）")
    f6, d6 = audit_request_checks()                         # ★2026-10-10＝⑥監査依頼の手書きの文書 ⑦依頼書の見直し表
    fails += f6
    done += d6
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
