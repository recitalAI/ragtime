PROJECT_NAME:str = "LDS"

if PROJECT_NAME == "YOUR PROJECT":
    print('PLEASE ENTER YOUR PROJECT NAME IN THE FIRST LINE OF MAIN.PY !!')
    exit(1)

import ragtime
from ragtime import expe, generators
from ragtime.expe import QA, Chunks, Prompt, Question, WithLLMAnswer
import pandas as pd
from collections import defaultdict

# always start with init_project before importing ragtime.config values since they are updated
# with init_project and import works by value and not by reference, so values imported before
# calling init_project are not updated after the function call
ragtime.config.init_project(name=PROJECT_NAME, init_type="globals_only")
from ragtime.config import FOLDER_ANSWERS, FOLDER_QUESTIONS, logger

# Note: the logger can be used only *after* ragtime.config.init_project
logger.debug(f'*** PROJECT "{PROJECT_NAME}" STARTS')

# If you're using Windows, make your environment variables for LLM providers accessible with the following instruction
# ragtime.config.init_win_env(['OPENAI_API_KEY', 'ALEPHALPHA_API_KEY', 'MISTRAL_API_KEY'])

#####
# TODO : terminer lecture de l'Excel et construction de l'Expe avec Questions et Faits
# Convert EXcel sheet into Questions and Facts and stores the file
def read_XL_facts():    
    # Paramètres
    file_path = ""
    sheet_name = "MonOnglet"  # nom de l'onglet à lire

    # Charger l'onglet
    df = pd.read_excel(FOLDER_QUESTIONS / "Questions_et_Faits.xlsx", sheet_name="Droit de la consommation et e-c", skiprows=1)

    # Supposons :
    # Colonne A = question
    # Colonne B = fait
    question_col = df.columns[0]
    fact_col = df.columns[1]

    questions_faits = defaultdict(list)

    current_question = None

    for _, row in df.iterrows():
        question = row[question_col]
        fact = row[fact_col]

        # Nouvelle question
        if pd.notna(question) and str(question).strip():
            current_question = str(question).strip()

        # Ajouter le fait associé à la question courante
        if current_question and pd.notna(fact) and str(fact).strip():
            questions_faits[current_question].append(str(fact).strip())

    questions_faits = dict(questions_faits)