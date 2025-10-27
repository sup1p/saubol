from src.schemas.protocol import MedicalProtocol
from typing import List 
import os
from datetime import date
    
    
# def save_protocol_as_txt(protocol: MedicalProtocol, output_dir: str, header_data: dict,client: str = "default") -> str:
#     os.makedirs(output_dir, exist_ok=True)
#     filename = f"medical_protocol_{client}.txt"
#     output_path = os.path.join(output_dir, filename)

#     lines: List[str] = []
#     lines.append("МЕДИЦИНСКИЙ ПРОТОКОЛ")
#     lines.append("Форма утверждена МЗ РК")
#     lines.append("")

#     # Жалобы
#     lines.append("ЖАЛОБЫ:")
#     lines.append(protocol.complaints or "-")
#     lines.append("")

#     # Анамнез заболевания
#     lines.append("АНАМНЕЗ ЗАБОЛЕВАНИЯ:")
#     lines.append(protocol.history_of_disease or "-")
#     lines.append("")

#     # Анамнез жизни
#     lines.append("АНАМНЕЗ ЖИЗНИ:")
#     lh = protocol.life_history
#     if lh:
#         lines.append(f"- Наследственность: {lh.heredity or '-'}")
#         lines.append(f"- Аллергологический анамнез: {lh.allergy_history or '-'}")
#         lines.append(f"- Хронические заболевания: {lh.chronic_diseases or '-'}")
#         lines.append(f"- Приём медикаментов: {lh.medications or '-'}")
#     else:
#         lines.append("- -")
#     lines.append("")

#     # Объективный статус
#     lines.append("ОБЪЕКТИВНЫЙ СТАТУС:")
#     os_stat = protocol.objective_status
#     if os_stat:
#         lines.append(f"Общее состояние: {os_stat.general_condition or '-'}")
#         lines.append(f"Сознание: {os_stat.consciousness or '-'}")
#         lines.append(f"Кожные покровы: {os_stat.skin or '-'}")
#         if os_stat.signs:
#             lines.append("Неврологический статус:")
#             for s in os_stat.signs:
#                 lines.append(f"- {s}")
#         else:
#             # сохранить краткое упоминание признаков, если focal_symptoms содержит текст
#             if os_stat.focal_symptoms:
#                 lines.append("Неврологический статус:")
#                 lines.append(f"- {os_stat.focal_symptoms}")
#             else:
#                 lines.append("-")
#     else:
#         lines.append("-")
#     lines.append("")

#     # Предварительный диагноз
#     lines.append("ПРЕДВАРИТЕЛЬНЫЙ ДИАГНОЗ:")
#     lines.append(protocol.preliminary_diagnosis or "-")
#     lines.append("")

#     # План обследования
#     lines.append("ПЛАН ОБСЛЕДОВАНИЯ:")
#     if protocol.investigation_plan:
#         for i, item in enumerate(protocol.investigation_plan, start=1):
#             lines.append(f"{i}. {item}")
#     else:
#         lines.append("-")
#     lines.append("")

#     # План лечения
#     lines.append("ПЛАН ЛЕЧЕНИЯ:")
#     if protocol.treatment_plan:
#         for i, item in enumerate(protocol.treatment_plan, start=1):
#             lines.append(f"{i}. {item}")
#     else:
#         lines.append("-")
#     lines.append("")

#     # Рекомендации пациенту
#     lines.append("РЕКОМЕНДАЦИИ ПАЦИЕНТУ:")
#     if protocol.patient_recommendations:
#         for rec in protocol.patient_recommendations:
#             lines.append(f"- {rec}")
#     else:
#         lines.append("-")
#     lines.append("")

#     # Назначения
#     lines.append("НАЗНАЧЕНИЯ:")
#     if protocol.prescriptions:
#         for p in protocol.prescriptions:
#             qty = f" №{p.quantity}" if p.quantity else ""
#             dosage = f" {p.dosage}" if p.dosage else ""
#             instr = f"\nСпособ применения: {p.instructions}" if p.instructions else ""
#             lines.append(f"{p.name}{dosage}{qty}{instr}")
#     else:
#         lines.append("-")
#     lines.append("")

#     # Контроль / повторный приём
#     lines.append("КОНТРОЛЬ / ПОВТОРНЫЙ ПРИЁМ:")
#     lines.append(protocol.follow_up or "-")
#     lines.append("")

#     # Дополнительные метаданные
#     lines.append(f"Дата отчёта: {protocol.report_date or date.today().isoformat()}")
#     lines.append(f"Имя и позиция врача: {header_data.get('doctor_name', '-')} - {header_data.get('doctor_position', '-')}")
#     lines.append(f"Медицинское учреждение: {header_data.get('institution', '-')}")
#     # сохраняем
#     with open(output_path, "w", encoding="utf-8") as f:
#         f.write("\n".join(lines))

#     return output_path



def _sex_label(s: str | None) -> str:
    if s == 'M':
        return 'мужской'
    if s == 'F':
        return 'женский'
    if s == 'other':
        return 'другой'
    return '-'

def _format_bp(bp_obj) -> str:
    # bp_obj может быть экземпляром BP, dict или None
    if not bp_obj:
        return "-"
    try:
        syst = getattr(bp_obj, "systolic", None) or bp_obj.get("systolic")
        dias = getattr(bp_obj, "diastolic", None) or bp_obj.get("diastolic")
        if syst is None and dias is None:
            return "-"
        return f"{syst}/{dias} мм рт. ст."
    except Exception:
        return "-"

def _format_vital(vitals: dict, key: str, default="-") -> str:
    if not vitals:
        return default
    val = vitals.get(key)
    if val is None:
        return default
    # если значение — словарь/объект с value/unit
    if isinstance(val, dict):
        v = val.get("value") or val.get("val") or None
        u = val.get("unit") or ""
        return f"{v} {u}".strip()
    return str(val)

def save_protocol_as_txt(protocol: MedicalProtocol, output_dir: str, header_data: dict, client: str = "default") -> str:
    """
    Сохраняет объект MedicalProtocol в текстовый файл формата медицинского протокола.
    Возвращает путь к файлу.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"medical_protocol_{client}.txt"
    output_path = os.path.join(output_dir, filename)

    lines: List[str] = []

    # Заголовок / шапка пациента
    p = protocol.patient
    lines.append("Ф.И.О. пациента: " + (p.full_name or "______________________"))
    age_str = str(p.age) if p and p.age is not None else "-"
    lines.append("Возраст: " + age_str)
    lines.append("Пол: " + _sex_label(p.sex if p else None))
    lines.append("Дата осмотра: " + ((p.date_of_exam.isoformat()) if (p and p.date_of_exam) else "______________________"))
    lines.append("")

    # Жалобы
    lines.append("Жалобы:")
    if protocol.chief_complaints:
        for cc in protocol.chief_complaints:
            # используем формализованный текст, но если есть raw_text — добавляем как уточнение
            text = cc.text if getattr(cc, "text", None) else (cc.raw_text or "-")
            lines.append(text)
            if getattr(cc, "raw_text", None) and cc.raw_text != cc.text:
                lines.append(f"(Исходная фраза: {cc.raw_text})")
    else:
        lines.append("-")
    lines.append("")

    # Анамнез заболевания
    lines.append("Анамнез заболевания:")
    if protocol.anamnesis_morbi and getattr(protocol.anamnesis_morbi, "text", None):
        lines.append(protocol.anamnesis_morbi.text)
    else:
        lines.append("-")
    lines.append("")

    # Анамнез жизни
    lines.append("Анамнез жизни:")
    av = protocol.anamnesis_vitae
    if av:
        # если есть свободный текст — вывести
        if av.text:
            # разбить на строки, если длинный
            lines.extend([ln for ln in av.text.splitlines() if ln.strip()])
        else:
            # попытаться вывести структурированные поля
            disp = av.dispensary_register_status or "unknown"
            lines.append(f"- Диспансерный учёт: {disp}")
            lines.append(f"- Аллергии: {', '.join(av.allergies) if av.allergies else 'не отмечены'}")
            lines.append(f"- Хронические заболевания: {', '.join(av.chronic_diseases) if av.chronic_diseases else 'не выявлены'}")
    else:
        lines.append("-")
    lines.append("")

    # Объективный статус
    lines.append("Объективный статус:")
    os_stat = protocol.objective_status
    if os_stat:
        # краткое резюме
        if os_stat.summary:
            lines.append(os_stat.summary)
        # витальные
        vitals = os_stat.vitals or {}
        #температура, пульс, давление
        temp = _format_vital(vitals, "temperature")
        pulse = _format_vital(vitals, "pulse")
        bp_repr = _format_bp(vitals.get("bp") or vitals.get("blood_pressure") or vitals.get("pressure"))
        if temp != "-" or pulse != "-" or bp_repr != "-":
            if temp != "-":
                lines.append(f"Температура тела: {temp}")
            if pulse != "-":
                lines.append(f"Пульс: {pulse} уд/мин")
            if bp_repr != "-":
                lines.append(f"Артериальное давление: {bp_repr}")
        # другие находки
        if os_stat.other_findings:
            for f in os_stat.other_findings:
                lines.append(f"- {f.text}")
    else:
        lines.append("-")
    lines.append("")

    # Status localis (локальный осмотр)
    if protocol.status_localis:
        lines.append("Status localis:")
        for region in protocol.status_localis:
            lines.append(region.region + ":")
            if region.findings:
                for ff in region.findings:
                    lines.append(ff.text)
            else:
                lines.append("-")
            lines.append("")  # разделитель между регионами
    else:
        # если нет — не обязательно, но добавим пустой блок
        lines.append("Status localis:")
        lines.append("-")
        lines.append("")

    # Предварительный диагноз
    lines.append("Предварительный диагноз (по МКБ-10):")
    if protocol.preliminary_diagnosis:
        for pd in protocol.preliminary_diagnosis:
            icd = f" — {pd.icd10}" if getattr(pd, "icd10", None) else ""
            certainty = f" (уверенность: {pd.certainty})" if getattr(pd, "certainty", None) else ""
            lines.append(f"{pd.text}{icd}{certainty}")
            if getattr(pd, "rationale", None):
                lines.append(f"Обоснование: {pd.rationale}")
    else:
        lines.append("-")
    lines.append("")

    # Дифференциальный диагноз
    lines.append("Дифференциальный диагноз:")
    if protocol.differential_diagnosis:
        for i, dd in enumerate(protocol.differential_diagnosis, start=1):
            icd = f" — {dd.icd10}" if getattr(dd, "icd10", None) else ""
            lines.append(f"    {i}. {dd.text}{icd}")
    else:
        lines.append("-")
    lines.append("")

    # План обследования
    lines.append("План обследования:")
    if protocol.plan_investigations:
        # отсортируем по полю order на всякий случай
        for item in sorted(protocol.plan_investigations, key=lambda x: getattr(x, "order", 0)):
            notes = f": {item.notes}" if getattr(item, "notes", None) else ""
            lines.append(f"    {item.order}. {item.test}{notes}")
    else:
        lines.append("-")
    lines.append("")

    # План лечения
    lines.append("План лечения:")
    if protocol.plan_treatment:
        for item in sorted(protocol.plan_treatment, key=lambda x: getattr(x, "order", 0)):
            parts = [item.treatment]
            if item.dose:
                parts.append(item.dose)
            if item.route:
                parts.append(f"({item.route})")
            if item.freq:
                parts.append(f", {item.freq}")
            if item.duration:
                parts.append(f", {item.duration}")
            lines.append(f"    {item.order}. " + " ".join(str(p) for p in parts if p))
    else:
        lines.append("-")
    lines.append("")

    # Рекомендации
    lines.append("Рекомендации:")
    if protocol.recommendations:
        for r in sorted(protocol.recommendations, key=lambda x: getattr(x, "order", 0)):
            lines.append(f"    {r.order}. {r.text}")
    else:
        lines.append("-")
    lines.append("")

    # Прогноз
    lines.append("Прогноз:")
    if protocol.prognosis and getattr(protocol.prognosis, "text", None):
        prog = protocol.prognosis
        cat = f" ({prog.category})" if getattr(prog, "category", None) else ""
        lines.append(prog.text + cat)
    else:
        lines.append("-")
    lines.append("")

    # Подпись врача / авторство
    lines.append("Врач-ординатор / Специалист: " + (protocol.sign_off.doctor_name if protocol.sign_off and protocol.sign_off.doctor_name else header_data.get("doctor_name", "-")))
    if protocol.sign_off and getattr(protocol.sign_off, "specialty", None):
        lines.append("Специальность: " + protocol.sign_off.specialty)
    elif header_data.get("doctor_position"):
        lines.append("Специальность: " + header_data.get("doctor_position"))
    if protocol.sign_off and getattr(protocol.sign_off, "experience_years", None) is not None:
        lines.append(f"Стаж работы: {protocol.sign_off.experience_years} лет")
    else:
        if header_data.get("doctor_experience_years") is not None:
            lines.append(f"Стаж работы: {header_data.get('doctor_experience_years')}")
    # подпись (если требуется)
    sig_required = (protocol.sign_off.signature_required if protocol.sign_off is not None else True)
    lines.append("Подпись: " + ("_____________" if sig_required else "(не требуется)"))
    lines.append("")

    # Запись в файл
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path