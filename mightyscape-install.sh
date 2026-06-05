After install check availability of required commands
Pyqt update win11/macOS

#!/bin/bash
clear

NF="\033[0m"
CL="\033[38;5;45m"
CR="\033[38;5;3m"
GIT_SERVER="github.com"
GIT_MAINTAINER="eridur-de"
GIT_REPO="mightyscape-1.2"
INKSCAPE_FLATPAK_ID="org.inkscape.Inkscape"

bye () {
    echo -e "${CR}Installation was arborted. Check for possible errors. Please start the script again to finish installation! ${NF}"
    exit 1
}

goon () {
    exec 3<>/dev/tty
    read -u 3 -p "$(echo -e ${CL}"Do you like to continue? [y/n]\n "${NF})" -n 1 REPLY
}

test_is_root () {
    if [[ $EUID == 0 ]]; then
        echo -e "${CR}Please do not run as root! ${NF}"
    bye
    fi
}

test_can_sudo () {
    echo -e "${CL}Check if user can sudo ...${NF}"
    local prompt
    prompt=$(sudo -nv 2>&1)
    if [[ $? -eq 0 ]]; then
		:
    elif echo $prompt | grep -q '^sudo:'; then
		:
    else
		echo -e "${CR}The current user is not allowed for sudo. Cannot continue ...${NF}"
		bye
    fi
}

test_is_running () {
    echo -e "${CL}Checking for running Inkscape instances ...${NF}"
    INK_RUNNING=$(pgrep -l "inkscape$" | wc -l)
    if [[ $INK_RUNNING -gt 0 ]]; then
        echo -e "${CR}Error: Inkscape is running right now. Please quit and try again!\n${NF}"
        echo -e "${CL}PIDs:${NF}"
        pgrep -l "inkscape$"
        bye
    fi
}

get_installations () {
    echo -e "${CL}Checking for having Inkscape :-) ...${NF}"

    if [[ $(type -P "flatpak") ]]; then
        flatpak list | grep $INKSCAPE_FLATPAK_ID > /dev/null 2>&1; if [[ $? == 0 ]]; then echo -e "${CL} - Flatpak package \"$INKSCAPE_FLATPAK_ID\" installed (0)${NF}"; fi
    fi
    if [[ $(type -P "snap") ]]; then
        snap list | grep inkscape > /dev/null 2>&1; if [[ $? == 0 ]]; then echo -e "${CL} - snap package \"inkscape\" installed (1)${NF}"; fi
    fi
    if [[ $(grep -Ei --exclude-dir=* 'debian|buntu|mint' /etc/*release 2>&1) ]]; then
        PACKMAN="apt"
    fi
    if [[ $(grep -Ei --exclude-dir=* 'fedora|redhat' /etc/*release 2>&1) ]]; then
        PACKMAN="dnf"
    fi
    if [[ $PACKMAN == "apt" ]]; then
        for PKG in inkscape; do
            dpkg -s $PKG > /dev/null 2>&1; if [[ $? == 0 ]]; then echo -e "${CL} - apt package \"$PKG\" installed (2)${NF}"; fi
        done
    fi
    if [[ $PACKMAN == "dnf" ]]; then
        for PKG in inkscape; do
            rpm -q $PKG > /dev/null 2>&1; if [[ $? == 0 ]]; then echo -e "${CL} - dnf package \"$PKG\" installed (3)${NF}"; fi
        done
    fi
    if [[ $PACKMAN == "apt" ]] || [[ $PACKMAN == "dnf" ]]; then
        echo -e "${CL} - AppImage (maybe existent?) (4)${NF}"
    fi
    if [[ $(type -P "mdfind") ]]; then
        if [[ $(mdfind -name 'Inkscape' 2>&1 | grep "Inkscape.app") ]]; then echo -e "${CL} - dmg package \"Inkscape.app\" installed (5)${NF}"; fi
    fi

    exec 3<>/dev/tty
    read -u 3 -p "$(echo -e ${CL}"Choose an Inkscape instance where to install and configure MightyScape:\n "${NF})" -n 1 SELECTION
}

instance_choice () {
    echo -e "${CL}Preparing installation environment ...${NF}"
    get_installations
    case $SELECTION in
    0)
        INKSCAPE_CMD="flatpak run $INKSCAPE_FLATPAK_ID"
        INKSCAPE_USER_DIR="$($INKSCAPE_CMD --user-data-directory)"
        INKSCAPE_EXTENSIONS_DIR="$INKSCAPE_USER_DIR/extensions"
        ;;
    1)
        snap list inkscape | grep devmode > /dev/null
        if [[ $? == 0 ]]; then
            INKSCAPE_CMD="/snap/bin/inkscape"
            INKSCAPE_USER_DIR="$($INKSCAPE_CMD --user-data-directory)"
            INKSCAPE_EXTENSIONS_DIR="$HOME/snap/inkscape/common/extensions"
            SNAP_PYTHON_VERSION=$(ls /snap/inkscape/current/lib/ | grep "python3.")
            echo -e "${CL}Info: snap is using ${SNAP_PYTHON_VERSION}. This must match python version in pyproject.toml!${NF}"
        else
            echo -e "${CR}Error: snap is not installed with enough permissions. If you want to use MightyScape for snap, please reinstall it with devmode: 'sudo snap remove inkscape && sudo snap install inkscape --devmode'\n${NF}"
            bye
        fi
        ;;
    2|3)
        INKSCAPE_CMD="/usr/bin/inkscape"
        INKSCAPE_USER_DIR="$($INKSCAPE_CMD --user-data-directory)"
        INKSCAPE_EXTENSIONS_DIR="$INKSCAPE_USER_DIR/extensions"
        ;;
    4)
        exec 3<>/dev/tty
        read -u 3 -p "$(echo -e ${CL}"Please enter the path of your Inkscape-1.?.?.AppImage. If you leave empty, default values for configuration are used.\n "${NF})" INKSCAPE_APPIMAGE
        if [[ -e "$INKSCAPE_APPIMAGE" ]]; then
            INKSCAPE_CMD=$INKSCAPE_APPIMAGE
            INKSCAPE_USER_DIR="$($INKSCAPE_CMD --user-data-directory 2> /dev/null | tail -n 1)"
            INKSCAPE_EXTENSIONS_DIR="$INKSCAPE_USER_DIR/extensions"
        else
            echo -e "${CR}Error: path seems not to exist. Using default values.\n${NF}"
            INKSCAPE_CMD="no-appimage-provided"
            INKSCAPE_USER_DIR="$HOME/.config/inkscape"
            INKSCAPE_EXTENSIONS_DIR="$INKSCAPE_USER_DIR/extensions"
        fi
        ;;
    5)
        INKSCAPE_CMD="/Applications/Inkscape.app/Contents/MacOS/inkscape"
        INKSCAPE_USER_DIR="$($INKSCAPE_CMD --user-data-directory)"
        INKSCAPE_EXTENSIONS_DIR="$INKSCAPE_USER_DIR/extensions"
        ;;
    *)
        bye
        ;;
    esac

    if [[ ! -e "$INKSCAPE_USER_DIR" ]]; then
        echo -e "${CR}Error: Inkscape user directory ${INKSCAPE_USER_DIR} does not exist!${NF}"
        bye
    fi

    echo -e "\n${CL}Inkscape user directory: ${INKSCAPE_USER_DIR}${NF}"
    echo -e "${CL}Inkscape extension directory: ${INKSCAPE_EXTENSIONS_DIR}${NF}"
}

uv_setup () {
	echo -e "${CL}Checking for Python UV existence ...${NF}"
    if [[ ! $(type -P "uv") ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
    fi
}

install_system_packages () {
    echo -e "${CL}Installing system packages ...${NF}"
    if [[ $PACKMAN == "apt" ]] &&  [[ $SELECTION == 2 ]]; then
        APT_PACKAGES="git cmake jq g++ python3-full python3-dev python3-venv xmlstarlet libgirepository-2.0-dev libcairo2-dev"
        sudo apt install -y $APT_PACKAGES
        sudo apt update && sudo apt upgrade -y $APT_PACKAGES
    fi
    if [[ $PACKMAN == "dnf" ]] && [[ $SELECTION == 3 ]]; then
        DNF_PACKAGES="curl git cmake jq g++ python3-devel python3-venv xmlstarlet cairo-devel"
        sudo dnf install $DNF_PACKAGES
        sudo dnf update $DNF_PACKAGES
    fi
    if [[ $SELECTION == 5 ]]; then
        if [[ ! $(type -P "port") ]]; then
            echo -e "${CL}Installing MacPorts ...${NF}"
            xcode-select --install
        else
            echo -e "${CL}Upgrading MacPorts tree first (might take a while) ...${NF}"
        fi
        sudo port selfupdate
        echo -e "${CL}Installing system packages ...${NF}"
        PACKAGES="git jq libiconv xmlstarlet"
        sudo port install $PACKAGES
        sudo port upgrade outdated
    fi
}

git_update () {
    echo -e "${CL}MightyScape repo ...${NF}"
    git stash
    git pull
}

setup_mightyscape () {
    echo -e "${CL}Cloning MightyScape ...${NF}"
    GIT_REPO_SIZE=$(curl -s -k https://api.${GIT_SERVER}/repos/${GIT_MAINTAINER}/${GIT_REPO})
    if [[ "$GIT_REPO_SIZE" =~ ^[0-9]+$ ]] && [[ $GIT_REPO_SIZE -gt 0 ]]; then
        echo -e "${CL}Repository size is approx. $(( $(echo ${GIT_REPO_SIZE} | jq '.size') / 1000 )) MB.${NF}"
    fi
    cd "$INKSCAPE_EXTENSIONS_DIR/"
    if [[ $? != 0 ]]; then
        echo -e "${CL}Extensions directory \"$INKSCAPE_EXTENSIONS_DIR\" could not be found. Trying to create!${NF}"
        mkdir -p "$INKSCAPE_EXTENSIONS_DIR"
        cd "$INKSCAPE_EXTENSIONS_DIR/"
        if [[ $? != 0 ]]; then
            echo -e "${CL}Error: Extensions directory \"$INKSCAPE_EXTENSIONS_DIR\" could not be created. Please check your Inkscape installation!${NF}"
            bye
        fi
    fi

    if [[ -e "$INKSCAPE_EXTENSIONS_DIR/$GIT_REPO/" ]]; then
            echo -e "${CL}Target directory already exists. Checking if it's git project ...'${NF}"
            if [[ -e "$INKSCAPE_EXTENSIONS_DIR/$GIT_REPO/.git" ]]; then
                echo -e "${CL}Target directory is git. Update the repo?'${NF}"
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    git_update
                fi
            fi
    else
        git clone https://$GIT_SERVER/$GIT_MAINTAINER/$GIT_REPO.git
        if [[ $? != 0 ]]; then
            echo -e "${CR}Error while cloning.${NF}"
            bye
        fi
    fi
    goon
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CL}Enrolling Python3 virtual environment + required packages ...${NF}"
        uv_setup
        cd "$INKSCAPE_EXTENSIONS_DIR/$GIT_REPO/"
        export UV_PROJECT_ENVIRONMENT="$INKSCAPE_EXTENSIONS_DIR/$GIT_REPO"
        uv self update
        uv venv --allow-existing "$INKSCAPE_EXTENSIONS_DIR/$GIT_REPO"
        uv add --frozen -r requirements.txt
        uv pip install --upgrade -r requirements.txt
        echo -e "\n${CL}Total size of installation: $(du -sh "$(pwd)" | awk '{print $1}') ...${NF}"
    else
        bye
    fi
}

adjust_preferences () {
    echo -e "${CL}Adjusting/inserting attribute value \"python-interpreter\" in \"$INKSCAPE_USER_DIR/preferences.xml\"...${NF}"
    PREF_FILE="$INKSCAPE_USER_DIR/preferences.xml"
    PREF_NODE="/inkscape/group[@id=\"extensions\"]"
    PREF_ATTRIB="python-interpreter"
    PREF_VALUE="$INKSCAPE_EXTENSIONS_DIR/$GIT_REPO/bin/python3"
    grep "python-interpreter" "$PREF_FILE" > /dev/null
    if [[ $? == 0 ]]; then
        xmlstarlet edit --inplace --ps --pf --update $PREF_NODE/@$PREF_ATTRIB --value "$PREF_VALUE" "$PREF_FILE"
    else
        xmlstarlet edit --inplace --ps --pf --insert $PREF_NODE --type attr -n $PREF_ATTRIB --value "$PREF_VALUE" "$PREF_FILE"
    fi
}

call_about_extension () {
    CALL="$INKSCAPE_CMD --with-gui --actions=\"fablabchemnitz.de.about-upgrade-mightyscape\""
	echo -e "${CL}Calling About Extension to test installation: ${CALL}${NF}"
	eval $CALL
}

echo -e "${CL}                                                      ${NF}"
echo -e "${CL}   __  ____      __   __       ____                   ${NF}"
echo -e "${CL}  /  |/  (_)__ _/ /  / /___ __/ __/______ ____  ___   ${NF}"
echo -e "${CL} / /|_/ / / _ \`/ _ \/ __/ // /\ \/ __/ _ \`/ _ \/ -_)${NF}"
echo -e "${CL}/_/  /_/_/\_, /_//_/\__/\_, /___/\__/\_,_/ .__/\__/   ${NF}"
echo -e "${CL}         /___/         /___/            /_/           ${NF}"
echo -e "${CL}                                                      ${NF}\n\n"
echo -e "${CL}This script will install MightyScape Open Source extensions for Inkscape.${NF}"

test_is_root
test_can_sudo
test_is_running
instance_choice
install_system_packages
setup_mightyscape
adjust_preferences
call_about_extension
