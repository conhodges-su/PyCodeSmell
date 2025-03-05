def emptyOrSpacesOnly(line):
    return len(line) == 0 or line.isspace()

# REF: https://stackoverflow.com/questions/11911252/python-jaccard-distance-using-word-intersection-but-not-character-intersection
def jaccard_similarity(string1, string2):
        set1 = set(string1.split())
        set2 = set(string2.split())
        return float( len(set1 & set2) / len(set1 | set2))


def get_prompt_string(prompt_file):
    try:
        with open(prompt_file) as file_handle:
            prompt_str = file_handle.read()
    except SyntaxError as e:
        print(e)
        return ''
    except OSError as e:
        print(e)
        return ''
    else:
        return prompt_str