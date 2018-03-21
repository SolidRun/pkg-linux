# This is a deb build tree for the Linux Kernel, utilizing debhelper.

## Branches - pay attention, there are many!
- master: This is the template branch for shared packaging logic, where everything is forked from. If you are looking to work on the kernel, find the right branch for you from this very list!
- 4.9.y-clearfog: 4.9 based, for Clearfog
- 4.9.y-imx6: 4.9 based, for i.MX6 Cubox-i, Hummingboard and Hummingboard 2
### No longer maintained:
- 3.10.y-marvell-clearfog: original version by Marvell for the Clearfog
- 3.14.y-fslc-imx6: 3.14 based i.MX6 Cubox-i, Hummingboard and Hummingboard 2
- 3.14.y-fslc-imx6_wheezy: ^^ with hacks for Wheezy
- 4.4.y-clearfog: 4.4 based, for Clearfog
- 4.4.y-marvell-8040: original version by Marvell for the MACCHIATObin

## Cross-Compiling for armhf:  
1.  Install Cross-Compiler for armhf (starting from Stretch, follow the "For unstable" section):  
    [https://wiki.debian.org/CrossToolchains#Installation](https://wiki.debian.org/CrossToolchains#Installation)
2.  install build dependencies:  
    ```bash
    sudo apt-get install debhelper bc lzop linux-libc-dev
3.  Get the Code:  
    ```bash
    git clone --branch <name_branch_here> https://github.com/mxOBS/deb-pkg_kernel-xyz.git
    cd deb-pkg_kernel-xyz
    git submodule update --init
4.  build deb:  
    ```bash
    cd deb-pkg_kernel-xyz
    dpkg-buildpackage -a armhf -b

## Building natively on armhf:
1.  install build dependencies:  
    ```bash
    sudo apt-get install debhelper bc lzop
2.  Get the Code (Warning: initial clone of the sumodule may fail with less than 2GB of RAM!):  
    ```bash
    git clone --branch <name_branch_here> https://github.com/mxOBS/deb-pkg_kernel-xyz.git
    cd deb-pkg_kernel-xyz
    git submodule update --init
3.  build deb:  
    ```bash
    cd deb-pkg_kernel-xyz
    dpkg-buildpackage -a armhf -b

## Maintainer-Scripts Documentation:
# kernel package initrd postinst logic:
1.  manage unversioned symlinks (zImage, initrd)
2.  call system-wide hooks in /etc/kernel/*.d/*
