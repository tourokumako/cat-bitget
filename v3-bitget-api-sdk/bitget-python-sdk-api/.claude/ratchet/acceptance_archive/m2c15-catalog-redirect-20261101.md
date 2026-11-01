<!-- ARC iter="m2c15-catalog-redirect-20261101" -->

# 設計書｜161-2＝列を作る所 build_catalog を、読む口の列を作る組から列を作る形にし、列の名前・並び・値が直す前と同じかを比べる。ToDo の161番・M2-C-15

TARGET: .claude/state/indicator_review/gen_indicators_draft.py, v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py, v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py, v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py, v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
NEW_FILE: .claude/breaks/b222_catalog_drops_last_set.sh, .claude/breaks/b223_catalog_reads_old_key.sh, .claude/breaks/b224_reader_sets_no_reg.sh, .claude/breaks/b225_draft_source_is_catalog.sh, .claude/breaks/b226_h2_watch_no_indicators.sh, .claude/breaks/b227_materials_keys_from_catalog.sh
MODEL: .claude/breaks/b137_material_params_ignored.sh
工事の種類: 種類①（指標・探索・売買のロジック・設定に触る工事）（直すファイルの一覧から、プログラムが決めた）
この工事が解く問題: 列を作る所（build_catalog）は、161-1 で indicators.json に入れた列を作る組を読まず、設定ファイルの古い鍵 約40個と material_params から列を作っているので、indicators.json を直しても列に届かない。この工事（161-2）は、build_catalog を読む口の列を作る組から列を作る形にし、列の名前・並び・値が直す前と同じかを比べる。（§1 概要の1文目を、プログラムが写した）


**承認の状態＝承認の印（`.claude/state/acceptance.approved`・`design_approved.json`）が正本。****実装の状態＝7-6 の完成の条件の表（承認のプログラムが「済」を書く）が正本。**この文は状態を持ちません。

**★この設計書は、工事のフォルダ `verbatim/m2c15-catalog-redirect-20261101/` からプログラムが組み立てます。**（verbatim/ は、作業中は `.claude/state/` の下、承認の後は `SDK/.claude/ratchet/acceptance_archive/` の下に在る）CC が手で書いたのは、やることの表.md の「手書きの項目」の11つだけです＝§1 概要・この工事が結ぶ要件と、減らす違い・2-1 何を測るか・目標・3-2 決めてほしいこと・4-4 処理の流れ・4-5 止まる条件・4-8 作る物の形・4-13 影響範囲・4-19 通しの例・7-6 完成の条件。それ以外は、まこさんが OK した案の逐語（【項目の番号】の見出しで切った中身）と実物から作りました。作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-catalog-redirect-20261101 --write`。検出＝`--work m2c15-catalog-redirect-20261101 --verify`。

## 要件定義と工事の流れ（固定・毎回 載せる・消さない）

［自動］正本 .claude/rules/core_requirements.md からプログラムが写した（まこさん指示 2026-10-12）
**■ 要件定義と工事の流れ（固定・毎回 読む・消さない）**

★この文書は、まこさんが OK した要約（2026-10-18・逐語のファイル `okd_summary_20261018.txt`・OK の発言＝`ok_summary_20261018.txt`。10 だけは 2026-10-20 の `design-audit-scope-20261020/okd_summary10_20261020.txt`・OK の発言＝`ok_summary10_20261020.txt`）を、プログラムが写した物です。見出しの行と、この説明の4行だけが、プログラムの中の決まった文です。
★全文＝`.claude/rules/core_requirements_full.md`（同じプログラムが逐語のファイルから作る）。要約の中の まこさんの言葉（「」の行と、機能要件の6行）が全文に1文字も違わずに在ることを、`--verify` が照らします。
★作り直し＝`python3 .claude/tools/gen_core_requirements.py --write`。検出＝`--verify`。
★設計書・監査の依頼書・next_step の上部には、それぞれを作るプログラムが、この要約を写して載せます（いつも載せるのは 1・2・3・7・8・10。売買のロジックに触る工事では 4・5・6・9 も足します）。この文書が無い・逐語のファイルと違うときは、どのプログラムも文書を作らずに止まります。

**■ 1. CAT プロジェクトの目標**
- 本番で BOT を走らせて、全月 net ≥ $1,900 を達成する。単月で判定する。全部の採用戦略を合わせた net で見る。
- 「目標達成のため、ただ早く進めることが正解ではなく、正しく早く進めることが最善」

**■ 2. engine_tuner の目的**
- 「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的」
- 「上記目的に即していないものは作らないこと。」
- 現状の位置付け＝「現状、CCの思考を補助する機能とする」

**■ 3. engine_tuner の機能要件**
指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、Entry/Exitやレジーム判定などの条件を作る
| 1 | 指標が、承認済みのカタログに在るものから使われている
| 2 | 閾値が、範囲から探されている
| 3 | パラメータが、範囲から探されている
| 4 | 時間足が、使える時間足から指定されている
| 5 | 4つが、それぞれの役割に沿って使われている
| 6 | つなぎ方が、型の表と場面の決まりに沿っている

**■ 4. 探し方**
- 最初の段階は、パラメータと閾値を代表の固定値にして、指標・時間足・役割・つなぎ方の組を絞る。
- 最後の段階で、残った組のパラメータと閾値を、指標ごとの範囲から探す。「範囲で探せるという上記要件は絶対」
- ほかの探し方に替えない。

**■ 5. 言葉**
- 代表の固定値＝最初の段階で固定して使う値。戦略（スキャル／デイトレ）ごと・指標ごとに1つ。教科書に在ればその値、無ければ既定の値。「厳密でなくてもいい」
- 範囲＝最後の段階で探す幅。指標ごとに1つ。指標の名前に値を入れて指標を増やさない。
- 教科書＝指標のパラメータ・閾値・役割・計算の出どころの資料（資料の表3つ）。
- 法則＝相場から見つけた知識を文で書いた物（regime_detection_kb.md §11）。「法則があるからロジックって言われてるんだけど。」

**■ 6. 指標と、教科書と法則の扱い**
- 指標は、指標一覧（material）からだけ呼び出す。オン・オフは全部のロジックに効く。
- 教科書と法則は完璧ではない前提で作る。誤りは置き場の1か所を直せば済み、直した物が全部のロジックに届く作りにする。

**■ 7. 作ってはいけないもの**
1. ランダムに条件をつなぐだけのもの。
2. 探す値を、CC が先に決まった数字の一覧で限定するもの。

**■ 8. 設計書と監査で確かめること**
- その設計のとおりに作ると、net 利益を最大にするロジックを見つける力が上がるか。少なくとも、損なわないか。
- 文字や手順が合っているかは、その手前の確かめ。

**■ 9. 工事の流れ**
| 1 | 設計書の元を作る（読む・案・まこさんの OK） | 私 → まこさん |
| 2 | 設計書を作る | プログラム |
| 3 | 設計書の監査（設計の中身が正しいか） | 監査 |
| 4 | 設計書の監査結果の確認（直す範囲を決める） | まこさん |
| 5 | 設計書の修正（監査が書いた修正を入れる） | プログラム |
| 6 | 承認 | まこさん |
| 7 | 実装（承認した設計書から書き込む） | プログラム |
| 8 | 実装の監査（設計書のとおりか） | 監査 |
| 9 | 実装の監査結果の確認（直す範囲を決める） | まこさん |
| 10 | 実装の修正（監査が書いた修正を入れる） | プログラム |
- 設計の誤りは 3〜5 で全部 出して直す。8 で見るのは「設計書のとおりか」だけ。

**■ 10. 設計書の監査が要る物**
- 売買のロジック・材料（指標）・法則・設定（scripts/priority_rebuild の .py と設定ファイル）を直す工事＝要る。
- インフラ（.claude/hooks・.claude/tools・文書を作るプログラム）を直す工事＝要らない。直した後の監査も要らない。
- インフラの工事も、宣言に規模を書く。応相談にするかは、まこさんが決める。
- 検査・問い・止める条件を外す、または緩める直しは、直す前に、消す行を まこさんに見ていただく。

### 0-R 要件定義の索引（要件定義の何番を、この設計書のどの節に書いたか）

［自動］要件は正本から。書いた節と、その節の状態は、プログラムがこの設計書の中身から決めた（CC は判定を書かない）
| # | 要件（正本から） | 書いた節と、その節の状態 |
|---|---|---|
| 1 | CAT プロジェクトの目標 | 3-0 目標の③＝書いた |
| 2 | engine_tuner の目的 | 3-0 目標の①＝書いた |
| 3-1 | 指標が、承認済みのカタログに在るものから使われている | 4-7＝書いた |
| 3-2 | 閾値が、範囲から探されている | 4-7＝書いた |
| 3-3 | パラメータが、範囲から探されている | 4-7＝書いた |
| 3-4 | 時間足が、使える時間足から指定されている | 4-7＝書いた |
| 3-5 | 4つが、それぞれの役割に沿って使われている | 4-7＝書いた |
| 3-6 | つなぎ方が、型の表と場面の決まりに沿っている | 4-4＝書いた／4-6＝書いた |
| 4 | 探し方（段階を追って絞る） | 4-7＝書いた |
| 5 | 言葉の定義 | 4-8＝非該当（一覧に種類「作る」の行が無い（F-1〜F-6 は、どれも在るファイルを直す）。読む口の column_sets の返り値に足す欄（登録の名前）は、F-2 と 4-19 に書いた。）／4-9＝書いた |
| 6 | 指標の使い方 | 4-3＝書いた／4-13＝書いた |
| 7 | 教科書と法則の扱い（前提） | 4-10＝書いた／4-23＝書いた |
| 8-1 | ランダムに条件をつなぐだけのもの。 | 7-3b＝書いた |
| 8-2 | 探す値を、CC が先に決まった数字の一覧で限定するもの。 | 7-3b＝書いた／4-21＝書いた |
| 9 | 設計書と監査で確かめること（★この節は私の言葉です） | 3-0 目標の①＝書いた／3-0 目標の⑤＝書いた／3-0 目標の⑥＝書いた |
| 10 | いまの実物との違い（今後 直す物・今日 実物で確かめた分だけ） | 2-0＝書いた |

**見出しの直下の印＝［手書き］＝CC が やることの表.md の「手書きの項目」に書いた文／［自動］＝プログラムが、まこさんが OK した案の逐語と実物から作った。**

## 1｜概要

［手書き］やることの表の「§1 概要」
列を作る所（build_catalog）は、161-1 で indicators.json に入れた列を作る組を読まず、設定ファイルの古い鍵 約40個と material_params から列を作っているので、indicators.json を直しても列に届かない。この工事（161-2）は、build_catalog を読む口の列を作る組から列を作る形にし、列の名前・並び・値が直す前と同じかを比べる。

#### 目的
- CAT の目標は、本番で全月 net ≥ $1,900 を達成することです（core_requirements_full.md:13）。engine_tuner の目的は、「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ること」です（:19）。
- 指標は、指標一覧（material）からだけ呼び出します（:85）。指標一覧は、指標を計算する、ただ1つの置き場で、Entry・Exit・場面の判定は全部ここから指標を呼び出します（:81）。工事の後は、読む口 indicators.py が指標一覧に当たります（集約の要件定義書 §5・:49）。
- 誤りは置き場の1か所を直せば済み、直した物が全部のロジックに届く作りにします（core_requirements_full.md:95〜96）。
- この工事の目的は、集約の要件定義書の R6「列を作る所（build_catalog）は、記録のパラメータだけから列を作る。古い鍵33個は読まない」（:144）のうち、「記録から作る・古い鍵を読まない」を満たすことです。

#### 経緯
- 2026-10-24 に、修正の5つに まこさんの OK をいただきました（okd_plan5_20261024.txt）。「3.」に「列を作る所（build_catalog）は、記録のパラメータだけから列を作ります。古い鍵33個は読みません。」と在ります（集約の要件定義書:85）。同じ日に、直す前の列の控えを作りました（col_snapshot/before_20261024.json・名前652・列7148本・3637秒）。
- 2026-10-31 に、161番を2本に分けました（まこさん「分けて良い」・ok_split_161_20261031.txt）。理由は、1本の設計書だと、当てた直後の indicators.json がまだ古い形で、承認の前の検査が走らせる観察の道具の自己テストが落ちるためです（worklog 20261031:495）。
- 2026-11-01 に、161-1 を commit しました（b6d0d468）。indicators.json は新しい形になり、列を作る組（②-12・④-9）が314記録・652組で入りました。実装の監査 CP95 の修正10・11・17・18 は当てていません（まこさん「１は当てない」・worklog 20261101 §6-2）。
- 2026-11-01 に、161-2 の読むもの宣言（40件）と工事名に まこさんの OK をいただきました（worklog 20261101 §8）。読む中で、写すプログラムの写す元が build_catalog であること（gen_indicators_draft.py:973）・H2 の印の対象に indicators/ の2本が無いこと（leak_causality_diag.py:244〜263）・gen_materials が build_catalog の設定の鍵を数えていること（gen_materials.py:454〜478）を見つけました（worklog 20261101 §9）。
- 10-24 の控えの後に、計算が変わったかを確かめました。observe_diag.py の変更は commit d2fb0f39 の注記1行だけ、indicator_reference_diag.py の変更は commit ca445bd3 の説明の文だけで、5分足の CSV は 2026-07-23 から変わっていません（git log・git show・stat）。

#### ゴール
- 工事全体（ゴール1〜3）のゴール＝指標の情報が1つのデータにあり、そこからしか取れない。engine_tuner は、最初の段階で代表の値を、最後の段階で範囲を、そのデータから読む（指標の構造の要件定義書 第1章）。
- この設計書のゴール＝build_catalog が、読む口の列を作る組から列を作り、設定の古い鍵・material_params・drop_columns を読まない。列の名前・並び・値が、直す前の控えと1本も違わない（col_snapshot.py --compare＝控えに在って今に無い列 0・今にだけ在る列 0・値が違う列 0・名前の並び 同じ）。写すプログラムの --verify が「違い 0 件」のまま。H2 の印が indicators.json と読む口を見張る。
- この設計書では届かない所＝パラメータの軸の代表の値と範囲から列を作る形（171番・M2-E-8）・engine_tuner の経路の7本の向け直し（171番）・残りの24本（170番）・元の置き場と写す元の関数を消す（162番）・閾値と代表の値を写す（70番）。

#### 範囲
- 入れる物＝一覧の F-1〜F-6。出どころ＝161番の決まった中身（worklog 20261030:1308）・161-1 の Y-17・Y-18・4-13 の :232。
- 外す物＝この表の Y-1〜Y-13。

### 1-1 この工事でやること（結論）

［自動］やることの表の「## 一覧」の種類・直すファイル・番号から、プログラムが作った
- 直す：v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py（F-1・F-3）
- 直す：v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py（F-2）
- 直す：.claude/state/indicator_review/gen_indicators_draft.py（F-4）
- 直す：v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py（F-5）
- 直す：v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py（F-6）

## 2｜背景と範囲

### 2-0 この工事が結ぶ要件と、減らす違い

［自動］やることの番号と結ぶ要件＝読むもの宣言から、プログラムが写した
- やることの番号＝M2-C-15
- 結ぶ要件＝M2-C-15＝この工事が満たす要件は、要件定義の次の3つです。3番：指標・閾値・パラメータ・時間足が、それぞれの役割に沿って使われ、閾値とパラメータが範囲から探されていること。4番と5番：最初の段階では、閾値とパラメータを、戦略ごとの代表の固定値にして探すこと。6番：指標は1か所から呼び出すこと。教科書と法則の誤りは、1か所を直せば全部に届くこと。（出どころ＝やることリスト m2_todo.json の「結ぶ要件」）

［手書き］やることの表の「この工事が結ぶ要件と、減らす違い」
| 欄 | 中身 |
|---|---|
| 要件定義の「いまの実物との違い」のどの行か | 「指標は指標一覧からだけ呼び出す（6）／E38 の11本と、売買を回すプログラムに、自前の計算が在る」（core_requirements_full.md:112） |
| その違いを、どこまで減らすか | 減るのは、列を作る所が指標一覧に当たる読む口から列の組を読むこと。この工事の後も、E38 と売買を回すプログラムの自前の計算は残る（171番）。列を作る所の写す元の関数（設定の古い鍵を読む）は、162番まで写すプログラムのために残る |
| 順番（要件定義の6番「指標を完璧に修正しきってから、M2へ戻す」） | この工事は、指標の修正の残り（70番）より前の工事です。M2 へ戻る前の工事です |

### 2-0b やることの一覧

［自動］やることの表の「## 一覧」から、プログラムが写した
| 番号 | 一文 | 種類 | 直すファイル | 直す所 | 直す前 | 直し方 | 出どころ |
|---|---|---|---|---|---|---|---|
| F-1 | 列を作る所（build_catalog）を、読む口が返す列を作る組から列を作る形にする | 直す | v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py | :1792〜2229（def build_catalog）・:7812〜7943（selftest_catalog＝カタログの自己テスト） | 設定の鍵ごとの for で列を作る。cfg[ で鍵を読む行が71行（古い鍵 約40個・atr_periods 7回ほか）。material_params に在る種類はその組で作り（:1806〜1817）、帯の8種は _band_material に床を渡して作り（:1964〜1980）、最後に drop_columns で列を省く（:2220〜2228）。読む口の column_sets を呼ぶ行は0 | 読む口（indicators.load().column_sets()）が返す組を、並びの順に1つずつ列にする。指標の記録の組は make_material（登録の名前, 組）で、部品の記録の組は _band_material（登録の名前, 床, 組）で作る。床は、いまと同じく渡された設定の band_fee_mult から作る（_band_fee_floor(cfg)・:1964）。設定の古い鍵・material_params・drop_columns は読まない（R6）。列を作る組は、drop_columns で省いた後のいまのカタログから写した物（gen_indicators_draft.py:970〜988）なので、省く処理は要らない。列の名前と並びと値は、直す前と同じにする。カタログの自己テストに照らしを2つ足す＝①build_catalog の名前の並びが、写す元の関数（F-3）の名前の並びと1本も違わない ②build_catalog の構文の木に、cfg の鍵を読む所（cfg[...]・cfg.get(...)）が無い | 161番の決まった中身（worklog 20261030:1308）・161-1 の Y-17・集約の要件定義書 R6（:144）・okd_plan5 の「3.」（集約の要件定義書:85） |
| F-2 | 読む口の column_sets が、組ごとに計算の登録の名前も返す | 直す | v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py | :335〜360（def column_sets）・:28（使い方の説明）・自己テスト（:521〜535 の列を作る組の行） | 組ごとに {記録・種類・名前の型・組・並び} を返す（:352）。計算の登録の名前は返さない。記録の名前と計算の登録の名前は、組を持つ記録のうち54記録で違う（全記録では56記録）（例＝ALMA傾き% の登録は ALMA傾き・jq 2026-11-01） | 組ごとの返り値に「登録の名前」を足す。値は、その記録の計算の関数の要素（指標の記録＝②-2・部品の記録＝④-3・要素の名前は番号から引く＝決まり①）の「登録の名前」。組を持つのに登録の名前が無い記録が在れば止まる（いまは0記録＝組を持たない13記録は組が空・jq 2026-11-01）。自己テストに、登録の名前を返す行と、無ければ止まる行を足す | 161-1 の F-1（「build_catalog に、作る列の組を渡す口を持つ」）・決まり① |
| F-3 | いまの build_catalog の中身を、写すプログラムの写す元として、別の名前の関数に残す（162番で消す） | 直す | v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py | :1792〜2229 の中身（F-1 で置き替える前の文字の全部） | build_catalog 1つが、列を作る所と、写すプログラムの写す元の両方を兼ねる（gen_indicators_draft.py:592・:973 が build_catalog を呼ぶ） | いまの中身を1文字も変えずに、別の名前の関数（_catalog_from_config(cfg)）として残す。呼ぶのは写すプログラム（F-4）と、観察の道具のカタログの自己テスト（F-1 の名前の並びの照らし）と、gen_materials の鍵を拾う口（F-6）だけにする。この形にする理由＝F-1 の後に build_catalog を写す元にすると、写す元が indicators.json 自身になり、設定の鍵を直しても列に届かず、写すプログラムの --verify は自分と比べることになる。写す元を残せば、161-1 で決まった「162番までは写す元で直して、写すプログラムで作り直す」（修正14 案B）を変えずに済む。この形が正しいかは、設計書の監査で問う（まこさん「よい」2026-11-01＝技術のやり方は CC が決め、監査で確かめる・恒久49番） | 修正14 案B（161-1 の やることの表 F-2＝「162番で写す元を消すまでは、新しい形でも、値を写す元で直してこの口で作り直す」）・Y-3 |
| F-4 | 写すプログラムが、列を作る組と出どころの鍵を、F-3 の写す元の関数から作る | 直す | .claude/state/indicator_review/gen_indicators_draft.py | :590〜606（build_old の cols）・:970〜988（catalog_sets）・:835〜838（table_update）・:128（PART_SRC）・:16（頭の説明）・自己テスト（:1557〜） | 列を作る組（②-12・④-9）を od.build_catalog の出力から作る（:973〜984）。出どころの鍵も、build_catalog に渡す設定の鍵を1つずつ空にして決める（:590〜606）。F-1 の後に build_catalog を呼ぶと、写す元が indicators.json 自身になり、--verify（:1421）と --rewrite（:1474）が自分と比べることになる。indicators.json の要素の定義表の ②-12・④-9 は「写す元＝…（observe_diag.build_catalog）」「読むプログラム＝空」で（indicators.json:283〜303）、部品の記録8件の出どころは「build_catalog の帯の for」（PART_SRC）。どれも F-1・F-3 の後は事実と違う文になる | od.build_catalog の呼び出し2か所を、F-3 の関数（od._catalog_from_config）に替える。table_update に、②-12・④-9 の「写す元」を _catalog_from_config に、「読むプログラム」に build_catalog を書く行を足す（②-9・③-5 の写す元を合わせる :835〜838 と同じ形）。PART_SRC と頭の説明の文も _catalog_from_config に合わせる。当てた後に --rewrite を1回 走らせ、indicators.json の10か所（②-12・④-9 の写す元の2か所と部品の記録8件の出どころ）を作り直す（4-4 の3）。自己テストに、cols と catalog_sets が build_catalog を呼んでいないことを構文の木で照らす行を足す | 前の返信の1つ目の見つけた所（worklog 20261101 §9）・修正14 案B |
| F-5 | H2 の印の対象に、読む口と1つのデータを足す | 直す | v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py | :244〜263（WATCHED） | 対象に indicators/indicators.json と indicators/indicators.py が無い（grep -c で 0）。F-1 の後は、engine_tuner の経路の build_catalog がこの2本を読むので、indicators.json を直しても H2 の印が変わらない | WATCHED に2本（f"{_PR}/indicators/indicators.json"・f"{_PR}/indicators/indicators.py"）を足す。理由の注記に「build_catalog が読む（161-2）」と書く | 前の返信の2つ目の見つけた所・leak_causality_diag.py:253〜255（observe_diag.py を足したときと同じ理由） |
| F-6 | gen_materials の「設定の鍵を読む所」の数え方を、F-3 の写す元の関数に向ける | 直す | v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py | :454〜478（_catalog_keys）・:2477〜2480（自己テスト T12 の書き替え） | build_catalog の中で cfg から読む鍵を数え、materials.md の「決まった数字だけの並び」の場所1 に使う。F-1 の後は build_catalog が cfg の鍵を読まない（床は _band_fee_floor(cfg) に cfg を渡すだけ）ので、場所1 が黙って0本になる | 数える相手の関数の名前を、build_catalog から F-3 の関数に替える（:465 と、関数の説明の :455・T12 の :2478〜2480）。設定の鍵の数（場所1）は、直す前と同じになる。materials.md に入る説明の文（:1588）は直さない（Y-13） | 前の返信の3つ目の見つけた所 |

### 2-1 いまの状態（走らせて測ったもの）

［手書き］何を測ったか・コマンド・読み方＝やることの表の「2-1 何を測るか」
［自動］結果＝道具がコマンドを走らせて入れた
| 何を測ったか | コマンド | 読み方 | 結果 |
|---|---|---|---|
| build_catalog が、設定の鍵を読んで列を作る | `awk '/^def build_catalog/{f=1} /^def _catalog_from_config/{f=0} /^# ══ 指標の組み立て/{f=0} f{if(/cfg\[/)n++} END{print n+0}' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 直す前は、設定の鍵を読む行の数が出る（ゼロでない）。直した後は、ゼロになる（床の倍数は _band_fee_floor(cfg) に cfg を渡すだけで、cfg[ の行を持たない）。直した後は build_catalog のすぐ後に写す元の関数 _catalog_from_config が来るので、その def の行で数えるのを止め、写す元の関数の中の cfg[ は数えない | 71（終了コード 0） |
| build_catalog が、読む口の列を作る組を読まない | `awk '/^def build_catalog/{f=1} /^def _catalog_from_config/{f=0} /^# ══ 指標の組み立て/{f=0} f{if(/column_sets/)n++} END{print n+0}' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py` | 直す前は、ゼロ。直した後は、ゼロでない（build_catalog が column_sets を呼ぶ） | 0（終了コード 0） |
| H2 の印が、読む口と1つのデータを見張らない | `grep -c "indicators/indicators" v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py` | 直す前は、ゼロ。直した後は、ゼロでない（WATCHED に indicators.json と indicators.py の行が在る） | 0（終了コード 1） |

### 2-2 探す材料（印がオンのもの・プログラムが正本から出しました）

［自動］印のファイル・型の表・格子と範囲
<!-- ACC_MATERIALS_START hash=9851f098568d0cf1 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`indicator_switch.json`・`signal_families.json`・`search_limits.json`。

**この工事が関わる指標＝0種**（案の【4-7】の文に名前が在る物。印がオンの指標は、全部で 185種）。

```

```

**別枠の材料**

| 別枠 | 印がオンのもの |
|---|---|
| レンジ幾何 | W%・下半分位置・帯内位置% |
| 需給 | CVD・L-S比・taker_ls |
| 時間帯 | 時刻・曜日 |

**役割ごとに使える系統と時間足（型の表）**

| 役割 | 系統 | 時間足 | レンジ幾何 |
|---|---|---|---|
| env | トレンド・ボラ・時間帯・強さ・勢い | 全部 | — |
| location | 構造・位置 | 全部 | 使う |
| sufficiency | ボラ・出来高・需給・オシレーター・強さ | 全部 | — |
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
| `material_param_ranges` | {"ADX": [{"kind": "int", "lo": 7, "hi": 21}], "DI差": [{"kind": "int", "lo": 7, "hi": 21}], "MACD線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}], "MACDヒスト%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "MACDシグナル線%": [{"kind": "int", "lo": 3, "hi": 12}, {"kind": "int", "lo": 10, "hi": 26}, {"kind": "int", "lo": 1, "hi": 9}], "転換線": [{"kind": "int", "lo": 5, "hi": 12}], "基準線": [{"kind": "int", "lo": 13, "hi": 26}], "EMA傾き": [{"kind": "int", "lo": 9, "hi": 200}], "KSTシグナル": [{"kind": "int", "lo": 9, "hi": 9}], "PPO": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOシグナル": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "PPOヒスト": [{"kind": "int", "lo": 12, "hi": 12}, {"kind": "int", "lo": 26, "hi": 26}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIXヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TSI": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIシグナル": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "TSIヒスト": [{"kind": "int", "lo": 4, "hi": 13}, {"kind": "int", "lo": 7, "hi": 26}, {"kind": "int", "lo": 7, "hi": 12}], "KAMA傾き%": [{"kind": "int", "lo": 7, "hi": 10}], "WMA傾き%": [{"kind": "int", "lo": 20, "hi": 200}], "AROONU": [{"kind": "int", "lo": 7, "hi": 288}], "AROOND": [{"kind": "int", "lo": 7, "hi": 25}], "AROONOSC": [{"kind": "int", "lo": 7, "hi": 25}], "VTXP": [{"kind": "int", "lo": 14, "hi": 30}], "VTXM": [{"kind": "int", "lo": 14, "hi": 30}], "RSI": [{"kind": "int", "lo": 2, "hi": 21}], "ROC": [{"kind": "int", "lo": 9, "hi": 24}], "Stoch%K": [{"kind": "int", "lo": 5, "hi": 21}], "Stoch%D": [{"kind": "int", "lo": 5, "hi": 21}], "MFI": [{"kind": "int", "lo": 10, "hi": 20}], "CMF": [{"kind": "int", "lo": 20, "hi": 36}], "OBV傾き": [{"kind": "int", "lo": 10, "hi": 20}], "BB%b": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "volume_ratio": [{"kind": "int", "lo": 20, "hi": 50}], "CCI": [{"kind": "int", "lo": 7, "hi": 21}], "PVO": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOシグナル": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "PVOヒスト": [{"kind": "int", "lo": 8, "hi": 12}, {"kind": "int", "lo": 18, "hi": 26}, {"kind": "int", "lo": 5, "hi": 9}], "StochRSI%K": [{"kind": "int", "lo": 7, "hi": 21}], "StochRSI%D": [{"kind": "int", "lo": 7, "hi": 21}], "DPO%": [{"kind": "int", "lo": 14, "hi": 40}], "EFI比": [{"kind": "int", "lo": 10, "hi": 20}], "EOM比": [{"kind": "int", "lo": 10, "hi": 20}], "NVI傾き": [{"kind": "int", "lo": 10, "hi": 20}], "PVT傾き": [{"kind": "int", "lo": 10, "hi": 20}], "ATR%": [{"kind": "int", "lo": 5, "hi": 21}], "BB幅": [{"kind": "int", "lo": 10, "hi": 50}, {"kind": "float", "lo": 1.9, "hi": 2.1, "dec": 1}], "realized_vol": [{"kind": "int", "lo": 10, "hi": 50}], "Donchian幅": [{"kind": "int", "lo": 10, "hi": 20}], "MMI": [{"kind": "int", "lo": 200, "hi": 500}], "ER": [{"kind": "int", "lo": 7, "hi": 21}], "CHOP": [{"kind": "int", "lo": 7, "hi": 21}], "VHF": [{"kind": "int", "lo": 7, "hi": 28}], "MAD比": [{"kind": "int", "lo": 20, "hi": 50}], "stdev%": [{"kind": "int", "lo": 10, "hi": 50}], "UI": [{"kind": "int", "lo": 7, "hi": 21}], "高値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "安値からの経過バー": [{"kind": "int", "lo": 9, "hi": 288}], "形スコア": [{"kind": "int", "lo": 24, "hi": 96}], "W字": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}], "fractal高値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "fractal安値距離%": [{"kind": "int", "lo": 2, "hi": 3}], "高値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "安値切り上げ幅%": [{"kind": "int", "lo": 2, "hi": 3}], "構造破断距離%": [{"kind": "int", "lo": 2, "hi": 3}], "close vs EMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs SMA": [{"kind": "int", "lo": 5, "hi": 60}], "close vs VWAP": [{"kind": "int", "lo": 288, "hi": 288}], "Keltner上": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "Keltner下": [{"kind": "int", "lo": 20, "hi": 20}, {"kind": "float", "lo": 1.0, "hi": 3.0, "dec": 1}], "n本高値": [{"kind": "int", "lo": 10, "hi": 50}], "n本安値": [{"kind": "int", "lo": 10, "hi": 50}], "pivotPP": [{"kind": "int", "lo": 288, "hi": 288}], "pivotR1": [{"kind": "int", "lo": 288, "hi": 288}], "pivotS1": [{"kind": "int", "lo": 288, "hi": 288}], "fib位置": [{"kind": "int", "lo": 14, "hi": 96}], "S-Rタッチ1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "S-Rタッチ数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "close vs ALMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs DEMA%": [{"kind": "int", "lo": 9, "hi": 200}], "close vs FWMA%": [{"kind": "int", "lo": 10, "hi": 20}], "close vs HMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs JMA%": [{"kind": "int", "lo": 3, "hi": 80}], "close vs KAMA%": [{"kind": "int", "lo": 7, "hi": 30}], "close vs LINREG%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs LRb%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs MCGD%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs MIDPOINT%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MIDPRICE%": [{"kind": "int", "lo": 2, "hi": 200}], "close vs MMAR%": [{"kind": "int", "lo": 10, "hi": 35}], "close vs PWMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs RAINBOW%": [{"kind": "int", "lo": 2, "hi": 2}, {"kind": "int", "lo": 1, "hi": 10}], "close vs RMA%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SINWMA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs SSF%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs SWMA%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs T3%": [{"kind": "int", "lo": 8, "hi": 200}], "close vs TEMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TRIMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs TSF%": [{"kind": "int", "lo": 4, "hi": 200}], "close vs VIDYA%": [{"kind": "int", "lo": 14, "hi": 200}], "close vs VWMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs WMA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs MEDIAN%": [{"kind": "int", "lo": 4, "hi": 200}], "RCI": [{"kind": "int", "lo": 5, "hi": 52}], "close vs VWAP典型": [{"kind": "int", "lo": 288, "hi": 288}], "W字確定谷": [{"kind": "int", "lo": 24, "hi": 96}, {"kind": "float", "lo": 0.0, "hi": 0.06, "dec": 3}], "S-Rタッチ確定数": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.0015, "hi": 0.006, "dec": 4}], "S-Rタッチ確定1時間ATR": [{"kind": "int", "lo": 144, "hi": 288}, {"kind": "float", "lo": 0.5, "hi": 1.5, "dec": 1}, {"kind": "int", "lo": 7, "hi": 21}], "DPO教科書%": [{"kind": "int", "lo": 14, "hi": 40}], "StochRSI素%K": [{"kind": "int", "lo": 7, "hi": 21}], "TRIX_EMAシグナル": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "TRIX_EMAヒスト": [{"kind": "int", "lo": 7, "hi": 21}, {"kind": "int", "lo": 9, "hi": 9}], "realized_vol_rv": [{"kind": "int", "lo": 10, "hi": 50}], "close vs SSF平均%": [{"kind": "int", "lo": 10, "hi": 200}], "close vs TRIMA_TA%": [{"kind": "int", "lo": 1, "hi": 200}], "close vs VIDYA_CMO%": [{"kind": "int", "lo": 20, "hi": 200}]} |

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

### 3-0 目標

［手書き］やることの表の「目標」（①は、プログラムが、結ぶ要件と「その違いを、どこまで減らすか」から写した）
| 番号 | 欄 | 中身 |
|---|---|---|
| ① | どの要件のためか | M2-C-15＝この工事が満たす要件は、要件定義の次の3つです。3番：指標・閾値・パラメータ・時間足が、それぞれの役割に沿って使われ、閾値とパラメータが範囲から探されていること。4番と5番：最初の段階では、閾値とパラメータを、戦略ごとの代表の固定値にして探すこと。6番：指標は1か所から呼び出すこと。教科書と法則の誤りは、1か所を直せば全部に届くこと。（出どころ＝やることリスト m2_todo.json の「結ぶ要件」）。その要件との違いを、どこまで減らすか＝減るのは、列を作る所が指標一覧に当たる読む口から列の組を読むこと。この工事の後も、E38 と売買を回すプログラムの自前の計算は残る（171番）。列を作る所の写す元の関数（設定の古い鍵を読む）は、162番まで写すプログラムのために残る |
| ② | 何が出来るようになるか | 直す前は、build_catalog が設定の鍵（cfg[ の行 71）から列を作り、読む口の列を作る組を読まず（column_sets の行 0）、H2 の印が indicators.json を見張らない（2-1 の3行）。直した後は、build_catalog が読む口の列を作る組から同じ列を作り、indicators.json の列を作る組を直せば列に届く（7-6 の F-1・F-2・F-5 と、4-4 の5 の列の比べ） |
| ③ | net までのつながり | この工事の出力（読む口から列を作る build_catalog）を次に使うのは、171番（engine_tuner の経路の7本を読む口へ向け直す）→ M2-E-8（最初の段階は代表の値・最後の段階は範囲）→ M2-D-8（成績表の作り直し）。net を直に測らない段なので、途中で測る数字＝列の比べの4つ（控えに在って今に無い列・今にだけ在る列・値が違う列の数と、名前の並び。python3 .claude/state/indicator_review/col_snapshot.py --compare .claude/state/indicator_review/col_snapshot/before_20261024.json で出す。全部 0 と「同じ」なら、engine_tuner が使う材料は直す前と同じ） |
| ④ | 無駄だったと分かる物 | 171番で列をパラメータの軸の代表の値から作る形にしたときに、読む口の column_sets を呼ぶ所を数える（grep -rn 'column_sets' v3-bitget-api-sdk/bitget-python-sdk-api/scripts）。build_catalog のほかに呼ぶ所が無く、build_catalog も呼ばなくなれば、column_sets と②-12・④-9 と F-2 の登録の名前は要らなくなる（161-1 の目標④と同じ） |
| ⑤ | 済んだ直後に、②を何で確かめるか | 7-6 のコマンド（観察の道具の --selftest-catalog・読む口の --selftest・写すプログラムの --selftest・gen_materials の --selftest・grep）。当てた後は、写すプログラムの --verify と、列の比べ（4-4 の3・5） |
| ⑥ | この工事が損なう恐れのある要件 | 要件6（オン/オフが全部に効く）＝損なわない。根拠＝build_catalog は、いまと同じくオフの種類の列も作り（列を作る組はオフの121記録（組を持つのは111記録）の250組を持つ＝indicators.py:337〜338）、engine_tuner は、いまと同じく indicator_switch.json で外す（engine_tuner_gen.py:219・:277）。要件3（パラメータが範囲から探されている）＝損なわない。列の名前が同じなので、engine_tuner が列の数字から作る範囲（engine_tuner_gen.py:286〜293）も同じ（列の比べで名前の並びが同じことを確かめる）。作ってはいけない物2（数字の一覧で限定する）＝新しく限定しない。列を作る組は点の一覧だが、いまのカタログの列をそのまま写した物で、171番まで列を変えないための物（Y-4） |

### 3-1 やらないこと（1件ずつ・理由と出どころ）

［自動］やることの表の「## やらないこと」の表から、同じ件数で、プログラムが写した
| # | やらないこと | 理由 | 出どころ |
|---|---|---|---|
| 1 | engine_tuner の経路の7本（observe_diag.py のほかの関数・engine_tuner_exec.py・engine_tuner_gen.py・indicator_reference_diag.py・e38.py・e38_logic_parts.py・enforce_g2_pass.py）を、読む口へ向け直さない | 171番で行う。列の名前と並びは変わらないので、7本はいまのまま build_catalog の名前を読める（engine_tuner_gen.py:211・:268） | ToDo の171番・まこさん 2026-10-25「ok」 |
| 2 | 残りの道具・採点・診断の24本を、読む口へ向け直さない（F-4・F-6 を除く） | 170番で行う | ToDo の170番 |
| 3 | 元の置き場を消さない（observe_config.json の古い鍵・material_params・drop_columns・F-3 の写す元の関数・INDICATOR_TABLE・_reg の名前と型・search_limits.json の範囲・indicator_switch.json） | 162番で行う。161-2 の後も、写すプログラム（gen_indicators_draft.py:549〜550）・engine_tuner_exec・gen_materials・check_indicator_sources がこれらを読む | ToDo の162番・161-1 の Y-3 |
| 4 | 列の名前・並び・値を変えない。パラメータの軸（②-4）の代表の値と範囲から列を作る形にしない | 列を作る組（②-12・④-9）は、171番まで列を変えないための写し（161-1 の目標④・Y-4）。集約の要件定義書 R6 の「記録のパラメータだけから列を作る」のうち、161-2 で満たすのは「古い鍵を読まない・記録から作る」まで。代表の値から作るのは171番と M2-E-8 | 161-1 の やることの表 Y-4・目標④・core_requirements_full.md:55 |
| 5 | build_catalog から、読む口の計算の口（calc）を呼ばない。計算の本体は、いまと同じく make_material と _band_material が計算の登録（MATERIAL_FAMILIES）から取る | calc はオフの指標の計算を返さない（indicators.py:311〜312）。列を作る組は、オフの121記録（組を持つのは111記録）の250組も持つ（jq 2026-11-01・indicators.py:337〜338）。calc が返す関数と make_material が使う関数は、同じ計算の登録の同じ行（indicators.py:301〜306・observe_diag.py:1060）。calc は観察の道具を import し直す（indicators.py:73〜87）ので、観察の道具を __main__ で走らせたとき（python3 observe_diag.py --selftest-catalog）と gen_signal_families.py:55〜57 が spec_from_file_location で読み込んだときに、build_catalog から calc を呼ぶと観察の道具が2重に読み込まれる（MATERIAL_FAMILIES が別の辞書になる）。また、calc が返す帯の計算式は床を設定ファイルから読む（observe_diag.py:731〜740）ので、CP83 の修正14 案B「渡した設定の床を部品へ結び付ける」は _band_material（:793〜797）でしか守れない。★161-1 の 4-13 の :232「計算の口（calc）を、読む口から読む」とは違う。この違いが正しいかは、設計書の監査で問う（まこさん「よい」2026-11-01＝技術のやり方は CC が決め、監査で確かめる・恒久49番） | indicators.py:301〜324・observe_diag.py:1051〜1065・161-1 の やることの表:232 |
| 6 | 監査の前の検査の指紋（.claude/tools/pre_audit_check.py:108〜122 の FINGERPRINT_FILES と :213〜215 の materials_fingerprint）に indicators/ の2本を足す直しを、この設計書に入れない | インフラの直し（2026-10-20 の決定の2＝.claude/tools は設計書と監査が要らない）。実装の後、監査に出す前のチェック（4-4 の6）の前に、規模を宣言して直す（同じ決定の3）。足すだけで、検査を外す・緩める直しではない | core_requirements_full.md:156〜157 |
| 7 | 閉じた工事の壊すプログラム b137（observe_diag.py:1811 を壊す）と b128（:1823 を壊す）を直さない・消さない | 2つの工事（m2c15-param-values-20261006・m2c15-indicator-six-items-20261004）は閉じている。F-3 で壊す相手の行が写す元の関数へ移る。照らし⑮が写す元の関数を呼ぶので、b137 は写す元の関数の SystemExit「指標ごとの一覧 material_params の種類が…」で落ち（期待の文と同じ）、b128 は⑮の「名前の並びが、写す元の関数と違う」で落ちる（期待の文「❌ K-1:」とは違う＝古い壊すプログラム）。承認で走るのは設計書の表の壊すプログラムだけ（run_breaks.py --design）なので止まらない（前提が変わる＝4-13）。消すのは守りを外す直し。161-2 の守りは、7-6 の新しい壊すプログラムで作る | 161-1 の Y-14 と同じ扱い・2026-10-20 の決定の4 |
| 8 | 161-1 で決まった、隠れた数字の軸の代表の値の分け方を変えない。分け方は、CP95 の修正10 の案B の文＝「合わない軸は「まだ決めていない」にし、合わない値の一覧を画面に出す（対応を決めるのは70番の T-3）。隠れた数字の軸は、資料の表に合わない値が在る記録では「まだ決めていない」にし、資料の表に当てる値が無い記録では、いまの値（要件5 の②＝既定の値・F-3）を代表の値にする」 | 161-2 は列を作る所だけを直し、パラメータの軸の値は写し直さない。この文は、161-1 の やることの表 F-2（:20）の文が実装と違う所を、正しく書いた物（修正10 は当てなかった＝まこさん「１は当てない」2026-11-01）。対応を決めて写すのは70番の T-3 | CP95 の結果:518・next_step.md:54・worklog 20261101 §6-2 |
| 9 | RVGI({},4) の「4」のような名前の型に在る固定の数字と、登録の外の定数（band_fee_mult・_SR_ATR_TOL_LO・_SR_ATR_TOL_HI）を、パラメータの軸にしない | 軸にするのは171番と70番の T-3（161-1 の 4-13 の :232・CP91 の修正13）。161-2 は列を変えない | 161-1 の やることの表:232 |
| 10 | 閾値の値・範囲・代表の値を、新しく調べて埋めない | 70番（T-2・T-3）で行う | ToDo の70番・集約の要件定義書 §9 |
| 11 | 置き場どうしで値が違う物を、CC がどちらかに決めない | R11。列を作る組は、いまのカタログの列をそのまま写した物で、どちらの値かを選んでいない | 集約の要件定義書 R11 |
| 12 | 成績表（material_ranking.json）と型の表を作り直さない | 列の名前が変わらないので、成績表はいまのまま引ける。型の表を作る道具は build_catalog の名前を読む（gen_signal_families.py:53〜62）が、名前が同じなので型の表は変わらない見込み（G2 で確かめる）。作り直すのは M2-D-8 と197番 | m2_todo.json の M2-D-8・ToDo の197番 |
| 13 | materials.md に入る説明の文（gen_materials.py:1588「材料カタログを作る関数（`observe_diag.build_catalog`）が実際に読む鍵」）を直さない | 直すと、作る文書 materials.md の作り直しが要る（gen_materials.py が作る＝docmap.json）。161-2 の後、この文の「build_catalog」は、正しくは写す元の関数（F-3）を指す。162番で写す元の関数を消すときに、場所1 の数え方ごと直す | gen_materials.py:1585〜1590・docmap.json |

### 3-2 決めてほしいこと

［手書き］やることの表の「3-2 決めてほしいこと」
| # | 中身 | 私の案（決まるまでこれで進める） | 出どころ |
|---|---|---|---|
| 1 | 無し（写す元の関数を残す形〔F-3・F-4〕と、calc の代わりに make_material を使う形〔Y-5〕は、技術のやり方なので CC が決め、設計書の監査で問う） | — | まこさん「よい」（2026-11-01）・恒久の決まり49番・m2c15_指標の構造_要件定義書.md:291 |

## 4｜設計の中身

項目の正本＝`design_section_map.json`（3つの出どころを、全部 引き受ける形。件数は、検算 `gen_design_sections.py --check` が出す）。各項目の「何を書くか」の説明は正本に在り、設計書には出しません。

### 4-0 この仕組みは何か（全体・一続きの文章で書く）

［自動］CC が書いて、まこさんが OK した案の【4-0】
［自動］§1 概要の1文目を、プログラムが写した
この工事が解く問題＝列を作る所（build_catalog）は、161-1 で indicators.json に入れた列を作る組を読まず、設定ファイルの古い鍵 約40個と material_params から列を作っているので、indicators.json を直しても列に届かない。この工事（161-2）は、build_catalog を読む口の列を作る組から列を作る形にし、列の名前・並び・値が直す前と同じかを比べる。

いまの build_catalog（observe_diag.py:1792〜2229）は、設定ファイル observe_config.json の鍵を読み（cfg[ の行 71）、種類ごとの for で列を作ります。161-1 で indicators.json に入れた列を作る組（②-12・④-9・314記録・652組）は、まだ誰も読んでいません（scripts の下で column_sets を呼ぶ所は indicators.py の中だけ）。この工事は、build_catalog を、読む口 indicators.py の column_sets が返す組を、並びの順に1つずつ列にする形に替えます。指標の記録の組は make_material（計算の登録の名前・組）で、部品の記録（帯の8種）の組は _band_material（登録の名前・床・組）で作ります。床だけは、いまと同じく設定の band_fee_mult から作ります。直す前の作り方は _catalog_from_config という名前で残し、写すプログラムが列を作る組を作り直すときの写す元にだけ使います（162番で消す）。完成すると、build_catalog は設定の鍵を1つも読まず、indicators.json の列を作る組を直せば、その列が engine_tuner の材料に届きます。列の名前・並び・値は直す前と同じです（列の比べ col_snapshot.py --compare で確かめる）。なぜこの形か＝列を作る組は、いまのカタログの列を、省いた後の形で写した物（gen_indicators_draft.py:970〜988）なので、組を並びの順に回すだけで、名前と並びが直す前と同じになります。10-25 の下書き（build_catalog_new.txt:14〜18）も同じ形でした。読む口の calc を使わないのは、calc がオフの指標を返さず（indicators.py:311〜312）、列を作る組はオフの121記録（組を持つのは111記録）の250組も持つためです。

### 4-1 システムの境界（誰が動かし、誰が結果を使うか）

［自動］CC が書いて、まこさんが OK した案の【4-1】
- この工事の実装を書くのは、当てる道具 apply_audit_fix.py --design です。承認の後に CC が走らせます。
- build_catalog を呼ぶのは、観察の道具の中の38行（grep "build_catalog(" から def を除いた数）と、gen_materials.py:112・:1243・engine_tuner_gen.py:211・:268・engine_tuner.py:168・:182・engine_tuner_exec.py:4020・gen_signal_families.py:60・gen_observe_manual.py:149・condition_parts_diag.py:521・col_snapshot.py:46・gen_params_in_name.py:274 です。出力の形（名前・計算・向きの組の並び）は変わらないので、呼ぶ側は直しません。
- _catalog_from_config を呼ぶのは、写すプログラム（gen_indicators_draft.py:592・:973）・カタログの自己テスト・gen_materials の鍵を拾う口（gen_materials.py:465）だけです。

### 4-2 入力と出力（受け取るもの・出すもの・その形）

［自動］CC が書いて、まこさんが OK した案の【4-2】
- build_catalog の入力＝設定 cfg（読むのは band_fee_mult だけ・_band_fee_floor を通す）と、読む口の column_sets です。出力＝(名前, 計算, 向き) の並びで、直す前と同じ形・同じ652本です。
- column_sets の出力＝組ごとに {記録・種類・名前の型・組・並び・登録の名前} です（登録の名前を足す）。
- _catalog_from_config の入力と出力は、直す前の build_catalog と同じです。
- 写すプログラムの入力は、写す元を _catalog_from_config に替えるほかは同じです。出力の indicators.json は、要素の定義表の ②-12・④-9 の「写す元」「読むプログラム」と、部品の記録8件の出どころの文だけが変わります（当てた後の --rewrite で1回）。
- コマンド＝観察の道具の --selftest-catalog（照らしを2つ足す）・読む口の --selftest・写すプログラムの --selftest・--rewrite・--verify・gen_materials の --selftest です。旗は足しません。

### 4-6 制約（従う決まりの全件と、その出どころ）

［自動］CC が書いて、まこさんが OK した案の【4-6】
| 種類 | 決まり | 原文 | この設計でどう守るか |
|---|---|---|---|
| 法則 | 無し（判定の中身を変えない） | ［自動］ | 法則のファイルに触らない（Y-1・直すファイルの一覧に無い） |
| 型の表 | 無し | ［自動］ | 型の表に触らない（Y-12）。列の名前が同じなので、型の表を作る道具が読む名前（gen_signal_families.py:53〜62）も同じ。G2 で確かめる |
| 場面の決まり | 無し | ［自動］ | 触らない（直すファイルの一覧に無い） |
| そのほか | 指標は指標一覧（material）からだけ呼び出す | core_requirements_full.md:85 | build_catalog が、指標一覧に当たる読む口の列を作る組から列を作る（F-1・F-2） |
| そのほか | 範囲は指標ごとに1つ | core_requirements_full.md:60 | 範囲に触らない（②-4・④-4 の軸のまま・161-1 で写した物） |
| そのほか | 指標の名前に値を入れない | core_requirements_full.md:55・:62 | 列の名前を変えない（Y-4）。記録の名前は RSI のまま |
| そのほか | 作ってはいけない物2（探す値を一覧で限定しない） | core_requirements_full.md:101 | 新しく限定しない。列を作る組は、いまのカタログの列をそのまま写した物で、171番まで列を変えないための物（Y-4） |
| そのほか | 新しいファイルを作らない（恒久78番） | permanent_rules.md §6 の78番 | 新しいファイルは、7-6 が求める壊すプログラム6本だけ |
| そのほか | 控えを作らない（恒久79番の4） | permanent_rules.md §6 の79番 | 直す前の build_catalog は、控えでなく、写すプログラムが使う写す元の関数として残す（162番で消す）。直す前の文字は git に在る |
| そのほか | コードを触ったら G2、H2 の順に印を取り直す | permanent_rules.md §7 の §0-5・§0-5b | observe_diag.py と leak_causality_diag.py を直すので、当てた後に G2 → H2 を走らせる（4-4 の4） |
- 新しく足す決まり：足しません。照らし2つ（⑮⑯）は、列を変えないことと R6 を見張る物で、組めなくなる形はありません。

### 4-3 部品と責任の割り当て（どの部品が何をやるか）

［自動］CC が書いて、まこさんが OK した案の【4-3】
| 部品 | 何に責任を持つか | 新設か直すか |
|---|---|---|
| observe_diag.py の build_catalog | 読む口の列を作る組を並びの順に列にする。設定の鍵を読まない | 直す（中身を置き替える） |
| observe_diag.py の _catalog_from_config | 直す前の build_catalog の中身（写すプログラムの写す元・162番まで） | 新設（中身は直す前の build_catalog のまま） |
| observe_diag.py の selftest_catalog | 名前の並びの照らし（⑮）と、設定の鍵を読まないことの照らし（⑯）を足す | 直す |
| indicators.py の Indicators.column_sets と <モジュール直下>（使い方の説明の行） | 組ごとに計算の登録の名前を返す。無ければ止まる。使い方の説明を合わせる | 直す |
| gen_indicators_draft.py の build_old と catalog_sets | 写す元を _catalog_from_config にする | 直す |
| gen_indicators_draft.py の table_update と <モジュール直下>（PART_SRC・頭の説明） | 要素の定義表の ②-12・④-9 の「写す元」「読むプログラム」と、部品の記録の出どころの文を、いまの形に合わせる | 直す |
| leak_causality_diag.py の <モジュール直下>（WATCHED） | H2 の印の対象に indicators.json と indicators.py を足す | 直す |
| gen_materials.py の _catalog_keys と T12 | 場所1 を数える相手を _catalog_from_config にする | 直す |
| .claude/breaks/b222〜b227 | 7-6 の6行の守り | 新設 |
- 指標を使う部品について：build_catalog は、指標を、読む口の列を作る組（indicators.json の②-12・④-9）と、計算の登録（observe_diag.py:903 の MATERIAL_FAMILIES と、make_material :1051〜1065）から作ります。自前の式は置きません（実装の指示の1件目の直した後の文字に、計算の式は無く、make_material と _band_material を呼ぶだけです）。指標のオン・オフは、いまと同じく engine_tuner の側で indicator_switch.json から効きます（engine_tuner_gen.py:219・:277）。build_catalog は、171番まで列を変えないため、オフの列も作ります（Y-4・indicators.py:337〜338）。

### 4-4 処理の流れ（うまくいったとき、何がどの順に起きるか）

［手書き］やることの表の「4-4 処理の流れ」
| 順 | 読む物 | すること | 書く先 |
|---|---|---|---|
| 1 | 設計書の 4-20 の実装の指示 | 当てる道具（apply_audit_fix.py --design）が、観察の道具・読む口・写すプログラム・H2 の検査・gen_materials と、壊すプログラムに当てる（1件でも合わなければ当てない） | F-1〜F-6 の直すファイル・.claude/breaks の新しい .sh |
| 2 | 直したファイル | 7-6 のコマンドを走らせる（観察の道具の --selftest-catalog・読む口の --selftest・写すプログラムの --selftest・gen_materials の --selftest・grep）。続けて、gen_materials.py --verify（materials.md の場所1 の数が直す前と同じか＝6-5 の3 をここで消す）と、git diff -U0 -- scripts/priority_rebuild/observe_diag.py（出力の先頭が「-」の行＝消えた行が :1792〜1797 の def と docstring だけ＝F-3「本体の文字は1文字も変えない」の確かめ）を走らせる | 画面（結果を worklog に写す） |
| 3 | indicators.json と、写す元（F-3 の関数ほか） | 写すプログラムの --rewrite を1回 走らせ、要素の定義表の ②-12・④-9 の「写す元」「読むプログラム」と、部品の記録8件の出どころ（合わせて10か所）を作り直す（F-4）。画面に出る「違う所」が、この10か所だけであることを見る。続けて --verify で「違い 0 件」かを見る（写す元を F-3 の関数に替えても、②-12・④-9 の組と並びが同じに作れること） | indicators.json・画面 |
| 4 | 直した観察の道具・H2 の検査 | G2 → H2 の印を取り直す（gen_signal_families.py --verify・約73秒 → leak_causality_diag.py・約315秒＝worklog 20261101:157）。observe_diag.py と leak_causality_diag.py を直したため（恒久の決まり §0-5・§0-5b） | g2_pass.json・h2_pass.json |
| 5 | 直す前の列の控え before_20261024.json | 列の比べ（python3 .claude/state/indicator_review/col_snapshot.py --compare .claude/state/indicator_review/col_snapshot/before_20261024.json・約61分・まこさんの OK の後）。4つ（控えに在って今に無い列・今にだけ在る列・値が違う列・名前の並び）を見る＝155-1（同じパラメータの値で計算した値が、直す前と同じこと）。161-2 は列の名前を変えないので、名前ごとの値の比べが、そのまま 155-1 になる | 画面（結果を worklog に写す） |
| 6 | 直した後の全部 | インフラの直し（Y-6＝監査の前の検査の指紋に indicators/ の2本を足す）を、規模を宣言してから行い、監査に出す前のチェックを走らせる（pre_audit_check.py --run・約12分・まこさんの OK の後） | pre_audit_check.json |
| 7 | 直した後の全部（commit の直前） | 2 と 3 を走らせ直し、7-6 が全部成り立ち、--verify が「違い 0 件」かを見る。4〜6 の後に、写す元が指すファイルを消した・直したときと、indicators.json を書き替えたときも、走らせ直してから commit する（CP95 の修正17・next_step.md:61） | 画面（結果を worklog に写す） |

### 4-19 この工事で何が変わるかを、1件に当てはめて示した例

［手書き］やることの表の「4-19 通しの例」
| 修正の番号 | 欄の名前 | 直す前の値 | 直した後の値 |
|---|---|---|---|
| F-1 | RSI の列 | build_catalog が material_params の "RSI" の組 [5]・[7]・[9]・[14]・[21] から作る（observe_diag.py:1806〜1817・:1827〜1828）。名前は RSI5・RSI7・RSI9・RSI14・RSI21 | build_catalog が、読む口の RSI の列を作る組（組 [5]・[7]・[9]・[14]・[21]・並び 8〜12・indicators.json の指標の記録 RSI の②-12）を並びの順に make_material("RSI", 5) ほかで作る。名前と並び（8〜12）は直す前と同じ |
| F-1 | 帯VA の列 | build_catalog が sr_tol の値ごとに _band_material("帯VA", 床, t) で作る（observe_diag.py:1972〜1975） | build_catalog が、読む口の帯VA の列を作る組（組 [0.0015]・[0.003]・[0.006]・並び 230・233・236・部品の記録 帯VA の④-9）を _band_material("帯VA", 床, 0.0015) ほかで作る。床は同じく _band_fee_floor(cfg) |
| F-2 | column_sets の RSI の1件 | {記録 "RSI", 種類 "指標の記録", 名前の型 "RSI{}", 組 [5], 並び 8}（indicators.py:352） | 同じ欄に、登録の名前 "RSI"（RSI の計算の関数の②-2 の登録の名前）が足される。名前の違う例＝ALMA傾き% の1件は、登録の名前 "ALMA傾き" |
| F-3 | いまの build_catalog の中身 | build_catalog の本体（observe_diag.py:1792〜2229） | 同じ文字のまま、_catalog_from_config(cfg) の本体になる |
| F-4 | 写すプログラムが RSI の組を作る元 | od.build_catalog(cfg) の出力（gen_indicators_draft.py:973） | od._catalog_from_config(cfg) の出力。RSI の組 [5]・[7]・[9]・[14]・[21] と並び 8〜12 は同じ（--verify が「違い 0 件」） |
| F-4 | 要素の定義表の ②-12 の写す元と読むプログラム | 写す元「…いまのカタログの並び（observe_diag.build_catalog）」・読むプログラム 空（indicators.json:295・:294） | 写す元「…いまのカタログの並び（observe_diag._catalog_from_config＝写す元の関数・162番まで）」・読むプログラム ["observe_diag.build_catalog"]（--rewrite の後） |
| F-5 | H2 の印の対象 | indicators/indicators.json と indicators/indicators.py が無い（leak_causality_diag.py:244〜263） | 2本が在る。RSI の列を作る組を indicators.json で直すと、H2 の印が合わなくなる |
| F-6 | materials.md の場所1 が数える rsi_periods | build_catalog の中の cfg["rsi_periods"]（observe_diag.py:1827）を数える（gen_materials.py:465） | _catalog_from_config の中の cfg["rsi_periods"] を数える。場所1 の数は同じ |

### 4-7 探索の範囲（決める値と、その探し方＝範囲・並び・本数）

［自動］CC が書いて、まこさんが OK した案の【4-7】
| 何 | この工事が関わるか | どう扱うか | 探し方のどの段階か | 役割・範囲・代表の値（スキャル／デイトレ）・出どころ・カタログに在るか・オンか |
|---|---|---|---|---|
| 指標 | 関わる（列を作る所の読み元を替える。列は変えない） | 読むだけ（列を作る組の652組を読む） | 最初の段階の母数の元（指標 × 時間足）。中身は変えない | ［自動］ |
| 閾値 | 関わらない（直すファイルに閾値の置き場が無い・build_catalog は閾値を読まない＝observe_diag.py:1792〜2229） | 触らない | — | ［自動］ |
| パラメータ | 列を作る組の値（いまの列のパラメータ）を読む | 読むだけ。値は変えない | 最初の段階（いまの列のまま）。範囲から探すのは171番・M2-E-8 | ［自動］ |
| 時間足 | 関わらない（build_catalog は時間足を読まない＝observe_diag.py:1792〜2229 に timeframes が無い・時間足は build_features が読む） | 触らない | — | ［自動］ |
- 役割に沿って使うこと（要件定義の3番の5）：この工事は指標の役割を変えません。列を作る所の読み元だけを替えます。右の列にプログラムが写す役割と違う使い方はしません。

［自動］`indicator_params_by_strategy.json`・`indicator_roles_thresholds.json`・`indicator_switch.json` から、この項目の文に名前が在る指標の行を、プログラムが写した
この項目の文に、指標の名前（指標の定義の表の「種類」）が見つかりません。

［自動］使える時間足の全部＝`observe_config.json` の timeframes。役割ごとに使える時間足＝`signal_families.json` の role_lineage。プログラムが写した
| 何 | 使える時間足 |
|---|---|
| 全部（11個） | 1m・3m・5m・10m・15m・30m・1h・2h・4h・6h・1d |
| 役割 env（型 E-a1・E-a4・E-a5・E-a8 に掛かる） | 全部 |
| 役割 location（型 E-a1・E-a4・E-a5・E-a8 に掛かる） | 全部 |
| 役割 sufficiency（型 E-a1・E-a4・E-a5・E-a8 に掛かる） | 全部 |
| 役割 trigger（型 E-a1・E-a4・E-a5・E-a8 に掛かる） | 5m・10m・15m |

### 4-9 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗）

［自動］CC が書いて、まこさんが OK した案の【4-9】
- 指定できる項目は足しません。build_catalog が読む設定は band_fee_mult だけです（observe_config.json:410）。設定の古い鍵と material_params・drop_columns は、写す元の関数（_catalog_from_config）だけが読みます。
- 値の持ち方：範囲は、指標ごとに1つの欄にだけ置きます（②-4・④-4 の軸ごと・161-1 のまま）。この工事は範囲に触りません。

### 4-21 新しく入る数字と式の一覧（1件ずつの出どころ）

［自動］CC が書いて、まこさんが OK した案の【新しく入る数字と式の一覧】
| 番号 | 数字か式 | 出どころ |
|---|---|---|
| ［自動］ | 2026・11・01・20261101・161・162・171 | 工事の日付（2026-11-01）と工事名（m2c15-catalog-redirect-20261101）と ToDo の番号（161-2・162番・171番）。全部 説明の文で、計算には使わない |
| ［自動］ | 2・3・4・5・6・9・12 | やることの表の番号（F-1〜F-6・Y-5）と要素の定義表の番号（②-2・②-12・④-3・④-9）と、集約の要件定義書の R5・R6。説明の文で、計算には使わない |
| ［自動］ | 1・-1・0 | 壊すプログラム b222 の、最後の1組を落とす切り方（[:-1]）と、b226 の grep の数が 0 という決まった文。build_catalog の照らし（⑮）の、最初に違う番号を数える所の 0 始まり |
| ［自動］ | 222・223・224・225・226・227 | 新しい壊すプログラムの番号（.claude/breaks の最後の番号 b221 の次から） |
| ［自動］ | 2026-08-20・2026-08-13 | 既に在る説明の文の日付（observe_diag.py:1795 の A-2・leak_causality_diag.py:253 の M2-1-9）を、そのまま残した物 |

［自動］実装の指示のうち、売買のロジック・設定のファイルに新しく入る数字を、プログラムが抜き出した（コメントの中の数字と、直す前から在る数字は除く）
| 実装の番号 | 数字 |
|---|---|
| 1 | 20261101 |
| 1 | 1 |
| 1 | 11 |
| 1 | 01 |
| 1 | 161 |
| 1 | 12 |
| 1 | 9 |
| 1 | 5 |
| 1 | 0 |
| 1 | 3 |
| 2 | 0 |
| 3 | 2026 |
| 3 | 11 |
| 3 | 01 |
| 3 | 20261101 |
| 3 | 2 |
| 3 | 3 |
| 5 | 161 |
| 6 | 161 |
| 6 | 2 |
| 14 | 2026 |
| 14 | 11 |
| 14 | 01 |
| 14 | 20261101 |
| 14 | 6 |

### 4-12 出る結果の姿（完成したとき、何がどう表示されるか）

［自動］CC が書いて、まこさんが OK した案の【4-12】
当てた直後に、7-6 の6行のコマンドが全部 通ります（観察の道具の --selftest-catalog は「❌ 0 件」・読む口と写すプログラムと gen_materials の自己テストは全部 ✅・grep は「…leak_causality_diag.py:1」）。当てた後の手順が済んでから確かめる物は、次のとおりです。
- 写すプログラムの --rewrite＝「写す元から作り直した物と違う所＝10 件」（要素の定義表の ②-12・④-9 と、部品の記録8件の出どころ）を出して書く（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/gen_indicators_draft.py --rewrite を SDK の直下で）。
- 写すプログラムの --verify＝「✅ 違い 0 件」（python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/gen_indicators_draft.py --verify を SDK の直下で）。
- 2-1 の3行＝awk の数が 0 と 1 以上・grep -c が 1（WATCHED の2本は1行に書く）。
- G2 → H2 の印＝python3 scripts/priority_rebuild/gen_signal_families.py --verify と python3 scripts/priority_rebuild/leak_causality_diag.py が全部 pass（h2_pass.json の対象が2本増える。g2_pass.json の対象は indicators.py だけ増え、indicators.json は入らない＝verify() が build_table() を _G2FileSpy の外で先に呼び、読む口が1回だけ読むため。jq -r '.files[]' .claude/state/g2_pass.json | grep indicators で見る）。
- 列の比べ（155-1）＝python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/col_snapshot.py --compare /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/col_snapshot/before_20261024.json が「控えに在って今に無い列 0・今にだけ在る列 0・値が違う列 0・名前の並び 同じ」で終わりのコード 0（約61分・まこさんの OK の後）。

### 4-5 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか）

［手書き］やることの表の「4-5 止まる条件」
| 条件 | 止める所 | 画面に出す文 |
|---|---|---|
| indicators.json が無い・古い形・列を作る組の並びが重なる／抜ける | 読む口の読み込み（build_catalog が読む口を呼んだとき・indicators.py:182・:349〜359） | 読む口の文のまま（「[読む口] indicators.json が無い・読めない」「並びが重なる」「並びが抜ける」ほか） |
| 列を作る組を持つ記録に、計算の登録の名前が無い（F-2） | 読む口の column_sets | 「[読む口] 列を作る組を持つのに、計算の関数の登録の名前が無い」と、記録の名前 |
| 列を作る組の登録の名前が、計算の登録に無い | build_catalog が呼ぶ make_material（observe_diag.py:1056〜1058） | 「[材料カタログ] 知らない指標の種類」と、登録の名前 |
| 組の数が、名前の型の {} の数と合わない | build_catalog が呼ぶ make_material（observe_diag.py:1062〜1064） | 「[材料カタログ] <種類> のパラメータの個数が合わない」 |
| 部品の記録の登録の名前が、帯の計算式の表（_BAND_IMPL）に無い | build_catalog | 「[材料カタログ] 部品の記録 <名前> の登録の名前が、帯の計算式の表に無い」 |
| 指標の記録の登録の名前が、帯の計算式の表（_BAND_IMPL）に在る（床の無い列を黙って作らない＝監査 CP96 の修正13） | build_catalog | 「[材料カタログ] 指標の記録 <名前> の登録の名前 <登録の名前> が、帯の計算式の表に在る（床を結び付ける部品の記録で作る物）」 |
| indicators の名前で読み込んだ物が、読む口でない（load が無い＝監査 CP96 の修正14） | build_catalog（読む口を読み込んだ直後） | 「[材料カタログ] 読む口でない物が indicators の名前で読み込まれている: <読み込んだ物のファイル>」 |
| build_catalog の名前の並びが、写す元の関数（F-3）の名前の並びと違う | 観察の道具の --selftest-catalog | 「[材料カタログ] build_catalog の名前の並びが、写す元の関数と違う」と、最初に違う番号と名前 |
| build_catalog の中に、cfg の鍵を読む所（cfg[...]・cfg.get(...)）が在る | 観察の道具の --selftest-catalog（構文の木で照らす） | 「[材料カタログ] build_catalog が設定の鍵を読んでいる」と、鍵の名前 |
| 写すプログラムの cols・catalog_sets が build_catalog を呼ぶ（F-4） | 写すプログラムの --selftest（構文の木で照らす） | 「❌ 写す: 写す元は _catalog_from_config で、build_catalog を呼ばない（161-2 の F-4）」 |

### 4-10 保存先（出したものをどこに置くか・上書きか、書き足すか）

［自動］CC が書いて、まこさんが OK した案の【4-10】
- 直すのはコードと、壊すプログラム6本（新しいファイル）です。データは、当てた後の写すプログラムの --rewrite が indicators.json を1回 上書きします。変わるのは、要素の定義表の ②-12・④-9 の「写す元」「読むプログラム」と、部品の記録8件の出どころの文の10か所だけで、列を作る組の組と並び・指標の値は変わりません（--rewrite が違う所を全部 画面に出す）。
- 置き場が1か所であること：列を作る組は、indicators.json の②-12・④-9 の1か所だけで、build_catalog はそこを読みます（scripts の下で column_sets を呼ぶ所は、直した後も build_catalog だけ＝grep -rn "column_sets()" --include='*.py' v3-bitget-api-sdk/bitget-python-sdk-api/scripts）。写す元の関数（_catalog_from_config）は、列を作る組を作り直すときの写す元で、列を作る所ではありません（162番で消す）。
- 直すと届く先：build_catalog を呼ぶ所の全部（【4-1】の2行目）。
- 出どころをどこまで確かめたか：値がページに在るかまで（列を作る組は、161-1 で写した値をそのまま読む）。中身の正しさは確かめていません（70番）。

### 4-23 置き場の地図（直す前と後）

［自動］CC が書いて、まこさんが OK した案の【4-23】
| 置き場 | 直す前（何が在る・誰が書く・誰が読む） | 直した後（何が在る・誰が書く・誰が読む） |
|---|---|---|
| 列を作る組の読み元 | build_catalog が observe_config.json の古い鍵・material_params・drop_columns を読む。indicators.json の②-12・④-9 は誰も読まない | build_catalog が読む口の column_sets から②-12・④-9 を読む。設定は band_fee_mult だけを読む |
| 直す前の build_catalog の中身 | build_catalog（列を作る所と、写すプログラムの写す元を兼ねる） | _catalog_from_config（写すプログラムの写す元だけ・162番で消す） |
| H2 の印の対象 | WATCHED に indicators/ の2本が無い | WATCHED に indicators.json と indicators.py が在る |
| materials.md の場所1 の数え方 | build_catalog の中の設定の鍵を数える | _catalog_from_config の中の設定の鍵を数える（数は同じ） |
| indicators.json の要素の定義表の ②-12・④-9 と部品の記録の出どころの文 | 写す元＝build_catalog・読むプログラム＝空・部品の出どころ＝build_catalog の帯の for | 写す元＝_catalog_from_config・読むプログラム＝build_catalog・部品の出どころ＝_catalog_from_config の帯の for（写すプログラムが --rewrite で書く） |
- 直した後に、列を作る組を変えるときの手順：162番までは、写す元（observe_config.json の鍵）を直し、写すプログラムの --rewrite で indicators.json を作り直します（161-1 の修正14 案B）。build_catalog は、作り直した indicators.json を読みます。
- 読む先が変わるプログラム：build_catalog だけです。呼ぶ側（【4-1】の2行目）は、build_catalog の出力をいまと同じ形で受けます。写すプログラムと gen_materials は、読む相手を build_catalog から _catalog_from_config に替えます。

### 4-14 性能（どれくらい時間が掛かり、どれくらい容量を使うか）

［自動］CC が書いて、まこさんが OK した案の【4-14】
| 何 | 見込み | 根拠 |
|---|---|---|
| 観察の道具の --selftest-catalog | 約13秒（build_catalog と写す元の関数を1回ずつ多く作るが、関数を組むだけ） | 2026-11-01 に今のコードで 12.7秒 |
| 読む口の --selftest | 約0.1秒 | worklog 20261101:118 |
| 写すプログラムの --selftest・--rewrite・--verify | 約3秒・約97秒・約95秒 | worklog 20261101:118・:229・:230 |
| gen_materials の --selftest | 約82秒 | worklog 20261101:157 |
| G2 → H2 | 約73秒 → 約315秒 | worklog 20261101:157 |
| 列の比べ | 約61分 | col_snapshot/before_20261024.log の 3637秒 |
| 監査に出す前のチェック | 約12分 | worklog 20261101:157 |

### 4-15 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか）

［自動］CC が書いて、まこさんが OK した案の【4-15】
- 仮当て（A12）と壊すプログラムは、本物のファイルを仮に書き替える道具の錠を取ってから走ります（require_design_check_before_approval.py:800〜816）。2つが同じファイルを同時に書くことはありません。
- 列の比べ（col_snapshot.py --compare）は、控えを読むだけで書きません（col_snapshot.py:105〜113）。
- この工事の走行は1つずつ打ちます。

### 4-16 セキュリティ（人に見せてはいけない値と、書き換えられては困る記録）

［自動］CC が書いて、まこさんが OK した案の【4-16】
- 取引所の鍵・本番で実際に発注するかの切り替えには触りません（直すファイルの一覧に無い）。
- 検査済みの記録（h2_pass.json・g2_pass.json）は、当てた後に G2 と H2 の検査を走らせて、道具が書きます。手では書きません。

### 4-17 ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか）

［自動］CC が書いて、まこさんが OK した案の【4-17】
- 自己テストは、1行ずつ通ったか落ちたかの印を出します（python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog ほか、7-6 の6行のコマンド）。
- 列の比べは、50種ごとに「何種目まで・何秒」を出します（col_snapshot.py:79〜80）。

### 4-13 影響範囲（この直しで、ほかのどれが壊れるか）

［手書き］やることの表の「4-13 影響範囲」
| 読む側 | この工事の後どうなるか | 受け持つ工事 |
|---|---|---|
| 観察の道具の中で build_catalog を呼ぶ38行（observe_diag.py:2386・:2726・:3914 ほか。grep "build_catalog(" から def の行を除いた数。48 は語の出現数） | 変わらない。名前と並びと計算の関数は、直す前と同じ（列の比べで確かめる） | この工事 |
| engine_tuner_gen.py:211・:268（material_pool・material_ranges） | 変わらない。名前が同じなので、材料と範囲も同じ | 向け直すのは171番 |
| engine_tuner.py:168・:182・engine_tuner_exec.py:4020・condition_parts_diag.py:521・gen_observe_manual.py:149・gen_materials.py:112・:1243・col_snapshot.py:46・gen_params_in_name.py:274 | 変わらない。build_catalog の名前を読むだけ | 170番・171番 |
| gen_signal_families.py:60（型の表を作る道具） | 変わらない見込み。名前が同じなので、型の表と承認の指紋は変わらない。G2 で確かめる（4-4 の4） | この工事 |
| 写すプログラム gen_indicators_draft.py:592・:973・:835〜838・:128・:16 | F-4 で、写す元を F-3 の関数に替え、要素の定義表と部品の記録の出どころの文を合わせる。当てた後の --rewrite で indicators.json の10か所が変わり、その後の --verify は「違い 0 件」 | この工事 |
| indicators.json（要素の定義表の ②-12・④-9・部品の記録8件の出どころ） | 文だけが変わる（列を作る組の組と並び・指標の値は変わらない）。H2 の印の対象に入る（F-5）ので、--rewrite の後に H2 を取り直す（4-4 の4） | この工事 |
| gen_materials.py:455・:465・:2478 | F-6 で、数える相手を F-3 の関数に替える。materials.md の場所1 の数は変わらない見込み。説明の文 :1588 は直さない（Y-13） | この工事 |
| H2 の印（leak_causality_diag.py:244〜263） | F-5 で、indicators.json と indicators.py が対象に入る。印を取り直す（4-4 の4） | この工事 |
| G2 の印（gen_signal_families.py:871〜972） | 対象に入るのは indicators.py だけで、indicators.json は入らない。理由＝verify() は build_table()（_catalog() → build_catalog → 読む口が indicators.json を読む）を _G2FileSpy の外で先に呼び（gen_signal_families.py:526）、読む口は同じパスを1回だけ読む（indicators.py:366〜378）ので、spy の中（:567・:964〜972）では indicators.json が開かれない。files()（:909〜916）が足すのは sys.modules の .py だけ。indicators.json の見張りは H2（F-5）。4-4 の4 の後に grep -o 'indicators/indicators[.a-z]*' .claude/state/g2_pass.json で対象を見る（indicators/indicators.py だけが出る）。G2 の対象に indicators.json を足すのは171番（enforce_g2_pass・gen_signal_families） | この工事 |
| 監査の前の検査の指紋（.claude/tools/pre_audit_check.py:108〜122・:213〜215） | indicators/ の下は入っていない。インフラの直しで足す（Y-6） | インフラの直し（承認の後） |
| 閉じた工事の壊すプログラム b137・b128 | 前提が変わる。壊す相手の行（:1811・:1823）は F-3 の関数へ移る。照らし⑮が F-3 の関数を呼ぶので、b137 は期待の文で落ち、b128 は⑮の文で落ちる（期待の文「❌ K-1:」と違う）。承認では走らない（Y-7） | 閉じた工事のまま（直さない） |
| 161-1 の壊すプログラム b215〜b221 | 変わらない見込み。壊すのは読む口の決まりと写すプログラムの写し方で、F-2 と F-4 の直す所と重ならない（確かめていない＝承認の前の検査で走る） | この工事 |
| 観察の道具のカタログの自己テストの P-1（observe_diag.py:7894〜7928） | 変わらない。設定の material_params から期待の名前を作り、build_catalog の名前と照らす。列を作る組がいまの列の写しなので通る＝162番までは、設定と indicators.json がずれていないかの見張りにもなる | この工事 |

### 4-18 再利用（手本にした、既にあるものの形）

［自動］CC が書いて、まこさんが OK した案の【4-18】
| 手本 | 何を写すか |
|---|---|
| .claude/state/verbatim/m2c15-single-source-redirect-20261025/cc_draft_2a1/build_catalog_new.txt | 組を並びの順に回して make_material か _band_material を呼ぶ形 |
| .claude/state/indicator_review/gen_fix_inventory.py の読む口の import（sys.path に indicators を足して import する） | build_catalog が読む口を読み込む形 |
| observe_diag.py:7894〜7928（カタログの自己テストの P-1・P-2） | 照らし（⑮⑯）の書き方 |
| .claude/breaks/b137_material_params_ignored.sh・b221_draft_rep_by_position.sh | 壊すプログラムの形（guard・1か所でなければ止まる・measure・finish） |

### 4-20 実装の指示（プログラムが実物に当てる形・6つの欄）

［自動］CC が書いて、まこさんが OK した案の【4-20】＝コードの文字は CC の手書き
<!-- ACC_IMPL_START hash=4a83646713dcc5c6 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝元データの `実装の指示`。当て方＝`python3 .claude/tools/apply_audit_fix.py --design [--dry]`（承認の印と設計書のハッシュ値が合うときだけ当たる）。

#### 実装 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: build_catalog の頭（F-1・F-3）＝読む口の列を作る組から列を作る新しい build_catalog を置き、直す前の中身を _catalog_from_config として残す（直す前の本体の文字は1文字も変えない）
直す前の文字:
~~~
def build_catalog(cfg: dict) -> list[tuple]:
    """指標カタログ。期間・パラメータは observe_config.json から取る（コードに焼かない）。

    ★2026-08-13（A-2）＝計算式は上の材料の表（MATERIAL_FAMILIES）に在る。
      この関数がやるのは「設定ファイルの数字を読んで、その組を1つずつ作る」ことだけ。
    """

~~~
直した後の文字:
~~~
def build_catalog(cfg: dict) -> list[tuple]:
    """指標カタログ＝読む口（indicators/indicators.py）の列を作る組から作る（工事 m2c15-catalog-redirect-20261101・やることの表 F-1）。

    ★2026-11-01（161-2・集約の要件定義書 R6）＝直す前は、設定ファイル observe_config.json の鍵（古い鍵・material_params・drop_columns）を
      読み、種類ごとの for で組を作っていた（その作り方は下の _catalog_from_config に残す＝写すプログラムの写す元・162番で消す）。
      いまは、indicators.json の列を作る組（②-12・④-9＝161-1 で、省いた後のいまのカタログの列から写した物）を、並びの順に1つずつ列にする。
    ★cfg から読むのは、帯の床の倍数 band_fee_mult だけ（_band_fee_floor に cfg を渡す）。設定の鍵は1つも読まない。
    ★計算は、いまと同じく計算の登録（MATERIAL_FAMILIES）から make_material・_band_material が取る
      （読む口の calc はオフの指標を返さないので使わない＝やることの表 Y-5）。
    """
    _ind_dir = str(pathlib.Path(__file__).resolve().parent / "indicators")
    if _ind_dir not in sys.path:
        sys.path.insert(0, _ind_dir)
    import indicators as _ind                        # 読む口（indicators.json を開くのは、このプログラムだけ＝集約の要件定義書 R5）
    if not hasattr(_ind, "load"):
        raise SystemExit(f"[材料カタログ] 読む口でない物が indicators の名前で読み込まれている: {getattr(_ind, '__file__', _ind)}")
    _load_pta()
    _bfl = _band_fee_floor(cfg)
    C = []
    for cs in _ind.load().column_sets():
        reg = cs["登録の名前"]
        if cs["種類"] == "部品の記録":
            if reg not in _BAND_IMPL:
                raise SystemExit(f"[材料カタログ] 部品の記録 {cs['記録']} の登録の名前 {reg} が、帯の計算式の表に無い")
            C.append(_band_material(reg, _bfl, *cs["組"]))
        else:
            if reg in _BAND_IMPL:
                raise SystemExit(f"[材料カタログ] 指標の記録 {cs['記録']} の登録の名前 {reg} が、帯の計算式の表に在る（床を結び付ける部品の記録で作る物）")
            C.append(make_material(reg, *cs["組"]))
    return C


def _catalog_from_config(cfg: dict) -> list[tuple]:
    """直す前の指標カタログの作り方（期間・パラメータを observe_config.json から取る）。

    ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-3）＝列を作る所は build_catalog（読む口の列を作る組から作る）に替えた。
      この関数は、写すプログラム（gen_indicators_draft.py）が列を作る組を作り直すときの写す元としてだけ残す（162番で消す）。
      呼ぶのは、写すプログラム・カタログの自己テスト（build_catalog と名前の並びを照らす）・gen_materials の鍵を拾う口だけ。
    ★2026-08-13（A-2）＝計算式は上の材料の表（MATERIAL_FAMILIES）に在る。
      この関数がやるのは「設定ファイルの数字を読んで、その組を1つずつ作る」ことだけ。
    """

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:1792「def build_catalog(cfg: dict) -> list[tuple]:」
状態: 確定

#### 実装 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: カタログの自己テスト selftest_catalog（F-1）＝build_catalog と写す元の関数の名前の並びの照らし（⑮）と、build_catalog が設定の鍵を読まないことの照らし（⑯）を足す
直す前の文字:
~~~
    if not _g14._group_usable_col("ROC12__5m", "ROC", "5m", None, _tb14):
        ng.append("修正1: 範囲の中の数字の列（ROC12）を、段の候補に使えないと判定した")
    if exit_:

~~~
直した後の文字:
~~~
    if not _g14._group_usable_col("ROC12__5m", "ROC", "5m", None, _tb14):
        ng.append("修正1: 範囲の中の数字の列（ROC12）を、段の候補に使えないと判定した")
    # ── 工事 m2c15-catalog-redirect-20261101 の番人（2026-11-01・やることの表 F-1）──
    #  ⑮build_catalog（読む口の列を作る組から作る）の名前の並びが、写す元の関数 _catalog_from_config と1本も違わない
    _new15 = [nm for nm, _f, _d in build_catalog(cfg)]
    _old15 = [nm for nm, _f, _d in _catalog_from_config(cfg)]
    if _new15 != _old15:
        _i15 = next((i for i, (a, b) in enumerate(zip(_new15, _old15)) if a != b), min(len(_new15), len(_old15)))
        ng.append(f"[材料カタログ] build_catalog の名前の並びが、写す元の関数と違う（{len(_new15)} 本 ／ {len(_old15)} 本・"
                  f"最初に違う番号 {_i15}＝{_new15[_i15] if _i15 < len(_new15) else 'なし'} ／ {_old15[_i15] if _i15 < len(_old15) else 'なし'}）")
    #  ⑯build_catalog の構文の木に、cfg の鍵を読む所（cfg[...]・cfg.get(...)）が無い（集約の要件定義書 R6）
    import ast as _ast16
    import inspect as _in16
    _fn16 = _ast16.parse(_in16.getsource(build_catalog))
    _keys16 = sorted({n.slice.value for n in _ast16.walk(_fn16)
                      if isinstance(n, _ast16.Subscript) and isinstance(n.value, _ast16.Name) and n.value.id == "cfg"
                      and isinstance(n.slice, _ast16.Constant)}
                     | {n.args[0].value for n in _ast16.walk(_fn16)
                        if isinstance(n, _ast16.Call) and isinstance(n.func, _ast16.Attribute) and n.func.attr == "get"
                        and isinstance(n.func.value, _ast16.Name) and n.func.value.id == "cfg"
                        and n.args and isinstance(n.args[0], _ast16.Constant)})
    if _keys16:
        ng.append(f"[材料カタログ] build_catalog が設定の鍵を読んでいる: {_keys16}")
    if exit_:

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:7936「if not _g14._group_usable_col("ROC12__5m", "ROC", "5m", None, _tb14):」
状態: 確定

#### 実装 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py
直す箇所: 読む口の column_sets（F-2）＝組ごとに計算の登録の名前を返す。組を持つのに登録の名前が無い・計算の関数の要素がオフなら止まる
直す前の文字:
~~~
        ★171番まで列を変えないため、決まり⑤の外（オフの指標と、オフの指標を使う部品の列の組も返す）。決まり③は守る＝「列を作る組」の要素が
          オフなら止まる（監査 CP94 の修正12）。"""
        out = []
        for kind in ("指標の記録", "部品の記録"):
            el = self._el("列を作る組", kind)
            if (self.rows[kind][el].get("オン/オフ")) != "オン":
                _stop(f"オフの要素は返さない: {kind} の「{el}」")
            for nm, rec in self.records[kind].items():
                cs = rec.get(el)
                if not cs:
                    continue
                tpls, sets, order = cs.get("名前の型") or [], cs.get("組") or [], cs.get("並び") or []
                if len(sets) != len(order):
                    _stop(f"列を作る組の組と並びの数が合わない: {nm}")
                for p, i in zip(sets, order):
                    out.append({"記録": nm, "種類": kind, "名前の型": tpls[0] if tpls else None, "組": list(p), "並び": int(i)})

~~~
直した後の文字:
~~~
        ★171番まで列を変えないため、決まり⑤の外（オフの指標と、オフの指標を使う部品の列の組も返す）。決まり③は守る＝「列を作る組」の要素が
          オフなら止まる（監査 CP94 の修正12）。
        ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-2）＝組ごとに、計算の登録の名前（②-2・④-3 の「登録の名前」）も返す。
          build_catalog が、その名前で計算の登録から列を作る（記録の名前と登録の名前が違う記録が在る＝例 ALMA傾き% の登録は ALMA傾き）。
          組を持つのに登録の名前が無ければ止まる。「計算の関数」の要素がオフでも止まる（決まり③）。"""
        out = []
        for kind in ("指標の記録", "部品の記録"):
            el = self._el("列を作る組", kind)
            if (self.rows[kind][el].get("オン/オフ")) != "オン":
                _stop(f"オフの要素は返さない: {kind} の「{el}」")
            ce_el = self._el("計算の関数", kind)
            if (self.rows[kind][ce_el].get("オン/オフ")) != "オン":
                _stop(f"オフの要素は返さない: {kind} の「{ce_el}」")
            for nm, rec in self.records[kind].items():
                cs = rec.get(el)
                if not cs:
                    continue
                tpls, sets, order = cs.get("名前の型") or [], cs.get("組") or [], cs.get("並び") or []
                if len(sets) != len(order):
                    _stop(f"列を作る組の組と並びの数が合わない: {nm}")
                ce = rec.get(ce_el)
                reg = ce.get("登録の名前") if isinstance(ce, dict) else None
                if sets and not reg:
                    _stop(f"列を作る組を持つのに、計算の関数の登録の名前が無い: {nm}")
                for p, i in zip(sets, order):
                    out.append({"記録": nm, "種類": kind, "名前の型": tpls[0] if tpls else None, "組": list(p), "並び": int(i),
                                "登録の名前": reg})

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py:352「out.append({"記録": nm, "種類": kind, "名前の型": tpls[0] if tpls else None, "組": list(p), "並び": int(i)})」
状態: 確定

#### 実装 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py
直す箇所: 読む口の使い方の説明（F-2）
直す前の文字:
~~~
  r.column_sets()                             # 列を作る組（指標と部品）をカタログの並びの順で（161-2 の build_catalog が使う）

~~~
直した後の文字:
~~~
  r.column_sets()                             # 列を作る組（指標と部品）をカタログの並びの順で・組ごとに計算の登録の名前も（build_catalog が使う）

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py:28「# 列を作る組（指標と部品）をカタログの並びの順で（161-2 の build_catalog が使う）」
状態: 確定

#### 実装 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py
直す箇所: 読む口の自己テスト（F-2）＝登録の名前を返す行と、無ければ止まる行を足す
直す前の文字:
~~~
    t("列を作る組を並びの順で返す（指標と部品）", [x["記録"] for x in cs] == ["RSI", "OFF指標", "RSI", "帯見本"] and [x["並び"] for x in cs] == [0, 1, 2, 3])

~~~
直した後の文字:
~~~
    t("列を作る組を並びの順で返す（指標と部品）", [x["記録"] for x in cs] == ["RSI", "OFF指標", "RSI", "帯見本"] and [x["並び"] for x in cs] == [0, 1, 2, 3])
    t("列を作る組は、組ごとに計算の登録の名前も返す（build_catalog が使う・161-2 の F-2）", [x.get("登録の名前") for x in cs] == ["RSI", "OFF", "RSI", "帯見本"])
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["計算の関数"]["登録の名前"] = None
    t("列を作る組を持つのに計算の登録の名前が無いと止まる（161-2 の F-2）", stops(bad, "登録の名前が無い"))

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py:523「t("列を作る組を並びの順で返す（指標と部品）"」
状態: 確定

#### 実装 6
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py
直す箇所: 読む口の自己テスト（F-2）＝計算の口の「登録の名前が無ければ止まる」の試しを、組を持たない部品（帯既定）で行う（組を持つ記録は、3件目の直しで読み込みのときに止まるため）
直す前の文字:
~~~
    bad = copy.deepcopy(base)
    bad["指標の記録"]["RSI"]["計算の関数"]["登録の名前"] = None
    t("計算: 登録の名前が無ければ止まる", calc_stops(Indicators(bad, timeframes=["5m"], registry=reg), "RSI", "計算の関数の登録が無い"))

~~~
直した後の文字:
~~~
    bad = copy.deepcopy(base)
    bad["部品の記録"]["帯既定"]["計算の関数"]["登録の名前"] = None
    t("計算: 登録の名前が無ければ止まる（組を持たない部品＝帯既定で試す・組を持つ記録は読み込みで止まる＝161-2 の F-2）",
      calc_stops(Indicators(bad, timeframes=["5m"], registry=reg), "帯既定", "計算の関数の登録が無い"))

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.py:563「t("計算: 登録の名前が無ければ止まる"」
状態: 確定

#### 実装 7
対象のファイル: .claude/state/indicator_review/gen_indicators_draft.py
直す箇所: 写すプログラムの build_old の cols（F-4）＝写す元を _catalog_from_config にする
直す前の文字:
~~~
        for nm, _f, _d in od.build_catalog(c):

~~~
直した後の文字:
~~~
        # ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-4）＝写す元は、設定から列を作る _catalog_from_config（162番まで）。
        #   build_catalog は読む口の列を作る組から作るので、写す元にすると indicators.json を indicators.json から作ることになる。
        for nm, _f, _d in od._catalog_from_config(c):

~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:592「for nm, _f, _d in od.build_catalog(c):」
状態: 確定

#### 実装 8
対象のファイル: .claude/state/indicator_review/gen_indicators_draft.py
直す箇所: 写すプログラムの catalog_sets（F-4）＝写す元を _catalog_from_config にする
直す前の文字:
~~~
    cat = od.build_catalog(cfg)

~~~
直した後の文字:
~~~
    cat = od._catalog_from_config(cfg)                    # 写す元＝設定から列を作る関数（162番まで・161-2 のやることの表 F-4）

~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:973「cat = od.build_catalog(cfg)」
状態: 確定

#### 実装 9
対象のファイル: .claude/state/indicator_review/gen_indicators_draft.py
直す箇所: 写すプログラムの自己テスト（F-4）＝写す元が build_catalog でないことを、構文の木で照らす行を足す
直す前の文字:
~~~
    except SystemExit as e:
        t(f"読む口: 写した物を読み込める（{e}）", False)
    for name, good in ok:

~~~
直した後の文字:
~~~
    except SystemExit as e:
        t(f"読む口: 写した物を読み込める（{e}）", False)
    # 5 写す元（161-2 のやることの表 F-4）＝列を作る組と出どころの鍵を作る所（build_old の cols・catalog_sets）は、
    #   build_catalog でなく写す元の関数 _catalog_from_config を呼ぶ（構文の木で、呼んでいる属性の名前を見る）
    import ast as _ast5
    _calls5 = {}
    for _n5 in _ast5.walk(_ast5.parse(Path(__file__).read_text(encoding="utf-8"))):
        if isinstance(_n5, _ast5.FunctionDef) and _n5.name in ("build_old", "catalog_sets"):
            _calls5[_n5.name] = {c.func.attr for c in _ast5.walk(_n5) if isinstance(c, _ast5.Call) and isinstance(c.func, _ast5.Attribute)}
    t("写す: 写す元は _catalog_from_config で、build_catalog を呼ばない（161-2 の F-4）",
      len(_calls5) == 2 and all("_catalog_from_config" in v and "build_catalog" not in v for v in _calls5.values()))
    for name, good in ok:

~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:1711「t(f"読む口: 写した物を読み込める（{e}）", False)」
状態: 確定

#### 実装 10
対象のファイル: .claude/state/indicator_review/gen_indicators_draft.py
直す箇所: 写すプログラムの table_update（F-4）＝要素の定義表の ②-12・④-9 の「写す元」を _catalog_from_config に、「読むプログラム」に build_catalog を書く（当てた後の --rewrite で indicators.json に入る）
直す前の文字:
~~~
    for no, add in (("②-9", SRC29_ADD), ("③-5", SRC35_ADD)):         # 監査 CP94 の修正9＝写す元の文を、いまの写し先に合わせる
        e = next(x for x in t["要素"] if x["番号"] == no)
        if add not in e["写す元"]:
            e["写す元"] = e["写す元"] + add

~~~
直した後の文字:
~~~
    for no, add in (("②-9", SRC29_ADD), ("③-5", SRC35_ADD)):         # 監査 CP94 の修正9＝写す元の文を、いまの写し先に合わせる
        e = next(x for x in t["要素"] if x["番号"] == no)
        if add not in e["写す元"]:
            e["写す元"] = e["写す元"] + add
    # ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-4）＝列を作る組の写す元は _catalog_from_config（162番まで）、
    #   読むのは build_catalog になった。要素の定義表の ②-12・④-9 の「写す元」と「読むプログラム」を、いまの形に合わせる（2回 呼んでも同じ物）
    for no in ("②-12", "④-9"):
        e = next(x for x in t["要素"] if x["番号"] == no)
        e["写す元"] = e["写す元"].replace("（observe_diag.build_catalog）", "（observe_diag._catalog_from_config＝写す元の関数・162番まで）")
        if "observe_diag.build_catalog" not in e["読むプログラム"]:
            e["読むプログラム"] = list(e["読むプログラム"]) + ["observe_diag.build_catalog"]

~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:835「for no, add in (("②-9", SRC29_ADD), ("③-5", SRC35_ADD)):」
状態: 確定

#### 実装 11
対象のファイル: .claude/state/indicator_review/gen_indicators_draft.py
直す箇所: 写すプログラムの PART_SRC（F-4）＝部品の記録の出どころの文を、帯の for の在りか（_catalog_from_config）に合わせる（当てた後の --rewrite で indicators.json の部品の記録8件に入る）
直す前の文字:
~~~
PART_SRC = "observe_diag.py の _BAND_IMPL（帯の計算式の表）と build_catalog の帯の for"

~~~
直した後の文字:
~~~
PART_SRC = "observe_diag.py の _BAND_IMPL（帯の計算式の表）と _catalog_from_config の帯の for（161-2 の前は build_catalog の中に在った）"

~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:128「PART_SRC = "observe_diag.py の _BAND_IMPL（帯の計算式の表）と build_catalog の帯の for"」
状態: 確定

#### 実装 12
対象のファイル: .claude/state/indicator_review/gen_indicators_draft.py
直す箇所: 写すプログラムの頭の説明（F-4）＝列の並びの写す元を _catalog_from_config と書く
直す前の文字:
~~~
    12 いまのカタログの列の並び（observe_diag.build_catalog＝列を作る組 ②-12・④-9・171番まで）

~~~
直した後の文字:
~~~
    12 いまのカタログの列の並び（observe_diag._catalog_from_config＝写す元の関数・162番まで＝列を作る組 ②-12・④-9・171番まで。161-2 から build_catalog はこれを読む）

~~~
根拠の抜き書き: .claude/state/indicator_review/gen_indicators_draft.py:16「12 いまのカタログの列の並び（observe_diag.build_catalog＝列を作る組 ②-12・④-9・171番まで）」
状態: 確定

#### 実装 13
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py
直す箇所: H2 の印の対象 WATCHED（F-5）＝読む口と1つのデータを足す
直す前の文字:
~~~
    f"{_PR}/observe_diag.py", f"{_PR}/observe_config.json",

~~~
直した後の文字:
~~~
    f"{_PR}/observe_diag.py", f"{_PR}/observe_config.json",
    # ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-5）＝build_catalog が、読む口と1つのデータから列を作るようになったので、
    #   この2本が変われば材料の列が変わりうる＝印の対象に足す（2026-08-20 に observe_diag.py を足したときと同じ理由）。
    f"{_PR}/indicators/indicators.json", f"{_PR}/indicators/indicators.py",

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/leak_causality_diag.py:255「f"{_PR}/observe_diag.py", f"{_PR}/observe_config.json",」
状態: 確定

#### 実装 14
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py
直す箇所: gen_materials の鍵を拾う口 _catalog_keys の説明（F-6）
直す前の文字:
~~~
    """`observe_diag.build_catalog` が読む設定の鍵を、コードから機械で拾う。

~~~
直した後の文字:
~~~
    """`observe_diag._catalog_from_config`（列を作る組の写す元＝設定から列を作る関数・162番まで）が読む設定の鍵を、コードから機械で拾う。

    ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-6）＝build_catalog は読む口の列を作る組から作り、設定の鍵を読まない。
      設定の鍵（決まった数字の並び）が列を決めるのは、写すプログラムが写す元の関数から列を作る組を作り直すときなので、その関数を数える。

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py:455「"""`observe_diag.build_catalog` が読む設定の鍵を、コードから機械で拾う。」
状態: 確定

#### 実装 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py
直す箇所: gen_materials の鍵を拾う口 _catalog_keys（F-6）＝見る関数を _catalog_from_config にする
直す前の文字:
~~~
               if isinstance(n, ast.FunctionDef) and n.name == "build_catalog"), None)

~~~
直した後の文字:
~~~
               if isinstance(n, ast.FunctionDef) and n.name == "_catalog_from_config"), None)

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py:465「if isinstance(n, ast.FunctionDef) and n.name == "build_catalog"), None)」
状態: 確定

#### 実装 16
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py
直す箇所: gen_materials の自己テスト T12（F-6）＝鍵の読みを足す相手の関数を _catalog_from_config にする
直す前の文字:
~~~
        _od12 = _od12.replace("def build_catalog(cfg: dict) -> list[tuple]:\n",
                              "def build_catalog(cfg: dict) -> list[tuple]:\n"
                              '    _zzz_uso = cfg["zzz_uso_periods"]\n', 1)

~~~
直した後の文字:
~~~
        _od12 = _od12.replace("def _catalog_from_config(cfg: dict) -> list[tuple]:\n",
                              "def _catalog_from_config(cfg: dict) -> list[tuple]:\n"
                              '    _zzz_uso = cfg["zzz_uso_periods"]\n', 1)

~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_materials.py:2478「_od12 = _od12.replace("def build_catalog(cfg: dict) -> list[tuple]:\n",」
状態: 確定

#### 実装 17
対象のファイル: .claude/breaks/b222_catalog_drops_last_set.sh
直す箇所: 壊すプログラム b222（7-6 の F-1 の1行目）＝build_catalog が列を作る組の最後の1組を作らないと、カタログの自己テストが落ちる（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_catalog が、読む口の列を作る組の最後の1組を作らない形にする＝名前の並びが写す元の関数と違い、カタログの自己テストが落ちる
# EXPECT_MSG: [材料カタログ] build_catalog の名前の並びが、写す元の関数と違う
# b222_catalog_drops_last_set — build_catalog が列を作る組を1組でも落とすと、カタログの自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-1 の1行目）
#   守っているもの＝7-6 の F-1 の1行目（測るコマンドは、完成の条件と同じ＝observe_diag.py --selftest-catalog）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    for cs in _ind.load().column_sets():\n'
new = '    for cs in _ind.load().column_sets()[:-1]:\n'
if s.count(old) != 1:
    raise SystemExit("[b222_catalog_drops_last_set] 壊す対象（列を作る組を回す行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: やることの表 7-6 の F-1 の1行目「壊し方＝build_catalog が、列を作る組の最後の1組を作らない形にする」
状態: 確定

#### 実装 18
対象のファイル: .claude/breaks/b223_catalog_reads_old_key.sh
直す箇所: 壊すプログラム b223（7-6 の F-1 の2行目）＝build_catalog が設定の鍵を読むと、カタログの自己テストが落ちる（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_catalog に、設定の古い鍵 rsi_periods を読む行を足す＝構文の木の照らしが当たり、カタログの自己テストが落ちる
# EXPECT_MSG: [材料カタログ] build_catalog が設定の鍵を読んでいる
# b223_catalog_reads_old_key — build_catalog が設定の鍵を読む形に戻ると、カタログの自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-1 の2行目・集約の要件定義書 R6）
#   守っているもの＝7-6 の F-1 の2行目（測るコマンドは、完成の条件と同じ＝observe_diag.py --selftest-catalog）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/observe_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    _bfl = _band_fee_floor(cfg)\n    C = []\n    for cs in _ind.load().column_sets():\n'
new = '    _bfl = _band_fee_floor(cfg)\n    _zzz_rsi = cfg["rsi_periods"]\n    C = []\n    for cs in _ind.load().column_sets():\n'
if s.count(old) != 1:
    raise SystemExit("[b223_catalog_reads_old_key] 壊す対象（build_catalog の床と列を作る組を回す行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$PR/observe_diag.py" --selftest-catalog
finish

~~~
根拠の抜き書き: やることの表 7-6 の F-1 の2行目「壊し方＝build_catalog に、cfg["rsi_periods"] を読む行を足す」
状態: 確定

#### 実装 19
対象のファイル: .claude/breaks/b224_reader_sets_no_reg.sh
直す箇所: 壊すプログラム b224（7-6 の F-2）＝column_sets が登録の名前を返さないと、読む口の自己テストが落ちる（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 読む口の column_sets が、組ごとの計算の登録の名前を返さない形にする＝読む口の自己テストが落ちる
# EXPECT_MSG: ❌ 列を作る組は、組ごとに計算の登録の名前も返す
# b224_reader_sets_no_reg — 列を作る組に計算の登録の名前が無いと、読む口の自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-2）
#   守っているもの＝7-6 の F-2（測るコマンドは、完成の条件と同じ＝indicators.py --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/indicators/indicators.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '                                "登録の名前": reg})\n'
new = '                                })\n'
if s.count(old) != 1:
    raise SystemExit("[b224_reader_sets_no_reg] 壊す対象（列を作る組に登録の名前を入れる行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish

~~~
根拠の抜き書き: やることの表 7-6 の F-2「壊し方＝返り値から登録の名前を外す」
状態: 確定

#### 実装 20
対象のファイル: .claude/breaks/b225_draft_source_is_catalog.sh
直す箇所: 壊すプログラム b225（7-6 の F-3・F-4）＝写すプログラムの写す元が build_catalog に戻ると、自己テストが落ちる（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: 写すプログラムの catalog_sets の呼び先を build_catalog に戻す＝写す元が indicators.json 自身になり、写すプログラムの自己テストが落ちる
# EXPECT_MSG: ❌ 写す: 写す元は _catalog_from_config で、build_catalog を呼ばない
# b225_draft_source_is_catalog — 写すプログラムの写す元が build_catalog に戻ると、自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-3・F-4）
#   守っているもの＝7-6 の F-3・F-4（測るコマンドは、完成の条件と同じ＝写すプログラムの --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$ROOT/.claude/state/indicator_review/gen_indicators_draft.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    cat = od._catalog_from_config(cfg)                    # 写す元＝設定から列を作る関数（162番まで・161-2 のやることの表 F-4）\n'
new = '    cat = od.build_catalog(cfg)\n'
if s.count(old) != 1:
    raise SystemExit("[b225_draft_source_is_catalog] 壊す対象（catalog_sets の写す元の行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish

~~~
根拠の抜き書き: やることの表 7-6 の F-3・F-4「壊し方＝catalog_sets の呼び先を build_catalog に戻す」
状態: 確定

#### 実装 21
対象のファイル: .claude/breaks/b226_h2_watch_no_indicators.sh
直す箇所: 壊すプログラム b226（7-6 の F-5）＝H2 の印の対象から読む口と1つのデータを消すと、完成の条件が落ちる（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: H2 の印の対象（WATCHED）から、読む口と1つのデータの行を消す＝grep の数が 0 になり、完成の条件が落ちる
# EXPECT_MSG: leak_causality_diag.py:0
# b226_h2_watch_no_indicators — H2 の印が indicators.json を見張らなくなると、完成の条件が落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-5）
#   守っているもの＝7-6 の F-5（測るコマンドは、完成の条件と同じ＝grep -H -c で数え、0 なら終わりのコード 1）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/leak_causality_diag.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    f"{_PR}/indicators/indicators.json", f"{_PR}/indicators/indicators.py",\n'
new = ''
if s.count(old) != 1:
    raise SystemExit("[b226_h2_watch_no_indicators] 壊す対象（WATCHED の読む口と1つのデータの行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure grep -H -c -F 'indicators/indicators.json' "$PR/leak_causality_diag.py"
finish

~~~
根拠の抜き書き: やることの表 7-6 の F-5「壊し方＝WATCHED から indicators.json の行を消す」
状態: 確定

#### 実装 22
対象のファイル: .claude/breaks/b227_materials_keys_from_catalog.sh
直す箇所: 壊すプログラム b227（7-6 の F-6）＝鍵を拾う口が見る関数を build_catalog に戻すと、gen_materials の自己テスト T12 が落ちる（新しいファイル）
直す前の文字:
~~~
なし
~~~
直した後の文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: gen_materials の鍵を拾う口が見る関数を build_catalog に戻す＝写す元の関数に鍵の読みを足しても場所1 が増えず、gen_materials の自己テスト T12 が落ちる
# EXPECT_MSG: T12: 場所1 に架空の数の並びを1つ 足しても件数が1 増えない
# b227_materials_keys_from_catalog — 場所1 の数え方が写す元の関数を見なくなると、gen_materials の自己テストが落ちる（工事 m2c15-catalog-redirect-20261101・やることの表 7-6 の F-6）
#   守っているもの＝7-6 の F-6（測るコマンドは、完成の条件と同じ＝gen_materials.py --selftest）
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。lib.sh の guard が控えを取り、必ず戻す。
source "$(dirname "$0")/lib.sh"

F="$SDK/scripts/priority_rebuild/gen_materials.py"
guard "$F"

python3 - "$F" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '               if isinstance(n, ast.FunctionDef) and n.name == "_catalog_from_config"), None)\n'
new = '               if isinstance(n, ast.FunctionDef) and n.name == "build_catalog"), None)\n'
if s.count(old) != 1:
    raise SystemExit("[b227_materials_keys_from_catalog] 壊す対象（鍵を拾う口が見る関数の名前の行）が1か所でない")
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$F" --selftest
finish

~~~
根拠の抜き書き: やることの表 7-6 の F-6「壊し方＝_catalog_keys が見る関数の名前を build_catalog に戻す」
状態: 確定

<!-- ACC_IMPL_END -->

［自動］CC が書いて、まこさんが OK した案の【番号】の「非該当＝」の後ろの文と、項目の正本の名前
**非該当の項目（理由と出どころ）**＝4-22 検査やプログラムを直す工事で書く5つ＝種類①の工事（直すファイルの一覧から、プログラムが決めた）／4-8 データ構造（表や JSON の列と中身を、新しく作るか・変えるか）＝一覧に種類「作る」の行が無い（F-1〜F-6 は、どれも在るファイルを直す）。読む口の column_sets の返り値に足す欄（登録の名前）は、F-2 と 4-19 に書いた。／4-11 時刻の扱い（時間帯・足の区切りをどこで切るか）＝この工事は、時刻と足の区切りを扱いません。build_catalog は列の名前と計算を組むだけで、時間足と足の区切りは build_features が扱います（observe_diag.py:1792〜2229 に timeframes が無い）。

### 4-A この節に何を書いたか（一覧）

［自動］項目の正本と、OK された案・やることの表の有無
| 番号 | 段 | 項目 | 書いたか |
|---|---|---|---|
| 4-0 | 必ず | この仕組みは何か（全体・一続きの文章で書く） | 書いた |
| 4-1 | 必ず | システムの境界（誰が動かし、誰が結果を使うか） | 書いた |
| 4-2 | 必ず | 入力と出力（受け取るもの・出すもの・その形） | 書いた |
| 4-6 | 必ず | 制約（従う決まりの全件と、その出どころ） | 書いた |
| 4-22 | 条件 | 検査やプログラムを直す工事で書く5つ | 非該当（種類①の工事（直すファイルの一覧から、プログラムが決めた）） |
| 4-3 | 必ず | 部品と責任の割り当て（どの部品が何をやるか） | 書いた |
| 4-4 | 必ず | 処理の流れ（うまくいったとき、何がどの順に起きるか） | 書いた |
| 4-19 | 必ず | この工事で何が変わるかを、1件に当てはめて示した例 | 書いた |
| 4-7 | 必ず | 探索の範囲（決める値と、その探し方＝範囲・並び・本数） | 書いた |
| 4-9 | 条件 | 設定（走らせる人が指定できる項目＝設定ファイルの値・コマンドの旗） | 書いた |
| 4-21 | 条件 | 新しく入る数字と式の一覧（1件ずつの出どころ） | 書いた |
| 4-12 | 必ず | 出る結果の姿（完成したとき、何がどう表示されるか） | 書いた |
| 4-5 | 必ず | 異常系（途中で止まったとき・入力が壊れていたとき、どうなるか） | 書いた |
| 4-8 | 条件 | データ構造（表や JSON の列と中身を、新しく作るか・変えるか） | 非該当（一覧に種類「作る」の行が無い（F-1〜F-6 は、どれも在るファイルを直す）。読む口の column_sets の返り値に足す欄（登録の名前）は、F-2 と 4-19 に書いた。） |
| 4-10 | 条件 | 保存先（出したものをどこに置くか・上書きか、書き足すか） | 書いた |
| 4-23 | 条件 | 置き場の地図（直す前と後） | 書いた |
| 4-11 | 条件 | 時刻の扱い（時間帯・足の区切りをどこで切るか） | 非該当（この工事は、時刻と足の区切りを扱いません。build_catalog は列の名前と計算を組むだけで、時間足と足の区切りは build_features が扱います（observe_diag.py:1792〜2229 に timeframes が無い）。） |
| 4-14 | 条件 | 性能（どれくらい時間が掛かり、どれくらい容量を使うか） | 書いた |
| 4-15 | 条件 | 競合（同時に2つ走らせたときに、同じファイルを奪い合わないか） | 書いた |
| 4-16 | 条件 | セキュリティ（人に見せてはいけない値と、書き換えられては困る記録） | 書いた |
| 4-17 | 省ける | ログと進捗表示（走っている途中に何を画面へ出すか・何を記録に残すか） | 書いた |
| 4-13 | 必ず | 影響範囲（この直しで、ほかのどれが壊れるか） | 書いた |
| 4-18 | 省ける | 再利用（手本にした、既にあるものの形） | 書いた |
| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 22 件・プログラムが作る） |


## 5｜決めたことと理由・捨てた案

［自動］CC が書いて、まこさんが OK した案の【5】
| # | 決めたこと | 理由 | 捨てた案 |
|---|---|---|---|
| 1 | 直す前の build_catalog の中身を、写す元の関数 _catalog_from_config として残す（F-3） | 写すプログラムの写す元が indicators.json 自身になるのを防ぎ、161-1 で決まった「162番までは写す元で直して作り直す」（修正14 案B）を変えずに済む。技術のやり方なので CC が決め、設計書の監査で問う（まこさん「よい」2026-11-01） | 写すプログラムが②-12・④-9 を作り直さず、indicators.json を正本にする形（162番より前に、設定の鍵を直しても列に届かなくなり、修正14 案B と食い違う） |
| 2 | build_catalog から読む口の calc を呼ばず、make_material と _band_material を使う（Y-5） | calc はオフの指標を返さない（indicators.py:311〜312）が、列を作る組はオフの250組を持つ。calc が返す関数と make_material の関数は同じ計算の登録の同じ行。calc は観察の道具を import し直すので、観察の道具を __main__ で走らせたときと spec_from_file_location で読み込んだとき（gen_signal_families.py:55〜57）に、観察の道具が2重に読み込まれる。calc が返す帯の計算式は床を設定ファイルから読む（observe_diag.py:731〜740）ので、渡した設定の床を結び付ける（CP83 の修正14 案B）には _band_material が要る | calc がオフの指標も返す形に直す（決まり⑤と要件6 の「オフの指標は、どのロジックからも使えない」に反する） |
| 3 | column_sets が組ごとに計算の登録の名前を返す（F-2） | 記録の名前と登録の名前が違う記録が、組を持つ記録のうち54ある（全記録では56）。build_catalog が要素の名前（計算の関数）をコードに書いて引くと、決まり①（要素の名前をコードに書かない）に反する | build_catalog が記録の計算の関数の要素を直に引く形 |
| 4 | H2 の印の対象に indicators.json と indicators.py を足す（F-5） | build_catalog がこの2本から列を作るので、2本が変われば材料の列が変わりうる。足さないと、indicators.json を直しても H2 の印が合ったままになる | 足さない形 |
| 5 | 要素の定義表の ②-12・④-9 と部品の記録の出どころの文を、写すプログラムで合わせる（F-4） | 同じ事実（列を作る組の写す元と読む所）を書く場所を揃える（恒久72番の2）。indicators.json は手で直さず、写すプログラムで作り直す（161-1 の修正14 案B） | 文を直さずに 162番まで残す形（indicators.json の説明が事実と違ったままになる） |
| 6 | gen_materials の場所1 を、写す元の関数で数える（F-6） | 設定の鍵が列を決めるのは、写す元の関数を通して写すプログラムが組を作り直すときだから。数は直す前と同じ | 読む口の列を作る組で数える形（場所1 の意味が変わり、materials.md の作り直しが要る） |
| 7 | 列の比べは、完成の条件でなく、当てた後の手順（4-4 の5）で行う | 約61分かかり、当てた直後の仮当てでは走らせられない（案のひな型 :193） | 完成の条件に入れる形 |
| 8 | 監査の前の検査の指紋の直しは、この設計書に入れない（Y-6） | .claude/tools の直しは、インフラの直しで、設計書と監査が要らない（2026-10-20 の決定の2） | この設計書に入れる形 |

## 6｜テストとリスクと見積もり

### 6-1 わざと壊して止まるか試すテスト

［自動］CC が書いて、まこさんが OK した案の【7-6】の壊し方の欄
<!-- ACC_SELFTEST_START hash=281440e1c6d40e63 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝まこさんが OK した案の【7-6】。

| 壊すプログラム | 守る行 | 壊し方 |
|---|---|---|
| `b222_catalog_drops_last_set.sh` | #1 | build_catalog が、列を作る組の最後の1組を作らない形にする |
| `b223_catalog_reads_old_key.sh` | #2 | build_catalog に、cfg["rsi_periods"] を読む行を足す |
| `b224_reader_sets_no_reg.sh` | #3 | 返り値から登録の名前を外す |
| `b225_draft_source_is_catalog.sh` | #4 | catalog_sets の呼び先を build_catalog に戻す |
| `b226_h2_watch_no_indicators.sh` | #5 | WATCHED から indicators.json の行を消す |
| `b227_materials_keys_from_catalog.sh` | #6 | _catalog_keys が見る関数の名前を build_catalog に戻す |

**★終了コードは、承認のプログラムが実際に走らせて記録します。**0 以外だったときだけ、その行を「済」にできます。

<!-- ACC_SELFTEST_END -->

### 6-2 リスク

［自動］CC が書いて、まこさんが OK した案の【6-2】
| # | リスク | どうするか |
|---|---|---|
| 1 | 観察の道具の2重の読み込み | build_catalog は読む口を import するだけで、calc を呼ばない。読む口は calc を呼んだときだけ観察の道具を import する（indicators.py:73〜87・:301〜306） |
| 2 | 読む口は1回だけ読む（indicators.py:366〜378） | 同じ走行の中で indicators.json を書き替えても、build_catalog は前に読んだ物を使う。写すプログラムの --rewrite は、F-4 の後は build_catalog を呼ばないので、この形で困る所は無い |
| 3 | 同じ名前のモジュール | cat/indicators.py は「cat.indicators」として読まれる（strategies/cat_v9_decider.py:25）ので、読む口の「indicators」とぶつからない |
| 4 | materials.md の説明の文が古くなる | Y-13。162番で写す元の関数を消すときに直す |
| 5 | 閉じた工事の壊すプログラム b137・b128 の前提が変わる | 照らし⑮が写す元の関数を呼ぶので、b137 は期待の文で落ち、b128 は⑮の文で落ちる（期待の文「❌ K-1:」と違う）。承認では走らない（Y-7）。161-2 の守りは b222〜b227 |

### 6-3 見積もり

［自動］CC が書いて、まこさんが OK した案の【6-3】
| 何 | 見込み | 根拠 |
|---|---|---|
| 当てる・7-6 の6行 | 約3分 | 【4-14】の自己テストの時間の合計 |
| --rewrite・--verify・G2・H2 | 約10分 | 【4-14】 |
| 列の比べ | 約61分 | 【4-14】 |
| 監査に出す前のチェック | 約12分 | 【4-14】 |

**★どれか1つでも見込みの2倍を超えたら、そこで止めて まこさんに報告します。**

**6-4 この設計書が受けた設計書の監査**＝`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-11-01_m2c15_catalog_redirect_20261101_design_cp96_audit_report.md`（結果ファイルの名前から、プログラムが見つけた。修正の指示は、結果ファイルの8番の節に在る）

### 6-5 確かめていないこと（CC がやっていない確かめ）

［自動］CC が書いて、まこさんが OK した案の【確かめていないこと】
| # | 確かめていないこと | なぜ確かめていないか | 確かめるなら、何を走らせるか |
|---|---|---|---|
| 1 | 列の比べで、列の名前・並び・値が直す前と同じこと（155-1） | 約61分の走行で、承認の後・まこさんの OK の後に走らせる（4-4 の5） | python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/col_snapshot.py --compare /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/col_snapshot/before_20261024.json |
| 2 | G2 で、型の表と承認の指紋が変わらないこと | 当てた後に走らせる（4-4 の4） | python3 scripts/priority_rebuild/gen_signal_families.py --verify |
| 3 | materials.md の場所1 の数が、直す前と同じこと | gen_materials の --verify を、当てた後に走らせていない | python3 scripts/priority_rebuild/gen_materials.py --verify |
| 4 | --rewrite が出す「違う所」が、要素の定義表の ②-12・④-9 と部品の記録8件の出どころの10か所だけであること | 当てた後に走らせる（4-4 の3）。indicators.json で build_catalog を書く所は10か所（grep -c・2026-11-01） | python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/indicator_review/gen_indicators_draft.py --rewrite（SDK の直下） |
| 5 | 監査の前の検査の指紋に indicators/ の2本を足す直し | インフラの直し（Y-6）で、承認の後に行う | 直した後に python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/pre_audit_check.py --run |

## 7｜付録（hook が求める項目）

### 7-1 深掘り4点

［自動］CC が書いて、まこさんが OK した案の【7-1】
この工事が解く問題＝列を作る所（build_catalog）は、161-1 で indicators.json に入れた列を作る組を読まず、設定ファイルの古い鍵 約40個と material_params から列を作っているので、indicators.json を直しても列に届かない。この工事（161-2）は、build_catalog を読む口の列を作る組から列を作る形にし、列の名前・並び・値が直す前と同じかを比べる。（プログラムが、§1 概要の1文目を写した）

**① 真因（root cause）**＝161-1 で列を作る組を indicators.json に入れたが、build_catalog を同じ設計書で直せなかった（当てた直後の indicators.json が古い形で、承認の前の検査が走らせる観察の道具の自己テストが落ちる＝worklog 20261031:495）。そのため、列を作る所がまだ設定の鍵を読み、indicators.json を直しても列に届かない（要件 core_requirements_full.md:85・集約の要件定義書 R6 と違う）

**② 期待値分解**＝売買に触らない工事＝［自動］目標の③④の写し

**③ root か symptom か**＝root。列を作る所の読み元そのものを、設定の鍵から読む口の列を作る組に替える。代表の値と範囲から列を作る形（171番・M2-E-8）は別の工事

**④ ベースアップ**＝233回目の読むもの宣言40件（指標の構造の要件定義書・集約の要件定義書の §5・§7・§8・§10・161-1 の やることの表と設計書の控え・CP95 の §7・§8・読む口・indicators.json・observe_diag.py の帯と計算の登録と build_catalog とカタログの自己テスト・col_snapshot.py と控え・写すプログラム・gen_materials の鍵を拾う口・H2 の対象・監査の前の検査の指紋・承認の前の検査の自己テスト・b137・value_conflicts・fix_inventory）。WebSearch は使っていない（値を新しく調べない工事のため）

### 7-2 ★疑似シミュ由来の固定値ゼロ宣言

［自動］CC が書いて、まこさんが OK した案の【7-2】
この工事は、疑似シミュ由来の固定値を1つも入れません。列は、161-1 で写した列を作る組（いまのカタログの列の写し）から作ります。コードの中の数字は、壊すプログラムの切り方と決まった文、説明の文の日付と番号だけです。

### 7-3 変更の単位（H16）

［自動］CC が書いて、まこさんが OK した案の【7-3】
変更の単位は「列を作る所（build_catalog）の読み元を、設定の鍵から読む口の列を作る組に替える（それに伴い、写すプログラムの写す元・H2 の印の対象・gen_materials の数える相手を付け替える）」の1つです。代表の値と範囲から列を作る形（171番・M2-E-8）・engine_tuner の経路の7本（171番）・残りの24本（170番）・元の置き場と写す元の関数を消す（162番）・閾値と代表の値を写す（70番）は別の工事です。

### 7-3b 要件の「作ってはいけないもの」との照合（恒久の決まり §1）

［自動］左の2列は要件定義の8番（正本）・右の2列は CC が書いて、まこさんが OK した案の【7-3b】
| # | 作ってはいけないもの（要件定義の8番） | 根拠 | 確かめ直すコマンド |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの。 | この工事は条件をつなぎません。列を作る所の読み元を替えるだけです。実装の指示に乱数の語は0件です | grep -c -e random -e rng /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/verbatim/m2c15-catalog-redirect-20261101/impl_4-20_20261101.json |
| 2 | 探す値を、CC が先に決まった数字の一覧で限定するもの。 | 探す値を一覧で新しく限定しません。列を作る組は、いまのカタログの列をそのまま写した物で、171番まで列を変えないための物です（Y-4）。列の名前と並びが直す前と同じことを、カタログの自己テストの照らし（⑮）と列の比べで見ます | python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog |

### 7-4 塞げないもの

［自動］CC が書いて、まこさんが OK した案の【7-4】
| 問い | 塞げないこと |
|---|---|
| **照らし⑮は値まで見るか** | 見ない。名前と並びだけを見る。値は、列の比べ（約61分）で見る |
| **照らし⑯は、関数を通した設定の読みまで見るか** | 見ない。build_catalog の中の cfg[...]・cfg.get(...) だけを見る。cfg を渡す関数（_band_fee_floor）の中の読みは見ない（床の倍数は、この形で読むと決めた物） |
| **写す元の関数と build_catalog が同じ列を作るか** | 名前と並びは⑮が見る。計算の関数は、どちらも同じ計算の登録から取る（make_material・_band_material）が、値が同じかは列の比べで見る |
| **閉じた工事の壊すプログラム b137・b128** | 前提が変わる。照らし⑮が写す元の関数を呼ぶので、b137 は期待の文で落ち、b128 は⑮の文で落ちる（期待の文「❌ K-1:」と違う＝走らせると期待と違う結果になる）。消さない（Y-7） |
| **監査 cp14 の Q5 の1＝照合D は中身を見るか** | 見ない。名前が在るかだけを見る。中身は 7-6 の6行と壊すプログラム6本と、当てた後の --verify・列の比べで見る |
| **監査 cp14 の Q5 の2＝照合A・B は循環していないか** | impl_functions は、直す前の文字が入る関数を def の行から確かめて書いた。照合A は、触った関数が impl_functions に在るかを見る。設計の中身は設計書の監査で見る |
| **監査 cp14 の Q5 の3＝must_use_from を使うか** | 使わない。must_use は、カタログの自己テストが呼ぶ関数（build_catalog・_catalog_from_config・load_config・find_material）を書く |
| **監査 cp14 の Q5 の4＝Bash の止めを抜ける打ち方は無いか** | 変数から組んだコマンドなどは門の語の外に出うる。この工事は当てる道具でだけ書く |
| **監査 cp14 の Q5 の5＝承認の記録を消したら門は通るか** | 通る。手で消す・書き替えることは門では見抜けない。git の差で後から見る |

### 7-5 §4.6 ハード制約の照合

［自動］項目は hook の実体から抽出・答えは CC が書いて、まこさんが OK した案の【7-5】
<!-- ACC_CHECKLIST_START hash=efbab2e13cb9fb27 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`list_banned_words.checklist_items()`（hook の実体から抽出）。

| # | 項目（hook の実体から抽出） | この工事での答え（OK された案の【7-5】） |
|---|---|---|
| 1 | 【群1】`TARGET: scripts/priority_rebuild/<1ファイル>.py`（編集する実体1ファイル。複数ファイルに跨るなら分割 or 主ファイル＋やることに明記） | TARGET は、やることの表の「直す」の行の5本（observe_diag.py・indicators.py・gen_indicators_draft.py・leak_causality_diag.py・gen_materials.py）です（設計書を作るプログラムが一覧から作る）。 |
| 2 | 【群1】`DESIGN_CONTRACT`（fenced json）= `impl_file` / `self_check_calls`（実装ソースに文字列で在る識別子）/ 必要なら `must_combine` | DESIGN_CONTRACT は【7-8】に書きます。impl_file は observe_diag.py で、impl_functions は直す関数（observe_diag.py の build_catalog・_catalog_from_config・selftest_catalog、indicators.py の <モジュール直下>（使い方の説明の行）・Indicators.column_sets・selftest、gen_indicators_draft.py の <モジュール直下>（PART_SRC と頭の説明）・build_old・catalog_sets・table_update・selftest、leak_causality_diag.py の <モジュール直下>（WATCHED）、gen_materials.py の _catalog_keys・selftest）です。名前は、仮当て（A12）の照合A が出した名前に合わせました。 |
| 3 | 【群1】★新しくファイルを作るときだけ足す2行（2026-08-27・まこさん承認「進めて良い」・86番の直し）＝`NEW_FILE: <新しく作るファイルのパス>`（カンマ区切りで複数可）と `MODEL: <手本にしたファイ | NEW_FILE は、7-6 の壊すプログラム6本（b222〜b227）で、プログラムが足します。MODEL は .claude/breaks/b137_material_params_ignored.sh です。 |
| 4 | 【群1】① 真因（root cause・損/不足の構造的原因） | 真因は【7-1】に書きました。 |
| 5 | 【群1】② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか） | 期待値分解は【7-1】に書きました。 |
| 6 | 【群1】③ root か symptom か（最易パッチ＝symptom 患いを避ける・Y/N＋理由） | root か symptom かは【7-1】に書きました（root）。 |
| 7 | 【群1】④ ベースアップ（参照した KB / WebSearch の証跡・記憶ベース禁止） | ベースアップは【7-1】に書きました。 |
| 8 | 【群1】変更は 1レバーか（複数混ぜない） | 1レバーです。列を作る所の読み元を替えることだけで、指標の値・列の名前と並び・計算の式は変えません。 |
| 9 | 【群1】過去に破棄した失敗（lessons / 破棄した E / 6軸）を再演していないか（する場合は差分を1行） | 過去の失敗を再演しません。前の回の誤り（--verify の後にファイルを消し、走らせ直さずに commit した＝worklog 20261101:212）は、4-4 の7（commit の直前に走らせ直す）で防ぎます。 |
| 10 | 【群1】新しい部品・前処理を足すときは、H2（`leak_causality_diag.py`）が走らせる案（`tuner_recipes`）にその部品が入るかを開いて示す。入らないなら「H2 で測る」と書かず、番人に打ち切り（ | 非該当です。案を作るプログラムに、新しい部品・前処理を足しません。 |
| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R | 直すファイルに engine_tuner_exec.py・engine_tuner_gen.py は入りません。build_catalog を呼ぶ側は、出力の形が同じなので直しません。 |
| 12 | 【群1】直すファイルの名前そのもので壊すプログラムを grep する（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、 | 直すファイルの名前で .claude/breaks を grep すると、observe_diag.py を名指す壊すプログラムが約70本 当たります。壊す相手の行（old の1行目）が build_catalog の範囲（:1792〜2229）に在るのは b137・b128 の2本で、閉じた工事の物なので直しません（Y-7）。ほかは各指標の式を壊す物で、build_catalog の行を壊しません。 |
| 13 | 【群1】壊すプログラムが測るコマンドが、本物の結果の置き場（results/ ほか）や帳簿に書くなら、guard で控えに写すか、測った後に壊した道具が書いたファイルを消す形にする（監査 CP49＝b97 は --purpose | 壊すプログラム6本が測るのは、自己テストと grep だけで、結果の置き場に書きません。壊す相手は lib.sh の guard が控えを取り、必ず戻します。 |
| 14 | 【群1】実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前） | 新しく足す関数（def）は、observe_diag.py の _catalog_from_config だけです（中身は直す前の build_catalog）。build_catalog は中身を置き替えます。 |
| 15 | 【群1】新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-che | 新しく足すコマンドの旗と設定の鍵はありません。 |
| 16 | 【群1】実装の後に設計書を作り直して2回目の承認に出すときは、実装の中で変わった手順（やらなかった手順・後に回した手順）を、元データの 4-4・やらないこと・4-7〜4-9・4-13・4-19・見積もり・まこさんの決定に書き直し | 実装の後に設計書を作り直すときは、変わった手順を 4-4・やらないこと・4-13・4-19・見積もりに書き直してから作り直します。 |
| 17 | 【群1】★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）: probe（疑似シミュ・静的後処理）は あたりを付ける専用＝決定的根拠でない。設 | 固定値ゼロの宣言は【7-2】に書きました。 |
| 18 | 【群1】★ARC マーカー（改善アーク自動生成の源・まこさん指示 2026-06-27）: acceptance に機械可読 ARC マーカーを1ブロック入れる＝承認時に approve_impl が `.claude/ratc | ARC の行は、設計書を作るプログラムが入れます。 |
| 19 | 【群1】H16 1変更・過去失敗の不再演 | 1変更です（8つ目の答え）。過去の失敗は、9つ目の答えのとおり再演しません。 |
| 20 | 【群1】自己検査を列挙（恒等 / 会計保存 / cap / leak grep 等・「わざと壊して落ちるか」のメタ確認 §2.9③） | 自己検査は、7-6 の6行（観察の道具の --selftest-catalog・読む口と写すプログラムと gen_materials の --selftest・grep）と、壊すプログラム6本と、当てた後の --verify・G2・H2・列の比べです。 |

- 【群2】既定 OFF で恒等（新パラメータ None 等で既存ベースと完全一致）を設計で保証し、自己検査で確認するか
- 【群2】新しい exit_reason を出すか？ → YES なら「やること」に score.py の MAKER_EXIT_REASONS / TAKER_EXIT_REASONS へ登録 ＋ 既知答えテスト再pass」を含
- 【群2】entry/exit のコスト種別（maker/taker）が変わるか？ → eval_engine / score の分類と一致するか確認
- 【群2】judge（score.py / eval_engine）の計算式に触れるか？ → 原則触らない（H13）。触るなら既知答えテスト再pass を必須に
- 【群2】新スクリプト名・出力CSV名は pdca 命名規約に乗るか（実験= strat_/train_/measure_/e3N_ ／ 分析= *_probe / *_deep_analysis ／ 審判= score.py C
- 【群2】使用パラメータ・Entry/Exit ロジックのサイドカー出力を含めるか（新戦略は必須・2026-06-19）→ 売買記録CSVの隣に `<stem>_params.json` を `params_sidecar.wri
- 【群2】出力は共通の書き出し処理を使うか（命名/archive/上書き防止の踏襲・2026-06-22 まこさん確定・全戦略汎用）→ 新しい戦略（e37/38/39…）は売買記録を共通の書き出し処理 `_output_and_r
- 【群2】共通土台 `strat_base.py` を import するか（2026-06-23 新設・中立）→ 新戦略は `strat_base` から ①load_5m ／ ⑤_verify_cap・_funding_cos
- 【群2】H1 cap 合計 0.12 BTC（_verify_cap / score.assert_hard_constraints で実測）
- 【群2】H2 leak なし（特徴量 t 時点・`shift(-`/`center=True` grep assert・学習末 < 採点始）
- 【群2】H5 約定モデル（entry 指値maker・TTL3 / 出口 TP・SL=maker / TIME・能動=taker+slip）
- 【群2】H6 価格非依存（%/比率/BTC 単位・USD 絶対値の閾値/ラベル禁止）
- 【群2】H8 期間分割（学習窓で fit・採点窓は評価のみ・封印は不参照・値決め窓で選んだ値は確認窓で選び直さない）。実値は下の機械生成の表＝`gen_windows.py` が periods.py から差し込む（手で数字を書
- 【群2】H13 judge 固定（score.py/eval_engine は実験で改造しない・改造時 既知答えテスト再pass）
- 【群2】H15 ボラ逃げ禁止（方向スコアで atr/ボラ 非支配・feature importance で確認）
- 【群2】学習窓で純増を先に測る（採点窓 不参照・H8）→ プラスかつ非degenerate なら採点
- 【群2】公式判定は score.py / score.score（CC は net 計算に触れない＝import のみ）・両窓で改善を確認するまで「効いた」と言わない
- 【群2】degenerate（near-inaction＝ほぼ無取引で損が小さいだけ）でないか（件数/伸びを玉単位で確認）

<!-- ACC_CHECKLIST_END -->

### 7-6 完成の条件

［手書き］条件とコマンドは やることの表の「7-6 完成の条件」・状態の欄は承認のプログラムが書く
**★状態は全部「未着手」です。「済」にするのはプログラムです**（承認のコマンドが壊すプログラムを走らせ、終了コードが 0 以外のときだけ済にします）。**自分で「直った」と判定しません**（恒久の決まり64番）。

<!-- ACCEPT_TABLE_START -->

| # | 完成の条件 | その数字を出したコマンド | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|---|
| 1 | F-1：build_catalog の名前の並びが、写す元の関数（F-3）の名前の並びと1本も違わない（違えば終わりのコード 1） | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | build_catalog の全部の組 | build_catalog が、列を作る組の最後の1組を作らない形にする | `b222_catalog_drops_last_set.sh` | 要 | **未着手** |
| 2 | F-1：build_catalog の中に、cfg の鍵を読む所（cfg[...]・cfg.get(...)）が無い（在れば終わりのコード 1） | `python3 scripts/priority_rebuild/observe_diag.py --selftest-catalog` | build_catalog の構文の木 | build_catalog に、cfg["rsi_periods"] を読む行を足す | `b223_catalog_reads_old_key.sh` | 要 | **未着手** |
| 3 | F-2：読む口の column_sets が、組ごとに計算の登録の名前を返し、登録の名前が無い記録に組が在れば止まる（自己テストは自分の中の見本で試す）（通らなければ終わりのコード 1） | `python3 scripts/priority_rebuild/indicators/indicators.py --selftest` | 読む口の column_sets | 返り値から登録の名前を外す | `b224_reader_sets_no_reg.sh` | 要 | **未着手** |
| 4 | F-3・F-4：写すプログラムの cols と catalog_sets が、build_catalog でなく写す元の関数を呼ぶ（呼べば終わりのコード 1） | `python3 ../../.claude/state/indicator_review/gen_indicators_draft.py --selftest` | 写すプログラムの写す元 | catalog_sets の呼び先を build_catalog に戻す | `b225_draft_source_is_catalog.sh` | 要 | **未着手** |
| 5 | F-5：H2 の印の対象に、indicators/indicators.json が在る（無ければ「…leak_causality_diag.py:0」と出て終わりのコード 1） | `grep -H -c -F 'indicators/indicators.json' scripts/priority_rebuild/leak_causality_diag.py` | H2 の対象の一覧 | WATCHED から indicators.json の行を消す | `b226_h2_watch_no_indicators.sh` | 要 | **未着手** |
| 6 | F-6：gen_materials の自己テストが通る（T12＝写す元の関数に設定の鍵の読みを1つ足すと、場所1 が1つ増える）（通らなければ終わりのコード 1） | `python3 scripts/priority_rebuild/gen_materials.py --selftest` | gen_materials の鍵を拾う口 | _catalog_keys が見る関数の名前を build_catalog に戻す | `b227_materials_keys_from_catalog.sh` | 要 | **未着手** |

<!-- ACCEPT_TABLE_END -->

［自動］CC が書いて、まこさんが OK した案の【7-6】の、行が無いやることの番号と理由の行
- 行が無いやることの番号と、その理由：無し。★列の名前・並び・値が直す前と同じこと（155-1）は、当てた後の長い走行（約61分）でしか確かめられないので、完成の条件には入れず、4-4 の5 と案の【4-12 出る結果の姿】に書く（案のひな型 :193＝「完成の条件に書くコマンドは、実装を当てた直後に走らせて成功する物だけにする」）。

### 7-7 触る関数と、その定義の行

［自動］実物のコードから読んだ定義の行
<!-- ACC_CODEREF_START hash=98c499e8154af169 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl` の `def_lines`（★行番号を手で写さない・93番）。

**直す相手**＝`scripts/priority_rebuild/observe_diag.py`

| 触る関数 | 定義の行 |
|---|---|
| `selftest_catalog` | 7812 |

**★この行番号は `--write` を走らせた時点のものです。**実装すると動きます（全部で 211件の関数が在ります）。

<!-- ACC_CODEREF_END -->

### 7-8 プログラムが読む設定（2つ）

［自動］DESIGN_CONTRACT は CC が書いて、まこさんが OK した案の【7-8】・SPEC は実物のコードから読んだ関数と定数
<!-- ACC_SPEC_START hash=4b20ec7ccada2ed6 gen_acceptance.py が自動生成＝手で書き換えない -->
出どころ＝`verify_design_contract.spec_from_impl`。**手で1文字も直していません。**

DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/observe_diag.py",
  "_impl_file の意味": "列を作る所 build_catalog と、写す元の関数 _catalog_from_config と、カタログの自己テストが在る観察の道具。",
  "impl_functions": {
    "scripts/priority_rebuild/observe_diag.py": [
      "build_catalog",
      "_catalog_from_config",
      "selftest_catalog"
    ],
    "scripts/priority_rebuild/indicators/indicators.py": [
      "<モジュール直下>",
      "Indicators.column_sets",
      "selftest"
    ],
    "../../.claude/state/indicator_review/gen_indicators_draft.py": [
      "<モジュール直下>",
      "build_old",
      "catalog_sets",
      "table_update",
      "selftest"
    ],
    "scripts/priority_rebuild/leak_causality_diag.py": [
      "<モジュール直下>"
    ],
    "scripts/priority_rebuild/gen_materials.py": [
      "_catalog_keys",
      "selftest"
    ]
  },
  "self_check_calls": [
    "selftest_catalog"
  ],
  "_self_check_calls の意味": "observe_diag.py に在るはずの、カタログの自己テストの関数の名前。",
  "must_use": {
    "selftest_catalog": [
      "build_catalog",
      "_catalog_from_config",
      "load_config",
      "find_material"
    ]
  },
  "_must_use の意味": "カタログの自己テストが呼ぶ関数（_catalog_from_config は、この工事で足す照らし⑮が呼ぶ）。",
  "spec_lists": {},
  "no_spec_lists_reason": "この工事は、観察の道具の外から読む一覧の形（カタログの1件＝名前・計算・向き）を変えない。column_sets の返り値に登録の名前を足すが、それを読むのは build_catalog だけ（grep）。",
  "generated_from": {
    "impl_functions": "直す前の文字が入る関数を、grep で def の行から確かめた。一番外の行（説明・PART_SRC）は <モジュール直下>・クラスの中の関数は Indicators.column_sets と、仮当て（A12）の照合A が出した名前に合わせた",
    "must_use": "selftest_catalog の中の呼び出しを grep で確かめた（_catalog_from_config は実装の指示の2件目で足す）",
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
  "spike_threshold": [],
  "spike_stat": [],
  "lee_mykland_stat": [],
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
  "selftest_known_ng": [],
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
  "selftest_lineage": [],
  "selftest_band": [
   "build_catalog",
   "find_material",
   "load_config",
   "make_material"
  ],
  "selftest_atr1h": [
   "build_catalog",
   "build_features",
   "load_config"
  ],
  "selftest_match": [
   "build_catalog",
   "load_config"
  ],
  "selftest_catalog": [
   "build_catalog",
   "build_features",
   "find_material",
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
   "selftest_band",
   "selftest_catalog",
   "selftest_insp5",
   "selftest_lineage",
   "selftest_match",
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
  "--selftest-band",
  "--selftest-catalog",
  "--selftest-insp5",
  "--selftest-known-ng",
  "--selftest-lineage",
  "--selftest-match",
  "--selftest-rank-demand",
  "--selftest-rank-resume"
 ]
}
```

<!-- ACC_SPEC_END -->
