import React from "react";
import { Audio } from "@remotion/media";
import { AbsoluteFill, Sequence, staticFile } from "remotion";
import { ShortVertical } from "./ShortVertical";
import type { PropsShortTimelineSchema } from "../schemas/shorts";

export const ShortTimeline: React.FC<PropsShortTimelineSchema> = ({ audio, cenas }) => (
  <AbsoluteFill>
    {audio ? <Audio src={staticFile(audio)} /> : null}
    {cenas.map((cena) => (
      <Sequence
        key={cena.id}
        name={cena.id}
        from={cena.inicio_frame}
        durationInFrames={cena.duracao_frames}
      >
        <ShortVertical {...cena.props} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
