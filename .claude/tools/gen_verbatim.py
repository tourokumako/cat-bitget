#!/usr/bin/env python3
"""gen_verbatim.py — まこさんの発言と、まこさんが OK した CC の文を、やり取りの記録からプログラムで抜き出し、逐語のファイルにする。

まこさん指示（2026-09-29・逐語）
  「設計書、監査依頼書、実装、監査結果からの設計書への修正、監査結果からの実装への修正、少なくともこの５点は自動生成にしろ。」
  「正確には以下を自動生成できてるのか確認→修正 ・やることリストなどの設計のもとになるものから設計書作成を自動生成 …」
  「OKなのですべて完璧に上記チャットの１から５の各要件の通りに修正をすること。完成後に要件通りに修正できているのかすべて証明をすること」

なぜ要るか
  132回目、まこさんが OK した文を、CC が自分の要約に置き換えて設計書と依頼書を書いた
  （帯の線・検査15・役割の3つが食い違い、依頼書に まこさんの文の38行が1行も入らなかった＝worklog 20260929 §12・§18）。
  CC が文を写す限り、置き換えは止まらない。だから、やり取りの記録（Claude Code が書く jsonl）から機械で抜き出す。

使い方
  python3 .claude/tools/gen_verbatim.py --list [--all] [--grep 語] [--tail N] [--session <id か jsonl のパス>]
      発言の一覧（uuid・時刻・話し手・先頭80文字）。既定＝まこさんの発言だけ。--all で CC の文も出す。
  python3 .claude/tools/gen_verbatim.py --write <名前> --uuid <uuid>[,<uuid>…] [--session …]
      .claude/state/verbatim/<名前>.txt（本文だけ）と <名前>.meta.json（記録の置き場・uuid・sha256）を書く。
  python3 .claude/tools/gen_verbatim.py --verify <名前>
      逐語のファイルが、記録の発言と1文字も違わないかを照らす（違えば終了コード 1）。
  python3 .claude/tools/gen_verbatim.py --lines <名前>
      逐語の行の番号（<名前>:V01 …・空の行は数えない）と中身を出す。設計書と依頼書はこの番号で行を指す。

★CC は文を書かない。CC が選ぶのは uuid だけ。
限界（正直に）
  ①どの uuid を選ぶか（どの発言が OK の相手か）は CC が決める＝選び間違いは、まこさんの目と監査が見る。
  ②記録の形（jsonl の鍵）が Claude Code の版で変わると、読めなくなる（そのときは止まる）。
  ③恒久71番＝文書を作る道具なので、壊すプログラムは付けない。走らせて確かめる。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".claude" / "state"
VERBATIM_DIR = STATE / "verbatim"                   # ★自己テストで差し替えられるように、関数は既定でここを読む
PROJECT_DIR = Path.home() / ".claude" / "projects" / "-Users-tachiharamasako-Documents-GitHub-cat-bitget"
SKIP_BLOCK = ("<ide_", "<system-reminder>")         # まこさんが打った文ではない区画（編集器と仕組みが足すもの）
SKIP_TEXT = ("Stop hook feedback", "[Request interrupted")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class VerbatimError(Exception):
    """読めない・見つからない・食い違う（fail-closed）。"""


def session_path(session: str | None = None) -> Path:
    """記録の jsonl の置き場。省くと、いちばん新しく書かれた jsonl。"""
    if session:
        p = Path(session)
        if p.suffix == ".jsonl" and p.exists():
            return p
        q = PROJECT_DIR / f"{session}.jsonl"
        if q.exists():
            return q
        raise VerbatimError(f"記録が見つからない: {session}")
    files = sorted(PROJECT_DIR.glob("*.jsonl"), key=lambda x: x.stat().st_mtime)
    if not files:
        raise VerbatimError(f"記録が1つも無い: {PROJECT_DIR}")
    return files[-1]


def _prompt_text(p) -> str:
    """途中に届いた発言（queued_command）の prompt を文にする（文字のことも、区画の一覧のこともある）。"""
    if isinstance(p, str):
        try:
            p = json.loads(p)
        except Exception:                                   # noqa: BLE001
            return p
    if isinstance(p, str):
        return p
    ts = [b.get("text", "") for b in (p or []) if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(x for x in ts if not x.startswith(SKIP_BLOCK))


def load_messages(path: Path) -> list[dict]:
    """記録から、まこさんの発言と CC の文を順に読む。戻り＝[{uuid, time, who, text}, …]。

    ★2026-09-29＝作業の途中に届いた まこさんの発言（記録の type=attachment・attachment.type=queued_command）も読む。
      直す前は user の行だけを読み、途中に届いた発言を1つも拾わなかった（worklog 20260929 §53）。
    """
    out = []
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            o = json.loads(ln)
        except Exception:                                   # noqa: BLE001
            continue
        t = o.get("type")
        if o.get("isSidechain"):
            continue
        if t == "attachment" and (o.get("attachment") or {}).get("type") == "queued_command":
            text = _prompt_text((o.get("attachment") or {}).get("prompt"))
            if text.strip() and not text.startswith(SKIP_TEXT):
                out.append({"uuid": o.get("uuid", ""), "time": o.get("timestamp", ""), "who": "まこさん", "text": text})
            continue
        if t not in ("user", "assistant"):
            continue
        c = (o.get("message") or {}).get("content")
        blocks = [{"type": "text", "text": c}] if isinstance(c, str) else (c if isinstance(c, list) else [])
        if t == "user":
            if o.get("isMeta"):
                continue
            if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks):
                continue
            kind = (o.get("origin") or {}).get("kind")
            if kind not in (None, "human"):
                continue
            texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
            texts = [x for x in texts if not x.startswith(SKIP_BLOCK)]
            text = "\n".join(texts)
            if not text.strip() or text.startswith(SKIP_TEXT):
                continue
            who = "まこさん"
        else:
            texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
            text = "\n".join(texts)
            if not text.strip():
                continue
            who = "CC"
        out.append({"uuid": o.get("uuid", ""), "time": o.get("timestamp", ""), "who": who, "text": text})
    return out


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ★2026-09-29＝CC の文は、返信の報告の部分（書き換えたファイルの一覧）の手前で切る。
#   直す前は、OK をもらった提案の後ろの報告まで逐語に入り、設計書の対応の表に要件でない行が5行 並んだ（worklog 20260929 §49 の3）。
REPORT_RE = re.compile(r"^\s*(?:#+\s*)?\**\s*(?:このターン|このやり取り)で(?:書き換え|書き替え)たファイル")


def _cut_report(text: str) -> str:
    ls = text.splitlines()
    for i, ln in enumerate(ls):
        if REPORT_RE.match(ln):
            return "\n".join(ls[:i]).rstrip()
    return text


def build_text(msgs: list[dict], uuids: list[str]) -> tuple[str, list[dict]]:
    """選んだ uuid の発言を、書いた順につなぐ（間は空の行1つ）。見つからない uuid が在れば止まる。
    CC の文は、返信の報告の部分（書き換えたファイルの一覧）の手前までにする。"""
    by = {m["uuid"]: m for m in msgs}
    missing = [u for u in uuids if u not in by]
    if missing:
        raise VerbatimError(f"記録に無い uuid: {', '.join(missing)}")
    chosen = [by[u] for u in uuids]
    return "\n\n".join(_cut_report(m["text"]) if m["who"] == "CC" else m["text"] for m in chosen), chosen


def paths(name: str, base: Path | None = None) -> tuple[Path, Path]:
    if not NAME_RE.match(name or ""):
        raise VerbatimError(f"名前に使えない文字が在る（英数字・_・.・- だけ）: {name}")
    d = Path(base) if base else VERBATIM_DIR
    return d / f"{name}.txt", d / f"{name}.meta.json"


def write(name: str, uuids: list[str], session: str | None = None, base: Path | None = None) -> Path:
    """逐語のファイルと、その出どころ（記録の置き場・uuid・sha256）を書く。"""
    sp = session_path(session)
    text, chosen = build_text(load_messages(sp), uuids)
    txt, meta = paths(name, base)
    txt.parent.mkdir(parents=True, exist_ok=True)
    txt.write_text(text, encoding="utf-8")
    meta.write_text(json.dumps({
        "_これは何か": "gen_verbatim.py が、やり取りの記録から抜き出した逐語のファイルの出どころ（手で書き換えない・--verify で照らす）",
        "session": str(sp), "uuids": uuids, "who": [m["who"] for m in chosen],
        "time": [m["time"] for m in chosen], "sha256": _sha(text)}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    return txt


def verify(name: str, base: Path | None = None) -> tuple[bool, str]:
    """逐語のファイルが、記録の発言と1文字も違わないか。戻り＝(合うか, 理由)。"""
    try:
        txt, meta = paths(name, base)
        if not txt.exists() or not meta.exists():
            return False, f"逐語のファイルか出どころが無い: {txt.name}"
        m = json.loads(meta.read_text(encoding="utf-8"))
        body = txt.read_text(encoding="utf-8")
        if _sha(body) != m.get("sha256"):
            return False, f"{txt.name} が、書いた後に書き替えられている（sha256 が出どころと違う）"
        want, _ = build_text(load_messages(Path(m["session"])), list(m.get("uuids") or []))
        if want != body:
            return False, f"{txt.name} が、記録の発言と違う"
        return True, ""
    except (VerbatimError, OSError, ValueError, KeyError) as e:
        return False, f"{name}: {e}"


def lines(name: str, base: Path | None = None) -> list[tuple[str, str]]:
    """逐語の行（空の行は数えない）＝[(<名前>:V01, 行), …]。照らしが通らなければ止まる。"""
    ok, why = verify(name, base)
    if not ok:
        raise VerbatimError(why)
    txt, _ = paths(name, base)
    rows = [ln for ln in txt.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [(f"{name}:V{i:02d}", ln) for i, ln in enumerate(rows, 1)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--grep", default="")
    ap.add_argument("--tail", type=int, default=30)
    ap.add_argument("--session", default=None)
    ap.add_argument("--write", default="")
    ap.add_argument("--uuid", default="")
    ap.add_argument("--verify", default="")
    ap.add_argument("--lines", default="")
    a = ap.parse_args(argv)
    try:
        if a.list:
            sp = session_path(a.session)
            ms = [m for m in load_messages(sp) if a.all or m["who"] == "まこさん"]
            if a.grep:
                ms = [m for m in ms if a.grep in m["text"]]
            print(f"記録＝{sp}（{len(ms)} 件のうち後ろの {min(a.tail, len(ms))} 件）")
            for m in ms[-a.tail:]:
                head = m["text"].replace("\n", "⏎")[:80]
                print(f"{m['uuid']}  {m['time'][:19]}  {m['who']}  {head}")
            return 0
        if a.write:
            uu = [u.strip() for u in a.uuid.split(",") if u.strip()]
            if not uu:
                print("❌ --uuid が空")
                return 2
            p = write(a.write, uu, a.session)
            print(f"✅ 書いた: {p.relative_to(ROOT)}（uuid {len(uu)} 件・行 {len(lines(a.write))} 行）")
            return 0
        if a.verify:
            ok, why = verify(a.verify)
            print(f"✅ --verify: {a.verify} は記録の発言と1文字も違わない" if ok else f"❌ --verify: {why}")
            return 0 if ok else 1
        if a.lines:
            for vid, ln in lines(a.lines):
                print(f"{vid}\t{ln}")
            return 0
    except VerbatimError as e:
        print(f"❌ {e}")
        return 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
