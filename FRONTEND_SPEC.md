# Ferric, Frontend Spec

## Overview

This is the authoritative frontend specification for Ferric, built for the Ready, Spec, Ship Hackathon sponsored by Kiro. It covers three surfaces: the public landing page, the drift report viewer that the `ferric drift` command generates, and the docs site. It sits alongside CLAUDE.md, which holds the design system values and code rules, and BUILD_GUIDE.md, which holds build order.

Ferric is a recording and replay layer for LLM and agent traffic. You wrap a model client in one line, it captures every prompt, tool call and response into a cassette on disk, then replays those cassettes in CI with no network access and no API spend. The design job is to make an invisible testing layer feel like physical evidence.

Read this file in full before writing any component.

---

## Confirmed Decisions

Every value below was confirmed through the gate system. Nothing here is an assumption.

**Design read:** a technical developer tool landing page with a cold forensic direction, evidence over persuasion, and one scroll-driven moment that demonstrates the product rather than describing it.

**Dials:** DESIGN_VARIANCE 8, MOTION_INTENSITY 8, VISUAL_DENSITY 5.

**Fingerprint:** top-left lead bottom-right support / compressed statement / monochrome plus single pop / technical grid / editorial stagger / scroll-driven narrative.

**Trends:** Surveillance Design primary, Blueprint Design supporting, expressed at intensity 8 per the DESIGN_VARIANCE mapping. Surveillance contributes the monospace system-log language, timestamps, status labels and recorded-session framing. Blueprint contributes the annotated cassette anatomy diagram in Section 6 and the measurement-line treatment on the technical grid.

**Gate 1, aesthetic:** bold brutalist.
**Gate 2, nav:** A4 dual-pill split nav.
**Gate 3, background:** Option 5 static but atmospheric, no ambient background animation.
**Gate 3, transitions:** Option D GSAP pinned scroll in Section 4 only, Option B staggered viewport reveal in every other section.
**Gate 4, fonts:** Big Shoulders Display, Geist, Martian Mono.
**Gate 5, palette:** graphite and bone with amber pop.
**Gate 6, hero:** headline top-left, live recorder readout bottom-right.
**Gate 7, sections:** eight, listed in Section Order below.

---

## Global Rules

**Font import, single line:**
```html
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@400..900&family=Geist:wght@300..600&family=Martian+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
```

Three families, the cap set by the skill file. Big Shoulders Display is a variable grotesk with a genuine weight axis from 400 to 900, which is what makes the scroll-driven weight shift in Section 3 possible with no JavaScript.

**Typography scale:**
```
display-xl:  font-display, clamp(3.5rem, 9vw, 8rem), leading-[0.86], tracking-[-0.03em], weight 800, uppercase
display-lg:  font-display, clamp(2.5rem, 6vw, 5rem), leading-[0.9], tracking-[-0.02em], weight 700, uppercase
display-md:  font-display, clamp(2rem, 4vw, 3.25rem), leading-[0.95], tracking-[-0.02em], weight 700, uppercase
heading:     font-body, 1.125rem (18px), leading-[1.3], weight 500
body-lg:     font-body, 1.0625rem (17px), leading-[1.6], weight 400
body:        font-body, 0.9375rem (15px), leading-[1.65], weight 400
body-sm:     font-body, 0.8125rem (13px), leading-[1.5], weight 400
data-xl:     font-mono, clamp(2rem, 4vw, 3rem), leading-[1], weight 500, tabular-nums
data:        font-mono, 0.8125rem (13px), leading-[1.55], weight 400
data-sm:     font-mono, 0.6875rem (11px), leading-[1.4], weight 400
label:       font-mono, 0.625rem (10px), leading-[1], weight 500, tracking-[0.2em], uppercase
```

Body copy is capped at 68 characters per line everywhere. Headings use `text-wrap: balance`, paragraphs use `text-wrap: pretty`.

**Colour palette, graphite and bone with amber pop:**
```css
:root {
  --bg-primary:     #0b0b0c;
  --bg-secondary:   #121214;
  --bg-surface:     #17171a;
  --bg-elevated:    #1e1e22;
  --accent:         #ffb020;
  --accent-hover:   #ffc352;
  --accent-glow:    rgba(255, 176, 32, 0.12);
  --text-primary:   #ededea;
  --text-secondary: #9a9a94;
  --text-muted:     #5c5c57;
  --border-subtle:  rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.11);
  --border-strong:  rgba(255, 255, 255, 0.18);
  --signal-fail:    #ff5c46;
}
```

Colour strategy is Restrained: tinted neutrals plus one accent on under 10% of the surface. Amber is the record light, so the accent carries meaning rather than taste. Green does not exist in this system. A passing assertion renders as quiet bone text at `--text-secondary`. A failing one is the only loud thing on the page. Tests should be silent when they pass.

`--signal-fail` is a state colour, not an accent. It appears in exactly three places: the failing diff row in Section 4 phase three, the failed assertion badge in Section 5, and the fail column of the drift report viewer. Nowhere else.

**Spacing scale:** 4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 160px. Use `gap-` on grids and flex, never margins between siblings.

**Radius language, held across all three surfaces:** everything is `rounded-none` except two exceptions. Pills in the nav are `rounded-full`. The status dot is `rounded-full`. Bold brutalist means hard corners, and mixing radius scales is a banned pattern. No `rounded-xl` anywhere.

**Border language:** all borders are 1px. `border-subtle` for internal dividers, `border-default` for panel edges, `border-strong` for the hero readout and any element that must read as a physical enclosure.

**Shadows:** none, with one exception. No drop shadows anywhere on the landing page or docs. The report viewer uses one tinted shadow on the sticky filter bar only: `box-shadow: 0 8px 24px -12px rgba(0,0,0,0.6)`. Generic dark shadows are banned, outer glows are banned.

**Transition standard:**
```
fast:    140ms cubic-bezier(0.16, 1, 0.3, 1)
default: 240ms cubic-bezier(0.16, 1, 0.3, 1)
slow:    620ms cubic-bezier(0.16, 1, 0.3, 1)
```

**Entrance animation standard, every below-fold element:**
```
initial:    { opacity: 0, filter: 'blur(10px)', y: 24 }
whileInView:{ opacity: 1, filter: 'blur(0px)', y: 0 }
viewport:   { once: false, amount: 0.1 }
transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] }
```

`once: false` on every single scroll animation with zero exceptions. This is the enforcement rule from the top of FRONTEND_SKILL.md. Any `whileInView` with `once: true` is a build failure, not a preference. Stagger containers use `staggerChildren: 0.08` on the parent with children driven by `variants`.

**Motion library:** `import { motion, AnimatePresence, useScroll, useTransform, useMotionValue, useSpring } from 'motion/react'`. Installed via `npm install motion`. Never `framer-motion`.

**GSAP:** used only inside `Recorder.tsx`, Section 4. Registered once in that file. Every ScrollTrigger instance killed on unmount. `toggleActions: 'play none none reverse'` so the sequence reverses on scroll up.

**Icons:** inline hand-written SVG only. No icon library, no Lucide, no emoji, no AI-generated symbols. Ferric needs six icons total: record dot, play, arrow-right, arrow-up-right, copy, check. All six are written as inline paths in `src/components/ui/Icon.tsx` with a `name` prop. Stroke width 1.5, `currentColor`, 24x24 viewBox.

**Technical grid, the page-wide background treatment:**
```css
.tech-grid {
  background-image:
    linear-gradient(to right, var(--border-subtle) 1px, transparent 1px),
    linear-gradient(to bottom, var(--border-subtle) 1px, transparent 1px);
  background-size: 64px 64px;
  background-position: -1px -1px;
}
```
Applied to the hero and Section 6 only, not every section. Section rhythm is editorial stagger, so the grid appearing and disappearing is part of the rhythm.

**Noise grain overlay, one instance, fixed, page-wide:**
```tsx
<div
  className="fixed inset-0 pointer-events-none z-[var(--z-grain)] opacity-[0.035]"
  style={{
    backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`,
    backgroundSize: '128px 128px',
  }}
/>
```

**Semantic z-index scale, declared once in `globals.css`:**
```css
:root {
  --z-base:      0;
  --z-grid:      1;
  --z-content:   10;
  --z-grain:     40;
  --z-sticky:    200;
  --z-nav:       250;
  --z-overlay:   300;
  --z-modal:     400;
}
```
No arbitrary values like 999 anywhere.

**Scrollbar, hidden globally while scrolling stays smooth:**
```css
html {
  scrollbar-width: none;
  scroll-behavior: smooth;
}
html::-webkit-scrollbar { display: none; }
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
```

**Hover states:** CSS class transitions and pseudo-classes only. No `onMouseEnter` or `onMouseLeave` setting style properties anywhere. The one permitted JS-driven pointer interaction is the magnetic hover on the hero primary CTA, which uses `useMotionValue` and `useTransform`, never `useState`.

**Backdrop blur:** applied only to `position: fixed` or `position: sticky` elements. That means the two nav pills and the report viewer filter bar. Never on a card inside a scrolling container.

**Viewport height:** `min-h-[100dvh]` everywhere. Never `h-screen`, never `min-h-screen`.

**Loading states:** skeleton shimmer, never spinners.
```tsx
<div className="relative overflow-hidden h-4 w-full bg-[var(--bg-elevated)]">
  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.06] to-transparent animate-shimmer" style={{ backgroundSize: '200% 100%' }} />
</div>
```

**Copy rules:** British English throughout. No em dashes in any string, comment, or file. No banned filler words: elevate, seamless, unleash, unlock, empower, revolutionise, transform, cutting-edge, next-gen, supercharge, streamline, leverage, discover. No placeholder data: no John Doe, no Acme, no 99.9%, no 1,234. Every number and name on these three surfaces is either real or a realistic recorded value drawn from an actual cassette.

**Reduced motion:** `prefers-reduced-motion: reduce` disables the GSAP pin in Section 4, which falls back to a plain stacked list, disables the magnetic hover, disables the scroll-driven weight shift in Section 3, and reduces every entrance animation to a plain 200ms opacity fade with no blur and no translate.

**No logo, no wordmark lockup, no brand mark.** This is a hard rule for this project, not a gap waiting to be filled. The left nav pill carries a live session timecode instead of a name, specified in Section 1. Nothing on the page is a logo, so there is no slot to fill later and no comment placeholder pretending otherwise.

The product name appears in exactly three places, each time because it is functionally required rather than decorative: the browser tab title, the install command in Section 7, and the footer sign-off. A tool names itself when it tells you how to run it.

**Favicon:** an inline SVG data URI, no file, no design work. A single amber record dot on the graphite background, which is the same element already used in the nav and the hero readout. It is a system component, not a mark.
```html
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%230b0b0c'/%3E%3Ccircle cx='16' cy='16' r='6' fill='%23ffb020'/%3E%3C/svg%3E" />
```
A blank tab reads as unfinished to a judge, and this costs nothing, ships with the HTML, and cannot drift from the palette because the hex values are the palette.

---

## Section Order

| # | Section | Recipe | Layout family | Eyebrow |
|---|---|---|---|---|
| 1 | Nav | A4 dual-pill split | Navigation | no |
| 2 | Hero | editorial-asymmetric-hero, adapted | Full-viewport hero | yes |
| 3 | The untested layer | full-width-statement | Typography statement | no |
| 4 | The recorder | bespoke, GSAP pinned | Pinned sequence | no |
| 5 | What you can assert | tabbed-feature-explorer | Interactive | yes |
| 6 | Cassette anatomy | asymmetric-bento-grid, Blueprint treatment | Content grid | no |
| 7 | Install | bespoke, command-led | Convert | no |
| 8 | Footer | bespoke, hairline | Footer | no |

Seven distinct layout families across eight sections, above the minimum of four. Two eyebrows across eight sections, inside the cap of one per three. No two consecutive sections share a layout family. No zigzag split-content pattern appears at all, so the alternation cap is not in play.

Section rhythm is editorial stagger, so no two sections share a height. Section 2 is `100dvh`. Section 3 is short at `py-32`. Section 4 is `400vh` of scroll distance. Section 5 is medium. Section 6 is tall. Section 7 is short. Section 8 is minimal.

---

## Section 1, Nav

**Component:** `src/components/layout/Nav.tsx`
**Pattern:** A4 dual-pill split nav.

Two separate pills with nothing across the centre. The empty centre is the composition.

**Z-index:** `--z-nav`, 250. Fixed, does not push content.

**Structure:**
```
<header> fixed top-0 inset-x-0 z-[var(--z-nav)] px-4 md:px-8 lg:px-12 pt-4 md:pt-6 flex items-start justify-between pointer-events-none

  LEFT PILL, session timecode, not a wordmark:
    classes: pointer-events-auto flex items-center gap-2.5 rounded-full border border-[var(--border-default)] bg-[var(--bg-primary)]/70 backdrop-blur-xl px-4 py-2.5
    record dot: w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-record-pulse shrink-0
    timecode: font-mono text-[12px] tracking-[0.14em] text-[var(--text-primary)] leading-none tabular-nums

    Behaviour: the timecode counts up from 00:00:00 on mount, formatted HH:MM:SS, driven by a
    single requestAnimationFrame loop writing to a ref, never to React state, so the page does
    not re-render sixty times a second. It measures how long the visitor has been on the page.

    This is deliberately not a brand mark. It is the same element a recording device puts in
    that corner, it does real work, and it means the first thing a visitor reads is the product
    behaving rather than the product introducing itself. It also removes the single most
    recognisable AI landing page tell, the wordmark sitting top left doing nothing.

    Clicking the pill scrolls to #top, replacing the usual logo-scrolls-home affordance.
    aria-label: "Session timecode. Return to top."
    Under prefers-reduced-motion the timecode still counts, since it is information rather than
    decoration, but the record dot stops pulsing.

  RIGHT PILL:
    classes: pointer-events-auto hidden md:flex items-center gap-1 rounded-full border border-[var(--border-default)] bg-[var(--bg-primary)]/70 backdrop-blur-xl px-1.5 py-1.5
    links, 3 total: "Recorder", "Assertions", "Docs"
      each: px-3.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-[240ms] rounded-full
      active: text-[var(--text-primary)] bg-[var(--bg-elevated)]
    CTA: "GitHub"
      classes: ml-1 px-3.5 py-1.5 rounded-full bg-[var(--accent)] text-[var(--bg-primary)] font-mono text-[11px] font-medium uppercase tracking-[0.14em] hover:bg-[var(--accent-hover)] transition-colors duration-[240ms]

  MOBILE TRIGGER (replaces right pill below md):
    classes: pointer-events-auto md:hidden flex flex-col gap-[5px] rounded-full border border-[var(--border-default)] bg-[var(--bg-primary)]/70 backdrop-blur-xl p-3.5
    three bars: w-4 h-[1.5px] bg-[var(--text-primary)] transition-all duration-[240ms]
    open state: bar 1 rotate-45 translate-y-[6.5px], bar 2 opacity-0, bar 3 -rotate-45 -translate-y-[6.5px]
```

**Mobile overlay, AnimatePresence:**
```
motion.div
  initial: { opacity: 0 }
  animate: { opacity: 1 }
  exit: { opacity: 0 }
  transition: { duration: 0.28, ease: [0.16, 1, 0.3, 1] }
  classes: fixed inset-0 z-[var(--z-overlay)] bg-[var(--bg-primary)] flex flex-col justify-end px-6 pb-20 md:hidden

  each link:
    motion.a
      initial: { opacity: 0, y: 20 }
      animate: { opacity: 1, y: 0 }
      transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1], delay: index * 0.06 + 0.08 }
      classes: font-display text-5xl font-700 uppercase tracking-[-0.02em] text-[var(--text-primary)] py-2 border-b border-[var(--border-subtle)]
```

**Record pulse keyframe:**
```css
@keyframes recordPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
.animate-record-pulse { animation: recordPulse 2s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .animate-record-pulse { animation: none; opacity: 1; }
}
```

**Scroll behaviour:** the pills never gain a solid background or a shadow. They already carry `backdrop-blur-xl` over a translucent base, which is the layering treatment the skill file requires instead of a painted block.

**Entrance:** both pills, `initial: { opacity: 0, y: -16 }`, `animate: { opacity: 1, y: 0 }`, `duration: 0.6`, `ease: [0.16, 1, 0.3, 1]`, left pill `delay: 0.1`, right pill `delay: 0.18`.

---

## Section 2, Hero

**Recipe:** `editorial-asymmetric-hero` from COMPOSITION_RECIPES.md, off-grid placement retained, background image swapped for the technical grid, floating detail block promoted into the bottom-right recorder readout.
**Component:** `src/components/sections/Hero.tsx`
**Funnel job:** Hook.

Headline anchored top-left, recorder readout anchored bottom-right, empty diagonal between them. Content must fit a 1280x800 viewport with no scrolling, and the first text must appear no lower than 220px from the top.

**Z-index stack:**
```
z-[var(--z-base)]:  section background, bg-[var(--bg-primary)]
z-[var(--z-grid)]:  technical grid, absolute inset-0, .tech-grid, mask-image radial fade
z-[var(--z-content)]: content grid, relative
z-[var(--z-grain)]: global grain, owned by App.tsx
z-[var(--z-nav)]:   nav
```

**Grid mask, so the grid fades rather than terminating at a hard edge:**
```css
mask-image: radial-gradient(ellipse 90% 70% at 30% 20%, black 0%, transparent 75%);
```

**Structure:**
```
<section id="top"> relative min-h-[100dvh] overflow-hidden bg-[var(--bg-primary)] flex flex-col

  grid layer: absolute inset-0 z-[var(--z-grid)] tech-grid, masked as above

  content: relative z-[var(--z-content)] flex-1 grid grid-cols-1 lg:grid-cols-12 gap-y-12 px-4 md:px-8 lg:px-12 pt-[8.5rem] md:pt-[9.5rem] pb-10 md:pb-14

  TOP-LEFT CLUSTER (lg:col-span-7, lg:col-start-1, self-start):

    eyebrow:
      "RECORD. REPLAY. PROVE IT STILL WORKS."
      classes: font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)] mb-6 md:mb-8
      animation: initial { opacity: 0, y: 10 } animate { opacity: 1, y: 0 } duration 0.6s ease [0.16,1,0.3,1] delay 0.25s

    headline, 2 lines:
      line 1: "YOUR AI FEATURE"
      line 2: "HAS NO TEST SUITE"
      classes: font-display text-[clamp(3.5rem,9vw,8rem)] font-800 uppercase leading-[0.86] tracking-[-0.03em] text-[var(--text-primary)] max-w-[14ch] [text-wrap:balance]
      animation: word-by-word blur reveal
        per word: initial { opacity: 0, filter: 'blur(12px)', y: 34 } animate { opacity: 1, filter: 'blur(0px)', y: 0 }
        duration: 0.65s, ease [0.16, 1, 0.3, 1]
        stagger: delay = 0.35 + (wordIndex * 0.07) seconds
        implementation: <BlurText> component, splits on spaces, each word inline-block, whitespace preserved

    subhead:
      "Ferric records every prompt, tool call and response your agent makes, then replays them in CI with no network and no API spend. Assertions run on the shape of the interaction, not the wording."
      classes: mt-7 md:mt-8 max-w-[52ch] font-body text-[15px] md:text-[17px] leading-[1.6] text-[var(--text-secondary)] [text-wrap:pretty]
      animation: initial { opacity: 0, filter: 'blur(8px)', y: 18 } animate { opacity: 1, filter: 'blur(0px)', y: 0 } duration 0.7s delay 0.72s
      word count: 34, over the 25-word guidance, justified because the third sentence is the differentiator and cutting it costs the pitch. Line count on desktop is 3, inside the cap.

    CTA cluster:
      classes: mt-8 flex flex-wrap items-center gap-x-6 gap-y-4
      animation: initial { opacity: 0, y: 16 } animate { opacity: 1, y: 0 } duration 0.6s delay 0.92s
      vertical gap from subhead: 32px, inside the 40px CTA proximity cap

      primary, magnetic hover:
        label: "See it catch a regression"
        classes: group relative inline-flex items-center gap-2.5 bg-[var(--accent)] text-[var(--bg-primary)] pl-5 pr-1.5 py-1.5 font-mono text-[12px] font-medium uppercase tracking-[0.14em] hover:bg-[var(--accent-hover)] transition-colors duration-[240ms]
        trailing icon circle (button-in-button pattern):
          classes: inline-flex items-center justify-center w-7 h-7 rounded-full bg-[var(--bg-primary)]/12 group-hover:translate-x-0.5 group-hover:-translate-y-px transition-transform duration-200
          icon: arrow-up-right, 13px
        magnetic physics: useMotionValue x and y, useTransform to translate, max drift 5px, spring { stiffness: 220, damping: 18 }, reset to 0 on pointer leave, disabled under reduced motion
        anchors to: #recorder

      secondary:
        label: "Read the docs"
        classes: inline-flex items-center gap-2 font-mono text-[12px] uppercase tracking-[0.14em] text-[var(--text-secondary)] border-b border-[var(--border-default)] pb-1 hover:text-[var(--text-primary)] hover:border-[var(--accent)] transition-colors duration-[240ms]

  BOTTOM-RIGHT READOUT (lg:col-span-5, lg:col-start-8, self-end, justify-self-end):
    wrapper: w-full max-w-[420px] lg:mt-auto
    animation: initial { opacity: 0, filter: 'blur(10px)', y: 26 } animate { opacity: 1, filter: 'blur(0px)', y: 0 } duration 0.8s delay 1.05s

    panel: border border-[var(--border-strong)] bg-[var(--bg-secondary)]/85 backdrop-blur-sm
      Note: this panel is fixed relative to the page flow, not inside a scroll container, so the blur is permitted

      header row:
        classes: flex items-center justify-between border-b border-[var(--border-subtle)] px-4 py-2.5
        left: record dot w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-record-pulse, plus "RECORDING" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-secondary)]
        right: "cassette 7f3a91" font-mono text-[10px] text-[var(--text-muted)]

      meta strip:
        classes: grid grid-cols-3 divide-x divide-[var(--border-subtle)] border-b border-[var(--border-subtle)]
        each cell: px-4 py-3
          label: font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]
          value: font-mono text-[13px] text-[var(--text-primary)] mt-1.5 tabular-nums
        cells: PROVIDER / anthropic · MODEL / opus-4.6 · EVENTS / 11

      event log, 5 rows:
        row classes: flex items-baseline gap-3 px-4 py-2 border-b border-[var(--border-subtle)] last:border-0
        index: font-mono text-[10px] text-[var(--text-muted)] w-5 shrink-0 tabular-nums
        content: font-mono text-[12px] text-[var(--text-secondary)] truncate
        rows, top to bottom:
          01  user      "reconcile the march ledger"
          02  tool_call read_ledger(month="2026-03")
          03  tool_res  1842 rows
          04  tool_call flag_anomalies(threshold=0.04)
          05  assistant 3 anomalies, awaiting review
        row 05: text-[var(--text-primary)] instead of secondary, marking the newest event
        animation per row: initial { opacity: 0, x: -10 } animate { opacity: 1, x: 0 } duration 0.34s, stagger 0.11s per row, start delay 1.35s
        loading state: three shimmer bars, h-3, bg-[var(--bg-elevated)]

      footer row:
        classes: flex items-center justify-between px-4 py-2.5 border-t border-[var(--border-subtle)]
        left: "written to tests/cassettes/" font-mono text-[10px] text-[var(--text-muted)]
        right: "0 secrets" font-mono text-[10px] text-[var(--text-muted)]

  MOBILE:
    single column. Headline drops to clamp(2.75rem, 12vw, 4rem). Readout moves directly below the CTA cluster at full width with mt-12. Meta strip collapses from 3 columns to 2 with the EVENTS cell hidden. Event log truncates to 3 rows.

RESPONSIVE:
  padding: px-4 md:px-8 lg:px-12
  top padding: pt-[8.5rem] md:pt-[9.5rem]
  grid: grid-cols-1 lg:grid-cols-12
  headline: clamp handles all scaling, no breakpoint variants needed
```

**ASSET BRIEF:**
```
Type: none
The hero uses zero raster assets. The technical grid is CSS, the grain is inline SVG, the
readout is real typographic content. This is deliberate: a tool that proves things should
not lean on decorative imagery in its first viewport, and it removes an entire asset
pipeline from a nine-day build.
Fallback: not applicable.
```

---

## Section 3, The Untested Layer

**Recipe:** `full-width-statement` from COMPOSITION_RECIPES.md.
**Component:** `src/components/sections/Untested.tsx`
**Funnel job:** Educate. No CTA, this is a breath between the hero and the pinned sequence.

**Z-index:** single layer, no grid, no overlay. The grid disappearing here is part of the editorial stagger rhythm.

**Structure:**
```
<section> py-24 md:py-36 lg:py-40 px-4 md:px-8 lg:px-12 bg-[var(--bg-secondary)]
  container: w-full max-w-[1400px] mx-auto

  statement, left aligned not centred:
    "EVERY OTHER LAYER OF YOUR STACK HAS TESTS. THE MODEL CALL DOES NOT."
    classes: font-display text-[clamp(2.5rem,7vw,6.5rem)] font-700 uppercase leading-[0.92] tracking-[-0.025em] text-[var(--text-primary)] max-w-[18ch] [text-wrap:balance]
    animation: word-by-word slide-up on scroll intersection
      per word: initial { opacity: 0, y: 40 } whileInView { opacity: 1, y: 0 }
      viewport: { once: false, amount: 0.2 }
      duration: 0.55s, ease [0.16, 1, 0.3, 1]
      stagger: delay = wordIndex * 0.045 seconds
    scroll-driven weight shift, progressive enhancement:
      @supports (animation-timeline: scroll()) applies weightShift from 'wght' 800 to 'wght' 500 over animation-range: entry 0% cover 60%
      disabled under prefers-reduced-motion

  metadata line:
    "Non-deterministic output. No assertion vocabulary. Live calls in CI cost money and flake."
    classes: mt-10 md:mt-14 font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)] max-w-[60ch]
    animation: standard entrance, delay 0.3s

No images, no cards, no CTA. The emptiness is the point.
```

**Scroll-driven weight shift:**
```css
@supports (animation-timeline: scroll()) {
  @keyframes weightShift {
    from { font-variation-settings: 'wght' 800; }
    to   { font-variation-settings: 'wght' 500; }
  }
  .kinetic-statement {
    animation: weightShift linear both;
    animation-timeline: view();
    animation-range: entry 0% cover 60%;
  }
}
@media (prefers-reduced-motion: reduce) {
  .kinetic-statement { animation: none; font-variation-settings: 'wght' 700; }
}
```

---

## Section 4, The Recorder

**Recipe:** bespoke. No existing recipe covers a three-phase pinned comparison, so this is written at golden-example specificity.
**Component:** `src/components/sections/Recorder.tsx`
**Funnel job:** Educate, and it carries the entire product demonstration.

This is the one GSAP pinned section, confirmed at Gate 3. It is also the money shot. A judge who watches only this section should understand the product completely.

**Dimensions:** outer container `h-[400vh]`, inner stage `sticky top-0 h-[100dvh]`. Three phases across the scroll distance, with the final quarter held on phase three so the failing diff stays on screen.

**Z-index stack:**
```
z-[var(--z-base)]:    bg-[var(--bg-primary)], fully opaque
z-[var(--z-grid)]:    horizontal scan lines only, opacity 0.04, Surveillance Design texture
z-[var(--z-content)]: pinned stage content
```

**Scan line texture, Surveillance Design contribution:**
```css
.scanlines {
  background-image: repeating-linear-gradient(
    to bottom,
    var(--border-subtle) 0px,
    var(--border-subtle) 1px,
    transparent 1px,
    transparent 4px
  );
  opacity: 0.04;
}
```

**Structure:**
```
<section id="recorder"> relative h-[400vh] bg-[var(--bg-primary)]

  <div> sticky stage
    classes: sticky top-0 h-[100dvh] overflow-hidden flex flex-col justify-center px-4 md:px-8 lg:px-12

    scanlines: absolute inset-0 z-[var(--z-grid)] scanlines pointer-events-none

    PERSISTENT HEADER (does not animate between phases):
      classes: relative z-[var(--z-content)] w-full max-w-[1400px] mx-auto mb-10 md:mb-14
      title: "THE RECORDER" font-display text-[clamp(1.75rem,3.5vw,3rem)] font-700 uppercase tracking-[-0.02em] text-[var(--text-primary)] leading-[0.95]

      phase indicator row:
        classes: mt-6 flex items-center gap-0 border-t border-[var(--border-subtle)]
        each of 3 segments:
          classes: flex-1 border-r border-[var(--border-subtle)] last:border-r-0 pt-4
          number: font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)]
          label: font-mono text-[11px] uppercase tracking-[0.16em] mt-1.5 transition-colors duration-[240ms]
          inactive label: text-[var(--text-muted)]
          active label: text-[var(--accent)]
          active segment also renders a 1px amber progress bar along its top edge, scaleX driven by GSAP from 0 to 1 across that phase
        segments: 01 RECORD · 02 REPLAY · 03 DRIFT

    PHASE STAGE:
      classes: relative z-[var(--z-content)] w-full max-w-[1400px] mx-auto h-[min(52vh,460px)]
      all three phase panels share this absolute footprint, only one is fully visible at a time

      shared panel classes: absolute inset-0 border border-[var(--border-default)] bg-[var(--bg-secondary)] grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border-default)] overflow-hidden

      PHASE 01, RECORD:
        left column: px-6 md:px-8 py-6 flex flex-col
          label: "IN PRODUCTION" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]
          heading: "One line, then it listens" font-body text-[18px] font-500 text-[var(--text-primary)] mt-3
          body: "Wrap the client you already have. Ferric forwards every request untouched and captures the normalised event log on the way back. Secrets are stripped before anything reaches disk." font-body text-[14px] leading-[1.6] text-[var(--text-secondary)] mt-3 max-w-[46ch]
          code block: mt-auto border border-[var(--border-subtle)] bg-[var(--bg-primary)] px-4 py-3 font-mono text-[12px] text-[var(--text-secondary)]
            content: client = ferric.wrap(client)
            the token "ferric.wrap" renders in text-[var(--accent)]
        right column: px-6 md:px-8 py-6 font-mono text-[12px]
          live event log, 6 rows appearing in sequence as this phase scrubs
          row: flex gap-3 py-1.5 border-b border-[var(--border-subtle)] last:border-0
          index text-[var(--text-muted)] w-5 tabular-nums, content text-[var(--text-secondary)]
          rows: user / tool_call / tool_res / tool_call / tool_res / assistant
          a small amber record dot sits top-right of this column, animate-record-pulse

      PHASE 02, REPLAY:
        left column:
          label: "IN CI"
          heading: "Same events, no network"
          body: "Replay serves the recorded response and never opens a socket to a provider. An unmatched request fails loudly with the nearest cassette printed, it never falls through to the live model."
          code block: FERRIC_MODE=replay pytest, with "replay" in text-[var(--accent)]
        right column:
          identical 6-row event log to phase 01, visually confirming the replay matches
          difference: the amber record dot is replaced by a static "REPLAY" chip, border border-[var(--border-default)] px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]
          a narrow banner sits along the bottom of this column: "0 network calls · 0 tokens · 340ms" font-mono text-[11px] text-[var(--text-muted)] border-t border-[var(--border-subtle)] px-0 py-2.5

      PHASE 03, DRIFT:
        left column:
          label: "ON MODEL UPGRADE"
          heading: "The upgrade that would have shipped"
          body: "Run the whole cassette library against a new model version. Ferric classifies every cassette as unchanged, reworded, or behaviourally changed, and names the dimension that moved."
          code block: ferric drift --to opus-4.7, with "drift" in text-[var(--accent)]
        right column, the diff:
          three rows comparing expected against observed
          row classes: grid grid-cols-[1fr_auto] items-baseline gap-4 py-2 border-b border-[var(--border-subtle)] last:border-0
          passing rows (2): label font-mono text-[12px] text-[var(--text-secondary)], status "MATCH" font-mono text-[10px] tracking-[0.2em] text-[var(--text-muted)]
          failing row (1): label font-mono text-[12px] text-[var(--text-primary)], status "DIVERGED" font-mono text-[10px] tracking-[0.2em] text-[var(--signal-fail)]
          failing row content: "tool order: read_ledger → flag_anomalies  ·  observed: flag_anomalies → read_ledger"
          the failing row also carries a 2px left border in var(--signal-fail) and a bg of rgba(255,92,70,0.05)
          bottom banner: "1 behavioural regression across 34 cassettes" font-mono text-[11px] text-[var(--signal-fail)] border-t border-[var(--border-subtle)] py-2.5
```

**GSAP timeline:**
```
gsap.registerPlugin(ScrollTrigger)  // registered once, in this file only

const tl = gsap.timeline({
  scrollTrigger: {
    trigger: sectionRef.current,
    start: 'top top',
    end: 'bottom bottom',
    scrub: 1,
    pin: stageRef.current,
    anticipatePin: 1,
    toggleActions: 'play none none reverse',
  },
})

initial states set with gsap.set before the timeline:
  phase01: { opacity: 1, y: 0 }
  phase02: { opacity: 0, y: 28 }
  phase03: { opacity: 0, y: 28 }
  progressBar01: { scaleX: 0, transformOrigin: 'left center' }
  progressBar02: { scaleX: 0, transformOrigin: 'left center' }
  progressBar03: { scaleX: 0, transformOrigin: 'left center' }

timeline positions, total 3 units of scrub:
  0.00  progressBar01 scaleX 0 -> 1, duration 0.85
  0.85  phase01 opacity 1 -> 0, y 0 -> -22, duration 0.15
  0.85  phase02 opacity 0 -> 1, y 28 -> 0, duration 0.15
  1.00  progressBar02 scaleX 0 -> 1, duration 0.85
  1.85  phase02 opacity 1 -> 0, y 0 -> -22, duration 0.15
  1.85  phase03 opacity 0 -> 1, y 28 -> 0, duration 0.15
  2.00  progressBar03 scaleX 0 -> 1, duration 0.70
  2.70  held, no animation, so the failing diff stays fully on screen for the final 30% of scroll

phase label colour is driven by three separate ScrollTrigger callbacks toggling a data-active
attribute, not by the timeline, so the CSS transition handles the colour change

cleanup on unmount:
  tl.kill()
  ScrollTrigger.getAll().forEach(t => t.kill())
```

**Fallback:** below the `lg` breakpoint, and whenever `prefers-reduced-motion: reduce` is set, this section renders as a plain stacked list of the three phases with no pin and no GSAP, using the standard entrance animation with `staggerChildren: 0.12`. Both conditions are checked before `registerPlugin` is ever called, so GSAP is not even initialised on mobile. Outer height drops from `h-[400vh]` to `h-auto` with `py-24`.

**ASSET BRIEF:**
```
Type: none
Every element in this section is live DOM: real text, real borders, real state. No screenshots,
no mockup images, no video. This matters beyond aesthetics, the hackathon rules run a pass-or-fail
screen on simulated features presented as working functionality, and a screenshot of a diff is
exactly the kind of thing that screen exists to catch. The content shown here mirrors a real
cassette committed in tests/cassettes/.
Fallback: not applicable.
```

---

## Section 5, What You Can Assert

**Recipe:** `tabbed-feature-explorer` from COMPOSITION_RECIPES.md, right visual column replaced with a live assertion result panel rather than a screenshot.
**Component:** `src/components/sections/Assertions.tsx`
**Funnel job:** Compare. This is the differentiator section.

**Z-index:** single layer, `bg-[var(--bg-primary)]`.

**Structure:**
```
<section id="assertions"> py-24 md:py-32 px-4 md:px-8 lg:px-12 bg-[var(--bg-primary)]
  container: max-w-[1400px] mx-auto

  header:
    eyebrow: "ASSERTIONS" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)] mb-5
      (eyebrow 2 of 2 for the page, next two sections carry none)
    headline: "STRING EQUALITY WAS NEVER GOING TO WORK" font-display text-[clamp(2rem,4.5vw,3.75rem)] font-700 uppercase leading-[0.94] tracking-[-0.02em] text-[var(--text-primary)] max-w-[20ch] [text-wrap:balance]
    subhead: "Four assertion families that survive non-determinism. Each one fails on a real regression and stays quiet when the model simply reworded itself." mt-5 max-w-[58ch] font-body text-[15px] md:text-[16px] leading-[1.6] text-[var(--text-secondary)]
    animation: standard entrance, stagger 0.08

  TAB BAR:
    classes: mt-12 md:mt-16 flex gap-0 border-b border-[var(--border-default)] overflow-x-auto
    each tab button:
      classes: relative px-5 md:px-7 py-4 font-mono text-[11px] uppercase tracking-[0.16em] whitespace-nowrap transition-colors duration-[240ms] border-r border-[var(--border-subtle)] last:border-r-0
      inactive: text-[var(--text-muted)] hover:text-[var(--text-secondary)]
      active: text-[var(--text-primary)]
      active underline: <motion.span layoutId="assertTab"> absolute bottom-[-1px] left-0 right-0 h-[2px] bg-[var(--accent)]
        transition: { type: 'spring', stiffness: 380, damping: 32 }
    tabs: SEQUENCE · ARGUMENTS · SCHEMA · LEAKAGE

  TAB CONTENT:
    classes: grid grid-cols-1 lg:grid-cols-[5fr_7fr] gap-0 border border-[var(--border-default)] border-t-0 divide-y lg:divide-y-0 lg:divide-x divide-[var(--border-default)]
    animation on switch: AnimatePresence mode="wait"
      initial: { opacity: 0, y: 12 }
      animate: { opacity: 1, y: 0 }
      exit: { opacity: 0, y: -8 }
      transition: { duration: 0.26, ease: [0.16, 1, 0.3, 1] }

    LEFT (explanation):
      classes: px-6 md:px-10 py-8 md:py-12 flex flex-col
      title: font-body text-[19px] font-500 text-[var(--text-primary)]
      body: mt-4 font-body text-[14px] leading-[1.65] text-[var(--text-secondary)] max-w-[46ch]
      catches line: mt-auto pt-8
        label "CATCHES" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]
        value font-mono text-[13px] text-[var(--text-primary)] mt-2

    RIGHT (result panel):
      classes: px-6 md:px-10 py-8 md:py-12 bg-[var(--bg-secondary)] font-mono text-[12px]
      renders the actual pass or fail output for that assertion family
      pass rows: text-[var(--text-secondary)], prefix "  ok  " in text-[var(--text-muted)]
      fail rows: text-[var(--text-primary)], prefix " fail " in text-[var(--signal-fail)], 2px left border var(--signal-fail), bg rgba(255,92,70,0.05), pl-3
      expected and observed lines under a fail: text-[var(--text-muted)] pl-8

  TAB CONTENT, all four:

    SEQUENCE:
      title: "Tool call order"
      body: "Compares the observed sequence of tool names against the expected sequence and reports the first point of divergence, not just that something differed."
      catches: "an agent that calls tools in a new order after a prompt edit"
      panel:
        ok    cassette 7f3a91  read_ledger → flag_anomalies
        ok    cassette 21c04b  fetch_policy → summarise
        fail  cassette 9e17dd  order diverged at index 0
              expected  read_ledger → flag_anomalies
              observed  flag_anomalies → read_ledger

    ARGUMENTS:
      title: "Critical field matching"
      body: "Exact match on the argument fields you declare as critical, everything else ignored. A reworded query string does not fail the test, a wrong account identifier does."
      catches: "an argument that silently changed type or lost a field"
      panel:
        ok    cassette 7f3a91  month="2026-03"  threshold=0.04
        ok    cassette 44b8f2  account_id=8841
        fail  cassette 9e17dd  threshold missing from flag_anomalies
              expected  threshold=0.04
              observed  (absent)

    SCHEMA:
      title: "Structured output validity"
      body: "Validates the response against the JSON schema you declared and reports the failing path rather than a bare boolean."
      catches: "a model that starts wrapping its JSON in prose"
      panel:
        ok    cassette 7f3a91  matches AnomalyReport
        fail  cassette 3d90ac  $.anomalies[2].confidence
              expected  number
              observed  string "high"

    LEAKAGE:
      title: "Redaction enforcement"
      body: "Fails the test if any declared pattern appears in an outbound request. Runs on the write path as well, so a secret never reaches a cassette on disk in the first place."
      catches: "a prompt template that started interpolating a raw key"
      panel:
        ok    cassette 7f3a91  0 matches across 11 events
        ok    cassette 21c04b  0 matches across 7 events
        fail  cassette 5a2f60  bearer token in event 04
              pattern   bearer_token
              location  messages[2].content

  Mobile: grid collapses to single column, tab bar scrolls horizontally with a right-edge gradient mask from bg-primary to transparent, w-12
```

---

## Section 6, Cassette Anatomy

**Recipe:** `asymmetric-bento-grid` from COMPOSITION_RECIPES.md, image slots replaced with Blueprint Design annotated diagrams. Six cells maximum, three distinct cell sizes, per the banned-pattern rule.
**Component:** `src/components/sections/Anatomy.tsx`
**Funnel job:** Reassure. No CTA.

This is where the supporting Blueprint trend does its work. A cassette is drawn as a technical schematic with annotation callouts and measurement lines, the same way a product gets exploded into labelled parts.

**Z-index stack:**
```
z-[var(--z-base)]:    bg-[var(--bg-secondary)]
z-[var(--z-grid)]:    .tech-grid, opacity via mask, second and final appearance of the grid on the page
z-[var(--z-content)]: grid content
```

**Structure:**
```
<section> relative py-24 md:py-36 px-4 md:px-8 lg:px-12 bg-[var(--bg-secondary)] overflow-hidden
  grid layer: absolute inset-0 z-[var(--z-grid)] tech-grid, mask-image: linear-gradient(to bottom, black 0%, transparent 60%)
  container: relative z-[var(--z-content)] max-w-[1400px] mx-auto

  header, no eyebrow:
    headline: "A CASSETTE IS A FILE YOU CAN READ IN A PULL REQUEST" font-display text-[clamp(2rem,4.5vw,3.75rem)] font-700 uppercase leading-[0.94] tracking-[-0.02em] text-[var(--text-primary)] max-w-[22ch] [text-wrap:balance]
    animation: standard entrance

  BENTO GRID:
    classes: mt-12 md:mt-16 grid grid-cols-1 lg:grid-cols-12 gap-px bg-[var(--border-default)] border border-[var(--border-default)]
    Note: the gap is 1px and the container background is the border colour, so the gaps
    become the grid lines. This is the bento technique from §2E, adapted to hard corners.

    each cell base: relative bg-[var(--bg-primary)] p-6 md:p-8 transition-colors duration-[240ms] hover:bg-[var(--bg-surface)]
    Note: no translateY lift, no scale, no shadow. Bold brutalist cells do not float.
    each cell carries a corner tick mark: absolute top-0 left-0 w-2 h-px bg-[var(--border-strong)] plus absolute top-0 left-0 w-px h-2 bg-[var(--border-strong)]

    CELL A, the schematic (lg:col-span-7, lg:row-span-2):
      label: "CASSETTE 7F3A91" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]
      content: inline SVG technical diagram, Blueprint treatment
        viewBox="0 0 600 420", w-full h-auto mt-6
        a stacked stack of six labelled bands representing the event list, each band 1px stroked in var(--border-default), fill var(--bg-surface)
        annotation callouts: thin 1px leader lines in var(--accent) at 0.5 opacity running from each band to a right-margin label
        labels in font-mono 10px, fill var(--text-muted), uppercase, tracking 0.16em
        measurement line down the left edge with end ticks, labelled "11 EVENTS"
        the fingerprint band is highlighted: stroke var(--accent), label in var(--accent)
        SVG path animation on scroll: leader lines draw in via stroke-dasharray and stroke-dashoffset
          initial: stroke-dashoffset = path length
          whileInView: stroke-dashoffset = 0
          viewport: { once: false, amount: 0.3 }
          transition: { duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: index * 0.08 }

    CELL B, plain JSON (lg:col-span-5):
      label: "ON DISK"
      body: "One interaction per file, plain JSON, content-hashed identifier. A cassette diff is readable in review, which is the whole reason it is not a binary format."
      classes: font-body text-[14px] leading-[1.65] text-[var(--text-secondary)] mt-4 max-w-[42ch]

    CELL C, fingerprint (lg:col-span-5):
      label: "MATCHING"
      body: "The request fingerprint is built from the model, the normalised message list and the tool definitions in scope. Timestamps and request identifiers are excluded, because they are volatile and matching on them would break every replay."
      classes: same as Cell B

    CELL D, redaction (lg:col-span-4):
      label: "REDACTION"
      value: "4 rule classes" font-mono text-[clamp(1.5rem,2.5vw,2rem)] text-[var(--text-primary)] mt-3 tabular-nums
      sub: "keys, bearer tokens, emails, card numbers, plus your own" font-body text-[13px] text-[var(--text-secondary)] mt-2

    CELL E, providers (lg:col-span-4):
      label: "ADAPTERS"
      value: "3" font-mono text-[clamp(1.5rem,2.5vw,2rem)] text-[var(--text-primary)] mt-3 tabular-nums
      sub: "OpenAI, Anthropic, and MCP tool calls, all normalised to one event schema" font-body text-[13px] text-[var(--text-secondary)] mt-2

    CELL F, honesty (lg:col-span-4):
      label: "NOT YET BUILT"
      body: "Streaming is coalesced into a single assistant message rather than recorded token by token. Embeddings, image and audio endpoints are out of scope."
      classes: font-body text-[13px] leading-[1.6] text-[var(--text-secondary)] mt-4
      Note: this cell exists on purpose. Documentation is 20 points and the rules run a
      pass-or-fail screen on overstated functionality. Naming the limits on the marketing
      page is the cheapest credibility on the site.

  ANIMATION:
    cells stagger in: parent staggerChildren 0.07
    each cell: initial { opacity: 0, filter: 'blur(8px)', y: 20 } whileInView { opacity: 1, filter: 'blur(0px)', y: 0 }
    viewport: { once: false, amount: 0.1 }
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] }
    No hover tilt, no 3D spring. Deliberate departure from the base recipe's tilt interaction.

  Mobile: grid-cols-1, every cell full width, Cell A's SVG scales with the container, annotation labels drop below the diagram instead of sitting in the right margin
```

**ASSET BRIEF:**
```
Type: inline SVG schematic, hand-authored, not generated
Location: Section 6, Cell A
Description: a technical exploded-view diagram of a cassette file. Six horizontal bands stacked
  vertically representing the ordered event list, each 1px stroked, with thin leader lines
  running right to annotation labels. A vertical measurement line with end ticks down the left
  edge labelled "11 EVENTS". The fingerprint band highlighted in amber.
Style: Blueprint Design. Technical drawing language, monospace annotation labels, hairline
  strokes, no fills beyond the flat surface colour, no gradients, no shadows.
Colours: strokes var(--border-default), highlight var(--accent), labels var(--text-muted)
Dimensions: viewBox 0 0 600 420, renders responsive at w-full h-auto
Format: inline JSX SVG in the component, not an external file, so it inherits CSS variables
  and animates with the rest of the page
Generation tool: none, this is authored by hand in the component. An AI-generated raster
  diagram would not inherit the palette, would not animate, and would not stay sharp.
Fallback: not applicable, SVG has no loading state
```

---

## Section 7, Install

**Recipe:** bespoke, command-led convert section.
**Component:** `src/components/sections/Install.tsx`
**Funnel job:** Convert. Maximum visual weight on the primary action.

**Structure:**
```
<section> py-24 md:py-32 px-4 md:px-8 lg:px-12 bg-[var(--bg-primary)] border-t border-[var(--border-subtle)]
  container: max-w-[1400px] mx-auto

  layout: grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 items-end

  LEFT (lg:col-span-7):
    headline: "RUNS OFFLINE. NO KEY REQUIRED." font-display text-[clamp(2.25rem,5vw,4.5rem)] font-800 uppercase leading-[0.9] tracking-[-0.025em] text-[var(--text-primary)] max-w-[16ch] [text-wrap:balance]
    sub: "Clone the demo repository and the full suite passes against committed cassettes with no provider account and no network access." mt-6 max-w-[52ch] font-body text-[15px] leading-[1.6] text-[var(--text-secondary)]

  RIGHT (lg:col-span-5):
    command block:
      classes: group flex items-center justify-between gap-4 border border-[var(--border-strong)] bg-[var(--bg-secondary)] pl-5 pr-2 py-4
      command: "pipx install ferric" font-mono text-[13px] md:text-[14px] text-[var(--text-primary)]
        the word "pipx" renders in text-[var(--text-muted)]
        Note: "ferric" is the distribution name, the import name, and the CLI entrypoint. One
        word, three roles, no hyphenated fallback and no suffix. Verified unclaimed on PyPI.
      copy button:
        classes: shrink-0 inline-flex items-center justify-center w-9 h-9 border border-[var(--border-default)] text-[var(--text-muted)] hover:text-[var(--accent)] hover:border-[var(--accent)] transition-colors duration-[240ms]
        icon: copy, 14px, swaps to check for 1.6s after a successful copy
        copied state announced to screen readers via aria-live="polite"

    second command, smaller:
      classes: mt-3 flex items-center gap-3 font-mono text-[12px] text-[var(--text-muted)]
      content: "then  FERRIC_MODE=replay pytest"

    CTA row:
      classes: mt-8 flex flex-wrap items-center gap-x-6 gap-y-3
      primary: "View on GitHub"
        classes: inline-flex items-center gap-2.5 bg-[var(--accent)] text-[var(--bg-primary)] px-5 py-3 font-mono text-[12px] font-medium uppercase tracking-[0.14em] hover:bg-[var(--accent-hover)] transition-colors duration-[240ms]
      secondary: "Watch the demo"
        classes: inline-flex items-center gap-2 font-mono text-[12px] uppercase tracking-[0.14em] text-[var(--text-secondary)] border-b border-[var(--border-default)] pb-1 hover:text-[var(--text-primary)] hover:border-[var(--accent)] transition-colors duration-[240ms]

  ANIMATION: standard entrance, left column delay 0, right column delay 0.15s
```

**CTA intent audit across the whole page:** the hero primary is "See it catch a regression", an anchor to Section 4, which is a demo intent. The hero secondary and the nav link are both "Read the docs" and "Docs", a single docs intent using one label family. The Section 7 primary is "View on GitHub", matching the nav CTA exactly, one repo intent, one label. "Watch the demo" is the only video intent and appears twice, here and in the footer, with the identical label. No two CTAs on the page share an intent with different wording.

---

## Section 8, Footer

**Component:** `src/components/layout/Footer.tsx`

```
<footer> py-14 md:py-16 px-4 md:px-8 lg:px-12 bg-[var(--bg-primary)] border-t border-[var(--border-default)]
  container: max-w-[1400px] mx-auto

  top row: flex flex-col md:flex-row md:items-end md:justify-between gap-8
    left:
      statement, not a wordmark: "A FLIGHT RECORDER FOR AGENT TRAFFIC."
        classes: font-display text-[clamp(1.5rem,3vw,2.25rem)] font-700 uppercase leading-[0.95] tracking-[-0.02em] text-[var(--text-primary)] max-w-[16ch]
      Note: the footer closes on what the tool does, not on its name. The name appears once
      below, in the sign-off line, where it is attribution rather than branding.
    right:
      classes: flex flex-col gap-2.5 font-mono text-[12px] uppercase tracking-[0.14em]
      links: "View on GitHub", "Watch the demo", "Read the docs"
      each: text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors duration-[240ms] w-fit

  bottom row: mt-14 pt-6 border-t border-[var(--border-subtle)] flex flex-col md:flex-row md:items-center md:justify-between gap-3
    left: "Ferric · built with Kiro for the Ready, Spec, Ship Hackathon" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]
      the token "Ferric" renders in text-[var(--text-secondary)], one step brighter, since it is the only naming on the page
    right: "Back to top" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors duration-[240ms], anchors to #top

  ANIMATION: standard entrance, single stagger group, staggerChildren 0.06
```

No version label, no build number, no locale strip. All three are banned decorations.

---

## Surface 2, Drift Report Viewer

**What it is:** the single self-contained HTML file that `ferric drift --html report.html` writes to disk. A judge opens it from the filesystem with no server. It has no external dependencies: no CDN, no web fonts, no framework. All CSS is inlined in a `<style>` block, all interactivity is vanilla JS in a `<script>` block, the whole file is generated by a Python template in `src/ferric/report.py`.

**Why the constraint:** a report artefact that needs a network to render is useless in CI, and the in-app preview sandbox blocks external resources anyway. System font stack, inlined everything.

**Font stack, since Google Fonts are unavailable offline:**
```css
--font-display: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
--font-mono: ui-monospace, "SFMono-Regular", "Cascadia Mono", "Liberation Mono", monospace;
```
The display face degrades to the system sans here. That is an accepted trade for a zero-dependency artefact, and the palette, spacing, borders and radius language stay identical to the landing page so the two still read as one product.

**Layout:**
```
<body> bg #0b0b0c, text #ededea, font-mono 13px, padding 0

  HEADER (static, not sticky):
    padding 32px 32px 24px, border-bottom 1px solid rgba(255,255,255,0.11)
    title: "DRIFT REPORT" font-display 22px, weight 700, uppercase, letter-spacing 0.04em
    meta row: display flex, gap 32px, margin-top 12px, font-mono 11px, color #5c5c57, uppercase, letter-spacing 0.16em
      cells: BASELINE / opus-4.6 · TARGET / opus-4.7 · CASSETTES / 34 · GENERATED / 2026-08-21 14:32 UTC

  SUMMARY STRIP:
    display grid, grid-template-columns repeat(3, 1fr), border-bottom 1px solid rgba(255,255,255,0.11)
    each cell: padding 24px 32px, border-right 1px solid rgba(255,255,255,0.06), last has none
      label: font-mono 10px, uppercase, letter-spacing 0.2em, color #5c5c57
      value: font-mono 32px, margin-top 8px, font-variant-numeric tabular-nums
    cells:
      UNCHANGED   28   value colour #9a9a94
      REWORDED     5   value colour #9a9a94
      DIVERGED     1   value colour #ff5c46
    Note: no green on the unchanged count. Passing is quiet.

  FILTER BAR (sticky):
    position sticky, top 0, z-index 200
    background rgba(11,11,12,0.88), backdrop-filter blur(12px)
    border-bottom 1px solid rgba(255,255,255,0.11)
    box-shadow 0 8px 24px -12px rgba(0,0,0,0.6)
    padding 12px 32px, display flex, gap 8px
    each filter button:
      padding 6px 14px, border 1px solid rgba(255,255,255,0.11), background transparent
      font-mono 11px, uppercase, letter-spacing 0.16em, color #5c5c57, cursor pointer
      transition color 240ms, border-color 240ms
      hover: color #ededea
      active: color #0b0b0c, background #ffb020, border-color #ffb020
    buttons: ALL · DIVERGED · REWORDED · UNCHANGED
    filtering is pure vanilla JS toggling a data-state attribute on <tbody> rows, no framework

  RESULTS TABLE:
    width 100%, border-collapse collapse
    thead th: text-align left, padding 12px 32px, font-mono 10px, uppercase, letter-spacing 0.2em, color #5c5c57, border-bottom 1px solid rgba(255,255,255,0.11)
    columns: CASSETTE · EVENTS · CLASSIFICATION · DIMENSION
    tbody tr: border-bottom 1px solid rgba(255,255,255,0.06), cursor pointer
      hover: background #17171a
    td: padding 14px 32px, font-mono 12px, color #9a9a94
    classification cell:
      unchanged: color #5c5c57, text "unchanged"
      reworded:  color #9a9a94, text "reworded"
      diverged:  color #ff5c46, text "diverged", row also gets border-left 2px solid #ff5c46 and background rgba(255,92,70,0.05)
    dimension cell: only populated for diverged rows, e.g. "tool order"

  EXPANDED ROW (click to toggle, one open at a time):
    a hidden <tr> immediately after each row, display none until expanded
    inner cell colspan 4, padding 0 32px 24px, background #121214
    contains a two-column diff:
      grid-template-columns 1fr 1fr, gap 1px, background rgba(255,255,255,0.11), border 1px solid rgba(255,255,255,0.11)
      each side: background #0b0b0c, padding 16px
      side header: font-mono 10px, uppercase, letter-spacing 0.2em, color #5c5c57, margin-bottom 10px
        left "BASELINE", right "TARGET"
      event rows: font-mono 12px, line-height 1.7, color #9a9a94
      differing rows on the target side: color #ededea, background rgba(255,92,70,0.06), padding-left 8px, border-left 2px solid #ff5c46
    expansion animation: max-height 0 to 600px, transition 320ms cubic-bezier(0.16,1,0.3,1), plus opacity
      Note: a CSS transition, not a keyframe animation, so it replays every toggle

  FOOTER:
    padding 24px 32px, border-top 1px solid rgba(255,255,255,0.06)
    left: "generated by ferric" font-mono 10px, uppercase, letter-spacing 0.2em, color #5c5c57
    right: total token spend for the drift run, font-mono 10px, color #5c5c57
    Note: the token cost of the check itself is shown honestly. Running drift is the one part
    of Ferric that costs money and it should say so.

  RESPONSIVE:
    below 768px: summary strip becomes grid-template-columns 1fr with row borders, table
    horizontal padding drops to 16px, the EVENTS column is hidden via a media query, the
    expanded diff stacks to one column
    below 768px the table scrolls horizontally inside a wrapper with overflow-x auto

  PRINT:
    @media print: background white, text black, all rows expanded, filter bar hidden,
    diverged rows keep the left border as a solid black rule so the report survives being
    printed or exported to PDF for a review
```

---

## Surface 3, Docs Site

**What it is:** the documentation surface. Same palette, same fonts, same border and radius language as the landing page, but tuned for reading rather than persuasion.

**Layout:** three columns on desktop, `grid-cols-[240px_1fr_200px]`. Left sidebar navigation, centre content, right on-page table of contents. Below `lg` it collapses to a single column with the sidebar behind a slide-in drawer and the table of contents hidden entirely.

**Nav:** the same A4 dual-pill split nav from Section 1, with one change. The right pill's three links are replaced with a search trigger and the GitHub CTA:
```
search trigger: px-3.5 py-1.5 flex items-center gap-2.5 font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors duration-[240ms] rounded-full
  content: "Search" plus a keyboard hint chip
  hint chip: border border-[var(--border-default)] px-1.5 py-0.5 font-mono text-[9px] text-[var(--text-muted)] rounded-full, content "/"
```

**Left sidebar:**
```
classes: hidden lg:block sticky top-[6.5rem] h-[calc(100dvh-8rem)] overflow-y-auto pr-8 border-r border-[var(--border-subtle)]
group label: font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)] mb-3 mt-8 first:mt-0
link: block py-1.5 font-body text-[14px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors duration-[240ms]
active link: text-[var(--text-primary)] border-l-2 border-[var(--accent)] pl-3 -ml-[2px]
groups and pages:
  START      Install · Quickstart · How replay works
  RECORD     Wrapping a client · Adapters · Redaction
  REPLAY     Matching · Unmatched requests · CI setup
  ASSERT     Sequence · Arguments · Schema · Leakage
  COMMANDS   promote · drift · list · verify
  REFERENCE  Cassette format · Event schema · Limitations
```

**Content column:**
```
classes: min-w-0 py-12 lg:py-16 px-0 lg:px-12 max-w-[720px]
h1: font-display text-[clamp(2rem,4vw,3rem)] font-700 uppercase leading-[0.95] tracking-[-0.02em] text-[var(--text-primary)]
h2: font-display text-[1.75rem] font-700 uppercase tracking-[-0.015em] text-[var(--text-primary)] mt-16 pt-8 border-t border-[var(--border-subtle)]
h3: font-body text-[17px] font-500 text-[var(--text-primary)] mt-10
p:  font-body text-[15px] leading-[1.7] text-[var(--text-secondary)] mt-4 max-w-[68ch] [text-wrap:pretty]
a inline: text-[var(--accent)] border-b border-[var(--accent)]/30 hover:border-[var(--accent)] transition-colors duration-[240ms]
ul: mt-4 space-y-2, marker is a 4px amber square via ::marker fallback to a pseudo-element
code inline: font-mono text-[13px] bg-[var(--bg-elevated)] px-1.5 py-0.5 text-[var(--text-primary)]
pre block:
  classes: mt-6 border border-[var(--border-default)] bg-[var(--bg-secondary)] overflow-x-auto
  header bar: flex items-center justify-between px-4 py-2 border-b border-[var(--border-subtle)]
    language label: font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)]
    copy button: same component as Section 7
  code: block px-4 py-4 font-mono text-[13px] leading-[1.7] text-[var(--text-secondary)]
callout, used for the limitations page:
  classes: mt-6 border-l-2 border-[var(--accent)] bg-[var(--accent-glow)] px-5 py-4
  label: font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--accent)]
  body: font-body text-[14px] leading-[1.6] text-[var(--text-secondary)] mt-2
```

**Right table of contents:**
```
classes: hidden xl:block sticky top-[6.5rem] h-fit pl-8 border-l border-[var(--border-subtle)]
label: "ON THIS PAGE" font-mono text-[10px] uppercase tracking-[0.2em] text-[var(--text-muted)] mb-4
link: block py-1.5 font-body text-[13px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors duration-[240ms]
active: text-[var(--accent)]
active tracking: IntersectionObserver on every h2 and h3, rootMargin '0px 0px -70% 0px'
```

**Motion on docs:** almost none, deliberately. Documentation pages do not get scroll reveals, the skill file is explicit that motion patterns are contextual and dashboards and reading surfaces do not need them. The only motion is the sidebar drawer slide on mobile and the copy button state change.

---

## Authenticity Rules

The hackathon runs a pass-or-fail eligibility screen on simulated or hard-coded features presented as working functionality. That screen sits before scoring, so failing it is not a deduction, it removes the entry. These three rules exist to make that structurally impossible on the frontend, and they were confirmed as design decisions rather than suggestions.

**Rule 1: every value on these surfaces traces to a real cassette.**

`tests/cassettes/` is the single source of truth. Cassette `7f3a91`, its eleven events, the ledger reconciliation tool calls, the `9e17dd` tool-order divergence, the 34-cassette library size and the one behavioural regression are all real recorded artefacts committed to the repository, not copy written to look plausible. The build step reads them and generates `src/data/cassettes.generated.ts`, and every section that displays cassette content imports from that file. Nothing is typed by hand into a component.

This means a judge can open `tests/cassettes/7f3a91.json` and find the exact eleven events shown in the hero. If the cassettes change, the page changes, because the page is a view over them. A hard-coded string that happens to match is a different thing from a value that cannot diverge, and only the second one survives scrutiny.

If a cassette does not exist by build time, the section renders its skeleton shimmer state permanently rather than inventing a number. An honest empty state costs one section, an invented number costs the entry.

**Rule 2: nothing anywhere is a screenshot of the product.**

Section 4's pinned sequence, Section 5's four assertion panels, Section 6's schematic, the hero readout and the entire drift report viewer are live DOM: real text nodes, real borders, real state, real CSS. There is not one raster image of a terminal, a diff, or a UI anywhere across the three surfaces. The only image on any page is the favicon, which is four shapes of inline SVG.

A screenshot of a passing test suite is precisely the artefact that pass-or-fail screen exists to catch, and it is also the laziest possible answer to a section that is meant to prove something. Building it live costs a few more hours and it is the difference between showing evidence and showing a picture of evidence.

**Rule 3: green does not exist, and the limitations are stated on the marketing page.**

Passing states render as quiet neutrals, `--text-secondary` at most. `--signal-fail` appears in exactly three places, all of them real failures drawn from real cassettes. A page that renders green ticks everywhere is asking to be believed. A page where the only saturated colour is a failure it caught is demonstrating something instead.

Section 6 Cell F names what is not built: streaming is coalesced rather than recorded token by token, and embeddings, image and audio endpoints are out of scope. That cell is not an apology and it is not filler. Documentation carries 20 of the 100 points, the rules explicitly screen for overstated functionality, and being the first to name your own limits is the cheapest credibility on the site. It also means every other claim on the page reads as measured, because the visitor has already seen you decline to overstate one.

Any future section that cannot satisfy all three rules by day seven gets cut from the page and listed in Cell F, not shipped in a weakened form.

---

## Banned Patterns, enforced across all three surfaces

- No logo-left, links-centre, button-right nav. A4 dual-pill only.
- No purple or blue AI gradient glow anywhere.
- No gradient text on any heading.
- No three equal generic feature cards. Section 5 is tabbed, Section 6 is asymmetric with six cells and three sizes.
- No bento grid with more than six cells.
- No green anywhere in the palette. Passing states are quiet neutrals.
- No outer glow on any button or card. Inner borders and flat fills only.
- No generic dark drop shadows. One tinted shadow on the report filter bar, nothing else.
- No Inter as a display font. No Instrument Serif, no Fraunces. No Space Grotesk, no Outfit.
- No JetBrains Mono. Martian Mono only, with the system mono stack as the offline fallback in the report viewer.
- No mixed radius scales. Hard corners everywhere except nav pills and status dots.
- No `viewport={{ once: true }}` on any animation. Zero exceptions.
- No CSS keyframe animation with `animation-fill-mode: forwards` for any scroll reveal.
- No `onMouseEnter` or `onMouseLeave` setting style properties.
- No `useState` for cursor tracking on the magnetic CTA.
- No icon library, no emoji, no AI-generated symbols.
- No em dashes in any string, comment, or file.
- No placeholder data. No John Doe, no Acme, no 99.9%, no 1,234, no lorem ipsum.
- No version labels, build numbers, section-number eyebrows, pagination overlays, or locale strips as decoration.
- No screenshots or mockup images standing in for working functionality anywhere on the page.
- No `h-screen`. `min-h-[100dvh]` only.
- No hardcoded hex values in components. CSS variables only.
- No logo or favicon substituted with a generated symbol.

---

## Spec Self-Check

- [x] Every element has exact Tailwind classes, no vague descriptions
- [x] Every animation declares initial, animate, duration, ease and delay
- [x] Every section declares its z-index stack against the semantic scale
- [x] Every section needing imagery has an asset brief, including the two that deliberately need none
- [x] Every positional and sizing class carries responsive breakpoints
- [x] Composition recipes referenced by name where applicable, bespoke sections written at the same specificity
- [x] Scroll animations replay on re-entry, `once: false` throughout
- [x] Scrollbar hidden globally with smooth scrolling preserved
- [x] Entrance animations use blur plus opacity plus translate, not plain fadeUp
- [x] Layout repetition caps satisfied, seven families across eight sections
- [x] Eyebrow restraint satisfied, two across eight sections
- [x] Hero stack discipline satisfied, four elements, CTA within 32px of the subhead
- [x] No banned copy words in any string
- [x] No duplicate CTA intent across the page
- [x] A junior developer could build this without asking a design question
- [x] No logo, wordmark or brand mark on any surface, and no placeholder slot pretending one is coming
- [x] Every displayed value traces to a committed cassette, none typed by hand into a component
- [x] Zero raster images across all three surfaces, favicon excepted
- [x] Name resolved and verified unclaimed on PyPI, consistent across all thirteen appearances

---

## Resolved Decisions

All four previously open items are closed. None were deferred, none were half filled.

**1. Name: Ferric.** `rewind` is taken on PyPI, verified live against the JSON API, it is an existing AGPL project by Jens Rantil. `cassette`, `recorder`, `replay`, `reel` and `spool` are all taken too. `ferric` returns 404 on PyPI, meaning unclaimed, so it works as the distribution name, the import name and the CLI entrypoint without a hyphen or a suffix. One word, three roles.

Ferric is iron oxide, the magnetic coating on recording tape. It is the material that made recording and playback possible, which is exactly what the tool does for agent traffic. It is a real word rather than an invented one, it is single word per your naming rule, and it carries the amber colour in its own etymology since ferric oxide is rust coloured. The accent colour and the name come from the same place.

Note that `ferric` is taken on npm and the GitHub user namespace exists, neither of which matters here since this ships as a Python package and the repository sits under your own account.

**2. No logo, no wordmark, no lockup.** Closed as a design decision, not a pending asset. The nav carries a live session timecode. The footer closes on a statement of what the tool does. The name appears three times total, each time functionally: the tab title, the install command, and the footer sign-off. Nothing on any of the three surfaces is a brand mark.

**3. Favicon: inline SVG data URI**, one amber dot on graphite, hex values taken directly from the palette. No file, no design work, no drift risk.

**4. Demo video URL.** Anchors resolve to `#` until the video exists on day eight, and the two CTAs that point at it are `aria-disabled="true"` with `pointer-events-none` and `opacity-50` until the real URL is set in `src/config.ts`. A dead link that looks live is worse than one that visibly is not ready yet, and a judge clicking into nothing is an avoidable presentation loss.

---

## Naming Consistency Reference

Every appearance of the name across the codebase, so nothing drifts during the build.

| Context | Value |
|---|---|
| PyPI distribution | `ferric` |
| Python import | `import ferric` |
| CLI entrypoint | `ferric` |
| Source directory | `src/ferric/` |
| Install command | `pipx install ferric` |
| Replay env var | `FERRIC_MODE=replay` |
| Drift command | `ferric drift --to <model>` |
| Report command | `ferric drift --html report.html` |
| Report footer | `generated by ferric` |
| Browser tab title | `Ferric` |
| Footer sign-off | `Ferric · built with Kiro for the Ready, Spec, Ship Hackathon` |
| Nav | no name, session timecode only |
| Hero | no name anywhere in the first viewport |
