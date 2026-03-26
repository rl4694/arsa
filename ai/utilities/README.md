## backfill and deduplication system

these two scripts are designed for backward compatibility of our database in an effort to deduplicate natural disasters
the current issue is that multiple reports can be generated from the same real world natural disaster if they:
- have a large radius of effect
- span over several days
the scripts leverage new fields: severity, show, parent events, reports, as well as the new haverine great circle geography and time proximity search fields
to update old objects in the database with the new fields, first run the backfill.py to apply the new fields to the existing objects
this will enable the fields for the dedupe.py script
configure the radius to dedupe (in km) as well as the time proximity fields, the script will consolidate all natural disasters within the same radius of another disaster
with the same disaster time, and also within the same time proximity
the script will then group the object to the other object, setting the show field to false for the sub report object, and setting the parent event field to the other object
(to implement: check if the object you are grouping to has a parent object and use that instead)