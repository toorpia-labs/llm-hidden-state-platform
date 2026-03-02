"use client";

import { useState, useEffect, useCallback } from "react";

type ModelInfo = {
  id: string;
  name: string;
  description: string;
  is_loaded: boolean;
};

type Props = {
  onModelLoaded: (modelId: string) => void;
};

export default function ModelSelector({ onModelLoaded }: Props) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingModelId, setLoadingModelId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = useCallback(async () => {
    try {
      const res = await fetch("/api/models");
      const data = await res.json();
      setModels(data.models);
      setCurrentModel(data.current_model);
    } catch {
      setError("モデル一覧の取得に失敗しました");
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleLoad = async (modelId: string) => {
    setLoading(true);
    setLoadingModelId(modelId);
    setError(null);
    try {
      const res = await fetch("/api/models/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: modelId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "モデルのロードに失敗しました");
        return;
      }
      setCurrentModel(modelId);
      onModelLoaded(modelId);
      await fetchModels();
    } catch {
      setError("モデルのロードに失敗しました");
    } finally {
      setLoading(false);
      setLoadingModelId(null);
    }
  };

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">モデル選択</h2>
      {currentModel && (
        <p className="text-sm text-blue-600 font-medium">
          現在のモデル: {models.find((m) => m.id === currentModel)?.name || currentModel}
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {models.map((model) => (
          <div
            key={model.id}
            className={`border rounded-lg p-4 ${
              model.is_loaded
                ? "border-blue-500 bg-blue-50"
                : "border-gray-200 bg-white"
            }`}
          >
            <h3 className="font-medium text-sm">{model.name}</h3>
            <p className="text-xs text-gray-500 mt-1">{model.description}</p>
            <button
              onClick={() => handleLoad(model.id)}
              disabled={loading || model.is_loaded}
              className={`mt-3 px-3 py-1.5 text-xs rounded font-medium ${
                model.is_loaded
                  ? "bg-blue-100 text-blue-700 cursor-default"
                  : loading
                  ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                  : "bg-blue-600 text-white hover:bg-blue-700"
              }`}
            >
              {model.is_loaded
                ? "ロード済み"
                : loadingModelId === model.id
                ? "ロード中..."
                : "ロード"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
