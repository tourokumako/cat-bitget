# 監査結果 cp88 — CP88 — 指標の情報を1つのデータに集約する修正（設計書の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-24_m2c15_single_source_fix_20261023_design_cp88_audit_request.md`
- 依頼書のハッシュ値: 83cfad11235a5f17f33105063daae1d1da79b982cf30a63fe50d65ab24edec94
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 94d0909881631f0a8b3ec69513355800e67842a4a2fc8db1e8f55128d48b65a8
- 監査が照らしたハッシュ値: 94d0909881631f0a8b3ec69513355800e67842a4a2fc8db1e8f55128d48b65a8（`shasum -a 256 .claude/state/acceptance.md`・依頼書の値と一致。監査の終わりにも同じ値）
- 実施日: 2026-10-24


## 2. 監査対象の型宣言

- コード型：実装の指示1（写すプログラム gen_indicators_draft.py の全文・620行）と、実装の指示2〜9（壊すプログラム8本）。
- 文書型：設計書（acceptance.md・1980行）と、その元（やることの表.md・まこさんが OK した案の写し3本）。
- 数値型：記録の数 301・「①写す」の行 723・名前の違う種類 56・食い違いの種類の数（46／48／52）。監査人は、写すプログラムの写しを作業場で走らせ、これらの数を数え直した。


## 3. 監査対象の事実データの確認

### 手書きと自動の割り当ての表（やることの表.md・まこさんが OK した表）

- 依頼書の割り当ての表の「手書き」の行は9行です（§1 概要・2 要件との違い・2 順番・2-1 何を測るか・3 目標の②〜⑥・3-2・4-4/4-5/4-8/4-13・7-6・4-19）。依頼書:327 は「CC が手で書く項目は 7 件」と書き、設計書 acceptance.md:14 は「11つ」と書いています。3つの数が合いません。この数はプログラムの決まった文なので、修正の指示は出しません（Q5 の所見）。
- 監査人は、作業場で `python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --dry-run` を走らせました（rc 0・15.4秒）。出た文（cp88_work/cp88_dryrun.md・1981行）と acceptance.md（1980行）の違いは、末尾の空行1つだけでした。＝設計書は、元と案の写しから、プログラムが作ったままです。

### 監査に出す前のチェック（pre_audit_check.json）

- `.claude/state/pre_audit_check.json` を jq で開きました。at＝2026-10-24 22:32:35、design＝.claude/state/acceptance.md です。
- 18本のコマンドと終了コードは、依頼書の表と1行ずつ同じでした（approve の2本は null、verify_design_contract.py --diff と check_indicator_sources.py が 1、ほかは 0）。
- verify_design_contract.py --diff の 1 は、設計書の監査では新しい関数がまだ実物に無いためで、依頼書:471 のとおりです。

### 必読に要るファイル（道具が設計書と実装から拾った）

- 6本とも在ります。ただし `SDK/scripts/priority_rebuild/indicators/indicators.json` は、依頼書:420 の「いまは無いので」と違い、もう在ります（2026-10-24 20:50・3,189,432 バイト・git では untracked）。
- その sha256 は 748648feed25dce5fd13470361877531e4d1f16e2b67c3ab60e36c4cd5527230 で、監査人が作業場の写しで作った indicators.json と同じでした。写すプログラムの本物は、直す前の109行のままです。＝A12（仮当て）の後に、新しく作ったファイルだけが残っています（修正15・16）。


## 4. 所見

### 一般の観点

- ①統計学的妥当性：数字の根拠が足りているかを見ます。 ＝ 性質の食い違いの数が3通りに書かれている。3-2 の2件目は「46種」（やることの表:162）、okd_plan5_20261024.txt:51 は「オンで48種」、写しの走行の食い違いの記録では52種（オン48種＝46種＋向きつき2種・オフ4種）。301・723・56 は、監査人の走行の出力と合う（修正12）。
- ②リスク管理：損失が出たときや、プログラムが壊れたときの備えが在るかを見ます。 ＝ 壊れたときに止まる所は 4-5 のとおり揃っている。ただし、写す元のファイルが1行ずれると、照らす口も書く口も止まり、作り直す道が無い（Q3 の2つ目・修正8）。
- ③認知バイアス：CC の思い込みで組まれた所が無いかを見ます。 ＝ 「向きつき」に vol を当てた理由を役割の区分「値動きの幅」から決め、式（observe_diag.py:835）を開いていない（修正4）。4-13 で reversal も性質テストで確かめられると書いている（修正3）。
- ④ソフトウェア工学：プログラムの作りが正しいかを見ます。重複・壊れやすさ・テストの抜けが、見る物です。 ＝ 決まった欄の置き場（OWN）を、照らす口が中身を見ずに「入った」とする（acceptance.md:1180）。そのため CONST_REGISTRY の12件のうち7件が写らなくても通る（修正1）。mako は種類ごとに最初の1つだけを取る（acceptance.md:1121）。注記：「ほかの置き場の値」は、値に直せない物をソースの文のまま入れる（記録の中で211件のうち32件・区分の言葉の表で43件のうち25件・監査人の jq）。F-3 の決めたとおりの動きなので、修正の指示は出さない。
- ⑤再現性：同じ手順で、同じ結果が出るかを見ます。 ＝ 見つからなかった。20:50 に本物の置き場へ書かれた物と、監査人が 22:54 に作業場で作り直した物の sha256 が同じだった。
- ⑥実行プロセス：CC が、決めた流れのとおりに進めたかを見ます。 ＝ A12（仮当て）の後に、新しく作った indicators.json を消していない。設計書 2-1 の1行目の結果（acceptance.md:182）が、読み方「直す前は何も出ない」と食い違っているのに、気づいていない（修正15・16）。
- ⑦主エージェントバイアス：CC が、自分に都合よく判定した所が無いかを見ます。 ＝ F-3 と F-7 の完成の条件が、穴を見ない形になっている。F-3 は写すプログラムが読まない値を測れず、F-7 の grep は DECIDED_PROP の「向きつき」を見ない（修正2・9）。

### Q1 — 目的と施策は正しいか（優先度 A）

- 1つ目（目的）：目的は、要件定義の6番と7番に合っています。根拠＝core_requirements_full.md:85「**指標は、指標一覧（material）からだけ呼び出す。**」・:95〜96「誤りが見つかったら、置き場の1か所を直せば済む。」「直した物が、それを使う全部のロジックに、そのまま届く。」。結ぶ要件（acceptance.md:153）の「材料（指標）の誤りを教科書と照らして直し」は、親のやること M2-C-15 全体の文です。設計書1は写すだけで直しません。設計書2・3と ToDo の70番まで含めて初めて満たされます。結ぶ要件はプログラムが写す項目なので、所見だけに書きます。
- 2つ目（施策ごと）：
  - F-1＝出どころ（okd_plan5:17「置き場は、`scripts/priority_rebuild/indicators/indicators.json` の1本です」）が支える。手段は正しい。ただし別枠の材料8つの記録が無い（Q11）。
  - F-2＝出どころが支える。手段は正しい。もっと良い手段は無い。
  - F-3＝出どころ（okd_plan5:18「記録に入れる物は、89番で数えた置き場の全部です」）が支える。手段は一部だけ正しい。直す相手の一覧に頼るので、一覧の漏れ（Q8）がそのまま残る。決まった欄の置き場（OWN）は中身を照らさない。
  - F-4＝出どころ（okd_plan5:19〜24）が支える。手段は一部だけ正しい。種類の名前を文字で持たない値が、区分の言葉の表に入る（Q11）。
  - F-5＝出どころ（okd_plan5:26）が支える。手段は正しい。監査人の走行で、名前の違う56種がそろい、つながらない登録は0件だった。
  - F-6＝出どころ（要件定義書 R11・3-2 の1件目）が支える。手段は正しい。列を作る値・範囲・オン/オフは、いまの列を作る側の値を選ぶ。
  - F-7＝出どころ（okd_plan5:50「役割と値の作りからプログラムが決めます」）は一部だけ支える。「増やせる作り」は decide() の中だけで、indicators.json の表に1行を足すと照らす口が落ちる（Q4・修正9）。
  - F-8＝出どころが支える。作り直して照らす形は正しい。ただし写すプログラム自身が読み漏らした値は見つけない（Q4・修正2）。
- 3つ目（表に無い直し・要らない直し）：要るのに表に無い直しは、CONST_REGISTRY を全部写すこと（修正1）、別枠の材料の記録・2つ以上の名前に一度に入れる既定値の代入6か所・種類の名前で引けない値（修正10）です。要らないのに入っている直しは、ありません。やらないこと Y-01〜Y-07 の中に、この工事でやるべき物はありません。
- 4つ目（目標の②③④⑥）：②の「indicators.json が無い」（acceptance.md:293）は、3節の事実と食い違います（修正16）。③のつながりは正しいです。④は正しい物差しです。⑥は「列の値は変わりません」とだけ書き、記録の性質が INDICATOR_TABLE と52種で違うこと（オン48種・オフ4種）を書いていません（修正7）。

修正の番号＝1・2・7・9・10・16

### Q2 — 設計の主張は、出どころに合っているか（優先度 A）

- 1つ目（数字）：新しく入る数字「301」は、監査人の走行の「記録 301 種」と合います。ほかに新しい数字は入りません。
- 2つ目（指標・閾値・パラメータ・時間足）：
  - 指標＝この工事で足す指標は0種です。4-7 の「指標の名前が見つかりません」は、その結果の正しい出方です。
  - パラメータ＝範囲を持つ記録は117/301種です（監査人の走行）。残りの184種は範囲を持たないまま写されます。機能要件3の「パラメータが、範囲から探されている」との違いは残ります。代表の固定値は by_strategy の最初の値で、185種のうち50種は「1つのサイトだけのため使わない」で値を外しています（Plan agent が jq で数えた・例＝RSI の「スキャル（1つのサイトだけのため使わない）: [2]」）。これは core_requirements_full.md:53「①教科書にその戦略向けの値が在れば、それを使う（1つのサイトだけの値でもよい）」と合いません。ただし engine_tuner は代表の固定値をまだ読まない（core_requirements_full.md:113）ので、設計書1の段では損ないません。
  - 閾値＝記録の21の欄に、閾値の代表の固定値と閾値の範囲の欄がありません。正本は core_requirements_full.md:47「パラメータと閾値のそれぞれに、戦略（スキャル／デイトレ）ごと・指標ごとに、1つ決めます。」と、:60「パラメータと閾値を探す幅です。**指標ごとに1つ**です。」です。いまの置き場にもこの形の値はありません（gen_acceptance.py:563「THRESHOLD_KEY = "閾値の値"」の鍵は indicator_roles_thresholds.json に0件・修正11）。
  - 時間足＝変えません。合っています。
- 3つ目（要件1〜10）：
  - 1 目標・2 目的・3-1〜3-5＝反しない（いまの値のまま）。3-6＝当たらない。
  - 4 探し方・5 言葉＝閾値の代表の固定値と範囲の欄が無い（修正11）。
  - 6 指標の使い方＝別枠の材料には記録もオン/オフも無いので、「オン・オフが全部のロジックに効く」を indicators.json で持てない（修正10）。
  - 7 1か所で直せる＝札を役割の区分の表から決めるのは149/301種だけで、区分が空の152種は INDICATOR_TABLE の札を写す（Plan agent の jq）。2つの表の元はプログラム（gen_indicator_table.py:49〜51）に残る（修正9）。
  - 8 作ってはいけないもの＝反しない（乱数を使わない・CC が選んだ数の一覧を足さない）。
  - 9 監査で確かめること＝7-1② の「この力を損ないません」（acceptance.md:1717）は、設計書2の後に性質52種の判定が変わることを書いていない（修正7）。
  - 10 いまの実物との違い＝合っている。
  - 対応の表の誤り＝要件7 が「4-10 保存先・4-23」に当たっています（acceptance.md:102）。7 の中身を受けているのは §1 概要と F-7 です。この表はプログラムが作るので、修正の指示は出しません。

#### Q8 — 写す元を直す相手の一覧の「①写す」の行から読む形で、写し漏れを防げるか（優先度 A）

- 1つ目：7-4 の例（indicator_reference_diag.py:5477 の別枠6種の札）のほかに、6か所が直す相手の一覧に無く、indicators.json にも入りません。監査人が実物で確かめました（fix_inventory_20261024.md を grep して0件・作業場の indicators.json を grep して0件）。
  - indicator_reference_diag.py:4525「_ABER_L, _ABER_A = 5, 15                 # aberration の既定（中心線の本数, ATR の本数）」
  - indicator_reference_diag.py:4526「_ACCB_L, _ACCB_C = 20, 4.0               # accbands の既定（本数, 帯の係数）」
  - indicator_reference_diag.py:4527「_CE_L, _CE_M = 22, 3.0                   # ce（シャンデリア・エグジット）の既定（本数, ATR の倍率）」
  - indicator_reference_diag.py:4528「_HW_NA, _HW_NB, _HW_NC, _HW_ND, _HW_S = 0.2, 0.1, 0.1, 0.1, 1.0   # hwc の既定」
  - indicator_reference_diag.py:4529「_MASSI_F, _MASSI_S = 9, 25               # massi の既定（EMA の本数, 合計する本数）」
  - indicator_reference_diag.py:4803「_EBSW_L, _EBSW_B = 40, 10                # ebsw の既定（拾う波の上限の本数, 低域通過の本数）」
  - 原因は、一覧を作るプログラムが代入の左辺を1つの名前でしか読まないことです（gen_fix_inventory.py:131「nm = getattr(tg, "id", None) or getattr(tg, "attr", None) or ""」）。左辺が組の代入は名前が空になり、拾われません。
- 2つ目：自己テストの関数の中の17行（engine_tuner_exec.py:4183 の selftest に7行・engine_tuner_gen.py:4982 の selftest_rank_demand に1行と :5293 の selftest に5行・observe_diag.py:7484 の selftest_band に1行と :7946 の selftest に2行・regime_r9_diag.py:754 の selftest に1行）は、どれも試しの値です。写すべき値を落としていません。名前が selftest でない検査の関数（gen_materials.py:842 の condition_parts・observe_diag.py:7680 の _insp_hidden_params）の中の行は写されます。写しすぎにはなりますが、写し漏れにはなりません。

#### Q9 — 性質を一覧にし、方向から性質への対応の表で決める形は、読む側と M-1 を妨げないか（優先度 A）

- 1つ目：設計書2で読む側を記録に向けると、性質テストと法則 R10 は今と同じ判定を出せません。
  - 記録の性質は、INDICATOR_TABLE の性質と52種で違います（監査人の走行・オン48種）。内訳は、方向「反転サイン」で記録 reversal・INDICATOR_TABLE trend がオン27種、同じ方向で INDICATOR_TABLE none がオン19種・オフ2種、順張り値で記録 trend・INDICATOR_TABLE none がオフ2種、向きつきで記録 [trend, vol]・INDICATOR_TABLE none がオン2種です。
  - 性質テストが分けるのは trend と vol だけです（observe_diag.py:4669「if kind == "trend":」・:4680「elif kind == "vol":」・:4686「性質テストの型なし（反転サイン・状態量＝既知答えの側で検証）」）。そのため、INDICATOR_TABLE が trend のオン27種は、記録に向けると性質テストで確かめられなくなります。4-13 の「trend と vol と reversal だけ」（やることの表:245）は誤りです。
  - 一覧の形にすると、比べ方も変わります。observe_diag.py:4667 は性質を1つの値として読み（「kind = ref["prop"] if ref else …」）、engine_tuner_exec.py:1407 は「pm.get(p["fam"]) == sel["性質"]」で1つの値どうしを比べます。一覧を入れると、この比べは偽になります。一覧を「どれか1つ」で読むか「全部」で読むかは、設計書に書いてありません。
- 2つ目：「向きつき」に vol を当てる根拠は、式と合いません。LeeMykland の値は observe_diag.py:835「L(i)＝r_i ÷ √V_i」で、ふだんの揺れの平方根で割ってあります。性質テストの vol は「荒い相場の中央値 ≥ 静かな相場の中央値」を見ます（observe_diag.py:4680〜4683）。また vol を当てると、法則 R10（regime_laws.json:822〜841・数える部品「"性質": "vol"」）を、ばらつきの水準を測らない部品が満たします。実際に性質テストでこの2種が落ちるかは、走らせていないので「データ不足」です（10節の、走らせられなかった物の1）。

#### Q10 — 食い違いを1つの値にする選び方は、設計書2の後に列の値と探す幅を変えないか（優先度 A）

- 1つ目：列を作る値・範囲・オン/オフ・札は、いまの値と違いません。列を作る値は、いまのカタログの列を選びます（acceptance.md:1085）。範囲は search_limits.json の値です（acceptance.md:1117）。札は gen_indicator_table.py:122〜126 と同じ決め方です。違う欄は3つです。性質が52種（Q9）、V9 の名前が7種（gen_signal_families.py の V9_FAMILY_MAP を選び、observe_diag.py の _V9_LABEL_TO_FAMILIES を選ばないため）、ライブラリとの対応が1種です。どれも監査人の走行の食い違いの記録の数です。
- 2つ目：代表の固定値を選び直さずに写す形は、設計書1の段では要件4を損ないません。engine_tuner はまだ代表の固定値を読まないためです（core_requirements_full.md:113）。ただし50種は正本の選び方（core_requirements_full.md:53）と違います。設計書2で engine_tuner に読ませる前に、選び直しが要ります（ToDo の70番）。

#### Q11 — indicators.json は、工事のゴールに足りる情報を全部持つ形になっているか（優先度 A）

- 1つ目：足りません。
- 2つ目：足りない情報は、次の4つです。
  - (a) 別枠の材料に記録が無い。W%・下半分位置・帯内位置%・CVD・L-S比・taker_ls・時刻・曜日は、INDICATOR_TABLE の301種に無いので記録がありません（記録の名前を jq で引くと0件）。情報（observe_diag.py:250 の _DEMAND_FILES・indicator_reference_diag.py:5226 の DEMAND_REF・:5349 の RANGE_GEO_REF・:6037 の TIME_REF）は、区分の言葉の表に置き場ごとに入るだけで、名前では引けません。3-2 の8件目「CVD の記録の「ほかの置き場の値」の欄に」（やることの表:168）は、記録が無いので、実際の写し方と食い違います。
  - (b) 種類の名前で引けない値が、区分の言葉の表に入る。例＝_THERMO_L（indicator_reference_diag.py:4530「_THERMO_L = 20                           # thermo の既定（EMA の本数）」）・_HT_START_A・_HT_START_B・_MSW_P・_CDLZ_N・_DOJI_N・(_SR_ATR_TOL_LO, _SR_ATR_TOL_HI)（observe_diag.py:471）・_MA_FUNCS（observe_diag.py:1507）・RUNTIME_ALIAS（engine_tuner_exec.py:289）。
  - (c) CONST_REGISTRY の12件（indicator_reference_diag.py:6003〜）のうち、記録に入るのは出口の水準の5件（RSI_OB・RSI_OS・STOCH_OB・STOCH_OS・ADX_TREND）だけです。NEUTRAL_0・MID_50・FULL_100・SCALP_FLOOR・V11_SL_BUF・BE_TTL_BARS・TOL_SR の7件は写りません（監査人が作業場の indicators.json を grep して、引用符つきの名前が0件）。TOL_SR は engine_tuner_gen.py が使う S-R タッチの許容幅です。原因は2つです。1つは、閾値の値の欄が出口の水準の名前しか取らないこと（acceptance.md:1129）。もう1つは、照らす口が決まった欄の置き場を中身を見ずに「入った」とすること（acceptance.md:1180「elif k in ("決まった欄", "自己テストの見本"):」）。直す相手の一覧は CONST_REGISTRY を「①写す→②消す」としています（fix_inventory_20261024.md:1476）。監査人は、作業場の写しで OWN から "CONST_REGISTRY" を外して走らせました（書く走行 rc 0・14.1秒・--verify rc 0・違い0件）。CONST_REGISTRY は区分の言葉の表に入り（43件→44件）、12件の名前が全部その値の中に在りました。
  - (d) 閾値の代表の固定値と閾値の範囲の欄が無い（Q2）。

修正の番号＝1・3・4・5・6・7・10・11・12

### Q3 — コードは施策のとおりか（優先度 A）

- 1つ目（実装の指示ごと）：
  - 実装1（gen_indicators_draft.py）＝施策 F-2〜F-8 のとおりに書かれています。監査人が作業場の写しで走らせると、--selftest は rc 0（2.8秒・2件 ✅）、書く走行は rc 0（15.1秒・記録 301 種・欄 21・「①写す」の行 723）、--verify は rc 0（14.3秒・違い 0 件）でした。誤りは2つです。1つは、決まった欄の置き場を無条件で通すこと（acceptance.md:1180・修正1）。もう1つは、DECIDED_PROP の vol（acceptance.md:696・修正5）です。修正1と修正5は実装の指示の中身（impl_4-20_20261024.json）を変えるので、その指紋を持つ案の写しの【4-20】（okd_an_20261024.txt:72）も変わります（修正17）。
  - 実装2〜9（壊すプログラム8本）＝どれも、期待する文（EXPECT_MSG）が写すプログラムの出す文に含まれます。ss1_f5 の「INDICATOR_TABLE の名前1つにつながらない」は acceptance.md:1024 の文に、ss1_f7 の「方向から性質への対応の表に無い」は :1138 の文に含まれます。ss1_f7 が壊す文字「"ボラ量": "vol", 」は gen_indicator_table.py:51 に1か所だけ在ります。
- 2つ目（4-13 に無い壊れる物）：写すプログラムを呼ぶ所は、.py と .sh を grep して0件です。4-13 に書かれていない物が2つあります。1つは、本物の置き場に残った indicators.json です（3節）。もう1つは、写す元の14本のファイルが1行でもずれると、照らす口が落ちることです。置き場は「ファイル:行」で記録され（acceptance.md:967）、一覧の行がずれると「代入が見つからない」で止まり（:952）、もう在る indicators.json と違えば上書きせずに止まります（:1256）。そのため、設計書2で写す元のファイルを直した時点で、作り直す道も照らす道も無くなります。
- 3つ目（H2・H6）：反する所はありません。build_catalog は列の名前と関数を作るだけで、データを計算しません（acceptance.md:1032）。値段の水準を持つ閾値も足しません。

修正の番号＝1・5・8・15・17

### Q4 — 完成の条件で、施策が効いたと言えるか（優先度 A）

- 1つ目（施策ごと）：
  - F-1（#1）・F-4（#4）・F-5（#5）・F-8（#9）・Y-03（#10）＝施策を測っています。
  - F-2（#2）＝grep の文字「"indicators_draft"」は、`HERE / "indicators_draft/indicators.json"` のように書くとすり抜けます（修正13）。
  - F-3（#3）＝測れていません。--verify は、写すプログラムが作り直した物と indicators.json を比べるだけです（acceptance.md:1199「    want, rows = build()」）。写すプログラム自身が読まない値（Q8 の6か所・Q11(c) の7件）があっても、rc 0 になります。監査人の走行でも、7件が写らないまま --verify は「✅ 違い 0 件」でした（修正1・2）。
  - F-6（#6）＝作り直しとの食い違いだけを見ます。
  - F-7（#7）＝grep は「順張り値」「行き過ぎ」の2語だけを見て、DECIDED_PROP の「向きつき」（acceptance.md:696）を見ません（修正9）。
  - #8 の selftest＝decide() を手で作った辞書で試すだけで、indicators.json の表に1行を足したときの動きは試しません。手で足すと、照らす口（acceptance.md:1202）で落ちます（修正9）。
- 2つ目（6-5 の1件ずつ）＝6節に書きました。

修正の番号＝1・2・9・13

### Q5 — 設計書の書き方は正しいか（優先度 A）

- 1つ目（結論だけの文）：根拠のコマンドが無い文が3か所あります。4-13 の1行目「grep して0件・2026-10-24」（やることの表:241・修正14）、7-5 の11・12（acceptance.md:1767・:1768「0件です（2026-10-24 に grep）」）、7-1② の「この力を損ないません」（acceptance.md:1717・修正7）です。
- 2つ目（決めた作り方のとおりか）：監査人の --dry-run の出力と設計書の違いは、末尾の空行1つだけでした。手書きの項目の数は、依頼書の「7 件」・設計書の「11つ」・割り当ての表の9行で合いません。プログラムの決まった文なので、修正の指示は出しません。
- 3つ目（まこさんの OK）：逐語のファイルは工事のフォルダに在ります（ok_an_20261024.txt・ok_plan5_20261024.txt・ok_todo92_20261024.txt・ok_steps6_20261024.txt ほか）。
- 4つ目（捨てた案）：§5 では、良い案を理由なく捨ててはいません。ただし、「1回だけ写して indicators.json を正本にする」か、「元を正本のまま作り直して照らす」かの選びを、§5 に書いていません。この選びが書かれていないことが、修正8・修正9 の元です。

修正の番号＝7・8・9・14


## 5. 外部検索

### 検索 1 — 指標の分類の外の標準

- https://jp.tradingview.com/chart/USDCAD/GBAo2mqO-What-are-Technical-Indicators の逐語＝「Technical indicators fall into four main categories: trend, momentum, volatility and volume.」「Some indicators get classed into two groups and are open to interpretation about what group they should belong to.」
- https://sentimentrader.com/education/technical-indicators の逐語＝「This section groups commonly used indicators into four main categories — Trend, Momentum, Volatility, and Volume」
- https://ta-lib.github.io/ta-lib-python/funcs.html の関数の群＝「Overlap Studies」「Momentum Indicators」「Volume Indicators」「Volatility Indicators」「Price Transform」「Cycle Indicators」「Pattern Recognition」「Statistic Functions」
- 照らした結果：4つの群（トレンド・勢い・ボラ・出来高）は、役割の区分の表の7つ（向き・強さ・勢い・行き過ぎ・値動きの幅・出来高・位置）の中に在ります。TA-Lib の「Pattern Recognition」（ローソク足の形）に当たる区分はありません。札がローソクの16種は区分が空です（Plan agent の jq）。「two groups」の文は、性質を一覧にする作りを支えます（修正11）。

### 検索 2 — 1つのデータに集める作りの外の標準

- https://cdn.jsdelivr.net/npm/@tansuasici/claude-code-kit@1.21.0/tasks/lessons/2026-07-08-generated-config-single-source.md の逐語＝「Two hand-maintained sources of the same structure always drift.」「don't copy it — generate it from the base + an explicit delta」「add a CI --check that regenerates and diffs」
- https://dev.to/dobybaxter127/testing-against-state-drift-guarding-a-config-tool-whose-source-of-truth-lives-somewhere-else-kgf の逐語＝「a fixture is also a frozen copy of the truth.」「test each invariant at the seam where it actually lives.」
- 照らした結果：作り直して照らす口（--verify）は、外の標準の「regenerates and diffs」と合います。ただし外の標準は、元を正本として残す作りです。この工事は設計書3で元を消すので、消した後に何を正本にするかが決まっていません（修正8・9）。また、作り直して照らす形は、作るプログラムが読み漏らした値を見つけません。これが Q4 の F-3 の穴です（修正2）。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

確かめないまま実装に進んでよい。値が教科書に照らして正しいかは、この工事の範囲の外で、ToDo の70番で確かめます。

### 自己申告 2

このままでは進めない。実例が見つかりました（Q8 の6か所・Q11 の(a)(b)(c)）。先に修正1・2・10 を入れます。走らせるべきコマンドは、作業場の写しで OWN から "CONST_REGISTRY" を外した走行（監査人が走らせて rc 0・14.1秒）と、10節の走らせられなかった物の2（決まった欄の置き場に、記録に入らない種類が在るか）です。

### 自己申告 3

進めてよい。監査人の写しで RSI の記録を開くと、4-8・4-19 の例と合いました（列を作る値 [[5],[7],[9],[14],[21]]・範囲 int 2〜21・性質 ["trend"]・食い違いは by_strategy と review の [[7],[9],[14],[21]]）。

### 自己申告 4

進めてよい。設計書1は e38_logic_parts.py を写す相手にしていません。設計書2の元を作るときに、e38_logic_parts.py:75〜76・:86 と observe_diag の計算の関数の式を照らします。

### 自己申告 5

進めてよい。設計書を作るプログラムの読み方の件で、この工事の記録とは別の所です。閾値の欄が無い件は、修正11 に書きました。

### 自己申告 6

進めてよい。数えた結果は50/185種です。設計書2で engine_tuner に代表の固定値を読ませる前に、選び直します（ToDo の70番）。

### 自己申告 7

進めてよい。写すプログラムの食い違いの記録では、オフの116種の食い違いは性質の4件だけでした。by_strategy・roles・review はオンの185種しか持たないので、比べる相手がありません。

### 自己申告 8

進めてよい。ただし設計書3の前に、indicator_fix_plan.json の「作り」の欄を写す相手を決めます。確かめるコマンドは `jq '.["指標"][0]["作り"]' .claude/state/indicator_fix_plan.json` です。

### 自己申告 9

済み。監査人の作業場の写しで、書く走行は15.1秒、--verify は14.3秒でした。

### 自己申告 10

進めてよい。数える道具（ss_outside_probe.py）の数は、設計書3の後に0件を確かめる物差しです。監査人は、この道具が途中で gen_fix_inventory.py を走らせて本物の一覧を作り直す（ss_outside_probe.py:192）ので、走らせていません。

### 自己申告 11

見込みの「数分」は、実測で約15秒でした。見込みを超えていません。


## 7. 総合判定

### 結論と件数

- 結論＝CONDITIONAL-GO（根拠＝作りの向き〔写すプログラムで1回だけ写し、作り直して照らす〕は外の標準と合う。ただし CONST_REGISTRY の7件が写らないまま照らす口が通る穴〔修正1〕と、F-3 の完成の条件がその穴を測れない穴〔修正2〕の2つが Critical で、直せば先に進める）
- Critical＝2
- Major＝9
- Minor＝3
- Process＝3


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
OWN = (\"INDICATOR_TABLE\", \"REFS\", \"MATERIAL_FAMILIES\", \"INDUSTRY_MAP\", \"TA_CLASS_MAP\", \"EXT2\", \"CONST_REGISTRY\",
~~~
直した後の文字:
~~~
OWN = (\"INDICATOR_TABLE\", \"REFS\", \"MATERIAL_FAMILIES\", \"INDUSTRY_MAP\", \"TA_CLASS_MAP\", \"EXT2\",
~~~
根拠の抜き書き: .claude/state/acceptance.md:1180「        elif k in ("決まった欄", "自己テストの見本"):        # 見本は写さない（worklog 20261024:357）」
状態: 確定

#### 修正 2
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 270
直す前の文字:
~~~
| F-3 | 4-4 の1〜9の写す元を全部読み、記録に入らない写す元の値が0件。直す相手の一覧の「①写す」の行のうち、記録にも3つの表にも入らない行が0件 |
~~~
直した後の文字:
~~~
| F-3 | 直す相手の一覧の「①写す」の行のうち、記録にも3つの表にも入らない行が0件。4-4 の1〜8の写す元は、写すプログラムが読んだ値と indicators.json の値が同じかを見る（写すプログラムが読まない値は、照らす口では見つからない＝7-4） |
~~~
根拠の抜き書き: .claude/state/acceptance.md:1199「    want, rows = build()」
状態: 確定

### Major

#### 修正 3
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 245
直す前の文字:
~~~
性質テストが確かめられる性質は trend と vol と reversal だけで（observe_diag.py:4668〜）
~~~
直した後の文字:
~~~
性質テストが確かめられる性質は trend と vol の2つだけで（observe_diag.py:4669・:4680）、reversal と none は「性質テストの型なし」で通らない（:4686）。記録の性質が INDICATOR_TABLE と違う52種のうち、方向「反転サイン」で INDICATOR_TABLE が trend のオン27種は、読む側を記録に向けると、性質テストで確かめられなくなる
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:4686「                why[name] = "性質テストの型なし（反転サイン・状態量＝既知答えの側で検証）"」
状態: 確定

#### 修正 4
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 171
直す前の文字:
~~~
方向から性質への対応の表に「向きつき → ["trend", "vol"]」の1行を足します。trend にする理由は、読み方が上げと下げで値の向きが分かれるからです。vol にする理由は、役割の区分が「値動きの幅」で、急な跳ねの大きさを測る指標だからです。2つが正しいかは、材料の検査の性質テストが確かめます（trend＝上げの値動きの値が下げの値動きの値より大きいか・vol＝荒い値動きの値が静かな値動きの値より大きいか・observe_diag.py:4668〜）。いまの試しのデータで両方が通るかは、まだ走らせていません。
~~~
案A 直した後の文字:
~~~
方向から性質への対応の表に「向きつき → ["trend"]」の1行を足します。trend にする理由は、読み方が上げと下げで値の向きが分かれるからです。vol は当てません。LeeMykland の値は、今の1本の動きを、直前の K−1 本のふだんの揺れの平方根で割った物で（observe_diag.py:835「L(i)＝r_i ÷ √V_i」）、揺れの大きさで割ってあるので、ばらつきの水準を表しません。vol を当てると、法則 R10（regime_laws.json:822〜841・数える部品「"性質": "vol"」）が、ばらつきの水準を測らない部品で満たされます。trend が正しいかは、材料の検査の性質テストが確かめます（observe_diag.py:4669）。
~~~
案B 直した後の文字:
~~~
方向から性質への対応の表に「向きつき → ["trend", "vol"]」の1行を足します。trend にする理由は、読み方が上げと下げで値の向きが分かれるからです。vol にする理由は、役割の区分が「値動きの幅」で、急な跳ねの大きさを測る指標だからです。2つが正しいかは、材料の検査の性質テストが確かめます（trend＝上げの値動きの値が下げの値動きの値より大きいか・vol＝荒い値動きの値が静かな値動きの値より大きいか・observe_diag.py:4669・:4680）。承認の前に、この2種を trend と vol の両方で性質テストに通し、落ちた性質は当てません。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:835「    """Lee-Mykland（2008, Review of Financial Studies v21 n6）の jump の検定統計 L(i)＝r_i ÷ √V_i（論文の式(7)・式(8)）。」
状態: 案が複数

#### 修正 5
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json
直す箇所: 8
直す前の文字:
~~~
DECIDED_PROP = {\"向きつき\": dict(性質=[\"trend\", \"vol\"]
~~~
案A 直した後の文字:
~~~
DECIDED_PROP = {\"向きつき\": dict(性質=[\"trend\"]
~~~
案B 直した後の文字:
~~~
DECIDED_PROP = {\"向きつき\": dict(性質=[\"trend\", \"vol\"]
~~~
根拠の抜き書き: .claude/state/acceptance.md:696「DECIDED_PROP = {"向きつき": dict(性質=["trend", "vol"], 出どころ="やることの表 3-2 の11件目（まこさん 2026-10-24「ok」）")}」
状態: 案が複数

#### 修正 6
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 168
直す前の文字:
~~~
CVD の記録の「ほかの置き場の値」の欄に、_DEMAND_FILES（observe_diag.py:250〜259）の CVD の行としてそのまま写します
~~~
直した後の文字:
~~~
区分の言葉の表（ほかの置き場）に、_DEMAND_FILES（observe_diag.py:250〜259）の置き場として、そのまま写します（CVD は INDICATOR_TABLE の301種に無いので、CVD の記録は在りません）
~~~
根拠の抜き書き: .claude/state/acceptance.md:1155「        if not o["種類"]:」
状態: 確定

#### 修正 7
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 154
直す前の文字:
~~~
どちらも、⑤の照らしと、3-2 の値の決め方で見ます。
~~~
足す文字:
~~~
また、記録の性質は、INDICATOR_TABLE の性質と52種で違います（オン48種・オフ4種＝3-2 の2件目と11件目）。V9 の名前は7種、ライブラリとの対応は1種で、いまの読む側の値と違います。設計書2で、性質テスト（observe_diag.py:4667）と法則の「性質」の数え（engine_tuner_exec.py:1405〜1407）を記録に向けると、この52種の判定が変わります。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:1406「        pm = _refs_prop()」
状態: 確定

#### 修正 8
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 244
直す前の文字:
~~~
| 作業場の下書き .claude/state/indicator_review/indicators_draft/ | 写すプログラムが書かなくなる。消すのは設計書3 | 設計書3 |
~~~
足す文字:
~~~

| 写すプログラムの照らす口（--verify）と書く口 | 写す元のファイル（直す相手の一覧の「①写す」の行が在る14本）が1行でもずれると、置き場の「ファイル:行」が変わって照らす口が落ちる。一覧の行がずれると、写すプログラムは「代入が見つからない」で止まる（4-5）。書く口は、もう在る indicators.json と違えば止まり、上書きしない（4-10）。設計書2で写す元のファイルを直す前に、indicators.json を正本にして照らす口の相手を替えるか、照らす口を外すかを決める | 設計書2 |
~~~
根拠の抜き書き: .claude/state/acceptance.md:1256「        raise SystemExit(f"❌ {OUT} はもう在り、写す元から作り直した物と違う（1回だけ書く・違いは --verify で見る）")」
状態: 確定

#### 修正 9
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 274
直す前の文字:
~~~
| F-7 | indicators.json に2つの表が在り、札と性質が表から決まり、決められない種類が0件。写すプログラムの中に、区分の名前を書いた辞書が無い | ! grep -n -e '"順張り値"' -e '"行き過ぎ"' .claude/state/indicator_review/gen_indicators_draft.py && python3 .claude/state/indicator_review/gen_indicators_draft.py --verify |
~~~
案A 直した後の文字:
~~~
| F-7 | indicators.json に2つの表が在り、札と性質が表から決まり、決められない種類が0件。写すプログラムの中に、区分の名前を書いた辞書は DECIDED_PROP の「向きつき」の1行だけ（3-2 の11件目）。2つの表の元は、設計書1では gen_indicator_table.py:49〜51 の CAT2LIN・HOUKOU2PROP と DECIDED_PROP で、indicators.json の表に手で1行を足すと照らす口が落ちる。表に1行を足して増やせるのは、indicators.json を正本にした後 | ! grep -n -e '"順張り値"' -e '"行き過ぎ"' .claude/state/indicator_review/gen_indicators_draft.py && python3 .claude/state/indicator_review/gen_indicators_draft.py --verify |
~~~
案B 直した後の文字:
~~~
| F-7 | indicators.json に2つの表が在り、札と性質が表から決まり、決められない種類が0件。写すプログラムの中に、区分の名前を書いた辞書が無い | ! grep -n -e '"順張り値"' -e '"行き過ぎ"' -e '"向きつき"' .claude/state/indicator_review/gen_indicators_draft.py && python3 .claude/state/indicator_review/gen_indicators_draft.py --verify |
~~~
根拠の抜き書き: .claude/state/acceptance.md:1202「        if norm(have.get(key)) != norm(want[key]):」
状態: 案が複数

#### 修正 10
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/okd_an_20261024.txt
直す箇所: 131
直す前の文字:
~~~
設計書3の後に0件を確かめる |
~~~
足す文字:
~~~

| 記録の無い材料 | 別枠の材料（レンジ幾何の W%・下半分位置・帯内位置%、需給の CVD・L-S比・taker_ls、時間帯の時刻・曜日）は、INDICATOR_TABLE の301種に無いので、記録を持たない。情報（observe_diag.py:250 の _DEMAND_FILES・indicator_reference_diag.py:5226 の DEMAND_REF・:5349 の RANGE_GEO_REF・:6037 の TIME_REF）は、区分の言葉の表（ほかの置き場）に置き場ごとに入るだけで、名前で引けない。記録を足すかは、まこさんが決める |
| 直す相手の一覧に無い置き場 | indicator_reference_diag.py:4525〜4529・:4803 の、照合の関数の既定値を2つ以上の名前に一度に入れる代入（_ABER_L, _ABER_A・_ACCB_L, _ACCB_C・_CE_L, _CE_M・_HW_NA ほか・_MASSI_F, _MASSI_S・_EBSW_L, _EBSW_B）は、直す相手の一覧に無く（gen_fix_inventory.py:131 が代入の左辺を1つの名前でしか読まない）、indicators.json に入らない |
| 種類の名前で引けない指標の情報 | _THERMO_L・_HT_START_A・_HT_START_B・_MSW_P・_CDLZ_N・_DOJI_N（indicator_reference_diag.py:4530・:4801・:4802・:4804・:5060・:5061）、(_SR_ATR_TOL_LO, _SR_ATR_TOL_HI)（observe_diag.py:471）、_MA_FUNCS（observe_diag.py:1507）、RUNTIME_ALIAS（engine_tuner_exec.py:289）は、値に種類の名前の文字が無いので、その種類の記録ではなく区分の言葉の表（ほかの置き場）に入る |
~~~
根拠の抜き書き: .claude/state/indicator_review/gen_fix_inventory.py:131「            nm = getattr(tg, "id", None) or getattr(tg, "attr", None) or ""」
状態: 未決

#### 修正 11
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 171
直す前の文字:
~~~
（食い違いの記録に none を残します） | まこさん 2026-10-24「両方」「該当箇所複数にすれば？」・session_worklog_20261023.md:81 |
~~~
足す文字:
~~~

| 役割の区分の表（いま7行＝CAT2LIN）に、ローソク足の形の区分がありません。札がローソクの16種は区分が空で、INDICATOR_TABLE の札をそのまま写します。外の分類では、ローソク足の形は1つの群です（TA-Lib の関数の群「Pattern Recognition」） | 区分を足すかを、まこさんに伺います。足すときは、役割の区分の表に1行を足します | https://ta-lib.github.io/ta-lib-python/funcs.html |
| 記録の21の欄に、閾値の代表の固定値（スキャル／デイトレ）と閾値の範囲の欄がありません。正本は、代表の固定値を「パラメータと閾値のそれぞれに」決め、範囲を「パラメータと閾値を探す幅」としています（core_requirements_full.md:47・:60）。いまの置き場には、この形の値がありません（indicator_roles_thresholds.json に鍵「閾値の値」が0件） | 2つの欄を設計書1で空のまま足すか、T-2・T-3 で足すかを、まこさんに伺います | core_requirements_full.md:47・:60・gen_acceptance.py:563 |
~~~
根拠の抜き書き: .claude/rules/core_requirements_full.md:47「**最初の段階で、探さずに固定して使う値です。パラメータと閾値のそれぞれに、戦略（スキャル／デイトレ）ごと・指標ごとに、1つ決めます。**」
状態: 未決

### Minor

#### 修正 12
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 162
直す前の文字:
~~~
一覧＝value_conflicts_20261024.md:196（数えると46種）
~~~
直した後の文字:
~~~
一覧＝value_conflicts_20261024.md:196（数えると46種。写すプログラムの食い違いの記録では52種＝オン48種〔46種と3-2 の11件目の2種〕・オフ4種）
~~~
根拠の抜き書き: .claude/state/verbatim/m2c15-single-source-fix-20261023/okd_plan5_20261024.txt:51「- 決めた値がいまの値と違う種類（オンで48種）は、一覧にしてまこさんに伺います。」
状態: 確定

#### 修正 13
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 269
直す前の文字:
~~~
| ! grep -n '"indicators_draft"' .claude/state/indicator_review/gen_indicators_draft.py | 写すプログラム |
~~~
直した後の文字:
~~~
| ! grep -n '"indicators_draft' .claude/state/indicator_review/gen_indicators_draft.py | 写すプログラム |
~~~
根拠の抜き書き: .claude/state/acceptance.md:689「OUT = PR / "indicators" / "indicators.json"                 # F-2＝書く先（作業場には書かない）」
状態: 確定

#### 修正 14
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 241
直す前の文字:
~~~
（.claude/tools・.claude/hooks・.claude/breaks・scripts を grep して0件・2026-10-24）
~~~
直した後の文字:
~~~
（.claude/tools・.claude/hooks・.claude/breaks・scripts を grep して0件・2026-10-24・確かめ直すコマンド＝grep -rln --include='*.py' --include='*.sh' gen_indicators_draft .claude/tools .claude/hooks .claude/breaks v3-bitget-api-sdk/bitget-python-sdk-api/scripts（実装の後は .claude/breaks/ss1_*.sh の8本だけが出る））
~~~
根拠の抜き書き: .claude/state/acceptance.md:1767「| 11 | 【群1】直すファイルの行番号を指している文書を `git grep -n -E 'engine_tuner_(exec／gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
rm v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/indicators.json && rmdir v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators
~~~
根拠の抜き書き: .claude/state/acceptance.md:182「| 指標の情報を全部持つデータが在るか | `find v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild -maxdepth 1 -name indicators` | 直す前は何も出ない。直した後は、indicators のフォルダの名前が出る | v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators（終了コード 0） |」（監査人は本物を消さないので走らせていない＝かかった時間は測っていない）
状態: 未決

#### 修正 16
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/やることの表.md
直す箇所: 169
直す前の文字:
~~~
indicators.json の置き場 scripts/priority_rebuild/indicators/ は、いま無いフォルダです（ls で確かめた）。新しいフォルダを作ります
~~~
直した後の文字:
~~~
indicators.json の置き場 scripts/priority_rebuild/indicators/ には、2026-10-24 の A12（仮当て）の後も、写すプログラムが書いた indicators.json（20:50・sha256 748648feed25dce5fd13470361877531e4d1f16e2b67c3ab60e36c4cd5527230）が残っています。設計書の 2-1 の1行目は、このフォルダを出しています。仮当ての後に、新しく作ったファイルを消す手順がありませんでした。消して新しいフォルダとして作り直すかは、まこさんが決めます
~~~
根拠の抜き書き: .claude/state/acceptance.md:182「| 指標の情報を全部持つデータが在るか | `find v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild -maxdepth 1 -name indicators` | 直す前は何も出ない。直した後は、indicators のフォルダの名前が出る | v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators（終了コード 0） |」
状態: 確定

#### 修正 17
対象のファイル: .claude/state/verbatim/m2c15-single-source-fix-20261023/okd_an_20261024.txt
直す箇所: 72
直す前の文字:
~~~
ファイル: /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json sha256=c5db62a45bb1a9f6516626f8e474ced58ea1cad9cbd78c8e7597a36cfa53daf2
~~~
直した後の文字:
~~~
ファイル: /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json sha256=<修正1と修正5を当てた後の impl_4-20_20261024.json の sha256>
~~~
根拠の抜き書き: .claude/state/verbatim/m2c15-single-source-fix-20261023/okd_an_20261024.txt:72「ファイル: /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/verbatim/m2c15-single-source-fix-20261023/impl_4-20_20261024.json sha256=c5db62a45bb1a9f6516626f8e474ced58ea1cad9cbd78c8e7597a36cfa53daf2」
状態: 未決


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**開いたファイル（監査人と Plan agent）**
- 全文：依頼書（634行）、acceptance.md、やることの表.md、okd_an_20261024.txt・okd_plan5_20261024.txt・okd_todo92_20261024.txt、ok_*.txt、core_requirements_full.md、.claude/breaks/lib.sh、impl_4-20_20261024.json の1件目の中身（作業場に写して620行を全部）。
- 部分：fix_inventory_20261024.md（:1〜120・:621〜630・:1476・「①写す」の全行）、gen_fix_inventory.py（:120〜175）、observe_diag.py（:250・:469〜473・:819〜850・:1060〜1100・:1505〜1510・:1785〜1835・:4640〜4700・:6060〜6075）、indicator_reference_diag.py（:1040〜1046・:4525〜4530・:4799〜4806・:5058〜5062・:5470〜5482・:6000〜6030）、gen_indicator_table.py（:40〜55・:110〜135）、engine_tuner_exec.py（:287〜292・:1205〜1230・:1350〜1412）、engine_tuner_gen.py（:1888〜1900）、regime_laws.json（:815〜845）、gen_acceptance.py（:1360〜1376・:2486〜2530・:3340〜3386）、gen_audit_docs.py（:2604〜2720）、ss_outside_probe.py（:1〜30・HERE の行）、enforce_observe_diag_only.sh（止める条件の行）、pre_audit_check.json（jq）、indicator_params_by_strategy.json・indicator_fix_plan.json（jq）。

**走らせたコマンド（リポジトリの根で・全部 rc と秒数）**
- `shasum -a 256 .claude/state/acceptance.md`＝94d09098…（依頼書と一致）
- `python3 .claude/tools/gen_acceptance.py --work m2c15-single-source-fix-20261023 --dry-run > cp88_work/cp88_dryrun.md`＝rc 0・15.4秒・設計書との違いは末尾の空行1つ
- `python3 .claude/tools/gen_audit_docs.py result <依頼書> cp88_work/cp88_result.md`＝rc 0・0.14秒
- 作業場の写し `cp88_work/impl/gen_indicators_draft_copy.py`（実装1の全文から、HERE と OUT の2行だけを作業場向けに替えた物）：`--selftest`＝rc 0・2.8秒（2件 ✅）／書く走行＝rc 0・15.1秒（記録 301 種・欄 21・「①写す」の行 723・名前の違う種類 56・食い違いの記録が在る種類 126・区分の言葉の表 43 件）／`--verify`＝rc 0・14.3秒（違い 0 件）
- 修正1を当てた写し `cp88_work/impl/fix1/gen_indicators_draft_fix1.py`（上の写しの OWN から "CONST_REGISTRY" を外し、OUT を fix1/ に替えた物）：書く走行＝rc 0・14.1秒（区分の言葉の表 44 件）／`--verify`＝rc 0・14.2秒（違い 0 件）。CONST_REGISTRY の12件の名前が、区分の言葉の表の indicator_reference_diag.py:6003 の値に全部在った
- jq と grep：食い違いの欄ごとの数（系統 72・列を作る値 72・性質 52・範囲 26・V9 の名前 7・オン/オフ 2・ライブラリとの対応 1）、性質の食い違い52種の内訳、一覧に無い代入6か所（一覧で0件・出力で0件）、CONST_REGISTRY の7件（出力で0件）、修正の指示16件の直す前の文字（どれも相手のファイルに1か所）
- `git status --short`（監査の前と後）＝234行で同じ（11節）

**走らせられなかったもの**
1. Plan agent が求めた「LeeMykland の2種が性質テストの trend と vol を通るか」のコマンド。`python3 -c` の形で、hook（require_design_contract_before_run.sh）が止める打ち方のため。新しい調べのプログラムを作ると、恒久の決まり78番（思いつきで新しい道具を作らない）に当たるため、作っていない。＝Q9 の2つ目は「データ不足」。
2. Plan agent が求めた「決まった欄の置き場（REFS・EXT2・INDUSTRY_MAP・TA_CLASS_MAP・V9_FAMILY_MAP）に、INDICATOR_TABLE に無い種類と、mako が2つ以上の種類が在るか」のコマンド。理由は1と同じ。
3. `python3 .claude/state/indicator_review/ss_outside_probe.py`。途中で gen_fix_inventory.py を走らせ、本物の直す相手の一覧を作り直す（ss_outside_probe.py:192）ため。本物を書き替えない決まりに当たる。


## 11. 本物のファイルを書き替えていないこと

- 監査を始める前と、結果を書く前に、`git status --short` を取りました。出力は cp88_work/cp88_git_status_before.txt と cp88_work/cp88_git_status_after.txt です。`diff` は rc 0（違い無し）で、どちらも234行です。
- 監査人が書いたのは、作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp88_work/` の中だけです（cp88_dryrun.md・cp88_result.md・impl/ の写しと indicators.json・fix1/ の写しと indicators.json・git status の控え2本）。cp88_work/ は、監査の前から untracked でした（cp88_src.gen.md が在った）。
- 本物の acceptance.md の sha256 は、監査の前後で 94d0909881631f0a8b3ec69513355800e67842a4a2fc8db1e8f55128d48b65a8 のままです。本物の gen_indicators_draft.py は、直す前の109行のままです。
- 監査の後の `git status --short` のうち、この工事に関わる行は次の3行です（全234行は cp88_git_status_after.txt）。

```
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp88_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicators/
```

- 1行目の decisions.md と3行目の indicators/ は、監査の前から同じ状態でした（before の控えに同じ行が在る）。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-24_m2c15_single_source_fix_20261023_design_cp88_audit_request.md request_sha256=83cfad11235a5f17f33105063daae1d1da79b982cf30a63fe50d65ab24edec94 -->
