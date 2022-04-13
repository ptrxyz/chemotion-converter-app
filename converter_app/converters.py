import logging
import os
import re

from .models import Profile

logger = logging.getLogger(__name__)


class Converter(object):

    def __init__(self, profile):
        self.profile = profile
        self.matches = []
        self.tables = []

    def match(self, file_data):
        for identifier in self.profile.data.get('identifiers', []):
            if identifier.get('type') == 'fileMetadata':
                match = self.match_file_metadata(identifier, file_data.get('metadata'))
            elif identifier.get('type') == 'tableMetadata':
                match = self.match_table_metadata(identifier, file_data.get('tables'))
            elif identifier.get('type') == 'tableHeader':
                match = self.match_table_header(identifier, file_data.get('tables'))
            else:
                return False

            if match is False and not identifier.get('optional'):
                # return immediately if one (non optional) identifier does not match
                return False

            # store match
            self.matches.append({
                'identifier': identifier,
                'result': match
            })

        # if everything matched, return how many identifiers matched
        return len(self.matches)

    def match_file_metadata(self, identifier, metadata):
        input_key = identifier.get('key')
        input_value = metadata.get(input_key)
        if input_key and input_value:
            value = self.match_value(identifier, input_value)
            if value:
                return {
                    'value': value
                }

        return False

    def match_table_metadata(self, identifier, input_tables):
        input_table_index = identifier.get('tableIndex')
        input_table = self.get_input_table(input_table_index, input_tables)
        if input_table is not None:
            input_key = identifier.get('key')
            input_value = input_table.get('metadata', {}).get(input_key)
            if input_key and input_value:
                value = self.match_value(identifier, input_value)
                if value:
                    return {
                        'value': value,
                        'tableIndex': input_table_index
                    }

        return False

    def match_table_header(self, identifier, input_tables):
        input_table_index = identifier.get('tableIndex')
        input_table = self.get_input_table(input_table_index, input_tables)
        if input_table is not None:
            # try to get the line_number from the identifier
            try:
                line_number = int(identifier.get('lineNumber'))
            except (ValueError, TypeError):
                line_number = None

            if line_number is None:
                # use the whole header
                header = os.linesep.join(input_table['header']).rstrip()
            else:
                # use only the provided line
                try:
                    # the interface counts from 1
                    header = input_table['header'][line_number - 1].rstrip()
                except IndexError:
                    # the line in the header does not exist
                    return False

            if header:
                # try to match the value
                value = self.match_value(identifier, header)

                if value:
                    # if no line number was provided, find the line number for the value
                    if line_number is None:
                        line_number = self.get_line_number(input_table['header'], value)

                    return {
                        'value': value,
                        'tableIndex': input_table_index,
                        'lineNumber': line_number,
                    }

        return False

    def match_value(self, identifier, value):
        if value is not None:
            if identifier.get('isRegex'):
                pattern = identifier.get('value')
                match = re.search(pattern, value)
                logger.debug('match_value pattern="%s" value="%s" match=%s', pattern, value, bool(match))
                if match:
                    try:
                        return match.group(1).strip()
                    except IndexError:
                        return match.group(0).strip()
                else:
                    return False
            else:
                result = (value == identifier.get('value'))
                logger.debug('match_value identifier="%s", value="%s" result=%s', identifier.get('value'), value, result)
                return value if result else False
        else:
            return False

    def process(self, input_tables):
        for output_table_index, output_table in enumerate(self.profile.data.get('tables')):
            header = output_table.get('header', {})

            # merge the metadata from the profile (header) with the metadata
            # extracted using the identifiers (see self.match)
            for match in self.matches:
                match_result = match.get('result')
                if match_result:
                    match_output_key = match.get('identifier', {}).get('outputKey')
                    match_output_table_index = match.get('identifier', {}).get('outputTableIndex')
                    match_value = match_result.get('value')
                    if match_output_key and (
                        output_table_index == match_output_table_index or
                        match_output_table_index is None
                    ):
                        header[match_output_key] = match_value

            x_column = output_table.get('table', {}).get('xColumn')
            y_column = output_table.get('table', {}).get('yColumn')
            x_operations = output_table.get('table', {}).get('xOperations', [])
            y_operations = output_table.get('table', {}).get('yOperations', [])

            # repare rows
            x_rows = []
            y_rows = []
            for operation in x_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []
            for operation in y_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []

            for table_index, table in enumerate(input_tables):
                for row_index, row in enumerate(table['rows']):
                    for column_index, column in enumerate(table['columns']):
                        if x_column and \
                                table_index == x_column.get('tableIndex') and \
                                column_index == x_column.get('columnIndex'):
                            x_rows.append(self.get_value(row, column_index))

                        if y_column and \
                                table_index == y_column.get('tableIndex') and \
                                column_index == y_column.get('columnIndex'):
                            y_rows.append(self.get_value(row, column_index))

                        for operation in x_operations:
                            if operation.get('type') == 'column' and \
                                    table_index == operation.get('column', {}).get('tableIndex') and \
                                    column_index == operation.get('column', {}).get('columnIndex'):
                                operation['rows'].append(self.get_value(row, column_index))

                        for operation in y_operations:
                            if operation.get('type') == 'column' and \
                                    table_index == operation.get('column', {}).get('tableIndex') and \
                                    column_index == operation.get('column', {}).get('columnIndex'):
                                operation['rows'].append(self.get_value(row, column_index))

            for operation in x_operations:
                x_rows = self.run_operation(x_rows, operation)
            for operation in y_operations:
                y_rows = self.run_operation(y_rows, operation)

            self.tables.append({
                'header': header,
                'x': x_rows,
                'y': y_rows
            })

    def run_operation(self, rows, operation):
        for i, row in enumerate(rows):
            op_value = None
            if operation.get('type') == 'column':
                try:
                    op_value = operation['rows'][i]
                except IndexError:
                    pass
            elif operation.get('type') == 'value':
                op_value = operation.get('value')

            if op_value:
                if operation.get('operator') == '+':
                    row_value = float(row) + float(op_value)
                elif operation.get('operator') == '-':
                    row_value = float(row) - float(op_value)
                elif operation.get('operator') == '*':
                    row_value = float(row) * float(op_value)
                elif operation.get('operator') == ':':
                    row_value = float(row) / float(op_value)
                rows[i] = str(row_value)

        return rows

    def get_input_table(self, index, input_tables):
        if index is not None:
            try:
                if int(index) >= len(input_tables):
                    return None
                else:
                    return input_tables[int(index)]
            except KeyError:
                return None

    def get_line_number(self, header, value):
        # if line_number is None:
        for i, line in enumerate(header):
            if value in line:
                # again we count from 1
                return i + 1

    def get_value(self, row, column_index):
        return str(row[column_index]).replace(',', '.').replace('e', 'E')

    @classmethod
    def match_profile(cls, client_id, file_data):
        converter = None
        matches = 0

        for profile in Profile.list(client_id):
            current_converter = cls(profile)
            current_matches = current_converter.match(file_data)

            logger.info('profile=%s matches=%s', profile.id, current_matches)

            if current_matches is not False and current_matches > matches:
                converter = current_converter
                matches = current_matches

        return converter
