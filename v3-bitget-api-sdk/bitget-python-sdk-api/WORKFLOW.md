# WORKFLOW.md — cat-bitget 作業フロー

旧詳細版 → [WORKFLOW_ARCHIVE_20260422.md](WORKFLOW_ARCHIVE_20260422.md)

---

## 役割 + 行動原則

ClaudeはPM・PL・SE・プログラマの全役割を担う。

- 指示を待たず、自分で現状を把握して「次に何をすべきか」を先に提案する
- 仮説はデータで検証してから提示する（根拠なしの仮説は出さない）
- GOを待つのは「実装・コマンド実行・コミット」のみ
- 目標（$60/day）から常に逆算して行動する。目先の指標改善に満足しない

## シグナル管理

シグナル候補・レジーム×方向マッピング・検証実績は **`.claude/memory/signal_ledger.md`** が**唯一の正本**。
WORKFLOW.md にシグナル個別の状態を書かない（重複は不整合の元）。
セッション開始時・新規シグナル検証時・Priority 化時は signal_ledger.md を読み、更新する。

---

## Step 0: セッション開始プロトコル（省略禁止）

```
① 目標 $60/day − 現在 $5.97/day = 不足 $54/day
② 現フォーカスレジーム（DOWNTREND）の現状 vs 目標 $60/dt-day
③ [Step 0 D] 目標: $XX/dt-day / 現状: $YY/dt-day / 理論最大: $ZZ/dt-day → 到達可能性: YES/NO
   ※ この1行が出るまで提案・分析を開始しない
③.5 [Step 0 E] 直近タスク期待値合計: $AA/dt-day / 残差: $BB/dt-day
    カバー率 = AA/BB × 100%
    → カバー率 < 50% の場合: 「既存タスクのみでは目標到達不可能。
      新 Priority 設計を直近タスク1として再配置を検討」と明示する
④ 今セッションのタスクを優先順位付きで提示 → STOP
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
  → 専用パラメータ（P23_POSITION_SIZE_BTC等）を追加して個別設定する
  → エッジの高いPriorityに大きく配分することで$/total-dayを最大化できる
- 複数Priority並立の目的: リスク分散。詰まったら「新Priority追加」であり「サイズ増加」ではない
- 時間帯フィルターは個別Priority最適化では禁止。統合調整フェーズで実施

---

## 改善サイクル

**Step 1. 構造把握**
cat_v9_decider.py（Entry条件）・replay_csv.py（Exit優先順位）・cat_params_v9.json（現在値）を読む。
CSVにmfe_usd/mae_usd/exit_reason/hold_minが揃っているか確認する。

**Step 2. 結果分析**（グリッドサーチ前・省略禁止）

- **0. ポジション構造**: add_count × exit_reason マトリクスを作る。TIME_EXITが構造的コストか・フィルターで削れるかを1文で言語化してからA/Bへ進む
- **A. なぜ負けているか**: exit_reason別 件数/NET/avgMFE。MFEとMAEから損失の性質（即逆行 or 長期漂流）を特定する

  **TIME_EXIT分類（TIME_EXIT削減に着手する前に必須）**:
  TIME_EXITトレードのMFE分布を確認し、TYPE I / II に分類してから対策を決める。
  - TYPE I（MFEが小さい・概ね<$5）: Entry品質問題 → フィルター強化（ATR/ADX/RSI）
  - TYPE II（MFEが大きいが戻った・概ね>$15）: Exit設計問題 → TRAIL/PROFIT_LOCK改善
  - 分類なしのTIME_EXIT削減は失敗する（L-100: 早期EXIT→逆効果）
  採用条件: 「件数削減」ではなく「TIME_EXIT per-trade 平均損失改善 かつ 全体NET改善」で評価する
- **B. なぜ勝てないか**: TIME_EXIT中のMFE/TP比率・TP_FILLEDのMFE余裕を確認。「勝ちを逃している主因」を1文で言語化する
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

- add_count=1 のみの Priority は精度高い。add が複数ある Priority は誤差が出る点に注意。
- 改善が見込めない軸・範囲はグリッドから除外してから実行する。
→ 絞り込み結果を提示してGO待ち ← STOP

**Step 4. グリッドサーチ設計・実行**

- データ期間: 対象PriorityのターゲットREGIMEが密集した期間を選ぶ
  - P23(DOWNTREND): 180d（2025-10〜2026-04）/ P4(RANGE)・P24(UPTREND): 別途特定
- Phase 1（方向確認）: 各軸3点（低・中・高）。効かない軸はPhase 2から除外
- Phase 2（絞り込み）: 有効軸のみ・3〜5点・組み合わせ≤15
- OOS検証: グリッド後に365d Replay（regime_switch=ON）で $/regime-day > ベースラインを確認
- 採用基準: ① 365d $/regime-day > ベースライン ② 全体NET改善 ③ per-trade NET > 手数料
- TP変更時は手数料計算を先に実施（L-40）
→ grid_search.py更新後、実行コマンドをユーザーに提示 ← STOP

**Step 5. 結果評価** → 上位パターン比較表・推奨Before/After。未達ならStep 3へ ← STOP

**Step 6. 実装** → diff提示・GO待ち ← STOP

**Step 7. 最終Replay** → コマンド提示 ← STOP

**Step 8. 採用判定** → 「採用しますか？」。打ち切り前に未試行軸（Entry品質/EXIT設計/add戦略/シグナル条件）がないか確認する ← STOP

**Step 9. baseline更新** → $/regime-day表・$/total-day表を更新。目標との残差を再計算する

**Step 10. Gitコミット** → ユーザーの明示OK後のみ ← STOP

---

## 新規Priority設計フロー（P1/P21等・新規追加時）

1. 必要貢献額を逆算してシグナルの最大期待値が届くか確認する（届かなければ設計変更）
2. シグナルエッジをフィルターなし・タイトなTP/SLで先に検証する（勝率60%未満は却下）
3. Entry特性を言語化してからExitをゼロから設計する（既存流用禁止）
4. 実装 → Replay → 必要貢献額を満たすか判定

---

## Priority別ステータス（2026-04-24更新）

| Priority | downtrend/day | range/day | uptrend/day | 状態 |
|---------|--------------|-----------|-------------|------|
| P23-SHORT | **+$21.32/dt-day**（365d OOS・HIGH_ADX filter採用） | +$0.60 | -$3.70 | 稼働中（DT最適化完了） |
| P21-SHORT | **+$11.41/dt-day**（365d OOS・2026-04-25 TRAIL_RATIO=0.9/MFE_GATE_PCT=0.04 採用） | — | — | 稼働中（DT最適化進行中） |
| P2-LONG | **+$4.75/dt-day**（365d OOS・2026-04-25 TP_PCT=0.006/MFE_STALE_GATE=3.0 採用） | — | — | 稼働中（DT最適化進行中） |
| P3-LONG | — | — | — | DT停止確定（2026-04-24 整合修正・`ENABLE_P3_LONG: False`） |
| P4-LONG | — | +$0.69/day | — | 未着手（RANGE割当） |
| P24-SHORT | — | — | +$0.88/day | 未着手（UPTREND割当） |
| P1-LONG | — | — | -$0.36/day | 未着手（UPTREND割当・要改善） |
| P22-SHORT | — | — | — | DT停止中（コード`ENABLE_P22_SHORT: False`・全レジーム未着手） |
| P25-SHORT | — | — | — | REJECTED（L-118・N3 ADXスパイク・P23干渉で DT-$14.38悪化） |

> 状態の定義:
> - 稼働中: 現在 replay で動作・最適化完了または進行中
> - 休止: 特定レジームで停止中（他レジームは未評価・将来再開候補あり）
> - 未着手: 改善試行をまだしていない

---

## 現在のベースライン（2026-04-24更新）

### PM基準（$/total-day・Step 0専用）

| レジーム | /total-day | 有効Priority |
|---------|-----------|-------------|
| DOWNTREND | +$14.68（365d実測・2026-04-25 マスタープラン#2完了） | P2/P21/P23 |
| RANGE | -$0.41 | P4 |
| UPTREND | +$0.52 | P1/P24 |
| MIXED | +$0.39 | P4 |
| **合計** | **+$15.18** | ※365d regime_switch=ON |

※90d（Jan-Apr 2026）は好況期バイアスあり。365dを正本とする。

### Priority最適化基準（$/regime-day・Step 2〜9専用）

| Priority | 対象レジーム | $/regime-day | データ |
|---------|------------|-------------|-------|
| P23-SHORT | DOWNTREND | **+$21.32（365d OOS・HIGH_ADX filter採用）** | 365d=143dt-day |
| P21-SHORT | DOWNTREND | **+$11.41（365d OOS・2026-04-25 TRAIL系最適化）** | 365d=143dt-day |
| P2-LONG | DOWNTREND | **+$4.75（365d OOS・2026-04-25 TP/MFE系最適化）** | 365d=143dt-day |
| P3-LONG | DOWNTREND | — | DT停止確定（0件） |
| **DT合計** | DOWNTREND | **$37.48/dt-day（2026-04-25 マスタープラン#2完了）** | 目標$60まで-$22.52 |
| P4-LONG | RANGE | 未最適化 | — |
| P24-SHORT | UPTREND | 未最適化 | — |

### _REGIME_PRIORITY_SETS（replay_csv.py・2026-04-24修正）

| Priority | DOWNTREND | RANGE | UPTREND | MIXED |
|---------|-----------|-------|---------|-------|
| P1-LONG | ❌ | ❌ | ✅ | ❌ |
| P2-LONG | ✅ | ❌ | ❌ | ❌ |
| P3-LONG | ❌（2026-04-24停止確定） | ❌ | ❌ | ❌ |
| P4-LONG | ❌ | ✅ | ❌ | ✅ |
| P21-SHORT | ✅ | ❌ | ❌ | ❌ |
| P22-SHORT | ❌ | ❌ | ❌ | ❌ |
| P23-SHORT | ✅ | ❌ | ❌ | ❌ |
| P24-SHORT | ❌ | ❌ | ✅ | ❌ |
| P25-SHORT | ❌（REJECTED・L-118） | ❌ | ❌ | ❌ |

---

## 🔴 セッション切替メモ（2026-04-26 Day 2 終了時点・最優先で読む）

### Day 2 完了報告（2026-04-26）

**実施内容**:
1. 特徴量計算スクリプト実装: [scripts/phase1_features.py](scripts/phase1_features.py)
2. 5年分日足から特徴量算出: [results/phase1_features_daily.csv](results/phase1_features_daily.csv)（1778行×8特徴・warmup49日除外）
3. ダッシュボード組み込み: [dashboard/data/phase1_features.json](dashboard/data/phase1_features.json) + ⑦HMM特徴量タブ追加
4. JSON生成スクリプト: [scripts/build_phase1_features_json.py](scripts/build_phase1_features_json.py)

**特徴量設計（情報量効率版・8本）**:
当初20本まで拡張予定 → 初版8本で相関確認したところ |r|≥0.7 が6ペア発生（方向性カテゴリの冗長）→ 1ペアまで削減 → streak_max_30d 差し替えで完全消滅。
- A方向性: `ma50_dev`（MA50乖離率%）
- B強度  : `adx_14`
- C構造  : `streak_max_30d`（30日内最大連続陽線/陰線・符号付き）
- Dボラ  : `atr_14_pct` / `bb_width_20` / `bb_pct_b`
- Eその他: `vol_chg_7d` / `ret_skew_30d`（30日リターン歪度）

**確認結果**:
- |r|≥0.7 ペア: 0個（冗長削除成功）
- 中度相関（許容）: ma50_dev⇔bb_pct_b +0.67 / atr_14_pct⇔bb_width_20 +0.62 など4ペア
- 全特徴の分布が妥当範囲内（NaN/∞なし）

**今日の判断**:
- 当初予定の「15-20本まで拡張」を **8本で確定** に変更
- 理由: 冗長を抱えたまま膨らませると HMMが方向性カテゴリに支配される。情報量効率を優先
- 精度低下時は5m足の日中分布特徴を追加して粒度上げる方針（次セッション以降）

**懸念**:
- ma50_devが他4つの特徴と中度相関（最大+0.67）→ HMM学習で支配的になる可能性。Day 3で状態解釈時に要観察
- 段階1（ガウシアンHMM）が30-40%精度天井にぶつかる可能性は残る（L-129相当）

**明日（Day 3）予定**: ガウシアンHMM学習・状態解釈・リターン分布評価

---

### 本セッション総括（2026-04-25〜26）

**重要決定**: regime 判定の根本再設計を開始（HMM 教師なし学習プロジェクト・1-2週間規模）。
**Replay組み込み・Priority最適化は regime 判定確定まで全停止** とユーザー合意。

#### 大きな発見・経緯
1. **look-ahead バグ確認 (L-128)**:
   - replay_csv.py の `_build_regime_map` 系3関数すべてに最大23時間55分の look-ahead
   - 実害: total NET $5593→$4506 (-$1087/-19.4%)、P23 $21.32→$16.34 (-23.4%)
   - 既採用パラメータ（P21/P2/P23）は look-ahead プレミアム前提で最適化されたもの
   - SAFE版 `--regime-safe` 実装済み（コード修正のみ・3関数並走）

2. **手動ルール25個 + 機械学習（RF/GB）試行 → 全て30-40%天井 (L-129)**:
   - ground truth（まこさん肉眼判定 53週 → さらに365日に粒度上げ）に対して評価
   - すべて月-水で30%台（ランダム以下）・全曜日80%達成ゼロ
   - 機械学習: 学習98-100% / 検証31-32% = 重度の過学習・データ不足

3. **「regime廃止・Priority個別判定」提案ミス (L-127)**:
   - 経緯（Phase 1 全相場対応型→regime切替転換）を忘却した的外れ提案
   - ユーザー指摘で撤回・以後は経緯確認必須

4. **判定基準の閾値根拠なし誤り (L-130)**:
   - 「±0.20%」を根拠なく提示 → BTC実データでは無意味（0.06σ相当）
   - データ駆動で閾値を再設計 → **平均±0.3σ で合意**

5. **HMM 教師なし学習プロジェクト開始**:
   - WEB Claude のアドバイス採用: 教師なし学習・リターン分布評価・段階的（HMM→GMM-HMM→UMAP+HDBSCAN）
   - 5年分BTCUSDT 5m足取得完了（2020-2024・1826日・525,714本）
   - hmmlearn インストール完了
   - Phase 0 完了: 日次リターン分布算出 → 判定基準合意

### 🔴 確定事項（HMM 研究プロジェクト前提）

#### 判定基準（候補B: 平均±0.3σ）
- **UPTREND判定時 平均日次リターン > +1.22%** (= mean+0.3σ)
- **DOWNTREND判定時 平均日次リターン < -0.82%** (= mean-0.3σ)
- **RANGE判定時 |平均日次リターン| < 0.34%** (= 0.1σ)
- **状態継続中央値 ≥ 3日 かつ ≤ 30日**
- 統計的有意性: t検定で p<0.05 を補助確認

#### BTC 5年分 統計（基準算出元）
- 期間: 2020-01-01 〜 2024-12-31 / 1826日
- 平均日次リターン: +0.200%
- 標準偏差（σ）: 3.405%
- 中央値: +0.076%
- パーセンタイル: 25%=-1.30% / 50%=+0.08% / 75%=+1.67% / 95%=+5.45%

#### 進捗報告ルール
- **1日1回・各Day終了時**にチャット報告 + WORKFLOW.md追記
- ダッシュボードで視覚確認可能な状態を Day 単位で更新
- フォーマット: 「今日やったこと / 数値 / 明日予定 / 懸念 / 軌道修正必要性」

#### 段階的進行（過剰最適化防止）
- 段階1（ガウシアンHMM）合格 → 段階2/3に進まず即 Replay 移行
- 各段階 5-7回の調整で不合格なら次段階（最大15-21回でストップ）
- 段階1 完了予定: Day 3-4（特徴量実装+学習+評価まで）

### 🔴 次セッション最優先タスク（HMM Day 3: ガウシアンHMM学習）

**Day 1完了** (2026-04-26): データ取得・ライブラリ準備・Phase 0 統計算出 ✅
**Day 2完了** (2026-04-26): 特徴量設計・計算・ダッシュボード組み込み ✅

**Day 3 タスク（次セッション）**:
1. ガウシアンHMM学習スクリプト実装（hmmlearn）
   - 入力: [results/phase1_features_daily.csv](results/phase1_features_daily.csv)（1778行×8特徴）
   - 状態数: まず 3（uptrend/downtrend/range 想定）→ 結果次第で 4-5 試行
   - StandardScaler で正規化してから fit
   - 出力: 各日の予測状態 + 状態遷移確率 + 各状態の平均特徴量
2. 状態解釈
   - 各状態の平均日次リターン分布を算出（Phase 0 基準と照合）
   - 候補B（平均±0.3σ）合格判定:
     - UPTREND判定状態 平均日次リターン > +1.22%
     - DOWNTREND判定状態 平均日次リターン < -0.82%
     - RANGE判定状態 |平均日次リターン| < 0.34%
   - 状態継続中央値 ≥ 3日 かつ ≤ 30日
3. ダッシュボード「⑦ HMM特徴量」を拡張または「⑧ HMM状態検証」タブ追加
4. 段階1合格判定 → 合格なら即 Replay 移行 / 不合格なら 5-7 回調整 → 上限到達で段階2へ

**判定基準 候補B 数値（再掲）**:
- UPTREND: 平均日次リターン > +1.2213%
- DOWNTREND: 平均日次リターン < -0.8216%
- RANGE: |平均日次リターン| < 0.3405%
- 統計有意性: t検定 p<0.05 補助確認

### 🔴 既採用パラメータの取り扱い（停止中・解凍は regime確定後）
- P21: TRAIL_RATIO=0.9 / MFE_GATE_PCT=0.04 / TIME_EXIT_MIN=180 / ATR14_MIN=150 → $11.41/dt-day（look-ahead プレミアム含む）
- P2: TP_PCT=0.006 / MFE_STALE_GATE=3.0 / ATR14_MIN=100 / ATR14_MAX=300 → $4.75/dt-day（同上）
- P23: TP_PCT=0.012 / HIGH_ADX_THRESH=40 / HIGH_ADX_ATR_MIN=200 / TIME_EXIT_MIN=480 → $21.32/dt-day（look-ahead プレミアム-$4.98含む・SAFE値 $16.34）
- P4: ATR14_MIN=200 / TP_PCT=0.005 → -$0.67/range-day
- replay_csv.py: `--regime-safe` 実装済み・本番経路は未対応
- **regime 判定確定後にゼロから再評価**（lookahead-safe + 新regime label）

### 🔴 試行禁止リスト
- ❌ 1週ラグ運用（regime切替の意味なくなる）
- ❌ 「regime廃止・Priority個別判定」提案（Phase 1 失敗確定済・L-127）
- ❌ 教師あり学習で ground truth に完全フィット狙い（L-129 で30-40%天井確認済）
- ❌ ground truth との完全一致を目標にする（リターン分布評価が正本）
- ❌ 段階1合格後に段階2/3に進む（過剰最適化禁止）
- ❌ 根拠なき閾値提示（L-130・対象データ統計を必ず先に確認）
- ❌ Replay組み込み・Priority最適化への着手（regime確定まで全停止）

### 🔴 引き継ぎリソース（次セッション必読）
- **WORKFLOW.md**（このファイル・現状の唯一の正本）
- **.claude/memory/lessons.md**（**L-126〜L-131 を必読** — regime研究の経緯）
- **CLAUDE.md**（v3-bitget-api-sdk/CLAUDE.md・設計思想・絶対不変）
- **scripts/download_binance_5y.py**（5年分DLスクリプト）
- **scripts/phase0_return_distribution.py**（リターン分布算出）
- **scripts/phase1_features.py**（Day 2: 8特徴量計算・look-ahead安全）
- **scripts/build_phase1_features_json.py**（Day 2: ダッシュボード用JSON生成）
- **data/BTCUSDT-5m-2020-01-01_2024-12-31_5y.csv**（5年分5m足・1826日）
- **results/phase0_return_distribution.json**（基準算出結果）
- **results/phase1_features_daily.csv**（Day 2: 1778行×8特徴）
- **dashboard/data/phase1_features.json**（Day 2: ⑦タブ用データ）
- **dashboard/index.html / assets/app.js**（⑦HMM特徴量タブ実装済み）
- **.venv/**（hmmlearn / scikit-learn / ta / pandas / numpy インストール済）

### 🔴 ライブラリインストール状況
- ✅ scikit-learn 1.8.0 / pandas 2.3.3 / numpy 2.4.0 / ta（既存ML用）
- ✅ hmmlearn 0.3.3（段階1ガウシアンHMM用）
- ⚠️ hdbscan / umap-learn: llvmlite ビルド失敗 → 段階3進む際に対応
- ⚠️ pomegranate: 未インストール → 段階2進む際に対応

---

## マスタープラン（2026-04-25・$60/day 必達コミット）

CLAUDE.md「目標 $60/day に対し、あらゆる手段を講じてコミット」原則に従い、
DT 単独で届かない積算上限（PMレビュー $37〜$42/dt-day）を補うため、
**全レジ並行 9本マスタープラン** を順次消化する。

### 重大事実（2026-04-25 仮想シミュ確定）
- **DT 期間中の idle 時間 = 90.95%**（誰もポジ持ってない時間が大半）
- → 「Priority 別固定枠」の期待効果は +$1.3〜+$2.4/dt-day と薄い（Step 3 判定基準で ④ 採用）
- → 構造的問題は **「枠の取り合い」ではなく「発火頻度の絶対不足」**
- → 解決策は サイズ最適化ではなく シグナル/Exit 多軸並行改善

### マスタープラン 9本（順次消化・順序固定）

| # | 手段 | 期待効果 $/dt-day | リスク |
|---|------|---|------|
| 1 | ✅ **完了** P21 TRAIL_RATIO=0.9 / MFE_GATE_PCT=0.04 採用（+$3.90/dt-day 達成・L-118干渉ゼロ）| +$3.90 実測 | — |
| 2 | ✅ **完了** P2 TP_PCT=0.006 / MFE_STALE_GATE=3.0 採用（+$2.43/dt-day 達成・L-118干渉ゼロ）| +$2.43 実測 | — |
| 3 | P23 段階的利確（MFE=$50で半分決済・非ratchet）| +$1〜+$2 | L-114 変形リスク（要慎重） |
| 4 | P23 ATR ベース動的TP（下限0.012・上限ATR連動）| +$1〜+$3 | TP狭めると L-114 再発・**広げる方向のみ** |
| 5 | レジーム変化Exit（MA70再クロスで即Exit）| +$0.5〜+$2 | 未計測 |
| 6 | 共通エンジン拡張 → N6 SHORT を P26 として育成 | +$1〜+$3 | L-118 干渉再発リスク |
| 7 | DT サブレジーム分類（深DT/浅DT で別 Priority）| +$2〜+$5 | 設計大改修 |
| 8 | 新規シグナル N7/N10/N14/N16/N17 候補追加（10→20候補）| +$0〜+$5 | L-117 発火少シグナル罠 |
| 9 | RANGE/UPTREND 並行着手（P4/P1/P24）| +$15〜+$25/total-day | 別レジーム最適化 |

**累計期待効果（DT $/dt-day）**: +$10〜+$25
**累計期待効果（total $/day）**: + $15〜+$25 (RANGE/UP 寄与)
**理論到達点**: $31.15 + DT追加 $10〜$25 + RANGE/UP $15〜$25 = **$56〜$81/total-day**（$60目標達成圏内）

### 既決事項（2026-04-25）
- ❌ Priority 別固定枠導入: idle 90% で効果薄 → ④（現状取り合い設計維持）
- ❌ ポジションサイズ拡大（個別 Priority のみ）: CLAUDE.md「サイズ増加でスケール禁止」抵触

---

## 次のアクション（2026-04-24 継続セッション終了時点）

```
【現在フォーカス: DOWNTREND / 合計$60/dt-day目標】
現状: $31.15/dt-day / 目標$60 / 残差-$28.85
2026-04-24 前セッション(Exit改善): +$4.08/dt-day（$26.35→$30.43）
2026-04-24 本セッション(新規Priority探索): +$0.72/dt-day（$30.43→$31.15）
  - P3-LONG DT停止（WORKFLOW認識と実装整合修正）→ +$0.72
  - N1/N3 新規シグナル検証: 両方却下・P25-SHORT実装→L-118でロールバック

【本セッション 2026-04-24 採用済み】
✅ P3-LONG DT停止（ENABLE_P3_LONG: False）
   - WORKFLOW表「休止」と実装「True」の矛盾を修正
   - 365d Replay: P3 0件・P2-LONG +$0.21/dt-day（LONGスロット空き効果）

【前セッション 2026-04-24 採用済み】
✅ P21_TIME_EXIT_MIN=180（実効90min）→ P21 $5.95→$7.36/dt-day
✅ P23 HIGH_ADX フィルター → P23 $18.74→$21.32/dt-day

【本セッション REJECTED 提案（2026-04-24 新規Priority探索）】
❌ N1 シグナル（EMA20リジェクト SHORT・戻り売り）
  - 180d grid exit: $25.44/dt-day / 365d OOS: $2.60/dt-day（L-115 過学習）
  - 20件/dt-day で per-trade 構造的に薄い（L-116）
  - per-trade指標フィルタでも改善せず（L-117）

❌ N3 シグナル → P25-SHORT 実装（ADXスパイク順張り SHORT）
  - 365d grid/exit: $10.90/dt-day 予測
  - 365d Replay 実測: P25 +$2.90 / DT合計 $30.43→$16.05（-$14.38悪化）
  - P23-SHORT が $21.32→$3.58 に失墜（L-118 / L-46 干渉）
  - 即ロールバック（downtrend の ENABLE_P25_SHORT: False）
  - P25 コード（cat_v9_decider + cat_params）は将来再設計用に残存

【前セッション REJECTED 提案（2026-04-24 継続）】
❌ P23 MAX_ADDS 削減（5→3or4）
  - 仮想シミュ: add=4,5 は NET最大貢献源（+$1,860 / 全体61%）
  - 削減は $-1.19〜-$4.14/dt-day。WORKFLOW直近タスク1は却下

❌ P23 A1_STALL 事前エントリーフィルタ
  - A1_STALL 51件-$433 の分離可能性を探索
  - 最良 bb_mid_slope>-20 で +$1.07/dt-day（A1_TP 4件巻き添え）
  - 改善幅が小さくサンプル過少（統計有意性弱）

❌ P23 MFE_STALE_CUT チューニング（B2案）
  - 現行 GATE=$4/HOLD=30 は A1_STALL 51件を完璧に捕捉済み
  - HOLD短縮（20min）の理論上限 +$0.5〜+$1.7/dt-day
  - 優先度低く実行せず

❌ P23 TRAIL_EXIT 追加（L-113 記録）
  - 仮想シミュ予測 +$14.62/dt-day → 実測 -$20.14/dt-day（P23 $21.32→$1.18）
  - TP_FILLED 47件→1件・STOCH_REVERSE_EXIT 41件消滅・avgHold 100→9.5分
  - 原因: デフォルト GATE_PCT=0.05（≈MFE$1で即活性化）が P23 長ホールド型に壊滅的不整合
  - ロールバック済（replay_csv.py の priority list を (1,21) に復元）

❌ P23 MFE_DRAWDOWN_CUT（L-114 記録・PMレビュー後の第2ラウンド）
  - パラメータ: MIN_USD=30 / RATIO=0.3（TP奪取リスクを設計で回避したつもり）
  - 実測 -$10.29/dt-day（P23 $21.32→$11.03）
  - TP_FILLED 47件→40件（-7件）・STOCH_REVERSE_EXIT 41件→26件（-15件）
  - MFE_DRAWDOWN_CUT 33件は NET -$219（avg -$6.6・期待値負）
  - ロールバック済（cat_params_v9.json から 2行削除）

【ratchet型 Exit 全面禁止（L-114 確定）】
  P23 に PROFIT_LOCK / TRAIL_EXIT / MFE_DRAWDOWN_CUT を追加する提案は
  原則禁止。P23 は TP到達までに volatile-path をたどる性質で、ratchet型は
  TP経路の中間 pullback を誤認して発火しTP奪取する。3連敗で構造確定。

【保留資産（次セッション以降）】
- P25-SHORT コード: decider + params 残存・無効化状態
  avgHold短縮 or 強Entry絞り込みで再設計の可能性
- A1_STALL の per-trade 損失 -$8.48 自体は MFE_STALE_HOLD_MIN 短縮で
  $0.5〜$1.7/dt-day 削れる可能性（非ratchet型・安全）

【直近タスク（優先順位順・非ratchet型のみ）】
1. 【新規】共通エンジン scripts/analyze_signals.py 作成
   - L-118織り込み: 占有時間試算 + 既存Priority発火重複率を事前評価
   - 複数シグナル候補を1スクリプトで効率検証（signal_ledger.md で追跡）
   - 実装前 Replay 干渉テストを必須化

2. 【新規】N6〜N18 候補シグナル検証（最低10候補）
   - feedback_ten_trials_minimum: 10候補×365d検証してから撤退判断
   - 優先順: N6 (ADX50超+DI-) / N2 (BB Trap) / N12 (出来高急増+陰線) / N8 (Donchian)
   - 制約: 発火 5-10件/dt-day・avgHold 60-120min（L-116）
   - 365d 直接検証（180d は使わない・L-115）
   - 順張り歓迎（feedback_trend_follow_welcomed）

3. STOCH_REVERSE_EXIT MFE_GATE 単軸スイープ（既存最適化）
   - 現行 P23_STOCH_EXIT_MFE_GATE=20 の周辺 [10, 15, 25, 30]
   - 期待 +$0.5〜+$2/dt-day

4. P23_STOCH_K_MAX ゲート（Entry強化）
   - decider L474 に実装済みだが params=999.0 で実質無効
   - CSV で TP vs TIME_EXIT の stoch_k_at_entry 分布を確認

5. P21 TP_PCT / BB_RATIO 最適化（別Priority・未試行軸）
   - 期待 +$1〜$3/dt-day

6. P22-SHORT DT 改善（新規設計級の工数）
   - 現在 DT 無効・DT 有効化 replay → フィルタ強化の流れ

7. P4-LONG RANGE 改善（DT目標達成後）

【確認済み・変更禁止】
- P23: HIGH_ADX_THRESH=40 / HIGH_ADX_ATR_MIN=200 / STOCH_REVERSE_EXIT(MFE=20/HOLD=150/UNREAL=0)
  → $21.32/dt-day（365d OOS）確定
- P21: ATR14_MIN=150 / TRAIL_RATIO=0.9 / MFE_GATE_PCT=0.04 / TIME_EXIT_MIN=180 → **$11.41/dt-day（365d OOS・2026-04-25 マスタープラン#1完了）**
- P2: TP_PCT=0.006 / MFE_STALE_GATE=3.0 / ATR14_MIN=100 / ATR14_MAX=300 → **+$4.75/dt-day（365d OOS・2026-04-25 マスタープラン#2完了）**
- **_REGIME_PRIORITY_SETS DT: ENABLE_P3_LONG=False / ENABLE_P25_SHORT=False 確定（2026-04-24）**
- replay_csv.py: P23 STOCH_REVERSE_EXIT（3f）実装済み
- replay_csv.py: P21 MFE_STALE_CUT（3e）実装済み
- replay_csv.py: TRAIL_EXIT 対象 priority は (1, 21) 維持
- P25-SHORT コード: decider + params 残存・無効化（ENABLE=False）

【PMレビュー知見（2026-04-23 + 2026-04-24）】
- スロット占有制約: 1ポジション保有中は他Priority入れない（シリアル実行）
  → 新規Priority追加前に占有時間試算必須（L-46 / L-118）
- $60/total-dayは現Priority構造のみでは困難・新Priority発掘が必要
  → 現フォーカスは DOWNTREND 維持（feedback_downtrend_focus）
  → 新Priority探索は順張り系歓迎（feedback_trend_follow_welcomed）
  → 最低10候補×365d検証が原則（feedback_ten_trials_minimum）

【本セッションの教訓】
- L-111: PROFIT_LOCK/TRAIL系は TP_FILLED 奪取リスクを必ず事前確認
- L-112: final_mfe は途中時点 MFE の推定に使えない（MFE=単調増加型）
- L-113: TRAIL_EXIT の trail_net 仮想シミュは ratchet型の動的挙動を捉えず大外しする
- L-114: P23 は ratchet型 Exit 全般と構造的不整合（volatile-path TP経路）
- L-115: 180d Exit最適化は過学習リスク極大（→365d正本化）
- L-116: 発火件数少=質高=Exit柔軟性（最適域 5-10件/dt-day・avgHold 60-120min）
- L-117: 発火少シグナルのper-tradeフィルタは絶対NET悪化（件数削減コスト）
- L-118: 単独シミュは複数Priority共存で $/dt-day を過大評価（L-46 実証確認）

【grid_search.py 現在の設定】
- TARGET: 未設定（新規シグナル検証フェーズ中）
```

---

## Replayコマンド

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

## 確定パラメータ（2026-04-22時点）

| Priority | パラメータ | 値 |
|---------|-----------|-----|
| P2-LONG | **P2_TP_PCT** | **0.006（2026-04-25採用・$2.32→$4.75）** |
| P2-LONG | P2_ATR14_MIN / ATR14_MAX | **100.0（採用確定）** / **300.0（採用確定）** |
| P2-LONG | **P2_MFE_STALE_GATE_USD** / HOLD_MIN | **3.0（2026-04-25採用）** / 90.0 |
| P23-SHORT | P23_TP_PCT | 0.012 |
| P23-SHORT | P23_TIME_EXIT_MIN | 480（実効240min via DOWN_FACTOR=0.5） |
| P23-SHORT | P23_ADX_MIN/MAX | 30.0 / 50.0 |
| P23-SHORT | P23_ATR14_MIN | 150.0 |
| P23-SHORT | **P23_HIGH_ADX_THRESH / P23_HIGH_ADX_ATR_MIN** | **40.0 / 200.0（2026-04-24採用）** |
| P23-SHORT | P23_MFE_STALE_GATE_USD / HOLD_MIN | 4.0 / 30.0 |
| P23-SHORT | P23_SHORT_PROFIT_LOCK_ENABLE | 0 |
| P23-SHORT | P23_STOCH_REVERSE_EXIT_ENABLE | true |
| P23-SHORT | P23_STOCH_EXIT_MFE_GATE | 20.0 |
| P23-SHORT | P23_STOCH_EXIT_MIN_HOLD | 150.0 |
| P23-SHORT | P23_STOCH_EXIT_UNREAL_MIN | 0.0 |
| P21-SHORT | **P21_TRAIL_RATIO / P21_MFE_GATE_PCT** | **0.9 / 0.04（2026-04-25採用・$7.51→$11.41）** |
| P21-SHORT | P21_TIME_EXIT_MIN | 180（2026-04-24採用・実効90min） |
| P21-SHORT | P21_SL_PCT | 0.02 |
| P22-SHORT | P22_TIME_EXIT_DOWN_FACTOR | 0.4 |
| P4-LONG | P4_TP_PCT | 0.003 |
| P4-LONG | P4_ATR14_MAX | 130.0 |
