/**
 * 이미지 처리 흐름을 관리하는 커스텀 훅
 *
 * 상태 전이:
 *   idle → uploading → analyzing → inpainting → ready
 *   ready → generating → done
 *   any → error
 */

"use client";

import { useReducer, useCallback } from "react";
import type { ProcessState, ProcessStep, TextBlock } from "@/types";
import {
  uploadImage,
  analyzeImage,
  inpaintText,
  generatePPT,
  extractErrorMessage,
} from "@/utils/api";

// ── 초기 상태 ────────────────────────────────────────────────────────────────

const initialState: ProcessState = {
  step: "idle",
  imageId: null,
  imageUrl: null,
  imageWidth: 0,
  imageHeight: 0,
  blocks: [],
  cleanedImageUrl: null,
  cleanedImageId: null,
  downloadUrl: null,
  fileId: null,
  error: null,
  errorDetail: null,
  dilationKernel: 5,
  inpaintRadius: 3,
  inpaintMethod: "telea",
};

// ── Action 타입 ──────────────────────────────────────────────────────────────

type Action =
  | { type: "SET_STEP"; payload: ProcessStep }
  | {
      type: "UPLOAD_DONE";
      payload: { imageId: string; imageUrl: string; imageWidth: number; imageHeight: number };
    }
  | { type: "ANALYZE_DONE"; payload: { blocks: TextBlock[] } }
  | {
      type: "INPAINT_DONE";
      payload: { cleanedImageUrl: string; cleanedImageId: string };
    }
  | { type: "PPT_DONE"; payload: { downloadUrl: string; fileId: string } }
  | { type: "SET_ERROR"; payload: { error: string; detail?: string } }
  | { type: "UPDATE_BLOCKS"; payload: TextBlock[] }
  | { type: "UPDATE_INPAINT_PARAMS"; payload: Partial<Pick<ProcessState, "dilationKernel" | "inpaintRadius" | "inpaintMethod">> }
  | { type: "RESET" };

// ── Reducer ──────────────────────────────────────────────────────────────────

function reducer(state: ProcessState, action: Action): ProcessState {
  switch (action.type) {
    case "SET_STEP":
      return { ...state, step: action.payload, error: null, errorDetail: null };

    case "UPLOAD_DONE":
      return {
        ...state,
        step: "analyzing",
        ...action.payload,
        blocks: [],
        cleanedImageUrl: null,
        downloadUrl: null,
        error: null,
        errorDetail: null,
      };

    case "ANALYZE_DONE":
      return { ...state, step: "inpainting", blocks: action.payload.blocks };

    case "INPAINT_DONE":
      return {
        ...state,
        step: "ready",
        cleanedImageUrl: action.payload.cleanedImageUrl,
        cleanedImageId: action.payload.cleanedImageId,
      };

    case "PPT_DONE":
      return {
        ...state,
        step: "done",
        downloadUrl: action.payload.downloadUrl,
        fileId: action.payload.fileId,
      };

    case "SET_ERROR":
      return {
        ...state,
        step: "error",
        error: action.payload.error,
        errorDetail: action.payload.detail ?? null,
      };

    case "UPDATE_BLOCKS":
      return { ...state, blocks: action.payload };

    case "UPDATE_INPAINT_PARAMS":
      return { ...state, ...action.payload };

    case "RESET":
      return initialState;

    default:
      return state;
  }
}

// ── Hook ─────────────────────────────────────────────────────────────────────

export function useImageProcessor() {
  const [state, dispatch] = useReducer(reducer, initialState);

  /**
   * 1단계: 이미지 업로드 → 2단계: OCR 분석 → 3단계: 인페인팅 자동 실행
   */
  const processImage = useCallback(
    async (file: File) => {
      dispatch({ type: "SET_STEP", payload: "uploading" });

      try {
        // Step 1: Upload
        const uploadRes = await uploadImage(file);
        dispatch({
          type: "UPLOAD_DONE",
          payload: {
            imageId: uploadRes.image_id,
            imageUrl: uploadRes.image_url,
            imageWidth: uploadRes.width,
            imageHeight: uploadRes.height,
          },
        });

        // Step 2: Analyze
        const analyzeRes = await analyzeImage(uploadRes.image_id);
        dispatch({ type: "ANALYZE_DONE", payload: { blocks: analyzeRes.blocks } });

        // Step 3: Inpaint
        const inpaintRes = await inpaintText(
          uploadRes.image_id,
          analyzeRes.blocks,
          state.dilationKernel,
          state.inpaintRadius,
          state.inpaintMethod
        );
        dispatch({
          type: "INPAINT_DONE",
          payload: {
            cleanedImageUrl: inpaintRes.cleaned_image_url,
            cleanedImageId: inpaintRes.cleaned_image_id,
          },
        });
      } catch (err) {
        dispatch({
          type: "SET_ERROR",
          payload: {
            error: extractErrorMessage(err),
            detail: "이미지 처리 파이프라인에서 오류가 발생했습니다.",
          },
        });
      }
    },
    [state.dilationKernel, state.inpaintRadius, state.inpaintMethod]
  );

  /**
   * 인페인팅만 재실행 (파라미터 변경 후 재처리)
   */
  const rerunInpaint = useCallback(async () => {
    if (!state.imageId) return;
    dispatch({ type: "SET_STEP", payload: "inpainting" });
    try {
      const res = await inpaintText(
        state.imageId,
        state.blocks,
        state.dilationKernel,
        state.inpaintRadius,
        state.inpaintMethod
      );
      dispatch({
        type: "INPAINT_DONE",
        payload: {
          cleanedImageUrl: res.cleaned_image_url,
          cleanedImageId: res.cleaned_image_id,
        },
      });
    } catch (err) {
      dispatch({
        type: "SET_ERROR",
        payload: { error: extractErrorMessage(err) },
      });
    }
  }, [state.imageId, state.blocks, state.dilationKernel, state.inpaintRadius, state.inpaintMethod]);

  /**
   * PPT 생성
   */
  const generatePPTFile = useCallback(async () => {
    if (!state.imageId || !state.cleanedImageId) return;
    dispatch({ type: "SET_STEP", payload: "generating" });
    try {
      const res = await generatePPT(
        state.imageId,
        state.cleanedImageId,
        state.blocks,
        state.imageWidth,
        state.imageHeight
      );
      dispatch({
        type: "PPT_DONE",
        payload: { downloadUrl: res.download_url, fileId: res.file_id },
      });
    } catch (err) {
      dispatch({
        type: "SET_ERROR",
        payload: { error: extractErrorMessage(err) },
      });
    }
  }, [state.imageId, state.cleanedImageId, state.blocks, state.imageWidth, state.imageHeight]);

  const updateBlocks = useCallback((blocks: TextBlock[]) => {
    dispatch({ type: "UPDATE_BLOCKS", payload: blocks });
  }, []);

  const updateInpaintParams = useCallback(
    (params: Partial<Pick<ProcessState, "dilationKernel" | "inpaintRadius" | "inpaintMethod">>) => {
      dispatch({ type: "UPDATE_INPAINT_PARAMS", payload: params });
    },
    []
  );

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return {
    state,
    processImage,
    rerunInpaint,
    generatePPTFile,
    updateBlocks,
    updateInpaintParams,
    reset,
  };
}
