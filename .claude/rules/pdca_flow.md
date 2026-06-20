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

## 1. hook 一覧（23本・登録は settings.local.json）

| hook | タイミング | matcher | 役割 |
|---|---|---|---|
| verify_handoff_paths | SessionStart | — | 引き継ぎパスの存在チェック（ずれ検出） |
| force_read_ml_design | SessionStart | — | 必読・6軸ゲート・保管ルール等を表示 |
| reset_read_log | SessionStart | — | read_log をリセット（前セッションの読了を持ち越さない） |
| show_latest_state | SessionStart | — | next_step.md 全文表示（起点） |
| require_read_before_work | PreToolUse | Bash/Edit/Write/MultiEdit | 必読2本＋目標逆算ブロックが済むまで作業ブロック |
| record_read | PostToolUse | Read | Read した .md を read_log.txt に記録 |
| check_websearch_before_design_write | PreToolUse | Write/Edit | 設計書 Write 前に直近60分の検索ベースアップを要求 |
| enforce_search_quality | PreToolUse | WebSearch | 検索品質（12語以内・allowed_domains 指定） |
| track_search_fetch / update_websearch_marker | PostToolUse | WebSearch/WebFetch | search_log・marker 記録 |
| require_spec_read_before_design | PreToolUse | Write/Edit | 設計書を書く瞬間に cat_requirements/exchange_spec を Read 強制 |
| show_budget_before_design | PreToolUse | Write/Edit | 設計/改善案（acceptance.md / *_design.md）を書く瞬間に「予算0.12は全採用戦略の共有枠」＋採用台帳を1セッション1回表示（exit2 で1回ブロック→再実行で通す・SessionStart 表示は効果ないため提案の瞬間に出す・2026-06-20・marker は reset_read_log が消す） |
| require_instrument_read_before_impl | PreToolUse | Write/Edit | 実装を書く前に eval_engine（計器）を Read 強制 |
| doc_map_guard | PreToolUse | Write/Edit | ledger/設計書に経緯・失敗の語を書くのをブロック（置き場所違反） |
| forbid_fixed_value_tuning | PreToolUse | Write/Edit | 固定値スイープ（採点窓で最良値選定）をブロック（L-267） |
| require_acceptance_before_impl | PreToolUse | Write/Edit | scripts/priority_rebuild/*.py を書く前に acceptance＋承認を要求 |
| block_uchikiri | PreToolUse | Write/Edit | アジャイル放棄を表す語をブロック（語一覧は実体参照） |
| require_precheck_before_score | PreToolUse | Bash | score.py を CLI 実行する前に precheck PASS を要求 |
| require_design_contract_before_run | PreToolUse | Bash | 戦略実行の前に DESIGN_CONTRACT で実装を機械照合 |
| require_period_source | PreToolUse | Bash | priority_rebuild の .py 実行前に、期間境界(TRAIN_END/SC_START/SCORE_START/SCORE_END/SEAL_START/EMBARGO)が periods.py 由来でない自前定義ならブロック（期間ズレ根絶・E0.5・2026-06-18） |
| pdca_mark | PostToolUse | Bash/Edit/Write | コマンド名で審判/分析/記録の旗を立てる/下ろす（--smoke/--no-score/--selftest は審判検知から除外・2026-06-18） |
| pdca_gate | Stop | — | 旗の残存でターン終了をブロック |
| approve_impl | （まこさんが実行） | — | acceptance の承認指紋を立てる |
| require_workflow_for_impl | （未登録） | — | 撤回済み（cc_role §1.4.6.3・複数CC Workflow 常時必須を廃止） |

## 2. 段階別フロー（順を追って）

### A. セッション開始（SessionStart）
4本（verify_handoff_paths / force_read_ml_design / reset_read_log / show_latest_state）が表示・準備。強制はまだ無い。次の作業で B が効く。

### B. 最初の Bash/Edit/Write の前（必読＋目標逆算）
- **require_read_before_work**（PreToolUse）: 必読2本（WORKFLOW.md / ledger.md）を Read tool で開く＋`goal_block.md` に目標逆算の必須見出しを書くまで、全 Bash/Edit/Write をブロック。
- 解除: read_log に2本が載り、goal_block の必須見出しが揃う。記録は record_read（PostToolUse Read）。

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
- **score.py / precheck.py 実行** → need_score を下ろし、need_report / need_analyze / need_analyze_report / need_ledger / need_5q / need_claim / need_next_step を一括で立てる。
- report.py(--vs) → need_report / need_vs を下ろす。
- analyze.py → need_analyze を下ろす。
- ledger.md 編集（5問＋主張を全部含む）→ need_ledger / need_5q / need_claim を下ろす。
- next_step.md 上書き（本筋/やってはいけない/出典 を含む）→ need_next_step を下ろす。
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
- **検証期間**（学習/捨て/採点/封印の境界）は `periods.py` から import する（自前で日付リテラルを書かない）。自前定義は require_period_source が実行前にブロック。表示文字列も periods から組み立てる（手打ちしない）。＝期間ズレ根絶の SSOT（ledger E0.5）。
- **使用パラメータ・ロジックのサイドカー**（2026-06-19）: 戦略は走行のたびに、出力する売買記録CSVの隣に `<stem>_params.json` を `params_sidecar.write_sidecar` で出す。中身＝その戦略で**実際に使った**指標/閾値/TP/SL/TimeExit/期間/サイズ ＋ **Entry/Exit ロジック（ルールの流れ・exit_reason）**。`report.py` 節0 が戦略名非依存で自動表示（E35 が手本・E36/E37 も同パターン）。read 専用メタ＝net 計算・審判に不関与。pdca_mark は `py_compile`（コンパイル確認）を実験/審判検知から除外（false trigger 防止・2026-06-18/19）。

---

## 改訂ルール
- hook の追加・修正・撤回があったら本書を更新（実体 settings.local.json / hooks/*.sh が正）。
- hook 修正は cc_role §1.4.6.2 に従い**まこさん明示承認＋git commit**で記録。
