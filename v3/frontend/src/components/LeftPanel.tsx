"use client";

import { useRef } from "react";
import { ImageInfo, TextLayer, ViewMode } from "@/types";

interface Props {
  imageInfo: ImageInfo | null;
  textLayer: TextLayer | null;
  showTextLayer: boolean;
  showMask: boolean;
  protectionStrength: number;
  viewMode: ViewMode;
  hasClean: boolean;
  hasRestored: boolean;
  onShowTextLayerChange: (v: boolean) => void;
  onShowMaskChange: (v: boolean) => void;
  onProtectionStrengthChange: (v: number) => void;
  onViewModeChange: (v: ViewMode) => void;
  onToggleAllVisible: (v: boolean) => void;
  onUpload: (file: File) => void;
}

export function LeftPanel({
  imageInfo,
  textLayer,
  showTextLayer,
  showMask,
  protectionStrength,
  viewMode,
  hasClean,
  hasRestored,
  onShowTextLayerChange,
  onShowMaskChange,
  onProtectionStrengthChange,
  onViewModeChange,
  onToggleAllVisible,
  onUpload,
}: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) onUpload(f);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) onUpload(f);
  };

  return (
    <aside className="w-64 shrink-0 flex flex-col gap-3 bg-gray-900 border-r border-gray-800 p-3 overflow-y-auto">
      {/* Upload zone */}
      <section>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">이미지 업로드</p>
        <div
          className="border-2 border-dashed border-gray-700 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500 transition-colors"
          onClick={() => fileRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/jpg"
            className="hidden"
            onChange={handleFile}
          />
          <div className="text-2xl mb-1">📁</div>
          <p className="text-xs text-gray-400">PNG / JPG 드래그 또는 클릭</p>
        </div>
      </section>

      {/* Image info */}
      {imageInfo && (
        <section className="bg-gray-800 rounded-lg p-3 text-xs space-y-1">
          <p className="font-semibold text-gray-300 truncate">{imageInfo.filename}</p>
          <p className="text-gray-500">{imageInfo.width} × {imageInfo.height} px</p>
          <p className="text-gray-600 font-mono text-[10px] truncate">{imageInfo.session_id}</p>
        </section>
      )}

      {/* OCR info */}
      {textLayer && (
        <section className="bg-gray-800 rounded-lg p-3 text-xs space-y-1">
          <p className="text-gray-400">텍스트 블록: <span className="text-white font-semibold">{textLayer.blocks.length}</span>개</p>
        </section>
      )}

      {/* View mode */}
      {imageInfo && (
        <section>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">미리보기</p>
          <div className="flex flex-col gap-1">
            {(
              [
                ["original", "원본"],
                ["clean", "텍스트 제거"],
                ["restored", "복원 완료"],
              ] as [ViewMode, string][]
            ).map(([mode, label]) => (
              <button
                key={mode}
                disabled={
                  (mode === "clean" && !hasClean) ||
                  (mode === "restored" && !hasRestored)
                }
                onClick={() => onViewModeChange(mode)}
                className={`text-xs px-3 py-1.5 rounded text-left transition-colors ${
                  viewMode === mode
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Overlay toggles */}
      {imageInfo && (
        <section>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">오버레이</p>
          <label className="flex items-center gap-2 cursor-pointer text-sm py-1">
            <input
              type="checkbox"
              checked={showTextLayer}
              onChange={(e) => onShowTextLayerChange(e.target.checked)}
              className="accent-blue-500"
            />
            텍스트 레이어 표시
          </label>
          <label className="flex items-center gap-2 cursor-pointer text-sm py-1">
            <input
              type="checkbox"
              checked={showMask}
              onChange={(e) => onShowMaskChange(e.target.checked)}
              className="accent-blue-500"
            />
            마스크 오버레이
          </label>
        </section>
      )}

      {/* Bulk block visibility */}
      {textLayer && textLayer.blocks.length > 0 && (
        <section>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">텍스트 블록</p>
          <div className="flex gap-2">
            <button
              onClick={() => onToggleAllVisible(true)}
              className="flex-1 text-xs bg-gray-800 hover:bg-gray-700 rounded px-2 py-1"
            >
              전체 표시
            </button>
            <button
              onClick={() => onToggleAllVisible(false)}
              className="flex-1 text-xs bg-gray-800 hover:bg-gray-700 rounded px-2 py-1"
            >
              전체 숨김
            </button>
          </div>
        </section>
      )}

      {/* Protection strength */}
      {imageInfo && (
        <section>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
            보호 마스크 강도: {(protectionStrength * 100).toFixed(0)}%
          </p>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={protectionStrength}
            onChange={(e) => onProtectionStrengthChange(Number(e.target.value))}
            className="w-full accent-blue-500"
          />
          <p className="text-[10px] text-gray-600 mt-1">
            낮을수록 구조물도 덮어씀. 마스크 재생성 필요.
          </p>
        </section>
      )}
    </aside>
  );
}
