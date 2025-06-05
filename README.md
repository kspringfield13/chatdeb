**KYDxBot**

* Python (FastAPI + OpenAI) for the backend
* DuckDB (via dbt) to manage and transform customer data
* dbt for data transformations (seeds, models, builds)
* A React/Next.js (or other Node-based) frontend served via npm

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
# (1) Create a venv in a folder named "venv"
python3 -m venv chatbot_env

# (2) Activate it
source chatbot_env/bin/activate
# You should now see "(venv)" at the front of your prompt.

# (3) Upgrade pip (optional, but recommended)
pip install --upgrade pip
```

**Install Python Dependencies**

```bash
pip install -r requirements.txt
```

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

**Start the Backend Server**

* The FastAPI (or similar) backend serves the chatbot API (semantic search, OpenAI calls, etc.)
* Start the server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
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
