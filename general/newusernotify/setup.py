# -*- coding: utf-8 -*-

# A simple setup script to create an executable that includes
# the python-swiftclient and easygui. 

import sys
import requests.certs
from cx_Freeze import setup, Executable

base = None
basegui = None
if sys.platform == 'win32':
    basegui = 'Win32GUI'
    #if 'bdist_msi' in sys.argv:
    #    sys.argv += ['--initial-target-dir', 'C:\\Program Files\\OpenStack\\Swift']

options = {
    'build_exe': {
        'packages': [],
        'includes': [],
        'excludes': [],
        'include_files':[(requests.certs.where(),'cacert.pem'),'README.md'],
        'compressed': True,
        #'path': sys.path + ['modules'],
        'include_msvcr': True,
        'icon': 'newuser.ico'
    },
    'bdist_msi': {
        'upgrade_code': '{1AEF9B5A-D776-4224-C8D3-EBB1B7871241}',
        'add_to_path': False,
        'initial_target_dir': 'C:\\Program Files\\FHCRC\\NewUserNotifier',
    }
}

##bdist_msi_options = {
##    'upgrade_code': '{66620F3A-DC3A-11E2-B341-002219E9B01E}',
##    'add_to_path': False,
##    'initial_target_dir': r'[ProgramFilesFolder]\%s\%s' % (company_name, product_name),
##    }
##
##build_exe_options = {
##    'includes': ['atexit', 'PySide.QtNetwork'],
##    }

##setup(name=product_name,
##      version='1.0.0',
##      description='blah',
##      executables=[exe],
##      options={
##          'bdist_msi': bdist_msi_options,
##          'build_exe': build_exe_options})
##

executables = [
    Executable(
               script='NewUserNotify.py',
               shortcutName='New User Notifier',
               shortcutDir='ProgramMenuFolder',
               #targetDir='OpenStack\\Swift',
               base=basegui),
]

setup(name='New User Notifier',
      version='0.9',
      description='send notifications for new AD users',
      options=options,
      executables=executables
      )
