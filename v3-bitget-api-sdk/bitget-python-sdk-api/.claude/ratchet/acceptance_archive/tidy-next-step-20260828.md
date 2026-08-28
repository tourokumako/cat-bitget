# acceptance.md — next_step.md が毎回 汚れて、まこさんが指示しないと整理されない件を、機械で直す（tidy_next_step.py ＋ Stop hook）

<!-- ARC order=70 iter="tidy-next-step-20260828" 前提="fast-mode ON・実験ゼロ・売買記録0本・next_step.md は69回目の末に手で整理した（353行 → 247行・worklog 20260828 §1）" 採否="未" base_csv="none" score_csv="none" train_csv="none" 狙い="next_step.md の §0 を、人（CC）の判断でなく機械が整えて、汚れたままセッションを閉じられない状態にする" 内容="①『次の書き替えで消す』印の節を archive へ1文字も変えずに自動で移す ②(0-b-2) の印の値を json から機械で書く ③§0 の形（消す印 0件・0-1 の日付・印の一致・行数・★いまここ 1件）を検査する ④Stop hook が検査 ❌ ならターンを終われない" 方法="わざと壊して止まるか試すテスト8件＋本物の next_step.md で --verify ✅ を実測" -->

NEW_FILE: .claude/tools/tidy_next_step.py, .claude/hooks/enforce_next_step_tidy.sh
MODEL: .claude/tools/gen_audit_index.py, v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py, .claude/hooks/pdca_gate.sh
TARGET: .claude/settings.json
TARGET: .claude/rules/pdca_flow.md

BASEUP_EXEMPT（net 不変の道具の直し・売買のロジックに触らない・2026-06-22 まこさん承認の免除の型）

**出どころ**＝まこさん 2026-08-28（逐語）「毎回、next_stepが汚くなり、私が指示しないと整理されない状況なんだけど、改善できないのか？」→ CC の案（プログラム1本＋hook 1本）→ まこさん「やる」。

---

## §1 何を作るか（1文）

**`next_step.md` の §0（次にやること）を、機械が整えて検査し、検査が ❌ のままではセッションを閉じられないようにする。**

---

## §2 いまどうなっているか（実物・2026-08-28 に Read tool で開いた行）

| # | 何 | 実物 |
|---|---|---|
| 1 | セッションの末に CC が 0-1 を書き足すとき、前の 0-1 に「（◯回目の記録・次の書き替えで消す）」の印を付けて残す。**次のセッションの CC はその印を見ても消さない** | 69回目の末の実測＝68・67・66・65回目の4節（45行）が残っていた（`next_step.md` の旧 L32-109・worklog 20260827 §61 で archive へ移した） |
| 2 | (0-b-2)「印の状態」は、H2・G2 の印の値を CC が手で写す。印を取り直しても書き直し忘れる | 旧 (0-b-2) は「2026-08-25 時点」の値のまま。実物の印は 2026-08-27（`.claude/state/h2_pass.json` L2-3＝`when` 2026-08-27 22:00・`fingerprint` `567c333a…`／`g2_pass.json` L2-3＝23:56・`a500061c…`） |
| 3 | 68回目の記録（「束を1本も組めない」）が 0-1 の直下に残り、0-1（「20本 組める」）と食い違って読める | 69回目の末に archive へ移した（worklog 20260828 §1・353行 → 247行） |
| 4 | **汚れているかを判定する機械が無い**。判定しているのは まこさんの目だけ | Stop hook で next_step を見るのは `pdca_gate.sh`（L65）だけで、それは「ledger に実験を書いた後に4見出しが在るか」を見る＝形の古さは見ない |
| 5 | §0 のいまの大きさ | `# §0` 〜 `## §0-4` の前＝**69行**（2026-08-28・整理の後・機械で数えた） |

---

## §3 深掘り4点

### ① 真因（root cause）

**「消す」を CC の判断に任せていること。**「消さない」の決まり（🔴／★消さない）が在るので、CC は印が付いた節でも触らない側に倒れる。加えて、印の値を手で写す作りなので、取り直しのたびに写し忘れる。**どちらも機械が見ていないので、汚れたままセッションが閉じる。**

### ② 期待値分解（勝率 / 平均利益 / 敗率 / 平均損失 のどれを何 pt 動かすか）

**★売買の期待値には触りません。非該当です。**代わりに動かす数字＝

| 何 | 直す前 | 直した後（★機械が出す） |
|---|---|---|
| 「次の書き替えで消す」印の節が §0 に残る数 | 4節（69回目の末の実測） | **0**（`--write` が毎回 移す・`--verify` が0件でないと ❌） |
| (0-b-2) の印の値と json の食い違い | 有（08-25 の値・08-27 の印） | **0**（json から機械で書く） |
| 汚れたままセッションを閉じられるか | 閉じられる | **閉じられない**（Stop hook） |

### ③ root か symptom か

**root です。**「消すかどうか」を人の判断から外し（印の付いた節は機械が移す）、「写す」を人の手から外し（json から書く）、「汚れていないか」を人の目から外す（Stop hook）。symptom の直し方＝今回のように手で整理する＝次のセッションでまた溜まる（69回目の末に実証）。

### ④ ベースアップ（★Read tool で実際に開いた実物だけ）

| ファイル | どこを開いたか |
|---|---|
| `.claude/state/next_step.md` | 全文（整理の前 353行・後 247行） |
| `.claude/state/h2_pass.json`・`.claude/state/g2_pass.json` | 1-6行（`when`・`fingerprint`・`files`） |
| `.claude/tools/gen_audit_index.py` | 1-40行（目印とハッシュ値の型・`--write`／`--verify` の作り＝手本） |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/gen_audit_request.py` | 全文（節の切り出し・凍結ファイルのハッシュ・番人の型＝手本） |
| `.claude/hooks/pdca_gate.sh` | 全文（Stop hook の型・判定の本体を別ファイルへ出す決まり L13-19） |
| `.claude/settings.json` | 1-30行（登録の形）。Stop の一覧は L335-354（`pdca_gate.sh`・`enforce_worklog_on_experiment.sh`・`enforce_chat_writing.sh` の3本） |
| `.claude/rules/pdca_flow.md` | 1-12行（表の形） |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_archive/regime-build-callers-and-usable-groups-20260827.md` | 全文（承認済みの設計書の型＝手本） |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/cat_requirements.md` | 1-8行 |
| `v3-bitget-api-sdk/bitget-python-sdk-api/.claude/rules/exchange_spec.md` | 1-6行 |
| `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/eval_engine.py` | 1-6行 |

**WebSearch は使っていません。**このリポジトリの文書の形の話だけで決まるためです。

---

## §4 変更は 1レバーか（H16・1ターン1変更）

**1つです＝「next_step.md の §0 を機械が整えて検査する」。**プログラム1本と、それを呼ぶ hook 1本は、同じ1つの仕組みの2つの部品です（判定の本体を別ファイルに出す決まり＝`pdca_gate.sh` L13-19 と同じ型）。

**過去に破棄した失敗の再演か**＝「手書きの一覧は書き忘れると黙って腐る」（`gen_audit_index.py` L4-6・L-468）と同じ型を、(0-b-2) の印の値で作っていました。今回はそれを「json から機械で書く」で閉じます。

---

## §5 ★疑似シミュ由来の固定値ゼロ宣言

**probe を1回も走らせていません。probe から出た数字は1つもありません。**
この設計が持つ数字は **§0 の行数の上限だけ**です。**★この数字は CC が決めません＝まこさんが決めます**（案＝**100行**。出どころ＝いまの実測 69行 に、次の1セッション分の書き足し（0-1 の1節＝約15行）と余裕を足した数。★まこさんが別の数字を言われたら、それにします）。採否は、わざと壊して止まるか試すテストと、本物の `next_step.md` での `--verify` の実測で決めます。

---

## §6 ハード制約（H1〜H16）と審判整合

**H1〜H16 と 審判整合（D）は、まとめて非該当です。**売買のロジック・審判・戦略・実行器に1バイトも触りません。売買記録CSV を1本も作りません。**H16（1変更・過去の型の不再演）は §4 で書きました。**

---

## §7 やること（2件）

### 7.1 触るファイル（4本）

| # | ファイル | 何を |
|---|---|---|
| 1 | `.claude/tools/tidy_next_step.py`（**新設**・手本＝`gen_audit_index.py`・`gen_audit_request.py`） | 整える・検査する・番人 |
| 2 | `.claude/hooks/enforce_next_step_tidy.sh`（**新設**・手本＝`pdca_gate.sh`） | Stop で 1 の `--verify` を呼び、❌ なら exit 2 |
| 3 | `.claude/settings.json`（**TARGET**） | Stop の一覧に 2 を登録（`pdca_gate.sh` の隣・L335-354） |
| 4 | `.claude/rules/pdca_flow.md`（**TARGET**） | §1 の表に1行 足す（件数 63本 → 64本） |

### 7.2 やること1＝`tidy_next_step.py`（3つの口）

| # | 口 | 何をするか |
|---|---|---|
| 1-1 | `--write` | ①`next_step.md` の中で、見出しに「次の書き替えで消す」を含む節（その見出しから、同じ深さか浅い次の見出しの前まで）を全部、`next_step_archive_202608.md` の末尾へ **1文字も変えずに** 移す（先頭に「いつ・何を移したか」の見出しを1行 足す）。移す前と後で 🔴／★消さない／毎回消さない の数を数え、**移した分と足し合わせて合わなければ書かずに止まる**（fail-closed）②(0-b-2) の節を、`h2_pass.json`・`g2_pass.json` の `fingerprint`（先頭16桁）・`when`・`files` の数から書き直す（節の見出しと3行の型は固定・CC の自由記述は入れない）③書いた後に自分で `--verify` を走らせ、その結果を画面に出す |
| 1-2 | `--verify` | 次の5つを検査し、1つでも ❌ なら exit 2 と一覧を出す＝(a)「次の書き替えで消す」の節が **0件** (b) 0-1 の見出しの日付が、**いちばん新しい `session_worklog_YYYYMMDD.md` の日付と同じ**（★セッションの最初は前日の worklog が最新なので通る。今日の worklog を作った後は、0-1 を今日に書き替えるまで ❌＝セッションの末に必ず更新させる）(c) (0-b-2) に書いてある H2・G2 の印の値が、json の `fingerprint` と一致 (d) `# §0` から `## §0-4` の前までの行数が上限（§5）以下 (e) 0-2 の表の「★いまここ」が **ちょうど1件** |
| 1-3 | `--selftest` | §「自己検査」の8件。実物は触らず、一時の場所に写した見本で試す |

### 7.3 やること2＝`enforce_next_step_tidy.sh`（Stop hook・safety＝fast-mode でも動く）

| # | 何 | どう |
|---|---|---|
| 2-1 | Stop のたびに `tidy_next_step.py --verify` を呼ぶ | ❌ なら、その一覧を画面に出して exit 2（ターンを終われない）。`pdca_gate.sh` と同じ型・判定の本体は .py（L13-19 の決まり） |
| 2-2 | ★fast-mode の時も止める | (0-b-2) の腐りと「消す」印の溜まりは fast-mode の間にも起きる（69回目は fast-mode）。だから `pdca_fast_mode` の判定を入れない（`enforce_todo_declaration.sh` と同じ safety の型） |
| 2-3 | 止める回数に上限を付けない | ToDo ゲートと違い、直し方が1つ（`--write` を走らせて 0-1 を書く）で、機械で直せるため |

### 7.4 変えないもの

| # | 何 | なぜ |
|---|---|---|
| 1 | 🔴／★消さない／毎回消さない の行 | 1行も消さない。移すときも1文字も変えない（数を前後で照らす） |
| 2 | 0-1 の文章の中身 | 機械は書かない（CC が書く）。機械が見るのは日付だけ |
| 3 | §5・§6・§7（判断待ち・あとで直すこと・過去の節） | この設計の外。§6 の「直したら移す」の決まりは、いまのまま人が行う |
| 4 | `pdca_gate.sh` | 触らない（別の旗を見ている） |

---

## §8 完成の条件（★全部 満たすまで終わりません・数字は機械が出す）

| # | 何 | どう確かめるか |
|---|---|---|
| 1 | 番人8件 全部 pass | `python3 .claude/tools/tidy_next_step.py --selftest` |
| 2 | **本物の `next_step.md` で `--verify` が ✅** | `python3 .claude/tools/tidy_next_step.py --verify`（いまの実物＝消す印 0件・0-1 は 2026-08-28・印は 08-27 の値・69行・★いまここ 1件） |
| 3 | 本物で `--write` を走らせても、🔴／★消さない／毎回消さない の数が1つも減らない | `--write` の画面の出力（前・後・移した分） |
| 4 | Stop hook が ❌ で止まる・✅ で通る | 一時の見本で `enforce_next_step_tidy.sh` を直に呼び、exit 2／0 を実測 |
| 5 | `settings.json` が json として読め、`hook_health_check.sh` が ✅ | `python3 -c "import json;json.load(open('.claude/settings.json'))"`／SessionStart の表示 |
| 6 | `pdca_flow.md` の表に行が在り、件数が 64本 | 目視＋`grep -c` |

---

## 自己検査（番人・★わざと壊して落ちるかをメタ確認する）

| # | 見本 | 期待 |
|---|---|---|
| T1 | 「次の書き替えで消す」の節が2つ在る見本で `--write` | 2節が archive へ移り、本文から消える。🔴 の数＝前 − 移した分 ＝ 後 |
| T2 | 移す途中で数が合わない見本（🔴 を含む行を移す先で1行 落とすよう わざと壊す） | **止まる**（書かない） |
| T3 | 0-1 の日付が最新の worklog の日付より古い見本で `--verify` | **❌ (b)** |
| T4 | (0-b-2) の印の値が json と違う見本 | **❌ (c)** |
| T5 | §0 が上限＋1行の見本 | **❌ (d)** |
| T6 | ★いまここ が 0件・2件の見本 | **❌ (e)**（2通り） |
| T7 | きれいな見本 | **✅ 0件** |
| T8 | hook を見本で直に呼ぶ | ❌ の見本＝exit 2／✅ の見本＝exit 0 |

---

## 走らせるもの・時間の見込み（恒久の決まり60番・61番・62番）

| # | 何 | 見込み | 過去の実測（記録の逐語） |
|---|---|---|---|
| 1 | `tidy_next_step.py --selftest` | **15分未満**（数秒＝文書の読み書きだけ） | なし（新設。同じ型の `gen_audit_request.py --selftest` は `session_worklog_20260827.md`「番人 11/11」＝数秒で終わっている） |
| 2 | `--verify`・`--write`（本物） | **15分未満**（1秒未満） | なし（新設） |

**途中経過**＝番人は1件ずつ画面に出る。**裏では走らせない。**

---

## ★入っていないもの（都合の悪い事実も書きます）

1. **0-1 の文章の中身が「いまの状態」として正しいかは、機械には分かりません。**見るのは日付だけです。中身の正しさは まこさんの目です。
2. **§6（あとで直すこと）の「直した行を移す」は自動にしません。**どの行が直ったかは機械には分からないためです。
3. **「次の書き替えで消す」の印を CC が付け忘れた節は、機械には見えません。**印の付け方（見出しにその文字を入れる）は 0-1 を書くときの決まりとして `next_step.md` の §0 の冒頭に1行 書きます（★これは文章の決まりで、機械の強制ではありません）。
4. **Stop hook は、この hook 自身を書き換えれば無効にできます**（ほかの safety hook と同じ）。
5. **行数の上限（§5）を超えたとき、何を移すかは機械が決めません。**❌ を出して止めるだけです（移す相手は CC が「消す」印を付けて `--write` に渡す）。

---

## DESIGN_CONTRACT

```json
{
  "impl_file": ".claude/tools/tidy_next_step.py",
  "self_check_calls": [
    "find_disposable_sections",
    "move_to_archive",
    "refresh_marks",
    "verify",
    "selftest"
  ]
}
```

---

## 「作ってはいけないもの」2件との照合（着手前・必須）

| # | 作ってはいけないもの | 当たるか | なぜ |
|---|---|---|---|
| 1 | ランダムに条件をつなぐだけのもの | **当たりません** | 売買の条件に1バイトも触りません。文書の整理の道具です |
| 2 | 探す値を、CC が先に「点の一覧」で限定するもの | **当たりません** | 探索に関わりません |

---

## この設計で net は動くか

**動きません。**実験ゼロ・売買記録0本・審判と戦略と実行器に1バイトも触りません。

---

## SPEC

**新設のファイルなので、いまは書き出せません。**実装の後に `python3 scripts/priority_rebuild/verify_design_contract.py --write .claude/state/acceptance.md` で実物から書き出して、ここに写します（手書きしない）。
