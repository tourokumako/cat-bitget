#!/usr/bin/env python3
"""next_move.py — 工事の「いまの段」と「次の一手」と「まこさんにお願いする前の条件」を、実物のファイルから読んで出す。

まこさん指示（2026-10-10・逐語）
  「今の修正対応が一区切りついたら以下をやってほしい」（＝読む文書ではなく、いまの状態を実物から読んで「次の一手」を出すプログラム）
  「とにかく、設計書の元作成→確認→確認OK→設計書作成→監査依頼書の元作成→確認→確認OK→監査依頼書作成→監査結果が出る→
    監査結果確認→修正→修正後確認→OK→実装→実装の監査依頼書の元作成→確認→OK→監査依頼書作成→監査結果→監査結果確認→修正
    という一連の流れで、毎回同じミスをしてるから、どういうミスをしてるのか検証して、ミスをしないような仕組みを作る」

なぜ要るか（検証＝session_worklog_20261010.md の §42）
  順番は next_step.md に書いてあり、CC は読んでいた。それでも、段の中身（どの形で書くか・お願いの前に何を済ませるか）を
  知らずに進めて、まこさんの OK や承認の後にミスが分かった（7日ぶんの記録で、まこさんの手数が無駄になった・増えた回が11回）。
  ＝CC が手順を思い出して動くのをやめ、このプログラムが実物から読んで出す。

何をするか（★読むだけ・何も書かない）
  1. 工事の名前から、流れの印（読むもの宣言・工事のフォルダ・案の逐語・設計書・承認・当てた記録・監査依頼の手書きの文書・
     依頼書・見直し表・監査の結果・結果の修正）を、実物のファイルで1つずつ見る。
  2. 最初に「まだ」の印が、いまの段。その段の「次の一手」を出す。
  3. その段で まこさんにお願いする前に済ませる条件を、在る検査を呼んで ✅／❌ で出す。
  ★コマンドの文は、このプログラムに書いていない。各プログラムの頭の説明の行を、走るたびに読んで出す（usage）。
    読む先の行が無くなったら「使い方の行が見つからない」と出す（古い文を出さない）。

使い方
  python3 .claude/tools/next_move.py --work <工事名> [--session <セッションの id>]
    終了コード＝0（出した）／2（工事の名前が無い・工事のフォルダが見つからない）

限界（正直に）
  ・印は「ファイルが在るか・記録が在るか・検査が通るか」で見る。中身が正しいかは見ない（見直し表・監査・まこさんの目）。
  ・設計書の監査（設計書を監査に出す段）は、出すかどうかを まこさんが工事ごとに決めるので、事実だけを出し、段の判定には使わない。
  ・恒久71番＝読むためのプログラムなので、壊すプログラムと自己テストは付けない。走らせて確かめる。
  ・このプログラムを走らせるかどうかは、CC に掛かっている（止める hook は無い）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
STATE = ROOT / ".claude/state"
AUDITS = SDK / ".claude/audits"
ARCHIVE = SDK / ".claude/ratchet/acceptance_archive"
sys.path.insert(0, str(ROOT / ".claude/tools"))
sys.path.insert(0, str(ROOT / ".claude/hooks"))


def rel(p) -> str:
    try:
        return os.path.relpath(str(p), str(ROOT))
    except ValueError:
        return str(p)


def usage(path: str, needle: str) -> str:
    """プログラムの中から、needle を含む最初の行を読んで返す（コマンドの文を、このプログラムに書かないため）。"""
    p = ROOT / path
    try:
        for i, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if needle in ln:
                return f"{ln.strip().lstrip('#').strip()}（{path}:{i}）"
    except OSError:
        pass
    return f"（使い方の行が見つからない＝{path} の中に「{needle}」が無い。プログラムが変わった）"


def run(cmd: list, timeout: int = 120) -> tuple:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
        out = [x for x in ((r.stdout or "") + (r.stderr or "")).splitlines() if x.strip()]
        return r.returncode, (out[-1] if out else "")
    except Exception as e:                                   # noqa: BLE001
        return None, f"走らせられない（{e}）"


def facts(work: str, session: str) -> dict:
    """流れの印を、実物から読む。"""
    import gen_verbatim as gv
    import gen_audit_docs as gad
    import apply_audit_fix as aaf
    f: dict = {"work": work}
    f["wdir"] = gv.work_dir(work)
    f["working"] = f["wdir"].parent == gv.VERBATIM_DIR     # 作業中の置き場か（承認の後は控えの置き場に移る）
    # 読むもの宣言
    plan = STATE / "design_read_plan.md"
    ptext = plan.read_text(encoding="utf-8") if plan.is_file() else ""
    pm = re.search(r"^設計書:\s*(\S+)", ptext, re.M)
    om = re.search(r"^まこさんの OK:[ \t]*(.*)$", ptext, re.M)
    f["plan_work"] = pm.group(1) if pm else ""
    f["plan_ok"] = bool(pm and pm.group(1) == work and om and om.group(1).strip())
    # 工事のフォルダの中
    f["todo"] = (f["wdir"] / "やることの表.md").is_file()
    cc, mako = [], []
    for mp in sorted(f["wdir"].glob("*.meta.json")):
        try:
            who = set(json.loads(mp.read_text(encoding="utf-8")).get("who") or [])
        except (OSError, ValueError):
            continue
        (cc if who == {"CC"} else mako).append(mp.name[: -len(".meta.json")])
    f["okd"], f["req"] = cc, mako
    # 設計書と承認
    acc = STATE / "acceptance.md"
    atext = acc.read_text(encoding="utf-8") if acc.is_file() else ""
    f["acc_is_this"] = f'iter="{work}"' in atext
    arch = ARCHIVE / f"{work}.md"
    f["archive"] = arch if arch.is_file() else None
    mark = STATE / "acceptance.approved"
    approved = mark.read_text(encoding="utf-8").strip() if mark.is_file() else ""
    f["approved_now"] = f["acc_is_this"] and approved == hashlib.sha256(atext.encode("utf-8")).hexdigest()
    f["design"] = acc if f["acc_is_this"] else f["archive"]
    f["approved"] = bool(f["approved_now"] or f["archive"])
    # 実装の指示と、当てた記録
    n_fix, n_done = 0, 0
    if f["design"]:
        dtext = Path(f["design"]).read_text(encoding="utf-8")
        try:
            nums = {str(x.get("番号")) for x in aaf.read_design_fixes(dtext)}
        except Exception:                                    # noqa: BLE001
            nums = set()
        done = aaf.applied_keys()
        n_fix = len(nums)
        n_done = len([n for n in nums if (f"design:{work}", n) in done])
    f["n_fix"], f["n_done"] = n_fix, n_done
    # 監査（種類ごと）
    f["audit"] = {}
    inputs = AUDITS / "inputs"
    for kind, (label, suffix) in gad.KINDS.items():
        a: dict = {"label": label}
        hand = f["wdir"] / gad.HAND_MD.format(label=label)
        a["hand"] = hand if hand.is_file() else None
        task = work.replace("-", "_") + suffix
        cps = []
        for n in sorted(os.listdir(inputs)) if inputs.is_dir() else []:
            m = re.search(rf"_{re.escape(task)}_cp(\d+)_audit_request\.md$", n)
            if m:
                cps.append((int(m.group(1)), n))
        a["request"] = (inputs / max(cps)[1]) if cps else None
        a["cp"] = max(cps)[0] if cps else None
        a["report"] = None
        if a["cp"] is not None:
            reps = [n for n in os.listdir(AUDITS) if n.endswith(f"_cp{a['cp']}_audit_report.md")]
            a["report"] = (AUDITS / sorted(reps)[-1]) if reps else None
        a["pending"], a["undecided"] = [], []
        if a["report"]:
            try:
                fixes = aaf.read_fixes(a["report"].read_text(encoding="utf-8"))
            except Exception:                                # noqa: BLE001
                fixes = []
            done = aaf.applied_keys()
            for x in fixes:
                num = str(x.get("番号"))
                if x.get("状態") != "確定":
                    a["undecided"].append(num)
                elif (a["report"].name, num) not in done:
                    a["pending"].append(num)
        f["audit"][kind] = a
    # 案の試しの記録（このセッション）
    tp = STATE / "sessions" / (session or "_nosession") / "trial_last.json"
    f["trial"] = None
    if tp.is_file():
        try:
            t = json.loads(tp.read_text(encoding="utf-8"))
            f["trial"] = bool(t.get("ok")) and t.get("work") == work
        except (OSError, ValueError):
            f["trial"] = False
    return f


def steps(f: dict) -> list:
    """流れの段を順に並べる。1件＝(名前, 済んだか, 根拠, 次の一手の行の一覧)。"""
    work = f["work"]
    imp = f["audit"]["impl"]
    later = bool(f["design"])                                # 設計書が在る＝それより前の段は済んでいる
    s = []
    s.append(("1 読むもの宣言（まこさんの OK）",
              f["plan_ok"] or f["todo"] or later,
              f"読むもの宣言の「設計書:」＝{f['plan_work'] or '（無い）'}・この工事への OK＝{'在る' if f['plan_ok'] else '無い'}",
              [usage(".claude/hooks/require_read_plan_before_design.py", "--check"),
               usage(".claude/hooks/require_read_plan_before_design.py", "shasum -a 256")]))
    s.append(("2 設計書の元（やることの表）",
              f["todo"],
              f"工事のフォルダ＝{rel(f['wdir'])}・やることの表.md＝{'在る' if f['todo'] else '無い'}",
              [usage(".claude/tools/gen_acceptance.py", "手で書くのは、工事のフォルダの")]))
    s.append(("3 案 → まこさんの OK（案の逐語）",
              bool(f["okd"]) or later,
              f"まこさんが OK した CC の文の逐語＝{'・'.join(f['okd']) or '（無い）'}",
              [usage(".claude/hooks/trial_design.py", "使い方: python3 .claude/hooks/trial_design.py"),
               usage(".claude/hooks/require_trial_before_proposal.py", "HEAD_RE = "),
               usage(".claude/tools/gen_verbatim.py", "gen_verbatim.py --write <名前>")]))
    s.append(("4 設計書を作る",
              later,
              f"いまの設計書がこの工事か＝{'はい' if f['acc_is_this'] else 'いいえ'}・承認の控え＝{rel(f['archive']) if f['archive'] else '（無い）'}",
              [usage(".claude/tools/gen_acceptance.py", "--work <工事名> --write")]))
    s.append(("5 設計書の見直し → 承認（まこさんが打つ）",
              f["approved"],
              f"承認の記録＝{'在る' if f['approved'] else '無い'}",
              [usage(".claude/tools/gen_review.py", "抜けを見つけたまま渡さない"),
               usage(".claude/hooks/require_design_check_before_approval.py", "手で試す"),
               "承認のコマンドは、承認のプログラムの頭の「使い方」の行（.claude/hooks の approve_impl.sh の 10〜11行）。まこさんが打つ"]))
    s.append(("6 実装（設計書の実装の指示を当てる）",
              f["n_fix"] > 0 and f["n_done"] == f["n_fix"],
              f"実装の指示 {f['n_fix']} 件のうち、当てた記録に在る物 {f['n_done']} 件",
              [usage(".claude/tools/apply_audit_fix.py", "apply_audit_fix.py --design"),
               "当てた後＝当てた分をコミット（まこさんの OK）→ G2 → H2 → gen_regime_kb.py --write todo → 監査に出す前のチェック",
               usage(".claude/tools/pre_audit_check.py", "pre_audit_check.py --run"),
               usage(".claude/tools/pre_audit_check.py", "pre_audit_check.py --verify")]))
    s.append(("7 実装の監査の依頼書の元（手書きの文書）→ まこさんの OK",
              bool(imp["hand"]) or bool(imp["request"]),
              f"監査依頼の手書きの文書＝{rel(imp['hand']) if imp['hand'] else '（無い）'}",
              [usage(".claude/tools/gen_audit_docs.py", "HAND_FORM = "),
               usage(".claude/hooks/check_source_on_save.py", "手で確かめる")]))
    s.append(("8 実装の監査の依頼書を作る → 見直し表 → まこさんに渡す",
              bool(imp["request"]),
              f"依頼書＝{rel(imp['request']) if imp['request'] else '（無い）'}",
              [usage(".claude/tools/gen_audit_docs.py", "request-design <design|impl> --work"),
               usage(".claude/tools/gen_review.py", "--skeleton"),
               usage(".claude/tools/gen_review.py", "抜けを見つけたまま渡さない")]))
    s.append(("9 監査の結果を待つ",
              bool(imp["report"]),
              f"結果ファイル＝{rel(imp['report']) if imp['report'] else '（まだ無い）'}",
              ["結果ファイルができるまで待つ（別のセッションで監査中）。監査が見るファイルは書き替えない"]))
    left = len(imp["pending"]) + len(imp["undecided"])
    s.append(("10 監査の結果の確認 → まこさんが直す範囲を決める → 修正を当てる",
              bool(imp["report"]) and left == 0,
              f"状態が「確定」で まだ当てていない修正＝{'・'.join(imp['pending']) or '無い'}／「未決」「案が複数」の修正＝{'・'.join(imp['undecided']) or '無い'}",
              [usage(".claude/tools/apply_audit_fix.py", "apply_audit_fix.py --report"),
               "直す範囲（Critical だけか・Major もか・Minor もか）は、まこさんが結果ファイルを見て決める（恒久65番）",
               "当てた後＝当てた分をコミット（まこさんの OK）→ G2（gen_signal_families.py --verify）→ H2（leak_causality_diag.py）"
               "→ gen_regime_kb.py --write todo（当てた直後の照らしは、触った関数を設計書と比べるので、コミットしてから取り直す＝worklog 20261010 §47）"]))
    return s


def conditions(f: dict, idx: int) -> list:
    """いまの段で、まこさんにお願いする前に済ませる条件。1件＝(通ったか〔True／False／None＝走らせていない〕, 文)。"""
    out = []
    imp = f["audit"]["impl"]
    if idx == 2:                                              # 案 → OK
        if f["trial"] is None:
            out.append((False, "このセッションの案の試しの記録（trial_last.json）が無い＝案を出す前に、試しの設計書で全部の検査を通す"))
        else:
            out.append((f["trial"], "案の試しの記録（trial_last.json）が、この工事で「通った」になっている"))
        out.append((None, "案は、決まった見出し（【4-0 …】の形）の文の全文をチャットに出す（リンクだけにしない・案の後ろに報告を書かない）"
                          "＝設計書を作るプログラムは、やり取りの記録から読む"))
    if idx == 4:                                              # 設計書 → 承認
        rc, last = run(["python3", ".claude/tools/gen_review.py", "--check", ".claude/state/acceptance.md"])
        out.append((rc == 0, f"設計書の見直し表の照らし（gen_review.py --check）＝{last}"))
        out.append((None, "承認の前の検査（A1〜A14・仮当てを含む）は時間がかかるので、ここでは走らせていない。上の「手で試す」の行で走らせる"))
    if idx == 7 and imp["hand"]:                              # 手書きの文書は在る・依頼書は まだ＝OK をお願いする前
        import check_source_on_save as cs
        _what, bad, why = cs.check(imp["hand"], imp["hand"].read_text(encoding="utf-8"))
        if why:
            out.append((None, f"手書きの文書の検査を走らせられない＝{why}"))
        else:
            out.append((not bad, "手書きの文書を、依頼書を作るプログラムが読める" + ("" if not bad else "＝" + " ／ ".join(bad))))
    if idx == 8 and imp["request"]:                           # 依頼書は在る・結果は まだ＝まこさんに渡す前
        rc, last = run(["python3", ".claude/tools/gen_review.py", "--check", rel(imp["request"])])
        out.append((rc == 0, f"依頼書の見直し表の照らし（gen_review.py --check）＝{last}"))
        rc, last = run(["python3", ".claude/tools/pre_audit_check.py", "--verify"])
        out.append((rc == 0, f"監査に出す前のチェックの記録（pre_audit_check.py --verify）＝{last}"))
    if idx in (5, 9):                                         # 当てる前（段6＝設計書の指示・段10＝監査の修正）
        out += apply_preconditions(f)
    return out


def apply_preconditions(f: dict) -> list:
    """当てる前の条件（★2026-10-11・166回目・まこさん「修正対応をした状態で確認に出す」「OK」）。

    なぜ要るか＝型 D（承認の後・当てた後の手順を先に確かめなかった・worklog 20261010 §42 の表・§46・§47）＝当てた直後に走る照らしが
      止まり、承認の打ち直し・まこさんの端末の打ち直し・コミットの OK が増えた。当てる前に、当てた後に走る物と同じ判定を呼ぶ。
    判定は書き写さない（在る関数を呼ぶ）
      ①設計書と実装の照らし＝verify_design_contract.check（当てる道具 apply_audit_fix.run_commands が当てた直後に掛ける物と同じ）
      ②壊すプログラムの凍結と実物の一致＝run_breaks.check_frozen（記録を書く走り方 --out が止まる原因・§6 の251番）
      ③A12 の仮当ての控えが残っていない＝require_design_check_before_approval._a12_leftover（戻せる物は、その中で戻す・§6 の247・249番）
    ★当てた後の手順（当てた分のコミット → G2 → H2 → gen_regime_kb.py --write todo）は steps の次の一手に出す。"""
    import contextlib
    import io
    out = []
    design = f.get("design")
    if design:
        sys.path.insert(0, str(SDK / "scripts/priority_rebuild"))
        import verify_design_contract as vdc
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ok = bool(vdc.check(str(design)))
            last = [x for x in buf.getvalue().splitlines() if x.strip()]
            out.append((ok, "設計書と実装の照らし（verify_design_contract.check＝当てた直後に掛かる物と同じ）が いま通る"
                            + ("" if ok else "＝" + (last[-1] if last else "通らない"))))
        except Exception as e:                                # noqa: BLE001
            out.append((None, f"設計書と実装の照らしを走らせられない＝{type(e).__name__} {e}"))
    import run_breaks
    ng = run_breaks.check_frozen()
    out.append((not ng, "壊すプログラムの凍結と実物の一致（run_breaks.check_frozen）" + ("" if not ng else "＝" + " ／ ".join(ng[:3]))))
    import require_design_check_before_approval as rd
    left = rd._a12_leftover()
    out.append((not left, "A12 の仮当ての控えが残っていない（戻せる物は戻した）" + ("" if not left else "＝" + " ／ ".join(left[:3]))))
    return out


def main() -> int:
    argv = sys.argv[1:]
    work = argv[argv.index("--work") + 1] if "--work" in argv and argv.index("--work") + 1 < len(argv) else ""
    session = argv[argv.index("--session") + 1] if "--session" in argv and argv.index("--session") + 1 < len(argv) else ""
    if not work:
        print("❌ 工事の名前が要る（--work <工事名>）")
        return 2
    try:
        f = facts(work, session)
    except Exception as e:                                    # noqa: BLE001
        print(f"❌ 工事の印を読めない＝{type(e).__name__} {e}")
        return 2
    st = steps(f)
    cur = next((i for i, x in enumerate(st) if not x[1]), None)
    print(f"工事＝{work}（工事のフォルダ＝{rel(f['wdir'])}・{'作業中の置き場' if f['working'] else '承認の後の控えの置き場'}）")
    print("")
    print("流れの印（実物のファイルから読んだ）")
    for i, (name, done, ev, _n) in enumerate(st):
        head = "✅ 済" if done else ("▶ いまここ" if i == cur else "・ まだ")
        print(f"  {head}｜{name}｜{ev}")
    d = f["audit"]["design"]
    print(f"  （設計書の監査＝手書きの文書 {'在る' if d['hand'] else '無い'}・依頼書 {rel(d['request']) if d['request'] else '無い'}"
          f"・結果 {rel(d['report']) if d['report'] else '無い'}。出すかどうかは まこさんが工事ごとに決める）")
    print("")
    if cur is None:
        print("いまの段＝この工事の流れは、最後の段まで済んでいる")
        return 0
    name, _done, _ev, nxt = st[cur]
    print(f"いまの段＝{name}")
    print("次の一手（各プログラムの頭の説明の行を、いま読んだ物）")
    for ln in nxt:
        print(f"  ・{ln}")
    cs = conditions(f, cur)
    if cs:
        print("まこさんにお願いする前の条件")
        for ok, text in cs:
            print(f"  {'✅' if ok else ('❌' if ok is False else '・（走らせていない）')} {text}")
        if any(ok is False for ok, _t in cs):
            print("  ★❌ が在る間は、まこさんにお願いを出さない（全部 直してから、もう1回 このプログラムを走らせる）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
