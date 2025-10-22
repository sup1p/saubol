from src.schemas.agent_output import MedicalProtocol
from typing import List 
import os
from datetime import date
    
    
def save_protocol_as_txt(protocol: MedicalProtocol, output_dir: str, header_data: dict,client: str = "default") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"medical_protocol_{client}.txt"
    output_path = os.path.join(output_dir, filename)

    lines: List[str] = []
    lines.append("МЕДИЦИНСКИЙ ПРОТОКОЛ")
    lines.append("Форма утверждена МЗ РК")
    lines.append("")

    # Жалобы
    lines.append("ЖАЛОБЫ:")
    lines.append(protocol.complaints or "-")
    lines.append("")

    # Анамнез заболевания
    lines.append("АНАМНЕЗ ЗАБОЛЕВАНИЯ:")
    lines.append(protocol.history_of_disease or "-")
    lines.append("")

    # Анамнез жизни
    lines.append("АНАМНЕЗ ЖИЗНИ:")
    lh = protocol.life_history
    if lh:
        lines.append(f"- Наследственность: {lh.heredity or '-'}")
        lines.append(f"- Аллергологический анамнез: {lh.allergy_history or '-'}")
        lines.append(f"- Хронические заболевания: {lh.chronic_diseases or '-'}")
        lines.append(f"- Приём медикаментов: {lh.medications or '-'}")
    else:
        lines.append("- -")
    lines.append("")

    # Объективный статус
    lines.append("ОБЪЕКТИВНЫЙ СТАТУС:")
    os_stat = protocol.objective_status
    if os_stat:
        lines.append(f"Общее состояние: {os_stat.general_condition or '-'}")
        lines.append(f"Сознание: {os_stat.consciousness or '-'}")
        lines.append(f"Кожные покровы: {os_stat.skin or '-'}")
        if os_stat.signs:
            lines.append("Неврологический статус:")
            for s in os_stat.signs:
                lines.append(f"- {s}")
        else:
            # сохранить краткое упоминание признаков, если focal_symptoms содержит текст
            if os_stat.focal_symptoms:
                lines.append("Неврологический статус:")
                lines.append(f"- {os_stat.focal_symptoms}")
            else:
                lines.append("-")
    else:
        lines.append("-")
    lines.append("")

    # Предварительный диагноз
    lines.append("ПРЕДВАРИТЕЛЬНЫЙ ДИАГНОЗ:")
    lines.append(protocol.preliminary_diagnosis or "-")
    lines.append("")

    # План обследования
    lines.append("ПЛАН ОБСЛЕДОВАНИЯ:")
    if protocol.investigation_plan:
        for i, item in enumerate(protocol.investigation_plan, start=1):
            lines.append(f"{i}. {item}")
    else:
        lines.append("-")
    lines.append("")

    # План лечения
    lines.append("ПЛАН ЛЕЧЕНИЯ:")
    if protocol.treatment_plan:
        for i, item in enumerate(protocol.treatment_plan, start=1):
            lines.append(f"{i}. {item}")
    else:
        lines.append("-")
    lines.append("")

    # Рекомендации пациенту
    lines.append("РЕКОМЕНДАЦИИ ПАЦИЕНТУ:")
    if protocol.patient_recommendations:
        for rec in protocol.patient_recommendations:
            lines.append(f"- {rec}")
    else:
        lines.append("-")
    lines.append("")

    # Назначения
    lines.append("НАЗНАЧЕНИЯ:")
    if protocol.prescriptions:
        for p in protocol.prescriptions:
            qty = f" №{p.quantity}" if p.quantity else ""
            dosage = f" {p.dosage}" if p.dosage else ""
            instr = f"\nСпособ применения: {p.instructions}" if p.instructions else ""
            lines.append(f"{p.name}{dosage}{qty}{instr}")
    else:
        lines.append("-")
    lines.append("")

    # Контроль / повторный приём
    lines.append("КОНТРОЛЬ / ПОВТОРНЫЙ ПРИЁМ:")
    lines.append(protocol.follow_up or "-")
    lines.append("")

    # Дополнительные метаданные
    lines.append(f"Дата отчёта: {protocol.report_date or date.today().isoformat()}")
    lines.append(f"Имя и позиция врача: {header_data.get('doctor_name', '-')} - {header_data.get('doctor_position', '-')}")
    lines.append(f"Медицинское учреждение: {header_data.get('institution', '-')}")
    # сохраняем
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path