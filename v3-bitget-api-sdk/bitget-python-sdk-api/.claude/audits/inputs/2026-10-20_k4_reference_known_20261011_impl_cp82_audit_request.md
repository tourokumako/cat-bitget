# 【監査依頼】CP82 — K-4 検査の直し＝監査 CP60 の修正59・60。参照表の独立実装に「教科書から書いたか・写しか」の印を付け、写しの物と4種の既知答えに定義から導いた答えを足す。M2-C-15（実装の監査）

## ⚠️ 監査人への宣言（本依頼書を開いた CC への指示・最優先）

**あなたは、本セッションで監査人として呼ばれた CC です**（依頼を出した CC とは別のセッション）。SessionStart で読み込まれる CLAUDE.md などは参考のみ。読むのは、本依頼書と「着手前必読」と、問いが材料として指す実物（コード・設定・記録）だけ。

依頼を出した CC の判断に共感しないこと（同型バイアス）。あなたは、まこさんの味方でも CC の味方でもなく、基準（要件定義・教科書・業界の標準）の味方です。

### やること（読み終えたら、確認の質問なしで）

1. 本依頼書の全文を Read で読む。
2. `Agent`（`subagent_type=Plan`）を cold start で起動する。渡すのは、依頼書のパスと着手前必読の名前だけ。Plan agent が依頼書を読んで監査し、所見を返す。Plan agent はファイルを作れず、コマンドを走らせられない。写しを作る・自己テストや試しの道具を走らせるのは、監査人の CC（あなた）がやり、結果を Plan agent に渡す。
3. 結果を、次の順で書く（手で1から書かない。コマンドは全部、リポジトリの根 `cat-bitget/` で打つ）:
   - 骨組みを作業場に作る: `python3 .claude/tools/gen_audit_docs.py result v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-20_k4_reference_known_20261011_impl_cp82_audit_request.md v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp82_work/cp82_result.md`
   - 骨組みの「<監査が書く>」を全部 埋める（見出しと並びは変えない）。
   - 照らす: `python3 .claude/tools/gen_audit_docs.py check v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-20_k4_reference_known_20261011_impl_cp82_audit_request.md <埋めた結果>` と `python3 .claude/tools/gen_audit_docs.py form <埋めた結果>` で、食い違い0件にする。
   - 見直す: `python3 .claude/tools/gen_review.py --skeleton <埋めた結果>` の表を全部 埋め、`python3 .claude/tools/gen_review.py --check <埋めた結果>` を通す。
   - 結果ファイル `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-20_k4_reference_known_20261011_impl_cp82_audit_report.md` に、Write で1回だけ書く（hook 11 が同じ照らしを掛ける。書いた後は書き替えられない）。
4. 戻り報告＝結果ファイルのパス／結論（GO・CONDITIONAL-GO・NO-GO）／重さごとの件数（Critical・Major・Minor・Process）。

### 禁止

- 依頼を出した CC への確認の質問（本依頼書だけで完結する）。
- Plan agent を起動せず、自分で監査すること。
- 本物のファイルを書き替えること。写しは作業場に作り、最後に `git status --short` で書き替えていないことを示す。
- ChatGPT など外の AI を使うこと（まこさんの課金外）。
- 「可能性がある」「かもしれない」「検討の余地」で答えること。数字と実物の行で言い切るか、「データ不足（理由）」と書く。

### 作業場

写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp82_work/` に作る。必要なファイルは自分で開き、写しで走らせて確かめる。

---

## 監査依頼メタ情報

- 依頼日: 2026-10-20
- 依頼者: CC（起案者）
- 監査の種類: 実装の監査
- 売買に触るか: はい
- 監査対象タスク: M2-C-15・M2-F-10f／設計書 k4-reference-known-20261011
- 監査の相手と版: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/k4-reference-known-20261011.md` ／ ハッシュ値 b06ca8a4ef349c641c404fa00cf698385a06b3e7e1c6a15637d5e27156de827b
- 直す相手: `SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`・`.claude/breaks/b172_alma_weights_reversed.sh`・`.claude/breaks/b173_stc_zero_range_divides.sh`・`.claude/breaks/b174_hilo_short_column.sh`・`.claude/breaks/b175_dpo_centered_future.sh`・`.claude/breaks/b176_sarext_sign_not_abs.sh`・`.claude/breaks/b177_psar_af_column.sh`・`.claude/breaks/b178_cksp_long_short_swapped.sh`・`.claude/breaks/b179_pmax_ma_of_high.sh`・`.claude/breaks/b180_vwap_volume_weight_dropped.sh`・`.claude/breaks/b181_thermo_ma_column.sh`・`.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b183_copy_verified_by_tb_alone.sh`
- 結果ファイル保存先: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-20_k4_reference_known_20261011_impl_cp82_audit_report.md`
- 入力ファイル保存先 (本依頼書): `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-20_k4_reference_known_20261011_impl_cp82_audit_request.md`

---

## 要件定義と工事の流れ (固定・消さない・まこさん指示 2026-10-12)

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

---

## この監査は何のためか（目的と経緯）

1. **この工事は何のためか**＝監査 CP60 が見つけた「参照表の教科書の独立実装10件が、教科書でなくカタログかライブラリの変形を写した物で、検査3 の照合が『自分と同じか』しか確かめていない」（修正59）と、「SAREXT・CKSP・PMAX・PSAR の既知答えが『値段が一定なら 0』だけで、売り側を一度も通らない」（修正60）を直す。目的＝材料（指標）の検査が、ライブラリと同じ誤り（ALMA の重みの向き・STC の式・SAREXT の符号）を「一致検証済み」で通さない状態にする。材料の値そのものは変えない
   監査 CP73 の Q8 が指摘した「観察の道具と同じ式の写しどうしの照らし」の3種（close vs SSF平均%・close vs VIDYA_CMO%・SQZ_ON_Carter）の独立の実装を、別の書き方にする（式の出どころは変えない）
2. **この工事は何か**＝監査 CP60 は、参照表の「教科書の独立実装」の多くが、教科書でなくカタログやライブラリの変形を別の書き方で写した物で、検査3 の照合が「自分と同じか」しか確かめていないと指摘しました（修正59・一般の観点④）。ALMA の重みの向き・STC の式・SAREXT の符号の誤りが、その照合を通った理由です。修正60 は、SAREXT・CKSP・PMAX・PSAR の既知答えが「値段が一定なら 0」だけで、売り側を一度も通らないと指摘しました。この工事は、参照表の登録に「教科書から書いたか・写しか」の欄を足し、名指しされた10件の独立実装を使う16の登録に写しの印を付け、写しの物に定義から導いた既知答えを足し、4種の既知答えに下げ続ける合成のバーを足します。観察の道具の検査3 は、写しの独立実装が合っただけでは一致検証済みに数えない形にし、自己テストに写しの印の番人を2つ足します。あわせて、監査 CP73 の Q8 で「観察の道具と同じ式の写しどうしの照らし」と指摘された3種（close vs SSF平均%・close vs VIDYA_CMO%・SQZ_ON_Carter）の独立の実装を、別の書き方にします。材料の値・設定の値は1つも変えません（写しで前から在る列の値の違い 0 本）。既知答えの数字は、定義から導いた式で書き、ライブラリの値を写していません。導いた答えは、写しで走らせて全部 ライブラリの実物の値と合いました。（やることの番号 M2-C-15・M2-F-10f）
   **この工事の位置**＝全月 net ≥ $1,900（単月判定・通算でない・要件定義書 §1.2） → M2｜場面の判定（レンジかどうか）を組み立てられる（②） → M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す → M2-C-15｜工事1＝材料を直す（監査 CP60 の修正・パラメータ・法則どおりの帯の部品・S1 の部品・役割・閾値） → M2-F｜段ごとに測って並べ、上位を次の段へ渡す（段1〜段4）＝1本ずつの成績と順位を出す → M2-F-10f｜教科書の版と今の版で値が違う指標を、一致率で比べ、レジーム判定に使う版を決める（上位足の1本の遅れも、直す前と後で比べる） → この工事
3. **この工事が結ぶ要件**＝（この設計書の形には、結ぶ要件の欄が無い。監査は、設計書の §1 概要と、やることの表から、結ぶ要件を読み取ってください）
4. **経緯**＝- 2026-10-11 に設計書を作り、設計書の監査 CP74 に出した。CP74 が問うたのは「設計書が割り当ての表のとおりか」の15問で、結論は GO（Minor 3・Process 3）。設計の中身が要件定義に合うかは問うていない。
   - 2026-10-12 に承認し、実装46件を書き込んだ（コミット ae172e2）。実装の監査は、まだ出していなかった。
   - 2026-10-12 に、設計書の監査は設計の中身を問う形に変わった（まこさん決定）。
   - 2026-10-20 に まこさんが決めた＝設計書は作り直さない。この実装の監査で、実装が要件定義を満たすかも照らす。直す所は、この監査の修正として当てる。
5. **なぜこの監査が要るか**＝設計の中身が要件定義に合うかを、実装の前に CC 以外が確かめていない。この監査で、実装そのものを要件定義と照らす。

---

## 監査の範囲

### 範囲の中

- 監査の相手＝`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/k4-reference-known-20261011.md`（設計書 `k4-reference-known-20261011`・実装の監査）。設計書の実装の指示のとおりに、当てる道具が実装を作れているか。
- 直す相手＝`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`・`.claude/breaks/b172_alma_weights_reversed.sh`・`.claude/breaks/b173_stc_zero_range_divides.sh`・`.claude/breaks/b174_hilo_short_column.sh`・`.claude/breaks/b175_dpo_centered_future.sh`・`.claude/breaks/b176_sarext_sign_not_abs.sh`・`.claude/breaks/b177_psar_af_column.sh`・`.claude/breaks/b178_cksp_long_short_swapped.sh`・`.claude/breaks/b179_pmax_ma_of_high.sh`・`.claude/breaks/b180_vwap_volume_weight_dropped.sh`・`.claude/breaks/b181_thermo_ma_column.sh`・`.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b183_copy_verified_by_tb_alone.sh`。
- 売買のロジックに触る工事。engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」（まこさん確定 2026-08-06）。

### 範囲の外（理由つき）

- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 写しの独立実装10件を教科書の作りに書き直すこと（修正59 の直し方は印と既知答えまで。書き直すと材料の値が変わり、別の工事になる）
- 名指しの10件の外の登録に印を付けること（1件ずつの判定が要る。この工事は名指しの10件と書き替える3種だけ）
- 修正61（説明の文だけ）（説明の文だけの直しは直さない）
- 材料の値・設定の値・探す範囲を変えること（T-2・T-3・P-6・P-7・H-1（この工事の後））
- 教科書の版と今の版を比べること（M2-F-10f）
- 仕組みの直し①②④（作業が実際に止まったときにやる（恒久65番の3））
- 監査に出す前のチェックの自己テストの P7-1 の落ち（この工事の前から在る。next_step §6 に積んである）

---

## 確かめてほしいこと（Q1〜QN）

★優先度＝A（結論を変える）／B（直すべき）／C（書き漏れ）／D（結論に効かせない）。結果の所見は、この番号をそのまま見出しにし、優先度の順に書く。時間が足りずに省いた問いは、結果にその番号を書く。
★各 Q に、何を確かめるか・材料（どのファイルのどこ）・答えの形（表／件数／見つけた事の一覧）を書く。

### R0 — この工事は、要件定義の何番を満たすための物か。要件定義に反する所は無いか（優先度 A）

**優先度の理由**＝要件定義に反する直しや、要件のどれにも結び付かない直しが、そのまま進む

この工事が結ぶ要件は、「この監査は何のためか」の 3 に書いてあります（3 に「欄が無い」と書いてあるときは、そこに書いた読み方で読み取ってください）。
要件定義は、依頼書の上部に要約を載せています。全文は `.claude/rules/core_requirements_full.md` です。

- **R0-1**＝結ぶ要件が、工事の目的と中身に合っているか。もっと合う要件や、抜けている要件は無いか。
- **R0-2**＝設計・実装・直しに、要件定義（上部の要約と、全文）に反する所は無いか。反する所は、ファイルと行で挙げてください。

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**優先度の理由**＝違えば、実装は設計書のとおりに作られていない

実装の前（事実データ「実装の前と後の版」の実装の前）の対象のファイル（`.claude/breaks/b172_alma_weights_reversed.sh`・`.claude/breaks/b173_stc_zero_range_divides.sh`・`.claude/breaks/b174_hilo_short_column.sh`・`.claude/breaks/b175_dpo_centered_future.sh`・`.claude/breaks/b176_sarext_sign_not_abs.sh`・`.claude/breaks/b177_psar_af_column.sh`・`.claude/breaks/b178_cksp_long_short_swapped.sh`・`.claude/breaks/b179_pmax_ma_of_high.sh`・`.claude/breaks/b180_vwap_volume_weight_dropped.sh`・`.claude/breaks/b181_thermo_ma_column.sh`・`.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b183_copy_verified_by_tb_alone.sh`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`）に、設計書 4-20 の実装の指示（46 件）を番号の順に当てた結果が、実装の後（事実データ「実装の前と後の版」の実装の後）と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**優先度の理由**＝在れば、設計書に無い変更が実装に混ざっている

実装の前（事実データ「実装の前と後の版」の実装の前）と実装の後（事実データ「実装の前と後の版」の実装の後）の差分（`.claude/breaks/b172_alma_weights_reversed.sh`・`.claude/breaks/b173_stc_zero_range_divides.sh`・`.claude/breaks/b174_hilo_short_column.sh`・`.claude/breaks/b175_dpo_centered_future.sh`・`.claude/breaks/b176_sarext_sign_not_abs.sh`・`.claude/breaks/b177_psar_af_column.sh`・`.claude/breaks/b178_cksp_long_short_swapped.sh`・`.claude/breaks/b179_pmax_ma_of_high.sh`・`.claude/breaks/b180_vwap_volume_weight_dropped.sh`・`.claude/breaks/b181_thermo_ma_column.sh`・`.claude/breaks/b182_copy_mark_without_known.sh`・`.claude/breaks/b183_copy_verified_by_tb_alone.sh`・`SDK/scripts/priority_rebuild/indicator_reference_diag.py`・`SDK/scripts/priority_rebuild/observe_diag.py`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**優先度の理由**＝合わなければ、どの件を道具が当てたかを後から確かめられない

当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:k4-reference-known-20261011`）が、実装の指示の 46 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**優先度の理由**＝当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない

承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/k4-reference-known-20261011.md`）と、監査の相手の設計書（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/k4-reference-known-20261011.md`。★`.claude/state/acceptance.md` は、この工事の後に別の工事の設計書で上書きされたので比べない）の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**優先度の理由**＝要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない

実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/k4-reference-known-20261011/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**優先度の理由**＝成り立たなければ、承認のときの「済」が根拠にならない

設計書の完成の条件（12 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/observe_diag.py --selftest-match`

### Q8 — 定義から導いた既知答え（写しの9登録と、下げ続ける足の7列）は、定義から正しく導かれているか（優先度 A）

**優先度の理由**＝導きが違えば、ライブラリと同じ誤りを「正しい答え」として固定し、修正59・60 の目的（誤りを捕まえる）が逆向きになる

書き込んだ後の参照表の既知答えの式（close vs VWAP＝:1241-1249・S-Rタッチ数＝:1507-1510・STC と STCstoch＝:3257-3263・_alma_lag と ALMA の2登録＝:3317-3337・close vs HILO%＝:3352-3354・下げ続ける足の説明と CKSP・DPO%・PMAX・PSAR・SAREXT＝:3532-3590・THERMO%＝:4324-4326）を、登録の定義・流儀の欄の文と、監査 CP60 の §5 が引いた原典の逐語、ライブラリの実物（必読の8本）から、監査が自分で導き直してください。特に＝ALMA の遅れ（重みの向き・i は古い側から）、HILO の「終値 − 11」（13本の高値の平均・21本の安値の平均）、DPO% の (n/2+1)＋(n−1)/2、VWAP の出来高 9 の足の式、PSAR の g←0.8×(g＋1) の収束＝4、CKSP の c＋17 と c＋1（TradingView の形 p=10・x=1・q=9）、PMAX の EMA10 の遅れ 4.5。★CC の自己申告（1）＝答えの数字は定義から導いた式で書き、ライブラリの値は写していません。書き込んだ後の実物で、全体の自己テストが通りました。通ったことは「導きがライブラリと同じ」の証拠で、「導きが定義どおり」の証拠ではありません。定義の読みは監査とまこさんの目です。★CC の自己申告（2）＝参照表の説明の行（:3537 の辺り）と設計書の 4-0 の③は、SAREXT の導きを「TA-Lib＝買いと売りの加速が同じなら PSAR と同じ線」と書いています。設計書の監査 CP74 は、この文に当たる文が TA-Lib のページに無いと書きました（外部検索 1。修正の番号は無し）。CC は、この文を引用ではなく定義から導いた文として残しました。根拠にしたのは、ライブラリの既定の加速が買い側も売り側も 0.02・0.02・0.2 であること（sarext.py の :163-168）と、売り側を負の数で返すこと（同 :137）です。この書き方を直すべきかを、所見に書いてください。

### Q9 — 写しの印16登録の選び方は、修正59 が名指しした10件の独立実装を使う登録と一致するか。印の外に写しが残っていないか（優先度 A）

**優先度の理由**＝印の付け忘れが在れば、その登録は独立実装だけで「一致検証済み」に数えられ続ける

修正59 の原文が名指しした10件（_tb_vs_pivot・_vp_ref・_tb_vs_vwap・_tb_wpat・_tb_sr_touch・_alma・_stc_parts・_tb_pos_hilo・_tb_thermo_pct・_tb_dpo）を使う登録を、書き込んだ後の参照表の実物から監査が数え直し、tb_kind="写し" の16登録（W字・close vs VWAP・pivotPP・pivotR1・pivotS1・POC・VAH・VAL・S-Rタッチ数・STC・STCstoch・close vs ALMA%・ALMA傾き%・close vs HILO%・DPO%・THERMO%）と合うかを見てください。名指しの10件を使う登録で印が付いていない物、名指しの外で同じ型（カタログかライブラリの変形の写し）の独立実装が在る物が在れば所見に書いてください。★CC の自己申告＝名指しの10件の外の登録（272件）は未判定（None）のままにしました（設計書の 3-1 の2・5 の5番）。

### Q10 — 検査3 の直し（独立(写し)✓）・番人2つ・軽い口 selftest_match は、修正59 の文の意図を満たすか。軽い口が検査3 を絞ることで守りが減らないか（優先度 A）

**優先度の理由**＝絞った軽い口が完成の条件の測る口になるので、絞りの外で検査3 が落ちる形を見逃すと、「通った」と読み替わる

検査3 の写しの枝（observe_diag.py の :4375 から＝写しは verified に入れない）・軽い口の本体（:7338-7393＝コマンドから呼ぶときは「既知答えを持つ登録の列と写しの印の列」に絞る・selftest からは全列）・全体の自己テストからの呼び出し（:7951＝軽い口を全列で呼び、_v3b を受け取って「検証済みにならない列」を数える＝:8042）・旗（:8581-8582）を読み、①全体の自己テストの中身が直す前より減っていないか ②壊すプログラム12本が落とす相手（既知答えの不一致・番人①②）が絞った列の中に全部 在るか ③絞りの条件（known が None でない・tb_kind が "写し"）で漏れる列が無いか、を見てください。★CC の自己申告＝軽い口で測る形は CC の判断です（設計書の 3-2 の4）。理由は、承認の前の仮当ての壊すプログラムの打ち切り 900秒に、全体の自己テスト（1本 約142秒）でも全列の軽い口（1本 約92秒）でも12本が入らなかったことです。絞った軽い口は、承認の前の写しで1本 約63秒・12本 714秒でした（k4_check_run.log）。

### Q11 — 3種の別の書き方（SSF＝scipy の線形フィルタ・VIDYA＝畳み込みと accumulate・Carter の ATR＝pandas の指数平滑）は、式の出どころを変えず、観察の道具と別の書き方になっているか（優先度 B）

**優先度の理由**＝同じ文字の写しどうしでは、両方に同じ誤りが入っても見つからない（監査 CP73 の Q8 の (c)）

書き込んだ後の3つの関数（_tb_sqz_carter＝:1721 から・_ssf2_avg＝:1752 から・_vidya_cmo＝:1785 から）を、観察の道具の実物（SSF の繰り返し・VIDYA の繰り返し・Wilder の ATR）と並べ、同じ式（出どころ＝linnsoft の Filt の逐語・ta-lib.org の VIDYA の逐語・Carter のスクイーズ）を別の計算の道筋で書いているか、初期値の扱い（SSF の最初の2本を初期状態に・VIDYA の種＝最初の n 本の単純平均・ATR の種＝最初の n 本の単純平均）が観察の道具と同じ始め方かを見てください。★CC の自己申告＝3種には手計算の既知答えを足していません（教科書の印＝tb_kind="教科書"）。独立の実装どうしの照らし（許容差 1e-6）で守ります。書き込んだ後の実物で、全体の自己テストが通りました。

### Q12 — 壊すプログラム12本は、直しを外したときだけ、決めた文で止まるか（優先度 B）

**優先度の理由**＝止まらない壊し方が在ると、既知答えや印が黙って消えても誰も気づかない

新しい12本（b172〜b183）の壊し方（ALMA の重みを逆向き・STC の 0 割り・HILO の列・DPO の centered=True・SAREXT の絶対値を外す・PSAR加速の列・CKSP の列の入れ替え・PMAX の入力を高値・VWAP の重みを外す・THERMO% の列・既知答えを外す・検査3 の直しを戻す）が、それぞれ1つの既知答えか番人で落ちるか、壊す対象がちょうど1か所か、落ちるはずの文（EXPECT_MSG）が軽い口の出力に出る形かを見てください。書き込んだ後の実物で、走らせるプログラム（run_breaks.py --design … --measure-only）が12本とも「期待どおり」（終了コード 1・期待 1）と出しました。監査が写しの作業場で走らせるなら、1本 約63秒です。★CC の自己申告＝CC は、壊したときに出る文そのものを画面で読んでいません（走らせるプログラムは、決めた文が出力に在るかを照らして「期待どおり」と出すだけです）。文を読んだのは、承認の前の写しの記録（k4_check_run.log の [8]）です。

### Q13 — 完成の条件12行は、やると決めた F-1〜F-6 を覆っているか。F-4 と F-6 に壊すプログラムが無い扱いは妥当か（優先度 B）

**優先度の理由**＝覆っていない直しは、「直った」を仕組みで確かめられない

やることの表の一覧（F-1 印・F-2 写しの既知答え・F-3 下げ続ける足・F-4 3種の別の書き方・F-5 検査3 と番人・F-6 列の名前を決めた文に持つ壊すプログラムの照らし）と、設計書の 7-6 の12行を照らしてください。F-4 は自己テストの「教科書の独立実装と不一致」が守る（4-5 の5行目）、F-6 は写しで確かめるプログラムの照らし（k4_check_run.log の [L-678]＝0本）で済ませ、壊すプログラムを作っていません。この扱いが妥当か、ほかに完成の条件が覆っていない直しが無いかを見てください。

### Q14 — 設計書の監査 CP74 の修正 1〜4 は、指示のとおりに入っているか。CC が直していない物の扱いを所見に書いてほしい（優先度 B）

**優先度の理由**＝監査の修正が入っていない設計書で実装すると、控えに誤った文が残る。直していない物を黙って残すと、次の工事で同じ形が出る

設計書の監査 CP74 の結論は GO（Minor 3・Process 3）でした。修正 1（4-19 の数字の符号）と修正 2（3-2 の出どころの記録の名前）は、修正を書き込むプログラム（apply_audit_fix.py --report）が やることの表.md に書きました。修正 3（未決）は、まこさんの決定で、CC が設計書を作るプログラム gen_acceptance.py に1行 足しました。修正 4（設計書の作り直し）は CC が走らせました。承認済みの設計書の控えで、3か所（3-2 の4行目・4-19・7-3b の見出しの下）が指示のとおりかを見てください。★CC の自己申告（1）＝修正 3 を足した後の gen_acceptance.py の自己テストは走らせていません（設計書を作る・--verify を走らせる・承認の前の検査が通る、までです）。売買のロジックに触る工事の設計書は、これから 7-3b に1行 増えます。★CC の自己申告（2）＝監査 CP74 の Process の3件のうち、直したのは見直し表の19番だけです（符号の違いを「同じ」と判定していた行）。出どころのファイルが無い逐語6本（ok_break_run・ok_commit_nextmove・ok_five_items・ok_read_plan・ok_trial_full・ok_try_and_hand）は、そのままです。出どころのファイルを作り直すと、設計書を作るプログラムがその逐語を §0-1 に数え、承認済みの設計書が作り直しで変わるためです。★CC の自己申告（3）＝設計書の監査の依頼書 CP74 は、ライブラリの必読に .venv の置き場（版 0.6.20）を書いていました。観察の道具が読み込むのは /usr/local の版 0.6.52 です。この依頼書の必読は 0.6.52 の行で書きました。設計書の見直し表の13番は、0.6.20 の行（sarext.py の :171〜176・:145）で書いたままです。★CC の自己申告（4）＝設計書の実装の指示の「直す箇所」の行番号は、書き込む前の実物の行です。書き込んだ後は、参照表も観察の道具も行が増えて動いています。★CC の自己申告（5）＝K-4 の設計書の見直し表（.claude/state/reviews/acceptance.review.md・95項目）は、後の工事（design-doc-gen-form-20261013）で上書きされて、残っていません（git にも控えにも無い・2026-10-20 に find と git log で確かめた）。19番・11番・90番・13番の扱いは、記録 .claude/state/session_worklog_20261012.md の §1〜§2 にだけ在ります。

### Q15 — 実装は、要件定義（機能要件の6行・6番・8番）を満たし、損なっていないか（優先度 A）

**優先度の理由**＝設計書の監査 CP74 が設計の中身を問うていないので、要件に反する作りが在っても、ここで見つけないと残る

①機能要件の6行（指標・閾値・パラメータ・時間足・役割・つなぎ方）ごとに、この工事が関わるか、関わるなら満たすか、関わらないなら損なっていないかを、表で書いてください。②要件定義の6番（指標は指標一覧〔material〕からだけ呼び出す・誤りは置き場の1か所を直せば全部に届く）を、書き込んだ後の参照表と観察の道具で照らしてください。③要件定義の8番（net 利益を最大にするロジックを見つける力を、損なっていないか）を、検査3 の「一致検証済み」の数え方の変化で照らしてください。直す所が在れば、実装のファイル（indicator_reference_diag.py・observe_diag.py・壊すプログラム）への修正の指示（6つの欄）で書いてください。★CC の自己申告＝監査に出す前のチェックのうち check_indicator_sources.py の②（observe_config.json の material_params が、いまの資料の表から写し直した物と42行違う）は、10-18 の22番の後に残った、分かっている食い違いです。P-6・P-7 の工事で直します。K-4 は observe_config.json に触りません。まこさん「B」（2026-10-20）で、この1件だけを、出力が同じときに限って通しました（pre_audit_check.py の KNOWN_NG）。この扱いで K-4 の監査の結論が変わらないかを、所見に書いてください。

---

## 問いの外から当てる視点

### 一般の観点（①〜⑦・どの監査でも当てる）

問いに無くても、次の7つの視点で見る。観点ごとに「見つけた事と根拠」を、結果の所見に書く（見つからなければ「見つからなかった」と、見た相手を書く）。

- ①統計学的妥当性＝数字の根拠は足りているか。
- ②リスク管理＝損失や壊れたときの備えは在るか。
- ③認知バイアス＝CC の思い込みで組まれていないか。
- ④ソフトウェア工学＝作りとして正しいか（重複・壊れやすさ・テスト）。
- ⑤再現性＝同じ手順で同じ結果が出るか。
- ⑥実行プロセス＝決めた流れのとおりに進めたか。
- ⑦主エージェントバイアス＝CC が自分に都合よく判定していないか。

### 外の基準で確かめること（外部検索・WebSearch／WebFetch）

内部の文書だけで判断しない。次の物を、外の出どころ（教科書・公式の文書・業界の標準・論文）で確かめ、結果に URL と使った逐語を書く。

件数: 2 件（結果の外部検索は、この件数に1つずつ答える）

1. **既知答えの定義の出どころ**:
   - 検索の言葉: （案に検索の言葉の列が無い。「何と照らすか」から、監査が検索の言葉を決めてください）
   - 何と照らすか: 参照表の定義・流儀の欄の文と、監査 CP60 の §5 に引いてある原典の逐語（TradingView の ALMA・TA-Lib の STC と SAREXT・LuxAlgo の HILO・StockCharts の VWAP）。新しく Web は開いていない（実装の監査＝この出どころと、実装の該当の所が合うか）
2. **ライブラリの作りの確かめ**:
   - 検索の言葉: （案に検索の言葉の列が無い。「何と照らすか」から、監査が検索の言葉を決めてください）
   - 何と照らすか: pandas_ta_classic 0.6.52 の実物（trend/psar.py・sarext.py・cksp.py・pmax.py・overlap/hilo.py・alma.py・volatility/thermo.py・trend/dpo.py）を読んだ。答えの数字はそこから写していない（実装の監査＝この出どころと、実装の該当の所が合うか）

---

## CC がまだ確かめていないこと

依頼を出した CC が、測っていない・確かめていない・設計書に書いていない事。結果は、この番号ごとに1件ずつ答える。

1. **この工事の外の作業中の変更**＝`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/gen_acceptance.py`・`.claude/tools/gen_audit_docs.py`・`.claude/tools/gen_core_requirements.py`・`.claude/tools/pre_audit_check.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）

---

## 着手前必読（省略禁止・37 件）

**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/k4-reference-known-20261011.md`（全文） — 監査の相手（設計書・プログラムが作った）／承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）／承認済みの設計書の控え（実装の指示46件＝参照表30・観察の道具4・壊すプログラム12。完成の条件12行。監査 CP74 の修正 1〜3 を入れた版）
2. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:k4-reference-known-20261011 の行）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/k4-reference-known-20261011/やることの表.md`（全文） — 設計書の元（やることの表）＝修正の指示を書く先／設計書の元データ＝一覧（F-1〜F-6・G-2）・やらないこと・手書きの5項目（監査 CP74 の修正 1・2 が入った行＝:107・:111）
4. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752） — 目標（全月 net ≥ $1,900）と全体戦略、ハード制約（§4.6＝H2 未来参照なし・H6 値段の高さで値が変わらない ほか）。合成の足と既知答えが検査の中だけで使われ、材料の計算を変えないことを照らす
5. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-232） — engine_tuner の目的と探し方の要件、作ってはいけないもの（乱数・探す値を点の一覧で限定する物）
6. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:124-146） — M2 が M1〜M6 のどこに当たり、何ができたら終わりか
7. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:81-109・:1173-1187） — M2 で作っている物と、この工事（M2-C-15 の残り＝K-4 検査の直し）の行
8. `SDK/.claude/audits/2026-10-03_indicator_textbook_check_cp60_audit_report.md`（:56-64・:276-288・:1826-1858） — 監査 CP60 の一般の観点④⑥と、§5 の原典の逐語（STC・ALMA・HILO）、修正59・60 の原文（名指しの10件・既知答えの足し方・「答えの値は手で出してから足す」）
9. `SDK/.claude/audits/2026-10-11_m2c15_formula_textbook_20261011_impl_cp73_audit_report.md`（:90-130・:237-250） — 監査 CP73 の Q8（3種が観察の道具と同じ式の写しどうしの照らしだったこと）と、CC の自己申告への答え
10. `SDK/.claude/audits/2026-10-11_k4_reference_known_20261011_design_cp74_audit_report.md`（全文） — 設計書の監査 CP74 の結果（結論 GO・Minor 3・Process 3・修正 1〜4・外部検索 1 と 2 の補足）（Q14）
11. `SDK/scripts/priority_rebuild/indicator_reference_diag.py`（:119-150・:953-1005・:1185-1198・:1238-1250・:1322-1341・:1388-1413・:1496-1511・:1700-1810・:1838-1882・:3250-3265・:3315-3356・:3530-3592・:4318-4327） — 書き込んだ後の参照表の実物＝合成の足の部品（_mk・_up・_dn・_flat・_thermo_in_case）・登録の関数 _r の欄 tb_kind・find と coverage・写しの印の16登録・定義から導いた既知答え・3種の独立の実装・遅れの部品 _alma_lag・下げ続ける足の既知答え（Q8・Q9・Q11）
12. `SDK/scripts/priority_rebuild/observe_diag.py`（:1015-1016・:1257・:1321・:1403-1404・:1468・:1478-1489・:1550・:4286-4420・:7338-7410・:7940-7953・:8042-8044・:8575-8583） — 書き込んだ後の観察の道具の実物＝壊すプログラム12本が壊す行・検査3 の照合本体（写しの枝＝:4375 から）・軽い口 selftest_match と手本 selftest_catalog・全体の自己テストからの呼び出し・検証済みにならない列の数え方・コマンドの分岐（Q10・Q12）
13. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/_version.py`（:21） — 観察の道具が実際に読み込むライブラリの版（0.6.52）（Q8・Q14）
14. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/psar.py`（:31-71） — PSAR の漸化式の実物。下げ続ける足の既知答え（SAR＝終値＋5・加速 0.2・反転 0）の導きを照らす（Q8）
15. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/sarext.py`（:137・:163-168） — SAREXT が売り側を負の数で返す所と、買い側・売り側の加速の既定の値（Q8）
16. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/cksp.py`（:42-46） — CKSP の買い側・売り側の逆指値の実物（終値＋17・終値＋1 の導き）（Q8）
17. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/pmax.py`（:79-80） — PMAX の帯の実物（EMA10＋3×ATR10 の導き）（Q8）
18. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/overlap/alma.py`（:32-38） — ALMA の重みの実物（遅れ _alma_lag の向き＝監査 CP60 の修正28 で直した向き）（Q8）
19. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/overlap/hilo.py`（:23-24・:50） — HILO の既定の本数（13・21＝終値 − 11 の導き）と、上抜けたときに安値の平均の線になる所（Q8）
20. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/volatility/thermo.py`（:41-45） — THERMO の絶対値の実物（内はらみ足で 0.5 の導き）（Q8）
21. `/usr/local/lib/python3.13/site-packages/pandas_ta_classic/trend/dpo.py`（:32） — DPO の centered=False のずらしの実物（(n/2+1)＋(n−1)/2 の導き）（Q8）
22. `.claude/breaks/b172_alma_weights_reversed.sh` — 新しい壊すプログラム。ALMA の重みを逆向きに戻す（Q12）
23. `.claude/breaks/b173_stc_zero_range_divides.sh` — 新しい壊すプログラム。STC を範囲 0 で割る形にする（Q12）
24. `.claude/breaks/b174_hilo_short_column.sh` — 新しい壊すプログラム。HILO の線を売り側の列に差し替える（Q12）
25. `.claude/breaks/b175_dpo_centered_future.sh` — 新しい壊すプログラム。DPO% を未来を見る版に戻す（Q12）
26. `.claude/breaks/b176_sarext_sign_not_abs.sh` — 新しい壊すプログラム。SAREXT の絶対値を外す（Q12）
27. `.claude/breaks/b177_psar_af_column.sh` — 新しい壊すプログラム。PSAR加速 を反転の列に差し替える（Q12）
28. `.claude/breaks/b178_cksp_long_short_swapped.sh` — 新しい壊すプログラム。CKSP の買い側を売り側の列に差し替える（Q12）
29. `.claude/breaks/b179_pmax_ma_of_high.sh` — 新しい壊すプログラム。PMAX の移動平均の入力を高値にする（Q12）
30. `.claude/breaks/b180_vwap_volume_weight_dropped.sh` — 新しい壊すプログラム。VWAP の分子の出来高の重みを外す（Q12）
31. `.claude/breaks/b181_thermo_ma_column.sh` — 新しい壊すプログラム。THERMO% を EMA の列に差し替える（Q12）
32. `.claude/breaks/b182_copy_mark_without_known.sh` — 新しい壊すプログラム。写しの印の登録から既知答えを外す（Q12）
33. `.claude/breaks/b183_copy_verified_by_tb_alone.sh` — 新しい壊すプログラム。検査3 の直しを戻す（Q12）
34. `.claude/state/indicator_review/k4_check_run.log` — 承認の前に、写しで当てて走らせた記録＝材料 534 → 534・前から在る列の値の違い 0 本・印の数・軽い口 63秒・全体の自己テスト 142秒・壊し方12本が落ちた文（Q9・Q12）
35. `.claude/hooks/require_design_check_before_approval.py`（:468-475・:707） — 承認の前の仮当てが走らせる自己テストの一覧と、壊すプログラムの打ち切り 900秒（軽い口を足した理由）（Q10）
36. `.claude/tools/gen_acceptance.py`（:1649-1660） — 設計書を作るプログラム。監査 CP74 の修正 3（7-3b の見出しの下に［自動］の文字を出す1行）を足した所（Q14）
37. `.claude/state/session_worklog_20261012.md`（全文） — この工事の、監査 CP74 の結果の確認から実装までの経緯（§1〜）

★直す相手のファイルを必ず入れる（結果の「修正の指示」の「直す前の文字」を、実物から写すため）。

---

## 事実データ

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 953〜961行（_r・監査 CP60 の修正59＝登録 _r に「教科書から書いたか・写しか」の欄 tb_kind を足す） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1185〜1193行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（W字＝_tb_wpat）） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1237〜1238行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（close vs VWAP＝_tb_vs_vwap）） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1316〜1317行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（pivotPP＝_tb_vs_pivot）） | 直した後の文字 |
| 5 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1318〜1323行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（pivotR1＝_tb_vs_pivot_rs）） | 直した後の文字 |
| 6 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1327〜1329行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（pivotS1＝_tb_vs_pivot_rs）） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1381〜1388行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（POC＝_vp_ref）） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1389〜1395行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（VAH＝_vp_ref）） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1396〜1401行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印 tb_kind="写し" を付ける（VAL＝_vp_ref）） | 直した後の文字 |
| 10 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1485〜1495行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（S-Rタッチ数＝_tb_sr_touch）） | 直した後の文字 |
| 11 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1688〜1690行（<モジュール直下>・監査 CP73 の Q8（修正2）＝3種の独立の実装を別の書き方にした旨の説明） | 直した後の文字 |
| 12 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1706〜1713行（_tb_sqz_carter・監査 CP73 の Q8＝SQZ_ON_Carter の独立の実装を別の書き方に（ATR は pandas の指数平滑）） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1730〜1740行（_ssf2_avg・監査 CP73 の Q8＝close vs SSF平均% の独立の実装を別の書き方に（scipy の線形フィルタ）） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1758〜1770行（_vidya_cmo・監査 CP73 の Q8＝close vs VIDYA_CMO% の独立の実装を別の書き方に（畳み込みと accumulate）） | 直した後の文字 |
| 15 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1825行（<モジュール直下>・3種の登録に印 tb_kind="教科書"（SQZ_ON_Carter）） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1839行（<モジュール直下>・3種の登録に印 tb_kind="教科書"（close vs SSF平均%）） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 1847行（<モジュール直下>・3種の登録に印 tb_kind="教科書"（close vs VIDYA_CMO%）） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3279行（<モジュール直下>・監査 CP60 の修正59＝ALMA の定義から遅れを導く部品 _alma_lag（既知答え用）） | 直した後の文字 |
| 19 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3281行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（close vs ALMA%＝_alma）） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3283行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（ALMA傾き%＝_alma）） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3222行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（STC＝_stc_parts）） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3225行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（STCstoch＝_stc_parts）） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3297行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（close vs HILO%＝_tb_pos_hilo）） | 直した後の文字 |
| 24 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3475行（<モジュール直下>・監査 CP60 の修正60＝下げ続ける合成のバーの既知答えの導き方（4種の登録の前の説明）） | 直した後の文字 |
| 25 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3475〜3482行（<モジュール直下>・監査 CP60 の修正60＝CKSPl・CKSPs の既知答えに下げ続ける足を足す） | 直した後の文字 |
| 26 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3488行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（DPO%＝_tb_dpo）） | 直した後の文字 |
| 27 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3491〜3492行（<モジュール直下>・監査 CP60 の修正60＝PMAX の既知答えに下げ続ける足を足す） | 直した後の文字 |
| 28 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3496〜3505行（<モジュール直下>・監査 CP60 の修正60＝PSAR%・PSAR加速・PSAR反転 の既知答えに下げ続ける足を足す） | 直した後の文字 |
| 29 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 3513行（<モジュール直下>・監査 CP60 の修正60＝SAREXT の既知答えに下げ続ける足を足す（符号の誤りを捕まえる）） | 直した後の文字 |
| 30 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 4246行（<モジュール直下>・監査 CP60 の修正59＝写しの独立実装の登録に印を付け、定義から導いた既知答えを足す（THERMO%＝_tb_thermo_pct）） | 直した後の文字 |
| 31 | `SDK/scripts/priority_rebuild/observe_diag.py` | 4375〜4377行（_insp_indicator_match・監査 CP60 の修正59＝検査3 で写しの独立実装が合っただけでは一致検証済みに数えない） | 直した後の文字 |
| 32 | `SDK/scripts/priority_rebuild/observe_diag.py` | 7333行（selftest_catalog・監査 CP60 の修正59＝検査3 と写しの印の番人2つを走らせる軽い口 selftest_match（壊すプログラム12本が承認の前の仮当ての打ち切り 900秒に入るため）） | 直した後の文字 |
| 33 | `SDK/scripts/priority_rebuild/observe_diag.py` | 7886〜7889行（selftest・監査 CP60 の修正59＝全体の自己テストから軽い口 selftest_match を呼ぶ（正しいカタログの検査3 と写しの印の番人2つ）） | 直した後の文字 |
| 34 | `SDK/scripts/priority_rebuild/observe_diag.py` | 8516〜8517行（<モジュール直下>・監査 CP60 の修正59＝コマンドの旗 --selftest-match を足す（selftest_catalog と同じ形）） | 直した後の文字 |
| 35 | `.claude/breaks/b172_alma_weights_reversed.sh` | なし（新しいファイル） | 直した後の文字 |
| 36 | `.claude/breaks/b173_stc_zero_range_divides.sh` | なし（新しいファイル） | 直した後の文字 |
| 37 | `.claude/breaks/b174_hilo_short_column.sh` | なし（新しいファイル） | 直した後の文字 |
| 38 | `.claude/breaks/b175_dpo_centered_future.sh` | なし（新しいファイル） | 直した後の文字 |
| 39 | `.claude/breaks/b176_sarext_sign_not_abs.sh` | なし（新しいファイル） | 直した後の文字 |
| 40 | `.claude/breaks/b177_psar_af_column.sh` | なし（新しいファイル） | 直した後の文字 |
| 41 | `.claude/breaks/b178_cksp_long_short_swapped.sh` | なし（新しいファイル） | 直した後の文字 |
| 42 | `.claude/breaks/b179_pmax_ma_of_high.sh` | なし（新しいファイル） | 直した後の文字 |
| 43 | `.claude/breaks/b180_vwap_volume_weight_dropped.sh` | なし（新しいファイル） | 直した後の文字 |
| 44 | `.claude/breaks/b181_thermo_ma_column.sh` | なし（新しいファイル） | 直した後の文字 |
| 45 | `.claude/breaks/b182_copy_mark_without_known.sh` | なし（新しいファイル） | 直した後の文字 |
| 46 | `.claude/breaks/b183_copy_verified_by_tb_alone.sh` | なし（新しいファイル） | 直した後の文字 |

### 当てた記録（applied_fixes.json の名前 design:k4-reference-known-20261011）

| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 2 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 3 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 4 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 5 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 6 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 7 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 8 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 9 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 10 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 11 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 12 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 13 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 14 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 15 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 16 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 17 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 18 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 19 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 20 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 21 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 22 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 23 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 24 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 25 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 26 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 27 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 28 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 29 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 30 | `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 31 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 32 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 33 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 34 | `SDK/scripts/priority_rebuild/observe_diag.py` | 当てた | 2026-10-12T12:20:13 |
| 35 | `.claude/breaks/b172_alma_weights_reversed.sh` | 当てた | 2026-10-12T12:20:13 |
| 36 | `.claude/breaks/b173_stc_zero_range_divides.sh` | 当てた | 2026-10-12T12:20:13 |
| 37 | `.claude/breaks/b174_hilo_short_column.sh` | 当てた | 2026-10-12T12:20:13 |
| 38 | `.claude/breaks/b175_dpo_centered_future.sh` | 当てた | 2026-10-12T12:20:13 |
| 39 | `.claude/breaks/b176_sarext_sign_not_abs.sh` | 当てた | 2026-10-12T12:20:13 |
| 40 | `.claude/breaks/b177_psar_af_column.sh` | 当てた | 2026-10-12T12:20:13 |
| 41 | `.claude/breaks/b178_cksp_long_short_swapped.sh` | 当てた | 2026-10-12T12:20:13 |
| 42 | `.claude/breaks/b179_pmax_ma_of_high.sh` | 当てた | 2026-10-12T12:20:13 |
| 43 | `.claude/breaks/b180_vwap_volume_weight_dropped.sh` | 当てた | 2026-10-12T12:20:13 |
| 44 | `.claude/breaks/b181_thermo_ma_column.sh` | 当てた | 2026-10-12T12:20:13 |
| 45 | `.claude/breaks/b182_copy_mark_without_known.sh` | 当てた | 2026-10-12T12:20:13 |
| 46 | `.claude/breaks/b183_copy_verified_by_tb_alone.sh` | 当てた | 2026-10-12T12:20:13 |

### 実装の前と後の版（git）

- **実装の前**＝commit 8bcb87da
- **実装の後**＝commit ae172e29。★この工事の中で、設計書の 4-4 の手順（G-1 の表の作り直しほか）の道具が、TARGET のファイルを書き出し直すことがある（例＝gen_materials.py --write が regime_detection_kb.md の件数の囲みを書き出す）。その行は実装の指示ではなく、設計書の 4-4・5 で照らす

### 必読に要るファイル（道具が設計書と実装から拾った）

| ファイル | どこから拾ったか | 必読か |
|---|---|---|
| `SDK/.claude/rules/cat_requirements.md` | 要件定義書（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_requirements.md` | engine_tuner の要件（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones.md` | engine_tuner のマイルストーン（売買のロジックに触る工事） | 入れる |
| `SDK/.claude/ratchet/engine_tuner_milestones2.md` | M2 のマイルストーン（やることの番号 M2-C-15・M2-F-10f） | 入れる |
| `SDK/scripts/priority_rebuild/indicator_reference_diag.py` | 直す相手（TARGET） | 入れる |
| `SDK/scripts/priority_rebuild/observe_diag.py` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b172_alma_weights_reversed.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b173_stc_zero_range_divides.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b174_hilo_short_column.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b175_dpo_centered_future.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b176_sarext_sign_not_abs.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b177_psar_af_column.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b178_cksp_long_short_swapped.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b179_pmax_ma_of_high.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b180_vwap_volume_weight_dropped.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b181_thermo_ma_column.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b182_copy_mark_without_known.sh` | 直す相手（TARGET） | 入れる |
| `.claude/breaks/b183_copy_verified_by_tb_alone.sh` | 直す相手（TARGET） | 入れる |

---

## 答えの出し方（結果ファイルフォーマット）

### 結果の11節（名前と並びは変えない・どの種類の監査でも同じ）

`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-10-20_k4_reference_known_20261011_impl_cp82_audit_report.md` に、次の 11 節をこの順で出力する。

| # | 結果の節 | 依頼書の対応する項目 |
|---|---|---|
| 1 | **監査の相手と版**（依頼書のパス・監査の相手・ハッシュ値を照らした結果・実施日） | 監査依頼メタ情報 |
| 2 | **監査対象の型宣言**（数値型・コード型・文書型のうち該当するもの全部） | —（結果だけ） |
| 3 | **監査対象の事実データの確認**（依頼書の事実データを、自分で確かめた結果） | 事実データ |
| 4 | **所見**（依頼書の問いの番号をそのまま見出しにし、優先度の順に書く。一般の観点①〜⑦は、観点ごとに見つけた事と根拠。各所見の末尾に、対応する修正の番号を書く。直し方の文は書かない。省いた問いは番号を書く） | 確かめてほしいこと・問いの外から当てる視点 |
| 5 | **外部検索**（依頼書の件数の調べる物に1つずつ・URL と逐語） | 外の基準で確かめること |
| 6 | **依頼を出した CC の自己申告への答え**（依頼書の番号ごとに1件ずつ） | CC がまだ確かめていないこと |
| 7 | **総合判定**（結論＝GO／CONDITIONAL-GO／NO-GO と根拠・重さごとの件数） | 答えの出し方 |
| 8 | **修正の指示**（下の「修正の指示の書き方」の形だけで書く。重さは Critical・Major・Minor） | 着手前必読（直す相手のファイル） |
| 9 | **CC プロセス欠陥対策**（下の「修正の指示の書き方」の形だけで書く。重さは Process） | —（結果だけ） |
| 10 | **開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由** | 着手前必読 |
| 11 | **本物のファイルを書き替えていないこと**（`git status --short` の出力） | 監査人への宣言の禁止 |

### 重さと結論

- **Critical**＝結論を変える。**Major**＝直すべきだが、結論は変えない。**Minor**＝結論に効かせない。**Process**＝CC の進め方の欠陥（9 に書く）。
- **GO**＝Critical が0件。**CONDITIONAL-GO**＝Critical が在る（直せば先に進める）。**NO-GO**＝直し方の向きが違う（何が違うかを、4 の所見で、指摘の文と実物の行で示す）。
- どこまで直すかは、まこさんが結果を見て決める。だから修正は、重さの見出し（「### Critical」「### Major」「### Minor」「### Process」）の下に並べる。

### 修正の指示の書き方（★この形以外では書けない）

- **目的**：監査が書いた修正方法のとおりに、CC の改ざん・虚偽・矮小化・不正を通さずに直すため。
- **監査の種類**：設計書の内容確認、設計書どおりに実装できているかの確認など、どの種類の監査でも同じ欄で書く。
- **直す相手**：設計書・コード・実装データ（設定・json・法則ファイルなど）・文書・走らせるコマンドなど。どの相手の直しも同じ欄で書く。
- **直し方**：どの修正指示も、プログラムがそのまま実行できる形で書く。プログラムが欄のとおりに直しを当てる。CC は文も数も打たない。
- **直す範囲**：まこさんが結果ファイルを見て決める（Critical だけか、Major もか、Minor もか）。そのため修正は、重さの見出し（「### Critical」「### Major」「### Minor」「### Process」）の下に並べる。Process は 9 に書く。
- **所見との結び付き**：修正の番号は、4 の所見の末尾に書いた番号と同じにする。所見の無い修正は書かない。所見に書いた修正の番号は、必ず 8 か 9 に在るようにする。

1件は次の形で書く。

```text
### Critical

#### 修正 <番号>
対象のファイル: <リポジトリの中のパス>
直す箇所: <監査が読んだ時点の行番号の範囲>
直す前の文字:
~~~
<実物から1文字も変えずに写す>
~~~
直した後の文字:
~~~
<そのまま当てられる全文>
~~~
根拠の抜き書き: <ファイル名>:<行番号>「<その行の逐語>」
状態: <確定 / 未決 / 案が複数 のどれか>
```

**欄の決まり（6つ）**

1. **対象のファイル**：直すファイルを1つだけ書く。プログラムが作る文書（設計書など）は書けない。その文書の元データの直し1件と、作り直すコマンド1件の2件に分けて書く。作り直すコマンドの件は、元データを直す件と同じ重さの見出しの中で、その件のすぐ後ろに書く。
2. **直す箇所**：監査が読んだ時点の行番号の範囲。走らせるコマンドのときは「なし」。
3. **直す前の文字**：対象のファイルの中で1か所だけに当たる文字を、実物から写す。新しいファイルを作るときと、走らせるコマンドのときは「なし」。
4. **直した後の文字**：見出しを次の4つから1つ選ぶ。
   - **直した後の文字**：直す前の文字を、この全文に置き換える。
   - **足す文字**：直す前の文字のすぐ後ろに足す。新しいファイルを作るときは、ここに全文を書く。
   - **消す文字**：直す前の文字の中から、この文字を消す。
   - **走らせるコマンド**：1行のコマンドをそのまま書く。承認のスクリプトなど、まこさんが打つコマンドもここに書く。監査が走らせたときにかかった時間を、根拠の抜き書きに書く（恒久61番）。
5. **根拠の抜き書き**：「ファイル名:行番号」と、その行の逐語。
6. **状態**：「確定」「未決」「案が複数」の3つだけ。
   - **未決**：まこさんが決めるもの。
   - **案が複数**：4の欄を「案A」「案B」のように、案の数だけ並べる。

**プログラムが止めて、まこさんに報告するとき（2つだけ）**

1. 直す前の文字か、根拠の抜き書きが、実物と合わないとき。
2. 状態が「未決」か「案が複数」のとき。

止めた後どうするかは、まこさんが決める。

**書けないもの**

- 行番号と向きだけの指示（例＝「78-114行を〜の形にする」）。
- 散文の「修正の方向性」「直し方（案）」「対策＝〜にする」。
- 取り下げ。一度出した結果ファイルに、あとから指示の取り下げを書き足さない。
- 1件に2つ以上のファイル。ファイルごとに件を分ける。
- 行ごとに残す・直す・消す・足すを並べた表。1行を1件にする。

**当てる順番**＝修正の番号の順。

### 修正をどこに書くか

実装が設計書と違う所は、その実装のファイルに書いてください（修正を当てるプログラムが当てます。.claude/hooks・.claude/tools・.claude/breaks のファイルには当てず、CC が書きます）。設計書の誤りは、設計書の元（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/k4-reference-known-20261011/やることの表.md`）に書いてください（設計書はプログラムが作るので直接は書けない）。

### 守ること

- CC は自分で「合っている」「動く」と判定していない（恒久64番）。それを確かめるのが、この監査。
- 乱数は禁止（恒久67番）。乱数を残す・足す形なら Critical にする。
- 監査は1つの工事につき1回（恒久65番）。どこまで直すかは、まこさんが結果を見て決める。
- 目標（全月 net ≥ $1,900）を下げる方向の提案はしない。目標の達成可能性の判定が対象外なら、明示する。
- net は M2-L まで使わない（まこさん決定 2026-09-01）。
- トレードについての外部認知（Crypto futures algo trading の業界実情）を踏まえる。

---

## 起動の仕方（まこさん向け呼びかけ例文）

別の Claude Code セッションを開き、本依頼書のパスを示して依頼する:

```
監査してほしい
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-20_k4_reference_known_20261011_impl_cp82_audit_request.md
```

→ 監査人の CC が、冒頭の宣言を読んで Plan agent を起動し、結果ファイルを書くまで自走する。

依頼書終わり。

<!-- gen_audit_docs: request src=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp82_work/cp82_src.gen.md src_sha256=1ffd2f60773e5c324b11fc1904512dfd5723bf9ce2d599543dd678dda38c508d body_sha256=7638266fc36570223f413327629f1a4884ef822429f7393907112eece76b566a -->
