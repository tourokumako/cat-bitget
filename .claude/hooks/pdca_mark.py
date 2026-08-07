#!/usr/bin/env python3
# pdca_mark.py — pdca_mark.sh の本体（PostToolUse・旗管理）。
# 2026-07-03 まこさん指示: 旧 pdca_mark.sh は python コードを bash の python3 -c '...'（シングルクォート）に
# 埋め込んでおり、2026-06-29 改善で足した行（引用符除去の正規表現）自身のシングルクォートが シェルの引用を壊し、
# python が毎回 SyntaxError → 末尾 exit 0 が握りつぶし＝旗管理が全停止していた（無言死）。
# 対策: python を本ファイルに分離（クォート問題の構造的根絶）＋ .sh 側で stderr をエラーログへ（無言死の可視化）。
# ロジックは旧ヒアドキュメントと同一（変更なし）。
import sys, json, os, re, glob

state = os.environ.get("PDCA_STATE", "/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state")
need_report = os.path.join(state, "pdca_need_report")
need_ledger = os.path.join(state, "pdca_need_ledger")
need_analyze = os.path.join(state, "pdca_need_analyze")
need_score = os.path.join(state, "pdca_need_score")
need_vs = os.path.join(state, "pdca_need_vs")
need_5q = os.path.join(state, "pdca_need_5q")
need_claim = os.path.join(state, "pdca_need_claim")   # 多角チェックの結論=主張1行（件数妥当性込み・2026-06-14 まこさん B）
need_next_step = os.path.join(state, "pdca_need_next_step")
need_analyze_report = os.path.join(state, "pdca_need_analyze_report")  # 分析レポートを出して読む強制（省略・読み飛ばし禁止・2026-06-15）
need_viz = os.path.join(state, "pdca_need_viz")   # 週次チャートPNG（report と同時に4週分 自動出力）強制（2026-06-21 まこさん「強制化」）
need_forward = os.path.join(state, "pdca_need_forward")   # probe(当たり付け)後に「できない証明で止まる」のを禁止（まこさん 2026-06-27）
viz_dir = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/viz"
no_baseline = os.path.join(state, "no_baseline_approved")
diagnostic_active = os.path.join(state, "pdca_diagnostic_active")   # 診断ラウンド（採点しない・2026-06-13）
score_bg_pending = os.path.join(state, "pdca_score_bg_pending")     # バックグラウンド実験 実行中（2026-06-13）


def touch(p):
    open(p, "w").close()


def rm(p):
    try:
        os.remove(p)
    except FileNotFoundError:
        pass


try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
tn = d.get("tool_name", "")
ti = d.get("tool_input", {}) or {}
if tn == "Bash":
    cmd = ti.get("command", "") or ""
    # ★引用符内（文字列リテラル）を除去した版で実行検知する＝git commit メッセージ・echo・printf テスト等で
    #   スクリプト名が「言及」されただけ（実行でない）の誤検知で審判/実験/probe 旗を立てる事案を防ぐ
    #   （2026-06-29 まこさん「毎回フラグ解除で時間がかかる・誤発火を直して」）。CSV 抽出は元 cmd を使う。
    # ★2026-08-07（まこさん指示「21は今やれば？」・next_step §6.5 の21番）＝下ごしらえを共通の1本にまとめた。
    #   引用符の中身に加えて、ヒアドキュメント（<<EOF … EOF）の中身も空白にする。
    #   実装＝.claude/hooks/hook_cmd.py（番人＝既知答え7件・--selftest）。読み込めなければ従来どおり引用符だけ消す。
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from hook_cmd import normalize_cmd
        cmd_x = normalize_cmd(cmd)
    except Exception:                                   # noqa: BLE001（fail-open＝旗管理を止めない）
        cmd_x = re.sub(r'"[^"]*"', " ", re.sub(r"'[^']*'", " ", cmd))
    # 実験スクリプト実行 → 審判(score.py/precheck.py)を通すまでターン終了不可（2026-06-12 E24 素通り事案）
    # ただし以下は need_score を立てない:
    #  - --smoke: 採点しない検証ステップ（自己検査・規模確認）（2026-06-12 まこさん・smoke で永久未閉じ事案）
    #  - --no-score: 設計上採点なしの工程（2026-06-12 まこさん承認）
    #  - py_compile: コンパイル確認のみ（2026-06-18 まこさん承認・false trigger 防止）
    # 実験＝戦略本体(strat_/train_/measure_/eNN_連番名)を採点ありで実行。probe/deep_analysis は分析＝除外(2026-06-16 命名非依存化)
    #   2026-07-04 まこさん承認: e3[0-9]_ → e[0-9][0-9]_ に一般化（E40 番台以降の新戦略が検知から素通りする穴＝pdca_flow §4 の登録忘れ構造を縮小）
    _is_exp = bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*(strat_|train_|measure_|e[0-9][0-9]_)[A-Za-z0-9_]*\.py", cmd_x)) \
        and not bool(re.search(r"(_probe|_deep_analysis)\.py|score[A-Za-z0-9_]*\.py", cmd_x)) \
        and "py_compile" not in cmd_x   # 採点ラッパー score_*・probe・分析・py_compile は実験から除外
    if _is_exp:
        if "--diagnostic" in cmd:
            # 診断（採点しない）→ PDCA 連鎖を一切要求しない（2026-06-13）。次の通常実験で解除。
            touch(diagnostic_active)
        elif "--smoke" in cmd or "--no-score" in cmd or "selftest" in cmd:
            pass   # 採点しない検証ステップ（--smoke/--no-score／self-test 系＝コマンドに "selftest" を含む: --param-schema-selftest・--v11-selftest-zones 等・2026-07-12 まこさん承認。self-test は売買記録を出さないので実験でない＝誤検知で need_score/exp_started が立つ穴を塞ぐ）
        else:
            rm(diagnostic_active)        # 通常実験＝診断状態を解除（採点を要求するラウンド）
            touch(need_score)
            touch(os.path.join(state, "pdca_exp_started"))   # ★データ捨て禁止（まこさん命令 2026-07-07）＝実験開始を記録し、新しい売買記録CSVが出るまで pdca_gate が終了をブロック
            if ti.get("run_in_background"):
                touch(score_bg_pending)  # バックグラウンド実行中は審判催促を抑制（2026-06-13）
    # python(3) で実際に score.py/precheck.py を実行する形のみ検知（grep/echo/別行言及では誤爆しない）
    _is_judge = (bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*score[A-Za-z0-9_]*\.py", cmd_x)) or
                 bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*precheck\.py", cmd_x))) \
                and "--selftest" not in cmd_x   # --selftest は自己テスト＝採点でない（2026-06-18・誤点火防止）
    if _is_judge:
        # score.py / precheck.py（審判の門）。FAIL=閉じる場合も 分析・記録・5つの問い を飛ばせない（2026-06-12）
        rm(need_score)
        rm(score_bg_pending)
        if os.path.exists(diagnostic_active):
            pass   # 診断ラウンド中の採点＝PDCA 連鎖を立てない（不能ループ防止・2026-06-13）
        else:
            touch(need_report); touch(need_ledger); touch(need_analyze); touch(need_5q); touch(need_claim)
            touch(need_next_step)       # 審判を通したセッションは next_step を1回上書きするまで終了不可（2026-06-14 まこさん GO）
            touch(need_analyze_report)  # 分析レポートを生成→Read tool で読む まで終了不可（2026-06-15 まこさん命令）
            touch(need_viz)             # report.py の週次チャートPNG（4週）が出るまで終了不可（2026-06-21 まこさん強制化）
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*report\.py", cmd_x):
        rm(need_report)
        # 週次チャートPNG（report.py M節）が採点CSV分 実在すれば need_viz を下ろす（無ければ旗が残る＝番人）
        _mc = re.search(r'report\.py[ \t]+"?([^"\s]+\.csv)', cmd)
        if _mc and glob.glob(os.path.join(viz_dir, os.path.basename(_mc.group(1))[:-4] + "_*.png")):
            rm(need_viz)
        # --vs（前回比較・KB §0）必須。無しは need_vs 旗（初回のみ no_baseline_approved で免除・1回で消費）
        if "--vs" in cmd_x:
            rm(need_vs)
        elif os.path.exists(no_baseline):
            rm(no_baseline); rm(need_vs)
        else:
            touch(need_vs)
    # 分析＝analyze.py（汎用 N0-N12）＋ 戦略固有 *_deep_analysis/*_probe（命名規約・2026-06-16）
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*(analyze|[A-Za-z0-9_]+_deep_analysis|[A-Za-z0-9_]+_probe)\.py", cmd_x):
        # ★付け忘れ防止＝中身検査（2026-06-25 まこさん「強制・自動化」）: 汎用 analyze.py は出力に
        #   §0前後比較[前回≠今回]＋N4分布ドリフトが揃う時だけ need_analyze を下ろす。
        is_generic = bool(re.search(r"python[0-9.]*[ \t]+[^|&;\n]*analyze\.py", cmd_x))
        incomplete = os.path.join(state, "pdca_analyze_incomplete")
        if not is_generic:
            # 2026-07-04 まこさん承認: *_deep_analysis/_probe では need_analyze を下ろさない＝§0前後比較＋N4ドリフトの
            #   中身検査を通る汎用 analyze.py だけが分析完了（deep_analysis 経由で前後比較を飛ばす抜け道を閉鎖）。
            rm(incomplete)
        else:
            rdir = "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/results/priority_rebuild/ratchet"
            files = sorted(glob.glob(os.path.join(rdir, "analysis_*.txt")), key=os.path.getmtime)
            ok = False; why = ""
            if files:
                txt = open(files[-1], encoding="utf-8", errors="ignore").read()
                has_vs = "前後比較" in txt and "前回" in txt and "今回" in txt
                has_n4 = "N4. 分布ドリフト" in txt
                same = bool(re.search(r"件数 \+0% / net [+-]?0 / avg [+-]0\.00 / 勝率 [+-]0\.0pt", txt))
                if not has_vs:
                    why = "§0前後比較が無い（--vs <直前の実験(report持ち)> を付ける）"
                elif not has_n4:
                    why = "N4分布ドリフトが無い（--train <train.csv> を付ける）"
                elif same:
                    why = "前回=今回の同値比較＝無意味（直前の別実験を --vs に・採用base同値や付け先取り違えを正す）"
                else:
                    ok = True
            else:
                why = "analysis_*.txt が見つからない"
            if ok:
                rm(need_analyze); rm(incomplete)
            else:
                touch(need_analyze)
                open(incomplete, "w", encoding="utf-8").write(why)
    # ★「できない証明で止める」態度の物理禁止（まこさん 2026-06-27 命令）:
    #   probe(*_probe.py) を走らせたターンは forward_action.md（できる証明/達成案/次の一手）を書くまで終了不可。
    if re.search(r"python[0-9.]*[ \t]+[^|&;\n]*_probe\.py", cmd_x):
        touch(need_forward)
elif tn in ("Edit", "Write", "MultiEdit"):
    fp = ti.get("file_path", "") or ""
    if fp.endswith("ledger.md"):
        rm(need_ledger)
        # ★file-state ベース判定（2026-06-29 まこさん改善）: ledger の【最新エントリ】(最後の "## " セクション)に
        #   6見出し＋方針/狙い/目的＋主張 が在れば旗を下ろす（複数編集で書いても通る・過去エントリで誤通過しない）。
        tokens = ["【問0 前後比較】", "【問1 レバー】", "【問2 不足量】", "【問3 負け集中】", "【問4 過去接続】", "【問5 次仮説】"]
        try:
            _lg = open(fp, encoding="utf-8", errors="ignore").read()
        except Exception:
            _lg = (ti.get("new_string", "") or "") + (ti.get("content", "") or "")
        _entries = re.split(r"\n## ", _lg)
        latest = _entries[-1] if _entries else _lg     # 最新エントリ＝現在の実験の記録
        has_purpose = any(k in latest for k in ("方針", "狙い", "目的"))
        if all(t in latest for t in tokens) and has_purpose:
            rm(need_5q)
        if "【主張】" in latest:        # 多角チェックの結論=主張1行（件数/日+net 込み・2026-06-14）
            rm(need_claim)
    if fp.endswith("next_step.md"):
        # 次セッションの起点を上書き更新 → 旗を下ろす（必須トークン＋改善アーク表の gen 生成 hash 一致が条件・2026-06-27）。
        import hashlib
        try:
            full = open(os.path.join(state, "next_step.md"), encoding="utf-8").read()
        except Exception:
            full = (ti.get("new_string", "") or "") + (ti.get("content", "") or "")
        m = re.search(r"ARC_TABLE_START hash=(\w+).*?-->\n(.*?)\n<!-- ARC_TABLE_END", full, re.DOTALL)
        arc_ok = bool(m) and hashlib.sha256(m.group(2).encode("utf-8")).hexdigest()[:12] == m.group(1)
        if all(t in full for t in ("本筋", "やってはいけない", "出典", "改善アーク")) and arc_ok:
            rm(need_next_step); rm(score_bg_pending); rm(diagnostic_active)   # セッション境界の安全側クリア
    if fp.endswith("forward_action.md"):
        # ★前向きな達成案を書いた→need_forward を下ろす（必須3見出しが揃う編集でだけ解除・2026-06-27）。
        fwd = (ti.get("new_string", "") or "") + (ti.get("content", "") or "")
        for e in (ti.get("edits", []) or []):
            fwd += e.get("new_string", "") or ""
        if all(t in fwd for t in ("できる証明", "達成案", "次の一手")):
            rm(need_forward)
