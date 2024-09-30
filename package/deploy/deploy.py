import os
import shutil
import time

shutil.rmtree("dist")
os.mkdir("dist")
os.system("python -m build")
os.system("twine upload dist/*")
# time.sleep(10)
# os.system('pip install ragtime --upgrade')