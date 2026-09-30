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
  python3 .claude/tools/gen_verbatim.py --write <名前> --work <工事名> --uuid <uuid>[,<uuid>…] [--drop V05,V08] [--session …]
      .claude/state/verbatim/<工事名>/<名前>.txt（本文だけ）と <名前>.meta.json（記録の置き場・uuid・sha256・drop）を書く。
      ★--drop＝要件のまとめで外す行の番号（問い・念押しの行など）。本文と番号は変えず、まとめの「外した行」に出す。
      ★--work（工事名＝設計書の ARC の iter）は必須（2026-09-29 まこさん指示「後先考えずに設計してゴミデータを量産するな」）。
  python3 .claude/tools/gen_verbatim.py --verify <名前>
      逐語のファイルが、記録の発言と1文字も違わないかを照らす（違えば終了コード 1）。
  python3 .claude/tools/gen_verbatim.py --lines <名前>
      逐語の行の番号（<名前>:V01 …・空の行は数えない）と中身を出す。設計書と依頼書はこの番号で行を指す。
  python3 .claude/tools/gen_verbatim.py --summary <工事名>
      その工事のフォルダに在る逐語のファイル全部から「要件のまとめ」1本（<工事名>/要件のまとめ.md）を作る
      ＝工事名・通し番号（R01…）・逐語の行の番号・文・話し手・出どころ（記録・uuid・時刻・sha256）。CC は書かない。

名前の解決（2026-09-29）
  <名前> は「<工事名>/<名前>」でも、<名前> だけでもよい。<名前> だけのときは、
  .claude/state/verbatim/<名前>・verbatim/*/<名前>・承認の後の archive（acceptance_archive/verbatim/*/<名前>）を探し、
  ちょうど1つ見つかればそれを使う（2つ以上なら止まる）。
  承認の後は、承認のプログラム（approve_impl.sh）が verbatim/<工事名>/ を設計書の控えと一緒に archive へ移す。

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
# ★2026-09-29＝承認の後の置き場（承認のプログラムが verbatim/<工事名>/ をここへ移す・読むだけ）
ARCHIVE_DIR = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim"
PROJECT_DIR = Path.home() / ".claude" / "projects" / "-Users-tachiharamasako-Documents-GitHub-cat-bitget"
SKIP_BLOCK = ("<ide_", "<system-reminder>")         # まこさんが打った文ではない区画（編集器と仕組みが足すもの）
SKIP_TEXT = ("Stop hook feedback", "[Request interrupted")
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
FULL_RE = re.compile(r"^(?:([A-Za-z0-9_.-]+)/)?([A-Za-z0-9_.-]+)$")   # <工事名>/<名前> か <名前>
SUMMARY_MD = "要件のまとめ.md"
SUMMARY_MARK = "<!-- VERBATIM_SUMMARY hash="


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


# ★2026-09-29（まこさん「それでいいので進めて」・worklog 20260929 §94）＝要件のまとめで、要件でない行を「外した行」へ分ける。
#   逐語のファイルの本文と行の番号（V01…）は変えない（--verify と、行の番号で指している物を壊さないため）。分けるのは まとめを作る時だけ。
#   ①道具の決まりで外す＝表の区切りの行／返信の終わりの「書き換えたファイル＝…」の行（REPORT_RE は「このターンで…」しか見ない）
#   ②CC が番号で外す＝--write の --drop（CC は文を書かず、番号を選ぶだけ・控えの drop に残る）
#   外した行は消さずに、まとめの「外した行」の表に逐語のまま全部 出す。
SEP_RE = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")
REPORT_LINE_RE = re.compile(r"^\s*(?:#+\s*)?\**\s*(?:(?:このターン|このやり取り)で)?(?:書き換え|書き替え)たファイル")


def drop_reason(ln: str, vid_short: str, drop: list) -> str:
    """要件のまとめで外す理由（外さないなら空）。vid_short＝V01 の形。"""
    if vid_short in drop:
        return "CC が番号で外した（--drop）"
    if SEP_RE.match(ln):
        return "表の区切りの行（道具の決まり）"
    if REPORT_LINE_RE.match(ln):
        return "返信の終わりの「書き換えたファイル」の行（道具の決まり）"
    return ""


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


def split_name(name: str) -> tuple[str | None, str]:
    """「<工事名>/<名前>」を (工事名, 名前) に分ける。<名前> だけなら (None, 名前)。"""
    m = FULL_RE.match(name or "")
    if not m:
        raise VerbatimError(f"名前に使えない文字が在る（英数字・_・.・- と、工事名との間の / だけ）: {name}")
    return m.group(1), m.group(2)


def paths(name: str, base: Path | None = None) -> tuple[Path, Path]:
    """逐語のファイルと控えの置き場（2026-09-29＝工事ごとのフォルダと archive を探す）。

    base が在ればそこ（自己テストと --write）。「<工事名>/<名前>」なら verbatim/<工事名>/。
    <名前> だけなら、verbatim/<名前>・verbatim/*/<名前>・archive の verbatim/*/<名前> を探し、ちょうど1つならそれ。
    1つも無ければ verbatim/<名前>（在るかどうかは呼ぶ側が見る）。2つ以上なら止まる（どれか分からない）。
    """
    work, short = split_name(name)
    if base:
        d = Path(base)
    elif work:
        # ★2026-09-29（承認の後に見つけた）＝承認のプログラムが verbatim/<工事名>/ を archive へ移すので、工事名つきでも archive を探す
        d = VERBATIM_DIR / work
        if not d.is_dir() and (ARCHIVE_DIR / work).is_dir():
            d = ARCHIVE_DIR / work
    else:
        hits = [p for p in [VERBATIM_DIR / f"{short}.txt"] if p.exists()]
        hits += sorted(VERBATIM_DIR.glob(f"*/{short}.txt"))
        hits += sorted(ARCHIVE_DIR.glob(f"*/{short}.txt")) if ARCHIVE_DIR.exists() else []
        if len(hits) > 1:
            raise VerbatimError(f"同じ名前の逐語のファイルが {len(hits)} つ在る（工事名を付けて指す）: "
                                + "・".join(str(h.relative_to(ROOT)) for h in hits))
        d = hits[0].parent if hits else VERBATIM_DIR
    return d / f"{short}.txt", d / f"{short}.meta.json"


def write(name: str, uuids: list[str], session: str | None = None, base: Path | None = None,
          work: str | None = None, drop: list | None = None) -> Path:
    """逐語のファイルと、その出どころ（記録の置き場・uuid・sha256・外す行の番号）を書く。

    ★2026-09-29＝置き場は工事ごとのフォルダ（--work か「<工事名>/<名前>」）。どちらも無ければ止まる
      （まこさん指示「後先考えずに設計してゴミデータを量産するな」＝直下に散らかさない）。
    ★2026-09-29＝drop＝要件のまとめで外す行の番号（V05 の形）。本文には在る番号でなければ止まる（書く前に照らす）。
    """
    sp = session_path(session)
    text, chosen = build_text(load_messages(sp), uuids)
    drop = [str(x).strip() for x in (drop or []) if str(x).strip()]
    n_rows = len([ln for ln in text.splitlines() if ln.strip()])
    bad = [x for x in drop if not re.fullmatch(r"V\d{2,}", x) or not (1 <= int(x[1:]) <= n_rows)]
    if bad:
        raise VerbatimError(f"--drop に、本文に無い行の番号が在る（V01〜V{n_rows:02d}）: {'・'.join(bad)}")
    w, short = split_name(name)
    work = work or w
    if not base:
        if not work or not NAME_RE.match(work):
            raise VerbatimError("--work（工事名＝設計書の ARC の iter・英数字・_・.・-）が要る。逐語のファイルは工事ごとのフォルダに置く")
        if (ARCHIVE_DIR / work).is_dir():
            raise VerbatimError(f"工事 {work} は承認の後（archive に在る）。承認の後の工事のフォルダには書かない（新しい工事名で書く）")
        base = VERBATIM_DIR / work
    txt, meta = paths(short, base)
    txt.parent.mkdir(parents=True, exist_ok=True)
    txt.write_text(text, encoding="utf-8")
    meta.write_text(json.dumps({
        "_これは何か": "gen_verbatim.py が、やり取りの記録から抜き出した逐語のファイルの出どころ（手で書き換えない・--verify で照らす）",
        "session": str(sp), "uuids": uuids, "who": [m["who"] for m in chosen],
        "time": [m["time"] for m in chosen], "sha256": _sha(text), "drop": drop}, ensure_ascii=False, indent=1) + "\n",
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
    _w, short = split_name(name)
    rows = [ln for ln in txt.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [(f"{short}:V{i:02d}", ln) for i, ln in enumerate(rows, 1)]


def work_dir(work: str) -> Path:
    """工事のフォルダ（作業中なら verbatim/<工事名>・承認の後なら archive）。無ければ止まる。"""
    if not NAME_RE.match(work or ""):
        raise VerbatimError(f"工事名に使えない文字が在る: {work}")
    for d in (VERBATIM_DIR / work, ARCHIVE_DIR / work):
        if d.is_dir():
            return d
    raise VerbatimError(f"工事のフォルダが無い: verbatim/{work}（--write --work {work} で作る）")


def summary(work: str) -> Path:
    """「要件のまとめ」1本を、工事のフォルダの逐語のファイル全部から作る（2026-09-29 まこさん指示）。

    1行＝要件1件（逐語の空でない行）。通し番号 R01… は、発言の時刻の順（古い発言から）。
    どのファイルも --verify を通らなければ止まる（fail-closed）。CC は文を書かない。
    """
    d = work_dir(work)
    metas = sorted(d.glob("*.meta.json"))
    if not metas:
        raise VerbatimError(f"逐語のファイルが1つも無い: {d.relative_to(ROOT)}")
    items = []
    for mp in metas:
        name = mp.name[: -len(".meta.json")]
        ok, why = verify(name, d)
        if not ok:
            raise VerbatimError(f"要件のまとめを作れない（照らしが通らない）: {why}")
        m = json.loads(mp.read_text(encoding="utf-8"))
        who = set(m.get("who") or [])
        speaker = ("まこさんの発言" if who == {"まこさん"} else
                   "まこさんが OK した CC の文" if who == {"CC"} else "まこさんの発言と CC の文")
        t0 = (m.get("time") or [""])[0]
        items.append((t0, name, speaker, m))
    items.sort(key=lambda x: x[0])
    body = ["| 通し番号 | 逐語の行 | 話し手 | 文（逐語） |", "|---|---|---|---|"]
    gone = ["| 逐語の行 | 話し手 | 文（逐語） | 外した理由 |", "|---|---|---|---|"]
    n = 0
    n_gone = 0
    # ★2026-09-29＝まこさんが OK した CC の案のうち【項目の番号】の見出しの下の行は、設計の中身（設計書の道具が
    #   その項目へ そのまま写す）なので、ここでは1行ずつ並べず「どの見出しに何行」の まとめにする（読みやすさ）。
    design: list = []
    key_re = re.compile(r"^\s*【([^】]+)】")
    for _t0, name, speaker, m in items:
        drop = list(m.get("drop") or [])
        is_cc = set(m.get("who") or []) == {"CC"}
        cur = None
        for vid, ln in lines(name, d):
            km = key_re.match(ln) if is_cc else None
            if km:
                cur = km.group(1).split()[0]
                design.append([f"{name}", cur, vid.rsplit(":", 1)[-1], vid.rsplit(":", 1)[-1], 1])
                continue
            if cur is not None:
                design[-1][3] = vid.rsplit(":", 1)[-1]
                design[-1][4] += 1
                continue
            why = drop_reason(ln, vid.rsplit(":", 1)[-1], drop)
            if why:
                n_gone += 1
                gone.append(f"| `{vid}` | {speaker} | {ln.replace('|', '／')} | {why} |")
                continue
            n += 1
            body.append(f"| R{n:02d} | `{vid}` | {speaker} | {ln.replace('|', '／')} |")
    if n_gone == 0:
        gone.append("| — | — | 無し | — |")
    src = ["| 逐語のファイル | 話し手 | 記録のファイル | 発言の uuid | 時刻（UTC） | 本文の sha256 の先頭 |",
           "|---|---|---|---|---|---|"]
    for _t0, name, speaker, m in items:
        src.append(f"| `{name}.txt` | {speaker} | `{Path(str(m.get('session', ''))).name}` "
                   f"| {'・'.join(m.get('uuids') or [])} | {'・'.join(m.get('time') or [])} | {str(m.get('sha256', ''))[:16]} |")
    text = "\n".join([
        f"# 要件のまとめ｜工事 `{work}`",
        "",
        "**★この文書はプログラム（gen_verbatim.py --summary）が、逐語のファイルから作ります。手で書き換えない。**"
        "文は やり取りの記録の発言そのもので、CC は1文字も書いていません。"
        "照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <逐語のファイルの名前>`。",
        "",
        f"**要件＝全部で {n} 行**（逐語の空でない行を1行1件と数える・通し番号は発言の古い順）。"
        f"要件でない行 {n_gone} 行は、下の「外した行」に逐語のまま出す（消していない）。",
        "",
        *body,
        "",
        "## OK された設計の案（【項目の番号】の見出しごと・中身は設計書の同じ番号の項目に写る）",
        "",
        "| 逐語のファイル | 見出し | 行 | 設計書に写るか |",
        "|---|---|---|---|",
        *([f"| `{f}` | 【{k}】 | {a}〜{b}（{c} 行） | "
           + ("写る" if [x[0] for x in design if x[1] == k][-1] == f
              else f"写らない（後の案 {[x[0] for x in design if x[1] == k][-1]} で置き換えた）") + " |"
           for f, k, a, b, c in design] or ["| — | 無し | — | — |"]),
        "",
        "## 外した行（要件でない行・消していない・逐語のまま）",
        "",
        "外し方は2つ＝道具の決まり（表の区切りの行・返信の終わりの「書き換えたファイル」の行）と、"
        "CC が逐語を書くときに行の番号で指定したもの（--drop・CC は文を書かず番号を選ぶだけ）。",
        "",
        *gone,
        "",
        "## 出どころ（どの記録の、どの発言から写したか）",
        "",
        *src,
        "",
    ])
    out = d / SUMMARY_MD
    out.write_text(f"{SUMMARY_MARK}{_sha(text)[:16]} gen_verbatim.py が自動生成＝手で書き換えない -->\n" + text,
                   encoding="utf-8")
    return out


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
    ap.add_argument("--work", default="", help="工事名（設計書の ARC の iter）＝--write の置き場 verbatim/<工事名>/")
    ap.add_argument("--summary", default="", help="工事名＝その工事の逐語のファイル全部から「要件のまとめ」1本を作る")
    ap.add_argument("--drop", default="", help="--write と一緒に＝要件のまとめで外す行の番号（V05,V08 の形）")
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
            p = write(a.write, uu, a.session, work=a.work or None,
                      drop=[x for x in a.drop.split(",") if x.strip()])
            print(f"✅ 書いた: {p.relative_to(ROOT)}（uuid {len(uu)} 件・行 {len(lines(a.write if '/' in a.write else f'{a.work}/{a.write}'))} 行）")
            return 0
        if a.summary:
            p = summary(a.summary)
            print(f"✅ 要件のまとめを書いた: {p.relative_to(ROOT)}（{sum(1 for ln in p.read_text(encoding='utf-8').splitlines() if ln.startswith('| R'))} 行）")
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
