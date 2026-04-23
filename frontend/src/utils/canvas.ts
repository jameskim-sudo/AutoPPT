/**
 * Canvas 유틸리티
 *
 * 원본 이미지 위에 bounding box를 그려 검출 결과를 시각화한다.
 */

import type { TextBlock } from "@/types";

const BOX_COLORS = [
  "#3b82f6", "#ef4444", "#10b981", "#f59e0b",
  "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
];

/**
 * 이미지 URL을 로드해 canvas에 그리고, 그 위에 bounding box 를 오버레이한다.
 *
 * @returns canvas element (호출자가 DOM에 추가하거나 toDataURL 로 변환 가능)
 */
export function drawDetectionOverlay(
  imageUrl: string,
  blocks: TextBlock[],
  maxWidth: number = 800
): Promise<HTMLCanvasElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      const scale = Math.min(1, maxWidth / img.width);
      const canvas = document.createElement("canvas");
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;

      const ctx = canvas.getContext("2d");
      if (!ctx) return reject(new Error("Canvas 2D context 없음"));

      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      blocks.forEach((block, i) => {
        const color = BOX_COLORS[i % BOX_COLORS.length];
        const { x, y, w, h } = block.bbox;

        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(x * scale, y * scale, w * scale, h * scale);

        // 번호 라벨
        const label = `${i + 1}`;
        ctx.fillStyle = color;
        const lx = x * scale;
        const ly = Math.max(0, y * scale - 4);
        ctx.font = "bold 12px sans-serif";
        const tw = ctx.measureText(label).width + 6;
        ctx.fillRect(lx, ly - 14, tw, 16);
        ctx.fillStyle = "#fff";
        ctx.fillText(label, lx + 3, ly);
      });

      resolve(canvas);
    };
    img.onerror = () => reject(new Error("이미지 로드 실패"));
    img.src = imageUrl;
  });
}
