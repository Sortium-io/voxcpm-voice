---
name: voxcpm-voice
description: Design, import, save, and reuse voices locally with VoxCPM2. Create brand-new voices from a text description (no reference audio needed), or import an existing audio clip to clone a real voice — a friend, a voice actor recording, the user's own voice, a sample they like. Once a voice is saved, it can speak any new lines. Invoke whenever the user wants to create a new voice (announcer, narrator, character, AI, villain, kid, elder, anything), clone a voice from an audio file they already have, pick a favorite take, generate voicelines or narration in a saved voice, or manage their voice library. Translates natural-language intent into VoxCPM's directive format. Supports YAML batches for VO banks and multi-voice scenes. Asks 2–3 clarifying questions when a description is too thin. Installs VoxCPM locally on first use.
---

# VoxCPM Voice Generator

This skill gives the user a local library of reusable voices. Voices get in the library two ways: by **designing** from a text description, or by **importing** an existing audio clip. Once a voice is in the library, `speak.py` generates arbitrary new lines in it with consistent timbre across renders.

## Phases

1. **Create** a voice — either
   - **Design** from text (`generate_voice.py`), or
   - **Import** from audio (`import_voice.py`).
2. **Save** a designed take as the voice's reference (`save_take.py`). Imports skip this step — they become the reference directly.
3. **Speak** new voicelines in any saved voice (`speak.py`).
4. **List** the library (`list_voices.py`).

Claude picks the phase based on what the user asks for. Mental cues:

- *"Make me a …"* / *"audition a …"* / *"try …"* → **design** (`generate_voice.py`).
- *"I have this audio clip, clone it"* / *"use my voice"* / *"turn this recording into a voice"* → **import** (`import_voice.py`).
- *"Take 2 is the one"* / *"save that"* / *"keep the first"* → **save** (`save_take.py`). Only applies to designed voices.
- *"Have the drill sergeant say …"* / *"narrate this in Sam's voice"* / *"render these lines"* → **speak** (`speak.py`).
- *"What voices do I have?"* → **list** (`list_voices.py`).
- *"Set this up in my project"* / *"wire voxcpm-voice into this codebase"* / *"init vo here"* → **init** (`init_project.py`).

## Library layout

The skill maintains a library at `~/voxcpm-voice/voices/`:

```
~/voxcpm-voice/voices/<voice_name>/
├── voice.json            metadata (prompt, spoken sentences, imported flag, timestamps)
├── reference.wav         the anchor for future lines
├── samples/              design rolls (DESIGNED voices only; overwritten on re-roll)
│   ├── t1.wav
│   └── t2.wav
└── lines/                cloned voicelines from speak.py (accumulates; never blown away)
    ├── get_your_gear_and_move_out.wav
    └── <batch>/
        ├── fall_in.wav
        └── on_my_mark.wav
```

**Designed voices**: `samples/` holds rolls; `save_take.py` picks one and writes `reference.wav`. Re-designing overwrites `samples/` but preserves `reference.wav` and `lines/`.

**Imported voices**: no `samples/` — `import_voice.py` writes `reference.wav` directly from the user's audio file. `voice.json` has `imported: true` and `source_audio` recording where it came from.

Either way, once `reference.wav` is present, `speak.py` works the same.

## When to invoke

Any of these should trigger this skill:

- "Create / make / design / audition / generate a voice …"
- "Clone this voice" / "use my voice" / "turn this audio into a voice I can use" / "import this clip"
- "Have the \<saved voice\> say …"
- "Narrate this in the \<saved voice\> voice"
- "Render these voicelines for \<voice\>"
- "What voices have I saved?" / "list my voices"
- "Save take N" / "keep the first one" / "use that one for future lines"
- "Set up voxcpm-voice in this project" / "init vo here" / "wire this into this codebase"

**Do NOT invoke for**: long-form TTS unrelated to a saved voice (use a regular TTS tool instead); arbitrary transcription or audio editing (this skill generates speech, not the reverse).

## Mental model

VoxCPM2 has three generation modes; the skill picks the right one automatically based on what the voice looks like in the library.

**Voice Design** (text only, no audio). Used by `generate_voice.py`. Reads `()`-wrapped prefixes as voice conditioning:
```
(voice fantasy)(emotion style)(Chinese hype directive)Sentence one! Sentence two!
```
Everything before the last `)` is style spec; only the sentences get spoken. Good for inventing new voices. Each render is stochastic — there's no anchor — so samples drift from each other.

**Ultimate Cloning** (reference audio + its transcript). Used by `speak.py` when the voice has a `lines` transcript in `voice.json`. Highest fidelity — the model reproduces every nuance of the reference: timbre, cadence, emotion, style. This is what saved voices default to.

**Controllable Cloning** (reference audio, no transcript). Used by `speak.py` when `voice.json` has no transcript, or when the user passes `--direction "..."`. Timbre is locked to the reference, but `()` directives can steer delivery (speed, emotion, pitch). Changes how it sounds — use sparingly if pure reproduction matters.

Three empirically-validated defaults this skill codifies:

1. **Single `generate()` call per design take.** All sentences joined → one voice per WAV. Separate calls = drift.
2. **Chinese emotion directives commit harder than English.** `请用极度激动和兴奋的语气大声喊` produces more actual shouting than "please shout loudly". VoxCPM2 is bilingual and weights Mandarin descriptors more strongly. On by default for energetic voices; off for calm/neutral.
3. **Stock `cfg_value=2.0`, `inference_timesteps=10`** — the README-evaluated config. Pushing cfg higher produces artifacts, not more emotion. Leave it alone.

Once a voice is in the library, `speak.py` renders new lines with consistent timbre — no drift, because cloning uses the saved `reference.wav` as an anchor.

## Workflow

### Step 0: Install VoxCPM if not already installed (idempotent)

Run once, on first use. Skip if already installed. The setup script is cross-platform Python; pick the invocation for the user's OS:

```bash
# macOS / Linux
python3 "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/setup.py"

# Windows (PowerShell or cmd)
python "%CLAUDE_PLUGIN_ROOT%\skills\voxcpm-voice\scripts\setup.py"
```

`${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory — Claude Code sets it automatically. Takes ~2 min on first run. The setup script:

- Creates a venv at `~/voxcpm-voice/voxcpm-venv/` (Windows: `%USERPROFILE%\voxcpm-voice\voxcpm-venv\`)
- Installs `torch` + `torchaudio` — **CUDA 12.1 wheels when `nvidia-smi` is on PATH** (Linux + Windows with NVIDIA cards), otherwise default wheels (macOS MPS, CPU elsewhere).
- Installs `voxcpm` + `soundfile` + `numpy` + `pyyaml`.

Model weights (~2 GB) download lazily on the first `generate()` call.

**Platform-specific Python invocation for later steps**:

- macOS / Linux: `~/voxcpm-voice/voxcpm-venv/bin/python`
- Windows: `%USERPROFILE%\voxcpm-voice\voxcpm-venv\Scripts\python.exe`

Pick the right one when invoking any of the other scripts below.

### Step 0.5: Init the project (optional, but do it when appropriate)

If the user is working inside a project (has a git repo, a source tree, etc.) and they want rendered voicelines to land in the project rather than the user-wide library, run init:

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/init_project.py" \
  --path /path/to/project
```

Creates `<project>/vo/` with `audio/` (rendered output), `scripts/` (YAML batches, starter `example.yaml` copied from the plugin template), and `README.md` (layout notes). Idempotent; safe to run twice.

**When to init automatically**: the user says "set up voxcpm-voice in this project" / "init vo here" / "wire this into my codebase". Don't init unprompted in random directories — the user library works fine for one-off generations.

**After init**, pass `--output-dir <project>/vo/audio` on `speak.py` invocations so WAVs land in the project. The voice *library* (voice.json, reference.wav, design samples) still lives at `~/voxcpm-voice/voices/` — that's machine-wide and shared across projects. Only rendered voicelines go into the project.

### Step 1: Design a voice (when the user wants to create one)

Read what the user said. If it's already concrete (age + gender + timbre + archetype), skip to generation. If it's thin, ask 1–3 focused questions:

- **Thin** (*"a villain voice"*) → gender? cold calculating vs theatrical? age? accent?
- **Medium** (*"a cyberpunk hacker girl"*) → teens or twenties? sassy or cold? accent?
- **Rich** (*"50-something gruff male drill sergeant, gravelly"*) → just generate.

Don't over-interrogate — 2-3 questions max. Also decide:

- **Takes**: default 1. For audition ("let me pick"), bump to 2–3.
- **Emotion directive**: shouting, whispering, menacing, cheerful, etc. Omit for neutral reads.
- **Chinese hype**: default on. Turn off for calm / clinical / narrator voices (`--no-chinese-hype`).

Then generate:

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/generate_voice.py" \
  --voice-name "Drill_Sergeant" \
  --voice-fantasy "gruff male drill sergeant in his fifties, weathered gravelly baritone, hoarse edge" \
  --emotion "SHOUTING with parade-ground authority, hard clipped cadence" \
  --takes 3
```

Writes samples to `~/voxcpm-voice/voices/Drill_Sergeant/samples/t1.wav` etc. + `voice.json`. On macOS, `open ~/voxcpm-voice/voices/Drill_Sergeant/samples/` to play them.

Key flags:

- `--voice-name NAME` (required) — slug; becomes the library folder name.
- `--voice-fantasy "..."` — 1st `()` directive. Concrete traits: age, gender, timbre, accent.
- `--emotion "..."` — 2nd `()` directive. Verbs + intensities.
- `--no-chinese-hype` — opt out of the Mandarin directive.
- `--takes N` — independent renders (stochastic — each is different).
- `--lines "a" "b" "c"` — override the Harvard test sentences (default).
- `--save-take N` — promote take N to `reference.wav` in the same invocation (shortcut; skips step 2).
- `--cfg-value` / `--inference-timesteps` — leave at defaults unless the user asks.
- `--output-dir PATH` — escape hatch for "I don't want this in the library". Skips metadata too.
- `--dry-run` — print composed text + target paths, no generation.

### Step 1b: Import from audio (when the user has an existing clip)

If the user says *"clone this audio"*, *"use my voice"*, *"turn this recording into a voice"*, or hands you a file, use import instead of design. No VoxCPM invocation — just preprocessing + metadata, so this is fast.

**Ask for**:
- The audio path (required).
- A **transcript** of what's said in the clip (optional but strongly recommended — enables Ultimate Cloning for max fidelity). If the user doesn't have one, offer to transcribe it (if you have the tools), or proceed without one and note the quality tradeoff.
- A slug name for the voice (`--voice-name`).

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/import_voice.py" \
  --voice-name "Narrator_Sam" \
  --audio ~/Desktop/sam.mp3 \
  --text "Hello, this is Sam reading a calibration paragraph for the tool."
```

Or with a transcript file:

```bash
... --text-file ~/Desktop/sam-transcript.txt
```

Writes `reference.wav` (mono, trimmed to 25 s) + `voice.json` with `imported: true`. The voice is immediately ready for step 3 — no save step needed.

**Reference-clip tips** to share with the user when appropriate:
- 10–25 seconds is the sweet spot. Longer clips are trimmed; shorter ones under-constrain the clone.
- Clean speech, minimal background noise. Music or heavy effects bake into the clone.
- Consistent delivery in the clip is what the clone inherits — if the clip is calm, the clone will sound calm by default. Add `--direction` at speak time to deviate.

### Step 2: Save a designed take (when the user picks a favorite)

Only for **designed** voices. If the user says "take 2 is the one" / "save that" / "keep the first one":

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/save_take.py" \
  --name Drill_Sergeant \
  --take 2
```

Copies `samples/t2.wav` to `reference.wav`, updates `voice.json`. The voice is now ready for step 3.

If the user is still re-rolling designs (no take is good yet), don't push to save. Offer to re-roll or sharpen the description instead.

Imported voices don't need this — `import_voice.py` writes `reference.wav` directly.

### Step 3: Speak in a saved voice (when the user wants voicelines or narration)

Works identically for designed and imported voices. If the user says "have \<voice\> say X" or "render these lines for \<voice\>":

**Single line:**

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/speak.py" \
  --voice Drill_Sergeant \
  --text "Get your gear and move out!"
```

**Multiple lines, one voice:**

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/speak.py" \
  --voice Drill_Sergeant \
  --lines "Fall in!" "Show me some hustle!" "On my mark."
```

**With a direction** (steers delivery via Controllable Cloning):

```bash
... --voice Narrator_Sam --text "..." --direction "slower, more menacing, whispered"
```

The `--direction` flag prepends `(direction)` to the text before generation. Use when the user wants a specific delivery tweak (faster, angry, excited, whispered, etc.) rather than the default reading.

**Warn the user** when they use `--direction`: this shifts the voice's delivery characteristics and may drift the timbre slightly from pure cloning. For "sound exactly like the original", skip direction. For "have them say this line angrily/softly/fast/etc.", it's the right tool.

**Rendering into a project folder** (after `init_project.py` has been run in that project):

```bash
... --voice Drill_Sergeant --yaml <project>/vo/scripts/example.yaml --output-dir <project>/vo/audio
```

With `--output-dir`, WAVs land at `<output-dir>/<voice>/[<batch>/]<slug>.wav` instead of in the user library. Use this whenever the user is working inside a project they've initialized — it keeps their VO output alongside their code, which is what they want for version control and hand-off.

**Full VO bank / multi-voice scene via YAML** (best when the user hands you a list):

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/speak.py" \
  --yaml path/to/voicelines.yaml
```

YAML schema (template at `${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/templates/voicelines.yaml`):

```yaml
voice: Drill_Sergeant       # default voice for every line
batch: training-vo          # optional subfolder under lines/
takes: 1                    # optional default takes per line
direction: ""               # optional default (direction) for every line

lines:
  - "Get your gear and move out!"              # plain string → uses defaults
  - text: "On my mark!"
    takes: 2                                    # per-line override
  - text: "Fall back, now."
    direction: "urgent, hushed"                 # per-line direction override
  - voice: Arena_PA                             # per-line voice override (multi-voice scene)
    text: "DOUBLE KILL!"
```

If the user hands you many voicelines or wants a scene across multiple voices, **prefer the YAML path** — copy the template, fill it in, pass it to `speak.py --yaml`. It's one model load for the whole batch instead of one per line.

Output lands at `~/voxcpm-voice/voices/<voice>/lines/[<batch>/]<slug>.wav`.

**Important preconditions:**

- The voice must exist in the library (`voice.json` present).
- `reference.wav` must be set (user has to have saved a take first).

If either is missing, `speak.py` exits with a clear error. Steer the user to step 1 or step 2 as appropriate.

### Step 4: List saved voices (when the user wants to see their library)

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/list_voices.py"
```

Shows each voice, its fantasy + emotion, whether a reference is set, and sample/line counts. Use this when the user asks "what voices do I have?" or when they name a voice you're not sure exists.

## Prompting rules of thumb (for when you're iterating with the user)

**Concrete traits beat subjective ones.** *"Baritone around 100 Hz, nasal resonance, slight Brooklyn accent, mid-forties"* gives the model more to lock onto than *"cool deep voice"*. If the output sounds generic, add more concrete traits to `--voice-fantasy`.

**Emotion lives in the directive, not in `cfg_value`.** Voice feels flat? Strengthen the emotion phrase, add more exclamation marks, or insert `[quick_breath]` / `[breath]` tags between sentences via `--lines`. Don't touch cfg.

**Re-rolling is free — try before editing.** Voice design is stochastic. If take 1 is close but not right, take 2 might be perfect without a single prompt change. Re-roll once before tweaking the description.

**Once saved, use speak for all new lines.** Don't re-design a voice for new lines — you'd get drift. Ultimate Cloning from the saved reference keeps the voice identical across renders.

## Common failure modes

- **First run looks stuck**: the model is downloading (~2 GB). Let it run.
- **`speak.py` errors "no reference.wav"**: the user hasn't saved a take yet. Run `save_take.py` first.
- **Voice drifts between lines in `speak` output**: shouldn't happen — Ultimate Cloning anchors to reference + transcript. If it does, check `voice.json` — the `lines` field should list what's actually spoken in `reference.wav`.
- **Voice sounds generic in design**: description too abstract. Add concrete traits; re-roll.
- **Apple Silicon `torch` / MPS error**: `PYTORCH_ENABLE_MPS_FALLBACK=1` is set. If it still fails, the user can edit the script to force CPU.
