import logging
import time
from sqlalchemy import text
from app.core.database import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info("Starting database initialization...")
            logger.info(f"Database URL: {engine.url}")
            
            # Test database connection
            with engine.connect() as connection:
                logger.info("Successfully connected to the database")
                
                # Create database if it doesn't exist
                connection.execute(text("CREATE DATABASE IF NOT EXISTS event_management"))
                connection.execute(text("USE event_management"))
                
                # Create users table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        hashed_password VARCHAR(255) NOT NULL,
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        role ENUM('ADMIN', 'ORGANIZER', 'ATTENDEE') DEFAULT 'ATTENDEE',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX ix_users_id (id)
                    )
                """))
                
                # Create events table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS events (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        start_time DATETIME NOT NULL,
                        end_time DATETIME NOT NULL,
                        location VARCHAR(255) NOT NULL,
                        max_attendees INT,
                        status ENUM('SCHEDULED', 'ONGOING', 'COMPLETED') DEFAULT 'SCHEDULED',
                        organizer_id INT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX ix_events_id (id),
                        FOREIGN KEY (organizer_id) REFERENCES users(id)
                    )
                """))
                
                # Create attendees table
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS attendees (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        event_id INT NOT NULL,
                        first_name VARCHAR(100) NOT NULL,
                        last_name VARCHAR(100) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        phone_number VARCHAR(20),
                        check_in_status BOOLEAN DEFAULT FALSE,
                        check_in_time DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX ix_attendees_id (id),
                        FOREIGN KEY (event_id) REFERENCES events(id)
                    )
                """))
                
                # Verify tables were created
                result = connection.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result]
                logger.info(f"Existing tables: {tables}")
                
                required_tables = {'users', 'events', 'attendees'}
                if required_tables.issubset(set(tables)):
                    logger.info("All required tables created successfully!")
                    return
                else:
                    missing_tables = required_tables - set(tables)
                    logger.warning(f"Missing tables: {missing_tables}. Retrying...")
                    retry_count += 1
                    time.sleep(5)
                    
        except Exception as e:
            logger.error(f"Error during database initialization (attempt {retry_count + 1}/{max_retries}): {str(e)}")
            retry_count += 1
            time.sleep(5)
    
    raise Exception("Failed to create all required tables after multiple attempts")

if __name__ == "__main__":
    init_db()