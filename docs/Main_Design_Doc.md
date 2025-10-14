##Design:

We are hoping on creating an API for a geographical database of natural disasters, the database will primarily be based on objects like cities, states and countries objects.

##Database Design (Not finalized)

┌─────────────┐
│   NATION    │
├─────────────┤
│ id: "1"     │
│ name: "USA" │
└─────────────┘

┌───────────────┐
│    STATE      │
├───────────────┤
│ id: "2"       │
│ name: "CA"    │
│ nation: "1"   │
└───────────────┘

┌────────────────────┐
│       CITY         │
├────────────────────┤
│ id: "3"            │
│ name: "LA"         │
│ state: "2"         │
│ nation: "1"        │
└────────────────────┘

┌────────────────────┐
│     DISASTER       │
├────────────────────┤
│ id: "4"            │
│ coordinates: ""    │
│ type: ""           │
│ deaths: 0          │
│ damage: 0          │ #economic damage, (we can then use some metric combining this to calculate intensity for the map feature)
│ city: "3"          │
│ state: "2"         │
│ nation: "1"        │
└────────────────────┘

:arrow_up: This doesn't display correctly so look at this in edit mode

Currently the database is stored locally in the python code for the endpoint, they will be migrated to an external file to pre populate the database with cities and states and countries, there are several good APIs for populating the DB with this data, we will most likely only pre populate the countries of the world as those are limited in scope, and the rest will be added on demand as new disasters are added.

* On second thought it could be better to make the objects connected for easy query of a object's childs, so for checking a country's cities it can recursively search the list of states inside the country, and for each state it will query the list of countries. (However this might over complicate things)

When adding an object, it should query the database for its parent objects's names, and if it doesnt exist it will create them (The creation process should return the ID so the child can add the parent's id inside itself. (This might be more complicated for states and cities since they will have to check multiple parameters as there are many cities with the same name.

For adding disasters, we will most likely pull this from live sources, and the main parameter we will take in will be it's coordinates, we can then use this to locate the nearest city, and use a city API (below) to locate the nearest city and it's state and nation, and then we can use this to initiate the add to city procedures

APIs for cities:
https://opencagedata.com/api (needs membership?)
https://www.geonames.org/export/web-services.html
https://locationiq.com/docs

APIs for disasters: (Draft)
Earthquake: https://earthquake.usgs.gov/fdsnws/event/1/
Hurricane: https://www.nhc.noaa.gov/gis/
Wildfire: https://firms.modaps.eosdis.nasa.gov/api/
Volcano: https://volcano.si.edu/
Flood: https://gpm.nasa.gov/data/directory
Tsunami: https://www.ngdc.noaa.gov/hazard/tsu_db.shtml

##Endpoints:

- /hello (GET)
- /endpoints (GET)
- /cities (GET,POST)
- /cities/<city_id> (GET,PUT,DELETE)
- ...

[Planning]

- A bit more complex, but a maps page that maps out the disasters and maybe increase the dot size by amount/severity would be nice

##Current Objectives:

[x] Decide on a geographical topic to focus on, then brainstorm general concept and additional requirements on top of the assignment objectives

[ ] Once the features have been planned out, assign tasks to each member on the parts they are responsible for, make sure we can deliver a continuously working product as we iterate on gradually adding features.

##Milestones:

[x] 10/14 Github Actions Working

[ ] 10/30 Incorporate the use of fixtures (reusable predefinied setup code for tests)

[ ] 10/30 Incorporate the use of raises (gracefully fail on bad inputs)

[ ] 10/30 Incorporate the use of skips (conditionally skip tests)

[ ] 10/30 Incorporate the use of patch (mock/replace functions for testing)

[ ] 11/13 Make sure the code is able to run with a local MongoDB server

[ ] 11/26 Make sure the code is able to run with a cloud based MongoDB server

[ ] 12/04 Deploy the API server on the cloud

(More milestones as features are agreed upon and fleshed out)

