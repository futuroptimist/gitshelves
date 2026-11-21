import { blocksForContributions } from "./domain";

export const DAY_COUNT = 30;
export const DAY_COLUMNS = 6;
const DAY_MS = 86_400_000;

export type GithubActivity = {
  username: string;
  start: string;
  counts: number[];
  sampled: number;
  limited: boolean;
};

const loginPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/i;
class SearchError extends Error {}
const SEARCH_TIMEOUT_MS = 12000;

export function normalizeGithubUsername(input: string): string | undefined {
  const username = input.trim();
  return username.length <= 39 && loginPattern.test(username)
    ? username.toLowerCase()
    : undefined;
}

export function parseActivity(
  value: unknown,
  username: string,
): GithubActivity {
  if (!value || typeof value !== "object")
    throw new SearchError("GitHub returned an unexpected response.");
  const {
    username: login,
    start,
    counts,
    sampled,
    limited,
  } = value as Partial<GithubActivity>;
  if (
    login !== username ||
    typeof start !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(start) ||
    !Number.isFinite(Date.parse(start)) ||
    new Date(start).toISOString().slice(0, 10) !== start ||
    !Array.isArray(counts) ||
    counts.length !== DAY_COUNT ||
    counts.some((count) => !Number.isSafeInteger(count) || count < 0) ||
    typeof sampled !== "number" ||
    !Number.isSafeInteger(sampled) ||
    sampled < 0 ||
    sampled > 100 ||
    counts.reduce((sum, count) => sum + count, 0) !== sampled ||
    typeof limited !== "boolean"
  )
    throw new SearchError("GitHub returned an unexpected response.");
  return { username, start, counts, sampled, limited };
}

export type ActivityDay = {
  date: string;
  commits: number;
  blocks: number;
  x: number;
  y: number;
};

export function activityDays(activity: GithubActivity): ActivityDay[] {
  const beginning = Date.parse(activity.start);
  return activity.counts.map((commits, index) => ({
    date: new Date(beginning + index * DAY_MS).toISOString().slice(0, 10),
    commits,
    blocks: blocksForContributions(commits),
    x: (index % DAY_COLUMNS) * 42,
    y: Math.floor(index / DAY_COLUMNS) * 42,
  }));
}

export function bindGithubSearch(
  form: HTMLFormElement,
  input: HTMLInputElement,
  output: HTMLOutputElement,
  show: (activity: GithubActivity) => void,
  fetchActivity = globalThis.fetch.bind(globalThis),
  onSearch = () => {},
): { cancel: () => void } {
  let active: AbortController | undefined;
  const report = (message: string, error = false) => {
    output.textContent = message;
    output.classList.toggle("error", error);
  };
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    void search();
  });
  input.addEventListener("input", () => input.removeAttribute("aria-invalid"));

  async function search() {
    active?.abort();
    active = undefined;
    const username = normalizeGithubUsername(input.value);
    if (!username) {
      input.setAttribute("aria-invalid", "true");
      report("Enter a valid GitHub username.", true);
      input.focus();
      return;
    }

    input.removeAttribute("aria-invalid");
    onSearch();
    const controller = new AbortController();
    active = controller;
    let timedOut = false;
    report(
      `Looking up @${username}. The current shelf stays visible while loading.`,
    );
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, SEARCH_TIMEOUT_MS);
    try {
      const response = await fetchActivity(
        `/api/github-activity?username=${encodeURIComponent(username)}`,
        {
          signal: controller.signal,
          headers: { Accept: "application/json" },
          credentials: "omit",
          redirect: "error",
          cache: "no-store",
        },
      );
      if (active !== controller) return;
      const json = response.headers
        .get("content-type")
        ?.toLowerCase()
        .startsWith("application/json");
      if (response.status === 429)
        throw new SearchError("GitHub search is busy. Try again in a minute.");
      if (response.status === 422 && json)
        throw new SearchError(
          "GitHub couldn’t search that username. Check the spelling or try again.",
        );
      if (!json && (response.status === 404 || response.ok))
        throw new SearchError(
          "Live GitHub search isn’t available on this static preview.",
        );
      if (!response.ok)
        throw new SearchError("GitHub search is unavailable. Try again.");
      const result = parseActivity(await response.json(), username);
      if (active !== controller) return;
      if (timedOut)
        throw new SearchError("GitHub search timed out. Try again.");

      show(result);
      const { sampled, limited } = result;
      if (!sampled) {
        report(
          limited
            ? `GitHub’s limited response included no usable public commits for @${username}. The shelf is empty.`
            : `No indexed public commits found for @${username} in the last 30 UTC days. The shelf is empty.`,
        );
        return;
      }
      const commits = sampled === 1 ? "commit" : "commits";
      report(
        `Showing ${sampled} ${limited ? "sampled " : ""}public ${commits} for @${username} over the last 30 UTC days.`,
      );
    } catch (error) {
      if (active !== controller) return;
      const fallback = "GitHub search is unavailable. Try again.";
      const safeError = error instanceof SearchError ? error.message : fallback;
      report(
        `${timedOut ? "GitHub search timed out. Try again." : safeError} The previous shelf is unchanged.`,
        true,
      );
    } finally {
      clearTimeout(timeout);
      if (active === controller) active = undefined;
    }
  }
  return {
    cancel() {
      active?.abort();
      active = undefined;
      input.removeAttribute("aria-invalid");
      report("");
    },
  };
}
