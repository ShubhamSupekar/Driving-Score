import cv2
import numpy as np
from keras.models import load_model
from pygame import mixer
import mysql.connector
from datetime import datetime

# MySQL server details
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="3232",
    database="DrowsinessDatabase"
)
cursor = db_connection.cursor()
session_start_time = datetime.now()

# Insert a new record in the session_data table to get the session ID
insert_session_query = "INSERT INTO session_data (session_duration) VALUES (NULL)"
cursor.execute(insert_session_query)
db_connection.commit()
session_id = cursor.lastrowid  # Get the session ID

mixer.init()
sound = mixer.Sound('Final Research Project/Alarm/alarm.wav')

# Load the trained model
best_model = load_model('Final Research Project/Model/DiffCnn100HighAccModel.h5')

# Create a Cascade Classifier for face and eye detection
face_cascade = cv2.CascadeClassifier('Final Research Project/Classifiers/haarcascade_frontalface_default.xml')
leye = cv2.CascadeClassifier('Final Research Project/Classifiers/haarcascade_lefteye_2splits.xml')
reye = cv2.CascadeClassifier('Final Research Project/Classifiers/haarcascade_righteye_2splits.xml')

# Open a video capture object (you may adjust the camera index or video file path)
# cap = cv2.VideoCapture("Research Project/Video Files/WIN_20230927_22_27_58_Pro.mp4")
# cap = cv2.VideoCapture("Research Project/Video Files/P1042751_na.mp4")
cap = cv2.VideoCapture(1)

# Define the new width and height for downscaling
new_width =  640  # Adjust as needed 640 320
new_height = 480 # Adjust as needed 480 240 

lopen = None
ropen = None

font = cv2.FONT_HERSHEY_COMPLEX_SMALL
counter = 0
drowsiness_start_time = None
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
            if (Lprediction > 0.1):
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
            if (Rprediction > 0.1):
                ropen = 1
            else:
                ropen = 0
            break

        if ropen == 1 or lopen == 1:
            if not drowsiness_detected:
                drowsiness_start_time = datetime.now()
                drowsiness_detected = True
            counter -= 2
            if (counter < 0):
                sound.stop()
                counter = 0
            cv2.putText(frame, "Open", (10, new_height - 20), font, 1, (0, 0, 255), 1, cv2.LINE_AA)
        else:
            counter += 1
            if drowsiness_detected:
                drowsiness_end_time = datetime.now()
                drowsiness_duration = (drowsiness_end_time - drowsiness_start_time).total_seconds()

                if drowsiness_duration > 3:
                    insert_query = "INSERT INTO drowsiness_data (drowsy_datetime, duration, session_id) VALUES (%s, %s, %s)"
                    data = (drowsiness_start_time, drowsiness_duration, session_id)
                    cursor.execute(insert_query, data)
                    db_connection.commit()

                # Reset drowsiness variables
                drowsiness_detected = False
            if (counter > 4):
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
# Insert session duration into the session_data table
update_session_query = "UPDATE session_data SET session_duration = %s WHERE id = %s"
data = (session_duration, session_id)
cursor.execute(update_session_query, data)
db_connection.commit()
# Release the video capture object and close all windows
cursor.close()
db_connection.close()
cap.release()
cv2.destroyAllWindows()