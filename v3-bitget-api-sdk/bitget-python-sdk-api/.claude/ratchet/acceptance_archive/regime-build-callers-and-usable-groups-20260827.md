# acceptance.md — 場面の判定の束が外から呼ぶ道で1本も組めない件（114番）を直す＝原因A・原因B（監査 第4要素 Major 3・Major 4）

<!-- ARC order=69 iter="regime-build-callers-and-usable-groups-20260827" 前提="fast-mode ON・実験ゼロ・売買記録0本・場面の判定の束は外から呼ぶ道で 0/96（68回目・worklog 20260827 §41）・監査 第4要素（NO-GO）が原因A・原因B を実物一致と認定" 採否="未" base_csv="none" score_csv="none" train_csv="none" 狙い="engine_tuner が場面の判定（レンジ）の束を外から呼ぶ道（診断・ダッシュボード）でも組めるようにする＝M2-10・M2-11 へ進む道を開く" 内容="①印（_num_src）を外してから検査を呼ぶ包みを公開し、外から呼ぶ3本をそれに揃える ②範囲のどの数字でも禁止3（標本不足）の組を、成績表の順位に数えない（範囲を全部 走査して判定＝乱数に依らない）" 方法="わざと壊して止まるか試すテスト3件（外の道・呼び出し元の走査・使えない組を数えない）＋外から呼ぶ道で束を組む実測（0/96 が何本になるか）＋恒等3本＋H2・G2 の印の取り直し" -->

TARGET: scripts/priority_rebuild/engine_tuner_gen.py
TARGET: scripts/priority_rebuild/regime_r9_diag.py
TARGET: scripts/priority_rebuild/engine_tuner_fire_diag.py

**★2026-08-27 の追記（承認のあと）**＝上の TARGET の2行目・3行目を足した。理由＝7.1 の「触るファイル」に書いてあった外から呼ぶ2本（1行ずつの書き換え）が、受け入れ条件ゲート（`require_acceptance_before_impl`）で「TARGET と一致しない」と止まったため。**中身（やること・完成の条件）は1文字も変えていない。**指紋が変わるので再承認が要る。

BASEUP_EXEMPT（net 不変の道具の直し・売買のロジックに触らない・2026-06-22 まこさん承認の免除の型）

**出どころ**＝まこさん決定 2026-08-27（逐語）「M2-10 を止めて、束が組めない件を先に直す」「『原因はこれで、こう直す』を実測つきで出した後、直す前に監査に出す」→ 監査 `.claude/audits/2026-08-27_regime_element04_audit_report.md`（Verdict NO-GO）の §6 **Major 3**（外部呼び出し用の検証の包みを1本にする・外の道の自己テスト）と **Major 4**（範囲内に使える数字が1つも無い組を順位から除外する）。**監査は2件とも「依頼書の案と同方向」「設計は妥当」と書いている**（同 §6 の 3・4）。

---

## §1 何を作るか（1文）

**案を作るプログラム（`engine_tuner_gen.py`）が組んだ場面の判定の束を、外のプログラム（診断・ダッシュボード）が検査に通しても落ちないようにし、成績表の順位から「範囲のどの数字でも標本不足で使えない組」を外す。**

---

## §2 いまどうなっているか（実物・69回目に Read tool で開いた行）

| # | 何 | 実物 |
|---|---|---|
| 1 | 案を作るプログラムは、数字を引くたびに「出どころの印」（`_num_src` ほか4種＝`_MARK_KEYS`・`engine_tuner_gen.py`:357）を付け、**印を付けたまま案を返す**（同 :2270 の逐語「★印は外さずに返す（C-7＝保存する案に出どころを残す）。実行器に渡す直前（run_trial）で外す」） | 59回目（2026-08-25・78番の直し）から |
| 2 | 生成器の中で検査を呼ぶ所は、印を外してから渡す（`_vr`＝同 :807-810・`strip_marks`＝同 :813-821） | 自己テストはこの道を通るので通り続けた |
| 3 | **外から検査を呼ぶ所は、印を外さずに `ex.validate_recipe(r, limits=lim)` を直に呼ぶ** | `regime_r9_diag.py`:250 ／ `build_regime_from_tuner.py`:192 ／ `engine_tuner_fire_diag.py`:392（3本・`grep -rn 'validate_recipe('` で機械で数えた） |
| 4 | だから検査 G5 が「hysteresis の value に書けるのは n だけ（['_num_src']）」で拒否する＝**0/96**（68回目・worklog 20260827 §41）。印を外して検査すると **36/120** | 原因A |
| 5 | 成績表を「種類×時間足」でまとめた順位（`ranked_groups`・同 :1977-2004）の上位に、**範囲のどの数字でも禁止3（標本不足）に当たる組**が混ざる＝env の順位1・3・4・6・7（stdev%×1d・kurtosis×1d・VWMACDシグナル%×1d・TSI×1d・TSIシグナル×1d）が **0/200** | 原因B（68回目の実測） |
| 6 | `_ranked_material_at`（同 :2007-2041）は、その組で10回 引いて全部だめなら **その案を諦める**（同 :2034-2036 の逐語「★次の組へ飛ばさない＝飛ばすと種によって指標が変わる（『1位から順』が乱数に依る）。この案だけ作れない」）＝意図した作り | 順位1・3・4・6・7 に当たる案は必ず落ちる |

**★監査が Step 0 で「実物一致」と認めた2件が、この §2 の 3〜6 です。**

---

## §3 深掘り4点

### ① 真因（root cause）

**真因は2つ、別々です。**

- **原因A**＝「印を外してから検査に渡す」という決まりが、**生成器の中の包み（`_vr`）にしか無く、外から呼ぶ側に渡す公開の道が無かった。**だから外から呼ぶ3本は、印が入る前の呼び方（`ex.validate_recipe` を直に）のまま残り、59回目に印が入った瞬間に黙って壊れた。**同じ判定が2か所に在って片方だけ直した型**（89番・恒久の決まり59番）。
- **原因B**＝順位の表は「列ごと」（期間を含む）だが、`ranked_groups` が種類×時間足でまとめて中央値を取るので、**その組の中に範囲で引ける数字が1つも無くても順位に残る。**`_ranked_material_at` は「その組で引けるか」を10回の乱数でしか確かめない。

### ② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか）

**★売買の期待値には、この設計は1つも触りません。非該当です。**売買記録を1本も作らず、探索の本走もしません。

**代わりに、この設計が動かす数字を書きます。**

| 何 | 直す前（実測） | 直した後（★数字は機械が出す・私は決めない） |
|---|---|---|
| 外から呼ぶ道で組めた束（`regime_r9_diag.py --build 20 --no-trades`） | **0/96**（順位0〜15 × 各6回） | 0 でない本数（完成の条件 2） |
| 印を外すだけで組める束 | 36/120 | 原因B も直すので、これ以上（順位1・3・4・6・7 の分が使える組へ回る） |
| env の順位で「範囲のどの数字でも禁止3」の組 | **5組**（0/200） | **0組**（順位に数えない） |
| 外から検査を直に呼ぶ所 | **3か所** | **0か所**（番人 T31 が走査で数える） |

### ③ root か symptom か

**root です。**「外から呼ぶ側が印を外し忘れる」道そのものを閉じ（公開の包みに揃え、直に呼ぶ所を番人が数える）、「引けない組が順位に残る」道そのものを閉じる（範囲を全部 走査して判定する）からです。
**symptom の直し方**＝`regime_r9_diag.py` の1行だけ直す。**それでは `build_regime_from_tuner.py` と `engine_tuner_fire_diag.py` が同じ型のまま残り、次に外から呼ぶプログラムを作ったときにまた壊れます。**

### ④ ベースアップ（★Read tool で実際に開いた実物だけを書きます）

| ファイル | どこを開いたか |
|---|---|
| `scripts/priority_rebuild/engine_tuner_gen.py` | 795-825行（`_cc`・`_vr`・`strip_marks`）／1975-2110行（`ranked_groups`・`_ranked_material_at`・`regime_draw_order`・`sample_regime_build`）／2236-2281行（`sample_structure` の末尾＝印を外さずに返す） |
| `scripts/priority_rebuild/regime_r9_diag.py` | 225-259行（外から検査を呼ぶ所） |
| `scripts/dashboard/build_regime_from_tuner.py` | 170-199行（同上） |
| `scripts/priority_rebuild/engine_tuner_fire_diag.py` | 378-399行（同上） |
| `scripts/priority_rebuild/gen_signal_families.py` | 642-673行（`insufficient_samples`＝禁止3 の式） |
| `scripts/priority_rebuild/engine_tuner_exec.py` | 2235-2252行（幾何 geo＝W% の式・帯の列の出どころ） |
| `scripts/dashboard/build_regime_gate_rg.py` | 95-149行（RG-v5 のゾーンビルダー） |
| `scripts/dashboard/build_range_gate_dashboard.py` | 48-55行（ゾーンの定数4つ） |
| `scripts/priority_rebuild/e37_scalp.py` | 118-126行（同じ定数4つ）／470-485行（内側の隙間の幅の判定） |
| `scripts/priority_rebuild/observe_diag.py` | 363-372行（`_sr_touch`） |
| `scripts/priority_rebuild/observe_config.json` | 222-255行（`fractal_k`・`sr_windows`・`sr_tol`） |
| `scripts/priority_rebuild/indicator_reference_diag.py` | 4136-4144行（RANGE_GEO_REF の W%） |
| `scripts/priority_rebuild/e38_logic_parts.py` | 20-26行（SCALP_FLOOR） |
| `scripts/priority_rebuild/gen_audit_request.py` | 200-215行（§3.4 の行の複写） |
| `scripts/priority_rebuild/verify_design_contract.py` | 420-431行（`--write`） |
| `.claude/ratchet/engine_tuner_milestones2.md` | 505-512行（凍結13要素表） |
| `.claude/memory/regime_detection_kb.md` | 717-720行（R5〜R8） |
| `.claude/state/session_worklog_20260827.md` | 1533-1562行（§41） |
| `.claude/audits/2026-08-27_regime_element04_audit_report.md` | 全文（1-118行） |
| `.claude/audits/inputs/2026-08-27_regime_element04_audit_request.md` | 1-320行 |
| `.claude/state/next_step.md` | 全文（1-380行） |
| `.claude/rules/permanent_rules.md` | 1-30行（自動で全文が読み込まれている） |
| `.claude/ratchet/adopted_strategies.md` | 全文（1-148行） |
| `.claude/rules/cat_requirements.md` | 1-8行 |
| `.claude/rules/exchange_spec.md` | 1-12行 |
| `scripts/priority_rebuild/eval_engine.py` | 1-10行 |
| `.claude/state/acceptance.md`（前の版＝92番） | 全文（1-245行） |

**WebSearch は使っていません。**この設計は、このリポジトリの中のコードのつながりだけで決まるためです（監査の外部検索7件は §4 の1〜7 に在り、この2件の直しには関わりません）。

---

## §4 変更は 1レバーか（H16・1ターン1変更）

**やることは2つですが、どちらも「案を組む道を通す」という1つの狙いの、別々の詰まりです。**監査（Major 3・Major 4）も、68回目の私の案（worklog §41）も、2つを1組で出しています。**まこさんの決定「束が組めない件を先に直す」の「件」がこの2つです。**
**分けて出す形**＝原因A だけ先に直すと、実測は 36/120 で止まり（原因B の5組が必ず落ちる）、「組める」の確かめが2回に分かれて H2・G2 の印の取り直し（約5分20秒）も2回になります。**★分けるべきと まこさんが判断されたら、やること1 だけの版に書き直します。**

**過去に破った失敗の再演か**＝**89番と同じ型（同じ判定が2か所に在り、片方だけ直した）を、78番の直し（59回目）でまた作っていました。**今回はその型を「公開の包み1本＋直に呼ぶ所を番人が数える」で閉じます。

---

## §5 ★疑似シミュ由来の固定値ゼロ宣言

**この設計には、疑似シミュ（probe）から出た数字が1つも入っていません。**

- (a) この設計が持つ数字は **「10」（既に在る引き直しの回数・触らない）** と **「範囲の下限・上限」（`material_ranges`＝カタログの最小・最大・触らない）** だけです。**新しい数字を1つも作りません。**
- (b) probe の数値を固定値に焼いていません。**probe を1回も走らせていません。**
- (c) 採否は、**わざと壊して止まるか試すテスト**と、**外から呼ぶ道で束を組む実測（機械が出す本数）**と、**恒等3本のハッシュ一致**で決めます。

---

## §6 ハード制約（H1〜H16）と審判整合

**H1〜H16 と 審判整合（D）は、まとめて非該当です。**
理由＝売買のロジックにも審判にも1バイトも触りません。売買記録CSV を1本も作りません。探索の本走もしません。
**H2**（未来参照）＝原因B の判定は、禁止3 の式（`gen_signal_families.insufficient_samples`＝値決め窓の日数 ÷ 値が独立に1つ決まる日数）をそのまま呼ぶだけで、採点窓のデータを1バイトも読みません。
**H16（1変更・過去の失敗の不再演）は §4 で書きました。**

---

## §7 やること（2件）

### 7.1 触るファイル（4本・主ファイルは1本）

| # | ファイル | 何を |
|---|---|---|
| 1 | `scripts/priority_rebuild/engine_tuner_gen.py`（**TARGET**） | やること1・やること2・番人3件 |
| 2 | `scripts/priority_rebuild/regime_r9_diag.py`:250 | `ex.validate_recipe(r, limits=lim)` → `g.validate_drawn(r, limits=lim)`（1行） |
| 3 | `scripts/dashboard/build_regime_from_tuner.py`:192 | 同上（1行） |
| 4 | `scripts/priority_rebuild/engine_tuner_fire_diag.py`:392 | 同上（1行・★58回目の印の導入以降、この診断も同じ型で落ちる状態） |

### 7.2 やること1（原因A）＝印を外してから検査を呼ぶ「公開の包み」を1本にし、外から呼ぶ3本を揃える

| # | 何 | どう |
|---|---|---|
| 1-1 | 公開の関数 `validate_drawn(recipe, *a, **k)` を足す | 中身＝`import engine_tuner_exec as ex; return ex.validate_recipe(strip_marks(recipe), *a, **k)`。説明文に「案を作るプログラムが返した案（印つき）を検査に通すときは必ずここを通る」と書く |
| 1-2 | `_vr` はそれを呼ぶ形にする | 判定を2か所に書き写さない（89番の型を作らない） |
| 1-3 | 外から呼ぶ3本を `validate_drawn` に揃える | 7.1 の 2〜4 |
| 1-4 | **番人 T30（外の道）** | `sample_structure(..., build_regime=True)` の戻りを (a) `ex.validate_recipe` に直に渡すと `RecipeError`（印が残っている証拠＝いまの壊れ方の再現）(b) `validate_drawn` に渡すと通る |
| 1-5 | **番人 T31（呼び出し元の走査）** | `scripts/priority_rebuild/` と `scripts/dashboard/` の `.py` を全部 構文木で読み、**`sample_structure(` を呼ぶファイルの中で `validate_recipe(` を直に呼んでいる所（`strip_marks`／`validate_drawn` を経由しない）が 0件**。★一覧は手で並べない＝ファイルを機械で集める（L-563 の型）。`engine_tuner_gen.py` 自身の中で `strip_marks(r)` を挟んで呼ぶ4か所（:3109・:3336・:3415・:5274・:5365）は「経由している」と数える |

### 7.3 やること2（原因B）＝範囲のどの数字でも禁止3 の組を、順位に数えない

| # | 何 | どう |
|---|---|---|
| 2-1 | `_group_usable(fam, tf, ranges, table) -> bool` を足す | その種類の範囲（`material_ranges()[fam]["axes"]`）の数字を**全部 走査**し、1つでも禁止3 を通れば True。整数の軸＝lo〜hi の全部／小数の軸＝lo〜hi を `dec`（カタログの小数の桁数）の刻みで全部（`draw_param` が丸める桁と同じ＝引ける数字を1つ残らず見る）。軸が複数なら直積。判定は `_banned_pair` と同じ式（`ex.build_name` → 表 → `_insufficient_samples`）。結果は (fam, tf) で覚える（同じ組を2回 走査しない） |
| 2-2 | `_ranked_material_at` の順位を数えるループで、`_group_usable` が False の組は `n` に数えない | 既存の「型の表・時間足・系統で数えない」と同じ場所（:2021-2024 の続き）。**10回の引き直し（:2029-2033）と「次の組へ飛ばさない」（:2034-2036）は触らない** |
| 2-3 | `ranked_groups` は触らない | 順位の表そのもの（M2-3 で承認）の読み方は変えない。外すのは「材料を取る所」だけ |
| 2-4 | **番人 T32（使えない組を数えない）** | (a) 実物の順位で env「強さ」の1位が **stdev%×1d でない**こと（直す前は1位＝0/200 の組）(b) `_insufficient_samples` をわざと「全部 使える」に差し替えると、直す前と同じ順位に戻ること（＝外しているのが本当にこの判定であるメタ確認）(c) 同じ種で2回 呼んで同じ組が返ること（乱数に依らない） |

### 7.4 変えないもの

| # | 何 | なぜ |
|---|---|---|
| 1 | 印を付けたまま案を返す作り（`sample_structure`:2270・C-7） | 保存する案に出どころを残す決まり（59回目・まこさん承認） |
| 2 | `ranked_groups`（順位の表の読み方） | M2-3 で承認済み |
| 3 | 10回の引き直しと「次の組へ飛ばさない」 | 「1位から順」を乱数に依らせない意図（:2035 の逐語） |
| 4 | 範囲（`material_ranges`）・引き方（`draw_param`・`_mat_drawn`）・閾値（`_thr_drawn`） | 探す範囲を1バイトも動かさない |
| 5 | `engine_tuner_exec.py`・`score.py`・`eval_engine.py`・戦略ファイル | 対象ではない（H13） |

---

## §8 完成の条件（★全部 満たすまで終わりません・数字は機械が出す）

| # | 何 | どう確かめるか |
|---|---|---|
| 1 | 番人 T1〜T29 ＋ T30・T31・T32 が全部 pass | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` |
| 2 | **外から呼ぶ道で束が組める**＝組めた本数が 0 でない | `python3 scripts/priority_rebuild/regime_r9_diag.py --build 20 --seed 53 --no-trades`（68回目は 0/96） |
| 3 | 外から検査を直に呼ぶ所が 0か所 | 番人 T31 の出力 |
| 4 | env の順位で「範囲のどの数字でも禁止3」の組が順位に無い | 番人 T32 の出力 |
| 5 | 直す前と後で結果が同じか確かめる3本の走行（S2・L1・S1）のハッシュ値が一致 | `--identity`（場面の判定の束を使わない案は1バイトも変わらないはず） |
| 6 | H2・G2 の印を取り直して両方 一致 | `leak_causality_diag.py`（約4分49秒）／`gen_signal_families.py --verify`（約29.6秒） |
| 7 | 機械生成の文書の `--verify` が全部 ✅（22番の決まり） | `gen_materials` ほか |
| 8 | `regime_r9_diag.py --selftest`・`engine_tuner_fire_diag.py` の自己テスト（在れば）が通る | 各 `--selftest` |

---

## 自己検査（番人・★わざと壊して落ちるかをメタ確認する）

| # | 見本 | 期待 |
|---|---|---|
| T30-a | 印つきの案を `ex.validate_recipe` に直に渡す | **止まる**（`RecipeError`・いまの壊れ方の再現） |
| T30-b | 同じ案を `validate_drawn` に渡す | **通る** |
| T31-a | いまの3本（揃えた後） | **0件** |
| T31-b | わざと `regime_r9_diag.py` の写しを一時の場所に置き、`ex.validate_recipe(r, …)` に戻す | **1件 出て止まる**（走査が本物であるメタ確認） |
| T32-a | 実物の順位で env「強さ」の1位 | stdev%×1d **でない** |
| T32-b | `_insufficient_samples` を「全部 使える」に差し替える | 直す前と同じ順位に**戻る** |
| T32-c | 同じ種で2回 | 同じ組 |
| 既存 T1〜T29 | 触らない | 全部 pass のまま |

---

## 走らせるもの・時間の見込み（恒久の決まり60番・61番・62番）

| # | 何 | 見込み | 過去の実測（記録の逐語） |
|---|---|---|---|
| 1 | `engine_tuner_gen.py --selftest` | **約5分**（15分未満） | `session_worklog_20260827.md`:1794「`engine_tuner_gen.py --selftest`（T1〜T29）… 5分06秒」／同 :308「所要 5分04秒」 |
| 2 | `regime_r9_diag.py --build 20 --no-trades` | **約7分**（15分未満・★案1本あたりの時間は不明＝最初に `--build 1` で測ってから 20 へ） | 同 :1335「R9 の診断（… `--build 1 --seed 53 --no-trades`）… 束 0本（所要 19秒）」＝0本でも19秒＝データの読み込みが主 |
| 3 | 恒等3本 `--identity` | **約10分**（15分未満） | `session_worklog_20260825.md`:536「`--identity-quick`・S2・90日＝real 103.99秒」。本走3本は同 :537（S2 165行・L1・S1） |
| 4 | H2（`leak_causality_diag.py`） | **約5分** | `next_step.md` (0-b-2)「実測 4分41秒」／§0-3「実測 4分49秒」 |
| 5 | G2（`gen_signal_families.py --verify`） | **約30秒** | 同「実測 28.5秒」「実測 29.6秒」 |

**途中経過**＝1・4 は検査ごとに1行ずつ画面に出る。2 は案ごとに「組めない／組めた」が出る。**裏では走らせない**（どれも15分未満）。

---

## ★入っていないもの（都合の悪い事実も書きます）

1. **監査の Critical 1（M2 に「帯を作る」行を新設＝ゾーンビルダーの4定数を recipe から範囲で渡す）と Critical 2（幅の絶対床＝`const` を生成器の場面の束で使う・内側の隙間の ratio 列）は入れていません。**どちらも `engine_tuner_exec.py`（と `e37_scalp.py`／ダッシュボード）を触り、**M2 のやることリストの順番に関わります（恒久の決まり58番＝順番は まこさんが決める）。**別の設計書にします。
2. **この2件を直しても、第4要素（スイング数≥2のゾーン対・幅≥0.4%）は組めるようになりません。**監査の Q1 の逐語＝「依頼書の2原因を直しても (1)(2)(3) は残る」。**この設計書が直すのは「束が1本も組めない」詰まりであって、「組んだ束が第4要素を満たす」ではありません。**
3. **原因B を直しても、その組の中で10回 引いて全部 禁止3 になる案は残ります**（範囲の一部だけが使える組）。乱数に依らせない直し（使える数字だけから引く）は `_mat_drawn`（数字を引く唯一の入口）を触るので、この回では入れません。
4. **番人 T31 の走査は「`sample_structure(` を呼ぶファイル」しか見ません。**案を json で受け取って検査するプログラム（`--validate`）は対象外です（そこには印つきの案は渡らない設計ですが、機械では確かめていません）。
5. **T32-a は実物の順位（`material_ranking.json`）に依ります。**順位を作り直すと見本の期待が変わりえます（そのときは番人を作り直す）。

---

## DESIGN_CONTRACT

```json
{
  "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
  "self_check_calls": [
    "validate_drawn",
    "strip_marks",
    "_group_usable",
    "_ranked_material_at",
    "ranked_groups",
    "_banned_pair",
    "selftest"
  ]
}
```

---

## 「作ってはいけないもの」2件との照合（着手前・必須）

| # | 作ってはいけないもの | 当たるか | なぜ |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 条件のつなぎ方（`sample_regime_build` の A∩B∩C・hysteresis）に1バイトも触りません |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 範囲を1つも狭めません。順位から外すのは「範囲の全部が禁止3 の組」で、それを決めるのは範囲の全走査（機械）です。私は数字を書きません |

---

## この設計で net は動くか

**動きません。**実験を1本も走らせません。売買記録CSV を1本も作りません。探索の本走もしません。
`score.py`・`eval_engine.py`・戦略ファイル・`engine_tuner_exec.py` は1バイトも触りません。
**★これから先の net には効きます。**束が組めなければ、場面の判定を net で選ぶ工程（M2-10・M2-11）に進めないからです。

---

## SPEC（★手書きしない＝verify_design_contract.py --write が実物のコードから書き出したものを写した・2026-08-27）

> `python3 scripts/priority_rebuild/verify_design_contract.py --write .claude/state/acceptance.md` の出力（公開する関数 65件／定数 5件／コマンドの旗 0件）をそのまま写した。
> **手で直したのは1行だけ**＝今回 足す公開の関数 `"validate_drawn": ["strip_marks"]`（やること 1-1）。`_group_usable` は名前が `_` で始まる（公開でない）ので SPEC には載らない。

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/engine_tuner_gen.py",
 "public_functions": {
  "load_limits": [],
  "HoldRangeError": [],
  "resolve_hold_range": [
   "HoldRangeError"
  ],
  "hold_bars": [
   "HoldRangeError"
  ],
  "material_pool": [],
  "material_ranges": [
   "load_limits"
  ],
  "param_in_range": [
   "material_ranges"
  ],
  "draw_param": [
   "material_ranges"
  ],
  "assert_provenance": [
   "SampleError",
   "material_ranges",
   "param_in_range",
   "q_range_of"
  ],
  "assert_roles": [
   "SampleError"
  ],
  "assert_exit_roles": [
   "SampleError"
  ],
  "validate_drawn": [
   "strip_marks"
  ],
  "strip_marks": [],
  "int_range_of": [],
  "draw_int": [
   "int_range_of"
  ],
  "num_range_of": [],
  "draw_num": [
   "num_range_of"
  ],
  "ladder_min_frac": [],
  "max_ladder_steps": [
   "ladder_min_frac",
   "num_range_of"
  ],
  "q_range_of": [],
  "quantile_list": [
   "q_range_of"
  ],
  "draw_q": [
   "q_range_of"
  ],
  "q_in_range": [
   "q_range_of"
  ],
  "num_in_range": [
   "num_range_of"
  ],
  "SampleError": [],
  "load_signal_table": [],
  "load_scene_rules": [],
  "load_material_ranking": [],
  "ranked_materials": [
   "load_material_ranking"
  ],
  "same_fn_family_pairs": [],
  "pair_allowed": [
   "same_fn_family_pairs"
  ],
  "load_exit_table": [],
  "ranked_groups": [
   "ranked_materials"
  ],
  "regime_draw_order": [
   "SampleError"
  ],
  "sample_regime_build": [
   "SampleError",
   "load_scene_rules",
   "regime_draw_order"
  ],
  "default_regime": [],
  "sample_structure": [
   "SampleError",
   "default_regime",
   "load_signal_table",
   "sample_regime_build"
  ],
  "recipe_hash": [
   "strip_marks"
  ],
  "write_kakikudashi": [],
  "structure_breakdown": [],
  "needed_qkeys": [],
  "build_qtable": [
   "needed_qkeys"
  ],
  "attach_materials": [],
  "pvalue_daily": [],
  "bh_select": [],
  "strat_gate": [],
  "Journal": [],
  "assert_known_exit_reason": [],
  "run_trial": [
   "strip_marks"
  ],
  "run_trial_guarded": [
   "run_trial"
  ],
  "reject_code": [],
  "zero_trade_gate": [],
  "per_day_gate": [
   "zero_trade_gate"
  ],
  "suggest_slot": [],
  "value_slots": [
   "hold_bars",
   "int_range_of",
   "num_range_of",
   "q_range_of"
  ],
  "apply_slots": [],
  "read_slots": [],
  "run_generation": [
   "Journal",
   "apply_slots",
   "bh_select",
   "build_qtable",
   "per_day_gate",
   "pvalue_daily",
   "quantile_list",
   "read_slots",
   "recipe_hash",
   "reject_code",
   "run_trial",
   "run_trial_guarded",
   "sample_structure",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "suggest_slot",
   "value_slots",
   "write_kakikudashi"
  ],
  "synth_df": [],
  "selftest": [
   "Journal",
   "apply_slots",
   "assert_known_exit_reason",
   "bh_select",
   "build_qtable",
   "gate_matrix",
   "ladder_min_frac",
   "lint_provenance",
   "load_exit_table",
   "load_limits",
   "load_material_ranking",
   "load_signal_table",
   "material_pool",
   "max_ladder_steps",
   "needed_qkeys",
   "num_in_range",
   "pair_allowed",
   "param_in_range",
   "per_day_gate",
   "pre_run_gate",
   "pvalue_daily",
   "q_in_range",
   "q_range_of",
   "quantile_list",
   "ranked_groups",
   "ranked_materials",
   "read_slots",
   "regime_draw_order",
   "reject_code",
   "resolve_hold_range",
   "run_generation",
   "run_trial_guarded",
   "sample_structure",
   "strat_gate",
   "strip_marks",
   "structure_breakdown",
   "synth_df",
   "value_slots",
   "verify_provenance",
   "zero_trade_gate"
  ],
  "pre_run_gate": [],
  "run_main": [
   "assert_known_exit_reason",
   "hold_bars",
   "load_limits",
   "material_pool",
   "pre_run_gate",
   "resolve_hold_range",
   "run_generation"
  ],
  "main": [
   "gate_matrix",
   "lint_provenance",
   "load_limits",
   "material_pool",
   "run_main",
   "sample_structure",
   "selftest",
   "strip_marks",
   "structure_breakdown",
   "verify_provenance"
  ],
  "lint_provenance": [],
  "gate_matrix": [
   "apply_slots",
   "load_limits",
   "load_signal_table",
   "material_pool",
   "material_ranges",
   "resolve_hold_range",
   "run_trial_guarded",
   "sample_structure",
   "value_slots"
  ],
  "verify_provenance": [
   "load_limits",
   "load_signal_table",
   "resolve_hold_range"
  ]
 },
 "constants": {
  "PARAM_SRC": "_param_src",
  "Q_SRC": "_q_src",
  "NUM_SRC": "_num_src",
  "LIN_SRC": "_lineage_src",
  "ATTACH_CALLS": 0
 },
 "cli_flags": []
}
```
