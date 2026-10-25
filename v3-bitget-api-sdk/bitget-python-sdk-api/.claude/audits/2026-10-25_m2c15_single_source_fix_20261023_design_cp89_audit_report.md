# 監査結果 cp89 — CP89 — 指標の情報を1つのデータに集約する修正（設計書の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-25_m2c15_single_source_fix_20261023_design_cp89_audit_request.md`
- 依頼書のハッシュ値: 89c565f8b4f8b86e3e8cce0214cdf66973ffeb0092fd9993f1c8d081d052ca5a
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 9086fb544bb94bd0f3755977b9d3f8e63250d739af816c6c94bc378edaa06afd
- 監査が照らしたハッシュ値: 9086fb544bb94bd0f3755977b9d3f8e63250d739af816c6c94bc378edaa06afd（`shasum -a 256 .claude/state/acceptance.md` の出力。依頼書と一致しました）
- 実施日: 2026-10-25


## 2. 監査対象の型宣言

- コード型：実装の指示9件（写すプログラムの全文 669行と、壊すプログラム8本）を監査しました。
- 文書型：設計書 acceptance.md（2045行）と、設計書の元（やることの表.md 283行）と、まこさんが OK した案の写し4本を監査しました。
- 数値型：記録の数 314 と、欄の数 23 を、写しで走らせた出力と照らしました。


## 3. 監査対象の事実データの確認

### 手書きと自動の割り当ての表（やることの表.md・まこさんが OK した表）

- 監査人は、作業場で `python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --dry-run` を走らせ、出力を acceptance.md と diff で比べました。
- 違いは1行だけでした。2-1 の1行目「指標の情報を全部持つデータが在るか」の測った結果です。acceptance.md:182 は「v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators（終了コード 0）」と書いています。いま走らせると「（終了コード 0）」だけで、フォルダは出ません。
- ほかの2044行は、プログラムが作り直した物と同じでした。そのため、割り当ての表のとおりに作られています。2-1 の結果が古い件は、修正4 と修正9 の作り直しで直ります。

### 監査に出す前のチェック（pre_audit_check.json）

- 依頼書:474〜493 の表の終了コードは、自分では走らせ直していません。理由は、leak_causality_diag.py（約13分）と材料の検査（約35分）が長く、この監査の問いの答えを変えないためです。
- 監査人が自分で走らせた確かめは、10節に書きました（写すプログラムの写しの書く走行・照らす口・自己テスト・dry-run）。

### 必読に要るファイル（道具が設計書と実装から拾った）

- 依頼書:499〜505 の5本は、着手前必読の20件に全部入っていました。
- 監査人は、このほかに次の物を開きました。
  - recipes/search_limits.json（:10 quantile_range・:24 hour_range）
  - engine_tuner_gen.py（:555〜570 の _thr_fixed・:1272〜1283 の _kubun_of）
  - engine_tuner_exec.py（:1055〜1066 の時刻の閾値・:2392〜2402 の出口の置き方）
  - e37_scalp.py:213（V25_K）
  - scripts/dashboard/build_range_gate_dashboard.py:50〜52（ZONE_LOOKBACK・ZONE_TOL・ZONE_TOUCH）
  - scripts/dashboard/build_regime_gate_rg.py:59・:262（v17 の import・_adaptive_tol_1h）
  - .claude/state/indicator_review/ss_outside_probe.py:1〜40


## 4. 所見

### 一般の観点

- ①統計学的妥当性：数字の根拠が足りているかを見ます。 ＝ 「閾値の値はいまの置き場に無い」という結論の根拠が、1つのファイルの1つの鍵の数え（indicator_roles_thresholds.json の鍵「閾値の値」が0件・やることの表:233）だけでした。時刻の閾値の範囲は search_limits.json:24 に在ります（修正2・7）。314 と 23 は、写しの出力（記録 314 種・欄 23）と合いました。
- ②リスク管理：損失が出たときや、プログラムが壊れたときの備えが在るかを見ます。 ＝ 実装で indicators.json を書いた後に、直す相手の一覧を作り直すと、名前の元が変わります（gen_fix_inventory.py:81）。その道が 4-13 にありません（修正8）。
- ③認知バイアス：CC の思い込みで組まれた所が無いかを見ます。 ＝ 「別枠の材料には、パラメータが無い」という前提で、レンジ幾何の記録の「列を作る値」「コードの中の既定値」「範囲」を空にしています（実装1:512〜514）。実物の計算は、5つのパラメータを使います（observe_diag.py:2452〜2456 の _rg_zone_consts・e37_scalp.py:213 の V25_K）。修正1・3 に書きました。
- ④ソフトウェア工学：プログラムの作りが正しいかを見ます。重複・壊れやすさ・テストの抜けが、見る物です。 ＝ 次の4つを見つけました。①別枠の13種の方向の区分が None で、読む側の _kubun_of（engine_tuner_gen.py:1276）と形が違う（修正5）。②定義の表の「同上」が、そのまま記録に入る（indicator_reference_diag.py:5355〜5358・修正6）。③別枠の表どうしの名前の重なりを照らさない（実装1:82・修正6）。④画面の数え方が、中身が全部 null の辞書を「空でない」に数える（実装1:660・修正10）。名前の違う種類の数に、別枠の11種が混ざる（実装1:656・修正11）。
- ⑤再現性：同じ手順で、同じ結果が出るかを見ます。 ＝ 写しの書く走行を2回 走らせました。2回目は「もう在り、写す元から作り直した物と同じ（書かない）」で終わりのコード 0 でした。照らす口は「違い 0 件」でした。indicators.json が在るかで、gen_fix_inventory.py:81 の名前の元が変わり、一覧の結果が変わります（修正8）。
- ⑥実行プロセス：CC が、決めた流れのとおりに進めたかを見ます。 ＝ CC は、修正15 で indicators.json を消した後に、設計書を作り直していません。そのため 2-1 の結果が古いままです（acceptance.md:182・修正4・9）。まこさんの OK の逐語は在ります（ok_an_cp88_20261025.txt・ok_decline_cp88_fix6_20261025.txt）。
- ⑦主エージェントバイアス：CC が、自分に都合よく判定した所が無いかを見ます。 ＝ 別枠の13種を decide() に通さない判断（実装1:517）を、§5 にも 4-8 にも書いていません。そのため、4-5 の「方向が表に無い種類が在れば止まる」が、13種には黙って当たりません（修正3）。

### Q1 — 目的と施策は正しいか（優先度 A）

**1つ目（目的）**
- 目的は、要件定義に合っています。core_requirements_full.md:85「**指標は、指標一覧（material）からだけ呼び出す。**」と、:95〜96「誤りが見つかったら、置き場の1か所を直せば済む。」が、この工事の目的を支えています。
- 結ぶ要件の「材料（指標）の誤りを教科書と照らして直し」（acceptance.md:153）は、親の M2-C-15 全体の文です。設計書1は写すだけです。結ぶ要件はプログラムが写す項目なので、所見にだけ書きます。

**2つ目（施策ごと）**
- F-1：出どころが支えています。手段も正しいです。ただし、レンジ幾何のパラメータ5つと、時刻の閾値の範囲が、記録に入りません（修正1〜3）。
- F-2：正しいです。書く先は scripts/priority_rebuild/indicators/indicators.json です（実装1:40）。
- F-3：直す相手の一覧に頼る作りなので、一覧に無い置き場が漏れます。漏れている置き場は次のとおりです。
  - e37_scalp.py:213 の V25_K（レンジ幾何の束ね幅の倍率）
  - scripts/dashboard/build_range_gate_dashboard.py:50〜52 の ZONE_LOOKBACK・ZONE_TOL・ZONE_TOUCH（レンジ幾何の束ね定数・observe_diag.py:2452〜2456 が読む）
  - scripts/dashboard/build_regime_gate_rg.py:262 の _adaptive_tol_1h の既定値 lo=0.0015・hi=0.006
  - recipes/search_limits.json:24 の hour_range（時刻の閾値の範囲）
  - 一覧で search_limits.json を読む行は「material_param_ranges 117」だけです（fix_inventory_20261024.md:73）。上の dashboard の2本と e37_scalp.py:213 は、一覧に0件です（grep で確かめました）。
- F-4：別枠の13種の方向の区分が None で、「同上」がそのまま写ります（修正3・5・6）。
- F-5：正しいです。写しの出力で、名前の違う56種が表の名前にそろいました（修正11 の後の画面）。
- F-6：正しいです。食い違いの記録を持つ種類は126種でした。
- F-7：301種には正しいです。別枠の13種は decide() を通りません（実装1:497〜532）。その扱いは、修正3 で 4-8 に書きます。
- F-8：作り直して照らす形は、外の標準と合っています（5節）。読み漏らした値は見つけません（7-4 のとおり）。

**3つ目（表に無い直し・要らない直し）**
- 要るのに表に無い直しは、上の4つの置き場を写すことです（修正1〜3）。
- 要らない直しは、ありません。
- Plan agent は、全部の材料に共通の分位の範囲 quantile_range（search_limits.json:10）と、その真ん中の1点（engine_tuner_gen.py:562〜568）を、314種の記録の全部に写す案を出しました。監査人は、この案を採りません。理由は、1つの共通の設定を314か所に写すと、同じ値の写しが314個できるからです。それは「指標の情報を１つのデータに集約」と逆向きです。この値は種類ごとの値ではなく、探し方の設定です。代わりに、閾値の欄の null の意味を決める直しにしました（修正7）。
- 「やらないこと」の Y-01〜Y-07 の中に、この工事でやるべき物はありません。

**4つ目（目標の②③④⑥）**
- 目標の2行目：「indicators.json が無い（2-1 の1行目）」と書いてあります。ところが acceptance.md:182 の結果は、フォルダが在ると出ています。設計書が古いままです（修正4・9）。
- 目標の3行目：正しいです。
- 目標の4行目：物差しにした一覧（fix_inventory_20261024.md）が、実装の後に作り直すと変わります（修正8）。
- 目標の6行目：レンジ幾何のパラメータが記録に無いと、設計書2で読む口を作るときに、W%・帯内位置%・下半分位置（オン）のパラメータを表の外から読む所が残ります。そうなると、要件3-3（パラメータが範囲から探されている）の材料が揃いません。修正1〜3 で埋めます。

修正の番号＝1・2・3・4・8・9

### Q2 — 設計の主張は、出どころに合っているか（優先度 A）

**1つ目（数字）**
- 314：RANGE_GEO_REF 8（indicator_reference_diag.py:5349〜5367）・DEMAND_REF 3（:5226〜5251）・TIME_REF 2（:6037〜6041）・INDICATOR_TABLE 301 で、合っています。写しの出力も「記録 314 種（INDICATOR_TABLE 301 ・別枠の材料 13 ）」でした。
- 23：実装1:42〜46 の FIELDS の数と、写しの出力「欄 23」が合っています。

**2つ目（指標・閾値・パラメータ・時間足）**
- 指標：この工事で足す指標は0種です。要件3-1 に反しません。
- パラメータ：301種は写すだけで、要件3-3・4 に反しません。レンジ幾何の8種のパラメータが写りません（修正1・3）。
- 時間足：変えません。要件3-4 に反しません。
- 閾値：やることの表:233〜234 は「無し（いまの置き場に、この形の値が無い…）」と書いています。これは、時刻については誤りです。時刻の閾値の範囲は search_limits.json:24 `"hour_range": { "lo": 6, "hi": 18, "kind": "int" }` で、engine_tuner_exec.py:1062 が「時刻の閾値」として照らしています（修正1・2）。ほかの種類の閾値は、種類ごとの値が無いので、null の意味を決めます（修正7）。
- 4-7 の★について：別枠の13種は、資料の表3つに行がありません（Plan agent が grep で W%・CVD・taker_ls・時刻・res_hi を数えて0件）。役割・代表の値・パラメータの範囲は、資料には在りません。この工事は資料を直さないので、範囲の外です。

**3つ目（要件1〜10）**
- 1・2・3-1・3-4〜3-6・7・8・10：反していません。
- 3-2・3-3・4・5：時刻の閾値の範囲と、レンジ幾何のパラメータが写らない点で、材料が揃いません（修正1〜3）。
- 6：価格水準の5種（res_hi・res_lo・sup_hi・sup_lo・mid）は「オフ」と写ります。ところが出口の置き方は、印を見ずにこの5種を使います（engine_tuner_exec.py:2394〜2401）。「オフの指標は、どのロジックからも使えない」（core_requirements_full.md:86）で読む側を向け直すと、出口の置き方が止まります。設計書2の受け持ちなので、4-13 に書きます（修正8）。
- 9：工事の流れに反していません。
- 対応の表の誤り：要件7 が「4-10・4-23」に当たっています（acceptance.md:102）。中身を受けているのは §1 と F-7 です。プログラムが作る表なので、所見にだけ書きます。

#### Q8 — 別枠の材料13種の記録は、範囲と形が足りているか（優先度 A）

**1つ目（範囲）**
- 13種という範囲は正しいです。
- STATE_COLS（indicator_reference_diag.py:6052）は、記録に入れなくてよいです。根拠は2つです。:6044「ポジション状態列（出口 fire の材料・入口の条件には使えない＝建玉が無いと定義できない）」と、一覧の振り分け「外す（B・指標の情報ではない）」（fix_inventory_20261024.md:452）です。

**形の欠陥（4つ）**
- (a) レンジ幾何の8種に、パラメータが入りません。写しの記録は「列を作る値」「コードの中の既定値」「範囲」が全部空でした。実物の計算は、次の5つを使います。
  - V25_K＝0.5（e37_scalp.py:213）
  - ZONE_TOL＝0.003・ZONE_TOUCH＝2・ZONE_LOOKBACK＝168（build_range_gate_dashboard.py:50〜52。observe_diag.py:2456 が rgmod.v17 から読む）
  - _adaptive_tol_1h の lo＝0.0015・hi＝0.006（build_regime_gate_rg.py:262）
  - しかも、この5つの置き場は、直す相手の一覧に無く、数える道具 ss_outside_probe.py の数える相手（scripts/priority_rebuild・scripts/regime ほか・ss_outside_probe.py:5〜8）にも入りません。scripts/dashboard を数えず、1つの数の代入も数えないからです。そのため設計書3の後に「表の外が0件」と出ても、この5つは表の外に残ります。工事のゴールに届きません（修正1・3・8）。
- (b) 方向の区分が None です（実装1:517）。いまの読む側は、区分を読み方の「＝」の前から引いています（engine_tuner_gen.py:1276「return iref.RANGE_GEO_REF[m["geo"]]["houkou"].split("＝")[0]」）。設計書2で読む側を記録に向けると、文字を切る処理がコードに残ります（修正5）。
- (c) 定義の表の「同上」が、そのまま記録に入ります（res_lo・sup_hi・sup_lo の流儀と方向の読み方、mid の方向の読み方・indicator_reference_diag.py:5355〜5358）。記録は1種ずつ読むので、何と同じかが分かりません（修正6）。
- (d) 4-5 の「方向が表に無い種類が在れば止まる」が、13種には黙って当たりません。この扱いは 4-8 に書いてありません（修正3）。
- 監査人は、修正1・5・6 のコードを作業場の写しに当てて走らせました。結果は次のとおりです。
  - 照らす口は「違い 0 件」で通りました。
  - W% の記録の「ほかの置き場の値」に、5つのパラメータが入りました。
  - res_lo の方向の区分は「価格水準」になり、流儀は res_hi の文になりました。
  - 時刻の閾値の範囲は [{"lo":6,"hi":18,"kind":"int","出どころ":…}] になりました。

**2つ目（時刻・曜日の計算の関数の欄が空）**
- 設計書2で、指標一覧の側へ移せます。計算は engine_tuner_exec.py:2084〜2086 の2行で、引数も依存もありません。
- ただし、この2行は直す相手の一覧に載っていません（fix_inventory を grep して _col_array は0件）。場所は 4-8 の文（やることの表:235）にだけ在ります。設計書2の元で、この行を「③向け直す」に入れる必要があります。設計書2の受け持ちなので、修正の指示は出しません。

#### Q9 — 閾値の2つの欄（null）は、要件定義の4番・5番と T-2・T-3 に合う形か（優先度 A）

**1つ目（T-2・T-3 が値を入れられるか）**
- 形の上では入れられます。null には型が無いからです。
- ただし、入れる道が決まっていません。写すプログラムは、この欄を None と決めて書きます（実装1:487〜488・:526〜527）。T-2・T-3 が indicators.json を手で埋めると、照らす口が「欄「閾値の代表の固定値（スキャル／デイトレ）」が写す元と違う」で落ちます（実装1:607〜609）。書く口も上書きしません（:648〜652）。値の置き場をどこにするかを、T-2・T-3 の設計書で決める必要があります（修正8）。
- また、「値の組2つ」には、どの閾値か（RSI なら上の 70 か下の 30 か）の名前がありません。CONST_REGISTRY の閾値は、上と下の2つの名前で持っています（例＝RSI_OB・RSI_OS・やることの表:231）。T-3 で形を決めるときに、この点を決める必要があります（修正7）。
- 時刻だけは、いまの置き場に閾値の範囲が在ります（search_limits.json:24）。修正1・2 で写します。

**2つ目（null が別の意味に取られないか）**
- 取り違えられます。パラメータの「範囲」の null は「範囲を持たない」の意味です（4-7「範囲を持たない種類は、無いまま写します」）。閾値の欄の null は「まだ決めていない」の意味です。同じ null で、2つの意味が区別できません。
- 写すプログラムの画面は、dict(スキャル=None, デイトレ=None) を「空でない」に数え、314 と出します（写しの出力「閾値の代表の固定値（スキャル／デイトレ） 314」）。修正10 を当てた写しでは 0 と出ました。

修正の番号＝1・2・3・5・6・7・8・10

### Q3 — コードは施策のとおりか（優先度 A）

**1つ目（実装の指示ごと）**
- 実装1（gen_indicators_draft.py）は F-1〜F-8 のための直しです。誤りは次のとおりです。
  - レンジ幾何のパラメータと、時刻の閾値の範囲を写していません（実装1:495〜532・修正1）。
  - 別枠の方向の区分が None です（:517・修正5）。
  - 「同上」がそのまま写り、別枠の表どうしの名前の重なりを見ません（:82・修正6）。
  - 画面の数え方（:656・:660・修正10・11）。
- 実装2〜9（壊すプログラム8本）は、F-1〜F-8 のそれぞれに1本です。期待する文（EXPECT_MSG）は、写すプログラムが出す文に含まれています。別枠の13種と、閾値の2つの欄を壊す試しはありません。監査人は、この8本を走らせていません。8本とも本物のファイル（indicators.json・observe_diag.py・gen_indicator_table.py ほか）を一時的に書き替える作りだからです（lib.sh の guard と trap で戻す作り）。

**2つ目（4-13 に無い壊れる物）**
- 直す相手の一覧を作るプログラムは、indicators.json が在ると、その記録の名前を名前の元にします（gen_fix_inventory.py:81「_BASE = set(json.loads(_IJ.read_text(encoding="utf-8")).get("記録", {})) if _IJ.exists() else set(iref.INDICATOR_TABLE)」）。実装の後に一覧を作り直すと、名前が314種になり、一覧の行が変わります。写すプログラムは一覧の「①写す」の行を写す元にするので、照らす口が落ちます。この件は 4-13 にありません（修正8）。何行変わるかは、データ不足です。理由は、gen_fix_inventory.py が本物の一覧（fix_inventory_20261024.md:319〜320 で HERE に書く）を書き替える作りで、写しでは走らせられなかったからです。
- 数える道具 ss_outside_probe.py も、indicators.json が在ればその記録の名前を使います（ss_outside_probe.py:25〜28）。

**3つ目（H2・H6）**
- 反していません。写すプログラムは列の値を計算しません。価格水準の5種の記録は、値段の水準の値を持ちません（値域の種別 price を写すだけ）。

#### Q10 — CP88 の修正が、監査の書いたとおりに設計書と実装の指示に入っているか（優先度 B）

**1つ目（当てた12件と、手で対応した2件）**
- Plan agent が12件を1件ずつ実物と照らし、全部「監査のとおり」でした。監査人は、そのうち2件（修正4 の案A＝やることの表:171・修正9 の案A＝やることの表:280）を、自分で開いて確かめました。
- 修正15：indicators.json は消えています（ls で無い）。ただし、消した後に設計書を作り直していないので、2-1 の結果が古いままです（修正4・9）。
- 修正17：新しい案 okd_an_cp88_20261025.txt:38 のハッシュ値 9fd91f2d… は、いまの impl_4-20_20261024.json の sha256 と同じでした（shasum で確かめました）。この監査の修正1・5・6・10・11 を当てると、実装の指示のハッシュ値が変わります。そのため、案のハッシュ値を直す件を Process に書きました（修正13）。

**2つ目（修正6 を当てない理由）**
- 理由は正しいです。写しの CVD の記録の「ほかの置き場の値」に、observe_diag.py:250 の _DEMAND_FILES のうち CVD の行 {"CVD":["../../data/BTCUSDT-1m-binance-taker-2024-03-01_2026-06-30.csv","timestamp",null]} が入りました（jq で確かめました）。

修正の番号＝1・4・5・6・8・9・10・11・13

### Q4 — 完成の条件で、施策が効いたと言えるか（優先度 A）

**1つ目（施策ごとに効いたと言えるか）**
- F-1：完成の条件の1番は「記録が314種」を、写すプログラムの中の照らし（実装1:539）で見ます。この照らしは、同じ表から作った数どうしの比べです。別枠の表どうしで名前が重なると、数も同じだけ減るので通ります（修正6 で塞ぎます）。
- F-2・F-4・F-5・F-6・F-8・Y-03：施策を測っています。
- F-3：読まない値は測れません（7-4 のとおり）。レンジ幾何のパラメータと時刻の閾値の範囲が写らない件も、この形では見つかりません（修正1〜3）。
- F-7：別枠の13種は decide() を通らないので、7番・8番の外です（修正3）。
- 閾値の2つの欄を測る行はありません。
- 10番の `git diff --quiet -- scripts/priority_rebuild` は、リポジトリの根から打つと、指す先が無いので必ず 0 で終わります（監査人が根で走らせて rc=0・`ls scripts/priority_rebuild` は無い）。承認の前の検査 A12 と承認のプログラムは、SDK を作業場所にして走らせるので（require_design_check_before_approval.py:935・approve_impl.sh:506）、機械の上では正しく照らします。修正の指示は出しません。

**2つ目（6-5 の1件ずつ）**
- 6節に書きました。

修正の番号＝1・2・3・6

### Q5 — 設計書の書き方は正しいか（優先度 A）

**1つ目（結論だけの文）**
- 4-8 のやることの表:233「いまの置き場に、この形の値が無い」は、根拠が1つの鍵の数えだけで、時刻については誤りです（修正2・7）。
- 6-2 の1番目「照らす口が、4-4 の1〜9の写す元の全部と比べる」（okd_an_20261024.txt:97）は、7-4 と 7-6 の3番「写すプログラムが読まない値は、照らす口では見つからない」と食い違います（修正12）。

**2つ目（決めた作り方のとおりか）**
- dry-run の出力と acceptance.md の違いは、2-1 の1行だけでした（3節）。決めた作り方のとおりに作られています。

**3つ目（まこさんの OK）**
- 逐語のファイルが在ります。ok_an_cp88_20261025.txt・ok_decline_cp88_fix6_20261025.txt・ok_plan5_20261024.txt・ok_todo92_20261024.txt ほか（工事のフォルダの ls で確かめました）。

**4つ目（捨てた案）**
- §5 は、別枠の13種を decide() に通さない判断と、パラメータを空にする判断を書いていません。良い案を理由なく捨てたのではなく、判断そのものが書かれていません（修正3）。

修正の番号＝2・3・7・12


## 5. 外部検索

### 検索 1 — 指標の分類の外の標準

- 検索の言葉：technical indicator categories trend oscillator volatility volume momentum classification
- 出どころ：https://sentimentrader.com/education/technical-indicators
- 逐語：「This section groups commonly used indicators into four main categories — Trend, Momentum, Volatility, and Volume」
- 照らした結果：外の4つの群（トレンド・モメンタム・ボラティリティ・出来高）は、役割の区分の表7行（向き→トレンド・勢い→勢い・値動きの幅→ボラ・出来高→出来高ほか）の中に全部在ります（写しの indicators.json の「役割の区分の表」）。欠けている区分はありません。検索の要約は、MACD がトレンドとモメンタムの両方に数えられることも示しています。これは、1つの種類に性質を一覧で持たせる作り（F-7）を支えます。

### 検索 2 — 1つのデータに集める作りの外の標準

- 検索の言葉：single source of truth configuration generated file drift check verify
- 出どころ：https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentops02-bp02.html
- 逐語：「First, determine your source of truth for configuration. If approved baselines live in a wiki, a shell history, or in the AWS console, then drift detection has nothing to compare against.」
- 2つ目の出どころ：https://cdn.jsdelivr.net/npm/@tansuasici/claude-code-kit@1.21.0/tasks/lessons/2026-07-08-generated-config-single-source.md（1つの事業の教訓の文書で、標準ではありません）。検索の要約は「generate it from the base plus an explicit delta, commit the output, and add a CI check that regenerates and diffs it」です。
- 照らした結果：作り直して1件ずつ照らす口（F-8）は、外の作り方と合っています。ただし、この工事では、作る側の入力（直す相手の一覧）が、作った物（indicators.json）で変わります（gen_fix_inventory.py:81）。比べる相手が自分の作った物に左右される点は、AWS の「まず正本を決める」と合いません（修正8）。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

進めてよいです。値が教科書に照らして正しいかは、この工事の範囲の外で、ToDo の70番で見ます。

### 自己申告 2

このまま進めてはいけません。写す元にも一覧にも無い置き場の実例が在ります（e37_scalp.py:213 の V25_K・build_range_gate_dashboard.py:50〜52・build_regime_gate_rg.py:262・search_limits.json:24 の hour_range）。しかも、数える道具 ss_outside_probe.py は scripts/dashboard と1つの数の代入を数えないので、設計書3の後にも見つけません。先に修正1〜3 と修正8 を入れます。

### 自己申告 3

進めてよいです。種類の名前を持たない値を区分の言葉の表に入れ、種類の記録へ結ぶのは、設計書2の受け持ちです。写しでは区分の言葉の表が46件でした。

### 自己申告 4

進めてよいです。監査人が写しで書いた indicators.json を開き、W%・res_lo・mid・時刻・曜日・CVD の記録を見ました（jq）。見つけた欠陥は、修正1・5・6 に書きました。修正を当てた後に、実装で書いた物を同じ jq で開いて見てください。

### 自己申告 5

進めてよいです。この工事は e38_logic_parts.py を直さず、設計書2の元で照らします。

### 自己申告 6

進めてよいです。設計書を作るプログラムが読む鍵の件は、この工事の記録とは別の所です。ただし、「閾値の値がいまの置き場に無い」の結論は、時刻については誤りです（修正2）。

### 自己申告 7

進めてよいです。設計書1は値を写すだけで、選び直しは ToDo の70番で行います。

### 自己申告 8

進めてよいです。写すプログラムは、食い違いの記録を種類の全部（オンとオフ）について作ります（実装1:414〜459 は TABLE の全部を回す）。写しでは126種が食い違いの記録を持ちました。

### 自己申告 9

進めてよいです。写す相手は、設計書3の前に決めます。

### 自己申告 10

進めてよいです。監査人が写しで測りました。書く走行は17.6秒、照らす口は17.2秒でした（修正10・11 を当てる前）。修正1・5・6・10・11 を当てた写しの書く走行は17.7秒でした。

### 自己申告 11

進めてよいです。この工事は元のコードを直さず、性質テストの判定を変えません。材料の検査は約35分かかるので、監査人は走らせていません（データ不足）。M-1 の前に、observe_diag.py --check-materials の性質テストの行で見てください。

### 自己申告 12

進めてよいです。計算は engine_tuner_exec.py:2084〜2086 の2行で、設計書2で移せます。ただし、この2行は直す相手の一覧に無いので、設計書2の元で「③向け直す」の行に足す必要があります（Q8 の2つ目）。


## 7. 総合判定

### 結論と件数

- 結論＝CONDITIONAL-GO（根拠＝作りの向き〔いまの置き場から1回だけ写し、作り直して照らす〕は、要件定義の6番・7番と外の標準に合っています。ただし、レンジ幾何の8種のパラメータ5つと、時刻の閾値の範囲が、写す元にも直す相手の一覧にも数える道具の相手にも無く、記録に入りません。照らす口もこれを見つけません。このまま設計書2・3へ進むと、表の外に指標の情報が残ったまま「0件」と出ます。修正1〜4 を入れれば先に進めます）
- Critical＝4
- Major＝5
- Minor＝3
- Process＝1


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
raise SystemExit(f\"❌ {f} の記録の欄が、4-8 の23の欄と違う\")\n    if unknown_dir:
~~~
直した後の文字:
~~~
raise SystemExit(f\"❌ {f} の記録の欄が、4-8 の23の欄と違う\")\n    # CP89 の修正1＝別枠の材料と時刻の、直す相手の一覧に無いパラメータと閾値の置き場を写す（読むだけ・ast で開く）\n    dash = SDK / \"scripts/dashboard\"\n    geo_params = []\n    for p, nm in ((PR / \"e37_scalp.py\", \"V25_K\"), (dash / \"build_range_gate_dashboard.py\", \"ZONE_TOL\"),\n                  (dash / \"build_range_gate_dashboard.py\", \"ZONE_TOUCH\"), (dash / \"build_range_gate_dashboard.py\", \"ZONE_LOOKBACK\")):\n        v, ln = module_assign(p, nm)\n        geo_params.append(dict(置き場=f\"{p.relative_to(SDK / 'scripts').as_posix()}:{ln}\", 名前=nm, 値=v))\n    for n in ast.parse((dash / \"build_regime_gate_rg.py\").read_text(encoding=\"utf-8\")).body:\n        if isinstance(n, ast.FunctionDef) and n.name == \"_adaptive_tol_1h\":\n            a = n.args\n            geo_params.append(dict(置き場=f\"dashboard/build_regime_gate_rg.py:{n.lineno}\", 名前=\"_adaptive_tol_1h の引数の既定値\",\n                                   値={x.arg: ast.literal_eval(d) for x, d in zip(a.args[len(a.args) - len(a.defaults):], a.defaults)}))\n    if len(geo_params) != 5:\n        raise SystemExit(\"❌ レンジ幾何のパラメータの置き場が読めない（build_regime_gate_rg.py に _adaptive_tol_1h が無い）\")\n    for f, (grp, _d) in EXTRA_OF.items():\n        if grp == \"レンジ幾何\":\n            recs[f][\"ほかの置き場の値\"] += copy.deepcopy(geo_params)\n    recs[\"時刻\"][\"閾値の範囲\"] = [dict(jload(PR / \"recipes/search_limits.json\")[\"hour_range\"],\n                                   出どころ=\"recipes/search_limits.json の hour_range（engine_tuner_exec.py:1057〜1066）\")]\n    if unknown_dir:
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:2455「    return float(rgmod.v17.ZONE_TOL), int(rgmod.v17.ZONE_TOUCH), int(rgmod.v17.ZONE_LOOKBACK)」
状態: 確定

#### 修正 2
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 234
直す前の文字:
~~~
| 無し（同上）。T-2・T-3 で埋める | null |
~~~
直した後の文字:
~~~
| 時刻だけは、いまの置き場の値を写す＝recipes/search_limits.json:24 の hour_range（engine_tuner_exec.py:1057〜1066 が時刻の閾値として照らす）。ほかの種類は null（「まだ決めていない」の意味＝T-2・T-3 で埋める） | 時刻＝[{kind int・lo 6・hi 18・出どころ hour_range}]・ほかは null |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json:24「  "hour_range": { "lo": 6, "hi": 18, "kind": "int" },」
状態: 確定

#### 修正 3
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 235
直す前の文字:
~~~
時間帯の2種は、計算が engine_tuner_exec.py の _col_array（:2086）の中に在るので空（関数として切り出すのは設計書2）。値の無い欄は null か空
~~~
足す文字:
~~~
。レンジ幾何の8種の「ほかの置き場の値」には、直す相手の一覧に無いパラメータの置き場5つを写す＝V25_K（e37_scalp.py:213）・ZONE_TOL・ZONE_TOUCH・ZONE_LOOKBACK（scripts/dashboard/build_range_gate_dashboard.py:50〜52・observe_diag.py:2452〜2456 の _rg_zone_consts が読む）・_adaptive_tol_1h の引数の既定値 lo・hi（scripts/dashboard/build_regime_gate_rg.py:262）。どれも ast で開いて読む（import しない）。定義の表の「同上」は、表の並びで1つ前の行の値に置き換えて写す（res_lo・sup_hi・sup_lo の流儀と方向の読み方、mid の方向の読み方）。方向の区分は、方向の読み方の「＝」の前を写す（engine_tuner_gen.py:1272〜1282 の _kubun_of と同じ取り方）。性質は空のまま写す。別枠の材料は性質を表から決めないので、4-5 の方向の止まる条件を当てない（decide を通さない）。別枠の表どうしで名前が重なれば止まる
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_scalp.py:213「V25_K = 0.5                       # 束ね幅 tol=clamp(K×ATR%_1h,0.15%,0.6%) の倍率（幾何指標 diag＋まこさん視認校正で選定＝採点窓 net 不参照・L-267 非該当・build_regime_gate_rg._adaptive_tol_1h に渡す）」
状態: 確定

#### 修正 4
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:14「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --write`。」（同じ工事の --dry-run は、監査人の作業場で既定の2分の上限の中で終わった。秒数は、道具の行に time を付けると hook が止めるので測っていない。修正1 で実装の指示のハッシュ値が変わるので、修正13 で案のハッシュ値を直し、まこさんの OK をいただいてから走らせる）
状態: 未決

### Major

#### 修正 5
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
dict(区分=None, 読み方=d.get(\"houkou\"))
~~~
直した後の文字:
~~~
dict(区分=(d.get(\"houkou\") or \"\").split(\"＝\")[0] or None, 読み方=d.get(\"houkou\"))
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:1276「        return iref.RANGE_GEO_REF[m["geo"]]["houkou"].split("＝")[0]」
状態: 確定

#### 修正 6
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
EXTRA_OF = {nm: (grp, d) for grp, tb in EXTRA.items() for nm, d in tb.items()}
~~~
直した後の文字:
~~~
def _carry(tb: dict) -> dict:\n    \"\"\"定義の表の「同上」を、表の並びで1つ前の行の値に置き換える（記録は1種ずつ読むので「同上」では読めない・CP89）。\"\"\"\n    out, prev = {}, {}\n    for nm, d in tb.items():\n        e = {k: (prev.get(k, v) if v == \"同上\" else v) for k, v in d.items()}\n        out[nm], prev = e, e\n    return out\n\n\n_dup = sorted(nm for nm in {n for tb in EXTRA.values() for n in tb} if sum(nm in tb for tb in EXTRA.values()) > 1)\nif _dup:\n    raise SystemExit(f\"❌ 別枠の材料の名前が、別枠の表どうしで重なる: {_dup}\")\nEXTRA_OF = {nm: (grp, d) for grp, tb in EXTRA.items() for nm, d in _carry(tb).items()}
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py:5355「    "res_lo": dict(kind="price", teigi="レジスタンス帯の下端", ryugi="同上", houkou="同上"),」
状態: 確定

#### 修正 7
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 233
直す前の文字:
~~~
無し（いまの置き場に、この形の値が無い＝indicator_roles_thresholds.json に鍵「閾値の値」が0件・CP88 の修正11）。T-2・T-3 で埋める | スキャル null・デイトレ null |
~~~
直した後の文字:
~~~
無し（種類ごとの値は、いまの置き場に無い＝indicator_roles_thresholds.json に鍵「閾値の値」が0件・CP88 の修正11）。T-2・T-3 で埋める。この欄と「閾値の範囲」の欄の null は「まだ決めていない」の意味で、「閾値を使わない」の意味ではない（パラメータの「範囲」の欄の null は「範囲を持たない」の意味で、別の意味）。全部の材料に共通の分位の範囲 quantile_range（recipes/search_limits.json:10）と、その真ん中の1点（engine_tuner_gen.py:562〜568 の _thr_fixed）は、種類ごとの値ではなく探し方の設定なので、記録に写さない（314か所に写すと同じ値の写しが増える）。上と下の2つの閾値を持つ種類（例＝RSI_OB・RSI_OS）で、値の組をどう名前で分けるかは T-3 で決める | スキャル null・デイトレ null |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:562「    ★どの1点か＝承認済みの範囲（`recipes/search_limits.json` の `quantile_range`）の真ん中。」
状態: 確定

#### 修正 8
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 251
直す前の文字:
~~~
| 読む側を向け直すのは設計書2・区分の一覧を持つ所を消すのは設計書3 |
~~~
足す文字:
~~~

| 直す相手の一覧を作る gen_fix_inventory.py（:81 で、indicators.json が在ればその記録の名前を名前の元にする）と、数える道具 ss_outside_probe.py（:25〜28 で同じ） | 実装で indicators.json を書いた後に一覧を作り直すと、名前が301種から314種（別枠の材料13種）に増え、一覧の行が変わる。写すプログラムは一覧の「①写す」の行を写す元にするので、一覧が変わると照らす口（--verify）が落ちる。設計書2で一覧を作り直す前に、照らす口の相手を決める | 設計書2 |
| 数える道具 ss_outside_probe.py の数える相手 | 数える相手は scripts/priority_rebuild・scripts/regime・.claude/tools・.claude/hooks・.claude/state/indicator_review の直下で（ss_outside_probe.py:5〜8）、scripts/dashboard を数えない。また、辞書・組・一覧・集合の代入だけを数え、1つの数の代入（ZONE_TOL＝0.003 など）を数えない。そのため、レンジ幾何のパラメータの元の置き場（build_range_gate_dashboard.py:50〜52・build_regime_gate_rg.py:262・e37_scalp.py:213）は、設計書3の後も数に出ない。設計書3で、この5つの置き場を消すか、数える相手に足すかを決める | 設計書3 |
| 閾値の代表の固定値と閾値の範囲の2つの欄（T-2・T-3 で埋める） | 照らす口は、この2つの欄を写すプログラムが作り直した値と比べる。T-2・T-3 で indicators.json を手で埋めると、照らす口が「写す元と違う」で落ち、書く口は上書きしない（4-10）。T-2・T-3 の値の置き場（写す元）を作って写すプログラムに読ませるか、indicators.json を正本にした後に埋めるかを、T-2・T-3 の設計書で決める | T-2・T-3 |
| 価格水準の5種（res_hi・res_lo・sup_hi・sup_lo・mid）の記録の「オン/オフ」 | indicator_switch.json の geo_on に無いので「オフ」と写る。この5種は、出口の置き方の幾何参照に、印を見ずに使われている（engine_tuner_exec.py:2394〜2401）。読む側を記録に向けるとき、「オフの指標は、どのロジックからも使えない」（core_requirements_full.md:86）で読むと、出口の置き方が止まる | 設計書2 |
~~~
根拠の抜き書き: .claude/state/indicator_review/gen_fix_inventory.py:81「_BASE = set(json.loads(_IJ.read_text(encoding="utf-8")).get("記録", {})) if _IJ.exists() else set(iref.INDICATOR_TABLE)」
状態: 確定

#### 修正 9
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:14「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --write`。」（--dry-run は既定の2分の上限の中で終わった。秒数は hook の決まりで測っていない。修正4 を走らせた後なら、修正7・8 を当ててから1回だけ走らせればよい）
状態: 未決

### Minor

#### 修正 10
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
if r[fld] not in (None, '', [], {}))}
~~~
直した後の文字:
~~~
if r[fld] not in (None, '', [], {}) and not (isinstance(r[fld], dict) and all(v in (None, '', [], {}) for v in r[fld].values())))}
~~~
根拠の抜き書き: .claude/state/acceptance.md:449「- 写した後の画面＝記録の数（314＝INDICATOR_TABLE の301種と別枠の材料13種）・欄ごとの空でない記録の数・食い違いの記録を持つ記録の数・書いたパス。」
状態: 確定

#### 修正 11
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
for c in r[\"計算の関数\"] if c[\"登録の名前\"] != f})
~~~
直した後の文字:
~~~
for c in r[\"計算の関数\"] if c[\"登録の名前\"] not in (f, None)})
~~~
根拠の抜き書き: .claude/state/acceptance.md:1508「#   守っているもの＝7-6 の F-5（名前の違う56種が表の名前にそろい、つながらない登録が0件）」
状態: 確定

#### 修正 12
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/okd_an_20261024.txt
直す箇所: 97
直す前の文字:
~~~
| 写し漏れ（記録に入らない置き場の値が残る） | 照らす口が、4-4 の1〜9の写す元の全部と比べる。直す相手の一覧の「①写す」の行（自己テストの見本を除く）とも照らす |
~~~
直した後の文字:
~~~
| 写し漏れ（記録に入らない置き場の値が残る） | 照らす口は、写すプログラムが作り直した物と比べるので、写すプログラムが読まない値は見つけない（7-4）。直す相手の一覧の「①写す」の行（自己テストの見本を除く）が、記録か3つの表に入ったかを照らす |
~~~
根拠の抜き書き: .claude/state/verbatim/m2c15-single-source-fix-20261023/okd_an_20261024.txt:97「| 写し漏れ（記録に入らない置き場の値が残る） | 照らす口が、4-4 の1〜9の写す元の全部と比べる。直す相手の一覧の「①写す」の行（自己テストの見本を除く）とも照らす |」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 13
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/okd_an_cp88_20261025.txt
直す箇所: 38
直す前の文字:
~~~
impl_4-20_20261024.json sha256=9fd91f2de685569e2ac044304f9da1400575389f7e2e55c755a05d82de8213cd
~~~
直した後の文字:
~~~
impl_4-20_20261024.json sha256=<修正1・5・6・10・11 を当てた後の impl_4-20_20261024.json の sha256>
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:341「        bad.append(f"【4-20】＝実装の指示のファイルのハッシュ値が、OK された案と違う（案 {m.group(2)[:12]}… ／ 今 {got[:12]}…）＝ファイルが変わっている")」
状態: 未決


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**開いたファイルと行（監査人）**
- 依頼書（全文 635行）
- acceptance.md:12〜14・:182・:1860〜1890（7-6）
- impl_4-20_20261024.json の実装1（全文 669行・作業場に写して読んだ）と実装2〜9 の EXPECT・MEANS・壊し方の行
- やることの表.md:12〜15・:171・:228〜256・:280・:283
- okd_an_20261024.txt:97・okd_an_cp88_20261025.txt:38
- indicator_reference_diag.py:5222〜5255・:5345〜5370・:5470〜5485・:6030〜6075
- observe_diag.py:250〜259・:2420〜2485
- engine_tuner_gen.py:555〜570・:1272〜1283
- engine_tuner_exec.py:1055〜1066・:2392〜2402
- e37_scalp.py:213・:506〜530
- scripts/dashboard/build_regime_gate_rg.py:46〜60（import）・build_range_gate_dashboard.py:50〜52
- recipes/search_limits.json:10〜11・:24〜25
- fix_inventory_20261024.md（grep：hour_range・quantile_range・ZONE_・V25_K・STATE_COLS・_DEMAND_FILES・search_limits）
- gen_fix_inventory.py:78〜83・:319〜320
- ss_outside_probe.py:1〜40
- approve_impl.sh:490〜520・require_design_check_before_approval.py の cwd の行（:110・:935・:951）
- Plan agent（subagent_type=Plan）の所見（Q1〜Q5・Q8〜Q10・観点・自己申告・修正13件の案）。監査人は、中心の主張の根拠の行を全部 実物で開き直しました。Plan agent の修正1〜5（quantile_range を314種に写す案）は、5節と Q1 の3つ目の理由で採りませんでした。

**走らせたコマンドと結果と秒数（全部 リポジトリの根・写しは作業場 cp89_work）**
- `shasum -a 256 .claude/state/acceptance.md` → 9086fb54…（依頼書と一致）
- `jq -r '.[0]["中身"]' impl_4-20_20261024.json` ほか → 実装の指示9件を作業場に写した（669行・壊すプログラム8本）
- 写すプログラムの写し（HERE と OUT の2行だけを作業場に替えた gen_indicators_draft.work.py）の書く走行 → 「記録 314 種・欄 23・「①写す」の行 730」・17.6秒
- 同じ写しの `--verify` → 「違い 0 件」・17.2秒
- 同じ写しの `--selftest` → 2件とも ✅・rc 0
- 同じ写しの2回目の書く走行 → 「もう在り…同じ（書かない）」・rc 0
- jq で写しの indicators.json の別枠13種・W%・res_lo・mid・時刻・曜日・CVD の記録と2つの表を開いた
- 修正1・5・6・10・11 を写しに当てた書く走行 → 「記録 314 種」・名前の違う種類 56種・閾値の範囲 1・17.7秒。`--verify` → 「違い 0 件」
- `python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --dry-run | diff .claude/state/acceptance.md -` → 違いは :182 の1行と、終わりの空行1つ（秒数は測っていない）
- `git diff --quiet -- scripts/priority_rebuild`（根）→ rc 0（指す先が無い）・`git -C v3-bitget-api-sdk/bitget-python-sdk-api diff --quiet -- scripts/priority_rebuild` → rc 0
- grep -cF で、修正の直す前の文字がそれぞれ1か所だけに当たることを確かめた（全部 1）
- WebSearch 2件・WebFetch 2件（5節）

**走らせられなかったものと理由**
- 壊すプログラム8本：本物のファイル（indicators.json・observe_diag.py・gen_indicator_table.py ほか）を一時的に書き替える作りのため。
- gen_fix_inventory.py の写しでの走行：本物の一覧 fix_inventory_20261024.md に書く作り（:319〜320）で、書く先を替える口が無いため。修正8 の1行目の行数は「データ不足」としました。
- 材料の検査（observe_diag.py --check-materials・約35分）と leak_causality_diag.py（約13分）：長く、この監査の問いの答えを変えないため。
- dry-run の秒数：道具の行に time や date を付けると、土台ゲートの hook が止めるため（.claude/state/sessions/92085a58-3960-42fc-9eda-861015509b67/lessons.md に決まりを書いた）。


## 11. 本物のファイルを書き替えていないこと

- 監査を始める前の `git status --short`（242行）を作業場に控え、終わりの `git status --short` と diff で比べました。diff の終わりのコードは 0 で、違いは0行でした（作業場 cp89_work/ は、監査の前から追跡していないフォルダとして在ったため、1行のままです）。
- 終わりの `git status --short` のうち、追跡しているファイルの行（?? 以外）は次の6行で、監査の前と同じです。
~~~
 M .claude/hooks/require_design_check_before_approval.py
 M .claude/state/indicator_review/fix_inventory_20261024.md
 M .claude/state/next_step.md
 M .claude/state/next_step_src.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/applied_fixes.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
~~~
- 監査人が書いたのは、作業場 v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp89_work/ の中のファイルと、このセッションの決まりの記録 .claude/state/sessions/92085a58-3960-42fc-9eda-861015509b67/lessons.md（hook が書くよう求めた物）だけです。
- scripts/priority_rebuild/indicators/ は、監査の前も後も在りません（ls で確かめました）。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-25_m2c15_single_source_fix_20261023_design_cp89_audit_request.md request_sha256=89c565f8b4f8b86e3e8cce0214cdf66973ffeb0092fd9993f1c8d081d052ca5a -->
