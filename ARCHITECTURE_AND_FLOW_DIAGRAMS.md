# Web Verification System - Visual Architecture & Flow Diagrams

## 1. Complete System Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                    CHATBOT WITH VERIFICATION                     ║
║                                                                  ║
║                        USER INTERFACE                            ║
║                    (Web/Mobile/API Client)                       ║
║                                                                  ║
╚════════════════════════════╤═════════════════════════════════════╝
                             │
                             │ Query
                             ▼
╔══════════════════════════════════════════════════════════════════╗
║                      API LAYER (FASTAPI)                         ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           ║
║  │POST /chat/   │  │WS /chat/     │  │GET /chat/    │           ║
║  │    verify    │  │ verify/stream│  │ verify/logs  │           ║
║  └──────────────┘  └──────────────┘  └──────────────┘           ║
║  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           ║
║  │WS /chat/    │  │GET /chat/    │  │WS /chat/     │           ║
║  │verify/hybrid │  │    verify/   │  │   stream     │           ║
║  │              │  │  statistics  │  │ [verify. flag]           ║
║  └──────────────┘  └──────────────┘  └──────────────┘           ║
╚════════════════════════════╤═════════════════════════════════════╝
                             │
                             ▼
╔══════════════════════════════════════════════════════════════════╗
║                 VERIFICATION ORCHESTRATOR                        ║
║                (Main Workflow Coordinator)                       ║
║                                                                  ║
║  1. Classify Query Type (Location/Factual/Temporal/Person)      ║
║  2. Route to appropriate verifier                               ║
║  3. Execute verification                                        ║
║  4. Format output                                               ║
║  5. Log results                                                 ║
╚════════════════════════════╤═════════════════════════════════════╝
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌─────────┐
    │ LOCATION     │ │    FACTUAL   │ │ GENERAL │
    │ VALIDATOR    │ │   VERIFIER   │ │ (SKIP)  │
    └──────────────┘ └──────────────┘ └─────────┘
            │                │
            ▼                ▼
    ┌──────────────┐ ┌──────────────┐
    │  OpenStreetMap   │ │ Google Search │
    │  Nominatim   │   │ + Wikipedia  │
    └──────────────┘ └──────────────┘
            │                │
            ├────────────────┤
            │                │
            ▼                ▼
    Cross-Verification    Cross-Verification
    (Validate Hierarchy)   (2+ sources match)
            │                │
            └────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────┐
    │  STRUCTURED OUTPUT FORMATTER    │
    │                                 │
    │  ✓ Answer                       │
    │  ✓ Sources (with URLs)          │
    │  ✓ Confidence (High/Med/Low)    │
    │  ✓ Verification metadata        │
    │  ✓ JSON + Human readable        │
    └──────────────┬──────────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │  VERIFICATION LOGGER         │
    │                              │
    │  • Log query type            │
    │  • Log sources used          │
    │  • Log confidence score      │
    │  • Log timestamps            │
    │  • Provide analytics         │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────┐
    │  RETURN TO USER              │
    │                              │
    │  Answer + Sources + Confidence
    │  or                          │
    │  "I couldn't verify this"    │
    └──────────────────────────────┘
```

---

## 2. Query Classification Flow

```
                 USER QUERY
                    │
                    ▼
         ┌──────────────────────┐
         │ QueryClassifier      │
         │ (analyzes keywords)  │
         └──────────┬───────────┘
                    │
        ┌───────────┼───────────┬──────────┐
        │           │           │          │
        ▼           ▼           ▼          ▼
    LOCATION    FACTUAL    TEMPORAL    PERSON
    "Where?"     "What?"    "When?"    "Who?"
        │           │           │          │
        │           └───────────┤──────────┘
        │                       │
        │        (merged under FactVerifier)
        │                       │
        ▼                       ▼
   LocationValidator      FactVerifier
        │                       │
        ├─────────────────────┬─┤
        │       GENERAL QUERIES (optional verification)
        │
        ▼
   (Uses OpenStreetMap)
```

---

## 3. LocationValidator Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCATION QUERY                           │
│           e.g., "Where is Ponnur?"                         │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
    ┌──────────────────────┐
    │ Extract Place Name   │
    │  from query          │
    └──────────┬───────────┘
               │ "Ponnur"
               ▼
    ┌──────────────────────────────┐
    │ Query Nominatim API          │
    │ (OpenStreetMap)              │
    └──────────┬────────────────────┘
               │
               ▼
    ┌────────────────────────────────────┐
    │ Parse Results                      │
    │ • Find best match                  │
    │ • Extract place name               │
    │ • Extract district                 │
    │ • Extract state                    │
    │ • Extract country                  │
    │ • Get coordinates                  │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌────────────────────────────────────┐
    │ Validate Hierarchy                 │
    │ • Reverse geocode coordinates      │
    │ • Check consistency                │
    │ • Validate place → district        │
    │     → state → country              │
    └──────────┬───────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
    VALID        INVALID
        │             │
        │             ├─ Ambiguous?
        │             │  → Return suggestions
        │             │
        │             └─ Not found?
        │                → Return error
        │
        ▼
    ┌──────────────────────────────┐
    │ Return LocationHierarchy     │
    │ • Place: Ponnur              │
    │ • District: Guntur           │
    │ • State: Andhra Pradesh      │
    │ • Country: India             │
    │ • Lat/Lon: 16.20, 80.19      │
    └──────────────────────────────┘
```

---

## 4. FactVerifier Flow

```
┌──────────────────────────────────────────────────┐
│          FACTUAL QUERY                           │
│  e.g., "What is the capital of India?"          │
└──────┬───────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Extract Key Terms        │
│ from query               │
└──────┬───────────────────┘
       │ ["capital", "India"]
       ▼
┌──────────────────────────────────┐
│ Search Multiple Sources          │
└───────┬──────────────────────────┘
        │
        ├─ Search 1: Google (DuckDuckGo API)
        │  Results: "New Delhi is capital..."
        │
        └─ Search 2: Wikipedia API
           Results: "New Delhi is capital..."
        
        Both return: "New Delhi"
        │
        ▼
┌─────────────────────────────────────┐
│ Assess Source Credibility           │
│ • Wikipedia = VERY_HIGH (95%)       │
│ • Google = HIGH (85%)               │
└─────────┬───────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│ Cross-Check Results                     │
│ Check: Do both sources agree?           │
│ YES: "New Delhi" appears in both        │
│ Confidence: 90%                         │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────┐
│ Return Verification Result          │
│ • Fact: "New Delhi is capital"      │
│ • Verified: TRUE                    │
│ • Sources: 2 (Wiki + Google)        │
│ • Confidence: 90%                   │
│ • Cross-checked: YES                │
└─────────────────────────────────────┘
```

---

## 5. Confidence Scoring

```
                SOURCES FOUND
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    SOURCE 1    SOURCE 2     SOURCE 3
   Wikipedia     Google       News
        │            │            │
        │ Credibility │            │
        ▼ Scoring    ▼            ▼
       95%         85%           70%
        │            │            │
        └────────────┬────────────┘
                     │
                     ▼
            AVERAGE CREDIBILITY
                   83%
                     │
        ┌────────────┼────────────┐
        │            │            │
        NO           PARTIAL      YES
        │            │            │
        ▼            ▼            ▼
      <50%        50-80%        >80%
        │            │            │
        ▼            ▼            ▼
       LOW        MEDIUM        HIGH
    Confidence  Confidence  Confidence
```

---

## 6. Verification Result Types

```
┌─────────────────────────────────────────────────┐
│        VERIFICATION RESULT TYPES                │
└─────────────────────────────────────────────────┘
        │
    ┌───┴───┬─────────────┬──────────────┐
    │       │             │              │
    ▼       ▼             ▼              ▼
VERIFIED  PARTIAL     UNVERIFIED   CONTRADICTED
(✅)      (⚠️)          (❌)         (⚠️)
│         │            │            │
│ Found   │ Found 1    │ Found 0    │ Found
│ in ≥2   │ source or  │ sources OR │ conflicting
│ sources │ conflicting│ insufficient│ sources
│ matching│ sources    │ confidence │
│         │            │            │
├─────────┴──────────────────────────────┘
│
└─→ Used to:
    1. Determine confidence level
    2. Include/exclude from answer
    3. Request clarification
    4. Log for analytics
```

---

## 7. Data Flow: Complete Example

```
USER INPUT: "Where is Ponnur?"
     │
     ▼
[1] CLASSIFY QUERY
    → Type: LOCATION
     │
     ▼
[2] EXTRACT PLACE NAME
    → "Ponnur"
     │
     ▼
[3] SEARCH SOURCES
    → OSM Nominatim API
    → Result: Multiple matches
    → Select: Guntur district match
     │
     ▼
[4] EXTRACT HIERARCHY
    ┌─────────────────────┐
    │ Place: Ponnur       │
    │ District: Guntur    │
    │ State: A.P.         │
    │ Country: India      │
    │ Lat: 16.20, Lon: 80.19
    └─────────────────────┘
     │
     ▼
[5] VALIDATE
    → Reverse geocode: ✓ Consistent
    → Hierarchy: ✓ Complete
    → Confidence: 95%
     │
     ▼
[6] FORMAT OUTPUT
    ┌──────────────────────────────────┐
    │ Answer:                          │
    │ "Ponnur is in Guntur district,  │
    │  Andhra Pradesh, India"         │
    │                                  │
    │ Verified: TRUE                  │
    │ Confidence: High (95%)          │
    │                                  │
    │ Sources:                        │
    │ 1. OpenStreetMap Nominatim      │
    │    (credibility: VERY_HIGH)     │
    │                                  │
    │ Coordinates:                    │
    │ 16.20° N, 80.19° E            │
    └──────────────────────────────────┘
     │
     ▼
[7] LOG VERIFICATION
    {
      "query": "Where is Ponnur?",
      "type": "location",
      "timestamp": "2026-04-07T12:00:00",
      "sources_count": 1,
      "confidence": 0.95,
      "verified": true,
      "method": "location_hierarchy_validation"
    }
     │
     ▼
[8] RETURN TO USER
    → Display answer + sources + confidence
    → User can click source links
    → Complete transparency achieved ✅
```

---

## 8. Comparison: Before vs After

```
BEFORE: Guessing
┌──────────────────────────────┐
│ Query: "Where is Ponnur?"    │
│                              │
│ LLM Memory → "Ponnur is in   │
│              Vijayawada"     │
│                              │
│ ❌ WRONG (but user doesn't   │
│    know it's wrong)          │
│                              │
│ No sources, no confidence,   │
│ no verification              │
└──────────────────────────────┘

AFTER: Verification
┌──────────────────────────────┐
│ Query: "Where is Ponnur?"    │
│                              │
│ OSM Search → Guntur match    │
│ Validate → Hierarchy check   │
│ Cross-check → ✓ Consistent   │
│                              │
│ ✅ CORRECT WITH SOURCES:     │
│ ✓ OpenStreetMap verified     │
│ ✓ Coordinates validated      │
│ ✓ 95% confidence stated      │
│                              │
│ User sees proof & can verify │
└──────────────────────────────┘
```

---

## 9. Error Handling Flow

```
                    VERIFICATION ATTEMPT
                            │
                ┌───────────┬┴──────────┐
                │           │           │
                ▼           ▼           ▼
            SUCCESS     PARTIAL      FAILURE
              │           │            │
              ▼           ▼            ▼
          Found 2+    Found 1 or      Found 0
          sources     conflicting     sources
              │           │            │
              ▼           ▼            ▼
            Return    Return partial  Retry [1]
           verified    verified with   Try
            answer     caveat         refined
              │           │           search
              │           │            │
              │           │        ┌───┴────┐
              │           │        │         │
              │           │        ▼         ▼
              │           │      Success  Failure
              │           │        │         │
              │           │        ▼         ▼
              │           │      Return   Retry [2]
              │           │      partial  Broader
              │           │              search
              │           │                │
              │           │            ┌───┴─────┐
              │           │            │          │
              │           │            ▼          ▼
              │           │         Success    Failure
              │           │           │          │
              │           │           ▼          ▼
              └───────────┴──────────┬─────────────┐
                                     └─ Return
                                        "I couldn't
                                         verify this"
                                        (HONEST!)
```

---

## 10. Cache Strategy

```
USER QUERY 1
"Where is    → OSM Search  → Cache stored
 Ponnur?"    │ (Wait 3s)   │ {
             │             │  "Ponnur": {...}
             └─────────────┘ }

             ▼ (after 1 second)

USER QUERY 2
"Where is    → Check Cache → FOUND!
 Ponnur?"    │ (Wait 10ms) │ Return from
             │             │ cache
             └─────────────┘

             ▼ (after 1 hour)

CACHE EXPIRED
             → Regular search again
```

---

## 11. System Deployment Architecture

```
┌─────────────────────────────┐
│    FRONTEND (React/Vue)     │
│ ┌───────────────────────────┤
│ │ Chat Interface            │
│ │ + Source Display          │
│ │ + Confidence Badge        │
│ └───────────────────────────┤
└────────────┬────────────────┘
             │
             │ HTTP/WS
             ▼
┌─────────────────────────────┐
│    BACKEND (FastAPI)        │
│ ┌───────────────────────────┤
│ │ API Routes                │
│ │ └─ /chat/verify           │
│ │ └─ /chat/verify/stream    │
│ │ └─ /chat/verify/hybrid    │
│ │ └─ /chat/verify/logs      │
│ │ └─ /chat/verify/statistics│
│ ├───────────────────────────┤
│ │ Verification Layer        │
│ │ ├─ Orchestrator           │
│ │ ├─ FactVerifier           │
│ │ ├─ LocationValidator      │
│ │ ├─ StructuredOutput       │
│ │ └─ Logger                 │
│ └───────────────────────────┤
└─────────┬───────────────────┘
          │
          ├─────────────────┐
          │                 │
          ▼                 ▼
      ┌──────────┐   ┌────────────┐
      │   WEB    │   │ VECTOR DB  │
      │  APIs    │   │ (Optional) │
      │ ┌─────┐  │   │            │
      │ │OSM  │  │   │ Chroma     │
      │ │Wiki │  │   │ Vector     │
      │ │Duck │  │   │ Store      │
      │ │DDGo │  │   │            │
      │ └─────┘  │   └────────────┘
      └──────────┘
```

---

## Summary

This architecture ensures:
- ✅ **No guessing** - Mandatory verification
- ✅ **Multi-source** - 2+ sources required
- ✅ **Transparent** - All sources shown
- ✅ **Confident** - Confidence scores
- ✅ **Logged** - Complete audit trail
- ✅ **Performant** - Caching & optimization
- ✅ **Reliable** - Error handling & graceful degradation
