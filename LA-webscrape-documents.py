import os
import time
import requests
import shutil
from bs4 import BeautifulSoup
from urllib.parse import quote
import csv

pics = "pics"
# Ensure directory exist
os.makedirs(pics, exist_ok=True)


# Path to your CSV file
csv_filename = "sites_data.csv"

docs = []
# Open and read the CSV file
with open(csv_filename, "r", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    headers = next(reader)  # Read the header row
    
    # Iterate through the rows and process data
    for row in reader:
        # get only name of the doc and link with numbers of signs and sequences 
        docs.append(row[2:7])  # Prints each row as a list


signs_csv = "signs.csv"
with open(signs_csv, "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["sign_number", "sign", "function", "document_name", "link", "signs"])

    seq_csv = "sequences.csv"
    with open(seq_csv, "w", encoding="utf-8", newline="") as csvfile_seq:
        writer_seq = csv.writer(csvfile_seq)
        writer_seq.writerow(["sequence_number", "sequence", "complete", "length", "document_name", "link", "sequences"])

        for i in range(len(docs)):
            try: 
                doc_id, link, type, signs, words = docs[i]
                print(docs[i])
                # Fetch the document page
                time.sleep(0.1)
                
                # === 1. Extract Tablet Image ===
                tablet_img_url = link + quote(doc_id) + ".png"
    
                # Download and save the tablet image
                tablet_img_name = os.path.join(pics, f"{doc_id}.png")
                img_response = requests.get(tablet_img_url, stream=True)
                img_response.raise_for_status()
    
                with open(tablet_img_name, "wb") as f:
                    shutil.copyfileobj(img_response.raw, f)
                #print(f"Tablet Image saved at: {tablet_img_name}")
    
                doc_signs = os.path.join(pics, doc_id)
                os.makedirs(doc_signs, exist_ok=True)
    
                for i in range(int(signs)):
                    time.sleep(0.1)
                    sign_pic = link + quote(doc_id) + f"_{i+1}.png"
                    
                    sign_pic_name = os.path.join(doc_signs, f"{i+1}.png")
                    img_response = requests.get(sign_pic, stream=True)
                    img_response.raise_for_status()
    
                    with open(sign_pic_name, "wb") as f:
                        shutil.copyfileobj(img_response.raw, f)
                    #print(f"Sign Image saved at: {sign_pic_name}")
     
                    sign_page = link + f"index-{i+1}.html"
     
                    sign_response = requests.get(sign_page)
                    sign_response.raise_for_status()
                    soup = BeautifulSoup(sign_response.text, "html.parser")
     
                    sign_popup = soup.find("span", class_="selected")
                    sign_name = sign_popup.find("span", class_="sure-reading")
                    sign_name = "[?]" if sign_name is None else sign_name.text
                    sign_fun = sign_popup.find("span", class_="role").text
                    
                    writer.writerow([i+1, sign_name, sign_fun, doc_id, link, signs])
    
                for i in range(int(words)):

                    time.sleep(0.1)
                    seq_page = link + f"index-word-{i}.html"
    
                    seq_response = requests.get(seq_page)
                    seq_response.raise_for_status()
                    soup = BeautifulSoup(seq_response.text, "html.parser")
    
                    seq_popup = soup.find("span", class_="selected")
    
                    seq = seq_popup.find("a", title="View othe rattestations of this sequence").text

                    # a sequence is incomplete 
                    # if some symbols are missing at the beginning (]seq)
                    # if some symbols are missing at the end (seq[)
                    # if an unidentified symbol [?] occurs in the sequence 
                    complete = not ("[" in seq or "]" in seq)
    
                    # remove parenthesis indicating incomplete sequence (we have the flag)
                    if seq.endswith("["):
                        seq = seq[:-1]
                    if seq.startswith("]"):
                        seq = seq[1:]
    
                    length = seq.count("-") + 1
                    #length = sign_popup.find("span", class_="role").text
                    #

                    writer_seq.writerow([i+1, seq, complete, length, doc_id, link, words])
    
                
            except Exception as e:
                print(f"Error processing {doc_id}: {e}")


    print("\nExtraction Complete!")
