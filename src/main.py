from loginscreen import LoginScreen
from settings import Settings
from mainscreen import MainWindow
from profile import ProfileHelper, tox_factory
import sys
from PySide import QtCore, QtGui
from callbacks import init_callbacks
from bootstrap import node_generator
from util import curr_directory


class login(object):

    def __init__(self, arr):
        self.arr = arr

    def login_screen_close(self, t, number=-1, default=False, name=None):
        """ Function which processes data from login screen
        :param t: 0 - window was closed, 1 - new profile was created, 2 - profile loaded
        :param number: num of choosen profile in list (-1 by default)
        :param default: was or not choosen profile marked as default
        :param name: name of new profile
        """
        print str(t), str(number), str(default), str(name)
        self.t = t
        self.num = number
        self.default = default
        self.name = name

    def get_data(self):
        return self.arr[self.num]


def main():
    """
        main function of app. loads loginscreen if needed and starts mainscreen
    """
    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(curr_directory() + '/images/icon.png'))
    settings = Settings()
    if not settings['auto_profile']:
        # show login screen if default profile not found
        ls = LoginScreen()
        ls.setWindowIconText("Toxygen")
        profiles = ProfileHelper.find_profiles()
        ls.update_select(map(lambda x: x[1], profiles))
        _login = login(profiles)
        ls.update_on_close(_login.login_screen_close)
        ls.show()
        app.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app, QtCore.SLOT("quit()"))
        app.exec_()
        if not _login.t:
            return
        elif _login.t == 1:  # create new profile
            # TODO: test
            name = _login.name if _login.name else 'toxygen_user'
            tox = tox_factory()
            tox.self_set_name('Toxygen User')
            tox.self_set_status('Toxing on Toxygen')
            ProfileHelper.save_profile(tox.get_savedata(), name)
        else:  # load existing profile
            path, name = _login.get_data()
            if _login.default:
                settings['auto_profile'] = (path, name)
                settings.save()
            data = ProfileHelper.open_profile(path, name)
            tox = tox_factory(data, settings)
    else:
        path, name = settings['auto_profile']
        data = ProfileHelper.open_profile(path, name)
        tox = tox_factory(data, settings)

    ms = MainWindow(tox)
    #ms.setup_info_from_tox()
    ms.show()
    # bootstrap
    for data in node_generator():
        tox.bootstrap(*data)
    # initializing callbacks
    init_callbacks(tox, ms)
    # starting thread for tox iterate
    mainloop = ToxIterateThread(tox)
    mainloop.start()

    app.connect(app, QtCore.SIGNAL("lastWindowClosed()"), app, QtCore.SLOT("quit()"))
    app.exec_()
    mainloop.stop = True
    mainloop.wait()
    del tox


class ToxIterateThread(QtCore.QThread):

    def __init__(self, tox):
        QtCore.QThread.__init__(self)
        self.tox = tox
        self.stop = False

    def run(self):
        while not self.stop:
            self.tox.iterate()
            self.msleep(self.tox.iteration_interval())


if __name__ == '__main__':
    # TODO: add command line options?
    main()
