#! /usr/bin/python3
# coding=utf-8

# Importerar bibliotek
import ast
import json
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import requests
import sys
import time
from math import sin, cos, sqrt, atan2, radians, degrees
from PIL import Image

######################################
# Här skall egen lat/long ställas in #
# Grader och decimaler av grader     #
egenLat = 56.676                     #
egenLong = 12.857                    #
######################################

# Definierar var mottaget meddelande skall hämtas
API = "http://127.0.0.1/dump1090/data/aircraft.json"

# Konfigurerar Pygame (grafik)
pygame.init()
pygame.display.set_caption('Data från ADS-B')
mediumfont = pygame.font.SysFont("monospace", 20, bold=True)
smallfont = pygame.font.SysFont("monospace", 15, bold=True)
screensize = [1200, 600]
screen = pygame.display.set_mode(screensize)
pygame.mouse.set_visible(False)
my_clock = pygame.time.Clock()
ppiMittX = 300
ppiMittY = 300

# Konfigurerar bakgrundskartan
try:
    kartMittX = (67.34 * egenLong) - 391  # Omvandling av grad till pixel i just denna karta
    kartMittY = (- 2.5 * egenLat * egenLat) + (163.25 * egenLat) + 755
    kartBredd = 65  # För att kartans skala skall bli ungefär rätt
    karta = Image.open("Bakgrundskarta_Sverige.png")  # 1545 x 2249 pixlar
    karta = karta.crop((kartMittX - kartBredd, kartMittY - kartBredd, kartMittX + kartBredd, kartMittY + kartBredd))
    karta = karta.resize([600, 600], resample = 2)
    karta = pygame.image.fromstring(karta.tobytes(), karta.size, karta.mode)
    karta = karta.convert()
except:
    print("Något gick fel vid inläsning och bearbetning av kartbakgrunden")

# Definierar färger (R,G,B)
BLACK = (0, 0, 0)
GREEN = (0, 220, 0)
MEDIUMGREEN = (0, 150, 0)
DARKGREEN = (0, 100, 0)
DARKDARKGREEN = (0, 30, 0)
RED = (255, 0, 0)

# Definierar konstanter
R = 6373.0
PI = 3.141592653

# Definierar variabler och listor
done = False  # För att stoppa huvudloopen
angle = 0  # Svepets vinkel på ppi:et
updateCounter = 0  # Stegar upp från 0 till 60 på en sekund
antalMottagnaFlygplan = 0 
ListaMedGamlaPositionerX = []
ListaMedGamlaPositionerY = []
mottagenListaMedFlygplan = []
internListaMedFlygplan = []
ettFlygplansData = []

#############
# Huvudloop #
#############
while not done:
    # För att kunna stoppa programmet genom att stänga fönstret eller med ESC
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if pygame.key.name(event.key) == 'escape':
                done = True

    ###############################################
    # Saker som enbart skall utföras varje sekund #
    ###############################################
    if updateCounter >= 60:
        updateCounter = 0
        mottagenListaMedFlygplan = []
        internListaMedFlygplan = []
        
        # Läser in mottaget meddelande och plocka ut listan med flygplan ur meddelandet
        try:
            mottagetMeddelande = requests.get(url=API, headers={'User-Agent': 'Mozilla/5.0'}, timeout=1)
            #print(json.loads(mottagetMeddelande.content))  # Skriver ut hela det mottagna meddelandet
            mottagenListaMedFlygplan = json.loads(mottagetMeddelande.content)['aircraft']
            #print(mottagenListaMedFlygplan)  # Skriver ut listan med flygplan
            antalMottagnaFlygplan = len(mottagenListaMedFlygplan)
        except:
            antalMottagnaFlygplan = 0
        
        # Repeterar för varje flygplan i den mottagna flygplanslistan
        for i in mottagenListaMedFlygplan:
            ettFlygplan = ast.literal_eval(json.dumps(i, ensure_ascii=False))
            # print (ettFlygplan)

            # Sorterar innehållet i det mottagna meddelandet för varje flygplan
            try:
                hexKod = (ettFlygplan['hex']) # Flygplanets unika id
                altitude = (ettFlygplan['altitude']) # Höjd i fot
                squawk = (ettFlygplan['squawk'])
                targetLat = (ettFlygplan['lat'])
                targetLong = (ettFlygplan['lon'])
                heading = (ettFlygplan['track'])
                speed = (ettFlygplan['speed'])
                inTheDark = (ettFlygplan['seen_pos']) # Tid sedan positionsinformation mottagits
                ok = 1  # Om meddelandet är komplett
            except:
                ok = 0  # Om meddelandet inte är komplett
            
            # Kontrollerar om meddelandet också innehåller information om flight och kategori
            if ok == 1:
                try:
                    flight = (ettFlygplan['flight'])
                except:
                    flight = ("--")
                try:
                    kategori = (ettFlygplan['category'])
                    # A0 = No data, A1 = Light, A2 = Medium, A3 = Heavy, A4 = High vortex
                    # A5 = Very heavy, A6 = High performance, high speed, A7 = Rotocraft
                except:
                    kategori = ("--")

            # Gör beräkningar av avstånd och riktning mm om meddelandet är komplett och inte för gammalt
            if ok == 1 and inTheDark < 31:
                egenLatRad = radians(egenLat)
                egenLongRad = radians(egenLong)
                targetLatRad = radians(targetLat)
                targetLongRad = radians(targetLong)
                diffLat = targetLatRad - egenLatRad
                diffLong = targetLongRad - egenLongRad
                a = sin(diffLat / 2) ** 2 + cos(egenLatRad) * cos(targetLatRad) * sin(diffLong / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                avst = (R * c)
                x = sin(diffLong) * cos(targetLatRad)
                y = cos(egenLatRad) * sin(targetLatRad) - (sin(egenLatRad) * cos(targetLatRad) * cos(diffLong))
                compassBearingToTarget = (degrees(atan2(x, y)) + 360) % 360
                riktning = int((compassBearingToTarget + 15) / 30)
                if riktning == 0:
                    riktning = 12
                kurs = int((heading + 15) / 30)
                if kurs == 0:
                    kurs = 12
                speed = speed / 10
                targetX = int(5 * (avst * sin(atan2(x, y))))
                targetY = int(5 * (avst * cos(atan2(x, y))))
                kursX = int(12 * sin(radians(heading)))
                kursY = int(12 * cos(radians(heading)))
                kursVektorX = int((speed + 12) * sin(radians(heading)))
                kursVektorY = int((speed + 12) * cos(radians(heading)))
                avst = int(avst)
            
                # Lägger till det mottagna och beräknade i en intern lista med flygplan
                ettFlygplansData = [avst, riktning, kurs, flight, squawk, kategori, altitude, hexKod,
                                    targetX, targetY, kursX, kursY, kursVektorX, kursVektorY, inTheDark]
                internListaMedFlygplan.append(ettFlygplansData)

                # Sorterar den interna listan med flygplan efter avstånd
                internListaMedFlygplan.sort()
                
                # Lägger till den uträknade positionen i listan för gamla positioner
                if avst < 61:
                    ListaMedGamlaPositionerX.append(targetX)
                    ListaMedGamlaPositionerY.append(targetY)
         
        # För att efter hand ta bort gamla positioner då inga flygplan finns
        if antalMottagnaFlygplan == 0:
            ListaMedGamlaPositionerX.append(0)
            ListaMedGamlaPositionerY.append(0)
    
    ######################################
    # Saker som skall utföras varje gång #
    ######################################
    
    # Ritar ut bakgrundskartan. Kommentera bort för att köra utan kartbakgrund
    screen.blit(karta, (0, 0))
    
    # Ritar ut svepet
    ppiSvepX = -250 * sin(angle) + ppiMittX
    ppiSvepY = -250 * cos(angle) + ppiMittY
    pygame.draw.line(screen, DARKDARKGREEN, [ppiMittX, ppiMittY], [ppiSvepX, ppiSvepY], 6)

    # Ritar ut avståndsringarna med 10 km emellan
    pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 50, ppiMittY - 50, 100, 100], 2)
    pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 100, ppiMittY - 100, 200, 200], 2)
    pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 150, ppiMittY - 150, 300, 300], 2)
    pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 200, ppiMittY - 200, 400, 400], 2)
    pygame.draw.ellipse(screen, DARKGREEN, [ppiMittX - 250, ppiMittY - 250, 500, 500], 2)
        
    # Ritar ut listan med gamla positioner
    for j in range(len(ListaMedGamlaPositionerX)):
        ppiHistX = ListaMedGamlaPositionerX[j]
        ppiHistY = ListaMedGamlaPositionerY[j]
        pygame.draw.ellipse(screen, MEDIUMGREEN, [ppiMittX + ppiHistX - 2, ppiMittY - ppiHistY - 2, 4, 4], 0)
        
    # Raderar de äldsta av de gamla positionerna
    while len(ListaMedGamlaPositionerX) > (antalMottagnaFlygplan * 30):
        ListaMedGamlaPositionerX.pop(0)
        ListaMedGamlaPositionerY.pop(0)

    # Ritar ut linjen mellan ppi:et och textdelen
    pygame.draw.line(screen, DARKGREEN, [600, 0], [600, 600], 2)

    # Mitten av ppi:et
    pygame.draw.ellipse(screen, BLACK, [ppiMittX - 10, ppiMittY - 10, 20, 20], 0)

    # Ställer in hastighet på svepet
    # angle = angle - 0.01047  # 10s per varv
    # angle = angle - 0.0209  # 5s per varv
    # angle = angle - 0.02618  # 4s per varv
    angle = angle - 0.05235  # 2s per varv
    # angle = angle - 0.0698 # 1,5 s per varv
    # angle = angle - 0.1047  # 1s per varv
    
    # Återställer vinkeln på svepet då det roterat ett varv
    if angle < 0:
        angle = 2 * PI

    # Skriver ut aktuell tid på skärmen
    klockan = time.strftime("%H:%M:%S", time.localtime())
    textTime = mediumfont.render(str(klockan), 1, MEDIUMGREEN)
    screen.blit(textTime, (15, 15))
    
    # Skriver ut egen position på skärmen
    textEgenLat = mediumfont.render(str(egenLat), 1, MEDIUMGREEN)
    textEgenLong = mediumfont.render(str(egenLong), 1, MEDIUMGREEN)
    screen.blit(textEgenLat, (15, screensize[1] - 60))
    screen.blit(textEgenLong, (15, screensize[1] - 35))

    # Skriver ut rubriker till flygplansinformationen
    textRubriker = smallfont.render("Flight         Hex     Typ   Squawk   Ri  Kurs  Avst    Höjd", 1, MEDIUMGREEN)
    screen.blit(textRubriker, (615, 15))
    
    # Skriver ut antalet flygplan som mottaget meddelande innehåller på skärmen
    # Obs oftast fler än antalet flygplan med kompletta meddelanden som finns i den interna listan
    textantal = mediumfont.render(str(antalMottagnaFlygplan), 1, MEDIUMGREEN)
    screen.blit(textantal, (560, 15))
    
    # Skriver ut den interna listan med flygplan på skärmen
    for k in range(len(internListaMedFlygplan)):
        textAvst = mediumfont.render(str(internListaMedFlygplan[k][0]), 1, MEDIUMGREEN)
        textRiktning = mediumfont.render(str(internListaMedFlygplan[k][1]), 1, MEDIUMGREEN)
        textKurs = mediumfont.render(str(internListaMedFlygplan[k][2]), 1, MEDIUMGREEN)
        textFlight = mediumfont.render(str(internListaMedFlygplan[k][3]), 1, MEDIUMGREEN)
        textSquawk = mediumfont.render(str(internListaMedFlygplan[k][4]), 1, MEDIUMGREEN)
        textKategori = mediumfont.render(str(internListaMedFlygplan[k][5]), 1, MEDIUMGREEN)
        textAltitude = mediumfont.render(str(internListaMedFlygplan[k][6]), 1, MEDIUMGREEN)
        textHexKod = mediumfont.render((str(internListaMedFlygplan[k][7])).upper(), 1, MEDIUMGREEN)     
        
        textrad = (k * 30) + 35
        if textrad < 550:
            screen.blit(textFlight, (615, textrad))
            screen.blit(textHexKod, (730, textrad))
            screen.blit(textKategori, (825, textrad))
            screen.blit(textSquawk, (880, textrad))
            if (internListaMedFlygplan[k][1]) < 10:
                screen.blit(textRiktning, (965, textrad))
            else:
                screen.blit(textRiktning, (955, textrad))
            if (internListaMedFlygplan[k][2]) < 10:
                screen.blit(textKurs, (1010, textrad))
            else:
                screen.blit(textKurs, (1000, textrad))
            if (internListaMedFlygplan[k][0]) < 10:
                screen.blit(textAvst, (1065, textrad))
            else:
                screen.blit(textAvst, (1055, textrad))
            if (internListaMedFlygplan[k][6]) < 10000:
                screen.blit(textAltitude, (1120, textrad))
            else:
                screen.blit(textAltitude, (1110, textrad))
        
        # Hämtar avståndet ur listan med flygplan
        ppiAvst = internListaMedFlygplan[k][0]
                
        # Sorterar ut mål som är närmare än 61 km för att eventuellt rita ut dessa
        if ppiAvst < 61:
            ppiHexKod = internListaMedFlygplan[k][7]
            ppiTargetX = internListaMedFlygplan[k][8]
            ppiTargetY = internListaMedFlygplan[k][9]
            ppiKursX = internListaMedFlygplan[k][10]
            ppiKursY = internListaMedFlygplan[k][11]
            ppiKursVektorX = internListaMedFlygplan[k][12]
            ppiKursVektorY = internListaMedFlygplan[k][13]
            ppiInTheDark = internListaMedFlygplan[k][14]
            
            # Ritar ut plottsymbol om positionsmeddelande mottagits de senaste 10 sekunderna
            if ppiInTheDark < 11:
                pygame.draw.line(screen, GREEN, [ppiMittX + ppiTargetX, ppiMittY - ppiTargetY - 4],
                                 [ppiMittX + ppiTargetX, ppiMittY - ppiTargetY + 4], 2)
                pygame.draw.line(screen, GREEN, [ppiMittX + ppiTargetX + 4, ppiMittY - ppiTargetY],
                                 [ppiMittX + ppiTargetX - 4, ppiMittY - ppiTargetY], 2)

            # Ritar ut målföljet. Blinkar om det är äldre än 20 sekunder
            if ppiInTheDark < 20 or updateCounter < 30:
                
                # Kollar om målet skall märkas som fientligt
                if (ppiHexKod == '4a9d02'  # SE-GHB TGT52
                    or ppiHexKod == '4a9d06'  # SE-GHF TGT56
                    or ppiHexKod == '4aa5f6'  # SE-IOV TGT57
                    or ppiHexKod == '4aa5fa'  # SE-IOZ TGT58
                    or ppiHexKod == '4aa6a1'  # SE-IUA TGT59
                    or ppiHexKod == '4a910f'  # SE-DHO TGT01
                    or ppiHexKod == '4a9110'  # SE-DHP TGT02
                    or ppiHexKod == '4ac861'  # SE-RCA TGT03
                    or ppiHexKod == '39c422'):
                    pygame.draw.polygon(screen, RED, [[ppiMittX + ppiTargetX, ppiMittY - ppiTargetY - 10],
                                                      [ppiMittX + ppiTargetX - 10, ppiMittY - ppiTargetY + 10],
                                                      [ppiMittX + ppiTargetX + 10, ppiMittY - ppiTargetY + 10]], 3)
                    pygame.draw.line(screen, RED, [ppiMittX + ppiTargetX + ppiKursX, ppiMittY - ppiTargetY - ppiKursY],
                                     [ppiMittX + ppiTargetX + ppiKursVektorX, ppiMittY - ppiTargetY - ppiKursVektorY], 3)

                # Annars ritas målet ut som okänt
                else:
                    pygame.draw.rect(screen, GREEN, [ppiMittX + ppiTargetX - 10, ppiMittY - ppiTargetY - 10, 21, 21], 3)
                    pygame.draw.line(screen, GREEN, [ppiMittX + ppiTargetX + ppiKursX, ppiMittY - ppiTargetY - ppiKursY],
                                     [ppiMittX + ppiTargetX + ppiKursVektorX, ppiMittY - ppiTargetY - ppiKursVektorY], 3)

    # Uppdaterar skärmen
    pygame.display.flip()
    my_clock.tick(60)
    updateCounter = updateCounter + 1
    pygame.draw.rect(screen, BLACK, [0, 0, screensize[0], screensize[1]], 0)

# Avslutar programmet
pygame.quit()
sys.exit()
