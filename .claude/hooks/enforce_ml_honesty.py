#!/usr/bin/env python3
# enforce_ml_honesty.py — PreToolUse on Write|Edit（2026-07-13 まこさん指示「機械学習の不正=疑似MLのインチキ設計を徹底的に防げ」）
#
# 前身 enforce_optimization_honesty は「Optuna があれば本物の最適化として通す」欠陥があった（まこさん指摘 2026-07-13）。
# ＝Optuna は ML の妥協版にすぎず、しかも教師・学習内容が壊れていても通った＝また矮小化を許す欠陥品だった。
# 本 hook は Optuna 中心の判定を排除し、「機械学習(ML)を名乗る設計が、目的に対して 学習方法・学習内容・教師 が
# 不適切/不完全な"疑似ML"になっていないか」を弾くことに純化する。
#
# 背景（CC が42 iter やった疑似ML/インチキの型）:
#   P1 目的↔教師のズレ  : 目的は「レンジ天井→下限を取る」なのに教師は「約定した分の net」だけ＝取り逃し(7/18)を見ない。
#   P2 ML が飾り(疑似ML): LightGBM 等を置くが実際は「場面を箱に割る/勝ち負け二値」の脇役で、入口/出口のルール構造は手書き。
#   P3 疑似最適化の詐称 : 実体は手置きメニューの greedy なのに「機械学習で学習/最適化」と呼ぶ。
#   P4 教師の leak     : 教師ラベルが未来参照(shift(-)/MFE/期間全体)＝本番再現不可(H2/類型A)を明記していない。
#
# 何を物理強制するか: acceptance/improvement_plan/*_design を書く瞬間、機械学習を名乗るなら宣言ブロック ML_DECL
#   （目的/教師/学習内容/学習方法/自己申告 の5項目）を要求し、P0(宣言欠落)/P1/P2/P3/P4 を弾く。
#   ＝まこさんが宣言を読めば「目的に対して教師・学習内容・学習方法が適切/完全か」を ML 知見ゼロでも見える。
#
# 限界（正直に・隠さない）: これはテキスト検査。宣言に巧妙な嘘（教師を偽記＝実装は約定分 net なのに「取り逃しを含む」と書く）を
#   書けば doc 層では見抜けない（番人ケース h で実証）。→ ①非同型 Web Claude レビューで宣言↔実装を照合
#   ②DESIGN_CONTRACT で「その ML の予測がレバー/入口の決定に実際に使われるか」を実行前にコード機械照合
#   ③まこさんの目、で補う。本 hook 単独で「本物の ML 設計」は保証しない＝「目的に対する教師/学習内容/学習方法の
#   正直な表示を強制し、構造的なインチキ(P0〜P4)を弾く」までを守る。

import sys, os, json, re

TARGETS = ("acceptance.md", "improvement_plan.md")  # ＋ *_design.md（下で判定）

# 機械学習(ML)を名乗る語（design 文書に在れば ML_DECL を要求）。「学習窓」(=検証期間)は除外。
CLAIM = re.compile(
    r'機械学習|ML最適化|ML選定|MLで|ML を|学習器|教師|ラベル|分類器|予測器|検出器'
    r'|LightGBM|lightgbm|決定木|メタラベリング|Triple ?Barrier|トリプルバリア|学習して|学習で選|学習で最適'
)
# ML を使わない明言（あれば発火しない＝素ルール設計を邪魔しない）
NO_ML = re.compile(r'ML *不使用|機械学習.{0,3}使わ|機械学習.{0,3}不使用|ML *なし|ML *は使わ')

# 手置き系（学習方法/自己申告に在れば「本物のML/最適化」ではない＝疑似）
HANDMENU = re.compile(r'greedy|グリーディ|手置き|手書き|メニュー|逐次|固定候補|決め打ち|総当たり|疑似ML|疑似 ?ml')

# 取り逃し(機会損失)を教師が見ている証拠語
OPP = re.compile(r'取り逃し|機会損失|取れていない|取れなかった|未約定|理想トレード|正解トレード|取るべき|見送り')
# 教師が「約定した分だけ」を示す語
EXECUTED_ONLY = re.compile(r'約定した|約定分|net *[>＞]? *0|勝ち負け|二値|実行した取引|net合計|約定のみ|約定イベント')
# 学習内容が「脇役ML(飾り)」を示す語
SIDE_ML = re.compile(r'場面.{0,2}分割|箱に割|セルに割|場面セル|二値分類|勝ち負け.{0,2}分類|クラスタ|過熱判定')
# 学習内容が「本体(入口/出口のルール構造)を ML が決める」証拠語
CORE_ML = re.compile(r'入口.{0,2}ルール|出口.{0,2}ルール|発火条件|エントリー条件|ルール構造|建てる条件|天井|下限|入口を学|出口を学|入口を予測|決定を学|方策|policy')
# 教師の leak 対策の明記
LEAK_OK = re.compile(r'未来参照.{0,2}(なし|無|ゼロ)|leak.{0,2}(なし|無)|因果|t時点|過去のみ|shift\(1\)|確定済')
# 「最適化/学習した」等の肯定的な達成表現（詐称チェック用）
AFFIRM_ML = re.compile(r'機械学習で.{0,4}(学習|最適化|選定)|MLで.{0,4}(学習|最適化|選定)|学習で最適化|最適化した|学習した|ML最適化')

# 否定文脈で ML/最適化 を語る許容フレーズ（詐称チェック前に除去）
NEG_PHRASES = [
    "最適化ではない", "最適化でない", "最適化と呼ばない", "最適化に達していない", "最適化の矮小化",
    "最適化詐欺", "学習ではない", "本物の最適化ではない", "本物のMLではない", "機械学習ではない",
    "疑似ML", "飾り", "本来の用途でない", "矮小化",
]

ML_KEYS = ["目的", "教師", "学習内容", "学習方法", "自己申告"]


def get_content(ti):
    fp = ti.get("file_path", "")
    c = ti.get("content")
    if c is None:
        old = ti.get("old_string")
        new = ti.get("new_string") or ""
        try:
            cur = open(fp).read()
        except Exception:
            cur = ""
        c = cur.replace(old, new) if old else (cur + new)
    return c or ""


def field(block, name):
    mm = re.search(re.escape(name) + r'\s*[:：]\s*(.+)', block)
    return (mm.group(1).strip() if mm else "")


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if d.get("agent_type"):
        sys.exit(0)
    ti = d.get("tool_input", {}) or {}
    fp = ti.get("file_path", "") or ""
    base = os.path.basename(fp)
    if not ((base in TARGETS) or base.endswith("_design.md")):
        sys.exit(0)

    content = get_content(ti)
    if not content:
        sys.exit(0)
    if not CLAIM.search(content):
        sys.exit(0)  # 機械学習を名乗っていない＝対象外
    if NO_ML.search(content):
        sys.exit(0)  # ML 不使用の素ルール設計＝邪魔しない

    viol = []

    m = re.search(r'<!--\s*ML_DECL(.*?)-->', content, re.S)
    if not m:
        viol.append(
            "[P0 宣言なし] 機械学習(ML/教師/分類器/LightGBM 等)を名乗るなら、正直な宣言ブロックが必須です。\n"
            "  次を本文に入れてください（5項目すべて・目的に対して 学習方法/学習内容/教師 が適切かをまこさんが判別できる形）:\n"
            "  <!-- ML_DECL\n"
            "  目的: (この設計で学ばせたい挙動＝§1.2.1 の指示トレード 例 レンジの戻り天井で入り下限で取る)\n"
            "  教師: (ラベルの定義。①約定した分だけか/取り逃し[機会損失]を含むか ②未来参照[leak]なしを明記 ③目的と一致するか)\n"
            "  学習内容: (予測器が学ぶのは何か＝入口/出口のルール構造か、それとも場面分割/勝ち負け二値だけか)\n"
            "  学習方法: (実体。MLの予測がレバー/入口の決定に実際に使われるか＝飾りでないか。手置きgreedyなら正直にそう書く)\n"
            "  自己申告: (本物のML設計 / 疑似ML[手書きルール＋飾りのML])\n"
            "  -->"
        )
        emit(viol)
        return

    block = m.group(1)
    missing = [k for k in ML_KEYS if not re.search(re.escape(k) + r'\s*[:：]', block)]
    if missing:
        viol.append("[P0 宣言 不完全] ML_DECL に必須項目が欠けています: " + " / ".join(missing))

    purpose = field(block, "目的")
    teacher = field(block, "教師")
    learn = field(block, "学習内容")
    method = field(block, "学習方法")
    selfdecl = field(block, "自己申告")

    # P1: 目的↔教師のズレ（教師が取り逃しを見ない＝目的に届かない）
    if teacher:
        if EXECUTED_ONLY.search(teacher) and not OPP.search(teacher):
            viol.append(
                "[P1 目的↔教師のズレ] 教師が「約定した分だけ(net>0 等)」で、取り逃し(機会損失)を見ていません。\n"
                "  目的が「今取れていないレンジ/挙動を取る」なら、取れていないバーは教師にゼロで現れ、学習は"
                "『取れ』と言えません（7/18 が取れない42 iter の根＝2026-07-13 診断）。\n"
                "  教師に取り逃し(未約定/理想トレード/機会損失)を含めるか、含めないなら「目的は取り逃しを含まない」と目的側で明記。"
            )
        elif OPP.search(purpose) and not OPP.search(teacher):
            viol.append(
                "[P1 目的↔教師のズレ] 目的に「取り逃し/取るべき挙動」があるのに、教師にそれを教える項がありません。\n"
                "  目的で取ると言った挙動を、教師(ラベル)が正解として持っていないと学習できません。"
            )

    # P2: ML が飾り（疑似ML）＝学習内容が脇役だけで本体は手書き、なのに「本物」自称
    if learn and SIDE_ML.search(learn) and not CORE_ML.search(learn):
        if re.search(r'本物', selfdecl) or not HANDMENU.search(selfdecl):
            viol.append(
                "[P2 ML が飾り(疑似ML)] 学習内容が「場面分割/勝ち負け二値」等の脇役だけで、入口/出口のルール構造を"
                "ML が学んでいません（本体は手書きルール）。これで『本物のML設計』を名乗るのは疑似MLです。\n"
                "  ML に本体(入口/出口の発火・ルール)を決めさせるか、脇役なら自己申告を「疑似ML(手書き＋飾りのML)」に正す。"
            )

    # P3: 疑似最適化/学習の詐称（手置きgreedy なのに「機械学習で学習/最適化」と肯定）
    is_fake = bool(HANDMENU.search(method) or HANDMENU.search(selfdecl))
    if is_fake:
        scan = content.replace(m.group(0), "")
        for p in NEG_PHRASES:
            scan = scan.replace(p, "")
        if AFFIRM_ML.search(scan):
            viol.append(
                "[P3 疑似最適化の詐称] 学習方法/自己申告が「手置きメニューの greedy＝疑似」なのに、本文で"
                "「機械学習で学習/最適化した」と肯定しています。\n"
                "  greedy・手置きを『機械学習/最適化』と呼ばないでください（正直な表記＝手置き候補の逐次選定・本物のMLではない）。"
            )

    # P4: 教師の leak 未対策（未来参照なしの明記が無い）
    if teacher and not LEAK_OK.search(teacher):
        viol.append(
            "[P4 教師の leak 未対策] 教師(ラベル)に「未来参照なし/leak なし/因果/t時点/過去のみ」の明記がありません。\n"
            "  教師ラベルが未来参照(shift(-)/MFE/期間全体)だと本番で再現不可(H2/類型A)＝虚偽達成の温床。教師の因果性を明記。"
        )

    emit(viol)


def emit(viol):
    if viol:
        sys.stderr.write("🔒 [機械学習 正直ゲート] 疑似ML/インチキ設計の防止（まこさん 2026-07-13「目的に対し 学習方法/学習内容/教師 が不適切・不完全なら弾く」）\n")
        for v in viol:
            sys.stderr.write(v + "\n")
        sys.stderr.write(
            "  → 趣旨: 目的(§1.2.1 指示トレード)に対して 学習方法・学習内容・教師 が適切/完全かを、まこさんが ML 知見ゼロでも宣言で見える状態にする。\n"
            "     限界: テキスト検査＝宣言に嘘を書けばすり抜ける（番人で実証）→ 非同型 Web レビュー＋DESIGN_CONTRACT コード照合＋まこさんの目で補う。\n"
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
