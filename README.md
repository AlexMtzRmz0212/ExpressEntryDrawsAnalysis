# Canadian Immigration Draw Analysis  
📊 Analysis of Express Entry draw trends (CRS scores, draw sizes, and distributions).  

## Tools Used  
- Python (Pandas, Matplotlib, Seaborn)  
- Power BI
- Tableau
- Jupyter Notebook

## Key Insights Examples
1. CRS scores were lowest in Q1 2023 due to increased draw sizes.  
2. PNP-specific draws had higher cutoffs than general draws.  

## How to Run

Follow these steps to get the project up and running on your local machine.

### 1. Get the Code & Dependencies

First, clone the repository and install the required Python packages.

```bash
# Clone the repository
git clone https://github.com/AlexMtzRmz0212/ExpressEntryDrawsAnalysis.git

cd ExpressEntryDrawsAnalysis

# Install dependencies (pandas, requests, etc.)
pip install -r requirements.txt
```

### 2. Initialize the Data

This project requires data from the IRCC (Immigration, Refugees and Citizenship Canada) API. The first time you run it, you need to fetch all the historical data.

-   **Run the data updater:**
    ```bash
    python update_draws.py
    ```
    This script will:
    - Create a `./Data/` directory.
    - Download the complete draw history as a JSON file.
    - Process and save the data into a clean CSV file (`ExpressEntry.csv`).

### 3. Check the Latest Draw

The main application displays information about the most recent draw and can check for updates.

-   **Run the main program:**
    ```bash
    python last_draw.py
    ```
    When you run this, it will:
    1.  Check your local `ExpressEntry.csv` file.
    2.  Contact the IRCC API to see if any new draws have occurred.
    3.  **Prompt you** to update your local data if new draws are found.
    4.  Display a formatted summary of the latest draw, including the date, draw number, CRS score, and days since the last draw.

### Ongoing Usage

After the initial setup, you can simply run `python last_draw.py` whenever you want to check for new draws. It will handle the update process for you.

### Glosary
dd1: Number of Federal Skilled Worker Program invitations

dd2: Number of Canadian Experience Class invitations

dd3: Number of Federal Skilled Trades Program invitations

dd4 to dd9: Sub-categories by provinces or regions for invitations (e.g., Ontario, Quebec, BC, Alberta, etc.)

dd10 to dd15: Distribution by language proficiency or age groups

dd16 to dd18: Other stats like total candidates in pool, total applicants invited historically, or pending applications