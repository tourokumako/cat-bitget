#!/usr/bin/env python3
# require_design_check_before_approval.py — 承認をお願いする前に、承認のプログラムの止まり所を全部 確かめる
#
# まこさん指示（2026-09-21・逐語）＝
#   「いかなる理由があっても、承認でミスをすることは許さない。強制で承認ミスを防ぎ、
#     何度も同じ承認をさせることをしないでほしい。その承認を突破するために、試す方法は
#     ランダムは不可とする。一回で改善できる状態にしろ。」「いいよ。修正しろ」
#
# なぜ要るか（実測 2026-09-21・worklog 20260921 §4-7）＝
#   直す前の hook（.sh だけ）は、承認のプログラム approve_impl.sh の止まり所のうち、
#   1つ目（pre_audit_check.py --check-design）しか見ていなかった。
#   CC は「不足0件」を「承認が通る」と読み、宣言（# EXPECT_MSG:）の足りない既存の
#   壊すプログラム b41 を完成の条件に載せたまま承認をお願いした。
#   承認は最後の止まり所（run_breaks.py --design）で取り消され、まこさんに無駄に打たせた。
#
# 何をするか＝approve_impl.sh が止まる（または承認を取り消す）場所を、上から順に、
#   **同じ道具を呼んで**確かめる。不足は全部 集めて一度に出す（1件ずつ止めない）。
#   A群＝その場で走らせる（読むだけ・何も書かない）。
#     A1 設計書が在るか（approve_impl.sh:16）
#     A2 pre_audit_check.py --check-design（:32）
#     A3 凍結の前の検査＝approve_impl.sh の1つ目の python の囲みを、書き先だけ一時置き場に
#        替えて そのまま走らせる（:72-288＝contract_for_freeze・resolve_spec_list ほか）
#     A4 控えを残す所（:301-315）＝ARC の目印・控えの置き場に書けるか・git が無視しないか・index.lock
#     A5 承認の記録の鍵（:347-366）＝approve_design.sh が書く鍵と check_approval が読む鍵が同じか
#     A6 run_breaks.py --count-targets --design（:386）
#     A7 run_breaks.py --parse-only（:401 の入口＝表が読めるか・列がずれていないか）
#     A8 表に載っている既存の壊すプログラムの宣言を expect_of で読む（:401＝159番の STOP）
#     A10 完成の条件のコマンドが、SDK を作業場所にしても開けるか（:472 の _run＝cwd=SDK・L-614）
#   B群＝時間がかかるので、その場では走らせない。やり取りの記録（harness が書く）に、
#        設計書・壊すプログラム・TARGET より新しい実行の結果が在るかを見る。
#     B1 表に載っている既存の壊すプログラムが、--measure-only で「✅ 期待どおり」だったか
#     B2 その行の「その数字を出したコマンド」を走らせて、止められずに終わったか
#     ＝どちらかが欠けると、承認しても行が「未着手」のまま残り、もう1回 承認が要る。
#   ★止め方＝A群が1件でも在れば止める。B群だけのときは、返信に「承認は もう1回 要ります」の
#     文字が在れば通す（実装の前の承認では B群が残るのが当たり前なので、行き止まりを作らない。
#     その代わり、承認が もう1回 要ることを まこさんに先に伝えさせる）。
#
# 使い方:
#   Stop hook        : bash require_design_check_before_approval.sh（標準入力＝hook の json）
#   書いた直後に出す : python3 <この .py> --after-write   （止めない・出すだけ）
#   手で試す         : python3 <この .py> --try [--design <設計書>] [--transcript <記録>]
#
# 限界（正直に）:
#   ・承認のお願いを「approve_impl.sh」の文字を出さずに書けば当たらない。
#   ・設計書の中身が正しいかは見ない。中身は まこさんの目と監査。
#   ・B群は記録の形を見る＝コマンドを `| tail` でつないだ実行や、裏で走らせた実行は、
#     落ちていても「止められずに終わった」に見える。
#   ・approve_impl.sh の形が変わって A3 の囲みを取り出せなくなったら、不足として止める
#     （黙って飛ばさない）。そのときは この hook を直す。
#   ・cp や git add がその瞬間に失敗する類（ディスクが一杯 など）は先に分からない。
#   ・この hook 自身を書き換えれば無効にできる（差分は git に出る）。
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import time

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK = ROOT + "/v3-bitget-api-sdk/bitget-python-sdk-api"
ACC = ROOT + "/.claude/state/acceptance.md"
APPROVE = ROOT + "/.claude/hooks/approve_impl.sh"
PRE = ROOT + "/.claude/tools/pre_audit_check.py"
RUNB = ROOT + "/.claude/tools/run_breaks.py"
ARC_DIR = SDK + "/.claude/ratchet/acceptance_archive"
TABLE = ROOT + "/.claude/state/design_approved.json"
# ★お願いの形＝まこさんに打ってもらうコマンド（bash …/approve_impl.sh）。
#   名前だけ（説明の文の中の approve_impl.sh）では当てない＝説明のたびに止めないため。
WORD_RE = re.compile(r"bash\s+\S*approve_impl\.sh")
SAY = "承認は もう1回 要ります"          # B群だけが残るとき、返信に在れば通す文字


def _run(cmd, stdin=None, timeout=90):
    try:
        r = subprocess.run(cmd, input=stdin, capture_output=True, text=True,
                           timeout=timeout, cwd=ROOT)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:                                   # noqa: BLE001
        return None, f"走らせられませんでした（{e}）"


def _tail(out, n=25):
    ls = [l for l in (out or "").splitlines() if l.strip()]
    return "\n".join("        " + l for l in ls[-n:])


# ── A群 ─────────────────────────────────────────────────────────────
def a2_check_design(acc):
    rc, out = _run(["python3", PRE, "--check-design", acc])
    if rc == 0:
        return []
    return [f"A2 設計書の門の検査（approve_impl.sh:32）が rc={rc}:\n{_tail(out, 60)}"]


def a3_freeze_block(acc):
    try:
        src = open(APPROVE, encoding="utf-8").read()
    except Exception as e:                                   # noqa: BLE001
        return [f"A3 承認のプログラムを読めません（{e}）"]
    m = re.search(r'python3 - "\$LIST" "\$SPEC_OUT" "\$FROZEN_OUT" <<\'PY\'\n(.*?)\nPY\n', src, re.S)
    if m is None:
        return ["A3 承認のプログラムから、凍結の前の検査の囲みを取り出せません"
                "（approve_impl.sh の形が変わった＝この hook を直してください。黙って飛ばしません）"]
    with tempfile.TemporaryDirectory() as td:
        rc, out = _run(["python3", "-", acc, td + "/spec_lists.json",
                        td + "/impl_functions_frozen.json"], stdin=m.group(1))
    if rc == 0:
        return []
    return [f"A3 凍結の前の検査（approve_impl.sh:72-288＝ここで落ちると承認が取り消される）が rc={rc}:\n"
            f"{_tail(out)}"]


def a4_archive(md):
    bad = []
    m = re.search(r'iter="([^"]*)"', md)
    if m is None or not m.group(1):
        return ["A4 設計書に ARC の目印（iter=\"…\"）が無い＝控えの名前がハッシュ値になる（恒久の決まり §0-2 の2）"]
    safe = m.group(1).replace(" ", "_").replace("/", "_")
    if not os.path.isdir(ARC_DIR) or not os.access(ARC_DIR, os.W_OK):
        bad.append(f"A4 控えの置き場に書けません: {ARC_DIR}")
    if os.path.exists(ROOT + "/.git/index.lock"):
        bad.append("A4 .git/index.lock が在る＝git add が失敗して承認が取り消される（approve_impl.sh:311）")
    if os.path.exists(f"{ARC_DIR}/{safe}.md"):
        seq = 1
        while os.path.exists(f"{ARC_DIR}/{safe}.{seq:02d}.md"):
            seq += 1
        keep = f"{ARC_DIR}/{safe}.{seq:02d}.md"
        rc, _ = _run(["git", "-C", ROOT, "check-ignore", "-q", keep])
        if rc == 0:
            bad.append(f"A4 前の版の控え（{os.path.basename(keep)}）を git が無視する設定＝"
                       "git add が失敗して承認が取り消される（approve_impl.sh:311）")
    return bad


def a5_approval_key(acc):
    sys.path.insert(0, SDK + "/scripts/priority_rebuild")
    try:
        import verify_design_contract as v                    # noqa: E402
    except Exception as e:                                   # noqa: BLE001
        return [f"A5 照合の道具を読み込めません（{e}）＝承認の直後の確認（approve_impl.sh:360）が落ちる"]
    bad = []
    if os.path.abspath(v._DESIGN_APPROVED) != os.path.abspath(TABLE):
        bad.append("A5 承認の記録の置き場が、書く側（approve_design.sh）と読む側（check_approval）で違う")
    wrote = os.path.join(os.path.realpath(os.path.dirname(acc)), os.path.basename(acc))
    if os.path.abspath(acc) != wrote and acc == ACC:
        bad.append(f"A5 承認の記録の鍵が食い違う（書く側 {wrote} ／読む側 {os.path.abspath(acc)}）")
    return bad


def a6_count_targets(acc):
    rc, out = _run(["python3", RUNB, "--count-targets", "--design", acc])
    if rc == 0:
        return []
    return [f"A6 壊すプログラムの探す文字の数え（approve_impl.sh:386＝落ちると承認が取り消される）が rc={rc}:\n"
            f"{_tail(out, 12)}"]


def a7_parse_only(acc):
    rc, out = _run(["python3", RUNB, "--parse-only", "--design", acc])
    if rc == 0:
        return []
    return [f"A7 完成の条件の表を読めません（approve_impl.sh:401 が rc=2 で承認を取り消す）:\n{_tail(out, 12)}"]


def a8_expect(md):
    sys.path.insert(0, ROOT + "/.claude/tools")
    try:
        import run_breaks as rb                               # noqa: E402
    except Exception as e:                                   # noqa: BLE001
        return [f"A8 壊すプログラムを走らせる道具を読み込めません（{e}）"], [], None
    bad, exist = [], []
    for r in rb.parse_table(md):
        if not r.get("script"):
            continue
        if not (rb.BREAKS_DIR / r["script"]).exists():
            continue
        exist.append(r)
        _exp, _means, why, _msg = rb.expect_of(r["script"])
        if why:
            bad.append(f"A8 完成の条件 #{r['no']} の既存の壊すプログラムの宣言を読めません"
                       f"（approve_impl.sh:401 が承認を取り消す・159番）: {why}")
    return bad, exist, rb


def a9_contract_full(acc):
    """A9 設計↔実装ゲートと同じ照合A〜D（verify_design_contract.py <設計書>）が通るか。

    ★2026-09-24（監査 CP42 の B3）＝承認のプログラムとこの検査は、照合A〜D を1回も走らせていなかった。
      設計書 impl-instruction-apply-20260924 は承認③まで通ったのに照合C（selftest の must_use）が落ち、
      CC はその道具を直下からの --selftest 以外で走らせられない状態になった（ゲートが止める）。
    ★実装の前の承認では照合が落ちるのが当たり前なので、TARGET に git の差分が在るとき（実装の途中・後）だけ見る。
      呼ぶ関数がまだ無いときの落ち方（配線が無い・関数が無い）も、実装の前として見ない。
    """
    md = open(acc, encoding="utf-8").read()
    targets = [x.strip() for t in re.findall(r"^TARGET:\s*(.+)$", md, re.M) for x in t.split(",") if x.strip()]
    changed = False
    for t in targets:
        for base in (ROOT, SDK):
            pth = os.path.join(base, t)
            if os.path.exists(pth):
                rc_g, _o = _run(["git", "diff", "--quiet", "HEAD", "--", pth])
                changed = changed or rc_g == 1
    if not changed:
        return []
    # ★2026-09-30（設計書 point1-one-way-20260930-2 の W-4・5 の決めたこと3）＝照合の道具は直さず、
    #   凍結として「この設計書の impl_functions」を引数で渡して、照合A〜D をこの場で走らせる。
    #   直す前＝道具をそのまま走らせたので、前の承認の凍結と比べ、次の承認で直す予定の関数まで
    #   「凍結に無い関数を直した」と落ち、承認の前に止まった（worklog 20260930 §18）。
    #   承認の後は、設計↔実装ゲートが本物の凍結と比べる（今までどおり）。
    sys.path.insert(0, SDK + "/scripts/priority_rebuild")
    here = os.getcwd()
    try:
        import verify_design_contract as vdc                  # noqa: E402
        os.chdir(SDK)                                         # 道具を CLI で走らせるときと同じ作業場所
        contract = vdc.extract_contract(open(acc, encoding="utf-8").read())
        if not contract:
            return ["A9 設計書に DESIGN_CONTRACT が無い＝設計↔実装ゲートが .py を走らせられない"]
        src = open(vdc._resolve_impl(acc, contract["impl_file"]), encoding="utf-8").read()
        design = {k: v for k, v in (contract.get("impl_functions") or {}).items()}
        msgs = (vdc.check_impl_functions(contract, acc, frozen=design)
                + vdc.check_must_use(contract, src, acc)
                + vdc.check_spec_lists(contract, src))
    except Exception as e:                                   # noqa: BLE001
        return [f"A9 照合の道具を走らせられません（{e}）"]
    finally:
        os.chdir(here)
    msgs = [m for m in msgs if "実装にその関数が無い" not in m]   # 実装の前として見ない（今までどおり）
    # ★2026-09-30（設計書 point1-one-way-20260930-3 の W-4）＝承認の瞬間に approve_impl.sh が作る
    #   「もう汚れていた .py」の一覧（<iter>.dirty.json）を、承認の前はこの場で同じ作り方で作り、
    #   照合A(双方向) からその一覧のファイルを外す（承認の後のゲートも外すので、承認で消える不足）。
    #   直す前＝一覧がまだ無い承認の前に、別の工事の直しかけ（enforce_no_false_claim.py）で止まった（worklog 20260930 §26）。
    if not vdc.dirty_baseline(acc):
        _rc, _st = _run(["git", "-C", ROOT, "status", "--porcelain"])
        _watch = ("scripts/priority_rebuild/", ".claude/hooks/", ".claude/tools/")   # approve_impl.sh の _watch と同じ
        _dirty = {_l[3:].strip().split(" -> ")[-1] for _l in (_st or "").splitlines()
                  if _l[3:].strip().endswith(".py") and any(_w in _l for _w in _watch)}
        msgs = [m for m in msgs
                if not (m.startswith("A(双方向) ") and m[len("A(双方向) "):].split(":")[0] in _dirty)]
    if not msgs:
        return []
    return ["A9 照合A〜D（設計↔実装ゲートが .py を走らせる前に掛けるもの）が落ちる"
            "＝承認しても、CC はその .py を走らせられない:\n" + _tail("\n".join(msgs), 20)]


def a10_cmd_cwd(md):
    """A10 完成の条件のコマンドが、承認のプログラムの作業場所（SDK）で開けるか（approve_impl.sh の _run＝cwd=SDK）。

    ★2026-09-24（監査 CP42 の B3・L-614）＝設計書 impl-instruction-apply-20260924 は、完成の条件のコマンドを
      直下からの相対で書いたので、承認②で条件のコマンドが rc=2 になり、行が済にならず、承認が1回 増えた。
      直下に在って SDK に無いパスを書いた行だけを止める（新しく作るファイルは止めない）。
    """
    m = re.search(r"<!-- ACCEPT_TABLE_START -->(.*?)<!-- ACCEPT_TABLE_END -->", md, re.S)
    bad = []
    for cmd in re.findall(r"`(python3 [^`]+)`", m.group(1) if m else ""):
        py = next((t for t in cmd.split()[1:] if t.endswith(".py")), "")
        if py and not py.startswith("/") and os.path.isfile(os.path.join(ROOT, py)) \
                and not os.path.isfile(os.path.join(SDK, py)):
            bad.append(f"A10 完成の条件のコマンド `{cmd}` の {py} は直下からの相対＝承認のプログラムは"
                       "SDK を作業場所にして走らせるので開けず rc=2 になり、行が済にならない（L-614）")
    return bad


# ── B群（やり取りの記録を見る）──────────────────────────────────────
def _load_rows(path):
    try:
        return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception:                                        # noqa: BLE001
        return []


def _ts(row):
    t = row.get("timestamp") or ""
    try:
        return datetime.datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
    except Exception:                                        # noqa: BLE001
        return 0.0


def _bash_runs(rows):
    """[(時刻, コマンド, 結果の文字, 止められたか)] を返す（Bash の呼び出しだけ）。"""
    res = {}
    for r in rows:
        if r.get("type") != "user":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                c = b.get("content")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
                res[b.get("tool_use_id")] = (c or "", bool(b.get("is_error")))
    out = []
    for r in rows:
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                got = res.get(b.get("id"))
                if got is None:
                    continue
                out.append((_ts(r), (b.get("input") or {}).get("command") or "", got[0], got[1]))
    return out


def b_runtime(md, exist, rb, transcript):
    if not exist:
        return []
    m = re.search(rb.AT_START, md, re.S | re.M)
    line_of = {}
    for ln in (m.group(1).splitlines() if m else []):
        s = ln.strip()
        if s.startswith("|"):
            cells = [c.strip() for c in s.replace("\\|", "\x00").strip("|").split("|")]
            if cells:
                line_of[cells[0]] = (s, cells)
    targets = [x.strip() for t in re.findall(r"^TARGET:\s*(.+)$", md, re.M) for x in t.split(",")]
    newest = os.path.getmtime(ACC) if os.path.exists(ACC) else 0.0
    for t in targets:
        for base in (ROOT, SDK):
            p = os.path.join(base, t)
            if os.path.exists(p):
                newest = max(newest, os.path.getmtime(p))
    runs = _bash_runs(_load_rows(transcript)) if transcript else []
    bad = []
    for r in exist:
        p = str(rb.BREAKS_DIR / r["script"])
        need = max(newest, os.path.getmtime(p))
        s, cells = line_of.get(r["no"], ("", []))
        if "**未着手**" not in s and "承認のときに機械が2つとも測った" not in s:
            continue                                         # 承認のプログラムが測り直さない行
        ok1 = any(ts >= need and not err and "run_breaks.py" in cmd and "--measure-only" in cmd
                  and re.search(r"期待どおり[^\n]*" + re.escape(r["script"]), out)
                  for ts, cmd, out, err in runs)
        if not ok1:
            bad.append(f"B1 完成の条件 #{r['no']}＝{r['script']} を、設計書・壊すプログラム・TARGET の"
                       "いちばん新しい書き替えより後に測った記録が無い（または期待どおりでない）。"
                       "このまま承認すると行が「未着手」のまま残り、もう1回 承認が要ります。\n"
                       "        走らせる: python3 .claude/tools/run_breaks.py --design "
                       ".claude/state/acceptance.md --measure-only")
        mc = re.search(r"`([^`]+)`", cells[2] if len(cells) > 2 else "")
        cmd_want = mc.group(1).strip() if mc else ""
        if not (cmd_want.startswith("python3 ") or cmd_want.startswith("bash ")):
            bad.append(f"B2 完成の条件 #{r['no']} の「その数字を出したコマンド」を読み取れない"
                       "（`python3 …` か `bash …` を ` で囲む）＝承認しても済にならない")
            continue
        ok2 = any(ts >= need and not err and cmd_want in cmd for ts, cmd, out, err in runs)
        if not ok2:
            bad.append(f"B2 完成の条件 #{r['no']} のコマンドを、いちばん新しい書き替えより後に走らせて"
                       "止められずに終わった記録が無い＝承認しても済にならず、もう1回 承認が要ります。\n"
                       f"        走らせる（SDK の置き場で）: {cmd_want}")
    return bad


def check_all(acc=ACC, transcript=None, split=False):
    """不足の一覧を返す。split=True なら（A群＝承認が止まる, B群＝もう1回 承認が要る）に分けて返す。"""
    if not os.path.isfile(acc):
        a1 = [f"A1 設計書がありません: {acc}（approve_impl.sh:16）"]
        return (a1, []) if split else a1
    md = open(acc, encoding="utf-8").read()
    bad = []
    bad += a2_check_design(acc)
    bad += a3_freeze_block(acc)
    bad += a4_archive(md)
    bad += a5_approval_key(acc)
    bad += a6_count_targets(acc)
    bad += a7_parse_only(acc)
    bad += a9_contract_full(acc)
    bad += a10_cmd_cwd(md)
    b8, exist, rb = a8_expect(md)
    bad += b8
    bad_b = b_runtime(md, exist, rb, transcript) if rb is not None else []
    return bad + bad_b if not split else (bad, bad_b)


def _turn_text(data):
    """このターンの CC の返信の文字（まこさんの最後の発言より後の本文を全部つないだもの）。"""
    parts = [json.dumps(data, ensure_ascii=False)]
    path = data.get("transcript_path") or ""
    if not path:
        return parts[0]
    sys.path.insert(0, ROOT + "/.claude/hooks")
    try:
        from enforce_chat_writing import last_chat_text      # noqa: E402
        _text, uid = last_chat_text(path)
    except Exception:                                        # noqa: BLE001
        return parts[0]
    rows = _load_rows(path)
    start = next((i for i, r in enumerate(rows) if uid and r.get("uuid") == uid), -1)
    for r in rows[start + 1:]:
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text") or "")
    return "\n".join(parts)


def _print(bad, head):
    e = sys.stderr
    print(head, file=e)
    print(f"   不足 {len(bad)} 件（全部 一度に出しています。全部 直してから、もう一度 確かめてください）:", file=e)
    for i, b in enumerate(bad, 1):
        print(f"   {i}. {b}", file=e)
    print("   確かめ直す: python3 .claude/hooks/require_design_check_before_approval.py --try", file=e)


def main(argv):
    if "--try" in argv or "--after-write" in argv:
        acc = argv[argv.index("--design") + 1] if "--design" in argv else ACC
        tr = argv[argv.index("--transcript") + 1] if "--transcript" in argv else None
        t0 = time.time()
        bad = check_all(acc, tr)
        if bad:
            _print(bad, "📋 [承認の前の検査] 承認のプログラムの止まり所を、上から全部 確かめました。")
        else:
            print("✅ [承認の前の検査] 承認のプログラムの止まり所 A1〜A8・B1・B2 は全部 通ります（不足0件）。")
        print(f"   （かかった時間 {time.time() - t0:.1f} 秒）")
        # --after-write（PostToolUse）は、不足が在るとき 2 で終わる＝書いたものは取り消されない
        #   （道具はもう走り終わっている）。2 にするのは、不足の一覧を CC の画面に出すため。
        if "--after-write" in argv:
            return 2 if bad else 0
        return 0 if not bad else 1
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:                                        # noqa: BLE001
        data = {}
    text = _turn_text(data)
    if WORD_RE.search(text) is None:
        return 0
    # --try-stop は、止める側の道を別の設計書で試すための口（本物の Stop hook は旗なしで呼ばれる＝ACC だけを見る）
    acc = argv[argv.index("--design") + 1] if ("--try-stop" in argv and "--design" in argv) else ACC
    bad_a, bad_b = check_all(acc, data.get("transcript_path"), split=True)
    # ★B群だけが残るのは、実装の前の承認（書く権利をもらう承認）では当たり前に起きる
    #   ＝まだ実装していないので、条件のコマンドが通らない。これを止めると、
    #   「承認の前は実装できない／実装の前は承認をお願いできない」の行き止まりになる。
    #   だから B群だけのときは、返信に SAY の文字が在れば通す
    #   ＝承認が もう1回 要ることを、まこさんに先に伝えたときだけ通る。
    if not bad_a and (not bad_b or SAY in text):
        return 0
    head = ("🔒 [承認の前の検査] 承認のプログラムが止まる（または もう1回 承認が要る）状態のまま、"
            "承認をお願いしようとしています。\n"
            "   まこさん指示 2026-09-21「強制で承認ミスを防ぎ、何度も同じ承認をさせることをしないでほしい」")
    if not bad_a:
        head += (f"\n   ★残りは B群だけです。上のコマンドを走らせて消すか、返信に「{SAY}」と書き、"
                 "その理由（どの行が未着手のまま残るか）を まこさんに先に伝えてください。")
    _print(bad_a + bad_b, head)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
