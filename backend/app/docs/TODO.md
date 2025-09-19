# TODO - AI DriveThru Backend

## 🎯 **High Priority**

### **Conversation State Machine**
- **Problem**: Need explicit conversation flow control
- **Solution**: Implement state machine for drive-thru conversation flow
- **States**: `Greeting → MenuHelp → Ordering → Clarifying → Confirming → Payment → Closing → Idle`
- **Transitions**: Based on agent outputs, timeouts, frontend lifecycle events
- **Benefits**: Prevents ambiguous "what happens next" scenarios
- **Implementation**: State machine owns turn-level decisions, agents focus on their tasks

### **Intent Router (Enhanced Relevancy Agent)**
- **Problem**: Need to route different types of customer interactions
- **Solution**: Classify customer intent and route appropriately
- **Categories**: `{ordering, small talk, complaint, menu question, not relevant}`
- **Routing Logic**:
  - Menu questions → Answer directly from menu/FAQ tool
  - Ordering → Proceed to order flow
  - Low confidence → Use canned phrases
- **Performance**: Small model first, larger model only if uncertain

### **Semantic Parser + Rules (Enhanced Order Deconstruction)**
- **Problem**: Need reliable order parsing with LLM + deterministic validation
- **Solution**: Hybrid approach - LLM proposes, rules verify
- **Components**:
  - **Domain DSL**: `ADD itemId=burger_classic size=large mods=[no_onion]`
  - **Menu Grammar**: Deterministic validation against menu schema
  - **Coreference Handling**: "that" refers to `lastMentionedItemRef`
- **Action Schema**:
  ```json
  {
    "type": "ADD|REMOVE|CHANGE|SET_COMBO|SET_QTY",
    "target": { "ref": "last|itemIdx:2|byId:menuItemId" },
    "payload": { "menuItemId": "...", "quantity": 1, "size": "large", "modifiers": [...] },
    "confidence": 0.88
  }
  ```

### **Transactional Order Updater (Enhanced Order Agent)**
- **Problem**: Need reliable, idempotent order state management
- **Solution**: Treat each action as a transaction with diffs
- **Features**:
  - **Idempotency**: Action UUIDs prevent double-processing
  - **Smart Updates**: "upgrade drink to large" finds correct sub-item
  - **Result Diffs**: Track what actually changed
- **Order State Schema**:
  ```json
  {
    "lineItems": [{"id": "li_123", "menuItemId": "...", "quantity": 1, "size": "medium", "modifiers": [...]}],
    "lastMentionedItemRef": "li_123",
    "totals": {"subtotal": 7.49, "tax": 0.45, "total": 7.94}
  }
  ```

### **NLG with Style (Enhanced Response Generator)**
- **Problem**: Need consistent, policy-aware response generation
- **Solution**: Generate natural language with house style and policy awareness
- **Features**:
  - **Error Handling**: "We're out of apple pies; would a cookie be okay?"
  - **One Thing at a Time**: In clarifying state, ask one question
  - **House Style**: Concise, friendly, no filler
  - **No State Transitions**: Only generates text, state machine handles transitions

### **Transcription Correction Service**
- **Problem**: Whisper sometimes mishears words (e.g., "lunar" → "looter")
- **Solution**: Implement Levenshtein distance algorithm for word correction
- **Requirements**:
  - Load restaurant menu items for correction candidates
  - Calculate edit distance between transcribed words and menu items
  - Replace words with closest menu match (within threshold)
  - Handle multi-word corrections (e.g., "Big Mac" vs "big mac")
- **Algorithm Considerations**:
  - Fast word-by-word processing
  - Context-aware corrections (consider surrounding words)
  - Confidence scoring for corrections
  - Fallback to original if no good match found
- **Performance**: Need efficient algorithm for real-time correction
- **Dependencies**: Menu items from restaurant database

### **Audio Quality Improvements**
- **Noise Reduction**: Implement background noise filtering
- **Audio Normalization**: Standardize audio levels
- **Format Optimization**: Ensure optimal audio format for Whisper
- **Multiple Attempts**: Try different Whisper parameters for better accuracy

## 🔧 **Medium Priority**

### **Memory and Persistence**
- **Redis Keys**: `session:{driveThruId}:{lane}:{sessionId}`
- **State Storage**: `order_state`, `referent_stack`, `turn_counter`, `last_action_uuid`
- **TTL**: Aligned to lane "car leaves" event; soft timeout if no speech for N seconds
- **Logging**: Raw user text + parsed DSL + applied diffs for audit and offline improvement

### **Menu/Policy Intelligence**
- **MenuTool**: Query items, sizes, allowed modifiers, availability, prices, combos
- **PolicyTool**: Allergy flags, legal phrasing for age-restricted items, store hours, payment rules
- **Benefits**: Let Deconstructor validate and Response Generator stay honest

### **Confirmation Strategy**
- **Minimize read-backs** but gate risky operations
- **High ticket or ambiguous**: "Just to confirm: a large #2 with Coke, no onion. Anything else?"
- **Before Closing**: Short summary + total price, then "Is your order correct?"

## �� **Future Enhancements**

### **Testing and Evaluation**
- **Golden Sets**: 100–200 utterances covering combos, customizations, corrections, OOS, accents, noise
- **Metrics**:
  - Parse accuracy (action list correctness)
  - Edit distance between intended and final order
  - Clarification rate
  - Turn count to completion
  - Latency p95
- **Chaos Cases**: "Actually cancel that," "swap Coke for Sprite," "make the last two medium," "add two of those," "wait, not the drink, the fries."

### **Failure Modes and Safe Fallbacks**
- **Low confidence parse** → Clarifying state with 1 short question
- **Repeated low confidence** → Offer human handoff or board prompt: "Please pull forward for assistance."
- **Tool failure** (menu store down) → Static cached menu, then graceful apology if price mismatches

### **Latency and Turn Robustness**
- **Barge-in handling**: Frontend should allow user to interrupt TTS; on barge-in, cancel speech and route utterance through the same turn pipeline
- **Partial hypotheses**: Optionally feed partial ASR if you need ultra-low latency, but commit actions only on final ASR
- **Fast path**: Intent Router (small model), Parser (medium model with constrained prompt), Everything else deterministic

## 📝 **Notes**

- **Current Status**: Basic speech-to-text working with Whisper
- **Test Results**: Successfully transcribing audio files
- **Accuracy Issues**: Some words misheard (e.g., "lunar" → "looter")
- **Architecture**: 4-agent split with explicit state machine orchestration
- **Key Insight**: LLM for parsing + deterministic rules for validation = reliable system
- **Next Steps**: Implement conversation state machine and enhanced agents