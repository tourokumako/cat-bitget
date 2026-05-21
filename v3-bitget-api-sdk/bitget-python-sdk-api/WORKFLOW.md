# WORKFLOW.md — cat-bitget 作業フロー

---

## 🛑 2 大絶対規定（プロジェクト全期間で常に有効・各 Phase 着手前に必ず確認）

本プロジェクトには、Phase に依存せず常に守るべき 2 つの最大級の禁止事項がある。これらに違反した実装・成果物は、いかなる Phase 進行・指示書内容にも優先して無効とする。

### 1. Prime Directive — 本番運用で再現不可能な実装の絶対禁止
本番運用の推論時点 t において、その変数の値が因果的に確定済みで、かつ実際の取引システムから取得可能であるものだけを、計算式・判定式・採用ロジックに使用できる。
詳細: `.claude/rules/false_positive_incident_policy.md` §0-1
違反は同 §2 類型 A（look-ahead leak）として最重大インシデント扱い。

### 2. ポジション上限 0.12 BTC 合計厳守
任意の時点 t において、保有中の全ポジションの合計 BTC サイズが 0.12 BTC を超えてはならない。1 ポジあたりではなく合計上限。各ポジの配分は柔軟（強い combo に多く、弱い combo に少なく等）。
詳細: `.claude/rules/false_positive_incident_policy.md` §0-2
違反は同 §2 類型 H（運用上限逸脱）として最重大インシデント扱い。

各 Phase の着手前および完了報告時に、両規定への適合を verify すること。

---

> 過去版・歴史的記録: [archive/workflow/](archive/workflow/)
> - [WORKFLOW_20260427.md](archive/workflow/WORKFLOW_20260427.md) — 直前の Day 2/3 完了報告・本セッション総括・マスタープラン9本・古い Priority ステータス
> - [WORKFLOW_20260422.md](archive/workflow/WORKFLOW_20260422.md) — 2026-04-22 時点スナップショット
> - [WORKFLOW_reference.md](archive/workflow/WORKFLOW_reference.md) — $60/day達成の数学・参考資料

---

## 役割 + 行動原則

ClaudeはPM・PL・SE・プログラマの全役割を担う。

- 指示を待たず、自分で現状を把握して「次に何をすべきか」を先に提案する
- 仮説はデータで検証してから提示する（根拠なしの仮説は出さない）
- 設計判断は感覚で進めず必ず定量比較を経てから提案する（feedback_quantitative_comparison）
- GOを待つのは「実装・コマンド実行・コミット」のみ
- 目標（**月次 NET ≥ $1,900 全月クリア達成**）から常に逆算して行動する。目先の指標改善に満足しない（cc_role.md §1.0 整合・$60/day はデイリー参考値で判定基準ではない）
- 方向転換時は WORKFLOW のフェーズと照合してから提案する（脇道に逸れない）
- 議論が行き詰まった・同じ提案を繰り返している・直前2ターン同じ語彙の時は「思考フレーム/目標コミット 自己点検」を実行する（後述）
- **作業完了報告は 3点必須**（2026-05-08 追加）: ① 完了フラグ + ファイル名 / ② 結果中身のサマリー（数値・上位5-10件・次元保持）/ ③ ファイル提示（リンク）。「ファイルに書いた」だけでは報告完了とみなさない
- **成果物ファイル名の一意化ルール**（2026-05-14 追加・まこさん指摘）:
  - 比較・対照される成果物 (prerefit/postrefit・複数 k・複数 option・複数 Phase など) は、ファイル名そのものに識別子を含める。フォルダ名だけでの区別は禁止
  - NG: `ml_phase2_rerun_prerefit/net_quality_24combinations.csv` と `ml_phase2_rerun_postrefit/net_quality_24combinations.csv` (同名・フォルダ違い)
  - OK: `net_quality_24combinations_PREREFIT.csv` / `net_quality_24combinations_POSTREFIT.csv` (識別子をファイル名末尾に付与)
  - 理由: チャット添付時にフォルダ階層が失われ、同名ファイルの取り違えが発生するため (2026-05-14 セッション中に 3 回発生)
  - 適用範囲: **今後生成する全成果物**。既存ファイルは遡及リネーム不要だが、チャット提示時は識別子付きでリネームコピーして提示
- **公式判定 source の定義**（2026-05-14 追加・監査#8 必須3）:
  - Phase X の合否の公式 source は `results/.../phase{X}_summary.json` (スクリプト出力) のみ
  - 完了報告内の手計算・補完評価は「参考」表記とし、「公式」「公式判定」「公式記録」の語を使用しない
  - 完了報告には冒頭に「公式 source: results/.../phaseX_summary.json」を必ず明記する
  - 背景: 2026-05-14 監査#8 で「Phase 2 改訂後 spec PASS」が script 改修されないまま手計算で補完されていた事案を防止
- **完了報告必須証跡 8点**（2026-05-08 追加 / 5点目 2026-05-09 追加・L-162 / 7点目・8点目 2026-05-15 追加・false_positive_incident_policy.md §5A/B）:
  1. **コード総点検 grep 結果**（全件・"no matches"含む・関連スクリプト全部）
     - 4種の grep: ① TF endswith/startswith ② TFリスト固定値 ③ カテゴリ固定値 ④ 絞り込み処理（best 1/argmax/nlargest(1)）
  2. **数値の二重提示**（サマリー + 出典ファイル引用・行番号付き）
  3. **成果物ファイルの実体**（チャット側に届く形・パス + 行数 + 更新時刻）
  4. **実行ログ**（コマンド・開始時刻・終了時刻・所要時間・終了コード）
  5. **絞り込み示唆語彙の自己 grep 結果**（全件・"no matches"含む・チャット出力 + 報告 md ファイル対象）（L-162・2026-05-09 追加）
     - grep 語彙: 「採用候補」「効く/効かない」「重要」「優先」「不要」「切れる」「残せる」「除外して良い」「使える」「意味がある/ない」
     - 違反検出時: 数値 + 軸/カテゴリ間比較に表現を置き換えてから報告完了とする
     - 背景: L-159/L-160 を追加したのに 1 日で再発した事実は教訓追加の限界を示す。「頭で分かっていても漏れる」癖は手続きで矯正する（思考フレーム自己点検 L-136 と同じ思想）
  6. **個別組合せ/クラスタの train→test 変化表**（2026-05-14 追加・audit#9 懸念2）
     - 形式: 組合せ名 / train 値 / test 値 / 差 (pp) / test 件数
     - 適用: 組合せ比較・設計選択を含む完了報告に必須（Phase 4-b 系タスク等）
  7. **異常値スメルテスト結果**（false_positive_incident_policy.md §5A・2026-05-15 追加）
     - 以下 4 条件を全て確認した結果を1行で報告：① 勝率 / ② 月次 NET / ③ IS-OOS Sharpe 比 / ④ 最大 DD
     - いずれか 1 つでも ① > 70% / ② > $3,800 / ③ > 3 倍乖離 / ④ < 月次 NET の 10% に該当したら「合格」と書かず「**異常値・要調査**」と書く
  8. **全工程の未来参照 verify（変数の因果性宣言）**（false_positive_incident_policy.md §5B・2026-05-15 追加）
     - PnL・判定計算式（Entry / Exit / Replay 全工程）の入力変数を列挙し、「各変数が推論時点 t で因果的に存在するか」を 1 行ずつ宣言する
     - 変数名 grep だけでは名前変更で素通りするため、因果性の宣言が必須（例: `mfe_te[i]` が test_MFE_K12 を参照しているか確認）
  - 1つでも欠けたら完了とみなさない
  - 「総点検したから違反なし」を grep 結果なしに主張しない
  - 「やった」「完了」を実行ログなしに主張しない
  - 「絞り込み示唆語彙なし」を grep 結果なしに主張しない（L-162）
  - 「実は完了済み」を主張する場合は該当ターン番号と全文を再提示する
- **指示書のファイル保管義務**（2026-05-14 追加・まこさん複数回指摘）:
  - CC に指示書を発行する際は、チャットに投げ文を出すだけでなく、必ず「この指示書を `.claude/instructions/日付_タスク名.md` として保存し commit せよ」を CC 投げ文に含める
  - 目的: 後から「どのタスクでどんな指示書だったか」を参照できる状態を必ず作る
  - 三重化で担保: ① memory ② web_claude_self_check.md チェックA ③ 本ルール
  - 新規タスクの指示書を書く前に、CC に過去の同種指示書 (`.claude/instructions/` 配下) を見せてもらう、またはまこさんから添付を受け、フォーマット・粒度・前回の問いの立て方を確認してから書く

## 思考フレーム自己点検

**起動条件**（いずれか）:
- 同じ構造の提案を 2 ターン以上繰り返している
- まこさんから「視点が狭い」「同じこと言ってる」「それじゃない」と指摘された
- 自分の前ターンと現ターンの語彙がほぼ同じ

**手順**:
1. いまの議論が暗黙に前提にしているフレームを 3 つ言語化する
2. **いま自分が何の問題を解いているのか**を 1 行で書く（例: 「ML pipelineの部品最適化」「探索効率化」「研究の整理」「expert system設計」）
3. **試行単位とデプロイ単位を比較する**。試行で評価している単位（指標単体？レシピ全体？）が、最終的に運用に載る単位と一致するか確認する。ズレていれば最深層のフレーム不一致と判断
4. 各フレームに「これを外したらどう見えるか」を 1 行で書く
5. 外した結果、議論方向が変わるなら「前提を外して再考したい」と宣言してから進む

**禁則**:
- 「広く考えました」と主張する前にフレームを必ず言語化する
- 指摘されてから外すのを常態化させない（自分から起動する）
- **手順 2-3 をスキップして手順 1 だけで完了したと判断しない**（操作的フレーム3つ並べて満足する失敗パターン）

**背景**: Claude は文脈の語彙に引っ張られて与えられたフレーム内でしか動けなくなる癖がある。明示的に外す手続きを置く（2026-04-27 教訓）。**手順1だけでは「操作的な3フレーム」を挙げて深層フレームを温存する失敗あり**（例: 「1指標vs多指標」を3つ挙げても「問題はpipelineで解く」前提を外せない・2026-04-27 regime研究議論）。手順 2-3 で問題設定そのものとデプロイ単位を強制的に比較し、深層フレーム不一致を検出する。

## 目標コミット自己点検

**起動条件**（いずれか）:
- 自分の発言に「現実的には」「落とし所」「構造的に難しい」「記録する方が近道」が出た
- まこさんから「諦めるな」「コミット弱い」「目標から逃げてる」と指摘された
- 「月次 NET ≥ $1,900 全月クリア達成」を 5 ターン口に出していない
- 議論が「達成方法」から「達成できない理由の整理」にシフトしている

**手順**:
1. 直前の自分の発言を「月次 NET ≥ $1,900 全月クリア達成への前進 / 諦めの言い換え」で 2 値判定する
2. 後者なら撤回し「月次 NET ≥ $1,900 全月クリア達成に届かせるなら、ここから何ができるか」で書き直す
3. 「できない」と言いそうになったら「いつまでに / どの条件が揃えば / 何を試せば」の 3 点で具体化してから出す

**禁則**:
- 「現実的な落とし所」を出す前に月次 NET ≥ $1,900 全月クリア達成に届く案を最低 1 つ出す
- 認知バイアスや構造的制約の説明で 1 ターン丸ごと使わない（説明は 2 文以内）
- 目標を下げる方向の整理をこちらから提案しない

**背景**: Claude は「達成への思考」より「諦めを丁寧に言語化する思考」に流れやすい癖がある。思考フレーム自己点検（狭さ対策）と二段構えで引き戻す（2026-04-27 教訓）。

## ML pipeline 管理 (旧表記「Priority 再構築管理」)

> 🧊 priority_rebuild.md (旧 A-1〜D framework) は 2026-05-13 ML pipeline 切替で廃止・参照のみ。
> フォルダ名 `priority_rebuild/` は履歴的経緯で残置 (実体は ML pipeline Phase 0〜7 出力)。

ML pipeline (Phase 0〜7) の**仕様・合否基準・設計確定事項**の正本は以下の 4 ファイル:
- **[cc_ml_design_spec.md](cc_ml_design_spec.md)** — Phase 別設計仕様・合否基準・drift 対処方針
- **[WORKFLOW.md](WORKFLOW.md)** (本ファイル) — 現フェーズ + 次のタスク + セッション確定事項
- **[.claude/rules/phase_compliance_checklist.md](.claude/rules/phase_compliance_checklist.md)** — Phase 別着手前チェックリスト
- **[.claude/rules/cc_role.md](.claude/rules/cc_role.md)** — CC 役割定義・思考プロセス・対話プロトコル (2026-05-21 ML 設計担当 CC 移譲)

## シグナル管理

シグナル候補・検証実績は **`.claude/memory/signal_ledger.md`** が**唯一の正本**。
WORKFLOW.md にシグナル個別の状態を書かない（重複は不整合の元）。
セッション開始時・新規シグナル検証時・Priority 化時は signal_ledger.md を読み、更新する。
（regime × 方向マッピング部分は凍結中・参照のみ）

## regime 研究（🧊 凍結中）

regime 判定研究は 2026-05-11 に凍結。`.claude/memory/regime_research.md` §0 に凍結ステータスを明記済。
**新規調査・新規試作・自己点検の起動は禁止**。素材（1,432 指標列・k=2 探索フレーム）の参照のみ可。
再開条件: Priority 再構築フェーズで「regime label が必要」と判定された場合のみ。

---

## Step 0: セッション開始プロトコル（省略禁止）

```
⓪ [Step 0 ⓪] **WORKFLOW.md の Step 0 ②/③ 記述を読み上げる前に実装/直近コミットで grep verify する** (L-180):
   - 「現フェーズ」「段階」名称 → 直近実行スクリプト名 + git log で確認
   - 「前提条件」「評価軸」「分割方法」各項目 → 該当スクリプト grep で 1 件ずつ確認
   - 「完了済み」「合格」記述 → leak チェック等で無効化されてないか確認
   - 不一致あれば作業着手前に提示して GO 待ち
   - 違反検出時: ドキュメント側を実装準拠に修正してから ① 以降を継続
   → 1 件でも未確認/不一致があれば、作業着手前に提示して GO 待ち
   ※ 設計転換コミット直後セッションでは feedback_design_transition_grep_sweep.md (L-181・命令) を再読
① 合格ライン 月次 ≥ $1,900/月 − 凍結ベースライン $370/月 = 不足 $1,530/月（5.1倍ギャップ）
   ※ デイリー $60 は目安・日次絶対下限ではない・判定は月次のみ・一次ソース: MEMORY/project_goal.md
② 現フェーズ確認（ML pipeline Phase 0〜7・Phase 0=ラベル再生成 (14 ラベル独立) / Phase 1=LightGBM 学習 / Phase 2=精度判定 / Phase 3-a/3-b=ハイパラ調整 / Phase 4-a=クラスタリング / Phase 4-b=Exit 設計 / Phase 5/5-b/5-c=Replay / Phase 5-d=POS_SIZE 再計算 / Phase 5-e=Funding 控除 / Phase 6-a/6-b=本テスト / Phase 7-a=Bot 統合準備 / Phase 7-b〜e=Bot 実装/デモ/本番 のどこか明示・旧表記「Priority 再構築」）
   ※ 2026-05-13 leak 修正後は Phase 0 (ラベル再生成) から再開・Phase 1〜7-a 旧成果は無効
③ 当該 Phase の前提条件（K 窓 1h/2h/4h/8h・LONG/SHORT 同時・期間分割: train 2021-04〜2024-12 + valid 末尾10% + 仮テスト 2025 + 本テスト 2026 Q1・評価軸: train RMSE / Entry predicted MFE/MAE 比 / Exit pnl_median）を再確認
④ [Step 0 D] Phase 完了後の月次 NET ≥ $1,900 全月クリア達成可能性: YES / NO / 試算未済
   ※ leak フリー再学習中 (Phase 0〜5 完了前) は「試算未済 (Phase 5-c Replay で初めて判定)」と書いてよい
   ※ この 1 行が出るまで提案・分析を開始しない
   ※ 「$60/day」はデイリー参考値 (月次÷30 の目安)・判定基準ではない (cc_role.md §1.0 / CLAUDE.md §目標 整合)
⑤ [Step 0 E] 着手前の目的整合性 3 項目チェック（L-166）:
   - データ粒度: 検証対象と一致しているか
   - データカバレッジ: 判断分岐に十分なサンプル数か
   - 直接性: 目的を直接測れる手段か（代理指標は要警戒）
   → 1 つでも NO/不明なら、作業着手前に提示して GO 待ち
⑥ [Step 0 F] **ML 系作業 (学習・推論・特徴量生成) を含む場合は leak 4 点チェック必須** (L-179・~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md):
   - 特徴量計算コードの grep 静的検査 (`.shift(-` / `center=True` / `j+1, j+2` 等の未来 index 参照)
   - データ流入経路 verify (is_X / fractal / pivot の使用箇所で `j ≤ i-K` フィルタが**実装で**適用されているか)
   - 学習データの timestamp range 確認 (train が test 期間に侵入していないか)
   - 1 ラベル目の学習完了直後に feature_importance_top20 を即時 review
   → 1 つでも未確認/異常があれば、作業着手前に提示して GO 待ち
   → コードコメントの「look-ahead 防止」を信頼しない。実装で verify
⑦ [Step 0 G] 前セッションで議論が行き詰まった or 同じ提案を繰り返した記録があるか確認。
   ある場合: 思考フレーム/目標コミット 自己点検を 1 回実行してから ⑧ に進む
⑧ 今セッションのタスクを優先順位付きで提示 → STOP
```

---

## PMレビュー（オンデマンド）

**起動タイミング**: 「目標に届く気がしない」「方向性が正しいか確信が持てない」「N セッション改善が止まった」と感じたとき。

**起動方法**: ユーザーが「PMレビューして」または `/pm-review` と入力する。

**実行手順**:
1. WORKFLOW.md の現状（Current/Gap/アクティブ Priority 実績）を読む
2. `.claude/pm_review_template.md` のテンプレートに現在値を埋める
3. **Plan タイプのサブエージェント**としてスポーン（コールドスタート・独立評価）
4. 結果を [PM REVIEW] 形式で提示 → ユーザーの判断を待つ

> サブエージェントは実装提案を出さない。方向性判定のみ。

## 監査エージェント（オンデマンド）

**起動タイミング**: 「本当にこの方向で大丈夫か？」「見落としがある気がする」と感じたとき。PM レビュー後に続けて呼ぶことも可。

**起動方法**: ユーザーが「監査して」または `/audit` と入力する。

**実行手順**:
1. WORKFLOW.md の現状と直近の Replay 結果を読む
2. PM レビュー結果が直前にある場合はそれもコンテキストに含める
3. `.claude/auditor_template.md` を読み込み、**統計学・リスク管理・認知バイアス・ソフトウェア工学**の外部基準で評価する（観点は状況に応じて 2〜3 個に絞る）
4. 結果を出力フォーマットで提示 → ユーザーの判断を待つ

> 監査エージェントはコードを書かない・実行しない。外部基準からの指摘のみ。最終判断はまこさん。

---

## 設計思想（2026-05-21 改訂16 反映・cc_role.md / false_positive_incident_policy §0-2 整合）

> 旧「Priority 構築方針 / 実装方針」(2026-05-11 大方針転換時) は「Priority」用語が手動 Priority (P1-P24) と混同される問題があったため、2026-05-21 ML 設計担当 CC 移譲を機に **ML pipeline 用語**で再整理。実質方針は同じ (regime 凍結 / 1432 指標網羅 / cluster 並立 / 月次 NET 評価)。

### ML pipeline 構築方針（2026-05-11 大方針転換 → 2026-05-21 改訂16）

- **regime 判定先行は廃止**（精度天井 + 情報密度不足 + 時間軸ズレで凍結・regime_research.md §0）
- 5m bar × **1,432 指標 + 業界カタログ拡張** × 未来 MFE/MAE pct (14 ラベル独立学習・対称性活用) で **Entry/Exit 規則を網羅探索**して ML pipeline (Phase 0〜7) を構築
- 既存手動 Priority (P1-P24) は **スタートライン参照のみ** (cc_role.md §1.7・手動 Priority は ML が当然到達すべき最低限の構成・「ベンチマーク」ではない・到達後が本題)
- **複数 cluster / combo を並立** させてリスク分散 (cluster 別最適 Exit・combo 別 cap・LONG/SHORT 動的配分)
- **Entry/Exit 両側学習方法改善** (handoff v19 §0.14・新 Path A 改 = Entry Binary Classification + Direction Multiclass + Exit Triple Barrier multiclass + Meta-labeling + Walk-forward CV) を Layer 1 並行実装で議論中
- 最終検証: 365d Replay で 月次 NET 評価（仮テスト 2025 + 本テスト 2026 Q1 単一 chronological holdout・**月次 NET ≥ $1,900 全月クリア** = 合格ライン）

### 実装方針

- **5m 足ベース** + MTF 特徴量 (5m/15m/30m/1h/4h/1d・1w/1M Layer 2 検討・1m/3m は CLAUDE.md §⛔ 提案禁止リスト) を Entry 条件に組込み可
- **ポジションサイズ上限: 合計 0.12 BTC 厳守**（false_positive_incident_policy §0-2 第二絶対規定・**1 ポジあたりではなく合計上限**・任意の時点 t で `sum(active_position_btc) ≤ 0.12` を実装で verify）
- 上限内での **combo 別 / cluster 別 / 予測強度別配分は柔軟** (例: 強い combo に 0.04 BTC・弱い combo に 0.01 BTC・cap=N なら 1 pos = 0.12/N BTC)
- per-position サイズは **0.000167 BTC 以上** (BTC=$30k stress test 通過・最小注文 0.0001 BTC + 最小注文額 5 USDT verify・learning_design_v3 制約セット)
- 複数 combo / cluster 並立の目的: **リスク分散**。詰まったら「新 combo / cluster 追加」であり「サイズ増加ではない」（CLAUDE.md §⛔「ポジションサイズ増加でスケール」禁止）
- 時間帯フィルター (D-δ) は **個別 combo 最適化では禁止**。Layer 2 統合フェーズで実施 (learning_design_v3 23 軸振り分け表 D-δ)

---

## ファイル配置規則（恒久・直下平置き禁止）

### scripts/
直下に `.py` を置かない。必ず以下のサブフォルダのいずれかに配置:

| サブフォルダ | 用途 |
|---|---|
| `dashboard/`        | ダッシュボード配信・JSON生成 |
| `labels/`           | 教師ラベル基盤 |
| `data/`             | 外部データ取得・テスト |
| `regime/`           | regime 試作・検証スクリプト（**凍結**・参照のみ） |
| `priority_rebuild/` | Priority 再構築フェーズ ML pipeline (Phase 0=build_labels / Phase 1-3=run_lgbm_* / Phase 4=run_phase4_* / Phase 5=run_phase5* / Phase 6=本テスト / Phase 7=Bot 統合) |
| `signal_research/`  | シグナル候補検証（`signals/` サブモジュール含む） |
| `grid_search/`      | レシピ・パラメータ探索 |
| `hmm/`              | HMM 系（凍結中・参照のみ） |

新カテゴリが必要な場合は本セクションに追加してから作成する。

### results/
直下にデータファイルを置かない。出力先は必ずサブフォルダ:

| サブフォルダ | 用途 |
|---|---|
| `replay/`              | Replay 出力（CSV / summary JSON） |
| `phase_hmm/`           | HMM 系出力（凍結） |
| `regime_research/`     | regime 評価出力（凍結・参照のみ） |
| `priority_rebuild/`    | Priority 再構築フェーズ ML pipeline 出力（labels_mfe_mae_pct_*.parquet / ml_phase{1,3_a,3_b,4_a,4_b,5,5_b,5_c,5_d,5_e,6_b}/ / ml_artifacts/ / archive/ 等）|
| `recipe_search/`       | レシピ探索出力 |
| `grid_search/`         | グリッドサーチ結果 |
| `vshape_design/`       | v13/v14 V字検出仕様 + 出力（凍結） |
| `spike_analysis*/`     | スパイク検出（凍結） |
| `regime_prototype/`    | v1 試作（凍結） |
| `regime_label_analysis/` | 教師ラベル分布（凍結・素材として参照）|
| `charts/`              | 共通チャート |

新スクリプトの書き出し先は `OUT_DIR = REPO_ROOT / "results" / "<カテゴリ>"` で必ずサブフォルダ指定する。

---

## 改善サイクル（旧 Priority 最適化フェーズ用・🧊 凍結中・参照のみ）

> ⚠️ このセクションは**旧フロー**（regime → Priority 振り分け前提）。
> 2026-05-11 大方針転換で凍結。Priority 再構築フェーズの改善サイクルは ML pipeline Phase 0〜7 ([現フェーズ section](#-現在のフェーズ2026-05-13-改訂2ml-パイプライン-leak-修正完了--phase-1-再学習待ち) 参照)。
> 既存 Priority 解体時の参考・グリッドサーチ実装の文法参考として残置。

**Step 1〜10**: 旧フロー（$/regime-day 単位・regime_switch=ON 前提）。**新規実行禁止**。
詳細は git history（commit fa38ec2 以前）で参照可能。

---

## 新規Priority設計フロー（P1/P21等・新規追加時）

1. 必要貢献額を逆算してシグナルの最大期待値が届くか確認する（届かなければ設計変更）
2. シグナルエッジをフィルターなし・タイトなTP/SLで先に検証する（勝率60%未満は却下）
3. Entry特性を言語化してからExitをゼロから設計する（既存流用禁止）
4. 実装 → Replay → 必要貢献額を満たすか判定

---

## 🔴 現在のフェーズ（2026-05-22 改訂19・**Layer 配分逆転 (B') 確定** + 業界知識統合 + 3 層併存閾値設計）

> **【現在の正本ブロック・改訂19・2026-05-22 セッション末】**
>
> ### 本セッション (handoff v21 受領後) 完了事項
>
> #### 1. ナレッジベース v3 確定 (technical_analysis_knowledge_base.md・1691 行)
> - v1 (450 行) → v2 (1528 行) → v3 (1691 行)
> - WebSearch 54 件 + Gemini 見解 2 件統合
> - §A-§D 個別辞典 (RSI/MACD/ADX/ATR/BB/Stoch/Ichimoku/Fib/VP/Pivot/RCI/Williams + キャンドル + Wyckoff + SMC + AFML)
> - **§I 閾値設計論** (4 大分類: 自己実現的 / 計算式由来 / 業界経験 / Adaptive + DSR + 3 層併存設計)
> - §F 出典 69 件 URL
>
> #### 2. Phase 0 改修指示書 v3.1 確定 (576 行・Triple Barrier ラベル同時生成)
> - 5 ファイル同時改修 (pruned_column_list + 4 .py)
> - 約 2316-3016 列 (1432 既存 + 800-1500 新規特徴量 + 28 既存ラベル + **28 Triple Barrier ラベル**)
> - L-196 メンテフラグ削除 (L-181 違反訂正)
> - 業界 5 系統分類 + 3 層併存閾値設計
> - mlfinlab パッケージ依存追加
>
> #### 3. Phase 1 学習方法再設計指示書 v1 新規作成 (429 行・Layer 配分逆転 (B') 確定版)
> - **6 案並列**: 案 a (14 ラベル RMSE) + 案 b (Binary) + 案 c (Multiclass) + **案 d (Ranking LambdaRank)** + **案 e (Triple Barrier multiclass)** + **案 f (Meta-Labeling 2 段階)**
> - **Walk-forward Purged K-Fold 5 fold** (mlfinlab.cross_validation・Layer 3 → Layer 1 前倒し)
> - **DSR (Deflated Sharpe Ratio・Bailey + Lopez de Prado 2014) 採用** (selection bias 補正)
> - **合格基準 5 指標数値** (entropy lift > 10% / TP Precision > 0.5 / Direction Accuracy > 0.55 / Simulated PnL 8+ 月プラス + 年 $500 / DSR > 1.0)
> - **Layer 3 投入条件厳格化** (6 案ベストでも 5 指標未達 → 即 Layer 3)
> - リソース計画 (3 並列・30-45 GB・約 20 時間)
>
> #### 4. learning_design_v4 → v5 改訂 (377 行・+41 行)
> - §3 振り分け表 B-13/B-14/B-15 Layer 1 前倒し明示
> - §4 「Layer 1 (Layer 配分逆転・2026-05-22 v5)」セクション新規追加
> - §6 Layer 3 タスク縮小
> - §11 着手フロー大幅修正
>
> #### 5. cc_ml_design_spec §1.5.1 追加 (399 行・+19 行)
> - Phase 1 合格基準 5 指標数値正式化
> - §1.6.1 メタルール整合 (実行後緩和禁止)
>
> ### CC 同型バイアス再演 9 件 (本セッション・累積 36+ 件)
>
> handoff v21 §0.27 累積 18 件 + 本セッション 9 件 = **累積 36+ 件**。詳細は lessons_active.md L-201 + handoff v22 §0.30 参照。
>
> ### 次セッション CC 優先順位 (handoff v22 §3 参照)
>
> 1. **優先 1 (最優先)**: §3.1 **Phase 0 改修指示書 v3.1 実装着手** (5 ファイル同時改修 + Triple Barrier ラベル + L-196 メンテフラグ削除・約 4-6 時間)
> 2. **優先 2**: §3.2 **Phase 1 学習方法再設計指示書 v1 実装着手** (6 案並列 + Purged K-Fold 5 fold + DSR・約 3-4 週間)
> 3. **優先 3 (将来)**: Phase 4-b 設計再 audit + DSR + Adaptive 閾値最適化 / Phase 7-d 着手前 maxMarketOrderQty paper trading test

---

> ### 🧊 改訂18 ブロック (履歴・参照用)

> **【旧正本ブロック・改訂18・2026-05-22 セッション末】**
>
> ### 本セッション (handoff v20 受領後) 完了事項
>
> #### 1. 未 commit 整理 (handoff v19 §2 残課題)
> - `6510231`: Phase 0/1-a/1-b/1-c smoke 実行ログ 7 件
> - `91317c5`: priority_rebuild scripts 3 件 (Phase 0 集計 + option5 v2/v3)
> - `c16005f`: 過去 audits + 指示書 一括 (audit15/16/19 + 13 指示書 + modified 3)
> - `9638c26`: audit17 phase_a §0.13 #1 違反成果物 (記録として保持)
>
> #### 2. §3.0 cc_ml_design_spec §4 改訂 (前提タスク・learning_design_v4 §8)
> - `7872559`: cc_ml_design_spec.md §4 全面改訂 + pm_review_template.md L35 旧表記訂正 + handoff_to_web_claude.md (凍結) 注記追加
> - 「1 回のサイズ 固定 0.12 BTC」→「合計 0.12 BTC 厳守」+ cap カウント = **合算カウント** 確定 (B-8 / D-ζ.10)
> - 全エントリー時点で `sum(active_position_btc) ≤ 0.12` verify 実装義務
>
> #### 3. phase_flow_v4_with_recovery.md 全面書き直し (試作 7 回 → 確定版)
> - `6d06425`: phase_flow_v4 新規作成 (888 行) + V3 archive 移動
> - `f540c1e`: A 案修正反映 (888 → 977 行・+89 行)
>   - phase_compliance_checklist.md (222 行) + false_positive_incident_policy.md (225 行) 全文 view → 整合性総点検 → A 案 8 件修正
>
> ### CC 同型バイアス再演 8 件 (本セッション・累積 18 件)
>
> handoff v19 §0.13 (5 件) + handoff v20 §0.26 (5 件) + 本セッション (8 件) = **累積 18 件**。詳細は lessons_active.md L-200 + handoff v21 §0 参照。
>
> ### 次セッション CC 優先順位 (handoff v21 §3 参照)
>
> 1. **優先 1 (最優先)**: §3.1 Phase 0 改修指示書発注 (build_labels_pct.py 改修・1432 → 約 2000-2500 列・約 3-6 時間)
> 2. **優先 2**: §3.2 Phase 1 並列学習 3 案 (約 1-2 週間) + CP2 分岐判定
> 3. **優先 3 (将来)**: Phase 2 着手前 smoothing 設計再 audit / Phase 7-d 着手前 maxMarketOrderQty paper trading test

---

> ### 🧊 改訂17 ブロック (履歴・参照用)

> **【旧正本ブロック・改訂17・2026-05-21 セッション末】**
>
> ### 本セッション後半 (handoff v19 受領後) 完了事項
>
> #### 1. 書類整理 11 件 (handoff v20 §0.17)
> - A-a/b/c: cc_ml_design_spec.md (作成者表記 + Phase 1 Step 4 + §10 報告フロー)
> - A-2: `.claude/rules/cc_role.md` **新規作成 366 行** (CC 役割定義・web_claude_role v3 反転)
> - A-1: web_claude_role.md v3.1 (冒頭に降格注記)
> - A-d: auditor_template.md (L24 同型バイアス警告 + 14 ラベル化)
> - A-e: memory/handoff_to_web_claude.md (凍結マーク追加)
> - B-1: web_claude_self_check.md (CC 兼用注記)
> - B-2: CLAUDE.md (必読リスト 4 件追加 + 14 ラベル化 + 目標表記 cc_role §1.0 整合)
> - C-1: 本 WORKFLOW.md 改訂16
> - F-1: MEMORY.md index + role_transition_20260521.md 新規 (memory 配下・git 管理外)
> - C-3: phase_compliance_checklist.md verify only (旧記述 0 hit ✅)
>
> #### 2. WORKFLOW.md スリム化 (handoff v20 §0.18)
> - 887 → **373 行 (-58%)**
> - 履歴 538 行を `archive/workflow/WORKFLOW_archive_20260521.md` に全文移動
>
> #### 3. §設計思想 ML pipeline 用語化 (handoff v20 §0.19)
> - L217 「Priority 構築方針 / 実装方針」(P1-P24 ゼロから再設計) → ML pipeline 用語 + **合計 0.12 BTC 厳守** (false_positive §0-2) 明示
> - CLAUDE.md L88/L97 + WORKFLOW.md L124/L163 関連 3 箇所も整理
>
> #### 4. 目標表記 cc_role §1.0 整合 (handoff v20 §0.20)
> - CLAUDE.md L40/L13/L149 + WORKFLOW.md L38/L109-118/L164/L519/L839 (合計 8 箇所)
> - 目標 $60/day → **月次 NET ≥ $1,900 全月クリア達成** + 「あらゆる手段」「全力でコミット」中身明記
>
> #### 5. learning_design_v4.md 新規作成 (handoff v20 §0.21/§0.22)
> - 23 軸 CSV 全文 view 完了で V3 全面再構築
> - 構成: 23 軸 → 5 学習タスク (T1-T5) 分解 + Layer 1〜3 割り付け + §X.10 明示
> - learning_design_v3.md → `.claude/memory/archive/learning_design_v3_20260521.md` archive
> - V4 = 296 行 (初版)
>
> #### 6. ChatGPT → Claude 監査モード `/audit` 訂正 (handoff v20 §0.23)
> - まこさん明示「私チャッピーに課金してない・Claude の監査モードでやるしかない」
> - 3 ファイル 11 箇所訂正 (現役 / 未来用記述のみ・過去歴史記録は保持)
>
> #### 7. auditor_template.md 本セッション変更全反映 (handoff v20 §0.24)
> - 15 箇所修正 (473 → 520 行・+47 行)
> - Phase 構成更新 (14 ラベル / k=3 / Phase 2 = §1.6 4 指標 / 合計 0.12 BTC 厳守)
> - 完了報告必須証跡 5 点 → 8 点 (false_positive §5A/B 整合)
> - CC 同型バイアス 7 件全列挙
> - 参照ファイルリスト更新 (cc_role / learning_design_v4 / CSV 1962 行 / handoff v19 等)
>
> #### 8. 監査 #20 実施 → V4.1 へ 5 箇所修正 (handoff v20 §0.25)
> - Claude 監査モード `/audit` で general-purpose subagent 起動
> - 3 件懸念指摘:
>   - 懸念 1: entropy lift 数値誤記 (旧 2.2% → 実測 **6.04%**・計算式 `1 − 1.0322/ln(3) = 0.0604`・false_positive §2 類型 E/G リスク)
>   - 懸念 2: §X.10 = Layer 3 教条主義 (CSV B-13.10 両論併記・handoff v19 §0.13 #4 再演)
>   - 懸念 3: Entry 学習根本問題温存 (handoff v19 §0.13 #5 再演・Lopez de Prado *AFML* Ch.3 推奨閾値 < 10% は meta-labeling 投入域)
> - 5 箇所修正反映:
>   1. §9 entropy lift 2.2% → 6.04% 訂正
>   2. §9「§X.10 確定 Layer 3 に従う」削除 + 判断軸「数値根拠 + Lopez de Prado 閾値」変更
>   3. §4 Layer 1 に **Entry Binary Classification + Direction Multiclass を 14 ラベル独立 RMSE と Layer 1 並列追加** (Layer 3 → Layer 1 昇格)
>   4. §11 着手フロー CP2 に分岐判定追加 (3 案物理証跡対比 → 採用案 or Layer 3 投入)
>   5. §10/§12 改訂履歴に監査 #20 反映 5 件追加
> - V4 = 296 → **V4.1 = 336 行 (+40 行)**
>
> #### 9. handoff v20 作成 (本セッション末)
> - `.claude/instructions/handoff_to_cc_v20_session_20260521.md` 新規 (宛先 CC)
> - 本セッション全成果物 + CC 同型バイアス再演 5 件 + 次セッション CC 優先順位を記録
>
> ### 次セッション CC 優先順位 (handoff v20 §3 参照)
>
> 1. **優先 1 (前提タスク)**: cc_ml_design_spec §4 改訂 (「1 回」→「合計」明文化 + B-8 cap カウント方法明文化)
> 2. **優先 2 (Phase 0 改修)**: build_labels_pct.py 改修指示書発注 (8 指標 + まこさん発振系 + 1w/1M MTF + Fractional differentiation + PCA + パラメータ並列展開・1432 → 約 2000-2500 列・約 3-6 時間) + CP1 Claude 監査モード `/audit` 経由独立検証
> 3. **優先 3 (Layer 1 着手)**: Phase 1 並列学習 (Entry Binary + Direction Multiclass + 14 ラベル独立 RMSE 3 案・約 1 週間) + CP2 物理証跡対比 → 採用案 or Layer 3 投入分岐
> 4. **優先 4 (将来)**: Phase 2 着手前 smoothing 設計再 audit (Sharpe maximizing 復活検討) / Phase 7-d 着手前 maxMarketOrderQty paper trading test
>
> ### CC 同型バイアス再演 5 件記録 (handoff v20 §0.26)
>
> handoff v19 §0.13 (1 週間前指摘 5 件) + cc_role.md §1.4 (7 件定義) を受けたにもかかわらず、本セッションでも再演:
> - #3 確認質問乱発 (AskUserQuestion 3 ターン連続)
> - #4 教条主義 (V4 §9「§X.10 = Layer 3」)
> - #5 まこさん発言翻訳 (Entry 学習駄目 → 特徴量拡張)
> - 計算ミス (entropy lift 2.2% 誤記)
> - 専門用語括弧書き違反 (まこさんから「文章がよくわからない」指摘)
>
> → **ルール追加だけでは止まらない実証**。次セッション CC は本ブロックを最優先で警戒。

---

> ### 🧊 改訂16 ブロック (履歴・参照用)

> **【現在の正本ブロック・改訂16・2026-05-21 セッション末】**
>
> 以下が現状の状態:
>
> ### Phase 進捗 (本セッション 2026-05-21 完了事項)
> - **Phase 0 v3 spec sweep 完了** (commit `22e75a9`): cc_ml_design_spec.md / phase_compliance_checklist.md / ml_axis_catalog.md の「16/28 ラベル → 14 ラベル独立学習」機械反映 + Funding 0.01% 固定 → median baseline (audit#19 確定値) 反映
> - **Phase 1-a 14 ラベル LightGBM RMSE 学習完了** (commit `9d99dbb`): 67 分・rmse_ratio 14/14 ✅・ただし top1 = atr14_pct__5m 33-65% dominance (ボラ予測のみ機能)
> - **phase_flow_v3_with_recovery 保管** (commit `57f92d1`): Phase 1-b 以降の全 Phase フロー + 失敗時改善フロー
> - **Phase 1-b 簡易 PnL チェック → NO-GO** (commit `2f01a98`): SL hit が TP の 1.78 倍・time order 未学習・12 ヶ月中 6+ ヶ月プラス基準未達
> - **audit#18 起票 → A 案切替** (commit `5890622`): ChatGPT 独立検証で「PnL/Sharpe maximizing custom objective は barrier hit non-smooth で grad/hess 未定義」確定 → Triple Barrier 3 クラス multiclass + EV フィルタ に切替・Sharpe maximizing は Phase 2 以降 smoothing 設計後に再 audit・learning_design_v3.md §B-15 + phase_flow_v3 §2 同期書き換え
> - **Phase 1-c Triple Barrier multiclass smoke 実行 → NO-GO** (未 commit): K=12 単独・15 分 45 秒・logloss 1.0322 ≥ 0.95 (uninformed baseline log(3)≈1.10 から entropy lift 2.2%) / TP Precision 0.2364 ≤ 0.4 → Entry 学習問題が示唆された
>
> ### ML 設計担当 Web Claude → CC 完全移譲 (handoff v18/v19 でまこさん決定)
> - **2026-05-21 移譲**: Web Claude が 2026-05-15〜2026-05-19 で構造的バイアス由来のミス (視野狭窄・押し付け・確認質問乱発・デザイン責任転送) を 4 回繰り返したため、まこさん決定
> - **Web Claude = 機械照合担当** (文書整合性 / grep sweep / 旧記述検出のみ)
> - **CC = 実装担当 + ML 設計担当兼務**
> - **新規ガバナンス文書**: `.claude/rules/cc_role.md` (CC 役割定義・v1) / `.claude/rules/web_claude_role.md` v3.1 (降格注記追加)
> - **handoff v19** (`.claude/instructions/handoff_to_cc_v19_session_20260521.md`): 宛先 CC・§0.13 CC 同型バイアス 5 件記録・§0.14 Entry/Exit 両側学習方法改善議論到達点・§0.15 未確定 4 件
>
> ### Entry/Exit 両側学習方法改善議論 (handoff v19 §0.14・新 Path A 改)
> 観察された事実 (Phase 1-a/1-b/1-c 物理証跡 3 連続):
> 1. 1432 指標で **ボラ予測のみ機能** (top1 = atr14_pct__5m 33-65% dominance)
> 2. SL hit が TP の 1.78 倍 (Phase 1-b・時間順序未学習)
> 3. multiclass logloss が entropy baseline からほぼ改善なし (lift 2.2%・Phase 1-c)
>
> → Entry 学習問題が示唆 (Exit 側のみではない)
>
> CC 提案 = **新 Path A 改** (Entry Binary Classification + Direction Multiclass + Exit Triple Barrier + Meta-labeling + Walk-forward CV) を Layer 1 で並行実装 (4-5 週想定)。まこさん判断待ち (handoff v19 §0.15)。
>
> ### 2026-05-21 セッション後半 書類整理 11 件 (本セッション完了)
> - **A グループ (現役正本不整合)**: cc_ml_design_spec.md (作成者表記 + Phase 1 Step 4 + §10 報告フロー) / auditor_template.md (同型バイアス警告 + 戦略リード + Phase 1 表 + L461) / .claude/memory/handoff_to_web_claude.md (凍結マーク追加)
> - **B グループ (役割定義)**: web_claude_role.md (v3.1 冒頭ブロック追加) / cc_role.md (新規 366 行)
> - **C グループ (セルフチェック)**: web_claude_self_check.md (冒頭注記・CC 兼用ルール) / CLAUDE.md (セッション開始時必読リスト更新)
> - **D グループ (進捗反映)**: 本ブロック (WORKFLOW.md §🔴 現在のフェーズ 改訂16) / CLAUDE.md L161 (16 ラベル → 14 ラベル) / auditor_template.md 14 ラベル化
> - **F グループ (memory)**: role_transition_20260521.md 新規作成 + MEMORY.md index 追加
> - **G グループ (grep sweep)**: 「Web Claude が ML 設計」関連記述 55 件検出 → カテゴリ分け (現役正本 5 件のみ整理 + 過去指示書 / handoff / 監査依頼書は歴史的記録として保持)
>
> ### 未 commit 成果物 10 ファイル (handoff v19 §2・本セッション末で commit 判断)
> - Phase 1-c smoke 関連 5 ファイル (commit 推奨)
> - 軸監査タスク 2 ファイル (§0.13 #1 違反成果物・白紙化検討中・まこさん判断)
> - handoff v17/v18/v19 + 本セッション書類整理 11 件 (通常 commit)
>
> ### 次セッション CC 優先順位 (handoff v19 §3 / §7 参照)
> 1. 優先 1: handoff v19 §0.15 未確定 4 件のうち、まこさん指示で着手項目を確定
>    - #1 新 Path A 改 (Entry/Exit 両側修正) で進めるか
>    - #2 Step 1 (Entry Binary・1 週) から段階実装で良いか
>    - #3 ChatGPT 独立検証を新 Path A 改着手前に通すか
>    - #4 未 commit 成果物の commit 範囲
> 2. 優先 2: 新 Path A 改採用なら指示書発注 → Entry Binary Classification smoke 実装
> 3. 優先 3 (将来): Phase 2 着手前 smoothing 設計再 audit (Sharpe maximizing 復活検討・learning_design_v3 §B-15 修正履歴 #13)
>
> ---
> ### 🧊 改訂15 ブロック以前 (履歴・archive 移動済・参照用)
>
> 改訂15 以前の旧現フェーズブロック (改訂13/14/15/7) / 旧次のタスク (Phase 4-a 改訂23・Phase 2 = 238 行) / 試行禁止リスト / 旧 Priority パラメータ凍結 / Replay コマンド (旧フロー) / 引き継ぎリソース (旧版) は **2026-05-21 スリム化** で [archive/workflow/WORKFLOW_archive_20260521.md](archive/workflow/WORKFLOW_archive_20260521.md) (538 行) に全文保存。過去指示書 / handoff / 監査依頼書からの行番号参照 (例: 元 L353/L365/L546-560/L648) は archive ファイル内で対応 (元 L350 = archive L1・以降 L350+x = archive L1+x)。

---

## 📚 履歴セクション スリム化記録 (2026-05-21)

本ファイル WORKFLOW.md は 2026-05-21 にスリム化:
- **旧**: 887 行 (履歴 538 行 = 60% 占有)
- **新**: 約 360 行 (現役のみ・履歴は archive)
- **削減効果**: -60%

スリム化理由 (CC 判断 2026-05-21):
1. 読了ゲート負荷大 (cc_role.md §1.6 / web_claude_self_check.md 読了ゲート)
2. 改訂16 で上書きされた旧現フェーズや Phase 2 時点の旧タスクが残置
3. 次の改訂17/18 で更に膨張する構造を回避

archive ファイル内訳:
| 範囲 (archive 内) | 行数 | 内容 |
|---|---|---|
| L1-L74 | 74 | 🔴 旧現フェーズ表記 (改訂13/14/15) |
| L75-L192 | 118 | 🔴 旧現フェーズ表記 (改訂7) |
| L193-L225 | 33 | 2026-05-14 セッション成果物一覧 |
| L226-L463 | 238 | 🧊 旧次のタスク (Phase 4-a 改訂23・Phase 2) |
| L464-L538 | 75 | 試行禁止リスト / 旧 Priority パラメータ凍結 / Replay コマンド / 引き継ぎリソース (旧版) |
