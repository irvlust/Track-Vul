# Track-Vul

Python application vulnerability tracking API exercise

Please refer to the email where this Exercise is outlined for the general requirements

## Notes

This project implements the following -

- **Implements a REST based API using FastAPI and python**
- **Uses the Open Source Vulnerability (OSV) API to fetch vulnerability data**
- **Application and dependency data are stored in a postgres database running locally in docker container**
- **Calls to the OSV API are cached locally**
- **Tests are implemented using pytest (happy path for now)**
- **Very simple exception handling is implemented**
- **Logging included**
- **Swagger available out of the box so that the user can view and manually try out requests directly from the browser**

Info on how to run the applcation or tests (Run Application or Run Tests) are outlined in later sections below.

## Assumptions, Reasoning, Decisions, & Potential Improvements

### Database Structure

Since the OSV API accepts specific revision data (version specs) with the dependency name and the response results with the same dependency and different revisions can be different, it was decided to create records in the Dependency table that include separate columns for the dependency name and version spec (see the app/models.py directory). Caching of the results of the OSV endpoint therefore uses the name and version.

Note that I've used the requirements-parser python library to parse the requirements.txt file and this includes picking up the extras (ex: sqlalchemy[asyncio]). They're not used by the OSV API, however for potential future use, the extras have been included in the Dependency model.

Note that the schema could've been broken down further beyond just the single Dependency table. For example, the version spec could've been put into a separate table and foreign keys to the Application and Dependency tables could have been used (or some similar type of breakdown). This could potentially cut down on the Dependency table size, however, it was decided to just use a single table.

Note - since it's a small project, I did not include implementing migrations. When I required changing the models.py, I just reset the database. The project could benefit from use of a migration tool like Alembic for example.

### Error Exception Handling & Logging

Exception handling has been implemented very simplisticly. For example, even though the functions in app/api/utils.py, (\_get_vulnerabilities_uncached) can raise different RuntimeError types, it was decided at the route level (in app/apiroutes_applications.py) to just return a 500.

Specific handlers may be implemented to improve this, for example something like this -

```bash
except RuntimeError as e:
    if "Invalid JSON" in str(e):
        raise HTTPException(status_code=502, detail="Upstream vulnerability service returned bad JSON")
    elif "Network error" in str(e):
        raise HTTPException(status_code=503, detail="Vulnerability API unavailable")
    elif "HTTP error" in str(e):
        raise HTTPException(status_code=502, detail="Vulnerability API responded with error")
    else:
        raise HTTPException(status_code=500, detail="Unexpected vulnerability error")
```

That, of course would imply more logic to maintain. Custom handlers could've also been used as well or handlers could've been used that are harmonized in the approach that Morgan Stanley uses (no info on that in the requirements).

So again, it was decided at the route level (in app/apiroutes_applications.py), to just return a 500.

In addition to that, I decided to use a granular (many try-excepts) versus a coarse style (extreme would be one giant try-except). Yes, this is a bit boilerplate and results in longer and possibly more repetitive code, however, this results in easier debugging, and a more precise error context. This would expecially be the case if I had used custom handlers. This also allows including logging messages more frequently which also aids with debugging.

### OSV Endpoint Issues

I've decided to implement the "/dependency/{name}" endpoint route (where name is the dependency name) to return a list of vulnerabilities, where each element is associated with a specific version spec of the dependency. Using the version spec was explained in the above `Database Structure` section.

I have setup the vulnerability functions (app/api/utils.py) that deal with accessing the OSV API endpoint do not deal with all potential issues that might arise with the OSV API. Specifically, the OSV documention mentions a potential next_page_token that implements paging. The documentation also explains that the OSV API result may return a response that consists only of the next_page_token that is used as a flag indicating that the data was not available in the available time limit. I wasn't successful in trying to force this token to appear, but I didn't spend too much time on it.

I've decided not to implement the next_page_token flag. However, this is an enhancement that can be added in the future. I've added a comment in the \_get_vulnerability_uncached function where this can be added. A function could be called that concatenates further results from extended pages or does a retry if needed.

This of course could mean that the elements of the return list of vulnerabilities could be either cut short, or only contain a next_page_token tag.

Note that in the returned list of vulnerabilities, each element consists of the whole OSV API response.

### Testing

I've added a set of simple tests in the unit_tests and e2e_tests directories in the project's test directory. They are self-explanatory. Note that even though the e2e test are not really end-to-end tests, I've called them e2e as they access the OSV API endpoints.

See the Run Tests section below for how to run them separately.

I've kept the tests very simple (mostly happy path tests). The project can benefit from more tests. They could also benefit from using classes from the app/schemas.py file.

### Swagger Documentation and Scripts

Since the endpoints are generally easy to understand, I've decided not to add an documentation to the routes for swagger. Note, there is a requirements.txt file in the req_examples directory that includes interesting version specs that played with (see following).

```bash
# req_examples/requirements.txt
fastapi==0.103.0
uvicorn>=0.23.0,<0.24.0
requirements-parser==1.7.3
sqlalchemy[asyncio]
```

This file can be used as a test file to be uploaded in the /application enpoint in swagger.

This project could also benefit from some bash scripts that would initialize all the setup sections automatically. I've decided not to include those.

## Setup

This application uses a posgresql database running in a docker container. Do the following in a terminal to set that up -

```bash
docker run --name track-vul-db \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin \
  -e POSTGRES_DB=track-vul \
  -p 5434:5432 \
  -v track-vul-data:/var/lib/postgresql/data \
  -d postgres
```

Note - it is left up to the user to check whether the docker container is up and running.

Once the container is running clone the repository to your local machine.

```bash
git clone blah
```

Go to the application directory -

```bash
cd Track-Vul
```

Note - this project was built using python 3.13.0. It is suggested to use a virtual environment with python 3.13.0. It is left up to the user to set this up and start the virtual environment.

Once the virtual environment is setup and activated, install the dependencies -

```bash
pip install -r requirements.txt
```

At this point, you can either run the applicaton, or run the tests. An explanation of how to setup and run the tests are provided in the Run Tests section.

## Run Application

Run the following command to set up the database tables (this resets and recreates the database tables)-

```bash
python -m app.init_db
```

Run the application -

```bash
python run.py
```

To use Swagger to test the endpoints, open the following url in a browser -

```bash
http://127.0.0.1:8000/docs#
```

## Run Tests

Note that the tests are set up to use a database in the postgres container in parallel to the application database. Therefore, application data will not be nuked by running these tests (yes - quick and dirty).

Run the following steps to create a test database -

```bash
docker exec -it track-vul-db psql -U admin -d postgres
```

At the `postgres=#` prompt, run the following -

```bash
CREATE DATABASE "track-vul-test";
```

Exit by using the `\q` command.

Now run pytest -

```bash
# Only run unit tests
pytest -m unit

# Only run E2E tests (accesses external OSV api)
pytest -m e2e

# Run all tests
pytest
```

Note that running the e2e tests will hit the OSV endpoint and so may slow the tests down somewhat.

## Memory Help

sudo docker exec -it track-vul-db psql -U admin track-vul
