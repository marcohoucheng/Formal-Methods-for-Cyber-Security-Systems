import pynusmv
import sys

# Model is of type fsm
def spec_to_bdd(model, spec):
    """
    Return the set of states of `model` satisfying `spec`, as a BDD.
    """
    bddspec = pynusmv.mc.eval_ctl_spec(model, spec)
    return bddspec


def check_explain_inv_spec(spec):
    """
    Return whether the loaded SMV model satisfies or not the invariant
    `spec`, that is, whether all reachable states of the model satisfies `spec`
    or not. Return also an explanation for why the model does not satisfy
    `spec``, if it is the case, or `None` otherwise.

    The result is a tuple where the first element is a boolean telling
    whether `spec` is satisfied, and the second element is either `None` if the
    first element is `True``, or an execution of the SMV model violating `spec`
    otherwise.

    The execution is a tuple of alternating states and inputs, starting
    and ennding with a state. States and inputs are represented by dictionaries
    where keys are state and inputs variable of the loaded SMV model, and values
    are their value.
    """
    ltlspec = pynusmv.prop.g(spec)
    res, trace = pynusmv.mc.check_explain_ltl_spec(ltlspec)
    return res, trace

if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "filename.smv")
    sys.exit(1)

pynusmv.init.init_nusmv()
filename = sys.argv[1]
pynusmv.glob.load_from_file(filename)
pynusmv.glob.compute_model()
invtype = pynusmv.prop.propTypes['Invariant']
# retrieve model as BddFsm
bddfsm = pynusmv.glob.prop_database().master.bddFsm
for prop in pynusmv.glob.prop_database():
    spec = prop.expr
    if prop.type == invtype:
        print("Property", spec, "is an INVARSPEC.")
        print("All the states of fsm satisfying spec")
        bdd = spec_to_bdd(bddfsm, spec)
        satstates = bddfsm.pick_all_states(bdd)
        for state in satstates:
            print(state.get_str_values())
        print("All the states of fsm not satisfying spec")
        # compute complementary of `spec`
        nspec = pynusmv.prop.not_(spec)
        # compute the set of states of `bddfsm` satisfying `nspec`, as a BDD
        bddspec = spec_to_bdd(bddfsm, nspec)
        satstates = bddfsm.pick_all_states(bddspec)
        for state in satstates:
            print(state.get_str_values())
        """
        if res == True:
            print("Invariant is respected")
        else:
            print("Invariant is not respected")
            print(trace)
        """
        print("\n")
    else:
        print("Property", spec, "is not an INVARSPEC, skipped.")

pynusmv.init.deinit_nusmv()
"""
for prop in pynusmv.glob.prop_database():
    spec = prop.expr
    print("For spec", spec)
    print("All the states of fsm satisfying spec")
    bdd = spec_to_bdd(fsm, spec)
    satstates = fsm.pick_all_states(bdd)
    for state in satstates:
        print(state.get_str_values())
    print("\n All the reachable states of fsm satisfying spec")
    bdd = spec_to_bdd(fsm, spec) & fsm.reachable_states
    satstates = fsm.pick_all_states(bdd)
    for state in satstates:
        print(state.get_str_values())
    print("\n")
    res, trace = check_explain_inv_spec(spec)
    if res == True:
        print("Invariant is respected")
    else:
        print("Invariant is not respected")
        print(trace)
    print("\n")

#fsm = pynusmv.glob.prop_database().master.bddFsm #<class 'pynusmv.fsm.BddFsm'>

invtype = pynusmv.prop.propTypes['Invariant'] #invtype=105=prop.type
for prop in pynusmv.glob.prop_database():
    spec = prop.expr
    if prop.type == invtype:
        print("Property", spec, "is an INVARSPEC.")
        res, trace = check_explain_inv_spec(spec)
        if res == True:
            print("Invariant is respected")
        else:
            print("Invariant is not respected")
            print(trace)
    else:
        print("Property", spec, "is not an INVARSPEC, skipped.")
"""

