#!/usr/bin/env python3
"""gen_observe_manual.py — observe_diag の取扱説明書を機械生成する（手書き禁止・2026-07-26 まこさん指示）

なぜ機械生成か
--------------------------------------------------------------------------
手書きの説明書は必ず腐る。コードを直したときに説明書が更新されず、実体とずれる。
このプロジェクトでは既に gen_design.py（設計書）と gen_flow.py（フロー）が同じ理由で
機械生成になっている。本スクリプトはその3本目。

何を材料にするか（すべて実体から取る・CC が自由記述する箇所を作らない）
--------------------------------------------------------------------------
  ・observe_diag.py のフェーズ定義（SECTIONS / SECTIONS_SCENE）
  ・observe_diag.py の引数定義（build_parser）
  ・observe_diag.py の自己検査（selftest の検査文言）＝この道具が守ると言っていること
  ・observe_diag.py の説明文（モジュールの docstring）＝渡せるもの／渡せないもの／限界
  ・observe_config.json（設定で変えられるもの・登録済みの場面）
  ・periods.py（検証できる期間）

使い方
--------------------------------------------------------------------------
  python3 gen_observe_manual.py --write     # 生成して .claude/ratchet/ に書く
  python3 gen_observe_manual.py --verify    # 手書き改変と、作り直し忘れの検出（ハッシュ照合と、作り直した中身との比べ）
  python3 gen_observe_manual.py --selftest  # 自己検査（材料が実体から取れているかの番人）

出力の先頭に sha256 を入れる。--verify で本文と照合して手書き改変を検出し、さらに作り直した中身と1文字ずつ比べて、
実体や設定・売買記録が変わった後の作り直し忘れを検出する（gen_flow.py と同型）。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import observe_diag as od          # noqa: E402
from periods import SCORE_START, SCORE_END   # noqa: E402

ROOT = HERE.parents[1]                                   # bitget-python-sdk-api/（HERE=priority_rebuild → parents[0]=scripts）
# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。
#   なぜ要るか＝名前で数えると必ず漏れる（出力先の変数名が道具ごとにバラバラで、
#   読むファイルと作るファイルが同じ形で並んでいる＝外から見分けられない）。
#   だから道具の側に名乗らせる。集める道具＝gen_docmap.py。
#   形＝(リポジトリの根からのパス, "まるごと" か "一部の節")。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/observe_diag_manual.md", "まるごと"),
]

OUT = ROOT / ".claude" / "ratchet" / "observe_diag_manual.md"
CFG = HERE / "observe_config.json"


# ══ 言葉の説明（2026-07-26 まこさん指示）════════════════════════════════
#   経緯: できた説明書に対してまこさんから10個の質問が来た。うち8個は言葉の意味だった
#   （型とは／母集団とは／売買記録モードとは／場面観察モードとは／登録されている場面とは／
#     検証できる期間が採点窓と同じとは／設定ファイルは何の値か／指標の閾値・時間足・パラメータはあるのか）。
#   ＝説明書が CC 向けの用語のまま書かれていて、まこさん向けになっていなかった。
#   ここに定義表を持ち、説明書へ機械で流す。gen_flow.py が型を持つのと同じ方式
#   （説明書そのものは今までどおり自動生成＝手書き禁止）。
#   言葉を足すときはここに1行足す。英語をそのまま日本語にした言葉は使わない（まこさん指示）。
GLOSSARY: list[tuple[str, str]] = [
    ("既存ロジックの検証",
     "既に動いている戦略の売買記録CSVを渡して、改善すべき点を見つけるやり方。"
     "道具の目的の2つ目にあたる。旧称は売買記録モード。"),
    ("新規ロジックの検証",
     "まだ取引記録が無い新しい入口の候補を、値動きだけから調べるやり方。玉が無いので、"
     "値動きから仮の勝ち負けを機械で付けて調べる。道具の目的の1つ目にあたる。旧称は場面観察モード。"),
    ("フェーズ",
     "出力のまとまり。番号が付いていて、上から順に出る。既存ロジックの検証と新規ロジックの検証で中身が違う。"),
    ("型（down / flat_up）",
     "入口の型。建てた時点で決まる2種類。down は下落系で、天井が直近の高値。"
     "flat_up は平坦上昇系で、天井がレジスタンス帯の上端。値動きの形が違うので分けて見る。"),
    ("母集団",
     "分析する玉の全部、または観察する場面のバーの全部。統計の言葉をそのまま使っていた。"),
    ("場面",
     "入口の候補になる値動きの状況。例えば S2 は「レンジの中で戻ったところを売る」状況。"
     "どんな場面を見るかは設定ファイルに登録する。"),
    ("指標・時間足・パラメータ・閾値の組み合わせ",
     "検証の最小の1個。指標はRSIなどの計算方法。時間足は5分足や1時間足。パラメータはRSIの期間などの数値。"
     "閾値は「どこで線を引くか」。この4つが決まって、はじめて1つの条件になる。"),
    ("閾値と分位",
     "閾値は値そのものでは決めない。分布の何%の位置かで決める。上位30%より上、といった決め方。"
     "こうすると相場の水準が変わっても同じ意味の条件になる。設定の quantiles がその刻み。"),
    ("分離力",
     "指標1つで勝ちと負けがどれだけ分かれるかの強さ。強いほど、その指標だけで見分けられる。"
     "ただし実際には1つでは足りないので、材料として順位を出すだけに使う。"),
    ("コンフルエンス",
     "複数の条件が同時に成り立つこと。1つの指標では弱いので、種類の違う指標を2〜3個重ねて"
     "勝率が上がる組を探す。同じ種類の指標を二度掛けするのは禁止している。"),
    ("巻き込み",
     "負けを切ろうとしたときに、同じ条件に当たってしまう勝ち玉のこと。"
     "負けだけを切ることはできないので、切る案には必ずこれを付ける。"),
    ("出口理由",
     "その玉がどうやって決済されたか。利確、損切り、時間切れ、などの区別。売買記録に記録されている。"),
    ("検証できる期間が採点窓と同じ理由",
     "今の値動きに近い直近の期間だけで見るため。学習窓は2021年からで、価格の水準も相場つきも今と違う。"
     "だから観察にも使わない。窓を変えられるのはまこさんだけ。"),
    ("設定ファイルに並んでいる値",
     "検証の探索範囲。どの時間足を使うか、閾値を何段に刻むか、各指標の期間をいくつ試すか、など。"
     "走らせる前にこのファイルを編集して、範囲を広げたり狭めたりする。使った値は出力の先頭に全部出る。"),
]


# observe_diag と engine_tuner の違い（2026-07-26 まこさん質問「違いってなに？」）。
#   どちらも条件を探索するので混同しやすい。事実の裏づけ＝engine_tuner は 32行目で
#   `import score as judge`・91行目で `judge.score(t)` を呼ぶ（実エンジンを回して審判の式で評価）。
#   observe_diag は score を1度も呼ばない（read-only 診断・売買記録CSVも書かない）。
DIFF_ROWS: list[tuple[str, str, str]] = [
    ("何をする道具か", "観察して材料と候補を出す", "候補の値を決める"),
    ("売買エンジンを回すか", "回さない", "回す"),
    ("審判の式を使うか", "使わない", "使う"),
    ("手数料・約定・funding", "入らない", "入る"),
    ("同じ枠の取り合い", "入らない", "入る"),
    ("玉の集合", "条件を変えても変わらない", "条件を変えると変わる"),
    ("使う期間", "採点窓だけ", "探索窓と確認窓"),
    ("出す数字の意味", "材料。順位づけまで", "候補の順位づけ"),
    ("採否を決めるか", "決めない", "決めない"),
]


# 場面の型が「どんな値動きか」の説明（2026-07-26 まこさん指摘＝型の名前だけでは分からない）。
#   型そのものの一覧は observe_diag._SCENE_TYPES から取る。ここは名前と日本語の対応だけを持つ。
#   型を足したら1行足す（足し忘れは自己検査が落とす）。
SCENE_TYPE_JP = {
    "pullback_short": "レンジの中で戻ったところを売る",
    "fade_short": "レンジの上に抜けかけて失敗したところを売る",
    "zscore_short": "平均から統計的に離れすぎたところを売る",
    "crash_rebound_long": "急落したあとの反発を買う",
    "fade_long": "レンジの下に抜けかけて失敗したところを買う",
    "zscore_long": "平均から統計的に離れすぎたところを買う",
    "support_touch_long": "レンジの下端に触れたところを買う",
    "resistance_touch_short": "レンジの上端に触れたところを売る",
    "grid_short": "レンジを等分した線に下から触れたところを売る（グリッド売り）",
    "grid_long": "レンジを等分した線に上から触れたところを買う（グリッド買い）",
}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _catalog_names(cfg: dict) -> list[str]:
    """検証する指標の名前の一覧（実体＝observe_diag.build_catalog が作る（名前, 計算, 向き）の名前だけ）。"""
    return sorted({c[0] for c in od.build_catalog(cfg)})


def _mode_rows() -> list[tuple[str, str, str, str]]:
    """探索の系統ごとに（今オンか・名前・何を検証するロジックか・検証する値）を実体から取る。"""
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    on = set(cfg.get("search_modes") or [])
    rows = []
    for k, (name, logic, values) in od.MODE_INFO.items():
        rows.append(("オン" if k in on else "オフ", name, logic, values))
    return rows


def _pair_cols() -> list[str]:
    """玉と玉の間の特徴（指標とは別枠で探索に入る列）を実体から取る。"""
    src = inspect.getsource(od)
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and isinstance(node.slice.value, str):
            v = node.slice.value
            if any(v.startswith(p) for p in ("レンジ内", "前玉")):
                out.append(v)
    return sorted(set(out))


def _exit_reasons(cfg: dict) -> list[str]:
    """売買記録に出てくる出口理由。採用土台の売買記録CSVから実体で拾う（無ければ空）。"""
    import csv
    d = ROOT / "results" / "priority_rebuild" / "ratchet"
    files = sorted(d.glob("trades_*_score.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[:3]:
        try:
            with p.open(encoding="utf-8") as f:
                rd = csv.DictReader(f)
                if "exit_reason" not in (rd.fieldnames or []):
                    continue
                return sorted({r["exit_reason"] for r in rd if r.get("exit_reason")})
        except Exception:
            continue
    return []


def _doc_block(name: str) -> list[str]:
    """モジュールの説明文から、見出し行に続くブロックを取り出す（罫線で区切られた節）。"""
    doc = (od.__doc__ or "").split("\n")
    out, on = [], False
    for ln in doc:
        if ln.strip().startswith(name):
            on = True
            continue
        if on:
            if ln.strip().startswith("---"):      # 罫線は節の飾り＝読み飛ばす
                continue
            if ln.strip() and not ln.startswith(" ") and not ln.startswith("・") and out:
                break
            out.append(ln.rstrip())
    return [x for x in out if x.strip()]


def _guards() -> list[str]:
    """自己検査が「落とす条件」の文言を実体から取る＝この道具が守ると言っていること。"""
    src = inspect.getsource(od.selftest)
    out = []
    for node in ast.walk(ast.parse(src.lstrip())):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (isinstance(f, ast.Attribute) and f.attr == "append"):
            continue
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) and len(a.value) > 6:
                out.append(a.value)
            elif isinstance(a, ast.JoinedStr):        # f文字列は定数部分だけ拾う
                s = "".join(v.value for v in a.values if isinstance(v, ast.Constant))
                if len(s.strip()) > 6:
                    out.append(s.strip())
    return sorted(set(out))


def _args_rows() -> list[tuple[str, str]]:
    ap = od.build_parser()
    rows = []
    for act in ap._actions:
        if act.dest == "help":
            continue
        name = ", ".join(act.option_strings) if act.option_strings else act.dest
        rows.append((name, act.help or ""))
    return rows


def build() -> str:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    scenes = cfg.get("scenes") or {}
    L: list[str] = []
    L.append("# observe_diag 取扱説明書（gen_observe_manual.py が自動生成＝手書き禁止）")
    L.append("")
    L.append("⚠️ このファイルを手で書き換えないでください。中身は observe_diag.py と observe_config.json から")
    L.append("   機械で取っています。道具を直せばこの説明書も変わります。改変の検出は次のコマンドです。")
    L.append("")
    L.append("```")
    L.append("python3 scripts/priority_rebuild/gen_observe_manual.py --verify")
    L.append("```")
    L.append("")

    L.append("## この道具は何か")
    L.append("")
    L.append((od.__doc__ or "").strip().split("\n")[0].split("—", 1)[-1].strip())
    L.append("")

    L.append("## この道具の目的（まこさん確定 2026-07-26・正本は observe_diag.py の説明文）")
    L.append("")
    for ln in _doc_block("この道具の目的"):
        L.append(ln.strip() if ln.strip().startswith("・") else ln)
    L.append("")
    L.append("この2つに紐づかない機能は足しません。")
    L.append("")

    L.append("## 言葉の説明")
    L.append("")
    L.append("この説明書と observe_diag の出力に出てくる言葉です。先にここを読んでください。")
    L.append("")
    L.append("| 言葉 | 意味 |")
    L.append("|---|---|")
    for w, d in GLOSSARY:
        L.append(f"| {w} | {d} |")
    L.append("")

    L.append("## 2つのモード")
    L.append("")
    L.append("| モード | いつ使うか | 渡すもの |")
    L.append("|---|---|---|")
    L.append("| 既存ロジックの検証 | 実際に取引した記録を分析するとき | 売買記録CSV と 5分足CSV |")
    L.append("| 新規ロジックの検証 | まだ取引記録のない新しい入口の候補を、値動きから観察するとき | --scene で場面ID |")
    L.append("")
    L.append("どちらも `--plan` を付けると、検証計画だけを出して本走しません。まこさんへ提出する1枚です。")
    L.append("")

    L.append(f"## 既存ロジックの検証が出すもの（{len(od.SECTIONS)}フェーズ）")
    L.append("")
    L.append("| # | 何を出すか |")
    L.append("|---|---|")
    for s in od.SECTIONS:
        n, _, rest = s.partition(" ")
        L.append(f"| {n} | {rest} |")
    L.append("")

    L.append(f"## 新規ロジックの検証が出すもの（{len(od.SECTIONS_SCENE)}フェーズ）")
    L.append("")
    L.append("| # | 何を出すか |")
    L.append("|---|---|")
    for s in od.SECTIONS_SCENE:
        n, _, rest = s.partition(" ")
        L.append(f"| {n} | {rest} |")
    L.append("")

    L.append("## 実行のしかた")
    L.append("")
    L.append("```")
    L.append("# 既存ロジックの検証")
    L.append("python3 scripts/priority_rebuild/observe_diag.py <売買記録CSV> <5分足CSV>")
    L.append("# 新規ロジックの検証（まず計画を出してまこさんに提出→OK が出てから本走）")
    L.append("python3 scripts/priority_rebuild/observe_diag.py --scene <場面ID> --plan")
    L.append("python3 scripts/priority_rebuild/observe_diag.py --scene <場面ID>")
    L.append("# 自己検査")
    L.append("python3 scripts/priority_rebuild/observe_diag.py --selftest")
    L.append("```")
    L.append("")
    L.append("| 引数 | 意味 |")
    L.append("|---|---|")
    for name, hlp in _args_rows():
        L.append(f"| {name} | {hlp} |")
    L.append("")
    # ★保存先は実体（observe_diag.OBSERVE_DIR）から読む＝手で書かない。2026-08-03 まこさん指示で
    #   ratchet 直下 → その下の observe/ へ移した。実体を読む形なので、また変わっても説明書は自動で追う。
    L.append(f"結果は `{od.OBSERVE_DIR.relative_to(ROOT)}` に保存されます。"
             f"既にある同名は同じ階層の archive へ逃がすので上書きしません。")
    L.append("計画（--plan）は画面に出すだけで保存しません。")
    L.append("")

    L.append("## 検証する項目")
    L.append("")
    L.append("何を検証の対象にしているかの一覧です。すべてコードと設定ファイルから取っています。")
    L.append("")

    names = _catalog_names(cfg)
    L.append(f"### 1. 指標（{len(names)}種）")
    L.append("")
    L.append(f"この{len(names)}種に、時間足{len(cfg['timeframes'])}種を掛けて "
             f"{len(names) * len(cfg['timeframes'])}列になります。閾値は分位{len(cfg['quantiles'])}段で刻みます。")
    L.append("")
    for i in range(0, len(names), 6):
        L.append("- " + " ／ ".join(names[i:i + 6]))
    L.append("")

    L.append("### 2. 探索の系統")
    L.append("")
    L.append("一度に全部は回しません。1系統ずつ順番に回します。どれを回すかは設定の search_modes で決めます。")
    L.append("")
    L.append("| いま | 系統 | 何を検証するか | 検証する値 |")
    L.append("|---|---|---|---|")
    for st, name, logic, values in _mode_rows():
        L.append(f"| {st} | {name} | {logic} | {values} |")
    L.append("")

    pc = _pair_cols()
    if pc:
        L.append(f"### 3. 玉と玉の間の特徴（{len(pc)}列）")
        L.append("")
        L.append("指標とは別枠で、同じ土俵で探索に入ります。前の玉との関係から作る列です。")
        L.append("")
        for c in pc:
            L.append(f"- {c}")
        L.append("")

    L.append("### 4. 需給のデータ")
    L.append("")
    L.append("外から持ってくる3種です。期間の被覆が短いので、条件に選ばれにくいことがあります。")
    L.append("")
    for k in od._DEMAND_FILES:
        L.append(f"- {k}")
    L.append("")

    L.append("### 5. 場面の型")
    L.append("")
    L.append("新規ロジックの検証で使える型です。型を選んで、設定ファイルに場面として登録します。")
    L.append("")
    L.append("| 型 | どんな値動きの場面か |")
    L.append("|---|---|")
    for t in od._SCENE_TYPES:
        L.append(f"| {t} | {SCENE_TYPE_JP.get(t, '（説明が未登録）')} |")
    L.append("")

    er = _exit_reasons(cfg)
    if er:
        L.append(f"### 6. 出口理由（{len(er)}種）")
        L.append("")
        L.append("売買記録に出てくる決済のしかたです。多くのフェーズがこれで分けて見ます。")
        L.append("")
        L.append("- " + " ／ ".join(er))
        L.append("")

    L.append("## 登録されている場面")
    L.append("")
    L.append("新規ロジックの検証で観察できる入口の候補です。設定ファイルに登録したものが並びます。")
    L.append("")
    if scenes:
        L.append("| 場面ID | 方向 | どんな場面か | 判定の窓 | 勝ちの条件 |")
        L.append("|---|---|---|---|---|")
        for sid, s in scenes.items():
            wt = s.get("win_target", "mid")
            win = "レンジ中央に先着" if wt == "mid" else f"建値から手数料床×{s.get('win_pct_k', '?')} の順行に先着"
            ty = s.get("type", "")
            bars = s.get("tmax_bars", "")
            mins = f"{int(bars) * 5}分" if str(bars).isdigit() else str(bars)
            L.append(f"| {sid} | {s.get('side', '')} | {SCENE_TYPE_JP.get(ty, ty)} | {mins} | {win} |")
    else:
        L.append("登録なし")
    L.append("")
    L.append("同じ型が複数あるのは、同じ場面を条件を変えて観察しているためです。"
             "判定の窓は、建ててから勝ち負けを判定するまでの時間です。")
    L.append("")

    L.append("## 設定で変えられるもの")
    L.append("")
    L.append(f"設定ファイル: `{CFG.relative_to(ROOT)}`")
    L.append("")
    L.append("| 項目 | いまの値 |")
    L.append("|---|---|")
    for k, v in cfg.items():
        if k.startswith("_") or k in ("scenes",):
            continue
        sv = json.dumps(v, ensure_ascii=False)
        L.append(f"| {k} | {sv if len(sv) <= 120 else sv[:117] + '…'} |")
    L.append("")

    L.append("## 検証できる期間")
    L.append("")
    L.append(f"採点窓 {SCORE_START.date()} 〜 {SCORE_END.date()} の中だけです（periods.py が正本）。")
    L.append("この外を設定で指定しても止まります。学習窓と封印期間は使えません。")
    L.append("")

    L.append("## 渡せるもの／渡せないもの")
    L.append("")
    for ln in _doc_block("呼び出し側が渡せるもの"):
        L.append(ln)
    L.append("")

    L.append("## この道具が守ると言っていること")
    L.append("")
    for ln in _doc_block("守っていること"):
        L.append(ln)
    L.append("")
    L.append("上は説明文です。実際に機械で検査している項目は下です。`--selftest` で全部走ります。")
    L.append("どれか1つでも崩れると自己検査が止まります。")
    L.append("")
    for g in _guards():
        L.append(f"- {g}")
    L.append("")

    L.append("## engine_tuner との違い")
    L.append("")
    L.append("どちらも条件を探索します。名前も役割も似ているので混同しやすいですが、"
             "評価のしかたが根本的に違います。")
    L.append("")
    L.append("| | observe_diag | engine_tuner |")
    L.append("|---|---|---|")
    for a, b, c in DIFF_ROWS:
        L.append(f"| {a} | {b} | {c} |")
    L.append("")
    L.append("### 一番大きい違い")
    L.append("")
    L.append("observe_diag は、既にある玉や場面のバーに条件を当てはめて、勝ち負けを静かに数えます。"
             "条件を変えても玉は増えません。")
    L.append("")
    L.append("engine_tuner は、条件を変えるたびに売買エンジンを最初から回し直します。"
             "だから玉の集合そのものが変わります。同じ枠を別の玉が取り合う動きも入ります。")
    L.append("")
    L.append("これが「疑似シミュで上位だった条件が、実際に回すと順位が逆転する」の理由です（L-330）。"
             "observe_diag が良いと言った条件が engine_tuner で悪くなることは普通に起きます。")
    L.append("")
    L.append("### 検証の3層での位置")
    L.append("")
    L.append("```")
    L.append("層1 観察      → observe_diag（材料と候補を出す）")
    L.append("層2 あたり付け → 疑似シミュ（採否にも候補選定にも使わない）")
    L.append("層3 候補選定  → engine_tuner（実エンジン × 審判の式で値を決める）")
    L.append("本走・採否    → e38_priority_stack + score.py（採点窓・まこさんが決める）")
    L.append("```")
    L.append("")
    L.append("observe_diag は入口です。engine_tuner は出口の1つ手前です。")
    L.append("")
    L.append("### 紛らわしい点")
    L.append("")
    L.append("observe_diag のフェーズ8 も条件を探索します。engine_tuner と名前も動きも似ています。")
    L.append("")
    L.append("ただしフェーズ8 は「既にある玉のうち、どれを除外すると合計がどうなるか」を静かに計算するだけです。"
             "engine_tuner のように回し直しません。だから同じ「探索」でも数字の重みが違います。")
    L.append("")

    L.append("## この道具では分からないこと")
    L.append("")
    L.append("- 採否は決められません。採否は score.py を採点窓に通して、まこさんが決めます。")
    L.append("- 場面観察の数字は疑似シミュです。スロットの取り合い・約定の不確実・funding を含みません。")
    L.append("- 実際の成績は層3 の実エンジンでしか出ません。観察は候補の材料までです。")
    L.append("")

    body = "\n".join(L).rstrip() + "\n"
    return f"<!-- MANUAL_HASH={_sha(body)} -->\n{body}"


def _print_stale(old: str, new: str) -> None:
    """作り直した中身と違うときに、違う行の数と、違う行の全部を画面に出す（verify から呼ぶ）。"""
    import difflib
    diff = [ln for ln in difflib.unified_diff(old.splitlines(), new.splitlines(),
                                              "いまの文書", "作り直した中身", n=0, lineterm="")
            if ln not in ("--- いまの文書", "+++ 作り直した中身")]
    n = sum(1 for ln in diff if ln[:1] in ("-", "+"))
    print(f"❌ 作り直していない（実体・設定・売買記録が変わった後に、作り直していない・違う行 {n} 行）")
    for ln in diff:
        print(f"   {ln}")
    print("   直し方: python3 scripts/priority_rebuild/gen_observe_manual.py --write")


# ★2026-10-15（工事 verify-rebuild-compare-20261015）＝作り直しとの照らしの番人の部品。selftest から呼ぶ。
def _stale_guard(wrap, txt: str, run_verify) -> list[str]:
    """番人の部品。一時の置き場に文書を置いて、照らす旗を走らせる。

    ①作り直した中身そのままの文書は通す（終了コード 0）
    ②1行 足して、ハッシュ値だけを合わせた文書は止める（終了コード 1）
    本物の文書には書かない。
    """
    import contextlib
    import io
    import tempfile
    ng: list[str] = []
    _, _, body = txt.partition("\n")
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "doc.md"
        for name, content, want in (("作り直した中身のまま", txt, 0),
                                    ("ハッシュ値は合うが古い", wrap(body + "番人用の古い行\n"), 1)):
            p.write_text(content, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                rc = run_verify(p)
            if rc != want:
                ng.append(f"番人（作り直しとの照らし）失敗＝{name}の文書で、照らす旗の終了コードが {rc}（期待 {want}）")
    return ng


def verify(path: pathlib.Path = OUT) -> int:
    if not path.exists():
        print(f"❌ 説明書が無い: {path}"); return 1
    txt = path.read_text(encoding="utf-8")
    head, _, body = txt.partition("\n")
    want = head.replace("<!-- MANUAL_HASH=", "").replace(" -->", "").strip()
    got = _sha(body)
    if want != got:
        print(f"❌ 手書きで書き換えられている（ハッシュ不一致 期待 {want} / 実際 {got}）"); return 1
    # ★2026-10-15（工事 verify-rebuild-compare-20261015）＝作り直した中身と1文字ずつ比べる。
    #   ハッシュ値の照らしは、手の書き換えしか見ない。実体（observe_diag.py）や設定・売買記録が変わった後に
    #   --write を走らせ忘れても「改変なし」と出ていた（2026-10-14 の実測・worklog 20261014 §10）。
    rebuilt = build()
    if txt != rebuilt:
        _print_stale(txt, rebuilt)
        return 1
    print(f"✅ 改変なし・作り直した中身と一致（ハッシュ {got}）"); return 0


def selftest() -> int:
    ng = []
    if not hasattr(od, "build_parser"):
        ng.append("observe_diag に引数定義の関数が無い＝実行のしかたを実体から取れない")
    if len(od.SECTIONS) < 2 or len(od.SECTIONS_SCENE) < 2:
        ng.append("フェーズ定義が実体から取れていない")
    if len(_guards()) < 10:
        ng.append(f"自己検査の検査文言が実体から取れていない（{len(_guards())}件しか拾えない）")
    if not _args_rows():
        ng.append("引数の一覧が実体から取れていない")
    if not _doc_block("守っていること"):
        ng.append("説明文の『守っていること』が実体から取れていない")
    # 目的（まこさん確定 2026-07-26）が実体から取れて説明書に載ること＝この道具の存在理由が消えない
    pur = _doc_block("この道具の目的")
    if len(pur) < 2:
        ng.append("説明文に『この道具の目的』が無い（何のための道具かが正本に書かれていない）")
    for need in ("組み合わせロジックを見つける", "改善すべき点を見つける"):
        if not any(need in x for x in pur):
            ng.append(f"目的の逐語が欠けている: {need}")
    # 検証する項目（2026-07-26 まこさん OK）が実体から取れていること
    cfg0 = json.loads(CFG.read_text(encoding="utf-8"))
    if len(_catalog_names(cfg0)) < 50:
        ng.append(f"指標の一覧が実体から取れていない（{len(_catalog_names(cfg0))}種しか拾えない）")
    if len(_mode_rows()) < 3:
        ng.append("探索の系統が実体から取れていない")
    if not _pair_cols():
        ng.append("玉と玉の間の特徴が実体から取れていない")
    miss = [t for t in od._SCENE_TYPES if t not in SCENE_TYPE_JP]
    if miss:
        ng.append(f"場面の型の説明が未登録: {miss}（型を足したら SCENE_TYPE_JP にも足す）")
    txt = build()
    if len(DIFF_ROWS) < 5:
        ng.append("engine_tuner との違いの表が足りない（混同したまま使われる）")
    for must in ("この道具は何か", "この道具の目的", "言葉の説明", "2つのモード", "実行のしかた",
                 "検証する項目", "指標（", "探索の系統", "場面の型",
                 "登録されている場面", "設定で変えられるもの", "検証できる期間",
                 "engine_tuner との違い", "検証の3層での位置", "紛らわしい点",
                 "この道具では分からないこと"):
        if must not in txt:
            ng.append(f"説明書に見出しが無い: {must}")
    # 2026-07-26 にまこさんが引っかかった言葉が、全部 説明書に載っていること
    for w in ("既存ロジックの検証", "新規ロジックの検証", "型（down / flat_up）", "母集団", "場面",
              "指標・時間足・パラメータ・閾値の組み合わせ", "分離力", "コンフルエンス",
              "検証できる期間が採点窓と同じ理由", "設定ファイルに並んでいる値"):
        if not any(w == k for k, _ in GLOSSARY):
            ng.append(f"言葉の説明が抜けている: {w}")
        if w not in txt:
            ng.append(f"言葉の説明が説明書に出ていない: {w}")
    # 番人＝実体を差し替えたら生成物も変わること（＝実体から取っている証拠）
    keep = od.SECTIONS
    try:
        od.SECTIONS = list(keep) + ["99 番人用のダミー"]
        if "番人用のダミー" not in build():          # 表の行は「| 99 | 番人用のダミー |」に整形される
            ng.append("フェーズ一覧が実体を見ていない（コードを変えても説明書が変わらない）")
    finally:
        od.SECTIONS = keep
    # 番人（2026-10-15・工事 verify-rebuild-compare-20261015）＝ハッシュ値は合うが、作り直した中身と違う文書を、照らす旗が止めること
    ng.extend(_stale_guard(lambda b: f"<!-- MANUAL_HASH={_sha(b)} -->\n{b}", txt, verify))
    print("=" * 80)
    print("gen_observe_manual 自己検査")
    print("=" * 80)
    print(f"  フェーズ 既存ロジックの検証 {len(od.SECTIONS)} / 新規ロジックの検証 {len(od.SECTIONS_SCENE)}")
    print(f"  引数 {len(_args_rows())} 個 / 機械で検査している項目 {len(_guards())} 件")
    print(f"  出力先 {OUT}")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="observe_diag の取扱説明書を機械生成する")
    ap.add_argument("--write", action="store_true", help="生成して書き出す")
    ap.add_argument("--verify", action="store_true", help="手書き改変と、作り直し忘れの検出")
    ap.add_argument("--selftest", action="store_true", help="自己検査")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        sys.exit(verify())
    txt = build()
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(txt, encoding="utf-8")
        print(f"✅ 書き出した: {OUT}（{len(txt.splitlines())}行・ハッシュ {txt.split('=')[1].split(' ')[0]}）")
    else:
        print(txt)


if __name__ == "__main__":
    main()
