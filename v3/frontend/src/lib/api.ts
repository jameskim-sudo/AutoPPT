import {
  ImageInfo,
  TextBlock,
  TextLayer,
  MaskUrls,
} from "@/types";

const BASE = "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json();
}

export async function uploadImage(file: File): Promise<ImageInfo> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: fd });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function detectText(sessionId: string): Promise<{
  session_id: string;
  text_layer: TextLayer;
  block_count: number;
}> {
  return post("/api/detect-text", { session_id: sessionId });
}

export async function createMasks(
  sessionId: string,
  blocks: TextBlock[],
  protectionStrength = 1.0
): Promise<MaskUrls & { session_id: string }> {
  return post("/api/create-masks", {
    session_id: sessionId,
    blocks,
    protection_strength: protectionStrength,
  });
}

export async function removeText(
  sessionId: string,
  blocks: TextBlock[]
): Promise<{ session_id: string; clean_background_url: string; blocks: TextBlock[] }> {
  return post("/api/remove-text", { session_id: sessionId, blocks });
}

export async function restoreBackground(
  sessionId: string,
  blocks: TextBlock[]
): Promise<{ session_id: string; restored_background_url: string; blocks: TextBlock[] }> {
  return post("/api/restore-background", { session_id: sessionId, blocks });
}

export function staticUrl(path: string): string {
  return `${BASE}${path}`;
}

export function downloadUrl(sessionId: string, key: string): string {
  return `${BASE}/api/download/${sessionId}/${key}`;
}

export function debugZipUrl(sessionId: string): string {
  return `${BASE}/api/download/${sessionId}/debug/zip`;
}
