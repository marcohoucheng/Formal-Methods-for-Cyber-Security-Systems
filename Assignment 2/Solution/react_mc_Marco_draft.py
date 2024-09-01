import pynusmv
import sys
from pynusmv_lower_interface.nusmv.parser import parser 
from collections import deque

specTypes = {'LTLSPEC': parser.TOK_LTLSPEC, 'CONTEXT': parser.CONTEXT,
    'IMPLIES': parser.IMPLIES, 'IFF': parser.IFF, 'OR': parser.OR, 'XOR': parser.XOR, 'XNOR': parser.XNOR,
    'AND': parser.AND, 'NOT': parser.NOT, 'ATOM': parser.ATOM, 'NUMBER': parser.NUMBER, 'DOT': parser.DOT,

    'NEXT': parser.OP_NEXT, 'OP_GLOBAL': parser.OP_GLOBAL, 'OP_FUTURE': parser.OP_FUTURE,
    'UNTIL': parser.UNTIL,
    'EQUAL': parser.EQUAL, 'NOTEQUAL': parser.NOTEQUAL, 'LT': parser.LT, 'GT': parser.GT,
    'LE': parser.LE, 'GE': parser.GE, 'TRUE': parser.TRUEEXP, 'FALSE': parser.FALSEEXP
}

basicTypes = {parser.ATOM, parser.NUMBER, parser.TRUEEXP, parser.FALSEEXP, parser.DOT,
              parser.EQUAL, parser.NOTEQUAL, parser.LT, parser.GT, parser.LE, parser.GE}
booleanOp = {parser.AND, parser.OR, parser.XOR, parser.XNOR, parser.IMPLIES, parser.IFF}

def spec_to_bdd(model, spec):
    """
    Given a formula `spec` with no temporal operators, returns a BDD equivalent to
    the formula, that is, a BDD that contains all the states of `model` that
    satisfy `spec`
    """
    bddspec = pynusmv.mc.eval_simple_expression(model, str(spec))
    return bddspec
    
def is_boolean_formula(spec):
    """
    Given a formula `spec`, checks if the formula is a boolean combination of base
    formulas with no temporal operators. 
    """
    if spec.type in basicTypes:
        return True
    if spec.type == specTypes['NOT']:
        return is_boolean_formula(spec.car)
    if spec.type in booleanOp:
        return is_boolean_formula(spec.car) and is_boolean_formula(spec.cdr)
    return False
    
def check_GF_formula(spec):
    """
    Given a formula `spec` checks if the formula is of the form GF f, where f is a 
    boolean combination of base formulas with no temporal operators.
    Returns the formula f if `spec` is in the correct form, None otherwise 
    """
    # check if formula is of type GF f_i
    if spec.type != specTypes['OP_GLOBAL']:
        return False
    spec = spec.car
    if spec.type != specTypes['OP_FUTURE']:
        return False
    if is_boolean_formula(spec.car):
        return spec.car
    else:
        return None

def parse_react(spec):
    """
    Visit the syntactic tree of the formula `spec` to check if it is a reactive formula,
    that is wether the formula is of the form
    
                    GF f -> GF g
    
    where f and g are boolean combination of basic formulas.
    
    If `spec` is a reactive formula, the result is a pair where the first element is the 
    formula f and the second element is the formula g. If `spec` is not a reactive 
    formula, then the result is None.
    """
    # the root of a spec should be of type CONTEXT
    if spec.type != specTypes['CONTEXT']:
        return None
    # the right child of a context is the main formula
    spec = spec.cdr
    # the root of a reactive formula should be of type IMPLIES
    if spec.type != specTypes['IMPLIES']:
        return None
    # Check if lhs of the implication is a GF formula
    f_formula = check_GF_formula(spec.car)
    if f_formula == None:
        return None
    # Create the rhs of the implication is a GF formula
    g_formula = check_GF_formula(spec.cdr)
    if g_formula == None:
        return None
    return (f_formula, g_formula)

def find_path(bddfsm, reach, f_state, g_state, l = None, current_bdd = None):
    """ PRINT g_states 
    g_states = bddfsm.pick_all_states(g_state)
    for s in g_states:
        print(s.get_str_values())
    """
    if l == None:
        l = []
    if current_bdd == None:
        current_bdd = reach.diff(reach)
    f_states = bddfsm.pick_all_states(f_state)
    for state in f_states:
        ls = l + [state.get_str_values()]
        #print(ls)
        if current_bdd.intersected(state):
            return False, ls
        if g_state.intersected(state):
            continue
        post_state = bddfsm.post(state) #<class 'pynusmv.dd.BDD'>
        next_bdd = current_bdd.union(state) #<class 'pynusmv.dd.BDD'>
        """ Find POST states
        print("Before checking")
        print("For spec:", state.get_str_values())
        post_states = bddfsm.pick_all_states(post_state)
        for s in post_states:
            print(s.get_str_values())
        print("After checking")
        """
        res = find_path(bddfsm, reach, post_state, g_state, l = ls, current_bdd = next_bdd)
        if res[0] == False:
            return res
    return True, None

def check_react_spec(spec):
    """
    Return whether the loaded SMV model satisfies or not the GR(1) formula
    `spec`, that is, whether all executions of the model satisfies `spec`
    or not. 
    """
    if parse_react(spec) == None:
        return None
    # return pynusmv.mc.check_explain_ltl_spec(spec)
    specs = parse_react(spec) # formulas = (f_formula, g_formula)

    ####################################### SET UP BDD #######################################

    # retrieve model as BddFsm
    bddfsm = pynusmv.glob.prop_database().master.bddFsm
    # compute the set of states of `bddfsm` satisfying `spec`, as a BDD
    bddspec = spec_to_bdd(bddfsm, specs[0])
    bddspec_target = spec_to_bdd(bddfsm, specs[1])

    #################################### REACHABLE STATES ####################################

    # compute the set of reachable states, which is the least fixpoint of 
    # bddfsm's `post` function, starting from its initial states
    reach = bddfsm.init
    new = bddfsm.post(reach)
    while not new.equal(reach.intersection(new)):
        reach = reach.union(new.diff(reach))
        new = bddfsm.post(reach)

    ##########################################################################################

    # retrieve the BDD of reachable states in which spec is true
    intersection = bddspec.intersection(reach) # All type pynusmv.dd.BDD
    # retrieve the BDD of reachable states in which target spec is true
    intersection_target = bddspec_target.intersection(reach)

    enc = bddfsm.bddEnc
    print(enc.stateVars)
    print(enc.inputsVars) # frozenset({'press'})

    # If IVAR exists, then do a POST with this and continue from there...

    res = None
    #res = find_path(bddfsm, reach, intersection, intersection_target)

    # Find trace here...

    return res

if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "filename.smv")
    sys.exit(1)

pynusmv.init.init_nusmv()
filename = sys.argv[1]
pynusmv.glob.load_from_file(filename)
pynusmv.glob.compute_model()
type_ltl = pynusmv.prop.propTypes['LTL']
for prop in pynusmv.glob.prop_database(): # <class 'pynusmv.prop.Prop'>
    spec = prop.expr #<class 'pynusmv.prop.Spec'>
    if prop.type != type_ltl:
        print("property is not LTLSPEC, skipping")
        continue
    print("For spec", spec)

    res = check_react_spec(spec)
    if res == None:
        print('Property is not a GR(1) formula, skipping')
        continue
    if res[0] == True:
        print("Property is respected")
    elif res[0] == False:
        print("Property is not respected")
        print("Counterexample:", res[1])
pynusmv.init.deinit_nusmv()

# To do:
# 1. IVAR failing (switch)
# 2. Build Trace
