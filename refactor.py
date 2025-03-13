import os
import re
# from dotenv import load_dotenv, dotenv_values
from constants import REFACTOR_PROMPT_FILE
from utils import get_prompt_string
from operator import itemgetter
from llm import LLMRequest


class CodeRefactorer():
    def __init__(self, src_code: str, dupe_code_list: list[tuple[str, str, tuple[int, int], tuple[int, int], int]]):
        self.src_code = src_code
        self.updated_src_code = ''
        self.dupe_code_list = dupe_code_list 
        self.refactored_code = []
    

    def produce_refactored_code(self):
        self._refactor_duplicate_code()
        self._remove_duplicate_code()
        self._add_refactored_code()
        self._replace_function_calls()
        return self.updated_src_code
    

    def _extract_function_names(self, idx):
        m1, m2, *_ = self.dupe_code_list[idx]
        replacement = self.refactored_code[idx]
        for method in (m1, m2, replacement):
            method = self._get_func_name_only(method)
        return (m1, m2, replacement)


    def _get_func_name_only(self, method):
        return method.split('def')[1].strip().split('(')[0]

    
    def _refactor_duplicate_code(self):
        refactor_prompt = get_prompt_string(REFACTOR_PROMPT_FILE)
        methods_strings_list = self._method_list_to_string()
        for refactor_request in methods_strings_list:
            completion = self._get_llm_request(refactor_prompt, refactor_request)
            self.refactored_code.append(completion.choices[0].message.content)


    def _method_list_to_string(self):
        METHOD_BOLD = "METHOD"
        methods_string_list = []
        for method_pair_data in self.dupe_code_list:
            methods_str = ''
            m1, m2, *_ = method_pair_data
            methods_str += f'{METHOD_BOLD} 1:\n'
            methods_str += f'{m1}\n'
            methods_str += f'{METHOD_BOLD} 2:\n'
            methods_str += f'{m2}\n'
            methods_string_list.append(methods_str)
        return methods_string_list
    

    def _get_llm_request(self, prompt, request):
        return LLMRequest.sendRequest(prompt, request)
    

    def _remove_duplicate_code(self):
        to_remove = sorted(self._get_remove_termini(), key=itemgetter(0))
        tuple_generator = iter(to_remove)
        refeactored_code_lines = self._add_non_duplicate_code(tuple_generator)
        self.updated_src_code = '\n'.join(refeactored_code_lines)
        

    def _add_refactored_code(self):
        all_new_code = ''
        for new_code in self.refactored_code:
            all_new_code += new_code + '\n'
        self.updated_src_code = all_new_code + '\n' + self.updated_src_code

    
    def _replace_function_calls(self):
        old_to_new_mapping = self._get_old_to_new_mapping()
        # add all keys to regex pattern w/ OR, matching whole words, 
        # with lookahead to confirm function call
        pattern = r'\b(' + \
                  '|'.join(map(re.escape, old_to_new_mapping.keys())) + \
                  r')\b(?=\()'
        self.updated_src_code = re.sub(
            pattern, 
            lambda match: old_to_new_mapping[match.group(1)], 
                          self.updated_src_code
        )
    

    def _get_old_to_new_mapping(self):
        old_to_new_mapping = {}
        for i in range(len(self.dupe_code_list)):
            old_func1, old_func2, new_func = self._extract_function_names(i)
            old_to_new_mapping.update({old_func1 : new_func, 
                                       old_func2 : new_func})
        return old_to_new_mapping


    def _add_non_duplicate_code(self, tuple_generator):
        code_lines = self.src_code.splitlines()
        new_code_lines = []
        start, end = next(tuple_generator)
        for i in range(len(code_lines)):
            if i < start - 1:
                new_code_lines.append(code_lines[i])
            elif i == end:
                new_code_lines.append(code_lines[i])
                try:
                    start, end = next(tuple_generator)
                except StopIteration:
                    start = float('inf')
        return new_code_lines

        
    def _get_remove_termini(self):
        to_remove = []
        for dupe_line in self.dupe_code_list:
            _, _, termini1, termini2, _ = dupe_line
            # to_remove.append(termini1)
            # to_remove.append(termini2)
            to_remove.extend([termini1, termini2])
        return to_remove