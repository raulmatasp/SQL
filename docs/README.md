# HugData Analytics Platform

A comprehensive AI-powered analytics platform built with Laravel, FastAPI, React, and Dagster. Transform natural language queries into SQL, generate insights, and create interactive dashboards with collaborative features.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React SPA     │    │   Laravel API    │    │  FastAPI AI     │
│   (Frontend)    │◄──►│   (Backend)      │◄──►│   (ML/AI)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
        ┌─────────────────┐     │     ┌─────────────────┐
        │   PostgreSQL    │◄────┴────►│     Redis       │
        │   (Database)    │           │   (Cache)       │
        └─────────────────┘           └─────────────────┘
                 │
        ┌─────────────────┐           ┌─────────────────┐
        │    Weaviate     │           │    Dagster      │
        │  (Vector DB)    │           │  (Orchestration)│
        └─────────────────┘           └─────────────────┘
```

## 🚀 Features

### Core Capabilities
- **Natural Language to SQL**: Transform plain English queries into optimized SQL
- **AI-Powered Insights**: Automatic analysis and recommendations
- **Interactive Dashboards**: Drag-and-drop dashboard builder
- **Real-time Collaboration**: Multi-user query editing and sharing
- **Advanced Visualizations**: Charts, tables, and custom widgets

### AI & ML Features
- **Multi-LLM Support**: OpenAI, Anthropic, Cohere with intelligent fallback
- **Vector Search**: Semantic search for similar queries and insights
- **Query Optimization**: Automatic SQL optimization and validation
- **Contextual Recommendations**: Smart suggestions based on data patterns

### Collaboration & Workflow
- **Real-time Editing**: WebSocket-based collaborative query editing
- **Query Sharing**: Secure sharing with granular permissions
- **Version Control**: Query history and change tracking
- **Team Workspaces**: Organized spaces for different teams

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended)
- **PHP 8.3+** with extensions: mbstring, dom, fileinfo, pgsql, redis
- **Node.js 18+** and npm
- **Python 3.13+**
- **PostgreSQL 16+**
- **Redis 7+**

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/hugdata-platform.git
cd hugdata-platform
```

### 2. Environment Setup
```bash
# Copy environment files
cp hugdata-app/.env.example hugdata-app/.env
cp hugdata-ai/.env.example hugdata-ai/.env

# Configure your API keys and database credentials
# Edit .env files with your specific settings
```

### 3. Docker Deployment (Recommended)
```bash
# Start all services
docker-compose up -d

# Initialize the database
docker-compose exec laravel php artisan migrate --seed

# Access the application
open http://localhost:3000
```

### 4. Manual Setup (Development)

#### Laravel Backend
```bash
cd hugdata-app
composer install
php artisan key:generate
php artisan migrate --seed
php artisan serve --port=8000
```

#### FastAPI AI Service
```bash
cd hugdata-ai
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

#### React Frontend
```bash
cd hugdata-frontend
npm install
npm start
```

#### Dagster Orchestration
```bash
cd hugdata-ai
export DAGSTER_HOME=$PWD/dagster_home
dagster dev --port 3001
```

## 📚 Documentation

### User Guides
- [Getting Started](docs/user-guide/getting-started.md)
- [Writing Natural Language Queries](docs/user-guide/natural-language-queries.md)
- [Creating Dashboards](docs/user-guide/creating-dashboards.md)
- [Collaboration Features](docs/user-guide/collaboration.md)

### Developer Documentation
- [API Reference](docs/api/README.md)
- [Frontend Architecture](docs/development/frontend-architecture.md)
- [Backend Architecture](docs/development/backend-architecture.md)
- [AI Service Integration](docs/development/ai-service.md)
- [Database Schema](docs/development/database-schema.md)

### Deployment & Operations
- [Production Deployment](docs/deployment/production.md)
- [Docker Configuration](docs/deployment/docker.md)
- [Monitoring & Logging](docs/deployment/monitoring.md)
- [Security Best Practices](docs/deployment/security.md)

## 🔧 Configuration

### Environment Variables

#### Laravel (.env)
```env
APP_NAME="HugData Analytics Platform"
APP_ENV=production
APP_URL=https://hugdata.example.com

DB_CONNECTION=pgsql
DB_HOST=postgres
DB_DATABASE=hugdata
DB_USERNAME=hugdata
DB_PASSWORD=your_secure_password

AI_SERVICE_URL=http://fastapi:8003
REDIS_HOST=redis
```

#### FastAPI (.env)
```env
ENVIRONMENT=production
DATABASE_URL=postgresql://hugdata:password@postgres:5432/hugdata
REDIS_URL=redis://redis:6379/0
WEAVIATE_URL=http://weaviate:8080

OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
COHERE_API_KEY=your_cohere_key
```

### AI Model Configuration
The platform supports multiple AI providers with intelligent fallback:

1. **OpenAI GPT-4** (Primary)
2. **Anthropic Claude** (Fallback)
3. **Cohere Command** (Secondary Fallback)

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
cd hugdata-app && php artisan test

# AI service tests  
cd hugdata-ai && python -m pytest tests/

# Frontend tests
cd hugdata-frontend && npm test

# Integration tests
python -m pytest tests/test_integration.py
```

### Test Coverage
- **Laravel**: >80% coverage required
- **Python**: >75% coverage required
- **React**: >70% coverage required

## 📊 Monitoring

### Health Checks
- Laravel: `GET /api/health`
- FastAPI: `GET /health`
- Dagster: `GET /`

### Metrics & Monitoring
- **Prometheus**: Metrics collection on `:9090`
- **Grafana**: Dashboard visualization on `:3001`
- **Application logs**: Structured JSON logging
- **Performance monitoring**: Response time tracking

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards
- **PHP**: PSR-12 with Laravel Pint
- **TypeScript**: ESLint + Prettier configuration
- **Python**: Black + Flake8 formatting
- **Commit messages**: Conventional Commits format

## 📈 Performance

### Benchmarks
- **Query Response Time**: <2s for complex queries
- **Dashboard Load Time**: <3s for 10+ widgets
- **Concurrent Users**: 100+ simultaneous users
- **Database Performance**: Optimized for 1M+ records

### Optimization Features
- **Query Caching**: Redis-based intelligent caching
- **Database Optimization**: Automatic index suggestions
- **CDN Integration**: Static asset optimization
- **Lazy Loading**: Progressive data loading

## 🔐 Security

### Authentication & Authorization
- **JWT Tokens**: Secure API authentication
- **Role-based Access**: Granular permission system
- **OAuth Integration**: Google, GitHub, Microsoft support
- **2FA Support**: Time-based one-time passwords

### Data Security
- **Encryption**: AES-256 encryption at rest
- **HTTPS Only**: TLS 1.3 enforcement
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Content Security Policy

## 🛠️ Troubleshooting

### Common Issues

#### Service Connection Issues
```bash
# Check service health
curl http://localhost:8003/health  # FastAPI
curl http://localhost:8000/api/health  # Laravel

# View logs
docker-compose logs fastapi
docker-compose logs laravel
```

#### Database Connection Issues
```bash
# Test database connection
docker-compose exec postgres psql -U hugdata -d hugdata

# Check migrations
docker-compose exec laravel php artisan migrate:status
```

#### AI Service Issues
```bash
# Verify API keys
docker-compose exec fastapi python -c "import os; print('OpenAI:', bool(os.getenv('OPENAI_API_KEY')))"

# Test AI endpoints
curl -X POST http://localhost:8003/query \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT 1"}'
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Laravel** - PHP web framework
- **FastAPI** - Modern Python web framework
- **React** - Frontend library
- **Dagster** - Data orchestration platform
- **OpenAI** - AI/ML services
- **Weaviate** - Vector database
- **PostgreSQL** - Primary database
- **Redis** - Caching and queues

## 📞 Support

- **Documentation**: [https://docs.hugdata.example.com](https://docs.hugdata.example.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/hugdata-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/hugdata-platform/discussions)
- **Email**: support@hugdata.example.com

---

**Built with ❤️ by the HugData Team**