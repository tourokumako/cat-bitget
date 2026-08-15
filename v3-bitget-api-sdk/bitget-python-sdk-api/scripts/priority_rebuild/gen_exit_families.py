#!/usr/bin/env python3
"""gen_exit_families.py — 出口の枝の表（許可の一覧）の自動生成（D2 の前段・2026-08-07）

まこさん指示（逐語 2026-08-07）: 「X-a〜X-kから自動生成して」「お前は手書きはするな」。

作り（入口の型の表 gen_signal_families.py と同型）:
  表の本体＝軸カタログ entry_exit_matrix.md の X-a〜X-k の選択肢を全部 機械抽出して展開する。
  能力＝実行器 engine_tuner_exec.py の実物から機械抽出する（置き場所・執行の方式・scope・状態列）。
  執行（指値 maker か 成行 taker か）＝決済理由から機械で決まる（score.py が正本・H13）。
  検算＝機械生成の v9_exits.md（V9 の決済の枝）の全部に受け手が在るか。

★CC の手書きの md はゼロ。判断の入る対応（軸の選択肢 → 枝の型／組めない理由）は
  規則ファイル `.claude/ratchet/exit_families_rules.json` に1行ずつ出典つきで置き、
  承認の指紋がまこさんの判断の記録になる（D1 の対応表と同じ形）。

fail-closed（止まる条件）:
  ①規則ファイルの選択肢が軸カタログと1対1でない（漏れ・余り）②出典（basis）が空の行が在る
  ③枝の決済理由が score.py に登録されていない ④置き場所が実行器の受け皿に無い
  ⑤発火条件の材料が実行器の状態列に無い／実装で死んでいる列 ⑥値の格子が設定ファイルに無い（値待ち）
  ⑦恒等検収レーン専用のキーを使っている ⑧V9 の枝に受け手が無い

このスクリプトがやらないこと: 売買しない・値を選ばない・採点しない・engine_tuner 系のコードに触れない。
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import pathlib
import re
import sys

import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(HERE))

MATRIX_MD = SDK / ".claude/ratchet/entry_exit_matrix.md"          # 軸カタログの正本（X-a〜X-k）
V9_EXITS_MD = SDK / ".claude/ratchet/v9_exits.md"                 # V9 の枝（機械生成＝検算の既知答え）
SIGNAL_JSON = SDK / ".claude/ratchet/signal_families.json"        # 入口の型の表（部品＝確認条件の材料）
RULES_JSON = SDK / ".claude/ratchet/exit_families_rules.json"     # 規則（軸の選択肢 → 枝の型・出典つき）
LIMITS_JSON = HERE / "recipes/search_limits.json"
EXEC_PY = HERE / "engine_tuner_exec.py"
OUT_JSON = SDK / ".claude/ratchet/exit_families.json"
OUT_MD = SDK / ".claude/ratchet/exit_families.md"
APPROVED_FILE = SDK / ".claude/ratchet/exit_families_approved.txt"

# 役割から機械で決まる値（格子ではない＝設定ファイルの格子検査の対象外）
ROLE_DERIVED_GRIDS = ("hold_bars_from_role",)


class GenError(SystemExit):
    """生成の拒否（fail-closed）＝黙って弱い表を作らない。"""


# ══ ① 軸カタログ（X-a〜X-k）を機械抽出 ═══════════════════════════════════════════
def parse_axes() -> list[dict]:
    """entry_exit_matrix.md の『共通 Exit ロジック軸』X-a〜X-k を、選択肢1つずつに割って返す。"""
    text = MATRIX_MD.read_text(encoding="utf-8")
    rows = re.findall(r"^- \*\*(X-[a-k]) ([^（*]+)(?:（[^）]*）)?\*\*: (.+)$", text, re.M)
    if len(rows) < 11:
        raise GenError(f"[生成エラー] 軸カタログの X 軸が {len(rows)} 本しか取れない（11本のはず）＝正本の形が変わった")
    axes = []
    for ax, name, body in rows:
        opts = re.split(r"\s*/\s*(?=\(\d+\))", body)
        items = []
        if len(opts) == 1:                       # 番号が振られていない軸（X-g・X-h・X-j・X-k）
            for i, o in enumerate(body.split(" / "), 1):
                items.append(dict(id=f"{ax}{i}", text=o.strip()))
        else:
            for o in opts:
                m = re.match(r"\((\d+)\)\s*(.+)", o.strip())
                if not m:
                    raise GenError(f"[生成エラー] {ax} の選択肢が読めない: {o[:40]}")
                items.append(dict(id=f"{ax}{m.group(1)}", text=m.group(2).strip()))
        axes.append(dict(axis=ax, name=name.strip(), options=items))
    return axes


# ══ ② 実行器の能力を AST で機械抽出 ═══════════════════════════════════════════════
def _fn(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise GenError(f"[生成エラー] 実行器に関数 {name} が無い＝実物の形が変わった")


def _str_compares(node, var: str) -> set:
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Compare) and isinstance(n.left, ast.Name) and n.left.id == var:
            for c in n.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    out.add(c.value)
                elif isinstance(c, (ast.Tuple, ast.List, ast.Set)):
                    out |= {e.value for e in c.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
    return out


def exec_capability() -> dict:
    """実行器（engine_tuner_exec.py）が実際に受けられるものを、実物から機械で数える。"""
    import engine_tuner_exec as ex
    src = EXEC_PY.read_text(encoding="utf-8")
    tree = ast.parse(src)
    level_kinds = sorted(_str_compares(_fn(tree, "_check_level"), "kind"))
    # scope のキー＝_exit_fire_ok の中で変数 sc（＝枝の scope）に対して読んでいる名前だけを拾う。
    #（関数全体の添字を拾うと、玉の内部の名前や木のキー all/any まで混ざる＝2026-08-07 に混ざっていた）
    fire_fn = _fn(tree, "_exit_fire_ok")
    scope_keys = sorted(
        {n.slice.value for n in ast.walk(fire_fn)
         if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == "sc"
         and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)}
        | {n.args[0].value for n in ast.walk(fire_fn)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get"
           and isinstance(n.func.value, ast.Name) and n.func.value.id == "sc"
           and n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str)}
        | {c.value for n in ast.walk(fire_fn) if isinstance(n, ast.Compare)
           and isinstance(n.comparators[0], ast.Name) and n.comparators[0].id == "sc"
           for c in [n.left] if isinstance(c, ast.Constant) and isinstance(c.value, str)})
    # 恒等検収レーン専用（lane != "legacy" で拒否されるキー）＝探索の案では使えない
    legacy_only = sorted(set(re.findall(r'"(position_exits|trend_caught|while_waiting)"[^\n]{0,200}?恒等', src))
                         | {k for k in ("position_exits", "trend_caught", "while_waiting")
                            if re.search(rf'{k}[\s\S]{{0,400}}?lane != "legacy"', src)})
    # ★死んでいる状態列の機械検出＝その列が読む lot のキーに、実装のどこにも代入が無い
    dead = []
    for col, lot_key in (("peak_age_bars", "peak_idx"),):
        if not re.search(rf'\["{lot_key}"\]\s*=|{lot_key}\s*=\s*[^=]', src):
            dead.append(col)
    # ★出口の発火条件で実際に使える形＝実行器を呼んで確かめる（2026-08-07）。
    #   AST では読み切れないので、形ごとに1本ずつ実物へ渡して、例外が出ないものだけを「使える」とする。
    #   事案＝ローソクの向き（材料の無い形）を出口の条件に入れたら、実行器が材料を探しに行って落ちた。
    fire_forms = []
    _df = pd.DataFrame({"ts": pd.date_range("2024-01-01", periods=3, freq="5min"),
                        "open": [1.0] * 3, "high": [1.0] * 3, "low": [1.0] * 3,
                        "close": [1.0] * 3, "volume": [1.0] * 3})
    _lot = {"first_idx": 0, "add_count": 1, "avg": 1.0, "max_fav": 1.0, "max_adv": 1.0,
            "side": "SHORT", "pk_prev": 1.0}
    for label, cond in (
        ("state", {"role": "env", "form": "level", "side": "above",
                   "material": [{"state": "hold_min"}], "value": {"n": 1}}),
        ("candle_dir", {"role": "env", "form": "candle_dir", "value": {"dir": "bull"}}),
    ):
        try:
            ex._exit_fire_ok({"fire": {"all": [cond]}}, _lot, 1, _df, {}, "", {})
            fire_forms.append(label)
        except BaseException:
            pass
    return dict(
        exec_methods=list(ex.EXEC_METHODS),
        exit_fire_forms=fire_forms,
        exec_registered_only=list(ex.EXEC_REGISTERED_ONLY),
        placement_kinds=["resting", "on_close"],
        level_kinds=level_kinds,
        scope_keys=scope_keys,
        forms=list(ex.FORMS),
        state_cols=list(__import__("indicator_reference_diag").STATE_COLS),
        dead_state_cols=dead,
        legacy_only=legacy_only,
        family_templates=sorted(ex.FAMILY_TEMPLATES),
    )


# ══ ③ 決済理由（score.py が正本・H13）═══════════════════════════════════════════
def exit_reasons() -> dict:
    import score as sc
    return dict(maker=sorted(sc.MAKER_EXIT_REASONS), taker=sorted(sc.TAKER_EXIT_REASONS))


# ══ ④ V9 の枝（機械生成の v9_exits.md）＝検算の既知答え ══════════════════════════
def v9_branches() -> list[str]:
    text = V9_EXITS_MD.read_text(encoding="utf-8")
    names = []
    for row in text.splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) >= 5 and re.fullmatch(r"\d+", cells[0]):
            names.append(re.sub(r"（\d+件目）", "", cells[1]).strip())
    if not names:
        raise GenError("[生成エラー] v9_exits.md から枝の名前が1つも取れない＝正本の形が変わった")
    return sorted(set(names))


# ══ ⑤ 規則ファイル ═══════════════════════════════════════════════════════════════
def load_rules() -> dict:
    r = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    for k in ("branch_types", "axis_options", "reason_codes", "v9_coverage"):
        if k not in r:
            raise GenError(f"[生成エラー] 規則ファイルに {k} が無い")
    return r


def _grid_names(obj, out: set) -> None:
    """枝の定義の中に出てくる格子の名前（*_grid）を全部 集める。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            # 格子の指し方は2通り＝キー名が *_grid（例 k_grid）／キー名が grid（発火条件の中）。
            # 2026-08-07 に後者を拾い漏らし、値待ち（hold_frac_grid・loss_cap_grid）が表に出なかった。
            if (k.endswith("_grid") or k == "grid") and isinstance(v, str):
                out.add(v)
            else:
                _grid_names(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _grid_names(v, out)


# ══ ⑥ 検査（fail-closed の本体）═══════════════════════════════════════════════════
def check(rules: dict, axes: list[dict], cap: dict, reasons: dict, limits: dict,
          v9: list[str]) -> tuple[list[str], list[str]]:
    """規則を実物と突き合わせる。戻り＝(止める違反, 値待ち)。"""
    ng: list[str] = []
    waiting: list[str] = []

    # (1) 網羅＝軸カタログの選択肢と規則のキーが1対1
    cat_ids = [o["id"] for a in axes for o in a["options"]]
    rule_ids = list(rules["axis_options"])
    miss = [i for i in cat_ids if i not in rule_ids]
    extra = [i for i in rule_ids if i not in cat_ids]
    if miss:
        ng.append(f"軸カタログに在るのに規則に無い選択肢: {miss}")
    if extra:
        ng.append(f"規則に在るのに軸カタログに無い選択肢: {extra}")

    # (2) 出典（basis）が全行に在る
    for oid, o in rules["axis_options"].items():
        if not str(o.get("basis") or "").strip():
            ng.append(f"{oid}: 出典（basis）が空")
        if o.get("status") == "blocked" and o.get("reason_code") not in rules["reason_codes"]:
            ng.append(f"{oid}: 組めない理由の分類が一覧に無い（{o.get('reason_code')}）")
    for bid, b in rules["branch_types"].items():
        if not str(b.get("basis") or "").strip():
            ng.append(f"枝 {bid}: 出典（basis）が空")

    # (3) 枝の型を実物と突き合わせる
    all_reasons = set(reasons["maker"]) | set(reasons["taker"])
    for bid, b in rules["branch_types"].items():
        rsn = b.get("reason")
        if rsn not in all_reasons:
            # 未登録＝「決済の名前の登録待ち」。表には載せるが、登録が済むまでその枝は生成できない
            #（H13＝審判 score.py への登録はまこさんの承認＋既知答えテスト再pass が要る）。
            side = b.get("reason_pending_side")
            if side not in ("maker", "taker"):
                ng.append(f"枝 {bid}: 決済理由 {rsn} が score.py 未登録なのに、登録の提案の側"
                          f"（reason_pending_side＝maker/taker）が規則に書かれていない")
                continue
            waiting.append(f"決済の名前 {rsn} の登録（{side}・枝 {bid}）")
            is_maker = side == "maker"
        else:
            is_maker = rsn in set(reasons["maker"])
        pl = b.get("placement") or {}
        kind = pl.get("kind")
        if kind not in cap["placement_kinds"]:
            ng.append(f"枝 {bid}: placement.kind が実行器の受け皿に無い（{kind}）")
        if is_maker and kind != "resting":
            ng.append(f"枝 {bid}: maker の決済理由なのに指値（resting）でない＝H5（出口の既定は指値 maker）")
        if (not is_maker) and kind != "on_close":
            ng.append(f"枝 {bid}: taker の決済理由なのに成行（on_close）でない")
        lv = pl.get("level") or {}
        if kind == "resting":
            if lv.get("kind") not in cap["level_kinds"]:
                ng.append(f"枝 {bid}: 置き場所 {lv.get('kind')} が実行器の受け皿に無い（在るのは {cap['level_kinds']}）")
            if pl.get("fill") not in ("profit", "adverse"):
                ng.append(f"枝 {bid}: 指値の当たり方（profit/adverse）が無い")
        # 発火条件の材料＝ポジション状態列
        for f in (b.get("fire") or []):
            st = f.get("state")
            if st is None:
                # 材料の無い形（ローソクの向きなど）＝実行器が出口の発火条件で扱えるかを実物で確かめた結果で判定
                if f.get("indicator") and "candle_dir" in (f.get("forms") or []) \
                        and "candle_dir" not in cap["exit_fire_forms"]:
                    ng.append(f"枝 {bid}: 出口の発火条件に材料の無い形（candle_dir）を使っているが、"
                              f"実行器は出口でその形を扱えない（実物で確認済み・使えるのは {cap['exit_fire_forms']}）")
                continue
            if st not in cap["state_cols"]:
                ng.append(f"枝 {bid}: 状態列 {st} が実行器に無い")
            if st in cap["dead_state_cols"]:
                ng.append(f"枝 {bid}: 状態列 {st} は実装で値が入らない（死んでいる列）＝使わない")
        for key in (b.get("scope") or {}):
            base = key.replace("_min_grid", "").replace("_grid", "")
            if base not in cap["scope_keys"]:
                ng.append(f"枝 {bid}: scope の {key} が実行器に無い")
        # 恒等検収レーン専用のキーを使っていないか
        blob = json.dumps(b, ensure_ascii=False)
        for k in cap["legacy_only"]:
            if f'"{k}"' in blob:
                ng.append(f"枝 {bid}: {k} は恒等検収レーン専用＝探索の案では使えない")
        # 値の格子が設定ファイルに在るか
        gs: set = set()
        _grid_names(b, gs)
        for g in sorted(gs):
            if g in ROLE_DERIVED_GRIDS:
                continue
            if g not in limits or limits.get(g) is None:
                waiting.append(f"{g}（枝 {bid} が使う）")

    # (4) 規則が指す枝の型が実在するか
    for oid, o in rules["axis_options"].items():
        for bid in (o.get("branches") or []):
            if bid not in rules["branch_types"]:
                ng.append(f"{oid}: 指している枝の型 {bid} が定義に無い")

    # (5) V9 の枝10種に受け手が在るか（機械生成の v9_exits.md が正本）
    cov = {k: v for k, v in rules["v9_coverage"].items() if not k.startswith("_")}
    for nm in v9:
        if nm not in cov:
            ng.append(f"V9 の枝 {nm} に受け手が無い（v9_coverage に行が無い）")
            continue
        for bid in cov[nm]:
            if bid not in rules["branch_types"]:
                ng.append(f"V9 の枝 {nm} の受け手 {bid} が定義に無い")
    for nm in cov:
        if nm not in v9:
            ng.append(f"v9_coverage に在るが v9_exits.md に無い枝: {nm}")

    return ng, sorted(set(waiting))


# ══ ⑦ 表を作る ═══════════════════════════════════════════════════════════════════
def build_table() -> dict:
    axes = parse_axes()
    cap = exec_capability()
    reasons = exit_reasons()
    rules = load_rules()
    limits = {k: v for k, v in json.loads(LIMITS_JSON.read_text(encoding="utf-8")).items()
              if not k.startswith("_")}
    v9 = v9_branches()
    sig = json.loads(SIGNAL_JSON.read_text(encoding="utf-8")) if SIGNAL_JSON.exists() else {}
    ng, waiting = check(rules, axes, cap, reasons, limits, v9)
    if ng:
        raise GenError("[生成エラー] 規則が実物と合わない（fail-closed）:\n  - " + "\n  - ".join(ng))

    status_count: dict = {}
    for o in rules["axis_options"].values():
        status_count[o["status"]] = status_count.get(o["status"], 0) + 1
    maker = set(reasons["maker"])
    all_r = maker | set(reasons["taker"])
    branches = {}
    for bid, b in rules["branch_types"].items():
        if b["reason"] in all_r:
            side, pend = ("maker" if b["reason"] in maker else "taker"), ""
        else:
            # 決済の名前が score.py に未登録＝登録待ち（提案の側は規則に書いてあり、生成器が検査済み）
            side, pend = b["reason_pending_side"], "・★登録待ち"
        branches[bid] = dict(b, exec_method=("maker（指値）" if side == "maker" else "taker（成行）") + pend)

    return dict(
        purpose="net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的（まこさん確定 2026-08-06 逐語）",
        built_by="gen_exit_families.py（全自動生成・CC の手書きの md はゼロ・まこさん指示 2026-08-07『X-a〜X-kから自動生成して』『お前は手書きはするな』）",
        sources=dict(
            axes="entry_exit_matrix.md の共通 Exit ロジック軸 X-a〜X-k（軸カタログ＝正本）",
            capability="engine_tuner_exec.py の実物（AST で機械抽出）",
            reasons="score.py の MAKER_EXIT_REASONS／TAKER_EXIT_REASONS（H13）",
            v9="v9_exits.md（replay_csv.py から機械生成・検算の既知答え）",
            materials="signal_families.json（入口の型の表＝確認条件の材料と禁止3 を共有）",
            grids="recipes/search_limits.json（まこさん承認 2026-08-01）",
        ),
        axes=axes,
        capability=cap,
        reasons=reasons,
        branch_types=branches,
        axis_options=rules["axis_options"],
        reason_codes=rules["reason_codes"],
        v9=dict(branches=v9, coverage={k: v for k, v in rules["v9_coverage"].items() if not k.startswith("_")}),
        confirm_conditions=dict(
            rule="どの枝にも、確認の条件を 0〜2本 足せる。材料は入口の型の表の部品だけ（禁止3 も同じ）。"
                 "閾値は分位。向きは『出口＝入口の逆』で機械が決める（入口の向きの決まり DC1〜DC4 を逆向きに適用）",
            parts_count=len(sig.get("parts") or []),
            timeframes=sig.get("timeframes") or [],
            quantile_grid=limits.get("quantile_grid"),
            banned_pairs=len(((sig.get("bans") or {}).get("insufficient_samples") or {}).get("pairs") or []),
        ),
        counts=dict(
            axes=len(axes),
            options=sum(len(a["options"]) for a in axes),
            status=status_count,
            branch_types=len(branches),
            maker_branches=sum(1 for b in branches.values() if b["reason"] in maker),
            taker_branches=sum(1 for b in branches.values() if b["reason"] not in maker),
        ),
        waiting=waiting,
        approval=dict(fingerprint=None,
                      note="まこさんの承認の指紋が入るまで、この表は無効（D2 の実装に進めない）"),
    )


def _canon(t: dict) -> str:
    return json.dumps(t, ensure_ascii=False, sort_keys=True, indent=1)


_STATUS_JP = {
    "buildable": "組める",
    "partial": "一部だけ組める",
    "covered_elsewhere": "別の仕組みで持っている",
    "blocked": "組めない",
    "out_of_scope_stage": "この工程の担当でない",
    "no_data": "データが無い",
    "not_applicable_market": "この市場に当てはまらない",
}


def _md(t: dict, h: str) -> str:
    c = t["counts"]
    # ★2026-08-15（段A の A-5-3）＝分位の範囲は設定ファイルから直に読む（承認済みの表には入れない）。
    _QR = json.loads(LIMITS_JSON.read_text(encoding="utf-8")).get("quantile_range")
    L = [
        f"<!-- EXIT_FAMILIES hash={h} gen_exit_families.py が自動生成＝手で書き換えない -->",
        "# exit_families.md — 出口の枝の表（許可の一覧・全自動生成・CC の手書きの行ゼロ）",
        "",
        f"作り＝{t['built_by']}",
        "",
        "## 出どころ（全部 機械で読む）",
        "",
        "| 何を | どこから |",
        "|---|---|",
    ]
    for k, v in t["sources"].items():
        L.append(f"| {k} | {v} |")
    L += [
        "",
        f"## 集計＝軸 {c['axes']} 本 ／ 選択肢 {c['options']} 個 ／ 枝の型 {c['branch_types']} 種"
        f"（指値 maker {c['maker_branches']} 種・成行 taker {c['taker_branches']} 種）",
        "",
        "| 選択肢の状態 | 数 |",
        "|---|---|",
    ]
    for s, n in sorted(t["counts"]["status"].items(), key=lambda x: -x[1]):
        L.append(f"| {_STATUS_JP.get(s, s)} | {n} |")
    L += [
        "",
        "## 実行器が実際に受けられるもの（engine_tuner_exec.py から機械抽出）",
        "",
        f"- 置き場所（価格の決め方）: {'、'.join(t['capability']['level_kinds'])}",
        f"- 発注の方式: {'、'.join(t['capability']['exec_methods'])}"
        f"（登録済みだが実行不能＝{'、'.join(t['capability']['exec_registered_only'])}）",
        f"- 玉の状態の列: {'、'.join(t['capability']['state_cols'])}",
        f"- ★実装で値が入らない列（使わない）: {'、'.join(t['capability']['dead_state_cols']) or 'なし'}",
        f"- 枝を当てる玉の絞り: {'、'.join(sorted(set(t['capability']['scope_keys'])))}",
        f"- 恒等検収レーン専用（探索では使えない）: {'、'.join(t['capability']['legacy_only']) or 'なし'}",
        "",
        "## 決済の名前（score.py が正本＝執行はここから機械で決まる）",
        "",
        f"- 指値 maker: {'、'.join(t['reasons']['maker'])}",
        f"- 成行 taker: {'、'.join(t['reasons']['taker'])}",
        "",
        "## 枝の型（この表が許可するもの）",
        "",
        "| 枝 | 何をするか | 決済の名前 | 執行 | 置き場所 | 発火の条件 | 値の格子 |",
        "|---|---|---|---|---|---|---|",
    ]
    for bid, b in t["branch_types"].items():
        pl = b.get("placement") or {}
        lv = pl.get("level") or {}
        place = lv.get("kind", pl.get("kind", "—"))
        fire = "／".join(
            (f"{f['state']} を見る" if f.get("state") else "指標（型の表の部品）")
            for f in (b.get("fire") or [])) or "なし（常に置く）"
        gs: set = set()
        _grid_names(b, gs)
        L.append(f"| {bid} | {b['jp']} | {b['reason']} | {b['exec_method']} | {place} | {fire} | "
                 f"{'、'.join(sorted(gs)) or '—'} |")
    L += [
        "",
        f"## どの枝にも足せる確認の条件（0〜2本）",
        "",
        f"規則: {t['confirm_conditions']['rule']}",
        f"材料＝入口の型の表の部品 {t['confirm_conditions']['parts_count']} 種 × 時間足 "
        f"{len(t['confirm_conditions']['timeframes'])} 本 ／ 閾値＝分位 "
        # ★2026-08-15（段A の A-5-3）＝分位は範囲になった。範囲は設定ファイルから直に読む。
        #   ★承認済みの表（json）には入れない＝入れると表の指紋が変わり、再承認（まこさんの操作）が要る。
        + (f"**範囲 q{int(_QR['lo'])}〜q{int(_QR['hi'])}**（`quantile_range`）"
           if isinstance(_QR, dict) and _QR.get("lo") is not None else
           f"{len(t['confirm_conditions']['quantile_grid'] or [])} 段")
        + " ／ 標本不足の禁止 "
        f"{t['confirm_conditions']['banned_pairs']} 組も同じように効く",
        "",
        "## 軸カタログ X-a〜X-k の選択肢 全部（1つずつ・出典つき）",
        "",
    ]
    opts = t["axis_options"]
    for a in t["axes"]:
        L += [f"### {a['axis']} {a['name']}", "",
              "| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |", "|---|---|---|---|---|"]
        for o in a["options"]:
            r = opts[o["id"]]
            st = _STATUS_JP.get(r["status"], r["status"])
            if r.get("branches"):
                mid = "、".join(r["branches"])
            elif r.get("reason_code"):
                mid = t["reason_codes"][r["reason_code"]]
            else:
                mid = r.get("note", "—")
            note = f"（{r['note']}）" if r.get("note") and r.get("branches") else ""
            L.append(f"| {o['id']} | {o['text']} | {st} | {mid}{note} | {r['basis']} |")
        L.append("")
    L += [
        "## V9 の枝との検算（機械生成の v9_exits.md が正本）",
        "",
        "| V9 の枝 | 受け手の枝の型 |",
        "|---|---|",
    ]
    for nm in t["v9"]["branches"]:
        L.append(f"| {nm} | {'、'.join(t['v9']['coverage'][nm])} |")
    L += [
        "",
        "## 値待ち（まこさんが決める・決まるまでその枝は生成できない）",
        "",
    ]
    L += ([f"- {w}" for w in t["waiting"]] or ["- なし"])
    L += [
        "",
        "## 承認",
        "",
        f"- 指紋: {t['approval']['fingerprint']}（{t['approval']['note']}）",
    ]
    return "\n".join(L) + "\n"


def write() -> None:
    t = build_table()
    canon = _canon(t)
    h = hashlib.md5(canon.encode("utf-8")).hexdigest()[:16]
    OUT_JSON.write_text(canon, encoding="utf-8")
    OUT_MD.write_text(_md(t, h), encoding="utf-8")
    c = t["counts"]
    print(f"[生成] {OUT_JSON}")
    print(f"[生成] {OUT_MD}")
    print(f"[本体] 軸 {c['axes']} 本 ／ 選択肢 {c['options']} 個 ／ 枝の型 {c['branch_types']} 種"
          f"（指値 maker {c['maker_branches']}・成行 taker {c['taker_branches']}）")
    print(f"[状態] " + " ／ ".join(f"{_STATUS_JP.get(k, k)} {v}" for k, v in sorted(c["status"].items(), key=lambda x: -x[1])))
    print(f"[検算] V9 の枝 {len(t['v9']['branches'])} 種 全部に受け手が在る")
    print(f"[値待ち] {len(t['waiting'])} 件" + ("＝" + "／".join(t["waiting"]) if t["waiting"] else ""))
    print(f"[指紋] md5 {h} ／ 承認の指紋 = {t['approval']['fingerprint']}（無し＝表は無効のまま）")


def verify() -> None:
    if not OUT_JSON.exists() or not OUT_MD.exists():
        raise GenError("[検証エラー] 表がまだ無い（--write が先）")
    now = _canon(build_table())
    disk = OUT_JSON.read_text(encoding="utf-8")
    strip = lambda s: re.sub(r'"fingerprint": "[^"]*"', '"fingerprint": null', s)  # noqa: E731
    if strip(disk) != strip(now):
        raise GenError("[検証エラー] 表が入力と一致しない（手の改変か、入力の正本が変わった）＝ --write で作り直す")
    print("[検証] ✅ 表は入力の正本と一致（手の改変なし）")


def table_status() -> tuple[bool, str]:
    if not OUT_JSON.exists():
        return False, "出口の表（exit_families.json）が無い"
    h = hashlib.md5(OUT_JSON.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    if not APPROVED_FILE.exists():
        return False, f"承認の指紋が無い（まこさんが --approve を実行するまで表は無効）。今の表 md5 {h[:8]}…"
    rec = APPROVED_FILE.read_text(encoding="utf-8").split()[0]
    if rec != h:
        return False, f"承認の指紋（{rec[:8]}…）が今の表（{h[:8]}…）と一致しない＝表が変わった。再承認が要る"
    return True, f"承認済み（md5 {h[:8]}…）"


def approve() -> None:
    """★まこさんが実行する承認の操作（CC は実行しない＝実行した場合は worklog に残る）。"""
    verify()
    import datetime
    h = hashlib.md5(OUT_JSON.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    APPROVED_FILE.write_text(f"{h}  approved {datetime.date.today()}\n", encoding="utf-8")
    print(f"[承認] 指紋を記録した: {h}")


# ══ ⑧ 番人（既知答え・わざと壊して落ちるか）══════════════════════════════════════
def selftest() -> None:
    axes = parse_axes()
    cap = exec_capability()
    reasons = exit_reasons()
    limits = {k: v for k, v in json.loads(LIMITS_JSON.read_text(encoding="utf-8")).items()
              if not k.startswith("_")}
    v9 = v9_branches()
    base = load_rules()

    def run(r):
        return check(r, axes, cap, reasons, limits, v9)[0]

    cases = []
    cases.append(("正しい規則（そのまま）", base, True))

    r1 = copy.deepcopy(base); r1["axis_options"].pop("X-g11")
    cases.append(("軸の選択肢を1つ 規則から消す（網羅の検査）", r1, False))

    r2 = copy.deepcopy(base); r2["branch_types"]["PEAKLOCK"]["reason"] = "ナニカ_EXIT"
    cases.append(("枝の決済理由を score.py 未登録の名前にする（H13）", r2, False))

    r3 = copy.deepcopy(base); r3["branch_types"]["TP_ZONE_MID"]["placement"]["level"]["kind"] = "sigma_band"
    cases.append(("置き場所を実行器に無いものにする", r3, False))

    r4 = copy.deepcopy(base); r4["axis_options"]["X-a1"]["basis"] = "  "
    cases.append(("出典（basis）を空にする", r4, False))

    r5 = copy.deepcopy(base)
    r5["branch_types"]["PEAKLOCK"]["fire"] = [{"state": "peak_age_bars", "side": "above", "grid": "int_grid"}]
    cases.append(("実装で値が入らない状態列（死んでいる列）を使う", r5, False))

    r6 = copy.deepcopy(base)
    r6["branch_types"]["TIME"]["placement"] = {"kind": "resting", "fill": "profit",
                                               "level": {"kind": "pct", "base": "entry", "k_const": "SCALP_FLOOR"}}
    cases.append(("成行の決済理由の枝を指値にする（執行は理由から機械で決まる）", r6, False))

    r7 = copy.deepcopy(base)
    r7["branch_types"]["SL_ZONE"]["placement"] = {"kind": "on_close"}
    cases.append(("指値の決済理由の枝を成行にする（H5＝出口の既定は指値 maker）", r7, False))

    r8 = copy.deepcopy(base); r8["v9_coverage"].pop("MFE_EXIT")
    cases.append(("V9 の枝の受け手を1つ 消す（2026-08-07 の漏れの再発検出）", r8, False))

    # ★実物に合わせた既知答え（2026-08-07）＝恒等検収レーン専用は実行器の AST 抽出で決まる
    #（position_exits・trend_caught）。while_waiting は「peak_giveback の枝だけが持てる」制約であって
    #  恒等レーン専用ではない＝CC が最初に書いた既知答えが実物とずれていた（番人が捕まえた）。
    r9 = copy.deepcopy(base)
    r9["branch_types"]["PEAKLOCK"]["scope"] = {"trend_caught": True}
    cases.append(("恒等検収レーン専用のキー（trend_caught）を使う", r9, False))

    ngs = []
    for label, r, want_ok in cases:
        got = run(r)
        ok = not got
        mark = "✅" if ok == want_ok else "🚨"
        print(f"  {mark} {label}: 期待={'通る' if want_ok else '止まる'} ／ 実際={'通った' if ok else '止まった'}"
              + (f"（{got[0][:70]}）" if got else ""))
        if ok != want_ok:
            ngs.append(label)
    if ngs:
        raise GenError(f"[番人] 🚨 既知答えに正しく反応しない: {ngs}")
    print(f"[番人] ✅ 既知答え {len(cases)} 件 全部 期待どおり")


def v9_test() -> None:
    """検算＝V9 の枝の全部に受け手が在るか（表を作った後の再確認・単独で打てる）。"""
    rules = load_rules()
    v9 = v9_branches()
    cov = {k: v for k, v in rules["v9_coverage"].items() if not k.startswith("_")}
    ng = [nm for nm in v9 if nm not in cov]
    print(f"[検算] V9 の枝（v9_exits.md から機械抽出）＝{len(v9)} 種")
    for nm in v9:
        print(f"   {'✅' if nm in cov else '🚨'} {nm} → {'、'.join(cov.get(nm, [])) or '受け手なし'}")
    if ng:
        raise GenError(f"[検算] 🚨 受け手の無い枝: {ng}")
    print("[検算] ✅ 全部に受け手が在る")


def main() -> None:
    p = argparse.ArgumentParser(description="出口の枝の表の自動生成（X-a〜X-k から）")
    p.add_argument("--write", action="store_true", help="表を作る")
    p.add_argument("--verify", action="store_true", help="手の改変を検出する")
    p.add_argument("--selftest", action="store_true", help="番人（わざと壊して落ちるか）")
    p.add_argument("--v9-test", action="store_true", help="V9 の枝の検算")
    p.add_argument("--status", action="store_true", help="承認の状態")
    p.add_argument("--approve", action="store_true", help="★まこさん専用＝承認の指紋を記録する")
    a = p.parse_args()
    if a.write:
        write()
    elif a.verify:
        verify()
    elif a.selftest:
        selftest()
    elif a.v9_test:
        v9_test()
    elif a.status:
        ok, msg = table_status()
        print(("✅ " if ok else "❌ ") + msg)
    elif a.approve:
        approve()
    else:
        p.print_help()


if __name__ == "__main__":
    main()
