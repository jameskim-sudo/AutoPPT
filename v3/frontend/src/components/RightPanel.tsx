"use client";

import { TextBlock, ProcessingMode, RestoreStatus } from "@/types";

interface Props {
  blocks: TextBlock[];
  onUpdateBlock: (block: TextBlock) => void;
  sessionId: string | null;
}

const MODE_OPTIONS: { value: ProcessingMode; label: string }[] = [
  { value: "keep_original", label: "유지" },
  { value: "safe_fill", label: "색상 채움" },
  { value: "text_pixel_inpaint", label: "자동 선택" },
  { value: "gradient_restore", label: "그라데이션" },
  { value: "panel_restore", label: "패널 복원" },
  { value: "advanced_inpaint", label: "고급 inpaint" },
  { value: "manual_review", label: "수동 검토" },
];

const STATUS_BADGE: Record<RestoreStatus, { label: string; cls: string }> = {
  pending: { label: "대기", cls: "bg-gray-700 text-gray-300" },
  success: { label: "완료", cls: "bg-green-900 text-green-300" },
  failed: { label: "실패", cls: "bg-red-900 text-red-300" },
  rollback: { label: "롤백", cls: "bg-orange-900 text-orange-300" },
  manual_review: { label: "수동필요", cls: "bg-yellow-900 text-yellow-300" },
};

function riskBadge(score: number) {
  if (score > 0.7) return "text-red-400";
  if (score > 0.4) return "text-yellow-400";
  return "text-green-400";
}

export function RightPanel({ blocks, onUpdateBlock, sessionId }: Props) {
  if (!sessionId) {
    return (
      <aside className="w-72 shrink-0 bg-gray-900 border-l border-gray-800 flex items-center justify-center">
        <p className="text-xs text-gray-600">이미지를 업로드하세요</p>
      </aside>
    );
  }

  if (blocks.length === 0) {
    return (
      <aside className="w-72 shrink-0 bg-gray-900 border-l border-gray-800 flex items-center justify-center">
        <p className="text-xs text-gray-600">텍스트 검출을 실행하세요</p>
      </aside>
    );
  }

  return (
    <aside className="w-72 shrink-0 flex flex-col bg-gray-900 border-l border-gray-800 overflow-hidden">
      <div className="px-3 py-2 border-b border-gray-800">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          텍스트 블록 ({blocks.length})
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {blocks.map((block) => (
          <BlockCard key={block.id} block={block} onUpdate={onUpdateBlock} />
        ))}
      </div>
    </aside>
  );
}

function BlockCard({
  block,
  onUpdate,
}: {
  block: TextBlock;
  onUpdate: (b: TextBlock) => void;
}) {
  const badge = STATUS_BADGE[block.restore_status];

  return (
    <div
      className={`rounded-lg border p-2 text-xs space-y-1.5 transition-colors ${
        block.visible ? "border-gray-700 bg-gray-800" : "border-gray-800 bg-gray-900 opacity-60"
      }`}
    >
      {/* Header row */}
      <div className="flex items-start gap-2">
        <input
          type="checkbox"
          checked={block.visible}
          onChange={(e) => onUpdate({ ...block, visible: e.target.checked })}
          className="mt-0.5 accent-blue-500 shrink-0"
        />
        <div className="flex-1 min-w-0">
          <p className="text-gray-200 font-medium truncate leading-tight">{block.text}</p>
          <p className="text-gray-500 text-[10px]">{block.id}</p>
        </div>
        <span className={`shrink-0 rounded px-1 py-0.5 text-[10px] font-medium ${badge.cls}`}>
          {badge.label}
        </span>
      </div>

      {/* Stats row */}
      <div className="flex gap-3 text-[10px] text-gray-500">
        <span>신뢰도: <span className="text-gray-300">{(block.confidence * 100).toFixed(0)}%</span></span>
        <span>
          위험도:{" "}
          <span className={riskBadge(block.risk_score)}>
            {(block.risk_score * 100).toFixed(0)}%
          </span>
        </span>
      </div>

      {/* BBox */}
      <p className="text-[10px] text-gray-600 font-mono">
        {block.bbox.x},{block.bbox.y} {block.bbox.w}×{block.bbox.h}
      </p>

      {/* Mode selector */}
      <div>
        <select
          value={block.mode}
          onChange={(e) =>
            onUpdate({ ...block, mode: e.target.value as ProcessingMode })
          }
          className="w-full bg-gray-700 border border-gray-600 rounded px-1 py-0.5 text-[11px] text-gray-200 focus:outline-none focus:border-blue-500"
        >
          {MODE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {/* Manual review warning */}
      {block.restore_status === "manual_review" && (
        <p className="text-yellow-500 text-[10px]">
          구조물과 겹쳐 자동 처리 불가. 모드를 변경하거나 유지하세요.
        </p>
      )}
      {block.restore_status === "rollback" && (
        <p className="text-orange-400 text-[10px]">
          품질 미달로 원본 유지됨. 모드를 변경 후 재실행하세요.
        </p>
      )}
    </div>
  );
}
