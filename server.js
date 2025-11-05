import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { Server } from "socket.io";

const app = express();
const PORT = process.env.PORT || 3000;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(express.static(path.join(__dirname, "public")));
app.use(express.static(path.join(__dirname, "view")));
app.use(express.static(path.join(__dirname, "images")));

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

const server = app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});

const io = new Server(server);
let room = {};
let socketToRoom = {}; 

io.on("connection", (socket) => {
  console.log("Client connected"); 
  const cleanupRoom = (roomID) => {
    if (room[roomID]) {
      console.log(`Cleaning up room ${roomID}`);
      delete room[roomID]; 
    }
  };

  socket.on("disconnect", () => {
    console.log("Client disconnected");
    const roomID = socketToRoom[socket.id]; 
    if (roomID) {
      socket.to(roomID).emit("player2Left"); 
      cleanupRoom(roomID);
      delete socketToRoom[socket.id];
    }
  });

  socket.on("createRoom", (roomID) => {
    room[roomID] = {
      p1Choice: null,
      p2Choice: null,
      p1Score: 0,
      p2Score: 0
    };
    socket.join(roomID);
    socketToRoom[socket.id] = roomID; 
  });

  socket.on("joinRoom", (roomID) => {
    if (!io.sockets.adapter.rooms.has(roomID)) {
      return socket.emit("notValidToken");
    }

    const roomSize = io.sockets.adapter.rooms.get(roomID).size;
    if (roomSize > 1) {
      return socket.emit("roomFull");
    }

    socket.join(roomID);
    socketToRoom[socket.id] = roomID; 
    socket.to(roomID).emit("playersConnected");
    socket.emit("playersConnected");
  });

  socket.on("p1Choice", (data) => {
    const { rpschoice, roomID } = data;
    room[roomID].p1Choice = rpschoice;
    socket.to(roomID).emit("p1Choice", { rpsValue: rpschoice });

    if (room[roomID].p2Choice) declareWinner(roomID);
  });

  socket.on("p2Choice", (data) => {
    const { rpschoice, roomID } = data;
    room[roomID].p2Choice = rpschoice;
    socket.to(roomID).emit("p2Choice", { rpsValue: rpschoice });

    if (room[roomID].p1Choice) declareWinner(roomID);
  });

  socket.on("playerClicked", (data) => {
    const { roomID } = data;
    room[roomID].p1Choice = null;
    room[roomID].p2Choice = null;
    io.to(roomID).emit("playAgain");
  });

  socket.on("exitGame", (data) => {
    const { roomID, player } = data;
    socket.to(roomID).emit(player ? "player1Left" : "player2Left");
    socket.leave(roomID);
    cleanupRoom(roomID);
    delete socketToRoom[socket.id];
  });
});

const declareWinner = (roomID) => {
  const { p1Choice, p2Choice } = room[roomID];
  let winner;

  if (p1Choice === p2Choice) winner = "draw";
  else if (
    (p1Choice === "rock" && p2Choice === "scissor") ||
    (p1Choice === "paper" && p2Choice === "rock") ||
    (p1Choice === "scissor" && p2Choice === "paper")
  ) {
    winner = "p1";
    room[roomID].p1Score++;
  } else {
    winner = "p2"; 
    room[roomID].p2Score++;
  }

  io.to(roomID).emit("winner", {
    winner: winner,
    p1Score: room[roomID].p1Score,
    p2Score: room[roomID].p2Score,
  });
};
