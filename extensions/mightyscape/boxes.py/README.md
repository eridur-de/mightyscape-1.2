# MightyScape for Inkscape 1.2

**In short**: MightyScape is a maintained extension collection for Inkscape 1.2, working on Windows and Linux. There are **238 extension folders** with **412 .inx files** inside. We also take part at the offical extension gallery with single extension uploads. See https://inkscape.org/gallery/=extension.

# About MightyScape

Looking to get more productive we started using some more special Inkscape extensions. We love Inkscape. And we love things like 3d printing, laser cutting, vinyl cutting, pen plotting, maths, physics, geometry, patterns, 2D drawings, 3D CAD , embroidery and more stuff. All this you can do with Inkscape! We recognized that there is no good source to pull extensions in a quick and clean way. Each developer puts his own code on his hidden/unknown repository and often without enough documentation or visible results for common understanding. Many plugins are completely unknown that way, and a lot of extensions are forked x times or are unmaintained. So many of them do not work with recent Inkscape or were never tested with newer versions so far.

# What and why?

This is a one-to-bundle-them-all collection of hundreds of additional functions to Inkscape (extensions) for the Python 3 based Inkscape version 1.2 including documentation, made for makers and artists. All plugins where sorted into custom categories (to avoid overloading the standard extension menu of Inkscape). You can find most of them in sub menu "FabLab Chemnitz". We renamed and cleaned a lot of *.inx files and *.py files. We applied some function renamings, id changes (for preferences.xml clean-keeping), spelling fixes, formattings and parameter corrections.

It took years to search and find all them on the web (so much different possible sources where to find!), to read, to comment (report issues), to fix problems, to test, to document and to provide them online. Many extensions were nearly lost in translation.

At least this repo will help to bring alife some good things and will show hidden gold. It meshes things together in a fresh and bundled way - with ease of use and minimum installation stress. A lot of code is not at the optimum. A mass of bugs has to be fixed and different tools should be improved in usage generally. This package will show errors more quickly. So hopefully a lot of new code fixes is result from this package. Maybe some people help to make all the stuff compatible with Inkscape 1.2 and newer.

# Credits / Help to develop

* This is not a repository to steal the work of others. The credits go to each developer, maintainer, commiter, issue reporter and so on. Please have a look at the meta.json in each directory to get information about licenses and authors.
* All plugins are open source licensed and are GNU GPL compatible. See https://www.gnu.org/licenses/license-list.html#GPLCompatibleLicenses for more details.
* All plugins were taken from each git repo's master branch (if git/svn available). There might exist some development branches, fork branches or issue comments which might resolve some issues or enhance functionality of provided plugins. To check for recent github forks use https://techgaun.github.io
* A lot of plugins were fixed by ourselves in countless hours
* If you find bugs or have ideas please push them directly to the corresponding root repository of the developer or put it to https://github.com/eridur-de/mightyscape-1.2/issues
* Credits for creation of this big package: Mario Voigt / FabLab Chemnitz

# Used software for development

* Gitea and Github for hosting this
* LiClipse for code and git committing
* regular Python installation (both Linux and Windows)

# Requirements / Tested environment

* tested with Inkscape 1.2.1 and Python 3.10 (64 Bit)
  * Windows portable version
  * Fedora 37
* Python 3.11 is not used because it causes trouble with some modules like lxml or Shapely at the moment
* some extensions require custom Python installation/modules. See documentation at our FabLab Chemnitz Wiki (see below).
* some extensions require additional commands, packages or other installers (see documentation too).

# Installation, documentation and examples

The structure of this repo is intended the be easy. Just copy the complete MightyScape folder or the folders you want to your Inkscape's extension directory. You will find redundancies in this repo like node.exe (NodeJS). We did it this way to give easy possibilty to only pick the extensions you want (instead creating ~200 repositories). MightyScape does not work with any releases or feature branches. Just use "git clone" to get the recent commit from master branch. Please see at https://y.stadtfabrikanten.org/mightyscape-overview for installation tips like required python modules, file locations and other adjustments.

# About older MightyScape versions

Please note there are older MightyScape repositories:

Since Inkscape 1.2 we only work with official releases. In the past we worked with some development versions. This led to some issues with different extension code. This means: for each new major Inkscape release we create a new MightyScape repository too.

# Donate

<img src="./extensions/mightyscape/000_about_fablabchemnitz.svg">

We are the Stadtfabrikanten, running the FabLab Chemnitz since 2016. A FabLab is an open workshop that gives people access to machines and digital tools like 3D printers, laser cutters and CNC milling machines.

You like our work and want to support us? You can donate to our non-profit organization by different ways:
https://y.stadtfabrikanten.org/donate

**Thanks for using our extension and helping us!**

# git Locations

This repo has two remotes:

* https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2 (root repo origin)
* https://github.com/eridur-de/mightyscape-1.2 (repo for collaboration. **Please put your issues here**)

# Zip Archives - Mirrors

If you only want to download single extensions of MightyScape, use one of the following mirrors to do that easily:

* https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2-zipmirror
* https://github.com/eridur-de/mightyscape-1.2-zipmirror