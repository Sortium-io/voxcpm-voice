---
name: voxcpm-voice
description: Generate any voice the user wants — announcer, narrator, character, AI assistant, villain, kid, elder, anything — using VoxCPM2 voice design (text-only TTS, no reference audio). Takes loose natural-language input ("a gruff drill sergeant", "a bubbly anime schoolgirl", "a raspy detective") and expands it into VoxCPM's stacked-`()` directive format, producing one or more WAVs. Invoke whenever the user asks to create, test, audition, or iterate on any voice — announcers, characters, narrators, trailer voices, villain voices, AI system voices, whatever — even if they don't name VoxCPM. If the user's description is thin, ask 2-3 targeted clarifying questions (age/gender/timbre/emotion/accent/context) to dial it in before generating. Supports multiple takes per design so the user can audition variations. Installs VoxCPM locally on first use.
---

# VoxCPM Voice Generator

Generate any voice using VoxCPM2's voice design mode — text-only, no reference audio required. This skill handles three things the user shouldn't have to think about:

1. **Translation**: user says "a gruff drill sergeant"; this skill expands that into the `(concrete voice description)(emotion style)(Chinese hype directive)sentence1! sentence2! sentence3!` format VoxCPM needs.
2. **Clarification**: if the user's description is too loose to produce a distinctive voice, ask 2-3 focused questions before generating.
3. **Execution**: one or many takes, consistent voice within each WAV, silence-padded sentence boundaries, output WAVs with sane names.

## When to invoke

Invoke this skill whenever the user wants to create, test, audition, or iterate on a voice sample of any kind:

- Game announcer / hero-shooter PA / arena voice
- Character voices (villain, sidekick, mentor, kid, elder, creature)
- Narrator / trailer / audiobook voice
- AI system voice / virtual assistant / synthetic operator
- Mascot, radio DJ, newscaster, drill sergeant, ghost, anything

Also invoke when the user says things like "make a voice that sounds like X", "generate a voice", "create a VO sample", "audition some voice ideas", or similar — even if they don't name VoxCPM.

**Do NOT invoke for**: voice cloning from a reference clip (this is voice-design only — point them at a batch-YAML cloning workflow if they need that), long-form narration or full VO bank generation (this skill is scoped to short audition samples), or general TTS of arbitrary long text.

## Mental model — why this approach

The core trick: VoxCPM2 reads `()`-wrapped prefixes as **voice conditioning**, not as speech. So the text passed to the model looks like:

```
(concrete voice description)(emotion / style directive)(Chinese hype directive)Sentence one! Sentence two! Sentence three!
```

VoxCPM treats everything before the last `)` as style spec and only speaks what follows.

Three empirically-validated defaults this skill codifies:

1. **Single `generate()` call per take.** All sentences joined into one text = one voice. Separate generates for separate sentences = voice drift (no anchor locks timbre across calls in voice-design mode).

2. **Chinese emotion directives commit harder than English.** `请用极度激动和兴奋的语气大声喊` produces more actual shouting than "please shout loudly". VoxCPM2 is bilingual and weights Mandarin descriptors more. On by default for high-energy voices; off by default for calm/neutral voices.

3. **Stock `cfg_value=2.0`, `inference_timesteps=10`** — the README-evaluated configuration. Pushing cfg higher tends to produce digital/compressed artifacts rather than more emotional commitment. Leave these alone unless the user has a specific reason.

## Workflow

### Step 1: Install VoxCPM if not already installed (idempotent)

```bash
bash ~/.claude/skills/voxcpm-voice/scripts/setup.sh
```

Creates a venv at `~/voxcpm-voice/voxcpm-venv/` and installs torch + voxcpm + soundfile + numpy. Exits immediately if already installed. Takes ~2 min on first run.

Model weights (~2GB) download lazily on first `generate()` call — user sees HuggingFace progress when step 4 runs.

### Step 2: Gather voice intent

Read what the user already said. Most user requests fall on a spectrum:

**Rich (has concrete traits)**: *"a gruff 50-something male drill sergeant, deep gravelly voice, barks commands, slightly hoarse"* → skip to step 3, enough to build a good prompt.

**Medium (has a vibe but loose)**: *"a cyberpunk hacker girl"* → ask 1-2 questions to get specific. Examples:
- "Teen or twenties?"
- "Playful/sassy or cold/intense?"
- "Any accent (Japanese, British, flat American)?"

**Thin (just an archetype)**: *"a villain voice"* → ask 2-3 focused questions before generating:
- "Male/female/androgynous?"
- "Cold and calculating, or theatrical and chewing scenery?"
- "Any age/accent preference?"

**When in doubt, ask.** A 30-second question exchange is cheaper than generating a wrong-feeling voice and re-rolling 3 times. But don't over-interrogate — 2-3 questions max before you just try it.

Also ask (only when relevant):
- **How many takes?** Default 1. Voice design is stochastic — 3 takes let the user pick the best. Good default for "audition" requests, overkill for one-off.
- **Any emotion/energy direction?** Shouting, whispering, menacing, cheerful, panicked, deadpan, etc. If the user says "neutral reading", turn off Chinese hype.
- **Custom test sentences?** Default is the Harvard sentences (TTS-standard comparison set). User can supply their own lines if they're testing specific content.

### Step 3: Expand the user's input into the VoxCPM prompt

Build three directive strings:

**voice_fantasy** (1st `()` directive): concrete traits. Age band, gender, timbre, accent, archetype. Not subjective words like "cool" or "epic" — those don't give the model enough to lock onto.

| User said | Expand to |
|---|---|
| "gruff drill sergeant" | "gruff male drill sergeant in his fifties, weathered gravelly baritone, shouted military commands, hoarse edge" |
| "cyberpunk hacker girl" (clarified: early 20s, sassy, mild Japanese accent) | "playful young female cyberpunk hacker in her early twenties, wry sassy tone, light Japanese-accented English, gamer energy" |
| "deep movie trailer voice" | "booming male cinematic trailer announcer, rich low chest voice, epic theatrical gravitas, slow deliberate pacing" |

**emotion** (2nd `()` directive, optional): style / energy direction. Use verbs and intensities. SHOUTING, growling, whispering, barking. Adrenaline, menace, awe, panic, amusement. Omit if the user wants a neutral reading.

**chinese_hype** (3rd `()` directive, on/off): default on. Only turn off for explicitly calm/neutral/clinical voices (narrator, PSA, audiobook, AI system read).

### Step 4: Run the generator

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  ~/.claude/skills/voxcpm-voice/scripts/generate_voice.py \
  --voice-name "Drill_Sergeant" \
  --voice-fantasy "gruff male drill sergeant in his fifties, weathered gravelly baritone, shouted military commands, hoarse edge" \
  --emotion "SHOUTING with parade-ground authority, hard clipped cadence, explosive bark" \
  --takes 3
```

Flags:
- `--voice-name NAME` (required) — slug used for output filename. Short, no spaces. Use underscores.
- `--voice-fantasy "..."` — the concrete voice description (1st directive).
- `--emotion "..."` — the style/energy directive (2nd directive, optional).
- `--no-chinese-hype` — opt out of the Chinese directive (on by default).
- `--takes N` — number of independent renders of the same prompt (default 1). Each take is stochastically different.
- `--lines "line1" "line2" "line3"` — override the three test sentences. Default is the Harvard sentences.
- `--cfg-value 2.0` — VoxCPM guidance (default 2.0 = README-evaluated). Leave unless the user specifically asks.
- `--inference-timesteps 10` — diffusion steps (default 10 = README-evaluated). Leave unless asked.
- `--output-dir PATH` — override output location (default `~/voxcpm-voice/outputs/`).
- `--skip-padding` — don't pad inter-sentence silence. Only use if the user is debugging.
- `--dry-run` — print the composed text and output paths without invoking the model. Useful for showing the user what prompt will be sent.

Output naming:
- Single take: `<voice_name>.wav`
- Multiple takes: `<voice_name>_t1.wav`, `<voice_name>_t2.wav`, ...

### Step 5: Report + offer next moves

Tell the user the output path(s). On macOS, `open ~/voxcpm-voice/outputs/` opens the folder in Finder.

Then offer the obvious next steps without listing them all — pick the one that matches the situation:

- **If takes > 1**: "Which take do you like? Re-roll, keep iterating on the prompt, or move on?"
- **If takes = 1 and it sounded off**: "Want to re-roll (voice design is stochastic), sharpen the description, or try a different emotion directive?"
- **If it nailed it**: "Want to generate more takes for variation, or move on to the next voice?"

## Prompting rules of thumb (for when you're iterating with the user)

**Concrete traits beat subjective ones.** "Baritone around 100 Hz, nasal resonance, slight Brooklyn accent, mid-forties" gives the model more to lock onto than "cool deep voice". If the output sounds generic, add more concrete traits to the fantasy string.

**Emotion lives in the directive, not the cfg knob.** Voice feels flat? Strengthen the emotion phrase ("SHOUTING with explosive adrenaline" → "barking at full volume, jaw-forward shouted bark, parade-ground intensity"), add more exclamation marks on the sentences, try inline `[quick_breath]` bursts — don't reach for higher cfg.

**Chinese directives commit harder.** Counterintuitive but reliable. Default on. Turn off for calm/neutral voices (narrator, AI system, audiobook).

**Re-rolling is free.** Voice design is stochastic. If take 1 is close but not right, take 2 might be perfect without any prompt change. Before editing the prompt, try one re-roll.

**Stronger isn't always better.** If the user says "more intense" and it's already maxed, the opposite move sometimes helps — narrowing the description to fewer, more specific traits. Over-stacked directives can confuse the model.

## Silence padding

After generation, the script detects internal silence runs ≥200ms at amplitude <0.01 and pads any shorter than 600ms up to 600ms. Head/tail silence is preserved as-is. If a voice's natural pauses are already ≥600ms, the file is untouched.

If padded silences feel unnatural (rare — usually only with slow theatrical deliveries), offer `--skip-padding`. If the opposite — sentences run together — the user's delivery produced sub-200ms gaps; add `[breath]` between sentences in `--lines` to force pauses.

## Common failure modes

- **First run looks stuck for a minute**: `from_pretrained()` is downloading the model from HuggingFace (~2GB). Let it run.
- **Voice sounds generic / nothing like the description**: description is too abstract. Rewrite with concrete traits (age band, gender, timbre, accent). Re-roll.
- **Voice drifts between sentences in one file**: shouldn't happen with this skill — the generator uses a single `generate()` call. If it does, something went wrong in the script invocation; verify with `--dry-run`.
- **Chinese directive not working**: make sure `--no-chinese-hype` wasn't set. Check the composed text with `--dry-run`.
- **MPS/torch error on Apple Silicon**: `PYTORCH_ENABLE_MPS_FALLBACK=1` is set by the script; if ops still fail, edit `generate_voice.py` to force CPU (`torch.set_default_device("cpu")`).
