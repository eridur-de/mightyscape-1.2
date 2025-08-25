#!/usr/bin/env python3

"""
Upgrade MightyScape from Inkscape Extension Dialog. Made for end users

Extension for Inkscape 1.3.2
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 14.01.2024
Last patch: 25.08.2025
License: GNU GPL v3

ToDo
    - add routine to check for differences between remotes (unequal commits)
"""

import inkex
import os
import subprocess
from subprocess import Popen, PIPE
import warnings
from datetime import datetime, timezone
from lxml import etree

prefs = os.path.join(os.environ['INKSCAPE_PROFILE_DIR'], "preferences.xml")
doc = etree.parse(prefs)
for element in doc.xpath("//inkscape/group[@id=\"extensions\"]/@python-interpreter", namespaces=inkex.NSS):
    python_interpreter = element
    break
inkex.utils.debug("Your config file: {}\n".format(prefs))
inkex.utils.debug("Configured attribute 'python-interpreter': {}\n".format(python_interpreter))
python_interpreter_abs = os.path.isabs(python_interpreter)
if python_interpreter_abs is False:
    inkex.utils.debug("Warning: python-interpreter path is not absolute. \
This might lead to failure of extension execution! Please do not use \
relative paths like '~/.config/inkscape/extensions/mightyscape-1.2/venv/bin/python3'. \
Instead use '/home/YOURUSER/.config/inkscape/extensions/mightyscape-1.2/venv/bin/python3'\n")

try:
    import git
    from git import Repo #requires GitPython lib
except:
    inkex.utils.debug("Error. GitPython was not installed but is required to run the upgrade process!")
    exit(1)

class AboutUpgradeMightyScape(inkex.EffectExtension):

    restart = False

    def install_requirements(self):
        requirements = os.path.abspath(os.path.join(self.ext_path()) + "/../../../requirements.txt")
        if not os.path.exists(requirements):
            inkex.utils.debug("requirements.txt could not be found.")
            exit(1)

        if os.name=="nt":
            python_venv = os.path.abspath(os.path.join(os.path.dirname(git.__file__), '../', '../', '../', '../', 'venv', 'Scripts', 'python.exe'))
        else: #Linux/MacOS
            python_venv = os.path.abspath(os.path.join(os.path.dirname(git.__file__), '../', '../', '../', '../', 'bin', 'python'))
        command = "{} -m pip install --upgrade --no-cache-dir -r {}".format(python_venv, requirements)
        inkex.utils.debug("Executing: {}".format(command))
        proc = subprocess.Popen(command, shell=True, stdout=PIPE, stderr=PIPE, encoding="UTF-8")
        stdout, stderr = proc.communicate()
        try:
            inkex.utils.debug(stdout)
            inkex.utils.debug(stderr)
        except:
            pass
        
        proc.wait()

    def update(self, local_repo, remote, localCommitCount):
        inkex.utils.debug("Chosen remote is: {}".format(remote))
        try:
            localCommit = local_repo.head.commit
            remote_repo = git.remote.Remote(local_repo, remote)
            remoteCommit = remote_repo.fetch()[0].commit
            inkex.utils.debug("Latest remote commit is: " + str(remoteCommit)[:7])
            remoteCommitCount = 0 
            for c in remote_repo.repo.iter_commits('origin/master'):
                remoteCommitCount += 1
            inkex.utils.debug("Commits at remote: {}".format(remoteCommitCount))
                
            if localCommit.hexsha != remoteCommit.hexsha:
                ssh_executable = 'git'
                with local_repo.git.custom_environment(GIT_SSH=ssh_executable):
                    #origin = local_repo.remotes.origin
                    #origin.fetch()
                    #fetch_info = origin.pull() #finally pull new data
                    fetch_info = remote_repo.fetch()
                    remote_repo.pull() #finally pull new data
    
                    for info in fetch_info: #should return only one line in total
                        inkex.utils.debug("Updated {} to commit id {}. {} commits were pulled".format(info.ref, str(info.commit)[:7], remoteCommitCount - localCommitCount))    
                    self.restart = True
            else:
                self.restart = False
                   
        except git.exc.GitCommandError as e:
            inkex.utils.debug("git command failed. Please save or stash your local git changes first and try again. You can enable 'Stash untracked files' to continue. This will also reset your branch to master.")
            inkex.utils.debug("Error was: {}".format(str(e)))
            return False
        return True

   
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--install_requirements", type=inkex.Boolean, default=False, help="Install python requirements")
        pars.add_argument("--convert_to_git", type=inkex.Boolean, default=False, help="If you downloaded MightyScape as .zip or .tar.gz you cannot upgrade using this extension. But you can convert your downloaded directory to a .git one by enabling this option")
        pars.add_argument("--recreate_remotes", type=inkex.Boolean, default=False, help="Update remotes in git config file (useful if you have an older version of MightyScape or if sth. changes)")
        pars.add_argument("--stash_untracked", type=inkex.Boolean, default=False, help="Stash untracked files and continue to upgrade")
        
    
    def effect(self):
        
        global so
        so = self.options
        
        warnings.simplefilter('ignore', ResourceWarning) #suppress "enable tracemalloc to get the object allocation traceback"

        if so.install_requirements is True:
            self.install_requirements()

        #get the directory of mightyscape
        extension_dir = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../')) #go up to main dir /home/<user>/.config/inkscape/extensions/mightyscape-1.2/
        main_dir = os.path.abspath(os.path.join(extension_dir, '../../')) #go up to main dir /home/<user>/.config/inkscape/extensions/mightyscape-1.2/

        #create some statistics
        totalFolders = 0
        for root, folders, files in os.walk(extension_dir):
            totalFolders += len(folders)                        
            break #prevent descending into subfolders
        
        totalInx = 0
        for root, folders, files in os.walk(extension_dir):
            for file in files:    
                if file.endswith('.inx'):
                    totalInx += 1
        
        inkex.utils.debug("Locally there are {} extension folders with {} .inx files!\n".format(totalFolders, totalInx))

        remotes = []
        remotes.append(["https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.2.git", "origin"]) #main
        remotes.append(["https://github.com/eridur-de/mightyscape-1.2.git", "github"]) #copy/second remote
            
        gitDir = os.path.join(main_dir, ".git")
        
        if not os.path.exists(gitDir):
            if so.convert_to_git is True:
                local_repo = Repo.init(main_dir)
                local_repo.git.add(all=True)
                localRemotes = []
                for remote in remotes:
                    localRemotes.append(local_repo.create_remote(remote[1], url=remote[0]))
                localRemotes[0].update()
                local_repo.index.commit('.')
                local_repo.git.checkout('origin/master')
            else:
                inkex.utils.debug("MightyScape .git directory was not found. It seems you installed MightyScape the traditional way (by downloading and extracting from archive). Please install MightyScape using the git clone method if you want to use the upgrade function. More details can be found in the official README.")
                exit(1)
        
        local_repo = Repo(gitDir)
      
        #drop local changed. update might fail if file changes are present
        if so.stash_untracked is True:
            local_repo.git.stash('save')
            local_repo.git.checkout('master')
            self.restart = True
            #local_repo.git.checkout('origin/master')
        
        existingRemotes = [] #check for existing remotes. if one is missing, add it (or delete and recreate)
        for r in local_repo.remotes:
            existingRemotes.append(str(r))
        for remote in remotes:
            if remote[1] not in existingRemotes:
                local_repo.create_remote(remote[1], url=remote[0])
            if so.recreate_remotes is True: #delete and then recreate
                local_repo.delete_remote(remote[1])
                local_repo.create_remote(remote[1], url=remote[0])
                    
        #check if it is a non-empty git repository
        if local_repo.bare is False:
            if local_repo.is_dirty(untracked_files=True) is False:        
                if len(local_repo.untracked_files) > 0:
                    if so.stash_untracked is True:
                        local_repo.git.stash('save')
                    else:
                        inkex.utils.debug("There are some untracked files in your MightyScape directory. Still trying to pull recent files from git...")
              
            localLatestCommit = local_repo.head.commit
            localCommits = list(local_repo.iter_commits("origin/master", skip=0))
            localCommitCount = len(localCommits)
            inkex.utils.debug("Local commit id is: " + str(localLatestCommit)[:7])
            inkex.utils.debug("There are {} local commits at the moment.".format(localCommitCount))
            localCommits = localCommits[:10] #get only last ten commits
            localCommitList = []
            for localCommit in localCommits:
                localCommitList.append(localCommit)
            #localCommitList.reverse()
            inkex.utils.debug("*"*40)
            inkex.utils.debug("Latest {} local commits are:".format(len(localCommits)))
            for i in range(0, len(localCommits)):
                inkex.utils.debug("{} | {} : {}".format(
                    datetime.fromtimestamp(localCommitList[i].committed_date, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    localCommitList[i].name_rev[:7],
                    localCommitList[i].message.strip())
                    )   
                #inkex.utils.debug(" - {}: {}".format(localCommitList[i].newhexsha[:7], localCommitList[i].message))   
            inkex.utils.debug("*"*40)
            
            #finally run the update
            success = self.update(local_repo, remotes[0][1], localCommitCount)
            if success is False: #try the second remote if first failed
                inkex.utils.debug("Error receiving latest remote commit from main git remote {}. Trying second remote ...".format(remotes[0][0]))
                success = self.update(local_repo, remotes[1][1], localCommitCount)
            if success is False: #if still false:
                inkex.utils.debug("Error receiving latest remote commit from second git remote {}.\nAre you offline? Cannot continue!".format(remotes[0][0]))
                exit(1)
        
            if self.restart is True:
                inkex.utils.debug("Please restart Inkscape to let all changes take effect.")
            else:
                inkex.utils.debug("Nothing to do! MightyScape is already up to date!")
                
        else:
            inkex.utils.debug("No \".git\" directory found. Seems your MightyScape was not installed with git clone. Please see documentation on how to do that.")  
            exit(1)

if __name__ == '__main__':
    AboutUpgradeMightyScape().run()