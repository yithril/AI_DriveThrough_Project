# Work in Progress - Critical Issues & Edge Cases

## 🚨 CRITICAL ISSUES TO FIX

### 1. Restaurant ID Validation (HIGH PRIORITY)
**Issue:** API accepts any `restaurant_id` without validating it exists in the database.

**Current Code:**
```python
restaurant_id: int = Form(...),  # No validation
```

**Problem:** 
- Invalid restaurant IDs cause downstream failures
- Could lead to data corruption or security issues
- Session creation fails silently for non-existent restaurants

**Fix Needed:**
```python
# Add restaurant validation before processing
if not await restaurant_exists(restaurant_id, db):
    raise HTTPException(404, "Restaurant not found")
```

**Impact:** Prevents processing requests for non-existent restaurants.

---

### 2. Session ID Validation (HIGH PRIORITY)
**Issue:** API accepts any `session_id` without validating format or existence.

**Current Code:**
```python
session_id: str = Form(...),  # No validation
```

**Problem:**
- Malformed session IDs cause Redis/PostgreSQL errors
- Non-existent sessions crash the pipeline
- Could lead to session data corruption

**Fix Needed:**
```python
# Add session validation
if not await session_exists(session_id, db):
    raise HTTPException(404, "Session not found")

# Validate session format (UUID pattern)
if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', session_id):
    raise HTTPException(400, "Invalid session ID format")
```

**Impact:** Prevents processing requests for invalid/non-existent sessions.

---

### 3. Language Code Validation (HIGH PRIORITY)
**Issue:** API accepts any language code without validation.

**Current Code:**
```python
language: str = Form("en"),  # No validation
```

**Problem:**
- Invalid language codes cause transcription failures
- Could lead to incorrect language processing
- Wastes API calls on invalid requests

**Fix Needed:**
```python
# Add language validation
valid_languages = ["en", "es", "fr"]
if language not in valid_languages:
    raise HTTPException(400, f"Invalid language code. Must be one of: {valid_languages}")
```

**Impact:** Prevents transcription failures due to invalid language codes.

---

## 🟡 MEDIUM PRIORITY ISSUES

### 4. Audio Duration Validation
**Issue:** No validation for audio duration (could be hours long).

**Problem:**
- Very long audio files cause API timeouts
- Expensive transcription costs
- Poor user experience

**Fix Needed:**
```python
# Add duration validation in _validate_audio_file
if audio_duration > 60:  # Max 60 seconds
    return OrderResult.error("Audio too long (max 60 seconds)")
```

### 5. Rate Limiting
**Issue:** No rate limiting per session.

**Problem:**
- Users could spam the API
- High costs from excessive API calls
- Potential DoS attacks

**Fix Needed:**
```python
# Add rate limiting
if await is_rate_limited(session_id):
    raise HTTPException(429, "Too many requests")
```

---

## 🔍 EDGE CASES TO CONSIDER

### Audio Processing Edge Cases
- **Corrupted audio files** that pass validation but fail transcription
- **Very short audio** (0.1 seconds) that transcribes as empty
- **Audio with no speech** (background noise only)
- **Audio with multiple languages** (language parameter mismatch)
- **Poor audio quality** leading to low confidence transcriptions

### Infrastructure Edge Cases
- **S3 service down** during audio storage
- **OpenAI API down** during transcription
- **Redis down** during session retrieval
- **PostgreSQL down** during fallback operations
- **Network timeouts** during external service calls

### Workflow Edge Cases
- **LangGraph workflow failures** during conversation processing
- **Intent classification failures** for unknown intents
- **Command execution failures** in business logic
- **Voice generation failures** leading to no audio response
- **Workflow timeouts** for complex processing

### Error Handling Edge Cases
- **Canned audio service down** during error responses
- **Canned audio doesn't exist** for specific restaurants
- **Restaurant slug mismatch** in canned audio paths
- **Empty response_text** in successful responses
- **Empty audio_url** in successful responses

---

## 📋 IMPLEMENTATION PLAN

### Phase 1: Critical Validations (Do First)
1. ✅ Add restaurant ID validation
2. ✅ Add session ID validation  
3. ✅ Add language code validation
4. ✅ Add proper error responses for validation failures

### Phase 2: Enhanced Validations
1. Add audio duration validation
2. Add rate limiting per session
3. Add request size validation
4. Add timeout handling

### Phase 3: Edge Case Handling
1. Add retry logic for external services
2. Add circuit breakers for failing services
3. Add fallback responses for all failure modes
4. Add monitoring and alerting

---

## 🧪 TESTING STRATEGY

### Unit Tests Needed
- Restaurant ID validation tests
- Session ID validation tests
- Language code validation tests
- Audio file validation tests
- Error handling tests

### Integration Tests Needed
- End-to-end pipeline tests
- External service failure tests
- Database connection failure tests
- Rate limiting tests

### Load Tests Needed
- High concurrent request handling
- Large audio file processing
- Long-running session handling
- Memory usage under load

---

## 📊 MONITORING & ALERTING

### Metrics to Track
- Request validation failure rates
- External service failure rates
- Pipeline processing times
- Error response rates
- Session creation/retrieval success rates

### Alerts to Set Up
- High validation failure rates
- External service outages
- Pipeline processing timeouts
- Error rate spikes
- Database connection failures

---

## ✅ COMPLETED ITEMS

### Input Validation (COMPLETED)
- ✅ Restaurant ID validation (404 if not found/inactive)
- ✅ Session ID validation (404 if not found)  
- ✅ Language code validation (400 if invalid)
- ✅ Audio file validation (400 for invalid type, 413 for too large)
- ✅ Controller-level validation with proper HTTP status codes

### API Response Enhancement (COMPLETED)
- ✅ Added `order_state_changed` boolean to `ConversationWorkflowState`
- ✅ API response now includes `order_state_changed` field
- ✅ Frontend can now determine when to refresh order state

---

*Last Updated: [Current Date]*
*Status: Work in Progress*
