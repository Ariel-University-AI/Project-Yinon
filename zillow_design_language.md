# Zillow — Design Language Analysis

> Reference: https://www.zillow.com/ | Analyzed: May 2026

---

## 1. Brand Identity & Tone

| Attribute | Value |
|-----------|-------|
| **Brand feeling** | Trusted, modern, approachable |
| **Voice** | Helpful, confident, data-driven |
| **Audience** | Homebuyers, renters, sellers — all levels of expertise |
| **Core promise** | "The most trusted real estate marketplace" |

---

## 2. Color Palette

### Primary Colors

| Role | Color | Hex |
|------|-------|-----|
| Primary Blue | Zillow Blue | `#006AFF` |
| Primary Dark | Deep Blue | `#1277E1` |
| Primary Hover | Button Hover | `#0053D6` |

### Neutral Palette

| Role | Color | Hex |
|------|-------|-----|
| Background | Off-White | `#F5F5F5` |
| Card / Surface | Pure White | `#FFFFFF` |
| Dark Text | Charcoal | `#2A2A33` |
| Secondary Text | Medium Gray | `#696969` |
| Subtle Text | Light Gray | `#9A9A9A` |
| Dividers / Borders | Very Light Gray | `#E0E0E0` |

### Accent / Status Colors

| Role | Color | Hex |
|------|-------|-----|
| Success / Savings | Green | `#1A9E3F` |
| Warning / Alert | Amber | `#F5A623` |
| Error / Price Drop | Red | `#D9534F` |
| "Zestimate" Brand | Teal Accent | `#00A2AD` |

### Hero Section

- Large photo/illustration backgrounds with **dark overlay gradients**
- Gradient: `linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.10))`

---

## 3. Typography

### Font Family

```
Primary: "Circular", "Graphik", or system fallback:
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
```

Zillow uses a **geometric humanist sans-serif** — clean, neutral, optimized for data display.

### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| Display XL | 48–56px | 700 | 1.1 | Hero headlines |
| Display L | 36–42px | 700 | 1.2 | Section headers |
| Heading 1 | 28–32px | 600–700 | 1.25 | Page titles |
| Heading 2 | 22–24px | 600 | 1.3 | Card headers |
| Heading 3 | 18–20px | 600 | 1.35 | Sub-sections |
| Body L | 16px | 400 | 1.5 | Main body text |
| Body M | 14px | 400 | 1.5 | Secondary info |
| Caption | 12px | 400 | 1.4 | Labels, metadata |
| Micro | 10–11px | 500 | 1.3 | Tags, badges |

### Price Display (Critical Element)

```
font-size: 22–28px;
font-weight: 700;
color: #2A2A33;
```

---

## 4. Spacing & Grid

### Base Unit: 8px

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon gap, tight labels |
| sm | 8px | Internal card padding |
| md | 16px | Component spacing |
| lg | 24px | Section spacing |
| xl | 32px | Major section gaps |
| 2xl | 48px | Hero padding |
| 3xl | 64–80px | Page section separation |

### Layout Grid

- Desktop: **12-column grid**, max-width `1440px`, gutters `24px`
- Tablet: **8-column grid**
- Mobile: **4-column grid**, 16px side margins
- Listing cards: `repeat(auto-fill, minmax(280px, 1fr))` grid

---

## 5. Border Radius

| Component | Radius |
|-----------|--------|
| Buttons | `4–6px` (slightly rounded, not pill) |
| Input fields | `4px` |
| Listing cards | `8px` |
| Map pins | `50%` (circle) + rectangular callout |
| Badges / tags | `2–4px` |
| Modal dialogs | `12px` |
| Pill filters | `20–24px` (full pill) |
| Avatar images | `50%` |

---

## 6. Shadows & Elevation

```css
/* Card resting */
box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

/* Card hover */
box-shadow: 0 4px 16px rgba(0, 0, 0, 0.14);

/* Sticky navbar */
box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);

/* Modal / drawer */
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);

/* Map popup */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.20);
```

Elevation is **subtle and purposeful** — no dramatic shadows. Cards lift slightly on hover.

---

## 7. UI Components

### Search Bar (Hero Element)

```
Background: white
Height: 52–60px
Border-radius: 4px
Border: none (shadow only)
Shadow: 0 4px 16px rgba(0,0,0,0.18)
Internal padding: 12px 16px
Placeholder text: color #9A9A9A
CTA button: #006AFF, white text, rounded right side
```

The search bar is the **visual anchor** of every page.

### Buttons

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| Primary | `#006AFF` | White | None |
| Primary Hover | `#0053D6` | White | None |
| Secondary | White | `#006AFF` | `1px solid #006AFF` |
| Ghost | Transparent | `#006AFF` | None |
| Danger | `#D9534F` | White | None |
| Disabled | `#E0E0E0` | `#9A9A9A` | None |

- Padding: `10–12px 20–24px`
- Font-weight: 500–600
- Letter-spacing: `0` (no tracking)
- Transition: `0.15s ease`

### Listing Card (Core Component)

```
┌─────────────────────────────┐
│  [Photo — 16:9 aspect]      │  ← heart icon top-right
│  [Save badge if saved]      │
├─────────────────────────────┤
│  $425,000                   │  ← price, 22px bold
│  3 bd | 2 ba | 1,240 sqft   │  ← specs, 14px medium
│  123 Main St, City, ST      │  ← address, 14px regular gray
│  [Zestimate badge]          │  ← teal accent
│  [Days on market tag]       │
└─────────────────────────────┘
```

- Card width: 280–340px
- Photo ratio: 16:9
- Hover: shadow intensifies, slight translateY(-2px)
- Save heart: outline → filled red on save (animated)

### Filter Pills (Horizontal scroll on mobile)

```
background: white;
border: 1px solid #D1D1D1;
border-radius: 20px;
padding: 6px 16px;
font-size: 14px;
font-weight: 500;
```

Active state: `background: #EBF3FF; border-color: #006AFF; color: #006AFF`

### Map Integration

- Full-bleed interactive map (Mapbox or Google Maps)
- Split-view: listings left, map right (50/50 on desktop)
- Map pins: circular blue dots with price labels
- Selected pin: enlarged, white background, blue border
- Cluster pins: circle with count badge

---

## 8. Navigation

### Desktop Top Nav

```
Height: 64px
Background: white
Border-bottom: 1px solid #E0E0E0
Sticky: yes
Logo: left
Links: Buy | Rent | Sell | Home Loans | Agent Finder
CTA: "Sign In" outline button + optional "Post a listing"
```

### Mobile Bottom Nav

```
Fixed bottom bar
5 icons: Home | Search | Save | Map | Profile
Height: 56px + safe area
Active icon: #006AFF
Inactive: #9A9A9A
```

---

## 9. Iconography

- Style: **Line icons**, 2px stroke weight, rounded caps
- Size: 16px, 20px, 24px grid
- Color: inherits from text context (`#696969` secondary, `#2A2A33` primary)
- Special: Filled icons only for interactive states (saved heart = filled red)
- Amenity icons: bed, bath, sqft, garage — consistent set

---

## 10. Imagery Style

| Type | Style |
|------|-------|
| Hero backgrounds | Full-bleed exterior home photography, golden hour light, aspirational |
| Listing photos | User-submitted / professional, 16:9, auto-carousel |
| Illustrations | Flat, geometric, limited palette — used in empty states and onboarding |
| Maps | Muted/light basemap to let listing pins pop |
| Agent avatars | Circular crop, professional headshots |

---

## 11. Motion & Animation

| Interaction | Animation |
|-------------|-----------|
| Card hover | `transform: translateY(-2px)` + shadow, `0.2s ease` |
| Save heart | Scale bounce + color fill, `0.3s spring` |
| Photo carousel | Slide, `0.4s ease-in-out` |
| Map pin select | Scale up `1.2x`, `0.15s ease` |
| Filter drawer open | Slide from right, `0.3s ease` |
| Skeleton loader | Shimmer gradient animation |
| Page transitions | Fade, `0.2s` |

Philosophy: **purposeful and fast** — never decorative, always responsive to intent.

---

## 12. Key Design Patterns

### Information Hierarchy on Listing Cards
1. Price (largest, boldest)
2. Bed/bath/sqft specs
3. Address
4. Status/Zestimate metadata

### Progressive Disclosure
- Summary on card → full detail on listing page
- Filters collapsed by default → expand on tap
- Contact agent form behind CTA button

### Trust Signals
- Zestimate badge (proprietary data)
- Days on market
- "Listed by [Brokerage]"
- Agent reviews/ratings

### Empty States
- Illustrated character + friendly message
- Single clear CTA to adjust search

---

## 13. Accessibility

- Contrast ratio: 4.5:1 minimum for body text
- Focus rings: `2px solid #006AFF` with `2px offset`
- Touch targets: minimum 44x44px
- Skip navigation link
- ARIA labels on map pins and icon-only buttons

---

## 14. Mobile-First Principles

- Everything works touch-first
- Bottom sheet for filters and detail panels
- Swipe gestures on photo carousels
- Map + list toggle (not always split)
- Persistent search bar at top of scroll
- Large, tap-friendly price and CTA targets

---

## Summary — Design Principles

| Principle | Expression |
|-----------|-----------|
| **Clarity** | Data is king — price, specs, location always front-and-center |
| **Trust** | Consistent blue brand, clean data presentation, no clutter |
| **Speed** | Subtle animation, skeleton loaders, no gratuitous motion |
| **Utility** | Every element earns its place — no decoration for decoration's sake |
| **Scalability** | Works on mobile just as well as on a 4K monitor |
