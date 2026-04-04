# WORKFLOW.md — V9 改善フロー（2026-04-04 更新）

## セッション開始時の確認事項（最優先）

| 項目 | 状態 |
|------|------|
| 現在のフェーズ | **Phase 5（常時稼働）— BOT 停止中** |
| 本番ポジション | なし（BOT 停止中） |
| 次のタスク | **環境分類 × 損失特化分析（Step 2）→ 時間帯フィルター等の改善案検討** |
| ALLOW_LIVE_ORDERS | True（Claudeは変更しない） |
| open_position_long.json | なし |
| open_position_short.json | なし |
| paper_trading | false |
| Replay 本番投入基準 | **NET $100/day 以上**（intra-bar fill 過大評価バッファ込み） |
| 本番 NET 目標 | **$60/day** |

### 現在の cat_params_v9.json（2026-04-04 セッション後）

| パラメータ | 値 |
|-----------|-----|
| **LONG_TP_PCT / SHORT_TP_PCT** | **0.005**（旧 0.0032） |
| LONG_SL_PCT / SHORT_SL_PCT | 0.05 |
| LONG_TIME_EXIT_MIN | 150 |
| SHORT_TIME_EXIT_MIN | 480 |
| P2_TIME_EXIT_MIN | 480 |
| **LONG_TIME_EXIT_DOWN_FACTOR** | **0.50**（旧 0.75） |
| **SHORT_TIME_EXIT_DOWN_FACTOR** | **0.50**（旧 0.75） |
| LONG_MAX_ADDS / SHORT_MAX_ADDS | 5 |
| **MAX_ADDS_BY_PRIORITY** | **`{"2": 4, "4": 1, "23": 1, "24": 1}`**（旧 `{"2": 4}`） |
| TP_ADX_BOOST_ENABLE | 1 |
| TP_PCT_CLAMP_ENABLE | 1 |
| FEAT_SHORT_RSI_REVERSE_EXIT | true |
| LONG_PROFIT_LOCK_ENABLE | 1 |
| P23_SHORT_PROFIT_LOCK_ENABLE | 1 |
| LONG_POSITION_SIZE_BTC / SHORT_POSITION_SIZE_BTC | 0.024 |

### 現在の replay_csv.py の設定

| 項目 | 値 |
|------|-----|
| PENDING_TTL_BARS | 2（= 翌バー1本のみで fill 判定） |
| fill 判定 | intra-bar（LONG=low, SHORT=high） |
| limit_price | close ± 0.01% |
| 手数料 | entry=maker / exit TP=maker / exit SL=taker |
| **サマリー出力** | **Priority×Exit クロス・add_count別・entry指標別に拡張済み** |

### 直近 Replay 結果（2026-04-04 セッション4・最新）

| 項目 | 値 |
|------|-----|
| 総トレード数 | 552件 |
| NET | **+$76 / 90日（+$0.8/day）** |
| TP率 | 81%（446件） |
| TIME_EXIT | 100件 |
| MIDTERM_CUT | 0件 |
| 平均保持時間 | — |
| CSV | `results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |

### Priority別 NET（最新）

| Priority | 件数 | NET | TP率 | TIME_EXIT | 主な問題 |
|---------|------|-----|------|-----------|---------|
| P2-LONG | 177 | **+$138** | 92% | 14件/-$381 | — |
| P22-SHORT | 8 | -$9 | 62% | 2件/-$44 | 件数少・影響小 |
| P23-SHORT | 182 | -$114 | 86% | 23件/-$387 | TIME_EXIT が残存 |
| P24-SHORT | 22 | -$30 | 86% | 3件/-$78 | 件数少・影響小 |
| P4-LONG | 163 | **+$91** | 64% | 58件/-$527 | TP率低・TIME_EXIT 多い |

### 構造的天井の発見（重要）

**TP_PCT=0.005 時の TP 利益合計: +$2,262 / 90日 = +$25.1/day（639件時点）**

損失ゼロにしても最大 +$25.1/day → **目標 $100/day はパラメータ調整のみでは到達不可**。

→ スケールアップ（マルチシンボル等）が必要。まず per-trade エッジをプラスにしてからスケール。

### 重要な分析知見（2026-04-04）

- **TIME_EXIT の 62% は「エントリー直後から逆行」** → TP_PCT 調整では救えない。エントリー品質の問題。
- **atr_14 が最も分離力の強い指標**: TP_FILLED の atr 平均 232 vs TE_bad（MFE<0.2%）の atr 平均 166
- **低ボラ（atr<150）環境はレンジ回帰が起きず TIME_EXIT になりやすい**（P4/P2 共通）
- **Entry フィルターは P4→P2 の流入（L-19）に注意**。片方だけ追加すると相殺・逆転する。

### このセッションで実施・却下した変更

**採用済み（累計 +$1,107 改善）:**
| 変更 | 効果 |
|------|------|
| MAX_ADDS_BY_PRIORITY P4: 5→2 | +$215（MIDTERM_CUT 削減） |
| DOWN_FACTOR LONG/SHORT: 0.75→0.50 | +$170（MIDTERM_CUT 完全消滅） |
| MAX_ADDS_BY_PRIORITY P4: 2→1 | +$71（P4 add=2 損失削減） |
| MAX_ADDS_BY_PRIORITY P23/P24: 5→1 | +$192（P24 壊滅的 add=4,5 消滅） |
| LONG/SHORT_TP_PCT: 0.0032→0.005 | +$326（NET -$452→-$127、P2/P4 黒字転換） |
| P4_ATR14_MIN: 150 / P2_ATR14_MIN: 150 | +$133（NET -$127→+$7、P2 TP率 85%→92%） |
| **P23_ATR14_MIN: 150 / P24_ATR14_MIN: 150** | **+$69（NET +$7→+$76、P23/P24 TP率 83/81%→86%）** |

**却下済み:**
| 変更 | 理由 |
|------|------|
| LONG_MIDTERM_PNL_USD: -30→-20 | MIDTERM_CUT が 17→23件に増加（逆効果） |
| P2/SHORT_TIME_EXIT_MIN: 480→240 | TP 14件減少・TIME_EXIT 増加（+$146 のみ） |
| P4 ADX Entry フィルター（>=24等） | TP維持率 57%（基準 80%未満） |
| P23_SLOPE<=-25 Entry フィルター | 外科的スコア 0.15（不十分） |
| P23 transit_A × ret_5>0 フィルター | signal/fill バーズレで CSV+$143 → Replay +$2（L-26） |

### 次セッションの選択肢

※ 本番投入基準: **Replay NET $100/day 以上**（現在 +$0.1/day のため本番投入不可）

| 方針 | 内容 | 期待値 |
|------|------|--------|
| **A. P4 TP率改善** | P4 TP率 64% が低い。TIME_EXIT 58件/-$527 が最大残存損失源 | atr>=150 絞り込み後の別指標分析 |
| **B. P2 TIME_EXIT 削減** | 14件/-$381 が残存。add_count>=2 が深い損失 | add制限 or 別指標フィルター |
| **C. スケールアップ** | ETH/SOL 追加でトレード数×3〜5倍 | エッジが正になってから |

---

## 改善フロー（Phase 5）

**このフローを必ず順番通りに実行する。前のステップが完了するまで次に進まない。**

```
Step 1. 現状把握
  — Replay 実走・結果CSV確認
  — exit reason別・Priority別・LONG/SHORT別に集計

Step 2. 環境分類 × 深掘り分析
  【環境定義（ADX × atr_14 で分類）】
  ① レンジ   : ADX < 25 かつ atr_14 が低位（相場が静か）
  ② トレンド : ADX ≥ 25 かつ atr_14 が高位（相場が動いている）
  ③ 遷移     : その他（①②の境界・不安定期）

  全体集計の前に必ず環境別に分解する。
  「全体改善」は環境ミックスで騙される → 環境別で見て初めて本質が見える。

  【分析の切り口チェックリスト（必ず全て確認する）】
  □ 環境 × Priority × net_usd（どの環境で本当に儲かっているか）
  □ LONG / SHORT 別
  □ Priority 別（P2/P4/P22/P23/P24）
  □ add_count 別
  □ 時間帯 × net_usd（entry_hour）
  □ 勢い × ボラ × exit_reason（ret_5 × atr_14）
  □ パラメータはLONG/SHORTで別々に最適化できないか

  【損失特化分析（必須）】
  平均は本質を埋める。下位20%損失トレードだけ抽出して分析する。
  — 下位20%損失トレード: どの環境・Priority・時間帯に集中しているか？
  — 上位20%利益トレード: どの環境・Priority・時間帯か？（稼ぎ場の特定）
  — 「全体で-$X」ではなく「環境②・P4・朝8時に損失が集中」という形で特定する

  集計だけからの仮説立案禁止。個別トレードを確認してから仮説を立てる。

Step 2.5. 設計思想チェック ← STOP（提案前に必ず通過すること）
  「具体的な手段（TP幅・add回数等）は目的達成のために最適化する」が設計思想。
  手段そのものを禁じるのではなく、目的に近づくかを確認する。

  □ lessons.md を確認し、提案手法が過去の失敗パターンに該当しないか確認する
    （特に L-16/L-19/L-20/L-26 は繰り返しやすい）
  □ NET は改善するか（環境別で確認・全体だけでは不十分）
  □ 平均保有時間が24h以内に収まるか
  □ 改善対象の環境を一言で言えるか（「環境①でのP4損失を削る」等）

  NG なら案を捨てて Step 2 に戻る。

  【改善の方向性】
  「全体を削る」のではなく「特定の環境での損失だけ潰す」。
  改善提案は必ず「どの環境・どのPriority・どの状態での損失を削るか」を明示する。

  【改善手段の優先順位】
  理想形（狭いTP × 高TP率 × 速い回転）を維持したまま改善できる順に試す。
    ① TIME_EXIT 削減（特定環境での損失を削る）← 最優先
    ② エントリーフィルター改善（負け環境への参加を減らす）
    ③ TP幅を広げる ← 理想形を崩す方向・最終手段

Step 3. CSV シミュレーション（Replay の前に必ず実施）
  — 既存の結果CSVを使って Python で直接フィルター効果を試算
  — 評価軸: NET改善額・TP維持率・外科的スコア(TE削減/TP損失)
  — **環境別で評価する**（全体NETだけでなく環境①②③それぞれで効果を確認）
  — Entry フィルター変更 → CSV上で完全シミュレーション可能
  — Exit タイミング変更 → 線形近似で上限推定（実値は Replay で確認）
  — 複数アプローチを比較してから最良案を1つ選ぶ

Step 4. 提案 → ユーザー承認 ← STOP
  — 「どの環境・どのPriorityの損失を削るか」を明示
  — 期待値（NET改善・TP維持率・外科的スコア）を環境別で提示

Step 5. 実装（同じ目的の変更はまとめてOK）

Step 6. Replay 実走 → 結果確認 ← STOP

Step 7. 採用 or 却下
  — 採用: 次のステップへ
  — 却下: 即巻き戻し → Step 1 に戻る

Step 8. WORKFLOW.md 更新 ← STOP

Step 9. 本番反映（run_once_v9.py / cat_params_v9.json）← STOP

Step 10. Git コミット ← STOP
```

### Step 3 シミュレーションの判断基準

| 指標 | 定義 | 目安 |
|------|------|------|
| NET改善額 | 変更後NET - 現在NET（環境別で確認） | 大きいほど良い |
| TP維持率 | 残るTP件数 / 全TP件数 | 80%以上が望ましい |
| 外科的スコア | TE削減件数 / (TP損失件数+1) | 高いほどTP巻き添えが少ない |

**Entry フィルターは構造的にTP巻き添えが発生する（最良でも外科的スコア0.2前後）。**
TP維持率が低い場合は Exit タイミング変更を優先して検討すること。

**設計思想（CLAUDE.md より）:**
- 対象トレード: 24時間以内に決済できる取引
- ベース: レンジ回帰型（行って戻ってきてTP）
- 手数料を上回る利益を確実に取る設計
- 手段（TP幅・add回数等）は目標達成のために最適化する

---

## Replay 実行コマンド

```bash
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
echo "=====🚀 RUN START $(date) =====" && \
.venv/bin/python3 runner/replay_csv.py \
  /Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv
```

---

## ツール一覧

### tools/trade_summary.py — 本番ログ集計レポート

```bash
.venv/bin/python3 tools/trade_summary.py
.venv/bin/python3 tools/trade_summary.py --since "2026-03-24"
```

---

## 過去作業記録（Phase 0-4）

- Phase 0（2026-03-20）: cat/パッケージ・cat_v9_decider.py・cat_params_v9.json 作成
- Phase 1（2026-03-21）: run_once_v9.py 作成・H-0〜H-5 通過
- Phase 2（2026-03-21〜24）: Logic Parity 200/200 MATCH・Param Parity・Demo Run 完了
- Phase 3（2026-03-24）: Safety/Observability 完了
- Phase 4（2026-03-25）: 本番切り替え完了・cron 稼働開始
- Phase 5（2026-03-26〜）: MAX_SIDES=2 実装・本番稼働中

### 主なバグ修正記録（参照用）
- 45135バグ（2026-03-31）: SHORT TP設定時にstate未作成 → reconciliation STOP → 修正済み
- 429リトライ（2026-03-26）: get_candles() 即STOP → 最大3回リトライに変更
- PARTIAL_FILL_TP_SET 誤発火（L-12）: TTLキャンセル後の既存ポジション誤検知 → 修正済み
- SL_PCT 極小時の 40917 無限STOPループ（L-13）: _place_sl で即クローズに変更
- Bitget デモ口座 SL 非発動バグ（L-14）: fill-history 照合（Change A/B）で対処済み
