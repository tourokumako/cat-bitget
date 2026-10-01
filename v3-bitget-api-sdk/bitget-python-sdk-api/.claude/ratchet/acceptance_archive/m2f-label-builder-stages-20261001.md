<!-- ARC iter="m2f-label-builder-stages-20261001" -->

# 設計書｜段の候補を作る側と測る側の不具合6つを直し、渡す本数を10本にする

TARGET: scripts/priority_rebuild/engine_tuner_gen.py, scripts/priority_rebuild/regime_r9_diag.py, scripts/priority_rebuild/recipes/search_limits.json

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2f-label-builder-stages-20261001/ok_stages_20261001`・`m2f-label-builder-stages-20261001/ok_todo_20261001`・`m2f-label-builder-stages-20261001/okd_stages_20261001`・`m2f-label-builder-stages-20261001/req_14b_20260928`・`m2f-label-builder-stages-20261001/req_k1_20260918`・`m2f-label-builder-stages-20261001/req_m27_20260928`・`m2f-label-builder-stages-20261001/req_m2_20261001`・`m2f-label-builder-stages-20261001/req_split_20261001`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2f-label-builder-stages-20261001/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2f-label-builder-stages-20261001 --write`。検出＝`--work m2f-label-builder-stages-20261001 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=c05410ff929cb6fb gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2f-label-builder-stages-20261001/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2f-label-builder-stages-20261001/ok_stages_20261001.txt`（まこさんの発言）・`verbatim/m2f-label-builder-stages-20261001/ok_todo_20261001.txt`（まこさんの発言）・`verbatim/m2f-label-builder-stages-20261001/okd_stages_20261001.txt`（まこさんが OK した CC の文）・`verbatim/m2f-label-builder-stages-20261001/req_14b_20260928.txt`（まこさんの発言）・`verbatim/m2f-label-builder-stages-20261001/req_k1_20260918.txt`（まこさんの発言）・`verbatim/m2f-label-builder-stages-20261001/req_m27_20260928.txt`（まこさんの発言）・`verbatim/m2f-label-builder-stages-20261001/req_m2_20261001.txt`（まこさんの発言）・`verbatim/m2f-label-builder-stages-20261001/req_split_20261001.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝461 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_stages_20261001` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_todo_20261001` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_stages_20261001` | V01〜V08（8 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_stages_20261001` | V09〜V10（2 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V11〜V13（3 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V14〜V16（3 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V17〜V29（13 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V30〜V34（5 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V35〜V37（3 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V38〜V40（3 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V41〜V42（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V43〜V45（3 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V46〜V47（2 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V48〜V49（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V50〜V51（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V52〜V55（4 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V56〜V59（4 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V60〜V61（2 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V62〜V63（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V64〜V65（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V66〜V67（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V68〜V69（2 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V70〜V304（235 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V305〜V315（11 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V316〜V321（6 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V322〜V327（6 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V328〜V334（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V335〜V336（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V337〜V338（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V339〜V343（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V344〜V353（10 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V354〜V374（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V375〜V380（6 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V381〜V435（55 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_stages_20261001` | V436〜V440（5 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_14b_20260928` | V01〜V03（3 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_k1_20260918` | V01〜V07（7 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_m27_20260928` | V01〜V05（5 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_m2_20261001` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_split_20261001` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
M2 は、4つの場面（レンジ・上げ・下げ・スパイク）の判定を、全部の戦略のために組む段です。判定の束は、§2.2 の段（帯 → 強さの否定 → 向きの否定 → 3枠目 → 持続 → 差し戻し）ごとに測って並べ、上位を次の段へ渡します。いまの組む側（engine_tuner_gen.py）と測る道具（regime_r9_diag.py）には不具合が6つ在り、渡す本数を10本にすると組む側が止まり、強さの否定の出る線が逆向きで、段1 の下側の帯と差し戻しの「なし」が測られず、同じ候補が最大6回 並び、候補の並べる正解が3つ混ざっています。この工事は、6つを直し、渡す本数を10本にします。これで段1〜段4 の走行（M2-F-8〜15）に進めます。答え合わせの札の構造（14a）は別の工事に分けました（まこさん「じゃあ修正せずに、分けてすすめれば」）。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 組む側の段の上端が、候補の本数を超えると止まるか | `grep -c -F 'の上端が候補の本数を超える:' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は止める文が在る。実装の後は無い | 0（終了コード 1） |
| 段1・段2c を並べる正解 | `grep -n -F -e '"stage1":' -e '"stage2c":' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py` | 実装の前は label が None。実装の後は強さ | 2540:    "stage1":  {"label": "強さ", "pick": "lineage"}, ⏎ 2543:    "stage2c": {"label": "強さ", "pick": "family"}, ⏎ 6584:        #   直す前は {"stage1": 354, …}（監査の実測）と ±10% で比べていた＝私（CC）が ⏎ 7664:        _c43 = _cands43({"stage_limits": {"stage1": {"tfs": [_one43]}}}) ⏎ 7669:        for _bad43, _why43 in (({"stage1": {"bogus": 1}}, "知らない鍵"), ⏎ 7670:                               ({"stage1": {"tfs": ["9m"]}}, "時間足の表に無い名前"), ⏎ 7671:                               ({"stage1": {"quantiles": ["q99"]}}, "範囲の…（出力 9 行のうち先頭 500 文字）（終了コード 0） |
| 渡す本数の上端 | `grep -n -F '"stage_keep_range"' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json` | 実装の前は上端が null の行。実装の後は まこさんが決めた本数の行 | 50:  "stage_keep_range": { "lo": 1, "hi": 10, "kind": "int" },（終了コード 0） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=27bccc2869a2aa6f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

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

［自動］成績表
<!-- ACC_RANKING_START hash=c4af94c1b5c022bf gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`material_ranking.json`。

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
| 1 | 答え合わせの札の構造（14a＝札の部品・設定・版）を、この工事に入れない | 案が1回の返信に収まらない（実装の指示が約10万文字）。別の工事に分ける | req_split_20261001 |
| 2 | 固定のレシピ r9_demand_fixture.json の出る線を直さない | このレシピは需給の列が足されるかを測るための物で、出る線の向きは測る中身に関係しない。直すと、直す前と同じ結果が出ることを確かめる条件（壊すプログラム b97）が崩れる | milestones2 の M2-F-13b の②「直すかは設計書で決める」 |
| 3 | 段の走行（M2-F-8〜15）は、この工事の実装に入れない | 実装の後に、時間の見込みをフロー宣言に書いてから走らせる（恒久60〜62番） | milestones2 の M2-F-8 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| — | 無し（やることの表の「決めてほしいこと」が「無し」か空） | — | — |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、段の候補を作る側と測る道具の不具合6つを直し、渡す本数を10本にするものです。**§2.2 の段（帯 → 強さの否定 → 向きの否定 → 3枠目 → 持続 → 差し戻し）ごとに測って並べ、上位を次の段へ渡す探し方が、止まらずに最後まで回り、正しい向きの線で、上側と下側の帯・3枠目の「なし」・同じ物を重ねない候補を測れるようにします。これで段1〜段4 の走行（M2-F-8〜15）に進めます。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、測る道具 regime_r9_diag.py の段の口（--stage・--sweep）をコマンドから動かします。組む側 engine_tuner_gen.py の段の候補の一覧（build_stage_candidates）と束を組む関数（sample_regime_build）は、測る道具と engine_tuner から呼ばれます。
**誰が結果を使うか。**段の順位表と落ちた候補（M2-F の段の選抜）と、engine_tuner が組む場面の判定の束。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**入力。**設定 search_limits.json（stage_keep_range ほか）・法則 regime_laws.json・型の表・成績表 material_ranking.json。
**出力。**段の候補の一覧（同じ条件は1本・段1・段2c は強さの順）・組んだ判定の束（出る線の向きを直した物）・段の順位表と落ちた候補（段1 は上側と下側・差し戻しは「なし」と足す側を含む）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
- 乱数を使わない（恒久67番）。段の候補は法則が名指しした物を、成績表の順位で並べる。
- 渡す本数の上端10は まこさんの決定（2026-09-18「とりあえず１０本にする」）。CC は本数を選ばない。

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
- engine_tuner_gen.stage_keep_of＝上端が候補の本数を超える段は、候補の本数を使う（B-1）。
- engine_tuner_gen.sample_regime_build＝段2a の強さの否定の出る線（off_c）を、入る線と反対の向きに緩める（B-2）。
- engine_tuner_gen.build_stage_candidates＝条件の中身が同じ候補は最初の1本だけ残す（B-5）。
- engine_tuner_gen.STAGE_SPEC＝段1・段2c の label を「強さ」にする（B-6・まこさん決定）。
- engine_tuner_gen.selftest_stages（新）＝T48 の本体。selftest と口 --selftest-stages が呼ぶ。
- regime_r9_diag._loosened_off＝not の中身だけ、緩める向きを入る線と反対にする（B-2）。
- regime_r9_diag._both_sides（新）＝段1 の候補に、側を返した帯を足す（B-3）。run_stage が呼ぶ。
- regime_r9_diag._sweep_slots・_slot_variants（新）＝差し戻しの枠に、段2c の「なし」と、段2c を足す枠を入れる（B-4）。run_sweep が呼ぶ。
- regime_r9_diag.selftest に ⑭⑮⑯ を足す。
- recipes/search_limits.json の stage_keep_range の hi＝10（K-1）。
- 触る所（engine_tuner_gen.py）＝<モジュール直下>・stage_keep_of・build_stage_candidates・sample_regime_build・selftest_stages・selftest・main
- 触る所（regime_r9_diag.py）＝_loosened_off・_both_sides・_sweep_slots・_slot_variants・run_stage・run_sweep・selftest

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当てます。
2. 組む側の --selftest-stages（T48）と測る道具の --selftest（⑭⑮⑯）を走らせます。
3. engine_tuner_gen.py と search_limits.json は G2・H2 の印の対象なので、G2（gen_signal_families.py --verify・約30秒）→ H2（leak_causality_diag.py・約5分）の順で印を取り直します。
4. 実装を監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝設定の上端が10のとき、組む側は段2b（候補1本）で止まらずに1本を使い、レンジの判定の束を組む。段2a の強さの否定が「ADX above q50 の否定」なら、出る線は「ADX above q51」になる（強さが はっきり上がったら出る）。測る道具が --stage stage1 を走らせると、帯の候補ごとに上側と下側の2本を束にし、強さの順に並べた候補（同じ条件は1本だけ）から測って、上位10本を順位表に書く。--sweep は段2c の枠で「なし」も試し、「なし」で勝った束には段2c の候補を足して試す。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
- 新しい旗は組む側の --selftest-stages だけ（T48 を短く走らせる口）。測る道具の旗は変えない。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
- 上端 10 の設定で、組む側がレンジの判定の束を組める。段2a の出る線は「強さ above q(X+1)」（側が above のとき）。
- --stage stage1 の測る束は、上側と下側の帯の両方（本数は2倍）。--sweep は段2c の「なし」と足す側を試す。
- 段の候補に、中身が同じ条件は1本だけ。段1・段2c の候補は強さの分離力の順。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
- 上端が候補の本数を超える＝止めずに候補の本数を使う（B-1）。下端が1未満・下端が上端より大きいは、いままでどおり止める。
- 差し戻しで「なし」か段2c を足す側が勝って枠の数が変わった＝その周の残りの枠を飛ばし、枠の並びを作り直して次の周へ進む（B-4）。

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
- 段の候補の一覧は、同じ条件の行が無くなる（行の数が減る）。段1 の測る束は、側を返した帯の分だけ増える（2倍）。
- 差し戻しの印は（内側・包み・枠）の3つになる（直す前は内側と包みの2つ）。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
- B-5 で重なりを除くと、段1 の候補は 2,487行 → 中身の違う 812本 の見込み（worklog 20260928 §15 の 15-8 の実測）。B-3 で2倍。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
変えない（差し戻しの印字は同じ形・「なし」の束は名前の末尾が _none）。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
- engine_tuner_gen.py と search_limits.json は H2・G2 の印の対象＝直した後は印を取り直すまで engine_tuner が走らない（4-4 の手順3）。
- 14b で直す行を探す壊すプログラム（b77・b79・b82・b84・b85・b86・b87_stages_record・b91・b92・b93・b97・b99・b109・b113・b116）の探す文字は、この工事の直す前の文字と重ならない（直す前の文字はそれぞれ実物にちょうど1か所）。
- 段1 の束が2倍になるので、段1 の走行（M2-F-8）の時間は約49分 → 約98分の目安（milestones2 の M2-F-13b の③・掛け算の目安で未測定）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
- B-2 の向きは、帯の幅と段1 の出る線がすでに使う _flip_loose の向き（engine_tuner_gen.py:3135〜3145）に揃える。B-1 は stage_keep_of の下端の検査の形をそのまま残す。T48 の口は --selftest-rank-demand の作りに揃える。

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=0eadb7b17bc03e94 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: stage_keep_of の上端の検査（B-1）
直す前の文字:
~~~
        raise SampleError(f"stage_keep_range の上端が候補の本数を超える: hi={hi} > {int(n_cands)}（fail-closed）")

~~~
直した後の文字:
~~~
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-1）＝上端が候補の本数を超える段は、候補の本数の分だけ使う（止めない）。
        #   段2b の候補は1本なので、上端に10を書くと組む側がレンジの判定の束を1本も組めなかった（next_step §6 の224番）
        hi = int(n_cands)

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:3164「if hi > int(n_cands):」
状態: 確定

#### 実装 2
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: stage_keep_of の説明の文（B-1）
直す前の文字:
~~~
    ★数字を作らない＝範囲の外（lo < 1／hi > 候補の本数／lo > hi）は SampleError で止める（fail-closed）。

~~~
直した後の文字:
~~~
    ★数字を作らない＝範囲の外（lo < 1／lo > hi）は SampleError で止める（fail-closed）。
    ★上端が候補の本数を超える段は、候補の本数を使う（2026-10-01・B-1＝直す前は止めていた）。

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:3154「範囲の外（lo < 1／hi > 候補の本数／lo > hi）は SampleError で止める」
状態: 確定

#### 実装 3
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: sample_regime_build の off_c（B-2）
直す前の文字:
~~~
    off_c["value"]["threshold_q"] = _loose_q_fixed(limits, strong["value"]["threshold_q"], strong_side)

~~~
直した後の文字:
~~~
    # ★2026-10-01（B-2）＝not の中身の出る線は、強さが はっきり上がった所（above なら1つ大きい分位）。側は返さない（強さが戻ったら出る）。
    #   直す前は強さの側のまま緩めたので、出る線が入る側の内側（above q(X−1)）で真になった（監査 CP48 の別に見つけたこと）
    off_c["value"]["threshold_q"] = _loose_q_fixed(limits, strong["value"]["threshold_q"],
                                                "below" if strong_side == "above" else "above")

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:3349「off_c["value"]["threshold_q"] = _loose_q_fixed(limits, strong["value"]["threshold_q"], strong_side)」
状態: 確定

#### 実装 4
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: build_stage_candidates の見た条件の入れ物（B-5）
直す前の文字:
~~~
    _moving: list[dict] = []

~~~
足す文字:
~~~
    _seen_c: set = set()                           # ★2026-10-01（B-5）＝同じ条件の候補を2回 並べない

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2879「_moving: list[dict] = []」
状態: 確定

#### 実装 5
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: build_stage_candidates の条件を作った後（B-5）
直す前の文字:
~~~
                    "side": side, "value": _thr_fixed(limits)}

~~~
足す文字:
~~~
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-5）＝条件の中身が同じ候補は、最初の1本（順位の高い方）だけを残す。
        #   ranked_groups は（正解・先読み・種類・時間足）の組ごとに出すので、同じ種類×時間足の同じ列が最大6回 並んでいた
        #   （段1 は 2,487行のうち中身の違う列 812・worklog 20260928 §15 の 15-8）
        _ck = json.dumps(cond, sort_keys=True, ensure_ascii=False)
        if _ck in _seen_c:
            rank -= 1
            continue
        _seen_c.add(_ck)

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2940「"side": side, "value": _thr_fixed(limits)}」
状態: 確定

#### 実装 6
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: STAGE_SPEC の段1（B-6）
直す前の文字:
~~~
    "stage1":  {"label": None,   "pick": "lineage"},

~~~
直した後の文字:
~~~
    # ★2026-10-01（B-6・まこさん決定「それでいいので進めて」）＝段1・段2c は強さ（場面の正解＝実際にレンジだったか）の順に並べる。
    #   直す前は None＝3つの正解を混ぜた順で、段1 の1位は「大きさ・先288本」で上がった
    "stage1":  {"label": "強さ", "pick": "lineage"},

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2538「"stage1":  {"label": None,   "pick": "lineage"},」
状態: 確定

#### 実装 7
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: STAGE_SPEC の段2c（B-6）
直す前の文字:
~~~
    "stage2c": {"label": None,   "pick": "family"},

~~~
直した後の文字:
~~~
    "stage2c": {"label": "強さ", "pick": "family"},

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:2541「"stage2c": {"label": None,   "pick": "family"},」
状態: 確定

#### 実装 8
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: selftest の前に、T48 の本体 selftest_stages を足す（B-1・B-2・B-5・B-6）
直す前の文字:
~~~
def selftest() -> int:

~~~
直した後の文字:
~~~
def selftest_stages() -> list:
    """T48（2026-10-01・工事 m2f-label-builder-stages-20261001）＝B-1 上端・B-2 出る線の向き・B-5 重なり・B-6 並べる正解。

    ★selftest の T48 と、口 --selftest-stages の両方がこの1本を呼ぶ（判定を2か所に書き写さない）。
      --selftest の全体は約6分半で、承認の前の仮当ての打ち切り（300秒）を超えるため、この口で短く走らせる。
    戻り＝ダメだった件の一覧（空なら全部 通った）。
    """
    t48 = []

    def _find_not48(t):
        if isinstance(t, dict):
            if isinstance(t.get("not"), dict) and t["not"].get("form") == "level":
                return t["not"]
            for _v in t.values():
                _r = _find_not48(_v)
                if _r:
                    return _r
        if isinstance(t, list):
            for _v in t:
                _r = _find_not48(_v)
                if _r:
                    return _r
        return None
    try:
        _lm48, _w48 = load_limits()
        _lm48h = {**_lm48, "stage_keep_range": {"lo": 1, "hi": 10, "kind": "int"}}
        if stage_keep_of(_lm48h, 1) != 1:
            t48.append("B-1: 上端10・候補1本で 1 にならない")
        if STAGE_SPEC["stage1"]["label"] != "強さ" or STAGE_SPEC["stage2c"]["label"] != "強さ":
            t48.append("B-6: 段1・段2c の label が強さでない")
        _laws48 = laws_for_scene("range")
        _tb48 = load_signal_table()
        _pool48, _tfs48, _ = material_pool()
        for _st48 in ("stage1", "stage2a", "stage2c"):
            _cs48 = build_stage_candidates(_st48, _laws48, _tb48, _tfs48, _lm48)
            _ks48 = [json.dumps(_c["cond"], sort_keys=True, ensure_ascii=False) for _c in _cs48]
            if len(_ks48) != len(set(_ks48)):
                t48.append(f"B-5: {_st48} に同じ条件が {len(_ks48) - len(set(_ks48))} 本 重なる")
            if _st48 != "stage2a" and any(_c.get("label") not in ("強さ", None) for _c in _cs48):
                t48.append(f"B-6: {_st48} の候補に強さ以外の正解で並んだ物が在る")
        _bd48, _dr48 = sample_regime_build(_lm48h, _pool48, _tfs48, _tb48)
        _hy48 = _bd48["entry"]["tree"]["all"][0]
        _n48 = _find_not48(_hy48["on"])
        _o48 = _hy48["off"]["any"][2]
        _qi48 = int(str(_n48["value"]["threshold_q"]).lstrip("q"))
        _qo48 = int(str(_o48["value"]["threshold_q"]).lstrip("q"))
        if _o48["side"] != _n48["side"] or not ((_qo48 > _qi48) if _n48["side"] == "above" else (_qo48 < _qi48)):
            t48.append(f"B-2: 段2a の出る線が緩い側でない（入る {_n48['side']} q{_qi48}・出る {_o48['side']} q{_qo48}）")
    except BaseException as _e48:                   # noqa: BLE001
        t48.append(f"途中で止まった: {type(_e48).__name__} {str(_e48)[:120]}")
    return t48


def selftest() -> int:

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:5026「def selftest() -> int:」
状態: 確定

#### 実装 9
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: selftest の T46 の後ろで T48 を呼ぶ（B-1・B-2・B-5・B-6）
直す前の文字:
~~~
    print("  T46 持続の内側が成立の全体: ①入る条件が持続1つ ②内側が条件の束 ③内側の本数が引いた記録と一致 ④並びが A・B・C・(D)・(G)")

~~~
足す文字:
~~~
    # ══ T48（2026-10-01・工事 m2f-label-builder-stages-20261001）＝本体は selftest_stages（口 --selftest-stages と同じ1本）══
    t48 = selftest_stages()
    ng += [f"T48: {_x}" for _x in t48]
    print("  T48 段の不具合の直し: B-1 上端が候補の本数を超えても組める ／ B-2 強さの否定の出る線は緩い側 ／ B-5 同じ条件を2回 並べない ／ B-6 段1・段2c は強さで並べる")

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:7739「print("  T46 持続の内側が成立の全体」
状態: 確定

#### 実装 10
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 旗 --selftest-stages を足す
直す前の文字:
~~~
                         "壊すプログラム b38 が使う（設計書 demand-in-ranking-20260907）")

~~~
足す文字:
~~~
    ap.add_argument("--selftest-stages", action="store_true",
                    help="段の不具合の直し（B-1・B-2・B-5・B-6）だけを試す＝T48 と同じ本体（selftest_stages）を呼ぶ"
                         "（全体の --selftest は約6分半で、承認の前の仮当ての打ち切り300秒を超えるため）")

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:7928「壊すプログラム b38 が使う（設計書 demand-in-ranking-20260907）」
状態: 確定

#### 実装 11
対象のファイル: scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 旗 --selftest-stages の口
直す前の文字:
~~~
    a = ap.parse_args()

~~~
足す文字:
~~~
    if a.selftest_stages:
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001）＝T48 だけを短く走らせる口（--selftest-rank-demand と同じ作り）
        _ng48 = selftest_stages()
        for _x in _ng48:
            print(f"  ❌ T48: {_x}")
        print(f"  {'❌' if _ng48 else '✅'} T48 段の不具合の直し／ダメだった件 {len(_ng48)}")
        return 1 if _ng48 else 0

~~~
根拠の抜き書き: scripts/priority_rebuild/engine_tuner_gen.py:7929「a = ap.parse_args()」
状態: 確定

#### 実装 12
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: _loosened_off の not の中身の緩める向き（B-2）
直す前の文字:
~~~
            cc["value"]["threshold_q"] = g._loose_q_fixed(limits, q, side)

~~~
直した後の文字:
~~~
            # ★2026-10-01（B-2）＝not の中身（段2a の強さ）は、緩める向きを入る線と反対にする（強さ above qX の否定で入るなら、
            #   出るのは above q(X+1)）。帯の幅と段1 は今までどおり（側を返したうえで隣の段へ）
            _ls = ("below" if side == "above" else "above") if is_not else side
            cc["value"]["threshold_q"] = g._loose_q_fixed(limits, q, _ls)

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:354「cc["value"]["threshold_q"] = g._loose_q_fixed(limits, q, side)」
状態: 確定

#### 実装 13
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_stage の前に、段1 の両側と差し戻しの枠の関数を足す（B-3・B-4）
直す前の文字:
~~~
def run_stage(df, a) -> int:

~~~
直した後の文字:
~~~
def _both_sides(cands: list) -> list:
    """段1 の候補に、側を返した帯を後ろに足す（2026-10-01・工事 m2f-label-builder-stages-20261001 の B-3・監査 CP49 の修正5）。

    ★組む側は帯の向きを案の番号で上下交互に決める（engine_tuner_gen.py の sample_regime_build）が、一覧の側は
      法則が側を決めない帯で above だけ＝下側の帯が段1 で1本も測られなかった。
    """
    out = list(cands)
    for c in cands:
        cc = json.loads(json.dumps(c))
        cc["cond"]["side"] = "below" if cc["cond"].get("side", "above") == "above" else "above"
        cc["側を返した"] = True
        out.append(cc)
    return out


def _sweep_slots(cf: list, wrap) -> list:
    """差し戻しで入れ直す枠の並び＝条件の枠＋（包みが在れば）持続の枠＋（段2c の枠が無ければ）段2c を足す枠（2026-10-01・B-4）。"""
    return list(cf) + (["stage3"] if wrap else []) + ([] if "stage2c" in cf else ["stage2c+"])


def _slot_variants(tag: str, inner: list, cf: list, wrap, st: str, k: int, cands_of: dict) -> list:
    """差し戻しの1つの枠を入れ直した束の一覧＝[(名前, 内側, 包み, 枠)]（2026-10-01・B-4・監査 CP49 の修正7）。

    ★段2c の枠は「なし」（段2c の条件を外した束）も試す（§2.2 の段2c「「なし」を必ず併走」）。
    ★段2c の枠が無い束（「なし」で勝った束）は、段2c の候補を足した束を試す（段4「全候補を1枠ずつ入れ直して1周」）。
    """
    v = []
    if st == "stage2c+":
        for j, c in enumerate(cands_of["stage2c"]):
            v.append((f"{tag}_c{j}", list(inner) + [json.loads(json.dumps(c["cond"]))], wrap, list(cf) + ["stage2c"]))
        return v
    if st == "stage2c" and k < len(cf):
        v.append((f"{tag}_none", list(inner[:k]) + list(inner[k + 1:]), wrap, list(cf[:k]) + list(cf[k + 1:])))
    for j, c in enumerate(cands_of[st]):
        nm = f"{tag}_c{j}"
        if k < len(cf):
            iv = json.loads(json.dumps(inner))
            iv[k] = json.loads(json.dumps(c["cond"]))
            v.append((nm, iv, wrap, list(cf)))
        else:
            wv = dict(wrap)
            wv["持続n"] = int(c["cond"]["value"]["n"])
            v.append((nm, inner, wv, list(cf)))
    return v


def run_stage(df, a) -> int:

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:409「def run_stage(df, a) -> int:」
状態: 確定

#### 実装 14
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_stage の段1 で両側の帯を測る（B-3）
直す前の文字:
~~~
             else g.build_stage_candidates(a.stage, laws, table, tfs, lm))

~~~
足す文字:
~~~
    if a.stage == "stage1":
        cands = _both_sides(cands)               # ★2026-10-01（B-3）＝帯の下側も測る

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:419「else g.build_stage_candidates(a.stage, laws, table, tfs, lm))」
状態: 確定

#### 実装 15
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_sweep の _measure_one の印に枠も持たせる（B-4）
直す前の文字:
~~~
            marks[nm] = (iv, wv)

~~~
直した後の文字:
~~~
            marks[nm] = (iv, wv, fv)               # ★2026-10-01（B-4）＝「なし」と足す側で枠が変わるので、枠も持つ

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:535「marks[nm] = (iv, wv)」
状態: 確定

#### 実装 16
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_sweep の枠の入れ直し（B-4）（1/6）
直す前の文字:
~~~
        slots = list(cf) + (["stage3"] if wrap else [])
        for st in slots:
            if st not in cands_of:
                cands_of[st] = (g.build_width_candidates(laws, table, tfs, lm) if st == "width"
                                else g.build_stage_candidates(st, laws, table, tfs, lm))

~~~
直した後の文字:
~~~
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-4・監査 CP49 の修正7）＝段2c の枠には「なし」も試し、
        #   段2c の枠が無い束（「なし」で勝った束）には「段2c を足す」枠を足す。枠の並びは周ごとに作り直す。
        for st in _sweep_slots(cf, wrap) + ["stage2c"]:
            st0 = "stage2c" if st == "stage2c+" else st
            if st0 not in cands_of:
                cands_of[st0] = (g.build_width_candidates(laws, table, tfs, lm) if st0 == "width"
                                 else g.build_stage_candidates(st0, laws, table, tfs, lm))

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:549「# ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠」
状態: 確定

#### 実装 17
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_sweep の枠の入れ直し（B-4）（2/6）
直す前の文字:
~~~
            for k, st in enumerate(slots):
                variants = []
                for j, c in enumerate(cands_of[st]):
                    nm = f"sweep_b{b_i}_r{rnd}_f{k}_c{j}"
                    if k < len(cf):
                        iv = json.loads(json.dumps(inner))
                        iv[k] = json.loads(json.dumps(c["cond"]))
                        variants.append((nm, iv, wrap, cf))
                    else:
                        wv = dict(wrap)
                        wv["持続n"] = int(c["cond"]["value"]["n"])
                        variants.append((nm, inner, wv, cf))

~~~
直した後の文字:
~~~
            for k, st in enumerate(_sweep_slots(cf, wrap)):
                variants = _slot_variants(f"sweep_b{b_i}_r{rnd}_f{k}", inner, cf, wrap, st, k, cands_of)

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:549「# ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠」
状態: 確定

#### 実装 18
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_sweep の枠の入れ直し（B-4）（3/6）
直す前の文字:
~~~
                cand_best = next((r for r in rows if r.get("判定") in marks and "①時間の割合" in r), None)

~~~
直した後の文字:
~~~
                cand_best = next((r for r in rows if r.get("判定") in marks and "①時間の割合" in r), None)
                _len0 = len(cf)

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:549「# ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠」
状態: 確定

#### 実装 19
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_sweep の枠の入れ直し（B-4）（4/6）
直す前の文字:
~~~
                    inner, wrap = marks[cand_best["判定"]]

~~~
直した後の文字:
~~~
                    inner, wrap, cf = marks[cand_best["判定"]]

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:549「# ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠」
状態: 確定

#### 実装 20
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_sweep の枠の入れ直し（B-4）（5/6）
直す前の文字:
~~~
                print(f"[差し戻し] 束 {b_i}・周 {rnd}・枠 {k}（{st}）＝いまの最良 {best.get('判定')}")

~~~
直した後の文字:
~~~
                print(f"[差し戻し] 束 {b_i}・周 {rnd}・枠 {k}（{st}）＝いまの最良 {best.get('判定')}")
                if len(cf) != _len0:
                    break                 # ★枠の数が変わった（「なし」か足す側が勝った）＝枠の並びを作り直して周の頭から

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:549「# ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠」
状態: 確定

#### 実装 21
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: run_sweep の枠の入れ直し（B-4）（6/6）
直す前の文字:
~~~
        best_row["枠"] = frames

~~~
直した後の文字:
~~~
        best_row["枠"] = cf

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:549「# ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠」
状態: 確定

#### 実装 22
対象のファイル: scripts/priority_rebuild/regime_r9_diag.py
直す箇所: selftest の⑤の前に ⑭⑮⑯ を足す（B-2・B-3・B-4）
直す前の文字:
~~~
    # ⑤ 印の作り方が観察の道具の実物と同じ関数であること（写しを作っていない）

~~~
直した後の文字:
~~~
    # ⑭ 段2a の強さの否定の出る線は、入る線より緩い側（above なら1つ大きい分位）（2026-10-01・B-2）
    try:
        import engine_tuner_gen as _g14
        _lm14, _w14 = _g14.load_limits()
        _c14 = [{"not": {"role": "env", "form": "level", "material": [{"family": "ADX", "param": 14, "tf": "1h"}],
                         "side": "above", "value": {"threshold_q": "q50"}}}]
        _o14 = _loosened_off(_c14, _lm14, frames=["stage2a"])["any"][0]
        if _o14["value"]["threshold_q"] != "q51" or _o14["side"] != "above":
            ng.append(f"⑭: 強さの否定の出る線が緩い側でない（{_o14['side']} {_o14['value']['threshold_q']}）")
    except BaseException as _e14:
        ng.append(f"⑭: 出る線を作る所で止まった: {type(_e14).__name__} {str(_e14)[:80]}")
    # ⑮ 段1 は帯の上側と下側の両方を測る（2026-10-01・B-3）
    _b15 = _both_sides([{"rank": 1, "cond": {"side": "above", "value": {"threshold_q": "q50"}}}])
    if sorted(c["cond"]["side"] for c in _b15) != ["above", "below"]:
        ng.append("⑮: 段1 の候補に上側と下側の両方が無い")
    # ⑯ 差し戻しの段2c の枠に「なし」を入れ、段2c の枠が無い束には段2c を足す（2026-10-01・B-4）
    _co16 = {"stage2c": [{"cond": {"x": 1}}], "stage1": [{"cond": {"y": 1}}]}
    _v16a = _slot_variants("t", [{"a": 1}, {"b": 1}], ["stage1", "stage2c"], None, "stage2c", 1, _co16)
    _v16b = _slot_variants("t", [{"a": 1}], ["stage1"], None, "stage2c+", 1, _co16)
    if (not any(_nm.endswith("_none") and _fv == ["stage1"] for _nm, _iv, _wv, _fv in _v16a)
            or not any(_fv == ["stage1", "stage2c"] for _nm, _iv, _wv, _fv in _v16b)
            or _sweep_slots(["stage1"], None) != ["stage1", "stage2c+"]):
        ng.append("⑯: 差し戻しで段2c の「なし」か、段2c を足す束が試されない")
    # ⑤ 印の作り方が観察の道具の実物と同じ関数であること（写しを作っていない）

~~~
根拠の抜き書き: scripts/priority_rebuild/regime_r9_diag.py:787「# ⑤ 印の作り方が観察の道具の実物と同じ関数であること（写しを作っていない）」
状態: 確定

#### 実装 23
対象のファイル: scripts/priority_rebuild/recipes/search_limits.json
直す箇所: stage_keep_range の hi（K-1）
直す前の文字:
~~~
  "stage_keep_range": { "lo": 1, "hi": null, "kind": "int" },

~~~
直した後の文字:
~~~
  "stage_keep_range": { "lo": 1, "hi": 10, "kind": "int" },

~~~
根拠の抜き書き: scripts/priority_rebuild/recipes/search_limits.json:50「"stage_keep_range": { "lo": 1, "hi": null, "kind": "int" },」
状態: 確定

<!-- ACC_IMPL_END -->

［自動］まこさんが OK した案の【番号】の「非該当＝」の後ろの文と、項目の正本の名前
**非該当の項目（理由と出どころ）**＝4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）＝探す値の範囲は変えない（渡す本数の上端だけを書く）／4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）＝書き先を変えない（順位表と落ちた候補は results/priority_rebuild/regime_r9/ の日時つきの新しいファイル）／4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）＝時刻の列・足の区切りに触らない／4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）＝同時に2つ走らせない／4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）＝鍵・本番の発注に触らない

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
| 4-7 | 条件 | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 非該当（探す値の範囲は変えない（渡す本数の上端だけを書く）） |
| 4-9 | 条件 | 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗） | 書いた |
| 4-12 | 必ず | 出る結果の姿（完成したとき、何がどう表示されるか） | 書いた |
| 4-5 | 必ず | 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか） | 書いた |
| 4-8 | 条件 | データ構造（表や JSON の列と中身を、新しく作るか・変えるか） | 書いた |
| 4-10 | 条件 | 保存先（出したものをどこに置くか・上書きか、書き足すか） | 非該当（書き先を変えない（順位表と落ちた候補は results/priority_rebuild/regime_r9/ の日時つきの新しいファイル）） |
| 4-11 | 条件 | 時刻の扱い（時間帯・足の区切りをどこで切るか） | 非該当（時刻の列・足の区切りに触らない） |
| 4-14 | 条件 | 性能（どれくらい時間が掛かり、どれくらい容量を使うか） | 書いた |
| 4-15 | 条件 | 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか） | 非該当（同時に2つ走らせない） |
| 4-16 | 条件 | セキュリティ（人に見せてはいけない値と、書き換えられては困る記録） | 非該当（鍵・本番の発注に触らない） |
| 4-17 | 省ける | ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか） | 書いた |
| 4-13 | 必ず | 影響範囲（この直しで、ほかのどれが壊れるか） | 書いた |
| 4-18 | 省ける | 再利用（手本にした、既にあるものの形） | 書いた |
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 23 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 14a（札の構造）と分け、14b と15番だけの工事にする | まこさんの指示（req_split_20261001）。6d とまとめた案は約10万文字で1回の返信に収まらない | 設計書の道具を直して【4-20】をファイルから読む（まこさん「修正せずに」） |
| 2 | B-1 は上端を候補の本数に切り詰める（止めない） | 段2b の候補は1本で、上端10 を書くと束が1本も組めない。下端の検査は残す | 段ごとに別の上端を設定に持たせる |
| 3 | B-2 は not の中身だけ、緩める向きを反対にする | 帯の幅と段1 は _flip_loose で側を返していて正しい向き。not の中身だけが強さの側のまま緩めていた | not の中身も側を返す（強さが戻ったら出る形でなくなる） |
| 4 | B-3・B-4 の作りは測る道具に小さな関数（_both_sides・_sweep_slots・_slot_variants）として足し、自己テストで直に試す | 合成データで段の走行を丸ごと回さなくても、両側と「なし」と足す側を確かめられる | run_stage・run_sweep の中に直に書く |
| 5 | B-5 は条件の中身（JSON）が同じ候補を飛ばし、順位を詰める | 同じ列の行はまったく同じ束（段1 に動く線は無い）。順位を詰めないと、組む側の順位で取る束がずれる | 測る道具の側で重なりを除く（組む側の重なりが残る） |
| 6 | B-6 は強さで並べる | まこさん決定（ok_todo_20261001）。M2-A で決めた場面の正解は強さだけ | 3つの正解を混ぜた順のまま |
| 7 | T48 を短く走らせる口 --selftest-stages を足す | 組む側の --selftest の全体は約6分半で、承認の前の仮当ての打ち切り300秒を超える（2026-10-01 の試しで打ち切られた） | 完成の条件を全体の --selftest にする |
| 8 | 固定のレシピ r9_demand_fixture.json の出る線は直さない | 需給の列が足されるかを測るためのレシピで、出る線の向きは測る中身に関係しない。直すと直す前と同じ結果を確かめる条件が崩れる | 同じ回に直す |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=f78a4bf12b6a4520 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `—` | #1・#2・#3 | — |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 段1 の束が2倍になり、段1 の走行が約49分 → 約98分（目安・未測定） | 走らせる前に、束1本の時間を小さく測ってフロー宣言に見込みを書く（恒久60〜62番） |
| 2 | 組む側の --selftest は全体で約6分23秒（b35 の注記の実測）。承認の打ち切り120秒より長い | 完成の条件の壊すプログラムは「—」にし、承認の後に --selftest を直接 走らせて貼る |
| 3 | B-5 で順位を詰めるので、組む側が順位で取る束（sample_regime_build の B・C・G）の中身が直す前と変わる | T48 と既存の T24・T39〜T47 を走らせて、束が組めて法則の審査を通ることを確かめる |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 組む側の自己テスト（T48 を含む全体） | 約6分半 | python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest の全体（b35_gate_branch_gone.sh の注記の実測＝6分23秒） |
| 測る道具の自己テスト（⑭⑮⑯ を含む） | 1分以内の見込み | ⑪ の合成データの走行を含む既存の自己テスト（時間の実測の記録は未確認） |
| G2 → H2 の印の取り直し | 約30秒 ＋ 約5分 | next_step の印の節 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝段の候補を作る側と測る道具が、§2.2 の段の探し方の一部（上端の扱い・出る線の向き・段1 の下側・3枠目の「なし」・重なり・並べる正解）を実装していなかったこと（milestones2 の M2-F-13b）。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。

**③ root か symptom か**＝root です。止まる所・向き・測り漏れ・重なり・並べる正解を、それぞれの関数で直します（結果を後から手で直す運用にしません）。

**④ ベースアップ**＝手本＝_flip_loose（出る線の向き・engine_tuner_gen.py:3135〜3145）・stage_keep_of の下端の検査・run_stage の段2c の「なし」の併走・--selftest-rank-demand の口の作り（engine_tuner_gen.py:7926〜7937）。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。渡す本数の上端10は まこさんの決定（2026-09-18）です。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝段の候補を作る側と測る道具を、M2-F の段の走行（M2-F-8〜15）に使える形にする（段の不具合6つと、渡す本数10本）。札の構造（14a）は別の工事に分けた（req_split_20261001）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | ランダムに条件をつなぐだけのもの、ではありません。段の候補は法則が名指しした物を成績表の順位で並べ、乱数を使いません（測る道具の⑦と組む側の T24 が乱数の道を見る）。 |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 探す値を CC が先に点の一覧で限定するもの、ではありません。探す値の範囲は変えず、渡す本数の上端10は まこさんの決定です。 |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **B-3 で側を返した帯が、法則として意味のある帯か** | 道具は側を返すだけで、帯の向きの意味は見ない（法則が側を決めない帯だけに当たる） |
| **B-4 の差し戻しが、良くならなくなるまでに何周 回るか** | 周の数の上限は持たない（直す前と同じ） |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=185973f1e19bc5a8 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝3本（組む側 engine_tuner_gen.py・測る道具 regime_r9_diag.py・設定 search_limits.json）を【7-8】に書いた。1ファイルに収まらないのは、段の候補を作る側と測る側の両方に同じ不具合が在るため（7-3）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝engine_tuner_gen.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 非該当（新しいファイルを作らない）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝直す前の文字が実物にちょうど1か所ずつ在ることを道具で数えた。142回目に、読むもの宣言のために直す相手と関係の無い壊すプログラムまで全部 読み込んだ誤りは再演しない（直す行を探す物だけに絞る）。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 非該当（売買のロジックの部品・前処理を足さない）。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書は、実装の後に git grep で数え、ずれを直す（gen_regime_kb.py --verify の引用の実在検査で見る）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前で壊すプログラムを grep した。14b で直す行を探す物の探す文字は、この工事の直す前の文字と重ならない（4-13）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 非該当（壊すプログラムを新しく作らない）。b97 は、壊した道具が results/ に書いた順位表と落ちた候補を消す形のまま。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数（selftest_stages・_both_sides・_sweep_slots・_slot_variants）は、全部 DESIGN_CONTRACT の impl_functions に書いた（【7-8】）。＝engine_tuner_gen.py: <モジュール直下>・stage_keep_of・build_stage_candidates・sample_regime_build・selftest_stages・selftest・main ／ regime_r9_diag.py: _loosened_off・_both_sides・_sweep_slots・_slot_variants・run_stage・run_sweep・selftest |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗 --selftest-stages は、完成の条件の行が走らせる。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2f-label-builder-stages-20261001）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝組む側の --selftest-stages（T48）・測る道具の --selftest（⑭⑮⑯）・承認の前の検査。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | 上端が候補の本数を超えても組む側がレンジの判定の束を組め、段2a の出る線が緩い側に在り、段の候補に同じ条件が2回 並ばず、段1・段2c は強さで並ぶ（T48＝B-1・B-2・B-5・B-6） | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest-stages` | 実経路 | — | `—` | 要 | **未着手** |
| 2 | 測る道具の出る線が緩い側（⑭）・段1 が上側と下側の両方の帯を測る（⑮）・差し戻しが段2c の「なし」と足す側を試す（⑯） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | — | `—` | 要 | **未着手** |
| 3 | 渡す本数の上端が10（K-1） | `jq '.stage_keep_range.hi' scripts/priority_rebuild/recipes/search_limits.json` | 実経路 | — | `—` | 要 | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=57503b9a4df57026 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/engine_tuner_gen.py`

| 触る関数 | 定義の行 |
|---|---|
| `selftest_stages` | 5043 |
| `_seen_c` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 161件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=8c72c6a11d92927f gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "self_check_calls": [
    "selftest_stages",
    "_seen_c"
  ],
  "impl_functions": {
    "scripts/priority_rebuild/engine_tuner_gen.py": [
      "<モジュール直下>",
      "stage_keep_of",
      "build_stage_candidates",
      "sample_regime_build",
      "selftest_stages",
      "selftest",
      "main"
    ],
    "scripts/priority_rebuild/regime_r9_diag.py": [
      "_loosened_off",
      "_both_sides",
      "_sweep_slots",
      "_slot_variants",
      "run_stage",
      "run_sweep",
      "selftest"
    ]
  },
  "must_use": {
    "run_stage": [
      "_both_sides"
    ],
    "run_sweep": [
      "_sweep_slots",
      "_slot_variants"
    ]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この工事の道具が外から読む一覧の形は変えない",
  "generated_from": {
    "impl_functions": "4-3 に書いた、この工事で触る所",
    "must_use": "直した後に呼ぶ名前（4-3）",
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
  "pre_win_bars": [
   "SampleError"
  ],
  "stage_warm": [
   "pre_win_bars",
   "stage_candidates"
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
   "pre_win_bars",
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
  "selftest_stages": [
   "build_stage_candidates",
   "laws_for_scene",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "sample_regime_build",
   "stage_keep_of"
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
   "pre_win_bars",
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
   "selftest_stages",
   "stage_candidates",
   "stage_counts",
   "stage_keep_of",
   "stage_lineages_of",
   "stage_tfs_of",
   "stage_warm",
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
   "run_generation",
   "stage_warm"
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
   "selftest_stages",
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
  "_EXEC_BAR_MIN": 5,
  "ATTACH_CALLS": 0
 },
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->
