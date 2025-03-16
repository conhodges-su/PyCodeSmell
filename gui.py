import PySimpleGUI as sg
import os
from textwrap import dedent
from analyzers import CodeAnalyzer
from refactor import CodeRefactorer
from constants import (CODE_FONT, BOLD_FONT, GREY_TEXT, PY_FILE,  
                       MAX_LINES_OF_CODE, MAX_PARAMETER_COUNT)


class SimpleGUI():
    sg.theme('GreenMono')

    def __init__(self):
        self.col = self._column_list()
        self.layout = self._layout_list()
        self.window = sg.Window('Code Smell Detector', self.layout, size=(1300,750))
        self.src_code = ''
        self.filename = ''
        self.code_analyzed = False
        self.semantic_checked = False
        self.code_analyzer = None
        self.long_methods = []
        self.long_param_lists = []
        self.duplicate_code = []
        self.semantic_dupes = []
    

    def _column_list(self):
        return [
            [sg.Text(f'Long Methods (LOC > {MAX_LINES_OF_CODE})', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Listbox(values=[], size=(60,5), key='-METHODS-', enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Text(f'Long Paramter Lists (PARAMS > {MAX_PARAMETER_COUNT})', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Listbox(values=[], size=(60,5), key='-PARAMS-', enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Text('Duplicate Methods', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Listbox(values=[], size=(60,6), key='-DUPES-', enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)],
            [sg.Button('Refactor Code', key='-REFACTOR-', disabled=True, disabled_button_color='grey')],  
            [sg.Text('Semantic Duplicates', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Listbox(values=[], size=(60,8), key='-SEMANTIC-DUPES-', enable_events=True, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE)]
        ]


    def _layout_list(self):
        return [
            [sg.Text('Code Smell Detector', font=BOLD_FONT)],
            [sg.Push(), sg.Text('File', size=(8, 1)), sg.Input(key='-FILEINPUT-', default_text = 'Select file to analyze', text_color=GREY_TEXT), sg.FileBrowse(), sg.Button('Open', key='-FOPEN-'), sg.Push()],
            [sg.Text('Code Display', text_color='white', background_color='magenta', font=BOLD_FONT)],
            [sg.Push(), sg.Multiline(size=(90, 30), key='-MINPUT-', horizontal_scroll=True, write_only=True, font=CODE_FONT), sg.Push(), sg.vtop(sg.Column(self.col)), sg.Push()],
            [sg.Text('')],
            [sg.Push(), sg.Button('Analyze Code', key='-ANALYZE-'), sg.Button('Semantic Dupe Check', key='-SEMANTIC-'), sg.Button('Exit'), sg.Push()]
        ]


    def show(self):
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED or event == 'Exit':
                break
            else:
                self._event_handler(event, values)
        self.window.close()
    

    def _event_handler(self, event, values):
        if event == '-FOPEN-':
            self._clear_input_elements()
            self._load_file(values['-FILEINPUT-'])
        elif event == '-ANALYZE-':
            self._analyze_code()
            self._check_if_duplicate_present()
            self._prompt_to_refactor()
        elif event == '-SEMANTIC-':
            self._identify_semantic_dupes()
        elif event in ('-METHODS-','-PARAMS-', '-DUPES-'):
            selected = values[event]
            self._jump_to_selected_line(selected)
        elif event == '-REFACTOR-':
            self._refactor_code()


    def _load_file(self, filename):
        *_, filetype = filename.split('.')
        if filetype != PY_FILE:
            sg.popup('ONLY SUPPORTS .PY FILES!')
        else:
            self.filename = filename
            try:
                with open(filename) as file_handle:
                    self.src_code = file_handle.read()
                    contents = self._get_code_with_linenums() + '\n\n\n'
                    self.window['-MINPUT-'].update(value=contents)
                    self.code_analyzed = False
                    self.semantic_checked = False
            except (SyntaxError, OSError) as e:
                print(e)
    

    def _get_code_with_linenums(self):
        code_with_line_nums = []
        code_lines = self.src_code.splitlines()
        for i in range(len(code_lines)):
            line_str = f'{(i+1):>3}   ' + code_lines[i]
            code_with_line_nums.append(line_str)
        return '\n'.join(code_with_line_nums)
    

    def _analyze_code(self):
        if not self.src_code:
            sg.popup('You must select and load a file before analyzing it!')
        elif self.src_code and not self.code_analyzed:
            self._get_code_metrics()
            self._display_code_metrics()
            self.code_analyzed = True
            if self.long_methods or self.long_param_lists or self.duplicate_code:
                sg.popup("Code smells found!")
            else:
                sg.popup("No code smells found!")    
        else:
            sg.popup('This code is already analyzed!')
    

    def _check_if_duplicate_present(self):
        is_disabled = False if self.duplicate_code else True
        self.window['-REFACTOR-'].update(disabled=is_disabled)
    

    def _prompt_to_refactor(self):
        if not self.duplicate_code:
            return
        choice = sg.popup_yes_no('Duplicate code detected, refactor?')
        if choice == 'Yes':
            self._refactor_code()


    def _identify_semantic_dupes(self):
        if not self.code_analyzed:
            sg.popup('Analyze the code before checking for semantic duplicates!')
        elif not self.semantic_checked:
            self.semantic_dupes = self.code_analyzer.semantic_dupe_check()
            self._display_code_metrics()
            self.code_analyzed = True
        else:
            sg.popup('Already checked for semantic code')


    def _get_code_metrics(self):
        self.code_analyzer = CodeAnalyzer(self.src_code)
        self.long_methods = self.code_analyzer.get_long_methods()
        self.long_param_lists = self.code_analyzer.get_long_paramaters()
        self.duplicate_code = self.code_analyzer.get_similar_methods() 


    def _clear_input_elements(self):
        self.filename = ''
        for elem in ['-METHODS-', '-PARAMS-', '-DUPES-', '-SEMANTIC-DUPES-']:
            self.window[elem].update(values=[])
        for value_arr in [self.duplicate_code, self.long_methods, self.long_param_lists, self.semantic_dupes]:
            value_arr.clear()
        self._check_if_duplicate_present()
    

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
        method_lst = self._get_format_list(self.long_methods)
        param_lst = self._get_format_list(self.long_param_lists)
        dupe_lst = self._format_duplicate_methods()
        semantic_dupes_formatted = [elem for item in self.semantic_dupes for elem in item]

        fields_to_display = [(method_lst, '-METHODS-'), (param_lst, '-PARAMS-'),
                           (dupe_lst, '-DUPES-'), (semantic_dupes_formatted, '-SEMANTIC-DUPES-')]
        for item_list, key in fields_to_display:
            self.window[key].update(values=item_list)
    

    def _get_format_list(self, format_list):
        return [''.join(map(str, (f'LINE:{attribute[1]:>4}, DEF: {dedent(attribute[0])}, COUNT: {attribute[2]}', ))) for attribute in format_list if format_list]
    

    def _format_duplicate_methods(self):
        count = 0
        method_lst = []
        for dupe_rows in self.duplicate_code:
            method1, method2, term1, term2, jaccard = dupe_rows
            for method, termini in [(method1, term1), (method2, term2)]:
                method_stripped = dedent(method.splitlines()[0])
                method_lst.append((f'LINE: {termini[0]}, #{count+1}. {method_stripped}, JACCARD: {jaccard:.2f}'))
            count += 1
        return method_lst


    def _refactor_code(self):
        if self.duplicate_code:
            refactorer = CodeRefactorer(self.src_code, self.duplicate_code)
            refactored_code = refactorer.produce_refactored_code()
            filename = self._write_refactored_code_to_file(refactored_code)
            sg.popup(f'FILE: {filename}\nRefactored code output to:\n{os.getcwd()}', title='Code Output')
        else:
            sg.popup('No duplicate code to refactor!')
    

    def _write_refactored_code_to_file(self, refactored_code):
        updated_filename = self.filename.split('.')[0] + '_refactor.py'
        try:
            with open(updated_filename, 'w') as file:
                file.write(refactored_code)
        except SyntaxError as e:
            print(e)
        except OSError as e:
            print(e)
        finally:
            return updated_filename.split('/')[-1]
    

if __name__ == '__main__':
    gui = SimpleGUI()
    gui.show()