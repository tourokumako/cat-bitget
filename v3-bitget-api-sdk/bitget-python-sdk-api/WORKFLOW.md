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

## シグナル管理

シグナル候補・レジーム×方向マッピング・検証実績は **`.claude/memory/signal_ledger.md`** が**唯一の正本**。
WORKFLOW.md にシグナル個別の状態を書かない（重複は不整合の元）。
セッション開始時・新規シグナル検証時・Priority 化時は signal_ledger.md を読み、更新する。

---

## Step 0: セッション開始プロトコル（省略禁止）

```
① 目標 $60/day − 現在 $5.97/day = 不足 $54/day
② 現フェーズ確認（regime研究中 / Priority最適化停止中 を明示）
③ 現フォーカスレジーム（DOWNTREND）の現状 vs 目標 $60/dt-day
④ [Step 0 D] 目標: $XX/dt-day / 現状: $YY/dt-day / 理論最大: $ZZ/dt-day → 到達可能性: YES/NO
   ※ この1行が出るまで提案・分析を開始しない
⑤ [Step 0 E] 直近タスク期待値合計: $AA/dt-day / 残差: $BB/dt-day
   カバー率 = AA/BB × 100%
   → カバー率 < 50% の場合: 「既存タスクのみでは目標到達不可能。
     新 Priority 設計を直近タスク1として再配置を検討」と明示する
⑥ [Step 0 F] 前セッションで議論が行き詰まった or 同じ提案を繰り返した記録があるか確認。
   ある場合: 思考フレーム/目標コミット 自己点検を 1 回実行してから ⑦ に進む
⑦ 今セッションのタスクを優先順位付きで提示 → STOP
```

レジーム移行条件: 現レジームが目標達成後のみ（DOWNTREND → RANGE → UPTREND）

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

### レジーム切り替え方針（2026-04-21 確定）
- 日足MA70を基準に downtrend / range / uptrend の3レジームに切り替える
- 各レジームに方向性の合う Priority を割り当て、個別に最適化・設計する
- 現状 Priority は「方向性が近いもの」をスタート地点として育てる
- 最終検証: 365d Replay で GO/NO（ここでの再チューニング禁止）

### 実装方針
- 全Priority: 5m足・Priority単位で独立最適化
- ポジションサイズ上限: 0.12 BTC/trade（増加禁止）
- 上限内でのPriority別配分は自由（例: P23=0.06、P3=0.01）
- 複数Priority並立の目的: リスク分散。詰まったら「新Priority追加」であり「サイズ増加」ではない
- 時間帯フィルターは個別Priority最適化では禁止。統合調整フェーズで実施

---

## 改善サイクル（Priority最適化フェーズ用・現在は凍結中）

**Step 1. 構造把握**
cat_v9_decider.py（Entry条件）・replay_csv.py（Exit優先順位）・cat_params_v9.json（現在値）を読む。
CSVにmfe_usd/mae_usd/exit_reason/hold_minが揃っているか確認する。

**Step 2. 結果分析**（グリッドサーチ前・省略禁止）

- **0. ポジション構造**: add_count × exit_reason マトリクスを作る。TIME_EXITが構造的コストか・フィルターで削れるかを1文で言語化してからA/Bへ進む
- **A. なぜ負けているか**: exit_reason別 件数/NET/avgMFE。MFEとMAEから損失の性質（即逆行 or 長期漂流）を特定する

  **TIME_EXIT分類**:
  - TYPE I（MFEが小さい・概ね<$5）: Entry品質問題 → フィルター強化（ATR/ADX/RSI）
  - TYPE II（MFEが大きいが戻った・概ね>$15）: Exit設計問題 → TRAIL/PROFIT_LOCK改善
  - 採用条件: 「件数削減」ではなく「TIME_EXIT per-trade 平均損失改善 かつ 全体NET改善」で評価
- **B. なぜ勝てないか**: TIME_EXIT中のMFE/TP比率・TP_FILLEDのMFE余裕を確認
- **C. 総合判断**: A・Bを並べてどちらを先に解決するか決めてから Step 2.5 へ

> 単位ルール: $/regime-day（= Priority NET ÷ 対象レジーム日数）で集計・提示する。$/total-dayは禁止。

**Step 2.5. シグナル理解の言語化**（グリッドサーチ設計前・省略禁止）

① シグナルが「何を捉えているか」を1文で言語化する
② 期待する価格挙動を時間軸で定義する（理想TP・許容・崩壊のそれぞれ何分で解決するか）
③ 「自然な解決時間」と現在のTP幅・TIME_EXITを比較する。乖離が大きければExit全面見直しを優先する
④ 1日の最大発火スロット数（= 24h ÷ avg_hold）と現状件数/dayを比較し、抑圧要因を特定する
→ ユーザーに提示してGO待ち ← STOP

**Step 3. 仮説立案**
損失 vs 成功トレードの指標分布を比較し「その差が損失を説明できるか」を確認する。
候補パラメータの変更効果（件数増減・NET増減）を事前推定する。根拠なしの仮説は出さない。

**Step 3.5. 仮想シミュレーション**（グリッドサーチ前・省略禁止）

results CSV の per-trade 指標（adx_at_entry / atr_14 / rsi_at_entry 等）を pandas でフィルタして NET を瞬時に推定し、有効な軸・範囲を絞り込んでからグリッドサーチを設計する。

```python
p = df[df['priority']==TARGET].copy()
for threshold in candidates:
    filtered = p[p['adx_at_entry'] >= threshold]
    print(threshold, filtered['net_usd'].sum() / DT_DAYS)
```

→ 絞り込み結果を提示してGO待ち ← STOP

**Step 4. グリッドサーチ設計・実行**
- データ期間: 対象PriorityのターゲットREGIMEが密集した期間を選ぶ
- Phase 1（方向確認）: 各軸3点（低・中・高）。効かない軸はPhase 2から除外
- Phase 2（絞り込み）: 有効軸のみ・3〜5点・組み合わせ≤15
- OOS検証: グリッド後に365d Replay（regime_switch=ON）で $/regime-day > ベースラインを確認
- 採用基準: ① 365d $/regime-day > ベースライン ② 全体NET改善 ③ per-trade NET > 手数料
- TP変更時は手数料計算を先に実施（L-40）
→ grid_search.py更新後、実行コマンドをユーザーに提示 ← STOP

**Step 5. 結果評価** → 上位パターン比較表・推奨Before/After。未達ならStep 3へ ← STOP
**Step 6. 実装** → diff提示・GO待ち ← STOP
**Step 7. 最終Replay** → コマンド提示 ← STOP
**Step 8. 採用判定** → 「採用しますか？」。打ち切り前に未試行軸がないか確認 ← STOP
**Step 9. baseline更新** → $/regime-day表・$/total-day表を更新。目標との残差を再計算
**Step 10. Gitコミット** → ユーザーの明示OK後のみ ← STOP

---

## 新規Priority設計フロー（P1/P21等・新規追加時）

1. 必要貢献額を逆算してシグナルの最大期待値が届くか確認する（届かなければ設計変更）
2. シグナルエッジをフィルターなし・タイトなTP/SLで先に検証する（勝率60%未満は却下）
3. Entry特性を言語化してからExitをゼロから設計する（既存流用禁止）
4. 実装 → Replay → 必要貢献額を満たすか判定

---

## 🔴 現在のフェーズ（2026-04-27時点・唯一の正本）

**フェーズ: regime判定研究中（レシピ型 grid search 設計 + ラベル付け 1826日）**
**Priority個別最適化: regime確定まで全停止**

> **regime研究の詳細は `.claude/memory/regime_research.md` が唯一の正本**
> （経緯タイムライン・判定軸マトリクス・試行履歴・既知リスク・凍結リソース・候補B評価軸・**§10 レシピ型設計仕様**を全集約）
>
> **段階1〜8の表記は廃止**。試行単位 = 完全レシピ（L-137）。判定軸マトリクスはレシピ評価結果から逆算して更新する。
> **§8 はレシピ型探索戦略 S1〜S5 に書き換え済**（2026-04-27）。**§10 にレシピ型設計仕様を新設**（試行単位定義・評価フロー・初期テンプレ12件・harness仕様）。

### 要点抜粋（詳細は regime_research.md）

- **既試行**: 日足ルール（採用中）/ 1h+ヒステリシス（不採用）/ v3スコアリング（不採用）/ Gaussian HMM（不合格）/ Mom 1h ルール（不採用）/ PELT（不採用）/ 教師あり週52本+RF/GB（L-129過学習）
- **未試行多数**: レシピ型探索全般（時間軸セット × 全カテゴリ指標 × 集約方法）・MiniROCKET/TS2Vec 等
- **評価本丸**: 月単位の支配 regime が肉眼判定と一致するか（L-126）

---

## 🔴 次のタスク（2026-04-27時点）

**並行2タスク（ラベル付け中・私=設計）**:

### A. まこさん作業: 1826日肉眼ラベル付け ✅ 完了（2026-04-27）
- 1826/1826 (100%) — downtrend 536日(29.4%) / range 691日(37.8%) / uptrend 599日(32.8%)
- 期間: 2021-04-01〜2026-03-31
- UI: http://localhost:8765/index.html → タブ⑤「日次肉眼判定（5年）」
- 進捗確認: `python3 scripts/regime_label_progress.py`

### B. Claude 作業: レシピ型 grid search 設計

**正本**: [.claude/memory/regime_research.md §10](.claude/memory/regime_research.md)

**現状**: 草案レビュー1巡完了（2026-04-27）。§10.1〜§10.7 確定済み。

**進捗**:
- ✅ §10.1 試行単位の定義（5要素・値域）
- ✅ §10.2 評価フロー（日次70% / 月支配80% / 候補B / R01比NET方向チェック）
- ✅ §10.3 既存資産の扱い（流用 / 再評価から / 指標部品扱い）
- ✅ §10.4 初期テンプレ12件（R01〜R12）
- ✅ §10.5 残18件起案方針（月支配変種 → 4h変種 → 5m変種 → その他の優先順）
- ✅ §10.6 harness仕様（recipe_grid_search.py + recipe_top10.md トップ10サマリ）
- ✅ §10.4 レシピ表 R01〜R35（35件・**2026-04-27 凍結**・全件採用）
- ✅ harness 実装（`cat/recipe/` パッケージ + `scripts/recipe_grid_search.py` + `configs/recipes.yaml`・2026-04-27）
- ✅ smoke test 合格（R01〜R03・365日ラベルで exit 0・致命バグなし。hierarchical の構造的限界を L-138 として記録）
- ✅ 1826日OHLCV取得（`data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv`・525,708バー・32.7MB・2026-04-27）
- ✅ R01〜R03 を 1826日全期間で再走 → L-138 解消確認（DT予測 367日出る）
- ⬜ **次の作業**: configs/recipes.yaml に R04〜R35（残32件）を追加 → 全件 default-grid で本走査
- ⬜ 全35レシピ default 通過後: S2 閾値前向き選択（5×5 grid）→ S3 上位N抽出 → S4 クロス世代 → S5 最終OOS

#### 1826日 default-grid 結果（R01〜R03 / 2026-04-27）

| Recipe | monthly | daily | DT% | UT% | RANGE% | 候補B |
|--------|---------|-------|-----|-----|--------|-------|
| R03 月支配＋日補正 | 1.00 | 0.52 | -0.24 | +0.28 | ±0.03 | ❌（M_dom直結のため評価対象外）|
| R02 1h多数決 | 0.42 | 0.37 | -0.73 | +0.73 | ±0.11 | ❌（DT基準-0.82%まで0.09pt）|
| R01 ベースライン | 0.22 | 0.33 | -0.03 | +0.18 | ±0.57 | ❌ |

> 観察: R02 が R01 を全項目で上回る（多時間軸合議が単一時間軸より有意な兆候）。R02 の DT は基準にあと 0.09pt なので R04〜R35 で DT 系シグナル強化レシピが通る可能性。

#### 1826日OHLCV 再取得手順（コミット対象外のため）

```
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/fetch_ohlcv.py --start 2021-04-01 --end 2026-04-01
# → data/BTCUSDT-5m-2021-04-01_03-31_1826d.csv (約1分・32.7MB)
```

**設計探索戦略**: S1テンプレ起案 → S2 閾値前向き選択 → S3 上位N抽出（R01比NET方向チェック含む）→ S4 クロス世代 → S5 最終OOS

### Step 0 で必ず確認すること

セッション開始時に確認:
1. 現フェーズ = regime研究中（レシピ型 grid search + ラベル付け1826日）
2. ラベル進捗（`scripts/regime_label_progress.py` 実行）
3. レシピ型設計の進捗（regime_research.md §10 のどのチェックボックスまで埋まっているか）
   - 現状（2026-04-27）: §10.1〜§10.7 確定済 / 残18件起案待ち / harness 未着手
4. 試行単位 = レシピ全体（部品単独評価は禁止・L-137）
5. 設計仕様の正本は **regime_research.md §10**（WORKFLOW.md には進捗のみ書く・仕様の二重化禁止）

---

## 試行禁止リスト

### regime判定研究関連

→ **`.claude/memory/regime_research.md` §7 が正本**。重複を避けるためここでは省略。

### Priority最適化関連（regime確定まで全停止）
- ❌ Replay組み込み・Priority最適化への着手（regime確定まで全停止）
- ❌ 1週ラグ運用（regime切替の意味なくなる）
- ❌ 「regime廃止・Priority個別判定」提案（Phase 1 失敗確定済・L-127）
- ❌ 既存Priority(P1/P2/P3/P4/P21/P22/P23/P24)の 1m足回帰（CLAUDE.md）
- ❌ ポジションサイズ増加でスケール（CLAUDE.md）
- ❌ マルチシンボル化（CLAUDE.md）
- ❌ ratchet型 Exit（PROFIT_LOCK / TRAIL_EXIT / MFE_DRAWDOWN_CUT）を P23 に追加（L-114）

### 行動ルール関連
- ❌ 設計判断を感覚で進める（feedback_quantitative_comparison）
- ❌ ユーザーの感覚発言を採用根拠化する（同上）
- ❌ WORKFLOW フェーズと照合せず脇道に逸れた提案を出す（2026-04-27 教訓）

---

## 既採用パラメータ（regime確定まで凍結中・解凍は再評価後）

regime 判定確定後にゼロから再評価（lookahead-safe + 新regime label）。

| Priority | 凍結パラメータ | 当時の $/dt-day |
|---------|--------------|---------------|
| P21 | TRAIL_RATIO=0.9 / MFE_GATE_PCT=0.04 / TIME_EXIT_MIN=180 / ATR14_MIN=150 | $11.41（look-ahead プレミアム含む） |
| P2 | TP_PCT=0.006 / MFE_STALE_GATE=3.0 / ATR14_MIN=100 / ATR14_MAX=300 | $4.75（同上） |
| P23 | TP_PCT=0.012 / HIGH_ADX_THRESH=40 / HIGH_ADX_ATR_MIN=200 / TIME_EXIT_MIN=480 | $21.32（look-ahead プレミアム-$4.98含む・SAFE値 $16.34） |
| P4 | ATR14_MIN=200 / TP_PCT=0.005 | -$0.67/range-day |

replay_csv.py: `--regime-safe` 実装済み（コード修正のみ・3関数並走）。本番経路は未対応。

---

## Replayコマンド（参考・現在は実行凍結中）

```bash
# 180d グリッドサーチ用
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/grid_search.py data/BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv

# 90d Replay（regime_switch=ON・全Priority）
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv --regime

# 365d OOS検証
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-5m-2025-04-01_03-31_365d.csv --regime
```

---

## 確定パラメータ表（凍結中・参考用・2026-04-22時点）

| Priority | パラメータ | 値 |
|---------|-----------|-----|
| P2-LONG | P2_TP_PCT | 0.006（2026-04-25採用・$2.32→$4.75） |
| P2-LONG | P2_ATR14_MIN / ATR14_MAX | 100.0 / 300.0 |
| P2-LONG | P2_MFE_STALE_GATE_USD / HOLD_MIN | 3.0（2026-04-25採用）/ 90.0 |
| P23-SHORT | P23_TP_PCT | 0.012 |
| P23-SHORT | P23_TIME_EXIT_MIN | 480（実効240min via DOWN_FACTOR=0.5） |
| P23-SHORT | P23_ADX_MIN/MAX | 30.0 / 50.0 |
| P23-SHORT | P23_ATR14_MIN | 150.0 |
| P23-SHORT | P23_HIGH_ADX_THRESH / P23_HIGH_ADX_ATR_MIN | 40.0 / 200.0（2026-04-24採用） |
| P23-SHORT | P23_MFE_STALE_GATE_USD / HOLD_MIN | 4.0 / 30.0 |
| P23-SHORT | P23_SHORT_PROFIT_LOCK_ENABLE | 0 |
| P23-SHORT | P23_STOCH_REVERSE_EXIT_ENABLE | true |
| P23-SHORT | P23_STOCH_EXIT_MFE_GATE | 20.0 |
| P23-SHORT | P23_STOCH_EXIT_MIN_HOLD | 150.0 |
| P23-SHORT | P23_STOCH_EXIT_UNREAL_MIN | 0.0 |
| P21-SHORT | P21_TRAIL_RATIO / P21_MFE_GATE_PCT | 0.9 / 0.04（2026-04-25採用・$7.51→$11.41） |
| P21-SHORT | P21_TIME_EXIT_MIN | 180（2026-04-24採用・実効90min） |
| P21-SHORT | P21_SL_PCT | 0.02 |
| P22-SHORT | P22_TIME_EXIT_DOWN_FACTOR | 0.4 |
| P4-LONG | P4_TP_PCT | 0.003 |
| P4-LONG | P4_ATR14_MAX | 130.0 |

---

## 引き継ぎリソース（次セッション必読）

- **WORKFLOW.md**（このファイル・現状の唯一の正本）
- **CLAUDE.md**（v3-bitget-api-sdk/CLAUDE.md・設計思想・絶対不変）
- **.claude/memory/lessons_active.md**（直近36件・L-103〜L-135／regime研究の経緯はL-126〜L-135）
- **.claude/memory/lessons_archive.md**（L-102以前のアーカイブ・必要時のみ）
- **.claude/memory/signal_ledger.md**（シグナル候補唯一の正本）
- **archive/workflow/WORKFLOW_20260427.md**（直前の Day 2/3 完了報告・マスタープラン9本詳細）
- **dashboard/index.html**（⑨タブで月別判定確認可）
