'''
pip install the following before running:
nltk
spacy
spacy-langdetect
bs4
googletrans
pandas
html2text 
'''

import nltk, spacy # stanza pip install each, only nltk/spacy used in this version
print(nltk.data.path)
#nltk.download('punkt')
#nltk.download('punkt_tab')
try:
    nltk.download('all')
except Exception as e:
    print(e)
from nltk.tokenize import sent_tokenize

from bs4 import BeautifulSoup			#Libraries needed for API scraping
from bs4.element import Comment
import urllib.request
from urllib.parse import urlparse, urlsplit
import html2text
from spacy.language import Language     #Language detection and confidence

from spacy_langdetect import LanguageDetector

from googletrans import Translator

import pandas as pd 	#for .xlsx export, pip install pandas openpyxl

def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.find_all(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

 
url = input("Input a URL to scrape for language processing --> ")	# Need to validate the url --> 	https://www.codingdeeply.com/python-check-if-url-is-valid/
parsedUrl = urlparse(url)
if parsedUrl.scheme and parsedUrl.netloc:
    print("*"*50, "\n", "Valid URL ... Standby for results \n", "*"*50)
    html = urllib.request.urlopen(url).read() #might need to encapsulate all in BeautifulSoup()
    txt = text_from_html(html)
    print(txt)	# create .txt with this output
    with open("webpageText.txt", 'w') as file:
        
        #txt = html.find('div', {'class' : 'body'})
        file.write(html2text.html2text(txt))
                   
else:
    print("Invalid URL ... ensure input follows format 'https://www.example.com'")


#clean the .txt of new lines to avoid irregular breaking of words, probably need a 'with open' line for webpageText.txt
with open("webpageText.txt", "r") as file:
    content = file.read()
    #for line in content:
    cleanedFile = content.replace("\n", " ")
with open("webpageText.txt", "w") as file:
    file.write(cleanedFile)
print('*'*50, '\n', 'File Cleaned \n', '*'*50)
    #cleanedFile = file.replace("\n", " ")
    

#create a list of sentences of the file


fileSentenceTokenized = sent_tokenize(cleanedFile, 'en')

# append each sentence to a new text file

for line in fileSentenceTokenized:
    with open("Text_Line_By_Line.txt", 'a') as file:
        print(line)
