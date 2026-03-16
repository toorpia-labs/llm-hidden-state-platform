"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import ModelSelector from "@/components/ModelSelector";
import PromptForm from "@/components/PromptForm";
import ExtractionConfig, {
  type ExtractionParams,
} from "@/components/ExtractionConfig";
import JobStatus from "@/components/JobStatus";
import ResultDownload from "@/components/ResultDownload";
import GenerationLog from "@/components/GenerationLog";

const DEFAULT_PARAMS: ExtractionParams = {
  n_trials: 10,
  temperature: 0.7,
  max_new_tokens: 100,
  layer: -1,
  n_segments: 10,
  overlap: 0.5,
  window_func: "hann",
};

export default function Home() {
  const [modelLoaded, setModelLoaded] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [params, setParams] = useState<ExtractionParams>(DEFAULT_PARAMS);
  const [running, setRunning] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("");
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const [generations, setGenerations] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const pollJob = useCallback(
    (id: string) => {
      const startedAt = Date.now();
      const MAX_POLL_MS = 10 * 60 * 1000; // 10分でタイムアウト
      let networkErrorCount = 0;

      pollingRef.current = setInterval(async () => {
        if (Date.now() - startedAt > MAX_POLL_MS) {
          stopPolling();
          setRunning(false);
          setError("タイムアウト: 処理が10分以上かかっています。バックエンドのログを確認してください。");
          return;
        }

        try {
          const res = await fetch(`/api/results/${id}`);
          const data = await res.json();
          networkErrorCount = 0;

          setJobStatus(data.status);
          if (data.progress) {
            setProgress(data.progress);
          }

          if (data.status === "completed") {
            stopPolling();
            setRunning(false);
            setMetadata(data.metadata || null);
            setGenerations(data.generations || []);
          } else if (data.status === "failed") {
            stopPolling();
            setRunning(false);
            setError(`抽出に失敗しました: ${data.error || "不明なエラー"}`);
          }
        } catch {
          networkErrorCount++;
          if (networkErrorCount >= 5) {
            stopPolling();
            setRunning(false);
            setError("バックエンドに接続できません。サーバーの状態を確認してください。");
          }
        }
      }, 2000);
    },
    [stopPolling]
  );

  const handleExtract = async () => {
    if (!prompt.trim()) {
      setError("プロンプトを入力してください");
      return;
    }

    setRunning(true);
    setError(null);
    setJobId(null);
    setJobStatus("");
    setProgress({ completed: 0, total: params.n_trials });
    setMetadata(null);
    setGenerations([]);

    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, ...params }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "抽出の開始に失敗しました");
        setRunning(false);
        return;
      }

      setJobId(data.job_id);
      setJobStatus("running");
      pollJob(data.job_id);
    } catch {
      setError("抽出の開始に失敗しました");
      setRunning(false);
    }
  };

  return (
    <main className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold">LLM Hidden State Extraction</h1>

      <ModelSelector onModelLoaded={() => setModelLoaded(true)} />

      <PromptForm value={prompt} onChange={setPrompt} disabled={running} />

      <ExtractionConfig
        params={params}
        onChange={setParams}
        disabled={running}
      />

      {error && (
        <p className="text-sm text-red-600 bg-red-50 p-3 rounded">{error}</p>
      )}

      <button
        onClick={handleExtract}
        disabled={!modelLoaded || running || !prompt.trim()}
        className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {running ? "実行中..." : "Extract Hidden States"}
      </button>

      {jobStatus && (
        <JobStatus
          status={jobStatus}
          completed={progress.completed}
          total={progress.total}
        />
      )}

      {jobId && jobStatus === "completed" && (
        <>
          <ResultDownload
            jobId={jobId}
            metadata={metadata as Parameters<typeof ResultDownload>[0]["metadata"]}
          />
          <GenerationLog generations={generations} />
        </>
      )}
    </main>
  );
}
