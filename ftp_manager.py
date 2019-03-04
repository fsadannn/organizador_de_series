import ftplib
import ftputil


class MySession(ftplib.FTP):

    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)


#ftputil.FTPHost(host, userid, password, port=port, session_factory=MySession)
