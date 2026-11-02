# session_worklog_20261102.md — 237回目

## §1 237回目＝161番（161-2 の実装の監査 CP97 の結果を読み、直す範囲を決めていただき、修正を書き込んだ・宣言に まこさん「8件全部・修正6 は入れる・設計書の食い違いは直さない」）

### 1-1 開いた物
- 最後まで開いた物＝next_step・CP97 の依頼書（663行）と結果（403行）・core_requirements_full・採用台帳・value_conflicts。
- 一部だけ開いた物＝worklog 20261101（:207〜242・:479〜最後）・設計書（4-4・4-5・4-10・4-23・7-6）・集約の要件定義書（:80〜154）・直す相手の一覧（:425〜434）。permanent_rules は自動の読み込みだけ。返信で申告した。
- 結果＝GO・Critical 0・Major 3・Minor 3・Process 2。

### 1-2 まこさんの決定（逐語 2026-11-02）
- 「8件全部・修正6 は入れる・設計書の食い違いは直さない」

### 1-3 止められた形
- 宣言の hook＝ToDo が無い／ToDo の状態の欄に「★いまここ」以外の文字を足した／必読の fix_inventory を sed で読み、Read の記録が無かった。
- 同じ相手の失敗の hook と同じ種類の失敗の hook＝別の hook に止められた操作も失敗に数えるため（block_repeat_failure.py:81〜85）。見立てと lessons を書いて通した。道具の引数は変えていない。

### 1-4 書き込んだ物（apply_audit_fix.py --report CP97 --severity Critical,Major,Minor,Process --choose 1=確定,…,8=確定）
- --dry＝当たる7件・実物と合わない件0。本番＝修正1・2・4・5・6・7・8 を書き込んだ。applied_fixes.json に7件。修正3 はコマンドの件なので、私が打つ。
- ★道具が続けて掛けた照合（verify_design_contract.check）が FAIL＝「B …indicators.py・gen_indicators_draft.py: 設計書に書いたのに実装していない」6件。道具は G2 と H2 を走らせなかった。原因は前例と同じ型（worklog 20261001:284・20261002:147・20261010:573・20261014:32）＝実装が HEAD に入っているので、差分の関数だけと照らす。
- ★私の誤り＝宣言の順番（確かめ → commit の前で止まる）を、この検査の行を読まずに書いた。前例が記録に在った。まこさんに、commit が先に要る物を返信で伝える。
- 試しの道具の結果＝G2・H2・gen_materials は止める hook 0本。observe_diag.py --selftest-catalog だけ require_design_contract_before_run が止める。commit すれば差分がゼロになり、全部の関数と照らす道に戻る（verify_design_contract.py:1060）。

### 1-5 走らせた結果（4-4 の7 のうち、commit の前に走らせられた物）
- 読む口 --selftest＝37/37（修正4 で1件増えた）。写すプログラム --selftest＝40/40。写すプログラム --verify＝「✅ 違い 0 件」（92.7秒）。照らした①写す の行 762。
- --rewrite は打っていない。--verify が「違い 0 件」なので書き替わる物が無いため。indicators.json の sha256＝4d3f3717… のまま。
- G2（gen_signal_families.py --verify）＝既知答え13件 期待どおり・対象40件・指紋 233f04a7…。
- H2（leak_causality_diag.py）＝注記なし未来参照 0件・打ち切り再現の食い違い 0件・指紋 3df718c8…。
- gen_materials.py --selftest＝全部 pass（該当なし1件 S5）。--verify＝一致。
- .gitignore の効き目＝git check-ignore で、6本は対象に入った。col_snapshot/before_20261024.log は対象外のまま。

### 1-6 修正3 と、まだ走らせていない物
- 修正3＝tidy_next_step.py --write。1回目は (b) で止まった（読むのは元データの「書いた日」の欄。見出しだけ直した）。欄を 2026-11-02 に直して2回目で通った＝検査20個。--selftest 28/28。next_step.md:106 に修正2 の文が在る。
- まだ走らせていない物＝observe_diag.py --selftest-catalog（7-6 の1・2行目）。設計↔実装ゲートが止める。commit の後に走らせる。observe_diag.py は CP97 の修正で変わっていない。
- 走らせない物＝列の比べ（約59分）と監査に出す前のチェック（少なくとも約47分）。修正は列を作る所を変えないため。
- 次＝まこさんのコミットの OK → 差分を commit → カタログの自己テスト → 結果を報告。

### 1-7 commit と残り
- まこさん「コミットOK」→ 15本をパスを指定して加えて commit 471b6fc9。鍵のファイルの変更なし。
- observe_diag.py --selftest-catalog＝「❌ 0 件」。ToDo の161番を ✅済 にした。
- 残り＝gen_regime_kb.py --verify todo が「m2_todo.json が変わったのに --write を走らせていません」と出る。m2_todo.json の最後の commit は f5ba54ba（10-31）で、CP97 の修正とは別。

## §2 237回目＝不備の直しの相談（まこさん 2026-11-02「時間とトークンを浪費する大きめな不備を先に修正したい」）

### 2-1 まこさんの決定と問い（逐語）
- 「コミット後に改善案３つの修正をしてほしい。今課題に上がっている不備以外は→17番「確かめずにミスをする問題は、別途まとめて対応する。」
- A＝「TODOはある程度まとめて作成してデータ保存してると思うが、そこから読み込めばいいのでは？」。B＝「Bの修正案は良さそう」。C＝問いが3つ（必読を読んでも踏まえるとは限らないか／CC はどう対応しているか／思いつきで処理する設定か）。

### 2-2 実物で分かったこと
- next_move.py:273〜274 に「当てた分をコミット → G2 → H2 → gen_regime_kb.py --write todo」が2026-10-11 から書いてある。:316〜317 の当てる前の条件も在る。私の案B の「新しく出す」は、在る物を確かめずに書いた誤り。
- 見えなかった原因＝next_move.py:402 が「いまここ」を、最初の済んでいない段にする。CP96 の6件が当てた記録に無いので段6 で止まり、段12 の手順が画面に出ない。next_step と worklog 20261101:590 は「妨げにならない」と書いていたが、誤り。
- ToDo の保存先＝next_step_src.json の③の表（tidy_next_step.py --todo-from が締めで書く・:799〜851）。読み込む口は無い（書く向きだけ）。

## §3 237回目＝204番（A・B の直し・宣言に まこさん「A・B はこの宣言で進める」。C はまこさん「段ごとに絞る方向でよい」）

### 3-1 直した物（インフラの直し・設計書と監査は要らない）
- gen_regime_kb.py --write todo＝engine_tuner_milestones2.md の2行（ハッシュ値と M2-C の状態の行）。
- B＝next_move.py の main＝いまの段を「済んだ段のうち最後の段の次」にした。前の済んでいない段は「⚠ 飛ばした」と出す。
- A＝tidy_next_step.py に start_todo と旗 --todo-start を足した（在る ToDo は上書きしない・「いまここ」「まだ（途中」の最初の行に ★いまここ・元の状態は記録の欄）。自己テスト T19 を足した。reset_read_log.sh が始めに呼ぶ。始めの表示の文も直した。

### 3-2 走らせた結果
- tidy_next_step.py --selftest＝29/29。bash -n reset_read_log.sh＝rc 0。
- --todo-start を試しの id で走らせた＝21行・161番に ★いまここ。試しのフォルダは消した。実際のセッションの始めでは、まだ走らせていない（次のセッションで見る）。
- next_move.py --work m2c15-indicator-redirect-20261031＝段6 が「⚠ 飛ばした」・段12 が「いまここ」・次の一手にコミット → G2 → H2 が出た。
