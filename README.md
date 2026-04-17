# voxcpm-voice

A Claude Code skill for generating any voice — announcer, narrator, character, AI assistant, villain, kid, elder — using [VoxCPM2](https://github.com/OpenBMB/VoxCPM) in voice-design mode (text-only TTS, no reference audio required).

You describe what you want in plain English. The skill expands your description into VoxCPM's stacked `()` directive format, runs the model, and writes a WAV you can drop into your game / app / project.

## What it does

Given an intent like *"a gruff drill sergeant"*, the skill:

1. **Asks 2–3 clarifying questions** if the description is thin (age, accent, emotion, context) — or skips straight to generation if you already provided concrete traits.
2. **Expands your description** into the format VoxCPM needs: `(voice_fantasy)(emotion_style)(chinese_hype_directive)sentence1! sentence2! sentence3!`
3. **Runs a single `generate()` call per take** so the voice stays consistent across all three sentences in a single WAV (no drift).
4. **Silence-pads sentence boundaries** to 600ms so the takes feel like takes, not a monologue.
5. Writes to `~/voxcpm-voice/outputs/<voice_name>.wav` (or `_t1.wav`, `_t2.wav` for multi-take runs).

The defaults codify what's been validated empirically:

- `cfg_value=2.0`, `inference_timesteps=10` — the VoxCPM README-evaluated config.
- Chinese emotion directive on by default — VoxCPM2 is bilingual and commits harder to Mandarin directives than English equivalents.
- Single-generate-per-take for voice consistency.

## Prerequisites

- [Claude Code](https://claude.com/claude-code) (this is a Claude Code skill)
- macOS or Linux (tested on macOS; Linux should work)
- Python 3.10 or newer with `venv` module
- ~3 GB free disk for the Python venv + VoxCPM2 model weights
- GPU helpful but not required (Apple Silicon MPS, CUDA, or CPU)

## Install

```bash
claude plugin marketplace add Sortium-io/voxcpm-voice
claude plugin install voxcpm-voice
```

That's it. Next time you start a Claude Code session, the skill is available. Ask for a voice in plain English and Claude will take it from there.

First voice generation triggers an auto-setup:

- Creates a Python venv at `~/voxcpm-voice/voxcpm-venv/`
- Installs `voxcpm`, `soundfile`, `torchaudio`, `numpy`, `pyyaml`
- Downloads the VoxCPM2 model weights (~2 GB) from HuggingFace

Subsequent runs skip all of that — setup is idempotent, weights are cached.

### Updating

```bash
claude plugin update voxcpm-voice
```

### Uninstalling

```bash
claude plugin uninstall voxcpm-voice
claude plugin marketplace remove voxcpm-voice   # optional: also forget the marketplace
rm -rf ~/voxcpm-voice                           # optional: remove the runtime (venv + outputs)
```

## Usage

Once the plugin's installed, just start a Claude Code session and describe the voice you want in plain English. The skill picks it up, asks a follow-up if your description is thin, then generates a WAV containing three test sentences in one consistent voice. On first run it'll spend ~2 min building the Python venv and ~1 min downloading the VoxCPM2 model; every run after that generates in under 10 seconds. Output lands in `~/voxcpm-voice/outputs/`.

### Kick it off

Paste this into Claude Code to try it:

```
Use the voxcpm-voice skill to audition a voice for me.
I want a gruff male drill sergeant in his fifties — weathered
gravelly baritone, shouted parade-ground commands, hoarse edge.
Give me 3 takes so I can pick the best one.
```

When it finishes, `open ~/voxcpm-voice/outputs/` on macOS (or browse there on Linux) and play the three takes. If none of them nail it, tell Claude what's off — *"deeper"*, *"less hoarse"*, *"more barking"* — and it'll re-roll with a sharper prompt.

### More examples

Any of these will trigger the skill:

- *"Make me a voice that sounds like a cyberpunk hacker girl — early twenties, sassy, mild Japanese accent."*
- *"I need a cold villain voice for a cartoon. Male, middle-aged, deliberate."*
- *"Generate an arena announcer for my FPS."*
- *"Audition a few takes of a grizzled detective narrating a noir scene."*

If your description is too thin (*"make me a villain voice"*), Claude will ask 2–3 targeted follow-ups (gender, age, accent, emotion, context) before generating. If it's concrete enough, it generates immediately.

### Direct CLI usage

The skill calls this underneath; you can invoke it directly once the plugin is installed:

```bash
~/voxcpm-voice/voxcpm-venv/bin/python \
  ~/.claude/plugins/marketplaces/voxcpm-voice/skills/voxcpm-voice/scripts/generate_voice.py \
  --voice-name "Drill_Sergeant" \
  --voice-fantasy "gruff male drill sergeant in his fifties, weathered gravelly baritone, shouted military commands, hoarse edge" \
  --emotion "SHOUTING with parade-ground authority, hard clipped cadence, explosive bark" \
  --takes 3
```

Available flags:

| Flag | Default | Description |
|---|---|---|
| `--voice-name NAME` | _required_ | Slug for output filename (no spaces, use underscores) |
| `--voice-fantasy "..."` | "" | Concrete voice description. Age + gender + timbre + accent + archetype. |
| `--emotion "..."` | "" | Style/energy directive. Use verbs (SHOUTING, whispering, barking). |
| `--no-chinese-hype` | off | Disable the Chinese emotion directive (on by default — commits harder). |
| `--takes N` | 1 | Number of independent renders of the same prompt. |
| `--lines "a" "b" "c"` | Harvard sentences | Override the three test sentences. |
| `--cfg-value N` | 2.0 | VoxCPM guidance (README default). Higher = over-commits, can produce artifacts. |
| `--inference-timesteps N` | 10 | Diffusion steps (README default). Higher = slower, marginally cleaner. |
| `--output-dir PATH` | `~/voxcpm-voice/outputs/` | Where to write WAVs. |
| `--skip-padding` | off | Skip inter-sentence silence padding. |
| `--dry-run` | off | Print composed prompt + target paths without generating. |

## How it works

VoxCPM2 reads `()`-wrapped prefixes as **voice conditioning**, not as speech. So the text passed to the model looks like:

```
(concrete voice description)(emotion/style directive)(Chinese hype directive)Sentence one! Sentence two! Sentence three!
```

Everything before the last `)` is style spec; only what follows is spoken. Three things matter:

**Concrete traits beat subjective ones.** *"Baritone around 100 Hz, gravelly, mid-forties"* gives the model more to lock onto than *"cool deep voice"*. Age, gender, timbre, accent, archetype — these are what VoxCPM weighs.

**Chinese directives commit harder than English.** Counterintuitive but reliable: `请用极度激动和兴奋的语气大声喊` produces more actual shouting than the English equivalent. VoxCPM2 is bilingual and weights Mandarin descriptors more strongly.

**Emotion lives in the directive, not in `cfg_value`.** If the output feels flat, strengthen the emotion phrase, add exclamation marks on the sentences, or drop in `[breath]` / `[quick_breath]` tags between sentences — don't reach for higher cfg. Pushing cfg can cause digital/compressed artifacts instead of more commitment.

## Prompt examples that work

| User asks for | Voice fantasy | Emotion |
|---|---|---|
| Arena PA | `deep gravelly male arena announcer, forties, PA-system reverb` | `SHOUTING with explosive adrenaline hype, urgent commanding bark` |
| Drill sergeant | `gruff male drill sergeant in his fifties, weathered gravelly baritone, hoarse edge` | `SHOUTING with parade-ground authority, hard clipped cadence` |
| Cyberpunk hacker girl | `playful young female cyberpunk hacker in her early twenties, wry sassy tone, light Japanese-accented English, gamer energy` | `cocky playful hype, smirking delivery` |
| Movie trailer | `booming male cinematic trailer announcer, rich low chest voice, epic theatrical gravitas, slow deliberate pacing` | `epic trailer intensity, grand declarations` |
| Cold villain | `cold male villain in his fifties, quiet measured baritone, clipped precise diction, detached menace` | _(leave empty — quiet villains lose menace if you add shout)_ — also `--no-chinese-hype` |
| AI assistant | `neutral synthetic female assistant AI, clean even timbre, friendly professional` | _(leave empty)_ — also `--no-chinese-hype` |

## File layout

```
voxcpm-voice/
├── SKILL.md                  # The Claude Code skill definition
├── scripts/
│   ├── setup.sh              # Idempotent venv installer
│   └── generate_voice.py     # CLI generator
└── README.md                 # This file
```

After setup runs, the following is created in your home directory:

```
~/voxcpm-voice/
├── voxcpm-venv/              # Python venv with voxcpm + deps
└── outputs/                  # Generated WAVs land here
```

## Troubleshooting

**First run appears stuck for a minute.** Normal. `VoxCPM.from_pretrained()` is downloading the model (~2 GB) from HuggingFace. Progress is on stderr. Subsequent runs skip this.

**Voice sounds generic / nothing like the description.** Description is too abstract. Rewrite with concrete traits (age band, gender, timbre, accent). Re-roll.

**Sentences run together.** Voice design produced <200 ms gaps that didn't qualify for padding. Add `[breath]` or `[quick_breath]` between sentences via `--lines`, or lower `--min-gap-ms` in `generate_voice.py`.

**`torch` / MPS error on Apple Silicon.** The script sets `PYTORCH_ENABLE_MPS_FALLBACK=1`. If that's not enough, edit `generate_voice.py` to force CPU before `from_pretrained()`: `import torch; torch.set_default_device("cpu")`.

**Voice drifts between sentences in a single file.** Shouldn't happen — the script does one `generate()` per take. Run with `--dry-run` to confirm the prompt composition. If it still drifts, open an issue.

## Acknowledgements

- [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB — the underlying TTS model.
- Harvard sentences for the default test set (standard TTS comparison corpus).
