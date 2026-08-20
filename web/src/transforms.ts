import type { MonthData } from "./metadata";
export type AssemblyMode = "assembled" | "exploded";
export const PITCH_MM = 42,
  HEIGHT_UNIT_MM = 7,
  BASE_SEAT_Z_MM = 7;
export function cubeTransform(
  month: MonthData,
  level: number,
  mode: AssemblyMode,
) {
  const gap = mode === "exploded" ? 8 : 0;
  return {
    x: month.x,
    y: month.y,
    z:
      BASE_SEAT_Z_MM +
      level * HEIGHT_UNIT_MM +
      (mode === "exploded" ? (month.month - 1) * 1.5 + level * gap : 0),
  };
}
export function groupVisible(group: number, visible: ReadonlySet<number>) {
  return visible.has(group);
}
export function reducedMotion(query: Pick<MediaQueryList, "matches">): boolean {
  return query.matches;
}
