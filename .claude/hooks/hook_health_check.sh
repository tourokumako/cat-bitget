#!/bin/bash
# hook_health_check.sh — SessionStart（2026-07-04 まこさん承認で新設）
# hook 無言死の検出（pdca_mark 2026-06-29〜07-03 無言死事案＝python SyntaxError を exit 0 が握りつぶし
# 旗管理が全停止していた、の横展開対策）。表示専用＝常に exit 0（ブロックしない）。
#  ① settings.json（共有・git 管理＝hook 登録の正本）＋ settings.local.json（ローカル上書き）両方に登録された全 hook .sh の実在・実行権限
#  ② hooks/*.py 全部の py_compile（構文死の検出）
#  ③ state/*_error.log の非空（fail-open で握りつぶされた実行時エラーの可視化）
#  ★2026-07-06: hook 登録を git 管理するため hooks ブロックを settings.local.json → settings.json へ移動（まこさん指示）。両方を走査。
HOOKS_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/hooks"
STATE_DIR="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state"
SETTINGS_MAIN="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/settings.json"
SETTINGS_LOCAL="/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/settings.local.json"
# ★2026-10-15＝試すときだけ、見本の設定に差し替えられる（HOOK_HEALTH_SETTINGS に見本のパスを入れて走らせる）
[ -n "${HOOK_HEALTH_SETTINGS:-}" ] && SETTINGS_MAIN="$HOOK_HEALTH_SETTINGS" && SETTINGS_LOCAL="/dev/null"
NG=0

# ① 登録 hook の実在・実行権限（settings.json＋settings.local.json 両方＝マージ後に効く全 hook）
# ★2026-10-15（まこさん「要ると思うが」・hook の見直しの3本目）＝拾い方を直した。直す前は、引用符の中がパスだけの登録しか拾わず、
#   「bash /…/x.sh」の形と .py の登録（41本のうち20本）を確かめていなかった。jq で command を全部 読み、パスを全部 拾う。
REG_CMDS=$(jq -r '.. | .command? // empty' "$SETTINGS_MAIN" "$SETTINGS_LOCAL" 2>/dev/null)
REG_FILES=$(printf '%s\n' "$REG_CMDS" | grep -oE '/[^ "]*/\.claude/hooks/[A-Za-z0-9_]+\.(sh|py)' | sort -u)
N_REG=$(printf '%s\n' "$REG_FILES" | grep -c .)
[ "$N_REG" -gt 0 ] || { echo "🔴 登録の hook を1本も拾えていない（拾い方が壊れた）"; NG=$((NG+1)); }
for f in $REG_FILES; do
  [ -f "$f" ] || { echo "❌ hook 不在: $f"; NG=$((NG+1)); }
done
# 実行権限が要るのは、パスを直接 書いた登録（前に bash・python3 を付けていない物）だけ
for f in $(printf '%s\n' "$REG_CMDS" | awk '{print $1}' | grep -E '/\.claude/hooks/[A-Za-z0-9_]+\.(sh|py)$' | sort -u); do
  if [ -f "$f" ] && [ ! -x "$f" ]; then echo "⚠️ 実行権限なし: $f"; NG=$((NG+1)); fi
done
# ①-b ★2026-10-15＝登録された .sh が呼ぶ本体の .py の実在。多くの .sh は本体が無いと黙って通す＝無言死の温床
for f in $(printf '%s\n' "$REG_FILES" | grep '\.sh$'); do
  [ -f "$f" ] || continue
  for b in $(grep -v '^[[:space:]]*#' "$f" | grep -oE '(\.claude/hooks/|\$HERE/|\$HOOKS/)[A-Za-z0-9_]+\.py' | sed -E 's#.*/##' | sort -u); do
    [ -f "$HOOKS_DIR/$b" ] || { echo "❌ hook の本体が無い: $HOOKS_DIR/${b}（$(basename "$f") が呼ぶ）"; NG=$((NG+1)); }
  done
done

# ② hooks/*.py の構文チェック（無言死の主因＝SyntaxError）
for p in "$HOOKS_DIR"/*.py; do
  [ -f "$p" ] || continue
  if ! python3 -m py_compile "$p" 2>/dev/null; then
    echo "❌ hook python 構文死（無言死の温床）: $p"; NG=$((NG+1))
  fi
done
# ②-b ★2026-10-15（hook の見直しの4本目で分かった）＝変数の直後に全角の文字を書いた行が無いか。
#   macOS の bash 3.2 は、UTF-8 の設定のとき、変数の直後の全角の文字を壊して読む＝表示の名前が「??」に化ける。${名前} と波括弧で囲む。
for f in $(printf '%s\n' "$REG_FILES" | grep '\.sh$'); do
  [ -f "$f" ] || continue
  hits=$(grep -nE '\$[A-Za-z_][A-Za-z0-9_]*[^ -~]' "$f" | grep -vE '^[0-9]+:[[:space:]]*#' | cut -d: -f1 | tr '\n' ' ')
  [ -z "$hits" ] || { echo "⚠️ 変数の直後に全角の文字（表示が化ける）: $(basename "$f") の ${hits}行"; NG=$((NG+1)); }
done

# ③ 実行時エラーログの可視化（fail-open で通した例外）
for lg in "$STATE_DIR"/*_error.log; do
  [ -s "$lg" ] || continue
  echo "⚠️ hook 実行時エラーあり（fail-open で素通りした可能性）: ${lg}（$(wc -l < "$lg" | tr -d ' ')行・要確認後クリア）"
  NG=$((NG+1))
done

# ④ ★合言葉（XXX_OK=1 で通す抜け道）が hook に戻っていないか（2026-08-16 まこさん指示「じゃあ強制解除できない状態にしろ」）
#    背景＝CC が同日に VERIFY_TOOL_OK=1 と FLOW_DECL_OK=1 を許可なく使った（worklog 20260816 §52.6）。
#    16箇所の通し判定を全部 消した。ここでは「通し判定の形」の行を数え、1件でも在れば 🔴 を出す。
#    ★注意＝説明文の中の文字列は数えない（通し判定の形＝grep -qE '…_OK=1' && exit 0 ／ "…_OK=1" in raw ／ '…_OK=1' in cmd）。
ESC=$(grep -nE "grep -qE '[A-Z0-9_]+_OK=1' && exit 0|\"[A-Z0-9_]+_OK=1\" in raw|'[A-Z0-9_]+_OK=1' in cmd" "$HOOKS_DIR"/*.sh "$HOOKS_DIR"/*.py 2>/dev/null)
if [ -n "$ESC" ]; then
  echo "🔴 合言葉（強制の解除）が hook に戻っている＝2026-08-16 に廃止したもの。まこさんへ報告:"
  printf '%s\n' "$ESC" | sed 's/^/     /'
  NG=$((NG+1))
fi
# ⑤ ★2026-10-15（hook の見直しの4本目・まこさん「要る 不具合はすべて修正する」）＝始めの表示と片づけ（reset_read_log.sh）が、
#   登録の無い hook の名前や、使う hook の無い印を扱っていないか。なぜ＝hook の登録を外しても reset_read_log.sh の表示と片づけが残り、
#   実物と違う表示（「強制 read」）と、使う hook の無い印の片づけが11個 残っていた。
RRL="${HOOK_HEALTH_RRL:-$HOOKS_DIR/reset_read_log.sh}"   # 試すときだけ、見本に差し替えられる（2026-10-15）
REG_BODIES=""
for f in $REG_FILES; do REG_BODIES="$REG_BODIES $f"; [ -f "${f%.*}.py" ] && REG_BODIES="$REG_BODIES ${f%.*}.py"; done
for n in $(grep -v '^[[:space:]]*#' "$RRL" | grep 'echo' | grep -oE '[a-z_]+\.sh' | sort -u); do
  printf '%s\n' "$REG_FILES" | grep -q "/$n\$" || { echo "⚠️ 始めの表示が、登録の無い hook を挙げている: ${n}（reset_read_log.sh）"; NG=$((NG+1)); }
done
for n in $(grep -v '^[[:space:]]*#' "$RRL" | grep -oE '\$(STATE_DIR|SESS_DIR)/[A-Za-z0-9_.]+' | sed 's#.*/##' | sort -u); do
  used=0
  for g in $REG_BODIES; do
    [ "$(basename "$g")" = "reset_read_log.sh" ] && continue
    grep -v '^[[:space:]]*#' "$g" | grep -q "$n" && { used=1; break; }
  done
  [ "$used" -eq 1 ] || { echo "⚠️ 始めの片づけが、使う hook の無い印を扱っている	: ${n}（reset_read_log.sh）"; NG=$((NG+1)); }
done

# ★2026-10-08（160回目・まこさん OK の案 3b）＝止められる打ち方の早見表
python3 /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/tools/try_hooks.py --cheatsheet --session "$(jq -r '.session_id // empty' 2>/dev/null)" 2>&1 || true
if [ "$NG" -eq 0 ]; then
  echo "✅ hook 健全性: 登録 ${N_REG}本の実在/実行権限・本体の .py の実在・hooks/*.py 構文・エラーログ・合言葉0件 ぜんぶ異常なし"
else
  echo "🔴 hook 健全性: 異常 ${NG} 件（上記）＝強制が効いていない可能性＝作業前にまこさんへ報告"
fi
exit 0
