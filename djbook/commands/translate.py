import logging
import os
import re

import goslate
from cliff.command import Command as BaseCommand
from polib import pofile


class Command(BaseCommand):
    """
    Translate untranslated messages with Google Translator.

    Example:

        ./translator.py translate ref/models/options.po
    """
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Command, self).get_parser(prog_name)
        parser.add_argument('file', metavar='file', type=str, help='Path to .po file')
        return parser

    def take_action(self, parsed_args):
        po_path = os.path.join(self.app.locale_path, parsed_args.file)
        po = pofile(po_path)

        for entry in po.untranslated_entries():
            if entry.obsolete:
                continue

            en_msg = Msg(entry.msgid)
            entry.msgstr = en_msg.translate()
            entry.flags.append(u'fuzzy')

        po.save()


class Msg(object):
    markup_pattern = re.compile(ur'(``(.+?)``|\:(.+?)\:`(.+?)`)')
    revert_pattern = re.compile(ur'\$ \$ (\d+?) \$ \$')
    gs = goslate.Goslate()

    def __init__(self, msg):
        self.msg = msg
        self._keywords = []

    def translate(self):
        msg = self._before_translate(self.msg)
        result = Msg.gs.translate(msg, "ru", "en")
        return self._after_translate(result)

    def _before_translate(self, msg):
        return Msg.markup_pattern.sub(self._replace_before, msg)

    def _after_translate(self, msg):
        return Msg.revert_pattern.sub(self._replace_after, unicode(msg))

    def _replace_before(self, matchobj):
        index = len(self._keywords)
        self._keywords.append(matchobj.group(0))
        return u'$ $ %s $ $' % index

    def _replace_after(self, matchobj):
        return self._keywords.pop(0)