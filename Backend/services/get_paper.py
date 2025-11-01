import requests
from zipfile import ZipFile
from pdfminer.high_level import extract_text

response = requests.get("https://www.cbse.gov.in/cbsenew/question-paper/2022/X/Computer_Applications.zip")

with open("Computer_Applications.zip", "wb") as file:
    file.write(response.content)

with ZipFile("Computer_Applications.zip", 'r') as zip_object:
    zip_object.extractall(".")

    

pdf_path = "53_Computer Applications.pdf"

# Extract text
text = extract_text(pdf_path)

# Print or save the extracted text
print(text)

# (Optional) Save to a text file
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(text)