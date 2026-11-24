// A button beside the key that opens a guide to every mark and label on the page.

import { useRef } from "react";
import {
    DECISION_ACTIONS,
    VERDICT_MARKS,
    VERDICT_MEANINGS,
    VERDICT_NAMES,
    VERDICTS,
} from "../labels";

/** What each decision means, in the order of the buttons. */
const DECISION_MEANINGS: Record<string, string> = {
    confirmed: "the difference is a real bug in the translation.",
    intended:
        "the Java differs on purpose, or the difference cannot matter here.",
    dismissed: "the flag is noise: wrong, or not worth a reviewer's time.",
};

/** The "What do these mean?" button and the guide it opens. */
export function KeyGuide() {
    const dialog = useRef<HTMLDialogElement>(null);

    const open = () => {
        const box = dialog.current;
        if (!box) return;
        if (typeof box.showModal === "function") box.showModal();
        else box.setAttribute("open", "");
    };
    const close = () => {
        const box = dialog.current;
        if (!box) return;
        if (typeof box.close === "function") box.close();
        else box.removeAttribute("open");
    };

    return (
        <>
            <button type="button" className="key-help" onClick={open}>
                What do these mean?
            </button>
            <dialog
                ref={dialog}
                className="guide"
                aria-labelledby="guide-title"
                onClick={(event) => event.target === dialog.current && close()}
            >
                <div className="guide-body">
                    <div className="guide-head">
                        <h2 id="guide-title">How to read this page</h2>
                        <button
                            type="button"
                            className="guide-close"
                            onClick={close}
                        >
                            Close
                        </button>
                    </div>

                    <section>
                        <h3>Line marks</h3>
                        <p>
                            A mark beside a line number shows Gemini's verdict
                            on the flag at that line. Colour means the verdict
                            and nothing else.
                        </p>
                        <ul className="guide-marks">
                            {VERDICTS.map((verdict) => (
                                <li key={verdict} data-verdict={verdict}>
                                    <span className="mark" aria-hidden="true">
                                        {VERDICT_MARKS[verdict]}
                                    </span>
                                    <span>
                                        <strong>
                                            {VERDICT_NAMES[verdict]}
                                        </strong>
                                        : {VERDICT_MEANINGS[verdict]}.
                                    </span>
                                </li>
                            ))}
                        </ul>
                        <p>
                            Lines Gemini says behave differently, or cannot
                            judge, are tinted; handled lines only carry the
                            mark. The open flag's lines are outlined. Click a
                            marked line to open its flag.
                        </p>
                    </section>

                    <section>
                        <h3>The lines between the panes</h3>
                        <p>
                            Each curve joins a flag's Python line to the Java
                            lines Gemini says implement it. The open flag's
                            curve is drawn bold; dashed curves are flags Gemini
                            could not judge.
                        </p>
                    </section>

                    <section>
                        <h3>Where each part of a flag comes from</h3>
                        <dl className="guide-sources">
                            <dt data-source="detector">Detector</dt>
                            <dd>
                                Fixed rules that read the Python and mark
                                constructs that often behave differently in
                                Java, such as <code>//</code> or{" "}
                                <code>input()</code>. It decides where a flag
                                goes and why that construct is risky. It never
                                sees the Java.
                            </dd>
                            <dt data-source="explainer">Explainer</dt>
                            <dd>
                                Gemini reads each site with the Java and gives
                                the verdict, the Java lines, what the
                                translation assumed, and a suggested fix. This
                                is a claim, not a result: it can be wrong in
                                both directions.
                            </dd>
                            <dt data-source="checks">Checks</dt>
                            <dd>
                                The server rejects any answer that names no
                                valid Java line, or that skips a site. Rejected
                                sites are listed under "Dropped by the checks"
                                and are not marked in the code.
                            </dd>
                            <dt data-source="you">You</dt>
                            <dd>
                                Your decision is the final word. It is saved
                                with the run, model and prompt version that
                                produced the flag.
                            </dd>
                        </dl>
                    </section>

                    <section>
                        <h3>Your decisions</h3>
                        <ul>
                            {DECISION_ACTIONS.map(({ kind, label, key }) => (
                                <li key={kind}>
                                    <strong>{label}</strong> (key{" "}
                                    <kbd>{key}</kbd>): {DECISION_MEANINGS[kind]}
                                </li>
                            ))}
                        </ul>
                        <p>
                            Changing your mind adds a new decision rather than
                            editing the old one, so the full history is kept.
                            Use <kbd>j</kbd> and <kbd>k</kbd> to move between
                            flags.
                        </p>
                    </section>

                    <section>
                        <h3>What this page does not show</h3>
                        <p>
                            The hand-tagged bug lines are hidden here so the
                            page cannot give away the answer before you decide.
                            How well each run scored against them is on the
                            Scores tab.
                        </p>
                    </section>
                </div>
            </dialog>
        </>
    );
}
