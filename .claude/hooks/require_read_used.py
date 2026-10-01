#!/usr/bin/env python3
"""require_read_used — 読んだ中身を、これからやることの判断に使ったかを、ターンの終わりに見せさせる（2026-10-01・142回目 新設）。

まこさん指示（逐語 2026-10-01）＝「だから以下をできる状態にしろ。強制が必要なら強制しろ。」
  相手の文（私の約束・逐語）＝「読む前に、何を判断するために読むかを決めます。／
  読んだら、中身のどの行が判断の根拠になったかを示して動きます。／判断に使わないものは読みません。」
なぜ要るか＝142回目の私は、読むもの宣言の77件（壊すプログラム54本を含む）を、中身を判断に使わずに開き続けた。
  既存の強制は「開いた記録」しか見ないので、開くだけで通った（まこさん「開くだけは確認ではない」）。

決まり（Stop＝ターンを終える時に見る・まこさんの最後の発言より後だけを数える）
  そのターンで Read したファイルごとに、記録に残った私の文に「ファイル名:行番号」か「ファイル名#L行番号」
  （行番号は読んだ範囲の中）か「使わなかった: ファイル名」が無ければ、ターンを終わらせない（終了コード 2）。
  止めるのは1つのターンにつき1回（2回目は通す＝書き直しの往復を増やしすぎない）。
★読む前の文（何を判断するために読むか）は見られない＝2026-10-01 に本物の記録で確かめた
  （--try の並び29件のうち文は2件だけ。道具と道具の間に書いた文は記録に残らない。最後の返信は残る）。
限界＝示した行が本当に判断の根拠だったかは見ない（まこさんが画面で見る）。読むだけの Bash（grep・sed）は数えない。

★2026-10-01（142回目・まこさん指示「強制を入れて」）＝渡す前に全部読む（check_handover）
  なぜ＝私は、道具が作った監査依頼書（cp57）を1行も読まずにリンクを渡し、意味の通らない問い2 を まこさんに見つけさせた。
    上の決まりは「読んだファイル」しか見ないので、読まずに渡すと素通りした。
  決まり＝返信に、設計書（acceptance.md）か監査依頼書（…_audit_request.md）へのリンク「](…)」が在れば、
    その文書を最後に書き換えた時刻より後に、Read で1行目から最後の行まで読んだ記録（範囲の合わせ）が無ければ止める。
    ★この判定は、同じターンの2回目でも止める（2回目を通すと、読まずに出し直せば通るため）。
  限界＝読んだ中身を正しく照らしたかは見ない（読んだ行を根拠に書かせる上の決まりと、まこさんの目）。リンクでなく名前だけ書けば見ない。
  ★同日 追記（まこさん「チェック項目を見直しすべきでは？」→ 案に「それならばOK」）＝見直し表（.claude/tools/gen_review.py）も照らす。
    表が文書のいまの版の全項目（見出しと問い）を埋めているか、②の欄に実在する根拠の行が在るか、
    その根拠の行を、文書を書き換えた後に Read で開いたか。どれかが欠ければ止める（2回目でも止める）。
使い方: （hook）標準入力に Stop の JSON ／ --selftest ／ --try <記録>（いまの記録で何が止まるかを出す・何も止めない）
"""
import datetime
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from require_confirm_before_act import user_text  # まこさんの発言の見分け方を同じものにする

READ_MAX = 2000  # Read の道具が limit 無しで返す行数の上限
ROOT = pathlib.Path(__file__).resolve().parents[2]
# 渡す文書＝設計書と監査依頼書（まこさん 2026-10-01「設計書・監査依頼書」）。リンクの形「](パス)」だけを見る
HANDOVER_RE = re.compile(r"\]\(([^)\s]*(?:acceptance\.md|_audit_request\.md))(?:#[^)]*)?\)")


def _range(inp: dict) -> tuple:
    off = max(int(inp.get("offset") or 1), 1)
    lim = int(inp.get("limit") or READ_MAX)
    return off, off + lim - 1


def events_since_user(objs) -> list:
    """まこさんの最後の発言の後の並び。戻り＝[("text", 文) | ("read", パス, 始め, 終わり) | ("tool",)]。"""
    ev = []
    for o in objs:
        if o.get("type") == "user" and user_text(o):
            ev = []
            continue
        if o.get("type") != "assistant":
            continue
        for b in (o.get("message") or {}).get("content") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "text" and str(b.get("text", "")).strip():
                ev.append(("text", str(b["text"])))
            elif b.get("type") == "tool_use":
                inp = b.get("input") or {}
                if b.get("name") == "Read":
                    lo, hi = _range(inp)
                    ev.append(("read", str(inp.get("file_path") or ""), lo, hi))
                else:
                    ev.append(("tool",))
    return ev


def _cited(base: str, lo: int, hi: int, text: str) -> bool:
    if re.search(r"使わなかった[:：]\s*\S*" + re.escape(base), text):
        return True
    return any(lo <= int(m.group(1)) <= hi
               for m in re.finditer(re.escape(base) + r"(?::|#L)(\d+)", text))


def check(ev: list) -> list:
    """止める理由の一覧（空なら通す）。読んだファイルごとに、その後の文に根拠の行か「使わなかった」が在るか。"""
    ng = []
    for k, e in enumerate(ev):
        if e[0] != "read":
            continue
        b = pathlib.Path(e[1]).name
        later = "\n".join(x[1] for x in ev[k + 1:] if x[0] == "text")
        if not _cited(b, e[2], e[3], later):
            ng.append(f"{b}（{e[2]}〜{e[3]}行）を読んだが、どの行を判断の根拠にしたかを返信に示していない"
                      f"＝「{b}:行番号」か「使わなかった: {b}」を返信に書く")
    return ng


def _ts(o: dict) -> float:
    try:
        return datetime.datetime.fromisoformat(str(o.get("timestamp") or "").replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _reads_all(objs) -> list:
    """記録の中の Read の全部＝[(実パス, 始め, 終わり, 時刻)]（まこさんの最後の発言より前も数える）。"""
    out = []
    for o in objs:
        if o.get("type") != "assistant":
            continue
        for b in (o.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Read":
                inp = b.get("input") or {}
                lo, hi = _range(inp)
                out.append((os.path.realpath(str(inp.get("file_path") or "")), lo, hi, _ts(o)))
    return out


def _missing(ranges: list, n: int) -> list:
    """1〜n 行のうち、どの範囲にも入らない行のまとまり＝[(始め, 終わり)]。"""
    gaps, nxt = [], 1
    for lo, hi in sorted(ranges):
        if lo > nxt:
            gaps.append((nxt, min(lo - 1, n)))
        nxt = max(nxt, hi + 1)
        if nxt > n:
            break
    if nxt <= n:
        gaps.append((nxt, n))
    return [g for g in gaps if g[0] <= g[1]]


def check_handover(objs, texts: list, review_for=None) -> list:
    """返信でリンクを渡した設計書・監査依頼書を、最後に書き換えた後に全部 読んだか・見直し表が通るか。止める理由の一覧（空なら通す）。

    ★2026-10-01（142回目・まこさん「チェック項目を見直しすべきでは？」→ 案に「それならばOK」）＝読んだかだけでなく、
      見直し表（gen_review.py）が文書のいまの版の全項目を埋めているか・表に書いた根拠の行を、文書を書き換えた後に Read で開いたかを見る。
    review_for＝自己テスト用（文書のパス → 表の文）。本番は None（表の置き場から読む）。"""
    ng = []
    reads = _reads_all(objs)
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    import gen_review
    for link in sorted(set(HANDOVER_RE.findall("\n".join(texts)))):
        p = pathlib.Path(link) if link.startswith("/") else ROOT / link
        if not p.is_file():
            continue
        rp = os.path.realpath(str(p))
        mt = p.stat().st_mtime
        when = datetime.datetime.fromtimestamp(mt).strftime("%H:%M:%S")
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        gaps = _missing([(lo, hi) for f, lo, hi, t in reads if f == rp and t >= mt], n)
        if gaps:
            ng.append(f"{p.name}（{n} 行）を、最後に書き換えた後（{when}）に全部 読んでいない"
                      f"＝読んでいない行 {'・'.join(f'{a}〜{b}' for a, b in gaps)}。Read で全部 読み、項目ごとに確かめてから渡す")
        try:
            ng_r, refs = gen_review.check(str(p), review=(review_for(str(p)) if review_for else None))
        except Exception as e:                                        # noqa: BLE001
            ng_r, refs = [f"見直し表を照らせない（{type(e).__name__}: {e}）"], []
        ng += [f"{p.name} の見直し表: {x}" for x in ng_r]
        unread = sorted({f"{os.path.basename(f)}:{ln}" for f, ln in refs
                         if not any(rf == f and lo <= ln <= hi and t >= mt for rf, lo, hi, t in reads)})
        if unread:
            ng.append(f"{p.name} の見直し表の根拠の行を、文書を書き換えた後（{when}）に Read で開いていない＝"
                      + "・".join(unread[:10]) + (f" ほか {len(unread) - 10} 件" if len(unread) > 10 else ""))
    return ng


def _load(tp: str) -> list:
    objs = []
    for ln in pathlib.Path(tp).open(encoding="utf-8", errors="replace"):
        try:
            objs.append(json.loads(ln))
        except Exception:
            continue
    return objs


def hook() -> int:
    try:
        d = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    if d.get("agent_type"):
        return 0
    tp = d.get("transcript_path")
    if not tp or not pathlib.Path(tp).exists():
        return 0
    objs = _load(tp)
    ev = events_since_user(objs)
    # ★渡す前に全部読む＝2回目でも止める（読まずに出し直せば通る形にしない）
    ng_h = check_handover(objs, [x[1] for x in ev if x[0] == "text"])
    ng = []   # 2026-10-01 まこさん決定＝読んだ行の根拠の照らしは止めない
    if not ng and not ng_h:
        return 0
    if ng_h:
        print("🔒 [渡す前に全部読む] リンクで渡す設計書・監査依頼書を、最後に書き換えた後に全部 読んでいない", file=sys.stderr)
        for x in ng_h:
            print("   ・" + x, file=sys.stderr)
        print("   まこさんの指示（2026-10-01）「監査依頼出すまえに、全部の項目をチェックしてよ」「強制を入れて」", file=sys.stderr)
    if ng:
        print("🔒 [読んだ中身を判断に使う] このターンで読んだファイルの、どの行を判断の根拠にしたかを返信に示してから終える", file=sys.stderr)
        for x in ng:
            print("   ・" + x, file=sys.stderr)
        print("   まこさんの指示（2026-10-01）「読んだ中身を、これからやることの判断に使うこと」", file=sys.stderr)
    return 2


def selftest() -> int:
    a, b = "/p/a.py", "/p/b.py"
    cases = [
        ("T1 読んでいない → 通る", [("text", "答えます")], True),
        ("T2 読んだのに根拠の行を示していない → 止まる", [("read", a, 1, 2000), ("text", "直しました")], False),
        ("T3 a.py:10 を示した → 通る", [("read", a, 1, 2000), ("text", "根拠＝a.py:10")], True),
        ("T4 読んだ範囲の外の行を示した → 止まる", [("read", a, 1, 50), ("text", "根拠＝a.py:100")], False),
        ("T5 使わなかったと書いた → 通る", [("read", a, 1, 2000), ("text", "使わなかった: a.py")], True),
        ("T6 2本 読んで1本だけ示した → 止まる",
         [("read", a, 1, 2000), ("read", b, 1, 2000), ("text", "根拠＝a.py:3")], False),
        ("T7 示した後に読んだ物は、その後の文で見る → 止まる",
         [("read", a, 1, 2000), ("text", "根拠＝a.py:3 と b.py:5"), ("read", b, 1, 2000)], False),
    ]
    bad = 0
    for name, ev, want in cases:
        ok = (not check(ev)) == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {name}")
    # ★2026-10-01（142回目）＝渡す前に全部読む（check_handover）。一時ファイル（10行）と作り物の記録で見る
    import tempfile
    import time
    tdir = tempfile.mkdtemp(prefix="rru_selftest_")
    doc = os.path.join(tdir, "x_cp1_audit_request.md")
    open(doc, "w", encoding="utf-8").write("## 節A\n" + "".join(f"行{i}\n" for i in range(2, 11)))
    mt = os.path.getmtime(doc)
    # ★見直し表（gen_review）の作り物＝項目「## 節A」の行を埋め、根拠に文書の3行目を書く
    sys.path.insert(0, str(ROOT / ".claude" / "tools"))
    import gen_review
    good_rv = gen_review.skeleton(doc).replace("争点: <書く>", "争点: 見本").replace(
        "| <書く> | <書く> | <書く> | <書く> |", "| 通じる | x_cp1_audit_request.md:3 合う | 合う | OK |")
    rv_other = good_rv.replace("x_cp1_audit_request.md:3", "gen_review.py:1")
    ok_rv = (lambda _p: good_rv)
    def iso(t):
        return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    def rd(lo, lim, t):
        return {"type": "assistant", "timestamp": iso(t), "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": doc, "offset": lo, "limit": lim}}]}}
    link = f"依頼書です。[x]({doc})"
    hcases = [
        ("T8 リンクで渡したのに読んでいない → 止まる", [], link, False),
        ("T9 書き換えた後に全部 読んだ → 通る", [rd(1, 2000, mt + 5)], link, True),
        ("T10 書き換える前に読んだだけ → 止まる", [rd(1, 2000, mt - 60)], link, False),
        ("T11 一部（1〜5行）だけ読んだ → 止まる", [rd(1, 5, mt + 5)], link, False),
        ("T12 2回に分けて全部 読んだ（1〜5行・6〜10行）→ 通る", [rd(1, 5, mt + 5), rd(6, 5, mt + 6)], link, True),
        ("T13 リンクでなく名前を書いただけ → 見ない（通る）", [], "x_cp1_audit_request.md を直します", True),
    ]
    for name, objs, text, want in hcases:
        ok = (not check_handover(objs, [text], review_for=ok_rv)) == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {name}")
    # ★2026-10-01（142回目）＝見直し表の照らし
    rcases = [
        ("T14 全部 読んだが見直し表が無い → 止まる", None, False),
        ("T15 見直し表の根拠（別のファイルの行）を開いていない → 止まる", (lambda _p: rv_other), False),
        ("T16 見直し表が骨組みのまま → 止まる", (lambda _p: gen_review.skeleton(doc)), False),
    ]
    for name, rv, want in rcases:
        ok = (not check_handover([rd(1, 2000, mt + 5)], [link], review_for=rv)) == want
        bad += not ok
        print(f"  {'✅' if ok else '❌'} {name}")
    os.remove(doc)
    os.rmdir(tdir)
    n = len(cases) + len(hcases) + len(rcases)
    print(f"自己テスト {n - bad}/{n}")
    return 1 if bad else 0


def try_transcript(tp: str) -> int:
    """--try <記録>＝本物の記録で、まこさんの最後の発言の位置・その後の並び・いま止まる理由を出す（何も止めない）。"""
    objs = _load(tp)
    idx = [i for i, o in enumerate(objs) if o.get("type") == "user" and user_text(o)]
    print("まこさんの最後の発言の行", idx[-1] if idx else None, "/", len(objs),
          (user_text(objs[idx[-1]])[:80].replace("\n", " ") if idx else ""))
    ev = events_since_user(objs)
    print("並び", len(ev), "（うち文", sum(1 for e in ev if e[0] == "text"), "・読み", sum(1 for e in ev if e[0] == "read"), "）")
    for x in check(ev):
        print("  止まる:", x)
    for x in check_handover(objs, [e[1] for e in ev if e[0] == "text"]):
        print("  止まる（渡す前に全部読む）:", x)
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--try" in sys.argv:
        sys.exit(try_transcript(sys.argv[sys.argv.index("--try") + 1]))
    sys.exit(hook())
