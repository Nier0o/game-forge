import { EventEmitter } from "events";
import { v4 as uuidv4 } from "uuid";
import tools from "./tools/toolDefinitions.js";
import PlannerAdapter from "./adapters/plannerAdapter.js";
import AssetAdapter from "./adapters/assetAdapter.js";
import CodeAdapter from "./adapters/codeAdapter.js";
import BuildAdapter from "./adapters/buildAdapter.js";

class MCPServer extends EventEmitter {
  constructor() {
    super();
    this.name = "game-forge-mcp";
    this.version = "1.0.0";
    this.tools = tools;
    
    this.plannerAdapter = new PlannerAdapter();
    this.assetAdapter = new AssetAdapter();
    this.codeAdapter = new CodeAdapter();
    this.buildAdapter = new BuildAdapter();
    
    this.activeJobs = new Map();
  }


  // List available tools
  listTools() {
    return {
      tools: this.tools.map(tool => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema
      }))
    };
  }

  // Execute a tool by name
  async executeTool(toolName, args) {
    const tool = this.tools.find(t => t.name === toolName);
    
    if (!tool) {
      throw new Error(`Tool '${toolName}' not found`);
    }

    // Validate args against schema (basic validation)
    this.validateArgs(tool.inputSchema, args);

    // Route to appropriate adapter
    switch (toolName) {
      case "plan_game":
        return await this.plannerAdapter.execute(args);
      
      case "generate_assets":
        return await this.assetAdapter.execute(args);
      
      case "generate_code":
        return await this.codeAdapter.execute(args);
      
      case "build_game":
        return await this.buildAdapter.execute(args);
      
      case "get_generation_status":
        return this.getJobStatus(args.jobId);
      
      default:
        throw new Error(`No handler for tool: ${toolName}`);
    }
  }


// Full game generation pipeline
// Orchestrates all adapters in sequence
  async generateGame(prompt, userId, options = {}) {
    const jobId = uuidv4();
    const projectId = uuidv4();
    
    // Initialize job tracking
    this.activeJobs.set(jobId, {
      id: jobId,
      projectId,
      userId,
      status: "initializing",
      currentStep: "planning",
      progress: 0,
      startedAt: new Date(),
      logs: []
    });

    // Run pipeline asynchronously
    this.runPipeline(jobId, projectId, prompt, userId, options);

    return {
      jobId,
      projectId,
      status: "started",
      message: "Game generation pipeline initiated",
      statusUrl: `/api/v1/games/status/${jobId}`
    };
  }

  /**
   * Main pipeline execution
   */
  async runPipeline(jobId, projectId, prompt, userId, options) {
    try {
      // Step 1: Planning
      this.updateJob(jobId, {
        status: "processing",
        currentStep: "planning",
        progress: 10
      });
      this.log(jobId, "Starting game planning...");

      const gamePlan = await this.executeTool("plan_game", {
        prompt,
        gameType: options.gameType || "top-down"
      });
      
      this.log(jobId, `Game plan created: ${gamePlan.title}`);
      this.updateJob(jobId, { progress: 25, gamePlan });

      // Step 2: Asset Generation
      this.updateJob(jobId, {
        currentStep: "assets",
        progress: 30
      });
      this.log(jobId, "Generating game assets...");

      const assets = await this.executeTool("generate_assets", {
        gamePlan,
        assetStyle: options.assetStyle || "pixel-art"
      });

      this.log(jobId, `Generated ${assets.length} assets`);
      this.updateJob(jobId, { progress: 50, assets });

      // Step 3: Code Generation
      this.updateJob(jobId, {
        currentStep: "code",
        progress: 55
      });
      this.log(jobId, "Generating game scripts and scenes...");

      const codeResult = await this.executeTool("generate_code", {
        gamePlan,
        assets
      });

      this.log(jobId, `Generated ${codeResult.scripts.length} scripts and ${codeResult.scenes.length} scenes`);
      this.updateJob(jobId, { progress: 75, codeResult });

      // Step 4: Build
      this.updateJob(jobId, {
        currentStep: "building",
        progress: 80
      });
      this.log(jobId, "Building Godot project and exporting...");

      const buildResult = await this.executeTool("build_game", {
        projectId,
        scripts: codeResult.scripts,
        scenes: codeResult.scenes,
        assets
      });

      // Success!
      this.updateJob(jobId, {
        status: "completed",
        currentStep: "done",
        progress: 100,
        finishedAt: new Date(),
        result: {
          gameUrl: buildResult.gameUrl,
          downloadUrl: buildResult.downloadUrl
        }
      });
      this.log(jobId, "Game generation completed successfully!");

      this.emit("jobCompleted", { jobId, projectId, result: buildResult });

    } catch (error) {
      this.updateJob(jobId, {
        status: "failed",
        error: error.message,
        finishedAt: new Date()
      });
      this.log(jobId, `Error: ${error.message}`);
      this.emit("jobFailed", { jobId, error });
    }
  }

  /**
   * Update job status
   */
  updateJob(jobId, updates) {
    const job = this.activeJobs.get(jobId);
    if (job) {
      Object.assign(job, updates);
      this.emit("jobUpdated", job);
    }
  }

  /**
   * Add log entry to job
   */
  log(jobId, message) {
    const job = this.activeJobs.get(jobId);
    if (job) {
      job.logs.push({
        timestamp: new Date(),
        message
      });
    }
    console.log(`[MCP:${jobId.slice(0, 8)}] ${message}`);
  }


  getJobStatus(jobId) {
    const job = this.activeJobs.get(jobId);
    if (!job) {
      return { found: false, message: "Job not found" };
    }
    return {
      found: true,
      ...job
    };
  }


  validateArgs(schema, args) {
    if (schema.required) {
      for (const field of schema.required) {
        if (!(field in args)) {
          throw new Error(`Missing required field: ${field}`);
        }
      }
    }
  }
}

const mcpServer = new MCPServer();
export default mcpServer;