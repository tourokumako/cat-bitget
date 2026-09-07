# 監査依頼 CP25（再監査）— M2-C＝cp24 の指摘9件を直せているか

## ⚠️ auditor 宣言ブロック

**あなたは auditor session の CC です。**メインの CC ではありません。auto-load される文書（CLAUDE.md・cc_role.md ほか）は参考であり、**着手前の必読は この依頼書に書いた7件だけ**です。確認質問をせず、すぐ Plan agent を起動してください。

## 0. この監査で答えてほしいこと（★2段で答えてください）

**1段目｜cp24 の指摘9件（Critical 4・Major 4・Minor 1）を、CC が直せているか。**

**2段目｜その9件を直したことによって、M2-C の要件が達成されているか。**

> **M2-C｜指標のオン・オフを一律で切り替えられるようにする ＋ 相場の法則が要る部品を足す**

**★2段目が、この監査の結論です。**1段目（9件）は手段です。**9件が全部 直っていても、2段目が達成されていなければ NO-GO にしてください。**

**2段目の判定の中身（この2つを、実物と実測で見てください）**

| # | 要件 | 何が言えたら「達成」か |
|---|---|---|
| **①** | 指標のオン・オフを一律で切り替えられる | **まこさんが「使わない」と決めた材料が、案に1件も出ない。**指標だけでなく、**別枠3種（レンジ幾何・需給・時間帯）にも同じように効く。**印を戻せば また出る |
| **②** | 相場の法則が要る部品を足す | **足した部品（需給3件・MMI 4件）が、engine_tuner の案に実際に出てくる。**部品の表に載っているだけ・列が作れるだけでは達成ではない |

**★前回（cp24）が NO-GO だった理由も、この2つでした。**①はオン・オフが効くのが指標だけ（別枠3種は効かない）、②は「engine_tuner が使えるようになった部品は 0件」。

## 1. 着手前に読むもの（7件）

| # | ファイル | どこを |
|---|---|---|
| 1 | `.claude/audits/2026-09-06_m2c4_cp24_reaudit_report.md` | 全文（前回の指摘9件＝§6） |
| 2 | `.claude/state/session_worklog_20260904.md` | **§47**（47-1 から 47-3f まで）＝CC が出した実測 |
| 3 | `.claude/state/acceptance.md` | 全文（今回の設計書・まこさん承認済み） |
| 4 | `scripts/priority_rebuild/engine_tuner_gen.py` | `_lineage_candidates`・`_pick_material`・`_lineage_of`・`_kubun_of`・`_attach_demand`・`assert_provenance`・`structure_breakdown`・`selftest` の T33-e |
| 5 | `scripts/priority_rebuild/engine_tuner_exec.py` | `load_indicator_switch`・`time_enabled`・`_material_family` |
| 6 | `scripts/priority_rebuild/gen_indicator_switch.py` | `source_time`・`source_identity`・`build`・`cmd_selftest` の T10・T11 |
| 7 | `.claude/breaks/` | `b33_extra_switch_off.sh`・`b34_identity_name_missing.sh` |

## 2. CC の自己申告（打ったコマンドと出力をそのまま）

| # | 監査の項目 | 打ったコマンド | 出力（そのまま） |
|---|---|---|---|
| 1 | §6-1 別枠にオン・オフ | `python3 scripts/priority_rebuild/engine_tuner_gen.py --count-extra-candidates` | `6`（直す前は 0。レンジ幾何2・需給3・時刻1） |
| 2 | §6-2 需給の引き口 | `python3 scripts/priority_rebuild/engine_tuner_gen.py --dry-run 20` | `[生成拒否] {}`（直す前は `{"[レシピ拒否 G3] 系統マップに無い fami": 5}`） |
| 3 | §6-4 足した部品が案に出る | `python3 scripts/priority_rebuild/engine_tuner_gen.py --dry-run 50` の「使った材料と回数」 | `"時刻": 19` ／ `"L-S比": 5` ／ `"CVD": 4` ／ `"taker_ls": 2` ／ `"MMI478__10m": 1` |
| 4 | §6-3 成績表の作り直し | `python3 scripts/priority_rebuild/observe_diag.py --rank-regime data/BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv` | MMI を含む行 **528**（直す前 0）／測れた列 6,057 → **6,101**（＋44＝MMI 4種×時間足11本）／窓・行数は同じ |
| 5 | §6-5・§6-6 印の道具 | `python3 scripts/priority_rebuild/gen_indicator_switch.py --selftest` | `✅ selftest 11/11 pass`（T10・T11 を新設） |
| 6 | §6-6 源3 の数 | `python3 scripts/priority_rebuild/gen_indicator_switch.py --write` | `使う 141 種／使わない 116 種`。`counts.源3_恒等レシピ` が **8 → 2** |
| 7 | §6-1 時間帯の欄 | `grep -n "time_on" -A 4 .claude/ratchet/indicator_switch.json` | `"time_on": [ "時刻", "曜日" ]`（直す前は欄そのものが無い） |
| 8 | §6-7 S1・L1 の走行 | `python3 scripts/priority_rebuild/engine_tuner_exec.py --identity-l1` ／ `--identity-s1` ／ `--identity` | 3本とも `✅ 完全一致`。L1 `96a9102ec8a34f94cf01e9e463f6aade`／S1 `18b3d31a5fe71c4a4b5f83cf1771a46c`／S2 `7b01f51b5a9b29b3c05a7b340c203ba1` |
| 9 | §6-8・全体 | `python3 scripts/priority_rebuild/engine_tuner_gen.py --selftest` | ❌ **3件**（T24②・T26・T30）＝前からの M2-E の工事。**T1・T19 は CC が壊して直した**（6分24秒） |
| 10 | §6-10 材料の一覧 | `python3 scripts/priority_rebuild/gen_materials.py --write` | `materials.md` の ★1 の C が **3件 → 0件**（`- **C（0 件）** … （無し＝3件とも型の表の別枠に在る）`） |
| 11 | 壊すプログラム | 承認の機械が走らせた | **10/10**（`b33` rc=1 が6回・`b34` rc=1 が4回） |
| 12 | 印 | `python3 scripts/priority_rebuild/gen_signal_families.py --verify` ／ `python3 scripts/priority_rebuild/leak_causality_diag.py` | G2 `78d0ebec0fe8bce4…`（対象38・11件の見本とも期待どおり）／H2 `1c9b62a16e19377f…`（注記なし未来参照 0件・打ち切り再現の食い違い 0件・4分55秒） |

**★この表の数字は、全部 `session_worklog_20260904.md` の §47 に出力を貼ってあります。**

## 3. ★CC が監査の案と違う道を取ったところ（1件・正直に）

**監査 §6-2 の3 は「需給を成績表に載せて、指標と同じ順位の道で引く」と書いていました。CC はその道を取っていません。**

| | 監査の案 | CC が取った道 |
|---|---|---|
| 需給をどこから引くか | 成績表に載せて、指標と同じ順位の道で引く | **別枠の道**（レンジ幾何・時間帯と同じ） |

**理由（実物で確かめたもの3つ）**

1. **成績表を作る本体が需給を測らない**＝`rank_materials_for_regime`（`observe_diag.py`:5705）が測るのは `build_catalog(cfg)` の列だけで、`load_demand` の呼び出しが 0件。
2. **承認済みの型の表が、需給を別枠に置いている**＝`signal_families.json` の `extra_parts.demand` の rule＝「需給の列（taker_ls・L-S比・CVD）は入口の条件の材料に使える。★時間足には展開しない（元データが5分足の1本だけ）」。役割は `sufficiency`。
3. **需給は指標ではない**＝8つの系統の1つ（`indicator_reference_diag.py`:4478 の `LINEAGE_KINDS`）。元データも別ファイル（`../../data/oi_BTCUSDT_5y.csv` ほか）。

**★この判断の是非を、監査に見てほしい。**

## 4. ★CC が塞げていないこと（正直に・5件）

| # | 中身 |
|---|---|
| 1 | **入口・出口の条件の束を法則で組む工事（D14・違反の記録 #14／#24）は、この直しでは直っていません。**直ったのは「どの材料を候補にするか」までです |
| 2 | **需給が本当に効くかは測っていません。**知識の正本 `range_scalping_kb.md` §6.7 の逐語＝「同じ需給フィルタが SHORT 側でも対称に効くかは未検証」 |
| 3 | **系統を選んでから部品を選ぶ、という構造は CC が決めました。**型の表は「どの系統を使えるか」を宣言していますが、選ぶ重みは宣言していません。別の形（部品を全部 並べて一様に選ぶ）にすると、需給は3件しかないので ほとんど選ばれません |
| 4 | **曜日は印ではオンですが、案には出ません。**閾値の格子（`hour_range` に当たるもの）が無いためです（まこさん §11-10 の判断待ち）。CC は `_TIME_GRID` に格子の在るものだけを候補にしました |
| 5 | **印の偽造はプログラムでは見抜けません**（H2・G2 と同じ限界） |

## 5. 監査への問い（2段・4つ）

**【1段目＝9件が直ったか】**

1. **cp24 の9件それぞれについて、直っているか。**実物のコードと出力で確かめてください。

**【2段目＝その結果、M2-C の要件が達成されたか】★これが結論です**

2. **①「指標のオン・オフを一律で切り替えられる」は達成されたか。**印から材料を外したとき、案に1件も出ないことを **自分で測って** ください。**指標だけでなく、別枠3種（レンジ幾何・需給・時間帯）でも同じか。**
3. **②「相場の法則が要る部品を足す」は達成されたか。**足した部品（需給3件・MMI 4件）が **案に実際に出てくる回数を、自分で測って** ください（CC の数字＝需給3件が 2〜5回・MMI が1回・時刻が19回／案50本）。**表に載っているだけ・列が作れるだけは達成ではありません。**

**【あわせて見てほしいこと】**

4. **§3 の「CC が監査の案と違う道を取ったところ」は、妥当か。**妥当でなければ、どう直すべきかを書いてください。
