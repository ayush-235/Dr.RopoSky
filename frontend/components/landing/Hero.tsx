"use client";

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { AnalysisInput } from "./AnalysisInput";
import { CoreFallback } from "../three/CoreFallback";
import { SceneState } from "@/types/report";
import { DrRopoSkyEmblem } from "../brand/DrRopoSkyLogo";

// Dynamic import with SSR disabled for Three.js
const ProjectCoreScene = dynamic(
  () =>
    import("../three/ProjectCoreScene").then((mod) => mod.ProjectCoreScene),
  {
    ssr: false,
    loading: () => <CoreFallback state="idle" />,
  }
);

interface HeroProps {
  onAnalyze: (options: { githubUrl?: string; zipFile?: File }) => void;
  isLoading: boolean;
  sceneState: SceneState;
  initialUrl?: string;
}

export const Hero: React.FC<HeroProps> = ({
  onAnalyze,
  isLoading,
  sceneState,
  initialUrl,
}) => {
  const [hasInput, setHasInput] = useState(false);

  const effectiveSceneState: SceneState = isLoading
    ? "scanning"
    : hasInput
    ? "input"
    : sceneState;

  return (
    <section className="relative w-full pt-10 pb-16 px-4 sm:px-6 overflow-hidden">
      {/* Background Subtle Gradient */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl pointer-events-none -z-10" />

      <div className="max-w-5xl mx-auto flex flex-col items-center text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-border bg-surface/80 backdrop-blur text-xs font-mono text-text-secondary mb-6 shadow-sm">
          <DrRopoSkyEmblem size={18} />
          <span>Dr.RopoSky &bull; AI-Powered Full-Project Software Auditor</span>
        </div>

        {/* Headline */}
        <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-text-primary max-w-3xl leading-tight">
          Find what’s wrong with your project.
        </h1>

        <p className="mt-4 text-sm sm:text-base text-text-secondary max-w-2xl font-mono leading-relaxed">
          Dr.RopoSky analyzes your codebase for security, reliability, quality, performance, architecture, and completeness issues — then explains what to fix and tracks your progress after every re-scan.
        </p>

        {/* 3D Project Analysis Core Visualizer */}
        <div className="w-full max-w-md h-64 sm:h-72 my-2 relative flex items-center justify-center">
          <ProjectCoreScene state={effectiveSceneState} />
        </div>

        {/* Input Interface */}
        <div className="w-full mt-2">
          <AnalysisInput
            onAnalyze={onAnalyze}
            isLoading={isLoading}
            onInputChange={setHasInput}
            initialUrl={initialUrl}
          />
        </div>
      </div>
    </section>
  );
};
