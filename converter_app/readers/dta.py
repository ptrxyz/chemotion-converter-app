import logging

from pathlib import Path

from .base import Reader

logger = logging.getLogger(__name__)


class DtaReader(Reader):
    identifier = 'dta_reader'
    priority = 10

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if self.encoding == 'binary':
            result = False
        elif Path(self.file_name).suffix.lower() == '.dta' and self.mime_type == 'text/plain':
            result = True
        else:
            result = False

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        table = self.append_table(tables)

        # loop over lines of the file
        header = True
        for line in self.file.readlines():
            row = line.decode(self.encoding).rstrip()

            # check if this is the first line of the header
            if not row.startswith('\t'):
                header = True

            if header:
                if table['rows']:
                    # if a table is already there, this must be a new header
                    table = self.append_table(tables)

                # append header line to last table
                table['header'].append(row)

                # add key value pairs from header to the metadata
                row_split = row.split()
                try:
                    key, value = row_split[0], row_split[2]
                    table['metadata'][key] = value
                except IndexError:
                    pass

            else:
                if table['metadata'].get('column_00') is None:
                    # this is the row with the columns
                    for idx, column_name in enumerate(row.split()):
                        # add the column name to the metadata
                        table['metadata']['column_{:02d}'.format(idx)] = column_name

                        # add the column name to list of columns
                        table['columns'].append({
                            'key': str(idx),
                            'name': 'Column #{} ({})'.format(idx, column_name)
                        })
                elif table['metadata'].get('column_00_unit') is None:
                    # this is the row with the units
                    for idx, column_unit in enumerate(row.split()):
                        # add the column unit to the metadata
                        table['metadata']['column_{:02d}_unit'.format(idx)] = column_unit

                else:
                    # now we extract the actual table
                    table['rows'].append([self.get_value(value) for value in row.split()])

            # check if this is the last line of the header
            if row.startswith('CURVE'):
                header = False

            table['metadata']['rows'] = len(table['rows'])
            table['metadata']['columns'] = len(table['columns'])

        return tables