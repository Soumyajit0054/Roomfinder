import React from "react";
import Svg, { Path } from "react-native-svg";
import { IconName, ICON_PATHS } from "./icons.generated";

/** Bootstrap Icons rendered as SVG, matching the web app's `bi bi-*` glyphs. */
export default function Icon({ name, size = 18, color = "#1f2933" }: { name: IconName; size?: number; color?: string }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 16 16" fill={color}>
      {ICON_PATHS[name].map((p, i) => (
        <Path key={i} d={p.d} fillRule={p.evenodd ? "evenodd" : undefined} clipRule={p.evenodd ? "evenodd" : undefined} />
      ))}
    </Svg>
  );
}

export type { IconName };
