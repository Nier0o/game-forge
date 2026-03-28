// Planner Adapter
// Converts natural language prompts into structured game design specifications


import OpenAI from "openai";

class PlannerAdapter {
  constructor() {
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    });
  }

  /**
   * Execute game planning
   */
  async execute({ prompt, gameType = "top-down" }) {
    console.log(`[PlannerAdapter] Planning game for: "${prompt}"`);

    const systemPrompt = this.buildSystemPrompt(gameType);
    const userPrompt = this.buildUserPrompt(prompt, gameType);

    try {
      const response = await this.openai.chat.completions.create({
        model: process.env.OPENAI_MODEL || "gpt-4",
        messages: [
          { role: "system", content: systemPrompt },
          { role: "user", content: userPrompt }
        ],
        temperature: 0.7,
        response_format: { type: "json_object" }
      });

      const planText = response.choices[0].message.content;
      const gamePlan = JSON.parse(planText);

      // Validate and enhance the plan
      return this.validateAndEnhancePlan(gamePlan, gameType);

    } catch (error) {
      console.error("[PlannerAdapter] Error:", error);
      // Return a default plan if AI fails
      return this.getDefaultPlan(prompt, gameType);
    }
  }

  buildSystemPrompt(gameType) {
    return `You are a game design AI assistant specialized in creating 2D ${gameType} games using the Godot engine.
Your task is to convert natural language game descriptions into detailed, structured game design specifications.

You must respond with a valid JSON object containing the game plan.

The JSON structure must be:
{
  "title": "Game Title",
  "genre": "action/shooter/puzzle/adventure/platformer/rpg",
  "gameType": "${gameType}",
  "description": "Brief description",
  "mechanics": {
    "playerMovement": "description of how player moves",
    "primaryAction": "main action (shoot/jump/collect)",
    "secondaryAction": "optional secondary action"
  },
  "entities": [
    {
      "name": "Player",
      "type": "player",
      "sprite": "player.png",
      "properties": {
        "speed": 200,
        "health": 100
      },
      "behaviors": ["movement", "shooting"]
    },
    {
      "name": "Enemy",
      "type": "enemy", 
      "sprite": "enemy.png",
      "properties": {
        "speed": 100,
        "health": 50,
        "damage": 10
      },
      "behaviors": ["patrol", "chase"]
    }
  ],
  "levels": [
    {
      "name": "Level 1",
      "layout": "open/maze/linear",
      "enemies": 5,
      "collectibles": 3
    }
  ],
  "winCondition": "Defeat all enemies / Collect all items / Reach the exit",
  "loseCondition": "Player health reaches 0",
  "ui": {
    "showHealth": true,
    "showScore": true,
    "showTimer": false
  }
}`;
  }

  buildUserPrompt(prompt, gameType) {
    return `Create a detailed game plan for the following game idea:

"${prompt}"

Requirements:
- Game type: 2D ${gameType}
- Keep it simple and achievable
- Include at least: player, 1 enemy type, 1 collectible
- Define clear win and lose conditions
- Make it fun and playable

Respond with the JSON game plan only.`;
  }

  validateAndEnhancePlan(plan, gameType) {
    // Ensure required fields exist
    const validated = {
      title: plan.title || "Untitled Game",
      genre: plan.genre || "action",
      gameType: gameType,
      description: plan.description || "",
      mechanics: plan.mechanics || {
        playerMovement: "WASD or arrow keys",
        primaryAction: "Space to shoot"
      },
      entities: plan.entities || this.getDefaultEntities(),
      levels: plan.levels || [{ name: "Level 1", layout: "open", enemies: 3, collectibles: 5 }],
      winCondition: plan.winCondition || "Defeat all enemies",
      loseCondition: plan.loseCondition || "Player health reaches 0",
      ui: plan.ui || { showHealth: true, showScore: true, showTimer: false },
      createdAt: new Date()
    };

    // Ensure player entity exists
    const hasPlayer = validated.entities.some(e => e.type === "player");
    if (!hasPlayer) {
      validated.entities.unshift(this.getDefaultPlayer());
    }

    return validated;
  }

  getDefaultEntities() {
    return [
      this.getDefaultPlayer(),
      {
        name: "Enemy",
        type: "enemy",
        sprite: "enemy.png",
        properties: { speed: 100, health: 30, damage: 10 },
        behaviors: ["patrol"]
      },
      {
        name: "Coin",
        type: "collectible",
        sprite: "coin.png",
        properties: { value: 10 },
        behaviors: []
      }
    ];
  }

  getDefaultPlayer() {
    return {
      name: "Player",
      type: "player",
      sprite: "player.png",
      properties: { speed: 200, health: 100 },
      behaviors: ["movement", "shooting"]
    };
  }

  getDefaultPlan(prompt, gameType) {
    return {
      title: "Generated Game",
      genre: "action",
      gameType: gameType,
      description: prompt,
      mechanics: {
        playerMovement: "WASD or arrow keys to move",
        primaryAction: "Space to shoot"
      },
      entities: this.getDefaultEntities(),
      levels: [{ name: "Level 1", layout: "open", enemies: 5, collectibles: 10 }],
      winCondition: "Collect all coins",
      loseCondition: "Player health reaches 0",
      ui: { showHealth: true, showScore: true, showTimer: false },
      createdAt: new Date()
    };
  }
}

export default PlannerAdapter;