---
title: "Investigating the Starlink Photo: When Could WorldView-3 Take the Shot?"
date: 2025-12-26
draft: true
description: "A deep dive into satellite conjunction analysis after SpaceX partnered with Vantor to photograph an anomalous Starlink satellite - and what I learned about the limits of public orbital data"
categories: ["Space", "Tools"]
tags: ["satellites", "orbital-mechanics", "starlink", "tle", "spacex"]
---

**STATUS: DRAFT - PENDING REVIEW**

---

On December 17, 2025, Starlink satellite 35956 experienced an anomaly. Within a day, SpaceX had partnered with Vantor to photograph the tumbling satellite from orbit using WorldView-3. The image, taken from 241 km away, showed the satellite was "largely intact."

A comment on LinkedIn caught my attention: *How quickly could they take this photo?*

I decided to find out.

## The Event

The [official Starlink announcement](https://x.com/Starlink/status/2001691802911289712) reported that satellite 35956 had lost communications and was venting propellant. SpaceX would deorbit it. [LeoLabs detected "tens of objects"](https://gizmodo.com/a-starlink-satellite-is-tumbling-toward-earth-after-a-strange-anomaly-in-orbit-2000701874) in the vicinity, though SpaceX described it as a "small number" of trackable debris.

The next day, [Michael Nicolls](https://x.com/michaelnicollsx/status/2002419447521562638), VP of Starlink Engineering, shared an image:

{{< twitter user="michaelnicollsx" id="2002419447521562638" >}}

> "Imagery collected by Vantor's WorldView-3 satellite about 1 day after the anomaly shows that Starlink Satellite 35956 is largely intact. The 12-cm resolution image was collected over Alaska from 241 km away."

[Vantor's LinkedIn post](https://www.linkedin.com/posts/vantortech_we-partnered-with-spacex-to-rapidly-image-activity-7408186335267540992-68ML) confirmed the rapid partnership.

This raised a natural question: What determines when two satellites can get close enough for imaging?

## Building SatToSat

I built [SatToSat](https://github.com/kvsankar/sattosat), a tool to explore satellite conjunctions. Given any two satellites, it finds their close approaches over a time window using public Two-Line Element (TLE) data and SGP4 propagation.

This was a ["vibe engineered"](https://simonwillison.net/2025/Oct/7/vibe-engineering/) project - Simon Willison's term for responsible AI-assisted development, as distinct from Andrej Karpathy's ["vibe coding"](https://x.com/karpathy/status/1886192184808149383) where you "forget that the code even exists." I built it with [Claude Code](https://claude.ai/code) and [OpenAI Codex](https://openai.com/index/openai-codex/). These AI coding tools have matured significantly over the past few months, and what might have taken weeks of wrestling with Three.js and orbital mechanics libraries came together in days. The iteration cycle of "describe what I want → review generated code and app → refine" has become remarkably productive.

![SatToSat main view showing WorldView-3 and Starlink orbits](/images/starlink-photo/main-view.png)

The repository has two parts:

**1. [Web UI](https://kvsankar.github.io/sattosat/)** - An interactive 3D visualization for exploring orbits and conjunctions manually. Select any two satellites from the catalog, see their orbital paths, and browse close approaches on a timeline.

**2. [Analysis Scripts](https://github.com/kvsankar/sattosat/blob/master/USAGE_SCRIPTS.md)** - Python and TypeScript scripts for deeper investigation:
   - *[Conjunction analysis](https://github.com/kvsankar/sattosat/blob/master/USAGE_SCRIPTS.md#find-conjunctions-using-a-profile)*: I implemented the conjunction algorithm in both TypeScript (for the web app) and Python (for verification). Comparing outputs confirmed they match within 27 meters.
   - *[Envelope period analysis](https://github.com/kvsankar/sattosat/blob/master/USAGE_SCRIPTS.md#analyze-envelope-periods)*: Scripts to analyze the periodic "envelope" pattern of close approaches between satellite pairs (more on this below).

The core conjunction algorithm:
1. Load TLEs for both satellites
2. Propagate positions at 30-second intervals over ±3 days
3. Find local minima in the distance function
4. Refine to 100ms precision using ternary search

## My Findings

Loading WorldView-3 (NORAD 40115) and Starlink-35956 (NORAD 66620) into SatToSat, I searched for conjunctions on December 17-19. The results:

| # | Time (UTC) | Distance | Location |
|---|------------|----------|----------|
| 1 | Dec 17 12:19 | 204 km | Atlantic Ocean (53°N, 17°W) |
| 2 | Dec 19 01:30 | 350 km | Sea of Okhotsk (55°N, 146°E) |
| 3 | Dec 18 23:55 | 981 km | Pacific (47°N, 167°E) |

The Dec 19 01:30 UTC conjunction is December 18 evening in US time zones (5:30 PM PST) - fitting the "about 1 day after" description.

But wait. The reported distance was **241 km over Alaska**. Neither match.

## The Discrepancy

| Metric | Reported | Calculated |
|--------|----------|------------|
| Distance | 241 km | 204 km (Dec 17) or 350 km (Dec 18 US time) |
| Location | Alaska | Atlantic or [Sea of Okhotsk](https://www.google.com/maps/@54,146,5z) |

I also searched specifically for approaches while WorldView-3 was over Alaska. The closest: **1,157 km** on Dec 18 23:54 UTC over the western Aleutians. Nowhere near 241 km.

What explains this gap?

### TLE Lag Doesn't Explain It

Looking at the TLE history for Starlink-35956:

| Date | Mean Motion (rev/day) | Notes |
|------|----------------------|-------|
| Dec 17 (pre-anomaly) | 15.493 | Normal |
| Dec 18 (all TLEs) | 15.493 | Still "normal"! |
| Dec 19 22:47 UTC | 15.452 | **Decay visible** |

The Dec 18 TLEs still showed the **pre-anomaly orbit**. The orbital decay only appeared in TLEs generated on Dec 19 - a full 26-hour lag.

But here's the thing: **I was already using those Dec 18 TLEs**. Even with those, I calculated 350 km over the Sea of Okhotsk, not 241 km over Alaska.

I also tested with the post-anomaly TLE (Dec 19 22:47 UTC, showing orbital decay) back-propagated to Dec 17-19:

| TLE Used | Dec 18 23:55 Distance | Best Approach |
|----------|----------------------|---------------|
| Normal TLEs | 981 km | 204 km (Dec 17) |
| Post-anomaly TLE | 650 km | 190 km (Dec 19 00:42) |
| **Reported** | **241 km** | **Alaska** |

The post-anomaly TLE gives closer results (650 km vs 981 km on Dec 18), but still nowhere near 241 km over Alaska. The discrepancy isn't about TLE lag or epoch selection.

### What's Really Going On

The mismatch suggests something more fundamental:

1. **Different orbital reality**: SpaceX had real-time tracking of their satellite's actual position - not a smoothed orbital fit from hours ago. The anomaly (tank venting, tumbling) likely changed the orbit in ways that public TLEs never captured.

2. **Different pass entirely**: The Alaska approach at 241 km may have been a different conjunction altogether - one that only existed in the satellite's true, post-anomaly orbit.

Starlink orbital data comes from multiple sources: [SpaceX publishes ephemerides](https://docs.space-safety.starlink.com/docs/tutorial-basics/trajectories/) to their space-safety portal (updated roughly every 30 minutes) and to Space-Track.org. The [18th Space Defense Squadron](https://www.space-track.org/documentation) also tracks satellites using the Space Surveillance Network. [Celestrak's supplemental GP data](https://celestrak.org/NORAD/elements/supplemental/) is derived from SpaceX's public ephemerides.

Even these public sources—with update cadences measured in minutes to hours—may not capture a satellite's true trajectory during an anomaly with rapid orbital changes from tank venting and tumbling. SpaceX's internal operations likely had real-time telemetry showing an orbit that never appeared in any public data.

## Understanding the "Beat Period"

Even with accurate orbital data, imaging opportunities don't occur continuously. There's a rhythm to how often two satellites get close.

![Distance envelope showing the scallop pattern over 6 days](/images/starlink-photo/envelope-wv3-starlink-healthy.png)

This graph shows the distance between WorldView-3 and a healthy Starlink satellite (Starlink-32153, NORAD 60330) over 6 days. Notice the pattern:
- Close approaches occur roughly every **47 minutes** (half the orbital period)
- But the **closest** approaches repeat every **~51 hours**

This "envelope period" - the time between the deepest dips - is what matters for imaging. You might get 8 close approaches within 6 hours, but only one of those will be close *enough*.

### The Physics

The envelope period follows the **synodic period formula**:

$$T_{envelope} \approx \frac{T_a \times T_b}{|T_a - T_b|}$$

Where $T_a$ and $T_b$ are the orbital periods. For WorldView-3 (~97 min) and a healthy Starlink (~94 min), this gives ~51 hours.

Satellites in similar orbits have long envelope periods - the tiny speed difference means it takes days for one to "lap" the other. Different inclinations or altitudes create shorter periods.

| Pair Type | Envelope Period | Why |
|-----------|-----------------|-----|
| Sun-sync vs LEO (WV3-Starlink) | ~51 hrs | 45° inclination difference |
| Same constellation | Never close | Identical orbital planes |
| ISS vs NOAA-20 | ~18 hrs | 47° inclination difference |

![ISS vs NOAA-20 envelope - much shorter period due to inclination difference](/images/starlink-photo/envelope-iss-noaa.png)

### An Interesting Detail

On December 17 around 17:32 UTC, WorldView-3 performed an orbital adjustment - raising its altitude by 2.7 km and reducing eccentricity by 67% (a circularization burn). This *decreased* the beat period with Starlink by about 4 hours.

Was this routine station-keeping, or something else? Without Maxar's operational logs, I can't say.

## What This Means

For the Starlink-35956 imaging:

1. **The ~1-day timeline was achievable.** With a ~42-hour envelope period (shorter due to the anomalous satellite's lower altitude), a close approach would occur within a day of any given moment.

2. **Public TLE data has limits.** During satellite anomalies, TLEs lag reality by hours to days. The 110 km discrepancy isn't a calculation error - it's a data accuracy problem.

3. **Internal tracking is essential.** SpaceX knew the actual orbit; I was working with yesterday's data.

## SatToSat: The Tool

Beyond this investigation, SatToSat is useful for exploring satellite conjunctions generally:

- **[Select any two satellites](https://github.com/kvsankar/sattosat/blob/master/USAGE_UI.md#satellite-selection)** from the catalog (~14,000 tracked objects)
- **[Visualize close approaches](https://github.com/kvsankar/sattosat/blob/master/USAGE_UI.md#close-approaches-panel)** on a 3D globe with orbital paths
- **[Analyze distance patterns](https://github.com/kvsankar/sattosat/blob/master/USAGE_UI.md#fullscreen-distance-graph)** with zoomable graphs
- **[View relative geometry](https://github.com/kvsankar/sattosat/blob/master/USAGE_UI.md#ab-relative-view)** - what Satellite A "sees" when looking at Satellite B

![Close approaches list showing conjunction times and distances](/images/starlink-photo/close-approaches-list.png)

It's educational for understanding orbital mechanics: why some satellites get close frequently, why others never do, and how inclination, altitude, and RAAN affect conjunction patterns.

[Try SatToSat](https://kvsankar.github.io/sattosat/) | [Source Code](https://github.com/kvsankar/sattosat)

## Conclusion

When I started this investigation, I expected to verify the reported 241 km distance. Instead, I learned something more interesting: during satellite anomalies, public orbital data becomes unreliable precisely when it matters most.

The tools work. The algorithms are [verified](https://github.com/kvsankar/sattosat/blob/master/USAGE_SCRIPTS.md#compare-python-vs-typescript-results) (I cross-checked Python and TypeScript implementations - they match within 27 meters). But garbage in, garbage out.

For routine conjunction analysis, public TLEs are fine. For an emergency imaging of a tumbling, venting satellite? You need the source.

---

*The [investigation details](https://github.com/kvsankar/sattosat/blob/master/python/investigation/README.md), [analysis scripts](https://github.com/kvsankar/sattosat/blob/master/USAGE_SCRIPTS.md#starlink-35956-investigation), and [envelope analysis](https://github.com/kvsankar/sattosat/blob/master/USAGE_SCRIPTS.md#analyze-envelope-periods) are available in the [SatToSat repository](https://github.com/kvsankar/sattosat).*
