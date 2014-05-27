def open_keyboard(self):

    if sys.platform == 'win32':
        try:
            programfiles = os.environ['ProgramW6432']
        except KeyError:
            programfiles = os.environ['ProgramFiles']

        cmd = r'{path}\Common Files\Microsoft Shared\ink\TabTip.exe'.format(path=programfiles)
        try:
            os.startfile(cmd)
        except WindowsError:
            roam.config.settings['keyboard'] = False
            roam.config.save()
    else:
        cmd = 'onboard'
        Popen(cmd)
