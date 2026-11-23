// Entry point: fonts, styles and the review screen.

import "@fontsource/atkinson-hyperlegible-next/400.css";
import "@fontsource/atkinson-hyperlegible-next/600.css";
import "@fontsource/atkinson-hyperlegible-mono/400.css";
import "@fontsource/atkinson-hyperlegible-mono/700.css";
import "./styles.css";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

createRoot(document.getElementById("root")!).render(
    <StrictMode>
        <App />
    </StrictMode>,
);
