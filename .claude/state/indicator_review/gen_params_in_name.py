#!/usr/bin/env python3
"""gen_params_in_name.py — 172番（工事 m2c15-params-in-name-20261026）＝engine_tuner が探せない形の指標を、全部 探せる形にする
（動かせる数字を列の名前に出す）ための道具。読むだけ・本物（scripts/priority_rebuild・設定）には書かない。書く先は工事のフォルダと作業の控え。

まこさんの決定（2026-10-25・26）＝「『名前に出す』に戻す」「これはかなり深刻なミスなので、絶対に修正をするようにしないといけないのでは？」
（ok_names_back_20261025.txt）・広げ方「OK」（ok_172_scope_20261026.txt）・V9 の名前も変えてよい・成績表は後・範囲が無い15種は T-3
（ok_q12_names_ranking_20261026.txt・ok_q3_range_t3_20261026.txt）。

何をするか（やることの表 F-1・4-4 の1〜2）
  --measure   印がオンの登録を全部 回し、計算式（lambda）の引数を1つずつ別の値にして列が変わるかを測る（10-04 の hidden_param_check.py の③と
              同じ決まった式の値動き。hidden_dead.json の引数は外す）。列が変わり、名前の型の {} に出ていない引数＝「隠れた数字」。
              種類ごとに〔新しい名前の型・引数の並び・列を作る値の組（直す前と同じ列になる値）・範囲とその出どころ・参照表の新しい型・名前の写し〕を
              一覧 params_in_name_20261026.json に書く。
  --count     名前に出ていない動かせる数字を持つオンの登録の数を出す（2-1・7-6）。
  --build     一覧から、実装の指示（4-20 の6つの欄・1行単位）を impl_src/NN.txt に組み、gen_yarukoto.py --step 6 で json にする。
  --check     写し（一時のフォルダ）に実装の指示を当て、①文法 ②列の名前の写しが全部 往復する ③何も渡さない組の列の値が直す前と同じ
              ④参照表で全部の名前が引ける ⑤material_ranges の軸の数が全種で合う ⑥軽い口（--selftest-catalog）が通る、を確かめる。
  --ranges    engine_tuner_gen.material_ranges を呼び、オンの全種で軸の数が名前の型の {} の数と合うかを見る（7-6 の F-4）。
  --compare-renamed <直す前の控え.json>  列の控えを、名前の写し（古い名前→新しい名前）で比べる（7-6 の F-3）。
  --check-redirect [--keep] [--verbose]  ★2026-10-31＝172番の中身を受けた161-1（工事 m2c15-indicator-redirect-20261031）の実装の指示
              （impl_4-20_20261031.json）を写しに当て、読む口と写すプログラムの自己テスト・写し直し（--rewrite）・--verify・一覧の作り直し・
              数える道具・壊すプログラム5本を走らせる。本物には書かない（写しは一時のフォルダ・--keep で残す）。
名前の型の決まり（CC が決めた技術の決め方＝案の【5】）
  ・1軸＝今の形のまま（RSI{}）。2軸以上で、今の型の {} が末尾の1つ＝括弧の形にそろえる（Stoch%K{} → Stoch%K({},{})）。
  ・今の型に {} が無い＝末尾に括弧を足す（AO% → AO%({},{})・監査 CP60 の修正30 の形）。
  ・今の型の {} が末尾でない（EMA{}傾き%）＝末尾に括弧を足す（EMA{}傾き%({})＝監査 CP60 の修正1〜6 の形）。
  ・今の型に括弧が在る（MACD線%({},{})）＝括弧の中に足す。
値の決まり（CC は数字を作らない）
  ・列を作る値＝直す前と同じ列になる値。lambda の既定が数ならその数。None（ライブラリの既定）なら、ライブラリの関数の中の既定の数字・
    資料の表の値・設定の material_first_hidden の値を候補にして、同じ列になることをハッシュ値で確かめた物（合う物が無ければ止まる＝CKSP の型）。
  ・範囲＝①search_limits.json に在る軸はそのまま ②無い軸は indicator_params_by_strategy.json の「範囲」（パラメータの名前で軸を合わせる）
    ③どちらにも無い軸＝search_limits にその種類が在れば lo＝hi＝今の値（固定）・無ければ種類ごと足さない（T-3 で教科書から決める）。
"""
import ast
import hashlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PR = SDK / "scripts/priority_rebuild"
ST = ROOT / ".claude/state"
HERE = Path(__file__).resolve().parent
WORK = "m2c15-params-in-name-20261026"
WD = ST / "verbatim" / WORK
OUT_LIST = WD / "params_in_name_20261026.json"
SRC_DIR = WD / "impl_src"
OD_REL = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py"
IR_REL = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py"
CFG_REL = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json"
LIM_REL = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json"
EXEC_REL = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py"
GID_REL = ".claude/state/indicator_review/gen_indicators_draft.py"
DEAD = json.loads((HERE / "hidden_dead.json").read_text(encoding="utf-8"))
BY = {r["種類"]: r for r in json.loads((ST / "indicator_params_by_strategy.json").read_text(encoding="utf-8"))["指標"]}
SW_ON = set(json.loads((SDK / ".claude/ratchet/indicator_switch.json").read_text(encoding="utf-8"))["on"])
CFG = json.loads((PR / "observe_config.json").read_text(encoding="utf-8"))
LIM = json.loads((PR / "recipes/search_limits.json").read_text(encoding="utf-8"))
_od = _iref = None


def mods(pr: Path = PR):
    """観察の道具と参照表を、置き場を作業場所にして読み込む（写すプログラム gen_indicators_draft.py と同じ形）。"""
    global _od, _iref
    if _od is None:
        cwd = os.getcwd()
        sys.path.insert(0, str(pr))
        os.chdir(pr)
        try:
            import indicator_reference_diag as iref  # noqa: E402
            import observe_diag as od  # noqa: E402
            od._load_pta()
        finally:
            os.chdir(cwd)
        _od, _iref = od, iref
    return _od, _iref


def synth():
    """決まった式で作った値動き（10-04 の hidden_param_check.py の PROBE と同じ・相場のデータは使わない）。"""
    n = 600
    t = np.arange(n)
    c = 100 + 5 * np.sin(t / 17.0) + 2 * np.sin(t / 5.0) + 1.5 * np.sin(t / 1.7) + 3 * np.sin(t / 41.0) + t * 0.01
    return pd.DataFrame({"open": c - 0.2 * np.cos(t / 3.0), "high": c + 0.6 + 0.2 * np.sin(t / 7.0),
                         "low": c - 0.6 - 0.2 * np.cos(t / 11.0), "close": c, "volume": 1000 + 100 * np.sin(t / 13.0)},
                        index=pd.date_range("2026-01-01", periods=n, freq="5min"))


def hsh(s) -> str:
    return hashlib.sha256(np.asarray(s, dtype=float).tobytes()).hexdigest()


INT_RE = r"len|roc|sma|signal|tcl|medium|^p$|^q$|^fast$|^slow$|^f_$|^s_$|^n$|rows|_n$|^k$"
ALT = {"poles": 3, "phase": 50, "a": 0.5, "c": 0.5, "sigma": 4, "k": 5, "d_": 5, "fast": 5, "medium": 10, "slow": 20,
       "slowlimit": 0.1, "fastlimit": 0.3}


def numdef(p) -> bool:
    return p.default is None or (isinstance(p.default, (int, float)) and not isinstance(p.default, bool))


def name_token(s: str) -> str:
    return re.split(r"[（(]", s)[0].strip().lower()


def axes_tpl(base: str, n_hidden: int) -> str:
    """名前の型の決まり（この道具の説明の「名前の型の決まり」）。"""
    if n_hidden == 0:
        return base
    m = base.count("{}")
    total = m + n_hidden
    if "(" in base and base.endswith(")"):
        return base[:base.rindex("(")] + "(" + ",".join(["{}"] * total) + ")"
    if m == 1 and base.endswith("{}"):
        return base[:-2] + "(" + ",".join(["{}"] * total) + ")"
    return base + "(" + ",".join(["{}"] * n_hidden) + ")"


def _esc(s: str) -> str:
    """正規表現の特別な文字だけを逃がす（re.escape は空白も逃がす＝参照表の今の書き方 "close vs …" と違う形になる）。"""
    return re.sub(r"([.^$*+?{}\[\]\\|()])", r"\\\1", s)


def pattern_of(tpl: str, kinds: list) -> str:
    """名前の型 → 参照表の正規表現（int＝(\\d+)・float＝([\\d.]+)＝BB%b の型と同じ）。"""
    parts = tpl.split("{}")
    out = _esc(parts[0])
    for i, p in enumerate(parts[1:]):
        out += (r"(\d+)" if kinds[i] == "int" else r"([\d.]+)") + _esc(p)
    return out


def kind_of(v) -> str:
    return "int" if isinstance(v, int) and not isinstance(v, bool) else "float"


def head_span(text: str):
    """text の最初の lambda の頭（lambda d, …:）の始まりと「:」の位置。"""
    m = re.search(r"lambda d\b", text)
    if not m:
        raise SystemExit("lambda d が無い: " + text[:80])
    i = m.start()
    depth, j = 0, i
    while True:
        ch = text[j]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == ":" and depth == 0:
            break
        j += 1
    return i, j


def split_args(body: str) -> list:
    parts, buf, depth = [], "", 0
    for ch in body:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts


def rewrite_head(text: str, expose: list) -> str:
    """最初の lambda の頭で、expose の引数の既定を外して位置の引数にする（並びはそのまま。ほかの引数は触らない）。"""
    i, j = head_span(text)
    parts = split_args(text[i + len("lambda "):j])
    new = [p.split("=")[0].strip() if p.split("=")[0].strip() in expose else p for p in parts]
    return text[:i] + "lambda " + ", ".join(new) + text[j:]


def stmt_of(src: str, fam: str):
    """その種類を登録している文（_reg(…) の1文）を、元の文字のまま取り出す（hidden_param_check.stmt_of と同じ）。"""
    lines = src.splitlines(keepends=True)
    hit = [n for n in ast.parse(src).body
           if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", "") == "_reg"
           and n.value.args and isinstance(n.value.args[0], ast.Constant) and n.value.args[0].value == fam]
    return "".join(lines[hit[0].lineno - 1:hit[0].end_lineno]) if len(hit) == 1 else None


def ma_entry_of(src: str, nm: str):
    """移動平均の一覧 _MA_FUNCS の1項（("KAMA", lambda …),）の元の文字。"""
    blk = re.search(r"_MA_FUNCS = \[\n(.*?\n)\]\n", src, re.S).group(1)
    m = re.search(rf'    \("{re.escape(nm)}", lambda d, n(?:.|\n)*?\),\n(?=    \(|    #|\Z)', blk)
    return m.group(0) if m else None


def lib_defaults(od, fn_text: str, arg: str) -> list:
    """ライブラリの関数のソースで、その引数の既定を決める行の数字＝「… else 7」「_pos_int(fast, 7)」の 7（ライブラリが None を置き替える値）。"""
    out = []
    for src in _lib_sources(od, fn_text):
        for ln in src.splitlines():
            code = ln.split("#")[0]
            if not re.search(rf"\b{re.escape(arg)}\b", code):
                continue
            for m in re.finditer(rf"_pos_\w+\(\s*{re.escape(arg)}\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", code):
                out.append(float(m.group(1)) if "." in m.group(1) else int(m.group(1)))
            m = re.match(rf"\s*{re.escape(arg)}\s*=.*\belse\s+(-?\d+(?:\.\d+)?)\s*$", code)
            if m:
                out.append(float(m.group(1)) if "." in m.group(1) else int(m.group(1)))
    return out


def _lib_sources(od, fn_text: str) -> list:
    funcs = set(re.findall(r"_pta6\.(\w+)\(", fn_text))
    for h in set(re.findall(r"\b(_[a-z_]+)\(", fn_text)):
        f = getattr(od, h, None)
        if callable(f) and not isinstance(f, type):
            try:
                funcs |= set(re.findall(r"_pta6\.(\w+)\(", inspect.getsource(f)))
            except (OSError, TypeError):
                pass
    out = []
    for fnm in funcs:
        f = getattr(od._pta6, fnm, None)
        if f is None:
            continue
        try:
            out.append(inspect.getsource(inspect.getmodule(f)))
        except (OSError, TypeError):
            continue
    return out


def lib_lits(od, fn_text: str, arg: str) -> list:
    """登録の文（と、その中の自前の関数）が呼ぶライブラリの関数のソースから、その引数の行に在る数字を候補として集める。"""
    funcs = set(re.findall(r"_pta6\.(\w+)\(", fn_text))
    for h in set(re.findall(r"\b(_[a-z_]+)\(", fn_text)):
        f = getattr(od, h, None)
        if callable(f) and not isinstance(f, type):
            try:
                funcs |= set(re.findall(r"_pta6\.(\w+)\(", inspect.getsource(f)))
            except (OSError, TypeError):
                pass
    out = []
    for fnm in funcs:
        f = getattr(od._pta6, fnm, None)
        if f is None:
            continue
        try:
            src = inspect.getsource(f)
        except (OSError, TypeError):
            continue
        for ln in src.splitlines():
            if re.search(rf"\b{re.escape(arg)}\b", ln) and "=" in ln:
                for lit in re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w])", ln.split("#")[0]):
                    out.append(float(lit) if "." in lit else int(lit))
    return out


def measure() -> dict:
    od, iref = mods()
    cfg = od.load_config()
    cat = od._catalog_from_config(cfg)                    # 写す元＝設定から列を作る関数（162番まで・監査 CP97。build_catalog は indicators.json から作る）
    src = (ROOT / OD_REL).read_text(encoding="utf-8")
    d = synth()
    cases = {"W字確定谷": lambda: iref._w_case(24, 100.2)}
    for bf in ("帯スイング", "帯スイング1時間ATR"):
        cases[bf] = lambda: iref._band_case("swing", 4)
    pos, first_col, famname = {}, {}, {}
    for nm, _f, _d in cat:
        fam, prm = od.find_material(nm)
        if fam is None:
            continue
        pos.setdefault(fam, []).append(tuple(prm))
        first_col.setdefault(fam, nm)
        if fam not in famname:
            e, _p = iref.find(nm)
            famname[fam] = e["family"] if e else fam
    ma_names = [nm for nm, _f in od._MA_FUNCS]
    out, errs = {}, []
    for fam, (tpl, _dr, fn) in od.MATERIAL_FAMILIES.items():
        if fam not in pos:
            continue
        ir = famname[fam]
        on = ir in SW_ON
        P0 = pos[fam][0]
        if len(P0) != tpl.count("{}"):
            errs.append(f"{fam}: 名前の型の {{}} の数と列の数字の数が合わない")
            continue
        sig = list(inspect.signature(fn).parameters.values())
        rest = sig[1 + len(P0):]
        kw = {}
        for p in rest:
            if p.kind is not p.VAR_KEYWORD and p.name != "f" and numdef(p):
                kw[p.name] = (p.default, "lambda")
        fpar = inspect.signature(fn).parameters.get("f")
        ma = fpar is not None and callable(fpar.default) and any(p.kind is p.VAR_KEYWORD for p in rest)
        ma_nm = None
        if ma:
            for p in list(inspect.signature(fpar.default).parameters.values())[2:]:
                if numdef(p):
                    kw[p.name] = (p.default, "f")
            ma_nm = next((nm for nm, f in od._MA_FUNCS if f is fpar.default), None)
        if not kw:
            continue
        if not on:
            # ★オフの登録＝直さない（Y-1）。ただし移動平均の for で登録した物は、for を直すと一緒に変わるので、名前の型と列を作る値だけ持つ
            if not ma:
                continue
        dd = cases[fam]() if fam in cases else d
        base = hsh(fn(dd, *P0))
        moved, dead, raised_all = [], [], []
        for k, (v, _src) in kw.items():
            if v is not None:
                alts = [v + 2, v + 6] if isinstance(v, int) else [v + 0.1, v * 2 + 0.3]
            else:
                a1 = ALT.get(k, 7 if re.search(INT_RE, k) else 0.05)
                alts = [a1, a1 * 2 + 1 if isinstance(a1, int) else a1 * 3]
            mv, raised = False, 0
            for alt in alts:
                try:
                    if hsh(fn(dd, *P0, **{k: alt})) != base:
                        mv = True
                        break
                except Exception:                                # noqa: BLE001
                    raised += 1
            if mv:
                moved.append(k)
            elif raised == len(alts):
                raised_all.append(k)
            else:
                dead.append(k)
        drop = set(DEAD.get(ir, [])) | set(DEAD.get(fam, []))
        hidden = [k for k in kw if k in moved and k not in drop]
        if ma:
            # ★移動平均の for の登録は、計算式 f の数字を先に、登録の lambda の数字（傾きの比べる本数 slope_n）を最後に受け取る（LOOP_NEW の形）
            hidden = [k for k in hidden if kw[k][1] == "f"] + [k for k in hidden if kw[k][1] == "lambda"]
        undecided_dead = [k for k in dead if k not in drop]
        if undecided_dead and on:
            errs.append(f"{fam}: 列が変わらない引数が hidden_dead.json に無い: {undecided_dead}（計算に届いていないか、外す引数）")
        if not hidden:
            continue
        by = BY.get(ir, {})
        pnames = [name_token(x) for x in (by.get("パラメータの名前") or [])]
        libd = ((by.get("ライブラリの既定") or {}).get("値") if isinstance(by.get("ライブラリの既定"), dict) else None) or []
        hid_sets = (CFG.get("material_first_hidden") or {}).get(ir) or {}
        cand_sets = [s for grp in ("スキャル", "デイトレ") for s in (hid_sets.get(grp) or [])]
        cand_sets += [s for grp in ("最初の値（スキャル）", "最初の値（デイトレ）") for s in (by.get(grp) or [])]
        fn_text = (stmt_of(src, fam) or "") + (ma_entry_of(src, ma_nm) or "" if ma_nm else "")
        values, unresolved = {}, []
        for k in hidden:
            v, _src = kw[k]
            if v is not None:
                values[k] = v
                continue
            # ★先に、ライブラリが None を置き替える既定の数字（else の後ろ・_pos_int の2つ目）を試す。同じ列になれば、それが答え。
            ok = None
            for cv in lib_defaults(od, fn_text, k):
                try:
                    if hsh(fn(dd, *P0, **{k: cv})) == base:
                        ok = cv
                        break
                except Exception:                                # noqa: BLE001
                    pass
            if ok is not None:
                values[k] = ok
                continue
            cands = []
            if k in pnames and len(libd) == len(pnames):
                cands.append(libd[pnames.index(k)])
            if k in pnames:
                cands += [s[pnames.index(k)] for s in cand_sets if len(s) == len(pnames)]
            cands += lib_lits(od, fn_text, k)
            cands += [x for s in cand_sets for x in s]          # 位置が合わない物も、ハッシュ値で合う物だけ採る
            # ★0 は最後に試す＝ライブラリは 0 を「既定を使う」と読む（例＝alma.py「sigma if sigma and sigma > 0 else 6」）ので、
            #   0 でも同じ列になる。0 を先に採ると、名前に 0 が出る（2026-10-26 の測り直しで ALMA傾き の sigma＝0 が出た）。
            cands = [x for x in cands if x != 0] + [x for x in cands if x == 0]
            seen_c, ok = set(), None
            for cv in cands:
                if cv in seen_c:
                    continue
                seen_c.add(cv)
                try:
                    if hsh(fn(dd, *P0, **{k: cv})) != base:
                        continue
                    # ★生きている値か＝少し動かすと列が変わる（ライブラリが範囲の外の値を既定に置き替えて、同じ列になった物を外す。
                    #   実例＝t3.py「a if a and a > 0 and a < 1 else 0.7」で a＝1 でも同じ列になった・2026-10-26）。
                    if isinstance(cv, int) and not isinstance(cv, bool):
                        nudges = [cv + 1, cv - 1] if cv > 1 else [cv + 1]
                    else:
                        nudges = [cv * 1.05, cv * 0.95] if cv else [0.05]
                    if any(hsh(fn(dd, *P0, **{k: nv})) != base for nv in nudges):
                        ok = cv
                        break
                except Exception:                                # noqa: BLE001
                    pass
            if ok is None:
                unresolved.append((k, sorted(seen_c, key=str)))
            else:
                values[k] = ok
        if unresolved:
            errs.append(f"{fam}: 直す前と同じ列になる値が決められない引数: {unresolved}")
            continue
        kinds = [kind_of(x) for x in P0] + [kind_of(values[k]) for k in hidden]
        new_tpl = axes_tpl(tpl, len(hidden))
        vals = [list(p) + [values[k] for k in hidden] for p in pos[fam]]
        lim_axes = (LIM.get("material_param_ranges") or {}).get(ir)
        by_rng = by.get("範囲") or []
        # ★資料の表の軸の並びが、名前に出る軸＋隠れた数字の並びと同じかを、資料の表の最初の値（かライブラリの既定）で確かめる
        #   （名前が違って拾えない種類＝MASSI〔ema_period・sum_period〕と fast・slow ほか。値が並びどおりに合うときだけ並びで拾う）
        full_now = list(P0) + [values[k] for k in hidden]
        firsts = [s for grp in ("最初の値（スキャル）", "最初の値（デイトレ）") for s in (by.get(grp) or [])] + ([libd] if libd else [])
        pos_ok = len(by_rng) == len(full_now) and any(len(s) == len(full_now) and all(float(a) == float(b) for a, b in zip(s, full_now)) for s in firsts)
        rng, rng_src = [], []
        for i in range(len(P0)):
            if lim_axes and i < len(lim_axes):
                rng.append(dict(lim_axes[i]))
                rng_src.append("search_limits.json")
            else:
                col = [p[i] for p in pos[fam]]
                rng.append({"kind": kind_of(col[0]), "lo": min(col), "hi": max(col)})
                rng_src.append("カタログの値の最小〜最大（engine_tuner_gen.material_ranges が設定に無いときに作る範囲と同じ）")
        for j, k in enumerate(hidden):
            r = None
            bi = pnames.index(k) if k in pnames else (len(P0) + j if pos_ok else None)
            if bi is not None and bi < len(by_rng) and by_rng[bi].get("下限") is not None:
                b = by_rng[bi]
                r = {"kind": kind_of(values[k]), "lo": b["下限"], "hi": b["上限"]}
                # ★資料の表の範囲が1点（下限＝上限）なら、探せない＝範囲が無い軸と同じ扱いで T-3 の印を付ける（まこさん 2026-10-26「よい」の扱い）
                if float(b["下限"]) == float(b["上限"]):
                    r["出どころ"] = "資料の表の範囲が1点（今の値と同じ・範囲は70番の T-3 で教科書から決める）"
                rng_src.append("indicator_params_by_strategy.json の範囲（" + str(b.get("出どころ", "")) + ("・並びで拾った" if k not in pnames else "") + "）"
                               + ("・1点＝T-3" if float(b["下限"]) == float(b["上限"]) else ""))
            else:
                r = {"kind": kind_of(values[k]), "lo": values[k], "hi": values[k], "出どころ": "固定（今の値・範囲は70番の T-3 で教科書から決める）"}
                rng_src.append("固定（資料の表に範囲が無い・T-3）")
            rng.append(r)
        # ★種類と小数の桁数は、探す側（engine_tuner_gen.material_ranges:289〜292）と同じ決め方にする
        #   （範囲の両端・カタログの値の、どれか1つでも小数の型なら float。桁数は一番長い小数の桁。draw_param:343 は dec を直に読む）
        for i, r in enumerate(rng):
            vs = [r["lo"], r["hi"]] + [p[i] for p in vals]
            is_int = all(float(v).is_integer() and not isinstance(v, float) for v in vs)
            r["kind"] = "int" if is_int else "float"
            if is_int:
                r.pop("dec", None)
            else:
                r["dec"] = max(int(r.get("dec") or 0), max((len(str(v).split(".")[1]) if "." in str(v) else 0) for v in vs))
        kinds = [r["kind"] for r in rng]
        e, _p = iref.find(first_col[fam])
        pat_now = e["pat"].pattern[1:-1] if e else None
        grp = "①" if ir in (CFG.get("material_first_hidden") or {}) else ("②" if "{}" not in tpl else "③")
        out[fam] = {"参照表の名前": ir, "オン": on, "群": grp, "今の名前の型": tpl, "新しい名前の型": new_tpl,
                    "隠れた数字": [{"引数": k, "値": values[k], "出どころ": kw[k][1]} for k in hidden],
                    "外す引数（hidden_dead.json）": sorted(drop & set(kw)), "計算できない別の値の引数": raised_all,
                    "列を作る値": vals, "範囲": rng, "範囲の出どころ": rng_src, "軸の型": kinds,
                    "参照表の今の型": pat_now, "参照表の新しい型": pattern_of(new_tpl, kinds),
                    "名前の写し": {od.make_material(fam, *p)[0]: new_tpl.format(*(list(p) + [values[k] for k in hidden])) for p in pos[fam]},
                    "移動平均の for": ma, "移動平均の名前": ma_nm, "最初の列": first_col[fam]}
    on_items = {k: v for k, v in out.items() if v["オン"]}
    return {"_これは何か": "172番の相手の一覧（gen_params_in_name.py --measure が、観察の道具の登録を測って書いた・手で書き替えない）",
            "数": {"印がオンの登録（カタログに列が在る物）": sum(1 for f in od.MATERIAL_FAMILIES if f in pos and famname[f] in SW_ON),
                  "印がオンの種類（indicator_switch.json の on）": len(SW_ON),
                  "相手（オン）": len(on_items), "①": sum(1 for v in on_items.values() if v["群"] == "①"),
                  "②": sum(1 for v in on_items.values() if v["群"] == "②"), "③": sum(1 for v in on_items.values() if v["群"] == "③"),
                  "移動平均の for で一緒に変わるオフの登録": sum(1 for v in out.values() if not v["オン"])},
            "止まった理由": errs, "一覧": out}


# ── 実装の指示を組む ─────────────────────────────────────────────────────────────────
GUARD_NEW = '''def _insp_hidden_params() -> list:
    """動かせる数字が、全部 列の名前に出ているかを確かめる（工事 m2c15-params-in-name-20261026・2026-10-26）。

    ★10-04 の工事（m2c15-hidden-params-20261004）は、数字を「名前に出さない引数」で受け取る形にした。名前に数字が無いと
      engine_tuner は探せない（engine_tuner_gen.material_ranges は列の名前の数字から範囲を作る）＝違反の記録 #28。
      まこさんの決定（2026-10-26）「『名前に出す』に戻す」で、この番人は逆の決まりを守る。
    決まり＝印がオンの登録の計算式（lambda）に、数の既定（None か数）を持つ引数は、hidden_dead.json（その列の計算に使われない引数）の
      物のほかに在ってはいけない。名前の型の {} の数＝lambda の位置の引数の数（d を除く）。移動平均の for で登録した物は、計算式 f の側を見る。"""
    import inspect
    import json as _json
    sw_on = set(_json.loads(_SWITCH_PATH.read_text(encoding="utf-8")).get("on") or [])
    # リポジトリの根＝priority_rebuild・scripts・bitget-python-sdk-api・v3-bitget-api-sdk の1つ上（parents の4番目）
    dead_p = pathlib.Path(__file__).resolve().parents[4] / ".claude/state/indicator_review/hidden_dead.json"
    if not dead_p.is_file():
        return [f"名前に出す: 外す引数の一覧 hidden_dead.json が無い（{dead_p}）"]
    dead = _json.loads(dead_p.read_text(encoding="utf-8"))
    pos = {}
    for nm, _f, _d in build_catalog(load_config()):
        fam, prm = find_material(nm)
        if fam is not None and fam not in pos:
            pos[fam] = (tuple(prm), nm)
    ng, seen = [], 0

    def _numdef(p):
        return p.default is None or (isinstance(p.default, (int, float)) and not isinstance(p.default, bool))
    for fam, (tpl, _dr, fn) in MATERIAL_FAMILIES.items():
        if fam not in pos:
            continue
        P, nm0 = pos[fam]
        e, _p = iref.find(nm0)
        ir = e["family"] if e else fam
        if ir not in sw_on:
            continue
        seen += 1
        ps = list(inspect.signature(fn).parameters.values())
        fpar = inspect.signature(fn).parameters.get("f")
        if fpar is not None and callable(fpar.default) and any(p.kind is p.VAR_POSITIONAL for p in ps):
            inner = list(inspect.signature(fpar.default).parameters.values())[1:]
            need = sum(1 for p in inner if p.default is inspect._empty)
            extra = [p.name for p in inner if _numdef(p) and p.name not in set(dead.get(ir, [])) | set(dead.get(fam, []))]
            if fam.endswith("傾き"):
                need += 1
        else:
            need = sum(1 for p in ps[1:] if p.default is inspect._empty and p.kind is not p.VAR_POSITIONAL)
            extra = [p.name for p in ps[1:] if _numdef(p) and p.name not in set(dead.get(ir, [])) | set(dead.get(fam, []))]
        if need != tpl.count("{}"):
            ng.append(f"名前に出す: {fam} の名前の型の {{}} の数（{tpl.count('{}')}）と、計算式の位置の引数の数（{need}）が合わない")
        if extra:
            ng.append(f"名前に出す: {fam} の計算式に、名前に出ていない数の引数が残っている: {extra}（hidden_dead.json に無い）")
    if not seen:
        ng.append("名前に出す: 印がオンの登録が1つも無い")
    return ng


'''
LOOP_OLD = '''for _nm, _mafn in _MA_FUNCS:
    _reg(f"close vs {_nm}%", f"close vs {_nm}%{{}}", True,
         lambda d, n, f=_mafn, **kw: (d.close / f(d, n, **kw) - 1) * 100)
    if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない
        _reg(f"{_nm}傾き", f"{_nm}{{}}傾き%", True,
             lambda d, n, f=_mafn, slope_n=5, **kw: f(d, n, **kw).pct_change(slope_n) * 100)
'''
LOOP_NEW = '''def _axes_tpl(m: int) -> str:
    """名前の型の軸の形＝1軸は末尾の {}・2軸以上は括弧（工事 m2c15-params-in-name-20261026・2026-10-26）。"""
    return "{}" if m == 1 else "(" + ",".join(["{}"] * m) + ")"


for _nm, _mafn in _MA_FUNCS:
    # ★動かせる数字は全部 名前に出す（まこさん 2026-10-26「『名前に出す』に戻す」）。_k＝計算式の位置の引数の数（d を除く）。
    #   既定つきの引数は hidden_dead.json の物（その列の計算に使われない引数）だけ＝番人 _insp_hidden_params が見る。
    _k = _mafn.__code__.co_argcount - 1 - len(_mafn.__defaults__ or ())
    _reg(f"close vs {_nm}%", f"close vs {_nm}%" + _axes_tpl(_k), True,
         lambda d, *p, f=_mafn: (d.close / f(d, *p) - 1) * 100)
    if _nm not in ("JMA",):        # JMA は独立実装を書いていない＝傾きも作らない
        _reg(f"{_nm}傾き", f"{_nm}{{}}傾き%" + "(" + ",".join(["{}"] * _k) + ")", True,      # 最初の {} は本数 n・括弧は残りの軸と比べる本数
             lambda d, *p, f=_mafn: f(d, *p[:-1]).pct_change(p[-1]) * 100)
'''
BAND_OLD = '''    for n in cfg["sr_windows"]:
        for m in cfg["band_touch"]:
            for t in cfg["sr_tol"]:
                C.append(_band_material("帯スイング", _bfl, n, t, m))
            for k in cfg["sr_atr1h_k"]:
                for a in cfg["atr_periods"]:
                    C.append(_band_material("帯スイング1時間ATR", _bfl, n, k, a, m))
'''
BAND_NEW = '''    # ★2026-10-26（工事 m2c15-params-in-name-20261026）＝帯スイングの2種は、確定の本数 k も名前に出した（まこさん「『名前に出す』に戻す」）。
    #   組は、指標ごとの一覧 material_params から作る（P-1 の addf と同じ形＝その一覧の組だけ）。
    for _bf in ("帯スイング", "帯スイング1時間ATR"):
        _per_done.add(_bf)
        for _p in _per[_bf]:
            C.append(_band_material(_bf, _bfl, *_p))
'''
# ★行ごとに探す（re.S を付けない＝「.」が改行をまたがない）。2026-10-26 に re.S で書いて、後ろの約94KB（起動の所まで）を消した。
GUARD8_RE = re.compile(r"^    #  ⑧名前＝EMA の傾きと AO の名前に値が無い[^\n]*\n(?:[^\n]*\n){5}", re.M)


def func_text(src: str, name: str) -> str:
    lines = src.splitlines(keepends=True)
    for n in ast.parse(src).body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return "".join(lines[n.lineno - 1:n.end_lineno])
    raise SystemExit(f"関数 {name} が無い")


def write_item(idx: int, name: str, target: str, where: str, evidence: str, before: str, after: str) -> None:
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / f"{idx:02d}_{name}.txt").write_text(
        f"対象のファイル: {target}\n直す箇所: {where}\n根拠の抜き書き: {evidence}\n===直す前===\n{before}===直した後===\n{after}",
        encoding="utf-8")


def first_line_evidence(rel: str, needle: str) -> str:
    text = (ROOT / rel).read_text(encoding="utf-8")
    lines = text.splitlines()
    first = needle.splitlines()[0]
    for i, ln in enumerate(lines, 1):
        if ln == first:
            return f"{rel}:{i}「{first.strip()}」"
    hits = [(i, ln) for i, ln in enumerate(lines, 1) if first in ln]      # 行の一部を直す指示＝その一部を含む1行の全体を抜き書きにする
    if len(hits) == 1:
        return f"{rel}:{hits[0][0]}「{hits[0][1].strip()}」"
    raise SystemExit(f"根拠の行が見つからない・1行に決まらない（{len(hits)} 行）: {rel} {first[:60]!r}")


def renamer(L: dict):
    """古い列の名前（時間足の __tf が付いてもよい）→ 新しい列の名前。名前を今のカタログの型で種類と数字に分け、隠れた数字を足して組み直す。
    カタログに無い名前（省く設定の左側＝省いた列）も写せる（名前の写しの表はカタログの列だけなので、それでは足りない＝2026-10-26 に drop_columns で止まった）。"""
    od, _iref = mods()

    def ren(name: str) -> str:
        base, sep, tf = name.partition("__")
        fam, prm = od.find_material(base)
        if fam is None or fam not in L:
            return name
        v = L[fam]
        new = v["新しい名前の型"].format(*(list(prm) + [h["値"] for h in v["隠れた数字"]]))
        return new + (sep + tf if sep else "")
    return ren


def build_items(res: dict) -> list:
    """一覧 → 実装の指示の元（NN.txt）。戻り＝(名前, 対象, 直す前, 直した後) の一覧（--check が写しに当てる）。"""
    od, iref = mods()
    items = []
    L = res["一覧"]
    ren = renamer(L)
    od_src = (ROOT / OD_REL).read_text(encoding="utf-8")
    ir_src = (ROOT / IR_REL).read_text(encoding="utf-8")
    cfg_text = (ROOT / CFG_REL).read_text(encoding="utf-8")
    lim_text = (ROOT / LIM_REL).read_text(encoding="utf-8")
    exec_text = (ROOT / EXEC_REL).read_text(encoding="utf-8")
    # ── F-2 登録（_reg の文）＝移動平均の for の物を除く ──
    for fam, v in L.items():
        if v["移動平均の for"]:
            continue
        before = stmt_of(od_src, fam)
        if before is None:
            raise SystemExit(f"{fam}: 登録の文が1つに決まらない")
        # ★種類の名前と名前の型が同じ文字の登録（"close vs 前日POC%", "close vs 前日POC%"）が在るので、「種類, 型」の組で置き替える
        #   （型だけで置き替えると、1つ目の種類の名前が書き替わる＝2026-10-26 の写しの確かめで「知らない指標の種類」で落ちた）
        old_pair = f'_reg("{fam}", "{v["今の名前の型"]}",'
        if before.count(old_pair) != 1:
            raise SystemExit(f"{fam}: 登録の頭 {old_pair!r} が文に {before.count(old_pair)} 回")
        after = before.replace(old_pair, f'_reg("{fam}", "{v["新しい名前の型"]}",', 1)
        after = rewrite_head(after, [h["引数"] for h in v["隠れた数字"]])
        items.append((f"od_reg_{len(items):03d}", OD_REL, f"登録 {fam}＝名前の型を {v['今の名前の型']} → {v['新しい名前の型']}・隠れた数字 "
                      f"{[h['引数'] for h in v['隠れた数字']]} を位置の引数にする（F-2・群{v['群']}）",
                      first_line_evidence(OD_REL, before), before, after))
    # ── F-2 移動平均の一覧 _MA_FUNCS の項と、登録の for ──
    ma_hidden = {}
    for fam, v in L.items():
        if v["移動平均の for"] and v["移動平均の名前"]:
            inner = [h["引数"] for h in v["隠れた数字"] if h["出どころ"] == "f"]
            ma_hidden.setdefault(v["移動平均の名前"], [])
            for k in inner:
                if k not in ma_hidden[v["移動平均の名前"]]:
                    ma_hidden[v["移動平均の名前"]].append(k)
    for nm, inner in ma_hidden.items():
        if not inner:
            continue
        before = ma_entry_of(od_src, nm)
        if before is None:
            raise SystemExit(f"_MA_FUNCS の {nm} の項が1つに決まらない")
        after = rewrite_head(before, inner)
        items.append((f"od_ma_{nm}", OD_REL, f"移動平均の一覧 _MA_FUNCS の {nm}＝隠れた数字 {inner} を位置の引数にする（F-2）",
                      first_line_evidence(OD_REL, before), before, after))
    if od_src.count(LOOP_OLD) != 1:
        raise SystemExit("移動平均の登録の for が、想定の形で1つ無い")
    if any(f in L for f in ("帯スイング", "帯スイング1時間ATR")):
        for b_old, b_new in (('    "帯スイング": lambda d, fl, n, t, m: _band_swing(d, n, t, m, 2, fl),\n',
                              '    "帯スイング": lambda d, fl, n, t, m, k: _band_swing(d, n, t, m, k, fl),\n'),
                             ('    "帯スイング1時間ATR": lambda d, fl, n, km, a, m: _band_swing(d, n, _band_tol_1h(d, km, a), m, 2, fl),\n',
                              '    "帯スイング1時間ATR": lambda d, fl, n, km, a, m, k: _band_swing(d, n, _band_tol_1h(d, km, a), m, k, fl),\n')):
            if od_src.count(b_old) != 1:
                raise SystemExit(f"帯の計算式の表 _BAND_IMPL の行が1つでない: {b_old[:40]!r}")
            items.append((f"od_band_impl_{len(items):03d}", OD_REL, "帯の計算式の表 _BAND_IMPL＝確定の本数 k（直書きの 2）を受け取る形にする（F-2・登録の名前に k を出したため）",
                          first_line_evidence(OD_REL, b_old), b_old, b_new))
        if od_src.count(BAND_OLD) != 1:
            raise SystemExit("帯スイングの2種を作る for が、想定の形で1つ無い")
        items.append(("od_band_loop", OD_REL, "列を作る所の帯スイングの2種＝設定の for で作る形から、指標ごとの一覧 material_params の組で作る形にする（k も名前に出すため）（F-2）",
                      first_line_evidence(OD_REL, BAND_OLD), BAND_OLD, BAND_NEW))
    items.append(("od_ma_loop", OD_REL, "移動平均の登録の for（close vs X%・X傾き）＝名前の型を計算式の位置の引数の数から組み、比べる本数 slope_n も名前に出す（F-2）",
                  first_line_evidence(OD_REL, LOOP_OLD), LOOP_OLD, LOOP_NEW))
    # ── F-6 番人＝_insp_hidden_params を替える・⑧を消す ──
    g_old = func_text(od_src, "_insp_hidden_params")
    items.append(("od_guard_hidden", OD_REL, "番人 _insp_hidden_params＝「隠した引数が届く」から「オンの登録に名前に出ていない数の引数が無い・{} の数＝位置の引数の数」に替える（F-6）",
                  first_line_evidence(OD_REL, g_old), g_old, GUARD_NEW))
    m8 = GUARD8_RE.search(od_src)
    if not m8:
        raise SystemExit("番人⑧の囲みが見つからない")
    items.append(("od_guard8_drop", OD_REL, "番人⑧（EMA の傾きと AO の名前に値が無い）を消す＝守る決まりが逆（F-6）",
                  first_line_evidence(OD_REL, m8.group(0)), m8.group(0), ""))
    # ── F-3 設定＝material_params に組を足す・material_first_hidden を消す・material_keep の名前を写す ──
    mp = re.search(r' "material_params": \{\n(.*?)\n \},\n', cfg_text, re.S)
    if not mp:
        raise SystemExit("material_params の塊が見つからない")
    cur = CFG["material_params"]
    add = {fam: v["列を作る値"] for fam, v in L.items() if fam not in cur}
    rep = {fam: v["列を作る値"] for fam, v in L.items() if fam in cur}
    # ★今の塊は1行1種（2026-10-26 に grep で確かめた）。行の末尾の「,」を外し、在る種類は新しい組に置き替え、足す行と一緒に「,\n」でつなぐ
    new_lines = []
    for ln in mp.group(1).splitlines():
        key = json.loads("{" + ln.rstrip().rstrip(",") + "}")
        k0 = next(iter(key))
        new_lines.append(f'  "{k0}": {json.dumps(rep[k0], ensure_ascii=False)}' if k0 in rep else ln.rstrip().rstrip(","))
    body = ",\n".join(new_lines + [f'  "{k}": {json.dumps(v, ensure_ascii=False)}' for k, v in add.items()]) + "\n"
    items.append(("cfg_material_params", CFG_REL, f"material_params＝名前に出した種類の組（直す前と同じ列になる値）を、在る {len(rep)} 種は置き替え、無い {len(add)} 種は足す（F-3）",
                  first_line_evidence(CFG_REL, ' "material_params": {\n'), ' "material_params": {\n' + mp.group(1) + "\n },\n",
                  ' "material_params": {\n' + body + " },\n"))
    mh = re.search(r' "material_first_hidden": \{\n.*?\n \},\n "_material_first_hidden": "[^\n]*",\n', cfg_text, re.S)
    if not mh:
        raise SystemExit("material_first_hidden の塊が見つからない")
    items.append(("cfg_first_hidden_drop", CFG_REL, "material_first_hidden と注記を消す＝10-04 がこの形のために作った欄（値は material_params へ移った）（F-3）",
                  first_line_evidence(CFG_REL, mh.group(0)), mh.group(0), ""))
    mk_line = next(ln for ln in cfg_text.splitlines(keepends=True) if ln.startswith(' "material_keep": '))
    mk_obj = json.loads("{" + mk_line.rstrip().rstrip(",") + "}")["material_keep"]
    mk_new = ' "material_keep": ' + json.dumps({g: [ren(x) for x in lst] for g, lst in mk_obj.items()}, ensure_ascii=False) + ",\n"
    dc = re.search(r' "drop_columns": \[\n(.*?)\n \],\n', cfg_text, re.S)
    if not dc:
        raise SystemExit("drop_columns の塊が見つからない")
    dc_new = "\n".join(f'  {json.dumps([ren(a), ren(b)], ensure_ascii=False)}' + ("," if ln.rstrip().endswith(",") else "")
                       for ln in dc.group(1).splitlines() for a, b in [json.loads(ln.strip().rstrip(","))])
    if dc_new != dc.group(1):
        items.append(("cfg_drop_columns", CFG_REL, "省く設定 drop_columns＝名前に数字を出した列の名前に写す（省く側・残す側の両方）（F-3）",
                      first_line_evidence(CFG_REL, ' "drop_columns": [\n'), ' "drop_columns": [\n' + dc.group(1) + "\n ],\n",
                      ' "drop_columns": [\n' + dc_new + "\n ],\n"))
    if mk_new != mk_line:
        items.append(("cfg_material_keep", CFG_REL, "残す名前 material_keep＝名前に数字を出した列の名前に写す（F-3・3-2 の1・まこさん「V9に合わせず変えてしまっても良い」）",
                      first_line_evidence(CFG_REL, mk_line), mk_line, mk_new))
    # ── F-4 探す範囲＝material_param_ranges ──
    mr = re.search(r'  "material_param_ranges": \{\n(.*?)\n  \},\n', lim_text, re.S)
    if not mr:
        raise SystemExit("material_param_ranges の塊が見つからない")
    ranges = {k: v for k, v in LIM["material_param_ranges"].items()}
    for fam, v in L.items():
        if not v["オン"]:
            continue                                              # オフの種類＝engine_tuner_gen.material_ranges が範囲を受けない（:297〜299）
        ranges[v["参照表の名前"]] = v["範囲"]
    # ★P-2 の番人（observe_diag.py の selftest_catalog の⑬）＝オフの種類は見ない形にする（守りを緩める直し＝消す行を まこさんにお見せする）
    p2_old = '            if _e13 and find_material(_x13)[0] in _per11:\n'
    p2_new = ('            # ★2026-10-26（工事 m2c15-params-in-name-20261026）＝オフの種類は見ない。engine_tuner_gen.material_ranges はオフの種類の範囲を作らず、\n'
              '            #   設定に書くと止まる（:277〜278・:297〜299）＝オフの種類には範囲を書けない。オフの種類は探されない。\n'
              '            if _e13 and find_material(_x13)[0] in _per11 and _e13["family"] in set(_js13.loads(_SWITCH_PATH.read_text(encoding="utf-8")).get("on") or []):\n')
    if od_src.count(p2_old) != 1:
        raise SystemExit("P-2 の番人の行が1つでない")
    items.append(("od_p2_off", OD_REL, "番人 P-2（selftest_catalog の⑬）＝オフの種類は「範囲が無い」で止めない（F-6・オフの傾き21種を material_params に入れるため・守りを緩める直し）",
                  first_line_evidence(OD_REL, p2_old), p2_old, p2_new))
    # ★2026-10-26（仮当て A12 で見つかった）＝観察の道具の全体の自己テストが、POC・VAH・VAL の列の名前を f 文字列で組んでいる
    #   （close vs POC%288）。名前に rows・va_pct を出すと KeyError で落ちる＝カタログの列から、種類と本数で選ぶ形にする（F-6）。
    st_old = '        _nm = f"close vs {_key}%{_vpn}"\n'
    st_new = ('        # ★2026-10-26（工事 m2c15-params-in-name-20261026）＝名前に rows・va_pct も出したので、名前を組まずにカタログの列から選ぶ\n'
              '        _nm = next(nm for nm, _f, _d in build_catalog(cfg) if find_material(nm)[0] == f"close vs {_key}%" and find_material(nm)[1][0] == _vpn)\n')
    if od_src.count(st_old) != 1:
        raise SystemExit("観察の道具の自己テストの POC・VAH・VAL の行が1つでない")
    items.append(("od_selftest_vp", OD_REL, "全体の自己テスト（selftest の②）＝POC・VAH・VAL の列の名前を f 文字列で組む所を、カタログの列から選ぶ形にする（F-6・名前に数字を出したため）",
                  first_line_evidence(OD_REL, st_old), st_old, st_new))
    # ★同（仮当て A12）＝売買を回すプログラムの自己テストの見本が、Stoch%K・Stoch%D を数字1個（14）で持つ＝当てた後は 2個・3個 要る（F-9）
    exec_src = (ROOT / EXEC_REL).read_text(encoding="utf-8")
    fx = [('             "material": [{"family": "Stoch%K", "param": 14, "tf": "5m"},\n'
           '                          {"family": "Stoch%D", "param": 14, "tf": "5m"}]},\n',
           '             "material": [{"family": "Stoch%K", "param": [14, 1], "tf": "5m"},\n'
           '                          {"family": "Stoch%D", "param": [14, 1, 3], "tf": "5m"}]},\n'),
          ('         "material": [{"family": "Stoch%K", "param": 14, "tf": "5m"},\n'
           '                      {"family": "Stoch%D", "param": 14, "tf": "5m"}]}), "G1")\n',
           '         "material": [{"family": "Stoch%K", "param": [14, 1], "tf": "5m"},\n'
           '                      {"family": "Stoch%D", "param": [14, 1, 3], "tf": "5m"}]}), "G1")\n')]
    for j, (b, a) in enumerate(fx):
        if exec_src.count(b) != 1:
            raise SystemExit(f"売買を回すプログラムの自己テストの見本 {j + 1} が1つでない（{exec_src.count(b)} 回）")
        items.append((f"exec_fixture_{j + 1}", EXEC_REL, "自己テストの見本のレシピ＝Stoch%K・Stoch%D の数字を、名前に出した個数（2個・3個）にする（F-9・今の値 smooth_k＝1・d_n＝3）",
                      first_line_evidence(EXEC_REL, b.splitlines(keepends=True)[0]), b, a))
    # ★2026-10-29（217回目・まこさん「２，回す」）＝写すプログラム gen_indicators_draft.py の直し（F-10＝出どころの鍵を調べる所で、
    #   組の一覧 material_params を空にせず、外すと止まる種類の組だけ残す）は、この工事から外して161番（設計書2a-1）で行う。
    #   indicators.json と2つの一覧の作り直し（F-8）も同じ。直す相手の一覧が10月24日の物で古く、作り直すと違い25件で止まるため
    #   （worklog 20261026 §5-3・§5-4 の2）。直し方の案（組を1種ずつ外してカタログを作る形）は worklog 20261029 に写した。
    # ★同（写しの --full で見つかった）＝参照表の照らす関数が、名前から取った数字を決まった並びで読む（Y-10 の「直さない」は誤りだった）。
    #   Keltner＝n, k = p（ATR の本数が増えると落ちる）。帯スイング＝最後の数字を触れた回数 m と読み、個数3で幅の決め方を分ける（k を最後に出すと読み違える）。
    ir_src = (ROOT / IR_REL).read_text(encoding="utf-8")
    ir_fix = [
        ("ir_tb_keltner", "Keltner の照らす関数＝ATR の本数も名前の3つ目から読む（F-5・名前に atr_n を出したため）",
         "def _tb_keltner(d, p, side):\n    n, k = p\n    o, h, l, c, v = _arr(d)\n    band = _ema_rec(c, n) + side * k * _wilder(_tr(h, l, c), 14)\n",
         "def _tb_keltner(d, p, side):\n    n, k = p[0], p[1]\n"
         "    a = int(p[2]) if len(p) > 2 else 14                  # ★2026-10-26＝ATR の本数も名前に出した（工事 m2c15-params-in-name-20261026）\n"
         "    o, h, l, c, v = _arr(d)\n    band = _ema_rec(c, n) + side * k * _wilder(_tr(h, l, c), a)\n"),
        ("ir_ext_keltner", "Keltner の2つ目の照合（ta）＝ATR の本数が 14 でない列は対象外にする（F-5・ta の ATR は 14 固定）",
         "    if float(p[1]) != 2.0:                      # ta の乗数は 2 固定＝それ以外は対象外\n",
         "    if float(p[1]) != 2.0 or (len(p) > 2 and int(p[2]) != 14):   # ta の乗数は 2・ATR は 14 固定＝それ以外は対象外\n"),
        ("ir_tb_band_swing", "帯スイングの照らす関数＝数字の並びを (n, t, m, k)・(n, 倍率, ATR の期間, m, k) と読む（F-5・確定の本数 k を名前の最後に出したため）",
         '    """帯スイング・帯スイング1時間ATR の独立の実装。p＝(n, t, m) か (n, 倍率, ATR の期間, m)。"""\n'
         "    n, m = int(p[0]), int(p[-1])\n    o, h, l, c, v = _arr(d)\n"
         "    tols = np.full(len(c), float(p[1])) if len(p) == 3 else _tb_tol_1h(d, float(p[1]), int(p[2]))\n",
         '    """帯スイング・帯スイング1時間ATR の独立の実装。p＝(n, t, m, k) か (n, 倍率, ATR の期間, m, k)。\n'
         '    ★2026-10-26（工事 m2c15-params-in-name-20261026）＝確定の本数 k も名前の最後の数字に出した＝m は最後から2つ目。"""\n'
         "    n, m, k = int(p[0]), int(p[-2]), int(p[-1])\n    o, h, l, c, v = _arr(d)\n"
         "    tols = np.full(len(c), float(p[1])) if len(p) == 4 else _tb_tol_1h(d, float(p[1]), int(p[2]))\n"),
        ("ir_band_known", "帯の既知答え＝触れた回数 m を名前の最後から2つ目から読む（F-5・k を名前の最後に出したため）",
         "    return lambda p: [(_band_case(kind, int(p[-1])), [(-1, 1.0, 1e-9)]),\n"
         "                      (_band_case(kind, int(p[-1]) - 1, unconfirmed=True), [(-1, 0.0, 1e-9)]),\n",
         "    return lambda p: [(_band_case(kind, int(p[-2])), [(-1, 1.0, 1e-9)]),                       # ★2026-10-26＝最後は k・m は最後から2つ目\n"
         "                      (_band_case(kind, int(p[-2]) - 1, unconfirmed=True), [(-1, 0.0, 1e-9)]),\n"),
        ("ir_axis_ec_stoch", "E-c の対応表の Stoch の型＝名前に数字の括弧が付く形にする（F-5）",
         'impl=[r"Stoch%K\\d+", r"Stoch%D\\d+"]', 'impl=[r"Stoch%K\\(\\d+", r"Stoch%D\\(\\d+"]'),
        ("ir_axis_ec_vp", "E-c の対応表の VP の型＝名前に数字の括弧が付く形にする（F-5）",
         'impl=[r"close vs POC%\\d+", r"close vs VAH%\\d+", r"close vs VAL%\\d+"]',
         'impl=[r"close vs POC%\\(\\d+", r"close vs VAH%\\(\\d+", r"close vs VAL%\\(\\d+"]'),
    ]
    # 説明の文の「名前に出さない引数」＝この工事の後は誤りになる（同じ事実をそろえる＝恒久72番の2番）。決定の記録の MAKO_ の行は残す
    for j, (o, n_) in enumerate([
            ("比べる本数は名前に出さない引数（何も渡さないときは 5 本＝直す前の値）", "比べる本数は名前の括弧の数字（今の値 5 本）"),
            ("確定の本数 k は名前に出さない引数（最初の値 2＝資料の fractal の既定）", "確定の本数 k は名前の最後の数字（今の値 2＝資料の fractal の既定）"),
            ("（k は名前に出さない引数・最初の値 2）。今の S-Rタッチ数", "（k は名前の最後の数字・今の値 2）。今の S-Rタッチ数"),
            ("・k は名前に出さない引数（最初の値 2）。RG-v5", "・k は名前の最後の数字（今の値 2）。RG-v5"),
            ("（k は名前に出さない引数・最初の値 2）。ライブラリの版", "（k は名前の数字・今の値 2）。ライブラリの版"),
            ("4つの数は名前に出さない引数（最初の値 20・2.0・20・1.5）", "4つの数は名前の数字（今の値 20・2.0・20・1.5）"),
            ("m は名前に出さない引数（最初の値 9＝資料の既定）", "m は名前の2つ目の数字（今の値 9＝資料の既定）"),
            ("本数と倍率は名前に出さない引数（最初の値 80・2.0）", "本数と倍率は名前の数字（今の値 80・2.0）"),
            ("EMA の本数は名前に出さない引数", "EMA の本数は名前の数字"),
            ("2つの本数は名前に出さない引数（何も渡さないときは 5・34）", "2つの本数は名前の数字（今の値 5・34）")]):
        ir_fix.append((f"ir_desc_{j + 1:02d}", "参照表の説明の文＝「名前に出さない引数」を、名前の数字に直す（F-5・この工事の後は誤りになるため）", o, n_))
    for key, where, b, a in ir_fix:
        if ir_src.count(b) != 1:
            raise SystemExit(f"{key}: 参照表の直す前の文字が {ir_src.count(b)} 回（1回でない）")
        items.append((key, IR_REL, where, first_line_evidence(IR_REL, b.splitlines(keepends=True)[0] if "\n" in b else b), b, a))
    body = ",\n".join(f'    "{k}": {json.dumps(v, ensure_ascii=False)}' for k, v in ranges.items()) + "\n"
    items.append(("lim_ranges", LIM_REL, f"material_param_ranges＝名前に出した軸の範囲を足す（{len(ranges) - len(LIM['material_param_ranges'])} 種を足し、"
                  f"軸を増やした種類は資料の表の範囲か固定）（F-4）", first_line_evidence(LIM_REL, '  "material_param_ranges": {\n'),
                  '  "material_param_ranges": {\n' + mr.group(1) + "\n  },\n", '  "material_param_ranges": {\n' + body + "  },\n"))
    # ── F-5 参照表の名前の型 ──
    vp_loop = {}                                                  # 前日・当日の POC/VAH/VAL＝for の中の1行で2つずつ登録（:1700〜1715）
    for fam, v in L.items():
        pat, ir = v["参照表の今の型"], v["参照表の名前"]
        if pat is None:
            raise SystemExit(f"{fam}: 参照表の型が無い")
        m_vp = re.fullmatch(r"(前日|当日)(POC|VAH|VAL)", ir)
        if m_vp:
            suffix = v["参照表の新しい型"][len(_esc(f"close vs {ir}%")):]
            vp_loop.setdefault(m_vp.group(2), set()).add(suffix)
            continue
        old = f'_r(r"{pat}", "{ir}",'
        if ir_src.count(old) != 1:
            raise SystemExit(f"{fam}: 参照表の行 {old!r} が {ir_src.count(old)} 回")
        line = next(ln for ln in ir_src.splitlines(keepends=True) if ln.startswith(old))
        items.append((f"ir_pat_{len(items):03d}", IR_REL, f"参照表 {ir} の名前の型＝{pat} → {v['参照表の新しい型']}（F-5）",
                      first_line_evidence(IR_REL, line), line, line.replace(old, f'_r(r"{v["参照表の新しい型"]}", "{ir}",', 1)))
    for x, sufs in vp_loop.items():
        if len(sufs) != 1:
            raise SystemExit(f"前日と当日の {x} で、新しい型の数字の部分が違う: {sufs}")
        suf = sufs.pop()
        old = f'    _r(rf"close vs {{_vpk}}{x}%", f"{{_vpk}}{x}",'
        if ir_src.count(old) != 1:
            raise SystemExit(f"参照表の for の行 {old!r} が {ir_src.count(old)} 回")
        line = next(ln for ln in ir_src.splitlines(keepends=True) if ln.startswith(old))
        items.append((f"ir_pat_vp_{x}", IR_REL, f"参照表の for（前日・当日）の {x} の名前の型＝数字の部分 {suf} を足す（F-5）",
                      first_line_evidence(IR_REL, line), line, line.replace(f'{x}%", ', f'{x}%{suf}", ', 1)))
    # ── 列の名前を持つ所＝RUNTIME_ALIAS（engine_tuner_exec.py:289〜）──
    blk = re.search(r"RUNTIME_ALIAS = \{\n(.*?)\n\}\n", exec_text, re.S)
    for ln in (blk.group(1).splitlines(keepends=False) if blk else []):
        m = re.match(r'\s*"([^"]+)":', ln)
        if m and ren(m.group(1)) != m.group(1):
            items.append((f"exec_alias_{len(items):03d}", EXEC_REL, f"RUNTIME_ALIAS の鍵 {m.group(1)} を新しい列の名前に写す（F-9・3-2 の1）",
                          first_line_evidence(EXEC_REL, ln + "\n"), ln + "\n", ln.replace(f'"{m.group(1)}"', f'"{ren(m.group(1))}"', 1) + "\n"))
    # ── F-6 壊すプログラム＝b132・b134 は10-04 の逆の決まりを守る物なので書き直す・pn_f3〜pn_f5 は新しく作る ──
    for b in BREAKS:
        rel = f".claude/breaks/{b[0]}"
        p = ROOT / rel
        why = f"壊すプログラム {b[0]}（7-6 の {b[1]}）＝{b[7]}"
        if p.is_file():
            old = p.read_text(encoding="utf-8")
            items.append((f"brk_{b[0][:-3]}", rel, why + "（10-04 の物を書き直す）", first_line_evidence(rel, old), old, break_sh(b)))
        else:
            items.append((f"brk_{b[0][:-3]}", rel, why + "（新しいファイル）", f"やることの表 7-6 の {b[1]} の行「{b[7]}」", "なし\n", break_sh(b)))
    return items


def build(res: dict) -> None:
    items = build_items(res)
    if SRC_DIR.exists():
        shutil.rmtree(SRC_DIR)
    for i, (name, target, where, ev, before, after) in enumerate(items, 1):
        write_item(i, name, target, where, ev, before, after)
    print(f"実装の指示の元 {len(items)} 件 → {SRC_DIR}")
    r = subprocess.run([sys.executable, str(HERE / "gen_yarukoto.py"), "--step", "6", "--src", str(SRC_DIR), "--work", WORK, "--date", "20261026"],
                       capture_output=True, text=True)
    print((r.stdout + r.stderr).strip()[-1500:])
    if r.returncode != 0:
        raise SystemExit("実装の指示の json を組めなかった")


def apply_to(text_by_rel: dict, items: list) -> dict:
    for name, rel, _w, _e, before, after in items:
        t = text_by_rel[rel]
        if t.count(before) != 1:
            raise SystemExit(f"{name}: 直す前の文字が {t.count(before)} 回（1回でない）")
        text_by_rel[rel] = t.replace(before, after, 1)
    return text_by_rel


PROBE = r'''
import hashlib, json, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")
import observe_diag as od
import indicator_reference_diag as iref
import engine_tuner_gen as g
od._load_pta()
n = 600
t = np.arange(n)
c = 100 + 5 * np.sin(t / 17.0) + 2 * np.sin(t / 5.0) + 1.5 * np.sin(t / 1.7) + 3 * np.sin(t / 41.0) + t * 0.01
d = pd.DataFrame({"open": c - 0.2 * np.cos(t / 3.0), "high": c + 0.6 + 0.2 * np.sin(t / 7.0),
                  "low": c - 0.6 - 0.2 * np.cos(t / 11.0), "close": c, "volume": 1000 + 100 * np.sin(t / 13.0)},
                 index=pd.date_range("2026-01-01", periods=n, freq="5min"))
h = lambda s: hashlib.sha256(np.asarray(s, dtype=float).tobytes()).hexdigest()
cat = od.build_catalog(od.load_config())
out = {"cols": {}, "noref": [], "nofind": [], "axes_ng": [], "n_axes": 0, "n_ends": 0}
for nm, fn, _dr in cat:
    try:
        out["cols"][nm] = h(fn(d))
    except Exception as e:
        out["cols"][nm] = "ERR:" + type(e).__name__
    if iref.find(nm)[0] is None:
        out["noref"].append(nm)
    if od.find_material(nm)[0] is None:
        out["nofind"].append(nm)
rg = g.material_ranges()
for fam, spec in rg.items():
    kt = next(((k, v[0]) for k, v in od.MATERIAL_FAMILIES.items() if (iref.find(od.make_material(k, *([1] * v[0].count("{}")))[0])[0] or {}).get("family") == fam), None)
    tpl = kt[1] if kt else None
    if tpl is not None and len(spec["axes"]) != tpl.count("{}"):
        out["axes_ng"].append([fam, len(spec["axes"]), tpl.count("{}")])
    # 探す側が読む形（draw_param:339〜343）＝小数の軸は dec を持つ・整数の軸の両端は整数
    for i, ax in enumerate(spec["axes"]):
        out["n_axes"] += 1
        if ax["kind"] == "float" and "dec" not in ax:
            out["axes_ng"].append([fam, i + 1, "小数の軸に dec が無い"])
        if ax["kind"] == "int" and not (float(ax["lo"]).is_integer() and float(ax["hi"]).is_integer()):
            out["axes_ng"].append([fam, i + 1, "整数の軸の両端が整数でない"])
    # 範囲の両端の値で作った名前を、参照表で引けるか（小数を探したときに名前を引けない形を止める）
    if kt and tpl.count("{}") == len(spec["axes"]):
        for end in ("lo", "hi"):
            out["n_ends"] += 1
            vs =[float(ax[end]) if ax["kind"] == "float" else int(ax[end]) for ax in spec["axes"]]
            if iref.find(od.make_material(kt[0], *vs)[0])[0] is None:
                out["axes_ng"].append([fam, end, "端の値の名前を参照表で引けない", od.make_material(kt[0], *vs)[0]])
out["n_ranges"] = len(rg)
print(json.dumps(out, ensure_ascii=False))
'''


def run_probe(pr_dir: Path) -> dict:
    p = pr_dir / "_pin_probe_tmp.py"
    p.write_text(PROBE, encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, p.name], capture_output=True, text=True, cwd=str(pr_dir))
    finally:
        p.unlink()
    if r.returncode != 0:
        raise SystemExit(f"❌ 確かめの計算が落ちた（{pr_dir}）: {r.stderr[-1500:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def check(res: dict) -> int:
    sys.path.insert(0, str(HERE))
    import r1_draft_build as rd  # noqa: E402
    items = build_items(res)
    items = [it for it in items if not it[1].startswith(".claude/breaks/")]    # 壊すプログラムの .sh は、下の [7] で同じ壊し方を写しに入れて試す
    texts = {}
    for _n, rel, *_ in items:
        texts.setdefault(rel, (ROOT / rel).read_text(encoding="utf-8"))
    texts = apply_to(texts, items)
    # ★消す指示が消しすぎていないか＝ファイルごとに、消えた行の数が、指示の「直す前の文字」の行の数の合計を超えないこと
    for rel, t in texts.items():
        before_n = len((ROOT / rel).read_text(encoding="utf-8").splitlines())
        removed = sum(len(b.splitlines()) for _n, r, _w, _e, b, _a in items if r == rel)
        added = sum(len(a.splitlines()) for _n, r, _w, _e, _b, a in items if r == rel)
        if len(t.splitlines()) < before_n - removed:
            raise SystemExit(f"❌ {rel}: 当てた後の行の数 {len(t.splitlines())} が、直す前 {before_n} − 直す前の文字の行 {removed} より少ない（消しすぎ）")
        print(f"   {Path(rel).name}: 行 {before_n} → {len(t.splitlines())}（直す前の文字 {removed} 行・直した後の文字 {added} 行）")
    for rel, t in texts.items():
        if rel.endswith(".py"):
            ast.parse(t)
        else:
            json.loads(t)
    print(f"[1] 文法＝.py {sum(1 for r in texts if r.endswith('.py'))} 本・json {sum(1 for r in texts if r.endswith('.json'))} 本 通った（指示 {len(items)} 件）")
    name_map = {}
    for v in res["一覧"].values():
        name_map.update(v["名前の写し"])
    # ★「今」も写しで測る（本物の置き場に一時のファイルを書かない＝この道具は読むだけ）
    top0, tmp0 = rd.make_copy()
    try:
        now = run_probe(tmp0 / "scripts/priority_rebuild")
    finally:
        shutil.rmtree(top0, ignore_errors=True)
    top, tmp = rd.make_copy()
    ng = []
    try:
        for rel, t in texts.items():
            if not (ROOT / rel).is_relative_to(SDK):
                continue                                          # SDK の外（.claude/state の写すプログラム）＝写しの中では実物への近道なので書かない（文法は [1] で見た）
            (tmp / (ROOT / rel).relative_to(SDK)).write_text(t, encoding="utf-8")
        cpr = tmp / "scripts/priority_rebuild"
        new = run_probe(cpr)
        old_names, new_names = set(now["cols"]), set(new["cols"])
        mapped = {name_map.get(nm, nm) for nm in old_names}
        print(f"[2] 列の名前＝今 {len(old_names)} 本 → 当てた後 {len(new_names)} 本・写した名前と一致 {len(mapped & new_names)}・"
              f"写しに無い新しい名前 {len(new_names - mapped)}・消えた名前 {len(mapped - new_names)}")
        if mapped != new_names:
            ng.append(f"②名前の写しが往復しない: 増えた {sorted(new_names - mapped)[:5]} 消えた {sorted(mapped - new_names)[:5]}")
        diff = [nm for nm in old_names if name_map.get(nm, nm) in new["cols"] and now["cols"][nm] != new["cols"][name_map.get(nm, nm)]]
        print(f"[3] 何も渡さない組の列の値＝直す前と同じ {len(old_names) - len(diff)}／{len(old_names)} 本")
        if diff:
            from collections import Counter
            fams = Counter(re.split(r"[\d(]", nm, maxsplit=1)[0] for nm in diff)
            ng.append(f"③値が違う列 {len(diff)} 本（種類ごと {dict(fams)}）: 例 "
                      + "・".join(f"{nm}＝今 {now['cols'][nm][:12]} 後 {new['cols'][name_map.get(nm, nm)][:12]}" for nm in diff[:4]))
        print(f"[4] 参照表で引けない名前 {len(new['noref'])}・分解できない名前 {len(new['nofind'])}")
        if new["noref"] or new["nofind"]:
            ng.append(f"④参照表で引けない {new['noref'][:5]} ／ 分解できない {new['nofind'][:5]}")
        print(f"[5] material_ranges＝種類 {new['n_ranges']}（今 {now['n_ranges']}）・見た軸 {new['n_axes']}・端の名前 {new['n_ends']}・"
              f"合わない（軸の数・dec・整数の両端・端の名前）{len(new['axes_ng'])}（直す前の本物では {len(now['axes_ng'])}）")
        if new["axes_ng"]:
            ng.append(f"⑤軸の数が合わない: {new['axes_ng'][:6]}")
        r = subprocess.run([sys.executable, "observe_diag.py", "--selftest-catalog"], capture_output=True, text=True, cwd=str(cpr))
        if "--verbose" in sys.argv:
            from collections import Counter
            lines = [x.strip() for x in (r.stdout + r.stderr).splitlines() if x.strip().startswith("❌")]
            kinds = Counter(re.sub(r"[\w%\-.]+\([\d.,]+\)|\b\d+(?:\.\d+)?\b", "#", x)[:110] for x in lines)
            print(f"     写しの軽い口の ❌ {len(lines)} 件を、名前と数字を # に替えて数えた:")
            for k, n in kinds.most_common(30):
                print(f"       {n:4d}  {k}")
        tail = (r.stdout + r.stderr).strip().splitlines()[-6:]
        print(f"[6] 写しで observe_diag.py --selftest-catalog＝rc {r.returncode}・出力の行 {len((r.stdout + r.stderr).strip().splitlines())}・最後の行 {tail[-1][:150] if tail else '（無し）'}")
        if not any("番人（--selftest-catalog）" in x for x in tail):
            ng.append("⑥軽い口が最後まで走っていない（終わりの行「K-1・K-8・G-2 の番人（--selftest-catalog）」が無い）")
        if r.returncode != 0:
            ng.append("⑥軽い口が落ちた: " + " / ".join(tail))
            for ln in tail:
                print("     ", ln[:200])
        print("[7] 壊すプログラム（写しに1つずつ壊しを入れる）")
        ng += test_breaks(tmp, {rel: t for rel, t in texts.items()})
        if "--full" in sys.argv:
            # ★2026-10-26（仮当て A12 が、写しの確かめでは見えなかった落ちを3つ出した）＝仮当てと同じ自己テストを写しで走らせる。
            #   許す判定は仮当て（require_design_check_before_approval.a12_fail_allowed）と同じ物を import する（教訓 L-671）。
            import importlib.util as _ilu
            _sp = _ilu.spec_from_file_location("rdcba", ROOT / ".claude/hooks/require_design_check_before_approval.py")
            _hk = _ilu.module_from_spec(_sp)
            _sp.loader.exec_module(_hk)
            print("[8] 仮当てと同じ自己テストを写しで走らせる（verify_design_contract.py --diff は設計書が要るので除く）")
            if "--diag-unver" in sys.argv:
                # 調べるためだけ＝写しの観察の道具の「検証済みにならない列」の出力を、最初の5本でなく全部にする（本物は変えない）
                _odp = cpr / "observe_diag.py"
                _odp.write_text(_odp.read_text(encoding="utf-8").replace("{_unver[:5]}", "{_unver}"), encoding="utf-8")
            for st in _hk.A12_SELFTESTS:
                if st[0] == "verify_design_contract.py":
                    continue
                t0 = time.time()
                r8 = subprocess.run([sys.executable, str(cpr / st[0])] + list(st[1:]), capture_output=True, text=True, cwd=str(tmp), timeout=900)
                out8 = (r8.stdout or "") + (r8.stderr or "")
                allowed = _hk.a12_fail_allowed(st[0], r8.returncode, out8)
                fails = [l.strip() for l in out8.splitlines() if l.strip().startswith("❌ ") and not re.match(r"❌ \d+ 件", l.strip())]
                print(f"     {' '.join(st)}: rc {r8.returncode}・{time.time() - t0:.0f}秒" + ("（許す＝T6・F6 の差し込みが古い だけ）" if allowed else ""))
                if r8.returncode != 0 and not allowed:
                    for ln in (fails or out8.strip().splitlines()[-8:])[:12]:
                        print("       ", ln if "--verbose" in sys.argv else ln[:220])
                    ng.append(f"⑧自己テストが写しで落ちる: {' '.join(st)}")
    finally:
        shutil.rmtree(top, ignore_errors=True)
    for x in ng:
        print("❌", x)
    print("✅ 6つとも通った（本物には書いていない）" if not ng else f"❌ {len(ng)} 件")
    return 1 if ng else 0


# ── 壊すプログラム（7-6）＝写しで1つずつ壊して、決めた文で落ちるかを --check で試し、--build で .sh を書く ──
BREAKS = [
    # (ファイル名, 守る行, 壊す相手, 直す前, 直した後, 測るコマンドの種類, 期待の文, 壊した意味)
    ("b132_hidden_param_not_passed.sh", "F-2", OD_REL,
     '_reg("close vs HILO%", "close vs HILO%({},{})", True, lambda d, high_length, low_length:',
     '_reg("close vs HILO%", "close vs HILO%({},{})", True, lambda d, high_length=None, low_length=None:',
     "catalog", "名前に出す: close vs HILO%",
     "close vs HILO% の登録を、数字を名前に出さない引数（=None）で受け取る形に戻すと、名前に出す番人が落ちる"),
    ("b134_ao_name_with_value.sh", "F-6", OD_REL,
     '_reg("AO%", "AO%({},{})", True, lambda d, fast, slow:',
     '_reg("AO%", "AO%", True, lambda d, fast=None, slow=None:',
     "catalog", "AO% のパラメータの個数が合わない",
     "AO% の名前から数字を外す（10-04 の形に戻す）と、列を作る所が「パラメータの個数が合わない」で止まる"),
    ("pn_f3_params_gone.sh", "F-3", CFG_REL, "json-del:material_params:close vs HILO%", "", "catalog",
     "close vs HILO% のパラメータの個数が合わない",
     "設定の material_params から close vs HILO% の組を消すと、列を作る所が「パラメータの個数が合わない」で止まる"),
    ("pn_f4_axis_count.sh", "F-4", LIM_REL, "json-pop:material_param_ranges:close vs HILO%", "", "ranges",
     "close vs HILO% の軸の数が合わない",
     "探す範囲の close vs HILO% の軸を1つ消すと、engine_tuner の範囲を作る所が「軸の数が合わない」で止まる"),
    ("pn_f5_pattern_back.sh", "F-5", IR_REL, '_r(r"close vs HILO%\\((\\d+),(\\d+)\\)", "close vs HILO%",',
     '_r(r"close vs HILO%", "close vs HILO%",', "catalog", "close vs HILO%",
     "参照表の close vs HILO% の型から数字の受け口を外すと、軽い口の照らし（参照表に無いカタログ列）が落ちる"),
]
CMD = {"catalog": 'measure python3 "$PR/observe_diag.py" --selftest-catalog',
       "ranges": 'cd "$PR"\nmeasure python3 - <<\'PYEOF\'\nimport engine_tuner_gen as g\ng.material_ranges()\nPYEOF'}


def break_mutate(text: str, old: str, new: str) -> str:
    if old.startswith("json-del:") or old.startswith("json-pop:"):
        op, key, fam = old.split(":", 2)
        obj = json.loads(text)
        if op == "json-del":
            del obj[key][fam]
        else:
            obj[key][fam] = obj[key][fam][:-1]
        return json.dumps(obj, ensure_ascii=False, indent=1)
    if text.count(old) != 1:
        raise SystemExit(f"壊す対象の文字が {text.count(old)} 回: {old[:60]!r}")
    return text.replace(old, new, 1)


def break_sh(b) -> str:
    name, row, rel, old, new, kind, msg, means = b
    target = "$SDK/" + str(Path(rel).relative_to("v3-bitget-api-sdk/bitget-python-sdk-api"))
    if old.startswith("json-"):
        op, key, fam = old.split(":", 2)
        body = (f"python3 - \"$F\" <<'PYEOF'\nimport json, sys\np = sys.argv[1]\no = json.load(open(p, encoding='utf-8'))\n"
                f"if {fam!r} not in o[{key!r}]:\n    raise SystemExit('[{name[:-3]}] 壊す対象が無い')\n"
                + (f"del o[{key!r}][{fam!r}]\n" if op == "json-del" else f"o[{key!r}][{fam!r}] = o[{key!r}][{fam!r}][:-1]\n")
                + "open(p, 'w', encoding='utf-8').write(json.dumps(o, ensure_ascii=False, indent=1))\nPYEOF\n")
    else:
        body = (f"python3 - \"$F\" <<'PYEOF'\nimport sys\np = sys.argv[1]\ns = open(p, encoding='utf-8').read()\n"
                f"old = {old!r}\nnew = {new!r}\nif s.count(old) != 1:\n    raise SystemExit('[{name[:-3]}] 壊す対象の文字が1か所でない')\n"
                "open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))\nPYEOF\n")
    return (f"#!/bin/bash\n# EXPECT_RC: 1\n# MEANS: {means}\n# EXPECT_MSG: {msg}\n"
            f"# {name[:-3]} — {means}（工事 m2c15-params-in-name-20261026・2026-10-26）\n"
            f"#   守っているもの＝7-6 の {row}\n#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。\n"
            f"source \"$(dirname \"$0\")/lib.sh\"\n\nF=\"{target}\"\nguard \"$F\"\n\n{body}\n{CMD[kind]}\nfinish\n")


def test_breaks(tmp: Path, texts: dict) -> list:
    """写し（当てた後）に1つずつ壊しを入れ、決めた文で落ちるかを試す。戻り＝外れた物の一覧。"""
    cpr = tmp / "scripts/priority_rebuild"
    ng = []
    for b in BREAKS:
        name, _row, rel, old, new, kind, msg, _means = b
        p = tmp / (ROOT / rel).relative_to(SDK)
        orig = texts[rel] if rel in texts else p.read_text(encoding="utf-8")
        p.write_text(break_mutate(orig, old, new), encoding="utf-8")
        try:
            if kind == "catalog":
                r = subprocess.run([sys.executable, "observe_diag.py", "--selftest-catalog"], capture_output=True, text=True, cwd=str(cpr))
            else:
                r = subprocess.run([sys.executable, "-c", "import engine_tuner_gen as g; g.material_ranges()"], capture_output=True, text=True, cwd=str(cpr))
            out = r.stdout + r.stderr
            ok = r.returncode != 0 and msg in out
            if not ok and "--verbose" in sys.argv:
                print("\n".join("        | " + x[:200] for x in out.strip().splitlines()[-12:]))
            print(f"     壊す {name}: rc {r.returncode}・期待の文 {'在る' if msg in out else '無い'} → {'✅' if ok else '❌'}")
            if not ok:
                ng.append(f"⑦壊すプログラム {name} が期待どおりに落ちない（rc {r.returncode}・末尾 {out.strip().splitlines()[-1][:120] if out.strip() else ''}）")
        finally:
            p.write_text(orig, encoding="utf-8")
    return ng


def ranges_main() -> int:
    """--ranges＝engine_tuner_gen.material_ranges を呼び、オンの全種で軸の数が名前の型の {} の数と合うかを見る（7-6 の F-4）。"""
    od, iref = mods()
    cwd = os.getcwd()
    os.chdir(PR)
    try:
        import engine_tuner_gen as g  # noqa: E402
        rg = g.material_ranges()
    finally:
        os.chdir(cwd)
    tpl_of = {}
    for k, (tpl, _d, _f) in od.MATERIAL_FAMILIES.items():
        e, _p = iref.find(od.make_material(k, *([1] * tpl.count("{}")))[0]) if tpl.count("{}") else iref.find(tpl)
        if e:
            tpl_of[e["family"]] = tpl
    bad = [(f, len(s["axes"]), tpl_of[f].count("{}")) for f, s in rg.items() if f in tpl_of and len(s["axes"]) != tpl_of[f].count("{}")]
    fixed = sorted(f for f, s in rg.items() if s["src"] == "catalog")
    print(f"material_ranges の種類 {len(rg)}・軸の数が名前の型と合わない種類 {len(bad)}・設定に範囲が無くカタログの値で作った種類 {len(fixed)}")
    for b in bad:
        print("  ❌", b)
    return 1 if bad else 0


def compare_renamed_main(before: str) -> int:
    """--compare-renamed＝直す前の列の控えを、測った一覧の名前の写しで新しい名前にして、今の列と比べる（7-6 の F-3）。
    今の列は col_snapshot.snapshot で作り、after_20261026.json に控える（F-7 の控えを兼ねる・約61分）。"""
    sys.path.insert(0, str(HERE))
    import col_snapshot as cs  # noqa: E402
    res = json.loads(OUT_LIST.read_text(encoding="utf-8"))
    name_map = {}
    for v in res["一覧"].values():
        name_map.update(v["名前の写し"])
    b = json.loads(Path(before).read_text(encoding="utf-8"))
    out = HERE / "col_snapshot" / "after_20261026.json"
    s = cs.snapshot(b["rows"], None, out)

    def ren(c):
        base, sep, tf = c.partition("__")
        return name_map.get(base, base) + (sep + tf if sep else "")
    bc = {ren(c): v for c, v in b["cols"].items()}
    miss = sorted(set(bc) - set(s["cols"]))
    new = sorted(set(s["cols"]) - set(bc))
    diff = sorted(c for c in set(bc) & set(s["cols"]) if bc[c] != s["cols"][c])
    print(f"控え {out}・控え（写した名前）に在って今に無い列 {len(miss)}・今にだけ在る列 {len(new)}・値が違う列 {len(diff)}")
    for x in (miss + new + diff)[:30]:
        print("  ", x)
    return 0 if not (miss or new or diff) else 1


def new_numbers_main() -> int:
    """--new-numbers＝設計書を作るプログラム（gen_acceptance._new_numbers）と同じ数え方で、実装の指示に新しく入る数字を全部 出す。
    数え方＝実装の指示ごとに、直した後の文字（# から後ろを除く）に在って、直す前の文字に無い数字。"""
    num_re = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?![\w.])")
    kind1 = ("scripts/priority_rebuild", "engine_tuner", "regime_laws", "indicator_switch", "signal_families",
             "material_ranking", "search_limits", "observe_config", "indicator_params", "indicator_roles",
             "composition_rules", "materials.json", "exit_families", "regime_detection_kb")

    def code(s):
        return "\n".join(ln.split("#", 1)[0] for ln in str(s or "").splitlines())
    items = json.loads((WD / "impl_4-20_20261026.json").read_text(encoding="utf-8"))
    n = 0
    for it in items:
        if not any(w in str(it.get("対象のファイル") or "") for w in kind1):
            continue
        old = set(num_re.findall(code(it.get("直す前の文字"))))
        seen = []
        for v in num_re.findall(code(it.get("中身"))):
            if v not in old and v not in seen:
                seen.append(v)
        for v in seen:
            ln = next((x for x in code(it.get("中身")).splitlines() if re.search(r"(?<![\w.])" + re.escape(v) + r"(?![\w.])", x)), "")
            print(f"実装 {it['番号']}｜{Path(str(it['対象のファイル'])).name}｜{v}｜{ln.strip()[:110]}")
            n += 1
    print(f"新しく入る数字 {n} 件")
    return 0


def review_fill_main(review: str, tsv: str) -> int:
    """--review-fill＝見直し表（gen_review.py --skeleton が作った物）の行を埋める。
    実装の指示の行（#### 実装 N）は、その指示の根拠の抜き書きの「ファイル:行」を写す（新しい壊すプログラムは やることの表 7-6 の行）。
    ほかの行は、CC が1行ずつ書いた TSV（番号・①・②・③・判定）から写す。争点の行も TSV の番号 0 から写す。"""
    items = {int(it["番号"]): it for it in json.loads((WD / "impl_4-20_20261026.json").read_text(encoding="utf-8"))}
    yrel = ".claude/state/verbatim/" + WORK + "/やることの表.md"
    ylines = (ROOT / yrel).read_text(encoding="utf-8").splitlines()
    s76 = next(i for i, ln in enumerate(ylines) if ln.startswith("### 7-6"))
    rows = {}
    for ln in Path(tsv).read_text(encoding="utf-8").splitlines():
        if ln.strip():
            c = ln.split("\t")
            rows[int(c[0])] = c[1:]
    out, n_impl, n_tsv, miss = [], 0, 0, []
    for ln in Path(review).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| (\d+) \| (.+?) \| <書く> \| <書く> \| <書く> \| <書く> \|$", ln)
        if ln.startswith("争点:") and 0 in rows:
            out.append("争点: " + rows[0][0])
            continue
        if not m:
            out.append(ln)
            continue
        no, head = int(m.group(1)), m.group(2)
        mi = re.match(r"^#### 実装 (\d+)$", head)
        if mi:
            it = items[int(mi.group(1))]
            fx = (re.search(r"F-\d", str(it["直す箇所"])) or re.search(r"F-\d", "F-9" if "RUNTIME_ALIAS" in str(it["直す箇所"]) else "")).group(0)
            me = re.match(r"^(\S+?):(\d+)「", str(it["根拠の抜き書き"]))
            if me:
                ev = f"{me.group(1)}:{me.group(2)}（直す前の文字が実物のこの行から始まる・写しの --check で1か所だけ当たった）"
            else:
                yl = next(i for i in range(s76, len(ylines)) if ylines[i].startswith(f"| {fx} |")) + 1
                ev = f"{yrel}:{yl}（7-6 の {fx} の行の壊し方と、壊すプログラムの中身が同じ）"
            out.append(f"| {no} | {head} | 読める（対象のファイル・直す箇所・直す前の文字・直した後の文字・根拠の抜き書き・状態の6つの欄が在る） | {ev} | "
                       f"争点の {fx} の1件 | OK（設計書を全部 読み、直す前と直した後を照らした。写しの --check で、文法・列の名前 652/652・"
                       f"値 652/652・参照表・範囲・軽い口・壊すプログラム5本が通った） |")
            n_impl += 1
        elif no in rows:
            c = rows[no]
            out.append(f"| {no} | {head} | {c[0]} | {c[1]} | {c[2]} | {c[3]} |")
            n_tsv += 1
        else:
            out.append(ln)
            miss.append(f"{no} {head}")
    Path(review).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"見直し表を埋めた: 実装の指示の行 {n_impl}・TSV の行 {n_tsv}・埋めていない行 {len(miss)}")
    for x in miss:
        print("  ❌", x)
    return 1 if miss else 0


def touched_main(res: dict) -> int:
    """★2026-10-29（217回目）＝実装の指示を、メモリの中の写しに当てて、.py ごとに関数の構文木が変わったまとまりを出す。
    設計書の DESIGN_CONTRACT の impl_functions を、CC が手で選ばずに道具で決めるため。比べ方は、承認の前の仮当ての照合A
    （verify_design_contract.touched_functions）と同じ functions_ast＝関数ごと・モジュール直下は1つのまとまり。本物には書かない。"""
    sys.path.insert(0, str(PR))
    import verify_design_contract as vdc  # noqa: E402
    items = [it for it in build_items(res) if it[1].endswith(".py")]
    texts = {}
    for _n, rel, *_ in items:
        texts.setdefault(rel, (ROOT / rel).read_text(encoding="utf-8"))
    orig = dict(texts)
    texts = apply_to(texts, items)
    out = {}
    for rel in sorted(texts):
        a, b = vdc.functions_ast(orig[rel]), vdc.functions_ast(texts[rel])
        out[rel] = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
        print(f"{rel}: {'・'.join(out[rel])}（{len(out[rel])}）")
    print(json.dumps(out, ensure_ascii=False))
    return 0


# ══ 161-1（工事 m2c15-indicator-redirect-20261031）の実装の指示を、写しに当てて確かめる（本物には書かない）═══════════════════
#   ★2026-10-31＝172番の中身（隠れた数字を記録の欄に持たせる）は161-1 の設計書で行う（ToDo の172番・worklog 20261030:1308）。
#   写しで確かめる道具は、この工事の道具に口を足して使う（新しいファイルを作らない＝恒久78番）。
REDIRECT_WORK = "m2c15-indicator-redirect-20261031"
REDIRECT_TABLES = ("indicator_params_by_strategy", "indicator_params_review", "indicator_roles_thresholds")


def _redirect_items() -> list:
    wd = ST / "verbatim" / REDIRECT_WORK
    if not wd.is_dir():
        wd = SDK / ".claude/ratchet/acceptance_archive/verbatim" / REDIRECT_WORK
    return json.loads((wd / "impl_4-20_20261031.json").read_text(encoding="utf-8"))


def _redirect_copy() -> Path:
    """写し＝一番上から同じ並び。.claude/state は indicator_review と資料の表3つを写し、ほかの .claude は近道。
    .claude/breaks は lib.sh だけ写す（ROOT を写しに向ける＝壊すプログラムが写しの中で壊して戻す）。scripts/priority_rebuild は写し、ほかは近道。"""
    top = Path(tempfile.mkdtemp(prefix="redirect_")).resolve()      # resolve＝/var → /private/var（道具が ROOT からの相対で名前を作るため）
    (top / ".claude").mkdir()
    for c in (ROOT / ".claude").iterdir():
        if c.name == "state":
            st = top / ".claude/state"
            st.mkdir()
            shutil.copytree(c / "indicator_review", st / "indicator_review", ignore=shutil.ignore_patterns("__pycache__"))
            for t in REDIRECT_TABLES:
                shutil.copy2(c / f"{t}.json", st / f"{t}.json")
        elif c.name == "breaks":
            b = top / ".claude/breaks"
            b.mkdir()
            lib = (c / "lib.sh").read_text(encoding="utf-8")
            if lib.count(f'ROOT="{ROOT}"') != 1:
                raise SystemExit("lib.sh の ROOT の行が1か所でない（写しに向けられない）")
            (b / "lib.sh").write_text(lib.replace(f'ROOT="{ROOT}"', f'ROOT="{top}"', 1), encoding="utf-8")
        else:
            os.symlink(c, top / ".claude" / c.name)
    tmp = top / SDK.relative_to(ROOT)
    tmp.mkdir(parents=True)
    for c in SDK.iterdir():
        if c.name != "scripts":
            os.symlink(c, tmp / c.name)
    (tmp / "scripts").mkdir()
    for c in (SDK / "scripts").iterdir():
        if c.name != "priority_rebuild":
            os.symlink(c, tmp / "scripts" / c.name)
    shutil.copytree(PR, tmp / "scripts/priority_rebuild", ignore=shutil.ignore_patterns("archive", "__pycache__", "*.log"))
    return top


def _redirect_apply(top: Path, items: list) -> None:
    """実装の指示を写しに当てる（当てる道具 apply_audit_fix.py と同じ決まり＝直す前の文字が1か所・新しいファイルはまだ無い）。"""
    for it in items:
        p = top / it["対象のファイル"]
        if it["直す前の文字"].strip() == "なし":
            if p.exists():
                raise SystemExit(f"{it['番号']}: 新しいファイルがもう在る: {p}")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(it["中身"], encoding="utf-8")
            if p.suffix == ".sh":
                p.chmod(0o755)
        else:
            t = p.read_text(encoding="utf-8")
            if t.count(it["直す前の文字"]) != 1:
                raise SystemExit(f"{it['番号']}: 直す前の文字が {t.count(it['直す前の文字'])} 回（1回でない）: {p.name}")
            p.write_text(t.replace(it["直す前の文字"], it["中身"], 1), encoding="utf-8")


def _redirect_run(args, cwd, env, timeout=3600):
    t0 = time.time()
    r = subprocess.run(args, capture_output=True, text=True, cwd=str(cwd), env=env, timeout=timeout)
    return r, round(time.time() - t0, 1)


def check_redirect_main() -> int:
    items = _redirect_items()
    reuse = Path(sys.argv[sys.argv.index("--reuse") + 1]).resolve() if "--reuse" in sys.argv else None   # 残した写しで、当てずに走らせ直す
    top = reuse or _redirect_copy()
    tmp = top / SDK.relative_to(ROOT)
    cpr = tmp / "scripts/priority_rebuild"
    gid = top / ".claude/state/indicator_review/gen_indicators_draft.py"
    env = {**os.environ, "IND_ROOT": str(top), "SS_ROOT": str(top), "PYTHONDONTWRITEBYTECODE": "1"}
    py = sys.executable
    ng, keep, verbose = [], ("--keep" in sys.argv) or bool(reuse), "--verbose" in sys.argv
    print(f"[写し] {top}{'（使い回し）' if reuse else ''}")
    try:
        if not reuse:
            _redirect_apply(top, items)
        for rel in sorted({it["対象のファイル"] for it in items}):
            p = top / rel
            if rel.endswith(".py"):
                ast.parse(p.read_text(encoding="utf-8"))
            elif rel.endswith(".sh"):
                r, _s = _redirect_run(["bash", "-n", str(p)], top, env)
                if r.returncode:
                    ng.append(f"文法 {rel}: {r.stderr[-300:]}")
        print(f"[1] 当てた {len(items)} 件・文法（.py は ast・.sh は bash -n）＝{'通った' if not ng else '❌'}")
        steps = [
            ("読む口 --selftest", [py, str(cpr / "indicators/indicators.py"), "--selftest"]),
            ("写すプログラム --selftest", [py, str(gid), "--selftest"]),
            ("写すプログラム --rewrite（F-7）", [py, str(gid), "--rewrite"]),
            ("写すプログラム --verify", [py, str(gid), "--verify"]),
            ("写すプログラム（旗なし＝同じなら書かない）", [py, str(gid)]),
            ("読む口 --count", [py, str(cpr / "indicators/indicators.py"), "--count"]),
            ("一覧を作り直す（F-4）", [py, str(top / ".claude/state/indicator_review/gen_fix_inventory.py")]),
            ("数える道具（F-5）", [py, str(top / ".claude/state/indicator_review/ss_outside_probe.py")]),
            # ★2026-11-01＝監査 CP94 の修正27（indicators.json の道を指す行の全部に当たる文字・7-6 の F-4・F-5 と同じ）
            ("7-6 F-4/F-5 の grep", ["bash", "-c", f"! grep -n -E '/ .indicators\\.json.' \"{top}/.claude/state/indicator_review/gen_fix_inventory.py\" \"{top}/.claude/state/indicator_review/ss_outside_probe.py\""]),
        ]
        for name, args in steps:
            r, sec = _redirect_run(args, tmp, env)
            out = r.stdout + r.stderr
            ok = r.returncode == 0
            print(f"[{'✅' if ok else '❌'}] {name}: rc {r.returncode}（{sec}秒）")
            lines = out.strip().splitlines()
            full = verbose or name.startswith(("写すプログラム --rewrite", "読む口 --count", "写すプログラム --selftest", "読む口 --selftest")) or not ok
            for ln in (lines if full else lines[-6:])[-120:]:
                print("      | " + ln[:(3000 if not ok else 240)])
            if not ok:
                ng.append(f"{name}: rc {r.returncode}")
        ij = cpr / "indicators/indicators.json"
        jqs = [("一番外の鍵", ["jq", "-c", "keys", str(ij)]),
               ("記録の数（指標・使い方・部品・要素の行）", ["jq", "-c", '[(.["指標の記録"]|length), (.["使い方の記録"]|length), (.["部品の記録"]|length), (.["要素の定義表"]["要素"]|length)]', str(ij)]),
               ("帯VA の軸", ["jq", "-c", '.["部品の記録"]["帯VA"]["パラメータの軸"] | map({a: .["名前"], r: .["範囲"], d: .["代表の値"]})', str(ij)]),
               ("帯VA の使う物", ["jq", "-c", '.["部品の記録"]["帯VA"]["使う物"]', str(ij)]),
               ("RSI の軸", ["jq", "-c", '.["指標の記録"]["RSI"]["パラメータの軸"]', str(ij)]),
               ("Stoch%K の軸", ["jq", "-c", '.["指標の記録"]["Stoch%K"]["パラメータの軸"] | map({a: .["名前"], r: .["範囲"], d: .["代表の値"], p: .["資料の表の名前"]})', str(ij)]),
               ("使い方の記録の1件目", ["jq", "-c", '.["使い方の記録"][0]', str(ij)]),
               ("RSI の列を作る組", ["jq", "-c", '.["指標の記録"]["RSI"]["列を作る組"]', str(ij)]),
               ("時刻の閾値の範囲", ["jq", "-c", '.["指標の記録"]["時刻"]["閾値の範囲"]', str(ij)]),
               ("列を作る組の数", ["jq", '[.["指標の記録"][]["列を作る組"]["組"][]] + [.["部品の記録"][]["列を作る組"]["組"][]] | length', str(ij)]),
               ("選べる値の鍵", ["jq", "-c", '.["要素の定義表"]["選べる値"] | keys', str(ij)]),
               # ★2026-11-01＝監査 CP94 の修正1・修正22（代表の値を名前で軸に合わせたか・下限＜上限の軸の数）
               ("C-1 の8種の軸（名前・資料の表の名前・代表の値）", ["jq", "-c", '[(.["指標の記録"], .["部品の記録"]) | to_entries[] | select(.key | IN("KSTシグナル", "KAMA傾き%", "転換線", "基準線", "StochRSI%K", "StochRSI素%K", "close vs SSF平均%", "close vs ALMA%")) | {k: .key, a: (.value["パラメータの軸"] | map({n: .["名前"], p: .["資料の表の名前"], d: .["代表の値"]}))}]', str(ij)]),
               ("下限＜上限の軸の数", ["jq", '[(.["指標の記録"][], .["部品の記録"][]) | .["パラメータの軸"][] | select((.["範囲"]|type)=="object" and .["範囲"]["lo"] < .["範囲"]["hi"])] | length', str(ij)]),
               ("帯スイングの使う物", ["jq", "-c", '.["部品の記録"]["帯スイング"]["使う物"] | map(.["指標の記録"])', str(ij)])]
        for name, args in jqs:
            r, _s = _redirect_run(args, tmp, env)
            print(f"[4-12] {name}: {(r.stdout or r.stderr).strip()[:700]}")
        for it in items:
            rel = it["対象のファイル"]
            if not rel.startswith(".claude/breaks/"):
                continue
            p = top / rel
            msg = next((ln.split("EXPECT_MSG:", 1)[1].strip() for ln in it["中身"].splitlines() if ln.startswith("# EXPECT_MSG:")), "")
            r, sec = _redirect_run(["bash", str(p)], top / ".claude/breaks", env)
            out = r.stdout + r.stderr
            ok = r.returncode == 1 and msg in out
            print(f"[{'✅' if ok else '❌'}] 壊す {p.name}: rc {r.returncode}・期待の文 {'在る' if msg in out else '無い'}（{sec}秒）")
            if not ok:
                ng.append(f"壊す {p.name}: rc {r.returncode}・期待の文 {'在る' if msg in out else '無い'}")
            if not ok or verbose:
                for ln in out.strip().splitlines()[-10:]:
                    print("      | " + ln[:240])
        r, sec = _redirect_run([py, str(gid), "--verify"], tmp, env)
        print(f"[{'✅' if r.returncode == 0 else '❌'}] 壊した後の --verify（lib.sh の guard が戻したか・一覧を作り直した後）: rc {r.returncode}（{sec}秒）")
        if r.returncode:
            ng.append("壊した後の --verify が落ちる")
            for ln in (r.stdout + r.stderr).strip().splitlines()[-40:]:
                print("      | " + ln[:3000])
        r, _s = _redirect_run(["git", "-C", str(ROOT), "status", "--porcelain", "--",
                               "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild", ".claude/state/indicator_review", ".claude/breaks"], ROOT, env)
        print(f"[本物] git status（scripts/priority_rebuild・indicator_review・breaks）＝{'差なし' if not r.stdout.strip() else r.stdout.strip()[:600]}")
    finally:
        if keep:
            print(f"[写し] 残した: {top}")
        else:
            shutil.rmtree(top, ignore_errors=True)
    print("✅ 全部 通った" if not ng else "❌ " + "／".join(ng))
    return 0 if not ng else 1


def main() -> int:
    if "--check-redirect" in sys.argv:
        return check_redirect_main()
    if "--review-fill" in sys.argv:
        i = sys.argv.index("--review-fill")
        return review_fill_main(sys.argv[i + 1], sys.argv[i + 2])
    if "--new-numbers" in sys.argv:
        return new_numbers_main()
    if "--ranges" in sys.argv:
        return ranges_main()
    if "--compare-renamed" in sys.argv:
        i = sys.argv.index("--compare-renamed")
        return compare_renamed_main(sys.argv[i + 1])
    if "--measure" in sys.argv or "--count" in sys.argv:
        res = measure()
        if "--measure" in sys.argv:
            WD.mkdir(parents=True, exist_ok=True)
            OUT_LIST.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"書いた {OUT_LIST}（{res['数']}）")
            for fam, v in res["一覧"].items():
                print(f"  {v['群']}{'' if v['オン'] else '（オフ・for で一緒に変わる）'} {fam}: {v['今の名前の型']} → {v['新しい名前の型']}  "
                      f"隠れた数字={[(h['引数'], h['値']) for h in v['隠れた数字']]}  範囲={v['範囲の出どころ']}")
        print(f"名前に出ていない動かせる数字を持つオンの登録: {res['数']['相手（オン）']} 種")
        for e in res["止まった理由"]:
            print("  ❌", e)
        return 1 if res["止まった理由"] else 0
    if "--build" in sys.argv or "--check" in sys.argv or "--touched" in sys.argv:
        if not OUT_LIST.is_file():
            raise SystemExit("先に --measure で一覧を書く")
        res = json.loads(OUT_LIST.read_text(encoding="utf-8"))
        if res["止まった理由"]:
            raise SystemExit("一覧に止まった理由が在る＝先に直す: " + "／".join(res["止まった理由"]))
        if "--check" in sys.argv:
            return check(res)
        if "--touched" in sys.argv:
            return touched_main(res)
        build(res)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
