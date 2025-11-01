import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_all_tables(html_doc):
    soup = BeautifulSoup(html_doc, 'html.parser')
    tables = soup.find_all('table', class_='TFtable')
    return tables

def get_year_class(url):
    url = "question-paper/2022/XII/Commercial_Art.zip"
    parts = url.split('/')  # splits by '/'
    year = parts[1]         # '2022'
    grade = parts[2] 
    return year, grade

def prepare_url(uri):
    BASE_URL = "https://www.cbse.gov.in/cbsenew/"
    return urljoin(BASE_URL, uri)

def get_details(detail):
    alltd = detail.find_all('td')
    if len(alltd) < 4:
        return None
    subject = alltd[0].get_text(strip=True)
    size = alltd[3].get_text(strip=True)
    link = alltd[1].find('a')['href']
    url = prepare_url(link)
    year, grade = get_year_class(link)
    return { "subject" : subject,"year" : year, "grade": grade, "size": size,"link": url }

def get_all_previous_papers_cbse():
    dict = []
    url = "https://www.cbse.gov.in/cbsenew/question-paper.html"
    response = requests.get(url)
    tables = get_all_tables(response.content)
    for header_div in tables:
        alltr = header_div.find_all('tr')
        for detail in alltr:
            data = get_details(detail)
            dict.append(data)
    return dict
