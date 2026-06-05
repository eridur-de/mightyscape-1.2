@echo off
setlocal ENABLEDELAYEDEXPANSION
net session>nul 2>&1 && goto :elevated
set ELEVATE_CMDLINE=cd /d "%~dp0" ^& "%~f0" %*
powershell.exe -noprofile -c Start-Process -WindowStyle Maximized -Verb RunAs cmd.exe \"/k $env:ELEVATE_CMDLINE\"
exit /b %ERRORLEVEL%

:elevated
cls
set GIT_SERVER=github.com
set GIT_MAINTAINER=eridur-de
set GIT_REPO=mightyscape-1.2
COLOR 03
echo.
echo.   __  ____      __   __       ____
echo.  /  ^|/  (_)__ _/ /  / /___ __/ __/______ ____  __
echo. / /^|_/ / / _ \/ _ \/ __/ // /\ \/ __/ _ \/ _ \/ -_)
echo./_/  /_/_/\_, /_//_/\__/\_, /___/\__/\_,_/ .__/\__/
echo.         /___/         /___/            /_/
echo.
echo.This script will install MightyScape Open Source extensions for Inkscape.

:test_is_running
echo.Checking for running Inkscape instances ...
tasklist /fi "ImageName eq inkscape.exe" /fo csv 2>nul | find /I "inkscape.exe">nul
if %ERRORLEVEL% EQU 0 (
	echo.Error: Inkscape is running right now. Please quit and try again!
	pause
	exit 1
	)
goto :get_installations

:get_installations
echo.Checking for having Inkscape :-) ...
where winget >nul 2>nul
if not %ERRORLEVEL%==0 (
	powershell -NoP -NoLogo -NonI -Command "Install-Script winget-install -Force"
	call refreshenv && powershell -NoP -NoLogo -NonI -ExecutionPolicy ByPass -Command "winget-install"
)
for /F "delims=" %%A in ('powershell -Command "$OldLog = Get-WinUserLanguageList; Set-WinUserLanguageList -LanguageList en-US -Force; $Path = ((winget list Inkscape --details | Select-String """Installed Location:""").Line); Set-WinUserLanguageList -LanguageList $OldLog -Force; $Path -replace """Installed Location: """, """""" "') do (
	set "PKG=%%A"
		if exist "!PKG!\VFS\ProgramFilesX64\Inkscape\bin\inkscape.exe" (
		set PKG_MSSTORE="!PKG!\VFS\ProgramFilesX64\Inkscape\bin\inkscape.exe"
	)
	if exist "!PKG!\bin\inkscape.exe" (
		set PKG_MSI="!PKG!\bin\inkscape.exe"
	)
)
if defined PKG_MSSTORE (
	echo. - Microsoft Store package installed (0^)
	)
if defined PKG_MSI (
	echo. - Regular Inkscape *.msi/*.exe setup installed (1^)
	)
echo. - portable executable (maybe existent?) (2)
goto :instance_choice

:instance_choice
set /P INSTANCE_CHOICE=Choose an Inkscape instance where to install and configure MightyScape: [0/1/2]?
if /I "%INSTANCE_CHOICE%" EQU "0" (
	setlocal DISABLEDELAYEDEXPANSION
	set "INKSCAPE_CMD=shell:AppsFolder\25415Inkscape.Inkscape_9waqn51p1ttv2^^!INKSCAPE"
	setlocal ENABLEDELAYEDEXPANSION
	set INKSCAPE_USER_DIR=%AppData%\inkscape
	)
if /I "%INSTANCE_CHOICE%" EQU "1" (
	set INKSCAPE_CMD=%PKG_MSI%
	rem set INKSCAPE_USER_DIR=%AppData%\inkscape
	for /F "delims=" %%A in ('%PKG_MSI% --user-data-directory') do (set INKSCAPE_USER_DIR=%%A)
	)
if /I "%INSTANCE_CHOICE%" EQU "2" (
	set /P PKG_PORTABLE=Please enter the path of your portable installation's Inkscape.exe. If you leave empty, default values for configuration are used.
	if not exist "%PKG_PORTABLE%" (
		echo.Error: path seems not to exist. Using default values
			set INKSCAPE_CMD=no-portable-provided
	) else (
		set INKSCAPE_CMD=%PKG_PORTABLE%
	)
	set INKSCAPE_USER_DIR=%AppData%\inkscape
	)
goto :proceed_setup

:proceed_setup

echo.Inkscape user directory: %INKSCAPE_USER_DIR%
if not exist "%INKSCAPE_USER_DIR%" (
	echo.Error: Inkscape user directory %INKSCAPE_USER_DIR% does not exist!
	pause
	exit 1
)
set INKSCAPE_EXTENSIONS_DIR=%INKSCAPE_USER_DIR%\extensions
echo.Inkscape extension directory: %INKSCAPE_EXTENSIONS_DIR%
if not exist "%INKSCAPE_EXTENSIONS_DIR%" (
	echo.Extensions directory "%INKSCAPE_EXTENSIONS_DIR%" could not be found. Trying to create!
	mkdir %INKSCAPE_USER_DIR%
	)
goto :install_system_packages

:install_system_packages
echo.Installing system packages ...
where choco >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing choco
	powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
	if !ERRORLEVEL!==350 goto :reboot
	)
choco feature | find /I "[x] exitOnRebootDetected" >nul 2>nul
if not %ERRORLEVEL%==0 (
	choco feature enable --name="exitOnRebootDetected"
	)
where curl >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing curl
	choco install -y curl
	if !ERRORLEVEL!==350 goto :reboot
	)
where jq >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing jq
	choco install -y jq
	if !ERRORLEVEL!==350 goto :reboot
	)
where xml >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing xmlstarlet
	choco install -y xmlstarlet
	if !ERRORLEVEL!==350 goto :reboot
	)
where git >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing git
	choco install -y git.install --params "'/GitAndUnixToolsOnPath /WindowsTerminal /NoAutoCrlf'"
	if !ERRORLEVEL!==350 goto :reboot
	)
choco list --lo --limit-output -e vcredist140 | find /i "vcredist140" >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing vcredist140
	choco install -y vcredist140
	if !ERRORLEVEL!==350 goto :reboot
	)
choco list --lo --limit-output -e vcredist2015 | find /i "vcredist2015" >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing vcredist2015
	choco install -y vcredist2015
	if !ERRORLEVEL!==350 goto :reboot
	)
uv --version >nul 2>nul
if not %ERRORLEVEL%==0 (
	echo.Installing Python UV ...
	choco install -y uv
	if !ERRORLEVEL!==350 goto :reboot
	)
call refreshenv && choco upgrade -y chocolatey curl git jq vcredist140 vcredist2015 xmlstarlet
goto :setup_mightyscape

:reboot
echo.Please reboot and call this setup again to continue!
pause
exit 1

:setup_mightyscape
echo.Cloning MightyScape ...
curl -s -k https://api.%GIT_SERVER%/repos/%GIT_MAINTAINER%/%GIT_REPO% > %TEMP%\size.tmp
jq ".size" %TEMP%\size.tmp >nul
for /f "delims=" %%A in ('jq ".size" %TEMP%\size.tmp') do set SIZE_KB=%%A
set /a SIZE_MB=%SIZE_KB%/1000>nul
echo.Repository size is approx. %SIZE_MB% MB
if not exist %INKSCAPE_EXTENSIONS_DIR% (
	echo.Extensions directory "%INKSCAPE_EXTENSIONS_DIR%" could not be found!
	pause
	exit 1
	)
cd %INKSCAPE_EXTENSIONS_DIR%\
if exist %INKSCAPE_EXTENSIONS_DIR%\%GIT_REPO%\ (
	echo.Target directory already exists. Checking if it's git project ...
	if exist %INKSCAPE_EXTENSIONS_DIR%\%GIT_REPO%\.git\ (
		goto :entry_git_update
	)
) else (
	git clone https://%GIT_SERVER%/%GIT_MAINTAINER%/%GIT_REPO%.git
	if %ERRORLEVEL% NEQ 0 (
		echo.Error while cloning.
		pause
		exit 1
		)
	goto :install_python_env
)

:entry_git_update
set /P c=Target directory is git. Update the repo? [y/n]?
if /I "%c%" EQU "y" goto :git_update
if /I "%c%" EQU "n" goto :install_python_env
goto :entry_git_update

:git_update
echo.Updating MightyScape repo ...
cd %INKSCAPE_EXTENSIONS_DIR%\%GIT_REPO%\
git stash
git pull
goto :install_python_env

:install_python_env
echo.Enrolling Python3 virtual environment + required packages ...
cd %INKSCAPE_EXTENSIONS_DIR%/%GIT_REPO%/
set UV_PROJECT_ENVIRONMENT=%INKSCAPE_EXTENSIONS_DIR%/%GIT_REPO%
uv self update
uv venv --allow-existing %INKSCAPE_EXTENSIONS_DIR%/%GIT_REPO%
for /r %%G in (requirements.txt) do (
    if exist "%%G" (
        uv add --frozen -r "%%G" 2>nul
        if errorlevel 1 (
            echo.Failed to install dependencies for: %%G
        )
    )
)
for /r %%G in (requirements.txt) do (
    if exist "%%G" (
        uv pip install --upgrade -r "%%G" 2>nul
        if errorlevel 1 (
            echo.Failed to upgrade dependencies for: %%G
        )
    )
)
echo.Total size of installation:
powershell -command "$fso = new-object -com Scripting.FileSystemObject; gci -Directory | select @{l='Size'; e={$fso.GetFolder($_.FullName).Size}},FullName | sort Size -Descending | ft @{l='Size [MB]'; e={'{0:N2}' -f ($_.Size / 1MB)}},FullName"
goto :adjust_preferences

:adjust_preferences
echo.Adjusting/inserting attribute value "python-interpreter" in "%INKSCAPE_USER_DIR%\preferences.xml"...
set PREF_FILE=%INKSCAPE_USER_DIR%\preferences.xml
set PREF_NODE=/inkscape/group[@id=\"extensions\"]
set PREF_ATTRIB="python-interpreter"
set PREF_VALUE=%INKSCAPE_EXTENSIONS_DIR%\%GIT_REPO%\Scripts\pythonw.exe
findstr /I "python-interpreter" %PREF_FILE%>nul
if %ERRORLEVEL% EQU 0 (
	xml edit --inplace --ps --pf --update %PREF_NODE%/@%PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	) else (
	xml edit --inplace --ps --pf --insert %PREF_NODE% --type attr -n %PREF_ATTRIB% --value %PREF_VALUE% %PREF_FILE%
	)
goto :call_about_extension

:call_about_extension
if /I "%INSTANCE_CHOICE%" EQU "0" (
	echo.Calling Inkscape without About Extension: !INKSCAPE_CMD!
	echo.If Inkscape is installed by MS Store, we cannot pass cli attributes! Please manually test by starting About Extension
	start "" %INKSCAPE_CMD%

) else (
	set CALL=%INKSCAPE_CMD% --with-gui --actions="fablabchemnitz.de.about-upgrade-mightyscape"
	echo.Calling About Extension to test installation: !CALL!
	call !CALL!
)
pause
exit 0
