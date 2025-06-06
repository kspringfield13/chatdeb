**KYDxBot**

* Python (FastAPI + OpenAI) for the backend
* DuckDB (via dbt) to manage and transform customer data
* dbt for data transformations (seeds, models, builds)
* A React/Next.js (or other Node-based) frontend served via npm

**Overview**

KYDxBot integrates a FastAPI backend, LangChain/OpenAI for querying, DuckDB for data storage via dbt, and a small React frontend.

**Key Components**

* Backend (FastAPI)

  * ```server.py``` exposes API endpoints. ```/register``` and ```/login``` manage credentials, while ```/chat```. ```/clear_history``` is optional. CORS is configured for the local React app

  * Primary business logic in ```chatbot.py```. It decides whether a query is data-related—looking for counts, totals or business metrics such as *sales*, *revenue* or *orders*—and routes those questions to SQL via LangChain. All other queries fall back to semantic search with Pinecone or a direct OpenAI call. It also saves all interactions in ```chatbot_responses.json```

  * ```langchain_sql.py``` builds a ```SQLDatabaseChain``` around DuckDB. ```query_via_sqlagent()``` sends questions to OpenAI to generate SQL and returns rows from DuckDB

  * ```db.py``` handles the DuckDB connection and SQLAlchemy engine instantiation

* Data Ingestion & dbt

  * ```data_ingest/load_data.py``` loads raw CSV files from ```raw_data/``` into staging tables in DuckDB and verifies row counts

  * ```data_ingest/drop_all_data.py``` drops all tables/views in DuckDB for a clean slate

  * ```data_models/``` contains the dbt project with models (e.g., ```marts/customers.sql```, ```marts/products.sql```) that build analytical tables. There is also a macro ```coalesce_and_round.sql``` used in the product model

* Semantic Search with Pinecone

  * ```pinecone_utils.py``` sets up the Pinecone index, offers functions to embed/ingest customers and products, and exposes ```get_embedding()``` plus a simple ```semantic_search()``` helper

* Frontend

  * ```ReactApp/``` contains a small Vite + React UI. ```ChatBox.jsx``` then posts questions to ```/chat```.

* Data & Logs

  * ```raw_data/``` holds sample CSVs for customers, products, etc.

  * ```logs/dbt.log``` shows past dbt invocations.

* Configuration

  * ```README.md``` provides setup instructions: create a Python virtual environment, install ```requirements.txt```, load data via ```data_ingest```, run dbt, configure ```.env``` with API keys, and start the FastAPI server and React app


**Prerequisites**

* macOS
* Homebrew
* Git
* Python 3.11.8
* Node.js & npm
* dbt-core
* duckDB

**Clone Repo**

* Clone via HTTPS

```bash
git clone git@github.com:kspringfield13/kydxbot.git
cd kydxbot
```

**Set Up Python Environment**

* Inside the project root, create and activate a fresh Python 3.11 virtual environment

```bash
# (1) Create a venv in a folder named "chatbot_env" using python version 3.11
python -m venv chatbot_env

# (2) Activate it
source chatbot_env/bin/activate
# You should now see "(chatbot_env)" at the front of your prompt.

# (3) Upgrade pip (optional, but recommended)
pip install --upgrade pip
```

**Install Python Dependencies**

```bash
pip install -r requirements.txt
```
If you're on a platform without Windows APIs (like Linux), `pywin32` has been
removed so installation should succeed without errors.

**Configure Environment Variables**

```bash
# create .env file in root directory
# put these in there:
OPENAI_API_KEY=
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_INDEX_NAME=
```

**Load Raw Data**

* Provided a script called load_data.py located in the data_ingest/ folder
* It will load CSVs from the raw_data folder into duckDB

```bash
cd data_ingest
python load_data.py
```

**Initialize or Inspect the Existing dbt Project**

```bash
cd data_models

# might not have to run this
dbt init data_models

dbt clean

dbt seed

dbt run

dbt build
```

**Setup Pinecone**

* Get Free Pinecone Index and Update .env
* https://www.pinecone.io/
* Enter index name
* Select text-embedding-3-small Config
* AWS cloud provider
* Create index
* PINECONE_ENVIRONMENT is the value right before .pinecone.io in the HOST name

```bash
python pinecone_utils.py
```

**Getting Started**
* Activate your virtual environment (if you haven’t already)
```bash
cd /path/to/your/project_root
source chatbot_env/bin/activate
```

* Install required packages
```bash
pip install -r requirements.txt
```

**Start the Backend Server**
* The FastAPI (or similar) backend serves the chatbot API (semantic search, OpenAI calls, etc.)
* You need to run the command from one level above the kydxbot/ directory

```bash
cd ..
uvicorn kydxbot.server:app --host 0.0.0.0 --port 8000 --reload
```

**Launch the Frontend App**

* Inside this repo there should be a folder named ReactApp
* From a new terminal

```bash
cd ReactApp
npm install
npm run dev
```


**Query the DuckDB database manually via CLI:**

```bash
cd data
duckdb data.db

.tables
SELECT * FROM customers LIMIT 5;
```

**Generate Local Visualizations**

The `/visualize/complete` endpoint now returns a path to a PNG file created
with `matplotlib`. Provide the SQL query along with x and y columns and a chart
type (bar, line, scatter or pie). The image is saved in the `charts/` folder and
the file path is returned to the frontend. The FastAPI app now serves this
directory under the `/charts` route so the React UI can load the images
directly.

**Table Previews**

Multi-row query results are now rendered as images using `matplotlib` with a
light shaded style. These PNG files are saved in the same `charts/` directory
and returned with a `TABLE:` prefix.

**Summarize Conversation**

After chatting, click the "Summarize?" button to receive a concise bullet style
recap. While the summary is being generated, "Processing..." appears at the
bottom of the chat. The frontend posts your chat history to the `/summarize`
endpoint which uses OpenAI to craft the summary based on the questions, answers
and any visuals created.

**Run the Tests**

After installing dependencies, you can execute the small test suite with

```bash
pytest -q
```
These tests only cover helper functions and will run even if you don't have a
`.env` file configured.

### Troubleshooting Data Questions

If the bot asks you to provide data when you already loaded the sample CSVs,
double‑check that you ran `python data_ingest/load_data.py` and that your `.env`
contains valid OpenAI and Pinecone keys. Including keywords like *sales*,
*revenue* or *orders* in your question helps the chatbot route it through the
DuckDB SQL agent so it can use the existing data without prompting for an
upload.
