import type { Server as HTTPServer } from "http";
import { Server } from "socket.io";

let io: Server | null = null;

export function initSocket(server: HTTPServer) {
  io = new Server(server, {
    cors: {
      origin: "*",
      methods: ["GET", "POST", "PATCH", "PUT", "DELETE"],
    },
  });

  io.on("connection", (socket) => {
    console.log("[Inventory WS] client connected:", socket.id);
    socket.on("disconnect", () => {
      console.log("[Inventory WS] client disconnected:", socket.id);
    });
  });

  return io;
}

export function getIO(): Server {
  if (!io) throw new Error("Socket.IO not initialized. Call initSocket(server) first.");
  return io;
}
