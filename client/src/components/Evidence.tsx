// Evidence blocks labelled with the part of the system they came from.

import type { ReactNode } from "react";

/** A block of evidence, labelled with the part of the system it came from. */
export function Evidence(props: {
    source: "detector" | "explainer" | "model" | "you";
    title: string;
    detail: string;
    children: ReactNode;
}) {
    return (
        <section className="evidence" data-source={props.source}>
            <h3 className="evidence-head">
                <span className="evidence-tag">{props.title}</span>
                <span className="evidence-detail">{props.detail}</span>
            </h3>
            {props.children}
        </section>
    );
}

/** A labelled fact on one line, e.g. "Java: line 7". */
export function Fact({
    name,
    children,
}: {
    name: string;
    children: ReactNode;
}) {
    return (
        <p className="fact">
            <span className="fact-name">{name}</span>
            <span>{children}</span>
        </p>
    );
}
