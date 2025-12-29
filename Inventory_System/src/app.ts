import express from "express";
import http from "http";

import products from "./routes/products";
import ledger from "./routes/ledger";
import stock from "./routes/stock";
import events from "./routes/events";
import { initSocket } from "./ws"; // ✅ correct name

const app = express();
app.use(express.json());
app.use(express.static("public"));

app.get("/health", (_req, res) => res.json({ ok: true }));

app.use("/products", products);
app.use("/ledger", ledger);
app.use("/stock", stock);
app.use("/events", events);

const port = process.env.PORT || 3001;

const server = http.createServer(app);
initSocket(server); // ✅ correct function

server.listen(port, () => {
  console.log(`Inventory listening on :${port}`);
});
