"use client";

import React, { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, ImageIcon } from "lucide-react";
import clsx from "clsx";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

const ACCEPT = { "image/png": [], "image/jpeg": [], "image/webp": [] };

export default function ImageUpload({ onFile, disabled }: Props) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) onFile(accepted[0]);
    },
    [onFile]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPT,
    maxFiles: 1,
    disabled,
  });

  return (
    <div
      {...getRootProps()}
      className={clsx(
        "flex flex-col items-center justify-center w-full h-52 rounded-xl border-2 border-dashed cursor-pointer transition-colors select-none",
        isDragActive && !isDragReject && "border-blue-500 bg-blue-50",
        isDragReject && "border-red-400 bg-red-50",
        !isDragActive && !isDragReject && "border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <input {...getInputProps()} />
      <UploadCloud
        className={clsx(
          "w-10 h-10 mb-3",
          isDragActive && !isDragReject ? "text-blue-500" : "text-gray-400"
        )}
      />
      {isDragReject ? (
        <p className="text-sm text-red-500 font-medium">PNG / JPG / WEBP 파일만 가능합니다</p>
      ) : isDragActive ? (
        <p className="text-sm text-blue-600 font-medium">여기에 놓으세요!</p>
      ) : (
        <>
          <p className="text-sm text-gray-600 font-medium">
            이미지를 드래그하거나{" "}
            <span className="text-blue-600 underline">클릭해서 선택</span>
          </p>
          <p className="text-xs text-gray-400 mt-1">PNG · JPG · WEBP (최대 20MB)</p>
        </>
      )}
      <ImageIcon className="w-4 h-4 text-gray-300 mt-3" />
    </div>
  );
}
