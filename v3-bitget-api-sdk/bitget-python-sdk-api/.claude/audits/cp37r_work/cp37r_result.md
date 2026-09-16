# 監査結果 cp37r — CP37 — 監査 cp36 の Major 7件と不具合1件を直す設計書は、指摘の本体を閉じる形になっているか。書いたとおりに作れるか

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-15_m2e2_major_design_cp37r_audit_request.md`
- 依頼書のハッシュ値: e57114a101dabbcd24c43ee3ffd306ada792780b5c6d59789dfdb518d30571ec
- 監査の相手と版（依頼書に書いてあるもの）: `SDK/.claude/audits/cp37r_work/design/acceptance.md` ／ ハッシュ値 0c692abf392b47e72e657f4ae99169a97b519c60b2118c5ed9b2622c0298d2d9
- 監査が照らしたハッシュ値: 0c692abf392b47e72e657f4ae99169a97b519c60b2118c5ed9b2622c0298d2d9（`shasum -a 256` の結果。依頼書の値と一致した）
- 実施日: 2026-09-15

補足:
- 監査の相手は、設計書の写し（目印 `m2e2-cp36-major-20260914`・1,130行）と、その元データの写し `cp37r_work/design/acceptance_src.json`（431行）。
- 監査は Plan エージェントが、依頼を出した CC の文脈を持たずに行った。このエージェントは読み取り専用の設定で起動されたので、写し（mirror）を作れなかった。写しでの実測を求める問い（A1-a・A2-a・A3-b）の扱いは 4 と 10 に書く。A1-a だけは、成績表の JSON を jq で読んで候補の順位を組み直した（再構成）。これは写しで走らせたものではない。
- いまの `.claude/state/acceptance.md` と `cp37_work/` の中身は開いていない。
- 月次 NET ≥ $1,900 に届くかどうかは、この監査の対象外（この工事は売買を1件も回さない）。


## 2. 監査対象の型宣言

- 文書型: 設計書 acceptance.md と、その元データ acceptance_src.json。
- コード型: 設計書が触る実物。`engine_tuner_gen.py`・`engine_tuner_exec.py`・`regime_r9_diag.py`・`run_breaks.py`・`count_builder_literals.py`・`gen_regime_kb.py`・壊すプログラム・hook。照らし合わせの相手として読んだ。
- 数値型: 成績表 `material_ranking.json` の分離力。段2a・段2c の候補の順位を組み直すのに使った。


## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの）

| # | 依頼書の行 | 自分で確かめた結果 |
|---|---|---|
| 1 | `gen_acceptance.py --write`＝1,130行・囲み11個・法則51件＝表51行 | 行数は写しで1,130行（`wc -l`）で一致。法則の表は ACC_LAWS の中の 244〜294行の51行で一致。**囲みは `_START` の目印を数えると10個**（ACC_* が9個＋ACCEPT_TABLE が1個）で、11個にならない。11個の数え方は記録に無い＝データ不足（理由：道具が土台ゲートで走らせられない） |
| 2 | `gen_acceptance.py --verify`＝囲み9つ ✅ | データ不足（理由：`.claude/tools/*.py` を走らせるコマンドは土台ゲートが止めた。しかもこの道具は、読むなと指示された いまの `.claude/state/acceptance.md` を読む） |
| 3 | `pre_audit_check.py --check-design`＝不足0件 | データ不足（理由は2と同じ） |
| 4 | `pre_audit_check.py --run`＝12件 rc=0 | 走らせていない（理由：土台ゲート。加えて worklog 20260914 §44 に「道具が書き直した文書4本」とあり、書き込みを伴う）。§44 の表（H2 322.1秒・G2 26.0秒・exec selftest 8.6秒）は依頼書の数字と一致した |
| 5 | `regime_r9_diag.py --build 3 --no-trades --seed 8` が `KeyError: 'n'` | 走らせていない（理由：`engine_tuner.py` の `load_windows_cached` に `CACHE_DIR.mkdir`／`df.to_parquet` があり、書き込みが起きる）。コードで仕組みを確かめた。`engine_tuner_exec.py`:2031 の `return f"{pre['op']}{pre['n']}:{name}"` は、abs の前処理だと n を持たない。n を持たないことは exec:610〜614 が強制している（abs に n を書くと G5 で止める）。だから abs の材料が解決表の道を通ると、KeyError が必ず起きる |
| 6 | `gen_regime_kb.py --verify` が rc=1 | データ不足（理由は2と同じ）。worklog §37 に記録はある |
| 7 | 承認④の記録で #5〜#7 が `script: null` | `acceptance_archive/m2e2-cp36-critical-20260913.breaks.json` を開いて確かめた。#5・#6・#7 は null。b93・b92・b91・b85・b78 は rc=1 で match は真。**b85 の最後の ❌ の行は「❌ T42」で、宣言は「T39」**だった |
| 8 | 自己テスト3回目が全部 pass・秒数の記録なし | worklog §29 に「✅ 全部 pass・rc=0」とあり、秒数は無い。一致した。再実行はしていない |


## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ FAIL（完成の条件 #5 の合否が、種7 の入口の乱数の引きで決まる）
- ②リスク管理 ＝ FAIL（打ち切り600秒に対して、自己テストの秒数の実測が無い）
- ③認知バイアス ＝ FAIL（C4 の当て方を、R3 の注意の説明文から導いた）
- ④ソフトウェア工学 ＝ FAIL（空の配列が既定に戻る形 `or [None]` を再び書いた。関数と `--lint-expect` の置き場所を書いていない）
- ⑤再現性 ＝ FAIL（R9 の完成の条件が種に依存する）
- ⑥実行プロセス ＝ FAIL（hook が止める確認を「自分で走らせて貼る」と約束した。見込みの秒数を「3回の実測」と書いた）
- ⑦主エージェントバイアス ＝ FAIL（自己申告1・2 の不安を測らないまま、期待「9件とも変わる」と種7 を完成の条件にして出した）

### A1 — 法則 C4 を1件だけ書き替えると、実際に組まれる束が本当に変わるか（優先度 A）

**重さ＝Critical**

- **A1-a（jq による再構成。写しでの実行ではない）**
  - 段2a（役割 env・札「強さ」）を組み直した。条件は `ranked_groups` と同じ中央値と並べ方、R5 の family と §2.2 の元データの7種、型の表の禁止の組。
  - 5m より後ろの絞りを掛けた場合の上位は、1位 MACDヒスト%×30m（0.541）、2位 ADX×1h（0.460）、3位 ADX×2h（0.462）、4位 EMA傾き×15m。
  - 絞りを外して5分足を入れると、**5分足の最初の候補は MACDヒスト%×5m の4位**（|中央値−0.5|＝0.037）。上位3位は変わらない。
  - env／強さ の5分足の列のうち |acc−0.5|>0.0375 のもの32本に、R5 と §2.2 の family は0本。
  - 1位は、監査 cp36 が実測した土台の C（MACDヒスト%(12,26,9)__30m）と一致した。
  - `regime_draw_order` で案0〜5 が使う C の順位は1位と2位だけ（gen:2374〜2382）。T24⑤ も `_N45 = 6`（gen:6278）。
  - 以上から、**設計書のとおり正しく作っても、C4 を外したとき案0〜5 の束は変わらない。**T24⑤ の期待「9件とも変わる」（設計書 726行・534行）は満たせない。その結果、完成の条件 #4・#9 と、同じ自己テストを使う #1・#2・#6 の条件のコマンドが rc=0 にならず、「済」が付かない。
  - 再構成の限界：`material_ranges` と系統の絞りは実行していない。ただし順位2と順位3の両方が落ちない限り、結論は変わらない。
- **A1-b**
  - 期待を「C4 は変わらない」に戻すと、M-3 を測れない。
  - 直す相手は T24⑤ の測り方か、C4 の当て方（A3）のどちらか。どちらを取るかは設計の選択なので、修正の指示では案を2つ並べた。
  - 同じ期待は元データの 233・245・356・380 行に書かれているので、4か所とも修正の指示に入れた。
- **A1-c**
  - 読みは正しい。R3 の系統を「ボラ」にすると、`stage_lineages_of` の重なり（R1＝構造・位置 ∩ R3＝ボラ）が空になり、SampleError で6本とも組めない。つまり「変わる」になる。
  - ただし、この書き替えで測れるのは R3 の系統を読んでいることだけで、R3 の時間足を読んでいることは測れない。

修正の番号＝1, 2, 35, 36, 37, 38, 39, 40

### A2 — 需給の材料が入る種で、R9 の診断が本当に3本とも測れるか（優先度 A）

**重さ＝Critical**

- **A2-a**
  - データ不足（理由：写しを作れず、本物の走行は parquet のキャッシュを書く）。
  - コードでは次のことが分かった。`sample_structure` は入口を `rng` で引き（gen:3029〜3132）、束は最後に乱数なしで組む（gen:3137〜3141）。`regime_r9_diag.py`:261 は `rng = np.random.default_rng([a.seed, 1, tries])` で、組めないと `tries` が進んで別の乱数になる。
  - つまり、**種7 に需給が入るかどうかは入口の乱数の引きで決まり、束が組めずに引き直した回数でも変わる。**
- **A2-b**
  - リスク4（設計書 626行）の「需給が入る種を探して、条件のコマンドを直す」は、成績を見ないとしても**種の引きで完成の条件の合否が決まる形**。まこさんの逐語「偶然による構築、選出はやめてほしい」（acceptance_src.json:61）に当たる。
  - 依頼書の前提2（乱数が1つでも残る形なら Critical）により **Critical** とする。
  - 設計が触る `main` に、この rng の行が残る。
  - `--recipe` の口（r9:232）があるので、固定のレシピで乱数に依らずに測れる。
  - 同じ完成の条件は元データの 100・231・336・357 行に書かれているので、4か所とも修正の指示に入れた。378 行（99回目に走らせたコマンドの記録）は完成の条件ではないので入れていない。
- **A2-c**
  - 残る。`measure` は `SystemExit` だけを受け（r9:132）、1本の失敗で全部の束を「測れない」にする（r9:143〜145）。入口に1分足・3分足や別の材料が引かれると、需給と関係なく rc=1 になる。
  - b97 の EXPECT_MSG が設計書で決まっていないので、別の理由で落ちても「期待どおり」に数える M-2 と同じ型が残る。

修正の番号＝3, 4, 5, 6, 7, 8, 9, 10, 41, 42

### A3 — 法則の当て方が、法則を CC が作る・強める・弱めることにならないか（優先度 A）

**重さ＝Major**（直す指示は A1 と同じ修正に含めた）

- **A3-a**
  - R3 を段1 に当てるのは正しい。R3 は「かつ・構造・位置・執行足より上」で、構造・位置の部品は帯（B）1本なので、1本の枠に掛けても法則と同じになる。
  - **C4 を段2a の枠ごとの絞りにするのは、法則の判定と合わない。**審判 G7 は C4 を束全体の部品の時間足で数える（exec:1328〜1332）。本数は1で、B が R3 で必ず上位足なので、C4 は束の単位で常に満たされる。
  - 根拠に使った R3 の注意「C4 は部品C…で常に満たす」は、組む側のいまの作りを説明した文で、C4 を段2a に掛けろという規定ではない。
  - 段2a を上位足に絞る出どころは §2.2 の文「時間足は上位足（15m〜4h）」（milestones2 §2.2 の段2a）。設計の形では、C4 を外すと段2a に5分足が入り、§2.2 の決定に反する。
  - 設計書が捨てた案（決めたこと2＝全部の枠に掛けると法則を強める）と同じ理屈で、段2a 1枠に掛けることも C4 単独に対しては強めることになる。
- **A3-b**
  - データ不足（写しを作れない）。
  - 再構成では、段2c の5分足の最初の候補は10位（BB幅×5m）。土台の G（1位 stdev%×30m・2位 BB幅×30m）は変わらない。
  - G7 の法則で、G に上位足を求めるもの（R2・R6・R10）は無い（exec:1321〜）。T24② が5分足で落ちる経路は、コードでは見つからなかった。
- **A3-c**
  - この工事で上端を変えない扱いは、恒久42番（値はまこさん）に合う。PASS。

修正の番号＝1, 2, 35, 36, 37, 38, 39, 40

### A4 — `stage_limits` を読む直しが、候補と実際の束の両方に効くか（優先度 A）

- **A4-a（重さ＝Major）T43 は1本目だけを測る形か**
  - T43 の文（設計書 724行）は候補の一覧だけを見る。
  - 2本目は `build_stage_candidates(…, limits)` をそのまま呼ぶ（gen:2903・2904・2958）ので、いまは同じ設定が効く。しかし、2本目に `stage_limits` が効いていることを測る自己テストは無い。
  - T42 は本物の設定（空）同士を比べるだけ。2本目に渡す設定を外すと、98回目の b92 と同じ型が見逃される。
- **A4-b（重さ＝Major）範囲の外で止まる判定の並び・空の配列**
  - 承認済みの範囲を広げる道は無い（tfs は計算済みの時間足の中・分位は quantile_range の中・param はカタログの中・families は §2.2 の中）。この点は PASS。
  - **ただし、設計書 4-4 の擬似コード `qs = lim_s.get("quantiles") or [None]`（設計書 332行・元データ 148行）は、空の配列を「無い」と同じに扱う形そのもの。**M-1 で直す `drop_tfs` の不具合（gen:2609）を、新しく足す欄で再び書いている。
  - 4-5 の表（設計書 463〜471行）には、`tfs`・`families`・`quantiles` が空の配列だったときの止まり方が無い。
- **A4-c（重さ＝Minor）分位を2つ書いたときの2本目の順位の意味**
  - `quantiles` を2つ書くと、1位と2位が同じ材料の分位違いになる（`_stage_pick` は一覧の順位をそのまま使う・gen:2805〜2812）。
  - `stage_keep_range` の上位の本数も「材料×分位」で数えることになる。
  - いまは値が空なので、動きには効かない。

修正の番号＝11, 12, 13, 14, 15, 16, 27, 28, 53, 54

### A5 — 乱数と法則番号の直書きが、新しく足す関数に入らないか（優先度 A）

**重さ＝Major**

- **A5-a**
  - 数える範囲は `START = "_ranked_material_at"`・`END = "default_regime"`（count_builder_literals.py:53〜54）の最上位の文だけ。
  - 設計書は、新しく足す4関数の置き場所を書いていない。
  - `print_stage_candidates`（regime_r9_diag.py）は別のファイルなので、数えられない。
  - つまり、完成の条件 #7 の文「新設の読み口」は、書いたとおりには測れない。
- **A5-b**
  - `law_tf` は元データの値と `laws["counts"]` の番号を比べるだけで済み、法則番号の文字は要らない。PASS。
  - 残る直書きは "5m" と "執行足より上"。どちらも法則番号ではなく、実行器も同じ形を持つ（exec:1284・1293）。

修正の番号＝17, 18

### B1 — EXPECT_MSG の直し（M-2）と `--lint-expect` が、書いたとおりに動くか（優先度 B）

**重さ＝Major**

- **B1-a**
  - `main` の順番は、`--parse-only`（run_breaks.py:353）→ `--freeze` → **凍結の照合（run_breaks.py:388〜394・rc=2）**→ 深さの判定（run_breaks.py:400〜403）。
  - b95 は b77 を書き替えるので、`--lint-expect` を凍結の照合より後ろに置くと、rc=2 と「❌ 壊すプログラムが承認のときから変わっています: b77…」になる。これには「❌ b77」が含まれない。
  - つまり、**`--parse-only` と同じく、凍結の照合より前に置く必要がある。**設計書には書かれていない。
  - CC の Bash は run_breaks.py を `--measure-only`・`--selftest` 以外では走らせられない（require_acceptance_before_impl.sh:249）。
- **B1-b**
  - 書き替え先は1つに決まらない。
  - 監査 cp36 §1-1 の「実際に落ちた行」は、98回目の変更（T24⑤・T42・T35 を足し、2本目を一覧から取る形にした）より前のもの。
  - 98回目の記録は最後の1行（`tail[-1]`・run_breaks.py:302）しか残さない（例：b85 は ❌ T42）。
  - 決まっているのは b82 の新しい形「❌ T40④」だけで、これは T40④ の判定（gen:6139〜6143）と合う。
  - 残りは、リスク3 の「壊し方を当てて観る」手順でしか決まらない。
- **B1-c**
  - 判定の拠り所が書かれていない。
  - 壊すプログラムは `measure python3 …/engine_tuner_gen.py --selftest` の行を持つ（b77:25・b81:41・b82:28・b93:30）ので、「`measure` で始まる行に `--selftest` がある」で決まる。

修正の番号＝19, 20

### B2 — 別の人が、この設計書だけを読んで作れるか（優先度 B）

**重さ＝Major**

- **B2-a**
  - `law_tf` を `stage_tfs_of` に届けるには、案を作るプログラムの `stage_candidates` が、写す鍵に `law_tf` を足す必要がある（いまは role・law・law_or・law_width だけ・gen:2505〜2518）。
  - 設計書 4-3 と DESIGN_CONTRACT は `expand_stage` だけを挙げ、`stage_candidates` を挙げていない（元データ 137行・406行）。ここで手が止まる。
  - ほか：`--lint-expect` の置き場所（B1）、4関数の置き場所（A5）。
- **B2-b**
  - T43・T44・b94・b98・b82 は、設計書の文で壊す行が1つに決まる。
  - b96 は A1 により意味を持たない。b97 は A2 により種に依存する。
- **B2-c**
  - 監査 cp35 §7-4 は開いていない＝データ不足（必読の一覧に無い）。
  - 列（順位・列の名前・種類・時間足・側・分位・前処理・分離力・本数）は、候補1件の鍵11個（gen:6087〜6088）から全部出せる。

修正の番号＝21, 22, 43, 44

### B3 — 完成の条件12行が、8件の直しを全部 覆っているか（優先度 B）

**重さ＝Major**（#8 の扱いは Minor・自分で走らせて貼る扱いは Process）

- **B3-a**：12行と8件を突き合わせた。
  - 不具合 → #1。M-1 → #2（1本目だけ）。M-2 → #3。M-3 → #4（A1 で成り立たない）。M-4 → #5（A2 で種に依存）。M-6 → #6。M-5 → #8（機械の確認なし）。
  - **M-7 は、コードの説明の文を覆う行が無い**（#12 は段の文書と R5 の注意だけ）。
  - M-7 の直す場所は設計書に書かれず、worklog §35 に書かれている（設計書 638行・元データ 346行）。
- **B3-b**
  - #8・#10・#12 は承認のプログラムが走らせない（approve_impl.sh:480〜481）。
  - CC が自分で走らせて貼った出力は、恒久64番（CC は自分の測定結果を「直った」の根拠にしない）に照らすと根拠にならない。この扱いは Process（修正 31・32）に書いた。
  - #9 は、#1・#2・#4・#6 と同じコマンドなので、そちらが済になれば承認のプログラムが rc=0 を測ったことになる。
  - #11 は `（既存の恒等の仕組み）` が括弧ごと消えて名前が空になり（run_breaks.py:172）、済にならない。
  - #8 の「恒久71番＝読むための口は壊すプログラムを作らない」は、71番の線引き表と合わない。regime_r9_diag.py は `scripts/priority_rebuild/*.py` で、表では「いままでどおり」の側（permanent_rules.md:387）。
- **B3-c**
  - b78・b82（新しい形）・b94・b95・b98 は、条件の文そのものを壊している。
  - b96 は T24⑤ が土台で落ちるので、壊す意味が無い（A1）。
  - b97 は種の引きに依存する（A2）。

修正の番号＝23, 24, 29, 30, 31, 32, 45, 46

### B4 — 自己テストの時間が、承認の打ち切り（600秒）に収まるか（優先度 B）

**重さ＝Major**（「3回の実測」と書いた誤りは Process）

- 秒数の実測は無い。記録は、2026-09-11 に424秒（run_breaks.py:65〜66）、監査 cp36 の写しで301秒（T24⑤・T42・T35 を足す前）、98回目は見込みの約8分半（worklog §28）で、§29 に秒数は無い。
- 設計書 4-14 は「98回目の3回の実測」と書いているが、事実と違う（元データ 254行）。同じ見込みの秒数は元データの 333・335・347・348 行にも書かれている。
- T42 は束を最大200本組み、T24⑤ は9回×6本組む。そこへ段2c に5分足の候補（組み直しでは10位以降に入る）が加わり、`build_stage_candidates` の一覧が長くなる。
- 秒数はデータ不足（理由：自己テストを走らせられない）。打ち切り600秒に対して、見込み510秒で余裕は90秒。

修正の番号＝25, 26, 33, 34, 47, 48, 49, 50, 51, 52

### B5 — 関数名・行番号・DESIGN_CONTRACT が実物と合うか（優先度 B）

**PASS**

- 7-7 の定義の行（2545・2824・2863）は実物と合う。新設の4関数は実物に無い。
- must_use は名前だけで、文字列を含まない。
- `check_must_use` は impl_functions の全部の .py を見る（verify_design_contract.py:1191〜1197）ので、`main` を regime_r9_diag.py で照らせる。
- 抜けている `stage_candidates` は B2 に書いた。

修正の番号＝なし

### C1 — M-7（説明の文）の線引き（優先度 C）

監査 cp36 §7-5 の13件を実物で数えた。

- **消えたもの 8件**＝#10（`sample_regime_build` の説明は直っている・gen:2867〜2870）、#12〜#18（前の設計書の文。写しの設計書で `int_range_of(limits, "stage_keep_range")`・「9段」・「n_passed」・「上位足7本」は0件）。
- **残っているもの 5件**＝#7（gen:2647〜2650）、#8（gen:2680〜2682）、#9（gen:2204〜2213）、#11（r9:234）、#19（regime_laws.json:654）。
- **設計書が明示して直すもの**＝#19（4-6）と #11（やらないこと1）。#7〜#9 は worklog §35 を参照しているだけ（B3 の修正 23・45 に数えた結果を入れた）。
- 結論に効く「直さないもの」は無い。
- 依頼書 cp36 の B5 の6件はデータ不足（その依頼書は必読に無く、開いていない）。

修正の番号＝なし

### C2 — 1つの工事に入れてよいか（H16）（優先度 C）

- まこさんの決定「Major 7件の修正をする」と恒久65番（監査は1工事1回）により、1工事にするのは決定に沿う。
- 分けるとしたら、R9 の診断の系（不具合・M-4・M-5）／段の読み口の系（M-1・M-3）／壊すプログラムの系（M-2・M-6）／説明の文（M-7）の4つ。直す指示は出さない。

修正の番号＝なし

### D1 — 「やらないこと」10件（優先度 D）

- 7番（入口の乱数を消さない）は M3 の順番どおりで、それ自体は正しい。
- ただし、その乱数を完成の条件 #5 に使っている点は A2 の Critical に書いた。
- ほかの9件で、問い1 の答えを変えるものは無い。

修正の番号＝なし

省いた問い＝無し（B2-c・C1 の一部はデータ不足として書いた）。


## 5. 外部検索

### 検索 1 — mutation testing で、壊した変更（mutant）を「狙ったテストが落ちたから殺した」と判定する方法

- https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/
  - 「When at least one test failed while this mutant was active, the mutant is killed.」
  - 「The test is covering mutants, but not killing any of them.」
- https://raw.githubusercontent.com/stryker-mutator/mutation-testing-elements/master/packages/report-schema/src/mutation-testing-report-schema.json
  - killedBy：「The test ids that killed this mutant. It is a best practice to "bail" on first failing test, in which case you can fill this array with that one test.」
  - statusReason：「In the case of a killed mutant, this should be filled with the failure message(s) of the failing tests.」
- 当てはめ：殺したことの帰属は「落ちたテストの id」と「その失敗の文」で記録するのが業界の形。EXPECT_MSG を「❌ T番号」にするのはこの形に合う。ただし記録は最後の1行（run_breaks.py:302）だけで、b85 の宣言 T39 と実際の T42 の食い違いは、出力全体への部分一致（run_breaks.py:250）で見逃された。

### 検索 2 — 設定ファイルの検証で、知らない鍵・範囲の外の値を読み込みの時点で止める作り

- https://json-schema.org/understanding-json-schema/reference/object
  - 「By default any additional properties are allowed.」
  - 「Setting the `additionalProperties` schema to `false` means no additional properties will be allowed.」
- https://docs.python.org/3/reference/expressions.html
  - 「the following values are interpreted as false: `False`, `None`, numeric zero of all types, and empty strings and containers (including strings, tuples, lists, dictionaries, sets and frozensets).」
  - 「The expression `x or y` first evaluates _x_; if _x_ is true, its value is returned; otherwise, _y_ is evaluated and the resulting value is returned.」
- https://www.inspiredpython.com/article/truthy-and-falsy-gotchas
  - 「The mistake here is coalescing two distinct conditions (`None` and `0`) and treating them as though they were one.」
- 当てはめ：知らない鍵を止めること（4-5）は additionalProperties: false と同じ考えで PASS。`lim_s.get("quantiles") or [None]` は、空の配列と「欄が無い」を1つに潰す形で、M-1 の `drop_tfs` の不具合と同じ型。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

確かめた（jq の再構成）。5分足の最初の候補は段2a の4位で、案0〜5 の束は変わらない。期待「9件とも変わる」は満たせない（Critical・A1）。

### 自己申告 2

データ不足（写しを作れない）。種7 に需給が入るかどうかは入口の乱数の引きで決まるので、完成の条件にしてはいけない形（Critical・A2）。固定のレシピで測る形に直す（修正 3〜10・41・42）。

### 自己申告 3

申告のとおり書かれていない。`print_stage_candidates` も数える範囲の外（Major・A5）。

### 自己申告 4

申告のとおり。`--lint-expect` は凍結の照合より前に置く必要がある（Major・B1）。承認の前に CC が確かめる道は無い（Process・修正 31）。

### 自己申告 5

#8・#10・#12 は承認のプログラムが走らせない。CC の出力は恒久64番で根拠にならない（Process・修正 31）。#9 は同じコマンドの #1・#2・#4・#6 で機械が測る。#11 は済にならない。

### 自己申告 6

記録（worklog §37）と一致した。再実行はデータ不足（hook と書き込みのため）。あわせて、4-14 の「98回目の3回の実測」は誤りと分かった（Process・修正 33）。

### 自己申告 7

受け取った。この結果を見てから承認①を頼むこと。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝8件とも、直し方の向きは指摘の本体に向いている。不具合 → `_mat_key` の枝（exec:2029〜2031 の欠落を直す）。M-1 → 設定を読む口。M-2 → ❌ の宣言と数える口。M-3 → 法則から読む。M-4 → 需給の列と rc。M-5 → 候補の口。M-6 → abs を付ける行を壊す。M-7 → 説明の文。M-3 のうち C4 の当て方（A3）は直しが要るが、「直書きをやめて出どころから読む」という向きは同じ）
- 問い2 ＝ NO（根拠＝Critical 2件。① T24⑤ の期待が、正しく作っても満たせない（A1）ので #4・#9 などが済にならない。② 完成の条件 #5 と b97 が乱数の引き（種7）に依存し、リスク4 が種を探す手順を定めている（A2・前提2）。ほかに、置き場所・空の配列・2本目の測り・M-7 の覆いが Major）

### 結論と件数

- 結論＝CONDITIONAL-GO
- Critical＝2（所見 A1・A2 ／ 修正の件数 18＝修正 1〜10・35〜42）
- Major＝8（所見 A3・A4-a・A4-b・A5・B1・B2・B3・B4 ／ 修正の件数 26＝修正 11〜26・43〜52）
- Minor＝2（所見 A4-c・B3 の #8 と恒久71番 ／ 修正の件数 6＝修正 27〜30・53・54）
- Process＝2（自分で走らせて貼る扱い・「3回の実測」の誤記 ／ 修正の件数 4＝修正 31〜34）

★修正の件数には、設計書を作り直すコマンドの件を含む（元データの直し1件ごとに、作り直すコマンド1件）。


## 8. 修正の指示

★作り直すコマンドの件（修正 2・4・6 ほか）は、状態をすべて「未決」にした。理由＝`gen_acceptance.py` は `acceptance_src.json` を ratchet の元データから読み（gen_acceptance.py:97）、この監査の相手である cp37r_work の写しを読まない。どの版の元データに当てて作り直すかは、まこさんが決める。

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 356
直す前の文字:
~~~
9件とも束が変わる（組めなくなるものを含む））", "コマンド"
~~~
案A 直した後の文字:
~~~
9件とも、案0〜5 の束か、段ごとの候補の一覧（build_stage_candidates の戻りの col・tf・rank の並び）の少なくとも一方が変わる（組めなくなるものを含む）。★C4 は段2a の一覧に5分足が入ることで測る＝監査 cp37r の再構成では、5分足の最初の候補は段2a の4位で、案0〜5 が使う1位・2位の束は変わらないため）", "コマンド"
~~~
案B 直した後の文字:
~~~
8件（C6・R1・R3・R4・R5・R6・R7・R8）は束が変わる（組めなくなるものを含む）。C4 は束の単位で数える法則（engine_tuner_exec.py の _law_count が束の全部の部品の時間足を数える）なので、組む側は束を組んだ後に C4 の本数を満たすかを確かめ、満たさなければ SampleError にする。T24⑤ は C4 の本数を束の部品の数より大きくした写しで、組めなくなることを測る。段2a の執行足より上の絞りは C4 ではなく §2.2 の段2a の文「時間足は上位足」を出どころにして段の元データから読む）", "コマンド"
~~~
根拠の抜き書き: engine_tuner_gen.py:6278「        _N45 = 6」
状態: 案が複数

#### 修正 2
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝土台ゲートが止めたため秒数なし。この道具は cp37r_work の写しでなく ratchet の元データを読む）
状態: 未決

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 357
直す前の文字:
~~~
"AUDIT-5＝R9 の診断が、入口に需給が入る種でも束を3本とも測り、rc=0（測れない束があれば rc=1）", "コマンド": "python3 scripts/priority_rebuild/regime_r9_diag.py --build 3 --no-trades --seed 7", "経路": "実経路", "壊し方": "需給の列を足す行を消すと、3本とも「測れない」になり rc=1 を返す"
~~~
直した後の文字:
~~~
"AUDIT-5＝R9 の診断が、入口に需給の材料を持つ固定のレシピでも束を測り、rc=0（測れない束があれば rc=1）。★レシピは scripts/priority_rebuild/recipes/r9_demand_fixture.json の1本（入口の条件に需給の材料 taker_ls を持ち、判定の束は sample_regime_build の order_n=0 の出力を写したもの）＝種と乱数に依らない", "コマンド": "python3 scripts/priority_rebuild/regime_r9_diag.py --recipe scripts/priority_rebuild/recipes/r9_demand_fixture.json --no-trades", "経路": "実経路", "壊し方": "需給の列を足す行を消すと、固定のレシピの束が「測れない」になり rc=1 を返す（EXPECT_MSG＝時間足が無い: taker_ls）"
~~~
根拠の抜き書き: regime_r9_diag.py:261「            rng = np.random.default_rng([a.seed, 1, tries])」
状態: 確定

#### 修正 4
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 231
直す前の文字:
~~~
regime_r9_diag.py --build 3 --no-trades --seed 7` が3本とも ①③ の数字を出し、rc=0。
~~~
直した後の文字:
~~~
regime_r9_diag.py --recipe scripts/priority_rebuild/recipes/r9_demand_fixture.json --no-trades` が、入口に需給の材料を持つ固定のレシピの束で ①③ の数字を出し、rc=0。
~~~
根拠の抜き書き: regime_r9_diag.py:232「    ap.add_argument("--recipe", default=None, help="判定の束を持つレシピ（json）")」
状態: 確定

#### 修正 6
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 336
直す前の文字:
~~~
実装のあと、種 7 の入口に需給が在ることを確かめる。無ければ需給が入る種を探して、設計書の条件のコマンドを直してから承認を頼む
~~~
直した後の文字:
~~~
種を探して選ぶことはしない（種の引きで完成の条件の合否が決まる形になるため）。条件のコマンドは、入口に需給の材料を持つ固定のレシピ（recipes/r9_demand_fixture.json）を測る
~~~
根拠の抜き書き: acceptance_src.json:61「    "とにかくランダム、乱数、偶然による構築、選出はやめてほしい。（2026-09-10）",」
状態: 確定

#### 修正 8
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 41
直す前の文字:
~~~
".claude/breaks/b98_qkey_abs_missing.sh"
~~~
足す文字:
~~~
,
    "scripts/priority_rebuild/recipes/r9_demand_fixture.json"
~~~
根拠の抜き書き: regime_r9_diag.py:249「        recipes.append(json.loads(pathlib.Path(a.recipe).read_text(encoding="utf-8")))」
状態: 確定

#### 修正 10
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 35
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 233
直す前の文字:
~~~
T24⑤（9件とも変わる）の行。
~~~
案A 直した後の文字:
~~~
T24⑤（9件とも、案0〜5 の束か段ごとの候補の一覧の少なくとも一方が変わる）の行。
~~~
案B 直した後の文字:
~~~
T24⑤（8件は束が変わり、C4 は本数を束の部品の数より大きくした写しで組めなくなる）の行。
~~~
根拠の抜き書き: engine_tuner_gen.py:6339「        _expect45 = {"C4": False, "C6": True, "R1": True, "R3": False, "R4": True,」
状態: 案が複数

#### 修正 36
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 37
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 245
直す前の文字:
~~~
C4 と R3 も「変わる」になる（9件とも変わる）
~~~
案A 直した後の文字:
~~~
C4 と R3 も「変わる」になる（9件とも、束か段ごとの候補の一覧の少なくとも一方が変わる。C4 は段2a の一覧に5分足が入ることで測る）
~~~
案B 直した後の文字:
~~~
R3 は「変わる」になる。C4 は束の単位の本数の検査を足し、本数を大きくした写しで組めなくなることで測る（9件とも変わる）
~~~
根拠の抜き書き: engine_tuner_gen.py:6339「        _expect45 = {"C4": False, "C6": True, "R1": True, "R3": False, "R4": True,」
状態: 案が複数

#### 修正 38
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 39
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 380
直す前の文字:
~~~
T24⑤ の期待（9件とも変わる）は、C4 と R3 を読む形にしたことから決まる期待で
~~~
案A 直した後の文字:
~~~
T24⑤ の期待（9件とも、束か段ごとの候補の一覧の少なくとも一方が変わる）は、C4 と R3 を読む形にしたことから決まる期待で
~~~
案B 直した後の文字:
~~~
T24⑤ の期待（8件は束が変わり、C4 は本数を大きくした写しで組めなくなる）は、R3 を読む形と C4 の束の単位の検査から決まる期待で
~~~
根拠の抜き書き: engine_tuner_gen.py:6339「        _expect45 = {"C4": False, "C6": True, "R1": True, "R3": False, "R4": True,」
状態: 案が複数

#### 修正 40
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 41
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 100
直す前の文字:
~~~
R9 の診断が需給の入る種でも3本とも測れること
~~~
直した後の文字:
~~~
R9 の診断が、入口に需給の材料を持つ固定のレシピ（recipes/r9_demand_fixture.json・種と乱数に依らない）の束を測れること
~~~
根拠の抜き書き: regime_r9_diag.py:261「            rng = np.random.default_rng([a.seed, 1, tries])」
状態: 確定

#### 修正 42
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

### Major

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 148
直す前の文字:
~~~
lim_s.get(\"quantiles\") or [None]
~~~
直した後の文字:
~~~
(lim_s[\"quantiles\"] if \"quantiles\" in lim_s else [None])
~~~
根拠の抜き書き: engine_tuner_gen.py:2609「    _drop_tfs = limits.get("drop_tfs") or ["1m", "3m", "10m"]」
状態: 確定

#### 修正 12
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 13
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 172
直す前の文字:
~~~
承認済みの分位の範囲の外・重複 | `SampleError` |",
~~~
足す文字:
~~~

      "| `tfs`・`families`・`quantiles` が空の配列・null・配列でない形 | `SampleError`（欄を書いたのに中身が空のとき、既定に黙って戻さない。既定を使うのは欄そのものが無いときだけ） |",
~~~
根拠の抜き書き: engine_tuner_gen.py:2609「    _drop_tfs = limits.get("drop_tfs") or ["1m", "3m", "10m"]」
状態: 確定

#### 修正 14
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 354
直す前の文字:
~~~
空の配列にすると10分足が候補に出る）
~~~
直した後の文字:
~~~
空の配列にすると10分足が候補に出る／同じ設定を渡した sample_regime_build の案0〜5 の B・C・G の時間足と分位が、その設定で作った一覧の中だけから来る（段1 の tfs を1本にした設定で、B の時間足がその1本であることを測る））
~~~
根拠の抜き書き: engine_tuner_gen.py:2903「    c1 = build_stage_candidates("stage1", laws, table, tfs, limits)」
状態: 確定

#### 修正 16
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 293
直す前の文字:
~~~
自己テストがその同じ関数を呼ぶ。"
~~~
直した後の文字:
~~~
自己テストがその同じ関数を呼ぶ。★置き場所＝4つとも engine_tuner_gen.py の最上位の関数として `_ranked_material_at` と `default_regime` の間に置く（数える道具 count_builder_literals.py の範囲は START・END の関数名で決まるため）。★regime_r9_diag.py の `print_stage_candidates` はこの道具の数える範囲の外なので、完成の条件 AUDIT-7 の文の「新設の読み口」はこの4つだけを指す。"
~~~
根拠の抜き書き: count_builder_literals.py:53「START = "_ranked_material_at"     # 範囲の始まり（この関数を含む）」
状態: 確定

#### 修正 18
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 138
直す前の文字:
~~~
で始まらなければ、その名前を出して rc=1 |
~~~
直した後の文字:
~~~
で始まらなければ、その名前を「❌ <壊すプログラムの名前>」の形で出して rc=1。★対象の判定＝その .sh の `measure` で始まる行に `--selftest` の語があるもの。★置き場所＝`main` の中で `--parse-only` と同じく、凍結の照合（check_frozen）と呼び合いの深さの判定より前（b95 は b77 を書き替えた状態で深さ1 から呼ばれるため、後ろに置くと rc=2 で止まるか照合だけで戻る） |
~~~
根拠の抜き書き: run_breaks.py:388「    ng = check_frozen()」
状態: 確定

#### 修正 20
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 21
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 137
直す前の文字:
~~~
照らす欄に足し、戻りに入れる |",
~~~
足す文字:
~~~

      "| `stage_candidates`（案を作るプログラム・段の元データを読む口） | `expand_stage` の戻りを段ごとに写す | 写す鍵に `law_tf` を足す（足さないと `stage_tfs_of`・`stage_lineages_of` が `law_tf` を読めない）。DESIGN_CONTRACT の impl_functions にも足す |",
~~~
根拠の抜き書き: engine_tuner_gen.py:2517「                "law_width": _s.get("law_width"),」
状態: 確定

#### 修正 22
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 23
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 300
直す前の文字:
~~~
監査の別枠 S-6 と同じ型を繰り返さない）。"
~~~
直した後の文字:
~~~
監査の別枠 S-6 と同じ型を繰り返さない）。★直す説明の文は次の6か所（関数と鍵の名前で指す）＝engine_tuner_gen.py の場面の判定の束の節の頭のコメント（D 上位足・n は範囲）／`build_stage_candidates` の中の「材料は `_mat_drawn`…乱数を外すのは手順9」のコメント／`_material_for_lineage` の説明の文／regime_r9_diag.py の `--seed` の help／regime_laws.json の R5 の注意の3つ目／b81 の MEANS。直した後、この6か所の古い語が grep で0件であることを出力で示す。"
~~~
根拠の抜き書き: engine_tuner_gen.py:2648「        #   ★乱数を外すのは手順9（完成の条件 AUDIT-3・AUDIT-5）＝5つの枠をまとめて直す。」
状態: 確定

#### 修正 24
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 25
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 333
直す前の文字:
~~~
いま約8分半。足す T43・T44 は数秒の見込み。
~~~
直した後の文字:
~~~
いまの秒数は実測が無い（98回目の約8分半は見込み・2026-09-11 の実測は424秒・監査 cp36 の写しは301秒＝どれも T24⑤・T42・T35 を足す前）。実装の前に、いまの版で1回 測って秒数を貼る。足す T43・T44 と、段2c の5分足で増える分も、実装のあとに測る。
~~~
根拠の抜き書き: run_breaks.py:67「TIMEOUT_SEC = 600」
状態: 確定

#### 修正 26
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 43
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 406
直す前の文字:
~~~
"stage_counts", "sample_regime_build", "selftest"
~~~
直した後の文字:
~~~
"stage_counts", "sample_regime_build", "selftest", "stage_candidates"
~~~
根拠の抜き書き: engine_tuner_gen.py:2517「                "law_width": _s.get("law_width"),」
状態: 確定

#### 修正 44
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 45
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 346
直す前の文字:
~~~
監査 §7-5 と worklog 20260914 §35 に在る
~~~
直した後の文字:
~~~
監査 cp36 §7-5 の #7〜#9・#11・#19 と b81 の MEANS の6か所（名前は「組み方」の M-7 の行に書いた）
~~~
根拠の抜き書き: regime_r9_diag.py:234「    ap.add_argument("--seed", type=int, default=53, help="閾値の分位・続く長さ（範囲で探す値）の種")」
状態: 確定

#### 修正 46
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 47
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 335
直す前の文字:
~~~
1本 約8分半＝約1時間40分
~~~
直した後の文字:
~~~
1本 約8分半は見込みで実測なし＝実装の前に測った秒数×12本で置き替える
~~~
根拠の抜き書き: run_breaks.py:66「#   実測が **7分4秒（424秒）**（2026-09-11 20:40:37〜20:47:41）。120 では必ず打ち切られます。」
状態: 確定

#### 修正 48
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 49
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 347
直す前の文字:
~~~
自己テスト1回 約8分半 × 約16回
~~~
直した後の文字:
~~~
自己テスト1回 約8分半（見込み・実測なし）× 約16回
~~~
根拠の抜き書き: run_breaks.py:66「#   実測が **7分4秒（424秒）**（2026-09-11 20:40:37〜20:47:41）。120 では必ず打ち切られます。」
状態: 確定

#### 修正 50
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 51
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 348
直す前の文字:
~~~
8回 × 約8分半＋速いもの
~~~
直した後の文字:
~~~
8回 × 約8分半（見込み・実測なし）＋速いもの
~~~
根拠の抜き書き: run_breaks.py:66「#   実測が **7分4秒（424秒）**（2026-09-11 20:40:37〜20:47:41）。120 では必ず打ち切られます。」
状態: 確定

#### 修正 52
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

### Minor

#### 修正 27
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 120
直す前の文字:
~~~
材料1つにつき候補が2件（分位の順）になります。
~~~
直した後の文字:
~~~
材料1つにつき候補が2件（分位の順）になります。★このとき、案の番号の順位（regime_draw_order の B・C・G）と `stage_keep_range` の上位の本数は「材料×分位」の数え方になり、1位と2位が同じ材料の分位違いになる。
~~~
根拠の抜き書き: engine_tuner_gen.py:2808「    if r > int(keep):」
状態: 確定

#### 修正 28
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 29
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 360
直す前の文字:
~~~
この行だけの壊し方は無い（恒久71番＝読むための口は壊すプログラムを作らない）
~~~
直した後の文字:
~~~
この行だけの壊し方は無い（恒久71番の線引き表では scripts/priority_rebuild/*.py はいままでどおり壊すプログラムで守る側にある。この口は画面に出すだけで、壊すプログラムを付けない扱いは まこさんが決める）
~~~
根拠の抜き書き: permanent_rules.md:387「    | **売買のロジック・審判・材料・法則に触るもの**（`scripts/priority_rebuild/*.py`・`regime_laws.json`・`indicator_switch.json`・`material_ranking.json` ほか） | **いままでどおり。**壊すプログラムで守る・完成の条件に載せる・監査に出す |」
状態: 未決

#### 修正 30
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 53
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 207
直す前の文字:
~~~
| 解決表 | 鍵が1種類 増える | 「abs:列の名前」 |",
~~~
足す文字:
~~~

      "| 段の候補の一覧の順位（`stage_limits.<段>.quantiles` を2つ以上書いたとき） | 意味が変わる | 順位と `stage_keep_range` の上位の本数を「材料×分位」で数える。1位と2位が同じ材料の分位違いになり得る |",
~~~
根拠の抜き書き: engine_tuner_gen.py:2808「    if r > int(keep):」
状態: 確定

#### 修正 54
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決


## 9. CC プロセス欠陥対策

### Process

#### 修正 31
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 382
直す前の文字:
~~~
今回は、条件のコマンドを自分で走らせて出力を貼ってから承認を頼みます。
~~~
直した後の文字:
~~~
壊すプログラムの無い行（#8・#10・#11・#12）の条件のコマンドは、承認のプログラムが走らせない（approve_impl.sh の「壊すプログラムの欄が空」の枝）。CC が自分で走らせた出力は「直った」の根拠にしない（恒久64番）。★CC の Bash は run_breaks.py を --measure-only・--selftest 以外で走らせられない（require_acceptance_before_impl.sh の通す条件）ので、--lint-expect は承認の前に CC が確かめられない。これらの行の第三者の確認を実装の監査で行うかは まこさんが決める。
~~~
根拠の抜き書き: require_acceptance_before_impl.sh:249「                and ('--measure-only' in _toks or '--selftest' in _toks)」
状態: 未決

#### 修正 32
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決

#### 修正 33
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/design/acceptance_src.json
直す箇所: 254
直す前の文字:
~~~
自己テスト1回＝約8分半（98回目の3回の実測・worklog 20260914 §29）。
~~~
直した後の文字:
~~~
自己テスト1回＝秒数の実測なし（98回目の約8分半は見込み＝worklog 20260914 §28。§29 の3回目の記録に秒数は無い）。
~~~
根拠の抜き書き: session_worklog_20260914.md:24「- 自己テスト3回目（T42 に「記録の上位が本物の一覧の本数から出る値と一致」を足した版）＝✅ 全部 pass・rc=0。T42 の行＝「案 40本／一覧と合わない・外す時間足・abs 無し・keep の食い違い＝0件／向きを持つ C 22件」。」
状態: 確定

#### 修正 34
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: gen_acceptance.py:97「SRC = RATCHET / "acceptance_src.json"」（監査は走らせていない＝秒数なし）
状態: 未決


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 10-1 開いたもの（Plan エージェントが Read tool と、読み取りの sed・grep・jq で開いた）

- 依頼書 全文 1〜494行
- 設計書の写し acceptance.md 全文 1〜1130行
- 元データの写し acceptance_src.json 全文 1〜431行
- 監査 cp36 レポート 全文 1〜408行
- engine_tuner_milestones2.md 150〜196行・374〜406行・1011〜1100行
- regime_laws.json C4 423〜446行・R1 546〜571行・R3 594〜620行・R5 643〜695行
- m2_stage_candidates.json 全文 1〜106行／search_limits.json 40〜54行
- engine_tuner_gen.py 419〜478行・540〜584行・1005〜1030行・1120〜1164行・1285〜1412行・2200〜2239行・2290〜2319行・2320〜3009行・3014〜3163行・3304〜3468行・4075〜4104行・5990〜6474行・7025〜7038行
- engine_tuner_exec.py 410〜515行・526〜615行・1276〜1350行・1940〜2039行・3120〜3164行
- regime_r9_diag.py 全文 1〜281行
- .claude/tools/run_breaks.py 全文 1〜660行
- .claude/breaks/lib.sh 全文・b77・b81・b82・b93 全文／EXPECT_MSG の行（b76〜b93 の grep）
- count_builder_literals.py 全文 1〜150行
- gen_regime_kb.py 1004〜1085行・1370〜1411行
- approve_impl.sh 446〜503行（ほか TIMEOUT_SEC の grep）
- require_acceptance_before_impl.sh 216〜249行
- require_design_contract_before_run.sh 1〜80行
- permanent_rules.md 157〜207行・348〜395行／engine_tuner_requirements.md 40〜53行
- verify_design_contract.py 1180〜1250行
- acceptance_archive/m2e2-cp36-critical-20260913.breaks.json 全文
- session_worklog_20260914.md 1〜150行・222〜281行
- signal_families.json（timeframes・role_lineage・insufficient_samples の jq）
- material_ranking.json（jq で env／強さ・sufficiency を読んだ）

### 10-1b 結果を写したセッションが開いたもの（引用した行が実物と合うかを確かめた）

- engine_tuner_gen.py 2199〜2214行・2369〜2383行・2500〜2522行・2604〜2685行・2800〜2813行・2862〜2908行・3024〜3034行・3130〜3142行・6082〜6092行・6134〜6144行・6273〜6344行
- engine_tuner_exec.py 605〜615行・1279〜1333行・2024〜2034行
- regime_r9_diag.py 127〜266行
- .claude/tools/run_breaks.py 60〜72行・167〜177行・245〜307行・348〜405行
- count_builder_literals.py 48〜58行／gen_acceptance.py 92〜102行
- approve_impl.sh 475〜485行／require_acceptance_before_impl.sh 244〜254行
- permanent_rules.md 382〜392行／regime_laws.json 649〜659行
- cp37r_work/design/acceptance_src.json 56〜66行／verify_design_contract.py 1186〜1197行／session_worklog_20260914.md 19〜29行
- 結果：8 の修正の指示の根拠の抜き書きと、4 の所見で引いた行は、どれも実物と1文字も違わなかった

### 10-2 走らせたコマンドと結果

| コマンド | 結果 | 秒 |
|---|---|---|
| `shasum -a 256 …/cp37r_work/design/acceptance.md` | 0c692abf…d2d9（一致） | 計測なし |
| `grep -o "__${tf}\"" material_ranking.json` を時間足ごとに数えた | 5m の列 4,308件（在る） | 計測なし |
| jq と awk による段2a の再構成（env／強さ・R5∩§2.2 の7種・中央値・禁止の組） | 1位 MACDヒスト%×30m／2位 ADX×1h／3位 ADX×2h／4位 MACDヒスト%×5m（5分足の最初） | 0.179（time の出力） |
| jq で5分足の env／強さ の列のうち \|acc−0.5\|>0.0375 を抜き出す | 32本。R5 と §2.2 の family は0本 | 計測なし |
| jq と awk による段2c の再構成（全札・R6∩§2.2 の5種・1m/3m/10m を除く） | 1位 stdev%×30m／2位 BB幅×30m／5分足の最初は10位 | 計測なし |
| grep 各種（コード・元データの目印の行・EXPECT_MSG・call site） | 所見に使った行のとおり | 計測なし |
| WebSearch 2回・WebFetch 5回 | 5 に逐語 | 計測なし |
| 結果を写したセッションの `grep -n -F`（修正 1・3・5・7・9・11・13・15・17・19・21・23・25・27・29・31・33 の直す前の文字、17本） | 17件とも元データの1行だけに当たった（行 356・357・231・336・41・148・172・354・293・138・137・300・333・120・360・382・254） | 計測なし |
| 結果を写したセッションの `grep -n -o -F '9件とも'`・`'--seed 7'` | 「9件とも」＝233・245・356・380 行／「--seed 7」＝231・357・378 行。抜けていた行を Plan エージェントに伝え、修正 35〜54 を足させた（378 行は走らせた記録なので対象外） | 計測なし |
| Plan エージェントの `grep -n -F`（修正 35〜54 の直す前の文字） | 10件とも元データの1行だけに当たった（233・245・380・100・406・346・335・347・348・207 行） | 計測なし |
| `python3 .claude/tools/gen_audit_docs.py result <依頼書> cp37r_work/cp37r_result.md` | 骨組みを作った（節 11・問い 13・事実データ 1・外部検索 2・自己申告 7） | 計測なし |
| `git status --short` | 11 のとおり | 計測なし |

### 10-3 走らせられなかったものと理由

- **写しの作成と、写しでの走行（A1-a・A2-a・A3-b）**：Plan エージェントは読み取り専用の設定で起動されたため、ファイルを作れない。A1-a は jq の再構成で代わりに測った（写しでの実行ではない）。A2-a・A3-b はデータ不足。
- 次のコマンドは、土台ゲート（`require_acceptance_before_impl.sh`）の同じメッセージで止まった。
  - `/usr/bin/time -p python3 .claude/tools/count_builder_literals.py`
  - `/usr/bin/time -p python3 .claude/tools/gen_regime_kb.py --verify`
  - `/usr/bin/time -p python3 .claude/tools/run_breaks.py --parse-only --design …/cp37r_work/design/acceptance.md`
  - `python3 .claude/tools/count_builder_literals.py`
  - 止めたメッセージ（先頭）：「🔒 [土台ゲート・Bash] 強制の土台になるファイルを、Bash で書こうとしています（2026-09-03・監査 cp16 の E-1・Critical）。…★通るもの＝cat・grep・ls・wc・head・tail・diff・shasum・stat・find・awk・sed（-i なし）…」
- `sed -n … scripts/priority_rebuild/engine_tuner_gen.py`：止めたメッセージは「🔒 [設計↔実装ゲート] engine_tuner を指す DESIGN_CONTRACT が1本もありません（fail-closed・2026-08-23・まこさん承認）。走らせようとしたもの: engine_tuner_gen.py」。代わりに Read tool で開いた。
- `cat -n` を `for` でつないだ壊すプログラムの一括表示、`cd && grep …` のつなぎ、`|`・`.claude/breaks` を含む `grep -F -e …` も土台ゲートで止まった（Read tool と、形を変えた grep で開き直した）。結果を写したセッションでも、`for` と `$( )` を使った grep の一括の数え上げが同じゲートで止まったので、1本ずつ走らせ直した。
- `regime_r9_diag.py --build 3 --no-trades --seed 8/7`・`engine_tuner_gen.py --selftest`・`pre_audit_check.py --run`：書き込みを伴う（parquet のキャッシュ・文書の書き直し）ので、読み取り専用の設定では走らせていない。


## 11. 本物のファイルを書き替えていないこと

`git status --short`（結果を写したセッションが、結果ファイルを書く直前に走らせた出力そのまま）

```
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md
?? .claude/settings.json.bak_20260819
?? .claude/settings.json.bak_20260826
?? .claude/settings.json.bak_20260902_implock
?? .claude/settings.json.bak_20260903_a6
?? .claude/settings.json.bak_m2_2_2b
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror_old/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/pristine/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/2026-09-15_m2e2_major_design_cp37r_audit_request.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/cp37r_filled_badverdict_test.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/cp37r_filled_test.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/cp37r_result.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/cp37r_skeleton.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/result_skeleton_work.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/try_h11_badverdict.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37r_work/try_h11_pass_filled.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

- `M` の5本と、未追跡のファイルのうち `cp37r_work/cp37r_result.md` 以外は、この監査を始める前（セッション開始時の git status）から在ったもの。
- この監査で増えたのは、作業場の `cp37r_work/cp37r_result.md`（結果の骨組みを埋めた写し）だけ。監査の相手・コード・法則ファイル・元データ（本物と写しの両方）は書き替えていない。
- このほかに、git の対象外の置き場へ、このセッションの ToDo のファイル（`.claude/state/sessions/<セッションの id>/session_todo.md` と貼った証拠）を書いた（ToDo ゲートが求めるため）。
- 結果ファイル `.claude/audits/2026-09-15_m2e2_major_design_cp37r_audit_report.md` は、この節を書いたあとに1回だけ書く。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-15_m2e2_major_design_cp37r_audit_request.md request_sha256=e57114a101dabbcd24c43ee3ffd306ada792780b5c6d59789dfdb518d30571ec -->
