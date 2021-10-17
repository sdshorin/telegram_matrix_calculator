#!/usr/bin/env python3

import telebot
from  telebot import types 
from matrix import Matrix, MatrixError
from collections import defaultdict
from func_timeout import func_set_timeout, FunctionTimedOut

import random
import time
import datetime
import re

# token from bot @BotFather
import config # store token separatly
bot = telebot.TeleBot(config.TOKEN)

EXAMPLE_MATRIX = [("A", 2, 2),("B", 2, 3), ("C", 3, 4), ("D", 3, 3), ("F", 4, 4), ("L", 2, 4)]

#TODO: USE DATABASE
# Для каждого пользователя храним его матрицы. {<user_id>: {"vars": {"A" = Matrix, "B" = Matrix}}}
user_data = defaultdict(lambda: {"vars": {}})

start_signature = str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

class BotException(BaseException):
	def __init__(self, str_d) -> None:
		self.str = str_d


# на команды /start и /help печатаем readme и выдаем ссылку на исходный код бота
@bot.message_handler(commands=['start', 'help'])
def start_command(message):
	log_message(message)
	keyboard = telebot.types.InlineKeyboardMarkup()
	keyboard.add(
		telebot.types.InlineKeyboardButton(
			"Связаться с разработчиком", url='telegram.me/shorins'
		)
	)
	keyboard.add(
		telebot.types.InlineKeyboardButton(
			"Открыть исходный код бота", url='https://github.com/sdshorin/telegram_matrix_calculator'
		)
	)
	with open("README.md") as f:
		bot.send_message(
			message.chat.id,
			f.read() + f"\nБот запущен в {start_signature}",
			reply_markup=keyboard
		)

# По команде /try создаем несколько случайных матриц заданного размера и содержании
@bot.message_handler(commands=['try'])
def try_command(message):
	log_message(message)
	def create_random_matrix(x, y):
		return Matrix([[random.randrange(-10, 50) for _ in range(x)] for _ in range(y)])
	global user_data
	for matrix_data in EXAMPLE_MATRIX:
		matrix:Matrix = create_random_matrix(*matrix_data[1:])
		user_data[message.from_user.id]["vars"][matrix_data[0]] = matrix
		bot.send_message(message.from_user.id,f"Матрица {matrix_data[0]} добавлена\nРазмер {matrix.size()}\n" + matrix.print_pretty())

# по команде /clear удаляем все сохраненные матрицы пальзователя
@bot.message_handler(commands=['clear'])
def clear_command(message):
	log_message(message)
	global user_data
	user_data[message.from_user.id]["vars"] = {}
	bot.send_message(message.from_user.id, "Все сохраненные матрицы удалены")


# по команде /vars показываем все сохраненные матрицы пальзователя
@bot.message_handler(commands=['vars'])
def vars_command(message):
	log_message(message)
	global user_data
	bot.send_message(message.from_user.id, "Cохраненные матрицы:")
	for name, matrix in user_data[message.from_user.id]["vars"].items():
		send_matrix(message, matrix, name)


# Основной обработчик сообщений
# Если в сообщении есть знак '=' - значит, пользователь хочет создать новую матрицу
# Если сообщение состоит из одного названия матрицы - значит. пользователь хочет ее вывести
# Иначе если в сообщении есть арифметические знаки - его нужно вычислить
@bot.message_handler(content_types=["text"])
def get_text_message(message):
	log_message(message)
	try:
		if message.text.find("=") != -1:
			add_new_var_for_user(message)
		elif is_valid_matrix_name(message.text):
			print_var(message, message.text)
		elif is_expression(message.text):
			matrix = eval_matrix_expression(message, check_expression(message.text))
			send_matrix(message, matrix)
		else:
			bot.send_message(message.from_user.id, "Неизвестная команда! Попробуйте /help")
	except BotException as e:
		bot.send_message(message.from_user.id, e.str)
	except MatrixError as e:
		bot.send_message(message.from_user.id, "MatrixError: " + str(e))
	except FunctionTimedOut as e:
		bot.send_message(message.from_user.id, "TimeOut!")
	except BaseException as e:
		bot.send_message(message.from_user.id, "Unknown error: " + str(e))


def log_message(message):
	log = f"Get message from {message.from_user.last_name} {message.from_user.first_name}. Content: {message.text}"
	print(log)

# Отправить пользователю его матрицу с именем var
def print_var(message, var):
	global user_data
	if not var in user_data[message.from_user.id]["vars"]:
		raise BotException(f"Переменная не найдена.\nБот запущен в {start_signature}")
	matrix: Matrix = user_data[message.from_user.id]["vars"][var]
	send_matrix(message, matrix, var)


def send_matrix(message, matrix, matrix_name = ""):
	if matrix_name:
		bot.send_message(message.from_user.id, f"{matrix_name} =\n{matrix.print_pretty()}")
	else:
		bot.send_message(message.from_user.id, f"{str(matrix.print_pretty())}")	
	

def is_valid_matrix_name(input_str):
	return len(input_str) == 1 and input_str.isupper() and input_str.isascii()

def is_expression(text):
	return "+" in text or "*" in text or "-" in text or "^T" in text


# Создаем или вычисляем новую матрицу
is_only_nums = re.compile('-?\d+$')
def add_new_var_for_user(message):
	global user_data
	new_var_name = message.text.split("=")[0]
	input_data = message.text.split("=")[1].strip()
	new_var_name = new_var_name.strip()
	if not is_valid_matrix_name(new_var_name):
		raise BotException("Некорректное имя переменной. Имя должно быть английской заглавной буквой")
	if not input_data:
		bot.send_message(message.from_user.id, f"Запущен интерактивный режим ввода матрицы. Вводите матрицу построчно, когда закончите - отправьте любое сообщение без чисел")	
		raise BotException("Интерактивный режим находится в разработке")
	if input_data.find("=") != -1:
		raise BotException("В выражении не должно быть знака '='")
	is_pure_matrix = True
	for num in input_data.split():
		if not is_only_nums.match(num):
			is_pure_matrix = False
			break
			# raise BotException(f"Error: matrix can have only natural values! Error in: {num}.")
	if is_pure_matrix:
		# матрица создается из строки
		user_data[message.from_user.id]["vars"][new_var_name] = Matrix(input_data)
		bot.send_message(message.from_user.id,f"Матрица {new_var_name} добавлена")
	else:
		# матрица создается из выражения
		new_matrix: Matrix = eval_matrix_expression(message, check_expression(input_data))
		print("get output: ", type(new_matrix))
		user_data[message.from_user.id]["vars"][new_var_name] = new_matrix
		bot.send_message(message.from_user.id,f"Матрица {new_var_name} добавлена")
		send_matrix(message, new_matrix, new_var_name)


def check_expression(exp):
	if "__" in exp or "for" in exp or "in" in exp:
		raise BotException(f"Недопустимое выражение")
	return exp


# Вычисляем матричное выражение через eval
def eval_matrix_expression(message, expression):
	global user_data
	vars = user_data[message.from_user.id]["vars"]
	expression = expression.replace("^T", ".get_transposd()")
	expression = expression.replace("^-1", ".inverse()")
	# return Matrix(eval(check_expression(expression, vars.keys()), {}, vars))
		# В eval запрещены все встроенные функции, из переменных доступны только матрицы
	output = _eval(expression, vars)
	if isinstance(output, BaseException):
		raise output
	if not isinstance(output, Matrix):
		print("raise:Результат вычисления должен быть матрицей")
		raise BotException(f"Результат вычисления должен быть матрицей")
	return output


@func_set_timeout(0.01)
def _eval(expression, vars):
	try:
		output = eval(expression, {"__builtins__": {}}, vars)
	except BaseException as e:
		output = e
	return output
	


# Альтернативное решение - самостоятельно распарсить сложно выражение перед тем, как использовать eval
# def check_expression(expression: str, valid_vars)-> str:
# 	WAIT_VAR = 0
# 	WAIT_ACTION = 1
# 	WAIT_POSITIVE_INT = 2
# 	status = WAIT_VAR
# 	result_str = ""
# 	expression = expression.strip()
# 	while len(expression):
# 		char = expression[0]
# 		if char.isspace():
# 			expression = expression[1:]
# 			continue
		
# 		if status == WAIT_VAR:
# 			if is_valid_matrix_name(char) and char in valid_vars:
# 				expression = expression[1:]
# 				result_str += char
# 				status = WAIT_ACTION
# 				continue
# 			elif char == "(":
# 				expression = expression[1:]
# 				result_str += char
# 				continue
# 		elif status == WAIT_ACTION:
# 			if char in "+-*":
# 				expression = expression[1:]
# 				result_str += char
# 				status = WAIT_VAR
# 				continue
# 		expression = expression[1:]

				
# Запускаем бота
while True:
	try:
		bot.polling(none_stop = True, interval = 0, timeout=30, long_polling_timeout = 5)
	except Exception as e:
		print(e)
		time.sleep(1)
		continue
	break

