# TODO Items

## Backend Pricing & Order Management

- [ ] **Move order price calculation to backend** - Currently frontend calculates `price × quantity`, but pricing logic should be server-side for security and consistency
  - Backend should calculate: base price + customization costs + tax
  - Return calculated totals (subtotal, tax, total) to frontend
  - Frontend should only display what backend sends
  - Add validation for all pricing calculations
  - Consider size-based pricing if needed

## Advanced Pricing System (Future)

- [ ] **Create Pricing Service with Strategy Pattern** - Handle complex pricing scenarios
  - Tax calculation service (state/country tax rates, VAT)
  - Location-based pricing (different states, countries)
  - Customer type pricing (business vs individual)
  - Promotion engine (discounts, loyalty points, specials)
  - Audit trail for all price calculations
  - Database tables for tax rates, location rules, customer types
  - Strategy pattern for different pricing models
