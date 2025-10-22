from fastapi import APIRouter, HTTPException
from pathlib import Path



router = APIRouter(prefix="/api", tags=["documents"])


@router.get("/protocol")
async def get_protocol(room_name: str):
    """
    Retrieve the medical protocol document for a given room.
    
    Args:
        room_name: Name of the room to get the protocol for.
    """
    file_path = Path(f"output/medical_protocol_{room_name}.txt")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Protocol not found")
    
    with open(file_path, "r", encoding="utf-8") as f:
        protocol_content = f.read()

    return {"room_name": room_name, "protocol": protocol_content}