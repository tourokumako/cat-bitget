# 設計書｜監査 cp20 の Critical 1〜3 を1本で直す（承認で空の凍結を止める・囲みの選択を1つにする・両方が空なら照合を NG にする）

TARGET: scripts/priority_rebuild/verify_design_contract.py, .claude/hooks/approve_impl.sh, .claude/hooks/require_acceptance_before_impl.sh, .claude/breaks/b23_empty_freeze_stops.sh, .claude/breaks/b24_both_empty_ng.sh, .claude/breaks/b25_block_choice_unified.sh, .claude/breaks/b26_narrowed_list_enforced.sh

NEW_FILE: .claude/breaks/b23_empty_freeze_stops.sh, .claude/breaks/b24_both_empty_ng.sh, .claude/breaks/b25_block_choice_unified.sh, .claude/breaks/b26_narrowed_list_enforced.sh

MODEL: .claude/breaks/lib.sh, .claude/breaks/b05_design_changed.sh, .claude/breaks/b12_no_record.sh, .claude/breaks/b16_breaks_write.sh

REQUIREMENTS: R17（CC が要件どおりに作っているかを、プログラムが確かめられるようにする）。M2-C-2（指標のオン・オフの印）の検収の鎖を、承認の仕組みと照合の道具の側で接続する。

**承認の状態＝未承認。**

<!-- ARC order=1 iter="freeze-fail-closed-cp20-20260905" 前提="監査 cp20 が PIVOT。M2-C-2 は『実装は完了・検収の鎖は未接続』（まこさん決定 2026-09-05）。承認スクリプトが空の impl_functions を3回 凍結し、照合の道具は両方が空なら一致で通す作りだった" 採否="未定" 狙い="承認の瞬間に空の凍結を fail-closed で止め、囲みの選択規則を extract_block の1つにし、凍結が空なら照合を比較の前に NG にする＝検収の鎖を接続してから M2-C-2 を閉じる" 内容="C1＝approve_impl.sh／C2＝approve_impl.sh と require_acceptance_before_impl.sh の囲み選択を verify_design_contract.extract_block に寄せる／C3＝verify_design_contract.check_impl_functions に『凍結が空なら NG』を足す＋番人 N13〜N17＋壊すプログラム3本" 方法="壊すプログラム3本（b23・b24・b25）を承認スクリプトが走らせ、終了コードを控えに残す。--self-test の番人 N13〜N17。完成の判定は監査（恒久の決まり64番）" -->

---

## 0｜まこさんの決定（逐語・2026-09-05）

| # | 逐語 | この設計のどこに効くか |
|---|---|---|
| 1 | 「M2-C-2 は「検収済」ではなく「実装は完了・検収の鎖は未接続」として扱います。成果物は残します。」 | §1・§7（成果物＝印・T25 の直しは残す） |
| 2 | 「【1｜最優先】Critical 1〜3 を1本の設計書にまとめて出す」 | この設計書そのもの |
| 3 | 「C1＝approve_impl.sh：凍結が空 かつ no_impl_functions_reason が無いなら exit する」 | §3.1 |
| 4 | 「C2＝囲みの選択規則を extract_block に一本化する」 | §3.2 |
| 5 | 「C3＝verify_design_contract.py：frozen が空なら比較の前に NG」 | §3.3 |
| 6 | 「★この設計書には、監査の提案 §1.4.6.4 の形式を必ず入れること。」 | §4（検査ごとに「止める／出すだけ」と「止まらないとき何が通るか」） |
| 7 | 「完成の条件には、わざと壊す確認を必ず入れること。…標準出力の貼り付けで示すこと。」 | §5・§6（壊すプログラム b23・b24・b25＋番人 N13〜N17） |
| 8 | 「【2】直したあと、--selftest を1回 走らせて鎖を接続し、M2-C-2 を閉じること。凍結された impl_functions の件数を報告すること。」 | §6 の7 |
| 9 | 「【今はやらないこと】T24②・T26・T30（M2-E）／gen_audit_request.py の拡張／指標の数そのものの見直し。」 | §3.5 |
| 10 | 「【壊すプログラムを1本 足してください】b26＝impl_functions に載せた「触る関数4件」のうち1件を抜いたとき、照合が実際に NG を出すこと。終了コードと標準出力で示すこと。」「★4件を増やせという話ではありません。4件が本当に照合されているかの確認です。」（1回目の承認のあと・2026-09-05） | §5 の10・§6 の8・§9 の O |
| 11 | 「【この書き方の変更を記録すること】next_step §6 に1行 足してください。「impl_functions の意味を、実物の全関数から触る関数へ変えた（2026-09-05・理由＝照合B の定義 impl_functions ⊆ 触った関数）」。」 | next_step §6 の132番（記録・この設計書の外） |

**★1回目の承認のあとに、この設計書を書き直した理由（2026-09-05）**＝実装に入ろうとしたら、書き込みの門が「impl_functions がありません」で止めた。門は「最初の impl_file の囲み」を契約と見る（C2 で直す当の規則）ので、SPEC の節（impl_file だけの json）が契約の節より前に在ると、SPEC を契約として読む。★これは §9 の M の不変条件が、門の側では「逆向き」に効くことの実測＝承認スクリプトは「最後」、門は「最初」を見るので、どちらの並びでも片方が壊れる。この版では契約の節（§10）を SPEC の節（§11）より前に置き、まこさんの追加（b26）を入れた。承認は取り直し（2回目）。

**★この設計書では、私は「直った」「効いている」を1件も判定しません**（恒久の決まり64番・§0-3）。壊すプログラムの終了コードと、--self-test の件数と、監査が判定します。

---

## 1｜いまの状態（監査 cp20 が実測したもの・レポート §6 の実装点をそのまま）

| # | 監査の指摘 | 実物の場所（Read tool で開いた） | いま何が起きるか |
|---|---|---|---|
| C1 | 承認の瞬間に「空の凍結」を fail-closed で止める | `.claude/hooks/approve_impl.sh` 108行 `_fz = obj.get("impl_functions") or {}` → 114行で「0 件を凍結しました」と印字するだけ | 空を凍結しても承認が通る。2026-09-04 に3回 通った（t25 の系統・空が凍結されたのは2本） |
| C2 | 囲みの選択規則を3つから1つに統一する | ①`require_acceptance_before_impl.sh` 601-608行（`break` 有り＝最初の impl_file の囲み）／②`verify_design_contract.py` 141-197行 `extract_block`（目印の行の後ろの囲み）／③`approve_impl.sh` 62-73行（`break` 無し＝最後の impl_file の囲み） | 同じ設計書を、3つの仕組みが別々の囲みで読む。SPEC の囲み（impl_file は在るが impl_functions は無い）が DC より後ろに在ると、③が SPEC を契約として凍結する |
| C3 | 「両方が空なら PASS」の穴を塞ぐ | `verify_design_contract.py` 951-953行＝design と frozen を json の文字列で比べるだけ | design が `{}` かつ frozen が `{}` なら一致＝1関数も照合していないのに「設計通り」と出る |

**成果物は残す（まこさんの決定1）**＝印 `indicator_switch.json`（使う 140種）・T25 の直し（commit b282902）・恒等3本の一致（S2・L1・S1）は、この設計書で1文字も触らない。

---

## 2｜深掘り4点

### ① 真因（root cause）

**承認・書き込みの門・照合の3か所が、それぞれ自前の規則で「どの囲みが契約か」を決め、しかも承認の側は空を「値」として受け取っていた。**空の凍結が3回 通ったのは、並び順の事故ではなく、止める処理が無かったことが真因（監査 Q1 の1）。並び順（SPEC を前に置く）は規約であって対策ではない（監査 Q2）。

### ② 期待値分解

**この設計書は売買のコードを1行も変えない。**勝率・平均利益・敗率・平均損失は1つも動かない。動くのは「設計書と実装が同じかを、機械が確かめずに通す道」が閉じるかどうかだけ。

### ③ root か symptom か

**root。**symptom の直し方＝`approve_impl.sh` の 72行に `break` を足す（最初の囲みにする）。これは取らない＝SPEC が先頭に在る設計書で同じ空の凍結が起きる（監査 Q1 の1）。root＝①空は止める（C1）②囲みの選択を1つの関数に寄せる（C2）③照合の側にも fail-closed を置く（C3）。

### ④ ベースアップ（このセッションで Read tool を使って開いたもの）

| 何を確かめたか | 出どころ |
|---|---|
| 承認スクリプトの囲みの選択と凍結の処理・承認の直後の確認・壊すプログラムの走らせ方 | .claude/hooks/approve_impl.sh（50-120行・116-280行・280-339行） |
| 書き込みの門の囲みの選択・impl_functions の判定・完成の条件の表の読み方・「塞げないもの」の判定 | .claude/hooks/require_acceptance_before_impl.sh（588-830行） |
| 照合の道具の目印の取り出し・凍結との突き合わせ・照合C・番人の並び・書き出し | scripts/priority_rebuild/verify_design_contract.py（56-105行・141-251行・442-570行・678-777行・793-883行・882-994行・1060-1130行・1211-1298行・1536-1651行） |
| 走らせる門の確認用の旗の一覧 | .claude/hooks/require_design_contract_before_run.sh（1-80行） |
| 壊すプログラムの共通の部品と見本 | .claude/breaks/lib.sh・b05_design_changed.sh・b12_no_record.sh・b16_breaks_write.sh |
| 壊すプログラムを走らせる道具（表の読み方・凍結・終了コードの記録） | .claude/tools/run_breaks.py（1-230行） |
| 監査 cp20 の Critical 1〜3・§1.4.6.4 の形式・Q1〜Q3 | v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/2026-09-05_m2c2_indicator_switch_cp20_audit_report.md（120-183行・305-364行） |
| 前の設計書（恒等 L1・S1 用）の形 | .claude/state/acceptance.md（承認済みの前の版・全文） |
| cp19 の設計書の TARGET・NEW_FILE・MODEL の書き方 | v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/impl-lock-fix-cp19-20260904.md（1-60行） |

**★WebSearch は使っていません。**うちの実物を読む話だからです。監査の業界根拠（OPA の fail-open／SLSA・in-toto の enforcement point の単一化）は、レポートの本文に在るものをそのまま採ります。

---

## 3｜何を作るか（監査の実装点のとおり・私が足すのは番人と壊すプログラムだけ）

### 3.1 C1＝承認の瞬間に、空の凍結を止める（`.claude/hooks/approve_impl.sh`）

| 何を | どう変えるか |
|---|---|
| 62-73行（自前の regex ループ） | 消す。代わりに `from verify_design_contract import contract_for_freeze` を使い、`obj, why = contract_for_freeze(md)` で契約を1つ取る（C2 と同じ関数＝選択規則が1つになる） |
| 108行 `_fz = obj.get("impl_functions") or {}` | `why` が空でなければ（＝契約が読めない／impl_functions が無い／空なのに `no_impl_functions_reason` が無い）、90-93行と同じ形で「❌ 承認を中止します（監査 cp20 の C1）」を出して `sys.exit(3)`。**止めるのは書き出す前**＝凍結ファイルを書かない |
| spec_lists の集め方（70-71行） | 契約（`obj`）の `spec_lists` だけを読む（いままでは「どの囲みでも `spec_lists` が在れば集める」だった＝これも選択規則の1つだったので、同じ関数に寄せる） |
| 「正しい空」（cp19 の形） | `no_impl_functions_reason` が在る空は通す。凍結は今までどおり `{}` を書く（C3 が「理由が在る空」を区別する） |

### 3.2 C2＝囲みの選択規則を `extract_block` の1つにする

| どこ | 何を |
|---|---|
| `scripts/priority_rebuild/verify_design_contract.py`（新設 `contract_for_freeze(md_text)`） | `extract_block(md_text, CONTRACT_MARK)` で契約を取り、①読めない ②`impl_functions` が辞書でない ③空で `no_impl_functions_reason` が無い、のどれかなら `(None, 理由の文)`。それ以外は `(契約, None)`。**承認スクリプトと壊すプログラムが、同じこの1つを呼ぶ** |
| 同（`__main__` に旗 `--freeze-contract <設計書>` を足す） | `contract_for_freeze` を呼び、通れば契約の json を標準出力に出して 0、通らなければ理由を stderr に出して **3** で終わる。**★壊すプログラム b23 がこの口で測る**（承認スクリプトを CC が走らせられないため） |
| `.claude/hooks/approve_impl.sh` | §3.1 のとおり `contract_for_freeze` を呼ぶ |
| `.claude/hooks/require_acceptance_before_impl.sh` 600-608行 | 自前の regex ループを消し、`sys.path` に道具の場所を足して `from verify_design_contract import extract_block` → `obj, _why = extract_block(md, "DESIGN_CONTRACT")`。読めないときの文を「DESIGN_CONTRACT（目印の行の後ろの json）が読めません（理由）」にする。**★道具が import できないときは `ng` に「照合の道具を読み込めません」を足して止める**（黙って通さない・§4 の13） |

**★これで「どの囲みが契約か」の解釈は `extract_block` の1つになる。**並び順の不変条件 A（SPEC を前に置く）・B（SPEC の見出しに目印の語を書かない）は、承認と門の側では要らなくなる（監査 Q2）。★`extract_block` 自身は変えない（B の「見出しに目印の語が在ると目印と数える」は残る＝§9 の M）。

### 3.3 C3＝凍結が空なら、比較の前に NG（`verify_design_contract.py` の `check_impl_functions`）

| 何を | どう変えるか |
|---|---|
| 945-953行（凍結を読んだ直後・json の文字列比較の前） | `if not frozen and not contract.get("no_impl_functions_reason"): ng.append("凍結された impl_functions が空です（承認のときに空が凍結された疑い・監査 cp20 の C3）…"); return ng` を足す。**控え（`<iter>.frozen.json`）の経路にも、いま作業している設計書の経路にも効く**（凍結を読んだ後の1か所に置くため） |
| 理由が在る空 | 通す＝今までどおり文字列で比べる（design も空なら一致・cp19 の控えは落とさない） |

### 3.4 番人（`--self-test` に足す・`SELF_TESTS` の末尾）

| # | 何を試すか | 期待 |
|---|---|---|
| N13 | `check_impl_functions({"impl_functions": {}}, md, frozen={})`（理由なし） | 「凍結された impl_functions が空です」が `ng` に在る |
| N14 | 同じ入力に `no_impl_functions_reason` を足す | その文が `ng` に無い（理由が在る空は通す） |
| N15 | 文書＝DESIGN_CONTRACT（impl_functions 3件）の後ろに、impl_file だけの json の囲み（SPEC の形）を置く → `contract_for_freeze` | 戻りが DESIGN_CONTRACT の側（impl_functions が3件） |
| N16 | 文書＝impl_file だけの囲みを**先**に置き、DESIGN_CONTRACT を後ろに置く → `contract_for_freeze` | N15 と同じ戻り（並び順に影響されない） |
| N17 | 文書＝DESIGN_CONTRACT の impl_functions が `{}` で理由なし → `contract_for_freeze` | `(None, 理由)`＝止まる側 |

### 3.5 触らないもの

- `engine_tuner_gen.py`・`engine_tuner_exec.py`＝1文字も変えない（`--selftest` を1回 走らせるだけ・まこさんの決定8）。
- `extract_block`（141-197行）＝変えない。
- T24②・T26・T30（M2-E）／`gen_audit_request.py`／指標の数の見直し／指標の増減の関所（Major 4）＝着手しない（まこさんの決定9）。

---

## 4｜★§1.4.6.4 の形式（監査 cp20 §7 の提案・検査ごとに「止める／出すだけ」と「止まらないとき何が通るか」）

> **§1.4.6.4 「止める」と「出す」を分けて宣言する義務**（監査の逐語）＝強制の仕組みを新設・改訂するとき、各検査について ①止める検査か、出すだけの検査か（exit する／しない）②止まらないとき何が通ってしまうか、を1行ずつ書く。

| # | どこ | 検査 | 止める／出すだけ | 通ってしまうもの（fail-open の内容） | この設計で変わるか |
|---|---|---|---|---|---|
| 1 | approve_impl.sh | spec_lists を正本から展開できない | 止める（exit 3） | — | 変えない |
| 2 | approve_impl.sh | 契約が読めない／impl_functions が無い／空で理由なし | **止める（exit 3・凍結を書く前）** | （止める側にするので無し） | **★新設（C1）。直す前＝「0 件を凍結しました」と出すだけ＝空の凍結が通っていた** |
| 3 | approve_impl.sh | 方針③の件数（機械で照らせる／照らせない） | 出すだけ | 件数が増減しても承認は通る（まこさんが件数を見て理由を聞く仕組み・監査 §6-A の3） | 変えない |
| 4 | approve_impl.sh | impl_functions が実物の全関数と同じ（⚠️） | 出すだけ | 実装から作った期待値でも承認は通る（⚠️ が出続けるのが正しい状態・まこさん指定 2026-09-03） | 変えない |
| 5 | approve_impl.sh | 承認の直後の `--check-approval` | 止める（承認を取り消す） | — | 変えない |
| 6 | approve_impl.sh | 壊すプログラムの凍結と走行（run_breaks.py） | 止める（承認を取り消す） | — | 変えない |
| 7 | verify_design_contract.py check_impl_functions | 照合の道具の承認の印が無い／道具が変わっている | 止める（ng） | — | 変えない |
| 8 | 同 | 控えに凍結が無い／読めない | 止める（ng） | — | 変えない |
| 9 | 同 | **凍結が空（理由なし）** | **止める（ng・比較の前）** | （止める側にするので無し） | **★新設（C3）。直す前＝design も空なら一致で通した＝1関数も照合せずに「設計通り」** |
| 10 | 同 | design と frozen の文字列が違う | 止める（ng） | — | 変えない |
| 11 | 同 | 差分がゼロのとき照合A を判定できない（[INFO]） | 出すだけ | 触っていない関数が在っても、差分がゼロなら照合A は走らない（照合B だけ全関数と行う・監査 cp13 の A-3 の指示どおり） | 変えない |
| 12 | require_acceptance_before_impl.sh | 契約が読めない | 止める（rc 2） | — | **★読む規則を extract_block に替える（C2）。直す前＝最初の impl_file の囲みを契約と見た** |
| 13 | 同 | 照合の道具を import できない | **止める（ng・rc 2）** | （止める側にするので無し） | **★新設。**直す前は道具を使っていなかったので該当なし。★これを「出すだけ」にすると、道具が壊れたとき門が黙って開く |
| 14 | 同 | impl_functions が空で理由なし | 止める（rc 2） | — | 変えない（C1 はこの判定を承認の側にも置くもの） |
| 15 | verify_design_contract.py `--freeze-contract` | contract_for_freeze が理由を返す | 止める（rc 3） | — | **★新設（壊すプログラム b23 の測る口）** |

**★「出すだけ」の3件（3・4・11）を「担保」「守っている」とは書きません**（監査 §1.4.6.4＝そう書けば類型 G）。

---

## 5｜わざと壊して止まるか試すテスト（標準出力をそのまま貼る・私は「通った」と文章で書かない）

| # | 何を試すか | 期待する結果 | 誰が走らせるか |
|---|---|---|---|
| 1 | `python3 scripts/priority_rebuild/verify_design_contract.py --self-test` | N13〜N17 が「期待どおり」・件数が 35/35（いま 30/30＝2026-09-05 に走らせた・＋5） | 私（実装の直後・出力を貼る） |
| 2 | 1 のあと、C3 の1行（`if not frozen and not …`）を一時的に外して `--self-test` | N13 が「★合わない」になり、件数が 34/35 に減る。戻して 35/35 | 私（出力を貼る・外した行は必ず戻す・`git diff` が実装分だけになることを貼る） |
| 3 | 1 のあと、`contract_for_freeze` の「空で理由なし」の分岐を一時的に外して `--self-test` | N17 が「★合わない」になり 34/35。戻して 35/35 | 私（同上） |
| 4 | `bash .claude/breaks/b23_empty_freeze_stops.sh; echo rc=$?`＝設計書の写しの impl_functions を `{}` にし理由を消して `--freeze-contract` → rc 3 ／ 理由を足した写し → rc 0。両方 成り立つときだけ 1 | 1（止まった） | 承認スクリプト（run_breaks.py）。私も承認の前に1回 走らせて出力を貼る |
| 5 | `bash .claude/breaks/b24_both_empty_ng.sh; echo rc=$?`＝一時の場所に、impl_functions `{}`・理由なしの控えと `{}` の凍結を並べて照合 → 出力に「凍結された impl_functions が空です」が在れば 1 | 1 | 同上 |
| 6 | `bash .claude/breaks/b25_block_choice_unified.sh; echo rc=$?`＝設計書（控えを取って戻す）を「impl_file だけの囲みが先・目印の行の DESIGN_CONTRACT が無い」中身に替え、書き込みの門を Write の入力で呼ぶ → stderr に「DESIGN_CONTRACT（目印の行の後ろの json）が読めません」が在れば 1 | 1 | 同上 |
| 7 | 承認と実装のあと `python3 scripts/priority_rebuild/verify_design_contract.py .claude/state/acceptance.md` | 照合A・B が PASS（凍結の impl_functions が §10 の4件と同じ・空でない）。★実装の差分が commit される前は、触っていない関数を照合B が「設計書に書いたのに実装していない」と言う作りなので、貼るのは出力そのもの | 私（出力を貼る） |
| 8 | 承認の前に、同じ照合 | NG（契約に書いた `contract_for_freeze` が実物に無い＝配線が無い） | 私（出力を貼る） |
| 9 | 【2】`python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest`（1回だけ・時間の見込み＝約6分・過去の実測「18分20秒」は3回分＝1回 約6分） | ❌ 0件（T24②・T26・T30 は M2-E で未着手なので、その3件は ❌ のまま出る＝そのまま貼る）。凍結された impl_functions の件数を報告 | 私（出力を貼る） |
| 10 | `bash .claude/breaks/b26_narrowed_list_enforced.sh; echo rc=$?`＝いまの設計書の写しを一時の場所に作り、契約の impl_functions から1件（`contract_for_freeze`）を抜き、同じ1件を抜いた凍結（`<名前>.frozen.json`）を並べて照合 → 出力に「設計書に書いていない関数を触った → contract_for_freeze」（照合A）が在れば 1。★まこさんの追加（決定10）＝「触る関数4件」に絞った見張りが効いているかの確認 | 1 | 承認スクリプト（run_breaks.py）。私も走らせて出力を貼る |

**★壊すプログラムは承認の後にしか書けない**（書き込みの門が `.claude/breaks/*.sh` を止める＝G-2）。**承認は3回 要る**＝①1回目（済・2026-09-05）②この書き直した版の承認（壊すプログラム4本は「MISSING」と記録される）③実装と壊すプログラムを書いたあとの再承認（凍結に4本が入り、走って終了コードが記録される）。★cp19 と同じ手順に、書き直しの1回が足された。**★②の承認スクリプトは まだ直す前の版**（C1・C2 が入るのは②のあと）＝「最後の impl_file の囲み」＝§11 の SPEC を契約と読み、**空を凍結する**（監査 cp20 の Q1 と同じ事故がもう1回 起きる）。その出力（「0 件を凍結しました」）をそのまま記録に残す。③では直した承認スクリプトが §10 の契約を取り、4件を凍結する。

---

## 6｜何ができたら完成か

<!-- ACCEPT_TABLE_START -->

**★「経路」＝`実経路`（コマンドで走らせた）か `部品`（関数を直接 呼んだ）。**
**★「壊すプログラム」＝承認スクリプトが走らせ、終了コードを控えに残す（0 以外のときだけ「済」の印を書ける）。私は「済」の印を書かない＝判定は監査（恒久の決まり64番）。**

| # | 完成の条件 | 経路 | 壊し方 | 壊すプログラム | 監査確認 | いまの状態 |
|---|---|---|---|---|---|---|
| 1 | C1＝impl_functions が空で理由なしの設計書は、承認の瞬間に exit 3 で止まり、凍結ファイルを書かない（AUDIT-1） | 実経路 | §5 の4（写しの impl_functions を `{}` にして理由を消す） | b23_empty_freeze_stops.sh | 対象 | **未着手** |
| 2 | C1 の対＝`no_impl_functions_reason` が在る空（cp19 の形）は承認が通る | 実経路 | §5 の4 の後半（理由を足した写しで rc 0） | b23_empty_freeze_stops.sh | — | **未着手** |
| 3 | C2＝書き込みの門・承認・照合の3つが `extract_block` で契約を選ぶ＝impl_file だけの囲みが先に在っても契約と読まない（AUDIT-2） | 実経路 | §5 の6（目印の行を消した設計書で門を呼ぶ） | b25_block_choice_unified.sh | 対象 | **未着手** |
| 4 | C3＝design も frozen も `{}` で理由なしなら、照合が比較の前に「凍結された impl_functions が空です」で NG（AUDIT-3） | 実経路 | §5 の5（空の控えと空の凍結を並べる） | b24_both_empty_ng.sh | 対象 | **未着手** |
| 5 | 番人 N13〜N17 が `--self-test` で「期待どおり」・C3 の1行を外すと N13 が「★合わない」になる | 実経路 | §5 の2・3（判定の行を一時的に外す） | — | — | **未着手** |
| 6 | 承認と実装のあと、単体の照合で凍結の impl_functions が §10 の4件と同じ（空でない） | 実経路 | §5 の8（承認の前は NG） | b06_tool_changed.sh | — | **未着手** |
| 7 | 【2】`engine_tuner_gen.py --selftest` を1回 走らせ、凍結された impl_functions の件数と ❌ の一覧を貼る（AUDIT-4） | 実経路 | §5 の9 | — | 対象 | **未着手** |
| 8 | b26＝impl_functions の「触る関数4件」から1件を抜くと、照合A が「設計書に書いていない関数を触った」で NG（まこさんの決定10） | 実経路 | §5 の10（写しと凍結の両方から `contract_for_freeze` を抜く） | b26_narrowed_list_enforced.sh | — | **未着手** |

<!-- ACCEPT_TABLE_END -->

**★私が自分で合格ラインを引いていないこと**＝1〜4 は監査 cp20 の Critical 1〜3 の文そのもの。7 はまこさんの決定8そのもの。
**★「完成」の判定は私がしません**（恒久の決まり64番）。終了コードと標準出力をそのまま貼るだけです。

---

## 7｜既存を壊さないこと（副作用）

| 何が | どうなるか |
|---|---|
| いま承認されている設計書（恒等 L1・S1 用）の控えと凍結（101件・空でない） | 残る（別の iter 名） |
| cp19 の控え（`impl-lock-fix-cp19-20260904` の凍結＝理由の在る空） | C3 は理由の在る空を通す＝落とさない。★実装のあと、その控えを照合して落ちないことを出力で貼る |
| 印（`indicator_switch.json`・使う 140種）・T25 の直し・恒等3本の一致 | 1文字も触らない（まこさんの決定1） |
| H2 の印・G2 の印 | 取り直し不要（engine_tuner の経路のコードに触れない。`verify_design_contract.py` と hook は H2 の印の一覧（22件）にも G2 の印の一覧（37件）にも無い＝2026-09-05 に `h2_pass.json`・`g2_pass.json` を Read tool で開いて確かめた） |
| 承認スクリプトの `from verify_design_contract import resolve_spec_list` の実績（58行） | 同じ形で `contract_for_freeze` も import する＝新しい依存は増えない |
| 書き込みの門の実行時間 | `verify_design_contract` の import が1回 増える（重い処理は無い＝`ast`・`json`・`re` だけ） |
| いま採用している戦略（E36 ほか） | 触らない |

---

## 8｜照合（群2＝まとめて非該当の1行）

**H1〜H16 と審判整合（群2の18件）は、まとめて非該当です。**理由＝売買のコードを1行も変えず、売買記録を1本も書かず、`score.py` と `eval_engine.py` に1行も触れないためです。

**★1変更か（H16）**＝監査が「1本の設計書に」と指定した3件（C1・C2・C3）を、同じ穴（囲みの選択と空の凍結）の直しとして1つに束ねています。番人と壊すプログラムは、その3件を測るもので、別の変更ではありません。

**★過去に破棄した失敗の再演か**＝当たりません。cp13〜cp19 で7回 続いた「実装した」を「効いている」と読み替える型（L-586）に対し、この設計書は ✅ を1つも書かず、終了コードと標準出力だけを貼ります。

---

## 9｜★正直に書く｜それでも塞げないもの

**塞げないもの（この設計の範囲で残る穴）**

| # | 塞げないもの | なぜ塞げないか | 何が代わりに守るか |
|---|---|---|---|
| I | **`no_impl_functions_reason` の中身は機械が見ない**＝何か1文字でも書けば「正しい空」として通る | 理由の真偽は文章の意味＝プログラムでは判定できない | 方針③の件数（「設計書に書いた理由」の件数が画面に出る）＋まこさんの目 |
| J | **凍結ファイルを承認のあとに手で `{}` に書き換える道** | 印の偽造は機械では見抜けない（H2・G2 と同じ限界・明示の違反） | C3 が「空」を止める＝書き換えて空にした時点で照合が NG になる。ただし理由の在る設計書なら通る（I と同じ） |
| K | **承認が2回 要る**＝壊すプログラム3本は承認の後にしか書けないので、1回目の承認では「MISSING」と記録され、終了コードは2回目の承認で初めて残る | 書き込みの門が `.claude/breaks/*.sh` を止める（G-2）＝承認の前に骨抜きにできない代わりに、承認の前に書けない | 2回目の承認（cp19 と同じ手順）。1回目と2回目の間に壊すプログラムを書き換えられる道は、2回目の承認で凍結されるまで残る（run_breaks.py の限界③と同じ） |
| L | **`--freeze-contract` は承認スクリプトそのものではない**＝b23 が測るのは「同じ関数を同じ口で呼んだときの終了コード」で、承認スクリプトの中でその戻りを exit 3 につないでいるかは b23 では測れない | 承認スクリプトを CC は走らせられない（b13 が守る） | 実装の差分（`git diff` の全文を貼る）＋監査が承認スクリプトの行を読む（AUDIT-1） |
| M | **`extract_block` の「見出しに目印の語が在れば目印」は残る**（監査 Q2 の不変条件 B） | `extract_block` は変えない（1変更の外・変えると T1〜T17 と3つの仕組みの全部に影響する） | 承認と門と照合が同じ関数を見るので、B を破ると3つとも同じ側（設計書の側が空）に落ち、C3 が止める（両方が空になる道は閉じる） |
| N | **照合B は、実装の差分が commit される前は「触っていない関数」を落とす**（`check_impl_functions` 978-981行＝impl_functions ⊆ 触った関数）＝§5 の7 の出力は commit の前後で変わる | 照合の道具の作り（監査 cp13 の A-3 のとおり）。commit はまこさんの OK が要る | 出力をそのまま貼る（commit の前と後の両方） |
| O | **b26 の結果も commit の前後で変わる**＝差分がゼロだと照合A は走らず（§4 の11）、抜いた1件はファイルに在るので照合B も落とさない＝b26 は「実装の差分が在るとき」だけ 1 を返す | 照合A が git の差分で触った関数を集める作り（`touched_functions`） | 3回目の承認（commit の前）で走らせて終了コードを記録する。commit のあとに走らせた結果も貼る（0 になるはず＝その旨を書く） |
| P | **1回目の承認で、書き込みの門が SPEC の囲みを契約と読んで実装を止めた**＝この版で契約の節を前にしたが、2回目の承認（直す前の承認スクリプト）は「最後の impl_file の囲み」＝SPEC を取って空を凍結する | 承認スクリプトを直す（C1・C2）には、その前に承認が要る＝直す前の版で1回 通るしかない | 3回目の承認で直した版が4件を凍結する。2回目の「0 件を凍結しました」は記録に残す（§5 の末尾） |

**★強制の土台そのものの穴（監査 cp14 の Q5 の5件・cp19 で「閉じない部分」として確定＝`lessons_active.md` の L-586。この設計は1つも塞がない・受け入れ条件ゲートが毎回 書かせる）**

| # | 塞げないもの | この設計での扱い |
|---|---|---|
| D | **照合D が実経路で1度も走っていない**（監査 Q5 の1） | この設計書も `spec_lists` は空（理由は §10 の `no_spec_lists_reason`）＝照合D はこの回も走らない |
| E | **照合の道具と印を、私が書ける場所に置いたまま**（監査 Q5 の2） | 触らない。J-6（外部CI）は まこさん決定で着手しない（L-586） |
| F | **照合A・B の期待値が、実装から作られる**（監査 Q5 の3） | この回の `impl_functions` は「触る関数4件」を手で列挙したもの＝実装から作っていない（§10 の `generated_from`）。承認の画面には 📐（設計書の側が出どころ）が出るはず＝その出力を貼る |
| G | **語を並べて迂回を塞ぐやり方は、原理的に閉じない**（監査 Q5 の4） | 触らない。この設計は書き込みの門の語の一覧を1つも変えない |
| H | **承認の記録を全部 消したときを測っていない**（監査 Q5 の5） | 測らない（まこさんの一覧の外・cp19 で確定） |

---

## 10｜DESIGN_CONTRACT

**★`impl_functions` は「この回で触る関数」だけを列挙したものです（手書き・4件）。**理由＝照合A（触った関数 ⊆ impl_functions）と照合B（impl_functions ⊆ 触った関数）の定義に合わせるため。`python3 .claude/tools/gen_impl_functions.py scripts/priority_rebuild/verify_design_contract.py` の出力（32件・2026-09-05 に走らせた）のうち触る3件＋新設1件。★新設の `contract_for_freeze` は道具の出力に無いので、手で足しました。

```json
{
  "impl_file": "scripts/priority_rebuild/verify_design_contract.py",
  "impl_functions": {
    "scripts/priority_rebuild/verify_design_contract.py": [
      "<モジュール直下>",
      "check_impl_functions",
      "contract_for_freeze",
      "self_test"
    ]
  },
  "self_check_calls": [
    "contract_for_freeze",
    "no_impl_functions_reason",
    "凍結された impl_functions が空です"
  ],
  "must_use": {
    "contract_for_freeze": ["extract_block", "CONTRACT_MARK"],
    "check_impl_functions": ["frozen_impl_functions"],
    "self_test": ["contract_for_freeze", "check_impl_functions"]
  },
  "spec_lists": {},
  "no_spec_lists_reason": "この設計書は承認の仕組みと照合の道具を直すもの。照合D の相手になる正本の配列（機械が読む一覧）は存在しない。",
  "generated_from": {
    "impl_functions": "手書き＝この回で触る関数4件（<モジュール直下>＝SELF_TESTS と __main__ の旗／check_impl_functions＝C3／contract_for_freeze＝新設／self_test＝N13〜N17）。gen_impl_functions.py の出力32件（2026-09-05）のうち触る3件＋新設1件。実物の全関数の写しではない",
    "must_use": "手書き＝§3.2・§3.3 の設計から（contract_for_freeze は extract_block と CONTRACT_MARK を使う／check_impl_functions は frozen_impl_functions を使う／self_test は新しい2つを呼ぶ）",
    "self_check_calls": "手書き＝新設の関数名・理由の鍵の名前・C3 の文（3つとも実装の後に文字として在るはずのもの）",
    "spec_lists": "無し（理由は no_spec_lists_reason）"
  }
}
```

---

## 11｜SPEC（★この節は `verify_design_contract.py --write` が照合の道具そのものから書き出したものを貼り、今回 足す1件（`contract_for_freeze`）と旗（`--freeze-contract`）だけを手で足す。★この節は契約の節（§10）の後ろに置く＝書き込みの門が「最初の impl_file の囲み」を契約と見るため（C2 で直す当の規則・§0 の末尾）。★見出しに契約の目印の語は書かない）

**出どころ**＝`python3 scripts/priority_rebuild/verify_design_contract.py --write .claude/state/acceptance.md`（2026-09-05・公開する関数 28件／定数 3件／コマンドの旗 6件）。**手で足した3か所**＝①`contract_for_freeze`（新設・`extract_block` を呼ぶ）②`self_test` の呼ぶ名前に `contract_for_freeze` ③旗 `--freeze-contract`。それ以外は書き出しのまま。★実装のあと `--diff` を走らせ、齟齬の件数をそのまま貼る。

SPEC

```json
{
 "impl_file": "scripts/priority_rebuild/verify_design_contract.py",
 "public_functions": {
  "outside_fence_lines": [],
  "extract_block": [
   "outside_fence_lines"
  ],
  "extract_contract": [
   "extract_block"
  ],
  "contract_for_freeze": [
   "extract_block"
  ],
  "rhs_names_for_symbol": [],
  "scan_contracts": [
   "extract_block"
  ],
  "spec_from_impl": [],
  "spec_from_design": [
   "extract_block"
  ],
  "diff_spec": [],
  "write_actual": [
   "extract_block",
   "scan_contracts",
   "spec_from_impl"
  ],
  "requirements_index": [],
  "extract_requirements": [
   "outside_fence_lines"
  ],
  "req_map": [
   "extract_requirements",
   "requirements_index",
   "scan_contracts"
  ],
  "format_req_map": [],
  "check_approval": [],
  "load_spec_lists": [],
  "frozen_impl_functions": [],
  "resolve_spec_list": [
   "must_use_from_source"
  ],
  "names_in_function": [],
  "functions_ast": [],
  "head_source": [],
  "touched_functions": [
   "functions_ast",
   "head_source"
  ],
  "check_impl_functions": [
   "frozen_impl_functions",
   "functions_ast",
   "touched_functions"
  ],
  "must_use_from_source": [],
  "check_must_use": [
   "must_use_from_source",
   "names_in_function"
  ],
  "probe_spec_lists": [],
  "check_spec_lists": [
   "probe_spec_lists"
  ],
  "check": [
   "check_impl_functions",
   "check_must_use",
   "check_spec_lists",
   "extract_contract",
   "rhs_names_for_symbol"
  ],
  "self_test": [
   "check_approval",
   "check_impl_functions",
   "check_must_use",
   "check_spec_lists",
   "contract_for_freeze",
   "diff_spec",
   "extract_block",
   "extract_requirements",
   "format_req_map",
   "frozen_impl_functions",
   "must_use_from_source",
   "probe_spec_lists",
   "req_map",
   "resolve_spec_list",
   "scan_contracts",
   "spec_from_design",
   "spec_from_impl",
   "touched_functions",
   "write_actual"
  ]
 },
 "constants": {
  "CONTRACT_MARK": "DESIGN_CONTRACT",
  "SPEC_MARK": "SPEC",
  "REQ_MARK": "REQUIREMENTS:"
 },
 "cli_flags": [
  "--check-approval",
  "--diff",
  "--freeze-contract",
  "--req-map",
  "--scan-contracts",
  "--self-test",
  "--write"
 ]
}
```

---

## 12｜まこさんにお願いすること

**2回目の承認の1点です**（`approve_design.sh` と `approve_impl.sh`）。★この承認では、直す前の承認スクリプトが「0 件を凍結しました」と出すはずです（§5 の末尾・§9 の P）。それで構いません＝止めずに通してください。承認のあと、§3 のとおり実装し、壊すプログラム4本（b23〜b26）を書き、§5 の1〜8・10 の出力を貼って、**3回目の承認**をお願いします（壊すプログラムの凍結と終了コードの記録のため）。そのあと §5 の9（`--selftest` 1回）を走らせ、凍結された impl_functions の件数を報告します。
