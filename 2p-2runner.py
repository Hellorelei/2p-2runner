"""WowHead quest parser, by Lorelei Chevroulet:
This script (1) iterates all text files in a given folder through a predefined
filter. It (2) discards files missing specific tokens, and (3) extracts
the desired tokens in new text files a specified folder.
"""
import sys
import os
from pathlib import Path
import glob
import time
import random
import html2text


class ansi:
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

PROMPT = '    ' + ansi.DIM + '>' + ansi.ENDC


# Code du module
def main():
    '''Main script. Iterates over text files.'''
    print(40 * '░')
    print(
        ansi.BOLD + LOGO + ansi.ENDC
        + '\n version 1.0, © Lorelei Chevroulet' + 2 * '\n'
    )
    while True:
        mode = select_mode()
        print('\n')
        if mode == '1':
            prune_html()
        elif mode == '2':
            export_long()
        elif mode == '3':
            pick_rand()
        else:
            print(ansi.FAIL + 'Error: mode ' + mode + ' does not exist.' + ansi.ENDC)
            sys.exit()


def select_mode():
    print(
        ansi.BOLD
        + '1)  Select mode: \n\n'
        + ansi.ENDC
        + '    1: Prune HTML or Markdown\n'
        + '    2: Filter longer text files \n'
        + '    3: Pick n random files\n'
    )
    return input(PROMPT)


def select_dir():
    print(ansi.BOLD + '2)  Enter text files directory:\n' + ansi.ENDC)
    directory = Path(input(PROMPT).strip().replace("\\", ""))
    print(f'\n    Looking for \'{ansi.BR_BLUE}{directory}{ansi.ENDC}\'...')
    if not directory.exists():
        print('\n' + ansi.FAIL + ansi.BOLD
              + f'    Path \'{ansi.BR_BLUE}{directory}{ansi.FAIL}\' not found.'
              + ansi.ENDC
              )
        sys.exit()
    print(
        '\n    '
        + ansi.BR_GREEN + ansi.BOLD
        + str(len(list(directory.glob('*'))))
        + ' file(s) found'
        + ansi.ENDC
        + '. Continue? y/n \n'
    )
    if input(PROMPT) == 'y':
        print('\n')
        return directory
    else:
        sys.exit()


def select_out_dir():
    print(ansi.BOLD + '3)  Enter output directory:\n' + ansi.ENDC)
    out_dir = Path(input(PROMPT).strip().replace("\\", ""))
    print(f'\n    Looking for \'{ansi.BR_BLUE}{out_dir}{ansi.ENDC}\'...')
    if not out_dir.exists():
        print('\n' + ansi.FAIL + ansi.BOLD
              + f'    Path \'{ansi.BR_BLUE}{out_dir}{ansi.FAIL}\' not found.'
              + ansi.ENDC
              )
        sys.exit()
    print(
        '\n    '
        + ansi.BR_GREEN + ansi.BOLD
        + 'Directory found'
        + ansi.ENDC
        + '. Continue? y/n \n'
    )
    if input(PROMPT) == 'y':
        print('\n')
        return out_dir
    else:
        sys.exit()


def select_version():
    print(
        ansi.BOLD
        + '    Select parser version: \n\n'
        + ansi.ENDC
        + '    1: V1 (HTML)\n'
        + '    2: V2 (html2text) \n'
        + '    3: V3 (Markdown)\n'
    )
    return input(PROMPT)


def prune_html():
    version = select_version()
    print('\n')
    directory = select_dir()
    out_directory = select_out_dir()
    print(ansi.BOLD + '4)  Processing file(s):' + 3 * '\n' + ansi.ENDC)
    num = 0
    total = str(len(list(directory.glob('*'))))
    for file in directory.iterdir():
        num += 1
        print(
            2 * (ansi.UP + ansi.CLINE)
            + f'    {ansi.BR_BLUE}{num:6}{ansi.ENDC}/{total:6} | File name\n'
            + 20 * ' ' + file.name
        )
        if not file.name == '.DS_Store':
            content = import_text(file)
            if version == '1':
                export = html_slice(content)
            elif version == '2':
                export = html_slice_v2(content)
            elif version == '3':
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
            ansi.FAIL + ansi.BOLD
            + 'Error while accessing file '
            + file.name
            + ansi.ENDC
            + 4 * '\r'
        )


def export_long():
    directory = select_dir()
    out_directory = select_out_dir()
    print(ansi.BOLD + '4)  Processing file(s):' + 3 * '\n' + ansi.ENDC)
    num = 0
    num_file = 0
    total = str(len(list(directory.glob('*'))))
    for file in directory.iterdir():
        num += 1
        print(
            2 * (ansi.UP + ansi.CLINE)
            + f'    {ansi.BR_BLUE}{num:6}{ansi.ENDC}/{total:6} | File name\n'
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
    directory = select_dir()
    out_directory = select_out_dir()
    n = int(input('3.5) How many random files? \n' + PROMPT))
    print(ansi.BOLD + '4)  Processing file(s):' + 3 * '\n' + ansi.ENDC)
    num = 0
    num_file = 0
    total = str(len(list(directory.glob('*'))))
    dir_list = list(directory.glob('*'))
    picked_files = random.sample(dir_list, n)
    time.sleep(5)
    for file in directory.iterdir():
        num += 1
        print(
            2 * (ansi.UP + ansi.CLINE)
            + f'    {ansi.BR_BLUE}{num:6}{ansi.ENDC}/{total:6} | File name\n'
            + 20 * ' ' + file.name
        )
        time.sleep(0)
        if not file.name == '.DS_Store':
            if file in picked_files:
                content = import_text(file)
                export = content
                if export is not None:
                    export_text(out_directory, export, file.name)
                    num_file = num_file + 1
    print(
        f'    {num_file:6} file(s) picked and exported.'
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
        time.sleep(0)
    return test2


def html_slice_v2(content):
    sliced_text = html2text.html2text(content)
    return sliced_text

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

# End-of-file (EOF)
if __name__ == "__main__":
    main()
