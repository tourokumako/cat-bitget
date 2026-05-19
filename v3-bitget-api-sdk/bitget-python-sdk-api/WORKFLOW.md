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
- 目標（$60/day）から常に逆算して行動する。目先の指標改善に満足しない
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
- 「$60/day」を 5 ターン口に出していない
- 議論が「達成方法」から「達成できない理由の整理」にシフトしている

**手順**:
1. 直前の自分の発言を「$60/day 達成への前進 / 諦めの言い換え」で 2 値判定する
2. 後者なら撤回し「$60/day に届かせるなら、ここから何ができるか」で書き直す
3. 「できない」と言いそうになったら「いつまでに / どの条件が揃えば / 何を試せば」の 3 点で具体化してから出す

**禁則**:
- 「現実的な落とし所」を出す前に $60/day に届く案を最低 1 つ出す
- 認知バイアスや構造的制約の説明で 1 ターン丸ごと使わない（説明は 2 文以内）
- 目標を下げる方向の整理をこちらから提案しない

**背景**: Claude は「達成への思考」より「諦めを丁寧に言語化する思考」に流れやすい癖がある。思考フレーム自己点検（狭さ対策）と二段構えで引き戻す（2026-04-27 教訓）。

## Priority 再構築管理

> 🧊 priority_rebuild.md (旧 A-1〜D framework) は 2026-05-13 ML pipeline 切替で廃止・参照のみ。

ML pipeline (Phase 0〜7) の**仕様・合否基準・設計確定事項**の正本は以下の 3 ファイル:
- **[cc_ml_design_spec.md](cc_ml_design_spec.md)** — Phase 別設計仕様・合否基準・drift 対処方針
- **[WORKFLOW.md](WORKFLOW.md)** (本ファイル) — 現フェーズ + 次のタスク + セッション確定事項
- **[.claude/rules/phase_compliance_checklist.md](.claude/rules/phase_compliance_checklist.md)** — Phase 別着手前チェックリスト

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
② 現フェーズ確認（Priority 再構築 ML pipeline・Phase 0=ラベル再生成 / Phase 1=LightGBM 学習 / Phase 2=精度判定 / Phase 3-a/3-b=ハイパラ調整 / Phase 4-a=クラスタリング / Phase 4-b=Exit 設計 / Phase 5/5-b/5-c=Replay / Phase 5-d=POS_SIZE 再計算 / Phase 5-e=Funding 控除 / Phase 6-a/6-b=本テスト / Phase 7-a=Bot 統合準備 / Phase 7-b〜e=Bot 実装/デモ/本番 のどこか明示）
   ※ 2026-05-13 leak 修正後は Phase 0 (ラベル再生成) から再開・Phase 1〜7-a 旧成果は無効
③ 当該 Phase の前提条件（K 窓 1h/2h/4h/8h・LONG/SHORT 同時・期間分割: train 2021-04〜2024-12 + valid 末尾10% + 仮テスト 2025 + 本テスト 2026 Q1・評価軸: train RMSE / Entry predicted MFE/MAE 比 / Exit pnl_median）を再確認
④ [Step 0 D] Phase 完了後の $60/day 到達可能性: YES / NO / 試算未済
   ※ leak フリー再学習中 (Phase 0〜5 完了前) は「試算未済 (Phase 5-c Replay で初めて判定)」と書いてよい
   ※ この 1 行が出るまで提案・分析を開始しない
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

## 設計思想（絶対不変）

### Priority 構築方針（2026-05-11 大方針転換）
- **regime 判定先行は廃止**（精度天井 + 情報密度不足 + 時間軸ズレで凍結）
- 5m bar × 1,432 指標 × 未来 MFE/MAE で **Entry 規則を網羅探索**して Priority を構築
- 既存 P1-P24 は改修せず**ゼロから再設計**
- 複数 Priority を並立させて**リスク分散**（regime 単位の振り分けではなく独立 Priority）
- 最終検証: 365d Replay で NET 評価（仮テスト 2025 + 本テスト 2026 Q1 単一 chronological holdout・月次 ≥ $1,900 全月クリア）

### 実装方針
- 全 Priority: 5m 足ベース・MTF 指標（5m/15m/30m/1h/4h/1d）を Entry 条件に組込み可
- ポジションサイズ上限: 0.12 BTC/trade（増加禁止）
- 上限内での Priority 別配分は自由（例: P23=0.06、P3=0.01）
- 複数 Priority 並立の目的: リスク分散。詰まったら「新 Priority 追加」であり「サイズ増加」ではない
- 時間帯フィルターは個別 Priority 最適化では禁止。統合調整フェーズで実施

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

## 🔴 現在のフェーズ（2026-05-16 改訂13・ML 棚卸し11ファイル完了・web_claude_role.md 配置完了）

> **確定事項 (2026-05-14・改訂10)**:
> - K12 LONG refit (commit d9d322c) **維持**確定
> - Phase 2 正式判定 = **改訂後 spec で 4 指標 ALL PASS**
> - 絶対閾値 drift 対処 = **rolling 365 日採用**（まこさん明示承認・2026-05-14）
>   - look-ahead leak verify 済 (`shift(1).rolling(365*288).quantile(0.99)`)
> - **選択肢 5 採用確定**（K × side × q-level・19 有効組合せ）
>
> **⚠️ Phase 4-b/5 v2 = 類型H インシデント (ポジション上限違反) で無効化 (2026-05-15)**:
> - v2 スクリプトが `POSITION_BTC=0.12` を全エントリーに直接掛け → 19 combo 同時発火で合計 **2.28 BTC（規定の 19 倍）**
> - v2 成果物は `_position_violation` サフィックスにリネーム済み（results/ 配下 4 ファイル）
> - 詳細: `false_positive_incident_policy.md` §3 #8
>
> **Phase 4-b/5 v3 実行済み (2026-05-15)**:
> - スクリプト: `scripts/priority_rebuild/run_phase4b_phase5_rolling_option5_v3.py`
> - 修正1: trailing exit → `sim_trailing_1btc()` (raw per 1 BTC・POSITION_BTC 乗算なし)
> - 修正2: 動的ポジションサイジング `size = remaining / n_sim`（aggregate ≤ 0.12 BTC 保証）
> - **sum_verify_max = 0.12000000 BTC ✅ (§0-2 assertion 通過)**
> - Phase 4-b 成果物: `results/priority_rebuild/ml_phase4_b/cluster_best_exit_option5_v3.csv` (19行)
> - Phase 5 結果: **total PnL = -$985.35（全12ヶ月マイナス → Phase 5 不合格）**
>   - no_trade (position_limit): 86.2% (70,146件) がポジション枠不足でブロック
>   - 根本原因: K96 combo が 8h 保有し続け 0.12 BTC を独占 → 後続発火が全滅
>   - 公式 source: `results/priority_rebuild/ml_phase5/phase5_summary_v3.json`
>
> **Priority vs ML 1432 棚卸し完了 (2026-05-15)**:
> - 完了報告: `.claude/instructions/2026-05-15_priority_vs_ml_stocktake_completion.md`
> - 未学習指標 8件中 5件が Priority の主軸: RCI(7/9/52)・RSI(21)・RSI_slope・BB_slope・Stoch(5m)
> - まこさん仮説「ML が手動 Priority より狭い範囲しか学習していない」→ **定量的に確認**
>
> **ガバナンス文書整備完了 (2026-05-15・commit a8aa804)**:
> - `.claude/rules/false_positive_incident_policy.md` 正本配置（150行）
> - `.claude/rules/web_claude_self_check.md` 最新版（140行）に更新
>
> **ML 完全棚卸し完了 (2026-05-16)**:
> - 出力先: `results/priority_rebuild/inventory_2026_05_16/` (11ファイル)
> - 指示書: `.claude/instructions/2026-05-16_ml_current_state_inventory.md`
> - 完了報告: `.claude/instructions/2026-05-16_ml_current_state_inventory_completion.md`
> - commit: d44e48b
> - 主要実測値: Phase 5 v3 -$985.35 / 0/12ヶ月合格 / ML カバレッジ 未学習8件 / 1432指標 145ファミリー
>
> **ガバナンス文書追加 (2026-05-16)**:
> - `.claude/rules/web_claude_role.md` (v2・278行) 配置 / commit 60d34ca
>
> **次のタスク**:
> 1. **Web Claude が棚卸し11ファイルを読む**: `results/priority_rebuild/inventory_2026_05_16/` を同期 → Layer 1+2 計画書ドラフト着手
> 2. **特徴量追加判断**: build_labels.py に RSI(21)/RSI_slope/BB_slope/stoch_5m/RCI(7/9/52) を追加するか → まこさん判断
> 3. **Phase 0 再実行**: 特徴量追加確定後 → Phase 1〜5 再実行
> 4. **Layer 1+2 計画書**: 棚卸し + 特徴量追加方針が揃ったら Web Claude が計画書ドラフト

---

## 🔴 旧現フェーズ表記 (2026-05-14 改訂7・参考)

> # ⚠️ **leak 修正完了 / Phase 1〜7-a 数値は依然として無効** ⚠
>
> 2026-05-13 に発覚した未来データ参照 leak (`structure_features.py:_detect_fractals` の j±2 未来参照) について、**2026-05-13 セッション内で修正完了**。
>
> **修正内容** (2026-05-13):
> - `_detect_fractals` を**返り値 4 配列に拡張** (`is_res, is_sup, pivot_high, pivot_low`) + ピボット確定タイミングを **j+2 バー後ろシフト**
> - `is_res[i]=True` のとき `pivot_high[i] = h[i-2]` (i 時点で確定済みの過去データのみ参照)
> - `compute_c1_features` / `compute_c4_v2_features` の使用箇所 (`h[start:end][is_res[start:end]]`) を `pivot_high[start:end][is_res[start:end]]` に置換
> - 検証: 旧 fractal 検出位置 [3,14,26] → 新 [5,16,28] へ +2 シフト確認 / pivot_high[i] == h[i-2] 完全一致確認
>
> **leak 監査範囲** (2026-05-13 実施):
> - 監査対象 5 ファイル (build_labels.py / shape_features.py / structure_features.py / analyze_regime_label_features.py / analyze_vshape_indicators.py)
> - 4 種 grep (負shift / center=True / j+1/j+2 / future/forward) + 構造的指標個別 verify (Pivot / Volume Profile / Donchian / Ichimoku 等)
> - **新規 leak は fractal の下流 2 関数のみ・他は全て leak フリー確認済み**
>
> **依然として無効** (再学習が必要):
> - Phase 1 (LightGBM × 16 ラベル) 〜 7-a (Bot 統合準備) の全成果 — leak 由来データで学習されたため
> - 仮テスト 2025 / 本テスト 2026 Q1 の月次 PnL / 合格判定
> - Phase 5-d (ポジションサイズ正解) / 5-e (Funding 控除) — 元数字が leak 由来のため
>
> **次セッションでの再開手順**:
> 1. WORKFLOW.md のこの警告ブロックを再読
> 2. [feedback_ml_leak_mandatory_check.md](~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_ml_leak_mandatory_check.md) (memory) で leak 4 点チェック手順を確認
> 3. [results/priority_rebuild/leak_incident_20260513.md](results/priority_rebuild/leak_incident_20260513.md) で全 14 件のミス記録 + 修正完了状況を読む
> 4. ✅ leak 由来の既存成果物を `archive/leak_invalid_20260513/` へ移動完了 (commit f1948e4)
> 5. `build_labels.py` で 1,432 指標 × 5y × 5m データを再生成
> 6. Phase 1 LightGBM × 16 ラベル を再学習 → 1 ラベル目完了直後に `feature_importance_top20` を即時 review (L-179 防止策)
> 7. Phase 2 → 7-a を順次再実行
> 8. **「Phase 7-a 完了 → Phase 7-b 着手」の幻の上で再スタートしない** (再学習結果を 1 段ずつ検証)

**フェーズ: Priority ゼロから再構築 — ML パイプライン v2 (leak フリー再構築)**
**regime 判定研究: 🧊 凍結**（素材転用のみ・新規調査停止）

設計詳細・段階別仕様は **[cc_ml_design_spec.md](cc_ml_design_spec.md)** が正本。進捗・確定事項は本ファイル (WORKFLOW.md)、着手前チェックは **[phase_compliance_checklist.md](.claude/rules/phase_compliance_checklist.md)** を参照。(priority_rebuild.md は旧 A-1〜D framework・凍結・参照のみ)

### 方針転換の背景（要約）

- regime 精度天井（v14 56% / stage3 33%）+ regime label 情報密度低 + 時間軸ズレ（持続 16-28h vs trade 15min）
- → regime 研究で蓄積した 1,432 指標素材を Priority Entry 規則の最適化に転用

### Phase 別フロー（概要のみ・詳細は [cc_ml_design_spec.md §5](cc_ml_design_spec.md)）

> ⚠️ 旧 framework「段階 A-1〜D」は ML pipeline 切替で 2026-05-13 廃止。
> A-1 → Phase 0 に統合 / A-2 (k=2 探索) は ML 不合格時の保険として未着手・cc_ml_design_spec §0 / A-3〜D → Phase 1〜7 に再編。

| Phase | 内容 | ステータス (2026-05-14 更新) |
|---|---|---|
| **Phase 0** | ラベル再生成 (5m × 1,432 指標 × 未来 MFE/MAE) | ✅ **完了** (2026-05-13 leak フリー) |
| Phase 1 | LightGBM × 16 ラベル × デフォルトハイパラ | ✅ **完了** (2026-05-14 / 141 分 / 全 16 ラベル異常なし / BL top20=0 件) |
| Phase 1-refit | K12 LONG num_leaves=15 部分採用 (監査懸念1 入力段階解消) | ✅ **完了** (2026-05-14 / 23.5 分 / +0.70pp 上方修正・採用判定 PASS / commit d9d322c) |
| Phase 2 | 精度判定 (仮テスト 2025 で 4 指標合格条件・改訂後 spec) | ✅ **完了** (2026-05-14 / 改訂後 spec PASS q99 加重 +21.28pp / 7/8 positive / commit 0ffd326 + d9d322c) |
| Phase 3 trial | 短期試行 (K 窓別 num_leaves・案 G 検証) | ✅ **完了** (2026-05-14 / パターン B 改善小・改訂後 spec で悪化 / 案 G 正当性確定 / commit a5dad18) |
| Phase 4-a | k-means クラスタリング (Entry 性質分類) | ✅ **完了** (2026-05-14 / 1.45 分 / k=3 採用 silhouette 0.510 / 全 cluster K12 LONG q99 ≥100 / K96 SHORT q99 全 cluster trade 可 / commit b88b9fa) |
| Phase 4-b | Exit 設計 (cluster × K × side 最適 Exit) | ⚠️ **v3 実行済み・trailing exit 修正・ただし Phase 5 v3 不合格のため設計見直し必要** |
| Phase 5/5-b/5-c | 365d Replay (cap なし → FIFO cap → 質駆動 cap) | ❌ **v3 不合格 (total PnL -$985・全12ヶ月マイナス)・特徴量追加後に再実行** |
| Phase 5-d | ポジションサイズ正解版で再計算 (0.12 BTC = 合計上限) | ✅ **v3 に統合済み** (aggregate ≤ 0.12 BTC の dynamic sizing) |
| Phase 5-e | Funding Rate 控除 (8h 毎・0.01%) | 再実行 待ち (Phase 5 合格後) |
| Phase 6-a/6-b | 本テスト 2026 Q1 (月次 NET ≥ $1,900 全月) | 再実行 待ち (Phase 5 合格後) |
| Phase 7-a | Bot 統合準備 (推論再現性検証) | 再実行 待ち |
| Phase 7-b | ML Decider 実装 (cat/ml_models.py 等新規) | 未着手 |
| Phase 7-c | run_once_ml.py 実装 (ALLOW_LIVE_ORDERS=False 維持) | 未着手 |
| Phase 7-d | デモトレード起動 (paper_trading=True 確認後・**まこさん明示 GO 必須**) | 未着手 |
| Phase 7-e | デモ結果 → 本番判断 | 未着手 |

ML 不合格時の保険として cc_ml_design_spec.md §0 で k=2 全探索を並走可と明示・未着手。

### Phase 6-b 基準 lock (cc_ml_design_spec §1.6.1 メタルール準拠・2026-05-14 案G で追加)

**実行前最終確定**: Phase 6-b 実行前に以下を最終確定し、実行後の緩和は許容しない:
- 月次 NET ≥ $1,900 (固定)
- 全 3 ヶ月クリア必須 (平均・中央値・1ヶ月クリアへの緩和禁止)
- cap 値・Exit 設定・他全パラメータ Phase 6-b 着手指示書発行時点で固定

**基準変更の禁止**: 結果確定後の基準緩和 ($1,900→$1,500・全月→2/3月・等) は
cc_ml_design_spec §1.6.1 メタルール違反。Phase 6-b 不合格時は §6 採否判定通り
「不合格→原因分析→ハイブリッド/設計見直し」または「廃案」のいずれか。

### 凍結時点の素材転用一覧

regime 研究は凍結したが、以下の素材は Priority 再構築フェーズで **再利用する**:

| 用途 | 凍結時点の成果物 |
|---|---|
| 1,432 列の指標素材 | [pruned_column_list.json](results/regime_label_analysis/pruned_column_list.json) + 計算ロジック [analyze_regime_label_features.py](scripts/regime/analyze_regime_label_features.py) / [analyze_stage1*_meta.py](scripts/regime/) / [shape_features.py](scripts/regime/shape_features.py) |
| k=2 全探索フレーム (🧊) | [stage2_combination_search.py](scripts/regime/stage2_combination_search.py) のフレーム流用（評価関数だけ MFE/MAE に差し替え）— ML pipeline 採用で**実際には未使用**・ML 不合格時の保険として残置 |
| MTF 集計ロジック | stage1 の MTF resample / attach コード（5m/15m/30m/1h/4h/1d） |
| ダッシュボード | タブ⑬ レジーム持続分布 / タブ⑭ trade×境界 整合性検証（参考表示） |

### Priority 再構築フェーズの引き継ぎ素材

- 持続分布（参考）: [regime_label_run_length.md](results/regime_research/regime_label_run_length.md)
- 4h 教師ラベル median 28h / v14 1h median 16h（regime は時間〜日オーダー）
- 365d Replay ベースライン: 1,157 trade / NET $4,506 / **$12.34/day** → 目標 $60/day まで 5 倍ギャップ

### 1-A 拡張詳細（v2・68 指標 × 8 カテゴリ）

| カテゴリ | 指標数 | N | 追加内容 |
|---|---:|---:|---|
| 1_trend | 18 | 7 | macd_line / macd_signal / macd_hist_change 追加 |
| 2_momentum | 11 | 5 | momentum_10b / div_rsi14_14b / div_macd_14b 追加 |
| 3_volatility | 12 | 10 | zscore_return_20b/50b / abs_return_3sigma_20b / donchian_width_pct_20 追加 |
| 4_adx_dmi | 4 | 14 | di_plus / di_minus 追加（情報落ち分解）|
| 5_volume | 6 | 6 | 変更なし |
| 6_priceaction | 11 | 1 | new_high/low_streak_5b / pinbar_top/bottom / bullish/bearish_engulfing 追加 |
| 7_position | 5 | 1 | donchian_position_20 追加 |
| 8_mtf（新カテゴリ）| 1 | 1 | mtf_slope_align_3way（短中長 slope 符号一致度・単軸内 MTF 模倣）|
| **合計** | **68** | — | 1-A 本実装 ★合計 540（v1 419 比 +121）|

### regime v14 判定（🧊 凍結時点の参考値）

- v14.4 性能（凍結時点）: 24 サンプルヒット率 7/24 (29.2%) / 2025 年一致率 56.6%
- 詳細: [`archive/regime_research/v14_judgment_spec.md`](archive/regime_research/v14_judgment_spec.md)
- **新規運用には使用しない**。凍結後の参考データ。

凍結ステータス・素材転用一覧は **[`regime_research.md`](.claude/memory/regime_research.md) §0** を参照。

---

## 2026-05-14 セッション成果物一覧 (Phase 4-a 検証 + 構造改善)

| 指示書 / 完了報告 | 内容 |
|---|---|
| `2026-05-14_phase4a_k2_revisit.md` + completion | k=2 vs k=3 比較 (k=2 stability 優位だが両方 35-44pp) |
| `2026-05-14_phase4a_normalize_reselect.md` + completion | 入力正規化 + k=2〜6 再選定 (k=2 のみ 16.15pp で要警戒帯) |
| `2026-05-14_clustering_alternatives_eval.md` + completion | 選択肢 1/4/5/6/7 評価 + K96 SHORT q99 test 0 件問題発覚 |
| `2026-05-14_phase2_revalidate_post_refit.md` + completion | refit 後 Phase 2 再判定 (§8 違反発覚) |
| `2026-05-14_phase2_script_fix_and_structural.md` + completion | run_phase2_precision.py 改修 + 構造改善 5 項目 |
| `2026-05-14_filename_uniqueness_rule.md` + completion | ファイル名一意化ルール (`*_PREREFIT.csv` 等) |
| `2026-05-14_threshold_drift_eval.md` + completion | 絶対閾値 drift 対処方針評価 (rolling 365 で +9.13pp) |

| ルール / 教訓 | 内容 |
|---|---|
| WORKFLOW.md 「成果物ファイル名の一意化ルール」 | 比較される成果物は識別子付与 |
| WORKFLOW.md 「公式判定 source の定義」 | phaseX_summary.json のみが公式 |
| cc_ml_design_spec.md §1.6.1 末尾「公式判定 source ルール」 | spec 改訂時 script 改修連動必須 |
| `.claude/rules/web_claude_self_check.md` (新規) | Web Claude 用 チェック A/B |
| `results/priority_rebuild/spec_script_consistency_20260514.md` | 7 項目 consistency check (2 未実装) |
| memory `feedback_pre_execution_premise_check.md` (新規) | 着手前 4 項目 verify |
| lessons_active.md L-183〜L-186 | §8 違反・spec/script 乖離・ファイル名・premise check |
| run_phase2_precision.py 改修 | CRITERION_1/4 → 6 + df_q99 抽出 (案 G 改訂後 spec 実装) |
| `2026-05-14_session_handoff_v5.md` + completion | セッション引き継ぎメモ + drift 確定 spec 明文化 |
| `handoff_to_web_claude_v5_session_20260514.md` | 次セッション向け handoff メモ (7 セクション) |
| **整合性修正 cb56a2d + 7c6b5ef** | L-181 違反解消: 旧 次のタスク 降格 + priority_rebuild.md 唯一の正本 表記廃止 |

## セッション確定事項（2026-05-14 時点・項目2/3 は 2026-05-15 改訂11 で更新済）

1. ✅ K12 LONG refit (commit d9d322c) **維持**確定 (audit#7 影響限定的)
2. ✅ 絶対閾値 drift = **固定維持 + K96 SHORT q99 除外**確定 (audit#9) 　🧊 旧確定事項（2026-05-14）・2026-05-15 改訂11 で rolling 365日採用に更新済（→ §🔴現在のフェーズ L273）
3. ✅ 次のタスク = **選択肢 5 vs 7 の再評価** (監査経路を通す・handoff §3 参照) 　🧊 旧確定事項（2026-05-14）・2026-05-15 改訂11 で更新済（→ §🔴現在のフェーズ L273）

---

## 🧊 旧 次のタスク（2026-05-14 改訂23・Phase 4-a k=3 採用前提・参考）

> ⚠️ **この記述は旧 Phase 4-b 直行パス（Phase 4-a 完了 → Phase 4-b 着手）を想定したもの。**
> 2026-05-14 セッション末の drift 対処確定 (固定維持 + K96 SHORT q99 除外) 後、
> 次のタスクは **「選択肢 5 vs 7 の再評価」** に更新済み (§🔴 現在のフェーズ L273 参照)。
> 本セクションは旧経緯の参考記録として保持する。Phase 4-b 着手時は L273 の最新指示を使うこと。

**Phase 4-b: cluster × K × side ごとの最適 Exit (固定 TP / トレーリング / 時間 Exit) をデータ駆動で選択。**
**phase_compliance §4b.4-b Exit 約定率 ≥ 12% 必達 / 採用 ML: Phase 1 + K12 LONG refit / 採用クラスタ: k=3 / 入力: predictions_train_2021_2024_k12long_refit.parquet + predictions_test2025_clustered.parquet。**

### 主要参照リソース (Phase 4-b 着手指示書発行時)

| パス | 内容 |
|---|---|
| .claude/instructions/2026-05-14_phase4a_clustering_completion.md | Phase 4-a 完了報告 (k=3 採用根拠・cluster 性質・サンプル数チェック) |
| .claude/instructions/2026-05-14_phase1_k12long_refit_completion.md | K12 LONG refit 完了報告 (採用判定 PASS) |
| results/priority_rebuild/ml_phase4_a/cluster_profile.csv | 16 予測値 × 3 cluster 平均 |
| results/priority_rebuild/ml_phase4_a/predictions_test2025_clustered.parquet | test 2025 cluster 付き予測値 |
| results/priority_rebuild/ml_phase4_a/scaler_train_2021_2024.joblib | StandardScaler artifact |
| results/priority_rebuild/ml_phase4_a/kmeans_k3_train_2021_2024.joblib | KMeans artifact |

### Phase 4-b 留意事項 (Phase 4-a 完了報告から)

1. **cluster 1 test 不均衡**: train 48.7% → test 4.5% で大幅縮小 (2025 年は低ボラ SHORT 有利局面が train 期間より稀) → cluster 1 ベース戦略の Phase 5 月次合計影響を要監視
2. **K96 SHORT q99 構造的問題**: train ベース全 cluster trade 可だが test 2025 で 2025-01/09 暴騰局面集中で逆行 → 時期別 no-trade 検討も必要
3. **K12 LONG num_leaves=15 効果**: 全 cluster で q99 サンプル数 ≥ 100 確保

---

## 旧 次のタスク (Phase 2・参考)

**Phase 2: predictions_test2025.parquet を使って仮テスト 2025 で 4 指標合格条件を判定。全 4 指標 PASS なら Phase 3 へ・1 件以上 FAIL ならまこさん協議 (cc_ml_design_spec §1.6 / 2026-05-14 改訂)。**

### このセッションで完了した事前準備 (2026-05-13)

| 項目 | 内容 |
|---|---|
| exchange_spec.md | Bitget USDT-FUTURES BTCUSDT スペック正本化 (Maker 0.00014 確定) |
| phase_compliance_checklist.md | §未確定項目 Maker fee 行を確定値に更新 / §5.4 更新 / §5.6 削除 |
| CLAUDE.md | 必読リストに exchange_spec.md 追加 |
| WORKFLOW.md | Maker fee 確認ステップを削除 (確定済) |
| run_lgbm_phase1.py | ハイパラ更新 (下記) + per-label iter log + early save |
| label_distribution_stats.json | 16ラベル分布算出 → results/priority_rebuild/ml_phase1/ 保存済 |
| Step 0-1〜0-5 | 全完了 (引用/整合性 verify/scan_leak/checklist更新/分布算出) |

#### run_lgbm_phase1.py 更新内容 (2026-05-13)

| パラメータ | 旧値 | 新値 |
|---|---|---|
| learning_rate | 0.05 | 0.02 |
| n_estimators | 2000 | 5000 |
| n_jobs | -1 | 1 (再現性・懸念10) |
| min_data_in_leaf | (なし) | 100 |
| feature_fraction | (なし) | 0.7 |
| bagging_fraction | (なし) | 0.8 |
| bagging_freq | (なし) | 5 |
| reg_lambda | (なし) | 0.1 |
| bagging_seed | (なし) | 42 |
| data_random_seed | (なし) | 42 |
| feature_fraction_seed | (なし) | 42 |

追加機能:
- per-label `lgbm_{label}_iteration_log.csv` 保存 (bit-exact 再現性確認用)
- 1 ラベル目完了時に `feature_importance_top20.csv` を early save (dry-run 証跡用)

### Phase 0 旧版サマリー (⛔ 2026-05-19 archive・USD 絶対値 + leak 由来で無効化)

旧 USD 絶対値 + 16 ラベル版 (build_labels.py 出力・2026-05-13 生成) は以下の理由で 2026-05-19 archive 行き:
- 価格非依存性違反 (USD 絶対値ラベル・BTC 価格変動で分布シフト)
- fractal leak (L-179) 由来の数値も含む

| 旧 parquet (archive 済) | 行数 | サイズ | 期間 |
|---|---|---|---|
| archive/labels_mfe_mae_train_2021_2024.parquet | 394,753 | 1.02 GB | 2021-04-01 07:55:00 〜 2024-12-31 23:55:00 |
| archive/labels_mfe_mae_test_2025.parquet | 105,120 | 0.30 GB | 2025-01-01 00:00:00 〜 2025-12-31 23:55:00 |
| archive/labels_mfe_mae_test_2026_q1.parquet | 25,823 | 0.07 GB | 2026-01-01 00:00:00 〜 2026-03-31 15:50:00 |

**新版 (Phase 0 v3・実行待ち)**: `build_labels_pct.py` で pct ラベル × 28 + メンテ時間帯フラグ + K_BARS=[6,12,24,48,96,144,288] で再生成。出力: `labels_mfe_mae_pct_*.parquet`。

- 指標列 1,432 完全一致 / fractal 修正後・3 期間とも 5min ギャップで完全分離
- 入力 CSV: `data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv` (Bitget USDT-FUTURES history-candles から取得・525,887 rows)
- 旧 Binance CSV は data/ に残置 (凍結 regime 研究 25 ファイルの実績保持)

### 並行タスク 1-5 改修完了内容 (commit 予定)

| タスク | ファイル | 内容 | 解消 |
|---|---|---|---|
| 1 | run_lgbm_phase1.py | 1 ラベル目完了直後 feature_importance top20 review + 2 段階 gate (leak hit / ALLOW gate) | L-179 物理化 |
| 2 | run_lgbm_phase1.py / run_lgbm_phase3_b.py | train 期間 predictions_train_2021_2024.parquet 追加保存 | Phase 4-a 入力 |
| 2 | run_phase4_a.py | fit/apply 分離 (train で fit, test は transform/predict のみ) + artifact 名 train_2021_2024 | L-183 #3 |
| 2 | run_phase4_b.py | cluster_best_exit 選定を train PnL で idxmax + TIME_EXIT_GRID K×2 削除 + test apply 分離 | L-183 #4 |
| 3 | run_phase5.py | BEST_PATH を cluster_best_exit_FROM_TRAIN.csv に変更 | パス整合 |
| 3 | run_phase5_c.py | sort_values を entry_ts 昇順 + 同 timestamp 内 pred_ratio 降順 | L-182 |
| 4 | run_phase6_b.py | scaler/km の再 fit 削除 → Phase 4-a artifact (joblib) load + "test" 文字列禁止 assertion + OHLC_CSV を Bitget 新 CSV に切替 | L-183 #13 |
| 5 | save_ml_artifacts.py | Phase 4-a artifact コピー方式に転換 + 命名 assertion | L-183 #13 後段 |
| 5 | verify_ml_inference.py | artifact パス → train_2021_2024 + "test" 文字列禁止 assertion + 比較先を cluster_labels_test2025_k4 に修正 | L-183 検証 |
| 補助 | .claude/rules/phase_compliance_checklist.md | Phase 0/1/4-a/4-b/5/5-d/5-e/6-b/7-c のチェックリスト + 暫定値テーブル | 正本化 |
| 補助 | scripts/data/download_bitget_5y.py | Bitget USDT-FUTURES 5y データ取得 + 整合性 verify | データ |
| 補助 | data/BTCUSDT-5m-bitget-2021-04-01_2026-03-31_5y.csv | Bitget 5y CSV (525,887 rows) | データ |

### 次セッション最初にやること (Phase 2: 精度判定)

> **Phase 1 完了済み。Phase 2 着手。**
> `predictions_test2025.parquet` は `results/priority_rebuild/ml_phase1/` に存在する (105,120行 × 17列)。
> `entry_thresholds.json` / `training_summary.csv` も保存済み。

1. WORKFLOW.md §🔴 現在のフェーズ + §次のタスク を再読
2. cc_ml_design_spec.md §Phase 2 精度判定基準を確認
3. **Phase 2: 仮テスト 2025 で 4 指標合格条件判定 (cc_ml_design_spec §1.6 / 2026-05-14 改訂)**
   - `predictions_test2025.parquet` (MFE/MAE 予測値 × 105,120行) と `labels_mfe_mae_pct_test_2025.parquet` (実際の MFE/MAE pct) を照合 ※ 旧版 `labels_mfe_mae_test_2025.parquet` は archive 済 (2026-05-19)
   - q90/q95/q99 閾値 × K12/24/48/96 × LONG/SHORT = 24 組合せ別に評価
   - 4 指標: ①q99 net_quality (加重平均 > +10pp かつ 20/24 組 > 0) / ②net_quality 最小値 > -50pp / ③valid_rmse/label_std (14/16 ラベル < 1.5) / ④mean_real_MFE/MAE (20/24 組 > 1.0)
   - 全 4 指標 PASS → Phase 3 へ / 1 件以上 FAIL → まこさん協議 (自動 k=2 切替なし)
4. 動的 verify (Phase 4 以降用・持ち越し):
   - Phase 4-a 実行後 `ls results/priority_rebuild/ml_phase4_a/*.joblib` (期待: `*train_2021_2024*` のみ・`*test*` 不在)
   - Phase 4-b 実行後 `cluster_best_exit_FROM_TRAIN.csv` の (cluster, K, side, exit_type) unique 列挙
   - Phase 5 実行直前/直後の merge 行数 + 突合

### Phase 1 達成サマリー (✅ 2026-05-14 leak フリー完了)

| 成果物 | 内容 |
|---|---|
| 16 LightGBM モデル | results/priority_rebuild/ml_phase1/models/ × 16 ファイル (155KB〜981KB) |
| predictions_test2025.parquet | 105,120行 × 17列 (16予測値+close) |
| predictions_train_2021_2024.parquet | 394,753行 × 17列 (Phase 4-a 入力・L-183 対応) |
| feature_importance_top20.csv | 16ラベル × top20 |
| training_summary.csv | 16ラベル × train/valid RMSE / best_iter / 判定 (全16✅) |
| entry_thresholds.json | K窓別 q90/q95/q99 閾値 |
| label_distribution_stats.json | 16ラベル mean/std/p50/p90/p99 |

- BL top20 ヒット: **全16ラベル 0件** ✅
- BL top21-50: support_distance_* / nearest_level_touch_count_* が一部出現 → Defense in Depth 記録継続
- bit-exact 再現性: ✅ (sha256 完全一致・n_jobs=1)
- 所要時間: ~141 分 (Step A 11分 × 2 + Step B 119分)

### 達成サマリー（⛔ leak 由来・全数値無効・2026-05-13）

> 以下は 2026-05-13 leak 発覚前の到達点。fractal j±2 未来参照を学習データに混入させたため、**全数値無効化**。leak フリー再学習後に再評価する。
> 構造的洞察 (time_exit N=K×2 が支配解 / 質駆動 cap が FIFO より優れる 等) は valid な可能性があるが、**数値裏付けは再学習結果を待つこと**。

| 指示書段階 | 当時報告 (⛔ 無効) | 主要数値 (⛔ 無効) |
|---|---|---|
| Phase 1 | ✅→⛔ | LightGBM × 16 ラベル × デフォルトハイパラ・51.8 分 |
| Phase 2 (精度判定) | ✅→⛔ | q99 net_quality +80.65pp |
| Phase 3-a (一律 num_leaves=15) | ✅→⛔ | q99 +99.91pp |
| Phase 3-b (K 窓別 num_leaves) | ✅→⛔ | q99 +110.75pp (採用 ML だったが leak 由来) |
| Phase 4-a (k-means k=4) | ✅→⛔ | C0 中央/C1 LONG長期/C2 SHORT弱/C3 強SHORT |
| Phase 4-b (Exit 試行) | ✅→⛔ | time_exit N=K×2 bar が支配解 (構造洞察として記録) |
| Phase 5 (no cap Replay) | ✅→⛔ | 月次平均 $166k / 12 ヶ月合格 |
| Phase 5-b (FIFO cap) | ✅/❌→⛔ | 本テスト 2026-02 で破綻 |
| Phase 5-c (質駆動 cap) | ✅→⛔ | 仮 12/12・本 3/3 合格 (構造洞察として記録) |
| Phase 5-d (POS_SIZE 再計算) | ✅→⛔ | cap=1/2/3/5 線形再現 |
| Phase 5-e (Funding 控除) | ✅→⛔ | 8h 毎 0.01% 概算 |
| Phase 6-a (2026 Q1 ラベル) | ✅→⛔ | 25,824 行 × 1,449 col |
| Phase 6-b (本テスト) | ✅→⛔ | 全 cap で 3/3・仮テストの 65-69% 維持 |
| Phase 7-a (Bot 統合準備) | ✅→⛔ | 推論再現性 deterministic (artifact 自体は leak 由来) |

### 旧「次セッション最初にやること」(leak フリー再学習開始版) は完了

→ Phase 0 完了 + 並行タスク 1-5 改修完了。新版 §「次セッション最初にやること (順番・Phase 1 着手)」を上記参照。

### Phase 7-b 以降（leak フリー再学習で 6-b 合格後・参考）

新規ファイル作成 (既存 V9 には触らない):
- `cat/ml_models.py` — 16 LightGBM + scaler + kmeans のロード・推論ヘルパー
- `cat/ml_features.py` — 1,432 指標のリアルタイム計算 (build_labels.py の compute_features_for_tf 流用)
- `strategies/cat_ml_decider.py` — ML ベース判定 (新規 Priority "ML")
- `config/cat_params_ml.json` — ML パラメータ (q95 閾値・cluster best Exit map・cap)
- (Phase 7-c で) `runner/run_once_ml.py` — ML 専用実行エンジン

### Phase 7 全体計画（leak フリー再学習完了後に再起動）

| Phase | 内容 | 所要 | 実弾近接度 |
|---|---|---|---|
| **Phase 0** (次) | ラベル再生成 (leak フリー・build_labels.py) | 2-3h | 0 |
| Phase 1〜6-b (再実行) | LightGBM 再学習 → Replay → 本テスト | 数日 | 0 |
| Phase 7-a (再実行) | offline 推論再現性検証 | 1h | 0 |
| Phase 7-b | ML Decider + パラメータ JSON + dry-run | 1-2h | 0 |
| Phase 7-c | run_once_ml.py 実装 (ALLOW_LIVE_ORDERS=False で起動可能) | 2-3h | 低 |
| Phase 7-d | デモトレード起動 (paper_trading=True 確認後・**まこさん明示 GO 必須**) | 数日 | 中 |
| Phase 7-e | デモ結果確認 → 本番判断 | - | 高 |

### 主要参照リソース

**現方針 (有効・再利用可)**:

| パス | 内容 |
|---|---|
| [cc_ml_design_spec.md](cc_ml_design_spec.md) | Web Claude が作った ML パイプライン仕様書 (現方針) |
| [results/priority_rebuild/indicator_catalogue.csv](results/priority_rebuild/indicator_catalogue.csv) / [.md](results/priority_rebuild/indicator_catalogue.md) | 1,432 指標カタログ |
| [results/priority_rebuild/leak_incident_20260513.md](results/priority_rebuild/leak_incident_20260513.md) | Leak Incident 全記録 + 修正完了状況 |
| [scripts/priority_rebuild/](scripts/priority_rebuild/) | Phase 0〜6 実装スクリプト群 (コード自体は再利用可・出力は再生成必要) |

**⛔ leak 由来・無効 (archive 対象)**:

| パス | 状態 |
|---|---|
| [.claude/memory/handoff_to_web_claude_v4_phase1_7a.md](.claude/memory/handoff_to_web_claude_v4_phase1_7a.md) | ⛔ 数値無効・構造洞察は参考 (banner 済) |
| [memory/project_ml_pipeline_phase1_7a.md](~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/project_ml_pipeline_phase1_7a.md) | ⛔ 数値無効・構造洞察は参考 (banner 済) |
| results/priority_rebuild/archive/labels_mfe_mae_*.parquet (3 ファイル・1.4GB) | ⛔ leak 由来 + USD 絶対値・2026-05-19 archive 済 (`labels_mfe_mae_pct_*.parquet` で再生成必要・build_labels_pct.py) |
| results/priority_rebuild/ml_phase*/ (11 ディレクトリ) | ⛔ 全 Phase 出力・再実行必要 |
| results/priority_rebuild/ml_artifacts/ | ⛔ 統合用 artifact・再生成必要 |

### Step 0 セッション開始時に必読（厳守・順番通り）

1. WORKFLOW.md（このファイル・現フェーズ + 次のタスクのポインタ・現方針の唯一の正本）
2. [CLAUDE.md](../CLAUDE.md) ⛔絶対禁止 / 提案禁止リスト + Phase 0〜7 骨格
3. [cc_ml_design_spec.md](cc_ml_design_spec.md) **ML パイプライン仕様書 (有効)**
4. **[~/.claude/projects/.../memory/feedback_ml_leak_mandatory_check.md](~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_ml_leak_mandatory_check.md)** L-179 ML leak 4 点チェック必須
5. **[~/.claude/projects/.../memory/feedback_doc_verify_before_quote.md](~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_doc_verify_before_quote.md)** L-180 ドキュメント引用前 verify 必須
6. **[~/.claude/projects/.../memory/feedback_design_transition_grep_sweep.md](~/.claude/projects/-Users-tachiharamasako-Documents-GitHub-cat-bitget/memory/feedback_design_transition_grep_sweep.md)** L-181 設計転換時 旧記述 grep sweep (**命令**)
7. [results/priority_rebuild/leak_incident_20260513.md](results/priority_rebuild/leak_incident_20260513.md) **leak 全 14 件ミス記録**
8. [.claude/memory/lessons_active.md](.claude/memory/lessons_active.md) L-179 重点
9. [.claude/rules/core_rules.md](.claude/rules/core_rules.md) MUST/NEVER
10. [.claude/rules/exchange_spec.md](.claude/rules/exchange_spec.md) Bitget 発注仕様
11. **[.claude/rules/false_positive_incident_policy.md](.claude/rules/false_positive_incident_policy.md)** **【最重大・CC/Web Claude 共通正本】虚偽達成・虚偽報告インシデント方針** — 類型 A〜G（look-ahead leak / バックテストトリック / 多重検定 / レジーム依存 / 計算ミス / proxy 偽装 / 読んだふり）・発見時強制手順・防止関所 7 つ（2026-05-15 制定）
12. [.claude/rules/web_claude_self_check.md](.claude/rules/web_claude_self_check.md) 読了ゲート・第〇原則・チェック A/B/C（新版 140 行・audit#12/14 反映・2026-05-15 更新）

---

## 試行禁止リスト

Priority 再構築・設計関連の禁止事項の旧正本 [priority_rebuild.md §6](.claude/memory/priority_rebuild.md) は 2026-05-13 に **🧊 凍結** (旧 A-1〜D framework・参照のみ)。ML pipeline (Phase 0〜7) 体系での禁止事項は [cc_ml_design_spec.md §8](cc_ml_design_spec.md) と本ファイル「行動ルール関連」が現方針の正本。

### 行動ルール関連（恒久）
- ❌ 設計判断を感覚で進める（feedback_quantitative_comparison）
- ❌ ユーザーの感覚発言を採用根拠化する（同上）
- ❌ WORKFLOW フェーズと照合せず脇道に逸れた提案を出す（2026-04-27 教訓）
- ❌ 詳細仕様が来ても目的整合性チェックを省略する（L-165）
- ❌ 着手前 3 項目チェック（粒度・カバレッジ・直接性）を省略する（L-166）

### regime 研究関連（凍結中）

→ 全般凍結。新規試行禁止。詳細は [priority_rebuild.md §6](.claude/memory/priority_rebuild.md) / [regime_research.md §0](.claude/memory/regime_research.md)。

---

## 旧 Priority パラメータ（🧊 凍結・参考用・2026-04-22 時点）

> ⚠️ 旧 Priority(P1/P2/P4/P21/P23/P24) の凍結時パラメータ。Priority 再構築フェーズで**ゼロから再設計**するため**新規利用しない**。
> 既存ロジックの参考・解体時の比較材料として残置。
> 当時の 365d Replay NET 合計: $4,506 / $12.34/day（凍結ベースライン・$60/day 目標まで 5 倍ギャップ）

| Priority | パラメータ |
|---------|-----------|
| P2-LONG | TP_PCT=0.006 / ATR14_MIN/MAX=100/300 / MFE_STALE_GATE=3.0 / HOLD_MIN=90 |
| P23-SHORT | TP_PCT=0.012 / TIME_EXIT_MIN=480 / ADX_MIN/MAX=30/50 / ATR14_MIN=150 / HIGH_ADX_THRESH=40 / STOCH_REVERSE_EXIT_ENABLE=true |
| P21-SHORT | TRAIL_RATIO=0.9 / MFE_GATE_PCT=0.04 / TIME_EXIT_MIN=180 / SL_PCT=0.02 |
| P22-SHORT | TIME_EXIT_DOWN_FACTOR=0.4 |
| P4-LONG | TP_PCT=0.003 / ATR14_MAX=130 |

詳細値は git history（commit fa38ec2 以前）または `config/cat_params_v9.json` を参照。

---

## Replay コマンド（🧊 旧フロー・参考のみ）

> ⚠️ `--regime` オプション付きの旧 Replay コマンドは凍結中。
> 新フローの Replay コマンドは ML pipeline Phase 5 / 6-b 系 (run_phase5*.py / run_phase6_b.py) を使う。

```bash
# 365d Replay（旧フロー・参考のみ・実行非推奨）
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-5m-2025-04-01_03-31_365d.csv --regime
```

凍結ベースライン: 上記コマンドで得た 1,157 trade / NET $4,506 / $12.34/day（[results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv](results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv)）

---

## 引き継ぎリソース（次セッション必読）

### 必読（現方針）
- **WORKFLOW.md**（このファイル・現フェーズ + 次のタスクのポインタ）
- **cc_ml_design_spec.md**（ML pipeline 仕様・合否基準・確定方針の正本）
- **.claude/rules/phase_compliance_checklist.md**（Phase 別着手前チェックリスト）
- ~~.claude/memory/priority_rebuild.md~~（🧊 旧 A-1〜D framework・凍結・参照のみ）
- **CLAUDE.md**（v3-bitget-api-sdk/CLAUDE.md・設計思想・現方針）
- **.claude/memory/lessons_active.md**（直近・L-159〜L-166 を重点）
- **.claude/memory/signal_ledger.md**（シグナル候補・regime マッピング部分は凍結中）
- **~/.claude/projects/.../memory/feedback_early_objection.md**（着手前 3 項目チェック・最新）

### 参照のみ（凍結中）
- **.claude/memory/regime_research.md**（🧊 凍結・§0 参照のみ）
- **.claude/memory/regime_trial_log.md**（🧊 凍結・履歴のみ）
- **.claude/memory/lessons_archive.md**（L-102 以前・必要時のみ）
- **archive/workflow/WORKFLOW_20260427.md**（凍結前のスナップショット）
- **dashboard/index.html**（タブ⑪/⑫ regime 試作 / ⑬ レジーム持続分布 / ⑭ trade×境界 整合性検証）
