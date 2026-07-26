#!/usr/bin/env python3
"""gen_design.py — E38 設計書の機械生成（フロー段1・まこさん確定「設計書は手書きしない」）

骨格を 設定 json（e38_logics.json＝ロジック定義の正本）＋要件 json＋段0 実測（worklog 逐語）から機械生成する。
CC の自由記述を最小化＝設定駆動により「設計書を書くと実装データもできる」は生成の向きごと消える
（e38_requirements.json decisions・gen_flow.py / 観察器 --plan と同じ思想）。

使い方:
  python3 gen_design.py            # 生成内容を stdout に表示（書かない）
  python3 gen_design.py --write    # .claude/ratchet/e38_design.md へ書き出し（DESIGN_HASH ヘッダ付き）
  python3 gen_design.py --verify   # 既存 e38_design.md の手書き改変検出（hash 照合）

- 期間の数値は書かない＝採点窓は periods.py（正本）・探索窓は engine_search_e37.py の SEARCH_* 行を
  ソースから逐語引用（require_period_source / SSOT・手打ちゼロ）。
- DESIGN_CONTRACT を含む（verify_design_contract.py が実行前に実装ソースと機械照合・e38_requirements.json decisions）。
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve()
SDK = HERE.parents[2]                       # bitget-python-sdk-api
REPO = HERE.parents[4]                      # cat-bitget
RATCHET = SDK / ".claude" / "ratchet"
REQ_JSON = RATCHET / "e38_requirements.json"
LOGIC_JSON = HERE.parent / "e38_logics.json"
FLOW_MD = RATCHET / "e38_flow.md"
OUT_MD = RATCHET / "e38_design.md"
WORKLOG = REPO / ".claude" / "state" / "session_worklog_20260723.md"
SEARCH_PY = HERE.parent / "engine_search_e37.py"

sys.path.insert(0, str(HERE.parent))
import periods  # noqa: E402  検証期間の唯一の正本（SSOT・手打ち禁止）

DESIGN_CONTRACT = {
    "impl_file": "scripts/priority_rebuild/e38_priority_stack.py",
    "self_check_calls": [
        "load_logic_config",      # 設定 json を読む固定部品（正本参照の配線）
        "e38_logics.json",        # 設定ファイル名（外部ハードコード禁止の要）
        "run_e37",                # e37 部品の import 再利用口（engine_search_e37 と同一口）
        "const_overrides",        # v59 値の json→setattr 注入（値の正本が json である配線）
        "_output_and_report",     # 共通書き出し（タグ連番・archive・sidecar・acceptance_checklist D）
        "priority",               # 優先度スタックの解釈口（段4 で調停本格化）
    ],
}


def _stage0_evidence() -> str:
    """段0 実測の逐語を worklog（session_worklog_20260723.md §8）から抽出する（手書き転記しない）。"""
    txt = WORKLOG.read_text(encoding="utf-8")
    m = re.search(r"(■ \(a\) スロット占有.*?)```", txt, re.S)
    if not m:
        raise SystemExit(f"段0 実測ブロックが見つからない: {WORKLOG}")
    return m.group(1).rstrip()


def _stage1_verbatim() -> str:
    """フロー正本 e38_flow.md の段1 節を逐語引用する（完了条件・禁止を再発明しない）。"""
    txt = FLOW_MD.read_text(encoding="utf-8")
    # 見出しは gen_flow の可読性改善（2026-07-24 §27）で「### 🟧 段1 …」形になった＝絵文字の有無どちらも受ける
    m = re.search(r"(### (?:🟧 )?段1 器＝.*?)(?=### (?:🟧 )?段2 )", txt, re.S)
    if not m:
        raise SystemExit(f"段1 節が見つからない: {FLOW_MD}")
    return m.group(1).rstrip()


def _search_window_verbatim() -> str:
    """値決め窓・確認窓は periods.py の実値から出す（2026-07-27 集約＝正本は periods.py 1箇所）。

    以前は engine_search_e37.py の定数行を逐語で拾っていたが、その定数が periods 参照へ変わり
    日付が出なくなったため実値へ切り替え。ここに日付を手で書かないのは前と同じ。
    """
    return (f"SEARCH_START = {periods.SEARCH_START.date()}   # 値決め窓（periods.py が正本）\n"
            f"SEARCH_END   = {periods.SEARCH_END.date()}   # 排他\n"
            f"CONFIRM_START= {periods.CONFIRM_START.date()}   # 確認窓（表示のみ・選び直さない）\n"
            f"CONFIRM_END  = {periods.CONFIRM_END.date()}   # 排他")


def _logic_section(lg: dict) -> str:
    pri = lg["priority"] if lg["priority"] is not None else "未確定（段3 まこさん）"
    s = [f"### {lg['id']}（priority {pri}・{lg['side']}・{'有効' if lg['enabled'] else '無効'}）: {lg['label']}",
         "",
         f"- 出典: {lg['source']}",
         f"- 実装: {lg['impl']['module']} / {lg['impl']['entry_point']}"]
    if lg["impl"].get("status"):
        s.append(f"- 状態: {lg['impl']['status']}")
    s.append(f"- 入口（type={lg['entry']['type']}）: {lg['entry'].get('summary', 'params が正本（null=段2 探索で決める）: ' + json.dumps(lg['entry'].get('params', {}), ensure_ascii=False))}")
    s.append(f"- 出口（type={lg['exit']['type']}）: {lg['exit'].get('summary', 'params が正本（null=段2 探索で決める）: ' + json.dumps(lg['exit'].get('params', {}), ensure_ascii=False))}")
    if lg["exit"].get("branches"):
        s.append("- 出口の枝（状態機械・entry_exit_matrix 基本原則③）:")
        for b in lg["exit"]["branches"]:
            s.append(f"  - {b}")
    s.append("")
    s.append("engine_flags（実装データ＝run_e37 への注入値・逐語）:")
    s.append("```json\n" + json.dumps(lg["engine_flags"], ensure_ascii=False, indent=2) + "\n```")
    if lg.get("const_overrides"):
        s.append("const_overrides（実装データ＝モジュール定数への注入値・逐語・段2 探索の主対象）:")
        s.append("```json\n" + json.dumps(lg["const_overrides"], ensure_ascii=False, indent=2) + "\n```")
    if lg.get("params"):
        s.append("params（実装データ＝関数引数への注入値・逐語）:")
        s.append("```json\n" + json.dumps(lg["params"], ensure_ascii=False, indent=2) + "\n```")
    return "\n".join(s)


def build() -> str:
    req = json.loads(REQ_JSON.read_text(encoding="utf-8"))
    cfg = json.loads(LOGIC_JSON.read_text(encoding="utf-8"))
    cfg_sha = hashlib.sha256(LOGIC_JSON.read_bytes()).hexdigest()[:16]

    p = []
    p.append("# e38_design.md — E38 優先度スタック 設計書（gen_design.py 機械生成＝手書き禁止）")
    p.append("")
    p.append(f"生成元: {LOGIC_JSON.name}（ロジック定義の正本・sha256={cfg_sha}）＋ {REQ_JSON.name} ＋ 段0 実測（worklog 逐語）。")
    p.append("再生成: python3 scripts/priority_rebuild/gen_design.py --write ／ 改変検出: --verify")
    p.append("⚠️ 本ファイルの手書き編集は禁止。変更は e38_logics.json（値）または gen_design.py（型・まこさん承認）を直して再生成。")
    p.append("⚠️ 設定 json が設計書の中核であり実装データそのもの（e38_requirements.json decisions）＝本書の flags/const は json の逐語ダンプ。")
    p.append("")
    p.append("## 1. 要件（逐語・正本 e38_requirements.json）")
    p.append("")
    for l in req["requirement_verbatim"]:
        p.append(f"> {l}")
    p.append("")
    p.append(f"目的: {req['goal']}")
    p.append("")
    p.append("## 2. 確定事項（まこさん決定・逐語）")
    p.append("")
    for d in req["decisions"]:
        p.append(f"- {d}")
    p.append("")
    p.append("## 3. 制約（全段共通・逐語）")
    p.append("")
    for c in req["constraints"]:
        p.append(f"- {c}")
    p.append("")
    p.append("## 4. 検証期間（数値は正本から・本書に手打ちしない）")
    p.append("")
    p.append(f"- 採点窓（采否・段5 のみ）: {periods.SCORE_START_STR} 〜 {periods.SCORE_END_STR}（periods.py 正本・fast-mode §8.5）")
    p.append("- 値決め窓・確認窓（段2 目的関数・まこさん決定 2026-07-24・選び方の正本 window_similarity_ranking.md）"
             "＝periods.py の実値（意味と経緯＝.claude/ratchet/windows.md）:")
    p.append("```python\n" + _search_window_verbatim() + "\n```")
    p.append("")
    p.append("## 5. 段0 実測（設計の入力・出典 session_worklog_20260723.md §8 逐語＝増やす手段の優先順位: 第1 ロジック追加・第2 スロット構成・第3 ゲート緩和）")
    p.append("")
    p.append("```")
    p.append(_stage0_evidence())
    p.append("```")
    p.append("⚠️ この数字は在庫の桁の把握＝設計の固定値に焼かない（L-330・フロー段0 ⛔）。")
    p.append("")
    p.append("## 6. global 設定（実装データ・逐語）")
    p.append("")
    p.append("```json\n" + json.dumps(cfg["global"], ensure_ascii=False, indent=2) + "\n```")
    p.append("")
    p.append("## 7. ロジック定義（段1 登録分＝S1/L1・値の出典は各節・CC の新数値ゼロ）")
    p.append("")
    tbl = ["| id | side | priority | enabled | 内容 | 入口 type | 出口 type |", "|---|---|---|---|---|---|---|"]
    for lg in cfg["logics"]:
        pri = lg["priority"] if lg["priority"] is not None else "未確定"
        tbl.append(f"| {lg['id']} | {lg['side']} | {pri} | {lg['enabled']} | {lg['label']} | {lg['entry']['type']} | {lg['exit']['type']} |")
    p.extend(tbl)
    p.append("")
    for lg in cfg["logics"]:
        p.append(_logic_section(lg))
        p.append("")
    if cfg.get("search_space"):
        p.append("## 7b. 探索範囲の宣言（段2・engine_tuner が読む・実装データ＝json 逐語）")
        p.append("")
        p.append("```json\n" + json.dumps(cfg["search_space"], ensure_ascii=False, indent=2) + "\n```")
        p.append("")
    p.append("## 8. 段1 の作業・完了条件・禁止（フロー正本 e38_flow.md 逐語＝再発明しない）")
    p.append("")
    p.append(_stage1_verbatim())
    p.append("")
    p.append("## 9. 段1 妥当性確認の番人（設計）")
    p.append("")
    p.append(f"- 恒等番人: S1+L1 を json 既定値のまま走らせた E38 出力が、採用土台 {cfg['global']['identity_baseline']['csv_stem']} と md5 完全一致（logic 列は比較時に除外・md5 は数字を見ない＝採点窓の覗き見でない）。")
    p.append("- 破壊番人: json をわざと壊す（必須キー欠落）と実行前に停止する。enabled=false でそのロジックの玉が消える。")
    p.append("- py_compile ＋ require_design_contract_before_run（下の DESIGN_CONTRACT を実行前に機械照合）。")
    p.append("")
    p.append("## 10. DESIGN_CONTRACT（verify_design_contract.py 実行前機械照合・e38_requirements.json decisions）")
    p.append("")
    p.append("```json\n" + json.dumps(DESIGN_CONTRACT, ensure_ascii=False, indent=2) + "\n```")
    p.append("")
    p.append("承認: まこさんの承認をもって段1 の設計確定（承認前にエンジン実装へ進まない）。")
    return "\n".join(p) + "\n"


def main():
    ap = argparse.ArgumentParser(description="E38 設計書の機械生成（e38_logics.json＋要件＋段0 実測から・手書き禁止）")
    ap.add_argument("--write", action="store_true", help="e38_design.md へ書き出し（DESIGN_HASH ヘッダ付き）")
    ap.add_argument("--verify", action="store_true", help="既存 e38_design.md の手書き改変検出")
    a = ap.parse_args()

    if a.verify:
        txt = OUT_MD.read_text(encoding="utf-8")
        m = re.match(r"<!-- DESIGN_HASH=([0-9a-f]{16}) -->\n", txt)
        if not m:
            raise SystemExit("DESIGN_HASH ヘッダなし＝手書きの疑い")
        body = txt[m.end():]
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        if h != m.group(1):
            raise SystemExit(f"改変検出: hash 不一致（ヘッダ {m.group(1)} / 実体 {h}）")
        print(f"verify OK: {OUT_MD}（hash {h}）")
        return

    body = build()
    if a.write:
        h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
        OUT_MD.write_text(f"<!-- DESIGN_HASH={h} -->\n" + body, encoding="utf-8")
        print(f"[出力] {OUT_MD}（hash {h}・{len(body.splitlines())}行）")
    else:
        print(body)


if __name__ == "__main__":
    main()
