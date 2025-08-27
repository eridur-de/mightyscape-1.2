@echo off
setlocal ENABLEDELAYEDEXPANSION

net session>NUL 2>&1 && goto :elevated
set ELEVATE_CMDLINE=cd /d "%~dp0" ^& "%~f0" %*
powershell.exe -noprofile -c Start-Process -WindowStyle Maximized -Verb RunAs cmd.exe \"/k $env:ELEVATE_CMDLINE\"
exit /b %ERRORLEVEL%

:elevated
set INKSCAPE_USER_DIR=%AppData%\inkscape
set TGT=%INKSCAPE_USER_DIR%\extensions
set VENV=venv
set GIT_SERVER=github.com
set GIT_MAINTAINER=eridur-de
set GIT_REPO=mightyscape-1.2
set PYTHON_VERSION=3.13.5
set CMAKE_VERSION=3.31.0

COLOR 03

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
where choco>NUL 2>NUL && if not ERRORLEVEL 0 (
	powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
	)

choco feature enable --name="exitOnRebootDetected"

:: Now use chocolatey to install basic requirements, if not already existing (we don't want to mess with duplicate installations)
where curl    >NUL 2>NUL && if not ERRORLEVEL 0 (choco install -y curl)

:: disabled until https://github.com/eridur-de/mightyscape-1.2/issues/131 is fixed
:: where cmake   >NUL 2>NUL && if not ERRORLEVEL 0 (
	:: choco install -y visualstudio2019buildtools --package-parameters "--includeRecommended --includeOptional"
	:: choco install -y visualstudio2019-workload-netcorebuildtools
	:: choco install -y visualstudio2019-workload-netcoretools
	:: choco install -y visualstudio2019-workload-vctools

	:: not required
	:: choco install -y visualstudio2019-workload-nativedesktop
	:: choco install -y visualstudio2019-workload-universal
	:: choco install -y visualstudio2019-workload-universalbuildtools
:: )
:: cmake.exe
set PATH=%PATH%;C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin
:: nmake.exe
set PATH=%PATH%;C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64
:: where cmake  >NUL 2>NUL && if not ERRORLEVEL 0 (choco install -y cmake --version=%CMAKE_VERSION%)
:: where gcc    >NUL 2>NUL && if not ERRORLEVEL 0 (choco install -y mingw)
where git    >NUL 2>NUL && if not ERRORLEVEL 0 (choco install -y git.install --params "'/GitAndUnixToolsOnPath /WindowsTerminal /NoAutoCrlf'")
where jq     >NUL 2>NUL && if not ERRORLEVEL 0 (choco install -y jq)
where python >NUL 2>NUL && if not ERRORLEVEL 0 (choco install -y python --version=%PYTHON_VERSION% --params "'/quiet InstallAllUsers=1 PrependPath=1'")
where xml    >NUL 2>NUL && if not ERRORLEVEL 0 (choco install -y xmlstarlet)

goto :setup

:setup
echo.Cloning MightyScape ...
curl -s -k https://api.%GIT_SERVER%/repos/%GIT_MAINTAINER%/%GIT_REPO% > %TEMP%\size.tmp
jq ".size" %TEMP%\size.tmp >NUL
for /f "delims=" %%A in ('jq ".size" %TEMP%\size.tmp') do set SIZE_KB=%%A
set /a SIZE_MB=%SIZE_KB%/1000>NUL
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
for /F %%k in ('findstr /V "#" requirements.txt') DO (%TGT%\%GIT_REPO%\%VENV%\Scripts\python.exe -m pip install %%k)
goto :adjust_preferences

:adjust_preferences
echo.Adjusting/inserting attribute value "python-interpreter" in "%INKSCAPE_USER_DIR%\preferences.xml"...
set PREF_FILE=%INKSCAPE_USER_DIR%\preferences.xml
set PREF_NODE=/inkscape/group[@id="extensions"]
set PREF_ATTRIB="python-interpreter"
set PREF_VALUE=%TGT%\%GIT_REPO%\%VENV%\Scripts\pythonw.exe
findstr /I "python-interpreter" %PREF_FILE%>NUL
if %ERRORLEVEL% EQU 0 (
	xml edit --inplace --ps --pf --update %PREF_NODE%/@%PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	) else (
	xml edit --inplace --ps --pf --insert %PREF_NODE% --type attr -n %PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	)

echo.Installation done!
powershell -command "$fso = new-object -com Scripting.FileSystemObject; gci -Directory | select @{l='Size'; e={$fso.GetFolder($_.FullName).Size}},FullName | sort Size -Descending | ft @{l='Size [MB]'; e={'{0:N2}' -f ($_.Size / 1MB)}},FullName"
pause
exit 0
