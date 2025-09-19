# AI DriveThru - Backend

AI-powered drive-thru ordering system with management capabilities and real-time inventory tracking.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry (dependency management)
- OpenAI API key

### Installation

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export DATABASE_URL="postgresql://user:password@localhost/ai_drivethru"

# Run the development server
poetry run uvicorn main:app --reload
```

## 🏗️ Architecture

### Core Components
- **FastAPI** - Modern, fast API framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Main database
- **OpenAI API** - AI order processing
- **WebSocket** - Real-time updates

### Database Schema
- **Restaurants** - Brand customization (logo, colors, name)
- **Menu Items** - Food items with pricing and categories
- **Inventory** - Stock tracking and availability
- **Orders** - Customer orders with validation
- **Users** - Manager/cashier/kitchen staff

## 🎯 Key Features

### Management System
- Restaurant setup and branding
- Menu item management (CRUD)
- Inventory tracking and alerts
- Order monitoring and analytics

### AI Order Processing
- Voice-to-text conversion
- Natural language order parsing
- Order validation and guardrails
- Real-time inventory checks

### Order Validation
- Menu item verification
- Customization rule enforcement
- Quantity limits (max 10 per item)
- Deal and package validation
- Inventory availability checks

## 🛠️ API Endpoints

### Restaurant Management
```
GET    /restaurants/{id}           # Get restaurant details
PUT    /restaurants/{id}           # Update restaurant settings
POST   /restaurants                # Create new restaurant
```

### Menu Management
```
GET    /restaurants/{id}/menu      # Get menu items
POST   /restaurants/{id}/menu      # Add menu item
PUT    /menu/{item_id}             # Update menu item
DELETE /menu/{item_id}              # Delete menu item
```

### Order Processing
```
POST   /orders                     # Create new order
GET    /orders/{id}                # Get order details
PUT    /orders/{id}/status         # Update order status
POST   /orders/validate            # Validate order
```

### AI Processing
```
POST   /ai/transcribe             # Voice-to-text conversion
POST   /ai/parse-order            # Parse natural language order
POST   /ai/validate-order         # AI-powered order validation
```

## 🔧 Development

### Running Tests
```bash
poetry run pytest
```

### Code Formatting
```bash
poetry run black .
poetry run flake8
```

### Database Migrations
```bash
# Generate migration
poetry run alembic revision --autogenerate -m "description"

# Apply migration
poetry run alembic upgrade head
```

## 🚀 Deployment

### Local Development
```bash
poetry run uvicorn main:app --reload
```

### Production (AWS Lambda)
```bash
# Install serverless framework
npm install -g serverless

# Deploy
serverless deploy
```

### Environment Variables
```
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret
```

## 📊 Order Validation Rules

### Quantity Limits
- Maximum 10 of any single item
- Maximum $200 total order value
- Reasonable quantity validation

### Customization Rules
- Only allow valid modifications
- Enforce required customizations
- Validate size preferences

### Inventory Checks
- Verify stock availability
- Check minimum stock levels
- Update inventory after orders

### Deal Validation
- Ensure deal requirements are met
- Apply discounts correctly
- Validate deal expiration

## 🤖 AI Processing Pipeline

### Voice-to-Order Flow
1. **Speech Recognition** (Whisper API)
2. **Intent Classification** (GPT-4)
3. **Menu Item Extraction** (Custom prompts)
4. **Order Validation** (Database lookup)
5. **Confirmation Generation** (GPT-4)

### Example AI Prompts
```
System: "You are an AI assistant for a fast-food drive-thru. Parse customer orders and extract:
- Menu items with quantities
- Modifications (no pickles, extra cheese)
- Special instructions
- Size preferences

Return structured JSON with validated menu items."
```

## 🔒 Security

### Authentication
- JWT token-based authentication
- Role-based access control
- API rate limiting

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 📈 Monitoring

### Logging
- Request/response logging
- Error tracking
- Performance metrics

### Health Checks
- Database connectivity
- External API status
- System resource usage

## 🚀 Getting Started

1. **Clone the repository**
2. **Install dependencies** with Poetry
3. **Set up environment variables**
4. **Run database migrations**
5. **Start the development server**

## 📝 License

MIT License - see LICENSE file for details
