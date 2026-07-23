#!/usr/bin/env python3
"""gen_flow.py — 要件 json からフローを固定テンプレートで自動生成（まこさん指示 2026-07-23）

狙い: CC がセッションごとにフローを手書き・再発明して二転三転する事故（2026-07-23 実演）を、
      観察器 --plan / gen_improvement_arc と同じ「機械生成＋hash 保護」の型で物理的に塞ぐ。
- フローの型（段の順序・各段の目的/道具/完了条件/禁止）は本ファイルの TEMPLATE に固定＝CC は変更しない
  （型の変更はまこさん承認＋本ファイルの編集＝git で追える）。
- 要件・確定事項・制約は e38_requirements.json（正本）から差し込む＝フロー本文に手書きしない。
- 段の完了は --done N --evidence <パス> でだけ記録（evidence の実在を検査）＝手書きで「完了」と書けない。
- 出力 md はヘッダに sha256。--verify で本文照合＝手書き改変を検出。

使い方:
  python3 gen_flow.py --req <requirements.json> --out <flow.md>            # 生成/再生成
  python3 gen_flow.py --req ... --out ... --done 0 --evidence <ファイル>    # 段0を完了に（根拠必須）
  python3 gen_flow.py --out <flow.md> --verify                             # 改変検出
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

# ── フローの型（固定・6段・変更はまこさん承認＋git commit のみ）─────────────────────────
TEMPLATE = [
    {
        "title": "段0 実測＝トレード数の天井の特定",
        "goal": "「トレード数を増やす」の設計を思いつきでなく在庫の実測で裏付ける。",
        "work": "現行 v59d_164 の売買記録とレンジ判定の時系列から3つを数える: "
                "(a) スロット占有＝同時保有が満杯で機会を逃した時間の割合 "
                "(b) 機会の在庫＝レンジ時間の分割（上端到達あり／届かない戻りのみ／下端到達／どれもなし） "
                "(c) ゲートの削り＝年齢制限・再発火待ち等が止めた発火数。",
        "tools": "read-only probe（*_probe.py 命名）または observe_diag。採点窓のみ。",
        "done_when": "3つの数字が worklog に機械出力の逐語で記録され、"
                     "増やす手段の優先順位（ロジック追加／スロット構成／ゲート緩和）が数字で決まっている。",
        "forbidden": "この数字を設計の固定値に焼く（あたり付け専用・L-330）。学習窓・全5年を使う。",
    },
    {
        "title": "段1 器＝E38 設定駆動エンジンと候補ロジック定義",
        "goal": "設定ファイルが正本のエンジンを新設し、設計書と実装の差異を構造的に消す。",
        "work": "e38 エンジン新設（strat_base・レンジ計器等を import 再利用・E37 一枚岩に挿し込まない）。"
                "ロジック定義（入口条件・出口値・優先度・スロット）は設定ファイル（json）に置き、"
                "エンジンは設定を解釈する固定部品にする。最初の登録＝S1（現行 v59d 相当ショート）と"
                "L1（現行 v57 相当ロング）。売買記録に logic 列（診断・net 不関与）。"
                "設計書は手書きしない＝骨格を設定 json＋段0 実測から機械生成（gen_design スクリプト・"
                "CC の自由記述を最小化）し、DESIGN_CONTRACT を含めて、まこさんの承認を得る。",
        "tools": "e38_*.py（新規）・logic config json・acceptance/設計書・verify_design_contract.py。",
        "done_when": "設計書がまこさん承認済み。E38 が S1/L1 構成で走り、py_compile・番人"
                     "（わざと壊して落ちる）・妥当性確認（件数/型別が v59d と桁が合う）を通過。",
        "forbidden": "採点窓を覗く。設定ファイルの外にロジック固有値をハードコードする。",
    },
    {
        "title": "段2 探索＝ロジック単位の層3エンジン内探索",
        "goal": "各候補ロジックの指標・閾値・時間軸・パラメータを実エンジン＋審判式で最適化する。",
        "work": "候補ロジック（ショート: S1 上端逆張り/S2 戻り売り/S3 上抜け失敗/S4 統計的回帰/S5 グリッド売り・"
                "ロング: L1 下端反発/L2 急落後反発/L3 下抜け失敗/L4 統計的回帰/L5 グリッド買い）を設定に足し、"
                "engine_search の E38 版（設定の値を差し替え）でロジックごとに探索。"
                "探索期間は前半＝最適化・後半＝同じ値のままの確認に分割（観察器 節8 と同型）。"
                "探索の目的関数窓はまこさんが決める。",
        "tools": "engine_search_e38（新規・engine_search_e37 の型）・Optuna・score.score（import のみ H13）。",
        "done_when": "ロジック別成績表（前半 net・後半 net・件数/日・保有・型別）が機械出力で揃っている。",
        "forbidden": "採点窓を目的関数にする（L-267）。疑似シミュの数字で候補を選ぶ（L-330）。"
                     "件数/日が出ないロジックを net だけで上位に置く（§8.6）。",
    },
    {
        "title": "段3 順位づけ＝優先度の確定",
        "goal": "成績表から各サイドの優先度1・2・3…をまこさんが決める。",
        "work": "安定（前半後半の両方でプラス）∩ 件数/日 を一級にした成績表を提示し、"
                "優先度リストのまこさん確定を得て設定ファイルに記録する。",
        "tools": "段2の成績表・logic config json。",
        "done_when": "優先度リストがまこさん確定として設定ファイルに記録されている。",
        "forbidden": "CC が優先度を確定する。成績表にない理由で順位を付ける。",
    },
    {
        "title": "段4 統合＝優先度スタック本走",
        "goal": "確定した優先度で全ロジックを1つの器に統合し、スロット配分で高優先を先に通す。",
        "work": "スロット配分（優先度別の枠数・発火競合は若い番号優先）とスロット構成"
                "（lot サイズ×枠数＝トレード数を増やす側の設計・値の水準はまこさん）を設定に入れ、"
                "統合構成で本走（--tag 連番）→ report/analyze --vs v59d_164。",
        "tools": "E38 エンジン・ratchet_io（タグ連番・archive 自動）・report.py/analyze.py。",
        "done_when": "統合本走の CSV・report・analyze が揃い、型別・ロジック別の分解が出ている。",
        "forbidden": "採点結果を見てから設定を戻して再本走を繰り返す（採点窓の実質探索化）。",
    },
    {
        "title": "段5 採点・採否",
        "goal": "統合最終形1つを採点窓で測り、まこさんが採否を判断する。",
        "work": "score.py（採点窓・periods 正本）＋件数/日≥5＋型別4分割＋ロジック別＋N5 区間の明記で報告。"
                "比較の基準＝trades_e37_range_scalp_v59d_164（採用土台）。",
        "tools": "score.py・report.py/analyze.py（--vs v59d_164）。",
        "done_when": "まこさんの採否が出て、台帳・worklog・next_step に記録されている。",
        "forbidden": "N5 が0を跨ぐのに黒字と書く。採用前に E37 土台を archive する。",
    },
]


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _state_path(out: Path) -> Path:
    return out.with_suffix(".state.json")


def build(req: dict, state: dict) -> str:
    L = []
    L.append(f"# {req['name']} フロー（gen_flow.py 自動生成＝手書き禁止・型は gen_flow.py TEMPLATE が正本）")
    L.append("")
    L.append(f"生成元要件: e38_requirements.json（{req['created']}・{req['owner']}）")
    L.append("⚠️ 本ファイルの手書き編集は禁止。段の完了は gen_flow.py --done N --evidence <パス> のみ。改変検出＝ --verify。")
    L.append("")
    L.append("## 要件（逐語・正本）")
    for s in req["requirement_verbatim"]:
        L.append(f"> {s}")
    L.append("")
    L.append(f"## 目的\n{req['goal']}")
    L.append("")
    L.append("## 確定事項（まこさん決定）")
    for s in req["decisions"]:
        L.append(f"- {s}")
    L.append("")
    L.append("## 制約（全段共通）")
    for s in req["constraints"]:
        L.append(f"- {s}")
    L.append("")
    L.append("## 段（この順で進める・飛ばさない・現在地は状態列）")
    L.append("")
    for i, st in enumerate(TEMPLATE):
        done = state.get(str(i))
        mark = f"✅ 完了（根拠: {done}）" if done else "⬜ 未着手"
        L.append(f"### {st['title']} — {mark}")
        L.append(f"- 目的: {st['goal']}")
        L.append(f"- 作業: {st['work']}")
        L.append(f"- 道具: {st['tools']}")
        L.append(f"- 完了条件: {st['done_when']}")
        L.append(f"- ⛔ 禁止: {st['forbidden']}")
        L.append("")
    body = "\n".join(L)
    return f"<!-- FLOW_HASH={_sha(body)} -->\n{body}"


def verify(out: Path) -> int:
    text = out.read_text(encoding="utf-8")
    head, _, body = text.partition("\n")
    want = head.replace("<!-- FLOW_HASH=", "").replace(" -->", "").strip()
    got = _sha(body)
    if want == got:
        print(f"✅ verify OK（hash {got}）")
        return 0
    print(f"❌ 改変検出: ヘッダ {want} ≠ 本文 {got}（手書き編集の疑い＝ gen_flow.py で再生成する）")
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--req", help="要件 json（正本）")
    ap.add_argument("--out", required=True, help="出力フロー md")
    ap.add_argument("--done", type=int, help="完了にする段番号（--evidence 必須）")
    ap.add_argument("--evidence", help="完了の根拠ファイル（実在検査）")
    ap.add_argument("--verify", action="store_true", help="改変検出のみ")
    a = ap.parse_args()
    out = Path(a.out)
    if a.verify:
        sys.exit(verify(out))
    req = json.loads(Path(a.req).read_text(encoding="utf-8"))
    sp = _state_path(out)
    state = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
    if a.done is not None:
        if not a.evidence or not Path(a.evidence).exists():
            sys.exit(f"❌ --done {a.done} には実在する --evidence が必須（根拠なしで完了と書けない）")
        state[str(a.done)] = a.evidence
        sp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    out.write_text(build(req, state), encoding="utf-8")
    print(f"[生成] {out}（段 {len(TEMPLATE)}・完了 {len(state)}）")


if __name__ == "__main__":
    main()
