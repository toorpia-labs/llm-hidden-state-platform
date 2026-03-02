"use client";

type Props = {
  status: string;
  completed: number;
  total: number;
};

export default function JobStatus({ status, completed, total }: Props) {
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium">
          {status === "running"
            ? "実行中..."
            : status === "completed"
            ? "完了"
            : status === "failed"
            ? "失敗"
            : "待機中"}
        </span>
        <span className="text-gray-500">
          {completed} / {total} 試行
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all duration-300 ${
            status === "completed"
              ? "bg-green-500"
              : status === "failed"
              ? "bg-red-500"
              : "bg-blue-500"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
