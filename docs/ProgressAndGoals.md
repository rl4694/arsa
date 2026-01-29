# Progress
The following were requirements for Fall 2025.
- create an API server for a geographic database.

- implement CRUD operations on a related set of data stored in a database. (countries, states, and cities)

- deploy the project to the cloud using CI/CD.

- include a dozen or more endpoints.

- ensure all endpoints and functions have unit tests.

- thoroughly documented each endpoint for [Swagger](https://swagger.io/).

They were met by implementing the following features.

### API Server
We created an API server which allows users to perform CRUD operations on
cities, states, nations, and natural disasters. Each data controller implements
type-checking, duplicate handling, and caching (using _id as the key). The
natural disasters also include Date validation. Each data controller has
a Flask endpoint that is documented with Swagger. In total, we have
4 resources x 5 operations (CRUD, select) = 20 endpoints.

This fulfills the requirements:
- create an API server for a geographic database.
- implement CRUD operations on a related set of data stored in a database. (countries, states, and cities)
- include a dozen or more endpoints.

### ETL Scripts
We are loading nation, earthquake, landslide, and tsunami data from CSV files
to MongoDB using ETL scripts. We are also mapping natural disaster coordinates
to cities using the Nominatim API. To avoid calling the Nominatim API for
seeding all of our local setups, we are also caching the generated MongoDB
records into JSON files and seeding the JSON files if they exist.

### CI Pipeline
We created a CI/CD pipeline which automates unit testing for our data controllers
and reusable ETL functions, as well as deploying to PythonAnywhere. We are also
storing our environment variables in GitHub (CI), .env files (local), and
WSGI config (PythonAnywhere).

This fulfills the requirements:
- deploy the project to the cloud using CI/CD.
- ensure all endpoints and functions have unit tests.

# Goals
We will try to reach the following goals in Spring 2026.

### Frontend Client
We will create a frontend React client with the following features. It will be done through incremental development on a new repository.
- Map with natural disasters overlaid on top. This can be implemented using [React Leaflet](https://react-leaflet.js.org/).
- Natural disaster details shown when clicking a disaster on the map
- List view for each resource
- Create, update, and delete forms for each resource
- Login and register pages
- Navbar with links and logout button. This can be implemented using React Router.
- Implement React testing
- Create HATEOAS features in the system
- Smart filtering for disaster types
- Ability to view disasters by nations when clicking on the nation

This will give each API endpoint a corresponding frontend interface.

### API Server
We will modify the Backend API Server to implement the following features:
- Add latitude and longitude fields to cities

  This will enable us to mark cities on the frontend map.

- Add a function to map coordinates to cities

  This will connect natural disasters to cities, since they both will have latitude and longitude data. 

- Add authentication system
  
  This will restrict the create, update, and delete forms to only be accessible to registered users instead of any public visitor.

### AI integration

- This is mostly speculative, but it could be nice to hook up an AI API key if a user would like to find more details on a specific disaster and find details and links for it, google AI studio has decent rate limits for free users with a google accounts (~50 per day for Gemini flash 2.5 and more for flash 2.0), this would require creating a template for the AI to follow for easy parsing, we can store these results for later so eventually we'll have more info on each disaster

### Live Data Integration

- Also speculative but having live data feed into the DB would be nice for disasters such as earthquakes and tornados, this could be also done with AI to some extent with google search features when no easy API exist for them, we could have the AI query and evaluate for disasters and id relevancy and severity, and get details about cities such as coordinates
