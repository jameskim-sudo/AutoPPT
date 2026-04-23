"use client";

import React from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  error: string;
  detail?: string | null;
  onRetry?: () => void;
}

const SUGGESTIONS: Record<string, string[]> = {
  OCR: [
    "이미지 해상도가 너무 낮지 않은지 확인하세요 (권장: 1000px 이상)",
    "텍스트가 선명하게 보이는지 확인하세요",
    "이미지가 너무 기울어지지 않았는지 확인하세요",
  ],
  인페인팅: [
    "dilation_kernel 값을 줄여서 다시 시도해보세요",
    "inpaint_radius 값을 조정해보세요",
    "배경이 복잡한 경우 NS 방법으로 변경해보세요",
  ],
  PPT: [
    "텍스트 블록이 하나 이상 있어야 합니다",
    "텍스트 인페인팅을 먼저 완료해야 합니다",
  ],
  기본: [
    "페이지를 새로고침 후 다시 시도하세요",
    "다른 이미지 파일로 시도해보세요",
    "파일 크기가 20MB 이하인지 확인하세요",
  ],
};

function getSuggestions(error: string): string[] {
  if (error.includes("OCR") || error.includes("ocr")) return SUGGESTIONS["OCR"];
  if (error.includes("인페인트") || error.includes("inpaint")) return SUGGESTIONS["인페인팅"];
  if (error.includes("PPT") || error.includes("pptx")) return SUGGESTIONS["PPT"];
  return SUGGESTIONS["기본"];
}

export default function ErrorAlert({ error, detail, onRetry }: Props) {
  const suggestions = getSuggestions(error);

  return (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-red-700">{error}</p>
          {detail && <p className="text-sm text-red-600 mt-0.5">{detail}</p>}

          {suggestions.length > 0 && (
            <ul className="mt-2 space-y-1">
              {suggestions.map((s, i) => (
                <li key={i} className="text-xs text-red-600 flex items-start gap-1.5">
                  <span className="mt-0.5 text-red-400">•</span>
                  {s}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 flex items-center gap-1.5 text-sm font-medium text-red-600 hover:text-red-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          다시 시도
        </button>
      )}
    </div>
  );
}
