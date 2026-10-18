#!/bin/bash
# L-239 ずれ防止: 新セッション開始時に「次セッション着手」ブロックの参照パスを自動 ls チェック。
# WORKFLOW.md 🔴 active ブロック + next_step.md から
# results/ scripts/ data/ .claude/ 配下の .parquet/.py/.md/.json/.csv/.joblib パスを抽出 → 存在確認。
# ❌欠落があれば、引き継ぎ記述が古い/思い込みの疑い → 着手前に疑う (= 学習済み誤断定・データ再作成の無駄を防ぐ)。
#
# ★2026-08-02 まこさん指示「この誤検知が度々発生しているので、今後一切このようなことを起こさない状態に」
#   原因＝パスを深い方（bitget-python-sdk-api）だけで探しており、リポジトリ直下にあるファイル
#   （.claude/rules/chat_writing_rules.md 等）を毎回「❌ 欠落」と誤報していた。
#   直し3点:
#     ① 探す場所を2つにした（リポジトリ直下 と bitget-python-sdk-api）。どちらかに在れば ✅。どこで
#        見つかったかも出す＝「似た名前のフォルダが2つある」ことが開始時に毎回見える。
#     ② この仕組み自体を毎回 自己検査する（下の SENTINEL）。既知答え3件＝直下にだけ在る／深い方にだけ
#        在る／本当に無い。1件でも外れたら大きく警告する＝検査が黙って壊れることを防ぐ。
#     ③ 見つからない時は、両方の場所で探した事実を出す（片方しか見ていない誤報と区別できる）。
REPO="/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SDK="$REPO/v3-bitget-api-sdk/bitget-python-sdk-api"
python3 - "$SDK" "$REPO" << 'PYEOF'
import sys, re, os, glob
SDK, REPO = sys.argv[1], sys.argv[2]
# 探す場所（名前, 実体）＝この2つが .claude を持つ全部（2026-08-02 実測・find で確認済み）
BASES = [("直下", REPO), ("sdk", SDK)]


def find_in_bases(rel: str):
    """相対パスを全部の場所で探し、見つかった場所の名前を返す（複数可・空なら本当に無い）。"""
    gp = re.sub(r'\{[^}]*\}', '*', rel)          # {label} 等テンプレ → glob
    gp = re.sub(r'Y{4}-?M{2}-?D{2}', '*', gp)    # 書き方の例の日付（YYYYMMDD・YYYY-MM-DD）→ glob（2026-10-15）
    hits = []
    for name, base in BASES:
        if glob.glob(os.path.join(base, gp)):
            hits.append(name)
    return hits


# ── ② 番人（既知答え）＝この仕組み自体が毎回自分を検査する ──────────────────────
SENTINEL = [
    (".claude/rules/chat_writing_rules.md", True, "直下にだけ在るファイル"),
    ("scripts/priority_rebuild/periods.py", True, "sdk にだけ在るファイル"),
    (".claude/rules/__this_file_never_exists__.md", False, "本当に無いファイル"),
    (".claude/state/session_worklog_YYYYMMDD.md", True, "書き方の例の日付を含むパス（同じ形の実物が在れば見つかる）"),
]
sent_ng = []
for rel, want, imi in SENTINEL:
    got = bool(find_in_bases(rel))
    if got != want:
        sent_ng.append(f"{imi}（{rel}）＝期待 {'見つかる' if want else '見つからない'} / "
                       f"実際 {'見つかった' if got else '見つからない'}")


def block(path, start_pat, end_pat=None):
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except Exception:
        return ""
    out, on = [], False
    for ln in lines:
        if not on and re.search(start_pat, ln):
            on = True
        elif on and end_pat and re.search(end_pat, ln):
            break
        if on:
            out.append(ln)
    return "\n".join(out)


# WORKFLOW の現在地 (🔴 現在地 → 次の見出し)。★2026-08-25 から現在地は「next_step.md §0 を見る」の1行だけ
#   （まこさん指示・改訂ブロックは archive/workflow/ へ移した）＝パスは next_step.md 側から拾う。
wf = block(f"{SDK}/WORKFLOW.md", r"🔴 現在(のフェーズ|地)", r"^## (改訂の履歴|🧊 改訂\d+ ブロック)")
# next_step.md（新セッションの起点・現行正本）
ns = block(f"{REPO}/.claude/state/next_step.md", r".")
text = wf + "\n" + ns

# ★2026-10-18（監査 CP79）＝日本語を含むパス（next_step.md の m2c15_全体の表.md）と .txt・.tsv・.jsonl も拾う。空白と引用符と括弧と句読点で切る。
pat = r'(?:results|scripts|data|\.claude)/[^\s`\'"|<>()（）「」『』〔〕【】、。，・…:：;；,]+\.(?:parquet|py|md|json|csv|joblib|txt|tsv|jsonl)'
paths = sorted(set(re.findall(pat, text)))

print("=== 次セッション着手: 参照パス存在チェック (自動・L-239 ずれ防止) ===")
if sent_ng:
    print("🚨 この検査自体が壊れている（番人が落ちた）＝下の ✅/❌ を信用しないでください:")
    for x in sent_ng:
        print(f"   ・{x}")
else:
    print("（番人 ✅ 4件 pass＝『直下にだけ在る』『sdk にだけ在る』『本当に無い』『書き方の例の日付』を正しく見分けられている）")
if not paths:
    print("⚠️ 引き継ぎブロックにファイルパスなし (= 実行可能テンプレ未記載の疑い・5列表で書き直せ)")
miss = 0
for p in paths:
    hits = find_in_bases(p)
    if hits:
        print(f"✅ {p}  ［{'／'.join(hits)}］")
    else:
        print(f"❌ 欠落: {p}  ［直下・sdk の両方で探して見つからない］")
        miss += 1
print(f"--- 欠落 {miss} / 計 {len(paths)} 件。❌ があれば引き継ぎ記述が古い/思い込みの疑い → 着手前に検証 ---")
print("--- ［直下］＝cat-bitget/ 直下の .claude ／［sdk］＝bitget-python-sdk-api/ の .claude。"
      "2つある理由は .claude/rules/README_folder_map.md ---")
PYEOF
exit 0
