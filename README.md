# Ouroboros

Merges a given input `.py` with all its local dependencies. The convention is that imports that use adjacent `.py` files,
should only contain function definitions or classes, no module level code.

Currently this is a naive first version created for obs-studio development. obs-studio only takes one `.py` file and
considering the amount of code one must write, it can easily become unwieldy during development, so keeping separate
files for libraries and objects makes things easier. At the end, Ouroboros can do the naive merging by making sure to
deduplicate library imports and directly merge, taking into account dependencies between local files for order of merging.
At the end, only adds any module-level code from the `.py` given in the command line, as it's assumed to be the __main__
equivalent in this scenario.

For module-level function definitions, there is currently no conflict resolution, or even analysis. The developer assumes
the onus for this task. For reference, you can use `pylint --errors-only output.py` to get a list of errors without running
the resulting merged `.py`.

## Installation

```cmd
pip install ouroboros
```

## Usage

```cmd
ouroboros -input <input_file> -output <output_file>
```

- input_file can be a relative path to the `.py` you want to merge its dependencies into.

- output_file can be a relative or absolute path, a filename (will be output in the same path as the input_file) and can be
completely omitted, in which case, it defaults to "output.py" and is, again, written adjacent to the input_file.

## Naming

It's a weird attempt at a pun. Ouroboros is the snake that feeds on itself. The use of a python executable with a python AST
library to analyze and merge multiple pythons into one, sounds similar in concept. I'm not proud of this "dad joke" but it does
sound cool.
