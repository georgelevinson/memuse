# strings
import argparse
from string import Template
from memory_use import MemoryUsedByModuleAnalyzer
from memory_use import MemoryUseReportCreator

# string constants

# default parameter values
temp_mods = ["Temp_MesureByStatus", "Temp_MesureSomePeriod", "WS_Family_Temperature", "Temp_MesureSomePeriodMultyTry"]
default_out_path = '/mnt/c/Users/user/Source/device1/Project_Output/'
default_report_name = 'temperature'
report_file_extension = '.xlsx'

# messages and message templates
welcome_desc_message = '\n\rWelcome to memuse, this utility will help you analyze memory requirements that various modules (files) incur on every project in the repo\n\r'
curr_args_message_template = Template('\n\rMemuse is running with the following parameter values:\n\r\n\r    proj output path:           $opath\n\r    modules analyzed:           $modules\n\r    report file name:           $rname\n\r')
continue_message = '\n\rWould you like to continue execution with current parameters? y/n\n\r(run with -h flag for parameters format)'

def main():
    # accept and parse command line args
    args_parser = argparse.ArgumentParser(description=welcome_desc_message)
    args_parser.add_argument('--rname', help='report .xlsx file name', default=default_report_name)
    args_parser.add_argument('--opath', help='full path to /Project_Output/', default=default_out_path)
    args_parser.add_argument('--modules', nargs='*', help='modules under inspection, whitespace-separated extensionless names', default=temp_mods)
    
    args = args_parser.parse_args()

    substitutions = {
        'opath': args.opath,
        'modules': args.modules,
        'rname': args.rname + report_file_extension
    }

    # notify user as to which values are being used for the current execution and ask in they want to execute
    print(curr_args_message_template.substitute(substitutions) + continue_message)

    while True:

        user_answ = input()

        if user_answ == 'y':
            break
        elif user_answ == 'n':
            return
        else:
            print('\n\rinvalid answer! please input y/n')
            continue
        
    # init worker objects
    analyzer = MemoryUsedByModuleAnalyzer(args.opath)
    report_creator = MemoryUseReportCreator(args.opath, args.rname + report_file_extension)

    # execute analysis and create .xlsx report file
    analysis_output = [analyzer.analyze(module) for module in args.modules]
    [report_creator.report(data_array) for data_array in analysis_output]

    # deinit worker objects
    del analyzer
    del report_creator

    print("end of execution")

    return

if __name__ == "__main__":
    main()