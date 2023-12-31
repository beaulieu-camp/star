import requests
from datetime import datetime,timedelta
import json
from io import BytesIO
from zipfile import ZipFile
import math
import pytz

def to_timezone(date):
    return pytz.timezone('Europe/Paris').localize(date, is_dst=None)

def req_func(url):
    req = requests.get(url)
    if req.status_code != 200 : raise Exception("Api Pété") 
    return req

def days_from_intervalle(start, end):
    temp = start
    liste = []
    while temp < end:
        liste.append(temp)
        temp += timedelta(days=1)
    return liste

urlhoraires = "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-busmetro-horaires-gtfs-versions-td&q=" 
urlarrets = "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-bus-topologie-pointsarret-td&q=&rows=2000&sort=nom"
urllignes = "https://data.explore.star.fr/api/records/1.0/search/?dataset=tco-bus-topologie-lignes-td&q=&rows=200&sort=id"

# filtrage arrets
arrets = req_func(urlarrets).json()["records"]
arrets_filt = {}
for arret in arrets :
    id = arret["fields"]["code"]
    nom = arret["fields"]["nom"]
    arrets_filt[id] = nom

with open("./out/index.json","w+") as file:
    liste = []
    for item in arrets_filt.values():
        if item not in liste:
            liste.append(item)
    file.write(json.dumps(liste))

# a partir de la c'est le dawa
urlzip = req_func(urlhoraires).json()["records"][0]["fields"]["url"]
zip = req_func(urlzip).content
myzip = ZipFile(BytesIO(zip))

# filtrage ligne
lignes = {}
for line in myzip.open("routes.txt").readlines()[1:]:
    l = line.decode('utf-8').replace('"',"").replace('\n',"").split(",")
    nom = l[2]
    id = l[0]
    lignes[id] = nom

# filtrage des jours
calendar = {}
for line in myzip.open("calendar.txt").readlines()[1:]:
    l = line.decode('utf-8').replace('"',"").replace('\n',"").split(",")
    jour = int( 6 - math.log2( int( "".join(l[1:8]) , 2 )))

    start = to_timezone( datetime.strptime(l[8],'%Y%m%d') )
    end =   to_timezone( datetime.strptime(l[9],'%Y%m%d') )
    dates = days_from_intervalle( start, end )
    id = l[0]
    calendar[id] = {
        "jour":jour,
        "dates":dates
    }

# filtrage intermédiaire
trips = {}
for line in myzip.open("trips.txt").readlines()[1:]:
    l = line.decode('utf-8').replace('"',"").replace('\n',"").split(",")
    id = l[2]
    trips[id] = {
        "dates":calendar[l[1]]["dates"],
        "jour":calendar[l[1]]["jour"],
        "direction" : l[3],
        "ligneid" : l[0],
        "sens" : l[5],
        "ligne" : lignes[l[0]],
    }


    
out_liste = {}
# filtrage de tout
for line in myzip.open("stop_times.txt").readlines()[1:]:
    l = line.decode('utf-8').replace('"',"").replace('\n',"").split(",")
    arretid = l[3]
    if arretid in arrets_filt.keys() :
        arret = arrets_filt[arretid]
        trip = trips[l[0]]
        ligne = trip["ligne"]
        ligneid = trip["ligneid"]
        sens = trip["sens"]
        direction = trip["direction"]
        dates = trip["dates"]
        jour = trip["jour"]

        time = l[1].split(":")
        hour = int(time[0])
        minute = int(time[1])

        if arret not in out_liste:
            out_liste[arret] = {"nom":arret,"dessertes":{}}

        if ligneid not in out_liste[arret]["dessertes"]:
            out_liste[arret]["dessertes"][ligneid] = {"nom":ligne,"sens":{}}

        if sens not in out_liste[arret]["dessertes"][ligneid]["sens"]:
            out_liste[arret]["dessertes"][ligneid]["sens"][sens] = {"direction":direction,"horaires":[]}
        
        for date in dates:
            date += timedelta(hours=hour,minutes=minute)
            timestamp = int(date.timestamp())
            weakday = date.weekday()
            if weakday == jour and to_timezone(datetime.now()) < date:
                
                out_liste[arret]["dessertes"][ligneid]["sens"][sens]["horaires"].append(timestamp)
                out_liste[arret]["dessertes"][ligneid]["sens"][sens]["horaires"].sort()

for key in out_liste.keys():
    with open("./out/"+key+".json","w+") as file:
        file.write(json.dumps(out_liste[key]))
