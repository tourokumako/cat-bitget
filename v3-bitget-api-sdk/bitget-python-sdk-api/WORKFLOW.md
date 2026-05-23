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

## 🔴 現在のフェーズ（2026-05-23 改訂29・**Step I-3.1〜I-3.5 完走 (順次実行) + CP4 監査 CONDITIONAL NO-GO + 全 8 組合せ 0/16 ALL PASS**・案 W+V+Critical-1+Critical-2 採用 vs 案 X 直行のまこさん cold head 判断が次タスク）

> **【現在の正本ブロック・改訂29・2026-05-23 セッション末（10 時間越え長丁場・改訂28 同日続編）】**
>
> ### 本セッション (改訂28 同日続編・2026-05-23 07:35 〜 22:00) 完了事項
>
> #### 1. Step I-3.1 tp_hit_classifier --full 完走 (3 並列 → 1 並列に切替・10 時間 13 分)
> - 当初 P1+P2+P3 3 並列で起動 → 各プロセス RSS 8 GB → 16GB マシン物理 RAM 超過 → swap 42 GB thrashing 発生 (L-211 別側面・L-212a 候補)
> - 2 並列も全 UN ステート → 全 kill → swap 自動縮小 (43 GB → 2 GB)
> - P1 単独 (K=12,24・4 組合せ × 3 fold) 308 分 → P2 単独 (K=48・2 組合せ × 3 fold) 149 分 → P3 単独 (K=96・2 組合せ × 3 fold) 151 分
> - 累計 608 分 = 10 時間 13 分 (3 並列理論 2-3 時間想定 → 約 4 倍コスト)
> - **スクリプト判定 5/8 PASS** (K12_SHORT + K24_LONG + K48_LONG + K48_SHORT + K96_LONG・AUC 0.78-0.88 全件大幅クリア・Brier 0.07-0.20 全件クリア・Calib 一部 0.13-0.21 で SHORT 側に集中)
> - 公式 source: `results/priority_rebuild/ml_phase1_v5/_tp_hit_classifier_p{1,2,3}/tp_hit_classifier_summary_train_2021_2024.json`
>
> #### 2. Step I-3.3 case_a_v2 --full 完走 (P1/P2/P3 順次・各 1 分以下・LightGBM 再学習なし)
> - P1 (K=12,24) 54 秒・P2 (K=48) 42 秒・P3 (K=96) 89 秒 = 計約 3 分 (handoff v29 推定 30-60 分の 1/60)
> - P1+P2 = 関所 A セーフ (anomaly_smell_detected: False・6/6 組合せ)
> - **P3 = 関所 A ② ヒット 2 件** (K96_LONG fixed_tp max year=$218,126 月次相当 $18,177 / K96_SHORT fixed_tp max year=$256,206 月次相当 $21,350・合格ライン $1,900 の 9.5-11.2 倍)
> - L-208 Step H「6/8 ヒット 44 倍最悪」と比較すると **2/8 ヒット 11 倍最悪に大幅改善** (3 重楽観仮定除去の効果実証)
> - 公式 source: `results/priority_rebuild/ml_phase1_v5/_case_a_v2_p{1,2,3}/case_a_v2_summary_*.json`
>
> #### 3. Step I-3.4 merge_step_i_summaries.py + §4.1 v5.1 判定完了
> - 公式 source: [phase1_v5_step_i_summary_merged.json](results/priority_rebuild/ml_phase1_v5/_step_i_merged/phase1_v5_step_i_summary_merged.json)
> - **fixed_tp ALL PASS: 0/8** / **time_exit ALL PASS: 0/8** = **全 8 組合せ 0/16 ALL PASS** ❌
> - `meets_6plus_any_method: False` / 撤退ライン文言「6+ 組合せ ALL PASS 未達 → 案 X (Layer 3) or 案 Z (案 b-f) — まこさんレビュー必須」適用
> - 失格理由: 全 fold で Sim PnL 赤字 ($-200K 〜 $-300K/年・time_exit でも $-22K 〜 -41K) → sim_pnl_pass=false → ALL fail
> - 追加発覚: dsr.py 9 件 warning (`sigma_SR denominator non-positive (SR = -2×10¹⁵ 等)`・L-207 同型・L-212b 候補・time_exit returns 定数化との相互作用 edge case)
>
> #### 4. Step I-3.5 CP4 監査 (Plan サブエージェント独立評価) 完了
> - **監査結論: CONDITIONAL NO-GO** (Critical 2 件修正してから次フェーズ判断)
> - **Critical-1 (新発覚)**: time_exit 評価設計が「予測装置」になっていない (naive baseline)・`merge_step_i_summaries.py` L162-176 で全 trade に train 中央値由来の単一定数を割り当てる構造 → 24 fold すべてで time_exit returns が fold 内完全同一値 → 16 fold 中 8 fold が構造的に PASS 不可能 (寄与率 25-30%)
> - **Critical-2**: DSR bug は「設計階層の役割誤認」(まこさん仮説のガード追加で不十分・統計理論として定数 returns で auto-PASS は誤り)
> - **原因切り分け寄与率**: ① 学習不良 10-15% / (2a) fixed_tp 評価式暫定 40-50% / (2b) time_exit naive baseline 25-30% / ③ データ regime 過依存 10-15%
> - **案推奨**: 案 W (SL_PCT grid 拡張 1-2 日) + 案 V (K96 除外 0.5 日) + Critical-1 修正 (case_a_v2_v3・1-2 日) + Critical-2 修正 (dsr.py ガード + 判定階層整理 0.5 日) を **1 週間並列**実施 → それでも 0/16 なら案 Z の e (meta-labeling) 投入 (K96 fold0 部分成功を Secondary Filter として活用)・**案 X 単独直行は時期尚早**
> - CC 同型バイアス健全に機能した証跡: 監査が CC 整理と異なる結論を 3 件 (Critical-1 / Critical-2 / 案 W+V+Critical 修正先行) 出している
>
> #### 5. lessons L-212a/b/c 新規追加 (本セッション末)
> - **L-212a**: 16GB マシンの並列受け入れ能力限界 (3 並列で swap 42GB thrashing 再発・L-211 別側面) → 並列度 = (RAM × 0.5) / 1 プロセス推定 RSS で機械的算出ルール
> - **L-212b**: dsr.py × merge time_exit 定数化の相互作用 edge case (L-207 同型・統合 test 階層化義務) → input contract 明文化 + ガード追加 + integration test 必須化
> - **L-212c**: time_exit 評価設計が naive baseline で 0/16 出すまで気付かなかった (関所 B「変数の因果性宣言」→「評価式の予測装置性宣言」拡張) → CP X.5 監査経路を本走前に必須化
>
> ### 次セッション CC 優先順位 (明日 fresh head・まこさん cold head 判断後着手)
>
> 1. **優先 1 — まこさん判断: 監査推奨 vs 案 X 直行 (CC 判断不可・cold head 必須)**
>    - 案 A (監査推奨): Critical-1 (case_a_v2_v3 time_exit 予測装置化・1-2 日) + Critical-2 (dsr.py ガード・0.5 日) + 案 W (SL_PCT grid 拡張・1-2 日) + 案 V (K96 除外・0.5 日) を 1 週間並列 → 結果に応じて案 Z の e (meta-labeling) 投入
>    - 案 B: 案 X (Layer 3 投入・CPCV + Focal loss + アルゴ多様化・2-3 週間) 単独直行
>    - 案 C: CC が見落とした選択肢 (まこさん発案)
> 2. **優先 2 — 採用案実装 (1-3 週間)**: 案 A なら 1 週間並列 / 案 B なら 2-3 週間直行
> 3. **優先 3 — 再評価 (Step I-3 再走 or 案 X 完了後の評価)**
> 4. **優先 4 — Phase 2 進行判定 or 次の撤退ライン適用判定**
> 5. **優先 5 — セッション終了処理** (lessons L-213+ + WORKFLOW 改訂30 + handoff v31)
>
> ### 引き継ぎリソース (3 層構造)
>
> #### Layer 1 (毎セッション必読)
> - **handoff v30** (本セッション末作成予定): `.claude/instructions/handoff_to_cc_v30_session_20260523_cp4_audit.md`
> - WORKFLOW.md 改訂29 active ブロック (本ブロック)
> - CLAUDE.md (改訂22 ベース)
> - lessons_active.md 直近 5 件 (**L-212c → L-212b → L-212a → L-211 → L-210**)
>
> #### Layer 2 (案採用後の実装着手時)
> - **CP4 監査結果 (本ブロック §4 + Plan サブエージェント出力チャット・公式 source あり)**
> - Step I-1 仕様書 v2.1: `.claude/instructions/2026-05-23_phase4b_forward_design_spec.md` (612 行)
> - 実装 6 ファイル (本セッションまで完成・触らない):
>   - `scripts/priority_rebuild/run_tp_hit_classifier.py` (684 行)
>   - `scripts/priority_rebuild/compute_phase4b_train_constants.py` (458 行)
>   - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (873 行)
>   - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py` (597 行)
>   - `scripts/priority_rebuild/test_aggregate_grid_idxmax.py` (270 行)
>   - `scripts/priority_rebuild/merge_step_i_summaries.py` (453 行)
> - 案採用後の改修対象ファイル:
>   - Critical-1: `merge_step_i_summaries.py` L162-176 (time_exit returns 再構成式 予測装置化)
>   - Critical-2: `scripts/priority_rebuild/dsr.py` L115-134 (sigma_sr_estimate input contract + ガード)
>   - 案 W: `run_lgbm_phase1_v5_case_a_v2.py` (TP_PCT grid / SL_PCT grid 拡張)
>   - 案 V: `merge_step_i_summaries.py` (K=96 除外 + 6 組合せで再判定)
>
> #### データ・環境
> - parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
> - Step I-3.1 artifact (済): `_tp_hit_classifier_p{1,2,3}/tp_hit_classifier_predictions_train_2021_2024.parquet` (P1=76MB / P2=33MB / P3=28MB)
> - Step I-3.2 artifact (済): `_phase4b_train_constants/time_exit_return_median_*.json` (16 個 + INDEX 2)
> - Step I-3.3 artifact (済): `_case_a_v2_p{1,2,3}/case_a_v2_summary_*.json`
> - Step I-3.4 artifact (済): `_step_i_merged/phase1_v5_step_i_summary_merged.json` (公式 source)

---

## 🧊 改訂28 ブロック (履歴・参照用)

### 🔴 旧フェーズヘッダ（2026-05-23 改訂28・**Step I-2.8 unit test 10/10 PASS + I-2.6/I-2.7 §8 verify 完了 + I-3.2 完了 + merge スクリプト作成完了 + I-3.1 ハング → kill → PC 再起動待ち**・Step I-3.1 再起動が次タスク）

> **【旧正本ブロック・改訂28・2026-05-23 セッション後半 + 緊急中継】**
>
> ### 本セッション (改訂27 同日続編・2026-05-23 04:25 〜 07:35) 完了事項
>
> #### 1. I-2.8 集約ロジック unit test 完了 ✅
> - **`scripts/priority_rebuild/test_aggregate_grid_idxmax.py`** (新規・270 行)
> - 10 test cases (L-207 失敗境界 5 件含む: empty / tied / 全zero / 空ts / NaN)
> - **10/10 PASS** (`python test_aggregate_grid_idxmax.py` 経由・約 3 秒)
> - NaN edge case test 10 で現実装の隠れた問題 (`np.argmax` が NaN を最大扱い) を document として保護
>
> #### 2. I-2.6/I-2.7 受け入れ基準 §8 verify 完了 ✅
> - §8.1 関所 A: smoke `anomaly_smell_detected: False` (1/1 ・full 8 組合せで継続 verify 必要)
> - §8.2 TP Classifier: AUC 0.7062 ✅ / Brier 0.2216 ✅ / Calibration 0.1362 ❌ (smoke 浅学習由来・full で改善期待・許容 12% まで)
> - §8.3 月次 NET 分布: smoke N=4・median $-171.73 / range $-358 〜 $-94 (現実レンジ・L-210 整合「smoke 赤字 ≠ 設計欠陥」)
> - §8.4 leak verify 6 項目: (i)/(ii)/(iii)/(v)/(vi) ✅ / (iv) slippage 0.005% 解釈 = 往復扱い (まこさん GO 取得済・現値継承 → Phase 4-b-1 本確定で再評価)
> - §8.5 リカバリ: 関所 A 達成済 → 不要 / Calibration full 走で再判定 / slippage Phase 4-b-1 で再設計
>
> #### 3. I-3.2 完了 ✅ (5 秒完走)
> - **`scripts/priority_rebuild/compute_phase4b_train_constants.py --full`**: 16 artifact + INDEX 生成
> - K=12 N=6: ±0.0034% / K=24 N=24: ±0.0103% / K=96 N=96: ±0.0268% (LONG/SHORT 対称)
> - 警告: 全 16 ファイルで §5.6 月別歪度 > 1.0 (regime 過依存懸念・Phase 4-b-1 で cluster 別 median 化予定)
> - 出力: [`results/priority_rebuild/ml_phase1_v5/_phase4b_train_constants/`](results/priority_rebuild/ml_phase1_v5/_phase4b_train_constants/)
>
> #### 4. merge_step_i_summaries.py 作成完了 ✅ (動作未検証)
> - **`scripts/priority_rebuild/merge_step_i_summaries.py`** (新規・453 行)
> - P1/P2/P3 case_a_v2 summary + tp_hit_classifier predictions + time_exit_index を merge → §4.1 v5.1 判定 (4 指標)
> - 4 指標: TP Precision > 0.5 / Simulated PnL (12 ヶ月中 8+ 月 + 年間 NET ≥ $500) / DSR > 1.0 (n_trials=16) / entropy lift > 10% (案 a 自動 PASS)
> - method 別 (fixed_tp / time_exit) で 6+ 組合せ ALL PASS あれば Phase 2 進行
> - **動作確認は I-3.1/I-3.3 完了後**
>
> #### 5. I-3.1 ハング → kill 事案 (L-211・2026-05-23 04:46-07:35)
> - **発生**: tp_hit_classifier --full × 3 並列を `python ... | tee log | tail` 経由で起動 → VS Code 強制終了で tee/tail が kill → Python の stdout SIGPIPE 詰まり → 2 時間半ハング
> - **検出**: 07:30 JST にまこさんからの状況確認 → CPU TIME = 5:30 のまま停止 / output mtime 04:46 のまま発見
> - **対応**: kill 30267 / 30278 / 30286 → memory 13GB → 6.5GB 解放
> - **教訓**: lessons L-211 追加・修正後の起動コマンドは `python -u` + `> log 2>&1` + `nohup` + `disown` 必須
>
> ### 次セッション CC 優先順位 (PC 再起動後)
>
> 1. **優先 1 — Step I-3.1 再起動 (PC 再起動後・新 claude code session)**
>    - 修正後コマンド (handoff v29 §3 参照): `python -u` + `nohup` + `disown` + `> log 2>&1`
>    - 推定: 1.5 - 2 時間 3 並列
> 2. **優先 2 — Step I-3.3 case_a_v2 --full 3 並列 (30-60 分)**
> 3. **優先 3 — Step I-3.4 merge_step_i_summaries.py 実行 + §4.1 判定**
> 4. **優先 4 — Step I-3.5 CP4 監査依頼 (`/audit` サブエージェント・関所 D 必須)**
> 5. **優先 5 — セッション終了処理** (lessons L-212+ + WORKFLOW 改訂29 + handoff v30)
>
> ### 引き継ぎリソース (3 層構造)
>
> #### Layer 1 (毎セッション必読)
> - **handoff v29 (緊急中継版)**: `.claude/instructions/handoff_to_cc_v29_session_20260523_emergency.md` (本セッション末作成)
> - WORKFLOW.md 改訂28 active ブロック (本ブロック)
> - CLAUDE.md (Layer 2 パス修正済・改訂22 ベース)
> - lessons_active.md 直近 5 件 (**L-211 最新** + L-210 + L-209 + L-208 + L-207)
>
> #### Layer 2 (Step I-3 着手時)
> - Step I-1 仕様書 v2.1: `.claude/instructions/2026-05-23_phase4b_forward_design_spec.md` (612 行)
> - 実装 6 ファイル (本セッションで完成・触らない):
>   - `scripts/priority_rebuild/run_tp_hit_classifier.py` (684 行・I-2.1)
>   - `scripts/priority_rebuild/compute_phase4b_train_constants.py` (458 行・I-2.2)
>   - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (873 行・I-2.3)
>   - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py` (597 行・I-2.4)
>   - `scripts/priority_rebuild/test_aggregate_grid_idxmax.py` (270 行・I-2.8 新規)
>   - `scripts/priority_rebuild/merge_step_i_summaries.py` (453 行・I-3.4 新規)
>
> #### データ・環境
> - parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
> - I-3.2 artifact (済): `_phase4b_train_constants/time_exit_return_median_train_2021_2024_*.json` (16 個 + INDEX)
> - I-3.1 出力ディレクトリ (空・再起動後生成): `_tp_hit_classifier_p{1,2,3}/`
> - I-3.3 出力ディレクトリ (空・再起動後生成): `_case_a_v2_p{1,2,3}/`

---

## 🧊 改訂27 ブロック (履歴・参照用)

### 🔴 旧フェーズヘッダ (2026-05-23 改訂27・**Step I-1 仕様書 v2.1 確定 + CP3.5 監査 + I-2.1〜I-2.4 実装完了 + smoke 関所 A ② 0/8 達成**・Step I-2.5 以降 + Step I-3 本走準備)

> **【旧正本ブロック・改訂27・2026-05-23 セッション末 (改訂26 同日続編)】**
>
> ### 本セッション (改訂26 同日続編・2026-05-23 03:30 〜 04:20) 完了事項
>
> #### 1. Step I-1 仕様書 v2 → v2.1 確定 (CP3.5 監査 1 回目反映 + parquet 制約反映)
> - **v1 → v2 改訂**: CP3.5 監査 (Plan サブエージェント) で Critical 2 + Major 5 + Minor 4 + B 系 4 全 15 件指摘 → 全件 100% 反映で v2 確定
>   - **C1**: §6 method (b) trailing 数式論理破綻 → Step I スコープから除外 (Phase 4-b-1 本確定で別 Classifier と統合再投入)
>   - **C2**: §7.1 改修コードに pred_MFE 由来楽観仮定残存 → TP 価格を pred_MFE 由来から **固定 TP_PCT grid (定数)** に変更 (3 重楽観仮定 (1)(3) 物理的解消)
>   - **M1-M5 / B1-B4 / m1-m4**: 全件反映 (詳細は仕様書 §12 改訂サマリー参照)
> - **v2 → v2.1 微修正** (parquet 制約発見): parquet に open/high/low 不在 → §2.1 ラベル定義を既存 `{side}_MFE_pct_K{K}` 流用に変更 (option δ・数学的等価変換)
> - 公式 source: `.claude/instructions/2026-05-23_phase4b_forward_design_spec.md` (612 行)
> - まこさん指摘で「監査推奨 100% 採用ケースは再監査不要」を §10.2 で明文化 → CC 自己 verify (機械 grep) で 15 件全反映確認
>
> #### 2. I-2.1: TP 約定率 Classifier 実装 + smoke 完走
> - **`scripts/priority_rebuild/run_tp_hit_classifier.py`** (新規・684 行)
> - 8 組合せ (K × side) × 5 fold = 40 学習設計 (TP_PCT 特徴量化で 1 model 統合)
> - TP_PCT grid: (0.3, 0.5, 0.8, 1.2, 1.8, 2.5) % 6 段階
> - smoke (sample K=12 LONG TP_PCT=(0.3, 0.5, 0.8) / 2 fold / n_estimators=50):
>   - **AUC fold 0=0.7205 / fold 1=0.6920** (受け入れ基準 ≥ 0.55 を大幅超過 ✅)
>   - Brier 0.221 (基準 ≤ 0.25 PASS) / Calibration max dev 0.18 fold 0 (基準 ≤ 0.10 超過・smoke 浅学習由来・full で改善見込み)
>   - 51 秒で完走
>   - phase_compliance §1.4 Z 案ガード正常動作 (2 件 hit → 物理 verify 全 PASS → 続行)
>
> #### 3. I-2.2: time_exit_return_median artifact 生成
> - **`scripts/priority_rebuild/compute_phase4b_train_constants.py`** (新規・458 行)
> - N grid: (K//2, K) のみ (K×2 禁止・phase_compliance §4b.3)
> - median 化採用 (M3 反映・mean 比較で regime ロバスト性確認: K=12 LONG N=12 で mean -0.019% vs median -0.001%)
> - smoke 1 秒完走・artifact 2 ファイル + INDEX 生成
> - 月別歪度 verify (§5.6・|skew| > 1.0 で warning)
>
> #### 4. I-2.3: compute_simulated_pnl_v2 関数追加 + unit test 5/5 PASS
> - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (773 → 873 行・+100 行)
> - 旧式 compute_simulated_pnl は backward compat で残置
> - 新式 compute_simulated_pnl_v2: method=fixed_tp / time_exit 2 並列対応
> - unit test 5 件 (fixed_tp 数式 / time_exit 数式 / 空入力 / 不正 method raise / 旧式 backward compat) 全 PASS
>
> #### 5. I-2.4: case_a v2 (2 method 並列・grid idxmax 集約) + smoke
> - **`scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py`** (新規・597 行)
> - 別ファイル化判断 (既存 case_a 保護・Step F-H 動作確認済を維持)
> - I-2.1 predictions parquet + I-2.2 medians artifact をロードして 2 method × 各 grid で sim_pnl 計算
> - train PnL idxmax で grid 集約 (M2 反映)
> - smoke 結果 (sample K=12 LONG / 2 fold):
>   - **🎯 anomaly_smell_detected: False (0/8 達成・関所 A ②)** ✅
>   - 旧式 K=12 LONG max month_pnl $4,298 → 新式 month_pnl $-95 〜 $-358 (現実レンジ)
>   - 3 重楽観仮定除去で評価式が「正直」に動作することを定量実証
>
> #### 6. lessons L-210 新規追加
> - **L-210**: Phase 4-b 前倒し評価式実装で smoke 関所 A ② 0/8 達成 — Step I 設計が機能している定量実証
>   - 含む内容: smoke 赤字 = 設計が機能していない、と誤読しないこと / monitoring 指標として「異常値スメル件数」を継続採用
>
> ### 次セッション CC 優先順位 (Step I-2.5 以降 + Step I-3 本走準備)
>
> 1. **優先 1 — Step I-2.5: runner v5.2 拡張 (約 0.5-1 日)**
>    - case_a v2 では簡易版を内蔵実装済 → 必要なら正式に runner v5.2 として `FoldMetrics` に method 別 sim_pnl 保持を追加
>    - もしくは case_a v2 内蔵版を維持 (runner には影響しない設計)
> 2. **優先 2 — Step I-2.6/I-2.7: 受け入れ基準 §8 verify (約 0.5 日)**
>    - §8.1 関所 A ② 0/8: smoke で達成済 → full でも継続確認
>    - §8.2 TP 約定率モデル品質 (full 4 年で AUC / Brier / Calibration 再評価)
>    - §8.3 月次 NET 分布の現実性
> 3. **優先 3 — Step I-2.8: 集約ロジック unit test (約 0.5-1 日)**
>    - `_aggregate_grid_idxmax` (case_a v2) を単独 unit test 化
>    - edge case (empty grid / 同点 idxmax) verify
> 4. **優先 4 — Step I-3: 本走 (約 4-6 時間 3 並列 + 1 日判定)**
>    - run_tp_hit_classifier --full (40 Classifier 学習・推定 4-5 時間 3 並列)
>    - compute_phase4b_train_constants --full (16 artifact 生成・推定 5 分)
>    - case_a v2 --full (推定 30-60 分・predictions + medians を merge)
>    - §4.1 v5.1 判定 (method 別 5 指標 + 6+ 組合せ ALL PASS 集計)
> 5. **優先 5 (将来) — Step G Major M2 + M3 統合**:
>    - M2: entropy_lift NaN 自動 PASS 修正 (Spearman 相関代替)
>    - M3: importance dominance 50% → 30% 厳格化 + merge_asof boundary verify
>
> ### 引き継ぎリソース (新セッション Step 0 で必読・3 層構造)
>
> #### Layer 1 (毎セッション必読)
> - handoff v28 (本セッション末作成・find で動的取得)
> - WORKFLOW.md 改訂27 active ブロック (本ブロック)
> - CLAUDE.md (Layer 2 パス修正済・改訂22 ベース)
> - lessons_active.md 直近 5 件 (**L-210 最新** + L-209 + L-208 + L-207 + L-206)
>
> #### Layer 2 (Step I-2.5+ / Step I-3 着手時)
> - **Step I-1 仕様書 v2.1**: `.claude/instructions/2026-05-23_phase4b_forward_design_spec.md` (612 行)
> - 実装 4 ファイル:
>   - `scripts/priority_rebuild/run_tp_hit_classifier.py` (684 行・I-2.1)
>   - `scripts/priority_rebuild/compute_phase4b_train_constants.py` (458 行・I-2.2)
>   - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (873 行・I-2.3 拡張)
>   - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py` (597 行・I-2.4)
> - 既存 case_a (Step F-H 動作確認済): `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` (785 行・触らない・Step F-H 比較用)
>
> #### データ・環境
> - parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
> - smoke 出力 (新規):
>   - `results/priority_rebuild/ml_phase1_v5/_tp_hit_classifier/` (I-2.1)
>   - `results/priority_rebuild/ml_phase1_v5/_phase4b_train_constants/` (I-2.2)
>   - `results/priority_rebuild/ml_phase1_v5/_case_a_v2/` (I-2.4)

---

## 🧊 改訂26 ブロック (履歴・参照用)

### 🔴 旧フェーズヘッダ (2026-05-23 改訂26・**Phase 1 v5.1 Step H 本走 80 学習完走 → 不合格 + 異常値スメル 6/8 + CP3 監査で評価式暫定性確定**・Step I = Phase 4-b 前倒し設計着手準備)

> **【旧正本ブロック・改訂26・2026-05-23 セッション末】**
>
> ### 本セッション (改訂25 同日続編・2026-05-22 23:00 〜 2026-05-23 03:30) 完了事項
>
> #### 1. Step G CP2 監査 Critical 2 件対処 (commit `de709a5`)
> - C1: `DEFAULT_N_TRIALS` 6 → 48 (= 6 案 × 8 組合せ・selection bias 過少推定補正)
> - C2 (a): cost-deducted return (`pred_MFE/100 - 0.033%`・往復 maker fee + 暫定 slippage)
> - C2 (b): 関所 A 異常値検出を case_a 集計段階に追加 (`_detect_anomaly_smell()`・summary JSON に flag 追記・mid-run sys.exit せず最終判定で要再監査)
> - cc_ml_design_spec.md §1.5.1 v5.1 同記述更新
>
> #### 2. Step H 本走 3 並列実行完走 (P1=133 min / P2=101 min / P3=101 min・並列で 2.2 時間)
> - P1: K={12, 24} × LONG/SHORT (4 組合せ・out_base `ml_phase1_v5_step_h_p1/`)
> - P2: K=48 × LONG/SHORT (2 組合せ・out_base `ml_phase1_v5_step_h_p2/`)
> - P3: K=96 × LONG/SHORT (2 組合せ・out_base `ml_phase1_v5_step_h_p3/`)
> - merge script `scripts/priority_rebuild/merge_step_h_summaries.py` (218 行) で 3 summary を統合 → `ml_phase1_v5_step_h_merged/phase1_v5_summary_merged.json`
>
> #### 3. Step H 統合判定 (§4.1 v5.1)
> - **n_combinations: 8 / 8 ✅** (P1+P2+P3 完全結合)
> - **n_combinations_all_pass: 0** ❌ (5 指標 ALL PASS 組合せ ゼロ)
> - **meets_6plus_criteria: False** (撤退ライン抵触)
> - **layer3_investigation_needed: True**
> - **anomaly_smell_detected: True (6/8 組合せ)**:
>   - K=12 LONG: ② 月次相当 $4,298
>   - K=12 SHORT: ② $17,088
>   - K=24 LONG: ② $9,002
>   - K=24 SHORT: ②③ $30,572 + Sharpe 3.39 倍乖離
>   - K=48 LONG: セーフ ($2,998)
>   - K=48 SHORT: ② $46,810
>   - K=96 LONG: セーフ ($534)
>   - **K=96 SHORT: ②③ $84,185 + Sharpe 14.28 倍乖離** (最悪・合格ライン 44 倍超)
> - 公式 source: [`results/priority_rebuild/ml_phase1_v5_step_h_merged/phase1_v5_summary_merged.json`](results/priority_rebuild/ml_phase1_v5_step_h_merged/phase1_v5_summary_merged.json)
>
> #### 4. CP3 監査 (Plan サブエージェント独立評価) 完了
> - **判断 1 (異常値原因)**: 仮説 B (評価式の暫定過大評価) が 7-8 割支配・A (学習不良) は 2-3 割重畳
>   - 決定的根拠: `compute_simulated_pnl` の `return = pred_MFE/100 - cost` 設計で「TP 約定率 100% + slippage 0 + TP 価格 = MFE ピーク価格」3 重楽観仮定
>   - K=96 SHORT fold 1 数値分解: 26,098 trade × 平均 3.23%/trade = return 累計 841 倍 = 数学的必然
>   - train_rmse / label_std 比正常 + LONG/SHORT 非対称が市場期間特性 (LUNA / FTX / 2024-04 暴落) で説明可 → leak でない
> - **判断 2 (次アクション)**: **案 Y (Phase 4-b 前倒し設計) 採用**・案 X (Layer 3 即投入) は不採用
>   - 理由: 評価式が暫定段階で出た不合格を「学習方法変えれば合格」前提の撤退ライン文言で即 Layer 3 するのは誤読 → 評価式を Phase 4-b-2 仕様まで前倒し実装してから再判定
> - **判断 3 (Step G Major 後送り)**: Major 4 件中 **M2 + M3 は本走前に対処すべきだった**
>   - L-207「test カバレッジ穴」同型バイアス再演
>
> #### 5. lessons L-208 + L-209 新規追加
> - **L-208**: 評価式が暫定段階で出た異常値スメルを学習不良と取り違える危険 (原因切り分け順序 ①学習/②評価式/③データ 必須化・撤退ライン文言の解釈基準・Phase 4-b 前倒しトリガ基準)
> - **L-209**: CC 同型バイアス「Major 後送り判断」= 自分で範囲狭めて OK 判定する癖の再演 (CP3 監査で発覚・関所 G に「Critical 漏れ + Major 後送り = すり抜け扱い」統合)
>
> #### 6. memory feedback 新規追加
> - **`~/.claude/projects/.../memory/feedback_plain_language.md`**: 専門用語多用禁止・例え話で補足・固有名詞最小化 (まこさん指摘「専門用語が多くよくわからない」反映)
>
> ### 次セッション CC 優先順位 (Step I = Phase 4-b 前倒し設計着手)
>
> 1. **優先 1 — Step I-1: Phase 4-b 前倒し設計仕様書作成 (約 1-2 日)**
>    - 設計ベース: `phase_flow_v4_with_recovery.md` L528 周辺 + `phase_compliance_checklist.md` §4b.4 + §4b.4-b
>    - 含むべき項目:
>      (a) TP 約定率モデル (別 LightGBM Classifier: `P(future_high >= entry × (1+TP_PCT))`)
>      (b) 実 TP 価格モデル (`pred_MFE × X%` or cluster 別 quantile)
>      (c) trailing exit 暫定モデル (高値追従・反転で利確)
>      (d) time exit 暫定モデル (N 分経過で強制決済)
>      (e) 3 方式並列 (固定 TP / トレーリング / 時間 Exit) で Phase 1 評価式に組込み
>      (f) `compute_simulated_pnl` 改修方針 (pred_MFE 全額計上 → 約定率モデル乗算)
> 2. **優先 2 — Step I-2: 実装 + smoke test (約 1-2 週間)**
>    - 改修後 case_a smoke で異常値スメル ② が消えることを verify (sample 89 日で月次 NET < $3,800 を目標)
>    - K=96 SHORT で sim_pnl_year_usd が $1,000,000 → $20,000-50,000 オーダーに縮小することを期待
> 3. **優先 3 — Step I-3: Step H 再走 (約 2-3 時間・3 並列)**
>    - 改修後 8 組合せ × 5 fold で再走し「真の」§4.1 判定
>    - 6+ 組合せ ALL PASS → Phase 2 進行 / 未達 → 案 X (Layer 3) or 案 Z (案 b-f) 検討
> 4. **優先 4 — Step G Major 4 件のうち M2 + M3 を本実装に統合**:
>    - M2: 案 a で `entropy_lift=NaN → 自動 PASS` の判定骨抜きを修正 (regression 代替指標 = Spearman 相関等)
>    - M3: importance dominance 50% → 30% に厳格化 + merge_asof boundary verify ロジック追加
>
> ### 引き継ぎリソース (新セッション Step 0 で必読・3 層構造)
>
> #### Layer 1 (毎セッション必読)
> - handoff v27 (本セッション末作成・find で動的取得)
> - WORKFLOW.md 改訂26 active ブロック (本ブロック)
> - CLAUDE.md (Layer 2 パス修正済・改訂22 ベース)
> - lessons_active.md 直近 5 件 (**L-209 最新** + L-208 + L-207 + L-206 + L-205)
>
> #### Layer 2 (Step I 着手時)
> - **CP3 監査結果** (本ブロック §4 + L-208 / L-209)
> - **phase_flow_v4_with_recovery.md** L528 周辺 (Phase 4-b-2 既存設計)
> - **phase_compliance_checklist.md** §4b.4 + §4b.4-b (TP 約定モデル基準)
> - **technical_analysis_knowledge_base.md** §I.6.3 (Phase 別データ駆動再検討フロー)
> - 実装: `run_phase1_v5_purged_kfold.py` (`compute_simulated_pnl` L295-316 が改修中心) + `run_lgbm_phase1_v5_case_a_rmse.py` (L382-388 returns_per_trade)
> - merge script: `merge_step_h_summaries.py` (Step I-3 再走時に再利用)
>
> #### データ・環境
> - parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
> - Step H 結果: `results/priority_rebuild/ml_phase1_v5_step_h_p{1,2,3}/` + `ml_phase1_v5_step_h_merged/`

---

## 🧊 改訂25 ブロック (履歴・参照用)

### 🔴 旧フェーズヘッダ(2026-05-22 改訂25・**Phase 1 v5.1 Step F 本走 smoke 完走 + dsr.py L119 隠れ bug 修正**・Step G CP2 監査着手準備）

> **【現在の正本ブロック・改訂25・2026-05-22 セッション後半】**
>
> ### 本セッション (改訂24 同日続編) 完了事項
>
> #### 1. Step F 本走 smoke 完走 (1.3 分・sample 5 fold)
> - 実行: `--smoke --n-estimators 300 --n-splits 5` (sample.parquet / K=12 LONG・3 fold 生成 = min_train_splits=2 仕様通り)
> - **Z 案ガード本来環境で正常動作確認** ✅ (handoff v26 §1.4・hit 2 列 → 物理 verify 4 項目 PASS → 警告 + 続行)
> - 公式 source: [`results/priority_rebuild/ml_phase1_v5/phase1_v5_summary.json`](results/priority_rebuild/ml_phase1_v5/phase1_v5_summary.json) (167 行・2026-05-22T22:55:00)
> - 結果: 5 指標未達 (smoke 1 組合せで合格不可・想定通り)・`tp_precision_mean=0.448` / `sim_pnl_year_usd_mean=$14,186` / `fold_sharpe_mean=7.99` / `dsr_zscore=-62.03`
> - **異常値スメル ③ 該当** (fold sharpe={4.37, 15.66, 3.96} で乖離) ・**統計有意性なし** (sample 89 日 × 3 fold) ・Step H 本走で再評価必須
> - fold 1 で W2 警告 (`valid_rmse/train_rmse=5.28 > 3.0`) → 物理 leak verify PASS のため **overfit と判定** (leak ではない・sample 小データ由来)
>
> #### 2. dsr.py L119 算術 bug 発見・修正 (handoff v26 未記載の隠れ bug)
> - smoke 1 回目 (`fold 3` 集約段階) で `ValueError: sigma_SR denominator non-positive (-0.194571)` crash
> - **根本原因**: Bailey-Lopez de Prado 2014 / Mertens 2002 形式 `(γ₄ - 1)/4` の **γ₄ は総 kurtosis (Gaussian で 3) を前提** だが、dsr.py は `scipy.stats.kurtosis(fisher=True)` (excess kurt・Gaussian で 0) を渡しており、Gaussian 入力 SR > 2 で `inner < 0` で確実に crash する設計欠陥
> - **修正**: `(excess_kurt - 1.0) / 4.0` → `(excess_kurt + 2.0) / 4.0` (等価: `total_kurt = excess_kurt + 3 → (total_kurt - 1)/4 = (excess_kurt + 2)/4`)
> - Lo (2002) closed form `Var(SR̂) = (1 + 0.5·SR²)/T` (Gaussian) と一致確認
> - `test_dsr.py` 2 ケース期待値再計算: Gaussian sigma = `sqrt(1.5/100)` (旧 `sqrt(0.75/100)`) / extreme case sigma_SR=0.14771・z=4.811 (旧 0.13440・5.287)
> - **test 10/10 PASS 維持**・smoke 再走 1.3 分完走 (Step F 達成)
>
> #### 3. lessons L-207 新規追加
> - **L-207**: test カバレッジが「合格境界」のみで「失敗境界」を含まないと bug 素通り — 数値式 test は失敗境界 (raise 境界) を必ず含める
>
> ### 次セッション CC 優先順位 (Step G CP2 監査着手)
>
> 1. **優先 1 — Step G: CP2 監査 (`/audit` または Plan サブエージェント・約 30-60 分)**
>    - 監査対象: Phase 1 v5.1 案 a 実装 + Z 案ガード改訂 + 本走 smoke 結果 + **dsr.py L119 bug 修正の数学的妥当性 (新規)**
>    - 監査項目 (handoff v26 §3.2 の 9 項目 + dsr fix):
>      - 1-9: handoff v26 §3.2 列挙
>      - 10. **(新規)** dsr.py L119 修正の Bailey-Lopez de Prado 原典との整合性 (γ₄ 総 kurt 解釈の妥当性)
>      - 11. **(新規)** test_dsr.py 期待値再計算の独立 verify (Lo 2002 closed form との一致)
>      - 12. **(新規)** 異常値スメル ③ (sample sharpe 乖離) の Step H 本走前の原因仮説評価
> 2. **優先 2 — Step H: full 8 組合せ実行 (CP2 OK 後・約 5-6 時間 / 3 並列 2 時間)**
> 3. **その後**: 案 b-f 順次実装 (約 3-4 週間)
>
> ### 引き継ぎリソース (新セッション Step 0 で必読・3 層構造)
>
> #### Layer 1 (毎セッション必読)
> - **handoff v26** (改訂24 セッション末作成・find で動的取得) — 主要記述は本改訂25 で更新済 (Step F smoke 完走 + dsr fix)
> - WORKFLOW.md 改訂25 active ブロック (本ブロック)
> - CLAUDE.md (Layer 2 パス修正済・改訂22 ベース)
> - lessons_active.md 直近 5 件 (**L-207 最新** + L-206 + L-205 + L-204 拡張 + L-203)
>
> #### Layer 2 (Step G 着手時)
> - smoke 結果: `results/priority_rebuild/ml_phase1_v5/phase1_v5_summary.json` (167 行) + `smoke_run_20260522T225341.log` (54 行)
> - dsr fix: `scripts/priority_rebuild/dsr.py` (204 行・L119 修正済) + `test_dsr.py` (205 行・10/10 PASS)
> - case_a: `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` (720 行) + runner v5.1 (773 行) + verify_top20 (490 行)
> - Phase 1 v5 指示書 v5.1 / cc_ml_design_spec.md §1.5.1 v5.1 / phase_compliance §1.4 Z 案
>
> #### データ・環境
> - parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
> - smoke 出力: `results/priority_rebuild/ml_phase1_v5/_early_fi_for_guard_review/`

---

## 🧊 改訂24 ブロック (履歴・参照用)

### 🔴 旧フェーズヘッダ(2026-05-22 改訂24・**Phase 1 v5.1 Step E (case_a) 実装完了 + Z 案ガード改訂**・Step F 本走 smoke 着手準備）

> **【現在の正本ブロック・改訂24・2026-05-22 セッション末】**
>
> ### 本セッション (改訂23 同日続編) 完了事項
>
> #### 1. Step E (case_a 実装) 完了
> - **`scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py`** (新規・637 行・commit pending)
> - 16 model (LONG/SHORT × MFE/MAE × K={12,24,48,96}) × 5 fold = 80 学習設計
> - TP first 0/1 化: `pred_MFE / max(pred_MAE, 1e-6) >= 1.5` (phase_flow_v4 L151 既定・LONG/SHORT 共通)
> - TP first 正解: `triple_barrier_label_{side}_K{K} == +1` (全案統一)
> - train/valid 分離: Purged train_idx 末尾 10% を valid + embargo assert
> - feature_importance 全 16 model 保存 (Phase 2 ハイパラ調整参照用)
> - runner v5.1 統合 (W1/W2 警告 + DSR 連携 + 8 組合せ aggregate)
> - CLI: `--smoke / --full / --parquet 明示 / --k / --side / --n-splits / --min-train-splits` 全揃い
>
> #### 2. 物理 leak verify ツール実装
> - **`scripts/priority_rebuild/verify_top20_features_leak.py`** (新規・446 行・commit pending)
> - 4 verify 項目: (i) lag-1 shift 不変性 **TF-aware** (5m/15m/30m/4h 各 TF の expected pct_diff = 5/TF_min を ±50% で許容) / (ii) 末尾 K bars NaN pattern / (iii) 二重 N サフィックス内外一致 / (iv) importance gain single < 50%
> - sample.parquet (25k 行) + full train_2021_2024.parquet (394k 行) で実行・JSON 保存
>
> #### 3. Plan エージェント独立監査 + 重大発見
> - sample 89 日で検出された 4 件 (`dist_to_fib_v2_382`, `resistance_distance`, `dist_to_fib_v2_500`, `nearest_level_touch_count`) は **full 4 年で top20 外**
> - **sample = レジーム過依存 (false_positive §2 類型 D 時代依存) 確定**
> - full 4 年で新検出 1 件 (`support_distance_pct_N100_N100__5m`) も物理 verify 全 PASS
> - full top20 トップは `atr14_pct__5m` / `close_vs_st_upper_pct__5m` / `bb_bw_rolling_p20_100b__15m` / `dist_to_VAH_pct_N200_b100_va80_N200__1h` 等の **業界知見整合の強い予測子**
>
> #### 4. phase_compliance §1.4 Z 案改訂 (3 段階運用・正本改訂)
> - **`.claude/rules/phase_compliance_checklist.md` §1.4** (改訂・commit pending)
> - 旧: top1-20 hit → 即 sys.exit(1)・調査必須・緩和不可
> - 新: (a-1) hit 検出 → 物理 verify 4 項目全 PASS → 警告ログ + full_rank 記録 + 続行可 / (a-2) 1 項目でも FAIL/SKIP → 即停止 / ブラックリストパターン自体の緩和は実施しない (将来回帰検出機能維持・defense-in-depth)
> - 案 a `_check_fractal_leak` ロジック拡張 (verify セット呼出 + 全 PASS 続行・smoke で動作確認 ✅)
>
> #### 5. lessons L-206 新規追加
> - **L-206**: ブラックリストガードを保守一辺倒で運用すると false positive で物理進行不能・Z 案 (物理 verify 経由続行) 改訂で defense-in-depth 維持
>
> ### ⚠️ 異常値スメル (次セッション要再評価)
>
> smoke (sample 89 日・n_estimators=30・1 fold) で **sharpe=6.417・sim_pnl_year_usd=$8689** という異常値検出。ただし統計的有意性なし (短期間 + 浅学習)。**Step F 本走 (full parquet 5 fold / n_estimators=300+) で再評価必須**。出続けたら類型 D regime 過依存等の調査要 (関所 A 異常値判定基準: sharpe > 3 倍乖離 / month NET > $3,800)。
>
> ### 次セッション CC 優先順位 (Step F 本走 smoke 着手)
>
> 1. **優先 1 — Step F: 本走 smoke (約 30-60 分)**
>    - 設定: `--parquet sample または train_2021_2024.parquet / --k 12 --side LONG / --n-splits 5 / --n-estimators 300`
>    - Z 案ガード警告ログ + 続行を本来環境で確認
>    - **異常値スメル 4 条件 verify** (sharpe / month NET / IS-OOS / DD)
>    - メモリ消費実測 (1 model 10-15 GB 想定)
> 2. **優先 2 — Step G: CP2 監査 (`/audit` 経由・指示書 §9 の 7 項目)**
>    - Z 案改訂後の整合性 + smoke 結果妥当性
> 3. **優先 3 — Step H: full 8 組合せ実行 (約 5-6 時間 / 3 並列 2 時間)**
>    - case_a 完走 → §4.1 採用判定 or Layer 3 投入決定
> 4. **その後**: 案 b-f 順次実装 (約 3-4 週間)
>
> ### 引き継ぎリソース (新セッション Step 0 で必読・3 層構造)
>
> #### Layer 1 (毎セッション必読)
> - **handoff v26** (本セッション末作成・find で動的取得)
> - WORKFLOW.md 改訂24 active ブロック (本ブロック)
> - CLAUDE.md (Layer 2 パス修正済・改訂22 ベース)
> - lessons_active.md 直近 5 件 (**L-206 最新** + L-205 + L-204 拡張 + L-203 + L-202)
>
> #### Layer 2 (Step F 着手時)
> - **Phase 1 v5 指示書 v5.1** (`.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`)
> - **cc_ml_design_spec.md §1.5.1 v5.1**
> - **`.claude/memory/phase_flow_v4_with_recovery.md`** (L151 1.5 既定 / L528 Phase 4-b-2 本確定)
> - **`.claude/memory/technical_analysis_knowledge_base.md`** §I.6.3 (Phase 別データ駆動再検討フロー)
> - **case_a スクリプト** (`scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py`・637 行)
> - **verify_top20 ツール** (`scripts/priority_rebuild/verify_top20_features_leak.py`・446 行)
> - **runner v5.1** (`scripts/priority_rebuild/run_phase1_v5_purged_kfold.py`・773 行)
> - **dsr.py + test_dsr.py** (`scripts/priority_rebuild/`)
> - **phase_compliance §1.4 Z 案** (`.claude/rules/phase_compliance_checklist.md`)
>
> #### データ・環境
> - **parquet 3 種** (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`)
> - **.venv311 環境** (mlfinpy 0.1.2 + timeseriescv 0.2 + scikit-learn 1.8.0 + lightgbm 4.6.0 + scipy 1.17.1)
> - **smoke 出力**: `results/priority_rebuild/ml_phase1_v5/_early_fi_for_guard_review/` (fi_top20 + full_rank csv)
> - **leak verify JSON**: `results/priority_rebuild/leak_verify_*.json` (sample + full 計 3 件)

---

## 🧊 改訂23 ブロック (履歴・参照用)

### 🔴 旧フェーズヘッダ(2026-05-22 改訂23・**Phase 1 v5.1 設計確定 + Step 2/D 完了** = runner v5.1 拡張完成・Step E (case_a) 着手準備)

> **【旧正本ブロック・改訂23・2026-05-22 セッション末】**
>
> ### 本セッション (改訂22 同日後半・継続) 完了事項
>
> #### 1. Step 2 完了 (commit `6412cf1`・共通 Purged K-Fold runner 初版)
> - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (529 行・新規)
> - timeseriescv.PurgedWalkForwardCV ラッパ + t1 vertical barrier runtime 算出 (parquet 未保存・index + K × 5min)
> - Phase -1 blacklist 64 列 + 56 ラベル列を物理 drop (Prime Directive §0-1)
> - dsr.py 統合 (5 fold aggregate で DSR 算出・sr_variance = fold_sharpe variance)
> - sample parquet 実機 verify: blacklist drop 64 ✅ / label drop 56 ✅ / X shape (25345, 2604) ✅
>
> #### 2. Phase 1 v5.1 設計確定 + Step A-C 完了 (commit `eff0aff`・spec/指示書/CLAUDE.md 修正)
> まこさん Q1/Q2/Q3 議論 (3 ファイル `learning_design_v4` / `phase_flow_v4_with_recovery` / `technical_analysis_knowledge_base` Read 後) で **Phase 1 v5 → v5.1 厳格化**確定:
> - **Q1 Entry 閾値**: 1.5 = phase_flow_v4 L151 既定 (旧 V3 比較ベースライン・改善期待しない明示)・本確定は **Phase 4-b-2 (3 方式並列)**・TP first 正解は **`triple_barrier_label_{LONG,SHORT}_K{K}` == +1** 全案統一
> - **Q2 train/valid 警告**: W1 (`train_rmse/label_std < 0.10`) + W2 (`valid_rmse > train_rmse × 3.0`) を warning ログ追加 (L-179 leak 補完層)
> - **Q3 評価単位厳格化**: K=12 LONG 単独 → **8 組合せ (K=12/24/48/96 × LONG/SHORT)・6+ 組合せで 5 指標 ALL PASS** (cc_ml_design_spec §1.6 撤退ライン同構造整合)
>
> 修正ファイル (3 件):
> - cc_ml_design_spec.md §1.5.1 v5.1 (8 組合せ + 6+ 合格判定 + §1.6.1 メタルール例外承認内)
> - Phase 1 v5 指示書 §2-§5 全面修正 (16/8 model × 5 fold = 260 学習・約 28-30 時間)
> - CLAUDE.md L142/146/147 パス hardcode 不整合修正 (L-204 追加事案)
>
> #### 3. Step D 完了 (commit `06dd10d`・runner v5.1 拡張)
> - `run_phase1_v5_purged_kfold.py` 529 → 773 行 (+244 行)
> - `FoldMetrics` 拡張 (`side` / `train_rmse` / `valid_rmse` / `label_std` / `warnings: List[str]`)
> - `CombinationSummary` dataclass 新規 (1 組合せ K × side 5 fold 統合 + DSR + pass 判定)
> - `CaseSummary` 全面再設計 (8 組合せ統合 + 6+ ALL PASS 判定 + `meets_6plus_criteria`)
> - `compute_fold_metrics` 拡張 (`y_true_tp_first` / `y_pred_tp_first` 引数化・W1/W2 警告検出)
> - `aggregate_combination_to_summary` + `aggregate_8_combinations_to_summary` 新規 (旧 `aggregate_to_summary` 廃止)
> - `_self_check` v5.1 拡張: timeseriescv split / compute_fold_metrics / W1/W2 warning / 2 組合せ aggregate 全 PASS
>
> #### 4. lessons L-205 新規 + L-204 拡張
> - **L-205**: ドキュメント引用前 実装 verify 漏れ + 早計自己申告 (1.5 を CC 独断値と即時自己申告したが phase_flow_v4 L151 既定値だった・L-180 同型再演)
> - **L-204 拡張**: CLAUDE.md L142/146/147 Layer 2 パス hardcode 不整合事案を追加 (handoff バージョン hardcode と同型「文書間参照リンク切れ」)
>
> ### 次セッション CC 優先順位 (Step E 着手)
>
> 1. **優先 1 — Step E (案 a 実装・約 1-2 日)**: `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` 新規 (約 320-380 行)
>    - 16 model (LONG/SHORT × MFE/MAE × K={12,24,48,96}) × 5 fold = **80 学習** (v5.1 設計)
>    - runner v5.1 を import: `load_parquet_with_blacklist` / `compute_fold_metrics` / `aggregate_8_combinations_to_summary`
>    - case 別 0/1 化ルール: 予測 MFE / |予測 MAE| ≥ 1.5 (phase_flow_v4 L151 既定)
>    - TP first 正解: `triple_barrier_label_{LONG,SHORT}_K{K}` == +1
>    - phase_compliance_checklist §1.4 ガード: 1 ラベル目 (K=12 LONG_MFE) feature_importance top20 review (top1-20 hit → sys.exit(1))
>    - W1/W2 警告ログ (smoke 段階で運用確認)
> 2. **優先 2 — Step F smoke test (約 1 時間)**: Fold 0 + K=12 LONG のみで動作確認・メモリ消費実測
> 3. **優先 3 — Step G CP2 監査依頼** (`/audit` 経由・7 項目)
> 4. **優先 4 — Step H full 8 組合せ実行** (約 28-30 時間・3 並列で 10-13 時間)
> 5. **その後**: 案 b-f 順次実装 → §4.1 採用判定 or Layer 3 投入
>
> ### 引き継ぎリソース (新セッション Step 0 で必読)
>
> - **handoff v25** (本セッション末作成) — Step 2/A-C/D 完了 + v5.1 設計確定経緯 + Step E 着手詳細
> - **lessons_active.md L-205 (最新)** — ドキュメント引用前 verify 漏れ・L-180 同型再演
> - **lessons_active.md L-204 拡張** — CLAUDE.md パス hardcode 不整合追加事案
> - **runner v5.1** (`scripts/priority_rebuild/run_phase1_v5_purged_kfold.py`・773 行・commit `06dd10d`)
> - **dsr.py + test_dsr.py** (`scripts/priority_rebuild/`・commit `5918456`)
> - **Phase 1 v5 指示書 v5.1** (`.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`・8 組合せ + W1/W2 + 260 学習版・commit `eff0aff`)
> - **cc_ml_design_spec.md §1.5.1 v5.1** (commit `eff0aff`)
> - **CLAUDE.md** Layer 2 パス修正済 (`.claude/memory/phase_flow_v4_with_recovery.md` / `technical_analysis_knowledge_base.md` / `CAT−指標マトリックス - 一覧.csv`)
> - **.venv311 環境** (Step C 完了・mlfinpy 0.1.2 + timeseriescv 0.2 + scikit-learn 1.8.0 + lightgbm 4.6.0 + scipy 1.17.1)
> - **parquet 3 種** (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`)

---

> ### 🧊 改訂22 ブロック (履歴・参照用・2026-05-22 セッション末で改訂23 に上書き)
>
> **【旧正本ブロック・改訂22・2026-05-22 セッション末】** — Step D 優先 1 (dsr.py) 完了 + 必読リスト 3 層構造化 + lessons L-204 追加 + 履歴 archive 移送
>
> 主な完了事項:
> 1. Step D 優先 1 (commit `5918456`): dsr.py 自前実装 (Bailey + Lopez de Prado 2014 SSRN 2460551・204 行)・test 10/10 PASS
> 2. ドキュメント整理 3 層構造化 (WORKFLOW 672 → 369 行 / lessons 2099 → 1141 行 / web_claude_role 477 → 35 行参照スタブ / CLAUDE.md 必読リスト 3 層化 + handoff hardcode 撤廃)
> 3. lessons L-204 追加 (system reminder auto-load 鵜呑み + handoff hardcode 不整合)
>
> 次セッション優先順位 (旧版・本改訂23 で更新済):
> - 優先 1: Phase 1 v5 §6 実装手順 Step 2 以降 → **改訂23 で Step 2/A-C/D 完了済 + Step E 着手準備**
>
> 詳細は `archive/workflow/WORKFLOW_archive_20260522.md` 経由参照 (改訂23 セッション末にて archive 移送)。

---

> ### 🧊 改訂21 ブロック (履歴・参照用)

> **【旧正本ブロック・改訂21・2026-05-22 セッション末】**
>
> ### 本セッション (改訂20 セッション → 同日継続) 完了事項
>
> #### 1. blacklist 48 → 64 列反映 (commit `ef0e26d`)
> - L-202 Q1 自己申告反映 (1w/1M MTF 拡張で 8 family × 8 TF = 64 列)
> - Phase 1 v5 指示書 6 箇所 + phase_compliance_checklist.md 13 箇所更新
> - 学習対象 feature 数: 1,414 → **2,604** (実 parquet 2,724 - 56 ラベル - 64 blacklist)
>
> #### 2. Step C 完了 (commit `560122e`)
> - brew install python@3.11 → Python 3.11.15 (.venv311 構築・.gitignore 済)
> - mlfinpy 0.1.2 / timeseriescv 0.2 / scikit-learn 1.8.0 / lightgbm 4.6.0 / pandas-ta-classic 0.6.20 / pyarrow 24.0.0 / ta 0.11.0 install
> - 機能 verify 全 pass (Triple Barrier / Meta-Labeling / PurgedWalkForwardCV / CombinatorialPurgedKFold / Fractional Diff / Sample Weights)
> - parquet 読み込み verify OK (test_2026_q1: 25,631 × 2,724)
>
> #### 3. 重大発見: mlfinlab PyPI 削除 + closed-source 化 (commit `560122e`)
> - **mlfinlab は PyPI 削除済**・GitHub `hudson-and-thames/mlfinlab` は "All Rights Reserved" license (Hudson & Thames が Business/Enterprise 商業ライセンスのみ提供)
> - handoff v22 Q4「Python 3.13 wheel なし → 自前実装」の根拠認識は誤り (**実態は商業化による PyPI 削除**)
> - 代替確定: **mlfinpy** (PyPI 公開・open-source・AFML 直接実装・`baobach/mlfinpy`) + **timeseriescv** (Walk-forward Purged CV・`sam31415/timeseriescv`) + **自前 DSR**
> - Phase 1 v5 指示書 18 hit → mlfinpy + timeseriescv に修正 (12 Edit・残存 8 件は経緯/API リファレンスとして意図的に保持)
> - WebSearch 能動活用義務 (cc_role §1.0 + L-201) を本セッション後半でようやく履行・L-201 1 週間以内再演
>
> #### 4. lessons L-203 追加 (mlfinlab 実態調査不足・L-201 再演)
> - 外部依存パッケージの状態確認を handoff の自己申告で済ます癖を矯正
> - 外部ライブラリ import を指示書に書く前に PyPI 実存確認義務
> - install 試行は機能 verify までセット (`pip install OK` だけで「動く」と判断しない)
>
> ### 次セッション CC 優先順位 (Step D 着手)
>
> 1. **優先 1 (dsr.py 自前実装・1-2 時間)**: Bailey + Lopez de Prado 2014 SSRN 2460551
>    - 数式: DSR = (SR - SR*) / sigma_SR (skew + kurtosis + 試行数補正・Euler-Mascheroni constant)
>    - 配置: `scripts/priority_rebuild/dsr.py`
>    - test ケース: scipy / numpy ベース・100+ grid 試行記録の selection bias 補正
> 2. **優先 2 (Phase 1 v5 実装着手・約 3-4 週間)**: Phase 1 v5 指示書 §6 実装手順 Step 2 以降
>    - run_phase1_v5_purged_kfold.py (共通 CV runner・timeseriescv.PurgedWalkForwardCV 主用)
>    - case_a (14 ラベル RMSE) / case_b (Binary) / case_c (Multiclass) / case_d (LambdaRank) / case_e (Triple Barrier・mlfinpy.labeling.get_events) / case_f (Meta-Labeling・mlfinpy.labeling.get_bins・case_e 後 sequential)
>    - smoke test (Fold 0・1-2 ヶ月・1 時間以内)
>    - CP2 監査 (Claude `/audit` 経由・7 項目)
>    - full 5 fold × 6 案 = 30 学習 (約 20 時間・3 並列・メモリ 30-45 GB)
>    - §4.1 採用判定 or Layer 3 投入 (6 案ベストでも 5 指標未達なら即 Layer 3)
> 3. **優先 3 (将来)**: Phase 4-b 設計再 audit / Phase 5/6/7 統合 / OI 特徴量化 (Phase 4-b 結果次第)
>
> ### 引き継ぎリソース (新セッション Step 0 で必読)
>
> - **handoff v23** (本セッション末作成予定) — Step C 完了 + mlfinpy 切替 + dsr.py 実装方針 + Step D 着手詳細
> - **lessons_active.md L-203** — mlfinlab PyPI 削除 + WebSearch 能動活用義務再確認 (本セッション学習)
> - **lessons_active.md L-202** — CC 完全網羅志向 + 指示書フロー並列実施手順違反
> - **lessons_active.md L-201** — WebSearch 能動活用 + 業界経験閾値 bool ハードコード禁止
> - **Phase 1 v5 指示書 (mlfinpy 切替版)** (`.claude/instructions/2026-05-22_phase1_layer_inversion_instruction.md`・約 440 行・commit `560122e`)
> - **phase_compliance_checklist.md §Phase -1** (blacklist 64 列反映済・commit `ef0e26d`)
> - parquet 3 種 (`results/priority_rebuild/labels_mfe_mae_pct_{train_2021_2024,test_2025,test_2026_q1}.parquet`・sha256 既出)
> - **.venv311 環境** (Step C 完了・gitignore 済・mlfinpy + timeseriescv + scikit-learn + lightgbm + 依存パッケージ install 済)

---


## 📚 履歴 archive 参照

WORKFLOW.md は 2026-05-22 改訂22 で再スリム化 (672 → 358 行・履歴 313 行を archive 移動):

| archive ファイル | 範囲 | 行数 |
|---|---|---|
| [archive/workflow/WORKFLOW_archive_20260522.md](archive/workflow/WORKFLOW_archive_20260522.md) | 改訂20 / 19 / 18 / 17 / 16 / 15 表記 | ~250 |
| [archive/workflow/WORKFLOW_archive_20260521.md](archive/workflow/WORKFLOW_archive_20260521.md) | 改訂13 / 14 / 15 / 7 + 試行禁止リスト + 旧 Priority パラメータ + Replay コマンド (旧フロー) + 引き継ぎリソース (旧版) | 538 |

履歴セクションの読了は **次セッション着手判断には不要**。現フェーズ判定で過去経緯を参照したい時に該当 archive を find で開く。
