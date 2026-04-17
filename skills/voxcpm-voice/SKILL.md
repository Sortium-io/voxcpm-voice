---
name: voxcpm-voice
description: Design, save, and reuse voices locally with VoxCPM2 — no reference audio needed to create a voice, and once saved the same voice can speak any new lines you throw at it. Invoke whenever the user wants to create a new voice (announcer, narrator, character, AI, villain, kid, elder, anything), pick a favorite take as a keeper, generate new voicelines or narration in an existing saved voice, or manage their voice library. Translates natural-language intent ("a gruff drill sergeant", "a bubbly hacker girl") into VoxCPM's stacked-`()` directive format. Supports YAML batches for VO banks and multi-voice scenes. Asks 2–3 clarifying questions when a description is too thin. Installs VoxCPM locally on first use.
---

# VoxCPM Voice Generator

Generate any voice using VoxCPM2, save the ones worth keeping, and reuse them to voice new lines later. This skill spans three phases:

1. **Design** — create a new voice from a text description. (Voice-design mode: text-only, no reference audio needed.)
2. **Save** — promote the best take of a designed voice to its `reference.wav` so it can be reused.
3. **Speak** — generate arbitrary new voicelines in a saved voice. (Ultimate Cloning mode: reference + transcript = consistent voice across renders.)

Claude picks the right phase based on what the user is asking for. The three mental cues:

- *"Make me a …"* / *"audition a …"* / *"try …"* → **design** (run `generate_voice.py`).
- *"That one's good, save it"* / *"use take 2"* / *"keep that one"* → **save** (run `save_take.py`).
- *"Have the drill sergeant say …"* / *"narrate this in the villain voice"* / *"render these lines"* → **speak** (run `speak.py`).
- *"What voices do I have?"* → **list** (run `list_voices.py`).

## Library layout

The skill maintains a library at `~/voxcpm-voice/voices/`:

```
~/voxcpm-voice/voices/<voice_name>/
├── voice.json            metadata (prompt, sentences spoken, reference_take, timestamps)
├── reference.wav         the chosen take — only written by save_take.py
├── samples/              design rolls (overwritten on re-roll — don't get attached)
│   ├── t1.wav
│   └── t2.wav
└── lines/                cloned voicelines from speak.py (accumulates; never blown away)
    ├── get_your_gear_and_move_out.wav
    └── <batch>/
        ├── fall_in.wav
        └── on_my_mark.wav
```

Re-designing with the same name overwrites `samples/` but leaves `reference.wav` and `lines/` alone. So the user can iterate safely on a design without losing what they already keep.

## When to invoke

Any of these should trigger this skill:

- "Create / make / design / audition / generate a voice …"
- "Have the \<saved voice\> say …"
- "Narrate this in the \<saved voice\> voice"
- "Render these voicelines for \<voice\>"
- "What voices have I saved?" / "list my voices"
- "Save take N" / "keep the first one" / "use that one for future lines"

**Do NOT invoke for**: voice cloning from an arbitrary reference clip the user provides (this skill only clones from voices it designed itself); long-form TTS of a paragraph unrelated to a saved voice (just use regular TTS tools).

## Mental model

VoxCPM2 reads `()`-wrapped prefixes as **voice conditioning**, not as speech. Voice design text looks like:

```
(voice fantasy)(emotion style)(Chinese hype directive)Sentence one! Sentence two! Sentence three!
```

Everything before the last `)` is style spec; only the sentences after get spoken.

Three empirically-validated defaults this skill codifies:

1. **Single `generate()` call per take.** All sentences joined into one text = one voice. Separate generates for separate sentences = voice drift. Voice design has no anchor.
2. **Chinese emotion directives commit harder than English.** `请用极度激动和兴奋的语气大声喊` produces more actual shouting than "please shout loudly". VoxCPM2 is bilingual and weights Mandarin descriptors more strongly. On by default for energetic voices; off for calm/neutral.
3. **Stock `cfg_value=2.0`, `inference_timesteps=10`** — the README-evaluated config. Pushing cfg higher produces artifacts, not more emotion. Leave it alone.

Once a voice is *saved* (has `reference.wav`), subsequent voicelines switch to **Ultimate Cloning** — reference WAV + transcript fed together to lock the voice exactly. No drift across renders.

## Workflow

### Step 0: Install VoxCPM if not already installed (idempotent)

Run once, on first use. Skip if already installed:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/setup.sh"
```

`${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory — Claude Code sets it automatically. Creates a venv at `~/voxcpm-voice/voxcpm-venv/` and installs torch + voxcpm + soundfile + numpy + pyyaml. Takes ~2 min on first run.

Model weights (~2 GB) download lazily on the first `generate()` call.

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

### Step 2: Save a take (when the user picks a favorite)

If the user says "take 2 is the one" / "save that" / "keep the first one":

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  "${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/save_take.py" \
  --name Drill_Sergeant \
  --take 2
```

Copies `samples/t2.wav` to `reference.wav`, updates `voice.json`. The voice is now ready for step 3.

If the user is still re-rolling designs (no take is good yet), don't push to save. Offer to re-roll or sharpen the description instead.

### Step 3: Speak in a saved voice (when the user wants voicelines or narration)

If the user says "have \<voice\> say X" or "render these lines for \<voice\>":

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

lines:
  - "Get your gear and move out!"              # plain string → uses defaults
  - text: "On my mark!"
    takes: 2                                    # per-line override
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
