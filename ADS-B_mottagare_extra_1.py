#! /usr/bin/python3
# coding=utf-8

###################################
# Extra kod till hemstudieuppgift #
###################################

# Importerar bibliotek
import json
import requests
import time


################################
# För att hämta data från FR24 #
################################

# Att hämta data från FR24 kan ta lite längre tid än att hämta från SDR-mottagaren
# För att inte svepet på ppi:et skall hacka kan man då lägga hämtningen i en separat tråd (thread)
import threading

# Definierar variabler och listor
done = False
FR24_mottagenListaMedFlygplan = []

# Skapar separat tråd som hämtar data från FR24
class GetData(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)        
        self.running = True
        
    def run(self):
        global FR24_mottagenListaMedFlygplan
        # OBS att du kan justera området som du hämtar flygplan ifrån i raden nedan (bounds är alltså lat/long)
        FR24_API = "https://data-live.flightradar24.com/zones/fcgi/feed.js?bounds=58.00,55.00,11.00,14.00"
        while self.running:
            time.sleep(1)
            FR24_mottagenListaMedFlygplan = []
            try:
                FR24_mottagetMeddelande = requests.get(url=FR24_API, headers={'User-Agent': 'Mozilla/5.0'}, timeout = 1)
                #print(FR24_mottagetMeddelande.content)
                FR24_mottagenListaMedFlygplan = json.loads(FR24_mottagetMeddelande.content)
                #print(FR24_mottagenListaMedFlygplan)
                FR24_listParts = len(FR24_mottagenListaMedFlygplan) - 2
                if FR24_listParts > 0:
                    del FR24_mottagenListaMedFlygplan["full_count"]
                    del FR24_mottagenListaMedFlygplan["version"]
            except:
                print("Error getting data from FR24")

getData = GetData()
getData.daemon = True
getData.start()

#############
# Huvudloop #
#############
while not done:   
    try:
        for i in FR24_mottagenListaMedFlygplan:
            FR24_ettFlygplan = FR24_mottagenListaMedFlygplan[i]
            #print (FR24_ettFlygplan)
            
            # OBS att vi får mer information från FR24 än från ADS-B mottagaren
            # Detta är tex till och från vilka destinationer som flygningen sker
            # Samtidigt saknas tex ADS-B kategori i datan
            FR24_hexKod = FR24_ettFlygplan[0]
            FR24_targetLat = FR24_ettFlygplan[1]
            FR24_targetLong = FR24_ettFlygplan[2]
            FR24_heading = FR24_ettFlygplan[3]
            FR24_altitude = FR24_ettFlygplan[4]
            FR24_speed = FR24_ettFlygplan[5]
            FR24_squawk = FR24_ettFlygplan[6]
            FR24_type = str(FR24_ettFlygplan[8])
            FR24_id = str(FR24_ettFlygplan[9])
            FR24_timestamp = FR24_ettFlygplan[10]
            FR24_fromAirport = str(FR24_ettFlygplan[11])
            FR24_toAirport = str(FR24_ettFlygplan[12])
            FR24_flight = str(FR24_ettFlygplan[16])
            print(FR24_hexKod,FR24_targetLat,FR24_targetLong,FR24_heading,FR24_altitude,FR24_speed,
                  FR24_squawk,FR24_type,FR24_id,FR24_timestamp,FR24_fromAirport,FR24_toAirport,FR24_flight)
    except:
        print("Error decoding message")
    
    time.sleep(1)
