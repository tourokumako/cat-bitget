<!-- COMPOSITION_RULES hash=dfc98537a8271619 gen_composition_rules.py が自動生成＝手で書き換えない -->
# composition_rules.md — engine_tuner が読む形の法則を作るために作ったが、実際は engine_tuner は読んでいない マコを欺くためだけの無意味な道具

> **★この見出しは、まこさんの指示（逐語 2026-08-29）です。**
>
> 「# composition_rules.md — 読み込ませる法則（全自動生成）ではなく、engine_tuner が読む形の法則を作るために作ったが、実際はengine_tuner は読んでいない マコを欺くためだけの無意味な道具って書いておけ」「こっちに書いておけ そのままに残せ」
>
> **なぜこう書かれたか（2026-08-29 に実物で確かめた事実）**
>
> - この道具の説明文には「くじを引く代わりに『相場の法則で候補を絞る』ためには、その相場の法則が機械の読める形で無いといけない。この道具はその相場の法則を作る」と書いてある。
>
> - 同じ説明文に「`composition_rules.json` … **engine_tuner が読む完成品**」と書いてある。
>
> - **しかし engine_tuner は、このファイルを読んでいない。**`engine_tuner_gen.py`:2188 が `load_scene_rules()` を呼ぶが、返り値を変数に受け取らずに捨てている。確かめているのは「ファイルが開けるか」だけ。
>
> - **30件のうち engine_tuner の動きに関わるのは7件（K-1〜K-7）だけだった。**残り23件は `engine_tuner_gen.py`（5,841行）と `engine_tuner_exec.py`（4,391行）に記号が **0回**しか出ない。
>
> - **その7件の判定も、このファイルではなく `engine_tuner_exec.py` の1094〜1119行にコードとして直接 書いてある。**
>
> - **★CC はこの状態を 2026-08-08 から 2026-08-29 まで確かめず、「engine_tuner が守る法則」として報告し続けた。**

**★2026-08-29（まこさん承認 rules30-to-7-20260829）＝30件から7件へ減らした。**消した23件は engine_tuner が1つも使っていなかった。逐語の出典がほかに無かった6件（ROLE-3・TW-1〜TW-5）は `technical_analysis_knowledge_base.md` の §J へ移した。

手で書いた行は recipes/composition_rules_src.json の 7 件だけ。


## ★場面ごとの読み込ませる法則（K-1〜K-7・まこさん承認 2026-08-22・プログラムが強制する）

engine_tuner が場面の判定の束（meta.regime.build）を作るとき、下の形を満たさない案は条件データを調べる部分（engine_tuner_exec.py の G7）が拒否する。数字は1つも持たない（閾値・本数・保つ長さは範囲で探す）。

| # | 読み込ませる法則 | 掛かる場面 | 出典 |
|---|---|---|---|
| K-1 | 「上げ」「下げ」を名乗る場面の判定の束には、向きを測る部品を1本以上 入れる（向きを持たない部品＝型の表の bans は数えない）。レンジ・スパイクには掛けない | uptrend・downtrend | regime_detection_kb.md §11 C1【本文】StockCharts 逐語『measures the… |
| K-2 | レンジ・上げ・下げの場面の判定の束には、執行足（5分足）より上の時間足の部品を1本以上 入れる。スパイクには掛けない（S1 は5分足1本の検定） | range・uptrend・downtrend | regime_detection_kb.md §11 C4【本文】LuxAlgo 逐語『Entries come fro… |
| K-3 | レンジ・上げ・下げの場面の判定の束には、成立の条件（on）と解除の条件（off）を別々に持つ、状態を保つ形（hysteresis）を1つ以上 入れる。スパイクには掛けない | range・uptrend・downtrend | regime_detection_kb.md §11 C6【本文】（安定させる仕組みは2つ）＋U10【実装】RG-v5＋… |
| K-4 | レンジの場面の判定の束には、構造・位置の系統の部品（帯・S/R タッチ実績）を1本以上 入れる | range | regime_detection_kb.md §11 R1【正本】range_scalping_kb §2 逐語『統計量… |
| K-5 | レンジの場面の判定の束には、トレンド状態の否定（not）を1本以上 入れる | range | regime_detection_kb.md §11 R8【実装】RG-v5 range_ok_rg5（帯あり ∩ 帯内… |
| K-6 | レンジの場面の判定の束には、帯の幅の条件を1本 入れる（下限の値は範囲で探す・幅を測る部品＝レンジ幾何の W% か、チャネルの幅の family） | range | regime_detection_kb.md §11 R7【正本】SCALP_FLOOR（e38_logic_parts… |
| K-7 | スパイクの場面の判定の束には、「いまの値動き ÷ ふだんの揺れ」の比を測る部品を1本以上 入れる（★2026-08-22 時点で該当の部品は0件＝スパイクの束はまだ組めない・部品は M2-8 で足す） | spike | regime_detection_kb.md §11 S1【実装】Lee-Mykland 2008（e36_short_… |

## 正本の指紋（元を直したら作り直す・--verify が照合する）

| 正本 | 指紋 |
|---|---|
| composition_rules_src.json | 6f9c50509ef21387… |
| exit_families.json | 5c90df3c8ac55dbe… |
| search_limits.json | 0396ff1b4eed6d93… |
| signal_families.json | b20d007cec4ba53f… |

