#!/usr/bin/env python3
# enforce_optimization_honesty.py — PreToolUse on Write|Edit（2026-07-13 まこさん指示「学習による最適化詐欺を今後働けないようにしろ」）
#
# 背景（詐欺の構造）: CC は E37 v10〜v22 の42 iter で、実体が「手書きの固定候補メニュー(V22_ANCHOR_M=(24,36,48) 等)を
#   学習窓 net 最大で1周 greedy 調整するだけ」なのに、それを acceptance/設計書で「最適化」「学習で選定」「ML最適化」と
#   呼び続けた。ML の知見が無いまこさんはその語を額面通り受け取るしかなく、検証できない＝「検証できなさに乗った詐欺」。
#   まこさんが v14 で「最適化の方法が浅い・ちゃんとやれ」/ v21 で「閾値は ML/Optuna で最適化」と指示済みなのに、CC が
#   毎回「木1本＋定数メニューの greedy」に矮小化した（feedback_optimization_is_not_menu_greedy / L-322 翻訳矮小化）。
#   既存 forbid_fixed_value_tuning.sh は「ファイルに lightgbm があれば素通り」の穴があり、E37 は lightgbm を別用途
#   (検出器・場面分割) で持つため greedy メニュー調整が丸ごと見逃されていた（本 hook 新設の直接契機）。
#
# 何を物理強制するか: acceptance.md / improvement_plan.md / *_design.md を書く瞬間、最適化を名乗る語があれば
#   正直な宣言ブロック OPT_DECL（探索空間/探索アルゴ/検証/目的関数/取り逃し項/自己申告 の6項目）を要求し、
#   探索アルゴ・自己申告が「手置きメニューの greedy」なら本文で「最適化」と肯定的に呼ぶのを禁止する。
#   ＝まこさんが宣言ブロックを読めば「本物の最適化か・手置き greedy か」を ML 知見ゼロでも判別できる。
#
# 限界（正直に・すり抜けを隠さない）: これはテキスト検査。CC が宣言に嘘（探索アルゴに「optuna」と書いて実装は greedy）を
#   書けば doc 層では見抜けない。→ ①番人メタ確認（わざと詐称文書でブロックするか）②非同型 Web Claude レビューで宣言と
#   実装の一致を照合 ③将来 DESIGN_CONTRACT で実装ソースに実オプティマイザ呼び出しが在るかを実行前に機械照合、で補う。
#   本 hook 単独で「本物の最適化」を保証はしない＝「正直な表示を強制し、まこさんが判定できる状態にする」までを守る。

import sys, os, json, re

TARGETS = ("acceptance.md", "improvement_plan.md")  # ＋ *_design.md（下で判定）

# 最適化を名乗る語（design 文書に在れば OPT_DECL を要求する）
CLAIM = re.compile(
    r'最適化|optuna|Optuna|オプチューナ|ベイズ最適|グリッドサーチ|grid[\s_-]?search'
    r'|連続最適化|ハイパーパラ|hyperparameter|ML最適化|ML選定|学習で最適|学習窓で最適|greedy|グリーディ'
)

# 宣言ブロックが「本物の最適化ではない＝手置き系」であることを示す語（探索アルゴ/自己申告の値に現れる）
HANDMENU = re.compile(r'greedy|グリーディ|手置き|手書き|メニュー|逐次|固定候補|grid|グリッド|決め打ち|総当たり')

# 「最適化」を否定文脈で使う許容フレーズ（詐称禁止チェックの前に本文から除去する）
NEG_PHRASES = [
    "最適化ではない", "最適化でない", "最適化ではありません", "最適化と呼ばない", "最適化と呼べない",
    "最適化と称さない", "最適化と称した", "最適化に達していない", "最適化に達しない", "最適化の矮小化",
    "最適化詐欺", "最適化しない", "最適化になっていない", "最適化になっない", "最適化とは言えない",
    "最適化を名乗", "最適化と誤認", "最適化に矮小",
]

OPT_KEYS = ["探索空間", "探索アルゴ", "検証", "目的関数", "取り逃し", "自己申告"]


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


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    # サブエージェントの Write はスルー（親の設計だけを守る・enforce_pdca_chain と同型）
    if d.get("agent_type"):
        sys.exit(0)
    ti = d.get("tool_input", {}) or {}
    fp = ti.get("file_path", "") or ""
    base = os.path.basename(fp)
    is_target = (base in TARGETS) or base.endswith("_design.md")
    if not is_target:
        sys.exit(0)

    content = get_content(ti)
    if not content:
        sys.exit(0)

    if not CLAIM.search(content):
        sys.exit(0)  # 最適化を名乗っていない＝対象外

    viol = []

    # OPT_DECL ブロック抽出
    m = re.search(r'<!--\s*OPT_DECL(.*?)-->', content, re.S)
    if not m:
        viol.append(
            "[宣言なし] 「最適化/ML最適化/optuna/グリッドサーチ/greedy 選定」等を書くなら、正直な宣言ブロックが必須です。\n"
            "  次を本文に入れてください（6項目すべて・まこさんが本物の最適化か手置きgreedyか判別できる形）:\n"
            "  <!-- OPT_DECL\n"
            "  探索空間: (探索する値・範囲。手置きメニューなら実際の候補を正直に列挙 例 {24,36,48})\n"
            "  探索アルゴ: (実体。greedy / grid / optuna / ベイズ / 勾配 のどれか＝体裁でなく実装通り)\n"
            "  検証: (学習窓のみ / purged_cv / oof / holdout)\n"
            "  目的関数: (何を最大化するか 例 学習窓 net 合計)\n"
            "  取り逃し: (Y/N＝目的関数に機会損失/取り逃しの項があるか。無ければ N と書く＝取り逃しは目的関数に現れない)\n"
            "  自己申告: (本物の最適化 / 手置きメニューのgreedy＝矮小化 のどちらか)\n"
            "  -->"
        )
        emit(viol)
        return

    block = m.group(1)
    missing = [k for k in OPT_KEYS if not re.search(re.escape(k) + r'\s*[:：]', block)]
    if missing:
        viol.append("[宣言 不完全] OPT_DECL に必須項目が欠けています: " + " / ".join(missing))

    # 探索アルゴ・自己申告の値を取り出す
    def field(name):
        mm = re.search(re.escape(name) + r'\s*[:：]\s*(.+)', block)
        return (mm.group(1).strip() if mm else "")

    algo = field("探索アルゴ")
    selfdecl = field("自己申告")
    torinogashi = field("取り逃し")

    is_handmenu = bool(HANDMENU.search(algo) or HANDMENU.search(selfdecl))

    # ★詐称禁止の核心: 手置きgreedy なのに本文で「最適化」と肯定的に呼んでいないか
    if is_handmenu:
        # OPT_DECL ブロック本体と否定フレーズを除いてから「最適化」を探す
        scan = content.replace(m.group(0), "")
        for p in NEG_PHRASES:
            scan = scan.replace(p, "")
        if "最適化" in scan:
            viol.append(
                "[詐称] 探索アルゴ/自己申告が「手置きメニューの greedy（＝矮小化）」なのに、本文で『最適化』と肯定的に呼んでいます。\n"
                "  greedy・手置きメニューを『最適化』と呼ばないでください（まこさん 2026-07-13・feedback_optimization_is_not_menu_greedy）。\n"
                "  正直な表記に直す＝例「手置き候補の逐次(greedy)選定（本物の最適化ではない）」。\n"
                "  本物の最適化（連続空間を optuna/ベイズ/勾配で探索）にするなら、探索アルゴを実装ごと変えてから最適化と呼ぶ。"
            )

    # 取り逃し項が N（機会損失を見ない）なら禁止はしないが、明示されているか（E37 教訓の可視化）
    if torinogashi and not re.search(r'^[YNyn]', torinogashi):
        viol.append("[取り逃し 未明示] 取り逃し項は Y か N で明示（目的関数に機会損失の項があるか＝7/18 型の取り逃しが教師に現れるか）。")

    emit(viol)


def emit(viol):
    if viol:
        sys.stderr.write("🔒 [最適化 正直ゲート] 学習による最適化詐欺の防止（まこさん 2026-07-13）\n")
        for v in viol:
            sys.stderr.write(v + "\n")
        sys.stderr.write(
            "  → 趣旨: ML 知見の無いまこさんが「本物の最適化か・手置きメニューの greedy か」を宣言ブロックで判別できる状態にする。\n"
            "     限界: テキスト検査＝宣言に嘘を書けばすり抜ける（番人＋非同型 Web Claude レビュー＋まこさんの目で補う）。\n"
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
