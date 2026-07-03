import requests
from bs4 import BeautifulSoup

URL = "https://forum.finanzaonline.com/forums/etf-fondi-e-gestioni-e-investment-certificates.6/"

with open("isins.txt") as f:
    ISINS = [x.strip().upper() for x in f if x.strip()]

print("Monitoring these ISINs:")
print(ISINS)

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(URL, headers=headers)

print(r.status_code)

soup = BeautifulSoup(r.text, "lxml")

titles = soup.find_all("a")

for t in titles:
    text = t.get_text(" ", strip=True).upper()

    for isin in ISINS:
        if isin in text:
            print(isin, text)
