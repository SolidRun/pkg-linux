#!/usr/bin/env python

import sys
sys.path.append(sys.argv[1] + "/lib/python")

from debian_linux.config import ConfigCoreDump, ConfigParser, SchemaItemList
from debian_linux.debian import *
from debian_linux.gencontrol import Gencontrol as Base, Makefile, PackagesList
from debian_linux.utils import Templates

class Gencontrol(Base):
    def __init__(self, config):
        super(Gencontrol, self).__init__(
            Config(config),
            Templates(["debian/templates",
                       "/usr/src/linux-support-all/modules/templates"]))
        self.process_changelog()

    def __call__(self):
        packages = PackagesList()
        makefile = Makefile()

        self.vars = {}
        self.do_source(packages)

        self.select_version(self.config['version',]['source'],
                            self.config['version',]['abiname'],
                            True)
        self.do_main(packages, makefile)
        self.do_extra(packages, makefile)

        for version in argv[2:]:
            self.select_version(version, version[version.rindex('-'):], False)
            self.do_main(packages, makefile)
            self.do_extra(packages, makefile)

        self.write(packages, makefile)

    def do_main_setup(self, vars, makeflags, extra):
        super(Gencontrol, self).do_main_setup(vars, makeflags, extra)
        makeflags.update({
            'VERSION_SOURCE': self.package_version.upstream,
            'VERSION_REVISION': self.package_version.revision,
            'MAJOR': self.version.linux_major,
            'UPSTREAMVERSION': self.version.linux_upstream,
            'ABINAME': self.abiname,
        })

    def do_main_makefile(self, makefile, makeflags, extra):
        makefile.add("binary-indep")

    def do_main_packages(self, packages, vars, makeflags, extra):
        packages['source']['Build-Depends'].extend(
            ['linux-headers-%s%s-all-%s [%s]' % (self.version.linux_upstream, self.abiname, arch, arch)
            for arch in self.config['base',]['arches']],
        )

    def do_flavour(self, packages, makefile, arch, featureset, flavour, vars, makeflags, extra):
        config_entry = self.config['module', 'base']

        config_base = self.config.merge('base', arch, featureset, flavour)
        if not config_base.get('modules', True):
            return

        super(Gencontrol, self).do_flavour(packages, makefile, arch, featureset, flavour, vars, makeflags, extra)

        for module in iter(config_entry['modules']):
            self.do_module(module, packages, makefile, arch, featureset, flavour, vars.copy(), makeflags.copy(), extra)

    def do_module(self, module, packages, makefile, arch, featureset, flavour, vars, makeflags, extra):
        config_entry = self.config['module', 'base', module]
        vars.update(config_entry)
        vars['module'] = module
        makeflags['MODULE'] = module

        if not vars.get('longdesc', None):
            vars['longdesc'] = ''

        if arch not in config_entry.get('arches', [arch]):
            return
        if arch in config_entry.get('not-arches', []):
            return
        if featureset not in config_entry.get('featuresets', [featureset]):
            return
        if featureset in config_entry.get('not-featuresets', []):
            return
        if flavour not in config_entry.get('flavours', [flavour]):
            return
        if flavour in config_entry.get('not-flavours', []):
            return

        modules = self.templates["control.modules"]
        if self.is_latest:
            # Do not use += as that will modify control.modules
            modules = modules + self.templates["control.modules.latest"]
        modules = self.process_packages(modules, vars)

        for package in modules:
            name = package['Package']
            if packages.has_key(name):
                package = packages.get(name)
                package['Architecture'].append(arch)
            else:
                package['Architecture'] = [arch]
                packages.append(package)

        abi_version = self.version.linux_upstream + self.abiname

        for i in self.makefile_targets:
            target1 = '_'.join((i, abi_version, arch, featureset, flavour))
            target2 = '_'.join((target1, module))
            makefile.add(target1, [target2])

        cmds_binary_arch = ["$(MAKE) -f /usr/src/linux-support-all/modules/rules.real binary-arch %s" % makeflags]
        cmds_build = ["$(MAKE) -f /usr/src/linux-support-all/modules/rules.real build %s" % makeflags]
        cmds_setup = ["$(MAKE) -f /usr/src/linux-support-all/modules/rules.real setup %s" % makeflags]
        makefile.add("binary-arch_%s_%s_%s_%s_%s" % (abi_version, arch, featureset, flavour, module), cmds = cmds_binary_arch)
        makefile.add("build_%s_%s_%s_%s_%s" % (abi_version, arch, featureset, flavour, module), cmds = cmds_build)
        makefile.add("setup_%s_%s_%s_%s_%s" % (abi_version, arch, featureset, flavour, module), cmds = cmds_setup)

    def process_changelog(self):
        self.package_version = self.changelog[0].version

    def select_version(self, version, abiname, is_latest):
        self.version = VersionLinux(version)
        self.abiname = abiname
        self.is_latest = is_latest
        self.vars = {
            'upstreamversion': self.version.linux_upstream,
            'version': self.version.linux_version,
            'source_upstream': self.version.upstream,
            'major': self.version.linux_major,
            'abiname': self.abiname,
        }
        # TODO: select flavours & featuresets for this version

class Config(ConfigCoreDump):
    config_suffix = '.linux-support'

    schemas_module = {
        'base': {
            'arches': SchemaItemList(),
            'flavours':  SchemaItemList(),
            'not-arches': SchemaItemList(),
            'not-flavours':  SchemaItemList(),
            'not-featuresets': SchemaItemList(),
            'featuresets': SchemaItemList(),
        }
    }

    def __init__(self, config):
        super(Config, self).__init__(fp = file(config))

        self._read_modules()

    def _read_modules(self):
        modules = [name[:-len(self.config_suffix)]
                   for name in os.listdir('debian')
                   if name.endswith(self.config_suffix)]
        self[('module', 'base')] = {'modules': modules}

        for module in modules:
            self._read_module(module)

    def _read_module(self, module):
        config = ConfigParser(self.schemas_module)
        config.read('debian/%s%s' % (module, self.config_suffix))

        for section in iter(config):
            real = ('module', section[-1], module) + section[1:]
            s = self.get(real, {})
            s.update(config[section])
            self[real] = s

if __name__ == '__main__':
    Gencontrol(sys.argv[1] + "/config.defines.dump")()
