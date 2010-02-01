"""cli.daemon - daemonizing applications

Copyright (c) 2008-2010 Will Maier <will@m.aier.us>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""

from cli.log import LoggingApp

__all__ = ["DaemonizingApp"]

class DaemonizingApp(LoggingApp):
    """A command-line application that knows how to daemonize.
    """

    def __init__(self, main, pidfile=None,
            chdir='/', null="/dev/null", **kwargs):
        self.pidfile = pidfile
        self.chdir = chdir
        self.null = null
        super(DaemonizingApp, self).__init__(main, **kwargs)

    def setup(self):
        super(DaemonizingApp, self).setup()

        # Add daemonizing options.
        self.add_param("-d", "--daemonize", default=False, action="store_true",
                help="run the application in the background")
        self.add_param("-u", "--user", default=None, 
                help="change to USER[:GROUP] after daemonizing")
        self.add_param("-p", "--pidfile", default=None, 
                help="write PID to PIDFILE after daemonizing")

    def daemonize(self):
        """Daemonize the application.
        
        Send the application to the background, redirecting
        stdin/stdout and changing its UID if requested.
        """
        if os.fork(): sys.exit(0)
        os.umask(0) 
        os.setsid() 
        if os.fork(): sys.exit(0)

        self.stdout.flush()
        self.stderr.flush()
        si = open(self.null, 'r')
        so = open(self.null, 'a+')
        se = open(self.null, 'a+', 0)
        os.dup2(si.fileno(), self.stdin.fileno())
        os.dup2(so.fileno(), self.stdout.fileno())
        os.dup2(se.fileno(), self.stderr.fileno())

        if self.args.pidfile:
            self.log.debug("Writing pidfile %s", self.args.pidfile)
            pidfile = open(self.args.pidfile, 'w')
            pidfile.write('%i\n' % os.getpid())
            pidfile.close()

        if self.args.user:
            import grp
            import pwd
            delim = ':'
            user, sep, group = self.args.user.partition(delim)

            # If group isn't specified, try to use the username as
            # the group.
            if delim != sep:
                group = user
            self.log.debug("Changing to %s:%s", user, group)
            os.setgid(grp.getgrnam(group).gr_gid)
            os.setuid(pwd.getpwnam(user).pw_uid)

        self.log.debug("Changing directory to %s", self.chdir)
        os.chdir(self.chdir)

        return True

