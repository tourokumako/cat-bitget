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
#   ★2026-10-15＝承認のプログラムの行番号は、ここに書かない（ずれるため）。目印の文字は _ANCHORS に在り、
#     不足の文には、走らせたときに探した行番号が出る（_at）。止まり所の数の照らしは A16。
#     A1 設計書が在るか（設計書が無いときに止める所）
#     A2 pre_audit_check.py --check-design（設計書の門の検査）
#     A3 凍結の前の検査＝承認のプログラムの1つ目の python の囲みを、書き先だけ一時置き場に
#        替えて そのまま走らせる（contract_for_freeze・resolve_spec_list ほか）
#     A4 控えを残す所＝ARC の目印・控えの置き場に書けるか・git が無視しないか・index.lock。
#        2026-10-15 から、逐語のファイルを控えへ移す所と、壊すプログラムを凍結する所も見る
#     A5 承認の記録の鍵＝approve_design.sh が書く鍵と check_approval が読む鍵が同じか
#     A6 run_breaks.py --count-targets --design
#     A7 run_breaks.py --parse-only（run_breaks.py --design の入口＝表が読めるか・列がずれていないか）
#     A8 表に載っている既存の壊すプログラムの宣言を expect_of で読む（run_breaks.py --design の159番の STOP）
#     A10 完成の条件のコマンドが、SDK を作業場所にしても開けるか（済を書く所の _run＝cwd=SDK・L-614）
#     A11 承認の後に打つ当てる道具（apply_audit_fix.py --design）が、実装の指示を全部 当てられるか
#         （一時の承認の印で check_one を全件に掛ける・道具そのものを直す件が在れば、当てた写しで2回目も見る）
#     A12 承認の後に起きること全部（当てる・完成の条件のコマンド・壊すプログラムの測り）を、本物のファイルに仮に当てて通し、
#         控えから元に戻す（.claude/state/_a12_backup・ハッシュ値で照らす）。A1〜A11 が全部 通ったときだけ走らせる
#     A13 設計書の中の事実（実装の指示の件数・工事名・触る関数・当てる道具を打つ回数）を道具が実物から数え、
#         全部の節の文と照らす（古いまま残った節を、CC に語を選ばせずに見つける）
#     A14 CC が設計書のいまの版を全部の項目について見直し終えているか（見直し表＝gen_review.py --check・
#         判定が「抜け」の項目が残っていれば止める）。承認のプログラムも同じ道具を呼んで承認を中止する（2026-10-04）
#     A16 承認のプログラムの、承認を止める行の数が、この検査の知っている数（_ANCHORS）と同じか（2026-10-15）
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
#   書いた直後に出す : show_design_check_after_write.sh が python3 <この .py> --post-tool を呼ぶ（標準入力＝hook の json・2026-10-15）
#                      ＝このコマンドで設計書が書き換わったときだけ調べて、結果を 2 で出す（post_tool の説明）。A12 は走らせない
#   手で書いた直後を試す: python3 <この .py> --after-write [--design <設計書>]（止めない・出すだけ・A12 は走らせない）
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
# ★2026-10-15＝試すときだけ、承認のプログラムの写しに差し替える口（HOOK_APPROVE_PATH・A16 の両方向の試しに使う）
APPROVE = os.environ.get("HOOK_APPROVE_PATH") or ROOT + "/.claude/hooks/approve_impl.sh"
PRE = ROOT + "/.claude/tools/pre_audit_check.py"
RUNB = ROOT + "/.claude/tools/run_breaks.py"
# ★2026-10-15＝試すときだけ、控えの置き場を差し替える口（HOOK_ARC_DIR・A4 の「止める」方向の試しに使う）
ARC_DIR = os.environ.get("HOOK_ARC_DIR") or SDK + "/.claude/ratchet/acceptance_archive"
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


def _rel(path):
    """不足の文に書く設計書の置き場（リポジトリの中なら根からの相対・外なら絶対）。★2026-10-15＝決め打ちの acceptance.md をやめた。"""
    p = os.path.abspath(path)
    return os.path.relpath(p, ROOT) if p.startswith(ROOT + os.sep) else p


# ★2026-10-15（181回目・まこさん「応急処置ではなく根本解決」）＝承認のプログラムの行番号を手で書かない。
#   直す前＝説明と不足の文に、承認のプログラムの行番号を手で書いていた（:72-288・:311・:360・:386・:401 ほか）。
#     承認のプログラムが直されるたびにずれ、10か所のうち7か所が、いまの行と合っていなかった。
#   直した後＝目印の文字を、走らせるたびに承認のプログラムの中で探し、そのときの行番号を出す（_at）。
#   さらに、承認を止める行（exit・sys.exit）を全部 数え、目印ごとの数と照らす（a16_stops_known）。
#     ＝承認のプログラムに止まり所が足されたのに、この検査を直していなければ、不足として出る。
# 並び＝（名前, 承認のプログラムの中の目印の文字, その目印の行から次の目印の前までに在る、承認を止める行の数）。
#   名前は、その止まり所を先に見ている検査（A1〜A7・A14）。数は 2026-10-15 に承認のプログラムを全部 読んで数えた（14行）。
_ANCHORS = [
    ("A1", 'if [ ! -f "$LIST" ]; then', 1),
    ("A2", 'pre_audit_check.py" --check-design "$LIST"', 1),
    ("A14", 'gen_review.py" --check "$LIST"', 1),
    ("A3", 'python3 - "$LIST" "$SPEC_OUT" "$FROZEN_OUT" <<\'PY\'', 3),
    ("A4", 'cp "$PREV_MD" "$KEEP"', 2),
    ("A4-逐語", 'mv "$VB_SRC" "$VB_DST"', 1),
    ("A1-もう一方の承認", 'approve_design.sh" "$LIST"', 1),   # もう一方の承認は、設計書が無いときだけ止まる（A1 と同じ）
    ("A5", '--check-approval "$LIST"', 1),
    ("A6", '--count-targets --design "$LIST"', 1),
    ("A4-凍結", '"$RUNB" --freeze', 1),
    ("A7", '"$RUNB" --design "$LIST" --iter "$ITER"', 1),
]
_STOP_RE = re.compile(r"\bexit\s+[1-9]|\bsys\.exit\(\s*[1-9]")


def _approve_lines():
    try:
        return open(APPROVE, encoding="utf-8").read().splitlines()
    except Exception:                                        # noqa: BLE001
        return None


def _at(key):
    """承認のプログラムの中で、その名前の目印が在る行（例＝「approve_impl.sh:32」）。見つからなければ、そう書いた文を返す。"""
    name = os.path.basename(APPROVE)
    lines = _approve_lines()
    if lines is None:
        return f"{name} を読めない"
    pat = next(a for k, a, _n in _ANCHORS if k == key)
    hits = [i + 1 for i, l in enumerate(lines) if pat in l]
    if len(hits) != 1:
        return f"{name} の中に目印「{pat}」が {len(hits)} か所＝この検査の _ANCHORS を直す"
    return f"{name}:{hits[0]}"


def a16_stops_known():
    """A16 承認のプログラムの、承認を止める行の数が、この検査の知っている数（_ANCHORS）と同じか。

    違えば、承認のプログラムに止まり所が足された（または消えた）のに、この検査が追いついていない。
    そのまま承認をお願いすると、ここが先に見ていない所で承認が止まりうる＝不足として出す。
    限界＝exit を使わずに承認を止める書き方を新しく足した場合は数えられない。"""
    name = os.path.basename(APPROVE)
    lines = _approve_lines()
    if lines is None:
        return [f"A16 承認のプログラムを読めません: {APPROVE}"]
    bad, pos = [], []
    for key, pat, n in _ANCHORS:
        hits = [i for i, l in enumerate(lines) if pat in l]
        if len(hits) != 1:
            bad.append(f"A16 {name} の中に目印「{pat}」（{key}）が {len(hits)} か所"
                       "＝この検査（require_design_check_before_approval.py の _ANCHORS）を直す")
        else:
            pos.append((hits[0], key, n))
    if bad:
        return bad
    pos.sort()
    stops = [i for i, l in enumerate(lines) if not l.lstrip().startswith("#") and _STOP_RE.search(l)]
    head = [i + 1 for i in stops if i < pos[0][0]]
    if head:
        bad.append(f"A16 {name} の最初の目印より前に、承認を止める行が在る（{', '.join(map(str, head))}行）"
                   "＝この検査が先に見ていない止まり所。この検査（_ANCHORS と A群）を直す")
    for j, (start, key, n) in enumerate(pos):
        end = pos[j + 1][0] if j + 1 < len(pos) else len(lines)
        got = [i + 1 for i in stops if start <= i < end]
        if len(got) != n:
            bad.append(f"A16 {name}:{start + 1}〜{end} の承認を止める行が {len(got)} 行"
                       f"（{', '.join(map(str, got)) or 'なし'}）。この検査が先に見ているのは {n} 行（{key}）"
                       "＝承認のプログラムの止まり所が増えた（または減った）のに、この検査が追いついていない。"
                       "この検査（_ANCHORS と A群）を直す")
    return bad


# ★2026-10-15（181回目・まこさん「応急処置ではなく根本解決」）＝設計書を書いた直後の口（--post-tool）。
#   show_design_check_after_write.sh（PostToolUse Bash）が、標準入力に hook の json を渡して呼ぶ。
#   直す前＝.sh が、コマンドの文字に「gen_acceptance.py」と「--write」が在るかだけで動き、いつも acceptance.md を調べた。
#     2026-09-24〜10-15 の記録で、設計書を作っていないのに64回 動き（合計1029秒）、--out で作った設計書は1回も調べなかった。
#     不足0件のとき（終了コード 0）と、検査が落ちたとき（終了コード 1）は、私の画面に何も出なかった。
#   直した後＝コマンドの文字では決めない。acceptance.md と、コマンドの --out の後ろの置き場のうち、
#     このコマンドを出した時刻（やり取りの記録の、その呼び出しの行の時刻）より後に書き換わったものだけを調べる。
#     調べたときは、不足が在っても0件でも 2 で終わる（PostToolUse で私の画面に届くのは 2 だけ＝記録の182回で届いている）。
#     書き換わったものが無ければ 0 で、何も出さない。検査が落ちたときは .sh が出す。
_BASH_MAX_SEC = 600   # Bash の道具の上限（10分）。これより前の更新は、このコマンドの書き換えではない（記録を読まずに済ませる）


def _tool_start(transcript, tool_use_id):
    """このコマンドを出した時刻（UNIX 秒）。やり取りの記録の後ろ 4MB から、その呼び出しの行の時刻を読む。読めなければ None。"""
    if not transcript or not os.path.isfile(transcript):
        return None
    size = os.path.getsize(transcript)
    with open(transcript, "rb") as fh:
        fh.seek(max(0, size - 4_000_000))
        tail = fh.read().decode("utf-8", "replace")
    ts = None
    for line in tail.splitlines():
        if '"tool_use"' not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:                                    # noqa: BLE001
            continue
        if r.get("type") != "assistant":
            continue
        for b in (r.get("message") or {}).get("content") or []:
            if (isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash"
                    and (not tool_use_id or b.get("id") == tool_use_id)):
                ts = r.get("timestamp")
    if not ts:
        return None
    try:
        return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:                                        # noqa: BLE001
        return None


def _out_paths(cmd, cwd):
    """コマンドの中の --out の後ろの置き場（引用符を外し、作業場所からの絶対パスにする）。"""
    out = []
    for p in re.findall(r"--out(?:=|\s+)(\"[^\"]+\"|'[^']+'|[^\s;&|]+)", cmd or ""):
        p = os.path.expanduser(p.strip("\"'"))
        out.append(os.path.abspath(os.path.join(cwd, p)))
    return out


def post_tool(raw):
    try:
        data = json.loads(raw or "{}")
    except Exception:                                        # noqa: BLE001
        data = {}
    cmd = (data.get("tool_input") or {}).get("command") or ""
    cwd = data.get("cwd") or ROOT
    now = time.time()
    cands = list(dict.fromkeys([ACC] + _out_paths(cmd, cwd)))
    recent = [p for p in cands if os.path.isfile(p) and now - os.path.getmtime(p) <= _BASH_MAX_SEC]
    if not recent:
        return 0
    tr = data.get("transcript_path")
    start = _tool_start(tr, data.get("tool_use_id"))
    e = sys.stderr
    if start is None:
        print("🔴 [設計書を書いた直後の検査] 設計書が10分以内に書き換わっていますが、このコマンドを出した時刻を"
              "やり取りの記録から読めません＝このコマンドが書き換えたかを決められないので、調べた結果を出します。", file=e)
        written = recent
    else:
        written = [p for p in recent if os.path.getmtime(p) >= start]
    if not written:
        return 0
    for acc in written:
        t0 = time.time()
        bad = check_all(acc, tr, trial=False)
        if bad:
            _print(bad, f"📋 [設計書を書いた直後の検査] {acc} が書き換わったので、承認のプログラムの止まり所を上から全部 確かめました。")
        else:
            print(f"✅ [設計書を書いた直後の検査] {acc} が書き換わったので確かめました。"
                  "A12（仮当て）のほかの止まり所は全部 通ります（不足0件）。", file=e)
        print("   ★A12（承認の後に起きることを本物に仮に当てて通す・約4分半）は、ここでは走らせていません。"
              "承認をお願いする前に `python3 .claude/hooks/require_design_check_before_approval.py --try` でかけてください。", file=e)
        print(f"   （かかった時間 {time.time() - t0:.1f} 秒）", file=e)
    return 2


# ── A群 ─────────────────────────────────────────────────────────────
def a2_check_design(acc):
    rc, out = _run(["python3", PRE, "--check-design", acc])
    if rc == 0:
        return []
    return [f"A2 設計書の門の検査（{_at('A2')}）が rc={rc}:\n{_tail(out, 60)}"]


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
    return [f"A3 凍結の前の検査（{_at('A3')} から始まる囲み＝ここで落ちると承認が取り消される）が rc={rc}:\n"
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
        bad.append(f"A4 .git/index.lock が在る＝git add が失敗して承認が取り消される（{_at('A4')}）")
    if os.path.exists(f"{ARC_DIR}/{safe}.md"):
        seq = 1
        while os.path.exists(f"{ARC_DIR}/{safe}.{seq:02d}.md"):
            seq += 1
        keep = f"{ARC_DIR}/{safe}.{seq:02d}.md"
        rc, _ = _run(["git", "-C", ROOT, "check-ignore", "-q", keep])
        if rc == 0:
            bad.append(f"A4 前の版の控え（{os.path.basename(keep)}）を git が無視する設定＝"
                       f"git add が失敗して承認が取り消される（{_at('A4')}）")
    # ★2026-10-15（181回目）＝直す前は、次の2か所の止まり所を先に見ていなかった（a16_stops_known の説明）。
    #   ①設計の元の逐語のファイル（.claude/state/verbatim/<iter>/）を控えの置き場へ移して git に入れる所（2026-09-29 に足された）
    vb = ROOT + "/.claude/state/verbatim/" + m.group(1)
    if os.path.isdir(vb):
        vdst = ARC_DIR + "/verbatim"
        if not os.access(vdst if os.path.isdir(vdst) else ARC_DIR, os.W_OK):
            bad.append(f"A4 逐語のファイルの移し先に書けません: {vdst}＝承認が取り消される（{_at('A4-逐語')}）")
        rc, _ = _run(["git", "-C", ROOT, "check-ignore", "-q", f"{vdst}/{safe}/x"])
        if rc == 0:
            bad.append(f"A4 逐語のファイルの移し先（{vdst}/{safe}/）を git が無視する設定＝"
                       f"git add が失敗して承認が取り消される（{_at('A4-逐語')}）")
    #   ②壊すプログラムを凍結する所（run_breaks.py --freeze が書く凍結のファイル）
    sys.path.insert(0, ROOT + "/.claude/tools")
    try:
        import run_breaks as rb                               # noqa: E402
        fz = os.environ.get("HOOK_FROZEN_PATH") or str(rb.FROZEN)   # ★試すときだけ差し替える口（2026-10-15）
    except Exception as e:                                   # noqa: BLE001
        bad.append(f"A4 壊すプログラムを走らせる道具を読み込めません（{e}）＝凍結の置き場を確かめられない（{_at('A4-凍結')}）")
    else:
        # 凍結を書く側は、親のフォルダを作ってから書く（run_breaks.py の --freeze）＝無ければ、いちばん近い実在する親に書けるかを見る
        near = fz if os.path.exists(fz) else os.path.dirname(fz)
        while near and not os.path.exists(near) and os.path.dirname(near) != near:
            near = os.path.dirname(near)
        if not os.access(near, os.W_OK):
            bad.append(f"A4 壊すプログラムの凍結のファイルに書けません: {fz}＝承認が取り消される（{_at('A4-凍結')}）")
    return bad


def a5_approval_key(acc):
    sys.path.insert(0, SDK + "/scripts/priority_rebuild")
    try:
        import verify_design_contract as v                    # noqa: E402
    except Exception as e:                                   # noqa: BLE001
        return [f"A5 照合の道具を読み込めません（{e}）＝承認の直後の確認（{_at('A5')}）が落ちる"]
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
    return [f"A6 壊すプログラムの探す文字の数え（{_at('A6')}＝落ちると承認が取り消される）が rc={rc}:\n"
            f"{_tail(out, 12)}"]


def a7_parse_only(acc):
    rc, out = _run(["python3", RUNB, "--parse-only", "--design", acc])
    if rc == 0:
        return []
    return [f"A7 完成の条件の表を読めません（{_at('A7')} が rc=2 で承認を取り消す）:\n{_tail(out, 12)}"]


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
                       f"（{_at('A7')} が承認を取り消す・159番）: {why}")
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
    # ★2026-09-30（worklog 20260930 §47・§48・まこさん指示「これ以上繰り返して時間を浪費しないでほしい」「改善しろ」）
    #   ＝設計書から当てる道（4-20 に実装の指示が在る）では、承認の前に「設計書に書いたのに実装していない」も見ない。
    #   直す前＝前の承認で一部だけ当たった差分が在ると、照合B が差分の関数と照らし、これから当てる関数
    #   （repo_path・selftest）で止まった。当たるかどうかは A11 が当てる道具で確かめ、当てた後は設計↔実装ゲートが照らす。
    if "<!-- ACC_IMPL_START" in md and "#### 実装 1" in md:
        msgs = [m for m in msgs if "設計書に書いたのに実装していない" not in m]
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


def a11_apply_dry(acc):
    """A11 承認の後に当てる道具（apply_audit_fix.py --design）が、設計書の実装の指示を全部 当てられるか。

    ★2026-09-30（worklog 20260930 §46〜§48・まこさん指示「これ以上繰り返して時間を浪費しないでほしい」「改善しろ」
      「なんで、強制で承認前のミスをさせないようにしてるのに、強制が効いてない？」）
      ＝直す前は、この検査が承認のプログラムの止まり所しか見ず、承認の後に打つ当てる道具を1回も試していなかった。
      工事 cp53-fix-20260930 は承認が通った後、当てる道具が新しい壊すプログラム2本を「守りの仕組み」で飛ばし、
      作り直しと承認がもう1回 要った（原因＝repo_path がまだ無いファイルを SDK 側に回す）。
    何をするか＝一時の承認の印（いまの設計書の sha256）を作り、当てる道具の check_one を全件に掛ける（何も書かない）。
      当てる道具そのものを直す件が在れば、その件を当てた写しで2回目を見る（まこさんが道具を2回 打つ流れと同じ）。
      2回目までに「当てられる」か「もう当て終わっている」にならない件を、不足として出す。
    """
    md = open(acc, encoding="utf-8").read()
    if "<!-- ACC_IMPL_START" not in md or "#### 実装 1" not in md:
        return []
    import hashlib
    import importlib.util
    tool = ROOT + "/.claude/tools/apply_audit_fix.py"
    tmp = tempfile.mkdtemp()

    def load(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    try:
        mark = os.path.join(tmp, "mark")
        with open(mark, "w", encoding="utf-8") as fh:
            fh.write(hashlib.sha256(open(acc, "rb").read()).hexdigest())
        sys.path.insert(0, ROOT + "/.claude/tools")
        a = load(tool, "_a11_apply_1")
        fixes = a.read_design_fixes(md)
        if not fixes:
            return []

        def sim(mod):
            mod.DESIGN, mod.APPROVED = acc, mark
            return [(f,) + tuple(mod.check_one(f, new_ok=True)[:2]) for f in fixes]

        r1 = sim(a)
        final = r1
        self_fix = [f for f, ok, _w in r1
                    if ok and os.path.realpath(a.repo_path(f["対象のファイル"])) == os.path.realpath(tool)]
        if self_fix:
            s = open(tool, encoding="utf-8").read()
            for f in self_fix:
                s, _how = a.apply_one(f, s)
            copy = os.path.join(tmp, "apply_audit_fix.py")
            with open(copy, "w", encoding="utf-8") as fh:
                fh.write(s)
            final = sim(load(copy, "_a11_apply_2"))
        bad = []
        for (f, ok1, w1), (_f, ok2, w2) in zip(r1, final):
            if ok1 or ok2 or "もう当て終わっている" in w1 or "もう当て終わっている" in w2:
                continue
            bad.append(f"件{f['番号']}（{f['対象のファイル']}）: {w2}")
    except Exception as e:                                   # noqa: BLE001
        return [f"A11 当てる道具を承認済みの形で試せません（{e}）＝承認の後に当たらない件を先に見られない"]
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    if not bad:
        return []
    return ["A11 承認の後に当てる道具を打っても、当たらない件が在る＝承認しても実装が終わらず、作り直しと承認が もう1回 要る:\n"
            + _tail("\n".join(bad), 20)]


def a13_facts(acc):
    """A13 設計書の中の事実が、節ごとに食い違っていないか（古いまま残った節を、CC に語を選ばせずに見つける）。

    ★2026-09-30（まこさん指示・逐語「一回の確認ですべて完全に修正できるように強制しろ」「矮小化するな」）
      ＝工事 cp53-fix-20260930-2 で、差し替えた節の外に、古い件数（実装の指示4件）・古い工事名（design:cp53-fix-20260930）・
      当てる道具を打つ回数（1回）・新しく触る関数の名前の抜け（repo_path）が9つの節に残り、CC が全行を読んで初めて見つけた。
    何を照らすか（事実は道具が実物から数える）
      ①実装の指示の件数＝4-20 の「#### 実装 N」の数。本文の「実装の指示 N件」「指示N件」がこれと違えば出す
      ②工事名＝1行目の ARC の iter。本文の「design:<名前>」「iter=<名前>」「工事 <名前>」が、iter の頭と同じで iter と違えば出す
      ③触る関数＝DESIGN_CONTRACT の impl_functions の名前。4-3（部品）と 7-5（照合）にその名前が無ければ出す
      ④当てる道具を打つ回数＝実装の指示に当てる道具そのもの（apply_audit_fix.py）を直す件と新しいファイルの件が両方 在れば2回、
        ほかは1回。本文の「当てる道具を N回」「端末で N回」がこれと違えば出す（「1回目」「1回 打つ」の順番の書き方は見ない）
    限界＝この4つの事実しか見ない（ほかの事実の食い違いは全行を読む CC と まこさんの目）。
    """
    md = open(acc, encoding="utf-8").read()
    if "<!-- ACC_IMPL_START" not in md:
        return []
    body = md.split("<!-- ACC_SOURCE_END -->", 1)[-1]
    body_nospec = body.split("<!-- ACC_SPEC_START", 1)[0]
    bad = []
    n = len(re.findall(r"^#### 実装 \d+", md, re.M))
    for m in re.finditer(r"(?:実装の)?指示\s?(\d+)\s?件", body_nospec):
        if int(m.group(1)) != n:
            ln = body_nospec[:m.start()].count("\n")
            bad.append(f"実装の指示の件数が {m.group(1)} 件と書いてある（実物は {n} 件）: …{body_nospec[max(0, m.start()-30):m.end()+10].strip()}…")
    mi = re.search(r'<!-- ARC iter="([^"]+)" -->', md)
    it = mi.group(1) if mi else ""
    head = re.sub(r"-\d+$", "", it)
    # ★実装の指示の囲みの中（コードのコメントの経緯）は見ない
    names_txt = body_nospec.split("<!-- ACC_IMPL_START", 1)[0] + body_nospec.split("<!-- ACC_IMPL_END -->", 1)[-1]
    for m in re.finditer(r"(?:design:|iter=|工事\s?)([A-Za-z0-9][A-Za-z0-9._-]+)", names_txt):
        nm = m.group(1).rstrip(".")
        if it and nm != it and head and (nm == head or re.sub(r"-\d+$", "", nm) == head):
            bad.append(f"工事名が古い（{nm}・いまは {it}）: …{names_txt[max(0, m.start()-30):m.end()+5].strip()}…")
    try:
        sys.path.insert(0, SDK + "/scripts/priority_rebuild")
        import verify_design_contract as vdc                  # noqa: E402
        c = vdc.extract_contract(md) or {}
    except Exception:                                        # noqa: BLE001
        c = {}
    funcs = sorted({f for v in (c.get("impl_functions") or {}).values() for f in v})
    sec = {}
    for m in re.finditer(r"^### (\d-\d+[a-z]?|\d+) [^\n]*\n(.*?)(?=^### |^## |\Z)", body_nospec, re.M | re.S):
        sec[m.group(1)] = m.group(2)
    chk = body_nospec.split("<!-- ACC_CHECKLIST_START", 1)[-1].split("<!-- ACC_CHECKLIST_END", 1)[0] if "ACC_CHECKLIST_START" in body_nospec else ""
    for f in funcs:
        if f not in (sec.get("4-3") or ""):
            bad.append(f"触る関数 {f}（DESIGN_CONTRACT の impl_functions）が 4-3 の部品の割り当てに無い")
        if chk and f not in chk:
            bad.append(f"触る関数 {f}（DESIGN_CONTRACT の impl_functions）が 7-5 の照合の答えに無い")
    impl = md.split("<!-- ACC_IMPL_START", 1)[-1].split("<!-- ACC_IMPL_END", 1)[0]
    self_fix = re.search(r"対象のファイル: \S*apply_audit_fix\.py", impl) is not None
    new_file = re.search(r"直す前の文字:\n~~~\nなし\n~~~", impl) is not None
    runs = 2 if (self_fix and new_file) else 1
    for m in re.finditer(r"(?:当てる道具を|端末で)\s?(\d)\s?回(?!目)(?!\s?打つ)", body_nospec):
        if int(m.group(1)) != runs:
            bad.append(f"当てる道具を打つ回数が {m.group(1)} 回と書いてある（この設計書は {runs} 回）: …{body_nospec[max(0, m.start()-30):m.end()+10].strip()}…")
    if not bad:
        return []
    return ["A13 設計書の中の事実が節ごとに食い違う（古いまま残った節）:\n" + _tail("\n".join(bad), 30)]


def a14_review(acc):
    """A14 CC が、設計書のいまの版を全部の項目について見直し終えているか（見直し表＝.claude/tools/gen_review.py --check）。

    ★2026-10-04（154回目・まこさん指示・逐語）＝「承認するまえに確認するフローに修正して」
      「私が承認する前にCCが設計書の内容を確認して修正箇所を見つけられるように、フローを修正すべき」。
    なぜ要るか（実測）＝154回目に CC は、道具が作った設計書を全部 読む前に承認のコマンドを まこさんに出した。
      ターンの終わりの検査（require_read_used）は返信が画面に出た後に走るので、まこさんは先に承認を打たれた。
      承認の後に読んで、完成の条件に RCI の行が無い抜けを見つけた＝承認の打ち直しが要る形になった。
    止める条件＝見直し表が無い／設計書のいまの版について書いたものではない／埋まっていない項目が在る／
      判定が「抜け」の項目が残っている（抜けを見つけたまま承認をお願いしない）。
    ★同じ道具を、承認のプログラム（approve_impl.sh）も呼ぶ＝CC が見直しを飛ばしても、承認の瞬間に止まる。
    限界＝見直しの判断が正しいかは見ない（項目を飛ばさないこと・根拠の行が実在すること・抜けを残さないことまで）。"""
    try:
        sys.path.insert(0, ROOT + "/.claude/tools")
        import gen_review
        ng, _refs = gen_review.check(acc)
    except Exception as e:                                   # noqa: BLE001
        return [f"A14 見直し表の道具を走らせられません（{e}）＝CC が設計書を見直したかを確かめられない"]
    if not ng:
        return []
    return ["A14 CC が設計書の見直しを終えていません（承認のプログラムも ここで承認を中止します）:\n"
            + _tail("\n".join(ng), 30)
            + "\n        やること: 設計書を1行目から最後まで Read で読み、"
              f"python3 .claude/tools/gen_review.py --skeleton {_rel(acc)} で表を作り、全部の項目を埋める。"
              "抜けを見つけたら設計書を直す（直すまで判定は「抜け」）"]


BK_DIR = ROOT + "/.claude/state/_a12_backup"
# ★2026-10-08（160回目）＝--try で A12 まで全部 通した設計書のハッシュ値の記録（終える前の検査が読む・main の説明）。
A12_OK = ROOT + "/.claude/state/a12_try_ok.json"


def _sha_of(path):
    import hashlib
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return ""


def _a12_ok_sha():
    try:
        return json.load(open(A12_OK, encoding="utf-8")).get("acc_sha", "")
    except Exception:                                        # noqa: BLE001
        return ""


def _a12_ok_write(acc):
    """acc＝全部 通った設計書（None なら記録を消す＝通らなかった）。"""
    if acc is None:
        if os.path.isfile(A12_OK):
            os.remove(A12_OK)
        return
    with open(A12_OK, "w", encoding="utf-8") as fh:
        json.dump({"acc_sha": _sha_of(acc), "acc": acc, "time": time.strftime("%Y-%m-%d %H:%M:%S")}, fh, ensure_ascii=False)
# ★2026-10-06（156回目・まこさん「監査出したあとに上記修正をする」「OK」・next_step の手順6）
#   ＝仮当てのまま走らせる自己テスト6本（監査に出す前のチェック pre_audit_check.py の CHECKS のうち、表を作り直さずに
#   走らせられるもの）。表の一致の検査（--verify）と H2 は入れない＝仮当てでは表を作り直さないので、名前が変わる工事では
#   必ず落ちる。増える時間＝1回 約3分半（2026-10-06 の実測の合計＝8.4・120.4・72.6・2.3・3.1・0.5秒）。
A12_SELFTESTS = (
    ("engine_tuner_exec.py", "--selftest"),
    ("observe_diag.py", "--selftest"),
    ("gen_materials.py", "--selftest"),
    ("gen_audit_request.py", "--selftest"),
    ("engine_tuner_gen.py", "--selftest-extra-gate"),
    ("verify_design_contract.py", "--diff"),       # 設計書のパスを後ろに足して走らせる
)


def a12_fail_allowed(name, rc, out):
    """A12 が自己テストの落ちを許すか（True＝止めない）。
    ★2026-10-08（160回目・まこさん OK の案 1b）＝写しで確かめる道具（.claude/state/indicator_review の *_draft_build.py）も
      この関数と A12_SELFTESTS を import して同じ判定を使う。159回目は写しの道具が許しを手で書き写し、B3・B4 まで許す形に
      直してから走らせ、A12（T6 だけ許す）と食い違って長い確かめを走らせ直した（教訓 L-671）。
    許すのは、gen_materials.py の落ちが T6（素の状態で --verify が鳴っている）だけのとき（下の _a12_trial_locked の説明）。"""
    fails = [l.strip() for l in (out or "").splitlines() if l.strip().startswith("❌ ") and not re.match(r"❌ \d+ 件", l.strip())]
    return bool(rc != 0 and name == "gen_materials.py" and fails
                and all(l.startswith("❌ T6: 素の状態で --verify が鳴っている") for l in fails))


def _a12_restore():
    """控えから元に戻す（途中で止まった前回の分も、始める前にここで戻す）。戻らなかったファイルを返す。"""
    import hashlib
    man = os.path.join(BK_DIR, "manifest.json")
    if not os.path.isfile(man):
        return []
    bad = []
    for e in json.load(open(man, encoding="utf-8")):
        p = e["path"]
        if e["existed"]:
            data = open(os.path.join(BK_DIR, e["bak"]), "rb").read()
            with open(p, "wb") as fh:
                fh.write(data)
            os.chmod(p, e["mode"])
            if e.get("mtime"):
                os.utime(p, (e["mtime"], e["mtime"]))      # ★書き替えた時刻も戻す（戻しただけで「検査の後に書き替えた」と見られないように）
            if hashlib.sha256(open(p, "rb").read()).hexdigest() != e["sha"]:
                bad.append(p)
        elif os.path.exists(p):
            os.remove(p)
    import shutil
    shutil.rmtree(BK_DIR, ignore_errors=True)
    return bad


def _a12_leftover():
    """★2026-10-06（157回目・まこさん「案１」）＝検査の最初に、前の仮当て（A12）が残した控えを見る。
    なぜ要るか＝設計書を書いた直後の hook（show_design_check_after_write.sh・上限 120秒）から呼ばれた仮当て（約4分半）が、
      本物のファイルを書き替えた後に打ち切られ、戻す処理（finally）が走らず、承認の前なのに本物が工事の中身のまま残った
      （2026-10-06 21:16・worklog 20261006 §21）。
    何をするか＝①控えのフォルダが無ければ何もしない ②一覧（manifest.json）の無い控えのフォルダは消す（何も控えなかった回）
      ③ほかの仮当てが錠を持っていれば何もしない（その仮当てが自分で戻す）④一覧の全部のファイルが、元どおりか、仮当てが書いた
      直後のハッシュ値（sha_after）のままなら、控えから戻す ⑤仮当ての後に書き替わったファイルが1本でも在れば、戻さずに止める
      （黙って戻すと、後からした本物の直しを消すため）。sha_after の無い古い一覧も、⑤と同じに扱う。
    戻り＝止める理由の一覧（無ければ空）。"""
    import hashlib
    import importlib.util
    import shutil
    if not os.path.isdir(BK_DIR):
        return []
    man = os.path.join(BK_DIR, "manifest.json")
    if not os.path.isfile(man):
        shutil.rmtree(BK_DIR, ignore_errors=True)
        return []
    spec = importlib.util.spec_from_file_location("_a12_runb_left", RUNB)
    rb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rb)
    took = rb.rw_take(wait=0)
    if took is False:
        return []
    try:
        if not os.path.isfile(man):
            return []
        ents = json.load(open(man, encoding="utf-8"))
        moved = []
        for e in ents:
            p = e["path"]
            cur = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.isfile(p) else None
            if cur == (e["sha"] if e["existed"] else None):
                continue                                     # もう元どおり
            if not e.get("sha_after") or cur != e["sha_after"]:
                moved.append(p)
        if moved:
            return [f"A12 前の仮当ての控え（{BK_DIR}）が残っていて、仮当てが書いた後に書き替わったファイルが在る"
                    f"＝自動では戻さない（後からした本物の直しを消さないため）。まこさんに報告する: {moved}"]
        left = _a12_restore()
        print(f"🔁 [承認の前の検査] 前の仮当てが途中で打ち切られて残した書き替え（{len(ents)} 本）を、控えから戻した", file=sys.stderr)
        if left:
            return [f"A12 前の仮当ての控えから戻せないファイルが在る（手で確かめる）: {left}"]
        return []
    finally:
        rb.rw_drop(took)


def a12_post_approval_trial(acc):
    """A12 の入口＝本物のファイルを仮に書き替える道具の錠（run_breaks.py の rw_take）を取ってから、仮当てをする。

    ★2026-10-06（156回目・まこさん「OK」・next_step §6 の249番）＝承認のプログラムが走らせた壊すプログラムと、この仮当てが
      重なり、片方が壊した状態を もう片方が元の中身として控えて戻した＝observe_diag.py に壊すプログラム b128 の壊し方が
      残った（2026-10-06 16:33）。錠を取れば、重なった方が待つ。中で走らせる run_breaks.py は、持ち主の印（環境の変数）を
      受け継ぐので錠を取り直さない。
    限界＝承認のプログラムが完成の条件のコマンドを走らせる所は錠を見ない（CC には直せない）＝重なると、本物は壊れないが、
      行が「未着手」のまま残ることがある。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_a12_runb", RUNB)
    rb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rb)
    took = rb.rw_take()
    if took is False:
        return [f"A12 ほかの道具が本物のファイルを仮に書き替え中で、{rb.LOCK_WAIT_SEC} 秒 待っても錠が取れない"
                f"（{rb.LOCK_DIR}）＝仮当てをしていない（もう一度 確かめる）"]
    try:
        return _a12_trial_locked(acc)
    finally:
        rb.rw_drop(took)


def _a12_trial_locked(acc):
    """A12 承認の後に起きること全部を、承認の前に本物のファイルで仮に通し、元に戻す（錠を持って呼ばれる）。

    ★2026-09-30（まこさん指示・逐語「一回の確認ですべて完全に修正できるように強制しろ」
      「承認後に修正が発生しないように、事前にミスが無いよう確認をしろ」「矮小化するな」）
      ＝直す前は、承認の後に当てる道具を打ち、自己テストと壊すプログラムを走らせて、初めて穴が見つかった
      （工事 cp53-fix-20260930＝承認の後に新しい壊すプログラム2本が作られず、作り直しと承認がもう1回 要った）。
    何をするか＝①TARGET・NEW_FILE の中身を控え（.claude/state/_a12_backup）に写す
      ②当てる道具の check_one と apply_one で、実装の指示を全部 本物のファイルに当てる
        （当てる道具そのものを直す件が在れば、直った道具を読み直して2回目も当てる＝まこさんが2回 打つ流れと同じ）
      ③完成の条件の全部の行のコマンドを、承認のプログラムと同じ作業場所（SDK）で走らせる
      ④run_breaks.py --design <設計書> --measure-only で、表の壊すプログラムを全部 測る
      ⑤控えから戻し、ハッシュ値で元どおりかを照らす（戻らなければ大きく出す）
      当たらない件・落ちたコマンド・期待と違う壊すプログラムを、全部 一度に出す。
    限界＝完成の条件と壊すプログラムが見る所しか見ない（中身の正しさは全行を読む CC とまこさんの目）。
    """
    md = open(acc, encoding="utf-8").read()
    if "<!-- ACC_IMPL_START" not in md or "#### 実装 1" not in md:
        return []
    import hashlib
    import importlib.util
    import stat
    left = _a12_restore()                                    # 前回が途中で止まっていたら先に戻す
    if left:
        return [f"A12 前回の仮当ての控えから戻せないファイルが在る（手で確かめる）: {left}"]
    tool = ROOT + "/.claude/tools/apply_audit_fix.py"
    bad = []
    tmp = tempfile.mkdtemp()

    def load(path, name):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    try:
        sys.path.insert(0, ROOT + "/.claude/tools")
        mark = os.path.join(tmp, "mark")
        with open(mark, "w", encoding="utf-8") as fh:
            fh.write(hashlib.sha256(open(acc, "rb").read()).hexdigest())
        a = load(tool, "_a12_apply_1")
        fixes = a.read_design_fixes(md)
        os.makedirs(BK_DIR, exist_ok=True)
        man = []

        def keep(p):
            """★書く直前に、その置き場を控えに足す（2026-09-30＝最初に置き場を決めて控えたら、直った道具が別の置き場に
            書き、新しいファイル2本が戻らずに残った。書く道具が決めた置き場そのものを控える）。"""
            p = os.path.realpath(p)
            if any(e["path"] == p for e in man):
                return
            e = {"path": p, "existed": os.path.isfile(p), "bak": f"{len(man)}.bak", "mode": 0o644, "sha": ""}
            if e["existed"]:
                data = open(p, "rb").read()
                open(os.path.join(BK_DIR, e["bak"]), "wb").write(data)
                e["mode"] = stat.S_IMODE(os.stat(p).st_mode)
                e["mtime"] = os.stat(p).st_mtime
                e["sha"] = hashlib.sha256(data).hexdigest()
            man.append(e)
            with open(os.path.join(BK_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
                json.dump(man, fh, ensure_ascii=False)

        def wrote(p):
            """★2026-10-06（157回目・まこさん「案１」）＝書いた直後のハッシュ値を控えの一覧に残す。途中で打ち切られて控えが残ったとき、
            次の検査（_a12_leftover）は、ファイルがこの値のまま（仮当ての後に誰も書き替えていない）のときだけ戻す。"""
            p = os.path.realpath(p)
            for e in man:
                if e["path"] == p:
                    e["sha_after"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
            with open(os.path.join(BK_DIR, "manifest.json"), "w", encoding="utf-8") as fh:
                json.dump(man, fh, ensure_ascii=False)
        done = set()
        for rnd in (1, 2):
            mod = a if rnd == 1 else load(tool, "_a12_apply_2")
            mod.DESIGN, mod.APPROVED = acc, mark
            changed_tool = False
            for f in fixes:
                if f["番号"] in done:
                    continue
                ok, why, cur = mod.check_one(f, new_ok=True)
                if "もう当て終わっている" in why:
                    done.add(f["番号"])
                    continue
                if not ok:
                    continue
                path = mod.repo_path(f["対象のファイル"])
                keep(path)
                if (f["直す前の文字"] or "").strip() == "なし":
                    body = next(b for _a, k, b in f["4つ目"] if k == "直した後の文字")
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(body.rstrip("\n") + "\n")
                    if path.endswith(".sh"):
                        os.chmod(path, 0o755)
                else:
                    new, _how = mod.apply_one(f, cur)
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(new)
                wrote(path)
                done.add(f["番号"])
                changed_tool = changed_tool or os.path.realpath(path) == os.path.realpath(tool)
            if rnd == 1 and not changed_tool:
                break
        for f in fixes:
            if f["番号"] not in done:
                bad.append(f"当てる道具を2回 打っても当たらない件＝件{f['番号']}（{f['対象のファイル']}）")
        m = re.search(r"<!-- ACCEPT_TABLE_START -->(.*?)<!-- ACCEPT_TABLE_END -->", md, re.S)
        for ln in (m.group(1).splitlines() if m else []):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) < 3 or not cells[0].isdigit():
                continue
            mc = re.search(r"`([^`]+)`", cells[2])
            if not mc:
                continue
            try:
                r = subprocess.run(mc.group(1), shell=True, capture_output=True, text=True, timeout=300, cwd=SDK)
                if r.returncode != 0:
                    bad.append(f"完成の条件 #{cells[0]} のコマンドが当てた後に落ちる（rc={r.returncode}）: {mc.group(1)}\n"
                               + _tail((r.stdout or "") + (r.stderr or ""), 8))
            except Exception as e:                           # noqa: BLE001
                bad.append(f"完成の条件 #{cells[0]} のコマンドを走らせられない（{e}）")
        rc, out = _run(["python3", RUNB, "--design", acc, "--measure-only"], timeout=900)
        wrong = [l for l in (out or "").splitlines() if "期待と違う" in l or "まだ測れない" in l]
        if rc not in (0,) or wrong:
            bad.append(f"壊すプログラムが当てた後に期待どおりでない（rc={rc}）:\n" + _tail("\n".join(wrong) or out, 12))
        # ★2026-10-06（156回目・next_step の手順6）＝仮当てのまま、自己テスト6本も走らせる（A12_SELFTESTS の説明）。
        for st in A12_SELFTESTS:
            cmd6 = ["python3", SDK + "/scripts/priority_rebuild/" + st[0]] + list(st[1:])
            if st[0] == "verify_design_contract.py":
                cmd6.append(acc)
            try:
                r6 = subprocess.run(cmd6, capture_output=True, text=True, timeout=600, cwd=SDK)
                # ★2026-10-06（157回目・まこさん「なおしてよい」）＝材料の名前が変わる工事は、材料の文書（materials.md）を
                #   作り直す（G-1・承認の後）まで、gen_materials.py の T6（素の状態で --verify が鳴っている）が必ず落ちる。
                #   仮当てでは表を作り直さないので、落ちた番人が T6 だけのときは止めない（表を作り直した後は、
                #   監査に出す前のチェック pre_audit_check.py が gen_materials.py --selftest と --verify を必ずかける）。
                # ★2026-10-07（監査 CP63 の修正3・Major-1）＝「❌ T」で始まる行だけを集めると、T で始まらない落ち
                #   （F4・R1・S1 ほか）と T6 が一緒に出たときに見逃す。件数の行（「❌ N 件」）を除く ❌ の行を全部 集める。
                if a12_fail_allowed(st[0], r6.returncode, (r6.stdout or "") + (r6.stderr or "")):
                    continue
                if r6.returncode != 0:
                    bad.append(f"自己テストが当てた後に落ちる（rc={r6.returncode}）: {' '.join(st)}\n"
                               + _tail((r6.stdout or "") + (r6.stderr or ""), 8))
            except Exception as e:                           # noqa: BLE001
                bad.append(f"自己テストを走らせられない（{' '.join(st)}・{e}）")
    except Exception as e:                                   # noqa: BLE001
        bad.append(f"仮に当てて通す試しが途中で落ちた（{e}）")
    finally:
        left = _a12_restore()
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        if left:
            bad.append(f"❗仮に当てたファイルを元に戻せない（手で確かめる）: {left}")
    if not bad:
        return []
    return ["A12 承認の後に起きること（当てる・完成の条件のコマンド・壊すプログラム・自己テスト6本）を仮に通すと落ちる"
            "＝このまま承認すると、承認の後に直しが要る:\n" + _tail("\n".join(bad), 40)]


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


def b_runtime(md, exist, rb, transcript, acc=ACC):
    # ★2026-10-15（181回目）＝acc を受け取る。直す前は、調べている設計書ではなく、いつも本物の設計書（ACC）の
    #   書き替えの時刻と比べていた＝--out で作った設計書を調べると、B1・B2 の判定と「走らせる」の文が誤った。
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
    newest = os.path.getmtime(acc) if os.path.exists(acc) else 0.0
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
                       f"        走らせる: python3 .claude/tools/run_breaks.py --design {_rel(acc)} --measure-only")
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


def check_all(acc=ACC, transcript=None, split=False, trial=True):
    """不足の一覧を返す。split=True なら（A群＝承認が止まる, B群＝もう1回 承認が要る）に分けて返す。
    ★2026-10-06（157回目・まこさん「案１」）＝trial=False（設計書を書いた直後の --after-write）は A12（仮当て・約4分半）を走らせない
      （上限 120秒の hook から呼ぶと打ち切られ、本物が書き替わったまま残るため）。A12 は --try と、ターンの終わりの検査（上限 600秒）でかける。
      どの呼び方でも、最初に前の仮当ての残りを見る（_a12_leftover）。"""
    left = _a12_leftover()
    if not os.path.isfile(acc):
        a1 = left + [f"A1 設計書がありません: {acc}（{_at('A1')}）"]
        return (a1, []) if split else a1
    md = open(acc, encoding="utf-8").read()
    bad = list(left)
    bad += a16_stops_known()                                 # ★2026-10-15＝承認のプログラムに、ここが知らない止まり所が増えていないか
    bad += a2_check_design(acc)
    bad += a3_freeze_block(acc)
    bad += a4_archive(md)
    bad += a5_approval_key(acc)
    bad += a6_count_targets(acc)
    bad += a7_parse_only(acc)
    bad += a9_contract_full(acc)
    bad += a10_cmd_cwd(md)
    bad += a11_apply_dry(acc)
    bad += a13_facts(acc)
    b8, exist, rb = a8_expect(md)
    if not bad and not b8 and trial:
        bad += a12_post_approval_trial(acc)                  # 重いので、ほかが全部 通ったときだけ（出す不足は全部 一度に）
    bad += b8
    bad += a14_review(acc)                                   # ★2026-10-04＝CC が設計書を見直し終えているか（承認のプログラムも同じ道具で止める）
    bad_b = b_runtime(md, exist, rb, transcript, acc) if rb is not None else []
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
    # ★2026-10-01（まこさん指示「以下強制を早急に修正しろ」「強制の不具合で進行が妨げられている」）
    #   直す前＝「まこさんの最後の発言」より後の返信を全部つないでいた。同じターンで hook に止められて
    #   書き直しても、止められた前の返信の文（お願いの言い方）が範囲に残り、何を書いても止まり続けた
    #   （監査のセッション 7b5dce33 の記録で実測＝「Stop hook feedback:」の行が11回 続いた）。
    #   直した後＝差し戻し（type=user・文字列「◯◯ hook feedback:」）の行が後ろに在れば、その最後の行より
    #   後だけを読む＝いま出そうとしている返信だけを見る。
    for i, r in enumerate(rows):
        if i > start and r.get("type") == "user":
            c = (r.get("message") or {}).get("content")
            if isinstance(c, str) and re.match(r"^\S+ hook feedback:", c.strip()):
                start = i
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
    if "--post-tool" in argv:
        # ★2026-10-15（181回目）＝show_design_check_after_write.sh が、標準入力に hook の json を渡して呼ぶ口（post_tool の説明）
        return post_tool(sys.stdin.read())
    if "--try" in argv or "--after-write" in argv:
        acc = argv[argv.index("--design") + 1] if "--design" in argv else ACC
        tr = argv[argv.index("--transcript") + 1] if "--transcript" in argv else None
        t0 = time.time()
        after = "--after-write" in argv
        bad = check_all(acc, tr, trial=not after)
        if not after:
            # ★2026-10-08（160回目）＝A12 まで通したかの記録（終える前の検査は A12 を走らせず、この記録を見る＝main の下の説明）
            _a12_ok_write(acc if not bad else None)
        if bad:
            _print(bad, "📋 [承認の前の検査] 承認のプログラムの止まり所を、上から全部 確かめました。")
        elif after:
            print("✅ [承認の前の検査] A12（仮当て）のほかの止まり所は全部 通ります（不足0件）。")
        else:
            print("✅ [承認の前の検査] 承認のプログラムの止まり所 A1〜A8・B1・B2 は全部 通ります（不足0件）。")
        if after:
            # ★2026-10-06（157回目・まこさん「案１」）＝書いた直後は A12 を走らせない（check_all の説明）
            print("   ★A12（承認の後に起きることを本物に仮に当てて通す・約4分半）は、設計書を書いた直後には走らせていません。"
                  "承認をお願いする前に `python3 .claude/hooks/require_design_check_before_approval.py --try` でかけてください。")
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
    # ★2026-10-08（160回目・まこさん「原因究明後、対策をして」）＝終える前の検査では A12（仮当て）を走らせない。
    #   A12 は約17分（実測 992.8秒・1041.6秒）かかり、この hook の上限 600秒（settings.json）で打ち切られる。
    #   打ち切られると戻す処理（finally）が走らず、本物のファイルに仮当ての中身と新しい壊すプログラムが残り、
    #   まこさんの承認が「新規と書いたのに実在する」で2回 止まった（07:25 と 08:51 に走った仮当ての残り）。
    #   代わりに、--try で A12 まで通した記録（A12_OK）が、この設計書の今の版（ハッシュ値）のものかだけを見る。
    bad_a, bad_b = check_all(acc, data.get("transcript_path"), split=True, trial=False)
    if not bad_a and _a12_ok_sha() != _sha_of(acc):
        bad_a.append("A12 --try で承認の後に起きること（仮当て）まで通した記録が、この設計書の今の版に無い"
                     "＝`python3 .claude/hooks/require_design_check_before_approval.py --try` を先に走らせて通してから、"
                     "承認をお願いする（終える前の検査では A12 を走らせない＝上限 600秒で打ち切られ、本物に仮当てが残るため）")
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
