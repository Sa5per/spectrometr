from tkinter import *
from tkinter import filedialog as fd
import tkinter.ttk as ttk
import sys
import os
import math
import copy
from operator import itemgetter

import numpy as np
import pandas as pd
import statsmodels.api as sm

from pandas.plotting import autocorrelation_plot
from scipy import fftpack
from scipy import log10
import scipy.stats as stats

from matplotlib import pyplot as plt
from matplotlib.widgets import TextBox
import pickle

ydata_patterns=[]

ydata_rgb=[]

CCDrawR=[]
CCDrawG=[]
CCDrawB=[]

red=[]
green=[]
blue=[]

red_mid = 643 #лазер светит на частоте 660нм. вся линейка охватывает спектр шириной 35,7 нм. серединалинейки приходится надлину волны примерно 660-17=643нм
green_mid=503 #лазер 520нм-17нм
blue_mid=433 #лазер 450нм-17нм

CCDSize=11082

def loadDataRGB():
    global CCDrawR
    global CCDrawG
    global CCDrawB
    global red
    global green
    global blue
    global ydata_rgb
    global ydata
    global timepoints
    global metkabuf
    global kategories
    global pic_list
    global pic_file_list
    global rgb
    global g_file_name

    CCDnumR=[]
    CCDnumG=[]
    CCDnumB=[]
    #CCDrawR=[]
    #CCDrawG=[]
    #CCDrawB=[]
    readData=[]
    #red=[]
    #green=[]
    #blue=[]
    CCDrawR.clear()
    CCDrawG.clear()
    CCDrawB.clear()
    red.clear()
    green.clear()
    blue.clear()
    
    

    
    #pi=pigpio.pi()
    baud_rgb_patterns.delete('1.0',END)
    baud_rgb_patterns.insert('1.0','Загружаем данные...\n')
    
    file_name = fd.askopenfilename(defaultextension='*.dat', filetypes=(("DAT files", "*.dat"),
                                                ("All files", "*.*")))
    
    if file_name :
        
        with open(file_name,'rb') as f:
            ydata_rgb=f.read()
        print('len ydata_rgb',len(ydata_rgb))
        file_time=file_name[0:-3]+'tim'
        g_file_name=file_name.split('/')
        
        try:
            f = open(file_time, 'r').read()
            print('f=',f)
            time_plot=f.split('\n')
            print('f.split=',time_plot)
            time_text=str('time:'+time_plot[0][:-1]+'sec,'+'frames:'+time_plot[1])
            print (time_text)
            step_time=float(time_plot[0])/int(time_plot[1])
            timepoints=[]
            for i in range (int(time_plot[1])):
                if i==0:
                    timepoints.append(0)
                else:
                    timepoints.append(timepoints[-1]+step_time)
        except IOError:
            print('no times in file')

        #открываем файл с метками:
        
        num_frames=int(len(ydata_rgb)/(CCDSize*2))
        print('frames:',num_frames)
        for j in range(0,num_frames):#len(ydata_rgb),2):
            for i in range (0,CCDSize*2,2):
                if i<len(ydata_rgb):
                    p=((ydata_rgb[j*CCDSize*2+i+1]<<8)|ydata_rgb[j*CCDSize*2+i])
                    readData.append(p)
            #print('len readData:',len(readData))
            CCDnumR=readData[0::3]
            CCDnumG=readData[1::3]
            CCDnumB=readData[2::3]
            #print ('len CCDnumR,G,B:',len(CCDnumR),len(CCDnumG),len(CCDnumB))
            
            #запишем в массивы red,green,blue максимумы значений (т.е. фактически - длины волн каждого лазера)
            #массив red,green,blue - содержат инфу по изменению длины волны каждого лазера.Максимальное значение - максимальная интенсивность
            #максимум графика - это максимальные значения графика. График перевернут, поэтому мин и макс поменяны местами
            #red.append(CCDnumR.index(min(CCDnumR[20:-1]))) # найдем номер пикселя матрицы,с максимальной засветкой (т.е. измеренную длину волны лазера).первые 20 байт содержат шум. их можно выкинуть.(из даташита по CCD-матрице).график инвертирован, поэтому ищем минимум
            #green.append(CCDnumG.index(min(CCDnumG[20:-1])))
            #blue.append(CCDnumB.index(min(CCDnumB[20:-1])))

            #Вариант2: максимум - центр масс пика. низ пика берется как 1/3 от разницы между мксимумом и минимумом (топорно, но хоть что-то)
            red.append(center_mass(CCDnumR[20:-1]))
            green.append(center_mass(CCDnumG[20:-1]))
            blue.append(center_mass(CCDnumB[20:-1]))


            
            
            CCDrawR.append(CCDnumR)
            CCDrawG.append(CCDnumG)
            CCDrawB.append(CCDnumB)
            readData.clear()

        metka_file=file_name[:-3]+'kat' 
        try:
            file = open(metka_file,'r').read()
        except IOError as e:
            print(u'файл с категориями не существует')
            metkabuf=[]
            pic_list=[]
            pic_file_list=[]
        else:
            #print(u'заносим метки в базу данных')
            buf=[]
            metkabuf=[]
            pic_list=[]
            pic_file_list=[]
            kategories=[]
            metkaArray = file.split('\n')
            print('metkaArray:',metkaArray)
            for eachLine in metkaArray:
              if len(eachLine)>0:
                buf=eachLine.split(';') #делим полученную строку на 2 части. разделитель ";"
                metkabuf.append(int(buf[0]))#первая часть - отметка. заносим её в буфер
                print('buf=',buf)
                #теперь получаем список файлов для каждой отметки
                pic_file_list.append(str(buf[-1]))
                pic_file_name=pic_file_list[-1].split('\\')#делим строку на части, где разделить "\"
                pic_list.append(pic_file_name[-1])# и записываем последню часть полученного масива (а это имя файла) в список показанных файлов
                kategories.append(pic_file_name[-2])
                #print('pic_file_list=',pic_file_list[-1])
                #print('pic_file_name=',pic_file_name[-1])
                #print('pic_list=',pic_list[-1])
            del metkabuf[0]#удаляем первый элемент метки, т.к. он не используется
            print(kategories)
            
    print ("R len:",len(red))
    print ("G len:",len(green))
    print ("B len:",len(blue))
    #pi.stop()
#генерим массив цветов равный количеству категорий
    rgb=np.random.rand(len(kategories),3)
    h=timepoints[-1]/3600 
    m=timepoints[-1]%3600/60 
    s=timepoints[-1]%3600%60
    time_text='Длительность: %i:%i:%i \n' % (h, m, s)
    
    CCDnumR.clear()
    CCDnumG.clear()
    CCDnumB.clear()
    fill_list_metok_rgb()
    baud_rgb_patterns.delete('1.0',END)
    baud_rgb_patterns.insert('1.0','Файл загружен.\n')
    
def center_mass(array_mass): #наодим индекс центра масс пика
    first_point=0 #номер индекса первой точки пика
    a=[]
    
    min_cm=min(array_mass[:-1])
    max_cm=max(array_mass[:-1])
    #print(min_cm,max_cm)
    delta_cm=(max_cm-min_cm)/3 #делаем срез на высоте 1/3  емжду мин и макс значением всего графика(отслеживаем центр масс начиная с высоты 1/3 пика от основания)
    #print(delta_cm)
    #new_array=-(array_mass[:-1]-max_cm)
    massive_cm = [(max_cm-x) for x in array_mass]#перевернем массив и сделаем срез (уберем лишние данные,т.к. пик на графике один)
    #print (massive_cm)

    a[:]=(x for x in massive_cm if x>delta_cm) # берем данные, только выше линии среза
    #print (a)
    
    for i in range(len(massive_cm)): #находим индекс первой точки пика
        if massive_cm[i]>delta_cm:
            first_point=i
        break
    #print (first_point)
    y=[j for j in range(0,len(a))]#создадим массив для расчета центра масс
    #print (y)
    max_point=int( np.average(y,weights=a))#положение максимума пика относительно первой точки
    #print("индекс центра массы:",max_point+first_point)
    return(max_point+first_point) #вернем индекс максимума относительно начала CCD (ПЗС) линейки


def loadData1():
    global ydata
    global timepoints
    global metkabuf
    global kategories
    global pic_list
    global pic_file_list
    global rgb
    global g_file_name
    
    file_name = fd.askopenfilename(defaultextension='*.csv', filetypes=(("CSV files", "*.csv"),
                                                ("All files", "*.*")))
    g_file_name=file_name.split('/')
    print (g_file_name[-1])
    
    if file_name :
        f = open(file_name, 'r').read()
        timepoints=[]
        ydata=[]
    dataArray = f.split('\n')

#загружаем сырые данные
    for eachLine in dataArray: 
        if len(eachLine)>1:
            x,y = eachLine.split(';')
            timepoints.append(float(x))
            ydata.append(float(y))

    if file_name:
#загружаем файл с метками и названием показанных картинок
        #пробуем загрузить названия категорий
        metka_file=file_name[:-3]+'kat' 
        try:
            file = open(metka_file,'r').read()
        except IOError as e:
            print(u'файл с категориями не существует')
            metkabuf=[]
            pic_list=[]
            pic_file_list=[]
        else:
            #print(u'заносим метки в базу данных')
            buf=[]
            metkabuf=[]
            pic_list=[]
            pic_file_list=[]
            kategories=[]
            metkaArray = file.split('\n')
            for eachLine in metkaArray:
              if len(eachLine)>0:
                buf=eachLine.split(';') #делим полученную строку на 2 части. разделитель ";"
                metkabuf.append(int(buf[0]))#первая часть - отметка. заносим её в буфер

                #теперь получаем список файлов для каждой отметки
                pic_file_list.append(str(buf[-1]))
                pic_file_name=pic_file_list[-1].split('\\')#делим строку на части, где разделить "\"
                pic_list.append(pic_file_name[-1])# и записываем последню часть полученного масива (а это имя файла) в список показанных файлов
                kategories.append(pic_file_name[-2])
            del metkabuf[0]#удаляем первый элемент метки, т.к. он не используется
            print(kategories)

#генерим массив цветов равный количеству категорий
    rgb=np.random.rand(len(kategories),3) 
 
    baud.delete('1.0',END)
    #baud.insert('1.0', "Файл прочитан \n")
    
    h=timepoints[-1]/3600 
    m=timepoints[-1]%3600/60 
    s=timepoints[-1]%3600%60
    time_text='Длительность: %i:%i:%i \n' % (h, m, s)
    baud.insert('1.0', time_text)

    baud.insert(END, str('Данных: '+str(len(ydata))))
    baud.insert(END, str('\nМеток: '+str(len(metkabuf))))

    fill_list_metok()
    
def save_rgb_patterns(color='r'):
    global g_file_name
    global ydata
    global timepoints
    global pic_list
    global pic_file_list
    global kategories

    #очищаем текстовое поле
    baud_rgb_patterns.delete('1.0',END)
    if g_file_name:
    #записываем файлы
        j=0
        ydata=[]
        if color=='r':
            
            ydata=red[:]
        elif color=='g':
            
            ydata=green[:]
        elif color=='b':
            
            ydata=blue[:]
            
        while j<len(pic_file_list):
            file_name=g_file_name[-1][:-4]+'_'+pic_list[j]+'_'+str(j)+'.csv'
            file_name_full='.\\save_patterns_rgb\\'+kategories[j]+'_'+color+'\\'+file_name

        #если не существует каталога с таким названием категории, то создадим его
            if not os.path.exists('.\\save_patterns_rgb\\'+kategories[j]+'_'+color):
                os.makedirs('.\\save_patterns_rgb\\'+kategories[j]+'_'+color)
            
            f = open(file_name_full, 'w')        
               
            if j==0:
                i=0 
                while i < metkabuf[0]:
                    f.write(str(timepoints[i])+';'+str(ydata[i])+'\n')
                    i +=1
            elif j==len(metkabuf):
                i=metkabuf[-1]
                while i < len(ydata):
                    f.write(str(timepoints[i])+';'+str(ydata[i])+'\n')
                    i +=1
            else:
                i=metkabuf[j-1]
                while i < metkabuf[j]:
                    f.write(str(timepoints[i])+';'+str(ydata[i])+'\n')
                    i +=1
            f.close()   
            j=j+1
        baud_rgb_patterns.insert(END, str('Записано паттернов '+color+': '+str(j)))
    else:
        baud_rgb_patterns.insert(END, str('Файл данных не загружен'))
        
def load_rgb_patterns():
    global patterns
    global ydata_patterns
    global timepoints_patterns
    global trainingSet
    global folder
    global patterns_kat
    print('\nЗагружем файлы паттернов...')
    trainingSet=[]

    #загрузим списки паттернов(на всякий случай):
    #init_list_rgb_patterns()

    baud_rgb_patterns.insert(END,'загружаем паттерны..\n')
         
       #проверим, существуют ли папки с паттернами
    if not os.path.exists('.\save_patterns_rgb'):
        baud_rgb_patterns.delete('1.0',END)
        baud_rgb_patterns.insert('1.0','папка с паттернами не найдена!!!\n')
        list_rgb_patterns.delete(0,END)
        return()
    else:
        baud_rgb_patterns.delete('1.0',END)
        baud_rgb_patterns.insert('1.0','загружаем паттерны..\n')

    #составим список папок:
    folder=[]
    for i in os.walk(".\save_patterns_rgb"):
        folder.append(i)
    
    print('каталоги:',folder[0][1])
    patterns_kat=folder[0][1]
    if len(folder[0][1])==0:
        baud_rgb_patterns.delete('1.0',END)
        baud_rgb_patterns.insert('1.0','паттернов в каталоге нет\n')
        list_rgb_patterns.delete('1.0', END) #очистим список паттернов
    
#подгрузим паттерны в память
    i=0
    timepoints_patterns.clear()
    ydata_patterns.clear()
#формируем список в массиве:patterns[i][j][z], где каталог - i, файл - j, данные - z.
    while i<len(folder[0][1]): #счетчик категорий(каталогов)
        j=0
        timepoints_patterns.append([]) #добавляем в массив список (элемент списка), в котором будут данные файлов из этого каталога
        ydata_patterns.append([])            
        while j<len(folder[i+1][2]):
            file_pattern=str(folder[i+1][0]+'\\'+folder[i+1][2][j]) #получаем название файла в этом каталоге
        #загружаем сырые данные
            f = open(file_pattern, 'r').read()
            dataArray = f.split('\n')
            timepoints_patterns[i].append([]) # добавляем в i-ую позицию (каталог i), данные файлов с порядковым номером j
            ydata_patterns[i].append([])

            t0=0 # приведем все временнЫе интервалы к отрезку [0:max] ( т.к. многие паттерны начинаются с 20 секунды и более)
            z=0 #счетчик данных
            for eachLine in dataArray:                
                if len(eachLine)>1:
                    t,y = eachLine.split(';')
                    timepoints_patterns[i][j].append(float(t))
                    ydata_patterns[i][j].append(float(y))
                    if z==0:#записываем первое значение временнОго ряда в t0
                        t0=float(t)
                    timepoints_patterns[i][j][-1]=timepoints_patterns[i][j][-1]-t0 # приводим все значения временнОго ряда к отрезку от 0 до максимума
                        
                z=z+1
            #print(timepoints[i][j])
            #print (file_pattern)
            
            j=j+1
        i=i+1
    #print(timepoints)
    print('Файлы паттернов загружены\n')
    print('кол-во паттернов:',len(ydata_patterns))
    baud_rgb_patterns.delete('1.0',END)
    baud_rgb_patterns.insert('1.0','паттерны загружены\n')
    list_rgb_patterns.delete(0, END) #очистим список паттернов
    i=0
    while i<len(folder[0][1]):
        count=len(folder[i+1][2])
        list_rgb_patterns.insert(END,str(folder[0][1][i]+': '+str(count)+' шт'))
        #print(str(folder[0][1][i])+': '+str(count)+' шт')
        i=i+1
        
def init_list_rgb_patterns():
    global patterns
    global patterns_kat

    
    #проверим, существуют ли папки с паттернами
    if not os.path.exists('.\save_patterns_rgb'):
        baud_patterns.delete('1.0',END)
        baud_patterns.insert('1.0','папка с паттернами не найдена!!!\n')
        list_patterns.delete(0,END)
        return()
    else:
         baud_patterns.delete('1.0',END)
         baud_patterns.insert('1.0','списки паттернов загружены\n')

    #составим список папок:
    folder=[]
    for i in os.walk(".\save_patterns_rgb"):
       folder.append(i)
    
    print('каталоги ф-ии init:',folder[0][1])
    patterns_kat=folder[0][1]
    if len(folder[0][1])==0:
        baud_patterns.delete('1.0',END)
        baud_patterns.insert('1.0','паттернов в каталоге нет\n')
        
    

    #выведем список категорий и кол-во файлов в них:

    list_patterns.delete(0, END) #очистим список паттернов

    i=0
    while i<len(folder[0][1]):
        count=len(folder[i+1][2])
        list_patterns.insert(END,str(folder[0][1][i]+': '+str(count)+' шт'))
        #print(str(folder[0][1][i])+': '+str(count)+' шт')
        i=i+1
        
def save_pattern(color=' '):
    global g_file_name
    global ydata
    global timepoints
    global pic_list
    global pic_file_list
    global kategories

    #очищаем текстовое поле
    baud_patterns.delete('1.0',END)
    if g_file_name:
    #записываем файлы
        j=0
        while j<len(pic_file_list):
            file_name=g_file_name[-1][:-4]+'_'+pic_list[j][:-4]+'_'+str(j)+'.csv'
            file_name_full='.\\save_patterns\\'+kategories[j]+'\\'+file_name

        #если не существует каталога с таким названием категории, то создадим его
            if not os.path.exists('.\\save_patterns\\'+kategories[j]):
                os.makedirs('.\\save_patterns\\'+kategories[j])
            
            f = open(file_name_full, 'w')        
               
            if j==0:
                i=0 
                while i < metkabuf[0]:
                    f.write(str(timepoints[i])+';'+str(ydata[i])+'\n')
                    i +=1
            elif j==len(metkabuf):
                i=metkabuf[-1]
                while i < len(ydata):
                    f.write(str(timepoints[i])+';'+str(ydata[i])+'\n')
                    i +=1
            else:
                i=metkabuf[j-1]
                while i < metkabuf[j]:
                    f.write(str(timepoints[i])+';'+str(ydata[i])+'\n')
                    i +=1
            f.close()   
            j=j+1
        baud_patterns.insert(END, str('Записано паттернов: '+str(j)))
    else:
        baud_patterns.insert(END, str('Файл данных не загружен'))
    
def save_pattern2():
    global g_file_name2
    global ydata2
    global timepoints2
    global pic_list2
    global pic_file_list2
    global kategories2

    #очищаем текстовое поле
    baud_patterns.delete('1.0',END)
    if g_file_name2:
    #записываем файлы
        j=0
        while j<len(pic_file_list2):
            file_name=g_file_name2[-1][:-4]+'_'+pic_list2[j][:-4]+'_'+str(j)+'.csv'
            file_name_full='.\\save_patterns\\'+kategories2[j]+'\\'+file_name

        #если не существует каталога с таким названием категории, то создадим его
            if not os.path.exists('.\\save_patterns\\'+kategories2[j]):
                os.makedirs('.\\save_patterns\\'+kategories2[j])
            
            f = open(file_name_full, 'w')        
               
            if j==0:
                i=0 
                while i < metkabuf2[0]:
                    f.write(str(timepoints2[i])+';'+str(ydata2[i])+'\n')
                    i +=1
            elif j==len(metkabuf2):
                i=metkabuf2[-1]
                while i < len(ydata2):
                    f.write(str(timepoints2[i])+';'+str(ydata2[i])+'\n')
                    i +=1
            else:
                i=metkabuf2[j-1]
                while i < metkabuf2[j]:
                    f.write(str(timepoints2[i])+';'+str(ydata2[i])+'\n')
                    i +=1
            f.close()   
            j=j+1
        baud_patterns.insert(END, str('Записано паттернов 2: '+str(j)))
    else:
        baud_patterns.insert(END, str('Файл данных не загружен'))
    
def loadData2():
    global ydata2
    global timepoints2
    global metkabuf2
    global kategories2
    global pic_list2
    global pic_file_list2
    global rgb
    global g_file_name2
    
    file_name = fd.askopenfilename(defaultextension='*.csv', filetypes=(("CSV files", "*.csv"),
                                                ("All files", "*.*")))
    g_file_name2=file_name.split('/')
    print (g_file_name2[-1])
    
    if file_name :
        f = open(file_name, 'r').read()
        timepoints2=[]
        ydata2=[]
    dataArray = f.split('\n')

#загружаем сырые данные
    for eachLine in dataArray: 
        if len(eachLine)>1:
            x,y = eachLine.split(';')
            timepoints2.append(float(x))
            ydata2.append(float(y))
          


    if file_name:
#загружаем файл с метками и названием показанных картинок
        #пробуем загрузить названия категорий
        metka_file=file_name[:-3]+'kat' 
        try:
            file = open(metka_file,'r').read()
        except IOError as e:
            print(u'файл с категориями не существует')
            metkabuf2=[]
            pic_list2=[]
            pic_file_list2=[]
        else:
            #print(u'заносим метки в базу данных')
            buf=[]
            metkabuf2=[]
            pic_list2=[]
            pic_file_list2=[]
            kategories2=[]
            metkaArray = file.split('\n')
            for eachLine in metkaArray:
              if len(eachLine)>0:
                buf=eachLine.split(';') #делим полученную строку на 2 части. разделитель ";"
                metkabuf2.append(int(buf[0]))#первая часть - отметка. заносим её в буфер

                #теперь получаем список файлов для каждой отметки
                pic_file_list2.append(str(buf[-1]))
                pic_file_name=pic_file_list2[-1].split('\\')#делим строку на части, где разделить "\"
                pic_list2.append(pic_file_name[-1])# и записываем последню часть полученного масива (а это имя файла) в список показанных файлов
                kategories2.append(pic_file_name[-2])# записываем категорию файла
            del metkabuf2[0]#удаляем первый элемент метки, т.к. он не используется
            print(kategories2)

    if len(kategories2)>len(kategories):
       rgb=np.random.rand(len(kategories2),3)
       
    baud.delete('1.0',END)
    
    h=timepoints2[-1]/3600 
    m=timepoints2[-1]%3600/60 
    s=timepoints2[-1]%3600%60
    time_text='Длительность 2 файла: %i:%i:%i \n' % (h, m, s)
    baud.insert('1.0', time_text)

    baud.insert(END, str('Данных: '+str(len(ydata2))))
    baud.insert(END, str('\nМеток: '+str(len(metkabuf2))))

    fill_list_metok2()

    
def plt_text(x1,x2,y):#выводим на экран среднее значение
    global timepoints
    global pic_list
    

    xm = np.mean(ydata[x1:x2])  # среднее значение
    xs = np.std(ydata[x1:x2])

    x=x1
    peregib=0
    if x2>0:
        while x<(x2-1):
            if (ydata[x]<xm) & (ydata[x+1]>xm):
                peregib=peregib+1
            elif (ydata[x]>xm) & (ydata[x+1]<xm):
                peregib=peregib+1
            else:
                peregib=peregib
            x=x+1
    elif x2==-1:
        while x<(len(ydata)-1):
            if (ydata[x]<xm) & (ydata[x+1]>xm):
                peregib=peregib+1
            elif (ydata[x]>xm) & (ydata[x+1]<xm):
                peregib=peregib+1
            else:
                peregib=peregib
            x=x+1
        
    x_pos=int(timepoints[x1]+(timepoints[x2]-timepoints[x1])/2)
    # выводим среднее
    plt.text(x_pos, xm+xs*2, 'ср.: %.3f'%(xm), verticalalignment='bottom', horizontalalignment='left',color='black')#,bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 10})
    #выводим кол-во перегибов
    plt.text(x_pos, xm+xs, peregib, verticalalignment='bottom', horizontalalignment='left',color='r')#bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 10})

    # выводим название картинки
    maxy=plt.ylim()
    #print(0.2*(maxy[1]-maxy[0])*(y%2))
    if len(pic_list)>0:
        plt.text(x_pos, maxy[0]+0.1*(maxy[1]-maxy[0])*(y%2), pic_list[y][:-4], verticalalignment='bottom', horizontalalignment='left',color='black')#,bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 10})
    

def plt_text2(x1,x2,y):#выводим на экран среднее значение и среднекв.откл
    global ydata2
    global timepoints2
    global pic_list2

    xm = np.mean(ydata2[x1:x2])  # среднее значение
    xs = np.std(ydata2[x1:x2])

    x=x1
    peregib=0
    if x2>0:
        while x<(x2-1):
            if (ydata2[x]<xm) & (ydata2[x+1]>xm):
                peregib=peregib+1
            elif (ydata2[x]>xm) & (ydata2[x+1]<xm):
                peregib=peregib+1
            else:
                peregib=peregib
            x=x+1
    elif x2==-1:
        while x<(len(ydata2)-1):
            if (ydata2[x]<xm) & (ydata2[x+1]>xm):
                peregib=peregib+1
            elif (ydata2[x]>xm) & (ydata2[x+1]<xm):
                peregib=peregib+1
            else:
                peregib=peregib
            x=x+1

    
    x_pos=int(timepoints2[x1]+(timepoints2[x2]-timepoints2[x1])/2)
    # выводим среднее
    plt.text(x_pos, xm+xs*2, 'ср.: %.3f'%(xm), verticalalignment='bottom', horizontalalignment='left',color='black')#,bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 10})
    #выводим кол-во перегибов
    plt.text(x_pos, xm+xs, peregib, verticalalignment='bottom', horizontalalignment='left',color='r')#bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 10})

    # выводим название картинки
    maxy=plt.ylim()    
    if len(pic_list2)>0:
        plt.text(x_pos, maxy[0]+0.1*(maxy[1]-maxy[0])*(y%2), pic_list2[y][:-4], verticalalignment='bottom', horizontalalignment='left',color='black')#,bbox={'facecolor': 'white', 'alpha': 0.7, 'pad': 10})


def analisSignalRgb(file='rgb_spectr.png'): #вывод трех сигналов на экран, с временнЫми отметками 
     global ydata
     global timepoints
     global metkabuf
     global plav_okno
     global pic_list

     plav_okno=int(okno_entry.get())
     if len(timepoints)==0:
         timepoints=[i for i in range(len(red))]

     if len(ydata_rgb)>0:
         
         plt.figure(num=1,figsize=(17, 8),clear=True)
         plt.subplots_adjust(left=0.05,bottom=0.06,right=0.99,top=0.96)
         
         plt.grid(True)# включаем сетку
        #вычислим максимум и минимум графика
         
         ax1=plt.subplot2grid((3,1),(0,0))
         ax2=plt.subplot2grid((3,1),(1,0))
         ax3=plt.subplot2grid((3,1),(2,0))
         plt.setp(ax1.get_xticklabels(), visible=False)
         plt.setp(ax2.get_xticklabels(), visible=False)
         ax1.set_title('RGB - изменение длины волн')
         ax2.set_ylabel('Длина волны [nm]')
         
         if len(metkabuf)<1:
             #plt.subplot(3,1,1)
             ax1.grid(True)
             #plt.title('RGB - изменение длины волн')
             ax1.plot(timepoints,red,color='r')
             #plt.subplot(3,1,2)
             ax2.grid(True)
             ax2.plot(timepoints,green,color='g')
             #plt.subplot(3,1,3)
             ax3.grid(True)
             ax3.plot(timepoints,blue,color='b')   
             #ydata=red # вывод точек интерполяции,'o',interp_timepoints, interp_ydata,'.')
             #plt_text(0,-1) #выводим на экран среднее значение и среднекв.откл
             #plt_text(0,-1)
             #plt_text(0,-1)
         else:
             #plt.subplot(3,1,1)
             ax1.grid(True)
             #plt.title('RGB - изменение длины волн')
             ax1.plot(timepoints[:metkabuf[0]],np.array(red[:metkabuf[0]])*0.0098+red_mid,color='r') #пиксель линейки шириной 8мкм (1 писель соответствует 0.0098нм). всего  3648 пикселей.ширина линейки 29.1мм. выхватываемый спектр шириной 35.7нм
             #plt.subplot(3,1,2)
             ax2.grid(True)
             ax2.plot(timepoints[:metkabuf[0]],np.array(green[:metkabuf[0]])*0.0098+green_mid,color='g')
             #plt.subplot(3,1,3)
             ax3.grid(True)
             ax3.plot(timepoints[:metkabuf[0]],np.array(blue[:metkabuf[0]])*0.0098+blue_mid,color='b')
             plt_text_rgb(0,metkabuf[0],0,ax3)
         #ylimit=plt.ylim()
         #print('ylimit=',ylimit)
         if len(metkabuf)>0:
                i=1
                while i < len(metkabuf):
                    #plt.subplot(3,1,1)
                    ax1.plot(timepoints[metkabuf[i-1]:metkabuf[i]],np.array(red[metkabuf[i-1]:metkabuf[i]])*0.0098+red_mid,color='r')
                    #plt.subplot(3,1,2)
                    ax2.plot(timepoints[metkabuf[i-1]:metkabuf[i]],np.array(green[metkabuf[i-1]:metkabuf[i]])*0.0098+green_mid,color='g')
                    #plt.subplot(3,1,3)
                    ax3.plot(timepoints[metkabuf[i-1]:metkabuf[i]],np.array(blue[metkabuf[i-1]:metkabuf[i]])*0.0098+blue_mid,color='b')
                    #выводим вертикальную линию для разделения графиков
                    #plt.subplot(3,1,1)
                    ylimit=ax1.get_ylim()
                    ax1.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='black')
                    #plt.subplot(3,1,2)
                    ylimit=ax2.get_ylim()
                    ax2.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='black')
                    #plt.subplot(3,1,3)
                    ylimit=ax3.get_ylim()
                    ax3.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='black')

                    #выводим на экран название картинок
                    
                    plt_text_rgb(metkabuf[i-1],metkabuf[i],i,ax3)
                    i=i+1                    
# выводим сигнал от последней метки до конца сигнала
                #plt.subplot(3,1,1)
                ax1.plot(timepoints[metkabuf[i-1]:],np.array(red[metkabuf[i-1]:])*0.0098+red_mid,color='r')
                #plt.subplot(3,1,2)
                ax2.plot(timepoints[metkabuf[i-1]:],np.array(green[metkabuf[i-1]:])*0.0098+green_mid,color='g')
                #plt.subplot(3,1,3)
                ax3.plot(timepoints[metkabuf[i-1]:],np.array(blue[metkabuf[i-1]:])*0.0098+blue_mid,color='b')
                #выводим вертикальную линию для разделения графиков
                #plt.subplot(3,1,1)
                ylimit=ax1.get_ylim()
                ax1.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='black')
                #plt.subplot(3,1,2)
                ylimit=ax2.get_ylim()
                ax2.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='black')
                #plt.subplot(3,1,3)
                ylimit=ax3.get_ylim()
                ax3.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='black')
                
                
                plt_text_rgb(metkabuf[i-1],-1,i,ax3)#выводим на экран название картинки

#выводим график плавающего среднего,ср.кв.откл и дисперсии
         mean_data=pd.Series(np.array(red)*0.0098+red_mid,index=timepoints)
         ma=mean_data.rolling(plav_okno).mean()
         mstd=mean_data.rolling(plav_okno).std()
         mvar=mean_data.rolling(plav_okno).var()
         #plt.subplot(3,1,1)
         ax1.plot(ma.index,ma,color='grey',label='Среднее') #вывод среднего
         #if disp_view.get()==1:
         #      plt.plot(mvar.index,mvar,color='blue',label='Дисперсия')
         #вывод ср.кв отклонения      
         #plt.fill_between(mstd.index, ma-2*mstd, ma+2*mstd, color='black', alpha=0.2,label='ср.кв.отклонение')

         mean_data=pd.Series(np.array(green)*0.0098+green_mid,index=timepoints)
         ma=mean_data.rolling(plav_okno).mean()
         mstd=mean_data.rolling(plav_okno).std()
         mvar=mean_data.rolling(plav_okno).var()
         #plt.subplot(3,1,2)
         ax2.plot(ma.index,ma,color='grey')#,label='Среднее')

         #if disp_view.get()==1:
         #      plt.plot(mvar.index,mvar,color='blue',label='Дисперсия')
         #вывод ср.кв отклонения       
         #plt.fill_between(mstd.index, ma-2*mstd, ma+2*mstd, color='black', alpha=0.2)#,label='ср.кв.отклонение')

         mean_data=pd.Series(np.array(blue)*0.0098+blue_mid,index=timepoints)
         ma=mean_data.rolling(plav_okno).mean()
         mstd=mean_data.rolling(plav_okno).std()
         mvar=mean_data.rolling(plav_okno).var()
         #plt.subplot(3,1,3)
         ax3.plot(ma.index,ma,color='grey')#,label='Среднее')
         #if disp_view.get()==1:
         #      plt.plot(mvar.index,mvar,color='blue',label='Дисперсия')
         #вывод ср.кв отклонения       
         #plt.fill_between(mstd.index, ma-2*mstd, ma+2*mstd, color='black', alpha=0.2)#,label='ср.кв.отклонение')
         
         #plt.subplot(3,1,1)
         ax1.legend()

         #plt.title('RGB - изменение длины волн')
         plt.xlabel('Время [сек]')
         #plt.ylabel('Длина волны [nm]')        
         plt.show()
         
def plt_text_rgb(x1,x2,y,ax):
     #print('выводим название отрезка')
     #ylimit=plt.ylim()
     #plt.subplot(3,1,3)

     maxy=ax.get_ylim()
     #print('ylimit=',maxy)
     x_pos=int(timepoints[x1]+(timepoints[x2]-timepoints[x1])/2)
     #print('x_pos=',x_pos)
     print('pic_list=',pic_list[y])
     if len(pic_list)>0:
             ax.text(x_pos, maxy[0]+0.1*(maxy[1]-maxy[0])*(y%2), pic_list[y], verticalalignment='bottom', horizontalalignment='left',color='red')
     return ax
    
def analisSignal(file='test.png',show=1,save=0):
#выводим графики сигнала+спектрограмма
    
    global ydata
    global timepoints
    global metkabuf
    global plav_okno
    global pic_list

    plav_okno=int(okno_entry.get())
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики
  
# первый график Принятого сигнала
        plt.figure(num=1,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.04,bottom=0.14,right=0.96,top=0.9)
                
        if len(metkabuf)<1:
            plt.plot(timepoints, ydata,ls=':')# вывод точек интерполяции,'o',interp_timepoints, interp_ydata,'.')
            plt_text(0,-1) #выводим на экран среднее значение и среднекв.откл
        else:
            plt.plot(timepoints[:metkabuf[0]],ydata[:metkabuf[0]],ls=':')
            plt_text(0,metkabuf[0],0)
        plt.title('Принятый сигнал 1')
        plt.xlabel('Время [сек]')
        plt.ylabel('Длина волны [nm]')
        plt.grid(True)# включаем сетку
        #вычислим максимум и минимум графика
        ylimit=plt.ylim()
        #print(ylimit)
#2-i график - сигнал между отметками       
        if len(metkabuf)>0:
                i=1
                while i < len(metkabuf):
                    plt.plot(timepoints[metkabuf[i-1]:metkabuf[i]],ydata[metkabuf[i-1]:metkabuf[i]],color=rgb[i-1],ls=':')
                    #выводим вертикальную линию для разделения графиков                    
                    plt.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='r')

                    #выводим на экран среднее значение и среднекв.откл 
                    plt_text(metkabuf[i-1],metkabuf[i],i)
                    i=i+1                    
# выводим сигнал от последней метки до конца сигнала
                plt.plot(timepoints[metkabuf[i-1]:],ydata[metkabuf[i-1]:],color=rgb[i-1],ls=':')
                #выводим вертикальную линию для разделения графиков                    
                plt.plot([timepoints[metkabuf[i-1]],timepoints[metkabuf[i-1]]],ylimit,color='r')
                plt_text(metkabuf[i-1],-1,i)#выводим на экран среднее значение и среднекв.откл

#выводим график плавающего среднего,ср.кв.откл и дисперсии
        mean_data=pd.Series(ydata,index=timepoints)
        ma=mean_data.rolling(plav_okno).mean()
        mstd=mean_data.rolling(plav_okno).std()
        mvar=mean_data.rolling(plav_okno).var()
        plt.plot(ma.index,ma,color='black',label='Среднее')
        if disp_view.get()==1:
           plt.plot(mvar.index,mvar,color='blue',label='Дисперсия')
        plt.fill_between(mstd.index, ma-2*mstd, ma+2*mstd, color='black', alpha=0.2,label='ср.кв.отклонение')
        plt.legend()

        if save==1:
            plt.savefig(file[:-4]+' сигнал.png')
        if show==1:
            plt.show()
        
def analisFFT(file='test.png',show=1,save=0,color=' '):
#выводим графики сигнала+FFT
    
    global ydata
    global timepoints
    global metkabuf

    if color=='r':
        if isinstance(ydata,list):
            ydata=[]
        ydata=np.array(red[:])*0.0098+red_mid
        title_text='Спектр канала R'
    elif color=='g':
        if isinstance(ydata,list):
            ydata=[]
        ydata=np.array(green[:])*0.0098+green_mid
        title_text='Спектр канала G'
    elif color=='b':
        if isinstance(ydata,list):
            ydata=[]
        ydata=np.array(blue[:])*0.0098+blue_mid
        title_text='Спектр канала B'
    else:
        title_text='Спектр всего сигнала 1'
#вычисляем время квантования (время между приемом двух сигналов)
    time_step = (timepoints[-1]-timepoints[0])/len(ydata)
     
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики
        
        w=1 #разбивка экрана на 3 ряда графиков
        h=1
            
        plt.figure(num=2,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.05,bottom=0.07,right=0.99,top=0.95,hspace=0.4)
        plt.subplot(h,w,1)
        
       
        plt.title(title_text)
        if len(metkabuf)<1:
            plt.xlabel('Частота [Гц]')
        plt.ylabel('Мощность [отн.ед.]')
        plt.grid(True)# включаем сетку

        sig_fft = fftpack.rfft(ydata)
        N=int(len(sig_fft))
        power = np.abs(sig_fft)# считаем фурье преобразование
        sample_freq=fftpack.rfftfreq(len(ydata),d=time_step)

        plt.plot(sample_freq[1:-1],2*power[1:-1]/N)
        plt.show()      
        
def analisHist(file='test.png',show=1,save=0,color=' '):
#выводим графики сигнала Гистограмма
    
    global ydata
    global timepoints
    global metkabuf

    mu = 100  # mean of distribution
    sigma = 15  # standard deviation of distribution

    if color=='r':
        if isinstance(ydata,list):
            ydata=[]
        ydata=np.array(red[:])*0.0098+red_mid
        title_text='Гистограмма канала R'
    elif color=='g':
        if isinstance(ydata,list):
            ydata=[]
        ydata=np.array(green[:])*0.0098+green_mid
        title_text='Гистограмма канала G'
    elif color=='b':
        if isinstance(ydata,list):
            ydata=[]
        ydata=np.array(blue[:])*0.0098+blue_mid
        title_text='Гистограмма канала B'
    else:
        title_text='Гистограмма всего сигнала 1'
        
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.figure(num=3,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)
        w=1
        h=1
        plt.subplot(h,w,1)
        n,bins,patches=plt.hist(ydata,bins='auto',density=True,stacked=True)
        
        plt.title(title_text)
        if len(metkabuf)<1:
            plt.xlabel('Длина волны [nm]')
        plt.ylabel('Плотность расределения')
        plt.grid(True)
        #plt.xlim(525, 540)
        plt.plot()
        plt.show()      

def deltaHist(file='test.png',show=1,save=0):
    global ydata
    global timepoints
    global metkabuf
    global ydata
    global pic_list

    select_metka=[]
    select_metka=list_metok.curselection() #получаем список выделенных элементов

    
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.figure(num=6,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)

        plt.title('Гистограмма сравниваемых сигналов 1')
        plt.xlabel('Длина волны [nm]')
        plt.ylabel('Плотность расределения')
        plt.grid(True)
        #plt.xlim(525, 540)
        
        if len(select_metka)>0:
                i=0
                while i < len(select_metka):
                    #print(i)
                    #print(select_metka[i])
                    if select_metka[i]==0:
                       n,bins,patches=plt.hist(ydata[:metkabuf[0]], bins='auto',density=True,stacked=True,alpha=0.5,label=pic_list[select_metka[i]])#,label=str('Спектр от 0 до '+str(int(timepoints[metkabuf[0]]))+' сек'))
                    elif select_metka[i]==len(metkabuf):
                       n,bins,patches=plt.hist(ydata[metkabuf[-1]:-1],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[len(metkabuf)-1],label=pic_list[select_metka[i]])#,label='x')
                    else:
                       n,bins,patches=plt.hist(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]]],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[select_metka[i]-1],label=pic_list[select_metka[i]])
                    #plt.title(str('от '+str(int(timepoints[metkabuf[i-1]]))+' до '+str(int(timepoints[metkabuf[i]]))+' сек'))
                    i=i+1
        plt.legend()
        plt.plot()
        plt.show()             


def fill_list_metok(): #заполняем список отметок для графиков сравнения
    global timepoints
    global metkabuf
    global kategories
    global pic_list

    list_metok.delete(0, END) #очистим список 
    
    if len(metkabuf)>0:
        list_metok.insert(END,str(pic_list[0][:-4]+' :от 0 до '+str(int(timepoints[metkabuf[0]]))+' сек:'))
        i=1
        while i < len(metkabuf):
            list_metok.insert(END,str(pic_list[i][:-4]+' :от '+str(int(timepoints[metkabuf[i-1]]))+' до '+str(int(timepoints[metkabuf[i]]))+' сек'))
            i=i+1
        list_metok.insert(END,str(pic_list[i][:-4]+' :от '+str(int(timepoints[metkabuf[i-1]]))+' до конца'))
                


def fill_list_metok2(): #заполняем список отметок для графиков сравнения
    global timepoints2
    global metkabuf2
    global kategories2
    global pic_list2

    list_metok2.delete(0, END) #очистим список 
    
    if len(metkabuf2)>0:
        list_metok2.insert(END,str(pic_list2[0][:-4]+' :от 0 до '+str(int(timepoints2[metkabuf2[0]]))+' сек:'))
        i=1
        while i < len(metkabuf2):
            list_metok2.insert(END,str(pic_list2[i][:-4]+' :от '+str(int(timepoints2[metkabuf2[i-1]]))+' до '+str(int(timepoints2[metkabuf2[i]]))+' сек'))
            i=i+1
        list_metok2.insert(END,str(pic_list2[i][:-4]+' :от '+str(int(timepoints2[metkabuf2[i-1]]))+' до конца'))

def fill_list_metok_rgb(): #заполняем список отметок для графиков сравнения
    global timepoints
    global metkabuf
    global kategories
    global pic_list

    print('pic_list=',pic_list)
    print('metkabuf=',metkabuf)
    print('len(timepoints)=',len(timepoints))
    list_rgb_metok.delete(0, END) #очистим список 
    
    if len(metkabuf)>0:
        list_rgb_metok.insert(END,str(pic_list[0]+' :от 0 до '+str(int(timepoints[metkabuf[0]]))+' сек:'))
        i=1
        while i < len(metkabuf):
            list_rgb_metok.insert(END,str(pic_list[i]+' :от '+str(int(timepoints[metkabuf[i-1]]))+' до '+str(int(timepoints[metkabuf[i]]))+' сек'))
            i=i+1
        list_rgb_metok.insert(END,str(pic_list[i]+' :от '+str(int(timepoints[metkabuf[i-1]]))+' до конца'))
        
        
def tetaDelta():
    select_metka=[]
    select_metka=list_metok.curselection()
    print (select_metka)

def tetaDelta2():
    select_metka2=[]
    select_metka2=list_metok2.curselection()
    print (select_metka)


def deltaFFT(file='test.png',show=1,save=0):
#выводим сравнение графиков сигнала FFT
    
    global ydata
    global timepoints
    global metkabuf
    global pic_list
    


    select_metka=[]
    select_metka=list_metok.curselection() #получаем список выделенных элементов
     
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики

        #вычисляем время квантования (время между приемом двух сигналов)
        #получается в районе 10-50 миллисекунд
        time_step = (timepoints[-1]-timepoints[0])/len(ydata)
        
        plt.figure(num=7,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.05,bottom=0.07,right=0.99,top=0.95,hspace=0.4)
        plt.title("Сравниваемые спектры 1")
        plt.xlabel('Частота [Гц]')
        plt.ylabel('Мощность [отн.ед.]')
        plt.grid(True)

#график - фурье спектр сигнала на разных промежутках времени     
        if len(select_metka)>0:
                i=0
                while i < len(select_metka):

                  if select_metka[i]==0: #если выбран первый отрезок времени
                      sig_fft = fftpack.rfft(ydata[:int(metkabuf[0])])
                      N=len(sig_fft)
                      power = np.abs(sig_fft)
                      sample_freq=fftpack.rfftfreq(len(ydata[:int(metkabuf[0])]),d=time_step)
                      #power_avarage=np.average(2*power[1:N]/N)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,label=pic_list[select_metka[i]])
                      #x=[1,80]
                      #y=[power_avarage,power_avarage]
                      #plt.plot(x,y)

                # выводим спектр сигнала от последней метки до конца сигнала
                  elif select_metka[i]==len(metkabuf):
                      sig_fft = fftpack.rfft(ydata[int(metkabuf[-1]):-1])
                      N=int(len(sig_fft))
                      power = np.abs(sig_fft)
                      sample_freq=fftpack.rfftfreq(len(ydata[int(metkabuf[-1]):-1]),d=time_step)
                     # power_avarage=np.average(2*power[1:N]/N)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[len(metkabuf)-1],label=pic_list[select_metka[i]])
                      #plt.plot(sample_freq[1:N],power_avarage,color=rgb[len(metkabuf)-1])
                  else:
                      sig_fft = fftpack.rfft(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]]])
                      N=int(len(sig_fft))
                      power = np.abs(sig_fft)# считаем фурье преобразование
                      sample_freq=fftpack.rfftfreq(len(ydata[int(metkabuf[select_metka[i]-1]):int(metkabuf[select_metka[i]])]),d=time_step)
                      #power_avarage=np.average(2*power[1:N]/N)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[select_metka[i]-1],label=pic_list[select_metka[i]])
                     # plt.plot(sample_freq[1:N], power_avarage,color=rgb[select_metka[i]-1])
                  i=i+1

                plt.plot()
                plt.legend()
        plt.show()      

def running_mean(x, N): #скользящее среднее
        cumsum = np.cumsum(np.insert(x, 0, 0)) 
        return (cumsum[N:] - cumsum[:-N]) / N
    
def a_correlation():
    global ydata
    global timepoints
    
    #data=pd.Series(ydata,index=timepoints)
    plt.figure(num=8,figsize=(14, 6),clear=True)
    autocorrelation_plot(ydata)
    plt.show()  

def barGraph(file='test.png',show=1,save=0): # столбчатая диаграмма - выводим количество принятых данных 
    global ydata
    global timepoints
    global metkabuf

    plt.figure(num=10,figsize=(14, 6),clear=True)
    plt.title("Кол-во сигналов 1")
    plt.xlabel('Длина волны [nm]')
    plt.ylabel('Кол-во отсчетов [%]')

    #plt.show() 
    
    select_metka=[]
    select_metka=list_metok.curselection() #получаем список выделенных элементов

    
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)
     
        if len(select_metka)>0:
                i=0
                while i < len(select_metka):
                    #print(i)
                    #print(select_metka[i])
                    if select_metka[i]==0:
                       signal=pd.value_counts(ydata[:metkabuf[0]]).sort_index()#сортируем список замеров
                       plt.plot(signal.div(signal.sum()*0.01)) #выводим кол-во замеров в процентном соотношении
                    elif select_metka[i]==len(metkabuf):
                       signal=pd.value_counts(ydata[metkabuf[-1]:-1]).sort_index()#.plot(alpha=0.5,color=rgb[len(metkabuf)-1])
                       plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[len(metkabuf)-1]) 
                    else:
                       signal=pd.value_counts(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]]]).sort_index()#.plot(alpha=0.5,color=rgb[select_metka[i]-1])
                       plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[select_metka[i]-1])
                    i=i+1

        plt.grid(True)
        plt.xlim(525, 540)
        plt.plot()
        plt.show()
    
#График автокорреляции
def deltaCorr(file='test.png',show=1,save=0):
    global ydata
    global timepoints
    global metkabuf
    global ydata
            
    select_metka=[]
    select_metka=list_metok.curselection() #получаем список выделенных элементов
    
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики
        plt.figure(num=9,figsize=(15, 7),clear=True)
        #plt.title('Автокорреляция отрезков')

        if len(select_metka)>0:
                i=0
                while i < len(select_metka):
                    if select_metka[i]==0:
                       autocorrelation_plot(ydata[:metkabuf[0]])
                    elif select_metka[i]==len(metkabuf):
                       autocorrelation_plot(ydata[metkabuf[-1]:-1])#,color=rgb[len(metkabuf)-1])#,label='x')
                    else:
                       autocorrelation_plot(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]]])#,color=rgb[select_metka[i]-1])
                    i=i+1

        #if save==1:
        plt.xlabel('Кол-во измерений [Шт]')
        #if show==1:
        plt.show() 
            
def help():
    plt.figure(num=50,figsize=(14, 6),clear=True)
    plt.title("Памятка")
    plt.axis('off')
    plt.text(0,0.95,'Среднее - среднее арифметическое по 100 отсчетам ', verticalalignment='bottom', horizontalalignment='left',color='black')
    plt.text(0,0.9,'Среднеквадратичное отклонение - позволяет оценить, насколько значения могут отличаться от среднего значения', verticalalignment='bottom', horizontalalignment='left',color='black')
    plt.text(0,0.75,'Дисперсия - мера отклонения от среднего значения.\n                     Высокая дисперсия позволяет предположить о сильном влиянии случайной компоненты,\n                     возможном наличии шума и аномальных значений', verticalalignment='bottom', horizontalalignment='left',color='black')
    plt.text(0,0.6,'Автокорреляция - это характеристика сигнала, которая помогает находить повторяющиеся участки сигнала или \n                               определять несущую частоту сигнала, скрытую из-за наложений шума и колебаний на других частотах', verticalalignment='bottom', horizontalalignment='left',color='black')
    plt.text(0,0.5,'Столбчатая диаграмма - аналог Гистограммы без мат обработки.\n                                           По оси X-напряжение Вольт, по оси Y - количество сигналов с таким напряжением', verticalalignment='bottom', horizontalalignment='left',color='black')
    plt.show() 
    



def analisSignal2(save=0,show=1):
    global ydata2
    global timepoints2
    global metkabuf2
    global plav_okno

    plav_okno=int(okno_entry.get())
    if len(ydata2)>0:#если данные приняты (длина буфера больше 0), то строим графики
  
# первый график Принятого сигнала
        plt.figure(num=11,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.04,bottom=0.14,right=0.96,top=0.9)
                
        if len(metkabuf2)<1:
            plt.plot(timepoints2, ydata2,ls=':')# вывод точек интерполяции,'o',interp_timepoints, interp_ydata,'.')
            plt_text2(0,-1) #выводим на экран среднее значение и среднекв.откл
        else:
            plt.plot(timepoints2[:metkabuf2[0]],ydata2[:metkabuf2[0]],ls=':')
            plt_text2(0,metkabuf2[0],0)
        plt.title('Принятый сигнал 2')
        plt.xlabel('Время [сек]')
        plt.ylabel('Длина волны [nm]')
        plt.grid(True)# включаем сетку

        ylimit=plt.ylim()
#2-i график - сигнал между отметками       
        if len(metkabuf2)>0:
                i=1
                while i < len(metkabuf2):
                    plt.plot(timepoints2[metkabuf2[i-1]:metkabuf2[i]],ydata2[metkabuf2[i-1]:metkabuf2[i]],color=rgb[i-1],ls=':')
                    plt.plot([timepoints2[metkabuf2[i-1]],timepoints2[metkabuf2[i-1]]],ylimit,color='r')
                    plt_text2(metkabuf2[i-1],metkabuf2[i],i)#выводим на экран среднее значение и среднекв.откл
                    i=i+1                    
          # выводим сигнал от последней метки до конца сигнала
                plt.plot(timepoints2[metkabuf2[i-1]:],ydata2[metkabuf2[i-1]:],color=rgb[i-1],ls=':')
                plt.plot([timepoints2[metkabuf2[i-1]],timepoints2[metkabuf2[i-1]]],ylimit,color='r')
                plt_text2(metkabuf2[i-1],-1,i)#выводим на экран среднее значение и среднекв.откл

#выводим график плавающего среднего,ср.кв.откл и дисперсии
        mean_data=pd.Series(ydata2,index=timepoints2)
        ma=mean_data.rolling(plav_okno).mean()
        mstd=mean_data.rolling(plav_okno).std()
        mvar=mean_data.rolling(plav_okno).var()
        plt.plot(ma.index,ma,color='black',label='Среднее')
        if disp_view.get()==1:
           plt.plot(mvar.index,mvar,color='blue',label='Дисперсия')
        plt.fill_between(mstd.index, ma-2*mstd, ma+2*mstd, color='black', alpha=0.2,label='ср.кв.отклонение')
        plt.legend()

        if save==1:
            plt.savefig(file[:-4]+' сигнал.png')
        if show==1:
            plt.show()
            
def analisFFT2 (file='test.png',show=1,save=0):    
    global ydata2
    global timepoints2
    global metkabuf2
    
#вычисляем время квантования (время между приемом двух сигналов)
    time_step = (timepoints2[-1]-timepoints2[0])/len(ydata2)
     
    if len(ydata2)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.figure(num=12,figsize=(14, 7),clear=True)
        plt.subplots_adjust(left=0.05,bottom=0.07,right=0.99,top=0.95,hspace=0.4)

# вывод спектра всего сигнала
        plt.subplot(1,1,1)     
        plt.title('Спектр всего сигнала 2')
        if len(metkabuf2)<1:
            plt.xlabel('Частота [Гц]')
        plt.ylabel('Мощность [отн.ед.]')
        plt.grid(True)# включаем сетку

        sig_fft = fftpack.rfft(ydata2)
        N=int(len(sig_fft))
        power = np.abs(sig_fft)# считаем фурье преобразование
        sample_freq=fftpack.rfftfreq(len(ydata2),d=time_step)

        plt.plot(sample_freq[1:-1],2*power[1:-1]/N)
        plt.show()
        
def analisHist2(file='test.png',show=1,save=0):
    global ydata2
    global timepoints2
    global metkabuf2
    global ydata2
    
    if len(ydata2)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.figure(num=13,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)

        plt.subplot(1,1,1)
        n,bins,patches=plt.hist(ydata2,bins='auto',density=True,stacked=True)
        
        plt.title('Гистограмма всего сигнала 2')
        if len(metkabuf2)<1:
            plt.xlabel('Длина волны [nm]')
        plt.ylabel('Плотность расределения')
        plt.grid(True)
        #plt.xlim(525, 540)
        plt.plot()
        plt.show()      

def deltaHist2(file='test.png',show=1,save=0):
    global ydata2
    global timepoints2
    global metkabuf2
    global pic_list2
    
    select_metka=[]
    select_metka=list_metok2.curselection() #получаем список выделенных элементов

    
    if len(ydata2)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.figure(num=16,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)

        plt.title('Гистограмма сравниваемых сигналов 2')
        plt.xlabel('Длина волны [nm]')
        plt.ylabel('Плотность расределения')
        plt.grid(True)
        plt.xlim(525, 540)

        if len(select_metka)>0:
                i=0
                while i < len(select_metka):
                    if select_metka[i]==0:
                       n,bins,patches=plt.hist(ydata2[:metkabuf2[0]], bins='auto',density=True,stacked=True,alpha=0.5,label=pic_list2[select_metka[i]])
                    elif select_metka[i]==len(metkabuf2):
                       n,bins,patches=plt.hist(ydata2[metkabuf2[-1]:-1],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[len(metkabuf2)-1],label=pic_list2[select_metka[i]])
                    else:
                       n,bins,patches=plt.hist(ydata2[metkabuf2[select_metka[i]-1]:metkabuf2[select_metka[i]]],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[select_metka[i]-1],label=pic_list2[select_metka[i]])
                    i=i+1

        plt.legend()
        plt.plot()
        plt.show()             

def deltaFFT2(file='test.png',show=1,save=0):
    global ydata2
    global timepoints2
    global metkabuf2
    global pic_list2

    select_metka=[]
    select_metka=list_metok2.curselection() #получаем список выделенных элементов
     
    if len(ydata2)>0:#если данные приняты (длина буфера больше 0), то строим графики

        #вычисляем время квантования (время между приемом двух сигналов)
        #получается в районе 10-50 миллисекунд
        time_step = (timepoints2[-1]-timepoints2[0])/len(ydata2)
        
        plt.figure(num=17,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.05,bottom=0.07,right=0.99,top=0.95,hspace=0.4)
        plt.title("Сравниваемые спектры 2")
        plt.xlabel('Частота [Гц]')
        plt.ylabel('Мощность [отн.ед.]')
        plt.grid(True)

#график - фурье спектр сигнала на разных промежутках времени     
        if len(select_metka)>0:
                i=0
                while i < len(select_metka):

                  if select_metka[i]==0: #если выбран первый отрезок времени
                      sig_fft = fftpack.rfft(ydata2[:int(metkabuf2[0])])
                      N=len(sig_fft)
                      power = np.abs(sig_fft)
                      sample_freq=fftpack.rfftfreq(len(ydata2[:int(metkabuf2[0])]),d=time_step)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,label=pic_list2[select_metka[i]])

                # выводим спектр сигнала от последней метки до конца сигнала
                  elif select_metka[i]==len(metkabuf2):
                      sig_fft = fftpack.rfft(ydata2[int(metkabuf2[-1]):-1])
                      N=int(len(sig_fft))
                      power = np.abs(sig_fft)
                      sample_freq=fftpack.rfftfreq(len(ydata2[int(metkabuf2[-1]):-1]),d=time_step)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[len(metkabuf2)-1],label=pic_list2[select_metka[i]])
                  else:
                      sig_fft = fftpack.rfft(ydata2[metkabuf2[select_metka[i]-1]:metkabuf2[select_metka[i]]])
                      N=int(len(sig_fft))
                      power = np.abs(sig_fft)# считаем фурье преобразование
                      sample_freq=fftpack.rfftfreq(len(ydata2[int(metkabuf2[select_metka[i]-1]):int(metkabuf2[select_metka[i]])]),d=time_step)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[select_metka[i]-1],label=pic_list2[select_metka[i]])
                  i=i+1
                plt.legend()
                plt.plot()
        plt.show()      

def barGraph2(file='test.png',show=1,save=0): # столбчатая диаграмма - выводим количество принятых данных 
    global ydata2
    global timepoints2
    global metkabuf2

    plt.figure(num=15,figsize=(14, 6),clear=True)
    plt.title("Кол-во сигналов 2")
    plt.xlabel('Длина волны [nm]')
    plt.ylabel('Кол-во отсчетов [%]')

    select_metka=[]
    select_metka=list_metok2.curselection() #получаем список выделенных элементов

    if len(ydata2)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)
     
        if len(select_metka)>0:
                i=0
                while i < len(select_metka):
                    if select_metka[i]==0:
                       signal=pd.value_counts(ydata2[:metkabuf2[0]]).sort_index()#сортируем список замеров
                       plt.plot(signal.div(signal.sum()*0.01)) #выводим кол-во замеров в процентном соотношении
                    elif select_metka[i]==len(metkabuf2):
                       signal=pd.value_counts(ydata2[metkabuf2[-1]:-1]).sort_index()
                       plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[len(metkabuf2)-1]) 
                    else:
                       signal=pd.value_counts(ydata2[metkabuf2[select_metka[i]-1]:metkabuf2[select_metka[i]]]).sort_index()
                       plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[select_metka[i]-1])
                    i=i+1

        plt.grid(True)
        plt.xlim(525, 540)
        plt.plot()
        plt.show()

def mediumSig(show=1):
    global ydata
    global timepoints
    global metkabuf
    global mediumSignal
    global mediumTime
    

    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики
  
# первый график Принятого сигнала


        select_metka=[]
        select_metka=list_metok.curselection() #получаем список выделенных элементов


        mediumSignal = []
        mediumTime=[]

   
        if len(select_metka)>0:
                
                lenbuf=len(ydata)
                #выясним длину наименьшего отрезка данной категории
                #print('выясняем длину короткого отрезка')
                if select_metka[0]==0:
                    lenbuf=len(ydata[:metkabuf[0]])
                    i=1
                else:                    
                    i=0
                while i < len(select_metka):
                    #print('i=',i)
                    if select_metka[i]==len(metkabuf):
                        if len(ydata[metkabuf[select_metka[i]-1]:-1])<lenbuf:
                            lenbuf=len(ydata[metkabuf[select_metka[i]-1]:-1])
                            print('len 2:',lenbuf)
                    else:
                        if len(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]]])<lenbuf:                           
                            lenbuf=len(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]]])
                    i=i+1
                #print('lenbuf:',lenbuf)

                i=0
                #суммируем сигналы всех отрезков
                while i < len(select_metka):
                    if select_metka[i]==0:
                        mediumSignal.append(ydata[0:lenbuf])
                        #print('metka=0,signal=',mediumSignal1)
                    else:
                        mediumSignal.append(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]-1]+lenbuf])
                        #print('signal=',mediumSignal1)
                    i=i+1
                #считываем среднее значение
                mediumSignal=np.mean(mediumSignal,axis=0)
                #print('lenbuf=',lenbuf)
                #вычислим среднее время одного замера
                mid=timepoints[lenbuf]/lenbuf

                #делаем массив с временнЫми отметками
                x=0
                while x<lenbuf:
                    mediumTime.append(mid*x)
                    x=x+1
                #print ('mediumTime:',mediumTime)
                
        if show==1:
            plt.figure(num=31,figsize=(6, 4),clear=True)
            #plt.subplots_adjust(left=0.04,bottom=0.14,right=0.96,top=0.9)
                
            plt.title('Усредненный сигнал 1')
            plt.xlabel('Время [сек]')
            plt.ylabel('Длина волны [nm]')
            plt.grid(True)# включаем сетку
            plt.plot(mediumTime,mediumSignal,ls=':')
            plt.show()

def view_med_fft():
    #выводим сравнение графиков сигнала FFT    
    global ydata
    global timepoints
    global metkabuf
    global pic_list
    print("starting from view_med_fft")
    select_metka=[]
    select_metka=list_rgb_metok.curselection() #получаем список выделенных элементов
     
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики

        #вычисляем время квантования (время между приемом двух сигналов)
        #получается в районе 10-50 миллисекунд
        time_step = (timepoints[-1]-timepoints[0])/len(ydata)
        
        plt.figure(num=7,figsize=(14, 6),clear=True)
        plt.subplots_adjust(left=0.05,bottom=0.07,right=0.99,top=0.95,hspace=0.4)
        plt.title("Сравниваемые спектры 1")
        plt.xlabel('Частота [Гц]')
        plt.ylabel('Мощность [отн.ед.]')
        plt.grid(True)

#график - фурье спектр сигнала на разных промежутках времени     
        if len(select_metka)>0:
                i=0
                while i < len(select_metka):

                  if select_metka[i]==0: #если выбран первый отрезок времени
                      sig_fft = fftpack.rfft(ydata[:int(metkabuf[0])])
                      N=len(sig_fft)
                      power = np.abs(sig_fft)
                      sample_freq=fftpack.rfftfreq(len(ydata[:int(metkabuf[0])]),d=time_step)
                      #power_avarage=np.average(2*power[1:N]/N)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,label=pic_list[select_metka[i]])
                      #x=[1,80]
                      #y=[power_avarage,power_avarage]
                      #plt.plot(x,y)

                # выводим спектр сигнала от последней метки до конца сигнала
                  elif select_metka[i]==len(metkabuf):
                      sig_fft = fftpack.rfft(ydata[int(metkabuf[-1]):-1])
                      N=int(len(sig_fft))
                      power = np.abs(sig_fft)
                      sample_freq=fftpack.rfftfreq(len(ydata[int(metkabuf[-1]):-1]),d=time_step)
                     # power_avarage=np.average(2*power[1:N]/N)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[len(metkabuf)-1],label=pic_list[select_metka[i]])
                      #plt.plot(sample_freq[1:N],power_avarage,color=rgb[len(metkabuf)-1])
                  else:
                      sig_fft = fftpack.rfft(ydata[metkabuf[select_metka[i]-1]:metkabuf[select_metka[i]]])
                      N=int(len(sig_fft))
                      power = np.abs(sig_fft)# считаем фурье преобразование
                      sample_freq=fftpack.rfftfreq(len(ydata[int(metkabuf[select_metka[i]-1]):int(metkabuf[select_metka[i]])]),d=time_step)
                      #power_avarage=np.average(2*power[1:N]/N)
                      plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[select_metka[i]-1],label=pic_list[select_metka[i]])
                     # plt.plot(sample_freq[1:N], power_avarage,color=rgb[select_metka[i]-1])
                  i=i+1

                plt.plot()
                plt.legend()
        plt.show()      
            
def mediumFFT():
    global mediumSignal
    global mediumTime
    
    mediumSig(show=0)
    print('получили средний сигнал 1')
    time_step = (mediumTime[-1]-mediumTime[0])/len(mediumSignal)
    sig_fft = fftpack.rfft(mediumSignal)
    N=len(sig_fft)
    power = np.abs(sig_fft)
    sample_freq=fftpack.rfftfreq(len(mediumSignal),d=time_step)
    
    plt.figure(num=37,figsize=(6, 4),clear=True)
    plt.title('Усредненный спектр 1')
    plt.xlabel('Частота [Гц]')
    plt.ylabel('Мощность [отн.ед.]')
    plt.grid(True)
    plt.plot(sample_freq[1:N], 2*power[1:N]/N)

    # выводим мощности 1/3, 2/3 и 3/3 части спектра
    len1=int(N/3)
    len2=int(N*2/3)
    P1_text='P1='+str(format(power[1:len1].sum(),'.4f'))
    P2_text='P2='+str(format(power[len1:len2].sum(),'.4f'))
    P3_text='P3='+str(format(power[len2:-1].sum(),'.4f'))
    PAll_text='P='+str(format(power[1:].sum(),'.4f'))
    ax=plt.gca()
    #plt.legend((P1_text,P2_text,P3_text))
    plt.text(0.15, 0.9,P1_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    plt.text(0.5, 0.9,P2_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    plt.text(0.9, 0.9,P3_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    plt.text(0.9, 0.8,PAll_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    #рисуем вертикальные линии  1/3, 2/3 и 3/3 части спектра
    plt.plot([0.33,0.33],[0,1],'r--',transform=ax.transAxes)
    plt.plot([0.66,0.66],[0,1],'r--',transform=ax.transAxes)
    
    plt.show()

def mediumHist():
    global mediumSignal
    global mediumTime

    mediumSig(show=0)

    plt.figure(num=36,figsize=(6, 4),clear=True)
    plt.title('Усредненная гистограмма 1')
    plt.xlabel('Длина волны [nm]')
    plt.ylabel('Плотность расределения')
    plt.grid(True)
    plt.xlim(525, 540)

    n,bins,patches=plt.hist(mediumSignal, bins='auto',density=True,stacked=True,alpha=0.5)#,label=str('Спектр от 0 до '+str(int(timepoints[metkabuf[0]]))+' сек'))


    plt.plot()
    plt.show()

def mediumSig2(show=1):
    global ydata2
    global timepoints2
    global metkabuf2
    global mediumSignal2
    global mediumTime2

    if len(ydata2)>0:#если данные приняты (длина буфера больше 0), то строим графики
  
# первый график Принятого сигнала


        select_metka=[]
        select_metka=list_metok2.curselection() #получаем список выделенных элементов


        mediumSignal2 = []
        mediumTime2=[]

   
        if len(select_metka)>0:
                
                lenbuf=len(ydata2)
                #выясним длину наименьшего отрезка данной категории
                #print('выясняем длину короткого отрезка')
                if select_metka[0]==0:
                    lenbuf=len(ydata2[:metkabuf2[0]])
                    i=1
                else:                    
                    i=0
                while i < len(select_metka):
                    #print('i=',i)
                    if select_metka[i]==len(metkabuf2):
                        if len(ydata2[metkabuf2[select_metka[i]-1]:-1])<lenbuf:
                            lenbuf=len(ydata2[metkabuf2[select_metka[i]-1]:-1])
                            print('len 2:',lenbuf)
                    else:
                        if len(ydata2[metkabuf2[select_metka[i]-1]:metkabuf2[select_metka[i]]])<lenbuf:                           
                            lenbuf=len(ydata2[metkabuf2[select_metka[i]-1]:metkabuf2[select_metka[i]]])
                    i=i+1
                #print('lenbuf:',lenbuf)

                i=0
                #суммируем сигналы всех отрезков
                while i < len(select_metka):
                    if select_metka[i]==0:
                        mediumSignal2.append(ydata2[0:lenbuf])
                        #print('metka=0,signal=',mediumSignal1)
                    else:
                        mediumSignal2.append(ydata2[metkabuf2[select_metka[i]-1]:metkabuf2[select_metka[i]-1]+lenbuf])
                        #print('signal=',mediumSignal1)
                    i=i+1
                #считываем среднее значение
                mediumSignal2=np.mean(mediumSignal2,axis=0)
                #print('lenbuf=',lenbuf)
                #вычислим среднее время одного замера
                mid=timepoints2[lenbuf]/lenbuf

                #делаем массив с временнЫми отметками
                x=0
                while x<lenbuf:
                    mediumTime2.append(mid*x)
                    x=x+1
                #print ('mediumTime:',mediumTime)
                
        if show==1:
            plt.figure(num=41,figsize=(6, 4),clear=True)
            #plt.subplots_adjust(left=0.04,bottom=0.14,right=0.96,top=0.9)
                
            plt.title('Усредненный сигнал 2')
            plt.xlabel('Время [сек]')
            plt.ylabel('Длина волны [nm]')
            plt.grid(True)# включаем сетку
            plt.plot(mediumTime2,mediumSignal2,ls=':')
            plt.show()


def mediumFFT2():
    global mediumSignal2
    global mediumTime2
    
    mediumSig2(show=0)
    print('получили средний сигнал 2')
    time_step = (mediumTime2[-1]-mediumTime2[0])/len(mediumSignal2)
    sig_fft = fftpack.rfft(mediumSignal2)
    N=len(sig_fft)
    power = np.abs(sig_fft)
    sample_freq=fftpack.rfftfreq(len(mediumSignal2),d=time_step)
    plt.figure(num=47,figsize=(6, 4),clear=True)
    plt.title('Усредненный спектр 2')
    plt.xlabel('Частота [Гц]')
    plt.ylabel('Мощность [отн.ед.]')
    plt.grid(True)
    plt.plot(sample_freq[1:N], 2*power[1:N]/N)

    # выводим мощности 1/3, 2/3 и 3/3 части спектра
    len1=int(N/3)
    len2=int(N*2/3)
    P1_text='P1='+str(format(power[1:len1].sum(),'.4f'))
    P2_text='P2='+str(format(power[len1:len2].sum(),'.4f'))
    P3_text='P3='+str(format(power[len2:-1].sum(),'.4f'))
    PAll_text='P='+str(format(power[1:].sum(),'.4f'))
    ax=plt.gca()
    #plt.legend((P1_text,P2_text,P3_text))
    plt.text(0.15, 0.9,P1_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    plt.text(0.5, 0.9,P2_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    plt.text(0.9, 0.9,P3_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    plt.text(0.9, 0.8,PAll_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
    #рисуем вертикальные линии  1/3, 2/3 и 3/3 части спектра
    plt.plot([0.33,0.33],[0,1],'r--',transform=ax.transAxes)
    plt.plot([0.66,0.66],[0,1],'r--',transform=ax.transAxes)

    plt.show()
    
    

def mediumHist2():
    global mediumSignal2
    global mediumTime2

    mediumSig2(show=0)

    plt.figure(num=46,figsize=(6, 4),clear=True)
    plt.title('Усредненная гистограмма 2')
    plt.xlabel('Длина волны [nm]')
    plt.ylabel('Плотность расределения')
    plt.grid(True)
    plt.xlim(525, 540)

    n,bins,patches=plt.hist(mediumSignal2, bins='auto',density=True,stacked=True,alpha=0.5)#,label=str('Спектр от 0 до '+str(int(timepoints[metkabuf[0]]))+' сек'))


    plt.plot()
    plt.show()


def deltaFFT_D():
    global list_1
    global list_2
    global ydata
    global timepoints
    global metkabuf
    global ydata2
    global timepoints2
    global metkabuf2
    print('before')
    if (len(ydata)>0) & (len(ydata2)>0):
        print('after')
        #вычисляем время квантования (время между приемом двух сигналов)
        #получается в районе 10-50 миллисекунд
        time_step = (timepoints[-1]-timepoints[0])/len(ydata)
        time_step2 = (timepoints2[-1]-timepoints2[0])/len(ydata2)
        
        
        plt.figure(num=27,figsize=(14, 7),clear=True)
        plt.subplots_adjust(left=0.05,bottom=0.07,right=0.99,top=0.95,hspace=0.4)
        title_str='Спектры '+str(kategories[list_1])+' и '+str(kategories2[list_2])
        plt.title(title_str)

        label1=kategories[list_1]+' 1'
        label2=kategories2[list_2]+' 2'
        
        plt.xlabel('Частота [Гц]')
        plt.ylabel('Мощность [отн.ед.]')
        plt.grid(True)

#график - фурье спектр сигнала на разных промежутках времени     

        if list_1==0: #если выбран первый отрезок времени
            sig_fft = fftpack.rfft(ydata[:int(metkabuf[0])])
            N=len(sig_fft)
            power = np.abs(sig_fft)
            sample_freq=fftpack.rfftfreq(len(ydata[:int(metkabuf[0])]),d=time_step)
            plt.plot(sample_freq[1:N], 2*power[1:N]/N,label=label1)
# выводим спектр сигнала от последней метки до конца сигнала
        elif list_1==len(metkabuf):
            sig_fft = fftpack.rfft(ydata[int(metkabuf[-1]):-1])
            N=int(len(sig_fft))
            power = np.abs(sig_fft)
            sample_freq=fftpack.rfftfreq(len(ydata[int(metkabuf[-1]):-1]),d=time_step)
            plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[len(metkabuf)-1],label=label1)
        else:
            sig_fft = fftpack.rfft(ydata[metkabuf[list_1-1]:metkabuf[list_1]])
            N=int(len(sig_fft))
            power = np.abs(sig_fft)# считаем фурье преобразование
            sample_freq=fftpack.rfftfreq(len(ydata[int(metkabuf[list_1-1]):int(metkabuf[list_1])]),d=time_step)
            plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[list_1-1],label=label1)

        if list_2==0: #если выбран первый отрезок времени
            sig_fft = fftpack.rfft(ydata2[:int(metkabuf2[0])])
            N=len(sig_fft)
            power = np.abs(sig_fft)
            sample_freq=fftpack.rfftfreq(len(ydata2[:int(metkabuf2[0])]),d=time_step2)
            plt.plot(sample_freq[1:N], 2*power[1:N]/N,label=label2)
# выводим спектр сигнала от последней метки до конца сигнала
        elif list_2==len(metkabuf2):
            sig_fft = fftpack.rfft(ydata2[int(metkabuf2[-1]):-1])
            N=int(len(sig_fft))
            power = np.abs(sig_fft)
            sample_freq=fftpack.rfftfreq(len(ydata2[int(metkabuf2[-1]):-1]),d=time_step2)
            plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[len(metkabuf2)-1],label=label2)
        else:
            sig_fft = fftpack.rfft(ydata2[metkabuf2[list_2-1]:metkabuf2[list_2]])
            N=int(len(sig_fft))
            power = np.abs(sig_fft)# считаем фурье преобразование
            sample_freq=fftpack.rfftfreq(len(ydata2[int(metkabuf2[list_2-1]):int(metkabuf2[list_2])]),d=time_step2)
            plt.plot(sample_freq[1:N], 2*power[1:N]/N,color=rgb[list_2-1],label=label2)
            
        plt.legend()
        plt.plot()
        plt.show() 




def deltaHist_D(): # сравниваем гистограммы из разных файлов
    global list_1
    global list_2
    global ydata
    global timepoints
    global metkabuf
    global ydata2
    global timepoints2
    global metkabuf2


    if (len(ydata)>0) & (len(ydata2)>0):#если данные приняты (длина буфера больше 0), то строим графики
        
        plt.figure(num=26,figsize=(14, 7),clear=True)
        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)
        title_str='Гистограммы '+str(kategories[list_1])+' и '+str(kategories2[list_2])
        plt.title(title_str)
        plt.xlabel('Длина волны [nm]')
        plt.ylabel('Плотность расределения')
        plt.grid(True)
        plt.xlim(525, 540)

        label1=kategories[list_1]+' 1'
        label2=kategories2[list_2]+' 2'
        # выводим первый график
        if list_1==0:
                n,bins,patches=plt.hist(ydata[:metkabuf[0]], bins='auto',density=True,stacked=True,alpha=0.5,label=label1)#,label=str('Спектр от 0 до '+str(int(timepoints[metkabuf[0]]))+' сек'))
        elif list_1==len(metkabuf):
                n,bins,patches=plt.hist(ydata[metkabuf[-1]:-1],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[len(metkabuf)-1],label=label1)#,label='x')
        else:
                n,bins,patches=plt.hist(ydata[metkabuf[list_1-1]:metkabuf[list_1]],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[list_1-1],label=label1)
        # выводим второй график для сравнения
        if list_2==0:
                n,bins,patches=plt.hist(ydata2[:metkabuf2[0]], bins='auto',density=True,stacked=True,alpha=0.5,label=label2)#,label=str('Спектр от 0 до '+str(int(timepoints[metkabuf[0]]))+' сек'))
        elif list_2==len(metkabuf2):
                n,bins,patches=plt.hist(ydata2[metkabuf2[-1]:-1],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[len(metkabuf2)-1],label=label2)#,label='x')
        else:
                n,bins,patches=plt.hist(ydata2[metkabuf2[list_2-1]:metkabuf2[list_2]],bins='auto',density=True,stacked=True,alpha=0.5,color=rgb[list_2-1],label=label2)

        plt.legend()
        plt.plot()
        plt.show()  

def barGraph_D():
    global list_1
    global list_2
    global ydata
    global timepoints
    global metkabuf
    global ydata2
    global timepoints2
    global metkabuf2

    plt.figure(num=14,figsize=(14, 6),clear=True)
    title_str='Кол-во сигналов '+str(kategories[list_1])+' и '+str(kategories2[list_2])
    plt.title(title_str)
    plt.xlabel('Длина волны [nm]')
    plt.ylabel('Кол-во отсчетов [%]')

    label1=kategories[list_1]+' 1'
    label2=kategories2[list_2]+' 2'
    
    if len(ydata)>0:#если данные приняты (длина буфера больше 0), то строим графики

        plt.subplots_adjust(left=0.11,bottom=0.07,right=0.97,top=0.93,hspace=0.4)
        if list_1==0:
            signal=pd.value_counts(ydata[:metkabuf[0]]).sort_index()#сортируем список замеров
            plt.plot(signal.div(signal.sum()*0.01),label=label1) #выводим кол-во замеров в процентном соотношении
        elif list_1==len(metkabuf):
            signal=pd.value_counts(ydata[metkabuf[-1]:-1]).sort_index()#.plot(alpha=0.5,color=rgb[len(metkabuf)-1])
            plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[len(metkabuf)-1],label=label1) 
        else:
            signal=pd.value_counts(ydata[metkabuf[list_1-1]:metkabuf[list_1]]).sort_index()#.plot(alpha=0.5,color=rgb[select_metka[i]-1])
            plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[list_1-1],label=label1)

        if list_2==0:
            signal=pd.value_counts(ydata2[:metkabuf2[0]]).sort_index()#сортируем список замеров
            plt.plot(signal.div(signal.sum()*0.01),label=label2) #выводим кол-во замеров в процентном соотношении
        elif list_2==len(metkabuf2):
            signal=pd.value_counts(ydata2[metkabuf2[-1]:-1]).sort_index()#.plot(alpha=0.5,color=rgb[len(metkabuf)-1])
            plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[len(metkabuf2)-1],label=label2) 
        else:
            signal=pd.value_counts(ydata2[metkabuf2[list_2-1]:metkabuf2[list_2]]).sort_index()#.plot(alpha=0.5,color=rgb[select_metka[i]-1])
            plt.plot(signal.div(signal.sum()*0.01),alpha=0.5,color=rgb[list_2-1],label=label2)


        plt.grid(True)
        plt.xlim(525, 540)
        plt.plot()
        plt.show()
    return 0


def on_first_box(idx, val):
    global list_1
    list_1 = idx
    #list_metok.activate(idx)
    print('First:', idx)


def on_second_box(idx, val):
    global list_2
    list_2 = idx
    print('Second :', idx)


def onselect(event, listbox):
    w = event.widget
    try:
        idx = int(w.curselection()[0])
    except IndexError:
        return
    if listbox is list_metok:
        return on_first_box(idx, w.get(idx))
    if listbox is list_metok2:
        return on_second_box(idx, w.get(idx))

def init_list_patterns():
    global patterns
    global patterns_kat

    
    #проверим, существуют ли папки с паттернами
    if not os.path.exists('.\save_patterns'):
        baud_patterns.delete('1.0',END)
        baud_patterns.insert('1.0','папка с паттернами не найдена!!!\n')
        list_patterns.delete(0,END)
        return()
    else:
         baud_patterns.delete('1.0',END)
         baud_patterns.insert('1.0','списки паттернов загружены\n')

    #составим список папок:
    folder=[]
    for i in os.walk(".\save_patterns"):
       folder.append(i)
    
    print('каталоги:',folder[0][1])
    patterns_kat=folder[0][1]
    if len(folder[0][1])==0:
        baud_patterns.delete('1.0',END)
        baud_patterns.insert('1.0','паттернов в каталоге нет\n')
        
    

    #выведем список категорий и кол-во файлов в них:

    list_patterns.delete(0, END) #очистим список паттернов

    i=0
    while i<len(folder[0][1]):
        count=len(folder[i+1][2])
        list_patterns.insert(END,str(folder[0][1][i]+': '+str(count)+' шт'))
        #print(str(folder[0][1][i])+': '+str(count)+' шт')
        i=i+1

def load_patterns():
    global patterns
    global ydata_patterns
    global timepoints_patterns
    global trainingSet
    global folder
    print('\nЗагружем файлы паттернов...')
    trainingSet=[]

    #загрузим списки паттернов(на всякий случай):
    init_list_patterns()

    baud_patterns.insert(END,'загружаем паттерны..\n')
         
       #проверим, существуют ли папки с паттернами
    if not os.path.exists('.\save_patterns'):
        baud_patterns.delete('1.0',END)
        baud_patterns.insert('1.0','папка с паттернами не найдена!!!\n')
        list_patterns.delete(0,END)
        return()
    else:
        baud_patterns.delete('1.0',END)
        baud_patterns.insert('1.0','загружаем паттерны..\n')

    #составим список папок:
    folder=[]
    for i in os.walk(".\save_patterns"):
        folder.append(i)
    
    #print('каталоги:',folder[0][1])
    if len(folder[0][1])==0:
        baud_patterns.delete('1.0',END)
        baud_patterns.insert('1.0','паттернов в каталоге нет\n')
        list_patterns.delete(0, END) #очистим список паттернов
    
#подгрузим паттерны в память
    i=0
    timepoints_patterns.clear()
    ydata_patterns.clear()
#формируем список в массиве:patterns[i][j][z], где каталог - i, файл - j, данные - z.
    while i<len(folder[0][1]): #счетчик категорий(каталогов)
        j=0
        timepoints_patterns.append([]) #добавляем в массив список (элемент списка), в котором будут данные файлов из этого каталога
        ydata_patterns.append([])            
        while j<len(folder[i+1][2]):
            file_pattern=str(folder[i+1][0]+'\\'+folder[i+1][2][j]) #получаем название файла в этом каталоге
        #загружаем сырые данные
            f = open(file_pattern, 'r').read()
            dataArray = f.split('\n')
            timepoints_patterns[i].append([]) # добавляем в i-ую позицию (каталог i), данные файлов с порядковым номером j
            ydata_patterns[i].append([])

            t0=0 # приведем все временнЫе интервалы к отрезку [0:max] ( т.к. многие паттерны начинаются с 20 секунды и более)
            z=0 #счетчик данных
            for eachLine in dataArray:                
                if len(eachLine)>1:
                    t,y = eachLine.split(';')
                    timepoints_patterns[i][j].append(float(t))
                    ydata_patterns[i][j].append(float(y))
                    if z==0:#записываем первое значение временнОго ряда в t0
                        t0=float(t)
                    timepoints_patterns[i][j][-1]=timepoints_patterns[i][j][-1]-t0 # приводим все значения временнОго ряда к отрезку от 0 до максимума
                        
                z=z+1
            #print(timepoints[i][j])
            #print (file_pattern)
            
            j=j+1
        i=i+1
    #print(timepoints)
    print('Файлы паттернов загружены\n')
    baud_patterns.delete('1.0',END)
    baud_patterns.insert('1.0','паттерны загружены\n')

def view_patterns(): #график усредненнго сигнала паттерна
    print("starting..")
    setrgb='black'
    select_metka=[]
    list_size=list_rgb_patterns.size()
    select_metka=list_rgb_patterns.curselection() #получаем список выделенных элементов
    print("select_metka list:",list_size)

    
    #print("select_metka selected element:",select_metka)
    #print("select metka=",list_rgb_patterns.get(select_metka[-1]))
    i=0 #номер позиции с паттерном fon_r(g/b)
    if list_rgb_patterns.get(select_metka[-1]).find('_r')!=-1:
        setrgb='red'
        while list_rgb_patterns.get(i).find('fon_r')<0:
            i=i+1
    elif list_rgb_patterns.get(select_metka[-1]).find('_g')!=-1:
        setrgb='green'
        while list_rgb_patterns.get(i).find('fon_g')<0:
            i=i+1
    elif list_rgb_patterns.get(select_metka[-1]).find('_b')!=-1:
        setrgb='blue'
        while list_rgb_patterns.get(i).find('fon_b')<0:
            i=i+1
    
    print("colour=",setrgb)
    
    if select_metka:
        plt.figure(num=int(260+select_metka[-1]),figsize=(7, 4),clear=True)    
        plt.title(str('Сигнал '+list_rgb_patterns.get(select_metka[-1])))
        plt.xlabel('Время [сек]')
        plt.ylabel('Длина волны [nm]')
        plt.grid(True)# включаем сетку
        j=0
        #while j<len(timepoints_patterns[select_metka[-1]]):
        #    plt.plot(timepoints_patterns[select_metka[-1]][j],ydata_patterns[select_metka[-1]][j],ls=':')
        #    j=j+1
        medium_pattern(select_metka[-1])
        if list_rgb_patterns.get(select_metka[-1]).find('fon')!=-1:
            if setrgb=='red':
                set_num=red_mid
            elif setrgb=='green':
                set_num=green_mid
            elif setrgb=='blue':
                set_num=blue_mid
                
            plt.plot(medium_pattern_signal_time,np.array(medium_pattern_signal)*0.0098+set_num,color='black')
            #np.array(red[:metkabuf[0]])*0.0098+red_mid
        else:
            if setrgb=='red':
                set_num=red_mid
            elif setrgb=='green':
                set_num=green_mid
            elif setrgb=='blue':
                set_num=blue_mid
            plt.plot(medium_pattern_signal_time,np.array(medium_pattern_signal)*0.0098+set_num,color=setrgb)
            medium_pattern(i)
            plt.plot(medium_pattern_signal_time,np.array(medium_pattern_signal)*0.0098+set_num,color='grey')
            
            
        plt.show()

def view_all_patterns(): #график усредненнго сигнала паттерна
    
        plt.figure(num=101,figsize=(7, 4),clear=True)    
        plt.title(str('Все сигналы из базы'))
        plt.xlabel('Время [сек]')
        plt.ylabel('Длина волны [nm]')
        plt.grid(True)# включаем сетку
        for i in range(len(ydata_patterns)):
            col=np.random.rand(3)
            for j in range (len(ydata_patterns[i])):
                 plt.plot(ydata_patterns[i][j],color=setrgb)

        plt.show()

def view_fft_patterns(): #спектр паттерна

    
    select_metka=[]
    select_metka=list_patterns.curselection() #получаем список выделенных элементов
    
    if select_metka:
        plt.figure(num=int(70+select_metka[-1]),figsize=(6, 4),clear=True)    
        plt.title(str('Спектр '+list_patterns.get(select_metka[-1])))
        plt.xlabel('Частота [Гц]')
        plt.ylabel('Мощность [отн.ед.]')
        plt.grid(True)
        j=0
        #while j<len(timepoints_patterns[select_metka[-1]]):
        #    time_step = (timepoints_patterns[select_metka[-1]][j][-1]-timepoints_patterns[select_metka[-1]][j][0])/len(timepoints_patterns[select_metka[-1]][j])
        #    sig_fft = fftpack.rfft(ydata_patterns[select_metka[-1]][j])
        #    N=len(sig_fft)
        #    power = np.abs(sig_fft)
        #    sample_freq=fftpack.rfftfreq(len(ydata_patterns[select_metka[-1]][j]),d=time_step)
        #    plt.plot(sample_freq[1:N], 2*power[1:N]/N,ls=':')
        #    j=j+1
           
        medium_pattern(select_metka[-1]) #получим усредненный сигнал для паттерна
        
        time_step = (medium_pattern_signal_time[-1]-medium_pattern_signal_time[0])/len(medium_pattern_signal_time)
        sig_fft = fftpack.rfft(medium_pattern_signal)
        N=len(sig_fft)
        power = np.abs(sig_fft)
        sample_freq=fftpack.rfftfreq(len(medium_pattern_signal),d=time_step)
        plt.plot(sample_freq[1:N], 2*power[1:N]/N,color='black') 
    

    # выводим мощности 1/3, 2/3 и 3/3 части спектра
        len1=int(N/3)
        len2=int(N*2/3)
        P1_text='P1='+str(format(power[1:len1].sum(),'.4f'))
        P2_text='P2='+str(format(power[len1:len2].sum(),'.4f'))
        P3_text='P3='+str(format(power[len2:-1].sum(),'.4f'))
        PAll_text='P='+str(format(power[1:].sum(),'.4f'))
        ax=plt.gca()
       #plt.legend((P1_text,P2_text,P3_text))
        plt.text(0.15, 0.9,P1_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
        plt.text(0.5, 0.9,P2_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
        plt.text(0.9, 0.9,P3_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
        plt.text(0.9, 0.8,PAll_text, horizontalalignment='center',verticalalignment='center',transform=ax.transAxes)
        #рисуем вертикальные линии  1/3, 2/3 и 3/3 части спектра
        plt.plot([0.33,0.33],[0,1],'r--',transform=ax.transAxes)
        plt.plot([0.66,0.66],[0,1],'r--',transform=ax.transAxes)
 
        plt.show()

def view_hist_patterns():
    
    select_metka=[]
    select_metka=list_patterns.curselection() #получаем список выделенных элементов
    
    if select_metka:
        plt.figure(num=int(80+select_metka[-1]),figsize=(6, 4),clear=True)    
        plt.title(str('Гистограмма '+list_patterns.get(select_metka[-1])))
        plt.xlabel('Длина волны [nm]')
        plt.ylabel('Плотность расределения')
        plt.grid(True)

        medium_pattern(select_metka[-1]) #получим усредненный сигнал для паттерна
        

        n,bins,patches=plt.hist(medium_pattern_signal, bins='auto',density=True,stacked=True,alpha=0.5)
        
        plt.plot()
        plt.show()
    
def medium_pattern(i=0):
    global medium_pattern_signal
    global ydata_patterns
    global medium_pattern_signal_time
    
    medium_pattern_signal.clear()
    medium_pattern_signal_time.clear()
    
    j=0    
    y=0
    y_sum=0
    count=0
    y_max=max(len(ydata_patterns[i][p]) for p in range(0,len(ydata_patterns[i]))) # максимальная длина данных в этом паттерне

#найдем индекс с сигналом маскимальной длины во вроемени
    z=0
    z_max=0
    p_int=0
    for p in range(0,len(timepoints_patterns[i])):
        z=len(timepoints_patterns[i][p])
        if z_max<z:
            z_max=z
            p_int=p

#будем использовать эту линейку времени для среднего сигнала
    medium_pattern_signal_time=timepoints_patterns[i][p_int].copy()

    print('y_max=',y_max)
    while y<y_max:
        try:
            if (j!=len(ydata_patterns[i])) & (y!=y_max):
                y_sum=y_sum+ydata_patterns[i][j][y]
                count=count+1
                j=j+1
            elif j==len(ydata_patterns[i]):
                medium_pattern_signal.append(float(y_sum/count))
                y_sum=0
                count=0
                j=0
                y=y+1
        except IndexError:
            j=j+1
    if len(medium_pattern_signal)>len(medium_pattern_signal_time):
        while len(medium_pattern_signal)>len(medium_pattern_signal_time):
            del medium_pattern_signal[-1]
    elif len(medium_pattern_signal)<len(medium_pattern_signal_time):
        while len(medium_pattern_signal)<len(medium_pattern_signal_time):
            del medium_pattern_signal_time[-1]
        
def normalise_data():
    global ydata_patterns
    mean_data=0
    
    print("нормализуем данные")
    for i in range(0,len(ydata_patterns)):
        for j in range(0,len(ydata_patterns[i])):
            mean_data=np.mean(ydata_patterns[i][j])
            ydata_patterns[i][j]=ydata_patterns[i][j]-mean_data
        
    print("данные нормализованы")          
    baud_patterns.insert(END,'данные нормализованы\n')  

def euclideanDistance(instance1, instance2, length):
	distance = 0
	for x in range(length):
		distance += pow((instance1[x] - instance2[x]), 2)
	return math.sqrt(distance)
 
def getNeighbors(trainingSet, testInstance, k):
        distances = []
        #print('len of traningSet:',len(trainingSet))
        #print('len of testSet:',len(testInstance))
        #print('len of ydata:',len(ydata_patterns))
        #print('traningSet:',trainingSet[:2][:3])
        #print('testSet:',testInstance)
        for x in range(len(trainingSet)):
            for y in range(len(trainingSet[x])):
                length = min(len(trainingSet[x][y]),len(testInstance))-1
                dist = euclideanDistance(testInstance, trainingSet[x][y], length)
                #print(dist) #выводим посчитанные расстояния
                distances.append((x,y,dist))
        distances.sort(key=itemgetter(2))
        #print('distances=',distances,'\n')
        neighbors = []
        for x in range(k):
            neighbors.append(distances[x])
        return neighbors
 
def getResponse(neighbors):
	classVotes = {}
	for x in range(len(neighbors)):
		response = neighbors[x][0]
		if response in classVotes:
			classVotes[response] += 1
		else:
			classVotes[response] = 1
	sortedVotes = sorted(classVotes.items(), key=itemgetter(1), reverse=True)
	return sortedVotes
 
#посчитаем соотношение числа в группе максимального сходства к числу в группах с остальными сходствами.
def getAccuracy(result):
	correct = result[0][-1]
	incorrect=0
	for x in range(1,len(result)):		
	    incorrect+=result[x][-1]
	return (correct/float(correct+incorrect) * 100.0)

#прогон 1000 сравнений данных базы 
def mean_1000_KNN():
    
    mean_KNN()
    mean_FFT_KNN()
    mean_hist_KNN()

    load_patterns()
    normalise_data()

    mean_KNN()
    mean_FFT_KNN()
    mean_hist_KNN()
    
    
#оценка методом KNN гистограмм сигналов всех паттернов
def mean_hist_KNN():
    global pattern_Hist_bins
    print('\nСравниваем ГИСТОГРАММЫ методом KNN\n')
    #посчитаем Hist для всех графиков паттернов
    
    prepare_patterns_Hist()    
    mean_KNN(pattern_Hist_bins)
    

#оценка методом KNN FFT сигналов всех паттернов
def mean_FFT_KNN():
    global pattern_fft_power
    print('\nСравниваем FFT(спектры) методом KNN\n')
    #посчитаем FFT для всех графиков паттернов
    prepare_patterns_fft()
    mean_KNN(pattern_fft_power)
    
#оценим среднюю точность метода в i-итерациях:
def mean_KNN(ydata_p=ydata_patterns):

    global_knn=0
    kat_knn=[]
    base=100 #количество итераций проверки базы
    #if len(ydata_p)==0:
    #    ydata_p=ydata_patterns
    global_perc=[]
    kat_perc=[]
    for i in range(0,base):
        global_knn,kat_knn=ocenkaKNN(ydata_p,0,0)
        global_perc.append(global_knn)
        kat_perc.append(kat_knn)
    kat_perc=np.mean(kat_perc,axis=0)
    print('\nСреднее KNN при макс.фоне:',np.mean(global_perc))
    print('Среднее по всем категориям:')
    for c in range(len(patterns_kat)):
        print(str(str(patterns_kat[c])+': '+str('%0.1f'%(kat_perc[c]))+' %'))

    kat_perc=[]
    for i in range(0,base):
        delFon(ydata_p)
        global_knn,kat_knn=ocenkaKNN(ydata_p,1,0)
        global_perc.append(global_knn)
        kat_perc.append(kat_knn)
    kat_perc=np.mean(kat_perc,axis=0)
    print('\nСреднее KNN при равном фоне:',np.mean(global_perc))
    print('Среднее по всем категориям:')
    for c in range(len(patterns_kat)):
        print(str(str(patterns_kat[c])+': '+str('%0.1f'%(kat_perc[c]))+' %'))
    
    
#оценим точность базы, где кол-во образцов фона= среднему значению других образцов
def bez_fon_KNN(ydata_p=ydata_patterns):
    delFon(ydata_p)
    ocenkaKNN(ydata_p,1,1)

#удалим часть фоновых картинок
def ravn_fon():
    delFon(ydata_patterns)
    
#удалим лишние паттерны фона
def delFon(ydata_p=ydata_patterns):
    global trainingSet

    trainingSet=copy.deepcopy(ydata_p)
    a=[]
    b=0
    t=0 #номер категории, которая назвается fon
    for i in range(len(trainingSet)):
        if patterns_kat[i]!='fon':
            a.append(len(trainingSet[i]))
        else:
            b=len(trainingSet[i])
            t=i
    b=b-int(np.mean(a))
    z=np.random.choice(len(trainingSet[t]),size=b,replace=False)
    z=sorted(z,reverse=True)
#    print('len(z)=',len(z))
#    print('len(trainingSet[t])=',len(trainingSet[t]))
    for m in range(len(z)):
#        print('m=',m)
        del trainingSet[t][z[m]]
    print('осталось fon:'+str(len(trainingSet[t]))+' шт')
 
def ocenkaKNN(ydata_p=ydata_patterns,global_patterns=0,print_res=1):
    global trainingSet
    
    category=0
    if global_patterns==0:
        trainingSet=copy.deepcopy(ydata_p)
        
    testSet=[]
    kat=[]
    if print_res==1:
        print('тестовых образцов:')
        
    for i in range(len(trainingSet)):
        k=int(0.33*len(trainingSet[i]))
        z=np.random.choice(len(trainingSet[i]),size=k,replace=False)
        z=sorted(z,reverse=True)

        for m in range(len(z)):
            testSet.append((i,trainingSet[i][z[m]]))
            del trainingSet[i][z[m]]
        kat.append(len(z))
    
    if print_res==1:
        print ('Сраваниваемых паттернов: ',len(trainingSet))
        print ('Кол-во тестовых образцов: ',len(testSet))
	# generate predictions
    predictions=[]
    tochnost_kat=[]
    k = 10
    for x in range(len(testSet)):
        if x<len(patterns_kat):
            predictions.append(0)
        neighbors = getNeighbors(trainingSet, testSet[x][1], k)
        #print('neighbors:',neighbors)
        result = getResponse(neighbors)
        if result[0][0]==testSet[x][0]:
            predictions[testSet[x][0]]=predictions[testSet[x][0]]+1

    tochnost_knn=sum(predictions)*100/len(testSet)
    tochnost=str('%0.1f'%(tochnost_knn))
    if print_res==1:
        print('Точность KNN: ',tochnost,'%')
    for c in range(len(predictions)):
        tochnost_kat.append(predictions[c]*100.0/kat[c])
        if print_res==1:
            print(str(str(patterns_kat[c])+': '+str('%0.1f'%(tochnost_kat[c]))+' %'))
    
    return tochnost_knn,tochnost_kat

def pattern_signal_KNN_old():
    global trainingSet
    if len(ydata_patterns)==0:
        load_patterns()
    if len(trainingSet)==0:
        trainingSet=copy.deepcopy(ydata_patterns)
        #normalise_data()
    #normalise_data()    
    print('Cравниваем выбранный отрезок файла с базой паттернов')
    if len(ydata)>0:
        select_metka=[]
        select_metka=list_metok.curselection() #получаем список выделенных элементов  
        if len(select_metka)>0:
            if select_metka[0]==0:
               testSet=(ydata[:metkabuf[0]])#-np.mean(ydata[:metkabuf[0]]))
               
            elif select_metka[-1]==len(metkabuf):
                testSet=(ydata[metkabuf[select_metka[-1]-1]:-1])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))
                
        #trainingSet = ydata_patterns
        predictions=[]
        k = 10
        
        neighbors = getNeighbors(trainingSet, testSet, k)
        
        result = getResponse(neighbors)
        predictions.append(result[0][0])
        baudKNN.delete('1.0', END)
        print('Максимум сходство с: ',patterns_kat[result[0][0]])
        baudKNN.insert(1.0, str('MAX сходство с: '+str(patterns_kat[result[0][0]])))
        
        accuracy = getAccuracy(result)
        print('Точность определния: ' ,accuracy, '%')
        baudKNN.insert(END, str('\nточность:'+str(accuracy)+'%\n'))
        
        print('найдено сходство с:')
        baudKNN.insert(END, str('\nвсего сходств с:\n'))
        
        for i in range(len(result)):            
            print(str(patterns_kat[result[i][0]])+'-'+str(result[i][1])+' ближайших')
            baudKNN.insert(END,str(str(patterns_kat[result[i][0]])+' -'+str(result[i][1])+' ближайших\n'))
            
def pattern_signal_KNN_rgb():
    
    print('Паттерны:',patterns_kat)
    print('Сравнение формы сигналов')
    baud_rgb_patterns.delete('1.0',END)
    baud_rgb_patterns.insert(END,'сравнение с R\n')
    pattern_signal_KNN(color='r')
    baud_rgb_patterns.insert(END,'сравнение с G\n')
    pattern_signal_KNN(color='g')
    baud_rgb_patterns.insert(END,'сравнение с B\n')
    pattern_signal_KNN(color='b')


def pattern_signal_KNN(color=' '):
    global trainingSet
    global pic_list
    global ydata
    
    if len(ydata_patterns)==0:
        load_patterns()
    if len(trainingSet)==0:
        trainingSet=copy.deepcopy(ydata_patterns)
        #normalise_data()
    #normalise_data()
    #print('ydata_patterns=',ydata_patterns)
    
    #print('Cравниваем выбранный отрезок файла с базой паттернов')
    
    
    if color=='r':
        ydata=[]
        ydata=red[:]
    elif color=='g':
        ydata=[]
        ydata=green[:]
    elif color=='b':
        ydata=[]
        ydata=blue[:]
        
    if len(ydata)>0:
       #создаем таблицу с кол-ом элементов, равным кол-ву паттернов
        knnTable=[]
        #for i in range(len(patterns_kat)):
        #        knnTable.append([])

        #перебираем все части загруженного файла и сравниваем с базой trainingSet   
        for z in range(len(metkabuf)+1):
            if z==0:
                testSet=(ydata[:metkabuf[0]])#-np.mean(ydata[:metkabuf[0]]))
               
            elif z==len(metkabuf):
                testSet=(ydata[metkabuf[z-1]:-1])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[z-1]:metkabuf[z]])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))
 
           
            predictions=[]
            k = 10
        
            neighbors = getNeighbors(trainingSet, testSet, k)
            #print('len(testSet)=',len(testSet))
            #print('len(trainingSet)=',len(trainingSet))
            
            result = getResponse(neighbors)
            predictions.append(result[0][0])
            accuracy = getAccuracy(result)
            #print('len(result)=',len(result))
            #print('result=',result)
            #print('knnTable=',knnTable)
            #print('patterns_kat=',patterns_kat)     
            #for i in range(len(result)):
            #    print(i)
            #    print(str(patterns_kat[result[i][0]])+'-'+str(result[i][1])+' ближайших')
                
            knnTable.append([])
            for i in range(len(patterns_kat)):
                knnTable[-1].append(0)
                #print(i)
            for i in range(len(result)):            
                knnTable[-1][result[i][0]]=result[i][1]*10

        print("Сравнение формы сигналов с сигналами цвета ",color)
        for i in range (len(knnTable)):
            if color!=' ':
                print(*knnTable[i],str(pic_list[i]))
            else:
                #text_baud=str(*knnTable[i])+str(pic_list[i][:-4])+'\n'
                print(*knnTable[i],str(pic_list[i][:-4]))
                #baud_rgb_patterns.insert(END,'text_baud')
               
                

def pattern_FFT_KNN_rgb():
        print('Паттерны:',patterns_kat)
        pattern_FFT_KNN(color='r')
        pattern_FFT_KNN(color='g')
        pattern_FFT_KNN(color='b')
        
def prepare_patterns_fft():
    global pattern_fft_power

    pattern_fft_power.clear()#подготовим мощности спектров каждого графика из паттернов

    for i in range(len(ydata_patterns)):
        pattern_fft_power.append([])
        for j in range(len(ydata_patterns[i])):
            sig_fft = fftpack.rfft(ydata_patterns[i][j])
            N=len(sig_fft)
            power = np.abs(sig_fft)
            pattern_fft_power[i].append(power)

    #print('FFT посчитано для всех графиков паттернов')

def pattern_FFT_KNN(normalise=0,color=' '):
    global pattern_fft_power
    global ydata

    if len(ydata_patterns)==0:
        load_patterns()
        #normalise_data()
    if normalise==1:
        normalise_data() #нормализуем данные (относительно средней линии каждого графика)


    prepare_patterns_fft()

    if color=='r':
        ydata=[]
        ydata=red[:]
    elif color=='g':
        ydata=[]
        ydata=green[:]
    elif color=='b':
        ydata=[]
        ydata=blue[:]   

    #print('Cравниваем выбранный FFT с базой паттернов:',color)
    #print('ydata len=',len(ydata))
    if len(ydata)>0:
        knnTable=[]
        for z in range(len(metkabuf)+1):
            if z==0:
                testSet=(ydata[:metkabuf[0]])#-np.mean(ydata[:metkabuf[0]]))
               
            elif z==len(metkabuf):
                testSet=(ydata[metkabuf[z-1]:-1])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[z-1]:metkabuf[z]])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))

            sig_fft = fftpack.rfft(testSet)
            N=len(sig_fft)
            power = np.abs(sig_fft)

            testSet=power          
            trainingSet = pattern_fft_power
            predictions=[]
            k = 10
            neighbors = getNeighbors(trainingSet, testSet, k)
            result = getResponse(neighbors)
            predictions.append(result[0][0])
            accuracy = getAccuracy(result)
            knnTable.append([])

            for i in range(len(patterns_kat)):
                knnTable[-1].append(0)
                #print(i)
            for i in range(len(result)):            
                knnTable[-1][result[i][0]]=result[i][1]*10

        print("Сравнение FFT с сигналами цвета ",color)
        for i in range (len(knnTable)):
            if color!=' ':
                print(*knnTable[i],str(pic_list[i]))
            else:
                print(*knnTable[i],str(pic_list[i][:-4]))
       
def pattern_FFT_KNN_old(normalise=0,color=' '):
    global pattern_fft_power

    if len(ydata_patterns)==0:
        load_patterns()
        #normalise_data()
    if normalise==1:
        normalise_data() #нормализуем данные (относительно средней линии каждого графика)


    prepare_patterns_fft()


    print('Cравниваем выбранный FFT с базой паттернов:',color)
    
    if len(ydata)>0:
        select_metka=[]
        select_metka=list_rgb_metok.curselection() #получаем список выделенных элементов  
        if len(select_metka)>0:
            if select_metka[0]==0:
               testSet=(ydata[:metkabuf[0]])#-np.mean(ydata[:metkabuf[0]]))
               
            elif select_metka[-1]==len(metkabuf):
                testSet=(ydata[metkabuf[select_metka[-1]-1]:-1])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))

        sig_fft = fftpack.rfft(testSet)
        N=len(sig_fft)
        power = np.abs(sig_fft)

        testSet=power          
        trainingSet = pattern_fft_power
        predictions=[]
        k = 10
        neighbors = getNeighbors(trainingSet, testSet, k)
        result = getResponse(neighbors)
        predictions.append(result[0][0])
        if color==' ':
            baudKNN.delete('1.0', END)
            baudKNN.insert(1.0, str('FFT MAX сходство с: '+str(patterns_kat[result[0][0]])))
        print('FFT Максимум сходство с: ',patterns_kat[result[0][0]])
        
        
        accuracy = getAccuracy(result)
        print('Точность определния: ' ,accuracy, '%')
        if color==' ':
            baudKNN.insert(END, str('\nточность:'+str(accuracy)+'%\n'))
            baudKNN.insert(END, str('\nвсего сходств с:\n'))

        print('найдено сходство с:')
        
        for i in range(len(result)):            
            print(str(patterns_kat[result[i][0]])+'-'+str(result[i][1])+'ближайших')
            if color==' ':
                baudKNN.insert(END,str(str(patterns_kat[result[i][0]])+' -'+str(result[i][1])+' ближайших\n'))



def prepare_patterns_Hist():
    global pattern_Hist_bins

    pattern_Hist_bins.clear()#подготовим гистограммы каждого графика из паттернов с количеством бинов=20 (максимально у фона насчитал 19)
    min_bin=0
    max_bin=0
    min_hist=0
    max_hist=0
                        
    for i in range(len(ydata_patterns)):
        pattern_Hist_bins.append([])
        for j in range(len(ydata_patterns[i])):            
            hist,bins=np.histogram(ydata_patterns[i][j], bins=20, density=True)
            pattern_Hist_bins[i].append(hist)

    #print('Гистограмма посчитана для всех графиков паттернов')

def pattern_Hist_KNN_rgb():
    print('Паттерны:',patterns_kat)
    pattern_Hist_KNN(color='r')
    pattern_Hist_KNN(color='g')
    pattern_Hist_KNN(color='b')

def pattern_Hist_KNN(color=' '):
    global pattern_Hist_bins
    global ydata

    if len(ydata_patterns)==0:
        load_patterns()
        #normalise_data()
    #normalise_data() #нормализуем данные (относительно средней линии каждого графика)

    if color=='r':
        ydata=[]
        ydata=red[:]
    elif color=='g':
        ydata=[]
        ydata=green[:]
    elif color=='b':
        ydata=[]
        ydata=blue[:]
        
    prepare_patterns_Hist()
          
    #print('Cравниваем выбранный Hist с базой паттернов:',color)
    #print('ydata len=',len(ydata))
    if len(ydata)>0:
        knnTable=[]
        for z in range(len(metkabuf)+1):
            if z==0:
                testSet=(ydata[:metkabuf[0]])#-np.mean(ydata[:metkabuf[0]]))
               
            elif z==len(metkabuf):
                testSet=(ydata[metkabuf[z-1]:-1])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[z-1]:metkabuf[z]])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))


            hist,bins=np.histogram(testSet, bins=20, density=True)
            testSet=hist
        
            trainingSet = pattern_Hist_bins
            predictions=[]
            k = 10
            neighbors = getNeighbors(trainingSet, testSet, k)
            result = getResponse(neighbors)
            predictions.append(result[0][0])
        
            accuracy = getAccuracy(result)
            knnTable.append([])

            for i in range(len(patterns_kat)):
                knnTable[-1].append(0)
                #print(i)
            for i in range(len(result)):            
                knnTable[-1][result[i][0]]=result[i][1]*10

        
        print("Сравнение HIST с сигналами цвета ",color)
        for i in range (len(knnTable)):
            if color!=' ':
                print(*knnTable[i],str(pic_list[i]))
            else:
                print(*knnTable[i],str(pic_list[i][:-4]))

    
def pattern_Hist_KNN_old(color=' '):
    global pattern_Hist_bins
    global ydata

    if len(ydata_patterns)==0:
        load_patterns()
        #normalise_data()
    #normalise_data() #нормализуем данные (относительно средней линии каждого графика)

        
    prepare_patterns_Hist()
          
    print('Cравниваем выбранный Hist с базой паттернов:',color)
    if len(ydata)>0:
        select_metka=[]
        select_metka=list_rgb_metok.curselection() #получаем список выделенных элементов  
        if len(select_metka)>0:
            if select_metka[0]==0:
               testSet=(ydata[:metkabuf[0]])#-np.mean(ydata[:metkabuf[0]]))
               
            elif select_metka[-1]==len(metkabuf):
                testSet=(ydata[metkabuf[select_metka[-1]-1]:-1])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))

        hist,bins=np.histogram(testSet, bins=20, density=True)
        testSet=hist
        
        trainingSet = pattern_Hist_bins
        predictions=[]
        k = 10
        neighbors = getNeighbors(trainingSet, testSet, k)
        result = getResponse(neighbors)
        predictions.append(result[0][0])
        if color==' ':
            baudKNN.delete('1.0', END)
            baudKNN.insert(1.0, str('Hist MAX сходство с: '+str(patterns_kat[result[0][0]])))
        print('Hist Максимум сходство с: ',patterns_kat[result[0][0]])
        
        
        accuracy = getAccuracy(result)
        print('Точность определния: ' ,accuracy, '%')
        if color==' ':
            baudKNN.insert(END, str('\nточность:'+str(accuracy)+'%\n'))
        
        print('найдено сходство с:')
        if color==' ':
            baudKNN.insert(END, str('\nвсего сходств с:\n'))
            
        for i in range(len(result)):            
            print(str(patterns_kat[result[i][0]])+'-'+str(result[i][1])+' ближайших')
            if color==' ':
                baudKNN.insert(END,str(str(patterns_kat[result[i][0]])+' -'+str(result[i][1])+' ближайших\n'))

def corrSig(): #считаем корреляцию между всеми отрезками в файле
    global metkabuf
    global ydata
    
    if len(ydata)>0:
        select_metka=[]
        select_metka=list_metok.curselection() #получаем список выделенных элементов  
        testSet=[]
        if len(select_metka)>0:
            baudKNN.delete('1.0', END)
            baudKNN.insert(END,'считаем корреляцию..')
            if select_metka[0]==0:
               testSet=(ydata[:metkabuf[0]]-np.mean(ydata[:metkabuf[0]]))
               
            elif select_metka[-1]==len(metkabuf):
                testSet=(ydata[metkabuf[select_metka[-1]-1]:-1]-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))

        len_test=len(testSet)
        baudKNN.delete('1.0', END)
        for i in range(len(metkabuf)):
            if i==0:
                c=len(ydata[:metkabuf[0]])
                if len_test>c: #проверяем длину тестового образца и длину сигнала, делаем длину тестового сигнала=длине сигнала
                    len_test=c
                arr=np.array(ydata[:len_test]) #преобразуем тип LIST в ARRAY (иначе не считает корреляцию)
                corr=100*np.corrcoef(testSet[:len_test],(arr-np.mean(arr)))[1,0]
                baudKNN.insert(END, str(str(pic_list[i][:-4])+' : '+str('%.1f'%corr)+'%\n'))
                print(str(pic_list[i])+' : '+str('%.1f'%corr))
                
            elif i==len(metkabuf):
                c=len(ydata[metkabuf[i-1]:-1])
                if len_test>c: #проверяем длину тестового образца и длину сигнала, делаем длину тестового сигнала=длине сигнала
                    len_test=c
                arr=np.array(ydata[metkabuf[i-1]:metkabuf[i-1]+len_test]) #преобразуем тип LIST в ARRAY (иначе не считает корреляцию)
                corr=100*np.corrcoef(testSet[:len_test],(arr-np.mean(arr)))[1,0]
                print(str(pic_list[i])+' : '+str('%.1f'%corr))
                baudKNN.insert(END, str(str(pic_list[i][:-4])+' : '+str('%.1f'%corr)+'%\n'))
                
            else:
                c=len(ydata[metkabuf[i-1]:metkabuf[i]])
                if len_test>c: #проверяем длину тестового образца и длину сигнала, делаем длину тестового сигнала=длине сигнала
                    len_test=c 
               # 
                arr=np.array(ydata[metkabuf[i-1]:metkabuf[i-1]+len_test]) #преобразуем тип LIST в ARRAY (иначе не считает корреляцию)
                corr=100*np.corrcoef(testSet[:len_test],(arr-np.mean(arr)))[1,0]
                print(str(pic_list[i])+' : '+str('%.1f'%corr))
                baudKNN.insert(END, str(str(pic_list[i][:-4])+' : '+str('%.1f'%corr)+'%\n'))    
        corr_arr=[]
        len_test=len(testSet)
        print(pic_list)
        # считаем корреляцию по всей базе паттернов
        for i in range(len(ydata_patterns)):
            for j in range(len(ydata_patterns[i])):
                c=len(ydata_patterns[i][j])
                if len_test>c:
                    corr=100*np.corrcoef(testSet[:c],ydata_patterns[i][j])[1,0]
                else:
                    corr=100*np.corrcoef(testSet,ydata_patterns[i][j][:len_test])[1,0]
                if i!=3:
                    corr_arr.append([abs(corr),patterns_kat[i]])

        sortedCorr = sorted(corr_arr)
        #print(sortedCorr)
                
    
def statSig(): #считаем корреляцию между всеми отрезками в файле
    global metkabuf
    global ydata
    global trainingSet
    global ydata_patterns
    global pic_list

    
    if len(ydata)>0:
        if len(ydata_patterns)==0:
            load_patterns()
        if len(trainingSet)==0:
            trainingSet=copy.deepcopy(ydata_patterns)
        select_metka=[]
        select_metka=list_metok.curselection() #получаем список выделенных элементов  
        testSet=[]
        #print('select_metka[-1]-1=',select_metka[-1]-1)
        #print('select_metka[-1]=',select_metka[-1])
        #print('select_metka[-1]+1=',select_metka[-1]+1)
        #print('len metkabuf=',len(metkabuf))
        print('стат.значимый результат:')
        #testSet=(ydata[:metkabuf[0]])
        #cсравнение сигналов из данного списка самих с собой:
#        for x in range(len(metkabuf)):
#            if x==0:
#                testSet=(ydata[:metkabuf[0]])
#                for y in range(len(metkabuf)):
#                    if y<(len(metkabuf)-1):
#                        if stats.ttest_ind(testSet,ydata[metkabuf[y]:metkabuf[y+1]])[-1]<0.05:
#                            print('1-ый сигнал отличен от: ',y+1)
#                    if y==(len(metkabuf)-1):
#                        if stats.ttest_ind(testSet,ydata[metkabuf[y]:-1])[-1]<0.05:
#                            print('1-ый сигнал отличен от: ',y+1)
#            if (x>0) and (x<(len(metkabuf)-1)):
#                testSet=ydata[metkabuf[x]:metkabuf[x+1]]
#                for y in range(x,len(metkabuf)):
#                    if y<(len(metkabuf)-1):
#                        if stats.ttest_ind(testSet,ydata[metkabuf[y]:metkabuf[y+1]])[-1]<0.05:
#                            print('%i-ый сигнал отличен от: %i'%(x+1,(y+1)))
#                    if y==(len(metkabuf)-1):
#                        if stats.ttest_ind(testSet,ydata[metkabuf[y]:-1])[-1]<0.05:
#                            print('%i-ый сигнал отличен от: %i'%(x+1,(y+1)))

#сравниваем каждый сигнал из загруженного списка с общей базой:

        statTable=[]
        #print(statTable)
        #print(len(metkabuf))
        for z in range(len(metkabuf)+1):
            if z==0:
                testSet=(ydata[:metkabuf[0]])
            if (z>0) and (z<(len(metkabuf))):
                testSet=ydata[metkabuf[z-1]:metkabuf[z]]
            if z==(len(metkabuf)):
                testSet=ydata[metkabuf[z-1]:-1]
                
            statTable.append([])
            
            for x in range(len(trainingSet)):
                
                delta=0
                for y in range(len(trainingSet[x])):
                    
                    if stats.ttest_ind(testSet,trainingSet[x][y])[-1]>0.05:
                        delta=delta+1
                if delta==0:
                    statTable[-1].append(0)
                else:
                    statTable[-1].append(len(trainingSet[x])/delta)
                #print(str('совпадение с:'+str(patterns_kat[x])+' '+str(delta)+'( из'+str(len(trainingSet[x]))+')'))
                
                
        for i in range (len(statTable)):
            print(*statTable[i],str(pic_list[i][:-4]))

            
        if len(select_metka)>0:
            baudKNN.delete('1.0', END)
            baudKNN.insert(END,'считаем стат.похожесть..')
            if select_metka[0]==0:
               testSet=(ydata[:metkabuf[0]])#-np.mean(ydata[:metkabuf[0]]))
               
            elif select_metka[-1]==len(metkabuf):
                testSet=(ydata[metkabuf[select_metka[-1]-1]:-1])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:-1]))
                
            else:
                testSet=(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]])#-np.mean(ydata[metkabuf[select_metka[-1]-1]:metkabuf[select_metka[-1]]]))

#            print ('Попарный анализ (Т-тест):')
#            x=0
#            y=0
#            for x in range(len(trainingSet)):
#                delta=0
#                for y in range(len(trainingSet[x])):
#                    if stats.ttest_ind(testSet,trainingSet[x][y])[-1]>0.05:
#                        delta=delta+1
#                print(str('совпадение с:'+str(patterns_kat[x])+' '+str(delta)+'( из'+str(len(trainingSet[x]))+')'))

#            print ('Анализ с группой(F_oneway-тест):')
#            x=0
#            for x in range(len(trainingSet)):
#                #if stats.f_oneway(testSet,trainingSet[x])[-1]<0.05:
#                    print("сравнение с группой:",patterns_kat[x], stats.f_oneway(testSet,*trainingSet[x]))
   

            #print ('F-тест (одинаковые дисперсии? выборки похожи?):',stats.f_oneway(testSet,ydata[metkabuf[select_metka[-1]]:metkabuf[select_metka[-1]+1]]))
            #print ('тест выбранного с послед.отрезком:',stats.ttest_ind(testSet,ydata[metkabuf[select_metka[-1]]:metkabuf[select_metka[-1]+1]]))
    #нормальность базы

def shapiro_test_patterns():
    global trainingSet
    global folder

    if len(ydata_patterns)==0:
        load_patterns()
    if len(trainingSet)==0:
        trainingSet=copy.deepcopy(ydata_patterns)
    print ('тест Шапиро-Вилкенсона(нормальное распределение?) всей базы:')
    for x in range(len(trainingSet)):
        for y in range(len(trainingSet[x])):
            if stats.shapiro(trainingSet[x][y])[-1]>0.05:
                print ('не нормальное распределение',patterns_kat[x],folder[x+1][2][y])
    print ('тест всей базы завершен..')
    
rgb=['red','pink','green','blue','orange','magenta','yellow','black','grey','red','green','blue','red','green','blue','red','green','blue','red','green','blue']

filter_data = '0'
comport=''
update_period = 5
serial_object = None
connect1=0
disconnect1=0
interp_timepoints=[]
interp_sig=[]
plav_okno=10 #по скольким отсчетам усредняем (размер плавающего окна)

folder=[]
timepoints=[]
ydata=[]
metka=False
metkabuf=[]
kategories=[]
pic_list=[]
pic_file_list=[]
mediumSignal=[]
mediumTime=[]

timepoints2=[]
ydata2=[]
metkabuf2=[]
kategories2=[]
pic_list2=[]
pic_file_list2=[]

patterns=[]
patterns_kat=[]

timepoints_patterns=[]
medium_pattern_signal=[]
medium_pattern_signal_time=[]
pattern_fft_power=[] #fft мощности паттернов для сравнения методом KNN
pattern_Hist_bins=[]
traningSet=[]

list_1=0
list_2=0

if __name__ == "__main__":

    root = Tk()
    root.title("Analizer v4.7")
    menu = Menu(root)
    root.config(menu=menu)

    note = ttk.Notebook(root)
    tab1 = Frame(note)
    tab2 = Frame(note)
    tab3 = Frame(note)
    
    note.add(tab1, text = "Главное")
    note.add(tab2, text = "Паттерны")
    note.add(tab3, text = "RGB спектрометр")

    file = Menu(menu)

    file.add_command(label = 'Help', command = help)
    file.add_command(label = 'Open file 1', command = loadData1)
    file.add_command(label = 'Open file 2', command = loadData2)
    file.add_command(label = 'Open file Spectrometr', command = loadDataRGB)
    file.add_command(label = 'Exit', command = lambda:exit())
    menu.add_cascade(label = 'File', menu = file)

    

    label_param=Label(tab1,text='Состояние: ')
    label_param.grid(row=1,column=0,padx=10)

    label_sred=Label(tab1,text='Усреднять по: ')
    label_sred.grid(row=2,column=0,padx=10)

    okno_entry=Entry(tab1)
    okno_entry.grid(row=2,column=1, padx=10, pady=5)
    okno_entry.insert(0, "10")
    
    disp_view = BooleanVar()
    disp_view.set(0)
    disp = Checkbutton(tab1,text="Показ дисперсии", variable=disp_view, onvalue=1, offvalue=0)
    disp.grid(row=3, column=0, padx=2, pady=2, sticky='nesw')

    baud =Text(tab1,height=4,width=22)
    baud.grid(row=1,column=1,sticky=E)
    baud.insert('1.0','Параметры загруженных данных:')   

    rgb1 = Button(tab3,text="Вывод сигнала", command=analisSignalRgb)
    rgb1.grid(row=1,column=1,padx=10,pady=10)

    rgb2=Button(tab3,text="Спектр R",command=lambda:analisFFT(color='r'))
    rgb2.grid(row=2,column=1,padx=10,pady=10)
    rgb3=Button(tab3,text="Спектр G",command=lambda:analisFFT(color='g'))
    rgb3.grid(row=3,column=1,padx=10,pady=10)
    rgb4=Button(tab3,text="Спектр B",command=lambda:analisFFT(color='b'))
    rgb4.grid(row=4,column=1,padx=10,pady=10)

    rgb5=Button(tab3,text="Гистограмма R",command=lambda:analisHist(color='r'))
    rgb5.grid(row=2,column=2,padx=10,pady=10)
    rgb6=Button(tab3,text="Гистограмма G",command=lambda:analisHist(color='g'))
    rgb6.grid(row=3,column=2,padx=10,pady=10)
    rgb7=Button(tab3,text="Гистограмма B",command=lambda:analisHist(color='b'))
    rgb7.grid(row=4,column=2,padx=10,pady=10)

    rgb8=Button(tab3,text="Сохранить паттерны R",command=lambda:save_rgb_patterns(color='r'))
    rgb8.grid(row=2,column=3,padx=10,pady=10)
    rgb9=Button(tab3,text="Сохранить паттерны G",command=lambda:save_rgb_patterns(color='g'))
    rgb9.grid(row=3,column=3,padx=10,pady=10)
    rgb10=Button(tab3,text="Сохранить паттерны B",command=lambda:save_rgb_patterns(color='b'))
    rgb10.grid(row=4,column=3,padx=10,pady=10)

    baud_rgb_patterns =Text(tab3,height=30,width=40)
    baud_rgb_patterns.grid(row=0,column=4,sticky=W,rowspan=11)
    baud_rgb_patterns.insert('1.0','...')

    rgb11=Button(tab3,text="Загрузить паттерны RGB",command=load_rgb_patterns)
    rgb11.grid(row=1,column=3,padx=10,pady=10)

    rgb12_b=Button(tab3,text="Спектр.средн.",command=view_patterns)
    rgb12_b.grid(row=11,column=2,padx=10,pady=10)

    Label(tab3,text="Выбрать интервал на графике:").grid(row=5, column=1)
    
    list_rgb_metok = Listbox(tab3,width=30,selectmode= SINGLE)
    list_rgb_metok.grid(row=6,column=1,padx=1,pady=10,rowspan=4)

    rgb11=Button(tab3,text="Сигнал.средн.",command=view_patterns)
    rgb11.grid(row=11,column=1,padx=10,pady=10)

    Label(tab3,text="Список загруженных паттернов:").grid(row=5, column=2,sticky=W)
    
    list_rgb_patterns = Listbox(tab3,width=40,selectmode= SINGLE)
    list_rgb_patterns.grid(row=6,column=2,padx=1,pady=10,rowspan=4)

    rgb12=Button(tab3,text="Спектр.средн.",command=view_med_fft)
    rgb12.grid(row=11,column=2,padx=10,pady=10)
    
    rgb_search_pattern = Button(tab3,text="Тип сигнала по KNN", command=pattern_signal_KNN_rgb)
    rgb_search_pattern.grid(row=7,column=3,padx=10,pady=10)
    rgb_search_pattern = Button(tab3,text="Тип Спектра по KNN", command=pattern_FFT_KNN_rgb)
    rgb_search_pattern.grid(row=8,column=3,padx=10,pady=10)
    rgb_search_pattern = Button(tab3,text="Тип Гистогр. по KNN", command=pattern_Hist_KNN_rgb)
    rgb_search_pattern.grid(row=9,column=3,padx=10,pady=10)

    
    
    b6 = Button(tab1,text="Вывод сигнала", command=analisSignal)
    b6.grid(row=1,column=2,padx=10,pady=10)

    b7 = Button(tab1,text="Спектр сигнала", command=analisFFT)
    b7.grid(row=2,column=2,padx=10,pady=10)

    b8 = Button(tab1,text="Гистограмма", command=analisHist)
    b8.grid(row=3,column=2,padx=10,pady=10)

    b9 = Button(tab1,text="Корреляция", command=corrSig)
    b9.grid(row=5,column=0,padx=10,pady=10)

    b9 = Button(tab1,text="Сравн.гистограмм", command=deltaHist)
    b9.grid(row=6,column=0,padx=10,pady=10)
    b10 = Button(tab1,text="Сравн.спектров", command=deltaFFT)
    b10.grid(row=7,column=0,padx=10,pady=10)

    b6_m = Button(tab1,text="Средн.сигнал", command=mediumSig)
    b6_m.grid(row=11,column=0,padx=10,pady=10)
    b9_m = Button(tab1,text="Средн.гистограмма", command=mediumHist)
    b9_m.grid(row=12,column=0,padx=10,pady=10)
    b10_m = Button(tab1,text="Средн.спектр", command=mediumFFT)
    b10_m.grid(row=13,column=0,padx=10,pady=10)

    b6_m2 = Button(tab1,text="Средн.сигнал", command=mediumSig2)
    b6_m2.grid(row=11,column=4,padx=10,pady=10)
    b9_m2 = Button(tab1,text="Средн.гистограмма", command=mediumHist2)
    b9_m2.grid(row=12,column=4,padx=10,pady=10)
    b10_m2 = Button(tab1,text="Средн.спектр", command=mediumFFT2)
    b10_m2.grid(row=13,column=4,padx=10,pady=10)
    
#    b11 = Button(text="Столбчатая диагр.", command=barGraph)
#    b11.grid(row=7,column=0,padx=10,pady=10)
    
    Label(tab1,text="Отрезки времени:").grid(row=3, column=1)
    
    list_metok = Listbox(tab1,width=30,selectmode= EXTENDED)
    list_metok.grid(row=5,column=1,padx=1,pady=10,rowspan=4)

    b_search_pattern = Button(tab1,text="Тип сигнала по KNN", command=pattern_signal_KNN_old)
    b_search_pattern.grid(row=11,column=1,padx=10,pady=10)

    b_search_pattern = Button(tab1,text="Тип Спектра по KNN", command=pattern_FFT_KNN_old)
    b_search_pattern.grid(row=12,column=1,padx=10,pady=10)

    b_search_pattern = Button(tab1,text="Тип Гистогр. по KNN", command=pattern_Hist_KNN_old)
    b_search_pattern.grid(row=13,column=1,padx=10,pady=10)

    baudKNN =Text(tab1,height=8,width=32)
    baudKNN.grid(row=11,column=2,rowspan=3,sticky=E)

    b6_2 = Button(tab1,text="Вывод сигнала2", command=analisSignal2)
    b6_2.grid(row=1,column=4,padx=10,pady=10)

    b7_2 = Button(tab1,text="Спектр сигнала2", command=analisFFT2)
    b7_2.grid(row=2,column=4,padx=10,pady=10)

    b8_2 = Button(tab1,text="Гистограмма2", command=analisHist2)
    b8_2.grid(row=3,column=4,padx=10,pady=10)

    b9_2 = Button(tab1,text="Сравн.гистограмм2", command=deltaHist2)
    b9_2.grid(row=5,column=4,padx=10,pady=10)

    b10_2 = Button(tab1,text="Сравн.спектров2", command=deltaFFT2)
    b10_2.grid(row=6,column=4,padx=10,pady=10)
    
#    b11_2 = Button(text="Столбчатая диагр.2", command=barGraph2)
#    b11_2.grid(row=7,column=4,padx=10,pady=10)
    

    Label(tab1,text="Отрезки времени:").grid(row=3, column=3)

    
    list_metok2 = Listbox(tab1,width=30,selectmode=  EXTENDED)
    list_metok2.grid(row=5,column=3,padx=1,pady=10,rowspan=4)
    

    b9_d = Button(tab1,text="<-гистограмма->", command=deltaHist_D)
    b9_d.grid(row=5,column=2,padx=10,pady=10)

    b10_d = Button(tab1,text="<-спектры->", command=deltaFFT_D)
    b10_d.grid(row=6,column=2,padx=10,pady=10)

    b11_d = Button(tab1,text="стат.обработка", command=statSig)
    b11_d.grid(row=7,column=2,padx=10,pady=10)
    
#    b11_d = Button(text="<-Столбчатая диагр->", command=barGraph_D)
#    b11_d.grid(row=7,column=2,padx=10,pady=10)


    list_metok.bind('<<ListboxSelect>>', lambda e: onselect(e, list_metok))
    list_metok2.bind('<<ListboxSelect>>', lambda e: onselect(e, list_metok2))



    
#вкладка Паттерны

    
    b_save= Button(tab2,text="Сохранить паттерны файла 1", command=save_pattern)
    b_save.grid(row=0,column=0,padx=10,pady=10)

    b_save2= Button(tab2,text="Сохранить паттерны файла 2", command=save_pattern2)
    b_save2.grid(row=1,column=0,padx=10,pady=10)

    Label(tab2,text="Список всех паттернов:").grid(row=3, column=0,sticky=W)
    
    list_patterns = Listbox(tab2,width=40,selectmode= SINGLE)
    list_patterns.grid(row=4,column=0,padx=1,pady=10,rowspan=6)

    Label(tab2,text="Состояние:").grid(row=11, column=0,sticky=W)

    baud_patterns =Text(tab2,height=4,width=30)
    baud_patterns.grid(row=12,column=0,sticky=W)
    baud_patterns.insert('1.0','...')

    b_list_patterns= Button(tab2,text="Показать списки паттернов", command=init_list_patterns)
    b_list_patterns.grid(row=0,column=1,padx=10,pady=10)

    b_shapiro_test_patterns= Button(tab2,text="Проверить нормальность паттернов", command=shapiro_test_patterns)
    b_shapiro_test_patterns.grid(row=0,column=2,padx=10,pady=10)

    b_load_pattern= Button(tab2,text="Загрузить паттерны", command=load_patterns)
    b_load_pattern.grid(row=1,column=1,padx=10,pady=10)

    b_view_pattern= Button(tab2,text="Паттерн", command=view_all_patterns)
    b_view_pattern.grid(row=4,column=1,padx=10,pady=10)

    b_view_fft_pattern= Button(tab2,text="Спектр", command=view_fft_patterns)
    b_view_fft_pattern.grid(row=5,column=1,padx=10,pady=10)

    b_view_hist_pattern= Button(tab2,text="Гистограмма", command=view_hist_patterns)
    b_view_hist_pattern.grid(row=6,column=1,padx=10,pady=10)

    b_normalise_data = Button(tab2,text="Нормализовать данные", command=normalise_data)
    b_normalise_data.grid(row=7,column=1,padx=10,pady=10)

    b_knn_tochnoct = Button(tab2,text="оценить точность KNN (фон макс)", command=ocenkaKNN)
    b_knn_tochnoct.grid(row=8,column=1,padx=10,pady=10)
    
    b_knn_tochnoct_mean_fon = Button(tab2,text="точность KNN(фон мин)", command=bez_fon_KNN)
    b_knn_tochnoct_mean_fon.grid(row=9,column=1,padx=10,pady=10)

    b_mean = Button(tab2,text="Оценка(средн) KNN", command=mean_KNN)
    b_mean.grid(row=10,column=1,padx=10,pady=10)

    b_mean_fft = Button(tab2,text="FFT спектры KNN", command=mean_FFT_KNN)
    b_mean_fft.grid(row=11,column=1,padx=10,pady=10)

    b_mean_hist = Button(tab2,text="Гистограммы KNN", command=mean_hist_KNN)
    b_mean_hist.grid(row=12,column=1,padx=10,pady=10)

    b_1000 = Button(tab2,text="1000 KNN", command=mean_1000_KNN)
    b_1000.grid(row=11,column=2,padx=10,pady=10)

    b_ravn_fon = Button(tab2,text="уравнять фон", command=ravn_fon)
    b_ravn_fon.grid(row=12,column=2,padx=10,pady=10)

     
    note.pack()
    root.mainloop()
