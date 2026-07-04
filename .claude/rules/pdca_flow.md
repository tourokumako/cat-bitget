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

## 1. hook 一覧（29本・登録は settings.local.json）

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
| require_analysis_before_proposal | PreToolUse | Write/Edit | 【分析フェーズ】を物理強制（採点非依存・2026-06-24）。**A 着手ゲート（分析KB読了）と B 完了ゲート（9見出し）を別タイミングで効かせる（2026-06-27 まこさん指摘で順序是正＝分析KB読了は分析の前提なので、分析の後に出す提案 acceptance を書く瞬間では遅い）**: ① **A 着手＝analysis_block.md を書く瞬間（分析の着手）に強制**＝分析KB(trade_analysis_methods_kb)/analysis_playbook §2/対象 report_・analysis_ を read_log で確認（未読なら analysis_block すら書けない＝分析を始める前にKBを読む）。② **B 完了＝改善提案/設計（acceptance.md / *_design.md）を書く瞬間に強制**＝`.claude/state/analysis_block.md` の必須**9見出し**（A も保険で再掲＝二重に守る）（前後比較/両窓/fat-tail/MAE/較正[予測確率]/3分類/問5/経緯照合[E番号引用必須]/**⑨巻き込み検証**）。**⑨巻き込み検証（2026-06-26 追加・本丸）＝切る/早切り/Exit 系レバーは、そのルールが勝ち玉（特に fat-tail）に当たる量を数字で出す。損玉だけ見て天井を語る分析手法の欠陥を塞ぐ（2026-06-26 時間切れ損玉だけ切り出し「取り逃し +$2,624」と誤推定・同じ含み益シグナルが勝ち282玉 +$3,401 に当たるのを見落とした事案＝iter10/DYING_CUT 再演手前）。Exit/切る でない提案は「該当なし」と明記**。pdca_gate が採点後しか分析を強制しない穴（採点なし既存データ分析=強制ゼロ）を塞ぐ。**③ B 完了ゲートに改善案生成ルール STEP3/3.5/4 を追加（2026-06-28 まこさん承認・番人9/9 pass・`.claude/state/improvement_plan.md`）＝STEP3 タグ付け＆重なり判定（軸A出血容疑＋軸B=N10両窓再現の分離指標を必ず使う＝「知ってる犯人だけ追う近視眼」封じ）／STEP3.5 発散（切り口5つ以上・各に N番号出典＝無難な1案収束封じ）／STEP4 収束3案（守り/攻め/構造・各〔玉数増減〕〔net増減=学習窓〕〔犠牲〕＝消去案逃げ封じ）＋禁止形式「閾値X→Y」「○帯を除外」検出（分離指標を木に渡す形に直す・L-267）。STEP1観察/STEP2要因は probe前ゲートA(require_probe_naming)で先に強制済** |
| block_uchikiri | PreToolUse | Write/Edit | アジャイル放棄を表す語をブロック（語一覧は実体参照） |
| block_premature_giveup | PreToolUse | Write/Edit | **中身の打ち切り/事前却下**（「期待値が低い/筋が悪い/やる意味が薄い/これ以上は無理/構造的に閉じた/採用に至らない見込み」等）を decision artifact（ledger/next_step/forward_action/acceptance）に書く時、**①** `.claude/state/exhaustion_check.md`（試した分析角度／未試行の分析角度＋「未試行: なし」宣言）が埋まっている **かつ ②** その編集に「いい面/活かせる点/部分採用/別用途/転用/次にどう活かすか」の併記がある、の両方を満たさないとブロック（2026-06-28 まこさん「ちゃんと強制して」「駄目な面で即却下・握りつぶし禁止・いい面も見出せ」）。①＝block_uchikiri の表面語をすり抜ける「中身で諦める」（やらない理由で潰す・受け身・案が浅い）を塞ぎ「思いつく限りの分析をしつくした上でのみ "できない" と言ってよい」を物理化。②＝駄目な面だけ見て即却下・握りつぶしを禁止し、却下時もいい面/活かし方を併記させる。⛔「まこさんの案を全部検証したか」は問わない（機嫌取りは侮辱・まこさん明示却下）。番人 ①6/6＋②4/4 pass |
| enforce_role_criteria | PreToolUse | Write/Edit | **役割忘れ防止（2026-06-29 まこさん承認・番人8/8 pass）**＝acceptance.md を書く瞬間に、TARGET スクリプト token（e3N）の役割を adopted_strategies.md の `ROLE_CHECK` マーカーから引き、役割に反する案をブロック。**scalp（e37）**＝F 受け入れに「件数/日を上げる（高頻度＝役割）」基準が必須＋「件数±0/減・頻度は次 iter」の尻すぼみ容認文言を禁止／**daytrade（e36）**＝「スキャル化/高頻度化」等 役割を壊す文言を禁止／未定義役割はスルー。背景＝CC が E37=スキャル（件数が役割）を忘れ件数±0 の floor 単独案を出し ⑩戦略整合に矛盾を書きながら「頻度は次 iter」と尻すぼみ容認した事案（E34 iter0/3 再演）。hook に戦略名を焼かず ROLE_CHECK マーカー追従（戦略増は1行追加・PORTFOLIO_CHECK と同型）。 |
| enforce_pdca_chain | PreToolUse | Write/Edit | **【最深刻・思考連結の物理化】PDCA全戦略共通（2026-07-02 まこさん指示「PDCAとすべての思考がつながる仕組み」・番人11/11 pass）**＝Check(analysis_block)→Action(improvement_plan)→Plan(acceptance) の"継ぎ目"で前段の結論を引き継がないとブロック。① analysis_block＝件数(トレード数)を per-trade より先に(§0①)・前後比較・原因3分類 ② improvement_plan＝件数起点＋多角発散(異手法2種)＋末尾に `<!-- LEVER: 動かす値 -->` を1つ確定＋next_step(過去失敗)読了 ③ **acceptance＝improvement_plan の LEVER を"逐語で"引き継がないとブロック（接続②＝分析→設計の連結）**。背景＝CC が分析(件数失格)を強制されてもその結論を無視し別の思いつきで設計した「思考が繋がらない」(2026-07-02・L-316)。限界＝逐語を引いても中身は形骸化可＝連結が本物かは score.py＋まこさんの目。 |
| enforce_e37_pdca | PreToolUse | Write/Edit | **E37=スキャル 特有のみ（2026-07-02・番人11/11 pass・共通は enforce_pdca_chain）**＝内容に e37 を含む時だけ発火。① analysis_block＝件数がスキャル頻度(役割=一級基準)を満たすか判定(失格/達成・§1.2.1) ② acceptance＝⑦手数料を超えるTP幅(maker往復)・⑨短保有(分単位・数分＝保有4h再演防止)・⑫5分足設定 RSI9/MTF(technical_kb §4/§5・RSI14/MTFなし 再演防止)。**Entry/Exit セットは戦術の一つ＝常時強制しない**（別々調整が良い局面もある）。**＋③ improvement_plan（Action 段・2026-07-04 まこさん承認「強制実装する」・番人17/17 pass）＝スキャル一級基準4点（件数/日の目標・逆算／短保有 分単位／手数料超えの幅／5分足設定 RSI9/MTF）を「設計の入力制約」として改善案の収束段階で照合強制。背景＝acceptance まで待つと案がデイトレ部品流用のまま収束する（2026-07-04 E36 の箱 BOX_N=100 流用案が scalp 照合なしでチャット即興提案された事案＝L-322 翻訳・矮小化の再演）**。**＋④ KB 読了ゲート（2026-07-04 まこさん承認・番人5/5 pass）＝E37 の improvement_plan/acceptance を書く瞬間、レンジ×スキャルの知識正本 range_scalping_kb.md（bitget-python-sdk-api/.claude/memory/・§7 に §1.2.1↔業界標準↔実装の対応表）が read_log に無ければブロック。背景＝スキャル/レンジの業界標準を知らずに設計し10日間堂々巡り（まこさん「レンジでスキャルで稼ぐ方法をインプットして・覚えたことをどこかに書いとけ」）＝KB に書いても次の CC が読まない穴を物理で塞ぐ** |
| enforce_strategy_anchor | PreToolUse | Write/Edit | **【戦略係留・全戦略汎用】acceptance.md を書く瞬間に「戦略の指定（担当局面・方向・頻度）との照合」を物理強制（2026-07-04 まこさん承認・番人9/9 pass・本体は enforce_strategy_anchor.py＝hook の python 別ファイル規約）**。台帳 adopted_strategies の `STRATEGY_ANCHOR` マーカー（＝cat_requirements §1.2.1 の機械可読形・例 e37=range,short_only,scalp）から TARGET 戦略の指定を引き、①マーカー逐語の再掲 ②局面ゲート識別子 GATE_IDENT=（入口を担当局面の判定で制約する列/関数）③方向機構識別子 SIDE_IDENT=（short_only/long_only の時のみ）の宣言＋**識別子の DESIGN_CONTRACT 登録**（→ require_design_contract_before_run が実行前に実装ソースと機械照合）を要求。「レンジ判定なし」「暗黙に学ぶ」等の逃げ文言はブロック。未定義 token・局面 none・方向 both はスルー。背景＝E37 が両側化・レンジ判定撤去・教師すり替えの5段階ドリフトで §1.2.1（ショートのみ・レンジ）違反のまま8イテレーション走った事案（ledger ARC11〜23・L-322）＝改善アーク/enforce_pdca_chain の「前 iter との連結」だけでは鎖全体の戦略からの漂流を検出できない穴を「戦略への係留」で塞ぐ。頻度役割は既存 enforce_role_criteria が担当（重複させない）。**＋経緯の係留（2026-07-04 追加）＝対象戦略の ledger 直近 ARC エントリの iter 名の逐語引用を必須**（ledger 必読が部分読で通る穴＝今日の事案の温床を塞ぐ・番人 15/15 pass）。**＋improvement_plan（Action 段）への前倒し係留（2026-07-04 同日・まこさん「強制実装する」・番人17/17 pass）＝improvement_plan.md を書く瞬間にも軽量検査（★戦略照合 見出し＋アンカー逐語再掲＋局面/方向/頻度の照合行3つ＋逃げ文言ブロック・token 検出は大文字 E37 表記も非区別）。重い検査（GATE_IDENT/SIDE_IDENT/DESIGN_CONTRACT/ARC 逐語）は acceptance 段のみ＝重複させない。背景＝acceptance の網の手前（改善案収束・チャット即興提案）で戦略から漂流した事案（2026-07-04＝E37 に E36 デイトレ箱の流用案が scalp 照合なしで出た）＝「書き写し（goal_block 引用）を照合の代わりにする」穴を、照合行の物理強制で塞ぐ**。限界＝識別子の形骸配線は見抜けない（score.py＋まこさんの目）。 |
| require_leak_annotation | PreToolUse | Write/Edit | **H2 leak パターンの書き込み時ゲート（2026-07-04 まこさん承認・番人 pass・本体 .py 別ファイル）**＝scripts/priority_rebuild/*.py に未来参照の典型（`.shift(-`・`center=True`）を含む行を書く瞬間、行内に `# H2OK: <理由>` が無ければブロック＝**全未来参照サイトを書く瞬間に因果性宣言させる**（false_positive §0-1 関所B の書き込み時強制・H2 が実装者の自己 assert 頼みだった穴の縮小）。build_labels*／archive／priority_rebuild 外は対象外。既存戦略は該当0件を確認済（既存を壊さない）。限界＝パターン網羅でない（rolling 窓ずれ等は検出外＝関所B・score.py が引き続き担保）。 |
| hook_health_check | SessionStart | — | **hook 無言死の検出（2026-07-04 まこさん承認・表示専用 exit 0）**＝①登録 .sh の実在・実行権限 ②hooks/*.py 全部の py_compile（構文死＝pdca_mark 2026-06-29〜07-03 無言死事案の型） ③state/*_error.log の非空（fail-open で握りつぶした実行時エラーの可視化）。初回実走で既存 require_tag_for_experiment.sh の実行権限欠落を検出・是正（2026-07-04）。 |
| require_precheck_before_score | PreToolUse | Bash | score.py を CLI 実行する前に precheck PASS を要求 |
| require_design_contract_before_run | PreToolUse | Bash | 戦略実行の前に DESIGN_CONTRACT で実装を機械照合 |
| require_period_source | PreToolUse | Bash | priority_rebuild の .py 実行前に、期間境界(TRAIN_END/SC_START/SCORE_START/SCORE_END/SEAL_START/EMBARGO)が periods.py 由来でない自前定義ならブロック（期間ズレ根絶・E0.5・2026-06-18） |
| require_direct_csv_for_analysis | PreToolUse | Bash | report.py/analyze.py の分析対象（第1引数）が archive/ 配下ならブロック（2026-06-24）。＝最新実験が archive に押し出された＝実験→分析の順序ミスを物理検出（実験は1回 --tag→直下で分析→2本目の前に済ます）。意図的な過去再分析のみ ANALYZE_ARCHIVE_OK=1 で通す |
| require_probe_naming | PreToolUse | Bash | /tmp・scratchpad から **python で走らせる** .py が `*_probe.py` / `*_deep_analysis.py` 命名でないとブロック（2026-06-26）。＝read-only 分析スクリプトの命名規約（§5）を物理化。背景＝接尾辞なし e3N_*.py 分析を pdca_mark が「実験」と誤検知し need_score 旗を誤発火させた事案。ls/mv/rm/cat は通す（python 実行時のみ＝改名・削除は可能）。**＋正しい命名の probe 実行時に「疑似シミュ＝あたり付け専用・出た数値を設計の固定値/採否根拠にしない・採否は実エンジン両窓 score.py」を必ず表示（2026-06-26 まこさん承認・使う瞬間に錨）**。**＋probe前ゲートA（2026-06-28 まこさん承認・番人9/9 pass）＝probe(`*_probe.py`)を走らせる前に「対象の report_/analysis_ を read_log で全文読了済み ＋ `.claude/state/improvement_plan.md` に STEP1観察（良い点≥3[各$]・最も黒字1行・問題点≥3[各$・金額順]）」が無ければブロック。背景＝前回データ(report/analysis)を読まず probe を量産し N10 を再発見した隙間(2026-06-28 事案)を物理的に塞ぐ。require_analysis_before_proposal の着手ゲートは acceptance/analysis_block を書く瞬間にしか発火せず probe(Bash)から始めると素通りした穴を、probe 実行(Bash)で発火する本 hook で塞ぐ**。**＋probe前ゲートB（2026-07-04 まこさん承認「強制実装する」・番人17/17 pass）＝走らせる probe の basename が improvement_plan に事前記載され、その記載行に戦略制約との対応（＝§1.2.1 のどの制約[局面/方向/頻度/保有/幅/件数]の成立確認か）が書かれていないとブロック＝計画にない probe は走らせられない・probe は「戦略の制約の成立を測る道具」を物理化。背景＝probe の検証設計が戦略に沿うかを問う場所が無く、前セッションの慣性（be フロンティア等）の検証を戦略照合なしに続けられた（2026-07-04 まこさん指摘）** |
| require_tag_for_experiment | PreToolUse | Bash | 戦略 .py（e3N_/strat_/measure_）を出力モードで **--tag 無し実行**するとブロック（2026-06-29 まこさん承認）。＝実験は必ず `--tag` で `_<tag>_<NNN>` 連番（§3.1）を物理化。タグ無しの安定名は**採用済み base 専用**（採用は結果＝score.py 両窓を見てから決まる＝採用前の新戦略に番号なし/"base" 名を pre-declare しない）。テスト/非出力（--smoke/--diagnostic/--selftest/--no-score/py_compile/--help）・判定器（score/precheck/report/analyze/plot）・probe/deep_analysis は対象外（regex 非該当）。採用 base の再走など正当なタグ無しは `TAGLESS_OK=1` で通す。背景＝新戦略 E37 をタグ無しで `_5m_base`（番号なし・"base" 入り）で出した命名規則違反（§3.1 旧文を誤読＋規則を捏造＋物理強制が無かった）。メタ確認 11/11 pass |
| pdca_mark | PostToolUse | Bash/Edit/Write | コマンド名で審判/分析/記録の旗を立てる/下ろす（--smoke/--no-score/--selftest は審判検知から除外・2026-06-18）。**2026-06-29 改善（まこさん「毎回フラグ解除で時間・誤発火」）: ①引用符内（文字列リテラル）を除去した cmd_x で実行検知＝git commit メッセージ・echo・printf テスト等でスクリプト名が言及されただけの誤発火を防ぐ ②need_5q/need_claim は編集 payload でなく ledger の【最新エントリ】(最後の ## セクション)に6見出し＋方針/狙い＋主張 が在るかで判定＝複数編集で書いても通る（6問を1編集に詰める制約を撤廃）**。**⚠️2026-07-03 復旧（まこさん指示で調査・修正）: 上記①の re.sub 行のシングルクォートが bash の python3 -c '…' 引用を破壊し、2026-06-29 以降 python が毎回 SyntaxError→末尾 exit 0 が握りつぶし＝旗管理が全停止していた（無言死・発見の契機＝実験後に report/analyze/png が強制されず素通り）。対策＝python 本体を hooks/pdca_mark.py へ分離（-c クォート問題の構造的根絶・今後 hook の python は -c 埋め込み禁止で別ファイル化）＋stderr を state/pdca_mark_error.log へ記録（無言死の可視化）。ロジック不変・番人11/11 pass** |
| pdca_gate | Stop | — | 旗の残存でターン終了をブロック。**2026-06-29 改善: Stop 時に file-state self-heal＝need_5q/need_claim（最新 ledger エントリの6見出し＋方針＋主張）・need_next_step（4見出し＋ARC_TABLE hash 一致）を実体ファイルの中身で最終判定し、在れば旗をクリアして通す（編集の形・gen が Bash で書いた・誤発火 等の機械的事情に依存しない）。番人＝問見出し/方針 を欠くと維持・ARC 表改ざんで hash 不一致＝維持（弱体化なし）** |
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
- next_step.md 上書き（本筋/やってはいけない/出典/**改善アーク** を含む ＋ **改善アーク表が gen 生成＝ARC_TABLE_START hash=H が表本文の sha256 と一致**）→ need_next_step を下ろす。**改善アーク自動生成（2026-06-27 まこさん指示「全列を改ざんできないように」）**＝改善アーク表は `gen_improvement_arc.py --write` が **ARC マーカー（ledger/acceptance・git tamper-evident）＋ score.py（結果/採点窓数字＝改造禁止 H13＝改ざん不可）** から自動生成し next_step の `<!-- ARC_TABLE_START hash=H -->`〜`<!-- ARC_TABLE_END -->` に書く。**CC は改善アークを手書きしない**＝手書き/改ざんすると hash 不一致で pdca_mark が旗を下ろさない（番人＝改ざん→ブロック確認済）。各 iter の 狙い/内容/方法/前提/採否ラベルは ARC マーカーが源（CC の記憶要約・狙い内容の取り違えを構造的に排除）。今後 iter は acceptance に ARC マーカーを入れ、approve_impl が承認時に `.claude/ratchet/acceptance_archive/<iter>.md`（git 永続・指紋保護）へ凍結保存し gen が優先参照（過去 iter は ledger フォールバック）。
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
- **分析**は `analyze.py` を通す。**⚠️2026-07-04 改訂（まこさん承認）: `*_deep_analysis.py`/`*_probe.py` は need_analyze を下ろさない**＝§0前後比較＋N4ドリフトの中身検査を通る汎用 analyze.py だけが分析完了（deep_analysis 経由で前後比較を飛ばす抜け道を閉鎖）。deep_analysis は補助分析として使う。
- **実験の検知は `e[0-9][0-9]_` に一般化済（2026-07-04）**＝E40 番台以降の新戦略も自動で審判強制に乗る（旧 e3N 固定＝素通りの穴を縮小）。
- **read-only 分析 probe**（/tmp・scratchpad に置く使い捨てスクリプト）は必ず `*_probe.py` または `*_deep_analysis.py` で命名する＝**require_probe_naming が物理強制**（python 実行時のみ・2026-06-26）。接尾辞なし（特に `e3N_*.py`）だと pdca_mark が「実験」と誤検知し need_score 旗を誤発火させる（2026-06-26 事案）。実戦略は scripts/priority_rebuild/ 配下に置き、probe を直下に作らない。
- **検証期間**（学習/捨て/採点/封印の境界）は `periods.py` から import する（自前で日付リテラルを書かない）。自前定義は require_period_source が実行前にブロック。表示文字列も periods から組み立てる（手打ちしない）。＝期間ズレ根絶の SSOT（ledger E0.5）。
- **使用パラメータ・ロジックのサイドカー**（2026-06-19）: 戦略は走行のたびに、出力する売買記録CSVの隣に `<stem>_params.json` を `params_sidecar.write_sidecar` で出す。中身＝その戦略で**実際に使った**指標/閾値/TP/SL/TimeExit/期間/サイズ ＋ **Entry/Exit ロジック（ルールの流れ・exit_reason）**。`report.py` 節0 が戦略名非依存で自動表示（E35 が手本・E36/E37 も同パターン）。read 専用メタ＝net 計算・審判に不関与。pdca_mark は `py_compile`（コンパイル確認）を実験/審判検知から除外（false trigger 防止・2026-06-18/19）。

---

## 6. 将来の段（定義のみ・強制は該当フェーズ到達時に設計・2026-07-04 まこさん確認）

今の PDCA マップはバックテストの個別戦略最適化で閉じている。**目標（月 net ≥$1,900・本番で出す数字）に届くには下の2段が将来必要**＝ここに段として定義しておく（次の CC が「単独 net の足し算＝届く」と誤読しない足場）。**今の個別最適化の段階では強制しない**（まこさん方針 2026-07-04＝各レジームの複数戦略がある程度最適化されてから）。

### 6.1 統合・最終調整段（V9 型・全戦略を1つに組み込む）
- 各局面の戦略（E32b/E36/E37/E28/上げ柱…）がある程度最適化されたら、**全戦略を1つの決め手（V9 のような構造）に組み込んで最終調整**する。
- この段で初めて審判するもの: ①**合算 cap ≤0.12**（単独 CSV の cap は個別戦略の話・本番は全戦略合算＝H1/§6.1） ②**同方向の食い合い**（E36/E35-SHORT が E32b と予算を奪い合う分＝additive か） ③**合算 net が全月 $1,900 以上か**（単独 net の素朴な足し算は未検証の見積り＝台帳の注意書き）。
- 強制の設計（合算採点スクリプト・hook）はこの段に入る時にまこさんと決める。

### 6.2 本番移行段（バックテスト→ライブ BOT の関所）
- 統合の合算採点を通った後、本番に出す前の関所: ①**offline=online 一致**（同じ入力でバックテスト実装とライブ BOT が同じ判断をするか・cat_requirements §4.2・V9 期の verify_ml_inference 相当を E系 pipeline に接続） ②**demo（paptrading）→本番の段階移行**（§4.5・H14＝ALLOW_LIVE_ORDERS/paper_trading はユーザーのみ変更） ③レート制限・発注仕様の照合（exchange_spec）。
- 強制の設計はこの段に入る時にまこさんと決める。バックテストの勝ちが本番に運ばれる保証はこの2段で初めて閉じる。

---

## 改訂ルール
- hook の追加・修正・撤回があったら本書を更新（実体 settings.local.json / hooks/*.sh が正）。
- hook 修正は cc_role §1.4.6.2 に従い**まこさん明示承認＋git commit**で記録。
