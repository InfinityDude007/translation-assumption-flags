// The flag panel's width, changed by dragging or arrow keys on its edge.

import {
    useEffect,
    useState,
    type KeyboardEvent,
    type PointerEvent,
} from "react";

/** Width the panel starts at, and returns to on double-click. */
const DEFAULT = 440;
/** Narrowest the panel can be. */
const MIN = 320;
/** Widest the panel can be, leaving room for the code. */
const max = () => Math.max(MIN, Math.min(1000, window.innerWidth - 360));
/** Where the width is remembered in this browser. */
const STORAGE_KEY = "translation-assumption-flags.side-width";

/** Keep a width inside the allowed range. */
const clamp = (width: number) =>
    Math.round(Math.min(Math.max(width, MIN), max()));

/** Read the remembered width, if the browser allows storage. */
function remembered(): number {
    try {
        const saved = Number(window.localStorage.getItem(STORAGE_KEY));
        return saved ? clamp(saved) : DEFAULT;
    } catch {
        return DEFAULT;
    }
}

/**
 * Track the panel width and handle its resize grip.
 *
 * The panel sits on the right, so the width is the distance from the pointer
 * to the window's right edge.
 *
 * @returns The width, its limits, and the handlers to spread on the grip.
 */
export function useSideWidth() {
    const [width, setWidth] = useState(remembered);

    useEffect(() => {
        try {
            window.localStorage.setItem(STORAGE_KEY, String(width));
        } catch {
            // Storage is optional; the width simply resets next time.
        }
    }, [width]);

    const handlers = {
        onPointerDown(event: PointerEvent<HTMLDivElement>) {
            event.currentTarget.setPointerCapture(event.pointerId);
        },
        onPointerMove(event: PointerEvent<HTMLDivElement>) {
            if (!event.currentTarget.hasPointerCapture(event.pointerId)) return;
            setWidth(clamp(window.innerWidth - event.clientX));
        },
        onDoubleClick() {
            setWidth(clamp(DEFAULT));
        },
        onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
            const step = event.shiftKey ? 80 : 24;
            if (event.key === "ArrowLeft") setWidth((w) => clamp(w + step));
            else if (event.key === "ArrowRight")
                setWidth((w) => clamp(w - step));
            else return;
            event.preventDefault();
        },
    };

    return { width, min: MIN, max: max(), handlers };
}
