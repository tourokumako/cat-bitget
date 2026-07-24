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
        "title": "段2 目標逆算＝1日のトレード数の目標を決める",
        "goal": "目標額から逆算して、ロングとショート合わせて1日に何トレード必要かを数字で決める。"
                "目標値が無いまま「増やす」と言わない（ピンぼけ防止・まこさん提示 2026-07-24 の①）。",
        "work": "机上の逆算（目標月額 ÷ 1件純益 ÷ 30日）は参考まで＝**実際の値動きの観察で現実的な値を出す**"
                "（まこさん指示 2026-07-24）。観察計画を --plan で自動生成してまこさんに提出し、OK で本走して、"
                "(a) レンジ中の戻り・往復の振幅分布＝手数料床（maker 往復＋滑り）を超える動きが1日に何回あるか "
                "(b) 型別（down/flat_up）・サイド別の1回あたり取れ幅の分布 "
                "(c) そこから現実的な「1日件数 × 1件単価」の取りうる範囲、を機械出力で提示する。"
                "材料に (d) E38 の目標月額（台帳マイルストーン＝E36+E38 合算 月$600 − E36 実測） "
                "(e) 採用土台 v59d_164 の実測単価（report A節/C2） (f) 段0 の在庫を添え、"
                "「1日トレード数の目標 × 前提の1件単価」の組をまこさんが確定する。",
        "tools": "observe_diag または read-only probe（--plan 提出→OK→本走）・report A節/C2（審判値）・段0 実測（worklog 逐語）。金額は機械出力の逐語のみ。",
        "done_when": "観察の機械出力（振幅分布・現実的な件数×単価の範囲）が揃い、"
                     "1日トレード数の目標と前提の1件単価がまこさん確定として worklog に記録されている。",
        "forbidden": "CC が目標値を決める。観察なしの机上逆算だけで目標を確定する。届かない時に前提の単価を黙って動かす。",
    },
    {
        "title": "段3 Entry 策定＝目標件数を満たす入口を両サイドで複数作る",
        "goal": "段2 の目標トレード数を達成できる Entry ロジックを、ロングとショートそれぞれで複数策定する"
                "（まこさん提示 2026-07-24 の②）。",
        "work": "候補（S2 戻り売り/S3 上抜け失敗/S4 統計的回帰/S5 グリッド売り・"
                "L2 急落後反発/L3 下抜け失敗/L4 統計的回帰/L5 グリッド買い・観察から出る新型も可）を1本ずつ、"
                "策定4段で進める。"
                "1️⃣層1 観察＝observe_diag の --plan で観察計画を自動生成してまこさんに提出し、OK で本走。"
                "指標カタログ全体（entry_exit_matrix E-c 145ファミリー等）を複数時間足で当てて分離指標を順位づけする（数個の決め打ち禁止）。"
                "2️⃣層2 あたり付け＝疑似シミュ。採否にも候補選定にも使わない（L-330）。"
                "3️⃣層3 候補選定＝engine_search_e38（値決め＝探索窓の全期間のみ・確認窓は選んだ値のまま1回表示のみ・"
                "窓はまこさん決定 2026-07-24・実日付は engine_search_e38 定数が実体）。"
                "4️⃣正式本走→採否＝最終候補1つだけを --tag 連番で本走し、採点窓 score.py＋型別4分割＋N5 区間で"
                "まこさんが採否（E37 と同じ運用）。"
                "この段の Exit は仮置き（共通部品）＝Entry の発火・件数・型の質を先に確定する。",
        "tools": "observe_diag（層1）・engine_search_e38（層3）・e38_priority_stack（本走）・score.py/report.py/analyze.py。",
        "done_when": "各サイドに採用候補 Entry が1本以上（採点窓の採否記録つき）あり、"
                     "採用候補の合計件数/日と段2 目標の充足率が機械出力で出ている。",
        "forbidden": "層を飛ばす（2026-07-24 の1周目暴走＝観察なしで探索に直行した再発防止）。"
                     "探索・選定に採点窓を使う（L-267）。件数不足を net だけで補って採用候補に置く（§8.6）。",
    },
    {
        "title": "段4 Exit 最適化＝採用候補 Entry ごとに出口を磨く",
        "goal": "採用候補の Entry に対して、Exit 側（状態機械の枝と値）を最適化する（まこさん提示 2026-07-24 の③）。",
        "work": "Entry は固定し、Exit を策定4段で進める。"
                "1️⃣層1 観察＝entry 後の建玉の動き（含み益の推移・ピーク反転・失速・逆行・時間×損益）を observe_diag で観察。"
                "2️⃣層2 あたり付け（採否・選定に不使用）。"
                "3️⃣層3＝出口の枝×値を engine_search_e38 で探索（枝の出発点＝V9 型状態機械カタログ・entry_exit_matrix ③-2）。"
                "4️⃣正式本走→採点窓でまこさんが採否。",
        "tools": "observe_diag・engine_search_e38・score.py/report.py/analyze.py。",
        "done_when": "各採用候補 Entry に、最適化済み Exit のセットが採否記録つきで揃っている。",
        "forbidden": "層を飛ばす。探索に採点窓を使う。勝ち玉の巻き込みを実測せずに切る系の枝を足す（Q1・L-352/L-353）。",
    },
    {
        "title": "段5 セット最適化＝Entry/Exit を一体で仕上げる",
        "goal": "Entry と Exit はセットで net が決まる（L-285）＝一体の微調整で各ロジックを完成形にする（まこさん提示 2026-07-24 の④）。",
        "work": "策定4段（層1 観察→層2 あたり付け→層3 探索→正式本走→採否）で、"
                "Entry×Exit の相互作用（確認の強さ×TP 位置・型別の分岐・保有時間の整合など）を調整する。",
        "tools": "observe_diag・engine_search_e38・score.py/report.py/analyze.py。",
        "done_when": "ロジックごとの完成形（Entry/Exit セット・採点窓の採否記録つき）が揃っている。",
        "forbidden": "層を飛ばす。探索に採点窓を使う。",
    },
    {
        "title": "段6 統合＝優先度・ポジションサイズ・枠数・add 数の最適化と最終採否",
        "goal": "完成したロジック群を優先度スタックとして統合し、配分を最適化して、まこさんが最終採否を判断する（まこさん提示 2026-07-24 の⑤）。",
        "work": "(a) 優先度＝各ロジックの採点窓の採否記録と件数/日を一級にした成績表を提示し、"
                "まこさんが各サイドの優先度1・2・3…を確定（設定 json に記録）。"
                "(b) スロット構成＝ポジションサイズ・枠数・add 数を策定4段で最適化（値の水準はまこさん・"
                "発火競合は若い番号優先）。"
                "(c) 統合最終形を本走→score.py 採点窓＋型別4分割＋ロジック別＋N5 区間→"
                "比較の基準＝trades_e37_range_scalp_v59d_164（採用土台）でまこさんが採否。",
        "tools": "logic config json・E38 エンジン・ratchet_io・score.py/report.py/analyze.py（--vs v59d_164）。",
        "done_when": "まこさんの採否が出て、台帳・worklog・next_step に記録されている。",
        "forbidden": "CC が優先度・サイズ・add 数を決める。採点結果を見てから設定を戻して再本走を繰り返す（採点窓の実質探索化）。"
                     "N5 が0を跨ぐのに黒字と書く。採用前に E37 土台を archive する。",
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
