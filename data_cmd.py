from tkinter import *
from tkinter import filedialog as fd
import tkinter.ttk as ttk
import numpy as np


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

file_name="0.dat"

CCDSize=11082 # раземер одного измерения (кол-во данных с трех  CCD матриц)

#данные записаны в виде rRgGbBrRgGBb...


import argparse

parser = argparse.ArgumentParser(description='Get data_stream.dat, find center mass of laser points and and save in to new file Data_stream_r.dat,*_g.dat,*_b.dat')
parser.add_argument("-r", default=643, type=int, help="red lenght of start point CCD in nm. default - 643nm")
parser.add_argument("-g", default=503, type=int, help="green lenght of start point CCD in nm. default - 503nm")
parser.add_argument("-b", default=433, type=int, help="blue lenght of start point CCD in nm. default - 433nm")
parser.add_argument("-part", default=0.33, type=float, help="middle point btw Min and Max of laserpick")
parser.add_argument("-file", required=True, type=str, help="file name of *.dat")
args = parser.parse_args()
red_mid = args.r
green_mid = args.g
blue_mid = args.b

part = args.part
file_name=args.file

#print(red_mid,green_mid,blue_mid,part)
#print(file_name)



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
    global file_name

    CCDnumR=[]
    CCDnumG=[]
    CCDnumB=[]
    readData=[]
    CCDrawR.clear()
    CCDrawG.clear()
    CCDrawB.clear()
    red.clear()
    green.clear()
    blue.clear()
    
    print("loading data..")
    

    if file_name :
        #baud.delete('1.0', END)
        #baud.insert(END,'загрузка..')
        with open(file_name,'rb') as f:
            ydata_rgb=f.read() #загружаем данные из файла в переменную ydata_rgb
        
        num_frames=int(len(ydata_rgb)/(CCDSize*2)) #количество фреймов (сколько раз сняли показания)
        #(CCDSize*2) - размер передаваемых данных. т.к. АЦП 12 битный, то для передачи данных об 1 пикселе каждой CCD линейки необходимо 2 байта

        for j in range(0,num_frames):
            for i in range (0,CCDSize*2,2):
                if i<len(ydata_rgb):
                    p=((ydata_rgb[j*CCDSize*2+i+1]<<8)|ydata_rgb[j*CCDSize*2+i]) # преобразуем каждые два байта обратно в 12 битное значение и запишем в переменную P
                    readData.append(p) #этот массив содержит все данные из фрейма
            #работаем с очередным фреймом данных
            CCDnumR=readData[0::3] #данные с красной CCD-линейки находятся в каждом 3-м переданном байте (rRgGbBrRgGBb...), выдергиваем их
            CCDnumG=readData[1::3] #данные с зеленой CCD-линейки идут следом
            CCDnumB=readData[2::3] #данные с синей CCD-линейки идут следом

            #Вариант 1:
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
            
            CCDrawR.append(CCDnumR) #запишем
            CCDrawG.append(CCDnumG)
            CCDrawB.append(CCDnumB)
            readData.clear()

    
    CCDnumR.clear()
    CCDnumG.clear()
    CCDnumB.clear()
    print ("frames:",len(CCDrawR))
    #baud.delete('1.0', END)
    #baud.insert(END,'файл загружен')
    print("Done")
    
#чтобы получить длину волны в нанометрах надо сделать следующее преобразование:
#red[i]*0.0098+red_mid
#green[i]*0.0098+green_mid
#blue[i]*0.0098+blue_mid 

def center_mass(array_mass): #наодим индекс центра масс пика
    first_point=0 #номер индекса первой точки пика
    a=[]
    
    min_cm=min(array_mass[:-1])
    max_cm=max(array_mass[:-1])
    #print(min_cm,max_cm)
    delta_cm=(max_cm-min_cm)*part #делаем срез на высоте 1/3  емжду мин и макс значением всего графика(отслеживаем центр масс начиная с высоты 1/3 пика от основания)
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


def SaveDataRGB():
    print("saving new files..")
    if file_name :
        r_file_name=file_name[:-4]+'_r'+'.dat'
        with open(r_file_name,'w') as f:
           i=len(CCDrawR)
           print("frames_r:",i)
           n=0
           while n < i:
               j=0
               while j<len(CCDrawR[n]):
                   f.write(str(j*0.0098+red_mid)+' '+str(CCDrawR[n][j])+'\n')
                   j +=1
               n+=1

        f.close()
        g_file_name=file_name[:-4]+'_g'+'.dat'
        with open(g_file_name,'w') as f:
           i=len(CCDrawG)
           print("frames_g:",i)
           n=0
           while n < i:
               j=0
               while j<len(CCDrawG[n]):
                   f.write(str(j*0.0098+green_mid)+' '+str(CCDrawG[n][j])+'\n')
                   j +=1
               n+=1

        f.close()        
        b_file_name=file_name[:-4]+'_b'+'.dat'
        with open(b_file_name,'w') as f:
           i=len(CCDrawB)
           print("frames_b:",i)
           n=0
           while n < i:
               j=0
               while j<len(CCDrawB[n]):
                   f.write(str(j*0.0098+blue_mid)+' '+str(CCDrawB[n][j])+'\n')
                   j +=1
               n+=1

        f.close() 
    print("Done!")    


loadDataRGB()
SaveDataRGB()


