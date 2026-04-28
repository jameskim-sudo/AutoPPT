"use client";

import { useState, useCallback } from "react";
import {
  ImageInfo,
  TextBlock,
  TextLayer,
  MaskUrls,
  ViewMode,
  ProcessingState,
} from "@/types";
import {
  uploadImage,
  detectText,
  createMasks,
  removeText,
  restoreBackground,
  staticUrl,
  downloadUrl,
  debugZipUrl,
} from "@/lib/api";
import { LeftPanel } from "@/components/LeftPanel";
import { CanvasPreview } from "@/components/CanvasPreview";
import { RightPanel } from "@/components/RightPanel";
import { BottomBar } from "@/components/BottomBar";

const INIT_STATE: ProcessingState = {
  isUploading: false,
  isDetecting: false,
  isCreatingMasks: false,
  isRemoving: false,
  isRestoring: false,
};

export default function Home() {
  const [imageInfo, setImageInfo] = useState<ImageInfo | null>(null);
  const [blocks, setBlocks] = useState<TextBlock[]>([]);
  const [textLayer, setTextLayer] = useState<TextLayer | null>(null);
  const [maskUrls, setMaskUrls] = useState<MaskUrls | null>(null);
  const [cleanBgUrl, setCleanBgUrl] = useState<string | null>(null);
  const [restoredBgUrl, setRestoredBgUrl] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("original");
  const [showTextLayer, setShowTextLayer] = useState(true);
  const [showMask, setShowMask] = useState(false);
  const [protectionStrength, setProtectionStrength] = useState(1.0);
  const [processing, setProcessing] = useState<ProcessingState>(INIT_STATE);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string>("");

  const status = (msg: string) => setStatusMsg(msg);

  const handleUpload = useCallback(async (file: File) => {
    setError(null);
    setProcessing((p) => ({ ...p, isUploading: true }));
    status("이미지 업로드 중...");
    try {
      const info = await uploadImage(file);
      setImageInfo(info);
      setBlocks([]);
      setTextLayer(null);
      setMaskUrls(null);
      setCleanBgUrl(null);
      setRestoredBgUrl(null);
      setViewMode("original");
      status("업로드 완료");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "업로드 실패");
    } finally {
      setProcessing((p) => ({ ...p, isUploading: false }));
    }
  }, []);

  const handleDetect = useCallback(async () => {
    if (!imageInfo) return;
    setError(null);
    setProcessing((p) => ({ ...p, isDetecting: true }));
    status("텍스트 검출 중... (최초 실행 시 OCR 모델 다운로드로 시간이 걸릴 수 있습니다)");
    try {
      const res = await detectText(imageInfo.session_id);
      setTextLayer(res.text_layer);
      setBlocks(res.text_layer.blocks);
      setShowTextLayer(true);
      status(`텍스트 ${res.block_count}개 검출 완료`);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "텍스트 검출 실패");
    } finally {
      setProcessing((p) => ({ ...p, isDetecting: false }));
    }
  }, [imageInfo]);

  const handleCreateMasks = useCallback(async () => {
    if (!imageInfo || blocks.length === 0) return;
    setError(null);
    setProcessing((p) => ({ ...p, isCreatingMasks: true }));
    status("마스크 생성 중...");
    try {
      const res = await createMasks(imageInfo.session_id, blocks, protectionStrength);
      setMaskUrls({
        text_mask_url: res.text_mask_url,
        protection_mask_url: res.protection_mask_url,
        final_remove_mask_url: res.final_remove_mask_url,
      });
      status("마스크 생성 완료");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "마스크 생성 실패");
    } finally {
      setProcessing((p) => ({ ...p, isCreatingMasks: false }));
    }
  }, [imageInfo, blocks, protectionStrength]);

  const handleRemoveText = useCallback(async () => {
    if (!imageInfo || !maskUrls) return;
    setError(null);
    setProcessing((p) => ({ ...p, isRemoving: true }));
    status("텍스트 제거 중...");
    try {
      const res = await removeText(imageInfo.session_id, blocks);
      setBlocks(res.blocks);
      setCleanBgUrl(res.clean_background_url);
      setViewMode("clean");
      status("텍스트 제거 완료 — clean background 생성됨");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "텍스트 제거 실패");
    } finally {
      setProcessing((p) => ({ ...p, isRemoving: false }));
    }
  }, [imageInfo, maskUrls, blocks]);

  const handleRestore = useCallback(async () => {
    if (!imageInfo || !maskUrls) return;
    setError(null);
    setProcessing((p) => ({ ...p, isRestoring: true }));
    status("배경 복원 중...");
    try {
      const res = await restoreBackground(imageInfo.session_id, blocks);
      setBlocks(res.blocks);
      setRestoredBgUrl(res.restored_background_url);
      setViewMode("restored");
      status("배경 복원 완료");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "배경 복원 실패");
    } finally {
      setProcessing((p) => ({ ...p, isRestoring: false }));
    }
  }, [imageInfo, maskUrls, blocks]);

  const updateBlock = useCallback((updated: TextBlock) => {
    setBlocks((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
  }, []);

  const toggleAllVisible = useCallback((visible: boolean) => {
    setBlocks((prev) => prev.map((b) => ({ ...b, visible })));
  }, []);

  const isAnyProcessing = Object.values(processing).some(Boolean);

  const currentImageUrl = (() => {
    if (!imageInfo) return null;
    if (viewMode === "restored" && restoredBgUrl) return staticUrl(restoredBgUrl);
    if (viewMode === "clean" && cleanBgUrl) return staticUrl(cleanBgUrl);
    return staticUrl(imageInfo.original_url);
  })();

  const maskOverlayUrl = showMask && maskUrls
    ? staticUrl(maskUrls.final_remove_mask_url)
    : null;

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="flex items-center gap-3 px-4 py-2 bg-gray-900 border-b border-gray-800 shrink-0">
        <span className="text-lg font-semibold text-white">Text Layer Separator</span>
        <span className="text-xs text-gray-500">v3</span>
        {statusMsg && (
          <span className="ml-4 text-sm text-blue-400 truncate max-w-lg">{statusMsg}</span>
        )}
        {error && (
          <span className="ml-4 text-sm text-red-400 truncate max-w-lg">오류: {error}</span>
        )}
      </header>

      {/* Main 3-panel area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel */}
        <LeftPanel
          imageInfo={imageInfo}
          textLayer={textLayer}
          showTextLayer={showTextLayer}
          showMask={showMask}
          protectionStrength={protectionStrength}
          viewMode={viewMode}
          hasClean={!!cleanBgUrl}
          hasRestored={!!restoredBgUrl}
          onShowTextLayerChange={setShowTextLayer}
          onShowMaskChange={setShowMask}
          onProtectionStrengthChange={setProtectionStrength}
          onViewModeChange={setViewMode}
          onToggleAllVisible={toggleAllVisible}
          onUpload={handleUpload}
        />

        {/* Center canvas */}
        <CanvasPreview
          imageUrl={currentImageUrl}
          maskOverlayUrl={maskOverlayUrl}
          blocks={blocks}
          showTextLayer={showTextLayer}
          imageInfo={imageInfo}
        />

        {/* Right panel */}
        <RightPanel
          blocks={blocks}
          onUpdateBlock={updateBlock}
          sessionId={imageInfo?.session_id ?? null}
        />
      </div>

      {/* Bottom bar */}
      <BottomBar
        imageInfo={imageInfo}
        hasMasks={!!maskUrls}
        hasClean={!!cleanBgUrl}
        hasRestored={!!restoredBgUrl}
        hasBlocks={blocks.length > 0}
        processing={processing}
        isAnyProcessing={isAnyProcessing}
        showTextLayer={showTextLayer}
        onDetect={handleDetect}
        onCreateMasks={handleCreateMasks}
        onRemoveText={handleRemoveText}
        onRestore={handleRestore}
        onToggleTextLayer={() => setShowTextLayer((v) => !v)}
        sessionId={imageInfo?.session_id ?? null}
      />
    </div>
  );
}
