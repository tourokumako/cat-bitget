#!/usr/bin/env python3
# enforce_purpose_gate.py — 目的ゲートの判定の本体
#   （2026-08-06 新設 → 2026-08-26 に作り直し・まこさん承認 7c80f0891bb553d0…・safety hook）
#
# ★まこさんの逐語（2026-08-06）
#   「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、
#     見つけることができる機械を作ることが目的」
#   「上記目的に即していないもの以外は作らないこと」
#   「つまりは上記条件を一つでも達成できていないものは作成してはいけないということ。」
#   「そのために強制hookを作ることはOK」
#
# ★2026-08-26 の作り直しで直したこと（設計書＝.claude/state/acceptance.md・やること1〜6）
#   1. 宣言の型を「目的2つ ＋ 条件4つ」に直した。
#      2026-08-06 に まこさんが3回 指摘した中身を、そのまま形にした（worklog 20260806 §9）。
#        ①「net 利益を最大化する」と「見つけることができる」は【条件】ではなく【目的】。
#           逐語＝「この条件が違う」。
#        ②「◯◯を組み合わせられるか」という問い方をやめる。
#           逐語＝「組み合わせることが目的ではないって言ったよね」＝目的は見つけること。
#           だから問いは「探して見つけられるか」にする。
#        ③「時間」は Entry の【時間足】を指す。
#           逐語＝「それ以外の保有時間はExit側のロジックだし、時間帯はまた別のジャンルの条件だよね」。
#   2. 通し道（合言葉と同じ働き）を消した。
#      直す前は、コマンドの文字列に purpose_check が入っていれば、その先を見ずに通していた
#      （引用符の中も見るので、文字列を1つ足すだけで外れた）。恒久の決まり57番の消し残し。
#   3. 宣言が 24時間 より古ければ止める（直す前は、1回 書けば以後ずっと通った）。
#   4. 宣言の「対象」に、いま触るファイルの名前が無ければ止める
#      （直す前は、前の作業の宣言のまま違うファイルを触れた）。
#   5. 設計書は「中身に engine_tuner の文字が在るとき」だけ止める。
#      ★この判定はプログラムが中身を読んで決める。CC の申告にはしない。
#      なぜ＝関わりのない設計書で「非該当」を書き流す癖がつくのを避ける
#      （まこさん指摘 2026-08-26・acceptance_checklist.md「★項目の群」と同じ理由）。
#      ★engine_tuner のコードそのものは、中身に関わらず必ず止める。
#
# 何を止めるか
#   ① Write/Edit/MultiEdit で engine_tuner*.py を書く／直す        … 中身に関わらず必ず
#   ② Write/Edit/MultiEdit で acceptance.md ／ *_design.md を書く  … 中身に engine_tuner が在るときだけ
#   ③ Bash で engine_tuner*.py を python 実行する
#        除外＝--selftest ／ --verify ／ --identity ／ --help ／ py_compile ／ --dry-run
#        （--dry-run の除外の根拠＝engine_tuner_gen.py:3353 の逐語
#          「検収専用（selftest／--dry-run）＝採否・本走に使わない」）
#
# 何を通すか
#   宣言のファイル自身／サブエージェント／読むだけのコマンド／上記以外の全部。
#
# 解除: 無し（合言葉は 2026-08-16 に全廃＝まこさん指示「じゃあ強制解除できない状態にしろ」）。
#
# 限界（正直に書く）
#   ①宣言に「✅」と嘘を書けば通る＝中身の真偽はプログラムには分からない。最後の関所は まこさんの目。
#   ②この hook のファイル自体を書き換えれば無効にできる（git diff には必ず出る）。
#   ③e38_priority_stack.py（戦略の本体）は止める相手に入れていない＝この hook は engine_tuner のためのもの。
#
# 番人: python3 .claude/hooks/enforce_purpose_gate.py --selftest

import json
import os
import re
import sys
from datetime import datetime, timedelta

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
DECL = os.path.join(ROOT, ".claude", "state", "purpose_check.md")

MAX_AGE_HOURS = 24                                  # フロー宣言のチェックと同じ値にそろえた
MARK_MOKUTEKI = ("目的1", "目的2")                   # 目的（この機械が何のためにあるか）
MARK_JOKEN = ("条件1", "条件2", "条件3", "条件4")     # 条件（何を探すのか）

# ★2026-08-26（2回目の直し・まこさん指示「あとで直さず、今直してほしい」・承認 7d1f2a8f62cef2f9）
#   条件の行に書ける3つ目の印。「この変更は、その条件の探索に1バイトも触らない」の意味。
#   なぜ要るか＝印が ✅／❌ の2つしかないと、探索の経路に触れない設計（文書を作るプログラム・hook 等）でも、
#     当てはまらない問い4つに ✅ を書かせることになる＝中身を見ずに書き流す癖がつく。
#     まこさんの逐語（2026-08-26・acceptance_checklist.md:14）＝
#     「非該当を毎回13件 書いていると、中身を見ずに書き流す癖がつき、本当に該当する1件を見落とします。」
#   ★CC が自由には使えない＝探索の経路のファイルを触るときは、この印を書いても止める（下の touches_search_path）。
#   ★目的1・目的2 には使えない（目的はどんな変更にも当てはまるため）。
MARK_KAENAI = "変えない"

# 探索の経路のファイルの一覧＝H2 の印から読む（★手書きしない＝教訓 L-468）。
_H2_PASS = os.path.join(ROOT, ".claude", "state", "h2_pass.json")

_RE_PY = re.compile(r"python[0-9.]*\s")
_RE_SKIP = re.compile(r"--selftest|--verify|--identity|--help|py_compile|--dry-run")
_RE_TUNER_PY = re.compile(r"(engine_tuner[a-z_]*\.py)")
_RE_TUNER_NAME = re.compile(r"^engine_tuner[a-z_]*\.py$")

TEMPLATE = """  【目的の照合】
  対象: <いま書く／直す／走らせるファイルの名前>
  日付: <YYYY-MM-DD HH:MM・24時間以内>

  ■ 目的（2つ・この機械が何のためにあるか）
  目的1 net 利益を最大にする方向に働くか: ✅ ＋ 根拠1行
  目的2 見つける（探す）ことができるか: ✅ ＋ 根拠1行

  ■ 条件（4つ・何を探すのか＝まこさんの逐語「指標、閾値、時間、パラメータ」）
  条件1 指標を、探して見つけられるか: ✅ ＋ 根拠1行
  条件2 閾値を、探して見つけられるか: ✅ ＋ 根拠1行
  条件3 時間足を、探して見つけられるか: ✅ ＋ 根拠1行
      ★ここで書くのは Entry の時間足だけ。
        保有時間は Exit 側のロジック。時間帯は別のジャンルの条件（まこさん整理 2026-08-06）。
  条件4 パラメータ（指標を作るときの設定）を、範囲から探して見つけられるか: ✅ ＋ 根拠1行

  作ってはいけないものの一覧との照合: <一覧の1件ずつ・当たらないことを書く>
  ★入っていないもの: <明示・無ければ「なし」>

  ★条件の行に書ける印は3つ（2026-08-26）
    ✅       ＝ この変更で、その条件を探して見つけられる状態になる（または良くなる）
    ❌       ＝ 探して見つけられない。1つでも在れば止まる
    変えない ＝ この変更は、その条件の探索に1バイトも触らない（狭めも広げもしない）
  ★「変えない」を書けるのは、探索の経路のファイルを触らないときだけ。
    触るのに書くと止まる（判定はプログラム＝H2 の印 h2_pass.json の一覧で見る）。
  ★目的1・目的2 に「変えない」は使えない（目的はどんな変更にも当てはまるため）。"""


def strip_text(cmd):
    """引用符とヒアドキュメントの中身を外す（文章での言及で誤って止めないため・他 hook と同型）。"""
    s = re.sub(r"<<\s*[\"']?(\w+)[\"']?.*?^\1", " ", cmd or "", flags=re.S | re.M)
    s = re.sub(r'"[^"]*"', " ", s)
    s = re.sub(r"'[^']*'", " ", s)
    return s


def is_target(tool, file_path, cmd, content):
    """止める相手か。返すのは (種類, いま触るものの名前)。相手でなければ (None, None)。

    種類＝ code（engine_tuner のコード）／ design（設計書）／ run（engine_tuner を走らせる）
    """
    base = os.path.basename(file_path or "")
    if tool in ("Write", "Edit", "MultiEdit"):
        if _RE_TUNER_NAME.match(base):
            return "code", base                      # ★中身に関わらず必ず止める
        if base == "acceptance.md" or base.endswith("_design.md"):
            if "engine_tuner" in (content or ""):    # ★プログラムが中身を読んで決める
                return "design", base
        return None, None
    if tool == "Bash":
        x = strip_text(cmd)
        if not _RE_PY.search(x):
            return None, None                        # python の実行でなければ通す（読むだけ 等）
        if _RE_SKIP.search(x):
            return None, None                        # 検査だけの実行は通す
        m = _RE_TUNER_PY.search(x)
        if m:
            return "run", m.group(1)
        return None, None
    return None, None


def search_path_files(path=_H2_PASS):
    """探索の経路のファイルの名前（basename）の集合を H2 の印から読む。

    ★手書きの一覧を作らない（教訓 L-468＝手書きは書き忘れが黙って通る）。
    読めないときは空の集合を返す＝「変えない」を書ける側に倒す。
      理由＝ここで止めると、H2 の印が無い状態（検査のやり直し中）で何も書けなくなる。
      その状態では enforce_h2_pass が別に engine_tuner の実行を止めている。
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return set()
    return {os.path.basename(p) for p in (data.get("files") or []) if p}


def _names_in_design(content):
    """設計書の中から、これから触る相手の名前を拾う（TARGET の行と impl_file の値）。"""
    names = set()
    for line in (content or "").splitlines():
        s = line.strip()
        if s.startswith("TARGET:"):
            for tok in re.findall(r"[\w./-]+\.(?:py|json)", s):
                names.add(os.path.basename(tok))
    for m in re.finditer(r'"impl_file"\s*:\s*"([^"]+)"', content or ""):
        names.add(os.path.basename(m.group(1)))
    return names


def touches_search_path(kind, name, content):
    """この変更は、探索の経路のファイルを触るか。触るなら「変えない」は書けない。"""
    files = search_path_files()
    if not files:
        return False
    if kind in ("code", "run"):
        return name in files
    if kind == "design":
        return bool(_names_in_design(content) & files)
    return False


def load_decl(path=DECL):
    """宣言のファイルを読む。無ければ None。"""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _line_starting(text, prefix):
    for line in (text or "").splitlines():
        if line.strip().startswith(prefix):
            return line.strip()
    return None


def decl_age_hours(text, now=None):
    """宣言の「日付:」から、いま何時間 経ったかを出す。読めなければ None。"""
    line = _line_starting(text, "日付:")
    if line is None:
        return None
    raw = line.split(":", 1)[1].strip()
    raw = re.sub(r"[（(].*?[）)]", "", raw).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            t = datetime.strptime(raw[:len(datetime(2026, 1, 1).strftime(fmt))], fmt)
        except Exception:
            continue
        return ((now or datetime.now()) - t).total_seconds() / 3600.0
    return None


def judge(tool, file_path, cmd, content, decl_text, now=None, agent_type=""):
    """止めるなら理由の文字列、通すなら None。"""
    if agent_type:
        return None                                   # サブエージェントは通す
    if os.path.abspath(file_path or "") == os.path.abspath(DECL):
        return None                                   # 宣言のファイル自身は通す（行き止まり回避）

    kind, name = is_target(tool, file_path, cmd, content)
    if kind is None:
        return None

    if decl_text is None:
        return f"目的の照合のファイルが無い（{DECL}）"
    if "【目的の照合】" not in decl_text:
        return "「【目的の照合】」の行が無い"

    taisho = _line_starting(decl_text, "対象:")
    if taisho is None:
        return "「対象:」の行が無い（これから書く／直す／走らせるものを書く）"
    if name not in taisho and not (kind == "design" and "engine_tuner" in taisho):
        return f"「対象:」の行に、いま触るもの（{name}）が書かれていない ／ いまの中身＝{taisho}"

    if _line_starting(decl_text, "日付:") is None:
        return "「日付:」の行が無い（いつ書いた宣言かが分からない）"
    age = decl_age_hours(decl_text, now)
    if age is None:
        return "「日付:」の行を読み取れない（例＝日付: 2026-08-26 15:04）"
    if age > MAX_AGE_HOURS:
        return f"宣言が古い（{age:.1f} 時間 前・上限 {MAX_AGE_HOURS} 時間）＝いまの作業に対して書き直す"

    for m in MARK_MOKUTEKI + MARK_JOKEN:
        if _line_starting(decl_text, m) is None:
            return f"「{m}」で始まる行が無い（目的2つと条件4つを1つずつ書く）"

    ng = [_line_starting(decl_text, m) for m in MARK_MOKUTEKI + MARK_JOKEN
          if "❌" in (_line_starting(decl_text, m) or "")]
    if ng:
        return "❌ が在る＝これは作ってはいけないものです ／ " + " ／ ".join(ng)

    # ★「変えない」の印（2026-08-26）＝❌ の判定の後に見る（❌ が優先）。
    mk = [_line_starting(decl_text, m) for m in MARK_MOKUTEKI
          if MARK_KAENAI in (_line_starting(decl_text, m) or "")]
    if mk:
        return ("目的の行に「" + MARK_KAENAI + "」は書けません（目的はどんな変更にも当てはまります）"
                " ／ " + " ／ ".join(mk))

    jk = [_line_starting(decl_text, m) for m in MARK_JOKEN
          if MARK_KAENAI in (_line_starting(decl_text, m) or "")]
    if jk and touches_search_path(kind, name, content):
        hit = sorted(_names_in_design(content) & search_path_files()) if kind == "design" else [name]
        return ("「" + MARK_KAENAI + "」は、探索の経路のファイルを触るときには書けません"
                f" ／ 触る相手＝{'・'.join(hit)}（H2 の印の一覧に在る）"
                " ／ " + " ／ ".join(jk))

    if _line_starting(decl_text, "作ってはいけないものの一覧との照合:") is None:
        return "「作ってはいけないものの一覧との照合:」の行が無い（要件定義書の一覧と1件ずつ突き合わせる）"
    if "入っていないもの" not in decl_text:
        return "「★入っていないもの:」の行が無い（都合の悪い事実を落とさない）"
    return None


def _message(reason):
    out = []
    out.append("🔒 [目的ゲート・safety hook] engine_tuner に手を入れる前に、目的の照合を書いてください。")
    out.append("")
    out.append("★まこさんの逐語（2026-08-06）")
    out.append("  「net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、"
               "見つけることができる機械を作ることが目的」")
    out.append("  「上記目的に即していないもの以外は作らないこと」")
    out.append("  「つまりは上記条件を一つでも達成できていないものは作成してはいけないということ。」")
    out.append("")
    out.append(f"不足: {reason}")
    out.append("")
    cur = load_decl()
    if cur is not None:
        out.append("───────── いまの目的の照合 ─────────")
        out.append(cur)
        out.append("──────────────────────────────────")
        out.append("")
    out.append(f"対処: ①下の型で {DECL} を書く ②同じ内容をチャットに貼る ③再実行する")
    out.append(TEMPLATE)
    out.append("")
    out.append("⛔ 目的2つ・条件4つのどれか1つでも ❌ が在るものは、作ってはいけません（まこさん確定 2026-08-06）。")
    out.append("★条件の行には「" + MARK_KAENAI + "」も書けます（＝その条件の探索に1バイトも触らない）。")
    out.append("   ただし探索の経路のファイルを触るときは書けません（判定はプログラム＝H2 の印の一覧）。")
    out.append("   目的の行には使えません。")
    out.append("   ❌ になるものを作りたいときは、まこさんに理由を出して確認してください（CC が勝手に進めません）。")
    out.append("（解除は 2026-08-16 に廃止＝合言葉では通りません）")
    return "\n".join(out)


def hook_main():
    try:
        data = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)                                   # 読めない入力では止めない（fail-open）
    ti = data.get("tool_input") or {}
    tool = data.get("tool_name", "")
    file_path = ti.get("file_path", "") or ""
    cmd = ti.get("command", "") or ""

    # 設計書かどうかを見るための中身。
    #   Write＝これから書く中身が、その設計書の中身そのもの。
    #   Edit/MultiEdit＝いま在る中身が、その設計書が何の設計かを決める。だから両方 見る。
    parts = [ti.get("content", "") or "", ti.get("new_string", "") or ""]
    for e in (ti.get("edits") or []):
        if isinstance(e, dict):
            parts.append(e.get("new_string", "") or "")
    if tool in ("Edit", "MultiEdit") and file_path:
        try:
            with open(file_path, encoding="utf-8") as f:
                parts.append(f.read())
        except Exception:
            pass
    content = "\n".join(parts)

    reason = judge(tool, file_path, cmd, content, load_decl(), agent_type=data.get("agent_type", ""))
    if reason:
        print(_message(reason), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


# ---------------- 番人（わざと壊して、止まることを確かめる） ----------------

def _decl(now, target="engine_tuner_gen.py", drop=(), ng=(), kaenai=()):
    """見本の宣言を作る。drop＝落とす行の印／ng＝❌ にする行の印／kaenai＝「変えない」にする行の印。"""
    rows = [
        ("head", "【目的の照合】"),
        ("対象", f"対象: {target}"),
        ("日付", "日付: " + now.strftime("%Y-%m-%d %H:%M")),
        ("目的1", "目的1 net 利益を最大にする方向に働くか: {m} 探索の結果を net で選ぶため"),
        ("目的2", "目的2 見つける（探す）ことができるか: {m} 範囲から探す形になっているため"),
        ("条件1", "条件1 指標を、探して見つけられるか: {m} 材料のカタログから選べるため"),
        ("条件2", "条件2 閾値を、探して見つけられるか: {m} 分位の範囲から引くため"),
        ("条件3", "条件3 時間足を、探して見つけられるか: {m} 8つの時間足から選べるため"),
        ("条件4", "条件4 パラメータを、範囲から探して見つけられるか: {m} lo〜hi の範囲から引くため"),
        ("照合", "作ってはいけないものの一覧との照合: 1番＝当たらない ／ 2番＝当たらない"),
        ("入って", "★入っていないもの: なし"),
    ]
    out = []
    for key, text in rows:
        if key in drop:
            continue
        mark = "❌" if key in ng else (MARK_KAENAI if key in kaenai else "✅")
        out.append(text.replace("{m}", mark))
    return "\n".join(out)


def selftest():
    now = datetime(2026, 8, 26, 18, 0)
    old = now - timedelta(hours=25)
    ok = _decl(now)
    W, B = "Write", "Bash"
    gen = os.path.join(ROOT, "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py")
    acc = os.path.join(ROOT, ".claude/state/acceptance.md")
    todo = os.path.join(ROOT, ".claude/state/session_todo.md")

    cases = [
        # (名前, tool, file_path, cmd, content, decl_text, agent, 止まるべきか)
        ("1 宣言のファイルが無いと止まる", W, gen, "", "", None, "", True),
        ("2 【目的の照合】の行が無いと止まる", W, gen, "", "", _decl(now, drop=("head",)), "", True),
        ("3 目的1 が無いと止まる", W, gen, "", "", _decl(now, drop=("目的1",)), "", True),
        ("4 条件3（時間足）が無いと止まる", W, gen, "", "", _decl(now, drop=("条件3",)), "", True),
        ("5 条件4 が ❌ だと止まる", W, gen, "", "", _decl(now, ng=("条件4",)), "", True),
        ("6 目的2 が ❌ だと止まる", W, gen, "", "", _decl(now, ng=("目的2",)), "", True),
        ("7 ★全部 ✅ で日付も対象も合っていれば通る", W, gen, "", "", ok, "", False),
        ("8 日付が 25時間 前だと止まる", W, gen, "", "", _decl(old), "", True),
        ("9 日付の行が無いと止まる", W, gen, "", "", _decl(now, drop=("日付",)), "", True),
        ("10 対象の行に、いま触るものの名前が無いと止まる", W, gen, "", "",
         _decl(now, target="e38_logics.json"), "", True),
        ("11 作ってはいけないものとの照合の行が無いと止まる", W, gen, "", "",
         _decl(now, drop=("照合",)), "", True),
        ("12 ★入っていないもの の行が無いと止まる", W, gen, "", "", _decl(now, drop=("入って",)), "", True),
        ("13 ★通し道＝コマンドに purpose_check を足しても止まる", B, "",
         'python3 engine_tuner.py --purpose search ; echo "purpose_check"', "", None, "", True),
        ("14 engine_tuner_gen.py を書くと止まる", W, gen, "", "", None, "", True),
        ("15 --selftest だけの実行は通る", B, "", "python3 engine_tuner_gen.py --selftest", "", None, "", False),
        ("16 --dry-run だけの実行は通る", B, "", "python3 engine_tuner_gen.py --dry-run 5", "", None, "", False),
        ("17 --purpose search の実行は止まる", B, "", "python3 engine_tuner.py --purpose search", "", None, "", True),
        ("18 engine_tuner の文字が在る設計書は止まる", W, acc, "",
         "TARGET: scripts/priority_rebuild/engine_tuner_gen.py", None, "", True),
        ("19 ★engine_tuner の文字が無い設計書は通る", W, acc, "",
         "TARGET: scripts/priority_rebuild/gen_materials.py", None, "", False),
        ("20 関わりのないファイルの書き込みは通る", W, todo, "", "engine_tuner の話を書いただけ", None, "", False),
        ("21 宣言のファイル自身は通る", W, DECL, "", "", None, "", False),
        ("22 サブエージェントは通る", W, gen, "", "", None, "general-purpose", False),
        ("23 読むだけのコマンドは通る", B, "", f"cat {DECL} ; grep -n engine_tuner_gen.py x.md", "", None, "", False),

        # ---- ★2026-08-26（2回目の直し）＝「変えない」の印 ----
        ("24 ★文書を作るプログラムの設計書で、条件4つを 変えない にすると通る", W, acc, "",
         "TARGET: scripts/priority_rebuild/gen_materials.py\nengine_tuner のやることリストに差し込む",
         _decl(now, target="acceptance.md", kaenai=MARK_JOKEN), "", False),
        ("25 engine_tuner_gen.py を書くときに 変えない を書くと止まる", W, gen, "",
         "", _decl(now, target="engine_tuner_gen.py", kaenai=MARK_JOKEN), "", True),
        ("26 engine_tuner.py を走らせるときに 変えない を書くと止まる", B, "",
         "python3 engine_tuner.py --purpose search", "",
         _decl(now, target="engine_tuner.py", kaenai=("条件2",)), "", True),
        ("27 設計書の TARGET が engine_tuner_exec.py なら 変えない は書けない", W, acc, "",
         "TARGET: scripts/priority_rebuild/engine_tuner_exec.py",
         _decl(now, target="acceptance.md", kaenai=MARK_JOKEN), "", True),
        ("28 設計書の impl_file が engine_tuner_gen.py なら 変えない は書けない", W, acc, "",
         'TARGET: .claude/hooks/x.py\n"impl_file": "scripts/priority_rebuild/engine_tuner_gen.py"',
         _decl(now, target="acceptance.md", kaenai=MARK_JOKEN), "", True),
        ("29 目的1 に 変えない を書くと止まる", W, gen, "", "",
         _decl(now, kaenai=("目的1",)), "", True),
        ("30 目的2 に 変えない を書くと止まる", W, gen, "", "",
         _decl(now, kaenai=("目的2",)), "", True),
        ("31 条件に 変えない と ❌ が混ざると止まる（❌ が優先）", W, gen, "", "",
         _decl(now, ng=("条件1",), kaenai=("条件2",)), "", True),
    ]
    ng_count = 0
    for name, tool, fp, cmd, content, decl, agent, want_block in cases:
        got = judge(tool, fp, cmd, content, decl, now=now, agent_type=agent)
        good = (got is not None) == want_block
        print(f"  {'✅' if good else '❌'} {name}" + ("" if good else f"   ← 出た結果: {got}"))
        ng_count += (not good)
    print(f"\n番人: {len(cases) - ng_count}/{len(cases)} pass")
    sys.exit(1 if ng_count else 0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    hook_main()
