#!/bin/sh
curl "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv" > data/us.csv
curl "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv" > data/us-states.csv
curl "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv" > data/us-counties.csv
curl "https://services1.arcgis.com/CY1LXxl9zlJeBuRZ/arcgis/rest/services/Florida_Cases_Zips_COVID19/FeatureServer/0/query?where=1%3D1&outFields=ZIP,COUNTYNAME,Cases_1&returnGeometry=false&outSR=4326&f=json" > data/fl-zip-cases-`date +%Y-%m-%d`.json
curl "https://services1.arcgis.com/CY1LXxl9zlJeBuRZ/arcgis/rest/services/Florida_COVID19_Cases/FeatureServer/0/query?where=1%3D1&outFields=COUNTY,COUNTYNAME,CasesAll,Deaths&returnGeometry=false&outSR=4326&f=json" > data/fl-county-totals.json
