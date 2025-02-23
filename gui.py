import PySimpleGUI as sg
import os
import threading
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
- DONE add line number to code output for easier reading, https://docs.pysimplegui.com/en/latest/cookbook/ecookbook/elements/multiline-text-output-with-multiple-colors/ 
- DONE update layout when selecting long methods/params from box to highlight the text
- DONE display the duplicate methods
- DONE add button for producing refactored code
- DONE build refactoring class
- decide to continue using LLM for code update, or do it directly to speed up
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
            [sg.Listbox(values=[], size=(60,5), key='-DUPES-', enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Button('Refactor Code', key='-REFACTOR-')]
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
        self.filename = ''
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
            if event in ('-METHODS-','-PARAMS-', '-DUPES-'):
                selected = values[event]
                self._jump_to_selected_line(selected)
            if event == '-REFACTOR-':
                self._refactor_code()
        self.window.close()
    

    def load_file(self, filename):
        *_, filetype = filename.split('.')
        if filetype != PY_FILE:
            sg.popup('ONLY SUPPORTS .PY FILES!')
        else:
            self.filename = filename
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
        self.duplicate_code = self.code_analyzer.get_similar_methods()       


    def _clear_input_elements(self):
        self.filename = ''
        for elem in ['-METHODS-', '-PARAMS-', '-DUPES-']:
            self.window[elem].update(values=[])
    

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
        method_lst = self._format_duplicate_methods()
        self.window['-DUPES-'].update(values=method_lst)
    

    def _format_duplicate_methods(self):
        count = 0
        method_lst = []
        for dupe_rows in self.duplicate_code:
            m1, m2, t1, t2, jaccard_val = dupe_rows
            m1 = m1.splitlines()[0]
            m2 = m2.splitlines()[0]
            method_lst.append(f'LINE: {t1[0]}, #{count+1}. {m1}')
            method_lst.append(f'LINE: {t2[0]}, #{count+1}. {m2}')
            count += 1
        return method_lst

    def _refactor_code(self):
        if self.duplicate_code:
            refactorer = CodeRefactorer(self.src_code, self.duplicate_code)
            refactored_code = refactorer.produce_refactored_code()
            self._write_refactored_code_to_file(refactored_code)
            sg.popup(f'Refactored code output to:\n{os.getcwd()}')
        else:
            sg.popup('No duplicate code to refactor!')
    

    def _write_refactored_code_to_file(self, refactored_code):
        updated_filename = self.filename.split('.')[0] + '_refactor.py'
        print(updated_filename)
        try:
            with open(updated_filename, 'w') as file:
                file.write(refactored_code)
        except SyntaxError as e:
            print(e)
        except OSError as e:
            print(e)
    

if __name__ == '__main__':
    gui = SimpleGUI()
    gui.show()