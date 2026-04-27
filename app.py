import streamlit as st
from streamlit import session_state as ss
import openpyxl
from openpyxl.styles import Side, Border, Alignment,Font
import os
import re
from collections import Counter
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import plot as plot_offline
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score,mean_squared_error,mean_absolute_error
import lasio as ls
from io import StringIO


def process_file(df):
    df.rename(columns = {'мин':'time','атм':'p'},inplace = True)
    df.drop(0,inplace = True)
    df = df.replace(',','.',regex = True)
    for column in df.columns:
        df[column] = df[column].astype(float)
    return df
    

def make_less_dots(df):
    upsampled_df = df.resample("1min", on = 'dt').max().reset_index()
    return upsampled_df

    
def process_las(uploaded_file):
    bytes_data = uploaded_file.read()
    str_io = StringIO(bytes_data.decode('Windows-1252'))
    las = ls.read(str_io)
    df = las.df()
    
    date = las.well['DATE'].value
    time = las.well['TIME'].value
    dt = pd.to_datetime(f'{date} {time}', format='%d.%m.%Y %H-%M-%S')
    
    df = df.rename(columns = {'PRES':'bhp','TEMP':'temp'})
    df['time'] = df.index/60
    df = df.reset_index(drop = True)
    df['dt'] = df['time'].apply(lambda r: pd.Timedelta(minutes=r) + dt)    
    
    df = make_less_dots(df)
    
    ss.fig_bhp = px.scatter(df, x="dt", y="bhp")
    ss.fig_bhp.update_layout(xaxis_title='<b>Дата</b>, мин',yaxis_title='<b>Забойное давление</b>, атм',margin=dict(l=20, r=20, t=20, b=20),height=400)
       
    #df = to_1_min(df)
    return df
    
def process_event(uploaded_file):
    df = pd.read_excel(uploaded_file,skiprows=2,names = ['dt_s','dt_e','text_1','text_2'], parse_dates = [0,1])
    df[['text_1','text_2']] = df[['text_1','text_2']].fillna('')
    df['stage'] = df['text_2'].str.findall('(\d+)[\s-]?ст', flags=re.IGNORECASE)
    df.loc[~df['stage'].isna(),'stage'] = df.loc[~df['stage'].isna(),'stage'].apply(lambda r: r[0] if r != [] else np.nan)
    #df['stage'] = df['stage'].replace('',np.nan)
    df['stage'] = df['stage'].fillna(method = 'ffill')
    df['stage'] = df['stage'].fillna(0)
    df['stage'] = df['stage'].astype(int)
    
    df['time'] = (df['dt_s'] - df.iloc[0]['dt_s']).dt.total_seconds()/60
    df['text'] =  df['dt_s'].astype(str) + ' | ' + df['text_1'] + ' | ' + df['text_2']
    ss.event_text = df['text'].to_list()
    #st.write(ss.event_text)
    ss.fig_all_thp_all_time = go.Figure() #px.scatter(df, x="dt_s", y = np.zeros(len(df)), text = "text_1" )
    #for index,row in df.iterrows():
    #    ss.fig_all_thp_all_time.add_vrect(x0 = row['dt_s'], x1 = row['dt_e'], opacity = .1, line_width = 1, fillcolor = 'red', annotation_text = row['text_1'])
    #fig.add_vrect(x0=1, x1=2, annotation_text="Vertical Label", annotation_textangle=90)
    return df
    
class TREND_LINE():
    def __init__(self,data_frame,min_time,max_time,index):
        self.index = index
        self.fig = go.Figure()
        self.min_time = min_time#ss.results.loc[ss.index,'filter_min']
        self.max_time = max_time#ss.results.loc[ss.index,'filter_max']
        
        
        self.df = data_frame.loc[(data_frame['time'] >= self.min_time)&(data_frame['time'] <= self.max_time)&((data_frame['p'] > 1)),['time','p']]
        #self.df = data_frame.loc[(data_frame['time'] >= self.min_time)&(data_frame['time'] <= self.max_time),['time','p']]
        
        self.dff = pd.DataFrame({'time':np.arange(self.max_time,self.max_time+int(ss.forcast_time*60) + ss.step, ss.step)})

        
        self.trend_func_name = {'line':lambda x,k1: 1-k1*x,
                        'exp':lambda x,k1: np.exp(-k1*x),
                        'line_exp':lambda x,k1,k2: (1+x)**(-k1) - abs(k2)*x,
                        'arps':lambda x,k1,k2: (1+k1*abs(k2)*x)**((-1)/abs(k2)),
                        'power':lambda x,k1: (1+x)**(-k1),
                        'plato':lambda x,k1,k2: k2 + (1 - k2)*np.exp(-k1*x),}      

    def find_the_best_trend_line(self):
        step_n = ss.step
        self.metrics = pd.DataFrame()
        self.popt_df = pd.DataFrame()
        
        #if self.min_max_trend:
            
        
        
        while self.max_time - step_n > self.min_time:
            try:
                
                x_0 = self.max_time - step_n
                
                x = self.df.loc[self.df['time'] >= x_0,'time'] 
                y = self.df.loc[self.df['time'] >= x_0,'p']
                x0 = x.min()
                y0 = y.iloc[0]
                
                xs = x - x0

                for func_name,func in self.trend_func_name.items():
                    try:
                        popt, pcov = curve_fit(func, xs, y/y0)
                        y_trend = func(xs, *popt)*y0
                        self.metrics.loc[x0,func_name] = r2_score(y,y_trend)
                        self.popt_df.loc[x0,func_name] = ' '.join(map(str,popt))
                    except ValueError:
                        pass

            except RuntimeError:
                pass
                
            step_n += ss.step

        try:
            self.func_name = self.metrics.max().idxmax()
            self.metrics_score = self.metrics.max().max()
        
            self.x0 = self.metrics[self.func_name].idxmax()

            df = self.df[self.df['time'] >= self.x0]
            self.x = df['time'] 
            self.y = df['p']
            self.y0 = self.y.iloc[0]

            self.func = self.trend_func_name[self.func_name]
            self.popt = map(float,self.popt_df.loc[self.x0,self.func_name].split())
            
            
            ss.results.loc[self.index,'trend'] = self.func_name
            ss.results.loc[self.index,'r2_score'] = self.metrics_score
            ss.results.at[self.index,'params'] = self.popt_df.loc[self.x0,self.func_name].split()
            ss.results.loc[self.index,'trend_min'] = self.x0
            ss.results.loc[self.index,'trend_max'] = self.df['time'].max()
            self.error = False
        except ValueError:
            log_text(f'Не удалось найти оптимальный тренд для файла № {self.index}', 'yellow')
            self.error = True
            ss.results.loc[self.index,'trend'] = np.nan
            ss.results.loc[self.index,'r2_score'] = np.nan
            ss.results.loc[self.index,'params'] = np.nan
            ss.results.loc[self.index,'trend_min'] = np.nan
            ss.results.loc[self.index,'trend_max'] = np.nan
            #ss.results.loc[self.index,'bhp'] = np.nan
        
    def build_the_trend_line(self):
        #self.df.loc[self.df['time'] >= self.x0,'pf'] = self.func(self.x - self.x0,*self.popt)*self.y0
        if not self.error:
            self.x_trend = self.dff['time']
            xs = self.x_trend - self.x0
            self.y_trend = self.func(xs,*self.popt)*self.y0
            self.dff['pf'] = self.y_trend
            self.dff.loc[self.dff['pf'] < 0, 'pf'] = 0
            self.dff['bhpf'] = self.y_trend + ss.bhp_add
            self.dff.loc[self.dff['bhpf'] < 0, 'bhpf'] = 0
            for ft in range(ss.forcast_time+1):
                bhp = self.dff.loc[self.dff['time'] == self.max_time+ft*60,'bhpf'].values[0]
                if ss.bhp_add/ss.filter <= bhp <= ss.bhp_add*ss.filter:
                    ss.results.loc[self.index,f'bhp_{ft}'] = bhp
                else:
                    ss.results.loc[self.index,f'bhp_{ft}'] = np.nan
    
    def run_all_trend_lines(self):
        self.find_the_best_trend_line()
        self.build_the_trend_line()

        self.fig.add_trace(go.Scatter(x = ss.df[self.index]['time'], y = ss.df[self.index]['p'], mode='lines+markers', name = f'Устьевое давление', marker=dict(color = 'grey'), line=dict(color = 'lightgrey', width = 3)))
        self.fig.add_trace(go.Scatter(x = self.df['time'], y = self.df['p'], mode='lines+markers', name = f'Устьевое давление фильтр', marker=dict(color = 'black'), line=dict(color = 'black', width = 3)))
        if not self.error:
            self.fig.add_trace(go.Scatter(x = self.dff['time'], y = self.dff['pf'], mode='lines+markers', name=f'Тренд прогноз',marker=dict(color = 'green'), line=dict(color = 'green', width = 3)))
            self.fig.add_trace(go.Scatter(x = self.dff['time'], y = self.dff['bhpf'], mode='lines+markers', name=f'Забойное давление',marker=dict(color = 'red'), line=dict(color = 'red', width = 3)))
            
            df_filter = self.df[(self.df['time'] >= ss.results.loc[self.index,'trend_min'])&(self.df['time'] <= ss.results.loc[self.index,'trend_max'])]
            self.fig.add_trace(go.Scatter(x = df_filter['time'], y = df_filter['p'], mode='lines', line=dict(color = 'lime', width = 3), name = f'Тренд {self.func_name} {self.metrics_score:.3f}')) 
        self.fig.update_layout(xaxis_title='<b>Время проведения ГРП</b>, мин',yaxis_title='<b>Устьевое/Забойное давление</b>, атм',margin=dict(l=20, r=20, t=50, b=20),height=250,legend=dict(orientation="h",yanchor="bottom",y = 1.0 ,xanchor="center", x= 0.5))        
        return self.fig

#tl = TREND_LINE(df,100,120, step = 5,show_plot = True)
#tl.run_all_trend_lines()    

def run_recalculate(index,filter_min,filter_max):
    df = ss.df[index]
    ss.results.loc[index,'filter_min'] = filter_min
    ss.results.loc[index,'filter_max'] = filter_max

    tl = TREND_LINE(df,filter_min,filter_max,index)
    fig = tl.run_all_trend_lines()
    ss.figures[index] = fig
    #del ss['df_editor']
    st.rerun()
    

def recalculate():
    if len(ss.df_editor["edited_rows"]) == 0:
        log_text(f'Не было изменений','yellow')
    else:
        for index, values in ss.df_editor["edited_rows"].items():
            #st.write(values)
            index = int(index)
            
            log_text(f'Перасчет файла #{index}: {ss.results.loc[index,"name"]}')
            
            if 'Рассчитать' in values:
                calculate = values['Рассчитать']
                #df_time_min = ss.df[index]['time'].min()
                #if filter_min < df_time_min:
                #    filter_min = df_time_min
            else:
                calculate = ss.results.loc[index,'calculate']            
            
            if 'Фильтр минимум, мин' in values:
                filter_min = values['Фильтр минимум, мин']
                df_time_min = ss.df[index]['time'].min()
                if filter_min < df_time_min:
                    filter_min = df_time_min
            else:
                filter_min = ss.results.loc[index,'filter_min']
                
            if 'Фильтр максимум, мин' in values:
                filter_max = values['Фильтр максимум, мин']
                df_time_max = ss.df[index]['time'].max()
                if filter_max > df_time_max:
                    filter_max = df_time_max                
            else:
                filter_max = ss.results.loc[index,'filter_max']
                
            if filter_min >= filter_max:
                log_text(f'В файле №{index} введены некорректные данные','red')
            else:
                if calculate:
                    run_recalculate(index,filter_min,filter_max)
                else:
                    df = ss.df[index]
                    fig = blank_thp(df)
                    ss.figures[index] = fig
                    ss.results.loc[index,bhp_columns] = np.nan
                    ss.results.loc[index,['trend','r2_score']] = np.nan
                    #st.write(ss.results)
                    st.rerun()
                    
                
def recalculate_all():
    try:
        if ss.figures != dict():
            with st.spinner("Перерасчет выполняется..."):
                progress = st.sidebar.progress(0, text='Перерасчет файлов')
                num_files = len(ss.figures)
                for index, _ in ss.figures.items():
                    df = ss.df[index]
                    filter_min = ss.results.loc[index,'filter_min']
                    filter_max = ss.results.loc[index,'filter_max']

                    tl = TREND_LINE(df,filter_min,filter_max,index)
                    fig = tl.run_all_trend_lines()
                    #streamlit_main.plotly_chart(fig)
                    ss.figures[index] = fig
                    
                    progress.progress(int((index+1)*100/num_files), text='Перерасчет файлов')
            st.rerun()
    except Exception as error:
        log_text(f'Ошибка в перерасчете всех графиков: {error}','red')
    
        
def change_excel(well_name):   
    def set_border(ws, side=None, blank=True):
        wb = ws._parent
        side = side if side else Side(border_style='thin', color='000000')
        for cell in ws._cells.values():
            cell.border = Border(top=side, bottom=side, left=side, right=side)
            cell.alignment = Alignment(horizontal='center', vertical='center',wrap_text=True)
            
    wb = openpyxl.load_workbook(f'result/{well_name}_result.xlsx')
    sh = wb.active

    sh.column_dimensions['A'].width = 50
    sh.column_dimensions['B'].width = 12
    sh.column_dimensions['C'].width = 12
    #sh.column_dimensions['D'].width = 20

    sh['T1'].font = Font(bold=True)

    side = Side(border_style='thin')
    set_border(sh, side)

    wb.save(filename = f'result/{well_name}_result.xlsx')    
        
def save_results():
    #try:
    if True:
        well_name = ''
        meetings = 0
        file_names = ' '.join(ss.results['name'].to_list())
        file_names = re.sub("\d\d.\d\d.\d\d\d\d","",file_names)
        find_all = re.findall('(\d+)',file_names)
        #Определение имени скважины по названиям вайлов
        for wn,count in Counter(find_all).items():
            if meetings <= count:
                if len(well_name) <=  len(wn):
                    well_name = wn

        os.makedirs("result", exist_ok=True)

        results = ss.results.drop(['filter_min','filter_max','params','trend_min','trend_max','text'],axis = 1,errors = 'ignore') #[['name','trend','r2_score','bhp']]
        results.loc[results.index.max()+1,'name'] = 'Среднее'

        
        bhp_columns = tuple(bhp_columns_reanme.keys())
        results['r2_score'] = results['r2_score'].astype(float).round(5)
        for bhp_i in bhp_columns:
            results.iloc[-1][bhp_i] = results[bhp_i]
            results[bhp_i] = results[bhp_i].round(1)
        
        results = results.rename(columns = {'name':'Имя файла','trend':'Тренд','r2_score':'Метрика R2'})
        results = results.rename(columns = bhp_columns_reanme)
        
        
        results.to_excel(f'result/{well_name}_result.xlsx',index = False)
        change_excel(well_name)
        
        
        for index,fig in ss.figures.items():
            fig.update_layout(height=500)
            fig_html = plot_offline(fig, output_type='div', include_plotlyjs='cdn')
            if index == 0:
                if 'fig_violin' in ss:
                    ss.fig_violin.update_layout(height=500)
                    fig_violin_html = plot_offline(ss.fig_violin, output_type='div', include_plotlyjs='cdn')
                    fig_all = fig_violin_html + fig_html
                    ss.fig_violin.update_layout(height=250)
                else:
                    fig_all = fig_html
            else:
                fig_all += fig_html
            fig.update_layout(height=250)
        #with open(f'result/{well_name}/{ss.results.loc[index,"name"]}.html', 'w') as file_pic:
        with open(f'result/{well_name}_pic.html', 'w') as file_pic:
            file_pic.write(fig_all)
            
        if 'fig_all_thp_all_time' in ss:
            for count,trace in enumerate(ss.fig_all_thp_all_time.data):
                x_values = trace.x
                y_values = trace.y
                if count == 0:
                    df_time_thp = pd.DataFrame({'Время':x_values,'Устьевое давление, атм':y_values})
                else:
                    df_time_thp_tmp = pd.DataFrame({'Время':x_values,'Устьевое давление, атм':y_values})
                    df_time_thp = pd.concat([df_time_thp,df_time_thp_tmp])
            df_time_thp = df_time_thp[~df_time_thp['Время'].isna()].sort_values(by = 'Время')
            df_time_thp.to_excel(f'result/{well_name}_thp.xlsx',index = False)
                    

     
        
        log_text(f'Результат успешно сохранен: result','green')
    #except Exception as error:
    #    log_text(f'Ошибка сохранения результатов','red')


#def merge_pressure():
#    ss.fig_ls = px.scatter(ss.df_ls, x="time_i", y="bhp_i")#, trendline='lowess', trendline_options=dict(frac=0.1))
#    for index,df in ss.df_1_min.items():
#        
#        len_df = len(df)
#        max_index = ss.df_ls.iloc[-len_df:].index.min()
#        best_d = np.inf
#        best_index = 0
#        for index_i,row in ss.df_ls.iterrows():
#            if index_i > max_index: break 
#            temp_d = ((ss.df_ls.loc[index_i:index_i+len_df,'bhp_d'] - df['bhp_d']).abs()).sum()
#            if d > temp_d: 
#                best_d = temp_d
#                best_index = index_i
#        st.write(index,best_index,best_d)
#        df['time_i'] += ss.df_ls.loc[best_index,'time_i']
#        ss.fig_ls.add_trace(go.Scatter(x = df['time_i'], y = df['bhp_i'], mode='lines+markers', name = f'Устьевое давление {index}'))

def blank_thp(df):
    fig = px.line(df, x = 'time', y = 'p', markers=True)
    fig.update_traces(line_color='black')
    fig.update_layout(xaxis_title='<b>Время проведения ГРП</b>, мин',yaxis_title='<b>Устьевое/Забойное давление</b>, атм',margin=dict(l=20, r=20, t=50, b=20),height=250,legend=dict(orientation="h",yanchor="bottom",y = 1.0 ,xanchor="center", x= 0.5))  
    return fig

def log_text(text,color = 'black'):
    if color == 'black':
        ss.text += text+'\t|\t'
    else:
        ss.text += f":{color}[{text}]\t|\t"
        
def add_annotation(fig):
    for index,row in ss.df_event.iterrows():
        if row['text_1'] == 'ГРП':
            fig.add_vrect(x0 = row['dt_s'], x1 = row['dt_e'], opacity = .1, line_width = 1, fillcolor = 'red', annotation_text = row['text_1'],annotation_position="top left",annotation_textangle = -90) 
        else:
            fig.add_vrect(x0 = row['dt_s'], x1 = row['dt_e'], opacity = .1, line_width = 1, fillcolor = 'white', annotation_text = row['text_1'],annotation_position="top left",annotation_textangle = -90) 

def change_all_thp_all_time():
    result_event_change = ss.result_event["edited_rows"]
    for index, text in result_event_change.items():
        ss.results.loc[index,'text'] = text['text']
        dt_s = ss.df_event.loc[ss.df_event['text'] == text['text'],'dt_s'].values[0]
        ss.df[index]['dt'] = ss.df[index]['time'].apply(lambda r: pd.Timedelta(minutes=r) + dt_s)     
        
    ss.fig_all_thp_all_time = go.Figure()
    add_annotation(ss.fig_all_thp_all_time)
    #for index,row in ss.df_event.iterrows():
    #    ss.fig_all_thp_all_time.add_vrect(x0 = row['dt_s'], x1 = row['dt_e'], opacity = .1, line_width = 1, fillcolor = 'red', annotation_text = row['text_1'],annotation_position="top left",annotation_textangle = -90)    
    for index,row in ss.results.iterrows():
        if pd.isna(row['text']): continue
        else:
            ss.fig_all_thp_all_time.add_trace(go.Scatter(x = ss.df[index]['dt'], y = ss.df[index]['p'],mode='lines+markers', name = row['name']))


def define_GRP():
    if 'text' not in ss.results.columns:
        ss.results['text'] = np.nan

    #st.write(ss.df_event)
    for index,row in ss.results.iterrows():
        if pd.isna(row['text']): 
            try:
                name = re.sub('[-_]',' ',row['name'].lower())
                if 'грп' not in name:
                    continue
                name = re.sub('\s+',' ',name)
                stage = re.findall('ст[\s]?(\d+)', name)[0]
                
                text = ss.df_event.loc[(ss.df_event['stage'] == int(stage))&(ss.df_event['text_1'].str.strip().str.lower() == 'грп'),'text'].values[0]
                ss.results.loc[index,'text'] = text
      
                dt_s = ss.df_event.loc[(ss.df_event['stage'] == int(stage))&(ss.df_event['text_1'].str.strip().str.lower() == 'грп'),'dt_s'].values[0]
                ss.df[index]['dt'] = ss.df[index]['time'].apply(lambda r: pd.Timedelta(minutes=r) + dt_s)                     
            except IndexError:
                log_text(f"Для файла {row['name']}, не была определена стадия ГРП",'orange')

    ss.fig_all_thp_all_time = go.Figure()
    add_annotation(ss.fig_all_thp_all_time)
 
    for index,row in ss.results.iterrows():
        if pd.isna(row['text']): continue
        else:
            ss.fig_all_thp_all_time.add_trace(go.Scatter(x = ss.df[index]['dt'], y = ss.df[index]['p'],mode='lines+markers', name = row['name']))
            

def make_shift():
    shift_edited = ss.shift["edited_rows"]
    for index, row in shift_edited.items():
        #st.write(row)
        ss.results.loc[index,'shift'] = row['Смещение, мин']
        
    ss.fig_all_thp = go.Figure()
    for index,row in ss.results.iterrows():
        ss.fig_all_thp.add_trace(go.Scatter(x = ss.df[index]['time']-row['shift'], y = ss.df[index]['p'], mode='lines+markers', name = row['name']))

st.set_page_config(layout="wide")  

if __name__ == '__main__':
    if 'index' not in ss:
        
        ss.results = pd.DataFrame(columns = ['name','filter_min','filter_max','trend','r2_score','params','trend_min','trend_max'])
        ss.df = dict()
        #ss.df_1_min = dict()
        ss.index = 0
        ss.figures = dict()
        ss.text = ''
        ss.fig_all_thp = go.Figure()
        #ss.fig_all_thp_all_time = go.Figure()
        ss.uploaded_file_name = ['','']
        ss.add_annotation_to_bhp = True
        #ss.fig_bhp = 
        

    st.sidebar.header('Пластовое давление по ГРП 🛢️')
    
    
    if st.sidebar.toggle('Расчитать давление на забой по глубине',value = True):
        H = st.sidebar.number_input('Верх перфорациии, м',min_value=0.0,max_value=10000.0,value=3000.0,key = 'H')
        h = st.sidebar.number_input('Удлинение, м',min_value= 0.0,max_value=10000.0,value=500.0, key = 'h')
        d = st.sidebar.number_input('Плотность жидкости, г/см3',min_value=0.1,max_value=5.0,value=1.01, key = 'd')
        ss.bhp_add = 9.8*ss.d*(ss.H-ss.h)*9.869/1000
        bhp_add = st.sidebar.number_input("Гидростатичесое давление на забой, атм", disabled = True, value = ss.bhp_add,on_change = recalculate_all)
    else:
        bhp_add = st.sidebar.number_input("Гидростатичесое давление на забой, атм",min_value = 0,max_value = 1000, value = 120, key = 'bhp_add',on_change = recalculate_all)
    forcast_time = st.sidebar.number_input("Прогноз построения тренда, час",min_value = 1,max_value = 24, value = 6,key = 'forcast_time',on_change = recalculate_all)
    step = st.sidebar.number_input("Шаг рассчета тренда, мин",min_value = 0,max_value = 60, value = 1,key = 'step', on_change = recalculate_all)
    st.sidebar.number_input("Ограничение по забойному давлению от гидростатического",min_value = 0.0,max_value = 10.0, value = 2.0,key = 'filter', on_change = recalculate_all)

    streamlit_main = st.container(border = False)
    tab_1,tab_2 = streamlit_main.tabs(['Прогноз устьевого/забойного давления','Сопоставление устьевого/забойного давления'])

    streamlit_left,streamlit_right = tab_1.columns([50, 50])
    log = st.expander(label = 'Информация для пользователя',expanded = True).container(border = True, height = 100)

    uploaded_files_1 = st.sidebar.file_uploader("Загрузка: Устьевых давлений", accept_multiple_files = True, type=["csv", "txt"])
    uploaded_file_2 = st.sidebar.file_uploader("Загрузка: Забойного давления", type=["las"])
    uploaded_file_3 = st.sidebar.file_uploader("Загрузка: Хронологии ГРП", type=["xlsx"])
    if uploaded_files_1 is not None:
        for uploaded_file_1 in uploaded_files_1:
            if uploaded_file_1.name in ss.results['name'].unique():
                pass
            else:

                try:
                    df = pd.read_csv(uploaded_file_1,skiprows = 1, sep=r"\s+")
                except UnicodeDecodeError as error:
                    st.error(f'Ошибка в кодировке файла: {error}')
                    st.info('Для решения проблемы, ноздайте новый .txt файл и скопируйте в него содержимое исходного файла (лучше делать в текстовом редакторе Notepad++)')

                df = process_file(df)
                

                trend_min = df['time'].min()
                trend_max = df['time'].max()
                
                ss.df[ss.index] = df
                #ss.df_1_min[ss.index] = to_1_min(df)
                ss.results.loc[ss.index,'name'] = uploaded_file_1.name
                ss.results.loc[ss.index,'filter_min'] = trend_min
                ss.results.loc[ss.index,'filter_max'] = trend_max
                ss.results.loc[ss.index,'shift'] = 0
                
                re_string = re.findall('грп',uploaded_file_1.name.lower())
                if re_string:
                    ss.results.loc[ss.index,'calculate'] = True
                    tl = TREND_LINE(df,trend_min,trend_max,ss.index)
                    fig = tl.run_all_trend_lines()
                else:
                    ss.results.loc[ss.index,'calculate'] = False
                    fig = blank_thp(df)

                
                ss.figures[ss.index] = fig
                ss.fig_all_thp.add_trace(go.Scatter(x = df['time'], y = df['p'], mode='lines+markers', name = uploaded_file_1.name))
                
                ss.index += 1
            
    if uploaded_file_2 is not None and 'df_bhp' not in ss:     
        ss.df_bhp = process_las(uploaded_file_2)
        ss.add_annotation_to_bhp = True
    elif uploaded_file_2 is None and 'df_bhp' in ss:
        del ss['df_bhp']
        
    if uploaded_file_3 is not None and 'df_event' not in ss:     
        ss.df_event = process_event(uploaded_file_3)
        define_GRP()
        ss.add_annotation_to_bhp = True
    elif uploaded_file_3 is None and 'df_event' in ss:
        del ss['df_event']
        
    if 'df_bhp' in ss and 'df_event' in ss:
        if ss.add_annotation_to_bhp:
            add_annotation(ss.fig_bhp)
            ss.add_annotation_to_bhp = False

    if not ss.results.empty:
        with tab_1:
            streamlit_df_left,streamlit_df_right = tab_1.columns([25, 75])
            
            bhp_columns = [f'bhp_{ft}' for ft in range(ss.forcast_time+1)]
            bhp_columns_reanme = {f'bhp_{ft}': f'Pз {ft}' for ft in range(ss.forcast_time+1)}
            df_editor = streamlit_df_left.data_editor(ss.results[['calculate','filter_min','filter_max']].rename(columns = {'calculate':'Рассчитать','filter_min':'Фильтр минимум, мин','filter_max':'Фильтр максимум, мин'}), num_rows = 'fixed', key = 'df_editor', hide_index  = True, on_change = recalculate) #.rename(columns = {'filter_min':'Минимальное время, мин','filter_max':'Максимальное время, мин'})
            streamlit_df_right.dataframe(ss.results.drop(['filter_min','filter_max','params','trend_min','trend_max','text','calculate','shift'],axis = 1,errors = 'ignore').rename(columns = {'name':'Имя файла','trend':'Тренд','r2_score':'Метрика R2','bhp':'Забойное давление, атм'} | bhp_columns_reanme))
            
            
            tab_1.write(f'Среднее забойное давление:')
            mean_result = ss.results[bhp_columns].mean().to_frame().T
            tab_1.write(mean_result.rename(columns = bhp_columns_reanme))
            
            for index,fig in ss.figures.items():
                uploaded_file_name = ss.results.loc[index,'name']
                if len(ss.figures) <= 2: 
                    tab_1.expander(label = uploaded_file_name,expanded = True).container(border = True).plotly_chart(fig) 
                else:
                    if index % 2 == 0: streamlit_lr = streamlit_left
                    else: streamlit_lr = streamlit_right
                    streamlit_lr.expander(label = uploaded_file_name,expanded = True).container(border = True).plotly_chart(fig) 
                    
            if len(ss.results) >= 4:
                ss.fig_violin = px.violin(ss.results, y = bhp_columns, box=True, points='all')
                ss.fig_violin.update_layout(xaxis_title=None,yaxis_title='<b>Забойное давление</b>, атм',margin=dict(l=20, r=20, t=20, b=20),height=250)
                tab_1.expander(label = 'Скрипичный график',expanded = True).container(border = True).plotly_chart(ss.fig_violin)     
                #st.sidebar.expander(label = 'Скрипичный график',expanded = True).container(border = True).plotly_chart(ss.fig_violin)   

        with tab_2:
            tab_2_left,tab_2_right = tab_2.columns([70, 30])
            tab_2_right.data_editor(ss.results[['name','shift']].rename(columns = {'name':'Название файла','shift':'Смещение, мин'}), hide_index=True,key = 'shift',on_change = make_shift)
            ss.fig_all_thp.update_layout(xaxis_title='<b>Время</b>, мин',yaxis_title='<b>Устьевое давление</b>, атм',margin=dict(l=20, r=20, t=20, b=20),height=400,)#legend=dict(orientation="h",yanchor="top", y=1.15, xanchor="center", x=0.5))
            tab_2_left.expander(label = 'Все устьевые давления',expanded = True).container(border = True).plotly_chart(ss.fig_all_thp)        
        
            if 'event_text' in ss:
                tab_2.data_editor(ss.results[['name','text']].rename(columns = {'name':'Название файла'}), column_config={"text": st.column_config.SelectboxColumn(
                    "Сопоставление даты и времени",
                    options=ss.event_text,
                    required=True,)},
                hide_index=True,key = 'result_event',on_change = change_all_thp_all_time)
                #tab_2.button('Автоопрделение стадий ГРП',on_click = define_GRP)
                ss.fig_all_thp_all_time.update_layout(xaxis_title='<b>Дата</b>',yaxis_title='<b>Устьевое давление</b>, атм',margin=dict(l=20, r=20, t=20, b=20),height=400)
                tab_2.expander(label = 'Устьевое давление за все время',expanded = True).container(border = True).plotly_chart(ss.fig_all_thp_all_time)

            if 'df_bhp' in ss:
                tab_2.expander(label = 'Забойное давление',expanded = True).container(border = True).plotly_chart(ss.fig_bhp)     
                

         
        button_save = st.sidebar.button('Сохранить результат',width = "stretch",on_click = save_results)


    log.write(ss.text)



































