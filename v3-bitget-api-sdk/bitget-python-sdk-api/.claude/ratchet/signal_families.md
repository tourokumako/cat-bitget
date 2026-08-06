<!-- SIGNAL_FAMILIES hash=1a9cb4e0682cf9a8 gen_signal_families.py が自動生成＝手で書き換えない -->
# signal_families.md — 型の表（許可の一覧・全自動生成・CC の手書きの行ゼロ）

作り（まこさん確定 2026-08-06）＝ 表の本体は広く展開 ／ 削るのは機械生成の禁止だけ ／ 検算は V9 の実物。

## 表の本体（広さ）＝型 8 種 × 部品 105 種 × 時間足 8 本

| 型 | 中身（軸カタログ E-a の逐語） |
|---|---|
| E-a1 | 逆張り＝平均回帰 MR（レンジ端/行き過ぎを fade） |
| E-a2 | 順張り＝モメンタム/トレンドフォロー |
| E-a3 | ブレイクアウト（レンジ/ATH 超え＋出来高） |
| E-a4 | 戻り売り・押し目（プルバック） |
| E-a5 | グリッド（往復を仕組みで刻む） |
| E-a6 | マーケットメイク（両側 maker・在庫制御＝Avellaneda-Stoikov/Cartea・スプレッド収益） |
| E-a7 | order-flow/需給（Institutional Accumulation・Flow Momentum） |
| E-a8 | レンジ内 value（stable range で仕込む） |

部品と時間足＝observe_diag のカタログ（2026-08-06 材料検査済み）の全部。**下の禁止に当たらない組み合わせは全部 許可。**

## 削る（全部 機械生成・根拠つき）

### 禁止1 向きの条件に使えない部品（区分＝状態量・ボラ量）… 20 種
根拠: indicator_reference_diag の「方向」の欄（2026-08-06 材料検査1＝合成系列＋実データの2本柱で全種検証済み・❌0件）
ADX14、ADX21、ADX7、ATR%14、ATR%21、ATR%7、BB幅(20,2.0)、BB幅(20,3.0)、BB幅(50,2.0)、BB幅(50,3.0)、Donchian幅%20、Donchian幅%48、S-Rタッチ数(288,0.003)、body比、realized_vol20、realized_vol50、volume_ratio20、volume_ratio50、zscore_return20、zscore_return50

### 禁止2 カタログ注記による向きの除外 … 6 種
根拠: 2026-08-06 材料検査1 の実測（普通の相場で向きの差が四分位幅の半分以下）＋まこさん OK
安値からの経過バー24、安値からの経過バー48、安値からの経過バー96、高値からの経過バー24、高値からの経過バー48、高値からの経過バー96

### 禁止3 有効標本数の不足（部品×時間足）… 113 組
規則: 値決め窓 549 日で有効標本数 n_eff < 30 の（部品×時間足）は条件の候補にしない
根拠: CP2 監査 4-4 の算術＋search_limits.json の n_min（まこさん OK 2026-08-01）。恒久の接続（検査5 の実測表）は D9 の直しで行う

| 部品 | 時間足 | n_eff |
|---|---|---|
| ADX21 | 1d | 26.1 |
| DI差21 | 1d | 26.1 |
| MACD線%(12,26) | 1d | 21.1 |
| MACDシグナル線%(12,26,9) | 1d | 21.1 |
| MACDヒスト%(12,26,9) | 1d | 21.1 |
| RSI21 | 1d | 26.1 |
| ROC24 | 1d | 22.9 |
| CMF20 | 1d | 27.4 |
| OBV傾き20 | 1d | 27.4 |
| close vs 基準線%(26) | 1d | 21.1 |
| RCI26 | 1d | 21.1 |
| EMA20傾き% | 1d | 27.4 |
| EMA50傾き% | 1d | 11.0 |
| EMA200傾き% | 4h | 16.5 |
| EMA200傾き% | 6h | 11.0 |
| EMA200傾き% | 1d | 2.7 |
| ATR%21 | 1d | 26.1 |
| BB%b(20,2.0) | 1d | 27.4 |
| BB幅(20,2.0) | 1d | 27.4 |
| BB%b(20,3.0) | 1d | 27.4 |
| BB幅(20,3.0) | 1d | 27.4 |
| BB%b(50,2.0) | 1d | 11.0 |
| BB幅(50,2.0) | 1d | 11.0 |
| BB%b(50,3.0) | 1d | 11.0 |
| BB幅(50,3.0) | 1d | 11.0 |
| realized_vol20 | 1d | 27.4 |
| realized_vol50 | 1d | 11.0 |
| Donchian幅%20 | 1d | 27.4 |
| Donchian幅%48 | 1d | 11.4 |
| zscore20 | 1d | 27.4 |
| zscore_return20 | 1d | 27.4 |
| zscore50 | 1d | 11.0 |
| zscore_return50 | 1d | 11.0 |
| volume_ratio20 | 1d | 27.4 |
| volume_ratio50 | 1d | 11.0 |
| swing高値距離%24 | 1d | 22.9 |
| swing安値距離%24 | 1d | 22.9 |
| 高値からの経過バー24 | 1d | 22.9 |
| 安値からの経過バー24 | 1d | 22.9 |
| 形スコア24(V=+/M=−) | 1d | 22.9 |
| W字(24,0.003) | 1d | 22.9 |
| swing高値距離%48 | 1d | 11.4 |
| swing安値距離%48 | 1d | 11.4 |
| 高値からの経過バー48 | 1d | 11.4 |
| 安値からの経過バー48 | 1d | 11.4 |
| 形スコア48(V=+/M=−) | 1d | 11.4 |
| W字(48,0.003) | 1d | 11.4 |
| swing高値距離%96 | 6h | 22.9 |
| swing高値距離%96 | 1d | 5.7 |
| swing安値距離%96 | 6h | 22.9 |
| swing安値距離%96 | 1d | 5.7 |
| 高値からの経過バー96 | 6h | 22.9 |
| 高値からの経過バー96 | 1d | 5.7 |
| 安値からの経過バー96 | 6h | 22.9 |
| 安値からの経過バー96 | 1d | 5.7 |
| 形スコア96(V=+/M=−) | 6h | 22.9 |
| 形スコア96(V=+/M=−) | 1d | 5.7 |
| W字(96,0.003) | 6h | 22.9 |
| W字(96,0.003) | 1d | 5.7 |
| close vs EMA20% | 1d | 27.4 |
| close vs EMA50% | 1d | 11.0 |
| close vs EMA200% | 4h | 16.5 |
| close vs EMA200% | 6h | 11.0 |
| close vs EMA200% | 1d | 2.7 |
| close vs SMA20% | 1d | 27.4 |
| close vs SMA50% | 1d | 11.0 |
| close vs SMA200% | 4h | 16.5 |
| close vs SMA200% | 6h | 11.0 |
| close vs SMA200% | 1d | 2.7 |
| close vs VWAP%288 | 2h | 22.9 |
| close vs VWAP%288 | 4h | 11.4 |
| close vs VWAP%288 | 6h | 7.6 |
| close vs VWAP%288 | 1d | 1.9 |
| close vs Keltner上%(20,2.0) | 1d | 27.4 |
| close vs Keltner下%(20,2.0) | 1d | 27.4 |
| close vs 24本高値% | 1d | 22.9 |
| close vs 24本安値% | 1d | 22.9 |
| close vs 48本高値% | 1d | 11.4 |
| close vs 48本安値% | 1d | 11.4 |
| close vs 96本高値% | 6h | 22.9 |
| close vs 96本高値% | 1d | 5.7 |
| close vs 96本安値% | 6h | 22.9 |
| close vs 96本安値% | 1d | 5.7 |
| close vs pivotPP%288 | 2h | 22.9 |
| close vs pivotPP%288 | 4h | 11.4 |
| close vs pivotPP%288 | 6h | 7.6 |
| close vs pivotPP%288 | 1d | 1.9 |
| close vs pivotR1%288 | 2h | 22.9 |
| close vs pivotR1%288 | 4h | 11.4 |
| close vs pivotR1%288 | 6h | 7.6 |
| close vs pivotR1%288 | 1d | 1.9 |
| close vs pivotS1%288 | 2h | 22.9 |
| close vs pivotS1%288 | 4h | 11.4 |
| close vs pivotS1%288 | 6h | 7.6 |
| close vs pivotS1%288 | 1d | 1.9 |
| fib位置96 | 6h | 22.9 |
| fib位置96 | 1d | 5.7 |
| close vs POC%288 | 2h | 22.9 |
| close vs POC%288 | 4h | 11.4 |
| close vs POC%288 | 6h | 7.6 |
| close vs POC%288 | 1d | 1.9 |
| close vs VAH%288 | 2h | 22.9 |
| close vs VAH%288 | 4h | 11.4 |
| close vs VAH%288 | 6h | 7.6 |
| close vs VAH%288 | 1d | 1.9 |
| close vs VAL%288 | 2h | 22.9 |
| close vs VAL%288 | 4h | 11.4 |
| close vs VAL%288 | 6h | 7.6 |
| close vs VAL%288 | 1d | 1.9 |
| S-Rタッチ数(288,0.003) | 2h | 22.9 |
| S-Rタッチ数(288,0.003) | 4h | 11.4 |
| S-Rタッチ数(288,0.003) | 6h | 7.6 |
| S-Rタッチ数(288,0.003) | 1d | 1.9 |

## ★機械で導けなかったもの（CC は書かない・まこさんの判断待ち）

- 向きの矛盾の定義: （空欄）型の狙う向きと条件の向きの矛盾の定義＝機械で導く根拠がまだ無い。CC は書かない。まこさんの判断待ち
- 役割ごとの系統の絞り: （空欄）役割（引き金・環境認識・十分性・位置）ごとに系統を絞る決まり＝機械で導く根拠がまだ無い。CC は書かない。まこさんの判断待ち

## 承認

- 指紋: None（まこさんの承認の指紋が入るまで、この表は無効（G1 が生成器のコードの書き込みを止める））
