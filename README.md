# FinPal 🛡️💰

**FinPal** is an intelligent multi-agent financial safety assistant that protects users from scams and helps them understand complex financial documents. Powered by Google Gemini AI and built with FastAPI, it provides real-time analysis of suspicious messages, loan agreements, and financial regulations.

## 🌟 Features

### 🚨 Scam Detection & Prevention
- **Real-time analysis** of UPI messages, SMS, WhatsApp texts
- **Pattern-based detection** for phishing, OTP theft, fake refunds, KYC scams
- **Educational explanations** to help users recognize scam tactics
- **News-powered updates** to stay current with emerging threats

### 📄 Loan & Insurance Document Analysis
- **Intelligent document parsing** (PDF, images, text)
- **Clause extraction** identifies hidden fees, penalties, and complex terms
- **Risk scoring** with 4-level assessment (LOW to VERY_HIGH)
- **Plain-language summaries** in multiple languages
- **Key metrics** extraction: APR, tenure, fees, collateral

### 📚 Financial Policy Q&A
- **RAG-powered answers** to questions about RBI/SEBI regulations
- **Citation-backed responses** with policy references
- **UPI limits, fraud reporting, and regulatory guidance**

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           FastAPI Application                    │
│              /guardian endpoint                  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         Master Router Agent                      │
│    (LLM-based intent classification)            │
└─────┬───────────────┬──────────────┬────────────┘
      │               │              │
      ▼               ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│   Scam   │   │   Loan   │   │  Policy  │
│ Pipeline │   │ Pipeline │   │ Pipeline │
└──────────┘   └──────────┘   └──────────┘
      │               │              │
      ▼               ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐
│ Pattern  │   │ Ingestion│   │  Fetch   │
│ Analyzer │   │ Extractor│   │Summarizer│
│ Educator │   │Risk Score│   │   Q&A    │
└──────────┘   │ Narrator │   └──────────┘
               └──────────┘
```

## 🧰 Tech Stack

- **Framework:** FastAPI + Uvicorn
- **AI Engine:** Google Gemini 2.5-flash
- **Database:** NeonDB (PostgreSQL) with SQLAlchemy 2.0 + asyncpg
- **Development:** Google ADK (Agent Development Kit)
- **Testing:** pytest
- **Language:** Python 3.9+

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- NeonDB account (optional, for persistence)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FinPal
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file
   copy .env.example .env  # Windows
   # OR
   cp .env.example .env    # Linux/Mac
   ```

   Edit `.env` with your credentials:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
   LOG_LEVEL=info
   APP_ENV=development
   ```

5. **Run database migrations** (optional)
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc

## 📖 API Usage

### Main Endpoint: `/guardian`

Send requests to the master agent that automatically routes to the appropriate pipeline.

#### Example 1: Scam Detection

```bash
curl -X POST "http://localhost:8000/guardian" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Urgent! Your UPI payment failed. Click here to get refund: https://suspicious-link.com",
    "language": "en"
  }'
```

#### Example 2: Loan Document Analysis

```bash
curl -X POST "http://localhost:8000/guardian" \
  -H "Content-Type: application/json" \
  -d '{
    "route_hint": "LOAN_DOC",
    "text": "Analyze this loan agreement",
    "language": "en",
    "metadata": {
      "file_id": "loan_doc_123"
    }
  }'
```

#### Example 3: Policy Question

```bash
curl -X POST "http://localhost:8000/guardian" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the daily UPI transaction limit according to RBI?",
    "language": "en"
  }'
```

### Response Format

```json
{
  "final_route": "SCAM_CHECK",
  "data": {
    "risk_level": "HIGH",
    "scam_likelihood": 0.95,
    "analysis": "This message shows classic phishing patterns...",
    "advice": "Do not click the link. Report to your bank."
  },
  "error": null
}
```

## 📁 Project Structure

```
FinPal/
├── app/
│   ├── agents/              # Agent implementations
│   │   ├── master/          # Router agent
│   │   ├── loan/            # Loan analysis pipeline
│   │   ├── policy/          # Policy Q&A pipeline
│   │   └── scam/            # Scam detection pipeline
│   ├── api/                 # FastAPI routes
│   ├── core/                # Core utilities (config, Gemini client)
│   ├── data/                # Sample data and policies
│   ├── db/                  # Database models
│   ├── schemas/             # Pydantic models
│   └── utils/               # Helper utilities (OCR, vector store, etc.)
├── tests/                   # Test suite
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
└── README.md
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_guardian_router.py -v
```

## 🔧 Development

### Adding a New Agent

1. Create agent module in `app/agents/<agent_name>/`
2. Define schemas in `app/schemas/`
3. Implement pipeline in `pipeline.py`
4. Update master router in `app/agents/master/master_agent.py`
5. Add route enum to `app/schemas/common.py`

### Google ADK Integration

Use Google's Agent Development Kit for visual debugging:

```bash
adk web
```

This opens a web interface to inspect agent workflows and debug interactions.

## 🗄️ Database Setup

The application uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

## 🌍 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | - | Google Gemini API key |
| `DATABASE_URL` | No | - | PostgreSQL connection string |
| `LOG_LEVEL` | No | `info` | Logging level (debug/info/warning/error) |
| `APP_ENV` | No | `development` | Environment (development/production) |

## 📊 Agent Pipelines

### Scam Pipeline
1. **Risk Analyzer**: Pattern-based quick scan
2. **Pattern Extractor**: Identifies scam signatures
3. **Educator**: Generates human-friendly explanations

### Loan Pipeline
1. **Ingestion**: Extracts text from documents (PDF/image/text)
2. **Clause Extractor**: Identifies key terms and conditions
3. **Risk Scorer**: Evaluates predatory patterns and hidden costs
4. **Narrator**: Generates plain-language summary

### Policy Pipeline
1. **Fetch**: Loads RBI/SEBI policy documents
2. **Summarizer**: Creates structured FAQ entries
3. **Q&A**: RAG-based question answering with citations

## 🛣️ Roadmap

### Current Status ✅
- [x] Multi-agent architecture
- [x] Gemini AI integration
- [x] FastAPI backend
- [x] Scam detection pipeline
- [x] Loan analysis pipeline
- [x] Policy Q&A pipeline

### Planned Features 🔮
- [ ] **Google Messages Integration**: Real-time SMS monitoring
- [ ] **Call Recording Analysis**: Detect scam calls
- [ ] **Screen Share Agent**: Visual fraud detection
- [ ] **Tavily Integration**: Enhanced web search for policy updates
- [ ] **Multi-model Support**: Fallback to other LLMs
- [ ] **Mobile App**: React Native companion app
- [ ] **Browser Extension**: Real-time website scam detection

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- **Developer A**: Master agent, Loan pipeline, Policy pipeline
- **Developer B**: Scam detection pipeline

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- NeonDB for serverless PostgreSQL
- FastAPI community for excellent documentation

## 📧 Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the `/docs` endpoint for API documentation

---

**Built with ❤️ for financial safety and literacy**
