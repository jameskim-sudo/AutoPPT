"use client";

/**
 * 텍스트 검출 결과 미리보기
 * 원본 이미지 위에 bounding box를 오버레이해서 보여준다.
 */

import React, { useEffect, useRef, useState } from "react";
import { drawDetectionOverlay } from "@/utils/canvas";
import type { TextBlock } from "@/types";
import { Loader2 } from "lucide-react";

interface Props {
  imageUrl: string;
  blocks: TextBlock[];
}

const BOX_COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b",
  "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
];

export default function DetectionPreview({ imageUrl, blocks }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!imageUrl || blocks.length === 0) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);

    drawDetectionOverlay(imageUrl, blocks, 800)
      .then((canvas) => {
        if (!canvasRef.current) return;
        const ctx = canvasRef.current.getContext("2d");
        if (!ctx) return;
        canvasRef.current.width = canvas.width;
        canvasRef.current.height = canvas.height;
        ctx.drawImage(canvas, 0, 0);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [imageUrl, blocks]);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">검출 결과</h3>
        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
          {blocks.length}개 블록
        </span>
      </div>

      <div className="relative rounded-lg overflow-hidden bg-gray-100 min-h-32 flex items-center justify-center">
        {loading && <Loader2 className="w-6 h-6 animate-spin text-gray-400" />}
        {error && <p className="text-xs text-red-500">{error}</p>}
        <canvas
          ref={canvasRef}
          className={`w-full h-auto ${loading || error ? "hidden" : ""}`}
        />
      </div>

      {/* 블록 번호 범례 */}
      {blocks.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {blocks.map((b, i) => (
            <span
              key={b.id}
              className="text-xs px-1.5 py-0.5 rounded text-white font-medium"
              style={{ backgroundColor: BOX_COLORS[i % BOX_COLORS.length] }}
            >
              {i + 1}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
