from gocept.munin.client import SimpleMultiGraph, main
from urllib import urlencode
from munin.zope.memory import vmkeys
from os.path import isdir, basename, abspath, normpath, join, exists
from os import environ, getcwd, symlink
from inspect import isclass
from socket import gethostname
from sys import argv


class zodbactivity(SimpleMultiGraph):
    keys = ['total_load_count', 'total_store_count', 'total_connections']
    names = ['Total_objects_loaded', 'Total_objects_stored',
             'Total_connections']
    title = 'ZODB Activity'
    category = 'Zope'


class zopecache(SimpleMultiGraph):
    keys = ['total_objs', 'total_objs_memory', 'target_number']
    names = ['Total_objects_in_database', 'Total_objects_in_all_caches',
             'Target_number_to_cache']
    title = 'Zope cache parameters'
    category = 'Zope'


class zopethreads(SimpleMultiGraph):
    keys = ['total_threads', 'free_threads']
    names = ['Total_threads', 'Free_threads']
    title = 'Z2Server threads'
    category = 'Zope'


keys = vmkeys()


class zopememory(SimpleMultiGraph):
    keys = keys
    names = keys
    title = 'Zope memory usage'
    category = 'Zope'


def initFilestorages(filestorages):
    def factory(base, filestorage):
        class newclass(base):
            def __init__(self, url, authorization, index):
                self.url = (
                    url % base.__name__ +
                    ('?' in url and '&' or '?') +
                    urlencode({'filestorage': filestorage}) +
                    '&name=%s'  # dummy argument for gocept.munin.client.GraphBase._prepare_fetch
                )
                self.authorization = authorization
                self.index = index
        # newclass.__name__ = "zodbactivity-%s" % filestorage.replace('_', '-')
        # newclass.__module__ = "munin.zope.plugins"
        return newclass
    for filestorage in filestorages:
        for plugin in [zodbactivity, zopecache]:
            classname = '%s-%s' % (plugin.__name__, filestorage.replace('_', '-'))
            globals()[classname] = factory(plugin, filestorage)
            globals()[classname].__name__ = classname


def install(script, cmd, path, prefix=None, suffix=None):
    """ set up plugin symlinks using the given prexix/suffix or the
        current hostname and directory """
    assert isdir(path), 'please specify an existing directory'
    if prefix is None:
        prefix = gethostname()
    if suffix is None:
        suffix = basename(getcwd())
    source = abspath(script)
    for name, value in globals().items():
        if isclass(value) and value.__module__ == __name__:
            plugin = '_'.join((prefix, name, suffix))
            target = normpath(join(path, plugin))
            if not exists(target):
                symlink(source, target)
                print 'installed symlink %s' % target
            else:
                print 'skipped existing %s' % target


def run(ip_address='localhost', http_address=8080, port_base=0, user=None,
        secret=None):
    if 3 <= len(argv) <= 5 and argv[1] == 'install':
        return install(*argv)
    port = int(http_address) + int(port_base)
    host = '%s:%d' % (ip_address, port)
    if not 'URL' in environ:
        environ['URL'] = 'http://%s/@@munin.zope.plugins/%%s' % host
    if not 'AUTH' in environ and user is not None:
        environ['AUTH'] = user
    if secret is not None:
        environ['URL'] = 'http://%s/@@munin.zope.plugins/%%s?secret=%s' % (host, secret)
    main()
