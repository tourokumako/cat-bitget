# 監査結果 cp57 — CP57 — 段の候補を作る側と測る側の不具合6つを直し、渡す本数を10本にする（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_request.md`
- 依頼書のハッシュ値: 78dae5fae2de27ed59fddd84682182992e32a1ea6bc248f5f2f719578e3c3202
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 cbfd521a0b8f294749bddb4e85f9f97d1d6b1279b368c107e6122e220aaaf853
- 監査が照らしたハッシュ値: cbfd521a0b8f294749bddb4e85f9f97d1d6b1279b368c107e6122e220aaaf853（依頼書の値と一致）
  - 承認の印 `.claude/state/acceptance.approved:1`「cbfd521a0b8f294749bddb4e85f9f97d1d6b1279b368c107e6122e220aaaf853」と同じ値です。
  - 控え `acceptance_archive/m2f-label-builder-stages-20261001.md` とも、`cmp` でバイト単位まで同じです。
  - 依頼書は 452行で、sha256 は上の値と一致しました。
  - 版の確かめ（git log）＝bf238d5 の親は e31d6e8 です（`git show -s --format='%H %P'`）。いまの HEAD は ab73155 で、bf238d5 より新しい版です。対象の3ファイルは、bf238d5・HEAD・作業ツリーの3つで同じでした（`git diff --stat bf238d5 HEAD` と `git diff --stat HEAD` の出力は0行）。
- 実施日: 2026-10-01（`date` の結果 2026-10-01 21:52:55）


## 2. 監査対象の型宣言

次の3つの型が全部 当たります。

- **コード型**: engine_tuner_gen.py と regime_r9_diag.py の差分。
- **数値型**: search_limits.json の hi=10、自己テストの終了コード、かかった秒数。
- **文書型**: 設計書 4-20 と控え2本、applied_fixes.json の記録、やることの表、逐語のファイル。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

依頼書の表と実物は全部 一致しました（23行）。

- 照らした実物は `.claude/state/acceptance.md:317-861` です（「#### 実装 N」の見出しと各欄）。
- 番号・対象のファイル・直す箇所・種類が一致しています。種類が「足す文字」なのは 4・5・9・10・11・14 で、残りは「直した後の文字」です。
- まこさんが OK した案の JSON を `jq` で設計書と同じ形に組み直し、`acceptance.md:317-861` と diff を取りました。差は0件です（対象＝`okd_stages_20261001.txt:96-327`・23件・番号は [1..23]）。

### 当てた記録（applied_fixes.json の名前 design:m2f-label-builder-stages-20261001）

依頼書の表と実物は全部 一致しました（23行）。

- 照らした実物は `SDK/.claude/audits/applied_fixes.json:1012-1172` です。
- num は 1〜23 です。file は 1〜11 が engine_tuner_gen.py、12〜22 が regime_r9_diag.py、23 が search_limits.json です。
- how は23件とも「当てた」、at は23件とも「2026-10-01T17:54:40」です。
- 名前の出現は `grep -c` で 23 件でした。この23行は bf238d5 で足されたもので、+161行＝23件×7行です。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**YES**

確かめ方（写しは作らず、読むだけの道具で照らしました）:

- （1）各指示の「直す前の文字」が、e31d6e8 のファイルにちょうど1か所在るかを数えました（`git show e31d6e8:<パス> | grep -n -F -e "<設計書の行>"`）。結果は23件とも1か所でした。複数行の 16（実装の前 550-554）と 17（実装の前 565-576）は、`diff <(sed -n '691,695p' acceptance.md) <(git show e31d6e8:… | sed -n '550,554p')` で差0でした。
- （2）各指示の「直した後の文字」「足す文字」を、bf238d5 の行の範囲と比べました（`diff <(sed -n 'X,Yp' acceptance.md) <(git show bf238d5:… | sed -n 'A,Bp')`）。結果は23件とも SAME（差0）でした。
- （3）`git diff -U0 e31d6e8 bf238d5` の差分のまとまり（engine_tuner_gen.py 11個・regime_r9_diag.py 11個・search_limits.json 1個）は、23件の指示と1対1に当たりました。

照らした位置（実装の前の行 → 実装の後の行）:

| 指示 | 実装の前の行 | 実装の後の行 |
|---|---|---|
| 1 | 3165 | 3177-3179 |
| 2 | 3154 | 3165-3166 |
| 3 | 3349 | 3363-3366 |
| 4 | 2879 | 2881 ＋ 2882 |
| 5 | 2940 | 2943 ＋ 2944-2951 |
| 6 | 2538 | 2538-2540 |
| 7 | 2541 | 2543 |
| 8 | 5026 | 5043-5096 |
| 9 | 7739 | 7809 ＋ 7810-7813 |
| 10 | 7928 | 8002 ＋ 8003-8005 |
| 11 | 7929 | 8006 ＋ 8007-8013 |
| 12 | 354 | 354-357 |
| 13 | 409 | 412-458 |
| 14 | 419 | 468 ＋ 469-470 |
| 15 | 535 | 586 |
| 16 | 550-554 | 601-607 |
| 17 | 565-576 | 618-619 |
| 18 | 580 | 623-624 |
| 19 | 583 | 627 |
| 20 | 586 | 630-632 |
| 21 | 589 | 635 |
| 22 | 787 | 833-856 |
| 23 | search_limits.json:50 | search_limits.json:50 |

- 各指示の根拠の抜き書きにある行番号（3164・3154・3349・2879・2940・2538・2541・5026・7739・7928・7929・354・409・419・535・549・787・50）は、全部 e31d6e8 の実物の行と合いました。
- 番号の順に当てても結果は変わりません。前の指示が足す文字の中に、後の指示の「直す前の文字」は在りません。実装の後のファイルで「直す前の文字」を数えると、足す種類の指示では1、直す種類の指示では0でした。

修正の番号＝なし

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**YES（在りません・0行）**

- `git diff --numstat e31d6e8 bf238d5` の結果:
  - engine_tuner_gen.py は +89/−5 です（8367行 → 8451行）。
  - regime_r9_diag.py は +90/−21 です（921行 → 990行）。
  - search_limits.json は +1/−1 です。
- この行数は23件の指示の足し引きと一致しました。
  - engine_tuner_gen.py: 足す行＝3+1+1+8+2+3+4+53+4+3+7＝89、消す行＝5。
  - regime_r9_diag.py: 足す行＝4+46+2+1+7+2+1+1+2+1+23＝90、消す行＝1+1+5+12+1+1＝21。
- 差分のまとまり23個は、全部 Q1 の表の指示に当たりました。
- 乱数については、差分の足した行に random・rng・seed・shuffle・choice( が0件でした。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**YES**

- 記録は23件で、指示の番号と対象のファイルが全部 1対1に合いました（`applied_fixes.json:1012-1172`）。
- 「もう当て終わっていた」は0件、記録が無い指示は0件です。
- 時刻 17:54:40 は、対象3ファイルの更新時刻（`ls -la` で Oct 1 17:54）と、承認（worklog `session_worklog_20261001.md:201`「承認（17:54）→ 当てる道具が23件を当てた（applied_fixes.json に23行）」）と合います。

修正の番号＝なし

### Q7 — まこさんの要望（逐語）を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**NO（満たしていない要望が1件在ります＝req_m2_20261001:V02）**

| 要望 | 判定 | 根拠 |
|---|---|---|
| req_14b_20260928:V01「直す範囲は全部」 | 満たす | この発言が答えた CC の問いは「直す範囲（Major まで／Minor まで／全部）」でした。CC は監査 CP49 の修正5（段1 の下側）と修正7（段2c の「なし」）を M2-F-13b に回していました（記録 d9852551…jsonl:239 の直前の CC の文「\| 2 \| 修正5・6＝段1 で帯の下側も測るか \| **測る。直すのは M2-F-13b** \|」）。その中身は実装されています。B-3＝regime_r9_diag.py:412-425・469-470。B-4＝regime_r9_diag.py:427-457・586・601-607・618-619・623-635。 |
| req_14b_20260928:V02「決めることはCCのおすすめでOK」 | 満たす | CC の案「測る」「入れ直す」のとおりに実装されています（上の行）。決めてほしいことは acceptance.md:207 で「無し」です。 |
| req_14b_20260928:V03「ではその不具合は修正して、ミッション達成できるようにしてほしい」 | 満たす（その不具合の修正の部分） | 「その不具合」は、直前の CC の文の「同じ束が名簿に約3回ずつ並ぶ」と「名簿の並び順が「強さ」ではない」です（記録 d9852551…jsonl:1423 の直前）。直した行は engine_tuner_gen.py:2882・2944-2951（B-5）と 2538-2540・2543（B-6）です。T48 は「ダメだった件 0」でした。ミッションが達成できるかは、段の走行（M2-F-8〜15）が工事の外なので、この監査では測れません（データ不足：理由＝acceptance.md:200 で走行を工事に入れないため）。 |
| req_k1_20260918:V02「→とりあえず１０本にする」 | 満たす | search_limits.json:50「"stage_keep_range": { "lo": 1, "hi": 10, "kind": "int" },」。jq の出力も 10 です。 |
| req_k1_20260918:V03「結果を見て変更すると思う」 | 満たす | 10 は設定の1行にだけ在ります。コードの中の 10 は自己テストの見本 engine_tuner_gen.py:5068 の1か所だけです。走るときは stage_keep_of が設定を読みます（regime_r9_diag.py:489・561）。 |
| req_m27_20260928:V04「了解。状況は理解した。」 | 満たす（実装を求める文ではない） | 受け取りの返事です。 |
| req_m27_20260928:V05「M2-F-7 の進め方はCCの案でOK」 | 満たす | CC の案は「組む側の直しの後に hi=10 を書く・同じ回・H2 の印の取り直しは1回」でした（m2_todo.json:1207）。指示 1 と 23 は同じ時刻 17:54:40 に当たっています。H2 の印は 19:12:55 に書かれ、いまのコードと一致します（`enforce_h2_pass.py --check-fingerprint`→「印と、いまのコードが一致」）。 |
| req_m2_20261001:V01「じゃあ、milestone２の残りを早く進めてくれ。」 | 満たす（この工事の分） | M2-F-13b と M2-F-7 の実装は入っています。m2_todo.json:1176・1195 の状態が「まだ」なのは、監査の結果を当ててから済にする運用です（next_step.md:116）。 |
| **req_m2_20261001:V02「やってるふりじゃなく、ちゃんと完成しろ」** | **満たさない** | 組む側の自己テストの全体 `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` が、実装の後に**終了コード 1**（361秒）で落ちます。出力の最後の行は「  ❌ T35③: 範囲の外（hi > 本数）で止まらない」です。原因は、B-1（指示1）で止めなくなった動きを、既存の T35③ が「止まる」と求めたまま残っていることです（足りない実装の行＝engine_tuner_gen.py:7017-7018「({"lo": 1, "hi": _n35 + 1}, "hi > 本数")):」と 7021、説明の 6991・7025）。設計書は「承認の後に --selftest を直接 走らせて貼る」（acceptance.md:931）、「T48 と既存の T24・T39〜T47 を走らせて…確かめる」（acceptance.md:932）と約束していました。しかし作業記録が残しているのは短い口だけです（session_worklog_20261001.md:204「自己テスト＝engine_tuner_gen.py --selftest-stages（T48・ダメだった件0）／regime_r9_diag.py --selftest（全部 pass…）」）。さらに、壊すプログラム b91（.claude/breaks/b91_keep_range_ignored.sh:4「# EXPECT_MSG: ❌ T35」）は、壊さない状態の出力でも「❌ T35③」が出るので、壊した所を捉えたかどうかを見分けられなくなりました。 |
| req_split_20261001:V01「なんだそれ。」 | 満たす（実装を求める文ではない） | 反応の言葉です。 |
| req_split_20261001:V02「じゃあ修正せずに、分けてすすめれば」 | 満たす | 14a は別の工事に分けてあります（acceptance.md:198、やることの表.md:3）。対象3ファイルの差分に札の構造の行は0行です。設計書を作る道具 gen_acceptance.py は bf238d5 で変更されていません（`git show --stat bf238d5` に無い）。 |

修正の番号＝1・5

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**YES**

- `diff <(sed -n '/ACC_IMPL_START/,/ACC_IMPL_END/p' .01.md) <(同 .md)` の差は0です（どちらも549行）。
- いまの acceptance.md と控え .md は、`cmp` でバイト単位まで同じです。
- .01.md の sha256 は 93918f98…c0c5b で、`m2f-label-builder-stages-20261001.01.sha.txt` と一致します。
- 2つの控えの違いは ACC_IMPL の外だけです（2-1 の測った結果・ACC_CODEREF・ACC_SPEC）。当てた版（17:54 の承認の版＝.01）といまの版で実装の指示は同じなので、実装への影響は0です。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**NO（要件に要る直しが1件、実装の指示に無い）**

やることの表の各項目と指示の対応:

| 要件 | 当たる指示 |
|---|---|
| B-1 | 1・2 |
| B-2 | 3・12 |
| B-3 | 13・14 |
| B-4 | 13・15〜21 |
| B-5 | 4・5 |
| B-6 | 6・7 |
| K-1 | 23 |
| 各確かめ方 | 8〜11（T48）・22（⑭⑮⑯） |

- **要件に在るのに実装の指示に無いもの（Critical）**: やることの表.md:45 の B-1「止めず、候補の本数を使う（下端の検査と、上端が下端より小さいときの検査は残す）」は、既存の T35③ と逆の動きです。T35③ は engine_tuner_gen.py:7017-7021 で、3通り目の「hi > 本数」に SampleError を求めています。23件の指示に T35③ の直しが無いため、組む側の番人（--selftest の全体）が B-1 と食い違ったまま残りました。実測は rc=1・361秒です。直す前は止まっていたので T35③ は通っていました（e31d6e8:engine_tuner_gen.py:3164-3165「if hi > int(n_cands):」「raise SampleError(f"stage_keep_range の上端が候補の本数を超える: …")」）。
- **実装の指示に在るのに要件に無いもの**: 旗 --selftest-stages（指示10・11）は、やることの表の一覧には在りません。ただし、まこさんが OK した案の【4-9】（okd_stages_20261001.txt:61）と【5】の7番（同:339）に在るので、承認の外の変更ではありません。
- **事実として満たされている点**: K-1 の確かめ方「leak_causality_diag.py が全部 pass」（やることの表.md:109）は完成の条件（7-6）に入っていません。それでも実物は満たしています。h2_pass.json の when は 2026-10-01 19:12:55 で、`--check-fingerprint` は一致を返しました（対象22件に engine_tuner_gen.py・search_limits.json が入る）。G2 も 19:08:07 で一致しています（対象38件）。M2-F-13b の触るファイルにある stage_counts は直していませんが、stage_counts は stage_keep_of を呼ぶだけなので（engine_tuner_gen.py:3249）、B-1 で止まらなくなっています。
- **Minor（古い説明）**: search_limits.json:51 `_stage_keep_range_note` が「上端 null は…」の説明のまま残り、10 が まこさんの決定であることも B-1 も書かれていません。CC も next_step §6 の239番に登録済みです。修正は なし（直した後の文をどうするかは、この監査の争点の外です）。

修正の番号＝1・2・3

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**YES（3行とも成り立つ）**

SDK のフォルダで走らせました。-B は、バイトコード（.pyc）を書かないために付けた旗で、判定の中身は変わりません。

| # | コマンド | 結果 | 秒数 |
|---|---|---|---|
| 1 | `python3 -B scripts/priority_rebuild/engine_tuner_gen.py --selftest-stages` | 「  ✅ T48 段の不具合の直し／ダメだった件 0」・rc=0 | 6秒 |
| 2 | `python3 -B scripts/priority_rebuild/regime_r9_diag.py --selftest` | 「  ✅ 全部 pass」・rc=0 | 3秒 |
| 3 | `jq '.stage_keep_range.hi' scripts/priority_rebuild/recipes/search_limits.json` | `10`・rc=0 | 0秒 |

- 自己テストが3行の中身を本当に見ているかを、コードで確かめました。
  - 1行目（T48）: 直す前のコードなら、B-1 は SampleError で「途中で止まった」になり、B-6 は label が None で落ち、B-2 は q49 < q50 で落ちます。B-2 の比べ方は engine_tuner_gen.py:5085-5089 で、off.any の3番目が off_c であることは sample_regime_build の 3398 行の並び（[_flip_loose(A), _flip_loose(B), off_c]）と合います。
  - 2行目の ⑭⑮⑯ は regime_r9_diag.py:833-855 にあり、早く抜ける道はありません。
- **Minor**: 2行目のまとめの表示（regime_r9_diag.py:860-861）には ⑭⑮⑯ が出ません。画面の出力だけでは3つを走らせた証拠になりません。
- **完成の条件では見つからない問題**: 完成の条件に全体の --selftest が入っていないため、T35③ の落ち（Q5・Q7）は3行では見つかりません。

修正の番号＝4


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

**事実と合っています。** `diff .01.md .md` の結果:

- 囲みの外（2-1 の表）は 87-89 行の3行が置き換わり、6行です。
- ACC_CODEREF は 1043・1050・1053 行が置き換わり、6行です。
- ACC_SPEC は 1060 行の置き換え（2行）と、足した11行（1328-1336・1380・1417）で、13行です。
- ACC_IMPL の差は0です。

実装の指示は変わっていないので、実装への影響はありません。

### 自己申告 2

**挙げた3本については合っていますが、一覧は全部ではありません。**

- 挙げた3本は bf238d5 に入っておらず、この工事の対象でもありません。
  - `.claude/hooks/require_chat_draft_before_long_reply.sh`（未追跡・2026-09-19 更新）
  - `.claude/hooks/require_request_understood.sh`（未追跡・2026-09-29 更新）
  - `e38_logics.backup_20260802_005140.json`（未追跡・2026-07-27 更新）
- 一覧から抜けているもの: 追跡されている変更 ` M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md`（+52/−53・21:05:06 更新＝依頼書を作った 21:29:41 より前）。このほか未追跡のログ・results/・他の工事の控えなどが在ります（`git status --short` は211行）。
- どれも対象3ファイルではありません。対象3ファイルは bf238d5・HEAD・作業ツリーで同じなので、Q1・Q2 の答えは変わりません。
- 一覧の抜けは Minor とし、修正は なしです（一覧を作るのは依頼書の道具で、道具の直しは守りの穴探しにあたり、この監査の範囲の外です）。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ NO（根拠＝Q1・Q2・Q3・Q4・Q6 は YES で、設計書のとおりに1文字も違わずに当たり、設計書に無い変更は0行。ただし Q5 が NO＝B-1 の要件と食い違う既存の自己テスト T35③（engine_tuner_gen.py:7017-7021）を直す指示が23件に無く、組む側の --selftest の全体が rc=1（361秒・「❌ T35③: 範囲の外（hi > 本数）で止まらない」）になった）
- 問い2 ＝ NO（根拠＝req_m2_20261001:V02「やってるふりじゃなく、ちゃんと完成しろ」を満たしていない。組む側の番人が落ちたまま監査に出され、設計書が約束した「承認の後に --selftest を直接 走らせて貼る」（acceptance.md:931）は実行された記録が無い（session_worklog_20261001.md:204）。壊すプログラム b91 も見分けがつかなくなった。ほかの10行は満たす）

### 結論と件数

- 結論＝NO-GO
  - 理由＝問い1・問い2 がどちらも NO。
- Critical＝1（T35③ が B-1 と逆の動きを求めたまま＝全体の --selftest が rc=1・b91 が見分けられない）
- Major＝0
- Minor＝4（T35 の説明の2行／測る道具のまとめの表示に ⑭⑮⑯ が無い／search_limits.json:51 の説明が古い／自己申告2 の一覧の抜け）
- Process＝1（設計書 6-2 の2番・3番の「承認の後に --selftest の全体を走らせる」を行わずに監査へ出した）


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7017-7023
直す前の文字:
~~~
        for _bad35, _why35 in (({"lo": 0, "hi": None}, "lo 0"), ({"lo": 3, "hi": 2}, "lo > hi"),
                               ({"lo": 1, "hi": _n35 + 1}, "hi > 本数")):
            try:
                stage_keep_of({**_lm35, "stage_keep_range": _bad35}, _n35)
                ng.append(f"T35③: 範囲の外（{_why35}）で止まらない")
            except SampleError:
                pass
~~~
直した後の文字:
~~~
        for _bad35, _why35 in (({"lo": 0, "hi": None}, "lo 0"), ({"lo": 3, "hi": 2}, "lo > hi")):
            try:
                stage_keep_of({**_lm35, "stage_keep_range": _bad35}, _n35)
                ng.append(f"T35③: 範囲の外（{_why35}）で止まらない")
            except SampleError:
                pass
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-1・監査 cp57）＝上端が候補の本数を超えるときは、止めずに候補の本数を使う
        if stage_keep_of({**_lm35, "stage_keep_range": {"lo": 1, "hi": _n35 + 1}}, _n35) != _n35:
            ng.append(f"T35③: 上端が候補の本数（{_n35}）を超えるのに keep が候補の本数でない（B-1）")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/やることの表.md:45「| 中身 | engine_tuner_gen.py の stage_keep_of で、上端が候補の本数を超えるときに止めず、候補の本数を使う（下端の検査と、上端が下端より小さいときの検査は残す） |」
状態: 確定

### Major

なし

### Minor

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 6991
直す前の文字:
~~~
    #   ③範囲の外（lo 0／lo > hi／hi > 本数）は止まる（fail-closed）
~~~
直した後の文字:
~~~
    #   ③範囲の外（lo 0／lo > hi）は止まる（fail-closed）・上端が候補の本数を超えるときは候補の本数を使う（2026-10-01・B-1）
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/やることの表.md:45「| 中身 | engine_tuner_gen.py の stage_keep_of で、上端が候補の本数を超えるときに止めず、候補の本数を使う（下端の検査と、上端が下端より小さいときの検査は残す） |」
状態: 確定

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: 7025
直す前の文字:
~~~
              "『上位 1 本の外』で組めない／③範囲の外 3通りは止まる")
~~~
直した後の文字:
~~~
              "『上位 1 本の外』で組めない／③範囲の外 2通りは止まり、上端が候補の本数を超えるときは候補の本数")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/やることの表.md:45「| 中身 | engine_tuner_gen.py の stage_keep_of で、上端が候補の本数を超えるときに止めず、候補の本数を使う（下端の検査と、上端が下端より小さいときの検査は残す） |」
状態: 確定

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 861
直す前の文字:
~~~
／ ⑩並べる鍵は平均 ／ ⑪段の口の束（合成データ・関所で拒否の行）")
~~~
直した後の文字:
~~~
／ ⑩並べる鍵は平均 ／ ⑪段の口の束（合成データ・関所で拒否の行）／ ⑭段2a の出る線は緩い側 ／ ⑮段1 は上側と下側 ／ ⑯差し戻しの段2c の「なし」と足す側")
~~~
根拠の抜き書き: .claude/state/acceptance.md:1035「| 2 | 測る道具の出る線が緩い側（⑭）・段1 が上側と下側の両方の帯を測る（⑮）・差し戻しが段2c の「なし」と足す側を試す（⑯） | `python3 scripts/priority_rebuild/regime_r9_diag.py --selftest` | 実経路 | — | `—` | 要 | **未着手** |」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cd v3-bitget-api-sdk/bitget-python-sdk-api && python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest
~~~
根拠の抜き書き: .claude/state/acceptance.md:931「| 2 | 組む側の --selftest は全体で約6分23秒（b35 の注記の実測）。承認の打ち切り120秒より長い | 完成の条件の壊すプログラムは「—」にし、承認の後に --selftest を直接 走らせて貼る |」（監査が修正1 の前に走らせた結果＝361秒・終了コード 1・「  ❌ T35③: 範囲の外（hi > 本数）で止まらない」。修正1 を当てた後に走らせ、終了コード 0 を貼る）
状態: 確定


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 開いたファイル（Read で全文、または示した行）

- 依頼書（1-453 行の全文）。
- `.claude/state/acceptance.md`（1-1452 行の全文）。
- やることの表.md（1-145）、要件のまとめ.md（1-96）。
- 逐語のファイル ok_stages・ok_todo・req_14b・req_k1・req_m27・req_m2・req_split（全文）と、各 meta.json（全文）。
- okd_stages_20261001.txt（1-477 の全文）。
- m2_todo.json:1165-1214・2040-2079。
- applied_fixes.json:1000-1174。
- 控え .01.md と .md（diff による全行の比較）、.breaks.json・.dirty.json・.01.sha.txt・.01.diff.txt。
- engine_tuner_gen.py:629-648・2862-3158・3159-3258・6989-7030・7806-7821・7956-8030。
- regime_r9_diag.py:322-391・544-645・693-910。
- search_limits.json:47-51（git diff と sed）。
- `.claude/hooks/enforce_h2_pass.py:30-200・318-330`。
- gen_signal_families.py:516-575・935-950。
- `.claude/breaks/b91_keep_range_ignored.sh`（全文）、`.claude/breaks/lib.sh:60-120`。
- regime_laws.json:546-575。
- session_worklog_20261001.md:196-275。
- next_step.md:91・99・112・116・240。
- cp57_result.md（全文）、cp57_src.gen.md:1-40。
- `.claude/state/acceptance.approved`。
- やり取りの記録 d9852551…jsonl:200-239・1380-1423（jq で読んだだけ）。
- 監査 CP49 の結果:600-664。

### 走らせたコマンド（秒数を書いていないものは即時）

- `git log --oneline -12`・`git rev-parse HEAD`・`git show -s --format='%H %P %ci' bf238d5 e31d6e8`
- `git diff --stat`／`--numstat`／`-U0` の e31d6e8..bf238d5、bf238d5..HEAD、HEAD..作業ツリー（対象3ファイル）
- `git show e31d6e8:… | grep -n -F` と `git show bf238d5:… | sed -n | diff`（23件全部・Q1）
- `jq` による okd JSON の組み直しと、`diff - <(sed -n '317,861p' acceptance.md)`
- `shasum -a 256`（設計書・控え・依頼書）、`cmp`
- `python3 -B scripts/priority_rebuild/engine_tuner_gen.py --selftest-stages` → rc=0・6秒
- `python3 -B scripts/priority_rebuild/regime_r9_diag.py --selftest` → rc=0・3秒（⑨は一時フォルダ /var/folders/…/T/tmpjaq7l8ul/ に書いた。リポジトリの外）
- `jq '.stage_keep_range.hi' …search_limits.json` → 10・0秒
- `python3 -B .claude/hooks/enforce_h2_pass.py --check-fingerprint` → 一致・rc=0・0秒
- `python3 -B .claude/hooks/enforce_g2_pass.py --check-fingerprint` → 一致・rc=0・0秒
- `python3 -B scripts/priority_rebuild/engine_tuner_gen.py --selftest`（全体）→ rc=1・361秒・失敗は「T35③」の1件だけ（engine_tuner_gen.py:7815-7818 で失敗の一覧を最後にまとめて出す。直前の行は T48 の表示）。書き込みは全部 TemporaryDirectory の中です。
- `git status --short`（走らせる前と後）

### 走らせられなかったものと理由

- `python3 - <<EOF` の作業用スクリプト: hook require_design_contract_before_run.sh に止められました（「走らせる .py を確定できないコマンドです」）。.py を作業場に作ることも、読むだけの役目のため しませんでした。Q1 は上の読むだけの組み合わせで確かめました。
- `gen_signal_families.py --verify`: g2_selftest の中で g2_pass.json を書く（gen_signal_families.py:942）ので走らせていません。代わりに `enforce_g2_pass.py --check-fingerprint`（読むだけ）で照らしました。
- 壊すプログラム b91 の実走: 本物の engine_tuner_gen.py を一時的に書き替える作りなので走らせていません。見分けがつかなくなったことは、EXPECT_MSG（b91:4）と、いまの出力の「❌ T35③」の文字で示しました。
- 実装の前（e31d6e8）の全体 --selftest: 写しのファイルが要るので走らせていません。T35③ が直す前に通っていたことは、e31d6e8:engine_tuner_gen.py:3164-3165 が hi > 本数 で SampleError を出す行であることで示しました。


## 11. 本物のファイルを書き替えていないこと

監査（Plan agent）が走らせた `git status --short` は、走らせる前も後も211行で、sha256 は同じ 956faaa9af1c139326596b03374f9ed332caa1a55479514d50e336b4011034f3 でした。追跡されているファイルの変更は、監査の前から在る次の1行だけです。

```
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
```

- 監査（Plan agent）は作業場 cp57_work の中身を書き替えていません。作業場の外にも変化はありません。自己テストが作った一時ファイルは /var/folders/…/T/ の下にあり、リポジトリの外です。
- 結果を写した側（監査を起動したセッション）が書いたものは、作業場の `cp57_result.md`（この結果）と見直し表 `cp57_result.review.md`、それと結果ファイル1本だけです。
- 結果ファイルを書く前に、監査を起動したセッションが走らせた `git status --short` では、追跡されているファイルの変更は上の decisions.md の1行だけで、未追跡は210行でした。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-01_m2f_label_builder_stages_20261001_impl_cp57_audit_request.md request_sha256=78dae5fae2de27ed59fddd84682182992e32a1ea6bc248f5f2f719578e3c3202 -->
