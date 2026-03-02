# CLAUDE.md — LLM Hidden State Extraction Platform

## プロジェクト概要

LLMに対してプロンプトを与え、複数回の試行で生成テキストと内部hidden stateベクトルを抽出するWebプラットフォーム。
Linux GPUサーバー上に構築し、Tailscale VPN経由で学生（梅崎さん）がブラウザからアクセスできるようにする。
**学生にはサーバーへのSSHアクセスを与えない。すべてWeb UI + API経由で操作する。**

### 入出力の定義

**入力**:
- モデル名（サーバーに登録済みのモデルから選択）
- プロンプト
- 試行回数
- 生成パラメータ（temperature, max_new_tokens）
- セグメンテーションパラメータ（n_segments, overlap, window_func, layer）

**出力**（試行回数分）:
- 各試行の生成テキスト
- hidden stateベクトル（CSV形式） — toorPIA API clientに直接投入可能な形式

ユーザは出力されたCSVを手元でtoorPIA API client (https://github.com/toorpia/toorpia) に投げることで可視化結果を得る。可視化はサーバー側の責務ではない。

## リポジトリ

- **GitHub Organization**: [toorpia-labs](https://github.com/toorpia-labs)
- **リポジトリ名**: `llm-hidden-state-platform`
- **URL**: `https://github.com/toorpia-labs/llm-hidden-state-platform`
- **可視性**: Private（梅崎さんをCollaboratorとして招待）

### Git運用ルール

- **ブランチ戦略**: `main` は安定版。開発は `feature/*` ブランチで行い、PRでマージする。
- **機密情報の管理**: `.env`, APIキー, モデルキャッシュは `.gitignore` に含める。絶対にcommitしない。
- **`models.yaml` はリポジトリに含める**: デフォルトのモデル定義をバージョン管理する。サーバー固有のカスタマイズが必要な場合は `models.local.yaml` を `.gitignore` に追加して対応。
- **`data/` ディレクトリはリポジトリに含めない**: 実験結果はサーバーローカルに保存。

### コラボレーションモデル

梅崎さんはサーバーにSSHできないが、GitHubリポジトリへのアクセスは可能:
- コードの閲覧・理解はGitHub上で行う
- フロントエンドやドキュメントの改善提案はPRで受け付ける
- サーバー側のデプロイ（`git pull` + `systemctl restart`）は管理者（YT）が行う

## アーキテクチャ

```
[梅崎さんのPC (browser)] ──Tailscale VPN──▶ [Linux GPU Server]

Linux GPU Server 内部構成:

  Next.js (:3000)  ──HTTP──▶  FastAPI (:8000)  ──GPU──▶ transformers
      Web UI + APIプロキシ         モデル常駐 + hidden state抽出
                                        │
                                                                          ▼
                                                                                                    data/jobs/{job_id}/
                                                                                                                                ├── segments.csv      ← ダウンロード可能
                                                                                                                                                            ├── metadata.json
                                                                                                                                                                                        └── generations.txt

                                                                                                                                                                                        梅崎さんの手元:
                                                                                                                                                                                          ダウンロードしたCSV → toorPIA API client → 可視化結果
                                                                                                                                                                                          ```

## ディレクトリ構成

```
llm-hidden-state-platform/
├── CLAUDE.md                    # この指示書（Claude Code用）
├── README.md                    # プロジェクト説明（梅崎さん向け利用ガイド）
├── .gitignore
├── .env.example                 # 環境変数テンプレート（.envはgit管理外）
│
├── backend/                     # FastAPI (Python) — GPU推論 + hidden state抽出
│   ├── requirements.txt
│   ├── models.yaml              # 利用可能モデル定義（管理者が編集）
│   ├── app/
│   │   ├── main.py              # FastAPIアプリケーション
│   │   ├── config.py            # 設定管理
│   │   ├── models/
│   │   │   └── llm_worker.py    # モデルレジストリ + 常駐 + hidden state抽出ロジック
│   │   ├── services/
│   │   │   ├── extraction.py    # STFTセグメンテーション処理
│   │   │   └── job_manager.py   # 非同期ジョブ管理
│   │   ├── routes/
│   │   │   ├── models.py        # GET /models, POST /models/load
│   │   │   ├── extract.py       # POST /extract
│   │   │   └── results.py       # GET /results/{job_id}, GET /results/{job_id}/download
│   │   └── schemas/
│   │       └── requests.py      # Pydantic リクエスト/レスポンスモデル
│   └── tests/
│
├── frontend/                    # Next.js — Web UI + APIプロキシ
│   ├── package.json
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         # メインページ（モデル選択 + プロンプト入力 + 結果表示）
│   │   │   ├── layout.tsx
│   │   │   └── api/             # APIプロキシルート (Next.js Route Handlers)
│   │   │       ├── models/route.ts
│   │   │       ├── extract/route.ts
│   │   │       └── results/[id]/route.ts
│   │   └── components/
│   │       ├── ModelSelector.tsx       # モデル選択 + ロード/アンロード
│   │       ├── PromptForm.tsx         # プロンプト入力フォーム
│   │       ├── ExtractionConfig.tsx   # パラメータ設定UI
│   │       ├── JobStatus.tsx          # ジョブ進捗表示
│   │       ├── ResultDownload.tsx     # CSVダウンロード + メタデータ表示
│   │       └── GenerationLog.tsx      # 生成テキスト一覧
│   └── tailwind.config.ts
│
├── data/                        # 実行結果の永続化ディレクトリ（git管理外）
│   └── jobs/                    # ジョブごとのサブディレクトリ
│       └── {job_id}/
│           ├── segments.csv     # hidden stateベクトル（toorPIA投入可能形式）
│           ├── metadata.json    # 実験条件・統計情報
│           └── generations.txt  # 各試行の生成テキスト
│
├── deploy/                      # デプロイ関連
│   ├── llm-platform-backend.service    # systemd unit file
│   ├── llm-platform-frontend.service   # systemd unit file
│   └── setup.sh                        # 初回セットアップスクリプト
│
└── scripts/
    └── setup_tailscale.sh       # Tailscale初期設定ヘルパー
    ```

### .gitignore

以下を含めること:

```gitignore
# Environment & secrets
.env
*.local.yaml

# Data & results (server-local only)
data/

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node
node_modules/
.next/

# Model cache (huge)
*.gguf
*.safetensors

# OS
.DS_Store
```

### .env.example

```bash
# Backend
CUDA_VISIBLE_DEVICES=0
HF_HOME=/home/<YOUR_USER>/.cache/huggingface

# Frontend
BACKEND_URL=http://127.0.0.1:8000
```

### README.md

梅崎さん向けの利用ガイドとして以下を含めること:

1. プロジェクトの目的（LLMのhidden state抽出プラットフォーム）の簡潔な説明
2. Tailscaleのセットアップ手順（招待リンクからの参加方法）
3. Web UIへのアクセス方法（`http://<tailscale-ip>:3000`）
4. 基本的な使い方（モデル選択 → プロンプト入力 → 実行 → CSVダウンロード）
5. パラメータの説明（n_trials, temperature, layer, n_segments, overlap, window_func）
6. 出力CSVの形式説明（カラム構成: trial_id, segment_index, segment_position, dim_0, dim_1, ...）
7. toorPIA API clientでの可視化方法の簡単な案内（詳細は https://github.com/toorpia/toorpia を参照）

※ サーバー構築手順やsystemd操作はREADMEに含めない（管理者向け情報はCLAUDE.mdに集約）

### リポジトリ初期セットアップ

Claude Codeはプロジェクトの初回構築時に以下を実行すること:

```bash
git init
git remote add origin git@github.com:toorpia-labs/llm-hidden-state-platform.git
# 初回コミットはディレクトリ構成 + .gitignore + CLAUDE.md + README.md
git add -A
git commit -m "Initial project structure"
git branch -M main
git push -u origin main
```

以降、各Phaseの実装完了時にコミット + pushする。コミットメッセージは以下の形式:

```
feat: Phase 1 - FastAPI backend with hidden state extraction
feat: Phase 1 - Next.js frontend with prompt UI and CSV download
feat: Phase 2 - model switching and 4bit quantization support
fix: ...
docs: ...
```

## 技術スタック

### Backend (FastAPI + Python)

- **Python 3.11+**
- **FastAPI** — 非同期APIサーバー
- **transformers** — HuggingFace モデルロード + `output_hidden_states=True` による全layer hidden state取得
- **torch (CUDA)** — GPU推論
- **bitsandbytes** — 4bit量子化（大規模モデル用）
- **scipy** — 窓関数（STFT風セグメンテーション）
- **numpy, pandas** — データ処理
- **uvicorn** — ASGIサーバー

### Frontend (Next.js)

- **Next.js 14+ (App Router)**
- **TypeScript**
- **Tailwind CSS**
- **React** — UI

### インフラ

- **systemd** — バックエンド・フロントエンドをサービスとして自動起動・管理
- **Tailscale** — VPNによるアクセス制御（SSHなしでブラウザアクセスのみ）
- **Python venv** — バックエンドの依存管理
- **nvm / Node.js** — フロントエンドの実行環境

## 実装の詳細仕様

### 1. Backend: FastAPI (`backend/`)

#### モデルレジストリ + 動的切り替え (llm_worker.py)

- サーバー管理者（YT）が `models.yaml` に利用可能なモデルを定義する
- 梅崎さんはWeb UIから利用可能モデル一覧を取得し、選択してロードできる
- モデルのロード/アンロードはAPI経由で行う（SSH不要）
- 同時に1モデルのみGPUに常駐（VRAM制約）。切り替え時は現モデルをアンロードしてから新モデルをロード

```yaml
# backend/models.yaml — サーバー管理者が編集する設定ファイル
# 利用可能なモデルを定義。ここにないモデルはAPI経由でロードできない。

models:
  - id: "qwen3-0.6b"
      name: "Qwen3-0.6B（開発・テスト用）"
          hf_repo: "Qwen/Qwen3-0.6B"
              quantize: false
                  torch_dtype: "float16"
                      description: "軽量モデル。パイプライン検証用。"

                        - id: "qwen3-4b"
                            name: "Qwen3-4B"
                                hf_repo: "Qwen/Qwen3-4B"
                                    quantize: false
                                        torch_dtype: "float16"
                                            description: "中規模モデル。"

                                              - id: "qwen3-30b-a3b"
                                                  name: "Qwen3-30B-A3B（MoE, 4bit量子化）"
                                                      hf_repo: "Qwen/Qwen3-30B-A3B"
                                                          quantize: true           # bitsandbytes 4bit
                                                              torch_dtype: "float16"
                                                                  description: "本番用。Active 3Bパラメータ、MoEアーキテクチャ。"

                                                                    - id: "qwen3-8b"
                                                                        name: "Qwen3-8B"
                                                                            hf_repo: "Qwen/Qwen3-8B"
                                                                                quantize: false
                                                                                    torch_dtype: "float16"
                                                                                        description: "Dense 8Bモデル。MoEとの比較実験用。"

# 追加時はこのファイルにエントリを追加するだけでUIに反映される
```

```python
# llm_worker.py の概念

class LLMWorker:
    def __init__(self, models_config_path: str = "models.yaml"):
            self.model = None
                    self.tokenizer = None
                            self.current_model_id = None
                                    self.lock = asyncio.Lock()
                                            self.registry = self._load_registry(models_config_path)

                                                def _load_registry(self, path) -> dict:
                                                        """models.yaml を読み込み、id -> 設定 の辞書を返す"""
                                                                ...

                                                                    def list_available_models(self) -> list:
                                                                            """利用可能なモデル一覧を返す（UI表示用）"""
                                                                                    return [
                                                                                                {
                                                                                                                    "id": m["id"],
                                                                                                                                    "name": m["name"],
                                                                                                                                                    "description": m["description"],
                                                                                                                                                                    "is_loaded": m["id"] == self.current_model_id
                                                                                                                                                                                }
                                                                                                                                                                                            for m in self.registry.values()
                                                                                                                                                                                                        ]

                                                                                                                                                                                                            async def load_model(self, model_id: str):
                                                                                                                                                                                                                    """
                                                                                                                                                                                                                            指定モデルをロード。既に別モデルがロード済みなら先にアンロードする。
                                                                                                                                                                                                                                    同一モデルが既にロード済みなら何もしない。
                                                                                                                                                                                                                                            """
                                                                                                                                                                                                                                                    async with self.lock:
                                                                                                                                                                                                                                                                if model_id == self.current_model_id:
                                                                                                                                                                                                                                                                                    return {"status": "already_loaded"}

                                                                                                                                                                                                                                                                                                if model_id not in self.registry:
                                                                                                                                                                                                                                                                                                                    raise ValueError(f"Unknown model: {model_id}")

                                                                                                                                                                                                                                                                                                                                # 現モデルをアンロード（VRAM解放）
                                                                                                                                                                                                                                                                                                                                            if self.model is not None:
                                                                                                                                                                                                                                                                                                                                                                del self.model
                                                                                                                                                                                                                                                                                                                                                                                del self.tokenizer
                                                                                                                                                                                                                                                                                                                                                                                                torch.cuda.empty_cache()
                                                                                                                                                                                                                                                                                                                                                                                                                gc.collect()

                                                                                                                                                                                                                                                                                                                                                                                                                            # 新モデルをロード
                                                                                                                                                                                                                                                                                                                                                                                                                                        config = self.registry[model_id]
                                                                                                                                                                                                                                                                                                                                                                                                                                                    self.tokenizer = AutoTokenizer.from_pretrained(
                                                                                                                                                                                                                                                                                                                                                                                                                                                                    config["hf_repo"], trust_remote_code=True
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                )
                                                                                                                                                                                                                                                                                                                                                                                                                                                                self.model = AutoModelForCausalLM.from_pretrained(
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                config["hf_repo"],
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                torch_dtype=getattr(torch, config["torch_dtype"]),
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                device_map="auto",
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                trust_remote_code=True,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                quantization_config=BitsAndBytesConfig(load_in_4bit=True)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    if config.get("quantize") else None
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    )
                                                                                                                                                                                                                                                                                                                                                                                                                                                                            self.model.eval()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        self.current_model_id = model_id
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    return {"status": "loaded", "model": model_id}

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        async def generate_with_hidden_states(self, prompt, n_trials, **kwargs):
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                """排他制御付きで推論実行。モデル未ロード時はエラー。"""
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        if self.model is None:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        raise RuntimeError("No model loaded. Call POST /models/load first.")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                async with self.lock:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            return self._run_extraction(prompt, n_trials, **kwargs)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            ```

#### hidden state抽出ロジック (extraction.py)

- 既存スクリプトの `extract_hidden_states_from_generation()` と `create_overlapping_segments()` をそのまま移植する
- 以下が既存の実装（再利用すること）:

```python
def extract_hidden_states_from_generation(outputs, input_length, layer_idx=-1):
    """
        outputs.hidden_states はタプルのタプル:
            hidden_states[token_idx][layer_idx] -> (batch, seq_len, hidden_dim)
                各生成ステップの最後のポジション（新規トークン）のhidden stateを取得
                    """
                        hidden_states_list = []
                            for token_idx in range(len(outputs.hidden_states)):
                                        step_hidden = outputs.hidden_states[token_idx]
                                                layer_hidden = step_hidden[layer_idx]
                                                        token_hidden = layer_hidden[0, -1, :].cpu().numpy()
                                                                hidden_states_list.append(token_hidden)
                                                                    return np.stack(hidden_states_list, axis=0)

                                                                    def create_overlapping_segments(hidden_states, n_segments, overlap=0.5, window_func="hann"):
                                                                        """
                                                                            STFT風オーバーラップ窓によるセグメンテーション
                                                                                hidden_states: (num_tokens, hidden_dim) -> segments: (n_segments, hidden_dim)
                                                                                    """
                                                                                        # 実装は既存スクリプト参照（そのまま使う）
                                                                                        ```

#### APIエンドポイント

**GET /models**
```json
// Response — 利用可能なモデル一覧
{
      "models": [
          {
                    "id": "qwen3-0.6b",
                          "name": "Qwen3-0.6B（開発・テスト用）",
                                "description": "軽量モデル。パイプライン検証用。",
                                      "is_loaded": false
                                          },
                                              {
                                                        "id": "qwen3-30b-a3b",
                                                              "name": "Qwen3-30B-A3B（MoE, 4bit量子化）",
                                                                    "description": "本番用。Active 3Bパラメータ、MoEアーキテクチャ。",
                                                                          "is_loaded": true
                                                                              }
                                                                                ],
                                                                                  "current_model": "qwen3-30b-a3b"
}
```

**POST /models/load**
```json
// Request
{
      "model_id": "qwen3-30b-a3b"
}

// Response
{
      "status": "loaded",
        "model_id": "qwen3-30b-a3b",
          "message": "Model loaded successfully (took 45.2s)"
}
```

**POST /extract**
```json
// Request — 現在ロード中のモデルで実行される
{
      "prompt": "金属3Dプリンティングにおけるレーザー出力の最適化について説明してください",
        "n_trials": 10,
          "temperature": 0.7,
            "max_new_tokens": 100,
              "layer": -1,
                "n_segments": 10,
                  "overlap": 0.5,
                    "window_func": "hann"
}

// Response
{
      "job_id": "uuid-xxxx",
        "status": "running",
          "model_id": "qwen3-30b-a3b",
            "message": "Extraction started with 10 trials using Qwen3-30B-A3B"
}

// Error: モデル未ロード → 400 Bad Request
{
      "error": "No model loaded. Use POST /models/load first."
}
```

**GET /results/{job_id}**
```json
// Response (進行中)
{
      "job_id": "uuid-xxxx",
        "status": "running",
          "progress": { "completed": 3, "total": 10 }
}

// Response (完了)
{
      "job_id": "uuid-xxxx",
        "status": "completed",
          "model_id": "qwen3-30b-a3b",
            "metadata": { /* metadata.json の内容 */ },
              "files": {
                      "segments_csv": "/results/uuid-xxxx/download/segments.csv",
                          "metadata_json": "/results/uuid-xxxx/download/metadata.json",
                              "generations_txt": "/results/uuid-xxxx/download/generations.txt"
                                },
                                  "generations": [ /* 各試行の生成テキスト（プレビュー用） */ ]
}
```

**GET /results/{job_id}/download/{filename}**
- `segments.csv`, `metadata.json`, `generations.txt` をファイルとしてダウンロード
- Content-Disposition: attachment ヘッダを付与

#### ジョブ管理 (job_manager.py)

- 各抽出タスクはバックグラウンドタスクとして非同期実行する
- ジョブ状態は `data/jobs/{job_id}/` ディレクトリ内の `status.json` で管理
- 状態遷移: `queued` → `running` → `completed` / `failed`
- 進捗（完了した試行数）をリアルタイムで更新する

#### 出力CSV形式 (segments.csv)

toorPIA API clientに直接投入可能な形式で出力する:

```csv
trial_id,segment_index,segment_position,dim_0,dim_1,dim_2,...,dim_N
0,0,0.0,0.1234,-0.5678,0.9012,...
0,1,0.111,0.2345,-0.6789,0.0123,...
...
0,9,1.0,0.3456,-0.7890,0.1234,...
1,0,0.0,0.4567,-0.8901,0.2345,...
...
```

- 各行は1つのセグメント（1試行内の1時点）
- `trial_id`: 試行番号（0始まり）
- `segment_index`: セグメント番号（0始まり）
- `segment_position`: 正規化位置（0.0〜1.0）
- `dim_0` 〜 `dim_N`: hidden stateベクトルの各次元

### 2. Frontend: Next.js (`frontend/`)

#### メインページ (`page.tsx`)

以下の要素を1画面に配置する:

1. **モデル選択パネル** — 利用可能モデル一覧 + ロード/アンロードボタン + 現在のモデル状態表示
2. **プロンプト入力エリア** — テキストエリア + パラメータ設定パネル
3. **実行ボタン** — 「Extract Hidden States」（モデル未ロード時はdisabled）
4. **ジョブステータス** — プログレスバー + 完了試行数/全試行数
5. **結果表示エリア**:
   - CSVダウンロードボタン（segments.csv, metadata.json, generations.txt）
      - メタデータ表示（使用モデル、トークン統計、セグメンテーション設定）
         - 生成テキスト一覧（各試行のテキストをアコーディオン表示）

#### モデル選択UI (`ModelSelector.tsx`)

- ページロード時に `GET /api/models` を呼び、利用可能モデル一覧を表示する
- 各モデルはカード形式で表示: モデル名、説明、ロード状態（ロード済み/未ロード）
- 「ロード」ボタン押下で `POST /api/models/load` を呼び、ローディング表示する
- モデルロードには数十秒かかるため、ローディング中は他の操作をブロックするか、明確に「ロード中」と表示する
- 現在ロード中のモデルはハイライト表示し、その名前をページ上部に常時表示する

#### 結果ダウンロードUI (`ResultDownload.tsx`)

- ジョブ完了後に表示される
- 3つのファイルのダウンロードボタン:
  - **segments.csv** — hidden stateベクトル（メインの成果物、目立つボタンにする）
    - **metadata.json** — 実験条件・統計
      - **generations.txt** — 全試行の生成テキスト
      - メタデータの要約表示（使用モデル、試行数、トークン統計）

#### APIプロキシ (`app/api/`)

- Next.js Route Handlers でバックエンドAPIへのプロキシを実装
- フロントエンドからは `/api/models`, `/api/extract` 等にリクエストし、バックエンドの `http://127.0.0.1:8000/` に転送
- これにより、フロントエンドとバックエンドを同一オリジンに見せ、CORSの問題を回避

プロキシするエンドポイント:
- `GET  /api/models`                       → `GET  http://127.0.0.1:8000/models`
- `POST /api/models/load`                  → `POST http://127.0.0.1:8000/models/load`
- `POST /api/extract`                      → `POST http://127.0.0.1:8000/extract`
- `GET  /api/results/{id}`                 → `GET  http://127.0.0.1:8000/results/{id}`
- `GET  /api/results/{id}/download/{file}` → `GET  http://127.0.0.1:8000/results/{id}/download/{file}`

#### パラメータ設定UI (`ExtractionConfig.tsx`)

以下のパラメータをUIで設定可能にする:
- `n_trials` (試行数): スライダー 1-100, デフォルト10
- `temperature`: スライダー 0.0-2.0, デフォルト0.7
- `max_new_tokens`: 入力 10-500, デフォルト100
- `layer`: ドロップダウン（「最終層」「全層」「指定層」）
- `n_segments`: スライダー 5-50, デフォルト10
- `overlap`: スライダー 0.0-0.9, デフォルト0.5
- `window_func`: ドロップダウン (rect / hann / hamming)

### 3. デプロイ構成 (`deploy/`)

#### 初回セットアップ (`deploy/setup.sh`)

```bash
#!/bin/bash
set -e

PROJECT_DIR="/opt/llm-hidden-state-platform"
VENV_DIR="$PROJECT_DIR/backend/.venv"

echo "=== LLM Hidden State Platform Setup ==="

# System dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv nodejs npm

# Clone repository
sudo mkdir -p /opt
sudo chown $USER:$USER /opt
git clone git@github.com:toorpia-labs/llm-hidden-state-platform.git $PROJECT_DIR
cd $PROJECT_DIR

# Backend: Python venv + dependencies
python3.11 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

# Frontend: Node.js dependencies + build
cd $PROJECT_DIR/frontend
npm install
npm run build

# Data directory
mkdir -p $PROJECT_DIR/data/jobs

# Environment file
cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env
echo ">>> .env を編集して必要な設定を行ってください"

# Install systemd services
sudo cp $PROJECT_DIR/deploy/llm-platform-backend.service /etc/systemd/system/
sudo cp $PROJECT_DIR/deploy/llm-platform-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable llm-platform-backend llm-platform-frontend

echo "=== Setup complete ==="
echo "Start services: sudo systemctl start llm-platform-backend llm-platform-frontend"
```

#### systemd unit files

```ini
# deploy/llm-platform-backend.service
[Unit]
Description=LLM Hidden State Platform - Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=<YOUR_USER>
WorkingDirectory=/opt/llm-hidden-state-platform/backend
EnvironmentFile=/opt/llm-hidden-state-platform/.env
ExecStart=/opt/llm-hidden-state-platform/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=10

# GPU access
Environment=CUDA_VISIBLE_DEVICES=0

[Install]
WantedBy=multi-user.target
```

```ini
# deploy/llm-platform-frontend.service
[Unit]
Description=LLM Hidden State Platform - Frontend (Next.js)
After=llm-platform-backend.service

[Service]
Type=simple
User=<YOUR_USER>
WorkingDirectory=/opt/llm-hidden-state-platform/frontend
Environment=BACKEND_URL=http://127.0.0.1:8000
Environment=PORT=3000
ExecStart=/usr/bin/npm start
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

#### 日常の操作コマンド

```bash
# サービス起動/停止
sudo systemctl start llm-platform-backend llm-platform-frontend
sudo systemctl stop llm-platform-backend llm-platform-frontend

# ログ確認
journalctl -u llm-platform-backend -f
journalctl -u llm-platform-frontend -f

# コード更新 → 再デプロイ
cd /opt/llm-hidden-state-platform
git pull
source backend/.venv/bin/activate
pip install -r backend/requirements.txt   # 依存が変わった場合
cd frontend && npm install && npm run build  # フロント変更時
sudo systemctl restart llm-platform-backend llm-platform-frontend

# モデル追加（コード変更不要）
vi backend/models.yaml    # エントリ追加
sudo systemctl restart llm-platform-backend
```

### 4. Tailscale設定

- Linux GPUサーバーにTailscaleをインストール・起動する
- 梅崎さんのデバイスにもTailscaleをインストールし、同じtailnetに参加させる
- サーバーのTailscale IPの`:3000`でNext.js Web UIにアクセスできるようにする
- Tailscale ACLで、梅崎さんのデバイスからサーバーのポート3000のみ許可する設定を推奨

## セキュリティ考慮事項

- **SSHアクセスは一切与えない** — 梅崎さんはブラウザ経由のWeb UIのみ使用
- **Tailscale ACL** — ポート3000のみ許可（8000は外部公開しない）
- **入力バリデーション** — プロンプト長、試行数、トークン数に上限を設ける
- **リソース制限** — GPU排他制御（asyncio.Lock）により、同時実行によるOOMを防ぐ
- **API認証** — 最低限、シンプルなAPIキーまたはBasic認証をNext.jsレベルで実装する

## 実装の優先順位

### Phase 1: 最小動作版（MVP）
1. リポジトリ初期化（.gitignore, CLAUDE.md, README.md, ディレクトリ構成）→ `git push`
2. `backend/` — FastAPI + 小さいモデル（Qwen3-0.6B等）でhidden state抽出API + CSVダウンロードを実装
3. `frontend/` — Next.js でモデル選択 → プロンプト入力 → 実行 → CSVダウンロードのUI
4. バックエンド + フロントエンドを起動し、ローカルで動作確認 → `git push`

### Phase 2: 本番モデル + 運用
5. Qwen3-30B-A3B（4bit量子化）への切り替え
6. Tailscale設定 + 梅崎さんのアクセス確認
7. 認証、リソース制限、エラーハンドリングの強化 → `git push`

## 既存コードの再利用

添付の既存Pythonスクリプト（`extract_hidden_states.py`相当）の以下の関数はそのまま `backend/app/services/extraction.py` に移植すること:

- `create_overlapping_segments()` — STFT風セグメンテーション（変更不要）
- `compute_segment_metadata()` — メタデータ計算（変更不要）
- `extract_hidden_states_from_generation()` — hidden state取得（変更不要）
- `validate_output()` — 出力検証（変更不要）

変更が必要な部分:
- `run_extraction()` — CLIベースのフロー → FastAPIの非同期ジョブとして再構成
- モデルロード — 関数内ロード → `LLMWorker`クラスによる常駐化
- 出力先 — コマンドライン引数 → `data/jobs/{job_id}/` ディレクトリ

## 注意事項

- `output_hidden_states=True` + `return_dict_in_generate=True` は生成トークン数に比例してメモリを消費する。`max_new_tokens` の上限を適切に設定すること。
- MoEモデル（Qwen3-30B-A3B）では、expert routingの影響で同一プロンプトでもhidden stateの変動が大きい可能性がある。これは研究上むしろ有用な特性。
- モデル切り替え機能により、同一プロンプトに対するDense vs MoE、モデルサイズの違いによるhidden state変動の比較実験が容易になる。結果のmetadata.jsonには使用モデルIDが記録されるため、後から条件を追跡できる。
