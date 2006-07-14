#!/usr/bin/env python2.4
import sys
sys.path.append(sys.argv[1]+ "/lib/python")
import debian_linux.gencontrol
from debian_linux.config import *
from debian_linux.debian import *

class gencontrol(debian_linux.gencontrol.gencontrol):
    def __init__(self, config):
        super(gencontrol, self).__init__(config)
        self.process_config_version(config_parser({}, [sys.argv[1] + "/version"]))
        self.process_changelog_version()

    def do_flavour_packages(self, packages, makefile, arch, subarch, flavour, vars, makeflags, extra):
        image_latest = self.templates["control.image.latest"]
        headers_latest = self.templates["control.headers.latest"]

        packages_dummy = []
        packages_dummy.extend(self.process_packages(image_latest, vars))
        packages_dummy.extend(self.process_packages(headers_latest, vars))

        for package in packages_dummy:
            name = package['Package']
            if packages.has_key(name):
                package = packages.get(name)
                package['Architecture'].append(arch)
            else:
                package['Architecture'] = [arch]
                packages.append(package)

        makeflags['GENCONTROL_ARGS'] = '-v%s' % self.version['source']
        makeflags_string = ' '.join(["%s='%s'" % i for i in makeflags.iteritems()])

        cmds_binary_arch = []
        cmds_binary_arch.append(("$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='%s' %s" % (' '.join(["-p%s" % i['Package'] for i in packages_dummy]), makeflags_string),))
        makefile.append(("binary-arch-%s-%s-%s-real:" % (arch, subarch, flavour), cmds_binary_arch))
        makefile.append(("build-%s-%s-%s-real:" % (arch, subarch, flavour)))

    def do_extra(self, packages, makefile):
        templates_extra = self.templates["control.extra"]

        packages.extend(self.process_packages(templates_extra, {}))
        extra_arches = {}
        for package in templates_extra:
            arches = package['Architecture']
            for arch in arches:
                i = extra_arches.get(arch, [])
                i.append(package)
                extra_arches[arch] = i
        archs = extra_arches.keys()
        archs.sort()
        for arch in archs:
            cmds = []
            for i in extra_arches[arch]:
                tmp = []
                if i.has_key('X-Version-Overwrite-Epoch'):
                        tmp.append("-v1:%s" % self.version['source'])
                cmds.append("$(MAKE) -f debian/rules.real install-dummy ARCH='%s' DH_OPTIONS='-p%s' GENCONTROL_ARGS='%s'" % (arch, i['Package'], ' '.join(tmp)))
            makefile.append("binary-arch-%s:: binary-arch-%s-extra" % (arch, arch))
            makefile.append(("binary-arch-%s-extra:" % arch, cmds))

    def process_changelog_version(self):
        changelog_version = read_changelog()[0]['Version']
        # HACKALARM
        self.version['source'] = '%s+%s' % (self.version['upstream'], changelog_version)

    def process_config_version(self, config):
        entry = config['version',]
        self.process_version(parse_version(entry['source']))
        self.vars['abiname'] = self.abiname = entry['abiname']

# HACKALARM
def read_changelog(dir = ''):
    r = re.compile(r"""
^
(
(?P<header>
    (?P<header_source>
        \w[-+0-9a-z.]+
    )
    \ 
    \(
    (?P<header_version>
        [^\(\)\ \t]+
    )
    \)
    \s+
    (?P<header_distribution>
        [-0-9a-zA-Z]+
    )
    \;
)
)
""", re.VERBOSE)
    f = file(os.path.join(dir, "debian/changelog"))
    entries = []
    act_upstream = None
    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip('\n')
        match = r.match(line)
        if not match:
            continue
        if match.group('header'):
            e = {}
            e['Distribution'] = match.group('header_distribution')
            e['Source'] = match.group('header_source')
            e['Version'] = match.group('header_version')
            entries.append(e)
            break
    return entries

if __name__ == '__main__':
    gencontrol(sys.argv[1] + "/arch")()
