"""2p-2runner: a WowHead quest parser, by Lorelei Chevroulet.
This program provides utilities to parse the contents of typical WowHead quest info pages.
It contains the following tools:
* HTML tag remover using basic Python find()
* HTML to markdown conversion using the html2text module
* Selection of specific markdown content based on headers
* Exclusion of empty or short quest files
* Random selection of n files from a directory. 
"""
import sys
import os
from pathlib import Path
from multiprocessing import Pool, cpu_count
import glob
import time
import random
import html2text


class Ansi:
    HEADER = '\033[95m'
    BR_MAGENTA = '\033[95m'
    BR_BLUE = '\033[94m'
    BR_CYAN = '\033[96m'
    BR_GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLINK = '\033[5m'
    UNDERLINE = '\033[4m'
    RIGHT = '\033[C'
    # FRAMED = '\033[52m'
    CLEAR = '\033[J'
    CLINE = '\033[2K'
    UP = '\033[F'
    DOWN = '\033[E'
    ALLUP = '\033[H'
    B_GREEN = '\033[42m'
    B_RED = '\033[41m'
    B_BLUE = '\033[44m'
    B_MAGENTA = '\033[45m'
    B_CYAN = '\033[46m'
    BBR_GREEN = '\033[102m'
    BBR_RED = '\033[101m'
    BBR_BLUE = '\033[104m'
    BBR_MAGENTA = '\033[105m'
    BBR_CYAN = '\033[106m'


LOGO = '''
 ___         ___                         
|_  |___ ___|_  |___ _ _ ___ ___ ___ ___ 
|  _| . |___|  _|  _| | |   |   | -_|  _|
|___|  _|   |___|_| |___|_|_|_|_|___|_|  
    |_|                                
'''

PROMPT = '    ' + Ansi.DIM + '>' + Ansi.ENDC

total_files_processed = 0  # Used to track multiprocessing
total_files_queued = 0  # Used to track queued files in multiprocessing


def main():
    """Main script. Loop and mode selection."""
    print(40 * '░')
    print(
        Ansi.BOLD + LOGO + Ansi.ENDC
        + '\n version 2.0, © Lorelei Chevroulet' + 2 * '\n'
    )
    while True:
        mode = select_mode()
        print('\n')
        if mode == '1':
            text_conversion()
        elif mode == '2':
            export_long()
        elif mode == '3':
            pick_rand()
        elif mode == '4':
            match_list()
        else:
            print(Ansi.FAIL + 'Error: mode ' + mode + ' does not exist.' + Ansi.ENDC)
            sys.exit()


def select_mode():
    """Mode selection dialogue."""
    print(
        Ansi.BOLD
        + '1)  Select mode: \n\n'
        + Ansi.ENDC
        + '    1: Prune HTML or convert to markdown\n'
        + '    2: Select longer text files \n'
        + '    3: Select n files (randomly or sequentially)\n'
        + '    4: Match files against list\n'
    )
    return input(PROMPT)


def select_dir_prompt():
    """Directory selection prompt."""
    directory = Path(input(PROMPT).strip().replace("\\", ""))
    print(f'\n    Looking for \'{Ansi.BR_BLUE}{directory}{Ansi.ENDC}\'...')
    if not directory.exists():
        print('\n' + Ansi.FAIL + Ansi.BOLD
              + f'    Path \'{Ansi.BR_BLUE}{directory}{Ansi.FAIL}\' not found.'
              + Ansi.ENDC
              )
        sys.exit()
    return directory


def select_input_dir():
    """Input directory selection with confirmation of n files existing."""
    print(Ansi.BOLD + '2)  Enter text files directory:\n' + Ansi.ENDC)
    directory = select_dir_prompt()
    print(
        '\n    '
        + Ansi.BR_GREEN + Ansi.BOLD
        + str(len(list(directory.glob('*'))))
        + ' file(s) found'
        + Ansi.ENDC
        + '. Continue? y/n \n'
    )
    if input(PROMPT) == 'y':
        print('\n')
        return directory
    else:
        sys.exit()


def select_out_dir():
    """Output directory selection with confirmation of directory existence."""
    print(Ansi.BOLD + '3)  Enter output directory:\n' + Ansi.ENDC)
    out_dir = select_dir_prompt()
    print(
        '\n    '
        + Ansi.BR_GREEN + Ansi.BOLD
        + 'Directory found'
        + Ansi.ENDC
        + '. Continue? y/n \n'
    )
    if input(PROMPT) == 'y':
        print('\n')
        return out_dir
    else:
        sys.exit()


def select_conversion_tool():
    print(
        Ansi.BOLD
        + '    Select tool: \n\n'
        + Ansi.ENDC
        + '    1: HTML remover via Python find().\n'
        + '    2: HTML to markdown translation via html2text module. \n'
        + '    3: Extraction of specific markdown content via Python find().\n'
    )
    return input(PROMPT)


def text_conversion():
    global total_files_queued
    conversion_tool = select_conversion_tool()
    print('\n')
    input_directory = select_input_dir()
    out_directory = select_out_dir()
    total = str(len(list(input_directory.glob('*'))))
    print(
        f'{Ansi.BOLD}4)  Processing file(s): {Ansi.ENDC}\n\n'
        + f'    Total file(s): {Ansi.BOLD}{total:6}{Ansi.ENDC}'
    )
    available_cpu = cpu_count() - 1
    print(
        f'    Using {Ansi.BOLD}{available_cpu}{Ansi.ENDC} CPU core(s) for multithreading.\n\n\n'
    )
    pool = Pool(processes=(cpu_count() - 1))  # Create a pool with one slot fewer than amount of cpu cores.
    num = 0
    conversion_progress(total=total, status='init')
    for file in input_directory.iterdir():
        num += 1
        total_files_queued = num
        pool.apply_async(
            conversion_process, args=(conversion_tool, file, out_directory),
            callback=conversion_progress
        )
    pool.close()
    pool.join()
    print(
        f'\n    {Ansi.BOLD}{Ansi.BR_GREEN}Process complete{Ansi.ENDC}. \n'
    )


def conversion_progress(*args, **kwargs):
    global total_files_processed
    global total_files_queued
    if kwargs.get('status', None) == 'init':
        total_files_processed = 0
    else:
        total_files_processed = total_files_processed + 1
    print(
        2 * (Ansi.UP + Ansi.CLINE)
        + f'    Files queued     Files processed\n'
        + f'    {Ansi.BOLD}{total_files_queued:12}{Ansi.ENDC}  /  '
        + f'{Ansi.BR_GREEN}{Ansi.BOLD}{total_files_processed:<12}{Ansi.ENDC}'
    )


def conversion_process(conversion_tool, file, out_directory):
    if not file.name == '.DS_Store':
        content = import_text(file)
        if conversion_tool == '1':
            export = html_slice(content)
        elif conversion_tool == '2':
            export = html_to_markdown(content)
        elif conversion_tool == '3':
            export = markdown_slice(content)
        else:
            sys.exit()
        if export is not None:
            export_text(out_directory, export, file.name)


def import_text(file):
    try:
        with file.open('r', encoding='utf-8') as file:
            return file.read()
    except Exception:
        print(
            Ansi.FAIL + Ansi.BOLD
            + 'Error while accessing file '
            + file.name
            + Ansi.ENDC
            + 4 * '\r'
        )


def export_long():
    directory = select_input_dir()
    out_directory = select_out_dir()
    print(Ansi.BOLD + '4)  Processing file(s):' + 3 * '\n' + Ansi.ENDC)
    num = 0
    num_file = 0
    total = str(len(list(directory.glob('*'))))
    for file in directory.iterdir():
        num += 1
        print(
            2 * (Ansi.UP + Ansi.CLINE)
            + f'    {Ansi.BR_BLUE}{num:6}{Ansi.ENDC}/{total:6} | File name\n'
            + 20 * ' ' + file.name
        )
        time.sleep(0)
        if not file.name == '.DS_Store':
            content = import_text(file)
            if len(content) > 500:
                export = content
                if export is not None:
                    export_text(out_directory, export, file.name)
                    num_file = num_file + 1
    print(
        f'    {num_file:6} file(s) exported.'
    )
    return


def pick_rand():
    directory = select_input_dir()
    out_directory = select_out_dir()
    mode = str(input(Ansi.BOLD + '    Sequential (s) or random (r)? \n\n' + Ansi.ENDC + PROMPT))
    print('\n')
    num = 0
    num_file = 0
    total = str(len(list(directory.glob('*'))))
    dir_list = list(directory.glob('*'))
    if mode == 'r':
        n = int(input(Ansi.BOLD + '     How many random files? \n\n' + Ansi.ENDC + PROMPT))
        print('\n')
        picked_files = random.sample(dir_list, n)
    elif mode == 's':
        n = int(input(Ansi.BOLD + '    Every which file? \n\n' + Ansi.ENDC + PROMPT))
        print('\n')
        picked_files = dir_list[0::n]
    else:
        return
    print(Ansi.BOLD + '4)  Processing file(s):' + 3 * '\n' + Ansi.ENDC)
    for file in directory.iterdir():
        num += 1
        print(
            2 * (Ansi.UP + Ansi.CLINE)
            + f'    {Ansi.BR_BLUE}{num:6}{Ansi.ENDC}/{total:6} | File name\n'
            + 20 * ' ' + file.name
        )
        if not file.name == '.DS_Store':
            if file in picked_files:
                export = import_text(file)
                if export is not None:
                    export_text(out_directory, export, file.name)
                    num_file = num_file + 1
    print(
        + f'    {num_file:6} file(s) picked and exported.\n'
    )
    return


def export_text(out_dir, export, filename):
    file = Path(out_dir / filename)
    try:
        with file.open('w', encoding='utf-8') as f:
            f.write(export)
    except Exception:
        print('woops!')
        return
    return


def html_slice(content):
    i = 0
    j = 0
    try:
        i = content.find('<h2 class="heading-size-3">Description</h2>')
    except Exception:
        return
    if i == -1:
        return
    test = content[i + 43:len(content)]
    j = test.find('<h2')
    test2 = test[0:j]
    while test2.find('<') > 0:
        k = test2.find('<')
        l = test2.find('>')
        test2 = test2[0:k] + test2[l + 1:len(test2)]
    return test2


def html_to_markdown(content):
    try:
        translated_text = html2text.html2text(content)
    except AttributeError:
        return
    return translated_text


def markdown_slice(content):
    i = 0
    ii = 0
    j = 0
    jj = 0
    k = 0
    kk = 0
    try:
        i = content.find('## Description')
        ii = content.find('##', i+1)
    except Exception:
        return
    if i == -1:
        return
    else:
        sliced_text = content[i + 14:ii]
    try:
        content = content.replace('## [Progress](javascript:)', '## Progress')
        j = content.find('## Progress')
        jj = content.find('##', j+1)
    except Exception:
        pass
    if j != -1:
        sliced_text = sliced_text + content[j + 11:jj]
    try:
        content = content.replace('## [Completion](javascript:)', '## Completion')
        k = content.find('## Completion')
        kk = content.find('##', k+1)
    except Exception:
        pass
    if k != -1:
        sliced_text = sliced_text + content[k + 13:kk]
    return sliced_text


def match_list():
    directory = select_input_dir()
    out_directory = select_out_dir()
    print(Ansi.BOLD + '3.5)  Enter text file path:\n' + Ansi.ENDC)
    quest_list = import_text(select_dir_prompt())
    print(Ansi.BOLD + '4)  Processing file(s):' + 3 * '\n' + Ansi.ENDC)
    num = 0
    num_file = 0
    total = str(len(list(directory.glob('*'))))
    for file in directory.iterdir():
        num += 1
        print(
            2 * (Ansi.UP + Ansi.CLINE)
            + f'    {Ansi.BR_BLUE}{num:6}{Ansi.ENDC}/{total:6} | File name\n'
            + 20 * ' ' + file.name
        )
        if not file.name == '.DS_Store':
            if file.name in quest_list:
                export = import_text(file)
                if export is not None:
                    export_text(out_directory, export, file.name)
                    num_file = num_file + 1
    print(
        f'    {num_file:6} file(s) picked and exported.'
    )
    return


# End-of-file (EOF)
if __name__ == "__main__":
    main()
