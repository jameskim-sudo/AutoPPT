"use client";

import React from "react";
import { Download, Loader2 } from "lucide-react";

interface Props {
  downloadUrl: string | null;
  isGenerating: boolean;
  onGenerate: () => void;
  canGenerate: boolean;
}

export default function DownloadButton({
  downloadUrl,
  isGenerating,
  onGenerate,
  canGenerate,
}: Props) {
  const handleDownload = () => {
    if (!downloadUrl) return;
    // 새 탭에서 다운로드
    window.open(downloadUrl, "_blank");
  };

  if (downloadUrl) {
    return (
      <button
        onClick={handleDownload}
        className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold px-6 py-3 rounded-xl transition-colors shadow-md"
      >
        <Download className="w-5 h-5" />
        PPTX 다운로드
      </button>
    );
  }

  return (
    <button
      onClick={onGenerate}
      disabled={!canGenerate || isGenerating}
      className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-xl transition-colors shadow-md"
    >
      {isGenerating ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          PPTX 생성 중...
        </>
      ) : (
        <>
          <Download className="w-5 h-5" />
          PPT 생성하기
        </>
      )}
    </button>
  );
}
