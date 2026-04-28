/**
 * 백엔드 API 클라이언트
 *
 * Next.js rewrites 를 통해 /api/* → http://localhost:8000/api/* 로 프록시된다.
 */

import axios from "axios";
import type {
  UploadResponse,
  AnalyzeResponse,
  InpaintResponse,
  GeneratePPTResponse,
  TextBlock,
} from "@/types";

const client = axios.create({ baseURL: "/" });

// ── Upload ───────────────────────────────────────────────────────────────────

export async function uploadImage(
  file: File,
  onProgress?: (pct: number) => void
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await client.post<UploadResponse>("/api/upload-image", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
  return res.data;
}

// ── Analyze ──────────────────────────────────────────────────────────────────

export async function analyzeImage(imageId: string): Promise<AnalyzeResponse> {
  const res = await client.post<AnalyzeResponse>("/api/analyze-image", {
    image_id: imageId,
  });
  return res.data;
}

// ── Inpaint ──────────────────────────────────────────────────────────────────

export async function inpaintText(
  imageId: string,
  blocks: TextBlock[],
  dilationKernel: number = 5,
  inpaintRadius: number = 3,
  inpaintMethod: "telea" | "ns" = "telea"
): Promise<InpaintResponse> {
  const res = await client.post<InpaintResponse>("/api/inpaint-text", {
    image_id: imageId,
    blocks,
    dilation_kernel: dilationKernel,
    inpaint_radius: inpaintRadius,
    inpaint_method: inpaintMethod,
  });
  return res.data;
}

// ── Generate PPT ─────────────────────────────────────────────────────────────

export async function generatePPT(
  imageId: string,
  cleanedImageId: string,
  blocks: TextBlock[],
  imageWidth: number,
  imageHeight: number
): Promise<GeneratePPTResponse> {
  const res = await client.post<GeneratePPTResponse>("/api/generate-ppt", {
    image_id: imageId,
    cleaned_image_id: cleanedImageId,
    blocks,
    image_width: imageWidth,
    image_height: imageHeight,
  });
  return res.data;
}

// ── 에러 메시지 추출 ─────────────────────────────────────────────────────────

export function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data;
    if (data?.detail) return String(data.detail);
    if (data?.error) return String(data.error);
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "알 수 없는 오류가 발생했습니다.";
}
