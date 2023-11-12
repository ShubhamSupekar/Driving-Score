import cv2
import numpy as np
from keras.models import load_model
from pygame import mixer
import mysql.connector
from datetime import datetime

session_id = None  # Get the ID of the newly inserted session
session_start_time = None
            
# Function to register a new user
def register_user(cursor, db_connection):
    print("Register a new user:")
    driver_name = input("Enter your name: ")
    username = input("Enter a username: ")
    password = input("Enter a password: ")
    age = int(input("Enter your age: "))
    diabetic = input("Are you diabetic? (yes or no): ")

    # Insert user registration data into the driver_info table
    insert_user_query = "INSERT INTO driver_info (driver_name, username, password, age, diabetic) VALUES (%s, %s, %s, %s, %s)"
    user_data = (driver_name, username, password, age, diabetic)
    cursor.execute(insert_user_query, user_data)
    db_connection.commit()

# Function to log in an existing user
def login_user(cursor):
    print("Login:")
    username = input("Enter your username: ")
    password = input("Enter your password: ")

    # Check if the provided username and password match a record in the driver_info table
    select_user_query = "SELECT driver_id, driver_name, age, diabetic FROM driver_info WHERE username = %s AND password = %s"
    user_data = (username, password)
    cursor.execute(select_user_query, user_data)
    user_record = cursor.fetchone()

    if user_record:
        driver_id, driver_name, age, diabetic = user_record
        print(f"Welcome, {driver_name}!")
        return driver_id, driver_name, age, diabetic
    else:
        print("Invalid username or password. Please try again.")
        return None

# MySQL server details
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="3232",
    database="DrowsinessDatabase"
)
cursor = db_connection.cursor()

mixer.init()
sound = mixer.Sound('D:/Study/Research/Final Research Project/Alarm/alarm.wav')

# Check if the user wants to register or login
while True:
    choice = input("Do you want to register (r) or login (l)? ").lower()
    if choice == 'r':
        register_user(cursor, db_connection)
    elif choice == 'l':
        user_data = login_user(cursor)
        if user_data:
            driver_id, driver_name, age, diabetic = user_data
            # Initialize a new session when the user logs in
            insert_session_query = "INSERT INTO session_data (driver_id, session_duration) VALUES (%s, %s)"
            cursor.execute(insert_session_query, (driver_id, 0.0))  # Start with a duration of 0.0 seconds
            db_connection.commit()
            session_id = cursor.lastrowid  # Get the ID of the newly inserted session
            session_start_time = datetime.now()
            break
    else:
        print("Invalid choice. Please enter 'r' to register or 'l' to login.")

# Load the trained model
best_model = load_model('D:/Study/Research/Final Research Project/Model/DiffCnn100HighAccModel.h5')

# Create a Cascade Classifier for face and eye detection
face_cascade = cv2.CascadeClassifier('D:/Study/Research/Final Research Project/Classifiers/haarcascade_frontalface_default.xml')
leye = cv2.CascadeClassifier('D:/Study/Research/Final Research Project/Classifiers/haarcascade_lefteye_2splits.xml')
reye = cv2.CascadeClassifier('D:/Study/Research/Final Research Project/Classifiers/haarcascade_righteye_2splits.xml')

# Open a video capture object (you may adjust the camera index or video file path)
# cap = cv2.VideoCapture("D:/Study/Research/Research Project/Video Files/WIN_20230927_22_27_58_Pro.mp4")
# cap = cv2.VideoCapture("D:/Study/Research/Research Project/Video Files/P1042751_na.mp4")
cap = cv2.VideoCapture(0)

# Define the new width and height for downscaling
new_width = 320 #640  # Adjust as needed
new_height = 240 # 480  # Adjust as needed

# Initialize session variables

lopen = None
ropen = None

font = cv2.FONT_HERSHEY_COMPLEX_SMALL
counter = 0
drowsiness_start_time = datetime.now()
drowsiness_duration = 0
drowsiness_detected = False

while True:
    ret, frame = cap.read()
    height, width = frame.shape[:2]

    if not ret:
        break

    # Downscale the frame
    frame = cv2.resize(frame, (new_width, new_height))

    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 100, 100), 1)

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]
        Left_eye = leye.detectMultiScale(roi_gray)
        Right_eye = reye.detectMultiScale(roi_gray)

        for (ex, ey, ew, eh) in Left_eye:
            l_eye = roi_gray[ey:ey + eh, ex:ex + ew]
            l_eye = cv2.resize(l_eye, (64, 64))  # Resize to match the model's input size
            l_eye = (np.array(l_eye) - np.min(l_eye)) / (np.max(l_eye) - np.min(l_eye))
            l_eye = l_eye / 255.0  # Normalize

            # Expand dimensions to match model input shape
            l_eye = np.expand_dims(l_eye, axis=0)

            # Predict whether the eye is open or closed
            Lprediction = best_model.predict(l_eye)
            if Lprediction > 0.1:
                lopen = 1
            else:
                lopen = 0
            break

        for (ex, ey, ew, eh) in Right_eye:
            r_eye = roi_gray[ey:ey + eh, ex:ex + ew]
            r_eye = cv2.resize(r_eye, (64, 64))  # Resize to match the model's input size
            r_eye = (np.array(r_eye) - np.min(r_eye)) / (np.max(r_eye) - np.min(r_eye))
            r_eye = r_eye / 255.0  # Normalize

            # Expand dimensions to match model input shape
            r_eye = np.expand_dims(r_eye, axis=0)

            # Predict whether the eye is open or closed
            Rprediction = best_model.predict(r_eye)
            if Rprediction > 0.1:
                ropen = 1
            else:
                ropen = 0
            break

        if ropen == 1 or lopen == 1:
            if not drowsiness_detected:
                drowsiness_start_time = datetime.now()
                drowsiness_detected = True
            counter -= 1
            if counter < 0:
                sound.stop()
                counter = 0
            cv2.putText(frame, "Open", (10, new_height - 20), font, 1, (0, 0, 255), 1, cv2.LINE_AA)
        else:
            counter += 1
            if drowsiness_detected:
                drowsiness_end_time = datetime.now()
                drowsiness_duration = (drowsiness_end_time - drowsiness_start_time).total_seconds()

                if drowsiness_duration > 3:
                    # Insert drowsiness data into the database
                    insert_query = "INSERT INTO drowsiness_data (drowsy_datetime, duration, session_id, driver_id, day_or_night) VALUES (%s, %s, %s, %s, %s)"
                    data = (drowsiness_start_time, drowsiness_duration, session_id, driver_id, 'night')  # Modify 'day' to 'night' as needed
                    cursor.execute(insert_query, data)
                    db_connection.commit()

                # Reset drowsiness variables
                drowsiness_detected = False
            if counter > 4:
                try:
                    sound.play()
                except:
                    pass
            cv2.putText(frame, "Closed", (10, new_height - 20), font, 1, (0, 0, 255), 1, cv2.LINE_AA)

    cv2.putText(frame, 'Count:{:.2f}'.format(counter), (100, new_height - 20), font, 1, (0, 0, 255), 1, cv2.LINE_AA)

    # Display the frame
    cv2.imshow('Drowsiness Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

code_end_time = datetime.now()
session_duration = (code_end_time - session_start_time).total_seconds()

update_session_query = "UPDATE session_data SET session_duration = %s WHERE session_id = %s"
data = (session_duration, session_id)
cursor.execute(update_session_query, data)
db_connection.commit()

# Release the video capture object and close all windows
cursor.close()
db_connection.close()
cap.release()
cv2.destroyAllWindows()