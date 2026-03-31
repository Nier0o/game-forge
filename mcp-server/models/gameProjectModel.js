import mongoose from "mongoose";

const gameProjectSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "User",
    required: true
  },
  title: {
    type: String,
    required: true
  },
  prompt: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ["pending", "planning", "generating", "building", "completed", "failed"],
    default: "pending"
  },
  gamePlan: {
    type: mongoose.Schema.Types.Mixed
  },
  gameUrl: String,
  downloadUrl: String,
  error: String,
  createdAt: {
    type: Date,
    default: Date.now
  },
  completedAt: Date
});

export default mongoose.model("GameProject", gameProjectSchema);