---
title: "Building claude-history: A Tool for Cross-Platform Claude Code Sessions"
date: 2025-12-01
draft: true
description: "How I built a CLI tool to manage Claude Code conversation history across Windows, WSL, and Linux - and why your conversation history is more valuable than you think"
categories: ["Tools", "AI"]
tags: ["claude-code", "python", "cli", "productivity"]
---

I've been using Claude Code extensively for the past few months. One day, while working on a startup consulting project, I needed to reference an analysis Claude had helped me with. I had discussed alternatives, evaluated tradeoffs, and settled on a design approach for an Architecture Decision Record (ADR). But I hadn't asked Claude to generate the usual markdown report.

The analysis was gone from my immediate context. Somewhere in the conversation history, buried across multiple platforms where I work.

This is the story of how I built `claude-history` to solve this problem.

## The Inspiration

Simon Willison's [writing on Claude](https://simonwillison.net/tags/claude/) has been consistently educational. His [Observable notebook for converting Claude JSON to Markdown](https://observablehq.com/@simonw/convert-claude-json-to-markdown) and discussions about extracting learnings from conversation history to improve future interactions caught my attention.

The idea is simple: your conversations with Claude contain valuable context - design decisions, debugging sessions, research threads. If you can extract and reference them, you can work more effectively.

Tools like [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) exist, but they didn't fit my workflow. I needed something that could:

- Filter by workspace/project, not just session IDs
- Work across Windows, WSL, and Linux VMs (where I run the same projects)
- Help me generate insights and track usage
- Link related workspaces that had been renamed or moved

## First: Prevent Data Loss

Before anything else, if you're using Claude Code, check your `~/.claude/settings.json`. By default, Claude Code [deletes conversation history after 30 days](https://github.com/anthropics/claude-code/issues/4172). I learned this the hard way.

Add this to preserve your history:

```json
{
  "cleanupPeriodDays": 99999
}
```

No point building a history tool if your history keeps disappearing.

## My Cross-Platform Reality

I work on astronomy-related projects that need to run on Windows, WSL, and Linux. My typical workflow: push code from one platform, pull and continue on another. The `claude-history` tool itself was developed this way.

This means my conversation history for a single logical project gets scattered across environments. When I needed to find that missing ADR analysis, I had to figure out: which platform was I on? When did that conversation happen?

## What I Built

`claude-history` is a single-file Python CLI with zero external dependencies. It reads the JSONL files Claude Code stores in `~/.claude/projects/` and exports them to readable Markdown.

```
$ claude-history --help
usage: claude-history [-h] [--version]
                      {lsw,lss,lsh,export,alias,stats,reset} ...

Browse and export Claude Code conversation history

positional arguments:
  {lsw,lss,lsh,export,alias,stats,reset}
                        Command to execute
    lsw                 List workspaces
    lss                 List sessions
    lsh                 List homes and manage SSH remotes
    export              Export to markdown
    alias               Manage workspace aliases
    stats               Show usage statistics and metrics
    reset               Reset stored data (database, settings, aliases)

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

EXAMPLES:

  List workspaces:
    claude-history lsw                        # all local workspaces
    claude-history lsw myproject              # filter by pattern
    claude-history lsw -r user@server         # remote workspaces

  List sessions:
    claude-history lss                        # current workspace
    claude-history lss myproject              # specific workspace
    claude-history lss myproject -r user@server    # remote sessions

  Export (unified interface with orthogonal flags):
    claude-history export                     # current workspace, local home
    claude-history export --ah                # current workspace, all homes
    claude-history export --aw                # all workspaces, local home
    claude-history export --ah --aw           # all workspaces, all homes

    claude-history export myproject           # specific workspace, local
    claude-history export myproject --ah      # specific workspace, all homes
    claude-history export file.jsonl         # export single file

    claude-history export -o /tmp/backup      # current workspace, custom output
    claude-history export myproject -o ./out  # specific workspace, custom output

    claude-history export -r user@server      # current workspace, specific remote
    claude-history export --ah -r user@vm01   # current workspace, all homes + SSH

  Date filtering:
    claude-history lss myproject --since 2025-11-01
    claude-history export myproject --since 2025-11-01 --until 2025-11-30

  Export options:
    claude-history export myproject --minimal       # minimal mode
    claude-history export myproject --split 500     # split long conversations
    claude-history export myproject --flat          # flat structure (no subdirs)

  WSL access (Windows):
    claude-history lsh --wsl                        # list WSL distributions
    claude-history lsw --wsl                        # list WSL workspaces
    claude-history lsw --wsl Ubuntu                 # list from specific distro
    claude-history lss myproject --wsl              # list WSL sessions
    claude-history export myproject --wsl           # export from WSL

  Windows access (from WSL):
    claude-history lsh --windows                    # list Windows users with Claude
    claude-history lsw --windows                    # list Windows workspaces
    claude-history lss myproject --windows          # list Windows sessions
    claude-history export myproject --windows       # export from Windows
```

The key insight was making home (where) and workspace (which) filtering orthogonal:

```bash
# Current workspace, local only
claude-history export

# Current workspace, all homes (local + WSL + Windows + SSH remotes)
claude-history export --ah

# All workspaces, all homes
claude-history export --ah --aw
```

## Workspace Aliases: Linking Scattered Projects

During development, I kept renaming the project - `claude-sessions`, `claude-conversations`, `claude-history`. Each rename created a new workspace directory in Claude's storage. Across three platforms, I had fragments everywhere.

The alias feature lets me group them:

```bash
# Create an alias
claude-history alias create claude-history

# Add workspaces by pattern from different homes
claude-history alias add claude-history claude-sessions
claude-history alias add claude-history claude-conversations
claude-history alias add claude-history --windows claude-history
claude-history alias add claude-history -r user@vm01 claude-history

# Now I can query everything together
claude-history lss @claude-history
```

Here's what that looks like - sessions from the same project across local (WSL), Windows, and a remote Linux VM:

```
SOURCE              WORKSPACE                           FILE                    MESSAGES  DATE
local               /home/sankar/.../claude-history     6c073d8e-....jsonl      2733      2025-11-30
local               /home/sankar/.../claude-history     c37a7825-....jsonl      1397      2025-11-30
windows:kvsan       /C/sankar/.../claude-history        28ff722d-....jsonl      769       2025-11-30
remote:ubuntuvm01   /remote_.../claude-history          83f96a4f-....jsonl      445       2025-11-29
```

One logical project, four different locations, unified view.

## Use Cases I Didn't Expect

### Generating Specifications from Conversations

I built an astronomy app for a Chandrayaan-3 outreach session - a simple mission design tool as an educational aid. Claude made iterative development easy, but there were no upfront specs.

Later, I used `claude-history` to export the conversations and create documentation. The history captures the *problem space* - what I needed and wanted. The code captures the *solution*. For a specification, you want to stay in the problem domain describing needs, not implementation details.

### Time Tracking

The `stats --time` command calculates active Claude time per project:

```
$ claude-history stats @claude-history --time

TIME TRACKING
======================================================================
Total work time: 34h 52m
Work periods: 46
Session files: 51
Date range: 2025-11-20 to 2025-11-30

Daily Breakdown:
Date            Work Time    Periods   Messages
----------------------------------------------
2025-11-30         8h 33m          5       2735
2025-11-29          5h 5m          7       1945
2025-11-23         3h 28m          7        928
2025-11-22         5h 32m          7       1727
...
```

This helped with my consulting project - I had a rough sense of time spent, but Claude gave me realistic figures. Note that this measures *active interaction time*. Requirements gathering, meetings, and thinking happen outside the tool.

## A Design Decision: Stdlib Only

Early in development, I explored adding CLI interactivity - things like interactive menus, colored output, progress bars. Libraries like `rich` or `click` could have helped, but they'd introduce external dependencies.

I decided against it. The tool stays Python standard library only - a single file you can copy anywhere and run. No `pip install`, no virtual environments, no dependency conflicts.

This constraint shaped the design in good ways. The output is plain text that pipes well to other tools. The code stays focused. And when I need to run it on a new machine, I just copy the file.

## The Meta Moments

Building a tool to analyze Claude Code conversations *using* Claude Code creates interesting loops:

- I used `claude-history` to test itself across platforms
- I exported conversations and fed them back to Claude for insights on my own usage patterns
- The development history became test data

Looking at the exported sessions, you can see the project evolving - command-line arguments changing as I iterated on what felt intuitive, features emerging from actual use rather than upfront planning.

## Getting Started

The tool is available on GitHub: [github.com/kvsankar/claude-history](https://github.com/kvsankar/claude-history) (MIT License)

```bash
# Download and make executable
curl -O https://raw.githubusercontent.com/kvsankar/claude-history/main/claude-history
chmod +x claude-history

# List sessions from current project
./claude-history lss

# Export current project to markdown
./claude-history export
```

For Windows, run with `python claude-history lss`.

## Acknowledgments

Thanks to Simon Willison for his consistently high-signal, educational writing on working with LLMs. His posts on conversation extraction and using history for better context directly inspired this project.

---

Your Claude Code conversation history is more valuable than you might think. It contains design decisions, debugging sessions, research threads, and iterative refinements. With a bit of tooling, you can search it, learn from it, and reference it when that context matters most.

*Built with Claude Code*
