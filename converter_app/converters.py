import hashlib
import json
import logging
import os
import re
from collections import OrderedDict, defaultdict
from pathlib import Path

from flask import current_app as app

logger = logging.getLogger(__name__)


class Converter(object):

    def __init__(self, profile):
        self.profile = profile

    def clean(self):
        errors = defaultdict(list)
        if 'identifiers' in self.profile:
            if isinstance(self.profile['identifiers'], list):
                pass
            else:
                errors['identifiers'].append('This field has to be a list.')
        else:
            errors['identifiers'].append('This field has to be provided.')

        if 'rules' in self.profile:
            if isinstance(self.profile['rules'], dict):
                pass
            else:
                errors['rules'].append('This field has to be an object.')
        else:
            errors['rules'].append('This field has to be provided.')

        if 'metadata' in self.profile:
            if isinstance(self.profile['metadata'], dict):
                pass
            else:
                errors['metadata'].append('This field has to be an object.')
        else:
            errors['metadata'].append('This field has to be provided.')

        return errors

    def save(self):
        profiles_path = Path(app.config['PROFILES_DIR'])
        profiles_path.mkdir(parents=True, exist_ok=True)

        profile_json = json.dumps(self.profile, sort_keys=True, indent=4)
        checksum = hashlib.sha1(profile_json.encode()).hexdigest()

        file_path = profiles_path / '{}.json'.format(checksum)

        if not file_path.exists():
            with open(file_path, 'w') as fp:
                fp.write(profile_json)

    def match(self, file_data):
        self.header = OrderedDict()

        for identifier in self.profile.get('identifiers', []):
            if identifier.get('type') == 'metadata':
                value = self.match_metadata(identifier, file_data.get('metadata'))
            elif identifier.get('type') == 'data':
                value = self.match_data(identifier, file_data.get('data'))

            if value is False:
                return False
            else:
                # if a header key is given, store this match in the header
                header_key = identifier.get('headerKey')
                if header_key:
                    self.header[header_key] = value

        # if everything matched, return True
        return True

    def match_metadata(self, identifier, metadata):
        metadata_key = identifier.get('metadataKey')
        metadata_value = metadata.get(metadata_key)
        return self.match_value(identifier, metadata_value)

    def match_data(self, identifier, data):
        table_index = identifier.get('tableIndex')
        if table_index is not None:
            try:
                table = data[table_index]
            except KeyError:
                return False

            try:
                line_number = int(identifier.get('lineNumber')) - 1  # the interface counts from 1
                header_value = table['header'][line_number]
            except (ValueError, TypeError):
                header_value = os.linesep.join(table['header'])

            return self.match_value(identifier, header_value)

    def match_value(self, identifier, value):
        if value is not None:
            if identifier.get('isRegex'):
                pattern = identifier.get('value')
                match = re.search(pattern, value)
                logger.debug('match_value pattern="%s" value="%s" match=%s', pattern, value, bool(match))
                return match.group(1) if match else False
            else:
                result = value == identifier.get('value')
                logger.debug('match_value value="%s" result=%s', value, result)
                return value if result else False
        else:
            return False

    def get_header(self):
        header = self.profile.get('header')
        header.update(self.header)
        return header

    def get_data(self, data):
        x_column = self.profile.get('table', {}).get('xColumn')
        y_column = self.profile.get('table', {}).get('yColumn')
        first_row_is_header = self.profile.get('table', {}).get('firstRowIsHeader')

        x = []
        y = []
        for table_index, table in enumerate(data):
            if (x_column and table_index == x_column['tableIndex']) or (y_column and table_index == y_column['tableIndex']):
                for row_index, row in enumerate(table['rows']):
                    if first_row_is_header and first_row_is_header[table_index] and row_index == 0:
                        pass
                    else:
                        for column_index, column in enumerate(table['columns']):
                            if x_column and table_index == x_column['tableIndex'] and column_index == x_column['columnIndex']:
                                x.append(row[column_index].replace(',', '.'))
                            if y_column and table_index == y_column['tableIndex'] and column_index == y_column['columnIndex']:
                                y.append(row[column_index].replace(',', '.'))
        return {
            'x': x,
            'y': y
        }

    @classmethod
    def match_profile(cls, file_data):
        profiles_path = Path(app.config['PROFILES_DIR'])

        if profiles_path.exists():
            for file_name in os.listdir(profiles_path):
                file_path = profiles_path / file_name

                with open(file_path, 'r') as data_file:
                    profile = json.load(data_file)
                    converter = cls(profile)
                    if converter.match(file_data):
                        return converter
        else:
            return None

    @classmethod
    def list_profiles(cls):
        profiles = []
        profiles_path = Path(app.config['PROFILES_DIR'])
        for file_path in Path.iterdir(profiles_path):
            profiles.append(json.loads(file_path.read_text()))
        return profiles
