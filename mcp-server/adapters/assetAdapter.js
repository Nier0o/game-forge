
//  Asset Adapter
//  Generates or prepares visual and audio assets for the game


import fs from "fs";
import path from "path";
import { createCanvas } from "canvas";

class AssetAdapter {
  constructor() {
    this.assetDir = path.join(process.cwd(), "temp", "assets");
    this.defaultAssetsDir = path.join(process.cwd(), "base_game", "assets");
  }


  async execute({ gamePlan, assetStyle = "pixel-art" }) {
    console.log(`[AssetAdapter] Generating assets for: ${gamePlan.title}`);

    const assets = [];

    // Generate assets for each entity
    for (const entity of gamePlan.entities) {
      const asset = await this.generateEntityAsset(entity, assetStyle);
      assets.push(asset);
    }

    // Generate UI assets
    const uiAssets = await this.generateUIAssets(gamePlan.ui, assetStyle);
    assets.push(...uiAssets);

    // Generate background
    const bgAsset = await this.generateBackground(gamePlan, assetStyle);
    assets.push(bgAsset);

    // Generate audio assets (placeholders or default)
    const audioAssets = await this.generateAudioAssets(gamePlan);
    assets.push(...audioAssets);

    console.log(`[AssetAdapter] Generated ${assets.length} assets`);
    return assets;
  }

  /**
   * Generate asset for a game entity
   */
  async generateEntityAsset(entity, style) {
    const colors = this.getEntityColors(entity.type);
    const size = this.getEntitySize(entity.type);

    // For now, generate simple colored shapes
    const assetPath = await this.generateSimpleSprite(
      entity.sprite || `${entity.name.toLowerCase()}.png`,
      size,
      colors,
      entity.type
    );

    return {
      name: entity.name,
      type: "sprite",
      entityType: entity.type,
      path: assetPath,
      size: size
    };
  }

  /**
   * Generate a simple sprite using Canvas
   */
  async generateSimpleSprite(filename, size, colors, entityType) {
    const outputDir = path.join(process.cwd(), "temp", "generated_assets");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const canvas = createCanvas(size.width, size.height);
    const ctx = canvas.getContext("2d");

    // Draw based on entity type
    ctx.fillStyle = colors.primary;
    
    switch (entityType) {
      case "player":
        // Draw a simple character shape
        ctx.fillRect(size.width * 0.25, 0, size.width * 0.5, size.height * 0.4);
        ctx.fillRect(0, size.height * 0.4, size.width, size.height * 0.6);
        // Eyes
        ctx.fillStyle = colors.secondary;
        ctx.fillRect(size.width * 0.3, size.height * 0.15, 4, 4);
        ctx.fillRect(size.width * 0.6, size.height * 0.15, 4, 4);
        break;

      case "enemy":
        // Draw enemy shape
        ctx.beginPath();
        ctx.arc(size.width / 2, size.height / 2, size.width / 2 - 2, 0, Math.PI * 2);
        ctx.fill();
        // Angry eyes
        ctx.fillStyle = colors.secondary;
        ctx.fillRect(size.width * 0.25, size.height * 0.35, 6, 4);
        ctx.fillRect(size.width * 0.6, size.height * 0.35, 6, 4);
        break;

      case "collectible":
        // Draw coin/collectible
        ctx.beginPath();
        ctx.arc(size.width / 2, size.height / 2, size.width / 2 - 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = colors.secondary;
        ctx.beginPath();
        ctx.arc(size.width / 2, size.height / 2, size.width / 4, 0, Math.PI * 2);
        ctx.fill();
        break;

      default:
        ctx.fillRect(0, 0, size.width, size.height);
    }

    const filePath = path.join(outputDir, filename);
    const buffer = canvas.toBuffer("image/png");
    fs.writeFileSync(filePath, buffer);

    return filePath;
  }

 
// Generate UI assets
   
  async generateUIAssets(uiConfig, style) {
    const assets = [];

    if (uiConfig.showHealth) {
      assets.push({
        name: "HealthBar",
        type: "ui",
        path: await this.generateHealthBar(),
        size: { width: 100, height: 20 }
      });
    }

    return assets;
  }

  async generateHealthBar() {
    const outputDir = path.join(process.cwd(), "temp", "generated_assets", "ui");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const canvas = createCanvas(100, 20);
    const ctx = canvas.getContext("2d");

    // Background
    ctx.fillStyle = "#333333";
    ctx.fillRect(0, 0, 100, 20);

    // Health fill
    ctx.fillStyle = "#00ff00";
    ctx.fillRect(2, 2, 96, 16);

    const filePath = path.join(outputDir, "health_bar.png");
    fs.writeFileSync(filePath, canvas.toBuffer("image/png"));

    return filePath;
  }

// Generate background
  async generateBackground(gamePlan, style) {
    const outputDir = path.join(process.cwd(), "temp", "generated_assets");
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    const canvas = createCanvas(1920, 1080);
    const ctx = canvas.getContext("2d");

    // Simple gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, 1080);
    gradient.addColorStop(0, "#1a1a2e");
    gradient.addColorStop(1, "#16213e");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 1920, 1080);

    // Add some dots for stars/decoration
    ctx.fillStyle = "#ffffff";
    for (let i = 0; i < 100; i++) {
      const x = Math.random() * 1920;
      const y = Math.random() * 1080;
      ctx.fillRect(x, y, 2, 2);
    }

    const filePath = path.join(outputDir, "background.png");
    fs.writeFileSync(filePath, canvas.toBuffer("image/png"));

    return {
      name: "Background",
      type: "background",
      path: filePath,
      size: { width: 1920, height: 1080 }
    };
  }

// Generate audio asset references
  async generateAudioAssets(gamePlan) {
    // For now, return references to default audio files
    // In production, this could use AI audio generation
    return [
      {
        name: "ShootSound",
        type: "audio",
        path: path.join(this.defaultAssetsDir, "audio", "shoot.wav"),
        audioType: "sfx"
      },
      {
        name: "CollectSound",
        type: "audio",
        path: path.join(this.defaultAssetsDir, "audio", "collect.wav"),
        audioType: "sfx"
      },
      {
        name: "BackgroundMusic",
        type: "audio",
        path: path.join(this.defaultAssetsDir, "audio", "bgm.ogg"),
        audioType: "music"
      }
    ];
  }

  getEntityColors(type) {
    const colorMap = {
      player: { primary: "#4CAF50", secondary: "#ffffff" },
      enemy: { primary: "#f44336", secondary: "#ffffff" },
      collectible: { primary: "#FFD700", secondary: "#FFA500" },
      obstacle: { primary: "#795548", secondary: "#5D4037" }
    };
    return colorMap[type] || { primary: "#9E9E9E", secondary: "#757575" };
  }

  getEntitySize(type) {
    const sizeMap = {
      player: { width: 32, height: 32 },
      enemy: { width: 32, height: 32 },
      collectible: { width: 16, height: 16 },
      obstacle: { width: 64, height: 64 }
    };
    return sizeMap[type] || { width: 32, height: 32 };
  }
}

export default AssetAdapter;