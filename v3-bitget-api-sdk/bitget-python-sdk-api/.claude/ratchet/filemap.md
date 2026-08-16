<!-- FILEMAP_HASH=08eb439ac525cd1d -->
# filemap.md — 何がどこにあるかの地図（gen_filemap.py が自動生成＝手書き禁止）

⚠️ 手で書き換えないでください。ファイルの一覧も説明も、実体から機械で取っています。
説明はそのファイルの1行目です。だから中身とずれません。

```
python3 scripts/priority_rebuild/gen_filemap.py --write    # 作り直す
python3 scripts/priority_rebuild/gen_filemap.py --verify   # 改変・未更新の検出
```

## この地図でできること・できないこと（正直に）

できるのは「その道具が在ることを知らずに似たものを自作する」型の間違いを減らすことです。
できないのは「在るのに開かない」型と「経緯の受け取り方を間違える」型です。
そこはまこさんの目が最後の関所のまま残ります。

## 置き場所の注意（2026-07-27 に実測して判明）

- `.claude` は2箇所あります。repo の直下（hook・settings・state）と、bitget-python-sdk-api の下（ratchet・rules・memory）です。
- `bitget-python-sdk-api/.claude/state` は repo 直下の `.claude/state` へのリンクです。中身は1つで、どちらの道から開いても同じファイルです。
- next_step.md・goal_block.md・worklog は state にあります。

## やりたいこと → どれを使うか（迷ったらここだけ見る）

| やりたいこと | 使うもの | それは何か |
|---|---|---|
| いまの戦略の弱点を知りたい | `observe_diag.py` | 採点窓の売買記録を診断する。数えると診断するの2つだけ |
| Entry/Exit の値を調整したい | `engine_tuner.py` | 実エンジンと審判を回して値決め窓で値を選ぶ |
| E37 の値だけ調整したい | `engine_search_e37.py` | E37 専用の探索器 |
| 採否を決めたい | `score.py` | 採点窓の公式 net。ここだけが採否の数字 |
| 結果の中身を見たい | `report.py` | 型別・月別・出口別の内訳を出す |
| 前回との差を見たい | `analyze.py` | 前後比較と分布のずれを出す |
| 検証期間を知りたい | `periods.py` | 学習・捨て・値決め・確認・採点・封印の唯一の正本 |
| 採点窓を変えたので探索窓を選び直したい | `window_similarity.py` | 値動きの構造が近い窓を全期間から順位づける |
| 窓の選定の経緯を知りたい | `windows.md` | 期間の意味と経緯。gen_windows.py が機械生成 |
| いま何を採用しているか知りたい | `adopted_strategies.md` | 全戦略の地図と採用台帳 |
| まこさんが何を決めたか知りたい | `decisions.md` | 決定の一覧。提案の前に必ず読む |
| 次に何をするか知りたい | `next_step.md` | 次セッションの起点。セッション開始で全文表示される |

## 全部の一覧（231 件）

### 売買と判定のスクリプト — scripts/priority_rebuild（82 件）

| ファイル | 種類 | 使われ方 | 1行目の説明 |
|---|---|---|---|
| analyze.py | 結果を見る道具 | 実行して使う | 採点後の深掘りバッテリー（手抜き分析を物理的に不可能にする・1コマンドで全部出す） |
| build_labels_pct.py | データ・材料を作る | 読み込まれて使う／実行して使う | Phase 0: 5m bar × 1,462 指標 × 56 ラベル (28 MFE/MAE pct + 28 Triple Barrier) を生成 |
| condition_parts_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | 条件の部品の突き合わせ（段C の C-2・2026-08-11 新設・まこさん OK） |
| doc_coverage_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | 文書を作り直したときに「消えた中身」を機械で一覧に出す（読み取り専用の診断） |
| dsr_pbo.py | その他 | 読み込まれて使う | 評価基盤 項目F: Deflated Sharpe Ratio + Probability of Backtest Overfitting（自前） |
| e28_phase0_dollarbar.py | その他 | 読み込まれて使う／実行して使う | E28 Phase 0 Step 1: 情報バー(ドルバー)＋行き過ぎ分位＋FR フィルタ の素エッジ測定 |
| e29_phase0_lsratio.py | その他 | 読み込まれて使う／実行して使う | E29 Phase 0: 下げ相場 LONG 新入口＝L-S 比の極値（需給の歪み・素エッジ測定） |
| e34_levels.py | 戦略の実装 | 読み込まれて使う／実行して使う | E34 iteration-3 レジサポ特徴量（成分B＝盲点情報・H6 価格非依存・leak-safe） |
| e34_range_base.py | 戦略の実装 | 読み込まれて使う／実行して使う | E34 レンジBOT ベース v1（連続モード・LONG・merge+add+cap停止+単一TP中心回帰） |
| e34_range_zscore_taker.py | 戦略の実装 | 読み込まれて使う／実行して使う | E34 Phase 0: レンジ逆張り（相対分位 ∩ taker投げ売り枯渇・LONG単発）の素エッジ測定 |
| e35_box.py | 戦略の実装 | 読み込まれて使う／実行して使う | E35 レンジ上下オシレーション「箱」定義（下限S・上限R を 5m/1h/4h で別々に作り 5m に整列） |
| e35_range_oscillation.py | 戦略の実装 | 実行して使う | E35 レンジ上下オシレーション BOT（一式・連続モード両方向・採点まで） |
| e36_short_oscillation.py | 戦略の実装 | 読み込まれて使う／実行して使う | E36 SHORT専用 オシレーション戦略（急騰Exit SPIKE_SL ＋ 件数レバー） |
| e37_range_scalp.py | 戦略の実装 | 読み込まれて使う／実行して使う | E37 v5 レンジ・スキャル 両側 maker MR ＋「稼げるレンジ」検出器ゲート |
| e37_range_scalp_short.py | 戦略の実装 | 実行して使う | E37 レンジ・スキャル ショート戦略 v2（入口ゼロ設計・出来高伸び切り×上位足条件×浅スキャル出口） |
| e37_scalp.py | 戦略の実装 | 読み込まれて使う／実行して使う | e37_range_scalp.py — E37 v5 レンジ・スキャル 両側 maker MR ＋「稼げるレンジ」検出器ゲート |
| e38_logic_parts.py | 戦略の実装 | 読み込まれて使う／実行して使う | E38 候補ロジックの汎用売買部品（段2・まこさん GO 2026-07-24・設計 e38_design.md／グリッド節 E38） |
| e38_priority_stack.py | 戦略の実装 | 読み込まれて使う／実行して使う | E38 優先度スタック（設定駆動エンジン・フロー段1・設計書 e38_design.md まこさん承認 2026-07-24） |
| engine_search_e37.py | 値を調整する探索器 | 実行して使う | 層3エンジン内探索（まこさん GO 2026-07-21・段階B） |
| engine_tuner.py | 値を調整する探索器 | 読み込まれて使う／実行して使う | 実エンジン × 審判で Entry/Exit の値を調整しきる道具（旧 engine_search_e38.py・改名 2026-07-27 まこさん確定） |
| engine_tuner_exec.py | 値を調整する探索器 | 読み込まれて使う／実行して使う | 歩3 実行器（レシピ＝条件データを読んで共通の売買ループで売買する） |
| engine_tuner_fire_diag.py | 値を調整する探索器 | 読み込まれて使う／実行して使う | 撒いた構造が「どの関門で売買まで行けなくなるか」を数えるだけの道具。 |
| engine_tuner_gen.py | 値を調整する探索器 | 読み込まれて使う／実行して使う | 歩4 生成器（2段サンプリング＝構造をランダムに撒く→有望構造の値を TPE で詰める） |
| entry_pos_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 検証（診断レーン・acceptance 免除・2026-07-16 まこさん指示） |
| eval_engine.py | 審判・期間の正本（改造禁止） | 読み込まれて使う | 評価基盤 項目A: 約定・コスト計器（自前・replay_csv 準拠 + 楽観3点是正） |
| gen_auditor_brief.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | 監査テンプレの「プロジェクトの現在地」を実体から機械生成する（まこさん指摘 2026-07-27） |
| gen_cat_requirements.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | 要件定義書 cat_requirements.md を機械生成する（手書き禁止） |
| gen_composition_rules.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | 組み立ての決まりの生成器（2026-08-08 新設） |
| gen_decisions.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | まこさんが決めたことの一覧を機械生成する（手書き禁止・2026-07-26 まこさん OK） |
| gen_design.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | E38 設計書の機械生成（フロー段1・まこさん確定「設計書は手書きしない」） |
| gen_docmap.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | 機械が作る文書の全数の一覧を、道具の名乗りから作る（2026-08-16 新設） |
| gen_engine_tuner_manual.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | engine_tuner の取扱説明書を機械生成する（手書き禁止・2026-07-27 まこさん指示） |
| gen_engine_tuner_requirements.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | engine_tuner の要件定義書を機械生成する（手書き禁止・2026-07-27 まこさん指示） |
| gen_exit_families.py | 文書の生成器（手書き禁止の文書を作る） | 読み込まれて使う／実行して使う | 出口の枝の表（許可の一覧）の自動生成（D2 の前段・2026-08-07） |
| gen_filemap.py | 文書の生成器（手書き禁止の文書を作る） | 読み込まれて使う／実行して使う | 何がどこにあるかの地図を実体から機械生成する（まこさん指示 2026-07-27「一旦作ってみて」） |
| gen_fix_map.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | 監査FBの修正対応表（fix_map）を機械生成する（まこさん承認 2026-07-30）。 |
| gen_flow.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | 要件 json からフローを固定テンプレートで自動生成（まこさん指示 2026-07-23） |
| gen_materials.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | 材料の正本の生成器（2026-08-09 新設・マイルストーン①のフロー 段4） |
| gen_observe_manual.py | 文書の生成器（手書き禁止の文書を作る） | 読み込まれて使う／実行して使う | observe_diag の取扱説明書を機械生成する（手書き禁止・2026-07-26 まこさん指示） |
| gen_p23_candidates.py | 文書の生成器（手書き禁止の文書を作る） | 読み込まれて使う／実行して使う | P23 候補生成 + V9前向きシミュレーション（ratchet E6 土台） |
| gen_signal_families.py | 文書の生成器（手書き禁止の文書を作る） | 読み込まれて使う／実行して使う | 型の表（許可の一覧）の自動生成（CP4 監査フィードバック①・2026-08-06） |
| gen_v9_exits.py | 文書の生成器（手書き禁止の文書を作る） | 実行して使う | V9 の Exit 実装を実コードから機械で表にする（まこさん指摘 2026-07-27 を受けて新設） |
| gen_windows.py | 文書の生成器（手書き禁止の文書を作る） | 読み込まれて使う／実行して使う | 期間（窓）の説明を機械生成する（まこさん OK 2026-07-27「各書類へ自動生成するように」） |
| indicator_reference_diag.py | 観察・診断（売買記録を出さない） | 読み込まれて使う／実行して使う | 指標カタログの正しさの証明に使う参照表（read-only・診断レーン） |
| leak_causality_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | H2（leak なし）を「動かした結果」で確かめる読み取り専用の診断（2026-08-09 まこさん OK） |
| measure_e28_phase2.py | その他 | 実行して使う | E28 Phase 2: 下げ相場 LONG 確定エッジを連続モードで採点用 CSV 化 |
| measure_ground_combined_E32b.py | その他 | 実行して使う | P21+P23 合算地面（案2・cap停止つき・忠実ループ・自己検査つき） |
| measure_ground_newwindow_E31.py | その他 | 実行して使う | 検証期間 2ヶ月後ろ倒し版で P21/P23 の地面を測り直す（E31） |
| observe_diag.py | 観察・診断（売買記録を出さない） | 読み込まれて使う／実行して使う | 建玉の観察と探索を、決まった型で機械が全部出す道具（read-only 診断） |
| params_sidecar.py | 全戦略の共通土台 | 読み込まれて使う | 戦略が「実際に使ったパラメータ」を売買記録CSVの隣に書き出す汎用ヘルパー。 |
| periods.py | 審判・期間の正本（改造禁止） | 読み込まれて使う | 検証期間の【唯一の正本】（学習・捨て(embargo)・採点・封印の区切り）。 |
| precheck.py | 審判・期間の正本（改造禁止） | 読み込まれて使う／実行して使う | 採点前ゲート（手数料負け・環境ドリフトの事前検査・PASS しないと score.py が走らない） |
| preload_cache.py | データ・材料を作る | 実行して使う | replay preload(=ローソク足読込+指標計算) の parquet キャッシュ（時短③・承認済 2026-06-12） |
| ratchet_guards.py | その他 | 読み込まれて使う／実行して使う | ① 普遍的に常にダメ（正しさ・正直さ）を機械で自動中断する番人。 |
| ratchet_io.py | 全戦略の共通土台 | 読み込まれて使う／実行して使う | 全戦略・全ツール共有の「出力の保管インフラ」（read 専用の命名/移動のみ・net 不関与）。 |
| report.py | 結果を見る道具 | 読み込まれて使う／実行して使う | 結果レポート1本化（V9検証時代の散らばった出力を A〜I に統合） |
| rg5_dec17_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 診断（診断レーン・CSV/score 出力なし・print のみ） |
| rg5_entry_pos_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 診断（診断レーン・売買記録CSV/score を出さない・print/集計のみ） |
| rg5_upper_feasible_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 診断（診断レーン・CSV/score なし・print のみ） |
| rg5_vol_gate_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 診断（診断レーン・CSV/score なし・print のみ） |
| rg6_adaptive_band_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 診断（診断レーン・CSV/score なし・print のみ） |
| rg6_v25_entry_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 診断（診断レーン・CSV/score なし・print のみ） |
| score.py | 審判・期間の正本（改造禁止） | 読み込まれて使う／実行して使う | 味見の機械（審判）: 売買記録 → 手数料込み net を月いくらで返す |
| slot_opportunity_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | トレード数の天井の実測（read-only 診断・正本ツール） |
| strat_base.py | 全戦略の共通土台 | 読み込まれて使う／実行して使う | 全戦略（E35 / E36 / 今後 E37…）共通の土台モジュール（中立）。 |
| test_dsr_pbo_known_answers.py | 番人・検査 | 実行して使う | dsr_pbo.py 項目F の既知答えテスト F1-F6 |
| test_eval_engine_known_answers.py | 番人・検査 | 実行して使う | eval_engine.py 項目A の既知答えテスト T1-T5 |
| test_precheck_band_known_answers.py | 番人・検査 | 実行して使う | precheck --target 帯別証跡（v17）の既知答えテスト＋番人。 |
| train_e34_meta.py | その他 | 読み込まれて使う／実行して使う | E34 iteration-3: dwell 候補のメタラベリング（方向二値・LONG・採点なし） |
| traj_branch_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 検証（診断レーン・acceptance 免除・2026-07-14 GO） |
| traj_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | e37_traj_diag.py — read-only 検証（診断レーン・acceptance 免除・2026-07-14 まこさん承認・GO） |
| traj_sep_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 検証（診断レーン・acceptance 免除・2026-07-14 GO） |
| trend_exit_peak_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | read-only 検証（診断レーン・acceptance 免除・2026-07-16 まこさん指示） |
| tuner_backcalc.py | その他 | 読み込まれて使う／実行して使う | 判定の値を「逆算」で出すための材料を実測する（まこさん承認 2026-08-01） |
| tuner_judgement.py | その他 | 読み込まれて使う／実行して使う | 判定の1枚表（A＝出し切ったか／B＝本物か／C＝目標に届いたか）を1箇所に集める |
| tuner_stats.py | その他 | 読み込まれて使う／実行して使う | engine_tuner の「その数字が本物か」を測る（要件 R7 の B5・B6・まこさん OK 2026-07-27） |
| tuner_window_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | 窓の位置と長さを決めるための材料を実測する（読み取り専用・歩5 の3回目） |
| tuner_writeback.py | その他 | 実行して使う | engine_tuner が見つけた値を設定ファイルへ書き戻す（要件 R9・まこさん OK 2026-08-02） |
| v22_gate_diag.py | 観察・診断（売買記録を出さない） | 読み込まれて使う／実行して使う | read-only 検証（診断レーン・acceptance 免除・2026-07-14 まこさん承認） |
| v24_guard_diag.py | 観察・診断（売買記録を出さない） | 実行して使う | 番人メタ確認（read-only 診断レーン・acceptance 免除・2026-07-16） |
| verify_design_contract.py | 番人・検査 | 読み込まれて使う／実行して使う | 設計書 ↔ 実装 の機械照合（CC の「設計通り実装しない」虚偽＝類型G を物理検出） |
| window_similarity.py | データ・材料を作る | 実行して使う | window_similarity_probe.py — 探索窓の抽出＝値動きの構造特徴による類似窓ランキング（まこさん OK 2026-07-23） |

### 戦略の接続ファイル — scripts/priority_rebuild/tuner_adapters（3 件）

| ファイル | 種類 | 使われ方 | 1行目の説明 |
|---|---|---|---|
| __init__.py | その他 | 探索器が名前で読む | tuner_adapters — 戦略ごとの接続ファイル（engine_tuner が読む・要件 R4・まこさん承認 2026-07-27） |
| e37.py | 戦略の実装 | 探索器が名前で読む | e37 — E37 の接続ファイル（engine_tuner が読む・要件 R4／R1・まこさん承認 2026-07-27） |
| e38.py | 戦略の実装 | 探索器が名前で読む | e38 — E38 の接続ファイル（engine_tuner が読む・要件 R4・まこさん承認 2026-07-27） |

### 作業の正本・記録 — .claude/ratchet（38 件）

| ファイル | 種類 | 使われ方 | 1行目の説明 |
|---|---|---|---|
| adopted_strategies.md | 文書 | — | 全戦略ポートフォリオ地図 ＋ 採用済み戦略 台帳（正本インデックス） |
| analysis_playbook.md | 文書 | — | PDCA 分析プレイブック（原因分析の唯一の正本） |
| composition_rules.md | 文書 | — | 組み立ての決まり（全自動生成） |
| decisions.md | 文書 | — | まこさんが決めたこと（gen_decisions.py が自動生成＝手書き禁止） |
| docmap.md | 文書 | — | 機械が作る文書の全数の一覧（gen_docmap.py が自動生成＝手書き禁止） |
| e34_design.md | 文書 | — | E34 戦略設計書 v2 — レンジ逆張りBOT（行き過ぎ ∩ 投げ売り枯渇・LONG・add＋部分決済） |
| e35_design.md | 文書 | — | E35 戦略設計書 v1 — レンジ上下オシレーション BOT（多TFレジサポで箱定義・両方向・高頻度） |
| e37_design.md | 文書 | — | E37 戦略設計書 v5 — レンジ・スキャル 両側 maker MR ＋「稼げるレンジ」検出器ゲート |
| e37_improvement_milestones.md | 文書 | — | E37 改善マイルストーン（正本・まこさん確定 2026-07-17） |
| e38_design.md | 文書 | — | E38 優先度スタック 設計書（gen_design.py 機械生成＝手書き禁止） |
| e38_flow.md | 文書 | — | e38_priority_stack フロー（gen_flow.py 自動生成＝手書き禁止・型は gen_flow.py TEMPLATE が正本） |
| engine_tuner_defects.md | 文書 | — | engine_tuner の欠陥の一覧（2026-08-06 のセッションで発覚した分） |
| engine_tuner_fix_map.md | 文書 | — | engine_tuner 修正対応表（gen_fix_map.py が機械生成＝手書き禁止） |
| engine_tuner_manual.md | 文書 | — | engine_tuner 取扱説明書（gen_engine_tuner_manual.py が自動生成＝手書き禁止） |
| engine_tuner_materials.md | 文書 | — | 全体像を決めるための材料 |
| engine_tuner_milestones.md | 文書 | — | engine_tuner マイルストーン ／ フロー ／ やることリスト |
| engine_tuner_requirements.md | 文書 | — | engine_tuner 要件定義書（gen_engine_tuner_requirements.py が自動生成＝手書き禁止） |
| engine_tuner_step2_condition_format.md | 文書 | — | engine_tuner 歩2 — 条件データ形式の設計（CP3 反映版） |
| entry_exit_matrix.md | 文書 | — | Entry×Exit ロジック 網羅マトリクス（★全戦略共通） |
| exit_families.md | 文書 | — | 出口の枝の表（許可の一覧・全自動生成・CC の手書きの行ゼロ） |
| exit_opt_command_design.md | 文書 | — | Exit 最適化フローのスラッシュコマンド化【設計のみ・実装はまだ】 |
| ledger.md | 文書 | — | ratchet ledger — PDCA 全記録（結果 / 原因究明 / 改善 / 修正 をすべて残す） |
| materials.md | 文書 | — | 材料の正本（1枚・全自動生成・CC の手書きの行ゼロ） |
| observe_diag_manual.md | 文書 | — | observe_diag 取扱説明書（gen_observe_manual.py が自動生成＝手書き禁止） |
| research_e35_rangebot.md | 文書 | — | レンジ/逆張り BOT 設計の厳密ソース調査（deep-research 合成） |
| session_log_20260609.md | 文書 | — | セッション詳細ログ 2026-06-09（2026-06-08夜〜深夜）— CC の不正連続 / E9設計やり直し(出口の値を連続学習) / 本番大敗・出口値連続回帰は機能せず |
| session_log_20260610.md | 文書 | ⚠️ どこからも参照されていない | セッション詳細ログ 2026-06-10 — E10（P23 出口2分岐）実装→大敗→学習方法そのものへの疑義（要根本分析） |
| session_log_20260610_pm.md | 文書 | ⚠️ どこからも参照されていない | セッション詳細ログ 2026-06-10 PM — ML知識ベースアップ → E12/E13/E14（Entry net基準学習・サイズ強弱が初の地面超え・保有中早逃げ破棄） |
| session_log_20260611.md | 文書 | ⚠️ どこからも参照されていない | セッション詳細ログ 2026-06-11 — E15 部分決済の刻み ML（対照実験で棚上げ）→ E16 事前分析（境界スキャン・V9 全体地図）→ 次は P21 横展開 |
| session_log_20260612.md | 文書 | ⚠️ どこからも参照されていない | セッション詳細ログ 2026-06-12 — E19閉じ→E0.4計器修正→E20破棄→E21 GO（⚠️ 強制終了により翌セッションが事後再構成） |
| session_log_20260612_night.md | 文書 | ⚠️ どこからも参照されていない | セッション詳細ログ 2026-06-12 深夜 — E24-2 破棄→E25 実装・閉じ→分析の物理化第2弾 |
| session_log_20260711.md | 文書 | ⚠️ どこからも参照されていない | session_log 2026-07-11 — E37 基本原則③の照合分析 → v18 TP2 反対側ゾーン（詳細は ledger ARC33） |
| signal_families.md | 文書 | — | 型の表（許可の一覧・全自動生成・CC の手書きの行ゼロ） |
| strat_v9ml_design.md | 文書 | — | strat_v9ml 詳細設計（A・現方針＝V9踏襲ML） |
| v9_exits.md | 文書 | — | V9 の Exit 実装（gen_v9_exits.py が実コードから機械生成＝手書き禁止） |
| v9_logic.md | 文書 | — | V9 のロジックの構造（唯一稼いでいる実物の記録） |
| window_similarity_ranking.md | 文書 | — | 探索窓の類似窓ランキング（正本・2026-07-24 まこさん決定の根拠） |
| windows.md | 文書 | — | 検証に使う期間の正本（gen_windows.py が自動生成＝手書き禁止） |

### ルール — .claude/rules（10 件）

| ファイル | 種類 | 使われ方 | 1行目の説明 |
|---|---|---|---|
| acceptance_checklist.md | 文書 | — | acceptance.md 最低限必要項目（要件定義書 §4.6 準拠・出戻り防止） |
| cat_requirements.md | 文書 | — | 第0部 この文書を読む人へ |
| cc_role.md | 文書 | — | CC (Claude Code) 役割設定書 |
| core_rules.md | 文書 | — | 実装の MUST / NEVER |
| entry_fix_6axis_gate.md | 文書 | — | Entry 修正 6軸 受け入れゲート（§18.5 由来・実行強制用） |
| exchange_spec.md | 文書 | — | Bitget 発注仕様・安全基準 |
| false_positive_incident_policy.md | 文書 | — | 虚偽達成・虚偽報告インシデント方針（最重大） |
| phase_compliance_checklist.md | 文書 | — | Phase 別現実整合性チェックリスト |
| web_claude_role.md | 文書 | — | 機械照合担当 (降格・短縮版) |
| web_claude_self_check.md | 文書 | — | Web Claude セルフチェック (読了ゲート → 指示書発行前 → 完了報告受領時 → 重大判断時) |

### 知識と教訓 — .claude/memory（37 件）

| ファイル | 種類 | 使われ方 | 1行目の説明 |
|---|---|---|---|
| cc_entry_logic_self_study.md | 文書 | — | CC エントリーロジック自己学習資料 v6 |
| chatgpt_seven_step_origin.md | 文書 | — | 7 工程フレーム決定の根拠 (= ChatGPT 提案要約・⛔ 破綻判定済) |
| current_redesign_context.md | 文書 | — | なぜ今フロー改善・ML 内容見直しをしているのか (経緯サマリ) |
| entry_exit_relationship_kb.md | 文書 | — | トレードにおける Entry と Exit の関係性 ナレッジ |
| feedback_grid_conditions.md | 文書 | ⚠️ どこからも参照されていない | （見出しが無い） |
| handoff_to_web_claude.md | 文書 | — | Web Claude 向け 引き継ぎ資料 v1 (🧊 凍結・旧 framework) |
| handoff_to_web_claude_v2.md | 文書 | — | Web Claude 引き継ぎ資料 v2 — A-2 大枠設計の続き (🧊 凍結・旧 framework) |
| handoff_to_web_claude_v3_phase1_phase3a.md | 文書 | — | Web Claude 引き継ぎ資料 v3 — Phase 1 + Phase 3-a 完了報告 (⛔ leak 由来・数値無効) |
| handoff_to_web_claude_v4_phase1_7a.md | 文書 | ⚠️ どこからも参照されていない | Web Claude 引き継ぎ資料 v4 — Phase 1〜7-a 完了報告 (⛔ leak 由来・数値無効) |
| headroom_analysis_addendum_spec.md | 文書 | — | 頭打ち原因分析 追加分析 |
| headroom_analysis_spec.md | 文書 | — | 頭打ち原因分析 仕様書 (🧊 凍結・旧 framework) |
| improvement_ideation_kb.md | 文書 | — | 改善案・アイデアの発想法カタログ |
| improvements.md | 文書 | — | （見出しが無い） |
| indicator_combination_kb.md | 文書 | — | 指標の組み合わせ方の法則（知識の正本） |
| indicator_thresholds_outline.md | 文書 | — | A-2 閾値辞書 骨格（ターン A 成果物） |
| industry_benchmark_knowledge_base.md | 文書 | — | 業界相場・経験則 ナレッジベース |
| learning_design_v3.md | 文書 | ⚠️ どこからも参照されていない | ML 学習デザイン v3 完成版 (2026-05-20 まこさん承認・exchange_spec.md 準拠版) |
| lessons_active.md | 文書 | — | 現役教訓 (2026-05-02 以降・L-203〜L-153 + 新規 L-206 以降) |
| lessons_archive.md | 文書 | — | L-102以前のアーカイブ（106件） |
| ml_pipeline_baseline_v1.md | 文書 | — | ML pipeline 暫定ベース案 v2 (= 2026-05-27 セッション議論決着反映) |
| ml_pipeline_execlog.md | 文書 | — | ML pipeline 実行ログ + 現在地（新セッション最初に読む正本） |
| phase8_supervised_tool_survey.md | 文書 | — | 教師あり時系列分類 手法網羅リスト |
| phase_flow_v4_reorder_proposal.md | 文書 | ⚠️ どこからも参照されていない | phase_flow_v4 改善案 — 月 $1,900 到達のための 4 箇所改訂 |
| phase_flow_v4_with_recovery.md | 文書 | — | V4 学習フロー (Phase ごとの学習内容が主役・分かりやすく版) |
| priority_rebuild.md | 文書 | — | Priority ゼロから再構築フェーズ (🧊 凍結・旧 framework) |
| priority_v9_trade_logic_analysis.md | 文書 | — | 旧 Priority v9 トレードロジック構造分析 |
| project_v9_progress.md | 文書 | — | V9実装進捗（2026-04-03 更新 セッション2） |
| range_scalping_kb.md | 文書 | — | レンジ×スキャルで稼ぐ方法（知識の正本） |
| regime_research.md | 文書 | — | レジーム判定研究（🧊 **凍結中** 2026-05-11〜） |
| regime_trial_log.md | 文書 | — | レジーム試作版 詳細ログ |
| seven_step_framework.md | 文書 | — | 7 工程フレーム全体構成 (= ⛔ 破綻判定済・参照用) |
| signal_ledger.md | 文書 | — | シグナル候補検証台帳（唯一の正本） |
| step1_regime_design.md | 文書 | — | 工程 1 (相場の状態判定・レジーム判定) 詳細設計書 |
| technical_analysis_knowledge_base.md | 文書 | — | テクニカル分析ナレッジベース (辞典レベル) |
| trade_analysis_methods_kb.md | 文書 | — | トレード結果データ分析方法 ナレッジベース |
| trade_methods_study.md | 文書 | — | トレード手法 → ML設計ノート（最低限・都度深掘り前提） |
| v10_experiments.md | 文書 | ⚠️ どこからも参照されていない | （見出しが無い） |

### 物理強制の hook — .claude/hooks（61 件）

| ファイル | 種類 | 使われ方 | 1行目の説明 |
|---|---|---|---|
| approve_impl.sh | hook（条件を満たすまで手を動かせなくする） | — | まこさんが受け入れ条件リスト(.claude/state/acceptance.md)を承認する。 |
| block_premature_giveup.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit |
| block_uchikiri.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit |
| check_websearch_before_design_write.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit — 設計書前 しっかりベースアップ ゲート（2026-06-15 まこさん承認）。 |
| doc_map_guard.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse(Edit／Write): ledger.md / strat_v9ml_design.md に「経緯・失敗のログ」を書く違反(文書マップ §8.2)を物理ブロック。 |
| enforce_combo_matrix.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-06 まこさん指示で新設） |
| enforce_e37_pdca.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-02 まこさん指示・共通/E37専用を明確に分離） |
| enforce_e37_scalp_frequency.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse on Bash（2026-07-16 まこさん指示・fast-mode 専用ガード） |
| enforce_e37_split_ceiling.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-07-16 まこさん指示） |
| enforce_flow_declaration.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-07-25 まこさん指示・新設・safety hook＝両モードで有効） |
| enforce_ml_honesty.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-13 まこさん指示・機械学習の不正防止の1枚目=doc 層） |
| enforce_ml_wiring.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-07-13 まこさん指示・機械学習の不正防止の2枚目＝実行前コード照合） |
| enforce_no_false_report.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse on Write／Edit（2026-07-20 まこさん指示・fast-mode 限定） |
| enforce_observation_design.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-07-20 まこさん指示「今後そんな解釈しないように強制しろ」・新設） |
| enforce_observe_diag_only.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-07-24 まこさん指示・新設・safety hook＝両モードで有効） |
| enforce_pdca_chain.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-02 まこさん指示「PDCAとすべての思考がつながる仕組みを入れて」） |
| enforce_purpose_gate.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit／MultiEdit／Bash（2026-08-06 まこさん指示・新設・safety hook） |
| enforce_request_scope.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-07-20 まこさん指示・fast-mode 限定） |
| enforce_role_criteria.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-06-29 まこさん承認で新設） |
| enforce_scoring_window_only.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-07-16 まこさん指示で新設・fast-mode 専用ガード） |
| enforce_search_quality.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on WebSearch |
| enforce_signal_table_gate.sh | hook（条件を満たすまで手を動かせなくする） | — | G1【Critical・safety＝fast-mode でも有効】（CP4 監査・まこさん GO 2026-08-06） |
| enforce_strategy_anchor.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-04 まこさん承認で新設） |
| enforce_worklog_on_experiment.sh | hook（条件を満たすまで手を動かせなくする） | — | Stop（2026-07-16 まこさん指示・fast-mode 専用ガード／2026-07-17 まこさん承認で B/C 拡張） |
| forbid_fixed_value_tuning.sh | hook（条件を満たすまで手を動かせなくする） | — | 固定値調整の物理禁止（まこさん命令 2026-06-12・L-261/E20 再演防止） |
| force_read_ml_design.sh | hook（条件を満たすまで手を動かせなくする） | — | SessionStart hook: 必読の「警告・宣言義務」と、auto-load 対象外の小片だけを注入する。 |
| hook_health_check.sh | hook（条件を満たすまで手を動かせなくする） | — | SessionStart（2026-07-04 まこさん承認で新設） |
| pdca_fast.sh | hook（条件を満たすまで手を動かせなくする） | — | PDCA 強制フローの一時オンオフトグル（まこさん承認 2026-07-16・高速ループ用） |
| pdca_gate.sh | hook（条件を満たすまで手を動かせなくする） | — | Stop: PDCA 未閉じならターン終了をブロック（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示） |
| pdca_mark.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse: PDCA マーカー管理（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示） |
| record_read.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse on Read |
| remind_doc_readability.sh | hook（条件を満たすまで手を動かせなくする） | — | 資料文書を Write/Edit する瞬間に「文書はCCの足場が第一目的・ |
| require_acceptance_before_impl.sh | hook（条件を満たすまで手を動かせなくする） | — | ⚠️ fast-mode の早期 exit は「編集対象を判定した後」に移した（2026-07-20）。 |
| require_analysis_before_proposal.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-06-24 まこさん承認で新設） |
| require_arc_crosscheck_before_improve.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-16 まこさん承認・fast-mode 専用ガード） |
| require_banned_words_check.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse(Write／Edit) 禁止語チェックの事前実行を物理強制 |
| require_comprehension_check.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash／Edit／Write（2026-07-16 まこさん指示・新設） |
| require_data_read_before_improve.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-16 まこさん指示・fast-mode 専用ガード） |
| require_design_contract_before_run.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash |
| require_direct_csv_for_analysis.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-06-24 まこさん指示で新設） |
| require_instrument_read_before_impl.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-06-12 まこさん指示で新設） |
| require_interpretation.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit／MultiEdit／Bash（2026-07-26 まこさん指示・新設・safety hook） |
| require_leak_annotation.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-04 まこさん承認で新設） |
| require_period_source.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash |
| require_precheck_before_score.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash |
| require_probe_naming.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-06-26 まこさん承認で新設） |
| require_read_before_work.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash／Edit／Write／MultiEdit |
| require_spec_read_before_design.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-06-13 まこさん指示で新設） |
| require_tag_for_experiment.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Bash（2026-06-29 まこさん承認で新設） |
| require_workflow_for_impl.sh | hook（条件を満たすまで手を動かせなくする） | — | cc_role §1.4.6.3 物理強制: メインセッションが実装スクリプト(scripts/priority_rebuild/*.py)を |
| reset_interpretation.sh | hook（条件を満たすまで手を動かせなくする） | — | UserPromptSubmit（2026-07-26 まこさん指示・新設・safety hook＝両モードで有効） |
| reset_read_log.sh | hook（条件を満たすまで手を動かせなくする） | — | SessionStart |
| show_budget_before_design.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit |
| show_decisions.sh | hook（条件を満たすまで手を動かせなくする） | — | セッション開始時に「まこさんが決めたこと」の一覧を作り直して表示する |
| show_latest_state.sh | hook（条件を満たすまで手を動かせなくする） | — | SessionStart hook（現在地の機械表示・2026-06-12 まこさん指示で新設） |
| track_banned_words_check.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse(Bash) list_banned_words.py の実行を検知してマーカー touch |
| track_fastmode_data_read.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse on Bash（2026-07-16 まこさん指示・require_data_read_before_improve と対） |
| track_search_fetch.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse on WebSearch／WebFetch |
| update_websearch_marker.sh | hook（条件を満たすまで手を動かせなくする） | — | PostToolUse on WebSearch／WebFetch — L-236 物理強制経路 ＋ 検索ログ記録（2026-06-15 まこさん承認）。 |
| verify_handoff_paths.sh | hook（条件を満たすまで手を動かせなくする） | — | L-239 ずれ防止: 新セッション開始時に「次セッション着手」ブロックの参照パスを自動 ls チェック。 |
| warn_usd_absolute_in_e37.sh | hook（条件を満たすまで手を動かせなくする） | — | PreToolUse on Write／Edit（2026-07-16 まこさん指示・H6 価格非依存の警告のみ・非ブロック） |

## 使われていないもの（消し忘れ・重複の芽）

読み込まれてもいないし、実行もされないスクリプトです。同じ役割の道具を知らずに自作したときも、ここに出ます。

- 無し

どこからも名前を参照されていない文書です。役目を終えたか、書いたまま忘れられたものです。

- session_log_20260610.md
- session_log_20260610_pm.md
- session_log_20260611.md
- session_log_20260612.md
- session_log_20260612_night.md
- session_log_20260711.md
- feedback_grid_conditions.md
- handoff_to_web_claude_v4_phase1_7a.md
- learning_design_v3.md
- phase_flow_v4_reorder_proposal.md
- v10_experiments.md

## 足すときの決まり

- 新しいファイルの先頭には、必ず1行の説明を書きます。ここに出るのはその1行です。
- 「やりたいこと → どれを使うか」の索引に足すときは、gen_filemap.py の INDEX へ1行足します。
  実在しないファイル名を書くと自己検査が落ちます。
- 種類の分け方は名前の規約です。規約を増やすときは KIND_RULES へ1行足します。

