# セッション詳細ログ 2026-06-12 — E19閉じ→E0.4計器修正→E20破棄→E21 GO（⚠️ 強制終了により翌セッションが事後再構成）

> 注記: 当日セッションは固定値調整へのドリフト（トークン浪費）でまこさんが強制終了したため、本ログは未作成だった。翌セッション（2026-06-12 再開）が ledger（E19/E0.4/E20）・スクリプト実体・git status から再構成した。チャットの細かい経緯は残っていない。

## 0. 1段落サマリ
P21 をやり切る方針（まこさん）の下、E19（Exit 値の場面別学習・CPO 型）を実装→OOF で ML 寄与なしと確定し採点せず閉じた（V9 現行 Exit 値が12組中最良・遅咲き玉3.3%は entry 時点で予測不能）。途中、まこさん指摘（「手数料高すぎ」「V9 は Entry/Exit とも maker のはず」）から審判の trail=taker 仮定が live 原本（run_once_v9=placePosTpsl 指値）と不一致と発覚し E0.4 計器修正（trail=maker・既知答え15/15・P21 地面 $1,021.01→$2,697.32）。旧計器の仮説のまま設計した E20（ATR 床 veto・手置き候補 {0.15,0.20,0.25}）は採点 −$628 で破棄＝計器修正後は仮説の測り直しが必要と実証。次に E21（P21 Entry 判定の ML 置き換え・型=MACD デッドクロスのみ残し閾値は木へ）がまこさん GO となり Phase 1（教師生成＋実測サマリ）を実装したが、未実行のまま強制終了。固定値調整は hook（forbid_fixed_value_tuning.sh・まこさん命令）で物理禁止になった。

## 1. 確定事項（ledger が正・ここは要約）
- **E19 閉じる**: Exit 候補12組メニューで V9 現行値が固定値最良（12組中全勝）。oracle 天井 +20.9% は3.3%の遅咲き玉に集中し entry 時点の場面情報に痕跡なし（OOF cutoff 全て切替0玉・prob 上位 precision 0%）。採点1回温存。
- **E0.4 採用（まこさん決定）**: score.py MAKER_EXIT_REASONS に TRAIL_EXIT 追加。根拠=run_once_v9.py L320-348（TP/SL とも placePosTpsl 指値）/L130-131（損益 CSV も maker×2）・trail は run_once 未実装（taker は未決のままの仮定だった）。**P21 地面 $1,021.01→$2,697.32（月$299.70・+164%）**・学習期間 $9,676.61。「手数料 71%」の正体の大半は trail=taker の執行仮定。**旧計器の数字で立てたレバー仮説は全部測り直し**。本番宿題=trail の placePosTpsl 毎バー更新（Phase 7 必須）。
- **E20 破棄**: ATR 床の価格非依存化（USD150→ATR% 床・候補手置き {0.15,0.20,0.25}）。学習期間 +$40（2024 のみ・83玉）→採点 floor0.20 が −$628。①P21 でも「削る」方向は負ける（maker 化後は低 ATR% 玉も正味プラス）②計器修正後の仮説測り直しを実証 ③逆方向（床の下側=件数増）が開いた可能性。
- **E21 GO（まこさん 2026-06-12・script 冒頭に記録）**: P21 Entry 判定を ML に置き換え。型（MACD デッドクロス・原本 cat_v9_decider L556-569）だけ残し、固い閾値（ATR 床ほか）は木に渡す。入る条件=較正済み prob>0.5（手置き値でない）。Exit/サイズ 0.06/add なし=V9 のまま（H16 1変更）。Phase 1=候補生成＋教師 sim（E19 の simulate_exit 流用・judge 式が score.py と $1 以内一致を assert）＋V9 通過/見送り集団の実測サマリ（学習期間のみ・採点なし）。**実装済み・未実行**。
- **固定値調整の物理禁止**: `.claude/hooks/forbid_fixed_value_tuning.sh`（まこさん命令）。scripts/priority_rebuild/*.py への Write/Edit で「大文字定数=数値2個以上のタプル/リスト」を含み lightgbm を使わないものを block。レバーは ML 場面別学習で実装。例外はまこさん明示 GO+マーカーのみ。

## 2. 強制終了の経緯（翌セッションへの引き継ぎ）
- 複数セッションにわたり CC が固定値調整（手置き候補値スイープ・E20 型）にトークンを使い続け、まこさんが強制終了（L-261 の再演 → L-267）。
- 未了だったセッション終了処理（本ログ・lessons L-266/L-267・WORKFLOW 改訂74・commit）は翌セッションが修復。

## 3. 次セッション着手（再開セッションで goal_block 提出済み・まこさん GO・★都度確認条件付き）
1. E21 Phase 1 実行（--smoke → 本番）→ 見送り集団の取り分（件数・net・年別）を実測報告 → まこさん確認。
2. 取り分あり → Phase 2（学習・purged k-fold 玉単位・較正チェック）の設計報告 → GO 後実装。なし → E21 閉じて並立配分制御（E18 知見）へ。
3. 採点前ゲート: ①連続モード wrapper（E20 で地面完全一致 検証済）×年別で 2024 劣化なしを確認 ②OOF 較正が壊れていたら採点せず停止（E15 前例）③正の結果は対照実験/玉分解（analysis_playbook §2.8）。
4. ⚠️ P21 の数字は trail=maker 前提（本番未実装・Phase 7 宿題）の注記を毎回付ける。

## 4. 生成物（実在・git status で確認）
- scripts: train_p21_exit_E19.py / measure_p21_atrfloor_E20.py / train_p21_entry_E21.py（いずれも V9/審判 不変・import のみ）
- results: p21_exit_menu_E19_teacher.csv / p21_exit_E19_oof.json / p21_exit_E19_oof_pairs.csv / trades_p21_E20_floor{015,02,025}.csv / report_trades_p21_E20_floor02.txt
- 審判: score.py（E0.4・MAKER_EXIT_REASONS に TRAIL_EXIT・既知答え15/15）
- hook: .claude/hooks/forbid_fixed_value_tuning.sh
