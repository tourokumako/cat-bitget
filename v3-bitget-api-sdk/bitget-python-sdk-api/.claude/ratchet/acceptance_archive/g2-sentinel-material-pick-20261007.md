<!-- ARC iter="g2-sentinel-material-pick-20261007" -->

# 設計書｜G2 の番人が、指標の材料を持つ構造を選ぶ形に直す。M2-C-15

TARGET: scripts/priority_rebuild/gen_signal_families.py, .claude/breaks/b144_g2_sentinel_first_clean.sh
NEW_FILE: .claude/breaks/b144_g2_sentinel_first_clean.sh
MODEL: .claude/breaks/b141_catalog_out_of_range.sh

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `g2-sentinel-material-pick-20261007/ok_r6_20261007`・`g2-sentinel-material-pick-20261007/okd_r6_20261007`・`g2-sentinel-material-pick-20261007/req_a_20261007`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/g2-sentinel-material-pick-20261007/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work g2-sentinel-material-pick-20261007 --write`。検出＝`--work g2-sentinel-material-pick-20261007 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=32c36101bd8a9619 gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/g2-sentinel-material-pick-20261007/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/g2-sentinel-material-pick-20261007/ok_r6_20261007.txt`（まこさんの発言）・`verbatim/g2-sentinel-material-pick-20261007/okd_r6_20261007.txt`（まこさんが OK した CC の文）・`verbatim/g2-sentinel-material-pick-20261007/req_a_20261007.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝244 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_r6_20261007` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r6_20261007` | V01〜V13（13 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_r6_20261007` | V14〜V23（10 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V24〜V27（4 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V28〜V32（5 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V33〜V41（9 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V42〜V47（6 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V48〜V53（6 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V54〜V61（8 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V62〜V63（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V64〜V65（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V66〜V67（2 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V68〜V69（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V70〜V71（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V72〜V76（5 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V77〜V83（7 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V84〜V87（4 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V88〜V89（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V90〜V91（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V92〜V93（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V94〜V99（6 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V100〜V124（25 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V125〜V130（6 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V131〜V135（5 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V136〜V143（8 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V144〜V150（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V151〜V152（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V153〜V154（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V155〜V159（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V160〜V169（10 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V170〜V190（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V191〜V194（4 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V195〜V238（44 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_r6_20261007` | V239〜V242（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_a_20261007` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
同じ日の工事 m2c15-rci-pivot-sources-20261007 で、材料に RCI5 が1本 増えました。そのあと監査に出す前のチェックで、G2（型の表に沿った案かを見る検査）だけが「差し替えられる材料が構造に無い」で落ちました。G2 の番人は、生成器に乱数（種は固定）で構造を作らせ、表に沿った1本目の構造の、最初の指標の材料を差し替えて既知答えを作ります。材料が1本 増えると同じ種でも引かれる構造が変わり、1本目に指標の材料が無くなりました。番人の作りが乱数の引き方に頼っていたのが原因です。この工事は、番人が「表に沿っていて、指標の材料を持つ最初の構造」を選ぶ形に直します（まこさん「A」）。構造を乱数で作る作りは残ります（入口の乱数を外すのは M3 です）。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| 番人が表に沿った1本目をそのまま使う所（F-1） | `grep -n -F 'base_st = copy.deepcopy(clean[0])' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py` | 実装の前は、在る。実装の後は、無い | 995:    base_st = copy.deepcopy(clean[0])（終了コード 0） |
| 番人が指標の材料を持つ構造を選ぶ所（F-1） | `grep -n -F 'with_col = [st for st in clean' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py` | 実装の前は、無い。実装の後は、番人の関数の中に在る | （終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=b61112e623987231 gen_acceptance.py が自動生成＝手で書き換えない -->
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
| `material_param_ranges` | {"ADX": [{"kind": "int", "lo": 7, "hi": 21}], "DI差": [{"kind": "int", "lo": 7, "hi": 21}], "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}], "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "転換線": [{"kind": "int", "lo": 5, "hi": 12}], "基準線": [{"kind": "int", "lo": 13, "hi": 26}], "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}], "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}], "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TSI": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIシグナル": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIヒスト": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}], "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}], "AROONU": [{"kind": "int", "lo": 7, "hi": 288}], "AROOND": [{"kind": "int", "lo": 7, "hi": 25}], "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}], "VTXP": [{"kind": "int", "lo": 14, "hi": 30}], "VTXM": [{"kind": "int", "lo": 14, "hi": 30}], "RSI": [{"kind": "int", "lo": 2, "hi": 21}], "ROC": [{"kind": "int", "lo": 9, "hi": 24}], "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}], "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}], "MFI": [{"kind": "int", "lo": 10, "hi": 20}], "CMF": [{"kind": "int", "lo": 20, "hi": 36}], "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}], "BB%b": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}], "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}], "CCI": [{"kind": "int", "lo": 7, "hi": 21}], "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "StochRSI%K": [{"kind": "int", "lo": 7, "hi": 21}], "StochRSI%D": [{"kind": "int", "lo": 7, "hi": 21}], "DPO%": [{"kind": "int", "lo": 14, "hi": 40}], "EFI比": [{"kind": "int", "lo": 10, "hi": 20}], "EOM比": [{"kind": "int", "lo": 10, "hi": 20}], "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}], "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}], "ATR%": [{"kind": "int", "lo": 5, "hi": 21}], "BB幅": [{"kind": "int", "lo": 20, "hi": 50}, {"kind": "float", "lo": 2.0, "hi": 2.0, "dec": 1}], "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}], "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}], "MMI": [{"kind": "int", "lo": 200, "hi": 500}], "ER": [{"kind": "int", "lo": 7, "hi": 21}], "CHOP": [{"kind": "int", "lo": 7, "hi": 21}], "VHF": [{"kind": "int", "lo": 7, "hi": 28}], "MAD比": [{"kind": "int", "lo": 20, "hi": 50}], "stdev%": [{"kind": "int", "lo": 10, "hi": 50}], "UI": [{"kind": "int", "lo": 7, "hi": 21}], "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "形スコア": [{"kind": "int", "lo": 24, "hi": 96}], "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.003, "hi": 0.003, "dec": 3}], "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}], "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}], "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "n本高値": [{"kind": "int", "lo": 10, "hi": 50}], "n本安値": [{"kind": "int", "lo": 10, "hi": 50}], "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}], "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}], "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}], "fib位置": [{"kind": "int", "lo": 14, "hi": 96}], "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}], "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}], "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}], "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}], "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}], "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}], "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}], "RCI": [{"kind": "int", "lo": 5, "hi": 52}]} |

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
| 1 | 生成器（sample_structure）から乱数を外すこと | 入口の乱数を外すのは M3（まこさんが決めた順番）。この工事は番人が使う構造の選び方だけを直す | 恒久67番 |
| 2 | 番人の既知答えの中身を変えること | 何を差し替えて、何で止まるはずかは変えない。選ぶ構造が変わるだけ | 読むもの宣言の入れないもの |
| 3 | 監査に出す前のチェックの自己テストの P7-1 の落ち | この工事の前から在る。next_step §6 に積む | worklog 20261007 §11 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 直し方（A か B か） | 決定済み＝A（まこさん「A」2026-10-07） | req_a_20261007 |
| 2 | 監査の出し方 | 今日の3つの工事（m2c15-param-values-fix-20261007・m2c15-rci-pivot-sources-20261007・この工事）をまとめて、実装の監査 CP64 の1回に出す | 前の工事の 3-2 の1行目 |
| 3 | 目的の照合（purpose_check.md）の条件の書き方 | 事実だけを書く。パラメータ＝「今のまま」。閾値＝「今のまま」。時間足＝「今のまま」（番人の構造の選び方だけを直す） | 前の工事の 3-2 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、G2 の番人が既知答えの元にする構造の選び方を直す工事です。**G2 は、型の表に沿った案かを審査する処理（_judge_structure）が、見本に正しく反応するかを試す検査です。G2 が通ったときだけ検査済みの印が書かれ、印が無いと engine_tuner は回りません。
**①いま何が起きているか。**
- 番人（gen_signal_families.py の _g2_selftest_body）は、生成器に乱数（種は固定）で構造を30本 作らせ（_real_structures）、表に沿ったものだけを残します。
- 残った1本目の構造（clean[0]）を既知答えの元にし、その最初の指標の材料を、禁止3 の組・偽の指標・レンジ幾何・時間帯ほかに差し替えます。
- 同じ日の工事で材料に RCI5 が増えたので、同じ種でも引かれる構造が変わり、1本目の入口の条件に指標の材料が無くなりました。そのため「差し替えられる材料が構造に無い」で止まっています。
**②この工事で何が変わるか。**
- F-1：番人が、表に沿った構造のうち、指標の材料を持つ最初の構造を元に使います。そういう構造が1本も無いときは、そう言って止まります。
- 既知答えの中身（何を差し替えて、何で止まるはずか）は変えません。
- 構造を乱数で作る作りは残ります（入口の乱数を外すのは M3）。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、当てる道具 apply_audit_fix.py と、型の表の道具の --verify（G2）を動かします。承認のプログラム・監査に出す前のチェックも G2 を走らせます。
**誰が結果を使うか。**
- G2 が通ると、検査済みの印（.claude/state/g2_pass.json）が書かれ、enforce_g2_pass hook が engine_tuner を通します。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**今の実物（gen_signal_families.py）・型の表（signal_families.json）・生成器（engine_tuner_gen.py の sample_structure・material_pool）・設計書の 4-20。
**書くもの。**
- 当てる（--design）：gen_signal_families.py の1か所と、新しい壊すプログラム 1本。
- G2 が通ったとき：検査済みの印（g2_pass.json）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 乱数を新しく足さない | 恒久67番 | 足すのは、残った構造を前から順に見る絞り込みだけです。乱数は足しません |
| 作ってはいけないもの1番（ランダムに条件をつなぐだけのもの） | 要件 | 番人の既知答えの元の選び方を直すだけで、案を作る所は変えません |
| 未来のデータを使わない | 要件定義書 §4.6.H2 | 材料の計算は変えません。当てた後に H2 を取り直します |
| 値段の高さで値が変わらない | 要件定義書 §4.6.H6 | 材料の計算は変えません |
| 数字を CC が作らない | 思考の順の7（req_thinking_20261004） | 新しい数字はありません。構造の本数（30本）と種は前のままです |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| gen_signal_families.py の _g2_selftest_body | 既知答えの元にする構造を、表に沿っていて指標の材料を持つ最初の構造にする | 直す |
| .claude/breaks の壊すプログラム | 直しを戻すと、番人が決めた文で落ちるかを見る | 新設 |
- 触る関数は、指示を当てる前と後の構文木を比べて、道具が数えました（下の囲み）。
```
gen_signal_families.py＝_g2_selftest_body
```

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. まこさんの承認の後、全部を当てます（apply_audit_fix.py --design --dry → --design）。1件でも合わなければ1件も当てません。
2. 当てた直後に、当てる道具が G2 と H2 を自分で走らせます（gen_signal_families.py は G2 と H2 の対象です）。
3. 照合（verify_design_contract.py --diff）をかけます。
4. 壊すプログラムを走らせます。
5. 監査に出す前のチェック（pre_audit_check.py --run）を走らせ直し、今日の3つの工事をまとめて実装の監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝いまの番人。番人は生成器に構造を30本 作らせ、表に沿ったものだけを残します。いまは、残った1本目の構造の入口の条件に、指標の材料（family を持つ材料）が1つもありません。そのため、材料を禁止3 の組や偽の指標に差し替える既知答えが作れず、「差し替えられる材料が構造に無い」で止まります。直した後は、残った構造を前から順に見て、指標の材料を持つ最初の構造を使います。その構造の最初の指標の材料を差し替えて、前と同じ6件と足した4件の既知答えを作り、判定が期待どおりに反応するかを見ます。表に沿っていて指標の材料を持つ構造が1本も無いときは、そう言って止まります。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**変えません。**

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**変えません。**コマンドの旗も増やしません。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに出るもの。**
1. G2 が通る。コマンド＝python3 scripts/priority_rebuild/gen_signal_families.py --verify。画面に「G2 の既知答え 11件 全部 期待どおり」が出て、検査済みの印が書かれる。
2. 壊すプログラムが、決めた文で落ちる。コマンド＝python3 .claude/tools/run_breaks.py --design。
3. H2 が取り直される（監査に出す前のチェックの中）。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| --design の --dry で、当たらない件が出る | 1件も当てずに止まります。まこさんに報告します |
| 表に沿っていて指標の材料を持つ構造が1本も無い | 番人が「[番人エラー] 表に沿っていて指標の材料を持つ構造が1本も作れない」で止まります（G2 の印は書かれません） |
| 判定が既知答えに正しく反応しない | 番人が前と同じ形で落ちます（変えていない） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**変えません。**検査済みの印の形も前のままです。

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
| G2（--verify） | 45.5秒 | 同じ日の監査に出す前のチェックの実測（裏で走らせた画面の出力を .claude/state/indicator_review/pre_audit_run_20261007_1.log に控え、道具がそこから読んだ） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**ありません。**全部を --design の1回で当てるので、途中の状態は残りません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）は、取り直しの道具だけが書きます。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**変えません。**番人は今と同じく、既知答えごとに、期待どおりだったかどうかの行を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **gen_signal_families.py は G2 と H2 の対象です。**当てた後に G2 → H2 を取り直します。
2. **型の表の中身は変わりません。**表を作る所には触らないので、承認の指紋（0bdadafa…）はそのまま有効です。
3. **前からの壊すプログラムが探す文字の数は、当てる前と後で同じです。**道具が数えた相手は、下の囲みです。
```
なし
```

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| r5_proposal_build.py（同じ日の前の工事の道具） | 指示と壊すプログラムを作り、前からの壊すプログラムの探す文字を数え、一時の置き場で設計書を組む形 |
| 壊すプログラム b141 | 壊すプログラムの形（決めた文で落ちるかを見る） |
| 壊すプログラム b66 | G2 を守る壊すプログラム |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=2875312aba2a8bd6 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/priority_rebuild/gen_signal_families.py
直す箇所: 995〜1006行（_g2_selftest_body・G2 の番人が既知答えの元にする構造の選び方）
直す前の文字:
~~~
    base_st = copy.deepcopy(clean[0])

    def _first_col_cond(st):
        conds: list = []
        _walk_conds(st.get("entry", {}).get("connective", {}), conds)
        for c in conds:
            for m in (c.get("material") or []):
                if "family" in m:
                    return m
        return None

    ban_st = copy.deepcopy(base_st)

~~~
直した後の文字:
~~~
    def _first_col_cond(st):
        conds: list = []
        _walk_conds(st.get("entry", {}).get("connective", {}), conds)
        for c in conds:
            for m in (c.get("material") or []):
                if "family" in m:
                    return m
        return None

    # ★2026-10-07（工事 g2-sentinel-material-pick-20261007・まこさん「A」）＝表に沿っていて、指標の材料を持つ最初の構造を使う。
    #   直す前は表に沿った1本目（clean[0]）をそのまま使い、材料の一覧が1本 増えただけで（同じ日の RCI5）、
    #   1本目に指標の材料が無くなり「差し替えられる材料が構造に無い」で止まった（乱数の引き方に頼っていた）。
    with_col = [st for st in clean if _first_col_cond(st) is not None]
    if not with_col:
        raise SystemExit("[番人エラー] 表に沿っていて指標の材料を持つ構造が1本も作れない＝既知答えが作れない")
    base_st = copy.deepcopy(with_col[0])

    ban_st = copy.deepcopy(base_st)

~~~
根拠の抜き書き: scripts/priority_rebuild/gen_signal_families.py:995「base_st = copy.deepcopy(clean[0])」
状態: 確定

#### 実装 2
対象のファイル: .claude/breaks/b144_g2_sentinel_first_clean.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: G2 の番人が使う構造を、表に沿った1本目（clean[0]）に戻すと、番人が「差し替えられる材料が構造に無い」で落ちる
# EXPECT_MSG: 差し替えられる材料が構造に無い
# b144_g2_sentinel_first_clean — G2 の番人が使う構造を、表に沿った1本目（clean[0]）に戻すと、番人が「差し替えられる材料が構造に無い」で落ちる（工事 g2-sentinel-material-pick-20261007・2026-10-07）
#   守っているもの＝完成の条件の G2（gen_signal_families.py --verify）
#   壊し方＝scripts/priority_rebuild/gen_signal_families.py の中の、下の old を new に置き換える（直す前の形に戻す・承認の前の検査の仮当てで、落ちるのを確かめる）。
#   期待＝gen_signal_families.py --verify が「差し替えられる材料が構造に無い」で落ちる（終了コード 1・落ちたときは検査済みの印を書かない）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
#   ★いまの材料の一覧では、表に沿った1本目の構造に指標の材料が無いので落ちる。一覧が変わると落ちなくなることがある（設計書 7-4）。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/gen_signal_families.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    def _first_col_cond(st):\n        conds: list = []\n        _walk_conds(st.get("entry", {}).get("connective", {}), conds)\n        for c in conds:\n            for m in (c.get("material") or []):\n                if "family" in m:\n                    return m\n        return None\n\n    # ★2026-10-07（工事 g2-sentinel-material-pick-20261007・まこさん「A」）＝表に沿っていて、指標の材料を持つ最初の構造を使う。\n    #   直す前は表に沿った1本目（clean[0]）をそのまま使い、材料の一覧が1本 増えただけで（同じ日の RCI5）、\n    #   1本目に指標の材料が無くなり「差し替えられる材料が構造に無い」で止まった（乱数の引き方に頼っていた）。\n    with_col = [st for st in clean if _first_col_cond(st) is not None]\n    if not with_col:\n        raise SystemExit("[番人エラー] 表に沿っていて指標の材料を持つ構造が1本も作れない＝既知答えが作れない")\n    base_st = copy.deepcopy(with_col[0])\n\n    ban_st = copy.deepcopy(base_st)\n'
new = '    base_st = copy.deepcopy(clean[0])\n\n    def _first_col_cond(st):\n        conds: list = []\n        _walk_conds(st.get("entry", {}).get("connective", {}), conds)\n        for c in conds:\n            for m in (c.get("material") or []):\n                if "family" in m:\n                    return m\n        return None\n\n    ban_st = copy.deepcopy(base_st)\n'
if s.count(old) != 1:
    raise SystemExit("[b144_g2_sentinel_first_clean] 壊す対象の文字が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/gen_signal_families.py" --verify
finish

~~~
根拠の抜き書き: .claude/breaks/b141_catalog_out_of_range.sh:1「#!/bin/bash」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 2 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 表に沿っていて指標の材料を持つ最初の構造を使う | まこさん「A」。1か所の小さな直しで、材料が増えても落ちなくなる | 番人が乱数を使わずに決まった形の構造を作る（案 B・生成器の作りに関わり M3 と重なる） |
| 2 | そういう構造が1本も無いときは止まる | 黙って既知答えを減らさない（fail-closed） | 指標の材料が無いまま進める |
| 3 | 壊すプログラムは、直しを戻す形にする | 直す前の形で番人が落ちることを、いまの実物で確かめられる | 材料の一覧を書き換えて落とす |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=f883e7ba03e9a6ba gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b144_g2_sentinel_first_clean.sh` | #1 | 番人が使う構造を、表に沿った1本目に戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 構造は今も乱数（種は固定）で作る。材料の一覧がもっと変わると、表に沿っていて指標の材料を持つ構造が30本の中に1本も無い、ということは起こりうる | そのときは番人が言って止まる（4-5）。乱数を外すのは M3 |
| 2 | 壊すプログラムが落ちるのは、いまの材料の一覧で1本目に指標の材料が無いから。一覧が変わると、直しを戻しても落ちなくなることがある | 7-4 に書いた。そのときは壊し方を作り直す |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる（--design） | 1分未満 | 同じ日の前の工事で、当てる道具は1秒未満で終わった |
| G2 | 45.5秒 | 4-14 |
| H2 | 約5分 | 同じ日の実測（308.8秒） |
| 監査に出す前のチェック | 約10分 | 同じ日の実測（H2 を含む） |
| まこさんの承認 | 設計書は1回の見込み | 4-4 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝番人が、表に沿った1本目の構造をそのまま既知答えの元にしていた。構造は乱数（種は固定）で作るので、材料の一覧が1本 変わるだけで1本目が変わり、指標の材料が無い構造が来ると止まった。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は、この工事では動きません。G2 の印が書けるようになり、engine_tuner が回せる状態に戻ります。

**③ root か symptom か**＝番人の選び方の root です。構造を乱数で作る所（M3）は残ります。

**④ ベースアップ**＝番人のコード（_g2_selftest_body・_real_structures）と生成器（sample_structure・material_pool）を読んだ。いまの実物（直す前）で G2 が落ちることは、同じ日の監査に出す前のチェックで出た。直した後に通ることは、承認の前の検査の仮当てで確かめる。新しい Web の調べはしていません。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。構造の本数と種は前のままです。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝G2 の番人が既知答えの元にする構造の選び方。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

**★左の2列は、要件の正本からプログラムが取り出しています（手で写していません）。**出どころ＝`.claude/ratchet/engine_tuner_requirements.json`。**一覧が増えたら、この表も自動で増えます。**照合を書かないと設計書を作り直せません。

| # | 作ってはいけないもの（要件の逐語） | この工事は当たるか | 理由 |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 案を作る所は変えません。番人の既知答えの元の選び方を直すだけで、乱数も足しません |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 探す値には触りません |

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **構造を乱数で作ることを、この工事で塞ぐか** | 塞ぎません。入口の乱数を外すのは M3 です |
| **壊すプログラムが、材料の一覧が変わっても落ち続けるか** | 保証しません。いまの材料の一覧で、1本目に指標の材料が無いから落ちます。一覧が変わると落ちなくなることがあります |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=64958c463337bb59 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝gen_signal_families.py と、新しい壊すプログラムを【7-8】に書いた。主なファイルは gen_signal_families.py（G2 の番人）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝gen_signal_families.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは壊すプログラム（NEW_FILE）。手本は b141（MODEL）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝番人が乱数の引き方に頼り、材料が増えただけで落ちた。この工事で、指標の材料を持つ構造を選ぶ形にした。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | この工事は、新しい部品も前処理も足さない。材料の計算は変えない。当てた後に H2 を取り直す。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書は、番人の行より後ろが数行ずれる（設計書の CODEREF は道具が作り直す）。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前を本文に持つ壊すプログラムを全部 探し、探す文字の数が当てる前と後で同じことを道具が数えた（4-13 の3）。走らせるコマンドの旗は変えない。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムが測るのは gen_signal_families.py --verify で、落ちるときは検査済みの印を書かない。本物の結果の置き場には書かない。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数は無い。触る関数は DESIGN_CONTRACT の impl_functions に書いた（道具が当てる前と後の構文木で数えた）。must_use の名前は、当てた後の関数の中に在ることを道具が ast で照らした。gen_signal_families.py の触る関数＝_g2_selftest_body。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗は無い。番人は、完成の条件が走らせる --verify の中で通る。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=g2-sentinel-material-pick-20261007）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝G2 の番人そのもの（既知答え11件）と、壊すプログラム（直しを戻すと落ちるか）。承認の前の検査の仮当てで走らせる。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1＝G2 の番人が、表に沿っていて指標の材料を持つ構造を元に、既知答え11件を全部 期待どおりに判定する | `python3 scripts/priority_rebuild/gen_signal_families.py --verify` | 実経路 | 番人が使う構造を、表に沿った1本目に戻す | `b144_g2_sentinel_first_clean.sh` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=4eb6cbd3f7a2d4dd gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/gen_signal_families.py`

| 触る関数 | 定義の行 |
|---|---|
| `_g2_selftest_body` | 968 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 32件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=8475c934589548f7 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/gen_signal_families.py",
  "_impl_file の意味": "G2 の番人が在る、型の表の道具を照らす。",
  "impl_functions": {
    "scripts/priority_rebuild/gen_signal_families.py": [
      "_g2_selftest_body"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数（当てる前と後の構文木を関数ごとに比べて、r6b_build.py が数えた）。",
  "self_check_calls": [
    "_g2_selftest_body"
  ],
  "_self_check_calls の意味": "実装の後の gen_signal_families.py に在るはずの、この工事が触る関数の名前。",
  "must_use": {
    "_g2_selftest_body": [
      "_real_structures",
      "_judge_structure",
      "core_selftest"
    ]
  },
  "_must_use の意味": "番人が呼ぶ関数（r6b_build.py が当てた後の構文木で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は番人の構造の選び方だけを直す。外から読む一覧の形（型の表・検査済みの印）は変えない。",
  "generated_from": {
    "impl_functions": "当てる前と後の関数ごとの構文木の差（r6b_build.py が数えた）",
    "must_use": "ast で照らした",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/gen_signal_families.py",
 "public_functions": {
  "build_table": [],
  "core_of": [],
  "core_hash": [
   "core_of"
  ],
  "write": [
   "build_table",
   "core_hash"
  ],
  "verify": [
   "build_table",
   "core_hash",
   "g2_selftest"
  ],
  "approve": [
   "core_hash",
   "verify"
  ],
  "collect_materials": [],
  "insufficient_samples": [],
  "table_ranges": [],
  "check_structures": [],
  "g2_fingerprint": [],
  "g2_selftest": [],
  "core_selftest": [
   "core_hash"
  ],
  "v9_test": [],
  "v9_selftest": [
   "v9_test"
  ]
 },
 "constants": {},
 "cli_flags": [
  "--approve",
  "--check-structures",
  "--core-hash",
  "--core-selftest",
  "--g2-selftest",
  "--status",
  "--v9-selftest",
  "--v9-test",
  "--verify",
  "--write"
 ]
}
```

<!-- ACC_SPEC_END -->
