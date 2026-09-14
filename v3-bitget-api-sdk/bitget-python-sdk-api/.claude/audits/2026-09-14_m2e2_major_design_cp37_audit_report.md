# 監査レポート CP37 — 監査 cp36 の Major 7件と不具合1件を直す設計書のチェック

- 依頼書＝`SDK/.claude/audits/inputs/2026-09-14_m2e2_major_design_cp37_audit_request.md`（294行）
- 監査の相手＝`.claude/state/acceptance.md`（1,130行・目印 `m2e2-cp36-major-20260914`）
- 設計書のハッシュ値＝`0c692abf392b47e72e657f4ae99169a97b519c60b2118c5ed9b2622c0298d2d9`（監査の最初に `shasum -a 256` で照らし、依頼書の冒頭と同じだった）
- 実施＝2026-09-14・auditor session の CC
- 読む係＝Plan agent 2体（cold start）。前半＝A1・A3・A4・A5 と B2・B5 の該当部分。後半＝A2・B1・B2 の残り・B3・B4・B5 の残り・C1・C2・D1。
  - 2体に渡したもの＝依頼書のパス・§6 の必読・§3 の担当の問い。加えて「本物も写しも書き替えない／写しを書き替える実測は監査役が行う」という作業場の決まりだけ。
  - 2体の結論のうち、このレポートの結論に効くものは、監査役が実物の行で確かめ直した（§11-1 に行を書いた）。
- 実測＝監査役が作業場 `SDK/.claude/audits/cp37_work/` の写しで行った。

`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。行番号は、特に書かない限り本物のファイル（監査の時点）の行。

---

# ★先頭｜A1 と A2 の実測の結果

## A1 の実測＝設計書のとおりに作っても、C4 を書き替えたとき案0〜5 の束は変わらない

**測り方**＝写しの `engine_tuner_gen.py` の本文を読み、メモリの中だけで次の3つのモジュールを作って比べた（`cp37_work/a1_measure.py`・写しのファイルも書き替えていない）。

| 名前 | 中身 |
|---|---|
| g0 | 写しのまま（いまのコード） |
| gN | 1本目の `upper`（5m より後ろ）の絞りを外したもの（A1-a の②） |
| gP | 設計書 4-4 の決まりを当てた**監査の試作**。①段の law_tf（段1＝R3・段2a＝C4）の法則が、場面の「数える部品」に在り、判定の `時間足` が「執行足より上」なら 5m より後ろ。無い段（段2c）と、法則が場面に無いときは絞らない（外す3本は引く）。②段1 の系統＝R1 の系統と、R3 が「かつ」で持つ系統の重なり（空なら SampleError）。★実装ではない。law_tf は元データを書き替えずに、コードの中の小さな対応表で代えた |

**結果（`cp37_work/logs/a1_measure.json`・32秒）**

| 何を | 結果 |
|---|---|
| 段2a の候補の本数（g0 → gN） | 89本 → 103本（増えたのは 5m の14本だけ） |
| 段2a の1位・2位 | **同じ**＝1位 `MACDヒスト%(12,26,9)__30m`（abs 付き）／2位 `ADX21__1h` |
| 5分足の候補が最初に出る順位（gN） | **4位**（`MACDヒスト%(12,26,9)__5m`）。いまの4位 `EMA20傾き%__15m` は5位に下がる |
| T24⑤ と同じ比べ方（案0〜5・ハッシュ値と B の col・C の種類・G の種類）で、g0 の9件 | 変わった＝C6・R1・R4・R5・R6・R7・R8 ／ 変わらない＝C4・R3（いまの自己テストの期待どおり） |
| 同じ比べ方で、gP（設計書の試作）の9件 | 変わった＝C6・R1・**R3**・R4・R5・R6・R7・R8 ／ **変わらない＝C4** |
| gP の R3（系統→ボラ） | 案0〜5 が6本とも「組めない: R1 と R3 の系統が重ならない」＝設計書の読み（A1-c）どおり変わる |
| 段2c の候補（g0 → gP） | 183本 → 213本（5m の30本が入る）。5m の最初は10位 |
| 土台の束 案0〜199 の比較（g0 と gP） | 200本とも組めて、**200本ともハッシュ値が同じ**（段2c の5分足は、案0〜199 の G が使う順位まで上がらない） |

**案の本数を広げた実測（`cp37_work/a1b_scan_n.py 28`・`logs/a1b_scan_n28.json`）**

| 何を | 結果 |
|---|---|
| gP・案0〜27 | **9件とも変わる**。C4 で違ったのは案26・27 だけ（C が `EMA傾き / EMA20傾き%__15m` → `MACDヒスト% / MACDヒスト%(12,26,9)__5m`） |
| g0・案0〜27 | C4・R3 は変わらない（いまのコードは C4 も R3 も読まないので、本数を広げても区別できる） |

**自己テストそのものでの実測**＝写し mirror_p（設計書の試作＋`_mat_key` の abs の枝＋T24⑤ の期待を「9件とも変わる」にしたもの・`cp37_work/setup_proto.py`）で `engine_tuner_gen.py --selftest` を走らせた（`logs/A3b_selftest_proto.out`）。

```
  ❌ T40③-3: stage2c に引いてはいけない時間足が出た: ['5m']
  ❌ T24⑤: 期待と違う: C4=変わらない（期待＝7件 変わる・C4 と R3 は変わらない＝監査 cp36 §2 の実測）
rc=1 sec=319
```

（括弧の中の文は、書き替えていない古い期待の説明の文。落ちた中身は「C4=変わらない」。）

**なぜ変わらないか（コード）**＝`regime_draw_order`（`engine_tuner_gen.py`:2359〜2384）は、案0・1＝(B1,C1,G1)、案2・3＝(1,1,2)、案4・5＝(1,2,1)。T24⑤ は `_N45 = 6`（:6278）なので、C の順位は1位と2位しか使わない。C の順位が4になる最初の案は26番（和6 の組 (1,4,1)）。これは前半の Plan agent がコードから数えた筋道と、監査役の実測（案26・27 で違った）が一致した。

## A2 の実測＝不具合を直した後も、種7 は入口に需給の材料を含む。需給の列を足せば3本とも測れる

**測り方**＝写しの実行器と R9 の診断を import し、メモリの中だけで差し替えて `regime_r9_diag.main()` を `--build 3 --no-trades --seed <種>` で呼んだ（`cp37_work/a2_r9_probe.py`）。束の入口・出口に `{"demand": …}` の材料が在るかを、`measure` に渡るレシピから数えた。

| 差し替え | 種 | 秒 | 終わり方 | 入口の需給（束3本） | 行 |
|---|---|---|---|---|---|
| なし（いまのコード） | 7 | 111.8（初回はデータのキャッシュを作る） | **`KeyError: 'n'`**（`build_qtable` → `_mat_key`） | R9_2 に `taker_ls` | 出ない |
| `_mat_key` に abs の枝だけ | 7 | 10.7 | rc=0 | **R9_2 に `taker_ls`（まだ含む）** | RG-v5 は測れた／R9_0〜2 は3本とも「測れない: [実行器] 材料の名前に時間足が無い: taker_ls」 |
| 同上 | 8 | 13.0 | rc=0 | 無し | 3本とも測れた（①5.30%・1.04%・5.16%） |
| 同上 | 53 | 9.7 | rc=0 | 無し | 3本とも測れた（①は種8 と同じ値） |
| abs の枝＋measure の前に `demand_ok` の需給の列（CVD・L-S比・taker_ls）を足す | 7 | 15.6 | rc=0 | R9_2 に `taker_ls` | **3本とも測れた**（①は種8 と同じ値） |

**読めること**
- 依頼書 §4 の2の不安（直した後に種7 が需給を含まなくなる）は、**いまの写しでは起きなかった**。完成の条件 #5 と b97 は、いまの種7 で意味のある測り方になる（需給の列を消すと3本とも「測れない」になる道を実測で確かめた）。
- 束の ① は種を変えても同じだった（R9_0〜2 の ① が種8・53・7＋需給で一致）。種が効くのは入口の乱数だけ（`regime_r9_diag.py`:261 `np.random.default_rng([a.seed, 1, tries])`）。
- 試作は設計書のとおりの最終の形ではない（段2c の5分足・rc=1 の決まりは当てていない）。ただし A1 の実測で、段2c の5分足は案0〜199 の束を1本も変えなかったので、`validate_drawn` の通り方と `tries` の並びも変わらないと読める（推測）。

---

# 0. 結論

## 0-1 問い1＝この設計書のとおりに作ると、指摘の本体まで閉じるか ＝ **YES**

| 直すもの | 本体を閉じる向きか | 根拠 |
|---|---|---|
| 不具合（`_mat_key` の KeyError） | 閉じる | A2 の実測＝abs の枝だけで KeyError が消え、束3本が測れる（種8・53） |
| M-1（`stage_limits` を読まない） | 閉じる向き（穴は Major M-5〜M-7） | 読む関数を1本目に置き、2本目は1本目の一覧を使う形（`sample_regime_build`:2903〜2958） |
| M-2（EXPECT_MSG が正常な出力にも出る） | 閉じる向き（穴は Major M-9・M-10） | ❌ で始まる文字は正常な出力の行に出ない（`engine_tuner_gen.py`:7031〜7033 が ❌ を付けるのは失敗の行だけ） |
| M-3（時間足の直書き・R3 を読まない） | **組む側は閉じる。測る側（T24⑤）が閉じていない＝問い2 の Critical C-1** | 試作で、R3 は束が変わり、C4 は段2a の一覧が変わる（89→103本）。ただし案0〜5 では束が変わらない |
| M-4（需給の列を足さない・rc=0） | 閉じる | A2 の実測＝需給の列を足すと種7 でも3本とも測れる |
| M-5（候補の一覧の口が無い） | 閉じる | 口と列が決まっている（4-9・4-12） |
| M-6（b82 の壊し方） | 閉じる | 1本目が abs を付ける1行（`engine_tuner_gen.py`:2657）を消す形 |
| M-7（説明の文） | 一部（Major M-14・別枠 S-5） | 照らすコマンドが無い |

**向きは正しい。**「書く場所は作ったが、読む側・照らす側が無い」という型に対し、読む関数を1か所に置き、宣言を数える口を足す形になっている。**NO-GO の理由（直し方の向きが違う）は見つからなかった。**

★ただし、**段2a に C4 を当てる読み方は CC が決めたもので、法則の判定（束全体で上位足の部品が1本）より強い読み方になっている**（Major M-1）。いまの法則のままなら候補は1本も変わらないので、向きを変える指摘ではない。承認の前に まこさんに明示する項目。

## 0-2 問い2＝実物と合っていて、書いたとおりに作れるか ＝ **Critical 1件がある**

- **C-1（A1）**＝完成の条件 #4 の T24⑤「9件とも変わる」は、設計書のとおりに作っても C4 で落ちる。そのため #4・#9 が済にならず、壊すプログラム b96 は壊す前から同じ ❌ が出て何も測らない。

## 0-3 結論＝**CONDITIONAL-GO**（Critical 1件・Major 16件・別枠 6件）

C-1 を直せば実装に入れる。Major 以下は、恒久の決まり65番の1のとおり記録に積む。

| 重さ | 番号 | 一行 | 優先度 |
|---|---|---|---|
| **Critical** | **C-1** | T24⑤ は案0〜5 しか組まないので、C4 を読む形と読まない形を見分けられない（#4・#9・b96 が効かない） | A1・A1-b・B3-c |
| Major | M-1 | 段2a に C4 を当てると法則を強めて読むことになる。§2.2 の段2a の文が直接の出どころ | A3-a |
| Major | M-2 | `stage_lineages_of`（R1 と R3 の重なり）は審査 G7 より強い。そう書いていない | A1-c |
| Major | M-3 | 完成の条件 #5 と b97 が、入口の乱数（種7）の結果に依存している | A2-b |
| Major | M-4 | R9 の診断を rc=1 にする条件が足りない（束が `--build` に届かない・途中の例外） | A2-c |
| Major | M-5 | T43 は1本目の一覧だけを測る。段2b・段3 の鍵の誤りは2本目で黙って通る | A4-a |
| Major | M-6 | 空の配列が黙って既定に戻る道（`quantiles: []`）・止めるのが案ごとで遅い・比べる相手があいまい | A4-b |
| Major | M-7 | 分位を2つ書くと、2本目の順位の「2位」の意味が変わる | A4-c |
| Major | M-8 | 新設4関数の置き場所（数える道具の範囲）を書いていない | A5-a |
| Major | M-9 | `--lint-expect` の置き場所と数える範囲が決まっていない（`--selftest` を測る EXPECT_MSG 無しの古い16本） | B1-a・B1-c |
| Major | M-10 | 12本の EXPECT_MSG の書き替え先が記録から1つに決まらない。例外で落ちた行も「❌ Tnn」に当たる | B1-b・外部検索1 |
| Major | M-11 | 壊すプログラムの目印が動く・2か所に在る（b98・b93・b92・b85・b78）。`lib.sh` に `set -e` が無い。T40③-3 を `stage_tfs_of` から作ると b81 が効かない | B2 |
| Major | M-12 | 触る関数の一覧の抜け（`stage_candidates` の law_tf・`expand_stage`・`run_breaks.py`・閾値の印） | B2・B5 |
| Major | M-13 | 設計書の文だけでは手が止まる所（T43 の中身・T44 の組み立て・`print_stage_candidates` の側・`--candidates` の処理の順） | B2 |
| Major | M-14 | 完成の条件が覆っていない所と、承認で走らない #8・#10〜#12 を誰が走らせるか（恒久64番） | B3 |
| Major | M-15 | 自己テストの秒数「約8分半」は実測でない（写しの実測＝343秒） | B4 |
| Major | M-16 | 1つの工事でよいが、作る順番を書いていない | C2 |
| 別枠 | S-1〜S-6 | §5 に書いた | A3-b・A3-c・A5-b・B2-c・C1・D1 |

★Critical を1件にとどめた理由（重さの付け方が結論を左右するため、先に書く）
- **M-9（数える範囲）**は、後半の Plan agent が Critical 候補とした。監査役は Major とした。理由＝①設計書 2-1 の数え方（b7*・b8*・b9* の EXPECT_MSG）から「EXPECT_MSG を持つもの」を数える意図が読める ②字のとおりに作って16本を違反と数えても、承認で #3 が rc≠0 になり**見える形で止まる**（黙って済にならない）③1文で直る。
- **M-3（乱数への依存）**は、依頼書 §0-4 の2「設計書に乱数が1つでも残る形なら Critical」に当たるかを考えた。監査役は Major とした。理由＝①この設計書は乱数を1つも足さない（新設の関数にも無い）②種が効く入口の乱数は、まこさんが決めた順番で M3 が外すもので、設計書のやらないこと7に理由と出どころつきで書いてある ③いまの種7 で #5 と b97 が意味のある測り方になることを実測した。ただし M3 の後に黙って何も測らなくなる形なので、直し方（固定のレシピ）を書いた。
- **M-11 の b98（目印が2か所）**は、`_material_name` を壊しても「❌ T44」が出うる＝M-2 と同じ型の誤った kill になる。監査役は Major とした。理由＝設計書 4-18 が「関数の名前から数えて、その中の1件だけを壊す」と書いており、その文どおりに作れば起きない。

---

# 1. 優先度 A — 結論を変える

## A1 — 法則 C4 を1件だけ書き替えると、実際に組まれる束が本当に変わるか

### A1-a ＝ **変わらない（実測）＝Critical C-1**

先頭の表のとおり。段2a の1位・2位は5分足を入れても同じで、案0〜5 は C の1位・2位しか使わない。

### A1-b ＝ **直すのは測り方（T24⑤）。期待「C4 も変わる」は残す**

- 期待を「C4 は変わらない」に戻すと、監査 cp36 の M-3 の指摘（C4 を読まない）は測れないままになる（依頼書のとおり）。
- 書き替え方を変えても直らない。`stage_tfs_of` が知っている形は「執行足より上」だけで（設計書 4-4 の②）、C4 をどう書き替えても、動くのは「5m を入れる／入れない」の2通り。5m の候補は4位が最初なので、案0〜5 には出ない。
- 案の本数を固定で28本に増やすと、いまは9件とも変わる（実測）。ただし「5分足が4位」という成績表の中身に依る数字で、成績表が変わると黙って測れなくなる。

**C-1 の直し方（設計書に足すもの）**
1. T24⑤ は、法則1件を書き替えるたびに、土台と写しの両方で段ごとの候補の一覧（`build_stage_candidates("stage1"／"stage2a"／"stage2c", …)`）を作る。
2. 段ごとに、**最初に食い違う順位 k** を機械で探す。
3. `regime_draw_order` を 0 から順に回し、その段の順位（段1＝r_b・段2a＝r_c・段2c＝r_g）が k になる**最小の案の番号 n** を求める（乱数を使わない・数字を作らない）。
4. 案0〜5 に加えて、その n の束を土台と写しの両方で組み、比べる。
5. 一覧も案0〜5 の束も同じなら「変わらない」。
6. 6-2 のリスクに「案0〜5 では C の順位は 1・2 だけ（`regime_draw_order`）」を書く。
7. b96 の期待（❌ T24⑤）は、この直しの後に意味を持つ。

時間＝組む束は1件あたり最大6本（3段×2）増えるだけ。実測の比べ方（案0〜27）でも T24⑤ の部分は約11秒だった。

### A1-c ＝ **正しい（実測）。ただし G7 より強い読み方＝Major M-2**

- 試作では、R3 の系統をボラにすると R1 との重なりが空になり、案0〜5 が6本とも組めなくなった＝「変わる」。
- ただし審査 G7 の `_law_count_and`（`engine_tuner_exec.py`:1288〜1318）は、geo の部品を `g == "any"` なら系統も時間足も見ずに +1 する（:1296〜1302）。R3 の判定は `"geo": "any"`（`regime_laws.json`:610〜617）なので、G7 では帯の幅の部品 A（W%）だけで R3 が満たされる。**組む側は G7 より強い。**「1本の帯の部品が R1 と R3 の両方を満たす」は R3 の注意の逐語（:603）から来る読み方で、機械が読む判定からは出ない。
- **設計書に足すもの**＝§5 の2 に「R3 を帯の枠 B に当てるのは注意の逐語による。G7 は geo の部品でも R3 を満たすので、組む側は G7 より強い」と書く。

## A2 — 需給の材料が入る種で、R9 の診断が本当に3本とも測れるか

### A2-a ＝ **測れる（実測）**

先頭の表のとおり。筋道（実物の行）は次のとおり。
- 束の C の材料は `{"pre": {"op": "abs"}}` だけを持つ（`engine_tuner_gen.py`:2657）。`_mat_key`（`engine_tuner_exec.py`:2023〜2031）は abs が `SINCE_OPS` に無いので `f"{pre['op']}{pre['n']}:{name}"` に落ちて KeyError。KeyError は `SystemExit` の子ではないので、`measure` の `except SystemExit`（`regime_r9_diag.py`:132）を素通りする。
- abs の枝を足すと、需給の列が df に無いとき `build_qtable` が `ex.material_array(df, "taker_ls")` に進み（`engine_tuner_gen.py`:3440〜3450）、`"__" not in full` で RecipeError（`engine_tuner_exec.py`:1958〜1959）。RecipeError は `SystemExit` の子なので `measure` が受け、解決表が1回なので3本とも「測れない」になる（`regime_r9_diag.py`:129〜145）。

### A2-b ＝ **成績を見て種を選ぶ形にはならない。ただし完成の条件が入口の乱数の結果に依存する＝Major M-3**

- `--no-trades` では玉の成績を測らない（`regime_r9_diag.py`:112 `if with_trades`）。①③は束の列から出る。束は `order_n` で決まり種に依らない（実測＝①が種7＋需給・8・53 で一致）。
- 一方で、#5 のコマンド（`--seed 7`）と b97 は「種7 の入口の乱数が taker_ls を引いたか」に依存している。いまは引く（実測）。**入口の乱数を M3 で外すと、#5 と b97 は黙って何も測らなくなる**（98回目の b92 と同じ型）。
- 設計書のリスク4 の「需給が入る種を探す」は、探し方の決まり（何から順に試すか・何を記録するか）が無い。
- **設計書に足すもの（どちらか）**
  - (a) 乱数に依らない形。入口に `{"demand": "taker_ls"}` を持つ固定のレシピを作業に含め、`--recipe` で渡す。または R9 の診断の出力に「入口に需給を持つ束の本数」を出し、#5 の条件を「1本以上 かつ 3本とも測れる」にする。
  - (b) 種を使い続けるなら、「種は 0 から順に試し、3本のどれかの入口に需給が在る最初の種」「①②③は見ない」「試した種を全部記録する」と書く。

### A2-c ＝ **ほかの理由で rc=1 になる道・rc=0 のまま通る道が残る＝Major M-4**

- `measure` が受けるのは解決表の所だけ。`build_regime_columns`（`regime_r9_diag.py`:149）が G5 で拒否すると（有効標本0件で鍵が落ちたとき・`engine_tuner_gen.py`:3462〜3472）、`RecipeError` が `main` の外まで出て、行を出さずに終わる。設計書 4-5 の「全部の行を出したあと rc=1」にならない。
- 需給の元データが読めないと `attach_demand_columns` が RecipeError を出す（`engine_tuner_exec.py`:3158〜3159）。需給を使わない種でも起きる（`demand_ok` を全部足すため）。
- 束が `--build` の本数に届かないとき（`regime_r9_diag.py`:260 `tries < a.build * 20`）は、3本未満のまま rc=0。設計書の「測れない行が1つでもあれば rc=1」では捕まらない。
- `attach_demand_columns` は写しを返す（`engine_tuner_exec.py`:3156 `out = df.copy()`）。戻り値で df を置き替えないと効かない。手本の行（`engine_tuner_gen.py`:4093 `df2 = …`）は置き替えているが、設計書の文には書いていない。
- **設計書に足すもの**＝rc=1 の条件を3つ書く（測れない行・組めた束が `--build` に届かない・途中の例外は行を出してから rc=1）。b97 の EXPECT_MSG を需給の道に固有の文字にする（例「材料の名前に時間足が無い」）。戻り値で df を置き替えると書く。

## A3 — 法則の当て方が、法則を作る・強める・弱めることにならないか

### A3-a ＝ **段1＝R3 と段2c（法則なし）は正しい読み。段2a＝C4 は強めた読み＝Major M-1**

- C4 の判定は「束の中の上位足の部品が本数1」（`regime_laws.json`:441〜444）で、枠を名指ししていない。G7 は束全体の時間足を数える（`engine_tuner_exec.py`:1325〜1329 `n += sum(1 for t in seen["tfs"] …)`）。帯 B は R3 で上位足になるので、C4 は B だけで満たされる。そのうえで段2a（C の枠）にまで C4 を掛けるのは、本数1 を枠ごとの決まりに変える読み方で、設計書が §5 の2で「強めることになる」として捨てた案と同じ型。
- 根拠に挙げた R3 の注意「C4 は部品C（強さ×上位足）で常に満たす」（`regime_laws.json`:603）は、組む側の実測を述べた文で、「C に掛けよ」とは書いていない。
- **段2a を上位足に限る直接の出どころは §2.2 の段2a の文「時間足は上位足（15m〜4h）」**（`engine_tuner_milestones2.md`:187・`m2_stage_candidates.json` の `mako_note`）。C4 に結びつけると、C4 を外したとき段2a に5分足が入る＝§2.2 の文と逆になる（A1 の実測で89→103本）。
- いまの法則のままなら段2a の候補は1本も変わらない（試作の自己テストの T40＝stage2a 89本で同じ）。だから向きを変える指摘ではない。
- **設計書に足すもの（どちらか）**＝(a) 決めてほしいことに「C4 を段2a の枠に当てる読み方でよいか（束全体で1本という判定より強い）」を足す ／ (b) 段2a の時間足は §2.2 の文を出どころにした欄から読み、C4 は束全体で満たされているかを別に確かめる。

### A3-b ＝ **段2c に5分足が入っても、T24② と T42 は変わらない（実測）＝別枠 S-1**

| 何を | 何も変えない写し（`logs/B4_selftest_base.out`） | 設計書の試作の写し（`logs/A3b_selftest_proto.out`） |
|---|---|---|
| T24② 100本 組んで審査を通った本数 | 94本（落ちた6本は全部「R2: 同じ…」） | 94本（同じ内訳） |
| T42 | 案40本・食い違い0件・向きを持つ C 22件 | 同じ |
| T40 の段2c の本数 | 183本 | 213本 |
| 落ちた行 | 無し（✅ 全部 pass） | ❌ T40③-3（段2c の5m）・❌ T24⑤（C4＝変わらない） |

- T40③-3 が落ちるのは、設計書 4-13 が「読み方を変える」と書いている行（いまは段2c にも「5m より後ろ」を直書きで当てている・`engine_tuner_gen.py`:6121〜6127）。
- 段2c の5分足は10位が最初で、案0〜199 の G が使う順位まで上がらない（A1 の実測＝土台の束200本が同じ）。
- ★T40③-3 の直し方の注意は Major M-11 に書いた（期待を `stage_tfs_of` から作ると b81 が効かない）。

### A3-c ＝ **この工事で変えない扱いでよい。ただし出どころの扱いが揃っていない＝別枠 S-2**

§5 の3 は §2.2-3 の逐語を使って段2c を広げる一方、同じ種類の出どころである §2.2 段2a の文「15m〜4h」は「上端を決める法則は無い」（設計書 3-1 の4）を理由に当てていない。やらないこと4 の理由を「§2.2 の段2a の文と違うまま残す（段2c には §2.2-3 の文を当てた）。値は まこさんが決める」に直すとよい。

## A4 — `stage_limits` を読む直しが、候補と実際の束の両方に効くか

### A4-a ＝ **T43 は1本目だけを測る。C-1（cp36）と同じ型が一部に残る＝Major M-5**

- 2本目は同じ `limits` を `build_stage_candidates` に渡す（`engine_tuner_gen.py`:2903・2904・2958）ので、一覧から取る部品には効く見込み。T42 は束と一覧の一致を見るが、動かすのは本物の設定（`stage_limits` が空）だけ（:6367〜6372）。
- 一覧を通らない部品が残る＝帯の幅 A の閾値は `_thr_fixed(limits)` の直書き（:2912〜2913）で、`stage_limits.stage1.quantiles` が効かない。
- 段2b・段3 の鍵の誤りは、1本目では止まるが、2本目では `stage_counts` が `SampleError` を「止まった理由」の欄に入れて先へ進む（:2849〜2854）。`sample_regime_build` は段2b・段3 の一覧を直接作らないので、束は普通に組まれる。
- **設計書に足すもの**＝T43 に2本目の行（`stage_limits` を書いて `sample_regime_build` を組み、B・C・G の時間足と分位が設定の中に在ること／stage2b に鍵を書くと組む時点で止まること）を足す。帯の幅 A に stage1 の quantiles を掛けるかを 4-4 に書く。

### A4-b ＝ **承認済みの範囲を広げる道は塞がれている。黙って既定に戻る道・止まるのが遅い道が残る＝Major M-6**

- 塞がれている＝tfs は ①〜③ の中だけ（設計書 4-4 の④）・quantiles は承認済みの範囲の中・families は §2.2 の元データの中。
- **空の配列が黙って既定に戻る**＝4-4 の擬似コード `qs = lim_s.get("quantiles") or [None]`（設計書 332行）。`quantiles: []` は1点に戻る。これは設計書が `drop_tfs` で直している型そのもの（`engine_tuner_gen.py`:2609 `limits.get("drop_tfs") or [...]`）。`tfs: []`・`families: []` の扱いも書いていない。
- **止めるのが案ごと**＝`SampleError` は呼ぶ側で「この案は作れない」と数えられる。本走 `run_generation` は拒否を数えて引き直し、足りなければ最後に止まる（:4044〜4060）。R9 の診断は20回ずつ「組めない」と出したあと、束0本のまま `measure` へ進んで rc=0（`regime_r9_diag.py`:260〜273）。いまの設定の誤りは読み込みの時点で `SystemExit` の仲間で止めている（例＝`HoldRangeError`・:132〜178）。
- `param_range` を比べる相手が、カタログそのもの（:284〜292）か、まこさんの `material_param_ranges` を当てた後（:293〜302）かを書いていない。
- **外部検索2との照合**＝設定の知らない鍵・誤った値を黙って既定値で通すと、利用者は効いていると思い込む（awslabs/stickler #350＝"A misspelled key builds with no exception and no warning, at the fallback value."）。JSON Schema の `additionalProperties: false` は閉じた形で、知らない鍵は検証で落ちる（既定は許す側）。設計書の「知らない段・知らない鍵は止める」はこの閉じた形に当たる。残る穴は「空の配列を無いと同じに扱う」と「読み込みの時点でなく案ごとに止める」の2つ。
- **設計書に足すもの**＝空の配列は `drop_tfs` 以外すべて止める。`stage_limits` 全体を最初に読む時点で1回照らし、`SystemExit` の仲間で止める（must_use の `stage_limits_of: SampleError` も合わせる）。`param_range` は `material_ranges()` と比べる。

### A4-c ＝ **変わる＝Major M-7**

分位を2つ書くと、材料1つにつき候補が2件並ぶ（設計書 335〜336行）。r_b・r_c・r_g の「2位」が「1位と同じ材料の別の分位」になり、同じ案の本数で試せる材料が半分になる。`stage_keep_of` の「上位1本」も「1位の材料の最初の分位だけ」を意味するように変わる（`engine_tuner_gen.py`:2772〜2792）。T43 が「候補が2倍」を合格にするので、この意味が固まる。**設計書に足すもの**＝(i) 分位を `regime_draw_order` の別の軸にする か、(ii) 平たく並べることを採り、`stage_keep_range` と順位が「材料×分位」を数えると明記する。

## A5 — 乱数と法則番号の直書きが、新しく足す関数に入らないか

### A5-a ＝ **置き場所を書くべき＝Major M-8**

- 数える道具の範囲は、`count_builder_literals.py`:53〜54 の `START = "_ranked_material_at"`・`END = "default_regime"` の間の最上位の文だけ。いまの実物では `engine_tuner_gen.py`:2320〜3003。設定を読む新設関数を `_thr_fixed`（:551）や `_role_tfs`（:1397）の近くに置くと数えられない。
- b78 は `    spec_c = stage_candidates(stage)\n` がちょうど1件あることを求めて、その直後に書き込む。新設関数に同じ行を書くと2件になり、b78 は壊せない（b78 は TARGET の外で直せない）。
- **設計書に足すもの**＝「新設4関数（とそれだけが使う補助）は `_ranked_material_at` から `default_regime` の手前までに置く」「新設関数に `spec_c = stage_candidates(stage)` と同じ行を書かない」。

### A5-b ＝ **法則番号が文字で現れない設計＝問題なし（別枠 S-3）**

4-4 は `laws["counts"]` の番号と `spec_c["law_tf"]` を比べる形で、"C4"・"R3" を書く必要がない。ただし「5m より後ろ」はいま `engine_tuner_gen.py`:2606 と `engine_tuner_exec.py` の `_upper_tfs`（:1280〜1285）の2か所に在る。新設関数にもう1か所書くと3か所になるので、`ex._upper_tfs()` を呼ぶと書くとよい。

---

# 2. 優先度 B — 実装の前に直す

## B1 — EXPECT_MSG の直しと `--lint-expect`

### B1-a ＝ **置ける場所は1つ（凍結の照合より前）。設計書に書いていない＝Major M-9 の前半**

- `run_breaks.py` の `main` の順番（実物 :341〜403）＝`--selftest` → `--parse-only`（読むだけの口・壊すプログラムを走らせない）→ `--freeze` → **凍結の照合**（:388 `check_frozen()`・違えば rc=2）→ **深さの判定**（:400〜403・深さ>0 なら rc=0 で戻る）。
- b95 は b77 を書き替えてから、承認のプログラムの中（深さ1）で `--lint-expect` を走らせる。凍結の照合より後に置くと rc=2（出る行は「❌ 壊すプログラムが承認のときから変わっています」で「❌ b77」を含まない）、深さの判定より後なら rc=0。**`--parse-only` と同じ並び（凍結の照合より前）に置くしかない。**
- CC は承認の前に `--lint-expect` を走らせられない（`require_acceptance_before_impl.sh`:236〜240 は `--measure-only`・`--selftest` だけ通す）。
- **設計書に足すもの**＝「`--parse-only` と同じく凍結の照合と深さの判定より前で return する。違反は1本1行 `❌ <ファイル名>` の形で出す」。承認の前にどう確かめるか（承認で初めて走ると正直に書く／`run_breaks.py --selftest` に見本の .sh で lint を試す番人を足す）。

### B1-b ＝ **書き替え先は、記録からは少なくとも4本（b76・b81・b82・b85）が1つに決まらない＝Major M-10**

- b85 の98回目の承認の記録は、出力の最後の1行だけを残す（`run_breaks.py`:300〜302 `tail[-1]`）。「❌ T42」が最後の行だっただけで、T39 の ❌ が出たかは記録に無い。
- b81 は壊す行が `stage_tfs_of` の中へ移り、T40③-3 の書き方しだいで落ち方が変わる（M-11）。b82 は壊し方が変わるので実測が無い。b76 は `stage_lineages_of` が系統の空をどう扱うかが決まっていない。
- 監査 cp36 §1-1 の表は 98回目の直しの前のコードで測ったもの。
- **外部検索1との照合**＝mutation testing では、test が落ちる理由に assertion の失敗と assertion 以外の失敗（crash など）がある（Du・Palepu・Jones, arXiv 2411.09846 の §III ＝"When a test kills mutants, it can fail by assertions … or non-assertion failures (such as crashes)"）。同論文は test ごと・assertion ごとに kill を数えている。PIT の Killed の定義は「test が変更を捕まえた」だけ。
  - このプロジェクトの自己テストは、例外で止まった行も「❌ T24⑤: 途中で止まった: …」の形で出す（`engine_tuner_gen.py` に「途中で止まった」16か所・:7031〜7033 で ❌ を付ける）。**「❌ T43」は、T43 の判定で落ちたのか、T43 の中の例外で落ちたのかを区別しない**＝test 単位で、assertion 単位ではない。b98 は KeyError（例外）で落ちることを期待しており、ここは意図どおり。
- **設計書に足すもの**＝①書き替え先の出どころを「全部のコードを直した後に、同じ壊し方を当てて出た ❌ の行」に替える ②❌ が複数出たら MEANS が名指しする行を選び、出なければ MEANS を直す ③❌ の行は全部記録に残す（最後の1行だけにしない）④判定の失敗で落ちることを期待する壊すプログラムは、EXPECT_MSG に「途中で止まった」でない判定の文字まで含める（例「❌ T43②」）。

### B1-c ＝ **壊すプログラムの本文の `measure` の行で判定するのが正しい。数える範囲が決まっていない＝Major M-9 の後半**

- 実物（写しの breaks で数えた）＝全88本。EXPECT_MSG を持つ18本。`measure … --selftest`（語がちょうど `--selftest`）を持つ31本。**そのうち EXPECT_MSG を持たないものが16本**＝b28・b29・b34・b36・b41・b42・b44・b48・b52・b54・b59・b62・b66・b67・b72・b73。
- 設計書の文「測るコマンドが `--selftest` の壊すプログラムの EXPECT_MSG が ❌ で始まらなければ違反」を字のとおりに読むと、この16本（凍結されていて TARGET に無い）が違反になり、#3 は rc=0 にならない。
- `match_of` は部分一致（`run_breaks.py`:249〜250）なので、「❌ T2」は「❌ T24②」にも当たる。
- **設計書に足すもの**＝範囲の定義（例「`# EXPECT_MSG:` を持ち、本文に語がちょうど `--selftest` の `measure` の行を持つもの」）。16本を数えない理由（承認では `expect_of` が宣言の無いものを止めるので、そもそも承認で走らない）。

## B2 — 別の人が、この設計書だけを読んで作れるか

### B2-a・B2-b ＝ **作れるが、手が止まる所と、黙って守りが死ぬ所がある**

**Major M-11（壊すプログラムの目印）**
- **b98**＝壊す相手の文字 `in NO_ARG_OPS` は、`_mat_key` より前の `_material_name`（`engine_tuner_exec.py`:610）に既に在る。b93 の本文（`.claude/breaks/b93_law_filter_off.sh`:16〜27）はファイル全体で最初の1件を置き替える形なので、その形を写すと `_material_name` を壊し、abs が G5 で拒否されて、別の理由で「❌ T44」が出る（M-2 と同じ型の誤った kill）。設計書 4-18 の「関数の名前から数えて、その中の1件だけを壊す」を、b98 には必ず当てると書く。
- **b93・b92・b85・b78（TARGET の外）の目印**＝b93 は `if fams_law and fam not in fams_law:` と `if lins_law and …`（`engine_tuner_gen.py`:2628・2631）、b92 は `c1 = …`・`c2a = …` の2行（:2903〜2904）、b78 は `spec_c = stage_candidates(stage)`（:2571）を狙う。4-4 の擬似コードは `lins = stage_lineages_of(...)` と変数名が変わっている。
  - `lib.sh` は `set -u` だけで `set -e` が無い（:19）。b93 は目印が見つからないと python だけが `SystemExit` で止まり、壊さないまま自己テストを走らせる（b93 の本文・監査役が確かめた）。この承認では b93・b92・b85 は走らないので、次に誰かが走らせるまで気づかない。
  - 設計書に足すもの＝「TARGET の外の壊すプログラムが狙う行（上の4か所）の文字を変えない」を 4-13 に書く。
- **T40③-3**＝設計書 4-13 は「時間足と外す時間足を `stage_tfs_of`・`drop_tfs_of` から取る」と書く。期待の集合を `stage_tfs_of` の戻りから作ると、b81 がその関数の中を壊したとき期待も一緒に動いて落ちない（b81 の注記が同じ罠を書いている）。法則の判定と `drop_tfs_of` から独立に作ると書く。

**Major M-12（触る関数の抜け）**
- **`stage_candidates`**＝返す辞書の鍵を選んで写す形（`engine_tuner_gen.py`:2505〜2518）で、`law_tf` を写す行が要る。4-3・7-7・impl_functions に無い。写し忘れると `law_tf` が None になり、`stage_tfs_of` の②が「絞らない」に落ちて、段1・段2a に5分足が黙って入る（C-1 を直した T24⑤ なら捕まる）。
- **分位ごとの閾値と印**＝印 `_q_src` を書いてよいのは `_MARK_WRITERS` の関数だけ（:7313〜7316・`_thr_fixed` は入っている・`build_stage_candidates` は入っていない）。分位を2つ作る所で `_thr_fixed` に引数を足すのか、一覧を広げるのかを書いていない（T25 の静的検査に当たる）。
- **`.claude/tools/gen_regime_kb.py`（`expand_stage`）と `.claude/tools/run_breaks.py`（`main`・新設 `lint_expect`）**は TARGET に在るが impl_functions に無い。照合は `.claude/tools/` の .py も数える（`verify_design_contract.py`:1088〜1095）。
- M-7 の説明の文をモジュールの説明（`engine_tuner_gen.py`:17・22 行・`regime_r9_diag.py`:21〜23 行）で直すと、モジュール直下が変わる。照合との順番を書く。

**Major M-13（設計書の文だけでは手が止まる所）**
- **T43**＝分位を2つ試す段・範囲の外の時間足の具体例・2本目の行が無い（A4-a）。4-5 の止まる9行のうち、families・param_range・stage2b/stage3・drop_tfs の知らない名前が試されない。
- **T44**＝`needed_qkeys` はレシピ（`entry.connective`・`meta.lane` を持つ辞書）を受け取る（`engine_tuner_gen.py`:3375〜3395）。束だけでは呼べないので、`sample_structure(build_regime=True)` を使うか最小のレシピを作るかを書く。何本組むか。KeyError を受ける except が要る（`SystemExit` だけを受けると、b98 で自己テスト全体が traceback で落ち「❌ T44」が出ない）。
- **`print_stage_candidates`**＝段2a の「側」の列に、cond の not の中の強い側（:2659）と法則の側のどちらを出すか。limits に `resolve_hold_range(…, "e38")` を掛けるか。
- **`--candidates`**＝`regime_r9_diag.py`:240〜241 の `ap.error`（`--recipe` か `--build` が要る）とデータの読み込みより前で処理すると書く。

### B2-c ＝ **条件つきで閉じる（別枠 S-4）**

口と列が決まったので、cp35 §7-4 の「候補の一覧を出す口が無い」は閉じる。残り＝#8 は承認で走らない（M-14）。恒久71番は `scripts/priority_rebuild/*.py` を「いままでどおり」の側に置いているので、`regime_r9_diag.py` の口に「壊すプログラムを作らない」を当てるのは71番の文と合わない（読むための口なので結論には効かない）。

## B3 — 完成の条件12行が、8件の直しを全部 覆っているか

### B3-a ＝ **覆っていない所がある＝Major M-14 の前半**

| 直し | 覆う行 | 覆っていない所 |
|---|---|---|
| 不具合 | #1＋b98・#5 | b98 の壊す行（M-11） |
| M-1 | #2＋b94 | 2本目に効くか（A4-a）・`stage_counts` の覚える鍵・空の配列の意味 |
| M-2 | #3＋b95 | ❌ で始まる形だけ。12本の宣言が実際の ❌ と合うかは、承認で走る壊すプログラムが b82 だけなので **11本は機械で測られない** |
| M-3 | #4＋b96 | C4 の道だけ。R3（`stage_lineages_of`）を壊すプログラムが無い。★C-1 を直すまで #4 は済にならない |
| M-4 | #5＋b97 | 種への依存（M-3） |
| M-5 | #8 | 承認で走らない |
| M-6 | #6＋b82 | 覆う |
| M-7 | #12 | 段の文書だけ。コードの説明の文はどのコマンドでも照らさない。#12 も承認で走らない |

### B3-b ＝ **「承認のプログラムは走らせない」は実物どおり。CC が走らせて貼る補い方は恒久64番と合わない＝Major M-14 の後半**

- `approve_impl.sh`:475 `ok_brk = match[no] if no in match else (c not in (0, None))`。壊すプログラムの欄が空の行は code が None なので、:477〜479 で「壊すプログラムが落ちていない」になり、:485 の `_run(cmd)` に届かない。
- **#9 は #1 の済で測られる**＝#9 のコマンドは #1・#2・#4・#6 と同じ `engine_tuner_gen.py --selftest`。:485〜486 は条件のコマンドが rc=0 のときだけ済を書き、自己テストは失敗が0件のときだけ rc=0（`engine_tuner_gen.py`:7031〜7036）。
- 残る #8・#10・#11・#12 を「CC が自分で走らせて出力を貼る」形は、恒久64番（CC は自分の測定を直ったの根拠にしない）に当たる。**実装の監査が写しで走らせる行**と書くのが合う。

### B3-c ＝ **一部の壊すプログラムは、条件の文の一部しか壊さない**

| 壊すプログラム | 条件の文そのものを壊しているか |
|---|---|
| b78 | 一部。挿入するのは `build_stage_candidates` の中だけで、#7 の「新設の読み口」は壊さない（A5-a） |
| b82 | 壊す |
| b94 | 一部。空の配列の意味（`drop_tfs_of`）は壊さない |
| b95 | 壊す（範囲の定義しだい・M-9） |
| b96 | C4 の分だけで R3 の分は壊さない。**C-1 を直すまで何も測らない** |
| b97 | 入口に需給が入る種でだけ壊す（M-3） |
| b98 | 壊す行が `_mat_key` の中に定まれば壊す（M-11） |

## B4 — 自己テストの時間が、承認の打ち切り（600秒）に収まるか ＝ **収まる見込み。設計書の数字は実測に替える＝Major M-15**

| 何を | 秒 | 出どころ |
|---|---|---|
| 何も変えない写しの `engine_tuner_gen.py --selftest` | **343**（rc=0・✅ 全部 pass） | `cp37_work/logs/B4_selftest_base.out`（Plan agent 2体が同時に動いている中・8コア） |
| 設計書の試作の写しの自己テスト | **319**（rc=1） | `logs/A3b_selftest_proto.out` |
| 監査 cp36 の写しの自己テスト／壊した走行 | 301／294〜411 | cp36 §11-3 |
| T24⑤ を案0〜27 に広げた部分（C-1 の直しの大きさの目安） | 約11（`a1b_scan_n.py`・案6本では約3） | `logs/a1b_scan_n28.json` の `sec_t24_5_proto` |

- 設計書の「約8分半」（4-14・6-2・6-3）は、98回目の記録の見込みで、秒数の実測は worklog 20260913・20260914 に無い（後半の Plan agent が grep で確かめた・依頼書 §3 B4 のとおり）。
- 壊した走行は、cp36 で土台の最大 1.37倍（411÷301）だった。343秒×1.37＝約470秒で、600秒の中に収まる。
- T43・T44 の上乗せは、候補の一覧を作る回数（T40 の10回と同じくらい）と束数本で、数秒〜十数秒の見込み（推測）。
- **設計書に足すもの**＝4-14・6-2 の数字を実測（343秒）に替える。リスク3 の確かめのとき、b94・b96・b98・b82 の壊した走行の秒数を1本ずつ記録し、560秒を超えたら報告する。

## B5 — 関数名・行番号・DESIGN_CONTRACT が実物と合うか ＝ **行番号と must_use は合う。impl_functions に抜け（Major M-12 に含めた）**

- 行番号＝`build_stage_candidates` 2545・`stage_counts` 2824・`sample_regime_build` 2863（`engine_tuner_gen.py`）、`_mat_key` 2023（`engine_tuner_exec.py`）、`main` 229（`regime_r9_diag.py`）は実物どおり。新設4関数と `print_stage_candidates` が「実物に無い」も正しい。
- **must_use に文字列は無い**＝`SampleError`・`q_range_of`・`stage_keep_of`・`_stage_pick`・`NO_ARG_OPS`・`SINCE_OPS`・`attach_demand_columns`（属性として数えられる）はどれも名前。
- 抜け＝`stage_candidates`・`expand_stage`・`run_breaks.py` の `main` と `lint_expect`（M-12）。must_use の `stage_limits_of: SampleError` は、M-6 の直し（読み込みの時点で `SystemExit` の仲間）と食い違う。

---

# 3. 優先度 C — 完成の測り方以外の書き漏れ

## C1 — M-7 の線引き ＝ **結論に効く「直さないもの」は無い（別枠 S-5）**

後半の Plan agent が実物で数えた（監査役は grep の件数を確かめ直していない＝§11-4）。

| 出どころ | 件 | 扱い |
|---|---|---|
| 監査 cp36 §7-5 の #7・#8・#9・#11・#19 | 5件 | 直す（#8 の docstring は照合の順番に注意・M-12） |
| 同 #10・#12〜#18 | 8件 | 既に消えた（98回目の設計書の作り直しで。grep 0件） |
| cp36 の依頼書 B5 の #1〜#5 | 5件 | 既に消えた（承認済みの控えの中には残る） |
| 同 #6（`engine_tuner_gen.py`:2882「M2-6〜M2-8」） | 1件 | 直す |

- `engine_tuner_gen.py`:2207 行の「C の時間足は 5m より上からだけ引く」は、この工事でさらに古くなるが、一覧に無い。
- `search_limits.json` の `_stage_limits_note` は、段の名前に stage2b・stage3 を挙げ、例の鍵も tfs・quantiles だけ。この工事の「stage2b・stage3 に書くと止まる」と食い違う。止まる側に倒れるので結論には効かない。

## C2 — 1つの工事に入れてよいか ＝ **条件つき YES。作る順番を書く＝Major M-16**

- b97・#5 は `_mat_key` の直しが先に要る。12本の EXPECT_MSG は M-1・M-3・T43・T44・T24⑤ の直しで ❌ の行が変わるので、M-2 は最後にする必要がある。
- 分けると監査と承認が増える（恒久65番の1）。切るなら ①不具合＋M-4＋M-5 ②M-1＋M-3 ③M-2＋M-6 ④M-7（別コミット）。
- **設計書に足す順番（案）**＝①`_mat_key`＋T44 → ②読み口4つ・`stage_candidates`・`expand_stage`・T43・T24⑤（C-1 の直し）・T40・T42 → ③R9 の診断 → ④自己テストを通しで走らせる → ⑤12本の壊し方を当てて ❌ の行を全部記録 → ⑥EXPECT_MSG・lint・b94〜b98 → ⑦M-7（別コミット）。

---

# 4. 優先度 D — 結論に効かせない

## D1 — 「やらないこと」10件 ＝ **問い1 の答えを変えるものは無い（別枠 S-6）**

- 7番（入口の乱数を消さない）は、#5・b97 を入口の乱数に依存させる（M-3）。
- 4番（段2a の上端）は §2.2 の「15m〜4h」を満たさないまま残す（別枠 S-2）。cp36 M-3 の本体（C4 を読まない）とは別の件。
- 2番（G7 が abs を見ない）は、組む側の T40④・T42③・T44 で補われる。
- 書かれていない「やらないこと」＝TARGET の外の壊すプログラム（b93・b92・b85・b78）の目印を保つこと（M-11）。EXPECT_MSG の無い古い16本を lint で数えないこと（M-9）。

**省いた問い＝無し**（A〜D を全部答えた）。

---

# 5. 別枠（結論に効かせない）

| 番号 | 中身 |
|---|---|
| S-1 | 段2c に5分足が入っても、T24②（94本）と T42（食い違い0件）は変わらない（実測・A3-b） |
| S-2 | 段2a の上端を変えない理由の文を「§2.2 の文と違うまま残す」に直すとよい（A3-c） |
| S-3 | 「執行足より上」の判定は `ex._upper_tfs()` を呼び、3か所目を作らない（A5-b） |
| S-4 | `--candidates` の口に壊すプログラムを作らない扱いは、恒久71番の線引きの文と合わない（B2-c） |
| S-5 | M-7 の線引き（C1）。`engine_tuner_gen.py`:2207 と `_stage_limits_note` の古い文 |
| S-6 | やらないこと10件は問い1 を変えない（D1） |

---

# 6. 外部検索（依頼書 §7）

## 6-1 mutation testing の kill の帰属（B1 の材料）

| 出どころ | 逐語・要旨 | この監査との照合 |
|---|---|---|
| PIT「Basic concepts」 https://pitest.org/quickstart/basic_concepts/ | Killed＝"a test caught the mutation successfully." ／ Survived＝"the mutation was not detected by the covering test." ／ ほかに Timed Out・Memory error・Run error を別の結果として分ける | PIT は「落ちた理由」を別の結果に分ける。このプロジェクトの照合は rc と ❌ の文字だけで、例外で落ちた場合を別に数えない（M-10） |
| Du・Palepu・Jones "Leveraging Propagated Infection to Crossfire Mutants"（arXiv 2411.09846）§III https://arxiv.org/abs/2411.09846 | "When a test kills mutants, it can fail by assertions (Block 2) or non-assertion failures (such as crashes) (Block 1.5)." ／ §V-B "we count the number of mutants that each test case and each assertion kills." | test 単位でなく assertion 単位で kill を帰属させる考え方。「❌ T43」は test 単位で、「❌ T43: 途中で止まった」（例外）にも当たる。EXPECT_MSG に判定の文字まで含めると assertion 単位に近づく（M-10 の④） |
| 監査 cp36 §10 が引いた Mutation Testing Repository（uni.lu）の killed の定義 | 「その test が落ちたときだけ killed」 | 設計書の M-2 の直し（❌ で始まる文字）は、この「その test が落ちた」までを満たす。assertion の区別は上の2件が補う |

## 6-2 設定ファイルの fail-fast と、空を「無い」と同じに扱う危険（A4 の材料）

| 出どころ | 逐語・要旨 | この監査との照合 |
|---|---|---|
| awslabs/stickler Issue #350 https://github.com/awslabs/stickler/issues/350 | 題「model_from_json silently ignores every unrecognized config key, so "threshhold": 0.99 builds at 0.5」／"A misspelled key builds with no exception and no warning, at the fallback value."／直し＝知らない鍵で ValueError | 設計書の「知らない段・知らない鍵は止める」はこの直しと同じ向き（M-1 の本体を閉じる） |
| Jsonic「JSON Schema additionalProperties」 https://jsonic.io/guides/json-schema-additional-properties | "When `additionalProperties` is absent, JSON Schema uses the permissive default: any additional key is allowed" ／ "Setting `additionalProperties: false` turns the schema into a closed object." | 既定は許す側で、閉じるには明示が要る。`stage_limits` の鍵は閉じた形にする設計で合っている。残る穴は「空の配列 → 既定」（`quantiles: [] → [None]`）と「案ごとに止める」（M-6） |
| Ajv「Strict mode」 https://ajv.js.org/strict-mode.html | 検証器が曖昧な schema を厳しく扱う形の説明（検索で到達・本文の逐語は取っていない） | 参考のみ |

---

# 7. 依頼を出した CC の自己申告（依頼書 §4）への答え

| 自己申告 | 監査の答え |
|---|---|
| 1. A1（C4 で束が変わらないかもしれない）は実測していない | **変わらなかった**（実測）＝Critical C-1 |
| 2. A2（種7 がまだ需給を含むか）は実測していない | **含んでいた**（実測）。ただし入口の乱数への依存は残る＝Major M-3 |
| 3. 新設4関数の置き場所を書いていない | そのとおり＝Major M-8 |
| 4. `--lint-expect` の置き場所・承認の前に走らせる道が無い | 置ける場所は凍結の照合より前の1つ・承認の前に走らせる道は無い＝Major M-9 |
| 5. 壊すプログラムの無い行は承認で走らない | 実物どおり。#9 は #1 の済で測られる。#8・#10〜#12 は実装の監査が走らせる行にする＝Major M-14 |
| 6. 2-1 の表の数字は 99回目の実測 | 監査役が走らせた範囲（R9 の診断の KeyError）は再現した。`gen_regime_kb.py --verify` は走らせていない（§11-4） |
| 7. 承認はまだ | この監査の結論は CONDITIONAL-GO |

---

# 11. 開いたファイルと行・走らせたコマンドと結果（全部）

## 11-1 監査役が開いたもの（Read tool・sed・grep）

- 依頼書 全文（294行）
- `.claude/state/acceptance.md` 全文（1〜1130行）
- `SDK/.claude/audits/2026-09-13_m2e2_impl_cp36_audit_report.md`：見出しの一覧（grep）・330〜407行
- `SDK/.claude/audits/cp36_work/`：`setup_mirror.py` 全文・`mirror_edit.py` 全文・`run.sh` 全文・`scan_bundles.py` 全文・`r9_compare.py` 1〜40行・`manifest.json` 1〜30行・`logs/` の一覧
- `SDK/scripts/priority_rebuild/engine_tuner_gen.py`：1397〜1403・2320〜3009（1本目・2本目・`stage_counts`・`regime_draw_order`）・3304〜3470（`needed_qkeys`・`build_qtable`）・4038〜4062・4080〜4100・6115〜6130（T40③-3）・6255〜6474（T24⑤・T42・T35）・7025〜7040・7280〜7322（`_DRAW_CTORS`・`_MARK_WRITERS`）・grep（`def build_stage_candidates` ほか・「途中で止まった」16件）
- `SDK/scripts/priority_rebuild/engine_tuner_exec.py`：410〜440（`MATERIAL_PRE`・`NO_ARG_OPS`）・488〜508（`_apply_pre`）・520〜600（`_pre_of`・`_material_name` の頭）・604〜616・1276〜1350（`_upper_tfs`・`_law_count_and`・`_law_count`）・1940〜1990（`material_array`）・2018〜2034（`_mat_key`）・3120〜3165（`attach_demand_columns`）・grep（`NO_ARG_OPS` 2件＝438・610）
- `SDK/scripts/priority_rebuild/regime_r9_diag.py` 全文（281行）
- `SDK/scripts/priority_rebuild/engine_tuner.py`：grep（`load_windows_cached`・`CACHE_DIR`＝88行）
- `SDK/.claude/ratchet/regime_laws.json`：423〜446（C4）・546〜571（R1）・594〜620（R3）
- `SDK/.claude/ratchet/m2_stage_candidates.json` 全文
- `SDK/scripts/priority_rebuild/verify_design_contract.py`：1085〜1096
- `.claude/tools/count_builder_literals.py`：48〜60
- `.claude/tools/run_breaks.py`：336〜410
- `.claude/hooks/approve_impl.sh`：468〜492
- `.claude/breaks/lib.sh`：15〜25 ／ `b93_law_filter_off.sh` 全文 ／ `b92_stage2_no_drop_tfs.sh`（grep）／写し `cp37_work/mirror/breaks/*.sh`（grep＝EXPECT_MSG と measure の行）
- hook（止まった理由を知るため・読むだけ）：`require_read_before_work.sh` 1〜80・`enforce_todo_declaration.py` 1〜560・`enforce_worklog_on_experiment.sh` 全文・`enforce_worklog_on_experiment.py` 全文
- `.claude/state/sessions/*/session_todo.md`（前の監査の ToDo の書き方・grep と head）
- `.claude/state/session_worklog_20260914.md` 末尾・`session_worklog_20260911.md`（§78 の見出しの grep）

Plan agent 2体が開いたものは、各報告の一覧どおり（前半＝設計書全文・`engine_tuner_gen.py` の広い範囲・`material_ranking.json` の env／強さ・`gen_signal_families.py`・`indicator_reference_diag.py`・`verify_design_contract.py`・壊すプログラム ほか／後半＝cp36 レポート全文・`run_breaks.py` 全文・`approve_impl.sh` 380〜536・`require_acceptance_before_impl.sh` 180〜254・承認の記録2件・全88本の EXPECT_MSG と measure の行 ほか）。2体とも Python は走らせていない（`python3 -c` が hook に止められた）。

## 11-2 作業場（`SDK/.claude/audits/cp37_work/`）に作ったもの

| ファイル | 何か |
|---|---|
| `setup_mirror.py` | cp36 の同名の道具の写し（置き場を cp37_work に・古い版の組み立てを外した・b9* の壊すプログラムも数える）。本物の写し `mirror/`・壊すプログラムの写し `mirror/breaks/`・控え `pristine/`・`manifest.json`・入口 `run.sh`・`mirror_edit.py` を作る |
| `a1_measure.py` | A1 を測る（メモリの中で g0・gN・gP を作る） |
| `a1b_scan_n.py` | 上の写しで、案の本数を引数にしたもの（最初 `a1b_measure_n.py` と名付けたら実験の命名の hook に止められ、名前を変えた） |
| `a2_r9_probe.py` | A2 を測る（メモリの中で `_mat_key` と `measure` を差し替える） |
| `setup_proto.py` | 2つ目の写し `mirror_p/` を作り、設計書の試作（時間足と系統の読み方・T24⑤ の期待・`_mat_key` の abs の枝）を当てる |
| `run_p.sh` | `run.sh` の写しで、`mirror_p` を向く入口 |
| `logs/` | `a1_measure.json`・`a1b_scan_n28.json`・`a2_none_s7.out`・`a2_abs_s7.out`・`a2_abs_s8.out`・`a2_abs_s53.out`・`a2_abs_dem_s7.out`・`B4_selftest_base.out`・`A3b_selftest_proto.out` |
| `mirror/v3-bitget-api-sdk/results/priority_rebuild/tuner_cache/` | R9 の診断が作ったデータのキャッシュ（写しの中） |

## 11-3 走らせたコマンドと結果

| コマンド | 結果 | 秒 |
|---|---|---|
| `shasum -a 256 .claude/state/acceptance.md` | `0c692abf…`（依頼書と同じ） | — |
| `python3 setup_mirror.py` | 14件とも本物と写しのハッシュ値が同じ | — |
| `python3 a1_measure.py logs/a1_measure.json` | 先頭 A1 の表 | 32 |
| `python3 a1b_scan_n.py logs/a1b_scan_n28.json 28` | gP で9件とも変わる／g0 で C4・R3 は変わらない | 約40 |
| `python3 a2_r9_probe.py none 7 3` | `KeyError: 'n'` | 111.8 |
| `python3 a2_r9_probe.py abs 7 3` | rc=0・3本とも「測れない: taker_ls」 | 10.7 |
| `python3 a2_r9_probe.py abs 8 3` | rc=0・3本とも測れた | 13.0 |
| `python3 a2_r9_probe.py abs 53 3` | rc=0・3本とも測れた | 9.7 |
| `python3 a2_r9_probe.py abs+dem 7 3` | rc=0・3本とも測れた | 15.6 |
| `bash run.sh gen --selftest`（写しの `engine_tuner_gen.py --selftest`） | rc=0・✅ 全部 pass | 343 |
| `python3 setup_proto.py` | mirror_p の2ファイルに試作を当てた（mirror は元のまま・ハッシュ値で確認） | — |
| `bash run_p.sh gen --selftest`（試作の写し） | rc=1・❌ T40③-3（段2c の5m）・❌ T24⑤（C4＝変わらない） | 319 |
| 写しの breaks の grep（EXPECT_MSG と `measure … --selftest`） | 全88本・EXPECT_MSG 18本・`--selftest` を測る31本・そのうち EXPECT_MSG 無し16本 | — |
| WebSearch 3回・WebFetch 5回 | §6 の表 | — |

★1回目の R9 の診断の走行（zsh で引数が分かれず、5本とも空のログになった）は、ログを消して bash で走らせ直した。結論には効いていない。

## 11-4 走らせられなかったもの・測れなかったもの

- **本物の壊すプログラム**（`bash .claude/breaks/*.sh`）＝本物のファイルを書き替えるので走らせていない（依頼書の決まり）。壊すプログラムの写しも、この監査では走らせていない（新しい b94〜b98 はまだ無く、設計書のチェックでは要らないと判断した）。
- **本物の `.claude/breaks/` の中での `for` 文・`$(...)` を使った grep**＝土台ゲートに止められた。中身が同じ写し（ROOT の1行だけ違う）で数えた。
- **`python3 -`（標準入力から走らせる形）**＝設計↔実装ゲートに止められた。sed で代えた。
- **`touch .claude/state/worklog_ok`**＝権限の判定で止められた（回り道はしていない）。worklog の hook には、監査 cp35 の前例（20260911 §78）と同じく、今日の worklog に途中経過の節（§45）を書き足して答えた（§12）。
- **`gen_regime_kb.py --verify`・`engine_tuner_exec.py --selftest`・`--identity`・`pre_audit_check.py`**＝設計書のチェックの結論に効かないので走らせていない。
- **C1 の19件の grep の件数**＝後半の Plan agent の数えを使い、監査役は確かめ直していない。
- **試作の限界**＝`stage_limits_of`・`drop_tfs_of`・T43・T44・`--candidates`・rc=1 の決まりは試作に入れていない。law_tf は元データでなくコードの中の対応表で代えた。
- **自己テストの秒数**＝Plan agent 2体が同時に動いている中で測った。承認の打ち切りのときの負荷とは違う。

---

# 12. 本物のファイルを書き替えていないこと

`git status --short`（監査の前から在った変更と未追跡を含めて、そのまま載せる）＝

```
 M .claude/state/next_step.md
 M .claude/state/session_worklog_20260914.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
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
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-09-14_m2e2_major_design_cp37_audit_report.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror_old/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/pristine/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-14_m2e2_major_design_cp37_audit_request.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

**監査の前（SessionStart の時点）の git status と比べて増えたもの＝2つだけ。**
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-09-14_m2e2_major_design_cp37_audit_report.md`（このレポート・新規）
- `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37_work/`（作業場＝写し・測る道具・記録）

**監査の前から「M」だったが、監査役が書き足したもの＝1つ。**
- `.claude/state/session_worklog_20260914.md`＝末尾に §45「監査 cp37 の途中経過（auditor session が書いた）」を1節 書き足した。理由＝作業場で測る道具を走らせたので、ターンを閉じる hook（`enforce_worklog_on_experiment`）が記録を求めた。hook の案内の `worklog_ok` は権限の判定で置けなかった。前例＝監査 cp35 の担当が 20260911 §78 を書いた形。

**そのほか監査のために書いたファイル（git の一覧に出ない）**＝このセッションの ToDo（`.claude/state/sessions/99412617-0431-4cfb-a4e0-582d4952de75/session_todo.md` と貼った印・hook の要求）。

**本物のコード（`engine_tuner_gen.py`・`engine_tuner_exec.py`・`regime_r9_diag.py`）・設計書・法則ファイル・段の元データ・設定ファイル・壊すプログラム・道具は1文字も書き替えていない。**一覧の「M」の残り7件（next_step.md・acceptance_src.json・decisions.md・milestones 2本・materials 2本）は、監査の前から在った変更。

レポート終わり。
