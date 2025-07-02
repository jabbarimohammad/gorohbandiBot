import json
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router


API_TOKEN = '594011972:AAFsIRJDeFJNpNBg4mlvXV63nCg_AIVLYhY'  # اینجا توکن واقعی رباتتو بذار

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

DATA_FILE = 'data.json'

# ----------------- ذخیره‌سازی ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"people": [], "selected": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def reset_data():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

# ----------------- کیبوردها ------------------

def build_group_keyboard():
    builder = InlineKeyboardBuilder()
    for i in range(2, 6):
        builder.button(text=f"{i} گروه", callback_data=f"group_{i}")
    builder.adjust(3)
    return builder.as_markup()

def build_selection_keyboard(data):
    builder = InlineKeyboardBuilder()
    for i, person in enumerate(data["people"]):
        selected = "✅" if i in data["selected"] else "❌"
        builder.button(
            text=f"{selected} {person['name']} ({person['score']})",
            callback_data=f"toggle_{i}"
        )
    builder.adjust(1)
    return builder.as_markup()

# ----------------- الگوریتم گروهبندی ------------------

def group_people(people, num_groups):
    groups = [[] for _ in range(num_groups)]
    group_scores = [0] * num_groups
    sorted_people = sorted(people, key=lambda x: -x['score'])

    for person in sorted_people:
        min_index = group_scores.index(min(group_scores))
        groups[min_index].append(person)
        group_scores[min_index] += person['score']

    return groups, group_scores

# ----------------- هندلرها ------------------

@router.message(Command("start"))
async def start(message: Message):
    await message.answer("سلام! افراد رو با فرمت `نام:امتیاز` وارد کن.\n\nبرای انتخاب افراد از دستور /select استفاده کن.")

@router.message(Command("reset"))
async def reset(message: Message):
    reset_data()
    await message.answer("✅ لیست افراد پاک شد.")

@router.message(Command("select"))
async def select(message: Message):
    data = load_data()
    if not data["people"]:
        await message.answer("❗ لیست افراد خالیه.")
        return
    await message.answer("✅ افراد شرکت‌کننده رو انتخاب کن:", reply_markup=build_selection_keyboard(data))

@router.callback_query(F.data.startswith("toggle_"))
async def toggle_selection(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    data = load_data()

    if index in data["selected"]:
        data["selected"].remove(index)
    else:
        data["selected"].append(index)

    save_data(data)
    await callback.message.edit_reply_markup(reply_markup=build_selection_keyboard(data))

@router.message(Command("group"))
async def ask_group_count(message: Message):
    await message.answer("🔢 تعداد گروه‌ها رو انتخاب کن:", reply_markup=build_group_keyboard())

@router.callback_query(F.data.startswith("group_"))
async def group_callback(callback: CallbackQuery):
    num_groups = int(callback.data.split("_")[1])
    data = load_data()

    selected_people = [data["people"][i] for i in data["selected"]]

    if not selected_people:
        await callback.message.answer("❗ هیچ فردی انتخاب نشده.")
        return

    groups, scores = group_people(selected_people, num_groups)

    response = f"👥 تقسیم‌بندی به {num_groups} گروه:\n\n"
    for i, (group, score) in enumerate(zip(groups, scores)):
        response += f"🔹 گروه {i+1} (امتیاز: {score}):\n"
        for p in group:
            response += f"• {p['name']} ({p['score']})\n"
        response += "\n"

    await callback.message.answer(response)

@router.message()
@router.message()
async def add_person(message: Message):
    text = message.text.strip()
    if ':' not in text:
        await message.answer("❌ لطفاً فرمت رو به شکل `نام:امتیاز` وارد کن. مثل:\nعلیرضا:85")
        return

    name, score = text.split(":", 1)
    name = name.strip()
    score = score.strip()

    if not name:
        await message.answer("❌ نام نمی‌تونه خالی باشه.")
        return

    if not score.isdigit():
        await message.answer("❌ امتیاز باید عدد باشه. مثل:\nعلیرضا:85")
        return

    data = load_data()
    data["people"].append({"name": name, "score": int(score)})
    save_data(data)
    await message.answer(f"✅ {name} با امتیاز {score} اضافه شد.")
# ----------------- اجرا ------------------


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
