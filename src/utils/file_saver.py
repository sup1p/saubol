
import os


def create_medical_md(summary_obj, output_dir: str, client: str = "default"):
    
    lines = []
    
    # Создать выходную директорию, если она не существует
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"medical_report_{client}.md"
    output_path = os.path.join(output_dir, filename)

    # Заголовок
    lines.append("# Медицинский отчет о состоянии пациента - SAUBOL AI\n")

    # Секция заголовка
    lines.append("## 1. Заголовок")
    lines.append(f"- **Дата отчета:** {summary_obj.report_date or '-'}")
    lines.append(f"- **Полное имя врача:** {summary_obj.doctor_name or '-'}")
    lines.append(f"- **Должность:** {summary_obj.doctor_position or '-'}")
    lines.append(f"- **Медицинское учреждение:** {summary_obj.institution or '-'}\n")

    # Данные пациента
    lines.append("## 2. Данные пациента")
    lines.append(f"- **Полное имя:** {summary_obj.patient_name or '-'}")
    lines.append(f"- **Возраст / Пол:** {summary_obj.age_sex or '-'}")
    lines.append(f"- **Дата поступления / посещения:** {summary_obj.admission_date or '-'}")
    lines.append(f"- **Номер медицинской записи:** {summary_obj.record_number or '-'}\n")

    # Жалобы
    lines.append("## 3. Жалобы пациента")
    lines.append((summary_obj.complaints or '-') + "\n")

    # История настоящего заболевания
    lines.append("## 4. История настоящего заболевания")
    lines.append((summary_obj.present_illness or '-') + "\n")

    # Прошлая медицинская история
    lines.append("## 5. Прошлая медицинская история")
    lines.append((summary_obj.past_history or '-') + "\n")

    # Объективное обследование
    lines.append("## 6. Объективное обследование")
    lines.append((summary_obj.examination or '-') + "\n")

    # Диагноз
    lines.append("## 7. Диагноз")
    lines.append((summary_obj.diagnosis or '-') + "\n")

    # Лечение
    lines.append("## 8. Лечение и назначения")
    lines.append((summary_obj.treatment or '-') + "\n")

    # Прогноз
    lines.append("## 9. Прогноз")
    lines.append((summary_obj.prognosis or '-') + "\n")

    # Сохранение в .md
    md_content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Файл Markdown создан: {output_path}")