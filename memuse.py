import os
import re
import typing
from pathlib import Path
from string import Template

# strings

device1_out = '/mnt/c/Users/user/Source/device1/Project_Output/'


class MemoryUseAnalyzer:

    def __init__(self, out_dir : str) -> None:

        self.out_dir = out_dir
        self.__setup()


    def __setup(self) -> None:

        if not os.path.isdir(self.out_dir) or 'Project_Output' not in self.out_dir.split('/'):
            print('invalid directory passed to mapfile analyzer!')


    def extract_projname(self, list_path : str) -> str:

        return list_path.replace(self.out_dir + 'OUT_', '').replace('/List/', '')


    def get_lst_data(self, proj_path : str, module : str) -> dict:

        lst = [f for f in os.listdir(proj_path) if f.endswith(module + '.lst')]

        if not lst:
            print(f"{module + '.lst'} not found in directory {proj_path}.")
            return
        if len(lst) > 1:
            print(f"Multiple .lst files found in directory {proj_path}.")

        results = dict(project = self.extract_projname(proj_path), module = module, lst_data = "", decoding_err = [str])
        lstfile = open(proj_path + '/' + lst[0], 'r')
        write = False

        while True:
            try:
                line = lstfile.readline()
            except UnicodeDecodeError as e:
                results['decoding_err'].append(e)
                continue
            
            if not line:
                break
            if write:
                results['lst_data'] += line
            if line.endswith('sizes:\n'):
                write = True

        lstfile.close()

        return results


    def parse_map_data(self, results_dict : dict, data : str, indents : str) -> None:
        
        items = list(filter(lambda item: item != "", re.split(r'\s+', data)))

        if(not items.pop(0).startswith(results_dict['module'])):
            print('Parsing error - data does not refer to expected module!')
            return

        if(len(items) is 0):

            results_dict['rocode'] = '0'
            results_dict['rodata'] = '0'
            results_dict['rwdata'] = '0'

            return
        
        if(len(items) is 3):

            results_dict['rocode'] = items[0]
            results_dict['rodata'] = items[1]
            results_dict['rwdata'] = items[2]

            return

        pos_rocode = indents.index('ro code')
        pos_rodata = indents.index('ro data')
        pos_rwdata = indents.index('rw data')
        
        def set_position(idx : int, value : str) -> None:
            if idx > pos_rocode and idx < pos_rodata:
                results_dict['rocode'] = value
            if idx > pos_rodata and idx < pos_rwdata:
                results_dict['rodata'] = value
            if idx > pos_rwdata:
                results_dict['rwdata'] = value

        [set_position(data.index(item), item) for item in items]


    def get_map_data(self, proj_path, module) -> dict:

        map = [f for f in os.listdir(proj_path) if f.endswith(".map")]

        if not map:
            print(f"No .map files found in directory {proj_path}.")
            return
        if len(map) > 1:
            print(f"Multiple .map files found in directory {proj_path}.")

        results = dict(project = self.extract_projname(proj_path), module = module, decoding_err = [str])
        mapfile = open(proj_path + '/' + map[0], 'r')
        indents = ''

        while True:
            try:
                line = mapfile.readline()
            except UnicodeDecodeError as e:
                results['decoding_err'].append(e)
                continue

            if not line:
                break
            if line.lstrip().startswith('Module') and 'ro code' in line:
                indents += line
            if line.lstrip().startswith(module):
                mapfile.close()
                self.parse_map_data(results, line, indents)
                return results
            
    def analyze(self, module) -> [dict] [dict]:

        projects = [self.out_dir + f.name + "/List/" for f in os.scandir(path = self.out_dir) if f.is_dir()]

        raw_map_data = [self.get_map_data(path, module) for path in projects]
        filtered_map_data = list(filter(None, raw_map_data))

        raw_lst_data = [self.get_lst_data(path, module) for path in projects]
        filtered_lst_data = list(filter(None, raw_lst_data))

        print('execution complete')
        # [self.results_file.write(entry) for entry in filtered_map_data]
        # [self.results_file.write(entry) for entry in filtered_lst_data]

        return filtered_lst_data, filtered_map_data
                




analyzer = MemoryUseAnalyzer(device1_out)

temp_by_status_lst, temp_by_status_map = analyzer.analyze("Temp_MesureByStatus")
temp_by_per_lst, temp_by_per_map = analyzer.analyze("Temp_MesureSomePeriod")
temp_ws_lst, temp_ws_map = analyzer.analyze("WS_Family_Temperature")

del analyzer

print("end of execution")