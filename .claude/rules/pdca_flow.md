# pdca_flow.md — PDCA 物理強制マップ（段階 × 強制内容 × 強制方法 × 旗 × 抜け穴）

作成: 2026-06-16（まこさん指示「PDCA フローをまとめ直す・強制内容と強制方法を詳細に」）
位置付け: CC の PDCA 各段階で「何を・どの hook が・いつ・どう」物理強制しているかの一覧の正本。命名規約から外れたスクリプトが強制を素通りする抜け穴を明示し、新スクリプトの命名規約を定める。
出典: `.claude/settings.local.json`（hook 登録）/ `.claude/hooks/*.sh`（実体）。本書はインデックス（実体が正・差異が出たら実体に合わせて更新）。

---

## 0. 読み方（強制のタイミングは4種）

| タイミング | 意味 | 効果 |
|---|---|---|
| **SessionStart** | セッション開始時に実行 | 表示・準備（read_log リセット等） |
| **PreToolUse** | ツール実行の「前」 | FAIL（exit 2）でそのツールを実行させない＝ブロック |
| **PostToolUse** | ツール実行の「後」 | `.claude/state/pdca_need_*` の旗を立てる/下ろす |
| **Stop** | ターン終了の前 | 旗が残っていれば終了を止める（exit 2） |

- 旗 = `.claude/state/pdca_need_*` ファイル。`pdca_mark`（PostToolUse）が立て、`pdca_gate`（Stop）が残存を検出して終了を止める。
- 「ブロック」= ツールが実行されない。CC は条件を満たすまで先に進めない。

## 1. hook 一覧（26本・登録は settings.local.json）

| hook | タイミング | matcher | 役割 |
|---|---|---|---|
| verify_handoff_paths | SessionStart | — | 引き継ぎパスの存在チェック（ずれ検出） |
| force_read_ml_design | SessionStart | — | 必読・6軸ゲート・保管ルール等を表示 |
| reset_read_log | SessionStart | — | read_log をリセット（前セッションの読了を持ち越さない） |
| show_latest_state | SessionStart | — | next_step.md 全文表示（起点） |
| require_read_before_work | PreToolUse | Bash/Edit/Write/MultiEdit | 必読3本（WORKFLOW/ledger/adopted_strategies）＋目標逆算ブロック＋器の現在値が採用ポートフォリオの積み上げ（最大地面＋採用柱2本以上）になるまで作業ブロック（ゲート3＝近視眼防止・2026-06-22）＋**改善アーク列ゲート＝goal_block「改善の経緯」が 狙い だけでなく 内容（動かしたレバー/機構）・方法（検証/採否理由＝失敗の型）も列に持つ（2026-06-26・狙いだけでは過去 iter の失敗の型が見えず同型を再提案する穴を塞ぐ）** |
| record_read | PostToolUse | Read | Read した .md を read_log.txt に記録 |
| check_websearch_before_design_write | PreToolUse | Write/Edit | 設計書 Write 前に直近60分の検索ベースアップを要求 |
| enforce_search_quality | PreToolUse | WebSearch | 検索品質（12語以内・allowed_domains 指定） |
| track_search_fetch / update_websearch_marker | PostToolUse | WebSearch/WebFetch | search_log・marker 記録 |
| require_spec_read_before_design | PreToolUse | Write/Edit | 設計書を書く瞬間に cat_requirements/exchange_spec を Read 強制 |
| show_budget_before_design | PreToolUse | Write/Edit | 設計/改善案（acceptance.md / *_design.md）を書く瞬間に「予算0.12は全採用戦略の共有枠」＋採用台帳を1セッション1回表示（exit2 で1回ブロック→再実行で通す・SessionStart 表示は効果ないため提案の瞬間に出す・2026-06-20・marker は reset_read_log が消す） |
| require_instrument_read_before_impl | PreToolUse | Write/Edit | 実装を書く前に eval_engine（計器）を Read 強制 |
| doc_map_guard | PreToolUse | Write/Edit | ledger/設計書に経緯・失敗の語を書くのをブロック（置き場所違反） |
| forbid_fixed_value_tuning | PreToolUse | Write/Edit | 固定値スイープ（採点窓で最良値選定）をブロック（L-267） |
| require_acceptance_before_impl | PreToolUse | Write/Edit | scripts/priority_rebuild/*.py を書く前に acceptance＋承認を要求＋**疑似シミュ由来の固定値ゼロ宣言を必須（2026-06-26 まこさん承認）＝probe(疑似シミュ)で出た数値[θ/段数/AUC]を設計の固定値に焼くのをブロック。acceptance に『★疑似シミュ由来の固定値ゼロ』見出しが無いと exit2。背景＝add ゲート設計で probe の θ≤0.4/段数3 を「クリア」扱いし焼き込んだ事案（STRUCT_SL 近似+$895 が実エンジンで消失した轍と同型）** |
| require_analysis_before_proposal | PreToolUse | Write/Edit | 改善提案/設計（acceptance.md / *_design.md）を書く前に【分析フェーズ】を強制（採点非依存・2026-06-24）。A 着手＝分析KB(trade_analysis_methods_kb)/analysis_playbook §2/対象 report_・analysis_ を read_log で確認。B 完了＝`.claude/state/analysis_block.md` の必須**9見出し**（前後比較/両窓/fat-tail/MAE/較正[予測確率]/3分類/問5/経緯照合[E番号引用必須]/**⑨巻き込み検証**）。**⑨巻き込み検証（2026-06-26 追加・本丸）＝切る/早切り/Exit 系レバーは、そのルールが勝ち玉（特に fat-tail）に当たる量を数字で出す。損玉だけ見て天井を語る分析手法の欠陥を塞ぐ（2026-06-26 時間切れ損玉だけ切り出し「取り逃し +$2,624」と誤推定・同じ含み益シグナルが勝ち282玉 +$3,401 に当たるのを見落とした事案＝iter10/DYING_CUT 再演手前）。Exit/切る でない提案は「該当なし」と明記**。pdca_gate が採点後しか分析を強制しない穴（採点なし既存データ分析=強制ゼロ）を塞ぐ |
| block_uchikiri | PreToolUse | Write/Edit | アジャイル放棄を表す語をブロック（語一覧は実体参照） |
| require_precheck_before_score | PreToolUse | Bash | score.py を CLI 実行する前に precheck PASS を要求 |
| require_design_contract_before_run | PreToolUse | Bash | 戦略実行の前に DESIGN_CONTRACT で実装を機械照合 |
| require_period_source | PreToolUse | Bash | priority_rebuild の .py 実行前に、期間境界(TRAIN_END/SC_START/SCORE_START/SCORE_END/SEAL_START/EMBARGO)が periods.py 由来でない自前定義ならブロック（期間ズレ根絶・E0.5・2026-06-18） |
| require_direct_csv_for_analysis | PreToolUse | Bash | report.py/analyze.py の分析対象（第1引数）が archive/ 配下ならブロック（2026-06-24）。＝最新実験が archive に押し出された＝実験→分析の順序ミスを物理検出（実験は1回 --tag→直下で分析→2本目の前に済ます）。意図的な過去再分析のみ ANALYZE_ARCHIVE_OK=1 で通す |
| require_probe_naming | PreToolUse | Bash | /tmp・scratchpad から **python で走らせる** .py が `*_probe.py` / `*_deep_analysis.py` 命名でないとブロック（2026-06-26）。＝read-only 分析スクリプトの命名規約（§5）を物理化。背景＝接尾辞なし e3N_*.py 分析を pdca_mark が「実験」と誤検知し need_score 旗を誤発火させた事案。ls/mv/rm/cat は通す（python 実行時のみ＝改名・削除は可能）。**＋正しい命名の probe 実行時に「疑似シミュ＝あたり付け専用・出た数値を設計の固定値/採否根拠にしない・採否は実エンジン両窓 score.py」を必ず表示（2026-06-26 まこさん承認・使う瞬間に錨）** |
| pdca_mark | PostToolUse | Bash/Edit/Write | コマンド名で審判/分析/記録の旗を立てる/下ろす（--smoke/--no-score/--selftest は審判検知から除外・2026-06-18） |
| pdca_gate | Stop | — | 旗の残存でターン終了をブロック |
| approve_impl | （まこさんが実行） | — | acceptance の承認指紋を立てる |
| require_workflow_for_impl | （未登録） | — | 撤回済み（cc_role §1.4.6.3・複数CC Workflow 常時必須を廃止） |

## 2. 段階別フロー（順を追って）

### A. セッション開始（SessionStart）
4本（verify_handoff_paths / force_read_ml_design / reset_read_log / show_latest_state）が表示・準備。強制はまだ無い。次の作業で B が効く。

### B. 最初の Bash/Edit/Write の前（必読＋目標逆算＋器の現在値の積み上げ照合）
- **require_read_before_work**（PreToolUse）: 3ゲートを順に物理強制。全 Bash/Edit/Write をブロック。
  - **ゲート1（読了）**: 必読3本（WORKFLOW.md / ledger.md / **adopted_strategies.md＝採用ポートフォリオ台帳**）を Read tool で開く。
  - **ゲート2（目標逆算）**: goal_block.md に必須見出し（大目標/器の現在値/ギャップ/候補/天井/選定/3行ゲート/届く構成/戦略照合/**改善の経緯**）を書く。**改善の経緯**（2026-06-26 まこさん指示）＝対象戦略の直近イテレーション系譜を ledger から箇条書きで再構成し、各 iter に前提フラグ（nofloor ON/OFF 等・どの base の上か）を書く。最新1実験の局所結論を起点に改善議論へ走る穴（(A)DYING_CUT を nofloor OFF=base に当てた前提を見落とした 2026-06-26 事案）を塞ぐ。next_step「改善アーク」と対＝開始時(goal_block)と末(next_step)の二重強制。
  - **ゲート3（器の現在値＝近視眼防止・2026-06-22 まこさん指示）**: goal_block の「器の現在値」セクションに、採用台帳マーカー `<!-- PORTFOLIO_CHECK: BASE_MAX=… ; PILLARS=… -->` の「最大 deployable 地面（E32b）」＋「採用柱 計2本以上」が書かれているか照合。無ければブロック。＝最新の1実験だけを現在値にする近視眼（2026-06-22 E36 単独事案）を物理的に弾く。hook に戦略名を焼かず台帳マーカーから動的に読む（採用が変われば台帳1行更新で hook 追従）。
- 解除: read_log に3本が載り、goal_block の必須見出しが揃い、器の現在値が積み上げ照合を通る。記録は record_read（PostToolUse Read）。
- ⚠️ 採用/不採用・最大地面が変わったら adopted_strategies.md の `PORTFOLIO_CHECK` 行（BASE_MAX / PILLARS）だけ更新する（hook は本行に自動追従）。

### C. 設計・実装ファイルを書く前（PreToolUse Write/Edit が順に全部かかる）
- **check_websearch_before_design_write**: 設計書 Write 前に直近60分で WebSearch3本/ソース種別2/WebFetch2本（足がかり探索）。未達でブロック。
- **require_spec_read_before_design**: cat_requirements/exchange_spec を Read 強制（設計を書く瞬間）。
- **require_instrument_read_before_impl**: eval_engine（計器）未読なら実装 Write をブロック。
- **doc_map_guard**: ledger/設計書への経緯・失敗の語をブロック。
- **forbid_fixed_value_tuning**: 固定値スイープをブロック（L-267）。
- **require_acceptance_before_impl**: scripts/priority_rebuild/*.py は、acceptance.md（TARGET一致＋深掘り4点＋DESIGN_CONTRACT）＋まこさん承認指紋（approve_impl）が無いと書けない。
- **block_uchikiri**: アジャイル放棄を表す語をブロック。

### D. python 実行の前（PreToolUse Bash）
- **require_precheck_before_score**: score.py を CLI 実行する前に precheck の PASS が要る。
- **require_design_contract_before_run**: 戦略スクリプトを実行する前に、設計書/acceptance.md の DESIGN_CONTRACT で実装を機械照合（verify_design_contract.py）→FAIL=実行ブロック。★設計↔実装照合はここ（詳細 §3）。
- **require_period_source**: priority_rebuild の .py を実行する前に、検証期間の境界（TRAIN_END/SC_START/SCORE_START/SCORE_END/SEAL_START/EMBARGO）を periods.py から取らず自前定義（pd.Timestamp リテラル・e34v1.TRAIN_END 等）していたらブロック。★期間の手打ち禁止＝期間ズレ根絶（periods.py が唯一の正本＝SSOT・審判 score.py の正本窓ゲート score_official と対・ledger E0.5・2026-06-18）。periods.py 自身は除外。限界＝正規表現ベース（別名はすり抜けうる・審判窓ゲート＋まこさんの目と併せて担保）。

### E. 審判 → 分析 → 記録（PostToolUse pdca_mark が旗を操作・Stop pdca_gate が未閉じをブロック）
pdca_mark は**コマンド名の正規表現**で検知する:
- 実験スクリプト実行（`strat_`/`train_`/`measure_`）→ need_score を立てる。
- **score.py / precheck.py 実行** → need_score を下ろし、need_report / need_analyze / need_analyze_report / need_ledger / need_5q / need_claim / need_next_step / **need_viz** を一括で立てる。
- report.py(--vs) → need_report / need_vs を下ろす。**＋採点CSV分の週次チャートPNG（results/priority_rebuild/viz/ に `<stem>_*.png`）が実在すれば need_viz を下ろす**（report.py M節が「トレード最多/最少・NET最大/最小」の4週を自動出力＝結果レポートと同時に画像を出す強制・M節が黙って失敗して PNG が無ければ旗が残り pdca_gate がブロック・まこさん 2026-06-21 強制化・番人メタ確認 pass）。
- analyze.py → need_analyze を下ろす。
- ledger.md 編集（5問＋**方針/狙い/目的**＋主張を全部含む）→ need_ledger / need_5q / need_claim を下ろす。**方針/狙い/目的**（2026-06-26 まこさん指示）＝改善内容の意図＝前の iter の何を受けて何を狙ってこの変更をしたか。next_step の改善アーク「狙い」列がこの ledger「方針」を引用元にする（CC の記憶要約禁止＝2026-06-26 妄想で狙いを書いた事案）。
- next_step.md 上書き（本筋/やってはいけない/出典/**改善アーク**/**狙い**/**内容**/**方法** を含む）→ need_next_step を下ろす。**内容/方法**（2026-06-26 まこさん指示）＝改善アークの各 iter に 狙い(目的) だけでなく 内容（動かしたレバー/機構）と 方法（どう検証・採否理由＝失敗の型）も残す＝次セッションが「何をして/どう検証して/なぜ不採用か」を見て同型の手を再提案しないため（goal_block「改善の経緯」列ゲートと対）。**改善アーク**（2026-06-26 まこさん指示）＝対象戦略の直近イテレーション系譜＋前提フラグ（nofloor ON/OFF 等）を表 or 箇条書きで残す＝次セッションが流れを理解した上で改善するため（goal_block「改善の経緯」と対）。**狙い**（2026-06-26）＝各 iter に「前の iter の何を受けて何を狙ってこの変更をしたか」を ledger の「方針」記述から引用（CC の記憶要約禁止＝意図が誤解なく引き継がれるため）。
- analysis_*.txt を Read → need_analyze_report を下ろす（read_log 経由）。
- pdca_gate（Stop）が need_* の残存でターン終了をブロック。

### F. セッション終了
pdca_gate が全旗クリアを確認するまで終了不可。

## 3. 設計↔実装照合の仕組みと限界（require_design_contract + verify_design_contract）

### 仕組み
実行前に設計書/acceptance の DESIGN_CONTRACT（fenced json）を読み、impl_file が実行 .py と一致したら照合:
- **(a) self_check_calls 方式**: `self_check_calls` の各識別子が実装ソースに**文字列として在るか**（`if c in src`）＝自己チェック配線の存在確認。
- **(b) must_combine 方式**: AST で symbol（例 range_ok）の代入右辺に設計要求成分が**連結されているか**。入口シグナルの成分欠落を検出。
- FAIL=実行ブロック（trades CSV すら作れない＝採点に進めない）。メタ確認 `verify_design_contract.py --self-test`。

### ★限界（正直に・2026-06-16 まこさん指摘）
- self_check_calls は「**識別子の存在**」だけ＝「acceptance のやること1〜N が**正しく**実装されたか1つずつ」ではない。
- AST 照合（must_combine）は**入口シグナルの成分連結**に効くが、Exit/サイズ/ゲート等の変更には使っていない（iter5a 建値撤退ゲートは self_check_calls のみ）。
- ＝**核心成分の「存在」は物理で守るが、「全項目の正しさ」は CC の照合＋score.py の数字＋非同型(Web Claude)レビューに依存**（cc_role §1.4.6.3）。複数CC Workflow の常時照合は同型バイアスで無効と判明し撤回済み。

## 4. ★抜け穴（命名規約から外れると強制を素通り・2026-06-16 事案）

pdca_mark / require_design_contract の検知は全部「**コマンド名・impl_file の正規表現**」依存。E35 はこの命名から外れて素通りした:

| 段階 | 期待する名前 | E35 の実体 | 結果 |
|---|---|---|---|
| 実験検知 | `strat_`/`train_`/`measure_` | e35_range_oscillation.py | need_score 立たず |
| 審判検知 | `score.py` / `precheck.py` を CLI 実行 | `import score; score.score(df)` を別名 score_e35_iter5a.py で | score.py にマッチせず |
| 分析解除 | `analyze.py` | e35_deep_analysis.py | need_analyze 下りる対象外 |

→ E35 は **審判→分析→記録の PDCA 強制が丸ごと素通り**（採点直後に分析なしで ledger を書けた＝実害が出た）。

### 塞ぎ方（hook 修正＝まこさん承認＋commit が要る）
- pdca_mark の正規表現を拡張: 実験に `e35_range_oscillation` ／ 審判に `score\.score\(` または `score_e3` ／ 分析に `_deep_analysis` を追加。これで E35 も審判→分析→記録の強制に乗る。

## 5. 新スクリプトの命名規約（強制に確実に乗せるため）
- **実験**スクリプト名は `strat_` / `train_` / `measure_` で始める。外れる名前（戦略本体に E35 のような連番名を付ける）を作るなら、pdca_mark に明示登録する。
- **審判**は `score.py` を CLI で通す。gate 外の `score.score(df)` を別名スクリプトで呼ぶなら、その呼び出しを pdca_mark の審判検知に登録する。
- **分析**は `analyze.py` を通す。専用分析（`*_deep_analysis.py` 等）を使うなら need_analyze / need_analyze_report の解除対象に登録する。
- **read-only 分析 probe**（/tmp・scratchpad に置く使い捨てスクリプト）は必ず `*_probe.py` または `*_deep_analysis.py` で命名する＝**require_probe_naming が物理強制**（python 実行時のみ・2026-06-26）。接尾辞なし（特に `e3N_*.py`）だと pdca_mark が「実験」と誤検知し need_score 旗を誤発火させる（2026-06-26 事案）。実戦略は scripts/priority_rebuild/ 配下に置き、probe を直下に作らない。
- **検証期間**（学習/捨て/採点/封印の境界）は `periods.py` から import する（自前で日付リテラルを書かない）。自前定義は require_period_source が実行前にブロック。表示文字列も periods から組み立てる（手打ちしない）。＝期間ズレ根絶の SSOT（ledger E0.5）。
- **使用パラメータ・ロジックのサイドカー**（2026-06-19）: 戦略は走行のたびに、出力する売買記録CSVの隣に `<stem>_params.json` を `params_sidecar.write_sidecar` で出す。中身＝その戦略で**実際に使った**指標/閾値/TP/SL/TimeExit/期間/サイズ ＋ **Entry/Exit ロジック（ルールの流れ・exit_reason）**。`report.py` 節0 が戦略名非依存で自動表示（E35 が手本・E36/E37 も同パターン）。read 専用メタ＝net 計算・審判に不関与。pdca_mark は `py_compile`（コンパイル確認）を実験/審判検知から除外（false trigger 防止・2026-06-18/19）。

---

## 改訂ルール
- hook の追加・修正・撤回があったら本書を更新（実体 settings.local.json / hooks/*.sh が正）。
- hook 修正は cc_role §1.4.6.2 に従い**まこさん明示承認＋git commit**で記録。
