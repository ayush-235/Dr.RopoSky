import React from "react";
import { KeyRound, ShieldAlert, Package, Lock, EyeOff } from "lucide-react";

export const SecuritySection: React.FC = () => {
  const securityFeatures = [
    {
      icon: KeyRound,
      title: "Secret Exposure Defense",
      description: "Detects AWS tokens, Stripe keys, GitHub credentials, JWTs, and private keys with automatic redaction.",
      color: "text-red-400",
    },
    {
      icon: ShieldAlert,
      title: "Injection & AST Flaws",
      description: "Static AST inspection traps SQL injection, command execution, and unsafe deserialization.",
      color: "text-amber-400",
    },
    {
      icon: Package,
      title: "Dependency Auditing",
      description: "Scans lockfiles against known vulnerability databases without executing package install scripts.",
      color: "text-cyan-400",
    },
    {
      icon: EyeOff,
      title: "Zero-Leak Redaction",
      description: "All sensitive credentials in findings and code evidence are redacted before reaching AI or UI.",
      color: "text-emerald-400",
    },
  ];

  return (
    <section className="w-full py-16 border-t border-border bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-red-500/20 bg-red-500/10 text-xs font-mono text-red-400 mb-3">
            <Lock className="w-3.5 h-3.5" />
            <span>CYBERSECURITY COMMAND</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-text-primary font-mono">
            ENTERPRISE-GRADE SECURITY AUDIT
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-text-secondary font-mono">
            Untrusted code is analyzed purely via static AST, regex scanners, and sandboxed metadata inspectors.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {securityFeatures.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <div
                key={idx}
                className="p-5 rounded-xl border border-border bg-surface/40 hover:bg-surface transition-all flex flex-col justify-between"
              >
                <div>
                  <div className={`w-8 h-8 rounded-lg border border-border bg-surface-elevated flex items-center justify-center mb-3 ${feat.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-bold font-mono text-text-primary">
                    {feat.title}
                  </h3>
                  <p className="mt-1.5 text-xs text-text-secondary font-mono leading-relaxed">
                    {feat.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
