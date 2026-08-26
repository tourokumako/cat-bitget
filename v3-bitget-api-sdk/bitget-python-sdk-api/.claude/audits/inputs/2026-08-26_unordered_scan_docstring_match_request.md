# 【読み比べの依頼】説明文と実装が意味として合っているか（106番・2026-08-26）

> **★この依頼書の中身は、問いの文（§D）以外すべて、実物のファイルからプログラムが抜き出したものです。**
> 起案した CC は、コードも説明文も1文字も打ち直していません（`next_step.md` §6 の92番の趣旨）。

---

## ⚠️ auditor 宣言 (本依頼書を開いた CC への指示・最優先・auto-load 上書き)

**あなた = 本セッションで auditor として呼ばれた CC です** (= 起案 CC = メインセッション の CC とは別 process)。SessionStart hook で auto-load される CLAUDE.md / cc_role.md / lessons_active.md / MEMORY.md / phase_compliance_checklist.md 等は **本監査では参考のみ**。着手前必読は本依頼書の §着手前必読 N 件のみ。

メインセッション CC (= 依頼書起案者) の判断バイアスを共有しないこと (同型バイアス回避・cc_role §1.4.5 改善 9)。

### 即実行 (本依頼書を読了したら確認質問なしで以下を実施)

1. 本依頼書全文を Read tool で view (機械的証跡: wc -l + 該当行引用)
2. `Agent` tool で **Plan サブエージェント** (`subagent_type=Plan`) を **cold start 起動**:
   - 本会話の context は渡さず、依頼書パス + 着手前必読ファイル名 + Q1-QN + 外部検索要請 のみ prompt として渡す
   - Plan agent が依頼書を独立に Read して監査実施・所見を返却
3. Plan agent 返却の所見を受けて結果ファイル `.claude/audits/2026-XX-XX_<task>_cpN_audit_report.md` を Write
4. メインセッションへの戻り報告:
   - 結果ファイルパス
   - Verdict 一行 (GO / NO-GO / PIVOT / OTHER)
   - 最優先指摘 (Critical) 件数

### 禁止

- 依頼書起案者 (メインセッション CC) への確認質問 (= 同型バイアス共有経路・本依頼書だけで完結する設計になっている)
- auto-load された正本だけで監査着手 (= 着手前必読の独立 Read 省略)
- 自分が main session か auditor session か再確認する質問 (本宣言が答え)
- Plan agent を起動せず CC 自身で監査実施 (= 同型バイアス回避失敗)

### 例外 (Plan agent 起動を省略可能なケース)

軽い意見聞き (Critical/Major 判断を伴わない確認程度) はメインセッション内で CC が直接回答可。本テンプレは CP 監査 (CP3.5 / CP4 / CP5 / CP6 等の大型監査) 用。

---

---

## 監査依頼メタ情報（機械が実物から出した）

| 項目 | 値 |
|---|---|
| 対象ファイル | `v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py` |
| そのファイルの sha256 | `eac54d702d544fe4cc9d813d9468398a479d7c1caf266a9ba236f2de41ac31f9` |
| 読み比べる関数 | `unordered_iteration_scan`（3544行 〜 3643行・100行） |
| テストの場所 | 同ファイル 3988行 〜 4030行 |
| まこさんの指示（逐語 2026-08-26） | 「なるほど。ではAIに読み比べさせることにする」／「なるほど。では別セッションの Claude Codeに依頼する」 |

**★この依頼は CP 監査ではありません。**読み比べ1点だけです。テンプレの「例外（軽い意見聞き）」に当たると判断する場合は、Plan サブエージェントを立てずに直接 答えても構いません。**その判断は、この依頼書を開いた側に委ねます。**

**★背景（1段落だけ・実測）**＝この検査は 2026-08-16 に作られました。説明文には最初から「その関数の中で作った set だけを見る」と書いてありましたが、実装はそうなっておらず、生成器の3行に誤って ❌ を出していました。2026-08-26（このセッション）に2か所 直し、テストを2件 足しました。**その直したあとの状態を読み比べてほしい、という依頼です。**

---

## §A 説明文（実装の docstring・プログラムが抜き出した逐語）

```
「並びの決まらない入れ物（set）を上から順に見ている」所を、ソースから機械で全部 探す。

何を守るか＝同じ入力なら同じ結果が出ること（再現できること）。
Python の set は中身の並びが決まっていません。走らせるたびに文字列の置き場所が変わるので、
set を上から順に見ると、実行ごとに順番が変わります。
2026-08-16 に生成器で実際に起きました＝案の候補の並びが毎回 変わり、同じ種でも別の案が出て、
過去の探索をやり直せない状態でした（`session_worklog_20260816.md` の §4）。

★手で場所の一覧を書きません（手書きの一覧は書き忘れると穴になる＝next_step §6 の50番）。
★見るのは3つ＝①`for x in {…}` のように set を直に回す ②内包表記が set を直に回す
  ③その関数の中で set として作った変数を、あとで回す。
★`sorted(...)` で包んだものは並びが決まるので、ここには出ません（回す相手が Call になる）。
★set 扱いをやめる場合が2つあります＝①同じ名前に別の物を代入し直したとき
  ②同じ名前を for 文か内包表記の**ループ変数**として使ったとき。どちらも「入れ直し」です。
★限界（4つ）＝(a) 関数の外から渡ってきた set（引数・戻り値）は追えません
  (b) 入れ子の関数（関数の中の関数）で、外側が作った set を内側で回す形は追えません
  (c) 内包表記のループ変数が set を受け取る形も追えません（代入ではないため）
  (d) set を作って、その同じ名前をループ変数にも使い、別の場所でその set を回す形は
      追えません（上の②で set 扱いをやめるため）。engine_tuner の4本には在りません（実測 0件）。
  ここで見るのは「その関数の中で作った set」だけです。

★2026-08-26（106番・まこさん承認 07a004de…）に2か所 直しました。
  ①走査を ast.walk から _own_nodes へ差し替え＝直す前は、ファイル全体を見る回で入れ子の
    関数の中まで潜っていたため、「別の関数で作った set」と「別の関数のループ」が名前だけで
    結び付き、生成器の2行に誤って ❌ を出していました（gen:1352・:1362・実測）。
  ②ループ変数として使われた名前の set 扱いをやめる＝直す前は、生成器 4708行の内包表記の
    ループ変数 got を、同じ関数の 4274行の set と取り違えていました（実測）。
  どちらも、上の「その関数の中で作った set だけ」という説明と、実装が食い違っていた状態です。
```

---

## §B 実装（同じ関数の全文・プログラムが抜き出した逐語）

```python
def unordered_iteration_scan(src: str) -> list[tuple[int, str]]:
    """「並びの決まらない入れ物（set）を上から順に見ている」所を、ソースから機械で全部 探す。

    何を守るか＝同じ入力なら同じ結果が出ること（再現できること）。
    Python の set は中身の並びが決まっていません。走らせるたびに文字列の置き場所が変わるので、
    set を上から順に見ると、実行ごとに順番が変わります。
    2026-08-16 に生成器で実際に起きました＝案の候補の並びが毎回 変わり、同じ種でも別の案が出て、
    過去の探索をやり直せない状態でした（`session_worklog_20260816.md` の §4）。

    ★手で場所の一覧を書きません（手書きの一覧は書き忘れると穴になる＝next_step §6 の50番）。
    ★見るのは3つ＝①`for x in {…}` のように set を直に回す ②内包表記が set を直に回す
      ③その関数の中で set として作った変数を、あとで回す。
    ★`sorted(...)` で包んだものは並びが決まるので、ここには出ません（回す相手が Call になる）。
    ★set 扱いをやめる場合が2つあります＝①同じ名前に別の物を代入し直したとき
      ②同じ名前を for 文か内包表記の**ループ変数**として使ったとき。どちらも「入れ直し」です。
    ★限界（4つ）＝(a) 関数の外から渡ってきた set（引数・戻り値）は追えません
      (b) 入れ子の関数（関数の中の関数）で、外側が作った set を内側で回す形は追えません
      (c) 内包表記のループ変数が set を受け取る形も追えません（代入ではないため）
      (d) set を作って、その同じ名前をループ変数にも使い、別の場所でその set を回す形は
          追えません（上の②で set 扱いをやめるため）。engine_tuner の4本には在りません（実測 0件）。
      ここで見るのは「その関数の中で作った set」だけです。

    ★2026-08-26（106番・まこさん承認 07a004de…）に2か所 直しました。
      ①走査を ast.walk から _own_nodes へ差し替え＝直す前は、ファイル全体を見る回で入れ子の
        関数の中まで潜っていたため、「別の関数で作った set」と「別の関数のループ」が名前だけで
        結び付き、生成器の2行に誤って ❌ を出していました（gen:1352・:1362・実測）。
      ②ループ変数として使われた名前の set 扱いをやめる＝直す前は、生成器 4708行の内包表記の
        ループ変数 got を、同じ関数の 4274行の set と取り違えていました（実測）。
      どちらも、上の「その関数の中で作った set だけ」という説明と、実装が食い違っていた状態です。
    """
    import ast
    import collections
    tree = ast.parse(src)

    def _is_set_expr(n) -> bool:
        return isinstance(n, (ast.Set, ast.SetComp)) or (
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id in ("set", "frozenset"))

    def _own_nodes(scope) -> list:
        """その scope 直属のノードだけを、幅優先で返す（入れ子の関数の中には入らない）。

        ★入れ子の関数の中身は、その関数自身が scope になった回で見ます＝取りこぼしません。
        ★幅優先のまま（ast.walk と同じ順）にしています。下の setvars は「同じ名前に別の物を
          入れ直したら set 扱いをやめる」という、順番に依存する判定を持つためです。
          今回 変えたのは「入れ子の関数に入らない」の1点だけです。
        """
        out: list = []
        q = collections.deque(ast.iter_child_nodes(scope))
        while q:
            n = q.popleft()
            out.append(n)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue          # 入れ子の関数は、それ自身が別の scope として見られる
            q.extend(ast.iter_child_nodes(n))
        return out

    def _bound_names(target) -> list:
        """ループが名前に入れる先を集める（`for a, (b, c) in …` のような入れ子も開く）。"""
        if isinstance(target, ast.Name):
            return [target.id]
        if isinstance(target, (ast.Tuple, ast.List)):
            return [nm for e in target.elts for nm in _bound_names(e)]
        return []

    hits: list[tuple[int, str]] = []
    scopes = [tree] + [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for scope in scopes:
        own = _own_nodes(scope)
        setvars: dict[str, int] = {}
        for n in own:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                nm = n.targets[0].id
                if _is_set_expr(n.value):
                    setvars[nm] = n.lineno
                elif nm in setvars:          # 同じ名前に別の物を入れ直したら set 扱いをやめる
                    del setvars[nm]
        # ★2026-08-26（106番）＝ループが名前に入れ直す場合も、上と同じく set 扱いをやめる。
        #   直す前は、生成器 4708行の `for got in bn.values() for c, _a in got`（内包表記の
        #   ループ変数）を、同じ関数の 4274行の set と取り違えて ❌ を出していた（実測）。
        for n in own:
            if isinstance(n, (ast.For, ast.AsyncFor)):
                for nm in _bound_names(n.target):
                    setvars.pop(nm, None)
            for gen in getattr(n, "generators", []) or []:
                for nm in _bound_names(gen.target):
                    setvars.pop(nm, None)
        for n in own:
            iters = []
            if isinstance(n, ast.For):
                iters.append(n.iter)
            for gen in getattr(n, "generators", []) or []:
                iters.append(gen.iter)
            for it in iters:
                if _is_set_expr(it):
                    hits.append((n.lineno, "set を直に上から順に見ている"))
                elif isinstance(it, ast.Name) and it.id in setvars:
                    hits.append((n.lineno, f"set の変数 {it.id}（{setvars[it.id]}行で作成）を上から順に見ている"))
    return sorted(set(hits))
```

---

## §C この検査のためのテスト（プログラムが抜き出した逐語）

```python
    # ══ 番人 並びの決まらない入れ物（2026-08-16 新設・A-1a-0 の2番）═══════════════════════
    #   何を守るか＝同じ入力なら同じ結果が出ること。手で場所の一覧を書かず、機械が全部 数える。
    #   ★番人の番人＝わざと set を回すコードを見せたら、ちゃんと見つけるか。
    _uo_files = ["engine_tuner_exec.py", "engine_tuner_gen.py", "tuner_judgement.py", "tuner_stats.py"]
    _uo_hits: list[str] = []
    _uo_seen = 0
    for _uf in _uo_files:
        _up = pathlib.Path(__file__).resolve().parent / _uf
        if not _up.exists():
            _uo_hits.append(f"{_uf}: ファイルが無い（数え上げの対象が消えた）")
            continue
        _uo_seen += 1
        for _ln, _why in unordered_iteration_scan(_up.read_text(encoding="utf-8")):
            _uo_hits.append(f"{_uf}:{_ln} {_why}")
    if not unordered_iteration_scan("def f():\n    s = {1, 2}\n    for x in s:\n        pass\n"):
        _uo_hits.append("番人の番人: わざと set を回すコードを見せても見つけない（検査が効いていない）")
    #   ★番人の番人2つ目（2026-08-26・106番・まこさん承認 462031cb…）＝見つけすぎないか。
    #     直す前はこの見本で 1件 出た（＝生成器の3行の誤報と同じ形・実装の前に実測）。
    #     別々の関数で同じ名前を使っているだけで、並びが決まらない所は1つも無い。
    #     dict は入れた順を保つ（Python 3.7 以降・実測で確認）。
    _uo_false = ("def a():\n"
                 "    fams = {}\n"
                 "    fams.setdefault('x', []).append(1)\n"
                 "    return [f for f in fams]\n"
                 "\n"
                 "\n"
                 "def b():\n"
                 "    fams = {1, 2}\n"
                 "    return fams\n")
    _uo_fp = unordered_iteration_scan(_uo_false)
    if _uo_fp:
        _uo_hits.append(f"番人の番人: 別の関数の同じ名前を誤って結び付けた（106番の誤報が戻った）: {_uo_fp}")
    #   ★番人の番人3つ目（同上）＝弱めすぎていないか。
    #     同じ関数の中で作った set を回すのは、今までどおり 1件 見つける（行も合う）。
    _uo_true = "def c():\n    got = {1, 2}\n    for x in got:\n        print(x)\n"
    _uo_tp = unordered_iteration_scan(_uo_true)
    if len(_uo_tp) != 1 or _uo_tp[0][0] != 3:
        _uo_hits.append(f"番人の番人: 同じ関数の中の set を回すのを見つけられない（検査が弱まった）: {_uo_tp}")
    ng += _uo_hits
    print(f"[番人 並びの決まらない入れ物] {_uo_seen} 本のファイルを機械で全部 数える"
          "（+ 番人の番人3つ＝わざと set を回すと見つけるか・別の関数の同名を誤って結び付けないか・"
          "同じ関数の中の set は見つけるか） → "
          + ("✅ 0 件・番人の番人3つとも期待どおり" if not _uo_hits else "❌ " + " ／ ".join(_uo_hits)))
```

---

## §D 問い（★ここだけが、起案した CC の手書きです）

### Q1（本題）
下の §A「説明文」が主張していることと、§B「実装」が実際にしていることは、**意味として合っていますか。**
合っていない所があれば、①説明文のどの文か ②実装のどの行か ③どう食い違うか、を1件ずつ挙げてください。

### Q2
**説明文に書かれていない振る舞いが、実装に在りますか。**在れば挙げてください。

### Q3
§C に、この検査のためのテストが3件 在ります。
**その3件では捕まえられない食い違いが在れば**、挙げてください。

### Q4
この検査が守ろうとしているのは「同じ入力なら同じ結果が出ること（並びの決まらない set を上から順に見ていないこと）」です。
**この目的に対して、検査が見落とす形が在れば**挙げてください。

---

## 返す先

所見は `.claude/audits/2026-08-26_unordered_scan_docstring_match_report.md` に書いてください。
**「合っています」だけで終わらせず、読み比べた根拠（説明文の文と、実装の行の対応）を残してください。**
