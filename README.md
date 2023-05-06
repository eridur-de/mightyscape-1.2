# MightyScape for Inkscape 1.2

<img title="" src="./extensions/fablabchemnitz/000_Mightyscape.svg" alt="" data-align="left">

In short: A maintained extension collection for Inkscape 1.2, working on Windows and Linux. There are **237 extension folders** with **432 .inx files** inside. We also take part at https://inkscape.org/gallery/=extension/ (with single extension uploads).

# About MightyScape

Looking to get more productive we started using some more special Inkscape extensions. We love Inkscape. And we love things like 3d printing, laser cutting, vinyl cutting, pen plotting, maths, physics, geometry, patterns, 2D drawings, 3D CAD , embroidery and more stuff. All this you can do with Inkscape! We recognized that there is no good source to pull extensions in a quick and clean way. Each developer puts his own code on his hidden/unknown repository and often without enough documentation or visible results for common understanding. Many plugins are completely unknown that way, and a lot of extensions are forked x times or are unmaintained. So many of them do not work with recent Inkscape or were never tested with newer versions so far.

# What and why?

This is a one-to-bundle-them-all collection of hundreds of additional functions to Inkscape (extensions) for the new Python 3 based version 1.X including documentation, made  for makers and artists. All plugins where sorted into custom categories  (to avoid overloading the standard extension menu of Inkscape). You can find most of them in sub menu "FabLab Chemnitz". We renamed and cleaned a lot of *.inx files and *.py files. We applied some function renamings, id changes (for preferences.xml clean-keeping), spelling fixes, formattings and parameter corrections.

It took years to search and find all them on the web (so much different possible sources where to find!), to read, to comment (report issues), to fix problems, to test, to document and to provide them online. Many extensions were nearly lost in translation.

At least this repo will help to bring alife some good things and will show hidden gold. It meshes things together in a fresh and bundled way - with ease of use and minimum installation stress. A lot of code is not at the optimum. A mass of bugs has to be fixed and different tools should be improved in usage generally. This package will show errors more quickly. So hopefully a lot of new code fixes is result from this package. Maybe some people help to make all the stuff compatible with Inkscape 1.2 and newer.

# Licensing and credits

* This is not a repository to steal the work of others. The credits go to each developer, maintainer, commiter, issue reporter and so on. Please have a look at the meta.json in each directory to get information about licenses and authors for each extension.
* All plugins are open source licensed and are GNU GPL compatible. See https://www.gnu.org/licenses/license-list.html#GPLCompatibleLicenses for more details.
* All plugins were taken from each git repo's master branch (if git/svn available). There might exist some development branches, fork branches or issue comments which might resolve some issues or enhance functionality of provided plugins. To check for recent github forks use https://techgaun.github.io
* A mass of plugins were fixed by ourselves in countless hours
* Credits for creation of the MightyScape project: Mario Voigt / FabLab Chemnitz

# Used software for development

* Gitea and Github for hosting this
* LiClipse for code and git committing
* regular Python installation (both Linux and Windows)

# Tested environment

* tested with Inkscape
  * Fedora 37: Inkscape 1.2.2 (b0a8486541, 2022-12-01)
  * Windows 10 (@KVM/QEMU): Inkscape 1.2.1 (9c6d41e410, 2022-07-14)
* tested using Python 3.10 / 3.11 64 Bit

# Structure

The structure of this repo is intended the be easy. MightyScape does not work with any releases or feature branches. Just copy the complete MightyScape folder (or the particular folders you want) to your Inkscape's extension directory. You will find redundancies in this repo like node.exe (NodeJS). We did it this way to give easy possibilty to only pick the extensions you want.

# Installation

Please read this first before opening issues! This documentation does not maintain any progressive information about installing or handling Inkscape itself.

## Unsupported Inkscape versions
- Linux
  - MightyScape **does not support the snap version** and also **no** **[AppImage]([https://inkscape.org/release/inkscape-dev/gnulinux/appimage/dl](https://inkscape.org/release/inkscape-dev/gnulinux/appimage/dl/))** version of Inkscape. The snap edition comes with restrictions, letting a lot of extensions fail to work. The reason is missing access to external python interpreters. Libraries like `openmesh` or `pyclipper` cannot be used this way. The AppImage version will fail for a lot extension too, because subprocesses from the AppImage have no acccess to `/tmp` directory. You can still install MightyScape with snap or AppImage version but beware to get different errors. Feel free to contribute solutions to fix these issues.
- Windows
  - Windows App Store (this was not tested yet)

## Supported Inkscape versions
- Windows
  - portable
  - regular installation with MSI Setup
- Linux
  - regular installation from package manager like dnf/yum or apt
    `sudo apt install inkscape #Ubuntu`
    `sudo dnf install inkscape #Fedora`
- MacOS
  - this was never tested. We are sorry!

## Installation of prerequisites - python interpreter

MightyScape relies on the Python interpreter which is used by the OS. As we need to install some external dependencies (python modules, partially with C bindings), we cannot rely on the bundled Python version, which comes with Inkscape. For this reason we need to adjust the main configuration of inkscape to apply this change by adding `python-interpreter`.
**Note:** Using a custom Python environment on Windows wil make the official Inkscape Extensions Manager impossible to run. The reason is the library `pygobject`.

**On Linux this might look like:**

```
vim ~/.config/inkscape/preferences.xml
```
```
  <group
     id="extensions"
     python-interpreter="/usr/bin/python"
```

**On Windows this might look like:**

```
notepad %appdata%\inkscape\preferences.xml
```

```
  <group
     id="extensions"
     python-interpreter="C:\Users\youruser\AppData\Local\Programs\Python\Python310\pythonw.exe"
```

**Notes for Windows users:** 

* If you get a nasty popup window each time you are executing an extension, please double check if you really use `pythonw.exe`. Do not use `python.exe`.
* You can download and install Python for Windows from https://www.python.org/downloads/windows
* please review for correct enviroment variable adjustments. `python.exe` has to be in `%PATH%`

## Installation of prerequisites - additional python modules

The following extra libraries are required for some of the extensions within the MightyScape package. Those are listed in our [requirements.txt](https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2/requirements.txt) file. We are installing them together with MightyScape in the next section.


**Note:** if `openmesh` fails to install, please see [Paperfold](https://stadtfabrikanten.org/display/IFM/Paperfold) for more details about installing it.

## Installation dirs

There are two places where Inkscape extensions can be located by default, either install (global) directory or user directory. We usually put the extensions in the user's data directories directory, because if we would put it to the installation folder of Inkscape, we would risk deletion by upgrading. If we put them to the user directory we do not lose them.

| OS                     | user directory                   | global directory                        |
| ---------------------- | -------------------------------- | --------------------------------------- |
| Linux (Ubuntu, Fedora) | `~/.config/inkscape/extensions/` | `/usr/share/inkscape/extensions/`       |
| Windows                | `%AppData%\inkscape\extensions\` | `C:\Program Files\inkscape\extensions\` |

## Installation way 1: with git dependencies (preferred way)

**On Linux this might look like:**

```
dnf install python3-devel #this might be required on Fedora
cd  ~/.config/inkscape/extensions/
git clone https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2.git
python -m pip install --upgrade pip #upgrade pip first
pip install --upgrade  --quiet --no-cache-dir -r ~/.config/inkscape/extensions/requirements.txt
```

**On Windows this might look like:**

```
cd %AppData%\inkscape\extensions\
git clone https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2.git
cd %AppData%\..\Local\Programs\Python\Python310\Scripts
python -m pip install --upgrade pip #upgrade pip first
pip install --upgrade  --quiet --no-cache-dir -r %AppData%\inkscape\extensions\requirements.txt
```

**Note about git handling**: You can also download the whole git project as .zip or .tar.gz bundled archive and then place it to your target directory. This way you can ignore installing git on your system yet. You can convert that directory to the git-way using the [upgrade extension]([mightyscape-1.2/about_upgrade_mightyscape an master - mightyscape-1.2 - FabLab Chemnitz - Gitea: Git with a cup of tea](https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2/src/branch/master/extensions/fablabchemnitz/about_upgrade_mightyscape)) later on.
 <img title="" src="./docs/images/zip-download.png" alt="" data-align="left">

## Installation way 2: with zip archives (mirrors)

If you only want to download single parts of MightyScape, use one of the following mirrors:

* https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2-zipmirror
* https://github.com/eridur-de/mightyscape-1.2-zipmirror

You can put the extracted files into your local or global Inkscape extension directory. Please refer to the [official documentation](https://inkscape-manuals.readthedocs.io/en/latest/extensions.html#installing-extensions).

## Upgrading MightyScape

There are two ways to upgrade MightyScape. Choose from:

1. if you installed MightyScape using git clone, just go to the git directory and run `git pull` or use the extension "Upgrade MightyScape", which can be found in Extensions → FabLab Chemnitz → Upgrade MightyScape
   - There is some special updater extension which allows to update the complete MightyScape package once it was properly pulled by git. You need to install `GitPython` library to use the updater:
<img title="" src="./docs/images/upgrade-extension.png" alt="" data-align="left">

2. if you previously downloaded a bulk zip file from github or gitea, just replace the content of the containing folder with the new files

## Upgrading Python modules

Sometimes it can help to upgrade python modules. This section shows some useful shell lines (**but be warned to use them on your own risk**):

```
pip list --outdated

#Linux: 
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U 

#Windows: 
for /F "delims= " %i in ('pip list --outdated') do pip install -U %i
```

# Issues, questions, documentation, examples

This repo has two remotes:

* https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2 (root repo origin from our organization)
* https://github.com/eridur-de/mightyscape-1.2 (repo for **public collaboration**) 

You can create your issues and questions **[here](https://github.com/eridur-de/mightyscape-1.2/issues)**

You find a lot of documentation at the sub pages of https://y.stadtfabrikanten.org/mightyscape-overview. Please have a look there first (make use of the search function).

# Support us by a small donation

<img title="" src="./extensions/fablabchemnitz/000_about_fablabchemnitz.svg" alt="" data-align="left">

We are the Stadtfabrikanten, running the FabLab Chemnitz since 2016. A FabLab is an open workshop that gives people access to machines and digital tools like 3D printers, laser cutters and CNC milling machines.

You like our work and want to support us? You can donate to our non-profit organization by different ways:
https://y.stadtfabrikanten.org/donate

Each penny helps us to keep this project alive.

**Thanks for using our extension and helping us!**
