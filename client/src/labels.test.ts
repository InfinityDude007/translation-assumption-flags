// Tests for the reviewer-facing labels.

import { describe, expect, it } from "vitest";
import { percent } from "./labels";

describe("percent", () => {
    it("shows small probabilities to one decimal, without a trailing .0", () => {
        expect(percent(0.034)).toBe("3.4%");
        expect(percent(0.05)).toBe("5%");
    });

    it("rounds from 10% up, and floors tiny values at <0.1%", () => {
        expect(percent(0.876)).toBe("88%");
        expect(percent(0.0004)).toBe("<0.1%");
    });
});
