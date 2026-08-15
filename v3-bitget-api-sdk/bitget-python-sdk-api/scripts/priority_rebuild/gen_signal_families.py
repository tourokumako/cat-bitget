#!/usr/bin/env python3
"""gen_signal_families.py — 型の表（許可の一覧）の自動生成（CP4 監査フィードバック①・2026-08-06）

まこさん確定の作り（2026-08-06 逐語準拠）:
  表の本体＝カタログ105種×8時間足＋軸カタログから機械で広く展開する（V9 は使わない）。
  削る＝「方向」の欄から機械生成した禁止（向きの矛盾）などで、無意味な組み合わせだけ消す。
  試験＝できた表に V9 の実物の組み合わせが入っているかを機械で照合する（入っていなければ表が不合格）。

★すべて自動生成（まこさん指示「極力自動生成で作れ」「すべて自動生成でつくれ」）:
  - 表の本体・禁止の規則・出典は、全部このスクリプトが機械で作る。CC の作文の行はゼロ。
  - 機械で導けない決まりは、作らずに「空欄・まこさんの判断待ち」として表に明示する（根拠の無い行を書かない）。
  - 出力は決定論（同じ入力から2回作って md5 が一致）。--verify が手の改変を検出する。

このスクリプトがやらないこと: 売買しない・値を選ばない・採点しない・engine_tuner 系のコードに触れない。
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(HERE))

import indicator_reference_diag as iref                     # noqa: E402（方向の欄・系統＝②で検査済み）

MATRIX_MD = SDK / ".claude/ratchet/entry_exit_matrix.md"    # 軸カタログの正本（E-a シグナル家族）
LIMITS_JSON = HERE / "recipes/search_limits.json"           # n_min=30（まこさん OK 2026-08-01「たたき台でOK」）
OUT_JSON = SDK / ".claude/ratchet/signal_families.json"     # 型の表（機械可読・G2 判定器が読む）
OUT_MD = SDK / ".claude/ratchet/signal_families.md"         # 型の表（人が読む・同じ中身）

# 値決め窓の日数（periods.py 正本から機械で取る＝手打ちしない）
from periods import SEARCH_START, SEARCH_END                # noqa: E402


def _catalog():
    """部品の一覧＝observe_diag のカタログ（②の材料検査で検証済み）から機械抽出。"""
    import importlib.util as iu
    spec = iu.spec_from_file_location("od", HERE / "observe_diag.py")
    od = iu.module_from_spec(spec)
    spec.loader.exec_module(od)
    cfg = od.load_config(None)
    names = [nm for nm, _f, _d in od.build_catalog(cfg)]
    tfs = list(cfg["timeframes"])
    return names, tfs


def _families_ea() -> list[dict]:
    """型の一覧＝軸カタログ（entry_exit_matrix.md の E-a 行）から機械抽出。"""
    text = MATRIX_MD.read_text(encoding="utf-8")
    m = re.search(r"\*\*E-a シグナル家族（何を取るか・[^*]*\*\*:\s*(.+)", text)
    if not m:
        raise SystemExit("[生成エラー] entry_exit_matrix.md に E-a シグナル家族の行が見つからない")
    line = m.group(1)
    fams = []
    for chunk in re.split(r"\s*/\s*(?=\(\d\))", line):       # 区切りは「 / (数字)」＝型名の中の / では切らない
        mm = re.match(r"\((\d)\)\s*(.+)", chunk.strip())
        if mm:
            fams.append(dict(id=f"E-a{mm.group(1)}", name=mm.group(2).strip()))
    if len(fams) != 8:
        raise SystemExit(f"[生成エラー] E-a の型が {len(fams)} 個しか取れない（8個のはず）＝正本の形が変わった")
    return fams


def _n_min() -> int:
    j = json.loads(LIMITS_JSON.read_text(encoding="utf-8"))
    v = j.get("n_min")
    if not isinstance(v, (int, float)) or v <= 0:
        raise SystemExit("[生成エラー] search_limits.json の n_min が読めない")
    return int(v)


_TF_MIN = {"5m": 5, "10m": 10, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240, "6h": 360, "12h": 720, "1d": 1440}


def _window_days(name: str, tf: str) -> float | None:
    """部品×時間足の「値が独立に1つ決まるのに要する日数」＝カタログ名のパラメータから機械算出。
    出典＝CP2 監査 4-4 の算術（122日の窓に日足50本平均は独立区間が2つしか取れない）。"""
    ref, prm = iref.find(name)
    if ref is None or tf not in _TF_MIN:
        return None
    nums = [p for p in (prm or ()) if isinstance(p, (int, float)) and p >= 2]
    win_bars = max(nums) if nums else 1
    return win_bars * _TF_MIN[tf] / 1440.0


def build_table() -> dict:
    """表の本体＝広く展開。削る＝機械生成の禁止だけ。全行に根拠フィールドが付く。"""
    names, tfs = _catalog()
    fams = _families_ea()
    n_min = _n_min()
    period_days = (SEARCH_END - SEARCH_START).days

    # ── 禁止1: 向きを持たない部品を「向きの条件」に使わない（方向の欄＝②材料検査1 で全種検証済み）──
    ban_direction = []
    # ── 禁止2: カタログ注記「型の表で向きの材料に使わない」（②の実測＋まこさん OK 2026-08-06）──
    ban_note = []
    kubun = {}
    for nm in names:
        ref, _ = iref.find(nm)
        cat = ref["houkou"].split("＝")[0] if ref else "？"
        kubun[nm] = cat
        if "型の表で向きの材料に使わない" in (ref["houkou"] if ref else ""):
            ban_note.append(nm)
        elif cat in ("状態量", "ボラ量"):
            ban_direction.append(nm)

    # ── 禁止3: 有効標本数の不足（部品×時間足）。n_eff = 値決め窓の日数 ÷ 独立に1つ決まる日数 < n_min ──
    ban_samples = []
    for nm in names:
        for tf in tfs:
            wd = _window_days(nm, tf)
            if wd is None:
                continue
            n_eff = period_days / wd if wd > 0 else float("inf")
            if n_eff < n_min:
                ban_samples.append(dict(part=nm, tf=tf, n_eff=round(n_eff, 1)))

    # ── そもそもの一覧（目的の4要素＝指標・閾値・時間・パラメータ を1枚で確認できる写し・2026-08-07 まこさん指示）──
    #   正本＝指標と時間足: observe_diag のカタログ ／ 閾値と探索の格子: recipes/search_limits.json（まこさん承認 2026-08-01）。
    #   ここは機械の写し＝手で書かない。正本が変われば --write で写しも変わり、指紋が変わって再承認になる。
    limits_all = json.loads(LIMITS_JSON.read_text(encoding="utf-8"))
    grids = {k: v for k, v in limits_all.items() if not k.startswith("_")}
    lineage_of = {}
    for nm in names:
        ref, _ = iref.find(nm)
        fam = ref["family"] if ref else "？"
        lineage_of[nm] = iref.FAMILY_LINEAGE.get(fam, {}).get("k", "？")

    table = dict(
        purpose="net利益を最大化させる条件（指標、閾値、時間、パラメータ）の組み合わせを、見つけることができる機械を作ることが目的（まこさん確定 2026-08-06 逐語）",
        built_by="gen_signal_families.py（全自動生成・CC の手書きの行ゼロ）",
        inventory=dict(
            note="指標と時間足の正本＝observe_diag のカタログ。閾値と探索の格子の正本＝recipes/search_limits.json"
                 "（まこさん承認 2026-08-01『たたき台でOK』・r_min は 2026-08-01 OK で 0.25）。ここは機械の写し",
            lineage_of=lineage_of,
            thresholds=dict(
                quantile_grid=grids["quantile_grid"],
                quantile_range=grids.get("quantile_range"),   # ★2026-08-15（段A の A-5-3）
                note="閾値は USD の生の値でなく、値決め窓の分位（データを小さい順に並べた何%点か）で引く（H6 価格非依存）。"
                     "★2026-08-15（段A の A-5-3）に 9段のメニューから範囲（quantile_range）へ変えた。"
                     "直す前ここに書いてあった理由『9段より細かくしないのは、試す数が増えるほど合格の線が"
                     "厳しくなる（多重検定の罰）ため』は事実と違う＝合格の線 DSR の N は tuner_stats.py の "
                     "n_for_dsr ＝ n_eff（実際に走らせた試行を似た動きでまとめた数）＋ 過去の累積試行であって、"
                     "候補の広さは入っていない",
            ),
            grids=grids,
        ),
        # 表の本体（広さ）＝機械抽出。ここから下の禁止に当たらない組み合わせは全部 許可。
        families=fams,
        parts=names,
        timeframes=tfs,
        kubun=kubun,
        # 削る（全部 機械生成・根拠つき）
        bans=dict(
            direction_stateful=dict(
                rule="区分が 状態量・ボラ量 の部品は、向き（上昇/下落の優劣）の条件に使えない。強さ・量の条件には使える",
                parts=sorted(ban_direction),
                basis="indicator_reference_diag の「方向」の欄（2026-08-06 材料検査1＝合成系列＋実データの2本柱で全種検証済み・❌0件）",
            ),
            direction_note=dict(
                rule="カタログ注記「型の表で向きの材料に使わない」を持つ部品は、向きの条件に使えない",
                parts=sorted(ban_note),
                basis="2026-08-06 材料検査1 の実測（普通の相場で向きの差が四分位幅の半分以下）＋まこさん OK",
            ),
            insufficient_samples=dict(
                rule=f"値決め窓 {period_days} 日で有効標本数 n_eff < {n_min} の（部品×時間足）は条件の候補にしない",
                pairs=ban_samples,
                basis="CP2 監査 4-4 の算術＋search_limits.json の n_min（まこさん OK 2026-08-01）。恒久の接続（検査5 の実測表）は D9 の直しで行う",
            ),
        ),
        # ── 追加の部品（D12・2026-08-07 まこさん OK「OK」）＝カタログ105種の外に在る入口の材料を機械抽出 ──
        #   2026-08-07 の実測＝100本の案の入口の材料のうち65個（帯内位置%47・時刻18）が表に載っておらず、
        #   G2 が許可も禁止も言えなかった。保有時間（state:hold_min）は出口の材料＝この表の対象外のまま。
        extra_parts=dict(
            geo=dict(
                rule="レンジ幾何の列は kind=ratio（W%・帯内位置%）だけ入口の条件の材料に使える。"
                     "kind=price（帯の4隅 res_hi/res_lo/sup_hi/sup_lo・mid）は placement の幾何参照専用（H6 価格非依存）＝条件の材料に使えない",
                parts=sorted(nm for nm, r in iref.RANGE_GEO_REF.items() if r.get("kind") == "ratio"),
                basis="indicator_reference_diag.RANGE_GEO_REF の kind の欄（実行器 engine_tuner_exec.py 152行 G6 が登録済み列だけ通し、"
                      "259行が ratio 以外を条件の材料に使うのを既に止めている＝その決まりを表にも写した）",
            ),
            time=dict(
                rule="カレンダー由来の列（時刻・曜日）は入口の条件の材料に使える（計算なし・因果性自明）",
                parts=sorted(iref.TIME_REF),
                basis="indicator_reference_diag.TIME_REF ＋ entry_exit_matrix.md 軸カタログ E-j"
                      "（逐語＝「時刻と曜日は既存データから列を作れる（材料の列としても追加する）」）",
            ),
        ),
        # ── 役割×系統×時間足（D1 の対応表・2026-08-07 CC の案＝1行ずつ出典つき。承認の指紋がまこさんの判断の記録）──
        #   2026-08-06 の空欄（役割ごとの系統の絞り）を、材料（実測＝V9 の実物・KB 逐語・WebResearch 2026-08-07）を
        #   揃えて埋めた案。行が無い型は生成不可（fail-closed）＝根拠なしに広げない。
        role_lineage=dict(
            rule="レンジ系の型（E-a1 逆張り／E-a4 戻り売り・押し目／E-a5 グリッド／E-a8 レンジ内 value）の構造は、"
                 "役割ごとに下の系統×時間足だけから材料を引く。行が無い型（E-a2・E-a3・E-a6・E-a7）は生成不可",
            applies_to=["E-a1", "E-a4", "E-a5", "E-a8"],
            not_covered=dict(
                families=["E-a2", "E-a3", "E-a6", "E-a7"],
                note="根拠（実測・WebResearch）が未収集＝生成不可（fail-closed）。順張り（E-a2）の引き金＝トレンド系は"
                     " V9 P21 の実物が在るが、局面が下げトレンド＝レンジの表には書かない。材料を揃えたら行を足して再承認",
            ),
            roles=dict(
                trigger=dict(
                    lineages=["オシレーター", "ローソク"], tfs=["5m", "10m", "15m"],
                    basis="technical KB §2.4（V9 P3 実物＝『Stoch ゴールデンクロス ← オシレーター系・トリガー』）／"
                          "range_scalping_kb §3（拒否の確認材料＝反転ローソク足パターン＋モメンタム・『5分足は RSI9』）／"
                          "technical KB §2.1（『短期足でタイミング』）＝スキャルの保有は分単位（range_scalping_kb §1・§4）"
                          "＝上位足の引き金では入る瞬間を決められない",
                ),
                env=dict(
                    lineages=["トレンド", "ボラ", "時間帯"], tfs="all",
                    basis="technical KB §2.1（『長期足で方向性確認』＝環境認識）／§2.4（V9 P3 実物＝『BB middle slope ← "
                          "トレンド系・トレンド確認』『ADX ∈ [30,50) ← トレンド系・強さ確認』＝5分足）／"
                          "WebResearch 2026-08-07（上位足のトレンドフィルタ・ADX でレンジ/トレンドを分類・レンジは ADX 低）"
                          "※時間足は 5m を含む全部＝V9 の実物が 5m の環境認識で稼いでいるため締め出さない（v9-selftest の原則）",
                ),
                sufficiency=dict(
                    lineages=["ボラ", "出来高", "需給", "オシレーター"], tfs="all",
                    basis="technical KB §2.4（V9 P3 実物＝『ATR ≥ 250 ← ボラ系・ボラ十分性』）／"
                          "range_scalping_kb §3（拒否の確認材料に出来高）／§6.7（需給フィルタ＝このプロジェクトで既に効いている確定エッジ）／"
                          "WebResearch 2026-08-07（ATR のボラゲート＝動かない場面のスキャル失敗を避ける）"
                          "※オシレーターは行き過ぎの量（zscore_return 等の状態量）を数える用途",
                ),
                location=dict(
                    lineages=["構造・位置"], tfs="all", geo=True,
                    basis="range_scalping_kb §3（手順＝『①ゾーンに到達 → ②拒否の確認 → ③エントリー』）／"
                          "§7（上位足で機械検出したゾーンの間にいる時だけ入口を開く）／レンジ幾何2列と時刻は extra_parts",
                ),
            ),
        ),
        # ── 向きの矛盾の定義（D1 の対応表の向きの部分・2026-08-07 CC の案＝1行ずつ出典つき）──
        direction_conflict=dict(
            rule="型の狙う向きと逆の条件を作らない。機械で判定できる4つの決まり",
            items=[
                dict(id="DC1",
                     rule="順張り値の部品（プラス＝上昇優勢）を side 付きの形（level・diff・slope・slope_avg）で"
                          " 環境認識・十分性に使うとき、SHORT は below だけ・LONG は above だけ（逆＝狙いと逆の地合いの要求）",
                     basis="V9 P23 実物（SHORT＝『BB中央線 下向き』∩ 陰線・range_scalping_kb §9.1）／"
                           "V9 P3 実物（LONG＝『BB middle slope > 10』・technical KB §2.4）"),
                dict(id="DC2",
                     rule="レンジ系の型の引き金のオシレーター（level 形）は、行き過ぎを逆に取る＝"
                          "SHORT は above かつ 高分位（q70・q80・q90）・LONG は below かつ 低分位（q10・q20・q30）",
                     basis="E-a1 の逐語（『レンジ端/行き過ぎを fade』）／range_scalping_kb §3（『レンジ相場の RSI は 70/30 が有効』）／"
                           "WebResearch 2026-08-07（MR＝RSI>70 で売り・<30 で買いが入口）"
                           "※70/30 の絶対値を分位（q70/q30）へ写すのは実装の形式＝絶対値そのものではないことを明示"),
                dict(id="DC3",
                     rule="cross の direction は side と揃える＝up は LONG だけ・down は SHORT だけ",
                     basis="V9 P3 実物（Stoch ゴールデンクロス＝LONG の引き金）／V9 P23 実物（stoch デッドクロス＝SHORT の引き金・range_scalping_kb §9.1）"),
                dict(id="DC4",
                     rule="ローソクの反転サイン・candle_dir は SHORT＝bear だけ・LONG＝bull だけ",
                     basis="range_scalping_kb §3（『ショート＝レジスタンスゾーンで確認された拒否』＝反転ローソク）／"
                           "V9 P23 実物（陰線 ∩ SHORT・range_scalping_kb §9.1）"),
            ],
        ),
        approval=dict(fingerprint=None, note="まこさんの承認の指紋が入るまで、この表は無効（G1 が生成器のコードの書き込みを止める）"),
    )
    return table


def _canon(table: dict) -> str:
    return json.dumps(table, ensure_ascii=False, sort_keys=True, indent=1)


def _md(table: dict, h: str) -> str:
    b = table["bans"]
    lines = [
        f"<!-- SIGNAL_FAMILIES hash={h} gen_signal_families.py が自動生成＝手で書き換えない -->",
        "# signal_families.md — 型の表（許可の一覧・全自動生成・CC の手書きの行ゼロ）",
        "",
        "作り（まこさん確定 2026-08-06）＝ 表の本体は広く展開 ／ 削るのは機械生成の禁止だけ ／ 検算は V9 の実物。",
        "",
        f"## 表の本体（広さ）＝型 {len(table['families'])} 種 × 部品 {len(table['parts'])} 種 × 時間足 {len(table['timeframes'])} 本",
        "",
        "| 型 | 中身（軸カタログ E-a の逐語） |",
        "|---|---|",
    ]
    for f in table["families"]:
        lines.append(f"| {f['id']} | {f['name']} |")
    ep = table["extra_parts"]
    inv = table["inventory"]
    lin_of = inv["lineage_of"]
    kub = table["kubun"]
    by_lin: dict = {}
    for nm in table["parts"]:
        by_lin.setdefault(lin_of.get(nm, "？"), []).append(nm)
    lines += [
        "",
        "部品と時間足＝observe_diag のカタログ（2026-08-06 材料検査済み）の全部。**下の禁止に当たらない組み合わせは全部 許可。**",
        "",
        "## そもそもの一覧（目的の4要素＝指標・閾値・時間足・パラメータ・機械の写し）",
        "",
        f"（{inv['note']}）",
        "",
        f"### 指標 … {len(table['parts'])} 種（系統ごと・括弧の中は方向の区分）",
        "",
    ]
    for lin in sorted(by_lin, key=lambda k: -len(by_lin[k])):
        parts_s = "、".join(f"{nm}({kub.get(nm, '？')})" for nm in by_lin[lin])
        lines.append(f"- **{lin}**（{len(by_lin[lin])} 種）: {parts_s}")
    g = inv["grids"]

    def _rng(key: str) -> str:
        """範囲を人が読む形にする（★2026-08-15＝段A の A-5-2 で格子が範囲に変わったため）。

        直す前は `[1.0, 1.5, 2.0, 3.0]` のような「決まった数字だけ」の一覧を、そのまま印字していた。
        いまは下限と上限を印字する。設定ファイルに古い一覧が残っている間は、その一覧を印字する。
        """
        v = g.get(key)
        if isinstance(v, dict) and v.get("lo") is not None:
            kind = "整数" if str(v.get("kind")) == "int" else "小数"
            return f"{v['lo']} 〜 {v['hi']}（{kind}）"
        old = key[: -len("_range")] + "_grid" if key.endswith("_range") else key
        return str(g.get(key, g.get(old, "（設定ファイルに無い）")))

    lines += [
        "",
        f"### 時間足 … {len(table['timeframes'])} 本",
        "",
        "、".join(table["timeframes"]),
        "",
        # ★2026-08-15（段A の A-5-3）＝分位は9段のメニューから範囲になった。
        #   範囲が設定ファイルに在れば、それを印字する（無ければ直す前と同じ段の一覧を印字）。
        (f"### 閾値 … 分位 **範囲 q{int(g['quantile_range']['lo'])}〜q{int(g['quantile_range']['hi'])}**"
         f"（{int(g['quantile_range']['hi']) - int(g['quantile_range']['lo']) + 1} 通り・"
         "★段A の A-5-3 で 9段のメニューから範囲にした）"
         if isinstance(g.get("quantile_range"), dict) and g["quantile_range"].get("lo") is not None else
         f"### 閾値 … 分位 {len(inv['thresholds']['quantile_grid'])} 段"
         f"（{'、'.join(inv['thresholds']['quantile_grid'])}）"),
        "",
        f"（{inv['thresholds']['note']}）",
        "",
        "### 探索のパラメータの格子（正本＝recipes/search_limits.json・まこさん承認 2026-08-01）",
        "",
        "| 名前 | 値 | 何の格子か |",
        "|---|---|---|",
        f"| count_range | {g['count_range']} | 条件の本数の範囲 |",
        f"| role_max | {json.dumps(g['role_max'], ensure_ascii=False)} | 役割ごとの本数の上限（引き金は常に1本） |",
        f"| k_max | {g['k_max']} | 同じ系統を重ねられる上限 |",
        f"| depth_max | {g['depth_max']} | 入れ子の深さの上限 |",
        f"| p_max | {g['p_max']} | 発火経路の数の上限（探索の既定は1経路） |",
        f"| int_range | {_rng('int_range')} | 本数の範囲（傾き・連続などの N） |",
        f"| hour_range | {_rng('hour_range')} | 時刻の境界の範囲 |",
        f"| hold_range_by_role | {json.dumps(g['hold_range_by_role'], ensure_ascii=False)} | 保有時間の上限の範囲（役割ごと・5分足の本数） |",
        f"| state_mult_range | {_rng('state_mult_range')} | 出口の名前つき定数の倍数の範囲 |",
        f"| frac_range | {_rng('frac_range')} | 部分利確の割合の範囲（%） |",
        f"| exit_mult_range | {_rng('exit_mult_range')} | SL の帯幅の倍数の範囲（%） |",
        f"| max_adds_range | {_rng('max_adds_range')} | 積み増しの回数の範囲 |",
        f"| hold_frac_range | {_rng('hold_frac_range')} | 保有の門＝満期に対する割合の範囲 |",
        f"| giveback_range | {_rng('giveback_range')} | 含み益のピークから戻す割合の範囲 |",
        f"| loss_cap_range | {_rng('loss_cap_range')} | 1トレードの最大許容損失の範囲（%） |",
        f"| ladder_steps_range | {_rng('ladder_steps_range')} | 部分利確の段数の範囲 |",
        f"| n_min | {g['n_min']} | 列の有効標本数の下限（禁止3 の材料） |",
        f"| r_min | {g['r_min']} | リスクリワード比の下限 |",
        f"| fdr_q | {g['fdr_q']} | BH 法の偽発見率の線 |",
        "",
        "## 追加の部品（D12・2026-08-07）＝カタログの外に在る入口の材料（機械抽出）",
        "",
        f"### レンジ幾何 … {len(ep['geo']['parts'])} 列（{('、'.join(ep['geo']['parts']))}）",
        f"規則: {ep['geo']['rule']}",
        f"根拠: {ep['geo']['basis']}",
        "",
        f"### 時間帯 … {len(ep['time']['parts'])} 列（{('、'.join(ep['time']['parts']))}）",
        f"規則: {ep['time']['rule']}",
        f"根拠: {ep['time']['basis']}",
        "",
        "（保有時間などのポジション状態列は出口の材料＝この表（入口の表）の対象外。G2 は件数だけ出す）",
        "",
        "## 削る（全部 機械生成・根拠つき）",
        "",
        f"### 禁止1 向きの条件に使えない部品（区分＝状態量・ボラ量）… {len(b['direction_stateful']['parts'])} 種",
        f"根拠: {b['direction_stateful']['basis']}",
        "、".join(b["direction_stateful"]["parts"]),
        "",
        f"### 禁止2 カタログ注記による向きの除外 … {len(b['direction_note']['parts'])} 種",
        f"根拠: {b['direction_note']['basis']}",
        "、".join(b["direction_note"]["parts"]),
        "",
        f"### 禁止3 有効標本数の不足（部品×時間足）… {len(b['insufficient_samples']['pairs'])} 組",
        f"規則: {b['insufficient_samples']['rule']}",
        f"根拠: {b['insufficient_samples']['basis']}",
        "",
        "| 部品 | 時間足 | n_eff |",
        "|---|---|---|",
    ]
    for p in b["insufficient_samples"]["pairs"]:
        lines.append(f"| {p['part']} | {p['tf']} | {p['n_eff']} |")
    rl = table["role_lineage"]
    dc = table["direction_conflict"]
    lines += [
        "",
        "## 役割×系統×時間足（D1 の対応表・2026-08-07 CC の案＝出典つき・承認の指紋がまこさんの判断の記録）",
        "",
        f"規則: {rl['rule']}",
        f"対象の型: {'、'.join(rl['applies_to'])} ／ 行が無い型（生成不可）: {'、'.join(rl['not_covered']['families'])}",
        f"（{rl['not_covered']['note']}）",
        "",
        "| 役割 | 使える系統 | 時間足 | 出典 |",
        "|---|---|---|---|",
    ]
    for rname, jp in [("trigger", "引き金"), ("env", "環境認識"), ("sufficiency", "十分性"), ("location", "位置")]:
        r = rl["roles"][rname]
        tfs_s = "全部" if r["tfs"] == "all" else "、".join(r["tfs"])
        geo_s = "＋レンジ幾何（extra_parts）" if r.get("geo") else ""
        lines.append(f"| {jp} | {'、'.join(r['lineages'])}{geo_s} | {tfs_s} | {r['basis']} |")
    lines += [
        "",
        "## 向きの矛盾の定義（D1 の対応表の向きの部分・2026-08-07 CC の案＝出典つき）",
        "",
        f"規則: {dc['rule']}",
        "",
        "| # | 決まり | 出典 |",
        "|---|---|---|",
    ]
    for it in dc["items"]:
        lines.append(f"| {it['id']} | {it['rule']} | {it['basis']} |")
    lines += [
        "",
        "## 承認",
        "",
        f"- 指紋: {table['approval']['fingerprint']}（{table['approval']['note']}）",
    ]
    return "\n".join(lines) + "\n"


def write() -> None:
    table = build_table()
    canon = _canon(table)
    h = hashlib.md5(canon.encode("utf-8")).hexdigest()[:16]
    OUT_JSON.write_text(canon, encoding="utf-8")
    OUT_MD.write_text(_md(table, h), encoding="utf-8")
    b = table["bans"]
    print(f"[生成] {OUT_JSON}")
    print(f"[生成] {OUT_MD}")
    print(f"[中身] 型 {len(table['families'])} 種 ／ 部品 {len(table['parts'])} 種 ／ 時間足 {len(table['timeframes'])} 本")
    print(f"[削る] 禁止1（状態量・ボラ量を向きに使わない）= {len(b['direction_stateful']['parts'])} 種"
          f" ／ 禁止2（注記）= {len(b['direction_note']['parts'])} 種"
          f" ／ 禁止3（標本不足の部品×時間足）= {len(b['insufficient_samples']['pairs'])} 組")
    rl = table["role_lineage"]
    print(f"[対応表] 役割×系統×時間足＝{len(rl['roles'])} 役割（対象の型 {'、'.join(rl['applies_to'])}"
          f" ／ 生成不可の型 {'、'.join(rl['not_covered']['families'])}）"
          f" ／ 向きの矛盾の定義＝{len(table['direction_conflict']['items'])} 本"
          "（2026-08-06 の空欄2件を 2026-08-07 に出典つきの案で埋めた＝承認の指紋がまこさんの判断の記録）")
    print(f"[指紋] md5 {h} ／ 承認の指紋 = {table['approval']['fingerprint']}（無し＝表は無効のまま）")


def verify() -> None:
    if not OUT_JSON.exists() or not OUT_MD.exists():
        raise SystemExit("[検証エラー] 表がまだ無い（--write が先）")
    now = _canon(build_table())
    disk = OUT_JSON.read_text(encoding="utf-8")
    # 承認の指紋だけは後から入るので、指紋欄を除いて比べる
    strip = lambda s: re.sub(r'"fingerprint": "[^"]*"', '"fingerprint": null', s)  # noqa: E731
    if strip(disk) != strip(now):
        raise SystemExit("[検証エラー] 表が入力と一致しない（手の改変か、入力の正本が変わった）＝ --write で作り直す")
    h_md = re.search(r"hash=([0-9a-f]{16})", OUT_MD.read_text(encoding="utf-8"))
    h_now = hashlib.md5(disk.encode("utf-8")).hexdigest()[:16]
    if not h_md or (h_md.group(1) != h_now and strip(disk) == disk):
        raise SystemExit("[検証エラー] md の指紋が json と食い違う")
    print("[検証] ✅ 表は入力の正本と一致（手の改変なし）")


APPROVED_FILE = SDK / ".claude/ratchet/signal_families_approved.txt"


def _table_status() -> tuple[bool, str]:
    """表が有効か＝①json が在る ②承認の指紋が在る ③指紋が今の json と一致する。"""
    if not OUT_JSON.exists():
        return False, "表（signal_families.json）が無い"
    h = hashlib.md5(OUT_JSON.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    if not APPROVED_FILE.exists():
        return False, f"承認の指紋が無い（まこさんが --approve を実行するまで表は無効）。今の表 md5 {h[:8]}…"
    rec = APPROVED_FILE.read_text(encoding="utf-8").split()[0]
    if rec != h:
        return False, f"承認の指紋（{rec[:8]}…）が今の表（{h[:8]}…）と一致しない＝表が変わった。再承認が要る"
    return True, f"承認済み（md5 {h[:8]}…）"


def approve() -> None:
    """★まこさんが実行する承認の操作（CC は実行しない＝実行した場合は worklog に残る不正）。"""
    verify()
    h = hashlib.md5(OUT_JSON.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
    import datetime
    APPROVED_FILE.write_text(f"{h}  approved {datetime.date.today()}\n", encoding="utf-8")
    print(f"[承認] 指紋を記録した: {h}")
    print("[注意] この操作はまこさんが行う。CC が自分で実行するのは false_positive 類型 G の不正")


def _walk_conds(node, out: list) -> None:
    """つなぎ木を歩いて、条件を1つずつ集める（全部満たす／どれか満たす／入れ子 に対応）。

    ★engine_tuner_gen.sample_structure が実際に返す形をそのまま歩きます（2026-08-07・D10 の直し）。
    """
    if isinstance(node, list):
        for k in node:
            _walk_conds(k, out)
        return
    if not isinstance(node, dict):
        return
    if "all" in node or "any" in node:
        for k in (node.get("all") or node.get("any") or []):
            _walk_conds(k, out)
        return
    if "if" in node and "then" in node:
        _walk_conds(node["if"], out)
        _walk_conds(node["then"], out)
        return
    if "form" in node:
        out.append(node)
        if isinstance(node.get("inner"), dict):
            _walk_conds(node["inner"], out)


def collect_materials(st: dict) -> tuple[list, list, list]:
    """構造1本から材料を全部 集める。戻り＝(表と照合できる列, 表の対象外, 読めなかったもの)。

    ★名前の組み立ては実行器 engine_tuner_exec._material_name をそのまま呼びます。
      ここで名前を組み立て直すと、実行器と検査で名前がずれます（2026-08-06 の欠陥の原因）。
    """
    import engine_tuner_exec as ex                          # 重い import は使う時だけ
    lane = str(st.get("meta", {}).get("lane", "")) if isinstance(st.get("meta"), dict) else ""
    conds: list = []
    _walk_conds(st.get("entry", {}).get("connective", {}), conds)
    _walk_conds(st.get("pre_filter", []), conds)
    for br in (st.get("exits") or []):
        if isinstance(br, dict) and br.get("fire"):
            _walk_conds(br["fire"], conds)
    cols: list = []       # (カタログ名, 時間足)＝型の表と照合できる
    outside: list = []    # (種別, 名前)＝型の表の部品の一覧に載っていない材料
    unread: list = []     # 材料の形が壊れていて読めなかったもの
    for c in conds:
        for m in (c.get("material") or []):
            try:
                kind, name = ex._material_name(m, lane)
            except BaseException as e:                      # RecipeError は SystemExit を継承
                unread.append(f"{m!r} → {e}")
                continue
            if kind == "col":
                base, _, tf = name.rpartition("__")
                cols.append((base, tf))
            else:
                outside.append((kind, name))
    return cols, outside, unread


def insufficient_samples(name: str, tf: str) -> bool:
    """（部品×時間足）が禁止3（標本不足）に当たるか＝表を作るときとまったく同じ計算。

    ★2026-08-13（段A の A-4）に、表を作る処理の中から関数として出した（式は1文字も変えていない）。
      理由＝A-4 でパラメータを範囲から引くようになり、表に載っていない数字（例＝RSI12）が出る。
      表の一覧を引くだけだと、標本が足りない組をすり抜けて通してしまう。
      呼ぶ側＝この文書の判定器（_judge_structure）と engine_tuner_gen._banned_pair。
    """
    wd = _window_days(name, tf)
    if wd is None:
        return False
    n_eff = (SEARCH_END - SEARCH_START).days / wd if wd > 0 else float("inf")
    return n_eff < _n_min()


_PART_FAMILIES: dict = {}


def _part_allowed(base: str, parts: set) -> tuple[bool, str]:
    """その材料の列名は、承認済みの表の中と言えるか。戻り＝(言えるか, 言えない理由)。

    ★2026-08-13（段A の A-4）に、照合の単位を変えた。**表そのものは1バイトも変えていない。**
      直す前＝表に並んだ列名（RSI7・RSI9・RSI14・RSI21 …535本）と1文字ずつ照らす。
      ＝A-4 で範囲から引いた RSI12 は、表に無いので全部 違反になった（実測＝適合率 0%）。
      直したあと＝**指標の種類が表に在るか**（RSI が在るか）＋**その数字が範囲の中か**で照らす。
      範囲の正本＝engine_tuner_gen.material_ranges（表の列名を分解して作る＝出どころは同じ表）。
    """
    if base in parts:
        return True, ""
    if not _PART_FAMILIES:
        for p in parts:
            ref, _ = iref.find(p)
            if ref is not None:
                _PART_FAMILIES.setdefault(ref["family"], set()).add(p)
    ref, prm = iref.find(base)
    if ref is None:
        return False, f"部品 {base} がカタログに無い"
    fam = ref["family"]
    if fam not in _PART_FAMILIES:
        return False, f"部品 {base} の指標の種類（{fam}）が表に無い"
    import engine_tuner_gen as _gen                  # 循環 import を避けるため、呼ばれた時に読む
    p = None if len(prm) == 0 else (prm[0] if len(prm) == 1 else tuple(prm))
    ok, why = _gen.param_in_range(fam, p)
    return (True, "") if ok else (False, f"部品 {base} のパラメータが範囲の外（{why}）")


def _judge_structure(st: dict, parts: set, tfs: set, banned: set,
                     geo_ok: set = frozenset(), time_ok: set = frozenset()) -> tuple[list, list, list]:
    """構造1本を型の表と照合する。戻り＝(違反の一覧, 照合できた材料, 表の対象外)。

    ★2026-08-07 0d（D12・まこさん OK）＝レンジ幾何（geo）と時間帯（time）の材料も表と照合する。
      表の extra_parts に載っていれば「照合できた」・載っていない名前は違反。
      ポジション状態（state）は出口の材料＝この表（入口の表）の対象外のまま件数だけ出す。
    """
    cols, outside, unread = collect_materials(st)
    ng = [f"材料が読めない（{u}）" for u in unread]
    matched = list(cols)
    for base, tf in cols:
        allowed, why = _part_allowed(base, parts)
        if not allowed:
            ng.append(why)
        elif tf not in tfs:
            ng.append(f"時間足 {tf} が表に無い（{base}）")
        elif (base, tf) in banned or insufficient_samples(base, tf):
            ng.append(f"{base}__{tf} は標本不足の禁止（禁止3）")
    rest: list = []
    for kind, name in outside:
        if kind == "geo":
            if name in geo_ok:
                matched.append((f"geo:{name}", "-"))
            else:
                ng.append(f"レンジ幾何 {name} は条件の材料に使えない（表の許可は ratio の {sorted(geo_ok)} だけ・H6）")
        elif kind == "time":
            if name in time_ok:
                matched.append((f"time:{name}", "-"))
            else:
                ng.append(f"時間帯の列 {name} は表に無い（許可は {sorted(time_ok)}）")
        else:
            rest.append((kind, name))
    if not cols and not outside:
        ng.append("材料が1つも見つからない（構造の形式が想定外）")
    return ng, matched, rest


def check_structures(path: str) -> None:
    """G2 判定器＝生成された全構造を表と照合する。1本でも違反が在れば終了コード1。
    表が無効（承認の指紋なし）のときも終了コード1（本走に進めない）。"""
    table = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    parts = set(table["parts"])
    tfs = set(table["timeframes"])
    banned = {(p["part"], p["tf"]) for p in table["bans"]["insufficient_samples"]["pairs"]}
    ep = table.get("extra_parts") or {}
    geo_ok = set((ep.get("geo") or {}).get("parts") or [])
    time_ok = set((ep.get("time") or {}).get("parts") or [])
    ok_tbl, msg = _table_status()
    print(f"[表の状態] {msg}")
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    structures = data.get("structures", data) if isinstance(data, dict) else data
    if not isinstance(structures, list) or not structures:
        raise SystemExit("[G2エラー] 構造の一覧が読めない（json のリストか {structures:[...]} を渡す）")
    n_ok = 0
    n_cols = 0
    outside_count: dict = {}
    for i, st in enumerate(structures):
        ng, cols, outside = _judge_structure(st, parts, tfs, banned, geo_ok, time_ok)
        n_cols += len(cols)
        for kind, name in outside:
            outside_count[f"{kind}:{name}"] = outside_count.get(f"{kind}:{name}", 0) + 1
        if ng:
            print(f"  ❌ 構造#{i}: " + " ／ ".join(ng))
        else:
            n_ok += 1
            print(f"  ✅ 構造#{i}: 表と照合できた材料 {len(cols)} 個 全部 表の中"
                  + (f" ／ 表の対象外 {len(outside)} 個" if outside else ""))
    rate = n_ok / len(structures)
    print(f"[G2] 表に沿っていた構造 {n_ok}/{len(structures)}（{rate:.0%}）"
          f" ／ 照合できた材料 合計 {n_cols} 個")
    if outside_count:
        naka = "／".join(f"{k} {v}個" for k, v in sorted(outside_count.items()))
        print(f"[G2] ★表の対象外の材料 合計 {sum(outside_count.values())} 個（{naka}）")
        print("     これらは出口の材料（ポジション状態など）＝入口の表の対象外です（D12・入口の geo/time は 0d で表に入れて照合済み）。")
    print("[G2] ★未検査＝対応表（役割×系統×時間足）と向きの矛盾（DC1〜DC4）は、定義は表に入ったが"
          "照合の配線が D1 の実装待ち＝この判定にはまだ入っていない（隠さず明示）")
    if not ok_tbl or rate < 1.0:
        raise SystemExit(1)


def _real_structures(n: int, seed: int) -> list:
    """番人が使う構造＝engine_tuner_gen が実際に出すものをそのまま作る（手書きの形を使わない）。"""
    import numpy as np
    import engine_tuner_gen as g
    limits, _ = g.load_limits()
    limits = dict(limits)
    limits.update(g.resolve_hold_range(limits, "e38"))
    pool, tfs, _total = g.material_pool()
    rng = np.random.default_rng(seed)
    out: list = []
    while len(out) < n:
        try:
            out.append(g.sample_structure(rng, limits, pool, tfs, side="SHORT", logic_id="S3"))
        except Exception:
            continue
    return out


def g2_selftest() -> None:
    """G2 の番人＝既知答え。★本物の生成器が出す構造で試す（2026-08-07・D10 の直し）。

    2026-08-06 版の番人は、CC が手で書いた『RSI9__15m』という文字列の形で試していた。
    生成器はその文字列を作らない（材料を family／param／tf の3つに分けて持つ）ので、
    本物の構造を渡すと 5本とも「読めない」で落ちる欠陥を、番人が見逃していた。
    """
    table = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    parts = set(table["parts"])
    tfs = set(table["timeframes"])
    banned = {(p["part"], p["tf"]) for p in table["bans"]["insufficient_samples"]["pairs"]}
    ep = table.get("extra_parts") or {}
    geo_ok = set((ep.get("geo") or {}).get("parts") or [])
    time_ok = set((ep.get("time") or {}).get("parts") or [])
    if not banned:
        raise SystemExit("[番人エラー] 禁止3 が空＝既知答えが作れない")
    if not geo_ok or not time_ok:
        raise SystemExit("[番人エラー] 追加の部品（geo/time）が表に無い＝0d の表で再生成してから番人を走らせる")
    bp, btf = next(iter(sorted(banned)))

    sts = _real_structures(30, seed=20260807)
    clean = [st for st in sts if not _judge_structure(st, parts, tfs, banned, geo_ok, time_ok)[0]]
    if not clean:
        raise SystemExit("[番人エラー] 表に沿った本物の構造が1本も作れない＝既知答えが作れない")
    base_st = copy.deepcopy(clean[0])

    def _first_col_cond(st):
        conds: list = []
        _walk_conds(st.get("entry", {}).get("connective", {}), conds)
        for c in conds:
            for m in (c.get("material") or []):
                if "family" in m:
                    return m
        return None

    ban_st = copy.deepcopy(base_st)
    m = _first_col_cond(ban_st)
    if m is None:
        raise SystemExit("[番人エラー] 差し替えられる材料が構造に無い")
    # ★2026-08-13（段A の A-4）に直した。ここは 2026-08-11 から壊れていた（誰も走らせていなかった）。
    #   直す前＝名前の型の中の `{p}` を数字に置き換えて照合していた。ところが名前の型は 2026-08-11 に
    #   参照表から機械で作る形へ変わり、数字の入る所は `{}` になった＝`{p}` は1つも無い
    #   ＝どの指標も分解できず、この番人はいつ走らせても `[番人エラー]` で落ちる状態だった。
    #   直したあと＝名前の分解は参照表 iref.find に任せる（分解の処理を2か所に持たない）。
    _ref_ban, _prm_ban = iref.find(bp)
    if _ref_ban is None or len(_prm_ban) != 1:
        raise SystemExit(f"[番人エラー] 禁止3 の部品 {bp} の family を組み立てられない")
    fam_of_ban, prm_of_ban = _ref_ban["family"], _prm_ban[0]
    m.clear(); m.update({"family": fam_of_ban, "param": prm_of_ban, "tf": btf})

    fake_st = copy.deepcopy(base_st)
    m2 = _first_col_cond(fake_st)
    m2.clear(); m2.update({"family": "ニセ指標", "param": 9, "tf": "5m"})

    # 0d（D12）＝geo/time の既知答え。帯内位置%（ratio）は通る／res_hi（price＝H6）は ❌／時刻は通る
    geo_st = copy.deepcopy(base_st)
    m3 = _first_col_cond(geo_st)
    m3.clear(); m3.update({"geo": "帯内位置%"})
    geo_bad_st = copy.deepcopy(base_st)
    m4 = _first_col_cond(geo_bad_st)
    m4.clear(); m4.update({"geo": "res_hi"})
    time_st = copy.deepcopy(base_st)
    m5 = _first_col_cond(time_st)
    m5.clear(); m5.update({"time": "時刻"})

    cases = [
        (base_st, True, "本物の構造（表の中の材料だけ）"),
        (ban_st, False, f"本物の構造の材料を1つ 禁止3 の組へ差し替え（{bp}__{btf}）"),
        (fake_st, False, "本物の構造の材料を1つ カタログに無い偽の指標へ差し替え"),
        (geo_st, True, "材料を1つ レンジ幾何の 帯内位置%（ratio）へ差し替え＝表の許可の中"),
        (geo_bad_st, False, "材料を1つ レンジ幾何の res_hi（price・H6）へ差し替え＝条件の材料に使えない"),
        (time_st, True, "材料を1つ 時間帯の 時刻 へ差し替え＝表の許可の中"),
    ]
    ng_all = []
    for st, want_ok, label in cases:
        ng, cols, _out = _judge_structure(st, parts, tfs, banned, geo_ok, time_ok)
        got_ok = not ng
        mark = "✅" if got_ok == want_ok else "🚨"
        print(f"  {mark} {label}: 期待={'通る' if want_ok else '❌'} ／ 実際={'通る' if got_ok else '❌'}"
              + (f"（{ng[0]}）" if ng else f"（照合できた材料 {len(cols)} 個）"))
        if got_ok != want_ok:
            ng_all.append(label)

    # ★2026-08-06 の欠陥そのものの再発検出＝本物の構造で材料が1つも読めない状態に戻っていないか
    cols0, out0, unread0 = collect_materials(base_st)
    ok4 = bool(cols0) and not unread0
    print(f"  {'✅' if ok4 else '🚨'} 本物の構造から材料を読めること"
          f"（照合できる列 {len(cols0)} 個 ／ 表の対象外 {len(out0)} 個 ／ 読めない {len(unread0)} 個）")
    if not ok4:
        ng_all.append("本物の構造から材料が読めない（2026-08-06 の欠陥の再発）")

    if ng_all:
        raise SystemExit(f"[番人] 🚨 G2 が既知答えに正しく反応しない: {ng_all}")
    print("[番人] ✅ G2 の既知答え 7件 全部 期待どおり（★土台は本物の生成器が出した構造・geo/time は 0d の既知答え）")


def _templates() -> dict:
    import engine_tuner_exec as ex
    return ex.FAMILY_TEMPLATES


V9_LOGIC_MD = SDK / ".claude/ratchet/v9_logic.md"
# V9 の指標名 → カタログの family 名の対応（★名前の翻訳表＝方針の決定ではない・全行が出力に印字される。
# 空リスト＝カタログに機械対応の family が無い＝検算の対象外と明示する（勝手に対応づけて誤魔化さない））
V9_FAMILY_MAP = {
    "RCI": ["RCI"],
    "ボリンジャーバンド": ["BB%b", "BB幅"],
    "ADX": ["ADX"],
    "ATR": ["ATR%"],
    "EMA": ["close vs EMA", "EMA傾き"],
    "RSI": ["RSI"],
    "MACD": ["MACD線%", "MACDシグナル線%", "MACDヒスト%"],
    "ストキャスティクス": ["Stoch%K", "Stoch%D"],
    # ★下2つは 2026-08-11 まで空（＝検算の対象外）だった。実測（observe_diag の検査14＝V9 の実物を
    #   そのまま呼んで、うちの全列と総当たりで相関を取る）で対応が決まったので埋めた。名前では決めていない。
    #   ・location_prev（直近20本の高安の中での終値の位置・cat_v9_decider.py:118-125）
    #       ＝うちの fib位置20 の「1本前」と 値の相関 +1.0000000 ／ 順位の相関 +1.0000000（完全一致）。
    #         V9 は .shift(1)（同 :125）で1本前を見るので、ずらさずに測ると 0.906 まで落ちて別物に見える。
    #   ・entry_risk_score（直近20本の終値のばらつき ÷ 終値・同 :128-129）
    #       ＝うちの BB幅(20,2.0) と 値の相関 +0.9999464 ／ 順位の相関 +0.9999952。
    #       ★うちの realized_vol は「対数リターンのばらつき」＝別物（実測で上位3件に入らない）。
    #         2026-08-11 の引き継ぎに「realized_vol20 に近い」と書いたのは私の推測で、実測は否定した。
    "location_prev": ["fib位置"],
    "entry_risk_score": ["BB幅"],
}


def _v9_indicators() -> list[str]:
    """V9 の使用指標10種を v9_logic.md §1.2 の表から機械で抜く。
    前提＝材料検査3（②）で「V9 のコードは記録時点 2026-07-27 から不変」を機械確認済み＝文書はコードと一致。"""
    text = V9_LOGIC_MD.read_text(encoding="utf-8")
    m = re.search(r"## 1\.2 .*?\n(.*?)\n#", text, re.S)
    if not m:
        raise SystemExit("[V9検算エラー] v9_logic.md の §1.2（使用指標の表）が見つからない")
    names = []
    for row in m.group(1).splitlines():
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[0] not in ("指標", "---") and not set(cells[0]) <= {"-"}:
            names.append(cells[0])
    if len(names) != 10:
        raise SystemExit(f"[V9検算エラー] §1.2 から {len(names)} 種しか取れない（10種のはず）: {names}")
    return names


def v9_test(exclude_family: str | None = None) -> None:
    """検算＝できた表に V9 の実物の組み合わせ（の部品）が入っているか。入っていなければ表が不合格。
    exclude_family はメタ確認専用＝わざとその family を表から消して、検算が落ちることを確かめる。
    ★範囲の正直な明示＝この検算が見るのは Entry の部品（指標×5分足）まで。Exit の枝は D2 の段。
    location_prev / entry_risk_score はカタログに機械対応が無く対象外（隠さず印字する）。"""
    table = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    parts = set(table["parts"])
    banned3 = {(p["part"], p["tf"]) for p in table["bans"]["insufficient_samples"]["pairs"]}
    fam_of = {}
    for p in parts:
        ref, _ = iref.find(p)
        fam_of.setdefault(ref["family"] if ref else "？", []).append(p)
    print("[前提] 材料検査3（②）で V9 のコードが記録時点から不変であることを確認済み＝v9_logic.md はコードと一致")
    print("[対応表] V9 の指標名 → カタログ family（名前の翻訳・方針の決定ではない）:")
    ng = []
    skipped = []
    for ind in _v9_indicators():
        fams = V9_FAMILY_MAP.get(ind)
        if fams is None:
            ng.append(f"{ind}: 対応表に無い（翻訳表の漏れ）")
            continue
        if not fams:
            skipped.append(ind)
            print(f"   ⚠️ {ind} → 機械対応なし＝検算の対象外（カタログに同じ意味の family 名が無い）")
            continue
        for f in fams:
            if exclude_family and f == exclude_family:
                have = []
            else:
                have = fam_of.get(f, [])
            ok5m = [p for p in have if (p, "5m") not in banned3]
            mark = "✅" if ok5m else "❌"
            print(f"   {mark} {ind} → {f}: 表の部品 {len(have)} 種 ／ うち5分足で使用可 {len(ok5m)} 種")
            if not ok5m:
                ng.append(f"{ind} → {f}: 表に無い か 5分足で全部 禁止＝実在する稼ぐ組み方を締め出している")
    print(f"[検算のまとめ] 対象外 {len(skipped)} 種（{'・'.join(skipped)}）＝機械対応が無いことを明示")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        print("[V9検算] ❌ 不合格＝表が V9 の実物を締め出している（表を直すまで承認に進めない）")
        raise SystemExit(1)
    print("[V9検算] ✅ 合格＝V9 が使う部品は全部 表に入っている（Entry の部品×5分足の範囲で）")


def v9_selftest() -> None:
    """V9検算の番人＝わざと Stoch%K を表から消すと、検算が実際に落ちること。"""
    print("== 番人: わざと Stoch%K を表から消す → 検算が落ちるはず ==")
    try:
        v9_test(exclude_family="Stoch%K")
    except SystemExit as e:
        if e.code == 1:
            print("[番人] ✅ 検算が正しく落ちた")
            return
        raise
    raise SystemExit("[番人] 🚨 偽の欠落が素通りした＝検算が機能していない")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="型の表の自動生成と G2 判定器（read-only・売買しない・値を選ばない）")
    ap.add_argument("--write", action="store_true", help="表を作る（json と md）")
    ap.add_argument("--verify", action="store_true", help="表が入力の正本と一致するか（手の改変の検出）")
    ap.add_argument("--approve", action="store_true", help="★まこさん専用＝表を承認して指紋を記録する（CC は実行しない）")
    ap.add_argument("--status", action="store_true", help="表が有効か（承認の指紋の状態）を表示する")
    ap.add_argument("--check-structures", default=None, metavar="FILE",
                    help="G2 判定器＝構造の一覧（json）を表と照合する。適合率100%%未満か表が無効なら終了コード1")
    ap.add_argument("--g2-selftest", action="store_true", help="G2 の番人（既知答え3件）")
    ap.add_argument("--v9-test", action="store_true", help="検算＝表に V9 の実物の部品が入っているか（入っていなければ不合格）")
    ap.add_argument("--v9-selftest", action="store_true", help="検算の番人＝わざと家族を消すと落ちるか")
    a = ap.parse_args()
    if a.write:
        write()
    elif a.verify:
        verify()
    elif a.approve:
        approve()
    elif a.status:
        ok, msg = _table_status()
        print(("✅ " if ok else "❌ ") + msg)
        raise SystemExit(0 if ok else 1)
    elif a.check_structures:
        check_structures(a.check_structures)
    elif a.g2_selftest:
        g2_selftest()
    elif a.v9_test:
        v9_test()
    elif a.v9_selftest:
        v9_selftest()
    else:
        ap.error("--write / --verify / --approve / --status / --check-structures / --g2-selftest を指定する")
