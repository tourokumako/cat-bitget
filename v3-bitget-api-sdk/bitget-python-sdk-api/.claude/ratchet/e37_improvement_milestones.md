# e37_improvement_milestones.md — E37 改善マイルストーン（正本・まこさん確定 2026-07-17）

作成の経緯: まこさんが 2026-07-17 に E37 の改善マイルストーンをまとめ、正本として記録を指示した。過去にないまとめ。以後の improvement_plan / acceptance はこの5段に照合して書く。
位置付け: E37 改善の進むべき順番の正本。書くのは方向性と順番だけ。動く数字（現在の net・採否）は adopted_strategies.md と ledger.md を見る。

---

## 【目標】
net利益最大化するという目標（E36＋E37で月額net利益600＄以上）達成

## 【要件定義】必読
- cat_requirements.md　要件定義書
- exchange_spec.md　Bitget発注仕様、安全基準
- adopted_strategies.md — 採用済み戦略 台帳

## 【命題】
E37の戦略（スキャル）はぶらさないという条件のもと、
それぞれの入口の特性（下落系（天井=直近高値）と平坦/上昇系（天井=res_hi））に合わせて、
Entry/Exitの調整をする。

---

## ▼目標達成マイルストーン

### 1️⃣ Entry最適化
- レンジレジーム判定枠内で、TP取れる幅のあるレンジは漏れなくエントリーさせる。
- その際、2型に切り分ける（下落系=直近高値／平坦・上昇系=res_hi）。
- 1日10回くらい入れるといい。

**1️⃣の命題（まこさん 2026-07-17）**:
以下のような幅のあるレンジが来たら、必ずその上端で売って、下限までの往復を TP で取る。これをすべてのレンジでやる。

例示5窓（2026年・例示であり目標のすり替え禁止＝すべてのレンジが対象）:
- 5-6 21:40 ~ 5-7 00:50
- 5-12 7:10 ~ 16:55
- 3-23 18:45 ~ 3-24 5:20
- 3-26 2:00 ~ 13:30
- 3-3 1:40 ~ 8:40

**1️⃣の解決フロー（まこさん指定）**:
- ★前回データをすべて確認 → 分析（確認と分析方法がわからない→ナレッジ確認や WebResearch する）→ 改善案提案。
- ★Report 記載の「0. 使用パラメータ」も確認し、実装データの構造もインプットする。
- 前回データ: report_trades_e37_range_scalp_fix6m_097_score.txt ／ analysis_trades_e37_range_scalp_fix6m_097_score.txt

### 2️⃣ Exit側最適化
- 2型それぞれの特徴（エントリー後の玉の動きの特徴）に合わせて、利益は最大化、損失は最小化する。
- entry_exit_matrix.md を参考に最適化の方法を考える。

### 3️⃣ Entry/Exitをセットで最適化

### 4️⃣ ポジション数、add数も最適化
- add数は MAX の 5 にしてもいい（まこさん 2026-07-17）。

### 5️⃣ E36＋E37で最適化

---

## ナレッジ（分析・改善案の参照先）
- cc_entry_logic_self_study.md — エントリーロジック自己学習資料 v6
- entry_exit_relationship_kb.md — トレードにおける Entry と Exit の関係性 ナレッジ
- trade_methods_study.md — トレード手法
- trade_analysis_methods_kb.md — トレード結果データ分析方法 ナレッジベース
- technical_analysis_knowledge_base.md — テクニカル分析ナレッジベース（辞典レベル）
- industry_benchmark_knowledge_base.md — 業界相場・経験則
- range_scalping_kb.md — レンジ×スキャルで稼ぐ方法（知識の正本）

★改善案を思考する際は entry_exit_matrix.md — Entry×Exit ロジック 網羅マトリクス（全戦略共通）を参考にする。

---

## 守る前提（既存正本との接続）
- E37＝スキャル（§1.2.1・ショートのみ・レンジ・高頻度）。頻度を下げる改善は却下（cat_requirements §8.6）。
- fast-mode＝採点窓（直近6ヶ月）だけで probe・分析・采否（cat_requirements §8.5）。
- Exit の損切り・早切り系レバーは CC が提案しない。着手前にまこさんに相談（next_step.md Q1/Q3）。
- 実験の結果後は experiment_result_procedure.md の固定手順（score→report --vs→analyze --vs→型別分析→狙い対応の部分指標評価）。
