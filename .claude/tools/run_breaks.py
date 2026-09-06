#!/usr/bin/env python3
"""run_breaks.py — 完成の条件の「壊すプログラム」を機械で走らせ、終了コードを控えに残す。

まこさん指名 2026-09-03（監査 cp16 の E-12・承認 36051934db6eede3）
監査の逐語
  「完成の条件の各行の壊し方をコマンドの文字列にし、承認スクリプトが実際に走らせて
    acceptance_archive/<iter>.breaks.json に終了コードを保存する。
    ✅ 済 は終了コードが0でないときだけ書ける」

なぜ要るか（実測・cp13〜cp16 で4回 続いた型）
  設計書の完成の条件の「経路」も「壊し方」も CC の自由記述だった。
  CC は18行すべてに「実経路」と書いたが、実際に走らせた証拠は1件も残っていなかった。
  監査 cp16 が実測すると、C-7① は動いておらず、C-2 は Bash 経由が8通りとも通った。
  ＝書くだけで済むなら、CC は毎回 書くだけで済ませる。
  だから「実装した」と文章で書けなくし、機械が走らせた終了コードだけを根拠にする。

やること（3つ）
  1. 設計書の完成の条件の表から「壊すプログラム」の欄を読み、1行ずつ走らせる
  2. 走らせる前と後で、触った全ファイルのハッシュ値を照らす。1つでも違えば rc=2
  3. 結果を {行番号, 壊すプログラム, 終了コード} の形で <iter>.breaks.json に書く

★壊すプログラムの凍結（まこさん指示 2026-09-03・監査 cp16 の E-12 の土台）
  走る前に、.claude/breaks/*.sh のハッシュ値を breaks_frozen.json と照らす。
  1本でも違えば rc=2。凍結が無いときも rc=2（監査 cp16 の E-9 と同じ考え方）。
  ＝CC が壊すプログラムを書き換えて、終了コードを好きな値にする道を塞ぐ。

★呼び合いを止める（まこさんの注意 2026-09-03）
  b14_breaks_tampered.sh は この道具から呼ばれ、その中で また この道具を呼ぶ。
  目印の環境変数 CAT_RUN_BREAKS_DEPTH を使い、中から呼ばれた回は凍結の照合だけして戻す。

使い方
  python3 .claude/tools/run_breaks.py --design <設計書> --iter <iter名> [--out <保存先>]
  python3 .claude/tools/run_breaks.py --freeze          # 壊すプログラムの凍結を作り直す
  python3 .claude/tools/run_breaks.py --selftest

限界（正直に書く）
  ①この道具自身を CC が書き換えれば無効にできる（承認ゲートの対象なので、承認が要る）
  ②壊すプログラムが「本当に測りたいものを測っているか」は、この道具には分からない
    ＝終了コードが 0 以外であることしか見ない。中身は監査が見る
  ③凍結の照合は「承認のときの版と同じか」だけ。承認の前に骨抜きにした版を凍結できる
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
BREAKS_DIR = ROOT / ".claude" / "breaks"
FROZEN = SDK / ".claude" / "ratchet" / "breaks_frozen.json"
ARCHIVE = SDK / ".claude" / "ratchet" / "acceptance_archive"
DESIGN = ROOT / ".claude" / "state" / "acceptance.md"

DEPTH_ENV = "CAT_RUN_BREAKS_DEPTH"
TIMEOUT_SEC = 120

AT_START = r"^<!--\s*ACCEPT_TABLE_START\s*-->\s*$(.*?)^<!--\s*ACCEPT_TABLE_END\s*-->\s*$"

# ★2026-09-06（監査 cp23 の X-7 後半）＝列がずれた行に付ける説明の頭。
#   ここを1か所に置いて、parse_table と main が同じ文字で照らす（2か所に書き写さない）。
COL_NG = "列の数が見出しと違う"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def break_scripts() -> list:
    """.claude/breaks/ の .sh を、名前の順で並べて返す。"""
    if not BREAKS_DIR.is_dir():
        return []
    return sorted(p for p in BREAKS_DIR.glob("*.sh") if p.is_file())


def freeze_breaks() -> dict:
    """壊すプログラムのハッシュ値を集めて返す（承認スクリプトが呼ぶ）。"""
    return {p.name: sha(p) for p in break_scripts()}


def check_frozen() -> list:
    """凍結と いまのハッシュ値を照らす。戻り＝食い違いの説明の一覧（空なら合っている）。

    ★凍結が無いときも「食い違い」として返す（監査 cp16 の E-9＝記録が無いときは止める）。
    """
    if not FROZEN.exists():
        return [f"壊すプログラムの凍結がありません: {FROZEN}"
                "（監査 cp16 の E-9＝記録が無いときは止める）"
                "／承認を1回 打つと作られます"]
    try:
        want = json.loads(FROZEN.read_text(encoding="utf-8"))
    except Exception as e:                                   # noqa: BLE001
        return [f"凍結が読めません: {FROZEN} ({e})"]
    want = {k: v for k, v in want.items() if not str(k).startswith("_")}
    now = freeze_breaks()
    ng = []
    for name in sorted(set(want) | set(now)):
        if name not in now:
            ng.append(f"凍結に在る壊すプログラムが実物にありません: {name}")
        elif name not in want:
            ng.append(f"凍結に無い壊すプログラムが増えています: {name}")
        elif want[name] != now[name]:
            ng.append(f"壊すプログラムが承認のときから変わっています: {name}"
                      f"（いま {now[name][:16]}… ／ 承認時 {want[name][:16]}…）")
    return ng


def parse_table(md_text: str) -> list:
    """設計書の完成の条件の表から {行番号, 壊すプログラム} を読む。

    ★読むのは機械が読む目印の中だけ（監査 cp15 の C-1）。
    """
    m = re.search(AT_START, md_text, re.S | re.M)
    if m is None:
        return []
    rows = []
    for ln in m.group(1).splitlines():
        s = ln.strip()
        if not s.startswith("|"):
            continue
        # ★2026-09-03（まこさん指示・設計書 §3.8）＝打ち消した縦棒は、列の区切りにしない。
        #   直す前＝欄の中に書いた縦棒（前に \ を付けたもの）で列がずれ、
        #   別の欄の文字を「壊すプログラムの名前」として拾い、記録に実在しない行が1つ 増えた。
        #   まこさんの逐語＝「これは『表の書き方の問題』ではありません。実際に起きたのは
        #     記録に実在しない行が1つ 増えたことです。…記録の信頼性の問題です。」
        #   実測＝記録21行のうち、名前が入っている行が 15（本当は 14）。画面の分母も狂っていた。
        s = s.replace("\\|", "\x00")
        cells = [c.strip().replace("\x00", "\\|") for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue
        rows.append(cells)
    if not rows:
        return []
    head = rows[0]
    i_no = next((i for i, c in enumerate(head) if c.strip() == "#"), 0)
    i_brk = next((i for i, c in enumerate(head) if "壊すプログラム" in c), -1)
    if i_brk < 0:
        return []
    n_col = len(head)
    out = []
    for cells in rows[1:]:
        no = cells[i_no] if i_no < len(cells) else ""
        # ★2026-09-06（監査 cp23 の X-7 後半・設計書 iter="x7-column-count-20260906"）
        #   ＝見出しと列の数が違う行は読まない。
        #   直す前は、欄の中に生の縦棒を書くと列がずれ、**別の欄の文字を
        #   「壊すプログラムの名前」として拾った**（実測＝m2c4-add-parts-20260905.breaks.json
        #   の 24-27行＝"no": "4" だけ "script": "実経路"）。
        #   2026-09-03 に打ち消した縦棒（\|）は区切りにしない直しを入れたが、
        #   生の縦棒は そのままずれていた。
        if len(cells) != n_col:
            out.append({"no": no, "script": None, "code": None,
                        "note": f"列の数が見出しと違う（見出し {n_col} 列／この行 {len(cells)} 列）"
                                "＝欄の中に生の縦棒を書いていないか（打ち消して書く）"})
            continue
        raw = cells[i_brk] if i_brk < len(cells) else ""
        name = raw.strip().strip("`")
        name = re.sub(r"（.*?）", "", name).strip().strip("`")
        if not name or name in ("—", "-", "―"):
            out.append({"no": no, "script": None, "code": None,
                        "note": "壊すプログラムが無い＝この行は済にできない"})
            continue
        out.append({"no": no, "script": name, "code": None, "note": ""})
    return out


def run_one(name: str, depth: int) -> tuple:
    """壊すプログラムを1本 走らせる。戻り＝(終了コード, 説明)。"""
    p = BREAKS_DIR / name
    if not p.exists():
        return None, f"壊すプログラムがありません: {p}"
    env = dict(os.environ)
    env[DEPTH_ENV] = str(depth + 1)
    try:
        r = subprocess.run(["bash", str(p)], capture_output=True, text=True,
                           timeout=TIMEOUT_SEC, env=env, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return None, f"時間切れ（{TIMEOUT_SEC}秒）: {name}"
    tail = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode, (tail[-1][:200] if tail else "")


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="完成の条件の壊すプログラムを機械で走らせる")
    ap.add_argument("--design", default=str(DESIGN))
    ap.add_argument("--iter", dest="iter_name")
    ap.add_argument("--out")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--check-frozen", action="store_true")
    ap.add_argument("--parse-only", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest()

    # ★2026-09-03（まこさん指示・設計書 §3.8 の2番）＝読むだけの口。
    #   表を読んで、拾った名前と「実物が在るか」を並べるだけ。
    #   **壊すプログラムを1本も走らせない**ので、呼び合いが起きない＝深さに関わらず動く。
    #   なぜ要るか＝これが無いと、§3.8 の完成の条件に壊すプログラムを書けない
    #   （run_breaks.py を壊すプログラムの中から呼ぶと、呼び合いを止める仕組みで
    #     測る前に戻るため）。まこさんの逐語＝「— にすると人が画面を見て確かめることに
    #     なります。この工事は『人が目で確かめる項目を完成条件に入れない』ためにやってきました。」
    #   ★限界（設計書 §9 の 1c）＝「読むだけ」という前提が本当かは、私は確かめていない。
    #     監査に確かめてもらう。
    if a.parse_only:
        md_path = pathlib.Path(a.design)
        if not md_path.exists():
            print(f"[STOP] 設計書がありません: {md_path}", file=sys.stderr)
            return 2
        rows = parse_table(md_path.read_text(encoding="utf-8"))
        if not rows:
            print("[STOP] 完成の条件の表に「壊すプログラム」の欄がありません", file=sys.stderr)
            return 2
        for r in rows:
            if not r["script"]:
                continue
            mark = "OK" if (BREAKS_DIR / r["script"]).exists() else "MISSING"
            print(f"{r['no']}\t{r['script']}\t{mark}")
        # ★2026-09-06（監査 cp23 の X-7 後半）＝列がずれた表は、読めたことにしない。
        bad = [r for r in rows if COL_NG in (r.get("note") or "")]
        if bad:
            print("[STOP] 完成の条件の表に、列の数が見出しと違う行があります"
                  "（監査 cp23 の X-7）", file=sys.stderr)
            for r in bad:
                print(f"  ❌ 行 {r['no']}: {r['note']}", file=sys.stderr)
            return 2
        return 0

    if a.freeze:
        FROZEN.parent.mkdir(parents=True, exist_ok=True)
        d = freeze_breaks()
        d["_なにこれ"] = ("承認の瞬間に凍結した、壊すプログラムのハッシュ値。"
                          "run_breaks.py が走る前に照らす（監査 cp16 の E-12）")
        FROZEN.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
        print(f"🧊 壊すプログラムを凍結しました: {len(d) - 1} 本 → {FROZEN.name}")
        return 0

    # ★凍結の照合は、深さに関わらず必ず行う
    ng = check_frozen()
    if ng:
        print("[STOP] 壊すプログラムが、承認のときの版と違います（監査 cp16 の E-12）",
              file=sys.stderr)
        for x in ng:
            print(f"  ❌ {x}", file=sys.stderr)
        return 2
    if a.check_frozen:
        print(f"✅ 壊すプログラムは承認のときのまま（{len(freeze_breaks())} 本）")
        return 0

    # ★呼び合いを止める（まこさんの注意 2026-09-03）
    depth = int(os.environ.get(DEPTH_ENV, "0") or "0")
    if depth > 0:
        print(f"✅ 凍結の照合だけ行いました（中から呼ばれた回・深さ {depth}）")
        return 0

    md_path = pathlib.Path(a.design)
    if not md_path.exists():
        print(f"[STOP] 設計書がありません: {md_path}", file=sys.stderr)
        return 2
    rows = parse_table(md_path.read_text(encoding="utf-8"))
    if not rows:
        print("[STOP] 完成の条件の表に「壊すプログラム」の欄がありません"
              "（監査 cp16 の E-12）", file=sys.stderr)
        return 2

    # ★2026-09-06（監査 cp23 の X-7 後半）＝本走でも、列がずれた表は読まずに止める。
    bad = [r for r in rows if COL_NG in (r.get("note") or "")]
    if bad:
        print("[STOP] 完成の条件の表に、列の数が見出しと違う行があります"
              "（監査 cp23 の X-7）", file=sys.stderr)
        for r in bad:
            print(f"  ❌ 行 {r['no']}: {r['note']}", file=sys.stderr)
        return 2

    before = {p.name: sha(p) for p in break_scripts()}
    n_run = n_stop = 0
    for r in rows:
        if not r["script"]:
            continue
        code, note = run_one(r["script"], depth)
        r["code"], r["note"] = code, note
        n_run += 1
        if code not in (0, None):
            n_stop += 1
        mark = "✅ 止まった" if code not in (0, None) else "❌ 止まらなかった"
        print(f"   {mark}  #{r['no']:>3}  {r['script']}  rc={code}")

    after = {p.name: sha(p) for p in break_scripts()}
    if before != after:
        print("[STOP] 走らせた後で、壊すプログラム自身が変わっています"
              "（元に戻していない）", file=sys.stderr)
        return 2

    iter_name = a.iter_name or "unknown"
    out = pathlib.Path(a.out) if a.out else (ARCHIVE / f"{iter_name}.breaks.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"_なにこれ": ("完成の条件の壊すプログラムを、承認のときに機械が走らせた記録。"
                        "終了コードが 0 以外の行だけ「済」にできる（監査 cp16 の E-12）"),
         "iter": iter_name, "rows": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"   🧪 壊して確かめた件数: {n_stop}/{n_run} → {out.name}")
    return 0


SELF_TESTS = (
    ("T1", "表から壊すプログラムの欄を読める"),
    ("T2", "「—」の行は、済にできない印を付ける"),
    ("T3", "目印が無い設計書は 0件（＝呼ぶ側が止める）"),
    ("T4", "凍結が無ければ止める"),
    ("T5", "凍結と食い違えば止める"),
    ("T6", "凍結と合っていれば通る"),
    ("T7", "打ち消した縦棒を、列の区切りにしない（幽霊の行を作らない）"),
)


def selftest() -> int:
    """わざと壊して止まるか試すテスト（本物のファイルは1つも触らない）。"""
    import tempfile
    ng = []
    body = ("<!-- ACCEPT_TABLE_START -->\n"
            "| # | 完成の条件 | 壊すプログラム | いまの状態 |\n"
            "|---|---|---|---|\n"
            "| 1 | あ | `b01_x.sh` | 未着手 |\n"
            "| 2 | い | `—`（※1） | 未着手 |\n"
            "<!-- ACCEPT_TABLE_END -->\n")
    rows = parse_table(body)
    if len(rows) != 2 or rows[0]["script"] != "b01_x.sh":
        ng.append("T1")
    if rows[1]["script"] is not None or "済にできない" not in rows[1]["note"]:
        ng.append("T2")
    if parse_table("| 1 | あ | `b01_x.sh` |\n") != []:
        ng.append("T3")

    # T7 ★打ち消した縦棒（欄の中に書いた縦棒）で列がずれないか
    #    直す前＝ここで「bash` ほか」のような、実在しない名前を拾っていた
    body7 = ("<!-- ACCEPT_TABLE_START -->\n"
             "| # | 完成の条件 | 壊すプログラム | いまの状態 |\n"
             "|---|---|---|---|\n"
             "| 19 | `base64 -d \\| bash` ほかを掛ける | `—`（※2） | 未着手 |\n"
             "<!-- ACCEPT_TABLE_END -->\n")
    r7 = parse_table(body7)
    if len(r7) != 1 or r7[0]["script"] is not None:
        ng.append("T7")

    global FROZEN, BREAKS_DIR
    _kf, _kb = FROZEN, BREAKS_DIR
    try:
        with tempfile.TemporaryDirectory() as d:
            BREAKS_DIR = pathlib.Path(d) / "breaks"
            BREAKS_DIR.mkdir()
            (BREAKS_DIR / "b01_x.sh").write_text("exit 1\n", encoding="utf-8")
            FROZEN = pathlib.Path(d) / "no_such_frozen.json"
            if not check_frozen():
                ng.append("T4")
            FROZEN = pathlib.Path(d) / "frozen.json"
            FROZEN.write_text(json.dumps({"b01_x.sh": "0" * 64}), encoding="utf-8")
            if not check_frozen():
                ng.append("T5")
            FROZEN.write_text(json.dumps(freeze_breaks()), encoding="utf-8")
            if check_frozen():
                ng.append("T6")
    finally:
        FROZEN, BREAKS_DIR = _kf, _kb

    for tag, what in SELF_TESTS:
        print(f"  {'❌' if tag in ng else '✅'} {tag} {what}")
    total = len(SELF_TESTS)
    print(f"  {'❌' if ng else '✅'} 番人 {total - len(ng)}/{total} pass")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
