// @vitest-environment jsdom

import { afterEach, expect, it, vi } from "vitest";

const { show, showActivity } = vi.hoisted(() => ({
  show: vi.fn(),
  showActivity: vi.fn(),
}));
vi.mock("../src/files", async (original) => ({
  ...(await original<typeof import("../src/files")>()),
  readStlFiles: async () => [
    {
      name: "local_color1.stl",
      type: "contribution",
      colorGroup: 1,
      bytes: new Uint8Array(),
    },
  ],
}));
vi.mock("../src/scene", () => ({
  ProductScene: class {
    show = show;
    showActivity = showActivity;
  },
  analyzeBundle: () => ({ exact: false, proxyContributionGroups: [] }),
}));

const data = (username: string, count: number) => ({
  username,
  start: "2026-10-22",
  counts: [...Array(29).fill(0), count],
  sampled: count,
  limited: false,
});
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
afterEach(() => vi.unstubAllGlobals());

it("feeds thirty public daily counts to the real landing draw path; avoids stale and unsolicited reads", async () => {
  document.body.innerHTML = '<div id="app"></div>';
  let stale: ((value: Response) => void) | undefined;
  const fetchActivity = vi.fn((url: string): Promise<Response> => {
    if (url.startsWith("/models/"))
      return Promise.resolve(new Response(null, { status: 404 }));
    if (url.endsWith("futuroptimist"))
      return Promise.resolve(json(data("futuroptimist", 24)));
    if (url.endsWith("older"))
      return new Promise((resolve) => (stale = resolve));
    if (url.endsWith("newer")) return Promise.resolve(json(data("newer", 3)));
    if (url.endsWith("busy"))
      return Promise.resolve(json({ error: "rate_limited" }, 429));
    if (url.endsWith("empty")) return Promise.resolve(json(data("empty", 0)));
    if (url.endsWith("static"))
      return Promise.resolve(new Response("<!doctype html>"));
    throw new Error("unexpected");
  });
  vi.stubGlobal("fetch", fetchActivity);
  await import("../src/main");
  const form = document.querySelector("#github-search")!;
  const input = document.querySelector<HTMLInputElement>("#github-username")!;
  const status = document.querySelector("#github-search-status")!;
  const submit = (username: string) => {
    input.value = username;
    form.dispatchEvent(new Event("submit", { cancelable: true }));
  };
  const source = () => document.querySelector("#sample")!.textContent;
  const sceneDataset = () =>
    showActivity.mock.calls.at(-1)![0] as { date: string; blocks: number }[];

  expect(
    fetchActivity.mock.calls.every(([url]) => url.startsWith("/models/")),
  ).toBe(true);
  submit("invalid/query");
  expect(input.getAttribute("aria-invalid")).toBe("true");
  expect(
    fetchActivity.mock.calls.every(([url]) => url.startsWith("/models/")),
  ).toBe(true);
  document.querySelector("#stls")!.dispatchEvent(new Event("change"));
  await vi.waitFor(() =>
    expect(show.mock.calls.at(-1)![2]).toEqual([
      expect.objectContaining({ type: "contribution" }),
    ]),
  );
  submit(" Futuroptimist ");
  await vi.waitFor(() => expect(source()).toContain("@futuroptimist"));
  expect(sceneDataset()).toHaveLength(30);
  expect(sceneDataset().at(-1)).toMatchObject({
    date: "2026-11-20",
    blocks: 2,
  });
  expect(document.querySelector<HTMLButtonElement>("#manifest")!.disabled).toBe(
    true,
  );
  expect(document.querySelector<HTMLElement>("#print-plan")!.hidden).toBe(true);
  expect(show.mock.calls.at(-1)![2]).toEqual([
    expect.objectContaining({ type: "contribution" }),
  ]);
  expect(document.querySelector("#file-list")!.textContent).toContain(
    "local_color1.stl",
  );
  expect(document.querySelector("#days")!.textContent).toContain("24");
  expect(document.querySelector("#activity-caption")!.textContent).toContain(
    "2026-10-22 through 2026-11-20",
  );

  submit("older");
  expect(status.textContent).toContain("Looking up @older");
  submit("newer");
  await vi.waitFor(() => expect(source()).toContain("@newer"));
  stale!(json(data("older", 80)));
  await new Promise((resolve) => setTimeout(resolve, 0));
  expect(source()).toContain("@newer");
  expect(sceneDataset().at(-1)!.blocks).toBe(1);

  submit("busy");
  await vi.waitFor(() => expect(status.textContent).toContain("busy"));
  expect(source()).toContain("@newer");
  submit("static");
  await vi.waitFor(() =>
    expect(status.textContent).toContain("static preview"),
  );
  expect(source()).toContain("@newer");

  submit("empty");
  await vi.waitFor(() =>
    expect(status.textContent).toContain("shelf is empty"),
  );
  expect(source()).toContain("@empty");
  expect(sceneDataset().every((month) => month.blocks === 0)).toBe(true);

  document.querySelector<HTMLButtonElement>("#clear-activity")!.click();
  expect(source()).toBe("Synthetic sample");
  expect(input.value).toBe("");
  expect(document.querySelector("#days")!.textContent).toBe("");
  expect(document.activeElement).toBe(input);
  expect(document.querySelector<HTMLButtonElement>("#manifest")!.disabled).toBe(
    false,
  );
  expect(document.querySelector<HTMLElement>("#print-plan")!.hidden).toBe(
    false,
  );

  // Switching back to local metadata restores its imported STL, rather than
  // destroying it when the GitHub dataset was selected.
  const metadata = document.querySelector("#metadata")!;
  Object.defineProperty(metadata, "files", {
    value: [
      {
        name: "local.json",
        text: async () =>
          JSON.stringify({
            schemaVersion: "gitshelves.web/v1",
            year: 2026,
            months: Array.from({ length: 12 }, () => ({ contributions: 1 })),
          }),
      },
    ],
  });
  metadata.dispatchEvent(new Event("change"));
  await vi.waitFor(() => expect(source()).toBe("Local metadata"));
  expect(show.mock.calls.at(-1)![2]).toEqual([
    expect.objectContaining({ type: "contribution" }),
  ]);
});
