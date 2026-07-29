#!/usr/bin/env python3
"""gen_engine_tuner_manual.py — engine_tuner の取扱説明書を機械生成する（手書き禁止・2026-07-27 まこさん指示）

なぜ機械生成か
--------------------------------------------------------------------------
手書きの説明書は必ず腐る。コードを直したときに説明書が更新されず、実体とずれる。
このプロジェクトでは gen_design.py（設計書）・gen_flow.py（フロー）・gen_observe_manual.py（観察器の説明書）が
同じ理由で機械生成になっている。本スクリプトはその4本目。型は gen_observe_manual.py に合わせた。

この説明書の位置づけ（まこさん指示 2026-07-27）
--------------------------------------------------------------------------
「現状の engine_tuner が何をできるか」の記録である。何のための道具にするかの要件定義は この後に決める。
だから本書には「こうあるべき」を書かない。実体が今できることと、今できないことだけを機械で出す。

何を材料にするか（すべて実体から取る・CC が自由記述する箇所を作らない）
--------------------------------------------------------------------------
  ・engine_tuner.py の説明文・窓の定数・引数定義（build_parser）
  ・engine_tuner.py と e38_logic_parts.py の 実行前に止める条件（assert / SystemExit の文言）
  ・e38_logics.json の logics（探索できるロジックの登録）と search_space（探索する値の宣言）
  ・e38_logic_parts.py の入口の型テーブル（ENTRY_FNS）と確認の部品（HTF_PARTS / VOL_PARTS）
  ・periods.py（採点窓＝探索に使ってはいけない期間）
  ・gen_observe_manual.py の DIFF_ROWS（observe_diag との違い＝実体1箇所で管理する）

使い方
--------------------------------------------------------------------------
  python3 gen_engine_tuner_manual.py --write     # 生成して .claude/ratchet/ に書く
  python3 gen_engine_tuner_manual.py --verify    # 手書き改変の検出（ハッシュ照合）
  python3 gen_engine_tuner_manual.py --selftest  # 自己検査（材料が実体から取れているかの番人）

出力の先頭に sha256 を入れる。--verify で本文と照合して手書き改変を検出する（gen_observe_manual.py と同型）。
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

import e38_logic_parts as parts      # noqa: E402
import engine_tuner as es       # noqa: E402
from gen_observe_manual import DIFF_ROWS   # noqa: E402  observe_diag との違いは実体1箇所（あちらが正本）
from periods import SCORE_START, SCORE_END  # noqa: E402
from tuner_adapters import available, load_adapter   # noqa: E402  戦略ごとの接続ファイル（要件 R4）

ROOT = HERE.parents[1]                                   # bitget-python-sdk-api/
OUT = ROOT / ".claude" / "ratchet" / "engine_tuner_manual.md"
CFG = HERE / "e38_logics.json"


# ══ 言葉の説明（gen_observe_manual.GLOSSARY と同じ方式・英語をそのまま日本語にした言葉は使わない）══
#   足すときはここに1行足す。説明書へ機械で流す。
GLOSSARY: list[tuple[str, str]] = [
    # ⚠️ ここに秒数を書かないこと（2026-07-27 まこさん OK・監査 提案1）。
    #    以前は「実測でおよそ7秒かかる」と手で書いてあったが、それは別の道具 engine_search_e37.py の値だった。
    #    所要は engine_tuner が走るたびに実測して engine_tuner_timing.json に残す＝下の「1試行にかかる時間」で読む。
    ("試行",
     "値を1組決めて、その値で売買エンジンを最初から1回まるごと回して、審判で採点するまでの1回。"
     "試行の回数は --trials で決める。"),
    ("値決め窓",
     "どの値が良いかを決めるために使う期間。この期間の成績だけを見て値を選ぶ。"),
    ("確認窓",
     "値決め窓で選んだ値を、そのまま1回だけ走らせて表示する期間。ここの成績で値を選び直さない。"
     "選び直すと確認の意味が消えるため。"),
    ("採点窓",
     "採否を決めるための期間。探索には一切使わない。ここを探索に使うと、"
     "その期間に一番合う値を選ぶことになり、本番で再現しない（L-267）。"),
    ("分位から決める閾値",
     "閾値を値そのもので指定せず、その期間の分布の何%の位置かで指定するやり方。"
     "相場の水準が変わっても同じ意味の条件になる。CC が数字を手で打たない仕組みでもある。"),
    ("目的関数",
     "探索が最大にしようとする数字。いまは値決め窓の審判の純益。"),
    ("件数の下限ゲート",
     "1日あたりの件数がこの数を下回った試行を捨てる仕組み。"
     "純益だけを見ると、ほとんど建てずに損を減らすだけの形に逃げ込むため。"),
    ("入口の型",
     "どんな値動きで建てるかの種類。戻り売り、上抜け失敗、統計的な行き過ぎ、など。"
     "型ごとに専用の関数がある。"),
    ("確認の部品",
     "入口の条件に足す2つ目・3つ目の条件。上位足が過熱していないか、ボラと出来高が足りているか、を見る。"),
    ("汎用部品ロジック",
     "e38_logic_parts.py の共通の売買ループで動くロジック。値を差し替えるだけで走るので探索できる。"
     "これに当てはまらないロジックは、いまの探索器では扱えない。"),
    # ★ロジックと戦略の区別（まこさん指摘 2026-07-27「一度に1本のロジックというか戦略ということね？
    #   書き方が誤解を与える」）。この2語を混ぜて書くと、何が調整できて何ができないかが伝わらない。
    ("ロジック",
     "1つの入口と出口の組み合わせ。例えば S2 の戻り売り。engine_tuner が値を調整する単位はこれ。"),
    ("戦略",
     "複数のロジックを優先度で並べた全体。例えば E38 は S1・L1・S2 … を優先度順に並べる。"
     "同じ予算 0.12 BTC を取り合い、優先度の順に枠を取る。ロジック単体とは成績が変わる。"),
]


# パラメータ名の日本語（実体の名前だけでは何の値か分からないため・足したら1行足す）
PARAM_JP: dict[str, str] = {
    "tp1_frac": "1段目の利確を、建値と2段目の間のどこに置くか",
    "tp2_target": "2段目の利確の位置。mid はレンジ中央、opp は反対側のゾーン手前",
    "sl_zone_k": "損切りをゾーンの外側へ、帯の幅の何倍だけ離すか",
    "tmax_bars": "保有の上限。5分足の本数",
    "be_wait": "時間切れのとき、建値で待ってから決済するか",
    "tp_mode": "利確の置き方。zone はレンジの形に合わせた2段、pct は建値から固定%の1段",
    "tp_pct_k": "pct のときの利確幅。手数料の床の何倍か",
    "pos_min": "戻りの深さの下限。レンジ中央から上端までのどこまで戻ったか",
    "confirm": "失速したことの確認のしかた",
    "confirm_htf": "上位足のモメンタムが過熱していないかを見る部品",
    "confirm_vol": "ボラと出来高が足りているかを見る部品",
    "over_min": "抜けた幅の下限。帯の幅に対する比",
    "confirm_bars": "何本待ってから確認するか",
    "z_th": "平均からどれだけ離れたら建てるかの閾値",
    "trigger": "すぐ建てるか、反転を確認してから建てるか",
    "k_bars": "下落率を測る本数",
    "drop_th": "下落率の閾値",
    "vol_mult": "出来高が平均の何倍か",
    "fresh_only": "帯に入った最初のバーだけにするか",
}


def _param_jp(name: str) -> str:
    if name in PARAM_JP:
        return PARAM_JP[name]
    if name.startswith("th_"):
        return f"{name[3:]} の閾値"
    return ""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _c(s) -> str:
    """表のセルに入れる文字列を無害化する。実体の文字列に縦棒や改行が入ると表が崩れるため。"""
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def _const_text(node) -> str:
    """文字列定数と f文字列を取り出す。変数の位置は … で示す（消すと文の意味が取れなくなるため）。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else "…"
                       for v in node.values)
    return ""


def _guards() -> list[str]:
    """実行を止める条件の文言を実体から取る＝この道具が守ると言っていること。
    engine_tuner と e38_logic_parts の assert と SystemExit を機械で拾う。"""
    out = []
    for mod in (es, parts):
        for node in ast.walk(ast.parse(inspect.getsource(mod))):
            if isinstance(node, ast.Assert) and node.msg is not None:
                s = _const_text(node.msg).strip()
                if len(s) > 6:
                    out.append(s)
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                f = node.exc.func
                if isinstance(f, ast.Name) and f.id == "SystemExit" and node.exc.args:
                    s = _const_text(node.exc.args[0]).strip()
                    if len(s) > 6:
                        out.append(s)
    return sorted(set(out))


def _args_rows() -> list[tuple[str, str]]:
    rows = []
    for act in es.build_parser()._actions:
        if act.dest == "help":
            continue
        name = ", ".join(act.option_strings) if act.option_strings else act.dest
        rows.append((name, act.help or ""))
    return rows


def _cfg() -> dict:
    return json.loads(CFG.read_text(encoding="utf-8"))


def _adapters() -> list:
    """在る接続ファイルを全部読み込む（＝扱える戦略の一覧・実体は tuner_adapters/ の中身）。"""
    return [load_adapter(n) for n in available()]


def _all_logics() -> list[tuple[str, dict]]:
    """(戦略名, ロジックの情報) の一覧。回せるかの判定は接続ファイルが返したものをそのまま使う
    ＝説明書が自前で判定し直さない（実体と食い違わせないため）。"""
    out = []
    for ad in _adapters():
        for z in ad.logics():
            out.append((ad.NAME, z))
    return out


def _space_rows(space: dict) -> list[tuple[str, str, str]]:
    rows = []
    for name, d in space.items():
        t = d["type"]
        if t == "float":
            how = f"{d['lo']} 〜 {d['hi']} の間の値"
        elif t == "cat":
            how = "この中から1つ： " + " / ".join(str(x) for x in d["choices"])
        elif t == "quantile":
            how = (f"{d['series']} の分布の {d['q_lo'] * 100:g}% 〜 {d['q_hi'] * 100:g}% の位置から"
                   "実行時に決める")
        else:
            how = json.dumps(d, ensure_ascii=False)
        rows.append((name, _param_jp(name), how))
    return rows


def _timing() -> dict:
    """1試行の所要（engine_tuner が走るたびに実測して残したもの）。手書きの秒数は使わない。"""
    p = es.TIMING
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                        # noqa: BLE001
        return {}


def _coverage_rows() -> list[tuple[str, str, int, str]]:
    """(戦略, ロジック, 触れる列の本数, 割合) ＝どれだけ試していないかを機械で出す。"""
    size = es.catalog_size()
    total = size[0] * size[1] if size else 0
    out = []
    for ad in _adapters():
        cov = getattr(ad, "coverage", None)
        if cov is None:
            continue
        for z in ad.logics():
            if not z["searchable"]:
                continue
            n = len(list(cov(z["id"])))
            out.append((ad.NAME, z["id"], n, f"{n / total * 100:.2f}%" if total else "分母が取れない"))
    return out


def _doc_first_line() -> str:
    return (es.__doc__ or "").strip().split("\n")[0].split("—", 1)[-1].strip()


def _doc_block(name: str) -> list[str]:
    """説明文から、見出し行に続くブロックを取り出す（罫線で区切られた節・gen_observe_manual と同型）。
    ＝目的と使う順番の正本は engine_tuner.py の説明文であって、この生成器ではない。"""
    out, on = [], False
    for ln in (es.__doc__ or "").split("\n"):
        if ln.strip().startswith(name):
            on = True
            continue
        if on:
            if ln.strip().startswith("---"):          # 罫線は節の飾り＝読み飛ばす
                continue
            if ln.strip() and not ln.startswith((" ", "・", "▼", "※")) and out:
                break
            out.append(ln.rstrip())
    return [x for x in out if x.strip()]


def build() -> str:
    cfg = _cfg()
    logics = cfg["logics"]
    L: list[str] = []
    L.append("# engine_tuner 取扱説明書（gen_engine_tuner_manual.py が自動生成＝手書き禁止）")
    L.append("")
    L.append("⚠️ このファイルを手で書き換えないでください。中身は engine_tuner.py と")
    L.append("   e38_logic_parts.py と e38_logics.json から機械で取っています。")
    L.append("   道具を直せばこの説明書も変わります。改変の検出は次のコマンドです。")
    L.append("")
    L.append("```")
    L.append("python3 scripts/priority_rebuild/gen_engine_tuner_manual.py --verify")
    L.append("```")
    L.append("")

    L.append("## この説明書の位置づけ")
    L.append("")
    L.append("**いまの engine_tuner が何をできるかの記録です。** 何のための道具にするかの要件定義は、")
    L.append("この説明書を読んだ後に決めます。だから本書には「こうあるべき」を書きません。")
    L.append("実体が いまできること と いまできないこと だけを機械で出しています。")
    L.append("")

    L.append("## この道具は何か")
    L.append("")
    L.append(_doc_first_line())
    L.append("")
    L.append("値を1組決めて、売買エンジンを最初から回して、審判で採点する。これを何度も繰り返して、")
    L.append("値決め窓で一番よかった値を出します。**採否は決めません。**")
    L.append("")

    L.append("## この道具の目的（まこさん確定 2026-07-27・正本は engine_tuner.py の説明文）")
    L.append("")
    for ln in _doc_block("この道具の目的"):
        L.append(ln.strip() if ln.strip().startswith("・") else ln)
    L.append("")
    L.append("この2つに紐づかない機能は足しません。")
    L.append("")

    L.append("## 言葉の説明")
    L.append("")
    L.append("この説明書と engine_tuner の出力に出てくる言葉です。先にここを読んでください。")
    L.append("")
    L.append("| 言葉 | 意味 |")
    L.append("|---|---|")
    for w, d in GLOSSARY:
        L.append(f"| {_c(w)} | {_c(d)} |")
    L.append("")

    L.append("## 実行のしかた")
    L.append("")
    L.append("```")
    L.append(f"TAGLESS_OK=1 python3 scripts/priority_rebuild/{pathlib.Path(inspect.getfile(es)).name}"
             " --logic <ロジックid> --trials <試す回数>")
    L.append("```")
    L.append("")
    L.append("| 引数 | 意味 |")
    L.append("|---|---|")
    for name, hlp in _args_rows():
        L.append(f"| {_c(name)} | {_c(hlp)} |")
    L.append("")
    L.append("売買記録CSVは書きません。だからこれは実験ではなく、値を選ぶための装置です。")
    L.append("試行のログだけがファイルに残ります。")
    L.append("")

    L.append("## 使う期間")
    L.append("")
    L.append("| 窓 | 期間 | 何に使うか |")
    L.append("|---|---|---|")
    L.append(f"| 値決め窓 | {es.SEARCH_START.date()} 〜 {es.SEARCH_END.date()} の手前まで | "
             "この期間の成績だけで値を選ぶ |")
    L.append(f"| 確認窓 | {es.CONFIRM_START.date()} 〜 {es.CONFIRM_END.date()} の手前まで | "
             "選んだ値のまま1回走らせて表示するだけ。選び直さない |")
    L.append(f"| 採点窓 | {SCORE_START.date()} 〜 {SCORE_END.date()} | "
             "この道具では使わない。採否のための期間 |")
    L.append("")
    L.append(f"どちらの窓も、指標の助走のために {es.WARM.days} 日ぶん手前からデータを読み込みます。")
    L.append("助走の期間には建てません。")
    L.append("")
    L.append("窓が採点窓と重なっていないかを、起動した瞬間に機械で検査しています。重なっていれば止まります。")
    L.append("")

    L.append("## 扱える戦略")
    L.append("")
    L.append("戦略ごとに「接続ファイル」を1枚ずつ持ちます。**探索器は接続ファイルだけを見て、")
    L.append("戦略の中身（値をどこで差し替えるか）を知りません。** 戦略を1つ足すときは接続ファイルを1枚足すだけです。")
    L.append("")
    L.append("| 名前 | どんな戦略か |")
    L.append("|---|---|")
    for ad in _adapters():
        L.append(f"| {_c(ad.NAME)} | {_c(ad.LABEL)} |")
    L.append("")
    L.append("接続ファイルの置き場所は `scripts/priority_rebuild/tuner_adapters/` です。")
    L.append("必要なものが1つでも欠けていると、実行の前に止まります。")
    L.append("")

    L.append("## 調整できるロジック")
    L.append("")
    L.append("**回せるかどうかは接続ファイルが返した判定をそのまま出しています。**")
    L.append("説明書が自前で判定し直していません（実体と食い違わせないため）。")
    L.append("")
    L.append("| 戦略 | id | サイド | どんなロジックか | いま調整できるか |")
    L.append("|---|---|---|---|---|")
    rows = _all_logics()
    for sname, z in rows:
        mark = "できる" if z["searchable"] else f"できない（{z['why']}）"
        L.append(f"| {_c(sname)} | {_c(z['id'])} | {_c(z['side'])} | {_c(z['label'])} | {_c(mark)} |")
    L.append("")
    n_ok = sum(1 for _, z in rows if z["searchable"])
    L.append(f"登録は {len(rows)} 本、そのうち いま調整できるのは {n_ok} 本です。")
    L.append("")

    L.append("## 入口の型")
    L.append("")
    L.append("共通の売買ループが持っている入口の種類です。ロジックはこの型を1つ選んで、値だけを変えます。")
    L.append("")
    L.append("| 型 | サイド | 何をする入口か |")
    L.append("|---|---|---|")
    for name, (side, fn) in parts.ENTRY_FNS.items():
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        L.append(f"| {_c(name)} | {_c(side)} | {_c(doc)} |")
    L.append("")

    L.append("## 確認の部品")
    L.append("")
    L.append("入口の条件に足せる2つ目・3つ目の条件です。**この一覧にあるものしか使えません。**")
    L.append("")
    L.append(f"- 上位足のモメンタムが過熱していないか（値が閾値 以下 のときだけ通す）： "
             f"{' ／ '.join(parts.HTF_PARTS)}")
    L.append(f"- ボラと出来高の床（値が閾値 以上 のときだけ通す）： {' ／ '.join(parts.VOL_PARTS)}")
    L.append("")
    L.append(f"合わせて {len(parts.HTF_PARTS) + len(parts.VOL_PARTS)} 個です。"
             "時間足も部品ごとに固定で、選べません。")
    L.append("")

    L.append("## 出口の仕組み")
    L.append("")
    L.append("どのロジックも出口の部品は共通です。新しい出口の軸は作りません。")
    L.append("")
    L.append("| 値 | 何の値か | 実体に書かれている説明 |")
    L.append("|---|---|---|")
    for ln in (parts.generic_logic_loop.__doc__ or "").strip().split("\n"):
        s = ln.strip()
        if "…" not in s:
            continue
        name, _, rest = s.partition("…")
        name = name.strip()
        L.append(f"| {_c(name)} | {_c(_param_jp(name))} | {_c(rest)} |")
    L.append("")
    # ★この順番の文は 2026-07-30 に実装（e38_logic_parts.generic_logic_loop の出口ループ）と突き合わせて訂正した。
    #   それまで「損切り → 利確1 → 利確2 → 建値待ち → 時間切れ」と手書きされていて、実装と食い違っていた
    #   （機械生成の文書に手書きの主張が混ざる欠陥＝CP2 監査 4-23 と同族・歩0 で発見）。
    #   R13 で順番はデータになり探索と PDCA の対象になる＝そうなったらこの固定文はデータからの生成に置き換える。
    L.append("決済の見にいく順番は、いまの実装では 時間切れ → 損切り → 1段目の利確 → 2段目の利確 です。")
    L.append("建値待ち中の玉は 損切り → 建値 → 期限切れ の順に見ます。")
    L.append("同じバーで時間切れと損切りが両方成立した玉は、時間切れとして決済されます。")
    L.append("この順番は固定の設計ではありません。要件 R13 で枝のリストのデータになり、探索と PDCA で調整できるようにします。")
    L.append("建てたバーの次のバーから見にいきます。")
    L.append("")

    L.append("## 探索する値（e38 の場合）")
    L.append("")
    L.append("設定ファイル e38_logics.json の宣言から取っています。実行時に画面へも同じ範囲が印字されます。")
    L.append("戦略が増えたら、その戦略の接続ファイルが持つ宣言に置き換わります。")
    L.append("")
    L.append("### 出口の値（全ロジック共通）")
    L.append("")
    L.append("| 値 | 何の値か | どう決めるか |")
    L.append("|---|---|---|")
    for n, jp, how in _space_rows(cfg["search_space"]["common_exit"]):
        L.append(f"| {_c(n)} | {_c(jp)} | {_c(how)} |")
    L.append("")
    note = cfg["search_space"].get("_common_exit_note")
    if note:
        L.append(f"> {note}")
        L.append("")

    for lid, sp in cfg["search_space"]["logics"].items():
        L.append(f"### 入口の値（{lid}）")
        L.append("")
        L.append("| 値 | 何の値か | どう決めるか |")
        L.append("|---|---|---|")
        for n, jp, how in _space_rows(sp):
            L.append(f"| {_c(n)} | {_c(jp)} | {_c(how)} |")
        L.append("")

    L.append("## 1回の試行で起きること")
    L.append("")
    L.append("```")
    L.append("1. 探索器が値を1組えらぶ")
    L.append("2. その値で売買エンジンを最初から回す（値決め窓の全期間）")
    L.append("3. 出てきた売買記録を score.py にかけて純益を出す")
    L.append("4. 件数の下限を下回っていたら、その試行を捨てる")
    L.append("5. 純益が一番大きい組を覚えておく")
    L.append("```")
    L.append("")
    L.append("**採点は score.py をそのまま呼んでいます。** 手数料・funding・約定のしかたは審判の式のままです。")
    L.append("探索器は純益の計算に手を触れません。")
    L.append("")

    L.append("## 1試行にかかる時間")
    L.append("")
    L.append("**engine_tuner が走るたびに実測して記録した値です。この説明書に秒数を手で書きません。**")
    L.append(f"記録の置き場所は `{es.TIMING.name}` です。")
    L.append("")
    tm = _timing()
    if tm:
        L.append("| 戦略とロジック | データの読み込み | 1試行 | 何試行で測ったか | 測った日 |")
        L.append("|---|---|---|---|---|")
        for k in sorted(tm):
            r = tm[k]
            L.append(f"| {_c(k)} | {_c(r.get('load_sec'))}秒 | **{_c(r.get('per_trial_sec'))}秒** | "
                     f"{_c(r.get('trials'))}回 | {_c(r.get('measured_at'))} |")
        L.append("")
        L.append("読み込みの時間は試行の回数によらず毎回かかります。短い探索ではここが大半を占めます。")
    else:
        L.append("**未計測です。** engine_tuner を1回走らせると記録されます。")
    L.append("")
    L.append("> 2026-07-27 まで、ここには「実測でおよそ7秒」と手で書かれていました。")
    L.append("> それは別の道具 engine_search_e37.py の値で、engine_tuner の値ではありませんでした。")
    L.append("> 監査で発覚し、実測を機械で残す形に変えました。")
    L.append("")

    L.append("## 触れている指標の範囲")
    L.append("")
    size = es.catalog_size()
    if size:
        L.append(f"指標の作り方の正本は observe_diag です。カタログは **{size[0]}種 × 足 {size[1]}種 = "
                 f"{size[0] * size[1]}列** あります。そのうち、この道具が入口の条件に使える列は次の本数だけです。")
    else:
        L.append("指標カタログを読めませんでした。分母を出せません。")
    L.append("")
    rows_cov = _coverage_rows()
    if rows_cov:
        L.append("| 戦略 | ロジック | 触れる列 | カタログ全体に対する割合 |")
        L.append("|---|---|---|---|")
        for s, lid, n, pct in rows_cov:
            L.append(f"| {_c(s)} | {_c(lid)} | {n}本 | **{_c(pct)}** |")
        L.append("")
    L.append("**残りは落としたのではありません。候補にそもそも入っていません。**")
    L.append("これを広げるのが要件 R3 です。R3 はまだ終わっていません。")
    L.append("")

    L.append("## 件数の下限ゲート")
    L.append("")
    L.append("| ロジック | 1日あたりの下限 |")
    L.append("|---|---|")
    for lg in logics:
        v = lg.get("params", {}).get("search_min_per_day")
        L.append(f"| {_c(lg['id'])} | {_c(v) if v is not None else 'なし（値はまこさんが決める）'} |")
    L.append("")
    L.append("下限を下回った試行は捨てます。ほとんど建てずに損を減らすだけの形へ逃げ込むのを防ぐためです。")
    L.append("")

    L.append("## この道具が守ると言っていること")
    L.append("")
    L.append("実行の前に機械で検査し、1つでも崩れていれば止まります。")
    L.append("")
    for g in _guards():
        L.append(f"- {g}")
    L.append("")

    L.append("## observe_diag との違い")
    L.append("")
    L.append("どちらも条件を探します。評価のしかたが根本的に違います。")
    L.append("")
    L.append("| | engine_tuner | observe_diag |")
    L.append("|---|---|---|")
    for a, b, c in DIFF_ROWS:
        L.append(f"| {a} | {c} | {b} |")
    L.append("")
    L.append("engine_tuner は、条件を変えるたびに売買エンジンを最初から回し直します。")
    L.append("だから玉の集合そのものが変わります。同じ枠を別の玉が取り合う動きも入ります。")
    L.append("observe_diag は、既にある玉や場面のバーに条件を当てはめて数えるだけです。玉は増えません。")
    L.append("")

    L.append("## 使う順番（まこさん確定 2026-07-27・正本は engine_tuner.py の説明文）")
    L.append("")
    L.append("```")
    for ln in _doc_block("使う順番"):
        L.append(ln)
    L.append("```")
    L.append("")

    L.append("## いまできないこと")
    L.append("")
    L.append("要件定義を決めるための材料です。すべて上の表から出た事実です。")
    L.append("")
    ng = [(s, z) for s, z in rows if not z["searchable"]]
    if ng:
        L.append(f"- 登録 {len(rows)} 本のうち {len(ng)} 本が調整できません： "
                 + " ／ ".join(f"{z['id']}（{z['why']}）" for _, z in ng))
    L.append(f"- 接続ファイルは {len(_adapters())} 枚（{', '.join(available())}）です。"
             "これ以外の戦略は渡せません。どの戦略を対象にするかは要件定義書 engine_tuner_requirements.md の"
             "「この道具でやらないこと」を見てください（E36 は対象外と決まっています）。")
    L.append(f"- 入口に足せる確認の部品は {len(parts.HTF_PARTS) + len(parts.VOL_PARTS)} 個だけです。"
             "指標も時間足も、この一覧の外は試せません。")
    if size and rows_cov:
        worst = max(rows_cov, key=lambda z: z[2])
        L.append(f"- 指標カタログ {size[0] * size[1]}列 のうち、いちばん広いロジックでも触れているのは "
                 f"{worst[2]}本（{worst[3]}）です。**残りは試していません。**")
    L.append("- 局面の判定はレンジに固定です。共通の売買ループが range_ok_rg5 を前提にしています。")
    L.append("- 保有の上限の候補は分単位に固定です。デイトレの時間単位を試せません。")
    L.append("- 調整の単位はロジック1本です。**戦略まるごと**（複数のロジック＋優先度＋枠の配分）を"
             "一度に調整することはできません。ロジック単体で最善にしても、"
             "他のロジックと同じ予算を取り合うと全体では変わります。")
    L.append("")

    L.append("## この道具では分からないこと")
    L.append("")
    L.append("- 採否は決められません。採否は score.py を採点窓に通して、まこさんが決めます。")
    L.append("- 値決め窓と確認窓の成績は、採点窓の成績を約束しません。")
    L.append("- 建てなかった場面のことは分かりません。建てた玉の結果しか見ていません。")
    L.append("")

    body = "\n".join(L).rstrip() + "\n"
    return f"<!-- MANUAL_HASH={_sha(body)} -->\n{body}"


def verify() -> int:
    if not OUT.exists():
        print(f"❌ 説明書が無い: {OUT}")
        return 1
    txt = OUT.read_text(encoding="utf-8")
    head, _, body = txt.partition("\n")
    want = head.replace("<!-- MANUAL_HASH=", "").replace(" -->", "").strip()
    got = _sha(body)
    if want != got:
        print(f"❌ 手書きで書き換えられている（ハッシュ不一致 期待 {want} / 実際 {got}）")
        return 1
    print(f"✅ 改変なし（ハッシュ {got}）")
    return 0


def selftest() -> int:
    ng = []
    cfg = _cfg()
    if not hasattr(es, "build_parser"):
        ng.append("engine_tuner に引数定義の関数が無い＝実行のしかたを実体から取れない")
    if not _args_rows():
        ng.append("引数の一覧が実体から取れていない")
    if len(_guards()) < 5:
        ng.append(f"実行を止める条件が実体から取れていない（{len(_guards())}件しか拾えない）")
    if len(parts.ENTRY_FNS) < 3:
        ng.append("入口の型が実体から取れていない")
    if not cfg.get("logics") or not cfg.get("search_space"):
        ng.append("設定ファイルからロジックと探索範囲が取れていない")
    if len(DIFF_ROWS) < 5:
        ng.append("observe_diag との違いの表が足りない（混同したまま使われる）")
    # 窓の定数が実体から取れていること（説明書に日付を手打ちしない）
    for a in ("SEARCH_START", "SEARCH_END", "CONFIRM_START", "CONFIRM_END", "WARM"):
        if not hasattr(es, a):
            ng.append(f"窓の定数が実体に無い: {a}")
    # 目的（まこさん確定 2026-07-27）が実体から取れて説明書に載ること＝この道具の存在理由が消えない
    pur = _doc_block("この道具の目的")
    if len(pur) < 2:
        ng.append("説明文に『この道具の目的』が無い（何のための道具かが正本に書かれていない）")
    for need in ("組み合わせロジックを見つけ", "改善すべき点を見つけ", "利益最大化、損失最小化するまで調整する"):
        if not any(need in x for x in pur):
            ng.append(f"目的の逐語が欠けている: {need}")
    # 使う順番（まこさん確定 2026-07-27）＝どの道具をどの順で使うかが正本に残ること
    order = _doc_block("使う順番")
    if len(order) < 4:
        ng.append("説明文に『使う順番』が無い（どの道具をどの順で使うかが正本に書かれていない）")
    for need in ("observe_diag で診断", "型を選ぶ", "順位づけと候補選びはしない"):
        if not any(need in x for x in order):
            ng.append(f"使う順番の逐語が欠けている: {need}")
    # 接続ファイル（要件 R4）が実体から取れて、必要なものが揃っていること
    ads = _adapters()
    if not ads:
        ng.append("接続ファイルが1枚も無い（tuner_adapters/ が空）")
    for ad in ads:
        for k in ("NAME", "LABEL", "logics", "space", "run"):
            if not hasattr(ad, k):
                ng.append(f"接続ファイル {ad} に {k} が無い")
    if not _all_logics():
        ng.append("ロジックの一覧が接続ファイルから取れていない")
    # ★所要時間と網羅度は実体から取ること（2026-07-27 まこさん OK・監査 提案1）
    #   ＝手書きの秒数が生成器へ戻ってくるのを止める番人。
    src_gen = inspect.getsource(sys.modules[__name__])
    for w, d in GLOSSARY:
        if "秒かかる" in d or "秒です" in d:
            ng.append(f"言葉の説明に所要時間が手書きされている: {w}（実測は engine_tuner_timing.json から読む）")
    if "engine_tuner_timing" not in src_gen and "es.TIMING" not in src_gen:
        ng.append("所要時間の記録ファイルを読んでいない（説明書の秒数が手書きになる）")
    if es.catalog_size() is None:
        ng.append("指標カタログの大きさを observe_diag から取れない（網羅度の分母が出せない）")
    if not _coverage_rows():
        ng.append("触れる列の一覧を接続ファイルから取れない（網羅度の分子が出せない）")
    txt = build()
    for must in ("この説明書の位置づけ", "この道具は何か", "この道具の目的", "言葉の説明", "実行のしかた", "使う期間",
                 "扱える戦略", "調整できるロジック", "入口の型", "確認の部品", "出口の仕組み", "探索する値",
                 "1回の試行で起きること", "1試行にかかる時間", "触れている指標の範囲",
                 "件数の下限ゲート", "この道具が守ると言っていること",
                 "observe_diag との違い", "使う順番", "いまできないこと", "この道具では分からないこと"):
        if must not in txt:
            ng.append(f"説明書に見出しが無い: {must}")
    for w, _ in GLOSSARY:
        if w not in txt:
            ng.append(f"言葉の説明が説明書に出ていない: {w}")
    # パラメータの日本語が全部そろっていること（名前だけでは何の値か分からない）
    allsp = dict(cfg["search_space"]["common_exit"])
    for sp in cfg["search_space"]["logics"].values():
        allsp.update(sp)
    miss = [k for k in allsp if not _param_jp(k)]
    if miss:
        ng.append(f"探索する値の説明が未登録: {miss}（PARAM_JP に足す）")
    # 番人＝実体を差し替えたら生成物も変わること（＝実体から取っている証拠）
    keep = dict(parts.ENTRY_FNS)
    try:
        parts.ENTRY_FNS["番人用のダミー"] = ("SHORT", lambda *a: False)
        if "番人用のダミー" not in build():
            ng.append("入口の型が実体を見ていない（コードを変えても説明書が変わらない）")
    finally:
        parts.ENTRY_FNS.clear()
        parts.ENTRY_FNS.update(keep)
    rows = _all_logics()
    n_ok = sum(1 for _, z in rows if z["searchable"])
    print("=" * 80)
    print("gen_engine_tuner_manual 自己検査")
    print("=" * 80)
    print(f"  接続ファイル {len(_adapters())} 枚（{', '.join(available())}）")
    print(f"  登録ロジック {len(rows)} 本 / いま調整できる {n_ok} 本")
    print(f"  入口の型 {len(parts.ENTRY_FNS)} 種 / 確認の部品 {len(parts.HTF_PARTS) + len(parts.VOL_PARTS)} 個")
    print(f"  引数 {len(_args_rows())} 個 / 実行を止める条件 {len(_guards())} 件")
    print(f"  出力先 {OUT}")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="engine_tuner の取扱説明書を機械生成する")
    ap.add_argument("--write", action="store_true", help="生成して書き出す")
    ap.add_argument("--verify", action="store_true", help="手書き改変の検出")
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
        print(f"✅ 書き出した: {OUT}（{len(txt.splitlines())}行）")
    else:
        print(txt)


if __name__ == "__main__":
    main()
