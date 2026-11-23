// Reviewer-facing names for categories, verdicts and decisions.

import type { Category, DecisionKind, Verdict } from "./api";

/** The app's name, as in the repository. */
export const APP_NAME = "Translation assumption flags";

/** Category names in the reviewer's words. */
export const CATEGORY_NAMES: Record<Category, string> = {
    numeric: "Numeric types",
    input: "Input parsing",
    output: "Output format",
    api: "Library behaviour",
    division: "Division and modulo",
    errors: "Exceptions",
};

/** Gemini's verdicts in the reviewer's words. */
export const VERDICT_NAMES: Record<Verdict, string> = {
    mismatch: "Behaves differently",
    unclear: "Can't tell",
    handled: "Handled",
};

/** One-line meaning of each verdict, for the key above the code. */
export const VERDICT_MEANINGS: Record<Verdict, string> = {
    mismatch: "the Java gives a different result for some input",
    unclear: "Gemini could not decide",
    handled: "the Java deals with the difference",
};

/** The symbol that marks each verdict, in the code and in the flag list. */
export const VERDICT_MARKS: Record<Verdict, string> = {
    mismatch: "!",
    unclear: "?",
    handled: "–",
};

/** Verdicts from most to least serious. */
export const VERDICTS: Verdict[] = ["mismatch", "unclear", "handled"];

/** Logged decisions, as shown once made. */
export const DECISION_NAMES: Record<DecisionKind, string> = {
    confirmed: "Confirmed bug",
    intended: "Intended",
    dismissed: "Dismissed",
};

/** The action buttons, with the key that triggers each. */
export const DECISION_ACTIONS: {
    kind: DecisionKind;
    label: string;
    key: string;
}[] = [
    { kind: "confirmed", label: "Confirm bug", key: "1" },
    { kind: "intended", label: "Mark intended", key: "2" },
    { kind: "dismissed", label: "Dismiss", key: "3" },
];
