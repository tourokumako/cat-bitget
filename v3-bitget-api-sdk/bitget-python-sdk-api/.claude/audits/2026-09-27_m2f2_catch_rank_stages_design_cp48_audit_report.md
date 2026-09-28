# 監査結果 cp48 — CP48 — M2-F-2 の設計書（測る道具 regime_r9_diag.py に「捉えた割合」と順位、ファイルの書き出し、段ごとに測る口・差し戻しの口・値なしの口を足し、乱数を消し、試行を累積に数える）は、§2.2 の検索方法とまこさんの決定どおりの形になるか。書いたとおりに「実装の指示」をプログラムが当てられるか

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-27_m2f2_catch_rank_stages_design_cp48_audit_request.md`
- 依頼書のハッシュ値: 1480840b468e744ccc1f5a42219d96d024c8dafdbb9b3636cdea5b63a3f2e96e
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 8554e86b96e52118129e92ccd4f44b509f5f330ea9d96588338b2086664508de
- 監査が照らしたハッシュ値: `.claude/state/acceptance.md` の sha256＝8554e86b96e52118129e92ccd4f44b509f5f330ea9d96588338b2086664508de（依頼書と一致）。依頼書は 1480840b468e744ccc1f5a42219d96d024c8dafdbb9b3636cdea5b63a3f2e96e（骨組みと一致）。元データ acceptance_src.json は 7467f1f5bcdcb7f38475868a16d29438aa7c78285c5de6978a7c377882ebb5a3（worklog §18 と一致）。直す相手 regime_r9_diag.py は d0b0678d90c56b7d6e452fc874bb1e932aad814439a615c0adabe00811510576（HEAD との差の塊は0）。
- 実施日: 2026-09-27


## 2. 監査対象の型宣言

- **コード型**＝設計書 4-20 の実装の指示21件（regime_r9_diag.py に当てる17件と、壊すプログラム4本）。
- **数値型**＝3つの割合の式・並べる鍵（平均）・keep（渡す本数）・段3 の保つ上限の決め方。
- **文書型**＝設計書（acceptance.md）と元データ（acceptance_src.json）。完成の条件・4-4 の手順・4-13 の影響範囲。


## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの）

| 事実データ（依頼書の行） | 監査の確かめ | 結果 |
|---|---|---|
| grep -c '捉えた' → 0 | 同じコマンド | 0 ✅ |
| grep -c '順位' → 0 | 同じコマンド | **1 ❌**。regime_r9_diag.py:194 `print("順位\t指標\t時間足\t列\t分離力")` に当たる。設計書 2-1 の行も「1（終了コード 0）」を出したまま、読み方に「零件」と書いている。依頼書は0と写した（修正 57） |
| grep -c 'write_text' → 0 | 同じ | 0 ✅ |
| grep -n 'default_rng' → 324行の1件 | 同じ | 324 の1件 ✅ |
| grep -c 'record_run' → 0 | 同じ | 0 ✅ |
| M2-F-1 の固定のレシピ（8.704秒・①5.30%・③50.3%／51.4%） | worklog 20260927:441〜442 を読んだ（走らせていない＝写しを作れない） | 記録と一致 ✅（再走はデータ不足） |
| gen_acceptance --write（1,673行・囲み12・法則51/51） | `wc -l acceptance.md`＝1673。worklog:502 に同じ文 | 行数 ✅。囲み・法則の数は worklog だけ（再走は禁止＝本物を作り直すコマンド） |
| require_design_check --try 不足0件（5.2秒） | worklog:503 に「不足0件」 | 不足0件 ✅。**「5.2秒」は worklog:503 に無い＝確かめられない** |
| verify_design_contract --diff 齟齬0件 | 読むだけで走らせた（`python3 -B scripts/priority_rebuild/verify_design_contract.py --diff …/acceptance.md`） | rc=0・「齟齬: 0件」✅。★これは SPEC が直す前の実物から作られている証拠でもある（A4・修正 39） |
| gen_acceptance --verify rc=0 | 走らせようとして土台ゲートに止められた（§10） | worklog:504 の記録だけ（再走できず） |
| pre_audit_check --verify「監査に出せます」 | worklog:511 | 記録と一致（再走していない） |
| ls .claude/breaks の最後＝b112 | ls | b100〜b112 が在り、b113 以降は無い ✅（全108本） |


## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ FAIL（比べる相手 RG-v5 が上位の枠を1本 使う＝渡すのが9本になる〔修正 17〕。段3 の保つ上限が、前の束の順番と結び付いて決まる〔修正 15〕。先読みの片方だけで並ぶ行がある〔修正 63〕）
- ②リスク管理 ＝ FAIL（値なしの口が値なしを数えられない〔修正 21〕。段3 で G7 に掛けない〔修正 15〕。完成の条件6行が新しい口を1度も通らない〔修正 23〕）
- ③認知バイアス ＝ FAIL（「生成器と同じ形」〔4-18・塞げないもの3〕と「この道具を探す壊すプログラムは0本」〔依頼書 B2-d〕が実物と違う）
- ④ソフトウェア工学 ＝ FAIL（入口の木の無い束で解決表が KeyError になる〔修正 1〕。契約と実装の指示が食い違う〔修正 3・5〕）
- ⑤再現性 ＝ PASS（乱数が消え、束の並びは決まっている。例外＝同じ秒のファイルの上書き〔修正 61〕）
- ⑥実行プロセス ＝ FAIL（4-4 の順では、固定のレシピの走行を設計↔実装ゲートが止める〔修正 39〕。L-605 の grep が行の文字だけだった〔修正 77〕。事実データの「順位 0」の誤り〔修正 57〕）
- ⑦主エージェントバイアス ＝ FAIL（「動く見込み」をコードを読んだだけで書き、口を1度も走らせずに完成の条件を閉じる形〔修正 23・79〕）

### A0 — 完成の条件6行の壊し方と壊すプログラム4本（新設 b113〜b116）が、条件の文そのものを壊して測れる形か（優先度 A）

- **A0-a（読んだ結果・実際の走行はデータ不足＝写しを作れない）**
  - 直す前の selftest は、実装の指示 9 の後で ①〜⑩ が全部 通ります（⑨ は tempfile.mkdtemp に書く）。
  - b113（`~` を外す）で落ちるのは ⑥ の「正解レンジ0本→nan」だけです。CC の読みのとおりです。全部真／全部偽の既知答えと反転の検査は、分母の向きに反応しません。「使える」の印も selftest では全部 真なので、`& usable` を消す壊し方は1つも検出されません。**足りません。** 設計書 4-19 の通しの例1（8本・答え 0.5）が selftest に入っていません（修正 33）。
  - b114 → ⑦、b115 → ⑧、b116 → ⑨ は、どれも宣言どおり「❌」と rc=1 になると読めます。
- **A0-b** 実装の指示 7・16 を当てた後の `ts.record_run(` は、`_record` の中の1か所だけです。実装の指示 2 の説明文の「tuner_stats.record_run で」は、直後が「(」でないので当たりません。
- **A0-c**
  - ⑦ は Attribute の名前2つしか見ません。`from numpy.random import default_rng`（Name になる）・`import random`・np.random のほかの関数は通ります（修正 35）。
  - ⑧ は `_record` の中に record_run が在れば通ります。main・run_stage・run_sweep が `_record` を呼ばなくなっても落ちません（修正 37）。
  - 「説明の文の sample_structure は⑦に当たらない」は正しいです（説明の文は Constant で、Attribute ではない）。
- **A0-d**
  - #5（全部 通る）に壊すプログラムを付けないのは、恒久71番の線引き（`.claude/rules/permanent_rules.md`:387「**いままでどおり。**壊すプログラムで守る」）と合います。#6 も ⑨ が書く処理を守るので合います。
  - ただし、新しく足す「段の口の束を測れる」（⑪）には壊すプログラムが要ります（修正 49〜54）。
  - **完成の条件6行は、--stage・--top・--sweep・--build・--nan-check を1度も通りません。** だから修正 1 の KeyError が在っても6行が全部 通ります（修正 23〜26・79）。

修正の番号＝23・24・25・26・33・34・35・36・37・38・49・50・51・52・53・54・79

### A1 — 捉えた割合・当たった割合・正解レンジの割合の式と、並べる鍵（実装の指示 4・5・9）が、正本とまこさんの決定どおりか（優先度 A）

- **A1-a** 式は正本と1つずつ合います（milestones2:2000 の前置き3）。
  - 捉えた割合＝`col[(~strong)&usable].mean()`＝tp/(tp+fn)。
  - 当たった割合＝1−③＝tp/(tp+fp)。
  - 正解レンジの割合＝`(~strong)[usable].mean()`。
  - 並べる鍵＝③の2つの先読みの平均の低さ、次に捉えた割合の平均の高さ。まこさん決定「１は平均でOK」どおりです。
- **A1-b**
  - 正解0本は nan、③が nan なら当たったも nan、両方 nan は最後に置きます。嘘の0を出さない向きです。
  - 穴＝先読みの片方だけ nan の行は、残りの1つの数字で並びます（塞げないもの4＝CC の決定で、正本に無い）。決めたこと5-1 の理由（測れない束を上位に混ぜない）と同じ向きに、片方でも nan なら最後に置く形へ直します（修正 63〜66）。
  - ①が小さすぎる束（1バーだけ真なら当たった100%）の穴は、M2-F-10 で まこさんが決めるので、この設計では直しません。
- **A1-c** RG-v5 の行も `rank_rows` で順位を持ち、**keep の枠を1本 使います**（regime_r9_diag.py:146 で行が作られ、rank_rows は①が在る行を全部 数える）。
  - RG-v5 が上位10位に入ると、11位の束が「成績下位」になります。`_load_top` は内側が無い RG-v5 を外すので、次の段へ渡るのは**9本**です。まこさん決定「10本」が黙って崩れます。
  - RG-v5 が10位より下なら、束でない行が「落ちた候補」の成績下位に数えられます。
  - M2-F-9 の数え（散らばり）にも混ざります。**誤読の問題にとどまらず、選抜が狂います（Critical）**（修正 17・18・69・70）。
- **A1-d** `_labels_for`・observe_diag._regime_labels（5831〜5848）・_regime_horizons（5806〜5814）は1文字も変わりません。ラベルは窓の中の close だけから作るので、stage_warm でも変わりません。✅

修正の番号＝17・18・63・64・65・66・69・70

### A2 — 段の口（run_stage）と差し戻しの口（run_sweep）が組む束の形（実装の指示 7）が、§2.2 の段の表と M2-F-8〜15 の形どおりか（優先度 A）

- **A2-a（Critical）** `_loosened_off` は生成器の E と**2点で違います。**
  1. not で包んだ条件（段2a の強さ）も側を返しています。生成器は `off_c` の側を返しません（engine_tuner_gen.py:3349 `off_c["value"]["threshold_q"] = _loose_q_fixed(limits, strong["value"]["threshold_q"], strong_side)`・:3381 `"off": {"any": [_flip_loose(limits, cond_a), _flip_loose(limits, cond_b), off_c]}`）。固定のレシピの off も「MACDヒスト% above q49」で、同じ側です（r9_demand_fixture.json:49〜52）。CC の形の off は「強さ below q49」になり、**入る側の真ん中で毎回 出る＝段3 の判定がほぼ真にならず、段3 の順位が黙って狂います。**
  2. 段2c の条件も off に入れています。生成器は A・B・C だけです。

  直し＝修正 7〜14（frames を渡し、生成器と同じ部品・同じ向きにする）。

  ★別に見つけたこと（この工事の外）＝生成器の C の off（not(強さ above q50) に対して「above q49」）は、入る側の境目の内側で出ます。これは緩めた形ではありません（緩めるなら q51）。修正の番号＝なし（生成器はこの工事の TARGET の外。next_step §6 に積むかは まこさんが決める）。
- **A2-b** 帯の幅の候補（build_width_candidates）の先頭は、法則 R7 の geo＝["W%"]・側 above です（regime_laws.json:773〜786）。`_thr_fixed`＝q50（quantile_range 10〜90 の真ん中）なので、M2-F-8「W% が閾値より上・q50 の1点」と合います ✅。ただし geo が空になると、先頭が黙って BB幅 に替わります（修正 67）。
- **A2-c（Critical）**
  - 段3 の行は、枠に "stage3" を足すのに内側に条件を足しません。だから len(内側)+1＝len(枠) になり、**run_sweep が段3 の順位表を必ず拒否します**（M2-F-15 の相手を差し戻せない）。
  - 段3 の保つ上限は `_nv_fixed(…, i)` の i＝束の通し番号（前の束 × 候補）です。同じ候補でも、前の束が違えば別の値（24〜243）になります。設計書 4-7 の「候補の番号で」と違います（修正 15）。
  - out_col（regime_<段>_<番号>）は走行の中で重なりません。束ごとに df.copy() するので、build_regime_columns の上書き防止（exec:2324〜2326）にも当たりません ✅。
- **A2-d**
  - 終わり方＝rank_key を厳密に比べ、束の数は有限なので、無限に回る道はありません。while の最初の周は必ず回ります ✅。
  - ただし、**1位の1本だけ**を差し戻し、最後に1本だけ出します。M2-F-15（milestones2:2033「最終の10本を出す」）と違います。持続（streak の本数）の枠も入れ直しません（修正 19・20）。
- **A2-e（Critical）** 段3 の口は G7 を1度も掛けません（measure は build_regime_columns を呼ぶだけで、検査はしない）。M2-F-14（milestones2:2200「G7（法則の審査）に通します」・出るもの「G7 で落ちた束と理由」）を、この道具では走らせられません（修正 15）。
- **段2c（Critical）** §2.2 の段2c「「なし」を必ず併走」（milestones2:764）と M2-F-13「10本 ×（候補数＋1）・「なし」の行が在る」の、なしの束を組みません（修正 15）。
- **段2b（Critical）** `keep = g.stage_keep_of(lm, len(cands))` は、候補が1本の段2b で keep＝1 になり、上位1本しか渡りません。M2-F-7 で hi＝10 を書くと `stage_keep_of` が SampleError で止まります（engine_tuner_gen.py:3164 `if hi > int(n_cands):`）。**M2-F-12 を走らせられません**（修正 15）。
- **C3（Major・未決）** M2-F-13「C2 と C3 で落とします」と、法則ファイルの C3「使う段: M2-G」（機械が読む判定なし＝G7 でも落ちない）が食い違っています。§2.2 の段3（n＝state_hold_bars_range・緩め幅を探す）と M2-F-14（10本×22通り）も食い違っています。どちらもまこさんが決めるので、未決の行として書きました（修正 47）。

修正の番号＝7・8・9・10・11・12・13・14・15・16・19・20・47・48・67・68

### A3 — 乱数の撤去・旗の変更・余白の stage_warm 化で、既存の走行と道具が壊れないか（優先度 A）

- **A3-a** データ不足です（固定のレシピを写しで走らせられなかった）。コードの読み＝値の変わり方を決める3つは、どれも窓の中だけから作ります（ラベル＝`_labels_for(df.loc[win])`、解決表＝build_qtable の mask、engine_tuner_gen.py:3829〜3832）。レシピの材料（S-Rタッチ数 15m・144本／MACDヒスト% 30m EWM／stdev% 30m 50本／W%＝168h の帯）は、60日の余白で収束しています。だから①③は印字の桁で同じになる見込みです。変わるなら、前処理（prepare_df）で60日より長い記憶を持つ列が原因です。リスク2 の「長い記憶の指標」という説明の向きは正しいですが、差の大きさは実装の後の実測で決めます。キャッシュの指紋が変わるので、1回目の走行は約9秒ではなく、読み込み（99〜103秒以上）が足されます。
- **A3-b（Critical）** --build は、束だけのレシピ（`_stage_recipe`）を作ります。これには入口の木（"entry"）が無いので、`_qtable` → build_qtable → needed_qkeys の `ex._walk(r["entry"]["connective"])`（engine_tuner_gen.py:3787）で KeyError になります。measure は SystemExit しか受けないので、**--build も --stage も --sweep も必ず落ちます**（修正 1）。直した後の出力は正直です（組めない案は引き直さず dropped に残し、record_run の本数は測った束の数）。ただし、直す前の validate_drawn（regime_r9_diag.py:329）が外れ、法則に反する束も測るようになります（修正 73）。
- **A3-c（Critical）**
  - **この道具を名前で探す壊すプログラムは0本ではなく、2本です。**
    - b84＝探す行 `qt = qt_all` は残ります。測るのは組む側の T38 で、これは通ります。
    - **b97＝測るコマンドが `--recipe … --no-trades`（b97:31）です。この工事の後は、argparse が知らない旗で rc=2 を返し、--purpose も無いので、完成の条件 AUDIT-5 の番人が壊れます**（修正 27〜32・77）。
  - .claude/tools/gen_stage0_timing.py:59（読み方を regime_r9_diag.py:230 の WARM と同じにする）と、gen_s22_fidelity.py:15（--build と同じやり方）の文が、実物と合わなくなります（修正 69）。
  - enforce_h2_pass／enforce_g2_pass の自己テストは、コマンドの文字しか使わないので、影響はありません。
- **A3-d** 恒等3本・G2・H2・入口の案は、この道具を通りません。regime_r9_diag.py は h2_pass.json・g2_pass.json に0件で、印の対象の外です（grep で確認）✅。

修正の番号＝1・2・27・28・29・30・31・32・69・70・73・74

### A4 — 「実装の指示」21件が、当てる道具でそのまま当てられ、当てた後のコードが動くか（優先度 A）

- **当てられるか** 直す前の文字17件は、どれも実物で1か所だけでした（grep -x -F と -o -F で確認）。根拠の行も実物と合います。壊すプログラム18〜21は NEVER_WRITE に在るので当てず、rc=1 で終わります（設計書 4-4 どおり）。
- **A4-a（Critical）** 当てた後のコードは、次の所で止まります。
  1. 入口の木が無いことによる KeyError（修正 1）。
  2. **設計書の DESIGN_CONTRACT が、実装の指示と食い違っています。**
     - impl_functions に `_nanmean`・`_stage_recipe`・`_record` が無いので、照合A で落ちます（verify_design_contract.py:1056）。
     - must_use は main・run_stage・run_sweep に record_run を求めますが、3つとも `_record` を呼ぶだけです（照合C＝:1244）。
     - 設計↔実装ゲート（require_design_contract_before_run.sh:360）が、#6 と段の走行を止めます。impl_functions は承認で凍結されるので、実装の後に直すと「期待値を作り直した疑い」になります（修正 3〜6）。
  3. SPEC（7-8）は直す前の実物から作られています（いまの --diff が齟齬0件なのはそのため）。だから実装の後は `--diff` が公開の関数8本などを齟齬に出し、4-4 の手順3（固定のレシピ）を同じゲートが止めます（修正 39）。
  4. 値なしの口（修正 21）。
  - selftest ①〜⑩ は通ると読めます（実際の走行はデータ不足）。
- **A4-b** 同じファイルへ当てる件の順番で、先の件が後の件の直す前の文字を消すことはありません。8（_print_rows 全体）と 9（④の直後）、15（--build の塊）と 16（測って出す所）は、どれも重なりません ✅。
- **A4-c** 名前は定義の順で解決します（OUT_DIR・DROP_KINDS は指示4 の中で write_outputs より前、time は指示3、measure と _print_rows は見出しより前）。`import engine_tuner_gen` は関数の中で読むので、読み込みの輪を作りません ✅。
  - 指示7 は「足す文字」です。当てる道具は `before + body` で改行を入れずにつなぎます（apply_audit_fix.py:355）。だから「番人」の見出しと新しい節の見出しが1行につながり、番人の見出しが2つになります（壊れはしないが見出しの直前にならない＝修正 71）。
- **A4-d** 壊すプログラムが探す文字は、当てた後の実物と合います（b113＝指示4 の行／b114＝指示14 の後も `    ad = et.load_adapter(a.strategy)\n` は1か所／b115＝`ts.record_run(` 1か所／b116＝指示4 の行）。修正 1〜76 を当てた後も、この4行は変わりません ✅。
- **A4-e** main の並びは、既存の読み手と矛盾しません（機械が読む JSON を読む相手は0）✅。

修正の番号＝1・2・3・4・5・6・21・22・39・40・71・72

### A5 — record_run の使い方（実装の指示 7・11・13・16）が、tuner_stats の作りと恒久24番に合うか（優先度 A）

- **A5-a** `record_run(key=f"{strategy}/r9/{tag}", n_trials, stamp, purpose=a.purpose, note)` は tuner_stats.py:213〜230 と合います（purpose は既定なし・search は累積・check は確認の帳簿）✅。鍵は段ごとに分かれます（e38/r9/stage1 ほか）。M2-L で DSR の N に足すときは前方一致で合計します（この工事の外）。
- **A5-b** n_trials＝束の本数（まとめる前の本数）は、DSR の N を多めに入れる側です。罰が重い側で、CC の読みは正しいです ✅。
- **A5-c** --recipe＝check、段＝search、--nan-check・--selftest・--candidates・--dump-build は record_run を呼ばない＝数えません ✅。
  - M2-F-5（段1 の束を数本・milestones2:2091）を小さく測る口がありません。段1 の336本を丸ごと走らせるしかなく、恒久61・62番（小さく測ってから）を満たせません（修正 43〜46）。
  - add_cumulative は読んでから書き直す形で、鍵を持ちません（tuner_stats.py:175〜192）。段の走行を2つ同時に終えると、片方の本数が消えます（数えが甘くなる向き＝修正 75）。

修正の番号＝43・44・45・46・75・76

### B1 — 落ちた候補の5つの場面（実装の指示 4・6・7・15・16）に、漏れと二重数えが無いか（優先度 B）

- **B1-a** 実走に出る落ち方は、組めない・測れない・関所で拒否・成績下位の4つです。修正 15 の後は G7 で落ちた束も関所で拒否に入ります。「束が無い」は fail-closed で止まるので、実走のファイルには出ません（塞げないもの1 に正直に書いてあり、妥当）。
- **B1-b** 観察（修正なし）＝build_regime_columns の RecipeError は、関所（解決表に鍵が無い）以外に、材料を作れない・列が無い・上書き防止も含みます。それを全部「関所で拒否」と呼びます。注の頭で分けるので、測れない（解決表そのものが作れない）と取り違えることはありません。
- **B1-c**
  - run_stage の束の名前が `len(recipes)` なので、組めない束と次の束が同じ名前になります（落ちた候補と測った行に同じ名前が出る＝修正 15 で通し番号に直す）。
  - 差し戻しは、周をまたいで同じ組の束を測り直します。落ちた候補が周ごとに重なり、試行も重ねて数えます（多めの向き＝修正なし）。

修正の番号＝15・16

### B2 — 設計書 4-13（影響範囲）と「やらないこと」10件・「塞げないもの」8件に、見落としと成り立たない理由が無いか（優先度 B）

- **B2-a** やらないこと9（--nan-check を完成の条件に載せない）の理由は成り立ちます。ただし次の2つが足りません。
  - 口の中身が壊れています。材料の列は実行データに無く、実行器がその場で作ります（engine_tuner_exec.py:2101 `return material_array(df, name)`）。だから `if col not in dfx.columns` がいつも真になり、値なしを1本も数えずに rc=1 で止まります（修正 21）。
  - M2-F-13 の前に必ず走らせる行が、m2_todo／milestones2 に無いです（修正 55・56）。
- **B2-b** keep は、M2-F-7 の前は候補の本数（絞らない）で、段2b では1、hi＝10 では止まります。このことが設計書に書かれていません（修正 15 で、hi が無いまま前の段を読むときは止め、keep を測る束の本数から決める）。
- **B2-c** DESIGN_CONTRACT と 4-3 は、どちらも `_nanmean`・`_stage_recipe`・`_record` を欠いています。4-3 の実装の指示の番号は1つずれています（8→7・9→8・10〜15→11〜16・16・17→9・10＝修正 3〜6・59）。
- **B2-d** 探しているのは b84・b97 の2本です（上の A3-c）。L-605 の grep を行の文字だけでして、ファイル名と旗で探していませんでした（修正 27〜32・77）。
- 塞げないもの3（形は同じに書く）は、成り立っていません（A2-a）。

修正の番号＝3・4・5・6・15・16・21・22・27・28・29・30・31・32・55・56・59・60・77・78

### C1 — 名前・文書・見積もり（優先度 C）

- **C1-a** rank_／dropped_＋札＋日時の名前で、後から探せます ✅。
  - 日時は秒までなので、同じ秒・同じ札なら上書きします。4-10 の「上書きしない」を保証していません（修正 61）。
  - json.dumps は nan を `NaN` で書きます（Python は読める・jq は読めない＝観察のみ）。
- **C1-b** 内側・枠・包み・当たった・捉えた・正解レンジは読めます ✅。
- **C1-c**
  - selftest の時間は未実測です。
  - 段1 の約49分は掛け算で、1プロセスの共有分を含みません。
  - **差し戻しの見込みがありません。** 1周＝上位の束 ×（帯の幅＋段1 336＋段2a 89＋段2b 1＋段2c＋段3 22）本で、周の数も分からないので、56時間の中で最も重い段になります（修正 41）。
  - 事実データの「順位 0」の誤り（修正 57）。

修正の番号＝41・42・57・58・61・62


## 5. 外部検索

### 検索 1 — 段ごとの選抜（各段の上位 k を次の段へ渡し、最後に1枠ずつ入れ替えて改善が止まるまで回す形）が業界・文献に在るか

- **上位 k の渡し方（beam search）**＝在ります。arXiv 2203.04350「Beam Search for Feature Selection」の本文（https://arxiv.org/html/2203.04350）から逐語で引きます。
  - "beam search, which always keeps the best k subsets of features at each step during the process of searching."
  - "for each of the k groups of features of size t−1, fit p−(t−1) models by adding each of the remaining p−(t−1) features into the group of features."
  - "When the beam width k is 1, beam search reduces to forward selection."
  - "Finally, out of the k groups of features of size d, select the best group of features corresponding to the model with the lowest misclassification rate."
  - 要約（https://arxiv.org/abs/2203.04350）＝"beam search to perform feature selection, which can be viewed as a generalization of forward selection."
- **入れ替えの止め方（1周して改善が無ければ止める）**＝在ります。Wikipedia「Coordinate descent」（https://en.wikipedia.org/wiki/Coordinate_descent）の逐語です。
  - "one cyclically iterates through the directions, one at a time, minimizing the objective function"
  - "No improvement after one cycle of line search along coordinate directions implies a stationary point is reached."
  - 限界＝"coordinate descent iteration may get stuck at a non-stationary point if the level curves of the function are not smooth"
- **選んだ後に入れ替えて戻る形（SFFS）**＝mlxtend の説明（https://rasbt.github.io/mlxtend/user_guide/feature_selection/SequentialFeatureSelector/）の逐語です。
  - "In step 2, we only remove a feature if the resulting subset would gain an increase in performance."
  - 止め方＝"stop when k equals the number of desired features"
- **組み合わせ全体**＝「枠を段ごとに決め、各段で上位 k を渡し、最後に1枠ずつ全候補で入れ替えて、改善が無い1周で止める」を1つの名前で書いた業界標準の文献は、**見つかりませんでした。**
- 設計への意味：
  - beam の論文は最後に k 本から1本を選びます。この設計の「上位10本を渡す」は、beam 幅 k＝10 に当たります。
  - 座標降下の止め方は「改善が無い1周」で、run_sweep の `improved` と同じです。ただし、離れた候補の間を動くので、局所の最良で止まります。出発の束を1本（1位だけ）にすると、この限界がそのまま出ます。上位10本それぞれから差し戻す形（修正 19）は、出発点を増やす手当てになります。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

正しいです。走らせていません。この監査も写しを作れず、走らせていません（データ不足）。コードを読んだ結果は次のとおりです。
- ①当てた後のコードは、--build・--stage・--sweep が KeyError で落ちます（修正 1）。固定のレシピの走行は、設計↔実装ゲートが止めます（修正 3〜6・39）。
- ②番人⑥〜⑩は通り、b113〜b116 は宣言どおり落ちると読めます。
- ③2回目の承認の後なら、順位表と落ちた候補のファイルは書かれます。

### 自己申告 2

2か所目の形は生成器と2点で違います（not の条件の側を返す・段2c を off に入れる）。段3 の順位が黙って狂う Critical です（修正 7〜14）。生成器そのものの C の off も、入る側の内側で出ます（修正なし・この工事の外）。

### 自己申告 3

同じ型の書き誤りは、ほかにも残っていました。
- 入口の木の無い束（KeyError）
- `_loosened_off` の向き
- 段2b の keep
- 段3 の枠の数のずれ（差し戻しが拒否する）
- 値なしの口の列
- 契約の関数と must_use
- 4-3 の番号のずれ
- 指示7 が「足す文字」なので見出しが1行につながること

### 自己申告 4

作り直しの fail-closed は「読み方の数字」だけを見ます。読み方と出力が合っているかは見ません。2-1 の「順位」の行は出力が1なのに、読み方は「零件」です（修正 57）。

### 自己申告 5

CC が決めた項目は、それぞれ次のとおりです。
- nan の扱い（修正 63〜66）
- 書き先と名前＝妥当。ただし上書きの防止が要る（修正 61）
- 旗＝小さく測る旗が足りない（修正 43〜46）
- 行に残す鍵＝段3 の枠がずれる（修正 15）
- 保つ上限の歩き方＝束の通し番号で歩き、設計書の「候補の番号」と違う（修正 15）。24〜288 のうち試されない値が出る（修正 47 の2行目＝未決）


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝式が milestones2:2000 の前置き3 と1つずつ合う。並べる鍵が「１は平均でOK」どおり。正解の印と本数は1文字も変わらない。RG-v5 が keep を使う件と片方 nan の件は、組み方の欠陥なので問い3 に数えた）
- 問い2 ＝ YES（根拠＝向きが §2.2 の段の表・M2-F の順・まこさんの決定と合う。段の口・差し戻しの口・値なしの口・乱数の撤去・record_run・落ちた候補のファイル。既存の走行＝恒等3本・G2・H2・入口の案は、この道具を通らず変わらない。★ただし実装の指示7 の中身は、段2b・段2c・段3・段4・値なしの口を正しく組めていない。その6件は、実装の指示の直しで閉じる Critical として問い3 に数えた）
- 問い3 ＝ NO（根拠＝17件は当たるが、当てた後の --build・--stage・--sweep が KeyError で落ちる。契約と SPEC の食い違いで、ゲートが固定のレシピを止める。完成の条件6行は新しい口を1度も通らない。既存の b97 が壊れる）

### 結論と件数

- 結論＝CONDITIONAL-GO
- Critical＝9
- Major＝9
- Minor＝9
- Process＝3


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・_stage_recipe）
直す前の文字:
~~~
    return {\"meta\": {\"strategy\": strategy, \"logic_id\": name, \"side\": \"SHORT\",\n                     \"regime\": {\"name\": \"range\", \"entry_col\": bd[\"entry\"][\"out_col\"], \"build\": bd}}}
~~~
直した後の文字:
~~~
    return {\"meta\": {\"strategy\": strategy, \"logic_id\": name, \"side\": \"SHORT\",\n                     \"regime\": {\"name\": \"range\", \"entry_col\": bd[\"entry\"][\"out_col\"], \"build\": bd}},\n            # ★入口の木は空の all（束だけを測る・玉は測らない）。無いと build_qtable の needed_qkeys が r[\"entry\"] で KeyError になる（監査 CP48）\n            \"entry\": {\"connective\": {\"all\": []}}}
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3787「ex._walk(r["entry"]["connective"])        # ★木の形の検査は今までどおり通す（副作用を残す）」
状態: 確定

#### 修正 2
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 318行（DESIGN_CONTRACT の impl_functions）
直す前の文字:
~~~
"_load_top", "run_stage", "run_sweep", "run_nan_check", "measure",
~~~
直した後の文字:
~~~
"_load_top", "_stage_recipe", "_record", "_nanmean", "run_stage", "run_sweep", "run_nan_check", "measure",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py:1056「ng.append(f"A {rel}: 設計書に書いていない関数を触った → {extra}")」
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
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 324〜327行（DESIGN_CONTRACT の must_use）
直す前の文字:
~~~
      "main": ["stage_warm", "sample_regime_build", "rank_rows", "write_outputs", "record_run"],
      "run_stage": ["build_stage_candidates", "rank_rows", "write_outputs", "record_run", "_wrap_bundle"],
      "run_sweep": ["rank_rows", "write_outputs", "record_run", "_wrap_bundle"],
      "run_nan_check": ["build_stage_candidates", "_apply_pre"],
~~~
直した後の文字:
~~~
      "main": ["stage_warm", "sample_regime_build", "rank_rows", "write_outputs", "_record"],
      "run_stage": ["build_stage_candidates", "rank_rows", "write_outputs", "_record", "_wrap_bundle", "_check_scene_rules"],
      "run_sweep": ["rank_rows", "write_outputs", "_record", "_wrap_bundle", "_check_scene_rules"],
      "run_nan_check": ["build_stage_candidates", "_col_array"],
      "_record": ["record_run"],
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py:1244「ng.append(f"C {func}: 設計書が要求する名前が中身に無い → {missing}（{where}）")」
状態: 確定

#### 修正 6
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・_loosened_off の頭）
直す前の文字:
~~~
def _loosened_off(conds: list[dict], limits) -> dict:\n    \"\"\"hysteresis の出る線＝内側の水準の条件を1段 緩めて側を返した any。\n\n    ★sample_regime_build の E と同じ形をこの道具に書く（あちらは案の番号から束を丸ごと組む形で、\n      上位 × 候補の掛け合わせには使えない）。緩め方の判定は書き写さない＝生成器の _loose_q_fixed を呼ぶ。\n    \"\"\"\n    import engine_tuner_gen as g\n    outs = []\n    for c in conds:\n        base = c.get(\"not\") if isinstance(c, dict) and \"not\" in c else c\n
~~~
直した後の文字:
~~~
def _loosened_off(conds: list[dict], limits, frames: list | None = None) -> dict:\n    \"\"\"hysteresis の出る線＝sample_regime_build の E と同じ形の any（監査 CP48 で直した）。\n\n    ★生成器の E（engine_tuner_gen.py の sample_regime_build）＝off は、A（帯の幅）と B（段1）を1段 緩めて側を返したもの（_flip_loose）と、\n      C（段2a の not の中身）を1段 緩めて側は返さないもの（off_c）の any。段2b・段2c の条件は off に入れない。\n      緩め方の判定は書き写さない＝生成器の _loose_q_fixed を呼ぶ。frames＝各条件の段の名前（無ければ水準の条件を全部 使う）。\n    \"\"\"\n    import engine_tuner_gen as g\n    outs = []\n    for i, c in enumerate(conds):\n        if frames is not None and (i >= len(frames) or frames[i] not in (\"width\", \"stage1\", \"stage2a\")):\n            continue\n        is_not = isinstance(c, dict) and \"not\" in c\n        base = c.get(\"not\") if is_not else c\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3381「"off": {"any": [_flip_loose(limits, cond_a), _flip_loose(limits, cond_b), off_c]},」
状態: 確定

#### 修正 8
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・_loosened_off の側を返す行）
直す前の文字:
~~~
        cc[\"side\"] = \"below\" if side == \"above\" else \"above\"\n
~~~
直した後の文字:
~~~
        if not is_not:\n            # ★not の中身（段2a の強さ）は側を返さない＝生成器の off_c と同じ向き（強さが戻ったら出る）\n            cc[\"side\"] = \"below\" if side == \"above\" else \"above\"\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3349「off_c["value"]["threshold_q"] = _loose_q_fixed(limits, strong["value"]["threshold_q"], strong_side)」
状態: 確定

#### 修正 10
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・_wrap_bundle の定義の行）
直す前の文字:
~~~
def _wrap_bundle(inner: list[dict], wrap: dict | None, limits, out_col: str) -> dict:
~~~
直した後の文字:
~~~
def _wrap_bundle(inner: list[dict], wrap: dict | None, limits, out_col: str, frames: list | None = None) -> dict:
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3381「"off": {"any": [_flip_loose(limits, cond_a), _flip_loose(limits, cond_b), off_c]},」
状態: 確定

#### 修正 12
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 13
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・_wrap_bundle の off の行）
直す前の文字:
~~~
\"off\": _loosened_off(conds, limits), 
~~~
直した後の文字:
~~~
\"off\": _loosened_off(conds, limits, frames), 
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3381「"off": {"any": [_flip_loose(limits, cond_a), _flip_loose(limits, cond_b), off_c]},」
状態: 確定

#### 修正 14
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・run_stage の keep から marks まで）
直す前の文字:
~~~
    keep = g.stage_keep_of(lm, len(cands))\n    dropped: list[dict] = []\n    if a.stage == \"width\":\n        base = [{\"判定\": \"（単独）\", \"内側\": [], \"枠\": []}]   # 帯の候補1本だけの束（重ねる相手なし）\n    elif a.stage == \"stage1\":\n        base = [{\"判定\": \"帯（W% above q50）\", \"内側\": [_q50_width_cond(lm)], \"枠\": [\"width\"]}]\n    else:\n        if not a.top:\n            raise SystemExit(f\"[R9] {a.stage} には --top <前の段の順位表.json> が要る（width・stage1 だけ無しで走れる）\")\n        base = _load_top(a.top, keep)\n    recipes = []\n    marks = {}\n    for t in base:\n        for c in cands:\n            i = len(recipes)\n            name = f\"{a.stage}_{i}\"\n            try:\n                if a.stage == \"stage3\":\n                    wrap = {\"持続n\": int(c[\"cond\"][\"value\"][\"n\"]),\n                            \"保つ上限\": int(g._nv_fixed(lm, \"state_hold_bars_range\", \"n\", i)[\"n\"]),\n                            \"role\": c[\"cond\"].get(\"role\")}\n                    inner = list(t[\"内側\"])\n                else:\n                    wrap = None\n                    inner = list(t[\"内側\"]) + [json.loads(json.dumps(c[\"cond\"]))]\n                bd = _wrap_bundle(inner, wrap, lm, f\"regime_{name}\")\n            except (SystemExit, KeyError, TypeError) as e:\n                dropped.append({\"場面\": \"組めない\", \"判定\": name, \"理由\": str(e)[:120]})\n                continue\n            recipes.append(_stage_recipe(a.strategy, name, bd))\n            marks[name] = {\"内側\": inner, \"枠\": list(t.get(\"枠\") or []) + [a.stage], \"包み\": wrap,\n                           \"前の束\": t.get(\"判定\"),\n                           \"候補\": {k: c.get(k) for k in (\"rank\", \"family\", \"tf\", \"col\")}}\n
~~~
直した後の文字:
~~~
    dropped: list[dict] = []\n    if a.stage == \"width\":\n        base = [{\"判定\": \"（単独）\", \"内側\": [], \"枠\": []}]   # 帯の候補1本だけの束（重ねる相手なし）\n    elif a.stage == \"stage1\":\n        base = [{\"判定\": \"帯（W% above q50）\", \"内側\": [_q50_width_cond(lm)], \"枠\": [\"width\"]}]\n    else:\n        if not a.top:\n            raise SystemExit(f\"[R9] {a.stage} には --top <前の段の順位表.json> が要る（width・stage1 だけ無しで走れる）\")\n        if (lm.get(\"stage_keep_range\") or {}).get(\"hi\") is None:\n            raise SystemExit(\"[R9] stage_keep_range の hi が未設定＝前の段の上位を絞れない（M2-F-7 の後に走らせる・fail-closed）\")\n        base = _load_top(a.top, None)\n    # ★渡す本数（keep）は、この段で測る束の本数に対して stage_keep_of で決める（監査 CP48）。\n    #   直す前＝候補の本数で決めた＝候補1本の段2b で keep＝1（上位1本しか渡らない）・hi＝10 では stage_keep_of が止まった。\n    _n_meas = len(base) * (len(cands) + (1 if a.stage == \"stage2c\" else 0))\n    _hi = (lm.get(\"stage_keep_range\") or {}).get(\"hi\")\n    keep = g.stage_keep_of(lm, max(_n_meas, int(_hi)) if _hi is not None else _n_meas)\n    base = base[:keep]\n    recipes = []\n    marks = {}\n    for t in base:\n        # ★段2c は「なし」（3枠目を足さない束）を必ず併走する（§2.2 の段2c・M2-F-13）\n        for j, c in enumerate(([None] if a.stage == \"stage2c\" else []) + list(cands)):\n            name = f\"{a.stage}_{len(recipes) + len(dropped)}\"\n            try:\n                if a.stage == \"stage3\":\n                    # ★保つ上限は候補の番号 j で決める＝前の束が違っても同じ候補なら同じ値（sample_regime_build の order_n と同じ組）\n                    wrap = {\"持続n\": int(c[\"cond\"][\"value\"][\"n\"]),\n                            \"保つ上限\": int(g._nv_fixed(lm, \"state_hold_bars_range\", \"n\", j)[\"n\"]),\n                            \"role\": c[\"cond\"].get(\"role\")}\n                    inner = list(t[\"内側\"])\n                elif c is None:\n                    wrap = None\n                    inner = list(t[\"内側\"])\n                else:\n                    wrap = None\n                    inner = list(t[\"内側\"]) + [json.loads(json.dumps(c[\"cond\"]))]\n                # ★枠は内側と同じ並び（段3 の包みと「なし」は条件を足さない＝枠も足さない・差し戻しが読む）\n                frames_in = list(t.get(\"枠\") or []) + ([] if (a.stage == \"stage3\" or c is None) else [a.stage])\n                bd = _wrap_bundle(inner, wrap, lm, f\"regime_{name}\", frames=frames_in)\n            except (SystemExit, KeyError, TypeError) as e:\n                dropped.append({\"場面\": \"組めない\", \"判定\": name, \"理由\": str(e)[:120]})\n                continue\n            if a.stage == \"stage3\":\n                # ★完成した束だけを G7（法則の審査）に掛ける（M2-F-14）。途中の段では掛けない（中身13 の (j)）\n                try:\n                    ex._check_scene_rules({\"name\": \"range\", \"build\": g.strip_marks(bd)}, \"\")\n                except ex.RecipeError as e:\n                    dropped.append({\"場面\": \"関所で拒否\", \"判定\": name, \"理由\": f\"G7: {str(e)[:120]}\"})\n                    continue\n            recipes.append(_stage_recipe(a.strategy, name, bd))\n            marks[name] = {\"内側\": inner, \"枠\": frames_in, \"包み\": wrap,\n                           \"前の束\": t.get(\"判定\"),\n                           \"候補\": (\"なし\" if c is None else {k: c.get(k) for k in (\"rank\", \"family\", \"tf\", \"col\")})}\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3164「if hi > int(n_cands):」
状態: 確定

#### 修正 16
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 344行（実装の指示 4 の中身・rank_rows のくり返し）
直す前の文字:
~~~
    dropped = []\n    for i, r in enumerate(ok, start=1):\n        r[\"順位\"] = i\n        if keep is not None and i > keep:\n
~~~
直した後の文字:
~~~
    dropped = []\n    k = 0\n    for i, r in enumerate(ok, start=1):\n        r[\"順位\"] = i\n        # ★比べる相手（RG-v5）は順位だけ付け、上位の枠（keep）を使わない・落ちた候補に数えない（束ではないため・監査 CP48）\n        if str(r.get(\"判定\", \"\")).startswith(\"RG-v5\"):\n            r[\"比べる相手\"] = True\n            continue\n        k += 1\n        if keep is not None and k > keep:\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py:146「if "range_ok_rg5" in df.columns:」
状態: 確定

#### 修正 18
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・run_sweep の本体）
直す前の文字:
~~~
    row = json.loads(pathlib.Path(a.sweep).read_text(encoding=\"utf-8\"))\n    if isinstance(row, list):\n        _c = [r for r in row if r.get(\"順位\") and r.get(\"内側\")]\n        if not _c:\n            raise SystemExit(f\"[R9] --sweep の順位表に、束（内側）を持つ行が1本も無い（fail-closed）\")\n        row = sorted(_c, key=lambda r: r[\"順位\"])[0]\n    inner = row.get(\"内側\")\n    frames = row.get(\"枠\")\n    wrap = row.get(\"包み\")\n    if not inner or not frames or len(inner) != len(frames):\n        raise SystemExit(\"[R9] --sweep の行に 内側 と 枠 が揃っていない（段の口が書いた順位表の行を渡す・fail-closed）\")\n    lm, _w = g.load_limits()\n    lm = g.resolve_hold_range(lm, a.strategy)\n    laws = g.laws_for_scene(\"range\")\n    table = g.load_signal_table()\n    _pool, tfs, _ = g.material_pool()\n    cands_of = {}\n    for st in set(frames):\n        cands_of[st] = (g.build_width_candidates(laws, table, tfs, lm) if st == \"width\"\n                        else g.build_stage_candidates(st, laws, table, tfs, lm))\n    dropped: list[dict] = []\n\n    def _measure_one(tag, variants):\n        recipes, marks = [], {}\n        for j, (nm, iv, wv) in enumerate(variants):\n            try:\n                bd = _wrap_bundle(iv, wv, lm, f\"regime_{tag}_{j}\")\n            except (SystemExit, KeyError, TypeError) as e:\n                dropped.append({\"場面\": \"組めない\", \"判定\": nm, \"理由\": str(e)[:120]})\n                continue\n            recipes.append(_stage_recipe(a.strategy, nm, bd))\n            marks[nm] = (iv, wv)\n        rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=False)\n        rows, _ = rank_rows(rows)\n        dropped.extend({\"場面\": (\"関所で拒否\" if str(r.get(\"注\", \"\")).startswith(\"関所で拒否\") else \"測れない\"),\n                        \"判定\": r.get(\"判定\"), \"理由\": r.get(\"注\")} for r in rows if \"①時間の割合\" not in r)\n        return rows, marks, len(recipes)\n\n    rows0, marks0, n0 = _measure_one(\"sweep_r0\", [(\"sweep_r0_base\", inner, wrap)])\n    best = next(r for r in rows0 if r.get(\"判定\") == \"sweep_r0_base\")\n    n_all = n0\n    rnd = 0\n    improved = True\n    while improved:\n        improved = False\n        rnd += 1\n        for k, st in enumerate(frames):\n            variants = []\n            for j, c in enumerate(cands_of[st]):\n                iv = json.loads(json.dumps(inner))\n                iv[k] = json.loads(json.dumps(c[\"cond\"]))\n                variants.append((f\"sweep_r{rnd}_f{k}_c{j}\", iv, wrap))\n            rows, marks, n = _measure_one(f\"sweep_r{rnd}_f{k}\", variants)\n            n_all += n\n            cand_best = next((r for r in rows if r.get(\"判定\") in marks and \"①時間の割合\" in r), None)\n            if cand_best is not None and rank_key(cand_best) < rank_key(best):\n                best = cand_best\n                inner = marks[cand_best[\"判定\"]][0]\n                improved = True\n            write_outputs(f\"sweep_r{rnd}_f{k}\", rows, [])\n            print(f\"[差し戻し] 周 {rnd}・枠 {k}（{st}）＝いまの最良 {best.get('判定')}\")\n    best_row = dict(best)\n    best_row[\"内側\"] = inner\n    best_row[\"枠\"] = frames\n    best_row[\"包み\"] = wrap\n    write_outputs(\"sweep_final\", [best_row], dropped)\n    _record(a, \"sweep\", n_all)\n
~~~
直した後の文字:
~~~
    got = json.loads(pathlib.Path(a.sweep).read_text(encoding=\"utf-8\"))\n    rows_in = got if isinstance(got, list) else [got]\n    tops = sorted([r for r in rows_in if r.get(\"内側\") and not r.get(\"dropped_by\")],\n                  key=lambda r: (r.get(\"順位\") is None, r.get(\"順位\") or 0))\n    if not tops:\n        raise SystemExit(\"[R9] --sweep の順位表に、束（内側）を持つ行が1本も無い（fail-closed）\")\n    lm, _w = g.load_limits()\n    lm = g.resolve_hold_range(lm, a.strategy)\n    # ★M2-F-15＝上位（stage_keep_of の本数）の束ごとに差し戻し、最終の束を最大 keep 本 出す（監査 CP48・直す前は1位の1本だけ）\n    _hi = (lm.get(\"stage_keep_range\") or {}).get(\"hi\")\n    keep = g.stage_keep_of(lm, max(len(tops), int(_hi)) if _hi is not None else len(tops))\n    laws = g.laws_for_scene(\"range\")\n    table = g.load_signal_table()\n    _pool, tfs, _ = g.material_pool()\n    cands_of = {}\n    dropped: list[dict] = []\n    finals = []\n    n_all = 0\n\n    def _measure_one(tag, variants):\n        recipes, marks = [], {}\n        for j, (nm, iv, wv, fv) in enumerate(variants):\n            try:\n                bd = _wrap_bundle(iv, wv, lm, f\"regime_{tag}_{j}\", frames=fv)\n            except (SystemExit, KeyError, TypeError) as e:\n                dropped.append({\"場面\": \"組めない\", \"判定\": nm, \"理由\": str(e)[:120]})\n                continue\n            if wv:\n                # ★段3 の包みを持つ束（完成した束）は G7 に掛ける（M2-F-14 と同じ・入れ替えで法則を破った束を残さない）\n                try:\n                    ex._check_scene_rules({\"name\": \"range\", \"build\": g.strip_marks(bd)}, \"\")\n                except ex.RecipeError as e:\n                    dropped.append({\"場面\": \"関所で拒否\", \"判定\": nm, \"理由\": f\"G7: {str(e)[:120]}\"})\n                    continue\n            recipes.append(_stage_recipe(a.strategy, nm, bd))\n            marks[nm] = (iv, wv)\n        rows = measure(df, recipes, SEARCH_START, SEARCH_END, with_trades=False)\n        rows, _ = rank_rows(rows)\n        dropped.extend({\"場面\": (\"関所で拒否\" if str(r.get(\"注\", \"\")).startswith(\"関所で拒否\") else \"測れない\"),\n                        \"判定\": r.get(\"判定\"), \"理由\": r.get(\"注\")} for r in rows if \"①時間の割合\" not in r)\n        return rows, marks, len(recipes)\n\n    for b_i, row in enumerate(tops[:keep]):\n        inner = row.get(\"内側\")\n        frames = row.get(\"枠\") or []\n        wrap = row.get(\"包み\")\n        cf = list(frames[:len(inner or [])])\n        if not inner or len(cf) != len(inner):\n            raise SystemExit(\"[R9] --sweep の行に 内側 と 枠 が揃っていない（段の口が書いた順位表の行を渡す・fail-closed）\")\n        # ★入れ直す枠＝条件の枠（内側と同じ並び）＋段3 の包みが在れば持続（streak の本数）の枠\n        slots = list(cf) + ([\"stage3\"] if wrap else [])\n        for st in slots:\n            if st not in cands_of:\n                cands_of[st] = (g.build_width_candidates(laws, table, tfs, lm) if st == \"width\"\n                                else g.build_stage_candidates(st, laws, table, tfs, lm))\n        base_nm = f\"sweep_b{b_i}_r0_base\"\n        rows0, _m0, n0 = _measure_one(f\"sweep_b{b_i}_r0\", [(base_nm, inner, wrap, cf)])\n        best = next((r for r in rows0 if r.get(\"判定\") == base_nm), {\"判定\": base_nm})\n        n_all += n0\n        rnd = 0\n        improved = True\n        while improved:\n            improved = False\n            rnd += 1\n            for k, st in enumerate(slots):\n                variants = []\n                for j, c in enumerate(cands_of[st]):\n                    nm = f\"sweep_b{b_i}_r{rnd}_f{k}_c{j}\"\n                    if k < len(cf):\n                        iv = json.loads(json.dumps(inner))\n                        iv[k] = json.loads(json.dumps(c[\"cond\"]))\n                        variants.append((nm, iv, wrap, cf))\n                    else:\n                        wv = dict(wrap)\n                        wv[\"持続n\"] = int(c[\"cond\"][\"value\"][\"n\"])\n                        variants.append((nm, inner, wv, cf))\n                rows, marks, n = _measure_one(f\"sweep_b{b_i}_r{rnd}_f{k}\", variants)\n                n_all += n\n                cand_best = next((r for r in rows if r.get(\"判定\") in marks and \"①時間の割合\" in r), None)\n                if cand_best is not None and rank_key(cand_best) < rank_key(best):\n                    best = cand_best\n                    inner, wrap = marks[cand_best[\"判定\"]]\n                    improved = True\n                write_outputs(f\"sweep_b{b_i}_r{rnd}_f{k}\", rows, [])\n                print(f\"[差し戻し] 束 {b_i}・周 {rnd}・枠 {k}（{st}）＝いまの最良 {best.get('判定')}\")\n        best_row = dict(best)\n        best_row[\"内側\"] = inner\n        best_row[\"枠\"] = frames\n        best_row[\"包み\"] = wrap\n        best_row[\"差し戻しの元\"] = row.get(\"判定\")\n        finals.append(best_row)\n    finals, _ = rank_rows(finals)\n    write_outputs(\"sweep_final\", finals, dropped)\n    _record(a, \"sweep\", n_all)\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:2033「| **M2-F-15** | 段4 差し戻し＝M2-F-4 で作った口を使い、良くならなくなるまで繰り返して、最終の10本を出す | まだ |」
状態: 確定

#### 修正 20
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 21
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・run_nan_check の材料の読み方）
直す前の文字:
~~~
            if col not in dfx.columns:\n                print(f\"  ❌ {col}: 列がデータに無い\")\n                ng += 1\n                continue\n            arr = ex._apply_pre(dfx[col].to_numpy(float), pre)\n
~~~
直した後の文字:
~~~
            # ★材料は実行データの列に無い（実行器がその場で作る）＝_col_array で、前処理（動く線）まで実行器と同じ式で作る（監査 CP48）\n            try:\n                arr = ex._col_array(dfx, base[\"material\"][0], g._geo_of(dfx), \"\")\n            except ex.RecipeError as e:\n                print(f\"  ❌ {col}: 材料を作れない（{str(e)[:80]}）\")\n                ng += 1\n                continue\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:2101「return material_array(df, name)」
状態: 確定

#### 修正 22
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 23
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 349行（実装の指示 9 の中身の末尾・番人⑩の後）
直す前の文字:
~~~
        ng.append(\"⑩: 並べる鍵（2つの先読みの平均）か 成績下位 が違う\")
~~~
足す文字:
~~~
\n    # ⑪ 段の口が組む束（判定の束だけ・入口の木は空）を、合成データで最後まで測れる（束を組む→解決表→列→3つの割合・関所で拒否の行・監査 CP48）\n    _n11 = 2000\n    _c11 = 100.0 + (np.arange(_n11) % 7)\n    _df11 = pd.DataFrame({\"ts\": pd.date_range(\"2024-03-01\", periods=_n11, freq=\"5min\"), \"close\": _c11,\n                          \"v11_res_hi\": _c11 * (1.0 + (np.arange(_n11) % 5) / 1000.0), \"v11_res_lo\": _c11,\n                          \"v11_sup_hi\": _c11, \"v11_sup_lo\": _c11 * 0.99, \"v11_mid\": _c11})\n    _w11 = {\"role\": \"location\", \"form\": \"level\", \"material\": [{\"geo\": \"W%\"}], \"side\": \"above\",\n            \"value\": {\"threshold_q\": \"q50\"}}\n    _rec11 = [_stage_recipe(\"e38\", \"t11_ok\", _wrap_bundle([_w11], None, None, \"regime_t11_ok\")),\n              _stage_recipe(\"e38\", \"t11_ng\", _wrap_bundle([{\"not\": {\"bool_col\": \"t11_no_such_col\", \"want\": True}}],\n                                                          None, None, \"regime_t11_ng\"))]\n    try:\n        _rows11 = measure(_df11, _rec11, _df11[\"ts\"].iloc[0], _df11[\"ts\"].iloc[-1], with_trades=False)\n        _ok11 = [r for r in _rows11 if r.get(\"判定\") == \"t11_ok\" and \"①時間の割合\" in r and \"捉えた(先24本)\" in r]\n        _ng11 = [r for r in _rows11 if r.get(\"判定\") == \"t11_ng\" and str(r.get(\"注\", \"\")).startswith(\"関所で拒否\")]\n        if not _ok11 or not _ng11:\n            ng.append(f\"⑪: 段の口の束を測れない（測れた {len(_ok11)}・関所で拒否 {len(_ng11)}）\")\n    except BaseException as _e11:\n        ng.append(f\"⑪: 段の口の束を測る所で止まった: {type(_e11).__name__} {str(_e11)[:80]}\")
~~~
根拠の抜き書き: .claude/state/acceptance.md:1531「| 5 | 自己テストが全部 通る（①〜⑩・実データの試行ゼロ） |」
状態: 確定

#### 修正 24
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 25
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 283行（完成の条件 #5）
直す前の文字:
~~~
自己テストが全部 通る（①〜⑩・実データの試行ゼロ）
~~~
直した後の文字:
~~~
自己テストが全部 通る（①〜⑪・実データの試行ゼロ・⑪＝段の口の束を合成データで最後まで測れる）
~~~
根拠の抜き書き: .claude/state/acceptance.md:1531「| 5 | 自己テストが全部 通る（①〜⑩・実データの試行ゼロ） |」
状態: 確定

#### 修正 26
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 27
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 15〜17行（TARGET）
直す前の文字:
~~~
  "TARGET": [
    "scripts/priority_rebuild/regime_r9_diag.py"
  ],
~~~
直した後の文字:
~~~
  "TARGET": [
    "scripts/priority_rebuild/regime_r9_diag.py",
    ".claude/breaks/b97_demand_not_attached.sh"
  ],
~~~
根拠の抜き書き: .claude/breaks/b97_demand_not_attached.sh:31「measure python3 "$PR/regime_r9_diag.py" --recipe "$PR/recipes/r9_demand_fixture.json" --no-trades」
状態: 確定

#### 修正 28
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 29
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 361行（実装の指示 21 の末尾）
直す前の文字:
~~~
new = '    pass  # b116 が壊した（落ちた候補を書かない）\\n'\nopen(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))\nPYEOF\n\nmeasure python3 \"$DIAG\" --selftest\nfinish\n", "根拠の抜き書き": ".claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」", "状態": "確定"}
~~~
足す文字:
~~~
,
    {"番号": 22, "対象のファイル": ".claude/breaks/b97_demand_not_attached.sh", "直す箇所": "31行（測るコマンド）", "直す前の文字": "measure python3 \"$PR/regime_r9_diag.py\" --recipe \"$PR/recipes/r9_demand_fixture.json\" --no-trades", "種類": "直した後の文字", "中身": "measure python3 \"$PR/regime_r9_diag.py\" --recipe \"$PR/recipes/r9_demand_fixture.json\" --purpose check", "根拠の抜き書き": ".claude/breaks/b97_demand_not_attached.sh:31「measure python3 \"$PR/regime_r9_diag.py\" --recipe \"$PR/recipes/r9_demand_fixture.json\" --no-trades」", "状態": "確定"},
    {"番号": 23, "対象のファイル": ".claude/breaks/b97_demand_not_attached.sh", "直す箇所": "18行（控えに写すファイル）", "直す前の文字": "guard \"$DIAG\"", "種類": "直した後の文字", "中身": "guard \"$DIAG\" \"$SDK/.claude/ratchet/engine_tuner_check_runs.json\"", "根拠の抜き書き": ".claude/breaks/b97_demand_not_attached.sh:18「guard \"$DIAG\"」", "状態": "確定"}
~~~
根拠の抜き書き: .claude/breaks/b97_demand_not_attached.sh:18「guard "$DIAG"」
状態: 確定

#### 修正 30
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 31
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 218行（4-13 の7）
直す前の文字:
~~~
      "7. **壊すプログラム。**なぜ作るかの後に grep で確かめ、当たった壊すプログラムが探す行は消しません（L-605）。",
~~~
直した後の文字:
~~~
      "7. **壊すプログラム。**なぜ作るかの後に grep で確かめ、当たった壊すプログラムが探す行は消しません（L-605）。★監査 CP48＝この道具のファイル名で .claude/breaks を grep すると2本 当たる。b84＝探す行 qt = qt_all は残り、測るのは組む側の自己テスト T38＝この工事の後も通る。b97＝測るコマンドが --no-trades を使い --purpose が無い＝この工事の後は argparse が rc=2 で止め、完成の条件 AUDIT-5 の番人が壊れる。b97 は実装の指示 22・23 で直し（--purpose check・確認の帳簿を控えに写して戻す）、実装の後に run_breaks.py --design v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2e2-cp36-major-20260914.md --measure-only --only b97_demand_not_attached.sh で測る。",
~~~
根拠の抜き書き: .claude/breaks/b97_demand_not_attached.sh:31「measure python3 "$PR/regime_r9_diag.py" --recipe "$PR/recipes/r9_demand_fixture.json" --no-trades」
状態: 確定

#### 修正 32
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

### Major

#### 修正 33
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 349行（実装の指示 9 の中身・番人⑥の反転の検査の前）
直す前の文字:
~~~
    colX = (np.arange(n) % 3 == 0)\n
~~~
直した後の文字:
~~~
    # ⑥ の既知答え（設計書 4-19 の通しの例1）＝8本・強さが真は1・3・5・7本目・判定は2・4本目だけ真 → 0.5（監査 CP48）\n    _s8 = (np.arange(8) % 2 == 0)\n    _c8 = np.isin(np.arange(8), [1, 3])\n    if r9_catch_share(_c8, _s8, np.ones(8, bool)) != 0.5:\n        ng.append(\"⑥: 既知答え（8本・判定2本／正解レンジ4本＝0.5）にならない\")\n    # ⑥ 使えない印のバーは分母に入れない（8本目を使えないにすると 2÷3）\n    if abs(r9_catch_share(_c8, _s8, np.arange(8) != 7) - 2.0 / 3.0) > 1e-12:\n        ng.append(\"⑥: 使えない印のバーを分母から外していない\")\n    colX = (np.arange(n) % 3 == 0)\n
~~~
根拠の抜き書き: .claude/state/acceptance.md:274「**通しの例1（捉えた割合の既知答え・合成データ）。**バーが8本。」
状態: 確定

#### 修正 34
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 35
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 349行（実装の指示 9 の中身・番人⑦）
直す前の文字:
~~~
        if isinstance(node, ast.Attribute) and node.attr in (\"default_rng\", \"sample_structure\"):\n            ng.append(f\"⑦: 乱数の道が残っている: {node.attr} 行 {node.lineno}\")\n
~~~
直した後の文字:
~~~
        _nm7 = node.attr if isinstance(node, ast.Attribute) else (node.id if isinstance(node, ast.Name) else None)\n        if _nm7 in (\"default_rng\", \"sample_structure\", \"random\", \"RandomState\"):\n            ng.append(f\"⑦: 乱数の道が残っている: {_nm7} 行 {node.lineno}\")\n        if isinstance(node, ast.Import) and any(al.name.split(\".\")[-1] == \"random\" for al in node.names):\n            ng.append(f\"⑦: 乱数の import が残っている: 行 {node.lineno}\")\n        if isinstance(node, ast.ImportFrom) and (node.module or \"\").split(\".\")[-1] == \"random\":\n            ng.append(f\"⑦: 乱数の import が残っている: 行 {node.lineno}\")\n
~~~
根拠の抜き書き: .claude/state/acceptance.md:1528「| 2 | 乱数がこの道具に残っていない（⑦＝default_rng・sample_structure を構文木で見る・恒久67番） |」
状態: 確定

#### 修正 36
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 37
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 349行（実装の指示 9 の中身・番人⑧）
直す前の文字:
~~~
        ng.append(\"⑧: 試行を数える口（record_run）が1回も呼ばれていない\")\n
~~~
直した後の文字:
~~~
        ng.append(\"⑧: 試行を数える口（record_run）が1回も呼ばれていない\")\n    # ⑧ 測る口（main・run_stage・run_sweep）が、それぞれ試行を数える _record を呼ぶ（監査 CP48）\n    for _fn8 in (\"main\", \"run_stage\", \"run_sweep\"):\n        _d8 = [f for f in tree.body if isinstance(f, ast.FunctionDef) and f.name == _fn8]\n        if not _d8 or not any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == \"_record\" for x in ast.walk(_d8[0])):\n            ng.append(f\"⑧: 測る口 {_fn8} が試行を数える _record を呼んでいない\")\n
~~~
根拠の抜き書き: .claude/state/acceptance.md:1529「| 3 | 試行を累積に数える口が呼ばれている（⑧＝record_run の呼び出しを構文木で見る・§2.2・恒久24番） |」
状態: 確定

#### 修正 38
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 39
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 130〜136行（4-4 処理の流れ）
直す前の文字:
~~~
      "1. 当てる道具（apply_audit_fix.py --design）で実装の指示 1〜17 を当て、壊すプログラム4本（実装の指示 18〜21）を Write ツールで書きます。",
      "2. 構文を確かめ、regime_r9_diag.py --selftest を走らせ、⑥〜⑩の行を見ます。",
      "3. 固定のレシピを --purpose check で走らせ（python3 regime_r9_diag.py --recipe recipes/r9_demand_fixture.json --purpose check）、順位表と落ちた候補のファイルが書かれることを見ます。",
      "4. 壊すプログラム b113〜b116 を1本ずつ測ります（run_breaks.py）。",
      "5. M2-F-7＝search_limits.json の stage_keep_range の hi に 10 を書き、G2 → H2 の順で印を取り直します（設定は H2 の対象のため・約6分半）。",
      "6. 完成の条件の表の全部のコマンドを走らせ、承認をお願いします。",
      "7. 実装の監査（6段の⑤）に出します。"
~~~
直した後の文字:
~~~
      "1. 当てる道具（apply_audit_fix.py --design）で実装の指示を当て、壊すプログラムの新しいファイル（実装の指示 18〜21・24）を Write ツールで書き、b97 を実装の指示 22・23 のとおり Edit ツールで直します（壊すプログラムは当てる道具の NEVER_WRITE のため）。",
      "2. 構文を確かめ、regime_r9_diag.py --selftest を走らせ、⑥〜⑪の行を見ます。",
      "3. 壊すプログラム b113〜b117 を1本ずつ測ります（run_breaks.py --measure-only）。b97 は m2e2-cp36-major-20260914 の控えの設計書で --measure-only --only b97_demand_not_attached.sh を測ります。",
      "4. M2-F-7＝search_limits.json の stage_keep_range の hi に 10 を書き、G2 → H2 の順で印を取り直します（設定は H2 の対象のため・約6分半）。",
      "5. ★固定のレシピ（完成の条件 #6）は、ここではまだ走らせません（監査 CP48）。7-8 の SPEC と 7-7 の定義の行は直す前の実物から作られているので、実装の後は設計↔実装ゲート（require_design_contract_before_run.sh の --diff）が --selftest 以外の走行を止めます。gen_acceptance.py --write で設計書を作り直し（SPEC と定義の行を実物から取り直す）、verify_design_contract.py --diff が齟齬0件なのを確かめて、2回目の承認をお願いします。",
      "6. 2回目の承認の後に、固定のレシピを --purpose check で走らせ（python3 regime_r9_diag.py --recipe recipes/r9_demand_fixture.json --purpose check）、順位表と落ちた候補のファイルが書かれることを見て、①③を M2-F-1 の実測（①5.30%・③50.3%／51.4%）と並べて貼ります。",
      "7. 実装の監査（6段の⑤）に出します。"
~~~
根拠の抜き書き: .claude/hooks/require_design_contract_before_run.sh:360「DOUT=$(python3 "$VERIFY" --diff "$USE_MD" 2>&1)」
状態: 確定

#### 修正 40
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 41
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 200行（4-14 の最後の行）
直す前の文字:
~~~
      "| 壊すプログラム1本 | selftest 1回ぶん＋数秒 | b109〜b112 と同じ形（自己テストを測る） |"
~~~
足す文字:
~~~
,
      "| 段4 の差し戻し（--sweep・上位 keep 本） | かけ算の目安＝束1本の時間 × 周の数 × keep 本 ×（帯の幅＋段1＋段2a＋段2b＋段2c＋段3 の候補の本数）。★実測ではない・周の数は走らせるまで分からない | M2-F-5 の --limit で測った束1本の時間を掛けて M2-F-15 のフロー宣言に書く。見込みが要件 R7 の30分を超えるなら、走らせる前に まこさんに出す（監査 CP48） |"
~~~
根拠の抜き書き: .claude/state/acceptance.md:373「| 段1 の走行（--stage stage1・336本） | かけ算の目安＝約49分」
状態: 確定

#### 修正 42
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 43
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 352行（実装の指示 12 の中身の末尾）
直す前の文字:
~~~
    ap.add_argument(\"--nan-check\", action=\"store_true\",\n                    help=\"BB幅 の動く線の材料の値なしを数える（リスク8・まこさん決定「案1」・測らない）\")
~~~
足す文字:
~~~
\n    ap.add_argument(\"--limit\", type=int, default=None,\n                    help=\"--stage で測る束を先頭から N本 だけにする（束1本の時間の実測のため・M2-F-5・道具の確認なので --purpose check）\")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:2091「→ 段1 の束を数本 測る。」
状態: 確定

#### 修正 44
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 45
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・run_stage の測る前の印字）
直す前の文字:
~~~
    print(f\"[R9] {a.stage}＝前の束
~~~
直した後の文字:
~~~
    if a.limit:\n        recipes = recipes[:int(a.limit)]\n    print(f\"[R9] {a.stage}＝前の束
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:2091「→ 段1 の束を数本 測る。」
状態: 確定

#### 修正 46
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 47
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 251行（決めてほしいこと）
直す前の文字:
~~~
    {"中身": "無し（この設計書で新しく決めることはありません）。順位の鍵（平均）・書き先・口3つ・乱数の撤去・--nan-check は 2026-09-27 に決定済み、渡す本数10本と束3 のまとめ方は 2026-09-18・2026-09-24 に決定済みです", "私の案": "—", "出どころ": "worklog 20260927 §16・まこさん決定「１は平均でOK」「了解。進めて良い」"}
~~~
直した後の文字:
~~~
    {"中身": "段2c で C3（実データで動きがほぼ同じ指標は片方を外す）を掛けるか。M2-F-13 の中身は「C2（段2a と同じ系統は不可）と C3（動きが重なる組は落とす）で落とします」と書き、法則ファイルの C3 は「使う段: M2-G」で機械が読む判定を持たない（G7 でも落ちない）。この設計書の段の口は C2・C3 を掛けない", "私の案": "C3 は M2-G に任せ、段2c では掛けない（C2 は、段2c の候補が法則 R6 の名指しした family だけで段2a の系統と重ならないので、候補の作りで満たす）。M2-F-13 の中身の文を直すかは まこさんが決める", "出どころ": "engine_tuner_milestones2.md の M2-F-13・regime_laws.json の C3（監査 CP48）"},
    {"中身": "段3 で何を探すか。§2.2 の段3 は「成立の連続本数と解除の緩め幅・n＝state_hold_bars_range の範囲／緩め幅＝_loose_q の分位差」と書き、M2-F-14 は「streak（続く本数 n＝3〜24 の22通り）と hysteresis（解除の緩め幅・保つ上限 24〜288）を掛けて・測った本数＝10本 × 22通り」と書く。この設計書の段の口は streak の本数だけを候補にし、保つ上限は候補の番号で決まる1つの値、緩め幅は隣の段の1つに固定する＝保つ上限の範囲の大半と、ほかの緩め幅は段3 で1度も試されない", "私の案": "M2-F-14 の本数（10本 × 22通り）のまま進め、保つ上限と緩め幅は段5（詰め）で範囲から開く。M2-F-14 と §2.2 の段3 の文を揃えるかは まこさんが決める", "出どころ": "engine_tuner_milestones2.md の §2.2 の段3・M2-F-14（監査 CP48）"}
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:2188「C2（段2a と同じ系統は不可）と C3（動きが重なる組は落とす）で落とします。」
状態: 未決

#### 修正 48
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 49
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 24〜25行（NEW_FILE の最後）
直す前の文字:
~~~
    ".claude/breaks/b116_dropped_file_not_written.sh"
  ],
~~~
直した後の文字:
~~~
    ".claude/breaks/b116_dropped_file_not_written.sh",
    ".claude/breaks/b117_stage_recipe_no_entry.sh"
  ],
~~~
根拠の抜き書き: .claude/rules/permanent_rules.md:387「**いままでどおり。**壊すプログラムで守る・完成の条件に載せる・監査に出す」
状態: 確定

#### 修正 50
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 51
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 361〜363行（実装の指示の配列の末尾）
直す前の文字:
~~~
"状態": "確定"}
  ]
}
~~~
直した後の文字:
~~~
"状態": "確定"},
    {"番号": 24, "対象のファイル": ".claude/breaks/b117_stage_recipe_no_entry.sh", "直す箇所": "なし（新しいファイル）", "直す前の文字": "なし", "種類": "足す文字", "中身": "#!/bin/bash\n# EXPECT_RC: 1\n# MEANS: 段の口の束から入口の木を外すと、番人⑪が「段の口の束を測る所で止まった」で落ちた\n# EXPECT_MSG: ❌ ⑪\n# b117 — _stage_recipe から入口の木（entry）を外すと、⑪が落ちるか（M2-F-2・監査 CP48）\n#   守っているもの＝完成の条件 #7（段の口が組む束を、合成データで最後まで測れる）\n#   壊し方＝_stage_recipe の入口の木の行を、閉じ括弧だけの行に替える（入口の木の無い束に戻す）。\n#   期待＝regime_r9_diag.py --selftest の⑪が落ちる（終了コード 1）。\n#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。\nsource \"$(dirname \"$0\")/lib.sh\"\n\nDIAG=\"$PR/regime_r9_diag.py\"\nguard \"$DIAG\"\n\npython3 - \"$DIAG\" <<'PYEOF'\nimport sys\np = sys.argv[1]\ns = open(p, encoding='utf-8').read()\nold = '            \"entry\": {\"connective\": {\"all\": []}}}\\n'\nif s.count(old) != 1:\n    raise SystemExit(\"[b117] 壊す対象の行が1か所でない: \" + old.strip())\nnew = '            }  # b117 が壊した（入口の木を外す）\\n'\nopen(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))\nPYEOF\n\nmeasure python3 \"$DIAG\" --selftest\nfinish\n", "根拠の抜き書き": ".claude/breaks/b104_atr1h_own_tf.sh:1「#!/bin/bash」", "状態": "確定"}
  ]
}
~~~
根拠の抜き書き: .claude/rules/permanent_rules.md:387「**いままでどおり。**壊すプログラムで守る・完成の条件に載せる・監査に出す」
状態: 確定

#### 修正 52
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 53
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 284行（完成の条件 #6 の末尾）
直す前の文字:
~~~
--recipe recipes/r9_demand_fixture.json --purpose check", "経路": "実経路", "壊し方": "壊すプログラムは付けない（書けなければ rc≠0 か ⑨が落ちる）", "壊すプログラム": "—", "監査確認": "—", "いまの状態": "未着手"}
~~~
足す文字:
~~~
,
    {"条件": "段の口が組む束（判定の束だけ・入口の木は空）を、合成データで最後まで測れる（⑪＝束を組む→解決表→列→3つの割合・関所で拒否の行）", "コマンド": "python3 scripts/priority_rebuild/regime_r9_diag.py --selftest", "経路": "実経路", "壊し方": "段の口の束から入口の木を外すと、⑪が『❌』で落ちる", "壊すプログラム": "b117_stage_recipe_no_entry.sh", "監査確認": "—", "いまの状態": "未着手"}
~~~
根拠の抜き書き: .claude/rules/permanent_rules.md:387「**いままでどおり。**壊すプログラムで守る・完成の条件に載せる・監査に出す」
状態: 確定

#### 修正 54
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 55
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_todo.json
直す箇所: 1217行（M2-F-13 の確かめ方）
直す前の文字:
~~~
      "確かめ方": "測った本数＝10本 ×（候補数＋1）。「なし」の行が在る。",
~~~
直した後の文字:
~~~
      "確かめ方": "測った本数＝10本 ×（候補数＋1）。「なし」の行が在る。★走らせる前に regime_r9_diag.py --nan-check が rc=0（値決め窓・確認窓の動く線の材料に値なし 0本）であることを確かめ、値なしが在れば止まって まこさんに出す（M2-E-4e のリスク8・まこさん決定「案1」・監査 CP48）。",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:2062「この設計書に、BB幅 の動く線の材料の値なし（NaN）の本数を」
状態: 確定

#### 修正 56
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_regime_kb.py --write todo
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:396「→ `gen_regime_kb.py --write todo`（§3・1,557行・hash=d85c16bb…）」
状態: 確定

### Minor

#### 修正 57
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 55行（なぜ作るかの2行目のコマンド）
直す前の文字:
~~~
"コマンド": "grep -c '順位' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py"
~~~
直した後の文字:
~~~
"コマンド": "grep -c 'rank_key' v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py:194「print("順位\t指標\t時間足\t列\t分離力")」
状態: 確定

#### 修正 58
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 59
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 120〜127行（4-3 の表）
直す前の文字:
~~~
      "| _q50_width_cond・_loosened_off・_wrap_bundle・_load_top | 段1 の帯・段3 の包み（hysteresis）・前の段の上位の読み込み | **新設**（実装の指示 8） |",
      "| run_stage・run_sweep・run_nan_check | 段の口・差し戻しの口・値なしの口 | **新設**（実装の指示 8） |",
      "| _row（measure の中） | 当たった・捉えた・正解レンジの列を足す | 直す（実装の指示 5） |",
      "| measure | 関所（G5 ほか）の拒否を行として残す | 直す（実装の指示 6） |",
      "| _print_rows | 順位と新しい列を画面に出す | 直す（実装の指示 9） |",
      "| main | --trades・--purpose・--stage・--top・--sweep・--nan-check・stage_warm・sample_regime_build・record_run・ファイル書き | 直す（実装の指示 10〜15） |",
      "| selftest の⑥〜⑩ | 捉えた割合の既知答え・乱数0件・record_run・落ちた候補の5つの場面・並べる鍵 | 直す（実装の指示 16・17） |",
      "| b113〜b116 | 番人⑥⑦⑧⑨を壊して測る | **新設**（実装の指示 18〜21） |"
~~~
直した後の文字:
~~~
      "| _q50_width_cond・_loosened_off・_wrap_bundle・_load_top・_stage_recipe・_record | 段1 の帯・段3 の包み（hysteresis）・前の段の上位の読み込み・束だけのレシピ・試行の記録 | **新設**（実装の指示 7） |",
      "| run_stage・run_sweep・run_nan_check | 段の口・差し戻しの口・値なしの口 | **新設**（実装の指示 7） |",
      "| _nanmean | 並べる鍵の平均（nan を除く） | **新設**（実装の指示 4） |",
      "| _row（measure の中） | 当たった・捉えた・正解レンジの列を足す | 直す（実装の指示 5） |",
      "| measure | 関所（G5 ほか）の拒否を行として残す | 直す（実装の指示 6） |",
      "| _print_rows | 順位と新しい列を画面に出す | 直す（実装の指示 8） |",
      "| main | --trades・--purpose・--stage・--top・--sweep・--nan-check・stage_warm・sample_regime_build・record_run・ファイル書き | 直す（実装の指示 11〜16） |",
      "| selftest の⑥〜⑪ | 捉えた割合の既知答え・乱数0件・record_run・落ちた候補の5つの場面・並べる鍵・段の口の束 | 直す（実装の指示 9・10） |",
      "| b113〜b117 | 番人⑥⑦⑧⑨⑪を壊して測る | **新設**（実装の指示 18〜21・24） |",
      "| b97 | 固定のレシピの需給の列の番人（AUDIT-5）を新しい旗で測る | 直す（実装の指示 22・23） |"
~~~
根拠の抜き書き: .claude/state/acceptance.md:249「| _q50_width_cond・_loosened_off・_wrap_bundle・_load_top | 段1 の帯・段3 の包み（hysteresis）・前の段の上位の読み込み | **新設**（実装の指示 8） |」
状態: 確定

#### 修正 60
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 61
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 344行（実装の指示 4 の中身・write_outputs）
直す前の文字:
~~~
    dp = OUT_DIR / f\"dropped_{tag}_{stamp}.json\"\n
~~~
足す文字:
~~~
    if rp.exists() or dp.exists():\n        raise SystemExit(f\"[R9] 同じ名前のファイルが既に在る＝上書きしない（fail-closed）: {rp.name}\")\n
~~~
根拠の抜き書き: .claude/state/acceptance.md:355「日時つき＝上書きしない」
状態: 確定

#### 修正 62
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 63
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 344行（実装の指示 4 の中身・rank_key の第一キー）
直す前の文字:
~~~
    t3 = _nanmean([v for k, v in r.items() if k.startswith(\"③\")])\n
~~~
直した後の文字:
~~~
    _t3s = [v for k, v in r.items() if k.startswith(\"③\")]\n    # ★先読みの片方でも nan なら平均を取らない（1つだけの数字で並べない＝測れない束と同じく最後・監査 CP48）\n    t3 = _nanmean(_t3s) if _t3s and all(v == v for v in _t3s) else float(\"nan\")\n
~~~
根拠の抜き書き: .claude/state/acceptance.md:1489「| **並べる鍵の平均は、両方の先読みが揃わない束をどう扱うか** | nan を除いた平均です（片方だけ nan なら残りの1つ）。」
状態: 確定

#### 修正 64
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 65
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 308行（塞げないもの4）
直す前の文字:
~~~
    {"問い": "並べる鍵の平均は、両方の先読みが揃わない束をどう扱うか", "塞げないこと": "nan を除いた平均です（片方だけ nan なら残りの1つ）。両方 nan は最後に置きます。この扱いは私の設計です（正本に書かれていない）"},
~~~
直した後の文字:
~~~
    {"問い": "並べる鍵の平均は、両方の先読みが揃わない束をどう扱うか", "塞げないこと": "片方の先読みでも nan なら平均を取らず、測れない束と同じく最後に置きます（監査 CP48 で、nan を除いた平均＝残りの1つで並べる形から直した）。捉えた割合（第二キー）は nan を除いた平均のままです。この扱いは正本に書かれていません"},
~~~
根拠の抜き書き: .claude/state/acceptance.md:1489「| **並べる鍵の平均は、両方の先読みが揃わない束をどう扱うか** | nan を除いた平均です（片方だけ nan なら残りの1つ）。」
状態: 確定

#### 修正 66
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 67
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の中身・_q50_width_cond の戻り）
直す前の文字:
~~~
    return json.loads(json.dumps(cw[0][\"cond\"]))\n
~~~
直した後の文字:
~~~
    if not (cw and \"geo\" in ((cw[0][\"cond\"].get(\"material\") or [{}])[0])):\n        raise SystemExit(\"[R9] 帯の幅の候補の先頭がレンジ幾何でない（法則 R7 の geo が空・fail-closed）\")\n    return json.loads(json.dumps(cw[0][\"cond\"]))\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3012「for g in geo_names:」
状態: 確定

#### 修正 68
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 69
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 219行（4-13 の8）
直す前の文字:
~~~
      "8. **RG-v5 の行。**比べる相手として順位表に載り、順位も付きますが、束（内側）を持たないので --top には拾われません。"
~~~
直した後の文字:
~~~
      "8. **RG-v5 の行。**比べる相手として順位表に載り、順位も付きますが、束（内側）を持たないので --top には拾われません。★監査 CP48 の直しの後は、上位の枠（keep）を使わず、落ちた候補にも数えず、行に 比べる相手＝真 が付きます（M2-F-9 の数えでは外す）。",
      "9. **ほかの道具の文（この工事では直さない・1変更）。**.claude/tools/gen_stage0_timing.py の59行目は、読み方を regime_r9_diag.py:230 と同じ（WARM）と書くが、この工事の後の道具は stage_warm で読む＝段0 の時間の実測と余白が違う。.claude/tools/gen_s22_fidelity.py の15行目は、regime_r9_diag の --build と同じやり方と書くが、この工事の後の --build は sample_regime_build だけで組み、あちらは sample_structure と乱数のまま。2つとも next_step §6 に積む。"
~~~
根拠の抜き書き: .claude/tools/gen_stage0_timing.py:59「★読み方は `regime_r9_diag.py`:230 と同じにする」
状態: 確定

#### 修正 70
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 71
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 347行（実装の指示 7 の種類）
直す前の文字:
~~~
"種類": "足す文字", "中身": "# ══ 段ごとに測る口
~~~
直した後の文字:
~~~
"種類": "直した後の文字", "中身": "# ══ 段ごとに測る口
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:355「return cur.replace(before, before + body, 1), ("足した" + (f"（案{a}）" if a else ""))」
状態: 確定

#### 修正 72
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 73
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 355行（実装の指示 15 の中身・--build の束を組む行）
直す前の文字:
~~~
                bd, drw = g.sample_regime_build(lm, pool, tfs, table, order_n=i)\n
~~~
直した後の文字:
~~~
                bd, drw = g.sample_regime_build(lm, pool, tfs, table, order_n=i)\n                # ★直す前の validate_drawn と同じく、法則（G7）に反する束は測らない（監査 CP48）\n                ex._check_scene_rules({\"name\": \"range\", \"build\": g.strip_marks(bd)}, \"\")\n
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py:329「g.validate_drawn(r, limits=lim)          # ★69回目＝印を外してから検査に通す（原因A の直し・番人 T31）」
状態: 確定

#### 修正 74
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定

#### 修正 75
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 203行（4-15 競合）
直す前の文字:
~~~
      "**奪い合いに気をつけるもの。**順位表と落ちた候補は日時つきの新しいファイルに書くので、並走しても上書きしません。tuner_stats の記録（cumulative）は record_run の中の既存の書き方に従います（この設計では触りません）。"
~~~
直した後の文字:
~~~
      "**奪い合いに気をつけるもの。**順位表と落ちた候補は日時つきの新しいファイルに書くので、並走しても上書きしません。tuner_stats の記録（cumulative）は record_run の中の既存の書き方に従います（この設計では触りません）。★監査 CP48＝tuner_stats.add_cumulative は読んでから書き直す形で鍵を持たない（tuner_stats.py の175〜192行）＝段の走行を2つ同時に終えると、片方の本数が消える。だから段の走行（--stage・--sweep）は並べて走らせない。"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/tuner_stats.py:188「CUMULATIVE.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n",」
状態: 確定

#### 修正 76
対象のファイル: .claude/state/acceptance.md
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
python3 .claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: .claude/state/session_worklog_20260927.md:502「- まこさんの2回目の cp（sha256 7467f1f5…＝控えと一致）→ `gen_acceptance.py --write` ✅（設計書 1673行・囲み12個・法則の照合 51件／51行）。」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 77
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/acceptance_checklist.md
直す箇所: 42行
直す前の文字:
~~~
- ☐ 【群1】 **直すファイルの行番号を指している文書**を `git grep -n -E 'engine_tuner_(exec|gen)\.py:[0-9]+'` で出し、影響範囲（4-13）に並べる（監査 CP47＝法則ファイルの R7 と engine_tuner_milestones2.md の2行が、実装で行が下がって外れた）
~~~
足す文字:
~~~

- ☐ 【群1】 **直すファイルの名前そのもので壊すプログラムを grep する**（`grep -l '<直すファイルの名前>' .claude/breaks/*.sh`）。当たった壊すプログラムの①探す行 ②走らせるコマンドの旗 の両方が、直した後も通るかを 4-13 に書く（監査 CP48＝行の文字だけを探したので、--no-trades を消す直しで b97 が壊れるのを見落とした）
~~~
根拠の抜き書き: .claude/state/acceptance.md:238「| コードを直したら、その行を探す壊すプログラムを grep | L-605 | なぜ作るかの表の後に grep（当たった壊すプログラムが探す行は消さない＝4-13 の7） |」
状態: 確定

#### 修正 78
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/acceptance_checklist.md
直す箇所: 43行（行の頭）
直す前の文字:
~~~
- ☐ 【群1】 **★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）**
~~~
直した後の文字:
~~~
- ☐ 【群1】 **実装の指示で新しく足す関数（def）を全部 数え、DESIGN_CONTRACT の impl_functions に全部 在るかと、must_use の名前が直した後の関数の中に在るか（包みの関数を呼ぶなら包みの名前）を照らす**（監査 CP48＝_nanmean・_stage_recipe・_record が impl_functions に無く、must_use の record_run が main・run_stage・run_sweep の中に無かった）
- ☐ 【群1】 **★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）**
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/verify_design_contract.py:1056「ng.append(f"A {rel}: 設計書に書いていない関数を触った → {extra}")」
状態: 確定

#### 修正 79
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/acceptance_checklist.md
直す箇所: 43行（行の頭）
直す前の文字:
~~~
- ☐ 【群1】 **★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）**
~~~
直した後の文字:
~~~
- ☐ 【群1】 **新しく足すコマンドの旗・口は、完成の条件のどれか（自己テストの合成データの走行を含む）で1回は通る形にする**（監査 CP48＝完成の条件6行が --stage・--top・--sweep・--build・--nan-check を1度も通らず、入口の木の無い束で解決表が KeyError になる所を測れなかった）
- ☐ 【群1】 **★疑似シミュ由来の固定値ゼロ宣言（必須・require_acceptance hook が物理強制・まこさん承認 2026-06-26）**
~~~
根拠の抜き書き: .claude/state/acceptance.md:1531「| 5 | 自己テストが全部 通る（①〜⑩・実データの試行ゼロ） |」
状態: 確定


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**開いたもの（Read tool か sed／grep で行を指して開いた）**

1. 依頼書：全文 1〜460
2. .claude/state/acceptance.md：全文 1〜1674
3. acceptance_src.json：1〜308 を Read、309〜363 を awk、344・347・349・318・320・352・361〜363・308 の生の行を sed
4. regime_r9_diag.py：全文 1〜354
5. engine_tuner_milestones2.md：725〜784、1992〜2231
6. observe_diag.py：5800〜5851
7. tuner_stats.py：1〜240
8. engine_tuner_gen.py：540〜655、940〜1019、2540〜2590、2800〜3050、3135〜3170、3148〜3400、3668〜3682、3722〜3891、7005〜7098
9. engine_tuner_exec.py：296〜307、328〜377、436〜480、2032〜2143、2140〜2340、1486〜1560、3197〜3221
10. engine_tuner.py：77・83・88・99・132〜155
11. search_limits.json：10・17・42・50〜53
12. r9_demand_fixture.json：全文
13. b104・lib.sh：全文
14. b84・b97：全文
15. apply_audit_fix.py：1〜560
16. gen_audit_docs.py：685〜745
17. _template.md：229〜290
18. cat_requirements.md：§4.6 の H2・H6・H13・H16（545〜712）
19. engine_tuner_requirements.md：40〜59
20. session_worklog_20260927.md：300〜524
21. verify_design_contract.py：376〜505、861〜1133、1180〜1250、1765〜1824
22. require_design_contract_before_run.sh：1〜60、230〜410
23. enforce_h2_pass.py：1〜120
24. regime_laws.json：395〜422、760〜789
25. permanent_rules.md：381〜392
26. run_breaks.py：1〜60、99〜138
27. tuner_adapters/e38.py：296〜321
28. m2_todo.json：1205〜1235、1975〜1990
29. h2_pass.json：files の一覧
30. gen_s22_fidelity.py・gen_stage0_timing.py：grep と 52〜66
31. cp48_work/cp48_result.md：全文
32. cp48_work/real_hashes_before.txt：全文

**走らせたコマンド**（どれも読むだけ・写しは無し・秒数は測っていない＝すぐに返ったもの）

- 事実データの grep：捉えた 0／順位 1／write_text 0／default_rng 324行／record_run 0
- `git diff HEAD -- regime_r9_diag.py | grep -c '^@@'`＝0
- 実装の指示の直す前の文字15件：`grep -c -x -F` で全部1件。短いもの8件：`grep -o -F | wc -l`（直す前は1、壊すプログラムが探す文字は当てる前0）
- 修正の指示の直す前の文字：生の元データに `grep -o -F`／`grep -n -x -F` で全部1件（修正 15・19 の長い文字も1件）
- `python3 -B scripts/priority_rebuild/verify_design_contract.py --diff /…/.claude/state/acceptance.md`＝rc 0・「齟齬: 0件」
- `shasum -a 256`（帳簿2つ・依頼書・設計書・元データ・直す相手）
- `ls` で書き先 regime_r9 が無いのを確認
- `git status --short`

**外部検索**：WebSearch 3本・WebFetch 5本（§5）。arXiv の PDF を開くのは、道具の制約で本文が取れず、HTML 版で逐語を取った。

**hook に止められたコマンド（外していない・合言葉も付けていない）**

1. `python3 -B -c "…acceptance_src.json を読んで要約…"` → require_design_contract_before_run.sh「走らせる .py を確定できないコマンドです（2026-09-03・監査 cp14 の B-4）」
2. `perl -e 'print …' && grep -c -F …` → require_acceptance_before_impl.sh「書き込み先を確定できないコマンドです（2026-09-02・監査 cp13 の A-6）」
3. `ls .claude/breaks | sort -V | tail -6; cat b104 lib.sh` → 土台ゲート（sort が読むだけの語に無い）
4. `grep -l regime_r9_diag .claude/breaks/*.sh …; echo "rc=$?"; grep … | cut …` → 土台ゲート
5. `grep -n regime_r9_diag .claude/hooks/… .claude/tools/… | cut -c1-260` → 土台ゲート（cut）
6. `date +%s.%N; python3 -B .claude/tools/gen_acceptance.py --verify; echo …` → 土台ゲート（.claude/tools の .py を python で走らせる形）
7. `for spec in …; do sed …; done`（.claude/hooks・breaks・tools を含む） → 土台ゲート

**走らせられなかったものと理由**

- 写しの組み立て（setup_mirror・manifest）
- 直す前の写しの固定のレシピ
- 21件を写しに当てる／apply --design --dry（承認の印が無く、当てる前に止まる）
- py_compile
- --selftest
- 固定のレシピの --purpose check
- b113〜b116（写しに向けた ROOT）
- --stage・--top・--sweep・--nan-check の小さな1回

理由＝このサブエージェントは読み取り専用で、ファイルを作ることが一切できない（cp48_work の下も一時置き場も）。python・perl の場当たりの実行も hook が止める。gen_acceptance --write・承認のプログラム・本物の壊すプログラムは、依頼どおり走らせていない。**走らせて測るべき所（A0-a の実際の rc、A3-a の数字の差、A4-a の実際の落ち方）はデータ不足として残る。** auditor セッションが cp48_work で写しを作って確かめるなら、次の順を勧める。
1. 21件＋修正 1〜76 を当てる前の写しで selftest を走らせる。
2. 当てた後に `--stage stage1 --limit 2 --purpose check`（修正 43〜46 の後）を走らせ、修正 1 の前は KeyError・後は rc=0 になるのを見る。
3. 固定のレシピの①③を M2-F-1 と並べる。

### auditor セッション（監査役を起動した CC）がしたこと

監査の中身（所見・修正の指示・外部検索・自己申告への答え・総合判定）は、監査役（Plan agent）が書いたものを1文字も変えずに載せた。auditor セッションがしたのは、次のことだけ。

| # | したこと | 結果 |
|---|---|---|
| 1 | 依頼書を Read tool で全文 開き、`wc -l` で行数を数えた | 459 行（Read tool の表示は 460 行目まで） |
| 2 | `shasum -a 256 .claude/state/acceptance.md`（監査役を起動する前） | 8554e86b…＝依頼書の値と一致 |
| 3 | ToDo を書いて `enforce_todo_declaration.py --check` を通し、チャットに貼って印を作った | 1回目は ToDo の門が止めた（本文がまだ記録に書かれていなかった）。門が全文を画面に出した後の2回目で通った |
| 4 | 結果の骨組みを `gen_audit_docs.py result <依頼書> <cp48_work/cp48_result.md>` で作った | 「✅ 結果の骨組みを作った（節 11・問い 9・事実データ 1・外部検索 1・自己申告 5）」。1回目は先頭に `time` を付けたので hook 10 が止めた。外して2回目で書けた |
| 5 | 起動前の控えを取った | `git status --short`（21:26:54）・`regime_r9_diag.py` の sha256 d0b0678d…・試行の帳簿2つの sha256（cp48_work/real_hashes_before.txt＝abeec264…／70dd5005…） |
| 6 | 監査役を1体、会話の中身を渡さない形で起動した。渡したのは、依頼書のパス・必読16件・問い・外部検索1件・作業場での実走の頼み・返す形だけ | 終わりの通知の数字＝トークン 839,478・道具の呼び出し 150 回・3,355 秒（約56分）。監査役は「読み取り専用の決まりで、cp48_work の下にもファイルを作れない」と返し、写しでの実走は0件だった |
| 7 | 監査役の返事の全文を作業場に写した（agent_reply.txt）。先頭の道具の注意書き1行を外したものを、所見の控えとして残した（1回目の返事＝plan_findings_1st.md） | 注意書きは「settings-json に似た文が在る」というもので、当たったのは 11 節の git status に並ぶ settings.json の控えのファイル名だけだった（指示の文ではない） |
| 8 | 下書き cp48_final.md を `merge_result.py` で作った。骨組みの題・1 節の固定の3行・3 節の小見出し・目印と、監査役の本文の 1 節の2行・2〜10 節を機械でつないだ | 変えたのは2か所＝①3 節の本文の上に骨組みの小見出しを残した ②7 節の「- **問いN ＝ YES**（」の太字の印を外し、骨組みの「- 問いN ＝ YES（」の形にした |
| 9 | 下書きを `gen_audit_docs.py check`（依頼書と結果）と `gen_audit_docs.py form`（形）で照らした | check＝食い違い 0 件（12 項目とも ✅）／form＝形の食い違い 0 件 |
| 10 | 当てる道具の乾いた当て方 `apply_audit_fix.py --report <下書き> --severity Critical,Major,Minor,Process --dry`（本物は書かない） | 1回目＝rc=1。修正 51・78・79 の「直す前の文字」が本物に 0 か所（前の件が足す文字を「直す前の文字」にしていた）＝当てる道具が全件を止める形だった |
| 11 | 10 の3件だけ、同じ監査役に続きとして1回だけ書き直しを頼んだ（新しく起動していない） | 2回目の終わりの通知＝道具の呼び出し 3 回・99 秒（トークンは2回の合計で 849,350）。監査役の返事＝「変えたのは『直す前の文字』の置き場と、それに合わせた欄の種類・直す箇所だけ」「§4 の文の差し替えは要りません」。修正 51 の置き場＝元データの実装の指示の配列の末尾3行／修正 78・79 の置き場＝チェックリストの43行目の頭の文字 |
| 12 | 11 の3件を、1回目の返事の本文に `swap_fixes.py` で差し替えた。足す中身は1回目の各件の囲みから機械で取り出した（手で打ち写していない）。差し替えた本文から下書きを作り直した | `diff` の差は3件の欄（直す箇所・直す前の文字・4つ目の欄の見出しと中身）だけ。1回目の返事は plan_findings_1st.md、差し替えた後は plan_findings.md に残した |
| 13 | 作り直した下書きで、乾いた当て方を重さを変えて3回 走らせた | Critical・Major・Minor・Process＝rc=0・当たる 40 件（修正 1・3・5・…・75・77・78・79）・当てない 39 件（走らせるコマンド 38 件・未決 1 件＝修正 47）・実物と合わない件 0 ／ Critical だけ＝当たる 16 件・当てない 16 件 ／ Critical と Major＝当たる 27 件・当てない 29 件。どれも実物と合わない件は 0 |
| 14 | 所見・修正の指示の中の「ファイル名:行番号」の引用を、書き込みの門（enforce_checked_edit）と同じ正規表現で数えた（cp39 の cite_list.py を写して使った） | 42 か所（17 種のファイル）。差し替えの前と後で同じ一覧 |
| 15 | 14 の引用の全部を、auditor セッションが awk で開いた | 開いた行の中身は、所見に書かれた中身と合っていた（例＝engine_tuner_gen.py の 3787 行が `ex._walk(r["entry"]["connective"])`・b97 の 31 行の旗が `--no-trades`・regime_r9_diag.py の 194 行が「順位」を印字する行） |
| 16 | 結果を書く直前に、本物の状態を取り直した | 試行の帳簿2つ＝abeec264…／70dd5005…（起動前と同じ）・設計書 8554e86b…・直す相手 d0b0678d…・元データ 7467f1f5…（どれも起動前と同じ）・書き先 regime_r9 は SDK の下にも v3-bitget-api-sdk の下にも無い |

**auditor セッションが走らせなかったもの**＝写しの組み立てと、写しでの実走（直す前・実装の指示21件を当てた後の `--selftest`・固定のレシピ・b113〜b116・段の口）。理由＝所見を書くのは監査役で、auditor セッションが走らせた数字を後から足すと、監査役が見ていない根拠が結果に入るため。**走らせて測るべき所（A0-a の実際の rc・A3-a の数字の差・A4-a の実際の落ち方）は、データ不足のまま残る。**

**auditor セッションが hook に止められたコマンド（外していない）**
1. `time python3 .claude/tools/gen_audit_docs.py result …` → hook 10（依頼書のファイル名を含み、読むだけの語でない `time`）
2. `grep … | cut …`（.claude/tools の名前を含む）→ 土台ゲート（`cut`）
3. `python3 merge_result.py … && python3 .claude/tools/gen_audit_docs.py check …` → 土台ゲート（道具の .py と別の python を同じコマンドにした）
4. `for f in <過去の結果ファイル2本>; do grep …; done` → hook 11（結果のファイル名を含み、読むだけの語でない `for`）


## 11. 本物のファイルを書き替えていないこと

`git status --short`（リポジトリの根・2026-09-27 22:32:14・HEAD a6b1216）の出力を、下にそのまま写した。打ったのは auditor セッションで、結果ファイルを書く直前に打った。前の監査の作業場（cp36〜cp47 の `_work` の下）の行だけは `grep -v` で省いた（どれもこのセッションを始める前から在ったもの）。

```
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
?? .claude/hooks/require_chat_draft_before_long_reply.sh
?? .claude/settings.json.bak_20260819
?? .claude/settings.json.bak_20260826
?? .claude/settings.json.bak_20260902_implock
?? .claude/settings.json.bak_20260903_a6
?? .claude/settings.json.bak_m2_2_2b
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/agent_reply.txt
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/agent_reply_v2.txt
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/cite_list.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/cp48_final.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/cp48_result.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/merge_result.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/plan_findings.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/plan_findings_1st.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/real_hashes_before.txt
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/sec10_main.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/sec11.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp48_work/swap_fixes.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

- **git に追跡されているファイルで変わっている（M の）行は、`decisions.md` の1行だけ。**これは監査役も auditor セッションも書いていない。このセッションの開始時に、hook（`show_decisions`）が「まこさんが決めたこと」の一覧を作り直したもの。証拠＝`decisions.md` を書き替えた時刻は 21:22:02（stat で見た）で、監査役を起動する前（21:26:54）の `git status --short` に既に M で出ていた。
- **`??` の行のうち `cp48_work` の下は、この監査の作業場。**全部 auditor セッションが作った（監査役は読み取り専用で、1つも作っていない）＝骨組み `cp48_result.md`・起動前の控え `real_hashes_before.txt`・監査役の返事の写し `agent_reply.txt`・差し替えた本文 `agent_reply_v2.txt`・所見の控え `plan_findings_1st.md`（1回目）と `plan_findings.md`（差し替えた後）・つなぐ道具 `merge_result.py`・差し替える道具 `swap_fixes.py`・引用を数える道具 `cite_list.py`（cp39 の作業場から写した）・`sec10_main.md`・`sec11.md`・下書き `cp48_final.md`。`cp48_work/cp48_src.md` は依頼書の元データで git に登録済み（依頼を出した CC のもの・監査は書いていない）。
- **ほかの `??` の行は、このセッションを始めた時点の git の状態に既に在ったもの。**
- **本物の中身が変わっていないことの証拠（sha256・結果を書く直前に取った）**＝試行の帳簿 `engine_tuner_trials_cumulative.json` abeec264…・`engine_tuner_check_runs.json` 70dd5005…（どちらも起動前の控えと同じ）／設計書 `acceptance.md` 8554e86b…（依頼書の値と同じ）／直す相手 `regime_r9_diag.py` d0b0678d…・元データ `acceptance_src.json` 7467f1f5…（起動前と同じ）。書き先 `results/priority_rebuild/regime_r9/` は作られていない。
- **この出力の後に書いたのは、作業場 `cp48_work` の下の4つ（`sec10_main.md`・`sec11.md`・`cp48_final.md`・`plan_findings.md` の書き直し＝どれも上の一覧に既に在るファイル）と、結果ファイルそのもの（`.claude/audits/2026-09-27_m2f2_catch_rank_stages_design_cp48_audit_report.md`）だけ。**

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-27_m2f2_catch_rank_stages_design_cp48_audit_request.md request_sha256=1480840b468e744ccc1f5a42219d96d024c8dafdbb9b3636cdea5b63a3f2e96e -->
