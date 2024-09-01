# Assignment 1 - Invariant verification

In this assignment you will implement the symbolic algorithm for invariant verification, using BDDs as data structure to represent and manipulate regions.

The attached `inv_mc.smv` file contains a python script that uses the pynusmv library to verify invariants of SMV programs.

Using the `inv_mc.smv` script as a starting point, implement a function `check_explain_inv_spec(spec)` that respects the following specifications:

- the function checks if spec is an invariant of the loaded SMV model or not, that is, whether all the reachable states of the model satisfy spec or not.

- the function must return an explanation for why the model does not satisfy spec, if it is the case;

- the return value is a tuple where the first element is True and the second element is None if the invariant is true. When the invariant is not verified, the first element is False and the second element is an execution of the SMV model that violates spec;

- the execution is a tuple of alternating states and inputs, starting and ending with a state. States and inputs are represented by dictionaries where keys are state and inputs variable of the loaded SMV model, and values are their value.

## The pynusmv library

pynusmv is a python wrapper to NuSMV model checking algorithms.The library consists of several modules. To implement the project you can use only the following modules:

- init
- glob
- fsm, except for method reachable_states
- prop
- dd 
- the helper function spec_to_bdd (model, spec) included in inv_mc.py to convert a property to an equivalent BDD.

You can find more information about the pynusmv library at the websites http://lvl.info.ucl.ac.be/Tools/PyNuSMV and https://pynusmv.readthedocs.io.

Binary files to install pynusmv on recent Python versions are available at https://github.com/davidebreso/pynusmv/releases/latest

## Examples

The archive **examples.zip** contains some SMV programs to test your implementation.

---

## How to work with this LaTeX template

- If you want to add a section, go to res/sections, create `new_section.tex`, then go to `./listOfSections.tex` in the main folder and add your new section to the document with the following command (`.tex` is not required):

```latex
/includeSection{newsection} 
```

- If you want to add a package, add it to the `./config/packages.tex` file.
- If you want to add a command, add it to the `./config/commands.tex` file.
