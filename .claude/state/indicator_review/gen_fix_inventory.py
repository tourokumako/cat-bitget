#!/usr/bin/env python3
"""gen_fix_inventory.py — 直す相手（範囲のファイルの中の、指標の情報を持つ所・読む所・自分で計算する所）を、実物からファイル:行で全部出し、①②③に振り分けた表を作る（読むだけ）。

まこさん（2026-10-24）「全部正確にまとめろ」「手書きするな」・ゴール（req_goal_20261023.txt）。
範囲のファイル＝reach_from_engine_tuner.py --strict --import-only でたどれたプログラムと json、その json と INDICATOR_TABLE を書くプログラム
  （gen_indicator_switch.py・gen_indicator_table.py）、gen_indicator_table.py が読む資料の表（indicator_roles_thresholds.json・r1_role_map.json）、
  と資料の表の残り（indicator_params_by_strategy.json・indicator_params_review.json）。
名前の一覧＝INDICATOR_TABLE の種類・MATERIAL_FAMILIES の鍵・signal_families.json の parts（列 652）・RUNTIME_ALIAS の値・atr_14（engine_tuner_gen.py:4062）。
.py で拾う物（構文木）
  持つ＝代入の右辺が辞書・一覧・組・集合で、名前の一覧の文字を1つ以上持つ物／_r(...)・_reg(...) の呼び出し
  直書き＝それ以外の所に在る、名前の一覧の文字
  読む＝持つ物の名前（下の HOLDERS と、範囲の中で見つけた持つ物の名前）を使う所／範囲の json の名前を書いた文字
  自前で計算＝.rolling( .ewm( .pct_change( の呼び出し（observe_diag.py・indicator_reference_diag.py の計算の関数の本体は除く＝V37）
振り分け（このやり取りで決めた事・okd_plan5）
  持つ → ①写す→②消す ／ 直書き・読む・自前で計算 → ③向け直す ／ json は JSON_RULE のとおり
照らし＝readers_20261024/merge.md の範囲の中の行（持つ・読む・自前で計算）が、出力の同じファイルの行の範囲に在るか。無い行を「拾えなかった行」として出す。
出す物＝fix_inventory_20261024.md・fix_inventory_20261024.json と画面
使い方: python3 .claude/state/indicator_review/gen_fix_inventory.py
"""
import ast
import contextlib
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(os.environ.get("IND_ROOT", "/Users/tachiharamasako/Documents/GitHub/cat-bitget"))   # ★2026-10-31（F-4）＝写しで確かめるときは IND_ROOT で写しの一番上を渡す（ss_outside_probe.py の SS_ROOT と同じ形）
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PR = SDK / "scripts/priority_rebuild"
HERE = Path(__file__).resolve().parent

reach = json.loads((HERE / "reach_from_engine_tuner.json").read_text(encoding="utf-8"))
# ★2026-10-24＝engine_tuner の入口のファイルも全部入れる（直す前は、エージェントの表に在るファイルだけに絞っていて、engine_tuner_gen.py が抜けていた）
ENTRY = {"engine_tuner.py", "engine_tuner_gen.py", "engine_tuner_exec.py", "tuner_judgement.py", "precheck.py", "score.py", "report.py", "analyze.py"}
SCOPE_PY = sorted({f for f in reach["inside"] if f.endswith(".py")} | ENTRY | {"gen_indicator_switch.py", "gen_indicator_table.py"}
                  # ★2026-10-24（210回目）＝地図（indicator_dir_map_20261022.md）の「読む所」に在るのに範囲に無かった、売買の側と tools・hooks の18本
                  #   （okd_plan5:V28「engine_tuner_gen・engine_tuner_exec・gen_*・観察の道具・hooks・tools は、全部この読む口から読みます」）。
                  #   過去の戦略の e37.py は外す（まこさん 2026-10-23「37とか直書きしてる過去の戦略ファイルはどうでもいい」）
                  | {"e38.py", "e38_logic_parts.py", "gen_audit_request.py", "gen_composition_rules.py", "gen_decisions.py", "gen_docmap.py",
                     "gen_materials.py", "gen_observe_manual.py", "leak_causality_diag.py", "tuner_backcalc.py",
                     "check_indicator_sources.py", "count_builder_literals.py", "gen_acceptance.py", "gen_audit_docs.py", "gen_s22_combi.py",
                     "gen_stage0_match.py", "pre_audit_check.py", "enforce_g2_pass.py"})
SCOPE_JSON = sorted({f for f in reach["inside"] if f.endswith(".json")}
                    | {"indicator_roles_thresholds.json", "r1_role_map.json", "indicator_params_by_strategy.json", "indicator_params_review.json"}
                    | {"composition_rules.json", "materials.json"}   # ★2026-10-24（210回目）＝地図の「ratchet の表の、指標1種ごとの欄」（okd_plan5:V36）の2本が抜けていた
                    # ★2026-10-24（210回目）＝地図（indicator_dir_map_20261022.md の「現状」の表）に在るのに、一覧に無かった7本
                    | {"identity_s1_legacy.json", "identity_s2_legacy.json", "r9_demand_fixture.json", "indicator_fix_plan.json",
                       "indicator_params_by_strategy.before_153.json", "indicator_source_map.json", "read_plan_src_m2c15-hidden-params-20261004.json"})
JSON_RULE = {
    "observe_config.json": "①写す→②消す（指標の部分）", "search_limits.json": "①写す→②消す（範囲）", "indicator_switch.json": "①写す→②消す（ファイルごと）",
    "signal_families.json": "②消す（指標1種ごとの欄）", "exit_families.json": "②消す（指標1種ごとの欄）",
    "indicator_roles_thresholds.json": "①写す→②消す（資料の表）", "r1_role_map.json": "①写す→②消す", "indicator_params_by_strategy.json": "①写す→②消す（資料の表）",
    "indicator_params_review.json": "①写す→②消す（資料の表）",
    "regime_laws.json": "③記録の名前で引く", "m2_stage_candidates.json": "③記録の名前で引く", "condition_parts.json": "③記録の名前で引く",
    "exit_families_rules.json": "③記録の名前で引く", "material_ranking.json": "③列の名前を記録から作る（成績の記録は残す）",
    "composition_rules.json": "②消す（指標1種ごとの欄）", "materials.json": "②消す（指標1種ごとの欄）",
    "identity_s1_legacy.json": "③記録の名前で引く", "identity_s2_legacy.json": "③記録の名前で引く", "r9_demand_fixture.json": "③記録の名前で引く",
    "indicator_fix_plan.json": "②消す（売買のプログラムが読まない記録）", "indicator_params_by_strategy.before_153.json": "②消す（売買のプログラムが読まない記録）",
    "indicator_source_map.json": "②消す（売買のプログラムが読まない記録）", "read_plan_src_m2c15-hidden-params-20261004.json": "②消す（売買のプログラムが読まない記録）",
}
HOLDERS = {"INDICATOR_TABLE", "REFS", "FAMILY_LINEAGE", "MATERIAL_FAMILIES", "CONST_REGISTRY", "R1_KEEP_ON", "_EXIT_LEVEL_CONST", "RUNTIME_ALIAS",
           "V9_FAMILY_MAP", "_V9_LABEL_TO_FAMILIES", "_HOUKOU2PROP", "HOUKOU2PROP", "_BAND_IMPL", "_OSC_BOUNDS", "_OSC_PCTL", "FAMILY_TEMPLATES"}
COMPUTE_BODY_FILES = {"observe_diag.py", "indicator_reference_diag.py"}
CATWORDS = {"トレンド", "強さ", "勢い", "オシレーター", "ボラ", "出来高", "ローソク", "構造・位置", "需給", "時間帯",
            "順張り値", "状態量", "ボラ量", "反転サイン", "向きつき", "trend", "none", "vol", "reversal",
            "向き", "行き過ぎ", "値動きの幅", "位置"}

sys.path.insert(0, str(PR))
cwd = os.getcwd()
os.chdir(PR)
with contextlib.redirect_stdout(io.StringIO()):
    import indicator_reference_diag as iref  # noqa: E402
    import observe_diag as od  # noqa: E402
    import engine_tuner_exec as ex  # noqa: E402
os.chdir(cwd)
# ★2026-10-31（工事 m2c15-indicator-redirect-20261031・やることの表 F-4）＝名前は読む口 indicators.py から読む（集約の要件定義書 R5）。
#   indicators.json を直に開かない。読む口が無い・読めない・古い形なら、読む口が止める（fail-closed）
sys.path.insert(0, str(PR / "indicators"))
import indicators as _ind  # noqa: E402  読む口（indicators.json を開くのはこのプログラムだけ）
_BASE = set(_ind.load().names("指標の記録")) | set(_ind.load().names("部品の記録"))
NAMES = _BASE | set(od.MATERIAL_FAMILIES) | set(json.loads((SDK / ".claude/ratchet/signal_families.json").read_text(encoding="utf-8"))["parts"]) \
    | set(getattr(ex, "RUNTIME_ALIAS", {}).values()) | {"atr_14"}


def path_of(name):
    for base in (PR, ROOT / ".claude/tools", ROOT / ".claude/hooks", PR / "tuner_adapters"):
        p = base / name
        if p.exists():
            return p
    return None


def strs(node):
    return [n for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


# ★2026-11-01（235回目・ToDo の203番・まこさん「良い」「よい」）＝読む係の報告（readers_20261024/merge.md・2026-10-24 00:58）と
#   振り分けの返信（cc_cls_*.txt）の行番号は、報告が読んだ時点のコードの行。直す前は、その行番号をいまのコードとそのまま照らしていたので、
#   コードに行が足されると（161-2 で build_catalog の前に35行）、ずれた所に別の行が入り、写す行が黙って落ちる・入れ替わった
#   （_v9_part_variants の行が 2 → 0・worklog 20261101 §17-4）。
#   いまは、報告が読んだ時点の版（git の、報告の時刻より前の最後のコミット＝本物のリポジトリで引く・写しで走らせても同じ）と
#   いまのファイルを difflib で行ごとに突き合わせ、報告の行番号をいまの行番号に読み替えてから照らす。版が無い・中身が同じファイルは読み替えない。
REPORT_AT = "2026-10-24 00:58:00 +0900"
_REAL_ROOT = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
_LMAP: dict = {}


def _line_map(name: str) -> dict | None:
    """報告が読んだ時点の行番号 → いまの行番号（消えた行は、その直前で生きている行の次）。読み替えない物は None。"""
    if name in _LMAP:
        return _LMAP[name]
    import difflib
    import subprocess
    p = path_of(name)
    rel = p.relative_to(ROOT) if p is not None and str(p).startswith(str(ROOT)) else None
    mp = None
    if rel is not None:
        try:
            old = subprocess.run(["git", "-C", str(_REAL_ROOT), "log", "-1", "--format=%H", f"--before={REPORT_AT}", "--", str(rel)],
                                 capture_output=True, text=True, check=True).stdout.strip()
            old_text = subprocess.run(["git", "-C", str(_REAL_ROOT), "show", f"{old}:{rel}"], capture_output=True, text=True, check=True).stdout if old else ""
        except subprocess.CalledProcessError:
            old_text = ""
        new_text = p.read_text(encoding="utf-8")
        if old_text and old_text != new_text:
            a, b = old_text.splitlines(), new_text.splitlines()
            mp, cur = {}, 1
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
                for k in range(i1, i2):
                    if tag == "equal":
                        cur = j1 + (k - i1) + 1
                        mp[k + 1] = cur
                    else:
                        mp[k + 1] = (j1 + (k - i1) + 1) if tag == "replace" and k - i1 < j2 - j1 else cur
    _LMAP[name] = mp
    return mp


def _remap(name: str, n: int) -> int:
    mp = _line_map(name)
    return mp.get(n, n) if mp else n


def _remap_cell(name: str, cell: str) -> str:
    """報告の行の欄（「5856-5882」「3469・3990」「383,407」）の数字を、いまの行番号に読み替える。"""
    return re.sub(r"\d+", lambda m: str(_remap(name, int(m.group(0)))), cell)


rows = []   # (file, line, 種類, 中身, 振り分け)
for f in SCOPE_PY:
    p = path_of(f)
    if p is None:
        rows.append((f, 0, "読めない", "ファイルが見つからない", "—"))
        continue
    t = ast.parse(p.read_text(encoding="utf-8"))
    held_spans, holder_names = [], set()
    # ★2026-10-24（210回目）＝③の数の定数は、計算の関数（_r(...)・_reg(...) の呼び出しの中に名前が在る関数）が読む物だけにする。
    #   直す前は、検査の線（observe_diag.py:4351 の _INSP_STEP_NG_PCT ほか9つ）まで「①写す→②消す」に入っていた
    calc_refs = {x.id for c in ast.walk(t) if isinstance(c, ast.Call) and getattr(c.func, "id", "") in ("_r", "_reg")
                 for x in ast.walk(c) if isinstance(x, ast.Name)}
    reader_fn = defaultdict(set)   # 名前 → それを読む関数の名前
    fn_loads = defaultdict(set)    # 関数の名前 → その関数が読む名前
    for fd in ast.walk(t):
        if isinstance(fd, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for x in ast.walk(fd):
                if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                    reader_fn[x.id].add(fd.name)
                    fn_loads[fd.name].add(x.id)
    # 計算の関数から呼ばれる補助の関数まで、呼ばれる先をたどる（例＝_r の tb → _msw_indep が _MSW_P を読む）
    while True:
        more = set().union(*(fn_loads[x] for x in calc_refs)) - calc_refs
        if not more:
            break
        calc_refs |= more
    # 外すのは、読む所が在り、その全部がたどった関数の外にある定数（検査の線）だけ。どこからも読まれない定義は、指標の情報の残りとして入れる
    # ★2026-10-24（照らしで拾えなかった165行の A＝指標の情報なのに名前の文字を持たない物）を拾う
    #   ①区分の言葉（札・方向・性質・役割の区分）を2つ以上持つ辞書・一覧・dict(...)  ②名前が *_REF・*_REGISTRY・LINEAGE_*・*2PROP・*2LIN の代入
    #   ③indicator_reference_diag.py・observe_diag.py の一番外の、名前が「_大文字」で値が数の定数（パラメータ）
    for n in ast.walk(t):
        if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None:
            tg = n.targets[0] if isinstance(n, ast.Assign) else n.target
            nm = getattr(tg, "id", None) or getattr(tg, "attr", None) or ""
            cw = {s.value for s in strs(n.value)} & CATWORDS
            why = None
            if len(cw) >= 2 and isinstance(n.value, (ast.Dict, ast.List, ast.Tuple, ast.Set, ast.Call)):
                why = f"区分の言葉 {len(cw)}（例 {', '.join(sorted(cw)[:3])}）"
            elif re.search(r"(_REF|_REGISTRY|^LINEAGE_|2PROP$|2LIN$)", nm):
                why = "名前が定義の表"
            elif f in COMPUTE_BODY_FILES and n in t.body and re.match(r"^_[A-Z][A-Z0-9_]*$", nm) and isinstance(n.value, ast.Constant) \
                    and isinstance(n.value.value, (int, float)) and not isinstance(n.value.value, bool) \
                    and (nm in calc_refs or not reader_fn[nm] or reader_fn[nm] & calc_refs):
                why = f"パラメータの定数 {n.value.value}"
            # ★2026-10-25（監査 CP88 の修正10・まこさん「全部修正する」「ok」）＝左辺が組の代入（例＝_ABER_L, _ABER_A = 5, 15）も、1つずつ③の決まりで見る。
            #   直す前は nm が空になり、indicator_reference_diag.py:4525〜4529・:4803 の6か所が一覧に入らなかった
            elif f in COMPUTE_BODY_FILES and n in t.body and isinstance(tg, ast.Tuple) and isinstance(n.value, ast.Tuple) \
                    and len(tg.elts) == len(n.value.elts) and all(isinstance(e, ast.Name) for e in tg.elts):
                pairs = [(e.id, v.value) for e, v in zip(tg.elts, n.value.elts)
                         if re.match(r"^_[A-Z][A-Z0-9_]*$", e.id) and isinstance(v, ast.Constant)
                         and isinstance(v.value, (int, float)) and not isinstance(v.value, bool)]
                if len(pairs) == len(tg.elts) and any(k in calc_refs or not reader_fn[k] or reader_fn[k] & calc_refs for k, _ in pairs):
                    nm = ", ".join(k for k, _ in pairs)
                    why = f"パラメータの定数 {', '.join(str(v) for _, v in pairs)}"
                    holder_names.update(k for k, _ in pairs)
            if why:
                holder_names.add(nm)
                held_spans.append((n.lineno, n.end_lineno))
                rows.append((f, n.lineno, "持つ", f"{nm}（{why}）", "①写す→②消す"))
    for n in ast.walk(t):
        if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None and isinstance(n.value, (ast.Dict, ast.List, ast.Tuple, ast.Set)):
            hit = sorted({s.value for s in strs(n.value) if s.value in NAMES})
            if hit:
                tg = n.targets[0] if isinstance(n, ast.Assign) else n.target
                nm = getattr(tg, "id", None) or getattr(tg, "attr", None) or ast.unparse(tg)[:30]
                holder_names.add(nm)
                held_spans.append((n.lineno, n.end_lineno))
                rows.append((f, n.lineno, "持つ", f"{nm}（名前 {len(hit)}・例 {', '.join(hit[:3])}）", "①写す→②消す"))
        if isinstance(n, ast.Call) and getattr(n.func, "id", "") in ("_r", "_reg"):
            rows.append((f, n.lineno, "持つ", f"{n.func.id}(...) の呼び出し", "①写す→②消す"))
            held_spans.append((n.lineno, n.end_lineno))
    names_used = HOLDERS | holder_names
    for n in ast.walk(t):
        ln = getattr(n, "lineno", None)
        if ln is None or any(a <= ln <= b for a, b in held_spans):
            continue
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if n.value in NAMES:
                rows.append((f, ln, "直書き", n.value, "③向け直す"))
            elif any(j in n.value for j in SCOPE_JSON) and len(n.value) < 200:
                rows.append((f, ln, "読む", f"json の名前「{n.value[:60]}」", "③向け直す"))
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in names_used:
            rows.append((f, ln, "読む", n.id, "③向け直す"))
        elif isinstance(n, ast.Attribute) and n.attr in names_used:
            rows.append((f, ln, "読む", n.attr, "③向け直す"))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("rolling", "ewm", "pct_change") and f not in COMPUTE_BODY_FILES:
            rows.append((f, ln, "自前で計算", n.func.attr, "③向け直す"))


def jwalk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if str(k) in NAMES:
                out.append(f"{path}/{k}")
            jwalk(v, f"{path}/{k}", out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            jwalk(v, f"{path}[]", out)
    elif isinstance(o, str) and o in NAMES:
        out.append(path)


jrows = []
for j in SCOPE_JSON:
    cands = list((SDK / ".claude/ratchet").glob(j)) + list(PR.glob(j)) + list((PR / "recipes").glob(j)) + list((ROOT / ".claude/state").glob(j)) \
        + list((HERE).glob(j))
    if not cands:
        jrows.append((j, "見つからない", 0, JSON_RULE.get(j, "決まっていない")))
        continue
    out = []
    jwalk(json.loads(cands[0].read_text(encoding="utf-8")), "", out)
    top = Counter(re.sub(r"^/([^/\[]+).*", r"\1", x) for x in out)
    jrows.append((j, "・".join(f"{k} {v}" for k, v in top.most_common(6)), len(out), JSON_RULE.get(j, "決まっていない")))

# ★2026-10-24（210回目）＝指標の情報の置き場のうち、種類の名前の文字を持たない2つを足す（元＝ss_state_probe.json の 89-9＝observe_diag を読み込んで数えた出力）
#   d＝observe_config.json の古い鍵（値は数だけ。1つの鍵が何種類もの期間を決める）
#   d'＝どの設定の鍵からも読まない種類（パラメータが計算の関数の既定値＝_reg の行の中）
SP = json.loads((HERE / "ss_state_probe.json").read_text(encoding="utf-8"))["89-9"]
key_rows = [(k, len(v), "・".join(v)) for k, v in sorted(SP["鍵ごとのオンの種類"].items())]
reg_line = {}
for n in ast.walk(ast.parse((PR / "observe_diag.py").read_text(encoding="utf-8"))):
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_reg" and n.args and isinstance(n.args[0], ast.Constant):
        reg_line.setdefault(n.args[0].value, n.lineno)
code_rows = []
for s in SP["1種ずつ"]:
    if s["パラメータの鍵"]:
        continue
    ln = next((reg_line[r] for r in s["登録"] if r in reg_line), 0)
    code_rows.append(("observe_diag.py", ln, "持つ", f"{s['種類']} のパラメータ（計算の関数の既定値・設定の鍵から読まない）", "①写す→②消す"))
rows += code_rows

# 照らし
have = defaultdict(set)
for f, ln, *_ in rows:
    have[f].add(ln)
miss, checked, agent_rows = [], 0, []
for line in (HERE / "readers_20261024/merge.md").read_text(encoding="utf-8").split("## 全部の行", 1)[1].splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if not line.startswith("| a") or len(c) < 7 or c[1] not in SCOPE_PY:
        continue
    kind = c[4]
    if not ("持つ" in kind or kind.startswith(("読む", "自前で計算"))):
        continue
    checked += 1
    c[2] = _remap_cell(c[1], c[2])            # ★203番＝報告の行番号を、いまの行番号に読み替えてから照らす（表に出すのも読み替えた番号）
    sp = []
    for tok in re.split(r"[・,、 ]+", c[2]):
        nums = [int(x) for x in re.findall(r"\d+", tok)]
        if len(nums) >= 2 and re.search(r"[-〜~]", tok):
            sp.append((nums[0], nums[1]))
        else:
            sp += [(x, x) for x in nums]
    if not any(a <= x <= b for a, b in sp for x in have[c[1]]):
        miss.append(f"{c[1]}:{c[2]}  {c[3]}  [{kind}]  {c[5][:70]}")
        # ★2026-10-24＝拾えなかったエージェントの行も一覧に入れる（文は報告のまま）。実物の最初の行の文字を付ける
        src = path_of(c[1])
        first = ""
        if src is not None and sp:
            ls = src.read_text(encoding="utf-8").splitlines()
            first = ls[sp[0][0] - 1].strip()[:90] if 0 < sp[0][0] <= len(ls) else ""
        to = "①写す→②消す（確かめ待ち）" if "持つ" in kind else "③向け直す（確かめ待ち）"
        agent_rows.append((c[1], c[2], kind, c[3], c[5][:80], first, to))

# ★2026-10-24（まこさん「コピペしろ」「手書きはするな」）＝拾えなかったエージェントの行の振り分けは、CC の2つの返信の逐語のファイル
#   （verbatim/…/cc_cls_hold_20261024.txt・cc_cls_read_20261024.txt）から読み取る。見出し（**A.** など）の下の「ファイル名」と「:行」を拾う。
# ★2026-10-26＝工事のフォルダは、承認の後に acceptance_archive/verbatim/ へ動く（作業中の置き場に無ければ、控えの置き場を読む）
VB = next((p for p in (ROOT / ".claude/state/verbatim/m2c15-single-source-fix-20261023",
                       ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-single-source-fix-20261023")
           if p.is_dir()), ROOT / ".claude/state/verbatim/m2c15-single-source-fix-20261023")
LABEL = [(r"^\*\*A\.", "①写す→②消す（A・指標の情報）"), (r"^\*\*C\.", "③向け直す（C・読む所）"), (r"^\*\*B\.", "外す（B・指標の情報ではない）"),
         (r"^\*\*③向け直す", "③向け直す"), (r"^\*\*②消す側", "②消す（プログラムごと無くなる）"), (r"^\*\*(残り|これで)", None)]
cls = {}
for vf in ("cc_cls_hold_20261024.txt", "cc_cls_read_20261024.txt", "cc_cls_pta_20261024.txt"):
    lab, cur = None, None
    for line in (VB / vf).read_text(encoding="utf-8").splitlines():
        hit = next((lb for pat, lb in LABEL if re.match(pat, line.strip())), "NOHIT")
        if hit != "NOHIT":
            lab, cur = hit, None
            continue
        if lab is None:
            continue
        if not line.startswith("  "):
            cur = None
        for tok in re.finditer(r"([A-Za-z0-9_]+\.(?:py|json))|:(\d+)(?:〜:?(\d+))?", line):
            if tok.group(1):
                cur = tok.group(1)
            elif cur:
                lo = _remap(cur, int(tok.group(2)))       # ★203番＝振り分けの返信の行番号も、いまの行番号に読み替える
                hi = _remap(cur, int(tok.group(3))) if tok.group(3) else lo
                cls[(cur, lo, hi)] = lab


def _cls_of(f, cell):
    n = int((re.findall(r"\d+", cell) or ["0"])[0])
    for (cf, lo, hi), lb in cls.items():
        if cf == f and lo <= n <= hi:
            return lb
    return "振り分けが無い"


agent_rows = [r[:6] + (_cls_of(r[0], r[1]),) for r in agent_rows]
cnt = defaultdict(Counter)
for f, ln, k, what, to in rows:
    cnt[f][k] += 1
o = ["# 直す相手の一覧（gen_fix_inventory.py が実物から作った・手で書き替えない）", "",
     "範囲＝engine_tuner の入口から import でたどれるファイルと、その json と INDICATOR_TABLE を書くプログラム・資料の表（gen_fix_inventory.py の頭の説明）。",
     "振り分け＝持つ→①写す→②消す ／ 直書き・読む・自前で計算→③向け直す ／ json は表のとおり。", "",
     "## プログラム（ファイルごとの数）", "", "| ファイル | 持つ | 読む | 直書き | 自前で計算 |", "|---|---|---|---|---|"]
for f in SCOPE_PY:
    o.append(f"| {f} | {cnt[f]['持つ']} | {cnt[f]['読む']} | {cnt[f]['直書き']} | {cnt[f]['自前で計算']} |")
o += ["", "## json（指標の名前が出てくる鍵の道の数）", "", "| ファイル | 名前が出てくる所（一番外の鍵ごと） | 数 | すること |", "|---|---|---|---|"]
o += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in jrows]
o += ["", f"## observe_config.json の古い鍵（値は数だけで、種類の名前を持たない・{len(key_rows)}個・すること＝①写す→②消す）", "",
      "| 鍵 | 期間を決める種類の数 | 種類 |", "|---|---|---|"]
o += [f"| {k} | {n} | {v} |" for k, n, v in key_rows]
o += ["", f"## コードの中のパラメータ（設定の鍵から読まない種類・{len(code_rows)}種・すること＝①写す→②消す）", "",
      "| ファイル | 行（_reg の行） | 中身 |", "|---|---|---|"]
o += [f"| {f} | {ln or '—（f 文字列の登録）'} | {w} |" for f, ln, k, w, to in code_rows]
o += ["", f"## 照らし（エージェントの報告の行）", "", f"範囲の中の報告の行（持つ・読む・自前で計算）{checked} 行のうち、このプログラムが拾えなかった行 {len(miss)} 行", ""]
o += [f"- {m}" for m in miss]
o += ["", f"## エージェントの行で、このプログラムが拾えなかった物（{len(agent_rows)}行・文は報告のまま・実物の最初の行を付けた）", "",
      "| ファイル | 行 | 報告の欄 | 名前 | 報告の中身 | 実物の最初の行 | 振り分け |", "|---|---|---|---|---|---|---|"]
o += ["| " + " | ".join(str(x).replace("|", "／") for x in r) + " |" for r in agent_rows]
o += ["", "## 全部の行", "", "| ファイル | 行 | 種類 | 中身 | 振り分け |", "|---|---|---|---|---|"]
o += [f"| {f} | {ln} | {k} | {w.replace('|', '／')} | {to} |" for f, ln, k, w, to in sorted(rows)]
(HERE / "fix_inventory_20261024.md").write_text("\n".join(o) + "\n", encoding="utf-8")
(HERE / "fix_inventory_20261024.json").write_text(json.dumps(dict(py=rows, json=jrows, miss=miss, old_keys=key_rows, code_params=code_rows),
                                                           ensure_ascii=False, indent=1), encoding="utf-8")
print("古い鍵", len(key_rows), "個・コードの中のパラメータ", len(code_rows), "種（_reg の行が分からない", sum(1 for r in code_rows if not r[1]), "）")
print("範囲のプログラム", len(SCOPE_PY), "本・json", len(SCOPE_JSON), "本・名前の一覧", len(NAMES))
print("拾った行＝", len(rows), "（持つ", sum(1 for r in rows if r[2] == "持つ"), "・読む", sum(1 for r in rows if r[2] == "読む"),
      "・直書き", sum(1 for r in rows if r[2] == "直書き"), "・自前で計算", sum(1 for r in rows if r[2] == "自前で計算"), "）")
print("照らし＝報告の行", checked, "行のうち、拾えなかった行", len(miss))
for f in SCOPE_PY:
    print(f"  {f:32s} 持つ {cnt[f]['持つ']:4d} 読む {cnt[f]['読む']:4d} 直書き {cnt[f]['直書き']:4d} 自前 {cnt[f]['自前で計算']:3d}")
for a, b, c, d in jrows:
    print(f"  {a:36s} {c:6d}  {d}")
