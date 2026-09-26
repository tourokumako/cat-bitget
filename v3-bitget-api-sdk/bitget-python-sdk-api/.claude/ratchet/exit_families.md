<!-- EXIT_FAMILIES hash=12dcb1b4e431502e gen_exit_families.py が自動生成＝手で書き換えない -->
# exit_families.md — 出口の枝の表（許可の一覧・全自動生成・CC の手書きの行ゼロ）

作り＝gen_exit_families.py（全自動生成・CC の手書きの md はゼロ・まこさん指示 2026-08-07『X-a〜X-kから自動生成して』『お前は手書きはするな』）

## 出どころ（全部 機械で読む）

| 何を | どこから |
|---|---|
| axes | entry_exit_matrix.md の共通 Exit ロジック軸 X-a〜X-k（軸カタログ＝正本） |
| capability | engine_tuner_exec.py の実物（AST で機械抽出） |
| reasons | score.py の MAKER_EXIT_REASONS／TAKER_EXIT_REASONS（H13） |
| v9 | v9_exits.md（replay_csv.py から機械生成・検算の既知答え） |
| materials | signal_families.json（入口の型の表＝確認条件の材料と禁止3 を共有） |
| grids | recipes/search_limits.json（まこさん承認 2026-08-01） |

## 集計＝軸 11 本 ／ 選択肢 79 個 ／ 枝の型 19 種（指値 maker 14 種・成行 taker 5 種）

| 選択肢の状態 | 数 |
|---|---|
| 組める | 31 |
| この工程の担当でない | 19 |
| 組めない | 14 |
| 一部だけ組める | 7 |
| 別の仕組みで持っている | 7 |
| この市場に当てはまらない | 1 |

## 実行器が実際に受けられるもの（engine_tuner_exec.py から機械抽出）

- 置き場所（価格の決め方）: mix、pct、peak_giveback、shrink、swing、zone、zone_sl
- 発注の方式: maker、taker、post_only、stop（登録済みだが実行不能＝iceberg、twap、vwap）
- 玉の状態の列: unreal_pct、mfe_pct、mfe_prev_pct、mae_pct、peak_age_bars、hold_min、add_count、dist_be_pct、trend_caught
- ★実装で値が入らない列（使わない）: peak_age_bars
- 枝を当てる玉の絞り: adds、ceil_type、hold_min、trend_caught
- 恒等検収レーン専用（探索では使えない）: position_exits、trend_caught

## 決済の名前（score.py が正本＝執行はここから機械で決まる）

- 指値 maker: BE_EXIT、CENTER_LOCK、EDGE_TP、INDICATOR_REVERSE_TP、MFE_DRAWDOWN_CUT、MFE_EXIT、PARTIAL_TP、SL_FILLED、TP_FILLED、TRAIL_EXIT、TREND_CAUGHT_TP
- 成行 taker: BOX_BREAK_SL、BREAKOUT_CUT、DYING_CUT、FORCE_CLOSE_EOD、HOLD_MOM_EXIT、MAE_CUT、MFE_STALE_CUT、ML_STANCH、PROFIT_LOCK、RANGE_BREAK_EXIT、RSI_REVERSE_EXIT、SPIKE_SL、STOCH_REVERSE_EXIT、STRUCT_SL、TIME_EXIT、TREND_CONT

## 枝の型（この表が許可するもの）

| 枝 | 何をするか | 決済の名前 | 執行 | 置き場所 | 発火の条件 | 値の格子 |
|---|---|---|---|---|---|---|
| TP_ZONE_MID | 利確＝レンジ中央に指値 | TP_FILLED | maker（指値） | zone | なし（常に置く） | — |
| TP_ZONE_OPP | 利確＝反対側ゾーンまで伸ばす（届かない時は中央へ戻す） | TP_FILLED | maker（指値） | zone | なし（常に置く） | state_mult_grid |
| TP_PCT | 利確＝建値から固定%（手数料床の倍数）に指値 | TP_FILLED | maker（指値） | pct | なし（常に置く） | state_mult_grid |
| TP_SWING | 利確＝直近M本の押し安値・戻り高値の手前に指値（届かない時は元の置き方へ戻す） | TP_FILLED | maker（指値） | swing | なし（常に置く） | int_grid、state_mult_grid |
| TP1_LADDER | 部分利確＝建値と利確の間を刻んで指値（1〜2段） | PARTIAL_TP | maker（指値） | mix | なし（常に置く） | frac_grid、ladder_steps_grid |
| SHRINK | 利確＝残り時間の比で建値側へ縮む指値（時間切れの前に置き直す） | TP_FILLED | maker（指値） | shrink | なし（常に置く） | int_grid |
| PEAKLOCK | 含み益のピークから戻したら、利益を残す位置に指値（追従＋利益の下限） | MFE_DRAWDOWN_CUT | maker（指値） | peak_giveback | なし（常に置く） | giveback_grid、state_mult_grid |
| BEEXIT | 同値撤退＝一度 利が乗った後、建値+手数料床に指値 | BE_EXIT | maker（指値） | pct | mfe_prev_pct を見る | state_mult_grid |
| BESTALE | 停滞・失速の撤退＝時間が経っても利が乗らない玉を、建値フロアの指値で降りる | BE_EXIT | maker（指値） | pct | hold_min を見る／mfe_prev_pct を見る | hold_frac_grid、state_mult_grid |
| MFEEXIT | 長く持った玉の利確＝利確に届かないまま満期が近い玉を、手前の位置で確定する | MFE_EXIT | maker（指値） | mix | hold_min を見る／mfe_prev_pct を見る | frac_grid、hold_frac_grid、state_mult_grid |
| REVERSE_IND | 指標の反転で利確＝反転を検知したら利益側に指値（材料は型の表の部品から選ぶ） | INDICATOR_REVERSE_TP | maker（指値） | pct | 指標（型の表の部品）／unreal_pct を見る | state_mult_grid |
| SL_ZONE | 損切り＝レンジの帯の外に指値（帯の取り方3種・倍率つき） | SL_FILLED | maker（指値） | zone_sl | なし（常に置く） | exit_mult_grid |
| SL_PCT | 損切り＝建値から固定%に指値 | SL_FILLED | maker（指値） | pct | なし（常に置く） | exit_mult_grid |
| SL_SWING | 損切り＝直近M本の高安の外に指値 | SL_FILLED | maker（指値） | swing | なし（常に置く） | int_grid、state_mult_grid |
| TIME | 時間切れ＝保有の上限で成行 | TIME_EXIT | taker（成行） | on_close | hold_min を見る | hold_bars_from_role |
| TIME_DOWN | 時間切れの前倒し＝含み損の玉だけ満期を短くして成行（勝ちは満期まで） | TIME_EXIT | taker（成行） | on_close | hold_min を見る／unreal_pct を見る | hold_frac_grid |
| BREAKOUT | 前提崩れ＝レンジが壊れたら成行で降りる | BREAKOUT_CUT | taker（成行） | on_close | 指標（型の表の部品） | — |
| FINSTOP | 資金防衛＝1トレードの含み損が線に達したら無条件で成行 | MAE_CUT | taker（成行） | on_close | unreal_pct を見る | loss_cap_grid |
| MAECUT_ADDS | 積み増した玉の損切り＝積み増し回数が一定以上で、時間が経っても含み損なら成行 | MAE_CUT | taker（成行） | on_close | hold_min を見る／unreal_pct を見る | hold_frac_grid、max_adds_grid |

## どの枝にも足せる確認の条件（0〜2本）

規則: どの枝にも、確認の条件を 0〜2本 足せる。材料は入口の型の表の部品だけ（禁止3 も同じ）。閾値は分位。向きは『出口＝入口の逆』で機械が決める（入口の向きの決まり DC1〜DC4 を逆向きに適用）
材料＝入口の型の表の部品 573 種 × 時間足 11 本 ／ 閾値＝分位 **範囲 q10〜q90**（`quantile_range`） ／ 標本不足の禁止 515 組も同じように効く

## 軸カタログ X-a〜X-k の選択肢 全部（1つずつ・出典つき）

### X-a TP 固定目標

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-a1 | 固定 %/pip/dollar | 組める | TP_PCT、SL_PCT | 実行器 _check_level の pct（base=entry/avg・k は定数×格子） |
| X-a2 | R:R 固定（1:2/1:3） | 一部だけ組める | 比率そのものを置き場所にする受け皿は無い。下限の担保は入口の門（entry_guards の r_min＝リスクリワード比の下限 0.25・まこさん承認 2026-08-01）で行う | 実行器 _guards_ok（969行）／search_limits.json の r_min |
| X-a3 | レンジ中央 SMA/中央線 | 組める | TP_ZONE_MID | 実行器 _check_level の zone target=mid |
| X-a4 | 反対ゾーン（サポート側）まで伸ばす | 組める | TP_ZONE_OPP、TP_SWING | 実行器 _check_level の zone target=opp と swing（直近の高安＝構造線） |
| X-a5 | 固定σ幅 | 組めない | 実行器に、その置き場所（価格の決め方）の受け皿が無い | 実行器 _check_level に σ 幅の水準が無い（zone/zone_sl/mix/pct/shrink/swing の6種のみ） |
| X-a6 | VWAP 回帰 | 一部だけ組める | VWAP を置き場所にする受け皿は無い。VWAP からの乖離（close vs VWAP%）は確認条件の材料としては使える | 実行器 _check_level に VWAP の水準が無い／型の表に close vs VWAP%288 が在る |
| X-a7 | bracket order | 別の仕組みで持っている | bracket＝TP と SL を同時に置く発注の形。枝を複数持てば同じことになる（X-k7 と同じ） | 実行器は exits を配列で持ち、上から先勝ちで評価する（1295行） |

### X-b TP 段階決済 scale-out

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-b1 | 部分決済（例 中央35%/1.5σ35%/反転30%） | 組める | TP1_LADDER | 実行器 _check_level の mix ＋ size_ratio（0,1] |
| X-b2 | profit target ladder（段階利確） | 組める | TP1_LADDER（段数は ladder_steps_grid（1〜2）で振る。合計の size_ratio が 1 を超えない） | 同上／E37 v16 実測＝ladder の rung 幾何は 0 発火で不採択＝段数と位置を格子で振り直す残件 |
| X-b3 | pyramiding exit | この工程の担当でない | 積み増した玉の段階決済＝玉の持ち方（要件 R14）の残件。D2（出口の枝）では扱わない | 要件 R14（設計をまこさんに提出中） |
| X-b4 | 複数TP（最大20個・Bitget） | 別の仕組みで持っている | 複数TP＝X-b1／X-b2 と同じ（枝を複数持てる） | 実行器の exits 配列 |

### X-c トレーリング

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-c1 | %トレーリング | 組める | PEAKLOCK | 実行器 _peak_giveback_level（ピークからの戻し％） |
| X-c2 | ATR トレーリング（Chandelier） | 組めない | 実行器に、その置き場所（価格の決め方）の受け皿が無い | 実行器の peak_giveback は建値比%で動く＝ATR 連動（Chandelier）の水準を作る受け皿が無い |
| X-c3 | Parabolic SAR | 組めない | 型の表の部品に、その材料の列が無い | 型の表の部品に Parabolic SAR が無い（observe_diag のカタログに無い） |
| X-c4 | high-water mark | 組める | PEAKLOCK（high-water mark＝含み益のピーク基準＝peak_giveback そのもの） | 実行器 _peak_giveback_level（pk_prev＝前バーまでのピーク） |
| X-c5 | ボラ連動トレーリング（利益で 0.25-0.40% へ締める） | 組めない | 実行器に、その置き場所（価格の決め方）の受け皿が無い | X-c2 と同じ＝ボラに連動して締める受け皿が無い |

### X-d SL

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-d1 | 固定 % | 組める | SL_PCT | 実行器 _check_level の pct |
| X-d2 | ゾーンすぐ外・浅い構造線 | 組める | SL_ZONE（帯の取り方 w=zone/inner が浅い側） | 実行器 _check_level の zone_sl（w＝range/zone/inner） |
| X-d3 | **遠い Chan 型＝深SL・時間切れ主体**（L-323＝平均回帰に浅SLは逆効果） | 組める | SL_ZONE（帯の取り方 w=range ＋ 倍率を大きく＝深い側） | 同上／L-323＝平均回帰に浅SLは逆効果 |
| X-d4 | SLなし＝レンジ破れ/前提崩れ検知でのみ撤退（KB §5） | 組める | FINSTOP、BREAKOUT（SL の枝を持たない案＝資金防衛の枝（risk=loss_cap）が必須。前提崩れの枝で降りる） | 実行器 validate_recipe の G4（SL 系か loss_cap のどちらかが必須・554行） |
| X-d5 | ATR×k 倍 | 組めない | 実行器に、その置き場所（価格の決め方）の受け皿が無い | ATR×k の水準を作る受け皿が無い（ATR% は確認条件の材料としては使える） |
| X-d6 | swing 高安の外 | 組める | SL_SWING | 実行器 _check_level の swing |
| X-d7 | MAE stop | 組める | FINSTOP、MAECUT_ADDS | 実行器の状態列 mae_pct／unreal_pct（1051行） |
| X-d8 | acceleration SL（早期カット） | 組めない | 実行器に、その置き場所（価格の決め方）の受け皿が無い | 加速度（値動きの速さ）の水準を作る受け皿が無い |
| X-d9 | ±3σ | 組めない | 実行器に、その置き場所（価格の決め方）の受け皿が無い | X-a5 と同じ＝σ 幅の水準が無い |
| X-d10 | 建値撤退（含み損戻りで損ゼロ maker・E35 iter4） | 組める | BEEXIT | 実行器の pct（base=avg）＋状態列 mfe_prev_pct／E35 iter4 実績 |
| X-d11 | **1トレード最大許容損失＝フィナンシャルストップ**（資金比%で機械的に切る・予算0.12の合計capとは別の1トレード軸・2026-07-30 まこさん提示の出口11軸⑤との照合で欠けを発見・追加） | 組める | FINSTOP（線の値（含み損の%）はまこさんが決める＝loss_cap_grid） | 軸 X-d11 の逐語／実行器 G4 の risk=loss_cap |

### X-e 含み益管理

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-e1 | break-even（建値へ SL 移動） | 組める | BEEXIT | 同 X-d10（建値へ戻して降りる＝同じ枝） |
| X-e2 | profit lock（利益固定） | 組める | PEAKLOCK（利益の固定＝peak_giveback の floor（下限）が受け持つ） | 実行器 _peak_giveback_level の floor／V9 PROFIT_LOCK（v9_exits.md 枝12〜15） |
| X-e3 | MFE-based（含み益ピーク基準） | 組める | PEAKLOCK、MFEEXIT | 実行器の状態列 mfe_prev_pct／v9_exits.md 枝2・6 |
| X-e4 | MFE stale（含み益が伸びない検知） | 組める | BESTALE | v9_exits.md 枝3〜5（MFE_STALE_CUT）・枝16〜17（STAGNATION_CUT） |

### X-f 時間切れ・前提崩れ

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-f1 | 固定時間/バー数 成行 taker | 組める | TIME、TIME_DOWN | 実行器の状態列 hold_min／保有の上限は役割から（要件 R6） |
| X-f2 | **deadline shrink＝残り時間比で建値側 maker 化**（E35 iter8-9・E37 v13） | 組める | SHRINK | 実行器 _check_level の shrink（v13 deadline shrink・S1 の書き写し） |
| X-f3 | レンジ破れ（出来高∩境界外終値）で早期撤退 | 組める | BREAKOUT（V9 の BREAKOUT_CUT と同族（BB幅 ∩ RSI）。v15 の形（出来高∩ゾーン外終値∩1h持続）は実行器のハードコードで恒等レーン専用＝探索では組めない） | 実行器 validate_recipe の position_exits の門（lane != legacy で拒否・377行） |
| X-f4 | market close/曜日 exit | この市場に当てはまらない | BTC 無期限先物は24時間365日で市場の引け・週末またぎが無い。E37/E38 の FORCE_CLOSE_EOD はデータの最終バーの記録処理（e37_scalp.py 1564行・1646行）で戦略の枝ではない | exchange_spec.md（定期メンテなし・24/7 取引）／e37_scalp.py の実測 |
| X-f5 | なし | 別の仕組みで持っている | 枝を持たない＝枝の有無そのものが探索の対象（要件 R13） | 要件 R13 の逐語（枝の有無と順番が探索の対象になること） |
| X-f6 | **外部イベント回避**（FOMC/CPI/雇用統計の発表前に手仕舞い・発表時刻の過去データの入手はまこさんと相談・2026-07-30 まこさん提示の出口11軸⑪との照合で欠けを発見・追加） | 組めない | そのデータが無い | 軸 X-f6 の逐語／型の表の部品に指標発表の列が無い |

### X-g 指標反転・構造・ボラ・出来高・統計 Exit

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-g1 | RSI/Stoch/MACD reversal | 組める | REVERSE_IND（RSI・Stoch は型の表に在る。MACD は材料の組み立てが未対応（複合パラメータ＝FAMILY_TEMPLATES に無い）） | 実行器 FAMILY_TEMPLATES（MACD 系が無い＝G6 生成不可）／型の表のオシレーター24種 |
| X-g2 | BBタッチ | 組める | REVERSE_IND（BB%b・BB幅の水準として組む） | 型の表のオシレーター（BB%b 4種）・ボラ（BB幅 4種） |
| X-g3 | EMA cross | 組める | REVERSE_IND（close vs EMA% の水準・EMA傾き%・cross の形で組む） | 型の表のトレンド16種（close vs EMA/傾き）／実行器の形 cross |
| X-g4 | ADX decay | 組める | REVERSE_IND、BREAKOUT（ADX の水準・傾きで組む） | 型の表のトレンド（ADX7/14/21） |
| X-g5 | pivot反転 | 組める | REVERSE_IND（close vs pivotPP/R1/S1% の水準で組む） | 型の表の構造・位置（close vs pivotPP%288 ほか） |
| X-g6 | trendline-channel break | 一部だけ組める | トレンドラインの列は無い。チャネル破れに近いものは Donchian幅%・close vs 24/48/96本高値% で組む（同じものではないと明示） | 型の表の構造・位置とボラ（Donchian幅%20/48） |
| X-g7 | vol expansion-contraction | 組める | BREAKOUT、REVERSE_IND（ボラの拡大・縮小＝BB幅・ATR%・realized_vol の水準と傾き） | 型の表のボラ11種 |
| X-g8 | volume spike-divergence | 一部だけ組める | 出来高スパイクは volume_ratio で組める。ダイバージェンス（価格と出来高の逆行）は形の一覧に無い | 型の表の出来高5種／実行器の形11種にダイバージェンスが無い |
| X-g9 | order-flow reversal | 組めない | 型の表の部品に、その材料の列が無い | 型の表 signal_families.json の lineage_of の集計（2026-08-07 実測） |
| X-g10 | z-score reversion（統計的平均回帰閾値） | 組める | REVERSE_IND（zscore20/50・zscore_return20/50 の水準で組む） | 型の表のオシレーター（zscore 系4種） |
| X-g11 | **ローソク形状反転**（pinbar・包み足・ダブルトップ等の確定足の形で決済＝入口側 E-c のローソクの出口版・2026-07-30 まこさん提示の出口11軸③との照合で欠けを発見・追加） | 組めない | 実行器が、出口の発火条件でその形を扱えない（材料の無い形は評価できない） | 実行器 _exit_fire_ok を実物に呼んで確認（2026-08-07）＝出口の発火条件で扱えるのは材料のある形だけ。ローソクの向き（材料の無い形）を渡すと『材料の3軸が欠けている』で止まる。ローソクの7部品は実行器 FAMILY_TEMPLATES に無く材料としても引けない＝入口では candle_dir 形で使えるが出口では使えない。使えるようにするには実行器の出口の評価を直す必要がある（D2 の範囲外＝別の回） |

### X-h ML Exit

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-h1 | Triple Barrier（Lopez de Prado） | この工程の担当でない | ML の Exit。engine_tuner は固定ルールを組み立てる道具＝ML の解禁はまこさんが決める | engine_tuner_requirements『この道具でやらないこと』／cat_requirements §8.5 |
| X-h2 | meta-labeling | この工程の担当でない | — | 同 X-h1 |
| X-h3 | 強化学習 terminal policy | この工程の担当でない | — | 同 X-h1 |
| X-h4 | exit value prediction | この工程の担当でない | — | 同 X-h1 |

### X-i add / ピラミッディング

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-i1 | なし単発 | 別の仕組みで持っている | 積み増し無し＝position.max_adds=1（既に格子で振っている） | 生成器 sample_structure の position（max_adds_grid） |
| X-i2 | 順張りピラミッド（Turtle 逓減・N=20 ATR） | この工程の担当でない | 積み増しの入れ方＝要件 R14 の残件（add_trigger は resignal のみ実装） | 要件 R14／実行器 validate_recipe の add_trigger 4種（565行） |
| X-i3 | Martingale | この工程の担当でない | — | 同 X-i2 |
| X-i4 | Anti-Martingale | この工程の担当でない | — | 同 X-i2 |
| X-i5 | 予測強度依存 | この工程の担当でない | 予測強度＝ML の出力が要る（工程の対象外） | 同 X-h1 |
| X-i6 | Kelly fractional | この工程の担当でない | — | 同 X-i2 |
| X-i7 | vol-targeted | この工程の担当でない | — | 同 X-i2 |
| X-i8 | グリッド add | この工程の担当でない | グリッド売買の add＝S5/L5 のロジック側（grid_n の範囲がまこさん判断待ち） | next_step §6 の6番（grid_n の探索範囲） |
| X-i9 | add トリガ（逆行幅/時間経過/指標再発火/含み益確認） | 一部だけ組める | 実装済みは再発火（resignal）のみ。逆行幅・時間経過・含み益確認の3種は受け皿は在るが生成器が出していない＝R14 の残件 | 実行器 validate_recipe（565行＝resignal/adverse_pct/time/profit_confirm の4種を受ける） |

### X-j サイジング

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-j1 | 一律 | 別の仕組みで持っている | 枝ごとの決済の量＝size_ratio（0,1] で持つ | 実行器 validate_recipe の size_ratio（537行） |
| X-j2 | remaining÷n | この工程の担当でない | 建てる量の配分＝統合の段（全戦略で 0.12 BTC を取り合う） | cat_requirements §6.1／pdca_flow §6.1 |
| X-j3 | 予測強度比例 | この工程の担当でない | — | 同 X-j2（かつ予測強度＝ML） |
| X-j4 | Kelly（fractional 0.25-0.5） | この工程の担当でない | — | 同 X-j2 |
| X-j5 | risk parity | この工程の担当でない | — | 同 X-j2 |
| X-j6 | vol-targeting（ATR反比例） | この工程の担当でない | — | 同 X-j2 |
| X-j7 | cluster別固定 | この工程の担当でない | — | 同 X-j2 |
| X-j8 | 過去パフォーマンス重み（合計0.12 BTC 厳守） | この工程の担当でない | — | 同 X-j2 |

### X-k 決済方式

| # | 選択肢（軸カタログの逐語） | 状態 | 枝／理由 | 出典 |
|---|---|---|---|---|
| X-k1 | 成行 taker | 組める | 成行＝能動クローズの枝だけ（時間切れ・前提崩れ・資金防衛）。執行は決済理由から機械で決まる | score.py の TAKER_EXIT_REASONS／H5（成行 taker は能動クローズのみ） |
| X-k2 | 指値 maker | 組める | 指値＝出口の既定。maker の決済理由の枝は全部これ | score.py の MAKER_EXIT_REASONS／cat_requirements §6（手数料負け回避＝maker 優先） |
| X-k3 | post-only maker | 一部だけ組める | 実行器は post_only を受けるが、出口の枝の執行は maker/taker の2択で扱う（入口の執行は実行器の固定＝H5） | 実行器 EXEC_METHODS（maker/taker/post_only/stop） |
| X-k4 | stop（緊急SL taker） | 一部だけ組める | 実行器は stop を受けるが、score.py の理由の分類（maker/taker）と1対1にならない＝いまは使わない | 実行器 EXEC_METHODS／score.py の分類 |
| X-k5 | stop-limit maker | 組めない | 実行器が、その発注の方式を実行できない（登録済みでも拒否側） | 実行器 EXEC_METHODS に stop-limit が無い |
| X-k6 | trailing-stop | 別の仕組みで持っている | 追従＝PEAKLOCK（指値で追従する形） | 実行器 _peak_giveback_level |
| X-k7 | OCO（TP+SL 同時） | 別の仕組みで持っている | TP と SL を同時に置く＝枝を複数持てば同じ（上から先勝ち） | 実行器の exits 配列（1295行） |
| X-k8 | iceberg | 組めない | 実行器が、その発注の方式を実行できない（登録済みでも拒否側） | 実行器 EXEC_REGISTERED_ONLY（登録済みだが実行不能＝拒否側・CP3 Q1） |
| X-k9 | TWAP | 組めない | 実行器が、その発注の方式を実行できない（登録済みでも拒否側） | 同 X-k8 |
| X-k10 | VWAP（§6.7＝方向を当てない戦略は maker が生命線） | 組めない | 実行器が、その発注の方式を実行できない（登録済みでも拒否側） | 同 X-k8 |

## V9 の枝との検算（機械生成の v9_exits.md が正本）

| V9 の枝 | 受け手の枝の型 |
|---|---|
| BREAKOUT_CUT | BREAKOUT |
| MAE_CUT | FINSTOP、MAECUT_ADDS |
| MFE_DRAWDOWN_CUT | PEAKLOCK |
| MFE_EXIT | MFEEXIT |
| MFE_STALE_CUT | BESTALE |
| PROFIT_LOCK | PEAKLOCK |
| RSI_REVERSE_EXIT | REVERSE_IND |
| STAGNATION_CUT | BESTALE |
| STOCH_REVERSE_EXIT | REVERSE_IND |
| TIME_EXIT | TIME、TIME_DOWN |

## 値待ち（まこさんが決める・決まるまでその枝は生成できない）

- なし

## 承認

- 指紋: None（まこさんの承認の指紋が入るまで、この表は無効（D2 の実装に進めない））
