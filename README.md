# URL Shortener API

A modern URL shortener built with FastAPI, SQLite, and JWT authentication. Features include custom short codes, click tracking, analytics, and rate limiting.

## Features

- 🔐 **JWT Authentication** - Secure user registration and login
- 🔗 **URL Shortening** - Create short URLs with custom or auto-generated codes
- 📊 **Analytics** - Track clicks, referrers, and user agents
- ⏰ **Expiration** - Set optional expiration dates for URLs
- 🎯 **Custom Codes** - Create memorable custom short codes
- 📱 **RESTful API** - Clean, documented API endpoints
- 🐳 **Docker Support** - Easy deployment with Docker

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Pydantic
- **Testing**: Pytest, HTTPX
- **CI/CD**: GitHub Actions

## Quick Start

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/mrcrysta1/url-shortener.git
cd url-shortener
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open your browser and visit: `http://localhost:8000/docs`

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t url-shortener .
```

2. Run the container:
```bash
docker run -p 8000:8000 url-shortener
```

## API Endpoints

### Authentication
- `POST /token` - Get JWT access token
- `POST /users/` - Register new user
- `GET /users/me/` - Get current user info

### URL Management
- `POST /urls/` - Create short URL
- `GET /urls/` - List user's URLs
- `GET /urls/{url_id}` - Get specific URL details
- `DELETE /urls/{url_id}` - Deactivate URL
- `GET /urls/{url_id}/stats` - Get URL analytics

### URL Redirection
- `GET /{short_code}` - Redirect to original URL

## Usage Examples

### Register a User
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "testuser", "password": "securepassword123"}'
```

### Get Access Token
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=securepassword123"
```

### Create Short URL
```bash
curl -X POST "http://localhost:8000/urls/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.example.com/very-long-url"}'
```

### Create Custom Short Code
```bash
curl -X POST "http://localhost:8000/urls/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.example.com", "custom_code": "mysite"}'
```

## Project Structure

```
url-shortener/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   ├── auth.py           # JWT authentication
│   ├── database.py       # Database connection
│   └── utils.py          # Utility functions
├── tests/
│   ├── __init__.py
│   └── test_api.py       # API tests
├── .github/workflows/
│   └── ci.yml            # GitHub Actions CI
├── requirements.txt
├── Dockerfile
├── .gitignore
├── LICENSE
└── README.md
```

## Configuration

The application uses the following environment variables (optional):

- `SECRET_KEY` - JWT secret key (default: development key)
- `DATABASE_URL` - SQLite database URL (default: `./urls.db`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time (default: 30 minutes)

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with FastAPI
- Authentication using python-jose
- Database ORM with SQLAlchemy
- Validation with Pydantic

---

**Made with ❤️ by mrcrysta1**
