from fastapi import APIRouter
from dashboard.backend.services.csv_reader import read_all, read_latest


router = APIRouter(prefix="/telemetry")

@router.get("/history")
def get_history():
    return read_all()

@router.get("/latest")
def get_latest():
    return read_latest()
