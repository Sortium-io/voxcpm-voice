# voxcpm-voice

**Ship the next thing you're building with a full cast of voices you own — no voice actors, no studio time, no recording sessions.** By the end of today you'll have characters, narrators, announcers, and AI personalities saved in a local library that you can call on any time, for any line, and hear back the same voice every time. Your game, app, video, or podcast gets a voice cast that's ready whenever you are.

You'll describe what you want in plain English and get a working voice in under a minute. You'll pick the takes you love and keep them forever. You'll hand over a script of 500 lines and watch them render in the same character you saved last week. If you have a recording of a real voice — your own, a friend's, a voice actor's demo reel — you'll turn it into a reusable asset in seconds.

---

## What you'll walk away with

**A voice cast that's uniquely yours.** Not stock TTS that sounds like every other app. Characters you designed or cloned, each one distinct, each one a permanent asset you control.

**The same voice, every single time.** Once a voice is in your library, every line you generate in it sounds like the same speaker. No drift across a session. No drift across months. Voice number 17 in your script sounds like voice number 1.

**Speed you can build a project around.** A voice in a minute. A voiceline in seconds. A 200-line VO bank in a coffee break. No retakes, no scheduling, no emails chasing files.

**Your own voice (or anyone's) as an asset.** Drop in a clean 15-second recording and the voice is yours to use forever. Add a transcript for the highest fidelity reproduction.

**Delivery control when you need it.** *"Urgent, hushed."* *"Slower, menacing."* *"Cheerful, fast."* You tell the line how to be delivered without changing who's speaking.

**A library that compounds.** Every voice you add, every line you ship, sticks around. Your next project starts with everything you built in the last one.

**Outputs that live inside your project.** Run one init command and your rendered VO lands in a `vo/` folder next to your code — check the scripts into git, ship the audio with your builds, keep it all version-controlled.

---

## Get set up

```bash
claude plugin marketplace add Sortium-io/voxcpm-voice
claude plugin install voxcpm-voice
```

Restart your Claude Code session. Your first voice will auto-install the backing model (~2 GB, one-time). From then on, you're in seconds-per-voice territory.

Works on **macOS, Linux, and Windows**. If `nvidia-smi` is on your PATH (Linux or Windows with an NVIDIA card), the installer pulls CUDA 12.1 PyTorch wheels automatically — generation is dramatically faster on GPU. Apple Silicon uses MPS; anything else falls back to CPU (still works, just slower).

You'll need: [Claude Code](https://claude.com/claude-code), Python 3.10+, ~3 GB free disk. GPU helps but isn't required.

### Updating or starting over

```bash
claude plugin uninstall voxcpm-voice && claude plugin install voxcpm-voice   # update
claude plugin marketplace remove voxcpm-voice                                  # forget the marketplace
rm -rf ~/voxcpm-voice                                                          # nuke the library + venv
```

---

## Your first voice, in about a minute

Open a Claude Code session and say:

```
Use voxcpm-voice. I want a gruff male drill sergeant in his fifties —
weathered gravelly baritone, shouted parade-ground commands, hoarse edge.
Give me 3 takes so I can pick.
```

Three takes land in `~/voxcpm-voice/voices/Drill_Sergeant/samples/`. Play them. When one's the one, say:

```
Save take 2 as the drill sergeant's reference.
```

You just built a reusable character. The drill sergeant is now yours, forever, for any future line.

## Put that voice to work

```
Have the drill sergeant say: "Get your gear and move out, recruits!"
```

Output at `~/voxcpm-voice/voices/Drill_Sergeant/lines/`. Do it again with a different line. And again. Every line comes back in the same voice — locked timbre, locked cadence, locked identity.

### When you've got a whole script

Hand over a batch:

```
Render these lines for the drill sergeant:
- "Fall in!"
- "Show me some hustle!"
- "Water discipline. Check your canteens."
- "On my mark."
```

Or point at a YAML file if you're working from a real script. The template is at `${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/templates/voicelines.yaml` — copy, fill in, tell Claude to render it. One model load renders the whole batch. Scales from 3 lines to 300.

YAML also lets you mix voices — a drill sergeant line, a hacker kid's quip, an announcer's punctuation, all rendering together. Whole scenes in one pass.

### When you need a specific delivery

Say the delivery you want:

```
Have Sam say "we need to regroup" — urgent and low.
```

The skill shifts the delivery while keeping the voice identifiably the same speaker. Use it when a line needs to land a specific way. Skip it when you want pure reproduction of the saved voice.

---

## Use it inside a project

When you're building a game, app, or video and you want the rendered voicelines to live in the project itself (version-controlled, next to your source), tell Claude:

```
Set up voxcpm-voice in this project.
```

You'll end up with a `vo/` folder at the project root:

```
your-project/
└── vo/
    ├── README.md          # layout notes
    ├── audio/             # rendered WAVs land here
    └── scripts/
        └── example.yaml   # starter VO batch — edit this
```

From then on, when you render voicelines inside the project, Claude writes them to `vo/audio/<voice>/<line>.wav`. The voice library itself (character designs, reference audio, design takes) stays in your home directory where every project can share it — only the rendered output goes into the project.

Edit `vo/scripts/example.yaml` with your actual lines, then:

```
Render vo/scripts/example.yaml into this project's vo/audio.
```

Check the YAML scripts into git. Gitignore `vo/audio/` if the WAVs get too heavy to track.

## Already have a voice you want to use?

If you've got a recording of a voice you want to clone — your own, a friend's, a voice actor's demo, a clean sample from anywhere — hand it over:

```
Import this audio as a voice called Narrator_Sam:
  file: ~/Desktop/sam-intro.mp3
  transcript: "Hello, this is Sam reading a calibration paragraph."
```

That's it. Sam is now in your library, same as a designed voice. Generate voicelines, batch via YAML, add direction. The transcript is optional but worth including — with it, every future line reproduces Sam's voice with the highest fidelity.

What makes a good reference clip:
- 10–25 seconds of clean speech
- Minimal background noise, no music
- A delivery that matches how you'll use the voice (calm clips make calm clones)

---

## Prompts that work

Design:
- *"Make me a cyberpunk hacker girl — early twenties, sassy, mild Japanese accent."*
- *"Cold villain for a cartoon. Male, middle-aged, deliberate."*
- *"Arena announcer for my FPS."*
- *"Audition a grizzled detective narrator."*

Import:
- *"Clone this clip as Narrator_Sam — here's the transcript."*
- *"Turn this recording into a voice called Mom."*

Use:
- *"Have the drill sergeant say 'fall back, now!' — urgent."*
- *"Narrate these ten paragraphs in Sam's voice."*
- *"Render all the lines in ~/my-script.yaml."*

Manage:
- *"What voices have I saved?"*
- *"Re-roll the drill sergeant, deeper this time."*

If a description is too thin, Claude will ask 2–3 follow-ups (gender, age, accent, emotion). If it's concrete, it just runs.

---

## Tips that actually move the needle

**Concrete beats vague every time.** *"Baritone around 100 Hz, gravelly, mid-forties, slight Boston accent"* gets you a specific voice. *"Cool deep voice"* gets you a generic one. Age, gender, timbre, accent, archetype — that's what lands.

**Re-roll before you rewrite.** The model is stochastic — take 2 might be perfect without any prompt change. Ask for another roll before you touch the description.

**Once a voice is saved, never re-design it for new lines.** Ask for voicelines instead. Your saved voice is locked to its reference; re-designing starts from scratch and drifts.

**Exclamation marks carry real weight.** If a voice feels flat, punctuate harder. `"Move out! Now!"` lands harder than `"Move out now."` — same meaning, different delivery.

**Direction shifts timbre too, not just energy.** Use it for "say this line this way", not for "make this voice generally more X". For persistent timbre shifts, re-design the voice.

---

## Your voice library, on disk

Everything you build lives at `~/voxcpm-voice/voices/`:

```
~/voxcpm-voice/voices/<voice_name>/
├── voice.json        metadata, spoken transcript, timestamps
├── reference.wav     the anchor every future line clones from
├── samples/          (designed voices) the rolls from each design session
└── lines/            every line the voice has ever spoken
    └── <batch>/      optional grouping for VO banks
```

Designed voices get their `reference.wav` by saving one of the rolls. Imported voices get theirs directly from the file you handed in. Re-designing overwrites `samples/` but leaves `reference.wav` and everything in `lines/` alone — your work is safe.

---

## What's running under the hood

You're driving [VoxCPM2](https://github.com/OpenBMB/VoxCPM), an open-source multilingual TTS model, in three modes picked automatically:

- **Voice Design** — text only, invents a voice from your description.
- **Ultimate Cloning** — reference audio + its transcript, reproduces a voice with maximum fidelity.
- **Controllable Cloning** — reference audio only (or when you pass a direction), timbre locks while delivery shifts.

The skill handles all the config — model parameters, prompt format, Chinese-language style directives that commit harder than English equivalents (a bilingual-model quirk worth a long blog post), silence padding between sentences. You don't think about any of it.

---

## Skip Claude if you want (direct CLI)

Everything Claude runs is also a plain Python script you can call yourself.

```bash
# scaffold vo/ inside a project
.../init_project.py --path ~/projects/my-game

# design from text
.../generate_voice.py --voice-name Drill_Sergeant \
  --voice-fantasy "gruff male drill sergeant in his fifties, gravelly baritone, hoarse edge" \
  --emotion "SHOUTING with parade-ground authority" --takes 3

# import from audio
.../import_voice.py --voice-name Narrator_Sam --audio ~/sam.mp3 --text "..."

# save a designed take
.../save_take.py --name Drill_Sergeant --take 2

# speak (single line, or --lines, or --yaml batch, optional --direction, optional --output-dir)
.../speak.py --voice Drill_Sergeant --text "Get your gear and move out!"
.../speak.py --voice Narrator_Sam --text "..." --direction "slower, whispered"
.../speak.py --yaml ~/projects/my-game/vo/scripts/example.yaml \
              --output-dir ~/projects/my-game/vo/audio

# list
.../list_voices.py
```

All scripts live at `${CLAUDE_PLUGIN_ROOT}/skills/voxcpm-voice/scripts/`. Full flag reference in [SKILL.md](skills/voxcpm-voice/SKILL.md).

---

## If something's off

**First run looks frozen.** You're downloading a ~2 GB model. Let it cook.

**The voice came out generic.** Description was too vague. Add concrete traits — age, gender, timbre, accent — and re-roll.

**"No reference.wav yet" on speak.** You haven't saved a take for that voice, or the import didn't complete. Run save_take (for designed) or re-run import_voice (for imported).

**Sentences run together.** VoxCPM's pauses were too short for the padder. Add `[breath]` tags between sentences in `--lines`, or drop `--min-gap-ms` in the script.

**Apple Silicon MPS error.** `PYTORCH_ENABLE_MPS_FALLBACK=1` is already set. If torch still complains, force CPU by adding `torch.set_default_device("cpu")` at the top of the generate/speak scripts.

---

## Credits

- [VoxCPM2](https://github.com/OpenBMB/VoxCPM) by OpenBMB — the underlying TTS model.
- Harvard sentences for the default test set (standard TTS comparison corpus).
