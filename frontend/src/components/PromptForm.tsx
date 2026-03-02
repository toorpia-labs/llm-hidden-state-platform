"use client";

type Props = {
  value: string;
  onChange: (value: string) => void;
  disabled: boolean;
};

export default function PromptForm({ value, onChange, disabled }: Props) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium">プロンプト</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="プロンプトを入力してください..."
        rows={5}
        className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
      />
    </div>
  );
}
