"use client";

import { useEffect, useRef, useState } from "react";
import { TextBlock, ImageInfo } from "@/types";

interface Props {
  imageUrl: string | null;
  maskOverlayUrl: string | null;
  blocks: TextBlock[];
  showTextLayer: boolean;
  imageInfo: ImageInfo | null;
}

const STATUS_COLOR: Record<string, string> = {
  pending: "#60a5fa",
  success: "#34d399",
  failed: "#f87171",
  rollback: "#fb923c",
  manual_review: "#facc15",
};

const RISK_BORDER: (risk: number) => string = (r) =>
  r > 0.7 ? "#ef4444" : r > 0.4 ? "#f59e0b" : "#34d399";

export function CanvasPreview({
  imageUrl,
  maskOverlayUrl,
  blocks,
  showTextLayer,
  imageInfo,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const overlayRef = useRef<HTMLCanvasElement>(null);
  const [imgLoaded, setImgLoaded] = useState(false);

  // Redraw overlay whenever relevant props change
  useEffect(() => {
    const canvas = overlayRef.current;
    const img = imgRef.current;
    if (!canvas || !img || !imgLoaded) return;

    const dw = img.offsetWidth;
    const dh = img.offsetHeight;
    if (dw === 0 || dh === 0) return;

    canvas.width = dw;
    canvas.height = dh;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, dw, dh);

    if (!showTextLayer || blocks.length === 0) return;

    const nw = imageInfo?.width ?? img.naturalWidth;
    const nh = imageInfo?.height ?? img.naturalHeight;
    const sx = dw / nw;
    const sy = dh / nh;

    for (const block of blocks) {
      if (!block.visible) continue;

      const { x, y, w, h } = block.bbox;
      const rx = x * sx;
      const ry = y * sy;
      const rw = w * sx;
      const rh = h * sy;

      const borderColor = RISK_BORDER(block.risk_score);
      const statusColor = STATUS_COLOR[block.restore_status] ?? "#60a5fa";

      // Fill
      ctx.fillStyle = `${borderColor}22`;
      ctx.fillRect(rx, ry, rw, rh);

      // Border
      ctx.strokeStyle = borderColor;
      ctx.lineWidth = 1.5;
      ctx.strokeRect(rx, ry, rw, rh);

      // Status dot
      ctx.beginPath();
      ctx.arc(rx + rw - 5, ry + 5, 4, 0, Math.PI * 2);
      ctx.fillStyle = statusColor;
      ctx.fill();

      // Text label
      const label = block.text.length > 16 ? block.text.slice(0, 16) + "…" : block.text;
      ctx.font = "11px monospace";
      ctx.fillStyle = "#fff";
      ctx.shadowColor = "#000";
      ctx.shadowBlur = 3;
      ctx.fillText(label, rx + 2, ry - 3);
      ctx.shadowBlur = 0;
    }
  }, [blocks, showTextLayer, imageUrl, imgLoaded, imageInfo]);

  // Reset loaded state when image url changes
  useEffect(() => {
    setImgLoaded(false);
  }, [imageUrl]);

  if (!imageUrl) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-950 text-gray-600 select-none">
        <div className="text-center">
          <div className="text-5xl mb-3">🖼</div>
          <p className="text-sm">좌측에서 이미지를 업로드하세요</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="flex-1 flex items-center justify-center overflow-auto bg-gray-950 p-4"
    >
      <div className="relative inline-block max-w-full max-h-full">
        {/* Base image */}
        <img
          ref={imgRef}
          src={imageUrl}
          alt="preview"
          className="block max-w-full max-h-[calc(100vh-120px)] object-contain"
          onLoad={() => setImgLoaded(true)}
          style={{ display: "block" }}
        />

        {/* Mask overlay (semi-transparent) */}
        {maskOverlayUrl && imgLoaded && (
          <img
            src={`${maskOverlayUrl}?t=${Date.now()}`}
            alt="mask overlay"
            className="absolute inset-0 w-full h-full object-contain opacity-50 pointer-events-none mix-blend-screen"
          />
        )}

        {/* Text layer canvas */}
        <canvas
          ref={overlayRef}
          className="absolute inset-0 pointer-events-none"
          style={{ top: 0, left: 0 }}
        />
      </div>
    </div>
  );
}
