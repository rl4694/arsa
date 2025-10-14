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
│ id: "1"       │
│ name: "CA"    │
│ nation: "USA" │
└───────────────┘

┌────────────────────┐
│       CITY         │
├────────────────────┤
│ id: "1"            │
│ name: "LA"         │
│ state: "CA"        │
│ nation: "USA"      │
└────────────────────┘

┌────────────────────┐
│     DISASTER       │
├────────────────────┤
│ id: "1"            │
│ deaths: 0          │
│ damage: 0          │ #economic damage, (we can then use some metric combining this to calculate intensity for the map feature)
│ city: "LA"         │
│ state: "CA"        │
│ nation: "USA"      │
└────────────────────┘

Currently the database is stored locally in the python code for the endpoint, they will be migrated to an external file to pre populate the database with cities and states and countries, there are several good APIs for populating the DB with this data.

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

