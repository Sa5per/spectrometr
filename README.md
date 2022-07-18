# Spectrometr
triband fiber-optic laser spectrometr

# Hardware
see https://tcd1304.wordpress.com/

optical part - 3pcs TCD1304AP (Toshiba CCD-line)

![image](https://user-images.githubusercontent.com/109242312/178824541-b28361f7-9994-4c43-a802-ce1d4a4a84b5.png)

electrical part - Laptop-(ethernet)-Raspberry-(SPI)-NucleoF401RE-TCD1304

Here is a firmware for 3 CCDs. The firmware uses SPI, so follow the
rpi-specific steps on my site. Because the ADC needs time to scan
across the output of 3 CCDs, the MCLK is 2,0 MHz for this particular
firmware (my normal SPI-firmware is 4,0 MHz).

Connect each CCD to the same outputs on the nucleo, and use PC0, PC1
and PC2 for the ADC-input for the CCDs.

The data coming from the nucleo is arranged like this:

buffer[0] = ccd1[1]

buffer[1] = ccd2[1]

buffer[2] = ccd3[1]

buffer[3] = ccd1[2]

buffer[4] = ccd2[2]

buffer[5] = ccd3[2]
..

buffer[11082-3] = ccd1[3694]

buffer[11082-2] = ccd2[3694]

buffer[11082-1] = ccd3[3694]

# software

data_cmd.py - программа преобразования сырых данных со спектрометра (12 битные числа) в текстовый файл, пригодный для обработки данных в экселе

как запускать:

python data_cmd.py -file data_stream.dat

полная передача всех параметров выглядит так:

python data_cmd.py -r 650 -g 532 -b 405 -part 0.5 -file data_stream.dat
 
где буквы r,g,b задают длину волны для первого пикселя каждой ПЗС линейки.(по умолчанию 643,503,433)
part - это множитель, который указывает, с какой части графика обрабатывать горб (пик): 1 - это с учетом самого низкого значения (сюда попадают значения от всех пикселей пзс-линейки), 0.9 - это только  самое максимальное значение (самый верхний пиксель пика). оптимально брать 0.33 - это означает, что нижняя треть графика в расчет не берется вообще.

Analiser_v4.7 - программа обработки данных с трехканального лазерного оптоволоконного спектрометра

#analiser_v4.7 - main programm for postprocessing

пример спектра:
![спектр по максимуму](https://user-images.githubusercontent.com/109242312/178810478-5c541e99-16a5-42e7-9e0b-afd787b602d7.png)

окно программы:
![image](https://user-images.githubusercontent.com/109242312/178818678-647d94bf-e224-43bd-a509-80d82714900f.png)

![image](https://user-images.githubusercontent.com/109242312/178818780-9b2a03c8-6376-4c6b-b578-5fd83235aaf4.png)
![image](https://user-images.githubusercontent.com/109242312/178818856-614c5b17-88ec-4850-89f8-a4da76f7a4d3.png)

Окно программы управления на Raspberry:
![IMG20220401135538](https://user-images.githubusercontent.com/109242312/179446078-9878d343-ecf9-423a-b536-e28372513f3a.jpg)


Конструкция спектрометра:
![IMG_20210402_170915](https://user-images.githubusercontent.com/109242312/179446144-a094ae2a-3081-4de0-97e3-a899df6f5d76.jpg)
![IMG_20210409_081330](https://user-images.githubusercontent.com/109242312/179446148-a4c04ff9-0657-4b01-afab-b8096f0bb8e5.jpg)

Налобный датчик:
![IMG20220401135557](https://user-images.githubusercontent.com/109242312/179446222-6876ccbd-b2fc-4723-ab4c-0a2c4ac6a7a9.jpg)
