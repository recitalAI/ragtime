from ragtime.llms import LLM, LiteLLM
from ragtime.prompters.prompter import Prompter
from ragtime.retrievers.retriever import Retriever
from ragtime.generators import AnsGenerator, FactGenerator, EvalGenerator
from ragtime.expe import StartFrom

from ragtime.base import RagtimeException
from ragtime.expe import Expe
from ragtime.config import (
    FOLDER_ANSWERS,
    FOLDER_FACTS,
    FOLDER_EVALS,
    DEFAULT_HTML_TEMPLATE,
    DEFAULT_SPREADSHEET_TEMPLATE,
)

from pathlib import Path
from typing import Union


def LLMs_from_names(names: list[str], prompter: Prompter) -> list[LLM]:
    """
    names(str or list[str]):
    a list of LLM names to be instantiated as LiteLLMs the names come from https://litellm.vercel.app/docs/providers
    """
    if not prompter:
        raise RagtimeException(
            "You have to provide a Prompter in order to create LLMs from their name."
        )
    if isinstance(names, str):
        names = [names]
    return [LiteLLM(name=name, prompter=prompter) for name in names]


def run_pipeline(
    configuration: dict, start_from: str = None, stop_after: str = None
) -> dict:
    # Check if there is a folder and file name for a starting point
    # TODO: refacto the error handling + check if the folder and the file exist
    input_folder: Union[Path, str] = configuration.get("folder_name", None)
    if not input_folder:
        raise Exception("You must provide a starting point folder")
    file_name: str = configuration.get("file_name", None)
    if not file_name:
        raise Exception("You must provide a starting point file name")

    # This table HO function are helper to instanciate the classe and methode call from a dictionary
    # TODO: break down this implementation to a PipelineConfiguration class
    #       to split the error handling from the config file and the implementation details
    #       of the pipeline implementation
    generator_table: dict[str, dict] = {
        "answers": {
            "generator": (
                lambda llms, retriever: AnsGenerator(
                    llms=llms, retriever=retriever
                ).generate
            ),
            "default_output_folder": FOLDER_ANSWERS,
        },
        "facts": {
            "generator": (lambda llms, retriever: FactGenerator(llms=llms).generate),
            "default_output_folder": FOLDER_FACTS,
        },
        "evals": {
            "generator": (lambda llms, retriever: EvalGenerator(llms=llms).generate),
            "default_output_folder": FOLDER_EVALS,
        },
    }

    # Check is the generator suite is present
    # TODO: refacto error handling
    if not configuration.get("generate", None):
        raise Exception("The pipeline must provide a generator suite")

    steps: list[str] = ["answers", "facts", "evals"]
    b = steps.index(start_from if start_from in steps else steps[0])
    e = steps.index(stop_after if stop_after in steps else steps[-1], b) + 1

    output_folder: Union[Path, str]
    # loop through the step of the pipeline in this specific order
    for step in steps[b:e]:
        # Skip if the step is not defined
        # NOTE: I think there is a better way to express this behavior
        step_conf: dict = configuration["generate"].get(step, None)
        if not step_conf:
            continue

        # Check if a list if LLMs is provided
        # NOTE: The AnswerGenerator is the only step that allow using multiple LLMs
        #       finding a way to better expres that.
        # TODO: error handling
        llms: list[LLM] = step_conf.get("llms", None)
        if not llms:
            raise Exception(
                f"All generator step need a list of LLM to run! Failed at step {step}"
            )

        # Get the generator
        # and if not provider get the default_output_folder associated with the current step
        generator = generator_table[step]
        output_folder = step_conf.get(
            "output_folder", generator["default_output_folder"]
        )

        # The Retriever should be closer the the AnswerGenerator
        # TODO: find an elegant way to present this relation
        retriever: Retriever = None
        if step == "answers":
            retriever = configuration.get("retriever", None)

        # Instanciate the Exporter and start the generation
        expe: Expe = Expe(json_path=input_folder / file_name)
        generator["generator"](llms, retriever)(
            expe,
            only_llms=step_conf.get("only_llms", None),
            save_every=step_conf.get("save_every", 0),
            start_from=step_conf.get("start_from", StartFrom.beginning),
            b_missing_only=step_conf.get("b_missing_only", False),
        )

        written_at: Path = expe.save_to_json(path=output_folder / file_name)

        # Check if export is provided
        exports_format = step_conf.get("export", None)
        if exports_format:
            exporter_table = {
                "html": (
                    lambda template_path: expe.save_to_html(
                        path=output_folder / file_name,
                        template_path=(template_path or DEFAULT_HTML_TEMPLATE),
                    )
                ),
                "spreadsheet": (
                    lambda template_path: expe.save_to_spreadsheet(
                        path=output_folder / file_name,
                        template_path=(template_path or DEFAULT_SPREADSHEET_TEMPLATE),
                    )
                ),
            }
            # Run the export with the parameter provided
            for fmt in ["html", "spreadsheet"]:
                fmt_parameters = exports_format.get(fmt, None)
                if fmt_parameters is None:
                    continue
                exporter_table[fmt](fmt_parameters.get("path", None))
        # Update the next input folder with the current output folder
        input_folder = written_at.parent
        file_name = written_at.name
