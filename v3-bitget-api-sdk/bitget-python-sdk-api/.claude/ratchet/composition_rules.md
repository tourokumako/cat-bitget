<!-- COMPOSITION_RULES hash=f4a04f9f3e6d05b1 gen_composition_rules.py が自動生成＝手で書き換えない -->
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

手で書いた行は recipes/composition_rules_src.json の 0 件だけ。


## ★場面ごとの読み込ませる法則は、このファイルから regime_laws.json へ移した（M2-B0・2026-08-30）

**まこさん承認 iter="m2-b0-law-reader-20260830"。**7件（K-1〜K-7）は、相場の法則の正本 `regime_laws.json` の各法則（C1・C4・C6・R1・R8・R7・S1）の「機械が読む判定」になった。読むのは `engine_tuner_exec.load_regime_laws`・審査は G7。**法則を1件 書き替えると審査が変わる。**対応の記録＝`composition_rules_src.json` の `_M2-B0で移した7件`。


## 正本の指紋（元を直したら作り直す・--verify が照合する）

| 正本 | 指紋 |
|---|---|
| composition_rules_src.json | aac785d5d5a2c57b… |
| exit_families.json | fe095da61f8e6310… |
| search_limits.json | df063a11821bbfdf… |
| signal_families.json | e326f78fd4769b3a… |

