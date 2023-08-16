import xlsxwriter
from typing import List, Dict

class MemoryUseReportCreator:

    def __init__(self, out_dir : str, file_name : str) -> None:
        self.workbook = xlsxwriter.Workbook(out_dir + file_name)


    def __del__(self) -> None:
        self.workbook.close()

    
    def report(self, data : List[Dict[str, str]]) -> None:
        worksheet = self.workbook.add_worksheet(data[0]['module_name'])

        row = 1
        col = 1

        for key in data[0]:
            worksheet.write(row, col, key)
            col += 1

        row = 2
        col = 1

        for dp in data:
            for key in dp:
                try:
                    worksheet.write(row, col, dp[key])
                    col += 1
                except Exception:
                    col += 1
                    continue
            col = 1
            row += 1
        row = 2
