from pydantic import BaseModel
from typing import List, Dict

class ManagerAnalysisRequest(BaseModel):
    dialog_text: str

class ManagerAnalysisResponse(BaseModel):
    detected_objections: int
    objections: List[Dict]
    recommendations: Dict[str, List[str]]
    conversion_tips: List[str]
