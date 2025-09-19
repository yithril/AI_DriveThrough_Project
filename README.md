# AI DriveThru 🍔🤖

An AI-powered drive-thru ordering system with management capabilities, real-time inventory tracking, and natural language order processing.

## 🎯 Project Overview

This system allows restaurants to set up their own branded drive-thru experience with AI-powered order processing. Customers can place orders using natural language, and the system validates orders against the menu, inventory, and business rules.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Services   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (OpenAI)      │
│                 │    │                 │    │                 │
│ • Manager UI    │    │ • Menu API      │    │ • Whisper API   │
│ • Kitchen Display│    │ • Order API     │    │ • GPT-4 API     │
│ • Order Interface│    │ • Inventory API │    │ • Order Parsing │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Poetry (Python dependency management)
- OpenAI API key

### Backend Setup
```bash
cd backend
poetry install
poetry shell
export OPENAI_API_KEY="your-openai-api-key"
poetry run uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🎨 Key Features

### 🏪 Restaurant Management
- **Brand Customization** - Upload logos, set colors, customize branding
- **Menu Management** - Add, edit, and organize menu items
- **Inventory Tracking** - Real-time stock levels and alerts
- **Analytics Dashboard** - Sales data and performance metrics

### 🤖 AI Order Processing
- **Voice Recognition** - Convert speech to text using OpenAI Whisper
- **Natural Language Processing** - Parse complex orders with GPT-4
- **Order Validation** - Ensure orders are valid and available
- **Smart Suggestions** - Recommend items based on customer preferences

### 🛡️ Order Guardrails
- **Quantity Limits** - Prevent unreasonable orders (max 10 per item)
- **Menu Validation** - Only allow items that exist on the menu
- **Customization Rules** - Enforce valid modifications only
- **Inventory Checks** - Verify stock availability in real-time
- **Deal Validation** - Ensure package deals are properly applied

### 📱 Real-time Features
- **Kitchen Display** - Live order queue for kitchen staff
- **Order Tracking** - Real-time status updates
- **Inventory Alerts** - Low stock notifications
- **WebSocket Updates** - Instant communication between interfaces

## 🏗️ Technology Stack

### Backend
- **FastAPI** - Modern, fast API framework
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Main database
- **Redis** - Caching and session storage
- **OpenAI API** - AI processing
- **WebSocket** - Real-time updates

### Frontend
- **Next.js 14** - Full-stack React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **React Hook Form** - Form management
- **NextAuth.js** - Authentication
- **Socket.io** - Real-time updates

### AI/ML
- **OpenAI GPT-4** - Natural language processing
- **Whisper API** - Speech-to-text conversion
- **Custom prompt engineering** - Order parsing and validation

## 📊 Database Schema

### Core Entities
- **Restaurants** - Brand configuration and settings
- **Menu Items** - Food items with pricing and categories
- **Inventory** - Stock tracking and availability
- **Orders** - Customer orders with validation
- **Users** - Staff management and permissions
- **Deals** - Package deals and promotions

## 🎯 Development Roadmap

### Week 1: Core System
- [ ] Backend API setup
- [ ] Database schema design
- [ ] Menu management system
- [ ] Inventory tracking
- [ ] Basic order validation

### Week 2: AI Integration
- [ ] OpenAI API integration
- [ ] Voice processing
- [ ] Order parsing logic
- [ ] Real-time features
- [ ] Demo preparation

## 🛠️ Development Commands

### Backend
```bash
# Install dependencies
poetry install

# Run development server
poetry run uvicorn main:app --reload

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run flake8
```

### Frontend
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
```

## 🚀 Deployment

### Backend (AWS Lambda)
```bash
# Install serverless framework
npm install -g serverless

# Deploy to AWS
serverless deploy
```

### Frontend (Vercel)
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy to Vercel
vercel deploy
```

## 🔧 Environment Variables

### Backend
```
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret
```

### Frontend
```
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📱 User Interfaces

### Manager Dashboard
- Restaurant setup and branding
- Menu item management
- Inventory tracking
- Sales analytics
- Staff management

### Kitchen Display
- Real-time order queue
- Order status updates
- Prep time tracking
- Inventory alerts

### Drive-Thru Interface
- Voice ordering system
- Order confirmation
- Payment processing
- Real-time updates

## 🤖 AI Processing Examples

### Voice Input
```
Customer: "I want a large burger with no pickles and extra cheese, and a medium fries"
```

### AI Processing
```json
{
  "items": [
    {
      "name": "Large Burger",
      "quantity": 1,
      "modifications": ["no pickles", "extra cheese"]
    },
    {
      "name": "Medium Fries",
      "quantity": 1
    }
  ],
  "total": 12.99,
  "status": "validated"
}
```

## 🔒 Security Features

- JWT token-based authentication
- Role-based access control
- API rate limiting
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 📈 Monitoring & Analytics

- Request/response logging
- Error tracking
- Performance metrics
- Sales analytics
- Inventory reports
- Order success rates

## 🚀 Getting Started

1. **Clone the repository**
2. **Set up environment variables**
3. **Install dependencies** (Backend: Poetry, Frontend: npm)
4. **Run database migrations**
5. **Start development servers**
6. **Access the application** at `http://localhost:3000`

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions or issues, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for the future of drive-thru ordering**
