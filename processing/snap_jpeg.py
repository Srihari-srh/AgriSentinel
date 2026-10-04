import cv2

cap = cv2.VideoCapture(0)
ret, frame = cap.read()

if ret:
    cv2.imwrite("/userdata/snapshot.jpg", frame)
    print("Snapshot saved successfully to /userdata/snapshot.jpg[cite: 1]!")
else:
    print("Failed to capture image.")

cap.release()