import streamlit as st
import datetime
import telebot

api_key = '5386242423:AAGz5YhkjFVEpQRQyPh5jIxl6bok6OOUhyE'
chat_id = '540367764'
bot = telebot.TeleBot(api_key)

st.set_page_config(layout="wide")


with st.sidebar:
    st.header('Соцсети:')
    st.markdown("""
    - [Telegram](https://t.me/sergeevel)
    - [Instagram](https://instagram.com/sergeevel)
    - [VK](https://vk.com/sergeevel)
    """)


c1,c2,c3 = st.columns(3)

c1.subheader('Обо мне')
c1.markdown("""
Привет, меня зовут **Женя** 35 лет\n
Кредитов, жен, детей нет\n
Живу в ЮЗАО Москвы м. Саларьево\n
Работаю в нефтяной компании, занимаюсь разработкой месторождений\n

Увлечения:
- Спорт (занимаюсь bjj)
- Рисование
- Чтение
- Квизы
- Программирование
""")
    
c2.subheader('О тебе')
fvalue_0  = c2.multiselect('Что хотела бы найти?',['ONS','FWB','LTR'],default=[])
fvalue_1 = c2.slider('Возрост:',min_value  = 18,max_value  = 50,value = 30, step = 1)
fvalue_2 = c2.slider('Рост:',min_value  = 140,max_value  = 210,value = 160, step = 1)
fvalue_3 = c2.slider('Вес:',min_value  = 40,max_value  = 120,value = 60, step = 1)
fvalue_4 = c2.toggle('Замужем')
fvalue_5 = c2.toggle('Дети')
imt = fvalue_3/(fvalue_2/100)**2

if c2.button('Узнать совместимость'):
    f1 = (100 - (fvalue_1 - 21))/100
    
    
    if imt <= 25: f23 = 1
    elif imt <= 30: f23 = 0.8
    elif imt <= 35: f23 = 0.6
    elif imt <= 40: f23 = 0.4
    else: f23 = 0.2
    
    if fvalue_4: f4 = 0.95
    else: f4 = 1
    if fvalue_5: f5 = 0.8 
    else: f5 = 1
    
    f = f1*f23*f4*f5*100
    
    #c2.subheader(f'Совместимость {f1} {imt} {f23} {f4} {f5}: **{f:.1f}**%')
    c2.subheader(f'Совместимость: **{f:.1f}**%')
    
    with open('result.txt','a') as file:
        print(datetime.datetime.now(),file = file)
        print('Цель:',fvalue_0,file = file)
        print('Возрост:',fvalue_1,file = file)
        print('Рост:',fvalue_2,file = file)
        print('Вес:',fvalue_3,file = file)
        print('Замужем:',fvalue_4,file = file)
        print('Дети:',fvalue_5,file = file)
        #print('ЗП:',fvalue_6,file = file)
        print('Результат:',f,file = file)
        print('',file = file)
        

c3.subheader('О идеальном парне')
value_0 = c3.slider('Сколько должен зарабатывать? (💵 тыс руб в мес)',min_value  = 0,max_value  = 1000,value = 0, step = 10)
#if value_0 <= 200: v_0 = 1
#elif value_0 <= 300: v_0 = 0.95
#elif value_0 <= 400: v_0 = 0.9
#elif value_0 <= 600: v_0 = 0.8
#else: v_0 = 0.6
value_1 = c3.slider('Сколько длина болта? (🔩 см)',min_value  = 7,max_value  = 24,value = 15, step = 1)

if value_1 <= 14: c3.write('🧐')
elif 15 <= value_1 <= 18: c3.write('😎')
elif value_1 == 19: c3.write('🫤')
elif value_1 == 20: c3.write('😯')
elif value_1 == 21: c3.write('😮')
elif value_1 == 22: c3.write('😲')
elif value_1 == 23: c3.write('😧')
elif value_1 == 24: c3.write('😨')
    
with c3.form("О идеальном парне"):    
    st.write('Выберете 7 важнейших качеств для парня:')
    v_1 =  st.toggle('Честность')
    v_2 =  st.toggle('Ответственность')
    v_3 =  st.toggle('Чувство юмора')
    v_4 =  st.toggle('Физическая форма')
    v_5 =  st.toggle('Щедрость')
    v_6 =  st.toggle('Доброта и эмпатия')
    v_7 =  st.toggle('Успешность и целеустремленность')
    v_8 =  st.toggle('Опрятность')
    v_9 =  st.toggle('Стрессоустойчивость')
    v_10 = st.toggle('Верность')
    v_11 = st.toggle('Способность держать слово')
    v_12 = st.toggle('Общительность')
    v_13 = st.toggle('Авторитетность')
    v_14 = st.toggle('Умение слушать')
    v_15 = st.toggle('Без вредных привычек')

    v_sum = sum([v_1,v_2,v_3,v_4,v_5,v_6,v_7,v_8,v_9,v_10,v_11,v_12,v_13,v_14,v_15])
    st.write(f'Выбрано {v_sum} из 7')
    submitted = st.form_submit_button("Пуск")
    
    if submitted:
        if v_sum <= 7:
            st.write('Совпадение: 💘')
        else:
            st.write(f'Выберете меньше качеств')
            
with st.sidebar:

    with st.form("Форма"):
        telegram_id = st.text_input(label = 'Твой telegram id:', value = '')
        send_tg = st.form_submit_button("Познакомиться")
        if send_tg:
            if telegram_id != '':
                st.write('Приветствие отправлено')
                try:
                    v_list = ['Честность','Ответственность','Чувство юмора','Физическая форма','Щедрость','Доброта и эмпатия','Успешность и целеустремленность','Опрятность','Стрессоустойчивость','Верность','Способность держать слово','Общительность','Авторитетность','Умение слушать','Без вредных привычек']
                    v_string = ', '.join(v_list[n] for n,v in enumerate([v_1,v_2,v_3,v_4,v_5,v_6,v_7,v_8,v_9,v_10,v_11,v_12,v_13,v_14,v_15]) if v)
                except NameError:
                    v_string = ''
                bot.send_message(chat_id,text = f"""
                tg = {telegram_id}
                Цель знакомства: {fvalue_0}
                Возраст: {fvalue_1}
                Рост: {fvalue_2}
                Вес: {fvalue_3}
                ИМТ: {imt}
                Замужем: {fvalue_4}
                Дети: {fvalue_5}
                Совместимость: {f:.1f}
                Заработок: {value_0}
                Длина: {value_1}
                Параметры: {v_string}
                """)
                
            else:
                st.write('Пусто поле telegram id')
