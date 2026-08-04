#!/usr/bin/env python3
"""e38_priority_stack.py — E38 優先度スタック（設定駆動エンジン・フロー段1・設計書 e38_design.md まこさん承認 2026-07-24）

ロジック定義の正本＝e38_logics.json（設定 json が設計書の中核であり実装データそのもの・e38_requirements.json decisions）。
本エンジンは設定を解釈する固定部品＝設定の外にロジック固有値をハードコードしない。
E37 一枚岩へは挿し込まない＝部品は import 再利用（run_e37＝engine_search_e37 と同一口・E37 本体は無変更）。
優先度は priority 順に設定を束ねる解釈口まで（段1 は S1/L1 が side 別で競合しない＝スロット調停の本格実装は段4）。

report §0（使用パラメータ）は e37 の実値自動生成に乗せる（まこさん指摘 2026-07-24「v60_166 と同じように生成できないの」）:
  run_e37 を通常経路（return_trades=False）で呼ぶ＝e37._out が _param_sections（実値・PARAM_SECTION_SCHEMA assert）で
  §0 を組む。書き出しの瞬間だけ strat_base._output_and_report を包み、stem/strategy/script を E38 へ差し替え・
  logic 列（診断・net 不関与）を注入・E38 節（ロジック定義・設定駆動）を追記する。使用フラグ全量の節は
  argparse でなく e38_logics.json 由来で同型生成（設定 json が唯一の出所＝どの値も漏れず載る）。

使い方:
  python3 scripts/priority_rebuild/e38_priority_stack.py --tag <実験名>                 # 本走（logic 列つき）
  python3 scripts/priority_rebuild/e38_priority_stack.py --tag <実験名> --no-logic-col  # 恒等確認（v59d_164 と md5 比較・logic 列は比較時に除外＝設計書 §9）
  ... --config <path>   # 破壊番人テスト用の設定差し替え（既定 e38_logics.json）
"""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
import pathlib

import pandas as pd

import e37_scalp as e37     # 部品 import 再利用（レンジ計器 RG-v5/v6・状態機械・v57 ロング枝を含む実エンジン口）
import e38_logic_parts      # 段2: 候補ロジックの汎用売買部品（generic_logic_loop・ENTRY_FNS）
import strat_base           # 共通土台（_output_and_report＝タグ連番・archive・sidecar の共通書き出し・acceptance_checklist D）

HERE = pathlib.Path(__file__).resolve()
DEFAULT_CONFIG = HERE.parent / "e38_logics.json"

REQUIRED_TOP = ("schema_version", "name", "global", "logics")
REQUIRED_LOGIC = ("id", "side", "priority", "enabled", "label", "engine_flags")


def load_logic_config(path: pathlib.Path) -> dict:
    """設定 json（正本）を読み、構造を検査する。

    破壊番人＝必須キー欠落・side 不正・id 重複・run_e37 に無い engine_flag・
    e37_scalp に無い const_override は実行前に停止（json の値が配線されず黙って無視される穴を止める）。
    """
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for k in REQUIRED_TOP:
        if k not in cfg:
            raise SystemExit(f"[設定エラー] 必須キー欠落: {k}（{path.name}）")
    valid_kw = set(inspect.signature(e37.run_e37).parameters)
    ids = []
    for lg in cfg["logics"]:
        for k in REQUIRED_LOGIC:
            if k not in lg:
                raise SystemExit(f"[設定エラー] logic 必須キー欠落: {k}（{lg.get('id', '?')}）")
        if lg["side"] not in ("short", "long"):
            raise SystemExit(f"[設定エラー] side 不正: {lg['side']}（{lg['id']}）")
        for k in lg["engine_flags"]:
            if k not in valid_kw:
                raise SystemExit(f"[設定エラー] run_e37 に無い engine_flag: {k}（{lg['id']}）")
        for k in lg.get("const_overrides", {}):
            if not hasattr(e37, k):
                raise SystemExit(f"[設定エラー] e37_scalp に無い const_override: {k}（{lg['id']}）")
        if lg["enabled"]:
            if not isinstance(lg["priority"], int):
                raise SystemExit(f"[設定エラー] enabled なのに priority が整数でない: {lg['id']}（優先度の確定はまこさん＝段3）")
            if _is_generic(lg):
                if "unimplemented" in str(lg.get("impl", {}).get("status", "")):
                    raise SystemExit(f"[設定エラー] 未実装ロジックを enabled にした: {lg['id']}（{lg['impl']['status']}）")
                if _entry_point(lg) == "grid_loop":        # グリッド（S5/L5・要件 R2・2026-08-04）
                    if lg["entry"]["type"] not in e38_logic_parts.GRID_ENTRY_TYPES:
                        raise SystemExit(f"[設定エラー] grid_loop に無い entry type: {lg['entry']['type']}（{lg['id']}）")
                elif lg["entry"]["type"] not in e38_logic_parts.ENTRY_FNS:
                    raise SystemExit(f"[設定エラー] 未実装の entry type: {lg['entry']['type']}（{lg['id']}）")
                nulls = [k for k, v in {**lg["entry"].get("params", {}), **lg["exit"].get("params", {})}.items() if v is None]
                if nulls:
                    raise SystemExit(f"[設定エラー] enabled なのに未確定値 null: {nulls}（{lg['id']}＝値は段2 探索・確定はまこさん）")
        ids.append(lg["id"])
    if len(ids) != len(set(ids)):
        raise SystemExit(f"[設定エラー] logic id 重複: {ids}")
    return cfg


def _is_generic(lg: dict) -> bool:
    """汎用部品ロジック（e38_logic_parts 経路）か。False＝e37 run_e37 経路（S1/L1）。"""
    return lg.get("impl", {}).get("module") == "e38_logic_parts"


def _entry_point(lg: dict) -> str:
    """e38_logic_parts のどの売買ループで動くか（generic_logic_loop ／ grid_loop＝要件 R2・2026-08-04）。"""
    return str(lg.get("impl", {}).get("entry_point", "generic_logic_loop"))


def build_run_kwargs(cfg: dict) -> tuple[dict, dict, dict]:
    """enabled なロジックの engine_flags / const_overrides を priority 順に束ねる。

    global.regime のフラグ（v20_rg5 / v25_adaptive_band）は S1/L1 共通の局面ゲート。
    戻り値: (run_e37 kwargs, モジュール定数 overrides, side→logic id の対応＝診断 logic 列用)。
    """
    kw: dict = {}
    const: dict = {}
    by_side: dict = {}
    for k, v in cfg["global"].get("regime", {}).items():
        if k != "note":
            kw[k] = v
    en = [lg for lg in cfg["logics"] if lg["enabled"]]
    for lg in sorted(en, key=lambda z: (int(z["priority"]), str(z["id"]))):
        if _is_generic(lg):
            continue                            # 汎用部品ロジックは run_e37 に渡さない（generic_logic_loop が担当）
        kw.update(lg["engine_flags"])
        const.update(lg.get("const_overrides", {}))
        side = "SHORT" if lg["side"] == "short" else "LONG"
        by_side.setdefault(side, lg["id"])      # run_e37 経路の trades への logic 割当（side↔logic 1対1・調停は段4）
    return kw, const, by_side


def used_values_section(cfg: dict, kw: dict, const: dict) -> dict:
    """§0 用「使用フラグ全量」の E38 版＝e38_logics.json 由来で自動生成（e37 の argparse 版 _used_flags_section と同型）。

    設定 json を唯一の出所にする＝今後どのロジック値を足しても report に漏れず載る（手書きドリフト対策の E38 形）。
    """
    used = {}
    for k in sorted(kw):
        src = [lg["id"] for lg in cfg["logics"] if lg["enabled"] and k in lg["engine_flags"]] or ["global.regime"]
        used[f"{k} = {kw[k]}"] = f"出典 {'/'.join(src)}（e38_logics.json engine_flags）"
    for k in sorted(const):
        src = [lg["id"] for lg in cfg["logics"] if lg["enabled"] and k in lg.get("const_overrides", {})]
        used[f"{k} = {const[k]}"] = f"出典 {'/'.join(src)}（e38_logics.json const_overrides→モジュール定数注入）"
    title = ("【使用フラグ全量（e38_logics.json 由来・自動生成＝設定 json が唯一の出所・"
             "どのロジック値を足しても漏れず載る・argparse 版 _used_flags_section の E38 形）】")
    return {title: (used or {"（有効ロジックなし）": "engine_flags なし"})}


def main() -> None:
    ap = argparse.ArgumentParser(description="E38 優先度スタック（設定駆動・正本 e38_logics.json・設計書 e38_design.md）")
    ap.add_argument("--tag", required=True, help="実験タグ（必須・出力 _<tag>_<NNN> 連番・§3.1）")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG), help="ロジック定義 json（既定 e38_logics.json・破壊番人テスト用に差し替え可）")
    ap.add_argument("--no-logic-col", action="store_true", help="logic 列を付けない（恒等確認＝採用土台と md5 比較の時だけ）")
    ap.add_argument("--smoke", type=int, default=0, help="データ短縮（0=本走＝採点窓+助走・番人テスト用）")
    a = ap.parse_args()

    cfg_path = pathlib.Path(a.config)
    cfg = load_logic_config(cfg_path)
    cfg_sha = hashlib.sha256(cfg_path.read_bytes()).hexdigest()[:16]
    print(f"[e38] 設定 json 指紋 sha256={cfg_sha}（e38_design.md 生成元指紋と照合可・設計書と実装データの一致）")

    kw, const, by_side = build_run_kwargs(cfg)
    en = [f"{lg['id']}(priority{lg['priority']}・{lg['side']})" for lg in cfg["logics"] if lg["enabled"]]
    print(f"[e38] 有効ロジック: {'、'.join(en) if en else 'なし'} / engine_flags {len(kw)}個 / const_overrides {len(const)}個")

    e38_extra = {
        f"【E38 ロジック定義（正本 e38_logics.json・sha256={cfg_sha}・逐語は json 本体）】": {
            lg["id"]: f"priority{lg['priority']} / {lg['side']} / enabled={lg['enabled']} / {lg['label']}"
            for lg in cfg["logics"]
        },
        "【E38 設定駆動（段1）】": {
            "正本": "scripts/priority_rebuild/e38_logics.json（設計書 e38_design.md は gen_design.py が json から機械生成）",
            "エンジン": "e38_priority_stack.py＝設定を解釈する固定部品（run_e37 を import 再利用・E37 本体無変更・調停本格化は段4）",
        },
    }

    df = e37._load(a.smoke)

    gen_logics = [lg for lg in cfg["logics"] if lg["enabled"] and _is_generic(lg)]
    gen_trades: list = []
    if gen_logics:                               # 段2 以降: 汎用部品ロジックを先に回して統合（段1 恒等時は空＝従来経路のみ）
        adaptive_k = e37.V25_K if cfg["global"].get("regime", {}).get("v25_adaptive_band") else None
        dfp = e38_logic_parts.prepare_df(df.copy(), adaptive_k=adaptive_k)
        for lg in sorted(gen_logics, key=lambda z: (int(z["priority"]), str(z["id"]))):
            if _entry_point(lg) == "grid_loop":            # グリッド（S5/L5・要件 R2・2026-08-04）
                tr = e38_logic_parts.grid_loop(
                    dfp, lg["entry"]["type"], lg["entry"]["params"], lg["exit"]["params"],
                    max_lots=int(lg.get("params", {}).get("max_lots", 2)), logic_id=lg["id"])
            else:
                tr = e38_logic_parts.generic_logic_loop(
                    dfp, lg["entry"]["type"], lg["entry"]["params"], lg["exit"]["params"],
                    max_lots=int(lg.get("params", {}).get("max_lots", 2)), logic_id=lg["id"])
            print(f"[e38] {lg['id']}（{_entry_point(lg)}・{lg['side']}）: {len(tr)} 行")
            gen_trades += tr

    saved = {k: getattr(e37, k) for k in const}
    for k, v in const.items():
        setattr(e37, k, v)                       # 値の正本＝json（const_overrides→モジュール定数注入・engine_search_e37 と同型）

    orig_out = strat_base._output_and_report

    def _e38_out(t, suffix, *, stem, strategy, script, sections, tag=None):
        """書き出しの瞬間だけ E38 の identity に差し替える（e37 の _param_sections 実値 §0 はそのまま通す）。"""
        t = t.copy()
        if not a.no_logic_col:
            t["logic"] = t["side"].map(by_side).fillna("")   # 診断列（net 不関与・報告のロジック別分解用）
        if gen_trades:
            gt = pd.DataFrame(gen_trades)
            if a.no_logic_col:
                gt = gt.drop(columns=["logic"])
            t = pd.concat([t, gt], ignore_index=True).sort_values("entry_time", kind="stable").reset_index(drop=True)
        for sd in sorted(by_side):
            print(f"[e38] {by_side[sd]}（side={sd}・run_e37 経路）: {int((t['side'] == sd).sum() - sum(1 for r in gen_trades if r['side'] == sd))} 行")
        return orig_out(
            t, suffix, stem="e38_priority_stack",
            strategy=f"E38 優先度スタック（{cfg['name']}・schema v{cfg['schema_version']}・設定駆動・S1/L1＝v59d_164 恒等移植）",
            script="e38_priority_stack.py",
            sections={**sections, **e38_extra}, tag=tag)

    strat_base._output_and_report = _e38_out
    try:
        e37.run_e37(df, cfg["global"]["box_tf"], tag=a.tag,
                    used_flags_section=used_values_section(cfg, kw, const), **kw)
    finally:
        strat_base._output_and_report = orig_out
        for k, v in saved.items():
            setattr(e37, k, v)


if __name__ == "__main__":
    main()
