import requests
from bs4 import BeautifulSoup
import csv


url = 'https://linear-b.kinezika.com/lexicon.html'


response = requests.get(url)
response.raise_for_status() 

# Parse the content with BeautifulSoup
soup = BeautifulSoup(response.text, 'html.parser')

print(soup.prettify())  # Print the HTML to inspect it manually


with open('linear_b_anthroponyms_toponyms.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Transcription', 'Type', 'Definition'])


    for row in soup.find_all('tr', {'role': 'row', 'class': ['odd', 'even']}):
        cells = row.find_all('td')
        if len(cells) >= 3: 
            transcription = cells[1].text.strip()  
            definition = cells[2].text.strip()

            if 'anthroponym' in definition.lower():
                writer.writerow([transcription, 'Anthroponym', definition])
            elif 'toponym' in definition.lower():
                writer.writerow([transcription, 'Toponym', definition])

print("Scraping complete. Data saved to linear_b_anthroponyms_toponyms.csv.")

