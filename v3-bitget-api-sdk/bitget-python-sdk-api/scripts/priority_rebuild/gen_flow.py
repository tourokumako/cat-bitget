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
        "title": "段3 セット粗探索＝役割の枠内で稼げる Entry/Exit の組み合わせを見つける",
        "goal": "候補ロジックごとに、Entry/Exit のセットである程度成績の良い組み合わせを見つけ、"
                "優先度1候補を出す（まこさん提示 2026-07-25 の1）。Entry と Exit はセットで net が決まる"
                "（L-285）＝片側を先に固定して選ぶバイアスを避ける。",
        "work": "★探索範囲は戦略の役割（§8.6 スキャル＝保有は分単位・高頻度）から逆算した枠内に最初から固定する"
                "＝時間切れは5分〜1時間の刻み・枠外の値（2時間・4時間持ち等）を候補に入れない"
                "（2026-07-25 保有240分事案＝デイトレ部品値の流用の再発防止）。"
                "候補（S2 戻り売り/S3 上抜け失敗/S4 統計的回帰/S5 グリッド売り・"
                "L2 急落後反発/L3 下抜け失敗/L4 統計的回帰/L5 グリッド買い・観察から出る新型も可）を1本ずつ、"
                "策定4段で進める。"
                "1️⃣層1 観察＝observe_diag の --plan で観察計画を自動生成してまこさんに提出し、OK で本走。"
                "指標カタログ全体（entry_exit_matrix E-c 145ファミリー等）を複数時間足で当てて分離指標を順位づけする（数個の決め打ち禁止）。"
                "2️⃣層2 あたり付け＝疑似シミュ。採否にも候補選定にも使わない（L-330）。"
                "3️⃣層3 セット粗探索＝engine_tuner で Entry×Exit を同時に探索"
                "（値決め＝探索窓の全期間のみ・確認窓は選んだ値のまま1回表示のみ・"
                "窓はまこさん決定 2026-07-24・実日付は engine_tuner 定数が実体）。"
                "4️⃣正式本走→採否＝最終候補1つだけを --tag 連番で本走し、採点窓 score.py＋型別4分割＋N5 区間で"
                "まこさんが採否（E37 と同じ運用）。",
        "tools": "observe_diag（層1）・engine_tuner（層3）・e38_priority_stack（本走）・score.py/report.py/analyze.py。",
        "judge": "★段3 は粗探索＝一回の探索で net 最大化された完璧な値は出ない（段4 Entry 調整・段5 Exit 調整・段6 全体で作り込む土台）。"
                 "net がマイナスでも候補ごと却下しない＝「マイナス→切り捨て」で終える判定を禁止（全部切り捨てたら何も残らない・まこさん指摘 2026-07-25）。"
                 "① 全体 net の1数字で判定しない＝型別（side × down/flat_up）で切り分け、プラスの型・±0の型・出血の型を分ける。"
                 "② 出血がどの型・どの場面・どの出口理由に集中しているかを特定する＝それが段5 Exit 調整の対象（負けの1発を小さくする＝勝ち巻き込みを実測してセットで・Q1）。"
                 "③ プラス寄りの型・条件は段3ベースとして残す（設定 json／台帳）＝段4/段5 で作り込む入力にする。"
                 "④ 役割の枠外で稼げた形（例＝スキャル枠では負けbut長保有なら両窓プラス）は別戦略（レンジ×デイトレ E36 等）の材料として記録し渡す＝捨てない。"
                 "⑤ 判定に必ず「この結果のどこを段4/段5 でどう作り込めば目標に近づくか（活かす道筋）」を1つ以上書く。"
                 "参照＝feedback_no_discard_analysis_first（一回の悪化で破棄しない・ratchet）／feedback_execute_dont_critique_commit（やらない理由で潰さない・いい面も見出す）／block_premature_giveup。",
        "done_when": "各サイドに優先度1候補となる Entry/Exit セット（採点窓の採否記録つき）が1本以上あり、"
                     "件数/日と段2 最低ラインの充足が機械出力で出ている。"
                     "★各候補（不成立に見えるものを含む）に、上の判定視点⑤の「活かす道筋」が worklog に記録されている。",
        "forbidden": "役割の枠外の値（保有・時間切れが分単位の枠を超える等）を探索範囲に入れる。"
                     "層を飛ばす（2026-07-24 の1周目暴走＝観察なしで探索に直行した再発防止）。"
                     "探索・選定に採点窓を使う（L-267）。件数不足を net だけで補って採用候補に置く（§8.6）。"
                     "★結果がマイナスの候補を「不成立」で切り捨て、活かす点を見出さずに次へ行く（PDCA/ratchet 違反・まこさん指摘 2026-07-25）。",
    },
    {
        "title": "段4 Entry 調整＝Exit を固定して入口を磨く",
        "goal": "段3 で見つけた組み合わせの Exit 側を固定し、Entry 側（場面・確認・閾値）だけを調整する"
                "（まこさん提示 2026-07-25 の2）。",
        "work": "Exit＝段3 採択値に固定（動かさない）。Entry 側のパラメータだけを探索空間にして策定4段で回す"
                "（1️⃣層1 観察→2️⃣層2 あたり付け→3️⃣層3 探索→4️⃣正式本走→採否）。"
                "評価は件数/日・型別の質を一級にする（net だけで選ばない）。",
        "tools": "observe_diag・engine_tuner・score.py/report.py/analyze.py。",
        "done_when": "各候補の Entry 調整済み値が採否記録つきで揃っている。",
        "forbidden": "Exit 側の値を同時に動かす。層を飛ばす。探索に採点窓を使う。",
    },
    {
        "title": "段5 Exit 調整＝Entry を固定して出口を磨く",
        "goal": "Entry を段4 の値に固定し、Exit 側（状態機械の枝と値・保有時間）を細かく調整する"
                "（まこさん提示 2026-07-25 の3）。",
        "work": "Entry は固定。保有時間・時間切れはまこさんの刻み（5分・10分・15分・30分・45分・1時間）で細かく探索する。"
                "枝の出発点＝V9 型状態機械カタログ（entry_exit_matrix ③-2）。"
                "1️⃣層1 観察＝entry 後の建玉の動き（含み益の推移・ピーク反転・失速・逆行・時間×損益）を observe_diag で観察。"
                "2️⃣層2 あたり付け（採否・選定に不使用）。"
                "3️⃣層3＝出口の枝×値を engine_tuner で探索。"
                "4️⃣正式本走→採点窓でまこさんが採否。",
        "tools": "observe_diag・engine_tuner・score.py/report.py/analyze.py。",
        "done_when": "各候補に、調整済み Exit のセットが採否記録つきで揃っている。",
        "forbidden": "Entry 側の値を同時に動かす。層を飛ばす。探索に採点窓を使う。"
                     "勝ち玉の巻き込みを実測せずに切る系の枝を足す（Q1・L-352/L-353）。",
    },
    {
        "title": "段6 全体詳細調整＝セット微調整と優先度・サイズ・add・最終採否",
        "goal": "Entry/Exit セットの微調整と、優先度・ポジションサイズ・枠数・add 数の全体調整を行い、"
                "統合最終形をまこさんが採否する（まこさん提示 2026-07-25 の4）。",
        "work": "(a) セット微調整＝Entry×Exit の相互作用（確認の強さ×TP 位置・型別の分岐・保有時間の整合など）を策定4段で調整。"
                "(b) 優先度＝各ロジックの採点窓の採否記録と件数/日を一級にした成績表を提示し、"
                "まこさんが各サイドの優先度1・2・3…を確定（設定 json に記録）。"
                "(c) スロット構成＝ポジションサイズ・枠数・add 数を策定4段で最適化（値の水準はまこさん・"
                "発火競合は若い番号優先）。"
                "(d) 統合最終形を本走→score.py 採点窓＋型別4分割＋ロジック別＋N5 区間→"
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


def _bullets(text: str) -> list:
    """長い1文字列を『。』で区切って箇条書きの行にする（詰め込み解消・見やすさ・文言は変えない）。"""
    return [f"- {p.strip()}。" for p in text.split("。") if p.strip()]


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
    # 最初の未完了の段＝現在地（👈 今ここ）
    cur = next((i for i in range(len(TEMPLATE)) if not state.get(str(i))), None)

    # 段の一覧表（現在地が一目で分かる）
    L.append("## 段の一覧（現在地が一目で分かる）")
    L.append("")
    L.append("| 段 | 状態 | 何をする |")
    L.append("|---|---|---|")
    for i, st in enumerate(TEMPLATE):
        stt = "✅ 完了" if state.get(str(i)) else ("👈 今ここ" if i == cur else "⬜ 未着手")
        name = st["title"].split("＝")[0].strip()
        aim = st["goal"].split("。")[0].strip()
        L.append(f"| {name} | {stt} | {aim} |")
    L.append("")

    # 段の詳細（作業・完了条件・禁止は箇条書きに分ける＝1行詰め込みを解消・文言は不変）
    L.append("## 段の詳細（この順で進める・飛ばさない）")
    L.append("")
    for i, st in enumerate(TEMPLATE):
        if state.get(str(i)):
            mark = f"✅ 完了（根拠: {state.get(str(i))}）"
        elif i == cur:
            mark = "👈 今ここ・未着手"
        else:
            mark = "⬜ 未着手"
        L.append(f"### 🟧 {st['title']} — {mark}")
        L.append("")
        L.append(f"**目的**: {st['goal']}")
        L.append("")
        L.append("**作業**:")
        L += _bullets(st["work"])
        L.append("")
        L.append(f"**道具**: {st['tools']}")
        L.append("")
        if st.get("judge"):
            L.append("**結果の判定（活かす点を見出す視点・切り捨てない）**:")
            L += _bullets(st["judge"])
            L.append("")
        L.append("**完了条件**:")
        L += _bullets(st["done_when"])
        L.append("")
        L.append("**⛔ 禁止**:")
        L += _bullets(st["forbidden"])
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
