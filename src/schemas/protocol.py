from __future__ import annotations
from typing import List, Optional, Literal
from datetime import date, datetime

from pydantic import BaseModel, Field, confloat

# Тип для confidence: число в диапазоне [0.0, 1.0]
Confidence = confloat(ge=0.0, le=1.0)


class Patient(BaseModel):
    """Информация о пациенте (идентификация)."""
    id: Optional[str] = Field(None, description="Уникальный идентификатор пациента или null, если неизвестен")
    full_name: Optional[str] = Field(None, description="ФИО пациента или null")
    age: Optional[int] = Field(None, description="Возраст в годах или null")
    sex: Optional[Literal['M', 'F', 'other']] = Field(
        None, description="Пол: 'M'/'F'/'other' или null"
    )
    date_of_exam: Optional[date] = Field(
        None, description="Дата осмотра в формате YYYY-MM-DD"
    )


class Metadata(BaseModel):
    """Метаданные сессии/транскрипта."""
    doctor_specialty: Optional[str] = Field(None, description="Специальность врача (если известна)")
    audio_source_id: Optional[str] = Field(None, description="ID источника аудио или null")
    transcript_version: Optional[str] = Field(None, description="Версия/модель транскрипции или null")
    languages_detected: List[str] = Field(..., description="Список детектированных языков, напр. ['ru','kz','en']")
    consent_recording: bool = Field(..., description="Есть ли согласие пациента на запись (true/false)")
    flags: List[str] = Field(default_factory=list, description="Флаги: low_confidence_segments, multiple_speakers, EMERGENCY и т.п.")


class SourceTimestamp(BaseModel):
    """Простой контейнер для таймкодов (секунды или дробные секунды)."""
    ts: float = Field(..., description="Время в секундах от начала аудио (может быть точкой/интервалом).")


class ChiefComplaint(BaseModel):
    """Жалоба пациента в формализованном виде с указанием источника и уверенности."""
    text: str = Field(..., description="Формализованная версия жалобы (кратко)")
    raw_text: Optional[str] = Field(None, description="Исходная фраза из транскрипта (verbatim)")
    confidence: Confidence = Field(..., description="Оценка доверия извлечения (0.0-1.0)")


class AnamnesisMorbi(BaseModel):
    text: Optional[str] = Field(None, description="Описание заболевания: начало, динамика, самолечение и т.д.")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class AnamnesisVitae(BaseModel):
    text: Optional[str] = Field(None, description="Анамнез жизни: хронические заболевания, операции, пр.")
    dispensary_register_status: Optional[Literal['registered', 'not_registered', 'unknown']] = Field(
        'unknown', description="Статус диспансерного учёта"
    )
    allergies: List[str] = Field(default_factory=list, description="Список аллергий или ['none']")
    chronic_diseases: List[str] = Field(default_factory=list, description="Список кодов МКБ-10 хронических заболеваний")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class BP(BaseModel):
    systolic: Optional[int] = Field(None, description="Систолическое давление (ммHg)")
    diastolic: Optional[int] = Field(None, description="Диастолическое давление (ммHg)")
    unit: Literal['mmHg'] = Field('mmHg', description="Единица измерения давления")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class Vital(BaseModel):
    value: Optional[float] = Field(None, description="Значение витального показателя")
    unit: Optional[str] = Field(None, description="Единица измерения (°C, bpm и т.д.)")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class OtherFinding(BaseModel):
    text: str = Field(..., description="Текстовое описание дополнительного находки")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class ObjectiveStatus(BaseModel):
    summary: Optional[str] = Field(None, description="Краткое резюме объективного статуса (осмотренное)")
    vitals: Optional[dict] = Field(
        default_factory=dict,
        description="Словарь витальных показателей: temperature, pulse, bp (BP модель)"
    )
    other_findings: List[OtherFinding] = Field(default_factory=list, description="Дополнительные найденные признаки")
    confidence: Confidence = Field(..., description="Общая доверенность блока объективного статуса")


class StatusLocalisRegion(BaseModel):
    region: str = Field(..., description="Анатомическая область осмотра, напр. 'правое колено'")
    findings: List[OtherFinding] = Field(default_factory=list, description="Список находок для области")


class PreliminaryDiagnosis(BaseModel):
    text: str = Field(..., description="Текст предварительного диагноза")
    icd10: Optional[str] = Field(None, description="Код МКБ-10, если подобран")
    certainty: Optional[Literal['high', 'medium', 'low']] = Field(None, description="Степень уверенности диагноза")
    rationale: Optional[str] = Field(None, description="Обоснование (почему предложен)")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class DifferentialDiagnosis(BaseModel):
    text: str = Field(..., description="Текст варианта дифференциального диагноза")
    icd10: Optional[str] = Field(None, description="Возможный код МКБ-10")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class PlanInvestigation(BaseModel):
    order: int = Field(..., description="Порядковый номер в плане обследования")
    test: str = Field(..., description="Название исследования/анализа")
    notes: Optional[str] = Field(None, description="Доп. примечания, показания")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class PlanTreatment(BaseModel):
    order: int = Field(..., description="Порядковый номер в плане лечения")
    treatment: str = Field(..., description="Название препарата/процедуры")
    dose: Optional[str] = Field(None, description="Дозировка или null (если не указана)")
    route: Optional[str] = Field(None, description="Путь введения: oral/iv/etc или null")
    freq: Optional[str] = Field(None, description="Кратность приёма, напр. '1 раз в день'")
    duration: Optional[str] = Field(None, description="Длительность курса или null")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class Recommendation(BaseModel):
    order: int = Field(..., description="Порядковый номер рекомендации")
    text: str = Field(..., description="Текст рекомендации в официальной формулировке")
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class Prognosis(BaseModel):
    text: Optional[str] = Field(None, description="Краткое заключение по прогнозу")
    category: Optional[Literal['favorable', 'conditional', 'unfavorable']] = Field(
        None, description="Категория прогноза"
    )
    confidence: Confidence = Field(..., description="Доверие (0.0-1.0)")


class SignOff(BaseModel):
    doctor_name: Optional[str] = Field(None, description="ФИО врача или null")
    specialty: Optional[str] = Field(None, description="Специальность врача")
    experience_years: int = Field(0, description="Стаж в годах (целое число)")
    signature_required: bool = Field(True, description="Требуется ли подпись для финализации протокола")


class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(..., description="Время записи действия в формате ISO8601")
    action: str = Field(..., description="Действие, напр. 'extracted finding'")
    detail: Optional[str] = Field(None, description="Дополнительные детали")
    source_ts: List[float] = Field(default_factory=list, description="Таймкоды, связанные с действием")


class MedicalProtocol(BaseModel):
    """Главная модель — протокол первичного осмотра, соответствует требуемой JSON-схеме."""
    patient: Patient = Field(..., description="Блок идентификации пациента")
    metadata: Metadata = Field(..., description="Метаданные транскрипта/сессии")
    chief_complaints: List[ChiefComplaint] = Field(default_factory=list, description="Список жалоб")
    anamnesis_morbi: Optional[AnamnesisMorbi] = Field(None, description="Анамнез заболевания")
    anamnesis_vitae: Optional[AnamnesisVitae] = Field(None, description="Анамнез жизни")
    objective_status: Optional[ObjectiveStatus] = Field(None, description="Объективный статус (кратко)")
    status_localis: List[StatusLocalisRegion] = Field(default_factory=list, description="Подробный локальный осмотр (Status localis)")
    preliminary_diagnosis: List[PreliminaryDiagnosis] = Field(default_factory=list, description="Предварительные диагнозы с МКБ-10")
    differential_diagnosis: List[DifferentialDiagnosis] = Field(default_factory=list, description="Дифференциальный диагноз с МКБ-10")
    plan_investigations: List[PlanInvestigation] = Field(default_factory=list, description="План обследования")
    plan_treatment: List[PlanTreatment] = Field(default_factory=list, description="План лечения")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Рекомендации пациену на основе его диагноза если врач не дал своих(даже если дал дополнять их сюда на основе диагноза)")
    prognosis: Optional[Prognosis] = Field(None, description="Прогноз")
    sign_off: Optional[SignOff] = Field(None, description="Подпись врача и метаданные по авторству")
    audit_log: List[AuditLogEntry] = Field(default_factory=list, description="История изменений / действий для аудита")

    class Config:
        json_schema_extra = {
            'example': {
                'patient': {'id': None, 'full_name': 'Иванов И.И.', 'age': 45, 'sex': 'M', 'date_of_exam': '2025-10-24'},
                'metadata': {'doctor_specialty': 'therapist', 'audio_source_id': None, 'transcript_version': 'v1', 'languages_detected': ['ru'], 'consent_recording': True, 'flags': []},
                'chief_complaints': [{'text': 'боль в груди', 'raw_text': 'Болит грудь уже 3 дня', 'source_timestamps': [12.4], 'confidence': 0.95}],
                'anamnesis_morbi': {'text': 'Боль началась 3 дня назад...', 'source_timestamps': [12.4], 'confidence': 0.9},
                'anamnesis_vitae': {'text': 'Хронически: Гипертония', 'dispensary_register_status': 'registered', 'allergies': ['penicillin'], 'chronic_diseases': ['I10'], 'source_timestamps': [30.0], 'confidence': 0.9},
                'objective_status': {'summary': 'Пациент в удовлетворительном состоянии', 'vitals': {}, 'other_findings': [], 'confidence': 0.9},
                'status_localis': [{'region': 'левое колено', 'findings': []}],
                'preliminary_diagnosis': [{'text': 'Острый бронхит, вызванный Mycoplasma pneumoniae', 'icd10': 'J20.0', 'certainty': 'medium', 'rationale': 'на основании жалоб', 'source_ts': [45.0], 'confidence': 0.65}],
                'differential_diagnosis': [{"text": "Острый бронхит, вызванный Haemophilus influenzae [палочкой Афанасьева-Пфейффера]", "icd10": "J20.1", "confidence": 0.5}, {"text": "Острый бронхит, вызванный стрептококком", "icd10": "J20.2", "confidence": 0.4}],
                'plan_investigations': [],
                'plan_treatment': [],
                'recommendations': [],
                'prognosis': {'text': 'Возможен благоприятный исход', 'category': 'conditional', 'confidence': 0.6},
                'sign_off': {'doctor_name': None, 'specialty': 'therapist', 'experience_years': 10, 'signature_required': True},
                'audit_log': []
            }
        }

