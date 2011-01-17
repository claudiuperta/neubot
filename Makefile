# Makefile

#
# Copyright (c) 2010 Simone Basso <bassosimone@gmail.com>,
#  NEXA Center for Internet & Society at Politecnico di Torino
#
# This file is part of Neubot <http://www.neubot.org/>.
#
# Neubot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Neubot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

#
# The scripts/release script will automatically update the
# version number each time we tag with a new release.
#

VERSION	= 0.3.3

#
# The list of .PHONY targets.  This is also used to build the
# help message--and note that the targets named with a leading
# underscore are private.
# Here we list targets in file order because this makes it easier
# to maintain this list.
#

PHONIES += _all
PHONIES += archive
PHONIES += _install_skel
PHONIES += _install_sources
PHONIES += _install_www
PHONIES += _install_etc
PHONIES += _install_man
PHONIES += _install_bin
PHONIES += _install_icon
PHONIES += _install_menu
PHONIES += _install_edit
PHONIES += _install_compile
PHONIES += _install
PHONIES += _bdist
PHONIES += bdist.tgz
PHONIES += install
PHONIES += app
PHONIES += app.zip
PHONIES += _deb_data
PHONIES += _deb_data.tgz
PHONIES += _deb_control_skel
PHONIES += _deb_control_md5sums
PHONIES += _deb_control_size
PHONIES += _deb_control
PHONIES += _deb_control.tgz
PHONIES += _deb_binary
PHONIES += _deb
PHONIES += deb
PHONIES += clean
PHONIES += help
PHONIES += lint
PHONIES += _release
PHONIES += release
PHONIES += release_stable

.PHONY: $(PHONIES)
_all: help

#                 _     _
#   __ _ _ __ ___| |__ (_)_   _____
#  / _` | '__/ __| '_ \| \ \ / / _ \
# | (_| | | | (__| | | | |\ V /  __/
#  \__,_|_|  \___|_| |_|_| \_/ \___|
#
# Create source archives
#

STEM = neubot-$(VERSION)
ARCHIVE = git archive --prefix=$(STEM)/
FORMATS += tar
FORMATS += zip

archive:
	@echo "[ARCHIVE]"
	@install -m755 -d dist/
	@for FORMAT in $(FORMATS); do \
	 $(ARCHIVE) --format=$$FORMAT HEAD > dist/$(STEM).$$FORMAT; \
	done
	@gzip -9 dist/$(STEM).tar

#  _           _        _ _
# (_)_ __  ___| |_ __ _| | |
# | | '_ \/ __| __/ _` | | |
# | | | | \__ \ || (_| | | |
# |_|_| |_|___/\__\__,_|_|_|
#
# Install neubot in the filesystem
#

#
# We need to override INSTALL with 'install -o root' when
# we install from sources because in this case we want to
# enforce root's ownership.
#

INSTALL	= install

#
# These are some of the variables accepted by the GNU
# build system, in order to follow the rule of the least
# surprise [1].
# We install neubot in $(DATADIR)/neubot following sect.
# 3.1.1 of Debian Python Policy which covers the shipping
# of private modules [2].
# We follow BSD hier(7) and we install manual pages in
# /usr/local/man by default.  We override it when we make
# a debian package but you might want to pass MANDIR to
# make when installing from sources.
#
# [1] http://bit.ly/aLduJz (gnu.org)
# [2] http://bit.ly/ayYyAR (debian.org)
#

DESTDIR =
SYSCONFDIR = /etc/neubot
LOCALSTATEDIR = /var/neubot
PREFIX = /usr/local
BINDIR = $(PREFIX)/bin
DATADIR = $(PREFIX)/share
MANDIR = $(PREFIX)/man
ICONDIR = $(DATADIR)/icons/hicolor/scalable/apps
MENUDIR = $(DATADIR)/applications

SUBDIRS = `find neubot/ -type d`
SRCS = `find neubot/ -type f -name \*.py`
WEBPAGES = `find neubot/www -type f`

_install_skel:
	@$(INSTALL) -d -m755 $(DESTDIR)$(SYSCONFDIR)
	@$(INSTALL) -d -m755 $(DESTDIR)$(LOCALSTATEDIR)
	@$(INSTALL) -d -m755 $(DESTDIR)$(BINDIR)
	@$(INSTALL) -d -m755 $(DESTDIR)$(DATADIR)
	@$(INSTALL) -d -m755 $(DESTDIR)$(MANDIR)/man1
	@$(INSTALL) -d -m755 $(DESTDIR)$(ICONDIR)
	@$(INSTALL) -d -m755 $(DESTDIR)$(MENUDIR)
	@for SUBDIR in $(SUBDIRS); do \
	 $(INSTALL) -d -m755 $(DESTDIR)$(DATADIR)/$$SUBDIR; \
	done

_install_sources:
	@for SRC in $(SRCS); do \
	 $(INSTALL) -m644 $$SRC $(DESTDIR)$(DATADIR)/$$SRC; \
	done

_install_www:
	@for WWW in $(WEBPAGES); do \
	 $(INSTALL) -m644 $$WWW $(DESTDIR)$(DATADIR)/$$WWW; \
	done

_install_etc:
	@$(INSTALL) -m644 etc/neubot/config $(DESTDIR)/$(SYSCONFDIR)/config

#
# We keep in the sources the manual page so that one that
# does not have rst2man installed is still able to install
# neubot.
#

_install_man:
	@$(INSTALL) -m644 man/man1/neubot.1 $(DESTDIR)$(MANDIR)/man1

_install_bin:
	@$(INSTALL) -m755 bin/neubot $(DESTDIR)$(BINDIR)
	@$(INSTALL) -m755 bin/start-neubot-daemon $(DESTDIR)$(BINDIR)

_install_icon:
	@$(INSTALL) -m644 icons/neubot.svg $(DESTDIR)$(ICONDIR)/neubot.svg

_install_menu:
	@for F in `cd applications/ && ls`; do \
	 $(INSTALL) -m644 applications/$$F $(DESTDIR)$(MENUDIR)/$$F; \
	done

#
# After the install we need to edit the following files to
# tell neubot the path where it's installed.
# The original sources contain the @DATADIR@ placeholder and
# will use a sane default if they find the placeholder instead
# of a valid path.
# FIXME Actually the sources contain PREFIX but it should use
# DATADIR; however now we don't have time to fix that and so
# the above comment is not (yet) right.
#

NEEDEDIT += $(DESTDIR)$(BINDIR)/neubot
NEEDEDIT += $(DESTDIR)$(DATADIR)/neubot/pathnames.py
NEEDEDIT += $(DESTDIR)$(BINDIR)/start-neubot-daemon
NEEDEDIT += $(DESTDIR)$(DATADIR)/neubot/statusicon.py
NEEDEDIT += $(DESTDIR)$(MENUDIR)/neubot-status-icon.desktop
NEEDEDIT += $(DESTDIR)$(MENUDIR)/neubot-web-ui.desktop

# New style:
#
#_install_edit:
#	@for EDIT in $(NEEDEDIT); do \
#	 ./scripts/sed_inplace 's|@DATADIR@|$(DATADIR)|g' $$EDIT; \
#	done
#
# Old style:
#
_install_edit:
	@for EDIT in $(NEEDEDIT); do \
	 ./scripts/sed_inplace 's|@PREFIX@|$(PREFIX)|g' $$EDIT; \
	done

_install_compile:
	@python -m compileall -q $(DESTDIR)$(DATADIR)/neubot
	@LIST=`find $(DESTDIR)$(DATADIR)/neubot -type f -name \*.pyc` && \
	 chmod 644 $$LIST

INSTALL_RULES += _install_skel
INSTALL_RULES += _install_sources
INSTALL_RULES += _install_www
INSTALL_RULES += _install_etc
INSTALL_RULES += _install_man
INSTALL_RULES += _install_bin
INSTALL_RULES += _install_icon
INSTALL_RULES += _install_menu
INSTALL_RULES += _install_edit
INSTALL_RULES += _install_compile

_install:
	@for RULE in $(INSTALL_RULES); do \
	 make -f Makefile $$RULE; \
	done

_bdist:
	@echo "[BDIST]"
	@make -f Makefile _install DESTDIR=dist/bdist

bdist.tgz: bdist
	@echo "[BDIST.TGZ]"
	@cd dist/data && tar czf ../$(STEM)_`uname -m`.tgz *

#
# install should be invoked as root and will actually
# copy neubot on the filesystem, making sure that root
# owns the installed files.
#

install:
	@make -f Makefile _install INSTALL='install -o root'

#   __ _ _ __  _ __
#  / _` | '_ \| '_ \
# | (_| | |_) | |_) |
#  \__,_| .__/| .__/
#       |_|   |_|
#
# Application for MacOSX >= Leopard (10.5)
#

APP_NAME=$(STEM).app
APP_RESOURCES=$(APP_NAME)/Contents/Resources

app:
	@echo "[APP]"
	@make -f Makefile archive
	@cp -R MacOS/neubot.app dist/$(APP_NAME)
	@cd dist/$(APP_RESOURCES) && tar -xzf ../../../$(STEM).tar.gz && \
         ln -s $(STEM) neubot && rm -rf pax_global_header

app.zip:
	@echo "[APP.ZIP]"
	@make -f Makefile app
	@cd dist && zip -q --symlinks -r $(APP_NAME).zip $(APP_NAME)
	@cd dist && rm -rf $(APP_NAME) $(STEM).tar.gz $(STEM).zip

#      _      _
#   __| | ___| |__
#  / _` |/ _ \ '_ \
# | (_| |  __/ |_) |
#  \__,_|\___|_.__/
#
# Make package for debian/ubuntu
#

DEB_PACKAGE = dist/$(STEM)-1_all.deb

# Directories to create.
DEB_DATA_DIRS += dist/data/etc/init.d/
DEB_DATA_DIRS += dist/data/etc/apt/sources.list.d/

# Files to copy.
DEB_DATA_FILES += etc/init.d/neubot
DEB_DATA_FILES += etc/apt/sources.list.d/neubot.list

# Files to `chmod +x`.
DEB_DATA_EXEC += dist/data/etc/init.d/neubot

# Update URI
DEB_UPDATE_URI = "testing"

_deb_data:
	@make -f Makefile _install DESTDIR=dist/data PREFIX=/usr
	@cd dist/data && mv usr/man usr/share/man
	@for DIR in $(DEB_DATA_DIRS); do \
	 install -m755 -d $$DIR; \
	done
	@for FILE in $(DEB_DATA_FILES); do \
	 install -m644 debian/$$FILE dist/data/$$FILE; \
	done
	@for FILE in $(DEB_DATA_EXEC); do \
	 chmod 755 $$FILE; \
	done
	@./scripts/sed_inplace s/@TESTING@/$(DEB_UPDATE_URI)/g \
         dist/data/etc/apt/sources.list.d/neubot.list

_deb_data.tgz: _deb_data
	@cd dist/data && tar czf ../data.tar.gz ./*

DEB_CONTROL_FILE += control/control
DEB_CONTROL_FILE += control/postinst
DEB_CONTROL_FILE += control/prerm

_deb_control_skel:
	@install -d -m755 dist/control
	@for FILE in $(DEB_CONTROL_FILE); do \
	 install -m644 debian/$$FILE dist/$$FILE; \
	done

_deb_control_md5sums:
	@install -m644 /dev/null dist/control/md5sums
	@./scripts/md5sum `find dist/data -type f` > dist/control/md5sums
	@./scripts/sed_inplace 's|dist\/data\/||g' dist/control/md5sums

_deb_control_size:
	@SIZE=`du -k -s dist/data/|cut -f1` && \
	 ./scripts/sed_inplace "s|@SIZE@|$$SIZE|" dist/control/control

_deb_control:
	@make -f Makefile _deb_control_skel
	@make -f Makefile _deb_control_md5sums
	@make -f Makefile _deb_control_size

_deb_control.tgz: _deb_control
	@cd dist/control && tar czf ../control.tar.gz ./*

_deb_binary:
	@echo '2.0' > dist/debian-binary

#
# Note that we must make _deb_data before _deb_control
# because the latter must calculate the md5sums and the
# total size.
# The public command enforces root privileges because we
# don't want to ship a deb with ordinary user ownership by
# mistake.
#

_deb:
	@make -f Makefile _deb_data.tgz
	@make -f Makefile _deb_control.tgz
	@make -f Makefile _deb_binary
	@ar r $(DEB_PACKAGE) dist/debian-binary \
	 dist/control.tar.gz dist/data.tar.gz
	@cd dist && rm -rf debian-binary control.tar.gz data.tar.gz \
         control/ data/

deb:
	@echo "[DEB]"
	@make -f Makefile _deb INSTALL='install -o root'

#
# Other targets
#

clean:
	@echo "[CLEAN]"
	@find . -type f -name \*.pyc -exec rm -f {} \;
	@rm -rf -- dist/
help:
	@echo -n "Targets:"
	@for TARGET in `grep ^PHONIES Makefile|sed 's/^.*+= //'`; do	\
	     if echo $$TARGET|grep -qv ^_; then				\
	         echo -n " $$TARGET";					\
	     fi;							\
	 done
	@echo ""
lint:
	@echo "[LINT]"
	@find . -type f -name \*.py -exec pychecker {} \;

#           _
#  _ __ ___| | ___  __ _ ___  ___
# | '__/ _ \ |/ _ \/ _` / __|/ _ \
# | | |  __/ |  __/ (_| \__ \  __/
# |_|  \___|_|\___|\__,_|___/\___|
#
# Bless a new neubot release (sources, Debian, and MacOSX).
#

_release:
	@make clean
	@make app.zip
	@make deb
	@make archive
#
	@cd dist && dpkg-scanpackages . > Packages
	@cd dist && gzip --stdout -9 Packages > Packages.gz
	@cp debian/Release dist/
	@for FILE in Packages Packages.gz; do \
	  SHASUM=`sha256sum dist/$$FILE | awk '{print $$1}'` && \
	  KBYTES=`wc -c dist/$$FILE | awk '{print $$1}'` && \
	  echo " $$SHASUM $$KBYTES $$FILE" >> dist/Release; \
	 done
	@gpg -abs -o dist/Release.gpg dist/Release
#
	@cd dist && ../scripts/sha256sum neubot-* >> SHA256.inc
	@cd dist && chmod 644 *
	@chmod 777 dist

release:
	@echo "[RELEASE]"
	@make -f Makefile _release

release_stable:
	@echo "[RELEASE_STABLE]"
	@make -f Makefile _release DEB_UPDATE_URI=""
