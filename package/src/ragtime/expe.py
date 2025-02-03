from ragtime.base import (
    RagtimeBase,
    RagtimeText,
    RagtimeList,
    RagtimeException,
)

from ragtime.config import (
    DEFAULT_FACTS_COL,
    DEFAULT_HUMAN_EVAL_COL,
    DEFAULT_HEADER_SIZE,
    DEFAULT_HUMAN_EVAL_COL,
    DEFAULT_ANSWERS_COL,
    DEFAULT_QUESTION_COL,
    DEFAULT_SPREADSHEET_TEMPLATE,
    DEFAULT_WORKSHEET,
    logger,
    DEFAULT_HTML_RENDERING,
    DEFAULT_HTML_TEMPLATE,
)

from collections import defaultdict

from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from copy import copy
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from jinja2 import Environment, FileSystemLoader
from tabulate import tabulate
from pathlib import Path
import shutil
import json
import re

from enum import Enum, IntEnum
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar, Union
from enum import IntEnum


class Prompt(RagtimeBase):
    user: Optional[str] = ""
    system: Optional[str] = ""
    prompter:str = ""


class LLMAnswer(RagtimeText):
    prompt: Optional[Prompt] = None
    name: Optional[str] = None
    full_name: Optional[str] = None
    timestamp: datetime = Optional[datetime] 
    duration: Optional[float] = None  
    cost: Optional[float] = None
    chunks : Optional[list] = []

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%a, %d %b %Y %H:%M:%S GMT')
            except ValueError:
                pass
        return value

class WithLLMAnswer(BaseModel):
    llm_answer: Optional[LLMAnswer] = None

class Question(RagtimeText, WithLLMAnswer):
    pass


class Questions(RagtimeList[Question]):
    pass


class Eval(RagtimeText, WithLLMAnswer):
    """At first an Eval is made by a human, and then automatically generated from an LLM Answer"""

    human: Optional[float] = None
    auto: Optional[float] = None


class Answer(RagtimeText, WithLLMAnswer):
    eval: Optional[Eval] = Eval()


class Answers(RagtimeList[Answer]):
    pass


class Fact(RagtimeText):
    """A single fact contains only text - all the LLM data are in the Facts object
    since every single Fact is created with a single LLM generation"""

    pass


class Facts(RagtimeList[Fact], WithLLMAnswer):
    pass


class TypesWithLLMAnswer(Enum):
    answer = Answer
    facts = Facts
    eval = Eval


class Chunk(RagtimeText):
    pass


class Chunks(RagtimeList[Chunk]):
    pass


class QA(RagtimeBase):
    question: Question = Question()
    facts: Optional[Facts] = Facts()
    chunks: Optional[Chunks] = Chunks()
    answers: Optional[Answers] = Answers()

    def get_attr(self, path: str) -> list[Any]:
        """Returns the value within a QA object based on its path expressed as a string
        Useful for spreadhseets export - returns None if path is not found"""
        result: Any = self
        b_return_None: bool = False
        for a in path.split("."):
            if "[" in a:
                index: Union[str, int] = a[a.find("[") + 1 : a.rfind("]")]
                a_wo_index: str = a[: a.find("[")]

                if index.isdecimal():
                    index = int(index)  # if index is an int (list index), convert it
                elif index == "i":  # multi row
                    result = [
                        self.get_attr(path.replace("[i]", f"[{i}]"))
                        for i in range(len(getattr(result, a_wo_index)))
                    ]
                    return result
                else:  # dict (key not decimal)
                    index = index.replace('"', "").replace("'", "")  # if it is a string (dict index), remove quotes

                try:
                    result = getattr(result, a_wo_index)[index]
                except:
                    b_return_None = True
            else:
                try:
                    result = getattr(result, a)
                except:
                    b_return_None = True
            if b_return_None:
                return None

        return result


class UpdateTypes(IntEnum):
    human_eval = 0
    facts = 1


class StartFrom(IntEnum):
    beginning = 0
    chunks = 1
    prompt = 2
    llm = 3
    post_process = 4


class Expe(RagtimeList[QA]):
    meta: Optional[dict] = {}
    json_path: Path = Field(None, exclude=True)

    def __init__(self, json_path: Path = None, n_first:int=0):
        """Expe can be init with only the n_first items from the JSON file
        Useful to test something on a small subset of questions at first
        n_first = 0 to load eveything"""
        super().__init__()
        if json_path:
            self.json_path = json_path
            self.load_from_json(path=json_path, n_first=n_first)

    def stats(self) -> dict:
        """Returns stats about the expe : nb models, nb questions, nb facts, nb answers, nb human eval, nb auto eval"""
        res: dict = {}
        res["questions"] = len([qa for qa in self if qa and qa.question and qa.question.text])
        res["chunks"] = len([c for qa in self for c in qa.chunks if c])
        res["facts"] = len([f for qa in self for f in qa.facts if f])
        res["models"] = len(self[0].answers)
        res["answers"] = len([a for qa in self for a in qa.answers if a and a.text])
        res["human eval"] = len(
            [a for qa in self for a in qa.answers if a and a.eval and a.eval.human]
        )
        res["auto eval"] = len(
            [a for qa in self for a in qa.answers if a and a.eval and a.eval.auto]
        )
        return res

    def get_name(self) -> str:
        """Returns the name of the Expe based on the number of questions, answers..."""
        date_to_time_format: str = "%Y-%m-%d_%Hh%M,%S"
        stats: dict = self.stats()
        name: str = (
            f'{stats["questions"]}Q_{stats["chunks"]}C_{stats["facts"]}F_{stats["models"]}M_{stats["answers"]}A_{stats["human eval"]}HE_{stats["auto eval"]}AE_{datetime.now().strftime(date_to_time_format)}'
        )
        return name

    def _file_check_before_writing(
        self,
        path: Path = None,
        b_overwrite: bool = False,
        b_add_suffix: bool = True,
        force_ext: str = None,
    ) -> Path:
        if path and path.is_dir():
            if self.json_path:
                path = path / self.json_path.stem
            else:
                raise RagtimeException('No JSON file attached to this Expe and you provided only a folder Path')
        if not path:
            if self.json_path:
                path = Path(self.json_path.parent) / self.json_path.stem
            else:
                raise RagtimeException(f"Cannot save to JSON since no json_path is stored in expe and no path has been provided in argument.")

        # Make sure at least 1 QA is here
        if len(self) == 0:
            raise Exception("The Expe object you're trying to write is empty! Please add at least one QA")

        # Check and prepare the destination file path
        if not (path):
            raise Exception("No file defined - please specify a file name to save the Expe into")

        # If the provided path is a string, convert it to a Path
        result_path = Path(path) if isinstance(path, str) else path

        # If a suffix is to be added, add it
        if b_add_suffix:
            file_no_ext: str = result_path.stem
            # genrates the new suffix like --5M_50Q_141F_50A_38HE
            sep: str = "--"
            new_suf: str = self.get_name()
            if file_no_ext.find(sep) != -1:  # if already a suffix, replace it
                old_suf: str = file_no_ext[file_no_ext.find(sep) + len(sep) :]
                file_no_ext = file_no_ext.replace(old_suf, new_suf)
            else:
                file_no_ext = f"{file_no_ext}{sep}{new_suf}"
            str_name: str = f"{file_no_ext}{result_path.suffix}"
            result_path = result_path.parent / Path(str_name)

        # Force ext
        if force_ext:
            if result_path.suffix:  # if already an extension, replace it
                result_path = Path(str(result_path).replace(result_path.suffix, force_ext))
            else:  # if no extension, just add it
                result_path = Path(f"{result_path}{force_ext}")

        # If path exists and overwrite not allowed, raise an Exception
        if result_path.is_file() and not b_overwrite:
            raise FileExistsError(f'"{result_path}" already exists! Set b_overwrite=True to allow overwriting.')

        return result_path

    def load_from_json(self, path: Path, n_first:int=0):
        with open(path, mode="r", encoding="utf-8") as file:
            data: list = json.load(file)
            qa_list: dict = data
            if "meta" in data:
                self.meta = data["meta"]
                qa_list = data["items"]
            n_first = n_first if n_first else len(qa_list)
            for json_qa in qa_list[:n_first]:
                qa: QA = QA(**json_qa)
                self.append(qa)

    def filter_answer(self, llm_facts_name: str):
        """
        Filters the current Expe object to include only the QA pairs with answers from the specified LLM.
        """
        for qa in self:
            filtered_answers = [
                a
                for a in qa.answers
                if a.llm_answer and a.llm_answer.name == llm_facts_name
            ]
            qa.answers = Answers(items=filtered_answers)

    # TODO: Cannot implement this function due to circular imports issue (need objects from generators.py objects and generators.py needs
    # expe.py objects too) - if someone finds a way, that would be nice since it would allow to easily chain Answer, Facts and Eval generation
    # def gen_Eval(self, folder_out:Path, prompter:Prompter, llm_names:list[str],
    #             start_from:StartFrom=StartFrom.beginning, b_missing_only:bool = False, only_llms:list[str] = None, save_every:int=0):
    #     eval_gen:EvalGenerator = EvalGenerator(llm_names=llm_names, prompter=prompter)
    #     eval_gen.generate(self, start_from=start_from,  b_missing_only=b_missing_only, only_llms=only_llms, save_every=save_every)
    #     self.save_to_json(path=folder_out / self.json_file)

    def update_from_spreadsheet(
        self,
        path: Path,
        update_type: UpdateTypes,
        data_col: int = None,
        question_col: int = DEFAULT_QUESTION_COL - 1,
        answer_col: int = DEFAULT_ANSWERS_COL - 1,
        sheet_name: str = DEFAULT_WORKSHEET,
        header_size: int = DEFAULT_HEADER_SIZE,
    ):
        """Updates data from a spreadsheet, e.g. human evaluation or facts
        Args:
        - data_col (int): indicates the column number (starts at 0) from where the data will be imported in the spreadsheet
        if None (default), default column values are used, i.e. DEFAULT_FACTS_COL if update_type==Facts and
        DEFAULT_HUMAN_EVAL_COL if update_type==human_eval
        - update_type (UpdateTypes): can be "human_eval" or "facts"
        - question_col (int): indicates the column number (starts at 0) where the questions are - default: DEFAULT_QUESTION_COL-1 (0 based)
        - answer_col (in): used if update_type==human_eval, since the eval entered in the spreadsheet has to be matched with a specific answer
        """

        def starts_with_num(fact: str) -> bool:
            result: bool = False
            if "." in fact:
                try:
                    dummy: int = int(fact[: fact.find(".")])
                    result = True
                except (TypeError, ValueError):
                    pass
            return result

        wb: Workbook = load_workbook(path)
        ws: Worksheet = wb[sheet_name]
        cur_qa: QA = None
        if not data_col:
            data_cols: dict = {
                UpdateTypes.facts: DEFAULT_FACTS_COL,
                UpdateTypes.human_eval: DEFAULT_HUMAN_EVAL_COL,
            }
            data_col = data_cols[update_type] - 1

        new_facts: Facts = (
            Facts()
        )  # the new facts to replace the old ones in the current QA

        # For each row in the worksheet
        for i, row in enumerate(ws.iter_rows(min_row=header_size + 1), start=1):
            if row[question_col].value:  # a question is in the current row, so a new question starts
                if cur_qa:  # not first question
                    cur_qa.facts = new_facts
                cur_qa = next((qa for qa in self if qa.question.text.lower() == row[question_col].value.lower()), None)  # get the corresponding QA in the Expe
                new_facts: Facts = Facts()

            if cur_qa:  # QA and question in the worksheet is made
                data_in_ws = row[data_col].value
                if data_in_ws:
                    if update_type == UpdateTypes.facts:  # Update FACTS
                        if not starts_with_num(data_in_ws):  # if the fact in the ws does not start with a number, add it
                            data_in_ws = f"{len(new_facts) + 1}. {data_in_ws}"
                        new_facts.append(Fact(text=data_in_ws))
                    elif update_type == UpdateTypes.human_eval:  # Update HUMAN EVAL
                        answer_text: str = row[answer_col].value
                        cur_ans: Answer = next((a for a in cur_qa.answers if a.text == answer_text), None)
                        if cur_ans:  # corresponding Answer has been found
                            try:
                                human_eval: int = int(data_in_ws)
                                cur_ans.eval.human = human_eval
                            except (TypeError, ValueError):
                                logger.warn(f'Human eval should be a value between 0 and 1 - cannot use "{data_in_ws}" as found in line {i}')
                        else:
                            logger.warn(f'Cannot find Answer corresponding with the human eval "{data_in_ws}" - Answer should contain the text "{answer_text}"')
        
        # Save facts for the last question
        if cur_qa and update_type == UpdateTypes.facts:
            cur_qa.facts = new_facts



    def save_temp(self, name: str = "TEMP_"):
        """Save the expe as is as a temporary backup. Useful to save the work already done
        when an Exception occurs or if you want to create intermediate backups while computing.
        """
        if self.json_path:
            file_name: str = f"{name}{self.json_path.stem}"
            file_path: str = self.json_path.parent
        else:
            file_name: str = f"{name}.json"
            file_path: str = ""
        self.save_to_json(
            path=Path(file_path) / Path(file_name), b_overwrite=True, b_add_suffix=True
        )

    def save_to_json(self, path: Path = None, b_overwrite: bool = False, b_add_suffix: bool = True) -> Path:
        """
        Saves Expe to JSON - can generate a suffix for the filename
        Returns the Path of the file actually saved
        """
        path: Path = self._file_check_before_writing(path, b_overwrite=b_overwrite, b_add_suffix=b_add_suffix, force_ext=".json")
        with open(path, mode="w", encoding="utf-8") as file:
            file.write(self.model_dump_json(indent=2))
        self.json_path = path
        logger.info(f"Expe saved as JSON to {path}")
        return path

    def save_to_html(
        self,
        path: Path = None,
        b_overwrite: bool = False,
        b_add_suffix: bool = True,
        # render_params: dict[str, bool] = DEFAULT_HTML_RENDERING,
        b_show_answers:bool = True,
        b_show_chunks:bool = True,
        b_show_facts:bool = True,
        b_show_evals:bool = True,        
        template_path: Path = DEFAULT_HTML_TEMPLATE,
    ):
        """
        Saves Expe to an HTML file from a Jinja template - can generate a suffix for the filename
        Returns the Path of the file actually saved
        """
        path: Path = self._file_check_before_writing(path, b_overwrite=b_overwrite, b_add_suffix=b_add_suffix, force_ext=".html")
        environment = Environment(loader=FileSystemLoader(searchpath=template_path.parent, encoding="utf-8")        )
        render_params:dict[str, bool] = {
            "show_answers": b_show_answers,
            "show_chunks": b_show_chunks,
            "show_facts": b_show_facts,
            "show_evals": b_show_evals,
        }
        template = environment.get_template(template_path.name)
        context = {
            "expe": self,
            **render_params,
            "report_name": self.get_name(),
            "sub": (lambda pattern, repl, s: re.sub(pattern, repl, s)),
        }
        with open(path, mode="w", encoding="utf-8") as file:
            file.write(template.render(context))
        logger.info(f"Expe saved as HTML to {path}")
        return path

    def save_to_spreadsheet(
        self,
        path: Path = None,
        template_path: Path = DEFAULT_SPREADSHEET_TEMPLATE,
        header_size: int = DEFAULT_HEADER_SIZE,
        sheet_name: str = DEFAULT_WORKSHEET,
        b_overwrite: bool = False,
        b_add_suffix: bool = True,
    ):
        """Saves Expe to a spreadsheet - can generate a suffix for the filename
        Returns the Path of the file actually saved"""
        path: Path = self._file_check_before_writing(path, b_overwrite=b_overwrite, b_add_suffix=b_add_suffix, force_ext=".xlsx")

        # Prepare the result file
        # Copy template
        shutil.copy(template_path, path)
        wb: Workbook = load_workbook(path)
        wb.iso_dates = True

        # Create worksheet
        ws: Worksheet = wb[sheet_name]

        # Retrieve sst configuration from original file
        # ws_conf is a list of str, each element describes the path of the data to be added in the current row
        ws_conf: list[str] = [cell.value for cell in ws[header_size + 1]]

        # Write the values at specific rows - they are defined in second row, below the one describing the value to insert
        for cell in ws[header_size + 2]:  # read the row just after the conf row - it contains configuration for specific rows
            # if a value is present, analyse it - it should contain a "row" indication e.g. "answers[0].full_name, row=1"
            if cell.value:
                if cell.value == "#":
                    continue  # special token # used to indicate question number
                val: str = cell.value
                row: int = int(val[val.find("row=") + len("row=") :])
                if row < 1:
                    raise RagtimeException(
                        f'The row value "row={row}" specified in cell {cell.coordinate} is invalid and must be greater than 0'
                    )
                # write the value since it does not need to be done for each row
                p: str = val[: val.find(",")]
                # get the first non empty value in the required column
                val = next((qa.get_attr(p) for qa in self if qa.get_attr(p)), "")
                ws.cell(row=row, column=cell.column, value=val)

        qa: QA
        row: int = header_size + 1
        col_with_formulas: dict[int, str] = {
            c: ws.cell(column=c, row=row).value
            for c in range(1, ws.max_column)
            if ws.cell(column=c, row=row).value
            and str(ws.cell(column=c, row=row).value)[0] == "="
        }
        for num_q, qa in enumerate(self, start=1):  # write each row in expe
            next_row: int = 0
            for col, p in enumerate(ws_conf, start=1):
                if p == "#":  # special token # used to indicate question number
                    val = [num_q]
                elif p[0] == "=":  # if a formula is here, write it as is in the formula field
                    continue
                else:  # if it is a path to get a value in QA, get it
                    # Get value in the QA object
                    val = qa.get_attr(p)
                    if val is None or val == []:
                        val = [""]  # write a blank if nothing is found
                if not isinstance(val, list):
                    val = [val]

                # Write the value(s)
                for offset, v in enumerate(val):
                    # Do standard conversions to string
                    if isinstance(v, list):
                        v = str(v)
                    elif isinstance(v, datetime):
                        v = v.strftime("%d/%m/%Y %H:%M:%S")
                    elif isinstance(v, str):
                        # Remove illegal characters before writing the value
                        v = ILLEGAL_CHARACTERS_RE.sub("", str(v))
                    # Write value
                    ws.cell(row=row + offset, column=col).value = v
                    # From second row copy cell style from the one up
                    if row + offset > header_size + 1:
                        ws.cell(row=row + offset, column=col)._style = copy(ws.cell(row=header_size + 1, column=col)._style)

                next_row = max(next_row, row + offset + 1)
            row = next_row

        # extend the formulas
        for row in range(header_size + 1, ws.max_row):
            for col, formula in col_with_formulas.items():
                # simply adjust the row number in the formula
                cell_refs: set = set(re.findall(r"[A-Z]+[0-9]+", formula))
                for cell_ref in cell_refs:
                    new_cell_ref: str = cell_ref.replace(str(header_size + 1), str(row))
                    formula = formula.replace(cell_ref, new_cell_ref)
                ws.cell(row=row, column=col, value=formula)

        # save spreadsheet
        wb.save(path)
        logger.info(f"Expe saved as Spreadsheet to {path}")
        return path


def analyse_expe_folder(path: Path):
    if not path.is_dir():
        raise Exception(f'"{path}" is not a folder - please provide one')
    print(f'In "{path}":')
    res: defaultdict = defaultdict(list)
    for f in [f for f in path.iterdir() if f.is_file() and f.suffix == ".json"]:
        exp: Expe = Expe(json_path=f)
        res["File"].append(f.name)
        for k, v in exp.stats():
            res[k].append(v)

    print(tabulate(res, headers="keys"))


# DEPRECATED
# def export_to_html(json_path:Path, render_params:dict[str,bool]=DEFAULT_HTML_RENDERING,
#                     template_path:Path=DEFAULT_HTML_TEMPLATE):
#  expe:Expe = Expe(json_path=json_path)
#  expe.save_to_html(path=json_path, render_params=render_params, template_path=template_path, b_add_suffix=True)
#
# def export_to_spreadsheet(json_path:Path, template_path:Path=DEFAULT_SPREADSHEET_TEMPLATE,
#                            header_size:int=DEFAULT_HEADER_SIZE, sheet_name:str = DEFAULT_WORKSHEET,):
#  expe:Expe = Expe(json_path=json_path)
#  expe.save_to_spreadsheet(path=json_path, template_path=template_path, header_size=header_size, sheet_name=sheet_name, b_add_suffix=True)
