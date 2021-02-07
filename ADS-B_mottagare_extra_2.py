#! /usr/bin/python3
# coding=utf-8

###################################
# Extra kod till hemstudieuppgift #
###################################

# Importerar bibliotek
import json
import requests
import time


#######################################
# För läsning av orienteringar på mål #
#######################################

# För att installera espeak kör följande i ett kommandofönster: pip3 install python-espeak
from espeak import espeak

# Definierar vilken röst som skall användas.
# Testa att byta till annan tex m1 eller f2
espeak.set_voice("sv+m3")

# Definierar variabler och listor
done = False
lastlist = ["0"]
newlist = ["0"]
internListaMedFlygplan = []

#############
# Huvudloop #
#############
while not done:
    # För att den bara ska läsa "nytt mål" då orientering om just det specifika målet läses för första gången 
    lastlist = newlist
    newlist = ["0"]
    
    internListaMedFlygplan = []
    # Lägger till ett exempelmeddelande
    # ettFlygplansData = [avst, riktning, kurs, flight, squawk, kategori, altitude, hexKod,
    #                                targetX, targetY, kursX, kursY, kursVektorX, kursVektorY, inTheDark]
    ettFlygplansData = [10, 12, 6, 'TGT52', 2000, 'A0', 3000, '4a9d02',
                    50, 0, 1, 0, 2, 0, 1]
    internListaMedFlygplan.append(ettFlygplansData)
    ettFlygplansData = [20, 3, 9, 'TGT56', 2000, 'A0', 3000, '4a9d06',
                    0, 100, 0, -1, 0, -2, 1]
    internListaMedFlygplan.append(ettFlygplansData)

    # Sorterar den interna listan med flygplan efter avstånd
    internListaMedFlygplan.sort()
    # print(internListaMedFlygplan)
    
    try:
        if len(internListaMedFlygplan) > 0:
            for j in range(len(internListaMedFlygplan)):
                speekRiktning = internListaMedFlygplan[j][1]
                speekKurs = internListaMedFlygplan[j][2]
                speekAvst = internListaMedFlygplan[j][0]
                speekHexKod = internListaMedFlygplan[j][7]
                print("Riktning:{} Kurs:{} Avstånd:{} km" .format(speekRiktning, speekKurs, speekAvst))
                
                if speekAvst < 50:
                    newlist.append(speekHexKod)
                    if lastlist.count(speekHexKod) == 0:
                        espeak.synth("nytt")
                        while espeak.is_playing():
                            time.sleep(0.1)
                    espeak.synth("måål riktning")
                    while espeak.is_playing():
                        time.sleep(0.1)
                    espeak.synth(str(speekRiktning))
                    while espeak.is_playing():
                        time.sleep(0.1)
                    espeak.synth("kurs")
                    while espeak.is_playing():
                        time.sleep(0.1)
                    espeak.synth(str(speekKurs))
                    while espeak.is_playing():
                        time.sleep(0.1)
                    espeak.synth("avstånd")
                    while espeak.is_playing():
                        time.sleep(0.1)
                    espeak.synth(str(speekAvst))
                    while espeak.is_playing():
                        time.sleep(0.1)
                    espeak.synth("kilometer")
                    while espeak.is_playing():
                        time.sleep(0.1)
                    time.sleep(2)
    except:
        print("Error in speek")
        
    time.sleep(30)
