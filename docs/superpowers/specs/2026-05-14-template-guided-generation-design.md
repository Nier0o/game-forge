# Template-Guided Generation Design

## Context

Game Forge is a multi-service pipeline that turns a natural-language game prompt into a playable Godot 4 HTML5 export. The current path is:

1. The planner produces a `GamePlan`.
2. The asset and code services run in parallel.
3. The code service renders Godot scripts from fixed templates and selected entity templates.
4. The builder assembles a temporary Godot project, seeds static placeholder assets, exports HTML5, and uploads the game.

The current code service always emits the same core and UI script bundle, then selects entity and level templates. This makes the generated project predictable, but it also makes the templates behave like a fixed game shell instead of deterministic guides that can be applied only where needed.

## Goal

Generalize template usage so templates are deterministic guides and runtime building blocks, not a mandatory all-or-nothing bundle. The system should support the existing deterministic range:

- Side-scroller and platformer games.
- Top-down games.
- Top-down shooter and arena games.
- Simple puzzle and adventure variants.

The coder may extend, adjust, or add scripts within bounded rules when a requested game needs behavior beyond a base template. This pass must not integrate the asset service into the validation flow; generated games should rely on static placeholder assets already present in the builder.

## Non-Goals

- Do not add a new game family outside the existing range.
- Do not hardcode a Flappy Bird product path.
- Do not introduce the asset MCP or external asset-service dependency for this validation pass.
- Do not switch to unconstrained full-script LLM generation.

## Recommended Approach

Use a deterministic scaffold plus bounded LLM extension hooks.

The code service should derive a generation profile from the normalized plan. The profile describes required systems and capabilities, then the renderer emits only the scripts required by that profile. Templates remain deterministic and reusable, while the coder can fill explicit extension slots or create narrowly scoped extra scripts when the base templates cannot express a required behavior.

This keeps the project inside a reliable Godot runtime shape while allowing games in the supported range to differ meaningfully.

## Architecture

### Plan Normalization

The existing normalization step remains the bridge between planner output and renderer input. It should continue to normalize health, win conditions, world size, spawn defaults, and UI preferences.

Add a profile derivation step after normalization:

```text
GamePlan -> normalized plan -> GenerationProfile -> selected templates + extension tasks
```

The profile should describe:

- `family`: side-scroller, platformer, top-down, arena-shooter, puzzle, or adventure.
- `systems`: movement, camera, world, HUD, scoring, health, lives, timer, combat, projectiles, collectibles, hazards, doors, spawners, and triggers.
- `templates`: deterministic scripts needed for the requested game.
- `extensions`: bounded behavior requests for hooks or extra scripts.

### Template Selection

Templates should be selected when their capability is required:

- Core runtime is always needed: entry point, world, and game manager.
- Camera is needed when the player moves through a world larger than one screen or the game family expects following/scrolling behavior.
- HUD is needed only when the plan uses visible score, lives, health, timer, or game-over/win messaging.
- Projectile script is needed only when player or enemy behavior uses shooting.
- Entity templates are needed only for entities present in the plan.
- Level template is selected by game family and level layout.

This design does not require all template files to be emitted for every game. It also does not remove deterministic templates; it makes their inclusion explicit.

### Coder Extensions

The LLM should not generate arbitrary whole-game scripts by default. Instead, it receives:

- The selected template id.
- The template capabilities already covered.
- The exact hooks or extra script responsibilities it may fill.
- A list of forbidden redeclarations and Godot 4 constraints.

Extension output should remain bounded:

- Hook bodies for existing templates where possible.
- Small extra scripts only when the profile requires a capability not represented by a base template.
- No redeclaration of Godot built-ins such as `velocity`.
- No external dependencies.
- No missing placeholder slots.

### Static Assets

For this pass, playable output should rely only on the builder's static assets:

- The builder already seeds `workspace/assets` with placeholder PNGs.
- Missing entity sprites should continue to fall back by entity type.
- The build path should tolerate empty `assetDocs`.
- The UI/playback validation should not require asset-service output.

The asset service can be integrated later after the deterministic generation path is stable.

## Validation Game

Use a Flappy-style side-scroller as a validation scenario, not a special case.

The requested prompt should produce a side-scroller using the general profile and template-extension path. Expected behavior:

- One-button flap or jump-like vertical impulse.
- Gravity pulls the player down.
- The world scrolls or the player progresses horizontally.
- Pipe-like or wall-like obstacles act as hazards.
- Score increases through survival, passing obstacles, or collecting markers.
- Collision with obstacles or falling out of bounds causes game over.
- The game is playable using static assets.

This scenario is useful because it stresses side-scroller movement, camera/scrolling, hazards, scoring, and loss conditions without requiring external assets.

## Testing

Automated tests should cover the deterministic code path before browser testing:

- Profile derivation selects only necessary template systems.
- Projectile templates are omitted when no shooting behavior exists.
- HUD-related scripts are omitted or included according to visible UI systems.
- Static-asset fallback remains valid when `assetDocs` is empty.
- A Flappy-style plan produces side-scroller movement and hazard/scoring systems without a hardcoded Flappy template.

UI/playback verification should then run the frontend visibly and exercise the generated game:

- Create or load a generated side-scroller game.
- Open the play page in a visible browser.
- Focus the iframe.
- Send flap/jump inputs.
- Observe player movement, collisions, scoring, and game-over behavior.
- Iterate until the behavior is correct inside the supported deterministic range.

## Success Criteria

- Template inclusion is profile-driven rather than a fixed mandatory bundle.
- The coder extends deterministic templates through bounded hooks or scoped extra scripts.
- The system still supports the existing game families.
- A Flappy-style side-scroller can be generated, exported, opened in the UI, and played with static assets only.
- Verification includes automated checks and visible browser playback.
