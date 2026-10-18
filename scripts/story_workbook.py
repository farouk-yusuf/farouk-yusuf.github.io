"""Read committed story workbooks without adding website build dependencies."""
import posixpath
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL_NS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def read_sheet(filename, name):
    """Return header-keyed rows; preserve sparse, blank and rich-text cells."""
    def text(node):
        return ''.join(t.text or '' for t in node.findall('.//m:t', NS)) if node is not None else ''

    with ZipFile(filename) as archive:
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared = [text(si) for si in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        sheet = next(s for s in workbook.findall('m:sheets/m:sheet', NS) if s.attrib['name'] == name)
        relations = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        target = next(r.attrib['Target'] for r in relations if r.attrib['Id'] == sheet.attrib[REL_NS+'id'])
        path = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        rows = []
        for row in ET.fromstring(archive.read(path)).findall('m:sheetData/m:row', NS):
            cells = {}
            for cell in row.findall('m:c', NS):
                column = re.match('[A-Z]+', cell.attrib['r'])[0]
                value = cell.find('m:v', NS)
                value = value.text if value is not None else ''
                if cell.attrib.get('t') == 's':
                    value = shared[int(value)]
                elif cell.attrib.get('t') == 'inlineStr':
                    value = text(cell.find('m:is', NS))
                cells[column] = value
            rows.append(cells)
        headers = rows[0]
        return [{title: row.get(column, '') for column, title in headers.items()} for row in rows[1:] if any(row.values())]
