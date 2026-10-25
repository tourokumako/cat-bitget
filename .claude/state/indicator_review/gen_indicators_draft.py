#!/usr/bin/env python3
"""gen_indicators_draft.py — ①集める：指標の情報を1つのデータ（scripts/priority_rebuild/indicators/indicators.json）に、
いまの置き場からプログラムで1回だけ写す（元のコードは1行も直さない・読むだけ）。

まこさん（2026-10-23）「指標の情報を１つのデータに集約して、そこからしか指標の情報は取れない状態にするための修正」。
工事 m2c15-single-source-fix-20261023 の設計書1（①集める）。やることの表の一覧 F-1〜F-8・4-4 処理の流れ・4-5 止まる条件・
4-8 作る物の形のとおりに作る。
写す元（4-4 の1〜9）
  1 INDICATOR_TABLE  2 定義表 REFS（_r・MAKO_R1 が足した mako を含む）  3 計算の登録 MATERIAL_FAMILIES（_reg）
  4 observe_config.json（material_params・material_first_hidden・古い鍵）  5 計算の関数の引数の既定値
  6 indicator_params_by_strategy.json・recipes/search_limits.json  7 indicator_switch.json
  8 表の外の辞書（INDUSTRY_MAP・TA_CLASS_MAP・EXT2・CONST_REGISTRY・_EXIT_LEVEL_CONST・V9_FAMILY_MAP・CAT2LIN・HOUKOU2PROP）
  9 資料の表・調べた結果と、直す相手の一覧（fix_inventory_20261024.md）の「①写す」の行の全部（どの行を読むかは一覧から読む）
比べるだけの相手＝materials.json（4-4 の10・値の食い違いの一覧が比べた相手）。
★2026-10-25（監査 CP88・まこさん「全部修正する」「ok」）
  修正10＝別枠の材料（レンジ幾何 RANGE_GEO_REF・需給 DEMAND_REF・時間帯 TIME_REF の13種）も、1種につき1つの記録を持つ（記録は 301＋13＝314種）。
  修正11＝閾値の代表の固定値（スキャル／デイトレ）と閾値の範囲の2つの欄を足す（23の欄）。値はまだどこにも無いので null（T-2・T-3 で埋める）。
使い方:
  python3 .claude/state/indicator_review/gen_indicators_draft.py            # 写して書く（もう在れば、同じなら書かずに終わり、違えば止まる＝1回だけ書く）
  python3 .claude/state/indicator_review/gen_indicators_draft.py --verify   # 書かずに、記録と写す元を1件ずつ比べる（違えば終わりのコード 1）
"""
import argparse
import ast
import contextlib
import copy
import inspect
import io
import itertools
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PR = SDK / "scripts/priority_rebuild"
ST = ROOT / ".claude/state"
HERE = Path(__file__).resolve().parent
OUT = PR / "indicators" / "indicators.json"                 # F-2＝書く先（作業場には書かない）
INV = HERE / "fix_inventory_20261024.md"                    # 直す相手の一覧（「①写す」の行＝写し漏れを確かめる相手）
FIELDS = ("名前", "列の名前の型", "計算の関数", "照合の関数・既知答え", "代表の固定値（スキャル／デイトレ）",
          "名前に出ない軸の最初の値", "列を作る値", "コードの中の既定値", "範囲", "役割・札・値域・注記", "方向・性質",
          "オン/オフ", "mako", "ライブラリとの対応", "出口の水準", "V9 の名前", "教科書の出どころ", "閾値の値", "閾値の文",
          "閾値の代表の固定値（スキャル／デイトレ）", "閾値の範囲",
          "食い違いの記録", "ほかの置き場の値")      # 4-8 の23の欄（F-4・CP88 の修正11 で2つ足した）
# 3-2 の11件目（まこさん 2026-10-24「ok」）＝方向から性質への対応の表に足す1行。いまの4つの対応（HOUKOU2PROP）に無い方向。
DECIDED_PROP = {"向きつき": dict(性質=["trend"], 出どころ="やることの表 3-2 の11件目（まこさん 2026-10-24「ok」）")}
# 写す元のうち、記録の決まった欄に入る置き場（ここに無い「①写す」の行は、代入の右辺を ast で開いて「ほかの置き場の値」に写す）
OWN = ("INDICATOR_TABLE", "REFS", "MATERIAL_FAMILIES", "INDUSTRY_MAP", "TA_CLASS_MAP", "EXT2",
       "_EXIT_LEVEL_CONST", "V9_FAMILY_MAP", "R1_KEEP_ON", "MAKO_R1", "CAT2LIN", "HOUKOU2PROP", "_r", "_reg")
JSON_PATH = {"indicator_params_by_strategy.json": ST / "indicator_params_by_strategy.json",
             "indicator_params_review.json": ST / "indicator_params_review.json",
             "indicator_roles_thresholds.json": ST / "indicator_roles_thresholds.json",
             "indicator_switch.json": SDK / ".claude/ratchet/indicator_switch.json",
             "observe_config.json": PR / "observe_config.json",
             "r1_role_map.json": HERE / "r1_role_map.json",
             "search_limits.json": PR / "recipes/search_limits.json"}
JSON_OWN = {"indicator_params_by_strategy.json": {"指標"}, "indicator_params_review.json": {"[]/種類", "[]/元にした種類"},
            "indicator_roles_thresholds.json": {"[]/種類"}, "indicator_switch.json": {"on", "off", "sources"},
            "observe_config.json": {"material_params", "material_first_hidden"},
            "search_limits.json": {"material_param_ranges"}}


def jload(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                                   # noqa: BLE001
        raise SystemExit(f"❌ 写す元のファイルが読めない: {p}（{e}）")


sys.path.insert(0, str(PR))
_cwd = os.getcwd()
os.chdir(PR)
with contextlib.redirect_stdout(io.StringIO()):
    import indicator_reference_diag as iref  # noqa: E402
    import observe_diag as od  # noqa: E402
os.chdir(_cwd)
TABLE = iref.INDICATOR_TABLE
# CP88 の修正10＝別枠の材料（INDICATOR_TABLE の301種に無い種類）の定義の表。名前 → (群, 定義)。群はオン/オフの鍵と計算の関数を選ぶのに使う
EXTRA = {"レンジ幾何": iref.RANGE_GEO_REF, "需給": iref.DEMAND_REF, "時間帯": iref.TIME_REF}
def _carry(tb: dict) -> dict:
    """定義の表の「同上」を、表の並びで1つ前の行の値に置き換える（記録は1種ずつ読むので「同上」では読めない・CP89）。"""
    out, prev = {}, {}
    for nm, d in tb.items():
        e = {k: (prev.get(k, v) if v == "同上" else v) for k, v in d.items()}
        out[nm], prev = e, e
    return out


_dup = sorted(nm for nm in {n for tb in EXTRA.values() for n in tb} if sum(nm in tb for tb in EXTRA.values()) > 1)
if _dup:
    raise SystemExit(f"❌ 別枠の材料の名前が、別枠の表どうしで重なる: {_dup}")
EXTRA_OF = {nm: (grp, d) for grp, tb in EXTRA.items() for nm, d in _carry(tb).items()}


def module_assign(path: Path, name: str):
    """ファイルの一番外の代入 name の右辺を、ast で開いて値にする（import しない）。返り値＝(値, 行)。"""
    for n in ast.parse(path.read_text(encoding="utf-8")).body:
        tg = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == name for t in tg):
            return ast.literal_eval(n.value), n.lineno
    raise SystemExit(f"❌ 写す元が読めない＝{path.name} に {name} の代入が無い")


def plain(x):
    """json に書ける形にする（関数は名前、正規表現は型の文字、組は一覧）。"""
    if isinstance(x, re.Pattern):
        return x.pattern
    if callable(x):
        return getattr(x, "__name__", repr(x))
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set, frozenset)):
        return [plain(v) for v in (sorted(x, key=str) if isinstance(x, (set, frozenset)) else x)]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return repr(x)


def src_text(fn) -> str:
    try:
        return inspect.getsource(fn).strip()
    except (OSError, TypeError):
        return repr(fn)


def called(fn) -> list:
    """lambda の中で呼ぶ関数の名前（観察の道具と定義表の、一番外に在る関数だけ）。"""
    code = getattr(fn, "__code__", None)
    if code is None:
        return []
    out = []
    for nm in code.co_names:
        for m in (od, iref):
            f = getattr(m, nm, None)
            if inspect.isfunction(f) and nm not in out:
                out.append(nm)
    return out


def defaults(fn) -> dict:
    """呼ぶ関数の引数の既定値と、式の中に直に書いた数（4-8 の「コードの中の既定値」）。"""
    def sig(f):
        try:
            return {k: v.default for k, v in inspect.signature(f).parameters.items() if v.default is not inspect.Parameter.empty}
        except (TypeError, ValueError):
            return {}
    d = {}
    own = sig(fn)                                             # lambda 自身の引数（None＝呼ぶライブラリの既定値を使う）
    if own:
        d["<lambda>"] = plain(own)
    for nm in called(fn):
        ps = sig(getattr(od, nm, None) or getattr(iref, nm, None))
        if ps:
            d[nm] = plain(ps)
    code = getattr(fn, "__code__", None)
    gl = getattr(fn, "__globals__", {})
    codes, i = ([code] if code else []), 0                    # 中の lambda（例 HT_DCPHASE の _cyc に渡す lambda）も見る
    while i < len(codes):
        codes += [c for c in codes[i].co_consts if inspect.iscode(c)]
        i += 1
    names = [nm for c in codes for nm in c.co_names]
    for nm in names:                                          # 呼ぶライブラリの関数（例 _pta6.uo）の引数の既定値
        mod = gl.get(nm)
        if inspect.ismodule(mod):
            for attr in names:
                f = getattr(mod, attr, None)
                if callable(f) and not inspect.isclass(f):
                    ps = sig(f)
                    if ps:
                        d[f"{nm}.{attr}"] = plain(ps)
    nums = [k for c in codes for k in c.co_consts if isinstance(k, (int, float)) and not isinstance(k, bool)]
    return {"引数の既定値": d, "式の中の数": nums}


_RESOLVE: dict = {}


def resolve(s):
    """文字 → 種類の名前（表の名前そのもの、または列の名前を定義表の find でたどった種類）。当たらなければ None。"""
    if not isinstance(s, str):
        return None
    if s not in _RESOLVE:
        e, _p = iref.find(s)
        _RESOLVE[s] = s if (s in TABLE or s in EXTRA_OF) else (e["family"] if e else None)
    return _RESOLVE[s]


def kinds_in(v) -> set:
    if isinstance(v, str):
        k = resolve(v)
        return {k} if k else set()
    if isinstance(v, dict):
        return set().union(*(kinds_in(k) | kinds_in(x) for k, x in v.items())) if v else set()
    if isinstance(v, (list, tuple, set, frozenset)):
        return set().union(*(kinds_in(x) for x in v)) if v else set()
    return set()


def narrow(v, kind):
    """値のうち、その種類に当たる所だけを残す（辞書は鍵が種類なら値ごと・一覧は種類を含む要素ごと）。"""
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if resolve(k) == kind:
                out[k] = x
            elif kind in kinds_in(x):
                out[k] = narrow(x, kind)
        return out
    if isinstance(v, (list, tuple, set, frozenset)):
        return [x for x in v if (resolve(x) == kind if isinstance(x, str) else kind in kinds_in(x))]
    return v


def norm(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def decide(t: dict, role_table: dict, prop_table: dict):
    """札と性質を、2つの表から決める（F-7）。表に無い区分・方向は、止める物として返す。返り値＝(札, 性質の一覧, 無い区分, 無い方向)。
    札は、区分が在る種類だけを表から決める（区分が2つ以上なら、いまの札に合う区分＝gen_indicator_table.py の compute と同じ決め方）。"""
    cats = t["役割"]["区分"] or []
    miss_role = [c for c in cats if c not in role_table]
    cands = [role_table[c]["札"] for c in cats if c in role_table]
    lin = (t["札"] if t["札"] in cands else cands[0]) if cands else t["札"]
    hk = t["方向"]["区分"]
    miss_dir = [] if hk in prop_table else [hk]
    return lin, list(prop_table.get(hk, {}).get("性質", [])), miss_role, miss_dir


def nums(x):
    """パラメータの値の並びを、数の組の一覧にそろえる（値の食い違いの一覧と同じ比べ方）。"""
    if x is None:
        return None
    return sorted(tuple(v) if isinstance(v, list) else (v,) for v in (x if isinstance(x, list) else [x]))


# ══ 直す相手の一覧の「①写す」の行（4-4 の9）════════════════════════════════════════════════
def inventory() -> list:
    """全部の行の節（669行）・拾えなかった行の節・json の節・古い鍵の節から、「①写す」の行を読む。"""
    rows, sec = [], ""
    for ln in INV.read_text(encoding="utf-8").splitlines():
        if ln.startswith("## "):
            sec = ln[3:]
            continue
        if not ln.startswith("| ") or ln.startswith("|---"):
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if sec.startswith("全部の行") and len(c) == 5 and c[4].startswith("①写す"):
            rows.append(dict(節="全部の行", ファイル=c[0], 行=c[1], 中身=c[3]))
        elif sec.startswith("エージェントの行で") and len(c) == 7 and c[6].startswith("①写す"):
            rows.append(dict(節="拾えなかった行", ファイル=c[0], 行=c[1], 中身=c[3]))
        elif sec.startswith("json") and len(c) == 4 and c[3].startswith("①写す"):
            rows.append(dict(節="json", ファイル=c[0], 行="", 中身=c[1]))
        elif sec.startswith("observe_config.json の古い鍵") and len(c) == 3 and c[0] != "鍵":
            rows.append(dict(節="古い鍵", ファイル="observe_config.json", 行="", 中身=c[0]))
    return rows


def row_name(r) -> str:
    m = re.match(r"`?([A-Za-z_]\w*)", r["中身"])
    return m.group(1) if m else ""


_AST: dict = {}


def parsed(path: Path):
    if not path.exists():
        raise SystemExit(f"❌ 写す元のファイルが読めない: {path}")
    if path not in _AST:
        text = path.read_text(encoding="utf-8")
        _AST[path] = (text, ast.parse(text))
    return _AST[path]


def in_selftest(r) -> bool:
    """その行が、自己テストの関数（一番外の関数で、名前が selftest で始まる物）の中か。
    見本は記録に写す物ではない（worklog 20261024:357 の決定）。"""
    _text, tree = parsed(PR / r["ファイル"])
    lo = int(re.split(r"[-〜]", r["行"])[0])
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("selftest")
               and n.lineno < lo <= n.end_lineno for n in tree.body)


def row_kind(r) -> str:
    """その行が、記録のどの欄で写されるか（決まった欄・json・古い鍵・自己テストの見本・ほかの置き場）。"""
    if r["節"] == "古い鍵":
        return "古い鍵"
    if r["節"] == "json":
        return "json"
    if "設定の鍵から読まない" in r["中身"]:
        return "コードの中の既定値"
    if row_name(r) in OWN:
        return "決まった欄"
    return "自己テストの見本" if in_selftest(r) else "ほかの置き場"


def code_copy(r) -> list:
    """「①写す」の行の置き場を ast で開いて写す。返り値＝[{置き場, 名前, 値, 種類}]。名前が行に無ければ止まる（4-5）。"""
    text, tree = parsed(PR / r["ファイル"])
    lines = text.splitlines()
    lo, hi = (int(x) for x in (re.split(r"[-〜]", r["行"]) + [r["行"]])[:2])
    name = row_name(r)
    # 行の範囲の中で始まる置き場（文・関数の引数）のうち、一番外の物だけ（入れ子の中の文は、外の物の値に入っている）
    cand = [n for n in ast.walk(tree) if isinstance(n, (ast.stmt, ast.keyword)) and lo <= getattr(n, "lineno", 0) <= hi]

    def inside(n, m):
        if m is n or not (m.lineno <= n.lineno and n.end_lineno <= m.end_lineno):
            return False
        sm, sn = m.end_lineno - m.lineno, n.end_lineno - n.lineno
        return sm > sn or (sm == sn and isinstance(m, ast.stmt) and isinstance(n, ast.keyword))
    starts = sorted((n for n in cand if not any(inside(n, m) for m in cand)), key=lambda n: n.lineno)
    end = max([hi] + [n.end_lineno for n in starts])
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             and n.lineno <= lo <= n.end_lineno]
    if name not in "\n".join(lines[lo - 1:end]) and name not in funcs:
        raise SystemExit(f"❌ 直す相手の一覧の置き場に、代入が見つからない（行がずれた・名前が変わった）: {r['ファイル']}:{r['行']} {name}")
    out = []
    for n in starts:
        val = None
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.keyword)) and getattr(n, "value", None) is not None:
            with contextlib.suppress(ValueError, SyntaxError, TypeError):
                val = ast.literal_eval(n.value)
        if val is None:
            val = "\n".join(lines[n.lineno - 1:n.end_lineno])
            strs = [c.value for c in ast.walk(n) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
            kinds = kinds_in(strs)
        else:
            kinds = kinds_in(val)
        tg = (n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else [])
        nm = "・".join(ast.unparse(t) for t in tg) or (n.arg if isinstance(n, ast.keyword) else name)
        out.append(dict(置き場=f"{r['ファイル']}:{n.lineno}", 名前=nm, 値=plain(val), 種類=sorted(kinds)))
    if not out:
        val = "\n".join(lines[lo - 1:end])
        strs = re.findall(r"[\"']([^\"'\n]+)[\"']", val)
        out.append(dict(置き場=f"{r['ファイル']}:{lo}", 名前=name, 値=val, 種類=sorted(kinds_in(strs))))
    return out


def json_copy(r) -> list:
    """json の行のうち、決まった欄に入らない鍵を写す。"""
    js = jload(JSON_PATH[r["ファイル"]])
    out = []
    for key in [t.split()[0] for t in r["中身"].split("・")]:
        if key in JSON_OWN.get(r["ファイル"], set()):
            continue
        val = js if key.startswith("[]") else js.get(key)
        out.append(dict(置き場=f"{r['ファイル']} の {key}", 名前=key, 値=plain(val), 種類=sorted(kinds_in(val))))
    return out


# ══ 写す（4-4 の1〜11）═══════════════════════════════════════════════════════════════════════
def build() -> dict:
    cfg = jload(PR / "observe_config.json")
    mp, first_hidden = cfg.get("material_params", {}), cfg.get("material_first_hidden", {})
    lim = jload(PR / "recipes/search_limits.json").get("material_param_ranges", {})
    sw = jload(SDK / ".claude/ratchet/indicator_switch.json")
    on, off = set(sw.get("on", [])), set(sw.get("off", []))
    roles = {x["種類"]: x for x in jload(ST / "indicator_roles_thresholds.json")}
    bys = {x["種類"]: x for x in jload(ST / "indicator_params_by_strategy.json")["指標"]}
    rev = {x["種類"]: x for x in jload(ST / "indicator_params_review.json")}
    outw = {x["種類"]: x for i in range(1, 5) for x in jload(HERE / f"research/out_w{i}.json")}
    trole = {x["種類"]: x for x in jload(HERE / "research/threshold_role.json")}
    mat = jload(SDK / ".claude/ratchet/materials.json")["body"]
    mrows, mper = {x.get("名前"): x for x in mat.get("rows", [])}, mat.get("engine", {}).get("期間", {})
    cat2lin, ln_c = module_assign(PR / "gen_indicator_table.py", "CAT2LIN")
    h2p, ln_h = module_assign(PR / "gen_indicator_table.py", "HOUKOU2PROP")
    exit_lv, _ln = module_assign(PR / "engine_tuner_gen.py", "_EXIT_LEVEL_CONST")
    v9map, _ln = module_assign(PR / "gen_signal_families.py", "V9_FAMILY_MAP")

    # 2つの表（F-7）＝区分と対応は、プログラムの中に書かず、いまの値から1回だけ写す
    role_table = {k: dict(札=v, 出どころ=f"gen_indicator_table.py:{ln_c} の CAT2LIN") for k, v in cat2lin.items()}
    prop_table = {k: dict(性質=[v], 出どころ=f"gen_indicator_table.py:{ln_h} の HOUKOU2PROP") for k, v in h2p.items()}
    prop_table.update(copy.deepcopy(DECIDED_PROP))

    # 3 計算の登録 → 種類（F-5＝名前の違う種類も、表の名前1つにそろえる。つながらない登録が在れば止まる）
    regs, unmapped = {}, []
    for rf, (tpl, directional, fn) in od.MATERIAL_FAMILIES.items():
        fam = None
        for combo in itertools.product(["14", "2.0", "3", "0.5"], repeat=tpl.count("{}")):
            fam = resolve(tpl.format(*combo))
            if fam:
                break
        if fam is None:
            unmapped.append(rf)
            continue
        regs.setdefault(fam, []).append((rf, tpl, directional, fn))
    if unmapped:
        raise SystemExit(f"❌ 計算の登録の名前が、INDICATOR_TABLE の名前1つにつながらない: {unmapped}")
    refs = {}
    for e in iref.REFS:
        refs.setdefault(e["family"], []).append(e)

    # 4 列を作る値＝いまのカタログの列を、定義表の find でたどった値。出どころの鍵は、鍵を1つずつ空にして列が減る種類で決める
    def cols(c):
        got = {}
        for nm, _f, _d in od.build_catalog(c):
            e, p = iref.find(nm)
            if e:
                got.setdefault(e["family"], set()).add(tuple(p or ()))
        return got
    base = cols(cfg)
    cfg0 = copy.deepcopy(cfg)
    cfg0["material_params"] = {}
    cfg0["drop_columns"] = type(cfg0.get("drop_columns", []))()
    base0 = {k: len(v) for k, v in cols(cfg0).items()}
    keydep = {}
    for k, v in cfg0.items():
        if k.startswith("_") or k in ("material_params", "drop_columns") or not isinstance(v, (list, dict)) or not v:
            continue
        c2 = copy.deepcopy(cfg0)
        c2[k] = type(v)()
        try:
            now = cols(c2)
        except (Exception, SystemExit):                      # noqa: BLE001  空にすると止まる鍵は、その種類の出どころにしない
            continue
        for f, n in base0.items():
            if len(now.get(f, ())) < n:
                keydep.setdefault(f, []).append(k)

    v9_other = getattr(od, "_V9_LABEL_TO_FAMILIES", {})
    ta_names = set(iref.TA_CLASS_MAP)
    recs, unknown_role, unknown_dir = {}, [], []
    for f in sorted(TABLE):
        t = TABLE[f]
        fr, fg = refs.get(f, []), regs.get(f, [])
        lin, props, miss_role, miss_dir = decide(t, role_table, prop_table)
        if miss_role:
            unknown_role.append((f, miss_role))
        if miss_dir:
            unknown_dir.append((f, miss_dir[0]))
        mreg = [rf for rf, *_x in fg]
        src_keys = ((["observe_config.json の material_params"] if (f in mp or any(x in mp for x in mreg)) else [])
                    + keydep.get(f, [])) or ["計算の関数の中（設定の鍵から読まない）"]
        b, rv, ro = bys.get(f) or {}, rev.get(f) or {}, roles.get(f) or {}
        conflicts = []

        def conflict(field, chosen, where, others, skip_empty=True):
            """選んだ値と違う置き場の値を残す（選んだ値が空のときは比べない＝値の食い違いの一覧と同じ比べ方）。"""
            if skip_empty and chosen in (None, "", []):
                return
            got = {k: v for k, v in others.items() if v not in (None, "", []) and norm(v) != norm(chosen)}
            if got:
                conflicts.append(dict(欄=field, 選んだ値=chosen, 選んだ置き場=where, 選ばなかった=got))

        conflict("系統", lin, "INDICATOR_TABLE の札（役割の区分の表で決めた）",
                 {"roles の今の系統": ro.get("今の系統"), "by_strategy の系統": b.get("系統"), "review の系統": rv.get("系統"),
                  "materials の系統": (mrows.get(f) or {}).get("系統")})
        made = sorted(base.get(f, set()))
        conflict("列を作る値", nums([list(x) for x in made]), "いまのカタログの列（observe_config.json）",
                 {"observe_config の material_params": nums(mp.get(f)), "by_strategy の今の値": nums(b.get("今の値")),
                  "review の今のパラメータの組": nums(rv.get("今のパラメータの組")), "materials の期間": nums(mper.get(f))})
        conflict("範囲", [[d.get("lo"), d.get("hi")] for d in lim.get(f) or []] or None, "search_limits.json の material_param_ranges",
                 {"by_strategy の範囲": [[d.get("下限"), d.get("上限")] for d in b.get("範囲") or []]}, skip_empty=False)
        state = "オン" if f in on else "オフ" if f in off else "どちらにも無い"
        eng = (mrows.get(f) or {}).get("engine_tuner")
        if state == "オン" and (eng is None or not str(eng).startswith("選べる")):
            conflicts.append(dict(欄="オン/オフ", 選んだ値=state, 選んだ置き場="indicator_switch.json",
                                  選ばなかった={"materials の engine_tuner": eng}))
        conflict("性質", props, "方向から性質への対応の表", {"INDICATOR_TABLE の性質": [t["性質"]] if t["性質"] else None})
        v9 = sorted(lab for lab, fams in v9map.items() if f in fams)
        conflict("V9 の名前", v9, "gen_signal_families.py の V9_FAMILY_MAP",
                 {"observe_diag.py の _V9_LABEL_TO_FAMILIES": sorted(lab for lab, fams in v9_other.items() if f in fams)},
                 skip_empty=False)
        ta_have = sorted(c for c, ks in iref.TA_CLASS_MAP.items() if f in ks)
        ta_used = sorted({nm for e in fr for nm in getattr(getattr(e.get("ext"), "__code__", None), "co_names", ())} & ta_names)
        if set(ta_used) - set(ta_have):                     # 照合で使う ta のクラスが、TA_CLASS_MAP ではこの種類に向いていない
            conflicts.append(dict(欄="ライブラリとの対応", 選んだ値=ta_have, 選んだ置き場="indicator_reference_diag.py の TA_CLASS_MAP",
                                  選ばなかった={"照合の関数 ext が使う ta のクラス": ta_used}))
        recs[f] = {
            "名前": f,
            "列の名前の型": dict(照らす形=[e["pat"].pattern for e in fr], 列を作る形=[tpl for _rf, tpl, *_x in fg]),
            "計算の関数": [dict(登録の名前=rf, 名前の型=tpl, 向きを持つ=d, 関数の名前=called(fn), 式の文=src_text(fn))
                       for rf, tpl, d, fn in fg],
            "照合の関数・既知答え": [dict(定義=e.get("teigi"), 流儀=e.get("ryugi"), tb=plain(e.get("tb")), ext=plain(e.get("ext")),
                                  known=src_text(e["known"]) if callable(e.get("known")) else plain(e.get("known")),
                                  tol=e.get("tol"), tb_kind=e.get("tb_kind")) for e in fr],
            "代表の固定値（スキャル／デイトレ）": dict(スキャル=b.get("最初の値（スキャル）"), デイトレ=b.get("最初の値（デイトレ）")),
            "名前に出ない軸の最初の値": first_hidden.get(f),
            "列を作る値": dict(値=[list(x) for x in made], 出どころ=src_keys),
            "コードの中の既定値": {rf: defaults(fn) for rf, _tpl, _d, fn in fg},
            "範囲": lim.get(f),
            "役割・札・値域・注記": dict(役割=t["役割"], 札=lin, 値域=t["値域"], 注記=t.get("注記", "")),
            "方向・性質": dict(方向=t["方向"], 性質=props),
            "オン/オフ": dict(状態=state, 源=sorted(k for k, v in (sw.get("sources") or {}).items() if f in v)),
            "mako": next((e["mako"] for e in fr if e.get("mako")), None),
            "ライブラリとの対応": dict(INDUSTRY_MAP=plain(iref.INDUSTRY_MAP.get(f)), TA_CLASS_MAP=ta_have,
                                 EXT2=plain(iref.EXT2.get(f))),
            "出口の水準": list(exit_lv.get(f) or []) or None,
            "V9 の名前": v9,
            "教科書の出どころ": dict(review=rv or None, roles=ro or None,
                                 by_strategy={k: v for k, v in b.items() if k not in
                                              ("種類", "系統", "今の値", "最初の値（スキャル）", "最初の値（デイトレ）", "範囲")} or None),
            "閾値の値": dict(定数={c: plain(iref.CONST_REGISTRY[c]) for c in (exit_lv.get(f) or []) if c in iref.CONST_REGISTRY},
                          調べた結果={k: v for k, v in (outw.get(f) or {}).items() if k != "種類"} or None),
            "閾値の文": {k: v for k, v in (trole.get(f) or {}).items() if k != "種類"} or None,
            "閾値の代表の固定値（スキャル／デイトレ）": dict(スキャル=None, デイトレ=None),   # CP88 の修正11＝値は T-2・T-3 で埋める
            "閾値の範囲": None,
            "食い違いの記録": conflicts,
            "ほかの置き場の値": [],
        }
        if list(recs[f]) != list(FIELDS):
            raise SystemExit(f"❌ {f} の記録の欄が、4-8 の23の欄と違う")

    # CP88 の修正10＝別枠の材料の13種の記録。値は定義の表（RANGE_GEO_REF・DEMAND_REF・TIME_REF）・FAMILY_LINEAGE・indicator_switch.json から写す。
    #   時間帯の2種は、計算が engine_tuner_exec.py の _col_array の中に在る（関数として切り出すのは設計書2）ので、計算の関数の欄は空
    calc_fn = {"レンジ幾何": od.build_range_geometry, "需給": od.load_demand, "時間帯": None}
    known_fn = {"レンジ幾何": "range_geo_known_check（indicator_reference_diag.py）"}
    for f, (grp, d) in sorted(EXTRA_OF.items()):
        if f in recs:
            raise SystemExit(f"❌ 別枠の材料の名前 {f} が、INDICATOR_TABLE の名前と重なる")
        fn = calc_fn[grp]
        state = "オン" if f in set(sw.get({"レンジ幾何": "geo_on", "需給": "demand_on", "時間帯": "time_on"}[grp], [])) else "オフ"
        recs[f] = {
            "名前": f,
            "列の名前の型": dict(照らす形=[], 列を作る形=[]),
            "計算の関数": [dict(登録の名前=None, 名前の型=None, 向きを持つ=None, 関数の名前=[fn.__name__], 式の文=src_text(fn))] if fn else [],
            "照合の関数・既知答え": [dict(定義=d.get("teigi"), 流儀=d.get("ryugi"), tb=None, ext=None, known=known_fn.get(grp),
                                  tol=None, tb_kind=None)],
            "代表の固定値（スキャル／デイトレ）": dict(スキャル=None, デイトレ=None),
            "名前に出ない軸の最初の値": None,
            "列を作る値": dict(値=[], 出どころ=[]),
            "コードの中の既定値": {},
            "範囲": None,
            "役割・札・値域・注記": dict(役割=None, 札=(iref.FAMILY_LINEAGE.get(f) or iref.FAMILY_LINEAGE.get(grp) or {}).get("k"),
                                   値域=dict(種別=d["kind"]) if d.get("kind") else None, 注記=""),
            "方向・性質": dict(方向=dict(区分=(d.get("houkou") or "").split("＝")[0] or None, 読み方=d.get("houkou")), 性質=[]),
            "オン/オフ": dict(状態=state, 源=sorted(k for k, v in (sw.get("sources") or {}).items() if f in v)),
            "mako": d.get("mako"),
            "ライブラリとの対応": None,
            "出口の水準": None,
            "V9 の名前": [],
            "教科書の出どころ": dict(source=d["source"]) if d.get("source") else None,
            "閾値の値": dict(定数={}, 調べた結果=None),
            "閾値の文": None,
            "閾値の代表の固定値（スキャル／デイトレ）": dict(スキャル=None, デイトレ=None),
            "閾値の範囲": None,
            "食い違いの記録": [],
            "ほかの置き場の値": [],
        }
        if list(recs[f]) != list(FIELDS):
            raise SystemExit(f"❌ {f} の記録の欄が、4-8 の23の欄と違う")
    # CP89 の修正1＝別枠の材料と時刻の、直す相手の一覧に無いパラメータと閾値の置き場を写す（読むだけ・ast で開く）
    dash = SDK / "scripts/dashboard"
    geo_params = []
    for p, nm in ((PR / "e37_scalp.py", "V25_K"), (dash / "build_range_gate_dashboard.py", "ZONE_TOL"),
                  (dash / "build_range_gate_dashboard.py", "ZONE_TOUCH"), (dash / "build_range_gate_dashboard.py", "ZONE_LOOKBACK")):
        v, ln = module_assign(p, nm)
        geo_params.append(dict(置き場=f"{p.relative_to(SDK / 'scripts').as_posix()}:{ln}", 名前=nm, 値=v))
    for n in ast.parse((dash / "build_regime_gate_rg.py").read_text(encoding="utf-8")).body:
        if isinstance(n, ast.FunctionDef) and n.name == "_adaptive_tol_1h":
            a = n.args
            geo_params.append(dict(置き場=f"dashboard/build_regime_gate_rg.py:{n.lineno}", 名前="_adaptive_tol_1h の引数の既定値",
                                   値={x.arg: ast.literal_eval(d) for x, d in zip(a.args[len(a.args) - len(a.defaults):], a.defaults)}))
    if len(geo_params) != 5:
        raise SystemExit("❌ レンジ幾何のパラメータの置き場が読めない（build_regime_gate_rg.py に _adaptive_tol_1h が無い）")
    for f, (grp, _d) in EXTRA_OF.items():
        if grp == "レンジ幾何":
            recs[f]["ほかの置き場の値"] += copy.deepcopy(geo_params)
    recs["時刻"]["閾値の範囲"] = [dict(jload(PR / "recipes/search_limits.json")["hour_range"],
                                   出どころ="recipes/search_limits.json の hour_range（engine_tuner_exec.py:1057〜1066）")]
    if unknown_dir:
        raise SystemExit("❌ 方向が、方向から性質への対応の表に無い種類が在る（表に1行を足すと通る）: "
                         + "・".join(f"{f}（{h}）" for f, h in unknown_dir))
    if unknown_role:
        raise SystemExit("❌ 役割の区分が、役割の区分の表に無い種類が在る（表に1行を足すと通る）: "
                         + "・".join(f"{f}（{'・'.join(m)}）" for f, m in unknown_role))
    if len(recs) != len(TABLE) + len(EXTRA_OF):
        raise SystemExit(f"❌ 記録の数 {len(recs)} が、INDICATOR_TABLE の種類の数 {len(TABLE)} と別枠の材料の数 {len(EXTRA_OF)} の和と合わない")

    # 9 直す相手の一覧の「①写す」の行のうち、決まった欄に入らない置き場を写す（F-3・F-4 の23番目の欄）
    rows = inventory()
    others = {}                                               # 置き場 → 写した物（同じ置き場が2つの節に出ても1回だけ写す）
    for r in rows:
        k = row_kind(r)
        for o in (code_copy(r) if k == "ほかの置き場" else json_copy(r) if k == "json" else []):
            others.setdefault(o["置き場"], o)
    kubun = []
    for o in others.values():
        if not o["種類"]:
            kubun.append({x: o[x] for x in ("置き場", "名前", "値")})
        for f in o["種類"]:
            val = narrow(o["値"], f) if not isinstance(o["値"], str) else o["値"]
            recs[f]["ほかの置き場の値"].append(dict(置き場=o["置き場"], 名前=o["名前"], 値=val))
    data = {"_作った道具": ".claude/state/indicator_review/gen_indicators_draft.py（手で書かない）",
            "役割の区分の表": role_table, "方向から性質への対応の表": prop_table,
            "区分の言葉の表（ほかの置き場）": kubun, "記録": recs}
    return json.loads(json.dumps(data, ensure_ascii=False, default=repr)), rows


# ══ 照らす（4-4 の12・F-8）════════════════════════════════════════════════════════════════════
def coverage(data: dict, rows: list) -> list:
    """直す相手の一覧の「①写す」の行のうち、記録にも3つの表にも入らない行（4-5）。"""
    recs = data["記録"]
    placed = {o["置き場"] for r in recs.values() for o in r["ほかの置き場の値"]} | {o["置き場"] for o in data["区分の言葉の表（ほかの置き場）"]}
    src_keys = {k for r in recs.values() for k in r["列を作る値"]["出どころ"]}
    miss = []
    for r in rows:
        k = row_kind(r)
        if k == "古い鍵":
            ok = r["中身"] in src_keys
        elif k == "コードの中の既定値":
            f = r["中身"].split(" のパラメータ")[0]
            ok = f in recs and any(v["引数の既定値"] or v["式の中の数"] for v in recs[f]["コードの中の既定値"].values())
        elif k in ("決まった欄", "自己テストの見本"):        # 見本は写さない（worklog 20261024:357）
            ok = True
        elif k == "json":
            keys = [t.split()[0] for t in r["中身"].split("・")]
            ok = all(key in JSON_OWN.get(r["ファイル"], set()) or f"{r['ファイル']} の {key}" in placed for key in keys)
        else:
            lo = int(re.split(r"[-〜]", r["行"])[0])
            ok = any(p.startswith(f"{r['ファイル']}:") and int(p.split(":")[1]) == lo for p in placed)
        if not ok:
            miss.append(f"{r['ファイル']}:{r['行']} {r['中身'][:40]}")
    return miss


def verify() -> int:
    """indicators.json の値と、写す元から作り直した値を1件ずつ比べる。書かない。違えば 1。"""
    if not OUT.exists():
        print(f"❌ {OUT} が無い（先に写す）")
        return 1
    have = jload(OUT)
    want, rows = build()
    bad = []
    for key in ("役割の区分の表", "方向から性質への対応の表", "区分の言葉の表（ほかの置き場）"):
        if norm(have.get(key)) != norm(want[key]):
            bad.append(f"表「{key}」が写す元と違う")
    hr, wr = have.get("記録", {}), want["記録"]
    for f in sorted(set(hr) | set(wr)):
        if f not in hr or f not in wr:
            bad.append(f"{f}: 記録が{'無い' if f not in hr else '写す元に無い'}")
            continue
        if list(hr[f]) != list(FIELDS):
            bad.append(f"{f}: 欄が 4-8 の23の欄と違う（{len(hr[f])}個）")
        for fld in FIELDS:
            if norm(hr[f].get(fld)) != norm(wr[f].get(fld)):
                bad.append(f"{f}: 欄「{fld}」が写す元と違う（記録 {norm(hr[f].get(fld))[:80]} ／ 写す元 {norm(wr[f].get(fld))[:80]}）")
    miss = coverage(want, rows)
    bad += [f"直す相手の一覧の「①写す」の行が、記録にも3つの表にも入らない: {m}" for m in miss]
    print(f"照らした＝記録 {len(hr)} 種 × {len(FIELDS)} 欄・表 3つ・直す相手の一覧の「①写す」の行 {len(rows)} 行")
    for b in bad:
        print("  ❌", b)
    print("✅ 違い 0 件" if not bad else f"❌ 違い {len(bad)} 件")
    return 0 if not bad else 1


def selftest() -> int:
    """2つの表に1行を足すと、プログラムを直さずに新しい区分・方向が使えるか（7-6 の F-7）。表に無ければ止める物として返るか。"""
    t = dict(役割=dict(区分=["試しの区分"], 出どころ="自己テスト"), 札="試しの札", 方向=dict(区分="試しの方向", 読み方=""), 性質="none")
    role, prop = {}, {}
    ok = []
    _l, _p, mr, md = decide(t, role, prop)
    ok.append(("表に無い区分と方向は、止める物として返る", mr == ["試しの区分"] and md == ["試しの方向"]))
    role["試しの区分"] = dict(札="試しの札2", 出どころ="自己テスト")
    prop["試しの方向"] = dict(性質=["trend", "vol"], 出どころ="自己テスト")
    lin, props, mr, md = decide(t, role, prop)
    ok.append(("表に1行ずつ足すと、札と性質（2つ）が表から決まる", (lin, props, mr, md) == ("試しの札2", ["trend", "vol"], [], [])))
    for name, good in ok:
        print(f"  {'✅' if good else '❌'} {name}")
    return 0 if all(g for _n, g in ok) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verify:
        return verify()
    data, rows = build()
    miss = coverage(data, rows)
    if miss:
        raise SystemExit("❌ 直す相手の一覧の「①写す」の行のうち、記録にも3つの表にも入らない行が在る: " + "／".join(miss))
    if OUT.exists():
        if norm(jload(OUT)) == norm(data):
            print(f"{OUT} はもう在り、写す元から作り直した物と同じ（書かない）")
            return 0
        raise SystemExit(f"❌ {OUT} はもう在り、写す元から作り直した物と違う（1回だけ書く・違いは --verify で見る）")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    recs = data["記録"]
    renamed = sorted({f for f, r in recs.items() for c in r["計算の関数"] if c["登録の名前"] not in (f, None)})
    print("書いた", OUT, "・記録", len(recs), "種（INDICATOR_TABLE", len(TABLE), "・別枠の材料", len(EXTRA_OF), "）・欄", len(FIELDS),
          "・「①写す」の行", len(rows))
    print("欄ごとの空でない記録の数（4-12）:", "・".join(
        f"{fld} {sum(1 for r in recs.values() if r[fld] not in (None, '', [], {}) and not (isinstance(r[fld], dict) and all(v in (None, '', [], {}) for v in r[fld].values())))}" for fld in FIELDS))
    print("名前の違う種類（表の名前にそろえた）", len(renamed), "種:", "・".join(renamed))
    print("食い違いの記録が在る種類", sum(1 for r in recs.values() if r["食い違いの記録"]),
          "・区分の言葉の表", len(data["区分の言葉の表（ほかの置き場）"]), "件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
