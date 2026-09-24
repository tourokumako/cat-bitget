# 監査結果 cp40 — CP40 — 古い方の依頼書の道具 gen_audit_request.py が、テンプレへ足した見出し2つを設計書のとおりに扱えるか。設計書と実装の食い違いを、まとめて直せる形で洗い出す

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-21_audit_request_tool_impl_cp40_audit_request.md`
- 依頼書のハッシュ値: cfc87b6e1524e4529d9a553e88b9320fb9b3fbd4f2d65134bd8d9b334d961d7c
- 監査の相手と版（依頼書に書いてあるもの）: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py` ／ ハッシュ値 693800c7a33486e2d88e339a75df1ee7589e0e1888a43d78a789ea8483098c77
- 監査が照らしたハッシュ値: `693800c7a33486e2d88e339a75df1ee7589e0e1888a43d78a789ea8483098c77`（`shasum -a 256` の実測）＝**依頼書の記載と完全に一致**。設計書 `.claude/state/acceptance.md` は 612行・1行目の目印が `audit-request-template-heads-20260921` で、別の工事に上書きされていない。元データの控え `.claude/state/acceptance_src_audit-request-template-heads-20260921.json`（267行）は、正本 `SDK/.claude/ratchet/acceptance_src.json` と `diff` で同一。
- 実施日: 2026-09-24


## 2. 監査対象の型宣言

**コード型**（`gen_audit_request.py` の実装・壊すプログラム b41）と**文書型**（設計書・その元データ・テンプレ・凍結ファイル）の2つが該当する。**数値型は非該当**＝この工事は売買を1件も回さず、成績の数字を1つも作らない。


## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの）

依頼書の表の5件を、監査が自分で走らせた結果です。

| # | 依頼書の主張 | 監査が確かめた方法 | rc | 秒 | 結果 |
|---|---|---|---|---|---|
| 1 | 直す前＝12件のうち11件が rc=0・1件が NG（`gen_audit_request.py --selftest`＝10/11 pass） | 過去の状態なので走らせられない。`.claude/state/pre_audit_check.json` と worklog 20260921 §3-2 の写しを突き合わせた | — | — | **記録と整合**。ただし監査が再現したものではない |
| 2 | 直した後＝`--selftest` 12/12 pass・rc=0・`_selftest_tmp_` のフォルダは0個 | `python3 scripts/priority_rebuild/gen_audit_request.py --selftest` を走らせ、走行後に一時フォルダを数え、凍結ファイルの sha256 を撮った | 0 | 2.40 | **そのとおり**。`✅ わざと壊して止まるか試すテスト 12/12 pass`／一時フォルダ 0個／凍結ファイルは `50467a8c…` のまま。★秒数は設計書 4-14 の見込み「1秒未満」ではなく **2.40秒** |
| 3 | b41 が期待どおり rc=1・凍結ファイルは元に戻る | **走らせていない**（b41 は本物の凍結ファイルを書き替えて戻す作りで、監査は本物を書き替えない） | — | — | **データ不足（理由＝本物を書き替えるため走らせられない）**。落ちる道の内訳は 4節 A0-d に書いた。凍結ファイルのいまの sha256 は `50467a8c1d5bcb0b3cbc8f8ee315508c1d5498390dd7b338d6490fd138a1eefe` で、道具の中の記録と一致＝前回の走行から元に戻っている |
| 4 | `--run` が全部 rc=0・`--verify` が「監査に出せます」 | `--run` は走らせていない（途中で本物の文書を書き直すため）。`python3 .claude/tools/pre_audit_check.py --verify` を走らせ、`pre_audit_check.json` を読んだ | 0 | 0.3 | **そのとおり**。`監査に出せます（チェックの1枚が新しく、全部 rc=0）`／json の `at` は 2026-09-21 15:29:06・rc が 0 でない行は0件 |
| 5 | 本物の走行を設計↔実装の hook が止める（「設計書に書いていない関数を触った → <モジュール直下>」「齟齬: 4件」） | `python3 scripts/priority_rebuild/gen_audit_request.py`（旗なし）を走らせた | hook が exit 2 | 0.6 | **逐語で一致**。依頼書は作られていない |


## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ PASS
- ②リスク管理 ＝ PASS
- ③認知バイアス ＝ FAIL
- ④ソフトウェア工学 ＝ FAIL
- ⑤再現性 ＝ PASS
- ⑥実行プロセス ＝ FAIL
- ⑦主エージェントバイアス ＝ FAIL

判定の根拠を1件ずつ書きます。

- **①**＝この工事は統計の主張を1つもしていない。固定値ゼロ宣言のとおり、疑似シミュから取った値は0件。
- **②**＝本物の凍結ファイルの sha256 が走行の前後で変わらない。止まる道（fail-closed）が5か所とも残っている。一時フォルダの残骸は0個。
- **③**＝依頼書が問いの中に答えを置いている。`cp40_src.md`:78「**（必読の精査の節は、着手前必読の節の中に入るので、この数には入りません）**」。その前提は実物と違う（`gen_audit_request.py`:431 が `frozen["必読の精査"]` を依頼書へ入れる）。この前提をそのまま受け取ると、監査は A1-e の食い違いを見落とす。
- **④**＝機械の関所が赤のまま残っている（照合A が `RESULT: FAIL`・`--diff` が齟齬4件・どちらも rc=1）。さらに、この工事が新しく作った枝の中核（`gen_audit_request.py`:607 の凍結ファイルの本文の複写）を、自己テストが1つも見ていない。
- **⑤**＝依頼書の事実データ2・4・5 を監査が再現できた。1・3 は記録と実物の追跡でのみ追認した（再現していないことを明記した）。
- **⑥**＝依頼書が**実在しないコマンド**を監査に走らせるよう指示している（`cp40_src.md`:83 と 143 の `verify_design_contract.py --check <設計書>`）。実測は `FileNotFoundError: [Errno 2] No such file or directory: '--check'`。起案者が1回も走らせずに書いた。
- **⑦**＝③⑥と同じ根。加えて、自己申告に無い食い違いが4件 出た（A2-b）。自己申告の3件は正直だが、「自己申告に無い件は無い」は成り立たない。

### A0 — 自己テストの新しい枝（Q6②・Q10・Q12・Q12b・Q6①）と壊すプログラム b41 が、測ると言っているものを本当に測っているか（優先度 A）

**A0-a｜PASS。**Q10 は見本の凍結ファイルで測っており、手前の別の理由では止まっていない。`gen_audit_request.py`:736 逐語＝`                       lambda: _with_frozen(full, lambda: build_request(full)), "知らない見出し")`。測る相手は `full`＝足された2つの節を持つ見本なので、「足された節が無い」の道には入らない。照らす文字「知らない見出し」を `raise` に持つのは 581行の1か所だけ（`grep` で確認）。`stops_with`（674〜681行）は止まった理由の文まで見るので、別の理由で止まったものは通らない。

**A0-b｜通っている。ただし Q12 の照らす文字が甘い。**Q12b の照らす文字「小見出しが足りない」は 603行の1か所だけで、12/12 pass はその行に届いた証拠になる。一方 Q12（759行）は `build_request(QUESTION)`＝**本物の凍結ファイル**を渡し、照らす文字は「凍結ファイルに節が無い」で、これは 196行（必須の節が無い）と 596行（足された節が無い）の**2か所**に出る。いまは本物の凍結ファイルの sha256 が道具の記録と一致し、必須5節も実在するので 196行は発火しえず、今日の 12/12 は 596行に届いた証拠として成立する。しかし設計書 4-13 の5 が予定している「凍結ファイルへ節を足す」作業を行うと、Q12 は 196行の文でも通る。**変異テスト（`raise` を消して自己テストが落ちるか）は走らせていない＝データ不足（理由＝本物を書き替えずに写しを壊す手段が、この監査の実行環境では取れなかった）。**文字の一意性と、いまの凍結ファイルの状態の実測で代替した。

**A0-c｜中身までは見ていない。**Q6② が照らすのは4つだけ＝①テンプレの見出しが全部 在るか ②長さが 5000 文字を超えるか ③凍結ファイルの題が入っているか ④テンプレの丸括弧の決まりの行が入っているか（742〜753行）。**凍結ファイルの節の本文が入ったかを見る式が1つも無い**＝`gen_audit_request.py`:607 の `            p.append(frozen[key])` を消しても、自己テストは 12/12 のまま通る。この工事が新しく作った枝の中核が、自己テストで守られていない。あわせて、丸括弧の行を集める `_rules`（689行）は「この監査で答えてほしいこと」の節からしか取らないので、「依頼を出した CC の自己申告」の節の丸括弧の行が入ったかも見ていない。

**A0-d｜データ不足（理由＝b41 は本物の凍結ファイルを書き替えて戻す作りで、監査は本物を1文字も書き替えないため走らせていない）。**読んで断定できることだけを書く。①宣言の行は実在する＝`b41_req_frozen_section_gone.sh`:4 逐語＝`# EXPECT_MSG: ❌ Q6`。走らせる道具が求める形（`run_breaks.py`:433 の正規表現）を満たす。②落ちる道は両方＝b41 は `b41_req_frozen_section_gone.sh`:37 で `## [SECTION:スコープ]` の行を消す。すると Q6①（832〜840行）は本物を読んでハッシュ値の不一致（185行）で落ち、Q6②（742〜755行）は見本のハッシュを計算し直す（718行）のでハッシュ検査は通り、196行「凍結ファイルに節が無い: スコープ」で落ちる。＝b41 の説明「どちらの道でも止まる」は正しい。③元に戻る担保＝`lib.sh`:59 逐語＝`trap _restore EXIT` と、戻した後に sha256 を照らして違えば `exit 99` にする枝（48〜52行）。実測でも凍結ファイルは `50467a8c…` のままである。④限界＝`EXPECT_MSG` は部分一致なので、Q6 が別の原因で落ちても「期待どおり」になる。これは恒久71番（文書を作る道具に過剰なテストを付けない）と釣り合うので、監査は修正を出さない。

**A0-e｜PASS。**見る先の差し替えは、例外の種類を問わず戻る。`_with_frozen`（713〜722行）は `finally` で戻し、Q10 の `SECTION_KIND` の差し替えも `finally` で戻す（732〜738行）。見本のフォルダは 767〜773行の `finally` で消す。さらに Q6①（833行）が「差し替えが戻っていないこと」自体を検出する。残る穴はプロセスごと止められた場合だけで、道具が 696行に自分で書いている。

修正の番号＝修正5・修正14

### A1 — `build_request` と `load_frozen_question` と `template_sub_lines` が、設計書 4-2・4-4・4-5 のとおりに動くか（優先度 A）

**A1-a｜PASS。**605〜610行が、見出し → 空行 → 凍結ファイルの文 → テンプレの丸括弧の決まりの行、の順に並べている。設計書 4-4 の5 と一致する。

**A1-b｜止まる動きは PASS。照らし方には「誤って通る」形が2つ在る。**止まるのは 596行（節が無い）と 603行（小見出しが足りない）で、どちらも届いていることを A0-b で確かめた。照らし方は 600〜601行で、凍結ファイルの節の行を前後の空白を除いて集め、テンプレの小見出しの行がその集合に在るかを見る。①小見出しの行が在りさえすれば、その下に中身が1文字も無くても通る ②並び順を見ず、コードの囲みの中に小見出しの文字を書いても通る。**取りこぼし（在るのに無いと言う形）は見つからなかった。**この2つは中身の無い依頼書を止める目的に対して緩いだけで、恒久71番と釣り合うため、監査は修正を出さない。

**A1-c｜実装は正しく止まる。設計書がその場合を書いていない。**`load_frozen_question`（200〜201行）の「凍結ファイルの節が空」は、191行のくり返しが `FROZEN_SECTIONS + ADDED_SECTIONS` を回すので、足された節にも掛かる。中身の無い依頼書を出さないという設計の狙いと同じ向きで、止まる側に倒れている＝**この動きでよい**。設計書 4-5（異常系）の5行にこの行が無い＝設計書の側の書き漏れ。

**A1-d｜PASS。**`template_sub_lines`（228〜240行）がテンプレの節からその場で取り出すので、小見出しの名前も丸括弧の行も道具の中に書かれていない。テンプレの「依頼を出した CC の自己申告」の節は小見出しが0行・丸括弧の行が1行で、601〜602行が空の一覧どうしを照らすため落ちない。実測でも Q6②／Q9 が通っている。ただし、その丸括弧の行が依頼書に入ったかは自己テストが見ていない（A0-c と同じ）。

**A1-e｜合っていない。**567〜572行が作る文は、対応の表 `SECTION_KIND` の `frozen`／`frozen_added` の6件だけを数える。ところが `必読の精査` も凍結ファイルの節で、依頼書の本文に確かに入る＝`gen_audit_request.py`:431 逐語＝`    out.append(frozen["必読の精査"])          # ★分けた理由・外した理由は凍結ファイルから`。＝「起案者 (CC) が書いた文章は、凍結ファイル由来の6節…だけ」は実物と合わない（実際は7節）。**「着手前必読の中に入るから数えない」という理由づけは、その文自身が「起案者が書いた文章は6節だけ」と宣言している以上、成り立たない**（監査に対して、起案者の自由記述の範囲を実際より少なく申告する文になる）。設計書 4-3 は「数え方を実物に合わせる」と要求している＝設計書は正しく、実装が満たしていない。直す前の文（「4節」）も同じ誤りを持っていた。

**A1-f｜いまの実装はすり抜けていない。ただし死角が1つ増えた。**Q7 は `build_request`・`_meta`・`_reading`・`_facts` の文字定数だけを見る（779〜804行）。新しく足した文字定数は許す語（「起案者」「凍結ファイル」）を含むか 12文字未満なので、すり抜けではなく許された範囲に入る。一方、直す前は節の名前が `build_request` の中の文字定数で Q7 の監視下だったが、直した後は `SECTION_KIND` の鍵（モジュール直下＝Q7 の対象外）から依頼書の本文へ流れ込む。＝守りが1段 弱くなった。実害は小さい（鍵は「## 」で始まる見出しの形に縛られ、テンプレと突き合わせる）ので、これ単独では重さを付けない。修正4 を当てると、この流れが凍結ファイルの鍵（ハッシュ値で守られている側）由来に変わり、死角はむしろ狭くなる。

修正の番号＝修正4・修正16・修正20

### A2 — 設計書と実装の食い違いの全件と、その直し方（設計書の側か・実装の側か）（優先度 A）

**A2-a｜自己申告の3件は、3件ともそのとおりだった。**

★依頼書が指定したコマンドは実在しない。`python3 scripts/priority_rebuild/verify_design_contract.py --check .claude/state/acceptance.md` の実測は `FileNotFoundError: [Errno 2] No such file or directory: '--check'`（rc=1・0.12秒）。`verify_design_contract.py`:1825 逐語＝`    sys.exit(0 if check(sys.argv[1]) else 1)`＝旗ではなく、1つ目の引数をそのまま設計書のパスとして開く作り。正しい形は**旗を付けない**。

旗を付けずに走らせた出力（rc=1・0.27秒）:

```
design : /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md  ()
impl   : scripts/priority_rebuild/gen_audit_request.py
  [PASS] 自己チェック配線あり: load_frozen_question
  [PASS] 自己チェック配線あり: template_sub_lines
  [PASS] 自己チェック配線あり: build_request
  [PASS] 自己チェック配線あり: selftest
  [PASS] must_use build_request: 全部あり ['load_frozen_question', 'template_heads', 'template_sub_lines', 'section_refs_missing']
  [PASS] must_use selftest: 全部あり ['load_frozen_question', 'build_request']
  [FAIL] A scripts/priority_rebuild/gen_audit_request.py: 設計書に書いていない関数を触った → <モジュール直下>
RESULT: FAIL（設計と実装が乖離＝採点に進めない）
```

`--diff` の出力（rc=1・0.13秒）:

```
design : /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md
impl   : scripts/priority_rebuild/gen_audit_request.py
齟齬: 4件
    実物にあるが設計に無い関数: template_sub_lines
    build_request が実物では template_sub_lines を呼んでいるが設計に書いていない
    selftest が実物では load_frozen_question を呼んでいるが設計に書いていない
    selftest が実物では template_sub_lines を呼んでいるが設計に書いていない
```

- **自己申告1**＝そのとおり。元データ 249〜252行の `impl_functions` に `<モジュール直下>` が無い。照合の道具はモジュール直下を1つのまとまりとして数える＝`verify_design_contract.py`:884 逐語＝`      **モジュール直下（import・定数・トップレベルの処理）も 1つのまとまりとして入れる**`／903行 逐語＝`        out["<モジュール直下>"] = "\n".join(top)`。先例も実在＝`breaks-fix-found-20260917.frozen.json`:6 逐語＝`  "<モジュール直下>",`。＝この工事だけの入れ忘れ。
- **自己申告2**＝そのとおり。齟齬4件のうち3件は `template_sub_lines` の新設に伴うもの、1件は `selftest` が新しく `load_frozen_question` を呼ぶようになったもの（835行）。
- **自己申告3**＝そのとおり。見本は 707行で本物の凍結ファイルと同じフォルダの中に作られる。設計書 4-10 は「一時の置き場に作ります（今までの見本の作り方と同じ）」で、今までの作り方 `_tmp_md`（253〜259行）はシステムの一時置き場。理由の主張も実物どおり＝`gen_audit_request.py`:477 逐語＝`        p.append(f"| \`{path.relative_to(REPO)}\` | \`{_sha(path)}\` |")`＝リポジトリの外のパスに `relative_to(REPO)` を掛ければ ValueError になる。

**A2-b｜自己申告に無い食い違いが4件 在った。**

| 見た所 | 設計書の要求 | 実物 | どちらの側か |
|---|---|---|---|
| 4-3 の `build_request` の行（元データ 81行） | 冒頭の説明の「凍結ファイル由来の節」の数え方を実物に合わせる | 567〜572行は `必読の精査` を数えない＝「…だけ」が実物と合わない（A1-e） | **実装**（設計書は正しい） |
| 4-3 の「道具の冒頭の説明」の行（元データ 83行） | 節の出どころの説明を、いまの形に合わせる | 足した段（28〜38行）は在るが、元の説明はそのまま＝16行「CC が書ける4節だけ」／25行の一覧に `必読の精査` と足された2節が無い／272行／888行 | **実装** |
| 4-19 の5（元データ 167行） | 足された節の無い**見本**（＝本物と同じ形）で組み立てる | 759行は `build_request(QUESTION)`＝**本物の凍結ファイル**。副作用として照らす文字が 196行とも一致しうる | **設計書＋実装の1行**（本物で測る利点が在るので、設計書を実物に合わせ、照らす文字を締める） |
| 4-19 の1（元データ 163行） | 一時の置き場に作り、小見出しを3つ書く | 置き場は自己申告3のとおり違う。小見出しはテンプレから読んだ全部で、3という数を道具は持たない | **設計書** |

**食い違いでは無かったもの。**4-3 の残り6行は実物と一致した（`git diff` と現物で1件ずつ確認）。4-5 の5行は、足りない行が A1-c の1行だけ。4-19 の2・3・4・6 は実物どおり。7-6 の2行は、どちらも実測で達成を確認した（#1＝12/12 pass・rc=0／#2＝`--verify` rc=0）。ただし `acceptance.md`:495 と 496 の両行とも壊すプログラムの欄が `—` で、**承認のプログラムが「済」を書く道がこの工事に無い**＝恒久64番（CC は自分で直ったと判定しない）の担保が機械に無く、この監査が初めての外部の確認になる。恒久71番と釣り合うので、壊すプログラムを新しく作れという指摘は出さない。

**A2-c｜どちらの側を直すか。**8節の各件に割り当てた。振り分けの根拠は3つ。①設計書が明示的に要求している動きを実装が満たしていない件（A1-e・「4節」の説明）は**実装**を直す。②実装の判断のほうが妥当で、設計書が実物と違う件（見本の置き場・4-5 の空の行・4-19の1）は**設計書**を直す。③`impl_functions` は、実装が設計書 4-3 の「モジュール直下の定数と冒頭の説明を直す」をそのとおり行っているので、誤っているのは 7-8 の説明文の側＝**設計書（元データ）**を直す。見本の置き場を設計書どおりに戻す道は在る（`_facts` の 476〜477行を直す）が、`_facts` は承認済みの `impl_functions` に入っていないため、1変更（H16）を破って承認をもう1往復 増やす。いまの実装は残骸0個・他の道具の誤反応0件を実測しているので、設計書の側を実物に合わせる。

修正の番号＝修正1・修正2・修正3・修正4・修正5・修正6・修正7・修正8・修正9・修正10・修正11・修正12・修正13・修正17・修正18・修正19

### B1 — 見本の凍結ファイルを、本物の凍結ファイルと同じフォルダの中の一時フォルダに作る形で、害が無いか（優先度 B）

**B1-a｜PASS（残らない）。**正常に終わったときは実測で0個（`find .claude/audits/inputs -maxdepth 1 -name '_selftest_tmp_*' | wc -l` が 0）。`git status --short` にも1件も出ない。途中で例外が出たときは 767〜773行の `finally` が、作った瞬間に登録したフォルダ（707〜708行）を全部 消す。残る穴はプロセスごと止められた場合だけ。★この工事の外の事実として、`_tmp_md`（253〜259行）が作る見本は一度も消しておらず、システムの一時置き場に 26個 残っている。リポジトリの外で、この工事が作ったものでもないので、監査は修正を出さない。

**B1-b｜PASS（他の道具は誤って反応しない）。**1本ずつ実物で確かめた。①CP 監査一覧を作る道具＝`gen_audit_index.py`:58 逐語＝`    for p in sorted((AUD / "inputs").glob("*.md")):`＝深さ1だけを見るので、1段 深い見本には当たらない。加えて 59〜60行が `_` で始まる名前を飛ばす。②監査依頼書を書く瞬間に止める hook＝`enforce_audit_docs.py`:49 逐語＝`REQ_RE = re.compile(r"/\.claude/audits/inputs/[^/_][^/]*_audit_request\.md$")`＝`inputs/` の次が `_` では当たらず、名前も `_audit_request.md` で終わらない。③`pre_audit_check.py` に依頼書の置き場を走査する処理は無い。

**B1-c｜設計書の側を実物に合わせるのが正しい。**戻す道は `_facts` の 476〜477行の1点だけで実在する。取らない理由は A2-c に書いたとおり（1変更を破り、承認を1往復 増やす。いまの形の害は実測で0件）。

修正の番号＝修正6・修正7

### B2 — 監査に出す前のチェックと、新しい方の道具への影響（優先度 B）

**B2-a｜PASS。**`python3 .claude/tools/pre_audit_check.py --verify` は rc=0 で、出力は `監査に出せます（チェックの1枚が新しく、全部 rc=0）`。★あわせて穴を1つ実測した＝指紋の対象は9本で、そこに `gen_audit_request.py` は入っていない（`pre_audit_check.py`:78 逐語＝`FINGERPRINT_FILES = [`・中身は 79〜81行の9本。`grep -n "gen_audit_request"` の実測では 70行と 74行の2か所にしか出ない）。＝検査の一覧には `pre_audit_check.py`:70 逐語＝`    "gen_audit_request.py --selftest",` として入っているのに、指紋には入っていない＝チェックの後にこの道具を壊しても「チェックの1枚が新しい」と言い続ける。依頼書が `pre_audit_check.py` を監査対象外としているので、監査は修正を出さない。

**B2-b｜PASS（食い違い0件）。**`python3 .claude/tools/gen_audit_docs.py check <この依頼書> <この結果>` が rc=0 で、11項目すべて ✅・`食い違い 0 件`。あわせて、依頼書が道具で作られた後に書き替えられていないことも確かめられた（本文のハッシュ値を末尾の目印と照らす作りで、その食い違いの行が出ていない）。★`check` は依頼書1本では走らない（引数は依頼書と結果の2つ）。依頼書の書き方どおり1本で打つと使い方の案内が出て rc=2 になる。

修正の番号＝なし

### C1 — 説明の文と名前（優先度 C）

**C1-a｜足した段は合っている。元からあった説明は合っていない（4か所）。**足した段（28〜38行）は実物どおりで誤りがない。合っていないのは次の4つ。①16行 逐語＝`凍結ファイル（CC が書ける4節だけを置いたもの。既定＝\`_frozen_question_regime.md\`）を渡すと、`＝必須は5節（88行）＋足された2節。②25行 逐語＝`    frozen   … 凍結ファイル（経緯・スコープ・監査観点(本監査固有)・外部検索要請）`＝`必読の精査` が抜け、足された2節の行も無い。③272行 逐語＝`      直した後＝監査の題も対象も、凍結ファイル（CC が書ける4節）から取る。`。④888行 逐語＝`    ap.add_argument("--frozen", help="凍結ファイル（CC が書ける4節・既定＝_frozen_question_regime.md）")`＝**走らせる人が `--help` で読む文**なので、この4つの中では実害が大きい。

**C1-b｜件数の 12 は、見る枝の数ではなく、まとめの行に並べた Q ラベルの数。**856行 逐語＝`    total = 12`。実際に ❌ を出しうる検査を数えると **23件**（`stops` 7件・`stops_with` 3件・Q6② の枝5件・外側の例外1件・Q7 1件・Q11 3件・Q6① 3件）。枝が2つ在る番号の扱いも一貫していない＝Q8b（672行）は前からまとめの行にも `total` にも出ておらず、Q12b（763行）を足したのに `total` は 11 → 12 の1しか増えていない。分子は負になりうる＝271行 逐語＝`      **その結果、この道具の番人は Q6 が 0/13 で、-4/11 pass のまま3回の監査をまたいだ。**`。**＝「12/12 pass」は「失敗0件」の意味であって、「12件の検査に合格した」ではない。**依頼書の問い1 が言う「12/12 pass」は、この意味で読む必要が在る。なお この文字列を読み取っている壊すプログラムと hook は0本（b41 は `❌ Q6`・b30 は `Q11:`・チェックの道具は終了コードだけを見る）＝表示を変えても他は壊れない。

修正の番号＝修正11・修正12・修正13・修正15


## 5. 外部検索

### 検索 1 — なし

**しなかった。**依頼書の指定（「この工事は文書を作る道具の直しで、外の出どころに当たる論点は在りません。**外部検索は要りません。**『しなかった』と書いてください」）に従った。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

**そのとおり。**照合A の実測は `[FAIL] A scripts/priority_rebuild/gen_audit_request.py: 設計書に書いていない関数を触った → <モジュール直下>`・`RESULT: FAIL`（rc=1・0.27秒）。照合の道具がモジュール直下を1つのまとまりとして数えることは `verify_design_contract.py`:884・903行で確かめた。先例（`breaks-fix-found-20260917.frozen.json`:6）も在るので、この工事だけの入れ忘れである。直す相手は元データ 249〜252行で、`impl_functions` の一覧と `_impl_functions の意味` の説明文の両方＝説明文を残すと、直しと矛盾する。→ 修正1

### 自己申告 2

**そのとおり。**`--diff` の齟齬は4件（内訳は4節 A2-a に貼った）。**ただし承認をもう1回 もらう手間は、自己申告1 と同じ1回で済む。**7-8 の SPEC は設計書を作り直すたびに実物から作られる＝`gen_acceptance.py`:421 逐語＝`    spec = spec_from_impl(str(path))`。＝自己申告1 の直しを当てて作り直せば、SPEC の齟齬4件も同時に閉じる。2件を別々の往復に分ける必要はない。→ 修正1・修正2・修正3

### 自己申告 3

**そのとおり。**見本の置き場は 707行で本物の凍結ファイルと同じフォルダの中、設計書 4-10 は「一時の置き場（今までの見本の作り方と同じ）」で、今までの作り方はシステムの一時置き場（253〜259行）。理由の主張（`_facts` がリポジトリからの相対で印字する）も 477行の実物どおり。**実装の判断は妥当**＝残骸0個・他の道具の誤反応0件を実測した。直すのは設計書の側。→ 修正6・修正7

### 自己申告 4

**そのとおり。**`git diff` で `stops_with`（674〜681行）と Q12b（760〜765行）の新設を確認した。**この2つはどちらも守りを強くする方向**（Q12b は小見出しの検査を測り、`stops_with` は別の理由で止まったものを通さない）で、設計書 4-3 の `selftest` の行の趣旨に沿う。**足したこと自体を、監査は問題にしない。**問題はその分を件数に足していないことだけ（C1-b）。→ 修正15

### 自己申告 5

**そのとおり。**`acceptance.md`:495 と 496 の2行とも、壊すプログラムの欄は `—`。＝承認のプログラムが「済」を書く道がこの工事に無い。b41 の1回の測定は起案者の申告だけが根拠で、監査は再現していない（A0-d のとおり、本物を書き替えるため）。**＝完成の確認は、この監査が唯一の外部の目である。**恒久71番と釣り合うので、壊すプログラムを新しく作れという指摘は出さない。

### 自己申告 6

**そのとおり。そのうえで、設計の向きそのものは正しいと判定する。**根拠は3つ。①本物の凍結ファイルへ節を足す案は、まこさんが承認した文へ起案者が新しい文を書き足すことになり、この道具の芯（起案者が文を書けるのは凍結ファイルの中だけ・ハッシュ値で見張る）を起案者自身が動かす形になる。②テンプレから写す案は、テンプレの埋め草がそのまま残り、中身の無い依頼書が監査に出る。③チェックの一覧から外す案は、番人（`pre_audit_check.py`:74）と壊すプログラム b42 が守っている決まりを外す。3つの案を実物で比べた結果、採った案だけが止まる側（fail-closed）を保つ。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝設計書が決めた4つの動きを、実測で1つずつ確かめた。①足された2つの節を凍結ファイルから写す＝605〜610行の並びと、Q6② の丸括弧の行の検査が通っている ②節が無い・小見出しが足りないときに止まる＝596行・603行に届いていることを、照らす文字の一意性と、いまの凍結ファイルの状態の実測で確かめた ③テンプレに知らない見出しが在れば止まる＝581行・見本で測るので手前では止まらない ④本物の凍結ファイルは触らない＝走行の前後で sha256 が `50467a8c…` のまま。「12/12 が別の理由で通っている」ことは今日の時点では無い。★ただし「12」は検査の数ではなく失敗0件の意味であり、その読み方でのみ根拠になる＝C1-b）
- 問い2 ＝ YES（根拠＝自己申告の3件を実測で追認し、そのうえで自己申告に無い食い違いを4件 見つけた＝A2-b の表。合計7件について、設計書の側を直すか実装の側を直すかを8節に1件ずつ書いた。＝「全部 挙げられるか」は YES だが、「自己申告の3件だけ」ではない）

### 結論と件数

- 結論＝CONDITIONAL-GO
- Critical＝3（修正の指示の件数。所見としては1件＝設計↔実装の関所が赤のまま残置され、この道具の本物の走行が物理的に止まる）
- Major＝7（修正の指示の件数。所見としては3件）
- Minor＝8（修正の指示の件数。所見としては5件）
- Process＝2

CONDITIONAL-GO にした理由＝道具は設計書の決めた動きをしている（問い1 が YES）。一方で、設計↔実装の機械の関所が FAIL のまま残り、そのせいで**この道具で実際に依頼書を作る道が、いま物理的に塞がっている**（事実データ5）。＝この工事の目的のうち、自己テストとチェックの道は開いたが、本物の走行の道は開いていない。これは直せば閉じられる。


## 8. 修正の指示

★当てる順番＝番号の順。元データを直す件のあとには、その重さの中で必ず「作り直すコマンド」と「再承認のコマンド」が続く（重さを選んで当てても、設計書と承認が必ず揃うようにするため）。

### Critical

#### 修正 1
対象のファイル: `.claude/state/acceptance_src_audit-request-template-heads-20260921.json`
直す箇所: 249-252行
直す前の文字:
~~~
    "impl_functions": {
      "scripts/priority_rebuild/gen_audit_request.py": ["load_frozen_question", "template_sub_lines", "build_request", "selftest"]
    },
    "_impl_functions の意味": "この工事で触る関数。`template_sub_lines` は新設。見出しの一覧 `SECTION_KIND` と節の名前の一覧はモジュールの定数なので、この一覧には入らない（4-3 に書いた）。",
~~~
直した後の文字:
~~~
    "impl_functions": {
      "scripts/priority_rebuild/gen_audit_request.py": ["<モジュール直下>", "load_frozen_question", "template_sub_lines", "build_request", "selftest"]
    },
    "_impl_functions の意味": "この工事で触る関数と、モジュール直下のまとまり。`template_sub_lines` は新設。見出しの一覧 `SECTION_KIND`・節の名前の一覧 `ADDED_SECTIONS`・冒頭の説明はモジュール直下に在り、照合の道具はそれを `<モジュール直下>` という1つのまとまりとして数える（`verify_design_contract.py` の 884行・903行）。4-3 に書いたとおり、この工事で直す相手なのでこの一覧に入れる。",
~~~
根拠の抜き書き: `verify_design_contract.py`:903「`        out["<モジュール直下>"] = "\n".join(top)`」
状態: 確定

#### 修正 2
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json`
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cp /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance_src_audit-request-template-heads-20260921.json /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json && python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: `gen_acceptance.py`:421「`    spec = spec_from_impl(str(path))`」＝7-8 の SPEC は設計書を作り直すたびに実物から作られるので、自己申告2（齟齬4件）はこのコマンドで同時に閉じる
状態: 確定

#### 修正 3
対象のファイル: `.claude/state/acceptance.approved`
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh
~~~
根拠の抜き書き: `approve_impl.sh`:11「`#   bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh`」＝設計書を作り直したら、承認を打ち直さないとこの道具自身が依頼書を作らない
状態: 確定

### Major

#### 修正 4
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`
直す箇所: 567-570行
直す前の文字:
~~~
    # ★2026-09-21＝凍結ファイル由来の節の数と名前を、対応の表（SECTION_KIND）から出す。
    #   直す前は「4節」と名前を手で書いていた＝見出しが足されると、この文だけ古くなる。
    _from_frozen = [k[3:] + (")" if "(" in k and ")" not in k else "")
                    for k, v in SECTION_KIND.items() if v[0] in ("frozen", "frozen_added")]
~~~
直した後の文字:
~~~
    # ★2026-09-24（監査 cp40 の A1-e）＝凍結ファイルから読めた節を、そのまま数える。
    #   直す前は対応の表（SECTION_KIND）から出していた＝「必読の精査」を数え落としていた。
    #   その節は「## 着手前必読」（machine）の中に `_reading` が入れるので表には出てこないが、
    #   依頼書に入る CC の文であることは同じ＝「…だけ」の文が実物と合わなかった。
    #   凍結ファイルの鍵をそのまま使えば、節が増えても減っても数と名前が自動で合う。
    _from_frozen = list(frozen.keys())
~~~
根拠の抜き書き: `gen_audit_request.py`:431「`    out.append(frozen["必読の精査"])          # ★分けた理由・外した理由は凍結ファイルから`」
状態: 確定

#### 修正 5
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`
直す箇所: 759行
直す前の文字:
~~~
        stops_with("Q12 足された節が無ければ止まる", lambda: build_request(QUESTION), "凍結ファイルに節が無い")
~~~
直した後の文字:
~~~
        stops_with("Q12 足された節が無ければ止まる", lambda: build_request(QUESTION),
                   f"凍結ファイルに節が無い: {ADDED_SECTIONS[0]}")
~~~
根拠の抜き書き: `gen_audit_request.py`:196「`            raise SystemExit(f"[依頼書] 凍結ファイルに節が無い: {name}")`」＝必須の節が無いときも同じ文字が出るので、直す前の照らし方では 596行と区別できない
状態: 確定

#### 修正 6
対象のファイル: `.claude/state/acceptance_src_audit-request-template-heads-20260921.json`
直す箇所: 122行
直す前の文字:
~~~
      "**変えません。**自己テストの見本の凍結ファイルは、一時の置き場に作ります（今までの見本の作り方と同じ）。"
~~~
直した後の文字:
~~~
      "**変えます。**自己テストの見本の凍結ファイルは、本物の凍結ファイルと同じフォルダの中の一時のフォルダ（`_selftest_tmp_…`・走らせるたびに別の名前）に作り、終わったら必ず消します。今までの作り方（`_tmp_md`＝システムの一時置き場）にしない理由は、事実データを作る関数 `_facts` が凍結ファイルの場所をリポジトリからの相対で印字する所で ValueError になるためです（`_facts` はこの工事で触る関数に入れていません）。限界＝自己テストの途中でプロセスごと止められると、そのフォルダが残ります。"
~~~
根拠の抜き書き: `gen_audit_request.py`:707「`        d = pathlib.Path(tempfile.mkdtemp(dir=str(QUESTION.parent), prefix="_selftest_tmp_"))`」
状態: 確定

#### 修正 7
対象のファイル: `.claude/state/acceptance_src_audit-request-template-heads-20260921.json`
直す箇所: 163行
直す前の文字:
~~~
      "1. 自己テストが、本物の凍結ファイルの文の後ろに、見本の節を2つ足した文を、一時の置き場に作ります。「答えてほしいこと」の見本には、テンプレと同じ小見出しを3つ書きます。",
~~~
直した後の文字:
~~~
      "1. 自己テストが、本物の凍結ファイルの文の後ろに、見本の節を2つ足した文を、本物の凍結ファイルと同じフォルダの中の一時のフォルダ（`_selftest_tmp_…`）に作ります。「答えてほしいこと」の見本には、テンプレから読んだ小見出しを全部 書きます（いまのテンプレでは3つ）。",
~~~
根拠の抜き書き: `gen_audit_request.py`:704「`        for s in sub_lines:`」＝小見出しの数は道具が持たず、テンプレから読んだ一覧の数で決まる
状態: 確定

#### 修正 8
対象のファイル: `.claude/state/acceptance_src_audit-request-template-heads-20260921.json`
直す箇所: 167行
直す前の文字:
~~~
      "5. 次に、足された節の無い見本（＝本物の凍結ファイルと同じ形）で組み立てます。「凍結ファイルに節が無い」で止まることを見ます（Q12）。",
~~~
直した後の文字:
~~~
      "5. 次に、本物の凍結ファイル（足された2つの節が無い）で組み立てます。「凍結ファイルに節が無い: 答えてほしいこと」で止まることを見ます（Q12）。止まった理由の文は、足りない節の名前まで照らします（必須の節が無いときの同じ文言と区別するためです）。",
~~~
根拠の抜き書き: `gen_audit_request.py`:759「`        stops_with("Q12 足された節が無ければ止まる", lambda: build_request(QUESTION), "凍結ファイルに節が無い")`」＝`QUESTION` は本物の凍結ファイルで、見本ではない
状態: 確定

#### 修正 9
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json`
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cp /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance_src_audit-request-template-heads-20260921.json /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json && python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: `gen_acceptance.py`:97「`SRC = RATCHET / "acceptance_src.json"`」＝設計書の元データの正本はここで、控えを写してから作り直す
状態: 確定

#### 修正 10
対象のファイル: `.claude/state/acceptance.approved`
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh
~~~
根拠の抜き書き: `approve_impl.sh`:11「`#   bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh`」＝Major まで当てると設計書がもう一度 変わるので、承認を打ち直す
状態: 確定

### Minor

#### 修正 11
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`
直す箇所: 888行
直す前の文字:
~~~
    ap.add_argument("--frozen", help="凍結ファイル（CC が書ける4節・既定＝_frozen_question_regime.md）")
~~~
直した後の文字:
~~~
    ap.add_argument("--frozen", help="凍結ファイル（CC が書ける節・既定＝_frozen_question_regime.md）")
~~~
根拠の抜き書き: `gen_audit_request.py`:88「`FROZEN_SECTIONS = ("経緯", "必読の精査", "スコープ", "問い", "外部検索要請")`」＝必須は5節で、4節ではない
状態: 確定

#### 修正 12
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`
直す箇所: 16行
直す前の文字:
~~~
凍結ファイル（CC が書ける4節だけを置いたもの。既定＝`_frozen_question_regime.md`）を渡すと、
~~~
直した後の文字:
~~~
凍結ファイル（CC が書ける節だけを置いたもの＝必須5節 `FROZEN_SECTIONS` ＋ 足された2節 `ADDED_SECTIONS`。
既定＝`_frozen_question_regime.md`）を渡すと、
~~~
根拠の抜き書き: `gen_audit_request.py`:94「`ADDED_SECTIONS = ("答えてほしいこと", "自己申告")`」
状態: 確定

#### 修正 13
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`
直す箇所: 25行
直す前の文字:
~~~
    frozen   … 凍結ファイル（経緯・スコープ・監査観点(本監査固有)・外部検索要請）
~~~
直した後の文字:
~~~
    frozen   … 凍結ファイル（経緯・スコープ・監査観点(本監査固有)・外部検索要請）
                 ※「必読の精査」も凍結ファイルの節で、machine の「着手前必読」の中に入る。
    frozen_added … 凍結ファイル（答えてほしいこと・自己申告）＝2026-09-15 にテンプレへ足された見出し2つ
~~~
根拠の抜き書き: `gen_audit_request.py`:102「`    "## この監査で答えてほしいこと": ("frozen_added", "答えてほしいこと"),`」
状態: 確定

#### 修正 14
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`
直す箇所: 751-753行
直す前の文字:
~~~
            lost = [r for r in _rules if r not in body]
            if lost:
                ng.append(f"Q6: テンプレの丸括弧の決まりの行が依頼書に入っていない {lost[:1]}")
~~~
足す文字:
~~~
            # ★2026-09-24（監査 cp40 の A0-c）＝足された節の「中身」が入ったかも見る。
            #   直す前は、見出しとテンプレの丸括弧の行しか見ていなかった＝`build_request` の
            #   `p.append(frozen[key])` を消しても 12/12 のまま通った（新しく作った枝が無防備）。
            for _k in ADDED_SECTIONS:
                if _with_frozen(full, lambda: load_frozen_question())[_k] not in body:
                    ng.append(f"Q6: 足された節「{_k}」の凍結ファイルの本文が依頼書に入っていない")
~~~
根拠の抜き書き: `gen_audit_request.py`:607「`            p.append(frozen[key])`」＝この1行を消しても、742〜753行の検査は1つも落ちない
状態: 確定

#### 修正 15
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py`
直す箇所: 856-857行
直す前の文字:
~~~
    total = 12
    print(f"  {'❌' if ng else '✅'} わざと壊して止まるか試すテスト {total - len(ng)}/{total} pass")
~~~
直した後の文字:
~~~
    print(f"  {'❌' if ng else '✅'} わざと壊して止まるか試すテスト 落ちた枝 {len(ng)} 件"
          f"（見る枝＝Q1・Q2・Q3・Q4・Q5・Q6①・Q6②・Q7・Q8・Q8b・Q9・Q10・Q11・Q12・Q12b）")
~~~
根拠の抜き書き: `gen_audit_request.py`:271「`      **その結果、この道具の番人は Q6 が 0/13 で、-4/11 pass のまま3回の監査をまたいだ。**`」＝分子は負になりうる＝「N/N pass」は検査の数ではなく「失敗0件」の意味でしかない
状態: 未決

#### 修正 16
対象のファイル: `.claude/state/acceptance_src_audit-request-template-heads-20260921.json`
直す箇所: 99行
直す前の文字:
~~~
      "| 「答えてほしいこと」の節に、テンプレの小見出しが足りない | 足りない小見出しの名前を出して止まる |",
~~~
足す文字:
~~~
      "| 足された2つの節が、在るのに中身が空 | 読み込みの段で、必須の節と同じく「凍結ファイルの節が空」を出して止まる |",
~~~
根拠の抜き書き: `gen_audit_request.py`:201「`            raise SystemExit(f"[依頼書] 凍結ファイルの節が空: {name}")`」＝191行のくり返しが `FROZEN_SECTIONS + ADDED_SECTIONS` を回すので、足された節にも掛かる
状態: 確定

#### 修正 17
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json`
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
cp /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance_src_audit-request-template-heads-20260921.json /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json && python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/gen_acceptance.py --write
~~~
根拠の抜き書き: `gen_acceptance.py`:97「`SRC = RATCHET / "acceptance_src.json"`」＝修正16 を設計書に反映するため
状態: 確定

#### 修正 18
対象のファイル: `.claude/state/acceptance.approved`
直す箇所: なし
直す前の文字:
~~~
なし
~~~
走らせるコマンド:
~~~
bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh
~~~
根拠の抜き書き: `approve_impl.sh`:11「`#   bash /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks/approve_impl.sh`」＝Minor まで当てたときの最後の承認
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 19
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp40_work/cp40_src.md`
直す箇所: 83行
直す前の文字:
~~~
- **A2-a**｜自己申告の1番（`impl_functions` に `<モジュール直下>` が無い）・2番（SPEC が実装の前のまま）・3番（見本の凍結ファイルの置き場）を、それぞれ確かめてください。`python3 scripts/priority_rebuild/verify_design_contract.py --check .claude/state/acceptance.md` と `--diff` の出力を、結果に貼ってください。
~~~
直した後の文字:
~~~
- **A2-a**｜自己申告の1番（`impl_functions` に `<モジュール直下>` が無い）・2番（SPEC が実装の前のまま）・3番（見本の凍結ファイルの置き場）を、それぞれ確かめてください。`python3 scripts/priority_rebuild/verify_design_contract.py /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md`（★旗を付けない＝1つ目の引数を設計書のパスとして開く作り）と `python3 scripts/priority_rebuild/verify_design_contract.py --diff /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md` の出力を、結果に貼ってください。★依頼書にコマンドを書く前に、起案者が1回 走らせて終了コードと出力を確かめてください（恒久53番）。
~~~
根拠の抜き書き: `verify_design_contract.py`:1825「`    sys.exit(0 if check(sys.argv[1]) else 1)`」＝`--check` という旗は無く、監査が走らせた実測は `FileNotFoundError: [Errno 2] No such file or directory: '--check'`（0.12秒）。同じ誤りが 143行（着手前必読の9番）にも在る
状態: 確定

#### 修正 20
対象のファイル: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp40_work/cp40_src.md`
直す箇所: 78行
直す前の文字:
~~~
- **A1-e**｜依頼書の冒頭の説明の「凍結ファイル由来の節」の数と名前を、対応の表から出す形にしました。出てくる文が実物と合っているか（必読の精査の節は、着手前必読の節の中に入るので、この数には入りません）。
~~~
直した後の文字:
~~~
- **A1-e**｜依頼書の冒頭の説明の「凍結ファイル由来の節」の数と名前を、対応の表から出す形にしました。出てくる文が実物と合っているか。★「入る／入らない」の判断は監査が実物から出してください（起案者の見立てを問いに書かない＝問いの中に答えを置くと、監査が起案者の判断を引き継ぎます。同型バイアスの経路）。
~~~
根拠の抜き書き: `_template.md`:12「`メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。`」＝起案者が括弧書きで置いた前提は実物と違い、そのまま受け取れば監査は Major を1件 見落とす
状態: 確定


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 開いたファイル（着手前必読10件は全部・省略なし）

| # | ファイル | 開いた範囲 |
|---|---|---|
| 1 | `.claude/state/acceptance.md` | 全文 612行（目印は1行目・完成の条件の表は 490〜500行を監査自身も開いた） |
| 2 | `.claude/state/acceptance_src_audit-request-template-heads-20260921.json` | 全文 267行 |
| 3 | `SDK/scripts/priority_rebuild/gen_audit_request.py` | 全文 914行 |
| 4 | `git diff -- …gen_audit_request.py .claude/breaks/b41_req_frozen_section_gone.sh` | 出力 全文 |
| 5 | `SDK/.claude/audits/inputs/_template.md` | 全文 323行（7〜16行は監査自身も開いた） |
| 6 | `SDK/.claude/audits/inputs/_frozen_question_regime.md` | 冒頭30行・節の見出し5件・sha256 |
| 7 | `.claude/breaks/b41_req_frozen_section_gone.sh`（全文 44行）・`.claude/breaks/lib.sh`（全文 101行） | 全文（1〜10行・32〜44行・44〜64行は監査自身も開いた） |
| 8 | `.claude/tools/pre_audit_check.py` | 64〜108行（検査の一覧・指紋の対象・走らせる処理）ほか |
| 9 | `SDK/scripts/priority_rebuild/verify_design_contract.py` | 878〜908行（モジュール直下の扱い）・1818〜1825行（コマンドの口） |
| 10 | `.claude/state/session_worklog_20260921.md` | §3〜§6 |
| 追 | `.claude/tools/gen_acceptance.py`（92〜102行・410〜426行）・`.claude/tools/gen_audit_docs.py`・`.claude/tools/run_breaks.py`（428〜455行）・`.claude/tools/gen_audit_index.py`（53〜62行）・`.claude/hooks/enforce_audit_docs.py`（44〜54行）・`.claude/hooks/approve_impl.sh`（6〜16行）・`acceptance_archive/breaks-fix-found-20260917.frozen.json`（1〜10行）・`SDK/.claude/audits/cp40_work/cp40_src.md`（73〜88行・138〜148行） | 該当の範囲 |

### 走らせたコマンドと結果と秒数

| コマンド | rc | 秒 | 要点 |
|---|---|---|---|
| `shasum -a 256 …/gen_audit_request.py` | 0 | 0.1 | `693800c7…`＝依頼書の記載と一致 |
| `python3 scripts/priority_rebuild/gen_audit_request.py --selftest` | 0 | 2.40 | `✅ わざと壊して止まるか試すテスト 12/12 pass` |
| `find .claude/audits/inputs -maxdepth 1 -name '_selftest_tmp_*' \| wc -l` | 0 | 0.1 | 0（残骸なし） |
| `shasum -a 256 …/_frozen_question_regime.md`（走行後） | 0 | 0.1 | `50467a8c…`＝道具の記録と一致 |
| `python3 scripts/priority_rebuild/verify_design_contract.py --check <設計書>` | 1 | 0.12 | `FileNotFoundError: … '--check'`＝依頼書が指定したコマンドは実在しない |
| `python3 scripts/priority_rebuild/verify_design_contract.py <設計書>` | 1 | 0.27 | `[FAIL] A … <モジュール直下>` ／ `RESULT: FAIL` |
| `python3 scripts/priority_rebuild/verify_design_contract.py --diff <設計書>` | 1 | 0.13 | `齟齬: 4件` |
| `python3 scripts/priority_rebuild/gen_audit_request.py`（旗なし） | hook が exit 2 | 0.6 | 設計↔実装ゲートがブロック。依頼書は作られていない |
| `python3 .claude/tools/pre_audit_check.py --verify` | 0 | 0.3 | `監査に出せます（チェックの1枚が新しく、全部 rc=0）` |
| `python3 .claude/tools/gen_audit_docs.py check <依頼書> <この結果>` | 0 | 0.4 | `食い違い 0 件`（11項目 全部 ✅） |
| `python3 .claude/tools/gen_audit_docs.py form <この結果>` | 0 | 0.3 | 形の食い違い 0件 |
| `diff <控え> <正本 acceptance_src.json>` | 0 | 0.2 | 同一 |
| `grep -n "gen_audit_request" .claude/tools/pre_audit_check.py` | 0 | 0.1 | 70行と74行の2か所だけ＝指紋の一覧（78〜81行）には入っていない |
| `git status --short`（結果を書き終えた時点で1回） | 0 | 0.3 | 出力の全文を11節に貼った |

### 走らせられなかったものと理由

| 走らせられなかったもの | 理由 |
|---|---|
| 写しを作って `raise` を消す変異テスト（A0-b が指定） | 監査の実行環境で写しを作れず、インラインの python（`python3 -` ／ `python3 -c`）も設計↔実装ゲートが全部 止めるため、メモリ上で計装する道も取れなかった。照らす文字の一意性と、いまの凍結ファイルの状態の実測で代替した |
| b41 の実走（A0-d が指定） | b41 は本物の凍結ファイルを書き替えて戻す作り（37〜40行）で、依頼書の禁止（本物のファイルを書き替えない）に当たる。戻る担保（`lib.sh` の trap と sha256 の照合）は読んで確かめた |
| `pre_audit_check.py --run`（事実データ4） | 途中で `gen_indicator_switch.py --write` と `gen_materials.py --write` が本物の文書を書き直し、最後にチェックの結果の1枚を上書きする（約10分）。`--verify` とその結果の1枚の中身で代替した |
| 外部検索 | 依頼書が「要りません」と指定した |


## 11. 本物のファイルを書き替えていないこと

`git status --short` の出力の全文（結果を書き終えた時点で撮ったもの・1行も削っていない）。

```
 M .claude/breaks/b41_req_frozen_section_gone.sh
 M .claude/hooks/require_design_check_before_approval.sh
 M .claude/hooks/show_design_check_after_write.sh
 M .claude/rules/pdca_flow.md
 M .claude/settings.json
 M .claude/state/hook_roles.json
 M .claude/state/next_step.md
 M .claude/state/next_step_archive_202608.md
 M .claude/state/next_step_src.json
A  v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/audit-request-template-heads-20260921.01.diff.txt
A  v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/audit-request-template-heads-20260921.01.md
A  v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/audit-request-template-heads-20260921.01.sha.txt
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/impl_functions_frozen.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_todo.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.json
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md
 M v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py
?? .claude/hooks/require_chat_draft_before_long_reply.sh
?? .claude/hooks/require_design_check_before_approval.py
?? .claude/settings.json.bak_20260819
?? .claude/settings.json.bak_20260826
?? .claude/settings.json.bak_20260902_implock
?? .claude/settings.json.bak_20260903_a6
?? .claude/settings.json.bak_m2_2_2b
?? .claude/state/session_worklog_20260921.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/mirror_old/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp36_work/pristine/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp37_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp39_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp40_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-21_audit_request_tool_impl_cp40_audit_request.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/audit-request-template-heads-20260921.breaks.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/audit-request-template-heads-20260921.dirty.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/audit-request-template-heads-20260921.frozen.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/audit-request-template-heads-20260921.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

上に出ている `M` は全部、この工事（2026-09-21）とその前の工事が commit していない差分で、**監査が作ったものは1件も無い**。`cp40_work/` の中に作ったのは、この結果の下書き1本だけ。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-21_audit_request_tool_impl_cp40_audit_request.md request_sha256=cfc87b6e1524e4529d9a553e88b9320fb9b3fbd4f2d65134bd8d9b334d961d7c -->
