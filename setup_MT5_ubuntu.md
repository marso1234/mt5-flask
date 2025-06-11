# Update Packages
`sudo apt update -y`<br>
`sudo apt upgrade -y`<br>
# Install Wine
`sudo apt install wine64`<br>
`cd ~/Desktop`<br>
# Download MT5 and Python
`wget https://www.python.org/ftp/python/3.8.0/python-3.8.0-amd64.exe --no-check-certificate`<br>
`wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe --no-check-certificate`<br>
# Install MT5
`wine uninstaller` -> select install and then select mt5setup.exe<br>
# Install Python
`wine cmd`<br>
`cd /folder_where_python3.8_setup.exe`<br>
`python-3.8.0-amd64.exe`<br>
`c:`<br>
`cd windows`<br>
`copy py.exe python.exe`<br>
# Install MT5, Flask Python packages
`python -m pip install pip --upgrade`<br>
`exit`<br>
`wine cmd`<br>
`pip install MetaTrader5 flask`
