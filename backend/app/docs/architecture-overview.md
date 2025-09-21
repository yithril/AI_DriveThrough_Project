# AI DriveThru - Architecture Overview (MVP)

## 🎯 **System Overview**

The AI DriveThru system uses a **multi-agent LangGraph workflow** to handle natural language drive-thru orders. The system combines **deterministic state management** with **flexible LLM agents** to create a robust, conversational ordering experience.

## 🏗️ **High-Level Architecture**

```
User Speech → LangGraph Workflow → Voice Response
     ↓              ↓                    ↓
  Frontend    Backend API          Audio File
```

### **Core Components**
- **LangGraph Workflow**: Orchestrates conversation flow with specialized agents
- **State Machine**: Manages conversation states and valid transitions
- **Command System**: Executes order operations with validation and error handling
- **Voice Service**: Generates natural speech responses
- **Session Management**: Redis-backed conversation persistence

## 🔄 **LangGraph Workflow Nodes**

### **1. Intent Classifier (Router Agent)**
- **Purpose**: First line of defense - validates user intent against state machine
- **Input**: User speech text + current conversation state
- **Output**: Intent classification + confidence score
- **Behavior**: 
  - Valid transitions → Continue to next node
  - Invalid/off-topic → Return canned response
  - Low confidence → Route to clarification

### **2. Transition Decision**
- **Purpose**: Determines if commands are needed for the state transition
- **Input**: Intent + current state + target state
- **Output**: Action type (`commands_needed` | `canned_response` | `clarification_needed`)
- **Behavior**: Routes based on state machine rules

### **3. Command Agent**
- **Purpose**: Decomposes user intent into executable commands
- **Input**: Intent + slots + conversation context
- **Output**: List of commands (AddItem, RemoveItem, etc.)
- **Behavior**: Creates commands for order modifications

### **4. Command Executor**
- **Purpose**: Executes commands and validates results
- **Input**: List of commands + session context
- **Output**: `CommandBatchResult` with success/failure status
- **Behavior**: Runs all commands, aggregates results, determines follow-up action

### **5. Follow-up Agent (Conditional)**
- **Purpose**: Generates natural language responses for complex situations
- **Input**: Command results + conversation context + state machine context
- **Output**: Natural language response text
- **Behavior**: 
  - Success cases → Simple confirmation
  - Error cases → Helpful clarification or alternatives
  - Upsell opportunities → Contextual suggestions

### **6. Voice Generator**
- **Purpose**: Converts text response to audio
- **Input**: Response text + voice settings
- **Output**: Audio file URL
- **Behavior**: Uses existing TTS service, implements caching for identical responses

## 🎭 **State Machine Integration**

### **States**
- **ORDERING**: Building order, accepting modifications
- **THINKING**: Customer browsing, answering questions
- **CLARIFYING**: Resolving ambiguity with targeted questions
- **CONFIRMING**: Order summary and confirmation
- **CLOSING**: Finalizing order and handoff
- **IDLE**: Empty lane, session cleanup

### **State Machine Role**
- **Structure**: Provides conversation flow rules and valid transitions
- **Context**: Passes current state, target state, and recent actions to agents
- **Guardrails**: Prevents invalid state transitions and off-topic responses
- **Deterministic**: Ensures consistent behavior regardless of LLM variability

## 🔧 **Command System**

### **Command Pattern**
- **BaseCommand**: Abstract interface for all order operations
- **CommandInvoker**: Executes commands with validation and error handling
- **CommandFactory**: Creates command instances from intent data
- **CommandContext**: Provides scoped services (OrderService, ValidationService, etc.)

### **Result Handling**
- **OrderResult**: Individual command execution results with error categorization
- **CommandBatchResult**: Aggregated results from multiple commands
- **Error Codes**: Granular error types (ITEM_UNAVAILABLE, MODIFIER_CONFLICT, etc.)
- **Follow-up Actions**: Recommendations for AI response (CONTINUE, ASK, STOP)

## 📊 **Data Flow**

### **Input Processing**
1. **User Speech** → Whisper (Speech-to-Text)
2. **Text** → Intent Classifier (LangGraph Node 1)
3. **Intent** → State Machine Validation
4. **Valid Intent** → Transition Decision (LangGraph Node 2)

### **Command Execution**
5. **Commands Needed** → Command Agent (LangGraph Node 3)
6. **Command List** → Command Executor (LangGraph Node 4)
7. **Results** → Follow-up Agent (LangGraph Node 5, conditional)
8. **Response Text** → Voice Generator (LangGraph Node 6)

### **Output Delivery**
9. **Audio File** → Frontend via API response
10. **Order Updates** → Frontend via session polling

## 🚀 **Key Design Principles**

### **1. Separation of Concerns**
- **State Machine**: Orchestrates conversation flow
- **LLM Agents**: Generate content and handle complexity
- **Command System**: Executes business logic deterministically
- **Voice Service**: Handles audio generation and caching

### **2. Fault Tolerance**
- **Command Isolation**: Individual command failures don't stop batch execution
- **Error Categorization**: Different error types get appropriate responses
- **Fallback Responses**: Canned responses for system failures
- **State Recovery**: Graceful handling of invalid transitions

### **3. Performance Optimization**
- **Response Caching**: Identical `CommandBatchResult` objects reuse voice files
- **Session Management**: Redis-backed conversation persistence
- **Parallel Processing**: Commands execute independently
- **Minimal LLM Calls**: Deterministic logic where possible

### **4. Maintainability**
- **Clear Interfaces**: Well-defined contracts between components
- **Comprehensive Testing**: Unit tests for all critical paths
- **Error Tracking**: Detailed error codes and categorization
- **Modular Design**: Easy to add new commands or modify behavior

## 🎯 **MVP Scope**

### **Core Features**
- ✅ Natural language order processing
- ✅ Multi-item orders with customizations
- ✅ Error handling and clarification
- ✅ Voice response generation
- ✅ Session management and persistence

### **Future Enhancements**
- 🔄 Advanced upsell logic
- 🔄 Multi-language support
- 🔄 Payment integration
- 🔄 Analytics and optimization
- 🔄 A/B testing for responses

## 📝 **Implementation Status**

### **Completed**
- ✅ Command system with validation and error handling
- ✅ OrderResult and CommandBatchResult DTOs
- ✅ Comprehensive unit test coverage
- ✅ State machine design and implementation
- ✅ Voice service integration

### **In Progress**
- 🔄 LangGraph workflow implementation
- 🔄 Intent classification and routing
- 🔄 Follow-up agent development
- 🔄 Frontend integration

### **Next Steps**
- 📋 Implement LangGraph nodes
- 📋 Create agent interfaces
- 📋 Build transition logic
- 📋 Add response caching
- 📋 Integrate with frontend

---

**This architecture provides a solid foundation for an MVP while maintaining flexibility for future enhancements. The combination of deterministic state management and flexible LLM agents creates a robust, maintainable system.**
