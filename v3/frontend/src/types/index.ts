export type ProcessingMode =
  | "keep_original"
  | "safe_fill"
  | "text_pixel_inpaint"
  | "gradient_restore"
  | "panel_restore"
  | "advanced_inpaint"
  | "manual_review";

export type RestoreStatus =
  | "pending"
  | "success"
  | "failed"
  | "manual_review"
  | "rollback";

export type ViewMode = "original" | "clean" | "restored";

export interface BBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface TextBlock {
  id: string;
  text: string;
  bbox: BBox;
  polygon: [number, number][];
  confidence: number;
  visible: boolean;
  mode: ProcessingMode;
  risk_score: number;
  restore_status: RestoreStatus;
}

export interface TextLayer {
  session_id: string;
  image_width: number;
  image_height: number;
  blocks: TextBlock[];
}

export interface ImageInfo {
  session_id: string;
  original_url: string;
  width: number;
  height: number;
  filename: string;
}

export interface MaskUrls {
  text_mask_url: string;
  protection_mask_url: string;
  final_remove_mask_url: string;
}

export interface ProcessingState {
  isUploading: boolean;
  isDetecting: boolean;
  isCreatingMasks: boolean;
  isRemoving: boolean;
  isRestoring: boolean;
}
