#!/bin/bash
# PostToolUse: PDCA マーカー管理（analysis_playbook §4 物理強制・2026-06-05 まこさん矯正指示）
# score.py 採点 → 「report未済」「ledger未済」の旗を立てる。
# report.py 実行で report 旗 / ledger.md 編集で ledger 旗 を下ろす。
# 2026-06-12 拡張（まこさん合意）:
#  - precheck（審判の門）通過/FAIL でも report/analyze/ledger/5q を必須化（FAIL=閉じる時も分析を飛ばせない）
#  - report.py は --vs（前回ベースライン比較・KB §0）必須。無しで実行すると need_vs 旗。
#    真の初回のみ、まこさん GO を得て state/no_baseline_approved を作成（1回で消費）。
#  - ledger 記録は「5つの問い」(【問1 レバー】【問2 不足量】【問3 負け集中】【問4 過去接続】【問5 次仮説】)
#    が全部含まれる編集があるまで need_5q 旗が残る（最低ライン分析≠ゴールの物理化）。
# Stop hook(pdca_gate.sh) が旗の残存でターン終了をブロックする。
export PDCA_STATE="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
mkdir -p "$PDCA_STATE"
cat | python3 -c '
import sys, json, os, re, glob
state = os.environ["PDCA_STATE"]
need_report = os.path.join(state, "pdca_need_report")
need_ledger = os.path.join(state, "pdca_need_ledger")
need_analyze = os.path.join(state, "pdca_need_analyze")
need_score = os.path.join(state, "pdca_need_score")
need_vs = os.path.join(state, "pdca_need_vs")
need_5q = os.path.join(state, "pdca_need_5q")
need_claim = os.path.join(state, "pdca_need_claim")   # 多角チェックの結論=主張1行（件数妥当性込み・2026-06-14 まこさん B）
need_next_step = os.path.join(state, "pdca_need_next_step")
need_analyze_report = os.path.join(state, "pdca_need_analyze_report")  # 分析レポートを出して読む強制（別途・省略・読み飛ばし禁止・2026-06-15）
need_viz = os.path.join(state, "pdca_need_viz")   # 週次チャートPNG（report と同時に4週分 自動出力）強制（2026-06-21 まこさん「強制化」）
viz_dir = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/viz"
no_baseline = os.path.join(state, "no_baseline_approved")
diagnostic_active = os.path.join(state, "pdca_diagnostic_active")   # 診断ラウンド（採点しない・2026-06-13）
score_bg_pending = os.path.join(state, "pdca_score_bg_pending")     # バックグラウンド実験 実行中（2026-06-13）
def touch(p): open(p, "w").close()
def rm(p):
    try: os.remove(p)
    except FileNotFoundError: pass
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tn = d.get("tool_name", "")
ti = d.get("tool_input", {}) or {}
if tn == "Bash":
    cmd = ti.get("command", "") or ""
    # 実験スクリプト実行 → 審判(score.py/precheck.py)を通すまでターン終了不可（2026-06-12 E24 素通り事案）
    # ただし以下は need_score を立てない:
    #  - --smoke: 採点しない検証ステップ（自己検査・規模確認）（2026-06-12 まこさん・smoke で永久未閉じ事案）
    #  - --no-score: 設計上採点なしの工程（メタラベリング Phase1=OOF 診断のみ・採点は別工程 Phase2 の score.py）。
    #    （2026-06-12 まこさん承認・E28 Phase1 OOF で永久未閉じ事案＝Phase1 は連続モード変換前で score.py 適用外）
    #  - py_compile: コンパイル確認のみ＝戦略を回さない・売買記録を生成しない（2026-06-18 まこさん承認・false trigger 防止）
    # 実験＝戦略本体(strat_/train_/measure_/e3N_連番名)を採点ありで実行。probe/deep_analysis は分析＝除外(2026-06-16 命名非依存化)
    _is_exp = bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*(strat_|train_|measure_|e3[0-9]_)[A-Za-z0-9_]*\.py", cmd)) \
        and not bool(re.search(r"(_probe|_deep_analysis)\.py|score[A-Za-z0-9_]*\.py", cmd)) \
        and "py_compile" not in cmd   # 採点ラッパー score_*(名に e35_ を含む)・probe・分析・py_compile(コンパイル確認) は実験から除外
    if _is_exp:
        if "--diagnostic" in cmd:
            # 診断（採点しない・cap実態/規模確認等）→ PDCA 連鎖を一切要求しない（2026-06-13・診断CSVは
            # cap で report/score が STOP＝不能ループに陥る事案の防止）。次の通常実験で解除。
            touch(diagnostic_active)
        elif "--smoke" in cmd or "--no-score" in cmd:
            pass   # 既存: 採点しない検証ステップ（自己検査・規模確認・Phase1 OOF 等）
        else:
            rm(diagnostic_active)        # 通常実験＝診断状態を解除（採点を要求するラウンド）
            touch(need_score)
            if ti.get("run_in_background"):
                touch(score_bg_pending)  # バックグラウンド実行中は審判催促を抑制（2026-06-13・長時間 replay 待ち）
    # python(3) で実際に score.py/precheck.py を実行する形のみ検知（grep/echo/別行言及では誤爆しない）
    # 審判＝score.py CLI ＋ 採点ラッパー score_*.py（gate外 score.score を呼ぶ＝命名規約 scripts/priority_rebuild/score_*.py・2026-06-16）
    _is_judge = (bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*score[A-Za-z0-9_]*\.py", cmd)) or
                 bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*precheck\.py", cmd))) \
                and "--selftest" not in cmd   # --selftest* は自己テスト＝採点でない（--smoke と同扱い・2026-06-18・誤点火防止）
    if _is_judge:
        # score.py / precheck.py（審判の門）。FAIL=閉じる場合も 分析・記録・5つの問い を飛ばせない（2026-06-12）
        rm(need_score); rm(score_bg_pending)
        if os.path.exists(diagnostic_active):
            pass   # 診断ラウンド中の採点＝PDCA 連鎖を立てない（不能ループ防止・2026-06-13）
        else:
            touch(need_report); touch(need_ledger); touch(need_analyze); touch(need_5q); touch(need_claim)
            touch(need_next_step)   # 審判を通したセッションは next_step を1回上書きするまで終了不可（ledger 編集回数に依存させない・2026-06-14 まこさん GO）
            touch(need_analyze_report)  # 分析レポートを生成→Read tool で読む まで終了不可（「別途」で逃げる・省略・読み飛ばし を物理禁止・2026-06-15 まこさん命令）
            touch(need_viz)  # 審判後 report.py が 週次チャートPNG（トレード最多/最少・NET最大/最小 の4週）を出すまで終了不可（2026-06-21 まこさん強制化）
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*report\.py", cmd):
        rm(need_report)
        # 週次チャートPNG（report.py M節が 最多/最少・NET最大/最小 の4週を自動出力）が 採点CSV分 実在すれば need_viz を下ろす。
        # M節がスキップ（matplotlib/plot_trades 故障）で PNG が無ければ旗が残る＝gate がブロック（2026-06-21 強制化・番人）。
        _mc = re.search(r"report\.py[ \t]+\"?([^\"\s]+\.csv)", cmd)
        if _mc and glob.glob(os.path.join(viz_dir, os.path.basename(_mc.group(1))[:-4] + "_*.png")):
            rm(need_viz)
        # --vs（前回比較・KB §0）必須。無しは need_vs 旗（初回のみ no_baseline_approved で免除・1回で消費）
        if "--vs" in cmd:
            rm(need_vs)
        elif os.path.exists(no_baseline):
            rm(no_baseline); rm(need_vs)
        else:
            touch(need_vs)
    # 分析＝analyze.py（汎用 N0-N12）＋ 戦略固有 *_deep_analysis/*_probe（命名規約・2026-06-16）
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*(analyze|[A-Za-z0-9_]+_deep_analysis|[A-Za-z0-9_]+_probe)\.py", cmd):
        rm(need_analyze)  # 深掘りバッテリー実行で旗が下りる
elif tn in ("Edit", "Write", "MultiEdit"):
    fp = ti.get("file_path", "") or ""
    if fp.endswith("ledger.md"):
        rm(need_ledger)
        # ★2026-06-14 まこさん GO: ledger は「ログ」＝都度何度でも追記してよい。ledger 編集ごとに next_step を
        #   強制すると同一セッションで何度も付箋の上書きが走る（friction）。→ need_next_step は審判実行時に
        #   1回だけ立て（上の _is_judge ブロック）、ledger 編集では立てない。next_step はセッション末に1回。
        #   経緯を忘れない本体は ledger（追記・恒久・開始時 Read 強制）＝こちらは触らない。
        # 5つの問いが全部含まれる編集なら need_5q を下ろす（形だけ防止は まこさん30秒チェックが担保）
        payload = (ti.get("new_string", "") or "") + (ti.get("content", "") or "")
        for e in (ti.get("edits", []) or []):
            payload += e.get("new_string", "") or ""
        tokens = ["【問0 前後比較】", "【問1 レバー】", "【問2 不足量】", "【問3 負け集中】", "【問4 過去接続】", "【問5 次仮説】"]
        if all(t in payload for t in tokens):
            rm(need_5q)
        if "【主張】" in payload:        # 多角チェックの結論=主張1行（件数/日+net 込み・#19・2026-06-14）
            rm(need_claim)
    if fp.endswith("next_step.md"):
        # 次セッションの起点を上書き更新 → 旗を下ろす。ただし記載必須項目（本筋/やってはいけない/出典）を
        # 含む編集の時だけ（薄い1文字編集で旗を消す＝引き継ぎ空洞化を防ぐ・中身の質はまこさん30秒チェック）。
        ns = (ti.get("new_string", "") or "") + (ti.get("content", "") or "")
        for e in (ti.get("edits", []) or []):
            ns += e.get("new_string", "") or ""
        if all(t in ns for t in ("本筋", "やってはいけない", "出典")):
            rm(need_next_step); rm(score_bg_pending); rm(diagnostic_active)   # セッション境界の安全側クリア
'
exit 0
