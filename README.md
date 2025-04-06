# Event Management API

A FastAPI-based Event Management System that provides features for creating, managing, and tracking events and attendees.

## Features

- Event creation and management
- Attendee registration and check-in
- User authentication and authorization
- API versioning support
- Docker containerization
- Automatic event status updates
- Bulk attendee check-in via CSV

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
# Database Configuration
MYSQL_SERVER=your_server
MYSQL_USER=user
MYSQL_PASSWORD=password
MYSQL_DB=app_db
MYSQL_PORT=port
DATABASE_URL=mysql+pymysql://{user}:{password}@{host}:{port}/{db}

# JWT Configuration
SECRET_KEY=secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
PROJECT_NAME=Event Management API
VERSION=1.0.0
API_V1_STR=/api/v1
API_V2_STR=/api/v2
```

3. Start the application using Docker Compose:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

## API Documentation

### Authentication

All API endpoints except login and registration require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### API Endpoints

#### Authentication

- `POST /api/v1/user/login`
  - Login with username and password
  - Returns JWT token for authentication

#### Events

- `POST /api/v1/events`
  - Create a new event
  - Required fields: title, description, start_time, end_time, location, max_attendees
  - Optional fields: category, status

- `GET /api/v1/events`
  - List all events
  - Query parameters: skip, limit, status

- `GET /api/v1/events/{event_id}`
  - Get event details by ID

- `PUT /api/v1/events/{event_id}`
  - Update event details
  - All fields are optional

#### Attendees

- `POST /api/v1/events/{event_id}/attendees`
  - Register a new attendee for an event
  - Required fields: first_name, last_name, email, phone_number

- `GET /api/v1/events/{event_id}/attendees`
  - List all attendees for an event
  - Query parameters: skip, limit, check_in_status

- `GET /api/v1/events/{event_id}/attendees/{attendee_id}`
  - Get attendee details

- `POST /api/v1/events/{event_id}/attendees/{attendee_id}/check-in`
  - Check in an attendee
  - Only available when event status is ONGOING

- `POST /api/v1/events/{event_id}/attendees/bulk-check-in`
  - Bulk check-in attendees via CSV file
  - CSV format: email

#### Event Status

Events automatically update their status based on time:
- SCHEDULED: Before start time
- ONGOING: Between start and end time
- COMPLETED: After end time

### API Documentation Tools

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
app/
├── api/              # API endpoints and routes
│   ├── v1/          # Version 1 endpoints
│   └── v2/          # Version 2 endpoints
├── common/          # Common utilities and constants
├── core/            # Core configuration and settings
├── dao/             # Data Access Objects
├── dto/             # Data Transfer Objects
├── vo/              # Value Objects
│   ├── user.py      # User-related models
│   ├── event.py     # Event-related models
│   └── attendee.py  # Attendee-related models
├── service/         # Business logic
└── utils/           # Utility functions
```

## API Versions

- v1: Current stable version
- v2: Future version (under development)

## Testing

Run tests using pytest:
```bash
pytest
```