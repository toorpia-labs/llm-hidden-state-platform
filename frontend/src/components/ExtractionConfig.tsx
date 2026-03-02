"use client";

export type ExtractionParams = {
  n_trials: number;
  temperature: number;
  max_new_tokens: number;
  layer: number;
  n_segments: number;
  overlap: number;
  window_func: string;
};

type Props = {
  params: ExtractionParams;
  onChange: (params: ExtractionParams) => void;
  disabled: boolean;
};

export default function ExtractionConfig({ params, onChange, disabled }: Props) {
  const update = (key: keyof ExtractionParams, value: number | string) => {
    onChange({ ...params, [key]: value });
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">パラメータ設定</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* n_trials */}
        <div>
          <label className="block text-xs font-medium mb-1">
            試行回数 (n_trials): {params.n_trials}
          </label>
          <input
            type="range"
            min={1}
            max={100}
            value={params.n_trials}
            onChange={(e) => update("n_trials", Number(e.target.value))}
            disabled={disabled}
            className="w-full"
          />
        </div>

        {/* temperature */}
        <div>
          <label className="block text-xs font-medium mb-1">
            Temperature: {params.temperature.toFixed(2)}
          </label>
          <input
            type="range"
            min={0}
            max={200}
            value={params.temperature * 100}
            onChange={(e) => update("temperature", Number(e.target.value) / 100)}
            disabled={disabled}
            className="w-full"
          />
        </div>

        {/* max_new_tokens */}
        <div>
          <label className="block text-xs font-medium mb-1">
            最大トークン数: {params.max_new_tokens}
          </label>
          <input
            type="number"
            min={10}
            max={500}
            value={params.max_new_tokens}
            onChange={(e) => update("max_new_tokens", Number(e.target.value))}
            disabled={disabled}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
          />
        </div>

        {/* layer */}
        <div>
          <label className="block text-xs font-medium mb-1">Layer</label>
          <select
            value={params.layer}
            onChange={(e) => update("layer", Number(e.target.value))}
            disabled={disabled}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value={-1}>最終層</option>
            <option value={0}>第0層（埋め込み層）</option>
            <option value={1}>第1層</option>
            <option value={-2}>最終から2番目</option>
          </select>
        </div>

        {/* n_segments */}
        <div>
          <label className="block text-xs font-medium mb-1">
            セグメント数: {params.n_segments}
          </label>
          <input
            type="range"
            min={5}
            max={50}
            value={params.n_segments}
            onChange={(e) => update("n_segments", Number(e.target.value))}
            disabled={disabled}
            className="w-full"
          />
        </div>

        {/* overlap */}
        <div>
          <label className="block text-xs font-medium mb-1">
            オーバーラップ: {params.overlap.toFixed(2)}
          </label>
          <input
            type="range"
            min={0}
            max={90}
            value={params.overlap * 100}
            onChange={(e) => update("overlap", Number(e.target.value) / 100)}
            disabled={disabled}
            className="w-full"
          />
        </div>

        {/* window_func */}
        <div>
          <label className="block text-xs font-medium mb-1">窓関数</label>
          <select
            value={params.window_func}
            onChange={(e) => update("window_func", e.target.value)}
            disabled={disabled}
            className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
          >
            <option value="hann">Hann</option>
            <option value="hamming">Hamming</option>
            <option value="rect">Rectangular</option>
          </select>
        </div>
      </div>
    </div>
  );
}
