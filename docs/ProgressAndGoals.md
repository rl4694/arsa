# Progress
The following features were implemented in Fall 2025.
- Backend API Server (20 endpoints total)
    - 4 resources: cities, states, nations, natural disasters
    - 5 operations per resource: CRUD, select
    - Cities, states, and nations are connected to each other
    - Cache using _id as key
    - Date validation, type checking, and duplicate handling
- ETL Scripts
    - Load nation, earthquake, landslide, and tsunami data from CSV files to MongoDB
    - Map disaster coordinates to cities using Nominatim API
    - Cache created disasters and geographic entities into JSON files
- CI Pipeline
    - Automated unit tests for data controllers and reusable ETL function
    - Deployment to PythonAnywhere
    - Environment variables stored in GitHub (CI), .env files (local), and WSGI config (PythonAnywhere)

# Goals
We will try to implement the following features in Spring 2026:
- Frontend Client
    - Map with natural disasters overlaid on top
    - Natural disaster details shown when clicking a disaster on the map
    - List view for each resource
    - Create, update, and delete forms for each resource
    - Login and register pages
    - Navbar with links and logout button
- Backend API Server
    - Connect natural disasters to cities
    - Add authentication system
- If we have time
    - Special effects on the map based on natural disaster intensity/frequency (ex. big scary circles)