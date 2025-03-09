import ast_utils
import textwrap
from utils import emptyOrSpacesOnly, jaccard_similarity, get_prompt_string
from llm import LLMRequest
from constants import (MAX_LINES_OF_CODE, MAX_PARAMETER_COUNT, 
                       MAX_JACCARD_SIMILARITY,  SELF_PARAM_VALUE,
                       SEMANTIC_DUPE_PROMPT_FILE)

class MethodAnalyzer():
    def __init__(self, method_lst: list[str], start: int, end: int):
        self.method_lst = method_lst
        self.start = start
        self.end = end
        self.lines_of_code = self._set_lines_of_code()
        self.param_count = self._set_param_count()
        self.method_name = method_lst[0]
    

    def get_method_attributes(self):
        return (self.method_name, 
                self.start, 
                self.end, 
                self.lines_of_code, 
                self.param_count)


    def _set_lines_of_code(self):
        count = len(self.method_lst)
        for line in self.method_lst:
            if emptyOrSpacesOnly(line):
                count -= 1
        return count


    def _set_param_count(self):
        ast_tree = ast_utils.tree_parse(textwrap.dedent('\n'.join(self.method_lst)))
        param_names = ast_utils.get_param_names(ast_tree)
        if SELF_PARAM_VALUE in param_names:
            param_names.remove(SELF_PARAM_VALUE)
        return len(param_names)


class CodeAnalyzer():
    def __init__(self, src_code: str):
        self.src_code = src_code
        self.method_lines = ast_utils.extract_method_lines(self.src_code)
        self.method_analyzers = self._analyze_methods()


    def get_long_methods(self):
        long_methods = []
        for method_obj in self.method_analyzers:
            name, start, end, lines, _ = method_obj.get_method_attributes()
            if lines > MAX_LINES_OF_CODE:
                long_methods.append( (name, start, end, lines) )
        return long_methods


    def get_long_paramaters(self):
        long_param_lst = []
        for method_obj in self.method_analyzers:
            name, start, *_, param_count = method_obj.get_method_attributes()
            if param_count > MAX_PARAMETER_COUNT:
                long_param_lst.append( (name, start, param_count) )
        return long_param_lst


    def get_similar_methods(self):
        similar_methods = []
        methods = self._extract_methods(self.method_lines)
        for i in range(len(methods)):
            start, end = self.method_lines[i]
            methods[i] = ('\n'.join(methods[i]), start, end)

        compared_methods = self._compare_methods(methods)
        for method in compared_methods:
            *_, jaccard_val = method
            if jaccard_val >= MAX_JACCARD_SIMILARITY:
                similar_methods.append(method)
        return similar_methods


    def _analyze_methods(self):
        analyzers = []
        collected_methods = self._extract_methods(self.method_lines)
        for i in range(len(collected_methods)):
            start, end = self.method_lines[i]
            analyzers.append(MethodAnalyzer(collected_methods[i], start, end)) 
        return analyzers
    

    def _extract_methods(self, method_lines):
        src_code_lines = self.src_code.splitlines()
        methods = []
        for method_terminuses in method_lines:
            start, end = method_terminuses
            method = []
            for i in range(start - 1, end):
                method.append(src_code_lines[i])
            methods.append(method)
        return methods


    def _compare_methods(self, methods_list):
        length = len(methods_list)
        compared_methods = []
        for i in range(length - 1):
            for j in range(i+1, length):
                method1, start1, end1 = methods_list[i]
                method2, start2, end2 = methods_list[j]
                jaccard_value = jaccard_similarity(method1, method2)
                compared_methods.append( (method1,
                                          method2,
                                          (start1, end1),
                                          (start2, end2),
                                          jaccard_value ) )
        return compared_methods

    def semantic_dupe_check(self):
        devPrompt = get_prompt_string(SEMANTIC_DUPE_PROMPT_FILE)
        completion = LLMRequest.sendRequest(devPrompt, self.src_code, 'gpt-4o')
        semantic_dupe_string = completion.choices[0].message.content
        semantic_dupe_list = semantic_dupe_string.splitlines()
        for index, value in enumerate(semantic_dupe_list):
            m1, m2 = value.split('|')
            m1 = textwrap.dedent(m1)
            m2 = textwrap.dedent(m2)
            semantic_dupe_list[index] = (m1, m2)
        return semantic_dupe_list