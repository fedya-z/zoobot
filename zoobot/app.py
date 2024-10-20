import telebot
from telebot import types
import os
from conflig import questions, TOKEN, animal_mapping, animal_images, image_folder

bot = telebot.TeleBot(TOKEN)

user_data = {}


@bot.message_handler(commands=["help"])
def help(message: telebot.types.Message):
    text = '''Вы попали в викторину от московского зоопарка! 
Ответив на несколько вопросов вы узнаете своё тотемное животное и сможете помочь ему в реальной жизни. 
Подробнее о нашем зоопарке можно узнать на <a href="https://www.moscowzoo.ru">сайте Московского зоопарка</a> и в <a href="https://t.me/Moscowzoo_official">telegram-канале</a>.
Ну чтож начнём!: /start.'''
    bot.reply_to(message, text, parse_mode='HTML')


@bot.message_handler(commands=["start"])
def start(message: telebot.types.Message):
    text = "Наш зоопарк полон различных животных, но ответив на следующие вопросы вы найдете именно ваше тотемное животное! Для начала давайте знакомиться, как вас зовут?"
    bot.reply_to(message, text)
    bot.register_next_step_handler(message, get_name)


def get_name(message: telebot.types.Message):
    name = message.text
    user_data[message.chat.id] = {"name": name, "answers": []}
    text = f"Приятно познакомиться, {name}! Теперь давайте перейдем к вопросам викторины."
    bot.reply_to(message, text)
    ask_question(message, 0)


def ask_question(message: telebot.types.Message, question_index: int):
    if question_index < len(questions):
        question_text = questions[question_index]["question"]
        options = questions[question_index]["options"]
        options_text = "\n".join([f"{i + 1}. {option}" for i, option in enumerate(options)])
        bot.reply_to(message, f"{question_text}\n{options_text}")
        bot.register_next_step_handler(message, handle_answer, question_index)
    else:
        calculate_totem_animal(message)


def handle_answer(message: telebot.types.Message, question_index: int):
    try:
        answer_index = int(message.text) - 1
        if answer_index < 0 or answer_index >= len(questions[question_index]["options"]):
            raise ValueError
        answer = questions[question_index]["options"][answer_index]
        user_data[message.chat.id]["answers"].append(answer)
        ask_question(message, question_index + 1)
    except (ValueError, IndexError):
        bot.reply_to(message, "Пожалуйста, выберите корректный вариант ответа (введите число от 1 до 4).")
        bot.register_next_step_handler(message, handle_answer, question_index)


def calculate_totem_animal(message: telebot.types.Message):
    answers = user_data[message.chat.id]["answers"]
    animal_counts = {}

    for answer in answers:
        animal = animal_mapping.get(answer)
        if animal:
            if animal in animal_counts:
                animal_counts[animal] += 1
            else:
                animal_counts[animal] = 1

    totem_animal = max(animal_counts, key=animal_counts.get)
    name = user_data[message.chat.id]["name"]


    caption = (f"{name}, ваше тотемное животное: {totem_animal}!\n"
               "Вот мы и выяснили ваше тотемное животное. "
               "Поддержать его вы можете на <a href='https://www.moscowzoo.ru'>сайте Московского зоопарка</a> "
               "и в <a href='https://t.me/Moscowzoo_official'>telegram-канале</a>.")


    animal_image_filename = animal_images.get(totem_animal)
    if animal_image_filename:
        animal_image_path = os.path.join(image_folder, animal_image_filename)
        with open(animal_image_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo, caption=caption, parse_mode='HTML')


    markup = types.InlineKeyboardMarkup()
    start_again_button = types.InlineKeyboardButton("Начать заново", callback_data="start_again")
    markup.add(start_again_button)


    bot.send_message(message.chat.id, "Хотите начать викторину заново?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "start_again")
def start_quiz_again(call):
    bot.answer_callback_query(call.id, "Начинаем заново!")
    start(call.message)


bot.polling(none_stop=True)
