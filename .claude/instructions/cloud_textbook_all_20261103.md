# 依頼書｜指標データに要る項目を教科書で調べる・第1回（クラウドのセッション用）

## この作業の目的

engine_tuner は、指標の役割・パラメータ・閾値を、教科書を出どころにして使います。いまの教科書のデータには、欠けた指標と欠けた欄があります。

この作業は、後の工事（ToDo の169・212・213・70番）の材料を作ります。値は決めません。値を決めるのは、それぞれの工事の設計書と監査です。この作業は、「どのページに何と書いてあるか」だけを書きます。

第1回の相手は10種です。かかる時間と、結果の形が使えるかを、この10種で確かめます。

## 調べる相手

| 指標データの名前 | 調べる相手 |
|---|---|
| Stoch%K | Stochastic Oscillator の %K |
| Stoch%D | Stochastic Oscillator の %D |
| ROC | Rate of Change |
| volume_ratio | 出来高を、その平均で割った比 |
| CCI | Commodity Channel Index |
| MFI | Money Flow Index |
| CMF | Chaikin Money Flow |
| OBV傾き | On Balance Volume と、その傾き |
| AROONOSC | Aroon Oscillator |
| UO | Ultimate Oscillator |

## やること

10種のそれぞれについて、次の Q1〜Q7 に教科書で答えます。場面と売買スタイルは絞りません。

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

1. indicator_params_review.json に書いてある値と URL について、ページを開き、その値と逐語がページに在るかを確かめます。結果は「合う」「違う」「開けない」のどれかで書きます。
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
11. 乱数を使いません。プログラムを走らせる必要はありません。
12. 下の「出す物」のほかに、ファイルを作らず、直しません。
13. hook が止めたら、回り込まずに、止まった文を書いて作業を終えます。

## 出す物

- ファイルを1本だけ作ります。置き場は .claude/state/indicator_review/research/out_c1.json です。
- 中身は JSON の配列で、10種を1行ずつ入れます。形は下の見本のとおりにします。
- 欄の名前を変えません。「種類」には、上の表の指標データの名前を、そのまま書きます。
- 見つかった行は全部書きます。見本は、欄ごとの行数を絞ってあります。
- 別のブランチにコミットします。ブランチの名前は research/textbook-all-1 です。master へは入れません。

### 見本（RSI の1行）

RSI は第1回の相手ではありません。形を示すための物です。

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

次の6つを出してください。

1. 作ったファイルのパスと、ブランチの名前
2. 10種の Q1〜Q7 の答えの1行ずつ
3. いまの値と違う所
4. 分からなかったこと
5. 開けなかったページ
6. 作業にかかった時間
