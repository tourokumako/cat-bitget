#!/usr/bin/env python3
"""gen_hook_list.py — pdca_flow.md の §1 の hook の一覧を、settings.json の登録と hook_roles.json から作る（2026-09-17）

なぜ在るか（設計書 docs-autogen-next-step-pdca-20260917・まこさん指示 2026-09-17
「CCは確認せずミスを繰り返すので、手書きせざるをえないもの以外は自動生成にしてほしい」）
  pdca_flow.md の hook の一覧は手で書いていて、見出しの本数（実測 69本）が settings.json の登録（72本）と合わず、
  登録に在るのに一覧に1行も無い hook が19本 在った（2026-09-17 に数えた）。

使い方:
  python3 .claude/tools/gen_hook_list.py --import   # いまの §1 の表から hook_roles.json を作る（最初の1回・作り直しが1文字も違わないときだけ書く）
  python3 .claude/tools/gen_hook_list.py --write    # 元データと settings.json から §1 を作り、目印とハッシュ値で囲む
  python3 .claude/tools/gen_hook_list.py --verify   # 囲みが元データから作ったままか・本数が登録と同じか・登録の全部に行が在るか

決まり:
  ・名前・タイミング・matcher は settings.json が正本（pdca_flow.md の冒頭「実体が正」）。役割の文だけを hook_roles.json に書く。
  ・登録に在るのに役割が無い hook が1本でも在れば、書かずに止まる。
  ・hook_roles.json に在るのに登録が無い行は消さず、名前の欄に「（登録なし）」を足す（廃止した行の履歴を消さないため）。
  ・恒久71番＝文書を作る道具なので、壊すプログラムと自己テストは付けない。走らせて1回 確かめる。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PDCA = ROOT / ".claude" / "rules" / "pdca_flow.md"
ROLES = ROOT / ".claude" / "state" / "hook_roles.json"
SETTINGS = ROOT / ".claude" / "settings.json"

HEAD_PREFIX = "## 1. hook 一覧"
TABLE_HEAD = "| hook | タイミング | matcher | 役割 |"
START = "<!-- HOOK_LIST_START hash="
START_RE = re.compile(r"^<!-- HOOK_LIST_START hash=([0-9a-f]{16}) [^\n]*-->$")
END = "<!-- HOOK_LIST_END -->"
COUNT_RE = re.compile(r"実測 \d+本")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
NAME_RE = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")
KEYS = ("名前の欄", "タイミングの欄", "matcher の欄", "役割の欄")
NOT_REGISTERED = "（登録なし）"


def registered(settings_path: pathlib.Path = SETTINGS) -> dict[str, dict]:
    """settings.json の登録＝{名前: {"タイミング": [...], "matcher": [...]}}（登録の順）。"""
    d = json.loads(settings_path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for event, entries in (d.get("hooks") or {}).items():
        for ent in entries:
            m = ent.get("matcher") or ""
            for h in ent.get("hooks") or []:
                for name in re.findall(r"hooks/([a-z0-9_]+)\.sh", str(h.get("command") or "")):
                    r = out.setdefault(name, {"タイミング": [], "matcher": []})
                    if event not in r["タイミング"]:
                        r["タイミング"].append(event)
                    if m and m not in r["matcher"]:
                        r["matcher"].append(m)
    return out


def _cells(line: str) -> list[str] | None:
    if not (line.startswith("|") and line.endswith("|")):
        return None
    parts = CELL_SPLIT_RE.split(line)[1:-1]
    return parts if len(parts) == 4 else None


def find_region(lines: list[str]) -> tuple[int, int, bool]:
    """§1 の見出しから表の終わりまで（[始まり, 終わり)）。囲みの目印が在れば目印の行を含む。戻り＝(s, e, 囲み在り)。"""
    for i, ln in enumerate(lines):
        if START_RE.match(ln):
            e = next((j for j in range(i + 1, len(lines)) if lines[j] == END), None)
            if e is None:
                raise SystemExit(f"[hook_list] 始まりの目印は在るのに、終わりの目印 {END} が無い＝書かずに止まる")
            return i, e + 1, True
    s = next((i for i, ln in enumerate(lines) if ln.startswith(HEAD_PREFIX)), None)
    if s is None:
        raise SystemExit(f"[hook_list] 見出し『{HEAD_PREFIX}』が {PDCA.name} に無い")
    t = next((i for i in range(s, len(lines)) if lines[i] == TABLE_HEAD), None)
    if t is None:
        raise SystemExit(f"[hook_list] 表の見出しの行『{TABLE_HEAD}』が無い")
    e = t + 2
    while e < len(lines) and lines[e].startswith("|"):
        e += 1
    return s, e, False


def parse_region(region: list[str]) -> dict:
    """囲みの中（目印の行を除く）を元データにする。"""
    head = region[0]
    t = region.index(TABLE_HEAD)
    rows = []
    for ln in region[t + 2:]:
        c = _cells(ln)
        if c is None:
            raise SystemExit(f"[hook_list] 表の行を4つの欄に分けられない＝書かずに止まる: {ln[:80]}")
        rows.append(dict(zip(KEYS, c)))
    return {"見出し": head, "前": region[1:t], "見出しの行": TABLE_HEAD, "区切り": region[t + 1], "行": rows}


def names_in(cell: str) -> list[str]:
    return NAME_RE.findall(cell)


def render_region(roles: dict, reg: dict[str, dict] | None) -> list[str]:
    """元データから囲みの中を作る。reg=None なら読み込みの照らし（見出しの本数も行も元のまま）。"""
    head = roles["見出し"]
    if reg is not None:
        head = COUNT_RE.sub(f"実測 {len(reg)}本", head, count=1)
    out = [head, *roles["前"], roles["見出しの行"], roles["区切り"]]
    for r in roles["行"]:
        name = r["名前の欄"]
        tim = r.get("タイミングの欄")
        mat = r.get("matcher の欄")
        if reg is not None:
            ns = [n for n in names_in(name) if n in reg]
            if tim is None:
                tim = " " + " ／ ".join(dict.fromkeys(e for n in ns for e in reg[n]["タイミング"])) + " "
            if mat is None:
                ms = list(dict.fromkeys(m for n in ns for m in reg[n]["matcher"]))
                # ★縦棒は表の欄の区切りになるので、\| にする（2026-09-17・書き出して実測した）
                mat = " " + (" ／ ".join(m.replace("|", "\\|") for m in ms) if ms else "—") + " "
            if not ns and NOT_REGISTERED not in name and "登録" not in name + (tim or "") and "~~" not in name:
                name = name.rstrip() + NOT_REGISTERED + " "
        out.append("|" + "|".join([name, tim or "", mat or "", r["役割の欄"]]) + "|")
    return out


def _hash16(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:16]


def _atomic_write(path: pathlib.Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def missing_roles(roles: dict, reg: dict[str, dict]) -> list[str]:
    have = {n for r in roles["行"] for n in names_in(r["名前の欄"])}
    return [n for n in reg if n not in have]


def do_import() -> int:
    if ROLES.exists():
        print(f"❌ [hook_list --import] {ROLES} が既に在る＝上書きしない（元データを直して --write を使う）")
        return 1
    lines = PDCA.read_text(encoding="utf-8").split("\n")
    s, e, boxed = find_region(lines)
    region = lines[s + 1:e - 1] if boxed else lines[s:e]
    roles = parse_region(region)
    if render_region(roles, None) != region:
        print("❌ [hook_list --import] 作り直した表が いまの §1 と違う＝元データを書かない")
        return 1
    _atomic_write(ROLES, json.dumps(roles, ensure_ascii=False, indent=1) + "\n")
    reg = registered()
    miss = missing_roles(roles, reg)
    print(f"✅ [hook_list --import] {ROLES.name} を書いた＝表の行 {len(roles['行'])}／作り直した表は いまの §1 と1文字も違わない")
    print(f"   settings.json の登録 {len(reg)} 本のうち、表に行が無いもの＝{len(miss)} 本（--write の前に役割の文を足す）: {' '.join(miss)}")
    return 0


def do_write() -> int:
    roles = json.loads(ROLES.read_text(encoding="utf-8"))
    reg = registered()
    miss = missing_roles(roles, reg)
    if miss:
        print(f"❌ [hook_list --write] settings.json に登録が在るのに、{ROLES.name} に役割の行が無い hook が {len(miss)} 本＝書かない:")
        for n in miss:
            print(f"   ・{n}（タイミング {'／'.join(reg[n]['タイミング'])}・matcher {'／'.join(reg[n]['matcher']) or '—'}）")
        return 2
    lines = PDCA.read_text(encoding="utf-8").split("\n")
    s, e, _boxed = find_region(lines)
    body = render_region(roles, reg)
    box = [f"{START}{_hash16(body)} gen_hook_list.py が settings.json と {ROLES.name} から作った＝手で書き換えない -->",
           *body, END]
    new = lines[:s] + box + lines[e:]
    _atomic_write(PDCA, "\n".join(new))
    print(f"[hook_list --write] §1 を作った＝登録 {len(reg)} 本／表の行 {len(roles['行'])}")
    return do_verify()


def do_verify() -> int:
    ng: list[str] = []
    lines = PDCA.read_text(encoding="utf-8").split("\n")
    s, e, boxed = find_region(lines)
    reg = registered()
    if not ROLES.exists():
        print(f"❌ [hook_list --verify] 元データ {ROLES.name} が無い → `--import`")
        return 2
    roles = json.loads(ROLES.read_text(encoding="utf-8"))
    if not boxed:
        ng.append(f"§1 の表が目印で囲まれていない → `gen_hook_list.py --write`")
    else:
        m = START_RE.match(lines[s])
        body = lines[s + 1:e - 1]
        if m and m.group(1) != _hash16(body):
            ng.append(f"囲みのハッシュ値 {m.group(1)} と中身 {_hash16(body)} が違う＝手で書き換えた → 元データ {ROLES.name} を直して `--write`")
        if body != render_region(roles, reg):
            ng.append(f"囲みの中が、元データと settings.json から作ったものと違う → `--write`")
        cm = re.search(r"実測 (\d+)本", body[0]) if body else None
        if not cm or int(cm.group(1)) != len(reg):
            ng.append(f"見出しの本数（{cm.group(1) if cm else '無い'}）が settings.json の登録 {len(reg)} 本と違う → `--write`")
    miss = missing_roles(roles, reg)
    if miss:
        ng.append(f"登録に在るのに一覧に行が無い hook {len(miss)} 本: {' '.join(miss)} → {ROLES.name} に役割の行を足して `--write`")
    if ng:
        print(f"❌ [hook_list --verify] {len(ng)} 件:")
        for x in ng:
            print(f"   ・{x}")
        return 2
    print(f"✅ [hook_list --verify] 登録 {len(reg)} 本 ＝ 見出しの本数 ／ 表の行 {len(roles['行'])} ／ 登録の全部に行が在る ／ 囲みは元データから作ったまま")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="pdca_flow.md の §1 の hook の一覧を作る")
    ap.add_argument("--import", dest="do_import", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.do_import:
        return do_import()
    if a.write:
        return do_write()
    if a.verify:
        return do_verify()
    ap.error("--import / --write / --verify のどれかを指定してください")
    return 2


if __name__ == "__main__":
    sys.exit(main())
