import mongoose from "mongoose";

const logEntrySchema = new mongoose.Schema({
  timestamp: { type: Date, default: Date.now },
  message: String
});

const generationJobSchema = new mongoose.Schema({
  project: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "GameProject",
    required: true
  },
  status: {
    type: String,
    enum: ["queued", "processing", "completed", "failed"],
    default: "queued"
  },
  currentStep: {
    type: String,
    enum: ["planning", "assets", "code", "building", "done"],
    default: "planning"
  },
  progress: {
    type: Number,
    default: 0,
    min: 0,
    max: 100
  },
  logs: [logEntrySchema],
  error: String,
  startedAt: {
    type: Date,
    default: Date.now
  },
  finishedAt: Date
});

export default mongoose.model("GenerationJob", generationJobSchema);