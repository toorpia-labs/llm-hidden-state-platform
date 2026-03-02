"use client";

type Props = {
  jobId: string;
  metadata: {
    model_id?: string;
    n_trials?: number;
    temperature?: number;
    max_new_tokens?: number;
    trials?: Array<{ num_generated_tokens?: number; hidden_dim?: number }>;
  } | null;
};

export default function ResultDownload({ jobId, metadata }: Props) {
  const downloadUrl = (filename: string) =>
    `/api/results/${jobId}/download/${filename}`;

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">結果ダウンロード</h2>

      <div className="flex flex-wrap gap-3">
        <a
          href={downloadUrl("segments.csv")}
          className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-lg font-medium text-sm hover:bg-green-700"
        >
          segments.csv
        </a>
        <a
          href={downloadUrl("metadata.json")}
          className="inline-flex items-center px-3 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700"
        >
          metadata.json
        </a>
        <a
          href={downloadUrl("generations.txt")}
          className="inline-flex items-center px-3 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700"
        >
          generations.txt
        </a>
      </div>

      {metadata && (
        <div className="bg-gray-50 rounded-lg p-3 text-xs space-y-1">
          <p>
            <span className="font-medium">モデル:</span> {metadata.model_id}
          </p>
          <p>
            <span className="font-medium">試行数:</span> {metadata.n_trials}
          </p>
          <p>
            <span className="font-medium">Temperature:</span>{" "}
            {metadata.temperature}
          </p>
          {metadata.trials && metadata.trials[0] && (
            <>
              <p>
                <span className="font-medium">Hidden dim:</span>{" "}
                {metadata.trials[0].hidden_dim}
              </p>
              <p>
                <span className="font-medium">生成トークン数 (Trial 0):</span>{" "}
                {metadata.trials[0].num_generated_tokens}
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
