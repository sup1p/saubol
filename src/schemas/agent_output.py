from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class Diagnosis(BaseModel):
    mkb_code: str
    name: str
    reason: str = Field(description="Причина выбора данного кода МКБ-10. Пошаговое объяснение от верхнего уровня до конечных деталей")
    
class SimilarDiagnosis(BaseModel):
    exact_answer: Optional[Diagnosis] = Field( description="Точный ответ если был найден детальный код МКБ-10. Или первый из списка похожих если точного нет")
    similar_answers: List[Diagnosis] = Field(description="Список похожих ответов если не был найден точный ответ")


class MessageToRoleAgent(BaseModel):
    role: str
    content: str
    
class RoleAgentOutput(BaseModel):
    messages: list[MessageToRoleAgent]
    

