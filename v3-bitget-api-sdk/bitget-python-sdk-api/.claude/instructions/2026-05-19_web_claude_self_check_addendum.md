⛔ archive: v2 系・v3 化で機械反映済 (2026-05-20 まこさん承認・本指示書は 2026-05-19 発行当時の追記内容を凍結)。
正本は `.claude/memory/learning_design_v3.md` (exchange_spec.md 準拠化済・2026-05-20 確定)。
本ファイル内の以下数値は v3 で更新済 (本ファイルは参照禁止・履歴のみ):
- メンテ時間帯 火/水/木 05-08 UTC → メンテなし (24/7・exchange_spec.md L37)
- Funding 8h 毎 0.01% → median +0.0002%/8h baseline / p95 0.01%/8h stress (audit#19)
- n_sim 上限 718/359/239/143/89/71 → 150/75/50/30/18/15 (maxPositionNum=150 反映)
- 最大レバ 125x → 150x (audit#19)
- maxPositionNum 200 → 150 (audit#19)
- 削除類型 11 種 → 10 種 (旧 #10 メンテ時間帯混入を削除)
- 28 ラベル独立 → 14 ラベル独立 (対称性活用・LONG×K=7×{MFE,MAE}・Phase 0 v3 §3.2 bit-exact 確認済)

---

# 【タスク】web_claude_self_check.md に「本番再現性 7 項目」「価格非依存性」を追記

## メタ情報

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-19 |
| 発行者 | Web Claude |
| 承認 | まこさん (2026-05-19 OK) |
| 関連必読 | web_claude_self_check.md / exchange_spec.md / false_positive_incident_policy.md §0-1 / §2 類型 H |
| 適用対象 | Web Claude (本書) |

## 保存・commit 指示 (memory ルール 19・必須)

本指示書を以下のパスに保存し commit する:

```
.claude/instructions/2026-05-19_web_claude_self_check_addendum.md
```

完了報告:

```
.claude/instructions/2026-05-19_web_claude_self_check_addendum_completion.md
```

---

## 背景

2026-05-19 セッションで Web Claude (旧) が以下 2 件の構造的見落としを発生させた:

| # | 見落とし | 発見契機 |
|---|---|---|
| 1 | ML 設計提案 v1/v2 で本番再現性 7 項目 (exchange_spec.md) を verify せずに MAX_ADDS / cap / per-position サイズを並べた | まこさん指摘 (「最小単位とか把握できてる?」) |
| 2 | ML 設計提案 v2 でラベル MFE/MAE が USD 絶対値のまま / PROFIT_LOCK_USD 残存・価格非依存性を verify せずに進めた | まこさん指摘 (「500BTC で Entry して 530BTC で Exit するとかしてないよね?」) |

両件とも「知識として正本に書いてある (exchange_spec.md / Phase 4-a normalize_reselect)」のに **Web Claude が設計時に起動できなかった**。これは false_positive §2 類型 G/H 近接。

web_claude_self_check.md は既存だが、これら 2 項目を **チェック A (CC に指示書を出す前)** に明示的に組み込まないと、再発が物理的に止まらない。

---

## 追記内容

### 追記場所 1: チェック A (CC に指示書を出す前)

既存の「チェック A」セクション末尾に以下を追加:

```markdown
- [ ] **本番再現性 7 項目 verify (exchange_spec.md・memory ルール 23 対応・2026-05-19 追加)**: 設計提案・指示書発行前に以下 7 項目を 1 行ずつ verify した内容をチャットに提示したか:
  1. 最小注文サイズ 0.0001 BTC (per-position サイズが BTC 単位で 0.0001 以上か算術 verify・組み合わせ MAX_ADDS × n_sim ごとに最悪値で verify)
  2. 最小注文額 5 USDT (BTC 価格依存・per-position × BTC 価格 ≥ 5 USDT・学習期間最低値 + 想定下落幅で stress test)
  3. Tick size 0.1 USDT (指値価格丸めロジック verify)
  4. Maker 指値 TTL 3 本 (15 分) + 同一 side pending 禁止 (add 速度制約・add トリガ条件が TTL 制約と矛盾しないか verify)
  5. SL 設定は add_count ≥ 2 のみ (MAX_ADDS=1 combo の Exit 設計は SL なしで time_exit / TP のみ運用)
  6. メンテ時間帯 火/水/木 05:00-08:00 UTC (発注スキップ実装 + バックテスト → 実運用差異モニタリング)
  7. Maker 剥落時 0.02% で stress test (Phase 5 NET 計算で Maker 0.014% (適用) と 0.02% (標準) の両方で月次 NET ≥ $1,900 全月クリアを verify)
  (2026-05-19: MAX_ADDS{1,2,3,5,8,10} を最小単位 0.0001 BTC verify なしに並べた事案。最小単位を割る組み合わせを検知できなかった。再発させない。)

- [ ] **価格非依存性 verify (2026-05-19 追加)**: ラベル定義・特徴量・Exit パラメータ・cluster 入力ベクトル・add トリガすべてが BTC 価格絶対値に依存しない (% / 比率 / 無次元 / BTC 単位) で表現されているか verify したか:
  1. **ラベル定義**: MFE/MAE を USD 絶対値ではなく pct ベース (MFE_pct = (MFE / close) × 100) で表現しているか。`LONG_MFE = max(high) - close` のような USD 絶対値定義のまま学習させていないか
  2. **Exit パラメータ**: TP_PCT / SL_PCT / TRAIL_RATIO / MFE_GATE_PCT / TIME_EXIT_MIN は % / 比率 / 分単位を使っているか。**PROFIT_LOCK_USD のような USD 絶対値は禁止** (PROFIT_LOCK_PCT に置換)
  3. **cluster 入力ベクトル**: 予測値を close で除算した pct 化を採用しているか (Phase 4-a normalize_reselect 既存対応の継承)
  4. **feature_importance 上位の USD 絶対値系**: dist_to_fib_v2_* / resistance_distance_* / support_distance_* / nearest_level_* は blacklist 済か
  5. **add トリガ**: 「価格逆行幅 X%」「含み益 Y%」が % 表現を維持しているか
  6. **TP_FEE_FLOOR**: 手数料分の TP 上乗せ計算が BTC 価格で動的化されているか
  (2026-05-19: ML 設計提案 v2 でラベル MFE/MAE が USD 絶対値・PROFIT_LOCK_USD 残存を見落とし。学習期間 BTC 価格 ($30k〜$100k) と本番価格 ($100k〜$150k 予定) の乖離で「学習時の典型 MFE 値が本番では発生しない」「USD 絶対値 Exit 閾値が相対的に変動」構造的問題。Phase 4-a 監査#5 懸念 2 で「BTC 価格変化で cluster 境界ドリフト」と既に認識されていたのにラベル自体の同問題に気づかなかった。再発させない。)
```

### 追記場所 2: 限界の自覚

既存の「限界の自覚」セクションに以下を追加:

```markdown
### 「知識として持っているのに起動されない」構造的問題 (2026-05-19 追加)

Web Claude は正本に書かれている内容を「知識として」持っていても、**設計時に起動できない** 構造的問題を持つ。今日のセッションで実証:

| # | 知識として持っていたもの | 設計時に起動できなかった理由 |
|---|---|---|
| 1 | exchange_spec.md の最小注文サイズ 0.0001 BTC | 「発注時の制約」と「学習時の表現」を無自覚に切り離した |
| 2 | Phase 4-a normalize_reselect で「BTC 価格変化で cluster ドリフト」認識済 | ラベル自体の同問題に思考が走らなかった |
| 3 | false_positive §2 類型 H (運用上限逸脱) | 既存知識として持っていたが、新設計で起動しなかった |
| 4 | web_claude_self_check.md「読了ゲート」 | 機械的証跡 (wc -l + 0/25/50/75/100% 引用) を出さず「読んだ」と書いた (類型 G) |

**ルール追加では効かない**。本書 (web_claude_self_check.md) が 2026-05-14 制定後、複数回の見落としを経験している実証あり。

**対応**:
- まこさん側に「読まない権利」を持たせる (検閲フロー)・チェック A・B・C の証跡が揃わなければ提案を読まずに差し戻し
- 監査経路を私と並走させる (audit#18 など独立評価)
- 私の構造的限界をまこさんと共有 (信用度のキャリブレーション)

これでも再発リスクはゼロにならない。すり抜けるたびに穴を塞ぐ (関所 G・有効性検証ループ)。
```

### 追記場所 3: 再発記録表 (新設または末尾追記)

既存「限界の自覚」セクションの末尾、または新セクションとして以下を追加:

```markdown
### Web Claude の見落とし再発記録 (このリストは消さない・追記のみ)

| # | 日付 | 内容 | 発見者 | 既存ルールでカバーされていたか |
|---|---|---|---|---|
| 1 | 2026-05-19 | ML 設計提案で本番再現性 7 項目 (exchange_spec.md) を verify せずに MAX_ADDS / cap を並べた | まこさん | exchange_spec.md は存在・読了ゲート対象だが起動されず |
| 2 | 2026-05-19 | ML 設計提案でラベル MFE/MAE が USD 絶対値・PROFIT_LOCK_USD 残存・価格非依存性を verify せず | まこさん | Phase 4-a normalize_reselect で既に知識として保有・起動されず |

**共通構造**: Web Claude は正本に書かれた知識を持っていても設計時に起動できない。チェックリスト追加だけでは効かない (本書 2026-05-14 制定後の複数回見落としが実証)。まこさんの検閲・監査経路・構造的限界の共有が併用必要。
```

---

## CC への作業指示

`.claude/rules/web_claude_self_check.md` を view し、以下を実施:

1. 「チェック A」セクション末尾に **追記場所 1** の 2 項目を追加
2. 「限界の自覚」セクション末尾に **追記場所 2** の章を追加
3. 「限界の自覚」セクション末尾 (追記場所 2 の後) に **追記場所 3** の再発記録表を追加
4. ファイル冒頭の更新日記載を「2026-05-14 監査#8 必須5 (構造改善)・2026-05-15 監査#12/#14 を受け... 2026-05-19 本番再現性 7 項目 + 価格非依存性 + 構造的見落とし記録 追加」と更新

## 完了確認

CC は完了報告に以下を含めること:
1. 追記前の web_claude_self_check.md 総行数 (wc -l)
2. 追記後の web_claude_self_check.md 総行数 (wc -l)
3. 追記された 3 箇所の行範囲 (例: L80-L105 / L130-L155 / L155-L170)
4. diff (追記前後の差分)
5. sha256 (追記前 / 追記後)

## 監査経路

本指示書は web_claude_self_check.md の改訂を含むため、本書 §6 改訂ルール「重大改訂は監査経路を通す」に該当。
ただし今回は「既存知識を起動する仕組みの追加」であり、本書の構造変更ではないため、まこさん最終確認のみで commit 可。
監査経路への送付はまこさん判断に委ねる。
