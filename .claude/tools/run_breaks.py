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


def expect_of(name: str) -> tuple:
    """壊すプログラムの宣言（期待する終了コードと、その意味）を読む。

    ★2026-09-08（next_step §6 の159番・監査 cp29 の §4-2 と §5-5）
      監査の逐語＝「あとで記録だけを読む人は、#12 を『壊したら検査が落ちた』と読みます。
        実際に起きたのは『壊したら土台ゲートが通った』です。**意味が反対です。**」
      直す前＝合格の決め方が「終了コードが 0 以外」の1つだけだった。
        11本は「検査が落ちる」＝0 以外で意味が合っていたので、誰も気づかなかった。
        12本目（b51）は向きが反対なので、記録も表示も逆の意味になっていた。
        さらに、中で異常が起きた終了コード（lib.sh の 99＝控えから戻せなかった）も
        「止まった」に数えていた＝b51 の「正しい成功」の 1 と見分けが付かなかった。
      直した後＝壊すプログラムが自分で「期待する終了コードと、その意味」を宣言し、
        この道具がそれと照らす。**宣言が無ければ止める（fail-closed）。**

    書き方（.sh の先頭・#! の次あたり）
      # EXPECT_RC: 1
      # MEANS: その検査が落ちた（守りが働いた）

    戻り＝(期待する終了コード or None, 意味の文, 読めなかった理由 or "")
    ★読めなかったときは、呼ぶ側が止める（この関数は例外を投げない）。
    ★限界（正直に）＝宣言した値が正しいかは見ない。CC が実測から書き写す。
      間違った値を書くと、その壊すプログラムは永久に不合格になる（合格側には倒れない）。
    """
    p = BREAKS_DIR / name
    if not p.exists():
        return None, "", f"壊すプログラムがありません: {p}"
    rc = means = None
    for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines()[:40]:
        m = re.match(r"^#\s*EXPECT_RC:\s*(-?\d+)\s*$", ln)
        if m and rc is None:
            rc = int(m.group(1))
        m = re.match(r"^#\s*MEANS:\s*(.+?)\s*$", ln)
        if m and means is None:
            means = m.group(1)
    if rc is None:
        return None, "", f"宣言 # EXPECT_RC: がありません: {name}"
    if not means:
        return None, "", f"宣言 # MEANS: がありません: {name}"
    return rc, means, ""


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
    # ★2026-09-07（next_step §6 の150番・設計書 iter="approval-audit-plumbing-20260907"）
    #   ＝壊すプログラムを走らせて終了コードを画面に出すだけの口。
    #   **記録も凍結も1バイトも書かない。**
    #   なぜ要るか（実測）＝承認より後にコードを直したとき、壊すプログラムを走らせ直せるのが
    #     まこさんだけだった（この道具は土台ゲートの通す一覧に入っていない）。
    #     2026-09-07 に監査 cp27 が、これを理由に「壊し方を1文字も変えずに写した
    #     再現プログラム」で代行した（別枠 6-2）。
    #   ★土台ゲートは、この旗が在るときだけ この道具を通す
    #     （require_acceptance_before_impl.sh の _readonly_seg の枝。--freeze・--out が在れば止める）。
    ap.add_argument("--measure-only", action="store_true")
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
        # ★2026-09-08（159番）＝走らせる前に宣言を読む。
        #   **ファイルは在るのに宣言が無い**ときだけ止める（fail-closed）。
        #   ★ファイルがまだ無いときは止めない＝今までどおり run_one が None を返し、
        #     その行は「未着手」のまま残る。
        #     これを止めると、新しい壊すプログラムを作る流れ
        #     （①承認で書く権利をもらう ②書く ③承認で測る）が塞がる。
        #     実測（2026-09-08）＝止める形にしたら、b52 を書く前の承認が取り消された。
        exp, means, why = expect_of(r["script"])
        if why and (BREAKS_DIR / r["script"]).exists():
            print(f"[STOP] 壊すプログラムの宣言を読めません（159番）: {why}", file=sys.stderr)
            print("  ★書き方＝.sh の先頭に # EXPECT_RC: <数字> と # MEANS: <その意味> の2行",
                  file=sys.stderr)
            return 2
        code, note = run_one(r["script"], depth)
        r["code"], r["note"] = code, note
        r["expect"], r["means"] = exp, means
        r["match"] = (code == exp)
        n_run += 1
        if r["match"]:
            n_stop += 1
        mark = "✅ 期待どおり" if r["match"] else "❌ 期待と違う"
        print(f"   {mark}  #{r['no']:>3}  {r['script']}  rc={code}（期待 {exp}）")
        print(f"        意味＝{means}")

    after = {p.name: sha(p) for p in break_scripts()}
    if before != after:
        print("[STOP] 走らせた後で、壊すプログラム自身が変わっています"
              "（元に戻していない）", file=sys.stderr)
        return 2

    # ★2026-09-07（150番）＝測るだけの口は、ここで終わる（記録も凍結も書かない）。
    if a.measure_only:
        print(f"   🧪 測るだけ（記録は書きません）: 止まった {n_stop}/{n_run}")
        return 0

    iter_name = a.iter_name or "unknown"
    out = pathlib.Path(a.out) if a.out else (ARCHIVE / f"{iter_name}.breaks.json")
    write_record(out, iter_name, rows)
    print(f"   🧪 壊して確かめた件数: {n_stop}/{n_run} → {out.name}")
    return 0


def write_record(out: pathlib.Path, iter_name: str, rows: list) -> None:
    """壊すプログラムの終了コードを、設計書の控えの隣に記録として書く。

    ★2026-09-07（next_step §6 の146番・設計書 iter="approval-audit-plumbing-20260907"）
      ＝承認スクリプトの「済」の付け方は、次の2つが**両方**そろったときだけ書く形にしてある
      （approve_impl.sh:414-424）。
        ①壊すプログラムの終了コードが 0 以外 ②その行の条件のコマンドが rc=0
      ①の材料が、ここで書く記録（<iter>.breaks.json）。
      ★この直し自体を守る完成の条件が1件も無かった（監査 cp26 の別枠の指摘3）。
      だから、書く処理を関数に切り出して番人 T8 で試せるようにした
      （承認スクリプトを直に走らせると、本物の承認の印を書いてしまうため）。
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(
        {"_なにこれ": ("完成の条件の壊すプログラムを、承認のときに機械が走らせた記録。"
                        "match が真の行だけ「済」にできる（監査 cp16 の E-12・cp29 の §5-5）"),
         "_欄の読み方": ("code＝実際の終了コード ／ expect＝壊すプログラムが宣言した期待値 ／ "
                         "means＝その値が意味すること ／ match＝一致したか。"
                         "★b51 だけは向きが裏返っている（意味の文に書いてある）＝"
                         "1 は『検査が落ちた』ではなく『土台ゲートが通った』"),
         "iter": iter_name, "rows": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


SELF_TESTS = (
    ("T1", "表から壊すプログラムの欄を読める"),
    ("T2", "「—」の行は、済にできない印を付ける"),
    ("T3", "目印が無い設計書は 0件（＝呼ぶ側が止める）"),
    ("T4", "凍結が無ければ止める"),
    ("T5", "凍結と食い違えば止める"),
    ("T6", "凍結と合っていれば通る"),
    ("T7", "打ち消した縦棒を、列の区切りにしない（幽霊の行を作らない）"),
    # ★2026-09-07（next_step §6 の146番）＝承認の「済」の材料になる記録を、本当に書くか。
    ("T8", "壊すプログラムの終了コードを、記録のファイルへ書く（済の材料が残る）"),
    ("T9", "宣言（EXPECT_RC・MEANS）の無い .sh は、理由つきで読み取りを止める"),
    ("T10", "宣言が在れば、期待する終了コードと意味の文をそのまま読み取る"),
    ("T11", "期待と違う終了コードなら、記録の match が偽になる"),
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
            # ★T8（2026-09-07・146番）＝記録を本当に書くか（本物のファイルは触らない）
            _o8 = pathlib.Path(d) / "rec" / "t8.breaks.json"
            write_record(_o8, "t8", [{"no": "1", "script": "b01_x.sh", "code": 1}])
            _d8 = json.loads(_o8.read_text(encoding="utf-8")) if _o8.exists() else {}
            if (_d8.get("iter") != "t8"
                    or [r.get("code") for r in (_d8.get("rows") or [])] != [1]):
                ng.append("T8")
            # ★T9・T10・T11（2026-09-08・159番）＝宣言の読み取りと、期待との照らし
            _t9 = BREAKS_DIR / "b90_no_decl.sh"
            _t9.write_text("#!/bin/bash\n# 宣言を書いていない見本\nexit 1\n", encoding="utf-8")
            if not expect_of("b90_no_decl.sh")[2]:
                ng.append("T9")
            _t10 = BREAKS_DIR / "b91_decl.sh"
            _t10.write_text("#!/bin/bash\n# EXPECT_RC: 2\n# MEANS: 見本の意味\nexit 2\n",
                            encoding="utf-8")
            _e10, _m10, _w10 = expect_of("b91_decl.sh")
            if _w10 or _e10 != 2 or _m10 != "見本の意味":
                ng.append("T10")
            _o11 = pathlib.Path(d) / "rec" / "t11.breaks.json"
            write_record(_o11, "t11", [{"no": "1", "script": "b91_decl.sh", "code": 1,
                                        "expect": 2, "means": "見本の意味", "match": False}])
            _d11 = json.loads(_o11.read_text(encoding="utf-8")) if _o11.exists() else {}
            if [r.get("match") for r in (_d11.get("rows") or [])] != [False]:
                ng.append("T11")
    finally:
        FROZEN, BREAKS_DIR = _kf, _kb

    for tag, what in SELF_TESTS:
        print(f"  {'❌' if tag in ng else '✅'} {tag} {what}")
    total = len(SELF_TESTS)
    print(f"  {'❌' if ng else '✅'} 番人 {total - len(ng)}/{total} pass")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
