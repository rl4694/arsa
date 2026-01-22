# arsa
An API server for geographical data of natural disasters :volcano:.

To build production, type `make prod`.

To create the env for a new developer, run `make dev_env`.

## Configuration
- To run this project, you must set the following environment variables (or create a .env file locally)
- CLOUD_MONGO: Set to "1" to use Atlas, or "0" for local
- MONGO_URL: mongodb+srv://sjp9:[key]@arsa.afndfz7.mongodb.net/?appName=arsa

# Spring 2026
You can find the objectives for Spring 2026 [here](./docs/ProgressAndGoals.md).

# Fall 2025
## Objectives
- create an API server for a geographic database.

- implement CRUD operations on a related set of data stored in a database. (countries, states, and cities)

- deploy the project to the cloud using CI/CD.

- include a dozen or more endpoints.

- ensure all endpoints and functions have unit tests.

- thoroughly documented each endpoint for [Swagger](https://swagger.io/).

## Ideas
The following is a list of ideas involving geographic data we could implement:
- Natural Disasters ([earthquakes](https://www.kaggle.com/datasets/warcoder/earthquake-dataset), [tsunamis](https://www.kaggle.com/datasets/andrewmvd/tsunami-dataset))
- Airplane crashes ([dataset](https://www.kaggle.com/datasets/saurograndi/airplane-crashes-since-1908))
- Corporate Headquarters ([dataset](https://www.kaggle.com/datasets/mannmann2/fortune-500-corporate-headquarters))

- Urban Heat Islands ([dataset](https://www.kaggle.com/datasets/bappekim/urban-heat-island-intensity-dataset))
- Global Air Quality Index ([dataset](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india))
- Urban Flood Risk ([dataset](https://www.kaggle.com/datasets/pratyushpuri/urban-flood-risk-data-global-city-analysis-2025))
- US Wildfires ([dataset](https://www.kaggle.com/datasets/firecastrl/us-wildfire-dataset/data))
- Global Bike Sales ([dataset](https://www.kaggle.com/datasets/hamedahmadinia/global-bike-sales-dataset-2013-2023))
- Global Population Stats For 2024 ([dataset](https://www.kaggle.com/datasets/raveennimbiwal/global-population-stats-2024))
