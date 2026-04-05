# 引き継ぎメモ: CSV リプレイスクリプト作成

作成日: 2026-04-02

---

## 目的

本番エンジン（run_once_v9.py）と同じロジックを CSV データで動かすリプレイスクリプトを  
**このリポ（cat-bitget）内に** 作成する。

```
runner/replay_csv.py  ← 作成場所
```

---

## なぜ作るのか

バックテスト（cat-swing-sniper）と本番（cat-bitget）の乖離を埋めるため。  
同じ CSV を両方に流して差分を取る。

```
同じCSVデータ
  ├── バックテスト（CAT_v9_regime.py）     → 結果A
  └── 本番エンジンリプレイ（replay_csv.py）→ 結果B

A と B の差 = バックテスト側で修正すべき箇所
```

---

## 前回セッションの分析結果

### 本番 vs バックテスト ギャップ（同期間 7.4日: 3/26〜4/2）

| 指標 | バックテスト | 本番 | 差 |
|------|------------|------|-----|
| NET/day | +$170.2 | -$19.6 | **-$189.8** |
| トレード数/day | 20.9件 | 9.3件 | 2.2倍少ない |
| P23 SHORT/day | 11.5件 | 3.4件 | **3.5倍少ない** |
| P23 TP率 | 84% | 67% | -17pt |
| P23 PROFIT_LOCK | 12% | 0% | なぜか不発 |
| P23 TIME_EXIT | 0% | 12.5% | 360min ブロック |

### 既に特定した事実

- `SHORT_TIME_EXIT_MIN`: BT=480 / 本番config=720 だが、本番の実際の発動は全件 360min
  - → 本番は 480×0.75=360 で動いている（config の 720 は不使用）
  - → **BT と TIME_EXIT タイミングは揃っている**
- P23 SHORT PROFIT_LOCK V2 は本番コードに実装済み・有効だが **live では一件も発動していない**
  - ARM=$15 条件（mfe_usd >= 15）に届く前に TIME_EXIT になっている可能性
- **P23 件数が 3.5倍少ない主因は TIME_EXIT による 360min スロット占有**
  - BT では TP が平均 10〜30min で決着 → スロット解放 → 次エントリー
  - 本番では 360min ブロックが発生 → その間 BT なら 8〜10件入れる
- **BT と本番の TP 率差（84% vs 67%）の根本原因はまだ不明**
  - 仮説: post-only 指値注文の約定ラグ（BT は close で即時約定を前提）

### 未解決の問題

- MIDTERM_CUT add=5 の false positive（本番 3/30、4/1 で 2件）
  - 閾値を add>=4 のとき -$50 に変更するコードはバックテスト側に実装済み
  - ただし本番 cat_params_v9.json に `LONG_MIDTERM_PNL_USD_ADD4` が未追加
  - また本番 run_once_v9.py の `_check_exits` も修正が必要

---

## 作成するスクリプトの仕様

### ファイル: `runner/replay_csv.py`

**入力**:
- CSV ファイル（`data/BTCUSDT-5m-*_combined.csv` 形式）
- `config/cat_params_v9.json`

**ループ処理（1バー = 1回の run_once_v9 相当）**:

```
for i, bar in enumerate(csv_bars):
    1. pending 約定チェック
       - post-only 指値: 翌バー以降で low<=limit(LONG) or high>=limit(SHORT) で約定
       - TTL = PENDING_TTL_BARS(3) でキャンセル

    2. Exit チェック（_check_exits と同ロジック）
       - TP → その他の順
       - mark_price = close（BT と同条件、スリッページなし）

    3. Entry 判断（cat_v9_decider.check_entry_priority）
       - 発火 → pending に登録（limit price = close）

    4. MFE 更新
```

**出力**:
- `results/replay_{filename}.csv`（live_trades.csv と同じカラム構成）
- サマリー表示（exit_reason 別・priority 別）

### 注意点

- `time.time()` を使わず `ts_ms`（バーのタイムスタンプ）で保持時間を計算
- API 呼び出し・ファイル書き込み（state JSON）は全てスキップ
- MFE は close ベースで更新（バックテストと同条件）
- add 上限チェック: 既存ポジションの priority で `MAX_ADDS_BY_PRIORITY` を参照

### 参照すべき関数（run_once_v9.py）

| 機能 | 参照元 |
|------|--------|
| exit 判定ロジック | `_check_exits()` L390-490 |
| TP 価格計算 | `_calc_tp_pct()` L177-198 |
| ADD 上限チェック | `main()` L1200-1208 |
| entry 判断 | `cat_v9_decider.decide()` |

---

## 差分比較の方法

```bash
# 1. バックテスト実行（v9_27）
cd cat-swing-sniper && python strategies/CAT_v9_regime.py
# → results/v9/result_v9_27.csv

# 2. リプレイ実行
cd cat-bitget/... && python runner/replay_csv.py data/BTCUSDT-5m-2026-03-27_04-01_combined.csv
# → results/replay_v9_27.csv

# 3. 差分分析スクリプト（別途作成）
python tools/compare_bt_vs_replay.py
```

比較観点:
- エントリー件数・タイミングのズレ（バーインデックス差）
- exit reason の分布差
- 同一エントリー時刻のトレードがどう異なるか

---

## MIDTERM_CUT add=5 の修正（別タスク）

リプレイスクリプト完成後に実施。

**変更対象**:
1. `config/cat_params_v9.json` に `"LONG_MIDTERM_PNL_USD_ADD4": -50.0` を追加
2. `runner/run_once_v9.py` の `_check_exits()` L445-449 を修正:

```python
# 現行
if unreal < float(params.get("LONG_MIDTERM_PNL_USD", -30.0)):

# 変更後
_add = int(pos.get("add_count", 1))
_midterm_thresh = (
    float(params.get("LONG_MIDTERM_PNL_USD_ADD4", -50.0))
    if _add >= 4
    else float(params.get("LONG_MIDTERM_PNL_USD", -30.0))
)
if unreal < _midterm_thresh:
```

**根拠**: 本番 3/30・4/1 の add=5 MIDTERM_CUT 2件はいずれも false positive（カット後 75分〜2時間で entry 価格まで回復）。add=5 (0.12BTC) で -$30 は -$250/BTC = 低ボラ相場のノイズ範囲内。

---

## バックテスト側の変更状況

- `strategies/CAT_v9_regime.py`: `LONG_MIDTERM_PNL_USD_ADD4=-50.0` の分岐を追加済み（未commit）
- dev4 に v9_27（3/27-4/1）を追加済み（未commit）
- `LONG_MIDTERM_PNL_USD_ADD4` パラメータを params dict に追加済み（未commit）

次セッションで本番側の修正と合わせて commit すること。
