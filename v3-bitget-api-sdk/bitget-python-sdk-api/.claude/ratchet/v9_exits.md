<!-- V9_EXITS_HASH=b5af195300b2ac31 -->
# v9_exits.md — V9 の Exit 実装（gen_v9_exits.py が実コードから機械生成＝手書き禁止）

⚠️ 手で書き換えないでください。中身は `runner/replay_csv.py` と `config/cat_params_v9.json` から
機械で抜いています。V9 は改造禁止です。本書は読むだけの道具が作っています。

```
python3 scripts/priority_rebuild/gen_v9_exits.py --write    # 作り直す
python3 scripts/priority_rebuild/gen_v9_exits.py --verify   # 改変の検出
```

## なぜこの文書があるか

V9 の Exit について、手書きの要約が実装とずれていました（2026-07-27）。
その要約を引用した結果、5つの説明のうち2つが誤りでした。だから要約をやめて、
**実装から機械で抜いた事実だけ**を置きます。意味づけ（この枝は失速の枝、など）はしません。

## 決済の枝（上から順に見て、最初に成立した枝で決済する）

| # | 決済の名前 | 玉の状態 | 指標 | 参照している設定キー |
|---|---|---|---|---|
| 1 | BREAKOUT_CUT | 積み増した回数／Priority 番号 | BB幅／RSI（ショート用） | `P23_BREAKOUT_BB_WIDTH_MIN`／`P23_BREAKOUT_RSI_MIN` |
| 2 | MFE_EXIT | 保有時間（分）／含み益の最大（ドル）／Priority 番号 | **使わない** | `P22_SHORT_MFE_MAX_GATE_USD` |
| 3 | MFE_STALE_CUT | 積み増した回数／保有時間（分）／含み益の最大（ドル）／Priority 番号 | **使わない** | `P22_SHORT_MFE_STALE_GATE_USD` |
| 4 | MFE_STALE_CUT（2件目） | 積み増した回数／保有時間（分）／含み益の最大（ドル）／Priority 番号 | **使わない** | `P2_MFE_STALE_GATE_USD` |
| 5 | MFE_STALE_CUT（3件目） | 保有時間（分）／含み益の最大（ドル）／Priority 番号 | ATR14 | — |
| 6 | MFE_DRAWDOWN_CUT | 含み益の最大（ドル）／Priority 番号／いまの含み損益（ドル） | **使わない** | — |
| 7 | STOCH_REVERSE_EXIT | 保有時間（分）／含み益の最大（ドル）／Priority 番号／いまの含み損益（ドル） | ストキャス %D／ストキャス %K | `P23_STOCH_EXIT_MFE_GATE`／`P23_STOCH_EXIT_MIN_HOLD`／`P23_STOCH_EXIT_UNREAL_MIN`／`P23_STOCH_REVERSE_EXIT_ENABLE` |
| 8 | MFE_STALE_CUT（4件目） | 積み増した回数／保有時間（分）／含み益の最大（ドル）／Priority 番号 | **使わない** | `P3_MFE_STALE_GATE_USD` |
| 9 | MFE_STALE_CUT（5件目） | 積み増した回数／保有時間（分）／含み益の最大（ドル）／Priority 番号 | **使わない** | `P21_MFE_STALE_GATE_USD` |
| 10 | RSI_REVERSE_EXIT | 保有時間（分） | ADX／RSI（ショート用）／RSI の傾き | `FEAT_SHORT_RSI_REVERSE_EXIT`／`SHORT_MIN_HOLD_FOR_RSI_EXIT`／`SHORT_RSI_EXIT_ADX_MAX`／`SHORT_RSI_SLOPE_MAX`／`SHORT_RSI_THRESH` |
| 11 | MAE_CUT | 積み増した回数／保有時間（分）／Priority 番号 | **使わない** | — |
| 12 | PROFIT_LOCK | 含み益の最大（ドル）／いまの含み損益（ドル） | **使わない** | `LONG_PROFIT_LOCK_ARM_USD`／`LONG_PROFIT_LOCK_ENABLE`／`LONG_PROFIT_LOCK_USD` |
| 13 | PROFIT_LOCK（2件目） | 含み益の最大（ドル）／Priority 番号／いまの含み損益（ドル） | **使わない** | `P22_SHORT_PROFIT_LOCK_ARM_USD`／`P22_SHORT_PROFIT_LOCK_ENABLE`／`P22_SHORT_PROFIT_LOCK_USD` |
| 14 | PROFIT_LOCK（3件目） | 含み益の最大（ドル）／Priority 番号／いまの含み損益（ドル） | **使わない** | `P23_SHORT_PROFIT_LOCK_ENABLE` |
| 15 | PROFIT_LOCK（4件目） | 積み増した回数／Priority 番号 | **使わない** | — |
| 16 | STAGNATION_CUT | 保有時間（分）／含み益の最大（ドル）／Priority 番号 | **使わない** | `P4_STAGNATION_WIDE_ENABLE`／`P4_STAGNATION_WIDE_MAX_MFE`／`P4_STAGNATION_WIDE_MIN` |
| 17 | STAGNATION_CUT（2件目） | 保有時間（分）／含み益の最大（ドル）／Priority 番号 | **使わない** | `P4_STAGNATION_WIDE_ENABLE`／`STAG_MFE_USD`／`STAG_MIN_M` |
| 18 | TIME_EXIT | 保有時間（分）／いまの含み損益（ドル） | **使わない** | — |

枝は全部で 18 件です。

## 事実として言えること（数えただけ・解釈なし）

- **指標を条件に使っている枝は 4 件**です（BREAKOUT_CUT／MFE_STALE_CUT／RSI_REVERSE_EXIT／STOCH_REVERSE_EXIT）。残りの枝は、含み益・含み損益・保有時間・積み増し回数だけで決まります。
- **Priority 番号を条件に使っている枝は 15 件**です＝枝が Priority ごとに分かれています。
- **同じ決済の名前が複数の枝から返ります**（Priority 別に別々の条件で書かれているため）。

## 利確の値の決まり方（`_calc_tp_price`）

| 参照している設定キー | いまの値 |
|---|---|
| `1` | — |
| `ADX_THRESH` | 25.0 |
| `ADX_TP_THRESH_HIGH` | 35.0 |
| `FEE_MARGIN` | 1.5 |
| `FEE_RATE_MAKER` | 0.00014 |
| `P23_TP_ATR_ENABLE` | 0 |
| `P23_TP_ATR_FACTOR` | 1.5 |
| `P23_TP_PCT_MAX` | 0.02 |
| `TP_ADX_BOOST_ENABLE` | 0 |
| `TP_ADX_FACTOR` | 0.25 |
| `TP_ADX_RANGE` | 8.0 |
| `TP_FEE_FLOOR_ENABLE` | 1 |
| `TP_PCT_CLAMP_ENABLE` | 1 |
| `TP_PCT_SCALE` | 1.1 |
| `TP_PCT_SCALE_HIGH` | 1.2 |
| `nan` | — |

## この文書の限界（正直に）

- 抜いているのは「条件に出てくる名前」と「参照している設定キー」だけです。
  条件の意味（大なりか小なりか、どちらの向きか）は抜いていません。そこは実コードを読みます。
- V9 が良い設計だという保証ではありません。実装がこうなっている、という事実だけです。
- 出どころ＝`runner/replay_csv.py` の _check_exits_replay／_calc_tp_price と `config/cat_params_v9.json`。

