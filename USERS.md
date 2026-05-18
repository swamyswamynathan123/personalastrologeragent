# Personal Astrologer Agent — User Guide

## What is this app?

Personal Astrologer Agent is an AI-powered astrology platform that computes your full natal chart and generates a personalised, multi-section reading using both Western and Vedic traditions. Unlike apps that stitch together pre-written paragraphs, every reading is written fresh by an AI astrologer anchored to your exact planetary positions, degrees, and current timing layers.

---

## Getting Started

### Step 1 — Enter your birth details

Open the sidebar and fill in the form. Fields marked `*` are required.

| Field | What it is | Tips |
|---|---|---|
| **Full Name** | Used to personalise the reading | Any name or nickname works |
| **Date of Birth** | Determines all planetary positions | Must be exact |
| **Birth Time** | The most important field after date | Even 15 minutes can change your Ascendant and all 12 houses. Use a birth certificate or hospital records if available. |
| **Birth Time Confidence** | How certain you are of the time | See section below |
| **Birth Location** | Where you were born | Format: `City, Region, Country` — e.g., `Mumbai, Maharashtra, India` |
| **Birth Timezone** | The timezone of your birth location | This is the timezone of where you were born, not where you live now |
| **House System** | How the sky is divided into 12 life areas | If unsure, leave as Placidus |
| **Current Location** | Where you live now | Used for transits, Solar Return, and Lunar Return charts |

### Step 2 — Add optional context

- **Additional Context** — Share life events, decisions, questions, or concerns you want the reading to address. The more specific you are, the more relevant the guidance.
- **Report Focus** — Select one or more life areas for a dedicated deep-dive section at the end of your report.

### Step 3 — Generate your reading

Click **Generate My Reading ⭐**. The app will:
1. Validate your details and show any issues inline
2. Compute your full natal chart (~15 seconds)
3. Stream your reading live in 3 parts as the AI writes it

---

## Birth Time Confidence

Your birth time affects a large portion of the reading — particularly your Ascendant sign, all 12 house cusps, and all house-based timing predictions.

| Setting | When to use | Effect on reading |
|---|---|---|
| **Exact** | You have it from official records | Full house-based interpretation, no caveats |
| **Approximate** | You were told a rough time (±30 min) | House interpretations are softened; a birth-time rectification section is added |
| **Unknown** | No time available | Reading focuses on sign-based factors; rectification guidance added |

> **Tip:** If you don't know your birth time, set it to 12:00 noon and choose **Unknown**. The reading will still cover Sun sign, Moon sign, planetary aspects, and all timing layers — only house-specific interpretations will be uncertain.

---

## House Systems Explained

| System | Background | Best for |
|---|---|---|
| **Placidus** | Standard in modern Western astrology | Most people; the default |
| **Whole Sign** | Oldest system; used in Hellenistic and Vedic traditions | Those interested in traditional or Vedic crossover readings |
| **Koch** | Popular in German-speaking countries; emphasises the MC axis | Career-focused readings |

---

## Understanding Your Reading

Your reading is generated in 9 sections (10 with a Focus selected), streamed live in 3 parts.

### Part 1 — Identity & Soul

**Section 1 — Personal Overview**
Your core character portrait: Sun + Moon + Ascendant as a unified trio, chart ruler's condition, elemental and modal balance, and any life-defining fixed star contacts or anaretic degrees.

**Section 2 — Life Direction & Karmic Themes**
North and South Node axis (soul direction vs. comfort-zone traps), Chiron's wound and healing gift, aspect patterns (Grand Cross, T-Square, Grand Trine, Yod) as structural life architecture.

**Section 3 — Current Life Phase**
Your progressed chart: the psychological chapter you are living through right now. Progressed Sun sign, Progressed Moon's 2.5-year emotional climate, and the progressed lunation phase (where you are in a ~30-year psychological cycle).

---

### Part 2 — Timing & Cosmic Climate

**Section 4 — Current Cosmic Climate**
Three timing layers read together:
- **Firdaria** (Western biographical arc — multi-year life chapter)
- **Vimshottari Dasha** (Vedic biographical arc — cross-tradition confirmation)
- **Annual Profection** (which life area is activated this year)

Plus current transits, solar arc milestones, primary directions, and eclipse sensitivity.

**Section 5 — Key Life Themes**
3–4 dominant themes active in your chart right now, each supported by at least two independent chart factors.

**Section 6 — Practical Guidance**
3–4 specific, actionable items tied to applying transits and solar arcs, with approximate timeframes. Includes monthly profection timing for the most precise month-by-month advice.

**Section 7 — Favorable Timing**
2–3 specific upcoming windows — what each is good for and why, based on the activating aspect.

---

### Part 3 — Advanced Timing & Vedic Analysis

**Section 8 — Top 5 Exact Timing Windows**
A scannable table of the 5 most significant upcoming planetary events, pre-ranked by importance. Each entry includes the date, life area activated, and one sentence of actionable guidance.

**Section 9 — Vedic Full Reading**
A complete Jyotish interpretation including:
- Moon's nakshatra (the most important Vedic datum)
- Sidereal Sun and Lagna (how they differ from tropical positions)
- D9 Navamsha synopsis (soul-level dharmic qualities)
- Vimshottari Dasha interpretation (current biographical chapter in Vedic timing)
- Vedic yogas (special planetary combinations and what they promise)

**Section 10 — Focus Deep Dive** *(only when Report Focus is selected)*
A dedicated section going deeper on your chosen life areas, identifying the most active timing indicators for that specific domain right now.

---

## Saving and Loading Charts

### Save a reading
After your reading generates, click **💾 Save Reading**. Your chart data and report are stored locally and can be reloaded in any future session from the **📚 My Saved Charts** panel.

### Load a saved chart
Open **📚 My Saved Charts** in the sidebar, find your chart, and click **Load**. Your previous reading reloads instantly from cache — no API call needed.

### Regenerate a reading
Click **↺ Regenerate Reading** to force a fresh AI-generated report. Use this when:
- You want to change your Report Focus
- The reading cached from a previous day feels stale
- You want a fresh perspective on the same chart

---

## Transit Calendar

The **Transit Calendar** tab shows outer-planet transit activity for your chart across the current month, with:

- **Transit Timeline** — a Gantt-style chart showing when each outer planet forms a major aspect to a natal point over the next 12 months. Wider bars = multi-pass (retrograde) transits. Hover a bar for exact dates.
- **Monthly Calendar** — day-by-day transit events colour-coded by aspect type (harmonious / challenging / neutral).

---

## Compatibility (Synastry)

The **Compatibility** tab generates a full synastry reading between two people.

1. Enter Person A's details (pre-filled if you have a saved chart)
2. Enter Person B's details
3. Click **Explore Compatibility ✨**

The reading covers:
- Cross-chart aspects (how your planets interact)
- House overlays (which areas of life each person activates for the other)
- Composite chart (the relationship as its own entity)
- Timing (what is currently being activated in the relationship dynamic)

---

## Forecasts

The **Forecasts** tab provides four AI-generated forward-looking reports based on your current transits and timing layers:

| Forecast | Covers |
|---|---|
| **Weekly** | The next 7 days — most actionable timing |
| **Monthly** | The next 30 days — lunar cycle and profection focus |
| **Yearly** | The next 12 months — Solar Return and major transits |
| **Overall** | Long-range themes across the next 2–3 years |

---

## Follow-Up Chat

After your reading generates, a chat interface appears at the bottom of the **My Reading** tab. Ask any question about your chart — "Why did you say that about my Saturn?", "What does my 7th house ruler being in the 12th mean?", or "When is the best time to start a new project?" — and the AI responds with full chart context.

---

## Tips for the Best Reading

1. **Use your exact birth time if possible.** It is the single most impactful piece of data. Even 15 minutes shifts the Ascendant and all house cusps.

2. **Be specific in Additional Context.** "I'm considering leaving my job to start a business in September" gives the AI far more to work with than "career."

3. **Select a Report Focus for deeper guidance.** The 9 sections cover everything broadly; a Focus gives you a dedicated lens on what matters most to you right now.

4. **Read Part 1 before Part 2.** The sections build on each other — your natal character (Part 1) is the foundation for understanding the timing (Part 2).

5. **Use the follow-up chat.** The reading is a starting point. The chart-aware chat is where you can go as deep as you want on any theme.

6. **Regenerate after a major life event.** The reading is tied to the current date. Regenerating 6 months later gives you a fresh timing layer with new transits and profection house.

---

## Frequently Asked Questions

**Why does my birth time matter so much?**
Your birth time determines your Ascendant (Rising sign) and all 12 house cusps. The houses define which life area each planet governs for you specifically. Two people born on the same day in the same city but 2 hours apart can have completely different Ascendants, house rulers, and life themes.

**What is the difference between Western and Vedic astrology?**
Western (tropical) astrology uses a zodiac anchored to the seasons — the Sun is always in Aries at the spring equinox. Vedic (sidereal) astrology uses a zodiac anchored to the fixed stars, which has shifted ~24° from the tropical zodiac over 2,000 years. Most of your planets will be one sign earlier in your Vedic chart. This app uses Western as the primary framework and Vedic as a cross-tradition confirmation layer.

**What is a house system?**
The sky is divided into 12 segments (houses), each governing a life area. Different mathematical methods of dividing the sky produce slightly different house cusps. Placidus is the most common in modern Western astrology; Whole Sign (one sign = one house) is the oldest and simplest.

**What is a natal aspect?**
An aspect is an angular relationship between two planets (e.g., 90° = square, 120° = trine, 180° = opposition). Aspects describe how two planetary energies interact in your personality and life experience.

**Why does the reading sometimes take 30+ seconds?**
The app first computes your full natal chart including transits, progressions, solar arc, Vedic overlay, primary directions, and 12+ other layers (~15 seconds). It then generates a 9-section reading across 3 separate AI calls, streamed live. You will see the first sections appear while later sections are still being written.

**Can I use this without knowing astrology?**
Yes. The reading is written in plain language without assuming prior astrological knowledge. Use the tooltips (ⓘ) on the form for guidance on each field. The follow-up chat is also useful for clarifying any terms or concepts in the reading.

---

## Glossary

| Term | Meaning |
|---|---|
| **Ascendant (Rising)** | The zodiac sign on the eastern horizon at the moment of your birth. Governs your appearance, first impressions, and the lens through which you experience life. |
| **Midheaven (MC)** | The highest point in the sky at birth. Governs career, public reputation, and life direction. |
| **Transit** | A planet's current position in the sky forming an aspect to a natal planet in your chart. |
| **Progression** | A symbolic movement of your natal chart forward in time (1 day after birth = 1 year of life). Shows psychological development. |
| **Solar Arc** | Every natal planet moved forward by the same amount as the Sun has travelled since birth. Marks concrete external turning points. |
| **Primary Direction** | The oldest Western timing method. Marks biographical milestones with high precision. |
| **Profection** | An annual timing technique that activates one house (life area) per year of life. |
| **Firdaria** | A Persian time-lord system dividing life into planetary periods of varying lengths. |
| **Vimshottari Dasha** | The primary Vedic timing system dividing life into planetary periods totalling 120 years. |
| **Nakshatra** | One of 27 lunar mansions in Vedic astrology. The Moon's nakshatra is the most important Vedic placement. |
| **Navamsha (D9)** | A Vedic divisional chart showing soul-level qualities, dharma, and marriage themes. |
| **Synastry** | Comparison of two natal charts to assess relationship dynamics. |
| **Composite Chart** | A chart created from the midpoints of two people's planets, representing the relationship as its own entity. |
| **Dignity** | A planet's strength based on its sign: domicile (strongest) → exaltation → neutral → detriment → fall (most challenged). |
| **Retrograde (Rx)** | A planet appearing to move backward from Earth's perspective. Associated with internalisation and review of that planet's themes. |
| **Anaretic degree** | A planet at 29° of any sign — carries urgency and a drive to resolve that sign's themes. |
| **Aspect pattern** | A configuration of 3+ planets forming a geometric shape (Grand Trine, T-Square, Grand Cross, Yod). Represents structural life themes. |
| **Part of Fortune** | An Arabic Part (calculated point) showing the area of natural ease and abundance. |
| **Chiron** | A minor planet associated with a core wound and the healing gift that emerges from it. |
