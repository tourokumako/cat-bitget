# adopted_strategies.md — 採用済み戦略 台帳（最終ロジック・スクリプト・採点の正本インデックス）

作成: 2026-06-20（まこさん指示「過去に採用となった最終ロジック・スクリプトをどこかに記録してほしい」）
位置付け: **採用が確定した戦略の最終形（ロジック要約・実体スクリプト・採点・役割・状態）の一覧の正本**。詳細な経緯・実験は ledger.md（追記ログ）。本書は「今ポートフォリオに何が入っているか」の index（採用/不採用が変わったら更新）。
出典が正: ledger.md の各 E エントリ＋ score.py の数字。差異が出たら ledger に合わせて更新。

<!-- PORTFOLIO_CHECK: BASE_MAX=E32b ; PILLARS=E32b,P21,P23,E28,E35,E36 -->
<!-- ↑ require_read_before_work.sh ゲート3（近視眼防止・2026-06-22 まこさん指示）が読む機械可読マーカー。
     goal_block.md の「## 器の現在値」セクションに、BASE_MAX（今の最大 deployable 地面＝E32b）が必ず入っていて、
     かつ PILLARS の採用戦略が計2本以上書かれていないと Bash/Edit/Write をブロックする。
     ＝最新の1実験だけを現在値にする近視眼（2026-06-22 E36 単独事案）を物理的に弾く。
     採用/不採用や最大地面が変わったら本行（BASE_MAX / PILLARS）だけ更新する＝hook は本行に自動追従（hook 側に戦略名を焼かない）。 -->

---

## ⚠️⚠️ 予算 0.12 BTC は【全採用戦略の共有枠】（最重要・CC が繰り返し誤解・2026-06-20）

**0.12 BTC は単一戦略（E35 等）の枠ではない。任意の時点 t で、下表の全採用戦略の全建玉 size を合計して ≤0.12 BTC**（CLAUDE.md §0-2「1ポジあたりでなく合計上限」／ cat_requirements §6.1 / H1 / false_positive §0-2）。
- 配分は戦略間で柔軟（例: SHORT 柱に厚く・LONG add-on に薄く・CLAUDE.md「P23=0.06／P3=0.01」）。合計 ≤0.12 のみが絶対制約。
- ⛔ **CC が繰り返す誤り**: 「この戦略の cap 0.12」と単一戦略に矮小化する（E35 LONG/SHORT 分割で再演・2026-06-20）。**新戦略を作る/採点する時は、既存採用戦略（E32b・E28…）と同じ 0.12 を奪い合う**＝合算で測る・上乗せ(additive)かを必ず見る。
- 物理: score.assert_hard_constraints（売買記録の時系列 cap・違反は採点拒否）＋ eval_engine.assert_position_cap。単一戦略の採点 CSV では「その戦略だけで 0.12」を測るが、**本番は全戦略合算**＝最終配分段で合算 cap を検証する。

---

## 採用済み戦略（柱・add-on）— E31 正本窓（採点 2025-06〜2026-02・score.py）

> ★各戦略は「ロジック（中身＝売買ルール）」「計測の道具（成績を出すスクリプト）」「最終データ（売買記録CSV＝採点対象）」の3つで構成。**P21 と P23 は別々の戦略**（E32b はその合算＝別戦略でない・下記注記）。

| 戦略 | 方向 | 役割 | 採点（月平均） | ロジック（中身・★変更禁止） | 計測の道具 | 最終データCSV | ledger |
|---|---|---|---|---|---|---|---|
| **P21** | SHORT | **SHORT 最強の生きた柱** | **月$401.51**（915件） | cat_v9_decider.py ＋ cat_params_v9.json（素のV9・MACD系・Entry＝decider／Exit実行＝replay_csv.py rc.run） | `measure_ground_newwindow_E31.py` | archive/trades_p21_E31_newwin_ground.csv | E16/E0.4/E31 |
| **P23** | SHORT | **SHORT 柱（ライブ cat_v9 の起点）** | **月$241.72**（280件） | cat_v9_decider.py ＋ cat_params_v9.json（素のV9・ストキャス系・Entry＝decider／Exit実行＝gen_p23_candidates.py run_continuous） | `measure_ground_newwindow_E31.py` | archive/trades_p23_E31_newwin_ground.csv | E0/E32/E31 |
| **E28** | LONG | **下げ相場 LONG の存在証明 add-on** | 月$3.96（+$27.71） | `measure_e28_phase2.py`（ドルバー 行き過ぎ1%ile ∩ taker投げ売り・素ルール） | （同左） | trades_e28_phase2_score.csv | E28 |
| **E35**（レンジ上下オシレーション） | 両方向 | レンジ柱候補（作業中） | 月+$18.99（iter9） | `e35_range_oscillation.py --iter9`（独自ロジック・hold-ML判別＋部分利確） | （同左） | trades_e35_oscillation_5m_iter9_score.csv | E35 iteration-9 |
| **E36**（SHORT専用オシレーション＋急騰Exit＋件数レバー） | SHORT | SHORT 柱候補（E35 から SHORT 切り出し＋判別器ゲート急騰Exit＋強レンジ ゾーン拡大・2026-06-22 採用） | **月$60.97**（$548.74・463件・1.05/日） | `e36_short_oscillation.py`（既定=gated spike＋zone拡大0.35・strat_base import＋②③④自前コピー（2026-06-23 切り分け＝E35 を import しない・別戦略）・shortset1[1h MACDゲート]＋iter9 出口＋SPIKE_SL=Lee-Mykland jump ∩ hold-ML 判別器ゲート θ学習窓選定＋強レンジ(ER<q0.25)で SHORT 反転ゾーン0.25→0.35・`--no-zone` で zone OFF=$539.06・`--no-spike` で spike OFF=$427.66） | （同左・score.py） | trades_e36_short_oscillation_5m_shortset1_score.csv | E36/E36-spike-iter2/E36 freq-iter1 |

> **E32b は別戦略でない＝P21 と P23 を一緒に動かした合算の実測（deployable・月$616.55）**。素朴な和（$401.51+$241.72=$643.23）でなく $616.55 になるのは、共有 cap と decider 順（V9 優先 P23>P21）で互いを少し削るため（21→23 仮説は不成立＝V9 順維持・ledger E32b）。計測の道具＝`measure_ground_combined_E32b.py`。＝本番で P21・P23 を一緒に回した時の正味 SHORT 合算。
>
> ⚠️ **P21/P23 は素の V9（cat_v9_decider.py＋cat_params_v9.json）そのまま＝Entry/Exit/閾値を改善して採用された版は無い**（ML改善 E8/E9/E14/E19/E21 はほぼ破棄・採用は E13 サイズだけ＋E0.4 計器修正のみ）。$401.51/$241.72 は素の V9 を新窓で測った地面（2026-06-20 archive CSV で再現確認）。最終データCSV は §3.1 で archive 退避＝再生成は measure スクリプト（V9 を5年 or スライス replay・重い）だが、**数字の確認は archive CSV を score.py に通すだけ（一瞬）**。

### 配分レバー（単独戦略でなく、柱に乗せるサイジング/配分の手法）
| レバー | 内容 | 状態 | ledger |
|---|---|---|---|
| E13 配分 | P23/P21 の予測強度別サイジング（唯一勝った「切る」以外のレバー） | 採用（レバー） | E13 |
| E16 文脈配分 | 文脈別の配分（旧計器 $1,691.97・最終配分段で再採点要） | 採用（レバー・要再採点） | E16/E0.4 |

### 不採用（柱にならなかった・誤解防止のため明記）
- **P1/P2/P3/P4 単独**＝全て採点期マイナス＝単独柱不成立（LONG 側に単独で立つ柱は1本も無い・ledger E22）。P4 は E26 で止血採用したが net マイナスのまま。
- **E34（レンジ平均回帰 旧ベース）**＝iter3 −$65 まで改善も黒字未達（E35 が後継構造）。
- **E35 iter10/11/12**＝過剰適合/効果ゼロで不採用（base は iter9）。

---

## 使い方・更新ルール
- **新戦略を採点する時**: 単独 CSV の cap は「その戦略だけで 0.12」だが、**本番は本表の全戦略と 0.12 を共有**＝重複/上乗せ(additive)かを必ず確認（特に同方向＝E35-SHORT と E32b の食い合い）。
- **採用/不採用が確定したら本表を更新**（ledger に記録 → 本表の行を追加/状態更新）。役割（柱/add-on/レバー）と E31 窓 net と実体スクリプトを必ず書く。
- 詳細な経緯・5問・原因究明は ledger.md（本表は index・数字は score.py が正）。
- 地面（不変・比較の相手）: 手動 cat_v9 採点 月$172／通し$354（E0）。合格ライン 月$1,900 全月（全採用戦略の合算で届かせる）。
