import argparse, json
from openpyxl import Workbook
p=argparse.ArgumentParser()
p.add_argument('--input-json'); p.add_argument('--output-json'); p.add_argument('--output-excel')
a=p.parse_args()
payload=json.load(open(a.input_json, encoding='utf-8'))
wb=Workbook(); wb.active['A1']=payload['title']; wb.save(a.output_excel)
json.dump({'written': True}, open(a.output_json, 'w', encoding='utf-8'))
