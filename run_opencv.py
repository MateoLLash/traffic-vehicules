import cv2
from detector import create_detector

detector = create_detector(confidence=0.5, use_peruvian_model=True)
cap = cv2.VideoCapture(r"C:\Users\User\Downloads\WhatsApp Video 2026-06-05 at 1.11.45 PM.mp4")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    detections = detector.detect(frame)
    frame_drawn = detector.draw_detections(frame, detections)
    cv2.imshow("Traffic Analysis", frame_drawn)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()