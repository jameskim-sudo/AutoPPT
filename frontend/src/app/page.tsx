"use client";

/**
 * AutoPPT 메인 페이지
 *
 * 레이아웃:
 *   - 헤더: 타이틀 + 진행 단계 표시
 *   - 좌측 패널:  이미지 업로드 + 원본 이미지 미리보기
 *   - 중앙 패널:  검출 결과 + 텍스트 제거 결과
 *   - 우측 패널:  OCR 텍스트 편집기
 *   - 하단:       PPT 생성 / 다운로드 버튼
 */

import React, { useRef } from "react";
import { useImageProcessor } from "@/hooks/useImageProcessor";
import ImageUpload from "@/components/ImageUpload";
import DetectionPreview from "@/components/DetectionPreview";
import InpaintPreview from "@/components/InpaintPreview";
import OCREditor from "@/components/OCREditor";
import ProgressStepper from "@/components/ProgressStepper";
import ErrorAlert from "@/components/ErrorAlert";
import DownloadButton from "@/components/DownloadButton";
import { RefreshCw, FileImage, Info } from "lucide-react";

export default function HomePage() {
  const {
    state,
    processImage,
    rerunInpaint,
    generatePPTFile,
    updateBlocks,
    updateInpaintParams,
    reset,
  } = useImageProcessor();

  const isIdle = state.step === "idle";
  const isError = state.step === "error";
  const isReady = ["ready", "generating", "done"].includes(state.step);
  const isGenerating = state.step === "generating";
  const isDone = state.step === "done";
  const isWorking = ["uploading", "analyzing", "inpainting"].includes(state.step);

  const canGenerate =
    isReady &&
    !!state.cleanedImageId &&
    state.blocks.length > 0;

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── 헤더 ────────────────────────────────────────────────────────── */}
      <header className="border-b border-gray-200 bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <FileImage className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-bold text-gray-900">AutoPPT</h1>
            <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
              이미지 → Editable PPTX
            </span>
          </div>

          <div className="flex-1" />

          {/* 진행 상태 */}
          {!isIdle && <ProgressStepper currentStep={state.step} />}

          {/* 초기화 */}
          {!isIdle && (
            <button
              onClick={reset}
              className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              처음부터
            </button>
          )}
        </div>
      </header>

      {/* ── 본문 ────────────────────────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">

        {/* 에러 배너 */}
        {isError && (
          <div className="mb-6">
            <ErrorAlert
              error={state.error ?? "처리 중 오류가 발생했습니다"}
              detail={state.errorDetail}
              onRetry={reset}
            />
          </div>
        )}

        {/* ── 업로드 영역 (idle / error 상태) ─────────────────────────── */}
        {(isIdle || isError) && (
          <div className="max-w-lg mx-auto">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-800">이미지 업로드</h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  PNG / JPG / WEBP 이미지를 업로드하면 자동으로 텍스트를 검출하고 PPTX를 생성합니다.
                </p>
              </div>

              <ImageUpload onFile={processImage} disabled={isWorking} />

              <div className="flex items-start gap-2 text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
                <Info className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  업로드 → OCR 분석 → 텍스트 제거 → 편집 → PPTX 다운로드 순으로 진행됩니다.
                  한글 + 영문 혼합 이미지를 지원합니다.
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ── 처리 중 상태 ─────────────────────────────────────────────── */}
        {isWorking && (
          <div className="max-w-lg mx-auto bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center space-y-4">
            <div className="flex justify-center">
              <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin" />
            </div>
            <div>
              <p className="font-semibold text-gray-800">
                {state.step === "uploading" && "이미지 업로드 중..."}
                {state.step === "analyzing" && "텍스트 검출 중 (PaddleOCR)..."}
                {state.step === "inpainting" && "텍스트 제거 중 (Inpainting)..."}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {state.step === "analyzing" && "한국어 + 영어 OCR 분석 중입니다. 잠시 기다려주세요."}
                {state.step === "inpainting" && "배경에서 텍스트를 자연스럽게 제거하고 있습니다."}
              </p>
            </div>

            {/* 원본 이미지 미리보기 (업로드 후) */}
            {state.imageUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={state.imageUrl}
                alt="원본 이미지"
                className="max-h-48 mx-auto rounded-lg object-contain"
              />
            )}
          </div>
        )}

        {/* ── 편집 / 결과 화면 ─────────────────────────────────────────── */}
        {isReady && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* 좌측: 원본 + 검출 결과 */}
            <div className="space-y-4">
              {/* 원본 이미지 */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4 space-y-2">
                <h3 className="text-sm font-semibold text-gray-700">원본 이미지</h3>
                {state.imageUrl && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={state.imageUrl}
                    alt="원본"
                    className="w-full h-auto rounded-lg object-contain"
                  />
                )}
                <p className="text-xs text-gray-400 text-right">
                  {state.imageWidth} × {state.imageHeight} px
                </p>
              </div>

              {/* 검출 결과 */}
              {state.imageUrl && state.blocks.length > 0 && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4">
                  <DetectionPreview
                    imageUrl={state.imageUrl}
                    blocks={state.blocks}
                  />
                </div>
              )}
            </div>

            {/* 중앙: 텍스트 제거 결과 + 파라미터 */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4">
              <InpaintPreview
                cleanedImageUrl={state.cleanedImageUrl}
                step={state.step}
                onRerunInpaint={rerunInpaint}
                dilationKernel={state.dilationKernel}
                inpaintRadius={state.inpaintRadius}
                inpaintMethod={state.inpaintMethod}
                onParamChange={updateInpaintParams}
              />
            </div>

            {/* 우측: OCR 편집기 */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4">
              <OCREditor blocks={state.blocks} onChange={updateBlocks} />
            </div>
          </div>
        )}

        {/* ── 하단 액션 버튼 ───────────────────────────────────────────── */}
        {isReady && (
          <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
            <div className="text-sm text-gray-600">
              {isDone ? (
                <span className="text-green-600 font-semibold">
                  PPTX 생성 완료! 아래 버튼으로 다운로드하세요.
                </span>
              ) : (
                <span>
                  OCR 결과를 확인·수정하고 PPT를 생성하세요.{" "}
                  <span className="text-blue-600 font-medium">
                    {state.blocks.length}개 텍스트 블록
                  </span>
                </span>
              )}
            </div>

            <div className="flex gap-3">
              <DownloadButton
                downloadUrl={state.downloadUrl}
                isGenerating={isGenerating}
                onGenerate={generatePPTFile}
                canGenerate={canGenerate}
              />
            </div>
          </div>
        )}

        {/* 경고: 블록 없음 */}
        {isReady && state.blocks.length === 0 && (
          <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-yellow-700">
            텍스트 블록이 없습니다. OCR 편집 패널에서 블록을 직접 추가할 수 있습니다.
          </div>
        )}
      </main>

      {/* ── 푸터 ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 py-4 text-center text-xs text-gray-400">
        AutoPPT — PaddleOCR · OpenCV Inpainting · python-pptx
      </footer>
    </div>
  );
}
