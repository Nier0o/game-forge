# Template-Guided Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Godot script generation profile-driven so templates are used only when needed, while keeping the existing game families deterministic and playable with static assets.

**Architecture:** Add a `GenerationProfile` layer in `game-forge-code` after plan normalization and entity classification. Core templates stay deterministic, optional scripts are guarded by profile flags, and known side-scroller/impulse-flight behavior is supplied through deterministic hook snippets before falling back to bounded LLM hooks.

**Tech Stack:** Node.js ES modules, Node built-in test runner, Godot 4 GDScript templates, Docker Compose for end-to-end browser playback.

---

### Task 1: Add Generation Profile Tests

**Files:**
- Create: `game-forge-code/test/generationProfile.test.js`
- Modify: `game-forge-code/package.json`

- [ ] **Step 1: Add the test script**

Add this script to `game-forge-code/package.json`:

```json
"test": "node --test test/*.test.js"
```

- [ ] **Step 2: Write failing profile tests**

Create `game-forge-code/test/generationProfile.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { deriveGenerationProfile } from '../src/services/generationProfile.js';

const player = {
	name: 'Bird',
	type: 'player',
	sprite: 'bird',
	properties: { speed: 180, max_health: 1, jump_height: 120 },
	behaviors: ['tap to flap', 'always drift right'],
};

test('side-scroller impulse-flight plan selects camera and hud but no projectile', () => {
	const profile = deriveGenerationProfile({
		title: 'Cave Flap',
		gameType: 'side-scroller',
		genre: 'action',
		description: 'A bird flaps through hazards.',
		mechanics: { playerMovement: 'tap to flap through a scrolling corridor' },
		entities: [
			player,
			{ name: 'Pipe', type: 'hazard', sprite: 'pipe', properties: { damage: 1 }, behaviors: [] },
		],
		levels: [{ width: 1600, height: 720 }],
		winCondition: 'score 10 points',
		loseCondition: 'collision or falling',
		ui: { showScore: true, showHealth: false, showTimer: false },
	});

	assert.equal(profile.family, 'side-scroller');
	assert.equal(profile.systems.camera, true);
	assert.equal(profile.systems.hud, true);
	assert.equal(profile.systems.projectiles, false);
	assert.deepEqual(profile.coreTemplates, ['main', 'world', 'game_manager', 'camera_controller']);
	assert.deepEqual(profile.uiTemplates, ['hud', 'game_over', 'pause_menu']);
	assert.deepEqual(profile.sharedTemplates, []);
});

test('quiet puzzle plan can omit hud and pause templates', () => {
	const profile = deriveGenerationProfile({
		title: 'Quiet Switch Room',
		gameType: 'puzzle',
		genre: 'puzzle',
		description: 'Open a door by stepping on a trigger.',
		mechanics: { playerMovement: 'top-down movement', primaryAction: 'interact' },
		entities: [
			{ name: 'Player', type: 'player', sprite: 'player', properties: {}, behaviors: [] },
			{ name: 'Exit', type: 'door', sprite: 'door', properties: {}, behaviors: [] },
		],
		levels: [{ width: 800, height: 600 }],
		winCondition: 'reach the exit',
		loseCondition: 'none',
		ui: {
			showHealth: false,
			showScore: false,
			showTimer: false,
			showPause: false,
			showGameOver: false,
		},
	});

	assert.equal(profile.family, 'puzzle');
	assert.equal(profile.systems.hud, false);
	assert.equal(profile.systems.pause, false);
	assert.equal(profile.systems.endScreen, false);
	assert.deepEqual(profile.uiTemplates, []);
});

test('shooter plans include projectile dependency only when shooting is present', () => {
	const profile = deriveGenerationProfile({
		title: 'Arena Burst',
		gameType: 'top-down',
		genre: 'shooter',
		mechanics: { playerMovement: 'move in all directions', primaryAction: 'shoot projectiles' },
		entities: [
			{ name: 'Pilot', type: 'player', sprite: 'pilot', properties: {}, behaviors: ['shoot'] },
			{ name: 'Drone', type: 'enemy', sprite: 'drone', properties: {}, behaviors: ['shoot'] },
		],
		levels: [{ width: 1280, height: 720 }],
		ui: { showScore: true },
	});

	assert.equal(profile.family, 'arena-shooter');
	assert.equal(profile.systems.projectiles, true);
	assert.deepEqual(profile.sharedTemplates, ['projectile']);
});
```

- [ ] **Step 3: Run the tests and verify the expected failure**

Run: `npm test` from `game-forge-code`.

Expected: tests fail because `src/services/generationProfile.js` does not exist.

### Task 2: Implement Generation Profile

**Files:**
- Create: `game-forge-code/src/services/generationProfile.js`
- Modify: `game-forge-code/src/services/codeService.js`

- [ ] **Step 1: Add profile implementation**

Create `game-forge-code/src/services/generationProfile.js` with:

```js
import { classifyAll } from './entityClassifier.js';

const CORE_BASE = ['main', 'world', 'game_manager'];
const UI_ORDER = ['hud', 'game_over', 'pause_menu'];

export function deriveGenerationProfile(plan = {}, classificationResult) {
	const classified = classificationResult || classifyAll(plan);
	const family = resolveFamily(plan);
	const entities = Array.isArray(plan.entities) ? plan.entities : [];
	const ui = plan.ui || {};
	const settings = plan.settings || {};
	const text = searchableText(plan);
	const win = String(plan.winCondition || settings.win_condition || '').toLowerCase();
	const lose = String(plan.loseCondition || '').toLowerCase();

	const hasScore = ui.showScore !== false && (
		win.includes('score') ||
		entities.some((e) => ['collectible', 'enemy'].includes(String(e.type || '').toLowerCase()))
	);
	const hasHealth = ui.showHealth !== false && entities.some((e) => String(e.type || '').toLowerCase() === 'player');
	const hasLives = ui.showLives !== false && settings.show_lives !== false && !lose.includes('none');
	const hasTimer = ui.showTimer === true || win.includes('survive') || win.includes('time');
	const hasHud = ui.showHud !== false && (hasScore || hasHealth || hasLives || hasTimer);
	const hasPause = ui.showPause !== false;
	const hasEndScreen = ui.showGameOver !== false && !lose.includes('none');
	const hasCamera = needsCamera(plan, family);
	const hasProjectiles = classified.requiresProjectile || text.includes('projectile');

	return {
		family,
		systems: {
			camera: hasCamera,
			hud: hasHud,
			score: hasScore,
			health: hasHealth,
			lives: hasLives,
			timer: hasTimer,
			pause: hasPause,
			endScreen: hasEndScreen,
			projectiles: hasProjectiles,
			impulseFlight: isImpulseFlightPlan(plan),
		},
		coreTemplates: [...CORE_BASE, ...(hasCamera ? ['camera_controller'] : [])],
		uiTemplates: UI_ORDER.filter((id) =>
			(id === 'hud' && hasHud) ||
			(id === 'game_over' && hasEndScreen) ||
			(id === 'pause_menu' && hasPause)
		),
		sharedTemplates: hasProjectiles ? ['projectile'] : [],
		classifications: classified.classifications,
	};
}

export function isImpulseFlightPlan(plan = {}) {
	const text = searchableText(plan);
	return (
		(text.includes('flap') || text.includes('tap') || text.includes('bird') || text.includes('fly')) &&
		(text.includes('side') || text.includes('scroll') || text.includes('corridor') || String(plan.gameType || '').toLowerCase() === 'side-scroller')
	);
}

function resolveFamily(plan = {}) {
	const gameType = String(plan.gameType || '').toLowerCase();
	const genre = String(plan.genre || '').toLowerCase();
	if (gameType === 'side-scroller') return 'side-scroller';
	if (gameType === 'platformer') return 'platformer';
	if (gameType === 'top-down' && (genre === 'shooter' || genre === 'arena')) return 'arena-shooter';
	if (gameType === 'top-down') return 'top-down';
	if (gameType === 'puzzle') return 'puzzle';
	if (genre === 'adventure' || genre === 'rpg') return 'adventure';
	return 'top-down';
}

function needsCamera(plan, family) {
	const level = Array.isArray(plan.levels) ? plan.levels[0] || {} : {};
	const w = Number(level.width || plan.settings?.world_width || 0);
	const h = Number(level.height || plan.settings?.world_height || 0);
	return (
		['side-scroller', 'platformer', 'top-down', 'arena-shooter', 'adventure'].includes(family) ||
		w > 1000 ||
		h > 700
	);
}

function searchableText(plan = {}) {
	return [
		plan.title,
		plan.genre,
		plan.gameType,
		plan.description,
		plan.winCondition,
		plan.loseCondition,
		plan.mechanics?.playerMovement,
		plan.mechanics?.primaryAction,
		plan.mechanics?.secondaryAction,
		...(Array.isArray(plan.entities) ? plan.entities.flatMap((e) => [e.name, e.type, ...(e.behaviors || [])]) : []),
	].filter(Boolean).join(' ').toLowerCase();
}
```

- [ ] **Step 2: Run profile tests**

Run: `npm test` from `game-forge-code`.

Expected: profile tests pass.

### Task 3: Make Core/UI Template Rendering Profile-Aware

**Files:**
- Modify: `game-forge-code/src/templates/godot/core/main.gd`
- Modify: `game-forge-code/src/templates/godot/core/world.gd`
- Modify: `game-forge-code/src/services/templateRenderer.js`
- Modify: `game-forge-code/src/services/codeService.js`
- Create: `game-forge-code/test/templateRenderer.test.js`

- [ ] **Step 1: Write failing renderer tests**

Create `game-forge-code/test/templateRenderer.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { renderCore } from '../src/services/templateRenderer.js';

test('main template guards optional hud, pause menu, and end screen', () => {
	const content = renderCore('main', {
		plan: { title: 'Quiet Game', settings: {} },
		playerScriptName: 'player',
		levelScriptPath: 'res://scripts/level.gd',
		entitySpawns: '\tpass',
		profile: { systems: { hud: false, pause: false, endScreen: false } },
	});

	assert.match(content, /const ENABLE_HUD: bool = false/);
	assert.match(content, /const ENABLE_PAUSE_MENU: bool = false/);
	assert.match(content, /const ENABLE_END_SCREEN: bool = false/);
	assert.match(content, /if not ENABLE_HUD:/);
});

test('world template can omit camera dependency', () => {
	const content = renderCore('world', {
		plan: { settings: {} },
		playerScriptName: 'player',
		levelScriptPath: 'res://scripts/level.gd',
		entitySpawns: '\tpass',
		profile: { systems: { camera: false } },
	});

	assert.match(content, /const ENABLE_CAMERA: bool = false/);
	assert.match(content, /if not ENABLE_CAMERA:/);
});
```

- [ ] **Step 2: Run renderer tests and verify failure**

Run: `npm test` from `game-forge-code`.

Expected: renderer tests fail because the templates do not expose the new profile flags yet.

- [ ] **Step 3: Add optional flags to template renderer slots**

Update `buildCoreSlots()` in `game-forge-code/src/services/templateRenderer.js` to include:

```js
const systems = (ctx.profile && ctx.profile.systems) || {};
enable_hud: gdBool(toBool(systems.hud, true)),
enable_pause_menu: gdBool(toBool(systems.pause, true)),
enable_end_screen: gdBool(toBool(systems.endScreen, true)),
enable_camera: gdBool(toBool(systems.camera, true)),
hud_script_path: stringSlot(ctx.hudScriptPath, 'res://scripts/hud.gd'),
pause_menu_script_path: stringSlot(ctx.pauseMenuScriptPath, 'res://scripts/pause_menu.gd'),
end_screen_script_path: stringSlot(ctx.endScreenScriptPath, 'res://scripts/game_over.gd'),
camera_script_path: stringSlot(ctx.cameraScriptPath, 'res://scripts/camera_controller.gd'),
```

- [ ] **Step 4: Guard optional loads in `main.gd` and `world.gd`**

Add `ENABLE_HUD`, `ENABLE_PAUSE_MENU`, `ENABLE_END_SCREEN`, `ENABLE_CAMERA`, and script path constants to the templates. Guard `_build_hud()`, `_show_end_screen()`, pause input, `_pause()`, and `_build_camera()` so omitted scripts are never loaded.

- [ ] **Step 5: Use the profile in code generation**

In `game-forge-code/src/services/codeService.js`, import `deriveGenerationProfile`, derive the profile after `classifyAll(plan)`, and replace hardcoded core/UI/projectile loops with `profile.coreTemplates`, `profile.uiTemplates`, and `profile.sharedTemplates`.

- [ ] **Step 6: Run renderer/profile tests**

Run: `npm test` from `game-forge-code`.

Expected: all code-service tests pass.

### Task 4: Add Deterministic Impulse-Flight Extensions

**Files:**
- Create: `game-forge-code/src/services/behaviorExtensions.js`
- Modify: `game-forge-code/src/services/codeService.js`
- Modify: `game-forge-code/src/services/templateRenderer.js`
- Modify: `game-forge-code/src/templates/godot/level/side-scroller-level.gd`
- Create: `game-forge-code/test/behaviorExtensions.test.js`

- [ ] **Step 1: Write failing behavior extension tests**

Create `game-forge-code/test/behaviorExtensions.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { deterministicHooksFor } from '../src/services/behaviorExtensions.js';
import { renderTemplate, renderLevel } from '../src/services/templateRenderer.js';

const plan = {
	title: 'Flap Runner',
	gameType: 'side-scroller',
	genre: 'action',
	description: 'Tap to flap through a scrolling pipe corridor.',
	mechanics: { playerMovement: 'tap to flap and drift right' },
	settings: { world_width: 1280, world_height: 720 },
};

test('impulse-flight player gets deterministic flap and auto-scroll hooks', () => {
	const hooks = deterministicHooksFor({
		entity: { name: 'Bird', type: 'player', behaviors: ['tap to flap', 'always drift right'], properties: {} },
		templateId: 'platformer-player',
		plan,
	});

	assert.match(hooks.extra_input, /velocity\.x = SPEED/);
	assert.match(hooks.extra_input, /ui_accept/);
	assert.match(hooks.extra_physics, /add_score\(1\)/);
	assert.match(hooks.extra_physics, /take_damage\(MAX_HEALTH\)/);
});

test('rendered platformer player contains impulse-flight hook code', () => {
	const content = renderTemplate(
		'platformer-player',
		{ name: 'Bird', type: 'player', sprite: 'bird', properties: { max_health: 1 }, behaviors: [] },
		plan,
		deterministicHooksFor({
			entity: { name: 'Bird', type: 'player', behaviors: ['tap to flap'], properties: {} },
			templateId: 'platformer-player',
			plan,
		})
	);

	assert.match(content, /velocity\.x = SPEED/);
	assert.match(content, /Input\.is_action_just_pressed\("ui_accept"\)/);
});

test('side-scroller level can render in flight mode without ground/platform calls', () => {
	const content = renderLevel('side-scroller-level', {
		...plan,
		settings: { ...plan.settings, flight_mode: true },
	});

	assert.match(content, /const FLIGHT_MODE: bool = true/);
	assert.match(content, /if not FLIGHT_MODE:\n\t\t_build_ground\(\)/);
});
```

- [ ] **Step 2: Run tests and verify failure**

Run: `npm test` from `game-forge-code`.

Expected: behavior tests fail because deterministic hooks and `flight_mode` do not exist yet.

- [ ] **Step 3: Implement deterministic hook generation**

Create `behaviorExtensions.js` to detect impulse-flight side-scroller plans and return `extra_input` and `extra_physics` hooks that set horizontal velocity, flap on `ui_accept`/`ui_select`, award one score per elapsed second, and kill the player below the viewport.

- [ ] **Step 4: Merge deterministic hooks before LLM hooks**

In `codeService.js`, get deterministic hooks for each entity, call the LLM only when unknown behaviors remain, and merge hook strings by concatenating deterministic code before LLM code.

- [ ] **Step 5: Add flight-mode slots**

Add `flight_mode` to `buildLevelSlots()` and `side-scroller-level.gd`. In flight mode, skip ground and platform creation while keeping sky and side walls.

- [ ] **Step 6: Normalize side-scroller hazard sizing**

In `normalizePlan()`, when the plan is impulse-flight side-scroller, default player `max_health` to `1`, default hazard damage to `1`, and give hazards/pipe-like obstacles larger collision sizes when missing.

- [ ] **Step 7: Run tests**

Run: `npm test` from `game-forge-code`.

Expected: all code-service tests pass.

### Task 5: Builder Static Asset Test

**Files:**
- Modify: `game-forge-builder/package.json`
- Modify: `game-forge-builder/src/services/builderService.js`
- Create: `game-forge-builder/test/staticAssets.test.js`

- [ ] **Step 1: Add the test script**

Add this script to `game-forge-builder/package.json`:

```json
"test": "node --test test/*.test.js"
```

- [ ] **Step 2: Write failing static asset fallback test**

Create `game-forge-builder/test/staticAssets.test.js`:

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { seedStaticAssetsForPlan } from '../src/services/builderService.js';

test('static assets are seeded for plan entities when assetDocs is empty', async () => {
	const workspaceDir = await fs.mkdtemp(path.join(os.tmpdir(), 'gf-assets-'));
	try {
		await seedStaticAssetsForPlan({
			workspaceDir,
			plan: {
				entities: [
					{ name: 'Bird', type: 'player', sprite: 'bird' },
					{ name: 'Pipe', type: 'hazard', sprite: 'pipe' },
				],
			},
		});

		await assert.doesNotReject(() => fs.access(path.join(workspaceDir, 'assets', 'bird.png')));
		await assert.doesNotReject(() => fs.access(path.join(workspaceDir, 'assets', 'pipe.png')));
		await assert.doesNotReject(() => fs.access(path.join(workspaceDir, 'assets', 'projectile.png')));
	} finally {
		await fs.rm(workspaceDir, { recursive: true, force: true });
	}
});
```

- [ ] **Step 3: Run builder tests and verify failure**

Run: `npm test` from `game-forge-builder`.

Expected: test fails because `seedStaticAssetsForPlan` is not exported.

- [ ] **Step 4: Export a testable helper**

Export `seedStaticAssetsForPlan()` from `builderService.js`. It should call the existing static asset copy and missing-asset fill logic for a given plan.

- [ ] **Step 5: Run builder tests**

Run: `npm test` from `game-forge-builder`.

Expected: builder static asset test passes.

### Task 6: Verification and Visible Playback

**Files:**
- Modify only if failures reveal root cause.

- [ ] **Step 1: Run service tests**

Run:

```powershell
npm test
```

from `game-forge-code` and `game-forge-builder`.

- [ ] **Step 2: Run lint**

Run:

```powershell
npm run lint
```

from `game-forge-code`, `game-forge-builder`, and `game-forge-frontend`.

- [ ] **Step 3: Rebuild and start the stack**

Run:

```powershell
docker compose up -d --build code builder frontend backend server planner asset minio mongo
```

from `game-forge`.

- [ ] **Step 4: Generate a static-asset Flappy-style side-scroller**

Use the frontend in a visible browser to create a prompt like:

```text
Create a simple side-scroller where a small bird taps to flap through pipe hazards, drifts right automatically, scores points by surviving, and loses when it hits an obstacle or falls.
```

Confirm the spec, start the build, and open the playable game.

- [ ] **Step 5: Playtest behavior**

Focus the game iframe, press the flap key repeatedly, and verify:

- The player moves right automatically.
- The player flaps upward on input and falls under gravity.
- Static assets render.
- Hazards appear.
- Score changes during play.
- Collision or falling reaches a game-over state.

- [ ] **Step 6: Iterate if behavior is wrong**

If playback fails, use systematic debugging: reproduce, inspect console/Godot logs, identify the failing component, add or update a failing test, then apply the smallest fix and re-run verification.
