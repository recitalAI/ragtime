Thanks for being here! Glad you wish to contribute!

This repo contains the main Ragtime🎹 package. You can contribute by proposing new features, ideas, optimizations and documentation :)

# Backlog
Here are the projects we currently have in mind:
- `Test [TEST]`: user only has to provide documents, and question are automatically generated, their answer are automatically validated, facts are automatically generated and finally an evaluation is returned
- `User interface [UI]`: add a user interface on top of the JSON files...big stuff!
- `Fine tuning models [FTM]`: fine-tune models to generate questions, answers, facts and evaluations so that the package does not have to connect to an API
- `LLM Ops [OPS]`: add the required features to use Ragtime in a LLM Ops workflow
- `Documentation [Doc]`: add a wiki in GitHub
- `CI/CD [CICD]`: add a CI/CD pipeline in `ragtime-package`

# Testing the PR
Before releasing you can test your PR with `full_test.py` in `tests`.

You can then test the package with Linux and Windows if you're running with Windows computer with the `run_tests.py` script.
Just set the variable `script_dir` to the local `tests` folder on your computer and tun the script. Is will run `full_test.py` in your Windows environment and then run it on your Linux environment (assuming you already have installed WSL2 on your Windows).