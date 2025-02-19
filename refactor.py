import os
from dotenv import load_dotenv, dotenv_values
from constants import PROMPT_FILE
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
OR
- output the file immediately.
'''

class CodeRefactorer():
    def __init__(self, src_code, dupe_code_list):
        self.src_code = src_code
        self.dupe_code_list = dupe_code_list
        self.prompt = get_prompt_string(PROMPT_FILE)
    

    def produce_refactored_code(self):
        # Pass to refactor duplicate code
        # Get the newly refactored method
        # replace the method in the source code
        # return the new source code
        # OR
        # write a file to CWD with the new source code
        return self.src_code
    

    def _refactor_duplicate_code(self):
        methods_str = self._method_list_to_string()
        completion = self._get_llm_refactored_code(methods_str)


    def _method_list_to_string(self):
        METHOD_BOLD = "METHOD"
        methods_str = ''
        i = 1
        for method in self.dupe_code_list:
            methods_str += f'{METHOD_BOLD} {i}:\n'
            methods_str += f'{method}\n'
            i += 1
        return methods_str
    
    def _get_llm_refactored_code(self, methods_str):
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        prompt = get_prompt_string(PROMPT_FILE)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": f"{prompt}"},
                {"role": "user", "content": f"{methods_str}"}
            ]
        )
        return completion
    
    def _extract_new_method(self, completion):
        pass
