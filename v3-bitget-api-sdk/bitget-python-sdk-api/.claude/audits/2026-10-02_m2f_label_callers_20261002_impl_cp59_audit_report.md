# 監査結果 cp59 — CP59 — 観察の道具と測る道具を、札の部品 regime_label.py を呼ぶ形に切り替え、札の版の名前を順位表・落ちた候補・成績表に書く＝14a の工事 B（実装の監査）

## 1. 監査の相手と版

- 依頼書: `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_request.md`
- 依頼書のハッシュ値: ca59c6627e13ce360d169d6e48cbbe8f3b2c286dbdd950d146b17815049ad5ca
- 監査の相手と版（依頼書に書いてあるもの）: `.claude/state/acceptance.md` ／ ハッシュ値 4067f16f7c3eb1233f2b604fa48a1cc5bebbbc8d08bc7a4248e5b4be8d5df033
- 監査が照らしたハッシュ値: 4067f16f7c3eb1233f2b604fa48a1cc5bebbbc8d08bc7a4248e5b4be8d5df033（`shasum -a 256 .claude/state/acceptance.md` で監査が計算した。依頼書の値と一致。承認の控え `m2f-label-callers-20261002.md` とも一致。前の版の控え `.01.md` は 713943e3…）
- 実施日: 2026-10-02


## 2. 監査対象の型宣言

- コード型＝実装の前（commit fefb00e）と後（commit 19d1bd7）の6本（regime_r9_diag.py・observe_diag.py・regime_label.py・b122〜b124）を、設計書 4-20 の実装の指示30件と照らした。
- 文書型＝設計書（acceptance.md）・承認の控え2本・やることの表.md・要件の原文（worklog 20260928 §51・m2_todo.json の M2-F-6d の注意）を照らした。
- 数値型＝Q9 で、直す前と直した後の順位表の3つの割合を比べた。


## 3. 監査対象の事実データの確認

### 設計書の実装の指示の一覧（4-20・当てる道具が当てる相手）

- 依頼書の表の30件は、設計書 4-20 の番号・対象のファイル・直す箇所・種類と、30件とも一致した。
- 根拠の抜き書きの逐語を、実装の前（fefb00e）の実物の行と1文字ずつ照らした。27件が一致した。28〜30番（新しいファイル）の根拠「b113_catch_share_broken.sh:1「#!/bin/bash」」も一致した。
- 設計書の実装の指示の囲みの中の `~~~` の行は120行（30件 × 4）だった。

### 当てた記録（applied_fixes.json の名前 design:m2f-label-callers-20261002）

- `jq` で数えた。名前 design:m2f-label-callers-20261002 の行は30件。番号は1〜30で、重なりは無い。
- 対象のファイルは依頼書の表と30件とも一致した。当て方は30件とも「当てた」。時刻は30件とも 2026-10-02T08:29:46。
- 「もう当て終わっていた」の行は0件。

### 必読に要るファイル（道具が設計書と実装から拾った）

- 表の12本は、全部 実在した（ls で12本）。
- 「入れない」の search_limits.json について。観察の道具の中で、先を見る本数の欄 state_hold_bars_range は、説明の文にしか出てこない（observe_diag.py:5811「版1 er_median＝「先を見る本数」（24・288＝もとは search_limits.json の state_hold_bars_range の両端…」）。表の理由と合う。
- 参考＝観察の道具は、札と関係のない部品の格子（int_grid）を読むために、今も search_limits.json を読む。工事 B はそこに触っていない。


## 4. 所見

### 一般の観点

該当なし（依頼書のとおり）

### Q1 — 実装の指示を当てた結果が、実装の後と1文字も同じか（優先度 A）

**結論＝合う。重さ＝なし。**

- 当て方＝実装の前（fefb00e）の6本に、設計書 4-20 の30件を番号の順に当てた。直す前の文字の1か所目を置き替え、足す文字は直す前の文字の後ろに足し、新しいファイルは全文を書いた（当てる道具と同じ当て方）。
- 当てる時点で、30件とも「直す前の文字」がちょうど1か所に当たった。
- 当てた結果と実装の後（19d1bd7）の diff は、6本とも空だった（終了コード 0）。
  - regime_r9_diag.py（実装 1〜17）＝0.034秒
  - observe_diag.py（実装 18〜24）＝0.617秒
  - regime_label.py（実装 25〜27）＝0.018秒
  - b122・b123・b124（実装 28〜30）＝各 0.016秒
- 空振りしていない証拠＝当てた結果と実装の前の diff は90行。当てた結果と実装の後のバイト数が一致した（71,854／526,516／24,709）。

修正の番号＝なし

### Q2 — 実装の指示のどれにも当たらない行（設計書に無い変更）が無いか（優先度 A）

**結論＝合う（0行）。重さ＝なし。**

- Q1 で、当てた結果が実装の後とバイト単位で同じだった。だから6本の差の行は全部、30件のどれかから出ている。
- 19d1bd7 で6本の外に入った変更は、記録・凍結・帳簿・worklog だけで、Q2 の範囲の外。

修正の番号＝なし

### Q3 — 当てた記録が、実装の指示の全部と1件ずつ合うか（優先度 A）

**結論＝合う。重さ＝なし。**

- 当てた記録の30件と、実装の指示の30件が、番号と対象のファイルで1対1に合った（3 の節の jq の結果）。
- 「当てた」にも「もう当て終わっていた」にも入っていない件は0件。

修正の番号＝なし

### Q7 — まこさんの要望を、この工事の後の実装が満たしているか（問い2）（優先度 A）

**結論＝4件とも満たす。重さ＝なし。**

- 要望1（目的）＝札の式は札の部品の中にだけ在る。観察の道具の2つの口は部品を呼ぶだけ（observe_diag.py:5814「    return rl.bars_keys()」・observe_diag.py:5839「    return rl.labels_at_bars(win, n)」）。測る道具の口も部品を呼ぶだけ（regime_r9_diag.py:208「    w = df_win[[c for c in ("high", "low", "close") if c in df_win.columns]].astype(float)」の後で rl.keys・rl.labels_for_key・rl.key_label を呼ぶ）。
- 要望2（作る場所を1つ）＝設計書 2-1 の測り方 `grep -c -F 'er.median()' observe_diag.py` は0（実装の前は1）。⑪タブの道具は今も観察の道具の口を呼ぶ（build_regime_label_dashboard.py:64「    mask, usable = od._regime_labels(win, n)["強さ"]」）が、その先は部品なので、式は1か所。⑪タブの道具の切り替えは工事 C（依頼書の対象外）。
- 要望3（順位表と落ちた候補に札の版）＝測る道具が各行に書く（regime_r9_diag.py:163「    tag_l = rl.version_tag()」）。08:43 の実際の走行の順位表 rank_stage1_20261002-084303.json の3行とも、札の版＝label-er24-288。自己検査⑨⑬が書いた順位表1行と落ちた候補5行（5つの場面）も、全部 label-er24-288。
- 要望4（数字は設定ファイル）＝部品は呼ばれるたびに設定を読み直す（regime_label.py:41「CONFIG = HERE / "recipes" / "regime_label.json"」・読んだ値を取っておく所は無い）。観察の道具は先を見る本数を search_limits.json から読まなくなった（実装 20）。

修正の番号＝なし

### Q8 — 工事 B の後、札を作る場所が1つになり、札を直すと観察の道具と測る道具の両方が同じ札で動くか（優先度 A）

**結論＝札を作る場所は1つになった。ただし、前の段の順位表と成績表の札の版を照らす所が無く、古い札で選んだ物を黙って使う所が3か所在る（重さ＝Minor）。設計書の「8か所」の数が実物と違う（重さ＝Minor）。**

- 問いの①（設定の数字を書き替えて走らせる確かめ）＝走らせていない（10 の節）。コードの行で断言する。3つの口は、どれも設定を渡さずに部品を呼ぶ。部品の口は、呼ばれるたびに load_config() で設定を読み直す（regime_label.py:200 の keys・regime_label.py:212 の key_label・regime_label.py:242 の bars_keys）。だから er_median の「先を見る本数」を書き替えると、コードを1文字も変えずに、3つの口が同じ新しい本数と札を返す。
- 問いの②＝観察の道具と測る道具に、中央値で切る式は0件。24・288 は説明の文と自己検査の見本にだけ在る。
- 問いの③＝regime_label.json を読むのは、部品の load_config だけ。ほかの当たりは説明の文と H2 の見張りの一覧の名前だけ。
- **古い札で選んだ物を黙って使う所（3か所）**
  - (a) 前の段の順位表を読む _load_top（regime_r9_diag.py:418「    tops = [r for r in rows if r.get("順位") and not r.get("dropped_by") and r.get("内側")]」）は、行の「札の版」を見ない。札を直した後に --top で前の段の上位を渡すと、古い札で選んだ上位が、次の段の土台になる。次の段の順位表には新しい札の版だけが書かれる。だから「どの札で選んだ束か」を最後までたどれない（m2_todo.json:1166「…3つ目は、どの版の札で作った成績表かを、成績表の側に残すことです。…どの札で選んだ束かをたどれます。」）。
  - (b) 差し戻しの口が読む順位表（regime_r9_diag.py:583「        raise SystemExit("[R9] --sweep の順位表に、束（内側）を持つ行が1本も無い（fail-closed）")」の前の読み込み）も、同じく札の版を見ない。
  - (c) 段の候補の並び（engine_tuner_gen.py:2884「    for fam, tf, lab, hor, med, ncol, col in ranked_groups(role, label):」）は成績表 material_ranking.json から作られる。測る道具は、その成績表の札の版を照らさない（regime_r9_diag.py:497〜498 で候補を作る）。成績表を読む側（engine_tuner_gen.py:1344〜1355）は「順位」が在るかだけを見る。
  - 設計書は「組む側は札の版の欄を読まない」（4-1）と決めている。だから実装は設計書どおりで、止める仕組みが無いだけ。止める所を足すかは まこさんが決める（修正4〜6 は「未決」）。
- **設計書の数の誤り**＝設計書 3-1 の5番（acceptance.md:203）と 4-13 の2番（acceptance.md:353）は「呼んでいる8か所」と書く。実装の前（fefb00e）の観察の道具で、2つの口を呼ぶ行は10行だった（5913・5915・5992・6011・6184・6194・6351・7562・7569・7651 行。_regime_labels 6行・_regime_horizons 4行。def の2行を除く）。10行とも名前と戻りの形が変わらず部品を通るので、働きには効かない。4-13 の2番は まこさんが OK した案の逐語（okd_labelB_20261002.txt）から来るので、やることの表を直しても作り直しでは変わらない。

修正の番号＝4・5・6・7・8

### Q9 — 採点に使う版が er_median のとき、測る道具と成績表の数字が直す前と同じか（優先度 A）

**結論＝合う。重さ＝なし。**

- 直す前の版を写して走らせることはしていない（10 の節）。代わりに、本物の走行が書いた2つの順位表を、読むだけで比べた。
  - 直す前＝rank_stage1_20261002-002644.json（00:26）。regime_r9_diag.py と observe_diag.py を最後に変えた commit は 67405b1（10-01 22:36）で、19d1bd7 まで変わっていない（git log）。だから c44ac3a と同じコード。
  - 直した後＝rank_stage1_20261002-084303.json（08:43）。
- 「札の版」の欄を除いて `jq -S` で比べた diff は空（終了コード 0・0.007秒）。列の名前は両方とも同じ8列。

| 行 | ① | ③(先24本) | ③(先288本) | 捉えた(先24本) | 捉えた(先288本) |
|---|---|---|---|---|---|
| 1位 stage1_0（前／後） | 0.18534962558186602 ／ 同じ | 0.49614413430696785 ／ 同じ | 0.4722923633385655 ／ 同じ | 0.1868073478062851 ／ 同じ | 0.19597779805352797 ／ 同じ |
| 2位 stage1_1 | 0.18716479457599677 ／ 同じ | 0.5094785929104856 ／ 同じ | 0.4933599161963978 ／ 同じ | 0.18364455240119426 ／ 同じ | 0.18999645174371452 ／ 同じ |
| 3位 RG-v5 | 0.5721577109896782 ／ 同じ | 0.5044946429163765 ／ 同じ | 0.5106187235363231 ／ 同じ | 0.5669500531349628 ／ 同じ | 0.5594966545012166 ／ 同じ |

- 観察の道具の2つの口＝直す前の _regime_labels の式の行と、部品の er_median の式の行の diff は空。直す前の _regime_horizons が読んでいた search_limits.json（fefb00e）の state_hold_bars_range は {"lo":24,"hi":288}。いまの regime_label.json の er_median の「先を見る本数」は [24,288]。bars_keys は並べた (24, 288) を返す（regime_label.py:242〜245）。直す前の (lo, hi) と同じ。
- 自己検査 T5（版1 は前の式と同じ）は、監査の走行で pass した。

修正の番号＝なし

### Q10 — 札の版の名前が、順位表・落ちた候補・成績表に書かれ、たどれるか（優先度 A）

**結論＝合う。重さ＝なし（たどれなくなる所は Q8 の (a)〜(c) で数えた）。**

- 順位表と落ちた候補の各行の札の版は、version_tag() と同じ（regime_r9_diag.py:163〜165）。自己検査⑬が pass した。書かれたファイルでも確かめた（Q7 の要望3）。
- 成績表を書く口＝observe_diag.py:6111「    body["札の版"] = rl.version_tag()」。
- 需給を足す口＝observe_diag.py:6306「    body["札の版"] = rl.version_tag()」。
- 版の違う成績表に需給を足すと止まる（observe_diag.py:6302〜6305 の SystemExit。成績表を書く 6307 行より前）。走らせてはいない（控えのファイルを本物の ratchet に書くため）。
- 札の版の欄が無い、いまの material_ranking.json を版1 として読むのは正しい。この成績表は commit 32dd9a5（2026-09-26）で、部品が在る前の観察の道具の式で作った。その式は、いまの er_median と同じ文字（Q9）。本数が違う成績表は、先に需給を足す口の「先を見るバー数」の照らしで止まる（observe_diag.py:6301 の注記）。
- 成績表を読む側 load_material_ranking（engine_tuner_gen.py:1344〜1355）は「順位」が在るかだけを見る。「札の版」の欄が増えても読める。

修正の番号＝なし

### Q11 — 採点に使う版が役割を持つとき（band_hold）、役割ごとに測り、段ごとに役割ごとに keep 本ずつ残すか（優先度 A）

**結論＝合わない。重さ＝Critical（問い1 を NO にする所見）。あわせて、band_hold で自己検査⑪が落ちる（重さ＝Minor）。**

- **合う所**
  - 列の名前は役割になる（regime_label.py:212「def key_label(key, cfg=None) -> str:」＝版2 は役割の名前）。
  - rank_rows は役割ごとに keep 本の内を集める（regime_r9_diag.py:134「            if keep is None or k <= keep:」）。自己検査⑫が pass した。
  - 差し戻し（--sweep）は止まる（regime_r9_diag.py:589〜591）。
  - _regime_horizons は役割ごとの本数を返し、_regime_labels はその役割の札を返す（regime_label.py:231〜245）。
- **合わない所（Critical）＝次の段へ渡す所で、役割ごとの上位が全体の keep 本に切られる。**
  - 段2a から先の土台は、前の段の順位表の内側の行を全部 読む（regime_r9_diag.py:514「        base = _load_top(a.top, None)」）。band_hold では役割ごとに keep 本ずつなので、最大 2×keep 本が来る。
  - ところが次の行が、全体の順位で keep 本（いま 10）に切る（regime_r9_diag.py:520「    base = base[:keep]」）。
  - だから、役割ごとの上位のうち全体で keep 本に入らなかった行は、次の段へ渡らない。落ちた候補にも載らない。
  - 監査が作業場で走らせた確かめ（probe_q11_keep.py・2.77秒）＝自己検査⑫と同じ見本（S・T・U・keep=1・役割 scalp と daytrade）を rank_rows に通し、run_stage と同じ2行で読んだ。順位表に残った行＝S・T。落ちた候補＝U。_load_top が読んだ行＝S・T。base[:keep] の後に次の段へ渡る行＝S だけ。役割 daytrade の1位 T は渡らない。
  - 要件の原文＝session_worklog_20260928.md:1434「1. 測る道具と成績表は、役割ごとの札の両方で測って出す…段ごとに残す10本は、役割ごとに10本ずつ選ぶ。」。マイルストーンは、設定の上端を「段ごとに上位何本を次の段へ渡すか」と読むと書く（engine_tuner_milestones2.md:2199）。設計書 4-0（acceptance.md:222）は「段ごとに役割ごとに上位 keep 本ずつ残します」と書く。
  - 設計書の30件には、run_stage の受け渡し（regime_r9_diag.py:514〜520）を直す件が無い。工事 B の対象の行（L-6）なのに、実装の指示が抜けている。
  - いま（er_median）は groups が None なので、働きは変わらない。band_hold にしたときに出る。
- **Minor＝band_hold にすると、測る道具の自己検査⑪が必ず落ちる。**
  - ⑪の見本のデータに high・low の列が無い（regime_r9_diag.py:863「    _df11 = pd.DataFrame({"ts": pd.date_range("2024-03-01", periods=_n11, freq="5min"), "close": _c11,」）。
  - そのため _labels_for が close だけを部品に渡し（regime_r9_diag.py:208）、版2 の札の式が high を読む所（regime_label.py:155「    h = win["high"].astype(float)」）で KeyError になる。
  - さらに regime_r9_diag.py:880 が「捉えた(先24本)」の列を求める。この列は版1 にしか無い。
  - 採点に使う版を band_hold に切り替えるのは依頼書の対象外なので、結論には効かせない。

修正の番号＝1・2・3

### Q4 — 承認した版の設計書どうしで、実装の指示が同じか（優先度 B）

**結論＝合う。重さ＝なし。**

- `.01.md` と `.md` の diff は4か所＝2-1 の結果の3行・7-6 の状態の3行・SPEC の囲み（目印の行と、rank_rows の呼ぶ物 [] →「rank_key」）。
- 実装の指示の囲み（ACC_IMPL）の中に差は無い。
- 当てたのは 08:29:46 で、1回目の承認（.01）の下。いまの版（08:42 に承認を打ち直した）と実装の指示が同じなので、実装には効かない。

修正の番号＝なし

### Q5 — 実装の指示が、やることの表の要件を全部 満たすか（優先度 B）

**結論＝合わない。重さ＝Critical（Q11 と同じ所見。件数は Q11 で1件として数える）。**

- 要件 L-6 の「段ごとに…上位を残す」のうち、次の段へ渡す所の実装の指示が無い（Q11）。
- L-1 と L-5 は満たす（実装 6・20・21・26、実装 5・23・24）。
- 実装の指示に在って要件に無いものは無い。説明の文・自己検査・壊すプログラムは、表の「確かめ方」と設計書 §5 の5・6番が受け持つ。
- 参考＝やることの表の「確かめ方」の「H2 が全部 pass」は、7-6 の完成の条件に入っていない（4-4 の手順4 だけに在る）。Q13 で印が取り直されているので、所見にしない。

修正の番号＝1

### Q6 — 完成の条件が、実装の後に本当に成り立つか（優先度 B）

**結論＝合う（1〜3 は監査が走らせ、4 は本物の走行の記録で確かめた）。重さ＝なし。**

| # | コマンド | 結果 | 秒数 |
|---|---|---|---|
| 1 | `TMPDIR=作業場 python3 -B scripts/priority_rebuild/regime_label.py --selftest` | 終了コード 0。T1〜T11（T6 を含む）「✅ 全部 pass」 | 5.367 |
| 2・3 | `TMPDIR=作業場 python3 -B scripts/priority_rebuild/regime_r9_diag.py --selftest` | 終了コード 0。⑫・⑬を含めて「✅ 全部 pass」 | 2.905 |
| 4 | `python3 scripts/priority_rebuild/regime_r9_diag.py --stage stage1 --limit 2 --purpose check` | 走らせていない（本物の results/ と、git の登録がある確認の帳簿 engine_tuner_check_runs.json を書くため） | — |

- 4 の代わり＝08:43 の順位表は144回目と同じ数字だった（Q9）。3行に札の版が在る。落ちた候補は0行なので、実データでは「各行に札の版」は空のまま満たす。落ちた候補の側は、自己検査⑬が合成データで見ている。
- 参考＝07:59〜08:41 にも同じ中身の順位表が12本書かれ、確認の帳簿に12行が足されて 19d1bd7 に入った。承認の前の検査が、仮に当てた本物で完成の条件のコマンドを走らせたため。worklog 20261002 の 8-8 には1回だけと書かれている。確認の帳簿は累積の試行に入らない（purpose check の行き先は確認の帳簿）。

修正の番号＝なし

### Q12 — 自己検査 T6・⑫・⑬ と壊すプログラム b122〜b124 が、それぞれの判定を外したときに落ちるか（優先度 B）

**結論＝合う。重さ＝なし。**

- 壊すプログラムは走らせていない（10 の節）。lib.sh は本物のパス（PR＝SDK の scripts/priority_rebuild）を書き替えて戻す作りで、本物を書き替えることになるため。
- 壊す対象の行は3本とも1か所だった（`grep -c -x -F` と部分一致の両方で1）。b122＝observe_diag.py:5839。b123＝regime_r9_diag.py:164。b124＝regime_r9_diag.py:134。
- 壊した後の形と自己検査の判定を照らした。
  - b122＝rl. の呼び出しが無くなり、.median が入る。T6 の2つの判定（regime_label.py:349〜352）に当たる。
  - b123＝順位表の行に札の版が無くなる。⑬に当たる。
  - b124＝役割ごとの内側が空になる。⑫（regime_r9_diag.py:855〜859）と⑩に当たる。
- 承認の機械の記録 breaks.json は、3本とも code 1・expect 1・match true。
- T6 は測る道具の _labels_for も見ている（regime_label.py:344「                     ("_labels_for", HERE / "regime_r9_diag.py")):」）。

修正の番号＝なし

### Q13 — 観察の道具と札の部品を書き替えたことで、H2 の印が取り直されているか（優先度 B）

**結論＝合う。重さ＝なし。**

- H2＝`python3 -B .claude/hooks/enforce_h2_pass.py --check-fingerprint` の結果は「✅ 印と、いまのコードが一致（e4fc4dc24e6eef91… ／ 対象 24 件）」。終了コード 0・0.08秒（監査が打った）。対象には observe_diag.py・regime_label.py・recipes/regime_label.json が入っている。
- G2＝`python3 -B .claude/hooks/enforce_g2_pass.py --check-fingerprint` の結果は「✅ 印と、いまのコードが一致（09f97a773a763551… ／ 対象 39 件）」。終了コード 0・0.08秒。
- 38件から39件に増えた理由＝G2 の対象は「走行中に読んだファイル＋このリポジトリから import された .py」（gen_signal_families.py:912〜919）。実装で `import regime_label as rl` が observe_diag.py:116 と regime_r9_diag.py:52 に足された。実装の前（fefb00e）に regime_label を import する行は0件。だから増えた1件は regime_label.py（g2_pass.json の29番目）。
- regime_r9_diag.py は H2 と G2 のどちらの対象にも入っていない（h2_pass.json・g2_pass.json に名前が0件）。だから修正1〜6 を当てても、印は外れない。

修正の番号＝なし


## 5. 外部検索

該当なし（依頼書のとおり）


## 6. 依頼を出した CC の自己申告への答え

### 自己申告 1

- 監査が測った値＝regime_label.py --selftest は 5.367秒（4-14 の見込み「約5秒」の範囲）。regime_r9_diag.py --selftest は 2.905秒（4-14 では「測っていない」）。
- b122〜b124 は、本物を書き替えるので監査は測っていない。
- 6-3 の「見込みの2倍を超えたら止める」は、見込みの無い項目には照らせない。

### 自己申告 2

- 本当だった。囲みの中の6行＝目印の行が2行・rank_rows が1行から3行。囲みの外の12行＝2-1 が3行＋3行・7-6 が3行＋3行。実装の指示の囲み（ACC_IMPL）は同じ（Q4）。
- `.01.diff.txt` に 7-6 の行が無いのは、7-6 は承認のプログラムが後から書くため。

### 自己申告 3

- 3本とも git status で「??」。19d1bd7 の対象の一覧にも入っていない。Q1 と Q2 の差は、対象の6本だけで取った。
- 申告に無いものが1つ在る＝` M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md`。監査を始めたときから在り（更新時刻 10:44＝この監査のセッションの ToDo 10:45 より前）、19d1bd7 には入っていない。worklog 20261002 の 7-5 は「会話の始めの hook が作り直した生成物」と書く。


## 7. 総合判定

### 結論を決める問いへの答え

- 問い1 ＝ NO（根拠＝Q1・Q2・Q3・Q4・Q6・Q8・Q9・Q10・Q12・Q13 は合った。しかし Q11 と Q5 で、設計書 4-0 の「段ごとに役割ごとに上位 keep 本ずつ残します」（acceptance.md:222）と要件 L-6（session_worklog_20260928.md:1434）に当たる「次の段へ渡す所」の実装の指示が、30件に無い。実物＝regime_r9_diag.py:520「    base = base[:keep]」が、band_hold のとき役割ごとの上位を全体の keep 本に切る。監査の走行で、役割 daytrade の1位が次の段へ渡らないことを確かめた）
- 問い2 ＝ YES（根拠＝Q7。要望1〜4 を全部 満たす）

### 結論と件数

- 結論＝NO-GO
- Critical＝1（修正1・所見は Q11 と Q5 の1つ）
- Major＝0
- Minor＝7（修正2〜8・所見は3つ＝Q11 の自己検査⑪〔修正2・3〕／Q8 の札の版を照らさない3か所〔修正4・5・6〕／Q8 の「8か所」の誤り〔修正7・8〕）
- Process＝0


## 8. 修正の指示

### Critical

#### 修正 1
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 520行（run_stage）
直す前の文字:
~~~
    base = base[:keep]
~~~
直した後の文字:
~~~
    # ★監査 cp59（Q11）＝札の版が役割を持つとき（band_hold）は、前の段で役割ごとに keep 本の内に入った行（成績下位でない行＝_load_top が読んだ行）を
    #   全部 次の段へ渡す（worklog 20260928 §51 の1「段ごとに残す10本は、役割ごとに10本ずつ選ぶ」）。版1（groups が None）は いままでどおり keep 本
    base = base if rl.groups() is not None else base[:keep]
~~~
根拠の抜き書き: .claude/state/session_worklog_20260928.md:1434「1. 測る道具と成績表は、役割ごとの札の両方で測って出す…段ごとに残す10本は、役割ごとに10本ずつ選ぶ。」
状態: 確定

### Major

なし

### Minor

#### 修正 2
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 863行（selftest）
直す前の文字:
~~~
    _df11 = pd.DataFrame({"ts": pd.date_range("2024-03-01", periods=_n11, freq="5min"), "close": _c11,
~~~
直した後の文字:
~~~
    _df11 = pd.DataFrame({"ts": pd.date_range("2024-03-01", periods=_n11, freq="5min"), "close": _c11, "high": _c11, "low": _c11,
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_label.py:155「    h = win["high"].astype(float)」
状態: 確定

#### 修正 3
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 880行（selftest）
直す前の文字:
~~~
        _ok11 = [r for r in _rows11 if r.get("判定") == "t11_ok" and "①時間の割合" in r and "捉えた(先24本)" in r]
~~~
直した後の文字:
~~~
        _ok11 = [r for r in _rows11 if r.get("判定") == "t11_ok" and "①時間の割合" in r
                 and all(f"捉えた({rl.key_label(k)})" in r for k in rl.keys())]   # ★監査 cp59（Q11）＝列の名前は札の鍵（版1＝先24本・先288本／版2＝役割の名前）
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py:880「        _ok11 = [r for r in _rows11 if r.get("判定") == "t11_ok" and "①時間の割合" in r and "捉えた(先24本)" in r]」
状態: 確定

#### 修正 4
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 418行（_load_top）
直す前の文字:
~~~
    tops = [r for r in rows if r.get("順位") and not r.get("dropped_by") and r.get("内側")]
~~~
足す文字:
~~~

    # ★監査 cp59（Q8）＝前の段の順位表が、いまの設定の札で測った行かを見る（違う札で選んだ上位を黙って次の段へ渡さない・fail-closed）。
    #   札の版の欄が無い行（工事 B の前に作った順位表）は、③の列の名前が いまの札の鍵と同じときだけ通す。
    _now = rl.version_tag()
    _cols = {f"③実はトレンド({rl.key_label(k)})" for k in rl.keys()}
    _odd = [r.get("判定") for r in tops if (r.get("札の版") or _now) != _now or {k for k in r if k.startswith("③")} != _cols]
    if _odd:
        raise SystemExit(f"[R9] 順位表 {path} の行 {_odd[:3]} は、いまの設定の札（札の版 {_now}）で測った行でない（fail-closed）")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_todo.json:1166「…3つ目は、どの版の札で作った成績表かを、成績表の側に残すことです。…どの札で選んだ束かをたどれます。」
状態: 未決

#### 修正 5
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 583行（run_sweep）
直す前の文字:
~~~
        raise SystemExit("[R9] --sweep の順位表に、束（内側）を持つ行が1本も無い（fail-closed）")
~~~
足す文字:
~~~

    # ★監査 cp59（Q8）＝差し戻す順位表が、いまの設定の札で測った行かを見る（_load_top と同じ照らし・fail-closed）
    _now = rl.version_tag()
    _cols = {f"③実はトレンド({rl.key_label(k)})" for k in rl.keys()}
    _odd = [r.get("判定") for r in tops if (r.get("札の版") or _now) != _now or {k for k in r if k.startswith("③")} != _cols]
    if _odd:
        raise SystemExit(f"[R9] 順位表 {a.sweep} の行 {_odd[:3]} は、いまの設定の札（札の版 {_now}）で測った行でない（fail-closed）")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py:583「        raise SystemExit("[R9] --sweep の順位表に、束（内側）を持つ行が1本も無い（fail-closed）")」
状態: 未決

#### 修正 6
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py
直す箇所: 497〜498行（run_stage）
直す前の文字:
~~~
    cands = (g.build_width_candidates(laws, table, tfs, lm) if a.stage == "width"
             else g.build_stage_candidates(a.stage, laws, table, tfs, lm))
~~~
足す文字:
~~~

    # ★監査 cp59（Q8）＝候補の並びに使った成績表（material_ranking.json）が、いまの設定の札で作った物かを見る（違う札の成績表で並べた
    #   候補を、いまの札の順位表に黙って混ぜない・fail-closed）。札の版の欄が無い成績表は版1（er_median）で作った物として読み、
    #   先を見るバー数が いまの本数と同じときだけ通す（add_demand_to_ranking・merge_demand_into_ranking と同じ読み方）。
    _mr = g.load_material_ranking()
    if ((_mr.get("札の版") or rl.version_tag(version="er_median")) != rl.version_tag()
            or [int(x) for x in (_mr.get("先を見るバー数") or [])] != list(rl.bars_keys())):
        raise SystemExit(f"[R9] 成績表 material_ranking.json（札の版 {_mr.get('札の版')}・先を見るバー数 {_mr.get('先を見るバー数')}）が、"
                         f"いまの設定の札（{rl.version_tag()}・{list(rl.bars_keys())}）と違う（先に observe_diag.py --rank-regime で作り直す・fail-closed）")
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py:2884「    for fam, tf, lab, hor, med, ncol, col in ranked_groups(role, label):」
状態: 未決

#### 修正 7
対象のファイル: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md
直す箇所: 75行（3-1 やらないこと）
直す前の文字:
~~~
| 観察の道具の中で _regime_labels と _regime_horizons を呼んでいる8か所を直すこと | 呼ぶ名前と戻りの形を変えないので、8か所は直さずに部品を通る | observe_diag.py の中の呼び出し（git grep で数えた8か所） |
~~~
直した後の文字:
~~~
| 観察の道具の中で _regime_labels と _regime_horizons を呼んでいる10行（_regime_labels 6行・_regime_horizons 4行）を直すこと | 呼ぶ名前と戻りの形を変えないので、10行は直さずに部品を通る | observe_diag.py の中の呼び出し（監査 cp59 が実装の前 fefb00e で数えた10行＝5913・5915・5992・6011・6184・6194・6351・7562・7569・7651 行） |
~~~
根拠の抜き書き: v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-callers-20261002/やることの表.md:75「…呼んでいる8か所を直すこと…（git grep で数えた8か所）…」
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
python3 .claude/tools/gen_acceptance.py --work m2f-label-callers-20261002 --write
~~~
根拠の抜き書き: .claude/state/acceptance.md:13（監査は走らせていない＝設計書を書き替え、承認の印と食い違うため・秒数なし）「作り直し＝`python3 .claude/tools/gen_acceptance.py --work m2f-label-callers-20261002 --write`」
状態: 未決

- 修正8 を「未決」にした理由＝作り直すと設計書のハッシュ値が変わり、承認の打ち直しが要る。また 4-13 の2番の「8か所」（acceptance.md:353）は まこさんが OK した案の逐語から来るので、修正7 を当てて作り直しても変わらない。


## 9. CC プロセス欠陥対策

### Process

なし


## 10. 開いたファイルと行・走らせたコマンドと結果と秒数・走らせられなかったものと理由

### 監査の分担

- 監査の本体は Plan サブエージェント（cold start・会話の文脈を渡していない）が行った。Plan サブエージェントは読むだけの役割で、作業場に写しを作れなかった。
- 監査を起動した CC（auditor のセッション）は、所見の根拠の行と修正の指示の「直す前の文字」を実物で開き直して照らした。あわせて、Q11 の Critical を作業場の確かめのプログラムで走らせ、H2・G2 の印の照らしを打ち直した。

### 開いたもの（着手前必読 19件は全部）

1. acceptance.md＝全文（1〜1412行）。
2. `.01.md`＝diff で全行を照らした。
3. `.md`＝cmp で acceptance.md と同じ。
4. applied_fixes.json＝jq と grep。
5. やることの表.md＝1〜85行。
6. cat_requirements.md＝159〜268行・529〜752行。
7. engine_tuner_requirements.md＝28〜103行。
8. engine_tuner_milestones.md＝95〜146行。
9. engine_tuner_milestones2.md＝3〜46行・498〜619行・1342〜1392行。2021〜2368行は grep で M2-F の行を抜いて読んだ（2199行を含む）。
10. m2_todo.json＝1155〜1170行。
11. session_worklog_20260928.md＝1402〜1439行。
12. regime_r9_diag.py＝全文（1〜1044行）。
13. observe_diag.py＝90〜129行・5776〜5935行・5960〜6129行・6150〜6364行・7515〜7664行。
14. regime_label.py＝全文。
15. regime_label.json＝全文。
16. engine_tuner_gen.py＝1300〜1379行・2879〜2889行・3159〜3188行。
17〜19. b122・b123・b124＝全文。

ほかに開いたもの＝依頼書（全文・503行）・worklog 20261002・lib.sh・breaks.json・enforce_h2_pass.py・enforce_g2_pass.py・gen_signal_families.py・apply_audit_fix.py・gen_audit_docs.py・approve_impl.sh・require_design_check_before_approval.py・tuner_stats.py・leak_causality_diag.py・build_regime_label_dashboard.py・順位表 rank_stage1_20261002-002644／-084303・material_ranking.json の欄・h2_pass.json と g2_pass.json の対象。

### 走らせたコマンドと結果と秒数

| コマンド | 結果 | 秒数 |
|---|---|---|
| shasum（acceptance と控え2つ・依頼書） | 4067f16f…・713943e3…・4067f16f…・ca59c662… | 測っていない（読むだけ・短い） |
| jq（当てた記録） | 30件・番号1〜30・全部「当てた」 | 測っていない |
| awk でメモリの中で当てる＋diff（.py 3本） | 3本とも空 | 0.034／0.617／0.018 |
| 同じ（.sh 3本） | 3本とも空 | 各 0.016 |
| 根拠の抜き書き27件の照合（awk） | 27/27 一致 | 測っていない |
| 順位表 00:26 と 08:43 の jq の diff | 空 | 0.007 |
| regime_label.py --selftest（TMPDIR＝作業場） | 終了コード 0 | 5.367 |
| regime_r9_diag.py --selftest（TMPDIR＝作業場） | 終了コード 0 | 2.905 |
| enforce_h2_pass.py --check-fingerprint | 終了コード 0・対象24件 | 0.08 |
| enforce_g2_pass.py --check-fingerprint | 終了コード 0・対象39件 | 0.08 |
| 設計書 2-1 の grep 3本 | 0（終了コード 1）／1／2（実装の前は1） | 測っていない |
| 作業場の確かめ probe_q11_keep.py（Q11） | 次の段へ渡る行＝S だけ（T が渡らない） | 2.77 |
| 修正の指示の直す前の文字の grep -n -F（修正1〜7） | 7件とも1か所 | 測っていない |
| fefb00e の観察の道具で2つの口を呼ぶ行の grep | def の2行＋呼ぶ行10行 | 測っていない |

### 走らせられなかったものと理由

- M2-F-5 の走行（完成の条件4）＝本物の results/ と、git の登録がある確認の帳簿 engine_tuner_check_runs.json を書くため。
- Q8①・Q11 の設定を変えた走行、Q9 の c44ac3a の版の再走＝Plan サブエージェントは写しを作れない役割だった。python を -c や標準入力で走らせる形は hook（require_design_contract_before_run.sh）が止めた。Q11 は、監査を起動した CC が作業場の確かめのプログラムで、受け渡しの2行だけを走らせた。
- b122〜b124（Q12）＝lib.sh が本物のパスを書き替えて戻す作りのため。
- H2 の全部の検査（約5分）と G2 の走行＝印の照らしだけで足りるので走らせていない（依頼書のとおり）。

### 本物の外に出た書き込み（監査のコマンドではないもの）

- 自己検査⑨⑬が、作業場に `cp59_work/tmp3yzjgh2b/regime_r9/`（rank_selftest_20261002-105850.json・dropped_selftest_20261002-105850.json）を残した。
- hook require_design_contract_before_run.sh が、Plan サブエージェントの最初の `python3 -c` を止めたときに、`.claude/state/design_gate_fires.log`（git の対象外）へ1行（10:47:41）を足した。
- 監査を起動した CC が grep を打ったとき、PostToolUse の hook（show_design_check_after_write.sh）が「承認の前の検査」の不足7件を画面に出した。承認の側の検査なので、監査は案内のコマンド（run_breaks.py ほか）を走らせていない。


## 11. 本物のファイルを書き替えていないこと

`git status --short` を、結果ファイルを書く前に取った。

- 全体の行数＝218。
- 「??」以外の行は次の1行だけ。この行は監査を始める前から在った（更新時刻 10:44＝この監査のセッションの ToDo 10:45 より前・会話の始めの git の状態にも「M」で出ていた）。

```
 M v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/decisions.md
```

- 追跡していないファイルのうち、この監査のセッションの ToDo（10:45）より新しいものは、作業場 cp59_work の下の4本だけ（`git ls-files -o --exclude-standard` の各ファイルを、ToDo のファイルと更新時刻で比べた）。

```
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/cp59_result.md
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/probe_q11_keep.py
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/tmp3yzjgh2b/regime_r9/dropped_selftest_20261002-105850.json
v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp59_work/tmp3yzjgh2b/regime_r9/rank_selftest_20261002-105850.json
```

- この git status を取った後に、見直し表 cp59_result.review.md を同じ作業場 cp59_work に作った（本物のファイルではない）。
- 対象の6本・regime_label.json・engine_tuner_check_runs.json・material_ranking.json について、`git diff --stat HEAD` は差なし。

<!-- gen_audit_docs: result request=v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/inputs/2026-10-02_m2f_label_callers_20261002_impl_cp59_audit_request.md request_sha256=ca59c6627e13ce360d169d6e48cbbe8f3b2c286dbdd950d146b17815049ad5ca -->
