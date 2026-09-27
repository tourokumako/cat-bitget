<!-- ARC iter="m2e4e-r6-moving-line-20260927" -->

# 設計書｜M2-E-4e＝法則 R6 の「BB幅 は直近6か月の範囲の下の方」を、固定の線を残したまま「動く線」として段2c の候補に足す（新しい前処理の部品 ts_pos・窓つきの前処理の欄 pre_win）

TARGET: scripts/priority_rebuild/engine_tuner_exec.py, scripts/priority_rebuild/engine_tuner_gen.py, scripts/priority_rebuild/condition_parts_diag.py, .claude/ratchet/m2_stage_candidates.json, .claude/ratchet/condition_parts.json
NEW_FILE: .claude/breaks/b109_moving_line_not_built.sh, .claude/breaks/b110_ts_pos_in_random_draw.sh, .claude/breaks/b111_ts_pos_excludes_current.sh, .claude/breaks/b112_stage_warm_not_extended.sh
MODEL: .claude/breaks/b104_atr1h_own_tf.sh

REQUIREMENTS: まこさんの決定（下の §0）と、`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書はプログラムが作ります。**手で書いたのは、元データ `.claude/ratchet/acceptance_src.json` の5つ（何を作るか・なぜ作るか・組み方・やらないこと・決めてほしいこと）だけです。残りは正本から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --write`。手で書き換えられていないかの検出＝`--verify`。

## 0｜まこさんの決定（逐語）

> ★この工事への決定（逐語）
> ②と③はどちらもCCのおすすめ案でOK（2026-09-25＝法則 R6 の「小さい」は、固定の線を残したうえで、6か月で動く線も段2c の候補に足し、成績で engine_tuner に選ばせる。束1 ではやらない）
> この案でOK（2026-09-26＝M2-E-4e を束2 の後・M2-E-6 の前に足す）
> １，２どちらもOK（2026-09-27＝この設計書の読むもの宣言13件への OK）
> １，案A（2026-09-27＝動く線は BB幅 だけに付ける。six-month の逐語が付いているのは BB幅 の根拠の行だけ）
> ２，案①、新しい部品を1つ足す案（2026-09-27＝「6か月の範囲の下の方」は、直近6か月の最小と最大の間のどこにいるかを出す新しい部品で測る。ts_rank の順位ではない）
> OK（2026-09-27＝読むもの宣言に足す11件への OK）
> OK（2026-09-27＝設計の骨組み5つへの OK＝部品 ts_pos・乱数の道に入れない・窓は元データに6か月・BB幅 の固定の線と動く線の両方・作り直すもの）
> OK（2026-09-27＝読むもの宣言の25番 gen_s22_map.py への OK）
> 余白の直し方→C（2026-09-27＝データの前の余白が60日で、動く線の6か月に足りない件。動く線を使う走行だけ、余白を長くする）
> OK（2026-09-27＝読むもの宣言の26番・27番＝本走の口と WARM の定義への OK）
> ★前から引き継ぐ決定（逐語）
> 一旦この検索方法がベストということで記録しておいて（2026-09-01＝§2.2 レンジ判定の検索方法）
> じゃあ、まず１点でつくる（2026-09-11＝閾値の分位は1点）
> 乱数は禁止用語にするレベル。絶対に使うな（2026-09-09・恒久67番）
> お前が法則を決めるな（2026-09-09＝法則の中身は まこさんが決める。この工事は法則を1文字も変えない）
> ヌケモレがおおいから、手で書かざるを得ない部分以外は自動生成にしろよ。（2026-09-09・恒久69番）
> 2-Eと２−Fの進行が遅すぎるので、修正は極力まとめて効率的に進めること（2026-09-21）
> とにかく、不具合はすべて直すように（2026-08-21・恒久59番）
> コードを直したら、その行を探している壊すプログラムが在るかを、必ず grep（2026-09-16・L-605）

## 1｜概要

法則 R6（BB 幅の縮小は低ボラ＝レンジ寄り）の根拠の逐語「Ideally, BandWidth should be near the low end of its six-month range.」（StockCharts「Bollinger Band Squeeze」・regime_laws.json の R6）を、engine_tuner の段2c（3枠目）の候補に「動く線」として足します。いまの段2c の閾値は、値決め窓の分布から分位を1回だけ決めて固定する「固定の線」だけです（`build_qtable`＝rolling しない）。固定の線は残し、動く線を足して、どちらが良いかは成績で engine_tuner に選ばせます（まこさん決定 2026-09-25）。動く線は BB幅 だけに付けます（まこさん決定 2026-09-27「１，案A」）。そのために3つを作ります。1つ目は、前処理の部品 `ts_pos` です。直近 n本の最小と最大の間で、いまの値がどこにいるかを 0〜1 で出します（まこさん決定 2026-09-27「２，案①」）。式は Stochastic の %K と同じ形で、いまのバーを含め、未来は見ません。この部品には「入口の案を乱数で作る道では引かない」印（`gen_draw: False`）を付け、入口の案の作り方を1本も変えません（恒久67番）。2つ目は、§2.2 の元データ（m2_stage_candidates.json）の窓つきの前処理の欄 `pre_win` です。段2c の BB幅 の語に `{"op": "ts_pos", "months": 6}` を書きます。窓の月の数は逐語の six-month から取り、私は数字を作りません。3つ目は、組む側（`build_stage_candidates`）がこの欄を読み、BB幅 について固定の線の候補と同じ本数の動く線の候補を、固定の線の候補の後ろに並べる形です。前処理は実行データ（5分足）の並びに載った列に掛かるので、6か月は5分足の本数（52,596本）に直します。後ろに並べるので、固定の線の順位は1つも変わらず、束を組む側（順位で3枠目を取る）が作るいまの束も変わりません。動く線は6か月ぶんの過去が要りますが、engine_tuner が値決め窓の前に読む余白は60日（`engine_tuner.py` の `WARM`）です。このままでは値決め窓と確認窓の最初の約4か月、動く線が値なしになります。だから動く線を使う走行（組む側の本走 `run_main`）だけ、余白を「いまの余白＋いちばん長い窓（6か月）」にします（まこさん決定 2026-09-27「余白の直し方→C」）。恒等の走行・H2 など、ほかの走行の余白は今のまま変えません。あわせて、部品の正本（condition_parts.json）と突き合わせの道具（condition_parts_diag.py）に部品を1件ずつ足し、§2.2-0 の表に「動く線」を出し、材料の文書・G2・H2 を作り直します。売買は1件も回さないので、net は動きません。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

| 何を測ったか | コマンド | 結果 |
|---|---|---|
| 法則 R6 の根拠の逐語（窓の長さ） | `grep -c 'near the low end of its six-month range' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json` | 1（終了コード 0）／読み方＝逐語が在る。窓は六か月で、範囲の下の方を求める |
| いまの閾値の決め方 | `grep -n 'rolling しない' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 3777:    """解決表＝値決め窓の分布から分位→実値を1回だけ固定（rolling しない・§2.4-①）。""" ⏎ 4475:          f"（rolling しない・保存 {run_dir / 'qtable.json'}）")（終了コード 0）／読み方＝閾値は値決め窓の分布から一回だけ決めて固定する。直近の窓の中の位置ではない |
| 元データの前処理を読む所 | `grep -n 'if stage == "stage2a":' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 2893:        if stage == "stage2a":（終了コード 0）／読み方＝元データの前処理を読むのは段二aの分岐だけ。段二cには付ける道が無い |
| 元データに窓つきの前処理の欄が在るか | `grep -c 'pre_win' v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_stage_candidates.json` | 0（終了コード 1）／読み方＝零件。前処理の欄は部品の名前の文字だけで、窓の本数を書けない |
| 範囲の中の位置を出す部品が在るか | `grep -c '"ts_pos"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py` | 0（終了コード 1）／読み方＝零件。在るのは順位とばらつきと最大・最小で、範囲の中の位置は無い |
| 入口の案を乱数で作る道が引く部品の一覧 | `grep -n -F '_pre_opts = [None] + ex.pre_ops(same_unit=False)' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 1805:        _pre_opts = [None] + ex.pre_ops(same_unit=False)（終了コード 0）／読み方＝単位の変わる部品を全部 乱数で引く。新しい部品をそのまま足すと、乱数が引く相手が増える |
| 前処理が掛かる列の並び | `grep -n 'return _apply_pre(_col_array(df' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py` | 2058:        return _apply_pre(_col_array(df, {k: v for k, v in m.items() if k != "pre"}, geo, lane), pre, df)（終了コード 0）／読み方＝前処理は実行データの並びに載った列に掛かる。だから窓の本数は五分足の本数で数える |
| データの前の余白の長さ | `grep -n 'WARM = pd.Timedelta' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner.py` | 99:WARM = pd.Timedelta(days=60)                 # 助走（RG 168h＋rolling を満たす a-priori）（終了コード 0）／読み方＝余白は六十日。六か月の窓には足りないので、窓の最初の約四か月は動く線が値なしになる |
| 三枠目を取る決まり | `grep -n 'def regime_draw_order' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 2359:def regime_draw_order(n: int) -> tuple[int, int, int, str]:（終了コード 0）／読み方＝三枠目は案の番号から決まる順位で取る。一覧の後ろに足せば、いまの順位の束は変わらない |
| 直す行を探している壊すプログラム（L-605） | `grep -rln -e 'pre_ops(' -e 'ts_std' -e '_PRE_PARTS' -e 'build_stage_candidates' -e 'stage_candidates(' -e 'expand_stage' -e '_pre_opts' -e '_lv_ops' -e 'lins_law' -e 'alphagen:Std' -e 'NO_ARG_OPS' -e 'et.WARM' -e 'load_windows_cached' -e '実行が未実装' -e 'T36: 途中' -e 'rolling(int(n)).std' .claude/breaks` | .claude/breaks/b78_law_literal.sh ⏎ .claude/breaks/b92_stage2_no_drop_tfs.sh ⏎ .claude/breaks/b93_law_filter_off.sh ⏎ .claude/breaks/b98_qkey_abs_missing.sh ⏎ .claude/breaks/b79_param_drawn.sh ⏎ .claude/breaks/b82_abs_missing.sh（終了コード 0）／読み方＝当たる壊すプログラムが探す行は、どれもこの工事で消さない（足すのは別の行の後ろ） |
| 直すファイルに commit されていない差の塊の数 | `git diff HEAD -- v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/condition_parts_diag.py v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_stage_candidates.json v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/condition_parts.json .claude/tools/gen_regime_kb.py ／ grep -c '^@@'` | 0（終了コード 1）／読み方＝承認の前は差が無い。照合が数える触った関数は、この工事で直すものだけになる |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

<!-- ACC_MATERIALS_START hash=ba987a5abd7ee17e gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 141種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・fib位置・POC・VAH・VAL・MMI・S-Rタッチ1時間ATR・S-Rタッチ数・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
```

**別枠の材料**

| 別枠 | 印がオンのもの |
|---|---|
| レンジ幾何 | W%・帯内位置% |
| 需給 | CVD・L-S比・taker_ls |
| 時間帯 | 時刻・曜日 |

**役割ごとに使える系統と時間足（型の表）**

| 役割 | 系統 | 時間足 | レンジ幾何 |
|---|---|---|---|
| env | トレンド・ボラ・時間帯 | 全部 | — |
| location | 構造・位置 | 全部 | 使う |
| sufficiency | ボラ・出来高・需給・オシレーター | 全部 | — |
| trigger | オシレーター・ローソク | 5m・10m・15m | — |

**値の範囲と格子（承認済み・この工事で数字を1つも作らない）**

| 鍵 | 中身 |
|---|---|
| `quantile_grid` | ["q10", "q20", "q30", "q40", "q50", "q60", "q70", "q80", "q90"] |
| `quantile_range` | {"lo": 10, "hi": 90, "kind": "int"} |
| `int_grid` | [3, 6, 12, 24] |
| `int_range` | {"lo": 3, "hi": 24} |
| `state_hold_bars_range` | {"lo": 24, "hi": 288, "kind": "int"} |
| `nest_offset_range` | {"lo": 0, "hi": 1, "kind": "int"} |
| `ref_mult_range` | {"lo": 0.5, "hi": 1.5, "kind": "float", "dec": 2} |
| `hour_range` | {"lo": 6, "hi": 18, "kind": "int"} |
| `material_param_ranges` | （空＝材料カタログの最小〜最大を使う） |

<!-- ACC_MATERIALS_END -->

### 2-3 成績表に載っている本数

<!-- ACC_RANKING_START hash=31b989fc34f0fa0c gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`material_ranking.json`。

**成績表に載っている列の本数**（札＝強さ・先読み24・執行足より上の時間足だけ）

| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |
|---|---|---|
| env | 1918 | MMI500__1d（0.639）／PWMA20傾き%__1d（0.595）／kurtosis50__1d（0.405） |
| location | 1414 | close vs TSF%20__1d（0.429）／close vs TEMA%20__1d（0.434）／close vs LINREG%20__1d（0.435） |
| sufficiency | 1528 | MMI500__1d（0.639）／kurtosis50__1d（0.405）／MAD比50__1d（0.592） |
| trigger | 250 | TD_SEQ_DN__10m（0.473）／TD_SEQ_DN__15m（0.484）／HT_LEADSINE__10m（0.514） |

**★この本数は、印がオンの指標だけを数えたものではありません。**組む側は `ranked_materials` を通して引き、その関数が印オフの指標を落とします。

<!-- ACC_RANKING_END -->

### 2-4 いま乱数を使っている場所

<!-- ACC_RANDOM_START hash=b77eb360eebdb373 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`engine_tuner_gen.py` を構文の木で読んだ結果（コメントの中の文字は数えません）。

**乱数を使っている関数＝21個 ／ 使っている回数の合計＝64**

| 関数 | 回数 |
|---|---|
| `_make_exits` | 17 |
| `sample_structure` | 7 |
| `synth_df` | 6 |
| `_exit_indicator_cond` | 4 |
| `_make_cond` | 4 |
| `_pair_materials` | 4 |
| `_pick_material` | 3 |
| `_loose_q` | 2 |
| `_pick_exit_material` | 2 |
| `_thr_band_drawn` | 2 |
| `draw_num` | 2 |
| `draw_param` | 2 |
| `_dc1_side` | 1 |
| `_iv` | 1 |
| `_iv_from` | 1 |
| `_mat_drawn` | 1 |
| `_nv` | 1 |
| `_thr_drawn` | 1 |
| `draw_int` | 1 |
| `draw_q` | 1 |
| `write_kakikudashi` | 1 |

**★この工事で0にするのは、場面の判定の束を組む所だけです。**入口は M3、出口は M4 で外します（まこさんが決めた順番）。

<!-- ACC_RANDOM_END -->

## 3｜目標と、やらないこと

### 3-1 やらないこと（1件ずつ・理由と出どころ）

| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | 動く線を BB幅 以外（SQZ_ON・Donchian幅・ATR%・realized_vol・stdev%）に付けること | six-month の逐語が付いているのは BB幅 の根拠の行だけ。ほかの指標に窓を当てはめると、法則に無い窓を私が作ることになる | まこさん決定 2026-09-27「１，案A」 |
| 2 | 法則 R10（ATR% の自分の平均との比較）に動く線を付けること | 監査 CP39 の問い2 は R6 と R10 を並べたが、まこさんの決定は R6 だけ | まこさん決定 2026-09-25（worklog 20260925 §6-2 の②） |
| 3 | 「Bollinger BandWidth」のページの「an eight- to 12-month chart」を窓にすること | 決定は six-month（Squeeze のページの逐語）。別の長さを候補に足すと、まこさんの決定より広げることになる | まこさん決定 2026-09-25・worklog 20260927 §5-9 |
| 4 | 既存の部品 `ts_rank` で「範囲の下の方」を測ること | 順位は範囲の中の位置ではない | まこさん決定 2026-09-27「２，案①」 |
| 5 | 動く線の閾値の分位を、固定の線と別の点にすること | 閾値は「まず1点」。段2c の分位を §2.2 の範囲（下位15〜40%）に合わせるかは、束2 の決めてほしいこと2 と同じ件で まこさんが決める | まこさん決定 2026-09-11「じゃあ、まず１点でつくる」 |
| 6 | 入口の案を作る乱数の道で、新しい部品を引くこと | 乱数の道を広げない。入口の乱数を外すのは M3 そのもの | 恒久67番 |
| 7 | 元データの前処理の欄 `pre`（いつも掛ける）の形を変えること | 段2a の abs が使う形で、変えると束1 までの守り（b82）に触れる。窓つきは別の欄 `pre_win` にする | 恒久69番・L-605 |
| 8 | 窓の本数を範囲で探すこと（6か月の前後の月を候補に足すこと） | 窓の長さは逐語の six-month の1つ。範囲で探すかは段5（詰め）の工事で扱う | §2.2 の段5・恒久42番 |
| 9 | 成績表・型の表・印を作り直すこと | 部品の一覧（前処理）はそれらに読まれない。段2c の候補は成績表の列（前処理なし）から作り、前処理は候補の材料に付けるだけ | worklog 20260927 §5-7 の2 |
| 10 | データの前の余白 `engine_tuner.WARM`（60日）を、全部の走行で延ばすこと（余白の直し方の案A） | 恒等の走行・H2 ほかの余白まで変わり、長い記憶の指標の値が変わって、直す前と後で結果が同じかの確かめが崩れうる | まこさん決定 2026-09-27「余白の直し方→C」 |
| 11 | M2-F で段を測る道具（`regime_r9_diag.py`）の余白を、この工事で延ばすこと | その道具を直すのは M2-F-2 の設計書（1変更＝regime_r9_diag.py）。この工事は `stage_warm` を作り、組む側の本走で使うところまで。M2-F-13 で動く線を測る前に、M2-F-2 で同じ形にする（やることリストに書く） | next_step §0-2 の10番・cat_requirements §4.6 の H16 |
| 12 | m2_todo.json の M2-F-13 の注意（「213本・5種」）と束1 の3件の状態の欄を、この工事で直すこと | 記録の段（ToDo の記録）で直す。コードの工事の実装の指示に混ぜない | worklog 20260927 §4-5・§5-3 |

### 3-2 決めてほしいこと

| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 動く線の閾値の分位。いまは固定の線と同じ q50 の1点（「直近6か月の範囲の真ん中より下」）です。§2.2 の段2c は「分位＝下位15〜40%・刻み5」と書きますが、段2c の分位を範囲の中の点にするかは、束2 の決めてほしいこと2 と同じ件です。★M2-F-13（段2c を測る）の前に決める必要があります | この工事では変えない（まず1点のまま）。M2-F-13 の前に、束2 の決めてほしいこと2 と一緒に決めていただく | milestones2 の764行・まこさん決定 2026-09-11「じゃあ、まず１点でつくる」・束2 の設計書の決めてほしいこと2 |

## 4｜設計の中身

**★この節の項目は、正本 `design_section_sources.json` の3つの出どころ（うちの正本・外の標準・まこさんが過去に指摘したこと）118件を、1件も余さず引き受ける形に決めたものです。**割り当て＝`design_section_map.json`。検算＝`gen_design_sections.py --check`。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

**この項目に書くこと**＝何を作るのか／どういう流れで動くのか／何ができるようになるのか／完成したとき何が出るのか。★項目に分けない。ここだけ読めば全体が分かる状態にする。★★必ず「なぜこの形にするのか」を、ほかの形と比べた実測の数字で書く（この形を取らなかったら何通り・何時間 掛かるか）。★なぜ必須か＝まこさん指摘 2026-09-10「2-2の設計思想は、総当りで組合わせロジックを出すと数百年かかるので、段ごとに絞り込んでいくという方法ということを、このセッション内で何度も言ってるのに、毎回抜けるから、いい加減にしてほしい」。私は「段＝枠を埋める順番」と読み、「段＝候補を絞る段階」という思想を毎回 落とした。

**この仕組みは、法則 R6 の「BB幅 は直近6か月の範囲の下の方」を、段2c の候補に「動く線」として足すものです。**いまの固定の線（値決め窓で1回だけ決めた分位）は残し、動く線を足して、どちらが良いかは成績で engine_tuner に選ばせます（まこさん決定 2026-09-25）。

**①いま何が起きているか。**段2c（3枠目・R2・R6・R10）の候補は 261本・6種です（§2.2-0 の表）。閾値は全部、値決め窓の分布から分位を1回だけ決めた固定の線です（`build_qtable` の説明「rolling しない」）。法則 R6 の根拠の逐語は「直近6か月の範囲の中で下の方」＝直近の窓の中の位置を求めていますが、いまの engine_tuner にはその形の候補がありません。元データの前処理の欄（`pre`）は部品の名前の文字だけで窓の本数を書けず、読むのも段2a だけです（監査 CP39 の A6-b）。

**②どう変えるか。**前処理の部品 `ts_pos`（直近 n本の最小〜最大の間の、いまの値の位置・0〜1）を実行器に足します。元データの段2c の BB幅 の語に、窓つきの前処理の欄 `pre_win`＝`{"op": "ts_pos", "months": 6}` を書きます。組む側は、この欄を持つ指標について、固定の線の候補と同じ材料・同じ側・同じ閾値の分位で、材料に `ts_pos`（窓＝6か月を5分足の本数に直した 52,596本）を付けた候補を作り、固定の線の候補の後ろに並べます。

**③なぜこの形か（ほかの形と比べて）。**「範囲の下の方」は、範囲（最小〜最大）の中の位置です（まこさん決定「２，案①」）。既にある `ts_rank`（直近 n本の中の順位）は順位で、範囲の中の位置ではありません。`ts_pos` の式は StockCharts の Stochastic の %K「%K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100」と同じ形で、×100 をしない 0〜1 にします。動く線を付けるのは BB幅 だけです（まこさん決定「１，案A」＝six-month の逐語が付いているのは BB幅 の根拠の行だけ）。

**④乱数の道を広げない。**入口の案を作る関数 `_make_cond` は、単位の変わる部品を乱数で1つ引きます（`_pre_opts = [None] + ex.pre_ops(same_unit=False)`）。新しい部品をそのまま足すと、乱数が引く相手が増えます（恒久67番）。だから部品の性質に `gen_draw: False` を付け、`pre_ops` に絞り `gen_draw` を足し、入口の案の道は `gen_draw=True` の部品だけを引きます。入口の案の作り方は1本も変わりません。

**⑤データの前の余白。**engine_tuner は値決め窓の前に余白 60日（`engine_tuner.py` の `WARM`「助走（RG 168h＋rolling を満たす a-priori）」）を読みます。動く線は6か月の過去が要るので、このままでは値決め窓と確認窓の最初の約4か月が値なしになり、固定の線と同じ条件で比べられません。まこさん決定 2026-09-27「余白の直し方→C」で、動く線を使う走行（組む側の本走 `run_main`）だけ、余白を「いまの余白＋いちばん長い窓」（60日＋182.625日）にします（`stage_warm`）。いまの余白を足すのは、窓の最初の1本の材料にも指標の助走が要るためです。恒等の走行・H2・ほかの道具は `WARM` のまま変わりません。M2-F で段を測る道具（`regime_r9_diag.py`）は M2-F-2 の工事で同じ形にします。

**完成したときに出るもの。**`engine_tuner_gen.py --selftest` の T47 の行（①部品は乱数の道の外 ②既知答え ③段2c の動く線の本数・窓・並び ⑤動く線を使う走行の余白）。§2.2-0 の表の段2c の BB幅 の行の前処理の欄に `ts_pos（6か月・動く線）`。段2c の候補の本数が BB幅 の固定の線の本数だけ増えます。売買は1件も回さないので、net は動きません。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

**この項目に書くこと**＝このプログラムを呼ぶ相手（人か、別のプログラムか）と、出た結果を次に使う相手。やること／やらないことの線。

**誰が動かすか。**組む側（`engine_tuner_gen.py` の `build_stage_candidates`）が、§2.2 の元データ（`stage_candidates` → `gen_regime_kb.expand_stage`）を読んで段2c の候補を作ります。束を組む側（`sample_regime_build`）と §2.2-0 の表（`gen_regime_kb.py --write stage`）と段を数える口（`stage_counts`）が、同じ `build_stage_candidates` を呼びます。

**誰が結果を使うか。**段ごとに測る道具（M2-F-13＝段2c を測る）が、この一覧の候補を全部 測ります。束を組む側は順位で3枠目を取ります。動く線の材料の閾値は、分位の解決表（`build_qtable`）が前処理を掛けた値の分布から決め、実行器（`engine_tuner_exec._col_array` → `_apply_pre`）が同じ式で計算します。

**線。**直すのは、前処理の部品の一覧と式（実行器）・部品を引く一覧の絞り（実行器の `pre_ops` と組む側の2か所）・段の候補の元データの読み方と段2c の候補の作り方（組む側）・元データの照らしと表（`gen_regime_kb.py`）・元データ（`m2_stage_candidates.json`）・部品の正本（`condition_parts.json`）・突き合わせの道具（`condition_parts_diag.py`）です。法則・審判・売買のロジック・成績表・型の表・印・範囲の置き場は触りません。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

**この項目に書くこと**＝関数やコマンドの取り決め（引数・戻り値・その意味・呼んでよい相手）。

**受け取るもの（部品 `ts_pos`）。**材料の列（実行データの並び・5分足）と、窓の本数 n（2 以上の整数）。

**出すもの（部品 `ts_pos`）。**バーごとに（いまの値 − 直近 n本の最小）÷（直近 n本の最大 − 直近 n本の最小）。直近 n本はいまのバーを含めます。最初の n−1本と、幅が0の所と、値の無い所は値なし（NaN）です。

**元データの欄（`pre_win`）。**`{"op": 前処理の名前, "months": 窓の月の数}` の2つだけ。`expand_stage` が、名前が前処理の一覧に在るか・月の数が1以上の整数かを照らします（合わなければ止まる）。

**段2c の動く線の候補。**鍵は固定の線の候補と同じ11個＋`pre_win`。材料だけが `{…, "pre": {"op": "ts_pos", "n": 52596}}` になります。側と閾値の分位は固定の線と同じです。

**番人が出すもの。**`engine_tuner_gen.py --selftest` の T47 の行と、落ちたときの `❌ T47: …` の行。

### 4-6 制約（従う決まりの全件と、その出どころ）

**この項目に書くこと**＝決まりを1件も落とさずに並べ、どれをどの工程で使うかを書く。動かせないもの（承認済みの設定・取引所の仕様）も。

| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 固定の線を残したうえで、6か月で動く線も候補に足し、成績で選ばせる | まこさん決定 2026-09-25「②と③はどちらもCCのおすすめ案でOK」 | 固定の線の候補は1本も消さず、動く線を後ろに足す。どちらを選ぶかは M2-F が測る |
| 動く線は BB幅 だけ | まこさん決定 2026-09-27「１，案A」 | 元データの `pre_win` は段2c の BB幅 の語だけに書く |
| 範囲の下の方は、最小〜最大の間の位置で測る | まこさん決定 2026-09-27「２，案①」 | 新しい部品 `ts_pos`（Stochastic の %K と同じ形・0〜1） |
| 窓の長さは逐語から取る | 法則 R6 の根拠の逐語 six-month・恒久42番 | 元データに `months: 6`。5分足の本数へは式で直す（1か月＝365.25÷12日・5分足＝要件 H7） |
| 乱数を使わない・乱数の道を広げない | 恒久67番 | 部品に `gen_draw: False`。入口の案の道は `pre_ops(same_unit=False, gen_draw=True)` だけを引く。番人 T47 の①と壊すプログラム b110 |
| 未来のデータを使わない | cat_requirements §4.6 の H2 | rolling の最小・最大は過去 n本だけ。T47 の既知答えと H2（`leak_causality_diag.py`）で測る |
| 値段に依存しない | cat_requirements §4.6 の H6 | 位置は 0〜1 の比。BB幅 自体も割合 |
| 同じ判定を2か所に書かない | 恒久69番 | 窓の本数の計算は `pre_win_bars` の1か所。部品の式は実行器の `_apply_pre` の1か所（突き合わせの道具の独立の実装は照らす相手） |
| 法則を決めない | まこさん 2026-09-09「お前が法則を決めるな」 | 法則ファイルは1文字も変えない。R6 の読みは まこさんの決定のとおり |
| 1変更 | cat_requirements §4.6 の H16 | 「段2c の BB幅 に動く線を足す」の1つ。部品・欄・候補の作り方はその1つを作る部品 |
| コードを直したら、その行を探す壊すプログラムを grep | L-605 | 当たった b78・b79・b82・b92・b93 が探す行は消さない（なぜ作るかの10行目） |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

**この項目に書くこと**＝主要な部品を挙げ、それぞれが何に責任を持つかを書く。部品どうしの協調も。

| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| `engine_tuner_exec.MATERIAL_PRE` の `ts_pos` | 部品の性質（単位が変わる・乱数の道で引かない） | **新設**（実装の指示 1） |
| `engine_tuner_exec.pre_ops` | 絞り `gen_draw` を足す（既定 None は今までどおり全部） | 直す（実装の指示 2・3） |
| `engine_tuner_exec._apply_pre` | `ts_pos` の式 | 直す（実装の指示 4） |
| `engine_tuner_gen._make_cond` | 入口の案の道は `gen_draw=True` の部品だけを引く | 直す（実装の指示 5） |
| `engine_tuner_gen.stage_candidates` | 元データの `pre_win` を渡す | 直す（実装の指示 7） |
| `engine_tuner_gen.pre_win_bars` | 窓の月の数を5分足の本数に直す | **新設**（実装の指示 8） |
| `engine_tuner_gen.stage_warm` | 元データに窓つきの前処理が在れば、データの前の余白を「いまの余白＋いちばん長い窓」にする | **新設**（実装の指示 8） |
| `engine_tuner_gen.run_main` | 本走のデータを `stage_warm(et.WARM)` の余白で読む | 直す（実装の指示 27） |
| `b112_stage_warm_not_extended.sh` | 余白を延ばさないと T47 が落ちることを測る | **新設**（実装の指示 28） |
| `engine_tuner_gen.build_stage_candidates` | `pre_win` を持つ指標に動く線の候補を作り、固定の線の後ろに並べる | 直す（実装の指示 9・10・11） |
| `engine_tuner_gen.selftest` の T1-C6e と T47 | 案を作る道の部品の一覧を見る（T1-C6e）／動く線の番人（T47） | 直す（実装の指示 6）・**新設**（実装の指示 12） |
| `condition_parts_diag.p_ts_pos`・`_PRE_PARTS`・`_cases` | 実行器を使わない独立の実装と、突き合わせの見本1つ | **新設**・直す（実装の指示 13〜15） |
| `m2_stage_candidates.json` | 段2c の BB幅 の `pre_win` と、その欄の説明 | 直す（実装の指示 16・17） |
| `condition_parts.json` の "have" | 部品 `ts_pos` の正本の行 | 直す（実装の指示 23） |
| `.claude/tools/gen_regime_kb.py` の `expand_stage`・`build_stage` | `pre_win` を読み・照らし・表に出す | 直す（実装の指示 18〜22・私が Edit ツールで書く） |
| `b109_moving_line_not_built.sh` | 動く線を作らないと T47 が落ちることを測る | **新設**（実装の指示 24） |
| `b110_ts_pos_in_random_draw.sh` | 部品を乱数の道に入れると T47 が落ちることを測る | **新設**（実装の指示 25） |
| `b111_ts_pos_excludes_current.sh` | 部品の式からいまのバーを外すと T47 が落ちることを測る | **新設**（実装の指示 26） |

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

**この項目に書くこと**＝工程の順番と、工程の間で何を渡すか。組み方の根拠（何の法則で決めるか）も。

1. 当てる道具（`apply_audit_fix.py --design`）で実装の指示 1〜17・23・27 を当て、実装の指示 18〜22（`gen_regime_kb.py`）を Edit ツールで書き、壊すプログラム4本（実装の指示 24〜26・28）を Write ツールで書きます。
2. `py_compile` で直した .py の構文を確かめ、`gen_regime_kb.py --write stage`（§2.2-0 の表）と `--selftest` を走らせます。
3. `engine_tuner_exec.py --selftest` を走らせます。
4. `engine_tuner_gen.py --selftest` を走らせ、T47 の行を見ます。
5. `condition_parts_diag.py`（突き合わせ）を走らせ、食い違い 0 を見ます。
6. `gen_materials.py --write`（前処理の一覧の数が 8 → 9）と `--verify`・`--selftest` を走らせます。
7. 型の表を作り直しても変わらないことを確かめます（型の表を作る道具は部品の一覧を読まない＝`gen_signal_families.py --verify` が通る）。変わったら止まって まこさんに出します。
8. G2（`gen_signal_families.py --verify`）→ H2（`leak_causality_diag.py`）の順で検査済みの記録を取り直します（実行器と組む側を触るので失効する）。
9. 直す前と後で結果が同じか確かめる3本の走行（S2・L1・S1）を走らせます。
10. 完成の条件の表の全部のコマンドを走らせ、2回目の承認をお願いします。
11. `python3 .claude/tools/pre_audit_check.py --run` と `--verify` を走らせ（組む側と実行器の指紋が変わるため。ORDER の型の表と出口の表の `--write` は、部品の一覧を読まないので要らない）、「監査に出せます」が出てから実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

**この項目に書くこと**＝実際の1件が、入口から出口までどう通るか。★読み手が設計を確かめられる唯一の欄。

**通しの例（T47 の既知答え・窓 5本）。**数字は私が式から手で計算した値です（走らせた結果ではない）。

1. **データ。**値の並び＝1・2・3・4・5・3・3・3・3・3（10本）。
2. **5本目（値 5）。**直近5本＝1〜5。最小 1・最大 5 なので (5−1)÷(5−1)＝1.0。
3. **6本目（値 3）。**直近5本＝2・3・4・5・3。最小 2・最大 5 なので (3−2)÷3＝約 0.333。
4. **7〜9本目（値 3）。**最小 3・最大 5 なので 0.0（範囲のいちばん下）。
5. **10本目（値 3）。**直近5本が全部 3＝幅 0 なので値なし。
6. **いまのバーを外すと（壊すプログラム b111）。**5本目の最小が「直前5本（まだ4本しか無い）」になり値なし＝期待の 1.0 と違うので T47 の②が落ちます。
7. **本物の窓。**6か月＝6 × 365.25 ÷ 12 ＝ 182.625日。5分足は1日 288本なので 52,596本。段2c の BB幅 の動く線の材料は `{"op": "ts_pos", "n": 52596}` です。
8. **余白。**組む側の本走は、値決め窓の開始 2024-03-01 の「60日＋182.625日」前（2023-07-02 09:00）からデータを読みます。2024-03-01 のバーの直近6か月の窓の最初のバー（2023-09-01 ごろ）にも、60日の助走が在ります。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

**この項目に書くこと**＝工程ごとに、使う材料（指標）・時間足・閾値の格子・パラメータの範囲・候補の本数。

**窓の長さの出どころと、この工事で扱う値。**

| 値 | 中身 | 出どころ |
|---|---|---|
| 窓の月の数 | 6 | 法則 R6 の根拠の逐語「Ideally, BandWidth should be near the low end of its six-month range.」（StockCharts「Bollinger Band Squeeze」の本文を 2026-09-27 に開いた・worklog 20260927 §5-9） |
| 1か月の日数 | 365.25 ÷ 12 | 暦の平均（私の計算の決まり。月の数は作らない） |
| 実行データの足 | 5分 | 要件 cat_requirements §4.6 の H7「5m が現行標準」・実行データ（5分足の正本） |
| 窓の本数 | 52,596本 | 上の3つの掛け算（`pre_win_bars`） |
| 動く線の閾値 | 固定の線と同じ分位の1点 | まこさん決定 2026-09-11「じゃあ、まず１点でつくる」。★§2.2 の段2c の範囲（下位15〜40%）と合わせるかは、束2 の決めてほしいこと2 と同じ件（M2-F-13 の前に決める） |

**下の囲みは、§2.2 の段の表をプログラムがそのまま写したものです。**

<!-- ACC_STAGES_START hash=059ce7a3c2b6c72f gen_acceptance.py が自動生成＝手で書き換えない -->
**★この表はプログラムが作ります（手で書き換えない）。**出どころ＝`engine_tuner_milestones2.md` の §2.2（レンジ判定の検索方法）を、`gen_s22_map.py` の抽出関数で読んだもの。**私は1文字も足していません。**

| 段 | 何を選ぶ枠か | 使う法則 | 材料（指標の系統）と時間足 | 値の範囲 |
|---|---|---|---|---|
| **段0** | 0 準備 | — | ①候補×材料の突き合わせ表 ②1列・1組の時間の実測（3分超の段だけ「帯の形→付帯」に分割・差し戻しで拾い直す）③範囲の案を設計書へ | — |
| **段1** | 帯 | R1・R3・R7 | 帯タイプ7系統（レンジ幾何 W%・帯内位置%／S-Rタッチ数／pivot 3種／n本高安／close vs EMA%・SMA%・Keltner／POC・VAH・VAL／転換線・基準線）×時間足8本（10m〜1d） | S-R 窓144〜288・許容幅0.0015〜0.006／高安20〜96本／タッチ2〜4／幅の床0.08%×2〜6倍／余白0〜20%刻み5 |
| **段2a** | 強さの否定 | R5・C1 | ADX・CHOP・ER・VHF・MACDヒスト%・EMA傾き・DI差の絶対値。時間足は上位足（15m〜4h） | ADX 12〜28刻み2（期間は既定14・段5で開く）／CHOP 55〜70刻み3×期間7〜21／分位型は下位20〜50% |
| **段2b** | 向きの否定 | R8 | `rg5_uptrend` の not（承認済みの借用）。自前の向きは M2-M | — |
| **段2c** | 3枠目 | R2・R6・R10 | ばらつき（BB幅・ATR%・realized_vol・Donchian幅・stdev%）／出来高（volume_ratio・CMF ほか）／位置・形（BB%b と0.5の差・経過バー）／時刻。「なし」を必ず併走。段2a の系統は不可（C2）・動きが重なる組は落とす（C3） | 分位＝下位15〜40%刻み5／volume_ratio 0.5〜1.8／CMF 0.05〜0.15／差0.2〜0.35／経過10〜40本 |
| **段3** | 持続 | R4・C6・C7 | 成立の連続本数と解除の緩め幅。5分足で数える | n＝`state_hold_bars_range` の範囲／緩め幅＝`_loose_q` の分位差 |
| **段4** | 4 差し戻し | — | 確定した束に全候補を1枠ずつ入れ直して1周（列はキャッシュ再利用） | — |
| **段5** | 5 詰め | — | 勝った値の前後を細かく。勝った指標だけ期間を範囲から開く（カタログ外の期間も列を作る）。判定は最良値でなく形（前後で崩れる束は落とす） | 閾値は刻み1・分位は刻み半分／線＝`neighbor_drop_max`（まこさんの判断待ち） |
| **段§2.2** | §2.2 の語 | — | 正本を探す文字 | 当て方 |
| **段レンジ幾何** | レンジ幾何 W%・帯内位置% | — | `レンジ幾何` | 完全 |
| **段S-Rタッチ数** | S-Rタッチ数 | — | `S-Rタッチ数` | 完全 |
| **段pivot** | pivot 3種 | — | `pivot` | 前方 |
| **段n本高安（高値の側）** | n本高安 | 高値の側 | `n本高` | 前方 |
| **段n本高安（安値の側）** | n本高安 | 安値の側 | `n本安` | 前方 |
| **段close** | close vs EMA% | — | `close vs EMA` | 完全 |
| **段SMA%** | SMA% | — | `close vs SMA` | 完全 |
| **段Keltner** | Keltner | — | `Keltner` | 前方 |
| **段POC** | POC | — | `POC` | 完全 |
| **段VAH** | VAH | — | `VAH` | 完全 |
| **段VAL** | VAL | — | `VAL` | 完全 |
| **段指標** | 指標 | — | 候補の本数 |  |
| **段`S-Rタッチ1時間ATR`** | `S-Rタッチ1時間ATR` | — | 22 |  |
| **段`S-Rタッチ数`** | `S-Rタッチ数` | — | 22 |  |
| **段`pivotR1`** | `pivotR1` | — | 18 |  |
| **段`n本高値`** | `n本高値` | — | 34 |  |
| **段`n本安値`** | `n本安値` | — | 34 |  |
| **段`close** | `close vs ACCBU%` | — | 42 |  |
| **段`pivotS1`** | `pivotS1` | — | 18 |  |
| **段`ABER位置`** | `ABER位置` | — | 42 |  |
| **段`Keltner上`** | `Keltner上` | — | 36 |  |
| **段`安値からの経過バー`** | `安値からの経過バー` | — | 33 |  |
| **段`close** | `close vs SAREXT%` | — | 42 |  |
| **段`close** | `close vs HWMA%` | — | 42 |  |
| **段`HWC位置`** | `HWC位置` | — | 42 |  |
| **段`close** | `close vs MMAR%` | — | 40 |  |
| **段`close** | `close vs PSAR%` | — | 42 |  |
| **段`VAH`** | `VAH` | — | 18 |  |
| **段`close** | `close vs HILO%` | — | 42 |  |
| **段`close** | `close vs ABER_ZG%` | — | 42 |  |
| **段`close** | `close vs ACCBL%` | — | 42 |  |
| **段`close** | `close vs CKSPl%` | — | 42 |  |
| **段`close** | `close vs PMAX%` | — | 42 |  |
| **段`close** | `close vs EMA` | — | 34 |  |
| **段`fractal高値距離%`** | `fractal高値距離%` | — | 42 |  |
| **段`close** | `close vs CE_L%` | — | 42 |  |
| **段`close** | `close vs RAINBOW%` | — | 42 |  |
| **段`close** | `close vs FAMA%` | — | 42 |  |
| **段`HT_DCPHASE`** | `HT_DCPHASE` | — | 42 |  |
| **段`close** | `close vs FWMA%` | — | 36 |  |
| **段`close** | `close vs HT_TRENDLINE%` | — | 42 |  |
| **段`close** | `close vs MAMA%` | — | 42 |  |
| **段`fractal安値距離%`** | `fractal安値距離%` | — | 42 |  |
| **段`close** | `close vs CE_S%` | — | 42 |  |
| **段`close** | `close vs CKSPs%` | — | 42 |  |
| **段`close** | `close vs KAMA%` | — | 30 |  |
| **段`構造破断距離%`** | `構造破断距離%` | — | 42 |  |
| **段`高値からの経過バー`** | `高値からの経過バー` | — | 34 |  |
| **段`close** | `close vs MEDIAN%` | — | 32 |  |
| **段`close** | `close vs VIDYA%` | — | 30 |  |
| **段`高値切り上げ幅%`** | `高値切り上げ幅%` | — | 42 |  |
| **段`close** | `close vs RMA%` | — | 32 |  |
| **段`close** | `close vs TRIMA%` | — | 36 |  |
| **段`close** | `close vs MCGD%` | — | 31 |  |
| **段`close** | `close vs SINWMA%` | — | 32 |  |
| **段`close** | `close vs SSF%` | — | 31 |  |
| **段`close** | `close vs SWMA%` | — | 32 |  |
| **段`close** | `close vs WMA%` | — | 32 |  |
| **段`Keltner下`** | `Keltner下` | — | 36 |  |
| **段`close** | `close vs VWMA%` | — | 32 |  |
| **段`close** | `close vs SMA` | — | 32 |  |
| **段`close** | `close vs VWAP` | — | 18 |  |
| **段`fib位置`** | `fib位置` | — | 33 |  |
| **段`close** | `close vs PWMA%` | — | 30 |  |
| **段`close** | `close vs T3%` | — | 30 |  |
| **段`close** | `close vs ALMA%` | — | 32 |  |
| **段`close** | `close vs LRb%` | — | 32 |  |
| **段`close** | `close vs MIDPRICE%` | — | 32 |  |
| **段`安値切り上げ幅%`** | `安値切り上げ幅%` | — | 42 |  |
| **段`close** | `close vs DEMA%` | — | 33 |  |
| **段`close** | `close vs JMA%` | — | 34 |  |
| **段`close** | `close vs LINREG%` | — | 34 |  |
| **段`close** | `close vs HMA%` | — | 32 |  |
| **段`close** | `close vs MIDPOINT%` | — | 32 |  |
| **段`close** | `close vs ZLMA%` | — | 34 |  |
| **段`close** | `close vs TSF%` | — | 33 |  |
| **段`pivotPP`** | `pivotPP` | — | 18 |  |
| **段`POC`** | `POC` | — | 18 |  |
| **段`close** | `close vs TEMA%` | — | 34 |  |
| **段`PSAR反転`** | `PSAR反転` | — | 42 |  |
| **段`VAL`** | `VAL` | — | 18 |  |
| **段`形スコア`** | `形スコア` | — | 36 |  |
| **段`SMC_SWEEP`** | `SMC_SWEEP` | — | 42 |  |
| **段`W字`** | `W字` | — | 35 |  |
| **段§2.2** | §2.2 の語 | — | 正本を探す文字 | 当て方 |
| **段ADX** | ADX | — | `ADX` | 完全 |
| **段CHOP** | CHOP | — | `CHOP` | 完全 |
| **段ER** | ER | — | `ER` | 完全 |
| **段VHF** | VHF | — | `VHF` | 完全 |
| **段MACDヒスト%** | MACDヒスト% | — | `MACDヒスト%` | 完全 |
| **段EMA傾き** | EMA傾き | — | `EMA傾き` | 完全 |
| **段DI差の絶対値** | DI差の絶対値 | — | `DI差` | 完全 |
| **段指標** | 指標 | — | 候補の本数 |  |
| **段`MACDヒスト%`** | `MACDヒスト%` | — | 12 |  |
| **段`ADX`** | `ADX` | — | 14 |  |
| **段`EMA傾き`** | `EMA傾き` | — | 10 |  |
| **段`ER`** | `ER` | — | 14 |  |
| **段`CHOP`** | `CHOP` | — | 13 |  |
| **段`DI差`** | `DI差` | — | 12 |  |
| **段`VHF`** | `VHF` | — | 14 |  |
| **段`MMI`** | `MMI` | — | 5 |  |
| **段§2.2** | §2.2 の語 | — | 正本を探す文字 | 当て方 |
| **段BB幅** | BB幅 | — | `BB幅` | 完全 |
| **段ATR%** | ATR% | — | `ATR%` | 完全 |
| **段realized_vol** | realized_vol | — | `realized_vol` | 完全 |
| **段Donchian幅** | Donchian幅 | — | `Donchian幅` | 完全 |
| **段stdev%** | stdev% | — | `stdev%` | 完全 |
| **段BB%b** | BB%b と0.5の差 | — | `BB%b` | 完全 |
| **段経過バー** | 経過バー | — | `経過バー` | 後方 |
| **段指標** | 指標 | — | 候補の本数 |  |
| **段`stdev%`** | `stdev%` | — | 42 |  |
| **段`BB幅`** | `BB幅` | — | 42 |  |
| **段`Donchian幅`** | `Donchian幅` | — | 42 |  |
| **段`realized_vol`** | `realized_vol` | — | 42 |  |
| **段`ATR%`** | `ATR%` | — | 45 |  |
| **段`SQZ_ON`** | `SQZ_ON` | — | 48 |  |

**段の件数＝125件**（§2.2 に在るものを1つも落としていません）。

<!-- ACC_STAGES_END -->

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

**この項目に書くこと**＝指定できる項目・その置き場・既定値・指定しなかったときの動き。

**設定ファイルは変えません。**窓の月の数は §2.2 の元データ（`m2_stage_candidates.json`）の `pre_win` に書きます。範囲の置き場（`search_limits.json`）は変えません。

**コマンドの旗は足しません。**番人 T47 は `engine_tuner_gen.py --selftest` の中で走ります。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

**この項目に書くこと**＝できあがったときに出てくるものの形。★4-17（走っている途中の表示）とは別。数字は機械の出力から出す（私が書かない）。

**完成したときに画面に出るもの。**①`engine_tuner_gen.py --selftest` の T47 の行（動く線の本数・BB幅 の固定の線の本数・窓 52596本）。②§2.2-0 の表の段2c の BB幅 の行の前処理の欄に `ts_pos（6か月・動く線）`、実際の候補の本数に動く線の分。③`condition_parts_diag.py` の「すべて … 1バーも違いません（食い違い 0）」の行。★数は走らせた出力から書きます。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

**この項目に書くこと**＝入力の検証／起こりうる誤りの状態／中途半端な出力が残ったとき／やり直せるか。★正常の道だけを書かない。

| 起きたこと | どうなるか |
|---|---|
| 元データの `pre_win` に知らない前処理・形の違う値・月の数の不正 | `expand_stage` が止める（fail-closed）。組む側は候補を作れない |
| `pre_win_bars` に月の数の無い値が渡った | `SampleError` で止まる |
| 直近 n本の幅が0（値が動かない） | その所は値なし＝条件は既定 na=fail で不成立 |
| 最初の n−1本 | 値なし（rolling が過去 n本に満たない） |
| 部品が入口の案の乱数の道に入った | T47 の①が落ちる（壊すプログラム b110） |
| 動く線の候補が作られなくなった | T47 の③が落ちる（壊すプログラム b109） |
| 部品の式からいまのバーが外された | T47 の②が落ちる（壊すプログラム b111） |
| 実行器の式と突き合わせの道具の独立の実装が食い違った | `condition_parts_diag.py` が「食い違いました」で終了コード1 |
| 動く線を使う走行の余白が延びなくなった | T47 の⑤が落ちる（壊すプログラム b112） |
| `stage_warm` を通らずに `WARM` で読む道具（M2-F で段を測る道具ほか）で動く線を測った | 窓の最初の約4か月が値なし（黙って不成立になる）。M2-F-2 の工事で段を測る道具を同じ形にする（やらないこと） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

**この項目に書くこと**＝途中で作る表の列の意味・鍵の意味・既にあるデータの形をどう変えるか。

**§2.2 の元データに欄を1つ足します**（段2c の BB幅 の語に `pre_win`・説明の鍵 `_pre_win の欄`）。既存の語と欄は1つも変えません。

**部品の正本に1行 足します**（`condition_parts.json` の "have" に `ts_pos`）。

**作り直すもの（形は変えない）。**§2.2-0 の表（`engine_tuner_milestones2.md`）・材料の文書（`gen_materials.py --write` が作るもの）・G2・H2 の検査済みの記録。型の表・出口の表・印・成績表は作り直しません（部品の一覧を読まない）。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

**この項目に書くこと**＝置き場・上書きか追記か・作り直せるか・古いものをどうするか。

**新しく書く先はありません。**作り直すファイルは、既存の道具が既存の置き場に書き直します。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

**この項目に書くこと**＝タイムゾーン／境目の時刻を含むか含まないか／足の締まる時刻の定義。★静かに結果を変えるので、非該当にしない。

**窓の数え方。**前処理は実行データ（5分足）の並びに載った列に掛かります。材料の時間足が1時間足でも、窓は5分足の本数で数えます（時間の長さは足によらず6か月）。上位足の材料は、足が閉じた時刻から5分足の並びへ前の値を引き継いで載っています（`build_features` の既存の作り）。

**データの前の余白。**動く線を使う走行（組む側の本走 `run_main`）は、値決め窓・確認窓の開始より「60日＋182.625日」前からデータを読みます（`stage_warm`）。値決め窓の最初のバー（2024-03-01）でも、直近6か月の窓がそろい、その窓の最初のバーの材料にも60日の助走が在ります。ほかの走行は60日のままです。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

**この項目に書くこと**＝時間と容量。★設計の形を決める材料でもあるので、§6-3 の見積もりとは別に書く。

| 何 | 見込み | 根拠 |
|---|---|---|
| `engine_tuner_gen.py --selftest` の1回 | 約5分40秒 | 2026-09-20 の実測 5分33秒 ＋ T47（段2c の候補を1回作る＝§2.2-0 の表を作るのと同じ処理）。★T47 だけの時間は測っていない |
| `engine_tuner_exec.py --selftest` | 約10秒 | 2026-09-18 の実測（9.6秒） |
| `condition_parts_diag.py` | 測っていない | ★走らせる前に worklog から過去の実測を探し、無ければ まこさんに報告してから走らせる（恒久61・62番） |
| `gen_regime_kb.py --write stage`・`--selftest` | 1分未満 | 見込み（測っていない）。段ごとに候補を1回ずつ作る |
| `gen_materials.py --write`・`--verify`・`--selftest` | 約1分30秒 | `--selftest` 68.5秒（2026-09-26 の実測）ほか |
| G2・H2 の取り直し | 約6分半 | G2 約30秒・H2 約5〜6分（2026-09-26 の実測 H2 303.9秒） |
| 直す前と後で結果が同じか確かめる3本の走行 | 約30秒 | 2026-09-20 の実測（7秒・4秒・18秒） |
| 壊すプログラム b109〜b112 の1本 | 約5分40秒 | 上の1行目と同じ（組む側の自己テストを測る）。打ち切りは600秒 |
| 本走（run_main）が読むデータの行 | 値決め窓 約1.30倍・確認窓 約1.76倍 | 余白 60日 → 242.625日。値決め窓 549日・確認窓 181日（periods.py）に余白を足した日数の比。走らせて測っていない |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

**この項目に書くこと**＝同じファイル・同じ記録を2つの走行が触らないか。

**奪い合いに気をつけるもの。**H2 の取り直し（約5〜6分）の間に、組む側・実行器を書き換えません。§2.2 の元データは組む側が読む間 1回だけ読み込みます（`_STAGE_CANDS_MEMO`）。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

**この項目に書くこと**＝取引所の鍵／本番で実際に発注するかの切り替え／検査済みの記録。

**書き換えられては困る記録。**法則ファイル・範囲の置き場・型の表・印・成績表は読むだけです。G2・H2 の検査済みの記録は、決まったプログラムで取り直します。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

**この項目に書くこと**＝途中経過が見えるか（恒久60番が求める）。後から何が起きたかを追えるか。

**画面に出すもの。**T47 の1行（最後が「＝通った」か「＝落ちた」）と、落ちたときの `❌ T47: …` の行。§2.2-0 の表の前処理の欄。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

**この項目に書くこと**＝いま在るもののうち、何がこの部分に依存しているか。★hook 64本と承認・ハッシュ値が絡むので、この repo では特に重い。

1. **段2c の候補の本数。**BB幅 の固定の線の本数だけ増えます（いま 42本の見込み＝§2.2-0 の表の BB幅 の行）。★数は作り直した表から書きます。
2. **束を組む側。**3枠目は案の番号から決まる順位で取り、動く線は固定の線の後ろに並ぶので、いまの順位の束は変わりません。後ろの順位まで進んだ案だけが動く線を使います。
3. **入口の案。**部品が乱数の道の外なので、入口の案の作り方は変わりません（T1-C6e と T47 の①）。
4. **材料の文書。**前処理の一覧の数が 8 → 9 になり、作り直します。
5. **G2・H2 の検査済みの記録。**実行器と組む側を触るので失効します。G2 → H2 の順で取り直します。
6. **直す前と後で結果が同じか確かめる3本の走行（S1・S2・L1）。**固定のレシピは新しい部品を使わないので、変わらない見込みです。
7. **壊すプログラム b78・b79・b82・b92・b93。**探す行は消しません。
8. **売買のロジック・審判・法則・成績表・型の表・印・範囲の置き場。**触りません。
9. **組む側の本走のデータの余白。**60日 → 60日＋182.625日になります。長い記憶を持つ指標（上位足の長い期間の平均など）の値が、窓の始まりで少し変わりえます＝本走の土台の数字（`_run_baseline`）も変わりえます。データの置き場の指紋（`data_fingerprint`）に余白が入るので、前のキャッシュは使われず作り直されます。
10. **恒等の走行・H2・ほかの道具の余白。**`engine_tuner.WARM`（60日）のまま変わりません（`stage_warm` を呼ばない）。M2-F で段を測る道具（`regime_r9_diag.py`）は M2-F-2 の工事で `stage_warm` を使う形にします。
11. **束の案の記録と指紋。**場面の判定の束を付けた案（`--build-regime`）は、束の中身（条件）は変わりませんが、案に残す引いた記録（`meta.regime_draw` の G の「上位」と `stages` の段2c の候補の本数＝261 → 261＋BB幅 の固定の線の本数）が変わるので、案の指紋（`recipe_hash`）が全部 変わります。直す前の走行の記録からの再開（R12・鍵 `s1/番号/指紋`）では、同じ案でも走らせ直しになります。

### 4-18 再利用（手本にした、既にあるものの形）

**この項目に書くこと**＝同じ形が既にどこかに在るか。手本にしたファイル（`MODEL:` の行と同じ相手）。

| 手本 | 何を写すか |
|---|---|
| 実行器の `ts_rank`・`ts_std` の登録と式 | 窓 n を持つ前処理の部品の書き方（いまのバーを含める） |
| 実行器の `pre_ops` の `needs_n` の絞り（M2-E-3） | 既定 None で今までどおり全部を返す絞りの足し方 |
| 組む側の段2a の `pre`（abs）の付け方 | 元データの欄から材料に前処理を付ける形 |
| 組む側の T36（abs の番人） | 番人の①一覧 ②既知答え ③組む側の出し方 の並び |
| `condition_parts_diag.p_ts_rank` と見本「直近20本の中の順位 ≥0.8」 | 独立の実装と突き合わせの見本 |
| `.claude/breaks/b104_atr1h_own_tf.sh` | 壊すプログラムの書き方（EXPECT_RC・MEANS・EXPECT_MSG・guard・measure・finish） |
| StockCharts「Stochastic Oscillator」の %K | 範囲の中の位置の式（×100 はしない） |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

**この項目に書くこと**＝この工事で実物に当てる直しを、監査結果の修正の指示と同じ6つの欄（対象のファイル・直す箇所・直す前の文字・4つ目・根拠の抜き書き・状態）で1件ずつ書く。★元データの「実装の指示」が空なら非該当（理由を書く）。

<!-- ACC_IMPL_START hash=ed2417913ac7c6e7 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/engine_tuner_exec.py
直す箇所: 422行（MATERIAL_PRE の ts_std の行の直後）
直す前の文字:
~~~
    "ts_std": {"desc": "直近 n本のばらつき（標準偏差・いまのバーを含める）", "same_unit": False},
~~~
足す文字:
~~~

    # ★2026-09-27（M2-E-4e・設計書 m2e4e-r6-moving-line-20260927）＝直近 n本の最小〜最大の間の、いまの値の位置。
    #   まこさん決定（2026-09-27・逐語「２，案①、新しい部品を1つ足す案」）＝場面の判定の段2c の「動く線」
    #   （BB幅 が直近6か月の範囲の下の方に在るか）を測る部品。式は Stochastic の %K と同じ形
    #   （StockCharts の逐語 "%K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100"）で、×100 はしない（0〜1）。
    #   ★いまのバーを含める（ts_rank と同じ理由＝いまの値の位置を出すため）。最大＝最小なら値なし。
    #   ★`gen_draw: False`＝入口の案を乱数で作る道（engine_tuner_gen の `pre_ops(same_unit=False, gen_draw=True)`）では引かない
    #     （恒久67番＝乱数の道を広げない）。使うのは段2c の動く線だけ。
    "ts_pos": {"desc": "いまの値が 直近 n本の最小〜最大の間のどこか（0〜1・いまのバーを含める）",
               "same_unit": False, "gen_draw": False},
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_exec.py:422「"ts_std": {"desc": "直近 n本のばらつき（標準偏差・いまのバーを含める）", "same_unit": False},」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/engine_tuner_exec.py
直す箇所: 443〜444行（pre_ops の引数）
直す前の文字:
~~~
def pre_ops(same_unit: bool | None = None, needs_state: bool | None = None,
            needs_n: bool | None = None) -> list[str]:
~~~
直した後の文字:
~~~
def pre_ops(same_unit: bool | None = None, needs_state: bool | None = None,
            needs_n: bool | None = None, gen_draw: bool | None = None) -> list[str]:
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_exec.py:443「def pre_ops(same_unit: bool | None = None, needs_state: bool | None = None,」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/engine_tuner_exec.py
直す箇所: 464行（pre_ops の絞りの最後の行）
直す前の文字:
~~~
                  and (needs_n is None or v.get("needs_n", True) is needs_n))
~~~
直した後の文字:
~~~
                  and (needs_n is None or v.get("needs_n", True) is needs_n)
                  # ★2026-09-27（M2-E-4e）＝入口の案を乱数で作る道で引いてよい部品だけに絞る。
                  #   既定（None）では今までどおり全部 返す。gen_draw の欄を持たない部品は True とみなす。
                  and (gen_draw is None or v.get("gen_draw", True) is gen_draw))
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_exec.py:464「and (needs_n is None or v.get("needs_n", True) is needs_n))」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/engine_tuner_exec.py
直す箇所: 525行（_apply_pre の最後の拒否の行）
直す前の文字:
~~~
    raise RecipeError(f"[実行器] 材料の前処理 {op} の実行が未実装")
~~~
直した後の文字:
~~~
    if op == "ts_pos":
        # ★2026-09-27（M2-E-4e）＝いまの値が 直近 n本の最小〜最大の間のどこか（0〜1）。
        #   いまのバーを含める。rolling は過去 n本だけ＝未来は見ない。最大＝最小（幅が0）なら値なし。
        lo = s.rolling(n).min()
        width = s.rolling(n).max() - lo
        return ((s - lo) / width.where(width > 0)).to_numpy(float)
    raise RecipeError(f"[実行器] 材料の前処理 {op} の実行が未実装")
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_exec.py:525「raise RecipeError(f"[実行器] 材料の前処理 {op} の実行が未実装")」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 1805行（_make_cond の単位の変わる部品の一覧）
直す前の文字:
~~~
        _pre_opts = [None] + ex.pre_ops(same_unit=False)
~~~
直した後の文字:
~~~
        _pre_opts = [None] + ex.pre_ops(same_unit=False, gen_draw=True)   # ★2026-09-27（M2-E-4e）＝乱数の道で引かない部品（ts_pos）を外す
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:1805「_pre_opts = [None] + ex.pre_ops(same_unit=False)」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 5211行（selftest の T1-C6e の部品の一覧）
直す前の文字:
~~~
    _lv_ops = ex.pre_ops(same_unit=False)
~~~
直した後の文字:
~~~
    _lv_ops = ex.pre_ops(same_unit=False, gen_draw=True)   # ★2026-09-27（M2-E-4e）＝案を作る道が引く部品だけを見る（ts_pos は段2c の動く線だけで使う）
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5211「_lv_ops = ex.pre_ops(same_unit=False)」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 2509行（stage_candidates が元データから渡す鍵）
直す前の文字:
~~~
                "pre": dict(_s.get("pre") or {}),
~~~
足す文字:
~~~

                # ★2026-09-27（M2-E-4e）＝窓つきの前処理（指標の名前 → {"op", "months"}）。
                #   固定の線と別に「動く線」の候補を作る（build_stage_candidates）。
                "pre_win": dict(_s.get("pre_win") or {}),
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2509「"pre": dict(_s.get("pre") or {}),」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 2545行（符号を取り去る前処理の説明の最後の行の直後）
直す前の文字:
~~~
#   やろうとしないから、絶対入れろ」で足した前処理そのものは、1つも外していない。
~~~
足す文字:
~~~



# ★2026-09-27（M2-E-4e・設計書 m2e4e-r6-moving-line-20260927）＝窓つきの前処理の窓（月）を、実行データの足の本数に直す。
#   なぜ要るか＝前処理は実行データ（5分足）の並びに載った列に掛かる（engine_tuner_exec._col_array）。
#   だから窓の本数は、材料の時間足によらず5分足の本数で数える。
#   ★5 の出どころ＝要件 cat_requirements §4.6 の H7「5m が現行標準」と、実行データ（5分足の正本）。
#   ★1か月＝365.25 ÷ 12 日（暦の平均）。月の数は §2.2 の元データ（m2_stage_candidates.json の pre_win の months）が持ち、
#     その出どころは相場の法則の逐語 six-month。私は月の数を作らない。
_EXEC_BAR_MIN = 5


def pre_win_bars(pw: dict) -> int:
    """窓つきの前処理 {"op", "months"} の窓を、実行データ（5分足）の本数に直す（fail-closed）。"""
    months = pw.get("months")
    if not isinstance(months, int) or isinstance(months, bool) or months < 1:
        raise SampleError(f"窓つきの前処理の月の数が不正: {months!r}（1 以上の整数・fail-closed）")
    return int(round(months * 365.25 / 12 * 1440 / _EXEC_BAR_MIN))


def stage_warm(base_warm):
    """§2.2 の元データに窓つきの前処理（pre_win）が在れば、データの前の余白を「いまの余白＋いちばん長い窓」にする。

    ★2026-09-27（M2-E-4e・まこさん決定「余白の直し方→C」）＝動く線を使う走行（この道具の本走 run_main）だけ余白を延ばす。
      窓の最初の1本の材料にも、いまの余白（指標の助走）が要るので、足し算にする。
      恒等の走行・H2 など、この関数を呼ばない走行の余白は今のまま（engine_tuner.WARM）。
    """
    months = [int(pw["months"]) for k in STAGE_SPEC for pw in stage_candidates(k)["pre_win"].values()]
    if not months:
        return base_warm
    return base_warm + pd.Timedelta(minutes=pre_win_bars({"months": max(months)}) * _EXEC_BAR_MIN)
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2545「#   やろうとしないから、絶対入れろ」で足した前処理そのものは、1つも外していない。」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 2843行（build_stage_candidates の法則の系統を読む行の直後）
直す前の文字:
~~~
    lins_law = stage_lineages_of(stage, spec_c, laws)
~~~
足す文字:
~~~

    # ★2026-09-27（M2-E-4e）＝「動く線」の候補（窓つきの前処理を付けたもの）。固定の線の候補を全部 並べた後ろに足す
    #   ＝固定の線の順位を1つも変えない（束を組む側は順位で3枠目を取るので、いまの束は変わらない）。
    _moving: list[dict] = []
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2843「lins_law = stage_lineages_of(stage, spec_c, laws)」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 2917〜2918行（固定の線の候補を足す行の直後・分位の繰り返しの中）
直す前の文字:
~~~
                        "acc": med, "label": lab, "horizon": hor, "cond": _c,
                        "law_check": "—", "dropped_by": None})
~~~
足す文字:
~~~

            # ★2026-09-27（M2-E-4e）＝この指標に窓つきの前処理（pre_win）が在れば、同じ閾値の「動く線」の候補も作る。
            #   材料に前処理を付けるだけ＝側と閾値の分位は固定の線と同じ（法則が決める側・まこさん決定の1点）。
            _pw = spec_c["pre_win"].get(fam)
            if _pw:
                _cm = json.loads(json.dumps(_c))
                _inm = _cm["not"] if "not" in _cm else _cm
                _inm["material"] = [{**_inm["material"][0],
                                     "pre": {"op": _pw["op"], "n": pre_win_bars(_pw)}}]
                _moving.append({"stage": stage, "rank": None, "col": col, "family": fam, "tf": tf,
                                "acc": med, "label": lab, "horizon": hor, "cond": _cm,
                                "law_check": "—", "dropped_by": None, "pre_win": dict(_pw)})
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2917「"acc": med, "label": lab, "horizon": hor, "cond": _c,」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 2919〜2920行（候補が0件のときの拒否）
直す前の文字:
~~~
    if not out:
        raise SampleError(f"{stage} の候補が0件（法則 {_law} の名指し・§2.2 の語・型の表の絞りの後）")
~~~
直した後の文字:
~~~
    for _mv in _moving:                            # ★動く線は、固定の線の後ろに順位を続けて並べる（M2-E-4e）
        rank += 1
        _mv["rank"] = rank
        out.append(_mv)
    if not out:
        raise SampleError(f"{stage} の候補が0件（法則 {_law} の名指し・§2.2 の語・型の表の絞りの後）")
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2920「raise SampleError(f"{stage} の候補が0件（法則 {_law} の名指し・§2.2 の語・型の表の絞りの後）")」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7140行（selftest の T36 の最後の行の直後）
直す前の文字:
~~~
        ng.append(f"T36: 途中で止まった: {type(_e36).__name__} {_e36}")
~~~
足す文字:
~~~


    # ══ T47 動く線（M2-E-4e・2026-09-27）＝BB幅 が直近6か月の範囲の下の方に在るかを、段2c の候補に足す ══════
    #   ①部品 ts_pos が一覧に在り、入口の案を乱数で作る道の一覧（gen_draw=True）には入らない（恒久67番）
    #   ②既知答え＝直近5本の最小〜最大の中の位置（いまのバーを含める・幅0は値なし）
    #   ③6か月が5分足 52596本。段2c の候補に、BB幅 の固定の線と同じ本数の動く線が在り、
    #     材料は ts_pos・窓 52596本で、固定の線の後ろに並ぶ（固定の線の順位を変えない）
    #   ⑤動く線を使う走行（本走）の余白が「いまの余白＋6か月」（まこさん決定「余白の直し方→C」）
    #   ★壊すプログラム b109（動く線を作らない）・b110（乱数の道に入れる）・b111（いまのバーを外す）・b112（余白を延ばさない）がこの検査を測る。
    try:
        _ng47: list[str] = []
        if "ts_pos" not in ex.MATERIAL_PRE:
            _ng47.append("①前処理の一覧に ts_pos が無い")
        if "ts_pos" in ex.pre_ops(same_unit=False, gen_draw=True):
            _ng47.append("①入口の案を乱数で作る道の一覧に ts_pos が入っている")
        if "ts_pos" not in ex.pre_ops(same_unit=False):
            _ng47.append("①既定の一覧から ts_pos が落ちた")
        _a47 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 3.0, 3.0, 3.0, 3.0, 3.0])
        _g47 = ex._apply_pre(_a47, {"op": "ts_pos", "n": 5})
        _w47 = np.array([np.nan] * 4 + [1.0, 1.0 / 3.0, 0.0, 0.0, 0.0, np.nan])
        if not np.allclose(_g47, _w47, equal_nan=True):
            _ng47.append(f"②既知答えと違う: {list(np.round(_g47, 4))}（期待 {list(np.round(_w47, 4))}）")
        if pre_win_bars({"op": "ts_pos", "months": 6}) != 52596:
            _ng47.append(f"③6か月が5分足 52596本にならない: {pre_win_bars({'op': 'ts_pos', 'months': 6})}")
        _lm47, _ = load_limits()
        _lm47 = resolve_hold_range(_lm47, "e38")
        _c47 = build_stage_candidates("stage2c", laws_for_scene("range"), load_signal_table(),
                                      material_pool()[1], _lm47)
        _mv47 = [c for c in _c47 if c.get("pre_win")]
        _fx47 = [c for c in _c47 if not c.get("pre_win")]
        _bb47 = [c for c in _fx47 if c.get("family") == "BB幅"]
        if not _mv47:
            _ng47.append("③段2c の候補に動く線が1本も無い")
        if len(_mv47) != len(_bb47):
            _ng47.append(f"③動く線 {len(_mv47)} 本が、BB幅 の固定の線 {len(_bb47)} 本と合わない")
        for c in _mv47:
            _in47 = c["cond"]["not"] if "not" in c["cond"] else c["cond"]
            if c.get("family") != "BB幅" or _in47["material"][0].get("pre") != {"op": "ts_pos", "n": 52596}:
                _ng47.append(f"③動く線の材料が違う: {c.get('col')} {_in47['material'][0].get('pre')}")
                break
        if _mv47 and _fx47 and min(c["rank"] for c in _mv47) <= max(c["rank"] for c in _fx47):
            _ng47.append("③動く線が固定の線の後ろに並んでいない（固定の線の順位が変わる）")
        _wm47 = stage_warm(pd.Timedelta(days=60))
        if _wm47 != pd.Timedelta(days=60) + pd.Timedelta(minutes=52596 * 5):
            _ng47.append(f"⑤動く線を使う走行の余白が 60日＋6か月にならない: {_wm47}")
        _src47 = pathlib.Path(__file__).read_text(encoding="utf-8")
        _rm47 = _src47[_src47.index("\ndef run_main") + 1:]
        _rm47 = _rm47[:_rm47.index("\ndef ")]
        if "_warm, use_cache=not a.no_cache)" not in _rm47:
            _ng47.append("⑤本走（run_main）が stage_warm の余白でデータを読んでいない")
        ng += [f"T47: {x}" for x in _ng47]
        print(f"  T47 動く線: ①ts_pos は乱数の道の外 ／ ②既知答え ／ ③段2c の動く線 {len(_mv47)} 本"
              f"（BB幅 の固定の線 {len(_bb47)} 本・窓 5分足 52596本・固定の線の後ろ）／ ⑤余白 {_wm47}"
              + ("＝通った" if not _ng47 else "＝落ちた"))
    except SystemExit as _e47s:
        ng.append(f"T47: 途中で拒否されて止まった: {str(_e47s)[:120]}")
    except Exception as _e47:
        ng.append(f"T47: 途中で止まった: {type(_e47).__name__} {_e47}")
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:7140「ng.append(f"T36: 途中で止まった: {type(_e36).__name__} {_e36}")」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/condition_parts_diag.py
直す箇所: 151行（p_ts_std の最後の行の直後）
直す前の文字:
~~~
    return pd.Series(a).rolling(int(n)).std().to_numpy(float)
~~~
足す文字:
~~~



def p_ts_pos(a: np.ndarray, n: int) -> np.ndarray:
    """⑳直近 n本の最小〜最大の間の、いまの値の位置（0〜1・★2026-09-27 の M2-E-4e で足した部品）。

    いまのバーを含める（ts_rank と同じ）。幅0は値なし。
    ★実行器の式を使わずに書いた独立の実装＝突き合わせの相手（式は Stochastic の %K と同じ形・×100 はしない）。
    """
    s = pd.Series(a)
    lo = s.rolling(int(n)).min().to_numpy(float)
    hi = s.rolling(int(n)).max().to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = (np.asarray(a, float) - lo) / (hi - lo)
    return np.where(hi - lo > 0, out, np.nan)
~~~
根拠の抜き書き: scripts/priority_rebuild/condition_parts_diag.py:151「return pd.Series(a).rolling(int(n)).std().to_numpy(float)」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/condition_parts_diag.py
直す箇所: 296行（前処理の部品の表）
直す前の文字:
~~~
              "ts_rank": p_ts_rank, "ts_std": p_ts_std}
~~~
直した後の文字:
~~~
              "ts_rank": p_ts_rank, "ts_std": p_ts_std, "ts_pos": p_ts_pos}
~~~
根拠の抜き書き: scripts/priority_rebuild/condition_parts_diag.py:296「"ts_rank": p_ts_rank, "ts_std": p_ts_std}」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/condition_parts_diag.py
直す箇所: 420行（見本「直近20本のばらつき ≥10」の最後の行の直後）
直す前の文字:
~~~
             cols=1, v={"th": 10.0, "side": "above", "n": 20, "op": "ts_std"}),
~~~
足す文字:
~~~

        # ★2026-09-27（M2-E-4e）＝『いまの値が 直近20本の範囲の下から2割以内』（部品 ts_pos）。
        dict(form="level", compose="level_pre", label="直近20本の範囲の中の位置 ≤0.2",
             real={"form": "level", "side": "below", "value": {"n": 0.2},
                   "material": [{**m1, "pre": {"op": "ts_pos", "n": 20}}]},
             cols=1, v={"th": 0.2, "side": "below", "n": 20, "op": "ts_pos"}),
~~~
根拠の抜き書き: scripts/priority_rebuild/condition_parts_diag.py:420「cols=1, v={"th": 10.0, "side": "above", "n": 20, "op": "ts_std"}),」
状態: 確定

#### 実装 16
対象のファイル: .claude/ratchet/m2_stage_candidates.json
直す箇所: 78行（段2c の BB幅 の語）
直す前の文字:
~~~
        {"§2.2": "BB幅", "探す": "BB幅", "当て方": "完全"},
~~~
直した後の文字:
~~~
        {"§2.2": "BB幅", "探す": "BB幅", "当て方": "完全", "pre_win": {"op": "ts_pos", "months": 6}},
~~~
根拠の抜き書き: .claude/ratchet/m2_stage_candidates.json:78「{"§2.2": "BB幅", "探す": "BB幅", "当て方": "完全"},」
状態: 確定

#### 実装 17
対象のファイル: .claude/ratchet/m2_stage_candidates.json
直す箇所: 8行（法則と役割の欄の説明の最後）
直す前の文字:
~~~
段3 の役割がこの元データと食い違っていた（コード＝None）。",
~~~
足す文字:
~~~

  "_pre_win の欄": "★2026-09-27（M2-E-4e・設計書 m2e4e-r6-moving-line-20260927）＝窓つきの前処理。`pre`（いつも掛ける・窓なし）と違い、`pre_win` を持つ指標は、固定の線（前処理なし）と「動く線」（この前処理を付けたもの）の両方を候補に出す。書けるのは op（前処理の一覧 MATERIAL_PRE の名前）と months（窓の月の数・1 以上の整数）の2つだけ（gen_regime_kb.expand_stage が照らす）。月は engine_tuner_gen.pre_win_bars が実行データ（5分足）の本数に直す。★段2c の BB幅 の出どころ＝法則 R6 の根拠の逐語 Ideally, BandWidth should be near the low end of its six-month range.（StockCharts「Bollinger Band Squeeze」）・まこさん決定 2026-09-27「１，案A」（BB幅 だけ）「２，案①、新しい部品を1つ足す案」（最小〜最大の間の位置＝ts_pos）。",
~~~
根拠の抜き書き: .claude/ratchet/m2_stage_candidates.json:8「段3 の役割がこの元データと食い違っていた（コード＝None）。」
状態: 確定

#### 実装 18
対象のファイル: .claude/tools/gen_regime_kb.py
直す箇所: 1041行（expand_stage の段ごとの入れ物）
直す前の文字:
~~~
        pre: dict = {}
~~~
足す文字:
~~~

        pre_win: dict = {}                       # ★2026-09-27（M2-E-4e）＝窓つきの前処理（指標の名前 → {"op", "months"}）
~~~
根拠の抜き書き: .claude/tools/gen_regime_kb.py:1041「pre: dict = {}」
状態: 確定

#### 実装 19
対象のファイル: .claude/tools/gen_regime_kb.py
直す箇所: 1058行（語の前処理を集める行の直後）
直す前の文字:
~~~
                    pre[f] = w["pre"]
~~~
足す文字:
~~~

                if w.get("pre_win"):
                    pre_win[f] = w["pre_win"]
~~~
根拠の抜き書き: .claude/tools/gen_regime_kb.py:1058「pre[f] = w["pre"]」
状態: 確定

#### 実装 20
対象のファイル: .claude/tools/gen_regime_kb.py
直す箇所: 1071行（知らない前処理を止める行の直後）
直す前の文字:
~~~
                ng.append(f"{_k}: 知らない前処理 → {_f} に {_op}（前処理の一覧＝{sorted(pres_all)}）")
~~~
足す文字:
~~~

        for _f, _pw in pre_win.items():               # ★2026-09-27（M2-E-4e）＝窓つきの前処理の形を照らす（fail-closed）
            if not isinstance(_pw, dict) or set(_pw) != {"op", "months"}:
                ng.append(f"{_k}: 窓つきの前処理の形が違う → {_f} に {_pw}（op と months の2つだけ）")
            elif _pw["op"] not in pres_all:
                ng.append(f"{_k}: 知らない前処理 → {_f} に {_pw['op']}（前処理の一覧＝{sorted(pres_all)}）")
            elif not isinstance(_pw["months"], int) or isinstance(_pw["months"], bool) or _pw["months"] < 1:
                ng.append(f"{_k}: 窓つきの前処理の月の数が不正 → {_f} に {_pw['months']!r}（1 以上の整数）")
~~~
根拠の抜き書き: .claude/tools/gen_regime_kb.py:1071「ng.append(f"{_k}: 知らない前処理 → {_f} に {_op}（前処理の一覧＝{sorted(pres_all)}）")」
状態: 確定

#### 実装 21
対象のファイル: .claude/tools/gen_regime_kb.py
直す箇所: 1079行（expand_stage が返す鍵）
直す前の文字:
~~~
                   "lineages": list(s.get("lineages") or []), "geo_cols": geo, "pre": pre,
~~~
直した後の文字:
~~~
                   "lineages": list(s.get("lineages") or []), "geo_cols": geo, "pre": pre, "pre_win": pre_win,
~~~
根拠の抜き書き: .claude/tools/gen_regime_kb.py:1079「"lineages": list(s.get("lineages") or []), "geo_cols": geo, "pre": pre,」
状態: 確定

#### 実装 22
対象のファイル: .claude/tools/gen_regime_kb.py
直す箇所: 1211行（§2.2-0 の表の前処理の欄）
直す前の文字:
~~~
                _ps = "・".join(sorted({_pre[f] for f in _hit if f in _pre})) or "—"
~~~
直した後の文字:
~~~
                _pre_w = s.get("pre_win") or {}          # ★2026-09-27（M2-E-4e）＝窓つきの前処理も欄に出す
                _ps = "・".join(sorted({_pre[f] for f in _hit if f in _pre}
                                       | {f"{_pre_w[f]['op']}（{_pre_w[f]['months']}か月・動く線）"
                                          for f in _hit if f in _pre_w})) or "—"
~~~
根拠の抜き書き: .claude/tools/gen_regime_kb.py:1211「_ps = "・".join(sorted({_pre[f] for f in _hit if f in _pre})) or "—"」
状態: 確定

#### 実装 23
対象のファイル: .claude/ratchet/condition_parts.json
直す箇所: 222〜224行（ts_std の塊の最後）
直す前の文字:
~~~
    "alphagen:Std"
   ]
  },
~~~
足す文字:
~~~

  {
   "id": "ts_pos",
   "name": "n本の範囲の中の位置",
   "where": "材料の前処理（材料に pre:{op:ts_pos, n} を付ける）。★場面の判定の段2c の「動く線」だけで使う（入口の案を乱数で作る道では引かない＝gen_draw False）",
   "impl": "engine_tuner_exec._apply_pre＝(いまの値 − 直近n本の最小) ÷ (直近n本の最大 − 直近n本の最小)。いまのバーを含める（ts_rank と同じ理由）。幅0は値なし。値は 0〜1。★2026-09-27 の M2-E-4e で足した（BB幅 が直近6か月の範囲の下の方に在るか）。式は StockCharts の Stochastic の %K（%K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100）と同じ形で ×100 をしない。番人＝engine_tuner_gen --selftest の T47 ／ condition_parts_diag の『直近20本の範囲の中の位置』",
   "src": [
    "alphagen:Max",
    "alphagen:Min"
   ]
  },
~~~
根拠の抜き書き: .claude/ratchet/condition_parts.json:222「"alphagen:Std"」
状態: 確定

#### 実装 24
対象のファイル: .claude/breaks/b109_moving_line_not_built.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 段2c の候補に動く線を作る分岐を止めると、T47 が「段2c の候補に動く線が1本も無い」で落ちた
# EXPECT_MSG: ❌ T47
# b109 — build_stage_candidates が窓つきの前処理（pre_win）から動く線の候補を作る分岐を止めると、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #1（段2c の候補に、BB幅 の固定の線と同じ本数の動く線が在る）
#   壊し方＝`            if _pw:` を `            if False and _pw:` にする。
#   期待＝組む側の自己テスト T47 の③が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '            if _pw:\n'
if s.count(old) != 1:
    raise SystemExit("[b109] 壊す対象の行が1か所でない: " + old.strip())
new = '            if False and _pw:  # b109 が壊した（動く線を作らない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 25
対象のファイル: .claude/breaks/b110_ts_pos_in_random_draw.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 部品 ts_pos の「乱数の道で引かない」印を外すと、T47 が「入口の案を乱数で作る道の一覧に ts_pos が入っている」で落ちた
# EXPECT_MSG: ❌ T47
# b110 — 実行器の MATERIAL_PRE の ts_pos から gen_draw False を外すと、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #2（部品 ts_pos は入口の案を乱数で作る道の一覧に入らない・恒久67番）
#   壊し方＝`"same_unit": False, "gen_draw": False},` を `"same_unit": False},` にする。
#   期待＝組む側の自己テスト T47 の①が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
GEN="$PR/engine_tuner_gen.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '               "same_unit": False, "gen_draw": False},\n'
if s.count(old) != 1:
    raise SystemExit("[b110] 壊す対象の行が1か所でない: " + old.strip())
new = '               "same_unit": False},  # b110 が壊した（乱数の道の印を外す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 26
対象のファイル: .claude/breaks/b111_ts_pos_excludes_current.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 部品 ts_pos の最小からいまのバーを外すと、T47 が「既知答えと違う」で落ちた
# EXPECT_MSG: ❌ T47
# b111 — 実行器の _apply_pre の ts_pos で、最小を直前 n本（いまのバーを含めない）に変えると、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #3（直近 n本はいまのバーを含める＝いまの値の位置を出す）
#   壊し方＝`        lo = s.rolling(n).min()` を `        lo = s.shift(1).rolling(n).min()` にする。
#   期待＝組む側の自己テスト T47 の②（既知答え）が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

EXE="$PR/engine_tuner_exec.py"
GEN="$PR/engine_tuner_gen.py"
guard "$EXE"

python3 - "$EXE" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '        lo = s.rolling(n).min()\n'
if s.count(old) != 1:
    raise SystemExit("[b111] 壊す対象の行が1か所でない: " + old.strip())
new = '        lo = s.shift(1).rolling(n).min()  # b111 が壊した（いまのバーを最小から外す）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 27
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7730〜7732行（run_main が本走のデータを読む所）
直す前の文字:
~~~
    df, df_c = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END), (CONFIRM_START, CONFIRM_END)],
                                      et.WARM, use_cache=not a.no_cache)
    print(f"[データ] 値決め窓 {len(df):,} バー ／ 確認窓 {len(df_c):,} バー（助走込み・{time.time() - t0:.0f}秒）")
~~~
直した後の文字:
~~~
    # ★2026-09-27（M2-E-4e・まこさん決定「余白の直し方→C」）＝この本走は段2c の動く線（6か月の窓）を使いうるので、
    #   データの前の余白を「いまの余白＋いちばん長い窓」にする（stage_warm）。ほかの走行は engine_tuner.WARM のまま。
    _warm = stage_warm(et.WARM) if a.build_regime else et.WARM
    df, df_c = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END), (CONFIRM_START, CONFIRM_END)],
                                      _warm, use_cache=not a.no_cache)
    print(f"[データ] 値決め窓 {len(df):,} バー ／ 確認窓 {len(df_c):,} バー（助走込み・余白 {_warm}・{time.time() - t0:.0f}秒）")
~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:7731「et.WARM, use_cache=not a.no_cache)」
状態: 確定

#### 実装 28
対象のファイル: .claude/breaks/b112_stage_warm_not_extended.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 動く線を使う走行の余白を延ばさない形にすると、T47 が「余白が 60日＋6か月にならない」で落ちた
# EXPECT_MSG: ❌ T47
# b112 — stage_warm が余白を延ばさず、いまの余白をそのまま返す形にすると、T47 が落ちるか（M2-E-4e・2026-09-27）
#   守っているもの＝完成の条件 #4（動く線を使う走行の余白＝いまの余白＋6か月・まこさん決定「余白の直し方→C」）
#   壊し方＝`stage_warm` の最後の return を `    return base_warm` にする。
#   期待＝組む側の自己テスト T47 の⑤が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

GEN="$PR/engine_tuner_gen.py"
guard "$GEN"

python3 - "$GEN" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    return base_warm + pd.Timedelta(minutes=pre_win_bars({"months": max(months)}) * _EXEC_BAR_MIN)\n'
if s.count(old) != 1:
    raise SystemExit("[b112] 壊す対象の行が1か所でない: " + old.strip())
new = '    return base_warm  # b112 が壊した（余白を延ばさない）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$GEN" --selftest
finish

~~~
根拠の抜き書き: .claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」
状態: 確定

#### 実装 29
対象のファイル: .claude/ratchet/m2_stage_candidates.json
直す箇所: 88行（段2c の入れなかったものの1行目）
直す前の文字:
~~~
前処理の一覧（MATERIAL_PRE の8つ＝ts_max・ts_min・ts_rank・ts_std・since_min・since_max・at_entry・abs）
~~~
直した後の文字:
~~~
前処理の一覧（MATERIAL_PRE の9つ＝ts_max・ts_min・ts_rank・ts_std・since_min・since_max・at_entry・abs・ts_pos）
~~~
根拠の抜き書き: .claude/ratchet/m2_stage_candidates.json:88「MATERIAL_PRE の8つ＝ts_max・ts_min・ts_rank・ts_std・since_min・since_max・at_entry・abs」
状態: 確定

<!-- ACC_IMPL_END -->

### 4-A この節に何を書いたか（一覧）

**★この表は管理のためのものです。**設計の中身は上の 4-0 から順に読んでください。

| 番号 | 段 | 項目 | 書いたか |
|---|---|---|---|
| 4-0 | 必ず | この仕組みは何か（全体・一続きの文章で書く） | 書いた |
| 4-1 | 必ず | システムの境界（誰が動かし、誰が結果を使うか） | 書いた |
| 4-2 | 必ず | 入力と出力（受け取るもの・出すもの・その形） | 書いた |
| 4-6 | 条件 | 制約（従う決まりの全件と、その出どころ） | 書いた |
| 4-3 | 必ず | 部品と責任の割り当て（どの部品が何をやるか） | 書いた |
| 4-4 | 必ず | 処理の流れ（うまくいったとき、何がどの順に起きるか） | 書いた |
| 4-19 | 必ず | 通しの例（最初から最後まで、1件を追いかけた例） | 書いた |
| 4-7 | 条件 | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 書いた |
| 4-9 | 条件 | 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗） | 書いた |
| 4-12 | 必ず | 出る結果の姿（完成したとき、何がどう表示されるか） | 書いた |
| 4-5 | 必ず | 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか） | 書いた |
| 4-8 | 条件 | データ構造（表や JSON の列と中身を、新しく作るか・変えるか） | 書いた |
| 4-10 | 条件 | 保存先（出したものをどこに置くか・上書きか、書き足すか） | 書いた |
| 4-11 | 条件 | 時刻の扱い（時間帯・足の区切りをどこで切るか） | 書いた |
| 4-14 | 条件 | 性能（どれくらい時間が掛かり、どれくらい容量を使うか） | 書いた |
| 4-15 | 条件 | 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか） | 書いた |
| 4-16 | 条件 | セキュリティ（人に見せてはいけない値と、書き換えられては困る記録） | 書いた |
| 4-17 | 省ける | ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか） | 書いた |
| 4-13 | 必ず | 影響範囲（この直しで、ほかのどれが壊れるか） | 書いた |
| 4-18 | 省ける | 再利用（手本にした、既にあるものの形） | 書いた |
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 29 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 部品の名前を ts_pos にする | 既存の前処理の名前（ts_max・ts_min・ts_rank・ts_std）と同じ形で、直近 n本の中の位置（position）と分かる | stoch と名付ける。捨てた理由＝Stochastic の %K は ×100 で、終値を高値・安値の範囲で見る指標の名前。この部品は同じ列の最小〜最大で 0〜1 |
| 2 | 窓つきの前処理は、元データに別の欄 `pre_win` を作って書く | 既存の `pre` は「いつも掛ける・窓なし」で、段2a の abs が使う（文字の部品名を前提に照らしている）。`pre_win` は「固定の線と別に動く線を作る」で、意味が違う | `pre` を文字か辞書かで読み分ける。捨てた理由＝同じ欄に2つの意味を持たせると、読み手3つ（組む側・突き合わせの道具・表）の全部で分岐が要る |
| 3 | 動く線の候補は、固定の線の候補の後ろに並べる | 束を組む側は案の番号から決まる順位で3枠目を取る。後ろに足せば、いまの順位の束は1本も変わらない | 固定の線のすぐ隣に並べる。捨てた理由＝後ろの固定の線の順位が全部ずれ、いまの束が変わる |
| 4 | 窓の本数は5分足で数え、1か月＝365.25÷12日で直す | 前処理は実行データ（5分足）の並びの列に掛かる。月の数は逐語から取り、日への直し方は暦の平均にする | 材料の時間足の本数で数える。捨てた理由＝列は5分足の並びに載っているので、足の本数で数えると窓が短くなる |
| 5 | 部品に `gen_draw: False` を付け、`pre_ops` に絞り `gen_draw` を足す | 入口の案を乱数で作る道が引く一覧を、部品の性質表から絞る（名前を直書きしない） | 入口の道の一覧から名前で `ts_pos` を除く。捨てた理由＝名前の直書きは恒久69番に反する |
| 6 | 動く線を使う走行の余白を「いまの余白＋いちばん長い窓」にする（`stage_warm`） | 窓の最初の1本の材料にも指標の助走（いまの60日）が要る。長さは既に在る WARM と逐語の six-month から決まり、数字を作らない。延ばすのは組む側の本走だけ（まこさん決定 C） | ①WARM を全部の走行で延ばす（案A）。捨てた理由＝まこさん決定 C ②直さない（案B）。捨てた理由＝窓の約4分の3でしか測れない ③余白を6か月ちょうどにする。捨てた理由＝窓の最初のバーの材料に助走が無い |
| 7 | 壊すプログラムを4本 作る（b109〜b112） | 場面の判定の材料と候補を作る組む側と実行器を直す＝恒久71番の線引きの内 | 付けない。捨てた理由＝当てる先が BOT の中身 |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

<!-- ACC_SELFTEST_START hash=25c155ba48c5155d gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝元データの「完成の条件」。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b109_moving_line_not_built.sh` | #1 | 動く線を作る分岐を止めると、T47 が『❌ T47』で落ちる |
| `b110_ts_pos_in_random_draw.sh` | #2 | 部品の性質から `gen_draw: False` を外すと、T47 が『❌ T47』で落ちる |
| `b111_ts_pos_excludes_current.sh` | #3 | 部品の式の最小からいまのバーを外すと、T47 が『❌ T47』で落ちる |
| `b112_stage_warm_not_extended.sh` | #4 | `stage_warm` が余白を延ばさない形にすると、T47 が『❌ T47』で落ちる |
| `—` | #5・#6・#7・#8・#9・#10・#11・#12・#13・#14 | 壊すプログラムは付けない（既存の突き合わせ。式の壊し方は #3 の b111 が測る） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

| # | リスク | どうするか |
|---|---|---|
| 1 | `condition_parts_diag.py` の時間が分からない | 走らせる前に worklog から過去の実測を探す。無ければ まこさんに報告してから走らせる（恒久61・62番） |
| 2 | 窓 52,596本の rolling が遅い | pandas の rolling の最小・最大は窓の長さによらず1回の通し。H2 と自己テストの時間で確かめる |
| 3 | 値決め窓の先頭の6か月ぶんは動く線が値なしになる | 実行データは2021年から在り、値決め窓は2024-03 から＝先頭の前に6か月以上の足が在る（periods.py の値決め窓）。値なしのバーは条件が不成立になるだけ |
| 4 | 動く線の閾値 q50 が「範囲の下の方」より上になる | 決めてほしいこと1。M2-F-13 の前に決める |
| 5 | `gen_regime_kb.py` を当てる道具で当てられない | 承認の後に私が Edit ツールで実装の指示 18〜22 と同じ文字を書く。書いた後に `--selftest` と `--verify` を走らせる |
| 6 | 組む側の本走の余白が延びて、本走の土台の数字（`_run_baseline`）が前の走行と少し違う | 動く線を使う走行の前提として受け入れる（まこさん決定 C）。恒等の走行は `WARM` のままなので、直す前と後の確かめには使える |
| 7 | M2-F-2 で段を測る道具の余白を直し忘れる | 記録の段で、m2_todo.json の M2-F-2 の注意に「stage_warm を使う」を1行 足す |
| 8 | 窓 52,596本の rolling の最小・最大は、窓の中に値なし（NaN）が1本でも在ると値なしを返す（pandas の既定 min_periods＝窓の長さ）。材料の列の途中に値なしが在ると、その後の6か月が黙って値なしになる | 実装の後、本走の余白で読んだ値決め窓・確認窓で、BB幅 の動く線の材料の値なしの本数を数えて記録する。窓の始まりの後に値なしが在れば止まって まこさんに出す |

### 6-3 見積もり

| 何 | 見込み | 根拠 |
|---|---|---|
| コードの直し（当てる道具で当てる20件・Edit で書く5件・壊すプログラム4本） | 30分 | ★測っていない。当てる処理は道具が数秒で終わる |
| 走らせて確かめる（自己テスト2本・突き合わせ・表・材料の文書・恒等3本・G2・H2） | 約20分（突き合わせの時間を除く） | 4-14 |
| 壊すプログラム4本を測る | 約23分 | 1本 約5分40秒 × 4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

**① 真因（root cause）**＝①法則 R6 の根拠の逐語は「直近6か月の範囲の中で下の方」＝直近の窓の中の位置を求めているのに、M2-E で段の候補を作ったとき、閾値の作り方を値決め窓で1回だけ決める分位（固定の線）の1通りにし、窓つきの前処理を段2c に付ける道を作らなかったことです。②元データの前処理の欄を、段2a の abs のために「部品の名前の文字だけ」の形で作り、窓の本数を書く欄を持たせなかったことです（監査 CP39 の A6-b）。③範囲の中の位置を出す前処理の部品が、実行器に1つも無かったことです（在るのは順位・ばらつき・最大・最小）。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。動くのは、場面の判定の段2c の候補（BB幅 の動く線が増える）です。それが判定の成績と net にどう効くかは、M2-F（段2c を測る＝M2-F-13）と M2-L で測ります。

**③ root か symptom か**＝root です。①固定の線の分位を動かして「下の方」らしくする形は、直近の窓の中の位置という法則の求めるものを持たない symptom の直しです。この設計は、窓の中の位置を出す部品と、元データに窓を書く欄と、段2c に付ける道の3つを作ります。②窓の長さは逐語から元データに書き、コードに直書きしません。③乱数の道を広げないよう、部品の性質表で入口の道から外します。

**④ ベースアップ**＝外の検索を2026-09-27 に行いました（WebSearch 3本・WebFetch 3本・worklog 20260927 §5-9）。①StockCharts「Stochastic Oscillator (Fast, Slow, and Full)」の本文で %K の式「%K = (Current Close - Lowest Low)/(Highest High - Lowest Low) * 100」と「The Stochastic Oscillator measures the level of the close relative to the high-low range over a given period.」を開いた。②StockCharts「Bollinger Band Squeeze」の本文で「Ideally, BandWidth should be near the low end of its six-month range.」を開いた。③StockCharts「Bollinger BandWidth」の本文には six-month の文が無く、「an eight- to 12-month chart」の文が在ると確かめた（窓にはしない＝やらないこと）。④TradingView Pine の `ta.stoch(source, high, low, length)` を業界の同じものとして挙げた（リファレンスの本文の式は開けていない）。読むもの宣言（`design_read_plan.md`・まこさんの OK 2026-09-27「１，２どちらもOK」「OK」）の24件を Read tool で開きました（worklog 20260927 §5-2・§5-6）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

この工事に、疑似シミュから取った値は1つもありません。窓の月の数 6 は法則 R6 の逐語、1か月の日数 365.25÷12 は暦の平均、5分は要件 H7 と実行データの足です。閾値は既存の分位の1点のままです。

### 7-3 変更の単位（H16）

「段2c の BB幅 に、法則 R6 の動く線を足す」の1つです。部品 ts_pos・元データの欄 pre_win・組む側の候補の作り方・表と突き合わせの道具は、その1つを作るための部品です。H1〜H15 と審判整合（群2）は非該当です（売買のロジックにも審判にも触れないため。H2 と H6 は 4-6 で照らしました＝rolling は過去だけを見て、位置は 0〜1 の比）。過去に取りやめた失敗の再演か＝当たりません（乱数のくじ引きの再演を避けるため、部品を乱数の道の外に置きます）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | この工事は乱数を1つも足しません。新しい部品は入口の案を乱数で作る道の外に置き（`gen_draw: False`）、段2c の候補は元データと成績表の順位から決まった並びで作ります。番人の見本も決まった並びです。 |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 窓の月の数は法則 R6 の逐語 six-month の1つで、私が並べた点の一覧ではありません。動く線は固定の線と別の候補として足すだけで、既存の探す範囲（材料カタログの最小〜最大・分位の範囲）を狭めません。 |

### 7-4 塞げないもの

| 問い | 塞げないこと |
|---|---|
| **本走（run_main）の束が動く線を実際に使うか** | 使いません。3枠目の順位は案の番号から決まり（regime_draw_order）、動く線は段2c の 262位より後ろに並ぶので、届くのは案の番号 5,994,822番（C(263,3)×2）より後ろです。動く線を測るのは M2-F-13 の道具で、その余白は M2-F-2 で直します |
| **動く線と固定の線のどちらが良い判定か** | この工事では分かりません。判定の成績は M2-F-13 で、net は M2-L で測ります |
| **動く線の閾値 q50 が「範囲の下の方」を表しているか** | いまは固定の線と同じ分位の1点です。範囲の中の点にするかは まこさんが決めます（決めてほしいこと1） |
| **実行データが5分足でなくなったとき** | 窓の本数の計算（`pre_win_bars`）は5分足を前提にします。実行データの足を変えるときは、この計算も直します |
| **TradingView Pine の `ta.stoch` の式** | リファレンスの本文の式は開けていません。式の出どころは StockCharts の本文です |
| **この道具と壊すプログラムそのものを書き換えられたら** | 書き換えれば無効にできます。承認で凍結され、差分は git に出ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認済みで凍結されているため） |
| **完成の条件のうち、壊すプログラムを持たない行（#5〜#14）は、いつ閉じたと言えるか** | 承認のプログラムは、壊すプログラムの欄が空の行を「済」にしません。これらの行は、実装の監査が同じコマンドを本物で走らせ直した出力で閉じたとします。表の状態の欄は「未着手」のまま残ります |

### 7-5 §4.6 ハード制約の照合

<!-- ACC_CHECKLIST_START hash=cb5f35c3aee2bdd1 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

- 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記）
- 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine`
- 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ
- 【群1】① 真因（root cause・損/不足の構造的原因）
- 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか）
- 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由）
- 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止）
- 【群1】変更は 1レバーか（複数混ぜない）
- 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行）
- 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設
- 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc
- 【群1】H16 1変更・過去失敗の不再演
- 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③）
- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。**★触る関数の一覧は、実装の後に確定させます**＝`verify_design_contract.py --write` の出力で置き替えます。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 段2c の候補に、BB幅 の固定の線と同じ本数の動く線（材料に ts_pos・窓 52,596本）が在り、固定の線の後ろに並ぶ（番人 T47 の③） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 動く線を作る分岐を止めると、T47 が『❌ T47』で落ちる | `b109_moving_line_not_built.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝段2c の候補に動く線を作る分岐を止めると、T47 が「段2c の候補に動く線が1本も無い」で落ちた |
| 2 | 部品 ts_pos は、入口の案を乱数で作る道の一覧に入らない（番人 T47 の①） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 部品の性質から `gen_draw: False` を外すと、T47 が『❌ T47』で落ちる | `b110_ts_pos_in_random_draw.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝部品 ts_pos の「乱数の道で引かない」印を外すと、T47 が「入口の案を乱数で作る道の一覧に ts_pos が入っている」で落ちた |
| 3 | 部品 ts_pos の既知答え（直近5本の最小〜最大の中の位置・いまのバーを含める・幅0は値なし）が合う（番人 T47 の②） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | 部品の式の最小からいまのバーを外すと、T47 が『❌ T47』で落ちる | `b111_ts_pos_excludes_current.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝部品 ts_pos の最小からいまのバーを外すと、T47 が「既知答えと違う」で落ちた |
| 4 | 動く線を使う走行（組む側の本走）の余白が「いまの余白＋6か月」＝60日＋182.625日になる（番人 T47 の⑤） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | 実経路 | `stage_warm` が余白を延ばさない形にすると、T47 が『❌ T47』で落ちる | `b112_stage_warm_not_extended.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝動く線を使う走行の余白を延ばさない形にすると、T47 が「余白が 60日＋6か月にならない」で落ちた |
| 5 | 実行器の ts_pos と、突き合わせの道具の独立の実装が、実データで1バーも違わない | `python3 scripts/priority_rebuild/condition_parts_diag.py` | 実経路 | 壊すプログラムは付けない（既存の突き合わせ。式の壊し方は #3 の b111 が測る） | `—` | — | **未着手** |
| 6 | 実行器の自己テストが全部 通る | `python3 scripts/priority_rebuild/engine_tuner_exec.py --selftest` | 実経路 | 壊すプログラムは付けない（既存の自己テスト） | `—` | — | **未着手** |
| 7 | §2.2-0 の表の段2c の BB幅 の行に、動く線の前処理が出る | `grep -c 'ts_pos（6か月・動く線）' .claude/ratchet/engine_tuner_milestones2.md` | 実経路 | 壊すプログラムは付けない（読むだけの数え上げ。0件なら未達） | `—` | — | **未着手** |
| 8 | §2.2 の表を作る道具の検出が通る（読むための道具＝恒久71番の線引きで、動くことを1回 確かめるだけ） | `python3 ../../.claude/tools/gen_regime_kb.py --verify all` | 実経路 | 壊すプログラムは付けない（既存の検出） | `—` | — | **未着手** |
| 9 | 材料の文書が作り直されている（前処理の一覧の数が実物と合う） | `python3 scripts/priority_rebuild/gen_materials.py --verify` | 実経路 | 壊すプログラムは付けない（既存の照合） | `—` | — | **未着手** |
| 10 | 材料の文書の番人が通る（T17＝前処理の数が実物と合う） | `python3 scripts/priority_rebuild/gen_materials.py --selftest` | 実経路 | 壊すプログラムは付けない（既存の番人） | `—` | — | **未着手** |
| 11 | 直す前と後で結果が同じか確かめる走行のうち、S2 が変わらない | `python3 scripts/priority_rebuild/engine_tuner_exec.py --identity` | 実経路 | 壊すプログラムは付けない（既存の恒等の仕組み） | `—` | — | **未着手** |
| 12 | 直す前と後で結果が同じか確かめる走行のうち、L1 が変わらない（md5 が同じ） | `python3 scripts/priority_rebuild/engine_tuner_exec.py --identity-l1` | 実経路 | 壊すプログラムは付けない（既存の恒等の仕組み） | `—` | — | **未着手** |
| 13 | 直す前と後で結果が同じか確かめる走行のうち、S1 が変わらない（md5 が同じ） | `python3 scripts/priority_rebuild/engine_tuner_exec.py --identity-s1` | 実経路 | 壊すプログラムは付けない（既存の恒等の仕組み） | `—` | — | **未着手** |
| 14 | 型の表が変わらず、G2 の見本が期待どおり | `python3 scripts/priority_rebuild/gen_signal_families.py --verify` | 実経路 | 壊すプログラムは付けない（既存の G2） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

<!-- ACC_CODEREF_START hash=68818c40decd12b6 gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/engine_tuner_gen.py`

| 触る関数 | 定義の行 |
|---|---|
| `pre_win_bars` | （この関数は実物に無い） |
| `stage_warm` | （この関数は実物に無い） |
| `build_stage_candidates` | 2775 |
| `stage_candidates` | 2472 |
| `_EXEC_BAR_MIN` | （この関数は実物に無い） |
| `pre_win` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 158件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

<!-- ACC_SPEC_START hash=c86afdf3879cc4cb gen_acceptance.py が自動生成＝手で書き換えない -->
**★この節はプログラムが作ります（手で書き換えない）。**出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "impl_functions": {
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "<モジュール直下>",
      "_make_cond",
      "stage_candidates",
      "pre_win_bars",
      "stage_warm",
      "build_stage_candidates",
      "selftest",
      "run_main"
    ],
    "scripts/priority_rebuild/engine_tuner_exec.py": [
      "<モジュール直下>",
      "pre_ops",
      "_apply_pre"
    ],
    "scripts/priority_rebuild/condition_parts_diag.py": [
      "<モジュール直下>",
      "p_ts_pos",
      "_cases"
    ],
    "../../.claude/tools/gen_regime_kb.py": [
      "expand_stage",
      "build_stage"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数。`pre_win_bars`・`p_ts_pos` は新設。定数 `_EXEC_BAR_MIN`・部品の一覧 `MATERIAL_PRE`・`_PRE_PARTS` はモジュール直下で数える。照合A は commit 済みの版（HEAD）との差で数える＝直すファイルの差は0（なぜ作るかの11行目）。",
  "self_check_calls": [
    "pre_win_bars",
    "stage_warm",
    "build_stage_candidates",
    "stage_candidates",
    "_EXEC_BAR_MIN",
    "pre_win"
  ],
  "_self_check_calls の意味": "7-7 の表に出す engine_tuner_gen.py の名前。`pre_win_bars`・`_EXEC_BAR_MIN`・`pre_win` は この工事で新しく書くので、実装の後に在る。",
  "must_use": {
    "build_stage_candidates": [
      "stage_candidates",
      "pre_win_bars"
    ],
    "stage_warm": [
      "stage_candidates",
      "pre_win_bars"
    ],
    "run_main": [
      "stage_warm"
    ],
    "selftest": [
      "pre_win_bars",
      "build_stage_candidates",
      "stage_warm"
    ]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "組む側が外から読む一覧（法則・成績表・範囲の鍵・印）の形は、この工事で変えない。§2.2 の元データに欄 pre_win を足すが、その照らしは gen_regime_kb.expand_stage が行い（fail-closed）、番人 T47 が振る舞いで測る。",
  "generated_from": {
    "impl_functions": "設計の段で、中身を直す関数と新しく作る関数を書いた（HEAD との差が0なのを git で確かめた）",
    "must_use": "直した後に呼ぶ名前（4-3・4-18）",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
 "public_functions": {
  "load_limits": [],
  "HoldRangeError": [],
  "resolve_hold_range": [
   "HoldRangeError"
  ],
  "hold_bars": [
   "HoldRangeError"
  ],
  "material_pool": [],
  "material_ranges": [
   "load_limits"
  ],
  "param_in_range": [
   "material_ranges"
  ],
  "draw_param": [
   "material_ranges"
  ],
  "assert_provenance": [
   "SampleError",
   "material_ranges",
   "param_in_range",
   "q_range_of"
  ],
  "assert_roles": [
   "SampleError"
  ],
  "assert_exit_roles": [
   "SampleError"
  ],
  "validate_drawn": [
   "strip_marks"
  ],
  "strip_marks": [],
  "int_range_of": [],
  "draw_int": [
   "int_range_of"
  ],
  "num_range_of": [],
  "draw_num": [
   "num_range_of"
  ],
  "ladder_min_frac": [],
  "max_ladder_steps": [
   "ladder_min_frac",
   "num_range_of"
  ],
  "q_range_of": [],
  "quantile_list": [
   "q_range_of"
  ],
  "draw_q": [
   "q_range_of"
  ],
  "q_in_range": [
   "q_range_of"
  ],
  "num_in_range": [
   "num_range_of"
  ],
  "SampleError": [],
  "load_signal_table": [],
  "load_material_ranking": [],
  "ranked_materials": [
   "load_material_ranking"
  ],
  "same_fn_family_pairs": [],
  "pair_allowed": [
   "same_fn_family_pairs"
  ],
  "load_exit_table": [],
  "ranked_groups": [
   "ranked_materials"
  ],
  "regime_draw_order": [
   "SampleError"
  ],
  "laws_for_scene": [
   "SampleError"
  ],
  "stage_candidates": [
   "SampleError"
  ],
  "drop_tfs_of": [
   "SampleError"
  ],
  "stage_limits_of": [
   "SampleError",
   "material_ranges",
   "q_range_of"
  ],
  "stage_tfs_of": [
   "SampleError",
   "drop_tfs_of",
   "stage_limits_of"
  ],
  "stage_lineages_of": [
   "SampleError"
  ],
  "build_stage_candidates": [
   "SampleError",
   "int_range_of",
   "material_ranges",
   "ranked_groups",
   "stage_candidates",
   "stage_limits_of",
   "stage_lineages_of",
   "stage_tfs_of"
  ],
  "build_width_candidates": [
   "SampleError",
   "material_ranges",
   "ranked_groups",
   "stage_candidates",
   "stage_tfs_of"
  ],
  "stage_keep_of": [
   "SampleError"
  ],
  "stage_counts": [
   "build_stage_candidates",
   "stage_keep_of"
  ],
  "sample_regime_build": [
   "SampleError",
   "build_stage_candidates",
   "build_width_candidates",
   "laws_for_scene",
   "regime_draw_order",
   "stage_candidates",
   "stage_counts",
   "stage_keep_of"
  ],
  "default_regime": [],
  "sample_structure": [
   "SampleError",
   "default_regime",
   "load_signal_table",
   "sample_regime_build"
  ],
  "recipe_hash": [
   "strip_marks"
  ],
  "write_kakikudashi": [],
  "structure_breakdown": [],
  "needed_qkeys": [],
  "build_qtable": [
   "needed_qkeys"
  ],
  "attach_materials": [],
  "pvalue_daily": [],
  "bh_select": [],
  "strat_gate": [],
  "Journal": [],
  "assert_known_exit_reason": [],
  "run_trial": [
   "strip_marks"
  ],
  "run_trial_guarded": [
   "run_trial"
  ],
  "reject_code": [],
  "zero_trade_gate": [],
  "per_day_gate": [
   "zero_trade_gate"
  ],
  "suggest_slot": [],
  "value_slots": [
   "hold_bars",
   "int_range_of",
   "num_range_of",
   "q_range_of"
  ],
  "apply_slots": [],
  "read_slots": [],
  "run_generation": [
   "Journal",
   "apply_slots",
   "bh_select",
   "build_qtable",
   "load_signal_table",
   "per_day_gate",
   "pvalue_daily",
   "quantile_list",
   "read_slots",
   "recipe_hash",
   "reject_code",
   "run_trial",
   "run_trial_guarded",
   "sample_structure",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "suggest_slot",
   "value_slots",
   "write_kakikudashi"
  ],
  "synth_df": [],
  "selftest_rank_demand": [
   "load_signal_table",
   "ranked_groups",
   "ranked_materials"
  ],
  "selftest": [
   "Journal",
   "apply_slots",
   "assert_known_exit_reason",
   "assert_provenance",
   "bh_select",
   "build_qtable",
   "build_stage_candidates",
   "build_width_candidates",
   "drop_tfs_of",
   "gate_matrix",
   "ladder_min_frac",
   "laws_for_scene",
   "lint_provenance",
   "load_exit_table",
   "load_limits",
   "load_material_ranking",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "max_ladder_steps",
   "needed_qkeys",
   "num_in_range",
   "pair_allowed",
   "param_in_range",
   "per_day_gate",
   "pre_run_gate",
   "pvalue_daily",
   "q_in_range",
   "q_range_of",
   "quantile_list",
   "ranked_groups",
   "ranked_materials",
   "read_slots",
   "regime_draw_order",
   "reject_code",
   "resolve_hold_range",
   "run_generation",
   "run_trial_guarded",
   "sample_regime_build",
   "sample_structure",
   "selftest_rank_demand",
   "stage_candidates",
   "stage_counts",
   "stage_keep_of",
   "stage_lineages_of",
   "stage_tfs_of",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "synth_df",
   "validate_drawn",
   "value_slots",
   "verify_provenance",
   "zero_trade_gate"
  ],
  "pre_run_gate": [],
  "run_main": [
   "assert_known_exit_reason",
   "hold_bars",
   "load_limits",
   "material_pool",
   "pre_run_gate",
   "resolve_hold_range",
   "run_generation"
  ],
  "main": [
   "gate_matrix",
   "lint_provenance",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "run_main",
   "sample_structure",
   "selftest",
   "selftest_rank_demand",
   "strip_marks",
   "structure_breakdown",
   "verify_provenance"
  ],
  "lint_provenance": [],
  "gate_matrix": [
   "apply_slots",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "resolve_hold_range",
   "run_trial_guarded",
   "sample_structure",
   "value_slots"
  ],
  "verify_provenance": [
   "load_limits",
   "load_signal_table",
   "resolve_hold_range"
  ]
 },
 "constants": {
  "PARAM_SRC": "_param_src",
  "Q_SRC": "_q_src",
  "NUM_SRC": "_num_src",
  "LIN_SRC": "_lineage_src",
  "ATTACH_CALLS": 0
 },
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->
