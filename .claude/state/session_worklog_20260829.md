# 作業記録 2026-08-29（71回目・M2-A-1＝外を調べる）

> 70回目の記録は `session_worklog_20260828.md`（§3〜§14）。このセッションは M2-A-1 から始めた。

## §1 やったこと（1行）

**M2-A-1＝「実際にレンジだったか」の正解の作り方を、外ではどう作っているかを調べた。**

**正本**＝`.claude/ratchet/engine_tuner_milestones2.md` §3 の M2-A-1。
**正本の確かめ方（逐語）**＝「調べた結果の表。**確かめ方＝全行に「決まり／URL／逐語／一次ページを開けたか」の4つが入っている。開けなかったものは「開けなかった」と書く**」。
**触ったファイル**＝`session_todo.md` と、この記録の2本だけ。**`scripts/priority_rebuild/` は1バイトも触っていない。**

---

## §2 調べる問いを4つに決めた

**なぜこの4つか**＝M2-A-3 で まこさんが決める2つ（①正解の印の中身 ②先を見る本数）に、そのまま材料を渡すため。

| 問い | 何を知りたいか | M2-A-3 のどちらに効くか |
|---|---|---|
| ① | レンジ（横ばい）を、定量にどう定義しているか | ①正解の印の中身 |
| ② | 「実際にレンジだった」という正解ラベルを、後ろ向きにどう作っているか | ①正解の印の中身 |
| ③ | 判定の当たり外れを、どう測っているか（正解が目に見えないものをどう採点するか） | ①正解の印の中身 |
| ④ | 先を見る本数（ホライズン）を、どう決めているか | ②先を見る本数 |

**検索の回数**＝5回（WebSearch）。**開こうとした一次ページ**＝8件。**開けた**＝6件。**開けなかった**＝2件。

---

## §3 調べた結果の表（8件）

**★逐語は英語の原文のまま載せる。**訳すと、訳した私の解釈が混ざるため。日本語は私の説明で、逐語ではない。

### A-1｜レンジは「トレンドの否定」として定義されている（2件・一致）

| # | 決まり（何をしているか） | URL | 逐語（原文） | 一次ページを開けたか |
|---|---|---|---|---|
| 1 | **連続トレンド＝隣り合う山と谷の変動幅が閾値 ω を超えたとき。超えなければ「通常の変動」＝トレンドなし。**＝レンジを直接 定義せず、トレンドの否定として置く | https://pmc.ncbi.nlm.nih.gov/articles/PMC7597331/ | "the continuous trend was defined as the fluctuation amplitude between the two adjacent peak and trough points exceeding the given threshold parameter ω, otherwise the fluctuation was considered a normal fluctuation without a continuous trend." | **開けた**（Section 2.3） |
| 2 | **横ばい＝上げでも下げでもない、残り全部**（VIX の分位と3ヶ月のトレンドの向きで上げ下げを決め、それ以外を横ばいにする） | https://arxiv.org/html/2506.06356v1 | "Market regimes are defined based on volatility levels and trend directions: Bull Market (Low Vol): VIX < 20th percentile, positive 3-month trend; ... Sideways Market: All other periods" | **開けた**（Section V-C） |

### A-2｜正解ラベルの作り方（3件）

| # | 決まり（何をしているか） | URL | 逐語（原文） | 一次ページを開けたか |
|---|---|---|---|---|
| 3 | **閾値は絶対の数字で置く**（中央値で半分に切らない）。ω=0.15＝15% 動いたらトレンド。試した範囲は 0.05〜0.25。窓の長さ λ=11 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7597331/ | "a suboptimal parameter value ω = 0.15 was chosen instead and the average value ranged from 0.05 to 0.25. Therefore, if the price rose or fell by more than 15%, it would be regarded as an upward or downward trend" ／ "The sliding window parameter λ was set to 11 in this paper" | **開けた**（Section 4.1・2.2.1） |
| 4 | **短い先を見て今と比べるやり方は、短期のでたらめさを拾う**＝この論文が「連続トレンド」を作った理由 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7597331/ | "financial time series data are typically non-linear with obvious short-term randomness. Therefore, these labeling methods have not captured the continuous trend features of financial time series data" | **開けた**（Section 1） |
| 5 | **3つに分けるとき、真ん中に「どちらでもない」の帯を置く**（0.4〜0.6 が Neutral）。**★先の本数 n の選び方は書いていない** | https://ar5iv.labs.arxiv.org/html/1907.03010 | "Class 0: %Q>=0.6 means Up; Class 1: 0.4<%Q<0.6 means Neutral; Class 2: %Q<=0.4 means Down" ／ "N bars Up/Down: Classifier on Ct+n>Ct" | **開けた**（Section 6） |

### A-3｜正解が目に見えないものを、どう採点しているか（2件）

| # | 決まり（何をしているか） | URL | 逐語（原文） | 一次ページを開けたか |
|---|---|---|---|---|
| 6 | **場面は目に見えないものなので、①期間を分けて確かめる ②正解が既知の合成データを作って混同行列で測る。**合成の作り方＝AR(1) 係数0.9・正規化して 0〜1・0.7 超を高ボラ・高ボラ期は誤差項を3倍。**★誤りのコストは左右で違う** | https://ar5iv.labs.arxiv.org/html/2104.03667 | "Since market regimes are latent unobservable processes, the detected regimes should be validated in an out-of-sample framework." ／ "classifying a highly volatile regime as a calm one is a more costly misclassification compared to classifying a calm regime as a highly volatile one." | **開けた**（Section 4） |
| 7 | **正解ラベルの付いたデータで先に確かめてから、ラベルの無い実データへ移る** | https://ar5iv.labs.arxiv.org/html/2306.15835 | "In Section 5, we evaluate our clustering methodology on *labelled data* so as to verify our class assignments before moving onto *unlabelled data*." ／ 窓の選び方＝"The choice of h = (h₁, h₂) is largely dependent on the characteristics of the data one is working with." | **開けた**（Section 1.4・Remark 3.4） |

### A-4｜先を見る本数（ホライズン）の決め方（3件・食い違っている）

| # | 決まり（何をしているか） | URL | 逐語（原文） | 一次ページを開けたか |
|---|---|---|---|---|
| 8 | **★推論したい先の本数と、教える先の本数は、一致させるのが最適とは限らない。**中間の本数がいちばん効く場合がある。推奨＝本数を学習で決めさせる | https://arxiv.org/html/2602.03395v1 | "Minimizing training error on the canonical target horizon t+Δ does not guarantee optimal generalization on t+Δ. Contrary to intuition, the most effective supervision signal is often misaligned with the inference target, residing at an intermediate horizon t+δ (where δ≠Δ)." | **開けた**（Introduction・Section 3.4・4） |
| 9 | **本数と閾値を、ラベルの割合が釣り合うように探索して選ぶ**（5〜29日 × 7〜15%）。**★保有期間と結びつける記述は無い**（開いて確かめた） | https://arxiv.org/html/2504.02249v2 | "To ensure balanced label proportions during training, we optimized the labeling parameters by testing various combinations of time horizons (5–29 days with a step size of 1 day)" ／ "percentage thresholds (7%–15% with a step size of 1%)" | **開けた**（Section III-B） |
| 10 | **本数は「短い揺れを構造の変化と見なさない」長さに合わせる**（この論文は月次を選んだ） | https://ar5iv.labs.arxiv.org/html/2104.03667 | "We choose to detect regime switches at monthly frequency to allow the underlying mean-reverting data generating processes to have deviations that are not regarded as structural breaks." | **開けた**（Section 3） |

### A-5｜開けなかったもの（2件・正本の指示どおり「開けなかった」と書く）

| # | 何を見に行ったか | URL | 結果 |
|---|---|---|---|
| 11 | Poterba & Summers「Mean Reversion in Stock Prices」＝分散比の定義と、ホライズンの選び方 | https://papers.ssrn.com/sol3/delivery.cfm/nber_w2343.pdf?abstractid=227278 | **開けなかった**（HTTP 403） |
| 12 | 同じ arXiv 論文2本の PDF 版（`2104.03667` と `1907.03010`） | https://arxiv.org/pdf/2104.03667 ／ https://arxiv.org/pdf/1907.03010 | **開けなかった**（PDF を文字に直す道具が この環境に無い＝`pdftoppm is not installed`）。**★HTML 版（ar5iv）で開き直して逐語を取った**＝上の 6・5・10 |

---

## §4 ★検索の要約が、本文と違っていた1件（恒久の決まり43番の実例）

**検索の要約に出た文**＝「dynamic volatility threshold」「square root of time rule」「sideways conditions are identified when the absolute value of cumulative returns over k days does not exceed the threshold」。
**＝レンジを直接 定義する式が在るように読めた。**

**本文を開いた結果**＝**その式は書いていなかった。**本文の定義は「Sideways Market: All other periods」＝残りもの（上の表の2番）。

**＝検索の要約だけで表を書いていたら、実在しない定義を1件 載せていた。**
**恒久の決まり43番**＝「検索結果の要約で設計を書かない。記事本文を開いて逐語を取る」。**この1件が、その決まりが要る理由の実例。**

---

## §5 いまの正解の印（実物）と、外の作り方の違い（3つ）

### （1）いまの印の実物（逐語）

**実物＝`scripts/priority_rebuild/observe_diag.py` の `_regime_labels`（5436-5453行）。**

```
def _regime_labels(win: pd.DataFrame, n: int) -> dict:
    """そのバーから先 n本の値動きの性質を、3つの見方で真偽に直す（＝正解の印）。

    ①強さ   … 先 n本の ER（まっすぐ進んだ距離 ÷ 実際に歩いた距離）が、この窓の中央値以上か
    ②向き   … 先 n本の終値が、いまの終値より上か
    ③大きさ … 先 n本で動いた幅 ÷ 直前 n本で動いた幅 が、この窓の中央値以上か
    """
    ...
    return {"強さ": (er >= er.median(), er.notna()),
            "向き": (fwd > 0, fwd.notna()),
            "大きさ": (size >= size.median(), size.notna())}
```

**★「レンジだった」という印は、この3つの中に1つも無い。**在るのは「強さ」＝ER が窓の中央値以上なら**まっすぐ進んだ**。**レンジは、その否定として取り出す。**

### （2）外と同じところ（1つ）

**レンジをトレンドの否定として置くのは、外でも同じだった**（表の1番＝「超えなければ通常の変動」／2番＝「残り全部」）。
**＝「レンジを直接 定義していないのはおかしい」とは言えない。**私が調べる前に持っていた疑いは、外の実例で否定された。

### （3）外と違うところ（3つ・★ここが M2-A-3 の材料）

| # | いまの印 | 外 | 何が変わるか |
|---|---|---|---|
| **1** | **窓の中央値で切る**（`er >= er.median()`） | **絶対の数字で切る**（表の3番＝ω=0.15＝15%） | 中央値だと、**どの期間でも必ず半分がトレンド・半分がレンジになる。**「トレンドばかりの月」「レンジばかりの月」を区別できない。絶対値なら区別できるが、**でたらめな判定の基準線が 50% に決まらなくなる**（いまの長所が消える） |
| **2** | **真ん中の「どちらでもない」帯が無い**（中央値のすぐ上と、すぐ下が、別の札になる） | **真ん中に帯を置く**（表の5番＝0.4〜0.6 は Neutral） | 帯を置くと、**境目のすれすれの所を採点から外せる。**いまは境目のすれすれも「外した」と数える |
| **3** | **正解の印そのものが正しいかを確かめる仕組みが無い**（実測＝`observe_diag.py` に合成データの検査は無い） | **正解が既知の合成データを作って、混同行列で確かめてから実データへ移る**（表の6番・7番） | 合成データを1本 作れば、**「印が壊れていないか」を機械で確かめられる。**いまは印が壊れても誰も気づかない |

---

## §6 先を見る本数（M2-A-3 の2つ目）についての材料

**いまの実物**＝`recipes/search_limits.json`:42 の `state_hold_bars_range` が `{"lo": 24, "hi": 288}`（24本＝2時間・288本＝24時間）。
**E38 スキャルの玉の上限**＝同 20-23行 の `hold_range_by_role.scalp` が `{"lo_bars": 1, "hi_bars": 12}`（1〜12本＝5〜60分）。
**＝正解の印が見ている先（最短 2時間）が、玉を持つ時間（最長 60分）より長い。**

**外の3件は、答えが割れている。**

| 出どころ | 言っていること |
|---|---|
| **表の8番**（Label Horizon Paradox） | **一致させるのが最適とは限らない。**中間の本数がいちばん効く場合がある。＝「玉の時間に合わせる」は自明ではない |
| **表の9番**（Triple Barrier の実例） | **本数も閾値も探索して選んだ。**保有期間と結びつける記述は無い |
| **表の10番**（Realized Covariances） | **短い揺れを構造の変化と見なさない長さに合わせる**＝長めに取る理由 |

**＝「玉の時間に合わせて下限を下げる」（私が正本 §5 の2番に書いていた案）を支える一次の逐語は、今回1件も出なかった。**
**★私の案は、外の根拠ではなく「玉より長い先を見ている」という うちの実測から出たものです。**そう書き分けます。

---

## §7 M2-A のやることリストを直した（4か所・まこさんの問いで気づいた）

**まこさんの問い（逐語）**＝「やることリストは修正しなくても良いの？」。
**私の答え＝直す必要がありました。M2-A-1 を終えたのに、リストに1つも反映していませんでした。**

### （1）直した4か所（正本＝`engine_tuner_milestones2.md`）

| # | どこ | 直す前 | 直した後 |
|---|---|---|---|
| 1 | §3 M2-A-1 の状態 | `まだ` | **`✅済（2026-08-29）`** ＋ 確かめ方の欄に「実測＝開けた6件／開けなかった2件」を足した（恒久の決まり55番） |
| 2 | §3 M2-A-2 の確かめ方 | 件数と割合の表＋新しい節の行番号 | **＋「H2 の印を取り直した」を足した。**理由＝`observe_diag.py` は `h2_pass.json` の**対象21件に入っている**（2026-08-29 に import して実測）＝1文字でも変えると印が失効する |
| 3 | §3 M2-A-4 のやること | 実装＋わざと壊して止まるか試すテスト | **＋「答えが分かっているニセのデータ（合成データ）で、印そのものが壊れていないかを確かめる検査を足す」。★印を変えても変えなくても足す**＝いまは印が壊れても誰も気づかない |
| 4 | §5 の2番（先を見る本数）の「私の案」 | 玉の時間に合わせて下限を下げる | **＋「この案の根拠は、外の一次の逐語ではなく、うちの実測です」を足した。**外の3件は答えが割れている（§6）＝**都合の悪い事実を落とさない**（恒久の決まり34番） |

### （2）★2番と3番は、M2-A-1 をやる前には見えていなかったもの

- **2番**＝H2 の印の対象を実際に数えるまで、`observe_diag.py` が対象に入っていることを私は確かめていなかった。
- **3番**＝合成データで印を確かめるやり方は、**M2-A-1 で外の論文を開いて初めて分かった**（§3 の表の6番・7番）。

### （3）機械が作る文書を作り直した（元を直したら gen を走らせる＝恒久の決まり12番）

**★走らせる前に、過去の実測を記録から探した**（恒久の決まり62番）＝worklog の逐語「`gen_materials.py --write`（**4.8秒**）」。**見込み＝15分未満。**

| # | 走らせたもの | 結果 | 実測 |
|---|---|---|---|
| 1 | `gen_materials.py --verify` | **❌ 2件**（`engine_tuner_milestones.md` と `engine_tuner_milestones2.md` の差し込みが実物と食い違う）＝検査が効いている | 4.83秒 |
| 2 | `gen_materials.py --write` | 2本とも差し込み。**材料そのものは変わらず**（在る 261／足す 0／指紋 `59957e3edb80af39`） | 4.69秒 |
| 3 | `gen_materials.py --verify` | **✅ 一致** | — |
| 4 | `gen_docmap.py --verify` | **❌ 2件** | 5.63秒 |
| 5 | `gen_docmap.py --write` | 指紋 `f352aa7189d3052a` → `efac4556c745bc81` | 5.20秒 |
| 6 | `gen_docmap.py --verify` | **✅ 一致** | — |

**★4番が ❌ になった原因＝私が今日 新設した `session_worklog_20260829.md` です。**「人が手で書く文書」の数が **404本 → 405本** に増えたためでした（`git diff` で確かめた）。**道具の不具合ではありません。**

### （4）★見つけた食い違い1件（`next_step.md` §6 に足す候補）

**ToDo ゲート（`enforce_todo_declaration`）が、バッククォートのせいで3回 止まりました。**
**原因**＝ToDo のファイルにはバッククォートが入っているが、**チャットではバッククォートを使わない決まり**（memory `feedback_no_markdown_links`＝まこさん 2026-06-18「禁止は文字の背景がグレーになるやつ」）。hook は行の完全一致を見るので、外して貼ると「貼っていない」と判定される。
**その場の直し方**＝ToDo のファイル側からバッククォートを外した（これで一致した）。
**★根っこは残っている**＝次の CC も同じ所で止まる。**直すかどうかは まこさんが決めます。**

---

## §8 このセッションで書き換えたファイル

| ファイル | 何をしたか |
|---|---|
| `.claude/state/session_worklog_20260829.md` | **新設**（この記録） |
| `.claude/state/next_step.md` | 0-1 を今日の状態に書き替えた（`tidy_next_step.py --verify` が ✅ 6つ） |
| `.claude/state/next_step_archive_202608.md` | 古い 0-1（19行）をプログラムが移した（印の数 前 37 → 後 34・移した分3・**消えた印は0**） |
| `.claude/ratchet/engine_tuner_milestones2.md` | **M2-A のやることリストを4か所 直した**（§7）＋ 機械の差し込み |
| `.claude/ratchet/engine_tuner_milestones.md` | 機械の差し込みだけ（`gen_materials.py --write`） |
| `.claude/ratchet/docmap.md`・`docmap.json` | 機械が作り直した（`gen_docmap.py --write`） |
| `.claude/state/session_todo.md` | ToDo を2回 書いた（M2-A-1 の5件 → やることリストの直しの5件） |

**★`scripts/priority_rebuild/` のコードは1バイトも触っていない。net はゼロ**（実験ゼロ・採点ゼロ・売買記録0本）。

---

## §9 M2-A-2 の数え方を決めた

### （1）何を測るか

**「レンジ」という言葉の意味と、実際の値動きの食い違いを数える。**
**★これは「正解」ではない。**レンジの本当の答えは誰も持っていない（`session_worklog_20260829.md` §3 の表の6番の逐語 "Since market regimes are latent unobservable processes"）。**分かるのは食い違いの量だけ。**

### （2）新しい物差し＝片道の度合い

| | 中身 |
|---|---|
| **分子** | 区間の**始まりと終わりの価格差**（絶対値）＝`abs(close[i+n] - close[i])` |
| **分母** | その区間の**値幅**＝`max(high[i+1..i+n]) - min(low[i+1..i+n])` |
| **比** | 0 〜 1。**0 に近いほどレンジらしい**（行って戻った）／**1 に近いほどレンジではない**（片道） |

### （3）いまの印との違いは「分母」だけ

| | 分母 | 何が起きるか |
|---|---|---|
| **いまの印（ER）** | **歩いた距離の合計**（`c.diff().abs().rolling(n).sum()`＝`observe_diag.py`:5447） | **細かく揺れるほど分母が増えて、値が下がる。**＝ただ荒れているだけの区間も「レンジ」に入る |
| **新しい物差し** | **区間の値幅**（高値 − 安値） | **幅に対して片道でどれだけ動いたか**だけを見る。レンジという言葉の意味に近い |

### （4）出す数字（4つ）

| # | 出すもの | なぜ要るか |
|---|---|---|
| 1 | **レンジの札とトレンドの札、それぞれの比の分布**（10%刻み） | 全体の形が見える |
| 2 | レンジの札のうち、比が **0.5以上・0.7以上・0.9以上** の件数と割合 | 「言葉の意味と食い違う区間」の量 |
| 3 | **2つの札の比の中央値の差** | **分かれていなければ、いまの印はレンジらしさを捉えていない証拠になる** |
| 4 | 上の3つを、**先の本数ごと**（24本・288本＝`_regime_horizons()` が `search_limits.json` から読む） | まこさんが M2-A-3 で本数を決める材料 |

**★1番と3番が要る理由**＝レンジの札だけ見ても、多いのか少ないのか判断できない。**トレンドの札と並べて初めて、印が2つを分けられているかが分かる。**
**★0.5・0.7・0.9 は表示用の線。**分布は全部 出すので、線は目安（**探す値を点で限定するものではない**＝恒久の決まり42番）。

### （5）守るもの4つ

| # | 中身 | 使う実物 |
|---|---|---|
| 1 | **窓＝値決め窓（2024-03-01 〜 2025-09-01）だけ。**採点窓は1バーも使わない | `periods.py`:94-95 ／ 既存の `_assert_search_window_only` |
| 2 | **重なった区間を何度も数えない**（5分足で288本なら隣とは287本 重なる） | 既存の `_independent_step(tf, n)` |
| 3 | **H6（価格非依存）**＝分子も分母も価格の差なので、比は無次元 | — |
| 4 | **H2（未来参照）**＝この計算は未来を見る。いまの印と同じ「札を作る側」で、売買の判断には入らない。行に `# H2OK:` の理由を書く | `observe_diag.py`:5446-5447 と同じ形 |

### （6）実物で確かめた3つ（決める前に開いた）

| # | 確かめたこと | 結果 |
|---|---|---|
| 1 | 値決め窓 | `periods.py`:94-95＝`SEARCH_START = 2024-03-01` ／ `SEARCH_END = 2025-09-01`（排他） |
| 2 | 節の作り | `INSPECT_SECTIONS`（`observe_diag.py`:3400）に見出し、`stages`（4649-4661）に関数。**いま検査1〜14。新しいのは「検査15」として足す** |
| 3 | **承認が要るか** | **要る。**`require_acceptance_before_impl.sh`:55 が `ratchet_io`・`to_csv` 等を含むファイルを免除しない。**`observe_diag.py` には `ratchet_io` 7件・`to_csv` 1件・`write_sidecar` 1件・`score.score` 1件**（実測） |

### （7）★この節を書く順番を間違えた（記録に残す）

**ToDo の2番を ✅済 にしてから、この §9 を書こうとして、ToDo ゲートに止められた**（「2番が指す §9 が worklog の見出しに無い」）。
**＝記録を書く前に「済」にした。**hook が正しく止めた。**§7（4）のバッククォートの件と合わせて、今日 ToDo ゲートに止められたのは4回。**

---

## §10 目的ゲートの「変えない」の判定を直す（まこさん決定 B・直し方を決めた）

### （1）なぜ直すか

**M2-A-2 の設計書を書こうとして、目的ゲートに2回 止められた。**
条件4つ（指標・閾値・時間足・パラメータ）に書ける印は3つ（`✅` ／ `❌` ／ `変えない`）。**中身に合うのは「変えない」だが、hook が書かせない。**
**まこさんの決定（逐語）＝「B」**＝hook の作りを直す（A＝❌ を書いて例外で通す、は取らない）。

### （2）いまの作り（実物・`.claude/hooks/enforce_purpose_gate.py`）

| 行 | 中身 |
|---|---|
| 75 | `MARK_KAENAI = "変えない"` |
| 147-160 | `search_path_files()`＝**探索の経路のファイルの名前を、H2 の印（`h2_pass.json`）から読む**（★手書きの一覧を作らない＝教訓 L-468） |
| 176-185 | `touches_search_path(kind, name, content)`＝触るなら `True`。`kind` は code（.py を書く）／run（走らせる）／design（設計書を書く）の3つ |
| 266-272 | **条件の行に「変えない」が在り、かつ `touches_search_path` が `True` なら止める** |

### （3）何が表せないか

**「そのファイルの中の、探索に関わらない所へ、読むだけの処理を足す」が表せない。**
判定が**ファイルの名前だけ**で、**中身の変え方**を1つも見ていないため。

### （4）直し方（判定を1か所 足す ＋ テストを2件 足す）

**`touches_search_path` が `True` でも、その変更が「足すだけ」なら通す。**

| いつ（kind） | 直した後の判定 |
|---|---|
| **設計書を書く瞬間**（design） | **通す。**まだプログラムを書き換えていないので、足すだけかを確かめられない。**確かめるのは次の段（プログラムを書く瞬間）** |
| **プログラムを書く瞬間**（code） | **中身を見る。**Edit なら `old_string` が `new_string` に含まれるか。Write なら**いまのファイルの全行が、新しい中身に順序を保って含まれるか**。**1行でも消えていたら止める** |
| **走らせる瞬間**（run） | **通す。**実行はファイルを1バイトも変えない |

### （5）守りはどう変わるか（★正直に書く）

| | いま | 直した後 |
|---|---|---|
| 探索の経路のファイルを触るとき | **「変えない」は書けない**＝`✅` か `❌` を書くしかない。**`✅` と嘘を書けば通る**（機械は中身を1つも確かめない） | **「変えない」を書ける。ただし機械が「足すだけか」を確かめる。**1行でも消えていたら止まる |

**＝新しい道を1つ開くが、その道には機械の検査が付く。**
**★いまの `✅` の道は、機械が何も確かめていない。**だから「守りが減る」とは言えない。

### （6）テスト（31件 → 33件）

**いまの件数＝31/31 pass**（実測 0.07秒・2026-08-29）。足すのは2件。

| # | 何を試すか | 期待 |
|---|---|---|
| 32 | 探索の経路のファイル（`observe_diag.py`）に**足すだけ**の変更で「変えない」を書く | **通る** |
| 33 | 同じファイルの**既存の行を消す**変更で「変えない」を書く | **止まる** |

### （7）★この直しの限界（3つ）

1. **設計書の瞬間は宣言を信じる。**捕まえるのはプログラムを書く瞬間。
2. **「足すだけ」でも、足した処理が探索を変えることはありうる**（例＝新しい関数を既存の処理から呼ぶ）。**機械が見るのは行の増減だけ。**
3. **hook 自身を書き換えれば無効にできる**（いままでと同じ）。

### （8）実装した（まこさん承認 `12478b53a6d9abfa`）

**承認の確かめ方**＝`.claude/state/acceptance.approved` の中身の先頭16文字と、設計書 `acceptance.md` のハッシュ値が**一致**（2026-08-29 09:30）。

**★設計から1つ厳しくした（承認をもらった中身との差・必ず報告する）**

| | 設計書に書いたこと | 実装したこと | なぜ変えたか |
|---|---|---|---|
| 設計書を書く瞬間 | **通す** | **設計書に「★足すだけ」と書いたときだけ通す** | そのままだと、engine_tuner の本体を直す設計書でも「変えない」が書けてしまう（テスト27・28 が通る）＝**守りが減る** |
| テストの件数 | 31 → **33** | 31 → **35** | 上の差で2件 増えた |

**直したもの（`.claude/hooks/enforce_purpose_gate.py`・94行 足して 7行 消した）**

| # | 何を | どこ |
|---|---|---|
| 1 | `MARK_ADD_ONLY = "★足すだけ"` と `_OLD_SEP` を足した | `MARK_KAENAI` の直後 |
| 2 | `_is_add_only(tool, file_path, content, old_content)` を新設 | `touches_search_path` の直後 |
| 3 | `judge(...)` に `old_content=""` の引数を足した | 引数の並びの末尾（既定値つき＝既存の呼び出しは壊れない） |
| 4 | 「変えない」の判定を、kind ごとに3つに分けた | design＝目印を見る／code＝足すだけかを機械で見る／run＝いままでどおり止める |
| 5 | `hook_main` で、消される側（`old_string`）を集めて `judge` に渡すようにした | `content` を作った直後 |
| 6 | 型の案内と、止まったときの案内に、例外の説明を足した | 2か所 |
| 7 | テストを4件 足した（32〜35）。**既存の31件は1行も書き換えていない**（並びの読み方だけ `row[:8]` に変えて、9個目が在れば `old_content` に渡す形にした） | `selftest()` |

**★テストが、私の誤りを2件 捕まえた（1回目の走行＝33/35）**

| # | 何が起きたか | 原因 | 直した |
|---|---|---|---|
| 26 | **走らせる瞬間に「変えない」が書けてしまった**（＝守りが減る） | 私の判定が、走らせる場合まで「足すだけ」で通していた | kind=run はいままでどおり止める形にした |
| 33 | 止まるべきなのに通った | **テストの見本に `engine_tuner` の文字が無く、そもそも判定に入っていなかった**＝32 も偽の pass だった | 見本に `engine_tuner` の文字を入れた |

**実測（2回目の走行）**

| # | 走らせたもの | 結果 |
|---|---|---|
| 1 | `python3 -m py_compile` | **構文 OK** |
| 2 | `--selftest` | **35/35 pass**（実測 0.08秒） |
| 3 | `hook_health_check.sh` | **✅ 異常なし**（登録・構文・エラーログ・合言葉0件） |
| 4 | `grep -c "_OK=1"` | **0件**（合言葉は戻っていない） |

**★まだ確かめていないこと**＝**本物の呼び出しで、M2-A-2 の設計書が書けるようになったか。**いまの `purpose_check.md` は この直し向けに書いてあるので、M2-A-2 向けに書き直してから確かめる（ToDo の6番）。
