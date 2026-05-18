import os
import mimetypes
from dotenv import load_dotenv

load_dotenv()

# 🔥 ВСТАВЬ СВОЙ КЛЮЧ СЮДА (между кавычками) 🔥
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBBOnDtRCFguJLZ9E_ouCImBLnRdEH0FAo")


def generate_ai_description(prompt: str) -> str:
    """Генерация описания задачи с помощью Google Gemini"""
    if not API_KEY or API_KEY == "ТВОЙ_КЛЮЧ_СЮДА":
        return (f"🤖 Gemini: Отлично! Вот подробное описание задачи по запросу «{prompt}»:\n\n"
                f"**Цель задачи:**\nСоздать/выполнить {prompt} на высоком уровне качества.\n\nГотово к публикации! 🚀")

    try:
        # ИСПОЛЬЗУЕМ НОВУЮ БИБЛИОТЕКУ
        from google import genai
        client = genai.Client(api_key=API_KEY)
        
        system_prompt = (
            f"Ты — опытный Project Manager и технический писатель. Твоя задача: превратить короткую идею в идеальное, профессиональное ТЗ (техническое задание) для фриланс-биржи. Тема: {prompt}\n\n"
            "Если в идее не хватает деталей, самостоятельно додумай логичные требования, стек технологий и этапы, чтобы задача выглядела полноценной.\n\n"
            "Строго используй следующую структуру (с Markdown-разметкой для красоты):\n"
            "### 🎯 Суть задачи\n"
            "[Краткое и привлекательное описание того, что нужно сделать]\n\n"
            "### 📋 Пошаговый план работ\n"
            "[Маркированный список конкретных шагов]\n\n"
            "### 🛠 Требования к исполнителю\n"
            "[Стек технологий, навыки, пожелания к опыту]\n\n"
            "### ✅ Ожидаемый результат (Критерии приемки)\n"
            "[Что именно должно быть передано заказчику в конце]\n\n"
            "КРИТИЧЕСКИ ВАЖНО: Твой ответ будет напрямую скопирован на сайт. НЕ пиши никаких приветствий, пояснений или фраз вроде 'Вот ваше ТЗ'. Выдай ТОЛЬКО сам текст задания."
        )
        
        # Вызываем самую новую модель 2.5
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt
        )
        
        ai_text = response.text.strip()
        return f"🤖 Gemini ответил:\n\n{ai_text}"
        
    except Exception as e:
        print(f"Ошибка Gemini: {e}")
        return (f"🤖 Gemini: Отлично! Вот подробное описание задачи по запросу «{prompt}»:\n\n"
                f"**Цель задачи:**\nСоздать/выполнить {prompt} на высоком уровне качества.\n\nГотово к публикации! 🚀")


def recognize_file_content(filepath: str) -> str:
    """Распознавание текста из файлов (OCR)"""
    if not API_KEY or API_KEY == "ТВОЙ_КЛЮЧ_СЮДА":
        return "Ошибка: Вы забыли вставить ключ API Gemini в файл utils.py."
        
    try:
        # ИСПОЛЬЗУЕМ НОВУЮ БИБЛИОТЕКУ
        from google import genai
        client = genai.Client(api_key=API_KEY)
        
        prompt = "Твоя задача — выступить в роли OCR сканера. Внимательно изучи этот файл и извлеки из него весь текст. Выведи ТОЛЬКО распознанный текст, сохраняя оригинальные абзацы и пунктуацию. Никаких приветствий, просто выдай текст."
        
        ext = filepath.rsplit('.', 1)[-1].lower() if '.' in filepath else ''
        
        if ext in ['png', 'jpg', 'jpeg']:
            from PIL import Image
            img = Image.open(filepath)
            if img.mode in ("RGBA", "P"): 
                img = img.convert("RGB")
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[img, prompt]
            )
            return response.text.strip()
            
        elif ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[f"Вот текст файла:\n{text_content}\n\n", prompt]
            )
            return response.text.strip()
            
        else:
            # Загрузка PDF через новый File API
            gemini_file = client.files.upload(file=filepath)
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[gemini_file, prompt]
            )
            
            # Удаляем файл с серверов
            client.files.delete(name=gemini_file.name)
            return response.text.strip()
            
    except Exception as e:
        return f"Критическая ошибка нейросети при распознавании файла: {e}"