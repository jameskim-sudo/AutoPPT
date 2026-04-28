// ── 공통 타입 정의 ───────────────────────────────────────────────────────────

export type TextAlign = "left" | "center" | "right";

export interface BoundingBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface TextBlock {
  id: string;
  text: string;
  bbox: BoundingBox;
  fontSize: number;
  fontFamily: string;
  bold: boolean;
  italic: boolean;
  color: string;        // "#rrggbb"
  align: TextAlign;
  lineBreaks: string[];
  confidence: number;
}

// ── API 응답 타입 ────────────────────────────────────────────────────────────

export interface UploadResponse {
  image_id: string;
  filename: string;
  width: number;
  height: number;
  image_url: string;
}

export interface AnalyzeResponse {
  image_id: string;
  image_width: number;
  image_height: number;
  blocks: TextBlock[];
}

export interface InpaintResponse {
  cleaned_image_id: string;
  cleaned_image_url: string;
}

export interface GeneratePPTResponse {
  file_id: string;
  download_url: string;
}

export interface ApiError {
  error: string;
  detail: string;
  suggestions?: string[];
}

// ── 처리 상태 ────────────────────────────────────────────────────────────────

export type ProcessStep =
  | "idle"
  | "uploading"
  | "analyzing"
  | "inpainting"
  | "ready"
  | "generating"
  | "done"
  | "error";

export interface ProcessState {
  step: ProcessStep;
  imageId: string | null;
  imageUrl: string | null;
  imageWidth: number;
  imageHeight: number;
  blocks: TextBlock[];
  cleanedImageUrl: string | null;
  cleanedImageId: string | null;
  downloadUrl: string | null;
  fileId: string | null;
  error: string | null;
  errorDetail: string | null;
  // 인페인트 파라미터
  dilationKernel: number;
  inpaintRadius: number;
  inpaintMethod: "telea" | "ns";
}
