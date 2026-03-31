import { exec } from 'child_process';
import path from 'path';
import fs from 'fs';
import { promisify } from 'util';

const execAsync = promisify(exec);
const fsPromises = fs.promises;

const OUTPUT_DIR = path.join(process.cwd(), 'public', 'games');
const GODOT_EXECUTABLE = process.env.GODOT_PATH || 'godot';

class BuildAdapter {
  async execute({ projectId, scripts, scenes, assets }) {
    console.log(`[BuildAdapter] Building project: ${projectId}`);

    const outputPath = path.join(OUTPUT_DIR, projectId);
    const indexHtmlPath = path.join(outputPath, 'index.html');

    await fsPromises.mkdir(outputPath, { recursive: true });

    const godotCommand = `${GODOT_EXECUTABLE} --headless --path "${outputPath}" --export-release "Web" "${indexHtmlPath}"`;

    console.log(`[BuildAdapter] Running: ${godotCommand}`);

    try {
      const { stderr } = await execAsync(godotCommand);
      if (stderr) console.warn(`[BuildAdapter] stderr: ${stderr}`);
      console.log(`[BuildAdapter] Build succeeded for ${projectId}`);
    } catch (err) {
      console.error(`[BuildAdapter] Build failed: ${err.message}`);
      throw new Error(`Godot export failed: ${err.message}`);
    }

    const gameUrl = `/games/${projectId}/index.html`;

    return {
      projectId,
      gameUrl,
      downloadUrl: `/api/games/download/${projectId}`,
      outputPath,
    };
  }
}

export default BuildAdapter;
