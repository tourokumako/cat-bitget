# 監査結果 cp45 — CP45 — 束2 の実装（帯の許容幅を1時間足の値動きの幅で決める新しい部品 S-Rタッチ1時間ATR・張り付き割合を出す検査16・M2-E-1b の表）は、承認済みの設計書 m2e-bundle2-20260926 の決めた動きをしているか。設計書と実装の食い違いを、まとめて直せる形で洗い出す

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-26_m2e_bundle2_impl_cp45_audit_request.md`
- 依頼書のハッシュ値: 729e28182e1d0d83336de6464112aadc2c1ac71647c96a637240a162c8269291
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 bf964dd30ccd4ad84f6b45145fd08a340ac28edef79a07b2f177e322f90b6f62
- 監査が照らしたハッシュ値: bf964dd30ccd4ad84f6b45145fd08a340ac28edef79a07b2f177e322f90b6f62（`shasum -a 256 .claude/state/acceptance.md`・1853行・目印 `m2e-bundle2-20260926`）。依頼書の値と一致する。承認の印 `.claude/state/acceptance.approved` の中身も同じ値。★依頼書は「まだ commit していない」と書くが、実装はその後 `32dd9a5`（2026-09-26 23:03:05）で commit 済み。`git diff 5b7663d` の差は同じ。
- 実施日: 2026-09-26


## 2. 監査対象の型宣言

- **コード型**＝`observe_diag.py`・`indicator_reference_diag.py`・`observe_config.json`・`engine_tuner_gen.py` の差（`git diff 5b7663d`）と、壊すプログラム b104〜b107・`lib.sh`。
- **数値型**＝既知答え3件（見本1〜3）、検査16 の張り付き割合（99行）、成績表の分離力、T-A5 の既知答え。
- **文書型**＝設計書（`acceptance.md`）と元データ（`acceptance_src.json`）、作り直した表と文書（型の表・出口の表・読み込ませる法則の文書・印・成績表・材料の文書・§2.2-0）。


## 3. 監査対象の事実データの確認

### 監査対象の事実データ（依頼を出した CC が走らせたもの・まこさんが打ったもの）

| # | 依頼書の行 | 監査が確かめた結果 |
|---|---|---|
| 1 | まこさん・写しの番人と b104〜b107 | 写しは走らせていない（監査の Plan サブエージェントは読み取り専用）。写し `cp44_work/mirror` の observe_diag.py・indicator_reference_diag.py・observe_config.json と b104〜b107 の sha256 は、本物と全部同じ（3f2d3c7e…／d4f13163…／99d918a1…／a88c09d7…／7915ee53…／3d6c9312…／3c1e027c…）。本物での機械の記録は `acceptance_archive/m2e-bundle2-20260926.breaks.json` の6〜41行で、b104〜b107 はどれも code=1・match=true。★写しの出力そのものはデータ不足（理由＝ファイルに残っておらず、worklog 4-8 の転記しか無い） |
| 2 | `apply_audit_fix --design` で21件 | 本物と写しの sha256 は、上の4本と壊すプログラム4本で一致。engine_tuner_gen.py だけが違い（写し 0ef33e67…／本物 d3b7c903…）、これは後で T23② を直した分と合う。「当たる21／当てない4」の出力そのものはデータ不足（理由＝当てる道具は `.claude/tools` の .py で走らせていない） |
| 3 | `--selftest-atr1h` | 本物で走らせ直した。rc=0・5秒。「登録 18 件 ／ 値決め窓の5分足 158112 本 ／ T-A4 で切った時点 5 か所」「全部 pass（❌ 0件）」＝依頼書と一致 |
| 4 | 検査3・13 | 走らせ直していない（`--inspect` は記録を書き、前の記録を archive へ移す）。CC の記録 `observe/archive/observe_inspect_…_20260926.txt` の1050行「3区分（指標 18 種）: 一致検証済み 18 / 性質検証のみ 0 / 未検証 0」、1074行「値が変わった列…= 0 種」、1078〜1079行「✅ 検査3／検査13: 異常なし」＝一致 |
| 5 | 検査4（198列） | 記録 `…_prev002.txt` に「全 198 列 → 不一致 0 列」＝一致。★切った時点 `['2026-06-30 23:55:00', '2026-06-30 15:40:00', '2026-06-29 14:40:00']` の1つ目はデータの最後のバー（切る時点は `span.index[-1]`・`[-100]`・`[-400]`）で、実際に切っているのは2時点（A1-a）。7分26秒は記録の時刻（18:25→18:33）と矛盾しない |
| 6 | 検査16 | 記録 `…_prev003.txt` の99行（11足×期間3×倍率3）を全部読んだ。②の実数＝倍率0.5 下端 1.3〜6.2%・上端 7.4〜10.0%／倍率1.0 上端 53.9〜62.5%／倍率1.5 上端 83.2〜90.0%。★依頼書の「倍率1.0 上端 約56〜63%」には 6h・期間7 の 53.9% が入っていない |
| 7 | 検査12 | 記録 `observe/observe_inspect_…_20260926.txt` に「実質 同じもの = 0 組 ／ 近い組 = 19 組」。19組に新しい部品は0組＝一致。★この検査は5分足だけを測る（「20000 本 × 571 列（5m）」） |
| 8 | 型の表・出口の表（まこさん） | `gen_signal_families.py --status`＝「✅ 承認済み（中身の md5 ffc10b58…）」で approved.txt と一致。exit_families.json の md5 12dcb1b4… は exit_families_approved.txt と一致。signal_families.json の時刻 18:49:05。★打ったときの出力そのものはデータ不足（貼られていない） |
| 9 | composition `--verify` | 走らせ直した。rc=0・2秒・「✅ 改変なし・正本とのずれなし」 |
| 10 | 印 141／117 | jq で `.on`＝141・`.off`＝117＝一致 |
| 11 | 成績表の全走＋需給 | 記録 `archive/observe_…_prev011.txt` のループは 130.7分・「測れた列 6299 ／ 載った列 6179」。需給を足した後は「6302 ／ 6182・足した行 18」。成績表に需給の行は18件、`material_ranking.before_add_demand.json` には0件。★「location の1位 (144,1.5,21)__15m（0.745）」は同点で、`(144,1.5,7)__15m` も 0.745。組む側の `ranked_materials` は同点を名前の順で並べる（engine_tuner_gen.py:1393）ので (144,1.5,21) が1位になる。全体の 2時間16分19秒はデータ不足（記録に全体の時間が無い） |
| 12 | 組む側の自己テスト（直す前後） | 走らせていない（約6分・書き込みの有無を確かめきれていない）。コードでは、見本（engine_tuner_gen.py:6322）が `ranked_materials("location")` の先頭（上の同点の並べ方）と合う |
| 13 | G2・H2 | g2_pass.json の指紋 52e14be0…（22:51:30）、h2_pass.json 1df1d36a…（22:56:21）＝一致。「照合できる列 2個」の実走はデータ不足（G2 の `--verify` は g2_pass.json を書く＝gen_signal_families.py:942） |
| 14 | #8〜#19 | #8・#9・#10・#18・#19 を走らせ直し、全部通った（10節）。#11・#13・#17 は pre_audit_check.json（22:59:52）の rc=0 と、対象ファイルの最終書き替え時刻がどれもそれより前であることで確かめた。#12・#14〜#16 はデータ不足（worklog だけ） |
| 15 | 承認③ | acceptance.approved＝bf964dd3… で設計書と一致。acceptance.md の1577〜1580行が #1〜#4「✅済」、breaks.json の #1〜#4 が code=1・match=true |


## 4. 所見

### 一般の観点

- ①統計学的妥当性 ＝ PASS（新しい統計の線を作っていない。検査16 の数え方は「下端より小さい／上端より大きい・端ちょうどは数えない」＝observe_diag.py:4934〜4937 で、部品の clip と合う）
- ②リスク管理 ＝ PASS（売買を回さず、net にも審判にも触れていない）
- ③認知バイアス ＝ FAIL（G2 の数が減った原因を「成績表」と見立てたが実物は印の作り直し＝自己申告6。7-3b が「点の一覧に当たりません」と書くが、機械の数え方では1件増えている＝修正14）
- ④ソフトウェア工学 ＝ FAIL（T-A3 の突き合わせが build_features の道を通らない＝修正1〜5。T-A5 の既知答えは下端と上端が対称＝修正8）
- ⑤再現性 ＝ PASS（乱数0件。番人は本物で rc=0・5秒。設計↔実装の突き合わせは齟齬0件）
- ⑥実行プロセス ＝ FAIL（需給の足し直しが設計書の手順に無い・承認の回数が違う・型の表の `--write` を誰が打つかが違う＝修正6・11〜13・19・20）
- ⑦主エージェントバイアス ＝ FAIL（CC も CP44 も「関数 `_atr_pct_1h_on` の道」だけを守り、「build_features が置き場に何を入れるか」を守りの外に残した。CP44 の A3-d と同じ型＝修正1〜5）

### A0 — 壊すプログラム4本（b104〜b107）と番人 T-A1〜T-A5 が、測ると言っているものを本当に測っているか（優先度 A）

- **A0-a｜指摘なし。**見本3 は倍率1.5 の6件だけが割れる。1時間足の ATR% は 0.49%台 × 1.5 で上端 0.6% に張り付き数は n、5分足の ATR% では下端 0.15% に張り付き数は n/2。落ちる理由は許容幅の元の違いそのもの（indicator_reference_diag.py:728「t3 = min(max(k * a3 / 100.5, 0.0015), 0.006)」）。見本1・2 はどちらの足で測っても同じ答え。本物の記録＝breaks.json:10 の最後の行は「❌ T-A2: …(288,1.5,21) が教科書の式と違う（最大差 238.0）」だが、出力に EXPECT_MSG「❌ T-A1」を含み match=true（run_breaks.py:463〜466）。
- **A0-b｜指摘なし（走らせていない・コードで判定）。**「1本 前」（`a.index = h1.index + 2h`）は未来を見ないので T-A4 は通り、既知答え3 も上端 0.6% のままで T-A1 も通る。落ちるのは T-A2（教科書の式の時刻の当て方＝indicator_reference_diag.py:693〜694 と値が割れる）。「2本 先」（`h1.index - 1h`）は切ったデータに次の1時間足が無いので T-A4 が落ち、T-A2 も落ちる。＝時刻の誤りは、未来に向く分を T-A4、過去に向く分を T-A2 が受け持つ。
- **A0-c｜指摘なし（走らせていない・コードで判定）。**下限だけ外す＝見本1（ATR 0）で許容幅 0 になり、`l ≤ c+0` が 100.1≤100.0 で偽なので数が n から 0 に変わり、T-A1 が18件とも落ちる。上限だけ外す＝見本2 で許容幅が 1.96〜5.9% になり全部触れるので数が 0 から n に変わり、T-A1 が18件とも落ちる。
- **A0-d｜Critical。**T-A3 の2つ目（4時間足の突き合わせ）は、突き合わせる直前に自分で置き場へ5分足を入れ直している（observe_diag.py:6645「_H1_BASE["bars"] = big」）。そのため、build_features が置き場に入れた中身（observe_diag.py:1760「_H1_BASE["bars"] = bars」）を一度も見ていない。壊し方の例＝1760行を4時間足のバーを入れる形（`_resample(bars, "4h")`）に変える。覆いの判定（observe_diag.py:448〜453）は先頭と末尾が同じなので通り、4時間足に当たる値は「その4時間足のバーの ATR%」＝2026-09-06 に外した誤りと同じ形になる。それでも T-A3 の1つ目は「列が空でない」で通り、2つ目は置き場を入れ直すので通る。T-A1・T-A2・T-A4 は5分足だけ、検査3・13 も5分足、検査4 は切っても切らなくても同じ誤り、検査16 は insp5_frame の別の行（1747行）を使い、H2 は 5m・15m の案だけ＝どれも落ちない。完成の条件 #4 の文「`build_features` が…列を作れ、4時間足に当てた1時間足の ATR% が…1本も違わない」の後半を、build_features の道で測っていない。★監査を起動した側でも observe_diag.py:436〜470・1744〜1762・6630〜6656 を開き、6645行の入れ直しと覆いの判定の形を確かめた。
- **A0-e｜Minor（走らせていない・コードで判定）。**T-A5（observe_diag.py:6675〜6676）の見本で、①下端と上端の比べ方を入れ替える→["5","60.0%","60.0%"]で落ちる ②割る数に NaN を含める→16.7%で落ちる ③`<` を `<=` にする→下端 40.0%で落ちる ④戻り値の下端と上端の欄を入れ替える→["5","20.0%","20.0%"]のままで**通る**（見本の下端と上端がどちらも1本＝20.0% で対称のため）。
- **A0-f｜指摘なし。**lib.sh:59「trap _restore EXIT」で途中で落ちても戻し、48〜51行で戻した後の sha256 を照らして合わなければ exit 99。本物の observe_diag.py の sha256 は承認の後も 3f2d3c7e…（worklog 4-9 の値）のまま。

修正の番号＝1・2・3・4・5・8

### A1 — `_atr_pct_1h_on` と置き場 `_H1_BASE` が、未来を見ず、どの足にも正しい1時間足の値を当てるか（優先度 A）

- **A1-a｜指摘なし。**1時間足の値の時刻は「始まり＋1時間」（observe_diag.py:454「a.index = h1.index + pd.Timedelta("1h")」）で、各バーにはそのバーが閉じた時刻までの最後の値を当てる（455行「a.reindex(d.index + step, method="ffill")」）。上位足は build_features が閉じた時刻へずらしてから5分足へ写す（1784〜1786行）。T-A4 は毎時30分の5か所 × 期間3つを連続の値で 1e-12 まで比べ、監査の本走でも通った。★検査4 はこの誤りを見抜く力が弱い＝①比べる相手はタッチの数（整数・observe_diag.py:4149〜4156 の全列の比べ）②切る3時点のうち1つはデータの末尾で、実際に切っているのは2時点（15:40・14:40）。設計書の「決めたこと」7番もタッチの数の鈍さを書いている。時刻の行は5分足の道と長い足の道で共通なので、主な守りは T-A4。
- **A1-b｜指摘なし。**1分足・3分足＝1時間足は1分足の元データから作る。検査16 の②は 1m〜1h で同じ割合（例＝期間14・倍率1.0 の上端は 1m・3m・5m・10m・15m・30m・1h の全部で 58.9%）＝同じ1時間足の値が当たっている。長い足＝T-A3 の2つ目で、4時間足が閉じた時刻の値が5分足から作った値と 1e-12 まで一致（本走で通過・ただし A0-d のとおり置き場は入れ直した後）。2h・6h・1d を数値で一本ずつ比べた番人は無い＝データ不足（理由＝比べる番人が4時間足だけ）。検査16 の②は 2h・6h・1d でも 1h と±4pt 以内（6h・期間7・倍率1.0 が 53.9%、1h は 56.0%）。
- **A1-c｜指摘なし。**覆っていないときは止まる（observe_diag.py:448〜453「raise ValueError("1時間足より長い足には、…」）。置き場は build_features（1760行）と insp5_frame（1747行）が呼ばれるたびに入れ直す。成績表の全走（6021行）・実行器（engine_tuner_exec.py:2045）・組む側（engine_tuner_gen.py:3932）・検査4（4134・4151行）は全部 build_features を通る。部品の関数を直に呼ぶ所（587・3959・5465・5471・6603・6621行）はどれも5分足か合成の5分足。残る道（覆っていれば別の中身でも止まらない）は設計書 7-4 が書いている。
- **A1-d｜指摘なし。**検査4 はこの部品を198列とも通った（記録）。H2（leak_causality_diag.py）の案は恒等3本と、種を決めて作った 5m・15m の案（321〜341行）で、新しい部品を必ず通るとは言えない（設計書も H2 でこの部品を測るとは書いていない）。

修正の番号＝なし

### A2 — 部品の形（許容幅の式・挟み方・タッチの数え方）が、136番の逐語と出どころの逐語どおりか（優先度 A）

- **A2-a｜指摘なし。**許容幅＝`(k * atr_pct).clip(lower=_SR_ATR_TOL_LO, upper=_SR_ATR_TOL_HI)`、タッチは `_sr_touch(d.close, d.high, d.low, win, …)`＝渡された足の高値・安値で数える（observe_diag.py:466〜468）。136番の逐語どおり。
- **A2-b｜指摘なし。**教科書の式（indicator_reference_diag.py:662〜700 の `_tb_sr_touch_atr1h`）は観察の道具を import せず、1時間足への束ね・Wilder の平滑・時刻の当て方を自分で書いている。既知答え（705〜732行の `_known_sr_touch_atr1h`）を手で計算した＝見本1＝n、見本2＝0、見本3＝期間7・14・21 の ATR（59本目）は 0.4999・0.4937・0.4720 で、100.5 で割ると倍率0.5・1.0 は 0.5% 未満なので n/2、倍率1.5 は 0.6% に張り付くので n。★教科書の式は5分足しか扱わない（694行の「+ pd.Timedelta("5min")」）。1m・3m・長い足の式の突き合わせは T-A3 の4時間足の1本だけ。
- **A2-c｜指摘なし。**`_reg("S-Rタッチ` は900行（S-Rタッチ数）と908行（新しい部品）の2件だけ。設定に `sr_atr_k` は無く、`_sr_atr_k_外した記録` と `sr_atr1h_k` は別の鍵（observe_config.json:256・257）。参照表の新しい正規表現「S-Rタッチ1時間ATR\(」（indicator_reference_diag.py:1313）は外した名前に当たらない。

修正の番号＝なし

### A3 — 作り直した表と文書が、いまの部品と一致しているか（優先度 A）

- **A3-a｜指摘なし。**型の表の `parts` に18種が入り、禁止3 の組（窓144 は 4h・6h・1d、窓288 は 2h〜1d）も入っている。承認は `--status`「✅ 承認済み（中身の md5 ffc10b58…）」、出口の表は md5＝approved.txt。#18 は rc=0。
- **A3-b｜指摘なし。**印の「使う」は141で新しい部品が入っている（#10 true）。#19 の `--verify` は「✅ 改変なし・正本とのずれなし」。
- **A3-c｜指摘なし。**成績表は「測れた列 6302 ／ 載った列 6182」で需給の行は18件。§2.2-0 の812行「| `S-Rタッチ1時間ATR` | 22 |」、materials.md に2件、observe_diag_manual.md に4件。
- **A3-d｜指摘なし（この工事の欠陥ではない）。**G2 の見本の構造は `_real_structures(30, seed=20260807)` が作る（gen_signal_families.py:841〜856）。これは `sample_structure` を場面の判定の束を作らずに呼び（853行）、材料の袋 `material_pool` から種つきで引く。袋は印で絞られる（`ex.indicator_enabled`）。4-16 の G2（13個）は印を作り直す前（4-17 で 140→141 種）、4-21 の G2（2個）は後。減った原因は印の1種の追加で袋が変わり、同じ種で引いた最初の構造が変わったこと＝成績表ではない。守りの判定（gen_signal_families.py の1128〜1134行「ok4 = bool(cols0) and not unread0」）は変わっておらず弱まっていない。ただし照らす材料の数は種つきの引きで上下する。G2 の中の乱数はこの工事の前からのもの。走らせて確かめてはいない（g2_pass.json を書くため）。

修正の番号＝なし

### A4 — 検査16 の出力と、M2-E-1b の表（設計書 4-7）が、設計書の決めた形か（優先度 A）

- **A4-a｜指摘なし。**99行（11×3×3）。①の本数は各足の値決め窓の本数（5m＝158112・1m＝790556）、②は最初の1時間足が閉じるまでを除いた本数（5m＝158101）。1h の①と②は一致。
- **A4-b｜指摘なし。**`git diff 5b7663d -- scripts/priority_rebuild/recipes/` は差0件。milestones2 の差は機械の囲み（§2.2-0・§8）だけで、§2.2 の段の表（761〜767行）は変わっていない。

修正の番号＝なし

### A5 — この実装に、乱数と、新しい数字・点の一覧が0件か（優先度 A）

- **指摘なし。**足した行の中で乱数の語に当たったのは `_resample` の2件だけで、どちらも乱数ではない。b104〜b107 には0件。足した数字は3種類＝①まこさん決定の 0.5・1.0・1.5（設定）②出どころの逐語の 0.0015・0.006 ③番人の見本と道具立て（100.0・100.5・100.8・101.8・104.8・3000・500・100・30000・400・1e-12・1e-9）。前提4 の外の探索の数字は0件。

修正の番号＝なし

### B1 — 完成の条件のうち「未着手」のまま残った15行（#5〜#19）の閉じ方（優先度 B）

- **B1-a｜**走らせ直したもの＝#8 rc=0、#9＝1（812行）、#10 true、#18 rc=0（3秒）、#19 rc=0（2秒）。記録で確かめたもの＝#5・#6・#7（CC の検査の記録ファイル）、#11・#13・#17（pre_audit_check.json の rc=0・22:59:52・その後に対象ファイルの書き替えなし）。#12・#14〜#16 はデータ不足（worklog だけ）。どの行も、文を満たさない出力は無かった。★#4 の後半は A0-d のとおり build_features の道で測っていない（完成の条件 #20 を足す＝修正2）。
- **B1-b｜**走らせなかったもの＝#5・#6（検査4・約7分半）・#7（`--inspect` は observe/ に記録を書き前の記録を archive へ移す＝observe_diag.py:3655〜3660 の `_Tee` の `archive_if_exists`）、#11（約2分・自己テストが一時ファイルを書く）、#12（約6分・書き込みの有無を確かめきれていない）、#13〜#16（同じ理由）、#17（g2_pass.json を書く）。

修正の番号＝2

### B2 — 設計書と実装の食い違いの全件と、その直し方（設計書の側か・実装の側か）（優先度 B）

- **B2-a｜**自己申告の6件の答えは6節。
- **B2-b｜**自己申告に無い食い違い8件＝①Critical：T-A3 の突き合わせが build_features を通らない（A0-d）②Minor：T-A5 の見本が対称（A0-e）③Minor：`selftest_atr1h` の説明（observe_diag.py:6578〜6589）に T-A5 の行が無い ④Minor：手順9 は CC が `--write` を打つ書き方だが、実際は まこさんの端末で打った ⑤Minor：手順12 が手で書いた行番号「6321行・6312行」は、いまは 6322行・6313行（恒久69番）。同点の1位にも触れていない ⑥Minor：手順16 は「2回目の承認」だが実際は3回 ⑦Minor：7-3b の2番「点の一覧に当たりません」は、機械の表（engine_tuner_milestones2.md:2970「決まった数字だけの一覧 38件（場所1 37…）」＝この工事で+1）と合わない ⑧Minor：「なぜ作るか」の表は作り直すたびに実装の後の結果になり、読み方と食い違う（acceptance.md:49 の結果に「908:_reg("S-Rタッチ1時間ATR"…」があるのに読み方は「値動きの幅に連動する部品は外したまま」／acceptance.md:52＝12件なのに「零件」／acceptance.md:65＝19なのに「差が無い」）。
- **B2-c｜**SDK の中から `python3 scripts/priority_rebuild/verify_design_contract.py --diff /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md` を走らせた（PYTHONDONTWRITEBYTECODE=1・-B）。rc=0・1秒。出力はそのまま＝
  - `design : /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/acceptance.md`
  - `impl   : scripts/priority_rebuild/observe_diag.py`
  - `齟齬: 0件`
- **B2-d｜**①②③は実装の側（修正4・5・8・9）と設計書の側（修正1・2・3）、自己申告2 は設計書の側（修正6・7）、④〜⑧は設計書の側（修正11〜18）。

修正の番号＝1・2・3・4・5・6・7・8・9・11・12・13・14・15・16・17・18

### B3 — 実装の後に出た、設計書の外の影響と、確かめの道の限界（優先度 B）

- **B3-a｜Minor。**古くなった行番号・記録が3種類＝①observe_config.json:197「（QSTICK% は roc_periods を回す＝observe_diag.py:1320）」は、実物では observe_diag.py:1493「addf("QSTICK%", n)」（工事の前から違い、今回さらにずれた）②regime_laws.json:1264 と regime_detection_kb.md:1130 の「observe_diag.py:363」（363行は `_vp_levels` の辺り）は、`_sr_touch` が observe_diag.py:379（工事の前から違う）。★法則ファイルは前提6 により修正の指示を出さない（まこさんの判断材料として書くだけ）③next_step.md の §6 の136番（「まだ実測していない…0件」「監査 CP44 待ち」）と milestones2 の1806〜1808行の「まだ」＝設計書のやらないこと13 のとおり、記録の段で直す約束の分。
- **B3-b｜Major（自己申告2）。**全走の本体 `rank_regime`（observe_diag.py:6127〜6150）は `_insp_regime_rank` が同じファイルを上書きする（observe_diag.py:6122）ので、全走のたびに需給が消える。書くべき場所＝①設計書の手順11（修正6・今回の食い違いを閉じる）②全走の本体（修正22・恒久・案が複数）。`pre_audit_check.py` の ORDER（45〜54行）にも成績表は無く、`.claude/audits/m2d1_ranking_scan.py --assert-demand` は CHECKS に入っていない。★当てる道具の相手の外なので、そちらの修正は出さない。
- **B3-c｜Process。**設計↔実装ゲートは走らせる .py を相対の名前で照らす（session_worklog_20260926.md:364）ので、CC の Bash から写しは走らせられない。★本物の `observe_diag.py --selftest-atr1h` は監査の Bash では止まらなかった（rc=0）。限界＝写しの段は まこさんの端末でしか打てず、出力が worklog の転記でしか残らない（事実データ1 の出力はデータ不足）。
- **B3-d｜Process。**T23② は1位の名前を決め打ちしている（engine_tuner_gen.py:6322）。成績表を作り直すたびに、見本の直し→SPEC の作り直し→承認がもう1回 要る。さらに今回の1位は同点の名前順で決まっている（engine_tuner_gen.py:1393「同点は名前順」・0.745 が2本）＝ラベルの並べ方が変わるだけで見本が変わる、弱い形。

修正の番号＝6・7・10・19・20・21・22

### C1 — 名前・説明文・見積もり（優先度 C）

- **C1-a｜Minor。**`selftest_atr1h` の説明は見出しで T-A1〜T-A5 と書くが（observe_diag.py:6578）、各行の説明は T-A4 で終わっている（observe_diag.py:6589）。ほかの説明（`_sr_touch_atr`・`_insp_tol_saturation`・420〜437行の注記）はいまの動きと合う。
- **C1-b｜指摘なし（修正は6節と修正11・13・19 で閉じる）。**外れた所と、設計書に書けたか＝①承認3回＝4-10 で CC が「T23② を直すと承認がもう1回」と予告していた＝書けた ②写しの段がゲートに止まる＝足す前に1回試せば分かった（L-625）＝書けた ③型の表の `--write` が輪になる＝前の回（worklog 20260913）で同じことが起きていた＝書けた ④全走 2時間16分・検査4 7分26秒・検査12 5分40秒は見込みの中。組む側の自己テスト 6分6秒／6分8秒は見込み 5分30秒の約1.1倍。
- 省いた問いは無い（C も答えた）。

修正の番号＝9


## 5. 外部検索

### 検索 1 — なし

しなかった（依頼書のとおり。設計書の監査 CP44 が外部検索を済ませている）。


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

事実と矛盾しない（session_worklog_20260926.md:364 の記録どおり）。監査の Plan サブエージェントは読み取り専用で写しを作れないので、同じ止まりは再現していない。本物の `--selftest-atr1h` は監査の Bash では止まらなかった（rc=0・5秒）。監査の Bash では別の hook が6回止めた（10節）。run.sh を使わなかった判断は恒久57番に合う。限界は修正19 に書いた。

### 自己申告 2

必要だった。成績表に需給の行は18件、`material_ranking.before_add_demand.json`（足し直す前の全走の控え）には0件。全走の本体は需給を消す（observe_diag.py:6122）。設計書の手順11 に無いのは食い違い（Major・修正6・7）。恒久の置き場は修正22（案が複数）。

### 自己申告 3

差は3行（説明の名前・履歴の1行・見本の文字）。履歴の行の 0.745／0.743 は成績表の実物と合う。★見本の1位は同点（`(144,1.5,7)__15m` も 0.745）で、名前の順で決まっている。設計書の手順12 は行番号を手で書いていて古くなった（修正12）。

### 自己申告 4

①T-A5＝欄の入れ替えだけは通ってしまう（修正8）。②T-A3 の突き合わせ＝b107 で測れないことに加えて、突き合わせ自体が置き場を入れ直していて build_features の中身を測っていない（Critical・修正1〜5）。

### 自己申告 5

承認の状態を機械で確かめた（`--status` ✅ ffc10b58・出口の md5 が approved と一致・#18 rc=0）。輪になった経緯は session_worklog_20260926.md:427 の記録どおり。出力が残っていない点は、修正11・19 の手順に入れた。

### 自己申告 6

原因は成績表ではなく、印を 140→141 種に作り直したこと（G2 の見本は印で絞った材料の袋から種つきで引き、場面の判定の束は作らない＝gen_signal_families.py:853）。守りの判定は変わっていない（A3-d）。走らせての確認はしていない（g2_pass.json を書くため）。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ YES（根拠＝許容幅は倍率 × 1時間足の ATR%（その1時間足の終値で割る）を 0.15〜0.6% で挟む形で、タッチは渡された足の高値・安値で数える（observe_diag.py:466〜468）。1時間足は閉じた時刻から使う（454〜455行・T-A4 は監査の本走で通過）。全部の足で作れる（置き場・T-A3 の1つ目・検査4 198列）。検査16 は2つの形で99行を出し、表と文書は作り直されている（A3）。壊すプログラム4本は壊した理由どおりの行で落ちる（A0-a〜c）。未来を見る形・出どころとずれる形は見つからなかった。ただし完成の条件 #4 の後半を測る突き合わせが build_features を通っていない（Critical 1件・直せば閉じられる））
- 問い2 ＝ YES（根拠＝自己申告の6件に加えて、自己申告に無い食い違いを8件挙げ、設計書の側と実装の側を修正1〜22 で示した）

### 結論と件数

- 結論＝CONDITIONAL-GO
- Critical＝5（修正の数。所見は1件＝A0-d）
- Major＝2（修正の数。所見は1件＝B3-b・自己申告2）
- Minor＝11（修正の数。所見は7件）
- Process＝4（修正の数。所見は2件＝B3-c・B3-d）


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 26〜27行（NEW_FILE の最後の2行）
直す前の文字:
~~~
".claude/breaks/b106_atr1h_no_clip.sh",
    ".claude/breaks/b107_atr1h_base_not_passed.sh"
~~~
直した後の文字:
~~~
".claude/breaks/b106_atr1h_no_clip.sh",
    ".claude/breaks/b107_atr1h_base_not_passed.sh",
    ".claude/breaks/b108_atr1h_base_wrong_bars.sh"
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:6645「_H1_BASE["bars"] = big」
状態: 確定

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 398行（完成の条件 #19 の行の終わりの直後）
直す前の文字:
~~~
"コマンド": "python3 scripts/priority_rebuild/gen_composition_rules.py --verify", "経路": "実経路", "壊し方": "壊すプログラムは付けない（既存の照合）", "壊すプログラム": "—", "監査確認": "—", "いまの状態": "未着手"}
~~~
足す文字:
~~~
,
    {"条件": "`build_features` が置き場 `_H1_BASE` に入れる中身が5分足である＝番人 T-A3 は置き場を入れ直さず、build_features が入れたもので4時間足に当てた1時間足の ATR% を作り、5分足から作った値と1本も違わない（監査 CP45）", "コマンド": "python3 scripts/priority_rebuild/observe_diag.py --selftest-atr1h", "経路": "実経路", "壊し方": "`build_features` の置き場に4時間足のバーを入れると、T-A3 が『❌ T-A3』で落ちる", "壊すプログラム": "b108_atr1h_base_wrong_bars.sh", "監査確認": "—", "いまの状態": "未着手"}
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:383「"条件": "1時間足より長い足（4時間足）でも、`build_features` が新しい部品の列を作れ、4時間足に当てた1時間足の ATR% が、同じ5分足から作った1時間足の値と1本も違わない」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない＝本物の設計書を書き替える道具のため・所要時間の実測なし）「"_作り方": "python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify",」
状態: 確定

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 6645〜6646行（T-A3 の2つ目の、置き場の入れ直しと4時間足の値）
直す前の文字:
~~~
        _H1_BASE["bars"] = big
        _a4 = _atr_pct_1h_on(_d4, _an3)
~~~
直した後の文字:
~~~
        # ★監査 CP45＝置き場はここで入れ直さない（build_features が入れた中身をそのまま使う）。
        #   直す前＝ここで置き場に big を入れていたので、build_features が置き場に入れた中身（5分足か）を確かめていなかった
        #   （build_features が4時間足のバーを置き場に入れても、この突き合わせは通った）。
        try:
            _a4 = _atr_pct_1h_on(_d4, _an3)
        except ValueError as _e4:
            ng.append(f"T-A3: build_features が置き場に入れたもので、4時間足に当てる1時間足の ATR% が作れない（{_e4}）")
            _a4 = np.full(len(_d4), np.nan)
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:6645「_H1_BASE["bars"] = big」
状態: 確定

#### 修正 5
対象のファイル: .claude/breaks/b108_atr1h_base_wrong_bars.sh
直す箇所: なし（新しいファイル）
直す前の文字:
~~~
なし
~~~
足す文字:
~~~
#!/bin/bash
# EXPECT_RC: 1
# MEANS: build_features が置き場に5分足でなく4時間足のバーを入れると、4時間足の突き合わせの番人 T-A3 が落ちた
# EXPECT_MSG: ❌ T-A3
# b108 — build_features が置き場 _H1_BASE に入れる中身を4時間足のバーに変えると、T-A3 が落ちるか（監査 CP45）
#   守っているもの＝完成の条件 #20（build_features が置き場に入れる中身が5分足であること）
#   壊し方＝`build_features` の `_H1_BASE["bars"] = bars` を `_H1_BASE["bars"] = _resample(bars, "4h")` にする。
#   期待＝4時間足に当てた1時間足の ATR% が4時間足のバーの ATR% になり、5分足から作った値と違って T-A3 が落ちる（終了コード 1）。
#   ★壊す対象が1か所でなければ止まる（黙って壊さない）。
source "$(dirname "$0")/lib.sh"

OBS="$PR/observe_diag.py"
guard "$OBS"

python3 - "$OBS" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
old = '    _H1_BASE["bars"] = bars\n'
if s.count(old) != 1:
    raise SystemExit("[b108] 壊す対象の行が1か所でない: " + old.strip())
new = '    _H1_BASE["bars"] = _resample(bars, "4h")  # b108 が壊した（置き場に4時間足のバーを入れる）\n'
open(p, 'w', encoding='utf-8').write(s.replace(old, new, 1))
PYEOF

measure python3 "$OBS" --selftest-atr1h
finish
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:1760「_H1_BASE["bars"] = bars」
状態: 確定

### Major

#### 修正 6
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 169行（4-4 の手順11）
直す前の文字:
~~~
時間足ごとの経過を見る）。そのあと `gen_materials.py --write`
~~~
直した後の文字:
~~~
時間足ごとの経過を見る）。★全走の本体（`rank_regime`）は材料カタログの列だけで成績表を書き直し、需給3列を消すので、続けて `observe_diag.py --rank-regime <5分足CSV> --add-demand` で需給3列を足し直します（まこさん決定 2026-09-06「需給に関しては、2-Cでの判断がどうであれ、順位に入れるべき」）。そのあと `gen_materials.py --write`
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:6122「out.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")」
状態: 確定

#### 修正 7
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない・所要時間の実測なし）「"_作り方": "python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify",」
状態: 確定

### Minor

#### 修正 8
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 6673〜6676行（T-A5 の見本）
直す前の文字:
~~~
    #   倍率 1.0 × [0.001, 0.003, 0.007, 0.0015, 0.006, 空]＝値の出ている5本のうち、下端より小さいのは 0.001 の1本、
    #   上端より大きいのは 0.007 の1本（ちょうど端の 0.0015・0.006 は数えない）→ ["5", "20.0%", "20.0%"]
    _c5 = _tol_saturation_cells(1.0, [0.001, 0.003, 0.007, 0.0015, 0.006, float("nan")])
    if _c5 != ["5", "20.0%", "20.0%"]:
~~~
直した後の文字:
~~~
    #   倍率 1.0 × [0.001, 0.0012, 0.003, 0.007, 0.0015, 0.006, 空]＝値の出ている6本のうち、下端より小さいのは 0.001・0.0012 の2本、
    #   上端より大きいのは 0.007 の1本（ちょうど端の 0.0015・0.006 は数えない）→ ["6", "33.3%", "16.7%"]
    #   ★監査 CP45＝下端と上端の本数を変えた（前は 1本・1本＝20.0%・20.0% で、下端と上端の欄を取り違えても通った）。
    _c5 = _tol_saturation_cells(1.0, [0.001, 0.0012, 0.003, 0.007, 0.0015, 0.006, float("nan")])
    if _c5 != ["6", "33.3%", "16.7%"]:
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:6676「if _c5 != ["5", "20.0%", "20.0%"]:」
状態: 確定

#### 修正 9
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 6589行（selftest_atr1h の説明の T-A4 の行の直後）
直す前の文字:
~~~
      T-A4＝途中で切ったデータで計算し直しても、切った時点の許容幅の元（1時間足の ATR%）が変わらない（未来を見ない）
~~~
足す文字:
~~~

      T-A5＝検査16 の1マスの数え方（_tol_saturation_cells）が既知答えと一致する（値の出ている本数・下端の割合・上端の割合）
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:6578「"""T-A1〜T-A5＝S-Rタッチ1時間ATR（許容幅を1時間足の値動きの幅で決める部品）と検査16 の数え方を確かめる。」
状態: 確定

#### 修正 10
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json
直す箇所: 197行（説明の中の古い行番号）
直す前の文字:
~~~
（QSTICK% は roc_periods を回す＝observe_diag.py:1320）
~~~
直した後の文字:
~~~
（QSTICK% は roc_periods を回す＝observe_diag.py の build_catalog の addf(QSTICK%, n) の行）
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:1493「addf("QSTICK%", n)」
状態: 確定

#### 修正 11
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 167行（4-4 の手順9）
直す前の文字:
~~~
`gen_signal_families.py --write` で型の表を、`gen_exit_families.py --write` で出口の表を作り直し、まこさんに2つの `--approve` を打っていただきます
~~~
直した後の文字:
~~~
型の表（`gen_signal_families.py --write` と `--approve`）と出口の表（`gen_exit_families.py --write` と `--approve`）の4つを、まこさんの端末で打っていただき、出力を貼っていただきます（★CC の Bash からは、型の表の `--write` を H2 の検査済みゲートが止め、H2 を G2 の検査済みゲートが止める輪になる＝worklog 20260926 の 4-15）
~~~
根拠の抜き書き: .claude/state/session_worklog_20260926.md:427「＝型の表の --write → H2 → G2 → 型の表の --write、の輪になり、私の Bash からは進めない。」
状態: 確定

#### 修正 12
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 170行（4-4 の手順12）
直す前の文字:
~~~
見本の列の名前（6321行の文字と、6312行の説明の中の同じ名前）を、作り直した成績表の実物の1位に直します
~~~
直した後の文字:
~~~
見本の列の名前（`if _lst23[0][0] != ` の行の文字と、その上の説明の中の同じ名前）を、作り直した成績表の実物の1位に直し、説明の直後に履歴の1行（直した日・分離力・直す前の名前）を足します（★行番号は手で書かない＝恒久69番）。★成績表の分離力は小数3桁で持つので、同点のときは名前の順で1位が決まります（`ranked_materials` の並べ方）
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:6322「if _lst23[0][0] != "S-Rタッチ1時間ATR(144,1.5,21)__15m":」
状態: 確定

#### 修正 13
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 174行（4-4 の手順16）
直す前の文字:
~~~
2回目の承認をお願いし、実装の監査に出します。
~~~
直した後の文字:
~~~
承認をお願いし（手順12 で見本を直したときは engine_tuner_gen.py が変わり SPEC を作り直すので、もう1回＝3回目）、実装の監査に出します。
~~~
根拠の抜き書き: .claude/state/session_worklog_20260926.md:483「承認の印（acceptance.approved）＝bf964dd30ccd4ad8…＝いまの設計書の sha256 と一致。」
状態: 確定

#### 修正 14
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 403行（作ってはいけないものとの照合の2番の理由）
直す前の文字:
~~~
engine_tuner は材料カタログの最小〜最大を範囲として使うので、探す値は点の一覧に限定されません（`material_ranges`）。
~~~
直した後の文字:
~~~
engine_tuner は材料カタログの最小〜最大を範囲として使います（`material_ranges`）。★ただし段1 の候補（`build_stage_candidates`）は成績表の列の数字をそのまま使うので、段1 で試すのは18点です（範囲を開くのは §2.2 の段5）。★`gen_materials.py` が作る照合の表（engine_tuner_milestones2.md の §8）は、設定の `sr_atr1h_k` を決まった数字だけの一覧に数え、場所1 が 36件から 37件（合計 37件から 38件）に増えました（その表の答えは、この工事の前から「当たっています」）。
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md:2970「| 2 | **探す値を、CC が先に「点の一覧」で限定するもの** | 決まった数字だけの一覧 **38件**（場所1 37／場所2 1／場所3 0／場所4 0）・範囲を通さずに作っている所 **0件（合格）** | **当たっています** |」
状態: 確定

#### 修正 15
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 60行（なぜ作るかの「いま登録されている S-R タッチの部品」の読み方）
直す前の文字:
~~~
"読み方": "固定の許容幅の部品だけが登録されている。値動きの幅に連動する部品は外したまま"
~~~
直した後の文字:
~~~
"読み方": "実装の前は、固定の許容幅の部品（S-Rタッチ数）だけが登録されていた。実装の後は、許容幅を一時間足の値動きの幅で決める新しい部品の登録の行も当たる（設計書を作り直すたびに、このコマンドは走り直す）"
~~~
根拠の抜き書き: .claude/state/acceptance.md:49「908:_reg("S-Rタッチ1時間ATR", "S-Rタッチ1時間ATR({},{},{})", False,（終了コード 0）／読み方＝固定の許容幅の部品だけが登録されている。」
状態: 確定

#### 修正 16
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 63行（なぜ作るかの「張り付きの割合を出す節が在るか」の読み方）
直す前の文字:
~~~
"読み方": "零件＝足ごとの張り付きの割合を出す節は無い"
~~~
直した後の文字:
~~~
"読み方": "実装の前は零件＝足ごとの張り付きの割合を出す節は無かった。実装の後は、検査十六の節と番人の行が当たる（設計書を作り直すたびに、このコマンドは走り直す）"
~~~
根拠の抜き書き: .claude/state/acceptance.md:52「12（終了コード 0）／読み方＝零件＝足ごとの張り付きの割合を出す節は無い」
状態: 確定

#### 修正 17
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 76行（なぜ作るかの「commit されていない差の塊の数」の読み方）
直す前の文字:
~~~
"読み方": "承認の前は差が無い＝照合が数える触った関数は、この工事で直すものだけになる"
~~~
直した後の文字:
~~~
"読み方": "承認の前は差が無い＝照合が数える触った関数は、この工事で直すものだけになる。実装の後で commit の前は、この工事の差の塊が数えられる（commit の後は零に戻る。設計書を作り直すたびに、このコマンドは走り直す）"
~~~
根拠の抜き書き: .claude/state/acceptance.md:65「19（終了コード 0）／読み方＝承認の前は差が無い＝照合が数える触った関数は、この工事で直すものだけになる」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない・所要時間の実測なし）「"_作り方": "python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify",」
状態: 確定


## 9. CC プロセス欠陥対策

### Process

#### 修正 19
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 368行（リスクの「実装の指示の中身を…走らせていない」の どうするか）
直す前の文字:
~~~
1件でも落ちたら本物に当てずに まこさんに報告する
~~~
足す文字:
~~~
。★CC の Bash からは写しの .py を走らせられない（設計↔実装ゲートが、走らせる .py を相対の名前で見て本物のファイルを設計書と照らす＝worklog 20260926 の 4-7）。写しの段は、足す前に1回 走らせられるかを試し（教訓 L-625）、走らせられなければ承認のお願いのときに先に言い、まこさんの端末で打っていただき、出力を貼っていただく
~~~
根拠の抜き書き: .claude/state/session_worklog_20260926.md:364「写しの `observe_diag.py --selftest-atr1h` を絶対のパスで走らせたら、設計↔実装ゲート（require_design_contract_before_run）が止めた。」
状態: 確定

#### 修正 20
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json
直す箇所: 360行（リスクの1行目の どうするか）
直す前の文字:
~~~
変わっていたら見本を実物の1位に直す（4-4 の手順12）
~~~
足す文字:
~~~
。★見本を直すと engine_tuner_gen.py が変わるので、SPEC の作り直しと承認がもう1回 要る（この工事では承認が3回）。成績表を作り直す工事では毎回 起きうるので、決めてほしいこと（承認の回数）と見積もりに先に数える
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:1393「rows.sort(key=lambda r: (-r[0], r[1], r[3], r[4]))       # 強い順・同点は名前順（並びを決定論に）」
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
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json:3（監査は走らせていない・所要時間の実測なし）「"_作り方": "python3 .claude/tools/gen_acceptance.py --write ／ 手で書き換えられていないかの検出＝--verify",」
状態: 確定

#### 修正 22
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py
直す箇所: 6149〜6150行（rank_regime の最後）
直す前の文字:
~~~
    _insp_regime_rank(bars, cfg, catalog=cat,
                      tfs=[t.strip() for t in tfs.split(",")] if tfs else None)
~~~
案A 足す文字:
~~~

    # ★監査 CP45＝全走は材料カタログの列だけで成績表を書き直し、需給3列を消す（まこさん決定 2026-09-06 に反する状態になる）。
    print("  ★需給3列はこの走行で成績表から消えた。続けて --rank-regime <5分足CSV> --add-demand を打つ")
~~~
案B 足す文字:
~~~

    # ★監査 CP45＝全走（列も時間足も絞らない）のときは、続けて需給3列を足し直す（まこさん決定 2026-09-06）。
    if not cols and not tfs:
        add_demand_to_ranking(bars_csv, config_path)
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py:6122「out.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")」
状態: 案が複数


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 監査の形

- 監査は Plan サブエージェント（cold start・依頼書と必読だけを渡した）が行った。**このサブエージェントは読み取り専用**で、作業場に写しを作れなかった。そのため A0-b〜e の「別の壊し方」は走らせず、コードを行ごとに読んで判定した。
- 監査を起動した側（auditor session の CC）は、結果を書く前に次を実物で確かめた＝①observe_diag.py:358〜368・436〜470・1315〜1325・1488〜1498・1744〜1762・3650〜3662・4144〜4158・4929〜4939・6573〜6594・6620〜6680 ②indicator_reference_diag.py:660〜732（★サブエージェントが書いた行番号 1087〜1154 はずれていた＝別の指標の登録の行。実物の教科書の式は662〜700行・既知答えは705〜732行。所見の中身は実物と合うので、行番号だけを直した）③engine_tuner_exec.py:2040〜2050、engine_tuner_gen.py:1388〜1398・3927〜3937・6308〜6327 ④gen_signal_families.py:836〜858・937〜947 ⑤engine_tuner_milestones2.md:2965〜2975、regime_laws.json:1259〜1269、regime_detection_kb.md:1125〜1135 ⑥lib.sh:44〜64、run_breaks.py:455〜469 ⑦session_worklog_20260926.md:359〜369・420〜433・476〜488 ⑧acceptance.md:44〜70、observe_config.json:197・251〜261 ⑨修正の指示の「直す前の文字」18件が実物に1か所だけ在ること（`grep -c -F` で各1件・修正1 の2行の組は27行の1か所）と、「直す箇所」の行番号（acceptance_src.json の3・27・60・63・76・167・169・170・174・360・368・383・398・403行、observe_diag.py の6122・6149行）⑩完成の条件の行の形（acceptance_src.json:380〜399 の欄）と b107 の宣言の行（修正2・5 の形を合わせるため）。

### 開いたファイル（着手前必読16件を全部含む・SDK＝v3-bitget-api-sdk/bitget-python-sdk-api）

- 依頼書 1〜436（全文）
- `.claude/state/acceptance.md` 1〜1853（全文）
- SDK/.claude/ratchet/acceptance_src.json 1〜189・316〜435・380〜399（鍵の一覧は jq、26〜28・383・487行は grep）
- `git diff 5b7663d` の4本（全文）
- observe_diag.py：271〜283・358〜368・379〜470・570〜600・1315〜1325・1488〜1498・1603〜1606・1726〜1812・3636〜3668・3925〜3975・4085〜4190・4501〜4600・4923〜4972・5424〜5436・5440〜5560・5982〜6125・6127〜6152・6271〜6312・6573〜6690・7673・7733〜7736・7753
- indicator_reference_diag.py：50・59〜66・119〜145・659〜742・931〜968・1300〜1325・4551・4856
- observe_config.json：197・245〜263
- engine_tuner_gen.py：192〜240・1358〜1398・1457〜1486・1502〜1535・3360〜3560・3927〜3937・6300〜6355
- engine_tuner_exec.py：2040〜2050
- .claude/breaks/b104〜b107（全文）・lib.sh 1〜101（全文）
- CP44 の結果 1〜549
- next_step.md 1〜107・§6 の136番
- build_regime_gate_rg.py 262〜272
- engine_tuner_milestones2.md：578・628・761〜762・768〜812・1806〜1808・1908〜1922・2963〜2975
- regime_laws.json 1259〜1269、regime_detection_kb.md 1125〜1135
- pre_audit_check.py 45〜82
- run_breaks.py 448〜478
- approve_impl.sh 373〜529
- session_worklog_20260926.md 190〜510
- cat_requirements.md 545〜549・591〜595・702〜708
- permanent_rules.md 343・348・351・373・377
- gen_signal_families.py 296〜330・836〜858・937〜1040・1120〜1136・1341〜1380
- gen_exit_families.py 574〜602・736〜745
- gen_composition_rules.py 370〜395
- leak_causality_diag.py 151〜176・298〜360
- verify_design_contract.py 1285〜1300・1770〜1800
- gen_materials.py 1570〜1590・1876〜1892
- 検査の記録5本（observe/ と archive/ の 20260926 分・rank の prev011）
- material_ranking.json・signal_families.json・indicator_switch.json（jq）
- g2_pass.json・h2_pass.json・pre_audit_check.json
- acceptance_archive/m2e-bundle2-20260926.breaks.json 1〜60

### 走らせたコマンド

| コマンド | 終了コード | 秒数 | 出力の要点 |
|---|---|---|---|
| `shasum -a 256 .claude/state/acceptance.md` | 0 | 1未満 | bf964dd3… |
| `verify_design_contract.py --diff …/acceptance.md`（SDK から） | 0 | 1 | 齟齬: 0件 |
| #8 の中身（`grep -q '1時間ATR' … && ! grep -q '1時間ATR.*と実質 同じ' …`） | 0 | 1未満 | 通過（`bash -c` の形は土台ゲートが止めるので中身を直に打った） |
| #9 `grep -c '^. .S-Rタッチ1時間ATR. . [0-9]' …milestones2.md` | 0 | 1未満 | 1（812行） |
| #10 `jq -e 'any(.on[]; . == "S-Rタッチ1時間ATR")' …` | 0 | 1未満 | true |
| `observe_diag.py --selftest-atr1h`（PYTHONDONTWRITEBYTECODE=1・-B） | 0 | 5 | 全部 pass・登録18・158112本・切った時点5 |
| #18 `gen_exit_families.py --verify` | 0 | 3 | ✅ 表は入力の正本と一致 |
| #19 `gen_composition_rules.py --verify` | 0 | 2 | ✅ 改変なし・正本とのずれなし |
| `gen_signal_families.py --status` | 0 | 2 | ✅ 承認済み（ffc10b58…） |
| `shasum` 本物と写しの8本・承認の印 | 0 | 1未満 | 事実データ2 のとおり |
| grep・sed・jq・stat・git diff／log／status（読むだけ・約70回） | 0 | 各1未満 | 所見の根拠のとおり |
| （起動した側）`gen_audit_docs.py result`（骨組み） | 0 | 1未満 | 節 11・問い 10・事実データ 1・外部検索 1・自己申告 6 |
| （起動した側）`grep -c -F`・`grep -n -F`・`sed -n`（読むだけ・約10回） | 0 | 各1未満 | 直す前の文字18件が各1件・行番号が合う（上の⑨） |
| （起動した側）`gen_audit_docs.py check`（作業場の結果） | 1 → 0 | 1未満 | 1回目は「修正の番号」の行の括弧の中の「A0」の 0 を番号と読んで食い違い1件。番号だけの形に直して2回目は食い違い0件 |
| （起動した側）`gen_audit_docs.py form`（作業場の結果） | 0 | 1未満 | 形の食い違い 0 件 |

### hook に止められたコマンド（監査のサブエージェント6回・起動した側の種類4つ）

1. `python3 -c "…"`（元データの鍵の一覧）→ `require_design_contract_before_run.sh`「走らせる .py を確定できないコマンドです」
2. `cat -n .claude/breaks/b10x… ; … git -C … log …` → `require_acceptance_before_impl.sh`「土台ゲート・Bash」（読むだけの語の一覧に無い形）
3. `grep -n '^#\|^#### 修正' <CP44 の結果>` → `enforce_audit_report_form.sh`（hook 11・結果ファイルに触る、読むだけでないコマンド）
4. `jq … m2e-bundle2-20260926.breaks.json …` → `require_acceptance_before_impl.sh`（土台のファイルに jq）
5. `shasum … | cut …; ls … 2>&1; cat acceptance.approved` → `require_acceptance_before_impl.sh`（土台のファイルにパイプとリダイレクト）
6. `for … grep -c -F '".claude/breaks/b107…"' …` → `require_acceptance_before_impl.sh`
7. （起動した側）`mkdir … ; python3 .claude/tools/gen_audit_docs.py result …` → `require_acceptance_before_impl.sh`「土台ゲート・Bash」。`python3 … result …` だけにして通った
8. （起動した側）`python3 … result …` の最初の1回 → `enforce_todo_declaration.sh`（ToDo をチャットに貼った印が無い）。ToDo を貼って印を作り、通った
9. （起動した側）シェルの関数と printf で直す前の文字を数える形・変数の代入を使う形・`echo` を含む形（3回）→ `require_acceptance_before_impl.sh`「土台ゲート・Bash」。`grep -c -F` と `sed -n` を1行ずつ並べる形と Read tool にして通った
10. （起動した側）結果の骨組みへの1回目の Write → `enforce_checked_edit.sh`（書き足す「ファイル名:行番号」29か所を、起動した側がまだ開いていない）。全部を開いて照らし（上の「監査の形」の①〜⑧）、ずれていた indicator_reference_diag.py の行番号4か所を実物に直してから書いた

★写しの .py が止まる件（自己申告1）は、写しを作れないので再現していない。

### 走らせなかったものと理由

- 写しの作成と、写しを壊して走らせる確かめ（A0-b〜e の別の壊し方）＝監査のサブエージェントが読み取り専用のため
- #5・#6（検査4・約7分半）・#7＝`--inspect` は記録を書き、前の記録を移す
- #11（番人の全部・約2分）＝一時ファイルを書く
- #12（組む側の自己テスト・約6分）＝書き込みの有無が未確認
- #13〜#16＝書き込みの有無が未確認
- #17＝g2_pass.json を書く
- `pre_audit_check.py`・`apply_audit_fix.py`・`gen_acceptance.py --write`＝`.claude/tools` の .py で、本物の土台や設計書を書くため
- G2 の実走（13→2 の確認）＝g2_pass.json を書くため


## 11. 本物のファイルを書き替えていないこと

`git status --short | grep -v '^??'` は0行＝追跡中のファイルの変更は0件（監査のサブエージェントが測った）。追跡していないファイル（`??`）は130行で、監査の前から在るもの（cp36〜cp44 の作業場・settings.json の控え・results/ ほか）に、この監査の作業場 `cp45_work/cp45_result.md`（起動した側が道具で作った骨組み）が加わっただけ。起動した側が書いたのは、この作業場の1本と、この結果ファイルと、このセッションの ToDo（`.claude/state/sessions/<このセッション>/session_todo.md` と `session_todo_posted`＝git の外）だけ。結果ファイルを書いた後の `git status --short` の出力は、戻り報告で貼る。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-09-26_m2e_bundle2_impl_cp45_audit_request.md request_sha256=729e28182e1d0d83336de6464112aadc2c1ac71647c96a637240a162c8269291 -->
