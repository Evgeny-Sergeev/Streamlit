import streamlit as st
import datetime
st.set_page_config(layout="wide")    

with st.sidebar:
    st.header('Соцсети:')
    st.markdown("""
    - [Telegram](https://t.me/sergeevel)
    - [Instagram](https://instagram.com/sergeevel)
    - [VK](https://vk.com/sergeevel)
    """)



c1,c2 = st.columns(2)
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
    
c2.write('О тебе')
fvalue_0  = c2.multiselect('Что хотела бы найти?',['ONS','FWB','LTR'],default=[])
fvalue_1 = c2.slider('Возрост:',min_value  = 18,max_value  = 50,value = 30, step = 1)
fvalue_2 = c2.slider('Рост:',min_value  = 140,max_value  = 210,value = 160, step = 1)
fvalue_3 = c2.slider('Вес:',min_value  = 40,max_value  = 120,value = 60, step = 1)
fvalue_4 = c2.toggle('Замужем')
fvalue_5 = c2.toggle('Дети')
fvalue_6 = c2.slider('Сколько должен зарабатывать твой парень? (тыс руб в мес)',min_value  = 0,max_value  = 1000,value = 0, step = 10)

if c2.button('Узнать совместимость'):
    f1 = (100 - (fvalue_1 - 21))/100
    
    imt = fvalue_3/(fvalue_2/100)**2
    if imt <= 25: f23 = 1
    elif imt <= 30: f23 = 0.8
    elif imt <= 35: f23 = 0.6
    elif imt <= 40: f23 = 0.4
    else: f23 = 0.2
    
    if fvalue_4: f4 = 0.95
    else: f4 = 1
    if fvalue_5: f5 = 0.8 
    else: f5 = 1
    
    if fvalue_6 <= 200: f6 = 1
    elif fvalue_6 <= 300: f6 = 0.95
    elif fvalue_6 <= 400: f6 = 0.9
    elif fvalue_6 <= 600: f6 = 0.8
    else: f6 = 0.6
    
    f = f1*f23*f4*f5*f6*100
    
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
        print('ЗП:',fvalue_6,file = file)
        print('Результат:',f,file = file)
        print('',file = file)