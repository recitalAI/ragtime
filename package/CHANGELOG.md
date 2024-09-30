# v0.0.44 - in progress
- fix bug occurring when a cell is empty in a template spreadsheet
- created the `doc` folder for documentation

# v0.0.43 - June 10th 2024
- fix bug in update_from_spreadsheet where last question was not saved
- added "Validation sets" folder
- fix "nb_missing" calculation error in EvalPrompterFR
- add a time between calls in TextGenerator

# v0.0.42 - June 7th 2024
- test new prompts for answer and facts
- small evolutions in HTML output
- boolean parameters in save_to_html (vs. rendering_params)
- change "hallus" to "extra"
- added a "n_first" parameter when creating an Expe to load only the n first questions (useful for quick testing)
- added the prompter name in LLMAnswer to keep track of the prompter which generated the prompt
- added the "name" property to Prompter
- renamed FactPrompterFR to FactPrompterJazz - each Prompter must have a different name and new prompters must not overwrite the previous ones to keep track of the experiments
- fixed bug in spreadsheet export (everything was converted to a string)
- renamed spreadsheet templates

# v0.0.41 - June 2nd 2024
- updated log

# v0.0.40 - June 1st 2024
- updated prompt in FactPrompterFR to make facts more atomic - seems to work better after a sanity check on Google NQ

# v0.0.39
- packages hierarchy updated
- prompters renamed
- pipeline in progress

# v0.0.38
- Fully functionnal pipeline described as a dictionary
- Ability to start and stop a test suite at any point

# v0.0.37
- Small fixes

# v0.0.36 
- Module renamed
- Removed deprecated prompter (see v0.0.33)

# v0.0.35
- PR in progress

# v0.0.34 - May 16th 2024
- bug fixed in question number display in logs (in `LiteLLM.complete`)

# v0.0.33 - May 15th 2024
- removed old Eval prompters `PptrTwoFactsEvalFR` and `PptrSimpleEvalFR` and old Eval generator `TwoFactsEvalGenerator`
- removed old Facts prompter `PptrSimpleFactsFR`
- renamed Answer prompter `PptrBaseAns` to `PptrAnsBase`, Facts prompter `PptrFactsFRv2` to `PptrFactsFR`, Evals prompter `PptrEvalFRv2` to `PptrEvalFR`
- added `save_to...` parameters in `gen_Answers` to ease output files generation
- added a `generate` function in `generators.py` to replace the `gen_Answers`, `gen_Facts` and `gen_Evals` function which where too similar
- added a default `max_tokens` parameters in the `LLM.complete`

# v0.0.32 - May 6th 2024
- generation in async
- logs more precise
- `basic_template.xlsx` updated

# v0.0.31
- added "update_from_spreadsheet"
- updates in config.py regarding column numbers
- renamed Answer Prompters
- minor updates in README.md

# v0.0.30
- tests (folder `tests`) now run `full_test.py` on Windows and Linux (WSL)
- the script `run_tests.py` run the tests on both OS

# v0.0.29
- Update min Python version to 3.9
- Added dependancies
- Uses `Union` typing instead of `|`
- Added a logging instruction in the `main.py` from `base_folder`
- Explicitly sets an extra argument for the Logger (not needed in Python v3.10)
- Added this CHANGELOG.md