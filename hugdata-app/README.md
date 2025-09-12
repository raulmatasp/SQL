# HugData - AI-Powered Database Analytics Platform

HugData is a comprehensive analytics platform that enables natural language queries to databases, generating SQL, visualizations, and AI-powered insights. It's a Laravel + React adaptation of the WrenAI GenBI Agent.

## Architecture

- **Backend**: Laravel 11+ (PHP 8.2+) - API, business logic, authentication
- **Frontend**: React with TypeScript - User interface and data visualization
- **AI Service**: Python FastAPI - Natural language to SQL generation
- **Database**: Multi-database support (PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, SQL Server)

## Features

✅ **Multi-Database Connection Management**
- Support for PostgreSQL, MySQL, SQLite, BigQuery, Snowflake, SQL Server
- Connection testing and health monitoring
- Schema introspection across different database types

✅ **Natural Language SQL Generation**
- AI-powered conversion of natural language queries to SQL
- Confidence scoring and query explanation
- Fallback mechanisms when AI service is unavailable

✅ **Data Source Management**
- CRUD operations for data sources
- Connection configuration and testing
- Project-based organization

✅ **Query Interface**
- Natural language query input with suggestions
- Direct SQL editor mode
- Query execution with results display
- Query history and caching

✅ **Chart Generation & Visualization**
- AI-powered chart type suggestions
- Interactive charts with Chart.js
- Support for bar, line, pie, and doughnut charts
- Intelligent data analysis for optimal chart selection

✅ **API Documentation**
- Comprehensive OpenAPI/Swagger documentation
- Available at `/docs` endpoint
- Complete API reference with examples

## Getting Started

### Prerequisites

- PHP 8.2+
- Node.js 18+
- Python 3.8+
- Composer
- NPM/Yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hugdata-app
   ```

2. **Install Laravel dependencies**
   ```bash
   composer install
   cp .env.example .env
   php artisan key:generate
   ```

3. **Set up the database**
   ```bash
   php artisan migrate
   ```

4. **Install Python dependencies**
   ```bash
   cd ../hugdata-ai
   pip install -r requirements.txt
   ```

5. **Install frontend dependencies**
   ```bash
   cd ../hugdata-frontend
   npm install
   ```

### Running the Application

1. **Start the Laravel backend**
   ```bash
   cd hugdata-app
   php artisan serve --port=8000
   ```

2. **Start the AI service**
   ```bash
   cd hugdata-ai
   python -m uvicorn main:app --port=8003 --reload
   ```

3. **Start the React frontend**
   ```bash
   cd hugdata-frontend
   npm run dev
   ```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- AI Service: http://localhost:8003
- API Documentation: http://localhost:8000/docs

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout

### Projects
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Data Sources
- `GET /api/v1/projects/{projectId}/data-sources` - List data sources
- `POST /api/v1/projects/{projectId}/data-sources` - Create data source
- `POST /api/v1/data-sources/{id}/test` - Test connection
- `GET /api/v1/data-sources/{id}/schema` - Get schema

### Queries
- `POST /api/v1/queries/natural-language` - Process natural language query
- `POST /api/v1/queries/sql` - Execute SQL directly
- `POST /api/v1/queries/suggest-charts` - Get chart suggestions
- `GET /api/v1/queries/history` - Query history

## Configuration

### Environment Variables

#### Laravel (.env)
```env
DB_CONNECTION=sqlite
DB_DATABASE=/path/to/database.sqlite

# Redis for caching (optional)
REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

# AI Service URL
AI_SERVICE_URL=http://localhost:8003
```

#### Python AI Service
```env
OPENAI_API_KEY=your_openai_key (optional, will use mock provider without it)
WEAVIATE_URL=http://localhost:8080 (optional, will use mock vector store)
```

## Development

### Code Style
- Laravel: Follow PSR-12 standards, use Laravel Pint for formatting
- React: Use TypeScript, functional components, and hooks
- Python: Follow PEP 8 standards

### Testing
- Laravel: Use Pest for testing
- React: Jest and React Testing Library
- Python: pytest

### Database Migrations
```bash
php artisan migrate
```

### Generating API Documentation
The API documentation is automatically served at `/docs`. To update the OpenAPI specification, modify the `storage/api-docs/api-docs.json` file.

## Production Deployment

### Laravel
1. Set up production environment variables
2. Run `composer install --optimize-autoloader --no-dev`
3. Run `php artisan config:cache`
4. Run `php artisan route:cache`
5. Run `php artisan view:cache`

### React Frontend
1. Build production assets: `npm run build`
2. Serve static files from `dist/` directory

### Python AI Service
1. Use production ASGI server like Gunicorn with Uvicorn workers
2. Set up proper environment variables for OpenAI API key

## Contributing

1. Follow the established code style and conventions
2. Write tests for new features
3. Update documentation as needed
4. Use meaningful commit messages

## License

This project is proprietary software developed for HugData.

## Support

For technical support, contact: support@hugdata.com