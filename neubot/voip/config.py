# You should have received a copy of the GNU General Public License
# along with Neubot.  If not, see <http://www.gnu.org/licenses/>.
#

''' The voip module properties that you can configure '''

#
# All the other submodules of bittorrent should fetch the
# definition of CONFIG from this one.
# We don't register descriptions unless we are running the
# voip module, so the user does not see this settings
# in the common case (internals ought to be internals).
#

import random

from neubot.net.poller import WATCHDOG

from neubot.config import CONFIG

PROPERTIES = (
    ('voip.address', '', 'Address to listen/connect to ("" = auto)'),
    ('voip.listen', False, 'Run in server mode'),
    ('voip.negotiate', True, 'Enable negotiate client/server'),
    ('voip.negotiate.port', 8080, 'Negotiate port'),
    ('voip.watchdog', WATCHDOG, 'Maximum test run-time in seconds'),
)

CONFIG.register_defaults_helper(PROPERTIES)

def register_descriptions():
    ''' Registers the description of voip variables '''
    CONFIG.register_descriptions_helper(PROPERTIES)


def finalize_conf(conf):

    ''' Finalize configuration and guess the proper value of all
        the undefined variables '''

    if not conf['voip.address']:
        conf['voip.address'] = ':: 0.0.0.0'
