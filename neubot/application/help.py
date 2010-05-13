# neubot/application/help.py
# Copyright (c) 2010 NEXA Center for Internet & Society

# This file is part of Neubot.
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

import sys

from neubot.application.__defaults import defaults

HELP = 									\
"\n"									\
"Network neutrality bot (Neubot) -- version 0.0.2\n"			\
"Copyright (c) 2010 NEXA Center for Internet & Society\n"		\
"  For more info, see http://nexa.polito.it/neubot\n"			\
"\n"									\
"Usage: neubot [-bEv] [-I path] [-O opt=val] [--] [command [opts]]\n"	\
"\n"									\
"Options:\n"								\
"  -b                   Run in background as a daemon.\n"		\
"  -E                   Do not read any configuration file.\n"		\
"  -I path              Run the neubot located at path.\n"		\
"  -O opt=val           Set option's value via command line.\n"		\
"  -v                   Turn on debugging output.\n"			\
"\n"									\
"Commands:\n"								\
"  _exit                Exit immediatly (for testing).\n"		\
"  _neubot              The command invoked by default.\n"		\
"  _writeconfig         Write configuration on stdout.\n"		\
"  help                 Print this help screen and exit.\n"		\
"\n"

def main(configuration, argv):
	sys.stdout.write(HELP)
	sys.exit(0)

if (__name__ == "__main__"):
	main(defaults, sys.argv)