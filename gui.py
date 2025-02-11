'''
https://docs.pysimplegui.com/en/latest/cookbook/ecookbook/
CAN INSTALL WITH CONDA 

managing ENVS
https://www.rootstrap.com/blog/how-to-manage-your-python-projects-with-pipenv-pyenv
https://thepythoncorner.com/posts/2022-05-07-managing-python-versions-with-pyenv/ 

https://stackoverflow.com/questions/51863225/pyenv-python-command-not-found 

tk-inter fix: do `brew install python-tk`
https://stackoverflow.com/questions/59987762/python-tkinter-modulenotfounderror-no-module-named-tkinter

'''

'''
IDEAS
- long method
    - [x] AST but likely raw string review of finding each function "def" and comparing each
    - [x] NOPE - need to remove docstring code
- long params
    - [x] AST directly with the len(node.args.args) > 3
    - include `self` in length?
- dupe code
    - [ ] learn about jaccard
            - https://stackoverflow.com/questions/11911252/python-jaccard-distance-using-word-intersection-but-not-character-intersection 
    - Dupe code across classes? Or just top-level functions?
            
- GUI
    - [x] PySimpleGui
    - [x] add line # to multi line text input on code loading
    - [x] add text highlighting for long method/param/dupe code
'''

import PySimpleGUI as sg
import os
from analyzers import CodeAnalyzer
from refactor import CodeRefactorer
from constants import (CODE_FONT, 
                       BOLD_FONT, 
                       GREY_TEXT, 
                       PY_FILE, 
                       MAX_FILE_LENGTH, 
                       MAX_LINES_OF_CODE, 
                       MAX_PARAMETER_COUNT
                       )
'''
CONSTANTS 
-- ADD TO SEPARATE UTILS/CONSTANTS.PY FILE
'''

# def is_hidden(fname):
#     return os.path.basename(fname).startswith('.')
'''
END CONSTANTS
'''

### TODO
'''
- DONE add line number to code output for easier reading, https://docs.pysimplegui.com/en/latest/cookbook/ecookbook/elements/multiline-text-output-with-multiple-colors/ 
- DONE update layout when selecting long methods/params from box to highlight the text
- display the duplicate methods
- add button for producing refactored code
- build refactoring class
'''

class SimpleGUI():
    sg.theme('GreenMono')

    def __init__(self):
        self.col = [
            [sg.Text(f'Long Methods (LOC > {MAX_LINES_OF_CODE})', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Listbox(values=[], size=(60,5), key='-METHODS-', enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Text(f'Long Paramter Lists (PARAMS > {MAX_PARAMETER_COUNT})', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Listbox(values=[], size=(60,5), key='-PARAMS-', enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Text('Duplicate Methods', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Listbox(values=[], size=(60,5), key='-DUPES-', select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)]
        ]
        self.layout = [ 
            [sg.Text('Code Smell Detector', font=BOLD_FONT)],
            [sg.Push(), sg.Text('File', size=(8, 1)), sg.Input(key='-FILEINPUT-', default_text = 'Select file to analyze', text_color=GREY_TEXT), sg.FileBrowse(), sg.Button('Open', key='-FOPEN-'), sg.Push()],
            [sg.Text('Code Display', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Push(), sg.Multiline(size=(100, 30), key='-MINPUT-', horizontal_scroll=True, write_only=True, font=CODE_FONT), sg.Push(),
             sg.vtop(sg.Column(self.col)), sg.Push()],
            [sg.Text('')],
            [sg.Push(), sg.Button('Analyze Code', key='-ANALYZE-'), sg.Button('Exit'), sg.Push()]
        ]
        self.window = sg.Window('Code Smell Detector', self.layout, size=(1300,700))
        self.src_code = ''
        self.code_analyzed = False
        self.code_analyzer = None
        self.long_methods = []
        self.long_param_lists = []
        self.duplicate_code = []
 

    def show(self):
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED or event == 'Exit':
                break
            if event == '-FOPEN-':
                self._clear_input_elements()
                self.load_file(values['-FILEINPUT-'])
            if event == '-ANALYZE-':
                self.analyze_code()
            if event in ('-METHODS-','-PARAMS-'):
                selected = values['-METHODS-'] if event == '-METHODS-' else values['-PARAMS-']
                self._jump_to_selected_line(selected)
        self.window.close()
    

    def load_file(self, filename):
        *_, filetype = filename.split('.')
        if filetype != PY_FILE:
            sg.popup('ONLY SUPPORTS .PY FILES!')
        else:
            try:
                with open(filename) as file_handle:
                    self.src_code = file_handle.read()
                    contents = self.get_code_with_linenums() + '\n\n\n'
                    self.window['-MINPUT-'].update(value=contents)
                    self.code_analyzed = False
            except SyntaxError as e:
                print(e)
            except OSError as e:
                print(e)
    

    def get_code_with_linenums(self):
        code_with_line_nums = []
        code_lines = self.src_code.splitlines()
        for i in range(len(code_lines)):
            line_str = f'{(i+1):>3}   ' + code_lines[i]
            code_with_line_nums.append(line_str)
        return '\n'.join(code_with_line_nums)
    

    def analyze_code(self):
        if not self.src_code:
            sg.popup('You must select and load a file before analyzing it!')
        elif self.src_code and not self.code_analyzed:
            self._get_code_metrics()

            self._display_code_metrics()
            self.code_analyzed = True
            if self.long_methods or self.long_param_lists or self.duplicate_code:
                sg.popup("Code smells found!")
        else:
            sg.popup('This code is already analyzed!')
    

    def _get_code_metrics(self):
        self.code_analyzer = CodeAnalyzer(self.src_code)

        self.long_methods = self.code_analyzer.get_long_methods()
        self.long_param_lists = self.code_analyzer.get_long_paramaters()

        # retrieve duplicate code
        # self.duplicate_code = self.code_analyzer.get_similar_methods()       


    def _clear_input_elements(self):
        self.window['-METHODS-'].update(values=[])
        self.window['-PARAMS-'].update(values=[])
        self.window['-DUPES-'].update(values=[])
    

    def _jump_to_selected_line(self, selected):
        try:
            line = int(selected[0].split(':')[1].split(',')[0].strip())
        except ValueError:
            print("could not convert to int")
        except Exception as e:
            print(f"other exception: {e}")
        else:
            if line > 0:
                code_window = self.window['-MINPUT-']
                if code_window is not None:
                  text_widget = code_window.Widget
                  text_widget.see(f'{line}.0')


    def _display_code_metrics(self):
        # update the Long Methods ListBox
        method_lst = [''.join(map(str, (f'LINE:{m[1]:>4}, DEF: ', m[0]))) for m in self.long_methods if self.long_methods]
        self.window['-METHODS-'].update(values=method_lst)

        # update the Long Params ListBox
        param_lst = [''.join(map(str, (f'LINE:{p[1]:>4}, DEF: ', p[0]))) for p in self.long_param_lists if self.long_param_lists]
        self.window['-PARAMS-'].update(values=param_lst)

        # update the dupe code ListBox
        # TODO
        pass

if __name__ == '__main__':
    gui = SimpleGUI()
    gui.show()