# headroom_analysis_addendum_spec.md — 頭打ち原因分析 追加分析

作成日: 2026-05-13
前提: headroom_analysis_spec.md / headroom_analysis_summary.md 完了済
目的: 「構造的限界」と「Entry規則の網羅性不足」を切り分ける

---

## §1 切り分け論点

前回分析で以下が判明:
- Entry質: random より p=0.0032 で有意に良い（OK）
- 完璧Exit: 月次平均 $5,276.93（合格ラインの2.7倍）
- worst month: 完璧Exit でも $40.41
- 方向偏り: SHORT $4,197 / LONG $308
- regime偏り: downtrend $4,558 / 他全部マイナスor微益
- 時間帯偏り: 夜間+ / 日中-

これらから「Entry規則は機能しているが、カバー範囲が偏っている」可能性が高い。
ただし「特定月にtrade自体が少なくて構造的に届かない」可能性も残る。
切り分けるための追加分析が必要。

---

## §2 追加分析項目

### 追加1: 月ごとtrade数分布

| 集計内容 |
|---|
| 12ヶ月それぞれの trade数（baseline / matched subset 733 trade ベース）|
| 月別 net_usd_sum（baseline・perfect_exit_K96・最良現実Exit パターン）|
| worst month と best month が**それぞれどの月か**特定 |

出力: `headroom_step5_monthly_breakdown.csv`

### 追加2: worst month / best month の詳細解剖

worst month（perfect_exit_K96 で $40.41 の月）と best month の対比:

| 軸 | 集計 |
|---|---|
| その月の trade数 | 何件 trade した |
| side 分布 | LONG / SHORT 比率 |
| regime 分布 | downtrend / uptrend / range / mixed 比率 |
| hour 分布 | どの時間帯で trade したか |
| priority 分布 | どの Priority が動いたか |
| その月の市場状況 | BTC 価格レンジ・ATR 中央値・regime 滞在比率 |

出力: `headroom_step6_worst_best_month_detail.csv` + サマリーmd

### 追加3: LONG が稼げない原因の分離

LONG MFE/MAE は random より良い (p=0.006) のに net $308 しか稼げてない理由を分離:

| 切り口 | 集計 |
|---|---|
| LONG trade の MFE 取りこぼし | mfe_usd - net_usd の中央値・分布 |
| LONG trade の exit_reason 分布 | TP / TRAIL / TIME_EXIT / SL / その他 |
| LONG trade の hold_min 分布 | 早すぎ Exit か |
| LONG trade を完璧Exit したらいくらか | LONG だけの perfect_exit シミュレーション |

出力: `headroom_step7_long_diagnosis.csv` + サマリーmd

### 追加4: missed_fire（撃ち損ね）抽出

**前回 step3 と同様 抽出不可として明示**（2026-05-13 まこさん指示 = Option A）。
理由: replay_csv.py の出力には Entry 条件成立だが発火しなかった bar のログが含まれていない。再 Replay + logging 改修が必要だが、本タスクのスコープ外。

出力: `headroom_step8_missed_fire.csv`（N/A + 理由のみ）

---

## §3 結論パターン判定（切り分け）

| 観察パターン | 結論 |
|---|---|
| worst month の trade数が極端に少ない | **構造的限界**（その月は市場が動かなかった or 現Priority条件が成立しなかった）|
| worst month の trade数は普通だが LONG/uptrend/日中 ばかり | **Entry網羅性不足**（新Priority で穴埋め可能）|
| missed_fire が多い | **Position管理が原因**（同時保有制御で機会逃してる）→ 本タスクでは判定不能 |
| LONG完璧Exit でも稼げない | **LONG Entry規則が悪い**（SHORT と質的に違う）|
| LONG完璧Exit で稼げる | **LONG Exit設計が悪い**（取りこぼしてる）|

---

## §4 成果物

- `results/priority_rebuild/headroom_step5_monthly_breakdown.csv`
- `results/priority_rebuild/headroom_step6_worst_best_month_detail.csv`
- `results/priority_rebuild/headroom_step7_long_diagnosis.csv`
- `results/priority_rebuild/headroom_step8_missed_fire.csv`（N/A + 理由）
- `results/priority_rebuild/headroom_analysis_addendum_summary.md`

**ダッシュボードタブ反映は省略**（2026-05-13 まこさん指示）。CSV + サマリー md のみで完了とする。

---

## §5 所要時間目安

| 内訳 | 時間 |
|---|---|
| 追加1 月別集計 | 数分 |
| 追加2 worst/best 解剖 | 数十分 |
| 追加3 LONG 原因分離 | 数十分 |
| 追加4 missed_fire 抽出（A: 抽出不可明示）| 数分 |
| **合計** | **30 分〜1 時間** |

---

## §6 完了報告必須証跡 5点（WORKFLOW.md準拠）

1. コード総点検 grep 結果
2. 数値の二重提示
3. 成果物ファイル実体
4. 実行ログ
5. 絞り込み示唆語彙の自己grep 結果
