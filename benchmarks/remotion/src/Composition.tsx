import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export interface BenchmarkProps {
  title?: string;
  resolution?: string;
}

export const BenchmarkComposition: React.FC<BenchmarkProps> = ({
  title = "DocForja · Benchmark M0",
  resolution = "1080p Full HD",
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Ken Burns zoom effect on background image
  const imageScale = interpolate(frame, [0, 300], [1.0, 1.15]);
  const imageY = interpolate(frame, [0, 300], [0, -20]);

  // Entrance animation for title card
  const entrance = spring({
    frame,
    fps,
    config: {
      damping: 12,
    },
  });

  const cardScale = interpolate(entrance, [0, 1], [0.85, 1]);
  const cardOpacity = interpolate(entrance, [0, 1], [0.4, 1]);

  return (
    <AbsoluteFill style={{ backgroundColor: "#18191c", overflow: "hidden" }}>
      {/* Background image with Ken Burns */}
      <AbsoluteFill
        style={{
          transform: `scale(${imageScale}) translateY(${imageY}px)`,
          transformOrigin: "center center",
        }}
      >
        <Img
          src={staticFile("volcano.png")}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      </AbsoluteFill>

      {/* Dark gradient overlay for contrast */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(180deg, rgba(24, 25, 28, 0.4) 0%, rgba(24, 25, 28, 0.75) 100%)",
        }}
      />

      {/* Animated title card */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          fontFamily: "system-ui, -apple-system, sans-serif",
          color: "#f5f5f7",
        }}
      >
        <div
          style={{
            transform: `scale(${cardScale})`,
            opacity: cardOpacity,
            textAlign: "center",
            padding: "40px 70px",
            borderRadius: 24,
            backgroundColor: "rgba(24, 25, 28, 0.75)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.15)",
            boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
          }}
        >
          <div
            style={{
              fontSize: width > 2000 ? 64 : 48,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              marginBottom: 16,
              color: "#e27d3b",
            }}
          >
            {title}
          </div>
          <div
            style={{
              fontSize: width > 2000 ? 32 : 24,
              color: "#e4e4e7",
              fontWeight: 500,
            }}
          >
            {resolution} · {width}×{height} · 30 fps
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};


