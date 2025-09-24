import requests
import pandas as pd
# from bs4 import BeautifulSoup

# clear terminal output
import os
os.system('cls' if os.name == 'nt' else 'clear')


url = "https://www.canada.ca/content/dam/ircc/documents/json/ee_rounds_123_en.json"

# def parse_html_link(html_str):
#     """Extract text and href from an HTML anchor tag string."""
#     if not html_str:
#         return "", ""
#     soup = BeautifulSoup(html_str, "html.parser")
#     a = soup.find("a")
#     if a:
#         return a.text.strip(), a.get("href")
#     return html_str, ""
try:
    response = requests.get(url)
    data = response.json()
    if "rounds" not in data:
        print("No 'rounds' key found in the JSON data.")
        exit(1)
    # get the number of draws
    draw_count = len(data["rounds"])
except requests.exceptions.RequestException as e:
    print(f"Error fetching data from {url}: {e}")
    exit(1)

# check the number of rows in the ExpressEntry.csv
try:
    existing_df = pd.read_csv("ExpressEntry.csv")
    existing_count = len(existing_df) -1 # Subtract 1 for the header row
    print(f"Existing rows in ExpressEntry.csv: {existing_count}")
except FileNotFoundError:
    print("File not found. Creating a new one.")

# if existing_count == draw_count exit, if not excecute the code
if existing_count == draw_count:
    print("No new draws to add.")
    exit(0)

rows = []
for round_info in data["rounds"]:
    parsed = {}
    for key, val in round_info.items():
        parsed[key] = val
        # Parse HTML links for specific fields
        # if key in ["drawNumberURL", "mitext", "DrawText1"]:
        #     text, href = parse_html_link(val)
        #     parsed[f"{key}_text"] = text
        #     parsed[f"{key}_url"] = "https://www.canada.ca" + href if href.startswith("/") else href
        # else:
        #     parsed[key] = val
    rows.append(parsed)

df = pd.DataFrame(rows)

# Reorder columns so URLs are right after their text
# cols = []
# for c in df.columns:
#     if c.endswith("_text"):
#         base = c[:-5]
#         cols.append(c)
#         url_col = base + "_url"
#         if url_col in df.columns:
#             cols.append(url_col)
#     elif not c.endswith("_url"):
#         cols.append(c)

# df = df[cols]

# Select columns
selected_columns = [
    "drawNumber",
    "drawDate",
    "drawName",
    "drawSize",
    "drawCRS",
    "drawText2",
    "drawDateTime",
    "drawCutOff",
    "drawDistributionAsOn",
    "dd1",
    "dd2",
    "dd3",
    "dd4",
    "dd5",
    "dd6",
    "dd7",
    "dd8",
    "dd9",
    "dd10",
    "dd11",
    "dd12",
    "dd13",
    "dd14",
    "dd15",
    "dd16",
    "dd17",
    "dd18"
]

df = df[selected_columns]

df.to_csv("ExpressEntry.csv", index=False)