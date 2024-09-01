# Assignment 2 - Verification of reactivity properties

In this assignment you will implement a symbolic algorithm for the verification of a special class of LTL formulas, using BDDs as data structure to represent and manipulate regions. The class of formulas considered by the algorithm is called "reactivity" properties and have the special form:
<div align="center">

$\square\diamond f \rightarrow \square\diamond g$ </div>
where 
$f$
and
$g$ 
are Boolean combination of base formulas with no temporal operators. Some examples of reactivity properties for the Railroad Controller are listed below.

* If the west train is repeatedly waiting, then it will be repeatedly on the bridge:

  $\square\diamond train_w.mode = wait \rightarrow \square\diamond train_w.mode = bridge$

* If the west train is repeatedly waiting, then it will be repeatedly on the bridge:

  $\square\diamond train_w.mode = wait \rightarrow \square\diamond (signal_w = green\ \vee\ train_e.mode = bridge)$

* If the west train is repeatedly waiting with the east train off the bridge, then the west train will be repeatedly on the bridge:

  $\square\diamond(\neg(train_e.mode = bridge)\ \wedge\ train_w.mode = wait ) \rightarrow \square\diamond train_w.mode = bridge$

#### The following formulas **are not** reactivity properties, and should be discarded by the algorithm:

* $\square(train_w.mode = wait \rightarrow \diamond signal_w = green)$

* $\square\diamond \neg (train_e.mode = bridge ) \rightarrow \square\diamond train_w.mode = wait \rightarrow \square\diamond train_w.mode = bridge$

* $\square\diamond train_w.mode = wait \rightarrow \square\diamond (signal_w = green\ \wedge\ \bigcirc train_w.mode = bridge )$

The attached `react_mc.smv` file contains a python script that uses the `pynusmv` library to verify reactivity properties of SMV programs. The script uses the function `parse_react(spec)` to check if `spec` is a reactivity formula, and skips all formulas that are not in the correct form. 

Using the `react_mc.smv` script as a starting point, (re)implement the function `check_react_spec(spec)`, respecting the following specifications:

* the function checks if the reactivity formula `spec` is satisfied by the loaded SMV model or not, that is, whether all the executions of the model satisfy `spec` or not.

* the return value of `check_react_spec(spec)` is a tuple where the first element is `True` and the second element is `None` if the formula is true. When the formula is not verified, the first element is `False` and the second element is an execution of the SMV model that violates `spec`. The function returns `None` if `spec` is not a reactivity formula;

* the execution is a tuple of alternating states and inputs, starting and ending with a state. States and inputs are represented by dictionaries where keys are state and inputs variable of the loaded SMV model, and values are their value;

* the execution is looping: the last state should be somewhere else in the sequence to indicate the starting point of the loop.

---

## How to work with this LaTeX template

- If you want to add a section, go to res/sections, create `new_section.tex`, then go to `./listOfSections.tex` in the main folder and add your new section to the document with the following command (`.tex` is not required):


```latex
/includeSection{newsection} 
```

- If you want to add a package, add it to the `./config/packages.tex` file.
- If you want to add a command, add it to the `./config/commands.tex` file.
