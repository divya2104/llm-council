---
name: LLM Council
description: Multi-model deliberation and HR job-description drafting, in one editorial-toned app shell.
colors:
  ink: "#1e2321"
  ink-soft: "#454e49"
  muted: "#6b7268"
  paper: "#eceee7"
  panel: "#ffffff"
  rule: "#d7dacf"
  rule-strong: "#bcc0b1"
  sky-blue: "#21a6f1"
  sky-blue-deep: "#1483c4"
  sky-blue-wash: "#e4f4fe"
  clay-terracotta: "#b8622e"
  clay-terracotta-wash: "#f5e7dc"
  error: "#b3261e"
  error-wash: "#f6e5e3"
  success: "#3e7d4f"
  success-wash: "#e5efe6"
  warning: "#a67c00"
  warning-wash: "#faf1d9"
typography:
  display:
    fontFamily: "Spectral, Iowan Old Style, serif"
    fontSize: "1.5rem"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "-0.01em"
  body:
    fontFamily: "IBM Plex Sans, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, SFMono-Regular, monospace"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.08em"
rounded:
  xs: "2px"
  sm: "3px"
  md: "4px"
  lg: "6px"
  xl: "10px"
  pill: "999px"
  circle: "50%"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "20px"
  xl: "24px"
  2xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.sky-blue}"
    textColor: "#ffffff"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "14px 26px"
  button-primary-hover:
    backgroundColor: "{colors.sky-blue-deep}"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "0 18px"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.sky-blue}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "7px 16px"
  input-field:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "14px"
---

# Design System: LLM Council

## 1. Overview

**Creative North Star: "The Deliberation Room"**

This is a considered, editorial space where multiple voices are heard, weighed against each other, and synthesized into a verdict — never a single black-box answer presented as fact. The palette is a warm, muted paper-and-ink base with one clear signal color (Sky Blue) doing the pointing: it marks the user's own words, active focus, and primary action, and nothing else competes with it for attention. A serif display face gives headings and section titles a print-like authority; a clean sans body keeps the actual deliberation — model responses, rankings, job-description fields — legible and fast to scan. The system explicitly rejects the generic SaaS/ChatGPT-wrapper look (gradient heroes, cream-on-cream, hero-metric cards, tiny uppercase eyebrows) and the opposite failure mode of dense, grey-on-grey enterprise HR software. It should read as modern and a little colorful, but considered rather than flashy — confidence through precision, not decoration.

Two workflows share this shell: the LLM Council chat (anonymized peer review across models, chairman synthesis) and the JD Creator wizard (structured, Hay-methodology job description drafting for Aditya Birla Group entities). Both use the same tokens; the wizard just adds more structured form surfaces on top of the same base.

**Key Characteristics:**
- One signal color (Sky Blue), used sparingly and consistently for interactive/primary elements
- Serif display + sans body pairing, editorial rather than corporate
- Tight radii (2–6px) everywhere except pills (tags, progress) and circular controls
- Left-edge color accents mark provenance (whose words these are, what stage produced them), not decoration
- Flat by default; elevation is earned by interaction (see §4 for the direction this is moving)

## 2. Colors

A warm, low-saturation neutral base (paper and ink, not black-and-white) carries the interface; Sky Blue is the only saturated color doing regular work, with terracotta, success-green, and warning-amber reserved for status/semantic signaling only.

### Primary
- **Sky Blue** (#21a6f1): The one interactive signal — primary buttons, links, focus rings, active-state accents, the user's own chat bubble. If it's clickable or currently focused, it's some shade of this blue.
- **Sky Blue Deep** (#1483c4): Hover/pressed state for Sky Blue elements.
- **Sky Blue Wash** (#e4f4fe): Focus-ring glow and subtle selected-state backgrounds; never used as a large fill.

### Secondary
- **Clay Terracotta** (#b8622e): A warm secondary signal reserved for a distinct status meaning (currently: informational/attention callouts), kept separate from the primary blue so it never competes with it.

### Neutral
- **Ink** (#1e2321): Primary text color.
- **Ink Soft** (#454e49): Secondary text — labels, de-emphasized copy that still needs to read clearly.
- **Muted** (#6b7268): Tertiary text — metadata, placeholder-adjacent copy, timestamps.
- **Paper** (#eceee7): App background. A true warm-neutral, not a saturated cream — kept deliberately close to chroma-0 so it reads as paper, not a themed tint.
- **Panel** (#ffffff): Card, input, and modal surfaces sitting on top of Paper.
- **Rule** (#d7dacf): Default dividers and borders.
- **Rule Strong** (#bcc0b1): Emphasized borders — input outlines, active dividers.

### Status
- **Success** (#3e7d4f) / **Success Wash** (#e5efe6): Chairman/final-answer stage, confirmations.
- **Error** (#b3261e) / **Error Wash** (#f6e5e3): Validation and failure states.
- **Warning** (#a67c00) / **Warning Wash** (#faf1d9): Offline/degraded-mode banners, caution states.

### Named Rules
**The One Signal Rule.** Sky Blue is the only color used for interactive affordances. Terracotta, success, warning, and error are status colors — they inform, they never invite a click.

## 3. Typography

**Display Font:** Spectral (with Iowan Old Style, serif fallback)
**Body Font:** IBM Plex Sans (with system sans fallback)
**Label/Mono Font:** IBM Plex Mono (with system monospace fallback)

**Character:** A print-editorial serif for structure paired with a clean, technical sans for content — the pairing should feel like a well-typeset report, not a marketing page or a code editor.

### Hierarchy
- **Display** (500 weight, 1.5rem+, -0.01em letter-spacing, serif): Section headings, wordmark, h1–h3. Reserved for structural headings, never body copy.
- **Body** (400 weight, 15px, 1.5 line-height, sans): All reading content — chat messages, form fields, JD copy. Cap prose at 65–75ch.
- **Label** (600 weight, 11px, 0.08em tracking, uppercase, mono): Metadata labels — message source, stage labels, chairman label. Small, quiet, and always uppercase-tracked mono; never used for anything a user reads at length.

### Named Rules
**The Mono-Label Rule.** Any small uppercase tracked label (stage names, message sources, status tags) is set in IBM Plex Mono, never the body sans — it's the one consistent tell that separates "metadata about this content" from "the content itself."

## 4. Elevation

Today the system is flat at rest: shadows appear only on hover states (buttons lifting slightly) and modal dialogs (a soft, diffused shadow separating the dialog from the page). Going forward, the direction is toward more layering and a more tactile, confident feel — surfaces should earn slightly more visible depth on interaction, not just a color shift, so primary actions feel physically pressable rather than flat rectangles that happen to be clickable.

### Shadow Vocabulary
- **Interactive lift** (`box-shadow: 0 10px 20px -12px rgba(20, 131, 196, 0.55)`, deepening to `0 14px 24px -12px rgba(20, 131, 196, 0.6)` on hover): Primary buttons — a tinted shadow (using the button's own hue, not neutral black) paired with a 1px upward translate.
- **Modal separation** (`box-shadow: 0 24px 60px -16px rgba(20, 24, 22, 0.4)`): Dialogs and overlays, separating them from the page behind.
- **Focus ring** (`box-shadow: 0 0 0 3px var(--sky-blue-wash)`): Every focusable input and control, in place of a default browser outline.

### Named Rules
**The Tinted Shadow Rule.** Shadows on colored elements (primary buttons) pick up that element's own hue at low opacity, not generic black — depth reads as part of the color, not a separate effect bolted on.

## 5. Components

### Buttons
- **Shape:** 4–6px radius (`rounded.md` / `rounded.lg`), never fully rounded except icon-only circular controls.
- **Primary:** Sky Blue fill, white text, 14px/26px padding, tinted shadow on hover with a 1px lift (see §4). This is the only button style that should visually compete for attention.
- **Secondary / Outline:** White/panel background with an ink-soft or Sky-Blue outline and matching text color; no shadow at rest. Used for lower-priority actions sitting next to a primary button.
- **Hover / Focus:** Primary darkens to Sky Blue Deep and lifts; all buttons get the standard focus-ring treatment when tabbed to.

### Chips / Tags
- **Style:** Pill-shaped (`rounded.pill`, 999px), small mono-adjacent sans label, low-saturation background tied to the tag's semantic color.

### Cards / Containers
- **Corner Style:** 3–4px radius, consistently tight — this is not a soft, heavily-rounded system.
- **Background:** Panel (white) on Paper background, separated by a 1px Rule border rather than a shadow in the default state.
- **Border:** 1px solid Rule (default) or Rule Strong (emphasized); a small number of surfaces — the user's own chat message, the chairman's final answer — add a 3px left-edge accent in their semantic color (Sky Blue for the user, Success green for the chairman) to mark provenance at a glance.
- **Internal Padding:** 16–20px standard.

### Inputs / Fields
- **Style:** Panel background, 1px Rule Strong border, 4px radius.
- **Focus:** Border shifts to Sky Blue, plus the Sky-Blue-Wash focus ring (`0 0 0 3px`).
- **Disabled:** 0.5 opacity, background falls back to Paper.

### Navigation
- **Style:** A single 56px top bar (Panel background, 1px Rule bottom border) carrying the serif wordmark and a bordered Sky-Blue outline button for the primary external action. Flat, no shadow — the border does the separation work.

### Wizard Stepper (JD Creator)
The multi-step JD form uses a horizontal stepper with short mono-labeled steps (Basics, Purpose, Dims, Context, Accts, Reports, Hay, Sign-Off); the active step gets the Sky Blue treatment, completed steps a quieter success/neutral mark. This is the app's one genuinely bespoke navigation pattern and should stay visually quieter than the primary CTA it leads to.

## 6. Do's and Don'ts

### Do:
- **Do** keep Sky Blue as the only color used for interactive/clickable affordances (The One Signal Rule).
- **Do** set metadata labels (stage names, sources, status) in uppercase-tracked IBM Plex Mono, never body sans.
- **Do** tint shadows on colored elements with that element's own hue, not generic black.
- **Do** keep radii tight (2–6px); reserve fully-rounded shapes for pills and circular icon controls only.
- **Do** use a 3px left-edge accent sparingly and only where it marks real provenance (user vs. chairman vs. neutral), matching the existing pattern — not as generic card decoration.

### Don't:
- **Don't** build a generic SaaS/ChatGPT-wrapper look: no gradient hero sections, no cream-on-cream backgrounds, no hero-metric stat cards, no tiny uppercase uppercase eyebrows above every section.
- **Don't** build heavy corporate-enterprise-HR-software chrome: no dense grey-on-grey toolbars, no unstyled/default form controls, no cramped information density.
- **Don't** introduce a second saturated "interactive" color alongside Sky Blue; new status meanings should reuse Terracotta/Success/Warning/Error before inventing a new hue.
- **Don't** apply the left-edge color-stripe accent decoratively across arbitrary cards — it's reserved for the provenance pattern described above.
- **Don't** use gradient text (`background-clip: text` with a gradient) for emphasis; use weight, size, or the Sky Blue color instead.
