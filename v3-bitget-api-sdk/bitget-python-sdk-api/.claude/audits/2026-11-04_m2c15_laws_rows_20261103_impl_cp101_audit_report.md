# 監査結果 cp101 — CP101 — レベル3 の法則のデータに行を写し、読むプログラムを作る。ToDo の209番・M2-C-15（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-11-04_m2c15_laws_rows_20261103_impl_cp101_audit_request.md`
- 依頼書のハッシュ値: b98fc3343f3311aa4b543c73ed2c811e80b3b6c560788266c7fd7aa619c67290
- 監査の相手と版（依頼書に書いてあるもの）: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2c15-laws-rows-20261103.md` ／ ハッシュ値 4d785eea322aa0bfc4b301e8ff7821ddb4288a526a8611a976e5310a41e8eec2
- 監査が照らしたハッシュ値: 4d785eea322aa0bfc4b301e8ff7821ddb4288a526a8611a976e5310a41e8eec2（承認の控えの実物・`git show 8ed860d0:<控え>`・`.claude/state/acceptance.approved`・`.claude/state/acceptance.md` の4つが同じ）
- 実施日: 2026-11-04


## 2. 監査対象の型宣言

数値型（法則の中の数50行と、使い方の行の閾値）・コード型（laws.py・check_one_path.py の T44・pre_audit_check.py・壊すプログラム11本）・文書型（法則一覧.md・要件定義書）の3つ全部に当てはまります。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

依頼書の表と合います。監査は、当てる道具の読み取り関数 read_design_fixes で承認の控えを読みました。結果は34件です。対象のファイルの並びも依頼書の表のとおりです（cp101_work/q1_replay.py）。

### 当てた記録（applied_fixes.json の名前 design:m2c15-laws-rows-20261103）

依頼書の表と合います。34行で、番号は1〜34、当て方は全部「当てた」、時刻は全部 2026-11-04T09:11:45 です（cp101_work/q11_check.py）。

### 実装の前と後の版（git）

実装の前は bf699d9f、実装の後は 8ed860d0 です。依頼書のとおりです。依頼書の後に、commit 73d84bd4（2026-11-04 11:51:56）が入りました。これは依頼を出したセッションの締めのコミットです。対象のファイルの作業ツリーは 8ed860d0 と同じです（q1_replay.py の「作業ツリーと後の版＝同じ」が全行）。

### 必読に要るファイル（道具が設計書と実装から拾った）

依頼書の表のファイルは全部実在します。Plan agent が33件を開きました。応じた範囲は10節に書きます。


## 4. 所見

答えなかった問いはありません。

### 一般の観点

- ①統計学的妥当性：数字の根拠が足りているかを見ます。 ＝ 新しい数は BB%b の 1.0129892 の1つです。laws_rows_build.py --bb-check で測ると、値決め窓 158,112本で旗 8,085本・%b 8,085本・違い0本、全期間 551,916本で旗 27,935本・%b 27,935本・違い0本でした。n＝20 に限る値であることは、設計書 6-2 の#2 に書いてあります。ほかに統計の根拠を使う数はありません。
- ②リスク管理：損失が出たときや、プログラムが壊れたときの備えが在るかを見ます。 ＝ いまの売買には届きません。engine_tuner は laws.json を読みません。読み始める196番・M3-1・M4 より前に直さないと効く物が、Q11 の修正1〜9 です。合計 0.12 BTC を動かす行はありません。
- ③認知バイアス：CC の思い込みで組まれた所が無いかを見ます。 ＝ 写すプログラムが「読んだ鍵は写した」と数えています。このため、理由の文のうち4行が実物と合いませんでした（Q11 の3つ目）。依頼書の経緯は「鍵98件の理由を確かめていない」と自分で書いていて、そのとおりの所に誤りが在りました。
- ④ソフトウェア工学：プログラムの作りが正しいかを見ます。重複・壊れやすさ・テストの抜けが、見る物です。 ＝ 3つ見つけました。1つ目に、laws_rows_build.py:37 の line_of は探す文字を最初に含む行を返すので、出どころの行が値の無い行になります（Q11 の2つ目）。2つ目に、完成の条件 F-13 は grep -c なので「4本が在る」を測りません（Q6）。3つ目に、engine_tuner_gen.py:2059 の TP_PCT に side_sign がありません。engine_tuner_exec.py:2404〜2406 は side_sign が無いと建値に k をそのまま足すので、SHORT の利確が建値より上になります。これは読んだだけで、走らせていません。engine_tuner のコードはこの工事の範囲の外です。乱数は0件です。laws.py の変数 rng は範囲の名前で、乱数ではありません。
- ⑤再現性：同じ手順で、同じ結果が出るかを見ます。 ＝ 当て直しは、22行を先に入れれば、対象の19ファイルのうち17本で実装の後と1文字も同じです。残り2本の差は、経緯に書かれた出どころの2行です。laws_rows_build.py をいま走らせ直すと、この2行は :5 に戻ります（修正16・17）。
- ⑥実行プロセス：CC が、決めた流れのとおりに進めたかを見ます。 ＝ 2つ見つけました。1つ目に、設計書 6-5 の#2 は「b213 の結果を実装の監査の依頼書に書く」と書いていますが、依頼書には測り方だけで結果がありません。監査が測ると rc=1 でした。2つ目に、締めのコミット 73d84bd4 が作業場 cp101_work を丸ごと git に入れました（修正25）。そのうち q1_applied の18本は、監査人の私が作業場に作った写しです。
- ⑦主エージェントバイアス：CC が、自分に都合よく判定した所が無いかを見ます。 ＝ session_worklog_20261104.md:77 は「`--verify` が ❌ のまま進めた」と書いていますが、依頼書の経緯はこの ❌ を書いていません。原因は next_move.py:316 が設計書を指定せずに呼ぶことです（修正24）。監査が承認の控えを指定して走らせると「監査に出せます」と出ました。

### Q0 — 作った後の確認を走らせて通るか（優先度 A）

通ります。`check_one_path.py --work m2c15-laws-rows-20261103` の結果は「通る 1 件・見た範囲 0 件・通らない 0 件・未作 0 件」です。T44 は「S1 の枝 12/12 本がレシピと同じ。役割が未確認＝BB%b・RSI・基準線。置き替え＝枝S1-MTFCUT: +2σ の旗を BB%b の 1.0129892 より上に置き替えた」と出ました（動かした）。

修正の番号＝なし

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

依頼書の手順のままでは、4件が当たりません。実装14・17・19・20 の「直す前の文字」は「済＝208番」を含みますが、bf699d9f の実物は `"208"` です。経緯の22行を先に入れた版で当てると、10件とも当たりが1で、req_trace_src.json は実装の後と1文字も同じになりました。

対象の19ファイルのうち、16本は bf699d9f からそのまま当てて1文字も同じです。laws.json は2行、法則一覧.md は2行違います。4行とも経緯の出どころの直し（:5 → :15・:16）です（動かした・cp101_work/q1_replay.py）。

修正の番号＝なし

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

対象のファイルの中で、実装の指示に当たらない行は、経緯に書かれた2種だけです。req_trace_src.json の「済＝208番」のうち18行（残り4行は実装14・17・19・20 の相手）と、laws.json と法則一覧.md の出どころの4行です。

対象の外で変わったファイルは、req_trace.md（設計書 4-12 の gen_req_trace.py --write が作る物）・CP100 の結果・applied_fixes.json・breaks_frozen.json と、承認の控えと verbatim の下です。engine_tuner のコードに差はありません。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

合います。34件で、番号は全部そろい、記録にだけ在る番号はありません。対象のファイルも1件ずつ同じです（Plan agent が設計書の組と diff で照らした）。「もう当て終わっていた」は0件です。CP100 の修正の記録は 5・19・20・22・25・26・27・29・30・31 の10件で、依頼書の経緯のとおりです。

修正の番号＝なし

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 A）

14行とも rc=0 です。行ごとの結果は Q10 の1つ目に書きます。F-13 だけは、条件の文を測っていません。条件は「4本が在る」ですが、コマンドは grep -c で、出力は 5 です。指紋の行 `"laws/laws.py",` も数えるためです。grep -c は1件でも rc=0 になります。CHECKS の中に4本が在ることは、pre_audit_check.py:68〜71 を読んで確かめました。設計書はもう承認済みなので、この文の直しは修正にしません。

修正の番号＝なし

### Q8 — 当てた記録に無い修正22件は、設計書と実装に入っているか（優先度 A）

1つ目。22件とも入っています。動かしたものは3つ目に書きます。読んで確かめた物は次のとおりです。

- 修正1：laws.py:126〜128・:198・:225〜232
- 修正2：FINSTOP の「値を負にするか」・laws.py:545
- 修正3：check_one_path.py:302〜328・:359・:374〜399・:408〜427
- 修正4（案B）：設計書 4-21 の番号4・使い方の行 1.0129892・check_one_path.py:299
- 修正6：設計書 6-2 の#2
- 修正7：laws.py:372〜405・:424〜429
- 修正8：laws.py:133〜151・:234〜240・:295〜305
- 修正9：前半は b213 に入り、後半は経緯のとおり外した
- 修正10：pre_audit_check.py の CHECKS と指紋
- 修正11：laws.py:457〜566
- 修正12：設計書:5058
- 修正13：req_trace_src.json（22行へ広げた）
- 修正14：設計書:375
- 修正15：設計書 6-5 の#6〜#9
- 修正16：枝型の行に優先の順が無い・設計書:4951
- 修正17：設計書 4-21 の番号7
- 修正18：数の行が50行・S1_直近の安値の本数が1行
- 修正21：設計書:4947
- 修正23：玉の状態の「入口で使えない」が true
- 修正24：設計書 6-5 にその行が無い
- 修正28：設計書:373
- 修正32：laws_rows_build.py --unused-keys が「98件・理由なし0件」と出す

修正32 の一覧は、branch_types・S1 の鍵・S1〜S5 の logics だけが相手で、LOGICS.global・search_space・tuner は出ません（laws_rows_build.py:621〜628）。これらは写す元の鍵ですが、値は行へ写していません。

2つ目。CC の変更で、ほかの修正の中身は変わっていません。修正13 の22行は工事の欄の文字だけです。修正9 の後半は修正25・26 に影響しません。修正14 の相手を絞った後も、余白と建値待ちの本数は --check-sources の CONST_REGISTRY の照らし（laws.py:512〜517）で比べています。修正20 の36行は、数50行から共通14行を引いた数と合います。

3つ目。CP100 の壊し方は、全部いま止まります（動かした・メモリの上の写し・cp101_work/q8_mut.py）。

- Q8 の表の11行を15通りで試し、素通りは0件でした。無傷の版は 12/12 で通ります。
- 止める操作は正しく動きます。枝S1-TP2・枝S1-SHRINK・確認S1 を全部オフ＝読めます。売り方S1 だけオフ＝読めます。S1 の行17行を全部オフ＝読めて23行が残ります。枝S1-TP2 だけオフ＝止まります。
- 足す操作は正しく動きます。RSI の LONG の行＝解けます。CCI の行＝候補が複数1件と出ます。帯pivot の行＝落ちません。RSI の使い方の行が返らないとき＝止まらず、使える物が無い1件と出ます。
- 修正2 は、印を消すと --check-sources が「枝型-FINSTOP の negative」と止めます。
- 修正8 の見本13件は、全部止まるか、オフとして返しません。

修正の番号＝なし

### Q9 — 実物は、実装の指示34件のとおりか（優先度 A）

1つ目。実装ごとの結果は次のとおりです（q1_replay.py の「いまの実物に在る」）。

- 実装1〜4・6・7・9〜34：「直した後の文字」が実物に1文字も違わず在ります。
- 実装5：2行違います（出どころの :5 → :15・:16）。
- 実装8：2行違います（法則一覧.md の同じ2行）。

2つ目。実装の指示に無い変更は、経緯に書かれた2種だけです（Q2）。commit 8ed860d0 の後に、対象のファイルは変わっていません。

修正の番号＝なし

### Q10 — 完成の条件と試験は、設計書のとおりに動くか（優先度 A）

1つ目。14行の結果は次のとおりです（動かした・cp101_work/q6_conditions.sh）。

- F-1・F-2・F-6・F-9・F-10・F-11・F-12：rc=0、true
- F-3：rc=0、「法則の読む口の自己テスト＝43/43」
- F-4：rc=0、「法則一覧.md は作り直した物と同じ」
- F-5：rc=0、「写す元との照らし＝違い0件」
- F-7：rc=0
- F-8：rc=0、「要件の行＝752 行・止める理由＝0 件」
- F-13：rc=0、出力 5
- F-14：rc=0

2つ目。run_breaks.py --design <設計書> --measure-only の結果は「止まった 7/7」です。b234〜b240 は全部 rc=1（期待 1）です。走らせる前と後で、laws.json・laws.py・indicators.json・法則一覧.md・check_one_path.py のハッシュ値は同じです。

3つ目。b213 は rc=1（期待 1）で「止まった 1/1」です。問いの外ですが、実装21・23・24 の相手も測りました。b211 は前の工事の設計書を相手に rc=1、b228 と b230 は m2c15-outside-record-20261102.md を相手に rc=1 です。

4つ目。使い方の記録だけが 16 から 20 になりました。指標の記録306件と部品の記録8件は、bf699d9f と同じです（動かした・q11_check.py）。列を作る組は、いまの --count で 652組です。bf699d9f の版は走らせていません。indicators.py は bf699d9f と差分0行で、列を作る組は指標の記録と部品の記録から作るので（indicators.py:371〜）、同じ数です（読んだだけ）。

修正の番号＝なし

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

同じです。2つの設計書は同じファイルです。控えのハッシュ値・承認の印の値・控えのコミットの版（8ed860d0）が全部 4d785eea… で同じです。実装に影響する違いはありません。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

一覧に在るのに実装の指示に無い物は2つです。

1つ目は F-14 の「表10 の法則の行」です。実装27 は第3章の2 の文だけを直し、要件定義書:354 の「相場の法則の文と、プログラムが読む判定」は直っていません。この工事が入れた売り方・決済の枝などの行が、表に載っていません。

2つ目は F-9 の「壊す処理」です。実装21 は measure の行だけを直しました。laws.json の「構造に要ること」に b211 が消す16 は無いので、b211 は rc=1 で落ちます。動きに問題はありません。

実装の指示に在るのに一覧に無い物は、選べる値の「使えない単位」「未作の部品」「数だけの単位」「枝の名前で指せる語」と、欄の「値を負にするか」です。どれも CP100 の修正2・8 の分で、問題はありません。

修正の番号＝23

### Q11 — 実装で設計書と違った点の扱いは、正しいか（優先度 B）

1つ目。確かめの抜けはありません。g2_pass.json と h2_pass.json の対象のハッシュ値を、enforce_g2_pass.fingerprint・leak_causality_diag.h2_fingerprint と同じ式で作り直すと、G2 は 4d21bf6f5f85ccc0、H2 は 024062a98c1a5451 で、記録と同じです（動かした・q11_check.py）。どちらも missing は空です。`pre_audit_check.py --verify --design <承認の控え>` は「監査に出せます（チェックの1枚が新しく、全部 rc=0）」と出ました。

2つ目。説明の文の行を指す行は0件です。値の無い行を指す行が2行在ります。

- S1_TCTP_幅 の :88 は `"level": { "kind": "pct", "base": "avg",` で、値は :89 に在ります（修正11・12）。
- S1_床の倍数 の :30 は `"fee_floor": { "const": "SCALP_FLOOR" }` で、値の 1 はレシピの全行に在りません。T44 は check_one_path.py:416 で 1 と const を照らしています。1 は設計書 4-21 の「新しく入る数字」の一覧にも在りません。出どころの形を変えると laws.py:510 の形から外れるので、修正は書きません。

残りの48行は値が在ります。V59DOWN と V59FLAT の幅は文字の末尾だけ違いますが、float として同じです（動かした）。同じ作りの誤りは、使い方の行の DI差（:69・値は :70）と基準線（:78・値は :79）にも在ります（修正19〜22）。原因は line_of です（修正16〜18）。案の探す文字で、:15・:16・:89 になることを確かめました（動かした・q12_fix_try.py）。

3つ目。文字どおり「効かない」と書いた行は2行（fire の role と record）で、実物と合います。ただし、実物と合わない理由が4行在ります。

- `enabled`：「法則の中身でない」と書いています。実物は S2〜S5 が false で（e38_logics.json:148・:190・:226・:262）、e38_priority_stack.py:64 が読みます。売買に効く旗です。laws.json はこの4行を全部オンにしています（法則一覧.md）。設計書の Y-10 は「段⑤より前は S1 だけを通す」です（修正5〜9・13）。止める置き場は、要件定義書の表26 の5番が 241番の未決としているので、未決と書きます。
- `entry.params`：「S2〜S5 の値は未確定」と書いています。S2 の `ceil_filter` は `"flat_up"` で確定値です（e38_logics.json:162）。e38_logic_parts.py:281 が読み、建てる時が変わります。受け先の 6-5 の#7 にこの鍵がありません（修正10）。
- `reason_pending_side`：「売買の方向で決まる」と書いています。実物は登録の提案の側です（gen_exit_families.py:281・修正14）。
- `S1.meta.regime.*`：「レシピの案内」と書いています。entry_col と block_col は売買に効きます（engine_tuner_exec.py:1115・修正15）。

理由の文のほかに、値の向きが写す元と食い違う行が4行在ります。枝型-TP_PCT・BEEXIT・BESTALE・REVERSE_IND は決済の側が「利の側」ですが、値段の決め方に「向き」がありません。laws.json:1211 は、欄が無いときの既定を「建値から%の向き＝損の側」と書いています。engine_tuner_gen.py:2120・:2127・:2148 は3本に side_sign を入れています。設計書のとおりの実装で、実装の誤りではありません。--check-sources も T44 も比べません。受け先の 6-5 の#6 にも入っていません。読み始める M4 で、利確の値段が逆の側になります（修正1〜4）。案を写しで試すと、読み込み・T44・--check-sources は通ります（動かした・q12_fix_try.py）。

このほかに、枝型-TIME は hold_min（分）を保有の範囲_スキャル（本数）と比べる形です。engine_tuner_gen.py:2032 は scale=5 を掛けます（Plan agent が読んだ）。設計書 6-5 の#6 に hold_bars がありません。受け先の見出しが無いので、修正は書きません。

修正の番号＝1・2・3・4・5・6・7・8・9・10・11・12・13・14・15・16・17・18・19・20・21・22・24・25


## 5. 外部検索

### 検索 1 — 区分ごとに欄が違う記録を1つの表で持つ作り

検索の言葉のとおりに調べ、本文を1件開きました。種類ごとの欄を定義で持ち、読む口がそれを読む作りは、外の一般の作り方に合います。実装も合います。laws.py:107 は種類の表に無い種類で止まり、:264〜265 は種類に無い欄で止まります。

- https://warlock.js.org/v/latest/seal/recipes/polymorphic-data/ 「Look up the branch in the key→branch map built at construction.」「If the discriminator’s value isn’t in the map, validation fails with one clear error」

### 検索 2 — 売買ルールをデータで持つ作り

検索の言葉のとおりに調べ、本文を1件開きました。決済の枝の順を明示する作りは、外の一般の作り方に合います。実装の枝S1 は優先の順を行に持ちます。枝型は持ちません（設計書 5節の決定・M4-8）。この作りそのものを定めた標準は、検索の結果にありませんでした。

- https://www.freqtrade.io/en/stable/strategy-callbacks/ 「The exit-reasons (if applicable) will be in the following sequence:」


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

進めてよいです。秒数を測った完成の条件14行は、各行0〜1秒でした。ほかに走らせた物も、1回の呼び出しの上限（2分）に達していません（10節）。

### 自己申告 2

進めてよいです。e38_logics.backup_20260802_005140.json は未追跡のままで、この工事の対象の外です。Q1 と Q2 の差分は対象のファイルだけで取りました。


## 7. 総合判定

### 結論と件数

- 結論＝GO（根拠＝Critical が0件です。実装は設計書の 4-20 のとおりで、違いは経緯に書かれた2種だけです。完成の条件14行・壊すプログラム・T44・G2・H2 の指紋を、監査が走らせて確かめました）
- Critical＝0
- Major＝10
- Minor＝13
- Process＝2

このとおりに実装できていることは確かめました。目標（全月 net ≥ $1,900）を達成できるかは、engine_tuner がまだ laws.json を読まないので、この監査の対象の外です。


## 8. 修正の指示

### Critical

なし

### Major

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 1917〜1927行
直す前の文字:
~~~
    "出どころ": "exit_families_rules.json:39"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "建値",
    "幅": "state_mult_range"
~~~
直した後の文字:
~~~
    "出どころ": "exit_families_rules.json:39"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "建値",
    "幅": "state_mult_range",
    "向き": "利の側"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:2405「        if lv["k"].get("side_sign") == "profit":」
状態: 確定

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 2044〜2054行
直す前の文字:
~~~
    "出どころ": "exit_families_rules.json:117"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "平均建値",
    "幅": "state_mult_range"
~~~
直した後の文字:
~~~
    "出どころ": "exit_families_rules.json:117"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "平均建値",
    "幅": "state_mult_range",
    "向き": "利の側"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2120「"k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},」
状態: 確定

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 2080〜2090行
直す前の文字:
~~~
    "出どころ": "exit_families_rules.json:140"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "平均建値",
    "幅": "state_mult_range"
~~~
直した後の文字:
~~~
    "出どころ": "exit_families_rules.json:140"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "平均建値",
    "幅": "state_mult_range",
    "向き": "利の側"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2127「"k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},」
状態: 確定

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 2169〜2179行
直す前の文字:
~~~
    "出どころ": "exit_families_rules.json:197"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "平均建値",
    "幅": "state_mult_range"
~~~
直した後の文字:
~~~
    "出どころ": "exit_families_rules.json:197"
   },
   "決済のしかた": {
    "置き方": "足の途中に置く",
    "方法": "指値",
    "側": "利の側"
   },
   "値段の決め方": {
    "種類": "建値から%",
    "基準": "平均建値",
    "幅": "state_mult_range",
    "向き": "利の側"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2148「"k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},」
状態: 確定

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 1282行
直す前の文字:
~~~
   "計算の関数": "pullback_short",
~~~
直した後の文字:
~~~
   "オン/オフと注意": {
    "状態": "オフ"
   },
   "計算の関数": "pullback_short",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.json:148「      "enabled": false,」
状態: 未決

#### 修正 6
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 1298行
直す前の文字:
~~~
   "計算の関数": "fade_short",
~~~
直した後の文字:
~~~
   "オン/オフと注意": {
    "状態": "オフ"
   },
   "計算の関数": "fade_short",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.json:190「      "enabled": false,」
状態: 未決

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 1314行
直す前の文字:
~~~
   "計算の関数": "zscore_short",
~~~
直した後の文字:
~~~
   "オン/オフと注意": {
    "状態": "オフ"
   },
   "計算の関数": "zscore_short",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.json:226「      "enabled": false,」
状態: 未決

#### 修正 8
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 1330行
直す前の文字:
~~~
   "計算の関数": "grid_short",
~~~
直した後の文字:
~~~
   "オン/オフと注意": {
    "状態": "オフ"
   },
   "計算の関数": "grid_short",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.json:262「      "enabled": false,」
状態: 未決

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/法則一覧.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py:20「  python3 laws.py --write          # 法則一覧.md を作る」（走らせたときの時間＝--verify の同じ処理が1秒以内）
状態: 未決

#### 修正 10
対象のファイル: .claude/state/indicator_review/laws_rows_build.py
直す箇所: 580行
直す前の文字:
~~~
S2〜S5 の値は未確定。M3-1 で、
~~~
直した後の文字:
~~~
S2〜S5 の値は null で未確定。例外は S2 の ceil_filter＝flat_up（確定値で、建てる時が変わる）。M3-1 で、
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logic_parts.py:281「    ceil_filter = entry_params.get("ceil_filter")          # ★型の限定（S2=flat_up 専用・まこさん承認 2026-07-25」
状態: 確定

### Minor

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.json
直す箇所: 3180行
直す前の文字:
~~~
"出どころ": "recipes/identity_s1_legacy.json:88"
~~~
直した後の文字:
~~~
"出どころ": "recipes/identity_s1_legacy.json:89"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:89「                           "k": { "legacy": 0.0008, "side_sign": "profit" } } } },」
状態: 確定

#### 修正 12
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/法則一覧.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py --write
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/laws/laws.py:20「  python3 laws.py --write          # 法則一覧.md を作る」（走らせたときの時間＝--verify の同じ処理が1秒以内）
状態: 確定

#### 修正 13
対象のファイル: .claude/state/indicator_review/laws_rows_build.py
直す箇所: 575行
直す前の文字:
~~~
売り方の切り替えの旗で、法則の中身でない。法則のオン/オフは ⑤-10 で持つ
~~~
直した後の文字:
~~~
売り方の切り替えの旗で、売買に効く（S1 は true、S2〜S5 は false）。法則のオン/オフは ⑤-10 で持つ
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_priority_stack.py:64「        if lg["enabled"]:」
状態: 確定

#### 修正 14
対象のファイル: .claude/state/indicator_review/laws_rows_build.py
直す箇所: 592行
直す前の文字:
~~~
売買の方向で決まる決済の理由の保留。枝の型を案にする M4-1 で受ける
~~~
直した後の文字:
~~~
score.py に未登録の決済の理由の、登録の提案の側（maker か taker）。枝の型を案にする M4-1 で受ける
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_exit_families.py:281「                ng.append(f"枝 {bid}: 決済理由 {rsn} が score.py 未登録なのに、登録の提案の側"」
状態: 確定

#### 修正 15
対象のファイル: .claude/state/indicator_review/laws_rows_build.py
直す箇所: 600行
直す前の文字:
~~~
レシピの案内。売買の方向は売り方S1 に持つ
~~~
直した後の文字:
~~~
レシピの案内と場面の列の指定。entry_col と block_col は売買に効く。売買の方向は売り方S1 に持つ
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:1115「#     block_col  … このバーでは新規の発注を止める、を表す列の名前（要らなければ null）」
状態: 確定

#### 修正 16
対象のファイル: .claude/state/indicator_review/laws_rows_build.py
直す箇所: 143行
直す前の文字:
~~~
sp["down_window_hours"]["legacy"], "down_window_hours")
~~~
直した後の文字:
~~~
sp["down_window_hours"]["legacy"], '"down_window_hours"')
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:15「      "down_window_hours": { "legacy": 1.0 },」
状態: 確定

#### 修正 17
対象のファイル: .claude/state/indicator_review/laws_rows_build.py
直す箇所: 144行
直す前の文字:
~~~
sp["max_age_hours"]["legacy"], "max_age_hours")
~~~
直した後の文字:
~~~
sp["max_age_hours"]["legacy"], '"max_age_hours"')
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:16「      "max_age_hours": { "legacy": 6.0 },」
状態: 確定

#### 修正 18
対象のファイル: .claude/state/indicator_review/laws_rows_build.py
直す箇所: 186行
直す前の文字:
~~~
f"{nm}_幅", "割合", '"pct"', start)
~~~
直した後の文字:
~~~
f"{nm}_幅", "割合", '"k"', start)
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:89「                           "k": { "legacy": 0.0008, "side_sign": "profit" } } } },」
状態: 確定

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json
直す箇所: 99043行
直す前の文字:
~~~
"出どころ": "identity_s1_legacy.json:69"
~~~
直した後の文字:
~~~
"出どころ": "identity_s1_legacy.json:70"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:70「                           "value": { "legacy": 28.102910192963172 },」
状態: 確定

#### 修正 20
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json
直す箇所: 99062行
直す前の文字:
~~~
"出どころ": "identity_s1_legacy.json:69（工事
~~~
直した後の文字:
~~~
"出どころ": "identity_s1_legacy.json:70（工事
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:70「                           "value": { "legacy": 28.102910192963172 },」
状態: 確定

#### 修正 21
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json
直す箇所: 99081行
直す前の文字:
~~~
"出どころ": "identity_s1_legacy.json:78",
~~~
直した後の文字:
~~~
"出どころ": "identity_s1_legacy.json:79",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:79「                           "value": { "legacy": 0.283351853801863 },」
状態: 確定

#### 修正 22
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json
直す箇所: 99101行
直す前の文字:
~~~
"出どころ": "identity_s1_legacy.json:78（工事
~~~
直した後の文字:
~~~
"出どころ": "identity_s1_legacy.json:79（工事
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/identity_s1_legacy.json:79「                           "value": { "legacy": 0.283351853801863 },」
状態: 確定

#### 修正 23
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/要件定義書_レベル4_指標の構造.md
直す箇所: 354行
直す前の文字:
~~~
| 法則の行 | 相場の法則の文と、プログラムが読む判定 | 法則1件に1件 |
~~~
直した後の文字:
~~~
| 法則の行 | 相場の法則と組み合わせの法則の文とプログラムが読む判定（195番）。売り方・建てる前の確認・決済の枝・玉全体の決済・玉の持ち方の行（209番） | 法則1件に1件 |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2c15-laws-rows-20261103/やることの表.md:25「表10 の法則の行・第3章の2 の法則の文」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 24
対象のファイル: .claude/tools/next_move.py
直す箇所: 316行
直す前の文字:
~~~
rc, last = run(["python3", ".claude/tools/pre_audit_check.py", "--verify"])
~~~
直した後の文字:
~~~
rc, last = run(["python3", ".claude/tools/pre_audit_check.py", "--verify", "--design", str(f["archive"] or f["design"])])
~~~
根拠の抜き書き: .claude/tools/pre_audit_check.py:384「ng.append(f"チェックが照らした設計書が違う（照らした {got} ／ 問われた {want}）＝ --run --design {want} を打つ")」
状態: 確定

#### 修正 25
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp101_work/q1_applied
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
git rm -r --cached v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp101_work/q1_applied
~~~
根拠の抜き書き: .claude/rules/permanent_rules.md:526「同じ中身の写し・控えを作りたくなったとき」（走らせていないので時間は測っていない。ファイルは消さず git の記録からだけ外す。コミットは まこさんの OK の後）
状態: 確定


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

開いたファイルと行は次のとおりです。

- 全文：依頼書・laws.py（監査の CC は1〜599行、Plan agent は全行）・identity_s1_legacy.json・exit_families_rules.json・やることの表.md・法則一覧.md・壊すプログラム11本・laws_rows_build.py（Plan agent）
- 設計書：Plan agent は 296〜854・4326〜4645・4900〜5387 を読み、実装5〜9 を差分で照らしました。全行は読んでいません。実装の指示の全文は q1_replay.py が機械で照らしました。
- 指定の範囲：cat_requirements.md:268〜290、engine_tuner_requirements.md:28〜60、engine_tuner_milestones.md:132〜150、engine_tuner_milestones2.md:81〜109、CP100 の結果:125〜200・:476〜998、indicators.py:215〜334、indicator_reference_diag.py:6003〜6056、search_limits.json:14〜37、e38_logics.json:28〜100・:140〜290、check_one_path.py:1〜40・:260〜549、req_trace_src.json の指定の行、pre_audit_check.py:60〜80・:120〜135・:367〜384、要件定義書の該当の行
- そのほか：engine_tuner_exec.py:1112〜1116・:2372〜2410・:2518〜2540、engine_tuner_gen.py:2045〜2152、e38_logic_parts.py:281〜283・:365〜398、e38_priority_stack.py:37〜95、gen_exit_families.py:270〜290、apply_audit_fix.py:1〜100・:1000〜1135、next_move.py:118〜126・:304〜320、session_worklog_20261104.md:50〜86、require_acceptance_before_impl.sh:372〜410

走らせたコマンドと結果は次のとおりです。秒数を測った物には秒数を書きました。ほかは1回の呼び出しの上限（2分）に達していません。

- python3 .claude/tools/check_one_path.py --work m2c15-laws-rows-20261103：通る 1 件。
- python3 cp101_work/q1_replay.py：34件。4件は当たり0、22行を先に入れると当たり1。対象19本のうち違いは経緯の分だけ。
- bash cp101_work/q6_conditions.sh：14行とも rc=0。各行0〜1秒。
- python3 cp101_work/q11_check.py：記録34件、指標の記録と部品の記録が同じ、G2 と H2 の指紋が記録と同じ、出どころの全50行。
- python3 cp101_work/q8_mut.py：素通り0件。
- python3 cp101_work/q12_fix_try.py：修正の案で読み込み・T44・--check-sources が通る。
- python3 .claude/tools/run_breaks.py --design <承認の控え> --measure-only：止まった 7/7。
- python3 .claude/tools/run_breaks.py --design <m2c15-indicator-structure-20261031.md> --measure-only --only b213_place_missing.sh：rc=1。同じ形で b211：rc=1。
- python3 .claude/tools/run_breaks.py --design <m2c15-outside-record-20261102.md> --measure-only --only b228_laws_kubun_missing.sh：rc=1。同じ形で b230：rc=1。
- python3 .claude/tools/pre_audit_check.py --verify：止まる（照らした設計書が違う）。--design <承認の控え> を付けると「監査に出せます」。
- python3 .claude/state/indicator_review/laws_rows_build.py --unused-keys：98件・理由なし0件。
- python3 .claude/state/indicator_review/laws_rows_build.py --bb-check：1.0129892 で違い0本。
- python3 scripts/priority_rebuild/indicators/indicators.py --count：使い方の記録 20件・列を作る組 652組。

走らせられなかったものと理由は次のとおりです。

- run_breaks.py を複合のコマンドで打つ形は、土台ゲートが止めました。単独の形で走らせ直しました。
- bf699d9f の版の indicators.py --count は走らせていません。Q10 の4つ目のとおり、読むプログラムの差分が0行で、元の記録が同じだからです。
- pre_audit_check.py --run は走らせていません。--verify が記録の新しさを確かめるためです。engine_tuner_gen.py:2059 の TP_PCT の動きも走らせていません（engine_tuner のコードは範囲の外）。


## 11. 本物のファイルを書き替えていないこと

`git status --short` の出力のうち、未追跡を除いた行は次のとおりです。

```
 M .claude/state/session_worklog_20261104.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp101_work/cp101_result.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp101_work/q11_check.py
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
```

- session_worklog_20261104.md と decisions.md は、依頼を出したセッションの変更です。監査は書いていません（監査の開始の時点で、どちらも M でした）。
- cp101_result.md と q11_check.py は、監査の作業場のファイルです。締めのコミット 73d84bd4 が作業場を git に入れた後に、監査が直しました。
- 未追跡に増えた物は、作業場の q12_fix_try.py と cp101_result.review.md と、この結果ファイルです。ほかに監査が書いた物は、同じセッションのフォルダ `.claude/state/sessions/d7b9da10-6834-4eb7-8df0-817812c34a05/` の lessons.md（hook block_repeat_kind.sh が求めた）と diagnosis.md（hook block_repeat_failure.sh が求めた）です。
- 壊すプログラムは本物を仮に書き替えて戻します。走らせる前と後で、laws.json・laws.py・indicators.json・法則一覧.md・check_one_path.py のハッシュ値は同じです。対象のファイルの作業ツリーは 8ed860d0 と同じです。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-11-04_m2c15_laws_rows_20261103_impl_cp101_audit_request.md request_sha256=b98fc3343f3311aa4b543c73ed2c811e80b3b6c560788266c7fd7aa619c67290 -->
