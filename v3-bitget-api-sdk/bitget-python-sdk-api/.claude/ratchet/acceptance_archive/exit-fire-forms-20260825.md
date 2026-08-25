# 設計書｜実行器の出口の発火条件を、入口と同じ「形ごとの評価」にする（97番）｜v3（61回目・2026-08-25・監査 cp7b の条件つき GO を反映）

TARGET: scripts/priority_rebuild/engine_tuner_exec.py

**承認の状態＝未承認。**v1 は監査 cp7 で NO-GO → v2 で反映 → 再監査 cp7b＝**OTHER（条件つき GO）**＝「改善1・改善2 を足した版なら承認できる」。**この v3 は cp7b の Major 2件＋Minor 5件を全部 反映した版。実装はまだ1行も入れていない。承認するかは まこさんが決める。**
**この設計書が直すもの＝next_step.md §6 の97番**（実行器が出口の発火条件で「形」を見ていない・2026-08-25 に実測で確定）。

<!-- ARC order=3 iter="exit-fire-forms-20260825" 前提="97番＝実行器の出口の発火条件が形（水準・傾き・交差・差）を見ず、材料の値と数字の1点比較だけをしている（60回目に実測で確定・worklog 20260825 §27）。まこさん決定 (う)＝いま何も足さず走らせない → このセッションで (あ)＝実行器を直す。v1 は監査 cp7 で NO-GO → v2 → 再監査 cp7b＝条件つき GO（材料の種別の規則が検査と実行で違う・恒等が空の成立を許す）→ v3 で反映" 採否="未定" 狙い="出口の発火条件の評価を、入口と同じ形ごとの評価器（_eval_cond）に一本化し、黙って別物になる評価（slope が値vs本数に化ける等）をコードから無くす。直した先に残る黙って別物（strict・pre・ref・混在・not・種別の鍵の二重）は検査で止める（fail-closed）" 内容="_collect_fire_cols を条件ごとの真偽の配列の事前計算に置き換え・_exit_fire_ok の指標の道を配列参照に置き換え（not も評価・種別の判定は _material_name に一本化）・validate_recipe に出口の形の検査8つ（fail-closed）を足す・selftest に形が効く実測を足す" 方法="入口の評価器との一致を直呼びで実測（8組）＋恒等3つ（付け替える道＝指標の level／--identity 3本／状態だけ。レシピを保存してハッシュ値と発火件数 ≥1 を記録）＋--selftest 全部 pass（exec と gen の両方・T6 含む）＋H2/G2 の印の取り直し" -->

## 0. まこさんの決定（逐語・2026-08-25）

> 「(う) にして、次のセッションで (あ) をやる」

(あ)＝**実行器を直して、出口の発火条件でも形を見るようにする**（97番の直し方の案の1つ目・本筋）。
手順の順番＝「その順番でOKなので進めて」＝実物を読む → 量を出す → 設計書 → **監査** → 承認 → 実装。
**歯止め**＝97番が直るまで、engine_tuner の探索の本走をしない（値を選ぶ走行・確認の走行とも）。この設計書に本走は入っていない。

## 1. 何が起きているか（実測で確定・worklog 20260825 §25・§27）

- 出口の発火条件の評価（`_exit_fire_ok` の `_ev`・`engine_tuner_exec.py`:2091-2105）は、**材料の値（生の列の i 番目）と value の数字を side で比べるだけ**。form を1回も読まない。
- その結果（3つとも実測）＝①**slope（傾き）は「値そのもの vs 本数 n」の比較に化ける**（拒否されずに走る＝黙って別物。§27 の直呼び＝上がり続ける列と下がり続ける列で結果が同じ・level と slope の結果が同じ）②**cross（交差）は値 `{'direction': 'up'}` を解けず案ごと拒否**（ミニ走行 1/10本）③**diff は2本目の材料が無視される**。
- いっぽう実行器は `FORM_SPEC` の exit_ok で **cross・slope・diff・candle_dir を「出口で使える」と宣言している**（:92・:98-116）＝**宣言と実装の食い違い**。
- **自己テストの ❌1件（T6・`engine_tuner_gen.py --selftest`）はこれが原因**（交差の案が拒否され、journal に書かれず、再開の再利用が 10本 → 9本）。

### 1b. 監査で分かった「直した先に残る黙って別物」（v1・v2 が外していたもの・全部 私が実物で裏取り済み＝worklog §32・§34）

| # | 何 | 実物 | この v3 でどう扱うか |
|---|---|---|---|
| ア | **寄せる先の評価器 `_eval_cond` が、向きの strict 2値（above_strict・below_strict）を slope・slope_avg・diff で逆向きに評価する** | :1700・:1708・:1732＝`(d >= th) if side == "above" else (d <= th)`。検査（:783）は SIDES 4値を通す。露出＝生成器は strict を0件 作る／恒等レシピの strict 3件は全部 level（正しい） | **出口では検査で拒否**（やること3の (c)）。**評価器の3行の直しは別の1変更＝101番** |
| イ | **玉の状態の材料に pre（前処理）を付けても、検査は通り、実行は黙って無視する** | :2094-2096（`m.get("state")` だけ読む）。`pre_ok`（:90）を守る検査は0件 | **検査で拒否**（やること3の (d)）。入口の側の pre_ok は範囲外＝105番 |
| ウ | **`not` を出口の fire に置くと、検査は通り、実行は KeyError で探索が丸ごと止まる** | `_walk`（:255-262）は not を持つ／`_ev`（:2106-2110）は持たない／gen:2760 の except は RecipeError と SampleError だけ | **`_ev` に not を足す**（やること2） |
| エ | **連動する閾値 ref が、出口で使えるようになってしまう**（`_eval_cond` は ctx を必ず作る＝:1678） | `_vnum_q`:1505-1507＝ctx が None のときだけ拒否。`_check_value`:659-672 は ref を出口でも通す | **検査で拒否**（やること3の (e)） |
| オ | **材料に状態と指標が混在する条件の行き先が、v1 の設計に無かった** | `_col_array`（:1601）は state を「入口の材料に使えない種別」で止める＝理由の文が誤解を招く | **検査で拒否・理由を明示**（やること3の (f)） |
| カ | **v1 の恒等 C6 は「触らない道（状態だけ）」しか比べていなかった** | 恒等ハーネス S2（`run_identity`:2537〜・出口の材料 :2605 は state だけ）。★**S1 の恒等レシピ（`recipes/identity_s1_legacy.json`）の出口 fire には指標（legacy_col）の level が3枝（MTFCUT・V59DOWN・V59FLAT）在る**＝v2 の「指標の材料は0件」は私の誤り（cp7 の主張を exec.py だけの grep で「一致」と写した）。向きは有利＝恒等の網は書いてあるより広い | **C6 を「付け替える道＋--identity 3本＋触らない道」の3つに** |
| キ | v1 の「評価のタイミングは入口と同じ on_close」は REVERSE_IND（placement=resting）に当てはまらない | :2361-2371（`hit = (l[i] <= lvl)` → `_exit_fire_ok`） | **C11 の文を限定**。順序そのものは範囲外＝102番 |
| **ク** | ★cp7b 新1（Major）＝**材料が「列」か「玉の状態」かを決める規則が、検査と実行で違う**＝検査は `_material_name` の優先順（:514 legacy_col → :518 geo → :523 state → :528 time → :533 family）／実行の `_ev` は :2094 `m.get("state")` だけ。**1つの材料に種別の鍵を2つ書くと、検査は列として通し、実行は玉の状態を評価する**（起きる組＝legacy_col＋state・geo＋state の2通り・監査の実測） | :514-535・:2093-2095。露出＝生成器はこの形を作らない | **種別の判定を `_material_name` に一本化**（やること1・2）**＋種別の鍵が2つ以上なら拒否**（やること3の (g)） |
| **ケ** | ★cp7b Q3（Major）＝**v2 の C6（恒等）は「空の成立」を許す**＝走らせるレシピが固定されておらず、付け替える枝が1回も発火しなくても「一致」になる。golden master は正しさを保証せず変化を検出するだけ＝動かなかった道の恒等は何も検出しない | v2 §5 C6 | **C6 にレシピの保存とハッシュ値・付け替える枝の発火件数 ≥1 を足す** |

**監査 cp7 §6 の8件 → v2 で反映（cp7b が 8/8 一致を確認）。cp7b §6 の7件 → この v3 のどこ**＝改善1（Major・種別の規則）→ やること1・2・3(g)・C7／改善2（Major・恒等の空の成立）→ C6・やること5／改善3 → 3(c) を性質表から導く／改善4 → 3(b) に value の制限／改善5 → C2 を8組・C3(ii) の数え方／改善6 → 各検査の拒否コード（G5・G6）／改善7 → §2 の7件（:2605 は S2・S1 の指標3枝・gen:2760・行の範囲・C1/C7 のコード）。

## 2. いま実物に在るもの（この設計が読んだ行・2026-08-25・cp7b で直した所は★）

**engine_tuner_exec.py（TARGET）**

| 場所 | 何か |
|---|---|
| :98-116 | `FORM_SPEC`（形の性質表・exit_ok＝level・cross・slope・diff・candle_dir の5形／pre_ok＝level・band・band_exclude／needs_side＝level・slope・slope_avg・diff） |
| :136 | `SIDES`＝above・below・above_strict・below_strict の4値 |
| :245-271 | `_walk`＝つなぎ木を歩いて条件を集める。**not を持つ**（:255-262） |
| ★:485-536 | `_material_name`＝材料1本の種別と解決名。**種別の優先順＝legacy_col（:514）→ geo（:518）→ state（:523）→ time（:528）→ family（:533）**＝これが「列か状態か」を決める唯一の関数になる（やること1・2） |
| ★:659-672 | `_check_value`＝ref を「知っている鍵」として通す（出口でも）。ref の在りか＝value 直下・lo・hi・th |
| :783 | `_check_cond`＝needs_side の形は side が SIDES に無ければ拒否（G5・★strict は通る） |
| ★:835-836 | `_check_cond`＝candle_dir は材料を `mats = []` にして無視する（材料を書いても黙って捨てられる） |
| :858-859 | `_check_cond`＝状態の材料は出口の文脈（where が exit で始まる）だけで許す（G6・★pre の検査は無い） |
| ★:1471-1479 | `_side_cmp`＝4値の比較（strict を持つ・配列でも単値でも同じ式） |
| :1494〜 | `_vnum_q`＝分位・定数・ref の解決。**ref は ctx が None のときだけ拒否**（:1505-1507） |
| :1642-1738 | `_eval_cond`＝**入口の形ごとの評価**。条件1つ → 全バーの真偽の配列。13形の式が在る。**ただし slope（:1700）・slope_avg（:1708）・diff（:1732）は side を above/それ以外 の2値でしか見ない＝strict が逆向き（101番）**。cross（:1719 `fin &`）は na=pass を効かせない・candle_dir（:1674-1677）は材料を読まない |
| :1741-1779 | `_eval_tree`＝条件の木（all・any・**not**・if-then）。入口の発火・判定の中身・hysteresis の内側が同じこの1つを呼ぶ |
| :1334-1387 | `validate_recipe` の出口の枝の検査。fire の条件は `_walk`（:1361）で集めて `_check_cond`（:1363）に通す＝**形の書式は検査するのに、実行は形を見ない** |
| :2036-2052 | `_collect_fire_cols`＝出口 fire の材料列を「生の値の配列」でループ前に1回 解決（形は見ない）。鍵が素の列名（:2049）＝同じ列に違う pre を掛けた2条件が衝突して先勝ち。呼び出し1か所＝:2174 |
| :2055-2111 | `_exit_fire_ok`＝出口 fire の評価。scope（:2058-2075）→ 状態の組み立て（:2079-2089）→ `_ev`（:2091-2110・1点比較・not なし・★種別は :2094 `m.get("state")` で決める・状態の道は isfinite を見ない＝104番） |
| :2301・:2337・:2356・:2371・:2386 | 売買ループからの呼び出し5か所（引数の形を変えなければ無変更）。:2361-2371＝resting の枝は約定（:2369）の後に fire を評価（102番） |
| ★:2529-2534 | `_md5_trades`＝売買記録（期間で絞った `to_csv`）の md5 と件数＝**恒等のハッシュ値はこれで取る** |
| ★:2537／:2729／:2866 | 恒等ハーネス＝`run_identity`（**S2**・出口 fire の材料は :2605 の state だけ）／`run_identity_l1`／`run_identity_s1` |
| :3491 | `selftest`（exec 自身の自己テスト）。出口の呼び出し2か所＝:3712・:3714（状態だけの条件＝無変更）。壊し方の見本は `broke()` が拒否コードの文字列で照合する |

**engine_tuner_gen.py（今回は触らない・読んだだけ）**

| 場所 | 何か |
|---|---|
| ★:813-821 | `strip_marks`＝印を validate の前と実行器へ渡す直前に外す（:804・:810）＝**条件の canonical JSON に印は入らない** |
| :1632-1634 | `_state_cond`＝玉の状態を見る出口の条件は **form="level" で固定・pre なし・value は const**（生成器が作るのはこれだけ） |
| :1656-1726 | `_exit_indicator_cond`＝指標を見る出口の条件。level は `_EXIT_LEVEL_CONST` の定数だけ（:1712-1715 のコメント＝「実行器は出口の発火条件で分位を解けない」） |
| :2404-2450 | `_cond_keys`＝分位の鍵を作る枝＝level・ref の挟み・band・diff・cross(列1本)。slope の閾値の鍵は無い（103番） |
| :2456-2461 | `needed_qkeys`＝**出口の枝の発火条件も歩いて分位の鍵を集める**（D2・直し済み） |
| ★:2760 | 案1本を走らせる関数（`run_trial_guarded`:2739〜）の except＝`(ex.RecipeError, SampleError)` だけ＝それ以外の例外は上へ抜けて探索が止まる |
| :3386 | `synth_df(n=3000, seed=7)`＝自己テストの合成データ |
| ★:3412／:3841-3879 | gen の `selftest`／T6（ミニ本走＝seed=11・第1段10本・第2段6本・top_k=2・purpose=check・再開で再利用 10本 を期待） |

**恒等レシピ `recipes/identity_s1_legacy.json`（プログラムで数えた・2026-08-25）**＝出口 fire の材料の種別＝MTFCUT（state 1本＋legacy_col 2本）・FASTCUT（state）・V59DOWN（legacy_col）・V59FLAT（legacy_col）・MFESTALE（state）・TIME（state）＝**指標の level を持つ枝が3枝**＝付け替える道を実データで通る恒等（C6(ii)）。

**表（exit_families_rules.json と、機械生成の exit_families.json）**

- 指標の条件を持つ枝＝**19枝中2枝**＝REVERSE_IND（forms=cross・level・slope・diff・placement=resting・理由 INDICATOR_REVERSE_TP）／BREAKOUT（forms=level・slope・diff・placement=on_close・理由 BREAKOUT_CUT）＝枝×形 7件。玉の状態だけの枝＝7枝（条件11個・全部 level）。発火条件なし＝10枝。
- confirm_conditions.rule（承認済み）＝「閾値は分位」＝いまの実装（定数3部品だけ）と食い違っている（→ §7 (a)・99番）。

**numpy の型と json（私の実測）**＝`json.dumps(np.int64)`・`np.bool_` は TypeError／`np.float64` は通る＝やること1 の「json にできない値は RecipeError」が要る。

**そのほか読んだもの**＝next_step.md §6 の97番・session_worklog_20260825.md §25〜§27・§30〜§34・監査報告書 cp7 と cp7b（全文）・leak_causality_diag.py の冒頭・v9_exits.md。

## 3. 深掘り4点

- **① 真因（2つ）**＝(1) 出口の発火の評価が、形の評価器（`_eval_cond`）とは別に「値の1点比較」として独自に書かれ、形の実装が入口の側だけで育った。(2) ★**性質表（`FORM_SPEC`）・材料の種別（`_material_name`）と、検査・実行が接続されていない**＝pre_ok を守る検査が0件・strict を評価器が3形で未対応・種別の規則が検査と実行で別（cp7b 新1）＝「検査が通す × 実行が黙って別物」の型は同じ根から複数 生えている。**分類の規則が2つ在れば、検査と実行は必ずどこかで別物になる。**
- **② 期待値分解**＝net の回ではない（実験ゼロのまま直す）。効果＝(a) 嘘の net の道を塞ぐ（歯止めの解除の前提）(b) 出口の確認条件の形が実質 1形 → 5形 (c) T6 ✅ (d) 直した先に残る「黙って別物」（strict・pre・ref・混在・not・種別の二重）を検査で止める。
- **③ root か symptom か**＝root。1点比較の道を「玉の状態の条件」だけに限定し、指標の条件は入口と同じ評価器を通す。**種別の判定も `_material_name` の1か所に寄せる**（実行の側に別の規則を持たない）。strict の反転（評価器の3行）は別の1変更（101番）。
- **④ ベースアップ**＝cp7 の外部検索（same-bar execution・交差の定義）と cp7b の外部検索（golden master は変化の検出であって正しさの保証ではない／denylist は名指しの外を抜ける・allowlist と schema で閉じる）を取り込んだ＝C6 の発火件数・(c) を性質表から導く・(g) 種別の鍵は1つだけ、の根拠。

## 4. やること（5件）

| # | 何を | どこ |
|---|---|---|
| 1 | **`_collect_fire_cols` を「条件ごとの真偽の配列」の事前計算に置き換える**＝出口の枝の fire を `_walk` で歩き、**`_material_name(m, lane)[0] != "state"` の材料だけを持つ条件**（candle_dir＝材料なし を含む）を `_eval_cond(c, df, geo, lane, qtable)` で全バーの真偽の配列にする（★「`"state" in m`」で決めない）。**鍵＝`json.dumps(c, sort_keys=True, ensure_ascii=False)`**。**json にできない値（numpy の int64・bool_ など）が混じったら明示の RecipeError で止める**（黙って別の鍵にしない）。呼び出し（:2174）に qtable を渡す。評価の式をここに書き写さない | exec :2036-2052・:2174 |
| 2 | **`_exit_fire_ok` の `_ev` を直す（3点）**＝(i) 指標の条件の道を「配列の i 番目を引く」に置き換える (ii) 木の歩きに `not` を足す（`_eval_tree`:1765 と同じ意味）(iii) ★**状態か指標かの分岐（:2093-2095）を `_material_name(m, lane)[0] == "state"` に寄せる**（`m.get("state")` を消す）。**玉の状態の値の評価の式（1点比較・`_vnum`・isfinite なし）は変えない**（104番は範囲外）。引数の形は変えない＝呼び出し7か所 無変更 | exec :2091-2110 |
| 3 | **`validate_recipe` の出口の検査に8つ足す（全部 fail-closed・拒否の理由と拒否コードを明示）**＝(a) 指標の条件の form が `forms_where("exit_ok")` に無ければ拒否【G5】(b) 玉の状態の条件（`_material_name` が state）は form が level 以外なら拒否・★value に threshold_q か ref が在れば拒否（状態の値は分位の解決表を持たない・n／const／legacy だけ）【G6】(c) ★`forms_where("needs_side")` のうち level 以外の形で side が strict なら拒否（名指しでなく性質表から導く・101番が直るまで＝外す判断は まこさん）【G5】(d) 材料に state が在って pre も在れば拒否／pre_ok=False の形の材料に pre が在れば拒否【G6】(e) value（lo・hi・th を含む）に ref が在れば拒否【G5】(f) 材料2本で state と指標が混在すれば拒否（理由＝「玉の状態は指標と組み合わせて評価できない」）【G6】(g) ★**材料の辞書に種別の鍵（legacy_col・geo・state・time・family）が2つ以上 在れば拒否**（`_material_name` の中に足す＝入口・出口とも）【G6】(h) ★candle_dir に材料が書いてあれば拒否（黙って捨てない）【G5】 | exec :1359-1363 の並び・(g) は :514 の手前 |
| 4 | **exec の `selftest` に「形が効くこと」の実測を足す**＝直呼び（上がり続ける列／下がり続ける列・60バー）で C1・C2・C3(i)・C4・C5・C7・C12・C13 を機械が毎回 確かめる。壊し方は固定の見本＝C7 の偽レシピ11通り（拒否コードで照合） | exec :3491 の中 |
| 5 | **★恒等の基準値を、実装の前に測って記録する（golden master）**＝(i) 付け替える道のレシピ＝BREAKOUT（on_close・level・定数）と REVERSE_IND（resting・level・定数）を含み、**同じ列に違う pre を掛けた2条件を入れない**レシピを JSON で `.claude/ratchet/golden/exit_forms_20260825/` に保存し、その sha256 を §9 に書く (ii) `synth_df(3000, seed=7)` で走らせた売買記録の md5（`_md5_trades`）と件数、**exit_reason ごとの件数**（BREAKOUT_CUT と INDICATOR_REVERSE_TP が ≥1 件でなければ「未判定」と書き、レシピか合成データの長さを変えて ≥1 にする＝コードは変えない）(iii) 状態だけの枝のレシピも同じく保存・md5 (iv) `--identity` L1・S1・S2 の md5 と、S1 の指標3枝（MTFCUT・V59DOWN・V59FLAT）の発火件数。**数字は §9 に走らせた出力で書く（手で書かない）** | §9・`.claude/ratchet/golden/` |

**触らないもの**＝`score.py`・`eval_engine.py`（H13）／執行（placement・exec_method・maker/taker・resting の順序＝102番）／入口の評価（`_eval_cond`・`_eval_tree` は呼ぶだけ＝strict の3行は101番）／生成器（engine_tuner_gen.py）／表（exit_families）／期間（periods.py）／状態の条件の値の評価の式（104番）／`_material_name` の優先順そのもの（(g) は「2つ以上なら拒否」を足すだけ・順序は変えない）。

## 5. 完成の条件（全部 走らせた出力で確かめる・数字を手で書かない）

| # | 条件 | いまの実測（直す前） |
|---|---|---|
| C1 | **slope が傾きを見る**＝直呼びで side=above：上がり続ける列 → 成立・下がり続ける列 → 不成立／side=below：その逆。**strict は検査で G5 で拒否される** | above でどちらも成立／strict は検査を通り、評価器で逆向き |
| C2 | **入口の評価器との一致**＝同じ条件・同じ列で、`_exit_fire_ok` の各バーの結果が `_eval_cond` の配列と全バー一致する。★組は**8**＝level・slope・diff（na=fail／na=pass の2通りずつ＝6）＋cross・candle_dir（na=pass が効かないことが入口と同じ＝各1）。守るもの＝添字のずれと scope・状態の配管 | slope・cross・diff・candle_dir は一致しない |
| C3 | **cross が評価される**＝(i) 直呼びで交差のバーだけ真・前後は偽・最初のバーは偽 (ii) T6 と同じミニ走行（`synth_df(3000, seed=7)`・seed=11・第1段10本・第2段6本）で★**理由を問わず拒否が 0** かつ cross を含む案が ≥1本 生成されたことを数えて示す（0本なら (ii) は未判定と書く） | (ii) 1/10本 拒否 |
| C4 | **diff の2本目が効く**＝2本目の材料を入れ替えると結果が変わる（直呼び） | 2本目 無視 |
| C5 | **candle_dir が評価される**＝陽線／陰線の列で逆の結果（直呼び） | 材料なしで G6 に落ちて評価不能 |
| C6 | **★恒等（golden master・空の成立を許さない）**＝やること5 で保存したレシピ（sha256 が §9 と一致するもの）を直した後に走らせ、(i) 付け替える道＝売買記録の md5 と件数が §9 と一致 **かつ BREAKOUT_CUT・INDICATOR_REVERSE_TP の件数が §9 と一致し ≥1** (ii) `--identity` L1・S1・S2 の md5 が一致 **かつ S1 の指標3枝の発火件数が一致**（0件なら (ii) の指標の部分は未判定と書く）(iii) 状態だけの枝＝md5 一致 | —（基準値は実装の前に測る） |
| C7 | **検査が締まる**＝偽レシピ**11通り**が指定のコードで拒否される＝band を出口の fire に【G5】／state×slope【G6】／slope の above_strict【G5】／diff の below_strict【G5】／state＋pre【G6】／slope（pre_ok=False）＋pre【G6】／value に ref【G5】／材料に state と指標の混在【G6】／★種別の鍵が2つ（legacy_col＋state・geo＋state）【G6】／★state に threshold_q【G6】／★candle_dir に材料【G5】 | 11通り全部 素通り（監査の実測＝8通り・残りは同じ検査の欠け） |
| C8 | **自己テスト2本**＝`engine_tuner_exec.py --selftest` 全部 pass（やること4 の追加分を含む）**＋** `engine_tuner_gen.py --selftest` 全部 pass（**T6 ✅＝再開の再利用 10/10**・18マス ✅ 維持）**＋** `--lint-provenance` 0件 維持 | gen の T6 ❌1件 |
| C9 | **H2 の印の取り直し pass**（leak_causality_diag・全検査・実測 4分49秒）**・G2 の印の取り直し pass**（gen_signal_families --verify・実測 29.6秒） | 直す前の印は有効（コードを触ると失効） |
| C10 | **verify_design_contract --diff 齟齬 0件** | 0件（v3 も同じ SPEC） |
| C11 | **配列方式は新しい未来参照を増やさない**＝cross は i-1 と i（過去だけ）・slope は n 本前との差・静的検査（`h2_scan`）で新しい `.shift(-`／`center=True` が 0件。**これは H2 全体の担保ではない**＝resting の枝の順序（:2361-2371）は既存の作りで範囲外（102番） | — |
| C12 | **分位が出口で解ける**＝直呼びで `{"threshold_q": "q50"}` の出口 level 条件に、鍵1つの qtable を渡すと、成立／不成立が q50 の実値で決まる。鍵が無ければ RecipeError（fail-closed） | 出口は `_vnum` だけ＝解けない |
| C13 | **`not` が評価される**＝内側が真の `not` を出口の fire に置いた直呼びで偽になり、KeyError が出ない | KeyError 'if' |

## 6. ★疑似シミュ由来の固定値ゼロ

**この設計は新しい数字を1つも作らない。**閾値・分位・範囲・定数を足さない。評価の式は入口の実物（`_eval_cond`）を呼ぶだけ。完成の条件の判定は全部、走らせた機械の出力（C1〜C13）。恒等の基準値も走らせて測り、レシピはファイルで固定する（やること5）。

## 7. 入っていないもの（正直に）

| # | 何 | なぜ入れない・どこに残すか |
|---|---|---|
| (a) | 生成器の level の定数縛り（`_EXIT_LEVEL_CONST`）を分位に戻す＝表の決まり「閾値は分位」との食い違い。縛りの理由が消えるのは level・band・diff・cross(列1本) の分だけ | 生成器を触る別の変更＝**99番**。決めるのは まこさん |
| (b) | 生成器が diff を1回も作らない | 同上＝**100番** |
| (c) | confirm_max の実装 | 別件のまま＝**96番** |
| (d) | ローソク系統を出口の表の枝に戻すか | まこさんが決める（表の変更＝再承認） |
| (e) | 98番・95番（第2段） | 第2段（TPE）を触る別の回 |
| (f) | **探索の本走**＝実装と検証は合成データの自己テストとミニ走行と恒等ハーネスだけ。実データの試行はゼロ | 歯止め＝97番。**解除するかは、直しの実測を見て まこさんが決める** |
| (g) | 入口の評価器の strict の反転（`_eval_cond` の3行）を直す | 別の1変更＝**101番** |
| (h) | resting の枝の「約定の後に close の条件で取り消す」順序 | 既存の作り＝**102番** |
| (i) | slope の閾値 th の分位の鍵 | 生成器＝**103番** |
| (j) | 状態の条件の道が na=pass を無視する | **104番** |
| (k) | 入口の側の pre_ok の検査 | **105番** |
| (l) | ★`_material_name` の優先順そのものを変えること（legacy_col が state より先） | 変えない。(g) で「2つ以上は拒否」にすれば順序は意味を持たなくなる |

## 8. 変更の単位（H16）・審判整合（D）・§4.6 の照合

- **H16＝1変更**＝「出口の発火条件の評価を、入口の形ごとの評価器に一本化する（＋直した先に残る黙って別物を検査で止める・種別の判定も1か所に）」の1レバー。入れないものを §7 に12件 明示した。
- **審判整合（D）**＝新しい exit_reason を出さない・maker/taker の登録を変えない・score.py/eval_engine を触らない（H13）。
- **H1**＝非該当。**H2**＝該当＝C11（配列方式は新しい未来参照を増やさない・H2 全体の担保ではない＝102番）。**H3〜H5**＝非該当（net 計算・コスト・約定モデルを触らない）。**H6**＝非該当（新しい閾値・USD 絶対値を作らない）。**H8**＝非該当。**H15**＝非該当。

## 9. 実装の記録（2026-08-25・61回目・全部 走らせた出力＝worklog 20260825 §36〜§39）

### 9-1 恒等の基準値（やること5＝実装の前に測った・golden master）

- **保存先**＝`.claude/ratchet/golden/exit_forms_20260825/`＝`recipe_level_both.json`（sha256 `c29e6cb4dbfc3e74…`）・`recipe_state_only.json`（sha256 `2d9b2108e7fa8c3e…`）・`baseline_before.json`・`baseline_after.json`。合成データ＝`synth_df(3000, seed=7)`（3000本・2024-05-01 00:00〜05-11 10:00）。
- **付け替える道（level_both）の作り方**＝生成器の案（`sample_structure`・種 [61,5,0]）のうち BREAKOUT_CUT と INDICATOR_REVERSE_TP の両方の枝を持つもの（600本中1本）の指標の条件を、生成器の関数 `_exit_indicator_cond` に forms=['level'] を渡して引き直した（数字は定数レジストリ＝RSI19__15m ≥ RSI_OB／Stoch%K9__15m ≤ STOCH_OS）。**生成器の案600本には「両方の枝を level で持つ案」が0本だった**（正直に）。同じ列に違う pre を掛けた2条件は無い（プログラムで確かめた）。
- **直す前の実測**＝level_both **663行・md5 9ee158d88a58ff7f17d006d3fb2fcc54**（BREAKOUT_CUT 257・INDICATOR_REVERSE_TP 206・MFE_DRAWDOWN_CUT 157・TP_FILLED 26・SL_FILLED 16・FORCE_CLOSE_EOD 1）／state_only **780行・md5 f522362349fd601c50d8e8bc4dba41f7**（MFE_DRAWDOWN_CUT 586・TP_FILLED 189・SL_FILLED 5）／`--identity` S2 **165行・7b01f51b5a9b29b3c05a7b340c203ba1**（BE_EXIT 101・TIME_EXIT 42・PARTIAL_TP 17・TP_FILLED 5）・L1 **367行・96a9102ec8a34f94cf01e9e463f6aade**・S1 **6,569行・18b3d31a5fe71c4a4b5f83cf1771a46c**（TREND_CONT 1004 ほか）。所要＝3本で28秒（見込み「30分」は外れ＝短窓104秒の大半はキャッシュ無しのデータ読み込み）。

### 9-2 完成の条件の実測（実装の後）

| # | 結果 | 出典 |
|---|---|---|
| C1 | ✅ slope side=above：上がる列 True・下がる列 False／below：逆。strict は G5 で拒否 | `engine_tuner_exec.py --selftest`「番人 97番」✅ |
| C2 | ✅ 8組 全バー一致（level・slope・diff × na 2通り＋cross＋candle_dir） | 同上 |
| C3 | (i) ✅ 交差のバーだけ真 (ii) 同じ種のミニ走行＝案10本・**cross を含む案 1本・第1段の拒否 0**（直す前は 1/10 拒否）。**★第2段は 2/6 拒否＝98番（解決表の鍵・既知・別件）＝「理由を問わず0」はこの分 満たせない** | worklog §38 |
| C4 | ✅ 2本目を 0→1000 で True→False | selftest ✅ |
| C5 | ✅ 陽線／陰線で逆 | selftest ✅ |
| C6 | ✅ 3つとも一致＝(i) level_both md5 9ee158d8…・663行・件数 同じ（BREAKOUT_CUT 257・INDICATOR_REVERSE_TP 206 ≥1）(ii) --identity S2/L1/S1 の md5・件数 同じ（S1 の TREND_CONT 1004 も同じ。★枝ごとの件数は売買記録に無い＝理由の合計で代えた）(iii) state_only md5 f5223623… 同じ | `baseline_after.json`・`scratchpad/identity_after.log` |
| C7 | ✅ 偽レシピ11通り＝指定のコードと言葉で拒否・正しい5形は通る | selftest ✅ |
| C8 | **gen ✅ 全部 pass（297.73秒・T6 の再開 10/10・18マス ✅・--lint-provenance 0件）＝60回目の ❌1件（T6）が消えた**。**exec＝97番の番人 ✅・★全体は ❌3件＝「並びの決まらない入れ物」の検査が gen の3行を指す＝git の HEAD でも同じ3件（元から・私の変更と無関係・検査の誤検知＝106番）** | worklog §37・§38 |
| C9 | ✅ H2 印 `29277f8ba7a1b987…`（285.48秒・検査2 注記なし0件・番人 pass・1-a/1-b/1-c 食い違い0件）／✅ G2 印 `d8cad53a…`（27.57秒・見本11件） | `scratchpad/h2_after.log`・`g2_pass.json` |
| C10 | ✅ `--diff` 齟齬 0件 | 実測 |
| C11 | ✅ H2 の検査2（全数スキャン81本）で注記なしの未来参照 0件＝新しい未来参照なし。resting の順序は範囲外（102番） | `h2_after.log` |
| C12 | ✅ q50=70 で True・95 で False・解決表なしは RecipeError | selftest ✅ |
| C13 | ✅ not で偽・KeyError なし | selftest ✅ |

### 9-3 設計書からの差（正直に・3件）

1. **検査 (g) の範囲**＝設計書は「5つの鍵が2つ以上なら拒否」。実装は **legacy_col には family を添えてよい**（恒等レシピ3本に8か所 在る既存の書き方で、family は系統の判定＝gen `_lineage_of`・exec の G3 が読む鍵）。最初 設計書どおりに書いたら、恒等レシピの検証で止まった。監査が問題にした組（legacy_col＋state・geo＋state）と、state／geo／time に family を添える形は拒否のまま。
2. **C8 の exec 全体**＝元から在る ❌3件（106番）が残る＝「全部 pass」ではない。97番の番人は ✅。
3. **C3(ii)**＝第2段の 2/6 拒否（98番・既知）が残る。第1段の拒否は 0。

### 9-4 hook に止められた回数＝3・時間の見込みの外れ＝1

- 恒等検収の引数を変数（`$a`）で渡して G2 の印の hook に止められた（1回）／G2 の印の取り直しが「承認の経路が一時的に使えない」で止まった（1回）／検査 (g) が恒等レシピで止まった（1回・上の 9-3 の1）。
- 恒等検収3本の見込み「約30分」→ 実測28秒（根拠にした短窓104秒はキャッシュ無し）。次の根拠＝「3本で約30秒」。

---

DESIGN_CONTRACT

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_exec.py",
 "self_check_calls": [
  "RecipeError",
  "attach_recipe_columns",
  "build_name",
  "build_regime_columns",
  "cap_of",
  "e36_maker_taker_behavior_check",
  "engine_params_from_recipe",
  "forms_pair_in",
  "forms_where",
  "identity_l1_recipe",
  "identity_recipe",
  "identity_s1_recipe",
  "l1_engine_params",
  "legacy_cols_in",
  "main",
  "maker_taker_sync_check",
  "material_array",
  "pair_ops",
  "pre_ops",
  "regime_cols",
  "run_identity",
  "run_identity_l1",
  "run_identity_s1",
  "run_recipe",
  "s1_engine_params",
  "selftest",
  "source_logic",
  "unordered_iteration_scan",
  "validate_recipe"
 ]
}
```

## 作る関数の一覧（★手書きしていない＝`--write` の出力・2026-08-25 の実物から）

> 今回 変える関数は全部 内部の関数（`_collect_fire_cols`・`_exit_fire_ok`・`_material_name` の中・`validate_recipe` の中・selftest の中）＝**公開する関数の一覧は実装の前後で変わらない**。変わったら `--diff` が検出する。

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_exec.py",
 "public_functions": {
  "forms_where": [],
  "forms_pair_in": [],
  "build_name": [],
  "RecipeError": [],
  "pre_ops": [],
  "pair_ops": [],
  "regime_cols": [],
  "cap_of": [],
  "validate_recipe": [
   "cap_of"
  ],
  "material_array": [
   "RecipeError"
  ],
  "build_regime_columns": [
   "RecipeError"
  ],
  "run_recipe": [
   "RecipeError",
   "build_regime_columns",
   "validate_recipe"
  ],
  "identity_recipe": [],
  "engine_params_from_recipe": [],
  "run_identity": [
   "engine_params_from_recipe",
   "identity_recipe",
   "run_recipe"
  ],
  "legacy_cols_in": [],
  "source_logic": [
   "RecipeError"
  ],
  "attach_recipe_columns": [
   "RecipeError",
   "legacy_cols_in",
   "regime_cols",
   "source_logic"
  ],
  "identity_l1_recipe": [],
  "l1_engine_params": [],
  "run_identity_l1": [
   "attach_recipe_columns",
   "identity_l1_recipe",
   "l1_engine_params",
   "run_recipe"
  ],
  "identity_s1_recipe": [],
  "s1_engine_params": [],
  "run_identity_s1": [
   "attach_recipe_columns",
   "identity_s1_recipe",
   "run_recipe",
   "s1_engine_params"
  ],
  "maker_taker_sync_check": [],
  "e36_maker_taker_behavior_check": [],
  "unordered_iteration_scan": [],
  "selftest": [
   "e36_maker_taker_behavior_check",
   "identity_l1_recipe",
   "identity_recipe",
   "identity_s1_recipe",
   "maker_taker_sync_check",
   "unordered_iteration_scan",
   "validate_recipe"
  ],
  "main": [
   "run_identity",
   "run_identity_l1",
   "run_identity_s1",
   "selftest",
   "validate_recipe"
  ]
 },
 "constants": {
  "NO_CAP": "無制限"
 },
 "cli_flags": []
}
```
