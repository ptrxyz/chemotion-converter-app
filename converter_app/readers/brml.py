import logging
import zipfile

from pathlib import Path
import defusedxml.ElementTree as ET

from .base import Reader

logger = logging.getLogger(__name__)


class BrmlReader(Reader):
    identifier = 'brml_reader'
    priority = 10

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if Path(self.file_name).suffix != '.brml':
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []

        with zipfile.ZipFile(self.file) as zf:
            # open DataContainer.xml
            with zf.open('Experiment0/DataContainer.xml') as dc:
                data_container = ET.fromstring(dc.read())
                for raw_data in data_container.findall('./RawDataReferenceList/string'):
                    raw_data_file_name = raw_data.text

                    with zf.open(raw_data_file_name) as rd:
                        raw_data = ET.fromstring(rd.read())

                        for data_route in raw_data.findall('./DataRoutes/DataRoute'):
                            table = self.append_table(tables)

                            first = True
                            for datum in data_route.findall('./Datum'):
                                row = datum.text.split(',')

                                if first:
                                    first = False

                                    # add columns
                                    for idx, cell in enumerate(row):
                                        try:
                                            table['columns'][idx]
                                        except IndexError:
                                            table['columns'].append({
                                                'key': str(idx),
                                                'name': 'Column #{}'.format(idx)
                                            })

                                table['rows'].append(row)

                    table['metadata']['rows'] = len(table['rows'])
                    table['metadata']['columns'] = len(table['columns'])

        return tables