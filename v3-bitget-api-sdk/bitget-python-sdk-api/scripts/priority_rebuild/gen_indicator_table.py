#!/usr/bin/env python3
"""gen_indicator_table.py — 指標1種につき1行の表（INDICATOR_TABLE）を、定義表（indicator_reference_diag.py）の中に書く・照らす。

工事 m2c15-single-source-20261022（指標の情報の置き場を1つにする・a＝役割・札・方向・性質・検査）。
まこさん指示（2026-10-22・逐語）＝「指標の情報をどこから読み込んで、どこに繋いでとか 全体の設計をし直せ」
  「とにかく、指標は１つデータから読み込むようにできないの？」。

何をするか
  定義表の中の目印（INDICATOR_TABLE_START〜END）の間に、指標1種につき1行の表を書く。欄＝
    役割（教科書の区分と出どころ）・札（役割から1対1）・方向（区分と読み方）・性質（いまの値）・性質（方向から）・値域・注記。
  値の出どころ（CC は値を書かない）＝
    役割＝資料の表 indicator_roles_thresholds.json（係の調べ）と、90種の札の正本 r1_role_map.json（R-1 の決定・封つき）。
    札＝役割の区分 → 札の1対1（CAT2LIN＝build_role_threshold_table.py の LIN2CAT の逆）。区分が2つ以上なら、いまの札に合う区分。
    方向・読み方・性質・値域・注記＝いまの表（最初は 2026-10-22 の定義表の行と札の表と observe_diag の値域の一覧から写した）。
      ★この4つは、この道具では変えない（値の判定は M-1）。--write は役割・札・性質（方向から）だけを作り直す。
使い方
  python3 scripts/priority_rebuild/gen_indicator_table.py --write            定義表の目印の間を書き直す（役割・札・性質（方向から）を資料から）
  python3 scripts/priority_rebuild/gen_indicator_table.py --write --add <種類> --houkou <区分＝読み方> --prop <性質>
      表に新しい種類の行を足して書き直す（監査 CP86 の修正6・まこさん「CCのおすすめでよい」＝A）。方向・性質の値は、
      新しい種類の設計書の実装の指示が、この引数で渡す。札は役割から決める（資料の表に役割が無ければ書かずに止まる）。
      ★順番＝先にこの口で表の行を足し、その後に定義表の行（_r）を足す（定義表を保存する瞬間の hook が --verify を掛けるため。
        定義表の行を先に足すと、表に無い種類で _r が止まり、保存が止まる）。行を足すまでは --verify の②が「表に在って定義表の行に無い」を出す。
  python3 scripts/priority_rebuild/gen_indicator_table.py --verify [--file <定義表の写し>]
      ①定義表の行（_r）が方向・性質を引数で受け取っていない ②行の種類と表の種類が同じ ③札の表（FAMILY_LINEAGE）が表から作られている
      ④表の役割と札が、資料から作り直した物と同じ ⑤札が LINEAGE_KINDS（10区分）の1つ
      ⑥目印の行の hash が、目印の間の本文の sha256 の先頭16文字と同じ（--write を通さずに表を書き替えていない＝方向・性質・値域・注記の手書きも止める・監査 CP86 の修正3）。
      1つでも違えば rc 1。
  python3 scripts/priority_rebuild/gen_indicator_table.py --count            数だけ出す（書かない）
限界（正直に）＝役割の読み取りが正しいかは見ない（資料の表の逐語と、まこさんの決定と、監査が見る）。
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
ROOT = SDK.parents[1]
ST = ROOT / ".claude/state"
IREF = HERE / "indicator_reference_diag.py"
ROLES = ST / "indicator_roles_thresholds.json"
R1MAP = ST / "indicator_review/r1_role_map.json"
START = "# ══ INDICATOR_TABLE_START"
END = "# ══ INDICATOR_TABLE_END"
CAT2LIN = {"向き": "トレンド", "強さ": "強さ", "勢い": "勢い", "行き過ぎ": "オシレーター",
           "値動きの幅": "ボラ", "出来高": "出来高", "位置": "構造・位置"}
HOUKOU2PROP = {"順張り値": "trend", "状態量": "none", "ボラ量": "vol", "反転サイン": "reversal"}   # 材料の検査1 の決まりと同じ
POS_MAX = 4                                     # _r の位置引数＝pat・family・teigi・ryugi（方向・性質は表から）


def read_block(text: str) -> tuple[dict, int, int]:
    a, b = text.find(START), text.find(END)
    if a < 0 or b < 0 or text.count(START) != 1 or text.count(END) != 1:
        raise SystemExit("❌ 定義表に INDICATOR_TABLE の目印が1組 無い")
    body = text[text.index("\n", a) + 1:b]
    m = re.search(r"^INDICATOR_TABLE: dict\[str, dict\] = (\{.*\})\s*$", body, re.S | re.M)
    if not m:
        raise SystemExit("❌ INDICATOR_TABLE の形が読めない")
    return ast.literal_eval(m.group(1)), a, b


def scan_rows(text: str) -> list[dict]:
    """定義表の行（_r(...) の呼び出し・ループの中も）を構文木で読む。種類の名前が f 文字列の行は family=None。"""
    out = []
    for c in ast.walk(ast.parse(text)):
        if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_r":
            fam = c.args[1].value if len(c.args) > 1 and isinstance(c.args[1], ast.Constant) else None
            out.append({"family": fam, "npos": len(c.args), "kw": [k.arg for k in c.keywords], "line": c.lineno})
    return out


def load_families(path: Path) -> list[str]:
    """定義表のファイルを読み込んで、登録された種類（REFS の family）を並びのまま返す（ループの中の登録も入る）。"""
    import contextlib
    import importlib.util
    import io
    import os
    import sys
    sys.path.insert(0, str(path.parent))
    cwd = os.getcwd()
    os.chdir(path.parent)
    try:
        spec = importlib.util.spec_from_file_location("_iref_under_check", path)
        mod = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
    finally:
        os.chdir(cwd)
    seen = []
    for e in mod.REFS:
        if e["family"] not in seen:
            seen.append(e["family"])
    return seen


def role_of(fam: str, roles: dict, r1map: dict) -> tuple:
    """資料の表と R-1 の正本から、役割の区分の一覧と出どころを読む。決まらなければ (None, 理由)。"""
    r = roles.get(fam)
    if r is None:
        return None, "資料の表に無い（オフ）"
    if fam in r1map:                                            # 同じ区分が2回 書いてある行（例＝MMI「強さ・強さ」）は、並びのまま1つにする
        return list(dict.fromkeys(r1map[fam]["出どころの区分"])), "R-1（封つき r1_role_map.json・" + str(r1map[fam].get("出どころ", "")) + "）"
    src = str(r.get("出どころの役割") or "")
    if src.startswith("係の調べ"):
        return list(dict.fromkeys(c for c in src.split("：", 1)[-1].split("・") if c)), "係の調べ（逐語✅）"
    if src.startswith("出どころのページの語の数"):
        return None, "語の数だけ（弱い）"
    return None, "無い"


def compute(cur: dict) -> dict:
    """いまの表（方向・読み方・性質・値域・注記）に、資料から役割・札・性質（方向から）を作り直して足す。"""
    roles = {r["種類"]: r for r in json.loads(ROLES.read_text(encoding="utf-8"))}
    r1map = {r["種類"]: r for r in json.loads(R1MAP.read_text(encoding="utf-8"))}
    out = {}
    for fam, t in cur.items():
        cats, src = role_of(fam, roles, r1map)
        lin = t["札"]
        if cats:
            cands = [CAT2LIN[c] for c in cats if c in CAT2LIN]
            if cands:
                lin = t["札"] if t["札"] in cands else cands[0]
        out[fam] = {"役割": {"区分": cats, "出どころ": src}, "札": lin,
                    "方向": dict(t["方向"]), "性質": t["性質"], "性質（方向から）": HOUKOU2PROP.get(t["方向"]["区分"]),
                    "値域": dict(t["値域"]), "注記": t.get("注記", "")}
    return out


def render(table: dict) -> str:
    lines = [f"{START} hash=@@HASH@@ gen_indicator_table.py が自動生成＝手で書き換えない（役割＝資料の表と r1_role_map.json・方向と性質と値域は M-1 で直すまで今の値）",
             "INDICATOR_TABLE: dict[str, dict] = {"]
    for fam, t in table.items():
        lines.append(f"    {fam!r}: {t!r},")                 # ★Python の定数（None・True）で書く＝ast.literal_eval で読み戻せる
    lines += ["}", END]
    body = "\n".join(lines[1:-1])
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    lines[0] = lines[0].replace("@@HASH@@", h)
    return "\n".join(lines)


def problems(text: str) -> list[str]:
    """--verify の①〜⑥。"""
    bad = []
    table, _a, _b = read_block(text)
    # ⑥＝目印の行の hash と、目印の間の本文（render と同じ作り方）の sha256 の先頭16文字を照らす（監査 CP86 の修正3）。
    #   ④は方向・性質・値域・注記を表そのものから写すので、その手書きは④では見えない＝⑥で止める。
    head_end = text.index("\n", _a)
    mh = re.search(r"hash=([0-9a-f]{16})", text[_a:head_end])
    body = text[head_end + 1:_b].rstrip("\n")
    if not mh or hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] != mh.group(1):
        bad.append("⑥目印の hash が本文と違う（--write を通さずに表を書き替えた＝方向・性質・値域・注記も、資料と --write で作り直す）")
    rows = scan_rows(text)
    over = [r for r in rows if r["npos"] > POS_MAX or any(k in ("houkou", "prop") for k in r["kw"])]
    if over:
        bad.append(f"①定義表の行が方向か性質を引数で受け取っている（{len(over)}行・例＝{over[0]['family']} {over[0]['line']}行目）。方向と性質は INDICATOR_TABLE の欄")
        return bad                                               # 引数が戻った定義表は、読み込むと _r が TypeError で落ちる＝読み込まずに①で止める（⑥は上で数えた）
    try:
        fams = load_families(Path(PATH_UNDER_CHECK))            # 読み込んで数える（ループの中の登録も入る）
    except (SystemExit, Exception) as e:                         # noqa: BLE001  _r が「表に無い」で止めた・読み込みで落ちた
        return bad + [f"②定義表を読み込めない: {type(e).__name__}: {e}"]
    miss = sorted(set(fams) - set(table))
    extra = sorted(set(table) - set(fams))
    if miss:
        bad.append(f"②定義表の行に在って表に無い種類 {len(miss)}: {miss[:10]}")
    if extra:
        bad.append(f"②表に在って定義表の行に無い種類 {len(extra)}: {extra[:10]}")
    lin_ok = False                                                # ③＝FAMILY_LINEAGE の代入の右辺が _lineage_from_table() の呼び出しであること（構文木で見る）
    for node in ast.parse(text).body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "FAMILY_LINEAGE":
            v = node.value
            lin_ok = isinstance(v, ast.Call) and getattr(v.func, "id", "") == "_lineage_from_table"
    if not lin_ok:
        bad.append("③札の表（FAMILY_LINEAGE）が手書きの辞書に戻っている（表から作る _lineage_from_table() を使う）")
    want = compute(table)
    diff = [f for f in table if table[f] != want.get(f)]
    if diff:
        bad.append(f"④表の中身が、資料から作り直した物と違う {len(diff)} 種（手で書き替えた・資料が変わった＝--write で作り直す）: {diff[:10]}")
    for f, t in table.items():
        if t["札"] not in LINEAGE_KINDS_FALLBACK:            # ★監査 CP86 の修正14＝直す前は「and t["札"] is None」で、札が None のときしか落ちなかった
            bad.append(f"⑤{f}: 札が10区分の1つでない（{t['札']!r}）")
    return bad


LINEAGE_KINDS_FALLBACK = ("トレンド", "強さ", "勢い", "オシレーター", "ボラ", "出来高", "ローソク", "構造・位置", "需給", "時間帯")
PATH_UNDER_CHECK = str(IREF)                                     # --file で写しに替わる（problems が読み込む相手）


def counts(table: dict) -> dict:
    c = {"種類": len(table), "役割あり": 0, "役割なし（語の数だけ）": 0, "役割なし（無い）": 0, "役割なし（オフ）": 0,
         "性質が方向の決まりと違う": 0, "方向の区分を決まりが読めない": 0}
    for t in table.values():
        src = t["役割"]["出どころ"]
        if t["役割"]["区分"]:
            c["役割あり"] += 1
        elif "語の数" in src:
            c["役割なし（語の数だけ）"] += 1
        elif "オフ" in src:
            c["役割なし（オフ）"] += 1
        else:
            c["役割なし（無い）"] += 1
        if t["性質（方向から）"] is None:
            c["方向の区分を決まりが読めない"] += 1
        elif t["性質（方向から）"] != t["性質"]:
            c["性質が方向の決まりと違う"] += 1
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--count", action="store_true")
    ap.add_argument("--file", default=str(IREF), help="定義表（写しを照らすとき）")
    ap.add_argument("--add", default=None, help="--write と一緒に使う＝表に足す新しい種類の名前（監査 CP86 の修正6）")
    ap.add_argument("--houkou", default=None, help="--add の種類の方向の欄（「区分＝読み方」の形・読み方が無ければ区分だけ）")
    ap.add_argument("--prop", default=None, help="--add の種類の性質の欄（trend・none・vol・reversal ほか）")
    a = ap.parse_args()
    p = Path(a.file)
    global PATH_UNDER_CHECK
    PATH_UNDER_CHECK = str(p)
    text = p.read_text(encoding="utf-8")
    if a.add is not None and (not a.write or not a.houkou or not a.prop):
        print("❌ --add には --write・--houkou・--prop が要る")
        return 2
    if a.write:
        table, s, e = read_block(text)
        if a.add is not None:
            if a.add in table:
                print(f"❌ --add: {a.add} はもう表に在る（値を変えるのは M-1 の決まりで）")
                return 1
            kubun, yomi = (a.houkou.split("＝", 1) + [""])[:2]
            table[a.add] = {"札": None, "方向": {"区分": kubun, "読み方": yomi}, "性質": a.prop,
                            "値域": {"有界": None, "分位": None}, "注記": ""}
            if compute({a.add: table[a.add]})[a.add]["札"] is None:
                print(f"❌ --add: {a.add} の役割が資料の表（または r1_role_map.json）に無いので、札が決まらない＝先に資料の表に役割を足す（書かない）")
                return 1
        new = compute(table)
        nt = text[:s] + render(new) + text[e + len(END):]
        p.write_text(nt, encoding="utf-8")
        print(f"✅ --write: {p}（{json.dumps(counts(new), ensure_ascii=False)}）")
        if a.add is not None:
            print(f"  --add: {a.add} の行を足した＝次に、定義表に {a.add} の行（_r）を足す（足すまで②が出る）")
        bad = problems(nt)
        for x in bad:
            print("  ❌", x)
        return 1 if bad else 0
    if a.count:
        print(json.dumps(counts(read_block(text)[0]), ensure_ascii=False, indent=1))
        return 0
    bad = problems(text)
    for x in bad:
        print("  ❌", x)
    print(("❌" if bad else "✅") + f" --verify: INDICATOR_TABLE（{p.name}）" + ("" if bad else "＝定義表の行・札の表・資料と合う"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
