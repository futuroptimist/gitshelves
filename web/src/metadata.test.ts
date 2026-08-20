import { describe, expect, it } from "vitest";
import { parseMetadata } from "./metadata";
import { SAMPLE } from "./model";
const payload = JSON.stringify({
  username: "octocat",
  monthly_contributions: SAMPLE.months,
});
describe("metadata", () => {
  it("accepts current metadata", () =>
    expect(parseMetadata(payload).months).toHaveLength(12));
  it("accepts a run summary", () =>
    expect(
      parseMetadata(
        JSON.stringify({ outputs: [{ monthly_contributions: SAMPLE.months }] }),
      ).months,
    ).toHaveLength(12));
  it.each(["", "{", JSON.stringify({ monthly_contributions: [] })])(
    "rejects malformed or partial %s",
    (value) => expect(() => parseMetadata(value)).toThrow(),
  );
  it("rejects duplicate months", () =>
    expect(() =>
      parseMetadata(
        JSON.stringify({
          monthly_contributions: Array(12).fill(SAMPLE.months[0]),
        }),
      ),
    ).toThrow(/Duplicate/));
});
