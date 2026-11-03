# 依頼書｜指標データに要る項目を教科書で調べる・第6回（クラウドのセッション用・夜間の長い走行）

## この作業の目的

engine_tuner は、指標の役割・パラメータ・閾値を、教科書を出どころにして使います。いまの教科書のデータには、欠けた指標と欠けた欄があります。

この作業は、後の工事（ToDo の169・212・213・70番）の材料を作ります。値は決めません。値を決めるのは、それぞれの工事の設計書と監査です。この作業は、「どのページに何と書いてあるか」だけを書きます。

第6回の相手は154種です。第1回〜第5回の結果は、research/textbook-all-1〜5 ブランチの out_c1.json〜out_c5.json に在ります。

## 頼んだ人は寝ています

この作業を頼んだ人は寝ていて、質問に答えられません。確認の質問をせず、最後まで進めます。

- 見込みの時間は2時間〜3時間です。
- 20種ごとにファイルを作り、そのたびにコミットとプッシュをします。止まっても、そこまでの分が残ります。
- 始めるときに、`git ls-remote origin research/textbook-all-6` でブランチが在るかを確かめます。在れば、そのブランチの続きから始めます。ブランチの中に在る out_c6_*.json の番号を飛ばします。
- 会話の記録が要約に置き換わったときは、この依頼書の「守ること」と「出す物」を読み直します。作業の形が分からなくなったら、前に作ったファイルの1行と同じ形で書きます。
- 始めた時刻と終えた時刻を `date -u` で測ります。

## 調べる相手

154種は、指標データではオンの指標です。146種は資料の表に行があり、8種は行がありません。

**行のある146種：** .claude/state/indicator_params_review.json の、同じ「種類」の行の「元の指標」の欄が、調べる相手です。

**行の無い8種：**

| 指標データの名前 | 調べる相手 |
|---|---|
| CVD | Cumulative Volume Delta。テイカー買い − テイカー売りの累積 |
| L-S比 | Long/Short Ratio。ロング口座数 ÷ ショート口座数（Binance の先物のメトリクス） |
| taker_ls | Taker Buy/Sell Volume Ratio。テイカー買い量 ÷ テイカー売り量（Binance の先物のメトリクス） |
| W% | レンジの帯の幅。(レジスタンス帯の上端 − サポート帯の下端) ÷ 終値 × 100 |
| 帯内位置% | 帯の上半分の中の位置。(終値 − レンジの中央) ÷ (レジスタンス帯の上端 − レンジの中央) |
| 下半分位置 | 帯の下半分の中の位置。(終値 − レンジの中央) ÷ (レンジの中央 − サポート帯の下端) |
| 時刻 | バーの開始時刻の時（0〜23・UTC）。相場の時間帯の話として調べる |
| 曜日 | バーの曜日。相場の曜日の話として調べる |

**名前の読み方：**

- 「close vs ○○」は、指標データでは、終値と線 ○○ の距離です。元の線について Q1〜Q7 に答えます。
- 名前が「比」「%」「傾き」で終わる指標は、指標データでは、元の指標を割って単位をそろえた物や、変化を取った物です。元の指標について答えます。
- 割った形・距離にした形・傾きにした形を書いた文が無いときは、「見つからなかった」と書きます。
- 指標データの名前そのものを書いた文が無いときは、そのことを注の欄に書きます。

**ファイルごとの相手：**

| ファイル | 相手 |
|---|---|
| out_c6_01.json | ABER位置・ABER原作位置・ADX・AO%・AROOND・AROONU・ATR%・BB%b・BB幅・CHOP・CVD・DI差・Donchian幅・ER・HT_DCPHASE・HWC位置・HWC幅%・KST・KSTシグナル・Keltner上 |
| out_c6_02.json | Keltner下・L-S比・LeeMykland・LeeMykland_E36版・MACDシグナル線%・MACDヒスト%・MACD線%・MAD比・MASSI・MMI・POC・PPO・PPOシグナル・PPOヒスト・PSAR反転・PVT傾き・RCI・RSI・S-Rタッチ1時間ATR・S-Rタッチ数 |
| out_c6_03.json | S-Rタッチ確定1時間ATR・S-Rタッチ確定数・SQZ_ON・SQZ_ON_Carter・STC・STCstoch・StochRSI%D・StochRSI%K・StochRSI素%K・THERMO%・THERMO_EMA%・THERMO原作%・TR%・TRIX・TRIX_EMAシグナル・TRIX_EMAヒスト・TRIXシグナル・TRIXヒスト・TSI・TSIシグナル |
| out_c6_04.json | TSIヒスト・VAH・VAL・VHF・W%・WMA傾き%・close vs ABER_ZG%・close vs ACCBL%・close vs ACCBU%・close vs ALMA%・close vs CE_L%・close vs CE_S%・close vs CKSPl%・close vs CKSPs%・close vs DEMA%・close vs EMA・close vs FAMA%・close vs FAMA_HL%・close vs FWMA%・close vs HILO% |
| out_c6_05.json | close vs HMA%・close vs HT_TRENDLINE%・close vs HT_TRENDLINE_HL%・close vs HWMA%・close vs JMA%・close vs KAMA%・close vs LINREG%・close vs LRb%・close vs MAMA%・close vs MAMA_HL%・close vs MCGD%・close vs MEDIAN%・close vs MIDPOINT%・close vs MIDPRICE%・close vs MMAR%・close vs PMAX%・close vs PSAR%・close vs PWMA%・close vs RAINBOW%・close vs RMA% |
| out_c6_06.json | close vs SAREXT%・close vs SINWMA%・close vs SMA・close vs SSF%・close vs SSF平均%・close vs SWMA%・close vs T3%・close vs TEMA%・close vs TRIMA%・close vs TRIMA_TA%・close vs TSF%・close vs VIDYA%・close vs VIDYA_CMO%・close vs VWAP・close vs VWAP典型・close vs VWMA%・close vs WMA%・close vs ZLMA%・fib位置・fractal安値距離% |
| out_c6_07.json | fractal高値距離%・n本安値・n本高値・pivotPP・pivotR1・pivotS1・realized_vol・realized_vol_rv・swing安値距離・swing高値距離・taker_ls・下半分位置・前日POC・前日VAH・前日VAL・前期間pivotPP・前期間pivotR1・前期間pivotS1・前週pivotPP・前週pivotR1 |
| out_c6_08.json | 前週pivotS1・基準線・安値からの経過バー・安値切り上げ幅%・帯内位置%・当日POC・当日VAH・当日VAL・当日VWAP・時刻・曜日・構造破断距離%・高値からの経過バー・高値切り上げ幅% |

## やること

154種のそれぞれについて、次の Q1〜Q7 に教科書で答えます。場面と売買スタイルは絞りません。

| 番号 | 問い | 書く欄 |
|---|---|---|
| Q1 | その指標は、相場の何を見ているか。向き・強さ・勢い・行き過ぎ・値動きの幅・出来高・位置のどれに当たるか | 教科書の役割 |
| Q2 | 値が大きいと何を意味するか。向きを持つか。値の単位と、値の取り得る幅は何か。出力は何本か（%K と %D など） | 値の読み方・値の単位と値域・出力 |
| Q3 | 計算の式は何か。値が確定するまでに何本要るか | 計算の式・確定と期間 |
| Q4 | パラメータごとに、意味・既定の値・スキャル向けの値・デイトレ向けの値・範囲は何か。組で書いてある値は、組のまま書く | パラメータの軸 |
| Q5 | 閾値の形（値・分位・回数・倍率・前提つき）ごとに、値と範囲は何か。閾値を持たない指標は「持たない」と書く | 閾値 |
| Q6 | どう使うと書いてあるか。下の「選ぶ語」で書く | 使い方 |
| Q7 | 合図の形の数は何か（続く本数・クロスの相手・タッチの許容幅・何本以内か） | 合図の形のパラメータ |

### 選ぶ語

欄の値は、次の語から選びます。どれにも当たらないときは「書いてない」と書き、注の欄にページの言葉を書きます。

- 教科書の役割：向き・強さ・勢い・行き過ぎ・値動きの幅・出来高・位置
- 値の単位：値段・%・0〜100・分位・ドル・手数料の床の倍数・ATR の倍数
- 軸の意味：窓・倍率・割合・重み・本数・ずらす本数
- 閾値の形：値・分位・回数・倍率・前提つき
- 使い方の種類：場面の判定・入る合図・入ってはいけない場面を除く条件・合図が本物かを確かめる条件・出口の水準を作る材料・出口の反転・前提崩れの印
- 場面：レンジ・上げ・下げ・スパイク
- 玉の向き：SHORT・LONG・両方
- 向き：上側・下側・上へ抜ける・下へ抜ける
- 確かめの強さ：ページの文で確かめた・見つからなかった

## いまのデータと照らす

このリポジトリの次のファイルに、いまのデータが在ります。読むだけで、直しません。

- .claude/state/indicator_params_review.json
- .claude/state/indicator_params_by_strategy.json
- .claude/state/indicator_roles_thresholds.json
- v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json（「指標の記録」の下に、指標の名前ごとの行が在ります）

次の2つを確かめます。

1. indicator_params_review.json に行があるときは、書いてある値と URL についてページを開き、その値と逐語がページに在るかを確かめます。結果は「合う」「違う」「開けない」のどれかで書きます。行が無いときは、「資料の表の確認」を空の配列にします。今回は146種に行が在り、8種に行がありません。同じ URL は、開いた本文を使い回してかまいません。
2. 調べた値が indicators.json の値や定義の文と違うときは、違いを書きます。どちらが正しいかは決めません。

## 守ること

1. ページの本文を開いて、1つの値ごとに逐語と URL を残します。検索結果の要約だけで書きません。
2. 確かめの強さは、「ページの文で確かめた」「見つからなかった」のどちらかです。語の数を数えただけのものを、確かめたと書きません。
3. 書いてないことは「書いてない」と書きます。推測で埋めません。
4. その値がどの時間足の話かを書きます。書いてなければ「書いてない」と書きます。
5. 代表の値と範囲を提案しません。いくつかのページの値を並べて、範囲を作りません。
6. 2つ以上の出どころの値が違うときは、片方に決めず、両方を書きます。
7. 1つのサイトにしか無い値には、注の欄に「1サイトだけ」と書きます。
8. BTC や暗号資産について書いた資料は、注の欄に「暗号資産」と書きます。
9. 「選ぶ語」に分けたのが調べた人の読みであるときは、注の欄に「調べた人の読み」と書きます。
10. 開発者の原典と定番の教育サイトを先に使います。出どころの質を1件ごとに書きます。
11. 乱数を使いません。
12. リポジトリの中では、下の「出す物」のほかに、ファイルを作らず、直しません。ページの写しと短いスクリプトは、リポジトリの外の一時フォルダに置いてかまいません。
13. ページが開けないときは、結果を「開けない」と書き、HTTP の番号を注の欄に書いて、次へ進みます。ChartSchool が開けないときも同じです。ChartSchool の分は、後で手元で確かめます。
14. hook が止めたら、回り込まずに、止まった文を書いて作業を終えます。
15. 1つのページや1種に、時間を使いすぎません。開けないページや見つからない値は、記録して次へ進みます。
16. 使用量の上限や時間切れで続けられないときも、作り終えたファイルをコミットとプッシュしてあれば、そのまま終えてかまいません。

## 出す物

- 上の「ファイルごとの相手」の8本を、順に作ります。置き場は .claude/state/indicator_review/research/ です。
- 中身は JSON の配列で、そのファイルの相手を1行ずつ入れます。形は下の見本のとおりにします。
- 欄の名前を変えません。「種類」には、指標データの名前を、そのまま書きます。
- 見つかった行は全部書きます。見本は、欄ごとの行数を絞ってあります。
- 別のブランチにコミットします。ブランチの名前は research/textbook-all-6 です。master へは入れません。
- 1本を作り終えるたびに、次の順に行います。
  1. `jq length` で、JSON が読めることと、行の数が相手の数と同じことを確かめます。
  2. そのファイルをコミットします。
  3. リモートへプッシュします。プッシュが失敗したら、1回だけやり直し、それでも失敗したら次のファイルへ進みます。最後にもう一度プッシュします。

### 見本（RSI の1行）

RSI は第6回の相手です。見本は形を示すための物です。値を写さず、ほかの指標と同じようにページを開いて調べます。

```json
[
  {
    "種類": "RSI",
    "元の指標": "Relative Strength Index（J. Welles Wilder）",
    "教科書の役割": [
      {
        "区分": "勢い",
        "逐語": "The RSI, a momentum oscillator developed by J. Welles Wilder, measures the speed and change of price movements.",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
        "出どころの質": "定番の教育サイト",
        "読んだ日": "2026-11-03",
        "時間足": "書いてない",
        "確かめの強さ": "ページの文で確かめた",
        "注": ""
      }
    ],
    "値の読み方": [
      {
        "読み方": "上が買われ過ぎ、下が売られ過ぎ",
        "向きを持つ": "書いてない",
        "逐語": "When the RSI is above 70, it generally indicates overbought conditions; when the RSI is below 30, it indicates oversold conditions.",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
        "出どころの質": "定番の教育サイト",
        "読んだ日": "2026-11-03",
        "時間足": "書いてない",
        "確かめの強さ": "ページの文で確かめた",
        "注": ""
      }
    ],
    "値の単位と値域": [
      {
        "単位": "0〜100",
        "下限": 0,
        "上限": 100,
        "逐語": "The RSI moves up and down (oscillates) between zero and 100.",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
        "出どころの質": "定番の教育サイト",
        "読んだ日": "2026-11-03",
        "時間足": "書いてない",
        "確かめの強さ": "ページの文で確かめた",
        "注": ""
      }
    ],
    "出力": [
      {
        "名前": "RSI",
        "組の相手": null,
        "確かめの強さ": "見つからなかった",
        "注": "RSI を複数の線として書いた文は無かった"
      }
    ],
    "計算の式": {
      "逐語": [
        "RS = Average Gain / Average Loss",
        "First Average Gain = Sum of Gains over the past 14 periods / 14.",
        "Average Gain = [(previous Average Gain) x 13 + current Gain] / 14."
      ],
      "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
      "出どころの質": "定番の教育サイト",
      "読んだ日": "2026-11-03",
      "時間足": "書いてない",
      "確かめの強さ": "ページの文で確かめた",
      "指標データの定義の文との違い": "文の上では違わない。コードの計算は見ていない"
    },
    "確定と期間": [
      {
        "確定に要る本数": 250,
        "逐語": "A formula will need at least 250 data points to replicate our RSI numbers.",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
        "出どころの質": "定番の教育サイト",
        "読んだ日": "2026-11-03",
        "時間足": "書いてない",
        "確かめの強さ": "ページの文で確かめた",
        "注": ""
      }
    ],
    "パラメータの軸": [
      {
        "名前": "n",
        "意味": "窓",
        "既定": [
          {
            "値": 14,
            "逐語": "This RSI calculation is based on 14 periods, the default Wilder suggested in his book.",
            "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
            "出どころの質": "定番の教育サイト",
            "読んだ日": "2026-11-03",
            "時間足": "書いてない",
            "確かめの強さ": "ページの文で確かめた",
            "注": ""
          }
        ],
        "スキャル": [
          {
            "値": 7,
            "逐語": "For 5-minute scalping, the 7-period RSI is usually the best choice.",
            "URL": "https://www.mc2.fi/blog/best-rsi-for-scalping",
            "出どころの質": "ブログ",
            "読んだ日": "2026-11-03",
            "時間足": "5分足",
            "確かめの強さ": "ページの文で確かめた",
            "注": ""
          }
        ],
        "デイトレ": [
          {
            "値": [7, 9],
            "逐語": "Day traders commonly shorten the period to 7 to 9 on intraday charts",
            "URL": "https://bullynx.com/blog/best-rsi-settings",
            "出どころの質": "証券会社・ブログ",
            "読んだ日": "2026-11-03",
            "時間足": "日中の足",
            "確かめの強さ": "ページの文で確かめた",
            "注": ""
          }
        ],
        "範囲": [
          {
            "確かめの強さ": "見つからなかった",
            "注": "範囲を1つの文で書いたページは無かった"
          }
        ]
      }
    ],
    "閾値": [
      {
        "形": "値",
        "値": [70, 30],
        "意味": "上が買われ過ぎ、下が売られ過ぎ",
        "範囲": [
          {
            "確かめの強さ": "見つからなかった",
            "注": ""
          }
        ],
        "逐語": "Wilder considered RSI overbought above 70 and oversold below 30.",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
        "出どころの質": "定番の教育サイト",
        "読んだ日": "2026-11-03",
        "時間足": "書いてない",
        "確かめの強さ": "ページの文で確かめた",
        "注": ""
      }
    ],
    "使い方": [
      {
        "使い方の種類": "入る合図",
        "場面": "レンジ",
        "玉の向き": "書いてない",
        "向き": "書いてない",
        "逐語": "overbought and oversold readings for RSI work best when prices move sideways within a range",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
        "出どころの質": "定番の教育サイト",
        "読んだ日": "2026-11-03",
        "時間足": "書いてない",
        "確かめの強さ": "ページの文で確かめた",
        "注": "調べた人の読み"
      }
    ],
    "合図の形のパラメータ": [
      {
        "形": "上へ抜ける",
        "値": 70,
        "逐語": "Second, RSI must cross above 70 to become overbought.",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi",
        "出どころの質": "定番の教育サイト",
        "読んだ日": "2026-11-03",
        "時間足": "日足",
        "確かめの強さ": "ページの文で確かめた",
        "注": ""
      }
    ],
    "今の値との違い": [
      {
        "欄": "デイトレの代表の値",
        "指標データ": 14,
        "教科書": "日中の足で 7〜9",
        "注": "どちらが正しいかは決めない"
      }
    ],
    "資料の表の確認": [
      {
        "欄": "既定",
        "値": 14,
        "結果": "合う",
        "URL": "https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/relative-strength-index-rsi"
      }
    ],
    "分からなかったこと": [
      "開発者 Wilder の本は本文を読めなかった"
    ]
  }
]
```

## 終わりの報告

次の7つを出してください。答えの1行ずつの表は要りません。ファイルはプログラムで読みます。

1. 作ったファイルのパスと、ブランチの名前と、最後のコミット
2. 作り終えた本数と種類の数。作れなかった相手の名前
3. いまの値と違う所のうち、主なもの
4. 分からなかったこと
5. 開けなかったページ
6. 作業にかかった時間（始めた時刻と終えた時刻）
7. 途中で止まったときは、その理由と、続きを始める番号
