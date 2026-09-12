# 設計書の §4（設計の中身）に何を書くべきか — 3つの出どころの生の一覧

**★この一覧はプログラムが作ります（手で書き換えない）。**出どころ＝`gen_design_sections.py --write`。

**なぜ在るか**＝まこさん指摘 2026-09-10（逐語）「物事を組み立てる順番や複合要因の組み合わせ方など、思考が支離滅裂でその場しのぎすぎるんだよ」。私が思いつきで項目を足し、**4回とも まこさんの問いで「出どころに在るのに項目に入っていないもの」が出た**ため、**出どころから全部 抜いて番号を振る形にしました**（恒久の決まり39番）。

**件数**＝A（うちの正本）**46件** ／ B（外の標準）**35件** ／ C（過去の指摘）**38件** ／ 合計 **119件**。

**★番号は、項目への割り当て（`design_section_map.json`）で使います。**`--check` を打つと、**どの項目にも入っていない番号**を機械が出します＝私が「もう無い」と判断する場所がありません。

## A うちの正本が求めていること

| 番号 | 出どころ | 求めていること |
|---|---|---|
| A-1 | 恒久70番 §4 の中身 | 材料＝印がオンの指標・閾値・パラメータ・時間足・役割＝プログラムが出す |
| A-2 | 恒久70番 §4 の中身 | 守る法則＝法則ファイルから |
| A-3 | 恒久70番 §4 の中身 | 組み方＝文で |
| A-4 | 恒久70番 §4 の中身 | 作るとどうなるかの例を1つ |
| A-5 | 恒久70番 7つの節 | ①概要 |
| A-6 | 恒久70番 7つの節 | ②背景と範囲 |
| A-7 | 恒久70番 7つの節 | ③目標と やらないこと |
| A-8 | 恒久70番 7つの節 | ④設計の中身 |
| A-9 | 恒久70番 7つの節 | ⑤決めたことと理由・捨てた案 ⑥テストとリスクと見積もり ⑦付録 |
| A-10 | 恒久69番 手で書く5つ | 何を作るか |
| A-11 | 恒久69番 手で書く5つ | なぜ作るか |
| A-12 | 恒久69番 手で書く5つ | 作るとどうなるか（例を1つ） |
| A-13 | 恒久69番 手で書く5つ | 決めてほしいこと |
| A-14 | 恒久69番 手で書く5つ | 入れないものと理由 |
| A-15 | acceptance_checklist（群1） | `TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） |
| A-16 | acceptance_checklist（群1） | `DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` |
| A-17 | acceptance_checklist（群1） | ★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ |
| A-18 | acceptance_checklist（群1） | ① 真因（root cause・損/不足の構造的原因） |
| A-19 | acceptance_checklist（群1） | ② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） |
| A-20 | acceptance_checklist（群1） | ③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） |
| A-21 | acceptance_checklist（群1） | ④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） |
| A-22 | acceptance_checklist（群1） | 変更は 1レバーか（複数混ぜない） |
| A-23 | acceptance_checklist（群2） | 既定 OFF で恒等（新パラメータ None 等で既存ベースと完全一致）を設計で保証し、自己検査で確認するか |
| A-24 | acceptance_checklist（群1） | 過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） |
| A-25 | acceptance_checklist（群1） | ★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 |
| A-26 | acceptance_checklist（群1） | ★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc |
| A-27 | acceptance_checklist（群2） | 新しい exit_reason を出すか？ → YES なら「やること」に score.py の MAKER_EXIT_REASONS / TAKER_EXIT_REASONS へ登録 ＋ 既知答えテスト再pass」を含 |
| A-28 | acceptance_checklist（群2） | entry/exit のコスト種別（maker/taker）が変わるか？ → eval_engine / score の分類と一致するか確認 |
| A-29 | acceptance_checklist（群2） | judge（score.py / eval_engine）の計算式に触れるか？ → 原則触らない（H13）。触るなら既知答えテスト再pass を必須に |
| A-30 | acceptance_checklist（群2） | 新スクリプト名・出力CSV名は pdca 命名規約に乗るか（実験= strat_/train_/measure_/e3N_ ／ 分析= *_probe / *_deep_analysis ／ 審判= score.py C |
| A-31 | acceptance_checklist（群2） | 使用パラメータ・Entry/Exit ロジックのサイドカー出力を含めるか（新戦略は必須・2026-06-19）→ 売買記録CSVの隣に `<stem>_params.json` を `params_sidecar.wri |
| A-32 | acceptance_checklist（群2） | 出力は共通の書き出し処理を使うか（命名/archive/上書き防止の踏襲・2026-06-22 まこさん確定・全戦略汎用）→ 新しい戦略（e37/38/39…）は売買記録を共通の書き出し処理 `_output_and_r |
| A-33 | acceptance_checklist（群2） | 共通土台 `strat_base.py` を import するか（2026-06-23 新設・中立）→ 新戦略は `strat_base` から ①load_5m ／ ⑤_verify_cap・_funding_cos |
| A-34 | acceptance_checklist（群2） | H1 cap 合計 0.12 BTC（_verify_cap / score.assert_hard_constraints で実測） |
| A-35 | acceptance_checklist（群2） | H2 leak なし（特徴量 t 時点・`shift(-`/`center=True` grep assert・学習末 < 採点始） |
| A-36 | acceptance_checklist（群2） | H5 約定モデル（entry 指値maker・TTL3 / 出口 TP・SL=maker / TIME・能動=taker+slip） |
| A-37 | acceptance_checklist（群2） | H6 価格非依存（%/比率/BTC 単位・USD 絶対値の閾値/ラベル禁止） |
| A-38 | acceptance_checklist（群2） | H8 期間分割（学習窓で fit・採点窓は評価のみ・封印は不参照・値決め窓で選んだ値は確認窓で選び直さない）。実値は下の機械生成の表＝`gen_windows.py` が periods.py から差し込む（手で数字を書 |
| A-39 | acceptance_checklist（群2） | H13 judge 固定（score.py/eval_engine は実験で改造しない・改造時 既知答えテスト再pass） |
| A-40 | acceptance_checklist（群2） | H15 ボラ逃げ禁止（方向スコアで atr/ボラ 非支配・feature importance で確認） |
| A-41 | acceptance_checklist（群1） | H16 1変更・過去失敗の不再演 |
| A-42 | acceptance_checklist（群1） | 自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） |
| A-43 | acceptance_checklist（群2） | 学習窓で純増を先に測る（採点窓 不参照・H8）→ プラスかつ非degenerate なら採点 |
| A-44 | acceptance_checklist（群2） | 公式判定は score.py / score.score（CC は net 計算に触れない＝import のみ）・両窓で改善を確認するまで「効いた」と言わない |
| A-45 | acceptance_checklist（群2） | degenerate（near-inaction＝ほぼ無取引で損が小さいだけ）でないか（件数/伸びを玉単位で確認） |
| A-46 | hook（実測） | acceptance.md を相手にする hook＝32本 |

## B 外の標準が挙げている設計の関心事

| 番号 | 出どころ | 項目 | 本文の逐語 |
|---|---|---|---|
| B-1 | IEEE 1016-2009 の設計の視点 | Context viewpoint | The purpose of the Context viewpoint is to identify a design subject's offered services, its actors (users and other interacting stakeholders), to establish the system boundary and to effectively delineate the design subject's scope of use and operation. |
| B-2 | IEEE 1016-2009 の設計の視点 | Composition viewpoint | Software developers and maintainers use this viewpoint to identify the major design constituents of the design subject, to localise and allocate functionality, responsibilities, or other design roles to these constituents. |
| B-3 | IEEE 1016-2009 の設計の視点 | Logical viewpoint | The purpose of the Logical viewpoint is to elaborate existing and designed types and their implementations as classes and interfaces with their structural static relationships. |
| B-4 | IEEE 1016-2009 の設計の視点 | Dependency viewpoint | A Dependency view provides an overall picture of the design subject in order to assess the impact of requirements or design changes. It can help maintainers to isolate entities causing system failures or resource bottlenecks. |
| B-5 | IEEE 1016-2009 の設計の視点 | Information viewpoint | Key concerns include persistent data structure, data content, data management strategies, data access schemes, and definition of metadata. |
| B-6 | IEEE 1016-2009 の設計の視点 | Patterns use viewpoint | Key concerns include reuse at the level of design ideas (design patterns), architectural styles, and framework templates. |
| B-7 | IEEE 1016-2009 の設計の視点 | Interface viewpoint | An Interface view description serves as a binding contract among designers, programmers, customers, and testers. |
| B-8 | IEEE 1016-2009 の設計の視点 | Structure viewpoint | Compositional structure of coarse-grained components and reuse of fine-grained components |
| B-9 | IEEE 1016-2009 の設計の視点 | Interaction viewpoint | For designers. This includes evaluating allocation of responsibilities in collaborations, especially when adapting and applying design patterns. |
| B-10 | IEEE 1016-2009 の設計の視点 | State dynamics viewpoint | System dynamics including modes, states, transitions, and reactions to events. |
| B-11 | IEEE 1016-2009 の設計の視点 | Algorithm viewpoint | The Algorithm viewpoint provides details needed by programmers, analysts of algorithms in regard to time-space performance and processing logic prior to implementation. |
| B-12 | IEEE 1016-2009 の設計の視点 | Resource viewpoint | Key concerns include resource utilisation, resource contention, availability, and performance. |
| B-13 | Google の design doc | Context and scope | This section gives the reader a very rough overview of the landscape in which the new system is being built |
| B-14 | Google の design doc | Goals and non-goals | A short list of bullet points of what the goals of the system are |
| B-15 | Google の design doc | The actual design / System-context-diagram | Such a diagram shows the system as part of the larger technical landscape |
| B-16 | Google の design doc | The actual design / APIs | If the system under design exposes an API, then sketching out that API is usually a good idea |
| B-17 | Google の design doc | The actual design / Data storage | Systems that store data should likely discuss how and in what rough form this happens |
| B-18 | Google の design doc | The actual design / Code and pseudo-code | Design docs should rarely contain code, or pseudo-code except in situations where novel algorithms are described |
| B-19 | Google の design doc | The actual design / Degree of constraint | One of the primary factors that would influence the shape of a software design |
| B-20 | Google の design doc | Alternatives considered | This section lists alternative designs that would have reasonably achieved similar outcomes |
| B-21 | Google の design doc | Cross-cutting concerns | This is where your organization can ensure that certain cross-cutting concerns such as security, privacy, and observability are always taken into consideration |
| B-22 | Range の Tech Spec の問い | What are the user requirements? |  |
| B-23 | Range の Tech Spec の問い | What systems will be affected? |  |
| B-24 | Range の Tech Spec の問い | What new data structures are needed, what data structures will be changed? |  |
| B-25 | Range の Tech Spec の問い | What new APIs will be needed, what APIs will be changed? |  |
| B-26 | Range の Tech Spec の問い | What are the efficiency considerations (time/space)? |  |
| B-27 | Range の Tech Spec の問い | What are the expected access patterns (load/throughput)? |  |
| B-28 | Range の Tech Spec の問い | How will data be validated and what are the potential error states? |  |
| B-29 | Range の Tech Spec の問い | Are there any logging, monitoring, or observability needs? |  |
| B-30 | Range の Tech Spec の問い | Are there any security considerations? |  |
| B-31 | Range の Tech Spec の問い | Are there any privacy considerations? |  |
| B-32 | Range の Tech Spec の問い | Are there any mobile considerations? |  |
| B-33 | Range の Tech Spec の問い | Are there any web-specific considerations? |  |
| B-34 | Range の Tech Spec の問い | How will the changes be tested? |  |
| B-35 | Range の Tech Spec の問い | How does internationalization and localization — translations, time zones, unicode, etc. — affect your solution? |  |

## C まこさんが過去に「設計書に入っていない」と指摘した逐語

| 番号 | いつ | 逐語 |
|---|---|---|
| C-1 | 20260716 | 「刺さる×上抜けに轢かれない」 |
| C-2 | 20260720 | 「**CC が機械の出力に無い数字を書けなくする**」 |
| C-3 | 20260723 | 「設定駆動と設計書自動生成はどうなった」 |
| C-4 | 20260723 | 「設計書の自動生成（骨格を設定 json＋段0 実測から機械生成）」 |
| C-5 | 20260807 | 「設計は正本の網羅一覧との全数照合から始める。手近な要約・直前に触った材料から作らない。『何が正本の一覧か』を設計の1行目に書く」 |
| C-6 | 20260816 | 「直すことはOKだけど、これまでの範囲への修正はやってきてるのに、なんで今回36個も修正漏れがあった？」 |
| C-7 | 20260820 | 「足す形の設計を何の法則で決めるか」 |
| C-8 | 20260823 | 「まだ怪しいんだが。これは設計書なの？」 |
| C-9 | 20260825 | 「2番・3番は まこさんの1行に無い言葉」 |
| C-10 | 20260825 | 「実行器／解決表に鍵が無い」 |
| C-11 | 20260826 | 「実物にあるが設計に無い関数」 |
| C-12 | 20260901 | 「この設計に誤り・抜け・危険があるか」 |
| C-13 | 20260904 | 「うち材料に対応が無いのは5件」 |
| C-14 | 20260904 | 「承認の瞬間に空の凍結を止める機械が無い（`approve_impl.sh`:108／114・印字のみで exit しない・3回すり抜けた）」 |
| C-15 | 20260904 | 「照合が「設計書も凍結も空」 |
| C-16 | 20260904 | 「📐 設計書の側が出どころ」 |
| C-17 | 20260904 | 「★これは指示ではありません。実物を見て、直す根拠が無いなら「直さない・理由はこれ」 |
| C-18 | 20260904 | 「直す根拠が在るものだけ設計書を直して、まとめて1回で再提出してください。」 |
| C-19 | 20260904 | 「設計書に書いていないファイルを触った」 |
| C-20 | 20260904 | 「その時点で未コミットの .py が10本 在り、設計書の impl_functions に無かったから」 |
| C-21 | 20260904 | 「0本は設計・束には入らない（まこさん決定 2026-09-07）」 |
| C-22 | 20260904 | 「『設計書に書いていないファイルを触った』に数えない」 |
| C-23 | 20260904 | 「SPEC が設計書に無い（対象外）」 |
| C-24 | 20260904 | 「入れると書いたが入っていない」 |
| C-25 | 20260904 | 「守りを1本 消すと、対応する検査が落ちるか」 |
| C-26 | 20260904 | 「設計書に書いた関数が実装に在るか」 |
| C-27 | 20260909 | 「設計書が承認と食い違うので、依頼書を作れません（承認された値 fa168d22…／いまの設計書 25f4fd02…）」 |
| C-28 | 20260909 | 「承認の前に設計書を監査に出す」 |
| C-29 | 20260909 | 「依頼書の値: 0000000000000000… ／ いまの設計書: 25f4fd028b3aac4a…」 |
| C-30 | 20260909 | 「M2-E-2 で設計すると、どういう組み合わせが出せるようになるのか」 |
| C-31 | 20260909 | 「他にも条件として組み込んでいない法則は無いよね？」 |
| C-32 | 20260909 | 「`.claude/tools/gen_acceptance.py`＝設計書の impl_functions に書いていないファイルを触った」 |
| C-33 | 20260909 | 「設計にあるが実物に無い関数」 |
| C-34 | 20260910 | 「まるごと設計のコアの部分が無い状態だよね」 |
| C-35 | 20260910 | 「設計書のテンプレは汎用性のある項目にするよね？ まず、その項目を私に確認させて」 |
| C-36 | 20260910 | 「今回の設計内容に寄ってる感じだけど、本当に汎用的な項目なんだよね？ また簡略化してないよね？」 |
| C-37 | 20260910 | 「4-5 の『どこで止まるか』は、設計どおりに止まる場所のことです。入力が壊れていたとき、途中で落ちたとき、中途半端な出力が残ったとき、やり直せるかは書けません。」 |
| C-38 | 20260910 | 「どの項目にも入っていない番号」 |

**★C の抜き方の限界**＝「設計」を含み、かつ入っていないことを指す語（無い・落ち・入っていない・書いてない・足りない・抜け・ヌケ・漏れ・コア）を含む行から、鉤括弧の中を抜いています。**別の言い方をした指摘は拾えません。**
