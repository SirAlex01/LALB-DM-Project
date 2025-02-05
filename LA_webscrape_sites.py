import os
import csv
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, quote
import re
from tqdm import tqdm

# Base URL of the SigLA website
base_url = "https://sigla.phis.me"
browse_url = f"{base_url}/browse.html"

# Send a GET request to the browse page
response = requests.get(browse_url)
response.encoding = 'utf-8'  # Explicitly set encoding to UTF-8
response.raise_for_status()

# Parse the browse page content
soup = BeautifulSoup(response.text, "html.parser")

# Dictionary to store found sites and their documents
sites_dict = {}

# Find all "fieldset" elements containing site data
for fieldset in soup.find_all("fieldset", class_="result1"):
    # Extract site name from the legend
    legend = fieldset.find("legend")
    if legend:
        site_name = legend.text.split(":")[1].split("[")[0].strip()[1:-1]

        # Find all document links inside this site block
        document_links = set()  # Use a set to avoid duplicates
        for a in fieldset.find_all("a", href=True):
            link = quote(a["href"])

            if "document/" in link:
                full_link = f"{base_url}/{link}"

                # Remove links with "/index-<number>.html"
                if not ("/index-" in full_link):
                    document_links.add(full_link)

        # Store document links in the dictionary
        sites_dict[site_name] = sorted(document_links)  # Sort for consistency

# CSV file setup
csv_filename = "sites_data.csv"
with open(csv_filename, "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["site", "number_documents", "document_name", "link", "type", "signs", "words", "location", "period", "motif", "width_cm", "height_cm", "depth_cm"])

    # Loop through sites and extract metadata from document pages
    for site, docs in tqdm(sites_dict.items()):
        for doc in docs:
            try:
                # Wait 0.1 seconds before each request
                time.sleep(0.1)

                # Fetch document page
                doc_response = requests.get(doc)
                doc_response.raise_for_status()
                doc_soup = BeautifulSoup(doc_response.text, "html.parser")

                # Extract document metadata
                metadata_div = doc_soup.find("div", class_="document-metadata")

                # Extract document name from URL
                document_name = doc.replace(f"{base_url}/document/", "").rstrip("/")
                document_name = unquote(document_name)  # Convert %20 to spaces

                if metadata_div:
                    # Extract type of document
                    type_tag = metadata_div.find("a", href=lambda x: x and "/kind/" in x)
                    doc_type = type_tag.text.strip() if type_tag else ""

                    # Extract location
                    location_tag = metadata_div.find("a", href=lambda x: x and "/location/" in x)
                    location = location_tag.text.strip() if location_tag else ""

                    motif = None
                    if "Motif" in metadata_div.text:
                        motif = metadata_div.text.split("Motif: ")[1].split("(C")[0].strip()


                    # Extract dimensions (width × height × depth)
                    width_cm, height_cm, depth_cm = None, None, None
                    if doc_type != "Nodule" and doc_type != "Pithos" and doc_type != "Lamp" and doc_type!= "Sherd" \
                        and doc_type!= "Graffiti" and doc_type!= "Pithoid jar" and doc_type!= "Clay vase" and doc_type!= "Cup" \
                        and doc_type!= "Jewellery" and doc_type!= "Architecture" and doc_type!= "Stone weight" and doc_type!= "Clay weight" \
                        and doc_type!= "Metal engraving" and doc_type!= "Libation table":
                        dimensions = metadata_div.text.split("(")[1].split(")")[0].replace("Ã", "x")
                        if "x" in dimensions:
                            size_parts = dimensions.split("x")

                            # remove badly encoded and textual characters
                            for i in range(len(size_parts)):
                                size_parts[i] = size_parts[i].replace("\x97", "").replace("cm", "").strip()

                            width_cm = size_parts[0]
                            height_cm = size_parts[1]
                            depth_cm = size_parts[2]
                        if width_cm is None:
                            print(metadata_div.text)

                    # Extract period
                    period_tag = metadata_div.find("a", href=lambda x: x and "/period/" in x)
                    period = period_tag.text.strip() if period_tag else ""

                    # Extract number of signs and words from the last row of the metadata
                    signs_words_text = metadata_div.text.split("\n")[-1]  # Last row of the metadata
                    signs, words = None, None

                    # Use regular expression to extract the number of signs and words
                    match = re.search(r"(\d+)\s+signs\s*/\s*(\d+)\s+words", signs_words_text)
                    if match:
                        signs = match.group(1)
                        words = match.group(2)

                    if signs is None:
                        print("AOOO", metadata_div.text)
                    # Write data to CSV
                    writer.writerow([site, len(docs), document_name, doc, doc_type, signs, words, location, period, motif, width_cm, height_cm, depth_cm])

            except Exception as e:
                print(f"Error processing {doc}: {e}")

print(f"Sites and documents organized successfully! Data saved in {csv_filename}")
