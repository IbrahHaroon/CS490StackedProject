import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import * as pdfjsWorker from "pdfjs-dist/build/pdf.worker.mjs";
import App from "./App.jsx";
import "./index.css";

// Set up PDF.js worker
import { pdfjs } from "react-pdf";
pdfjs.GlobalWorkerOptions.workerSrc = pdfjsWorker;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
