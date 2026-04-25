import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { pdfjs } from "react-pdf";
import App from "./App.jsx";
import { ErrorBoundary } from "./components/ErrorBoundary.jsx";
import { initGlobalErrorCapture } from "./lib/errorHandler.js";
import "./index.css";

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.mjs",
  import.meta.url
).toString();

// Capture unhandled JS errors and promise rejections into the log buffer
initGlobalErrorCapture();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <ErrorBoundary name="App">
        <App />
      </ErrorBoundary>
    </BrowserRouter>
  </React.StrictMode>
);
