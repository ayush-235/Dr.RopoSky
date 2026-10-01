import React from "react";
import { SCORING_PILLARS } from "@/lib/constants";
import { Shield, Bug, Sparkles, Layers, Cpu, CheckCircle } from "lucide-react";

export const PipelineShowcase: React.FC = () => {
  const pillarIcons: Record<string, any> = {
    security: Shield,
    reliability: Bug,
    code_quality: CheckCircle,
    performance: Cpu,
    architecture: Layers,
    completeness: Sparkles,
  };

  return (
    <section className="w-full py-16 border-t border-border bg-surface/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-xl sm:text-2xl font-bold text-text-primary font-mono">
            DETERMINISTIC 6-PILLAR AUDIT ENGINE
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-text-secondary font-mono">
            Every repository is audited against mathematically verified engineering standards. Scores are reproducible and immutable.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {SCORING_PILLARS.map((pillar) => {
            const Icon = pillarIcons[pillar.key] || Shield;
            return (
              <div
                key={pillar.key}
                className="p-5 rounded-xl border border-border bg-surface/60 hover:bg-surface hover:border-border-active transition-all group"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg border border-border bg-surface-elevated flex items-center justify-center text-primary group-hover:border-primary/40 transition-colors">
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-surface-elevated border border-border text-text-muted">
                    {pillar.weight} Weight
                  </span>
                </div>
                <h3 className="text-sm font-bold font-mono text-text-primary group-hover:text-primary transition-colors">
                  {pillar.name}
                </h3>
                <p className="mt-1.5 text-xs text-text-secondary font-mono leading-relaxed">
                  {pillar.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
