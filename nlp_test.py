import requests
from bs4 import BeautifulSoup
import os
from googletrans import Translator
import spacy 
from spacy import tokenizer
from prettytable import PrettyTable
import asyncio
import nltk
from nltk.tokenize import word_tokenize
from pyfiglet import Figlet
import pandas as pd 

# python(version) -m spacy download (spacy NLP model)
def print_welcome_message(text="WELCOME\n    TO\nPOLYGLOT", font_name="big_money-ne"):
    f = Figlet(font=font_name)
    print(f.renderText(text))
def import_existing_excel_file():
    
    key_column = 'Lemma'
    value_column = 'Translation'
    while True:
        user_selection = input("Would you like to import an existing word list? NOTE: file must be .xls or .csv \n\nY/N: ")
        if user_selection == 'y':
            import_file = input("Please input the name of your current dictionary file: ")
            import_file = os.path.abspath(import_file)
            try:
                if os.path.exists(import_file) and import_file.endswith(('.xlsx', '.xls')):
                    readfile = pd.read_excel(import_file)
                elif os.path.exists(import_file) and import_file.endswith(('csv')):
                    readfile = pd.read_csv(import_file)
                else:
                    raise ValueError("Unsupported file format. NOTE: Must use .xlsx, .xls, or .csv files.")
            except FileNotFoundError:
                raise FileNotFoundError(f"File not found at path: {import_file}")
            except Exception as e:
                raise Exception(f"An error occurred while reading the file: {e}")
                
            if key_column not in readfile.columns or value_column not in readfile.columns:
                raise ValueError("One or both specified columns not found in the file.")
                
            import_data_dict= dict(zip(readfile[key_column], readfile[value_column]))
            return import_data_dict
        
        elif user_selection == 'n':
            print("You'll have the option to create a new dictionary file in a few steps. Save it for future uses!")
            return
        elif user_selection != 'y' or 'n':
            confirmation = input("Please input Y or N:")
            continue
    print("\n\nDictionary successfully imported\n\n")
    
    '''
    give the user the option to import an existing excel file if they would like to update a current one.
    if no, a new file will be created
    
    if yes upload current file to unique lemmas to process new words against
    '''
def target_language_selection():            # should probably use the large (lg) language models

    language_map = {
        '1': {'code': 'ru', 'model': 'ru_core_news_sm'}, # russian
        '2': {'code': 'es', 'model': 'es_core_news_sm'}, # spanish
        '3': {'code': 'ar', 'model': 'xx'}, # Placeholder for universal model arabic
        '4': {'code': 'fa', 'model': 'xx'}, # Placeholder for universal model farsi
        '5': {'code': 'ko', 'model': 'ko_core_news_sm'}, # korean
        '6': {'code': 'zh', 'model': 'zh_core_web_sm'}, # chinese
    }

    while True:
        user_input = input("\nSelect your target language from the following: \n\n [1] Russian \n [2] Spanish \n [3] Arabic \n [4] Farsi \n [5] Korean \n [6] Chinese \n\n\n --> ").strip()

        if user_input in language_map:
            selected_info = language_map[user_input]
            return selected_info['code'], selected_info['model']
        else:
            print("Invalid selection. Please input a number from 1 to 6.")
    
def get_webpage_body_text(url, output_file='webpage_content.txt'):
    """
    Retrieves the body text of a webpage and saves it to a text file.

    Args:
        url (str): The URL of the webpage to retrieve.
        output_filename (str): The name of the output text file.
                               Defaults to "webpage_body_text.txt".
    """
    try:
        # 1. Fetch the webpage content
        print(f"\nFetching content from: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        # Ensure content is decoded as UTF-8, which is standard for web
        html_content = response.content.decode('utf-8', errors='ignore')

        # 2. Parse the HTML content
        print("Parsing HTML content...")
        soup = BeautifulSoup(html_content, 'html.parser')

        # 3. Extract the body text
        # We target the 'body' tag, which contains the visible content of the page.
        # .get_text(separator='\n') ensures that block-level elements
        # (like paragraphs, divs) have newlines between them for readability.
        body_tag = soup.body
        if body_tag:
            # You can experiment with different ways to get text:
            # text_content = body_tag.get_text() # Simple text, might be very dense
            text_content = body_tag.get_text(separator='\n', strip=True)
            print("Successfully extracted body text.")
        else:
            print("Warning: Could not find <body> tag. Extracting text from the whole document.")
            text_content = soup.get_text(separator='\n', strip=True)

        # 4. Clean up the text (optional but recommended)
        # Remove excessive blank lines
        cleaned_text = os.linesep.join([s for s in text_content.splitlines() if s.strip()])
        # Further clean up might involve removing JavaScript, CSS, or script contents
        # BeautifulSoup's .get_text() with 'strip=True' handles a lot of this.

        # 5. Output the text to a file
        print(f"Writing extracted text to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
         
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL '{url}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


async def process_text_for_lemmas(file_path, target_language, spacy_model_name, import_data_dict):
    
    """
            Processes a text file to extract unique lemmas, their parts of speech,
            and English translations, then outputs them to a PrettyTable.
        
            Args:
                file_path (str): The path to the input text file.
                target_language (str): The source language for translation.
                                        Defaults to 'auto' for auto-detection.
            """
            # 1. Initialize NLP model and Translator
    print(f"Loading spaCy NLP model... {spacy_model_name}")
    try:
                # Load a small English model. Adjust if you need other languages or larger models.
                # Ensure you've downloaded it: python -m spacy download en_core_web_sm
        posNLP = spacy.load(spacy_model_name)
        print("spaCy model loaded.")
    except OSError:
        print(f"Error: spaCy model {spacy_model_name} not found.")
        print(f"Please install it using: python -m spacy download {spacy_model_name}")
        return # Exit function if model is not found
        
    print("Initializing Google Translator...")
    translator = Translator()
    print("Translator initialized.")
        
            # 2. Data structures to store unique lemmas and their associated info
            # We use a dictionary to store unique lemmas and their *first encountered* POS.
            # This avoids re-processing for POS and ensures each lemma has one POS in the table.
    unique_lemmas_info = {} # Format: {lemma: pos_tag}
    if import_data_dict is None:
        import_data_dict = {}
    '''
    import excel file of current lemmas to limit the number of "new" lemmas pulled from article
    overwrite save of old excel doc with new that includes all old and new lemmas with translation
        '''
            # 3. First Pass: Read file, extract unique lemmas and their POS
    print(f"Processing file: {file_path}")
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return
        
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip() # Remove leading/trailing whitespace
                if not line: # Skip empty lines
                    continue
        
                try:
                    doc = posNLP(line)
                    for token in doc:
                                # Only consider tokens that are not punctuation or whitespace
                        if token.is_alpha:
                            lemma = token.lemma_.lower() # Convert to lowercase for consistent uniqueness
                                    # Store the lemma and its part of speech if it's new
                        if lemma not in import_data_dict:
                            unique_lemmas_info[lemma] = token.pos_
                      
                except Exception as e:
                    print(f"Warning: Could not process line {line_num}: '{line[:50]}...' - {e}")
                    continue # Continue to the next line
        
    except Exception as e:
        print(f"Error reading or processing file: {e}")
        return
        
    print(f"Found {len(unique_lemmas_info)} unique lemmas.")
        
            # 4. Second Pass: Translate unique lemmas and populate PrettyTable
    table = PrettyTable(["Lemma", "Part of Speech", "Translation"])
    table.align = "l" # Align columns to the left
        
    print("Translating lemmas and populating table...")
    for i, (lemma, part_of_speech) in enumerate(unique_lemmas_info.items()):
        try:
                    # Translate the lemma from the target_language to English
            translation_obj = await translator.translate(lemma, src=target_language, dest='en')
            translation = translation_obj.text
            table.add_row([lemma, part_of_speech, translation])
        except Exception as e:
            print(f"Warning: Could not translate '{lemma}' (POS: {part_of_speech}) - {e}")
            table.add_row([lemma, part_of_speech, "Translation Error"])
        
                # Optional: Print progress for large files
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1} lemmas...")
        
            # 5. Print the PrettyTable
    print("\n\n")
    table.title = "Processed Article Results"
    print(table.get_string(sortby = "Lemma"))
    
    user_selection = input("\nWould you like to save a dictionary of the found words and definitions to an existing file? \n\n Enter Y/N:  ")
    if user_selection.lower() == 'y':
        table.del_column("Part of Speech")
        path = input("\nInput the filepath of the dictionary. All words found will be added to the end. \n\n --> ")
        path = os.path.abspath(path)
        with open(path, 'a') as updateFile:
            updateFile.write(table.get_csv_string())
        if not os.path.exists(path):
            print(f"Error: File not found at '{path}' new dictionary saved as 'New Dictionary.csv'")
            with open('New Dictionary.csv', 'w', newline= '') as output:
                output.write(table.get_csv_string())
    elif user_selection.lower() == 'n':
        table.del_column("Part of Speech")
        with open('New Dictionary.csv', 'a', newline= '') as output:
            output.write(table.get_csv_string())
                    
    
    print('='*100)    
    print_welcome_message(text="\nAll Done!", font_name="big_money-ne")
    print('='*100) 
    
if __name__ == "__main__":
    print('='*100) 
    print_welcome_message()
    print('='*100) 
    
    import_data_dict = {} # in the case that no file is initially imported
    try:
        import_dict_or_none = import_existing_excel_file()
        if import_dict_or_none is not None:
            import_data_dict = import_dict_or_none
        print("Existing dictionary loaded successfully." if import_data_dict else "No existing dictionary imported.")
        
                  
    except Exception as e:
        print('Error: ', e)    
    
    target_lang_code, spacy_model_name = None, None # Initialize to None
    try:
        target_lang_code, spacy_model_name = target_language_selection()
        print(f"Selected language: {target_lang_code}, SpaCy model: {spacy_model_name}")
    except TypeError: # Catch if target_language_selection returns None (e.g., due to an exit condition that wasn't properly handled)
        print("Language selection failed or was cancelled.")
        exit() # Exit if language selection fails    
        
    target_url = input("\nPaste your URL for processing --> ")
    output_file = "webpage_content.txt"
    
    get_webpage_body_text(target_url, output_file)
    
    print("\nHTML Parsing script finished.")
    #target_language = target_language_selection()
    file_path = os.path.abspath(output_file)
    while True:  
        selection = input("\nAt this time, crop webpage_content.txt as needed. \nWhen complete, save and enter 1 to continue or 2 to quit ...")
        print('\n')
        if selection == '1':
            if target_lang_code and spacy_model_name:
                asyncio.run(process_text_for_lemmas(file_path, target_lang_code, spacy_model_name, import_data_dict))
            else:
                print("Ending program: Target Language or SpaCy model not selected")
            exit()
        elif selection == '2':
            print("Ending program")
            exit()
        else:
            print("Invalid input. Enter 1 to continue or 2 to quit")
            continue      
    

    
    print(tbl.get_string(sortby = "Lemma")) 