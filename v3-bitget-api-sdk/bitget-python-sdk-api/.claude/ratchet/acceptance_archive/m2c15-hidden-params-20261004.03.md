<!-- ARC iter="m2c15-hidden-params-20261004" -->

# 設計書｜指標の修正の2つ目の工事＝パラメータを、名前に出さない引数で受け取る形にする。M2-C-15

TARGET: scripts/priority_rebuild/indicator_reference_diag.py, scripts/priority_rebuild/observe_config.json, scripts/priority_rebuild/observe_diag.py, .claude/breaks/b128_k1_copc_back_in_ao_loop.sh, .claude/breaks/b132_hidden_param_not_passed.sh, .claude/breaks/b133_cksp_mixed_set.sh, .claude/breaks/b134_ao_name_with_value.sh, .claude/breaks/b135_rci_mako_gone.sh, .claude/breaks/b136_insp2_bar_close_dropped.sh
NEW_FILE: .claude/breaks/b132_hidden_param_not_passed.sh, .claude/breaks/b133_cksp_mixed_set.sh, .claude/breaks/b134_ao_name_with_value.sh, .claude/breaks/b135_rci_mako_gone.sh, .claude/breaks/b136_insp2_bar_close_dropped.sh
MODEL: .claude/breaks/b131_industry_map_prev_pivot_gone.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2c15-hidden-params-20261004/ok_ao_a_20261004`・`m2c15-hidden-params-20261004/ok_r2_20261006`・`m2c15-hidden-params-20261004/ok_readplan_cksp_c_20261004`・`m2c15-hidden-params-20261004/okd_r2_20261006`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-hidden-params-20261004/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-hidden-params-20261004 --write`。検出＝`--work m2c15-hidden-params-20261004 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=1186d2eb411dc7a2 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2c15-hidden-params-20261004/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2c15-hidden-params-20261004/ok_ao_a_20261004.txt`（まこさんの発言）・`verbatim/m2c15-hidden-params-20261004/ok_r2_20261006.txt`（まこさんの発言）・`verbatim/m2c15-hidden-params-20261004/ok_readplan_cksp_c_20261004.txt`（まこさんの発言）・`verbatim/m2c15-hidden-params-20261004/okd_r2_20261006.txt`（まこさんが OK した CC の文）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝861 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_ao_a_20261004` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_r2_20261006` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_readplan_cksp_c_20261004` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r2_20261006` | V01〜V05（5 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r2_20261006` | V06〜V23（18 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V24〜V29（6 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V30〜V34（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V35〜V49（15 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V50〜V56（7 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V57〜V65（9 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V66〜V73（8 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V74〜V75（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V76〜V77（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V78〜V82（5 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V83〜V84（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V85〜V86（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V87〜V92（6 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V93〜V101（9 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V102〜V107（6 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V108〜V109（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V110〜V111（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V112〜V113（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V114〜V119（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V120〜V684（565 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V685〜V695（11 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V696〜V702（7 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V703〜V711（9 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V712〜V718（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V719〜V720（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V721〜V722（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V723〜V727（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V728〜V738（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V739〜V759（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V760〜V768（9 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V769〜V853（85 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_r2_20261006` | V854〜V857（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
指標の修正の2つ目の工事です。指標が、パラメータを受け取れる状態にします。中身は4つです。①資料のパラメータを受け取っていない指標を、パラメータを「名前に出さない引数」で受け取る形にする（何も渡さなければ今と同じ計算。名前も種類の数も変えない）。傾きの比べる本数も同じ形にする（H-1）。②CKSP の値の組を、TradingView の形にそろえる（まこさん「２はC」・H-2）。③151回目に名前に値が入った EMA の傾きと、値違いの列を足した AO を、名前に値を入れない形へ戻す（AO は、まこさん「A」・H-3）。④RCI を「使う」に保つ番人と、検査2 の上位足のずらしの確かめを守る番人を足す（H-4）。列の値が変わるのは、CKSP の2列だけです。名前が変わるのは、EMA の傾きと AO だけです。探す側（engine_tuner）へつなぐ直しは、この工事に入れません（工事2）。最後に表を作り直し、型の表を再承認していただき、自己テスト・G2・H2 を取り直します。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 名前に出さない引数を受け取る登録（HWMA の例・H-1） | `grep -n -F '_pta6.hwma(close=d.close' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、係数を渡さずに呼んでいる。実装の後は、受け取った係数を渡している | 1152:_reg("close vs HWMA%", "close vs HWMA%", True, lambda d: (d.close / _pta6.hwma(close=d.close) - 1) * 100)（終了コード 0） |
| CKSP の呼び方（H-2） | `grep -n -F '_pta6.cksp(' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、高値・安値・終値だけを渡して呼ぶ。実装の後は、tvmode=True と、受け取った引数を渡す | 647:    return _pta6.cksp(high=d.high, low=d.low, close=d.close)（終了コード 0） |
| EMA の傾きの登録（H-3） | `grep -n -F '_reg("EMA傾き"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、名前の型の後ろに、比べる本数を入れるかっこが在る。実装の後は、無い | 811:_reg("EMA傾き", "EMA{}傾き%({})", True, lambda d, n, k: d.close.ewm(span=n, adjust=False).mean().pct_change(k) * 100)（終了コード 0） |
| AO の登録（H-3） | `grep -n -F '_reg("AO%"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、名前の型に、本数を入れるかっこが在る。実装の後は、無い | 983:_reg("AO%", "AO%({},{})", True, lambda d, f_, s_: _pta6.ao(high=d.high, low=d.low, fast=f_, slow=s_) / d.close * 100)（終了コード 0） |
| 名前に値を出すための設定（H-3） | `grep -n -e ema_slope_lookbacks -e ao_params v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json` | 実装の前は、在る。実装の後は、無い | 136: "ema_slope_lookbacks": [ ⏎ 139: "_ema_slope_lookbacks": "傾き（EMA・ほかの移動平均）を何本前と比べるか（監査 CP60）。5 は直す前の決め打ちと同じ値＝列の値は変わらない。広げるのは まこさんが recipes/search_limits.json の material_param_ranges に書く（CC は数字を作らない）。", ⏎ 161: "ao_params": [ ⏎ 167: "_ao_params": "AO% の教科書の期間（TradingView の逐語 lengthAO1=input(5…)・lengthAO2=input(34…)・監査 CP60）。",（終了コード 0） |
| この工事の番人（H-4） | `grep -n -F '_insp_hidden_params' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 実装の前は、無い。実装の後は、番人の関数と、軽い口からの呼び出しが在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=8faab679aa44dc33 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**探す指標＝印がオンの 145種**（印を切り替えると、この一覧も設計も変わります）。

```
ADX・DI差・MACD線%・MACDヒスト%・MACDシグナル線%・RSI・ROC・Stoch%K・Stoch%D・MFI・CMF・OBV傾き・転換線・基準線・RCI・EMA傾き・ATR%・BB%b・BB幅・realized_vol・Donchian幅・volume_ratio・swing高値距離・swing安値距離・高値からの経過バー・安値からの経過バー・形スコア・W字・fractal高値距離%・fractal安値距離%・高値切り上げ幅%・安値切り上げ幅%・構造破断距離%・close vs EMA・close vs SMA・close vs VWAP・Keltner上・Keltner下・n本高値・n本安値・pivotPP・pivotR1・pivotS1・前期間pivotPP・前期間pivotR1・前期間pivotS1・fib位置・POC・VAH・VAL・MMI・S-Rタッチ1時間ATR・S-Rタッチ数・AO%・CCI・ER・KST・KSTシグナル・PPO・PPOシグナル・PPOヒスト・PVO・PVOシグナル・PVOヒスト・SMC_SWEEP・SQZ_ON・STC・STCstoch・StochRSI%K・StochRSI%D・TRIX・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル・TSIヒスト・UO・close vs ALMA%・close vs DEMA%・close vs FWMA%・close vs HILO%・close vs HMA%・close vs HT_TRENDLINE%・close vs HWMA%・close vs JMA%・close vs KAMA%・KAMA傾き%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs FAMA%・close vs MCGD%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA%・close vs SINWMA%・close vs SSF%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TSF%・close vs VIDYA%・close vs VWMA%・close vs WMA%・WMA傾き%・close vs ZLMA%・AROONU・AROOND・AROONOSC・CHOP・close vs CKSPl%・close vs CKSPs%・DPO%・close vs PMAX%・close vs PSAR%・PSAR加速・PSAR反転・close vs SAREXT%・VHF・VTXP・VTXM・EFI比・EOM比・NVI傾き・PVT傾き・MAD比・stdev%・close vs MEDIAN%・close vs ABER_ZG%・ABER位置・close vs ACCBL%・close vs ACCBU%・close vs CE_L%・close vs CE_S%・HWC位置・HWC幅%・MASSI・THERMO%・TR%・UI・HT_DCPHASE
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

［自動］成績表
<!-- ACC_RANKING_START hash=c3db5c4b748433d9 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`material_ranking.json`。

**成績表に載っている列の本数**（札＝強さ・先読み12・執行足より上の時間足だけ）

| 役割 | 上位足の列の本数 | 分離力の高い順に3本 |
|---|---|---|
| env | 1918 | THERMO比__1h（0.725）／TR%__1h（0.717）／CVI7__30m（0.714） |
| location | 1414 | S-Rタッチ数(144,0.0015)__10m（0.359）／S-Rタッチ1時間ATR(144,0.5,21)__10m（0.368）／S-Rタッチ1時間ATR(144,0.5,14)__10m（0.37） |
| sufficiency | 1528 | volume_ratio20__1h（0.757）／volume_ratio50__30m（0.749）／PVO(12,26,9)__15m（0.737） |
| trigger | 250 | TD_SEQ_UP__10m（0.602）／TD_SEQ_DN__15m（0.594）／TD_SEQ_DN__10m（0.589） |

**★この本数は、印がオンの指標だけを数えたものではありません。**組む側は `ranked_materials` を通して引き、その関数が印オフの指標を落とします。

<!-- ACC_RANKING_END -->

### 2-4 いま乱数を使っている場所

［自動］実物のコード
<!-- ACC_RANDOM_START hash=83d74398b13a5184 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`engine_tuner_gen.py` を構文の木で読んだ結果（コメントの中の文字は数えません）。

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

**★乱数を外すのは、入口は M3、出口は M4 です（まこさんが決めた順番）。**この工事で外すかどうかは、設計の中身（4-0・4-20）に書きます。

<!-- ACC_RANDOM_END -->

## 3｜目標と、やらないこと

### 3-1 やらないこと（1件ずつ・理由と出どころ）

［手書き］やることの表の「3-1 やらないこと」
| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | engine_tuner へのつなぎ込み（名前に出さない引数を、探す側が範囲から渡す仕組み） | 指標の修正の範囲外＝工事2。この工事の後も、名前に出さない引数は、まだ探す対象にならない | まこさん「範囲外だよね」（next_step の手順7番）・worklog 20261004 §29 |
| 2 | 別の値を渡した列を、参照表で照らすこと | 探す側の工事で、別の値を使い始めるときに決める。今の参照表は、何も渡さないときの列だけを照らす | worklog 20261004 §35 |
| 3 | パラメータの最初の値と範囲を設定に書く直し（P-1・P-2）・教科書の版を足す直し（K-3）・帯の部品（B-1）・S1 の部品（S-1）・役割と閾値（R-1・T-1） | 後の回 | まこさん「分ける」（ok_split_20261004） |
| 4 | THERMO%・swing高値距離・swing安値距離・close vs VIDYA%・close vs ZLMA% を直すこと | その列の計算に使う、受け取っていない数のパラメータが無い（道具が、登録の文とライブラリの引数から判定した） | worklog 20261004 §35 |
| 5 | その列の計算に使われない引数を受け取ること（KST の signal・SQZ_ON の mom_length と mom_smooth・ABER_ZG の atr_length・StochRSI%K の %D の本数・POC の出来高の割合） | 値を変えても列が変わらない引数は、その指標のパラメータではない（154回目に道具が測って一覧に書いた） | worklog 20261004 §35・hidden_dead.json |
| 6 | オフの指標だけの登録（MMAR傾き・RAINBOW傾き・MEDIAN傾き%）の傾きの本数 | 今は対応しない | まこさん「オフは現状は対応しなくてよい」（2026-10-04） |
| 7 | RSI7・RSI9・RSI14・RSI21 と、V9 が使う指標の名前を変えること | そのままでよい | まこさん「そのままで良い」（req_v9_indicators_on_20261004） |
| 8 | 成績表（material_ranking.json）の作り直し | M2-D-8 で、まこさんの OK の後に走らせる | 読むもの宣言の入れないもの |
| 9 | 前の工事の設計書の古い数字（監査 CP61 の修正2） | 当てない | まこさん「修正１だけあてる」（2026-10-04） |
| 10 | 検査2 の確かめそのものを強くすること（今は、決まった2つの時刻だけを見る） | この工事は、今の確かめが外されないように守る番人を足すだけ。確かめを強くするのは、上位足のずらしを切り替えて比べる前（M2-F-10f）に決める | 監査 CP61 の Q10 の4点目・worklog 20261004 §50 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 目的の照合（purpose_check.md）の条件の書き方。この工事は探索の経路のファイル（observe_diag.py・observe_config.json）を書き替えるので、目的ゲートは「変えない」を書かせない。この工事は、探す側の仕組み（閾値・時間足・パラメータの探し方）を変えない | 事実だけを書く。閾値＝「CKSP の2列の値が変わるので、その列の閾値は新しい値の上で探すことになる（探し方は今のまま）」。時間足＝「検査2 の上位足のずらしの確かめを守る番人を足す（探す時間足の候補は今のまま）」。パラメータ＝「指標がパラメータを受け取れる状態になる。探す側が範囲から渡す仕組みは、この工事に入っていない（工事2）」 | enforce_purpose_gate.py の「変えない」の決まり・前の工事の 3-2 |
| 2 | 成績表（material_ranking.json）と名前の食い違い。AO は名前が変わるので、成績表の古い名前の行が引けなくなり、成績表を作り直す（M2-D-8）まで、AO は段の候補の順位に出ない。EMA の傾きは、成績表が持つ名前に戻るので、順位に戻る。CKSP は名前が同じで値が変わるので、成績表の CKSP の行は、直す前の値で測った成績のまま残る | このまま進める（成績表の作り直しは M2-D-8） | 道具が数えた名前の差（r2_names.json）・成績表の grep |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、指標が、パラメータを受け取れる状態にする直しです。**まこさんの6項目の3番（パラメータが、範囲から探されている）のための、指標の側の土台です。
**①いま何が起きているか。**
- 使う指標のうち 47種類の登録は、資料に在るパラメータを受け取っていません。ライブラリの関数を引数なしで呼ぶか、計算式の中に数字を直に書いています。engine_tuner からは、その値を変えられません。
- CKSP は、引数なしで呼んでいるので、値は本の形・ならし方は TradingView の形という、混ざった組で計算されています（ライブラリ cksp.py の作り）。
- EMA の傾きは、151回目に、比べる本数が名前に入りました。AO は、151回目に、値違いの列が1つ足されました。どちらも、まこさんが「やめてほしい」と言われた形です。
- 前の工事の RCI を「使う」にする直しと、検査2 の上位足のずらしの確かめは、外されても落ちる番人が在りません（監査 CP61 の Q10）。
**②この工事で何が変わるか。**
- H-1：47種類の登録が、パラメータを「名前に出さない引数」で受け取ります。何も渡さなければ、今と同じ計算をします。移動平均の傾きの比べる本数も、同じ形で受け取ります。
- H-2：CKSP を、TradingView の形にそろえます（まこさん「２はC」）。
- H-3：EMA の傾きの名前を、151回目の前の名前に戻します。比べる本数は、名前に出さない引数で受け取ります。AO は、名前を AO% の1列にします（まこさん「A」）。2つの本数は、名前に出さない引数で受け取ります。何も渡さないときは、ライブラリの既定＝教科書の値です。名前に値を出すための設定（ema_slope_lookbacks・ao_params）は外します。
- H-4：軽い口（--selftest-catalog）に、番人を5つ足します。1つ目は、名前に出さない引数が計算に届いているか。2つ目は、CKSP が TradingView の形か。3つ目は、EMA の傾きと AO の名前に値が無いか。4つ目は、参照表の RCI の行に mako の欄が在るか。5つ目は、検査2 が上位足のずらし bar_close の形も確かめているか、です。
**③数字はどう変わるか。**材料の一覧の本数は 577 列 → 576 列 です（AO が2列から1列になる分）。名前が変わるのは、下の囲みの名前だけです。列の値は、決まった式で作った値動きの上で、CKSP の2列を除く 574本が、直す前と同じでした（名前が変わった列は、対応する古い名前の列と比べました）。CKSP の2列は、ライブラリを TradingView の形で直接 呼んだ列と同じでした。
```
消える名前＝AO%(12,26)・AO%(5,34)・EMA200傾き%(5)・EMA20傾き%(5)・EMA50傾き%(5)・EMA9傾き%(5)
増える名前＝AO%・EMA200傾き%・EMA20傾き%・EMA50傾き%・EMA9傾き%
```
**④この工事に入れなかったもの。**名前に出さない引数を、探す側（engine_tuner）が範囲から渡す仕組みは、入れていません。指標の修正の範囲外で、工事2 です。この工事の後も、名前に出さない引数は、まだ探す対象になりません。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py・観察の道具の自己テスト（observe_diag.py --selftest）・表を作る道具（G-1）・G2・H2 を動かします。
**誰が結果を使うか。**
- 材料の一覧（observe_diag.py の build_catalog）は、engine_tuner が試す範囲（engine_tuner_gen.py の material_ranges）と、成績表を作る道具が読みます。
- 型の表（signal_families.json）・出口の型の表・組み立ての表・オン・オフの表は、engine_tuner が読みます。G-1 で作り直します。
- 成績表（material_ranking.json）は、この工事では作り直しません（3-1）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（observe_diag.py・indicator_reference_diag.py・observe_config.json・壊すプログラム b128）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：上の4つのファイルと、新しい壊すプログラム 5本。
- G-1：型の表・出口の型の表・組み立ての表・材料の文書・オン・オフの表。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 指標の名前に値を入れない・指標の数を増やさない | まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて、指標数を増やすという解決策はやめてほしい」 | パラメータは、名前に出さない引数で受け取ります。名前に値が入っていた EMA の傾きと AO は戻します。材料の一覧の本数は増えません |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 引数の既定は、None（ライブラリが自分の既定で決める）か、今の式に書いてある数字を道具が読んだ値です。CKSP の値の組は、まこさんの決定とライブラリの注記の値です |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 計算式は、受け取る引数が増えるだけです。何も渡さないときの列は、CKSP を除いて直す前と同じです。当てた後に H2 を取り直します |
| 乱数を使わない | 恒久67番 | 足すのは、引数の受け渡し・番人・壊すプログラムだけです |
| オフの指標を直さない | まこさん「オフは現状は対応しなくてよい」 | オフの指標だけの登録には触りません |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_diag.py の材料の登録（関数の外に並ぶ登録の文） | 登録の計算式が、パラメータを名前に出さない引数で受け取り、ライブラリの関数か自前の式へ渡す | 直す |
| observe_diag.py の自前の関数（_ck・_ps・_hw・_mama・_ab・_acb ほか・_vp_levels） | 受け取った引数を、ライブラリの関数へそのまま渡す。_ck は tvmode=True で呼ぶ。_vp_levels は、出来高の割合と区画の数を引数で受け取る | 直す |
| observe_diag.py の build_catalog | EMA の傾きを、名前に比べる本数を出さない形で作る。AO を、名前に本数を出さない1列で作る | 直す |
| observe_diag.py の _insp_hidden_params | 名前に出さない引数を1つずつ別の値にして、列が変わるかを確かめる番人 | 新設 |
| observe_diag.py の selftest_catalog（軽い口） | この工事の番人5つを足す | 直す |
| indicator_reference_diag.py | 参照表の EMA の傾きと AO の行を、新しい名前の型にする。参照の計算は、名前に本数が無いときの値で計算する | 直す |
| observe_config.json | 名前に値を出すための設定（ema_slope_lookbacks・ao_params）を外す | 直す |
| .claude/breaks の壊すプログラム | 新しい 5本は、番人ごとに、直しを壊すと決めた文で落ちるかを見る。前の工事の b128 は、探す文字（AO の行）が変わるので書き直す | 新設と直す |
- 触る関数は、全部の指示を当てる前と後の構文木を比べて、道具が数えました（下の囲み）。
```
observe_diag.py＝<モジュール直下>・_ab・_acb・_cel・_ck・_hw・_insp_hidden_params・_mama・_ps・_vp_levels・build_catalog・selftest_catalog／indicator_reference_diag.py＝<モジュール直下>・_ext_ao・_ext_ema_slope・_tb_ao・_tb_ema_slope
```

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。当てる道具は、全件を当てる前の実物で照らしてから、番号の順に当てます。1件でも合わなければ1件も当てません。
2. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます。この時点の G2 は、型の表を作り直す前なので、一致しない見込みです（EMA の傾きと AO の名前が変わるため。走らせて確かめてはいません。型の表を作り直す前に G2 を走らせる場面は、写しでは作れないためです）。G2 と H2 は、G-1 の後に取り直します。
3. 照合（verify_design_contract.py --diff）をかけます。新しい関数を足すので、設計書の SPEC と実物が食い違う見込みです。食い違ったら、gen_acceptance.py --write で設計書を作り直し、私が全部 読んで見直してから、承認の打ち直しを1回 お願いします。
4. 軽い口（--selftest-catalog）と壊すプログラムを走らせ、全体の自己テスト（--selftest）を1回 走らせて、出力をそのまま貼ります。
5. G-1：表を作り直します。型の表は、EMA の傾きと AO の名前が変わるので、まこさんに再承認していただきます。出口の型の表は、中身が変わったときだけ再承認していただきます。
6. G-2：G2 → H2（約5分）の順に取り直します。そのあと、実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝HWMA。いま close vs HWMA% は、ライブラリの関数を、係数を渡さずに呼んでいる（係数はライブラリの既定で決まり、engine_tuner からは変えられない）。この工事の後は、登録の計算式が、3つの係数を名前に出さない引数で受け取り、ライブラリへ渡す。何も渡さなければ、ライブラリの既定で計算するので、列は今と同じ。名前は close vs HWMA% のまま。番人は、係数を別の値にすると列が変わることを確かめる。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す値の範囲は、この工事では変えません。**範囲を作る関数は、材料の名前に出ている数字だけから範囲を作ります。名前に出さない引数を、探す側が範囲から渡す仕組みは、工事2 で作ります。EMA の傾きは、比べる本数が名前から消えるので、範囲の表の軸が2つから1つに戻ります。AO は、名前に数字が無くなるので、範囲の表の軸が無くなります。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**observe_config.json から外すもの。**
- ema_slope_lookbacks と、その注記。
- ao_params と、その注記。
コマンドの旗は増やしません。この工事の番人は、前の工事で作った軽い口（--selftest-catalog）に足します。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. 軽い口が全部 通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog。全体の自己テストも通る。コマンド＝python3 scripts/priority_rebuild/observe_diag.py --selftest。
2. 壊すプログラムが、全部 決めた番人で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
3. 材料の一覧に、EMA の傾きが比べる本数の無い名前で在り、AO が AO% の1列で在る（軽い口の番人が見る）。
4. 表を作り直した後に G2 が一致する。コマンド＝python3 scripts/priority_rebuild/gen_signal_families.py --verify。続けて H2 を取り直す。コマンド＝python3 scripts/priority_rebuild/leak_causality_diag.py。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 登録が、受け取った引数を計算に渡していない | 軽い口が「名前に出さない引数:」で落ちます |
| CKSP が、TradingView の形でない | 軽い口が「CKSP:」で落ちます |
| EMA の傾きか AO の名前に、値が入っている | 軽い口が「名前:」で落ちます |
| 参照表の RCI の行から、mako の欄が消える | 軽い口が「RCI:」で落ちます |
| 検査2 が、上位足のずらし bar_close の形を確かめなくなる | 軽い口が「検査2:」で落ちます |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**カタログの1件の形（名前・計算・向き）は変えません。**登録の計算式が受け取る引数が増えます。名前の型の {} の数は、EMA の傾きが2つから1つに、AO が2つから0に変わります。ほかの登録は変わりません。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**変えません。**

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察の道具の自己テスト（全体） | 124秒 | 写しで当てた後に走らせた実測（r2_draft_build.py の [6]） |
| 軽い口（--selftest-catalog） | 4秒 | 写しで当てた後に走らせた実測（r2_draft_build.py の [6]） |
| 材料の一覧 | 577 列 → 576 列 | 写しで数えた（r2_draft_build.py の [3]） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てるので、途中の状態は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**軽い口の番人は、落ちたときだけ「名前に出さない引数:」「CKSP:」「名前:」「RCI:」「検査2:」で始まる行を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **observe_diag.py と observe_config.json は H2 の対象、indicator_reference_diag.py は G2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **古い名前を持つのは、道具が作る表だけです。**型の表・観察の説明書・成績表です。法則・段の候補・出口の型の表の元データには、古い名前は在りません（grep で確かめました）。ほかのプログラムにも、古い名前と、外す設定の名前は在りません（grep で確かめました）。型の表と観察の説明書は、G-1 で作り直します。材料の文書の「決まった数字だけの一覧」の数も、設定を2つ外すので変わります（道具が数え直します）。
3. **成績表（material_ranking.json）は、この工事では作り直しません。**AO は、古い名前の行が引けなくなるので、成績表を作り直すまで、段の候補の順位に出ません。EMA の傾きは、成績表が持つ名前に戻るので、順位に戻ります。CKSP は、名前が同じで値が変わるので、成績表の行は、直す前の値で測った成績のまま残ります（3-2 に書きました）。
4. **前からの壊すプログラムが探す文字の数は、書き直す b128 を除いて、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
b104_atr1h_own_tf.sh・b105_atr1h_future_hour.sh・b106_atr1h_no_clip.sh・b107_atr1h_base_not_passed.sh・b108_atr1h_base_wrong_bars.sh・b122_obs_formula_copied.sh・b126_rank_resume_save_off.sh・b129_htf_bar_close_two_bars.sh・b131_industry_map_prev_pivot_gone.sh・b55_cyc_key_time_gone.sh・b56_one_min_csv_old.sh・b60_only5_with_others.sh・b61_insp5_bars_kind.sh・b63_tm_bitget_scope.sh・b64_tm_subdir.sh・b65_tm_badtail.sh
```
5. **参照表の照らし合わせは、何も渡さないときの列だけを照らします。**別の値を渡した列を照らすことは、今の参照表にはできません（3-1 に書きました）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| hidden_param_check.py（154回目に写しで確かめた道具） | 登録の文から、受け取っていない引数を読んで、受け渡しを足す形。番人の確かめ方（引数を1つずつ別の値にして列が変わるか） |
| observe_diag.py の selftest_catalog（前の工事の軽い口） | 番人を足す場所と、落ちたときの行の形 |
| 壊すプログラム b131 | 壊すプログラムの形 |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=ec1cb8850e1d0219 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 361行（_vp_levels・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
def _vp_levels(c, v, win=288):

~~~
直した後の文字:
~~~
def _vp_levels(c, v, win=288, va_pct=0.7, rows=24):

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:361「def _vp_levels(c, v, win=288):」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 373行（_vp_levels・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
        bins = np.linspace(cw.min(), cw.max(), 25)

~~~
直した後の文字:
~~~
        bins = np.linspace(cw.min(), cw.max(), rows + 1)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:373「bins = np.linspace(cw.min(), cw.max(), 25)」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 381行（_vp_levels・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
        while acc / tot < 0.7 and (lo > 0 or hi < last):

~~~
直した後の文字:
~~~
        while acc / tot < va_pct and (lo > 0 or hi < last):

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:381「while acc / tot < 0.7 and (lo > 0 or hi < last):」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 641〜642行（_mama・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
def _mama(d):
    return _pta6.mama(close=d.close)

~~~
直した後の文字:
~~~
def _mama(d, **kw):
    return _pta6.mama(close=d.close, **kw)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:641「def _mama(d):」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 646〜647行（_ck・CKSP を TradingView の形（10・1・9・rma）にそろえ、3つの値を名前に出さない引数で受け取る（まこさん「２はC」））
直す前の文字:
~~~
def _ck(d):
    return _pta6.cksp(high=d.high, low=d.low, close=d.close)

~~~
直した後の文字:
~~~
# ★CKSP（2026-10-04・まこさん「２はC」）＝TradingView の形（10・1・9・rma）にそろえる。直す前は引数なしで呼び、
#   値は本の形（10・3・20）・ならし方は TradingView の形（rma）という混ざった組だった（ライブラリ cksp.py:22〜35）。
def _ck(d, **kw):
    return _pta6.cksp(high=d.high, low=d.low, close=d.close, tvmode=True, **kw)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:646「def _ck(d):」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 650〜651行（_ps・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
def _ps(d):
    return _pta6.psar(high=d.high, low=d.low, close=d.close)

~~~
直した後の文字:
~~~
def _ps(d, **kw):
    return _pta6.psar(high=d.high, low=d.low, close=d.close, **kw)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:650「def _ps(d):」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 658〜659行（_ab・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
def _ab(d):
    return _pta6.aberration(high=d.high, low=d.low, close=d.close)

~~~
直した後の文字:
~~~
def _ab(d, **kw):
    return _pta6.aberration(high=d.high, low=d.low, close=d.close, **kw)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:658「def _ab(d):」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 662〜663行（_acb・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
def _acb(d):
    return _pta6.accbands(high=d.high, low=d.low, close=d.close)

~~~
直した後の文字:
~~~
def _acb(d, **kw):
    return _pta6.accbands(high=d.high, low=d.low, close=d.close, **kw)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:662「def _acb(d):」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 666〜667行（_cel・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
def _cel(d):
    return _pta6.ce(high=d.high, low=d.low, close=d.close)

~~~
直した後の文字:
~~~
def _cel(d, **kw):
    return _pta6.ce(high=d.high, low=d.low, close=d.close, **kw)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:666「def _cel(d):」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 670〜671行（_hw・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
def _hw(d):
    return _pta6.hwc(close=d.close, channel_eval=True)

~~~
直した後の文字:
~~~
def _hw(d, **kw):
    return _pta6.hwc(close=d.close, channel_eval=True, **kw)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:670「def _hw(d):」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 792〜795行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("Stoch%K", "Stoch%K{}", True, lambda d, n: 100 * (d.close - d.low.rolling(n).min())
     / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan))
_reg("Stoch%D", "Stoch%D{}", True, lambda d, n: (100 * (d.close - d.low.rolling(n).min())
     / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan)).rolling(3).mean())

~~~
直した後の文字:
~~~
_reg("Stoch%K", "Stoch%K{}", True, lambda d, n, smooth_k=1: (lambda k: k if smooth_k == 1 else k.rolling(smooth_k).mean())(100 * (d.close - d.low.rolling(n).min())
     / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan)))
_reg("Stoch%D", "Stoch%D{}", True, lambda d, n, smooth_k=1, d_n=3: (lambda k: (k if smooth_k == 1 else k.rolling(smooth_k).mean()).rolling(d_n).mean())(100 * (d.close - d.low.rolling(n).min())
     / (d.high.rolling(n).max() - d.low.rolling(n).min()).replace(0, np.nan)))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:792「_reg("Stoch%K", "Stoch%K{}", True, lambda d, n: 100 * (d.close - d.low.rolling(n).min())」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 811行（<モジュール直下>・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("EMA傾き", "EMA{}傾き%({})", True, lambda d, n, k: d.close.ewm(span=n, adjust=False).mean().pct_change(k) * 100)

~~~
直した後の文字:
~~~
_reg("EMA傾き", "EMA{}傾き%", True, lambda d, n, slope_n=5: d.close.ewm(span=n, adjust=False).mean().pct_change(slope_n) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:811「_reg("EMA傾き", "EMA{}傾き%({})", True, lambda d, n, k: d.close.ewm(span=n, adjust=False).mean().pct_change(k) * 100)」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 891〜894行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("close vs Keltner上%", "close vs Keltner上%({},{})", True, lambda d, n, k:
     (d.close / (d.close.ewm(span=n, adjust=False).mean() + k * _atr(d.high, d.low, d.close)) - 1) * 100)
_reg("close vs Keltner下%", "close vs Keltner下%({},{})", True, lambda d, n, k:
     (d.close / (d.close.ewm(span=n, adjust=False).mean() - k * _atr(d.high, d.low, d.close)) - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs Keltner上%", "close vs Keltner上%({},{})", True, lambda d, n, k, atr_n=14:
     (d.close / (d.close.ewm(span=n, adjust=False).mean() + k * _atr(d.high, d.low, d.close, atr_n)) - 1) * 100)
_reg("close vs Keltner下%", "close vs Keltner下%({},{})", True, lambda d, n, k, atr_n=14:
     (d.close / (d.close.ewm(span=n, adjust=False).mean() - k * _atr(d.high, d.low, d.close, atr_n)) - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:891「_reg("close vs Keltner上%", "close vs Keltner上%({},{})", True, lambda d, n, k:」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 935〜940行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("close vs POC%", "close vs POC%{}", True, lambda d, n:
     (d.close / _vp_levels(d.close, d.volume, n)[0] - 1) * 100)
_reg("close vs VAH%", "close vs VAH%{}", True, lambda d, n:
     (d.close / _vp_levels(d.close, d.volume, n)[1] - 1) * 100)
_reg("close vs VAL%", "close vs VAL%{}", True, lambda d, n:
     (d.close / _vp_levels(d.close, d.volume, n)[2] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs POC%", "close vs POC%{}", True, lambda d, n, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, rows=rows)[0] - 1) * 100)
_reg("close vs VAH%", "close vs VAH%{}", True, lambda d, n, va_pct=0.7, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, va_pct=va_pct, rows=rows)[1] - 1) * 100)
_reg("close vs VAL%", "close vs VAL%{}", True, lambda d, n, va_pct=0.7, rows=24:
     (d.close / _vp_levels(d.close, d.volume, n, va_pct=va_pct, rows=rows)[2] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:935「_reg("close vs POC%", "close vs POC%{}", True, lambda d, n:」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 982〜983行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る／AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」））
直す前の文字:
~~~
_reg("KST", "KST", True, lambda d: _pta6.kst(close=d.close).iloc[:, 0])
_reg("AO%", "AO%({},{})", True, lambda d, f_, s_: _pta6.ao(high=d.high, low=d.low, fast=f_, slow=s_) / d.close * 100)

~~~
直した後の文字:
~~~
_reg("KST", "KST", True, lambda d, roc1=None, roc2=None, roc3=None, roc4=None, sma1=None, sma2=None, sma3=None, sma4=None: _pta6.kst(close=d.close, roc1=roc1, roc2=roc2, roc3=roc3, roc4=roc4, sma1=sma1, sma2=sma2, sma3=sma3, sma4=sma4).iloc[:, 0])
_reg("AO%", "AO%", True, lambda d, fast=None, slow=None: _pta6.ao(high=d.high, low=d.low, fast=fast, slow=slow) / d.close * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:982「_reg("KST", "KST", True, lambda d: _pta6.kst(close=d.close).iloc[:, 0])」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 990行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("KSTシグナル", "KSTシグナル{}", True, lambda d, g_: _pta6.kst(close=d.close, signal=g_).iloc[:, 1])

~~~
直した後の文字:
~~~
_reg("KSTシグナル", "KSTシグナル{}", True, lambda d, g_, roc1=None, roc2=None, roc3=None, roc4=None, sma1=None, sma2=None, sma3=None, sma4=None: _pta6.kst(close=d.close, signal=g_, roc1=roc1, roc2=roc2, roc3=roc3, roc4=roc4, sma1=sma1, sma2=sma2, sma3=sma3, sma4=sma4).iloc[:, 1])

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:990「_reg("KSTシグナル", "KSTシグナル{}", True, lambda d, g_: _pta6.kst(close=d.close, signal=g_).iloc[:, 1])」
状態: 確定

#### 実装 17
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1026行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("SMC_SWEEP", "SMC_SWEEP", False, lambda d: _pta6.smc_sweep(open_=d.open, high=d.high, low=d.low, close=d.close))

~~~
直した後の文字:
~~~
_reg("SMC_SWEEP", "SMC_SWEEP", False, lambda d, length=None, wick_mult=None: _pta6.smc_sweep(open_=d.open, high=d.high, low=d.low, close=d.close, length=length, wick_mult=wick_mult))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1026「_reg("SMC_SWEEP", "SMC_SWEEP", False, lambda d: _pta6.smc_sweep(open_=d.open, high=d.high, low=d.low, close=d.close))」
状態: 確定

#### 実装 18
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1031行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("SQZ_ON", "SQZ_ON", False, lambda d: _pta6.squeeze(high=d.high, low=d.low, close=d.close).iloc[:, 1])

~~~
直した後の文字:
~~~
_reg("SQZ_ON", "SQZ_ON", False, lambda d, bb_length=None, bb_std=None, kc_length=None, kc_scalar=None: _pta6.squeeze(high=d.high, low=d.low, close=d.close, bb_length=bb_length, bb_std=bb_std, kc_length=kc_length, kc_scalar=kc_scalar).iloc[:, 1])

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1031「_reg("SQZ_ON", "SQZ_ON", False, lambda d: _pta6.squeeze(high=d.high, low=d.low, close=d.close).iloc[:, 1])」
状態: 確定

#### 実装 19
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1065〜1066行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("STC", "STC", True, lambda d: _stc_textbook(d.close)[0])
_reg("STCstoch", "STCstoch", True, lambda d: _stc_textbook(d.close)[1])

~~~
直した後の文字:
~~~
_reg("STC", "STC", True, lambda d, tcl=10, f_=12, s_=26, fac=0.5: _stc_textbook(d.close, tcl=tcl, f_=f_, s_=s_, fac=fac)[0])
_reg("STCstoch", "STCstoch", True, lambda d, tcl=10, f_=12, s_=26, fac=0.5: _stc_textbook(d.close, tcl=tcl, f_=f_, s_=s_, fac=fac)[1])

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1065「_reg("STC", "STC", True, lambda d: _stc_textbook(d.close)[0])」
状態: 確定

#### 実装 20
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1070〜1073行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n).iloc[:, 0])
_reg("StochRSI%D", "StochRSI%D{}", True, lambda d, n:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n).iloc[:, 1])

~~~
直した後の文字:
~~~
_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n, k=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k).iloc[:, 0])
_reg("StochRSI%D", "StochRSI%D{}", True, lambda d, n, k=None, d_=None:
     _pta6.stochrsi(close=d.close, length=n, rsi_length=n, k=k, d=d_).iloc[:, 1])

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1070「_reg("StochRSI%K", "StochRSI%K{}", True, lambda d, n:」
状態: 確定

#### 実装 21
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1082行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("UO", "UO", True, lambda d: _pta6.uo(high=d.high, low=d.low, close=d.close))

~~~
直した後の文字:
~~~
_reg("UO", "UO", True, lambda d, fast=None, medium=None, slow=None, fast_w=None, medium_w=None, slow_w=None: _pta6.uo(high=d.high, low=d.low, close=d.close, fast=fast, medium=medium, slow=slow, fast_w=fast_w, medium_w=medium_w, slow_w=slow_w))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1082「_reg("UO", "UO", True, lambda d: _pta6.uo(high=d.high, low=d.low, close=d.close))」
状態: 確定

#### 実装 22
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1108行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
    ("ALMA", lambda d, n: _pta6.alma(close=d.close, length=n, distribution_offset=0.15)),

~~~
直した後の文字:
~~~
    ("ALMA", lambda d, n, distribution_offset=0.15, sigma=None: _pta6.alma(close=d.close, length=n, distribution_offset=distribution_offset, sigma=sigma)),

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1108「("ALMA", lambda d, n: _pta6.alma(close=d.close, length=n, distribution_offset=0.15)),」
状態: 確定

#### 実装 23
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1111〜1112行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
    ("JMA", lambda d, n: _pta6.jma(close=d.close, length=n)),
    ("KAMA", lambda d, n: _pta6.kama(close=d.close, length=n)),

~~~
直した後の文字:
~~~
    ("JMA", lambda d, n, phase=None: _pta6.jma(close=d.close, length=n, phase=phase)),
    ("KAMA", lambda d, n, fast=None, slow=None: _pta6.kama(close=d.close, length=n, fast=fast, slow=slow)),

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1111「("JMA", lambda d, n: _pta6.jma(close=d.close, length=n)),」
状態: 確定

#### 実装 24
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1115行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
    ("MCGD", lambda d, n: _pta6.mcgd(close=d.close, length=n)),

~~~
直した後の文字:
~~~
    ("MCGD", lambda d, n, c=None: _pta6.mcgd(close=d.close, length=n, c=c)),

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1115「("MCGD", lambda d, n: _pta6.mcgd(close=d.close, length=n)),」
状態: 確定

#### 実装 25
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1121行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
    ("SSF", lambda d, n: _pta6.ssf(close=d.close, length=n)),

~~~
直した後の文字:
~~~
    ("SSF", lambda d, n, poles=None: _pta6.ssf(close=d.close, length=n, poles=poles)),

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1121「("SSF", lambda d, n: _pta6.ssf(close=d.close, length=n)),」
状態: 確定

#### 実装 26
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1125〜1126行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
    ("T3", lambda d, n: (lambda r: pd.Series(np.nan, index=d.index) if r is None
                         else r.reindex(d.index))(_pta6.t3(close=d.close, length=n))),

~~~
直した後の文字:
~~~
    ("T3", lambda d, n, a=None: (lambda r: pd.Series(np.nan, index=d.index) if r is None
                         else r.reindex(d.index))(_pta6.t3(close=d.close, length=n, a=a))),

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1125「("T3", lambda d, n: (lambda r: pd.Series(np.nan, index=d.index) if r is None」
状態: 確定

#### 実装 27
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1138行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
         lambda d, n, f=_mafn: (d.close / f(d, n) - 1) * 100)

~~~
直した後の文字:
~~~
         lambda d, n, f=_mafn, **kw: (d.close / f(d, n, **kw) - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1138「lambda d, n, f=_mafn: (d.close / f(d, n) - 1) * 100)」
状態: 確定

#### 実装 28
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1141行（<モジュール直下>・移動平均の登録が、受け取った引数を計算式へ渡す。傾きの比べる本数も名前に出さない引数で受け取る）
直す前の文字:
~~~
             lambda d, n, f=_mafn: f(d, n).pct_change(5) * 100)

~~~
直した後の文字:
~~~
             lambda d, n, f=_mafn, slope_n=5, **kw: f(d, n, **kw).pct_change(slope_n) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1141「lambda d, n, f=_mafn: f(d, n).pct_change(5) * 100)」
状態: 確定

#### 実装 29
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1148〜1149行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("close vs HILO%", "close vs HILO%", True, lambda d: (d.close / _pta6.hilo(high=d.high, low=d.low,
                                                                              close=d.close).iloc[:, 0] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs HILO%", "close vs HILO%", True, lambda d, high_length=None, low_length=None: (d.close / _pta6.hilo(high=d.high, low=d.low,
                                                                              close=d.close, high_length=high_length, low_length=low_length).iloc[:, 0] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1148「_reg("close vs HILO%", "close vs HILO%", True, lambda d: (d.close / _pta6.hilo(high=d.high, low=d.low,」
状態: 確定

#### 実装 30
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1152〜1154行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("close vs HWMA%", "close vs HWMA%", True, lambda d: (d.close / _pta6.hwma(close=d.close) - 1) * 100)
_reg("close vs MAMA%", "close vs MAMA%", True, lambda d: (d.close / _mama(d).iloc[:, 0] - 1) * 100)
_reg("close vs FAMA%", "close vs FAMA%", True, lambda d: (d.close / _mama(d).iloc[:, 1] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs HWMA%", "close vs HWMA%", True, lambda d, na=None, nb=None, nc=None: (d.close / _pta6.hwma(close=d.close, na=na, nb=nb, nc=nc) - 1) * 100)
_reg("close vs MAMA%", "close vs MAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 0] - 1) * 100)
_reg("close vs FAMA%", "close vs FAMA%", True, lambda d, fastlimit=None, slowlimit=None: (d.close / _mama(d, fastlimit=fastlimit, slowlimit=slowlimit).iloc[:, 1] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1152「_reg("close vs HWMA%", "close vs HWMA%", True, lambda d: (d.close / _pta6.hwma(close=d.close) - 1) * 100)」
状態: 確定

#### 実装 31
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1207〜1208行（<モジュール直下>・CKSP を TradingView の形（10・1・9・rma）にそろえ、3つの値を名前に出さない引数で受け取る（まこさん「２はC」））
直す前の文字:
~~~
_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d: (d.close / _ck(d).iloc[:, 0] - 1) * 100)
_reg("close vs CKSPs%", "close vs CKSPs%", True, lambda d: (d.close / _ck(d).iloc[:, 1] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 0] - 1) * 100)
_reg("close vs CKSPs%", "close vs CKSPs%", True, lambda d, p=None, x=None, q=None: (d.close / _ck(d, p=p, x=x, q=q).iloc[:, 1] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1207「_reg("close vs CKSPl%", "close vs CKSPl%", True, lambda d: (d.close / _ck(d).iloc[:, 0] - 1) * 100)」
状態: 確定

#### 実装 32
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1210行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
     lambda d: (d.close / _pta6.pmax(high=d.high, low=d.low, close=d.close) - 1) * 100)

~~~
直した後の文字:
~~~
     lambda d, length=None, multiplier=None: (d.close / _pta6.pmax(high=d.high, low=d.low, close=d.close, length=length, multiplier=multiplier) - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1210「lambda d: (d.close / _pta6.pmax(high=d.high, low=d.low, close=d.close) - 1) * 100)」
状態: 確定

#### 実装 33
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1212〜1214行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
     lambda d: (d.close / (lambda t: t.iloc[:, 0].fillna(t.iloc[:, 1]))(_ps(d)) - 1) * 100)
_reg("PSAR加速", "PSAR加速", False, lambda d: _ps(d).iloc[:, 2])
_reg("PSAR反転", "PSAR反転", False, lambda d: _ps(d).iloc[:, 3])

~~~
直した後の文字:
~~~
     lambda d, af0=None, af=None, max_af=None: (d.close / (lambda t: t.iloc[:, 0].fillna(t.iloc[:, 1]))(_ps(d, af0=af0, af=af, max_af=max_af)) - 1) * 100)
_reg("PSAR加速", "PSAR加速", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 2])
_reg("PSAR反転", "PSAR反転", False, lambda d, af0=None, af=None, max_af=None: _ps(d, af0=af0, af=af, max_af=max_af).iloc[:, 3])

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1212「lambda d: (d.close / (lambda t: t.iloc[:, 0].fillna(t.iloc[:, 1]))(_ps(d)) - 1) * 100)」
状態: 確定

#### 実装 34
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1218行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
     lambda d: (d.close / _pta6.sarext(high=d.high, low=d.low).abs() - 1) * 100)

~~~
直した後の文字:
~~~
     lambda d, startvalue=None, offsetonreverse=None, accelerationinitlong=None, accelerationlong=None, accelerationmaxlong=None, accelerationinitshort=None, accelerationshort=None, accelerationmaxshort=None: (d.close / _pta6.sarext(high=d.high, low=d.low, startvalue=startvalue, offsetonreverse=offsetonreverse, accelerationinitlong=accelerationinitlong, accelerationlong=accelerationlong, accelerationmaxlong=accelerationmaxlong, accelerationinitshort=accelerationinitshort, accelerationshort=accelerationshort, accelerationmaxshort=accelerationmaxshort).abs() - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1218「lambda d: (d.close / _pta6.sarext(high=d.high, low=d.low).abs() - 1) * 100)」
状態: 確定

#### 実装 35
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1261行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_reg("close vs ABER_ZG%", "close vs ABER_ZG%", True, lambda d: (d.close / _ab(d).iloc[:, 0] - 1) * 100)

~~~
直した後の文字:
~~~
_reg("close vs ABER_ZG%", "close vs ABER_ZG%", True, lambda d, length=None: (d.close / _ab(d, length=length).iloc[:, 0] - 1) * 100)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1261「_reg("close vs ABER_ZG%", "close vs ABER_ZG%", True, lambda d: (d.close / _ab(d).iloc[:, 0] - 1) * 100)」
状態: 確定

#### 実装 36
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1263〜1270行（<モジュール直下>・パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
     lambda d: (lambda a: (d.close - a.iloc[:, 2]) / (a.iloc[:, 1] - a.iloc[:, 2]))(_ab(d)))
_reg("close vs ACCBL%", "close vs ACCBL%", True, lambda d: (d.close / _acb(d).iloc[:, 0] - 1) * 100)
_reg("close vs ACCBU%", "close vs ACCBU%", True, lambda d: (d.close / _acb(d).iloc[:, 2] - 1) * 100)
_reg("close vs CE_L%", "close vs CE_L%", True, lambda d: (d.close / _cel(d).iloc[:, 0] - 1) * 100)
_reg("close vs CE_S%", "close vs CE_S%", True, lambda d: (d.close / _cel(d).iloc[:, 1] - 1) * 100)
_reg("HWC位置", "HWC位置", False, lambda d: _hw(d)["HWPCT"])
_reg("HWC幅%", "HWC幅%", False, lambda d: _hw(d)["HWW"] / d.close * 100)
_reg("MASSI", "MASSI", False, lambda d: _pta6.massi(high=d.high, low=d.low))

~~~
直した後の文字:
~~~
     lambda d, length=None, atr_length=None: (lambda a: (d.close - a.iloc[:, 2]) / (a.iloc[:, 1] - a.iloc[:, 2]))(_ab(d, length=length, atr_length=atr_length)))
_reg("close vs ACCBL%", "close vs ACCBL%", True, lambda d, length=None, c=None: (d.close / _acb(d, length=length, c=c).iloc[:, 0] - 1) * 100)
_reg("close vs ACCBU%", "close vs ACCBU%", True, lambda d, length=None, c=None: (d.close / _acb(d, length=length, c=c).iloc[:, 2] - 1) * 100)
_reg("close vs CE_L%", "close vs CE_L%", True, lambda d, length=None, multiplier=None: (d.close / _cel(d, length=length, multiplier=multiplier).iloc[:, 0] - 1) * 100)
_reg("close vs CE_S%", "close vs CE_S%", True, lambda d, length=None, multiplier=None: (d.close / _cel(d, length=length, multiplier=multiplier).iloc[:, 1] - 1) * 100)
_reg("HWC位置", "HWC位置", False, lambda d, na=None, nb=None, nc=None, nd=None, scalar=None: _hw(d, na=na, nb=nb, nc=nc, nd=nd, scalar=scalar)["HWPCT"])
_reg("HWC幅%", "HWC幅%", False, lambda d, na=None, nb=None, nc=None, nd=None, scalar=None: _hw(d, na=na, nb=nb, nc=nc, nd=nd, scalar=scalar)["HWW"] / d.close * 100)
_reg("MASSI", "MASSI", False, lambda d, fast=None, slow=None: _pta6.massi(high=d.high, low=d.low, fast=fast, slow=slow))

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1263「lambda d: (lambda a: (d.close - a.iloc[:, 2]) / (a.iloc[:, 1] - a.iloc[:, 2]))(_ab(d)))」
状態: 確定

#### 実装 37
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1368〜1369行（build_catalog・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る）
直す前の文字:
~~~
        for k in cfg["ema_slope_lookbacks"]:
            addf("EMA傾き", n, k)

~~~
直した後の文字:
~~~
        addf("EMA傾き", n)

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1368「for k in cfg["ema_slope_lookbacks"]:」
状態: 確定

#### 実装 38
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1472〜1473行（build_catalog・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」））
直す前の文字:
~~~
    for (f_, s_, g_) in cfg["macd_params"]:
        addf("AO%", f_, s_)

~~~
直した後の文字:
~~~
    for (f_, s_, g_) in cfg["macd_params"]:

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1472「for (f_, s_, g_) in cfg["macd_params"]:」
状態: 確定

#### 実装 39
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 1485〜1488行（build_catalog・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」））
直す前の文字:
~~~
    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。
    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。
    for (f_, s_) in cfg.get("ao_params", []):
        addf("AO%", f_, s_)

~~~
直した後の文字:
~~~
    # ★AO（2026-10-04・工事 m2c15-hidden-params-20261004・まこさん「A」）＝名前は AO% の1列。2つの本数は名前に出さない引数で受け取る
    #   （何も渡さないときはライブラリの既定＝教科書の 5・34）。
    addf("AO%")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:1485「# ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。」
状態: 確定

#### 実装 40
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6926〜6927行（selftest_atr1h・番人の関数 _insp_hidden_params を足す（名前に出さない引数が計算に届いているか））
直す前の文字:
~~~
        raise SystemExit(0)
    return ng



~~~
直した後の文字:
~~~
        raise SystemExit(0)
    return ng


def _insp_hidden_params() -> list:
    """名前に出さない引数（工事 m2c15-hidden-params-20261004・2026-10-04）が、その列の計算に届いているかを確かめる。

    登録の計算式が、名前の {} の数より多く受け取る引数（既定つき）を1つずつ別の値にして、列が変わらなければ報告する。
    移動平均の for で登録した種類は、計算式 f の側の引数も見る。値動きは決まった式で作る（相場のデータは使わない）。
    ★別の値（下の _alt）は確かめのために渡す値で、指標の設定ではない（今の値と違えばよい）。"""
    import hashlib
    import inspect
    _load_pta()
    n = 600
    t = np.arange(n)
    c = 100 + 5 * np.sin(t / 17.0) + 2 * np.sin(t / 5.0) + 1.5 * np.sin(t / 1.7) + 3 * np.sin(t / 41.0) + t * 0.01
    d = pd.DataFrame({"open": c - 0.2 * np.cos(t / 3.0), "high": c + 0.6 + 0.2 * np.sin(t / 7.0),
                      "low": c - 0.6 - 0.2 * np.cos(t / 11.0), "close": c, "volume": 1000 + 100 * np.sin(t / 13.0)},
                     index=pd.date_range("2026-01-01", periods=n, freq="5min"))

    def _h(s):
        return hashlib.sha256(np.asarray(s, dtype=float).tobytes()).hexdigest()
    _int = r"len|roc|sma|signal|tcl|medium|^p$|^q$|^fast$|^slow$|^f_$|^s_$"
    _alt = {"poles": 3, "phase": 50, "a": 0.5, "c": 0.5, "sigma": 4, "k": 5, "d_": 5, "fast": 5, "medium": 10, "slow": 20,
            "slowlimit": 0.1, "fastlimit": 0.3}
    pos = {}
    for nm, _f, _d in build_catalog(load_config()):
        fam, prm = find_material(nm)
        if fam is not None and fam not in pos:
            pos[fam] = tuple(prm)
    ng, seen = [], 0
    for fam, (tpl, _dr, fn) in MATERIAL_FAMILIES.items():
        P = pos.get(fam)
        if P is None or len(P) != tpl.count("{}"):
            continue
        ps = list(inspect.signature(fn).parameters.values())[1 + len(P):]

        def _numdef(p):                                  # 既定が None か数の引数だけ（文字・関数の既定は、数のパラメータではない）
            return p.default is None or (isinstance(p.default, (int, float)) and not isinstance(p.default, bool))
        kw = {p.name: p.default for p in ps if p.kind is not p.VAR_KEYWORD and p.name != "f" and _numdef(p)}
        fpar = inspect.signature(fn).parameters.get("f")
        if fpar is not None and callable(fpar.default) and any(p.kind is p.VAR_KEYWORD for p in ps):
            kw.update({p.name: p.default for p in list(inspect.signature(fpar.default).parameters.values())[2:] if _numdef(p)})
        if not kw:
            continue
        seen += 1
        base = _h(fn(d, *P))
        for k, v in kw.items():
            if v is not None:
                alts = [v + 2, v + 6] if isinstance(v, int) else [v + 0.1, v * 2 + 0.3]
            else:
                a1 = _alt.get(k, 7 if re.search(_int, k) else 0.05)
                alts = [a1, a1 * 2 + 1 if isinstance(a1, int) else a1 * 3]
            moved, raised = False, 0
            for alt in alts:
                try:
                    if _h(fn(d, *P, **{k: alt})) != base:
                        moved = True
                        break
                except Exception:                            # noqa: BLE001
                    raised += 1
            # ★別の値が全部 計算できなかった引数は数えない（数のパラメータではない＝登録の for が取り込んだ列の番号など）
            if not moved and raised < len(alts):
                ng.append(f"名前に出さない引数: {fam} の {k} を変えても列が変わらない（計算に届いていない）")
    if not seen:
        ng.append("名前に出さない引数: 受け取る登録が1つも無い")
    return ng



~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6926「raise SystemExit(0)」
状態: 確定

#### 実装 41
対象のファイル: scripts/priority_rebuild/observe_diag.py
直す箇所: 6979〜6980行（selftest_catalog・軽い口 selftest_catalog に、この工事の番人を足す）
直す前の文字:
~~~
    except ImportError:
        ng.append("検査10 が使う pandas-ta-classic が入っていない（requirements.txt の版で入れる）")

~~~
直した後の文字:
~~~
    except ImportError:
        ng.append("検査10 が使う pandas-ta-classic が入っていない（requirements.txt の版で入れる）")
    # ── 工事 m2c15-hidden-params-20261004 の番人（2026-10-04）──
    #  ⑥名前に出さない引数が、その列の計算に届いている
    ng += _insp_hidden_params()
    #  ⑦CKSP＝何も渡さない列が TradingView の形（まこさん 2026-10-04「２はC」。値はライブラリの注記「TV defaults=(10,1,9)」）
    _load_pta()
    _ck7 = _pta6.cksp(high=_sb3.high, low=_sb3.low, close=_sb3.close, p=10, x=1, q=9, tvmode=True)
    if not np.array_equal(_ck(_sb3).to_numpy(float), _ck7.to_numpy(float), equal_nan=True):
        ng.append("CKSP: 何も渡さない列が TradingView の形（10・1・9・rma）と違う")
    #  ⑧名前＝EMA の傾きと AO の名前に値が無い（まこさん 2026-10-04「指標名に閾値やパラメータの値を固定で入れて…やめてほしい」「A」）
    for _n8 in cfg["ema_periods"]:
        if f"EMA{_n8}傾き%" not in _nm_k1:
            ng.append(f"名前: EMA{_n8}傾き% がカタログに無い（名前に値が入った形に戻っている）")
    if "AO%" not in _nm_k1 or any(_x8.startswith("AO%(") for _x8 in _nm_k1):
        ng.append("名前: AO% が、値の無い名前の1列になっていない")
    #  ⑨RCI＝参照表の RCI の行に mako の欄が在る（無いと、表を作り直したときに「使わない」へ戻る）
    if not any(_e9["family"] == "RCI" and _e9.get("mako") for _e9 in iref.REFS):
        ng.append("RCI: 参照表の RCI の行に mako の欄が無い（「使う」から外れる）")
    #  ⑩検査2＝上位足のずらし bar_close の形も確かめている（前の工事の実装 3・4・5）
    import inspect as _in10
    if _insp_close_leak(shift=True, mode="bar_close"):
        ng.append("検査2: 上位足のずらし bar_close の形で誤検出する")
    for _fn10 in (_insp_resample, selftest):
        if 'mode="bar_close"' not in _in10.getsource(_fn10):
            ng.append(f"検査2: {_fn10.__name__} が、上位足のずらし bar_close の形を確かめていない")

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_diag.py:6979「except ImportError:」
状態: 確定

#### 実装 42
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 318行（_tb_ema_slope・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る）
直す前の文字:
~~~
    k = int(p[1])

~~~
直した後の文字:
~~~
    k = int(p[1]) if len(p) > 1 else 5      # 名前に本数が無い＝何も渡さないときの 5 本

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:318「k = int(p[1])」
状態: 確定

#### 実装 43
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 836行（_ext_ema_slope・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る）
直す前の文字:
~~~
    return e.pct_change(int(p[1])) * 100

~~~
直した後の文字:
~~~
    return e.pct_change(int(p[1]) if len(p) > 1 else 5) * 100

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:836「return e.pct_change(int(p[1])) * 100」
状態: 確定

#### 実装 44
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1066〜1068行（<モジュール直下>・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る）
直す前の文字:
~~~
_r(r"EMA(\d+)傾き%\((\d+)\)", "EMA傾き",
   "EMA の k 本前からの変化率%（k は設定ファイル ema_slope_lookbacks・engine_tuner が探すパラメータ）",
   "EMA は標準の漸化式。比べる本数は教科書でも利用者が決めるパラメータ（ChartSchool Slope「The number of days controls the period」）＝決め打ちしない（監査 CP60）",

~~~
直した後の文字:
~~~
_r(r"EMA(\d+)傾き%", "EMA傾き",
   "EMA の何本か前からの変化率%。比べる本数は名前に出さない引数（何も渡さないときは 5 本＝直す前の値）",
   "EMA は標準の漸化式。比べる本数は教科書でも利用者が決めるパラメータ（ChartSchool Slope「The number of days controls the period」）＝名前には出さず、引数で受け取る（まこさん 2026-10-04）",

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1066「_r(r"EMA(\d+)傾き%\((\d+)\)", "EMA傾き",」
状態: 確定

#### 実装 45
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1070行（<モジュール直下>・EMA の傾きの名前を EMA◯傾き% に戻し、比べる本数を名前に出さない引数で受け取る）
直す前の文字:
~~~
   known=lambda p: [(_flat(max(60, p[0] * 4, p[1] + 10)), [(-1, 0.0, 1e-9)])])

~~~
直した後の文字:
~~~
   known=lambda p: [(_flat(max(60, p[0] * 4)), [(-1, 0.0, 1e-9)])])

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1070「known=lambda p: [(_flat(max(60, p[0] * 4, p[1] + 10)), [(-1, 0.0, 1e-9)])])」
状態: 確定

#### 実装 46
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 1435行（_tb_ao・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」））
直す前の文字:
~~~
def _tb_ao(d, p):

~~~
直した後の文字:
~~~
def _tb_ao(d, p):
    p = p or (5, 34)                          # 名前に本数が無い＝教科書の 5・34

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:1435「def _tb_ao(d, p):」
状態: 確定

#### 実装 47
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2524行（_ext_ao・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」））
直す前の文字:
~~~
def _ext_ao(d, p):

~~~
直した後の文字:
~~~
def _ext_ao(d, p):
    p = p or (5, 34)                          # 名前に本数が無い＝教科書の 5・34

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:2524「def _ext_ao(d, p):」
状態: 確定

#### 実装 48
対象のファイル: scripts/priority_rebuild/indicator_reference_diag.py
直す箇所: 2534〜2536行（<モジュール直下>・AO の名前を AO% にし、2つの本数を名前に出さない引数で受け取る（まこさん「A」）／パラメータを、名前に出さない引数で受け取る）
直す前の文字:
~~~
_r(r"AO%\((\d+),(\d+)\)", "AO%",
   "オーサム振動子。中値（高値と安値の平均）の短期平均 − 長期平均を、終値で割って%化",
   "TradingView（Awesome Oscillator）。単純移動平均。%化は価格非依存 H6 のための本プロジェクトの流儀",

~~~
直した後の文字:
~~~
_r(r"AO%", "AO%",
   "オーサム振動子。中値（高値と安値の平均）の短期平均 − 長期平均を、終値で割って%化。2つの本数は名前に出さない引数（何も渡さないときは 5・34）",
   "TradingView（Awesome Oscillator・lengthAO1=5・lengthAO2=34）。単純移動平均。%化は価格非依存 H6 のための本プロジェクトの流儀",

~~~
根拠の抜き書き: scripts/priority_rebuild/indicator_reference_diag.py:2534「_r(r"AO%\((\d+),(\d+)\)", "AO%",」
状態: 確定

#### 実装 49
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 136〜139行（設定・名前に値を出すための設定（ema_slope_lookbacks・ao_params）を外す）
直す前の文字:
~~~
 "ema_slope_lookbacks": [
  5
 ],
 "_ema_slope_lookbacks": "傾き（EMA・ほかの移動平均）を何本前と比べるか（監査 CP60）。5 は直す前の決め打ちと同じ値＝列の値は変わらない。広げるのは まこさんが recipes/search_limits.json の material_param_ranges に書く（CC は数字を作らない）。",

~~~
直した後の文字:
~~~

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:136「"ema_slope_lookbacks": [」
状態: 確定

#### 実装 50
対象のファイル: scripts/priority_rebuild/observe_config.json
直す箇所: 161〜167行（設定・名前に値を出すための設定（ema_slope_lookbacks・ao_params）を外す）
直す前の文字:
~~~
 "ao_params": [
  [
   5,
   34
  ]
 ],
 "_ao_params": "AO% の教科書の期間（TradingView の逐語 lengthAO1=input(5…)・lengthAO2=input(34…)・監査 CP60）。",

~~~
直した後の文字:
~~~

~~~
根拠の抜き書き: scripts/priority_rebuild/observe_config.json:161「"ao_params": [」
状態: 確定

#### 実装 51
対象のファイル: .claude/breaks/b128_k1_copc_back_in_ao_loop.sh
直す箇所: 1〜27行（全文・探す文字が AO の直しで変わるので書き直す）
直す前の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: K-1 で戻した7種を、AO の for の中へ入れ直すと（修正13 を当てた直後と同じ）、自己テストの K-1 の番人が落ちる
# EXPECT_MSG: ❌ K-1:
# b128_k1_copc_back_in_ao_loop — K-1 で戻した7種を、AO の for の中へ入れ直すと（修正13 を当てた直後と同じ）、自己テストの K-1 の番人が落ちる（工事 m2c15-indicator-six-items-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r1_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ K-1:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    for (f_, s_, g_) in cfg["macd_params"]:\n        addf("AO%", f_, s_)\n        addf("APO%", f_, s_)\n        # ★K-1（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正13 を当てたとき、下の7種が AO の for の中に入り、\n        #   AO の 5・34 と、上の for から漏れた g_ で作られていた（COPC(9,5,34) ほか）。修正13 の前（commit 4656de3）と同じ場所に戻す。\n        addf("COPC", g_, f_, s_)\n        addf("FISHER", f_, g_)\n        addf("FISHERシグナル", f_, g_)\n        addf("KSTシグナル", g_)\n        for n in cfg["stoch_periods"]:\n            addf("KDJ%K", n, g_)\n            addf("KDJ%D", n, g_)\n            addf("KDJ%J", n, g_)\n    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。\n    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。\n    for (f_, s_) in cfg.get("ao_params", []):\n        addf("AO%", f_, s_)\n'
new = '    for (f_, s_, g_) in cfg["macd_params"]:\n        addf("AO%", f_, s_)\n        addf("APO%", f_, s_)\n    # ★AO の教科書の期間（Bill Williams・TradingView の逐語 lengthAO1=5・lengthAO2=34・監査 CP60）。\n    #   macd_params の 12/26 だけだと AO% は PPO と相関 0.9974 の重複になる。\n    for (f_, s_) in cfg.get("ao_params", []):\n        addf("AO%", f_, s_)\n        addf("COPC", g_, f_, s_)\n        addf("FISHER", f_, g_)\n        addf("FISHERシグナル", f_, g_)\n        addf("KSTシグナル", g_)\n        for n in cfg["stoch_periods"]:\n            addf("KDJ%K", n, g_)\n            addf("KDJ%D", n, g_)\n            addf("KDJ%J", n, g_)\n'
if s.count(old) != 1:
    raise SystemExit("[b128_k1_copc_back_in_ao_loop] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: K-1 で戻した COPC の組（macd の組）の並びを入れ替えると、自己テストの K-1 の番人が落ちる
# EXPECT_MSG: ❌ K-1:
# b128_k1_copc_back_in_ao_loop — K-1 で戻した COPC の組（macd の組）の並びを入れ替えると、自己テストの K-1 の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ K-1:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    for (f_, s_, g_) in cfg["macd_params"]:\n        addf("APO%", f_, s_)\n        # ★K-1（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正13 を当てたとき、下の7種が AO の for の中に入り、\n        #   AO の 5・34 と、上の for から漏れた g_ で作られていた（COPC(9,5,34) ほか）。修正13 の前（commit 4656de3）と同じ場所に戻す。\n        addf("COPC", g_, f_, s_)\n        addf("FISHER", f_, g_)\n        addf("FISHERシグナル", f_, g_)\n        addf("KSTシグナル", g_)\n        for n in cfg["stoch_periods"]:\n            addf("KDJ%K", n, g_)\n            addf("KDJ%D", n, g_)\n            addf("KDJ%J", n, g_)\n    # ★AO（2026-10-04・工事 m2c15-hidden-params-20261004・まこさん「A」）＝名前は AO% の1列。2つの本数は名前に出さない引数で受け取る\n    #   （何も渡さないときはライブラリの既定＝教科書の 5・34）。\n    addf("AO%")\n'
new = '    for (f_, s_, g_) in cfg["macd_params"]:\n        addf("APO%", f_, s_)\n        # ★K-1（2026-10-04・工事 m2c15-indicator-six-items-20261004）＝監査 CP60 の修正13 を当てたとき、下の7種が AO の for の中に入り、\n        #   AO の 5・34 と、上の for から漏れた g_ で作られていた（COPC(9,5,34) ほか）。修正13 の前（commit 4656de3）と同じ場所に戻す。\n        addf("COPC", g_, s_, f_)\n        addf("FISHER", f_, g_)\n        addf("FISHERシグナル", f_, g_)\n        addf("KSTシグナル", g_)\n        for n in cfg["stoch_periods"]:\n            addf("KDJ%K", n, g_)\n            addf("KDJ%D", n, g_)\n            addf("KDJ%J", n, g_)\n    # ★AO（2026-10-04・工事 m2c15-hidden-params-20261004・まこさん「A」）＝名前は AO% の1列。2つの本数は名前に出さない引数で受け取る\n    #   （何も渡さないときはライブラリの既定＝教科書の 5・34）。\n    addf("AO%")\n'
if s.count(old) != 1:
    raise SystemExit("[b128_k1_copc_back_in_ao_loop] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b128_k1_copc_back_in_ao_loop.sh:1「#!/bin/bash」
状態: 確定

#### 実装 52
対象のファイル: .claude/breaks/b132_hidden_param_not_passed.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: HWMA の登録が、受け取った引数 na をライブラリへ渡さないと、名前に出さない引数の番人が落ちる
# EXPECT_MSG: ❌ 名前に出さない引数: close vs HWMA% の na
# b132_hidden_param_not_passed — HWMA の登録が、受け取った引数 na をライブラリへ渡さないと、名前に出さない引数の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 名前に出さない引数: close vs HWMA% の na」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_pta6.hwma(close=d.close, na=na, '
new = '_pta6.hwma(close=d.close, '
if s.count(old) != 1:
    raise SystemExit("[b132_hidden_param_not_passed] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
状態: 確定

#### 実装 53
対象のファイル: .claude/breaks/b133_cksp_mixed_set.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: CKSP を引数なしの呼び方（値は本の形・ならし方は TradingView の形の、混ざった組）に戻すと、CKSP の番人が落ちる
# EXPECT_MSG: ❌ CKSP:
# b133_cksp_mixed_set — CKSP を引数なしの呼び方（値は本の形・ならし方は TradingView の形の、混ざった組）に戻すと、CKSP の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ CKSP:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = 'close=d.close, tvmode=True, **kw)'
new = 'close=d.close, **kw)'
if s.count(old) != 1:
    raise SystemExit("[b133_cksp_mixed_set] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
状態: 確定

#### 実装 54
対象のファイル: .claude/breaks/b134_ao_name_with_value.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: AO の名前に値を入れると（AO%(5,34)）、名前の番人が落ちる
# EXPECT_MSG: ❌ 名前: AO%
# b134_ao_name_with_value — AO の名前に値を入れると（AO%(5,34)）、名前の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 名前: AO%」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '_reg("AO%", "AO%", True,'
new = '_reg("AO%", "AO%(5,34)", True,'
if s.count(old) != 1:
    raise SystemExit("[b134_ao_name_with_value] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
状態: 確定

#### 実装 55
対象のファイル: .claude/breaks/b135_rci_mako_gone.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 参照表の RCI の行から mako の欄を外すと（表を作り直すと「使わない」へ戻る）、RCI の番人が落ちる
# EXPECT_MSG: ❌ RCI:
# b135_rci_mako_gone — 参照表の RCI の行から mako の欄を外すと（表を作り直すと「使わない」へ戻る）、RCI の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/indicator_reference_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ RCI:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicator_reference_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])],\n   mako="2026-10-04 まこさん指示「V9で使ってる指標は入れるようにしてほしい」（V9 の P22 が RCI7 と RCI9 のクロスを使う）")\n'
new = '   known=lambda p: [(_up(p[0] + 5), [(-1, 100.0, 1e-9)]), (_dn(p[0] + 5), [(-1, -100.0, 1e-9)])])\n'
if s.count(old) != 1:
    raise SystemExit("[b135_rci_mako_gone] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
状態: 確定

#### 実装 56
対象のファイル: .claude/breaks/b136_insp2_bar_close_dropped.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 検査2 から、上位足のずらし bar_close の形の確かめを外すと、検査2 の番人が落ちる
# EXPECT_MSG: ❌ 検査2:
# b136_insp2_bar_close_dropped — 検査2 から、上位足のずらし bar_close の形の確かめを外すと、検査2 の番人が落ちる（工事 m2c15-hidden-params-20261004・2026-10-04）
#   守っているもの＝完成の条件の軽い口（observe_diag.py --selftest-catalog）の番人
#   壊し方＝scripts/priority_rebuild/observe_diag.py の中の、下の old を new に置き換える（r2_draft_build.py が当てた後の写しで同じ壊し方を走らせ、落ちるのを確かめた）。
#   期待＝observe_diag.py --selftest-catalog が「❌ 検査2:」で落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    leak = _insp_close_leak(shift=True) + _insp_close_leak(shift=True, mode="bar_close")   # ★K-8＝ずらし2種\n'
new = '    leak = _insp_close_leak(shift=True)\n'
if s.count(old) != 1:
    raise SystemExit("[b136_insp2_bar_close_dropped] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: .claude/breaks/b131_industry_map_prev_pivot_gone.sh:1「#!/bin/bash」
状態: 確定

<!-- ACC_IMPL_END -->

### 4-A この節に何を書いたか（一覧）

［自動］項目の正本と、OK された案・やることの表の有無
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 56 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 引数の既定を、None か、今の式に書いてある数字にする | None を渡すと、ライブラリは引数なしのときと同じ決め方で値を決めるので、今の列と必ず同じになる。値を書き写すと、写し違いで列が変わる（154回目の CKSP の例） | 資料の既定の値を、引数の既定として書き写す |
| 2 | CKSP は、自前の関数 _ck がライブラリを tvmode=True で呼ぶ形にする | まこさん「２はC」。tvmode=True を渡すと、ライブラリが値の組とならし方の両方を TradingView の形に決める | 値の組を引数の既定として書き写す |
| 3 | AO は、名前を AO% にし、何も渡さないときはライブラリの既定にする | まこさん「A」。ライブラリの既定は教科書の値と同じ（ao.py） | 値違いの列を2つ残す／151回目の前に戻す |
| 4 | 移動平均の傾きの比べる本数も、名前に出さない引数で受け取る | 151回目に取り下げた直し（傾きの本数を名前に出す）を、名前に出さない形で入れる、と引き継ぎに決まっている | 傾きの本数を決め打ちのまま残す |
| 5 | 実装の指示は、今の実物と、直しを全部 当てた後の中身を比べて、道具が作る | 同じ登録の文を2つの直しが触る所が在る。直しごとに指示を分けると、直す前の文字が今の実物に無くなる | 直しごとに指示を分ける |
| 6 | 番人は、前の工事の軽い口（--selftest-catalog）に足す | 新しい旗を増やさずに済む。完成の条件と壊すプログラムが、数秒で測れる | 新しい旗を作る |
| 7 | 番人は、別の値が全部 計算できなかった引数を数えない | 前から在る登録に、for が取り込んだ列の番号を既定に持つ引数が在り、数のパラメータではない（写しで落ちて分かった） | 既定つきの引数を全部 数える |
| 8 | 前の工事の壊すプログラム b128 を、この工事で書き直す | b128 が探す文字に AO の行が在り、AO の直しで探す文字が無くなる。放置すると b128 は何も壊せなくなる（恒久59番） | b128 をそのまま残す |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=3d695c6309c41570 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b132_hidden_param_not_passed.sh` | #1 | HWMA の登録が、受け取った引数をライブラリへ渡さない形にする |
| `b133_cksp_mixed_set.sh` | #2 | CKSP を、引数なしの呼び方（混ざった組）に戻す |
| `b134_ao_name_with_value.sh` | #3 | AO の名前に値を入れる |
| `b135_rci_mako_gone.sh` | #4 | 参照表の RCI の行から mako の欄を外す |
| `b136_insp2_bar_close_dropped.sh` | #5 | 検査2 から、bar_close の形の確かめを外す |
| `b128_k1_copc_back_in_ao_loop.sh` | #6 | COPC の組の並びを入れ替える |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | この工事の後も、名前に出さない引数は、探す側から渡されない（6項目の3番は、工事2 で探す側をつないで初めて満たされる） | 工事2 で、探す側が範囲から渡す仕組みを作る（3-1 に書いた） |
| 2 | 番人は、別の値が全部 計算できなかった引数を見逃す | 受け取る引数を新しく足すときは、写しで別の値を渡して列が変わることを、案を作る道具で確かめる（この工事は 47種類とも確かめた） |
| 3 | 検査2 の番人は、確かめが外されないことだけを守る。検査2 の確かめそのものは、決まった2つの時刻だけを見る | 上位足のずらしを切り替えて比べる前（M2-F-10f）に、確かめを強くするかを決める（3-1 に書いた） |
| 4 | CKSP の列の値が変わるので、成績表の CKSP の行は古い値の成績のまま残る | 成績表の作り直し（M2-D-8）で直る（3-2 に書いた） |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 前の工事で、当てる道具は1秒未満で終わった |
| 全体の自己テスト | 124秒 | 4-14 |
| 軽い口と壊すプログラム | 軽い口1回 4秒 | 写しで壊し方を並べて走らせた実測は 10秒（r2_draft_build.py の [7]） |
| G-1 の表の作り直し | 約1分 | 前の工事の実測（表を作る道具の合計） |
| G2 → H2 | 約30秒 → 約5分 | 前の工事の実測 |
| まこさんの承認 | 設計書は2回の見込み（当てる前・新しい関数で SPEC を作り直した後）。型の表は再承認が1回。出口の型の表は、中身が変わったときだけ | 4-4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝①登録の作りが「パラメータを受け取る＝名前に数字が出る」の1通りしか無く、名前に出さないパラメータを受け取る口が無かった。そのため、資料のパラメータを受け取らない登録が残り、151回目は名前に値を足す直しで埋めようとした。②CKSP は、ライブラリを引数なしで呼ぶと値の組が混ざる作りだった。③RCI と検査2 の直しは、前の工事で完成の条件に入れなかった。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。指標が、パラメータを受け取れる状態になります。

**③ root か symptom か**＝root です。登録の計算式そのものが引数を受け取る形にし、受け取った引数が計算に届いているかを番人で確かめます。

**④ ベースアップ**＝154回目に調べた資料（indicator_params_by_strategy・indicator_params_review）・ライブラリの実物（cksp.py・ao.py）・監査 CP60 と CP61。新しい Web の調べはしていません。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。引数の既定は、None か、今の式に書いてある数字です。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝指標が、パラメータを名前に出さない引数で受け取る形にする。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 乱数を使いません。条件をつなぐものではなく、指標がパラメータを受け取る形にする直しです |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 私は探す値を1つも決めていません。点の一覧を足す直しは在りません。名前に値を出すための設定を外します |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **この工事で、パラメータは範囲から探せるようになるか** | なりません（6-2 の1行目）。探す側をつなぐのは工事2 です |
| **番人は、受け取る引数を全部 見るか** | 別の値が全部 計算できなかった引数は見ません（6-2 の2行目） |
| **別の値を渡した列が、教科書どおりかを確かめるか** | 確かめません。参照表は、何も渡さないときの列だけを照らします |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=a9b5932111d4248c gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝observe_diag.py・indicator_reference_diag.py・observe_config.json・壊すプログラム b128 と、新しい壊すプログラムを【7-8】に書いた。主なファイルは observe_diag.py。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝observe_diag.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b131（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝151回目は、名前に値を足す直しでパラメータを増やそうとした。154回目は、資料の値を書き写して CKSP の列が変わった。この工事は、名前に出さない引数で受け取り、既定は None か今の式の値にして、写しで全部の列を直す前と比べた。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | この工事は、新しい部品も前処理も足さない。計算式が受け取る引数が増えるだけで、何も渡さないときの列は CKSP を除いて直す前と同じ。CKSP の2列は値が変わるので、当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | この工事は engine_tuner_exec.py・engine_tuner_gen.py を直さないので、その行番号を指す文書は無い。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の4）。探す文字が変わる b128 は、この工事で書き直す。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは observe_diag.py --selftest-catalog で、軽い口は決まった式で作った値動きだけを使い、ファイルに書かない。本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数は _insp_hidden_params の1つ。触る関数は全部 DESIGN_CONTRACT の impl_functions に書いた（道具が当てる前と後の構文木で数えた）。must_use の名前は、当てた後の関数の中に在ることを道具が ast で照らした。observe_diag.py の触る関数＝<モジュール直下>・_ab・_acb・_cel・_ck・_hw。observe_diag.py の触る関数＝_insp_hidden_params・_mama・_ps・_vp_levels・build_catalog・selftest_catalog。indicator_reference_diag.py の触る関数＝<モジュール直下>・_ext_ao・_ext_ema_slope・_tb_ao・_tb_ema_slope。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。番人は、完成の条件が走らせる軽い口（--selftest-catalog）の中で全部 通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2c15-hidden-params-20261004）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝軽い口の番人（名前に出さない引数・CKSP・名前・RCI・検査2 と、前の工事の K-1・K-8・G-2）と、壊すプログラム（わざと壊して落ちるか）。写しで走らせ、全部 通った。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | H-1＝名前に出さない引数が、その列の計算に届いている | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | HWMA の登録が、受け取った引数をライブラリへ渡さない形にする | `b132_hidden_param_not_passed.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝HWMA の登録が、受け取った引数 na をライブラリへ渡さないと、名前に出さない引数の番人が落ちる |
| 2 | H-2＝CKSP の何も渡さない列が、TradingView の形と同じ | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | CKSP を、引数なしの呼び方（混ざった組）に戻す | `b133_cksp_mixed_set.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝CKSP を引数なしの呼び方（値は本の形・ならし方は TradingView の形の、混ざった組）に戻すと、CKSP の番人が落ちる |
| 3 | H-3＝EMA の傾きと AO の名前に、値が無い | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | AO の名前に値を入れる | `b134_ao_name_with_value.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝AO の名前に値を入れると（AO%(5,34)）、名前の番人が落ちる |
| 4 | H-4＝参照表の RCI の行に mako の欄が在る | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | 参照表の RCI の行から mako の欄を外す | `b135_rci_mako_gone.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝参照表の RCI の行から mako の欄を外すと（表を作り直すと「使わない」へ戻る）、RCI の番人が落ちる |
| 5 | H-4＝検査2 が、上位足のずらし bar_close の形も確かめている | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | 検査2 から、bar_close の形の確かめを外す | `b136_insp2_bar_close_dropped.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝検査2 から、上位足のずらし bar_close の形の確かめを外すと、検査2 の番人が落ちる |
| 6 | 前の工事の K-1＝COPC ほかが macd の組で在る（b128 を書き直した後も守られている） | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | 実経路 | COPC の組の並びを入れ替える | `b128_k1_copc_back_in_ao_loop.sh` | — | **✅済**＝壊すと rc=1（宣言どおり）／条件のコマンドも rc=0（承認のときに機械が2つとも測った）／壊した意味＝K-1 で戻した COPC の組（macd の組）の並びを入れ替えると、自己テストの K-1 の番人が落ちる|

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=fb7b235b9ae21391 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `selftest_catalog` | 6930 |
| `_insp_hidden_params` | （この関数は実物に無い） |
| `_insp_close_leak` | 3866 |
| `build_catalog` | 1317 |
| `_ck` | 646 |
| `_vp_levels` | 361 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 179件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=1665b8dc37d241bb gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "照らす相手は実在するファイル。材料の登録・材料の一覧（build_catalog）・軽い口の番人（selftest_catalog）が在る、観察の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "<モジュール直下>",
      "_ab",
      "_acb",
      "_cel",
      "_ck",
      "_hw",
      "_insp_hidden_params",
      "_mama",
      "_ps",
      "_vp_levels",
      "build_catalog",
      "selftest_catalog"
    ],
    "scripts/priority_rebuild/indicator_reference_diag.py": [
      "<モジュール直下>",
      "_ext_ao",
      "_ext_ema_slope",
      "_tb_ao",
      "_tb_ema_slope"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（実装の指示を全部 当てる前と後の構文木を関数ごとに比べて、r2_proposal_build.py が数えた）。",
  "self_check_calls": [
    "selftest_catalog",
    "_insp_hidden_params",
    "_insp_close_leak",
    "build_catalog",
    "_ck",
    "_vp_levels"
  ],
  "_self_check_calls の意味": "実装の後の observe_diag.py に在るはずの、この工事が触る関数の名前。",
  "must_use": {
    "selftest_catalog": [
      "_insp_hidden_params",
      "_ck",
      "_insp_close_leak",
      "build_catalog",
      "load_config"
    ],
    "_insp_hidden_params": [
      "build_catalog",
      "load_config",
      "find_material"
    ]
  },
  "_must_use の意味": "軽い口が、この工事の番人で呼ぶ関数と、番人の関数が材料の一覧を作るために呼ぶ関数（r2_proposal_build.py が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、登録の計算式が受け取る引数と、2種類の名前の型を直すだけ。外から読む一覧の形（カタログの1件の形・参照表の欄）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（r2_proposal_build.py が数えた）",
    "must_use": "ast で照らした",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/observe_diag.py",
 "public_functions": {
  "load_config": [],
  "find_material": [],
  "make_material": [],
  "build_catalog": [
   "make_material"
  ],
  "load_1m": [],
  "insp5_frame": [
   "load_1m"
  ],
  "build_features": [
   "build_catalog",
   "load_1m"
  ],
  "load_demand": [],
  "build_range_geometry": [],
  "rank_separation": [],
  "rank_separation_independent": [
   "rank_separation"
  ],
  "trajectory": [],
  "post_exit": [],
  "neighbors": [],
  "observe": [
   "build_catalog",
   "build_features",
   "grow_search",
   "load_config",
   "load_demand",
   "mech_thresholds",
   "next_actions",
   "verdict"
  ],
  "next_actions": [],
  "grow_search": [
   "round_trip_cost"
  ],
  "mech_thresholds": [],
  "round_trip_cost": [],
  "plan_scene": [
   "build_catalog",
   "load_config",
   "round_trip_cost"
  ],
  "observe_scene": [
   "build_features",
   "load_config",
   "load_demand",
   "rank_separation_independent",
   "round_trip_cost"
  ],
  "plan": [
   "build_catalog",
   "load_config"
  ],
  "verdict": [],
  "inspect_data": [
   "build_catalog",
   "load_config"
  ],
  "check_materials": [
   "build_catalog",
   "load_config"
  ],
  "check_materials_meta": [
   "build_catalog",
   "load_config"
  ],
  "rank_materials_for_regime": [
   "build_catalog",
   "build_features",
   "rank_separation"
  ],
  "rank_regime": [
   "add_demand_to_ranking",
   "build_catalog",
   "load_config"
  ],
  "rank_demand_for_regime": [
   "load_demand",
   "rank_separation"
  ],
  "merge_demand_into_ranking": [],
  "add_demand_to_ranking": [
   "load_config",
   "merge_demand_into_ranking",
   "rank_demand_for_regime"
  ],
  "selftest_rank_demand": [
   "load_demand",
   "merge_demand_into_ranking",
   "rank_demand_for_regime",
   "rank_separation"
  ],
  "selftest_rank_resume": [
   "build_catalog",
   "load_config",
   "rank_materials_for_regime"
  ],
  "selftest_insp5": [
   "build_catalog",
   "insp5_frame",
   "load_1m",
   "load_config"
  ],
  "selftest_atr1h": [
   "build_catalog",
   "build_features",
   "load_config"
  ],
  "selftest_catalog": [
   "build_catalog",
   "build_features",
   "load_config"
  ],
  "selftest": [
   "build_catalog",
   "build_features",
   "build_range_geometry",
   "load_config",
   "load_demand",
   "make_material",
   "mech_thresholds",
   "next_actions",
   "rank_separation",
   "rank_separation_independent",
   "round_trip_cost",
   "selftest_atr1h",
   "selftest_catalog",
   "selftest_insp5",
   "selftest_rank_demand",
   "selftest_rank_resume",
   "verdict"
  ],
  "build_parser": []
 },
 "constants": {
  "ONE_MIN_CSV": "data/BTCUSDT-1m-binance-taker-2023-06-01_2026-06-30.csv",
  "BARS_CSV": "data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv",
  "_INSP_STEP_NG_PCT": 5.0,
  "_INSP_STEP_WARN_PCT": 0.5,
  "_H6_RTOL": 1e-08,
  "_DUP_NEAR": 0.999,
  "_DUP_SAME": 0.99999,
  "_DUP_CALC_ROWS": 60000,
  "_DUP_ROWS": 20000,
  "_V9_MATCH_SAME": 0.99999,
  "_V9_MATCH_NEAR": 0.99,
  "_V9_RECORD_SINCE": "2026-07-28 00:00",
  "DEMAND_RANK_TF": "5m"
 },
 "cli_flags": [
  "--selftest",
  "--selftest-atr1h",
  "--selftest-catalog",
  "--selftest-insp5",
  "--selftest-rank-demand",
  "--selftest-rank-resume"
 ]
}
```

<!-- ACC_SPEC_END -->
