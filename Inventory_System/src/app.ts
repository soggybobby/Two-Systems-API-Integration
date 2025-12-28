import express from "express";
import http from "http";

import products from "./routes/products";
import ledger from "./routes/ledger";
import stock from "./routes/stock";
import events from "./routes/events";
import { initWebsocket } from "./ws";

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => res.json({ ok: true }));

app.use("/products", products);
app.use("/ledger", ledger);
app.use("/stock", stock);
app.use("/events", events);

const port = process.env.PORT || 3001;

const server = http.createServer(app);
initWebsocket(server);

server.listen(port, () => console.log(`Inventory listening on :${port}`));
