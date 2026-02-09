import mongoose from "mongoose";

const mechanicsSchema = new mongoose.Schema({
  playerMovement: {
    type: String,
    default: "WASD or arrow keys"
  },
  primaryAction: {
    type: String,
    default: "Space to shoot"
  },
  secondaryAction: String
}, { _id: false });

const entitySchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ["player", "enemy", "collectible", "obstacle", "npc"],
    required: true
  },
  sprite: String,
  properties: {
    speed: Number,
    health: Number,
    damage: Number,
    value: Number
  },
  behaviors: [String]
}, { _id: false });

const levelSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true
  },
  layout: {
    type: String,
    enum: ["open", "maze", "linear", "arena"],
    default: "open"
  },
  enemies: {
    type: Number,
    default: 5
  },
  collectibles: {
    type: Number,
    default: 3
  },
  width: {
    type: Number,
    default: 1920
  },
  height: {
    type: Number,
    default: 1080
  }
}, { _id: false });

const uiConfigSchema = new mongoose.Schema({
  showHealth: {
    type: Boolean,
    default: true
  },
  showScore: {
    type: Boolean,
    default: true
  },
  showTimer: {
    type: Boolean,
    default: false
  },
  showMinimap: {
    type: Boolean,
    default: false
  }
}, { _id: false });

const gamePlanSchema = new mongoose.Schema({
  project: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "GameProject",
    required: true
  },
  title: {
    type: String,
    required: true
  },
  genre: {
    type: String,
    enum: ["action", "shooter", "puzzle", "adventure", "platformer", "rpg"],
    default: "action"
  },
  gameType: {
    type: String,
    enum: ["top-down", "platformer", "puzzle", "side-scroller"],
    default: "top-down"
  },
  description: String,
  mechanics: mechanicsSchema,
  entities: [entitySchema],
  levels: [levelSchema],
  winCondition: {
    type: String,
    required: true,
    default: "Defeat all enemies"
  },
  loseCondition: {
    type: String,
    required: true,
    default: "Player health reaches 0"
  },
  ui: uiConfigSchema,
  createdAt: {
    type: Date,
    default: Date.now
  }
});

// Index for quick project lookup
gamePlanSchema.index({ project: 1 });

export default mongoose.model("GamePlan", gamePlanSchema);