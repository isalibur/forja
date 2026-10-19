import React from "react";
import { Composition } from "remotion";
import { BenchmarkComposition } from "./Composition";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="benchmark-1080p"
        component={BenchmarkComposition}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "DocForja · Benchmark M0",
          resolution: "1080p Full HD",
        }}
      />
      <Composition
        id="benchmark-1440p"
        component={BenchmarkComposition}
        durationInFrames={300}
        fps={30}
        width={2560}
        height={1440}
        defaultProps={{
          title: "DocForja · Benchmark M0",
          resolution: "1440p Quad HD",
        }}
      />
    </>
  );
};


