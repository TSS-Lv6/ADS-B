#! /usr/bin/python3
# coding=utf-8

# Autostart
# sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
# #@xscreeensaver –no –splash
# @/usr/bin/python3 /home/pi/ppi.py &

# sudo apt-get install xscreensaver

# Inställning skärm
# sudo nano /boot/config.txt
# hdmi_group=2
# hdmi_mode=87
# hdmi_cvt=1280 1024 60 3
# hdmi_drive=1

# Importerar bibliotek
import json
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import requests
import time
import threading
from math import sin, cos, sqrt, atan2, radians, degrees
from PIL import Image
import psutil
import subprocess

# Bortkommenterad del för att kunna köras i laptop. Nyttjas med Rpi
'''
# New for km mode button
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(16,GPIO.IN, pull_up_down=GPIO.PUD_UP) # 16 för avst
GPIO.setup(12,GPIO.IN, pull_up_down=GPIO.PUD_UP) # 12 för ringar
GPIO.setup(24,GPIO.IN, pull_up_down=GPIO.PUD_UP) # 24 för karta
GPIO.setup(23,GPIO.IN, pull_up_down=GPIO.PUD_UP) # 23 för att slå av Rpi
GPIO.setup(14,GPIO.IN, pull_up_down=GPIO.PUD_UP) # 23 för att stoppa programmet
GPIO.add_event_detect(12, GPIO.FALLING) # 16 för avst
GPIO.add_event_detect(16, GPIO.FALLING) # 12 för ringar
GPIO.add_event_detect(24, GPIO.FALLING) # 24 för karta
GPIO.add_event_detect(23, GPIO.FALLING) # 23 för att slå av Rpi
GPIO.add_event_detect(14, GPIO.FALLING) # 23 för att stoppa programmet
#  2  4  6  8  10  12  14  16  18  20  22  24  26  28  30  32  34  36  38  40
# 5V 5V  G 14  15  18   G  23  24   G  25   8   7  SC   G  12   G  16  20  21
'''
# End of bortkommenterad del för att kunna köras i laptop. Nyttjas med Rpi

######################################
# Här skall egen lat/long ställas in #
# Grader och decimaler av grader     #
egenLat = 56.691 # 56.676            #
egenLong = 12.857 # 12.857           #
######################################

# Setup av pygame
pygame.init()
pygame.display.set_caption('Data från FR24')
mediumfont = pygame.font.SysFont("monospace", 32, bold = True) #monospace
smallermediumfont = pygame.font.SysFont("monospace", 18, bold = True)
smallfont = pygame.font.SysFont("monospace", 15, bold = True)
size = [1280, 1024]
#screen = pygame.display.set_mode(size, 0 ,0)
screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
pygame.mouse.set_visible(False)
my_clock = pygame.time.Clock()
ppiMittX = 512
ppiMittY = 512

# Definition av färger
BLACK = (0, 0, 0)
GREEN = (0, 175, 0)
MEDIUMGREEN = (0, 125, 0)
DARKGREEN = (0, 75, 0)
DARKERGREEN = (0,25,0)
RED = (255, 0, 0)
BLUE = (30, 60, 255)
WHITE = (255, 255, 255)

# Definition av konstanter
R = 6373.0
PI = 3.141592653

# Definierar variabler och listor
angle = 0.0  # Svepets vinkel på ppi:et
updateCounter = 100  # Stegar upp från 0 till 60 på en sekund
wifiStatus = 0
antalMottagnaFlygplan = 0
tgtWarning = 0
egetWarning = 0
cpu_usage = psutil.cpu_percent()
cpu_load = psutil.cpu_percent()
mottagenListaMedFlygplan = []
internListaMedFlygplan = []
ettFlygplansData = []
ListaMedGamlaPositionerX = []
ListaMedGamlaPositionerY = []

# Initial settings
kmMode50 = False
kartaOn = True
nyKartaOn = True
colorKarta = True
svepOn = False
avstRingarOn = True
reloadKarta = True

# Text
txtFM = smallermediumfont.render("FÖLJDA MÅL", True, MEDIUMGREEN)
txtRubrik = smallfont.render("ID       TYP   RI KURS AVST", True, MEDIUMGREEN)
txtStatus = smallermediumfont.render("STATUS", True, MEDIUMGREEN)
txtSystem = smallermediumfont.render("SYSTEM", True, MEDIUMGREEN)
txtTid = smallermediumfont.render("TID", True, MEDIUMGREEN)
txt50 = smallermediumfont.render("50 KM", True, MEDIUMGREEN)
txt100 = smallermediumfont.render("100 KM", True, MEDIUMGREEN)
txtRingarTill = smallermediumfont.render("AVSTÅNDSRINGAR TILL", True, MEDIUMGREEN)
txtRingarFran = smallermediumfont.render("AVSTÅNDSRINGAR FRÅN", True, MEDIUMGREEN)
txtCpu = smallermediumfont.render("% CPU ANVÄNDNING", True, MEDIUMGREEN)
txtWifiOk = smallermediumfont.render("WIFI OK", True, MEDIUMGREEN)
txtWifiNo = smallermediumfont.render("INGEN KONTAKT MED WIFI", True, MEDIUMGREEN)
txtMal = smallermediumfont.render("MÅL MOTTAGNA", True, MEDIUMGREEN)
txtTgt = smallermediumfont.render("TGT", True, RED)
txtTgtNo = smallermediumfont.render("0 TGT", True, MEDIUMGREEN)
txtEget = smallermediumfont.render("VÅRT FLYG I LUFTEN", True, BLUE)
textWifiOff = mediumfont.render('WIFI OFF?', True, RED)

# För att hämta data från fr24
class GetData(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.running = True

    def run(self):
        global mottagenListaMedFlygplan, antalMottagnaFlygplan, wifiStatus
        while self.running:
            time.sleep(1)
            try:
                mottagetMeddelande = requests.get(url = "https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds=58.00,54.00,11.00,15.00", headers = {'User-Agent': 'Mozilla/5.0'}, timeout = 1)
                mottagenListaMedFlygplan  = json.loads(mottagetMeddelande.content)
                #print(mottagenListaMedFlygplan)
                if (len(mottagenListaMedFlygplan)-2) >= 0:
                    del mottagenListaMedFlygplan["version"]
                    del mottagenListaMedFlygplan["full_count"]
                #print(mottagenListaMedFlygplan)
                antalMottagnaFlygplan = len (mottagenListaMedFlygplan)
                wifiStatus = 10
            except:
                if wifiStatus > 0:
                    wifiStatus = wifiStatus - 1
                else:
                    wifiStatus = 0
                    antalMottagnaFlygplan = 0

fr24GetData = GetData()
fr24GetData.daemon = True
fr24GetData.start()


#############
# Huvudloop #
#############
done = False
while not done:
    ###############################################
    # Saker som enbart skall utföras varje sekund #
    ###############################################
    if ((updateCounter >= 5 and nyKartaOn == True) or (updateCounter >= 30 and nyKartaOn == False)):
        updateCounter = 0
        tgtWarning = 0
        egetWarning = 0
        internListaMedFlygplan = []

        for event in pygame.event.get():
            # Stoppa programmet med tangentbord
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if pygame.key.name(event.key) == 'escape':
                    done = True

            # Byta avstånd med tangentbord
            if event.type == pygame.KEYDOWN:
                if pygame.key.name(event.key) == 'a':
                    reloadKarta = True
                    kmMode50 = not kmMode50

            # Avståndsringar på/av med tangentbord
            if event.type == pygame.KEYDOWN:
                if pygame.key.name(event.key) == 'r':
                    avstRingarOn = not avstRingarOn

            # Stega mellan olika kartbakgrunder med tangentbord
            if event.type == pygame.KEYDOWN:
                if pygame.key.name(event.key) == 'k':
                    reloadKarta = True
                    if nyKartaOn == True and colorKarta == True:
                        colorKarta = False
                    elif nyKartaOn == True and colorKarta == False:
                        nyKartaOn = False
                        svepOn = True
                    elif nyKartaOn == False and kartaOn == True:
                        kartaOn = False
                        svepOn = True
                    else:
                        kartaOn = True
                        nyKartaOn = True
                        colorKarta = True
                        svepOn = False

            # Slå av med tangentbord
            if event.type == pygame.KEYDOWN:
                if pygame.key.name(event.key) == 'q':
                    subprocess.run(["sudo shutdown -h now"], shell=True)

        # Bortkommenterad del för att kunna köras i laptop. Nyttjas med Rpi
        '''
        # Byte av avstånd med knapp
        if GPIO.event_detected(16):
            reloadKarta = True
            kmMode50 = not kmMode50
        
        # Avståndsringar på/av med knapp
        if GPIO.event_detected(12):
            avstRingarOn = not avstRingarOn
        
        # Stega mellan olika kartbakgrunder med knapp
        if GPIO.event_detected(24):
            reloadKarta = True
            if nyKartaOn == True and colorKarta == True:
                colorKarta = False
            elif nyKartaOn == True and colorKarta == False:
                nyKartaOn = False
                svepOn = True
            elif nyKartaOn == False and kartaOn == True:
                kartaOn = False
                svepOn = True
            else:
                kartaOn = True
                nyKartaOn = True
                colorKarta = True
                svepOn = False
        
        # Slå av Rpi med knapp
        if GPIO.event_detected(23):
            subprocess.run(["sudo shutdown -h now"], shell = True)

        # Stoppa programmet med knapp
        if GPIO.event_detected(14):
            done = True
        '''
        # End of bortkommenterad del för att kunna köras i laptop. Nyttjas med Rpi

        # Repeterar för varje flygplan i den mottagna flygplanslistan
        if antalMottagnaFlygplan > 0:
            # Repetera för varje mål
            try:
                for i in mottagenListaMedFlygplan:
                    #print(mottagenListaMedFlygplan[i])
                    lat = mottagenListaMedFlygplan[i][1]
                    long = mottagenListaMedFlygplan[i][2]
                    heading = mottagenListaMedFlygplan[i][3]
                    # alt = mottagenListaMedFlygplan[i][4]
                    speed = mottagenListaMedFlygplan[i][5]
                    # squawk = mottagenListaMedFlygplan [i][6]
                    typ = (mottagenListaMedFlygplan[i][8].encode("utf-8"))
                    regid = (mottagenListaMedFlygplan[i][9].encode("utf-8"))
                    hexKod = (mottagenListaMedFlygplan[i][0].encode("utf-8"))
                    fromAirport = (mottagenListaMedFlygplan[i][11].encode("utf-8"))
                    toAirport = (mottagenListaMedFlygplan[i][12].encode("utf-8"))
                    # print(idkod,lat,long,heading,id,typ)
                    lat1 = radians(egenLat)
                    lon1 = radians(egenLong)
                    lat2 = radians(lat)
                    lon2 = radians(long)
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                    c = 2 * atan2(sqrt(a), sqrt(1 - a))
                    avst = round((R * c), 2)
                    if avst < 110 and wifiStatus > 0:
                        x = sin(dlon) * cos(lat2)
                        y = cos(lat1) * sin(lat2) - (sin(lat1) * cos(lat2) * cos(dlon))
                        compass_bearing = (degrees(atan2(x, y)) + 360) % 360
                        riktning = int((compass_bearing + 15) / 30)
                        if riktning == 0:
                            riktning = 12
                        kurs = int((heading + 15) / 30)
                        if kurs == 0:
                            kurs = 12
                        speed = speed / 10
                        targetX = int(1.72 * 5 * (avst * sin(atan2(x, y))))
                        targetY = int(1.72 * 5 * (avst * cos(atan2(x, y))))

                        ListaMedGamlaPositionerX.append(targetX)
                        ListaMedGamlaPositionerY.append(targetY)

                        kursX = int(12 * sin(radians(heading)))
                        kursY = int(12 * cos(radians(heading)))
                        kursVektorX = int((speed + 12) * sin(radians(heading)))
                        kursVektorY = int((speed + 12) * cos(radians(heading)))
                        ettFlygplansData = [avst, riktning, kurs, regid, hexKod, targetX, targetY, kursX, kursY,
                                            kursVektorX, kursVektorY, fromAirport, toAirport, typ]
                        internListaMedFlygplan.append(ettFlygplansData)

                    if (regid[0:2] == b'60'
                            or regid[0:2] == b'84'
                            or regid[0:2] == b'17'
                            or regid[0:2] == b'10'):
                            #or regid[0:2] == b'SE'): # Test
                        egetWarning = egetWarning + 1

                    if (hexKod == b'4A9D02'  # SE-GHB TGT52
                            or hexKod == b'4A9D06'  # SE-GHF TGT56
                            or hexKod == b'4AA5F6'  # SE-IOV TGT57
                            or hexKod == b'4AA5FA'  # SE-IOZ TGT58
                            or hexKod == b'4AA6A1'  # SE-IUA TGT59
                            or hexKod == b'4A910F'  # SE-DHO TGT01
                            or hexKod == b'4A9110'  # SE-DHP TGT02
                            or hexKod == b'4AC861'#):  # SE-RCA TGT03
                            or regid[0:2] == b'70'): # Nya bet?
                            #or regid[0:2] == b'SE'): # Test
                            #or hexKod == b'458E4A'): # Test
                        tgtWarning = tgtWarning + 1

            except:
                pass

            # Sorterar den interna listan med flygplan efter avstånd
            internListaMedFlygplan.sort()
            internListaMedFlygplan = internListaMedFlygplan

        # För att efter hand ta bort gamla positioner då inga flygplan finns
        if len(internListaMedFlygplan) == 0 and len(ListaMedGamlaPositionerX) > 0:
            ListaMedGamlaPositionerX.pop(0)
            ListaMedGamlaPositionerY.pop(0)

        # Omarbetning av kartan
        if reloadKarta == True:
            try:
                kartMittX = (67.34 * egenLong) - 391  # Omvandling av grad till pixel i just denna karta
                kartMittY = (- 2.5 * egenLat * egenLat) + (163.25 * egenLat) + 755
                if kmMode50 == True:
                    kartBredd = 65  # För att kartans skala skall bli ungefär rätt
                else:
                    kartBredd = 130
                karta = Image.open("Bakgrundskarta_Sverige.png")  # 1545 x 2249 pixlar
                karta = karta.crop(
                    (kartMittX - kartBredd, kartMittY - kartBredd, kartMittX + kartBredd, kartMittY + kartBredd))
                karta = karta.resize([1024, 1024], resample=2)
                karta = pygame.image.fromstring(karta.tobytes(), karta.size, karta.mode)
                karta = karta.convert()
            except:
                print("Något gick fel vid inläsning och bearbetning av kartbakgrunden")

            try:
                nyKartMittX = 705
                nyKartMittY = 435
                if kmMode50 == True:
                    nyKartBredd = 208  # För att kartans skala skall bli ungefär rätt
                else:
                    nyKartBredd = 416
                if colorKarta == True:
                    nyKarta = Image.open("NewMap.png")
                else:
                    nyKarta = Image.open("NewMap2.png")
                nyKarta = nyKarta.crop((nyKartMittX - nyKartBredd, nyKartMittY - nyKartBredd, nyKartMittX + nyKartBredd,
                                        nyKartMittY + nyKartBredd))
                nyKarta = nyKarta.resize([1022, 1024], resample=2)
                nyKarta = pygame.image.fromstring(nyKarta.tobytes(), nyKarta.size, nyKarta.mode)
                nyKarta = nyKarta.convert()
            except:
                print("Något gick fel vid inläsning och bearbetning av kartbakgrunden")

            reloadKarta = False

        
        cpu_usage = psutil.cpu_percent()
        cpu_load = 0.9 * cpu_load + 0.1 * cpu_usage

    ######################################
    # Saker som skall utföras varje gång #
    ######################################
    # Ritar ut bakgrundskartan
    if kartaOn == True:
        try:
            if nyKartaOn == True:
                screen.blit(nyKarta, (0, 0))
            else:
                screen.blit(karta, (0, 0))
        except:
            pass

    # Ritar ut svepet
    if svepOn == True:
        x = int(-430*sin(angle)+ppiMittX)
        y = int(-430*cos(angle)+ppiMittY)
        pygame.draw.line(screen, DARKERGREEN, [ppiMittX, ppiMittY], [x, y], 4)

    # Svepets vinkel
    #angle = angle - .01047 #10 s
    #angle = angle - 0.0209 #5 s
    #angle = angle - 0.02618 #4 s
    #angle = angle - 0.039265 #3 s
    angle = angle - 0.05235 #2 s
    #angle = angle -0.1047 #1 s

    # Nollställ svepets vinkel
    if angle < 0:
        angle = angle +  2 * PI

    # Avstringar
    if avstRingarOn == True:
        pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX-86, ppiMittY-86, 172, 172], 2)
        pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX-172, ppiMittY-172, 344, 344], 2)
        pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX-258, ppiMittY-258, 516, 516], 2)
        pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX-344, ppiMittY-344, 688, 688], 2)
        pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX-430, ppiMittY-430, 860, 860], 2)

        if kmMode50 == False:
            pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 43, ppiMittY - 43, 86, 86], 2)
            pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 129, ppiMittY - 129, 258, 258], 2)
            pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 215, ppiMittY - 215, 430, 430], 2)
            pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 301, ppiMittY - 301, 602, 602], 2)
            pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 387, ppiMittY - 387, 774, 774], 2)

    # Mitten av ppi:et
    if svepOn == True:
        pygame.draw.ellipse(screen, BLACK, [ppiMittX - 10, ppiMittY - 10, 20, 20], 0)

    # Ritar ut listan med gamla positioner
    for j in range(len(ListaMedGamlaPositionerX)):
        ppiHistX = ListaMedGamlaPositionerX[j]
        ppiHistY = ListaMedGamlaPositionerY[j]
        if kmMode50 == False:
            ppiHistX = int(ppiHistX * 0.5)
            ppiHistY = int(ppiHistY * 0.5)
        if (ppiHistX*ppiHistX+ppiHistY*ppiHistY) < 262144:
            pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX + ppiHistX - 2, ppiMittY - ppiHistY - 2, 4, 4], 0)

    # Raderar de äldsta av de gamla positionerna
    while len(ListaMedGamlaPositionerX) > (antalMottagnaFlygplan * 20):
        ListaMedGamlaPositionerX.pop(0)
        ListaMedGamlaPositionerY.pop(0)

    # Textfält 1
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 15], [1092, 15], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1212, 15], [1280, 15], 2)
    screen.blit(txtFM, (1097, 5))
    screen.blit(txtRubrik, (1029, 25))
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 15], [1022, 505], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1278, 15], [1278, 505], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 505], [1280, 505], 2)

    # Textfält 2
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 519], [1112, 519], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1192, 519], [1280, 519], 2)
    screen.blit(txtStatus, (1120, 509))
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 519], [1022, 761], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1278, 519], [1278, 761], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 761], [1280, 761], 2)

    # Textfält 3
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 775], [1112, 775], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1192, 775], [1280, 775], 2)
    screen.blit(txtSystem, (1120, 765))
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 775], [1022, 1022], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1278, 775], [1278, 1022], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [1022, 1022], [1280, 1022], 2)

    # Klockan
    pygame.draw.line(screen, MEDIUMGREEN, [0, 979], [0, 1022], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [0, 1022], [171, 1022], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [170, 1022], [170, 979], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [0, 979], [65, 979], 2)
    pygame.draw.line(screen, MEDIUMGREEN, [106, 979], [171, 979], 2)
    screen.blit(txtTid, (70, 969))
    klockan = time.strftime("%H:%M:%S", time.localtime())
    texttime = mediumfont.render(str(klockan), True, MEDIUMGREEN)
    screen.blit(texttime, (10, 984))

    # Innehåll i textfält 3
    if kmMode50 == True:
        screen.blit(txt50, (1029, 783))
    else:
        screen.blit(txt100, (1029, 783))

    if avstRingarOn == True:
        screen.blit(txtRingarTill, (1029, 803))
    else:
        screen.blit(txtRingarFran, (1029, 803))

    screen.blit(smallermediumfont.render(str(int(cpu_load)), True, MEDIUMGREEN), (1029, 823))
    if cpu_load < 10:
        screen.blit(txtCpu, (1039, 823))
    else:
        screen.blit(txtCpu, (1049, 823))

    if wifiStatus > 0:
        screen.blit(txtWifiOk, (1029, 843))
    else:
        screen.blit(txtWifiNo, (1029, 843))

    # fps
    #screen.blit(smallermediumfont.render(str(int(my_clock.get_fps())), True, MEDIUMGREEN), (1029, 863))

    # Innehåll i textfält 2
    if wifiStatus > 0:
        # Skriver ut antal mål
        if antalMottagnaFlygplan >= 0:
            textAntal = smallermediumfont.render(str(antalMottagnaFlygplan), True, MEDIUMGREEN)
            screen.blit(textAntal, (1029, 527))
            if antalMottagnaFlygplan < 10:
                screen.blit(txtMal, (1049, 527))
            else:
                screen.blit(txtMal, (1059, 527))

        # Tgt varning
        if tgtWarning > 0:
            textAntalTgt = smallermediumfont.render(str(tgtWarning), True, RED)
            screen.blit(textAntalTgt, (1029, 547))
            if tgtWarning < 10:
                screen.blit(txtTgt, (1049, 547))
            else:
                screen.blit(txtTgt, (1059, 547))
        else:
            screen.blit(txtTgtNo, (1029, 547))

        # Eget varning
        if egetWarning > 0:
            screen.blit(txtEget, (1029, 567))

    else:
        screen.blit(textWifiOff, (840, 10))
        internListaMedFlygplan = []
        ListaMedGamlaPositionerX = []
        ListaMedGamlaPositionerY = []

    # Hanterar den interna listan för textfält 1 och ppi
    try:
        if kmMode50 == True:
            maxAvst = 60
        else:
            maxAvst = 110
        for j in range(len(internListaMedFlygplan)):
            #   0       1       2      3      4        5        6       7       8         9           10          11           12      13
            # [avst, riktning, kurs, regid, hexkod, targetX, targetY, kursX, kursY, kursVektorX, kursVektorY, fromAirport, toAirport, typ]
            textAvst = smallermediumfont.render(str(int(internListaMedFlygplan[j][0])), True, MEDIUMGREEN)
            textRiktning = smallermediumfont.render(str(internListaMedFlygplan[j][1]), True, MEDIUMGREEN)
            textKurs = smallermediumfont.render(str(internListaMedFlygplan[j][2]), True, MEDIUMGREEN)
            textRegid = smallermediumfont.render(internListaMedFlygplan[j][3], True, MEDIUMGREEN)
            textTyp = smallermediumfont.render(internListaMedFlygplan[j][13], True, MEDIUMGREEN)
            plats = (j * 25) + 45
            if plats < 490:
                screen.blit(textRegid, (1029, plats))
                screen.blit(textTyp, (1110, plats))
                if (internListaMedFlygplan[j][1]) < 10:
                    screen.blit(textRiktning, (1175, plats))
                else:
                    screen.blit(textRiktning, (1165, plats))
                if (internListaMedFlygplan[j][2]) < 10:
                    screen.blit(textKurs, (1210, plats))
                else:
                    screen.blit(textKurs, (1200, plats))
                if (internListaMedFlygplan[j][0]) < 10:
                    screen.blit(textAvst, (1260, plats))
                elif (internListaMedFlygplan[j][0]) < 100:
                    screen.blit(textAvst, (1250, plats))
                else:
                    screen.blit(textAvst, (1240, plats))

            # Sorterar ut mål som är närmare än max avstånd för att rita ut dessa
            if internListaMedFlygplan[j][0] < maxAvst:
                ppiRegid = internListaMedFlygplan[j][3]
                ppiHexKod = internListaMedFlygplan[j][4]
                ppiTargetX = internListaMedFlygplan[j][5]
                ppiTargetY = internListaMedFlygplan[j][6]
                ppiKursX = internListaMedFlygplan[j][7]
                ppiKursY = internListaMedFlygplan[j][8]
                ppiKursVektorX = internListaMedFlygplan[j][9]
                ppiKursVektorY = internListaMedFlygplan[j][10]
                ppiFromAirport = internListaMedFlygplan[j][11]
                ppiToAirport = internListaMedFlygplan[j][12]

                if kmMode50 == False:
                    ppiTargetX = int(ppiTargetX * 0.5)
                    ppiTargetY = int(ppiTargetY * 0.5)
                
                if nyKartaOn == True:
                    pygame.draw.line(screen, BLACK, [ppiMittX + ppiTargetX, ppiMittY - ppiTargetY - 4],
                                     [ppiMittX + ppiTargetX, ppiMittY - ppiTargetY + 4], 2)
                    pygame.draw.line(screen, BLACK, [ppiMittX + ppiTargetX + 4, ppiMittY - ppiTargetY],
                                     [ppiMittX + ppiTargetX - 4, ppiMittY - ppiTargetY], 2)
                else:
                    pygame.draw.line(screen, GREEN, [ppiMittX + ppiTargetX, ppiMittY - ppiTargetY - 4],
                                     [ppiMittX + ppiTargetX, ppiMittY - ppiTargetY + 4], 2)
                    pygame.draw.line(screen, GREEN, [ppiMittX + ppiTargetX + 4, ppiMittY - ppiTargetY],
                                     [ppiMittX + ppiTargetX - 4, ppiMittY - ppiTargetY], 2)

                # Kollar om målet skall märkas som eget
                #print(ppiRegid[0:2])
                if (ppiRegid[0:2] == b'60'
                        or ppiRegid[0:2] == b'84'
                        or ppiRegid[0:2] == b'17'
                        or ppiRegid[0:2] == b'10'):
                        #or ppiRegid[0:2] == b'SE'): # Test
                    pygame.draw.ellipse(screen, BLUE, [ppiMittX + ppiTargetX - 13, ppiMittY - ppiTargetY - 13, 27, 27], 3)
                    pygame.draw.line(screen, BLUE,
                                     [ppiMittX + ppiTargetX + ppiKursX, ppiMittY - ppiTargetY - ppiKursY],
                                     [ppiMittX + ppiTargetX + ppiKursVektorX,
                                      ppiMittY - ppiTargetY - ppiKursVektorY], 3)

                # Kollar om målet skall märkas som fientligt
                elif (ppiHexKod == b'4A9D02'  # SE-GHB TGT52
                        or ppiHexKod == b'4A9D06'  # SE-GHF TGT56
                        or ppiHexKod == b'4AA5F6'  # SE-IOV TGT57
                        or ppiHexKod == b'4AA5FA'  # SE-IOZ TGT58
                        or ppiHexKod == b'4AA6A1'  # SE-IUA TGT59
                        or ppiHexKod == b'4A910F'  # SE-DHO TGT01
                        or ppiHexKod == b'4A9110'  # SE-DHP TGT02
                        or ppiHexKod == b'4AC861'#):  # SE-RCA TGT03
                        or ppiRegid[0:2] == b'70'):  # Nya bet?
                        #or ppiHexKod == b'4408F5'): # Test
                        #or ppiRegid[0:2] == b'SE'):
                    pygame.draw.polygon(screen, RED, [[ppiMittX + ppiTargetX, ppiMittY - ppiTargetY - 10],
                                                      [ppiMittX + ppiTargetX - 10, ppiMittY - ppiTargetY + 10],
                                                      [ppiMittX + ppiTargetX + 10, ppiMittY - ppiTargetY + 10]], 3)
                    pygame.draw.line(screen, RED,
                                     [ppiMittX + ppiTargetX + ppiKursX, ppiMittY - ppiTargetY - ppiKursY],
                                     [ppiMittX + ppiTargetX + ppiKursVektorX,
                                      ppiMittY - ppiTargetY - ppiKursVektorY], 3)

                # Annars ritas målet ut som okänt
                else:
                    pygame.draw.rect(screen, GREEN,
                                     [ppiMittX + ppiTargetX - 10, ppiMittY - ppiTargetY - 10, 21, 21], 3)
                    pygame.draw.line(screen, GREEN,
                                     [ppiMittX + ppiTargetX + ppiKursX, ppiMittY - ppiTargetY - ppiKursY],
                                     [ppiMittX + ppiTargetX + ppiKursVektorX,
                                      ppiMittY - ppiTargetY - ppiKursVektorY], 3)

                # Skriver ut från till
                if (ppiMittX + ppiTargetX) < 974:
                    textfromairport = smallfont.render(ppiFromAirport, True, MEDIUMGREEN)
                    screen.blit(textfromairport, (ppiMittX + ppiTargetX + 13, ppiMittY - ppiTargetY + 12))
                    if (ppiFromAirport) != b'' or (ppiToAirport) != b'':
                        textstreck = smallfont.render('-', True, MEDIUMGREEN)
                        screen.blit(textstreck, (ppiMittX + ppiTargetX + 41, ppiMittY - ppiTargetY + 12))
                    texttoairport = smallfont.render(ppiToAirport, True, MEDIUMGREEN)
                    screen.blit(texttoairport, (ppiMittX + ppiTargetX + 51, ppiMittY - ppiTargetY + 12))
    except:
        pass

    # Display
    pygame.display.flip()
    if nyKartaOn == True:
        my_clock.tick(5)
    else:
        my_clock.tick(30)
    updateCounter = updateCounter + 1
    pygame.draw.rect(screen, BLACK, [0, 0, 1280, 1024], 0)

# Slut
pygame.quit()
