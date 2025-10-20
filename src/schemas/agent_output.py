from unittest.mock import Base
from pydantic import BaseModel


class PDFSummary(BaseModel):
    report_date: str | None = None
    doctor_name: str | None = None
    doctor_position: str | None = None
    institution: str | None = None
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
