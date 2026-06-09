# Product

## Register

brand

## Users

First-time apartment buyers in Israel with a budget and no real-estate background. They found a property, they're nervous, and they want to know whether the price is fair before making the biggest financial decision of their lives. They may also be comparing neighborhoods and have no idea where to start. They land on this page looking for a credible, honest tool — not a startup pitch or a government brochure.

## Product Purpose

An AI-powered real estate investment advisor trained on 6,609 real transactions from Israel's Tax Authority. It tells users whether a property's asking price is fair (or not), recommends neighborhoods that match their budget and investment goal, and lets them browse real historical transactions by city. Free, no sign-up required, built as an academic project.

## Brand Personality

Honest, analytical, direct.

Emotional goal: the user should leave feeling *confident and informed* — "this tool told me the truth about the price, I can trust it." Not excited, not impressed by design, not sold to. Just clear.

## Anti-references

- Flashy PropTech SaaS with gradient hero sections, glowing metrics, "10x your portfolio" copywriting, and enterprise pricing tables. This is the exact pattern to avoid.
- Generic AI tool dark-mode template: deep navy background, electric blue accents, glassmorphism stat cards with gradient numbers.
- Government and municipal sites: dense, bureaucratic, gray.
- Real-estate brokerage brochures: white kitchens, stock couples on balconies, glossy magazine feel.

## Design Principles

1. **Earn trust through clarity, not through aesthetics.** Every design choice should make the user feel informed, not impressed. If a section could be misread as marketing, simplify it.
2. **Data is the hero.** The 6,609 transactions and the R² score are the story. Show them as facts, not as marketing ammunition.
3. **Academic honesty.** This is a university project with real limitations (±607,000 ₪ error, 74% R²). Acknowledge that clearly rather than hiding it below the fold. Confidence comes from transparency, not from hiding caveats.
4. **Hebrew-native, not translated.** Right-to-left is a first-class layout decision, not an afterthought. Copy, rhythm, and hierarchy are written for Hebrew readers.
5. **No persuasion architecture.** No countdown timers, no social proof manipulation, no urgency signals. The user is making a serious financial decision — respect that.

## Accessibility & Inclusion

- WCAG 2.1 AA minimum. Body text must hit ≥4.5:1 against background at all sizes.
- Full RTL support. No LTR elements bleeding through without explicit intent.
- Reduced motion: all animations must have a `prefers-reduced-motion` fallback.
- Hebrew script must be legible at all sizes; display fonts that render poorly at small sizes should be avoided for body copy.
