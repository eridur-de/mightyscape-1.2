@echo off
setlocal ENABLEDELAYEDEXPANSION

net session>NUL 2>&1 && goto :elevated
set ELEVATE_CMDLINE=cd /d "%~dp0" ^& "%~f0" %*
powershell.exe -noprofile -c Start-Process -WindowStyle Maximized -Verb RunAs cmd.exe \"/k $env:ELEVATE_CMDLINE\"
exit /b %ERRORLEVEL%

:elevated
set INKSCAPE_USER_DIR=%AppData%\inkscape
set INKSCAPE_EXTENSIONS_DIR=%INKSCAPE_USER_DIR%\extensions
set GIT_SERVER=github.com
set GIT_MAINTAINER=eridur-de
set GIT_REPO=mightyscape-1.2
:: set CMAKE_VERSION=3.31.0
COLOR 03
echo.
echo.   __  ____      __   __       ____
echo.  /  ^|/  (_)__ _/ /  / /___ __/ __/______ ____  __
echo. / /^|_/ / / _ \/ _ \/ __/ // /\ \/ __/ _ \/ _ \/ -_)
echo./_/  /_/_/\_, /_//_/\__/\_, /___/\__/\_,_/ .__/\__/
echo.         /___/         /___/            /_/
echo.
echo.This script will install MightyScape Open Source extensions for Inkscape.

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
for /f "delims=" %%A in ('wmic product where "Name='Inkscape'" get InstallLocation ^| find "\"') do set INKSCAPE_CMD=%%A
SET INKSCAPE_CMD=%INKSCAPE_CMD:~0,-4%\bin\inkscape.exe
if not exist "%INKSCAPE_CMD%" (
	echo.Inkscape not installed! Hmm....
	pause
	exit 1
	)
if not exist "%INKSCAPE_USER_DIR%" (
	echo.Extensions directory "%INKSCAPE_EXTENSIONS_DIR%" could not be found. Trying to create!
	mkdir %INKSCAPE_USER_DIR%
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
where choco >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing choco
	powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
	if !ERRORLEVEL!==350 goto :reboot
	)
choco feature | find /I "[x] exitOnRebootDetected" >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	choco feature enable --name="exitOnRebootDetected"
	)
:: Now use chocolatey to install basic requirements, if not already existing (we don't want to mess with duplicate installations)
where curl >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing curl
	choco install -y curl
	if !ERRORLEVEL!==350 goto :reboot
	)

:: disabled until https://github.com/eridur-de/mightyscape-1.2/issues/131 is fixed
:: where cmake >NUL 2>NUL
:: if not %ERRORLEVEL%==0 (
	:: echo.Installing visualstudio2019 and workloads
	:: choco install -y visualstudio2019buildtools --package-parameters "--includeRecommended --includeOptional"
	:: choco install -y visualstudio2019-workload-netcorebuildtools
	:: choco install -y visualstudio2019-workload-netcoretools
	:: choco install -y visualstudio2019-workload-vctools
	:: not required
	:: choco install -y visualstudio2019-workload-nativedesktop
	:: choco install -y visualstudio2019-workload-universal
	:: choco install -y visualstudio2019-workload-universalbuildtools
	:: if !ERRORLEVEL!==350 goto :reboot
:: )
:: cmake.exe
:: set PATH=%PATH%;C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin
:: nmake.exe
:: set PATH=%PATH%;C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64
:: where cmake  >NUL 2>NUL
:: if not ERRORLEVEL%==0 (
::		echo.Installing cmake
::		choco install -y cmake --version=%CMAKE_VERSION%
::		if !ERRORLEVEL!==350 goto :reboot
::		)
:: where gcc    >NUL 2>NUL
:: if not ERRORLEVEL%==0 (
::		echo.Installing mingw
::		choco install -y mingw
::		if !ERRORLEVEL!==350 goto :reboot
::		)
where jq >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing jq
	choco install -y jq
	if !ERRORLEVEL!==350 goto :reboot
	)
where xml >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing xmlstarlet
	choco install -y xmlstarlet
	if !ERRORLEVEL!==350 goto :reboot
	)
where git >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing git
	choco install -y git.install --params "'/GitAndUnixToolsOnPath /WindowsTerminal /NoAutoCrlf'"
	if !ERRORLEVEL!==350 goto :reboot
	)
choco list --lo --limit-output -e vcredist140 | find /i "vcredist140" >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing vcredist140
	choco install -y vcredist140
	if !ERRORLEVEL!==350 goto :reboot
	)
choco list --lo --limit-output -e vcredist2015 | find /i "vcredist2015" >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing vcredist2015
	choco install -y vcredist2015
	if !ERRORLEVEL!==350 goto :reboot
	)
:: using 'where python' can lead to just open Microsoft App Store. To avoid, we call with parameters!
python --version >NUL 2>NUL
if not %ERRORLEVEL%==0 (
	echo.Installing Python UV ...
	powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
	if !ERRORLEVEL!==350 goto :reboot
	)
:: refresh environment variables after installing new commands to make them available on PATH
call refreshenv
goto :setup_mightyscape

:reboot
echo.Please reboot and call this setup again to continue!
pause
exit 1

:setup_mightyscape
echo.Cloning MightyScape ...
curl -s -k https://api.%GIT_SERVER%/repos/%GIT_MAINTAINER%/%GIT_REPO% > %TEMP%\size.tmp
jq ".size" %TEMP%\size.tmp >NUL
for /f "delims=" %%A in ('jq ".size" %TEMP%\size.tmp') do set SIZE_KB=%%A
set /a SIZE_MB=%SIZE_KB%/1000>NUL
echo.Repository size is approx. %SIZE_MB% MB
cd  %INKSCAPE_EXTENSIONS_DIR%\
if %ERRORLEVEL% NEQ 0 (
	echo.Extensions directory "%INKSCAPE_EXTENSIONS_DIR%" could not be found!
	pause
	exit 1
	)

git clone https://%GIT_SERVER%/%GIT_MAINTAINER%/%GIT_REPO%.git
if %ERRORLEVEL% NEQ 0 (
	echo.Error while cloning. Maybe the directory already exists.
	)

echo.Enrolling Python3 virtual environment + required packages ...
cd %INKSCAPE_EXTENSIONS_DIR%/%GIT_REPO%/
set UV_PROJECT_ENVIRONMENT=%INKSCAPE_EXTENSIONS_DIR%/%GIT_REPO%
uv venv --allow-existing %INKSCAPE_EXTENSIONS_DIR%/%GIT_REPO%
uv add -r requirements.txt
echo.Total size of installation:
powershell -command "$fso = new-object -com Scripting.FileSystemObject; gci -Directory | select @{l='Size'; e={$fso.GetFolder($_.FullName).Size}},FullName | sort Size -Descending | ft @{l='Size [MB]'; e={'{0:N2}' -f ($_.Size / 1MB)}},FullName"
goto :adjust_preferences

:adjust_preferences
echo.Adjusting/inserting attribute value "python-interpreter" in "%INKSCAPE_USER_DIR%\preferences.xml"...
set PREF_FILE=%INKSCAPE_USER_DIR%\preferences.xml
set PREF_NODE=/inkscape/group[@id=\"extensions\"]
set PREF_ATTRIB="python-interpreter"
set PREF_VALUE=%INKSCAPE_EXTENSIONS_DIR%\%GIT_REPO%\Scripts\pythonw.exe
findstr /I "python-interpreter" %PREF_FILE%>NUL
if %ERRORLEVEL% EQU 0 (
	xml edit --inplace --ps --pf --update %PREF_NODE%/@%PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	) else (
	xml edit --inplace --ps --pf --insert %PREF_NODE% --type attr -n %PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	)
goto :call_about_extension

:call_about_extension
set CALL="%INKSCAPE_CMD%" --with-gui --actions="fablabchemnitz.de.about-upgrade-mightyscape"
echo.Calling About Extension to test installation: %CALL%
call %CALL%
pause
exit 0
