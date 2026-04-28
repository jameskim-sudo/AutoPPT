"use client";

import { ImageInfo, ProcessingState } from "@/types";
import { downloadUrl, debugZipUrl } from "@/lib/api";

interface Props {
  imageInfo: ImageInfo | null;
  hasMasks: boolean;
  hasClean: boolean;
  hasRestored: boolean;
  hasBlocks: boolean;
  processing: ProcessingState;
  isAnyProcessing: boolean;
  showTextLayer: boolean;
  sessionId: string | null;
  onDetect: () => void;
  onCreateMasks: () => void;
  onRemoveText: () => void;
  onRestore: () => void;
  onToggleTextLayer: () => void;
}

function Btn({
  onClick,
  disabled,
  loading,
  children,
  variant = "default",
}: {
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
  variant?: "default" | "primary" | "success" | "ghost";
}) {
  const base =
    "px-3 py-1.5 rounded text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed";
  const variants = {
    default: "bg-gray-700 hover:bg-gray-600 text-gray-200",
    primary: "bg-blue-600 hover:bg-blue-500 text-white",
    success: "bg-emerald-600 hover:bg-emerald-500 text-white",
    ghost: "bg-transparent hover:bg-gray-800 text-gray-400 hover:text-gray-200",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${variants[variant]}`}
    >
      {loading ? "처리중..." : children}
    </button>
  );
}

export function BottomBar({
  imageInfo,
  hasMasks,
  hasClean,
  hasRestored,
  hasBlocks,
  processing,
  isAnyProcessing,
  showTextLayer,
  sessionId,
  onDetect,
  onCreateMasks,
  onRemoveText,
  onRestore,
  onToggleTextLayer,
}: Props) {
  return (
    <footer className="shrink-0 flex items-center gap-2 px-4 py-2 bg-gray-900 border-t border-gray-800 flex-wrap">
      {/* Pipeline steps */}
      <div className="flex items-center gap-1.5">
        <StepDot n={1} done={hasBlocks} active={!!imageInfo && !hasBlocks} />
        <Btn
          onClick={onDetect}
          disabled={!imageInfo || isAnyProcessing}
          loading={processing.isDetecting}
          variant="primary"
        >
          1. 텍스트 검출
        </Btn>
      </div>

      <Arrow />

      <div className="flex items-center gap-1.5">
        <StepDot n={2} done={hasMasks} active={hasBlocks && !hasMasks} />
        <Btn
          onClick={onCreateMasks}
          disabled={!hasBlocks || isAnyProcessing}
          loading={processing.isCreatingMasks}
        >
          2. 마스크 생성
        </Btn>
      </div>

      <Arrow />

      <div className="flex items-center gap-1.5">
        <StepDot n={3} done={hasClean} active={hasMasks && !hasClean} />
        <Btn
          onClick={onRemoveText}
          disabled={!hasMasks || isAnyProcessing}
          loading={processing.isRemoving}
        >
          3. 텍스트 제거
        </Btn>
      </div>

      <Arrow />

      <div className="flex items-center gap-1.5">
        <StepDot n={4} done={hasRestored} active={hasClean && !hasRestored} />
        <Btn
          onClick={onRestore}
          disabled={!hasMasks || isAnyProcessing}
          loading={processing.isRestoring}
          variant="success"
        >
          4. 배경 복원
        </Btn>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Overlay toggle */}
      <Btn onClick={onToggleTextLayer} disabled={!hasBlocks} variant="ghost">
        {showTextLayer ? "텍스트 레이어 숨기기" : "텍스트 레이어 보이기"}
      </Btn>

      {/* Downloads */}
      {sessionId && hasRestored && (
        <a href={downloadUrl(sessionId, "result")} download>
          <Btn variant="success">결과 다운로드</Btn>
        </a>
      )}
      {sessionId && (
        <a href={debugZipUrl(sessionId)} download>
          <Btn variant="ghost">디버그 ZIP</Btn>
        </a>
      )}
    </footer>
  );
}

function StepDot({ n, done, active }: { n: number; done: boolean; active: boolean }) {
  return (
    <span
      className={`w-5 h-5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 ${
        done
          ? "bg-emerald-500 text-white"
          : active
          ? "bg-blue-500 text-white animate-pulse"
          : "bg-gray-700 text-gray-500"
      }`}
    >
      {done ? "✓" : n}
    </span>
  );
}

function Arrow() {
  return <span className="text-gray-600 text-sm">→</span>;
}
