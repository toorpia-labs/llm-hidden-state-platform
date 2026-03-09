<h1 align="center">LLM Hidden State Extraction Platform</h1>

<p align="center">
  <b>LLMの「思考の軌跡」を可視化する</b><br>
  hidden stateベクトルの抽出からtoorPIAによる可視化まで
</p>

<br>

## このシステムは何をするのか？

大規模言語モデル（LLM）がテキストを生成するとき、モデル内部では各layerで**hidden stateベクトル**が計算されています。これはいわば、モデルが「次の単語を選ぶまでに考えていること」の数値的な表現です。

このプラットフォームは、**同じプロンプトに対して何度もLLMにテキストを生成させ、その都度hidden stateを記録する**ことで、モデルの内部状態の**ばらつき**（fluctuation）を観測可能にします。

```
                    ┌──────────────────────────────┐
                    │    同じプロンプトを N回入力     │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                 ┌────────────────────────────────────┐
                 │            LLM  (GPU)              │
                 │                                    │
                 │  Trial  1 ─▶ "レーザー出力は…"     │
                 │  Trial  2 ─▶ "最適化には…"         │
                 │  Trial  3 ─▶ "一般的に…"           │
                 │     :                              │
                 │  Trial 10 ─▶ "出力制御の…"         │
                 │                                    │
                 │  各Trialごとに                      │
                 │  hidden stateベクトルを記録          │
                 └──────────────┬─────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │                        │
                    │     segments.csv        │ ← 成果物
                    │  (N trials × M segs    │
                    │   × hidden_dim 次元)   │
                    │                        │
                    └────────────────────────┘
```

> **毎回同じプロンプトなのに、出力が微妙に異なる。**
> その「揺らぎ」はhidden stateにどう現れるのか？ ── これがこの研究の核心的な問いです。

<br>

---

## データフロー全体像

操作は大きく **2つのフェーズ** に分かれます。

```
  Phase 1  Hidden State 抽出                Phase 2  可視化
  Web UI ─▶ GPUサーバー                     手元のPC ─▶ toorPIA
 ─────────────────────────────────────────────────────────────────

  ┌──────────┐                ┌──────────┐
  │          │   Tailscale    │          │
  │ Browser  │ ──── VPN ────▶ │   GPU    │
  │          │                │  Server  │
  │          │ ◀── download ─ │          │
  └─────┬────┘                └──────────┘
        │
        │  segments.csv を手元に保存
        │
        ▼
  ┌──────────┐                ┌──────────┐
  │ toorPIA  │                │ toorPIA  │
  │  client  │ ── API call ─▶ │  Cloud   │
  │ (Python) │                │          │
  │          │ ◀── 可視化 ─── │          │
  └─────┬────┘                └──────────┘
        │
        ▼
   shareUrl をブラウザで開き
   Map Inspector で対話的に探索
```

<br>

---

## Phase 1: Hidden Stateの抽出

### Step 1 ── モデルを選ぶ

Web UI (`http://<サーバーIP>:3000`) にアクセスし、使いたいモデルを選択してロードします。

| モデル | パラメータ | VRAM目安 | 用途 |
|:--|:--|:--|:--|
| **Qwen3-0.6B** | 0.6B | ~1.2GB | 動作確認・テスト |
| **Qwen3-4B** (4bit) | 4B | ~3GB | 実験用 |
| **Phi-3.5-mini** (4bit) | 3.8B | ~2.5GB | 実験用（別アーキテクチャとの比較） |

> モデルのロードに数十秒かかることがあります。ローディング画面が出たら待ちましょう。
> サーバーのGPU（RTX 3050, 8GB VRAM）の制約により、大規模モデルは利用できません。

### Step 2 ── プロンプトとパラメータを設定する

<table>
<tr>
<th colspan="3">生成パラメータ</th>
</tr>
<tr><th>パラメータ</th><th>意味</th><th>推奨値</th></tr>
<tr><td><code>prompt</code></td><td>LLMへの入力テキスト</td><td>研究対象のプロンプト</td></tr>
<tr><td><code>n_trials</code></td><td>同一プロンプトで何回生成するか</td><td>10〜50</td></tr>
<tr><td><code>temperature</code></td><td>出力のランダム性（高い＝多様）</td><td>0.7</td></tr>
<tr><td><code>max_new_tokens</code></td><td>1回の生成の最大トークン数</td><td>50〜200</td></tr>
<tr>
<th colspan="3">セグメンテーションパラメータ</th>
</tr>
<tr><td><code>layer</code></td><td>hidden stateを取得するlayer</td><td>-1（最終層）</td></tr>
<tr><td><code>n_segments</code></td><td>出力をいくつの区間に分割するか</td><td>10</td></tr>
<tr><td><code>overlap</code></td><td>区間の重なり率</td><td>0.5</td></tr>
<tr><td><code>window_func</code></td><td>窓関数の種類</td><td>hann</td></tr>
</table>

### Step 3 ── 実行してCSVをダウンロードする

「**Extract Hidden States**」ボタンを押すと、GPUサーバーで抽出が始まります。
進捗バーが `10/10 trials completed` になったら、**segments.csv** をダウンロードしてください。

<br>

---

## CSVの中身を理解する

ダウンロードした `segments.csv` は以下のような構造です:

```
trial_id  segment_index  segment_position  dim_0     dim_1     dim_2    ...  dim_N
────────  ─────────────  ────────────────  ────────  ────────  ────────      ────────
0         0              0.000              0.1234   -0.5678    0.9012   ...
0         1              0.111              0.2345   -0.6789    0.0123   ...
 :         :               :                 :         :         :
0         9              1.000              0.3456   -0.7890    0.1234   ...
1         0              0.000              0.4567   -0.8901    0.2345   ...
1         1              0.111              0.5678   -0.9012    0.3456   ...
 :         :               :                 :         :         :
```

各カラムの役割:

```
  ┌─────────────────────┐     ┌──────────────────────────────────┐
  │ メタ情報（3列）       │     │ hidden stateベクトル（N次元）      │
  │                     │     │                                  │
  │  trial_id           │     │  dim_0, dim_1, dim_2, ..., dim_N │
  │  segment_index      │     │                                  │
  │  segment_position   │     │  ← toorPIAに投入する部分          │
  │                     │     │                                  │
  │  ※ toorPIAでは      │     │                                  │
  │    drop_columns で  │     │                                  │
  │    除外する          │     │                                  │
  └─────────────────────┘     └──────────────────────────────────┘
```

### STFT風セグメンテーションとは？

LLMの生成トークン数は毎回異なります（例: Trial 1は47トークン、Trial 2は62トークン）。
そのままでは長さが揃わず、試行間の比較ができません。

信号処理のSTFT（短時間フーリエ変換）にヒントを得た**オーバーラップ窓方式**で、
可変長の系列を固定長（n_segments個）に正規化します。

```
  n_segments = 5,  overlap = 0.5,  window_func = hann

  Trial 1  (47 tokens)
  ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  ├──[win]──┤                                         窓幅は
       ├──[win]──┤                                    トークン列の
            ├──[win]──┤                               長さに応じて
                 ├──[win]──┤                          自動調整される
                      ├──[win]──┤
      ↓       ↓       ↓       ↓       ↓
    seg_0   seg_1   seg_2   seg_3   seg_4

  Trial 2  (62 tokens)
  ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  ├───[win]───┤
        ├───[win]───┤
              ├───[win]───┤
                    ├───[win]───┤
                          ├───[win]───┤
      ↓        ↓        ↓        ↓        ↓
    seg_0    seg_1    seg_2    seg_3    seg_4

  → どちらも 5セグメント × hidden_dim 次元 に正規化される
```

> 窓関数（hann等）で重み付き平均を取ることで、区間境界の不連続性を抑え、
> 滑らかなhidden state trajectoryを得ます。

<br>

---

## Phase 2: toorPIA API Clientによる可視化

### セットアップ（初回のみ）

```bash
pip install toorpia
export TOORPIA_API_KEY="your-api-key"
```

### 基本的な使い方 ── basemapの作成

toorPIA の可視化は、まず **basemap（基準マップ）** を作成するところから始まります。
`basemap_csvform()` にCSVファイルを渡し、`drop_columns` でメタ情報カラムを除外します。

```python
from toorpia import toorPIA

client = toorPIA()

result = client.basemap_csvform(
    "segments.csv",
    drop_columns=["trial_id", "segment_index", "segment_position"],
    label="Qwen3-4B / laser optimization / temp=0.7 / 20 trials",
    tag="hidden-state-analysis"
)

print(f"Map Number: {result['mapNo']}")
print(f"Coordinates: {result['xyData'].shape}")
print(f"View: {result['shareUrl']}")  # ← ブラウザで開く
```

実行すると、高次元のhidden stateベクトルがトーラス面上に射影されます。
**shareUrl** をブラウザで開くと **Map Inspector** で対話的に探索できます。

```
  segments.csv                        toorPIA Map Inspector
  200行 (20 trials x 10 seg)         トーラス面への射影
  ┌───────────────────────┐
  │ dim_0  dim_1 ... dim_N│           ┌────────────────────────────┐
  │  0.12  -0.56 ...  0.90│           │                            │
  │  0.23  -0.67 ...  0.01│    ──▶    │  ●·····●·····●  Trial 1   │
  │   :      :         :  │           │   ○····○····○   Trial 2   │
  │  0.56  -0.90 ...  0.34│           │    ◆···◆···◆    Trial 3   │
  │   :      :         :  │           │                            │
  └───────────────────────┘           │  軌跡が近い = 類似した思考  │
                                      │  軌跡が遠い = 異なる思考    │
                                      └────────────────────────────┘
```

### 条件間の比較 ── addplot による重ね描き

異なる条件（別のモデル、異なるtemperature等）で抽出したCSVを、
既存の basemap に重ねてプロットすることで、差異を視覚的に比較できます。

```python
# Step 1: Qwen3 のデータで basemap 作成
result_base = client.basemap_csvform(
    "segments_qwen3-4b.csv",
    drop_columns=["trial_id", "segment_index", "segment_position"],
    label="Qwen3-4B baseline",
    tag="model-comparison"
)
print(f"Basemap: {result_base['shareUrl']}")

# Step 2: 別アーキテクチャのデータを addplot で重ねる
result_add = client.addplot_csvform("segments_phi-3.5-mini.csv")

print(f"Status: {result_add['abnormalityStatus']}")    # normal / abnormal / unknown
print(f"Score:  {result_add['abnormalityScore']:.3f}")
print(f"View:   {result_add['shareUrl']}")
```

> `addplot_csvform()` は basemap と同じ `drop_columns` 設定を自動的に引き継ぐため、
> 再度指定する必要はありません。

### 解像度パラメータの調整

データの分布をより細かく分析したい場合、解像度パラメータを調整できます:

```python
result = client.basemap_csvform(
    "segments.csv",
    drop_columns=["trial_id", "segment_index", "segment_position"],
    label="High-res analysis",
    identna_resolution=200,         # メッシュ解像度（デフォルト100）
    identna_effective_radius=0.05   # 有効半径比率（デフォルト0.1 → より局所的に）
)
```

### マップの管理

```python
# 作成済みマップの一覧
maps = client.list_map()
for m in maps:
    print(f"Map #{m['mapNo']}: {m.get('label', '(no label)')}")

# エクスポート（バックアップや共有に）
client.export_map(client.mapNo, "./exported_map/")

# インポート
new_map_no = client.import_map("./exported_map/")
```

<br>

---

## 可視化で着目するポイント

Map Inspector をブラウザで開いたら、以下の観点で観察してください。

<table>
<tr><th width="40%">観察パターン</th><th width="60%">解釈</th></tr>
<tr>
  <td>全Trialの軌跡が <b>重なる</b></td>
  <td>モデルは高い確信度で応答している</td>
</tr>
<tr>
  <td>軌跡が <b>分散する</b></td>
  <td>内部状態にばらつきがある（不確実性が高い）</td>
</tr>
<tr>
  <td>特定の区間で <b>分岐する</b></td>
  <td>生成のある時点で「迷い」が生じている</td>
</tr>
<tr>
  <td>層ごとに <b>異なるパターン</b></td>
  <td>浅い層と深い層で情報処理の性格が異なる</td>
</tr>
<tr>
  <td>addplotが basemap から <b>大きく外れる</b></td>
  <td>モデルの挙動が条件によって質的に異なる</td>
</tr>
<tr>
  <td><code>abnormalityScore</code> が <b>高い</b></td>
  <td>addplotのデータが basemap の正常領域から逸脱している</td>
</tr>
</table>

<br>

---

## 典型的な実験フロー

```
Step 1    プロンプトを用意する
          例: 「金属3Dプリンティングにおけるレーザー出力の最適化について説明してください」
              │
Step 2    Web UI でモデルを選択・ロードする
              │
Step 3    プロンプトを入力し、n_trials=20, temperature=0.7 で実行する
              │
Step 4    segments.csv をダウンロードする
              │
Step 5    toorPIA で basemap を作成する
          ┌───────────────────────────────────────────────────────────┐
          │ result = client.basemap_csvform(                         │
          │     "segments.csv",                                      │
          │     drop_columns=["trial_id","segment_index",            │
          │                   "segment_position"],                   │
          │     label="実験条件の説明"                                 │
          │ )                                                        │
          └───────────────────────────────────────────────────────────┘
              │
Step 6    shareUrl をブラウザで開いて Map Inspector で観察する
              │
Step 7    条件を変えて比較する
              │
              ├─ a) 同じプロンプトで別のモデル（Qwen3 vs Phi-3.5）
              │     → 別モデルのCSVを addplot_csvform() で重ね描き
              │
              ├─ b) 同じモデルで temperature を変える（0.3 vs 1.0）
              │     → 低temperatureを basemap、高temperatureを addplot
              │
              ├─ c) 異なる layer（layer=0 vs layer=-1）
              │     → それぞれ別の basemap として作成し比較
              │
              └─ d) 得意/不得意な分野のプロンプトを比較
                    → 得意分野を basemap、不得意分野を addplot
```

<br>

---

## 完全なPythonスクリプト例

CSVダウンロード後のbasemap作成から条件比較（addplot）までを1つのスクリプトにまとめた例です。

```python
"""
hidden state可視化スクリプトの例
Web UIからダウンロードした2つのCSVを比較する
"""
from toorpia import toorPIA

client = toorPIA()  # TOORPIA_API_KEY 環境変数を使用

DROP_COLS = ["trial_id", "segment_index", "segment_position"]

# ── Step 1: 基準データの basemap を作成 ──────────────────────
print("=== Creating basemap ===")
result_base = client.basemap_csvform(
    "segments_qwen3-4b_temp07.csv",
    drop_columns=DROP_COLS,
    label="Qwen3-4B / laser optimization / temp=0.7",
    tag="hidden-state",
    identna_resolution=150
)
print(f"  Map #{result_base['mapNo']}")
print(f"  Points: {result_base['xyData'].shape[0]}")
print(f"  URL: {result_base['shareUrl']}")

# ── Step 2: 比較データを addplot ─────────────────────────────
print("\n=== Adding Phi-3.5-mini data ===")
result_add = client.addplot_csvform(
    "segments_phi-3.5-mini_temp07.csv"
)
print(f"  Addplot #{result_add['addPlotNo']}")
print(f"  Abnormality: {result_add['abnormalityStatus']}")
print(f"  Score: {result_add['abnormalityScore']:.3f}")
print(f"  URL: {result_add['shareUrl']}")

# ── Step 3: 結果をブラウザで確認 ─────────────────────────────
import webbrowser
webbrowser.open(result_add['shareUrl'])
```

<br>

---

## FAQ

<details>
<summary><b>segments.csv の dim が何百次元もあるけど大丈夫？</b></summary>
<br>
toorPIA は高次元データを扱うために設計されています。次元数が多くても問題なく可視化できます。
<br><br>
</details>

<details>
<summary><b>n_trials を増やすとどうなる？</b></summary>
<br>
試行数を増やすほど、hidden stateの分布がより正確に見えます。ただしGPU時間も比例して増えます。まずは10〜20で試してください。
<br><br>
</details>

<details>
<summary><b>temperature=0 にしたら毎回同じ出力になる？</b></summary>
<br>
ほぼ同じになりますが、浮動小数点の丸めによりhidden stateに微小な差が出ることがあります。これ自体が興味深い観察対象になりえます。
<br><br>
</details>

<details>
<summary><b>複数のlayerを同時に取得できる？</b></summary>
<br>
UIのlayer設定で「全層」を選択すると可能です。ただしメモリ消費が大きくなるため、まずは最終層（layer=-1）から始めてください。
<br><br>
</details>

<details>
<summary><b>basemap と addplot の使い分けは？</b></summary>
<br>
basemap は「基準となるデータパターン」を構築するもの。addplot は「基準に対して新しいデータがどう異なるか」を調べるもの。実験では、まずコントロール条件を basemap にし、変化させた条件を addplot で重ねるのが基本です。
<br><br>
</details>

<details>
<summary><b><code>addplot_csvform()</code> で <code>drop_columns</code> を指定しなくていいの？</b></summary>
<br>
はい。<code>addplot_csvform()</code> は basemap 作成時の設定を自動的に引き継ぎます。再度指定する必要はありません。
<br><br>
</details>

<details>
<summary><b><code>abnormalityScore</code> の値はどう読む？</b></summary>
<br>
スコアが高いほど、addplot のデータが basemap の正常領域から逸脱しています。モデル間の比較では、「逸脱度が高い＝内部表現が質的に異なる」と解釈できます。
<br><br>
</details>

<br>

---

<p align="center">
  <a href="https://github.com/toorpia/toorpia">toorPIA API Client</a>&ensp;|&ensp;<a href="https://github.com/toorpia/toorpia/blob/main/docs/api-reference.md">API Reference</a>&ensp;|&ensp;<a href="https://github.com/toorpia-labs">toorpia-labs</a>
</p>
