from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date



class PDFSummary(BaseModel):
    patient_name: str | None = None
    age_sex: str | None = None
    admission_date: str | None = None
    record_number: str | None = None
    complaints: str | None = None
    present_illness: str | None = None
    past_history: str | None = None
    examination: str | None = None
    diagnosis: str | None = None
    treatment: str | None = None
    prognosis: str | None = None
    
    
class MessageToRoleAgent(BaseModel):
    role: str
    content: str
    
class RoleAgentOutput(BaseModel):
    messages: list[MessageToRoleAgent]
    
    
    
class LifeHistory(BaseModel):
    heredity: Optional[str] = None
    allergy_history: Optional[str] = None
    chronic_diseases: Optional[str] = None
    medications: Optional[str] = None

class NeurologicalStatus(BaseModel):
    general_condition: Optional[str] = None
    consciousness: Optional[str] = None
    skin: Optional[str] = None
    signs: Optional[List[str]] = None
    focal_symptoms: Optional[str] = None

class Prescription(BaseModel):
    name: str
    dosage: Optional[str] = None
    quantity: Optional[str] = None
    instructions: Optional[str] = None

class MedicalProtocol(BaseModel):
    report_date: Optional[str] = Field(default_factory=lambda: date.today().isoformat())
    complaints: Optional[str] = None
    history_of_disease: Optional[str] = None
    life_history: Optional[LifeHistory] = None
    objective_status: Optional[NeurologicalStatus] = None
    preliminary_diagnosis: Optional[str] = None
    investigation_plan: Optional[List[str]] = None
    treatment_plan: Optional[List[str]] = None
    patient_recommendations: Optional[List[str]] = None
    prescriptions: Optional[List[Prescription]] = None
    follow_up: Optional[str] = None
