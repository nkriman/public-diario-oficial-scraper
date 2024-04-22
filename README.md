
# Diario Oficial Scraper Documentation
## Introduction
This project provides an automated scraper tailored to extract, parse, process, and upload data from the official publication medium of the government of Chile, Diario Oficial. 
The scraped data revolves around business entities, specifically their incorporation, modifications, and dissolution.
When I first looked at the Diario Oficial (https://en.wikipedia.org/wiki/Diario_Oficial_de_la_Rep%C3%BAblica_de_Chile), it struck me that such a goldmine of public information was trapped behind an interface without a potent search function. If knowledge is power, then public knowledge should be democratically available and easily accessible. That’s what propelled me to embark on a journey — creating an API for the Diario Oficial. For a bit of context, according to the Wikipedia page:

    The Official Journal of the Republic of Chile (Spanish: Diario Oficial de la República de Chile) is Chile’s government gazette — a means of publication of laws, decrees, and other legal regulations issued by state bodies. It was created by decree of President Aníbal Pinto on 15 November 1876. Its first issue was published on 1 March 1877. The Official Journal appears Monday through Saturday, except holidays.

## From Curiosity to Code: The Inception

I’ve always believed that when you encounter a problem, you either find a solution or create one. And with my burgeoning interest in coding, cloud infrastructure, and data engineering, building a solution for the Diario Oficial was the challenge I needed. Moreover, as an advocate for transparent access to public data, the idea of an API resonated with me. It’s not just about reading data; it’s about making it searchable, filterable, and integrable.
## The main functionality of the scraper


The Diario Oficial website structure is simple enough. I created a generic function to abstract the parsing of each publication component to the html using Beautifulsoup:
```python
def soup_to_dictionary(soup):
    soup_dictionary = {}  # Dictionary to store the soup_dictionary

    # Temporary variables to store the current titles
    title1 = title2 = title3 = title4 = title5 = None

    for row in soup.select("tr"):
        if "title1" in row.td.get("class", []):
            title1 = row.td.get_text(strip=True)
            soup_dictionary[title1] = {}
            title2 = title3 = title4 = title5 = None
        elif "title2" in row.td.get("class", []):
            title2 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2] = {}
            title3 = title4 = title5 = None
        elif "title3" in row.td.get("class", []):
            title3 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2][title3] = {}
            title4 = title5 = None
        elif "title4" in row.td.get("class", []):
            title4 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2][title3][title4] = {}
            title5 = None
        elif "title5" in row.td.get("class", []):
            title5 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2][title3].setdefault(title4, {})[title5] = []
        elif "content" in row.get("class", []):
            name_div = row.select_one('td > div[style="float:left; width:550px;"]')
            rut_div = row.select_one('td > div[style="float:right;"]')
            link_a = row.select_one("td > a")
            if name_div and link_a:
                company_info = {
                    "company": name_div.text.strip(),
                    "link": link_a["href"],
                    "link_text": link_a.get_text(strip=True),
                }
                if rut_div:
                    company_info["RUT"] = rut_div.text.strip()
                soup_dictionary[title1][title2][title3].get(title4, {}).get(
                    title5, []
                ).append(company_info)

    return soup_dictionary
```

And so the main.py component can have more abstract logic to parse and save the content:

```python
def process_edition(edition, functions, publication_date, engine, batch_id):
    # Convert the edition URL to point to the "empresas_cooperativas" section
    url_parts = edition.split("?")
    specific_url = f"https://www.diariooficial.interior.gob.cl/edicionelectronica/empresas_cooperativas.php?{url_parts[1]}"
    # fetch url and parse html
    response = fetch_url(specific_url)
    soup = parse_html(response)
    # extract content and save it as a dictionary
    contents = soup_to_dictionary(soup)
    # iterate over the companies and their pdfs
    logging.info("Starting extraction...")
    for section, function in functions.items():
        if "Sumario" in contents and "Empresas y Cooperativas" in contents["Sumario"]:
            if section in contents["Sumario"]["Empresas y Cooperativas"]:
                for sub_section in contents["Sumario"]["Empresas y Cooperativas"][
                    section
                ][""]:
                    for item in contents["Sumario"]["Empresas y Cooperativas"][section][
                        ""
                    ][sub_section]:
                        pdf_link = item["link"]
                        # get the text content of the pdf
                        logging.info(f"Parsing PDF link: {pdf_link}")
                        time.sleep(
                            random.uniform(MIN_DELAY, MAX_DELAY)
                        )  # Be nice to the government
                        item["text_content"] = PdfParser().get_pdf_text(pdf_link)
                        item["clean_text_content"] = clean_text(item["text_content"])
                        item["trimmed_text_content"] = trim_text(
                            item["clean_text_content"]
                        )
                        item["section"] = section
                        item["sub_section"] = sub_section
                        item["publication_date"] = publication_date

                        logging.info("Uploading record to database")
                        upload_to_db(engine, item, batch_id)
            else:
                logging.info(f"No available content in section: {section}")
        else:
            logging.info("Reached end of file")
```

The parameters for process_edition are:

- edition: The URL of the Diario Oficial edition.
- functions: A dictionary that maps section names to functions that process those sections.
- publication_date: The date of the edition's publication.
- engine: Database engine used for uploading processed data.
- batch_id: Identifier for each batch of processed data.

## Step-by-Step Explanation:

### URL Manipulation:

The URL for the given edition is tweaked to directly target the “empresas_cooperativas” section. This tailored URL helps fetch just the required data, ensuring efficiency.

### Fetching and Parsing:

The tailored URL is fetched, and its content is parsed into a structured HTML format using the parse_html function.

### HTML to Dictionary Transformation:

The parsed HTML (contained in the soup variable) is then transformed into a dictionary structure using soup_to_dictionary. This makes data extraction more systematic and easier.

### Data Extraction:

The function logs the commencement of the extraction process.
Iterating through each section and its associated function, the function checks if the “Empresas y Cooperativas” content is available for extraction.
For every available section and subsection, it identifies PDF links associated with companies.

### PDF Parsing and Text Processing:

Every identified PDF link is logged and then processed.
To ensure respectful and non-abrupt server requests, a random sleep duration between a minimum (MIN_DELAY) and maximum (MAX_DELAY) limit is introduced before fetching each PDF.
The PdfParser class fetches text content from the PDF.
This text is then cleaned, trimmed, and further structured with meta-data like section, subsection, and publication date.

### Uploading to Database:

Each processed item (with the extracted and processed data) is uploaded to the specified database using the provided engine.

### Logging:

The function keeps a clear log of its progress. It identifies when content is available for extraction, and if not, it logs the sections where content is unavailable or when it has reached the end of the file. I graduated from debugging using print() some time ago, and it makes a big difference!
## A problem of scale

This project, while fueled with enthusiasm, wasn’t without its challenges. My first iterations, though functional, struggled under the vast volume of processing. It was a rite of passage for me. As I soon discovered, what works in theory or on a small scale can sometimes falter when faced with real-world data loads.

The website publishes around 200 new articles in electronic PDF format per day, in a somewhat standard digital format since 2016 (before that it published in a very difficult to parse format). That meant that there were around 500.000 articles to download!

The architecture had to evolve. Running the scraper on a local machine soon bumped into a wall: IP bans. Servers usually have mechanisms to detect suspicious activity, and a scraper running without any limitations or pause can appear malicious. Here, not only was there a technical problem to solve but also an ethical dilemma: how to extract public data without overburdening the public resource.

## Stepping Up with Cloud VM:

The first pivot was to leverage a Google Cloud Platform (GCP) Virtual Machine (VM). Running on a cloud-based VM offers several benefits:

Uptime: It can run continually, ensuring consistent data extraction.
Independence: Using Linux commands, the scraper can run even if the terminal connection is lost.
Scalability: Cloud VMs can be upgraded or downsized based on the requirements.

### Innovative IP Rotation with AWS API Gateway:

One of the standout features of this solution is the integration of the AWS API Gateway to facilitate IP rotation. IP rotation is crucial for extensive scraping tasks as it reduces the chances of getting banned by the source server.

This is achieved using requests_ip_rotator which interfaces with the API Gateway. The get_gateway function ensures that an instance of the IP rotating gateway is started and used whenever required, while shutdown_gateway responsibly closes down the gateway once the scraping job is finished.

### Concurrent Processing with Respect:

Multithreading is introduced to enhance the scraper’s efficiency. Each thread operates with a distinct IP, making the scraping process faster and more distributed. However, instead of letting all threads run amok, the following considerations are kept:

Limiting the Pool Size: By using Python’s multiprocessing Pool, concurrent jobs are managed. The number of jobs is not set to an extreme, ensuring that the server isn't overwhelmed.
Delays Between Executions: To further reduce the strain on the server, there’s an intentional delay between executions. This is an excellent move both technically (to avoid server-side throttling or bans) and ethically.

## Working with the data

### Automating Daily Scraping with GitHub Actions CRON Job:

Once the historical data was scraped, the focus shifted to keeping the dataset updated with the most recent data. Automating this task is where GitHub Actions stepped in, providing a robust platform to host a CRON job that would execute the scraping process daily.

This setup ensures that the dataset remains up-to-date without manual intervention, aligning with the principles of modern DevOps practices.

Building an Efficient API with Materialized Views and Indexing:

The next phase in the project was exposing the scraped data through an API. This required careful consideration of performance, especially given the size of the dataset, with over half a million records. To achieve this, a two-step approach was adopted:

Creating a Materialized View: Instead of directly querying the vast dataset, a materialized view named dof_materialized_2 was created. This SQL snippet demonstrates the process, first dropping the existing table (if any), then creating the materialized view by selectively pulling and transforming the required fields from the raw data. This was the first time I worked with a JSON field, it was very interesting!
Indexing for Performance: To further boost query performance, an index was created on the rut column. Indexing is a powerful optimization technique in relational databases, significantly reducing query execution time, especially for large datasets. I think the before and after was like 3 times faster.

The replace on the “RUT” field is made because, when the company self reports its tax ID (RUT), the publication notes that using an asterisk. I saved that valuable information in a different field.

Here’s a look at the SQL code that orchestrates this:
~~~sql
DROP TABLE IF EXISTS dof_materialized_2;

CREATE TABLE dof_materialized_2 as
select
    id,
    lower(REGEXP_REPLACE((json_payload->>'RUT')::text, '[.*]', '', 'g')) as RUT,
    -- (other fields here)...
from
    dof_2
where
    substring((json_payload->>'trimmed_text_content')::text from 1 for 4) = 'EXTR'
    and json_payload->>'section' = 'MODIFICACIÓN';

CREATE INDEX dof_materialized_2_rut_index ON dof_materialized_2 (rut);
~~~
This materialization is also made on a daily basis using a CRON job hosted on Github Actions.
## Building a Secure, User-Friendly Flask API on GCP coderun

As the project progressed, there was a pressing need to expose the collected data to end-users. An API bridges the gap between a dataset and its potential users, serving as the front-end of all the data collection, transformation, and storage efforts. But not just any API would do — it had to be user-friendly, efficient, and, most importantly, secure.
The Platform — GCP coderun:

Using Google Cloud’s coderun was a strategic choice for several reasons:

Automated CI/CD: Directly connecting the repository to GCP coderun ensured that any changes made to the codebase were automatically reflected in the deployed API, reducing manual deployment efforts and increasing productivity.
Scalability and Performance: GCP coderun promises automatic scalability, meaning that regardless of the incoming request volume, the service will adapt. This ensures users always get a responsive experience.

## Diving Deep into the Code:

The Flask API crafted for this purpose is a testament to clean and efficient coding practices:

API Key Authentication: Every user must provide an API key, which is first verified against the api_keys table in the database. This not only authenticates users but also allows for tracking usage and even implementing potential rate limits or tiered access in the future.
Structured Queries: Instead of constructing SQL queries on-the-fly, a structured get_tax_record_query function prepares the required SQL text. This makes the code more maintainable and reduces the risk of SQL injection attacks.
Error Handling: The API gracefully handles various potential issues — from unauthorized access due to invalid API keys to internal server errors, always providing the user with a clear message.

Let’s discuss the main endpoint:

~~~python

from flask import Flask, jsonify
from database import get_db, close_db
from sqlalchemy import text
from http import HTTPStatus
from urllib.parse import unquote


app = Flask(__name__)
app.teardown_appcontext(close_db)


def get_tax_record_query(tax_id):
    return (
        text(
            """
        SELECT * FROM dof_materialized_2 WHERE rut = :tax_id
    """
        ),
        {"tax_id": tax_id},
    )


@app.route("/api/v1/modifications/<string:api_key>/<string:tax_id>", methods=["GET"])
def get_tax_record(api_key, tax_id):
    try:
        db = get_db()

        # Check API Key
        result = db.execute(text('SELECT * FROM api_keys WHERE key = :key AND is_active = true'), {'key': api_key})
        if not result.fetchone():
            return jsonify({"error": "Invalid or inactive API key"}), HTTPStatus.UNAUTHORIZED

        # If API Key is correct, proceed with the query
        query, params = get_tax_record_query(tax_id)
        result = db.execute(query, params)
        column_names = result.keys()
        query_results = [
            {column: value for column, value in zip(column_names, row)}
            for row in result
        ]

        if not query_results:
            return jsonify({"error": "Tax ID not found"}), HTTPStatus.NOT_FOUND

        return jsonify(query_results)
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR

~~~
This endpoint fetches records based on the provided tax_id. But before diving into the actual query, it ensures that the provided API key is valid and active. If everything checks out, it queries the dof_materialized_2 table, and the results are structured and returned in a JSON format. If no matching records are found, it returns a 'Tax ID not found' message, and in case of any exception, an error message is generated, ensuring the user is always informed.
## A Transparent Future: Towards Open Public Data

At the heart of this journey is a conviction: Public data, especially of the magnitude and significance of Diario Oficial, should be easily accessible. As I transitioned from one phase of the project to another, this conviction only strengthened. And now, with the API built, I envision a future where developers, researchers, and curious minds can tap into this resource, integrating it into applications, studies, or even simple queries.

## Getting Started to reproduce the results
### Features

- **Scraping**: Extracts information about companies and cooperatives from various editions of Diario Oficial.
- **PDF Parsing**: Parses PDF files for specific sections (e.g., Incorporation, Modification, Dissolution).
- **Data Cleaning**: Cleans and trims the extracted text content.
- **Database Integration**: Uploads processed records to a specified Azure Database.
- **Proxy Rotation**: Employs a proxy rotation system to reduce the risk of IP banning.
- **OpenAI Integration**: Establishes a connection with OpenAI and provides processing functions for specific data structures.
- **Multithreading**: Utilizes multiprocessing to optimize the processing of multiple dates or editions.

### Scraper Variants

1. **Main Scraper (`main.py`)**: This script is designed to scrape data for a specified date range. It's ideal for backfilling or extracting data for historical analysis.

2. **Today's Scraper (`scraper_today.py`)**: This script focuses solely on the current day. It's lightweight, efficient, and tailored to be run daily by an external CRON job to keep the data up-to-date without any manual intervention.
### Prerequisites
Ensure you have Python (3.x) installed.
### Required dependencies:
json
logging
uuid
os
time
random
multiprocessing
dotenv
Custom modules as seen in the imports.
### Installation
Clone the repository:
```bash
git clone [repository_link]
```
Navigate to the project directory:

```bash
cd [project_directory]
```
Install the required packages:

```bash
pip install -r requirements.txt
```

Usage
Environment Variables
Firstly, ensure you have the .env file populated with the following variables:

- **AZURE_DB_USER**: The Azure database user name.
- **AZURE_DB_PASSWORD**: The Azure database password.
- **AZURE_DB_HOST**: The Azure database host URL.
- **API_KEY**: OpenAI API key for natural language processing.
Use **load_dotenv()** to load these variables into the environment.

Running the Scraper
Execute the script via:

```bash
python [script_name].py
```

The script will:

- Initialize the proxy gateway for Diario Oficial.
- Establish a connection to the Azure database.
- Initialize OpenAI services.
- Start the scraping process based on a specified date range.

### Core Functions
- main(): The main driver function of the script.
- process_date(): Handles the scraping operations for a given publication date.
- iter_dates(): Yields one date at a time from a list of dates.
- process_edition(): Processes individual editions from a publication date.
## Components
### Proxy Rotation
To bypass potential scraping barriers, the script utilizes proxy rotation, specifically the get_gateway and shutdown_gateway functions from the proxy_rotation module.

### Multi-processing
The script leverages Python's multiprocessing to parallelize the scraping of different publication dates, enhancing efficiency.

### Data Processing & Storage
Data fetched from the website is first parsed and converted into structured data.
Relevant PDFs are extracted, their content is parsed, cleaned, trimmed, and finally uploaded to the Azure database.
### Error Handling
The script uses Python's logging module to record its progress and report any issues during its execution.

## Important Notes
Avoid overwhelming the government website by maintaining a delay (MIN_DELAY to MAX_DELAY) between requests.
Ensure the necessary environment variables are set before running the script.
Regularly monitor the logs to diagnose potential issues.
## Contribution
Feel free to contribute to this project by submitting pull requests or issues. Before submitting a PR, ensure your code follows the project's code standards.

## License
This project is licensed under the MIT License.

