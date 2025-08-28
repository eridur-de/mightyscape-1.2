#!/bin/bash
clear

NF="\033[0m"
CL="\033[38;5;45m"
INKSCAPE_USER_DIR=$(inkscape --user-data-directory)
TGT="$INKSCAPE_USER_DIR/extensions"
VENV="venv"
GIT_SERVER="github.com"
GIT_MAINTAINER="eridur-de"
GIT_REPO="mightyscape-1.2"

sudo_test () {
    echo -e "${CL}Check if user can sudo ...${NF}"
    IS_SUDO=$(grep "sudo" <<< $(groups $(whoami)) > /dev/null; echo $?)
    if [ $IS_SUDO != 0 ]; then
        echo -e "${CL}The current user is not allowed for sudo. Cannot continue ...${NF}"
        exit 1
    fi
}

root_test () {
    if [ $EUID == 0 ]; then
        echo -e "${CL}Please do not run as root! ${NF}"
    exit
    fi
}

check_base () {
    if [ "$(grep -Ei 'debian|buntu|mint' /etc/*release)" ]; then
        PACKMAN="apt"
    fi
    if [ "$(grep -Ei 'fedora|redhat' /etc/*release)" ]; then
        PACKMAN="dnf"
    fi
    echo -e "${CL}Having a look for your local package manager ... It is: $PACKMAN ${NF}"
}

preflight () {
    echo -e "${CL}Checking for having Inkscape :-) ...${NF}"
    if [ $PACKMAN == "apt" ]; then
        for PKG in inkscape; do
            dpkg -s $PKG > /dev/null 2>&1; if [ $? == 1 ]; then echo -e "${CL}package \"$PKG\" not installed! Hmm....${NF}"; exit; fi
        done
    fi
    if [ $PACKMAN == "dnf" ]; then
        for PKG in inkscape; do
            rpm -q $PKG > /dev/null 2>&1; if [ $? == 1 ]; then echo -e "${CL}package \"$PKG\" not installed! Hmm....${NF}"; exit; fi
        done
    fi

    echo -e "${CL}Checking for running Inkscape instances ...${NF}"
    INK_RUNNING=$(pgrep -l inkscape | wc -l)
    if [ $INK_RUNNING -gt 0 ]; then
        echo -e "${CL}Error: Inkscape is running right now. Please quit and try again! \n${NF}"
        echo -e "${CL}PIDs:${NF}"
        pgrep -l inkscape
        exit 1
    fi
}

packages () {
    echo -e "${CL}Installing system packages ...${NF}"
    if [ $PACKMAN == "apt" ]; then
        sudo apt install -y curl git cmake g++ python3-full python3-dev   python3-venv xmlstarlet libgirepository-2.0-dev libcairo2-dev
    fi
    if [ $PACKMAN == "dnf" ]; then
        sudo dnf install    curl git cmake g++              python3-devel python3-venv xmlstarlet                         cairo-devel
    fi
}

setup () {
    echo -e "${CL}Cloning MightyScape ...${NF}"
    echo -e "${CL}Repository size is approx. $(( $(curl -s -k https://api.${GIT_SERVER}/repos/$GIT_MAINTAINER/$GIT_REPO | jq '.size') / 1000 )) MB${NF}"
    cd  $TGT/
    if [ $? != 0 ]; then
        echo -e "${CL}Extensions directory \"$TGT\" could not be found! ${NF}"
        exit 1
    fi

    git clone https://$GIT_SERVER/$GIT_MAINTAINER/$GIT_REPO.git
    if [ $? != 0 ]; then
        echo -e "${CL}Error while cloning. Check if the directory exists and if correct permissions are set! ${NF}"
        exit 1
    fi

    echo -e "${CL}Enrolling Python3 virtual environment + required packages ...${NF}"
    python3 -m venv $TGT/$GIT_REPO/$VENV
    $TGT/$GIT_REPO/$VENV/bin/pip install --upgrade pip
    cat $TGT/$GIT_REPO/requirements.txt | sed '/^#/d' | xargs -n 1 $TGT/$GIT_REPO/$VENV/bin/pip install --upgrade
}

adjust_preferences () {
    echo -e "${CL}Adjusting/inserting attribute value \"python-interpreter\" in \"$INKSCAPE_USER_DIR/preferences.xml\"...${NF}"
    PREF_FILE="$INKSCAPE_USER_DIR/preferences.xml"
    PREF_NODE="/inkscape/group[@id=\"extensions\"]"
    PREF_ATTRIB="python-interpreter"
    PREF_VALUE="$TGT/$GIT_REPO/$VENV/bin/python3"
    grep "python-interpreter" $PREF_FILE > /dev/null
    if [ $? == 0 ]; then
        xmlstarlet edit --inplace --ps --pf --update $PREF_NODE/@$PREF_ATTRIB --value $PREF_VALUE $PREF_FILE
    else
        xmlstarlet edit --inplace --ps --pf --insert $PREF_NODE --type attr -n $PREF_ATTRIB --value $PREF_VALUE $PREF_FILE
    fi
}

echo -e "${CL}                                                      ${NF}"
echo -e "${CL}   __  ____      __   __       ____                   ${NF}"
echo -e "${CL}  /  |/  (_)__ _/ /  / /___ __/ __/______ ____  ___   ${NF}"
echo -e "${CL} / /|_/ / / _ \`/ _ \/ __/ // /\ \/ __/ _ \`/ _ \/ -_)${NF}"
echo -e "${CL}/_/  /_/_/\_, /_//_/\__/\_, /___/\__/\_,_/ .__/\__/   ${NF}"
echo -e "${CL}         /___/         /___/            /_/           ${NF}"
echo -e "${CL}                                                      ${NF}\n\n"

echo -e "${CL}This script will install MightyScape Open Source extensions for Inkscape.${NF}"
echo -e "${CL}The target folder to install: $TGT/$GIT_REPO/\n${NF}"

exec 3<>/dev/tty
read -u 3 -p "$(echo -e ${CL}"Do you like to continue? [y/n]\n "${NF})" -n 1 REPLY

if [[ $REPLY =~ ^[Yy]$ ]]; then
    root_test
    sudo_test
    check_base
    preflight
    packages
    setup
    adjust_preferences

    echo -e "${CL}Installation done! ${NF}"
    du -sh $(pwd)
else
    echo -e "${CL}kk thx bye! ${NF}"
fi
