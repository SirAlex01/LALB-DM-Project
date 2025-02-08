import csv
from bs4 import BeautifulSoup
import requests
import time
import re
import os
import shutil
import unicodedata

# unfortunately, info from main LIBER text page cannot be web-scraped, as documents are returned as a result of a JS modification
# but I copied the HTML element containing the whole collection

# Open and parse the local HTML file
with open("LIBER.html", "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Extract anchor tags with class "idtab"
anchors = soup.find_all("a", class_="idtab")

# Prepare data for CSV
data = []
base_url = "https://liber.cnr.it/tablet/view/"

# collect id, doc_name, link from html
for anchor in anchors:
    doc_id = anchor.get("id")
    doc_name = anchor.text.strip()
    
    if doc_id and doc_name:
        doc_url = base_url + doc_id  # Adjust ID as per the pattern
        data.append([int(doc_id), doc_name, doc_url])
data.sort() # by document_id

pics = "pics_LB"
os.makedirs(pics, exist_ok=True)

def remove_dots_below(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))

# Function to make requests reliably: all documents are present for sure (manually checked failures)
def make_request(url, stream=False):
    while True:
        try:
            response = requests.get(url, stream=stream)
            response.raise_for_status()
            return response
        except requests.RequestException:
            print("REQUEST FAILED. Retrying in 5 seconds...")
            time.sleep(5)

# time to web-scrape 
with open("signs_LB.csv", "w", encoding="utf-8",newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["sign_number", "sign", "id", "document_name", "link", "signs"])

    with open("sequences_LB.csv", "w", encoding="utf-8",newline="") as csv_seq:
        writer_seq = csv.writer(csv_seq)
        writer_seq.writerow(["sequence_number", "sequence", "complete", "length", "id", "document_name", "link", "sequences"])

        for i in range(len(data)):
            doc_id, doc, link = data[i]
            try:
                time.sleep(0.1)
                doc_response = make_request(link)
                doc_soup = BeautifulSoup(doc_response.text, "html.parser")

                info = doc_soup.find_all("h6", class_="info_tab")
                # extract Findspot, Scribe, Palmprint, Chronology
                for j in range(1, len(info)):
                    val =  " ".join(info[j].text.split())
                    data[i].append(val if val != "—" else None)


                pref_url = "https://liber.cnr.it"
                pic_urls = doc_soup.find_all("a", class_="single_image")
                if len(pic_urls) > 0:
                    doc_pics = os.path.join(pics, str(doc_id))
                    os.makedirs(doc_pics, exist_ok=True)
                for j, url in enumerate(pic_urls):
                    sign_pic_name = os.path.join(doc_pics, f"{j+1}.png")
                    time.sleep(0.1)
                    img_response = make_request(pref_url + url["href"], stream=True)

                    with open(sign_pic_name, "wb") as f:
                        shutil.copyfileobj(img_response.raw, f)

                doc_text = doc_soup.find("div", id="table-text-container")
                
                if doc_text is None:
                    for _ in range(2):
                        data[i].append(0)
                    continue
                
                doc_text = doc_text.text.split()
                sequences = []

                j = 0
                while j < len(doc_text):
                    s = doc_text[j]
                    if s in "[],/↓→↗⸤⸥/⟦⟧:×" or s.startswith(".") or s.endswith(".") or s=="vacat" or s == "vest." or s == "deest" or s == "margo" or \
                        s == "reliqua" or s == "pars" or s == "sine" or s == "regulis" or s == "prior" or s == "Graffito":
                        j += 1
                        continue

                    s = remove_dots_below(s)
                    s = s.replace("[•]", "(TEMP)").replace("[-•-]","(TEMPP)").replace("'","").replace('"',"").replace("-]", "-").replace("[-", "-").replace("]-", "-") \
                         .replace("-[", "-").replace("--", "-").replace("?", "").replace("(TEMP)","[?]").replace("(TEMPP)","-[?]-").replace("•-•","[?]-[?]") \
                         .replace("⟦","").replace("⟧","").replace("[[","[").replace("]]","]").replace("⸥","").replace("⸤","").replace("•","[?]").replace("/","").replace(",","")\
                    
                    # skip all rows referring to sigillum
                    if s == "supra" or s == "sigillum":
                        for k in range(j+6 if s == "sigillum" else j+7):
                            if j + k < len(doc_text):
                                print("SKIPPING:",doc_text[j+k])
                        j = j + 6 if s == "sigillum" else j + 7
                        continue

                    complete = not (s.startswith("]") or s.endswith("[") or s.startswith("[") or s.endswith("]") or s.startswith("-") or s.endswith("-") or "[?]" in s)
                    if s.startswith("]") or (s.startswith("[") and not s.startswith("[?]")):
                        s = s[1:]
                    if s.endswith("[") or (s.endswith("]") and not s.endswith("[?]")):
                        s = s[:-1]
                    if s.startswith("-"):
                        s = s[1:]
                    if s.endswith("-"):
                        s = s[:-1]

                    if len(s) > 0 and not (s in "[],/↓→↗⸤⸥/⟦⟧:×" or s.startswith(".") or s.endswith(".") or s=="vacat" or s == "vest." or s == "deest" or s == "margo" or \
                        s == "reliqua" or s == "pars" or s == "sine" or s == "regulis" or s == "prior" or s == "Graffito"):
                        sequences.append(s)
                    
                    j += 1
                    if s == "separatum":
                        j += 1
                print(sequences,link)

                signs_counter = 0
                sign_data = []
                for j, seq in enumerate(sequences):
                    length = seq.count("-") + 1
                    writer_seq.writerow([j+1, seq, complete, length, doc_id, doc_name, link, len(sequences)])
                    for k, sign in enumerate(seq.split("-")):
                        sign_data.append([signs_counter+k+1, sign, doc_id, doc_name, link])
                    signs_counter += length

                for j in range(signs_counter):
                    sign_data[j].append(signs_counter)

                writer.writerows(sign_data)

                data[i].append(signs_counter)
                data[i].append(len(sequences))

            except Exception as e:
                print(f"Error processing {doc}: {e}")

# Save to CSV
with open("LIBER_documents.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["id", "document_name", "link", "findspot", "scribe", "palmprint", "chronology", "museum_inventory_number", "signs", "words"])
    writer.writerows(sorted(data))

print(f"Saved {len(data)} records to LIBER_documents.csv")
