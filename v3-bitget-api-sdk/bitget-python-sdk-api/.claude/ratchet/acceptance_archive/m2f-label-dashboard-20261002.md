<!-- ARC iter="m2f-label-dashboard-20261002" -->

# 設計書｜⑪タブの道具 build_regime_label_dashboard.py を、札の部品 regime_label.py を呼ぶ形に切り替え、⑪タブの版を設定ファイルから作る＝14a の工事 C

TARGET: scripts/dashboard/build_regime_label_dashboard.py

REQUIREMENTS: 設計のもと（下の §0-1）＝逐語のファイル `m2f-label-dashboard-20261002/ok_labelC_20261002`・`m2f-label-dashboard-20261002/ok_split_20261002`・`m2f-label-dashboard-20261002/ok_todo_20261001`・`m2f-label-dashboard-20261002/okd_labelC_20261002`・`m2f-label-dashboard-20261002/req_6d_20260928`・`m2f-label-dashboard-20261002/req_split_20261001`。

**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2f-label-dashboard-20261002/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の5つだけです＝§1 概要・2-1 何を測るか・3-1 やらないこと・3-2 決めてほしいこと・4-19 通しの例。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2f-label-dashboard-20261002 --write`。検出＝`--work m2f-label-dashboard-20261002 --verify`。

## 0｜設計のもと（まこさんの発言と、まこさんが OK した文）

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

### 0-1 設計のもと（まこさんの発言と、まこさんが OK した文・プログラムが写しました）

［自動］逐語のファイル（記録から抜き出した・CC は写していない）と、対応の表（どの【】の下の行かで道具が作った）
<!-- ACC_SOURCE_START hash=d97681f7ad52c82a gen_acceptance.py が自動生成＝手で書き換えない -->
**要件のまとめ**＝`verbatim/m2f-label-dashboard-20261002/要件のまとめ.md`（プログラムが逐語のファイルから作った・要件の文・話し手・出どころの表はそこに在る）（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）。
**この設計書が写す逐語のファイル**＝`verbatim/m2f-label-dashboard-20261002/ok_labelC_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-dashboard-20261002/ok_split_20261002.txt`（まこさんの発言）・`verbatim/m2f-label-dashboard-20261002/ok_todo_20261001.txt`（まこさんの発言）・`verbatim/m2f-label-dashboard-20261002/okd_labelC_20261002.txt`（まこさんが OK した CC の文）・`verbatim/m2f-label-dashboard-20261002/req_6d_20260928.txt`（まこさんの発言）・`verbatim/m2f-label-dashboard-20261002/req_split_20261001.txt`（まこさんの発言）。照らし方＝`python3 .claude/tools/gen_verbatim.py --verify <名前>`。

**写した行＝362 行。**全部の行に、設計書のどこで満たすかの対応が在ります（1行でも無ければ `--write` が止まります）。


**逐語の行と、行った先の節（行の範囲だけ。文は、【】の下の行は下の各節に、見出しの外の行は要件のまとめに在る）**

| 逐語のファイル | 行 | 設計書の節 | 理由 |
|---|---|---|---|
| `ok_labelC_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_split_20261002` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `ok_todo_20261001` | V01〜V01（1 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelC_20261002` | V01〜V37（37 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `okd_labelC_20261002` | V38〜V42（5 行） | 4-0 | OK された案の【4-0】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V43〜V45（3 行） | 4-1 | OK された案の【4-1】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V46〜V49（4 行） | 4-2 | OK された案の【4-2】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V50〜V56（7 行） | 4-3 | OK された案の【4-3】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V57〜V62（6 行） | 4-4 | OK された案の【4-4】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V63〜V70（8 行） | 4-5 | OK された案の【4-5】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V71〜V80（10 行） | 4-6 | OK された案の【4-6】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V81〜V82（2 行） | 4-7 | OK された案の【4-7】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V83〜V84（2 行） | 4-8 | OK された案の【4-8】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V85〜V87（3 行） | 4-9 | OK された案の【4-9】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V88〜V89（2 行） | 4-10 | OK された案の【4-10】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V90〜V91（2 行） | 4-11 | OK された案の【4-11】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V92〜V93（2 行） | 4-12 | OK された案の【4-12】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V94〜V99（6 行） | 4-13 | OK された案の【4-13】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V100〜V109（10 行） | 4-14 | OK された案の【4-14】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V110〜V111（2 行） | 4-15 | OK された案の【4-15】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V112〜V113（2 行） | 4-16 | OK された案の【4-16】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V114〜V115（2 行） | 4-17 | OK された案の【4-17】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V116〜V120（5 行） | 4-18 | OK された案の【4-18】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V121〜V185（65 行） | 4-20 | OK された案の【4-20】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V186〜V194（9 行） | 5 | OK された案の【5】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V195〜V200（6 行） | 6-2 | OK された案の【6-2】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V201〜V206（6 行） | 6-3 | OK された案の【6-3】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V207〜V213（7 行） | 7-1 | OK された案の【7-1】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V214〜V215（2 行） | 7-2 | OK された案の【7-2】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V216〜V217（2 行） | 7-3 | OK された案の【7-3】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V218〜V222（5 行） | 7-3b | OK された案の【7-3b】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V223〜V233（11 行） | 7-4 | OK された案の【7-4】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V234〜V254（21 行） | 7-5 | OK された案の【7-5】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V255〜V258（4 行） | 7-6 | OK された案の【7-6】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V259〜V307（49 行） | 7-8 | OK された案の【7-8】の見出しの下の行（道具が決めた） |
| `okd_labelC_20261002` | V308〜V311（4 行） | 対応なし | OK された案の【外部検索】の行＝監査の依頼書の外部検索に写す（設計書には写さない・道具が決めた） |
| `req_6d_20260928` | V01〜V46（46 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |
| `req_split_20261001` | V01〜V02（2 行） | 対応なし | 【】の見出しの外の行（要件の発言・前置き・OK の返事）＝設計書の節には写さない。文は要件のまとめ.md に在る（要件の行か外した行かは、そこの表で分かる・道具が決めた） |

<!-- ACC_SOURCE_END -->

## 1｜概要

［手書き］やることの表の「§1 概要」
M2 は、4つの場面（レンジ・上げ・下げ・スパイク）の判定を、全部の戦略のために組む段です。組んだ判定の良し悪しは、答え合わせに使う札（そのバーが後から見て実際にレンジだったかの答え）と照らして測ります。工事 A で札を作る部品 regime_label.py と設定 recipes/regime_label.json を作り、工事 B で観察の道具と測る道具を、部品を呼ぶ形にしました。しかし⑪タブの道具 build_regime_label_dashboard.py は、まだ観察の道具の口を呼んで札を作り、版の名前を「label-er」の固定の頭で作り、仕様の文を道具の中に手で書いています。版2（band_hold＝帯・幅・続く）の札は⑪タブに1本も出ないので、まこさんは版2 の「使う値」を⑪タブで見比べて選べません。この工事 C は、⑪タブの道具を部品を呼ぶ形に切り替え、⑪タブの版を設定ファイルから作り、版の名前に使った値を入れ、仕様に設定の中身をそのまま出し、版2 は役割ごとに値の組を全部 版にして検査15 の数を添えます。採点に使う版は er_median のままなので、札・順位表・成績表の数字は変わりません。

## 2｜背景と範囲

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| ⑪タブの道具が、まだ観察の道具の口で札を作っている | `grep -c -F 'od._regime_' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/dashboard/build_regime_label_dashboard.py` | 実装の前は当たる行が在る。実装の後は当たる行が無い（札は部品の口で作る） | 0（終了コード 1） |
| ⑪タブの版の名前を、固定の頭でつないで作っている | `grep -c -F 'VERSION_PREFIX' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/dashboard/build_regime_label_dashboard.py` | 実装の前は当たる行が在る。実装の後は当たる行が無い（版の名前は regime_label.version_tag） | 0（終了コード 1） |
| 版2 の値の組を⑪タブに出す所が無い | `grep -c -F 'rl.variants' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/dashboard/build_regime_label_dashboard.py` | 実装の前は当たる行が無い。実装の後は当たる行が在る | 1（終了コード 0） |

### 2-2 探す材料・成績表・乱数（2-2〜2-4＝この工事では非該当）

［自動］TARGET と NEW_FILE から非該当を決めた
<!-- ACC_MATERIALS_START hash=146f46ddc53368ac gen_acceptance.py が自動生成＝手で書き換えない -->
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。
<!-- ACC_MATERIALS_END -->
<!-- ACC_RANKING_START hash=146f46ddc53368ac gen_acceptance.py が自動生成＝手で書き換えない -->
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。
<!-- ACC_RANKING_END -->
<!-- ACC_RANDOM_START hash=146f46ddc53368ac gen_acceptance.py が自動生成＝手で書き換えない -->
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。
<!-- ACC_RANDOM_END -->

## 3｜目標と、やらないこと

### 3-1 やらないこと（1件ずつ・理由と出どころ）

［手書き］やることの表の「3-1 やらないこと」
| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | 版2 の使う値を選ぶこと・採点に使う版を band_hold に切り替えること | 使う値は まこさんが⑪タブの目と検査15 で選ぶ。この工事は選ぶ材料（⑪タブの版と検査15 の数）を出すだけ | req_6d_20260928（「この3つの中でどれを使うかは、⑪タブで まこさんが見ることと、検査15 の片道の度合いで決めます。私は選びません。」） |
| 2 | 札の部品の自己検査 T6 に⑪タブの道具を足すこと | ⑪タブの道具は読むための道具で、過剰なテストを付けない。T6 を直すと札の部品 regime_label.py（H2 の対象）が変わり、H2 の取り直しが要る。⑪タブの道具が札の式を写していないことは、案を作る道具が ast で1回 照らした | permanent_rules.md の71番 |
| 3 | 壊すプログラムと自己検査を作ること | 読むための道具。動くことを1回 確かめる | permanent_rules.md の71番・build_regime_label_dashboard.py:21 |
| 4 | 画面（index.html・app.js）を直すこと | 仕様の欄は中身のまま並べる作りで、版の名前は版の一覧から読むので、直さずに出る | dashboard/assets/app.js:2924〜2938 |
| 5 | 上げ・下げ・スパイクの札を作ること | 範囲は M2-M-1 で まこさんが決める | worklog 20260928 §51 の4 |
| 6 | 版の道具 build_regime_from_tuner.py の乱数（build_bundles の187行）を消すこと | この工事の相手ではない（⑪タブの道具は write_version_files と update_index だけを呼び、乱数を通らない）。next_step の「あとで直すこと」に積む | permanent_rules.md の67番・59番 |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | ⑪タブに、版2 の値の組を全部（スキャル6版・デイトレ6版＝12版）出すか | 全部 出す。値を選ぶのは まこさんの目なので、見比べる相手が⑪タブに要る。案を作る道具が値決め窓の全部で走らせた実測＝12版で 45.2秒と 45.0秒（2回 測った・版のファイルを書く時間は入らない・4-14 は後の回）。置き場は git の対象外で、1版 約10MB。デイトレの1版（x5-m66-c3）は「レンジだった」が0本だったが、その値の組の結果として出す | regime_label.py:269〜285（variants）・9/29 の控えの実装の指示 27・req_6d_20260928 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころ118件を引き受ける形・検算＝`gen_design_sections.py --check`）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］まこさんが OK した案の【4-0】
**この工事は、⑪タブの道具が、答え合わせに使う札（正解ラベル）を札の部品 regime_label.py から受け取る形にするものです。**14a を3つに分けた3つ目の工事です（まこさん「よい」2026-10-02）。
**①いま何が起きているか。**⑪タブの道具は、観察の道具の口（_regime_labels と _regime_horizons）を呼んで札を作ります。版の名前は「label-er」と先を見る本数をつないで作ります。仕様の文（札の作り方・先を見る本数の出どころ）は、道具の中に手で書いてあります。版2（band_hold＝帯・幅・続く）の札は、⑪タブに1本も出ません。だから まこさんは、版2 の「使う値」を⑪タブで見比べて選べません。
**②この工事で何が変わるか。**⑪タブの道具は、札の部品の口（er_median と band_hold）を呼んで札を作ります。版の名前は札の部品の version_tag が作り、使った値が名前に入ります。仕様には、設定ファイル recipes/regime_label.json の中身をそのまま出します。版2 は、役割ごとに、設定の範囲の両端と真ん中の値の組を全部 版にします。版ごとに検査15 の数（片道の度合いの中央値）を数えて、仕様に出します。
**③数字は変わりません。**版1 の2版（label-er24・label-er288）の札は、直す前と同じです。採点に使う版は er_median のままなので、測る道具と成績表の数字も変わりません。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］まこさんが OK した案の【4-1】
**誰が動かすか。**私（CC）が、実装の後に1回 走らせます。そのあとは、まこさんが設定の値を書き替えたときに走らせ直します。
**誰が結果を使うか。**まこさんが、⑪タブ（dashboard_server.py の画面）で版を切り替えて見比べ、版2 の「使う値」を選びます。選んだ値は設定ファイルの「使う値」に書きます（この工事では書きません）。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］まこさんが OK した案の【4-2】
**読むもの。**5分足 CSV（値決め窓だけ）と、設定ファイル recipes/regime_label.json。
**書くもの。**版ごとに4種類のファイル（5分の月ごと・1時間・1日・札の CSV）と、版の一覧 index.json の1行。書くのは build_regime_from_tuner.py の write_version_files と update_index です（直さずに呼びます）。置き場は dashboard/regime_prototype/（git の対象外）です。
**画面に出るもの。**版の名前と仕様（札の版・設定の中身・使った値・数えた結果・検査15）。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］まこさんが OK した案の【4-6】
| 決まり | 出どころ | この設計でどう守るか |
|---|---|---|
| 札を作る場所を1つにする | まこさん決定 2026-09-28（構造の文の2つ目） | ⑪タブの道具は部品の口を呼ぶだけ。札の式（median）を持たない（下書きの道具が ast で照らした） |
| 値を書き替えて走らせ直すと、札と⑪タブの版が作り直される | まこさん決定 2026-09-28（構造の文） | 版の作り方と値は、走らせるたびに設定ファイルから読む |
| ⑪タブの版の名前に、使った値を入れる | まこさん決定 2026-09-28（構造の文） | 版の名前は regime_label.version_tag（役割と6つの値が入る） |
| 設定ファイルの中身を、画面の「仕様」にそのまま出す。手で書き写さない | まこさん決定 2026-09-28（構造の文） | spec_of が regime_label.spec の中身をそのまま入れる |
| 値を選ぶのは、⑪タブの まこさんの目と検査15。CC は選ばない | req_6d_20260928 | 使う値は空のまま。版ごとに検査15 の数を出すだけ |
| 絵にするのは値決め窓だけ | 恒久の決まり（やってはいけないこと13番） | load_window はそのまま（直さない） |
| 乱数を使わない | 恒久67番 | 値の組は regime_label.variants（範囲の両端と真ん中の決まった並び） |

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| build_regime_label_dashboard.py | 札を部品から受け取る（label_frame）・検査15 を数える（check15）・仕様を設定から作る（spec_of）・版1 と版2 の全部の版を作る（main） | 直す |
| regime_label.py | 札の式・版の名前・値の組・設定の中身（工事 A で作った口を、呼ばれるだけ） | 直さない |
| build_regime_from_tuner.py | 版のファイルと版の一覧を書く | 直さない |
- 触る所（build_regime_label_dashboard.py）＝<モジュール直下>・check15・label_frame・main・spec_of。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［自動］まこさんが OK した案の【4-4】
1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当てます（⑪タブの道具の1本だけ）。
2. 当てた直後に、照合（verify_design_contract.py --diff）をかけます。★設計書の SPEC（7-8）は、設計書を作った時点の実物（実装の前のコード）から作られます。この工事は関数 check15 を足し、label_frame が check15 を呼び、定数 VERSION_PREFIX を消すので、SPEC と実物が食い違う見込みです。食い違ったら、gen_acceptance.py --write で設計書を作り直し、承認の打ち直しを1回 お願いします（教訓 L-655＝工事 B と同じ型）。打ち直すまで、設計↔実装ゲートが⑪タブの道具の走行を止めます。
3. ⑪タブの道具を1回 走らせます（引数なし＝版1 と版2 の全部）。★走らせる前に、時間の見込みをフロー宣言に書きます（恒久60〜62番・見込みは 4-14）。
4. 版1 の2版の数が 2026-09-28 の走行と同じかと、版2 の版が役割ごとに全部 出たかを、印字と版の一覧で見ます。⑪タブの道具は H2 と G2 の対象に入っていないので、取り直しは要りません（4-13 の1）。
5. 実装を監査に出します。

### 4-19 通しの例（最初から最後まで、1件を追いかけた例）

［手書き］やることの表の「4-19 通しの例」
例＝python3 scripts/dashboard/build_regime_label_dashboard.py を引数なしで走らせると、版1 の2版（label-er24・label-er288）と、版2 の12版（例＝label-band-scalp-x5-m6-c2-mw1.0-wl1.0-h1.0＝スキャル・倍率5・m 6・c 2・まとめる幅1.0倍・幅の線1.0倍・続く本数1.0倍）を⑪タブに出す。label-er24 の数えた結果は 2026-09-28 の走行と同じ（レンジだった 79,044本・トレンドだった 79,044本・使えない 24本）。版2 の各版の仕様には、役割・使った値・手数料の床・設定ファイルのその役割の中身がそのまま出て、検査15 の片道の度合いの中央値（レンジの札とトレンドの札）が並ぶ。まこさんは⑪タブで版を切り替えて色の付き方を見比べ、検査15 の数と合わせて、役割ごとの「使う値」を選ぶ。

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］まこさんが OK した案の【4-7】
**探す値はありません。**版2 の値の組は、設定の「範囲」の両端と真ん中です（regime_label.variants）。⑪タブに出すだけで、選びません。

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］まこさんが OK した案の【4-9】
**新しい設定はありません。**読むのは工事 A の設定 recipes/regime_label.json だけです。
**コマンドの旗を1つ足します。**--version（all・er_median・band_hold。既定は all）。

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］まこさんが OK した案の【4-12】
**完成したときに画面に出るもの。**①走らせた印字に、版1 の2版と版2 の 12 版の名前が並び、版1 の数えた結果が 2026-09-28 と同じ。②⑪タブの版の一覧に、版2 の版が足される。③各版の仕様に、札の版・設定の中身・検査15 が出る。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［自動］まこさんが OK した案の【4-5】
| 起きたこと | どうなるか |
|---|---|
| 設定ファイルが無い・採点に使う版が式の無い名前 | 札の部品が読む時点で止まる（LabelError） |
| 版2 のある値の組で、帯が1本もできない | その版は「レンジだった」が0本の版として出る（止まらない）。仕様の数えた結果に0が出る |
| 検査15 で、レンジの札かトレンドの札が0本 | 中央値を出さず、本数だけを出す |
| 窓の外のバーが混ざる | load_window の _assert_search_window_only が止める（直さない） |
| 同じ名前の版が版の一覧に在る | update_index が消してから足す（直さない） |

### 4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）

［自動］まこさんが OK した案の【4-8】
**形が変わるもの。**①仕様の欄が変わります。「札の版」「札の作り方（設定の説明）」「採点に使う版（いまの設定）」「設定の在る所」「設定ファイルの中身」が足され、「正解ラベルの作り方」「先を見る本数の出どころ」が無くなります。②数えた結果に「検査15（片道の度合い）」が足されます。③道具の中の札の列の名前が label_range_<n> から label_range になります。版のファイルには range_built の名前で書かれるので、画面とファイルの形は変わりません。

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］まこさんが OK した案の【4-10】
**変えません。**dashboard/regime_prototype/（git の対象外）と、その中の index.json です。版2 の 12 版が足されます。1版の大きさは約10MB です（label-er24 の実測＝5分の月ごと 5.3MB・札の CSV 4.6MB・1時間 452KB・1日 20KB）。

### 4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）

［自動］まこさんが OK した案の【4-11】
**窓は変えません。**値決め窓だけを読みます（load_window は直しません）。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 窓を読む | 2.9秒 | 下書きの道具が、当てた後の道具を本物に書かずに走らせた実測（値決め窓 158,112本） |
| 版1 label-er24（札を付け・検査15 を数え・仕様を作る） | 0.2秒 | 同上（版のファイルを書く時間は入らない） |
| 版1 label-er288（札を付け・検査15 を数え・仕様を作る） | 0.1秒 | 同上（版のファイルを書く時間は入らない） |
| 版2 scalp（6版・窓の全部） | 合計 22.8秒（1版 2.4〜6.5秒） | 同上 |
| 版2 daytrade（6版・窓の全部） | 合計 22.2秒（1版 2.3〜7.2秒） | 同上 |
| 版2 の全部（12版） | 45.0秒 | 同上（版のファイルを書く時間は入らない） |
| 版のファイルを書く | 1版 約2.5秒以下 | 2026-09-28 の走行（1版 2.5秒＝札を付けるのと書くのを合わせた時間・worklog 20260928 §34） |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］まこさんが OK した案の【4-15】
**奪い合いに気をつけるもの。**版の一覧 index.json は、⑪タブのほかの版を作る道具（build_regime_from_tuner.py）も書きます。2つを同時に走らせません。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］まこさんが OK した案の【4-16】
**触らないもの。**人に見せてはいけない値（取引所の鍵・本番の発注の切り替え）には触りません。書き換えられては困る記録（H2・G2 の検査済みの記録・承認の記録）にも触りません。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］まこさんが OK した案の【4-17】
**画面に出すもの。**版ごとに「[2/3] 何番目/全部 版の名前: 札を付ける ...」と、数えた結果・月のファイルの数・レンジの割合・秒を出します。最後に版の名前の一覧を出します。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［自動］まこさんが OK した案の【4-13】
1. **⑪タブの道具は、H2 と G2 の対象に入っていません。**h2_pass.json と g2_pass.json に、道具の名前も関数の名前（label_frame）も0件でした。
2. **画面（index.html・app.js）は直しません。**仕様の欄は、中身をそのまま並べる作りです（app.js:2932）。版の名前は版の一覧から読みます。
3. **版1 の2版は、同じ名前（label-er24・label-er288）で上書きされます。**札の数は同じで、仕様の欄だけが変わります。
4. **⑪タブの道具の行の文字を探している壊すプログラムは0本でした**（.claude/breaks/*.sh を、道具の名前と関数の名前の2つで grep した）。
5. **版の道具 build_regime_from_tuner.py の build_bundles（187行）に乱数が在ります。**この工事は write_version_files と update_index だけを呼ぶので、乱数は通りません。next_step の「あとで直すこと」に積みます（恒久67番・59番）。

### 4-18 再利用（手本にした、既にあるものの形）

［自動］まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| 9/29 の控えの実装の指示 23〜27 | 実装の指示の中身（道具で取り出した） |
| observe_diag の検査15（_insp_regime_label_oneway） | 検査15 の数え方（check15 は _oneway_ratio と _independent_step を呼ぶ・式は写さない） |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=23c50a26ce7a572c gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 2〜22行（<モジュール直下>）
直す前の文字:
~~~
"""build_regime_label_dashboard.py — 答え合わせに使う正解ラベル（いまの作り方）を、⑪タブの版として出す

2026-09-28（132回目）・まこさん「OK」（逐語＝「まず、現状に正解ラベルの精度を視覚で判断したいので、
ダッシュボードに表示させるとかできない？」→ 作り方を出して「OK」）。

何をするか（4つ）
  1. 5分足 CSV を読み、値決め窓（periods.SEARCH_START〜SEARCH_END）だけを切り出す
       ＝observe_diag の検査15（_insp_regime_label_oneway）と同じ切り出し方
  2. いまの正解ラベルを付ける ＝ observe_diag._regime_labels(win, n)["強さ"]
       （先 n本の ER が窓の中央値以上なら「トレンドだった」。★式はここに写さない＝observe_diag を呼ぶだけ）
       n＝observe_diag._regime_horizons()（= recipes/search_limits.json の state_hold_bars_range の両端＝24・288）
       ⑪タブに色を付けるのは「レンジだった」＝強さが偽 かつ 使える（先が足りる）バー
  3. 版のファイル4種類を書き出す ＝ build_regime_from_tuner.write_version_files（同じ形・同じ決まり）
       predictions_<版>_1h.json ／ _1d.json ／ predictions_<版>_5m/<年月>.json ／ labels_<版>.csv
  4. 版の一覧（index.json）に足す ＝ build_regime_from_tuner.update_index（同じ名前が在れば消してから足す）

版の名前＝label-er<n>（例＝label-er24・label-er288）

★絵にするのは値決め窓だけ（採点窓・封印窓は1本も出さない＝やってはいけないこと13番）。
★これは読むための道具（恒久の決まり71番）＝壊すプログラムは付けない。動くことを1回 確かめる。
★正解ラベルの式は observe_diag.py の1か所だけ（ここに書き写さない＝式を2か所に持たない）。
~~~
直した後の文字:
~~~
"""build_regime_label_dashboard.py — 答え合わせに使う正解ラベル（札）の版を、⑪タブの版として出す

2026-09-28（132回目）・まこさん「OK」（逐語＝「まず、現状に正解ラベルの精度を視覚で判断したいので、
ダッシュボードに表示させるとかできない？」→ 作り方を出して「OK」）。
2026-10-02（M2-F-6d の工事 A〜C）・札を作る場所を regime_label.py の1か所にし、数字を recipes/regime_label.json に置いた
（まこさん決定 2026-09-28＝m2_todo.json の M2-F-6d の注意に逐語）。

何をするか（4つ）
  1. 5分足 CSV を読み、値決め窓（periods.SEARCH_START〜SEARCH_END）だけを切り出す
       ＝observe_diag の検査15（_insp_regime_label_oneway）と同じ切り出し方
  2. 札を付ける ＝ regime_label.py を呼ぶだけ（★式はここに写さない）
       版1 er_median＝先を見る本数ごと（設定の「先を見る本数」）
       版2 band_hold＝役割ごと × 設定の範囲の両端と真ん中の値の組（regime_label.variants）＝まこさんが目で見て「使う値」を選ぶ
       ⑪タブに色を付けるのは「レンジだった」＝強さが偽 かつ 使えるバー
       版ごとに検査15（片道の度合いの中央値・レンジの札とトレンドの札）を数えて仕様に出す
       ＝値を選ぶのは、⑪タブの まこさんの目と検査15（定義の原文＝m2_todo.json の M2-F-6d の注意）
  3. 版のファイル4種類を書き出す ＝ build_regime_from_tuner.write_version_files（同じ形・同じ決まり）
       predictions_<版>_1h.json ／ _1d.json ／ predictions_<版>_5m/<年月>.json ／ labels_<版>.csv
  4. 版の一覧（index.json）に足す ＝ build_regime_from_tuner.update_index（同じ名前が在れば消してから足す）

版の名前＝regime_label.version_tag（版1＝label-er24・label-er288／版2＝label-band-<役割>-<値の組>＝使った値が名前に入る）
画面の「仕様」＝設定ファイルの中身を、そのまま出す（手で書き写さない）

★絵にするのは値決め窓だけ（採点窓・封印窓は1本も出さない＝やってはいけないこと13番）。
★これは読むための道具（恒久の決まり71番）＝壊すプログラムは付けない。動くことを1回 確かめる。
★札の式は regime_label.py の1か所だけ（ここに書き写さない＝式を2か所に持たない）。
~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:2「"""build_regime_label_dashboard.py — 答え合わせに使う正解ラベル（いまの作り方）を、⑪タブの版として出す」
状態: 確定

#### 実装 2
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 27行（<モジュール直下>）
直す前の文字:
~~~
  python3 scripts/dashboard/build_regime_label_dashboard.py --csv data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv
~~~
直した後の文字:
~~~
  python3 scripts/dashboard/build_regime_label_dashboard.py --csv data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv
  python3 scripts/dashboard/build_regime_label_dashboard.py --version er_median   （版1 だけ）
  python3 scripts/dashboard/build_regime_label_dashboard.py --version band_hold   （版2 だけ＝役割ごとに、設定の範囲の両端と真ん中の値の組を全部）
~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:27「  python3 scripts/dashboard/build_regime_label_dashboard.py --csv data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv」
状態: 確定

#### 実装 3
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 45行（<モジュール直下>）
直す前の文字:
~~~
VERSION_PREFIX = "label-er"
~~~
直した後の文字:
~~~
import regime_label as rl   # noqa: E402  札を作る、ただ1つの場所（M2-F-6d）
~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:45「VERSION_PREFIX = "label-er"」
状態: 確定

#### 実装 4
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 60〜72行（label_frame）
直す前の文字:
~~~
def label_frame(win: pd.DataFrame, n: int) -> tuple[pd.DataFrame, str, dict]:
    """いまの正解ラベルを付けた表を返す。列＝ts・close・<列名>（レンジだった＝True）。"""
    import observe_diag as od

    mask, usable = od._regime_labels(win, n)["強さ"]        # 強さ＝真ならトレンドだった
    col = f"label_range_{n}"
    is_range = (usable.fillna(False) & ~mask.fillna(False)).astype(bool)
    df = pd.DataFrame({"ts": win.index, "close": win["close"].to_numpy(), col: is_range.to_numpy()})
    counts = {"レンジだった": int(is_range.sum()),
              "トレンドだった": int((usable.fillna(False) & mask.fillna(False)).sum()),
              "使えない（先が足りない）": int((~usable.fillna(False)).sum()),
              "全部": int(len(df))}
    return df, col, counts
~~~
直した後の文字:
~~~
def check15(win: pd.DataFrame, n: int, mask: pd.Series, usable: pd.Series) -> dict:
    """検査15 と同じ数え方を、この版の札に掛ける（値を選ぶ材料＝まこさんの目と検査15）。

    片道の度合い＝observe_diag._oneway_ratio、重なった区間を数えない間隔＝observe_diag._independent_step（式は写さない）。
    ★判定はしない（数を出すだけ）。レンジの札の中央値がトレンドの札より低いほど、札がレンジらしさを捉えている。
    """
    import observe_diag as od
    ratio = od._oneway_ratio(win, n)
    step = od._independent_step("5m", n)
    idx = win.index[::step]
    r = ratio.reindex(idx)
    m = mask.reindex(idx)
    u = usable.reindex(idx).fillna(False) & r.notna()
    rng = r[u & ~m.fillna(True)]
    trd = r[u & m.fillna(False)]
    out = {"先の本数": int(n), "数える間隔（本）": int(step),
           "レンジの札の本数": int(len(rng)), "トレンドの札の本数": int(len(trd))}
    if len(rng) and len(trd):
        out["片道の度合いの中央値（レンジの札）"] = round(float(rng.median()), 3)
        out["片道の度合いの中央値（トレンドの札）"] = round(float(trd.median()), 3)
    return out


def label_frame(win: pd.DataFrame, version: str, key, values: dict | None = None) -> tuple[pd.DataFrame, str, dict]:
    """札を付けた表を返す。列＝ts・close・<列名>（レンジだった＝True）。★札の式は regime_label.py（呼ぶだけ）。

    version＝"er_median"（key＝先を見る本数）か "band_hold"（key＝役割・values＝⑪タブに出す値の組）。
    """
    cfg = rl.load_config()
    if version == "er_median":
        mask, usable = rl.er_median(win, int(key))["強さ"]        # 強さ＝真ならトレンドだった
    else:
        mask, usable = rl.band_hold(win, cfg, str(key), values)["強さ"]
    col = "label_range"
    is_range = (usable.fillna(False) & ~mask.fillna(False)).astype(bool)
    df = pd.DataFrame({"ts": win.index, "close": win["close"].to_numpy(), col: is_range.to_numpy()})
    counts = {"レンジだった": int(is_range.sum()),
              "トレンドだった": int((usable.fillna(False) & mask.fillna(False)).sum()),
              "使えない（先か前が足りない）": int((~usable.fillna(False)).sum()),
              "全部": int(len(df))}
    n15 = int(key) if version == "er_median" else rl.role_bars(cfg, str(key), values)
    counts["検査15（片道の度合い）"] = check15(win, n15, mask, usable)
    return df, col, counts
~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:60「def label_frame(win: pd.DataFrame, n: int) -> tuple[pd.DataFrame, str, dict]:」
状態: 確定

#### 実装 5
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 75〜94行（spec_of）
直す前の文字:
~~~
def spec_of(csv_path: pathlib.Path, win: pd.DataFrame, n: int, counts: dict, start, end) -> dict:
    """画面に出す仕様＝実物から作る（手で書かない）。"""
    md5 = hashlib.md5(csv_path.read_bytes()).hexdigest()[:12]
    return {
        "これは何か": ("engine_tuner の判定ではなく、判定の答え合わせに使う「正解ラベル」そのもの。"
                    "M2-A-3（2026-08-29）で決まった いまの作り方を、そのまま絵にした"),
        "入力データ": f"{csv_path.name}（5分足・値決め窓 {len(win):,}本・md5 {md5}）",
        "期間（絵にした所）": (f"値決め窓 {pd.Timestamp(start).date()}〜{(pd.Timestamp(end) - pd.Timedelta(days=1)).date()}"
                      "（periods.py が正本。採点窓・封印窓は1本も出していない）"),
        "正解ラベルの作り方": (f"そのバーから先 {n} 本（5分足なので {n * 5} 分）の ER（まっすぐ進んだ距離 ÷ 実際に歩いた距離）が、"
                      "この窓の中央値以上なら「トレンドだった」、未満なら「レンジだった」。★中央値で切るので、使えるバーの半分がレンジになる"),
        "色が付くバー": "「レンジだった」＝強さが偽 かつ 先が足りて使えるバー。末尾の先が足りないバーは色なし",
        "先を見る本数の出どころ": ("recipes/search_limits.json の state_hold_bars_range の両端（observe_diag._regime_horizons）"
                          "＝RG-v5 の停滞 2h と継続の窓 24h から取った値"),
        "式の在る所": "scripts/priority_rebuild/observe_diag.py の _regime_labels（この道具は呼ぶだけ・式を写していない）",
        "数えた結果": counts,
        "教師": "なし＝過去チャートの先の値動きから付けた札（手動のラベルは1件も読まない）",
        "出力粒度": "5m（月別）/ 1h（5分の多数決）/ 1d（日内のレンジ率 0.5 以上）",
        "生成方式": "scripts/dashboard/build_regime_label_dashboard.py が実行時の実物から本仕様を作る（手で書かない）",
    }
~~~
直した後の文字:
~~~
def spec_of(csv_path: pathlib.Path, win: pd.DataFrame, version: str, key, values, counts: dict, start, end) -> dict:
    """画面に出す仕様＝設定ファイルと実物から作る（手で書かない）。"""
    md5 = hashlib.md5(csv_path.read_bytes()).hexdigest()[:12]
    cfg = rl.load_config()
    ver = rl.spec(cfg)["版"][version]
    out = {
        "これは何か": ("engine_tuner の判定ではなく、判定の答え合わせに使う「正解ラベル（札）」そのもの。"
                    "札を作る場所は regime_label.py の1か所（M2-F-6d）"),
        "札の版": rl.version_tag(cfg, version, key, values),
        "入力データ": f"{csv_path.name}（5分足・値決め窓 {len(win):,}本・md5 {md5}）",
        "期間（絵にした所）": (f"値決め窓 {pd.Timestamp(start).date()}〜{(pd.Timestamp(end) - pd.Timedelta(days=1)).date()}"
                      "（periods.py が正本。採点窓・封印窓は1本も出していない）"),
        "札の作り方（設定の説明）": ver.get("説明"),
        "採点に使う版（いまの設定）": cfg["採点に使う版"],
        "色が付くバー": "「レンジだった」＝強さが偽 かつ 使えるバー。先か前のバーが足りないバーは色なし",
        "式の在る所": "scripts/priority_rebuild/regime_label.py（この道具は呼ぶだけ・式を写していない）",
        "設定の在る所": ("scripts/priority_rebuild/recipes/regime_label.json（値を書き替えて走らせ直すと、"
                     "札と⑪タブの版が作り直される）"),
        "数えた結果": counts,
        "教師": "なし＝過去チャートの先の値動きから付けた札（手動のラベルは1件も読まない）",
        "出力粒度": "5m（月別）/ 1h（5分の多数決）/ 1d（日内のレンジ率 0.5 以上）",
        "生成方式": "scripts/dashboard/build_regime_label_dashboard.py が実行時の設定ファイルと実物から本仕様を作る（手で書かない）",
    }
    if version == "er_median":
        out["先を見る本数"] = f"{int(key)} 本（5分足なので {int(key) * 5} 分）"
        out["設定ファイルの中身（この版・そのまま）"] = ver
    else:
        out["役割"] = str(key)
        out["使った値"] = values
        out["手数料の床（e38_logic_parts.SCALP_FLOOR）"] = rl.fee_floor()
        out["設定ファイルの中身（この役割・そのまま）"] = ver["役割"][str(key)]
    return out
~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:75「def spec_of(csv_path: pathlib.Path, win: pd.DataFrame, n: int, counts: dict, start, end) -> dict:」
状態: 確定

#### 実装 6
対象のファイル: scripts/dashboard/build_regime_label_dashboard.py
直す箇所: 97〜134行（main）
直す前の文字:
~~~
def main() -> int:
    ap = argparse.ArgumentParser(description="いまの正解ラベルを ⑪タブの版として出す")
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="5分足 CSV（既定＝Binance spot の正本）")
    a = ap.parse_args()
    csv_path = pathlib.Path(a.csv)
    if not csv_path.exists():
        print(f"❌ CSV が無い: {csv_path}")
        return 2

    import observe_diag as od
    from build_regime_from_tuner import INDEX_JSON, PROTO_DIR, update_index, write_version_files
    from periods import SEARCH_END, SEARCH_START

    t0 = time.time()
    print(f"[1/3] 5分足を読み、値決め窓を切り出す ... {csv_path.name}")
    win = load_window(csv_path)
    print(f"    値決め窓 {len(win):,}本（{win.index.min()} 〜 {win.index.max()}）・{time.time() - t0:.1f}秒")

    n_ver = None
    for n in od._regime_horizons():
        version = f"{VERSION_PREFIX}{n}"
        t1 = time.time()
        print(f"[2/3] {version}: 正解ラベルを付ける（先 {n} 本）...")
        df, col, counts = label_frame(win, n)
        st = write_version_files(PROTO_DIR, version, df, col, SEARCH_START, SEARCH_END)
        dist = {"range": {"count": st["range_count"], "pct": st["range_pct"]},
                "non_range": {"count": len(df) - st["range_count"],
                              "pct": round((len(df) - st["range_count"]) / max(len(df), 1) * 100, 2)}}
        n_ver = update_index(INDEX_JSON, version, spec_of(csv_path, win, n, counts, SEARCH_START, SEARCH_END),
                             dist, st["months"])
        print(f"    数えた結果＝{counts}")
        print(f"    月のファイル {st['n_month_files']} 本／5分 {st['n_5m_rows']:,}行／1時間 {st['n_1h_rows']:,}行／"
              f"レンジ {st['range_pct']}%／版の合計 {n_ver}／{time.time() - t1:.1f}秒")

    print(f"\n[3/3] 完了（{time.time() - t0:.1f}秒）。⑪タブ → 版 {VERSION_PREFIX}24・{VERSION_PREFIX}288 → 粒度5分 → 月を選ぶ")
    print("      比べる相手＝同じ⑪タブの rg-v5（いま E38 が使っている判定）")
    print("      画面の出し方＝python3 scripts/dashboard/dashboard_server.py")
    return 0
~~~
直した後の文字:
~~~
def main() -> int:
    ap = argparse.ArgumentParser(description="札の版を ⑪タブの版として出す")
    ap.add_argument("--csv", default=str(DEFAULT_CSV), help="5分足 CSV（既定＝Binance spot の正本）")
    ap.add_argument("--version", choices=("all", "er_median", "band_hold"), default="all",
                    help="出す版（既定＝全部。band_hold は役割ごとに設定の範囲の両端と真ん中の値の組を全部）")
    a = ap.parse_args()
    csv_path = pathlib.Path(a.csv)
    if not csv_path.exists():
        print(f"❌ CSV が無い: {csv_path}")
        return 2

    from build_regime_from_tuner import INDEX_JSON, PROTO_DIR, update_index, write_version_files
    from periods import SEARCH_END, SEARCH_START

    cfg = rl.load_config()
    jobs = []
    if a.version in ("all", "er_median"):
        jobs += [("er_median", n, None) for n in rl.horizons(cfg)]
    if a.version in ("all", "band_hold"):
        jobs += [("band_hold", role, v) for role in rl.roles(cfg) for v in rl.variants(cfg, role)]

    t0 = time.time()
    print(f"[1/3] 5分足を読み、値決め窓を切り出す ... {csv_path.name}")
    win = load_window(csv_path)
    print(f"    値決め窓 {len(win):,}本（{win.index.min()} 〜 {win.index.max()}）・{time.time() - t0:.1f}秒")

    names = []
    n_ver = None
    for i, (version, key, values) in enumerate(jobs, start=1):
        name = rl.version_tag(cfg, version, key, values)
        t1 = time.time()
        print(f"[2/3] {i}/{len(jobs)} {name}: 札を付ける ...")
        df, col, counts = label_frame(win, version, key, values)
        st = write_version_files(PROTO_DIR, name, df, col, SEARCH_START, SEARCH_END)
        dist = {"range": {"count": st["range_count"], "pct": st["range_pct"]},
                "non_range": {"count": len(df) - st["range_count"],
                              "pct": round((len(df) - st["range_count"]) / max(len(df), 1) * 100, 2)}}
        n_ver = update_index(INDEX_JSON, name, spec_of(csv_path, win, version, key, values, counts,
                                                       SEARCH_START, SEARCH_END), dist, st["months"])
        names.append(name)
        print(f"    数えた結果＝{counts}")
        print(f"    月のファイル {st['n_month_files']} 本／5分 {st['n_5m_rows']:,}行／1時間 {st['n_1h_rows']:,}行／"
              f"レンジ {st['range_pct']}%／版の合計 {n_ver}／{time.time() - t1:.1f}秒")

    print(f"\n[3/3] 完了（{time.time() - t0:.1f}秒）。⑪タブ → 版（{len(names)} 本）→ 粒度5分 → 月を選ぶ")
    for nm in names:
        print(f"      {nm}")
    print("      比べる相手＝同じ⑪タブの rg-v5（いま E38 が使っている判定）")
    print("      画面の出し方＝python3 scripts/dashboard/dashboard_server.py")
    return 0
~~~
根拠の抜き書き: scripts/dashboard/build_regime_label_dashboard.py:97「def main() -> int:」
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
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 6 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 9/29 の控えの 23〜27 を土台にし、直すのは事実が変わった所と足す所だけにする | 9/29 の控えは まこさんの構造の文と定義の文を満たす形で書いた。手で書き直すと写し間違いが入る | 一から書き直す。捨てた理由＝写し間違いが入る |
| 2 | 23番の説明の文の日付を 2026-10-02 にする | 札の部品を作ったのは工事 A（2026-10-02・commit c61ea74）。9/29 は設計書の土台を書いた日 | 9/29 のまま。捨てた理由＝説明が事実と食い違う |
| 3 | 23番の、値を選ぶ材料の出どころを まこさんの原文（m2_todo.json の M2-F-6d の注意）にする | label_structure_definition_verbatim_20260929.txt は CC の要約（監査 cp58 の修正4 と同じ事実） | 要約のファイルのまま。捨てた理由＝原文でないものを出どころにする |
| 4 | 使い方の行に --version の例を足す | 旗を足すので、使い方の説明と実物が食い違わないようにする | 足さない。捨てた理由＝説明が実物と食い違う |
| 5 | 札の部品の自己検査 T6 に⑪タブの道具を足さない | 恒久71番＝読むための道具に過剰なテストを付けない。T6 を直すと札の部品（H2 の対象）が変わり、H2 の取り直しが要る | T6 に足す。捨てた理由＝読むための道具のために、売買の経路の部品を直すことになる |
| 6 | 版2 の値の組を全部 版にする | 値を選ぶのは まこさんの目（req_6d）。見比べる相手が⑪タブに無いと選べない | 真ん中の組だけ出す。捨てた理由＝見比べられない |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=060059ea372b0b96 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `—` | #1 | 壊すプログラムは付けない（読むための道具＝恒久71番。直す前と後で版1 の数が同じかを、2026-09-28 の印字と照らす） |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 版2 の全部の版を作るのに時間がかかる | 4-14 の見込みをフロー宣言に書いてから走らせる。見込みの2倍を超えたら止めて まこさんに出す |
| 2 | 版2 のある値の組で、帯が1本もできない | そのまま出す（その値の組の結果として、まこさんが見る） |
| 3 | 置き場の大きさが増える | 1版 約10MB。git の対象外の置き場なので commit には入らない |

### 6-3 見積もり

［自動］まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる | 30秒未満 | 当てる道具は1秒未満で終わった（2026-10-02 の監査 cp59 の直し・worklog 20261002 §10） |
| ⑪タブの道具を1回 走らせる | 版2 の札だけで約 0.8 分。これに版1 と版のファイルを書く時間が足される | 4-14 |
| まこさんの承認 | 2回（当てる前に1回・当てた後に SPEC を実物から作り直した設計書に1回） | 4-4 の2（教訓 L-655） |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書に効いている監査の指摘＝非該当**（監査レポートの欄が空＝この設計書は監査の指摘を受けていない・道具が決めた）

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］まこさんが OK した案の【7-1】
**① 真因（root cause）**＝⑪タブの道具が、札を観察の道具の口から受け取り、版の名前と仕様を道具の中で手で作っていることです。だから版2 の札が⑪タブに出ず、まこさんが値を選べません。

**② 期待値分解**＝売買のロジックには触れません。勝率・平均利益・敗率・平均損失は動きません。採点に使う版は er_median のままなので、判定の成績（3つの割合）も動きません。

**③ root か symptom か**＝root です。まこさんが決めた構造（設定から作る・名前に値を入れる・仕様に設定の中身を出す）そのものを、⑪タブの道具に作ります。

**④ ベースアップ**＝版の名前と仕様の作り方は、まこさんの構造の文に従いました。検査15 の数え方は、observe_diag の検査15 と同じ口を呼びます。

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］まこさんが OK した案の【7-2】
この工事に、疑似シミュから取った値は1つもありません。新しい数字も作りません。値の組は設定ファイルの範囲から、先を見る本数は設定ファイルから読みます。

### 7-3 変更の単位（H16）

［自動］まこさんが OK した案の【7-3】
変更は1つ＝⑪タブの道具を、札の部品を呼ぶ形に切り替え、版を設定ファイルから作る（14a の工事 C＝L-1 の⑪タブの分・L-7）。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

［自動］TARGET と NEW_FILE から非該当を決めた
**非該当。**この工事の直す相手（TARGET・NEW_FILE）に、売買のロジック（scripts/priority_rebuild・engine_tuner）が無い（プログラムが TARGET と NEW_FILE から決めました）。

### 7-4 塞げないもの

［自動］まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **版2 のどの値の組が正しいか** | この工事では分かりません。まこさんが⑪タブの目と検査15 で選び、最後は M2-L の net で分かります |
| **⑪タブの道具に札の式が書き写されたら** | 自己検査は付けません（恒久71番）。実装の監査と、下書きの道具の ast の照らしで1回 確かめます |
| **⑪タブの道具そのものを書き換えられたら** | 書き換えれば無効にできます。承認で凍結され、差分は git に出ます |
| **Q5 の1＝完成の条件の数が合っていれば、中身も正しいか** | 見ません。行の数がそろっていれば、欄の中身が入れ替わっていても通ります |
| **Q5 の2＝見出しの列の数が正しいか** | 見出しの行を基準にします。見出し自体がずれていたら、その数を正しいものとして扱います |
| **Q5 の3＝表が2つ以上 在るとき** | プログラムが読む目印の中の表だけを見ます。ほかの表は見ません |
| **Q5 の4＝この設計書を作る道具を書き換えられたら** | その道具自身を書き換えれば無効にできます（承認ゲートの対象なので承認は要ります） |
| **Q5 の5＝過去の設計書の控え** | 直せません（承認の後は凍結されているため） |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=d2e09ee8d879d708 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET＝1本（⑪タブの道具 build_regime_label_dashboard.py）を【7-8】に書いた。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に在る（impl_file＝build_regime_label_dashboard.py）。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | 新しく作るファイルは無い（NEW_FILE は空）。手本のファイルも無い（MODEL は空）。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は 7-1 に書いた。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は 7-1 に書いた（売買に触らないので動かない）。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは 7-1 に書いた。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは 7-1 に書いた。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 変更は1つ（7-3）。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗の再演＝9/29 の控えの説明の文が、工事 A と監査 cp58 の後の事実とずれた所（日付と出どころ）を、道具で置き換えた。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 新しい部品は無い。札の部品は工事 A で作った物を呼ぶだけ。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルの行番号を指す文書は、9/29 の控え（承認していない古い控え）だけで、この工事の実装の指示の行は いまの実物から作り直した。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前と関数の名前で壊すプログラムを grep し、直す行の文字を探している物は0本だった（4-13 の4）。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラムは作らない（読むための道具＝恒久71番）。完成の条件のコマンドは⑪タブの道具そのもので、書くのは git の対象外の版の置き場だけ。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 触る関数は、全部 DESIGN_CONTRACT の impl_functions に書いた（【7-8】・下書きの道具が当てる前と後の差の行から数えた）。<モジュール直下>・check15・label_frame・main・spec_of。must_use に、main と label_frame が呼ぶ名前を書いた（下書きの道具が ast で照らした）。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足す旗は --version（4-9）。完成の条件の1行目は旗なし（既定＝all）で走らせる。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 2回目の承認の前に、実装の中で変わった手順を設計書に書き直す（その時にやる）。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 疑似シミュ由来の固定値は無い（7-2）。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の目印は設計書の1行目に在る（iter=m2f-label-dashboard-20261002）。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更・過去の失敗の不再演は、7-3 と上の9行目に書いた。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査＝付けない（恒久71番）。下書きの道具が当てた後の道具を本物に書かずに走らせ、承認の前の検査をかけた。 |

- 【群2・18件】まとめて非該当（売買のロジックにも審判にも触れないため）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［自動］条件とコマンドは まこさんが OK した案の【7-6】・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | ⑪タブの道具が、版1 の2版と版2 の全部の版（12版）を出し、版1 の数が 2026-09-28 の走行と同じ | `python3 scripts/dashboard/build_regime_label_dashboard.py` | 実経路 | 壊すプログラムは付けない（読むための道具＝恒久71番。直す前と後で版1 の数が同じかを、2026-09-28 の印字と照らす） | `—` | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=33fcf91860e71c11 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/dashboard/build_regime_label_dashboard.py`

| 触る関数 | 定義の行 |
|---|---|
| `version_tag` | （この関数は実物に無い） |
| `variants` | （この関数は実物に無い） |
| `band_hold` | （この関数は実物に無い） |
| `er_median` | （この関数は実物に無い） |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 5件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=867adf1112b108d4 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/dashboard/build_regime_label_dashboard.py",
  "_impl_file の意味": "照らす相手は実在するファイル（gen_acceptance.py:680〜683）。この工事で直すのは⑪タブの道具の1本だけ。",
  "impl_functions": {
    "scripts/dashboard/build_regime_label_dashboard.py": [
      "<モジュール直下>",
      "check15",
      "label_frame",
      "main",
      "spec_of"
    ]
  },
  "_impl_functions の意味": "この工事で触る関数。当てる前と後の差の行を、当てた後のコードの関数に当てはめて、下書きの道具（_labelC_draft_build.py）が数えた。",
  "self_check_calls": [
    "version_tag",
    "variants",
    "band_hold",
    "er_median"
  ],
  "_self_check_calls の意味": "実装の後の⑪タブの道具に在るはずの、札の部品の口の名前（版の名前・値の組・版2 の札・版1 の札）。★ファイル名を書かない＝7-7 の表が「読んだ」の行の下に並べ、必読ゲートが数えるため。",
  "must_use": {
    "main": [
      "load_window",
      "label_frame",
      "spec_of"
    ],
    "label_frame": [
      "check15"
    ]
  },
  "_must_use の意味": "main が窓を読み・札を付け・仕様を作るを呼び、label_frame が検査15 の数え方を呼ぶはず（下書きの道具が ast で照らした）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は⑪タブの道具が札を作る口と、版の名前と仕様の作り方だけを変える。外から読む一覧（候補・法則・成績表の順位・範囲の鍵）は読まない。",
  "generated_from": {
    "impl_functions": "当てる前と後の差の行（_labelC_draft_build.py が数えた）",
    "must_use": "main と label_frame が呼ぶ名前（ast で照らした）",
    "spec_lists": "空（理由＝no_spec_lists_reason）"
  }
}
```

SPEC

```json
{
 "impl_file": "scripts/dashboard/build_regime_label_dashboard.py",
 "public_functions": {
  "load_window": [],
  "check15": [],
  "label_frame": [
   "check15"
  ],
  "spec_of": [],
  "main": [
   "label_frame",
   "load_window",
   "spec_of"
  ]
 },
 "constants": {},
 "cli_flags": []
}
```

<!-- ACC_SPEC_END -->
