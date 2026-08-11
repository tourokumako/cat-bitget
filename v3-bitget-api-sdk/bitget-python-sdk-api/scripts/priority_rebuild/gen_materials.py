#!/usr/bin/env python3
"""gen_materials.py — 材料の正本の生成器（2026-08-09 新設・マイルストーン①のフロー 段4）

これは何か。
  engine_tuner と observe_diag が条件の材料として使える指標を、1枚の表にする道具。
  ★新しい事実を1つも書かない。既に在るものから機械で引くだけ（フロー 段4 の本文）。

なぜ要るか。
  まこさんの指示（逐語 2026-08-08）＝「入れる材料一覧を正本として自動生成して私が確認できる状態にしてほしい」。
  いまは、材料の一覧が observe_diag のコード・signal_families.md・参照表・検査10 の出力に散っていて、
  1枚で読めない。

1行が何か。
  ★1行＝1つの「指標の種類」。期間で行を分けない（CCI9・CCI20・CCI50 を別の行にしない）。
  理由＝要件の「作ってはいけないもの」2番＝探す値を先に点の一覧で限定するもの、に当たるため。
  期間は範囲の軸として engine_tuner が探す（教訓 L-413）。

欄は7つ（フロー 段4 の本文のとおり）。
  名前 ／ 系統 ／ 答える問い ／ 使える役割 ／ 計算の出どころ ／ グループ ／ 状態

正本（ここから機械で引く・書き写さない）。
  indicator_reference_diag.REFS            … 指標の種類 53 件（名前）
  indicator_reference_diag.FAMILY_LINEAGE  … 系統
  indicator_reference_diag.LINEAGE_QUESTION… 答える問い（出典つき）
  .claude/ratchet/signal_families.json     … 役割ごとに使える系統（role_lineage.roles）
  indicator_reference_diag.INDUSTRY_MAP / EXT2 / REFS[ext] … 計算の出どころと照合の相手
  pandas_ta_classic.Category               … 業界のライブラリの関数（足す候補の出どころ）
  indicator_reference_diag.INDUSTRY_SKIP   … 入れない候補（★まこさんの承認はまだ）

出すもの。
  .claude/ratchet/materials.md   … 人が読む1枚
  .claude/ratchet/materials.json … 機械が読む同じ中身

使い方。
  python3 gen_materials.py --write     … 作る
  python3 gen_materials.py --verify    … 手で書き換えられていないか／正本とずれていないかを検出する
  python3 gen_materials.py --selftest  … 番人（わざと壊すと落ちるか）
  python3 gen_materials.py --status    … いまの状態を表示する
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import indicator_reference_diag as iref   # noqa: E402

_RATCHET = _HERE.parent.parent / ".claude" / "ratchet"
_MD = _RATCHET / "materials.md"
_JSON = _RATCHET / "materials.json"
_SIGFAM = _RATCHET / "signal_families.json"

_GROUP_TBD = "（段8 で埋める）"
_TBD = "（未定・材料に足すときに決める＝段6）"
_EEM = _RATCHET / "entry_exit_matrix.md"

# ── 段5（足すものの一覧）で使う「選べるか」の言い方（1か所に置く＝表記ゆれ防止）──
_SEL_OK = "選べる"
_SEL_NO_TPL = "選べない（名前の組み立てが未登録＝G6 で拒否）"
_SEL_NO_COL = "選べない（材料カタログに列が無い）"
_SEL_NO_H6 = "使えない（価格そのもの＝placement の幾何参照専用・H6）"
_SEL_NA = "—（まだ材料に入っていない）"


def _quiet(fn, *a, **kw):
    """observe_diag は import と実行で画面に出すので、ここでは黙らせて戻り値だけ使う。"""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **kw)


def _engine_view() -> dict:
    """engine_tuner がいま「条件の材料として選べる」ものを、実物から機械で数える（段5・2026-08-09 新設）。

    ★なぜ要るか。materials.md の『在る』は『参照表に登録済み』という意味しか無かった。
      ところが engine_tuner の生成器が条件に選べるのは、そのうちの一部だけ。
      まこさんが『在る 65』を読んで『65 使える』と受け取ると、実物と食い違う。
    ★どこから引くか（書き写さない）。
      engine_tuner_exec.FAMILY_TEMPLATES … 生成器が名前を組み立てられる指標の種類（G6 の線）
      engine_tuner_gen.material_pool     … (指標, 期間) の候補と時間足＝いま探せる範囲そのもの
      observe_diag.build_catalog          … 材料カタログの部品（生成器の入口①）
      signal_families.json extra_parts    … レンジ幾何・時間帯（生成器の入口②③）
    """
    import json as _j

    def _load():
        import engine_tuner_exec as ex
        import engine_tuner_gen as g
        import observe_diag as od
        cfg = od.load_config()
        pool, tfs, cat_total = g.material_pool(cfg)
        names = [nm for nm, _f, _d in od.build_catalog(cfg)]
        return dict(tpl=dict(ex.FAMILY_TEMPLATES), pool=pool, tfs=list(tfs),
                    cat_total=int(cat_total), names=names,
                    demand=list(od._DEMAND_FILES), tf_list=list(cfg["timeframes"]))
    v = _quiet(_load)
    extra = (_j.loads(_SIGFAM.read_text(encoding="utf-8")).get("extra_parts") or {})
    v["geo_ok"] = list((extra.get("geo") or {}).get("parts") or [])
    v["time_ok"] = list((extra.get("time") or {}).get("parts") or [])
    fams = list(dict.fromkeys(e["family"] for e in iref.REFS))
    v["selectable_fams"] = sorted({p["family"] for p in v["pool"]})
    v["unselectable_fams"] = [f for f in fams if f not in set(v["selectable_fams"])]
    v["cols_selectable"] = len(v["pool"]) * len(v["tfs"])
    # 期間がいま「点」で固定されている実測（マイルストーン③の対象・段5 は事実を出すだけ）
    # ★2026-08-11（段6 の 6-7）＝数字の持ち方が3つになった（1つ／並び／無し）ので、
    #   int() に丸めず、そのままの形で集める。数字を持たない指標（包み足 ほか）はこの表に出さない。
    per: dict[str, list] = {}
    for p in v["pool"]:
        if p["param"] is None:
            continue
        per.setdefault(p["family"], []).append(p["param"])
    v["params"] = {k: sorted(set(x)) for k, x in sorted(per.items())}
    return v


# ★段6（材料を足す作業）の前の材料の一覧＝git のこの commit の materials.md（2026-08-09・段5 の分）。
#   ここを起点に「うちが元から持っていた指標が1件も消えていないか」を毎回 照らす（6-9②）。
_STAGE6_BASE_COMMIT = "03aad50"


def _kept_since_stage6(commit: str = _STAGE6_BASE_COMMIT) -> tuple[list[str], int]:
    """段6 の前に「在る」だった指標が、いまも材料に在るかを照らす。戻り＝(消えた名前, 元の件数)。

    ★一覧は git から取り出す（記憶や書き写しではない）。git が使えない環境では空を返す
      （＝この検査は黙って通る。番人の出力に「照らせなかった」と出す作りにはしていない＝
      次に触る人が気づけるよう、ここに書いておく）。
    """
    import subprocess
    rel = "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md"
    try:
        old = subprocess.run(["git", "show", f"{commit}:{rel}"], capture_output=True, text=True,
                             cwd=str(_HERE.parents[3]), timeout=60)
        if old.returncode != 0:
            return [], 0
    except Exception:                                            # noqa: BLE001
        return [], 0
    base = [ln.split("|")[1].strip() for ln in old.stdout.splitlines()
            if ln.startswith("|") and "| 在る |" in ln]
    rows = build_body()["rows"]
    now = {r["名前"] for r in rows if r["状態"] == "在る"}
    # ★「同じ挙動なので省いた」と設定に理由つきで書いてあるものは、消えたとみなさない
    #   （まこさん OK 2026-08-11・逐語「同じ挙動ならどちらかは使わないようにしていいよ」）。
    #   ＝黙って消えた場合だけ ❌ にする。設定 observe_config.json の drop_columns が根拠。
    dropped_fams = set()
    for d, _k in _dropped_columns():
        ent = iref.find(d)[0]
        if ent is not None:
            dropped_fams.add(ent["family"])
    lost = [b for b in base if b not in now and b not in dropped_fams]
    return lost, len(base)


def _dropped_columns() -> list[tuple[str, str]]:
    """同じ挙動なので省いた列の一覧（左＝省いた列・右＝残した列）。出どころ＝observe_config.json。"""
    import json as _j
    p = _HERE / "observe_config.json"
    try:
        return [(a, b) for a, b in (_j.loads(p.read_text(encoding="utf-8")).get("drop_columns") or [])]
    except Exception:                                            # noqa: BLE001
        return []


def _row_engine(row: dict, ev: dict) -> str:
    """1行が engine_tuner から選べるかを返す（上の _engine_view の実測だけで決める）。"""
    if row["状態"] != "在る":
        return _SEL_NA
    nm = row["名前"]
    if nm.startswith("レンジ幾何 "):
        part = nm.split(" ", 1)[1]
        if part in ev["geo_ok"]:
            return _SEL_OK + "（レンジ幾何）"
        return _SEL_NO_H6
    if nm in ev["time_ok"]:
        # 型の表は許すが、生成器が実際に作るかは別（曜日は閾値の格子が未定義＝engine_tuner_gen.py:256）
        return (_SEL_OK + "（時間帯）") if nm == "時刻" else \
            "選べない（型の表は許すが、閾値の格子が未定義＝engine_tuner_gen.py:256）"
    if nm in ev["demand"]:
        return _SEL_NO_COL
    return _SEL_OK if nm in set(ev["selectable_fams"]) else _SEL_NO_TPL


def _gaps(ev: dict, body_counts: dict, add_n: int, skip: list) -> list[dict]:
    """段5＝足すものの一覧。4か所に散っている不足を1つにまとめる（数は全部 実物から）。"""
    # 検査9（向きの穴）
    def _dg():
        import observe_diag as od
        return od._direction_gap(ev["names"])
    _dist, _slope, gap = _quiet(_dg)
    # 検査7（軸カタログ E-c の未実装）
    ec = [ln for ln in _EEM.read_text(encoding="utf-8").splitlines()
          if ln.lstrip().startswith("- **E-c")]
    ax_un: list[str] = []
    if len(ec) == 1:
        _ng, rows = iref.axis_ec_check(ec[0], ev["names"] + ev["demand"])
        ax_un = [f"{r['cat']}＝{r['token']}" for r in rows if r["status"] != "あり"]
    return [
        dict(印="A", 何を足すか="業界のライブラリに在って、うちの材料に無い指標",
             数=add_n, 単位="種類", 出どころ="検査10（observe_diag）",
             中身="下の『材料の一覧』で状態が「足す」の行"),
        dict(印="B", 何を足すか="★うちの材料カタログに在るのに、engine_tuner が条件に選べない指標",
             数=len(ev["unselectable_fams"]), 単位="種類", 出どころ="段5 で新しく数えた（検査には無い）",
             中身="・".join(ev["unselectable_fams"])),
        dict(印="C", 何を足すか="★参照表に在るのに、材料カタログに列が無い（需給）",
             数=len(ev["demand"]), 単位="件", 出どころ="段5 で新しく数えた（検査7 は『あり』と出る＝別の道で見ている）",
             中身="・".join(ev["demand"])),
        dict(印="D", 何を足すか="「終値と◯◯の距離%」に対する「◯◯ そのものの向き」",
             数=len(gap), 単位="件", 出どころ="検査9（observe_diag）", 中身="・".join(gap)),
        dict(印="E", 何を足すか="軸カタログ（入口 E-c）の未実装",
             数=len(ax_un), 単位="件", 出どころ="検査7（observe_diag）", 中身="・".join(ax_un) or "（無し）"),
        dict(印="F", 何を足すか="時間足（1分足・3分足）",
             数=2, 単位="本", 出どころ="要件 R15（フロー 段7 で足す）",
             中身=f"いま {len(ev['tf_list'])} 本＝" + "・".join(ev["tf_list"])),
        dict(印="G", 何を足すか="★型の表は許すが、閾値の格子が無くて選べない部品",
             数=sum(1 for t in ev["time_ok"] if t != "時刻"), 単位="件",
             出どころ="段5 で新しく数えた（engine_tuner_gen.py:256 の逐語）",
             中身="・".join(t for t in ev["time_ok"] if t != "時刻") or "（無し）"),
    ]


def _roles_by_lineage() -> dict[str, list[str]]:
    """signal_families.json の role_lineage から「系統 → 使える役割」を作る（書き写さない）。"""
    d = json.loads(_SIGFAM.read_text(encoding="utf-8"))
    roles = d["role_lineage"]["roles"]
    out: dict[str, list[str]] = {}
    for role, v in roles.items():
        for lin in v.get("lineages", []):
            out.setdefault(lin, []).append(role)
    return out


def _lib_funcs() -> dict[str, str]:
    """業界のライブラリの関数名 → カテゴリ。入っていなければ空。"""
    try:
        import pandas_ta_classic as pt
        return {fn: cat for cat, fns in pt.Category.items() for fn in fns}
    except Exception:                                           # noqa: BLE001
        return {}


def _source_note(fam: str, ext_ok: bool) -> str:
    """計算の出どころ＝式は全部 うちの自前。ライブラリに同じものが在るかと、照合の相手を書く。"""
    fns, _note = iref.INDUSTRY_MAP.get(fam, ((), ""))
    x2 = iref.EXT2.get(fam)
    checks = []
    if ext_ok:
        checks.append("ta")
    if x2 is not None:
        checks.append(x2[1])
    lib = f"ライブラリに同じものが在る（{'・'.join(fns)}）" if fns else "ライブラリに相当なし"
    chk = f"照合の相手: {'・'.join(checks)}" if checks else "照合の相手: 無し（手計算の既知答えで担保）"
    return f"うちの自前の式／{lib}／{chk}"


def forms_table() -> list[dict]:
    """★使い方（条件の形）の一覧を、実物から機械で引く（まこさん指示 2026-08-11「すべて自動生成にして」）。

    引く先は2つ。どちらも実物で、この道具は1行も手で書かない。
      ①形の名前と数 … engine_tuner_exec.FORMS（実行器が本当に実行できる形＝これが正）
      ②何をするか・必要な値 … engine_tuner_step2_condition_format.md §2.2 の表（人が読む説明）
    ★①に在って②に無い形が1つでもあれば ❌ にする（実物と説明のずれを黙らせない）。
    ★なぜ材料の正本に入れるか＝「材料（指標）に列が無い＝作れない」と CC が誤判定した事案
      （2026-08-11・RSI の差）の対策。指標の一覧と使い方の一覧が別の場所に在ると突き合わせられない。
    """
    import engine_tuner_exec as ex
    doc = _RATCHET / "engine_tuner_step2_condition_format.md"
    rows, ng = [], []
    text = doc.read_text(encoding="utf-8") if doc.exists() else ""
    desc = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        key = cells[0].split()[0]                      # 「level 水準」→「level」
        if key in ex.FORMS:
            desc[key] = dict(和名=cells[0], 材料=cells[1], 必要な値=cells[2], 実例=cells[3])
    # ★入れ子の欄の意味＝streak・within_n は「外側になる形」（内側に条件を1つ包む）。
    #   それ以外は「内側に置ける」（設計書 §2.2 の逐語「単純形＝入れ子形以外の全部」）。
    for f in ex.FORMS:
        nest = "外側になる形（中に条件を1つ包む）" if f in ex.NEST_FORMS else "内側に置ける"
        d = desc.get(f)
        if d is None:
            ng.append(f)
            rows.append(dict(形=f, 和名="？", 材料="？", 必要な値="？", 実例="？", 入れ子=nest))
            continue
        # 「level 水準」→「水準」（形の名前は左の欄に在るので、説明だけにする）
        wa = d["和名"].split(" ", 1)[1] if " " in d["和名"] else d["和名"]
        rows.append(dict(形=f, 和名=wa, 材料=d["材料"], 必要な値=d["必要な値"],
                         実例=d["実例"], 入れ子=nest))
    return dict(rows=rows, ng=ng, n_forms=len(ex.FORMS),
                doc=".claude/ratchet/" + doc.name)


def condition_parts() -> dict:
    """★条件の部品の一覧を出す（段C の C-1・2026-08-11 新設・まこさん OK）。

    なぜ要るか。
      いまの engine_tuner は「条件の形」を11個の名前で持っている（engine_tuner_exec.FORMS）。
      11個は 2026-08-01 の commit 254066a で一度に手で書かれ、以降1個も増えていない。
      ＝私が思いついたら1語 足す運用になっていた（まこさん指摘 2026-08-11
      「これは手書きで思い付いたら増やす。みたいな運用になるのか？すごい原始的なんだが。」）。
      11個を実物のコードで分解すると、全部が同じ小さい部品の組み合わせだった。

    どこから引くか。
      中身 … .claude/ratchet/condition_parts.json（業界5件と照らして決めた・判定の理由つき）
      ★下の4つは毎回 実物から取り直す（json の記録がずれたら ❌ を出す）。

    毎回 機械で確かめること（番人4件）。
      ①いまの形（FORMS）が、分解の表に全部 載っているか（逆に、表に在って実物に無い形が無いか）
      ②分解の表が使っている部品の名前が、「いま在る部品」に全部 在るか
      ③pandas-ta の「使い方」の関数の数が、記録と合っているか（入っているので毎回 数え直す）
      ④「閾値とのクロス」が、いまも本当に書けないか（実行器の検証器に渡して拒否されること）
    """
    import engine_tuner_exec as ex
    src = _RATCHET / "condition_parts.json"
    if not src.exists():
        return dict(ng=[f"正本が無い: {src}"], rows_have=[], rows_missing=[],
                    rows_no=[], sources=[], forms={}, live={})
    d = json.loads(src.read_text(encoding="utf-8"))
    ng: list[str] = []

    # ── 番人① いまの形が、分解の表に全部 載っているか（両向き）──
    dec = {k: v for k, v in d["form_decomposition"].items() if not k.startswith("_")}
    miss = [f for f in ex.FORMS if f not in dec]
    extra = [f for f in dec if f not in ex.FORMS]
    if miss:
        ng.append(f"実行器に在るのに分解の表に無い形: {miss}")
    if extra:
        ng.append(f"分解の表に在るのに実行器に無い形: {extra}")

    # ── 番人② 分解の表が使っている部品が、「いま在る部品」に全部 在るか ──
    have_ids = {p["id"] for p in d["have"]}
    used = {pid for v in dec.values() for pid in v}
    unknown = sorted(used - have_ids)
    if unknown:
        ng.append(f"分解の表が知らない部品を指している: {unknown}")
    unused = sorted(have_ids - used)

    # ── 番人③ pandas-ta の「使い方」の関数を数え直す ──
    live: dict = {}
    rec = {s["id"]: s for s in d["sources"]}
    try:
        import pandas_ta_classic.utils as _U
        key = ("above", "below", "cross", "signals", "lag")
        fns = sorted(n for n in dir(_U)
                     if not n.startswith("_") and callable(getattr(_U, n))
                     and any(k in n.lower() for k in key))
        live["pandas_ta"] = fns
        if len(fns) != rec["pandas_ta"]["n"]:
            ng.append(f"pandas-ta の使い方の関数が {rec['pandas_ta']['n']} 件の記録と違う（実測 {len(fns)} 件）")
    except Exception as e:                       # 入っていない時は黙らせず理由を出す
        live["pandas_ta"] = []
        ng.append(f"pandas-ta を数えられなかった: {str(e)[:60]}")

    # ── 番人④「閾値とのクロス」が、いまも本当に書けないか ──
    #   ★書けるようになったら、この部品は「足りない」から「在る」へ移す必要がある＝表が古いと分かる。
    probe = {"form": "cross", "side": "above", "value": {"direction": "up"},
             "material": [{"family": "RSI", "param": 14, "tf": "5m"}]}
    try:
        ex._check_cond(probe, "legacy", "番人（閾値とのクロス）", [])
        live["cross_value"] = "通った"
        ng.append("「閾値とのクロス」が通るようになっている＝部品の一覧が古い（cross_val を『在る』へ移す）")
    except SystemExit as e:
        live["cross_value"] = f"拒否（{str(e)[:60]}）"
    except Exception as e:
        live["cross_value"] = f"{type(e).__name__}"
        ng.append(f"「閾値とのクロス」の番人が動かなかった: {type(e).__name__}")

    # ── 番人⑤ 分解の表が、実際に動くコード（condition_parts_diag の組み立て）と一致するか ──
    #   ★表だけを直しても、動くコードと食い違えばここで落ちる（2026-08-11 の C-2 で
    #    「読んで分解した表」に3つの抜けが在ったため、表と実装を機械で結んだ）。
    live["decomposition"] = _parts_from_diag(dec, ng)

    return dict(ng=ng, unused=unused, sources=d["sources"], forms=dec,
                rows_have=d["have"], rows_missing=d["missing"], rows_no=d["not_needed"],
                live=live, note=d["_why"], scope=d["_scope"], how=d["_how_decided"],
                c2=d.get("_c2_found", ""))


def parts_matrix() -> dict:
    """★指標 × 部品 の突き合わせ（段C の C-3・2026-08-11）。

    何を出すか。
      ①指標 244種類を「パラメータの数」で分ける＝列を2本 並べられるかが決まる
      ②部品を「何が要るか」で分けて、使える指標の数を出す
      ③★業界の定番のクロスを1件ずつ、実行器と生成器の両方で機械判定する

    判定の根拠（全部 実物・CC が結果を手で書かない）。
      実行器 … engine_tuner_exec._check_cond に実際に条件を渡して、通るか拒否されるか
      生成器 … engine_tuner_gen._pair_materials の決まり（同じ指標でパラメータが2つ以上／
               Stoch%K と %D の直書きの対だけ）
    """
    import collections
    import engine_tuner_exec as ex
    import engine_tuner_gen as gen
    pool, tfs, _tot = _quiet(gen.material_pool)
    by: dict[str, list] = collections.defaultdict(list)
    for b in pool:
        by[b["family"]].append(b["param"])
    n_multi = sum(1 for ps in by.values() if len({str(p) for p in ps}) >= 2)
    n_one = sum(1 for ps in by.values() if len({str(p) for p in ps}) == 1 and ps[0] is not None)
    n_none = sum(1 for ps in by.values() if all(p is None for p in ps))

    src = _RATCHET / "condition_parts.json"
    d = json.loads(src.read_text(encoding="utf-8")) if src.exists() else {"classic_crosses": []}
    rows = []
    for cc in d.get("classic_crosses", []):
        a, b = cc["a"], cc["b"]
        pa, pb = by.get(a), by.get(b)
        if pa is None or pb is None:
            rows.append(dict(name=cc["name"], a=a, b=b, exec_ok="—（材料に無い）",
                             gen_ok="—", note=cc.get("note", "")))
            continue
        # ① 実行器＝実際に検証器へ渡す
        if a == b:
            ps = sorted({str(x): x for x in pa}.values(), key=str)
            m1, m2 = {"family": a, "param": ps[0], "tf": "5m"}, {"family": b, "param": ps[-1], "tf": "5m"}
        else:
            m1, m2 = {"family": a, "param": pa[0], "tf": "5m"}, {"family": b, "param": pb[0], "tf": "5m"}
        cond = {"form": "cross", "value": {"direction": "up"}, "material": [m1, m2]}
        try:
            ex._check_cond(cond, "legacy", "C-3", [])
            e_ok = "✅ 受け付ける"
        except SystemExit as e:
            e_ok = f"❌ 拒否（{str(e)[:40]}）"
        except Exception as e:
            e_ok = f"❌ {type(e).__name__}"
        # ② 生成器＝_pair_materials の決まりをそのまま当てる
        special = {a, b} == {"Stoch%K", "Stoch%D"}
        same_multi = (a == b) and len({str(x) for x in pa}) >= 2
        g_ok = "✅ 作る" if (special or same_multi) else "❌ 作らない（別の指標どうし）"
        rows.append(dict(name=cc["name"], a=a, b=b, exec_ok=e_ok, gen_ok=g_ok, note=cc.get("note", "")))

    ng = []
    blocked = [r for r in rows if r["gen_ok"].startswith("❌") and r["exec_ok"].startswith("✅")]
    return dict(n_fam=len(by), n_multi=n_multi, n_one=n_one, n_none=n_none,
                n_tf=len(tfs), rows=rows, blocked=len(blocked), ng=ng)


def _parts_from_diag(dec: dict, ng: list) -> str:
    """condition_parts_diag.py の組み立て（_c_◯◯）が、どの部品（p_◯◯）を使っているかを構文木で数え、
    json の分解の表と1件ずつ突き合わせる。★入れ子（_c_streak が _c_level を呼ぶ）は辿って足す。"""
    import ast
    src = _HERE / "condition_parts_diag.py"
    if not src.exists():
        ng.append(f"C-2 の突き合わせの道具が無い: {src.name}")
        return "道具なし"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    calls: dict[str, set] = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name.startswith("_c_"):
            calls[n.name] = {c.func.id for c in ast.walk(n)
                             if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                             and (c.func.id.startswith("p_") or c.func.id.startswith("_c_"))}
    def _resolve(fn: str, seen: set) -> set:              # 入れ子を辿る
        out: set = set()
        for c in calls.get(fn, ()):
            if c.startswith("p_"):
                out.add(c[2:])
            elif c not in seen:
                out |= _resolve(c, seen | {c})
        return out
    bad = 0
    for form, want in dec.items():
        got = _resolve("_c_" + form, {"_c_" + form})
        if got != set(want):
            bad += 1
            ng.append(f"分解の表と、動くコードが食い違う（{form}）＝表 {sorted(want)} ／ 実装 {sorted(got)}")
    return f"{len(dec) - bad}/{len(dec)} 一致"


def build_body() -> dict:
    """表の中身を作る（正本から機械で引く）。"""
    rbl = _roles_by_lineage()
    lib = _lib_funcs()
    rows = []
    # ★いま材料カタログに実際に列が在る family を機械で数える（2026-08-11 に足した）。
    #   理由＝この表は参照表 REFS から作っている。同じ挙動の列を省くと、カタログには無いのに
    #   ここだけ「在る」と書いてしまう（正本が嘘をつく＝L-430・L-436 と同じ型）。
    _drop_map = dict(_dropped_columns())

    def _live_families() -> dict:
        import contextlib as _c
        import io as _i
        with _c.redirect_stdout(_i.StringIO()):
            import observe_diag as _od
            _cfg = _od.load_config()
            _names = [n for n, _f, _d in _od.build_catalog(_cfg)]
        out: dict[str, int] = {}
        for n in _names:
            ent = iref.find(n)[0]
            if ent is not None:
                out[ent["family"]] = out.get(ent["family"], 0) + 1
        return out
    live = _live_families()
    # ── 状態「在る」＝いま材料カタログに在る指標の種類 ──
    for e in iref.REFS:
        fam = e["family"]
        lin = iref.FAMILY_LINEAGE.get(fam, {}).get("k", "")
        q = iref.LINEAGE_QUESTION.get(lin, ("", ""))[0]
        if live.get(fam, 0) == 0:
            keep = next((k for d, k in _drop_map.items() if (iref.find(d)[0] or {}).get("family") == fam), "")
            st = ("省いた（同じ挙動＝残したのは " + keep + "）") if keep else "省いた（列が無い）"
        else:
            st = "在る"
        rows.append(dict(名前=fam, 系統=lin, 答える問い=q,
                         使える役割="・".join(rbl.get(lin, [])) or "（どの役割にも割り当てが無い）",
                         計算の出どころ=_source_note(fam, e["ext"] is not None),
                         グループ=_GROUP_TBD, 状態=st))
    # ── 状態「在る」の続き＝参照表 REFS の外にある材料（別の定義表で管理されているもの）──
    #   ★2026-08-09 に、最初この3種類が抜けた材料の正本を出してしまい、自分で気づいて足した。
    #     「答える問い」の表に 需給・時間帯 が在るのに、その系統の行が1つも無かったのが手がかり。
    def _extra(name: str, ref: str, where: str, note: str = "", lin_key: str | None = None) -> None:
        lin = iref.FAMILY_LINEAGE.get(lin_key or name, {}).get("k", "")
        rows.append(dict(名前=name, 系統=lin,
                         答える問い=iref.LINEAGE_QUESTION.get(lin, ("", ""))[0],
                         使える役割=("・".join(rbl.get(lin, [])) or "（どの役割にも割り当てが無い）") + note,
                         計算の出どころ=f"うちの自前の式／定義表 {where}／照合の相手: {ref}",
                         グループ=_GROUP_TBD, 状態="在る"))
    for nm in iref.DEMAND_REF:
        _extra(nm, "検査6（元データの重複・整合・欠け・被覆）", "indicator_reference_diag.DEMAND_REF")
    for nm in getattr(iref, "TIME_REF", {}):
        _extra(nm, "無し（時刻と曜日は元データそのもの）", "indicator_reference_diag.TIME_REF")
    for nm, v in iref.RANGE_GEO_REF.items():
        # kind=price の帯の4隅と mid は、条件の材料に使えない（H6 価格非依存）。
        # 出どころ＝signal_families.json の extra_parts.geo.rule（機械で引く・書き写さない）。
        ng_note = ("（★ただし条件の材料には使えない＝placement の幾何参照専用・H6）"
                   if v.get("kind") == "price" else "")
        _extra(f"レンジ幾何 {nm}", "検査8（定義表・既知答え・切り詰め再計算・被覆）",
               "indicator_reference_diag.RANGE_GEO_REF", ng_note, lin_key="レンジ幾何")
    # ── 状態「足す」「入れない」＝ライブラリに在って、うちの材料に無いもの ──
    covered = {fn for fns, _n in iref.INDUSTRY_MAP.values() for fn in fns}
    for fn, cat in lib.items():
        if fn in covered:
            continue
        skip = iref.INDUSTRY_SKIP.get(fn)
        rows.append(dict(名前=fn, 系統=f"（未定・ライブラリの分類は {cat}）",
                         答える問い=("（指標ではない）" if skip else _TBD),
                         使える役割=("（指標ではない）" if skip else _TBD),
                         計算の出どころ="ライブラリ pandas-ta-classic",
                         グループ=_GROUP_TBD,
                         状態=(f"入れない（{skip}）" if skip else "足す")))
    counts = {"在る": sum(1 for r in rows if r["状態"] == "在る"),
              "足す": sum(1 for r in rows if r["状態"] == "足す"),
              "入れない": sum(1 for r in rows if r["状態"].startswith("入れない"))}
    # ── 段5（2026-08-09 追加）＝engine_tuner が選べるか ＋ 足すものの一覧 ＋ 入れない一覧 ──
    ev = _engine_view() if lib else None
    if ev is not None:
        for r in rows:
            r["engine_tuner"] = _row_engine(r, ev)
        # ★承認の欄（2026-08-10 新設）＝まこさんが実際に承認した19件（2026-08-09）だけを ✅ にする。
        #   それ以降に CC が足したものは ★未承認。文書が全件を「承認済み」と書いていたのを是正した。
        skip_rows = [dict(名前=fn, 理由=iref.INDUSTRY_SKIP[fn],
                          承認=iref.SKIP_APPROVED.get(fn, "★未承認"))
                     for fn in iref.INDUSTRY_SKIP if fn in lib]
        gaps = _gaps(ev, counts, counts["足す"], skip_rows)
        engine = dict(選べる指標の種類=len(ev["selectable_fams"]),
                      選べない指標の種類=len(ev["unselectable_fams"]),
                      選べる組=len(ev["pool"]), 時間足=len(ev["tfs"]),
                      選べる列=ev["cols_selectable"], カタログ総列数=ev["cat_total"],
                      レンジ幾何=ev["geo_ok"], 時間帯=ev["time_ok"], 期間=ev["params"])
    else:
        for r in rows:
            r["engine_tuner"] = _SEL_NA
        skip_rows, gaps, engine = [], [], {}
    return dict(rows=rows, counts=counts,
                lineage_question={k: dict(問い=v[0], 出典=v[1]) for k, v in iref.LINEAGE_QUESTION.items()},
                library_ready=bool(lib), library_funcs=len(lib),
                gaps=gaps, skip_rows=skip_rows, engine=engine)


def _body_hash(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def _render_parts(p: dict) -> list[str]:
    """★6｜条件の部品の一覧（段C の C-1）。中身は condition_parts.json＝ここで新しい事実を書かない。"""
    L = ["", "## ★6｜条件の部品の一覧（engine_tuner が条件を組み立てる部品）", "",
         "**★この節は機械が作ります（手書きゼロ）。**中身の正本＝`.claude/ratchet/condition_parts.json`。", "",
         f"**対象**＝{p.get('scope', '')}", "",
         "**なぜ部品で持つか。**" + p.get("note", ""), "",
         "**どうやって決めたか。**" + p.get("how", ""), ""]
    L += ["**照らした相手（業界の実物）**", "",
          "| 出どころ | 部品の数 | 取り方 | 中身 |", "|---|---|---|---|"]
    for s in p["sources"]:
        n = "—" if s.get("n") is None else str(s["n"])
        how = "**毎回 機械で数え直す**" if s["how"] == "live" else "記録（機械では数え直せない）"
        # 出どころが URL でないもの（このプロジェクトに入っているライブラリ）はリンクにしない
        nm = f"[{s['name']}]({s['url']})" if s["url"].startswith("http") else f"{s['name']}（このプロジェクトに入っている）"
        L.append(f"| {nm} | {n} | {how} | {s['detail']} |")
    L += ["", f"**いま在る部品＝{len(p['rows_have'])} 個。足りない部品＝{len(p['rows_missing'])} 個。"
              f"合計 {len(p['rows_have']) + len(p['rows_missing'])} 個。**", ""]
    L += ["### いま在る部品", "", "| # | 部品 | どこに在るか | 実物 | 業界の同じもの |", "|---|---|---|---|---|"]
    for i, r in enumerate(p["rows_have"], 1):
        L.append(f"| {i} | **{r['name']}** | {r['where']} | {r['impl']} | {'・'.join(r['src'])} |")
    L += ["", "### 足りない部品", "", "| # | 部品 | これがあると書ける条件 | 業界の同じもの |", "|---|---|---|---|"]
    for i, r in enumerate(p["rows_missing"], len(p["rows_have"]) + 1):
        L.append(f"| {i} | **{r['name']}** | {r['can_write']} | {'・'.join(r['src'])} |")
    L += ["", "### 要らないと判断したもの（理由つき・★判定は CC が書きました）", "",
          "| 業界に在る部品 | 要らない理由 |", "|---|---|"]
    for r in p["rows_no"]:
        L.append(f"| {r['name']} | {r['why']} |")
    L += ["", "### いまの11個の形が、どの部品でできているか（実物のコードを分解した）", "",
          "| 形 | 部品 |", "|---|---|"]
    for f, ps in p["forms"].items():
        L.append(f"| `{f}` | {'・'.join(ps)} |")
    L += ["", "### 番人（毎回 実物で確かめる）", ""]
    L.append(f"- pandas-ta の「使い方」の関数＝実測 **{len(p['live'].get('pandas_ta', []))} 件**"
             f"（{'・'.join(p['live'].get('pandas_ta', []))}）")
    L.append(f"- 「閾値とのクロス」（RSI が 70 を上抜けた）を実行器の検証器に渡した結果＝**{p['live'].get('cross_value','')}**")
    if p.get("unused"):
        L.append(f"- ⚠️ 分解の表がどの形からも使っていない部品＝{p['unused']}")
    if p["ng"]:
        L += ["", f"**❌ {len(p['ng'])} 件**"] + [f"- {x}" for x in p["ng"]]
    else:
        L += ["", "**✅ ずれ 0 件**（形の数・部品の名前・業界の数・閾値とのクロス、すべて実物と一致）"]
    return L


def _render_matrix(m: dict) -> list[str]:
    """★7｜指標 × 部品 の突き合わせ（段C の C-3）。判定は毎回 機械が実物に当てて出す。"""
    L = ["", "## ★7｜指標 × 部品 の突き合わせ（どの指標に、どの部品が使えるか）", "",
         "**★この節は機械が作ります（手書きゼロ）。**判定のたびに、実行器の検証器へ実際に条件を渡して確かめます。", "",
         "### 指標の内訳（列を2本 並べられるかが、ここで決まる）", "",
         "| 何 | 数 |", "|---|---|",
         f"| 指標の種類 | **{m['n_fam']}** |",
         f"| うち **パラメータを2つ以上 持つ**（同じ指標のパラメータ違いで 2本 並べられる） | **{m['n_multi']}** |",
         f"| うち パラメータが1つだけ | {m['n_one']} |",
         f"| うち パラメータが無い | {m['n_none']} |",
         f"| 時間足 | {m['n_tf']} |", "",
         "### 部品を「何が要るか」で分けると", "",
         "| 何が要るか | 部品 | 使える指標の数 |", "|---|---|---|",
         f"| **材料 1本** | 値を持ってくる・n本 ずらす・n本の平均・絶対値・比べる・掛け算・値が在るか"
         f"（＋足りない部品の n本の最大値・最小値・順位・ばらつき） | **{m['n_fam']}（全部）** |",
         f"| **材料 2本** | 引き算（差・クロス・タッチ）（＋足りない部品の 割り算・2本の相関） | "
         f"**{m['n_multi']}**（同じ指標のパラメータ違いに限る） |",
         "| **条件を受ける** | かつ・でない・n本のうち 全部／どれか・条件を n本 ずらす（＋足りない部品の どれか満たす・何本前に成立したか） | 指標に依らない |",
         "", "### ★業界の定番のクロスが、いま作れるか（1件ずつ 機械が判定）", "",
         "**実行器**＝条件を検証器に渡して通るか。**生成器**＝engine_tuner が実際にその組を作るか。", "",
         "| 定番のクロス | 実行器 | 生成器 | 注 |", "|---|---|---|---|"]
    for r in m["rows"]:
        L.append(f"| {r['name']} | {r['exec_ok']} | {r['gen_ok']} | {r['note']} |")
    if m["blocked"]:
        L += ["", f"**❌ 実行器は受け付けるのに、生成器が作らない定番のクロス＝{m['blocked']} 件。**", "",
              "**理由**＝生成器が「列2本の形」を作るとき、**同じ指標のパラメータ違い**しか組みません",
              "（`engine_tuner_gen._pair_materials`）。**別の指標どうしの組は、Stoch%K と %D の1組だけが",
              "コードに直書きで例外扱いされています。**", "",
              "**＝MACD のクロスは、engine_tuner が何回 走っても出てきません。**",
              "これは 2026-08-08 のインシデント #15（組み立ての決まりで MACD のクロスを潰した）と同じものが、",
              "別の場所（生成器の対の作り方）に残っていたということです。", "",
              "**★直すのはマイルストーン②です。**この節は「いまどうなっているか」を出すところまでです。"]
    else:
        L += ["", "**✅ 定番のクロスは全部 作れます。**"]
    return L


def render_md(body: dict) -> str:
    h = _body_hash(body)
    c = body["counts"]
    L = [f"<!-- MATERIALS hash={h} gen_materials.py が自動生成＝手で書き換えない -->",
         "# materials.md — 材料の正本（1枚・全自動生成・CC の手書きの行ゼロ）", "",
         "**1行＝1つの指標の種類です。**期間で行を分けていません（CCI9 と CCI20 を別の行にしない）。",
         "理由＝要件の「作ってはいけないもの」2番（探す値を先に点の一覧で限定するもの）に当たるためです。",
         "期間は範囲の軸として engine_tuner が探します。", "",
         f"**いまの数＝在る {c['在る']} 件 ／ 足す {c['足す']} 件 ／ 入れない {c['入れない']} 件"
         f"（合計 {len(body['rows'])} 行）。**", "",
         "> ★「入れない」の承認は**1件ずつ ★4 の表に出しています**（全部が承認済みではありません）。",
         "> 既定は「入れる」です（まこさん決定＝「利益最大化するために完全に不要な指標以外はすべて入れてほしい」）。",
         "> ですからここに載っているのは「指標ではないもの」だけです。", "",
         "> ⚠️ 「グループ」の欄は、この段では全部 空です（フロー 段8 で埋めます）。", ""]
    e = body.get("engine") or {}
    if e:
        L += ["## ★1｜足すものの一覧（フロー 段5・まこさんが見るのはここです）", "",
              "**4か所に散っていた不足を、機械が1つにまとめました。**下の A〜G が、これから足す候補の全部です。",
              "**この段では1件も足しません。**足すのは段6 です。", "",
              "| 印 | 何を足すか | 数 | 出どころ |", "|---|---|---|---|"]

        for g in body["gaps"]:
            L.append(f"| {g['印']} | {g['何を足すか']} | **{g['数']} {g['単位']}** | {g['出どころ']} |")
        L += ["", "**中身（名前の一覧）**", ""]
        for g in body["gaps"]:
            L.append(f"- **{g['印']}（{g['数']} {g['単位']}）** … {g['中身']}")
        L += ["",
              "> ★印 B・C・G は、検査9・検査10・検査7 が出したものではありません。**段5 で新しく数えたものです。**",
              "> 段6 で A（業界の指標）だけを材料カタログに足しても、engine_tuner はそれを条件に選べません。",
              "> 選べるようにするには B の入口（下の ★2）も一緒に直す必要があります。", "",
              "## ★2｜engine_tuner がいま条件の材料として選べるもの（段5 で機械が数えた）", "",
              "**材料カタログに在ることと、engine_tuner が条件に選べることは別です。**",
              "下は、生成器（engine_tuner_gen）が実際に選べるものを実物から数えた結果です。", "",
              "| 何 | 数 |", "|---|---|",
              f"| 材料カタログの列（部品 × 時間足） | {e['カタログ総列数']} 列 |",
              f"| **engine_tuner が選べる列** | **{e['選べる列']} 列"
              f"（{100.0 * e['選べる列'] / max(e['カタログ総列数'], 1):.1f}%）** |",
              f"| engine_tuner が選べる指標の種類 | **{e['選べる指標の種類']} 種類** |",
              f"| **engine_tuner が選べない指標の種類** | **{e['選べない指標の種類']} 種類**（上の一覧 B） |",
              f"| そのほかに選べるもの（レンジ幾何） | {'・'.join(e['レンジ幾何']) or '（無し）'} |",
              f"| そのほかに選べるもの（時間帯） | 時刻だけ（型の表は {'・'.join(e['時間帯'])} を許す） |",
              "",
              "**何が「選べる」を決めているか**＝実行器の `FAMILY_TEMPLATES`（列名の組み立て表）に",
              "載っていない指標は、レシピの読み込みの段階で `G6` が拒否します。",
              "**★2026-08-11（段6 の 6-7）に、この表を「手書き19件」から「参照表から機械で作る」形に変えました。**",
              "参照表 `indicator_reference_diag.REFS`（材料カタログの列名の正本）の正規表現から、",
              "名前の組み立ての型を機械で作ります＝材料カタログに列が増えれば、そのまま選べるようになります。",
              "**直す前は 232種類 が選べませんでした**（MACD・BB%b・一目の転換線と基準線・ローソク足の形 ほか。",
              "5,049列 のうち選べるのは 432列＝8.6% だけ）。**直したあとの実測は上の表のとおりです。**",
              "番人＝`engine_tuner_exec.py --selftest` の往復テスト（カタログの全列名を分解して組み立て直し、",
              "1文字も違わないこと＋わざと型を1件 壊すと落ちること）。", "",
              "> ⚠️ **ここで言う「選べる」は、レシピの読み込みが拒否しないという意味です。**",
              "> 生成器が実際にその部品を引くかどうかは、承認済みの型の表（`signal_families.json`）に",
              "> その部品が載っているかで決まります（材料が増えたぶんを表に反映するのが 6-6 です）。", "",
              "## ★3｜パラメータ（指標を作るときのローソク足の本数）が、決まった数字だけに固定されている", "",
              "**（マイルストーン③の対象。段5 は事実を出すだけで、直しません。）**", "",
              "**ここで言う数字は、ローソク足の本数です。**指標を計算するとき、直近の何本分のローソク足を使うかを",
              "先に決めます。RSI7 の「7」は 直近7本、RSI14 の「14」は 直近14本、という意味です。",
              "5分足なら 7本＝35分ぶん、14本＝70分ぶんになります。本数が少ないほど直近の値動きに素早く反応し、",
              "多いほどゆっくり動きます。", "",
              "**これは「パラメータ」です。「閾値」ではありません。**",
              "パラメータ＝指標を作るときの設定（RSI14 の 14＝本数）。",
              "閾値＝できあがった値の区切り（「RSI が 70 を超えたら」の 70）。**この表に閾値は出てきません。**", "",
              "**engine_tuner が試せる本数は、下の数字だけです。**この一覧に無い本数は、何回 試しても永久に出ません。",
              "例＝RSI で試せるのは 7本・9本・14本・21本 の4つだけで、RSI12（12本）も RSI30（30本）も出てきません。",
              "本来の形は「範囲で探す」＝7本 から 200本 までの、どの整数でもよい、という探し方です。",
              "いまは、要件の「作ってはいけないもの」2番（原文＝探す値を、CC が先に「点の一覧」で限定するもの）に",
              "当たる状態です。数字の出どころ＝`scripts/priority_rebuild/observe_config.json` の `*_periods` の行。", "",
              "| 指標の種類 | いま試せるローソク足の本数 |", "|---|---|"]
        for k, v in e["期間"].items():
            # ★数字が2つ以上の指標（MACD線%(12,26) のような形）は、組で1通りと数える（6-7・2026-08-11）
            if any(isinstance(x, (list, tuple)) for x in v):
                s = "・".join("(" + ",".join(str(y) for y in x) + ")" for x in v)
                L.append(f"| {k} | {s}（{len(v)} 通り・数字が2つ以上の指標は組で1通り） |")
            else:
                L.append(f"| {k} | {' 本・'.join(str(x) for x in v)} 本（{len(v)} 通り） |")
        # ★★使い方（条件の形）の一覧＝2026-08-11 まこさん指示で材料の正本に入れた。
        #   逐語＝「一覧の正本は materials.md だと思うけど。そこには使い方一覧は入れないの？」
        #        「すべて自動生成にして」。だから この節は1行も手で書かず、実物から機械で引く。
        _fm = forms_table()
        L += ["", "## ★5｜使い方の一覧（条件の形）＝指標をどう条件にするか", "",
              "**★この節は機械が実物から引いて書きます（手書きゼロ）。**",
              f"形の名前と数＝`engine_tuner_exec.py` の `FORMS`（実行器が本当に実行できる形）。",
              f"何をするか・必要な値＝`{_fm['doc']}` の §2.2 の表。", "",
              "**なぜ材料の正本に入れるか。**指標の一覧だけを見て「この列が無い＝engine_tuner は作れない」と",
              "判定すると間違えます。**2026-08-11 に実際に間違えました**（RSI の差の列が無いことを理由に",
              "「作れない」と報告したが、下の `slope` で作れた）。**指標と使い方は、同じ1枚で突き合わせます。**", "",
              f"**いま実行器が実行できる形＝{_fm['n_forms']} 種類。**", "",
              "| 形 | 何をするか | 使う材料 | 必要な値 | 実例 | 入れ子 |",
              "|---|---|---|---|---|---|"]
        for r in _fm["rows"]:
            L.append(f"| `{r['形']}` | {r['和名']} | {r['材料']} | {r['必要な値']} | {r['実例']} | {r['入れ子']} |")
        if _fm["ng"]:
            L += ["", f"**❌ 実行器に在るのに説明が見つからない形が {len(_fm['ng'])} 件**"
                      f"（{'・'.join(_fm['ng'])}）＝実物と説明がずれています。"]
        else:
            L += ["", "**✅ 実行器の形すべてに説明が付いています（実物と説明のずれ 0 件）。**"]
        L += ["", "**★使い方の側にも「決まった数字だけ」の縛りがあります。**",
              "例＝`slope`（いまの値 − n本前の値）の n として engine_tuner が選べるのは、",
              "`recipes/search_limits.json` の `int_grid` に並んだ数字だけです。**ここも ★3 と同じで、",
              "マイルストーン③（範囲で探せるようにする）の対象です。**"]
        L += _render_parts(condition_parts())
        L += _render_matrix(parts_matrix())
        _ok = sum(1 for s in body["skip_rows"] if s.get("承認", "").startswith("✅"))
        _po = sum(1 for s in body["skip_rows"] if s.get("承認", "").startswith("◯"))
        _no = len(body["skip_rows"]) - _ok - _po
        L += ["", "## ★4｜入れないと判断したもの（理由つき・★承認の欄を1件ずつ出します）", "",
              f"**{len(body['skip_rows'])} 件です。**既定は「入れる」なので、ここに載るのは",
              "**指標ではないもの**と、**うちに既に同じものが在るもの**だけです。",
              "（まこさん決定＝「利益最大化するために完全に不要な指標以外はすべて入れてほしい」）", "",
              "**★印は3種類です**（まこさん OK 2026-08-10）。"
              "**まこさんが見る必要があるのは ★未承認 だけです。**", "",
              "| 印 | 意味 | 件数 |",
              "|---|---|---|",
              f"| ✅ | **まこさんが名指しで「入れない」と言われたもの**"
              f"（2026-08-09「1,2,3,4全部いれないくていい」「willrは入れない」／2026-08-10「３は入れない」） | **{_ok} 件** |",
              f"| ◯ | **まこさんが方針を承認したもの**（2026-08-09 の逐語「他にも同じ挙動の指標があれば"
              f"紛らわしいので片方を省いていく」）。★**同じ挙動かどうかの判定は CC が実測でやりました**"
              f"＝まこさんは1件ずつ見ていません | **{_po} 件** |",
              f"| ★未承認 | **上のどちらにも当たらないもの** | **{_no} 件** |", "",
              "⚠️ 2026-08-10 まで、この文書は全件を「承認済み」と書いていました（承認の偽装）。是正しました。", "",
              "| ライブラリの関数 | 承認 | 入れない理由 |", "|---|---|---|"]
        for s in body["skip_rows"]:
            L.append(f"| {s['名前']} | {s.get('承認', '★未承認')} | {s['理由']} |")
        L += [""]
    L += ["## 答える問いの出どころ（系統ごと・1行ずつ）", "",
          "| 系統 | 答える問い | 出典 |", "|---|---|---|"]
    for k, v in body["lineage_question"].items():
        L.append(f"| {k} | {v['問い']} | {v['出典']} |")
    cols = ("名前", "系統", "答える問い", "使える役割", "計算の出どころ",
            "グループ", "状態", "engine_tuner")
    L += ["", "## 材料の一覧", "",
          "| " + " | ".join(cols) + " |",
          "|" + "---|" * len(cols)]
    for r in body["rows"]:
        L.append("| " + " | ".join(r[k] for k in cols) + " |")
    L += ["", "## この表の作り方（正本＝ここから機械で引いています）", "",
          "| 欄 | どこから引いたか |", "|---|---|",
          "| 名前 | `indicator_reference_diag.REFS` の family（指標の種類 53 件） |",
          "| 系統 | `indicator_reference_diag.FAMILY_LINEAGE` |",
          "| 答える問い | `indicator_reference_diag.LINEAGE_QUESTION`（上の表に出典つきで出しています） |",
          "| 使える役割 | `.claude/ratchet/signal_families.json` の `role_lineage.roles`（役割ごとに使える系統） |",
          "| 計算の出どころ | `INDUSTRY_MAP`（ライブラリに同じものが在るか）＋ `REFS[ext]`・`EXT2`（照合の相手） |",
          "| グループ | 空（フロー 段8 で埋める） |",
          "| 状態 | 在る＝参照表に登録済み ／ 足す・入れない＝`pandas_ta_classic.Category` と `INDUSTRY_SKIP` |",
          "| engine_tuner | `engine_tuner_exec.FAMILY_TEMPLATES`（生成器が名前を組み立てられる指標）"
          "＋ `engine_tuner_gen.material_pool`（実際の候補）＋ `signal_families.json` の `extra_parts` |",
          "", f"（業界のライブラリの関数 {body['library_funcs']} 種類を読み込みました"
          f"{'' if body['library_ready'] else '＝★入っていないので 足す・入れない の行が出ていません'}）", ""]
    return "\n".join(L) + "\n"


def write() -> int:
    body = build_body()
    if not body["library_ready"]:
        print("❌ pandas-ta-classic が入っていない＝『足す』『入れない』の行が作れない。requirements.txt の版で入れる")
        return 1
    _MD.write_text(render_md(body), encoding="utf-8")
    _JSON.write_text(json.dumps(dict(body=body, _本文の指紋=_body_hash(body)),
                                ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c = body["counts"]
    print(f"[作成] {_MD}（{len(render_md(body).splitlines())} 行）")
    print(f"[作成] {_JSON}")
    print(f"  在る {c['在る']} ／ 足す {c['足す']} ／ 入れない {c['入れない']} ／ 指紋 {_body_hash(body)}")
    return 0


def verify() -> list[str]:
    """手で書き換えられていないか／正本とずれていないかを検出する。"""
    ng: list[str] = []
    if not _MD.exists():
        return ["[未生成] materials.md が無い（--write で作る）"]
    body = build_body()
    if not body["library_ready"]:
        return ["pandas-ta-classic が入っていない＝突き合わせ不能"]
    want = render_md(body)
    got = _MD.read_text(encoding="utf-8")
    if got != want:
        ng.append("materials.md が正本と一致しない（手で書き換えたか、元が変わったのに作り直していない）"
                  f"＝いまの指紋 {_body_hash(body)}")
    if _JSON.exists():
        j = json.loads(_JSON.read_text(encoding="utf-8"))
        if j.get("_本文の指紋") != _body_hash(body):
            ng.append("materials.json の指紋が正本と合わない（--write で作り直す）")
    else:
        ng.append("materials.json が無い（--write で作る）")
    return ng


def selftest() -> int:
    ng: list[str] = []
    body = build_body()
    rows = body["rows"]
    # T1 在るの行数＝4つの定義表の件数の合計と一致する（1つでも取りこぼしたら落ちる）
    want_n = (len(iref.REFS) + len(iref.DEMAND_REF) + len(getattr(iref, "TIME_REF", {}))
              + len(iref.RANGE_GEO_REF))
    # ★「省いた（同じ挙動）」の行も定義表の側では数える（2026-08-11・まこさん OK で省いたため）
    _kept_or_dropped = body["counts"]["在る"] + sum(
        1 for r in rows if str(r["状態"]).startswith("省いた"))
    if _kept_or_dropped != want_n:
        ng.append(f"T1: 『在る』＋『省いた』の行数 {_kept_or_dropped} が定義表の合計 {want_n} 件と合わない"
                  f"（参照表 {len(iref.REFS)}＋需給 {len(iref.DEMAND_REF)}"
                  f"＋時間帯 {len(getattr(iref, 'TIME_REF', {}))}＋レンジ幾何 {len(iref.RANGE_GEO_REF)}）")
    # T1-2 「答える問い」の表に在る系統は、材料の行にも必ず出てくる（表だけ在って中身が無いのを防ぐ）
    used_lin = {r["系統"] for r in rows if r["状態"] == "在る"}
    for lin in iref.LINEAGE_KINDS:
        if lin not in used_lin:
            ng.append(f"T1-2: 系統『{lin}』の材料が1行も無い（答える問いの表にだけ在る状態）")
    # T2 在るの行に、系統・答える問い・使える役割の空欄が無い
    for r in rows:
        if r["状態"] != "在る":
            continue
        for k in ("系統", "答える問い"):
            if not r[k]:
                ng.append(f"T2: 『{r['名前']}』の{k}が空（正本から引けていない）")
        if r["系統"] not in iref.LINEAGE_KINDS:
            ng.append(f"T2: 『{r['名前']}』の系統『{r['系統']}』が系統の一覧に無い")
    # T3 グループの欄はこの段では全部 空（段8 の前）
    if any(r["グループ"] != _GROUP_TBD for r in rows):
        ng.append("T3: グループの欄が埋まっている行がある（埋めるのは段8）")
    # T4 期間で行を分けていない。
    #   ★数字が入っているかでは見ない（pivotR1 の「1」は期間ではなく水準の名前）。
    #   参照表の照合にかけて「パラメータが付いた形（RSI14 など）」になっていないかで見る。
    # ★「省いた（同じ挙動）」の行も、定義表には在る＝名前の突き合わせでは同じ側に数える
    #   （2026-08-11・まこさん OK で同じ挙動の列を省いたため）。
    got_names = {r["名前"] for r in rows if r["状態"] == "在る" or r["状態"].startswith("省いた")}
    want_names = ({e["family"] for e in iref.REFS} | set(iref.DEMAND_REF)
                  | set(getattr(iref, "TIME_REF", {}))
                  | {f"レンジ幾何 {k}" for k in iref.RANGE_GEO_REF})
    if got_names != want_names:
        ng.append(f"T4: 『在る』の名前が参照表の指標の種類と一致しない"
                  f"（余分 {sorted(got_names - want_names)[:3]} ／ 欠け {sorted(want_names - got_names)[:3]}）")
    for nm in sorted(got_names):
        _e, _p = iref.find(nm)
        if _e is not None and _p:
            ng.append(f"T4: 『{nm}』は期間つきの名前（1行＝指標の種類の決まりに反する）")
    # T5 答える問いの出どころが、系統の数だけ揃っている
    if set(body["lineage_question"]) != set(iref.LINEAGE_KINDS):
        ng.append("T5: 答える問いの表が、系統の一覧と食い違う")
    # ── 段5（2026-08-09 追加）の番人 ──
    # T7 engine_tuner の欄が全行に在り、「在る」の行に判定不能が混ざっていない
    for r in rows:
        if not r.get("engine_tuner"):
            ng.append(f"T7: 『{r['名前']}』に engine_tuner の欄が無い")
        elif r["状態"] == "在る" and r["engine_tuner"] == _SEL_NA:
            ng.append(f"T7: 『{r['名前']}』は材料に在るのに engine_tuner の欄が『まだ入っていない』")
    # T8 足すものの一覧の数が、いま材料の一覧に出ている「足す」の件数と一致する（表と一覧の食い違い防止）
    ga = {g["印"]: g for g in body.get("gaps", [])}
    if ga and ga["A"]["数"] != body["counts"]["足す"]:
        ng.append(f"T8: 足すものの一覧 A の {ga['A']['数']} が、材料の一覧の『足す』{body['counts']['足す']} 件と合わない")
    # T8-2 「選べない指標の種類」の数が、一覧 B の数と一致する
    if ga and ga["B"]["数"] != body["engine"]["選べない指標の種類"]:
        ng.append("T8-2: 一覧 B の数が engine_tuner の集計と合わない")
    # T10 段6 の前に「在る」だった指標が、いま1件も消えていない（2026-08-11・段6 の 6-9②）
    #   ★何を守るか＝業界のライブラリの指標を大量に足す作業（段6）の途中で、うちが元から持っていた
    #     指標（cat 独自のもの＝外部に照合の相手がいないものを含む）を うっかり消していないこと。
    #     一覧は git から取り出す＝記憶や書き写しではない。
    _lost, _base_n = _kept_since_stage6()
    if _lost:
        ng.append(f"T10: 段6 の前に在った指標が消えている（{len(_lost)}/{_base_n} 件）: {'・'.join(_lost)}")
    # T9 わざと FAMILY_TEMPLATES から1件 消すと「選べない」が1件 増える（この検査が生きていることの確認）
    try:
        import engine_tuner_exec as _ex
        _keep = dict(_ex.FAMILY_TEMPLATES)
        _base = len(_engine_view()["unselectable_fams"])
        _ex.FAMILY_TEMPLATES.pop("RSI", None)
        _cut = len(_engine_view()["unselectable_fams"])
        if _cut != _base + 1:
            ng.append(f"T9: FAMILY_TEMPLATES から1件 消しても『選べない』が増えない（{_base} → {_cut}）")
    except Exception as _e:                                      # noqa: BLE001
        ng.append(f"T9: 実行器を読み込めないので『選べるか』の検査を確かめられない（{str(_e)[:60]}）")
    finally:
        try:
            _ex.FAMILY_TEMPLATES.clear()
            _ex.FAMILY_TEMPLATES.update(_keep)
        except Exception:                                        # noqa: BLE001
            pass
    # T6 わざと書き換えると --verify が鳴る（メタ確認）
    if _MD.exists():
        keep = _MD.read_text(encoding="utf-8")
        try:
            _MD.write_text(keep + "この行は手で足しました\n", encoding="utf-8")
            if not verify():
                ng.append("T6: 手で書き足しても --verify が鳴らない（改変検出が死んでいる）")
        finally:
            _MD.write_text(keep, encoding="utf-8")
        if verify():
            ng.append("T6: 元に戻したのに --verify が鳴る（番人の後始末ができていない）")
    else:
        ng.append("T6: materials.md が無いので改変検出を確かめられない（先に --write）")
    print("=" * 70)
    print("gen_materials 自己検査")
    print("=" * 70)
    for x in ng:
        print("  ❌ " + x)
    print("  ✅ 全部 pass" if not ng else f"  ❌ {len(ng)} 件")
    return 1 if ng else 0


def status() -> int:
    body = build_body()
    c = body["counts"]
    print(f"materials.md: {'在る' if _MD.exists() else '無い'} ／ 在る {c['在る']} ／ 足す {c['足す']}"
          f" ／ 入れない {c['入れない']} ／ 指紋 {_body_hash(body)}")
    for x in verify():
        print("  ❌ " + x)
    return 0


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--verify" in argv:
        ng = verify()
        for x in ng:
            print("  ❌ " + x)
        print("  ✅ 一致（手で書き換えられていない）" if not ng else "")
        return 1 if ng else 0
    if "--write" in argv:
        return write()
    if "--status" in argv:
        return status()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
