# LLM Hidden State Extraction Platform

LLMの内部hidden stateベクトルを抽出するWebプラットフォームです。
プロンプトを入力し、複数回の試行で生成テキストとhidden stateを取得できます。
出力されたCSVはtoorPIA API clientで可視化できます。

## セットアップ（Tailscale）

1. 招待リンクからTailscaleに参加してください
2. Tailscaleアプリをインストール・起動してください
   - Windows: https://tailscale.com/download/windows
   - macOS: https://tailscale.com/download/macos
3. 同じtailnetに接続されていることを確認してください

## アクセス方法

ブラウザで以下のURLにアクセスしてください:

```
http://<tailscale-ip>:3000
```

（Tailscale IPは管理者から通知されます）

## 使い方

### 1. モデル選択
- ページ上部のモデル一覧から使用するモデルを選択し、「ロード」ボタンを押してください
- モデルのロードには数十秒かかります。ローディング表示が消えるまでお待ちください
- 同時に1つのモデルのみロード可能です。別のモデルに切り替えると、現在のモデルは自動的にアンロードされます

### 2. プロンプト入力
- テキストエリアにプロンプトを入力してください

### 3. パラメータ設定
- **n_trials** (試行回数): 同じプロンプトで何回生成を繰り返すか（デフォルト: 10）
- **temperature**: 生成のランダム性（デフォルト: 0.7、高いほどランダム）
- **max_new_tokens**: 生成する最大トークン数（デフォルト: 100）
- **layer**: hidden stateを取得するレイヤー（デフォルト: 最終層）
- **n_segments**: STFT風セグメンテーションの分割数（デフォルト: 10）
- **overlap**: セグメント間のオーバーラップ率（デフォルト: 0.5）
- **window_func**: 窓関数（rect / hann / hamming、デフォルト: hann）

### 4. 実行
- 「Extract Hidden States」ボタンを押してください
- 進捗バーで完了した試行数を確認できます

### 5. 結果ダウンロード
- 完了後、以下のファイルをダウンロードできます:
  - **segments.csv** — hidden stateベクトル（メインの成果物）
  - **metadata.json** — 実験条件・統計情報
  - **generations.txt** — 各試行の生成テキスト

## 出力CSV形式（segments.csv）

```csv
trial_id,segment_index,segment_position,dim_0,dim_1,dim_2,...,dim_N
0,0,0.0,0.1234,-0.5678,0.9012,...
0,1,0.111,0.2345,-0.6789,0.0123,...
...
```

| カラム | 説明 |
|--------|------|
| trial_id | 試行番号（0始まり） |
| segment_index | セグメント番号（0始まり） |
| segment_position | 正規化位置（0.0〜1.0） |
| dim_0 〜 dim_N | hidden stateベクトルの各次元 |

## toorPIAでの可視化

ダウンロードしたCSVをtoorPIA API clientに投入することで可視化できます。
詳細は https://github.com/toorpia/toorpia を参照してください。
