# 監査結果 cp44 — CP44 — 束2 の設計書（§2.2 の範囲と刻みの表／許容幅の張り付きを測る検査16／許容幅を1時間足の値動きの幅で決める部品 S-Rタッチ1時間ATR）は、出どころの逐語どおりの形になるか。書いたとおりに「実装の指示」をプログラムが当てられるか

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-26_m2e_bundle2_design_cp44_audit_request.md`
- 依頼書のハッシュ値: d16c2ff963ff109c79e71a68c320b981022277cac3954af45145ccf72d046a49
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 6b22bf8dad146a6228ad227aa7d2cd3de7b8fc78ca86329991a6e62697e15681
- 監査が照らしたハッシュ値: 6b22bf8dad146a6228ad227aa7d2cd3de7b8fc78ca86329991a6e62697e15681（`shasum -a 256 .claude/state/acceptance.md`・監査の始めと終わりの2回とも同じ値＝依頼書と一致）。設計書は1804行・目印 `m2e-bundle2-20260926`。元データ `acceptance_src.json`（483行）の sha256＝8be0c799598a46a054447f2bc73a1a4e08b810331883988147a7c98790d145a7（worklog 20260926 §3-12 の「8be0c799…」と一致）
- 実施日: 2026-09-26

## 2. 監査対象の型宣言

- **文書型**：設計書 acceptance.md と、その元データ acceptance_src.json（4-7 の表・決めてほしいこと・完成の条件19行・7-4）。
- **コード型**：実装の指示21件の Python（observe_diag.py・indicator_reference_diag.py・observe_config.json）と、壊すプログラム4本（bash と Python）。照らした既存コード＝engine_tuner_gen.py・engine_tuner_exec.py・gen_*.py・apply_audit_fix.py・approve_impl.sh・lib.sh・b53 ほか。
- **数値型**：手計算の既知答え3件（見本1〜3）、§2.2 の値の表、禁止3 の算術、検査16 の張り付きの割合の数え方。

## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの）

| 依頼書の行 | 監査が走らせたコマンドと結果 | 照合 |
|---|---|---|
| 136番の逐語 grep -c | `grep -c '許容幅は1時間足の値動きの幅で決め、タッチはその足の高値・安値で数える' .claude/state/next_step.md` → **1** | 一致 |
| tol=clamp の grep -c | observe_config.json → **2** | 一致 |
| `_reg("S-Rタッチ` | observe_diag.py → **862行の1件** | 一致 |
| `張り付` の grep -c | **0**（rc=1） | 一致 |
| 部品の関数に足のデータを渡す所 | `fn(src)` は 1724・4151・6443行。ほかの fn 呼び出し（3829・3905・3959〜3971・4469・4482・4564・5186・5359・5365・5391・5523 ほか）は、どれも5分足か合成の5分足 | 一致（「12か所」は数え方の違い。1時間足より長い足を渡す道は build_features と insp5_frame だけ、は一致） |
| TARGET 4本の差の塊 | `git diff HEAD -- （4本） \| grep -c '^@@'` → **0** | 一致 |
| 直す前の文字21件 | `grep -c -F` で **21件とも 1**（10節） | 一致 |
| 根拠の抜き書き25件 | 行番号 419・6471・7515・662・257 を実物で確かめて合致。残りは直す前の文字の件数で間接に確認 | 一致（抜き取り） |
| gen_exit_families --verify | `python3 -B …/gen_exit_families.py --verify` →「表は入力の正本と一致（手の改変なし）」rc=0・4.59秒 | 一致 |
| gen_composition_rules --verify | → 正本のずれ3件（exit_families.json・search_limits.json・signal_families.json）rc=1・2.25秒 | 一致 |
| gen_acceptance --write | 走らせていない（本物の設計書を書く道具のため）。設計書 1804行・sha256 一致は確認した | 事実の一部を確認 |
| pre_audit_check --check-design | 走らせていない（.claude/tools の .py は hook で走らせられない） | データ不足（理由：走らせていない） |
| require_design_check_before_approval --try | 監査の grep の文字に「gen_acceptance.py --write」が入っていたため、hook `show_design_check_after_write.sh` が自動で走らせた（13.1秒）。結果＝不足1件（A2）。理由は「この監査のセッションで Read tool が開いていないファイル」＝セッションごとの読み取り記録で決まる判定で、設計書の欠けではない | CC のセッションの結果（0件）とは比べられない |
| pre_audit_check --run | 走らせていない（記録を書くため・約10分） | データ不足（理由：走らせていない） |

## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ PASS（新しい統計の線を作っていない）
- ②リスク管理 ＝ PASS（売買しない・net に触れない・承認で止まる）
- ③認知バイアス ＝ FAIL（4-7 の「いまの engine_tuner」の欄を、§2.2 の文から書き、実物と照らしていない → 修正9・11・12・13）
- ④ソフトウェア工学 ＝ FAIL（新しい道＝長い足の値・検査16 の数え方に、値を確かめる番人が無い → 修正1〜7）
- ⑤再現性 ＝ PASS（乱数なし・決まった見本）。ただし実行しての再現は、CC も監査もしていない
- ⑥実行プロセス ＝ FAIL（承認の数を ORDER から数えずに決定を取った・当てた後のコードを走らせずに監査へ出した → 修正19・20）
- ⑦主エージェントバイアス ＝ FAIL（5分足での誤り＝見本3 には手を打ったが、決定 B で新しく作る長い足の道には「列が在るか」しか見ていない → 修正1〜3）

### A0 — 完成の条件19行の壊し方と壊すプログラム4本（新設 b104〜b107）が、条件の文そのものを壊して測れる形か（優先度 A）

- **A0-a**（b104 で見本3 が倍率1.5 で落ちるか）：手計算では落ちます。b104 の形では、最後のバー（720本目）の5分足の ATR% は、期間7 で約0.0848%、14 で約0.0607%、21 で約0.0537% です。1.5倍しても 0.127%・0.091%・0.081% で、どれも 0.15% 未満＝下端に張り付きます。帯は 100±0.15 になり、100.5 には触れず、数は 72（窓144）／144（窓288）です。正しい形の答えは 144／288 です（1.5 × ATR% ≧ 0.6%）。＝倍率1.5 の6件が ATR の期間 7・14・21 の全部で落ち、T-A1 の行が出ます。倍率0.5・1.0 は、期待の答えも n/2 なので割れません。CC の手計算（144 と 72）と一致しました。走らせての確認はデータ不足（理由：走らせていない）。
- **A0-b**（b105 で T-A4 が必ず落ちるか）：落ちます。b105 では、毎時30分で切ったとき、全部のデータの値は hh:00〜hh:55 の1時間足から、切ったデータの値は hh:00〜hh:30 の途中の1時間足から作られます。1e-12 以内で一致するには、5か所 × 期間3つ＝15通りの全部で「hh:30 の終値＝hh:55 の終値」かつ TR が同じ、でなければなりません。実データでは成り立ちません。T-A1 は b105 でも通ります（見本3 の倍率1.0 は ATR≈0.49995 で帯 0.49995＜0.5＝72＝期待と同じ）。＝落ちるのは T-A4（と T-A2）で、EXPECT_MSG の T-A4 の行が出ます。走らせての確認はデータ不足（理由：走らせていない）。
- **A0-c**（insp5_frame の置き場の行を消したとき、5本目を足すべきか）：足さなくてよい、と判定します。理由は3つです。①その行を消すと、検査16 は 2h〜1d で `_atr_pct_1h_on` が ValueError を投げて止まります＝完成の条件 #7 のコマンドが 0 以外で終わり、黙りません。②検査5（`_insp_samples`）は例外を拾って「計算できず」を印字します（observe_diag.py:4150〜4153）。ただし検査5 は判定しない報告で、禁止3 は検査5 の出力ではなく算術で決まります（gen_signal_families.py:125〜134）＝下流の判定は変わりません。③insp5_frame を通って部品を呼ぶのは、ほかに selftest_insp5 の HT_INPHASE%（1m・3m）だけです（6436〜6443行）。
- **A0-d**（正規表現と jq）
  - **#8**：「省いた列」は json.dumps(indent=1) で「"省く側": "残す側 と実質 同じ（…）"」の1行になります（observe_diag.py:5900・6014〜6016）。新しい部品が省く側・残す側・どうし、の3通りとも当たります。ただし、成績表のファイルが無いときや、新しい部品の列が載っていないときも 0 で通ります（`! grep -q` はファイルが無いと 2 を返し、`!` で 0 になる）→ 修正15。
  - **#9**：§2.2-0 の行は「| `指標` | 本数 |」の形です（gen_regime_kb.py:1126〜1130）。正規表現の `.` が当たる所はどれも1バイトの文字なので、どのロケールでも当たります。いまの S-Rタッチ数 の行で同じ形を grep すると、engine_tuner_milestones2.md:812 の1件に当たりました。
  - **#10**：`.on` は印の一番上の階層の一覧です（indicator_switch.json:69〜70＝`.on` の47・48番目の MMI・S-Rタッチ数）。jq は /usr/local/bin/jq に在ります。
  - #9・#10 は python3・bash で始まらないので、承認のプログラムは読みません（approve_impl.sh:466）。ただし壊すプログラムの無い行は承認では閉じない作り（506行）なので、7-4 の最後の行（実装の監査が走らせ直して閉じる）と合っています。
- **A0-e**（#5〜#19 に壊すプログラムを付けない判断と71番）：71番（permanent_rules.md:381〜387）では、scripts/priority_rebuild は「壊すプログラムで守る」相手です。#5・#6・#11〜#19 は既存の検査・自己テスト・照合で、それぞれ既存の番人が守っています（例＝検査4 の番人、observe_diag.py:6988〜6992）。#8〜#10 は作った物を読むだけです。★ただし #7（検査16）は新しいコードなのに、数え方を確かめる番人が1つもありません（前例の検査15 は T1〜T6・N4 を持つ、observe_diag.py:7380〜7443）＝71番の1行目に届いていません → 修正4〜7。★#4 は、壊すプログラムが「列が在るか」しか測りません（A3-d）→ 修正1〜3。

修正の番号＝1・2・3・4・5・6・7・10・15・18

### A1 — 1時間足の ATR% を当てる関数（`_atr_pct_1h_on`・実装の指示 1）が、未来を見ず、どの足にも正しい1時間足の値を当てるか（優先度 A）

- **A1-a**（未来を見ないか）：静的に読んだ結果、未来は見ません。①1時間足の値の時刻＝始まり＋1時間（実装の指示1）。②バー s には、s＋step（そのバーが閉じた時刻）以前に閉じた1時間足を ffill で当てる。③build_features は上位足の値を「始まり＋足の長さ」へずらしてから5分足へ ffill する（observe_diag.py:1730〜1731）。この3つを重ねると、5分足の時刻 t に写る値は、t 以前に閉じた足の値です。その足の許容幅は、その足が閉じた時刻以前に閉じた1時間足から作られます＝t 以前の情報だけです。出どころの戦略ファイルは、5分足へ写すときに1時間足を shift(1) しています。設計はそれより1時間新しい値を使いますが、そのバーの終値と同じ時刻に確定する値で、未来ではありません。検査4 を新しい部品だけで走らせる確認はデータ不足（理由：走らせていない）。
- **A1-b**（step の出し方）：中央値を使うので、欠けがあっても5分のままです。バーが1本だけのときは NaT→0 で「1時間足以下」として扱い、1時間足が閉じていないので空になります。1時間足より長い足が1本だけ渡されたときも空になり、違う値は出しません。最初の1時間足が閉じるまでは空です。
- **A1-c**（1分足の元データと5分足の違い）：同じ時間の1時間足の4本値は、2つの元データが同じ Binance Spot 系列なら一致します。一致を実測で確かめたかはデータ不足（理由：走らせていない。設計書 7-4 も「検査していない」と書いている）。元データの端の途中の1時間足は、どの道でも当てる前に捨てられます。
- **A1-d**（古い5分足が残る道）：列を作る道は、どれも置き場を入れ直します（build_features＝実装の指示9、insp5_frame＝実装の指示8）。検査4（4080・4097行）・成績表（5915行）・実行器（engine_tuner_exec.py:2044〜2045）・組む側（engine_tuner_gen.py:3927〜3932）は build_features を通ります。gen_materials の範囲の番人は合成の5分足です（gen_materials.py:713〜717）。＝いま古い5分足を当てる道はありません。★ただし 7-4 の「直に呼ぶ道＝止まります」は正確ではありません。同じプログラムの中で先に入った5分足がその期間を覆っていると止まらず、その5分足から1時間足を作ります（中身が同じデータかは見ない）→ 修正16。
- **A1-e**（覆いの判定）：切り詰めたデータでも正しく通ります（最初の5分足＜最初の足の始まり＋step、最後の足の始まり≦最後の5分足）。止まるのは、置き場が空のときと、別の期間のときです。
- **A1-f**（attrs を取らない理由と、ほかの渡し方）：理由は成り立ちます（pandas 2.x は派生の計算のたびに attrs を写すので、5分足の表を持たせると全部の計算で写しが起きる）。ContextVar なども、同じ「プログラムの中で1つの置き場」になります。置き場より良い渡し方は「部品の関数の引数を足す」ですが、573種の呼び方を変えることになり1変更に収まりません（設計書 5 の2番の理由と同じ）。置き場の形でよく、7-4 の書き方を実物に合わせます（修正16）。

修正の番号＝16・18

### A2 — 部品の形（許容幅の式・挟み方・タッチの数え方）が、136番の逐語と出どころの逐語どおりか（優先度 A）

- **A2-a**（逐語と RG-v6 との違い）：形は逐語どおりです（倍率 × ATR ÷ その1時間足の終値を 0.0015〜0.006 で挟む）。RG-v6 `_adaptive_tol_1h`（build_regime_gate_rg.py:262〜270）との違いは3つです。
  - ①ATR の平滑：RG-v6 は14本の単純平均（268行 `rolling(14).mean()`）、設計は `_atr`（Wilder の平滑、observe_diag.py:271〜273）
  - ②期間：RG-v6 は14だけ、設計は 7・14・21
  - ③値が出る前：RG-v6 は定数（`v17.ZONE_TOL`）で埋める、設計は空

  割る終値と挟み方は同じです。逐語は平滑の式を書いていないので、どちらも逐語には反しません。ただし逐語が指す実装（RG-v6）は単純平均で、設計書はこの違いをどこにも書いていません → 修正14（Minor）。
- **A2-b**（タッチの数え方）：`_sr_touch(d.close, d.high, d.low, …)`＝渡された足の高値・安値で数えます。136番の逐語どおりです。
- **A2-c**（窓を全部の足で同じ本数にすること）：既存の S-Rタッチ数 と同じ作りです。禁止3（gen_signal_families.py:99〜101・125〜134）で、窓288 は 2h・4h・6h・1d、窓144 は 4h・6h・1d が外れます（算術＝288×120÷1440＝24日、549÷24＝22.9＜30／144×120÷1440＝12日、45.8≧30）。4-0 の③と一致します。
- **A2-d**（手順8 で足りるか）：検査12 と、成績表の「省いた列」は5分足だけで測ります（`_dup_pairs` の `tf="5m"`）。T23② の1位は15分足なので、15分足での重なりは測られません。同点のときの残し方（4845〜4847行＝暖機が同じなら名前の並び順）では「S-Rタッチ1時間ATR」が「S-Rタッチ数」より前に並びます。＝倍率1.5 が既存の S-Rタッチ数(144,0.006) と実質 同じと出たら、既存の方が省かれます。これは #8（残す側の値にも「1時間ATR」が入る）と手順8 で、まこさんの前に出ます。実際に同じと出るかはデータ不足（理由：走らせていない）。

修正の番号＝14・18

### A3 — 番人 T-A1〜T-A4 と参照表の登録（教科書の式・既知答え3件）が、この直しを見抜けるか（優先度 A）

- **A3-a**（既知答えの手計算）：手で18種を確かめました。
  - 見本1＝ATR 0 → 下端 → 帯 ±0.15 → n。
  - 見本2＝ATR% 3.93% → 倍率0.5 でも 1.96% → 上端 0.6% → 安値100.8＞100.6 → 0。
  - 見本3＝ATR（59本目）は、期間7 で 0.49994、14 で 0.49370、21 で 0.47196。÷100.5 すると、倍率0.5・1.0 は 0.4975% 以下 → n/2。倍率1.5 は 0.6% → n。
  - いちばん境目に近いのは倍率1.0・期間7 で、余白は 0.0025（価格100 に対して）＝小数の丸めでは割れません。
  - `_mk` の時刻は 2026-03-01 0時で、時の区切りに揃っています（indicator_reference_diag.py:50）。

  走らせての確認はデータ不足（理由：走らせていない）。
- **A3-b**（教科書の式の独立性）：独立です（観察の道具を import していません）。丸めで数が1つずれるのは、窓の高値・安値が帯の端から 1e-14 程度の近さにあるときだけです。上下限に挟まれたバーは、両方とも同じ定数になるのでずれません。実データで1つもずれないかはデータ不足（理由：走らせていない）。
- **A3-c**（値決め窓と採点窓の違い）：どちらも式の突き合わせで、値は選びません。問題は無いです。
- **A3-d**：★Critical。T-A3 は4時間足の列が「空でない」ことしか見ていません。
  - 1時間足より長い足の枝が「渡された足のバーから1時間足を作る」形（`if step <= pd.Timedelta("1h"):` を外す）に戻っても、4時間足の ATR% が出て列は空になりません。
  - T-A1・T-A2・T-A4 は5分足しか見ず、検査3（5分足）・検査4（未来は見ない）・検査13 も通ります＝完成の条件19行のどれにも掛かりません。
  - これは、2026-09-06 に外した誤り（渡された足の ATR%）と同じ型です。それが、まこさん決定 B で新しく作る「2時間足〜1日足」の道にだけ、形を変えて残れる状態です。
  - cp22 の N-1 の教訓（合成の見本は通るのに実データでは通らない）と同じ所です。

  → 修正1〜3。

修正の番号＝1・2・3

### A4 — 「実装の指示」25件が、当てる道具でそのまま当てられ、当てた後のコードが動くか（優先度 A）

- **A4-a**：データ不足（理由：写しを作れず、1つも走らせていない。監査の Plan サブエージェントは読み取りだけの役割で起動され、ファイルを作れなかった）。静的に確かめたことは次のとおりで、読んで見つけたコードの誤りは0件です。
  - ①直す前の文字21件＝`grep -c -F` で全部 1。
  - ②新しいコードが使う名前（pathlib・iref・SEARCH_START/END・BARS_CSV・load_1m・_insp_windows・SUB_5M_TF・_assert_search_window_only・_resample・_atr）は、全部モジュールの中に在る。
  - ③`from __future__ import annotations`（95行）が在るので、`str | None` の書き方は動く。
  - ④名前の型が揃う＝`_reg`・参照表の正規表現・実行器の `_template_from_pattern`（engine_tuner_exec.py:265 → `S-Rタッチ1時間ATR({},{},{})`）・find_material。
  - ⑤参照表の網羅（observe_diag.py:6979〜6985）・系統の網羅（実行器 4585行）・印の源4（gen_indicator_switch.py:269）は、実装の指示18〜20 で揃う。
- **A4-b**（順番）：当てる道具は、当てる直前の中身で「直す前の文字がちょうど1か所か」を見直します（`_recheck`・apply_audit_fix.py:488〜497）。先の件の足す文字の中に、後の件の直す前の文字を含むものはありません。壊すプログラム4件は `NEVER_WRITE`（apply_audit_fix.py:67〜73）なので、当てずに一覧へ出るだけで、ほかの件は当たり、終了コードは1です（apply_audit_fix.py:535）。
- **A4-c**：`"--selftest" in sys.argv` はリストの要素の完全一致です。`selftest_atr1h()` は中で SystemExit を投げるので、引数の解析には進みません。
- **A4-d**（探す文字が当てた後の行と合うか）：合います。b104＝実装の指示5 の行＋改行、b105＝実装の指示1 の `a.index = …`、b106＝既存の430行、b107＝`    _H1_BASE["bars"] = bars\n`（insp5_frame の `= span`・T-A3 の `= None` とは別の文字）。
- **A4-e**（設定ファイル）：JSON は目視で正しいです。load_config は「_」で始まる鍵を捨てます（206行）。説明書を作る道具は、設定の鍵を1つずつ照らしません。

修正の番号＝19・21

### A5 — この設計に、乱数と、新しい数字・点の一覧が0件か（優先度 A）

- **A5-a**：新しいコードに乱数は0件です。番人の見本も決まった並びです。
- **A5-b**：material_ranges は倍率を小数の範囲 0.5〜1.5 にします。ただし段1 の候補（build_stage_candidates）は成績表の列の数字をそのまま使うので、段1 で試すのは18点です。これは既存の全部の部品と同じ作りで、範囲を開くのは §2.2 の段5 です。

修正の番号＝なし

### A6 — M2-E-1b の表（設計書 4-7）が §2.2 の段の表の値を全部 拾い、分け方・いまの値・置き場・出どころが実物と合っているか（優先度 A）

- **A6-a**：§2.2 の段の表（761〜767行）の「値の範囲」の欄には値が20個あり、4-7 の表に在るのは19個です。段5 の「線＝`neighbor_drop_max`（まこさんの判断待ち）」（engine_tuner_milestones2.md:767・3221行でも未決）が落ちています → 修正8（Major）。
- **A6-b**（分け方と「いまは書けない」）：分け方は正しいです（高安の本数＝パラメータ、経過バー・余白＝閾値）。「いまは書けない」も、組む側が作る閾値は分位だけで、生の値の範囲の置き場が無い、という意味では正しいです。ただし「いまの engine_tuner」の欄は、実物と違う所が2つあります。
  - ①実行器は値の4区分と連動（ref）を読みます（engine_tuner_exec.py:795〜803・1960〜1969）。「幅の床 0.08%」は名前つき定数 SCALP_FLOOR（indicator_reference_diag.py:4949）で、`{"const": "SCALP_FLOOR", "mult": m}` は実行器が計算できます → 修正12・13（Minor）。
  - ②段3 の緩め幅は、実物では `_loose_q_fixed`（隣の段に決め打ち・乱数なし、engine_tuner_gen.py:629〜645・3092・3298）です。表が書く `_loose_q`（乱数で引く、1699行）は、入口・出口の道（1733行）でしか使っていません → 修正9（Major）。
- **A6-c**（決めてほしいこと2件の読み）：
  - 決めてほしいこと1 の読みは正しく、実物でも裏づけられます。持続（streak）の n は `int_range`（2823行）から、状態を保つ形（hysteresis）の上限 n は `state_hold_bars_range`（3331行 `_nv_fixed(limits, "state_hold_bars_range", "n", order_n)`）から取っています。ただし表の段3 の行には、後者が書かれていません → 修正11（Minor）。
  - 決めてほしいこと2 の読み（q50 は段2c の範囲の外）も正しいです。
- **A6-d**：正しいです。n本高値・安値は swing_windows の 24・48・96 で、20 はありません。fib位置 は 20・96。Donchian（20・48）はボラの系統です。

修正の番号＝8・9・10・11・12・13・18

### B1 — 部品を足したあとの作り直しの道具と順番に、抜けや誤りが無いか（優先度 B）

- **B1-a**：型の表を読むものは、CC の12本に加えて hook 2本（enforce_signal_table_gate.sh・require_acceptance_before_impl.sh）です。どちらも承認の門で、`--approve` の後に通ります＝作り直しの道具は足りています。設計書の自動の節（2-2 の「140種」）は古くなりますが、承認の指紋を変えないため作り直さないのが正しいです（照らす hook は見つかりませんでした）。★出口の表の承認は、まこさんの決定④（1回）の外です → 修正17・修正20。
- **B1-b**：ORDER（pre_audit_check.py:45〜54）と設計書の手順9〜13 は、同じ順番です。読み込ませる法則の文書は、型の表・出口の表・範囲の置き場の sha256 を記録する（206〜210行）ので、承認の後に置くのが正しいです。成績表の全走について：材料の文書は成績表を読まない（grep 0件）ので、材料の文書より前に置く必要はありませんが、§2.2-0 の表と T23② が成績表を読むので、その2つの前に置くのが要ります＝設計の置き方は正しいです。★手順8 で倍率を外すと決まった場合、承認済みの実装の指示21 と違う形になりますが、その道（設計書の作り直しと再承認）は書かれていません（修正は付けない＝まこさんがそのとき決める）。
- **B1-c**：コードに部品の数の決め打ちがあるのは、T23② の見本（engine_tuner_gen.py:6321）だけです。文書の件数は道具が作り直します。engine_tuner_milestones2.md:1788 の「153部品・69種」は、日付つきの実測の記録です。

修正の番号＝17・18・20

### B2 — 設計書 4-13（影響範囲）と「やらないこと」に、見落としと、成り立たない理由が無いか（優先度 B）

- **B2-a**：scripts/priority_rebuild・scripts/dashboard・.claude/tools を grep した結果、1時間足より長い足を部品の関数に渡すのは build_features と insp5_frame だけです。condition_parts_diag.py:503 も build_features を通ります。dashboard は observe_diag を import していません。
- **B2-b**：T23② は「成績表の実物の1位の写し」で、①並び・③種類と時間足・⑤重なり の検査は別に効きます＝役目は壊れません。ただし、この直しは実装の指示の外で、CC が手で書きます（修正は付けない）。
- **B2-c**：b53 の探す8行は、実装の指示8 がその後ろに1行を足すだけなので残ります。observe_diag を書き替えるほかの11本（b39・b40・b55〜b58・b60・b61・b63〜b65）の探す文字も、どの指示にも消されません。b57 は H2 の印が最新であることが前提なので、手順13 の後に走らせます。
- **B2-d**：DESIGN_CONTRACT と 4-3 は合っています。修正4 で関数を1つ足すなら、impl_functions にも足します → 修正7。

修正の番号＝7

### C1 — 名前・文書・見積もり（優先度 C）

- **C1-a**：名前の分解で問題は出ません（禁止3 は2以上の数字の最大＝窓を使い、倍率は数えない、gen_signal_families.py:99）。
- **C1-b**：99行 × 2つの形の、本数・下端・上端の表は、線を決める材料として足ります（数え方の番人が無い点は修正4〜7）。
- **C1-c**：見積もりは過去の実測から出ていて、制限時間56時間の約1割です。修正1〜7 で番人の時間は数秒延びるだけです。

修正の番号＝なし

## 5. 外部検索

### 検索 1 — サポート・レジスタンスの帯の許容幅を、上位足の ATR で決める形

- WebSearch（allowed_domains＝tradingview.com・luxalgo.com・github.com）を2回。もう1回は、許されていないドメインを含めたため API に拒否されました。WebFetch は5回（うち2回は 404）。
- **https://github.com/Thashitharan27/Crypto-Strategy-Lab/pull/272**（取り出した逐語）：「zone_low = minimum raw pivot - padding × timeframe ATR / zone_high = maximum raw pivot + padding × timeframe ATR」「the zone uses **4H ATR**, not strategy ATR」＝線を作った足（4時間足）の ATR を使い、執行の足の ATR は使わない形です。幅を上下限で挟む形は、この文書には無いです。
- **https://www.tradingview.com/script/3WgfGErN-Support-and-Resistance-MTF-Flux-Charts/**：「You can switch zone size between fixed and dynamic, dynamic option has an ATR approach to zone size, and should be consistent across different timeframes」＝どの足の ATR かは書いていません。
- **https://www.tradingview.com/script/DrcEUv8C-Support-Resistance-Channels-Zones-Multi-Time-Frame/**：「"Maximum Channel Width %": is the percent for maximum width for each channel」＝上限は % で、ATR には連動していません。
- **結論**：上位足（線を作った足）の ATR で幅を決める形は、個人の実装に在りました（上の PR）。業界の標準・文献としては見つからなかった。「ATR に連動させ、上下限で挟む」形は見つからなかった。

## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

事実です。監査も走らせていません（監査の Plan サブエージェントは読み取りだけの役割で、写しを作れなかった）。静的に読んだ範囲では、コードの誤りは0件です。ただし、長い足の値（修正1）と検査16 の数え方（修正4〜7）には番人が無いと分かりました。走らせての確認は修正19 で手順にします。

### 自己申告 2

事実です。「中身」の側を読んだ結果、写し違いは見つかりませんでした。見つかったのは、番人の抜け（Critical・Major）です。

### 自己申告 3

事実です。型の表を読むものには、hook 2本も在りました（作り直しは不要）。承認が2つになることは、まこさんの決定④の外なので、決めてほしいことに出します → 修正17・20。

### 自己申告 4

名前は問題ありません。置き場の形も採ってよいですが、7-4 の書き方が実物と違います → 修正16。

### 自己申告 5

事実です（監査の実行でも3件・2.25秒）。手順9 と #19 で直る作りです。

### 自己申告 6

事実です。切り分けは、T-A1〜T-A4 が行ごとに分かれていることで一部 補えます。

## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝許容幅は「1時間足の ATR ÷ その1時間足の終値 × 倍率」を 0.15%〜0.6% で挟む形で、タッチはその足の高値・安値で数え、1時間足は閉じた時刻から使います（A1-a・A2-a・A2-b）。2h〜1d でも、置き場の5分足から作った正しい1時間足が当たります。2026-09-06 の誤りは、設計の形としては残っていません。守りの抜けは問い3 で扱います）
- 問い2 ＝ YES（根拠＝直し方の向きは正しく、20個の値のうち19個が正しく分けられています。決めてほしいこと2件の読みも、実物で裏づけられました。落ちている1個（neighbor_drop_max）と実物と違う欄は、行を足す・直すだけで済みます（修正8・9 は Major、11〜13 は Minor））
- 問い3 ＝ NO（根拠＝Critical が1件在ります。長い足の値を確かめる番人がありません（A3-d）。実装の指示が当たるかは、静的には問題ありません。当てた後のコードの実走はデータ不足（理由：走らせていない））

### 結論と件数

- 結論＝CONDITIONAL-GO
- Critical＝3（修正の数。所見の数は1）
- Major＝7（修正の数。所見の数は3）
- Minor＝8（修正の数。所見の数は6）
- Process＝3（修正の数。所見の数は2）

## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 470行（実装の指示 14 の中身・T-A3 の「列が作れない」の行の直後）
直す前の文字:
~~~
            ng.append(f\"T-A3: 4時間足で {cat[0][0]} の列が作れない（{meta.get(col)}）\")
~~~
足す文字:
~~~
\n        # ★T-A3 の2つ目（監査 CP44 の修正 1）＝4時間足に当てた1時間足の ATR% が、同じ5分足から作った1時間足の値と1本も違わない。\n        #   4時間足のバーから ATR を作る形（2026-09-06 に外した誤りと同じ型）を見抜く。わざと外した形（4時間足のバーの ATR%）も\n        #   同じ物差しに掛け、違いが出ることを毎回 確かめる（見抜く力の確かめ・検査15 の N4 と同じ考え）。\n        _an3 = cfg[\"atr_periods\"][0]\n        _d4 = _resample(big[[\"open\", \"high\", \"low\", \"close\", \"volume\"]], \"4h\")\n        _H1_BASE[\"bars\"] = big\n        _a4 = _atr_pct_1h_on(_d4, _an3)\n        _a5 = pd.Series(_atr_pct_1h_on(big, _an3), index=big.index)\n        _at = _d4.index + pd.Timedelta(\"4h\") - pd.Timedelta(\"5min\")\n        _in = _at.isin(big.index)\n        _b5 = _a5.reindex(_at[_in]).to_numpy(float)\n        _b4 = _a4[_in]\n        _bw = (_atr(_d4.high, _d4.low, _d4.close, _an3) / _d4.close).to_numpy(float)[_in]\n        _ok = ~np.isnan(_b4) & ~np.isnan(_b5)\n        if int(_ok.sum()) < 100:\n            ng.append(f\"T-A3: 4時間足の値を突き合わせる本数が足りない（{int(_ok.sum())} 本）\")\n        elif float(np.abs(_b4[_ok] - _b5[_ok]).max()) > 1e-12:\n            ng.append(\"T-A3: 4時間足に当てた1時間足の ATR% が、5分足から作った値と違う＝4時間足のバーから ATR を作っている疑い\")\n        elif float(np.abs(_bw[_ok] - _b5[_ok]).max()) <= 1e-12:\n            ng.append(\"T-A3: わざと外した形（4時間足のバーの ATR%）でも同じ値になる＝この突き合わせは何も見抜けない\")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:470「if col not in feats.columns or int(feats[col].notna().sum()) == 0:」
状態: 確定

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 377行（完成の条件 #4 の「条件」）
直す前の文字:
~~~
"条件": "1時間足より長い足（4時間足）でも、`build_features` が新しい部品の列を作れる（番人 T-A3）"
~~~
直した後の文字:
~~~
"条件": "1時間足より長い足（4時間足）でも、`build_features` が新しい部品の列を作れ、4時間足に当てた1時間足の ATR% が、同じ5分足から作った1時間足の値と1本も違わない（番人 T-A3。わざと外した形＝4時間足のバーの ATR% では違いが出ることも、毎回 確かめる）"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:377「1時間足より長い足（4時間足）でも、`build_features` が新しい部品の列を作れる（番人 T-A3）」
状態: 確定

#### 修正 3
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

### Major

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 469行（実装の指示 13 の中身・検査16 の関数の定義の行）
直す前の文字:
~~~
def _insp_tol_saturation(bars: pd.DataFrame, cfg: dict) -> list[str]:
~~~
直した後の文字:
~~~
def _tol_saturation_cells(k, x) -> list:\n    \"\"\"検査16 の1マス＝倍率 k × ATR% の並び x の「値の出ている本数・下端に張り付いた割合・上端に張り付いた割合」（文字）。\n\n    ★2026-09-26（監査 CP44 の修正 4）＝数え方を1か所に置き、番人 T-A5 が既知答えで確かめる。\n    ★張り付き＝下端より小さい（下端に置き換わる）／上端より大きい（上端に置き換わる）。ちょうど端の値は数えない。\n    \"\"\"\n    v = float(k) * np.asarray(x, dtype=float)\n    ok = ~np.isnan(v)\n    nn = int(ok.sum())\n    if nn == 0:\n        return [\"0\", \"—\", \"—\"]\n    return [str(nn), f\"{float((v[ok] < _SR_ATR_TOL_LO).mean()) * 100:.1f}%\",\n            f\"{float((v[ok] > _SR_ATR_TOL_HI).mean()) * 100:.1f}%\"]\n\n\ndef _insp_tol_saturation(bars: pd.DataFrame, cfg: dict) -> list[str]:
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:380「壊すプログラムは付けない（判定しない報告の節）」
状態: 確定

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 469行（実装の指示 13 の中身・1マスの数え方）
直す前の文字:
~~~
                cells = []\n                for x in (own, h1):\n                    v = float(k) * x\n                    ok = ~np.isnan(v)\n                    nn = int(ok.sum())\n                    if nn == 0:\n                        cells += [\"0\", \"—\", \"—\"]\n                        continue\n                    cells += [str(nn), f\"{float((v[ok] < _SR_ATR_TOL_LO).mean()) * 100:.1f}%\",\n                              f\"{float((v[ok] > _SR_ATR_TOL_HI).mean()) * 100:.1f}%\"]
~~~
直した後の文字:
~~~
                cells = _tol_saturation_cells(k, own) + _tol_saturation_cells(k, h1)
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:469「cells += [\"0\", \"—\", \"—\"]」
状態: 確定

#### 修正 6
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 470行（実装の指示 14 の中身・T-A4 の行の直後）
直す前の文字:
~~~
f\"（ATR の期間 {an}・全部 {v_full} ／ 切った {v_cut}）＝未来を見ている\")
~~~
足す文字:
~~~
\n    # ── T-A5＝検査16 の張り付き割合の数え方の既知答え（監査 CP44 の修正 6）──\n    #   倍率 1.0 × [0.001, 0.003, 0.007, 0.0015, 0.006, 空]＝値の出ている5本のうち、下端より小さいのは 0.001 の1本、\n    #   上端より大きいのは 0.007 の1本（ちょうど端の 0.0015・0.006 は数えない）→ [\"5\", \"20.0%\", \"20.0%\"]\n    _c5 = _tol_saturation_cells(1.0, [0.001, 0.003, 0.007, 0.0015, 0.006, float(\"nan\")])\n    if _c5 != [\"5\", \"20.0%\", \"20.0%\"]:\n        ng.append(f\"T-A5: 検査16 の張り付き割合の数え方が既知答えと違う（{_c5}）\")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:7390「ng.append("検査15 T1: 一直線の区間で比が 1.0 にならない"」
状態: 確定

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 431行（DESIGN_CONTRACT の impl_functions の観察の道具）
直す前の文字:
~~~
"_insp_tol_saturation", "inspect_data", "selftest_atr1h", "selftest"]
~~~
直した後の文字:
~~~
"_tol_saturation_cells", "_insp_tol_saturation", "inspect_data", "selftest_atr1h", "selftest"]
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:431「"_insp_tol_saturation", "inspect_data", "selftest_atr1h", "selftest"]」
状態: 確定

#### 修正 8
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 210行（4-7 の表の段5 の行の直後）
直す前の文字:
~~~
"| 段5 | 詰めの刻み | 閾値は刻み1・分位は刻み半分 | 詰めの刻み | 使っていない（段5 は未着手） | 段5 の工事で使う | milestones2 の767行 |",
~~~
足す文字:
~~~

        "| 段5 | 形の線 | 線＝`neighbor_drop_max`（まこさんの判断待ち） | 判定の線（勝った値の前後で束が崩れるかを見る線） | 使っていない（段5 は未着手・milestones2 の3221行でも未決） | 段5 の工事で使う。数字は まこさんが決める（この工事では書かない） | milestones2 の767行 |",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:767「線＝`neighbor_drop_max`（まこさんの判断待ち）」
状態: 確定

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 209行（4-7 の表の段3 の解除の緩め幅の行）
直す前の文字:
~~~
"| 段3 | 解除の緩め幅 | `_loose_q` の分位差 | 閾値（分位の差） | `_loose_q` | 変えない | milestones2 の765行 |",
~~~
直した後の文字:
~~~
"| 段3 | 解除の緩め幅 | `_loose_q` の分位差 | 閾値（分位の差） | `_loose_q_fixed`＝出る線を入る線の隣の段（分位1つ差）に決め打ち・乱数なし（`engine_tuner_gen.py` の `_flip_loose` と、状態を保つ形の出る線 `off_c`）。§2.2 の文の `_loose_q`（緩い側の範囲から引く形）は、場面の判定の束では使っていない | 変えない（いまは分位1つ差の1点） | milestones2 の765行 |",
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3092「out["value"]["threshold_q"] = _loose_q_fixed(limits, c["value"]["threshold_q"], c["side"])」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

### Minor

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 208行（4-7 の表の段3 の持続の本数の行の「いまの engine_tuner」の欄）
直す前の文字:
~~~
| 組む側は `int_range`（3〜24）から取る |
~~~
直した後の文字:
~~~
| 持続（何本 続いたか＝streak）の n は `int_range`（3〜24）から取る（`build_stage_candidates` の段3）。状態を保つ形（hysteresis）の真を保てる最大の本数 n は `state_hold_bars_range`（24〜288）から取る（`engine_tuner_gen.py` の3331行） |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:3331「"value": _nv_fixed(limits, "state_hold_bars_range", "n", order_n)}」
状態: 確定

#### 修正 12
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 195行（4-7 の表の段1 のタッチの行の「いまの engine_tuner」の欄）
直す前の文字:
~~~
| 閾値は分位だけ（`quantile_range` の q10〜q90・いまは q50 の1点） |
~~~
直した後の文字:
~~~
| 組む側が作る閾値は分位だけ（`quantile_range` の q10〜q90・いまは q50 の1点）。実行器は名前つき定数 × 倍率（例＝`SCALP_FLOOR` 0.08%）・整数（`n`）・連動（`ref`）も読めるが、組む側はそれを作らず、範囲を書く置き場も無い |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:800「known = {"threshold_q", "const", "mult", "side_sign", "n", "legacy", "direction", "dir", "na", "offset",」
状態: 確定

#### 修正 13
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 215行（4-7 の「表の読み方」）
直す前の文字:
~~~
「閾値」は、engine_tuner がいま分位でしか持てません（生の値の閾値を書く置き場が無い）。
~~~
直した後の文字:
~~~
「閾値」は、組む側（`engine_tuner_gen.py`）がいま分位でしか作りません（生の値の閾値の範囲を書く置き場も無い。実行器は名前つき定数 × 倍率・整数・連動も読める）。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py:800「known = {"threshold_q", "const", "mult", "side_sign", "n", "legacy", "direction", "dir", "na", "offset",」
状態: 確定

#### 修正 14
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 344行（決めたことと理由 の3番目の直後）
直す前の文字:
~~~
"捨てた案": "バーの始まりの時刻で当てる。捨てた理由＝まだ閉じていない1時間足を使う（未来を見る）"},
~~~
足す文字:
~~~

    {"決めたこと": "1時間足の ATR は観察の道具の `_atr`（Wilder の平滑・材料カタログの ATR% と同じ式）で作り、割る終値はその1時間足の終値にする", "理由": "出どころの逐語 `tol=clamp(K×ATR%_1h,0.15%,0.6%)` は平滑の式を書いていない。材料カタログの ATR% と同じ式にそろえる。形の手本の RG-v6 `_adaptive_tol_1h` は14本の単純平均（`rolling(14).mean()`）で、値が出る前を定数で埋める＝その2つは持ち込まない（違反の記録 #23）", "捨てた案": "RG-v6 と同じ14本の単純平均。捨てた理由＝ATR の期間は まこさん決定 2026-09-26 の②（7〜21）で14本に限らない。平滑の式を部品ごとに変えると、同じ ATR% という名前で別の値になる"},
~~~
根拠の抜き書き: v3-bitget-api-sdk/scripts/dashboard/build_regime_gate_rg.py:268「atr = pd.Series(tr).rolling(14).mean().to_numpy()」
状態: 確定

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 381行（完成の条件 #8 のコマンド）
直す前の文字:
~~~
! grep -q '1時間ATR.*と実質 同じ' .claude/ratchet/material_ranking.json
~~~
直した後の文字:
~~~
grep -q '1時間ATR' .claude/ratchet/material_ranking.json && ! grep -q '1時間ATR.*と実質 同じ' .claude/ratchet/material_ranking.json
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:381「! grep -q '1時間ATR.*と実質 同じ' .claude/ratchet/material_ranking.json」
状態: 確定

#### 修正 16
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 416行（塞げないもの の「直に呼ぶ道」の行）
直す前の文字:
~~~
"塞げないこと": "止まります（値は出さない）。黙って違う値は出しませんが、その呼び方では列が作れません。いまそういう呼び手は在りません（grep で数えた呼び手は、ほかは全部5分足）"
~~~
直した後の文字:
~~~
"塞げないこと": "置き場が空か、置き場の5分足が期間を覆っていなければ止まります（値は出さない）。★ただし同じプログラムの中で、先に列を作る道が置き場に入れた5分足がその期間を覆っているときは止まらず、その5分足から1時間足を作ります（置き場の5分足が、渡された足と同じデータかは見ません）。いまそういう呼び手は在りません（grep で数えた呼び手は、ほかは全部5分足）"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:416「止まります（値は出さない）。黙って違う値は出しませんが」
状態: 確定

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 338行（決めてほしいこと の2番目の直後）
直す前の文字:
~~~
"出どころ": "milestones2 の764行・まこさん決定 2026-09-11「じゃあ、まず１点でつくる」・2026-09-26 の③"}
~~~
足す文字:
~~~
,
    {"中身": "出口の表の承認（`gen_exit_families.py --approve`）。まこさん決定 2026-09-26 の④は「型の表の承認は まこさんが1回 打つ」でした。出口の表は型の表の部品の数と標本不足の組の数を中に書く（`gen_exit_families.py` の406行・409行）ので、部品を足すと作り直しと承認がもう1つ要ります。★決定④のときに私が挙げていなかったものです", "私の案": "型の表と出口の表の `--approve` を2つ打っていただく（出口の表を作り直さないと、完成の条件 #18 の照合が落ちる）", "出どころ": "`pre_audit_check.py` の ORDER（まこさんの承認が要る作り直しが2件）・`gen_exit_families.py` の406行・409行"}
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_exit_families.py:406「parts_count=len(sig.get("parts") or []),」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

## 9. CC プロセス欠陥対策

### Process

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 363行（リスク の8番目の直後）
直す前の文字:
~~~
"どうするか": "M2-F-13・M2-F-14 の前に決める（next_step に書く）"},
~~~
足す文字:
~~~

    {"中身": "実装の指示の中身（当てた後のコード）を、承認の前に一度も走らせていない（CC の自己申告1。監査 CP44 も読み取りだけの役割で、写しを作って走らせられなかった）", "どうするか": "承認の後、本物に当てる前に、作業場の写しに実装の指示を当て、`py_compile`・`observe_diag.py --selftest-atr1h`・壊すプログラム4本を写しで走らせ、出力を worklog に残す。1件でも落ちたら本物に当てずに まこさんに報告する"},
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:368「★測っていない。当てる処理は道具が数秒で終わる」
状態: 確定

#### 修正 20
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 364行（リスク の最後の直後）
直す前の文字:
~~~
"どうするか": "決定の前の前提を表す語（2時間足〜1日足では作らない・案(a)・1分足〜1時間足でだけ）で元データの全部の行を grep し、当たった行を1行ずつ全文で読んで揃える"}
~~~
足す文字:
~~~
,
    {"中身": "まこさんに決めてほしいこと（承認を何回 打つか）を出す前に、承認の要る作り直しを数えていなかった（出口の表の承認を落とした＝CC の自己申告3）", "どうするか": "決めてほしいことを出す前に、`pre_audit_check.py` の ORDER のうち まこさんの承認が要る行（種類が approve の行）を grep で数え、その全部を決めてほしいことに並べる"}
~~~
根拠の抜き書き: .claude/tools/pre_audit_check.py:48「("gen_exit_families.py --write", "approve",」
状態: 確定

#### 修正 21
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify」
状態: 確定

## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

**監査の形（正直に）**：依頼書の auditor 宣言のとおり、auditor のセッションの CC が Plan サブエージェントを cold start で起動し、監査は Plan サブエージェントが行いました（1回・約47分）。Plan サブエージェントは読み取りだけの役割で起動され、ファイルを1つも作れませんでした。そのため、依頼書が勧めた「作業場の写しに実装の指示を当てて走らせる確認」は、していません。所見の中の「データ不足（理由：走らせていない）」は、この理由です。

**auditor のセッションの CC が、結果に写す前に確かめたこと**（恒久の決まり72番）
- 修正の「直す前の文字」16件（修正1・2・4・6〜9・11〜17・19・20）を、元データの中で出てくる回数で数えた（`grep -o -F … | wc -l`）＝全部 1回。修正5 は当てる道具の `--dry` で確かめた（下の「走らせたコマンド」）。
- 所見と修正に出てくる「ファイル名:行番号」を、全部 実物で前後つきで開いた（sed と Read）。
- ★1か所だけ、Plan サブエージェントの所見の行番号が実物と合わなかったので、写すときに直した＝A4-b の当てる道具の行（所見では「apply_audit_fix.py:490〜495・537〜539」。実物は、当てる直前の見直しが488〜497行、壊すプログラムを当てない一覧 `NEVER_WRITE` が67〜73行、終了コード1 が535行。537〜539行は自己テストの見出しの行）。所見の中身は変えていない。
- 所見の「milestones2.md:行番号」は、実物のファイル名 engine_tuner_milestones2.md に揃えて書いた。
- A2-a の③（RG-v6 が値の出る前を埋める値）は、Plan サブエージェントの所見では「0.003」でした。実物（build_regime_gate_rg.py の269〜270行）は `v17.ZONE_TOL` という別のファイルの定数で、その値を CC は開いて確かめていないので、「定数（`v17.ZONE_TOL`）」と書き、修正14 の文も「定数で埋める」にした。
- 修正1 のコードが使う名前（`big`＝値決め窓の5分足の末尾30,000本・`cfg`・`_resample`・`_atr`・`_H1_BASE`・`_atr_pct_1h_on`）が、足す場所（実装の指示14 の `if cat:` の中）で使えることを、実装の指示14・1 の中身を開いて確かめた。4時間足の道と5分足の道は、どちらも置き場の5分足の全部から同じ1時間足と ATR を作るので、正しい形では差が0になる。

**Plan サブエージェントが開いたファイル**（パスは SDK＝v3-bitget-api-sdk/bitget-python-sdk-api）
- 依頼書 1〜474（全文）／ `.claude/state/acceptance.md` 1〜1804（全文）／ acceptance_src.json 1〜120・316〜456（Read）、120〜483（sed で要約）、457〜481（生の文字）
- next_step.md 38・201
- observe_config.json 1〜30・105〜135・215〜275
- observe_diag.py 95〜115・170〜240・260〜280・370〜435・680〜730・840〜870・1203〜1345・1545〜1560・1640〜1760・3625〜3665・3712〜3745・3800〜3975・4060〜4200・4455〜4630・4838〜4985・5705〜5730・5839〜5845・5876〜6020・6420〜6450・6880〜6891・6936〜7010・7440〜7525
- indicator_reference_diag.py 50・59〜66・100〜140・655〜672・850〜900・1195〜1250・4440〜4470・4755〜4775・4930〜4975
- build_regime_gate_rg.py 240〜300
- engine_tuner_gen.py 136・192〜304・440〜470・490〜500・625〜650・1699〜1712・1724〜1746・2775〜2890・3080〜3095・3280〜3331・3915〜3945・6305〜6340
- engine_tuner_exec.py 180〜300・795〜880・1960〜2010・2030〜2050
- gen_signal_families.py 34・82〜200・650〜670 ／ gen_exit_families.py 574〜602（406・409 は grep）／ gen_composition_rules.py 25〜50・195〜225・269〜300・370〜390 ／ gen_indicator_switch.py 253〜335（grep）／ gen_materials.py 1〜80・84〜90・700〜775 ／ gen_observe_manual.py 150〜175・236〜244・525〜545
- pre_audit_check.py 40〜90 ／ gen_regime_kb.py 1092〜1150 ／ apply_audit_fix.py 1〜100・128〜540 ／ approve_impl.sh 440〜530 ／ list_banned_words.py 1〜200 ／ block_uchikiri.sh 40 ／ block_premature_giveup.sh 49・56・72 ／ enforce_signal_table_gate.sh 1〜40
- lib.sh・b77・b53（全文）、b39・b40・b55〜b58・b60・b61・b63〜b65（探す文字）
- engine_tuner_milestones2.md 750〜775・1788・2870〜2895・3220〜3242 ／ search_limits.json 1〜60 ／ m2c4 の控え 40〜60 ／ cp22 の再監査 360〜400 ／ cp43 の結果 480〜555 ／ permanent_rules.md 345〜396 ／ worklog 20260926 231〜305 ／ regime_detection_kb.md 1280〜1300 ／ engine_tuner_requirements.md 40〜52 ／ cat_requirements.md 545・591（H2・H6）／ _template.md 229〜236
- 出どころの戦略ファイル（sr_tol の説明が指すもの）205〜220・515〜540・560〜600・620〜660 ／ cp36_work の setup_mirror.py 1〜30・run.sh 1〜20

**auditor のセッションの CC が開いたファイル**（結果に写す前の確かめ）
- acceptance_src.json 1〜8・190〜220・333〜349・358〜386・411〜436・464〜475、457行（実装の指示1）・469行（実装の指示13）・470行（実装の指示14）の中身
- observe_diag.py 90〜100・201〜211・266〜276・414〜424・1550〜1560・1719〜1736・4075〜4102・4145〜4156・4840〜4850・5895〜5920・6009〜6021・6431〜6448・6974〜6997・7375〜7395
- engine_tuner_gen.py 624〜650・1694〜1738・2818〜2828・3087〜3097・3293〜3336・3922〜3937・6316〜6326 ／ engine_tuner_exec.py 260〜270・790〜805・1955〜1974・2039〜2050・4580〜4590
- engine_tuner_milestones2.md 756〜772・807〜817・1783〜1793・3216〜3226（と grep で 767・812・1788・3221）
- gen_signal_families.py 94〜139 ／ indicator_switch.json 64〜75（`.on` は22行から＝69〜70行は `.on` の47・48番目）／ gen_materials.py 708〜722 ／ build_regime_gate_rg.py 257〜273 ／ indicator_reference_diag.py 45〜55・4944〜4954 ／ gen_composition_rules.py 201〜215 ／ gen_exit_families.py 401〜414 ／ gen_indicator_switch.py 264〜274 ／ permanent_rules.md 376〜392 ／ condition_parts_diag.py 498〜508
- gen_regime_kb.py 1121〜1135 ／ pre_audit_check.py 40〜59 ／ apply_audit_fix.py 1〜103・485〜544 ／ approve_impl.sh 461〜511 ／ gen_audit_docs.py 1〜150・551〜790

**走らせたコマンドと結果**
- Plan サブエージェント：`shasum`（2回・1秒未満・一致）／ `gen_exit_families.py --verify`（rc=0・4.59秒）／ `gen_composition_rules.py --verify`（rc=1・3件・2.25秒）／ 事実データの grep 一式（1秒未満）／ 直す前の文字21件の `grep -c -F`（全部 1）／ 修正の直す前の文字の `grep -c -F`（修正1・2・4〜9・11〜17・19・20 の全部が 1。修正15 は `$'…'` で引用して数えた）／ 根拠の行の照らし（全部 1）／ hook による自動実行 `require_design_check_before_approval.py --try`（13.1秒・不足1件＝この監査のセッションの読み取り記録による）／ WebSearch 3回（1回はドメインの拒否）／ WebFetch 5回（2回は 404）
- auditor のセッションの CC：`shasum -a 256`（設計書と元データ・1秒未満・一致）／ 修正の直す前の文字16件の `grep -o -F … | wc -l`（全部 1回・1秒未満）／ `gen_audit_docs.py result`（骨組みを作った・1秒未満）／ `gen_audit_docs.py check`（食い違い0件・1秒未満）／ `gen_audit_docs.py form`（形の食い違い0件・1秒未満）／ `apply_audit_fix.py --report cp44_work/cp44_result.md --severity Critical,Major,Minor,Process --dry`（当たる17件・走らせるコマンド4件・実物と合わない件0＝当てた後の中身でも確かめた・数秒）／ 作業場の `cp44_work/cp44_json_probe.py`（読むだけ・当てる道具と同じ関数 read_fixes・apply_one で、元データの文字の写しに17件を番号の順に当てた＝JSON として読めた〔実装の指示25件・決めてほしいこと3件・決めたことと理由12件・リスク11件〕・実装の指示13・14 の中身が Python の文法を通った・本物の元データの sha256 は 8be0c799… のまま・数秒）。★文法を通ることまでで、当てた後のコードを走らせてはいない

**走らせられなかったもの**：作業場の写しの作成、実装の指示の適用、py_compile、`--selftest-atr1h`、`--inspect … --only 3,13／4／16／12`、`--selftest`、壊すプログラム4本、`gen_acceptance.py --write`、`pre_audit_check.py --check-design／--run`。
- 理由①：監査の Plan サブエージェントは読み取りだけの役割で、ファイルを1つも作れない。
- 理由②：hook が `python3 -c`・ヒアドキュメント・`.claude/tools/*.py` の実行を止める。
- 理由③：同じ相手の照合は1セッション1回（恒久の決まり72番の3）。写しで走らせる確認をもう一度 頼むかは、まこさんが決める。

## 11. 本物のファイルを書き替えていないこと

- 追跡中のファイルの変更（` M`）は **0行** です。設計書と元データの sha256 は、監査の始めと同じです（1節）。
- この監査で新しく出来たのは、作業場の `cp44_work/cp44_result.md`（この結果の下書き）・`cp44_work/cp44_json_probe.py`（読むだけの確かめ・10節）と、結果ファイル `.claude/audits/2026-09-26_m2e_bundle2_design_cp44_audit_report.md`（この出力を取った後に1回だけ書く）の3つだけです。`cp44_work/cp44_src.md` は依頼を出した CC が作って commit 済み（`5b7663d`）のものです。
- 監査の途中に、別の場所で commit `5b7663d`（2026-09-26）が作られたため、監査の始めに在った ` M` の6行（next_step.md ほか）は消えています。この監査は1つも書き替えていません。
- 下は `git status --short` の出力です。`cp39_work/` の未追跡の行（約100行）は、前の監査の作業場の既存のファイルで、1行にまとめました（個々の行は監査の始めと同じ）。

```
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
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp39_work/（anchors/・apply_*.py・cite_list.py・cmp_g7.py・cp39_final.md・cp39_result.md・fixes_blocks.md・make_fixes.py・manifest*.json・merge_result.py・mirror*/・parts/・patch_make_fixes*.py・plan_findings.md・pristine*/・probe_*.py・put_src.py・run*.sh・sec10_main.md・sec11*・setup_mirror*.py・src_*・ws_map.py）
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp40_work/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/count_after.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/mirror/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/pristine/
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp43_work/cite_list_probe.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp43_work/cp43_final.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp43_work/cp43_result.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp43_work/plan_findings.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp43_work/sec11_note.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp44_work/cp44_json_probe.py
?? v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp44_work/cp44_result.md
?? v3-bitget-api-sdk/bitget-python-sdk-api/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_L1.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e37_v59.log
?? v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_e38_S2.log
?? v3-bitget-api-sdk/results/
```

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-26_m2e_bundle2_design_cp44_audit_request.md request_sha256=d16c2ff963ff109c79e71a68c320b981022277cac3954af45145ccf72d046a49 -->
