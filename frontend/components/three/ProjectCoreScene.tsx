"use client";

import React, { useRef, useMemo, useState, useEffect } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { SceneState } from "@/types/report";
import { CoreFallback } from "./CoreFallback";

interface CoreSceneProps {
  state?: SceneState;
}

function AnalysisCoreMesh({ state = "idle", reducedMotion = false }: { state: SceneState; reducedMotion: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const coreRef = useRef<THREE.Mesh>(null);
  const outerRingRef = useRef<THREE.LineSegments>(null);

  // Colors based on state
  const coreColor = useMemo(() => {
    switch (state) {
      case "scanning":
        return new THREE.Color("#00d2ff");
      case "issues":
        return new THREE.Color("#ef4444");
      case "completed":
        return new THREE.Color("#10b981");
      default:
        return new THREE.Color("#a855f7");
    }
  }, [state]);

  // Generate deterministic project nodes (representing AST, files, deps, security)
  const nodes = useMemo(() => {
    const items = [];
    const count = 16;
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(-1 + (2 * i) / count);
      const theta = Math.sqrt(count * Math.PI) * phi;
      const radius = 2.2 + (i % 3) * 0.4;
      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);

      const isSecurity = i % 4 === 0;
      const isDep = i % 4 === 1;

      items.push({
        position: [x, y, z] as [number, number, number],
        color: isSecurity ? "#ef4444" : isDep ? "#a855f7" : "#00d2ff",
        size: isSecurity ? 0.09 : 0.06,
      });
    }
    return items;
  }, []);

  // Frame animation loop
  useFrame((_, delta) => {
    if (reducedMotion || !groupRef.current) return;

    const speed = state === "scanning" ? 1.8 : 0.4;
    groupRef.current.rotation.y += delta * 0.3 * speed;
    groupRef.current.rotation.x += delta * 0.1 * speed;

    if (coreRef.current) {
      const scaleBase = state === "scanning" ? 1 + Math.sin(Date.now() * 0.005) * 0.1 : 1;
      coreRef.current.scale.set(scaleBase, scaleBase, scaleBase);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Central Analysis Core */}
      <mesh ref={coreRef}>
        <icosahedronGeometry args={[0.9, 1]} />
        <meshStandardMaterial
          color={coreColor}
          wireframe
          transparent
          opacity={0.85}
          emissive={coreColor}
          emissiveIntensity={state === "scanning" ? 0.6 : 0.2}
        />
      </mesh>

      {/* Inner Dense Core */}
      <mesh>
        <sphereGeometry args={[0.4, 16, 16]} />
        <meshBasicMaterial color={coreColor} />
      </mesh>

      {/* Outer Orbital Rings */}
      <mesh rotation={[Math.PI / 4, 0, 0]}>
        <ringGeometry args={[2.8, 2.84, 64]} />
        <meshBasicMaterial color="#26282e" side={THREE.DoubleSide} />
      </mesh>
      <mesh rotation={[-Math.PI / 4, Math.PI / 3, 0]}>
        <ringGeometry args={[3.2, 3.23, 64]} />
        <meshBasicMaterial color="#1c1d22" side={THREE.DoubleSide} />
      </mesh>

      {/* Surrounding Connected Nodes */}
      {nodes.map((node, i) => (
        <group key={i} position={node.position}>
          <mesh>
            <sphereGeometry args={[node.size, 12, 12]} />
            <meshBasicMaterial color={state === "issues" && i % 4 === 0 ? "#ef4444" : node.color} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

export const ProjectCoreScene: React.FC<CoreSceneProps> = ({ state = "idle" }) => {
  const [hasWebGL, setHasWebGL] = useState<boolean | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    // Check prefers-reduced-motion
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);

    // Check WebGL availability
    try {
      const canvas = document.createElement("canvas");
      const gl =
        canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      setHasWebGL(Boolean(gl));
    } catch {
      setHasWebGL(false);
    }

    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  if (hasWebGL === false) {
    return <CoreFallback state={state} />;
  }

  return (
    <div className="relative w-full h-full select-none flex items-center justify-center overflow-hidden">
      <Canvas
        camera={{ position: [0, 0, 6], fov: 45 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={1.2} />
        <AnalysisCoreMesh state={state} reducedMotion={reducedMotion} />
      </Canvas>
    </div>
  );
};
