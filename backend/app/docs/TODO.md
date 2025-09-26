# TODO Items

## Backend Pricing & Order Management

- [ ] **Move order price calculation to backend** - Currently frontend calculates `price × quantity`, but pricing logic should be server-side for security and consistency
  - Backend should calculate: base price + customization costs + tax
  - Return calculated totals (subtotal, tax, total) to frontend
  - Frontend should only display what backend sends
  - Add validation for all pricing calculations
  - Consider size-based pricing if needed

## Input Processing & Normalization

- [x] **Add normalized user input field to workflow state** - Clean up user input at intent classifier stage
  - Keep original user input in state for reference
  - Add `normalized_user_input` field to `ConversationWorkflowState`
  - Use intent classifier to clean up noise (music, background conversations, screaming kids)
  - Improve parsing accuracy by removing irrelevant audio artifacts
  - Update all agents to use normalized input instead of raw input
  - Consider using LLM to extract just the ordering-relevant parts
  - **STOPGAP IMPLEMENTED**: Field added, currently just copies original input

## Advanced Pricing System (Future)

- [ ] **Create Pricing Service with Strategy Pattern** - Handle complex pricing scenarios
  - Tax calculation service (state/country tax rates, VAT)
  - Location-based pricing (different states, countries)
  - Customer type pricing (business vs individual)
  - Promotion engine (discounts, loyalty points, specials)
  - Audit trail for all price calculations
  - Database tables for tax rates, location rules, customer types
  - Strategy pattern for different pricing models

## Dependency Injection Cleanup

- [ ] **Standardize ServiceFactory usage across codebase** - Convert manual ServiceFactory instantiation to proper DI
  - Update `app/api/sessions.py` to use DI instead of manual `ServiceFactory(container)`
  - Update all test files to use DI pattern instead of manual instantiation
  - Review other services that manually create ServiceFactory instances
  - Ensure consistent dependency injection pattern throughout the application
  - Consider if any other services need similar DI improvements
  - Benefits: Better testability, consistency, and maintainability

- [x] **Remove unnecessary FileStorageService wrapper** - Eliminated pointless wrapper class
  - Container now directly injects `S3FileStorageService` instead of wrapper
  - Removed 25 lines of unnecessary code that just passed through to S3FileStorageService
  - Cleaner dependency injection without extra abstraction layers
  - Benefits: Reduced complexity, better maintainability, fewer bugs