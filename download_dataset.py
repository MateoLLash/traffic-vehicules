from roboflow import Roboflow

rf = Roboflow(api_key="HuBd4pkG0GIPdDEUIFCE")
project = rf.workspace("mateos-workspace-oz4wl").project("vehiculos-peruanos-lima")
dataset = project.version(1).download("yolov8")