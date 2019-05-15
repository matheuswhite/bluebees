from common.file import file_helper
from common.utils import find_key
from random import randint
import re


class TemplateHelper:

    def __init__(self):
        self._random_pattern = r'\\d|\\h|\\c|\\a|\\A|\\t'
        self._sequence_pattern = r'\\s|\\S'
        self._sequences_filename = 'seq.yml'
        self._sequences = file_helper.load(self._sequences_filename, {})

    def _update_file(self):
        file_helper.write(self._sequences_filename, self._sequences)

    def _change_random(self, field_value: str):
        while True:
            if re.findall(r'\\d', field_value):
                val = str(randint(0, 9))
                field_value = field_value.replace('\\d', val, 1)
            elif re.findall(r'\\h', field_value):
                val = hex(randint(0, 16))[2]
                field_value = field_value.replace('\\h', val, 1)
            elif re.findall(r'\\c', field_value):
                val = chr(randint(0x21, 0x7e))
                field_value = field_value.replace('\\c', val, 1)
            elif re.findall(r'\\a', field_value):
                val = chr(randint(0x61, 0x7a))
                field_value = field_value.replace('\\a', val, 1)
            elif re.findall(r'\\A', field_value):
                val = chr(randint(0x41, 0x5a))
                field_value = field_value.replace('\\A', val, 1)
            elif re.findall(r'\\t', field_value):
                val = randint(0x41, 0x7a)
                while 0x5b <= val <= 0x60:
                    val = randint(0x41, 0x7a)
                val = chr(val)
                field_value = field_value.replace('\\t', val, 1)
            else:
                break
        return field_value

    def _change_sequence(self, field_value: str):
        try:
            pattern = field_value
            pattern = pattern.replace('\\s', '')
            pattern = pattern.replace('\\S', '')

            seq = self._sequences[pattern]
            field_value = field_value.replace('\\s', str(seq))
            field_value = field_value.replace('\\S', format(seq, 'x'))
            self._sequences[pattern] += 1

            self._update_file()

            return field_value
        except KeyError:
            self._sequences[pattern] = 0
            return self._change_sequence(field_value)

    def get_field(self, template, field_name):
        field_raw_value = template[field_name]
        field_value = field_raw_value

        if type(field_raw_value) != str and type(field_raw_value) != bytes:
            return field_value

        if re.findall(self._random_pattern, field_raw_value):
            field_value = self._change_random(field_raw_value)
        elif re.findall(self._sequence_pattern, field_raw_value):
            field_value = self._change_sequence(field_raw_value)
        elif re.findall(r'\\', field_raw_value):
            raise Exception(f'Symbol unknown')

        return field_value


template_helper = TemplateHelper()
