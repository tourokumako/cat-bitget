# WORKFLOW.md — cat-bitget 作業フロー

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
- **完了報告必須証跡 5点**（2026-05-08 追加 / 5点目 2026-05-09 追加・L-162）:
  1. **コード総点検 grep 結果**（全件・"no matches"含む・関連スクリプト全部）
     - 4種の grep: ① TF endswith/startswith ② TFリスト固定値 ③ カテゴリ固定値 ④ 絞り込み処理（best 1/argmax/nlargest(1)）
  2. **数値の二重提示**（サマリー + 出典ファイル引用・行番号付き）
  3. **成果物ファイルの実体**（チャット側に届く形・パス + 行数 + 更新時刻）
  4. **実行ログ**（コマンド・開始時刻・終了時刻・所要時間・終了コード）
  5. **絞り込み示唆語彙の自己 grep 結果**（全件・"no matches"含む・チャット出力 + 報告 md ファイル対象）（L-162・2026-05-09 追加）
     - grep 語彙: 「採用候補」「効く/効かない」「重要」「優先」「不要」「切れる」「残せる」「除外して良い」「使える」「意味がある/ない」
     - 違反検出時: 数値 + 軸/カテゴリ間比較に表現を置き換えてから報告完了とする
     - 背景: L-159/L-160 を追加したのに 1 日で再発した事実は教訓追加の限界を示す。「頭で分かっていても漏れる」癖は手続きで矯正する（思考フレーム自己点検 L-136 と同じ思想）
  - 1つでも欠けたら完了とみなさない
  - 「総点検したから違反なし」を grep 結果なしに主張しない
  - 「やった」「完了」を実行ログなしに主張しない
  - 「絞り込み示唆語彙なし」を grep 結果なしに主張しない（L-162）
  - 「実は完了済み」を主張する場合は該当ターン番号と全文を再提示する

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

Priority 再構築フェーズの**設計マトリクス・進捗管理表・検証結果集計表・教訓・試行禁止リスト**はすべて **`.claude/memory/priority_rebuild.md`** が**唯一の正本**。
WORKFLOW.md には設計詳細・進捗詳細を書かない（重複は不整合の元・regime 研究と同じ管理パターン）。
セッション開始時・段階遷移時・採否判定時は priority_rebuild.md を読み、更新する。

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
① 合格ライン 月次 ≥ $1,900/月 − 凍結ベースライン $370/月 = 不足 $1,530/月（5.1倍ギャップ）
   ※ デイリー $60 は目安・日次絶対下限ではない・判定は月次のみ・一次ソース: MEMORY/project_goal.md
② 現フェーズ確認（Priority 再構築・段階 A-1 / A-2 / A-3 / B / C / D のどこか明示）
③ 当該段階の前提条件（K 窓 1h/2h/4h/8h・LONG/SHORT 同時・walk-forward 5 fold・MFE/MAE 中央値 + 比）を再確認
④ [Step 0 D] 段階完了後の $60/day 到達可能性: YES / NO / 試算未済
   ※ 段階 A-1〜A-2 完了前は「試算未済（段階 B Replay で初めて判定）」と書いてよい
   ※ この 1 行が出るまで提案・分析を開始しない
⑤ [Step 0 E] 着手前の目的整合性 3 項目チェック（L-166）:
   - データ粒度: 検証対象と一致しているか
   - データカバレッジ: 判断分岐に十分なサンプル数か
   - 直接性: 目的を直接測れる手段か（代理指標は要警戒）
   → 1 つでも NO/不明なら、作業着手前に提示して GO 待ち
⑥ [Step 0 F] 前セッションで議論が行き詰まった or 同じ提案を繰り返した記録があるか確認。
   ある場合: 思考フレーム/目標コミット 自己点検を 1 回実行してから ⑦ に進む
⑦ 今セッションのタスクを優先順位付きで提示 → STOP
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
- 最終検証: 365d Replay で NET 評価（walk-forward 5 fold）

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
| `priority_rebuild/` | Priority 再構築フェーズ（A-1 ラベル生成・A-2 k=2 探索 等）|
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
| `priority_rebuild/`    | Priority 再構築フェーズ出力（A-1 ラベル / A-2 探索結果 等）|
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
> 2026-05-11 大方針転換で凍結。Priority 再構築フェーズの改善サイクルは段階 A-1〜D（[現フェーズ section](#-現在のフェーズ2026-05-11-改訂11大方針転換) 参照）。
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

## 🔴 現在のフェーズ（2026-05-11 改訂11・大方針転換）

**フェーズ: Priority ゼロから再構築 — MTF × 全指標組合せで Entry タイミング精度向上**
**regime 判定研究: 🧊 凍結**（素材転用のみ・新規調査停止）

設計詳細・段階別仕様・進捗管理表・検証結果集計表は **[`.claude/memory/priority_rebuild.md`](.claude/memory/priority_rebuild.md) §0〜§7 が唯一の正本**。本ファイルではポインタのみ記載。

### 方針転換の背景（要約）

- regime 精度天井（v14 56% / stage3 33%）+ regime label 情報密度低 + 時間軸ズレ（持続 16-28h vs trade 15min）
- → regime 研究で蓄積した 1,432 指標素材を Priority Entry 規則の最適化に転用

### 段階別フロー（概要のみ・詳細は priority_rebuild.md §2）

| 段階 | 内容 |
|---|---|
| A-1 | 学習データ生成（5m × 1,432 指標 × 未来 MFE/MAE ラベル）|
| A-2 | k=2 全探索（102 万組）+ walk-forward 5 fold 評価 |
| A-3 | 結果視認 → Entry 規則設計 |
| B | 新 Entry 規則 + Exit で 365d Replay 検証 |
| C | ML 回帰モデル（B 頭打ち時のみ）|
| D | 最終 Replay → 採否判定 |

### 凍結時点の素材転用一覧

regime 研究は凍結したが、以下の素材は Priority 再構築フェーズで **再利用する**:

| 用途 | 凍結時点の成果物 |
|---|---|
| 1,432 列の指標素材 | [pruned_column_list.json](results/regime_label_analysis/pruned_column_list.json) + 計算ロジック [analyze_regime_label_features.py](scripts/regime/analyze_regime_label_features.py) / [analyze_stage1*_meta.py](scripts/regime/) / [shape_features.py](scripts/regime/shape_features.py) |
| k=2 全探索フレーム | [stage2_combination_search.py](scripts/regime/stage2_combination_search.py) のフレーム流用（評価関数だけ MFE/MAE に差し替え） |
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

## 🔴 次のタスク（2026-05-13 改訂17・0-β 完了 → Web Claude 報告）

**段階 0-α + 0-β 頭打ち原因分析 完了。両結果を Web Claude に報告して A-2 大枠ドラフトを確定する。**

### 0-β 追加分析 完了状態（2026-05-12）

- 仕様: [headroom_analysis_addendum_spec.md](.claude/memory/headroom_analysis_addendum_spec.md)
- 成果物: [results/priority_rebuild/headroom_analysis_addendum_summary.md](results/priority_rebuild/headroom_analysis_addendum_summary.md) + step5-8 CSV
- スクリプト: [scripts/priority_rebuild/headroom_analysis_addendum.py](scripts/priority_rebuild/headroom_analysis_addendum.py)
- **暫定判定: 構造的限界 + LONG Entry 規則の質低（両方該当）**
  - worst month の trade 数が極端に少ない: YES（worst 2025-09 = 4 trade / median = 48）
  - LONG 完璧 K=96 Exit でも合格ライン未達: YES（LONG-only monthly_mean=$1,715 / 月 ≥$1,900 = 3/9 ヶ月）
- A-2 大枠ドラフトへの追加示唆:
  - 単純な ML Exit では届かない（worst month の発火数自体が極端に少ない）
  - regime=range / uptrend で発火する新 Priority の追加が必須
  - LONG Entry 規則の質改善（取りこぼし削減）

### Web Claude への報告材料（次セッションで Web Claude に共有）

1. [headroom_analysis_summary.md](results/priority_rebuild/headroom_analysis_summary.md) — 0-α 結果（4手順分析）
2. [headroom_analysis_addendum_summary.md](results/priority_rebuild/headroom_analysis_addendum_summary.md) — 0-β 追加切り分け
3. [handoff_to_web_claude.md](.claude/memory/handoff_to_web_claude.md) — Web Claude 分業の正本

### 次セッション最初にやること（順番）

1. このファイル §🔴 を再読
2. 上記 0-α / 0-β サマリーを Web Claude に共有
3. Web Claude が「構造的限界 + LONG Entry 規則質低」を踏まえて A-2 大枠ドラフトを更新・確定
   - regime=range / uptrend 新 Priority / LONG 規則改善 を A-2 設計に盛り込む
4. Web Claude 結論を [priority_rebuild.md](.claude/memory/priority_rebuild.md) §2 に反映
5. 実装フェーズ（A-2 探索 or B Replay）へ

### 0-α 完了状態（2026-05-12）

- 5 ファイル: [results/priority_rebuild/headroom_analysis_summary.md](results/priority_rebuild/headroom_analysis_summary.md) + step1-4 CSV
- ⑮ ダッシュボードタブ: [dashboard/index.html](dashboard/index.html) `data-tab="headroom"` (6 パネル + 判定バナー)
- スクリプト: [scripts/priority_rebuild/headroom_analysis.py](scripts/priority_rebuild/headroom_analysis.py)
- **暫定判定: 構造的限界の可能性**（完璧 K=96 Exit でも全月 $1,900 不達 / worst=$40.41 / 0/57 パターン合格）
- 構造ボトルネック: 月次 Entry 発火数の極端な偏り（4-240 trade/月）。2025-09 は matched 4 trade のみ

### 段階 A-1 完了状態（変更なし）

- train: `results/priority_rebuild/labels_mfe_mae_train_2021_2024.parquet` (394,573 行 / 1.05 GB)
- test:  `results/priority_rebuild/labels_mfe_mae_test_2025.parquet` (105,120 行 / 0.30 GB)
- 段階 B 温存: 2026-Q1 25,824 行（parquet 未生成）

### 引き継ぎ資料

- [handoff_to_web_claude.md](.claude/memory/handoff_to_web_claude.md) — Web Claude 分業の正本
- [headroom_analysis_spec.md](.claude/memory/headroom_analysis_spec.md) — 頭打ち原因分析 仕様書（0-α 実行仕様）
- [headroom_analysis_summary.md](results/priority_rebuild/headroom_analysis_summary.md) — **0-α 結果サマリー（Web Claude への報告内容）**

### 次セッション最初にやること（順番）

1. このファイル §🔴 を再読
2. [headroom_analysis_summary.md](results/priority_rebuild/headroom_analysis_summary.md) を Web Claude に共有
3. Web Claude が「構造的限界の可能性」を踏まえて A-2 大枠ドラフトを更新・確定
   - 特に「ML を Exit に入れるだけでは届かない」「Entry 発火頻度の月次安定化」「新 Priority 並立」を盛り込めるか
4. Web Claude 結論を [`priority_rebuild.md`](.claude/memory/priority_rebuild.md) §2 に反映
5. 実装フェーズ（A-2 探索 or B Replay）へ

### Step 0 セッション開始時に必読（厳守・順番通り）

1. WORKFLOW.md（このファイル・現フェーズ + 次のタスクのポインタ）
2. [`headroom_analysis_summary.md`](results/priority_rebuild/headroom_analysis_summary.md) ★0-α 結果（Web Claude 報告材料）
3. [`headroom_analysis_addendum_summary.md`](results/priority_rebuild/headroom_analysis_addendum_summary.md) ★0-β 追加切り分け（Web Claude 報告材料）
4. [`handoff_to_web_claude.md`](.claude/memory/handoff_to_web_claude.md)
5. [`priority_rebuild.md`](.claude/memory/priority_rebuild.md)
6. [CLAUDE.md](../CLAUDE.md)
7. [lessons_active.md](.claude/memory/lessons_active.md) **L-168〜L-172 重点**

---

## 試行禁止リスト

Priority 再構築・設計関連の禁止事項は **[priority_rebuild.md §6](.claude/memory/priority_rebuild.md) が唯一の正本**。本ファイルには **行動ルール関連のみ**残置。

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
> 新フローの Replay コマンドは段階 B 着手時に新規定義予定。

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
- **.claude/memory/priority_rebuild.md**（**Priority 再構築の唯一の正本**・設計マトリクス + 進捗 + 結果集計）
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
