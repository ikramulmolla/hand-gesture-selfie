import cv2
import mediapipe as mp
import pyttsx3
import datetime
import os
import csv
import time
import tkinter as tk
from tkinter import simpledialog

# Initialize text-to-speech
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

# Function to ask for username using a popup
def ask_username():
    """Show a popup to ask for the username."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    username = simpledialog.askstring("Enter Name", "Please enter your name:")
    root.destroy()
    return username

# Create 'selfies' folder if not exists
folder_name = "selfies"
if not os.path.exists(folder_name):
    os.makedirs(folder_name)

# CSV file to store image details
csv_file = os.path.join(folder_name, "selfie_log.csv")
if not os.path.exists(csv_file):
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Filename", "Username"])  # Write header

# Initialize camera
cap = cv2.VideoCapture(0)

# Set camera resolution to 640x480 for faster processing
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)

selfie_taken = False  # Flag to ensure only one selfie per user
timer_active = False  # Flag for active countdown
countdown_start_time = 0
display_text = "Waiting for V sign..."  # Initial text

def is_v_sign(landmarks):
    """Check if the hand is making a 'V' sign."""
    if not landmarks:
        return False

    # Finger landmark indices (MediaPipe)
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_TIP = 16
    PINKY_TIP = 20

    # Get y-coordinates of fingers
    index_y = landmarks[INDEX_FINGER_TIP].y
    middle_y = landmarks[MIDDLE_FINGER_TIP].y
    ring_y = landmarks[RING_FINGER_TIP].y
    pinky_y = landmarks[PINKY_TIP].y

    # Check if index and middle fingers are up & other fingers are down
    if index_y < landmarks[INDEX_FINGER_TIP - 2].y and \
       middle_y < landmarks[MIDDLE_FINGER_TIP - 2].y and \
       ring_y > landmarks[RING_FINGER_TIP - 2].y and \
       pinky_y > landmarks[PINKY_TIP - 2].y:
        return True
    return False

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Flip frame for a mirror effect
    frame = cv2.flip(frame, 1)

    # Convert to RGB for MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    v_sign_detected = False  # Reset for each frame

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            if is_v_sign(hand_landmarks.landmark):
                v_sign_detected = True  # V sign detected

                if not selfie_taken and not timer_active:
                    speak("Hold still! Selfie in 3 seconds.")
                    timer_active = True
                    countdown_start_time = time.time()  # Start timer

    if timer_active:
        elapsed_time = time.time() - countdown_start_time
        remaining_time = 3 - int(elapsed_time)

        if v_sign_detected:  # Continue countdown only if "V" sign is still present
            if remaining_time > 0:
                display_text = f"Selfie in {remaining_time}..."
            else:
                # Ask for the username **only when saving the selfie**
                username = ask_username()
                if username is None or username.strip() == "":
                    username = "Unknown"

                # Capture and save the selfie
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                filename = f'selfie_{username.replace(" ", "_")}.png'
                filepath = os.path.join(folder_name, filename)
                cv2.imwrite(filepath, frame)  # Save selfie
                speak(f"Selfie taken, {username}!")
                display_text = f"Last selfie: {username}"  # Show username only after taking the selfie

                # Save to CSV
                with open(csv_file, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, filename, username])

                selfie_taken = True
                timer_active = False  # Reset timer
                
                # Show selfie preview (async task)
                selfie = cv2.imread(filepath)
                cv2.imshow("Saved Selfie", selfie)
                cv2.waitKey(2000)  # Show for 2 seconds
                cv2.destroyWindow("Saved Selfie")  # Close preview
        else:
            # If V sign disappears, cancel countdown
            timer_active = False
            display_text = "Waiting for V sign..."

    else:
        # Reset when "V" sign is removed
        selfie_taken = False
        display_text = "Waiting for V sign..."

    # Set OpenCV window to fullscreen
    cv2.namedWindow("Hand Gesture Selfie", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Hand Gesture Selfie", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Display text on screen
    cv2.putText(frame, display_text, (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Display frame
    cv2.imshow("Hand Gesture Selfie", frame)

    # Exit on 'q' key
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
