# PyCodeSmell
## *Software Refactoring and Design*, Winter '25

### About the Project

PyCodeSmell was created for my Master's Degree *Software Refactoring and Design* course at Seattle University. The program detects 3 common code smells -- long methods, long parameter lists, and duplicate (structural) code -- all presented to users within a simple GUI. Additionally, duplicate code refactoring and semantic duplicate detection is provided with help from OpenAI LLMs.

### Built With

This project utilizes the OpenAI Python chat completion API to support proposing a single method to replace multiple duplicate methods, as well as detecting semantically duplicate code (code with the same behavior but different syntax).

PySimpleGUI was used as the GUI framework, however, as of March '25 is no longer maintained and versions 5+ cannot be accessed without a personal developer (created prior to the project close announcement). Older PySimpleGUI versions (< 5) are available to fork on other Github pages for those interested in using this framework for their own projects. 

### Goals of the Project

Its purpose is threefold:
1. To provide a GUI for interacting with source code, and displaying code smell metrics
2. To analyze code for long methods (15+ LOC), long parameter lists (3+ parameters), and structural (types I-III) duplicate methods w/ Jaccard value >= 0.75
3. If duplicate code is present, refactor the code and output to a new file.


