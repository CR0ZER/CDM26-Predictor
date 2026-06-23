from fastapi import APIRouter, HTTPException
from src.data.online.football_data_org import get_upcoming_matches

router = APIRouter()


@router.get("/matches")
def list_matches():
    try:
        return get_upcoming_matches()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur football-data.org : {e}")