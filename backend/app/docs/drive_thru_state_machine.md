# Drive-Thru State Machine Design

## 🎯 **Overview**

This document outlines the state machine design for the AI Drive-Thru system. The state machine manages conversation flow and order processing, with clear states, transitions, and guardrails.

## 📊 **States (MVP)**

### **1. Ordering (Default)**
- **Purpose**: Parse customer speech and build order
- **Behavior**: Parse → Apply → Keep building
- **Entry**: Enable parsing + rules, set expectation="free_form_ordering"
- **Exit**: Write diffs to audit log

### **2. Thinking**
- **Purpose**: Customer is browsing menu or not ready to order
- **Behavior**: Answer menu questions, wait for customer
- **Entry**: Set expectation="menu_questions_or_wait", suppress upsell loops
- **Exit**: Customer starts ordering

### **3. Clarifying**
- **Purpose**: Resolve ambiguity with one precise question
- **Behavior**: Ask exactly one targeted question
- **Entry**: Set expectation="single_answer"
- **Exit**: Customer provides clear answer

### **4. Confirming**
- **Purpose**: Summarize order and get confirmation
- **Behavior**: Build summary, get yes/no or edits
- **Entry**: Build summary from current order_state
- **Exit**: Customer confirms or requests changes

### **5. Closing**
- **Purpose**: Finalize order and handoff to POS
- **Behavior**: Freeze order, compute totals, emit ticket
- **Entry**: Freeze order, compute totals, emit ticket
- **Exit**: Order complete or customer adds more

### **6. Idle**
- **Purpose**: Empty lane, session over
- **Behavior**: Cleanup resources
- **Entry**: Clear Redis keys, release lane resources
- **Exit**: New customer arrives

## 🔄 **Global Events & Guards**

### **Events (Apply from any state)**
- **E.BARGE_IN**: User speaks while TTS → cancel TTS, route utterance normally
- **E.SILENCE(timeout)**: No input for N sec → Thinking if order not started, else stay put and issue short nudge
- **E.OOS(item)**: Menu tool says unavailable → jump to Clarifying with replacement question
- **E.SESSION_END**: Car leaves/lane cleared → Idle

### **Guards (Boolean conditions)**
- **G.hasOrder**: `order_state.lineItems.length > 0`
- **G.lowConfidence**: Parser confidence < threshold
- **G.unsafeChange**: High-risk action (e.g., removing many items) → require confirmation

## 🚦 **State Transitions**

### **Ordering State**
```
Utterance parsed ok → Ordering (apply result; update lastMentionedItem)
"give me a minute" / "looking" → Thinking (set thinking_since=now)
Unclear (G.lowConfidence) → Clarifying (emit one targeted question)
"that's it":
  - If G.hasOrder → Confirming
  - Else → Clarifying ("I don't have anything yet—want to start with a drink or a combo?")
```

### **Thinking State**
```
User starts ordering → Ordering
Menu question → stay Thinking (answer, optionally propose 1 upsell; no state advance)
E.SILENCE(30s) from frontend → play "still there?" nudge and remain Thinking
```

### **Clarifying State**
```
User answers clearly → Ordering
User says "never mind":
  - If G.hasOrder → Ordering (resume)
  - Else → Thinking
Still unclear after 1 try → Thinking (don't loop; give simple suggestion)
E.OOS (while clarifying) → remain Clarifying with concrete alternative
```

### **Confirming State**
```
User confirms → Closing
User requests changes → Ordering (apply diffs, keep referent)
"that's not right" → Clarifying (ask smallest disambiguating question)
G.unsafeChange during confirm → stay Confirming after change and re-summarize
```

### **Closing State**
```
Order complete (POS ack/ticket printed) → Idle
"Oh, add X" before finalize → Ordering
Payment problem → Clarifying (one retry, then suggest window)
```

## 📋 **Transition Table**

| STATE | EVENT | GUARD | NEXT | ACTION |
|-------|-------|-------|------|--------|
| Ordering | UTTERANCE_OK | | Ordering | apply(diffs), setReferent() |
| Ordering | UTTERANCE_UNCLEAR | G.lowConfidence | Clarifying | ask(one_targeted_question) |
| Ordering | USER_SAYS_DONE | G.hasOrder | Confirming | summarize() |
| Ordering | USER_SAYS_DONE | !G.hasOrder | Clarifying | ask(start_order_prompt) |
| Ordering | USER_NEEDS_TIME | | Thinking | setThinking() |
| Ordering | E.OOS(item) | | Clarifying | proposeAlternative(item) |
| Thinking | USER_STARTS_ORDER | | Ordering | — |
| Thinking | MENU_QUESTION | | Thinking | answerMenu() |
| Thinking | E.SILENCE(30s) | | Thinking | nudge() |
| Clarifying | USER_CLARIFIES_OK | | Ordering | applyIfActionable() |
| Clarifying | USER_SAYS_NEVER_MIND | G.hasOrder | Ordering | — |
| Clarifying | USER_SAYS_NEVER_MIND | !G.hasOrder | Thinking | — |
| Clarifying | STILL_UNCLEAR | | Thinking | givePatternHint() |
| Clarifying | E.OOS(item) | | Clarifying | proposeAlternative(item) |
| Confirming | USER_CONFIRMS | | Closing | finalizeTicket() |
| Confirming | USER_WANTS_CHANGES | | Ordering | apply(diffs) |
| Confirming | USER_SAYS_NOT_RIGHT | | Clarifying | ask(disambiguation) |
| Confirming | BIG_CHANGE | G.unsafeChange | Confirming | reSummary() |
| Closing | ORDER_COMPLETE | | Idle | cleanup() |
| Closing | ADD_MORE | | Ordering | — |

## 🎯 **Key Design Principles**

### **1. Agents Stay Dumb & Deterministic**
- **State Machine**: Decides transitions based on parser results + guards
- **Response Generator**: Only speaks to current state, no state transitions
- **Agents**: Focus on their specific tasks (parsing, updating, generating responses)

### **2. Risk-Gated Confirmation**
- If user makes big or ambiguous change (G.unsafeChange), force micro-confirm before leaving Confirming
- Prevents accidental order destruction

### **3. Single Question Constraint**
- Clarifying state asks exactly one question per turn
- Keeps conversations snappy and measurable
- Prevents overwhelming customers

### **4. Global Event Handling**
- OOS, barge-in, silence, session end handled cleanly from any state
- Prevents edge cases from breaking the flow

## 🔧 **Implementation Notes**

### **State Persistence**
- **Redis Keys**: `session:{driveThruId}:{lane}:{sessionId}`
- **State Storage**: `conversationState`, `orderState`, `conversationContext`
- **TTL**: Aligned to lane "car leaves" event

### **Frontend Integration**
- **Frontend Controls**: Car detection, initial greeting, timeout management
- **API Focus**: Order processing and conversation flow
- **Communication**: Frontend triggers API with appropriate events

### **Error Handling**
- **Low Confidence**: Jump to Clarifying with targeted question
- **OOS Items**: Propose alternatives immediately
- **Unsafe Changes**: Require confirmation before applying
- **Session End**: Clean up resources and transition to Idle

## 🚀 **Why This Works**

1. **Thinking stays purely "browse & wait"** - don't accidentally build orders while scanning menu
2. **Clarifying constrained to single question** - keeps conversations snappy
3. **Confirming only place you summarize** - reduces repetition during Ordering
4. **Global guards handle messy real-world bits** - OOS, barge-in, silence, session end
5. **Clear separation of concerns** - state machine orchestrates, agents execute

## 📝 **Next Steps**

1. **Implement State Machine Class** with Redis persistence
2. **Create Agent Interfaces** for each state
3. **Build Transition Logic** based on parser results and guards
4. **Add Global Event Handling** for OOS, barge-in, silence
5. **Test State Transitions** with golden test cases
6. **Integrate with Frontend** for car lifecycle management
