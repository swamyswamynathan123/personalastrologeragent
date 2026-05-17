# Architecture

## System Overview

```mermaid
graph TB
    subgraph Browser
        UI[Streamlit UI<br/>app.py]
    end

    subgraph LangGraph["LangGraph Pipeline (agent/)"]
        PG[prepare_graph<br/>validate + compute]
        FG[graph<br/>full pipeline + LLM]
    end

    subgraph Astro["Chart Engine (astro/)"]
        KC[kerykeion<br/>AstrologicalSubject]
        SW[pyswisseph<br/>asteroids]
        GEO[GeoNames API<br/>geocoding]
    end

    subgraph LLM["LLM Layer (llm/)"]
        RP[report.py<br/>prompt builder]
        OAI[OpenAI GPT-4o<br/>streaming]
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

### `prepare_graph` — Used by `app.py` on form submission

```mermaid
flowchart TD
    S([START]) --> A[ingest_inputs\nreset tracking fields]
    A --> B[validate_required_fields\ncheck presence + format]
    B --> C{missing or errors?}
    C -- yes --> D[request_follow_up\nbuild error message]
    C -- no --> E[normalize_and_parse\nparse datetimes + tz]
    E --> F{parse errors?}
    F -- yes --> D
    F -- no --> G[compute_astro\nkerykeion + swisseph]
    D --> Z([END])
    G --> Z
```

### `graph` — Full pipeline (integration tests)

```mermaid
flowchart TD
    S([START]) --> A[ingest_inputs]
    A --> B[validate_required_fields]
    B --> C{missing or errors?}
    C -- yes --> D[request_follow_up]
    C -- no --> E[normalize_and_parse]
    E --> F{parse errors?}
    F -- yes --> D
    F -- no --> G[compute_astro]
    D --> Z([END])
    G --> H[generate_report_node\nGPT-4o blocking call]
    H --> Z
```

---

## Streamlit Rendering State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle : page load

    Idle --> Computing : form submitted
    Computing --> ValidationFailed : follow_up_message set
    Computing --> Prepared : _prepared_state set
    Computing --> UnexpectedError : neither set

    ValidationFailed --> Idle : user corrects inputs

    Prepared --> StreamError : API failure during stream
    StreamError --> Prepared : Retry clicked
    Prepared --> Streaming : st.write_stream() begins
    Streaming --> Rerunning : stream complete\nreport_result set\n_prepared_state cleared
    Rerunning --> StyledReport : st.rerun() fires

    StyledReport --> StyledReport : follow-up chat questions
    StyledReport --> Computing : form resubmitted

    UnexpectedError --> Idle : user retries
```

---

## Natal Chart Computation Pipeline

```mermaid
flowchart TD
    S([compute_chart called]) --> SUBJ[AstrologicalSubject\nkerykeion + GeoNames]
    SUBJ --> P[Planets\nSun–Pluto + Chiron]
    SUBJ --> H[House Cusps\nall 12, with rulers]
    SUBJ --> AN[Angles\nASC + MC]
    SUBJ --> NN[Lunar Nodes\nNorth + South]

    P --> DIG[Essential Dignities\ndomicile / exaltation /\ndetriment / fall]
    P --> BAL[Elemental & Modal\nBalance]
    P --> SECT[Planetary Sect\nday / night chart]
    P --> LP[Lunar Phase\nnatal Moon archetype]

    H --> HR[House Rulers\nnatal condition of each ruler]

    AN --> CR[Chart Ruler\nASC sign → ruling planet]

    P & H & AN --> ASP[Natal Aspects\nconjunction / sextile /\nsquare / trine / opposition]
    ASP --> PAT[Aspect Patterns\nGrand Trine / T-Square /\nYod / Grand Cross / Kite]

    P & AN --> FS[Fixed Stars\n1° orb conjunctions]
    P & AN --> ANA[Anaretic Degrees\n29° planets]
    P --> ANT[Antiscia\nsolstice-point connections]
    P --> MR[Mutual Receptions]
    P --> STELL[Stelliums\n3+ planets same sign/house]

    P --> POF[Part of Fortune\n& Arabic Parts]

    SW[pyswisseph] --> AST[Major Asteroids\nCeres · Pallas · Juno · Vesta]

    subgraph Predictive
        TR[Current Transits\n3° orb]
        UT[Upcoming Transits\nnext 90 days]
        PROG[Secondary Progressions\nprogressed date positions]
        PA[Progressed Aspects\nto natal chart]
        SA[Solar Arc Directions\narc positions + aspects]
        SR[Solar Return\nannual return chart]
        PRO[Annual Profection\nhouse + lord of the year]
        FIR[Firdaria\nmajor + sub time lords]
    end

    P & AN --> TR
    P & AN --> UT
    P --> PROG --> PA
    P & AN --> SA
    P --> SR
    H & P --> PRO
    P --> FIR

    subgraph Vedic
        SID[Sidereal Positions\nLahiri ayanamsa]
        NAK[Moon Nakshatra\n+ pada]
        DASH[Vimshottari Dasha\nmahadasha + antardasha]
        YOGA[Vedic Yogas\nPancha Mahapurusha +\nGajakesari + Raj etc.]
    end

    P --> SID --> NAK
    SID --> DASH
    SID --> YOGA

    subgraph SVG
        CSVG[Natal Chart SVG\nKerykeionChartSVG]
        TSVG[Transit Overlay SVG]
    end

    SUBJ --> CSVG
    SUBJ --> TSVG
```

---

## Synastry Computation Pipeline

```mermaid
flowchart TD
    CA[chart_a\nPerson A natal dict] --> SYN[compute_synastry]
    CB[chart_b\nPerson B natal dict] --> SYN

    SYN --> XA[Inter-chart Aspects\nA planets ↔ B planets\n6° orb]
    SYN --> OVba[House Overlays\nB's planets in A's houses]
    SYN --> OVab[House Overlays\nA's planets in B's houses]
    SYN --> COMP[Composite Chart\nmidpoint positions]
    COMP --> CASP[Composite Aspects]

    XA & OVba & OVab & COMP & CASP --> PROMPT[build_synastry_prompt]
    PROMPT --> GPT[GPT-4o\nstreaming]
    GPT --> REPORT[Synastry Report]
```

---

## LLM Prompt Architecture

```mermaid
flowchart TD
    STATE[AstrologerState\nchart_data dict] --> BP[build_prompt]

    subgraph bp_sections[Prompt Sections]
        PD[Person Details\nname · DOB · location ·\nbirth time · house system]
        PLAC[Natal Placements\nall planets + angles]
        SPEC[Specialised Sections\n20+ formatted blocks]
        RULES[Interpretation Rules\ndigity · sect · timing\npriority hierarchy]
        SYNTH[Synthesis Protocol\nconvergence detection]
        INST[Report Instructions\n7 sections defined]
    end

    BP --> PD & PLAC & SPEC & RULES & SYNTH & INST

    PD & PLAC & SPEC & RULES & SYNTH & INST --> MSG[messages list\nsystem + user]

    MSG --> STREAM[generate_report_stream\nyields chunks]
    MSG --> BLOCK[generate_report\nblocking — tests only]

    STREAM --> WS[st.write_stream\nlive render]
    WS --> STORED[report_result\nsession state]
    STORED --> CARD[styled report-card div\nmarkdown → HTML via\npython-markdown]

    STORED --> FU[answer_followup_stream\nappends report as\nassistant turn]
    FU --> CHAT[st.chat_message\nstreaming reply]
```

---

## Module Dependencies

```mermaid
graph TD
    APP[app.py] --> AG[agent/graph.py]
    APP --> LR[llm/report.py]
    APP --> AC[astro/compute.py]

    AG --> AN[agent/nodes.py]
    AG --> AS[agent/state.py]

    AN --> AV[agent/validators.py]
    AN --> AC
    AN --> LR

    LR --> OAI_SDK[openai SDK]

    AC --> KER[kerykeion]
    AC --> SWE[pyswisseph]
    AC --> PYTZ[pytz]

    KER --> GEO_API[GeoNames API\nonline=True]
    KER --> SWE_FILES[sweph/ ephemeris files\nbundled with kerykeion]
    SWE --> SWE_FILES
```

---

## Session State Lifecycle

```mermaid
sequenceDiagram
    actor User
    participant Form as Sidebar Form
    participant SS as Session State
    participant PG as prepare_graph
    participant Stream as generate_report_stream
    participant OAI as OpenAI GPT-4o

    User->>Form: fill details + submit
    Form->>SS: clear report_result, _prepared_state, _stream_error
    Form->>PG: invoke(payload)
    PG->>SS: _prepared_state = computed chart state

    Note over SS: rerun — enters _prepared_state branch

    SS->>Stream: write_stream(generate_report_stream)
    Stream->>OAI: POST /chat/completions (stream=True)
    OAI-->>Stream: token chunks
    Stream-->>User: live text render

    alt stream succeeds
        Stream->>SS: report_result = {chart + report_text}
        Stream->>SS: _prepared_state = None
        Note over SS: st.rerun() — enters report_result branch
        SS-->>User: styled dark card + downloads + chat
    else stream fails
        Stream->>SS: _stream_error = error message
        Note over SS: st.rerun() — shows Retry button
        User->>SS: click Retry
        SS->>SS: _stream_error = None
        Note over SS: rerun — re-enters stream
    end

    User->>User: ask follow-up question
    User->>OAI: answer_followup_stream(report, history, question)
    OAI-->>User: streaming answer
```
