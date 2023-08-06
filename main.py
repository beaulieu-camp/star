import requests
import datetime
import json

url = "https://data.explore.star.fr/api/records/1.0/search/"
url += "?dataset=tco-bus-circulation-passages-tr"
url += "&geofilter.polygon=(48.1115718311405,-1.647477149963379),(48.11274662400898,-1.634538173675537),(48.12247345006807,-1.6274142265319822),(48.12851776605501,-1.6274571418762207),(48.119221829479585,-1.650395393371582),(48.1115718311405,-1.647477149963379)"

req = requests.get(url)
if req.status_code != 200 : raise Exception("Api Star Pété") 

data = req.json()

obj_ret = {}

for item in data["records"] : 
    id_ar = item["fields"]["idarret"]

    if id_ar not in obj_ret :
        obj_ret[id_ar] = {"nom":item["fields"]["nomarret"],"dessertes":[]}

    obj_ret[id_ar]["dessertes"].append( [
        item["fields"]["coordonnees"],
        item["fields"]["nomcourtligne"],
        item["fields"]["depart"],
        item["fields"]["destination"],


        # item.fields.sens,
        # item.fields.idligne,
    ])

with open("./out/index.json","w+") as file:
    file.write(json.dumps(obj_ret))
