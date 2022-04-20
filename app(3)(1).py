# libraries for bot

import telebot
from telebot import types
import sqlite3
import math
import sys
from io import BytesIO
import requests
from PIL import Image
from pay import creatpay
from pay import p2p


global p2p

# TOKEN for bot

token = "1797939131:AAE6kEgIOXmH5FFLEG8_hznXacgyid9BiTg"
bot = telebot.TeleBot(token)

def useraphone(message, whophone):
    mydb = sqlite3.connect('base.db')
    mycursor = mydb.cursor()
    if whophone == 'taxi':
        mycursor.execute(f'SELECT phone FROM taxi_drivers WHERE teg_id = {message.chat.id}')      
        taxi = mycursor.fetchone()
        return taxi[0]
    else:
        mycursor.execute(f'SELECT phone FROM passengers WHERE teg_id = {message.chat.id}')      
        passengers = mycursor.fetchone()
        return passengers[0]


def passmenu(message):
    buttons_actions = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_history_ways = types.KeyboardButton(text="Мои поездки")
    button_add_order = types.KeyboardButton(text="Новая поездка")
    button_settings = types.KeyboardButton(text="Настройки")
    buttons_actions.add(button_history_ways)
    buttons_actions.add(button_add_order)
    buttons_actions.add(button_settings)
    bot.send_message(message.chat.id, "Выберите действие.", reply_markup=buttons_actions)


def taximenu(message):
    buttons_actions = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_settings = types.KeyboardButton(text="Настройки")
    button_choose_order = types.KeyboardButton(text="Выбрать поездку")
    button_choose_balance = types.KeyboardButton(text="Баланс")
    button_choose_paybalance = types.KeyboardButton(text="Пополнить баланс")
    
    buttons_actions.add(button_choose_order)
    buttons_actions.add(button_choose_balance)
    buttons_actions.add(button_choose_paybalance)
    buttons_actions.add(button_settings)
    bot.send_message(message.chat.id, "Выберите действие.", reply_markup=buttons_actions)

def menunast(message):
    buttons_actions = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button_choose_taxi = types.KeyboardButton(text="Сменить роль")
    button_choose_back = types.KeyboardButton(text="Назад")
    
    buttons_actions.add(button_choose_taxi)
    buttons_actions.add(button_choose_back)

    bot.send_message(message.chat.id, "Выберите действие.", reply_markup=buttons_actions)




def reg_or_auth(message):
    try:
        # user phone
        input_phone = message.contact.phone_number

        # connect to base
        mydb = sqlite3.connect('base.db')
        mycursor = mydb.cursor()
    
        buttons_characters = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_taxi_driver = types.KeyboardButton(text="Таксист")
        button_passenger = types.KeyboardButton(text="Пассажир")
        buttons_characters.add(button_taxi_driver)
        buttons_characters.add(button_passenger)
        mess = bot.send_message(message.chat.id, "Выберите кем вы являетесь?", reply_markup=buttons_characters)
        bot.register_next_step_handler(mess, choose_character, input_phone)      
    
    except:
        mess = bot.send_message(message.chat.id, "Ошибка. Отправьте номер телефона!")
        bot.register_next_step_handler(mess, reg_or_auth)

def geo_location(message, phone, job, firm=None, car_numbers=None, src_photo_car=None):   # firm and car_numbers if taxi, default passenger
                     
        mydb = sqlite3.connect('base.db')
        mycursor = mydb.cursor()
        
        if job == 'Таксист':
            c = 0
            mycursor.execute(f'SELECT * FROM taxi_drivers')
            taxi_drivers = mycursor.fetchall()
            for driver in taxi_drivers:
                if driver[1] != phone:
                    c += 1
            if c == len(taxi_drivers):
                    
                sqlFormula = "INSERT INTO taxi_drivers ('phone', 'machine_firm', 'car_numbers', 'photo_car', 'teg_id', 'Balance') VALUES (?,?,?,?,?,?)"
                mycursor.execute(sqlFormula, (phone, firm, car_numbers, src_photo_car, message.chat.id, 0))
                mydb.commit()

                mydb = sqlite3.connect('base.db')
                mycursor = mydb.cursor()

            mycursor.execute(f'SELECT * FROM orders WHERE phone != 0')
            orders = mycursor.fetchall()                 
            if str(orders) == "[]":
                bot.send_message(message.chat.id, "Заказы не найдены")
                taximenu(message)
            else:
                for us in orders:
                    user = us
                        
                    first_checkpoint = user[2] # start address
                    second_checkpoint = user[3]   # end address
                    bot.send_message(message.chat.id, f"<i><b>Заказ №{user[0]}.</b></i>\n\n<i><b>Начальная точка:</b></i> {first_checkpoint}\n\n<i><b>Конечная точка:</b></i> {second_checkpoint}\n\n<b>Цена:</b> {user[4]} ₽", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
                
                
            
                
                mess = bot.send_message(message.chat.id, "Введите номер заказа.", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(mess, choose_order)

         
        elif job == 'Пассажир':
            mess = bot.send_message(message.chat.id, "<b>Отправьте адрес.</b>", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(mess, where_go, phone, message.text)

def choose_character(message, user_phone):
    if message.text == 'Таксист':
        mess = bot.send_message(message.chat.id, "Введите марку машины.", reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(mess, machine_firm, user_phone)
        
        
    elif message.text == 'Пассажир':
        
        # connect to base
        mydb = sqlite3.connect('base.db')
        mycursor = mydb.cursor()
            
        # Add new passenger in 'passengers' table
        sqlFormula = "INSERT INTO passengers ('phone', 'teg_id') VALUES (?,?)"
        mycursor.execute(sqlFormula, (user_phone, message.chat.id))
        mydb.commit()
        
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        passmenu(message)


def machine_firm(message, phone):
    firm = message.text
    mess = bot.send_message(message.chat.id, "Введите номера машины.", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(mess, car_numbers, phone, firm)

    

def car_numbers(message, phone, machine_firm):          
    car_numbers = message.text
    
    mess = bot.send_message(message.chat.id, "Отправьте фото машины.")    
    bot.register_next_step_handler(mess, handle_docs_photo, car_numbers, phone, machine_firm)



def handle_docs_photo(message, car_numbers, phone, machine_firm):
    try:
        chat_id = message.chat.id

        file_info = bot.get_file(message.photo[0].file_id)
        
        downloaded_file = bot.download_file(file_info.file_path)

        src = 'photo_cars/' + car_numbers + '.png';     # save png photo name - car_numbers
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
    
        geo_location(message, phone, 'Таксист', firm=machine_firm, car_numbers=car_numbers, src_photo_car=src)
    except Exception as err:
        menu(message)
        print(err)
    

def payfunc(message):
    global kolvokg
    kolvokg = message.text
    comment = message.chat.id
    global link
    link = creatpay(kolvokg, comment)
    proverka = types.InlineKeyboardMarkup(row_width=5)
    item1 = types.InlineKeyboardButton('Проверка оплаты', callback_data='prov')
    proverka.add(item1)

    bot.send_message(message.chat.id, f"Для оплаты перейдите по ссылке: {link.pay_url}", reply_markup=proverka)

def prover(message):
    status = p2p.check(bill_id=link.bill_id).status
    if status == 'PAID': # Если статус счета оплачен (PAID)
       print("Оплата прошла успешно")

       bot.delete_message(message.chat.id, message.message_id)
       bot.send_message(message.chat.id, f"Оплата прошла успешно!")

       mydb = sqlite3.connect('base.db')
       mycursor = mydb.cursor()
    
       mycursor.execute(f'UPDATE taxi_drivers SET Balance = {kolvokg} WHERE teg_id={message.chat.id}')
       mydb.commit()
    else:
        bot.send_message(message.chat.id, f"Оплата не прошла!")





def choose_order(message):
   # num order
    if message.text.isdigit():
        num_order = message.text
        mydb = sqlite3.connect('base.db')
        mycursor = mydb.cursor()

        mycursor.execute(f'SELECT Balance FROM taxi_drivers WHERE teg_id={message.chat.id}')
        balance = mycursor.fetchone()
        
        mycursor.execute(f'SELECT id FROM orders WHERE id = {num_order}')
        ordur = mycursor.fetchone()
        if ordur is None:
            bot.send_message(message.chat.id, "Нет такого заказа")
            taximenu(message)
        else:
             mycursor.execute(f'SELECT * FROM orders WHERE id = {num_order} AND phone != 0')
             orders = mycursor.fetchall()                         
             priceten = float(orders[0][4]) * 0.1
             if balance[0] >= int(priceten):

                 mycursor.execute(f'UPDATE taxi_drivers SET Balance = {balance[0] - int(priceten)} WHERE teg_id={message.chat.id}')
                 mydb.commit()


                 first_checkpoint = orders[0][2]  # start address
                 second_checkpoint = orders[0][3]  # end address

                 proverka = types.InlineKeyboardMarkup(row_width=5)
                 item1 = types.InlineKeyboardButton('Я подъехал!', callback_data=f'go{num_order}')
                 proverka.add(item1)
                
                 

                 bot.send_message(message.chat.id, f"<i><b>Номер пассажира: {orders[0][1]}.</b></i>\n\n<i><b>Начальная точка:</b></i> {first_checkpoint}\n\n<i><b>Конечная точка:</b></i> {second_checkpoint}\n\n<b>Цена:</b> {orders[0][4]} ₽", parse_mode='HTML', reply_markup=proverka)
                    
                    
                   
                    
                   
                 mycursor.execute(f'SELECT * FROM taxi_drivers WHERE teg_id={message.chat.id}')
                 user_taxi = mycursor.fetchall()
                 src_photo_car = user_taxi[0][4]                    # src_photo_car                                       
                    
                 bot.send_photo(orders[0][-1], open(src_photo_car, 'rb'));
                 mycursor.execute(f'UPDATE orders SET phone = 0 WHERE id={num_order}')
                 mydb.commit()
                 
                 
                   # passenger[0][-1] - teg_id user
                
             else:
                 bot.send_message(message.chat.id, f"Недостаточно средств, пожалуйста пополните ваш баланс на {priceten - balance[0]} рублей ")
                 taximenu(message)
                  
                         
    else:
        bot.send_message(message.chat.id, "Ошибка! Вы должны отправить число!")
        taximenu(message)
    
    

def where_go(message, phone, address_start):
    
    
   # end address for passenger
    address_end = message.text
    mess = bot.send_message(message.chat.id, "<b>Укажите желаемую цену в ₽.</b>", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(mess, price_way, phone, address_start, address_end)
   
    
def price_way(message, phone, address_start, address_end):   # end address for passenger
	try:
			   	
		price_way = int(message.text)
    
    

		bot.send_message(message.chat.id, f"<i><b>Ваш заказ.</b></i>\n\n<i><b>Начальная точка:</b></i> <b>{address_start}\n\nКонечная точка: {address_end}\n\n  Цена:</b> {price_way} ₽", parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
		mydb = sqlite3.connect('base.db')
		mycursor = mydb.cursor()
		sqlFormula = "INSERT INTO orders ('phone', 'address_start', 'address_end', 'price', 'teg_id') VALUES (?,?,?,?,?)"
		mycursor.execute(sqlFormula, (phone, address_start, address_end, price_way, message.chat.id))
		mydb.commit()
		passmenu(message)
		for a in mycursor.execute("SELECT Count(teg_id) FROM taxi_drivers"):
		  taxist = a[0]
		  i = 1
		  for b in range(taxist):
		           for ab in mycursor.execute(f"SELECT teg_id FROM taxi_drivers WHERE id = {i}"):
		           	user_taxi = ab[0]
		           	bot.send_message(user_taxi, "Добавлен новый заказ")
		           	i = i + 1
      	 


	except:
		bot.send_message(message.chat.id, "Ошибка!")
		passmenu(message)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, "Вопросы, жалобы предложения: @antowwa")

@bot.message_handler(commands=["menu"])
def menu(message):
    start(message)

@bot.message_handler(commands=["start"])
def start(message):
    mydb = sqlite3.connect('base.db')
    mycursor = mydb.cursor()
    name = message.text
    mycursor.execute(f'SELECT teg_id FROM passengers WHERE teg_id = {message.chat.id}')      
    data = mycursor.fetchone()

    mycursor.execute(f'SELECT teg_id FROM taxi_drivers WHERE teg_id = {message.chat.id}')      
    datatwo = mycursor.fetchone()



    if data is None and datatwo is None:
        bot.send_message(message.chat.id, "Привет <b>{first_name}</b>, рад тебя видеть. Пожалуйста, отправьте мне свой номер для этого есть команда /phone".format(first_name=message.from_user.first_name), parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
    else:
        if data is None:
            taximenu(message)
        else:
            passmenu(message)
    

@bot.message_handler(commands=["phone"])
def phone(message):
    mydb = sqlite3.connect('base.db')
    mycursor = mydb.cursor()

    mycursor.execute(f'SELECT teg_id FROM passengers WHERE teg_id = {message.chat.id}')      
    data = mycursor.fetchone()

    mycursor.execute(f'SELECT teg_id FROM taxi_drivers WHERE teg_id = {message.chat.id}')      
    datatwo = mycursor.fetchone()

    if data is None and datatwo is None:
        user_markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)   
        user_markup.add(button_phone)
        msg = bot.send_message(message.chat.id, "Согласны ли вы предоставить ваш номер телефона для регистрации в системе?", reply_markup=user_markup)
        bot.register_next_step_handler(msg, reg_or_auth)
    else:
        if data is None:
            taximenu(message)
        else:
            passmenu(message)        
        

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:     
        if call.data == 'prov':
            prover(call.message)
        else:
            mydb = sqlite3.connect('base.db')
            mycursor = mydb.cursor()
            mycursor.execute(f'SELECT * FROM orders WHERE teg_id = {call.message.chat.id}')      
            orders = mycursor.fetchall()
            for order in orders:
                if call.data == f'order{order[0]}':
                    mycursor.execute(f'DELETE FROM orders WHERE id={order[0]}')
                    mydb.commit()
                    bot.send_message(call.message.chat.id, f'Заказ №{order[0]}, удалён!')
                    passmenu(call.message)
                else:
                    break
            mycursor.execute(f'SELECT id FROM orders')      
            orderss = mycursor.fetchall()
            for orderr in orderss:
                
                if call.data == f'go{orderr[0]}':
                    bot.send_message(call.message.chat.id, f'Отлично! Ожидайте клиента.')
                    mycursor.execute(f'SELECT teg_id FROM orders WHERE id = {orderr[0]}')      
                    klient = mycursor.fetchone()
                    bot.send_message(klient[0], 'Водитель подъехал и ожидает вас!')
                    mycursor.execute(f'DELETE FROM orders WHERE id={orderr[0]}')
                    mydb.commit()
                    break
                  
@bot.message_handler(content_types=['text'])
def textreader(message):
    teg_id = message.chat.id

    mydb = sqlite3.connect('base.db')
    mycursor = mydb.cursor()

    if message.text == 'Мои поездки':
        
        # connect to base
        # find orders for history orders to passenger
        mycursor.execute(f'SELECT id FROM orders WHERE teg_id = {message.chat.id}')      
        data = mycursor.fetchone()
        if data is None:
            bot.send_message(message.chat.id, "Заказы не найдены")
            passmenu(message)
        else:
            mycursor.execute(f'SELECT * FROM orders WHERE teg_id = {message.chat.id}')      
            orders = mycursor.fetchall()
            for order in orders:
                first_checkpoint = order[2]   # start address
                second_checkpoint = order[3]  # end address

                proverka = types.InlineKeyboardMarkup(row_width=5)
                item1 = types.InlineKeyboardButton('Отменить заказ', callback_data=f'order{order[0]}')
                proverka.add(item1)

                bot.send_message(message.chat.id, f"<i><b>Заказ №{order[0]}.</b></i>\n\n<i><b>Начальная точка:</b></i> {first_checkpoint}\n\n<i><b>Конечная точка:</b></i> {second_checkpoint}\n\n<b>Цена:</b> {order[4]} ₽", parse_mode='HTML', reply_markup=proverka)


    elif message.text == 'Новая поездка':
        # geolocation new order
        user_phone = useraphone(message, 'pass')
        mess = bot.send_message(message.chat.id, "Отправьте ваше местоположение.")
        bot.register_next_step_handler(mess, geo_location, user_phone, 'Пассажир')
        
    elif message.text == 'Выбрать поездку':

        # connect to base
        mydb = sqlite3.connect('base.db')
        mycursor = mydb.cursor()

        user_phone = useraphone(message, 'taxi')

        # choose order for taxi driver
        mycursor.execute(f'SELECT * FROM taxi_drivers')
        taxi_drivers = mycursor.fetchall()
        for taxi_driver in taxi_drivers:
            if taxi_driver[1] == user_phone:
                
                geo_location(message, user_phone, 'Таксист', firm=taxi_driver[2], car_numbers=taxi_driver[3], src_photo_car=taxi_driver[-2])
                break

    elif message.text == 'Баланс':
        # connect to base
        mydb = sqlite3.connect('base.db')
        mycursor = mydb.cursor()
        # choose Balance for taxi driver
        mycursor.execute(f'SELECT Balance FROM taxi_drivers WHERE teg_id = {teg_id}')
        balance = mycursor.fetchone()
        bot.send_message(message.chat.id, f"Ваш баланс: {balance[0]}")

    elif message.text == 'Пополнить баланс':
        pay = bot.send_message(message.chat.id, "Введить сумму")
        bot.register_next_step_handler(pay, payfunc)

    elif message.text == "Настройки":
        menunast(message)

    elif message.text == 'Назад':
        start(message)

    elif message.text == 'Сменить роль':

        mycursor.execute(f'SELECT teg_id FROM passengers WHERE teg_id = {message.chat.id}')      
        data = mycursor.fetchone()

        mycursor.execute(f'SELECT teg_id FROM taxi_drivers WHERE teg_id = {message.chat.id}')      
        datatwo = mycursor.fetchone()



        if data is None and datatwo is None:
            bot.send_message(message.chat.id, "Привет <b>{first_name}</b>, рад тебя видеть. Пожалуйста, отправьте мне свой номер для этого есть команда /phone".format(first_name=message.from_user.first_name), parse_mode='HTML', reply_markup=types.ReplyKeyboardRemove())
        else:
            if datatwo is None:
                user_phone = useraphone(message, '1')

                mycursor.execute(f"DELETE FROM passengers WHERE teg_id = {message.chat.id}")
                mydb.commit()

                mess = bot.send_message(message.chat.id, "Введите марку машины.", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(mess, machine_firm, user_phone)
            else:
                user_phone = useraphone(message, 'taxi')
                 # Add new passenger in 'passengers' table
                sqlFormula = "INSERT INTO passengers ('phone', 'teg_id') VALUES (?,?)"
                mycursor.execute(sqlFormula, (user_phone, message.chat.id))
                mydb.commit()

                mycursor.execute(f"DELETE FROM taxi_drivers WHERE teg_id = {message.chat.id}")
                mydb.commit()
        
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                passmenu(message)


if __name__ == '__main__':
	bot.polling(none_stop=True, interval=0)