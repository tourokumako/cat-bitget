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
      E38 を2回 走らせ、CUT より前に決済が終わった売買を1行ずつ突き合わせる。
      ★売買ループの中で先の足を覗く型（出口判定が未来を走査する等）はここで捕まる。
      境目の扱い＝CUT の時点でまだ持っている玉は、打ち切り側だけ強制決済されうる。それは未来参照
      ではなくデータの終わりの都合なので、余白（既定3日）を取り、CUT−余白 より前に決済が
      終わった売買だけを厳密に突き合わせる。

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

使い方:
  python3 scripts/priority_rebuild/leak_causality_diag.py --selftest   # 検査3 だけ（番人）
  python3 scripts/priority_rebuild/leak_causality_diag.py --scan       # 検査2 だけ（全数スキャン・一瞬）
  python3 scripts/priority_rebuild/leak_causality_diag.py --features   # 検査1-a だけ（指標の突き合わせ）
  python3 scripts/priority_rebuild/leak_causality_diag.py              # 検査2 → 3 → 1-a → 1-b の順に全部
"""
from __future__ import annotations
import argparse
import inspect
import pathlib
import re
import sys
import time

import pandas as pd

HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

import periods                      # noqa: E402  検証期間の唯一の正本（SSOT・自前で日付を書かない）
import e37_scalp as e37             # noqa: E402  実エンジン（S1/L1 の売買ループ・データ読み込み口）
import e38_logic_parts              # noqa: E402  汎用ロジックの売買部品（S2〜L5）
import e38_priority_stack as e38    # noqa: E402  E38 の設定解釈（load_logic_config / build_run_kwargs）

# 既存 hook（require_leak_annotation.py）と同じ探し方＝検査2 はこの hook と同じ限界を持つ
SCAN_PAT = re.compile(r"\.shift\(\s*-|center\s*=\s*True")
SCAN_DIR = HERE.parent
# 突き合わせから外す列（診断のための記録で、売買の判断にも net にも関与しない）
IGNORE_COLS = ("logic",)


# ============================================================================
# 検査2｜既存コードの全数スキャン（穴② に対応・探し方は hook と同じなので穴③ は塞がらない）
# ============================================================================
def scan_line(line: str) -> bool:
    """1行が「注記なしの未来参照」か。コメントを外してから見る（穴⑤＝説明文での誤発火を塞ぐ）。"""
    return bool(SCAN_PAT.search(line.split("#", 1)[0])) and "H2OK:" not in line


def scan_existing_code() -> list[tuple[str, int, str]]:
    """scripts/priority_rebuild の .py を全部 見て、注記なしの未来参照パターンを返す。

    除外＝build_labels で始まるファイル（教師ラベル生成が本業＝学習窓内で正当）／
    本ファイル自身と ratchet_guards.py（探すパターンの文字列を持っているだけ）。
    """
    skip_names = {HERE.name, "ratchet_guards.py"}
    hits: list[tuple[str, int, str]] = []
    files = sorted(p for p in SCAN_DIR.glob("*.py") if p.name not in skip_names and not p.name.startswith("build_labels"))
    for p in files:
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if scan_line(line):
                hits.append((p.name, i, line.strip()[:120]))
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
        dfp = e38_logic_parts.prepare_df(df.copy(), adaptive_k=adaptive_k)
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


def compare_trades(full: pd.DataFrame, cut_df: pd.DataFrame, cut, margin_days: float) -> tuple[list[str], int]:
    """検査1-b｜CUT−余白 より前に決済が終わった売買を1行ずつ突き合わせる。"""
    edge = cut - pd.Timedelta(days=margin_days)
    srt = ["entry_time", "exit_time", "side"]
    a = full[full["exit_time"] < edge].sort_values(srt, kind="stable").reset_index(drop=True) if len(full) else full
    b = cut_df[cut_df["exit_time"] < edge].sort_values(srt, kind="stable").reset_index(drop=True) if len(cut_df) else cut_df
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
                     "exit_price": 99.0 + i + (0.5 if peek else 0.0)})
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
    ok = ok and hit and prose

    print(f"  → 番人の結果: {'全部 pass ✅' if ok else '❌ 落ちた＝この道具の出す結果は信用できない'}")
    return ok


# ============================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="H2（leak なし）を打ち切り再現テストで確かめる読み取り専用の診断")
    ap.add_argument("--cut-days", type=int, nargs="*", default=[45, 90],
                    help="採点窓の開始から何日目で打ち切るか（複数可・既定 45 と 90）")
    ap.add_argument("--margin-days", type=float, default=3.0,
                    help="売買記録の突き合わせで打ち切り日の手前に取る余白（日・既定3）")
    ap.add_argument("--selftest", action="store_true", help="検査3（番人）だけ走らせる")
    ap.add_argument("--scan", action="store_true", help="検査2（全数スキャン）だけ走らせる")
    ap.add_argument("--features", action="store_true", help="検査1-a（指標の突き合わせ）だけ走らせる")
    a = ap.parse_args()

    print("=" * 78)
    print("leak_causality_diag — H2（leak なし）を『動かした結果』で確かめる（読み取り専用）")
    print("=" * 78)

    if a.scan:
        return 0 if not scan_existing_code() else 1
    if a.selftest:
        return 0 if selftest(a.margin_days) else 1

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
    print("=" * 78)
    print(f"まとめ: 検査2 の注記なし未来参照 {len(scan_hits)} 件 / 打ち切り再現テストの食い違い {ng} 件")
    print("★この結果が言えるのは「この設定（e38_logics.json）とこの期間で leak が出なかった」までです。")
    print("  設定やロジックを変えたら測り直してください。未来を見ていても結果が変わらない場合は捕まりません。")
    print("=" * 78)
    return 0 if (ng == 0 and not scan_hits) else 1


if __name__ == "__main__":
    sys.exit(main())
