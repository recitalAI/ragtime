from enum import IntEnum
from typing import Literal
import ragtime
import logging
import logging.config
from pathlib import Path
import shutil
import sys, os
from importlib import resources

if os.name == "nt":
    from py_setenv import setenv

#################################
## CONSTANTS

UNKNOWN_LLM: str = "unknown LLM (manual ?)"
#################################

# # # FOLDERS
QUESTIONS_FOLDER_NAME: str = "01. Questions"
ANSWERS_FOLDER_NAME: str = "02. Answers"
FACTS_FOLDER_NAME: str = "03. Facts"
EVALS_FOLDER_NAME: str = "04. Evals"
VALIDATION_SETS_FOLDER_NAME:str = "05. Validation sets"
DATASETS_FOLDER_NAME : str = "datasets"
DOCUMENTS_FOLDER_NAME : str = "documents"
ROOT_FOLDER: Path = ROOT_FOLDER if "ROOT_FOLDER" in globals() else None
FOLDER_EXPE: Path = FOLDER_EXPE if "FOLDER_EXPE" in globals() else None
FOLDER_QUESTIONS: Path = FOLDER_QUESTIONS if "FOLDER_QUESTIONS" in globals() else None
FOLDER_ANSWERS: Path = FOLDER_ANSWERS if "FOLDER_ANSWERS" in globals() else None
FOLDER_FACTS: Path = FOLDER_FACTS if "FOLDER_FACTS" in globals() else None
FOLDER_EVALS: Path = FOLDER_EVALS if "FOLDER_EVALS" in globals() else None
FOLDER_TEMPLATES: Path = FOLDER_TEMPLATES if "FOLDER_TEMPLATES" in globals() else None
FOLDER_SST_TEMPLATES: Path = (
    FOLDER_SST_TEMPLATES if "FOLDER_SST_TEMPLATES" in globals() else None
)
FOLDER_HTML_TEMPLATES: Path = (
    FOLDER_HTML_TEMPLATES if "FOLDER_HTML_TEMPLATES" in globals() else None
)
# # # HTML
DEFAULT_HTML_RENDERING: dict[str, bool] = (
    DEFAULT_HTML_RENDERING if "DEFAULT_HTML_RENDERING" in globals() else None
)
DEFAULT_HTML_TEMPLATE: Path = (
    DEFAULT_HTML_TEMPLATE if "DEFAULT_HTML_TEMPLATE" in globals() else None
)
# # # Spreadheet
DEFAULT_SPREADSHEET_TEMPLATE: Path = (
    DEFAULT_SPREADSHEET_TEMPLATE
    if "DEFAULT_SPREADSHEET_TEMPLATE" in globals()
    else None
)
DEFAULT_WORKSHEET: str = DEFAULT_WORKSHEET if "DEFAULT_WORKSHEET" in globals() else None
DEFAULT_HEADER_SIZE: int = (
    DEFAULT_HEADER_SIZE if "DEFAULT_HEADER_SIZE" in globals() else None
)
DEFAULT_QUESTION_COL: int = (
    DEFAULT_QUESTION_COL if "DEFAULT_QUESTION_COL" in globals() else None
)
DEFAULT_FACTS_COL: int = DEFAULT_FACTS_COL if "DEFAULT_FACTS_COL" in globals() else None
DEFAULT_ANSWERS_COL: int = (
    DEFAULT_ANSWERS_COL if "DEFAULT_ANSWERS_COL" in globals() else None
)
DEFAULT_HUMAN_EVAL_COL: int = (
    DEFAULT_HUMAN_EVAL_COL if "DEFAULT_HUMAN_EVAL_COL" in globals() else None
)
# # # LLMs
DEFAULT_LITELLM_RETRIES: int = (
    DEFAULT_LITELLM_RETRIES if "DEFAULT_LITELLM_RETRIES" in globals() else None
)
DEFAULT_LITELLM_TEMP: int = (
    DEFAULT_LITELLM_TEMP if "DEFAULT_LITELLM_TEMP" in globals() else None
)
DEFAULT_MAX_TOKENS: int = (
    DEFAULT_MAX_TOKENS if "DEFAULT_MAX_TOKENS" in globals() else None
)


# Logging - class to add msg
class RagtimeLogger(logging.LoggerAdapter):
    prefix: str = ""

    def process(self, msg, kwargs):
        return f'{self.prefix + " " if self.prefix else ""}{msg}', kwargs


logger: RagtimeLogger = logger if "logger" in globals() else None


def init(root_folder: Path):
    """Init global variables for folder locations, template parameters and logger"""
    if isinstance(root_folder, str):
        root_folder = Path(root_folder)
    # FOLDERS
    global ROOT_FOLDER, FOLDER_EXPE, FOLDER_QUESTIONS, FOLDER_ANSWERS, FOLDER_FACTS, FOLDER_EVALS, FOLDER_TEMPLATES, FOLDER_SST_TEMPLATES, FOLDER_HTML_TEMPLATES
    # # # HTML
    global DEFAULT_HTML_RENDERING, DEFAULT_HTML_TEMPLATE
    # # # Spreadheet
    global DEFAULT_SPREADSHEET_TEMPLATE, DEFAULT_WORKSHEET, DEFAULT_HEADER_SIZE, DEFAULT_QUESTION_COL, DEFAULT_FACTS_COL
    global DEFAULT_ANSWERS_COL, DEFAULT_HUMAN_EVAL_COL
    # # # LLMs
    global DEFAULT_LITELLM_RETRIES, DEFAULT_LITELLM_TEMP, DEFAULT_MAX_TOKENS
    # Logger
    global logger

    # Folders
    ROOT_FOLDER = root_folder
    FOLDER_EXPE = root_folder / "expe"
    FOLDER_QUESTIONS = FOLDER_EXPE / QUESTIONS_FOLDER_NAME
    FOLDER_ANSWERS = FOLDER_EXPE / ANSWERS_FOLDER_NAME
    FOLDER_FACTS = FOLDER_EXPE / FACTS_FOLDER_NAME
    FOLDER_EVALS = FOLDER_EXPE / EVALS_FOLDER_NAME
    FOLDER_VALIDATION_SETS = FOLDER_EXPE / VALIDATION_SETS_FOLDER_NAME
    FOLDER_TEMPLATES = root_folder / "res"
    FOLDER_SST_TEMPLATES = FOLDER_TEMPLATES / "spreadsheet_templates"
    FOLDER_HTML_TEMPLATES = FOLDER_TEMPLATES / "html_templates"
    # # # HTML
    DEFAULT_HTML_RENDERING = {
        "show_answers": True,
        "show_chunks": True,
        "show_facts": True,
        "show_evals": True,
    }
    DEFAULT_HTML_TEMPLATE = FOLDER_HTML_TEMPLATES / "basic_template.jinja"
    # # # Spreadheet
    DEFAULT_SPREADSHEET_TEMPLATE = FOLDER_SST_TEMPLATES / "with_chunks.xlsx"
    DEFAULT_WORKSHEET = "Expe"
    DEFAULT_HEADER_SIZE = 2
    DEFAULT_QUESTION_COL = 2
    DEFAULT_FACTS_COL = 4
    DEFAULT_ANSWERS_COL = 11
    DEFAULT_HUMAN_EVAL_COL = 24
    # # # LLMs
    DEFAULT_LITELLM_RETRIES = 3
    DEFAULT_LITELLM_TEMP = 0
    DEFAULT_MAX_TOKENS = 1000  # empirically noticed the biggest answers are 4000 characters long - and 1 token is between 4 and 5 chars - keep the largest value, i.e. 4 chars per token

    ####################
    # LOGGING
    # You can choose the file where the logs are written in "log_conf" dict, key "handlers"/"file"/"filename" - default is "logs/logs.txt"
    # You can otherwise change everything you need as detailed in https://docs.python.org/3/library/logging.config.html

    log_conf: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                # "format": "[%(asctime)s %(levelname)-4s %(filename)s %(funcName)s l.%(lineno)s] %(message)s"
                "format": "[%(asctime)s] %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "standard",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": f"{root_folder}/logs/logs.txt",
                "maxBytes": 1000000,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "ragtime_logger": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": False,
            }
        },
    }

    # Logging - create the logs in the folder of the calling script (not ragtime)
    log_path: Path = root_folder / "logs"
    if not log_path.exists():
        log_path.mkdir()
    logging.config.dictConfig(log_conf)
    logger = RagtimeLogger(logging.getLogger("ragtime_logger"), extra=None)
    # below is simply a hack to turn off unexpected LiteLLM logging with Ragtime logging set to INFO or DEBUG
    logging.getLogger().setLevel(logging.WARNING)

def init_project(
    name: str,
    init_type: Literal[
        "globals_only", "copy_base_files", "delete_if_exists"
    ] = "globals_only",
    dest_path: Path = None,
):
    """Initiates a project : copy base files and and set global variables
    Args:
    - init_type
        "globals_only" = 0 # do not touch the files, only initiates the global variables (logger, folder variables...)
        "copy_base_files" = 1 # globals_only + copy files to create base_folder, raise an exception if already exists
        "delete_if_exists" = 2 # copy_base_files + remove folder if existing before copying base_folder
    """
    if not dest_path:
        if init_type == "globals_only":
            dest_path = Path(sys.argv[0]).parent
        else:
            dest_path = Path(sys.argv[0]).parent / name
    if init_type != "globals_only":
        src_path: Path = Path(resources.files("ragtime")) / "base_folder"
        if init_type == "delete_if_exists" and dest_path.exists():
            shutil.rmtree(dest_path)
        shutil.copytree(src_path, dest_path)
        # Add empty folders
        for sub_folder in [
            QUESTIONS_FOLDER_NAME,
            ANSWERS_FOLDER_NAME,
            FACTS_FOLDER_NAME,
            EVALS_FOLDER_NAME,
            VALIDATION_SETS_FOLDER_NAME,
        ]:
            if not Path(dest_path / "expe" / sub_folder).exists():
                Path(dest_path / "expe" / sub_folder).mkdir()

    init(dest_path)


def init_win_env(env_vars: list[str]):
    """Used to init environment variables in Windows"""
    if os.name == "nt":  # only if os is Windows
        for env_var in env_vars:
            api_key: str = setenv(env_var, user=True, suppress_echo=True)
            if api_key:
                os.environ[env_var] = api_key


# Default init values if first import (i.e. logger is None)
if not logger:
    root_folder: Path = Path(sys.argv[0]).parent
    os.chdir(root_folder)
    init(root_folder=root_folder)

import litellm

litellm.telemetry = False
litellm.set_verbose = False  # used for debuging purpose
