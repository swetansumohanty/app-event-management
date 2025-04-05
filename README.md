# Event Management API

A FastAPI-based Event Management System that provides features for creating, managing, and tracking events and attendees.

## Features

- Event creation and management
- Attendee registration and check-in
- User authentication and authorization
- API versioning support
- Docker containerization

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- MySQL

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd event-management-app
```

2. Create a `.env` file in the root directory:
```env
MYSQL_SERVER=db
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=event_management
MYSQL_PORT=3306
SECRET_KEY=your-secret-key-here
```

3. Start the application using Docker Compose:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
app/
├── api/
│   ├── v1/
│   └── v2/
├── common/
├── core/
├── dao/
├── dto/
├── vo/
│   ├── user.py
│   ├── event.py
│   └── attendee.py
├── service/
└── utils/
```

## API Versions

- v1: Current stable version
- v2: Future version (under development)

## Testing

Run tests using pytest:
```bash
pytest
```

## License

MIT 