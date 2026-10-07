# 監査結果 cp66 — CP66 — G2 の番人が、指標の材料を持つ構造を選ぶ形に直す。M2-C-15（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_g2_sentinel_material_pick_20261007_impl_cp66_audit_request.md`
- 依頼書のハッシュ値: 6dbc2c94c208a1b235010d407e1ec4f0eeec99b02e93c40400e87ce5acf2e695
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 6cd2c507b64c69c500d683a34f47c6a303ff881bbdf5f175299dc96b8ccf05aa
- 監査が照らしたハッシュ値: 6cd2c507b64c69c500d683a34f47c6a303ff881bbdf5f175299dc96b8ccf05aa（`shasum -a 256 .claude/state/acceptance.md` の出力。承認の控え `SDK/.claude/ratchet/acceptance_archive/g2-sentinel-material-pick-20261007.md` も同じ値で、依頼書の値と一致した）
- 実施日: 2026-10-07

★依頼書の版の書き方について（所見ではなく前提の訂正）：依頼書の Q1・Q2（:196・:202）は「実装の前＝HEAD の commit a6f8167」「実装の後＝まだ commit していない作業中の変更（`git diff HEAD`）」と書いている。監査の時点の実物は、HEAD＝f38759b で、実装は commit 85b7e1f に入っており、対象2ファイルの `git diff HEAD` は空だった。そこで、この監査は「実装の前＝a6f8167」「実装の後＝85b7e1f（＝HEAD＝作業中のファイル。a6f8167 から HEAD までで gen_signal_families.py を変えた commit は 85b7e1f だけ）」として照らした。この書き方のずれは、9 の修正3 に書いた。


## 2. 監査対象の型宣言

- コード型＝`SDK/scripts/priority_rebuild/gen_signal_families.py`（G2 の番人 _g2_selftest_body）と、壊すプログラム `.claude/breaks/b144_g2_sentinel_first_clean.sh`。
- 文書型＝設計書 `.claude/state/acceptance.md`（4-20 の実装の指示）・承認の控え・やることの表.md・当てた記録 applied_fixes.json。
- 数値型＝該当なし（net・件数などの数値の結果を出す工事ではない）。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

依頼書の表（2件）と実物は合った。
- 1＝`SDK/scripts/priority_rebuild/gen_signal_families.py` の _g2_selftest_body。直す前の文字（`base_st = copy.deepcopy(clean[0])` と空行）は a6f8167 の版に1か所だけ在り、実装の後には0か所。直した後の文字（with_col の絞り込み・止める文・`base_st = copy.deepcopy(with_col[0])`）は実装の後に1か所在る（いまの行は 1004〜1010）。
- 2＝`.claude/breaks/b144_g2_sentinel_first_clean.sh`（新しいファイル）。a6f8167 には無い（`git cat-file -e a6f8167:<パス>` が rc=128）。

### 当てた記録（applied_fixes.json の名前 design:g2-sentinel-material-pick-20261007）

依頼書の表（2件）と実物は合った。applied の配列の412番目（ファイルの2882行）＝番号1・gen_signal_families.py・当てた・2026-10-07T16:09:37。413番目（2889行）＝番号2・b144_g2_sentinel_first_clean.sh・当てた・2026-10-07T16:09:37。「もう当て終わっていた」の件は無い。

### 必読に要るファイル（道具が設計書と実装から拾った）

依頼書の表の6件（cat_requirements.md・engine_tuner_requirements.md・engine_tuner_milestones.md・engine_tuner_milestones2.md・gen_signal_families.py・b144）は、どれも実在し、必読の15件に入っていた。抜けは無い。ただし、Q8 の答えには必読の外の `SDK/scripts/priority_rebuild/engine_tuner_exec.py`（:188 indicator_enabled・:200 geo_enabled・:660〜705 の印の検査）と `SDK/.claude/ratchet/indicator_switch.json`（:169 "off"・:244 "ADXR"・:287〜290 geo_on）が要った（10 に書いた）。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

PASS。重さ＝なし。
- 当て方は当てる道具と同じ形にした（囲みの切り出し＝gen_audit_docs.py:1839-1843、置き換え＝apply_audit_fix.py:680「`cur.replace(before, body, 1)`」、新しいファイル＝:916「`.rstrip("\n") + "\n"`」）。
- 実装1 を a6f8167 の blob（fc86cf9）に当てた結果は、実装の後の blob（f006d08）と1文字も同じだった（86067 バイト同士・IDENTICAL）。直す前の文字は前に1か所・後に0か所、直した後の文字は後に1か所。
- 実装2 の全文は、HEAD の b144 と1文字も同じだった（3193 バイト同士）。
- 監査役（このセッション）も `git diff a6f8167 HEAD -- gen_signal_families.py` を開き、塊が1つ（@@ -992,8 +992,14 @@）で、消えた2行と足された8行が実装の指示の直す前・直した後と同じであることを目で確かめた。
- 進め方の欠陥（Process）：依頼書の Q1・Q2 の版の書き方（:196・:202「実装の後＝作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる）」）は、依頼書を作った後に commit 85b7e1f と f38759b までが積まれたため、監査の時点では成り立たなかった（対象2ファイルの `git diff HEAD` は空）。依頼書のとおりに照らすと「実装が無い」に見える。依頼書を作る道具（gen_audit_docs.py:1107-1109）が、HEAD という動く名前で版を書いているのが元。

修正の番号＝3

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

PASS（無い）。重さ＝なし。
- gen_signal_families.py の差分は上の1塊だけで、全部が実装1 に当たる（Q1 で IDENTICAL）。
- b144 は新しいファイル1本で、中身は実装2 と同じ。
- 依頼書の自己申告1 の、この工事の外のファイルは、Q1・Q2 の差分（対象2ファイル）には混ざっていない（6 に書いた）。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

PASS。重さ＝なし。
- 当てた記録2件（applied の412番目と413番目）が、実装の指示の番号1・2 と、番号と対象のファイルで1件ずつ合う（3 に書いた）。
- 抜けは無く、「もう当て終わっていた」の件も無い。

修正の番号＝なし

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

PASS（YES）。重さ＝なし。
- 要望1 は、gen_signal_families.py:1007「`with_col = [st for st in clean if _first_col_cond(st) is not None]`」と :1010「`base_st = copy.deepcopy(with_col[0])`」で満たす。表に沿った構造（clean）のうち、指標の材料を持つ最初の構造を元に使う形そのもの。
- 1本も無いときは :1009「[番人エラー] 表に沿っていて指標の材料を持つ構造が1本も作れない＝既知答えが作れない」で止まる。
- RCI5 を足した後の材料の一覧（部品 477）で G2 が通っていることは、Q6 の記録で確かめた。
- 30本の中に1本も無いときに止まる限界は、設計書 6-2 の1 に書いてあり、まこさんが OK した範囲。

修正の番号＝なし

### Q8 — 元の構造を選び直しても、既知答え11件はどれも狙った分岐を試しているか（優先度 A）

FAIL（一部）。重さ＝Major。★この工事が作ったものではなく、工事の前（a6f8167）から同じ。走らせてはいない（理由は 10）。コードと実物の設定を追って決めた。

選び直しは、元の6件の弾かれ方を変えていない。
- 差し替える材料は元の構造から独立している。禁止3 の部品は gen_signal_families.py:989「`bp, btf = next(iter(sorted(banned)))`」で決まる。偽の指標と res_hi は文字の決め打ち（:1029・:1037）。
- 足した4件（:1110〜1118）と材料を読めることの1件は、指標の材料を持つ元の構造なら狙いの文で弾かれる。with_col がそれを保証する。

元の6件のうち2件は、狙った分岐に届いていない。
- 禁止3 の見本：sorted(banned) の1つ目は ADXR21／1d（`.claude/ratchet/signal_families.json` の bans.insufficient_samples.pairs 366組を並べた1つ目・監査役が perl で確かめた）。ADXR は印で「使わない」（indicator_switch.json:244「  "ADXR",」は :169 から始まる "off" の中）。そのため collect_materials（gen_signal_families.py:641-644）が呼ぶ実行器の _material_name が、engine_tuner_exec.py:703「`if not indicator_enabled(fam):`」で拒否し、違反は :769「材料が読めない（…）」になる。禁止3 の分岐 :777-778「`{base}__{tf} は標本不足の禁止（禁止3）`」には届かない。
- res_hi の見本（H6）：印の geo_on は「W%」「帯内位置%」の2つだけ（indicator_switch.json:287-290）。res_hi は engine_tuner_exec.py:663「`if not geo_enabled(g):`」で拒否され、「材料が読めない」になる。H6 の分岐 :785「レンジ幾何 {name} は条件の材料に使えない（…H6）」には届かない。
- 偽の指標の見本は「材料が読めない」で弾かれ、これは :1062-1064 のコメントの狙いどおり。

影響：元の6件は通るか弾かれるかだけを見ている（:1053-1058）。そのため G2 は「11件 全部 期待どおり」と出すが、判定の禁止3 の分岐（:777-778）と H6 の分岐（:785）は、既知答えで1度も試されていない。設計書（4-0「既知答えの中身は変えません」・やることの表の Y-2）とは食い違っていないので、問い1 は NO にしない。

修正の番号＝1・2

### Q9 — 選び方は決まった並びで、乱数を足していないか。止まり方は正しいか（優先度 A）

PASS。重さ＝なし。
- 直した所（:1007-1010）は、clean を作った順に前から見る絞り込みだけで、rng を呼んでいない。
- 乱数は前からの _real_structures（:849「`rng = np.random.default_rng(seed)`」・種 20260807・30本）だけで、この工事は触っていない（Q2）。恒久67番に照らすと「残っている乱数」に当たるが、入口の乱数を外すのは M3（engine_tuner_milestones.md:147）で、この工事の範囲の外（やることの表 Y-1・依頼書 :176）。そのため「乱数を足す形」には当たらず、Critical にしない。
- with_col が空なら :1009 の SystemExit で止まる。g2_selftest の中で抜けるので、印を書く :965 には届かない（印は書かれない）。既知答えを減らして通る道は無い。件数は `len(cases) + len(extra) + 1`（:1146）で数えている。
- 付記：:1013-1015「差し替えられる材料が構造に無い」は、直した後は通らない行になった（with_col が材料を持つことを保証するため）。b144 はこの行の文を当てにしている（Q10）。

修正の番号＝なし

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

PASS。重さ＝なし。
- 承認の控えと、いまの acceptance.md は `diff` で完全に同じ。sha256 は両方 6cd2c507b64c69c500d683a34f47c6a303ff881bbdf5f175299dc96b8ccf05aa（監査役も shasum で確かめた）。
- 承認の印（`.claude/state/acceptance.approved`・design_approved.json）も同じ値。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

PASS。重さ＝なし。
- F-1（やることの表.md:12「…指標の材料を持つ最初の構造を既知答えの元に使う。…1本も無ければ、それを言って止まる」）は実装1（gen_signal_families.py:1007-1010）に当たる。
- G-1（:13「G2 → H2 を取り直す…チェックを走らせ直す」）は手順の項目で、実装の指示ではない。記録で済んでいる（g2_pass.json 16:18・h2_pass.json 16:23・pre_audit_check.json の at 2026-10-07 16:27:26 で全部の行が rc=0）。
- 実装2（b144）は、まこさんが OK した【7-6】（設計書 6-1・7-6 の行1）と 4-3「新設」から来ている。要件の外の変更ではない。
- Y-2（既知答えの中身を変えない）は守られている（差分は選び方の所だけ）。

修正の番号＝なし

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

PASS（記録で確認。走らせてはいない）。重さ＝なし。
- 走らせなかった理由：`--verify` は verify()（:1368）から g2_selftest()（:560）を呼び、通ると `G2_PASS_PATH.write_text(`（:942）で検査済みの記録を本物に書く。途中の core_selftest は本物の signal_families_approved.txt を一時的に書き替える（:1211・:1215 で戻す）。本物を書き替えない形が無いので、走らせていない（依頼書の禁止）。
- 代わりの根拠①：検査済みの記録（g2_pass.json）の指紋を、g2_fingerprint と同じ式で、印の対象39ファイルについて計算し直した（perl・0.149秒）。stamp と今の値が一致した（2544c926…・無いファイル0件）。対象には gen_signal_families.py・engine_tuner_gen.py・signal_families.json が入る。記録は番人が全部 通ったときだけ書かれ（:963-965）、記録の時刻 16:18:07 は当てた時刻 16:09:37 の後。つまり、いまのコードで G2 は通っている。
- 代わりの根拠②：pre_audit_check.json（16:27:26）に `"cmd": "gen_signal_families.py --verify", ... "rc": 0` が在る。
- 限界：記録を手で偽造されたら見抜けない（b66.sh:16 の限界①と同じ）。

修正の番号＝なし

### Q10 — 壊すプログラム b144 は、直しを外したときだけ落ちるか。前からの壊すプログラムに影響は無いか（優先度 B）

PASS（コードと記録で確認。走らせてはいない）。重さ＝なし。
- b144 の直す前の文字は実装1 の直した後の文字と同じで、b144 の直した後の文字は実装1 の直す前の文字と同じ（perl で SAME／SAME）。
- 直す前の文字は、いまのファイルに1か所だけ在る。b144.sh:22-23 は1か所でなければ止める。
- b144 で壊した後のファイルは、a6f8167 の版と1文字も同じ。つまり壊した形＝直す前のコード。直す前のコードで G2 が落ちたことは、pre_audit_run_20261007_1.log:17「NG gen_signal_families.py --verify  rc=1（45.5秒）」に在る（落ちた文「差し替えられる材料が構造に無い」は worklog §15 に在り、ログの :1-20 には文そのものは出ていない）。
- 当てた後に b144 が rc=1 で落ちたことは worklog §16 にだけ書かれていて、走らせた結果の記録ファイルは見つからなかった（データ不足・理由＝記録が無い）。
- b66：壊す相手は enforce_g2_pass.py で、gen_signal_families.py の文字は探していない。探す文字（enforce_g2_pass.py:167-169）は今も在る。a6f8167 から HEAD までで b66・lib.sh・enforce_g2_pass.py の差分は0。gen_signal_families.py を名指しする壊すプログラムは b144 だけ。
- CC の自己申告（材料の一覧が変わると b144 が落ちなくなる限界）：補わなくてよい。落ちなくなったときは run_breaks.py:850-855 が「❌ 期待と違う」を出して match を偽にする（黙らない）。その時点では直しを戻しても働きは同じなので、隠れた壊れは生まれない。設計書 6-2 の2 のとおり、そのときに作り直せば足りる。
- CC の自己申告（2つ目＝案の先頭の【】の行）：結果に効かない。
- CC の自己申告（3つ目＝r6_build.py）：やることの表.md:25「道具（r6_build.py）が写しで番人を走らせ、通ることと、直しを戻すと落ちることを確かめてから当てます」は、そのとおりには行われていない（r6_build.py は消され、r6b_build.py は engine の部品を読み込まない・worklog §16）。当てる前に写しで番人を走らせたかはデータ不足（理由＝承認の前の検査 --try が G2 を含んだかの記録が無い）。当てた後の G2 は通っているので、件数には数えない。

修正の番号＝なし


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

- 申告された11ファイルは、監査の時点では全部 commit 済み（追跡中のファイルの未 commit の変更は0件。`git status --short` の「??」以外が0行）。
- Q1・Q2 の差分には混ざっていない。a6f8167 から HEAD までで gen_signal_families.py を変えたのは 85b7e1f の1塊だけで、実装1 と1文字も同じ。b144 は実装2 の全文と同じ。
- ただし G2 の判定の結果には効いている。85b7e1f は3つの工事をまとめた commit で、engine_tuner_gen.py の変更（:463-470「`if not param_in_range(family, m["param"], ranges)[0]: return False`」・監査 CP63 の修正1）を含む。engine_tuner_gen.py は検査済みの記録の指紋の対象で、番人が構造を作る経路にも入る。承認のときに未 commit だったファイルは g2-sentinel-material-pick-20261007.dirty.json に在る（engine_tuner_gen.py を含む5本）。Q6 の G2 の結果は、この変更を含んだ状態で通ったもの。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝Q1〜Q4 は実物で照らして合った。実装1 を前の版に当てた結果が後の版と1文字も同じ・指示の外の行0・当てた記録2件が1件ずつ合う・承認の控えといまの設計書が同じ。Q5 は合う。Q6 は記録で通る。Q9・Q10 は PASS。Q8 の所見は工事の前から在るもので、設計書と実装の食い違いではない）
- 問い2 ＝ YES（根拠＝要望1 は gen_signal_families.py:1007-1010 で満たす。RCI5 を足した後の材料の一覧で G2 は通っている）

### 結論と件数

- 結論＝GO
- Critical＝0
- Major＝2（所見は Q8 の1件・修正1・2）
- Minor＝0
- Process＝1（修正3）


## 8. 修正の指示

### Critical

なし

### Major

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py
直す箇所: 989〜989
直す前の文字:
~~~
    bp, btf = next(iter(sorted(banned)))
~~~
直した後の文字:
~~~
    # ★（監査 CP66 の修正1）＝禁止3 の見本の部品は、印が「使う」で、数字が1つで、範囲の中のものから、並べた順の最初を使う。
    #   直す前は sorted(banned) の1つ目（ADXR21__1d）を使った。ADXR は印で「使わない」なので、見本は実行器の印の検査で
    #   「材料が読めない」になり、_judge_structure の禁止3 の分岐に1度も届いていなかった（乱数は使わない）。
    import engine_tuner_exec as _ex_ban                      # 印の判定は実行器の1つの関数だけ（書き写さない）
    import engine_tuner_gen as _gen_ban
    _ban_ok = []
    for _bp, _btf in sorted(banned):
        _rb, _pb = iref.find(_bp)
        if _rb is None or len(_pb) != 1 or not _ex_ban.indicator_enabled(_rb["family"]):
            continue
        if not _gen_ban.param_in_range(_rb["family"], _pb[0])[0]:
            continue
        _ban_ok.append((_bp, _btf))
    if not _ban_ok:
        raise SystemExit("[番人エラー] 印が「使う」で数字が1つで範囲の中の、禁止3 の組が無い＝禁止3 の既知答えが作れない")
    bp, btf = _ban_ok[0]
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json:244「  "ADXR",」
状態: 未決

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py
直す箇所: 1118〜1119
直す前の文字:
~~~
        (dict(st=_empty_st), "材料を1つも持たない構造", "材料が1つも見つからない"),
    ]
~~~
直した後の文字:
~~~
        (dict(st=_empty_st), "材料を1つも持たない構造", "材料が1つも見つからない"),
        # ★（監査 CP66 の修正2）＝前の6件の禁止3 とレンジ幾何（H6）は弾かれるかだけを見ていて、実際は印の検査
        #   （「材料が読めない」）で弾かれ、_judge_structure の2つの分岐に届いていなかった。出た違反の文まで照らす。
        (dict(st=copy.deepcopy(ban_st)), f"禁止3 の組（{bp}__{btf}）を、禁止3 の文で弾く",
         "は標本不足の禁止（禁止3）"),
        (dict(st=copy.deepcopy(geo_st), geo_ok=set()),
         "レンジ幾何の 帯内位置% を、許可を空にした写しで判定（H6 の分岐）",
         "レンジ幾何 帯内位置% は条件の材料に使えない"),
    ]
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_signal_families.py:785「                ng.append(f"レンジ幾何 {name} は条件の材料に使えない（表の許可は ratio の {sorted(geo_ok)} だけ・H6）")」
状態: 未決

### Minor

なし


## 9. CC プロセス欠陥対策

### Process

#### 修正 3
対象のファイル: .claude/tools/gen_audit_docs.py
直す箇所: 1107〜1109
直す前の文字:
~~~
        pre_desc = (f"HEAD の commit {head or '（読めない）'}（承認の控えをまだ commit していないので、実装の前は HEAD の版。"
                    f"`git show HEAD:<パス>` で出せる）")
        post_desc = "作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる）"
~~~
直した後の文字:
~~~
        pre_desc = (f"commit {head or '（読めない）'}（依頼書を作った時点の HEAD。承認の控えをまだ commit していないので、実装の前はこの commit の版。"
                    f"`git show {head or 'HEAD'}:<パス>` で出せる。★この後に commit しても、この番号で出せる）")
        post_desc = (f"依頼書を作った時点の作業中の変更（まだ commit していない。`git diff {head or 'HEAD'} -- <パス>` で見られる。"
                     "★この後に commit したときは `git log --oneline -- <パス>` でその commit を探し、"
                     f"`git diff {head or 'HEAD'} <その commit> -- <パス>` で見る）")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_g2_sentinel_material_pick_20261007_impl_cp66_audit_request.md:196「実装の前（HEAD の commit a6f8167（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））の対象のファイル（`.claude/breaks/b144_g2_sentinel_first_clean.sh`・`SDK/scripts/priority_rebuild/gen_signal_families.py`）に、設計書 4-20 の実装の指示（2 件）を番号の順に当てた結果が、実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。」
状態: 未決


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

監査は Plan サブエージェント（cold start・依頼書と必読と問いだけを渡した）が行い、監査役（このセッション）が修正の根拠の行を実物で開き直して確かめた。

開いたファイル（必読15件は全部）
1. `.claude/state/acceptance.md`（全730行）
2. 承認の控え g2-sentinel-material-pick-20261007.md（acceptance.md と diff で同じ・shasum も同じ）
3. `SDK/.claude/audits/applied_fixes.json`（:2882・:2889）
4. `やることの表.md`（全91行）
5. `SDK/.claude/rules/cat_requirements.md`（:159-268・:529-752）
6. `SDK/.claude/ratchet/engine_tuner_requirements.md`（:28-103）
7. `SDK/.claude/ratchet/engine_tuner_milestones.md`（:95-150・:182-186）
8. `SDK/.claude/ratchet/engine_tuner_milestones2.md`（:3-46・:1173-1183）
9. 承認の控え（2 と同じ・全文を diff で照らした）
10. `SDK/scripts/priority_rebuild/gen_signal_families.py`（:510-575・:597-1225・:1340-1385）。監査役も :630-650・:755-790・:980-1060・:1110-1125・:1140-1150 を開いた
11. `SDK/scripts/priority_rebuild/engine_tuner_gen.py`（:192-231・:3439-3480）
12. `.claude/breaks/b144_g2_sentinel_first_clean.sh`（全28行）
13. `.claude/breaks/b66_g2_fingerprint_loose.sh`（全42行）
14. `.claude/state/indicator_review/pre_audit_run_20261007_1.log`（:1-33）
15. `.claude/state/session_worklog_20261007.md`（:140-175）

必読の外で開いたもの
- `SDK/scripts/priority_rebuild/engine_tuner_exec.py`（:170-230・:268-310・:560-760。監査役も :660-666・:700-706 を開いた）
- `SDK/scripts/priority_rebuild/indicator_reference_diag.py`（:961-985・:2930-2935・:4308-4309）
- `SDK/.claude/ratchet/indicator_switch.json`（監査役が :240-246・:286-291 を開き、:22 "on"・:169 "off"・:287 "geo_on" の位置を grep で確かめた）
- `SDK/.claude/ratchet/signal_families.json`（禁止3・extra_parts）
- `.claude/breaks/lib.sh`（全101行）・`.claude/hooks/enforce_g2_pass.py`（:165-170）
- `.claude/tools/run_breaks.py`（:478-530・:845-855）・`.claude/tools/apply_audit_fix.py`（:175-214・:470-500）
- `.claude/tools/gen_audit_docs.py`（:1070-1144・:1816-1850。監査役も :1105-1110 を開いた）
- `.claude/hooks/require_design_contract_before_run.sh`（:100-299）・`.claude/rules/permanent_rules.md`（:379）
- g2_pass.json・pre_audit_check.json・承認の控えの breaks.json と dirty.json

走らせたコマンド（どれも読むだけ・1秒未満）
- `git log`・`git diff a6f8167 HEAD`・`git diff HEAD --stat`・`git status`・`git rev-parse`・`git cat-file -e` → 実装は 85b7e1f、対象2ファイルの未 commit の変更は0、b144 は a6f8167 に無い（rc=128）。
- `shasum -a 256`（acceptance.md と承認の控え）→ 両方 6cd2c507…。
- perl（検査済みの記録の指紋の計算し直し）→ 一致・0.149秒。
- perl ＋ `git cat-file --batch`（Q1 のメモリの中の当て直し・b144 の巻き戻し）→ IDENTICAL×2・SAME×2・1か所・巻き戻した結果が前の版と IDENTICAL・0.025秒。
- perl（禁止3 の最初の組）→ 366組の1つ目が ADXR21／1d（監査役も走らせて同じ結果）。印が「使う」の候補は 59組。
- grep（印・b66 の相手・壊すプログラムの参照）。

走らせられなかったものと理由
- `python3 scripts/priority_rebuild/gen_signal_families.py --verify` と `--g2-selftest`：検査済みの記録 g2_pass.json を本物に書き（:942）、signal_families_approved.txt を一時的に書き替える（:1211・:1215）ため。
- b144：本物の gen_signal_families.py を書き替えてから `--verify` を走らせる（b144.sh:24・lib.sh:61-73）ため。
- 写しで走らせること：Plan サブエージェントは読むだけの役目で、`python3 -c` と `python3 -` は hook（require_design_contract_before_run.sh:186-225）が止めた。走らせるなら、`git clone` で作った写しの中の SDK のフォルダから走らせる（REPO_ROOT＝SDK.parents[1]・:867 なので、記録は写しの `.claude/state` に書かれる）。
- hook が止めたコマンド（実行されていない）：`python3 -c`（設計↔実装ゲート・このとき hook 自身が `.claude/state/design_gate_fires.log` に止めた記録を1行 足した・.gitignore の対象）、perl に scripts/priority_rebuild のパスを渡した形（受け入れ条件ゲート）、`>>` や `<パス>` の文字を含む grep（土台ゲート）。


## 11. 本物のファイルを書き替えていないこと

`git status --short` は全体で178行で、全部「??」（追跡していないファイル）。追跡中のファイルの変更（「??」以外の行）は0行だった。

対象を絞った出力（gen_signal_families.py・b144・b66・applied_fixes.json・g2_pass.json・h2_pass.json・cp66_work）:

```
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp66_work/
```

cp66_work には、この監査が道具で作った結果の骨組み（cp66_result.md）と見直し表と、前から在った cp66_src.gen.md だけが在る。対象のファイルと記録の更新時刻は、どれも監査の前のまま（gen_signal_families.py 16:09・b144 16:09・applied_fixes.json 16:09・g2_pass.json 16:18・h2_pass.json 16:23）。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-07_g2_sentinel_material_pick_20261007_impl_cp66_audit_request.md request_sha256=6dbc2c94c208a1b235010d407e1ec4f0eeec99b02e93c40400e87ce5acf2e695 -->
