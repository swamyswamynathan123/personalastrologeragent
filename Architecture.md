# Architecture

## Color Key

| Color | Meaning |
|---|---|
| 🔵 Blue | User input / UI |
| 🟣 Purple | Computation / processing |
| 🟠 Amber | LLM / AI |
| 🟢 Green | Output / result |
| 🔴 Red | Error path |
| ⬛ Dark | State / data store |

---

## System Overview

```mermaid
graph TB
    classDef uiNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef computeNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef llmNode fill:#4a3000,stroke:#c8860a,color:#ffd580
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8
    classDef externalNode fill:#2a2a2a,stroke:#666,color:#ccc

    subgraph Browser
        UI[Streamlit UI\napp.py]:::uiNode
    end

    subgraph LangGraph["LangGraph Pipeline (agent/)"]
        PG[prepare_graph\nvalidate + compute]:::computeNode
        FG[graph\nfull pipeline + LLM]:::computeNode
    end

    subgraph Astro["Chart Engine (astro/)"]
        KC[kerykeion\nAstrologicalSubject]:::computeNode
        SW[pyswisseph\nasteroids]:::computeNode
        GEO[GeoNames API\ngeocoding]:::externalNode
    end

    subgraph LLM["LLM Layer (llm/)"]
        RP[report.py\nprompt builder]:::llmNode
        OAI[OpenAI GPT-4o\nstreaming]:::externalNode
    end

    UI -- "form submit" --> PG
    PG -- "_prepared_state" --> UI
    UI -- "st.write_stream()" --> RP
    RP -- "streaming tokens" --> OAI
    OAI -- "text chunks" --> UI
    PG --> KC
    KC --> GEO
    KC --> SW
    FG --> RP
    RP --> OAI
```

---

## LangGraph Graphs

### `prepare_graph` — used by `app.py` on form submission

```mermaid
flowchart TD
    classDef uiNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef processNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef errorNode fill:#3a1a1a,stroke:#a52a2a,color:#f8b4b4
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8
    classDef decisionNode fill:#1a1a3a,stroke:#4a4a8a,color:#c8c8f8

    S([START]):::uiNode
    A[ingest_inputs\nreset tracking fields]:::processNode
    B[validate_required_fields\ncheck presence + format]:::processNode
    C{missing or errors?}:::decisionNode
    D[request_follow_up\nbuild error message]:::errorNode
    E[normalize_and_parse\nparse datetimes + tz]:::processNode
    F{parse errors?}:::decisionNode
    G[compute_astro\nkerykeion + swisseph]:::outputNode
    Z([END]):::uiNode

    S --> A --> B --> C
    C -- yes --> D --> Z
    C -- no --> E --> F
    F -- yes --> D
    F -- no --> G --> Z
```

### `graph` — full pipeline (integration tests only)

```mermaid
flowchart TD
    classDef uiNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef processNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef errorNode fill:#3a1a1a,stroke:#a52a2a,color:#f8b4b4
    classDef llmNode fill:#4a3000,stroke:#c8860a,color:#ffd580
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8
    classDef decisionNode fill:#1a1a3a,stroke:#4a4a8a,color:#c8c8f8

    S([START]):::uiNode
    A[ingest_inputs]:::processNode
    B[validate_required_fields]:::processNode
    C{missing or errors?}:::decisionNode
    D[request_follow_up]:::errorNode
    E[normalize_and_parse]:::processNode
    F{parse errors?}:::decisionNode
    G[compute_astro]:::processNode
    H[generate_report_node\nGPT-4o blocking call]:::llmNode
    Z([END]):::uiNode

    S --> A --> B --> C
    C -- yes --> D --> Z
    C -- no --> E --> F
    F -- yes --> D
    F -- no --> G --> H --> Z
```

---

## `AstrologerState` Data Flow

Each node in the LangGraph pipeline reads and writes specific keys of `AstrologerState`. This diagram shows the full lifecycle of every state field.

```mermaid
flowchart TD
    classDef inputKey fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1,font-size:11px
    classDef validKey fill:#3a1a1a,stroke:#a52a2a,color:#f8b4b4,font-size:11px
    classDef parsedKey fill:#2d1b4e,stroke:#8866cc,color:#d4bfff,font-size:11px
    classDef chartKey fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8,font-size:11px
    classDef outputKey fill:#4a3000,stroke:#c8860a,color:#ffd580,font-size:11px
    classDef nodeBox fill:#111,stroke:#555,color:#eee,font-size:12px

    subgraph Raw["Raw Inputs — set by app.py"]
        I1[full_name]:::inputKey
        I2[dob]:::inputKey
        I3[birth_location]:::inputKey
        I4[birth_time]:::inputKey
        I5[birth_time_timezone]:::inputKey
        I6[birth_time_confidence]:::inputKey
        I7[house_system]:::inputKey
        I8[current_location]:::inputKey
        I9[current_datetime]:::inputKey
        I10[report_focus]:::inputKey
        I11[additional_info]:::inputKey
    end

    subgraph N1["ingest_inputs"]
        N1B[ ]:::nodeBox
    end

    subgraph Tracking["Validation Tracking — reset by ingest_inputs"]
        V1[missing_fields = \[\]]:::validKey
        V2[validation_errors = \{\}]:::validKey
        V3[parsed_dob = None]:::parsedKey
        V4[parsed_birth_datetime = None]:::parsedKey
        V5[parsed_current_datetime = None]:::parsedKey
        V6[chart_data = None]:::chartKey
        V7[follow_up_message = None]:::outputKey
        V8[final_report = None]:::outputKey
    end

    Raw --> N1
    N1 --> Tracking

    subgraph N2["validate_required_fields"]
        N2B[ ]:::nodeBox
    end

    Tracking --> N2

    subgraph V["Written by validate_required_fields"]
        V9[missing_fields]:::validKey
        V10[validation_errors]:::validKey
    end

    N2 --> V

    subgraph N3["normalize_and_parse"]
        N3B[ ]:::nodeBox
    end

    V --> N3

    subgraph P["Written by normalize_and_parse"]
        P1[parsed_dob]:::parsedKey
        P2[parsed_birth_datetime]:::parsedKey
        P3[parsed_current_datetime]:::parsedKey
    end

    N3 --> P

    subgraph N4["compute_astro"]
        N4B[ ]:::nodeBox
    end

    P --> N4

    subgraph C["Written by compute_astro"]
        C1[chart_data\nfull astrological dict]:::chartKey
    end

    N4 --> C

    subgraph N5["generate_report_node"]
        N5B[ ]:::nodeBox
    end

    C --> N5

    subgraph O["Written by generate_report_node"]
        O1[final_report]:::outputKey
    end

    N5 --> O
```

**Key reads by node:**

| Node | Reads | Writes |
|---|---|---|
| `ingest_inputs` | all raw inputs from state | resets: `missing_fields=[]`, `validation_errors={}`, `parsed_*=None`, `chart_data=None`, `follow_up_message=None`, `final_report=None` |
| `validate_required_fields` | all raw inputs | `missing_fields`, `validation_errors` |
| `request_follow_up` | `missing_fields`, `validation_errors` | `follow_up_message`, `final_report=None` |
| `normalize_and_parse` | `dob`, `birth_time`, `birth_time_timezone`, `current_datetime` | `parsed_dob`, `parsed_birth_datetime`, `parsed_current_datetime` |
| `compute_astro` | `parsed_birth_datetime`, `parsed_current_datetime`, `birth_location`, `current_location`, `birth_time_timezone`, `house_system`, `full_name` | `chart_data` |
| `generate_report_node` | entire state (passed to `build_prompt`) | `final_report` |

---

## Streamlit Rendering State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle : page load

    Idle --> Computing : form submitted\nclear report_result\nclear _stream_error

    Computing --> ValidationFailed : follow_up_message set
    Computing --> Prepared : _prepared_state set\n(chart computed)
    Computing --> UnexpectedError : neither set

    ValidationFailed --> Idle : user corrects inputs\nand resubmits

    Prepared --> StreamError : API failure\nduring st.write_stream()
    StreamError --> Prepared : Retry clicked\n_stream_error = None
    Prepared --> Streaming : st.write_stream() begins\n(no _stream_error)
    Streaming --> Rerunning : stream complete\nreport_result set\n_prepared_state = None
    Rerunning --> StyledReport : st.rerun() fires

    StyledReport --> StyledReport : follow-up chat\nanswer_followup_stream()
    StyledReport --> HouseMismatch : sidebar house_system\nchanged in form
    HouseMismatch --> Computing : Generate clicked\nwith new house_system
    StyledReport --> Computing : form resubmitted

    UnexpectedError --> Idle : user retries
```

---

## Natal Chart Computation — Part 1: Static Analysis

```mermaid
flowchart TD
    classDef inputNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef computeNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8
    classDef externalNode fill:#2a2a2a,stroke:#666,color:#ccc

    SUBJ[AstrologicalSubject\nkerykeion]:::computeNode
    GEO[GeoNames API\ngeocoding + lat/lon]:::externalNode
    HS[house_system param\nP / W / K]:::inputNode

    SUBJ --> GEO
    HS --> SUBJ

    SUBJ --> P[Planets\nSun · Moon · Mercury · Venus · Mars\nJupiter · Saturn · Uranus · Neptune · Pluto\nChiron · Ascendant · Midheaven]:::outputNode
    SUBJ --> H[House Cusps\nall 12, with sign + position]:::outputNode
    SUBJ --> NN[Lunar Nodes\nNorth + South Node]:::outputNode

    P --> DIG[Essential Dignities\ndomicile · exaltation\ndetriment · fall]:::outputNode
    P --> BAL[Elemental & Modal Balance\nFire/Earth/Air/Water\nCardinal/Fixed/Mutable]:::outputNode
    P --> SECT[Planetary Sect\nday vs night chart\nin-sect / out-of-sect]:::outputNode
    P --> LP[Lunar Phase\nnatal Moon archetype]:::outputNode
    P --> POF[Part of Fortune\n& Arabic Parts\nday/night formula]:::outputNode

    H --> HR[House Rulers\nnatal condition of each\nhouse's ruling planet]:::outputNode
    H & P --> CR[Chart Ruler\nASC sign → ruling planet\nsign · house · dignity]:::outputNode

    P & H & NN --> ASP[Natal Aspects\nconjunction / sextile / square\ntrine / opposition\napplying vs separating]:::outputNode
    ASP --> PAT[Aspect Patterns\nGrand Trine · T-Square\nYod · Grand Cross · Kite]:::outputNode

    SW[pyswisseph\nJulian day calc]:::externalNode
    SW --> AST[Major Asteroids\nCeres · Pallas · Juno · Vesta\nsign · house · retrograde]:::outputNode

    P & H --> FS[Fixed Stars\n1° orb conjunctions\nRoyal Stars · Algol · Spica etc.]:::outputNode
    P & H --> ANA[Anaretic Degrees\nplanets at 29°]:::outputNode
    P --> ANT[Antiscia\nsolstice-point connections\nantiscia + contra-antiscia]:::outputNode
    P --> MR[Mutual Receptions\nplanets in each other's signs]:::outputNode
    P --> STELL[Stelliums\n3+ planets same sign or house]:::outputNode
```

---

## Natal Chart Computation — Part 2: Predictive Layer

```mermaid
flowchart TD
    classDef inputNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef computeNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8

    NATAL[Natal Chart Dict\nchart_data]:::inputNode
    NOW[Current Datetime\n+ Location]:::inputNode

    NATAL & NOW --> TR[Current Transits\nouter + inner planets\nto natal chart · 3° orb\napplying / separating]:::outputNode

    NATAL & NOW --> UT[Upcoming Transits\nnext 90 days\nouter planets only\nexact dates + min orb]:::outputNode

    NATAL & NOW --> PROG[Secondary Progressions\nprogressed date = birth + age\nSun · Moon · Mercury\nVenus · Mars · ASC · MC]:::outputNode

    PROG & NATAL --> PA[Progressed Aspects\nto natal chart\n1° orb]:::outputNode

    PROG & NATAL --> SA[Solar Arc Directions\narc = progressed Sun − natal Sun\nall bodies directed forward]:::outputNode

    SA & NATAL --> SAA[Solar Arc Aspects\nto natal chart · 1° orb\napplying = event within ~1yr]:::outputNode

    NATAL & NOW --> SR[Solar Return Chart\nannual return moment\nSR ASC · SR Moon\nangular planets\nhighlighted houses]:::outputNode

    NATAL & NOW --> PRO[Annual Profection\nage → activated house\nlord of the year\nnatal condition of lord]:::outputNode

    NATAL & NOW --> FIR[Firdaria Time Lords\nmajor period · sub-period\nnatal condition of each lord\nyears remaining]:::outputNode

    NATAL --> SVG1[Natal Chart SVG\nKerykeionChartSVG\nwheel diagram]:::outputNode
    NATAL & NOW --> SVG2[Transit Overlay SVG\nKerykeionChartSVG\nnatal + current sky wheels]:::outputNode
```

---

## Natal Chart Computation — Part 3: Vedic Overlay

```mermaid
flowchart TD
    classDef inputNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef computeNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8

    NATAL[Tropical Positions\nchart_data]:::inputNode
    AYA[Lahiri Ayanamsa\n~24° subtracted]:::computeNode

    NATAL --> AYA

    AYA --> SID[Sidereal Positions\nSun · Moon · ASC · MC\nMercury through Pluto]:::outputNode

    SID --> NAK[Moon Nakshatra\n27 lunar mansions\nname · lord · pada]:::outputNode

    SID --> NAV[Navamsha D9\nsoul-level sign\nmarriage / dharma chart]:::outputNode

    SID --> DASH[Vimshottari Dasha\nMahadasha — 6 to 20 yr period\nAntardasha — sub-period\nyears remaining for each]:::outputNode

    SID --> YOGA[Vedic Yogas]:::outputNode

    YOGA --> Y1[Pancha Mahapurusha\nRuchaka · Bhadra · Hamsa\nMalavya · Shasha\nexceptional talent yogas]:::outputNode
    YOGA --> Y2[Gajakesari Yoga\nJupiter in kendra from Moon\nresilience + wisdom]:::outputNode
    YOGA --> Y3[Raj Yogas\nkendra-trikona lord links\nauthority + success]:::outputNode
    YOGA --> Y4[Neecha Bhanga Raj Yoga\ncancelled debilitation\nearly struggle → strength]:::outputNode
    YOGA --> Y5[Dhana Yogas\nfinancial capacity indicators]:::outputNode
```

---

## Synastry Computation Pipeline

```mermaid
flowchart TD
    classDef inputNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef computeNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef llmNode fill:#4a3000,stroke:#c8860a,color:#ffd580
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8
    classDef stateNode fill:#1a2a2a,stroke:#2d6a6a,color:#a8d8d8

    CA[chart_a\nPerson A natal dict]:::inputNode
    CB[chart_b\nPerson B natal dict\ncomputed fresh]:::inputNode

    CA & CB --> SYN[compute_synastry]:::computeNode

    SYN --> XA[Inter-chart Aspects\nA planets ↔ B planets\n6° orb · applying/separating]:::outputNode
    SYN --> OVba[House Overlays\nB's planets in A's houses\nkey planets only]:::outputNode
    SYN --> OVab[House Overlays\nA's planets in B's houses]:::outputNode
    SYN --> COMP[Composite Chart\nmidpoint of each planet pair]:::outputNode
    COMP --> CASP[Composite Aspects\ntop aspects of the\nrelationship entity]:::outputNode

    XA & OVba & OVab & COMP & CASP --> PREP[_synastry_prepared\nsession state]:::stateNode

    PREP --> PROMPT[build_synastry_prompt]:::llmNode
    PROMPT --> GPT[OpenAI GPT-4o\nstream=True]:::llmNode
    GPT --> STREAM[st.write_stream\nlive token render]:::outputNode
    STREAM --> SYN_RESULT[synastry_result\nsession state]:::stateNode
    SYN_RESULT --> RERUN[st.rerun\nstyled dark card]:::outputNode
```

---

## LLM Prompt Architecture

```mermaid
flowchart TD
    classDef inputNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef llmNode fill:#4a3000,stroke:#c8860a,color:#ffd580
    classDef outputNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8
    classDef sectionNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff

    STATE[AstrologerState\nchart_data dict]:::inputNode

    STATE --> BP[build_prompt]:::llmNode

    BP --> PD[Person Details\nname · DOB · location\nbirth time · confidence\nhouse system · focus]:::sectionNode
    BP --> PLAC[Natal Placements\nall planets + angles\nwith dignity + retrograde]:::sectionNode
    BP --> SPEC[20+ Formatted Sections\ntransits · progressions · solar arcs\nfirdaria · profection · vedic\nasteroids · fixed stars etc.]:::sectionNode
    BP --> RULES[Interpretation Rules\ndignity · sect · timing priority\nastiscia · yoga meanings]:::sectionNode
    BP --> SYNTH[Synthesis Protocol\nconvergence detection\nurgency ranking]:::sectionNode
    BP --> INST[Report Instructions\n7 sections defined\nPersonal Overview through\nFavorable Timing]:::sectionNode

    PD & PLAC & SPEC & RULES & SYNTH & INST --> MSG[messages list\nsystem + user]:::llmNode

    MSG --> STREAM[generate_report_stream\nyields text chunks\nused in app.py]:::llmNode
    MSG --> BLOCK[generate_report\nblocking — tests only]:::llmNode

    STREAM --> WS[st.write_stream\nlive render]:::outputNode
    WS --> STORED[report_result\nsession state]:::outputNode
    STORED --> CARD[styled report-card div\nmarkdown → HTML\nvia python-markdown]:::outputNode

    STORED --> FU[answer_followup_stream\nreport prepended as\nassistant turn\nchat history appended]:::llmNode
    FU --> CHAT[st.chat_message\nstreaming reply]:::outputNode
```

---

## Module Dependencies

```mermaid
graph TD
    classDef uiNode fill:#1e3a5f,stroke:#4a6fa5,color:#d4e6f1
    classDef agentNode fill:#2d1b4e,stroke:#8866cc,color:#d4bfff
    classDef astroNode fill:#1a3a2a,stroke:#2d7a4f,color:#a8d8b8
    classDef llmNode fill:#4a3000,stroke:#c8860a,color:#ffd580
    classDef externalNode fill:#2a2a2a,stroke:#666,color:#ccc

    APP[app.py]:::uiNode
    AG[agent/graph.py]:::agentNode
    AN[agent/nodes.py]:::agentNode
    AS[agent/state.py]:::agentNode
    AV[agent/validators.py]:::agentNode
    AC[astro/compute.py]:::astroNode
    LR[llm/report.py]:::llmNode
    OAI[openai SDK]:::externalNode
    KER[kerykeion]:::externalNode
    SWE[pyswisseph]:::externalNode
    GEO[GeoNames API]:::externalNode

    APP --> AG & LR & AC
    AG --> AN & AS
    AN --> AV & AC & LR
    LR --> OAI
    AC --> KER & SWE
    KER --> GEO
```

---

## Session State Lifecycle with Timings

```mermaid
sequenceDiagram
    actor User
    participant Form as Sidebar Form
    participant SS as Session State
    participant PG as prepare_graph
    participant Stream as generate_report_stream
    participant OAI as OpenAI GPT-4o

    User->>Form: fill details + submit
    Form->>SS: clear report_result,\n_prepared_state, _stream_error

    Note over Form,PG: Stage 1 — Chart computation (~15–25s total)
    Form->>PG: invoke(payload)

    Note over PG: ~2–5s GeoNames geocoding
    Note over PG: ~5–10s planets, houses,\naspects, patterns
    Note over PG: ~5–10s transits, progressions,\nsolar arcs, SR, profection
    Note over PG: ~2–3s Vedic, firdaria,\nasteroids, SVGs

    PG->>SS: _prepared_state = computed chart state

    Note over SS: rerun → enters _prepared_state branch

    Note over SS,OAI: Stage 2 — Report streaming (~20–40s)
    SS->>Stream: write_stream(generate_report_stream)
    Stream->>OAI: POST /chat/completions\nmax_tokens=4096, stream=True
    Note over OAI: ~1–2s time to first token
    OAI-->>Stream: token chunks (~20–40s total)
    Stream-->>User: live text render\n(markdown natively)

    alt stream succeeds
        Stream->>SS: report_result = {chart + report_text}
        Stream->>SS: _prepared_state = None
        Note over SS: st.rerun() → enters report_result branch
        SS-->>User: styled dark card\n+ downloads + chat
    else API failure mid-stream
        Stream->>SS: _stream_error = error message\n(_prepared_state unchanged)
        Note over SS: rerun → shows error + Retry button
        User->>SS: click Retry
        SS->>SS: _stream_error = None
        Note over SS: rerun → re-enters stream branch
        Note over Stream,OAI: Stage 2 retried\n(chart data preserved)
    end

    Note over User,OAI: Stage 3 — Follow-up chat (per question, ~5–10s)
    User->>User: ask follow-up question
    User->>OAI: answer_followup_stream\n(chart + report + history + question)
    Note over OAI: report prepended as\nassistant turn for context
    OAI-->>User: streaming answer\nmax_tokens=1024
```
