---
name: Cognitive Flow
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#684000'
  on-tertiary: '#ffffff'
  tertiary-container: '#885500'
  on-tertiary-container: '#ffd4a4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  display:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '800'
    lineHeight: 44px
  display-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '800'
    lineHeight: 38px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-bold:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  caption:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  margin: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
This design system merges rigorous cognitive utility with playful positive reinforcement. It pairs algorithmic spaced-repetition efficiency with friendly gamification mechanics to eliminate study fatigue and cognitive dread.

The aesthetic blends **Modern SaaS Precision** with **Tactile Gamified Elements**. It relies on generous whitespace, high-legibility typographic hierarchies, rounded interactive cards, subtle ambient depth, and vivid dopamine-inducing accent pops. The UI evokes momentum, cognitive clarity, and celebratory accomplishment without appearing juvenile or cluttered.

## Colors
The color architecture anchors deep cognitive focus while using saturated reward signals for retention states and gamified habits.

- **Primary (`#4F46E5` / Indigo-600):** Drives intentional primary interactions, active study flows, and core branding. Dark mode surfaces use `#6366F1`.
- **Secondary (`#10B981` / Emerald-500):** Designates retention mastery, positive feedback, accuracy metrics, and successful recall intervals.
- **Tertiary (`#F59E0B` / Amber-500):** Reserved strictly for gamification triggers—streaks, flame counters, XP progression, and urgency notifications.
- **Neutral (`#0F172A` / Slate-900):** Anchors high-contrast text and grounding structures.
- **Surfaces & Tints:**
  - App Canvas (Light): `#F8FAFC` (Slate-50)
  - Card/Container Surface (Light): `#FFFFFF`
  - Subtle Indigo Tint (Accent fill / Inactive tags): `#EEF2FF`
  - Structural Borders: `#E2E8F0` (Border-slate-200) and `#F1F5F9` (Border-slate-100)
  - App Canvas (Dark): `#0B0F19`
  - Card/Container Surface (Dark): `#1E293B`
  - Subtle Borders (Dark): `#334155`

## Typography
Plus Jakarta Sans serves as the single typographic family across all roles. Its geometric construction keeps numeric metrics legible, while its humanist terminal cuts inject warmth into high-intensity recall sessions.

- **Display & Headlines:** Set in bold and extrabold weights. Numeric stats, multipliers, and streak counts should always utilize tabular figures (`font-variant-numeric: tabular-nums`).
- **Body:** Standardized at 14px and 16px with comfortable line heights to reduce visual fatigue across long deck reviews.
- **Labels & Microcopy:** Used for spaced-repetition status tags, keyboard shortcut hints, and rating timers. Microcopy retains uppercase tracking (`letter-spacing: 0.04em`) when used inside pills or status chips.

## Layout & Spacing
The layout uses a fixed-width container philosophy on desktop dashboard views (max 1280px) and a centralized, distraction-free single-column canvas (max 680px) during study review mode.

- **Breakpoints:**
  - Mobile: `< 640px` (single-column, bottom app navigation dock, 1rem margins)
  - Tablet: `640px – 1024px` (collapsible navigation bar, fluid cards, 1.5rem margins)
  - Desktop: `> 1024px` (fixed 260px navigation sidebar, multi-column analytics grid, 2rem margins)
- **Study Canvas Exception:** During active review runs, secondary elements (navbars, sidebars, extra metric badges) recede into low opacity or collapse completely to preserve tunnel vision on the flashcard deck.

## Elevation & Depth
Visual depth uses a three-tier model combining diffused ambient shadows with hairline borders:

1. **Flat Baseline (Level 0):** Input fields, inactive study options, and container wells rely purely on subtle structural strokes (`1px solid #E2E8F0` / dark: `#334155`).
2. **Elevated Card (Level 1):** Dashboard summary widgets and resting flashcards use `box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03)` wrapped with a `1px` translucent border.
3. **Active/Floating Card (Level 2):** Study flashcards in active focus and floating control docks use `box-shadow: 0 20px 30px -8px rgba(79, 70, 229, 0.08), 0 8px 16px -4px rgba(15, 23, 42, 0.04)`.
4. **Tactile Bottom-Border Depth:** Gamified buttons and rating triggers employ an offset bottom shadow (`box-shadow: 0 3px 0 0 [tinted-darker-shade]`) to give an interactive, satisfying physical key-press feedback when depressed (`transform: translateY(2px)`).

## Shapes
A roundedness level of `2` establishes soft, friendly corners throughout the system.

- **Primary Cards & Modals:** Built with `rounded-2xl` (1.25rem / 20px) to enhance the tactile, physical flashcard metaphor.
- **Buttons, Quiz Option Tiles & Inputs:** Use `rounded-xl` (0.75rem / 12px) for comfortable click targets.
- **Pills, Streak Trackers & Status Badges:** Use full pills (`rounded-full` / 9999px) to communicate atomic status elements cleanly.

## Components

### Buttons
- **Primary Action:** Solid Indigo (`#4F46E5`) with bold text, white typography, and subtle bottom depth. Hover state transitions to `#4338CA`.
- **Gamified Accent Button:** Solid Amber (`#F59E0B`) or Emerald (`#10B981`) for claim actions, level-ups, and streak shares.
- **Ghost/Tertiary:** Transparent fill, Slate-600 text, shifting to soft Indigo tint (`#EEF2FF`) on hover.

### Spaced Repetition (SRS) Rating Bar
Docked persistently at the bottom of the review viewport, showing four tactile keys:
- **Again (1):** Crimson border/tint (`#EF4444`), displays predicted recurrence interval (e.g., `< 1m`).
- **Hard (2):** Orange border/tint (`#F97316`), displays interval (e.g., `12h`).
- **Good (3):** Primary Blue/Indigo (`#4F46E5`), standard target interval (e.g., `1d`).
- **Easy (4):** Emerald Green (`#10B981`), bonus retention jump (e.g., `4d`).
Each trigger shows its corresponding keyboard shortcut (`1`, `2`, `3`, `4`) inside a micro-pill key badge.

### Flashcard Container
- Dual-sided 3D perspective flip container (`perspective: 1000px`, `transform-style: preserve-3d`).
- Minimum height of 360px on desktop with centered, high-contrast typography.
- Subtle card stack background layers visible beneath to communicate remaining deck volume.

### SRS Status Pills
- **New:** Soft Blue background (`#EFF6FF`), text `#1D4ED8`.
- **Learning:** Soft Amber background (`#FEF3C7`), text `#B45309`.
- **Review:** Soft Violet background (`#EDE9FE`), text `#6D28D9`.
- **Mature:** Soft Emerald background (`#D1FAE5`), text `#047857`.

### Gamified Streak & XP Counters
- Streak pill features an animated flame icon with tertiary Amber fill, flanked by current consecutive study days.
- Linear XP progress bar features a 10px tall track (`#E2E8F0`), with an Emerald-to-Teal gradient fill, rounded-full caps, and an animated glow head indicator.

### Quiz Selection Tiles (4-Option Cards)
- Resting state: `border: 1.5px solid #E2E8F0`, white background, letter key prefix (`A`, `B`, `C`, `D`) enclosed in a neutral circle.
- Selected state: `border-color: #4F46E5`, background `#EEF2FF`.
- Success state: `border-color: #10B981`, background `#ECFDF5`.
- Error state: `border-color: #EF4444`, background `#FEF2F2`.

### Navigation Sidebar
- Slim, modern 260px desktop rail featuring icon + label pairs. Active route uses soft `#EEF2FF` fill with Indigo text and an active indicator bar on the left edge.