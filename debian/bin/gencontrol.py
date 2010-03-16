#!/usr/bin/python

import sys
sys.path.append(sys.argv[1] + "/lib/python")

from debian_linux.config import ConfigCoreDump
from debian_linux.debian import Changelog, PackageDescription, VersionLinux
from debian_linux.gencontrol import Gencontrol as Base
from debian_linux.utils import Templates

class Gencontrol(Base):
    def __init__(self, config):
        super(Gencontrol, self).__init__(ConfigCoreDump(fp = file(config)), Templates(["debian/templates"]))

        config_entry = self.config['version',]
        self.version = VersionLinux(config_entry['source'])
        self.abiname = config_entry['abiname']
        self.vars = {
            'upstreamversion': self.version.linux_upstream,
            'version': self.version.linux_version,
            'source_upstream': self.version.upstream,
            'major': self.version.linux_major,
            'abiname': self.abiname,
        }

        changelog_version = Changelog()[0].version
        self.package_version = '%s+%s' % (self.version.upstream, changelog_version.complete)

    def do_main_packages(self, packages, vars, makeflags, extra):
        packages['source']['Build-Depends'].extend(
            ['linux-support-%s%s' % (self.version.linux_upstream, self.abiname)]
        )

        latest_source = self.templates["control.source.latest"][0]
        packages.append(self.process_package(latest_source, vars))

        latest_doc = self.templates["control.doc.latest"][0]
        packages.append(self.process_package(latest_doc, vars))

    def do_flavour_packages(self, packages, makefile, arch, featureset, flavour, vars, makeflags, extra):
        config_base = self.config.merge('base', arch, featureset, flavour)
        config_description = self.config.merge('description', arch, featureset, flavour)
        config_image = self.config.merge('image', arch, featureset, flavour)

        vars['class'] = config_description['hardware']
        vars['longclass'] = config_description.get('hardware-long') or vars['class']

        templates = []

        if config_image.get('type', None) == 'plain-xen':
            templates.extend(self.templates["control.image.latest.type-modules"])
        else:
            templates.extend(self.templates["control.image.latest.type-standalone"])
        if config_base.get('modules', True):
            templates.extend(self.templates["control.headers.latest"])

        image_fields = {'Description': PackageDescription()}

        desc_parts = self.config.get_merge('description', arch, featureset, flavour, 'parts')
        if desc_parts:
            desc = image_fields['Description']
            for part in desc_parts[::-1]:
                desc.append(config_description['part-long-' + part])
                desc.append_short(config_description.get('part-short-' + part, ''))

        packages_dummy = []

        packages_dummy.append(self.process_real_image(templates[0], image_fields, vars))
        packages_dummy.append(self.process_real_image(templates[1], image_fields, vars))
        packages_dummy.extend(self.process_packages(templates[2:], vars))

        for package in packages_dummy:
            name = package['Package']
            if packages.has_key(name):
                package = packages.get(name)
                package['Architecture'].append(arch)
            else:
                package['Architecture'] = [arch]
                packages.append(package)

        makeflags['GENCONTROL_ARGS'] = '-v%s' % self.package_version

        cmds_binary_arch = ["$(MAKE) -f debian/rules.real install-dummy DH_OPTIONS='%s' %s" % (' '.join(["-p%s" % i['Package'] for i in packages_dummy]), makeflags)]
        makefile.add('binary-arch_%s_%s_%s_real' % (arch, featureset, flavour), cmds = cmds_binary_arch)

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
                if i.has_key('X-Version-Overwrite-Epoch'):
                    version = '-v1:%s' % self.package_version
                else:
                    version = '-v%s' % self.package_version
                cmds.append("$(MAKE) -f debian/rules.real install-dummy ARCH='%s' DH_OPTIONS='-p%s' GENCONTROL_ARGS='%s'" % (arch, i['Package'], version))
            makefile.add('binary-arch_%s' % arch, ['binary-arch_%s_extra' % arch])
            makefile.add("binary-arch_%s_extra" % arch, cmds = cmds)

    def process_real_image(self, entry, fields, vars):
        entry = self.process_package(entry, vars)
        for key, value in fields.iteritems():
            if key in entry:
                real = entry[key]
                real.extend(value)
            elif value:
                entry[key] = value
        return entry

if __name__ == '__main__':
    Gencontrol(sys.argv[1] + "/config.defines.dump")()
