"use client";

/**
 * OCR 결과 편집 패널
 *
 * 기능:
 * - 검출된 텍스트 목록 표시 및 수정
 * - 좌표(x, y, w, h) 미세 조정
 * - 폰트 크기 / Bold / 정렬 수정
 * - 블록 삭제
 * - 텍스트 색상 변경
 */

import React, { useState } from "react";
import type { TextBlock, TextAlign } from "@/types";
import { ChevronDown, ChevronUp, Trash2, Plus } from "lucide-react";
import clsx from "clsx";

interface Props {
  blocks: TextBlock[];
  onChange: (blocks: TextBlock[]) => void;
}

interface BlockEditorProps {
  block: TextBlock;
  index: number;
  onUpdate: (updated: TextBlock) => void;
  onDelete: () => void;
}

function BlockEditor({ block, index, onUpdate, onDelete }: BlockEditorProps) {
  const [expanded, setExpanded] = useState(false);

  const update = (partial: Partial<TextBlock>) =>
    onUpdate({ ...block, ...partial });

  const updateBbox = (partial: Partial<TextBlock["bbox"]>) =>
    onUpdate({ ...block, bbox: { ...block.bbox, ...partial } });

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* 헤더 */}
      <div
        className="flex items-center gap-2 p-2.5 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className="text-xs font-bold text-gray-400 w-5 shrink-0">
          {index + 1}
        </span>
        <div
          className="w-2.5 h-2.5 rounded-sm shrink-0"
          style={{ backgroundColor: block.color }}
        />
        <span className="text-xs text-gray-700 truncate flex-1 font-medium">
          {block.text || "(빈 텍스트)"}
        </span>
        <span className="text-xs text-gray-400 shrink-0">
          {Math.round(block.confidence * 100)}%
        </span>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="text-gray-300 hover:text-red-400 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </div>

      {/* 편집 영역 */}
      {expanded && (
        <div className="p-3 space-y-3 text-xs">
          {/* 텍스트 */}
          <div>
            <label className="block text-gray-500 mb-1 font-medium">텍스트</label>
            <textarea
              value={block.text}
              onChange={(e) => update({ text: e.target.value, lineBreaks: e.target.value.split("\n") })}
              rows={2}
              className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs resize-none focus:outline-none focus:ring-1 focus:ring-blue-400"
            />
          </div>

          {/* 좌표 */}
          <div>
            <label className="block text-gray-500 mb-1 font-medium">위치 / 크기 (px)</label>
            <div className="grid grid-cols-4 gap-1.5">
              {(["x", "y", "w", "h"] as const).map((key) => (
                <div key={key}>
                  <label className="block text-gray-400 mb-0.5 uppercase">{key}</label>
                  <input
                    type="number"
                    value={Math.round(block.bbox[key])}
                    onChange={(e) => updateBbox({ [key]: Number(e.target.value) })}
                    className="w-full border border-gray-200 rounded px-1.5 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* 폰트 설정 */}
          <div className="grid grid-cols-3 gap-2">
            {/* 폰트 크기 */}
            <div>
              <label className="block text-gray-500 mb-1 font-medium">크기(pt)</label>
              <input
                type="number"
                value={block.fontSize}
                min={6}
                max={144}
                step={0.5}
                onChange={(e) => update({ fontSize: Number(e.target.value) })}
                className="w-full border border-gray-200 rounded px-1.5 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
              />
            </div>

            {/* 색상 */}
            <div>
              <label className="block text-gray-500 mb-1 font-medium">색상</label>
              <input
                type="color"
                value={block.color}
                onChange={(e) => update({ color: e.target.value })}
                className="w-full h-7 rounded border border-gray-200 cursor-pointer"
              />
            </div>

            {/* 정렬 */}
            <div>
              <label className="block text-gray-500 mb-1 font-medium">정렬</label>
              <select
                value={block.align}
                onChange={(e) => update({ align: e.target.value as TextAlign })}
                className="w-full border border-gray-200 rounded px-1 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
              >
                <option value="left">왼쪽</option>
                <option value="center">가운데</option>
                <option value="right">오른쪽</option>
              </select>
            </div>
          </div>

          {/* Bold / Italic */}
          <div className="flex gap-3">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={block.bold}
                onChange={(e) => update({ bold: e.target.checked })}
                className="accent-blue-500"
              />
              <span className="font-bold">Bold</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={block.italic}
                onChange={(e) => update({ italic: e.target.checked })}
                className="accent-blue-500"
              />
              <span className="italic">Italic</span>
            </label>
          </div>

          {/* 폰트 패밀리 */}
          <div>
            <label className="block text-gray-500 mb-1 font-medium">폰트</label>
            <select
              value={block.fontFamily}
              onChange={(e) => update({ fontFamily: e.target.value })}
              className="w-full border border-gray-200 rounded px-1.5 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-400"
            >
              <option value="Malgun Gothic">맑은 고딕</option>
              <option value="NanumGothic">나눔고딕</option>
              <option value="NanumMyeongjo">나눔명조</option>
              <option value="Gulim">굴림</option>
              <option value="Dotum">돋움</option>
              <option value="Arial">Arial</option>
              <option value="Calibri">Calibri</option>
              <option value="Times New Roman">Times New Roman</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
}

export default function OCREditor({ blocks, onChange }: Props) {
  const updateBlock = (index: number, updated: TextBlock) => {
    const next = [...blocks];
    next[index] = updated;
    onChange(next);
  };

  const deleteBlock = (index: number) => {
    onChange(blocks.filter((_, i) => i !== index));
  };

  const addBlock = () => {
    const newBlock: TextBlock = {
      id: `block-new-${Date.now()}`,
      text: "새 텍스트",
      bbox: { x: 50, y: 50, w: 200, h: 40 },
      fontSize: 16,
      fontFamily: "Malgun Gothic",
      bold: false,
      italic: false,
      color: "#000000",
      align: "left",
      lineBreaks: ["새 텍스트"],
      confidence: 1.0,
    };
    onChange([...blocks, newBlock]);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">OCR 텍스트 편집</h3>
        <button
          onClick={addBlock}
          className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 border border-blue-200 hover:border-blue-400 rounded-lg px-2 py-1 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          블록 추가
        </button>
      </div>

      {blocks.length === 0 ? (
        <div className="text-center py-8 text-sm text-gray-400">
          검출된 텍스트가 없습니다.
          <br />
          블록 추가 버튼으로 수동 추가하세요.
        </div>
      ) : (
        <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
          {blocks.map((block, i) => (
            <BlockEditor
              key={block.id}
              block={block}
              index={i}
              onUpdate={(u) => updateBlock(i, u)}
              onDelete={() => deleteBlock(i)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
