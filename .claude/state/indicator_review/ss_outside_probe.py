#!/usr/bin/env python3
"""ss_outside_probe.py — 表（INDICATOR_TABLE）の外に、指標の情報を手で持っている所を全部数える（読むだけ・本物には書かない）。

まこさん（2026-10-23・逐語）＝「指標の情報を１つのデータに集約して、そこからしか指標の情報は取れない状態にするための修正」
  「完全に修正しろ」。ToDo の86番。

数える相手
  .py＝scripts/priority_rebuild（recipes を除く）・scripts/regime・.claude/tools・.claude/hooks・.claude/state/indicator_review の直下。
    ファイルの一番外（と関数の中）の代入のうち、右辺が辞書・組・一覧・集合の文字の並びで、次のどれかを持つ物。
      ①INDICATOR_TABLE の種類の名前を3つ以上 ②札の10区分を3つ以上 ③方向の区分（順張り値・状態量・ボラ量・反転サイン）を2つ以上
      ④役割の区分（向き・強さ・勢い・行き過ぎ・値動きの幅・出来高・位置）を3つ以上
    INDICATOR_TABLE そのものと、自分自身は数えない。
  .json＝scripts/priority_rebuild の直下と recipes・SDK/.claude/ratchet の直下。種類の名前を3つ以上 持つファイル（作る道具が在るかは docmap の「作る文書」で見る）。
使い方: python3 .claude/state/indicator_review/ss_outside_probe.py   （一覧を画面と ss_outside_probe.json に出す）
"""
import ast
import json
import re
from pathlib import Path

import os  # noqa: E402
ROOT = Path(os.environ.get("SS_ROOT", "/Users/tachiharamasako/Documents/GitHub/cat-bitget"))   # ★2026-10-23＝写しの一番上を渡すと、写しを数える
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PR = SDK / "scripts/priority_rebuild"
IREF = PR / "indicator_reference_diag.py"
HERE = Path(__file__).resolve().parent

# ★2026-10-31（工事 m2c15-indicator-redirect-20261031・やることの表 F-5）＝名前は読む口 indicators.py から読む（集約の要件定義書 R5）。
#   indicators.json を直に開かない。INDICATOR_TABLE からも読まない（読む口が無い・読めない・古い形なら、読む口が止める＝fail-closed）
import sys  # noqa: E402
sys.path.insert(0, str(PR / "indicators"))
import indicators as _ind  # noqa: E402  読む口（indicators.json を開くのはこのプログラムだけ）
FAMS = set(_ind.load().names("指標の記録")) | set(_ind.load().names("部品の記録"))
# ★2026-10-24（修正の1＝物差し・OK の返信 okd_plan5:V07〜V12）＝数える種類はオンの種類（まこさん 2026-10-23「指標はオンになってるやつのみにしろ」）
ON = set(json.loads((SDK / ".claude/ratchet/indicator_switch.json").read_text(encoding="utf-8"))["on"])
FAMS = FAMS & ON
LINS = {"トレンド", "強さ", "勢い", "オシレーター", "ボラ", "出来高", "ローソク", "構造・位置", "需給", "時間帯"}
HOUKOU = {"順張り値", "状態量", "ボラ量", "反転サイン"}
CATS = {"向き", "強さ", "勢い", "行き過ぎ", "値動きの幅", "出来高", "位置"}
SKIP_NAMES = {"INDICATOR_TABLE"}

py_files = sorted(PR.glob("*.py")) + sorted((SDK / "scripts/regime").glob("*.py")) \
    + sorted((ROOT / ".claude/tools").glob("*.py")) + sorted((ROOT / ".claude/hooks").glob("*.py")) \
    + sorted(HERE.glob("*.py"))
py_files = [p for p in py_files if p.resolve() != Path(__file__).resolve()]


def _rel(p: Path) -> str:
    """数える相手の名前（ROOT からの相対。写しを数えるときの、この道具の隣のファイルは本物の根から）。"""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p.relative_to(Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")))


def strings(node) -> list:
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def targets(node) -> str:
    ts = node.targets if isinstance(node, ast.Assign) else [node.target]
    out = []
    for t in ts:
        if isinstance(t, ast.Name):
            out.append(t.id)
        elif isinstance(t, ast.Attribute):
            out.append(t.attr)
        else:
            out.append(ast.unparse(t)[:40])
    return ",".join(out)


rows = []
for p in py_files:
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as e:
        rows.append(dict(file=_rel(p), line=0, name="（読めない）", why=str(e)[:80]))
        continue
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        if not isinstance(node.value, (ast.Dict, ast.Tuple, ast.List, ast.Set)):
            continue
        name = targets(node)
        if name in SKIP_NAMES:
            continue
        ss = set(strings(node.value))
        f, l, h, c = ss & FAMS, ss & LINS, ss & HOUKOU, ss & CATS
        why = []
        if len(f) >= 3:
            why.append(f"種類 {len(f)}")
        if len(l) >= 3:
            why.append(f"札 {len(l)}")
        if len(h) >= 2:
            why.append(f"方向 {len(h)}")
        if len(c) >= 3:
            why.append(f"役割 {len(c)}")
        if why:
            rows.append(dict(file=_rel(p), line=node.lineno, name=name, why="・".join(why),
                             sample=sorted(f)[:4] or sorted(l | h | c)[:4]))

dm = json.loads((SDK / ".claude/ratchet/docmap.json").read_text(encoding="utf-8"))
made = {d["文書"] for t in dm["body"]["tools"] for d in t["作る文書"]}
js_rows = []
# ★2026-10-23（209回目）＝.claude/state の直下・indicator_review・research の json も数える（直す前は数えず、
#   役割の正本 r1_role_map.json・役割の一覧 indicator_roles_thresholds.json・パラメータの表 indicator_params_*.json が漏れていた）
for p in sorted(PR.glob("*.json")) + sorted((PR / "recipes").glob("*.json")) + sorted((SDK / ".claude/ratchet").glob("*.json")) \
        + sorted((ROOT / ".claude/state").glob("*.json")) + sorted(HERE.glob("*.json")) + sorted((HERE / "research").glob("*.json")) \
        + sorted((HERE / "gemini_r1").glob("*.json")):
    if p.resolve() == (HERE / "ss_outside_probe.json").resolve():
        continue
    try:
        ss = set(strings(ast.parse(repr(json.loads(p.read_text(encoding="utf-8"))), mode="eval")))
    except Exception:                                     # noqa: BLE001
        continue
    f = ss & FAMS
    if len(f) >= 3:
        rel = _rel(p)
        js_rows.append(dict(file=rel, n=len(f), made="プログラムが作る" if rel in made else "手書き／作る道具が地図に無い"))

import contextlib   # noqa: E402
import io           # noqa: E402
import sys          # noqa: E402
sys.path.insert(0, str(PR))
with contextlib.redirect_stdout(io.StringIO()):
    import observe_diag as od   # noqa: E402
reg_keys = set(od.MATERIAL_FAMILIES)
reg_miss = sorted(reg_keys - FAMS)
print(f"計算の登録の鍵（MATERIAL_FAMILIES）{len(reg_keys)} のうち、表の種類の名前に無い鍵 {len(reg_miss)}: {reg_miss}")

# ★2026-10-24（修正の1）＝代入の外に在る指標の情報も数える（直す前は数えず、0件でも完成と言えなかった）
#   A＝定義表の _r(...) の呼び出し ／ B＝観察の道具の _reg(...) の呼び出し ／ C＝名前の型にパラメータの口が無い登録
#   （パラメータが計算の関数の既定値かライブラリの既定値＝コードの中）／ D＝表の外の指標の情報を読む行（構文木）
import os  # noqa: E402
_cwd = os.getcwd()
os.chdir(PR)
with contextlib.redirect_stdout(io.StringIO()):
    import indicator_reference_diag as iref  # noqa: E402
os.chdir(_cwd)


def _calls(path, fname):
    t = ast.parse(path.read_text(encoding="utf-8"))
    return [c for c in ast.walk(t) if isinstance(c, ast.Call) and getattr(c.func, "id", "") == fname]


r_calls = _calls(PR / "indicator_reference_diag.py", "_r")
reg_calls = _calls(PR / "observe_diag.py", "_reg")


def _fam_of_reg(tpl):
    import itertools
    for combo in itertools.product(["14", "2.0", "3", "0.5"], repeat=tpl.count("{}")):
        try:
            e, _p = iref.find(tpl.format(*combo))
        except SystemExit:
            return None
        if e:
            return e["family"]
    return None


reg_on = {rf: _fam_of_reg(tpl) for rf, (tpl, _d, _f) in od.MATERIAL_FAMILIES.items()}
reg_on = {rf: f for rf, f in reg_on.items() if f in ON}
code_params = sorted(f for rf, f in reg_on.items() if "{}" not in od.MATERIAL_FAMILIES[rf][0])
names_out = {r["name"] for r in rows} | {"INDICATOR_TABLE", "REFS", "FAMILY_LINEAGE", "MATERIAL_FAMILIES"}
json_out = {Path(r["file"]).name for r in js_rows}
read_lines = []
for p in py_files:
    try:
        t = ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        continue
    for n in ast.walk(t):
        hit = (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in names_out) \
            or (isinstance(n, ast.Attribute) and n.attr in names_out) \
            or (isinstance(n, ast.Constant) and isinstance(n.value, str) and any(j in n.value for j in json_out))
        if hit:
            read_lines.append(f"{_rel(p)}:{n.lineno}")
read_lines = sorted(set(read_lines))

# ★2026-10-24（ToDo の151番）＝E＝直書き（例＝engine_tuner_gen.py:4062 の "atr_14"）。直す前は数えていなかった。
#   数え方を2か所に書かないように、直す相手の一覧の道具（gen_fix_inventory.py）を走らせ、その「直書き」の行を数える
import subprocess  # noqa: E402
import sys as _sys  # noqa: E402
subprocess.run([_sys.executable, str(HERE / "gen_fix_inventory.py")], cwd=str(ROOT), check=True, capture_output=True, env={**os.environ, "IND_ROOT": str(ROOT)})   # ★写しを数えるときは、一覧も写しの一番上で作る（監査 CP95）
_inv = json.loads((HERE / "fix_inventory_20261024.json").read_text(encoding="utf-8"))
hard_lines = sorted({f"{r[0]}:{r[1]} {r[3]}" for r in _inv["py"] if r[2] == "直書き"})

for r in rows:
    print(f"{r['file']}:{r['line']}  {r['name']}  [{r['why']}]  例={r.get('sample', '')}")
print(f"\n.py の代入＝{len(rows)} 件（{len({r['file'] for r in rows})} ファイル）")
for r in js_rows:
    print(f"{r['file']}  種類 {r['n']}  {r['made']}")
print(f".json＝{len(js_rows)} 本")
print(f"A 定義表の _r(...) の呼び出し＝{len(r_calls)}")
print(f"B 観察の道具の _reg(...) の呼び出し＝{len(reg_calls)}（オンの種類に当たる登録 {len(reg_on)}）")
print(f"C パラメータがコードの中に在るオンの種類（名前の型に口が無い）＝{len(code_params)}")
print(f"D 表の外の指標の情報を読む行＝{len(read_lines)}（{len({x.rsplit(':', 1)[0] for x in read_lines})} ファイル）")
print(f"E 直書き（gen_fix_inventory.py の「直書き」の行）＝{len(hard_lines)}（{len({x.split(':', 1)[0] for x in hard_lines})} ファイル）")
total = len(rows) + len(js_rows) + len(r_calls) + len(reg_calls) + len(code_params) + len(read_lines) + len(hard_lines)
print(f"★表の外の合計＝{total}（完成＝0）")
(HERE / "ss_outside_probe.json").write_text(json.dumps(dict(py=rows, json=js_rows, r_calls=len(r_calls), reg_calls=len(reg_calls),
                                                             code_params=code_params, read_lines=read_lines, hard_lines=hard_lines, total=total),
                                                        ensure_ascii=False, indent=1), encoding="utf-8")
