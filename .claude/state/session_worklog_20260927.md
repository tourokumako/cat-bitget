# session_worklog_20260927.md — 124回目（束2 の6段の⑥＝監査 CP45 の修正を当てる）

## §1 監査 CP45 の結果の確かめと、まこさんの決定（2026-09-27・124回目）

### 1-1 監査 CP45 の結果（別のセッションで監査が終わっていた）

- 結果ファイル＝`SDK/.claude/audits/2026-09-26_m2e_bundle2_impl_cp45_audit_report.md`（661行・全部 読んだ）。
- 結論＝CONDITIONAL-GO。修正の指示22件＝Critical 5（修正1〜5）・Major 2（6・7）・Minor 11（8〜18）・Process 4（19〜22）。状態＝確定21件・案が複数1件（修正22）。
- 所見の本体＝A0-d（Critical）。自己テスト T-A3 の2つ目は、突き合わせの直前に置き場 `_H1_BASE` へ5分足を自分で入れ直すので、`build_features` が置き場に入れた中身を一度も見ていない。
- B3-b（Major）＝全走の本体 `rank_regime` は成績表を丸ごと書き直し、需給3列を消す。設計書の手順11 に需給の足し直しが無い。

### 1-2 私が実物で確かめたこと

- `observe_diag.py`:6645＝`_H1_BASE["bars"] = big`（T-A3 の2つ目の中）。1760行＝`build_features` の `_H1_BASE["bars"] = bars`。1747行＝`insp5_frame` の `_H1_BASE["bars"] = span`。＝A0-d のとおり。
- b108（修正5）が「❌ T-A3」で止まる見込み＝`_atr_pct_1h_on`（441〜457行）は、渡された足が1時間足以下なら置き場を使わない。T-A2（6621行）と T-A4（6665〜6667行）は5分足しか渡さない。置き場を使うのは T-A3 だけ。
- 修正22 の案B が呼ぶ `add_demand_to_ranking`（6271行）は実在し、引数は `(bars_csv, config_path)`。2回走らせても行が増えない作り（6247行＝古い需給の行だけ入れ替える・6259行＝測れた列を数え直さない）。前回の実測は8.0秒（worklog 20260926 の 4-19）。
- 元データの置き場（ratchet の acceptance_src.json）と控え `acceptance_src_m2e-bundle2-20260926_cp44.json` は同じ sha256（8b349184…）。設計書 acceptance.md と承認の印は同じ（bf964dd3…）。
- 修正10 の相手＝observe_config.json:197 の説明に、古い行番号「1320」が在る。observe_diag.py の1315〜1325行はローソクと形の部品で、QSTICK% を登録しているのは1493行（`addf("QSTICK%", n)`）＝監査の指摘どおり。

### 1-3 まこさんの決定（逐語）

- 直す範囲＝「すべて直す」＝22件を全部。
- 修正22＝私の説明が2回 伝わらず（まこさん「よくわからないので、わかり易く説明しなおして」2回）、3回目は質問にした（恒久の決まり §4 の2番）。まこさんの答え＝分からない所は4つとも（言葉が何を指すか・なぜ需給が消えるのか・誰がいつ打つのか・案で何が変わるか）。前提から書き直した説明のあと、決定＝「案B (Recommended)」。

### 1-4 私が最初に出した条件の誤り（直してまこさんに伝えた）

- 私は最初「`rank_regime` を触る関数の一覧（元データの437行）に足す cp が1回要る」「承認は1回の見込み」と書いた。確かめたら両方 誤りだった。
- cp＝要らない。一覧を承認のときから変えると、verify_design_contract.py の1031行が「impl_functions が承認のときから変わっています」で止め、承認の前にテストを走らせられなくなる。commit していない差が一部だけだと1057行（照合B）が止めるので、CP43 と同じく当てた後に commit し、差をゼロにして1052行の道で通す。
- 承認＝2回。`.claude/breaks/*.sh` は承認の印が要る相手（require_acceptance_before_impl.sh の 623行）で、当てる道具も書かない（apply_audit_fix.py:68 の NEVER_WRITE）。b108 を書くには、b108 が載った設計書の承認が先に要る。
- ★確かめる前に条件を書いた＝恒久53番（調べて証拠がある状態になるまで発言しない）に反した。

## §2 CP45 の修正を当てた（6段の⑥・2026-09-27）

### 2-1 直す行を探している壊すプログラム（L-605）

- 探し方1＝`.claude/breaks/*.sh` を、直す行の文字（`_H1_BASE["bars"] = big`・`20.0%`・`_tol_saturation_cells`・`_insp_regime_rank(bars, cfg, catalog=cat`・`T-A4＝途中で切った`・`QSTICK%`・`roc_periods を回す`・`rank_regime`）で grep＝0本。
- 探し方2＝`run_breaks.py --count-targets` の一覧から observe_diag.py を相手にする行を全部 見た＝探す文字は `_atr_pct_1h_on`・`_sr_touch_atr`・`build_features` の置き場の1行（b107）・需給を足す関数の2行・`_cyc` の鍵・1分足のパス・段の鍵・5分足の探し方で、今回直す行は0本。文字で探していない b53 は、中身を開いて `insp5_frame` の枠づくりと使い回しの鍵を探すと確かめた（今回は触らない）。全体＝「1か所 68 本 ／ 0か所か2か所以上 0 本 ／ 数えない 35 本（合計 103 本）」。

### 2-2 当てた

- `apply_audit_fix.py --report <CP45> --severity Critical,Major,Minor,Process --choose 22=B --dry`＝「当たる 17 件（修正 1・2・4・6・8・9・10・11・12・13・14・15・16・17・19・20・22）／当てない 5 件（実物と合わない件は0・当てた後の中身でも確かめた）」。当てない5件＝修正3・7・18・21（`gen_acceptance.py --write` の走らせるコマンド）と修正5（b108＝守りの仕組みなので当てない＝私が Write ツールで書く）。
- ★1回目は先頭に `time` を付けて hook 11 に止められた（当てる道具の形と読めない）。付けずに打ち直した。
- 本番＝「当てた 17 件／当てなかった 5 件」。相手＝acceptance_src.json（修正1・2・6・11〜17・19・20）・observe_diag.py（4・8・9・22 案B）・observe_config.json（10）。
- 確かめ＝`python3 -m py_compile observe_diag.py` が通った。acceptance_src.json は jq で読めた。observe_diag.py の差は監査の「直した後の文字」どおり（`git diff` を読んだ）。
- 案B の二重の走りは無い＝入口（7764〜7777行）で `--rank-regime --add-demand` は `add_demand_to_ranking` だけを呼び、`rank_regime` を呼ばない。
- 当てた後の元データの控え＝`.claude/state/acceptance_src_m2e-bundle2-20260926_cp45.json`（sha256 1060db70…＝ratchet と同じ・教訓 L-622）。

### 2-3 設計書を作り直した・書いた直後の検査の不足10件（2026-09-27）

- `gen_acceptance.py --write`（修正3・7・18・21）＝「--write 完了: acceptance.md（1856行・囲み 12個）・法則の件数の照合＝法則ファイル 51件 ／ 表 51行」。
- 書いた直後の検査（show_design_check_after_write）＝不足10件。
  - A2＝①必読ゲートの A（TARGET の indicator_reference_diag.py・observe_config.json・engine_tuner_gen.py を開いていない）と C（「読んだ」と書いた engine_tuner_gen.py・engine_tuner_milestones2.md・gen_s22_map.py を開いていない）②読むもの宣言ゲート（前の宣言35件を、このセッションで開いていない）③禁止語の一覧をこのセッションで走らせていない。
  - A9＝照合A「設計書に書いていない関数を触った → rank_regime」・照合B「設計書に書いたのに実装していない」10件（observe_diag.py）＝commit していない差が一部だけのため（1-4 の見込みどおり）。
  - B1・B2＝b104〜b107 とその行のコマンド（`--selftest-atr1h`）を、書き替えの後に測っていない。
- 直し方＝③は `list_banned_words.py acceptance` を走らせた（「全項目で抽出成功」）。②は前回 CP43 の⑥と同じく、今日の⑥で相手にする14件で宣言を出し直した（前の宣言の控え＝`design_read_plan_m2e-bundle2-20260926.md`・sha256 3ba221c9…）。まこさんの OK の後に14件を Read tool で開く。A9 は commit で解く（まこさんの OK 待ち）。B群は commit の後に測る。
