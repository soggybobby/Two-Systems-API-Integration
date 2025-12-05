// src/app.ts
import express from "express";
import cors from "cors";

import products from "./routes/products";
import ledger from "./routes/ledger";
import stock from "./routes/stock";
import events from "./routes/events";

const app = express();

// CORS for Vite frontend at :5173
app.use(
  cors({
    origin: "http://localhost:5173",   // your unified-frontend
  })
);

app.use(express.json());

// Simple health check
app.get("/health", (_req, res) => res.json({ ok: true }));

// Routes
app.use("/products", products);
app.use("/ledger", ledger);
app.use("/stock", stock);
app.use("/events", events);

const port = process.env.PORT || 3001;
app.listen(port, () => {
  console.log(`Inventory listening on :${port}`);
});
