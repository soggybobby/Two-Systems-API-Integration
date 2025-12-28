import type http from "http";
import { Server as IOServer } from "socket.io";

let io: IOServer | null = null;

export function initWebsocket(server: http.Server) {
  io = new IOServer(server, {
    cors: {
      origin: [
        "http://127.0.0.1:5000",
        "http://localhost:5000",
      ],
      methods: ["GET", "POST"],
      credentials: true,
    },
  });

  io.on("connection", (socket) => {
    console.log("[WS] connected:", socket.id);
    socket.emit("ws:hello", { ok: true });
  });

  return io;
}

export function getIO() {
  if (!io) throw new Error("Socket.IO not initialized");
  return io;
}
