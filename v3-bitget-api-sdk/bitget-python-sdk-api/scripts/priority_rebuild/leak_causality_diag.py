#!/usr/bin/env python3
"""leak_causality_diag.py — H2（leak なし）を「動かした結果」で確かめる読み取り専用の診断（2026-08-09 まこさん OK）

■ 何のための道具か
H2 は要件定義書 §4.6 の2番目の決まり＝「未来のデータを使って良い成績を出さないこと」。
これまでの担保は2つとも「書き方を見張る」やり方だった（shift にマイナスを渡す書き方と、
rolling の center を True にする書き方の、2種類を探す）。2026-08-09 に実測して、穴が5つ 出た。

  穴① 「# H2OK: 理由」の中身を機械が見ない（嘘の理由でも通る）
  穴② 新しく書く行だけが対象＝既に書いてあるコードは見ない
  穴③ 探している書き方が2種類だけ（iloc[i+3] や df.max() は素通りする＝実測で確認）
  穴④ 実行するときの見張り（ratchet_guards.assert_no_future_ref）を呼んでいるのは 78本中1本だけ
  穴⑤ 説明文で誤発火する（本ファイルを書く時に実際に止まった＝コメントや文章を外してから見ていない）

未来を見る書き方は数え切れないので、「書き方を見張る」やり方では原理的に完全にならない。
そこで本道具は **書き方を一切 見ない**。動かした結果だけで判定する。

■ やり方＝打ち切り再現テスト
同じものを2回 走らせる。1回目はデータを最後まで渡す。2回目はデータを途中の日付 CUT で切って渡す。
CUT より前の結果が1つでも違えば、それは CUT より後のデータを見ていたということ＝leak。

  検査1-a｜指標の突き合わせ（速い・列の名前まで分かる）
      _load が作る全30列を、打ち切りあり/なしで1セルずつ突き合わせる。
      ts < CUT の行が1セルでも違えば、その列は未来を見ている。
      ★局所的な未来参照（6本先の値を今の行に置く型）はここで捕まる＝CUT の直前 6 行がずれるため。

  検査1-b｜売買記録の突き合わせ（遅い・売買ループ自体を見る）
      E38 を2回 走らせ、CUT より前に決済が終わった売買を、CUT の直前の玉まで1行ずつ突き合わせる。
      ★売買ループの中で先の足を覗く型（出口判定が未来を走査する等）は、覗いた先が CUT を越える玉
        （＝CUT の直前の玉）で違いが出るので、ここで捕まる（番人1c-4 が実物で確かめる）。
      境目の扱い＝CUT の時点でまだ持っている玉は、打ち切り側だけ強制決済される（決済理由 FORCE_CLOSE_EOD）。
      それは未来参照ではなくデータの終わりの都合なので、**その玉だけを名指しで外す**。
      ★2026-08-23（74番）に直した＝直す前は「CUT−3日 より前の玉だけ」を比べていたので、3日（864本）
        より近くを覗く型が捕まらなかった（余白の中に違いが出る玉が居た）。余白の既定は 0 日にした。

  検査2｜既存コードの全数スキャン（穴② に対応）
      scripts/priority_rebuild の .py を全部 見て、注記なしの未来参照パターンを出す。
      ★これは既存 hook と同じ探し方なので、同じ限界を持つ（穴③ は塞がらない）。おまけ。
      ただし穴⑤ は塞いだ＝コメントを外してから見るので、説明文では誤発火しない。

  検査3｜番人（この検査自体が壊れていないかのメタ確認）
      わざと未来を見る細工を入れて、検査1-a・1-b が本当に落ちるかを確かめる。
      落ちなければ検査が壊れている＝この道具の出す ✅ は信用できない。

■ 限界（正直に）
  ・未来を見ていても、その未来の値がたまたま結果を変えなかった場合は捕まらない。
    → 打ち切る日付を複数にして減らす（既定2点）。
  ・走る時間が増える（打ち切り点の数だけ走らせ直す）。だから毎回でなく採点の前に1回 掛ける。
  ・本道具は「この設定・この期間で leak が出なかった」しか言えない。設定を変えたら測り直す。

■ 読み取り専用（診断レーン）
  売買記録のファイルを1つも出さない。審判を呼ばない。採用の書き出しをしない。
  戦略の実関数を import して呼ぶだけ（cat_requirements 診断レーン免除の条件どおり）。

  検査1-c｜engine_tuner の経路の打ち切り再現テスト（2026-08-16 まこさん GO「H2 完全化」の層3）
      探索が実際に使う道具立て（接続ファイルのデータ準備 → 実行器 run_recipe）を、打ち切りあり/なしで
      走らせて突き合わせる。①データの全列（探索の指標の経路）②売買（恒等3本＝S2・L1・S1 ＋
      種を固定した生成の案）。分位の解決表（qtable）は探索の実物と同じく「窓から1回 固定」＝
      両方の走行で同じものを使う（値の選定であって leak ではない・H8 値決め窓の中）。
      番人3本を同梱（データ経路の細工を見つける／レシピが毎回 同じ／同じ入力なら同じ出力）。

使い方:
  python3 scripts/priority_rebuild/leak_causality_diag.py --selftest   # 検査3 だけ（番人）
  python3 scripts/priority_rebuild/leak_causality_diag.py --scan       # 検査2 だけ（全数スキャン・一瞬）
  python3 scripts/priority_rebuild/leak_causality_diag.py --features   # 検査1-a だけ（指標の突き合わせ）
  python3 scripts/priority_rebuild/leak_causality_diag.py --tuner      # 検査1-c だけ（engine_tuner の経路）
  python3 scripts/priority_rebuild/leak_causality_diag.py              # 検査2 → 3 → 1-a → 1-b → 1-c の順に全部

★検査済みの印（層2・enforce_h2_pass hook と対）:
  全部の検査が pass したときだけ、この道具が .claude/state/h2_pass.json に「対象のコードと設定の
  指紋」を書く。engine_tuner・実行器・生成器・E38 は、この印がいまの指紋と一致しないと回れない
  （enforce_h2_pass hook が実行前に止める）＝コードか設定が1文字でも変わったら、検査し直すまで
  探索は物理的に回らない。
"""
from __future__ import annotations
import argparse
import hashlib
import inspect
import json
import pathlib
import sys
import time

import pandas as pd

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

import periods                      # noqa: E402  検証期間の唯一の正本（SSOT・自前で日付を書かない）
import e37_scalp as e37             # noqa: E402  実エンジン（S1/L1 の売買ループ・データ読み込み口）
import e38_logic_parts              # noqa: E402  汎用ロジックの売買部品（S2〜L5）
import e38_priority_stack as e38    # noqa: E402  E38 の設定解釈（load_logic_config / build_run_kwargs）

# ══ 探し方の正本＝hook（require_leak_annotation.py）そのもの ═══════════════════════════
#   ★2026-08-21（48回目・M2-2-8）に、書き写しをやめて hook の関数を直接 呼ぶ形にした。
#     直す前＝同じ正規表現を hook と ここの2か所に書き写していた。
#     何が起きたか＝41番（説明の文章の中の語で誤って止まる）を hook だけ直したら、
#     **この検査だけが古い探し方のまま残り、H2 の検査が落ちた**（2026-08-21 に実際に起きた）。
#     ＝「hook と同じ探し方」と説明文に書いてあっても、写しは黙ってずれる。
#   ★2026-08-23（54回目・77番）＝読み込む処理を h2_scan.py（共有モジュール）へ移した。
#     理由＝observe_diag の検査4 が同じ型（古い探し方のまま）で誤って ❌ を出していた＝使う側が2つに
#     なったので、読み込む処理も1か所にする。fail-closed は h2_scan の中（正本が無ければ止まる）。
import h2_scan                      # noqa: E402

SCAN_PAT = h2_scan.PAT                     # 表示・番人のためだけに持つ（判定は find_bad が行う）
SCAN_DIR = HERE.parent
# 突き合わせから外す列（診断のための記録で、売買の判断にも net にも関与しない）
IGNORE_COLS = ("logic",)


# ============================================================================
# 検査2｜既存コードの全数スキャン（穴② に対応・探し方は hook と同じなので穴③ は塞がらない）
# ============================================================================
def scan_line(line: str) -> bool:
    """1行が「注記なしの未来参照」か。★判定は hook の関数がする（写しを持たない・h2_scan 経由）。"""
    return h2_scan.scan_line(line)


def scan_text(text: str) -> list[tuple[int, str]]:
    """ファイルの全文を見て、注記なしの未来参照の行を返す。★判定は hook の関数がする。

    ★1行ずつでなく全文を渡す理由＝説明の文章（docstring）は複数行にまたがるので、
      1行だけ見ても「いま文字列の中か」が分からない（2026-08-21 に この取り違えで H2 が落ちた）。
    """
    return h2_scan.scan_text(text)


def scan_existing_code() -> list[tuple[str, int, str]]:
    """scripts/priority_rebuild の .py を全部 見て、注記なしの未来参照パターンを返す。

    除外＝build_labels で始まるファイル（教師ラベル生成が本業＝学習窓内で正当）／
    本ファイル自身と ratchet_guards.py（探すパターンの文字列を持っているだけ）。
    """
    skip_names = {HERE.name, "ratchet_guards.py"}
    hits: list[tuple[str, int, str]] = []
    files = sorted(p for p in SCAN_DIR.glob("*.py") if p.name not in skip_names and not p.name.startswith("build_labels"))
    for p in files:
        for i, line in scan_text(p.read_text(encoding="utf-8")):
            hits.append((p.name, i, line))
    print(f"[検査2] 全数スキャン: {len(files)} 本を見て、注記なしの未来参照パターン {len(hits)} 件")
    for name, i, line in hits[:20]:
        print(f"        {name}:{i}  {line}")
    if not hits:
        print("        ＝0件。ただしこれは既存 hook と同じ2種類の書き方しか見ていない（穴③ は塞がっていない）")
    return hits


# ============================================================================
# 走らせる部分（打ち切りあり/なし）
# ============================================================================
def _cut_loader(orig, cut):
    """生の5分足を CUT より前だけにして返す差し替え口（指標は打ち切った生データから作り直される）。"""
    def _f(smoke, *a, **kw):
        raw = orig(smoke, *a, **kw)
        return raw[raw["ts"] < cut].reset_index(drop=True)
    return _f


def load_features(cut=None, sabotage=None) -> pd.DataFrame:
    """_load（生データ読み込み＋指標付与）を1回 走らせて返す。cut=None なら打ち切らない。

    sabotage＝検査3（番人）用の細工。指標の1列をわざと未来の値に置き換える関数を渡す。
    """
    orig = e37.load_5m
    if cut is not None:
        e37.load_5m = _cut_loader(orig, cut)
    try:
        df = e37._load(0)
    finally:
        e37.load_5m = orig
    if sabotage is not None:
        df = sabotage(df)
    return df


def run_e38_trades(cut=None) -> pd.DataFrame:
    """E38 を1回 走らせて売買記録だけを返す（ファイルを1つも書かない）。

    e38_priority_stack.main() と同じ順番をなぞる＝設定を読む → 束ねる → データ → 汎用ロジック →
    モジュール定数の注入 → 実エンジン。違いは return_trades=True で書き出しをしないことだけ。
    """
    cfg = e38.load_logic_config(e38.DEFAULT_CONFIG)
    kw, const, _ = e38.build_run_kwargs(cfg)

    # ★2026-08-09 実測: build_run_kwargs は global.regime の鍵を「note 以外 全部」実エンジンへ渡す作りで、
    #   2026-08-03 の commit b0fc646 が name / entry_col / block_col / note_2026_08_03 を設定に足したため、
    #   E38 の本体（e38_priority_stack.py）はその日から実行の瞬間に落ちる（実測＝TypeError）。
    #   この4つは接続ファイルの regime() が使う名前で、実エンジンの引数ではない＝ここで外すのが正しい。
    #   ★本体は直していない（戦略ファイルの変更は承認が要る）。落ちている事実を毎回 画面に出す。
    valid = set(inspect.signature(e37.run_e37).parameters)
    dropped = sorted(k for k in kw if k not in valid)
    if dropped:
        kw = {k: v for k, v in kw.items() if k in valid}
        print(f"  ⚠️ E38 本体は実行できない状態です（2026-08-03 commit b0fc646 以降）。"
              f"実エンジンが受け取れない設定の鍵 {dropped} を、この診断の中だけで外して走らせました。")

    df = load_features(cut=cut)

    gen_rows: list = []
    gen_logics = [lg for lg in cfg["logics"] if lg["enabled"] and e38._is_generic(lg)]
    if gen_logics:
        adaptive_k = e37.V25_K if cfg["global"].get("regime", {}).get("v25_adaptive_band") else None
        # ★2026-10-21（工事 m2c15-band-s1-20261020・F-4・監査 CP83 の修正5）＝帯の1時間足の区切り（設定 global.regime.h1_edge）を渡す
        dfp = e38_logic_parts.prepare_df(df.copy(), adaptive_k=adaptive_k, h1_edge=cfg["global"]["regime"]["h1_edge"])
        for lg in sorted(gen_logics, key=lambda z: (int(z["priority"]), str(z["id"]))):
            args = (dfp, lg["entry"]["type"], lg["entry"]["params"], lg["exit"]["params"])
            mx = int(lg.get("params", {}).get("max_lots", 2))
            fn = e38_logic_parts.grid_loop if e38._entry_point(lg) == "grid_loop" else e38_logic_parts.generic_logic_loop
            gen_rows += fn(*args, max_lots=mx, logic_id=lg["id"])

    saved = {k: getattr(e37, k) for k in const}
    for k, v in const.items():
        setattr(e37, k, v)
    try:
        t = e37.run_e37(df, cfg["global"]["box_tf"], tag=None, return_trades=True, **kw)
    finally:
        for k, v in saved.items():
            setattr(e37, k, v)

    if gen_rows:
        t = pd.concat([t, pd.DataFrame(gen_rows)], ignore_index=True)
    if len(t):
        t["entry_time"] = pd.to_datetime(t["entry_time"])
        t["exit_time"] = pd.to_datetime(t["exit_time"])
    return t


# ============================================================================
# 検査1-c｜engine_tuner の経路の打ち切り再現テスト（2026-08-16 まこさん GO「H2 完全化」の層3）
# ============================================================================
TUNER_QUICK_DAYS = 90          # 1-c の窓の長さ（値決め窓の先頭から・実行時間を抑える）
TUNER_CUT_DAYS = 45            # 打ち切り日（窓の先頭から何日目か）
TUNER_GEN_N = 3                # 種を固定した生成の案の本数
TUNER_SEED = 20260816          # 生成の種（固定＝打ち切りあり/なしで同じ案になる）

ROOT = HERE.parents[4]                                   # cat-bitget（リポジトリの根）
H2_PASS = ROOT / ".claude" / "state" / "h2_pass.json"    # 検査済みの印（enforce_h2_pass hook が読む）
_PR = "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild"
WATCHED = [                                              # 指紋の対象＝engine_tuner の経路の実物ぜんぶ
    f"{_PR}/engine_tuner.py", f"{_PR}/engine_tuner_gen.py", f"{_PR}/engine_tuner_exec.py",
    f"{_PR}/e38_priority_stack.py", f"{_PR}/e38_logic_parts.py", f"{_PR}/e37_scalp.py",
    f"{_PR}/periods.py", f"{_PR}/e38_logics.json", f"{_PR}/leak_causality_diag.py",
    f"{_PR}/tuner_adapters/__init__.py", f"{_PR}/tuner_adapters/e37.py", f"{_PR}/tuner_adapters/e38.py",
    f"{_PR}/recipes/search_limits.json", f"{_PR}/recipes/identity_s2_legacy.json",
    f"{_PR}/recipes/identity_l1_legacy.json", f"{_PR}/recipes/identity_s1_legacy.json",
    "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.json",
    "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/exit_families.json",
    # ★2026-08-20（M2-1-9・まこさん OK）＝経路に載っているのに対象に無かった2本を足した（62番の穴）。
    #   engine_tuner_exec.py:1077 が observe_diag.build_features を呼ぶ＝この2本が変われば結果が変わりうる。
    f"{_PR}/observe_diag.py", f"{_PR}/observe_config.json",
    # ★2026-08-23（77番）＝探し方の正本を読む共有モジュール（検査2・検査4 が使う）。
    f"{_PR}/h2_scan.py",
    # ★2026-10-02（M2-F-6d の工事 A・L-8）＝札の部品と設定を印の対象に足す。観察の道具が読み込むのは工事 B（先に足しておけば、読み込んだ時から印が見張る）。
    f"{_PR}/regime_label.py", f"{_PR}/recipes/regime_label.json",
    # ★2026-08-30（M2-B0・まこさん承認 iter="m2-b0-law-reader-20260830"）＝場面の審査（G7）が読む
    #   相場の法則の正本。engine が読む設定は印の対象に入れる（2026-08-20 の observe_config.json と同じ型）。
    "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json",
]


def h2_fingerprint(root: pathlib.Path, files: list[str]) -> tuple[str, list[str]]:
    """対象ファイル一式の指紋。無いファイルは指紋に「無い」と刻む（黙って飛ばさない）。"""
    h = hashlib.sha256()
    missing = []
    for rel in sorted(files):
        p = root / rel
        h.update(rel.encode())
        if p.exists():
            h.update(hashlib.sha256(p.read_bytes()).digest())
        else:
            missing.append(rel)
            h.update(b"<missing>")
    return h.hexdigest(), missing


def _write_h2_pass() -> None:
    fp, missing = h2_fingerprint(ROOT, WATCHED)
    H2_PASS.parent.mkdir(parents=True, exist_ok=True)
    H2_PASS.write_text(json.dumps({
        "when": str(pd.Timestamp.now()).split(".")[0],
        "fingerprint": fp,
        "files": WATCHED,
        "missing": missing,
        "note": "leak_causality_diag の全部の検査（2→3→1-a→1-b→1-c）が pass したときにだけ、この道具が書く。"
                "対象のコードか設定が1文字でも変わると指紋が合わなくなり、enforce_h2_pass hook が"
                " engine_tuner を実行の前に止める。手でこのファイルを作るのは TODO_OK=1 の乱用と同じ明示の違反。",
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[H2 印] 検査済みの印を書いた: {H2_PASS}（指紋 {fp[:16]}…）")
    if missing:
        print(f"  ⚠️ 対象のうち実在しないファイル {len(missing)} 件（指紋には『無い』と刻んだ）: {missing}")


def _tuner_mods():
    import engine_tuner as tuner
    import engine_tuner_exec as ex
    import engine_tuner_gen as gen
    from tuner_adapters import e38 as ad
    return tuner, ex, gen, ad


def _tuner_window():
    s = pd.Timestamp(periods.SEARCH_START)
    return s, s + pd.Timedelta(days=TUNER_QUICK_DAYS)


def load_tuner_df(cut=None) -> pd.DataFrame:
    """探索と同じ経路（接続ファイル → 指標つきデータ）で読み込む。cut があれば生データを先に切る。

    キャッシュは使わない＝打ち切った生データから指標を作り直させる（キャッシュを使うと
    打ち切りが指標計算に届かず、検査にならない）。
    """
    tuner, _ex, _gen, ad = _tuner_mods()
    s, e = _tuner_window()
    orig = e37.load_5m
    if cut is not None:
        e37.load_5m = _cut_loader(orig, cut)
    try:
        (dfp,) = tuner.load_windows_cached(ad, [(s, e)], tuner.WARM, use_cache=False)
    finally:
        e37.load_5m = orig
    return dfp


def tuner_recipes() -> list[tuple[str, dict]]:
    """恒等3本＋種を固定した生成の案。データを一切 見ずに決まる＝打ち切りあり/なしで同じ。"""
    import numpy as np
    _t, ex, gen, _ad = _tuner_mods()
    recs = [("恒等S2", ex.identity_recipe()), ("恒等L1", ex.identity_l1_recipe()),
            ("恒等S1", ex.identity_s1_recipe())]
    lm, _warn = gen.load_limits()
    lm = gen.resolve_hold_range(lm, "e38")     # 保有時間の範囲＝役割（scalp）から先に解決（監査 4-19／要件 R6）
    pool, _rej, _n = gen.material_pool()
    got, i = 0, 0
    while got < TUNER_GEN_N and i < 60:
        i += 1
        try:
            # ★59回目（まこさん承認 2026-08-25）＝案は印（値の出どころ）つきで返る。実行器へ直に渡すので印を外す
            #   （本走の run_trial と同じ一手・設計書 v2 やること7）。
            r = gen.strip_marks(gen.sample_structure(np.random.default_rng([TUNER_SEED, i]), lm, pool, ["5m", "15m"]))
        except (Exception, SystemExit):                   # noqa: BLE001  引けない種は次へ（種の番号で再現可能）
            continue
        recs.append((f"生成{got + 1}(種{TUNER_SEED}-{i})", r))
        got += 1
    return recs


def _run_one(ex, dfp: pd.DataFrame, rec: dict, qt: dict):
    """レシピ1本を実行器で走らせて売買の表を返す。拒否・失敗は文字列で返す（黙って飛ばさない）。"""
    try:
        d2 = ex.attach_recipe_columns(dfp, rec)
        trades, _rep = ex.run_recipe(d2, rec, qtable=qt)
    except BaseException as err:                          # noqa: BLE001  実行器の拒否（SystemExit）も拾う
        return f"走れない（{type(err).__name__}: {str(err)[:80]}）"
    t = pd.DataFrame(trades)
    if len(t):
        t["entry_time"] = pd.to_datetime(t["entry_time"])
        t["exit_time"] = pd.to_datetime(t["exit_time"])
    return t


def tuner_check(margin_days: float) -> int:
    """検査1-c 本体。戻り＝食い違い（と番人の失敗）の件数。"""
    _t, ex, gen, _ad = _tuner_mods()
    s, e = _tuner_window()
    cut = s + pd.Timedelta(days=TUNER_CUT_DAYS)
    print(f"[検査1-c] engine_tuner の経路の打ち切り再現テスト"
          f"（窓 {s.date()}〜{e.date()} / 打ち切り {cut.date()} / キャッシュ不使用）")
    ng = 0

    t0 = time.time()
    full = load_tuner_df(cut=None)
    part = load_tuner_df(cut=cut)
    print(f"  データ: {len(full)} 行 {len(full.columns)} 列（読み込み2回 {time.time() - t0:.0f} 秒）")

    # ── 番人（この検査自体が壊れていないか・3本）─────────────────────────────
    def _sab(d):
        x = d.copy()
        x["stoch_k"] = pd.Series(x["stoch_k"]).shift(-6).to_numpy()   # H2OK: 番人の細工＝わざと未来を見せて検査が落ちるかを確かめる行。実戦の経路からは呼ばれない
        return x
    hit = [b for b in compare_features(_sab(full), _sab(part), cut) if b.startswith("stoch_k")]
    print(f"  番人1c-1 データ経路の細工（stoch_k を6本先の値に）を見つける: "
          f"{'✅ 見つけた' if hit else '❌ 見逃した＝この検査は信用できない'}")
    if not hit:
        return 1

    recs = tuner_recipes()
    same_rec = (json.dumps([r for _, r in recs], sort_keys=True, default=str)
                == json.dumps([r for _, r in tuner_recipes()], sort_keys=True, default=str))
    print(f"  番人1c-2 レシピが毎回 同じ（種の固定＝再現できる）: {'✅' if same_rec else '❌'}")
    if not same_rec:
        return 1

    # ── 番人1c-4（2026-08-23・54回目・75番・まこさん承認 eb6f38734142e25c…）＝売買ループの細工を見つける ──
    #   なぜ要るか＝番人3・4 は作り物の売買記録で「比べる関数」だけを試し、番人1c-1 は列の細工だけ。
    #   「実エンジンの売買ループに未来参照を入れたら落ちる」を一度も実物で確かめていなかった。
    #   ＝余白3日の穴（74番＝CUT の直前の玉を比べない）が在ることに、テストでは気づけなかった。
    #   細工＝実行器に渡す high・low（TP/SL の約定判定に使う列）を6本先の値にずらす。切った走行では
    #   最後の6本が NaN になって約定が変わる＝CUT の直前の玉が違う＝余白0日なら必ず捕まる。
    def _sab_hl(d):
        x = d.copy()
        for _col in ("high", "low"):
            x[_col] = pd.Series(x[_col]).shift(-6).to_numpy()   # H2OK: 番人1c-4 の細工＝わざと未来を見せて検査が落ちるかを確かめる行。実戦の経路からは呼ばれない
        return x
    #   ★切る所＝「細工で変わる足（最後の6本）に玉が掛かっている時刻」にする（2026-08-23 実測＝本番の
    #     打ち切り日 4/15 0:00 の直前は1日以上 玉が無く、どこも変わらなかった）。細工した切らない走行の
    #     S1 の玉のうち、CUT より前で最後に決済した玉の決済の足の直後を CUT4 にする＝その玉は切った走行
    #     では最後の6本（NaN）で約定できず強制決済（FORCE_CLOSE_EOD）になる＝余白0日なら件数が違って捕まる。
    s1 = dict(recs)["恒等S1"]                                  # 玉が多い（90日で約1,700件）
    a4 = _run_one(ex, _sab_hl(full), s1, None)
    if isinstance(a4, str) or not len(a4):
        print(f"  番人1c-4 売買ループの細工（high・low を6本先に）: ❌ 走れない／玉が無い（{a4 if isinstance(a4, str) else 0}）")
        return 1
    last_exit = a4.loc[a4["exit_time"] < cut, "exit_time"].max()
    cut4 = pd.Timestamp(last_exit) + pd.Timedelta(minutes=5)   # 決済の足を含めて切る（ts < cut4）
    part4 = load_tuner_df(cut=cut4)
    b4 = _run_one(ex, _sab_hl(part4), s1, None)
    if isinstance(b4, str):
        print(f"  番人1c-4 売買ループの細工（high・low を6本先に）: ❌ 走れない（{b4}）")
        return 1
    bad4, n4 = compare_trades(a4, b4, cut4, margin_days)
    print(f"  番人1c-4 売買ループの細工（high・low を6本先に）を見つける（切る所 {cut4}＝玉が掛かる足・突き合わせ {n4} 件）: "
          f"{('✅ 見つけた → ' + bad4[0][:80]) if bad4 else '❌ 見逃した＝売買の突き合わせが CUT の直前の玉を見ていない（74番）'}")
    if not bad4:
        return 1

    # ── (a) データの全列（探索の指標の経路）────────────────────────────────
    bad = compare_features(full, part, cut)
    if bad:
        ng += 1
        print(f"  [1-c 列] ⛔ 打ち切りより前の値が違う列 {len(bad)} 本")
        for b in bad[:10]:
            print(f"        - {b}")
    else:
        print(f"  [1-c 列] ✅ 全 {len(full.columns)} 列 一致（探索のデータ経路に leak なし）")

    # ── (b) 売買（恒等3本＋生成の案）────────────────────────────────────
    lm, _ = gen.load_limits()
    lm = gen.resolve_hold_range(lm, "e38")     # tuner_recipes と同じ解決（分位の一覧も同じ limits から）
    grid = gen.quantile_list(lm)
    ran_gen = 0
    rep_done = False
    for name, rec in recs:
        is_identity = name.startswith("恒等")
        try:
            d2f = ex.attach_recipe_columns(full, rec)
            # ★分位の解決表は、入口の条件のつなぎ（connective）を読んで作る。天井 resting 型
            #   （恒等S1）は入口に connective を持たない＝実物の恒等検収（run_identity_s1）と同じく
            #   解決表なしで走らせる（legacy 値は解決表を使わない）。
            qt = (gen.build_qtable(d2f, gen._geo_of(d2f), [rec], grid)
                  if "connective" in (rec.get("entry") or {}) else None)
        except BaseException as err:                      # noqa: BLE001
            print(f"  [1-c {name}] ⛔ 分位の解決表を作れない（{type(err).__name__}: {str(err)[:60]}）")
            ng += 1
            continue
        a = _run_one(ex, full, rec, qt)
        if is_identity and not rep_done and not isinstance(a, str):
            a2 = _run_one(ex, full, rec, qt)
            same_run = (isinstance(a2, pd.DataFrame)
                        and a.to_csv(index=False) == a2.to_csv(index=False))
            print(f"  番人1c-3 同じ入力なら同じ出力（{name} を2回）: {'✅' if same_run else '❌ 出力が揺れる'}")
            if not same_run:
                return ng + 1
            rep_done = True
        b = _run_one(ex, part, rec, qt)
        if isinstance(a, str) or isinstance(b, str):
            if isinstance(a, str) and a == b:
                print(f"  [1-c {name}] {'⛔ 恒等なのに走れない: ' + a if is_identity else '⚠️ 両方 走れない（同じ理由）＝突き合わせ対象外: ' + a}")
                ng += 1 if is_identity else 0
            else:
                print(f"  [1-c {name}] ⛔ 片方だけ走れない＝要調査: {str(a)[:60]} / {str(b)[:60]}")
                ng += 1
            continue
        badt, n = compare_trades(a, b, cut, margin_days)
        if badt:
            ng += 1
            print(f"  [1-c {name}] ⛔ 食い違い（突き合わせ {n} 件）")
            for x in badt[:5]:
                print(f"        - {x}")
        elif n == 0:
            print(f"  [1-c {name}] ⚠️ 打ち切りより前に決済した売買が 0 件＝この案は突き合わせの中身が無い（窓全体では {len(a)} 件）")
        else:
            print(f"  [1-c {name}] ✅ {n} 件 全一致（窓全体では {len(a)} 件）")
            if not is_identity:
                ran_gen += 1
    if ran_gen == 0:
        print(f"  ⚠️ 生成の案で突き合わせまで走れたものが 0 本＝生成レーンの覆いが無い（恒等3本だけの結果）")
        ng += 1
    return ng


# ============================================================================
# 突き合わせ
# ============================================================================
def _diff_cols(a: pd.DataFrame, b: pd.DataFrame, label_col: str) -> list[str]:
    """2つの表を1セルずつ突き合わせ、食い違った列の説明を返す。"""
    bad = []
    for col in a.columns:
        if col in IGNORE_COLS or col not in b.columns:
            continue
        x, y = a[col], b[col]
        same = (x.eq(y) | (x.isna() & y.isna()))
        if not bool(same.all()):
            n = int((~same).sum())
            first = int((~same).idxmax())
            bad.append(f"{col}（{n} 個 食い違い・最初は {a[label_col].iloc[first]}／"
                       f"打ち切りなし {x.iloc[first]!r} ／ 打ち切りあり {y.iloc[first]!r}）")
    return bad


def compare_features(full: pd.DataFrame, cut_df: pd.DataFrame, cut) -> list[str]:
    """検査1-a｜指標を1セルずつ突き合わせ、食い違った列の名前を返す。"""
    a = full[full["ts"] < cut].reset_index(drop=True)
    b = cut_df[cut_df["ts"] < cut].reset_index(drop=True)
    if len(a) != len(b):
        return [f"（行数が違う: 打ち切りなし {len(a)} 行 / 打ち切りあり {len(b)} 行）"]
    return _diff_cols(a, b, "ts")


FORCED_EOD = "FORCE_CLOSE_EOD"   # データの終わりで強制決済された玉の決済理由（e37._record・score.py の taker に登録済み）


def compare_trades(full: pd.DataFrame, cut_df: pd.DataFrame, cut, margin_days: float = 0.0) -> tuple[list[str], int]:
    """検査1-b｜CUT より前に決済が終わった売買を、CUT の直前の玉まで1行ずつ突き合わせる。

    ★2026-08-23（54回目・74番・まこさん承認 eb6f38734142e25c…）に直した。
      直す前＝CUT−3日 より前に決済した玉だけを比べていた（余白3日）。余白を取った理由は「切った走行では
      データの終わりで持っている玉が強制決済される＝未来参照ではない違いが出る」だった。
      ところが、売買ループの中の未来参照で結果が変わるのは「見ようとした先が CUT を越える玉＝CUT の直前の玉」
      だけで、その玉が余白の中に居た＝3日（864本）より近くを覗く型は捕まらなかった（番人1c-4 で実測＝見逃し）。
      直した後＝余白で一律に外すのをやめ、外すべき玉（強制決済＝決済理由 FORCE_CLOSE_EOD）だけを名指しで外す。
        a＝切らない走行の、CUT より前に決済した玉
        b＝切った走行の、強制決済ではない玉（切った走行の玉は全部 CUT より前に決済している）
      margin_days は残すが既定 0＝0 が正しい状態（余白は検査を甘くする・どうしても要るときだけ）。
    """
    edge = cut - pd.Timedelta(days=margin_days)
    srt = ["entry_time", "exit_time", "side"]
    a = full[full["exit_time"] < edge].sort_values(srt, kind="stable").reset_index(drop=True) if len(full) else full
    if len(cut_df):
        keep = cut_df["exit_time"] < edge
        if "exit_reason" in cut_df.columns:
            keep &= cut_df["exit_reason"] != FORCED_EOD
        b = cut_df[keep].sort_values(srt, kind="stable").reset_index(drop=True)
    else:
        b = cut_df
    if len(a) != len(b):
        return ([f"（件数が違う: 打ち切りなし {len(a)} 件 / 打ち切りあり {len(b)} 件）"], max(len(a), len(b)))
    if len(a) == 0:
        return ([], 0)
    return (_diff_cols(a, b, "entry_time"), len(a))


# ============================================================================
# 検査3｜番人（この検査自体が壊れていないかのメタ確認）
# ============================================================================
def _sab_local(df: pd.DataFrame) -> pd.DataFrame:
    """細工A＝局所的な未来参照。ADX を6本 先の値に置き換える。"""
    d = df.copy()
    d["adx"] = d["adx"].shift(-6)   # H2OK: 検査3 の細工＝わざと未来を見せて検査が落ちるか確かめるためだけの行。実戦の経路からは呼ばれない
    return d


def _sab_global(df: pd.DataFrame) -> pd.DataFrame:
    """細工B＝期間全体の集計。ATR% を「期間全部の平均」で割る（未来を含む＝全行がずれる）。"""
    d = df.copy()
    d["atr_pct"] = d["atr_pct"] / float(d["atr_pct"].mean())
    return d


def _sab_lucky(df: pd.DataFrame) -> pd.DataFrame:
    """細工C＝限界の実物。ATR% を「期間全部の最大値」で割る。

    ★これは未来を見ている（期間全部＝打ち切り後も含む）。それでも、この期間では最大値が
    たまたま打ち切り日より前にあるので、割った結果が変わらない＝この検査では捕まらない。
    2026-08-09 の実測で分かった。捕まらないことを、番人として明示的に残す（限界を文章だけにしない）。
    """
    d = df.copy()
    d["atr_pct"] = d["atr_pct"] / float(d["atr_pct"].max())
    return d


def _synthetic_trades(peek: bool) -> pd.DataFrame:
    """検査1-b の突き合わせが本当に働くかを、作り物の売買記録で確かめるための材料。"""
    base = pd.Timestamp(periods.SCORE_START)
    rows = []
    for i in range(10):
        rows.append({"entry_time": base + pd.Timedelta(hours=i),
                     "exit_time": base + pd.Timedelta(hours=i, minutes=30),
                     "side": "SHORT", "entry_price": 100.0 + i,
                     "exit_price": 99.0 + i + (0.5 if peek else 0.0),
                     "exit_reason": "TP_FILLED"})
    return pd.DataFrame(rows)


def _probe_line(kind: str) -> str:
    """番人5 の材料。探しているパターンを含むただの文字列を組み立てる（ここに直接 書くと hook が誤発火する＝穴⑤）。"""
    body = "x = c" + ".shift(" + "-1)"
    return body + ("  # H2OK: 理由" if kind == "annotated" else "")


def selftest(margin_days: float) -> bool:
    """番人。落ちるべきものが落ち、通るべきものが通ることを確かめる。"""
    ok = True
    print("[検査3] 番人（この検査自体が壊れていないかのメタ確認）")

    cut = pd.Timestamp(periods.SCORE_START) + pd.Timedelta(days=30)
    t0 = time.time()
    full = load_features(cut=None)
    part = load_features(cut=cut)
    print(f"        （実データ読み込み {time.time() - t0:.0f} 秒 / 打ち切り日 {cut.date()}）")

    clean = compare_features(full, part, cut)
    if clean:
        print(f"  番人0（細工なし＝通るのが正解）: ❌ 細工していないのに食い違った → {clean[:3]}")
        ok = False
    else:
        print("  番人0（細工なし＝通るのが正解）: ✅")

    for name, sab, col in (("番人1 局所の未来参照（ADX を6本先の値に）", _sab_local, "adx"),
                           ("番人2 期間全体の集計（ATR% を全期間の平均で割る）", _sab_global, "atr_pct")):
        bad = compare_features(sab(full), sab(part), cut)
        found = [b for b in bad if b.startswith(col)]
        if found:
            print(f"  {name}: ✅ 見つけた → {found[0]}")
        else:
            print(f"  {name}: ❌ 見逃した（検査が壊れている）→ {bad[:3]}")
            ok = False

    # 番人2' ＝この検査の限界を、文章でなく実物で示す（捕まらないのが正解）
    lucky = compare_features(_sab_lucky(full), _sab_lucky(part), cut)
    print(f"  番人2' 限界の実物（ATR% を全期間の最大で割る＝未来を見ているが捕まらない）: "
          f"{'✅ 予告どおり捕まらなかった' if not lucky else '（今回は捕まった＝最大値が打ち切り後に移った）'}")
    print("        → この検査は『未来を見ていない』の証明ではありません。『この期間で結果が変わらなかった』までです。")

    scut = pd.Timestamp(periods.SCORE_START) + pd.Timedelta(days=margin_days + 1)
    bad, n = compare_trades(_synthetic_trades(False), _synthetic_trades(False), scut, margin_days)
    print(f"  番人3 売買記録が同じ（通るのが正解・{n}件 突き合わせ）: {'✅' if not bad else '❌ ' + str(bad[:2])}")
    ok = ok and not bad
    bad, n = compare_trades(_synthetic_trades(False), _synthetic_trades(True), scut, margin_days)
    print(f"  番人4 売買記録が違う（止まるのが正解・{n}件 突き合わせ）: {('✅ 見つけた → ' + bad[0]) if bad else '❌ 見逃した'}")
    ok = ok and bool(bad)

    hit = scan_line(_probe_line("plain")) and not scan_line(_probe_line("annotated"))
    prose = not scan_line("# 説明文です。ここで未来参照の書き方に触れても誤発火しない")
    print(f"  番人5 全数スキャンの判定（注記なしは拾う・注記ありは拾わない）: {'✅' if hit else '❌'}")
    print(f"  番人6 説明文で誤発火しない（穴⑤ を塞いだ確認）: {'✅' if prose else '❌'}")
    # ★番人7（2026-08-21・M2-2-8 で新設）＝**説明の文章（docstring）の中の語で誤発火しない**。
    #   なぜ足したか＝番人6 は行内コメント（# 以降）だけを見ていて、複数行にまたがる説明の文章を
    #   1件も試していなかった。そのため 41番（説明の文章での誤発火）が残っていることに気づけず、
    #   2026-08-21 に H2 の検査が実際に落ちた。**番人が居るのに何も守らない状態だった。**
    _doc = 'def f():\n    """うしろを覗く' + _probe_line("plain").strip() + ' も使っていません。"""\n    return 1\n'
    doc_ok = not scan_text(_doc)
    _real = 'def f():\n    """説明。"""\n    ' + _probe_line("plain").strip() + '\n'
    real_ok = bool(scan_text(_real))
    print(f"  番人7 説明の文章（docstring）で誤発火しない（41番・2026-08-21 に直した）: {'✅' if doc_ok else '❌'}")
    print(f"  番人7' 説明の文章の下の本物のコードは拾う（甘くなっていない）: {'✅' if real_ok else '❌'}")
    ok = ok and hit and prose and doc_ok and real_ok

    print(f"  → 番人の結果: {'全部 pass ✅' if ok else '❌ 落ちた＝この道具の出す結果は信用できない'}")
    return ok


# ============================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="H2（leak なし）を打ち切り再現テストで確かめる読み取り専用の診断")
    ap.add_argument("--cut-days", type=int, nargs="*", default=[45, 90],
                    help="採点窓の開始から何日目で打ち切るか（複数可・既定 45 と 90）")
    ap.add_argument("--margin-days", type=float, default=0.0,
                    help="売買記録の突き合わせで打ち切り日の手前に取る余白（日・既定0＝0 が正しい状態。"
                         "2026-08-23 の74番の直しで 3→0。余白は検査を甘くする）")
    ap.add_argument("--selftest", action="store_true", help="検査3（番人）だけ走らせる")
    ap.add_argument("--scan", action="store_true", help="検査2（全数スキャン）だけ走らせる")
    ap.add_argument("--features", action="store_true", help="検査1-a（指標の突き合わせ）だけ走らせる")
    ap.add_argument("--tuner", action="store_true", help="検査1-c（engine_tuner の経路）だけ走らせる")
    a = ap.parse_args()

    print("=" * 78)
    print("leak_causality_diag — H2（leak なし）を『動かした結果』で確かめる（読み取り専用）")
    print("=" * 78)

    if a.scan:
        return 0 if not scan_existing_code() else 1
    if a.selftest:
        return 0 if selftest(a.margin_days) else 1
    if a.tuner:
        return 0 if tuner_check(a.margin_days) == 0 else 1

    ng = 0
    scan_hits = scan_existing_code()
    print()
    if not a.features:
        if not selftest(a.margin_days):
            print("\n⛔ 番人が落ちました。検査自体が壊れているので、以下の結果は信用できません。")
            return 1
        print()

    cuts = [pd.Timestamp(periods.SCORE_START) + pd.Timedelta(days=d) for d in a.cut_days]
    print(f"[検査1] 打ち切り再現テスト（打ち切り日 {', '.join(str(c.date()) for c in cuts)}）")

    t0 = time.time()
    full_f = load_features(cut=None)
    print(f"  指標: 打ち切りなしを読み込み（{len(full_f)} 行 {len(full_f.columns)} 列 / {time.time() - t0:.0f} 秒）")
    for cut in cuts:
        t0 = time.time()
        bad = compare_features(full_f, load_features(cut=cut), cut)
        if bad:
            ng += 1
            print(f"  [1-a] 打ち切り {cut.date()}: ⛔ 未来を見ている列が {len(bad)} 本")
            for b in bad[:10]:
                print(f"        - {b}")
        else:
            print(f"  [1-a] 打ち切り {cut.date()}: ✅ 全 {len(full_f.columns)} 列 一致（{time.time() - t0:.0f} 秒）")

    if a.features:
        print(f"\n結果: {'✅ 検査1-a は食い違いなし' if ng == 0 else '⛔ 食い違いあり'}")
        return 0 if ng == 0 else 1

    t0 = time.time()
    full_t = run_e38_trades(cut=None)
    print(f"  売買: 打ち切りなしを実行（{len(full_t)} 件 / {time.time() - t0:.0f} 秒）")
    for cut in cuts:
        t0 = time.time()
        bad, n = compare_trades(full_t, run_e38_trades(cut=cut), cut, a.margin_days)
        if bad:
            ng += 1
            print(f"  [1-b] 打ち切り {cut.date()}: ⛔ 食い違い（突き合わせ {n} 件）")
            for b in bad[:10]:
                print(f"        - {b}")
        else:
            print(f"  [1-b] 打ち切り {cut.date()}: ✅ {n} 件 全一致（{time.time() - t0:.0f} 秒）")

    print()
    ng += tuner_check(a.margin_days)

    print()
    print("=" * 78)
    print(f"まとめ: 検査2 の注記なし未来参照 {len(scan_hits)} 件 / 打ち切り再現テスト（1-a・1-b・1-c）の食い違い {ng} 件")
    print("★この結果が言えるのは「この設定（e38_logics.json）とこの期間で leak が出なかった」までです。")
    print("  設定やロジックを変えたら測り直してください。未来を見ていても結果が変わらない場合は捕まりません。")
    if ng == 0 and not scan_hits:
        _write_h2_pass()
    else:
        print("⛔ 落ちがあるので、検査済みの印（h2_pass）は書かない＝engine_tuner は回れないまま。")
    print("=" * 78)
    return 0 if (ng == 0 and not scan_hits) else 1


if __name__ == "__main__":
    sys.exit(main())
