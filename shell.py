import cmd
import os

from modules.folders_enum import FoldersEnum
from modules.cvs import CVS
from modules.helpers import Helpers
from modules.cvs_objects import Tree, TreeObjectData, Blob


class CVSShell(cmd.Cmd):
    intro = 'test'
    prompt = None

    def __init__(self):
        super(CVSShell, self).__init__()
        self.cvs = None
        self.path_to_repository = None
        self.working_directory = os.getcwd()
        self.do_cd(self.working_directory)

    def do_init(self, arg: str):
        '''Initialize repository'''
        if CVS.is_repository_exists(self.working_directory):
            return

        self.cvs = CVS(self.working_directory)
        self.cvs.initialize_repository()
        self.path_to_repository = self.working_directory

        print(f'initialized repository at {self.working_directory}')

    def do_commit(self, arg: str):
        '''Create a new commit'''
        self.cvs.make_commit()

    def do_status(self, arg: str):
        '''Show an index'''
        if not self.path_to_repository:
            print('not a repository')
            return

        self.cvs.update_index()
        staged_filter = lambda x: x not in self.cvs.index.staged
        for new in filter(staged_filter, self.cvs.index.new):
            print(f'new: {new}')
        for removed in filter(staged_filter, self.cvs.index.removed):
            print(f'removed: {removed}')
        for modified in filter(staged_filter, self.cvs.index.modified):
            print(f'modified: {modified}')
        for staged in self.cvs.index.staged:
            print(f'staged: {staged}')

    def do_add(self, arg: str):
        '''Add specified file to a commit'''
        self.cvs.update_index()
        if arg == '.':
            to_add = os.listdir('modules')
        else:
            to_add = arg.split(' ')
        for path in map(lambda path: os.path.join(self.path_to_repository, path), to_add):
            is_removed = not os.path.exists(path)
            if os.path.isdir(path) or is_removed and path.endswith(os.path.sep):
                data = TreeObjectData(os.path.join(path, ''), Tree, is_removed=is_removed)
            else:
                data = TreeObjectData(path, Blob, is_removed=is_removed)
            self.cvs.add_to_staged(data)

    def do_ls(self, arg: str):
        '''Show all files in specified directory'''
        for item in os.listdir(self.working_directory):
            print(item)

    def do_cd(self, arg: str):
        '''Change working directory'''
        directory = os.path.abspath(arg)
        if not os.path.exists(directory):
            print(f'can not find directory: {directory}')
            return

        self._set_working_directory(directory)
        if CVS.is_repository_exists(directory):
            # перешли в папку с репозиторием
            self.cvs = CVS(directory)
            self.cvs.initialize_repository()
            self.path_to_repository = directory
        elif self.path_to_repository \
                and os.path.commonprefix([directory, self.path_to_repository]) != self.path_to_repository:
            # покинули папку с репозиторием
            self.cvs = None
            self.path_to_repository = None

    def do_mkdir(self, arg: str):
        '''Create new directory'''
        try:
            os.mkdir(os.path.abspath(arg))
        except FileExistsError:
            print(f'directory {os.path.realpath(arg)} already exists')

    def do_reset(self, arg):
        '''Move head and current branch to specified commit'''
        try:
            commit = self.cvs.get_commit_by_hash(arg)
        except FileNotFoundError:
            print(f'can not find commit with hash {arg}')
            return
        head, branch = self.cvs.move_head_to_commit(commit)
        self.cvs.head = head
        self.cvs.store_head()
        if branch:
            self.cvs.store_branch(branch)

    def _set_working_directory(self, directory: str):
        self.working_directory = os.path.abspath(directory)
        os.chdir(self.working_directory)
        CVSShell.prompt = f'{self.working_directory}$ '


if __name__ == '__main__':
    CVSShell().cmdloop()
