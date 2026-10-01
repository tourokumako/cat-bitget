<!-- gen_audit_docs request-design kind=impl design_sha256=cbfd521a0b8f294749bddb4e85f9f97d1d6b1279b368c107e6122e220aaaf853 src_sha256=0e18fd4dd0424d6681faf69d0b04ad996a6898c9998a88a41785e0de77b6e873 body_sha256=24e96defa95319c856e7ed103636fce9d6b8497669e66f30460250069c53f0b6 -->
<!-- 項目: メタ -->
日付: 2026-10-01
task: m2f_label_builder_stages_20261001_impl
cp: cp57
題: CP57 — 段の候補を作る側と測る側の不具合6つを直し、渡す本数を10本にする（実装の監査）
依頼者: CC（起案者）
監査区分: 実装の監査
監査対象タスク: M2-F-7・M2-F-13b／設計書 m2f-label-builder-stages-20261001
監査の相手: .claude/state/acceptance.md
売買に触るか: はい

<!-- 項目: 作業場の指示 -->
**★この監査は「実装の監査」です。**あなたは必要なファイルを自分で開き、写しで走らせて確かめられます。開いて、走らせてください。

**★本物のファイルを書き替えないでください。**写しは作業場 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp57_work/` に作ってください。

**★この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました（CC は依頼書の文を書いていません）。**問いは、設計書のとおりに当てる道具が実装を作れているかを照らす、決まった6問（Q1〜Q6）と、まこさんの要望（逐語）を この工事の後の実装が満たしているかを問う Q7（結論を決める問い2 に当たる・要望の逐語が在る工事だけ）です。

<!-- 項目: 結論を決める問い -->
- **問い1**＝設計書の実装の指示（23 件）から、当てる道具が設計書のとおりに実装を作れているか（Q1〜Q6 で照らす）。実装が実装の指示と1文字でも違う・設計書に無い変更が在る・実装の指示が1件でも抜けていれば NO。

- **問い2**＝下に並べた まこさんの要望（逐語・5 回の発言・11 行）を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。1つでも満たしていなければ NO（Q7 で照らす）。
  - 発言 `req_14b_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 3 行）
    - `req_14b_20260928:V01` 直す範囲は全部
    - `req_14b_20260928:V02` 決めることはCCのおすすめでOK
    - `req_14b_20260928:V03` ではその不具合は修正して、ミッション達成できるようにしてほしい
  - 発言 `req_k1_20260918`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_k1_20260918:V02` →とりあえず１０本にする
    - `req_k1_20260918:V03` 結果を見て変更すると思う
  - 発言 `req_m27_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m27_20260928:V04` 了解。状況は理解した。
    - `req_m27_20260928:V05` M2-F-7 の進め方はCCの案でOK
  - 発言 `req_m2_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m2_20261001:V01` じゃあ、milestone２の残りを早く進めてくれ。
    - `req_m2_20261001:V02` やってるふりじゃなく、ちゃんと完成しろ
  - 発言 `req_split_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_split_20261001:V01` なんだそれ。
    - `req_split_20261001:V02` じゃあ修正せずに、分けてすすめれば

<!-- 項目: 結論の決め方 -->
- **GO**＝問い1 と 問い2 が YES で、Critical が0件。
- **CONDITIONAL-GO**＝問い1 と 問い2 が YES で、Critical が在る（直せば先に進める）。
- **NO-GO**＝問い1 と 問い2 のどれかが NO。違う所を、設計書の実装の指示の番号・要望の逐語と実物の行で示してください。

<!-- 項目: この監査の前提 -->
1. **乱数は禁止です**（恒久67番）。乱数を残す・足す形なら Critical にしてください。
2. **CC は自分で「合っている」「動く」と判定していません**（恒久64番）。
3. **修正の指示は、設計書の元（工事のフォルダ `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001`（やることの表.md と、まこさんが OK した案の逐語））に対して書いてください**（設計書はプログラムが作るので直接は書けない）。
4. **監査は1つの工事につき1回です**（恒久65番）。どこまで直すかは、まこさんが結果ファイルを見て決めます。
5. **net は M2-L まで使いません**（まこさん決定 2026-09-01）。

<!-- 項目: 経緯 -->
1. 設計書 `m2f-label-builder-stages-20261001`（段の候補を作る側と測る側の不具合6つを直し、渡す本数を10本にする）は、工事のフォルダ `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001`（やることの表.md と、まこさんが OK した案の逐語） から `gen_acceptance.py` が作りました。
2. 設計のもと（やることの番号 M2-F-7・M2-F-13b・逐語のファイル m2f-label-builder-stages-20261001/ok_stages_20261001・m2f-label-builder-stages-20261001/ok_todo_20261001・m2f-label-builder-stages-20261001/okd_stages_20261001・m2f-label-builder-stages-20261001/req_14b_20260928・m2f-label-builder-stages-20261001/req_k1_20260918・m2f-label-builder-stages-20261001/req_m27_20260928・m2f-label-builder-stages-20261001/req_m2_20261001・m2f-label-builder-stages-20261001/req_split_20261001）は、設計書の §0-1 に道具が写しました（CC は写していません）。逐語のファイルは `gen_verbatim.py` がやり取りの記録から抜き出したものです。
3. この依頼書は `gen_audit_docs.py request-design --work` が、設計書と工事のフォルダから作りました（CC は依頼書の元データを書いていません）。
4. 承認の印（`acceptance.approved`）は、いまの設計書の sha256 と同じです（同じでなければ、この依頼書は作れません）。
5. 承認した版の設計書の控えは 2 本（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md`）。当てる道具が当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2f-label-builder-stages-20261001`）は 23 件。
6. 実装の前＝HEAD の commit e31d6e8（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる） ／ 実装の後＝作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる）（承認の控えを入れた commit と、その親を git から読んだ。控えが commit されていなければ HEAD と作業中の変更）。

<!-- 項目: 着手前必読 -->
**パスはリポジトリの根（`cat-bitget/`）からの相対です。**`SDK` ＝ `v3-bitget-api-sdk/bitget-python-sdk-api`。

1. `.claude/state/acceptance.md` — 監査の相手（設計書・プログラムが作った）
2. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/やることの表.md` — 設計書の元（やることの表＝手書きの5項目と割り当ての表）
3. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/要件のまとめ.md` — 要件のまとめ（まこさんの逐語と OK された案）
4. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/ok_stages_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
5. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/ok_todo_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
6. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/okd_stages_20261001.txt` — まこさんが OK した CC の文（逐語・gen_verbatim.py が記録から抜き出した）
7. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_14b_20260928.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
8. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_k1_20260918.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
9. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_m27_20260928.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
10. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_m2_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
11. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/req_split_20261001.txt` — まこさんの発言（逐語・gen_verbatim.py が記録から抜き出した）
12. `SDK/.claude/ratchet/m2_todo.json` — やることリスト（番号 M2-F-7・M2-F-13b の行）
13. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
14. `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md` — 承認した版の設計書の控え（どの版の 4-20 で当てたかは Q4 で照らす）
15. `SDK/.claude/audits/applied_fixes.json` — 当てた記録（名前 design:m2f-label-builder-stages-20261001 の行）
16. `SDK/scripts/priority_rebuild/engine_tuner_gen.py` — 直す相手
17. `SDK/scripts/priority_rebuild/regime_r9_diag.py` — 直す相手
18. `SDK/scripts/priority_rebuild/recipes/search_limits.json` — 直す相手

<!-- 項目: 大目的の注記 -->
⚠️ 本監査スコープ = 設計書 `m2f-label-builder-stages-20261001` の実装の指示のとおりに、当てる道具が実装を作れているか（設計書と実装の照合）。あわせて、まこさんの要望（逐語）を、この工事の後の実装が満たしているか（問い2・Q7）。守りの穴探し（すり抜けの道を新しく探すこと）は対象外（探すたびに新しい穴が出て終わらないため・恒久の決まり65番。穴は作業が実際に止まったときに直す）。

engine_tuner の目的は「net 利益を最大にする条件（指標・閾値・時間・パラメータ）の組み合わせを見つけられる機械を作ること」です（まこさん確定 2026-08-06）。この監査の範囲は、設計書 `m2f-label-builder-stages-20261001` の中身です。

<!-- 項目: 事実データ 名前=設計書の実装の指示の一覧（4-20・当てる道具が当てる相手） -->
| 番号 | 対象のファイル | 直す箇所 | 種類 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | stage_keep_of の上端の検査（B-1） | 直した後の文字 |
| 2 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | stage_keep_of の説明の文（B-1） | 直した後の文字 |
| 3 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | sample_regime_build の off_c（B-2） | 直した後の文字 |
| 4 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | build_stage_candidates の見た条件の入れ物（B-5） | 足す文字 |
| 5 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | build_stage_candidates の条件を作った後（B-5） | 足す文字 |
| 6 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | STAGE_SPEC の段1（B-6） | 直した後の文字 |
| 7 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | STAGE_SPEC の段2c（B-6） | 直した後の文字 |
| 8 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | selftest の前に、T48 の本体 selftest_stages を足す（B-1・B-2・B-5・B-6） | 直した後の文字 |
| 9 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | selftest の T46 の後ろで T48 を呼ぶ（B-1・B-2・B-5・B-6） | 足す文字 |
| 10 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 旗 --selftest-stages を足す | 足す文字 |
| 11 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 旗 --selftest-stages の口 | 足す文字 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | _loosened_off の not の中身の緩める向き（B-2） | 直した後の文字 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_stage の前に、段1 の両側と差し戻しの枠の関数を足す（B-3・B-4） | 直した後の文字 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_stage の段1 で両側の帯を測る（B-3） | 足す文字 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の _measure_one の印に枠も持たせる（B-4） | 直した後の文字 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（1/6） | 直した後の文字 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（2/6） | 直した後の文字 |
| 18 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（3/6） | 直した後の文字 |
| 19 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（4/6） | 直した後の文字 |
| 20 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（5/6） | 直した後の文字 |
| 21 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | run_sweep の枠の入れ直し（B-4）（6/6） | 直した後の文字 |
| 22 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | selftest の⑤の前に ⑭⑮⑯ を足す（B-2・B-3・B-4） | 直した後の文字 |
| 23 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | stage_keep_range の hi（K-1） | 直した後の文字 |

<!-- 項目: 事実データ 名前=当てた記録（applied_fixes.json の名前 design:m2f-label-builder-stages-20261001） -->
| 番号 | 対象のファイル | 当て方 | 時刻 |
|---|---|---|---|
| 1 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 2 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 3 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 4 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 5 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 6 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 7 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 8 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 9 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 10 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 11 | `SDK/scripts/priority_rebuild/engine_tuner_gen.py` | 当てた | 2026-10-01T17:54:40 |
| 12 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 13 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 14 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 15 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 16 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 17 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 18 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 19 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 20 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 21 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 22 | `SDK/scripts/priority_rebuild/regime_r9_diag.py` | 当てた | 2026-10-01T17:54:40 |
| 23 | `SDK/scripts/priority_rebuild/recipes/search_limits.json` | 当てた | 2026-10-01T17:54:40 |

<!-- 項目: 監査対象 -->
- Q1：実装の指示を当てた結果が、実装の後と1文字も同じか
- Q2：実装の指示のどれにも当たらない行（設計書に無い変更）が無いか
- Q3：当てた記録が、実装の指示の全部と1件ずつ合うか
- Q4：承認した版の設計書どうしで、実装の指示が同じか
- Q5：実装の指示が、やることの表の要件を全部 満たすか
- Q6：完成の条件が、実装の後に本当に成り立つか
- Q7：まこさんの要望（逐語）を、この工事の後の実装が満たしているか（問い2）

<!-- 項目: 監査対象外 -->
- 守りの穴探し（すり抜けの道を新しく探すこと）＝探すたびに新しい穴が出て終わらない（恒久の決まり65番）。穴は作業が実際に止まったときに直す
- 答え合わせの札の構造（14a＝札の部品・設定・版）を、この工事に入れない（案が1回の返信に収まらない（実装の指示が約10万文字）。別の工事に分ける）
- 固定のレシピ r9_demand_fixture.json の出る線を直さない（このレシピは需給の列が足されるかを測るための物で、出る線の向きは測る中身に関係しない。直すと、直す前と同じ結果が出ることを確かめる条件（壊すプログラム b97）が崩れる）
- 段の走行（M2-F-8〜15）は、この工事の実装に入れない（実装の後に、時間の見込みをフロー宣言に書いてから走らせる（恒久60〜62番））

<!-- 項目: 問い 番号=Q1 優先度=A 理由=違えば、実装は設計書のとおりに作られていない 名前=実装の指示を当てた結果が、実装の後と1文字も同じか -->
実装の前（HEAD の commit e31d6e8（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））の対象のファイル（`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）に、設計書 4-20 の実装の指示（23 件）を番号の順に当てた結果が、実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））と1文字も同じか。確かめ方の例＝作業場に git show で実装の前のファイルを出し、直す前の文字を直した後の文字（足す文字なら直す前の文字＋足す文字）に置き替えて、実装の後と diff を取る。

<!-- 項目: 問い 番号=Q2 優先度=A 理由=在れば、設計書に無い変更が実装に混ざっている 名前=実装の指示のどれにも当たらない行（設計書に無い変更）が無いか -->
実装の前（HEAD の commit e31d6e8（承認の控えをまだ commit していないので、実装の前は HEAD の版。`git show HEAD:<パス>` で出せる））と実装の後（作業中の変更（まだ commit していない。`git diff HEAD -- <パス>` で見られる））の差分（`SDK/scripts/priority_rebuild/engine_tuner_gen.py`・`SDK/scripts/priority_rebuild/recipes/search_limits.json`・`SDK/scripts/priority_rebuild/regime_r9_diag.py`）のうち、実装の指示のどれにも当たらない行は在るか。在れば全部 挙げる。

<!-- 項目: 問い 番号=Q3 優先度=A 理由=合わなければ、どの件を道具が当てたかを後から確かめられない 名前=当てた記録が、実装の指示の全部と1件ずつ合うか -->
当てた記録（`SDK/.claude/audits/applied_fixes.json` の名前 `design:m2f-label-builder-stages-20261001`）が、実装の指示の 23 件と1件ずつ（番号・対象のファイル）合うか。「当てた」か「もう当て終わっていた」のどちらでも入っていない件は在るか。「もう当て終わっていた」の件は、どの実行で当たったか（当てる道具の出力・git の差分）で確かめる。

<!-- 項目: 問い 番号=Q4 優先度=B 理由=当てた版と、いまの版の実装の指示が違えば、どちらの版のとおりかが決まらない 名前=承認した版の設計書どうしで、実装の指示が同じか -->
承認した版の設計書の控え（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md`・`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md`）と、いまの設計書の 4-20 の実装の指示は同じか。違えば、違いが実装に影響するか。

<!-- 項目: 問い 番号=Q5 優先度=B 理由=要件に在るのに実装の指示に無ければ、設計書のとおりに作れても依頼が満たされない 名前=実装の指示が、やることの表の要件を全部 満たすか -->
実装の指示は、やることの表（`v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/verbatim/m2f-label-builder-stages-20261001/やることの表.md`）の一覧の要件を全部 満たすか。要件に在るのに実装の指示に無いもの・実装の指示に在るのに要件に無いものは在るか。

<!-- 項目: 問い 番号=Q6 優先度=B 理由=成り立たなければ、承認のときの「済」が根拠にならない 名前=完成の条件が、実装の後に本当に成り立つか -->
設計書の完成の条件（3 行）が、実装の後に本当に成り立つか。各行のコマンドを作業場か読むだけの形で走らせる（どのコマンドも `SDK` のフォルダで走らせる＝コマンドの中のパスは SDK からの相対）: `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest-stages`・`python3 scripts/priority_rebuild/regime_r9_diag.py --selftest`・`jq '.stage_keep_range.hi' scripts/priority_rebuild/recipes/search_limits.json`

<!-- 項目: 問い 番号=Q7 優先度=A 理由=満たしていない要望が在れば、まこさんの要望が届いていない（この答えが問い2 の答えになる） 名前=まこさんの要望（逐語）を、この工事の後の実装が満たしているか（問い2） -->
下に並べた まこさんの要望（逐語）を、この工事の後の実装が満たしているか。満たしていない要望を全部 挙げ、要望の番号と、足りない実装の行を示す。この問いの答えが、結論を決める問い2 の答えになる。

  - 発言 `req_14b_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 3 行）
    - `req_14b_20260928:V01` 直す範囲は全部
    - `req_14b_20260928:V02` 決めることはCCのおすすめでOK
    - `req_14b_20260928:V03` ではその不具合は修正して、ミッション達成できるようにしてほしい
  - 発言 `req_k1_20260918`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_k1_20260918:V02` →とりあえず１０本にする
    - `req_k1_20260918:V03` 結果を見て変更すると思う
  - 発言 `req_m27_20260928`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m27_20260928:V04` 了解。状況は理解した。
    - `req_m27_20260928:V05` M2-F-7 の進め方はCCの案でOK
  - 発言 `req_m2_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_m2_20261001:V01` じゃあ、milestone２の残りを早く進めてくれ。
    - `req_m2_20261001:V02` やってるふりじゃなく、ちゃんと完成しろ
  - 発言 `req_split_20261001`（まこさんの発言・外した行と CC の文の引用を除いた 2 行）
    - `req_split_20261001:V01` なんだそれ。
    - `req_split_20261001:V02` じゃあ修正せずに、分けてすすめれば


<!-- 項目: 自己申告 -->
**承認の後に設計書を作り直した**＝前の版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.01.md` と いまの版 `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/m2f-label-builder-stages-20261001.md` の違い＝ACC_CODEREF の囲みの中で 6 行・ACC_SPEC の囲みの中で 13 行・囲みの外で 6 行（実装の指示の囲み ACC_IMPL は同じ）

<!-- 項目: 自己申告 -->
**この工事の外の作業中の変更**＝`.claude/hooks/enforce_audit_docs.py`・`.claude/hooks/enforce_g2_pass.py`・`.claude/hooks/enforce_h2_pass.py`・`.claude/hooks/require_acceptance_before_impl.sh`・`.claude/hooks/require_chat_draft_before_long_reply.sh`・`.claude/hooks/require_confirm_before_act.py`・`.claude/hooks/require_read_plan_before_design.py`・`.claude/hooks/require_read_used.py`・`.claude/hooks/require_read_used.sh`・`.claude/hooks/require_request_understood.sh`・`.claude/tools/gen_audit_docs.py`・`.claude/tools/gen_review.py`・`.claude/tools/gen_verbatim.py`・`v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e38_logics.backup_20260802_005140.json`（この工事の実装の指示が当てたものではない。Q1・Q2 の差分は、この工事の対象のファイルだけで取る）
