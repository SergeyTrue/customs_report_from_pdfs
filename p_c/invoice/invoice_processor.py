from pathlib import Path

import pandas as pd
import pdfplumber
import tabulate

invoice = Path(r"C:\Users\belose\Downloads\7338057196.pdf")
invoice_content = pdfplumber.open(invoice)
first_page = invoice_content.pages[0]
df = pd.DataFrame(first_page.extract_table())
#TODO print(tabulate(df, headers='keys', tablefmt='psql')) TypeError: 'module' object is not callable
