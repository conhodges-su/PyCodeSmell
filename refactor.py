import os
import re
from dotenv import load_dotenv, dotenv_values
from constants import REFACTOR_PROMPT_FILE, REPLACE_PROMPT_FILE
from utils import get_prompt_string
from openai import OpenAI
load_dotenv()
OPEN_API_KEY = os.getenv('OPEN_API_KEY')

'''
TODO
- finish returning the completion object
- extract the method from the output
- strip old methods from the source code
- update the source with new method
- return new source code 
'''

class CodeRefactorer():
    def __init__(self, src_code, dupe_code_list):
        self.src_code = src_code
        self.updated_src_code = ''
        self.dupe_code_list = dupe_code_list  #[(m1,m2,(start1,end1),(start2,end2),jaccard)]
        self.refactored_code = []
    

    def produce_refactored_code(self):
        self._refactor_duplicate_code()
        self._replace_old_code()
        return self.updated_src_code
    

    def _replace_old_code(self):
        replace_prompt = get_prompt_string(REPLACE_PROMPT_FILE)
        replace_request = self._get_prompt_request_body()
        completion = self._get_llm_request(replace_prompt, replace_request)
        self.updated_src_code = completion.choices[0].message.content
    

    def _get_prompt_request_body(self):
        replace_request = ''
        for i in range(len(self.dupe_code_list)):
            replace_request += f'{i+1}.\n'
            m1, m2, replacement = self._extract_function_names(i)
            replace_request += f'({m1}, {m2}, {replacement})\n'
            replace_request += f'<DUPLICATE METHODS #{i+1}>\n'
            replace_request += f'- {m1}\n- {m2}\n'
            replace_request += f'<UPDATED METHOD #{i+1}>\n'
            replace_request += f'{self.refactored_code[i]}\n'
        replace_request += f'<SOURCE CODE>\n{self.src_code}\n<END SOURCE CODE>'
        return replace_request
    

    def _extract_function_names(self, idx):
        m1, m2, *_ = self.dupe_code_list[idx]
        replacement = self.refactored_code[idx]
        m1 = m1.split('def')[1].strip().split('(')[0]
        m2 = m2.split('def')[1].strip().split('(')[0]
        replacement = replacement.split('def')[1].strip().split('(')[0]
        return (m1, m2, replacement)

    
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
            m1, m2, termini1, termini2, jaccard = method_pair_data
            methods_str += f'{METHOD_BOLD} 1:\n'
            methods_str += f'{m1}\n'
            methods_str += f'{METHOD_BOLD} 2:\n'
            methods_str += f'{m2}\n'
            methods_string_list.append(methods_str)
        return methods_string_list
    

    def _get_llm_request(self, prompt, request):
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": f"{prompt}"},
                {"role": "user", "content": f"{request}"}
            ]
        )
        return completion