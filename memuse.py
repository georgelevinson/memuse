import os
import re
import typing
import xlsxwriter

from pathlib import Path
from string import Template

# strings

device1_out = '/mnt/c/Users/user/Source/device1/Project_Output/'


class MemoryUsedByModuleAnalyzer:

    def __init__(self, out_dir : str) -> None:

        self.out_dir = out_dir
        self.__validate()


    def __validate(self) -> None:

        if not os.path.isdir(self.out_dir) or 'Project_Output' not in self.out_dir.split('/'):
            print('invalid directory passed to mapfile analyzer!')


    def __try_int_cast(self, i : str) -> bool:
        try:
            integer_value = int(i)
            return True  # Successful cast
        except ValueError:
            return False # Cast failed


    def __extract_projname(self, list_path : str) -> str:

        return list_path.replace(self.out_dir + 'OUT_', '').replace('/List/', '')


    def __parse_lst_data(self, results_dict : dict) -> None:

        lines = iter(results_dict['lst_data'].splitlines())
        
        def write_field(field_name : str):
            try:
                ln = next(line for line in lines if field_name in line)
                splt = re.split(r'\s+', ln)
                results_dict[field_name] = next(e for e in splt if self.__try_int_cast(e))
            except Exception as e:
                results_dict[field_name] = '0'

        [write_field(name) for name in ['CODE', 'DATA']]


    def __parse_map_data(self, results_dict : dict, data : str, indents : str) -> None:
        
        items = list(filter(lambda item: item != "", re.split(r'\s+', data)))

        if(not items.pop(0).startswith(results_dict['module_name'])):
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


    def __get_data(self, proj_path : str, module_name : str) -> dict:

        map = [f for f in os.listdir(proj_path) if f.endswith(".map")] 
        if not map:
            print(f"No .map files found in directory {proj_path}.")
            return
        if len(map) > 1:
            print(f"Multiple .map files found in directory {proj_path}.")

        lst = [f for f in os.listdir(proj_path) if f.endswith(module_name + '.lst')]
        if not lst:
            print(f"{module_name + '.lst'} not found in directory {proj_path}.")
            return
        if len(lst) > 1:
            print(f"Multiple .lst files found in directory {proj_path}.")

        results = dict(project = self.__extract_projname(proj_path), module_name = module_name, lst_data = "", decoding_err = [str])

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
            if line.lstrip().startswith(module_name):
                mapfile.close()
                self.__parse_map_data(results, line, indents)
                break
        
        lstfile = open(proj_path + '/' + lst[0], 'r')
        write = False

        while True:
            try:
                line = lstfile.readline()
            except UnicodeDecodeError as e:
                results['decoding_err'].append(e)
                continue
            
            if not line:
                self.__parse_lst_data(results)
                break
            if write:
                results['lst_data'] += line
            if line.endswith('sizes:\n'):
                write = True


        lstfile.close()

        return results


    def analyze(self, module_name):

        projects = [self.out_dir + f.name + "/List/" for f in os.scandir(path = self.out_dir) if f.is_dir()]

        raw_data = [self.__get_data(path, module_name) for path in projects]
        filtered_data = list(filter(None, raw_data))

        print('execution complete')
        # [self.results_file.write(entry) for entry in filtered_map_data]
        # [self.results_file.write(entry) for entry in filtered_lst_data]

        return filtered_data


analyzer = MemoryUsedByModuleAnalyzer(device1_out)

temp_by_status = analyzer.analyze("Temp_MesureByStatus")
temp_by_period = analyzer.analyze("Temp_MesureSomePeriod")
temp_ws_family = analyzer.analyze("WS_Family_Temperature")

# [self.results_file.write(entry) for entry in filtered_map_data]
# [self.results_file.write(entry) for entry in filtered_lst_data]

del analyzer

print("end of execution")