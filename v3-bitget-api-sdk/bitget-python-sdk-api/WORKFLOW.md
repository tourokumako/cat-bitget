# WORKFLOW.md — V9調整方向性検討（2026-04-07 更新）

---

## 現在の方針（2026-04-07）

**V10 開発を中断し、V9 ベースで TP 幅を狭くする方向を検討中。**

---

## V9 TP=0.0006 検証結果（2026-04-07、90日データ）

| パターン | TP率 | NET/日 | 備考 |
|------|------|------|------|
| V9 元（TP=0.005、add有） | 49% | +$20.3 | WORKFLOW.md記録値 |
| V9 TP=0.0006、add有、SL=0.05 | 94.4% | -$3.0 | TIME_EXIT -$588 が元凶 |
| V9 TP=0.0006、add無、SL=0.05 | 92.6% | -$3.3 | MFE_STALE 増加で悪化 |
| V9 TP=0.0006、add無、SL=0.0006 | 68.1% | -$1.6 | TIME_EXIT消えるがTP率低下 |

### 発見事項

- **V9 シグナルは TP=0.0006 でも 94% の TP 率を持つ**（V10 Stoch OB/OS は 63.6%）
- add システムは TP=0.5% 前提の設計。TP=0.0006 では TIME_EXIT で大損失になる
- SL を締めると TIME_EXIT は消えるが TP率が 68% に低下（必要 73.3%）
- ギャップは必要 73.3% に対して実 68.1%（-5.2%）まで縮小

### 必要TP率の確認（TP=SL=0.0006、maker両方）

```
必要TP率 = (SL_gross + fee) / (TP_gross + SL_gross) = 73.3%
実際のTP率 = 68.1%  →  あと 5.2% 不足
```

### 次のタスク

- [ ] TP 幅を広げて必要 TP 率を下げる（例: TP=0.0012、SL=0.0006）
      → 必要 TP 率が下がる分、実 TP 率がどこまで下がるか確認
- [ ] シグナルフィルタリング（時間帯・ADX）で TP 率 73% 以上を目指す
      → 時間帯別 NET が偏っている（3時・5-6時・9-11時・13時・17時・19-21時が弱い）
- [ ] 採用後は 180 日データで過学習チェック

---

## V10 改善フロー（必ず守る）

**このフローを必ず順番通りに実行する。前のステップが完了するまで次に進まない。**

```
Step 1: 現状把握
  - Replay 実走・結果CSV確認
  - TP/SL別・LONG/SHORT別に集計
  - 結果を WORKFLOW.md に記録

Step 2: 環境分類 × 深掘り分析
  【環境定義（ADX × ATR）】
  ① レンジ   : ADX < 25（相場が静か）
  ② トレンド : ADX ≥ 25（相場が動いている）
  ③ 遷移     : 境界・不安定期

  【分析チェックリスト（必ず全て確認）】
  □ 環境別 × net_usd（どの環境で勝っているか）
  □ LONG / SHORT 別
  □ SL_FILLED の MFE 分析
    → MFE < 0: エントリー直後から逆行 → シグナル品質の問題
    → MFE > 0: 有利に動いたが戻った → SL幅・TP幅の問題
  □ 流動性異常チェック（スプレッド極端に広い足の確認のみ）

  集計だけからの仮説立案禁止。個別トレードを確認してから仮説を立てる。

  【設計思想】
  - TP幅を狭くしてあらゆる相場に対応するスキャル設計
  - 時間帯・流動性による絞り込みは設計思想と矛盾するため原則行わない

Step 2.5: 設計思想チェック ← STOP（提案前に必ず通過すること）
  □ CLAUDE.md のスキャル設計思想（小利確積み上げ）と整合しているか
  □ lessons.md に同じ失敗パターンがないか
  □ 改善対象を一言で言えるか（「トレンド環境でのSHORT損失を削る」等）
  NG なら案を捨てて Step 2 に戻る。

Step 3: CSV シミュレーション（Replay 前に必ず実施）
  - 既存の結果CSVを使って改善効果を試算してから Replay を走らせる
  - 評価軸: NET改善額・TP維持率

Step 4: 提案 → ユーザー承認 ← STOP

Step 5: 実装（1変更 = 1ターン・L-5）

Step 6: Replay 実走 → 結果確認 ← STOP

Step 7: 採用 or 却下
  - 採用: 次のステップへ
  - 却下: 即巻き戻し → Step 1 に戻る

Step 8: WORKFLOW.md 更新 ← STOP

Step 9: Git コミット ← STOP
```

---

## ⚠️ V9 アーカイブ済み（2026-04-06）

このV9戦略は開発を終了し、失敗例として保管。
新戦略（V10：1分足ストキャスベーススキャル）の開発へ移行。

### V9 総括

| 項目 | 結果 |
|------|------|
| 90日Replay NET | +$20.3/day |
| 180日Replay NET | +$5.3/day（急騰レジームで崩壊） |
| 本番投入基準（$100/day） | **未達・達成不可** |
| 失敗の根本原因 | addナンピン+広いTPでスイング化。設計思想と乖離 |
| バックテスト($61/day)の問題 | same-bar fill・手数料未控除・P23過学習 |

### 次のタスク（V10開発）← 完了済み

1. ~~1分足BTCデータ取得~~ → Binance API で取得済み
2. ~~ストキャスベーススキャル戦略の設計~~ → 設計・検証中
3. ~~シミュレーター構築（1分足対応replay）~~ → `runner/replay_v10.py` 完成
4. 検証 → 本番投入 ← **現在ここ（未達）**

---

## セッション開始時の確認事項（V9 参照用）

| 項目 | 状態 |
|------|------|
| V9フェーズ | **アーカイブ済み** |
| ALLOW_LIVE_ORDERS | True（変更しない） |
| open_position_long.json | なし |
| open_position_short.json | なし |

### 現在の cat_params_v9.json（2026-04-05 更新）

| パラメータ | 値 |
|-----------|-----|
| **LONG_TP_PCT / SHORT_TP_PCT** | **0.005**（旧 0.0032） |
| **P22_TP_PCT** | **0.005** |
| **P23_TP_PCT** | **0.007**（旧 0.005） |
| ~~P24_TP_PCT~~ | ~~0.007~~ （P24無効化のため参照なし） |
| LONG_SL_PCT / SHORT_SL_PCT | 0.05 |
| LONG_TIME_EXIT_MIN | 150 |
| SHORT_TIME_EXIT_MIN | 480 |
| P2_TIME_EXIT_MIN | 480 |
| **LONG_TIME_EXIT_DOWN_FACTOR** | **0.50**（旧 0.75） |
| **SHORT_TIME_EXIT_DOWN_FACTOR** | **0.50**（旧 0.75） |
| LONG_MAX_ADDS / SHORT_MAX_ADDS | 5 |
| **MAX_ADDS_BY_PRIORITY** | **`{"2": 5, "4": 5, "22": 5, "23": 5, "24": 5}`**（旧 `{"2": 4}`） |
| **P23_ADX_MAX** | **40**（旧 50） |
| **P4_ADX_EXCL_MIN / P4_ADX_EXCL_MAX** | **20.0 / 25.0**（新規・弱トレンド移行期除外） |
| **P22_SHORT_BB_MID_SLOPE_MAX** | **-20.0**（旧 -50.0） |
| **P2_ADX_EXCL_MIN / P2_ADX_EXCL_MAX** | **40.0 / 50.0**（新規・超強トレンド帯除外） |
| **TP_ADX_BOOST_ENABLE** | **0**（旧 1。TP圧縮バグ解消） |
| TP_PCT_CLAMP_ENABLE | 1 |
| FEAT_SHORT_RSI_REVERSE_EXIT | true |
| LONG_PROFIT_LOCK_ENABLE | 1 |
| P23_SHORT_PROFIT_LOCK_ENABLE | 1 |
| LONG_POSITION_SIZE_BTC / SHORT_POSITION_SIZE_BTC | 0.024 |
| **ENABLE_P24_SHORT** | **false**（旧 true。P22/P23干渉で全体NET悪化のため無効化） |

### データファイルパス（固定）

| 用途 | パス |
|------|------|
| キャンドル 90日（Replay 入力） | `/Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |
| キャンドル 180日 | `/Users/tachiharamasako/Documents/GitHub/cat-swing-sniper/data/BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv` |
| Replay 結果 CSV | `results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |

### 現在の replay_csv.py の設定

| 項目 | 値 |
|------|-----|
| PENDING_TTL_BARS | 2（= 翌バー1本のみで fill 判定） |
| fill 判定 | intra-bar（LONG=low, SHORT=high） |
| limit_price | close ± 0.01% |
| 手数料 | entry=maker / exit TP=maker / exit SL=taker |
| **サマリー出力** | **Priority×Exit クロス・add_count別・entry指標別に拡張済み** |

### 直近 Replay 結果（2026-04-05 最新）

| 項目 | 値 |
|------|-----|
| 総トレード数 | 385件 |
| NET | **+$1,828 / 90日（+$20.3/day）** |
| TP率 | — |
| CSV | `results/replay_BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv` |

### Priority別 NET（最新）

| Priority | 件数 | NET | TP率 | TIME_EXIT | 主な問題 |
|---------|------|-----|------|-----------|---------|
| P2-LONG | 109 | **+$895** | 71% | 11件/-$206 | MFE_STALE_CUT 14件/-$198 |
| P22-SHORT | 89 | **+$237** | 54% | 27件/-$651 | MFE_STALE_CUT 3件/-$126 |
| P23-SHORT | 79 | **+$387** | 54% | 13件/-$299 | MFE_STALE_CUT 16件/-$196 / SL 1件/-$79 |
| P24-SHORT | — | — | — | — | **無効化（ENABLE_P24_SHORT=false）** |
| P4-LONG | 108 | **+$310** | 52% | 46件/-$615 | — |

### 構造的天井の更新（重要）

**TP_ADX_BOOST無効化後の TP 利益合計: ~$2,807 / 90日 = ~$31/day（349件）**  
1件あたりTP利益: P2=$17.6 / P4=$9.4 / P23=$9.7 に改善。

→ $100/day 達成にはさらにトレード数増加（スケールアップ）が必要。

### 重要な分析知見（2026-04-04〜05）

- **TIME_EXIT の 62% は「エントリー直後から逆行」** → TP_PCT 調整では救えない。エントリー品質の問題。
- **atr_14 が最も分離力の強い指標**: TP_FILLED の atr 平均 232 vs TE_bad（MFE<0.2%）の atr 平均 166
- **低ボラ（atr<150）環境はレンジ回帰が起きず TIME_EXIT になりやすい**（P4/P2 共通）
- **Entry フィルターは P4→P2 の流入（L-19）に注意**。片方だけ追加すると相殺・逆転する。
- **P23 TIME_EXIT は全件逆行**（L-27タイムゾーンバグで誤分析→UTC修正後確認）。ret_5フィルターは L-26 で禁止、atr_14上限も逆効果。
- **P23_ADX_MAX=40 で解決**: ADX 40-50（強トレンド）への逆張りが損失の主因。ADX 30-40 のみに絞り P23 を黒字化（-$114→+$63）。
- **TP_ADX_BOOST_ENABLE=1 + TP_ADX_FACTOR=0.25 はTPを縮小していた**: ADX>=33でTP_PCT=0.5%→0.15%に圧縮。P2/P23/P24のTP利益を$2-3/件に抑制していた。0無効化でP2 TP=$17.6/件に正常化。NET+$287→+$896。
- **L-27 根絶（2026-04-05）**: replay_csv.py の entry/exit_time を UTC 出力に修正。MFEマッチ率 54%→100%。MFE正確値: TIME_EXIT 116件の81%がTP未到達（MFE 0〜0.55%）。※TP縮小は不採用（下記参照）。
- **P4_ADX_EXCL_MIN/MAX**: ADX_MINと違い「除外バンド」で実装。ADX<20（黒字）とADX>=25（一部良好）を維持したまま20-25（TP率50%）を除外。
- **分析スクリプトのタイムゾーン注意（L-27）**: Replay CSV は JST、candles.csv は UTC。変換せずに使うと 9h ずれたバーを参照する。
- **P24はP22/P23のSHORT枠を圧迫していた**: P24無効化でP23が $14→$346 に大幅改善。Priority間のSHORT枠競合を常に意識すること。
- **P22/P23/P24間の孤立シミュレーションは不正確**: 同一SHORT枠を共有するため、1つのExitタイミング変更が他の入出タイミングに連鎖する。MFE_STALE_CUT等の閾値グリッドはP2/P4（孤立性高）には有効だがP22/P23には過信禁止。
- **MFE_STALE_CUT有効パターン**: add==1 かつ hold>=120min（SHORT）/40min（LONG）で MFE低い場合。add≥2はMFE高く設計上の損失（add深→大TP利益のトレードオフ）なので対象外。
- **P4 TIME_EXIT**: 44件/-$611。MFE_STALE/TIME_EXIT短縮/STAGNATION/ADX_MAX（L-19）全て失敗。P4 ADX30-40は「P2より安価な損失吸収役」構造（P4-$116 vs P2流入-$494）。エントリーフィルターでの解決不可。
- **P2_ADX_EXCL 40-50**: P2は超強トレンド(ADX40-50)でTE率29-42%。ADX50+は再びTP率高い（U字型）。P4はADX40-50で0件のためL-19なし。+$162/90日実測。
- **P4 ADX30-40は L-19 の「盾」**: P4がADX30-40スロットを保持することでP2の劣質流入を防ぐ。P4を除くと同スロットにP2が入りavg-$26/件の損失。P4除外(-$116)より悪化。

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
| **P23_ADX_MAX: 50→40** | **+$177（NET +$76→+$253、P23 -$114→+$63、TP率86%→88%）ADX40-50の強トレンド逆張りを除外** |
| **P4_ADX_EXCL_MIN/MAX: 20-25** | **+$34（NET +$253→+$287）ADX20-25の弱トレンド移行期を除外（ADX<20良環境は維持）** |
| **TP_ADX_BOOST_ENABLE: 1→0** | **+$609（NET +$287→+$896）TP圧縮バグ解消。P2 TP avg $3.2→$17.6/件** |
| **P22_SHORT_BB_MID_SLOPE_MAX: -50→-20** | **+$124（NET +$896→+$1,020）P22 8件→87件に拡大。-10は崩壊（MFE_STALE_CUT急増）** |
| **MAX_ADDS_BY_PRIORITY["4"]: 1→3** | **+$104（NET +$1,020→+$1,124）P4 TP avg $9.4→$17.0/件。MIDTERM_CUT削除済みのため再add有効** |
| **MAX_ADDS_BY_PRIORITY["4"]: 3→5（拡張グリッド）** | **+$76（NET +$1,124→+$1,200）P4 NET $182→$258。TIME_EXIT add=5は1件のみ** |
| **MAX_ADDS_BY_PRIORITY["2"]: 4→5** | **+$24（NET +$1,200→+$1,224）P2 NET $733→$740** |
| **Priority別TP実装 + P23_TP_PCT: 0.005→0.007 / P24_TP_PCT: 0.005→0.007** | **+$149（NET +$1,344→+$1,493）P23 $215→$319、P22 $177→$210、P24 -$63→-$52** |
| **ENABLE_P24_SHORT: true→false（P24無効化）** | **+$96（NET +$1,493→+$1,589）P22 $205→$228、P23 $14→$346。P24がP22/P23のSHORT枠を圧迫していた構造が解消** |
| **P2/P23 MFE_STALE_CUT追加（add==1, hold>=120min）+ 閾値P2=$5/P23=$4** | **+$77（NET +$1,589→+$1,666）P23 TIME_EXIT 25→13件。閾値はシミュレーションで最適化（フルReplay不要）** |
| **P2_ADX_EXCL_MIN/MAX: 40-50** | **+$162（NET +$1,666→+$1,828）P2 TIME_EXIT 22→11件、TP率65%→71%。ADX40-50は超強トレンドでP2モメンタムが失敗しやすい帯域。L-19なし（P4はADX40-50に0件）** |

**却下済み:**
| 変更 | 理由 |
|------|------|
| LONG_MIDTERM_PNL_USD: -30→-20 | MIDTERM_CUT が 17→23件に増加（逆効果） |
| P2/SHORT_TIME_EXIT_MIN: 480→240 | TP 14件減少・TIME_EXIT 増加（+$146 のみ） |
| P4 ADX Entry フィルター（>=24等） | TP維持率 57%（基準 80%未満） |
| P23_SLOPE<=-25 Entry フィルター | 外科的スコア 0.15（不十分） |
| P23 transit_A × ret_5>0 フィルター | signal/fill バーズレで CSV+$143 → Replay +$2（L-26） |
| **P4 ret_5 ≤ 0.25 Entry フィルター** | **L-19 発生: P4除外→P2流入で P2 NET -$47悪化。全体 +$76→+$29（-$47）。P4は±0改善なし。** |
| **P23 ret_5 ≤ 0.05 Entry フィルター** | **L-26 発動: CSV期待値+$242 → Replay +$6。TP 40件が余計に除外。signal/fill バーズレで ret_5 が大きくズレた。** |
| **P24 MACDクロス軸へ再設計** | **P24単体 +$48 も P22 -$208（SHORT枠干渉）で全体 -$159。MACDは単なる干渉増加要因になっただけ。** |
| **P22 add=1 MFE_STALE_CUT（gate=$4, hold>=120min）** | **シミュレーション+$31予測も Replay -$59。STALE発火17件（予測9件）→ P22ポジション解放タイミング変化による interaction効果。P22はSHORT間干渉が強く孤立シミュレーション不正確。** |
| **P4_ADX_MAX=30** | **L-19: P4+$77も P2-$318でトータル-$241。P4ブロック→P2がADX30-40で劣質トレード流入（avg-$26/件）** |
| **P4 MFE_STALE_CUT add=1 hold>=30m** | **TP誤カット損 -$52 > TE改善 +$32。P4のTP到達は遅い（30min時点MFE<$5でも最終TP）** |
| **P4 TIME_EXIT_MIN 短縮（P4_TIME_EXIT_MIN=130-140）** | **価格回復パターンが多く早期カットが逆効果。75min→70minで net差-$45** |
| **P4 STAGNATION_WIDE 有効化** | **add=3 TP誤カット（tp$25→cut-$32）。P4はadd深まってからTP到達する設計と相性悪い** |
| **UTC 3h 全Priority除外** | **月別一貫性なし（2月は逆に黒字+$104）。90日30件では統計的根拠不十分。** |
| **P22_TIME_EXIT_MIN=360（240→180min短縮）** | **L-28: hold_min分析の欠陥。途中でunreal<0→後にTP到達する件数を見落とし。TE 27→30件に増加、-$112悪化。** |
| **スキャル化（TP=0.003, SL=0.02）** | **L-29: add構造と根本的に競合。SL_FILLED 2→15件（avg-$53/件）で-$1,364悪化。スキャル化はMAX_ADDS=0か1が前提。** |

### Phase 1 棚卸し結果（2026-04-05）

**削除済みデッドコード:**
| 対象 | 理由 |
|------|------|
| `MIDTERM_CUT` (P4 LONG add≥2) | MAX_ADDS_BY_PRIORITY["4"]=1 で不到達。現時点で無貢献。 |
| `MAE_CUT` (P23 SHORT add≥4) | MAX_ADDS_BY_PRIORITY["23"]=1 で不到達。同上。 |
| `BREAKOUT_CUT` P23分岐 | 同上。P22分岐は残存（SHORT_MAX_ADDS=5で到達可能） |
| config: `P4_TP_MULT` / `LONG_TP_WEAK_REDUCE` / `LONG_SHALLOW_TAIL_MIN` | コード内に参照なし |

**可視化済み:**
| 対象 | 対処 |
|------|------|
| `P22_SHORT_MFE_STALE_GATE_USD` | configに明示追加（従来は暗黙デフォルト12.0） |

**残存孤立パラメータ:** なし（2026-04-05 全件整理済み）
- 削除済み: PRICE_HIT_TOL / LONG_SLOPE_THRESH / LONG_RSI_{PERIOD,SLOPE_N,THRESH} / LONG_MIN_HOLD_FOR_RSI_EXIT / LONG_MIDTERM_{HOLD_MIN,PNL_USD} / SHORT_RISKSCORE_LOWER_THRESH（計9個）
- グレーゾーン残存: TP_ADX_FACTOR / TP_ADX_RANGE（BOOST=0で無効。再有効化時のため保留）

**現在の有効フィルター一覧:**
- P4: pullback + trend + slope(≥20/mean5≥15) + 陽線 + entry_ok + RSI_MAX(60) + ATR14(150) + ADX_EXCL(20-25)
- P2: stoch_GC(gap>0.3) + 陽線 + ADX(≥30) + RSI(≥45) + ATR14(150)
- P22: core_gate + bb_mid_slope(≤-50) ※ADX/RISKはRELAX_FINAL=1でバイパス
- P23: stoch_DC(gap>0.3) + 陰線 + bb_mid_slope(<-10) + ADX(30〜40) + ATR14(150)
- P24: RSI(>65) + rsi_slope(<0) + bb_slope(<50) + stoch_k(>60) + 陰線 + ATR14(150)

### Phase 2 進捗（2026-04-05 セッション）

**P22_SHORT_BB_MID_SLOPE_MAX 最適化（採用済み: -20）:**

フィルター段階別分析（180d=51,845バー）:
- core_gate 単独: 14,583バー（28%）→ bb_mid_slope≤-50 で **39バーに激減（99.7%除外）**
- slope≤-30: 222バー / slope≤-20: 543バー / slope≤-10: 1,522バー

テスト結果（90d Replay）:

| 閾値 | P22件数 | P22 NET | 全体NET | 全体差分 |
|------|--------|--------|--------|---------|
| -50（旧） | 8 | +$18 | +$896 | baseline |
| -30 | 41 | +$69 | +$908 | +$12 |
| **-20（採用）** | **87** | **+$205** | **+$1,020** | **+$124** |
| -10 | 201 | -$582 | +$258 | -$638（MFE_STALE_CUT急増で崩壊） |

※ -10崩壊原因: bb_slope緩い信号が長時間塩漬け → MFE_STALE_CUT 19件/$-982 急増
※ SHORT間 Priority 相互作用あり: P22増加→P23/P24が若干減少（P22がSHORT信号を先取り）

**P24 分析結果（完了・保留）:**
- コア信号自体が稀（0.51%）+ bb_slope<50 が55%除外
- 全ATR14閾値でTP維持率80%未満 → Entry filter不適
- 17件 NET -$10 ≈ フラット。Phase 3+4の自然対象として保留。

**P2/P4 LONG側分析結果（完了・打ち止め）:**
- P2: ATR14フィルター不効果（TIME_EXITのatr_14が逆に高い: add=2 avg232/add=3 avg292）。ret_5フィルターも改善なし。add≥2 TE 21件/$-641は設計上の代償（add深→大TP利益のトレードオフ）
- P4: 時間帯（18-19h・21h JST）除外で +$69 / TP維持率94.5% / 外科的3.75 だが18件サンプルで統計不十分 → 保留
- 結論: LONG側のEntryフィルター改善余地なし。Phase 3+4へ移行。

**180dデータ作成:**
- `/cat-swing-sniper/data/BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv` を作成済み
- Nov-Dec 2025 は history-candles API（v2）で取得
- Oct-Dec 2025 は BTC 強上昇レジーム（$65k→$100k）→ 現行パラメータと別レジーム・参考程度

### 今セッションの追加知見（2026-04-05）

- **TP_PCT 削減は全候補で NET 悪化（不採用）**:
  シミュレーション（add=1 ADX精度保証）で確認。
  - nom=0.004（実効0.44%）: -$150 / nom=0.003（実効0.33%）: -$374
  - 理由: TP_FILLED 174件の利益減 > TIME_EXIT 転換30件の利益。TIME_EXIT の62%はMFE<0.2%でTP変更では救えない。
- **実効TP = nominal × CLAMP scale**（TP_PCT_SCALE=1.1 / TP_PCT_SCALE_HIGH=1.2）:
  LONG_TP_PCT=0.005 → 実効 **0.55%**（ADX<35）/ **0.60%**（ADX≥35）
- **P4_TP_MULT=1.05 はデッドコード**: config に存在するが replay/run_once どこにも使われていない（無効）
- **add_count 別 TP_FILLED avg net**: add=1: $9.6 / add=2: $20.4 / add=3: $27.1 / add=4: $37.7
  → addが積み上がるほどTP価格が現値に近づき、かつ USD 利益が増える（設計の根幹）
- **TP / ADD / TIME_EXIT は相互作用が複雑**（TP幅広→TIME_EXIT増→add深損失増）
  → Phase 3+4 は同時最適化が必要（グリッドサーチ方式）

### 今セッション追加知見（2026-04-05 夜セッション）

- **時間帯除外は統計的に弱い**: UTC 3h (-$81.5) は月別一貫性なし（2月は+$104）。90日30件では不十分。
- **ATR帯別構造**: ATR<250でTP率50%、TE率40%。ATR>=250でTP率71%+。構造的な問題でTIME_EXIT調整では解決できない。
- **P22 TIME_EXIT短縮の限界（L-28）**: hold_min分析は途中の含み損状態を見えない。P22はシミュレーション精度が特に低い。
- **スキャル化はadd構造と非互換（L-29）**: TP=0.003+SL=0.02でSL_FILLED 2→15件(-$796)急増。add深いとSL損失が倍増する。スキャル化するならMAX_ADDS=0-1が前提。
- **TIME_EXITのadverse moveとTP利益が同程度（≈0.55%）**: SL=2%はTE（median 0.59%逆行）を捕捉できない。SL有効化には≤0.5%が必要だがTP全件巻き添えになる。

### 次セッション以降のフェーズ構成

※ 本番投入基準: **Replay NET $100/day 以上**（現在 +$20.3/day のため本番投入不可）

| Phase | 内容 | 状態 |
|-------|------|------|
| **Phase 1** | 全Priority Entry/Exit ロジック棚卸し（フィルター発火確認・デッドコード除去） | **完了** |
| **Phase 2** | Entry ロジック最適化（Priority間相互作用を考慮） | **← 次のタスク** |
| **Phase 3+4** | Add構造 × TP/TimeExit/SL 同時最適化（グリッドサーチ: TP_PCT × MAX_ADDS） | **LONG側完了・SHORT側未着手** |
| **Phase 5** | スケールアップ（ETH/SOL 追加） | 未着手 |

### 次セッション候補（優先度順）

1. **ポジションサイズ増加検討**: 現行 $20.3/day → $100/day は約5倍。0.024→0.12 BTCへの段階的スケールアップ（リスク管理要検討）
2. **Phase 2 Entry最適化残り**: P22 bb_mid_slope 下限調整（-20より緩めた場合の検証）
3. **P4 Entry 品質向上**: ADX 150-250帯でTP率34-51%。エントリー条件の再検討（L-19回避しながら）
4. **スキャル化（addなし版）**: MAX_ADDS=1 + TP=0.003 + SL=0.005 の純粋スキャルテスト（add構造を一時停止）

**Phase 3+4 LONG側グリッドサーチ結果（完了）:**

| | P4max=1 | P4max=2 | P4max=3 | P4max=4 | P4max=5 |
|---|---|---|---|---|---|
| TP=0.003 | $413 | $473 | $483 | $500 | $507 |
| TP=0.0035 | $750 | $836 | $851 | $900 | $918 |
| TP=0.004 | $501 | $556 | $566 | $606 | $626 |
| **TP=0.005（採用）** | **$1,020** | **$1,099** | **$1,124** | **$1,177** | **$1,200★** |
| TP=0.006 | $910 | $1,014 | $940 | $965 | $966 |
| TP=0.007 | $839 | $847 | $867 | $895 | $911 |

→ TP=0.005 / P4max=5 が最良。採用済み。

**Phase 3+4 SHORT側グリッドサーチ（次セッション）:**

SHORT_TP グリッド結果（LONG_TP=0.005固定 / SHORT adds上限=5）:

| SHORT_TP | NET | /day | P22 | P23 | P24 |
|---|---|---|---|---|---|
| 0.003 | $892 | $9.9 | $27 | -$14 | -$136 |
| 0.0035 | $1,009 | $11.2 | $47 | $62 | -$115 |
| 0.004 | $1,162 | $12.9 | $118 | $115 | -$85 |
| **0.005** | **$1,345** | **$14.9** | $177 | $215 | -$63 ◀現行 |
| 0.006 | $1,297 | $14.4 | $189 | $182 | -$90 |
| 0.007 | $1,436 | $16.0 | $67 | **$406** | -$52 |

**分析知見（2026-04-05）:**
- **P23 TP=0.007 $406 は異常値ではない**: add=5+TP拡大の相乗効果。TP件数44件/$1,021（avg $23.2/件 vs 0.005時 $9.8/件）。add積み上がりでTP価格が現値に近づきUSD利益増大。
- **P22 は TP=0.007 で崩壊**: TP率 53%→39%、BREAKOUT_CUT 出現。TP幅が広すぎてP22では届かない。
- **P24 は全TP値で赤字**: add解放しても TIME_EXIT 損失（avg -$44.9/件）が支配的。add=1 維持が適切。
- **結論: P22/P23/P24 は同一 TP での一括最適化は不適切。Priority別に分離最適化が必要。**

**Priority別TP最適化 完了（2026-04-05）:**
- P22_TP_PCT=0.005 / P23_TP_PCT=0.007 / P24_TP_PCT=0.007 に確定（adds=5 前提で再検証）
- P22は0.005が最良。P23=0.007で+$104、P24=0.007で+$44（P22相互作用込み）
- 組み合わせ確認Replay: NET $1,493（+$149改善）
- Priority別TP は replay_csv.py / run_once_v9.py / cat_params_v9.json に実装済み
- P24 は全TP値で赤字継続（TIME_EXIT支配的）→ 抜本的な構造変更なしには改善困難

**デッドパラメータ整理 完了（2026-04-05）:**
- 9個削除: PRICE_HIT_TOL / LONG_SLOPE_THRESH / LONG_RSI_{PERIOD,SLOPE_N,THRESH} / LONG_MIN_HOLD_FOR_RSI_EXIT / LONG_MIDTERM_{HOLD_MIN,PNL_USD} / SHORT_RISKSCORE_LOWER_THRESH
- 107個 → 89個に削減
- MAX_ADDS_BY_PRIORITY に P22/P23/P24=5 を明示追加（旧: SHORT_MAX_ADDS=5 暗黙フォールバック）

**集計出力拡充 完了（2026-04-05）:**
- replay_csv.py に [TP_FILLED × add_count 詳細] を追加（勝ち構造の可視化）
- add=1: avgNET $10.5 / add=2: $21.6 / add=3: $29.6 / add=4: $37.8 / add=5: $51.0

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

  【TIME_EXIT の MFE 分析（必須）】
  TIME_EXIT を「出口の問題」として扱う前に、MFE で原因を分類する。

  ```
  TIME_EXIT 全件について保有中の最大有利方向（MFE）を計算:
    MFE < 0.2%（逆行グループ）: エントリー直後から逆行 → 出口を変えても救えない。エントリー品質の問題。
    MFE >= 0.2%（届かずグループ）: 有利に動いたが TP に届かなかった → TP幅・TIME_EXIT_MIN の問題。
  ```

  — 逆行グループ（MFE<0.2%）が多い場合: Entry指標の分布を TP_FILLED と比較して「負け環境」を特定する
  — 届かずグループ（MFE>=0.2%）が多い場合: TP幅縮小・TIME_EXIT_MIN 延長を検討する
  — TP_PCT を変える前に必ずこの分類を行う（MFE分析なしでの TP幅変更は当てずっぽう）

  【逆行グループの Entry指標比較】
  逆行グループ（TE_bad）と TP_FILLED で各指標の平均を比較する。
  差が大きい指標が「負け環境の識別子」になる。
  atr_14 は14本平均のため signal/fill バーズレ（L-26）が小さく、Entry フィルターとして信頼性が高い。

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
