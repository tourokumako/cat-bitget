#!/usr/bin/env python3
# trial_design.py — 案に OK をいただく前に、その案から設計書を試しに作り、承認の前の検査を全部 かける
#
# まこさん指示（2026-09-30・逐語）＝「なんども同じ確認してるけど、一回の確認で全部のミスを見つけられるようにしろ」
#   「すべて当てずっぽうで当たるまでやり続けるから遅すぎるんだよ」「一回の確認ですべて正確に修正できるように強制しろ」
#
# なぜ要るか（worklog 20260930 §44〜§49）＝私は案を出してから OK をいただき、そのあと初めて道具で設計書を作って
#   検査にかけていた。だから OK のたびに次の穴（入れ忘れの節・古いまま残った節・当たらない件）が見つかり、
#   作り直しと OK と承認が何回も要った。
# 何をするか＝①工事のフォルダを一時の置き場に写す ②下書きの案を「まこさんが OK した CC の案」として一番新しい時刻で足す
#   ③gen_acceptance.py の write で一時の設計書を作る ④承認の前の検査（require_design_check_before_approval.py の
#   check_all＝A1〜A11）をかける ⑤--stale に渡した古い事実の語が設計書に残っていないかを数える
#   ⑥結果を記録（.claude/state/sessions/<セッション>/trial_last.json）に書く＝require_trial_before_proposal が読む。
#   本物の設計書・工事のフォルダには何も書かない。
#
# 使い方: python3 .claude/hooks/trial_design.py --work <工事名> --draft <下書き.txt> [--stale 語1,語2,…] [--session <id>]
#   一時の設計書は .claude/state/_trial_acceptance.md に置く（Read で全行 開いて確かめる）。
#
# 限界（正直に）＝検査が見る形しか見ない（中身の正しさは全行を読む私とまこさんの目）。古い事実の語は私が選ぶ。
import argparse
import datetime
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
OUT = ROOT / ".claude/state/_trial_acceptance.md"
SESS = ROOT / ".claude/state/sessions"


def record_path(sid: str) -> Path:
    return SESS / (sid or "_nosession") / "trial_last.json"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--work", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--stale", default="")
    p.add_argument("--session", default=os.environ.get("CLAUDE_SESSION_ID", ""))
    # ★2026-10-08（160回目・まこさん OK の案 2a）＝--fast は A12（仮当て・12〜17分）を飛ばし、ほかの段（約25秒）を全部 出す。
    #   159回目は、A12 以外の段（A2・A14 ほか）で落ちる直しを、A12 込みの長い検査で1つずつ見つけた（7回中 長い回3回）。
    #   使い方＝--fast が0件になってから、--fast を付けずに1回だけ走らせる。記録は trial_fast_last.json に書く
    #   （案を出す前の検査 require_trial_before_proposal・check_all_before_handoff が読む trial_last.json は書かない＝A12 抜きで通さない）。
    p.add_argument("--fast", action="store_true")
    a = p.parse_args()
    draft = Path(a.draft).read_text(encoding="utf-8")
    sys.path.insert(0, str(ROOT / ".claude/tools"))
    sys.path.insert(0, str(ROOT / ".claude/hooks"))
    import gen_verbatim as gv
    import gen_acceptance as ga
    import require_design_check_before_approval as rd
    tmp = Path(tempfile.mkdtemp())
    try:
        src = gv.work_dir(a.work)
        dst = tmp / "verbatim" / a.work
        shutil.copytree(src, dst)
        (dst / "zz_trial_draft.txt").write_text(draft, encoding="utf-8")
        (dst / "zz_trial_draft.meta.json").write_text(json.dumps(
            {"who": ["CC"], "time": ["9999-12-31T23:59:59"], "uuids": [], "drop": [], "sha256": gv._sha(draft)},
            ensure_ascii=False), encoding="utf-8")
        real_verify = gv.verify
        gv.verify = lambda n, d=None: (True, "") if str(n).endswith("zz_trial_draft") else real_verify(n, d)
        gv.VERBATIM_DIR, gv.ARCHIVE_DIR = tmp / "verbatim", tmp / "none"
        ga.WORK = a.work
        try:
            rc = ga.write(dest=OUT)
        except SystemExit as e:
            print(f"❌ 設計書を作れません＝{e}")
            rc = 2
        a_bad = []
        stale_hits = []
        if rc == 0:
            a_bad, _b = rd.check_all(acc=str(OUT), transcript=None, split=True, trial=not a.fast)
            text = OUT.read_text(encoding="utf-8")
            body = text.split("<!-- ACC_SOURCE_END -->", 1)[-1]
            for w in [x for x in a.stale.split(",") if x.strip()]:
                for i, ln in enumerate(body.splitlines(), 1):
                    if w in ln:
                        stale_hits.append(f"「{w}」: {ln.strip()[:120]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = rc == 0 and not a_bad and not stale_hits
    for x in a_bad:
        print("   ❌ " + x)
    for x in stale_hits:
        print("   ❌ 古い事実の語が残る " + x)
    rp = record_path(a.session)
    if a.fast:
        rp = rp.with_name("trial_fast_last.json")
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps({"time": datetime.datetime.now().isoformat(), "work": a.work, "ok": ok,
                              "draft": draft, "a_bad": a_bad, "stale": stale_hits}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    if a.fast:
        print(f"{'✅' if ok else '❌'} 速い段だけ（A12 の仮当ては走らせていない）＝A群 {len(a_bad)} 件・古い語 {len(stale_hits)} 件。"
              f"記録＝{rp}。0件になったら --fast を付けずに1回だけ走らせる")
        return 0 if ok else 1
    print(f"{'✅' if ok else '❌'} 試しの設計書＝{OUT}（A群 {len(a_bad)} 件・古い語 {len(stale_hits)} 件）。全行を Read で開いてから案を出す")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
