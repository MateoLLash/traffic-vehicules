import os
from dotenv import load_dotenv
from roboflow import Roboflow
from ultralytics import YOLO

load_dotenv()

if __name__ == '__main__':
    # 1. Descargar dataset desde Roboflow
    rf = Roboflow(api_key=os.getenv("ROBOFLOW_API_KEY"))
    project = rf.workspace("mateos-workspace-oz4wl").project("vehiculos-peruanos-lima")
    dataset = project.version(3).download("yolov8")

    # 2. Entrenar con YOLOv8
    model = YOLO("yolov8s.pt")
    model.train(
        data=f"{dataset.location}/data.yaml",
        epochs=100,
        imgsz=640,
        batch=16,
        device=0,
        workers=4,  # reducido para Windows
        project="runs/train",
        name="vehiculos-v3"
    )

    print("✅ Entrenamiento completado!")
    print("Modelo en: runs/train/vehiculos-v3/weights/best.pt")