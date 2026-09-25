# 監査結果 cp42 — CP42 — 設計書の「実装の指示」をプログラムが実物に当てる道具（`--design` の口）は、承認済みの設計書 impl-instruction-apply-20260924 の決めた動きをしているか。設計書と実装の食い違いを、まとめて直せる形で洗い出す

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-24_impl_instruction_apply_impl_cp42_audit_request.md`
- 依頼書のハッシュ値: 1a02f04f71d5869c5efe2dfb01e5e2bd1484486143132acdbee4040e605b4bf4
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/tools/apply_audit_fix.py` ／ ハッシュ値 9367982a3aac392b8b3c0ccc8deb43f85a3a53c5f25803cee1c097af6bbe01b9
- 監査が照らしたハッシュ値: 9367982a3aac392b8b3c0ccc8deb43f85a3a53c5f25803cee1c097af6bbe01b9（`shasum -a 256 .claude/tools/apply_audit_fix.py` の実測。依頼書の値と一致。監査の開始時と終了時で同じ）。あわせて照らしたもの＝`.claude/tools/gen_acceptance.py` 81523b78fd0228f41bd226991d81009865b43510bfb89a534ef617965655af75／`.claude/state/acceptance.md` 8fcd0a1305d1f0f2bf73ff85597ac30d338b8a539d74a69d2457db045c70f1a6（`.claude/state/acceptance.approved` の中身・`design_approved.json` の値と同じ・ARC iter="impl-instruction-apply-20260924"・672行）／`SDK/.claude/ratchet/acceptance_src.json` 559bd0ec82d9b5d186fec9bd6a2c5796466ca6f896b4b226ba17e35ad745af21／`b101_design_apply_no_approval.sh` a0ece8358388f014472af9b2ea5e5fc3eb8cbd3da6cedebe920775f8b15f937c／`b102_design_apply_no_precheck.sh` 6bb242ac938eb96a3666eaa2bac5a6470c2ea745a4617103a3e143517d60fb99／`lib.sh` 7a590f07202a7dd14c96c8475822b08158b778b5559121f336a998e8a5314757。★写し（`cp42_work/mirror`）が本物と同じかを `diff` で確かめた＝違いは根のパスの1行だけ（apply_audit_fix.py の59行・gen_audit_docs.py の74行・lib.sh の21行）。gen_acceptance.py・b101・b102・acceptance.md・acceptance.approved・acceptance_src.json は sha256 が本物と同じ。★この1行の違いのため、写しの `gen_acceptance.py --verify` は SPEC だけ ❌ になる（SPEC の定数 ROOT が写しの根になる）。判定には本物の `--verify`（rc=0）を使った。
- 実施日: 2026-09-24


## 2. 監査対象の型宣言

**該当は2つ＝コード型・文書型。数値型は非該当。**

- **コード型**＝監査の相手 `.claude/tools/apply_audit_fix.py`（695行）と `.claude/tools/gen_acceptance.py`（1377行）、壊すプログラム `.claude/breaks/b101_design_apply_no_approval.sh`・`.claude/breaks/b102_design_apply_no_precheck.sh`（各28行）と共通の部品 `.claude/breaks/lib.sh`（101行）。写しで走らせ、壊し、見本の設計書を当てて確かめた。
- **文書型**＝承認済みの設計書 `.claude/state/acceptance.md`（672行）と、その元データ `SDK/.claude/ratchet/acceptance_src.json`（318行）。設計書の文と実装を1件ずつ突き合わせた。
- **数値型は非該当**＝この道具は売買を1件も回さず、閾値・期間・点の一覧を1つも作らない（A5 の実測）。月 $1,900 の達成可能性の判定は対象外。


## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの・まこさんが打ったもの）

| # | 依頼を出した CC の主張 | 監査が走らせたコマンド | 監査の結果 | 判定 |
|---|---|---|---|---|
| 1 | `apply_audit_fix.py --selftest`＝1回目 4/12 → 直して 12/12 | 直下から `python3 .claude/tools/apply_audit_fix.py --selftest` | rc=0・0.15秒・「✅ selftest 12/12 pass」 | **12/12 は再現した。**4/12 は直す前のコードが残っていないので走らせられない（データ不足＝その版は commit されていない）。原因の説明（`^##+ ` が `#### 実装 1` を見出しと取り違える）は、いまの正規表現（apply_audit_fix.py:129）と合う |
| 2 | まこさん・SDK の中から＝T6 を直す前 11/12 → 直して 12/12 | SDK の中から `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | **走らなかった。**設計↔実装ゲートが止めた（「[FAIL] C selftest: 設計書が要求する名前が中身に無い → ['read_design_fixes', 'approved_ok']」）。自己テストは作業場所を使わない（見本は ROOT からの絶対パス）ので、直下と写しの 12/12 で中身は同じ | **中身は再現した。SDK の中から CC が打つ形は、いまは打てない**（B3 の Critical） |
| 3 | `gen_acceptance.py --selftest` 9/9（2回） | 直下から `python3 .claude/tools/gen_acceptance.py --selftest` | rc=0・2.74秒・「✅ selftest 9/9 pass」 | **再現した。**★T3 が本物の `acceptance_src.json` を一時的に書き替えて戻す作り（gen_acceptance.py:1251）。走らせた後の sha256 は 559bd0ec… のまま・更新時刻が 22:46:22 に変わった |
| 4 | b101＝rc=1・T4・T11 が「❌ 承認の印」／b102＝rc=1・T7 が「❌ 実物と合わない件」 | 写しで `bash run.sh break b101_design_apply_no_approval`／`… b102_design_apply_no_precheck` | b101＝rc=1・0.30秒・「❌ 承認の印 T4」「❌ 承認の印 T11」・10/12。b102＝rc=1・0.30秒・「❌ 実物と合わない件 T7: 半分だけ当たった／rc=1 code='x = 9\n'」・11/12 | **再現した。**★b102 が測るのは当てる直前の確かめだけ（A0-b） |
| 5 | 承認③＝b101・b102 とも期待どおり（2/2）・#3・#4 が「済」・印 8fcd0a13… | 走らせていない（依頼書の禁止）。記録を開いた | `acceptance.approved` の中身＝8fcd0a13…＝`acceptance.md` の sha256。`impl-instruction-apply-20260924.breaks.json` の行3・4＝match true（note「❌ selftest 10/12 pass」「❌ selftest 11/12 pass」）。設計書 7-6 の #3・#4＝「✅済」（acceptance.md:539） | **記録は主張と一致した** |
| 6 | SDK の中から `verify_design_contract.py --diff <設計書>`＝齟齬 0件 | 同じコマンドを SDK の中から | rc=0・0.13秒・「齟齬: 0件」 | **再現した。**★ただし同じ道具の照合A〜D（`verify_design_contract.py <設計書>`・設計↔実装ゲートが掛けるもの）は rc=1・0.46秒・「RESULT: FAIL（設計と実装が乖離＝採点に進めない）」（B2・B3） |
| 7 | `run_breaks.py --lint-expect`＝rc=1（b88_r2_exempt.sh） | 写しの入口から `bash run.sh tool run_breaks --lint-expect`（本物の直下からは土台ゲートが止めたため） | rc=1・「❌ b88_r2_exempt.sh」「[STOP] 自己テストを測る壊すプログラムの EXPECT_MSG が「❌」で始まっていません（1 本・監査 cp36 の M-2）」 | **再現した。**写しの run_breaks.py は根のパスを向け替えていないので、読んだのは本物の `.claude/breaks` |


## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ PASS
- ②リスク管理 ＝ FAIL
- ③認知バイアス ＝ FAIL
- ④ソフトウェア工学 ＝ FAIL
- ⑤再現性 ＝ PASS
- ⑥実行プロセス ＝ FAIL
- ⑦主エージェントバイアス ＝ FAIL

**① PASS**＝統計の判断を1つも含まない。乱数0件・新しい閾値／期間／点の一覧0件（A5 の実測）。

**② FAIL**＝当てる先が売買のロジックの本体なのに、守りが3つ 書き方ひとつで外れる（A3-d の欄の取り違え・A4 の `./` の形・A0-b の全件の先の確かめが測られていない）。さらに、いまこの道具は CC の Bash から走らない（B3）。

**③ FAIL**＝「自己テスト 12/12」「b102 期待どおり」「齟齬 0件」を、完成の根拠として読んでいる。12/12 は全件の先の確かめを外しても変わらず、「齟齬 0件」は SPEC の比べ（`--diff`）だけで、照合A〜D は FAIL（B2-c）。

**④ FAIL**＝設計書の契約（must_use・impl_functions）と実装が食い違ったまま承認された。`--dry` が本番と違う確かめをしている。見出しの切り出しが囲みを見ない。守りの一覧が書いた文字のままの部分一致。

**⑤ PASS**＝事実データ7行のうち、中身は全部 写しか本物で再現した（数字も出力も同じ）。SDK の中から打つ形だけが、いまはゲートで打てない（中身は作業場所に依らない）。

**⑥ FAIL**＝承認は3回。③は CC の誤り（完成の条件のコマンドの作業場所）。承認のプログラムと承認の前の検査が照合A〜D を走らせないので、照合C が落ちたまま承認③が通り、道具が CC の手で止まったまま実装の監査に出された。

**⑦ FAIL**＝CC の記録の「設計書との齟齬 0件」（session_worklog_20260924.md:325）は `--diff` の数で、照合A〜D ではない。自己テストの場面の数え方（「4-19 の11＋同時指定」・session_worklog_20260924.md:304）も、4-19 との対応（A0-c）と合わない。

### A0 — 壊すプログラム b101・b102 と自己テストの12場面が、測ると言っているものを本当に測っているか（優先度 A）

**A0-a｜b101＝測れている（指摘なし）。**写しの実測＝rc=1・0.30秒・「❌ 承認の印 T4: 印が違うのに当たった／止まらない（rc=0）」「❌ 承認の印 T11: 空の印で止まらない（rc=0）」・10/12。ほかの10場面は pass。T12 は同時指定で印の照らしより前に止まり、T6 は `--report` で印を見ないので、別の場面が先に落ちて「❌ 承認の印」の文字が出る形ではない。壊す行＝b101_design_apply_no_approval.sh:20「old = '        ok, why = approved_ok(a.design, approved_path)\n'」＝apply_audit_fix.py:364「        ok, why = approved_ok(a.design, approved_path)」。

**A0-b｜b102＝【Critical】宣言どおり T7 は落ちるが、完成の条件 #4 の中心を測っていない。**
- 写しの実測＝rc=1・0.30秒・「❌ 実物と合わない件 T7: 半分だけ当たった／rc=1 code='x = 9\n'」。壊した後に、見本のコードが半分だけ当たった状態（`x = 9`）になることを確かめた。rc=1 は「中身が変わらなかった」件が一覧に入るため（apply_audit_fix.py:484「            stopped.append((f, "中身が変わらなかった", cur))」）で、T7 を落とした理由はコードの比べ。
- b102 が壊すのは当てる直前の確かめ（b102_design_apply_no_precheck.sh:20「old = '        if not _recheck(f, cur):\n'」＝apply_audit_fix.py:477「        if not _recheck(f, cur):」）。設計書の壊し方は「全件を先に確かめる処理を外す」（acceptance.md:434「| `b102_design_apply_no_precheck.sh` | #4 | 全件を先に確かめる処理を外して、確かめながら当てる形に壊すと、自己テストが落ちる |」）で、その止めは apply_audit_fix.py:456「    if hard:」。
- **写しで `if hard:` を常に偽にして自己テストを走らせた＝rc=0・「✅ selftest 12/12 pass」。**＝全件を先に確かめる止めを外しても、自己テストも b101・b102 も何も言わない。外した写しに「2本のファイルへ1件ずつ・2件目の直す前の文字が実物に無い」見本を当てた＝「⏸ 修正 2（）: 直す前の文字が実物に 0 か所」「✅ 修正 1（設計書）: 置き替えた」・rc=1・1本目は `x = 2`、2本目はそのまま＝半分だけ当たった。
- CP41 は この穴を名指ししていた（2026-09-24_impl_instruction_design_cp41_audit_report.md:75「| 全件を先に確かめる（4行目） | `apply_audit_fix.py` の288〜303行 | 見本が1件しかないので落ちない |」）。実装は T7（当てる直前の確かめ）を足したが、この止め（いまの 438〜458行）を測る場面は足していない。

**A0-c｜12場面と 4-19 の対応。**4-19 は11手のうち1・2番が準備で、場面は3〜11番の9つ。T2↔3・T3↔4・T4↔5・T5↔6・T6↔7・T7↔8・T8↔9・T9↔10・T10↔11。4-19 に無い場面＝T1（完成の条件 #1＝節の形）・T11（4-5 の「印が空」）・T12（4-4 の1番＝同時指定）。worklog の「12場面（設計書 4-19 の11＋同時指定）」（session_worklog_20260924.md:304）は、この対応と合わない。**【Minor】弱めた場面＝T6。**4-19 の7番は「監査結果の見本で」（acceptance.md:266「7. 最後に、いまの `--report` の道が通ることを、監査結果の見本で確かめます。」）だが、T6 は本物の CP41 の結果を読み、rc が 0 でも 1 でも pass にする（apply_audit_fix.py:619「        if rc in (0, 1) and "— 当てる重さ:" in out and "テンプレの形ではありません" not in out:」）。判定に使う文字「— 当てる重さ:」は全件の確かめの前に出る行なので、コメントの「全件の確かめまで」も見ていない。写しで T6 の出力を出させた＝rc=1・「❌ 実物と合わない件が 1 件 あるので、1件も当てません」（修正 8 が 0か所）。★この出力の一覧に修正 7 が無い＝修正 7 は「当たる」側に数えられている（A2 の所見）。4-5 の「承認の印が無い（ファイルが無い）」も場面が無い（写しで印のパスを無いファイルにして呼ぶと「承認の印と一致: いいえ（承認の印が無い）」rc=1＝動きは在る）。

**A0-d｜本物に書かないか＝当てる道具の自己テストは書かない。**一時の置き場は apply_audit_fix.py:540「    tmp = tempfile.mkdtemp(prefix="_selftest_impl_apply_", dir=os.path.join(ROOT, ".claude", "state"))」で、finally の中の apply_audit_fix.py:687「        shutil.rmtree(tmp, ignore_errors=True)」が例外でも消す。走らせた後、`.claude/state` の下の `_selftest_impl_apply_` は0件。本物の設計書・印・コードの sha256 は走らせる前と同じ。T6 だけは本物の CP41 の結果と、その修正が名指す本物のファイルを読む（`--dry` なので書かない）。★設計書を作る道具の自己テストは、本物の元データを一時的に書き替えて戻す（3節の3行目）。

**A0-e｜元に戻るか＝戻る。**lib.sh:59「trap _restore EXIT」が途中で落ちても戻し、戻した後にハッシュ値を照らして違えば lib.sh:51「                exit 99」。写しで b101・b102 の後に `run.sh hash aaf`＝pristine と same。

修正の番号＝3・4・5・6・10・11・29

### A1 — 承認の印の照合（approved_ok）が、承認の前に実装を書く道を本当に塞ぐか（優先度 A）

**A1-a｜印が無い・空・違う＝3つとも「いいえ」（指摘なし）。**写しの実測＝無い→「承認の印と一致: いいえ（承認の印が無い）」rc=1／空→T11 pass（「承認の印が空」）／違う→T4 pass。**片方だけが変わる道は在る。**承認のプログラムは approve_design.sh で design_approved.json を書き替えた後（approve_impl.sh:347「bash "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_design.sh" "$LIST"」）に、失敗すると acceptance.approved だけを消す（approve_impl.sh:350「  rm -f "$STATE/acceptance.approved"」・同 364 ほか 391・398・404）。＝design_approved.json は承認済み・acceptance.approved は無い、に分かれる。approve_design.sh だけを打つと、design_approved.json だけが変わる。どちらの分かれ方でも、この道具は acceptance.approved を見るので止まる側に倒れる（取り消しの道で消えるのは acceptance.approved）。**正とすべきは acceptance.approved（いまの実装のまま）。**設計書 acceptance.md:11 は2つを並べて「正本」と書くが、実装が見る1つの方が厳しい側なので、重さは付けない。

**A1-b｜別のパスを渡したとき＝塞がっている（指摘なし）。**写しの実測＝前の版の控え（…20260924.01.md）→「承認の印（8fcd0a1305d1f0f2…）と設計書（706898c362ce70e9…）が違う」rc=1／別の iter の控え（audit-fix-evidence-backtick-20260924.md）→「…（da51e79c11c2df13…）が違う」rc=1／いまの iter の控え（impl-instruction-apply-20260924.md）→「承認の印と一致: はい」。この控えは設計書と1バイトも違わない（sha256 がどちらも 8fcd0a13…）ので、当たる中身も同じ。

**A1-c｜承認の後に書き替えて当てる道＝塞がっている（指摘なし）。**写しで見本の設計書に1文字 足した＝「承認の印（b00835f431f8d0b2…）と設計書（ee6d21b48614129b…）が違う＝承認の後に設計書が変わった」rc=1・見本のコードはそのまま。

修正の番号＝なし

### A2 — 全件を先に確かめてから当てる形（中身の上で当ててから、まとめて書く）が、設計書 4-4・4-5 のとおりか（優先度 A）

**A2-a｜【Major・設計書の側】`--report` にも掛かっている。守りとしては正しい。**当てる処理（apply_audit_fix.py:470「    mem: dict = {}」〜498行）は両方の道の共通。直す前との差（`git diff 360c3e7 d691721`）＝`--report` の当てる処理が「1件ずつ読み直して書く」から「中身の上で全件を当ててから、まとめて書く」に変わった。判断＝git apply と同じ「1つでも当たらなければ1バイトも書かない」形で、CP41 の修正 3 が求めた守り＝正しい。**食い違っているのは設計書の文**＝やらないことの2番（acceptance.md:155「| 2 | 監査結果を当てる道（`--report`）の中身を変えること | 1変更に混ぜない。いまの道が通ることは自己テストで測る | cat_requirements §4.6 の H16 |」）・4-6 の1変更の行（acceptance.md:215「| 1変更 | cat_requirements §4.6 の H16 | 変更の単位は「設計書の実装の指示を、プログラムが当てられる」の1つ。監査結果を当てる道は1文字も変えない |」）・4-13 の3番（acceptance.md:360「3. **監査結果を当てる道（`--report`）。**1文字も変えません。自己テストで、いまの道が通ることも測ります。」）・7-3 の変更の単位。直すのは設計書の側（元データ）。

**【Major・実装の側】`--dry` が本番と同じ確かめをしていない。**`--dry` の戻り（apply_audit_fix.py:459「    if a.dry:」）が、中身の上で当てる処理（477 の `_recheck`）より前に在る。写しで T7 と同じ見本を当てた＝`--dry`＝「✅ --dry: 当たる 2 件（修正 1・2）／当てない 0 件」rc=0 ／ 本番＝「❌ 修正 2: 先の件を当てた後の中身では「直す前の文字」がちょうど1か所ではありません」rc=1。設計書 acceptance.md:183「**完成したときに出るもの。**`apply_audit_fix.py --design <設計書> --dry` が、設計書の実装の指示を全件 確かめて一覧に出します。承認の印と設計書が合わないときは、1件も当てずに止まります。売買は1件も回さないので、net は動きません。」と合わない。当て間違いは起きない（本番は止まる）。

**A2-b｜【Minor】途中で書き込みが失敗したとき。**写しで2本目のファイルを読むだけにして当てた＝例外 PermissionError がそのまま上がり（終了コードも一覧も出ない）、1本目は `x = 2` に書き替わったまま。7-4 の「途中まで当たった状態が残ります」（acceptance.md:503）は事実と合う。ただし書き方が「開いて切り詰めてから書く」（apply_audit_fix.py:491「            with open(path, "w", encoding="utf-8") as fh:」）なので、書いている最中に止まると、そのファイルは途中で切れる。7-4 の理由「番号の順に1本ずつ書くため」も、いまの作り（ファイルごとにまとめて書く）と違う。

**A2-c｜【Major】中身が変わらない件を飛ばして進むと、半分だけ当たった状態が残る。**写しで、1件目は a.py を置き替え、2件目は b.py の直す前の文字に無い文字を「消す文字」にした＝「⏸ 修正 2: 中身が変わらなかった（当てていない）」「✅ 修正 1（設計書）: 置き替えた」rc=1・a.py は `x = 2`・b.py はそのまま。`--report` なら rc=0（apply_audit_fix.py:498「    return 1 if (design_mode and stopped) else 0」）。設計書はこの場合を書いていない。4-4 の6番の「1件でも合わなければ1件も当てない」に合わせて、止める側にする。

**【Major・設計書に書くべき限界】当て終わった文字を後で書き替えると、もう一度 当たる。**当て終わりの見分け（check_one・この設計書で触らない）は、当てた文字がそのまま実物に在るかを見る（apply_audit_fix.py:246「        if kind in ("直した後の文字", "足す文字") and done.strip() and done in cur:」）。写しで、CP41 の結果を `--report --severity Critical,Major --only 7` で当てた＝「✅ 修正 7（Critical）: 足した」rc=0・元データの「7. **壊すプログラム b72・b73・b89。**」の行が2つになった。修正 7 を当てた後に、worklog 7-6 のとおり同じ行へ grep のコマンドを足したため。T6 の出力の一覧にも修正 7 が無い＝「当たる」側。check_one を触らない設計なので、7-4 の塞げないものに書く。

修正の番号＝12・13・14・16・17・18・19・23・24・25・28・34・35

### A3 — 設計書の「実装の指示」の切り出し（read_design_blocks）と、元データとの突き合わせ（impl_src_mismatch）が、設計書 4-2・4-5・4-8 のとおりか（優先度 A）

**A3-a｜【Major】目印は壊さないが、囲みの中の `# ` の行は壊す。**写しで、元データに実装の指示2件を入れて設計書を作り、読み戻した＝塊2つ・欄の食い違い0件・元データとの違い0件（`<!-- ACC_IMPL_START … -->` の目印は切り出しを壊さない）。apply_audit_fix.py:129「    nxt = re.search(r"^#{1,3} ", rest, re.M)             # 次の見出し（### 4-A や ## 5）まで。#### は件の見出しなので飛ばさない」は、囲みを見ずに `# `・`## `・`### ` の行を次の見出しにする。写しで直した後の文字を `# comment` と `x = 2` の2行にした＝「❌ 実装の指示の欄が6つの形になっていません（3 件）」「❌ 修正 1: 4つ目の欄（…）が無い」「根拠の抜き書きが…の形でない」「状態が…どれでもない（None）」rc=1。止まる側（当て間違いは起きない）だが、当てる先 `scripts/priority_rebuild/*.py` には行頭が `# ` のコメントが多い。その行を含む指示は1件も当てられず、出る文も原因と違う。

**A3-b｜順番＝正しい（指摘なし）。**承認の印（apply_audit_fix.py:364）→欄の形（372〜378）→元データとの突き合わせ（383「        bad = impl_src_mismatch(all_fixes, a.src)」）。別の iter の控えを渡すと印で止まる（A1-b の実測）。

**A3-c｜往復は通る。【Major】「案が複数」だけは通らない。**普通の件と「走らせるコマンド」の件は食い違い0件（写しの実測・読めた状態＝確定・確定・4つ目＝直した後の文字／走らせるコマンド）。走らせるコマンドの件は当てずに一覧に出て rc=1。設計書 4-8（acceptance.md:311「…★案が複数のときは `案` の鍵に記号（A・B）を入れ、同じ番号で複数 並べます。」）のとおり同じ番号を2件にすると、build_impl（gen_acceptance.py:612「        head = (f"案{it['案']} " if it.get("案") else "") + str(it.get("種類", "直した後の文字"))」）が `#### 実装 1` を2つ出し、1つの塊に案が1つしか無いので、欄の検査（gen_audit_docs.py:746「    if st == "案が複数" and n_plans < 2:」）が必ず止める。写しの実測＝`--choose 1=A` を付けても「❌ 修正 1: 状態が「案が複数」なのに、案が2つ以上 無い」×2・rc=1。

**A3-d｜【Critical】足りない。1行の欄を元データと照らさないので、未決の件が当たる。**impl_src_mismatch は「直す前の文字」と「中身」だけを照らす（apply_audit_fix.py:193「        if (it.get("直す前の文字") or "") != (f["直す前の文字"] or ""):」・196「        if str(it.get("中身") or "") not in bodies:」）。欄の読み取り（gen_audit_docs.py:698「        m = re.search(rf"^{label}:[ \t]*(.*)$", block, re.M)」）は塊の中の最初の一致を取るので、中身の中に `状態: 確定` の行が在ると、それを欄として読む。写しの実測＝元データの状態を「未決」、直した後の文字を `x = 2` と `状態: 確定` の2行にした＝「✅ 修正 1（設計書）: 置き替えた」rc=0・見本のコードが書き替わった（対照＝中身にその行が無いと「⏸ 状態が「未決」＝まこさんが決めるまで当てない」rc=1）。根拠の抜き書きも同じ＝実物と合わない根拠（「WRONG」）でも、中身に正しい根拠の行を入れると当たった（対照＝入れないと「根拠の行が実物と合わない」で止まる）。＝設計書 4-2 の④（acceptance.md:203「**止まるとき。**①承認の印が無い、または印の値が設計書のハッシュ値と違う ②実装の指示の欄が6つの形になっていない ③直す前の文字か根拠の抜き書きが実物と合わない ④状態が「未決」か「案が複数」。①〜③は1件も当てずに止まります。④はその件だけ当てず、一覧に出します。」）が、この形では成り立たない（前提4＝当て間違いが起きる形）。★「根拠の抜き書き」に囲みの記号が入っても、1行の欄なので囲みの読み取りは切れない（問題は取り違えのほう）。

修正の番号＝2・3・10・11・15・22・24・25

### A4 — 当てない相手（NEVER_WRITE）と TARGET／NEW_FILE の縛りが、設計書 4-4 の 9・10 と 4-6 のとおりか（優先度 A）

**A4-a｜【Minor】CP41 の8件のうち、いまも止まらないもの＝6件。**`scripts/priority_rebuild/score.py`・`scripts/priority_rebuild/eval_engine.py`・`scripts/priority_rebuild/periods.py`・`runner/run_once_v9.py`・`config/cat_params_v9.json`・`.claude/rules/permanent_rules.md`。NEVER_WRITE（apply_audit_fix.py:67〜73）の語を1つも含まないので、守りの一覧に当たらない。設計書の道には TARGET・NEW_FILE の縛りが掛かる（設計書が名指しし、承認されたときだけ当たる）。監査結果の道には縛りが無い。書くべき所＝設計書の 3-2「決めてほしいこと」（元データの `決めてほしいこと` はいま空＝acceptance_src.json:230「  "決めてほしいこと": [],」）。

**【Critical】守りの一覧は、書き方を変えると外れる。**NEVER_WRITE は書いた文字のままの部分一致（apply_audit_fix.py:94「    return any(k in (rel or "") for k in NEVER_WRITE)」）で、TARGET の縛りは揃えた形（apply_audit_fix.py:443「            rel = os.path.normpath((f["対象のファイル"] or "").strip().strip("`"))」）。この差で、`.claude/./hooks/x.sh` と書いた件は、守りの一覧には当たらず、TARGET の `.claude/hooks/x.sh` には当たる。写しの実測＝一時の置き場に `.claude/hooks/x.sh` を作り、対象のファイルを `…/.claude/./hooks/x.sh`、TARGET を `…/.claude/hooks/x.sh` にした＝「✅ 修正 1（設計書）: 置き替えた → …/.claude/hooks/x.sh」rc=0・hook の見本が `x = 2` に書き替わった（対照＝ふつうの書き方なら「守りの仕組みなので当てない」rc=1）。`.claude//hooks/`・`.claude/./tools/`・`.claude//settings.json` も同じ形で、部分一致の語が崩れる。監査結果の道には TARGET の縛りも無いので、書き方だけで通る。設計書 4-16（acceptance.md:346「**書き換えられては困る記録。**承認の印（`acceptance.approved`・`design_approved.json`）・凍結の記録・hook・道具・壊すプログラムには、この道具から1バイトも書きません（`NEVER_WRITE` の一覧をそのまま使います）。」）が成り立たない。

**A4-b｜【Minor】自己申告6 のとおり。止まる側に倒れる。**写しの実測＝対象のファイルを `SDK/.claude/state/…/a.py`、TARGET を `.claude/state/…/a.py` にした（同じファイル＝SDK の `.claude/state` は直下の `.claude/state` への symlink）＝「⏸ TARGET の外（…: SDK/.claude/state/…/a.py）」rc=1・当たらない。当て間違いは起きない。★承認ゲートは実物の場所の後ろの一致で見る（require_acceptance_before_impl.sh:1195「  case "$FILE" in *"$tgt") MATCH=1; break ;; esac」）ので、4-4 の9番（acceptance.md:251「9. 当てる前に、1件ずつ 対象のファイルが設計書の TARGET か NEW_FILE に在るかを見ます。どちらにも無ければ、その件を当てず、一覧に出します（承認ゲートの1201行と同じ縛りを、この道の側にも置きます）。」）の「同じ縛り」になっていない。

**A4-c｜分け方は妥当（指摘なし）。**`--design` だけ、当てなかった件で rc=1（apply_audit_fix.py:463・498）＝4-4 の10番とやらないことの2番のとおり。`--report` は「実物と合わない件」と当てる直前の確かめ（477）で rc=1 になる（後者は A2-a の変化）。

修正の番号＝1・3・10・11・26・27・33・35

### A5 — この実装に、乱数と、新しい数字・点の一覧が0件か（優先度 A）

**乱数＝0件。新しい閾値・期間・点の一覧＝0件（指摘なし）。**`git diff 360c3e7 d691721` の足した行と b101・b102・lib.sh を `random|rng|shuffle|uuid|secrets|mkdtemp|mktemp` で探した＝当たりは `tempfile.mkdtemp`（apply_audit_fix.py:540）と `mktemp -d`（lib.sh:25）と、名前の `sample.py` だけ。足した定数は置き場のパス4つと NEVER_WRITE の2つで、どれも数ではない。**mkdtemp の判断＝乱数の禁止に当てない。**決まるのは一時の置き場の名前だけで、見本・当てる順番・当てる中身・結果には効かない（写しで何回 走らせても同じ 12/12）。禁止の出どころ（engine_tuner_requirements.md:51「| 1 | **ランダムに条件をつなぐだけのもの** | …」）は、条件や値を乱数で選ぶものを指す。

修正の番号＝なし

### B1 — 設計書を作る道具の直し（囲み IMPL・build_impl・4-20・page・verify）が、設計書 4-3 と CP41 の B1 のとおりか（優先度 B）

**B1-a｜確かめた（指摘なし）。**本物の `python3 .claude/tools/gen_acceptance.py --verify`＝rc=0・「— --verify: IMPL は元データの「実装の指示」が空なので出ない設計書（照らさない）」（秒数は取らなかった）。4-20 は非該当の行（acceptance.md:383）で、4-A の表でも非該当（411行）。gen_acceptance.py:714・754・1150「        if kind == "IMPL" and not (d.get("実装の指示") or []):」の分岐どおり。

**B1-b｜確かめた（指摘なし）。**写しの元データに実装の指示2件（直した後の文字1件・走らせるコマンド1件）を入れ、`write(dest=一時のファイル)` と `verify(dest=…)` を走らせ、終わったら元データを戻した（2.59秒）＝write rc=0・verify rc=0・「✅ --verify: IMPL は機械が書いたままです（hash=6846dfdda21c45ef）」・4-20 の見出しは379行目で 4-A（416行目）より前・4-A の行＝「| 4-20 | 条件 | 実装の指示（プログラムが実物に当てる形・6つの欄） | 書いた（実装の指示 2 件・プログラムが作る） |」。囲みの中を1文字 変えると「❌ --verify: IMPL は手で書き換えられています」rc=1。

**B1-c｜【Minor】文字列は止まる。文字列を並べた一覧は、決めた文で止まらない。**散文（文字列）＝「[gen_acceptance] 元データの「実装の指示」が一覧（[]）の形ではありません（fail-closed）。」で止まる。`["散文1"]` は gen_acceptance.py:795「    if "実装の指示" in d and not isinstance(d.get("実装の指示"), list):」を通り抜け、`AttributeError: 'str' object has no attribute 'get'` で落ちる。

**B1-d｜`gen_acceptance.py --selftest`＝本物で 9/9 pass・rc=0・2.74秒。**`pre_audit_check.py --check-design` は走らせていない＝データ不足（理由＝中で hook を実物の入力の形で呼び、hook が本物の記録へ書く作りのため＝本物を書き替えない決まり）。

修正の番号＝32

### B2 — 設計書と実装の食い違いの全件と、その直し方（設計書の側か・実装の側か）（優先度 B）

**B2-a｜自己申告の各件＝6節。**

**B2-b｜自己申告に無い食い違い（監査が見た範囲の全件）。**
1. **【Critical・設計書の側】must_use と selftest。**設計書 7-8（acceptance.md:607〜611 の `"selftest": ["read_design_fixes", "approved_ok", "main"]`）に対し、selftest が呼ぶのは read_design_blocks と main（apply_audit_fix.py:558「        blocks = read_design_blocks("### 4-20 見本\n\n" + ga.build_impl(d1) + "\n### 4-A\n")」）。照合C が落ちる（B2-c）。SPEC（acceptance.md:660〜663）は selftest＝main・read_design_blocks で、実装と合っている。
2. **【Critical・設計書の側】impl_functions の不足。**実装が新しく作った read_design_blocks・design_targets・impl_src_mismatch と、4-20 の囲みを出す section4 が一覧に無い（B2-c の照合A）。
3. **【Major・設計書の側】4-3 の部品の表。**acceptance.md:228「| `gen_acceptance.page` | 4 の節の終わりに「実装の指示」の小節を置く。元データに指示が無ければ、節ごと出さない | 直す |」＝実物は section4 が 4-20 を置き（gen_acceptance.py:714・754）、page は型を見るだけ（795）。read_design_blocks・design_targets・impl_src_mismatch・_recheck の行が無い。
4. **【Major・設計書の側】「--report は1文字も変えない」の4か所**（A2-a）。
5. **【Major・実装の側】--dry の約束**（A2-a）。
6. **【Major・設計書の側】4-5 の「当てる直前に読み直す」**（acceptance.md:302「| 同じファイルに2件 当てる | 当てる直前に読み直すので、後の件が前の件を消さない（いまの作りのまま） |」）＝実物は中身を1回 読んで中身の上で当てる。「中身が変わらない件」の行も無い（A2-c）。
7. **【Major・設計書の側】4-8 の「案」**（A3-c）。
8. **【Critical・実装の側】4-2 の④・4-16**（A3-d・A4）。
9. **【Minor・実装の側】4-4 の9番の「同じ縛り」**（A4-b）。
10. **【Minor・設計書の側】7-4 の「番号の順に1本ずつ書く」**（A2-b）。
11. **【Minor・実装の側】冒頭の説明**（C1）。
12. **【Critical・壊すプログラムの側】6-1・7-6 #4 の壊し方と b102**（A0-b）。

合っているもの＝4-9（`--severity` は `--design` のとき要らない＝apply_audit_fix.py:356「    if a.help or (not design_mode and (not a.report or not a.severity)):」）・4-17（先頭の2行＝363「        print(f"設計書: {a.design}")」・365）・4-10（一時の置き場・必ず消す）・4-14（自己テスト 0.15秒＜5秒・壊すプログラム 0.30秒＜1分）・4-2 の①〜③（写しの実測）。

**B2-c｜出力（SDK の中から）。**

```
$ python3 scripts/priority_rebuild/verify_design_contract.py --diff /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md
design : /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md
impl   : ../../.claude/tools/apply_audit_fix.py
齟齬: 0件
（rc=0・0.13秒）

$ python3 scripts/priority_rebuild/verify_design_contract.py /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md
  [PASS] 自己チェック配線あり: read_design_fixes ／ approved_ok ／ check_one ／ apply_one ／ selftest
  [INFO] ../../.claude/tools/apply_audit_fix.py: 差分がゼロ（commit 済み）＝照合B だけをファイルの中の全関数（16件）と行いました。照合A は判定できません
  [INFO] ../../.claude/tools/gen_acceptance.py: 差分がゼロ（commit 済み）＝照合B だけをファイルの中の全関数（32件）と行いました。照合A は判定できません
  [PASS] must_use read_design_fixes: 全部あり ['item_fields']
  [PASS] must_use main: 全部あり ['read_design_fixes', 'approved_ok', 'check_one', 'apply_one']
  [FAIL] C selftest: 設計書が要求する名前が中身に無い → ['read_design_fixes', 'approved_ok']（../../.claude/tools/apply_audit_fix.py）
RESULT: FAIL（設計と実装が乖離＝採点に進めない）
（rc=1・0.46秒）
```

**照合A は commit 済みで判定できない**（verify_design_contract.py:1053「                  f"ファイルの中の全関数（{len(allf)}件）と行いました。照合A は判定できません")」）。監査が git の差分（`git diff -U0 5545cad d691721`）で同じ比べ方をした＝d691721 が触った関数は、apply_audit_fix.py＝<モジュール直下>・read_design_blocks・read_design_fixes・approved_ok・design_targets・impl_src_mismatch・_recheck・main・selftest、gen_acceptance.py＝<モジュール直下>・build_impl・section4・page・verify。凍結した impl_functions（`impl-instruction-apply-20260924.frozen.json`）に無いもの＝read_design_blocks・design_targets・impl_src_mismatch・section4（_recheck は下線で始まるので数えない）。＝commit の前に照合A を走らせていれば落ちていた。

**B2-d｜直し方＝8節・9節**（設計書の側は元データ、実装の側は道具と壊すプログラム）。

修正の番号＝7・8・9・11・20・21・23・25

### B3 — 承認のプログラム・承認の前の検査との整合（優先度 B）

**【Critical】いま、この道具は CC の Bash から、直下から打つ `--selftest` 以外で1回も走らない。**設計↔実装ゲートが照合C で止める。走らせて確かめた（3つとも止められて走らなかった）＝①直下から `python3 .claude/tools/apply_audit_fix.py --design --dry` ②直下から `--report …cp41… --severity Critical --dry` ③SDK の中から `python3 ../../.claude/tools/apply_audit_fix.py --selftest`（完成の条件のコマンドそのもの）。3つとも「🔒 [設計↔実装ゲート] 設計書通りに実装されていません」「[FAIL] C selftest: 設計書が要求する名前が中身に無い → ['read_design_fixes', 'approved_ok']」。直下からの `--selftest` だけは、ゲートが確かめのための旗として免除するので走った。ゲートは走らせる .py の名前で設計書を選ぶ（require_design_contract_before_run.sh:303「    impl = os.path.basename(str(c.get('impl_file', '')))」）ので、この設計書が `.claude/state/acceptance.md` に在る間、6段の③④⑥（この道具で当てる）は CC の手で止まる。承認のプログラムは照合A〜D を走らせず（approve_impl.sh:360「CHK=$(python3 "$VERIFY_TOOL_PY" --check-approval "$LIST" 2>&1)」だけ）、承認の前の検査も走らせないので、承認③はこの落ち方のまま通った。直すのは設計書の側（must_use を実装に合わせる・修正 7）。

**B3-a｜【Process】決めておく所＝承認の前の検査（require_design_check_before_approval.py の A群）。**承認のプログラムは条件のコマンドを SDK を作業場所にして走らせる（approve_impl.sh:472「        r = subprocess.run(shlex.split(cmd), cwd=SDK, capture_output=True,」）。テンプレ・元データの書き方の決まりは CC が読んで守る形で、承認②で落ちたのは まさに読んで守らなかった所（session_worklog_20260924.md:318「- **原因（実物で確かめた）**＝承認のプログラムは条件のコマンドを SDK を作業場所にして走らせる…」）。承認の前の検査は、承認のプログラムの止まり所を機械で見る作り（require_design_check_before_approval.py:27「#     A8 表に載っている既存の壊すプログラムの宣言を expect_of で読む（:401＝159番の STOP）」ほか A1〜A8）なので、ここに置く。写しの実測＝「直下に在って SDK に無いパスを書いた行」を止める判定を関数にして、承認②の版の控え（…20260924.02.md）に掛けた＝4行とも当たった／いまの設計書＝0件。照合A〜D を同じ所で見る判定も関数にして試した＝いまの設計書で1件（照合C）。★実装の前の承認では照合が落ちるのが当たり前なので、そちらは止め方を まこさんが決める（修正 39・40＝未決）。

**B3-b｜限界（直すかは まこさんが決める）。**B2（条件のコマンドの実走）は、CC の Bash のコマンドの文字に設計書のコマンドの文字がそのまま入っているかで見て、作業場所は見ない（require_design_check_before_approval.py:268「        ok2 = any(ts >= need and not err and cmd_want in cmd for ts, cmd, out, err in runs)」）。この設計書のコマンドを CC が SDK の中から打つと、いまはゲートが止める（上）。直下から `python3 .claude/tools/…` で打つと文字が違うので、B2 に数えない。B1（壊すプログラムの `--measure-only`）も、壊すプログラムが `.claude/tools` を書き替えるので土台ゲートが CC を止める。＝B群は CC の記録からは埋まらず、まこさんの端末の結果（記録に入らない）で埋めるしかない。この検査は「承認は もう1回 要ります」の文字で通すことになる。

修正の番号＝7・11・36・37・38・39・40

### C1 — 名前・説明文・見積もり（優先度 C）

**C1-a｜【Minor】冒頭の説明に古い所が2か所。**①apply_audit_fix.py:4「設計書＝.claude/state/acceptance.md（iter audit-autofix-apply-20260916・まこさん承認 2026-09-16）。」＝この工事の設計書の名が無い ②apply_audit_fix.py:48「  ④恒久71番＝壊すプログラムと自己テストは付けない（まこさん決定 2026-09-16「３作らなくてよい」）。」＝この工事で付けた。使い方の `--design`・`--selftest` の段（19〜25行）は、いまの動きと合っている。27〜34行の「何をするか」は `--report` の手順だけで、`--design` の手順は19〜23行に在る。

**C1-b｜揃っている（指摘なし）。**read_design_blocks・read_design_fixes は既にある read_fixes と、approved_ok は既にある `*_ok` と、囲み IMPL は AUDITTODO と同じ付け方（登録＝gen_acceptance.py:119「          "IMPL")」・目印は `_begin` の形）。

**C1-c｜外れの原因は3つ（指摘なし・修正は B3 に含める）。**①承認③＝CC の誤り（完成の条件のコマンドの作業場所・L-614）。承認のプログラムの `_run` は読める所に在ったので、設計書に書けた ②まこさんの操作＝Claude Code の権限の制限で、CC が `.claude/tools` と hook に書けなかった分。設計を書いた時点（worklog §5-4）では `.claude/tools` への制限は記録に無く、書けなかった ③T6 の作り直し（本物の監査結果を見本にした・L-615）＝4-19 の7番は「見本で」と書いていたので、設計どおりに作れば起きなかった。

修正の番号＝30・31


## 5. 外部検索

### 検索 1 — なし

しなかった（依頼書の指定）。依頼書の外部検索要請は「検索 1 — なし」で、「外部検索は要りません。『しなかった』と書いてください」と指定している。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

**事実。書いた人が2つに分かれたことが原因の食い違いは、見つからなかった。**当てるプログラム `apply_impl_edits.py`（206行・8か所＝a1〜a4・g1・g2・g4・g6）は、CC の前のセッションの一時の置き場（`/private/tmp/claude-501/…/scratchpad/records/`）に残っていた。8か所の「直した後の文字」は、いまの実物に在る（例＝apply_audit_fix.py:441「        # ★設計書の道だけ（設計書 4-4 の 9）＝対象のファイルが TARGET／NEW_FILE に無ければ当てない」・gen_acceptance.py:119「          "IMPL")」）。B2 の食い違いは、どれも設計書の欄（must_use・impl_functions・4-3）を実装の後に揃えなかったことが原因。★ただし a4（TARGET の縛り）の比べ方（normpath）が、A4 の2件（守りの一覧との差・`SDK/` の前置き）の片方の元になっている。

### 自己申告 2

**事実。【Minor】（修正 29）。**T6 は本物の CP41 の結果を読み、rc が 0 でも 1 でも pass（apply_audit_fix.py:619）。写しで T6 の出力を出させた＝rc=1・「❌ 実物と合わない件が 1 件」。コメントは「全件の確かめまで」だが、判定に使う文字は確かめの前に出る。さらにこの出力は、修正 7 がもう一度 当たる側に入っていることを隠していた（A2 の実測＝当てると行が2つになる）。4-19 の7番の「見本」で測るには、テンプレの11節を満たす見本の監査結果が要る。この監査では作らない。

### 自己申告 3

**事実。判断＝守りとして正しく、設計書の側を直す**（A2-a・修正 16〜19）。直す前の動き（先の件だけ書いて rc=0）は、git apply の atomicity の決まりに反していた（CP41 の外部検索）。

### 自己申告 4

**事実（食い違いではない）。**`impl-instruction-apply-20260924.breaks.json` の行1・2＝「壊すプログラムが無い＝この行は済にできない」。設計（6-1）のとおり。★#1・#2 を測る場面（T1・T2・T3・T6）は、b101・b102 が壊さない。＝#1・#2 は「条件のコマンドが rc=0」以上の担保を持たない。結論を変えないので修正は書かない。

### 自己申告 5

**事実**（控え …01.md・…02.md・本体と、worklog 7-8〜7-10）。③の原因は設計書に書けた（C1-c）。同じ型を機械で止める判定を承認の前の検査に足す（修正 36〜38）。

### 自己申告 6

**事実。【Minor】（修正 26・27）。**写しの実測＝TARGET の外で止まる。当て間違いにはならない。承認ゲートの比べ方（実物の場所の後ろの一致）とも違う（A4-b）。

### 自己申告 7

**事実（この工事の外）。**写しの入口から走らせた＝rc=1・「❌ b88_r2_exempt.sh」。b101・b102 の宣言は「❌ 承認の印」「❌ 実物と合わない件」で、道具の決まり（run_breaks.py:217「        if not msg.startswith("❌"):」）を満たす。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ NO（根拠＝設計書が決めた動きのうち、次の3つが実物で成り立たない。①守りの仕組みには当てない（4-16）＝`.claude/./hooks/x.sh` と書いた件を、写しで hook の見本に当てた（rc=0）。守りの一覧は書いた文字のままの部分一致（apply_audit_fix.py:94）で、TARGET の縛りだけが揃えた形（:443）のため ②状態が「未決」の件は当てない（4-2 の④）＝中身に「状態: 確定」の行を入れた未決の件が当たった（rc=0）。元データとの突き合わせが1行の欄を照らさない（:193・:196） ③自己テスト 12/12 と b102 の「期待どおり」は、全件を先に確かめる止め（:456）を測っていない＝外しても 12/12 pass・外した写しで半分だけ当たった。あわせて、監査結果を当てる道も含めて、この道具はいま CC の Bash から走らない（設計↔実装ゲートが照合C で止める）。①②は前提4 の「当て間違いが起きる形」。承認の印の照らし・欄の形・当てる直前の確かめ・TARGET の縛り・当てなかった件の rc=1 は、写しで設計書どおりに働いた）
- 問い2 ＝ YES（根拠＝食い違いを B2-b に12件 挙げ、それぞれ直す側を示した。自己申告に無いもの＝must_use（照合C）・impl_functions の不足（照合A）・4-3 の部品の表・4-5 の「読み直す」・4-8 の案・--dry・中身が変わらない件・守りの一覧の書き方・欄の取り違え・6-1 #4 の壊し方と b102。設計書の側＝元データ acceptance_src.json（修正 7〜10・16〜24・33・34）と作り直すコマンド（11・25・35）。実装の側＝apply_audit_fix.py・gen_acceptance.py・b102（修正 1〜6・12〜15・26〜32）。進め方＝承認の前の検査（36〜40））

### 結論と件数

- 結論＝NO-GO
- Critical＝11
- Major＝14
- Minor＝10
- Process＝5

**何が弱まるか（実物の行）。**①守りの一覧＝apply_audit_fix.py:94 の部分一致が、`./`・`//`・大文字小文字で外れ、hook・道具・壊すプログラム・settings に書ける ②未決・案が複数の止め＝gen_audit_docs.py:698 の最初の一致と、apply_audit_fix.py:193・196 が1行の欄を照らさないことで、中身の中の1行で外れる ③完成の条件 #4 の測り＝apply_audit_fix.py:456 の止めを測る場面が無く、外しても何も落ちない。

**★向きは正しい。**指示を設計書の中に置き、承認のハッシュ値で凍結し、読み取り・確かめ・当てるを1か所にまとめる形は、そのままでよい。直しは局所で、直した後の文字を写しに全部 当てて確かめた＝自己テスト 16/16 pass（修正 3 で足した T13〜T16 を含む）・b101＝rc=1（T4・T11）・直した b102＝rc=1（T13・T16）・修正 1 と修正 2 を1つずつ戻すと T15・T14 が落ちる・上の場面（欄の取り違え・`./` の形・`# ` の行・--dry・中身が変わらない件・`SDK/` の前置き・根拠の取り違え）は全部 止まるか正しく当たった。


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 93-94
直す前の文字:
~~~
def never_write(rel: str) -> bool:
    return any(k in (rel or "") for k in NEVER_WRITE)
~~~
直した後の文字:
~~~
def never_write(rel: str) -> bool:
    # 守りの仕組みか。書いた形・揃えた形・実物の場所の3つで見る（大文字と小文字は区別しない）。
    # ★2026-09-24（監査 CP42 の A4）＝直す前は書いた文字のままを見たので、「.claude/./hooks/x.sh」と書くと
    #   一覧に当たらず、TARGET の縛り（揃えた形で照らす）も通って、hook に書けた（写しで実測）。
    raw = (rel or "").strip().strip("`")
    forms = (raw, os.path.normpath(raw), os.path.realpath(repo_path(raw)))
    return any(k.lower() in f.replace(os.sep, "/").lower() for f in forms for k in NEVER_WRITE)
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:94「    return any(k in (rel or "") for k in NEVER_WRITE)」
状態: 確定

#### 修正 2
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 195-197
直す前の文字:
~~~
        bodies = [b for _a, _k, b in f["4つ目"]]
        if str(it.get("中身") or "") not in bodies:
            bad.append(f"実装 {num}: 中身（4つ目の欄）が元データと違う（囲みの中で読み取りが切れた疑い）")
~~~
足す文字:
~~~

        # ★2026-09-24（監査 CP42 の A3）＝1行の欄も元データと照らす。直す前は中身と直す前の文字だけを照らしたので、
        #   中身の中に「状態: 確定」の行が在ると読み取りがそれを欄と取り違え、元データで「未決」の件が当たった（写しで実測）。
        want = {"対象のファイル": it.get("対象のファイル", ""), "直す箇所": it.get("直す箇所", "なし"),
                "根拠の抜き書き": it.get("根拠の抜き書き", ""), "状態": it.get("状態", "確定")}
        for key, val in want.items():
            if str(val or "").strip() != str(f.get(key) or "").strip():
                bad.append(f"実装 {num}: {key}が元データと違う（囲みの中の行を欄と読み違えた疑い）")
        if str(it.get("種類", "直した後の文字")) not in [k for _a, k, _b in f["4つ目"]]:
            bad.append(f"実装 {num}: 種類（4つ目の見出し）が元データと違う")
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:193「        if (it.get("直す前の文字") or "") != (f["直す前の文字"] or ""):」
状態: 確定

#### 修正 3
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 684-685
直す前の文字:
~~~
        else:
            fails.append(f"❌ 同時指定 T{total}: rc={rc}")
~~~
足す文字:
~~~


        # T13（監査 CP42 の A0）＝2本のファイルに1件ずつ・2件目の「直す前の文字」が実物に無い → 1件も当たらず rc=1
        #   ★全件を先に確かめる処理（実物と合わない件が在れば1件も当てない）を測る。直す前はこの場面が無く、
        #     その処理を外しても自己テストは 12/12 のままだった（写しで実測）。
        total += 1
        code2 = os.path.join(tmp, "sample2.py")
        rel2 = os.path.relpath(code2, ROOT)
        open(code, "w", encoding="utf-8").write("x = 1\n")
        open(code2, "w", encoding="utf-8").write("y = 1\n")
        items13 = [item(1, rel, "x = 1", "直した後の文字", "x = 2", ev),
                   item(2, rel2, "NOT_THERE", "直した後の文字", "y = 2", f"{rel2}:1「y = 1」")]
        open(md, "w", encoding="utf-8").write(design(items13, rel + ", " + rel2, srcj))
        mark_of(md, mark)
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and open(code).read() == "x = 1\n" and open(code2).read() == "y = 1\n":
            ok += 1
            print(f"   T{total} 1件でも実物と合わなければ、ほかの件も当たらない（rc=1） → pass")
        else:
            fails.append(f"❌ 実物と合わない件 T{total}: 先に全件を確かめずに当たった／rc={rc} code={open(code).read()!r}")

        # T14（監査 CP42 の A3）＝状態が「未決」の件の中身に「状態: 確定」の行が在っても当たらない
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 2\n状態: 確定", ev, state="未決")])
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and open(code).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 中身の中の、欄と同じ形の行を、欄と取り違えない → pass")
        else:
            fails.append(f"❌ 欄の取り違え T{total}: 未決の件が当たった（rc={rc}）")

        # T15（監査 CP42 の A4）＝守りの仕組みを「./」の形で書いても当てない
        total += 1
        hk = os.path.join(tmp, ".claude", "hooks")
        os.makedirs(hk, exist_ok=True)
        hook = os.path.join(hk, "x.sh")
        open(hook, "w", encoding="utf-8").write("x = 1\n")
        odd = os.path.relpath(os.path.join(tmp, ".claude"), ROOT) + "/./hooks/x.sh"
        open(md, "w", encoding="utf-8").write(design(
            [item(1, odd, "x = 1", "直した後の文字", "x = 2", f"{odd}:1「x = 1」")],
            os.path.relpath(hook, ROOT), srcj))
        mark_of(md, mark)
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and "守りの仕組みなので当てない" in out and open(hook).read() == "x = 1\n":
            ok += 1
            print(f"   T{total} 守りの仕組みは、書き方を変えても当てない → pass")
        else:
            fails.append(f"❌ 守りの仕組み T{total}: 書き方を変えると当たった（rc={rc}）")

        # T16（監査 CP42 の A0）＝先の件が、後の件の「直す前の文字」をもう1つ作る → 1件も当たらず rc=1
        #   ★当てる直前の確かめ（_recheck）だけが受ける場面。「直す前の文字が無くなる」場面（T7）は、
        #     当てても中身が変わらない件で止める処理も受ける。
        total += 1
        fresh([item(1, rel, "x = 1", "直した後の文字", "x = 1\nz = 0\ny = 2", ev),
               item(2, rel, "y = 2", "直した後の文字", "y = 3", ev)], body_text="x = 1\ny = 2\n")
        rc, out = run(["--design", md, "--src", srcj], mark)
        if rc == 1 and open(code).read() == "x = 1\ny = 2\n":
            ok += 1
            print(f"   T{total} 先の件が後の件の「直す前の文字」を2つにすると、1件も当たらず rc=1 → pass")
        else:
            fails.append(f"❌ 実物と合わない件 T{total}: 2か所になった件が当たった／rc={rc} code={open(code).read()!r}")
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:685「            fails.append(f"❌ 同時指定 T{total}: rc={rc}")」
状態: 確定

#### 修正 4
対象のファイル: .claude/breaks/b102_design_apply_no_precheck.sh
直す箇所: 23-24
直す前の文字:
~~~
new = '        if False:  # b102 が壊した（確かめずに当てる）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
~~~
直した後の文字:
~~~
new = '        if False:  # b102 が壊した（確かめずに当てる）\n'
s = s.replace(old, new, 1)
old2 = '    if hard:\n'
if old2 not in s:
    raise SystemExit("[b102] 壊す対象の行が見つからない（全件を先に確かめる処理）")
s = s.replace(old2, '    if False:  # b102 が壊した（全件を先に確かめない）\n', 1)
open(p, 'w', encoding='utf-8').write(s)
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:456「    if hard:」
状態: 確定

#### 修正 5
対象のファイル: .claude/breaks/b102_design_apply_no_precheck.sh
直す箇所: 3-3
直す前の文字:
~~~
# MEANS: 当てる直前の確かめを外して確かめながら当てる形にすると、当てる道具の自己テスト T7（半分だけ当てない）が落ちた
~~~
直した後の文字:
~~~
# MEANS: 全件を先に確かめる処理と当てる直前の確かめを外して、確かめながら当てる形にすると、当てる道具の自己テスト T13・T16（半分だけ当てない）が落ちた
~~~
根拠の抜き書き: .claude/state/acceptance.md:434「| `b102_design_apply_no_precheck.sh` | #4 | 全件を先に確かめる処理を外して、確かめながら当てる形に壊すと、自己テストが落ちる |」
状態: 確定

#### 修正 6
対象のファイル: .claude/breaks/b102_design_apply_no_precheck.sh
直す箇所: 8-9
直す前の文字:
~~~
#   壊し方＝main の `if not _recheck(f, cur):` を常に偽にする（確かめずに当てる）。
#   期待＝自己テスト（`--selftest`）の T7 が落ちる（終了コード 1・出力に「❌ 実物と合わない件」）。
~~~
直した後の文字:
~~~
#   壊し方＝main の `if hard:` と `if not _recheck(f, cur):` を常に偽にする（先に全件を確かめず、当てる直前にも確かめずに当てる）。
#   期待＝自己テスト（`--selftest`）の T13 と T16 が落ちる（終了コード 1・出力に「❌ 実物と合わない件」）。
~~~
根拠の抜き書き: .claude/breaks/b102_design_apply_no_precheck.sh:20「old = '        if not _recheck(f, cur):\n'」
状態: 確定

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 305-305
直す前の文字:
~~~
      "selftest": ["read_design_fixes", "approved_ok", "main"]
~~~
直した後の文字:
~~~
      "selftest": ["read_design_blocks", "main"]
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:558「        blocks = read_design_blocks("### 4-20 見本\n\n" + ga.build_impl(d1) + "\n### 4-A\n")」
状態: 確定

#### 修正 8
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 296-296
直す前の文字:
~~~
["<モジュール直下>", "read_design_fixes", "approved_ok", "main", "selftest"],
~~~
直した後の文字:
~~~
["<モジュール直下>", "never_write", "read_design_blocks", "read_design_fixes", "approved_ok", "design_targets", "impl_src_mismatch", "main", "selftest"],
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:163「def design_targets(design_text: str) -> set:」
状態: 確定

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 297-297
直す前の文字:
~~~
["<モジュール直下>", "build_impl", "page", "verify"]
~~~
直した後の文字:
~~~
["<モジュール直下>", "build_impl", "section4", "page", "verify"]
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:754「        if no == "4-20" and (d.get("実装の指示") or []):」
状態: 確定

#### 修正 10
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 204-204
直す前の文字:
~~~
      "11. 「直した後の文字」の中身に、囲みの記号そのもの（チルダ3つ）を1つ入れて呼びます。読み取った中身が元データと違うので、1件も当たらずに止まります。"
~~~
足す文字:
~~~
,
      "12. 見本の設計書に、2本の見本のコードへ1件ずつ実装の指示を入れ、2件目の「直す前の文字」を実物に無い文字にして呼びます。1件目も当たらず、終了コードが 1 になります（全件を先に確かめる処理を測る場面・完成の条件 #4 と壊すプログラム b102）。",
      "13. 状態を「未決」にした件の「直した後の文字」に、「状態: 確定」の行を入れて呼びます。元データと合わないので、1件も当たりません。",
      "14. 対象のファイルを、守りの仕組みのファイルを「./」の形で書いたものにして呼びます。当てず、「守りの仕組みなので当てない」と一覧に出ます。",
      "15. 先の件が、後の件の「直す前の文字」をもう1つ作る形にして呼びます。1件も当たらず、終了コードが 1 になります（当てる直前の確かめを測る場面・壊すプログラム b102）。"
~~~
根拠の抜き書き: .claude/state/acceptance.md:267「8. 見本の設計書に実装の指示を2件 入れ、2件とも同じ見本のコードを相手にし、先の件が後の件の「直す前の文字」を消す形にします。1件も当たらず、終了コードが 1 になります（完成の条件 #4 と壊すプログラム b102 を測る場面）。」
状態: 確定

#### 修正 11
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は本物では走らせていない（本物の設計書を書き替えるため）。写しで同じ関数（write に一時の置き場を渡す形）を走らせた＝囲み IMPL の試しと合わせて 2.59秒・rc=0。修正 1〜10 を当てたあとに1回 打つ（SPEC が新しい実装から作り直される。設計書のハッシュ値が変わるので、そのあと まこさんの承認が要る））「  "_作り方": "python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify",」
状態: 確定

### Major

#### 修正 12
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 459-463
直す前の文字:
~~~
    if a.dry:
        nums = "・".join(f["番号"] for f, _w, _c in ready) or "（無し）"
        print(f"\n✅ --dry: 当たる {len(ready)} 件（修正 {nums}）／"
              f"当てない {len(stopped)} 件（実物と合わない件は0）")
        return 1 if (design_mode and stopped) else 0
~~~
消す文字:
~~~
    if a.dry:
        nums = "・".join(f["番号"] for f, _w, _c in ready) or "（無し）"
        print(f"\n✅ --dry: 当たる {len(ready)} 件（修正 {nums}）／"
              f"当てない {len(stopped)} 件（実物と合わない件は0）")
        return 1 if (design_mode and stopped) else 0
~~~
根拠の抜き書き: .claude/state/acceptance.md:183「**完成したときに出るもの。**`apply_audit_fix.py --design <設計書> --dry` が、設計書の実装の指示を全件 確かめて一覧に出します。承認の印と設計書が合わないときは、1件も当てずに止まります。売買は1件も回さないので、net は動きません。」
状態: 確定

#### 修正 13
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 487-487
直す前の文字:
~~~
        plan.append((f, what, path))
~~~
足す文字:
~~~

    if a.dry:
        nums = "・".join(f["番号"] for f, _w, _p in plan) or "（無し）"
        print(f"\n✅ --dry: 当たる {len(plan)} 件（修正 {nums}）／"
              f"当てない {len(stopped)} 件（実物と合わない件は0・当てた後の中身でも確かめた）")
        return 1 if (design_mode and stopped) else 0
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:477「        if not _recheck(f, cur):」
状態: 確定

#### 修正 14
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 482-485
直す前の文字:
~~~
        if new == cur:
            print(f"   ⏸ 修正 {f['番号']}: 中身が変わらなかった（当てていない）")
            stopped.append((f, "中身が変わらなかった", cur))
            continue
~~~
直した後の文字:
~~~
        if new == cur:
            print(f"\n❌ 修正 {f['番号']}: 当てても中身が変わりません（消す文字が直す前の文字の中に無い など）"
                  f"＝実物と合わない件が在るので、1件も当てません（半分だけ当たった状態を作らない）")
            return 1
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:484「            stopped.append((f, "中身が変わらなかった", cur))」
状態: 確定

#### 修正 15
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 128-130
直す前の文字:
~~~
    rest = design_text[m.end():]
    nxt = re.search(r"^#{1,3} ", rest, re.M)             # 次の見出し（### 4-A や ## 5）まで。#### は件の見出しなので飛ばさない
    sec = rest[:nxt.start()] if nxt else rest
~~~
直した後の文字:
~~~
    rest = design_text[m.end():]
    # 次の見出し（### 4-A や ## 5）まで。#### は件の見出しなので飛ばさない。
    # ★2026-09-24（監査 CP42 の A3）＝囲み（チルダ3つの行）の中の行は見出しと見ない。直す前は、中身の中の
    #   「# コメント」の行を次の見出しと取り違えて節が途中で切れ、1件も当てられなかった（写しで実測）。
    end, pos, fence = len(rest), 0, False
    for ln in rest.splitlines(keepends=True):
        if ln.rstrip("\n") == "~" * 3:
            fence = not fence
        elif not fence and re.match(r"#{1,3} ", ln):
            end = pos
            break
        pos += len(ln)
    sec = rest[:end]
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:129「    nxt = re.search(r"^#{1,3} ", rest, re.M)             # 次の見出し（### 4-A や ## 5）まで。#### は件の見出しなので飛ばさない」
状態: 確定

#### 修正 16
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 222-222
直す前の文字:
~~~
"中身": "監査結果を当てる道（`--report`）の中身を変えること", "理由": "1変更に混ぜない。いまの道が通ることは自己テストで測る"
~~~
直した後の文字:
~~~
"中身": "監査結果を当てる道（`--report`）の読み取りと確かめ（`read_fixes`・`check_one`・`check_evidence`・`apply_one`）を変えること", "理由": "1変更に混ぜない。いまの道が通ることは自己テストで測る。★当てる処理（全件を中身の上で当ててから、ファイルごとにまとめて書く）は `--report` と `--design` で1か所を共有するので、監査 CP41 の A2（修正 3）の直しは `--report` にも掛かる。先の件が後の件の「直す前の文字」を消す場面では、直す前の「先の件だけ書いて終了コード 0」が、いまは「1バイトも書かずに終了コード 1」になる（監査 CP42 が写しで確かめた）"
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:477「        if not _recheck(f, cur):」
状態: 確定

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 133-133
直す前の文字:
~~~
監査結果を当てる道は1文字も変えない |",
~~~
直した後の文字:
~~~
監査結果を当てる道の読み取りと確かめは変えない。当てる処理は両方の道で共有するので、監査 CP41 の A2 の直しは `--report` にも掛かる（やらないことの2番） |",
~~~
根拠の抜き書き: .claude/state/acceptance.md:215「| 1変更 | cat_requirements §4.6 の H16 | 変更の単位は「設計書の実装の指示を、プログラムが当てられる」の1つ。監査結果を当てる道は1文字も変えない |」
状態: 確定

#### 修正 18
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 158-158
直す前の文字:
~~~
**1文字も変えません。自己テストで、いまの道が通ることも測ります。
~~~
直した後の文字:
~~~
**読み取りと確かめは変えません。当てる処理は `--design` と共有するので、先の件が後の件の「直す前の文字」を消す場面では、直す前の「先の件だけ書いて終了コード 0」が「1バイトも書かずに終了コード 1」に変わります（監査 CP41 の A2）。自己テストで、いまの道が読み取りと確かめの段まで通ることも測ります。
~~~
根拠の抜き書き: .claude/state/acceptance.md:360「3. **監査結果を当てる道（`--report`）。**1文字も変えません。自己テストで、いまの道が通ることも測ります。」
状態: 確定

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 274-274
直す前の文字:
~~~
監査結果を当てる道は1文字も変えません。
~~~
直した後の文字:
~~~
監査結果を当てる道の読み取りと確かめは変えません（当てる処理は両方の道で共有するので、監査 CP41 の A2 の直しは `--report` にも掛かります）。
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:470「    mem: dict = {}」
状態: 確定

#### 修正 20
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 89-89
直す前の文字:
~~~
      "| `gen_acceptance.page` | 4 の節の終わりに「実装の指示」の小節を置く。元データに指示が無ければ、節ごと出さない | 直す |",
~~~
直した後の文字:
~~~
      "| `gen_acceptance.section4` | 4-20 を囲み `IMPL`（`build_impl` の出力）として 4-A の前に置き、4-A の表に「書いた（実装の指示 N 件・プログラムが作る）」を出す。元データに指示が無ければ、4-20 は非該当の行になる | 直す |",
      "| `gen_acceptance.page` | 元データの `実装の指示` が一覧（[]）でなければ止める（fail-closed） | 直す |",
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:754「        if no == "4-20" and (d.get("実装の指示") or []):」
状態: 確定

#### 修正 21
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 91-91
直す前の文字:
~~~
      "| `apply_audit_fix.approved_ok` | 承認の印の値と、設計書のハッシュ値が同じかを見る。違えば当てない | **新設** |",
~~~
足す文字:
~~~

      "| `apply_audit_fix.read_design_blocks` | 設計書から「4-20 実装の指示」の節を切り出し、`#### 実装 <番号>` ごとの塊に分ける（`read_design_fixes` と、`main` の欄の検査が呼ぶ） | **新設** |",
      "| `apply_audit_fix.design_targets` | 設計書の `TARGET:`・`NEW_FILE:` の行から、当ててよいファイルの集合を作る | **新設** |",
      "| `apply_audit_fix.impl_src_mismatch` | 設計書から読んだ実装の指示を、元データの `実装の指示` と突き合わせる（囲みの中で読み取りが切れたら止める） | **新設** |",
      "| `apply_audit_fix._recheck` | 当てる直前に、前の件を当てた後の中身でも「直す前の文字がちょうど1か所」かを見る | **新設** |",
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:123「def read_design_blocks(design_text: str) -> list:」
状態: 確定

#### 修正 22
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 141-141
直す前の文字:
~~~
★案が複数のときは `案` の鍵に記号（A・B）を入れ、同じ番号で複数 並べます。
~~~
直した後の文字:
~~~
★「案が複数」の件は、実装の指示に書きません（承認の前に まこさんが決め、「確定」で書きます）。同じ番号を2件 並べる形は、欄の検査（`item_errors`）が「状態が「案が複数」なのに、案が2つ以上 無い」で必ず止めるので当てられません（監査 CP42 が写しで実測）。
~~~
根拠の抜き書き: .claude/tools/gen_audit_docs.py:746「    if st == "案が複数" and n_plans < 2:」
状態: 確定

#### 修正 23
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 121-121
直す前の文字:
~~~
      "| 同じファイルに2件 当てる | 当てる直前に読み直すので、後の件が前の件を消さない（いまの作りのまま） |",
~~~
直した後の文字:
~~~
      "| 同じファイルに2件 当てる | ファイルごとに中身を1回 読み、番号の順に中身の上で当ててから、まとめて書くので、後の件が前の件を消さない |",
      "| 当てても中身が変わらない件が在る（消す文字が直す前の文字の中に無い など） | 1件も当てずに止まり、終了コードを 1 にする。★実測（監査 CP42）＝直す前は、その件だけ飛ばして ほかの件を書き、半分だけ当たった状態が残った |",
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:484「            stopped.append((f, "中身が変わらなかった", cur))」
状態: 確定

#### 修正 24
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 289-289
直す前の文字:
~~~
    {"問い": "実装の指示の文字が、この設計書の §4 の中身と合っているか", "塞げないこと": "この道具は見ません。設計書の監査（6段の②）が、設計の文と指示の文を並べて見ます"}
~~~
足す文字:
~~~
,
    {"問い": "当て終わった文字を、あとで書き替えたら", "塞げないこと": "見分けられません。「当て終わっている」は、直した後の文字（足す文字の件は、直す前の文字＋足す文字）が実物に そのまま在るかで見るので、当てた後にその文を書き替えると、足す文字の件は もう一度 当たり、同じ文が2つになります（監査 CP42 が写しで実測＝監査 CP41 の修正 7 を `--only 7` で当てると、4-13 の7番の行が2つになった）"},
    {"問い": "実装の指示の中身に、「### 」で始まる行が在ったら", "塞げないこと": "欄の読み取り（`gen_audit_docs.item_fields`）が、その行を塊の終わりと見て切ります。元データとの突き合わせで止まり、1件も当てません（`gen_audit_docs.py` は直さない＝やらないことの5番）"}
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:246「        if kind in ("直した後の文字", "足す文字") and done.strip() and done in cur:」
状態: 確定

#### 修正 25
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は本物では走らせていない（本物の設計書を書き替えるため）。写しで同じ関数を走らせた＝2.59秒・rc=0。Major まで当てる場合に、修正 12〜24 のあとに1回 打つ）「  "_作り方": "python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify",」
状態: 確定

### Minor

#### 修正 26
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 171-171
直す前の文字:
~~~
                    out.add(os.path.normpath(p))
~~~
直した後の文字:
~~~
                    out.add(os.path.realpath(repo_path(p)))
~~~
根拠の抜き書き: .claude/hooks/require_acceptance_before_impl.sh:1195「  case "$FILE" in *"$tgt") MATCH=1; break ;; esac」
状態: 確定

#### 修正 27
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 443-443
直す前の文字:
~~~
            rel = os.path.normpath((f["対象のファイル"] or "").strip().strip("`"))
~~~
直した後の文字:
~~~
            rel = os.path.realpath(repo_path(f["対象のファイル"] or ""))
~~~
根拠の抜き書き: .claude/state/acceptance.md:251「9. 当てる前に、1件ずつ 対象のファイルが設計書の TARGET か NEW_FILE に在るかを見ます。どちらにも無ければ、その件を当てず、一覧に出します（承認ゲートの1201行と同じ縛りを、この道の側にも置きます）。」
状態: 確定

#### 修正 28
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 489-492
直す前の文字:
~~~
    for path, new in mem.items():
        if any(p == path for _f, _what, p in plan):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
~~~
直した後の文字:
~~~
    for path, new in mem.items():
        if any(p == path for _f, _what, p in plan):
            # ★2026-09-24（監査 CP42 の A2-b）＝一時のファイルに書いてから置き替える（書き込みの途中で落ちても、
            #   そのファイルが途中で切れない）。書けなかったら例外で落とさず、止まった所を出して rc=1。
            tmp_path = path + ".apply_tmp"
            try:
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    fh.write(new)
                os.chmod(tmp_path, os.stat(path).st_mode & 0o7777)
                os.replace(tmp_path, path)
            except OSError as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                print(f"\n❌ 書き込みに失敗しました（{os.path.relpath(path, ROOT)}・{e}）。"
                      f"この前に書いたファイルは当たった後です＝途中まで当たった状態が残っています")
                return 1
~~~
根拠の抜き書き: .claude/state/acceptance.md:503「| **当てる途中でプロセスが落ちたら** | 途中まで当たった状態が残ります。戻す仕組みは在りません（控えを取らず、番号の順に1本ずつ書くため） |」
状態: 確定

#### 修正 29
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 619-619
直す前の文字:
~~~
        if rc in (0, 1) and "— 当てる重さ:" in out and "テンプレの形ではありません" not in out:
~~~
直した後の文字:
~~~
        if (rc in (0, 1) and "— 当てる重さ:" in out and "テンプレの形ではありません" not in out
                and ("✅ --dry:" in out or "\n❌ " in out)):
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:618「        rc, out = run(["--report", rep, "--severity", "Critical,Major", "--dry"], None)」
状態: 確定

#### 修正 30
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 4-4
直す前の文字:
~~~
設計書＝.claude/state/acceptance.md（iter audit-autofix-apply-20260916・まこさん承認 2026-09-16）。
~~~
直した後の文字:
~~~
設計書＝.claude/state/acceptance.md（iter audit-autofix-apply-20260916・まこさん承認 2026-09-16）。--design の口と自己テスト＝iter impl-instruction-apply-20260924（まこさん承認 2026-09-24）。
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:20「    ★2026-09-24（設計書 impl-instruction-apply-20260924・まこさん承認）＝設計書の「4-20 実装の指示」を当てる口。」
状態: 確定

#### 修正 31
対象のファイル: .claude/tools/apply_audit_fix.py
直す箇所: 48-48
直す前の文字:
~~~
  ④恒久71番＝壊すプログラムと自己テストは付けない（まこさん決定 2026-09-16「３作らなくてよい」）。
~~~
直した後の文字:
~~~
  ④--report の道には、壊すプログラムと自己テストを付けない（恒久71番・まこさん決定 2026-09-16「３作らなくてよい」）。--design の道は、当てる先が売買のロジックの本体なので付けた（自己テスト --selftest・壊すプログラム b101・b102・設計書 impl-instruction-apply-20260924）。
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:24「  python3 .claude/tools/apply_audit_fix.py --selftest」
状態: 確定

#### 修正 32
対象のファイル: .claude/tools/gen_acceptance.py
直す箇所: 796-796
直す前の文字:
~~~
        raise SystemExit("[gen_acceptance] 元データの「実装の指示」が一覧（[]）の形ではありません（fail-closed）。")
~~~
足す文字:
~~~

    if any(not isinstance(it, dict) for it in (d.get("実装の指示") or [])):
        raise SystemExit("[gen_acceptance] 元データの「実装の指示」の中に、1件ずつの形（{…}）でないものが在ります（fail-closed）。")
~~~
根拠の抜き書き: .claude/tools/gen_acceptance.py:605「        L.append(f"#### 実装 {it.get('番号')}")」
状態: 確定

#### 修正 33
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 230-230
直す前の文字:
~~~
  "決めてほしいこと": [],
~~~
直した後の文字:
~~~
  "決めてほしいこと": [
    {"中身": "当てない相手の一覧（`NEVER_WRITE`）に、審判・期間の正本・発注のスイッチ・恒久の決まりを足すか。いま止まらないもの＝`scripts/priority_rebuild/score.py`・`scripts/priority_rebuild/eval_engine.py`・`scripts/priority_rebuild/periods.py`・`runner/run_once_v9.py`・`config/cat_params_v9.json`・`.claude/rules/permanent_rules.md`（監査 CP41 が挙げた8件のうち、足されたのは settings の2件だけ）", "私の案": "足さない。設計書の道は TARGET・NEW_FILE で縛られ、監査結果の道は まこさんが重さと番号を選ぶため。足すと決まったら、一覧に6件を加える直しを私が Write ツールで当てる", "出どころ": "監査 CP41 の A1-a・監査 CP42 の A4-a"}
  ],
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-09-24_impl_instruction_design_cp41_audit_report.md:83「**当てない相手の一覧で止まらないものの実測（8件）**＝`.claude/settings.json`（hook の登録 156件）」
状態: 確定

#### 修正 34
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 288-288
直す前の文字:
~~~
途中まで当たった状態が残ります。戻す仕組みは在りません（控えを取らず、番号の順に1本ずつ書くため）
~~~
直した後の文字:
~~~
途中まで当たった状態が残ります。戻す仕組みは在りません（全件を中身の上で当ててから、ファイルごとに1本ずつ書くので、書き終えたファイルと、まだ書いていないファイルに分かれます。1本の中は、一時のファイルに書いてから置き替えるので、途中で切れません）
~~~
根拠の抜き書き: .claude/tools/apply_audit_fix.py:491「            with open(path, "w", encoding="utf-8") as fh:」
状態: 確定

#### 修正 35
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は本物では走らせていない（本物の設計書を書き替えるため）。写しで同じ関数を走らせた＝2.59秒・rc=0。Minor まで当てる場合に、修正 26〜34 のあとに1回 打つ）「  "_作り方": "python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify",」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 36
対象のファイル: .claude/hooks/require_design_check_before_approval.py
直す箇所: 183-183
直す前の文字:
~~~
    return bad, exist, rb
~~~
足す文字:
~~~



def a10_cmd_cwd(md):
    """A10 完成の条件のコマンドが、承認のプログラムの作業場所（SDK）で開けるか（approve_impl.sh の _run＝cwd=SDK）。

    ★2026-09-24（監査 CP42 の B3・L-614）＝設計書 impl-instruction-apply-20260924 は、完成の条件のコマンドを
      直下からの相対で書いたので、承認②で条件のコマンドが rc=2 になり、行が済にならず、承認が1回 増えた。
      直下に在って SDK に無いパスを書いた行だけを止める（新しく作るファイルは止めない）。
    """
    m = re.search(r"<!-- ACCEPT_TABLE_START -->(.*?)<!-- ACCEPT_TABLE_END -->", md, re.S)
    bad = []
    for cmd in re.findall(r"`(python3 [^`]+)`", m.group(1) if m else ""):
        py = next((t for t in cmd.split()[1:] if t.endswith(".py")), "")
        if py and not py.startswith("/") and os.path.isfile(os.path.join(ROOT, py)) \
                and not os.path.isfile(os.path.join(SDK, py)):
            bad.append(f"A10 完成の条件のコマンド `{cmd}` の {py} は直下からの相対＝承認のプログラムは"
                       "SDK を作業場所にして走らせるので開けず rc=2 になり、行が済にならない（L-614）")
    return bad
~~~
根拠の抜き書き: .claude/hooks/approve_impl.sh:472「        r = subprocess.run(shlex.split(cmd), cwd=SDK, capture_output=True,」
状態: 確定

#### 修正 37
対象のファイル: .claude/hooks/require_design_check_before_approval.py
直す箇所: 288-288
直す前の文字:
~~~
    bad += a7_parse_only(acc)
~~~
足す文字:
~~~

    bad += a10_cmd_cwd(md)
~~~
根拠の抜き書き: .claude/state/session_worklog_20260924.md:318「- **原因（実物で確かめた）**＝承認のプログラムは条件のコマンドを SDK を作業場所にして走らせる」
状態: 確定

#### 修正 38
対象のファイル: .claude/hooks/require_design_check_before_approval.py
直す箇所: 27-27
直す前の文字:
~~~
#     A8 表に載っている既存の壊すプログラムの宣言を expect_of で読む（:401＝159番の STOP）
~~~
足す文字:
~~~

#     A10 完成の条件のコマンドが、SDK を作業場所にしても開けるか（:472 の _run＝cwd=SDK・L-614）
~~~
根拠の抜き書き: .claude/hooks/require_design_check_before_approval.py:27「#     A8 表に載っている既存の壊すプログラムの宣言を expect_of で読む（:401＝159番の STOP）」
状態: 確定

#### 修正 39
対象のファイル: .claude/hooks/require_design_check_before_approval.py
直す箇所: 183-183
直す前の文字:
~~~
    return bad, exist, rb
~~~
足す文字:
~~~



def a9_contract_full(acc):
    """A9 設計↔実装ゲートと同じ照合A〜D（verify_design_contract.py <設計書>）が通るか。

    ★2026-09-24（監査 CP42 の B3）＝承認のプログラムとこの検査は、照合A〜D を1回も走らせていなかった。
      設計書 impl-instruction-apply-20260924 は承認③まで通ったのに照合C（selftest の must_use）が落ち、
      CC はその道具を直下からの --selftest 以外で走らせられない状態になった（ゲートが止める）。
    ★実装の前の承認では照合が落ちるのが当たり前なので、TARGET に git の差分が在るとき（実装の途中・後）だけ見る。
      呼ぶ関数がまだ無いときの落ち方（配線が無い・関数が無い）も、実装の前として見ない。
    """
    md = open(acc, encoding="utf-8").read()
    targets = [x.strip() for t in re.findall(r"^TARGET:\s*(.+)$", md, re.M) for x in t.split(",") if x.strip()]
    changed = False
    for t in targets:
        for base in (ROOT, SDK):
            pth = os.path.join(base, t)
            if os.path.exists(pth):
                rc_g, _o = _run(["git", "diff", "--quiet", "HEAD", "--", pth])
                changed = changed or rc_g == 1
    if not changed:
        return []
    vdc = SDK + "/scripts/priority_rebuild/verify_design_contract.py"
    try:
        r = subprocess.run(["python3", vdc, acc], capture_output=True, text=True, timeout=90, cwd=SDK)
    except Exception as e:                                   # noqa: BLE001
        return [f"A9 照合の道具を走らせられません（{e}）"]
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode == 0 or "自己チェック配線が無い" in out or "実装にその関数が無い" in out:
        return []
    return [f"A9 照合A〜D（設計↔実装ゲートが .py を走らせる前に掛けるもの）が rc={r.returncode}"
            f"＝承認しても、CC はその .py を走らせられない:\n{_tail(out, 20)}"]
~~~
根拠の抜き書き: .claude/hooks/approve_impl.sh:360「CHK=$(python3 "$VERIFY_TOOL_PY" --check-approval "$LIST" 2>&1)」
状態: 未決

#### 修正 40
対象のファイル: .claude/hooks/require_design_check_before_approval.py
直す箇所: 288-288
直す前の文字:
~~~
    bad += a7_parse_only(acc)
~~~
足す文字:
~~~

    bad += a9_contract_full(acc)
~~~
根拠の抜き書き: .claude/hooks/require_design_contract_before_run.sh:303「    impl = os.path.basename(str(c.get('impl_file', '')))」
状態: 未決


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 開いたファイル（着手前必読15件＋追加）

| # | ファイル | 範囲 |
|---|---|---|
| 0 | 依頼書 | 全文 428行 |
| 1 | `.claude/state/acceptance.md` | 全文 672行 |
| 2 | `SDK/.claude/ratchet/acceptance_src.json` | 全文 318行 |
| 3 | `.claude/tools/apply_audit_fix.py` | 全文 695行 |
| 4 | `.claude/tools/gen_acceptance.py` | 100-130・580-630・700-800・1083-1182・1205-1264・1357-1377 |
| 5 | `.claude/breaks/b101_design_apply_no_approval.sh`・`b102_design_apply_no_precheck.sh`（各28行）・`lib.sh`（101行） | 全文 |
| 6 | `git diff 360c3e7 d691721 -- apply_audit_fix.py gen_acceptance.py .claude/breaks/`・`git diff -U0 5545cad d691721` | 全差分 |
| 7 | `.claude/tools/gen_audit_docs.py` | 162-184・596-780（item_fields 685〜・item_errors 715〜）・780-816 |
| 8 | `SDK/.claude/audits/inputs/_template.md` | 225-294 |
| 9 | `.claude/hooks/approve_impl.sh` | 40-70・336-410・455-480・530-560 |
| 10 | `SDK/scripts/priority_rebuild/verify_design_contract.py` | 870-915・1285-1300・1331-1400・1760-1825 |
| 11 | `SDK/.claude/audits/2026-09-24_impl_instruction_design_cp41_audit_report.md` | 全文 709行 |
| 12 | `SDK/.claude/rules/cat_requirements.md` の H13・H16 | 660-668・702-712（ほかは自動読み込みで全文） |
| 13 | `SDK/.claude/ratchet/engine_tuner_requirements.md` | 38-59 |
| 14 | `.claude/rules/permanent_rules.md` の 64・69・71・72番 | 348・377・381-410 |
| 15 | `.claude/state/session_worklog_20260924.md` の §5〜§7 | 118-348 |
| +1 | `.claude/hooks/require_design_contract_before_run.sh` | 30-50・280-410 |
| +2 | `.claude/hooks/require_acceptance_before_impl.sh` | 1180-1205 |
| +3 | `.claude/hooks/require_design_check_before_approval.py` | 1-100・166-300 |
| +4 | `.claude/hooks/approve_design.sh` | 1-40 |
| +5 | `.claude/tools/run_breaks.py` | 198-242・595-619 |
| +6 | `.claude/tools/pre_audit_check.py` | 370-477 |
| +7 | `SDK/.claude/ratchet/acceptance_archive/impl-instruction-apply-20260924.frozen.json`・`.breaks.json` | 全文 |
| +8 | CC の前のセッションの一時の置き場の `apply_impl_edits.py` | 1-23 と、8か所の見出しの行 |
| +9 | `cp42_work` の `run.sh`・`manifest.json`・`mirror_edit.py`・`cp42_result.md`（骨組み） | 全文 |

### 走らせたコマンドと結果と秒数

| # | コマンド | rc | 秒 | 結果の要所 |
|---|---|---|---|---|
| 1 | `shasum -a 256`（相手と関係するファイル）・`git log`・`git status --short`（開始） | 0 | 0.1 | 依頼書の値と一致 |
| 2 | 直下から `python3 .claude/tools/apply_audit_fix.py --selftest` | 0 | 0.15 | 12/12 pass |
| 3 | 直下から `python3 .claude/tools/gen_acceptance.py --selftest` | 0 | 2.74 | 9/9 pass（T3 が本物の元データを一時的に書いて戻す） |
| 4 | SDK の中から `verify_design_contract.py --diff <設計書>` | 0 | 0.13 | 齟齬: 0件 |
| 5 | SDK の中から `verify_design_contract.py <設計書>` | 1 | 0.46 | [FAIL] C selftest |
| 6 | SDK の中から `verify_design_contract.py --check-approval <設計書>` | 0 | 0.11 | 設計書の承認: 一致 |
| 7 | 直下から `python3 .claude/tools/gen_acceptance.py --verify` | 0 | 取らなかった | 全部 ✅・IMPL は照らさない |
| 8 | 写し `run.sh aaf --selftest` | 0 | 0.18 | 12/12 |
| 9 | 写し `run.sh break b101_design_apply_no_approval` | 1 | 0.30 | 10/12・T4・T11 |
| 10 | 写し `run.sh break b102_design_apply_no_precheck` | 1 | 0.30 | 11/12・T7・`x = 9` |
| 11 | 写しで `if hard:` を常に偽にして `--selftest` | 0 | — | 12/12 pass（止めを外しても落ちない） |
| 12 | 写しの見本を当てる試し（欄の取り違え・根拠の取り違え・`# ` の行・案・走らせるコマンド・`SDK/`・`./`） | — | 0.15 | 3節と4節の実測 |
| 13 | 写しの見本を当てる試し（--dry と本番・消す文字・書き込みの失敗・印が無い・1文字足した設計書・控え3本・既定の設計書） | — | 0.13 | 同上 |
| 14 | 写しで止めを外し、2本のファイルに当てる | 1 | — | 1本目だけ当たった |
| 15 | 写しの元データに実装の指示を入れ、write・verify・往復・型の検査（終わったら戻す） | — | 2.59 | B1・A3-c の実測 |
| 16 | 写しで T6 の出力を出させる／`--only 7` で当てる（終わったら戻す） | 1／0 | — | 修正 8 が0か所／修正 7 の行が2つ |
| 17 | 写し `run.sh acc --verify` | 1 | 0.52 | SPEC だけ ❌（写しの根の1行のため・判定に使わない） |
| 18 | 写し `run.sh tool run_breaks --lint-expect` | 1 | — | b88_r2_exempt.sh |
| 19 | 写しに修正 1〜3・12〜15・26〜31 を当てて `--selftest` | 0 | — | 16/16 pass |
| 20 | 直した写しで b101／直した b102 | 1／1 | — | 14/16（T4・T11）／14/16（T13・T16） |
| 21 | 直した写しで 修正 1・修正 2 を1つずつ戻す | 1／1 | — | T15 だけ落ちる／T14 だけ落ちる |
| 22 | 直した写しで試し12・13の場面をもう一度 | — | — | 全部 止まるか、正しく当たる |
| 23 | 写しの gen_acceptance に修正 32 を当てて型の試しと `--selftest` | 0 | 3.08 | 止まる・9/9 |
| 24 | 修正 36・39 の関数を、いまの設計書と控え .02 に掛ける（読むだけ） | — | — | a9＝1件（照合C）／a10＝いま0件・控え .02 で4件 |
| 25 | 直す前の文字の数え（写しの pyedit と grep -c -F） | — | — | 全40件の直す前の文字が、それぞれ1か所 |
| 26 | `run.sh restore-all`・`run.sh hash …`・本物の `shasum`・`git status --short`（終了） | 0 | — | 写しは pristine と same・本物は開始時と同じ |

### 走らせられなかったものと理由

| # | 走らせられなかったもの | 理由 |
|---|---|---|
| 1 | `bash .claude/hooks/approve_impl.sh` | 依頼書の禁止（承認のプログラムを走らせない） |
| 2 | 本物の b101・b102 | 本物の道具を書き替えるため（写しで走らせた） |
| 3 | SDK の中から `python3 ../../.claude/tools/apply_audit_fix.py --selftest` | 設計↔実装ゲートが止めた（照合C）＝B3 の Critical の証拠 |
| 4 | 本物の `--design --dry`・`--report … --dry` | 同じくゲートが止めた |
| 5 | 本物の `run_breaks.py --lint-expect` | 土台ゲートが止めた（写しの入口で走らせた） |
| 6 | 写しの `--report` に結果ファイルのパスを渡す形 | hook 11 が止めた（写しの自己テストの T6 に出力を出させて代えた） |
| 7 | `pre_audit_check.py --check-design` | 中で hook を実物の入力の形で呼び、hook が本物の記録に書く作りのため（本物を書き替えない決まり） |
| 8 | 本物の `gen_acceptance.py --write` | 本物の設計書を書き替えるため（写しで同じ関数を走らせた） |
| 9 | 直す前の版の自己テスト（4/12・11/12） | その版が commit されていない |
| 10 | 外部検索 | 依頼書の指定（しなかった） |

### 取りまとめ側（この監査のセッションの本体の CC）が確かめたこと

監査役（Plan エージェント・cold start・1回だけ起動）の所見を、この結果に写した。そのあと本体の CC が次を確かめた。所見の中身（重さ・結論・修正の文）は変えていない。変えたのは4行目の3件の語順だけ。

| # | 何を確かめたか | コマンド | 結果 |
|---|---|---|---|
| 1 | 所見に書いた「ファイル名:行番号」を、本体でも全部 開いたか | Read と sed -n（17ファイル） | 逐語は全部 実物の行と合った |
| 2 | 修正40件の「直す前の文字」が本物の中でちょうど1か所か。根拠が本物の行と合うか | cp42_work の count_before.py（読むだけ） | 直す前の文字は、コマンドの3件を除く37件がどれも1か所。根拠は37件が合った。3件（修正 11・25・35）は形が読めなかった（4行目） |
| 3 | 依頼書との対応と、結果の形 | gen_audit_docs.py の check と form | どちらも食い違い0件 |
| 4 | 修正 11・25・35 の根拠の抜き書き | Edit（作業場の cp42_result.md だけ） | 頭に在った説明の文を、「ファイル名:行番号」の後ろの括弧へ移した（語は変えていない）。当てる道具の読み取りが「ファイル名:行番号」を正しく拾う形にするため。直した後は40件とも合った |
| 5 | 設計書の側の修正15件（7〜10・16〜24・33・34）が当たるか | 写しで run.sh aaf --report（--only で15件） | 15件とも当たった（0.13秒・rc=0）。当てた後の写しの元データから、run.sh acc --dry-run で設計書を作れた（1.09秒・rc=0・690行）。写しの元データは run.sh restore src で戻した |
| 6 | 道具の側の修正17件（1〜6・12〜15・26〜32）を写しに当てた後の動き | cp42_work の apply_to_mirror.py（写しの中だけに書く）→ run.sh aaf --selftest・run.sh break b101／b102・run.sh acc --selftest | 自己テスト 16/16 pass（0.19秒）。b101＝14/16（T4・T11 が落ちる）。直した b102＝14/16（T13・T16 が落ちる）。設計書を作る道具の自己テスト 9/9 |
| 7 | いまの実装が、本当に守りを外しているか | 写しを戻し、修正 3（場面 T13〜T16）だけを当てて run.sh aaf --selftest | 14/16。T14（未決の件が当たった・rc=0）と T15（「./」の書き方で当たった・rc=0）が落ちた |
| 8 | 全件を先に確かめる止め（apply_audit_fix.py:456）を外しても、いまの自己テストが落ちないか | 写しを戻し、run.sh patch で `if hard:` を `if False:` にして run.sh aaf --selftest | 12/12 pass（落ちない） |
| 9 | 設計↔実装ゲートと同じ照合 | SDK の中から verify_design_contract.py <設計書>（読むだけ） | rc=1・0.47秒・「[FAIL] C selftest: 設計書が要求する名前が中身に無い → ['read_design_fixes', 'approved_ok']」 |

★写しの作業場（cp42_work の setup_mirror.py・run.sh・mirror_edit.py・mirror・pristine・manifest.json）は、本体の CC が監査役を起こす前に作った。手本は cp36_work の setup_mirror.py。写しの中の hooks は、本物の hooks への読み取りのリンクにしてある。そこで、監査役の作業の後に、本物の .claude/hooks に新しいファイルが無いことを find で確かめた（0件）。写しは最後に run.sh restore-all で全部 元に戻した。

## 11. 本物のファイルを書き替えていないこと

```
$ git status --short
 M .claude/state/next_step.md
 M .claude/state/next_step_archive_202608.md
 M .claude/state/next_step_src.json
 M .claude/state/session_worklog_20260924.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
?? .claude/hooks/require_chat_draft_before_long_reply.sh
?? .claude/settings.json.bak_20260819
?? .claude/settings.json.bak_20260826
?? .claude/settings.json.bak_20260902_implock
?? .claude/settings.json.bak_20260903_a6
?? .claude/settings.json.bak_m2_2_2b
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror_old/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/pristine/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp39_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp40_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/cp42_result.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/manifest.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/mirror/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/mirror_edit.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/pristine/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/run.sh
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/setup_mirror.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

**監査の開始時の `git status --short` と1行も違わない。**監査の相手の sha256 は、開始時と終了時で同じ（apply_audit_fix.py 9367982a…・acceptance.md 8fcd0a13…・acceptance_src.json 559bd0ec…）。写しは全部 pristine と同じに戻した（`run.sh restore-all`＝9件とも ✅・`run.sh hash` で same）。`.claude/state` の下に自己テストと監査の一時の置き場は残っていない（0件）。★正直に書くこと＝本物の `gen_acceptance.py --selftest`（呼び出し元が走らせてよいとした）は、T3 で本物の `acceptance_src.json` を一時的に書き替えて戻す作り。中身は同じ（sha256 559bd0ec… のまま・git にも差分なし）で、更新時刻だけが 22:46:22 に変わった。

**取りまとめ側の追記。**本体の CC が作業を始めたとき（作業場を作る前）の `git status --short` は23行で、上の一覧から cp42_work の7行を除いたものと同じだった。いまとの違いは、作業場 cp42_work の中のファイルだけ（この結果の写し・写しの一式・確かめのプログラム count_before.py・apply_to_mirror.py・list_cites.py・設計書の試しの出力 dryrun_after_design_fixes.md）。これに、この結果ファイル1本が加わる。★この結果ファイルを書いた後の `git status --short` は、メインセッションへの戻り報告に貼る。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-24_impl_instruction_apply_impl_cp42_audit_request.md request_sha256=1a02f04f71d5869c5efe2dfb01e5e2bd1484486143132acdbee4040e605b4bf4 -->
