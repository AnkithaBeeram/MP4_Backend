from flask import Flask, jsonify, request
import os
import pymysql
from pymysql.err import OperationalError
import logging
from flask_cors import CORS

application = Flask(__name__)
CORS(application)
logging.basicConfig(level=logging.INFO)


# Endpoint: Health Check
@application.route('/health', methods=['GET'])
def health():
    """
    This endpoint is used by the autograder to confirm that the backend deployment is healthy.
    """
    return jsonify({"status": "healthy"}), 200


# Endpoint: Data Insertion
@application.route('/events', methods=['POST'])
@application.route('/data', methods=['POST'])
def create_event():
    """
    Insert event data into the database.
    """
    try:
        payload = request.get_json()
        required_fields = ["title", "date"]
        if not payload or not all(field in payload for field in required_fields):
            return jsonify({"error": "Missing required fields: 'title' and 'date'"}), 400

        insert_data_into_db(payload)
        return jsonify({"message": "Event created successfully"}), 201

    except Exception as e:
        logging.exception("Error occurred during event creation")
        return jsonify({
            "error": "During event creation",
            "detail": str(e)
        }), 500


# Endpoint: Data Retrieval

@application.route('/data', methods=['GET'])
def get_data():
    try:
        data = fetch_data_from_db()
        return jsonify({"data": data}), 200
    except Exception as e:
        logging.exception("Error occurred during data retrieval")
        return jsonify({
            "error": "During data retrieval",
            "detail": str(e)
        }), 500

def get_db_connection():
    """
    Establish and return a connection to the RDS MySQL database.
    Required environment variables:
      - DB_HOST
      - DB_USER
      - DB_PASSWORD
      - DB_NAME
    """
    required_vars = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        msg = f"Missing environment variables: {', '.join(missing)}"
        logging.error(msg)
        raise EnvironmentError(msg)

    try:
        connection = pymysql.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            db=os.environ.get("DB_NAME"),
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )
        return connection
    except OperationalError as e:
        raise ConnectionError(f"Failed to connect to the database: {e}")


def create_db_table():
    """
    Create the events table if it does not already exist.
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                image_url VARCHAR(500),
                date DATE NOT NULL,
                location VARCHAR(255)
            )
            """
            cursor.execute(create_table_sql)
        connection.commit()
        logging.info("Events table created or already exists")
    except Exception as e:
        connection.rollback()
        logging.exception("Failed to create or verify the events table")
        raise RuntimeError(f"Table creation failed: {str(e)}")
    finally:
        connection.close()


def insert_data_into_db(payload):
    """
    Insert one event into the events table.
    """
    create_db_table()
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            insert_sql = """
            INSERT INTO events (title, description, image_url, date, location)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(
                insert_sql,
                (
                    payload.get("title"),
                    payload.get("description"),
                    payload.get("image_url"),
                    payload.get("date"),
                    payload.get("location")
                )
            )
        connection.commit()
        logging.info("Event inserted successfully")
    except Exception as e:
        connection.rollback()
        logging.exception("Failed to insert event into database")
        raise RuntimeError(f"Database insert failed: {str(e)}")
    finally:
        connection.close()


def fetch_data_from_db():
    """
    Fetch all events from the database in ascending order of date.
    Return as a list of objects.
    """
    create_db_table()
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            fetch_sql = """
            SELECT id, title, description, image_url, date, location
            FROM events
            ORDER BY date ASC
            """
            cursor.execute(fetch_sql)
            rows = cursor.fetchall()

        events = []
        for row in rows:
            formatted_date = row["date"].strftime("%a, %d %b %Y 00:00:00 GMT")
            events.append({
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "image_url": row["image_url"],
                "date": formatted_date,
                "location": row["location"]
            })

        return events

    except Exception as e:
        logging.exception("Failed to fetch data from database")
        raise RuntimeError(f"Database fetch failed: {str(e)}")
    finally:
        connection.close()


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))