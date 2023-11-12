import mysql.connector

# MySQL server details
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="3232",
    database="DrowsinessDatabase"
)
cursor = db_connection.cursor()

# Function to calculate the drowsiness score for a specific driver
def calculate_driver_score(username, password):
    # Check if the provided username and password exist in the database
    check_credentials_query = "SELECT driver_id, driver_name, age, diabetic FROM driver_info WHERE username = %s AND password = %s"
    cursor.execute(check_credentials_query, (username, password))
    driver_info = cursor.fetchone()

    if driver_info:
        driver_id, driver_name, age, diabetic = driver_info

        # Fetch all sessions for the driver
        select_sessions_query = "SELECT session_id, session_duration FROM session_data WHERE driver_id = %s"
        cursor.execute(select_sessions_query, (driver_id,))
        sessions = cursor.fetchall()

        # Initialize a list to store session scores
        session_scores = []

        for session in sessions:
            session_id, session_duration = session

            # Fetch drowsiness data for the session
            select_drowsiness_query = "SELECT SUM(duration) FROM drowsiness_data WHERE session_id = %s"
            cursor.execute(select_drowsiness_query, (session_id,))
            total_drowsy_duration = cursor.fetchone()[0] or 0  # If no drowsiness data, set to 0

            # Calculate session score as a percentage
            if session_duration > 0:
                session_score = (total_drowsy_duration / session_duration) * 100
            else:
                session_score = 0  # To avoid division by zero

            # Adjust the score based on age and diabetic status
            if age > 40:
                session_score *= 1.1  # Increase the score by 10% for age above 40
            if diabetic == 'yes':
                session_score *= 1.2  # Increase the score by 20% for diabetic drivers

            session_scores.append((session_id, session_score))

        # Calculate the average score across all sessions
        total_score = sum([score for (_, score) in session_scores])
        average_score = total_score / len(session_scores)

        # Display session scores for the driver
        print(f"Driver: {driver_name}")
        for session_id, session_score in session_scores:
            print(f"Session ID: {session_id}, Score: {session_score:.2f}%")

        # Display the average score for the driver
        print(f"Average Score: {average_score:.2f}%")

    else:
        print("Invalid login credentials")

# Provide a login id and password to calculate the score for a specific driver
username = "S"
password = "S"
calculate_driver_score(username, password)

# Close the database connection
cursor.close()
db_connection.close()
