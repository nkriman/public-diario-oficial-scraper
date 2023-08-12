
# Diario Oficial Scraper Documentation
## Introduction
This project provides an automated scraper tailored to extract, parse, process, and upload data from the official publication medium of the government of Chile, Diario Oficial. 
The scraped data revolves around business entities, specifically their incorporation, modifications, and dissolution.

## Getting Started
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

