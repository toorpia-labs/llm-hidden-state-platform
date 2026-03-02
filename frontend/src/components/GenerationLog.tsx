"use client";

import { useState } from "react";

type Props = {
  generations: string[];
};

export default function GenerationLog({ generations }: Props) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  if (generations.length === 0) return null;

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold">生成テキスト</h2>
      <div className="space-y-1">
        {generations.map((text, i) => (
          <div key={i} className="border border-gray-200 rounded">
            <button
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
              className="w-full text-left px-3 py-2 text-sm font-medium bg-gray-50 hover:bg-gray-100 flex justify-between items-center"
            >
              <span>Trial {i}</span>
              <span className="text-gray-400">
                {openIndex === i ? "−" : "+"}
              </span>
            </button>
            {openIndex === i && (
              <div className="px-3 py-2 text-sm whitespace-pre-wrap bg-white">
                {text}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
