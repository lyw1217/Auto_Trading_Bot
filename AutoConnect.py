from pywinauto import application
import time
import os

os.system('taskkill /IM coStarter* /F /T')
os.system('taskkill /IM CpStart* /F /T')
os.system('wmic process where "name like \'%coStarter%\'" call terminate')
os.system('wmic process where "name like \'%CpStart%\'" call terminate')
time.sleep(5)        

with open('./file/start_str.txt', 'r') as file:
    start_str = file.read()
    app = application.Application()
    app.start(start_str)
time.sleep(60)