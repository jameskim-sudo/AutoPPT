"use client";

import React from "react";
import clsx from "clsx";
import { CheckCircle, Loader2, Circle, XCircle } from "lucide-react";
import type { ProcessStep } from "@/types";

interface Step {
  key: ProcessStep[];
  label: string;
}

const STEPS: Step[] = [
  { key: ["uploading"], label: "업로드" },
  { key: ["analyzing"], label: "OCR 분석" },
  { key: ["inpainting"], label: "텍스트 제거" },
  { key: ["ready", "generating", "done"], label: "편집 / 생성" },
  { key: ["done"], label: "완료" },
];

type StepStatus = "done" | "active" | "pending" | "error";

function getStatus(step: Step, current: ProcessStep): StepStatus {
  if (current === "error") return "error";
  const allKeys: ProcessStep[] = STEPS.flatMap((s) => s.key);
  const currentIdx = allKeys.indexOf(current);
  const stepIdx = Math.max(...step.key.map((k) => allKeys.indexOf(k)));

  if (step.key.includes(current)) return "active";
  if (stepIdx < currentIdx) return "done";
  return "pending";
}

interface Props {
  currentStep: ProcessStep;
}

export default function ProgressStepper({ currentStep }: Props) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {STEPS.map((step, i) => {
        const status = getStatus(step, currentStep);
        return (
          <React.Fragment key={i}>
            <div className="flex items-center gap-1.5">
              {status === "done" && (
                <CheckCircle className="w-5 h-5 text-green-500" />
              )}
              {status === "active" && (
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
              )}
              {status === "pending" && (
                <Circle className="w-5 h-5 text-gray-300" />
              )}
              {status === "error" && (
                <XCircle className="w-5 h-5 text-red-400" />
              )}
              <span
                className={clsx(
                  "text-sm font-medium",
                  status === "done" && "text-green-600",
                  status === "active" && "text-blue-600",
                  status === "pending" && "text-gray-400",
                  status === "error" && "text-red-400"
                )}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className="w-6 h-px bg-gray-200 hidden sm:block" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
