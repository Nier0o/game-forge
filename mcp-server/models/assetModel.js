import mongoose from "mongoose";

const assetSchema = new mongoose.Schema({
  project: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "GameProject",
    required: true
  },
  name: {
    type: String,
    required: true
  },
  assetType: {
    type: String,
    enum: ["sprite", "background", "ui", "audio", "tileset", "animation"],
    required: true
  },
  entityType: {
    type: String,
    enum: ["player", "enemy", "collectible", "obstacle", "npc", "environment", null],
    default: null
  },
  filePath: {
    type: String,
    required: true
  },
  fileName: {
    type: String,
    required: true
  },
  mimeType: {
    type: String,
    default: "image/png"
  },
  size: {
    width: {
      type: Number,
      default: 32
    },
    height: {
      type: Number,
      default: 32
    }
  },
  fileSize: {
    type: Number, // in bytes
    default: 0
  },
  generationMethod: {
    type: String,
    enum: ["ai-generated", "template", "procedural", "uploaded"],
    default: "procedural"
  },
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

// Indexes
assetSchema.index({ project: 1 });
assetSchema.index({ project: 1, assetType: 1 });

// Virtual for full URL
assetSchema.virtual("url").get(function() {
  return `/assets/${this.project}/${this.fileName}`;
});

export default mongoose.model("Asset", assetSchema);