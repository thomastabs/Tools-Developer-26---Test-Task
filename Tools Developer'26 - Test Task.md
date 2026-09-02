# Junior Tools Software Developer — Test Task

## Overview
Thanks for your interest in joining the Tools team at our Lisbon Games Development Studio. Before we move to the technical interview, we'd like to see how you think and work through a realistic, small slice of the kind of problem you'd face on the team.

Scope this deliberately: decide what's worth building, complete it, and when you reach the edge of what you set out to build, stop there and add a short note on what you'd do next. We'd rather see clear thinking and good judgment in a small surface area than an over-engineered submission.

**You are explicitly expected to use AI tools** (Claude, ChatGPT, Cursor, Copilot, or whatever you prefer). We're not testing whether you can write code without AI — we want to see how you collaborate with it, where you trust it, where you push back, and how you verify its output. See the *AI Usage* section below.

---

## Context
Our team runs LiveOps for games with tens of millions of players. A big part of that is shipping a constant stream of content: promotional campaigns, events, and — the part that matters here — **localised in-game text**. Every string a player reads (buttons, offers, countdowns, reward descriptions) is translated into many languages and delivered to the client as a configuration file.

These files change often, and they're edited by many hands — translators, designers, engineers. A common source of pain is that a new version *looks* fine but ships a subtle regression: a translation that quietly dropped a `%@` placeholder (so the client crashes or shows a literal `%@`), a key that lost a language it used to have (so some players see English, or nothing), an empty string, or a text that's suddenly three times longer and overflows the button it lives in.

Right now, checking a new localisation version before it goes live is a slow, manual, error-prone job. We don't want to slow the team down. We want better tooling so these issues are caught before they ship.

## The Task
The team is about to ship **`localisations_1_2_1.plist`** to replace the version currently live in production, **`localisations_1_2_0.plist`**.

**Build a small tool that gives the team confidence that this new version is safe to ship.**

Both files are `.plist` (XML) files. Each contains a `version` string and a `localisations` dictionary. Each entry in `localisations` is keyed by a unique text ID (e.g. `7a794655-44e9-49d6-99c6-df936bec3fcc`) and maps language codes (e.g. `en-US`, `fr`, `pt-BR`) to the translated string for that language.

A useful tool does more than list what changed. Anyone can diff two files. The value is in helping a human answer: *"What changed, and which of those changes should I worry about?"*

Picture the person using it: a releaser on Monday morning with fifteen minutes and a ship/no-ship call to make. They can't read every string in every language. What do they need on screen?

To calibrate the bar with one example: if a translation quietly loses a `%@` placeholder, the client can crash or render literal garbage — that's a ship-blocker, and it's invisible in a line-by-line diff. **That's one class of problem. There are others in these files, and finding them is the exercise.** Some are obvious, some are subtle, and at least one is a change that *looks* alarming but is actually a fix — a tool that flags every changed string as a risk is worse than no tool at all.

We're more interested in *how you decided what was worth checking* than in how many checks you shipped. Tell us in the README, and tell us what your tool would still miss.

You decide:
- The shape of the tool (CLI, small script, library, small web UI, notebook — whatever fits).
- The language and stack. (Python is our team's default and a plus, but not a requirement.)
- Which checks are most worth building given the time budget.
- How the tool communicates its results — a human needs to act on the output, so a clear, scannable report matters more than raw output.
- What's in scope vs. explicitly out of scope.

> **What we don't want:** two failures, for opposite reasons. A tool that only re-implements `diff` and dumps every changed line — that's the floor, not the goal. And a tool that flags every change as risky, which a releaser learns to ignore within two releases. The role is about building leverage for the team, and the highest-value output is the one that points a busy releaser straight at the handful of changes that could actually break the game.

### About the inputs
- `localisations_1_2_0.plist` is the version currently live. Treat it as the baseline / source of truth.
- `localisations_1_2_1.plist` is the candidate release. It **deliberately includes a handful of seeded issues** of the kinds described above — some obvious, some subtle. Finding them is part of the exercise.
- The files are intentionally informal and reflect real-world messiness: fields may be missing, inconsistent, or contradictory. Part of the exercise is deciding which of those cases your tool should defend against, and which aren't worth the time.
- You're encouraged to construct **your own additional test inputs** — at minimum one or more deliberately broken files — to demonstrate what your tool catches and to prove it doesn't fall over on edge cases.

If something feels ambiguous, make a call, document the assumption in your README, and move on.

### Recommended approach
Start with the smallest complete version you can finish confidently. If you run low on time, stop, ship the small version, and use the README to describe what you'd have done next.

## Deliverables
Submit a single Git repository (GitHub, GitLab, or a zip) containing:

1. **The tool** — runnable, with clear instructions on how to run it against the provided `localisations_1_2_0.plist` and `localisations_1_2_1.plist`, plus any additional inputs you created to demonstrate what it catches.
2. **A short README** (max ~1 page) covering:
   - What problem you decided to focus on and why.
   - How you decided what was worth checking — and what your tool does *not* catch (its blind spots).
   - What your smallest complete version was, and what you added after that.
   - Key trade-offs and scope decisions you made.
   - What you explicitly chose *not* to do, and what you'd build next with another day.
   - Any assumptions you made about how the team would use this.
3. **A "Findings" note** (max ~1 page) — if you were handing this to the team on Monday morning, what would you tell them about the issues you found in `localisations_1_2_1.plist`, which are the highest-risk, and how would you propose the team uses a tool like this (manual step before release, part of CI, a pre-merge check, etc.)?
4. **An AI usage write-up** (see below).

## AI Usage — What We Want to See
This is the part most candidates under-invest in. Please don't.

We'd like a short document (`AI_USAGE.md`, ~1 page) that walks us through how you used AI on this task. Concretely:

- **What you used it for** (understanding the problem, exploring options, generating code, writing tests, writing docs, reviewing your own work, etc.).
- **Two or three specific moments** where AI gave you something you kept, and two or three moments where it gave you something you rejected or rewrote — and why.
- **How you verified its output** when it mattered.
- **Anything surprising** — places where AI saved you significant time, or places where it led you down a wrong path before you caught it.

You're welcome to include raw transcript excerpts or links to chat logs. They're useful but not required — a thoughtful write-up is more valuable than a wall of unedited transcript.

We are **not** looking for "I avoided AI" or "I used AI for everything." We're looking for evidence that you're a thoughtful operator of these tools — which is exactly how you'll be expected to work on the team.

Whatever you use, **you remain responsible for the final result.** Whether code is AI-generated or hand-written, you should understand it and be ready to walk us through your tool, your decisions, and why it's correct in the technical interview.

## What We're Evaluating
Roughly in priority order:

1. **Problem framing & judgment** — Did you scope something realistic and useful, or try to boil the ocean? Did you make defensible trade-offs about what to build and what to skip?
2. **Product mindset** — Did you build something that actually helps a teammate make a ship/no-ship decision, or just something that runs? Does the output point at what matters?
3. **Hacker mindset** — Did you think about what actually breaks localised content in production, beyond the obvious "the text changed"?
4. **Tool quality** — Does it work? Is it something a teammate could pick up and extend? Is the code reasonable and readable?
5. **AI collaboration** — Are you a confident, critical operator of AI tooling? Do you know when to trust it and when to verify?
6. **Communication** — Can you explain what you built, why, and what you'd do next, clearly and concisely?

We are deliberately **not** evaluating: polished UI, exhaustive coverage, framework choice, or test coverage percentage. A small, sharp, well-reasoned submission beats a sprawling one every time.

## Logistics
- **Time:** ~4 hours of focused work; hard cap 6.
- **Submission:** Reply to the original email with a link to your repo (or attach a zip). Include a one-line summary of what you built.
- **Turnaround:** Please submit within 7 days of receiving this brief. If you need more time, just let us know — life happens.
- **Questions:** If anything in this brief is genuinely unclear, email us before you start. If something is *deliberately* underspecified (most of it is), make a call, document it in your README, and move on.

We're looking forward to seeing how you think.
