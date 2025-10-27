from typing import Optional, List
import pandas as pd
from pydantic_ai import Agent, Tool, ToolReturn
from pydantic import BaseModel, Field
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from src.core.settings import settings
import asyncio


class AgentOutput(BaseModel):
    mkb_code: str
    name: str
    reason: str = Field(description="Причина выбора данного кода МКБ-10. Пошаговое объяснение от верхнего уровня до конечных деталей")
    
class SimilarAgentOutput(BaseModel):
    exact_answer: Optional[AgentOutput] = Field( description="Точный ответ если был найден детальный код МКБ-10. Или первый из списка похожих если точного нет")
    similar_answers: List[AgentOutput] = Field(description="Список похожих ответов если не был найден точный ответ")
    


def load_mkb():
    return pd.read_csv("mkb10.csv")

def get_mkb_classes() -> ToolReturn:
    """
    Возвращает верхний уровень (классы) — строки, где code длиной == 2.
    Возвращает структурированный ToolReturn: краткий текст, JSON + metadata.
    """
    df = load_mkb()
    filtered = df[df["code"].astype(str).str.len() == 2].copy()

    # Извлекаем код в скобках (например, "A00-B99")
    filtered["mkb_code"] = filtered["name"].str.extract(r"\(([A-Z0-9\-]+)\)")

    # Удаляем лишние колонки
    filtered = filtered.drop(columns=["id", "parent_id", "has_children", "is_active", "version_date"])
    
    data = filtered.to_json(orient="records", force_ascii=False, indent=2)
    
    return ToolReturn(
        return_value=f"Found {len(filtered)} MKB classes.",
        content=[
            "MKB classes (JSON):",
            data
        ],
        metadata={
            "count": len(filtered),
            "level": "classes",
        }
    )
    

def get_mkb_class_blocks(mkb_class_code: int | str) -> ToolReturn:
    """
    Возвращает блоки внутри класса (code длиной == 4 и startswith(mkb_class_code)).
    Пример: mkb_class_code='01' -> вернёт '0101','0102',...
    """
    df = load_mkb()
    filtered = df[
        (df["code"].astype(str).str.len() == 4) &
        (df["code"].astype(str).str.startswith(str(mkb_class_code)))
    ].copy()

    # Извлекаем код в скобках (например, "A00-B99")
    filtered["mkb_code"] = filtered["name"].str.extract(r"\(([A-Z0-9\-]+)\)")

    # Удаляем лишние колонки
    filtered = filtered.drop(columns=["id", "parent_id", "has_children", "is_active", "version_date"])

    data = filtered.to_json(orient="records", force_ascii=False, indent=2)
    
    return ToolReturn(
        return_value=f"Found {len(filtered)} MKB blocks for class: {mkb_class_code}.",
        content=[
            f"MKB class blocks for code {mkb_class_code} (JSON):",
            data
        ],
        metadata={
            "count": len(filtered),
            "level": "blocks",
        }
    )

def get_mkb_class_block_elements(mkb_class_block_code: int | str) -> ToolReturn:
    """
    Возвращает элементы блока (code длиной == 7 и startswith(mkb_class_block_code)).
    Пример: mkb_class_block_code='0101' -> вернёт '0101A00', '0101A01' и т.д. (если в CSV длина == 7).
    """
    df = load_mkb()
    filtered = df[
        (df["code"].astype(str).str.len() == 7) &
        (df["code"].astype(str).str.startswith(str(mkb_class_block_code)))
    ].copy()

    # Удаляем лишние колонки
    filtered = filtered.drop(columns=["id", "parent_id", "has_children", "is_active", "version_date"])

    data = filtered.to_json(orient="records", force_ascii=False, indent=2)
    
    return ToolReturn(
        return_value=f"Found {len(filtered)} elements for block {mkb_class_block_code}.",
        content=[
            f"MKB block elements for {mkb_class_block_code} (JSON):",
            data
        ],
        metadata={
            "count": len(filtered),
            "level": "block_elements",
        }
    )

def get_mkb_class_block_element_details(mkb_class_block_element_code: int | str) -> ToolReturn:
    """
    Возвращает детальные записи дочерних элементов:
    выбирает строки, у которых code длиннее 7 и начинается с mkb_class_block_element_code.
    Пример: mkb_class_block_element_code='0101A00' -> вернёт все '0101A00xxx' и т.д.
    """
    df = load_mkb()
    filtered = df[
        (df["code"].astype(str).str.len() > 7) &
        (df["code"].astype(str).str.startswith(str(mkb_class_block_element_code)))
    ].copy()

    # Удаляем лишние колонки
    filtered = filtered.drop(columns=["id", "parent_id", "has_children", "is_active", "version_date"])

    data = filtered.to_json(orient="records", force_ascii=False, indent=2)
    
    return ToolReturn(
        return_value=f"Found {len(filtered)} detail records for element {mkb_class_block_element_code}.",
        content=[
            f"MKB detail records for element code {mkb_class_block_element_code} (JSON):",
            data
        ],
        metadata={
            "count": len(filtered),
            "level": "details",
        }
    )

model = OpenAIChatModel('gpt-4o-mini', provider=OpenAIProvider(api_key=settings.openai_api_key))

agent = Agent(
    model=model,
    instructions = (
    """
    Инструкция для агента подбора кода МКБ-10.

    Цель
        Найти подходящий код МКБ-10, используя ТОЛЬКО предоставленные функции и данные, и следуя переданным Pydantic-схемам.

    Общие правила
        - Использовать только инструменты: get_mkb_classes(), get_mkb_class_blocks(mkb_class_code),
          get_mkb_class_block_elements(mkb_class_block_code), get_mkb_class_block_element_details(mkb_class_block_element_code).
        - Всегда вызывать функции последовательно: классы → блоки → элементы → детали. Ответы без вызова функций недопустимы.
        - Не придумывать коды и не обращаться к внешним источникам — все решения основывать исключительно на данных, возвращённых функциями.

    Решение о стратегии поиска (когда искать по name, когда по описанию)
        1. Определение, пришёл ли точный диагноз:
            - Считать ввод «точным диагнозом», если текст явно содержит слова/фразы типа: "диагноз", "у меня", "диагностирован(о)", "подтвержден", "назван", или если ввод короткий (примерно ≤ 6 слов) и выглядит как название болезни.
            - В остальных случаях считать ввод описанием симптомов/ситуации (описательный режим).

        2. Поведение в режиме "точный диагноз" (по name):
            - На каждом уровне обхода (классы → блоки → элементы → детали) сравнивать пользовательский ввод с полем name в возвращённых записях.
            - Ищите сначала точные совпадения name (полное равенство или полное вхождение). Если найдено точное совпадение на уровне деталей — это приоритет: выбрать соответствующий детальный код.
            - Если точного совпадения нет — вычислять степени схожести (лексическое совпадение / пересечение ключевых токенов / частичное вхождение) по полю name и собирать до 5 наиболее похожих кандидатов из уровня деталей (или, при их отсутствии, из элементов блока).
        
        3. Поведение в режиме "описание" (по описанию, постепенное сужение):
            - Выделить ключевые слова из описания (симптомы, локализация, ключевые сущности).
            - На уровне классов и блоков фильтровать записи, содержащие эти ключевые слова в поле name; переходить только в релевантные блоки/элементы.
            - На уровне деталей проводить ту же оценку схожести по name и выбирать до 5 лучших кандидатов; если среди деталей есть запись, наиболее соответствующая по словам и формату — считаться предпочтительной.

    Критерий детального (окончательного) кода
        - Признак детального кода: в поле mkb_code присутствует точка '.' и за ней цифра(ы) (например "A15.0"). Такой код является детальным финалом только если он присутствует в результатах get_mkb_class_block_element_details.
        - Если детальных кодов нет для выбранного элемента, допускается считать окончательным код элемента/блока (коды из get_mkb_class_block_elements), при условии что они наиболее релевантны по найденным совпадениям.
        - Всегда проверять наличие детальных записей через get_mkb_class_block_element_details перед тем, как финализировать выбор.

    Выдача результата и пояснения
        - Формирование ответа должно опираться только на данные, полученные функциями.
        - Если найден точный детальный код — предоставить его как основной результат и пояснить выбор в поле reason пошагово: класс → блок → элемент → деталь.
        - Если точного детального кода нет — предоставить набор похожих вариантов (до 5) с коротким объяснением причины выбора каждого (пошагово, от общего к частному).
    """
    ),
    tools=[
        Tool(get_mkb_classes, takes_ctx=False), 
        Tool(get_mkb_class_blocks, takes_ctx=False), 
        Tool(get_mkb_class_block_elements, takes_ctx=False), 
        Tool(get_mkb_class_block_element_details, takes_ctx=False)
    ],
    output_type=SimilarAgentOutput,
)



async def main():
    result = await agent.run(
        "\n ВОПРОС[Доктор сказал что у меня Туберкулез легких, подтвержденный только ростом культуры. Какой у меня может быть код МКБ-10?]"
    )
    print(result.output)
    
if __name__ == "__main__":
    asyncio.run(main())
    
