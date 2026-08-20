import type { Month } from "./domain";
export function moduleTransform(
  month: Month,
  level: number,
  exploded: boolean,
) {
  const gap = exploded ? 10 : 0;
  return {
    x: month.x + 21,
    y: month.y + 21,
    z: 6 + level * (7 + gap) + (exploded ? 8 : 0),
  };
}
export function paletteVisible(group: number, visible: Set<number>) {
  return group === 0 || visible.has(group);
}
