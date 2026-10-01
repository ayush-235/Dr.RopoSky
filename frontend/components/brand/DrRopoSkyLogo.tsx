"use client";

import React from "react";

export interface DrRopoSkyLogoProps {
  variant?: "full" | "compact" | "icon";
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  showSubtitle?: boolean;
  subtitle?: string;
  animated?: boolean;
}

/**
 * Dr.RopoSky Shield Emblem Vector Icon
 * Faithfully reproduces the approved cybersecurity shield, D/R monogram,
 * 4-point diagnostic scanning core star, and electric cyan-to-violet gradient accent.
 */
export const DrRopoSkyEmblem: React.FC<{
  size?: number | string;
  className?: string;
  animated?: boolean;
}> = ({ size = 32, className = "", animated = true }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 ${className}`}
      aria-label="Dr.RopoSky Shield Emblem"
    >
      <defs>
        {/* Shield Outer Stroke Gradient */}
        <linearGradient id="dr-shield-border" x1="10" y1="10" x2="90" y2="95" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="30%" stopColor="#00E5FF" />
          <stop offset="70%" stopColor="#0284C7" />
          <stop offset="100%" stopColor="#818CF8" />
        </linearGradient>

        {/* Shield Inner Dark Fill */}
        <linearGradient id="dr-shield-bg" x1="50" y1="12" x2="50" y2="92" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0B132B" />
          <stop offset="60%" stopColor="#070D1F" />
          <stop offset="100%" stopColor="#040711" />
        </linearGradient>

        {/* Monogram Cyan Gradient (Upper & Left Body) */}
        <linearGradient id="dr-mono-cyan" x1="22" y1="26" x2="72" y2="56" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#E0F2FE" />
          <stop offset="25%" stopColor="#38BDF8" />
          <stop offset="100%" stopColor="#0284C7" />
        </linearGradient>

        {/* Monogram Dynamic Violet/Purple Gradient (Lower Right Leg) */}
        <linearGradient id="dr-leg-violet" x1="45" y1="52" x2="88" y2="88" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="35%" stopColor="#6366F1" />
          <stop offset="75%" stopColor="#A855F7" />
          <stop offset="100%" stopColor="#C084FC" />
        </linearGradient>

        {/* Core Star Radial Glow */}
        <radialGradient id="dr-star-glow" cx="48" cy="42" r="14" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity="1" />
          <stop offset="35%" stopColor="#38BDF8" stopOpacity="0.8" />
          <stop offset="70%" stopColor="#00E5FF" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#00E5FF" stopOpacity="0" />
        </radialGradient>

        {/* Outer Glow Filter */}
        <filter id="dr-glow" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Background Glow Aura */}
      <circle cx="50" cy="50" r="38" fill="#00E5FF" opacity="0.08" filter="url(#dr-glow)" />

      {/* Outer Shield Path */}
      <path
        d="M50 10 L88 25 C88 56 74 80 50 94 C26 80 12 56 12 25 Z"
        fill="url(#dr-shield-bg)"
        stroke="url(#dr-shield-border)"
        strokeWidth="3.5"
        strokeLinejoin="round"
      />

      {/* Inner Shield Bevel Line */}
      <path
        d="M50 15 L82 28 C82 53 70 74 50 87 C30 74 18 53 18 28 Z"
        stroke="#00E5FF"
        strokeWidth="1"
        strokeOpacity="0.3"
        strokeLinejoin="round"
        fill="none"
      />

      {/* Monogram: D/R Integrated Architecture */}
      <g>
        {/* Left Vertical Spine / D-Frame */}
        <path
          d="M26 27 H37 V75 H26 Z"
          fill="url(#dr-mono-cyan)"
        />

        {/* Lower Left Connecting Base */}
        <path
          d="M26 64 L42 75 H26 Z"
          fill="#0284C7"
          opacity="0.8"
        />

        {/* Upper Loop of the Monogram (R & D Arch) */}
        <path
          d="M37 27 H62 C71 27 77 33 77 42 C77 51 71 57 62 57 H37 V27 Z M48 37 V47 H59 C63 47 66 45 66 42 C66 39 63 37 59 37 Z"
          fill="url(#dr-mono-cyan)"
        />

        {/* Dynamic Slanted Leg (Deep Violet / Electric Blue Gradient) */}
        <path
          d="M48 53 L74 82 H88 L60 53 Z"
          fill="url(#dr-leg-violet)"
          filter="url(#dr-glow)"
        />

        {/* Lower Facet Accent on Leg */}
        <path
          d="M60 53 L74 82 H80 L66 53 Z"
          fill="#E0E7FF"
          opacity="0.3"
        />

        {/* 4-Point Diagnostic Scanning Core Star */}
        <g transform="translate(48, 42)">
          {/* Radial Glow Halo */}
          <circle cx="0" cy="0" r="8" fill="url(#dr-star-glow)" />

          {/* Star Shape */}
          <path
            d="M0 -6 Q0.8 -0.8 6 0 Q0.8 0.8 0 6 Q-0.8 0.8 -6 0 Q-0.8 -0.8 0 -6 Z"
            fill="#FFFFFF"
            className={animated ? "animate-pulse" : ""}
          />
          {/* Center Point */}
          <circle cx="0" cy="0" r="1" fill="#00E5FF" />
        </g>
      </g>
    </svg>
  );
};

export const DrRopoSkyLogo: React.FC<DrRopoSkyLogoProps> = ({
  variant = "compact",
  size = "md",
  className = "",
  showSubtitle = true,
  subtitle = "AI-POWERED FULL-PROJECT SOFTWARE AUDITOR",
  animated = true,
}) => {
  const pixelSizeMap = {
    xs: 20,
    sm: 26,
    md: 34,
    lg: 44,
    xl: 56,
  };

  const wordmarkSizeMap = {
    xs: "text-xs tracking-tight",
    sm: "text-sm tracking-tight",
    md: "text-base sm:text-lg tracking-tight",
    lg: "text-xl sm:text-2xl tracking-tight",
    xl: "text-2xl sm:text-3xl tracking-tight",
  };

  const subtitleSizeMap = {
    xs: "text-[7px]",
    sm: "text-[8px]",
    md: "text-[9px] sm:text-[10px]",
    lg: "text-[10px] sm:text-[11px]",
    xl: "text-[11px] sm:text-[12px]",
  };

  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      {/* Approved Shield Emblem */}
      <DrRopoSkyEmblem
        size={pixelSizeMap[size]}
        animated={animated}
        className="transition-transform duration-200 group-hover:scale-105"
      />

      {/* Wordmark & Subtitle */}
      {variant !== "icon" && (
        <div className="flex flex-col justify-center leading-none">
          <div className={`font-mono font-extrabold flex items-baseline ${wordmarkSizeMap[size]}`}>
            <span className="text-white">Dr</span>
            <span className="text-cyan-400 font-black">.</span>
            <span className="text-white ml-0.5">Ropo</span>
            <span className="bg-gradient-to-r from-cyan-400 via-sky-400 to-cyan-300 bg-clip-text text-transparent font-black ml-0.5">
              Sky
            </span>
          </div>

          {variant === "full" && showSubtitle && (
            <span
              className={`font-mono font-medium text-text-muted mt-1 uppercase tracking-widest ${subtitleSizeMap[size]}`}
            >
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
