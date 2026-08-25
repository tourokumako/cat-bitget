# 【監査報告】実行器の出口の発火条件を「形ごとの評価」にする設計（97番・`.claude/state/acceptance.md`）cp7

- 監査日: 2026-08-25
- 依頼書: `.claude/audits/inputs/2026-08-25_exit_fire_forms_design_cp7_audit_request.md`（193行・ハッシュ値の先頭16桁 `109726adabfa172e`）
- 監査区分: cp7＝**設計だけの監査・実装前**（実装は1行も入っていない）
- 監査の体制: auditor セッションの CC が Plan サブエージェントを cold start で起こし、**返ってきた所見を auditor 側の CC が実物のコードと自分の再現で1件ずつ裏取りした**（下の「8. 二重の確認の記録」）
- **Verdict: NO-GO**（**方向は正しい＝維持。**設計書の検査を2件→6件に、完成の条件 C1・C3・C6・C8・C11 を書き直して再提出すれば GO に変わる）
- 指摘の件数＝**Critical 2件・Major 5件・Minor 1件**

---

## ★まこさんへ｜3行の結論

1. **設計は「入口の評価器（`_eval_cond`）は正しいので、出口もそこへ寄せる」を前提にしています。その入口の評価器に、向き（side）が `above_strict`／`below_strict` のとき、傾き（slope）と差（diff）を逆向きに評価する不具合が在ります**（`engine_tuner_exec.py`:1700・:1708・:1732）。私が直に呼んで実測しました＝**下がり続ける列で「上向き（strict）」が成立します。**検査（validate_recipe）はこの向きを通します（:783）。**設計書の完成の条件 C1〜C11 を全部 満たしても、この「黙って別物」は残ります**＝97番と同じ型の不具合が、直した先に在ります。
2. **完成の条件 C6（恒等）は「玉の状態だけの枝」しか比べません。**設計が付け替える道（指標の条件＝いま唯一 正しく動いている形 level）を、直す前と後で比べる条件が1つも無い＝**直したことで壊れても気づけません。**
3. **設計書の「実測」の記述のうち、「評価のタイミングは入口と同じ on_close」（worklog §30:443・C11 の前提）は、REVERSE_IND の枝には当てはまりません**（表の placement は resting＝バー内の約定を判定した後に、close 時点の指標で約定の有無を決める・:2369→:2371）。ほかに、数の食い違い1件（「条件12個」→ 実物 11個）と、行番号の1行ずれ1件。

**いま実害は出ていません**（歯止め＝探索の本走をしない・net ゼロ）。**設計書を直せば、実装に進める内容です。**

---

## 1. Step -1 監査対象の型宣言

**文書型（設計書）・実装前。**

| 型 | 対象 | 行数 | 何を見たか |
|---|---|---|---|
| 文書型（監査対象） | `.claude/state/acceptance.md` | 245 | やること4件（§4）／完成の条件 C1〜C11（§5）／§2 の実物の表／SPEC（公開する関数29件） |
| コード型（直す対象・読んだだけ） | `scripts/priority_rebuild/engine_tuner_exec.py` | 4,004 | `FORM_SPEC`・`SIDES`・`_walk`・`_check_cond`・`_vnum`・`_vnum_q`・`_side_cmp`・`_col_array`・`_material_name`・`_eval_cond`・`validate_recipe` の出口の検査・`_collect_fire_cols`・`_exit_fire_ok`・売買ループの resting／on_close の枝・恒等ハーネス・selftest |
| コード型（今回は触らない・読んだだけ） | `scripts/priority_rebuild/engine_tuner_gen.py` | 5,402 | `_EXIT_LEVEL_CONST`・`_state_cond`・`_exit_indicator_cond`・REVERSE_IND／BREAKOUT の組み立て・`_cond_keys`／`needed_qkeys`・案1本を走らせる関数の例外の捕まえ方・T6 |
| データ型 | `.claude/ratchet/exit_families_rules.json`（906行）／機械生成の `exit_families.json` | — | 出口の枝19件の fire・placement・confirm_conditions.rule |
| 文書型（経緯） | `.claude/state/session_worklog_20260825.md` §25〜§27・§30・§31 | — | 97番の実測の逐語・起案 CC が量を出した記録 |

**独立性**＝Plan サブエージェントには依頼書のパス・必読5件・Q1〜Q4・外部検索の要請だけを渡した。起案 CC への確認質問は0回。

---

## 2. Step 0 指摘前提確認

### 2-1. 事実データの verify（auditor 側の CC が自分で実測・2026-08-25）

| ファイル | 依頼書の行数 | 実測 | 依頼書のハッシュ値 | 実測 | 判定 |
|---|---|---|---|---|---|
| `.claude/state/acceptance.md` | 245 | **245** | 99f2056e79d4fd08 | **99f2056e79d4fd08** | ✅ 一致 |
| `engine_tuner_exec.py` | 4,004 | **4004** | 8a606184d6ed4cf8 | **8a606184d6ed4cf8** | ✅ 一致 |
| `engine_tuner_gen.py` | 5,402 | **5402** | 6bf0bc251d9ea521 | **6bf0bc251d9ea521** | ✅ 一致 |
| `exit_families_rules.json` | 906 | **906** | —（依頼書に無し） | f16d8354c51c0696 | ✅ 行数一致 |

**＝依頼書の事実データは全部 実物と一致。前提は成立しています。**git の HEAD＝`68360c6`。リポジトリのファイルは1つも書き換えていません。

### 2-2. spec 文言の verify

- 依頼書「97番の実測」6行（依頼書:84-91）＝`session_worklog_20260825.md` §27（376行〜）の機械の出力と一致（Plan agent が逐語で照合・私は §27 の見出しの実在と、私自身の再現が同じ6行になることで確かめた＝下の Q4）。
- 依頼書「設計の骨子」4件（依頼書:97-100）＝`acceptance.md` §4 の表（:66-69）と一致。
- 依頼書の行番号（exec :98-116・:1334-1387・:1642-1738・:1741-1779・:2036-2052・:2055-2111・呼び出し5か所／gen :1624・:1632・:1656-1726・:2452-2461）＝**全部 実物と一致**（私が Read と grep で確認）。
- 出口の表（`exit_families_rules.json` の `branch_types`）＝**19枝**。指標の条件を持つ枝＝**REVERSE_IND（forms=cross・level・slope・diff・placement=resting）と BREAKOUT（forms=level・slope・diff・placement=on_close）の2件**。玉の状態だけの枝＝**7件**（BEEXIT 1・BESTALE 2・MFEEXIT 2・TIME 1・TIME_DOWN 2・FINSTOP 1・MAECUT_ADDS 2＝**条件 11個**）。発火条件なし＝10件（私がプログラムで数えた）。
- `exit_families.json`:1597 の rule の逐語＝「どの枝にも、確認の条件を 0〜2本 足せる。材料は入口の型の表の部品だけ（禁止3 も同じ）。**閾値は分位。**向きは『出口＝入口の逆』で機械が決める…」＝設計書 §2（:51）の引用と一致。

### 2-3. 承認の状態

- `.claude/state/acceptance.approved` と `design_approved.json` の指紋＝`abff2bce…`。いまの `acceptance.md` の指紋＝`99f2056e…`＝**別物＝未承認**（依頼書の記述と一致）。

---

## 3. 観点 ①〜⑦ ＋ Q1〜Q4 の所見

### 観点 ①〜⑦

| 観点 | 判定 | 根拠（実物の行番号・私の実測） |
|---|---|---|
| ①統計学的妥当性 | **PASS** | 設計は新しい数字を1つも作らない（acceptance.md:91）。実験ゼロ・net の主張ゼロ＝統計の主張が無い。注記＝C2（:78「level と slope の結果が異なるケース」）は、同じ `value.n=5` が level では閾値5・slope では5本前との差＝**意味の違う2つを比べるので必ず異なる＝形が効いた証拠にならない**（判別力ゼロ）。 |
| ②リスク管理 | **FAIL** | C1〜C11 を全部 満たしても「黙って別物」が2件 残る（Critical-1＝strict の反転・Critical-2＝状態の材料の pre の無視。両方とも私が直に呼んで実測）。加えて `not` を出口 fire に置くと `KeyError`（RecipeError ではない）で、案1本を走らせる関数は `RecipeError` と `SampleError` しか捕まえない（gen:2760・docstring:2750「それ以外の例外は、そのまま上へ投げます」）＝探索が丸ごと止まる。歯止め（本走しない・acceptance.md:16）は妥当。 |
| ③認知バイアス | **FAIL** | worklog §30:447「正しく動くのは level だけ＝1/5」は言い過ぎ＝level の状態の道も、欠損の既定 na=pass を無視し（実測⑦）、pre を黙って無視する（実測⑧）。C6（恒等）を**触らない道（状態だけ）**で取り、**付け替える道（指標の level）**では取っていない＝自分の変更が壊し得る所を避けた検収の設計。 |
| ④ソフトウェア工学 | **FAIL**（方向は正） | 方向＝`_eval_cond` への一本化・条件の canonical JSON を鍵にする＝正しい。**好材料**＝いまの `_collect_fire_cols` は鍵を「素の列名」で取る（:2049 `key = _material_name(m, lane)[1]`）ので、同じ列に違う pre を掛けた2条件が衝突して先勝ちする既存バグ（実測⑩＝鍵が `['RSI14__5m']` の1つだけ）を、設計は副次的に直す。**欠け**＝`_ev` の木の歩き（:2106-2110）は `not` を持たない別実装のまま残る（`_eval_tree`:1765 は持つ）＝設計書 §3① が戒める「同じ式を2か所に持つと片方が腐る」をそのまま残す。`FORM_SPEC` の `pre_ok`（:90）を守る validate の行は**0件**。 |
| ⑤再現性 | **FAIL** | C3「ミニ走行で拒否 0」（:79）は種・設定が未指定＝cross の案が1本も生成されなければ自動的に満たされる（生成器が cross を作るのは Stoch%K と %D が両方 pool に在るときだけ・gen:1697）。C6「合成データのミニ走行」（:82）はどの合成データ・どの種かが未指定。C8「--selftest」（:84）はどのファイルの selftest かが未指定（T6・18マス・--lint-provenance は **gen** の selftest＝gen:3841-3877・:4808／TARGET は exec で、exec 自身の selftest は :3491）。 |
| ⑥実行プロセス | **PASS**（1件 注記） | 手順「実物を読む → 量を出す → 設計書 → 監査 → 承認 → 実装」（:15）は守られている。審判整合 D（:107）・H の照合（:108）・疑似シミュ由来の固定値ゼロ（:91）は記載あり。注記＝§3④（:60）「外部の検索は使わない」＝acceptance_checklist B④ の WebSearch 証跡を自ら省いた。外部の一次情報（§4）は、設計書の「入口と同じ on_close」という記述が resting の枝では成り立たないことを直接 指している。 |
| ⑦主エージェントバイアス | **FAIL** | 起案 CC は自分が書いた評価器（`_eval_cond`）を「13形 全部の式が実装済み」（:32）と評価して寄せる決断をしたが、その評価器の slope／slope_avg／diff は `SIDES`（:136）の4値のうち strict 2値を**逆向きに黙って評価する**（:1700・:1708・:1732＝`ok = (d >= th) if c.get("side") == "above" else (d <= th)`）。正しい比較の関数 `_side_cmp`（:1471-1481・strict を持つ）は同じファイルに在るのに、この3行は呼んでいない。自分のコードを「正しい側」として無検証で採用した。 |

### Q1 — 完成の条件は目的を担保するか

**判定＝食い違い（穴）8件**（C2・C3・C6・C8・C11 の記述の不備 5件＋欠けている条件 3件）。

| # | 条件（逐語・行） | ①目的に届くか | ②測れるか | 所見（行番号・実測） |
|---|---|---|---|---|
| C1 | :77「side=above のとき 上がり続ける列 → 成立・下がり続ける列 → 不成立」 | **穴** | 測れる | side=above だけ。`above_strict`／`below_strict` は `_eval_cond` が逆向きに評価する（**実測⑥**＝slope side=above_strict・下がる列で **True**・上がる列で **False**／diff side=above_strict・a−b=−1000 で **True**）。validate は strict を通す（**実測⑨**）。C1 を満たしても strict の slope は黙って別物のまま。 |
| C2 | :78「level と slope の結果が異なるケースが実測で在る（同じ材料・同じ数字）」 | 曖昧 | 測れるが無意味 | level の `n=5` は閾値5、slope の `n=5` は5本前との差＝意味が違うので**必ず異なる**。形が効いた証拠にならない。 |
| C3 | :79「交差を含む案がミニ走行で…拒否されない（拒否 0）」 | 穴 | **曖昧** | 種・設定が無い。生成器が cross を作るのは Stoch%K と %D が両方 pool に在るときだけ（gen:1697）＝作られなければ拒否0は自動成立。前提「cross の案が ≥1本 生成された」を条件に入れる必要がある。 |
| C4 | :80 diff の2本目 | 届く | 測れる | 直呼びで判定できる（**実測③**が基準）。 |
| C5 | :81 candle_dir | 届く | 測れる | 直す前は G6 で落ちる（**実測④**＝「材料の2軸（family×tf）が欠けている: {}」）。 |
| C6 | :82「指標の条件を含まないレシピ（玉の状態の条件だけ）の売買記録が、直す前と後で同じ」 | **穴** | 曖昧 | 設計が付け替える道＝**指標の level**（いま唯一 動いている指標の形）の回帰を検出しない。恒等ハーネス（run_identity_l1／s1／S2）の exit fire の材料は `{"state": "hold_min"}` だけ（exec:2605・grep で他0件）＝そこでも検出しない。合成データの出所・種も未指定。 |
| C7 | :83 band／state×slope の偽レシピが拒否 | 穴 | 測れる | 直す前は両方 素通り（**実測⑨**＝出口の文脈で「通った」）。だが **state＋pre・slope の strict 側・`not`・状態と指標の材料の混在・`ref`** の5件が検査に無い。 |
| C8 | :84「--selftest 全部 pass・T6 ✅・18マス ✅・--lint-provenance 0件」 | 届く | **曖昧** | T6（gen:3841-3877）・--lint-provenance（gen:4808）は `engine_tuner_gen.py --selftest`。TARGET の exec には別の selftest（exec:3491・:3712-3714 に出口の呼び出し2件）。両方を明記する必要がある。 |
| C9 | :85 H2 の印・G2 の印 | 届く（限定） | 測れる | ツール実在（`leak_causality_diag.py`・`gen_signal_families.py`）。ただし打ち切り再現（1-c）は**同じバーの中の順序**（バー内の約定 vs close の条件）を検出できない＝C11 の穴（下）を C9 は補わない。 |
| C10 | :86 verify_design_contract --diff | 届く | 測れる | ツール実在。SPEC（:161-245）は公開する関数29件＝機械出力と一致（worklog §31:458）。 |
| C11 | :87「新しい未来参照ゼロ＝cross は i-1 と i…`.shift(-`・`center=True` を新しく書かない」 | **穴** | grep で測れるが不足 | 配列方式は index i を引くだけ＝**新しい**未来参照は増えない（正）。だが REVERSE_IND は resting（rules.json placement.kind="resting"・gen:1880）＝売買ループは `hit = (l[i] <= lvl)`（バー内の約定・:2369）を判定した**あと**に `_exit_fire_ok`（:2371）で close[i] 時点の指標（配列の i 番目）と `unreal_pct`（:2087 `c = float(df["close"].iloc[i])`）を見て約定の有無を決める＝**約定より後の情報で約定を取り消す**。既存の作りで設計が新設したものではないが、worklog §30:443「評価のタイミングは入口と同じ on_close」は BREAKOUT（on_close）にしか当てはまらない。 |

**欠けている条件（3件）**＝(m1) slope／slope_avg／diff の strict 側の扱い（拒否か正しい評価か）／(m2) `not` を含む出口 fire の扱い（拒否か評価か）／(m3) 状態の材料に pre が付いたときの扱い（拒否）。3件とも「validate が通す × 実行が黙って別物」の組み合わせで、私の直呼びで実測済み（⑤⑥⑧⑨）。

### Q2 — 設計の方式に意味を変える穴が無いか（攻撃者の目）

**判定＝食い違い 6件**（設計が新設する穴 2件・設計が既存の穴を持ち込む 3件・設計が直す既存バグ 1件＝好材料）。

| 項 | 確認結果 | 逐語・行 |
|---|---|---|
| (a) qtable の鍵 | **一致（限定）**。`needed_qkeys` は出口の枝の fire も歩く（gen:2458-2461「for b in (r.get("exits") or []): if b.get("fire"): … conds += _tree_conds(b["fire"])」）。鍵を作る `_cond_keys`（gen:2404-2450）が持つ枝＝level・ref の挟み・band・diff・cross(列1本) の threshold_q だけ。**slope／slope_avg の閾値 `th` の鍵（実行器は `Δ{n}:{akey}`＝exec:1699）を作る枝が無い**（gen 全文で「Δ」**0件**・私が数えた）＝出口でも入口でも slope の閾値に分位は使えない。設計書 §7(a)（:97）「縛りの理由は今回の直しで消える」は level にだけ当てはまる。 | gen:2425-2450／exec:1699 |
| (b) 欠損の既定 | **指標の道は入口と一致**（**実測⑦**＝指標 NaN・na=pass → True）。**状態の道は na=pass を無視**（**実測⑦**＝mfe_pct=NaN・na=pass → False。exec:2094-2096 に isfinite の検査が無く :2105 で NaN を比較）＝設計は「1文字も変えない」（:67）ので残る。cross・candle_dir は NaN で常に False（exec:1719-1724 `fin &`）＝入口と同じ。 | exec:2094-2105・:1685・:1719 |
| (c) 評価のタイミング | 配列方式に**新しい**未来参照は無い（i 番目を引くだけ・cross は :1717 `np.roll(a, 1)`＝i-1 と i・:1718 で pa[0]=NaN）。**しかし REVERSE_IND（resting）は約定（:2369）の後に close[i] の条件で約定を取り消す作り**（:2371）。設計はこれを「入口と同じ on_close」と書いている（worklog §30:443）＝**主張が不正確**。 | exec:2361-2371・:2087 |
| (d) 鍵の衝突 | canonical JSON は決定的。印（`_num_src`・`_lineage_src`）は `strip_marks`（gen:813-816）が実行器に渡す直前と validate の前に外す＝鍵に印は入らない。同じ条件が2枝に現れても `_eval_cond` は枝に依存しない（引数に lot も枝も無い・:1642）＝同じ配列で正しい。**設計が直す既存バグ**＝いまは鍵が素の列名（:2049）なので、同じ列に違う pre を掛けた2条件は先勝ち（**実測⑩**＝2条件で鍵が `['RSI14__5m']` の1つ）。**新設の穴**＝材料に state と指標が混在する条件（mats[0] が指標・mats[1] が state）は §4-1「state を含まない」に当たらず、§4-3(b)「材料に state」に当たる＝設計書の中で行き先が決まっていない。実装で `_eval_cond` に行けば `_col_array` が「入口の材料に使えない種別: state」（:1601）で止まる＝fail-closed だが理由の文が誤解を招く。 | gen:813-816／exec:2049・:1601 |
| (e) scope との組み合わせ | **一致**。scope（adds・ceil_type・trend_caught・hold_min）は fire の前に評価（:2058-2075）で設計は触らない。while_waiting の道（:2301）にも同じ fire_cols が渡る。 | exec:2058-2075・:2301 |
| 追加1（新設の穴・Minor） | `ref`（連動する閾値）が出口で使えるようになる。`_eval_cond` は ctx=(df, geo, lane) を必ず作る（:1678）→ 出口の指標の条件を `_eval_cond` に通すと `_vnum_q` の「出口の枝では使えない」（:1501・:1505-1507）が効かなくなる。 | exec:1678・:1501-1507 |
| 追加2（持ち込む穴・**Critical-1**） | strict 側の反転。**実測⑥**＝`_eval_cond` slope side=above_strict・下がる列 → **True**／diff side=above_strict・a−b=−1000 → **True**。原因＝:1700「ok = (d >= th) if c.get("side") == "above" else (d <= th)」（:1708・:1732 も同型）。validate は `SIDES` 4値を通す（:783・**実測⑨**）。**露出の実測**＝生成器は strict を **0件** 作る（gen 全文 grep）／恒等レシピ `recipes/identity_s1_legacy.json` に strict が3件 在るが**全部 level**（level は `_side_cmp` を通る＝正しい）＝**いま作られる案で反転が起きるものは0件。**起きるのは、手書きのレシピと、探索が slope／diff に strict を出すようになった瞬間。 | exec:1700・:1708・:1732・:783・:136・:1471 |
| 追加3（持ち込む穴・**Critical-2**） | 状態の材料の pre が黙って無視される。**実測⑧**＝`{"state":"hold_min","pre":{"op":"ts_max","n":20}}` は出口の文脈の `_check_cond` を通り、実行は pre 無しと同じ結果（両方 True）。原因＝`_ev` の状態の道は `m.get("state")` だけ読む（:2094-2096）。`pre_ok`（FORM_SPEC:90）を守る validate の行は0件。露出＝生成器の `_state_cond`（gen:1632）は pre を付けない＝手書きのレシピの道。 | exec:2094-2096・:90・:853-859 |
| 追加4（持ち込む穴・**Major**） | `not` を出口 fire に置くと validate の `_walk` は通す（:255-262・**実測⑤**＝条件1件を返す）が、`_ev` は not を持たず `node["if"]` で **KeyError 'if'**（:2110・**実測⑤**）。案1本を走らせる関数は `except (ex.RecipeError, SampleError)`（gen:2760）＝KeyError は上へ投げる（docstring:2750）＝**探索が丸ごと止まる**。露出＝生成器が `not` を作るのは場面の判定の束（gen:2098）だけ＝出口では作らない＝手書きのレシピの道。 | exec:255-262・:2106-2110／gen:2750-2760 |

### Q3 — 設計書と実物は一致しているか

**判定＝行番号・関数一覧・表の数は一致（16か所）／食い違い 9件。**

一致（私が Read／grep で確認）＝FORM_SPEC :98-116／exit_ok の注記 :92／`_eval_cond` :1642-1738／`_eval_tree` :1741-1779／validate の出口の検査 :1334-1387／fire の検査 :1359-1363／`_collect_fire_cols` :2036-2052／呼び出し :2174／`_exit_fire_ok` :2055-2111／`_ev` :2091-2105／売買ループの呼び出し5か所／自己テスト2か所 :3712・:3714／gen `_state_cond` :1632／`_exit_indicator_cond` :1656／`_EXIT_LEVEL_CONST` :1624／SPEC の公開する関数29件・定数1件（NO_CAP）。

| # | 設計書の記述（逐語・行） | 実物 | 種別 |
|---|---|---|---|
| 1 | worklog §30:443「評価のタイミングは入口と同じ on_close」／acceptance.md:87 C11 の前提 | REVERSE_IND は **resting**（rules.json placement.kind="resting"・gen:1880）＝バー内の約定の後に close[i] で判定（exec:2361-2371） | 実物との食い違い（Major） |
| 2 | :50「玉の状態だけの枝＝7枝（条件12個・全部 level）」／worklog:448 も同じ | 状態だけの7枝の条件は **11個**（私がプログラムで数えた）。12 になるのは REVERSE_IND の状態の条件（unreal_pct）を足したとき | 数の食い違い（Minor） |
| 3 | :32「13形 全部の式が実装済み」 | 形は13で一致。だが `SIDES`（:136）の strict 2値は slope／slope_avg／diff で未実装（:1700・:1708・:1732） | 言い過ぎ（Critical-1 の根） |
| 4 | :46「needed_qkeys :2452-2461」 vs worklog:442「:2458-2461」 | 出口を歩く行は :2456-2461（for は :2458）。同じ塊を指す | 内部の不一致（Minor） |
| 5 | :97 §7(a)「縛りの理由（「実行器が分位を解けない」）は今回の直しで消える」 | level・band・diff・cross(1本) だけ。slope の th の鍵は生成器に無い（gen「Δ」0件） | 範囲が広すぎる（Major） |
| 6 | :84 C8「--selftest 全部 pass・T6 ✅・18マス ✅」 | T6 は gen の selftest（gen:3841-3877）。TARGET の exec は別の selftest（:3491） | 曖昧（Major） |
| 7 | worklog §30:447「正しく動くのは level だけ＝1/5」 | level の状態の道は na=pass を無視（実測⑦）・pre を無視（実測⑧） | 言い過ぎ（Major） |
| 8 | :66 §4-1「材料に state を含まない条件」／:68 §4-3(b)「材料に state」 | 材料2本で state と指標が混在する条件の行き先が設計書の中に無い | 内部の抜け（Minor） |
| 9 | :45「:1711-1714 のコメント」 | 該当コメントは gen:1712-1715（:1711 は「── 水準を見る形（level）──」の見出し行） | 1行ずれ（Trivial） |

### Q4 — 97番を独立に再現せよ

**直す前の実行器で `_exit_fire_ok` を直に呼んだ（auditor 側の CC 自身が走らせた・ヒアドキュメント・.py を作らない・環境変数なし・hook に止められなかった）。**材料＝`{"family":"RSI","param":[14],"tf":"5m"}`（`_material_name` の出力 `('col', 'RSI14__5m')`）。列2通り＝50→90（上がる）と 90→50（下がる）・60バー。**機械の出力（逐語）**:

```
--- ① 直す前の _exit_fire_ok：slope が向きを見るか（level と比較・n=5 と n=95）---
  form=slope side=above n=5 上がる列(最後90) -> 成立: True
  form=slope side=above n=5 下がる列(最後50) -> 成立: True
  form=level side=above n=5 上がる列(最後90) -> 成立: True
  form=level side=above n=5 下がる列(最後50) -> 成立: True
  form=slope side=above n=95 上がる列(最後90) -> 成立: False
  form=slope side=above n=95 下がる列(最後50) -> 成立: False
--- ② cross（直す前）---
  cross(RSI14×RSI7, up) -> 例外 RecipeError: [実行器] 値を解決できない（分位は解決表＝qtable が要る）: {'direction': 'up'}
--- ③ diff の2本目（直す前）---
  diff RSI14(最後90) - RSI7(=0.0) >= 5 -> 成立: True
  diff RSI14(最後90) - RSI7(=1000.0) >= 5 -> 成立: True
--- ④ candle_dir（直す前）---
  candle_dir bull -> 例外 RecipeError: [レシピ拒否 G6] 材料の2軸（family×tf）が欠けている: {}（数字は family によって 0〜3 個）
```

①②③＝**97番を独立に再現**（依頼書の表と同じ結果・設計書の表は写していない・Plan agent の走行とも一致）。④＝設計書 C5 の「材料なしで列引きに落ちて評価不能」（:81）も再現。

**追加で確かめた点（同じ走行・逐語）**:

```
--- ⑥ 入口の評価器 _eval_cond の strict 側（slope・diff）---
  _eval_cond slope side=above          下がる列(最終バー)／上がる列 -> 成立: (False, True)
  _eval_cond slope side=above_strict   下がる列(最終バー)／上がる列 -> 成立: (True, False)   ← 逆
  _eval_cond slope side=below          下がる列(最終バー)／上がる列 -> 成立: (True, False)
  _eval_cond slope side=below_strict   下がる列(最終バー)／上がる列 -> 成立: (True, False)
  _eval_cond diff side=above a-b=-1000（本来 False） -> 成立: False
  _eval_cond diff side=above_strict a-b=-1000（本来 False） -> 成立: True   ← 逆
--- ⑧ 状態の材料に pre を付けたとき（validate は出口の文脈 where="exit枝TEST" で呼んだ）---
  validate _check_cond(state+pre ts_max) -> 通った
  実行 pre あり (hold_min=295) -> 成立: True
  実行 pre なし (hold_min=295) -> 成立: True
--- ⑤ not を出口 fire に置く ---
  validate _walk(not) の条件の数 -> 1
  実行 _exit_fire_ok(not) -> 例外 KeyError: 'if'
--- ⑦ 欠損の既定 na=pass：状態 vs 指標 ---
  状態 mfe_pct=NaN na=pass -> 成立: False
  指標 RSI=NaN na=pass -> 成立: True
--- ⑨ validate の出口の検査（直す前・出口の文脈）---
  state+pre(ts_max) -> 通った ／ state×slope -> 通った ／ band in exit -> 通った ／ slope side=above_strict -> 通った ／ slope(pre_ok=False)+pre -> 通った
--- ⑩ 同じ列に違う pre を掛けた2条件の鍵（いまの _collect_fire_cols）---
  fire_cols の鍵 -> ['RSI14__5m']   ← 2条件で鍵が1つ＝先勝ち
```

**C6 は回帰の検出に不十分**（断言）。理由＝(1) 設計が付け替える道は「指標の条件」で、C6 はその道を1本も通らない。(2) いま唯一 正しく動く指標の形＝level（例＝BREAKOUT の ADX≥定数）の売買記録が直す前後で一致することを、C1〜C11 のどれも確かめない。(3) 恒等ハーネス（run_identity_l1／s1／S2）の exit fire の材料は `state` だけ（exec:2605・grep 他0件）＝ここでも検出しない。(4) 「合成データ」の出所と種が未指定＝同じ走行を再現できない。

---

## 4. 外部検索結果サマリー（Plan サブエージェントが WebSearch／WebFetch で実施・auditor 側の CC は URL を開き直していない）

クエリ1: `backtesting exit signal evaluation vectorized precomputed boolean series vs per-bar loop correctness pitfalls`
クエリ2: `crossover signal implementation lookahead bias previous bar comparison NaN handling`
クエリ3: `backtest limit order fill intrabar confirmation using bar close look-ahead bias event-driven vs vectorized`
クエリ4: `vectorbt crossed_above NaN first bar behavior pandas shift(1) crossover definition`

| # | 発見 | 本設計への当てはめ | 出典 |
|---|---|---|---|
| 1 | ベクトル方式（事前の真偽配列）は速いが、「生の合図」と「実際に執行された合図」を分けて扱わないと誤る＝出口の合図は建玉が在るときだけ意味を持つ | 設計は「配列の i 番目を引く」を玉ごとの scope・状態の判定の**後**に置く（exec:2058-2078 の順序を保つ）＝この落とし穴は回避している | IBKR「A Practical Breakdown of Vector-Based vs Event-Based Backtesting」（interactivebrokers.com/campus/ibkr-quant-news/）／Coriva vectorbt tutorial（coriva.eu.org/en/vectorbt-tutorial/） |
| 2 | 経路依存の出口（バー内の高値・安値を使うトレーリング等）と指値・逆指値の約定は、1バー＝1事象の事前計算では忠実に再現できない | REVERSE_IND（resting・fill=profit）は「バー内の約定」と「close の指標条件」を混ぜている（exec:2369→:2371）＝この文献が名指しする型 | 同上 IBKR |
| 3 | 「同じバーの close で合図を作り、同じバーで約定させる」＝same-bar execution が典型の look-ahead。直し方＝合図を1本ずらす（shift(1)）か次バー始値で約定 | 出口 on_close の枝（:2386→:2397 `c[i]` で記録）は既存の作り・設計は変えない。resting の枝は「約定がバー内・条件が close」＝同じ型 | ForexCodes「Same-Bar Execution: The Silent Python Backtest Bug」（forexcodes.com/learn/same-bar-execution-python） |
| 4 | 交差の堅い定義＝前バー（t−1）での上下関係と当バー（t）での上下関係を両方 使う | `_eval_cond` cross（:1717-1723）は `pa<=pb & a>b`＝この定義と一致 | trading-strategies.academy「Prior Bar Close in Pine Script」（/archives/2881） |
| 5 | vectorbt の crossed_above は NaN に堅牢・**最初のバーは False**（前バーが無い） | `_eval_cond` cross は :1718 で pa[0]=NaN → False、:1719 `fin` で NaN は False＝業界実装と同じ。na=pass を cross に効かせない現行の意味論は妥当 | vectorbt docs（vectorbt.dev/api/indicators/basic/・/getting-started/features/） |
| 6 | backtesting.py の `crossover(s1, s2)`＝「s1 が s2 を**ちょうど今**上抜けたら True」＝直近2値だけを見る | 設計の「cross は i-1 と i（過去だけ）」（:87）と同じ定義 | backtesting.py lib API（kernc.github.io/backtesting.py/doc/backtesting/lib.html） |
| 7 | 移動平均などの窓は先頭 n 本が NaN＝欠損の既定を明示して扱う | `_eval_cond` slope は :1698 `d[:n]=nan` → na=fail 既定。状態の道は NaN を isfinite で見ない（:2094-2105）＝既定が2通り在る（Q2(b)） | Medium「Simple Moving Average Crossover Strategy Using Python」 |
| 8 | 事象駆動＝「データ受信→合図→発注→約定」の順に処理するので look-ahead が構造的に入らない | 本実行器はループ内で「約定判定→条件判定」の順（:2369→:2371）＝事象の順が逆。設計の範囲外だが、C11 の「新しい未来参照ゼロ」だけでは H2 の担保にならない根拠 | QuantStart「Event-Driven Backtesting with Python Part I」 |

（Plan agent の注記＝WebFetch 403＝insiderfinance.io・IBKR 本文。要旨は検索結果の抜粋から。）

---

## 5. 総合判定

**Verdict: NO-GO**（このままの設計書では承認しない。**方向は正しい＝維持。**§4 の検査を2件→6件に、§5 の C1・C3・C6・C8・C11 を書き直して再提出すれば GO に変わる）。

根拠:
1. 目的（:6・ARC の狙い「黙って別物になる評価をコードから無くす」）に対し、**C1〜C11 を全部 満たしても黙って別物が2件 残る**＝slope／slope_avg／diff の strict 側の反転（実測⑥・exec:1700／:1708／:1732）と、状態の材料の pre の無視（実測⑧・exec:2094-2096）。どちらも validate が通す（実測⑨）。★露出はいま0件（生成器は strict も pre も作らない）だが、97番と同じ「検査が通す × 実行が黙って別物」の型を、直した先に残す設計は目的に届いていない。
2. **回帰の検収が付け替える道を通らない**＝C6 は状態だけ・恒等ハーネスも状態だけ（exec:2605）。いま正しく動く唯一の指標の形（level）が直した後も同じ売買記録を出す証拠が、設計のどこにも無い。
3. `not` で**探索が丸ごと止まる**（KeyError・gen:2760 は RecipeError と SampleError しか捕まえない）。
4. 設計書の主張「評価のタイミングは入口と同じ on_close」（worklog §30:443）が REVERSE_IND（resting・gen:1880）で成り立たない。既存の作りで設計の責任ではないが、C11 が「新しい」未来参照だけを見る以上、まこさんが H2 を担保されたと誤読する文になっている。
5. 好材料（維持すべき点）＝`_eval_cond` への一本化は、いまの `_collect_fire_cols` の「鍵＝素の列名」（:2049）による pre の衝突バグ（実測⑩）を副次的に直す。canonical JSON は印が外れた後に作られる（gen:813-816）ので鍵は安定。qtable を渡す下地（gen:2458-2461・exec:2115）は在る。

---

## 6. 改善方向性

| 優先 | # | 提案（設計書に足す・変える所） | 根拠の行 |
|---|---|---|---|
| **Critical** | 1 | §4-3 に検査 (c) を足す＝出口の fire で `form ∈ {slope, slope_avg, diff}` の `side` が `above_strict`／`below_strict` なら拒否（fail-closed）。C1 に「side=below の逆・strict は拒否される」の実測を足す。**入口にも同じ穴が在る**（同じ3行）ので **next_step §6 に新番号で登録**（:1700・:1708・:1732 を `_side_cmp`（:1471）に寄せる直しは入口の恒等が要る＝別の1変更） | exec:1700・:1708・:1732・:783・:136・:1471 |
| **Critical** | 2 | §4-3 に検査 (d) を足す＝材料が `state` の条件に `pre` が在れば拒否。加えて `pre_ok=False` の形（slope・cross・diff ほか）の材料に `pre` が在れば拒否（FORM_SPEC:90 を validate に接続）。C7 に両方の偽レシピを足す | exec:2094-2096・:90・:853-859 |
| **Major** | 3 | `_ev` の木の歩きに `not` を足す（`if "not" in node: return not _ev(node["not"])`）か、validate で出口の fire の `not` を拒否する。どちらかを §4-2 に明記。C7 に `not` の偽レシピを足す | exec:2106-2110・:255-262／gen:2760 |
| **Major** | 4 | C6 を書き直す＝(i) 指標の level を持つ出口の枝（BREAKOUT on_close＝ADX≥定数、REVERSE_IND resting）を含むレシピを、固定の種の合成データで直す前後 走らせ、売買記録のハッシュ値が一致 (ii) `--identity`（L1／S1／S2）のハッシュ値の一致 (iii) 合成データの生成関数と種を条件に書く | exec:2605・gen:1877-1892 |
| **Major** | 5 | C8 を「`engine_tuner_exec.py --selftest` 全部 pass ＋ `engine_tuner_gen.py --selftest` 全部 pass（T6 ✅・18マス ✅）＋ `--lint-provenance` 0件」に分ける。C3 に種・設定（§25 のミニ走行と同じ）と前提「cross の案 ≥1本 生成」を書く | gen:3841-3877・:4808／exec:3491 |
| **Major** | 6 | C11／worklog §30:443 の文を直す＝「配列方式は新しい未来参照を増やさない。REVERSE_IND（resting）は既存の作りで、バー内の約定の後に close[i] の条件で約定を取り消す（:2369→:2371）。この順序は本設計の範囲外＝next_step §6 に新番号で登録」。「入口と同じ on_close」と書かない | exec:2361-2371・:2087 |
| **Major** | 7 | 「実行器が qtable を受ければ分位が解ける」（§7(a)）を機械で確かめる条件を足す＝直呼びで `{"threshold_q":"q50"}` の出口 level 条件に1鍵の qtable を渡して成立を実測。§7(a) の範囲を「level・band・diff・cross(1本)」に限定し、slope の th の鍵が無いこと（gen「Δ」0件）を next_step に登録 | gen:2425-2450／exec:1699 |
| Minor | 8 | §4-3 に「材料に state と指標が混在する条件は拒否（理由文を明示）」「出口の fire で `ref` は拒否」を足す（`_vnum_q`:1501 の docstring と整合）。§2 の「条件12個」を11に直す。:45 の行番号を :1712-1715 に直す。canonical JSON は `json.dumps(..., sort_keys=True, ensure_ascii=False)` に加え、numpy の型が混じったら明示の RecipeError で止める | exec:1501-1507・:1601／gen:1712-1715 |

---

## 7. CC プロセス欠陥対策（cc_role §1.4.6 への追記案・3件）

1. **「付け替える道」の恒等を必須にする**（§1.4.6.1 の16番の隣に17番）＝既存の評価の道を別の実装へ付け替える設計書は、完成の条件に「付け替えられる側の道（いま正しく動いている形）で、直す前後の機械出力が一致する」条件を最低1件 含める。「触らない道の恒等」だけでは検収にならない（本件 C6 の型）。
2. **性質表と検査の対応を機械で出す**＝`FORM_SPEC` の欄（pre_ok・needs_side・exit_ok・state_free…）ごとに、それを守る validate の行番号を機械で列挙し、対応する検査が無い欄を「守られていない性質」として設計書に貼る（本件＝pre_ok は0件・SIDES の strict は評価器が未対応）。手書きの「13形 全部 実装済み」を許さない。
3. **自分のコードを「正しい側」と書くときは反証の直呼びを添える**＝設計書が「入口の評価器は正しいので寄せる」と書くときは、寄せる先の評価器を SIDES×形の全組み合わせで直呼びした機械の出力を §2 に貼る（本件は side=above だけを見て strict を見落とした・実測⑥）。§3④「外部の検索は使わない」の宣言は、外部の一次情報が設計の主張（on_close）を直接 否定する本件の実例をもって、acceptance_checklist B④ の省略を認めない運用に戻す。

---

## 8. 二重の確認の記録（auditor 側の CC が Plan サブエージェントの所見を実物で裏取りした結果）

| Plan agent の主張 | 私が測ったこと | 結果 |
|---|---|---|
| exec:1700・:1708・:1732 が strict を逆向きに評価 | 3行を Read（`ok = (d >= th) if c.get("side") == "above" else (d <= th)`）＋ `_eval_cond` を4つの side で直呼び（実測⑥） | ✅ 一致。above_strict・下がる列で True |
| validate は SIDES 4値を通す（:783） | :783 を Read＋出口の文脈で `_check_cond` 直呼び（実測⑨） | ✅ 一致 |
| `_ev` は state の名前しか読まず pre を無視（:2094-2096） | :2091-2110 を Read＋pre あり／なしで直呼び（実測⑧） | ✅ 一致（両方 True） |
| `_ev` に `not` が無く KeyError（:2110） | Read＋直呼び（実測⑤） | ✅ 一致（KeyError: 'if'） |
| gen:2760 は「except ex.RecipeError しか捕まえない」 | :2740-2762 を出力 | **⚠️ 訂正**＝実物は `except (ex.RecipeError, SampleError)`。**結論は同じ**（KeyError は通り抜ける・docstring:2750「それ以外の例外は、そのまま上へ投げます」） |
| resting の枝は約定の後に fire を判定（:2369→:2371） | :2355-2400 を Read | ✅ 一致 |
| 恒等ハーネスの exit fire の材料は hold_min だけ（:2605） | `grep '"state": "'` | ✅ 一致（:2605 の1件・:3625 は別用途） |
| `_cond_keys` に slope の鍵が無い・gen に「Δ」0件 | :2404-2465 を Read＋`grep -c "Δ"` | ✅ 一致（0件） |
| 状態だけの枝の条件＝11個 | rules.json をプログラムで数えた | ✅ 一致（7枝・11個。REVERSE_IND の state 項目1個を足すと12） |
| 生成器は出口に `not` を作らない | `grep '"not"'`＝:2098 は場面の判定の束 | ✅ 一致 |
| 鍵の衝突（:2049 素の列名） | 違う pre の2条件で `_collect_fire_cols` 直呼び（実測⑩） | ✅ 一致（鍵1つ） |
| 欠損の既定が状態と指標で違う | 直呼び（実測⑦） | ✅ 一致 |
| 依頼書の行番号（exec・gen）が全部 実物と一致 | Read／grep | ✅ 一致（gen:1624・:1632・:1656・:2396 の定義行も一致） |
| T6 は gen の selftest（:3841-3877） | grep | ✅ 一致（:4808 に --lint-provenance） |
| strict の露出（★私が足した実測） | gen 全文 grep＝0件／`recipes/*.json` grep＝identity_s1_legacy.json に3件・全部 level | いま作られる案で反転が起きるものは0件 |
| 外部検索の8件 | — | **開き直していない**（Plan agent の要約のまま） |

**私の側の誤り1件（訂正済み）**＝最初、`_check_cond` を入口の文脈（`where="test"`）で呼び、状態の材料が「出口 fire の材料専用」で止まった。validate は出口を `where=f"exit枝{nm}"`（:1363）で渡し、:858 が `where.startswith("exit")` で見分ける。出口の文脈で呼び直したら5通り全部「通った」＝Plan agent の所見どおり。

---

## 9. 限界（正直に）

- **直した後のコードは存在しない**。設計どおりに実装したときの挙動（配列方式のタイミング・鍵の安定）は、実物のコードを静的に読んだ判定。実測は「直す前」だけ。
- 外部検索の本文は Plan agent の要約。URL は開き直していない。
- 設計書の中の「意味の矛盾」は人が読んだ範囲＝機械で拾えるのは行番号・数・関数名の一致まで。
- 月次 NET ≥ $1,900 の達成可能性は対象外（本監査は設計の監査）。
