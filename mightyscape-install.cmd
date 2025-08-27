@echo off
setlocal ENABLEDELAYEDEXPANSION

SET INKSCAPE_USER_DIR=%AppData%\inkscape
SET TGT=%INKSCAPE_USER_DIR%\extensions
SET VENV=venv
SET GIT_SERVER=github.com
SET GIT_MAINTAINER=eridur-de
SET GIT_REPO=mightyscape-1.2
SET PYTHON_VERSION=3.13.5

COLOR 03

:: Start powershell as privileged admin
if not "%1"=="am_admin" (
powershell -Command "Start-Process -Verb RunAs -WindowStyle Maximized -FilePath '%0' -ArgumentList 'am_admin',%CD%" -Wait
exit
)

echo.                                                    
echo.   __  ____      __   __       ____                 
echo.  /  ^|/  (_)__ _/ /  / /___ __/ __/______ ____  __  
echo. / /^|_/ / / _ \/ _ \/ __/ // /\ \/ __/ _ \/ _ \/ -_)
echo./_/  /_/_/\_, /_//_/\__/\_, /___/\__/\_,_/ .__/\__/ 
echo.         /___/         /___/            /_/         
echo.                                                    

echo.This script will install MightyScape Open Source extensions for Inkscape.

echo.The target folder to install: %TGT%\%GIT_REPO%\

:entry
set /P c=Do you like to continue [y/n]?
if /I "%c%" EQU "y" goto :preflight
if /I "%c%" EQU "n" goto :quit
goto :entry

:quit
echo.kk thx bye!
pause
exit 0

:preflight
echo.Checking for having Inkscape :-) ...
if not exist %INKSCAPE_USER_DIR%\ (
	echo.Inkscape not installed! Hmm....
	pause
	exit 1
	)

echo.Checking for running Inkscape instances ...
tasklist /fi "ImageName eq inkscape.exe" /fo csv 2>NUL | find /I "inkscape.exe">NUL
if %ERRORLEVEL% EQU 0 (
	echo.Error: Inkscape is running right now. Please quit and try again!
	pause
	exit 1
	)
goto :packages

:packages
echo.Installing system packages ...
:: Install chocolatey
powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"

:: Now use chocolatey to install basic requirements, if not already existing (we don't want to mess with duplicate installations)
where curl   >NUL 2>NUL && if NOT ERRORLEVEL 0 (choco install -y curl)
where xml    >NUL 2>NUL && if NOT ERRORLEVEL 0 (choco install -y xmlstarlet)
where python >NUL 2>NUL && if NOT ERRORLEVEL 0 (choco install -y python --version=%PYTHON_VERSION% --params "'/quiet InstallAllUsers=1 PrependPath=1'")
where git    >NUL 2>NUL && if NOT ERRORLEVEL 0 (choco install -y git.install --params "'/GitAndUnixToolsOnPath /WindowsTerminal /NoAutoCrlf'")
where cmake  >NUL 2>NUL && if NOT ERRORLEVEL 0 (choco install -y cmake)
where gcc    >NUL 2>NUL && if NOT ERRORLEVEL 0 (choco install -y mingw)
where jq     >NUL 2>NUL && if NOT ERRORLEVEL 0 (choco install -y jq)

goto :setup

:setup
echo.Cloning MightyScape ...
curl -s -k https://api.%GIT_SERVER%/repos/%GIT_MAINTAINER%/%GIT_REPO% > %TEMP%\size.tmp
jq ".size" %TEMP%\size.tmp > NUL
for /f "delims=" %%A in ('jq ".size" %TEMP%\size.tmp') do set SIZE_KB=%%A
set /a SIZE_MB=%SIZE_KB%/1000 > NUL
echo.Repository size is approx. %SIZE_MB% MB
cd  %TGT%\
if %ERRORLEVEL% NEQ 0 (
	echo.Extensions directory "%TGT%" could not be found!
	pause
	exit 1
	)

git clone https://%GIT_SERVER%/%GIT_MAINTAINER%/%GIT_REPO%.git
if %ERRORLEVEL% NEQ 0 (
	echo.Error while cloning. Check if the directory exists and if correct permissions are set!
	pause
	exit 1
	)

echo.Enrolling Python3 virtual environment + required packages ...
python.exe -m venv %TGT%\%GIT_REPO%\%VENV%\
cd %TGT%\%GIT_REPO%\
%TGT%\%GIT_REPO%\%VENV%\Scripts\python.exe -m pip install --upgrade pip
FOR /F %%k in ('findstr /V "#" requirements.txt') DO ( %TGT%\%GIT_REPO%\%VENV%\Scripts\python.exe -m pip install %%k )
goto :adjust_preferences

:adjust_preferences
echo.Adjusting/inserting attribute value "python-interpreter" in "%INKSCAPE_USER_DIR%\preferences.xml"...
SET PREF_FILE=%INKSCAPE_USER_DIR%\preferences.xml
set PREF_NODE=/inkscape/group[@id="extensions"]
set PREF_ATTRIB="python-interpreter"
set PREF_VALUE=%TGT%\%GIT_REPO%\%VENV%\Scripts\pythonw.exe
findstr /I "python-interpreter" %PREF_FILE% > NUL
if %ERRORLEVEL% EQU 0 (
	xml edit --inplace --ps --pf --update %PREF_NODE%/@%PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	) else (
	xml edit --inplace --ps --pf --insert %PREF_NODE% --type attr -n %PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	)

echo.Installation done!
pause
exit 0