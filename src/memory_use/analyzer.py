import os
import re
from typing import List, Tuple


class MemoryUsedByModuleAnalyzer:

    def __init__(self, out_dir : str) -> None:

        self.out_dir = out_dir
        self.__validate()


    # Checks that MemoryUsedByModuleAnalyzer had been passed valid out_dir parameter
    def __validate(self) -> None:

        if not os.path.isdir(self.out_dir) or 'Project_Output' not in self.out_dir.split('/'):
            print('Invalid directory passed to memory analyzer!')


    # Used when parsing to check that a string represents a number
    def __try_int_cast(self, i : str) -> bool:
        try:
            integer_value = int(i)
            return True 
        except ValueError:
            return False


    # Returns string representing name of the project residing in proj_path
    def __extract_projname(self, proj_path : str) -> str:

        return proj_path.replace(self.out_dir + 'OUT_', '').replace('/List/', '')


    # Given a pointer to results_dict, analyzes multi-line excerpt from .lst file
    # Extracts data about CODE and DATA size, writes it to results_dict
    def __parse_lst_data(self, results_dict : dict) -> None:

        lines = iter(results_dict['lst_data'].splitlines())
        
        # Tries to find a single substring that may be cast to int 
        # If there's one - it's the value of interest, written to results_dict
        def write_field(field_name : str):
            try:
                ln = next(line for line in lines if field_name in line)
                splt = re.split(r'\s+', ln)
                results_dict[field_name] = next(e for e in splt if self.__try_int_cast(e))
            except Exception as e:
                pass

        [write_field(name) for name in ['CODE', 'DATA']]


    # Receives a pointer to results_dict, a line from .map file Modules table and table header
    # Extracts data about rocode, rodata and rwdata size, writes it to results_dict
    def __parse_map_data(self, results_dict : dict, data : str, indents : str) -> None:
        
        pos_rocode = indents.index('ro code')
        pos_rodata = indents.index('ro data')
        pos_rwdata = indents.index('rw data')
        
        # based on char position within a line (idx) determines 
        # which 'cell' of the table a given character belongs to
        def set_position(idx : int, value : str) -> None:
            if idx > pos_rocode and idx < pos_rodata:
                results_dict['rocode'] += value
            if idx > pos_rodata and idx < pos_rwdata:
                results_dict['rodata'] += value
            if idx > pos_rwdata:
                results_dict['rwdata'] += value

        char_cnt = 0

        # skips leading whitespaces and module_name.o
        for char in data:
            if(char == '.'):
                # jump to the first whitespace after file extension
                char_cnt += 2
                data = data[char_cnt:]
                break
            char_cnt += 1
        
        for char in data:
            if(char != ' '):
                set_position(char_cnt, char)
            char_cnt += 1


    # Given a path to project's output folder and a module name, finds .lst and .map files if present
    # Using __parse_xxx_data methods extracts data about module's RAM/FLASH memory requirements in a given project
    def __get_data(self, proj_path : str, module_name : str) -> dict:
        
        # finds .map file of the project in proj_path
        map = [f for f in os.listdir(proj_path) if f.endswith(".map")] 
        if not map:
            print(f"No .map files found in directory {proj_path}.")
            return
        if len(map) > 1:
            print(f"Multiple .map files found in directory {proj_path}.")

        # finds .lst of module module_name in proj_path
        lst = [f for f in os.listdir(proj_path) if f.endswith(module_name + '.lst')]
        if not lst:
            print(f"{module_name + '.lst'} not found in directory {proj_path}.")
            return
        if len(lst) > 1:
            print(f"Multiple .lst files found in directory {proj_path}.")

        results = dict(project = self.__extract_projname(proj_path), 
                       module_name = module_name, 
                       rocode = '', 
                       rodata = '', 
                       rwdata = '', 
                       CODE = '0',
                       DATA = '0',
                       lst_data = '',
                       decoding_err = [])

        # open .map file
        mapfile = open(proj_path + '/' + map[0], 'r')
        indents = ''
        # walk through and extract needed data
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
                self.__parse_map_data(results, line, indents)
                break
        # work with file complete
        mapfile.close()

        # open .lst file
        lstfile = open(proj_path + '/' + lst[0], 'r')
        write = False
        #walk through and extract needed data
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
        # work with file complete
        lstfile.close()

        # join all the data on errors into a single string such that it can later be written to .xlsx report

        errors = [error.reason for error in results['decoding_err']]
        results['decoding_err'] = ', '.join(errors)

        return results

    # access method to object's functionality, since proj folder is passed upon construction, only accepts module arg
    def analyze(self, module_name):

        projects = [self.out_dir + f.name + "/List/" for f in os.scandir(path = self.out_dir) if f.is_dir()]

        raw_data = [self.__get_data(path, module_name) for path in projects]
        filtered_data = list(filter(None, raw_data))

        return filtered_data
