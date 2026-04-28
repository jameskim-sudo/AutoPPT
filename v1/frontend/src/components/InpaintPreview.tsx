"use client";

/**
 * 텍스트 제거(inpaint) 결과 미리보기
 */

import React from "react";
import { Loader2 } from "lucide-react";
import type { ProcessStep } from "@/types";

interface Props {
  cleanedImageUrl: string | null;
  step: ProcessStep;
  onRerunInpaint: () => void;
  dilationKernel: number;
  inpaintRadius: number;
  inpaintMethod: "telea" | "ns";
  onParamChange: (params: { dilationKernel?: number; inpaintRadius?: number; inpaintMethod?: "telea" | "ns" }) => void;
}

export default function InpaintPreview({
  cleanedImageUrl,
  step,
  onRerunInpaint,
  dilationKernel,
  inpaintRadius,
  inpaintMethod,
  onParamChange,
}: Props) {
  const isLoading = step === "inpainting";

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-700">텍스트 제거 결과</h3>

      {/* 결과 이미지 */}
      <div className="relative rounded-lg overflow-hidden bg-gray-100 min-h-32 flex items-center justify-center">
        {isLoading ? (
          <div className="flex flex-col items-center gap-2 py-8">
            <Loader2 className="w-7 h-7 animate-spin text-blue-500" />
            <p className="text-sm text-gray-500">텍스트 제거 중...</p>
          </div>
        ) : cleanedImageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={cleanedImageUrl}
            alt="텍스트 제거 결과"
            className="w-full h-auto"
          />
        ) : (
          <p className="text-sm text-gray-400 py-8">텍스트 제거 후 결과가 표시됩니다</p>
        )}
      </div>

      {/* 파라미터 조정 */}
      <div className="rounded-lg border border-gray-200 p-3 space-y-3 text-sm">
        <p className="font-medium text-gray-700 text-xs uppercase tracking-wide">제거 강도 조절</p>

        <div className="grid grid-cols-2 gap-3">
          {/* Dilation Kernel */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              마스크 확장 크기: <strong>{dilationKernel}</strong>
            </label>
            <input
              type="range"
              min={1}
              max={20}
              value={dilationKernel}
              onChange={(e) => onParamChange({ dilationKernel: Number(e.target.value) })}
              className="w-full accent-blue-500"
            />
          </div>

          {/* Inpaint Radius */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              인페인트 반경: <strong>{inpaintRadius}</strong>
            </label>
            <input
              type="range"
              min={1}
              max={15}
              value={inpaintRadius}
              onChange={(e) => onParamChange({ inpaintRadius: Number(e.target.value) })}
              className="w-full accent-blue-500"
            />
          </div>
        </div>

        {/* Method */}
        <div className="flex gap-3 text-xs">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="radio"
              value="telea"
              checked={inpaintMethod === "telea"}
              onChange={() => onParamChange({ inpaintMethod: "telea" })}
              className="accent-blue-500"
            />
            TELEA (권장)
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input
              type="radio"
              value="ns"
              checked={inpaintMethod === "ns"}
              onChange={() => onParamChange({ inpaintMethod: "ns" })}
              className="accent-blue-500"
            />
            Navier-Stokes
          </label>
        </div>

        {/* 재실행 버튼 */}
        {cleanedImageUrl && !isLoading && (
          <button
            onClick={onRerunInpaint}
            className="w-full text-xs font-medium text-blue-600 hover:text-blue-700 border border-blue-200 hover:border-blue-400 rounded-lg py-1.5 transition-colors"
          >
            현재 설정으로 재처리
          </button>
        )}
      </div>
    </div>
  );
}
