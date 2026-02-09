export const tools = [
  {
    name: "plan_game",
    description: "Converts a natural language game prompt into a structured game design specification including genre, mechanics, entities, and win/lose conditions.",
    inputSchema: {
      type: "object",
      properties: {
        prompt: {
          type: "string",
          description: "Natural language description of the game to create"
        },
        gameType: {
          type: "string",
          enum: ["top-down", "platformer", "puzzle"], // Example game types
          description: "Type of 2D game to generate",
          default: "top-down"
        }
      },
      required: ["prompt"]
    }
  },
  {
    name: "generate_assets",
    description: "Generates or prepares visual and audio assets based on the game plan.",
    inputSchema: {
      type: "object",
      properties: {
        gamePlan: {
          type: "object",
          description: "The structured game plan from plan_game tool"
        },
        assetStyle: {
          type: "string",
          enum: ["pixel-art", "simple-shapes", "cartoon"], // Example asset styles
          default: "pixel-art"
        }
      },
      required: ["gamePlan"]
    }
  },
  {
    name: "generate_code",
    description: "Generates Godot scripts and scene files based on the game plan and assets.",
    inputSchema: {
      type: "object",
      properties: {
        gamePlan: {
          type: "object",
          description: "The structured game plan"
        },
        assets: {
          type: "array",
          description: "Array of generated asset references"
        }
      },
      required: ["gamePlan", "assets"]
    }
  },
  {
    name: "build_game",
    description: "Assembles the Godot project and exports it as a playable HTML5 game.",
    inputSchema: {
      type: "object",
      properties: {
        projectId: {
          type: "string",
          description: "Unique identifier for the game project"
        },
        scripts: {
          type: "array",
          description: "Generated GDScript files"
        },
        scenes: {
          type: "array",
          description: "Generated scene files"
        },
        assets: {
          type: "array",
          description: "Asset file references"
        }
      },
      required: ["projectId", "scripts", "scenes", "assets"]
    }
  },
  {
    name: "get_generation_status",
    description: "Gets the current status of a game generation job.",
    inputSchema: {
      type: "object",
      properties: {
        jobId: {
          type: "string",
          description: "The job ID to check status for"
        }
      },
      required: ["jobId"]
    }
  }
];

export default tools;