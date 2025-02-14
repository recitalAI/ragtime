PROJECT_NAME:str = "Albert"

import ragtime
import shutil

ragtime.config.init_project(name=PROJECT_NAME, init_type="copy_base_files")
# When you use ragtime a logs folder is created - in this case it is useless so it can be removed so as
# to create a new project only
shutil.rmtree('logs')