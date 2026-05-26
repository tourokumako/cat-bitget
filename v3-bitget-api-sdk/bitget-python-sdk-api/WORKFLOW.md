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

## 監査エージェント（オンデマンド・2026-05-26 改訂 L-218 反映）

**起動タイミング**: 「本当にこの方向で大丈夫か？」「見落としがある気がする」と感じたとき。CP 監査 (CP3.5/CP4/CP5/CP6 等) の定期実施。PM レビュー後に続けて呼ぶことも可。

### 経路 A: CP 大型監査 (別セッション起動・cc_role §1.4.5 適用・推奨)

Critical/Major 判定を伴う本格監査はこちら。同型バイアス回避のため必須。

**手順**:
1. **依頼書作成 (メインセッション CC)**:
   - `.claude/audits/inputs/_template.md` をコピー → `.claude/audits/inputs/2026-XX-XX_<task>_cpN_audit_request.md` にリネーム
   - テンプレ冒頭の **「⚠️ auditor 宣言ブロック」を必ず含める** (削除禁止)
   - 中身を埋める (経緯 / 着手前必読 / 監査対象データ / Q1-QN / 外部検索要請)
   - 依頼書を git commit
2. **別セッション起動 (まこさん)**:
   - VSCode で **新規 Claude Code セッション**を開く (メインセッションは保持・別 process)
   - 以下のように呼びかけ (**フルパス必須**):
     ```
     監査してほしい
     .claude/audits/inputs/2026-XX-XX_<task>_cpN_audit_request.md
     ```
3. **監査実行 (auditor session の CC)**:
   - 依頼書冒頭 auditor 宣言ブロックを読了
   - Plan サブエージェント (`Agent` tool・`subagent_type=Plan`) を cold start 起動
   - Plan agent 所見を受けて結果ファイル `.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md` を Write
4. **メインセッション再開 (まこさん + CC)**:
   - メインセッションに戻り、CC が結果ファイルを Read
   - 結果反映プロセスは「機械的反映」表現禁止 (cc_role §1.5.5 / L-213)・1 件ずつ独立評価

### 経路 B: 軽い意見聞き (メインセッション内 Agent 起動可・cc_role §1.4.5 例外)

Critical/Major 判定を伴わない確認程度はこちら。

**手順**:
1. ユーザーが「監査して」「ちょっと意見聞いて」等と入力
2. メインセッション内で `.claude/auditor_template.md` を読み込み、**統計学・リスク管理・認知バイアス・ソフトウェア工学**の外部基準で評価する（観点は状況に応じて 2〜3 個に絞る）
3. 結果を出力フォーマットで提示 → ユーザーの判断を待つ

### 共通制約

- 監査エージェントは**コードを書かない・実行しない**。外部基準からの指摘のみ
- 最終判断はまこさん
- ChatGPT 等の外部 AI 使用不可 (まこさん課金外)
- 経路 A 実施後は CP 監査一覧表 (本ファイル §CP 監査一覧) に追記必須

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

## セッション終了処理 (2026-05-26 確定・handoff_to_cc_v* 廃止後・L-216)

> **【2026-05-26 重大改訂】** handoff_to_cc_v* は廃止 (L-213/L-214/L-215 で 3 回連続再演した「伝言ゲーム化」経路の物理排除・cc_role §1.4.7)。引き継ぎ情報は **WORKFLOW.md 改訂N active ブロックに集約**。

### セッション終了時に必ず実施 (省略禁止・順序厳守)

1. **lessons_active.md 更新** (本セッション固有教訓のみ・L-XX 追加)
2. **WORKFLOW.md 改訂 N+1 active 新設** (本セクション以下「現在のフェーズ」ブロックを書き換え) + **改訂 N を 🧊 履歴に降格**
   - 改訂 N+1 active には以下を必ず含める:
     - **本セッション完了事項** (commit ハッシュ + 変更ファイル + 主要結論)
     - **次セッション CC 優先順位** (タスク列挙・想定時間)
     - **引き継ぎリソース 3 層構造** (Layer 1 毎セッション必読 / Layer 2 タスク特有 / Layer 3 リファレンス)
     - **CP 監査一覧表更新** (CP 実施時)
     - **目的整合性 1 行宣言** (cc_role §1.4.6・「次タスクが現フェーズの目的に貢献する根拠」)
3. **WORKFLOW.md 肥大化対策**: 改訂 N-5 以前の 🧊 履歴ブロックを `archive/workflow/WORKFLOW_改訂N-5_YYYYMMDD.md` に移送 (1147 行超えたら強制実施)
4. **git commit** (上記 1-3 まとめて)

### handoff_to_cc_v* 廃止の根拠

- 起案 CC = 読み手 CC = 同じ Claude (同型バイアス §1.4 #3) で書いた側の局所判断 (スコープ縮小 / 評価式集中 / etc.) を読み手も素通り
- L-213 (機械的反映同型バイアス) / L-214 (引き継ぎ伝言ゲーム化) / L-215 (5 セッション設計逸脱) で 3 回連続再演
- 改善 1-9 件の形式チェック強化では構造的に止まらない実証
- 過去 handoff v19-v32 は `.claude/instructions/archive/handoff/` に履歴保存 (引用可)

参照: cc_role §1.4.6 目的整合性ゲート / cc_role §1.4.7 handoff 廃止 / lessons_active.md L-215/L-216 / phase_flow_v4_with_recovery.md §6 v5 整合更新

---

## 🔴 現在のフェーズ（2026-05-26 改訂43・**🛑 セッション失敗で終了 (= 2 セッション連続・CC 連続再演 4 件) + 6 工程フロー暫定ベース案 ml_pipeline_baseline_v1.md 文書化 + feedback memory 2 件新設 (cat_v9 改造禁止 / 設計議論前ベースアップ義務) + priority_v9_trade_logic_analysis v2 書き直し (= Replay 365 日データ起点 4 軸) + seven_step_framework / chatgpt_seven_step_origin 「破綻判定済・参照用」降格 + L-231 追加** + 次セッション = まこさん新セッション再開待ち）

> **【現在の正本ブロック・改訂43・2026-05-26 セッション末（CC 連続再演 4 件でセッション失敗・6 工程フロー暫定ベース案として固定）】**
>
> ### 本セッション (2026-05-26 second half) 完了事項
>
> #### 1. 整合性解消 ✅
> - seven_step_framework.md / chatgpt_seven_step_origin.md = 冒頭に「⛔ 破綻判定済・参照用」明記
> - CLAUDE.md Layer 1 必読リストから seven_step_framework.md を削除 → Layer 3 (リファレンス) に降格
> - 「正本」フラグと L-230 破綻判定の矛盾解消
>
> #### 2. priority_v9_trade_logic_analysis.md v1 → v2 書き直し ✅
> - §4.5 = 「市場局面別」誤読表 → 「指標 AND 条件パターン検出器」+ Replay 365 日 Priority 別実績表に置換
> - §5 = 「業界カタログ 7 件思いつき」→ Replay データ起点 4 軸 (regime カバレッジ拡張 / Exit 早期化 / 単価上げ / LONG 系修正) に書き直し
> - §6 = 件数試算 → データ起点 4 経路寄与見積 (合計 +$1,230-1,630/月)
> - §8 = CC 理解状態 → 誤読経緯 + 事実記録 + 次作業候補
>
> #### 3. feedback memory 2 件新設 ✅
> - `feedback_cat_v9_no_modification.md` (= cat_v9 は ML スタートライン参照素材であり改造対象ではない・Replay データから具体改造案を出した瞬間に違反)
> - `feedback_baseup_before_design_discussion.md` (= 設計議論前 KB Read + WebSearch 必須・記憶ベース断定発言禁止)
> - MEMORY.md index 追加済 (= 最重要・命令マーク)
>
> #### 4. ml_pipeline_baseline_v1.md 新規作成 ✅ (= 暫定ベース案文書化)
> - まこさん提示の 6 工程ドラフトを暫定ベース案として 1 字 1 句一致で記録
> - 議論のスタート点・確定事項ではない・CC が「確定」と扱うことを禁止
> - 議論未確定事項を §4 で明示 (= 次セッションで詰める対象)
> - 設計思想 (= Entry/Exit 密接関係・マルチタスク学習理想・連鎖学習現実落とし所) を §3 で記録
>
> #### 5. lessons L-231 追加 ✅ (= 本セッション失敗 4 件 + 改善ルール 5 件)
>
> ### 本セッション CC 失敗パターン (= 連続再演)
>
> 1. **cat_v9 改造発想** (= feedback_cat_v9_no_modification を書いた直後の発言で違反)
> 2. **「議論やめて聞くだけ」提案** (= cc_role §1.5 デザイン責任放棄)
> 3. **「Entry ML 精度上げやすい」記憶ベース断定** (= feedback_no_unverified_assertions 違反)
> 4. **業界整合修正案で 7 工程フレーム再提案** (= L-230 破綻判定済 + 本セッション冒頭で降格作業したフレームを復活)
>
> 詳細は lessons L-231 参照。
>
> ### 次セッション CC 優先順位
>
> 1. **優先 1 — Step 0 + 新規ファイル auto-load 確認**:
>    - **`ml_pipeline_baseline_v1.md`** (= 本セッション新設・6 工程暫定ベース案・必読)
>    - **`feedback_cat_v9_no_modification.md`** (auto-memory・最重要・命令・本セッション新設)
>    - **`feedback_baseup_before_design_discussion.md`** (auto-memory・最重要・命令・本セッション新設)
>    - **`priority_v9_trade_logic_analysis.md` v2** (= 本セッション書き直し・Replay データ起点 4 軸)
>    - **lessons L-231** (= 本セッション失敗パターン + 改善ルール)
>    - その他 Layer 1 必読 (= CLAUDE.md / WORKFLOW.md / lessons 直近 5 件 / cc_role.md / feedback memory 群)
>
> 2. **優先 2 — 6 工程暫定ベース案を 1 工程ずつ詳細詰め**:
>    - 順序: [1] 特徴量計算層 → [2] Entry ML → [3] Position Sizing ML → [4] Exit 多層 ML → [5] Risk 管理 → [6] 運用監視
>    - 各工程で議論前に該当 KB § Read + WebSearch ベースアップ実施 (= [[feedback_baseup_before_design_discussion]] 整合)
>    - 1 ターン 1 論点 (= 並列複数論点禁止・[[feedback_cc_low_perspective_narrow_view]] 整合)
>    - cat_v9 改造発想に流れたら即 STOP (= [[feedback_cat_v9_no_modification]] 整合)
>
> 3. **優先 3 — 各工程の学習対象 / 特徴量 / ラベル / 評価指標を確定**
>
> 4. **優先 4 — 設計確定後の実装着手**
>
> 5. **優先 5 — セッション終了処理** (lessons + WORKFLOW 改訂44 + git commit)
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読・読了ゲート対象)
> - **WORKFLOW.md 改訂43 active** (本ブロック)
> - **CLAUDE.md** (= Layer 1 必読リスト更新済)
> - **`ml_pipeline_baseline_v1.md`** (= 本セッション新設・暫定ベース案・6 工程フロー)
> - **`current_redesign_context.md`** (= 経緯サマリ・SessionStart hook で自動表示)
> - **`priority_v9_trade_logic_analysis.md` v2** (= 本セッション書き直し)
> - **`technical_analysis_knowledge_base.md`** (= テクニカル辞典・1691 行)
> - **`industry_benchmark_knowledge_base.md`** (= 業界相場・420 行)
> - **`step1_regime_design.md` v2.2** (= 工程 1 実装設計書・保留中)
> - **lessons_active.md 直近 5 件** (= L-231 → L-230 → L-229 → L-228 → L-227)
> - **cc_role.md §1.4 / §1.4.5 / §1.4.6 / §1.4.6.1 / §1.4.7 / §1.5 / §1.7**
> - **`feedback_cat_v9_no_modification.md`** (auto-memory・**新規・最重要・命令**・2026-05-26)
> - **`feedback_baseup_before_design_discussion.md`** (auto-memory・**新規・最重要・命令**・2026-05-26)
> - **`feedback_cc_low_perspective_narrow_view.md`** (auto-memory・最重要・命令)
> - **`feedback_priority_starting_line_only.md`** (auto-memory・最重要・命令)
> - **`feedback_writing_style.md`** (auto-memory・最重要)
> - **`feedback_plain_language.md`** (auto-memory・最重要)
> - **`feedback_no_unverified_assertions.md`** (auto-memory・最重要・命令)
> - **`feedback_current_state_verify_before_design.md`** (auto-memory・最重要)
> - **`feedback_no_options_during_discussion.md`** (auto-memory)
> - **`feedback_trade_ml_knowledge_gap.md`** (auto-memory・最重要)
>
> #### Layer 2 (タスク特有)
> - 6 工程詳細詰め時: `cc_entry_logic_self_study.md` v6 (= ⚠️ 7 工程フレーム前提で書かれている点に注意・引用時はフレーム部分を引きずらない・各工程の業界実装パターン部分のみ抽出)
> - 工程 1 議論時: `step1_regime_design.md` v2.2 + `train_hmm_regime.py` + `build_step1_regime_dashboard.py`
> - データ分析時: `results/replay/replay_BTCUSDT-5m-2025-04-01_03-31_365d.csv` (= 1,157 trades・累計 NET $4,506)
>
> #### Layer 3 (リファレンス)
> - `false_positive_incident_policy.md`
> - `exchange_spec.md`
> - `lessons_archive.md` (L-152 以前)
> - **`seven_step_framework.md`** (⛔ 破綻判定済・参照用)
> - **`chatgpt_seven_step_origin.md`** (⛔ 破綻判定済・参照用)
>
> #### データ・環境
> - parquet 3 種 (= Phase 0 v3.1 既存・train_2021_2024 + test_2025 + test_2026_q1)
> - `.venv311` (= hmmlearn 0.3.3 + mlfinpy 0.1.2 + lightgbm 4.6.0 + 他)
> - 旧 Priority 実績: 月 $370 (= cat-bitget **唯一の実利資産**・スタートライン参照・構造的継承 OK・cat_v9 改造禁止)
>
> ### 目的整合性 1 行宣言 (cc_role §1.4.6)
>
> - **次タスク** = (1) Step 0 + 新規ファイル auto-load → (2) ml_pipeline_baseline_v1.md ベースに 6 工程暫定ベース案を 1 工程ずつ詳細詰め → (3) 各工程の学習対象 / 特徴量 / ラベル / 評価指標確定 → (4) 設計確定後の実装着手
> - **現フェーズ目的への貢献根拠** = 本セッションで CC が連続再演 4 件 (= cat_v9 改造発想 / デザイン責任放棄 / 記憶ベース断定 / 7 工程フレーム再提案) を起こしたが、暫定ベース案 ml_pipeline_baseline_v1.md として 6 工程フローを文書化 + feedback memory 2 件新設で再演防止策を強化 + priority_v9_trade_logic_analysis v2 で Replay データ起点 4 軸の事実記録を残した。次セッションは新規ファイル auto-load で CC が暫定ベース案から議論を出発させ、各工程を 1 ターン 1 論点で詰める形に進める。

---

## 🧊 改訂42 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-26 改訂42・**🛑 セッション失敗で終了 + 引き継ぎ資料化 + CC 思考癖 (= 視点低い・視野狭い) 矯正 feedback memory 新設 + 知識ベース 3 ファイル Layer 1 格上げ + L-230 追加** + 次セッション = まこさん新セッション再開待ち）

> **【現在の正本ブロック・改訂42・2026-05-26 セッション末（CC 失敗連発でセッション終了・引き継ぎ資料化）】**
>
> ### 本セッション (2026-05-26) 完了事項
>
> #### 1. 工程 1 (regime) 実装着手 + 視認チェック「精度微妙」で保留 ✅
> - `train_hmm_regime.py` + `build_step1_regime_dashboard.py` 作成 + 実行 → artifact 4 ファイル + dashboard v15 出力
> - 視認チェック結果 = 「精度微妙」(まこさん判断) → **一旦保留** (= feedback_regime_visual_check 整合・最低 10 回調整覚悟)
> - 詳細は lessons L-230 参照
>
> #### 2. ⚠️ seven_step_framework.md / chatgpt_seven_step_origin.md 作成 (= 要再評価)
> - 7 工程フレーム正本化 (= WORKFLOW 改訂 35 active L639-649 由来)
> - CLAUDE.md / WORKFLOW Layer 1 に index 登録
> - ⚠️ **重大課題**: 7 工程フレーム自体が cat-bitget 制約 (= 月 $1,900 / 月 100+ 件必要) と矛盾 (= 3 段階で振り落とすと月 25 件まで減る試算) → **次セッションで再評価**
>
> #### 3. ⚠️ priority_v9_trade_logic_analysis.md 作成 (= CC 理解誤りあり・要修正)
> - 旧 Priority v9 構造分析 (= cat_v9_decider.py 823 行 + cat_params_v9.json 169 行 を CC が構造分析・9 セクション 507 行)
> - ⚠️ **CC 理解誤り**: 「P4 は強上昇トレンド + プルバックを狙う」のように **市場局面別に解釈** していたが、正しくは「全 Priority があらゆる相場を想定・タイミング検出器・マッチした瞬間に発火」が実態 (= まこさん指摘・トレード現場感覚不足)
> - ⚠️ **ML 進化案 7 件は思いつき**: 旧 Priority 実態から導出してない・業界知識ベースで並べただけ・「7 件」の根拠なし
> - **次セッションで修正議論**
>
> #### 4. ✅ CC の悪い癖 (= 視点低い・視野狭い) 矯正 feedback memory 新設
> - `feedback_cc_low_perspective_narrow_view.md` 新規作成 (= 個人 memory)
> - MEMORY.md に index 登録 (= 最重要マーク付き)
> - 内容: 提案前 3 問チェック + 全体構造チェック + 禁止フレーズリスト
>
> #### 5. ✅ 知識ベース 3 ファイル Layer 1 格上げ
> - CLAUDE.md Layer 1 必読リストに以下を追加 (= 読了ゲート対象):
>   - `technical_analysis_knowledge_base.md` (既存・1691 行・テクニカル辞典 + 閾値設計論)
>   - `industry_benchmark_knowledge_base.md` (既存・420 行・業界相場 + 5 レバー定量根拠)
>   - `priority_v9_trade_logic_analysis.md` (新規・507 行・旧 Priority 構造分析・要修正)
> - 目的: 新セッション CC が **トレード知識をインプットした状態で議論開始** できる
>
> #### 6. ✅ lessons L-230 追加 (= 本セッション CC 失敗 7 件 + 改善ルール 5 件)
>
> ### 本セッション CC 失敗パターン (= まこさん指摘で発覚)
>
> 1. ChatGPT 案・業界整合性の鵜呑み (= seven_step_framework.md 正本化)
> 2. 短絡的翻訳・矮小化 (= 「Entry 緩め」→「固定」/「Exit 細かい」→「3 系統」)
> 3. 確認質問乱発 (= デザイン責任転送)
> 4. 目標達成からの逆算思考の欠如 (= 業界フレーム月 25 件で目標未達と気づかなかった)
> 5. 振り落とし型 cascade 盲信
> 6. **視点低い** (= 業界フレーム細部に逃げる癖)
> 7. **視野狭い** (= 個別の細部理解止まり・全体構造把握不足)
>
> 詳細は lessons L-230 参照。
>
> ### 次セッション CC 優先順位
>
> 1. **優先 1 — Step 0 + 知識ベース 3 ファイル全文 read** (= トレード知識をインプットした状態にする・読了ゲート対象):
>    - `technical_analysis_knowledge_base.md` (1691 行)
>    - `industry_benchmark_knowledge_base.md` (420 行)
>    - `priority_v9_trade_logic_analysis.md` (507 行・⚠️ CC 理解誤り要修正・修正対象)
>    - その他 Layer 1 必読 (= CLAUDE.md / WORKFLOW.md / lessons_active.md 直近 5 件・cc_role.md 等)
>
> 2. **優先 2 — feedback_cc_low_perspective_narrow_view.md の運用宣言** (= 毎ターン提案前に 3 問チェック + 全体構造チェック + 禁止フレーズ確認・違反検出時の即 STOP)
>
> 3. **優先 3 — priority_v9_trade_logic_analysis.md の CC 理解誤り修正議論**:
>    - 「市場局面別解釈」→「タイミング検出器・全相場想定」に修正
>    - まこさんと議論しながら CC の理解を深める (= 修正反映 → v2 へ)
>    - ML 進化案 7 件は **白紙化** → 旧 Priority 実態から再導出
>
> 4. **優先 4 — seven_step_framework.md の再評価**:
>    - cat-bitget 制約 (= 件数確保) と矛盾するフレームをどうするか議論
>    - 7 工程フレーム自体を捨てるか・大幅修正するか・部分修正するか
>    - 旧 Priority 構造 + cat-bitget 制約 (= 月 $1,900 / 0.12 BTC / 5 分足) から逆算した新フローを CC が独自設計
>
> 5. **優先 5 — 工程 2 議論再開** (= 優先 3-4 の議論結果を踏まえて):
>    - 必要 Entry 件数 × 1 件 NET の **戦略タイプ別シナリオ** 確定 (= スキャル / 中期 / 長期保持の選択)
>    - その上で Entry / Exit / Position Sizing の構造設計
>
> 6. **優先 6 — 工程 1 視認チェック「精度微妙」のフォロー**:
>    - 一旦保留中・優先 5 の構造確定後に再開
>    - feedback_regime_visual_check (= 最低 10 回調整覚悟) 整合・早計に廃案しない
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読・読了ゲート対象)
> - **WORKFLOW.md 改訂42 active** (本ブロック)
> - **CLAUDE.md** (= Layer 1 必読リスト更新済・3 知識ベース追加)
> - **`current_redesign_context.md`** (= 経緯サマリ・SessionStart hook で自動表示)
> - **`technical_analysis_knowledge_base.md`** (= テクニカル辞典・1691 行・**2026-05-26 Layer 1 格上げ**)
> - **`industry_benchmark_knowledge_base.md`** (= 業界相場・420 行・**2026-05-26 Layer 1 格上げ**)
> - **`priority_v9_trade_logic_analysis.md`** (= 旧 Priority 構造分析・507 行・**2026-05-26 新設**・⚠️ CC 理解誤り要修正)
> - **`seven_step_framework.md`** (⚠️ 要再評価・cat-bitget 制約矛盾発覚)
> - **`step1_regime_design.md` v2.2** (= 工程 1 実装設計書・実装済・保留中)
> - **lessons_active.md 直近 5 件** (= L-230 → L-229 → L-228 → L-227 → L-226)
> - **cc_role.md §1.4 / §1.4.5 / §1.4.6 / §1.4.6.1 / §1.4.7 / §1.5 / §1.7**
> - **`feedback_cc_low_perspective_narrow_view.md`** (auto-memory・**新規・最重要・命令**・2026-05-26)
> - **`feedback_priority_starting_line_only.md`** (auto-memory・最重要・命令)
> - **`feedback_writing_style.md`** (auto-memory・最重要)
> - **`feedback_plain_language.md`** (auto-memory・最重要)
> - **`feedback_no_unverified_assertions.md`** (auto-memory・最重要・命令)
> - **`feedback_current_state_verify_before_design.md`** (auto-memory・最重要)
> - **`feedback_no_options_during_discussion.md`** (auto-memory)
>
> #### Layer 2 (タスク特有)
> - 工程 1 修正時: `step1_regime_design.md` v2.2 + `train_hmm_regime.py` + `build_step1_regime_dashboard.py` + `dashboard/regime_prototype/predictions_v15_*` + `feedback_regime_visual_check.md`
> - 工程 2-7 議論時: `cc_entry_logic_self_study.md` v6 §13-§20 (= 全 7 領域業界カタログ・⚠️ 業界フレーム逃避リスクあり・参考のみ)
> - 旧 Priority 詳細議論時: `strategies/cat_v9_decider.py` (823 行) + `config/cat_params_v9.json` (169 行) + `priority_v9_trade_logic_analysis.md`
>
> #### Layer 3 (リファレンス)
> - `false_positive_incident_policy.md`
> - `exchange_spec.md`
> - `lessons_archive.md` (L-152 以前)
> - `chatgpt_seven_step_origin.md` (= ChatGPT 提案要約・⚠️ 要再評価・参考のみ)
>
> #### データ・環境
> - parquet 3 種 (= Phase 0 v3.1 既存・train_2021_2024 + test_2025 + test_2026_q1)
> - `.venv311` (= hmmlearn 0.3.3 + mlfinpy 0.1.2 + lightgbm 4.6.0 + 他)
> - 旧 Priority 実績: 月 $370 (= cat-bitget **唯一の実利資産**・スタートライン参照・構造的継承 OK)
>
> ### 目的整合性 1 行宣言 (cc_role §1.4.6)
>
> - **次タスク** = (1) Step 0 + 知識ベース 3 ファイル全文 read → (2) feedback_cc_low_perspective_narrow_view.md 運用宣言 → (3) priority_v9_trade_logic_analysis.md の CC 理解誤り修正 → (4) seven_step_framework.md 再評価 → (5) 工程 2 議論再開 → (6) 工程 1 視認チェック再開
> - **現フェーズ目的への貢献根拠** = 本セッションで CC が業界フレーム逃避・視点低い・視野狭い癖を連発し、cat-bitget 制約と矛盾するフレームを「正本」化してしまった。次セッションでこれを修正し、旧 Priority 実態 + cat-bitget 制約逆算で新フローを CC が独自設計する必要がある。トレード知識を Layer 1 格上げ + CC 矯正 feedback memory 新設で運用ルールを強化した。

---

## 🧊 改訂41 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-25 改訂41・**工程 1 (相場の状態判定・レジーム判定) 詳細設計確定 + step1_regime_design.md v2 完成 (= 実装詳細 11 項目全確定) + 経緯サマリ自動 load 仕組み化 (= current_redesign_context.md + SessionStart hook) + 設計提案前 4 問形式義務 (= feedback_writing_style.md) + 対話文義務 (= feedback_plain_language.md) + 業界実証 WebSearch verify 済 14 指標 × 6 時間軸 = 84 次元入力 + HMM 教師なし学習 + Walk-Forward Purged K-Fold 5 fold + オンライン Viterbi 100 時間窓 + L-229 追加**・次タスク = まこさん判断 (= 工程 1 実装着手 or 工程 2 詳細詰め)）

> **【現在の正本ブロック・改訂41・2026-05-25 セッション末（工程 1 詳細設計確定）】**
>
> ### 本セッション (2026-05-25) 完了事項
>
> #### 1. 工程 1 (相場の状態判定・レジーム判定) 詳細設計確定
>
> `step1_regime_design.md` v1 → v2 (= 実装詳細 11 項目全確定・新セッション CC が即実装着手できるレベル):
>
> - 判定間隔 1 時間 / ヒステリシス連続 2 回 (= 2 時間相当) / 3 種類分類 (= 上昇 / 下落 / レンジ)
> - HMM (Hidden Markov Model) 教師なし学習 (= covariance_type=diag / n_iter=100 / tol=0.01 / random_state=42 ・ step1_regime_design.md v2.1 で diag に変更・過学習防止)
> - 入力 14 指標 × 6 時間軸 = 84 次元 (= ベース 2 + トレンド方向性 3 + 移動平均 3 + 一目均衡表 2 + モメンタム 2 + ボラ 2・業界実証 WebSearch verify 済)
> - 業界実証 verify で log_returns + rolling_volatility をベース指標として確定 (= 業界 default として必須・Phase 0 v3.1 に存在しないため新規生成必要・step1_regime_design.md v2.2 §2.12 整合)
> - 前処理 RobustScaler を Pipeline で fold 毎 fit / NaN は学習時 drop (= 約 5% 削除)
> - 評価 Walk-Forward + Purged K-Fold 5 fold / purge 24 時間 / embargo 24 時間 / mlfinpy.PurgedKFold 使用
> - 状態ラベル付け = 1h DI 差中央値で機械的命名 + 妥当性チェック (= レンジの ADX が他より低い)
> - 本番運用 = オンライン Viterbi スライディング窓 100 時間・predict + predict_proba 両方使用
> - 入力ベクトル並び順 = カテゴリ → 指標 → 時間軸
> - artifact = joblib (HMM/Scaler) + JSON (状態ラベル/サマリ)・命名 `hmm_train_2021_2024.joblib` 等・保存先 `results/regime_step1/`
> - ライブラリ = 既存 `.venv311` 継承 + hmmlearn 0.3.x 新規インストール
>
> #### 2. 経緯サマリ + 仕組み化 (= L-229 4 段階構造的失敗の再演防止)
>
> 本セッション中に CC が 4 段階の構造的失敗 (= 経緯理解不足 / 学習資産引用フリ / 振り子の極端さ / 凍結対象再演) でまこさん 4 回介入させた事案を受けた仕組み化:
>
> - **`.claude/memory/current_redesign_context.md` 新規作成**: 「なぜ今フロー改善・ML 内容見直しをしているのか」を 1 ページに整理・専門用語に () 説明
> - **`~/.claude/settings.json` の SessionStart hook 更新**: `current_redesign_context.md` 全文を自動表示・新セッション CC が即座に経緯を把握
> - **`feedback_writing_style.md` (auto-memory) に 4 問形式義務追記**: 問 1 各知見の採否 / 問 2 学習資産機械的列挙 / 問 3 前ターン差分・振り子検知 / 問 4 凍結対象再演チェック (= CLAUDE.md §現在の方針 + memory grep 結果)
> - **`feedback_plain_language.md` (auto-memory) に対話文義務追記**: メモ文と対話文の区別・まこさんとのチャットは常に対話文で書く義務
>
> #### 3. 業界実証 WebSearch verify
>
> BTC HMM regime detection で「log_returns + rolling_volatility」が業界 default として追加発見:
> - Preprints 202603.0831 (= BTC HMM 3 状態研究 2024-2026)
> - QuantInsti (= regime adaptive trading Python guide)
> - PickMyTrade 2026 (= Regime Detection 2026 Guide)
> - JDMDC / ResearchGate (= K-Means + HMM ベース regime 研究)
> - 計 10 件 WebSearch 引用済
>
> #### 4. lessons L-229 追加
> - 4 段階構造的失敗 + 改善 4 件 (= 4 問形式 + 対話文 + 経緯サマリ + 工程 2 以降の同型再演防止)
>
> ### 次セッション CC 優先順位
>
> 1. **優先 1 — Step 0 + 経緯サマリ + step1_regime_design.md v2 auto-load 確認**:
>    - SessionStart hook で `current_redesign_context.md` が自動表示される (= 経緯サマリ・即座に把握)
>    - 表示内容を Step 0 で必ず読む
>    - `step1_regime_design.md` v2 (= 工程 1 実装設計書) を view + 全文把握
>    - **設計提案前 4 問形式義務** (= feedback_writing_style.md) + **対話文義務** (= feedback_plain_language.md) を再宣言
>
> 2. **優先 2 — 🎯 まこさん判断: 工程 1 実装着手 or 工程 2 詳細詰め**:
>
>    - **選択肢 A: 工程 1 実装着手** (= step1_regime_design.md v2 §6 実装手順に従って 8 ステップ)
>      - hmmlearn インストール → データ抽出 → 学習 → 状態ラベル付け → artifact 保存 → 本番運用スクリプト → 視認チェック
>      - 1-2 セッション規模・視認チェックでまこさん介入必要
>    - **選択肢 B: 工程 2 (Entry 候補生成・固定ロジック) 詳細詰め**
>      - 業界標準シグナル組合せ (= テクニカル全体カバー網羅)
>      - 旧 Priority はスタートライン参照のみ・素材化禁止 (= feedback_priority_starting_line_only)
>      - 1-2 セッション規模・議論密度高
>    - 開始時点でまこさん判断を確認
>
> 3. **優先 3 — 工程 2-7 詳細詰め継続** (= A/B どちらでも結局工程 2 以降は必要)
> 4. **優先 4 — 全工程確定後の実装着手 + Phase 5 Replay 結果評価**
> 5. **優先 5 — セッション終了処理** (= lessons + WORKFLOW 改訂42 + git commit)
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読)
> - **WORKFLOW.md 改訂41 active** (本ブロック)
> - **`current_redesign_context.md`** (= 経緯サマリ・SessionStart hook で自動表示)
> - **`seven_step_framework.md`** (= 7 工程フレーム全体構成正本・各 step{N}_*.md 詳細設計書の上位文書・2026-05-26 新設)
> - **`step1_regime_design.md` v2** (= 工程 1 実装設計書・11 項目全確定)
> - **CLAUDE.md**
> - **lessons_active.md 直近 5 件** (= L-229 → L-228 → L-227 → L-226 → L-225)
> - **cc_role.md §1.4 / §1.4.5 / §1.4.6 / §1.4.6.1 / §1.4.7 / §1.5 / §1.7**
> - **`feedback_writing_style.md`** (auto-memory・**4 問形式義務追加版**・最重要)
> - **`feedback_plain_language.md`** (auto-memory・**対話文義務追加版**・最重要)
> - **`feedback_priority_starting_line_only.md`** (auto-memory・最重要・命令)
> - **`feedback_no_unverified_assertions.md`** (auto-memory・最重要・命令)
> - **`feedback_current_state_verify_before_design.md`** (auto-memory・最重要)
> - **`feedback_trade_ml_knowledge_gap.md`** (auto-memory・最重要)
>
> #### Layer 2 (工程 1 実装 or 工程 2-7 詳細詰め時)
> - **`cc_entry_logic_self_study.md` v6** §13-§20 (= 全 7 領域業界カタログ・2485 行)
>   - 工程 1 実装時: §14.6 + §16 + §17 + §20.1
>   - 工程 2 詰め時: §1-§9 (= 旧 Priority 対比) + 関連業界シグナル全カテゴリ
>   - 工程 3 詰め時: §13 + §14 + §16 + §17 + §18 (= 案 g 主軸)
>   - 工程 4 詰め時: §14.5 + §18.3 + §19.4 + §20.3 (= Thompson Sampling)
>   - 工程 5 詰め時: §13.4 + §14.7 + §19.2
>   - 工程 6 詰め時: §19.3 + §19.5
>   - 工程 7 詰め時: §20 全節
> - `technical_analysis_knowledge_base.md` (既存・1691 行) / `industry_benchmark_knowledge_base.md` (既存・420 行)
> - cc_role §1.5 / §1.6
> - **旧 Priority 実装** (`strategies/cat_v9_decider.py` + `config/cat_params_v9.json`) = **学習材料のみ・素材化禁止** (= feedback_priority_starting_line_only)
> - `phase_flow_v4_with_recovery.md` v7 = **廃止判定済・素材参照のみ** (= L-223)
>
> #### Layer 3 (リファレンス)
> - `false_positive_incident_policy.md`
> - `exchange_spec.md`
> - `lessons_archive.md` (L-152 以前)
> - Phase 1 v6 6 案実装スクリプト + summary JSON = 学習材料・採用候補にはしない
>
> #### データ・環境
> - parquet 3 種 (= Phase 0 v3.1 既存データ再利用) + `.venv311`
> - Phase 1 v6 6 案結果 = **無効扱い** (= L-223)
>
> ### 目的整合性 1 行宣言 (cc_role §1.4.6)
>
> - **次タスク** = (1) Step 0 + 経緯サマリ + step1_regime_design.md v2 auto-load → (2) 🎯 まこさん判断: 工程 1 実装着手 or 工程 2 詳細詰め → (3) 4 問形式義務を機械的運用 → (4) 工程 2-7 詳細詰め継続 → (5) 全工程確定後の実装着手 + Phase 5 Replay
> - **現フェーズ目的への貢献根拠** = WORKFLOW 改訂40 active で確定した「工程 2-7 詳細詰め (= 設計確定)」方針の第 1 工程として工程 1 (レジーム判定) の詳細設計を完了。新セッション CC が即実装着手できるレベルに到達。L-229 4 問形式義務 + 対話文義務 + 経緯サマリ自動 load で構造的失敗の再演を防止する仕組みも整備済。

---

## 🧊 改訂40 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-25 改訂40・**🎉 cc_entry_logic_self_study.md v6 完成 = 案 B 学習 100% 完了・次タスク = 工程 2-7 詳細詰め (= 設計確定) に進む**）

> **【旧正本ブロック・改訂40・2026-05-25 セッション末（🎉 案 B 学習 100% 完了 = 領域 7/7 完成）】**
>
> 本ブロック詳細は改訂41 active 本文 + lessons L-228 参照。
> v6 (2485 行) + L-228 + WORKFLOW 改訂40 active を commit 8eafc66 で固定。

---

---

## 🧊 改訂39 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-25 改訂39・**cc_entry_logic_self_study.md v5 完成 (= ML 知識領域 6 リスク管理 業界カタログ整理・1610 → 1999 行・+389 行・WebSearch 8 件 + GARCH-family + EWMA + HAR-RV + Chandelier Exit + Wilder Volatility Stop + CPPI/TIPP + Kelly criterion + Pyramiding + CVaR + TSM Vol Scaling + ML 動的 Stop + Amberdata 引用 + L-227 追加) + 6 軸多様性欠落に第 7 軸 = リスク管理レイヤー不在追加 + Phase 5/6-b 多重防御 v5 候補 (Calmar > 2.0 / CVaR_95 / Sortino > 1.5) 確立 (§19.5)**・次タスク = 案 B 学習継続 = 残り 1 領域 (7) を v6 として追加・領域 7 (監視運用)）

> **【旧正本ブロック・改訂39・2026-05-25 セッション末（案 B 学習領域 6 完成・領域 6/7 = 約 86% 完成）】**
>
> 本ブロック詳細は改訂40 active 本文 + lessons L-227 参照。
> v5 (1999 行) + L-227 + WORKFLOW 改訂39 を commit 9ac3ea7 で固定。

---

## 🧊 改訂38 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-25 改訂38・**cc_entry_logic_self_study.md v4 完成 (= ML 知識領域 5 組合せ手法 業界カタログ整理・1255 → 1610 行・+355 行・WebSearch 14 件 + AFML Ch.6/16 + Lopez de Prado 2016 (HRP 原論文) + Raffinot 2018 (HERC) + Hudson & Thames meta-labeling repo + Riskfolio-Lib + PyPortfolioOpt + arxiv 4 件 + Viola-Jones cascade theory 引用 + L-226 追加) + Phase 1 v6 6 案全滅の構造的原因を 6 軸多様性欠落に整理 (= v1-v4 統合) + Phase 1 v7 候補「案 g」設計判断調査ノート確立 (§18.5)**・次タスク = 案 B 学習継続 = 残り 2 領域 (6/7) を v5 として追加・領域 6 (リスク管理) 先行）

> **【旧正本ブロック・改訂38・2026-05-25 セッション末（案 B 学習領域 5 完成）】**
>
> 本ブロック詳細は改訂39 active 本文 + lessons L-226 参照。
> v4 (1610 行) + L-226 + WORKFLOW 改訂38 を commit 814e381 で固定。

---

## 🧊 改訂37 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-25 改訂37・**cc_entry_logic_self_study.md v3 完成 (= ML 知識領域 3 特徴量設計 + 領域 4 評価方法 業界カタログ整理・727 → 1255 行・+528 行・WebSearch 16 件 + AFML Ch.2/5/7/8/14 + Bailey & LdP 2014 DSR/PBO + MLfAT Ch.4 + Hudson & Thames mlfinlab + arxiv microstructure 5 件 引用 + L-225 追加) + cat-bitget 設計判断確定事項 6 件追加 (= Phase 0 v4 特徴量拡張候補 / CPCV 検証強化候補 / Phase 5・6-b DSR>0.95+PBO<0.5 多重防御候補 / scaler leak Pipeline 義務化 / 統計指標 vs PnL 指標物理分離維持)**・次タスク = 案 B 学習継続 = 残り 3 領域 (5/6/7) を v4 として追加・領域 5 (組合せ手法) 先行）

> **【旧正本ブロック・改訂37・2026-05-25 セッション末（案 B 学習領域 3-4 完成）】**
>
> 本ブロック詳細は改訂38 active 本文 + lessons L-225 参照。
> v3 (1255 行) + L-225 + WORKFLOW 改訂37 を commit 012f47e で固定。

---

## 🧊 改訂36 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-27 改訂36・**cc_entry_logic_self_study.md v2 完成 (= ML 知識領域 1+2 業界カタログ整理・WebSearch 14 件 + 教科書引用 + L-224 追加) + Phase 1 v6 6 案全滅の補強原因 (= 全 LightGBM・アルゴ多様性ゼロ) verify + 7 工程アルゴ選定調査ノート整理 + WORKFLOW.md 改訂 30-23 archive 移送 (1629 → 889 行・約 45% 削減)**・次タスク = 案 B 学習継続 = 残り 5 領域 (3-7) を v3 として追加・領域 3-4 (特徴量設計 + 評価方法) 先行）

> **【旧正本ブロック・改訂36・2026-05-27 セッション末（案 B 学習領域 1-2 完成 + WORKFLOW 肥大化対策完了）】**
>
> ### 本セッション (2026-05-27) 完了事項
>
> #### 1. cc_entry_logic_self_study.md v2 完成 (= WORKFLOW 改訂 35 active 優先 2 = 案 B 学習継続)
> - v1 (346 行) → **v2 (727 行・+381 行)** に拡張
> - **§13 ML 学習方法 (6 章)**: GBDT 系 / 時系列深層学習 / 時系列特化 ML (MiniROCKET/TSFresh) / 強化学習 (PPO/SAC) / アンサンブル + Meta-Labeling (AFML Ch.3+Ch.6) / 7 工程まとめ
> - **§14 ML 学習項目 (8 章)**: Triple Barrier / Meta-Labeling ラベル / Volatility 予測 (GARCH/HAR-RV/ML) / Sharpe 直接最適化 / Kelly / Regime 予測 (HMM/GMM) / Exit timing / 7 工程マトリックス
> - **§15 総合所見**: cat-bitget 改善方向 4 点 + 次セッション残り 5 領域 + 設計判断調査ノート
> - WebSearch 14 件 + AFML Ch.3/6 + Oxford-Man Institute 2020 + Hudson & Thames mlfinlab + arxiv 8 件 引用
>
> #### 2. Phase 1 v6 6 案全滅の補強原因 verify (§13.1 で実証)
> - 案 a-f が **全 LightGBM** = アルゴリズム多様性ゼロ確認
> - 業界実証で XGBoost が momentum 戦略の Sharpe / DD で LightGBM 優位
> - L-223 ボラ予測 ML 設計欠陥 + 本セッション補強原因 = 6 案全滅の二大根本原因
>
> #### 3. 7 工程アルゴ選定調査ノート (§13.6 + §14.8 + §15.4)
> - 工程 1 (regime): 固定ルール (= ADX > 25 + DI 差) MVP → 後段 HMM ML 化候補
> - 工程 3 (Entry ML): LightGBM + XGBoost stacking + Meta-Labeling + regime 入力 + LONG/SHORT 分離 + MTF
> - 工程 4 (Position Sizing): phase_flow_v4 v7 改善 4 動的合成方式 8 維持
> - 工程 5 (Exit ML): PPO (RL・78% success rate) 主軸 + XGBoost (scale-out 確率) サブ
> - **確定ではなく調査ノート位置・設計確定は工程 2-7 詳細詰めで別途実施 (cc_role §1.5)**
>
> #### 4. lessons L-224 追加
> - cc_entry_logic_self_study.md v2 完成 + 学習成果 5 ポイント + 次セッション残り 5 領域 (3-7) 継続計画
>
> #### 5. WORKFLOW.md 肥大化対策 (L-216 cc_role §1.4.7 ルール実施)
> - 改訂 30 / 29 / 28 / 27 / 26 / 25 / 24 / 23 ブロック (= 8 ブロック・740 行) を archive 移送
> - 移送先: [archive/workflow/WORKFLOW_archive_revisions23-30_20260527.md](archive/workflow/WORKFLOW_archive_revisions23-30_20260527.md) (749 行)
> - 結果: WORKFLOW.md 1629 行 → 889 行 (-740 行・約 45% 削減)
>
> ### 次セッション CC 優先順位
>
> 1. **優先 1 — Step 0 + 新規 memory + cc_entry_logic_self_study.md v2 auto-load 確認**:
>    - `feedback_priority_starting_line_only.md` / `feedback_no_unverified_assertions.md` / `feedback_current_state_verify_before_design.md` / `feedback_trade_ml_knowledge_gap.md` 起動
>    - cc_role §1.4.6 / §1.4.6.1 起動
>    - **`cc_entry_logic_self_study.md` v2 全文 view** (= 727 行・本セッション完成・必読)
>
> 2. **優先 2 — 案 B 学習継続 (= 残り 5 領域・cc_entry_logic_self_study.md v3 として追加)**:
>    - **領域 3 (特徴量設計) + 領域 4 (評価方法) を先行**: 工程 3 (Entry ML) の再設計に直結
>      - 領域 3: Fractional Differentiation (AFML Ch.5) / スケーリング / 特徴量選択 / 出来高系 / 板情報系
>      - 領域 4: Walk-Forward / Purged K-Fold (AFML Ch.7) / CPCV / Embargo / DSR (AFML Ch.14) / 過学習検出
>    - **領域 5 (組合せ)** その後: §13.5 で半分カバー済 → 残り = 階層 / Cascade / 多段 stacking
>    - **領域 6-7** は工程 4-7 詳細詰めと並行可能
>    - 各領域 WebSearch 10-20 件 + 教科書 chapter 引用必須 (cc_role §1.4.6.1)
>    - 1-2 セッション規模 (= 領域 3-4 で 1 セッション・領域 5-7 で 1 セッション)
>
> 3. **優先 3 — 学習完了後の工程 2-7 詳細詰め (= 設計確定)**
> 4. **優先 4 — 工程 2-7 設計確定後の実装着手 + 全体結合テスト**
> 5. **優先 5 — セッション終了処理** (lessons + WORKFLOW 改訂37 + git commit)
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読)
> - **WORKFLOW.md 改訂 36 active** (本ブロック)
> - **CLAUDE.md**
> - **`cc_entry_logic_self_study.md` v2** (= 本セッション完成・727 行・次セッション v3 拡張対象)
> - **lessons_active.md 直近 5 件** (L-224 → L-223 → L-222 → L-221 → L-220)
> - **cc_role.md §1.4 / §1.4.5 / §1.4.6 / §1.4.6.1 / §1.4.7 / §1.7**
> - **`feedback_priority_starting_line_only.md`** (auto-memory・最重要・命令)
> - **`feedback_no_unverified_assertions.md`** (auto-memory・最重要・命令)
> - **`feedback_current_state_verify_before_design.md`** (auto-memory・最重要)
> - **`feedback_trade_ml_knowledge_gap.md`** (auto-memory・最重要)
>
> #### Layer 2 (案 B 学習継続時)
> - **AFML (Lopez de Prado 2018)** Ch.5 Fractional Differentiation / Ch.7 Cross-Validation in Finance / Ch.14 Backtest Statistics (= 領域 3-4 主軸)
> - **MLfAT (Stefan Jansen 2020)** Ch.4 Alpha Factor Research / Ch.8-10 Backtest 設計 (= 領域 3 + 領域 7)
> - **Hudson & Thames mlfinlab blog** (= 領域 3-7 業界実装パターン)
> - `technical_analysis_knowledge_base.md` (既存・1691 行) / `industry_benchmark_knowledge_base.md` (既存・420 行)
> - cc_role §1.5 / §1.6
> - 旧 Priority 実装 (`strategies/cat_v9_decider.py` + `config/cat_params_v9.json`) = **学習材料のみ・素材化禁止**
> - `phase_flow_v4_with_recovery.md` v7 = **事実上廃止・参照のみ**
>
> #### Layer 3 (リファレンス)
> - `false_positive_incident_policy.md`
> - `exchange_spec.md`
> - `lessons_archive.md` (L-152 以前)
> - Phase 1 v6 6 案実装スクリプト + summary JSON = 学習材料・採用候補にはしない
>
> #### データ・環境
> - parquet 3 種 + `.venv311`
> - Phase 1 v6 6 案結果 = **無効扱い** (= L-223)
>
> ### 目的整合性 1 行宣言 (cc_role §1.4.6)
>
> - **次タスク** = (1) Step 0 + cc_entry_logic_self_study.md v2 全文 view auto-load → (2) 案 B 学習継続 = 残り 5 領域 (3-7) を v3 として追加・領域 3-4 先行 → (3) 学習完了後に工程 2-7 詳細詰め → (4) 実装着手
> - **現フェーズ目的への貢献根拠** = WORKFLOW 改訂 35 active で確定した「学習完了後に工程 2-7 詳細詰めに進む」方針に従い、v2 (= 領域 1-2) 完成済 → 次は v3 (= 領域 3-7) で残り 5 領域を完成させて工程詳細詰めに進む準備を整える。L-224 改善 1 で領域 3-4 を先行 (= 工程 3 Entry ML 再設計直結)。

---

## 🧊 改訂35 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-25 改訂35・**Phase 1 v6 6 案全滅確定 (案 e/f 完走・combos_pass = 0/8) + ボラ予測 ML 設計欠陥確定 + phase_flow_v4_with_recovery.md v7 事実上廃止 + ChatGPT 7 工程フレーム + CC ハイブリッド構成への全面再設計開始 + CC 学習資料 cc_entry_logic_self_study.md v1 作成 + memory 2 件 + L-223 追加**・次タスク = 案 B (= ChatGPT 7 工程フレーム範囲の ML 知識体系化) を新セッションで継続）

> **【現在の正本ブロック・改訂35・2026-05-25 セッション末（フロー破綻 → 再設計 → CC 学習横道 → 新セッション切り替え）】**
>
> ### 本セッション (2026-05-25) 完了事項
>
> #### 1. Phase 1 v6 残作業の完走 (= WORKFLOW 改訂 34 優先 2)
> - 案 e (Triple Barrier multiclass) full + predictions parquet 保存版実装・110.7 分
> - 案 f (Meta-Labeling AFML 標準実装) full + cross_val_predict pattern (inner TimeSeriesSplit 3-fold OOF)・259 分
> - 結果: **6 案全て combos_pass = 0/8** (TP precision 0.43 頭打ち)
>
> #### 2. Phase 1 v6 6 案全滅の構造的原因究明
> - 入力 2604 特徴量に regime/trend 系列ゼロを grep verify
> - feature_importance top20 が全案でボラ系 (realized_vol / BB width / ATR) 支配を verify
> - 「ボラ予測 ML 設計欠陥」確定: LONG/SHORT 並列学習 + regime context 不在 + ボラ依存ラベル + MTF 欠落
> - 約 2 週間分の Phase 0 / Phase 1 作業が根本欠陥の上に乗っている = **無効扱い**
>
> #### 3. phase_flow_v4_with_recovery.md v7 全体フロー「破綻」判断
> - まこさん指摘「学習内容の手数はこれだけあるのに学習方法が支離滅裂」「現状この最小単位 (旧手動 Priority) ロジックにも劣る状態」「BTC は 8 割レンジ・BOT はレンジが一番得意」
> - ChatGPT 7 工程フレーム提案受領
> - 現状 v7 の致命的ギャップ確認: 工程 1 / 工程 2 / 工程 6 = 存在しない + 工程 3 = 設計思想違い (8 工程中 3 工程欠落 + 1 工程相違)
> - まこさん判断「現状フローは破綻してるみたいなので、フローから設計し直すわ」 → 全体フロー再設計確定
>
> #### 4. ChatGPT 7 工程フレーム + CC ハイブリッド構成確定
>
> | 工程 | 構成 |
> |---|---|
> | 1. 市場状態判定 | 固定ルール (ADX > 25 + DI 差)・後に ML 化検討 |
> | 2. Entry 候補生成 | 固定ロジック (= テクニカル全体から構築・旧 Priority 素材化禁止) |
> | 3. Entry ML | ML (LightGBM Classifier・TP first 確率) |
> | 4. Position Sizing | 動的合成式 (Half-Kelly + Volatility targeting + cluster 配分) |
> | 5. Exit ML | ML (単一 multiclass で TP/損切/STALE 判定・必要なら 3 系統分離) |
> | 6. Risk 管理 | 固定ルール (spread / ATR 急変 / volume spike)・後に ML 化検討 |
> | 7. Online 監視 | 運用層 (監視スクリプト + アラート) |
>
> - 工程 1 詳細詰め: 3 種類分類 (上昇/下降/レンジ) + 4 時間足単一判定 + B2 (regime ラベル + 各時間軸生指標 Entry ML 入力) + ADX > 25 / DI 差最小構成で方向確定
> - 工程 2 以降の詳細詰めは未着手 (= CC 学習完了後)
>
> #### 5. CC 学習資料 cc_entry_logic_self_study.md v1 作成 (まこさん命令)
> - 命令「指標・閾値・時間の使い方を勉強しなおして」
> - WebSearch 8 件 + 旧 Priority 実装 verify による業界対比分析・12 セクション
> - 旧 Priority がテクニカル 8 カテゴリ中 3.5 カテゴリ (= 約 40-45%) のみカバー verify
> - 残課題: 出来高 / パターン認識 / 板情報 / Mean Reversion 体系 / MTF 整合システム
>
> #### 6. memory 2 件作成・更新 (まこさん命令の永続化)
> - 新規: `feedback_priority_starting_line_only.md` (= 命令「旧 Priority スタートライン認識・10 回以上訂正・二度と忘れないように」)
> - 更新: `feedback_no_unverified_assertions.md` (= 命令「根拠のない適当な提案禁止」・2026-05-25 再演事案追記)
> - MEMORY.md 先頭登録で次セッション SessionStart hook auto-load 化
>
> #### 7. lessons L-223 追加
> - 3 重事案 + phase_flow_v4 v7 破綻経緯 + 横道経緯の構造的記録
> - 改善 5 件
>
> ### 横道経緯の重要記録 (まこさん指示)
>
> 本セッションは「**Phase 1 v6 残作業完走 → 6 案全滅 → 根本欠陥発覚 → phase_flow_v4 v7 破綻判断 → ChatGPT 7 工程フレーム導入 → 各工程要素詰め開始 → CC のテクニカル/ML 知識不足露呈 → CC 学習資料作成に横道 → 学習継続のため新セッション切り替え**」という構造。本来予定していた WORKFLOW 改訂 34 優先 3-5 (= 下位仕様 v7 整合改訂 / Phase 2 着手判断) は phase_flow_v4 v7 廃止により**全部無効**。
>
> ### 次セッション CC 優先順位
>
> 1. **優先 1 — Step 0 + 新規 memory + CC 学習資料 auto-load 確認**:
>    - `feedback_priority_starting_line_only.md` / `feedback_no_unverified_assertions.md` / `feedback_current_state_verify_before_design.md` / `feedback_trade_ml_knowledge_gap.md` 起動
>    - cc_role §1.4.6.1 起動
>    - **`cc_entry_logic_self_study.md` v1 全文 view** (本セッションで作成した CC 学習資料の再読・必読)
>
> 2. **優先 2 — 案 B 学習継続 (= ChatGPT 7 工程フレーム範囲の ML 知識体系化)**:
>    - 領域 1: ML 学習方法 (LightGBM / XGBoost / CatBoost / LSTM / Transformer / MiniROCKET / TSFresh / 強化学習)
>    - 領域 2: ML 学習項目 (TP first 確率 / Meta-Labeling / Volatility / Sharpe / Position size / Regime / Exit timing)
>    - 領域 3: ML 特徴量設計 (Fractional Differentiation / スケーリング / 特徴量選択 / 出来高系 / 板情報系)
>    - 領域 4: ML 評価方法 (Walk-Forward / Purged K-Fold / CPCV / Embargo / DSR / 過学習検出)
>    - 領域 5: ML 組合せ手法 (アンサンブル / Multi-model / Meta-Labeling / 階層 / Cascade)
>    - 領域 6: リスク管理 (Kelly / Half-Kelly / Volatility targeting / Stop-loss / Drawdown control)
>    - 領域 7: 監視・運用 (Concept drift / Online learning / A/B testing)
>    - `cc_entry_logic_self_study.md` v2 として追記・WebSearch 50-100 件 + 教科書 chapter 引用必須
>    - 2-3 セッション規模
>    - cc_entry_logic_self_study.md v1 §10.3 残課題 5 領域も並行
>
> 3. **優先 3 — 学習完了後の工程 2-7 詳細詰めに戻る**
> 4. **優先 4 — 工程 2-7 設計完了後の実装着手 + 全体結合テスト**
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読)
> - **WORKFLOW.md 改訂 35 active** (本ブロック)
> - **CLAUDE.md**
> - **`cc_entry_logic_self_study.md` v1** (= 本セッション作成・次セッション v2 拡張対象)
> - **lessons_active.md 直近 5 件** (L-223 → L-222 → L-221 → L-220 → L-218)
> - **cc_role.md §1.4 / §1.4.5 / §1.4.6 / §1.4.6.1 / §1.4.7 / §1.7**
> - **`feedback_priority_starting_line_only.md`** (auto-memory・最重要・命令)
> - **`feedback_no_unverified_assertions.md`** (auto-memory・最重要・命令)
> - **`feedback_current_state_verify_before_design.md`** (auto-memory・最重要)
> - **`feedback_trade_ml_knowledge_gap.md`** (auto-memory・最重要)
>
> #### Layer 2 (案 B 学習継続時)
> - `technical_analysis_knowledge_base.md` (既存・指標辞典 + 閾値理論 + MTF 理論・1691 行)
> - `industry_benchmark_knowledge_base.md` (既存・5 レバー業界相場 + 出典 47 件)
> - cc_role §1.5 / §1.6
> - 旧 Priority 実装 (`strategies/cat_v9_decider.py` + `config/cat_params_v9.json`) = **学習材料のみ・素材化禁止**
> - **`phase_flow_v4_with_recovery.md` v7** = **事実上廃止・参照のみ**
>
> #### Layer 3 (リファレンス)
> - `false_positive_incident_policy.md`
> - `exchange_spec.md`
> - `lessons_archive.md` (L-152 以前)
> - Phase 1 v6 6 案実装スクリプト + summary JSON = 学習材料・採用候補にはしない
>
> #### データ・環境
> - parquet 3 種 + `.venv311`
> - Phase 1 v6 6 案結果 = **無効扱い** (Phase 4-b 以降に渡さない)
> - 案 e predictions parquet = 保存済だが Phase 4-b 採用対象外 (設計欠陥のため)
>
> ### 目的整合性 1 行宣言 (cc_role §1.4.6)
>
> - **次タスク** = (1) Step 0 + 新規 memory + cc_entry_logic_self_study.md v1 auto-load → (2) 案 B 学習 (cc_entry_logic_self_study.md v2 として ML 知識 7 領域追加) → (3) 学習完了後に工程 2-7 詳細詰め → (4) 全体実装着手
> - **現フェーズ目的への貢献根拠** = Phase 1 v6 6 案全滅 + ボラ予測欠陥確定で phase_flow_v4 v7 破綻が確定。ChatGPT 7 工程フレーム + CC ハイブリッド構成への再設計開始。CC のテクニカル/ML 知識不足が再設計の障害なので、学習を完了させてから設計詳細詰めに進む。

---

## 🧊 改訂34 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-26 改訂34・**phase_flow_v4 v7 改訂完了 (reorder_proposal §3 改善 2/3/4 反映・Phase 4-a 独立工程化 + Phase 5 合格ライン $3,800 + Phase 5-d 動的合成主軸化 + Phase 4-c 保留) + §1.5 verify 枠組み新設 (= 業界標準の一般的 ML 品質チェック 11 項目 + Phase 5 Replay = 改善サイクル起点) + industry KB §5.2-5.3 削除 + L-222 追加**・次タスク = Phase 1 v6 残作業 = 案 f AFML 標準実装修正 + full 完走 + 案 e predictions parquet 保存）

> **【現在の正本ブロック・改訂34・2026-05-26 セッション末（phase_flow_v4 v7 反映議論完了 + 認識合致 + セッション終了処理）】**
>
> ### 本セッション (2026-05-26 後半) 完了事項
>
> #### 1. phase_flow_v4_with_recovery.md v7 改訂 (reorder_proposal.md §3 改善 2/3/4 反映)
> - **改善 2**: Phase 3-b / Phase 4-a (cluster 並立) 独立工程化注記 + 品質要件追加 (cluster 間相関 < 0.3 + cluster 別月次 Sharpe > 0.5)
> - **改善 3**: Phase 5 合格条件 月次 NET $1,900 → **$3,800** (DSR live degradation 50% 想定マージン・本番で半減して Phase 6-b で月 $1,900 死守) + 異常値スメル閾値 $3,800 → $7,600 連動更新
> - **改善 4**: Phase 5-d Position sizing 主軸を「Half-Kelly + Volatility targeting + cluster 強度別配分」の動的合成 (方式 8) に変更・残り 7 方式は比較ベースライン化
> - **改善 1 (Phase 4-c Regime filter) は保留**: §4 全体フロー末尾に注記追加・Phase 5 不合格時の追加投入候補・凍結 regime_research.md 素材転用可
> - §4 全体フロー俯瞰図 + §5.2 23 軸 B-11 cluster 更新
>
> #### 2. phase_flow_v4_with_recovery.md §1.5 verify 枠組み + Phase 5 Replay 位置付け 新設 (= 本セッション議論の核心)
> - **§1.5.1 各フェーズ完了 verify = 業界標準の一般的 ML 品質チェック 11 項目** (データ整合性 / leak / 学習収束 / artifact / feature_importance / 予測値分布 / 過学習サイン / class imbalance / 評価指標妥当性 / ハイパラ妥当性 / false_positive 関所通過)
> - **§1.5.2 Phase 5 Replay の位置付け = 改善サイクルの起点** (= 一発勝負の合否判定ではなく結果を見て該当フェーズに戻る反復サイクル) + 反復図
> - **§1.5.3 根拠ファイル参照** (reorder_proposal §2 / industry KB §3 / cc_ml_design_spec §7 / 本セッション議論)
> - **売上数値で縛る判定は廃止** (= 旧 5 指標 / 3 指標を Phase 1 等の判定基準として使わない・reorder_proposal §2 業界標準整合)
>
> #### 3. industry_benchmark_knowledge_base.md §5.2 + §5.3 削除 (= 監査 CC のレシピ提案部分)
> - §5.2 「Phase 4-b 単体検証 3 候補」(手動 Priority 前提誤認含む) 全削除
> - §5.3 「検証順序の改訂提案 7 ステップ」全削除
> - §5 タイトル「cat-bitget レシピへの示唆 (実践)」→「cat-bitget へのキャリブレーション」変更
> - §5.1 5 レバー責任値分担表 + §6-§8 (知識ギャップ / 改訂履歴 / 出典 47 件) は維持
>
> #### 4. lessons L-222 追加 (本セッション議論の構造的混乱事案 + 改善 6 件)
> - 「監査ベース改訂を CC が独自議論で再演」事案 (= L-220 + L-221 同型再演)
> - 改善 6 件: Step 0 で reorder_proposal 等確認 / テンプレ応答禁止 / 翻訳バイアス対策 / PM 視点定義 / 振り子防止 / 応答短縮 + 平易な言葉
>
> ### 次セッション CC 優先順位
>
> 1. **優先 1 — Step 0 プロトコル + 現状把握 verify (絶対遵守・L-222 対策含む)**:
>    - `feedback_current_state_verify_before_design.md` (auto-memory) 確認
>    - **`git log --oneline -10` + `ls -lat .claude/memory/ | head -20` で別セッション成果物確認** (= L-222 改善 1)
>    - 「凍結ベースライン $370 / 手動 Priority 凍結 / ML pipeline 現役 / phase_flow_v4 v7 が正本」再確認
>    - これらを出さずに設計提案・実装着手禁止
> 2. **優先 2 — Phase 1 v6 残作業 (= 学習未完了 + artifact 未整備の解消)**:
>    - **案 f (Meta-Labeling) AFML 標準実装修正** (cross-validated primary predictions・sklearn `cross_val_predict` パターン・コード ~50-100 行) + full 完走 (1-2 時間・1 並列)
>    - **案 e (Triple Barrier multiclass) predictions parquet 保存追加** (コード ~10-20 行) + 再実行 (60-90 分・1 並列)
>    - 各 case 完了 verify (= phase_flow_v4 §1.5.1 一般 ML 品質チェック 11 項目)
> 3. **優先 3 — 下位仕様ファイル v7 整合改訂 (Phase 1 v6 完了後)**:
>    - `cc_ml_design_spec.md`: §3 直前に Phase 4-a (cluster 並立) 新設 + §4 Position sizing 主軸明示 + §5 Phase 5 $3,800 + §6 採否判定段階別化
>    - `phase_compliance_checklist.md`: §Phase 4-a に 4a.6/4a.7 (cluster 品質要件) + §Phase 5-d に 5d.5 (動的合成検証) + §Phase 5 注記 (合格条件は phase_flow_v4 v7 整合)
> 4. **優先 4 — Phase 2 着手判断 (Phase 1 v6 完了後)**:
>    - Phase 1 v6 採用案決定 (= 売上数値判定廃止のため相対比較で最良案選定・別議論)
>    - Phase 2 ハイパラ最適化着手
> 5. **優先 5 — セッション終了処理** (= lessons + WORKFLOW 改訂 35 + 改訂 34 履歴降格)
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読・読了ゲート機械的証跡対象)
> - **WORKFLOW.md 改訂 34 active** (本ブロック)
> - **CLAUDE.md**
> - **phase_flow_v4_with_recovery.md** (v7・§1.5 verify 枠組み新設・1173 行)
> - **lessons_active.md 直近 5 件** (L-222 → L-221 → L-220 → L-218 → L-217)
> - **cc_role.md §1.4 / §1.4.5 / §1.4.6 / §1.4.6.1 / §1.4.7**
> - **`feedback_current_state_verify_before_design.md`** (auto-memory・最重要)
>
> #### Layer 2 (Phase 1 v6 残作業 + 改善議論時)
> - **`reorder_proposal.md` 第 2 版** (commit `3b30334`・改訂 4 箇所のうち 3 件反映済・改善 1 Phase 4-c 保留)
> - **`industry_benchmark_knowledge_base.md`** (v1・§5.2-5.3 削除済・5 レバー業界相場 + 出典 47 件)
> - **`technical_analysis_knowledge_base.md`** (v2・1691 行・個別指標辞典 + AFML/mlfinlab + 閾値設計論)
> - **監査結果 + §10 補足メモ** (`2026-05-26_phase1_v6_6cases_methodology_audit_report.md`・567 行)
> - **`cc_ml_design_spec.md`** (= v7 整合改訂対象・410 行) / **`phase_compliance_checklist.md`** (= 同・224 行)
>
> #### Layer 3 (リファレンス・必要時参照)
> - `false_positive_incident_policy.md`: 関所 A-G + 類型 A-H + §0-1/§0-2
> - `exchange_spec.md`: Bitget USDT-FUTURES BTCUSDT スペック
> - `lessons_archive.md`: L-152 以前
> - 既存 Phase 1 v6 実装 (案 a/b/c/d/e/f script + summary JSON・案 b/c/d/e full 完走 + 案 f smoke のみ)
>
> #### データ・環境
> - parquet 3 種 (train_2021_2024 / test_2025 / test_2026_q1) + `.venv311`
> - Phase 1 v6 5 案実装 script (commit `294a79f` 済・案 b/c/d/e/f)
> - **案 e predictions parquet**: ❌ **未生成** (case_e に保存追加 + 再実行必要・60-90 分)
> - **案 f**: smoke のみ・full 未実行 (AFML 標準実装修正後 full 走行)
> - log: `results/priority_rebuild/ml_phase1_v5/_logs/log_case_*.log`
>
> ### 目的整合性 1 行宣言 (cc_role §1.4.6)
>
> - **次タスク** = (1) Step 0 + 現状把握 verify (L-222 改善 1 含む) → (2) Phase 1 v6 残作業 (案 f AFML 修正 + case_e predictions parquet 保存) → (3) 下位仕様 v7 整合改訂 → (4) Phase 2 着手判断
> - **現フェーズ目的への貢献根拠** = phase_flow_v4 v7 + §1.5 で確定した「全工程通してから Phase 5 Replay で月の売上一括判定」業界標準フローに従い、Phase 1 v6 の残作業 (= 学習未完了 + artifact 未整備) を解消して Phase 2 着手準備を整える。L-222 同型再演防止のため Step 0 で reorder_proposal / WORKFLOW 改訂 34 を必読化。

---

## 🧊 改訂33 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-26 改訂33・**監査依頼書テンプレ整備 (L-218) + Phase 1 v6 6 案監査受領 (Verdict NO-GO + PIVOT) + 目標達成設計レシピ起草 → L-180 違反 partial revert (L-220) + industry_benchmark KB 維持 + 監査結果 §10 補足メモ追加**・次タスク = 現状把握 verify → phase_flow_v4 改善議論 + Phase 1 v6 Layer 3 投入 or Phase 4-b 単体検証）

> **【現在の正本ブロック・改訂33・2026-05-26 セッション末（監査受領 + 目標達成設計試行と部分巻き戻し + 再発防止策完了）】**
>
> ### 本セッション (2026-05-26) 完了事項
>
> #### 1. 監査依頼書テンプレ整備 (L-218・commit `56ca797`)
> - `.claude/audits/inputs/_template.md` 新設
> - 冒頭に「⚠️ auditor 宣言ブロック」(auto-load 上書き + 即実行手順 + 禁止事項)
> - cc_role §1.4.5 改善 10 追加 (テンプレ使用必須 + 宣言ブロック削除禁止 + 依頼書パス明示必須)
> - WORKFLOW.md §監査エージェント 改訂 (経路 A CP 大型監査 / 経路 B 軽い意見聞き)
>
> #### 2. Phase 1 v6 6 案監査受領 (commit `744a21e`)
> - 監査依頼書: `.claude/audits/inputs/2026-05-26_phase1_v6_6cases_methodology_audit_request.md`
> - 監査結果: `.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md`
> - **Verdict: NO-GO + PIVOT 混合判定**
> - 改善方向性 7 件 (案 f AFML 標準実装 / B-10 アルゴ多様化 / 正則化強化 / CPCV / ROC AUC / B-15 拡張 / プロセス対策)
>
> #### 3. 目標達成設計レシピ起草 → partial revert (L-220・commit `adf62ab` → `da471c1`)
> - まこさん指摘「目標達成するための、phase_flow_v4 のフローに不具合や改善すべき点が多々あるってこと?」を受けて起草
> - `cc_target_pathway_design.md` (5.1× gap 分解 5 レバー) + `phase_flow_v5_design_proposal.md` 新設
> - **L-180 違反**: 「Phase 4-b 単体検証で手動 Priority Entry (P1-P24) を使う」と書いた → CLAUDE.md L174「P1-P24 は解体・再設計」verify せず
> - まこさん指摘「ML に変更してるんだよ。めちゃくちゃだな」で発覚
> - **partial revert**: cc_target_pathway_design.md + phase_flow_v5_design_proposal.md + 元 L-219 削除
>
> #### 4. industry_benchmark_knowledge_base.md 維持
> - WebSearch 18 件 + 業界文献統合・出典 URL 47 件明記
> - 5 レバー定量根拠 (Entry 1.1-1.6× / Exit 1.3-2.0× / 並立 1.2-1.8× / Regime 1.1-1.6× / Sizing 1.1-1.3×)
> - 月次 NET 業界相場 + Phase 別合格基準 PnL 紐付け業界手法 + BTC 5m 業界実証
> - ML / 手動 Priority 区別と無関係の事実データ → 維持
>
> #### 5. 監査結果 §10 補足メモ追加 (commit `744a21e`)
> - 監査本体 §1-§9 は触らず、末尾に §10「メインセッション CC による補足メモ」追記
> - 次セッション着手前必須 / 取り組むべき問い / Phase 4-b 単体検証の Entry 信号選択 (**案 e predictions 推奨**) 明示
> - 監査の独立性維持しつつ、本セッションで失った積み上げの問題意識を次セッションに引き継ぐ
>
> #### 6. 同型再演防止策 (feedback memory)
> - `feedback_current_state_verify_before_design.md` (auto-memory) 新設
> - 最重要マークで MEMORY.md に index → 次セッション SessionStart hook で auto-load
> - 内容: ML pipeline 設計議論・提案前に「現役戦略 / 凍結対象 / 現フェーズ」を grep + Read で機械的証跡として出す
>
> #### 7. lessons L-218 + L-220 + L-221 追加 (L-219 は欠番)
> - L-218: 監査依頼書 auditor 宣言ブロック未整備事案
> - L-220: 設計議論時の現状把握 verify 不足事案 (partial revert 経緯含む・auditor session 側事案)
> - L-221: メインセッション CC の Phase 1 v6 6 案実装プロセス欠陥事案 (目的整合性ゲート 5 連続書き忘れ + Phase 境界喪失 + sweep 自己目的化)
>
> #### 8. Phase 1 v6 5 案実装 + smoke + full 完走 (commit `294a79f`・本セッション前半・auditor 起動前)
> - 5 ファイル: `scripts/priority_rebuild/run_lgbm_phase1_v5_case_{b,c,d,e,f}_*.py` (5 案分・2,905 行)
> - 案 b/c/d/e: full 完走 (train_2021_2024 / 8 組合せ × 3 fold)・案 f: smoke のみ (full 未実行)
> - smoke v1 fix: 案 c (Flat=0% + column index swap → class_to_col 動的解決) / 案 d (LightGBM 10000 row/query hard limit → 日次グループ 288 bar)
> - 5 案結果: いずれも TP precision 0.30-0.45 で頭打ち → 0/8 ALL PASS / 案 e の entropy_lift (K=24/48/96 で 0.20-0.35) が最良
> - 結果 artifact: `results/priority_rebuild/ml_phase1_v5/_case_{b,c,d,e,f}_*/case_*_summary_*.json` (規約上 commit 禁止 = git untracked)
> - log: `results/priority_rebuild/ml_phase1_v5/_logs/log_case_{b,c,d,e,f}_{smoke,full}.log` (12 ファイル・本セッション中盤に project root から移動)
>
> ### 次セッション CC 優先順位 (2026-05-26 セッション末更新・4 箇所改訂版整合)
>
> 1. **優先 1 — 現状把握 verify + 業界整合 verify (絶対遵守・最優先・L-220 同型再演防止)**:
>    - **auto-memory 2 件必読**: `feedback_current_state_verify_before_design.md` + `feedback_trade_ml_knowledge_gap.md` (= 最重要マーク)
>    - `grep -n "現フェーズ\|凍結\|大方針転換" WORKFLOW.md CLAUDE.md` で現状把握
>    - 「凍結ベースライン $370 / 手動 Priority 凍結 / ML pipeline 現役」再確認
>    - **設計提案・実装に着手する前に上記 verify を機械的証跡で出す** (= 出さずに進めるの絶対禁止)
> 2. **優先 2 — phase_flow_v4 改善案 (4 箇所改訂版) を本体に反映**:
>    - 参照: `.claude/memory/phase_flow_v4_reorder_proposal.md` (= 第 2 版・4 箇所改訂版・確定済)
>    - 改訂内容 (4 箇所のみ・順序変更なし):
>      1. Phase 4-c (Regime filter) 新規追加
>      2. Phase 4-a を独立工程化 (cluster 間相関 < 0.3 要件)
>      3. Phase 5 合格ライン 2 倍 (月 $1,900 → $3,800・DSR 50% degradation 想定)
>      4. Phase 5-d 動的化 (Half-Kelly + cluster 強度別配分)
>    - 反映先: `phase_flow_v4_with_recovery.md` 本体 + `cc_ml_design_spec.md` 整合改訂 + `phase_compliance_checklist.md` 整合改訂
>    - 各フェーズの判定方法は **業界標準と同じ** (= 進捗 verify のみ・月の売上判定は Phase 5 Replay で一括)
> 3. **優先 3 — Phase 1 v6 Layer 3 投入** (= 監査結果 §5 改善方向性 7 件反映):
>    - 案 f AFML 修正 (cross-validated primary predictions) / B-10 アルゴ多様化 / 正則化強化 / CPCV / ROC AUC
>    - 既存 untracked スクリプト (`run_lgbm_phase1_v5_case_b/c/d/e/f.py`) を Layer 3 仕様で修正してから commit
> 4. **優先 4 — trade_ml_pipeline_knowledge_base.md 新設 (= 私の理解度不足への根本対策・L-220 対策)**:
>    - **新規ファイル**: `.claude/memory/trade_ml_pipeline_knowledge_base.md`
>    - 内容: ML pipeline 業界標準フロー + 各フェーズの判定方法 + 5 レバー業界実装パターン + Lopez de Prado AFML / Stefan Jansen MLfAT chapter 別核心 + Hudson & Thames mlfinlab 機能 + Crypto futures algo trading 業界実例
>    - 構築方法: WebSearch 30 件 + WebFetch + 教科書知識統合 (= industry_benchmark KB と同パターン)
>    - 数セッションかけて構築する大きな仕事。優先 2/3 と並行 or 着手後
> 5. **優先 5 — セッション終了処理** (lessons + WORKFLOW 改訂34 + 改訂33 履歴降格)
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読・読了ゲート機械的証跡対象)
> - **WORKFLOW.md 改訂33 active** (本ブロック)
> - **CLAUDE.md** (Layer 2 更新済・industry_benchmark_knowledge_base 行追加)
> - **phase_flow_v4_with_recovery.md** (ML 学習正本・改訂対象)
> - **`.claude/memory/phase_flow_v4_reorder_proposal.md`** (= 4 箇所改訂版・第 2 版・確定済・次セッションで本体反映)
> - **lessons_active.md 直近 5 件** (L-220 → L-218 → L-217 → L-216 → L-215)
> - **cc_role.md §1.4 / §1.4.5 (改善 10 追加) / §1.4.6 (§1.4.6.1 業界整合 verify 追加) / §1.4.7**
> - **`feedback_current_state_verify_before_design.md`** (auto-memory・最重要マーク・auto-load)
> - **`feedback_trade_ml_knowledge_gap.md`** (auto-memory・最重要マーク・auto-load・ML pipeline 設計提案前の業界整合 verify 義務)
>
> #### Layer 2 (改善議論着手時)
> - **`.claude/memory/industry_benchmark_knowledge_base.md`**: 5 レバー定量根拠 + Phase 別合格基準 PnL 紐付け業界手法 (本セッション成果・維持)
> - **`.claude/audits/2026-05-26_phase1_v6_6cases_methodology_audit_report.md`**: 監査結果 §1-§9 + §10 補足メモ (次セッション着手前必須事項)
> - **`.claude/audits/inputs/_template.md`**: 監査依頼書テンプレ (L-218・auditor 宣言ブロック)
> - **`.claude/audits/inputs/2026-05-26_phase1_v6_6cases_methodology_audit_request.md`**: 旧形式依頼書 (auditor 宣言ブロック以前)
> - `cc_ml_design_spec.md`: ML pipeline 仕様・合否基準 (改善議論で改訂候補)
> - `phase_compliance_checklist.md`: Phase 別 verify 義務 (改善議論で改訂候補)
>
> #### Layer 3 (リファレンス・必要時参照)
> - `false_positive_incident_policy.md`: 関所 A-G + 類型 A-H + §0-1/0-2
> - `exchange_spec.md`: Bitget USDT-FUTURES BTCUSDT スペック (audit#19 確定値)
> - `lessons_archive.md`: L-152 以前
> - 既存 Phase 1 v5 実装 (案 a/b/c/d/e/f script + summary JSON・案 a/b/c/d/e 完走 + 案 f smoke)
>
> #### データ・環境
> - parquet 3 種 (train_2021_2024 / test_2025 / test_2026_q1) + .venv311
> - Phase 1 v6 5 案実装 script (commit `294a79f` 済・案 b/c/d/e/f) → Layer 3 投入時に修正
> - **案 e predictions**: `results/priority_rebuild/ml_phase1_v5/_case_e_triple_barrier/predictions_train_2021_2024.parquet` (Phase 4-b 単体検証 Entry 信号候補)
>   - ⚠️ **重要・未生成警告**: 現 `case_e_triple_barrier.py` 実装は summary JSON のみ出力で **predictions parquet 未保存**。Phase 4-b 単体検証着手前に case_e に predictions 保存追加 + 再実行 (60-90 分・1 並列順次) が必要。
> - log: `results/priority_rebuild/ml_phase1_v5/_logs/log_case_*.log` (12 ファイル・5 案実施時のログ保管場所)
>
> ### 目的整合性 1 行宣言 (cc_role §1.4.6)
>
> - **次タスク** = (1) 現状把握 verify → (2) 監査結果 §10 補足メモ Read → (3) phase_flow_v4 改善議論 (5 レバー観点) → (4) Phase 4-b 単体検証 or Phase 1 v6 Layer 3 投入
> - **現フェーズ目的への貢献根拠** = 本セッションで partial revert された「目標達成設計」を、**正しい現状把握** (= ML pipeline が現役・手動 Priority は凍結) の上で再構築する。L-220 同型再演を防ぐため、設計議論前に必ず現状 verify を機械的証跡で出す。

---

## 🧊 改訂32 ブロック (履歴・参照用)

### 旧フェーズヘッダ（2026-05-26 改訂32・**handoff_to_cc_v\* 廃止 + WORKFLOW 単一正本化 + phase_flow_v4 v5/v6 整合更新 + Phase 1 評価軸 5→3 指標 Exit 非依存化 (L-217) + Step I-4.5 本走で異常値スメル 8/8 ヒット (= L-215 設計逸脱事案発覚)**・次タスク = Phase 1 v6 6 案並列実装 (案 b/c/d/e/f 着手・3 指標 Exit 非依存判定))

> **【現在の正本ブロック・改訂32・2026-05-26 セッション末（5 セッション分の設計逸脱発覚 + 構造的再発防止策完了）】**
>
> ### 本セッション (2026-05-26) 完了事項
>
> #### 1. Step I-4.5 本走完了 (Critical-1/2 修正後 + 案 W/V revert 後 + 旧 grid)
> - 案 W (TP/SL grid 拡張) と 案 V (K=96 除外) を一度実装 (commit 5ceb004, e3d92ef) → CC 独立評価で **目的逸脱** と認め revert (commit aabed9d, 1bd2c6f)
> - Step I-4.5 本走 (`run_lgbm_phase1_v5_case_a_v2_v3.py --full` / 1.5 分完走 / 8 組合せ × 2 method × 3 fold) → **関所 A 8/8 異常値スメル ヒット** (合格ライン 20 倍超え・false_positive §5 関所 A 自動 STOP)
> - 公式 source: [`case_a_v2_v3_summary_labels_mfe_mae_pct_train_2021_2024.json`](results/priority_rebuild/ml_phase1_v5/_case_a_v2_v3/case_a_v2_v3_summary_labels_mfe_mae_pct_train_2021_2024.json)
> - Critical-1/2 修正で評価式は予測装置化したが、依然として現実的でない巨額数値 = **評価式に追加問題残存 (Phase 4-b 領域)**
>
> #### 2. 過去 5 セッション分の設計逸脱発覚 (L-215 級事案)
> - 2026-05-22 v22 で **Phase 1 v5 = 6 案並列確定** (案 a/b/c + 案 d Ranking LambdaRank + 案 e Triple Barrier multiclass + 案 f Meta-Labeling 2 段階 + Walk-forward Purged K-Fold 5 fold + DSR)
> - **実装は案 a (V3 14 ラベル独立 RMSE) のみ** で v23-v32 (= Step C-I 5 セッション) を回し続けた
> - CP3 監査 (v27) 結論「評価式暫定過大評価 7-8 割支配」を根拠に「案 a の評価式直す方が先」と判断 → 案 b/c/d/e/f 実装スコープから完全に外れた
> - 本セッション終盤で `learning_design_v4.md` + `phase_flow_v4_with_recovery.md` 全文読了で発覚
> - **5 セッション分のトークン・時間が Phase 1 v5 進捗ゼロで消費**
>
> #### 3. 構造的再発防止策完了 (handoff 廃止 + WORKFLOW 単一正本化)
> - **handoff_to_cc_v19〜v32 全 14 件を `.claude/instructions/archive/handoff/` に移送** (伝言ゲーム化経路の物理排除)
> - **`learning_design_v4.md` を `.claude/memory/archive/learning_design_v4_20260526.md` に移送** (phase_flow_v4 §2/§3 に統合済)
> - **`phase_flow_v4_with_recovery.md` を v5 整合に更新** (3 案 → 6 案 + Walk-forward Purged K-Fold 5 fold + DSR + 5 指標反映)
> - **CLAUDE.md Layer 1 必読リスト更新** (handoff 削除 + phase_flow_v4 追加)
> - **cc_role.md §1.4.6 (目的整合性ゲート・L-215) + §1.4.7 (handoff 廃止・L-216) 新規追加**
> - **WORKFLOW.md セッション終了処理セクション新設** (本セクション)
> - **lessons L-215/L-216 追加**
>
> #### 4. Phase 1 評価軸 Exit 非依存 3 指標化 (v6 改訂・L-217)
> - まこさん指摘「Entry のみで良し悪しの判定ってできるものなの？」を受けた CC 独立評価で v5 5 指標構成が **Entry 単独評価と Trading 評価を混在** させる構造的矛盾を発見
> - **Phase 1 評価軸を 5 指標 → 3 指標 Exit 非依存**に絞る (entropy lift > 10% / TP Precision > 0.5・TP_PCT 固定値 / Direction Accuracy > 0.55 (案 c のみ))
> - **Simulated PnL / DSR を Phase 5 合格条件に移動** (Trading 評価のため正しい配置・本丸 NET 基準とは別レンズ)
> - phase_flow_v4 v6 改訂で正本反映 (§2 Phase 1 / §4 全体フロー俯瞰 / §5.4 CP2 監査内容 / §6 改訂履歴)
> - lessons L-217 追加 (本件・L-215 の根本要因解明)
> - これにより過去 5 セッション (Step F-I・Simulated PnL 評価式改修) を Phase 1 で実施した構造問題 (Phase 4-b 領域の Phase 1 混入) が解消方向 = Phase 1 v6 は Exit 抜きで完結可能
>
> #### 5. 目的整合性 1 行宣言 (cc_role §1.4.6)
> - **次タスク** = Phase 1 v6 残り 5 案 (案 b/c/d/e/f) の並列実装着手
> - **現フェーズ目的への貢献根拠** = Phase 1 v6 (Entry AI が 6 案並列 + **3 指標 Exit 非依存** で機能するか測る) の本来の実装スコープに復帰 (案 a 単独 → 6 案並列・5 セッション分の設計逸脱を回収・Exit に依存しない純粋 Entry 評価で完結)
>
> ### 次セッション CC 優先順位
>
> 1. **優先 1 — Phase 1 v5 残り 5 案実装着手** (約 3-4 週間想定・learning_design_v4 archive §11 着手フロー v5 整合):
>    - 案 b: Entry Binary Classification (LightGBM binary objective + scale_pos_weight + entry_label = (MFE > X% and MAE > -Y%) ? 1 : 0)
>    - 案 c: Direction Multiclass (LightGBM multiclass num_class=3・LONG/SHORT/Flat)
>    - 案 d: Ranking LambdaRank (LightGBM objective='lambdarank'・MFE_pct ランキング)
>    - 案 e: Triple Barrier multiclass (Phase 0 v3.1 で生成済 28 ラベル列使用・LightGBM Multiclass)
>    - 案 f: Meta-Labeling 2 段階 (案 e primary → secondary で採用 / 見送り判定)
>    - Walk-forward Purged K-Fold 5 fold (mlfinpy.cross_validation.PurgedKFold) 全案で必須
>    - DSR > 1.0 補正必須
> 2. **優先 2 — Step I-4.5 異常値スメル 8/8 の原因切り分け (Phase 4-b 領域)**:
>    - 案 a 評価式の暫定問題は Critical-1/2 修正後も残存 → 評価式の現実性は Phase 4-b 完了後に正しく測れる
>    - 案 a の Simulated PnL 単独評価は一旦保留 (5 指標のうち 1 つ・他 4 指標は別測定)
> 3. **優先 3 — 案 a の残り 4 指標 (entropy lift / TP Precision / Direction Accuracy / DSR) 抽出** (= 案 a の Phase 1 v5 5 指標 verify 完成):
>    - 既存 case_a_v2_p1/p2/p3 + case_a_v2_v3 artifact から抽出可能
>    - 案 b〜f 学習結果と比較するベースライン値として保存
> 4. **優先 4 — CP6 監査 (関所 D 必須・別セッション起動・cc_role §1.4.5 適用)** (Phase 1 v5 6 案並列学習完了後)
> 5. **優先 5 — セッション終了処理** (lessons L-217+ + WORKFLOW 改訂33 active 新設 + 改訂32 履歴降格)
>
> ### 引き継ぎリソース 3 層構造
>
> #### Layer 1 (毎セッション必読・~700 行・読了ゲート機械的証跡対象)
> - **WORKFLOW.md 改訂32 active** (本ブロック)
> - **CLAUDE.md** (改訂22 ベース・Layer 1 必読リスト更新済)
> - **phase_flow_v4_with_recovery.md** (ML 学習正本・v6 Exit 非依存化更新済)
> - **lessons_active.md 直近 5 件** (L-217 → L-216 → L-215 → L-214 → L-213)
> - **cc_role.md §1.4 / §1.4.5 / §1.4.6 / §1.4.7** (同型バイアス + 監査別セッション化 + 目的整合性ゲート + handoff 廃止)
>
> #### Layer 2 (Phase 1 v5 着手時)
> - `cc_ml_design_spec.md`: ML pipeline 仕様・合否基準
> - `phase_compliance_checklist.md`: Phase 別 verify 義務
> - `archive/learning_design_v4_20260526.md`: 設計確定経緯 (引用のみ)
> - 既存案 a 実装ファイル (参考):
>   - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_rmse.py` (637 行・案 a 原型)
>   - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2.py` (597 行・案 a v2)
>   - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2_v3.py` (629 行・案 a v3・Critical-1/2 修正済)
>   - `scripts/priority_rebuild/run_phase1_v5_purged_kfold.py` (873 行・Purged K-Fold 共通 runner)
>   - `scripts/priority_rebuild/build_labels_pct.py` (Triple Barrier ラベル 28 列生成済・案 e/f 用)
>   - `scripts/priority_rebuild/dsr.py` (241 行・DSR 自前実装・test 12/12 PASS)
>
> #### Layer 3 (リファレンス・必要時参照)
> - `false_positive_incident_policy.md`: 関所 A-G + 類型 A-H + §0-1/0-2
> - `exchange_spec.md`: Bitget USDT-FUTURES BTCUSDT スペック (audit#19 確定値)
> - `lessons_archive.md`: L-152 以前 (Phase 1〜7-a / regime 研究時代教訓)
> - `archive/handoff/handoff_to_cc_v19〜v32`: 過去 handoff 履歴 (廃止前・引用のみ)
>
> #### データ・環境
> - parquet 3 種 (train_2021_2024 / test_2025 / test_2026_q1) + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
> - tp_hit_classifier 統合 predictions parquet: `_tp_hit_classifier/tp_hit_classifier_predictions_train_2021_2024.parquet` (136.7 MB・本セッション生成)
> - 案 a 全 artifact (Step I-3.1〜I-4.5 完走分・案 b/c/d/e/f 着手後も保持)

---

## 🧊 改訂31 ブロック (履歴・参照用)

### 🔴 旧フェーズヘッダ（2026-05-25 改訂31・**Step I-4.2 Critical-2 修正完了 (dsr ガード + 月次黒字率代替判定 + integration test) + commit dd80661**・次タスク = Step I-4.3 案 W (SL_PCT/TP grid 拡張) → 案 V (K96 除外) → Step I-3 再走）

> **【現在の正本ブロック・改訂31・2026-05-25 セッション末（Step I-4.2 完了 + 引き継ぎ伝言ゲーム化事案 L-214 + ルール消失復元）】**
>
> ### 本セッション (2026-05-25・前セッション 572e0b8 の続編) 完了事項
>
> #### 1. Step I-4.2 Critical-2 修正 (commit dd80661)
> - dsr.py: `compute_dsr_from_returns` に `std<1e-12` ガード追加 + input contract docstring (+29 行)
> - test_dsr.py: 失敗境界 test 2 件追加 (`constant_returns_case` / `extreme_sr_case`・**12/12 PASS**) (+38 行)
> - phase_compliance §1.6: 「複数 script interaction edge case verify」義務追加 (+1 行)
> - merge_step_i_summaries.py: dsr_pass を nan → 月次黒字率代替判定 (`THRESHOLD_MONTHS_POSITIVE=8`) に変更 + `dsr_judgment_method` を fold result に追加 + std ガード閾値を dsr.py 整合 (`1e-12`) に統一 (+18 / -2 行)
> - test_dsr_merge_interaction.py 新規 (125 行・**6/6 PASS**): 複数 script 相互作用 integration test
> - **追加発見 bug**: integration test 作成時に `compute_fold_sharpe_dsr` の std ガード閾値 (`<= 0`) が dsr.py (`< 1e-12`) と不一致 → 浮動小数点誤差 2.18e-19 がガードすり抜けて sharpe 異常値 (4.5×10¹⁵) 発生 → 同 commit で統一修正
> - 公式 source: smoke verify は Step I-4.5 で 8 組合せ一括 verify (CC 独立判断・本セッションは unit + integration test 18 件で実装信頼性確保)
>
> #### 2. 引き継ぎ伝言ゲーム化事案 (L-214) + ルール消失復元
> - **混乱経緯**: 本セッション開始直後、handoff v31 §2 を伝聞で読み「3 択提示」→ まこさん「資料読んだ？伝言ゲームになってない？」指摘 → L-212b 原本読了で乖離 4 件発見 (handoff v31 §2 が L-212b 4 項目を不完全要約・CP4/CP5/CP6 取り違え)
> - **根本原因**: `.claude/audits/` 保管ルールが 2026-05-21 cc_role 新規作成時に転記漏れで消失 → CP3.5/CP4 がファイル化されず handoff 概要のみ・CP5 が `.claude/instructions/` に混入
> - **改善 9 件**: handoff §2 項目数照合 / 擬似 signature 不一致明示 / WORKFLOW CP 監査一覧表 / Layer 1 必読に CP 監査追加 / 「機械的反映」表現厳格化 / **`.claude/audits/` 保管復元 (改善 6)** / handoff 起案者自己 verify / Layer 1 lessons 本文全文 / **監査立ち上げ別セッション化 (改善 9)** → L-214 で記録
>
> #### 3. 本セッション内で実施した改善 (3 件)
> - **改善 6 実体**: CP5 監査結果を `.claude/instructions/` → `.claude/audits/` に移動
> - **cc_role §1.4.5 追加**: 「監査結果保管 (.claude/audits/) + 監査立ち上げ別セッション化」ルールを cc_role に明記
> - **WORKFLOW §CP 監査一覧表**: 後述「## CP 監査一覧 (改訂31 新設・2026-05-25)」セクションを新設
>
> #### 4. 残り改善 (6 件) は handoff v32 §X で次セッションに継承
> - 改善 1 (handoff §2 項目数照合) / 改善 2 (signature 不一致明示) / 改善 4 (Layer 1 必読に CP 監査追加) / 改善 5 (「機械的反映」厳格化) / 改善 7 (handoff 起案者自己 verify) / 改善 8 (Layer 1 lessons 本文全文化)
> - 過去 CP 監査の後追いファイル化: CP3.5 (handoff v28 から) + CP4 (handoff v30 §1.4 + L-212b から)
>
> ### 次セッション CC 優先順位 (Step I-4.3 着手)
>
> 1. **優先 1 — Step I-4.3 案 W 実装 (約 1-2 日)**:
>    - `run_lgbm_phase1_v5_case_a_v2_v3.py` の SL_PCT grid 拡張 (0.3-0.8 → 0.3-1.5%)
>    - TP_PCT grid 上限拡張 (2.5 → 3.5%)
>    - smoke + 関所 A verify
> 2. **優先 2 — Step I-4.4 案 V 実装 (約 0.5 日)**:
>    - `merge_step_i_summaries.py` の判定対象を 6 組合せ (K=12,24,48) に限定
>    - K=96 LONG/SHORT を別レンズ評価 (Secondary Filter 候補)
> 3. **優先 3 — Step I-4.5 Step I-3 再走 (1-2 時間・1 並列順次・L-212a 整合)**:
>    - 修正後 case_a_v2_v3 で 8 組合せ × 2 method × 3 fold × 30 grid を再走
>    - 起動コマンド: `nohup python -u ... > log 2>&1 & disown` (L-211 整合)
>    - **本セッション Critical-2 修正 (dsr_judgment_method 等) の本走 verify 機会**
> 4. **優先 4 — Step I-4.6 CP6 監査** (関所 D 必須・**別セッション起動**・改善 9 適用):
>    - 修正後 0/16 から改善幅と Phase 2 進行可否判定
>    - 4 案合計 (Critical-1 + Critical-2 + 案 W + 案 V) の寄与率実証 (CP4 推定 75-95% 合計範囲)
>    - 結果ファイル: `.claude/audits/2026-XX-XX_step_i4_5_cp6_audit_report.md`
> 5. **優先 5 — L-214 改善 1/2/4/5/7/8 反映** (CLAUDE.md / cc_role / handoff テンプレ更新)
> 6. **優先 6 — 過去 CP 監査の後追いファイル化** (CP3.5 / CP4)
> 7. **優先 7 — セッション終了処理** (lessons L-215+ + WORKFLOW 改訂32 + handoff v33)
>
> ### 引き継ぎリソース (3 層構造)
>
> #### Layer 1 (毎セッション必読)
> - **handoff v32** (本セッション末作成): `.claude/instructions/handoff_to_cc_v32_session_20260525_step_i4_2_done.md`
> - WORKFLOW.md 改訂31 active ブロック (本ブロック) + CP 監査一覧表
> - CLAUDE.md (改訂22 ベース)
> - lessons_active.md 直近 5 件 (**L-214 → L-213 → L-212c → L-212b → L-212a**)
> - **cc_role.md §1.4.5 (新規・本セッション追加・`.claude/audits/` 保管 + 別セッション化)**
>
> #### Layer 2 (Step I-4.3 着手時)
> - 仕様書 v2 (Step I-4.1 用・参考): `.claude/instructions/2026-05-23_step_i4_1_case_a_v2_v3_critical1_spec.md`
> - CP5 監査結果 (Step I-4.1 用・新位置): `.claude/audits/2026-05-23_step_i4_1_critical1_cp5_audit_report.md`
> - 実装ファイル (本セッション commit dd80661 + 前セッション commit 572e0b8 = Step I-4.1 + I-4.2 完成):
>   - `scripts/priority_rebuild/dsr.py` (Step I-4.2 改修済)
>   - `scripts/priority_rebuild/test_dsr.py` (12/12 PASS)
>   - `scripts/priority_rebuild/test_dsr_merge_interaction.py` (6/6 PASS・新規)
>   - `scripts/priority_rebuild/merge_step_i_summaries.py` (Step I-4.1 + I-4.2 改修済)
>   - `scripts/priority_rebuild/run_lgbm_phase1_v5_case_a_v2_v3.py` (Step I-4.1 で新規・案 W 改修対象)
>
> #### データ・環境
> - parquet 3 種 + .venv311 (mlfinpy 0.1.2 / sklearn 1.8.0 / lightgbm 4.6.0 / scipy 1.17.1)
> - 前セッション artifact (Step I-3.1〜I-3.4・案 W/V 実装後 再走で書き換え)
> - 本セッション artifact なし (smoke は Step I-4.5 で実施)

---

## CP 監査一覧 (改訂31 新設・2026-05-25・L-214 改善 3 反映)

| CP | 実施日 | 対象タスク | 結果ファイル | 主要結論 |
|---|---|---|---|---|
| CP1 | (要遡及調査) | (要遡及調査) | — | — |
| CP2 | 2026-05-22 | Step G ML pipeline 検証 | `.claude/audits/2026-05-22_audit_routeB_records.md` (要 grep verify) | Critical 2 + Major 4 (一部反映) |
| CP3 | 2026-05-23 | Step H 異常値スメル 6/8 ヒット | `.claude/audits/` 内 (要 grep verify) | 案 Y (Phase 4-b 前倒し) 採用 |
| CP3.5 | 2026-05-23 | Step I-1 仕様書 v2.1 | **未ファイル化 (handoff v28 内記載のみ・後追い起案推奨)** | Critical 2 + Major 5 + Minor 4 |
| CP4 | 2026-05-23 | Step I-3.5 §4.1 v5.1 判定 (0/16 ALL PASS) | **未ファイル化 (handoff v30 §1.4 + L-212b 本文に記録・後追い起案推奨)** | **CONDITIONAL NO-GO** / Critical-1 (time_exit naive) + Critical-2 (DSR 設計階層誤認) / 案 A 推奨 (1 週間並列 4 タスク) |
| CP5 | 2026-05-23 | Step I-4.1 仕様書 v1 (Critical-1 修正) | `.claude/audits/2026-05-23_step_i4_1_critical1_cp5_audit_report.md` ✅ (2026-05-25 移動済) | CONDITIONAL GO / Critical 2 + Major 4 + Minor 3 = 9 件 (v2 で全件反映済) |
| CP6 | (Step I-4.5 完了後・別セッションで起動) | Step I-3 再走後の §4.1 判定再評価 | `.claude/audits/2026-XX-XX_step_i4_5_cp6_audit_report.md` (将来) | 未実施 |

**運用ルール (改訂31)**:
- 監査実施時は本表に追記 (実施日 / 対象 / 結果パス / 主要結論)
- 監査結果ファイルは必ず `.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md` (cc_role §1.4.5)
- 監査立ち上げは別 claude code セッションで実施 (cc_role §1.4.5・同型バイアス回避)
- セッション終了処理のチェックリストに「CP 監査一覧表の更新」を追加 (省略禁止)

---

## 📚 履歴 archive 参照

WORKFLOW.md は 2026-05-22 改訂22 で再スリム化 (672 → 358 行・履歴 313 行を archive 移動)。**2026-05-27 改訂36 で再々スリム化 (1629 → 889 行・改訂 30-23 ブロック 740 行を archive 移動・L-216 cc_role §1.4.7 ルール実施)**:

| archive ファイル | 範囲 | 行数 |
|---|---|---|
| [archive/workflow/WORKFLOW_archive_revisions23-30_20260527.md](archive/workflow/WORKFLOW_archive_revisions23-30_20260527.md) | 改訂30 / 29 / 28 / 27 / 26 / 25 / 24 / 23 (= Step H / Step I-1〜I-4 / dsr 統合 / CP3.5/CP4/CP5 監査結果反映) | 749 |
| [archive/workflow/WORKFLOW_archive_20260522.md](archive/workflow/WORKFLOW_archive_20260522.md) | 改訂20 / 19 / 18 / 17 / 16 / 15 表記 | ~250 |
| [archive/workflow/WORKFLOW_archive_20260521.md](archive/workflow/WORKFLOW_archive_20260521.md) | 改訂13 / 14 / 15 / 7 + 試行禁止リスト + 旧 Priority パラメータ + Replay コマンド (旧フロー) + 引き継ぎリソース (旧版) | 538 |

履歴セクションの読了は **次セッション着手判断には不要**。現フェーズ判定で過去経緯を参照したい時に該当 archive を find で開く。
