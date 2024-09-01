import pynusmv
import sys
from pynusmv_lower_interface.nusmv.parser import parser 
from collections import deque

specTypes = {
    'LTLSPEC': parser.TOK_LTLSPEC, 
    'CONTEXT': parser.CONTEXT,
    'IMPLIES': parser.IMPLIES, 
    'IFF': parser.IFF, 
    'OR': parser.OR, 
    'XOR': parser.XOR, 
    'XNOR': parser.XNOR,
    'AND': parser.AND, 
    'NOT': parser.NOT, 
    'ATOM': parser.ATOM, 
    'NUMBER': parser.NUMBER, 
    'DOT': parser.DOT,
    'NEXT': parser.OP_NEXT, 
    'OP_GLOBAL': parser.OP_GLOBAL, 
    'OP_FUTURE': parser.OP_FUTURE,
    'UNTIL': parser.UNTIL,
    'EQUAL': parser.EQUAL, 
    'NOTEQUAL': parser.NOTEQUAL, 
    'LT': parser.LT, 
    'GT': parser.GT,
    'LE': parser.LE, 
    'GE': parser.GE, 
    'TRUE': parser.TRUEEXP, 
    'FALSE': parser.FALSEEXP
}

basicTypes = {
    parser.ATOM, 
    parser.NUMBER, 
    parser.TRUEEXP, 
    parser.FALSEEXP, 
    parser.DOT, 
    parser.EQUAL, 
    parser.NOTEQUAL, 
    parser.LT, 
    parser.GT, 
    parser.LE, 
    parser.GE
}

booleanOp = {
    parser.AND, 
    parser.OR, 
    parser.XOR, 
    parser.XNOR, 
    parser.IMPLIES, 
    parser.IFF
}

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
    Visit the syntactic tree of the formula `spec` to check if it is a reactive formula, that is wether the formula is of the form
                    GF f -> GF g
    where f and g are boolean combination of basic formulas.
    If `spec` is a reactive formula, the result is a pair where the first element is the formula f and the second element is the formula g. If `spec` is not a reactive formula, then the result is None.
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

def old_check_react_spec(spec):
    """
    Return whether the loaded SMV model satisfies or not the GR(1) formula
    `spec`, that is, whether all executions of the model satisfies `spec`
    or not. 
    """
    if parse_react(spec) == None:
        return None
    """ 
    --- pynusmv.mc.check_explain_ltl_spec(spec) ---
    Return whether the loaded SMV model satisfies or not the LTL given spec, that is, whether all initial states of le model satisfies spec or not. Return also an explanation for why the model does not satisfy spec, if it is the case, or None otherwise.

    The result is a tuple where the first element is a boolean telling whether spec is satisfied, and the second element is either None if the first element is True, or a path of the SMV model violating spec otherwise.

    The explanation is a tuple of alternating states and inputs, starting and ennding with a state. The path is looping if the last state is somewhere else in the sequence. States and inputs are represented by dictionaries where keys are state and inputs variable of the loaded SMV model, and values are their value.
    """
    return pynusmv.mc.check_explain_ltl_spec(spec)

def check_react_spec(spec):
    """
    return None if `spec` is not a reactivity formula, i.e when formula is not of the
    form:
    Repeatedly f -> Repeatedly g
    where `f` and `g` are Boolean combination of base formulas with no temporal operators.
    """
    if parse_react(spec) == None:
        return None
    """
    `spec` is a reactivity formula, therefore we can determine the set of reachable states `reach` by computing the least fixpoint of `bddfsm` `post` function, starting from its initial states.
    """
    # retrieve model as BddFsm
    bddfsm = pynusmv.glob.prop_database().master.bddFsm
    # retrieve basic formulas f and g with no temporal operators 
    f, g = parse_react(spec)
    # compute the negation of g
    ng = pynusmv.prop.not_(g)
    # compute the BDD that contains all the states of `bddfsm` that satisfy `f`
    bddspec_f = spec_to_bdd(bddfsm, f)
    # compute the BDD that contains all the states of `bddfsm` that satisfy `g`
    bddspec_ng = spec_to_bdd(bddfsm, ng)
    """
    compute the set of reachable states, i.e. the least fixpoint of `bddfsm` `post` function starting from its initial states
    """
    reach = bddfsm.init
    new = bddfsm.post(reach)
    while not new.equal(reach.intersection(new)):
        reach = reach.union(new.diff(reach))
        new = bddfsm.post(reach)
    """
    `spec` represents a reactivity property:
    Repeatedly f -> Repeatedly g
    It means that, if `f` is satisfied infinitely often, then `g` is also satisfied
    infinitely often. However, it must be emphasized that reactivity (and therefore repeatability
    properties are related to infinite traces. A trace is a sequence of states and input terminating
    with a state. Since we are working with finite state machines, it is necessary to have a cycle for
    the former to satisfy such a reactivity property. A cycle is a trace such that the terminating state
    is equal to (oneof) the initial state(s). Our purpose now is to check whether there exists an
    infinite trace (i.e. a cycle) that satisfies the following repeatable formula, equivalent of `spec`:
    Repeatedly (f ∧ ¬g) 
    If such a cycle exists, then `spec` is not satisfied and a counterexample must be provided. Otherwise `spec` is satisfied by every execution of the system.
    """

    """Symbolic Repeatability Algorithm: slide 13 of Symbolic Repeatability Algorithm"""
    recur = reach.intersection(bddspec_f).intersection(bddspec_ng)
    # utility variables 
    is_repeatable = False
    pre_reach = reach
    # while at least 1 state in `cycle` is reachable and the guard is false
    while recur.intersected(pre_reach) and not is_repeatable:
        # compute the pre-image of `cycle` which satisfy `¬g`
        pre_reach = new = bddfsm.pre(recur).intersection(bddspec_ng)
        # while `new` region has at least 1 state
        while bddfsm.count_states(new) > 0:
            # start building the set in which the cycle lies by adding state of pre-images computed so far 
            pre_reach = pre_reach.union(new)
            # if `cycle` is entirely contained in `sub_reach`, then we are done
            if recur.entailed(pre_reach):
                is_repeatable = True
                break
            # iteration step
            new = (bddfsm.pre(new).diff(pre_reach)).intersection(bddspec_ng)
        # iteration step
        recur = recur.intersection(pre_reach)
    
    # cycle not found, hence the reactive property is respected
    if not is_repeatable:
        return True, None

    """Finding the cycle: slide 19 of Part 7: Repeatability Checking"""
    recur_states = list(bddfsm.pick_all_states(recur))
    found_cycle = False
    s = recur_states.pop(0)
    
    frontiers = []
    while not found_cycle:
        R = None
        frontiers = []
        new = bddfsm.post(s).intersection(pre_reach)
        while bddfsm.count_states(new) > 0:
            if R is not None:
                R = new.union(R)
            else:
                R = new
            frontiers.append(R)
            new = bddfsm.post(new).intersection(pre_reach)
            new = new.diff(R)
        R = R.intersection(recur)
        if s.entailed(R):
            found_cycle = True
        else: 
            s = recur_states.pop(0)

    """Building the loop: slide 21 of Part 7: Repeatability Checking"""
    k = 0
    while not s.entailed(frontiers[k]):
        k += 1
    
    path = [s]
    trace = [s.get_str_values()]
    curr = s
    for i in range(k-1, -1, -1):
        pred = bddfsm.pre(curr).intersection(frontiers[i])
        curr = bddfsm.pick_one_state(pred)
        trace = [curr.get_str_values(), 
                    bddfsm.pick_one_inputs(bddfsm.get_inputs_between_states(curr, path[0]))
                          .get_str_values()] + trace
        path = [curr] + path
    
    trace = [s.get_str_values(), 
                bddfsm.pick_one_inputs(bddfsm.get_inputs_between_states(s, path[0]))
                      .get_str_values()] + trace

    path = [s] + path

    """
    compute complete trace from an initial state to the loop (see inv_mc.py of HW1)
    """
    images = list()
    counterex = pre_counterex = s
    images.append(counterex)
    while not pre_counterex.intersected(bddfsm.init):
        counterex = pre_counterex
        pre_counterex = bddfsm.pre(counterex)
        images.insert(0, pre_counterex)

    """
    build a trace from an initial state to a counterexample by forward
    computing post-images and intersecting them with states already discovered
    by the pre-image computation 
    """ 
    trace_init = list()
    # start from initial states
    start = bddfsm.init
    # for every stored pre-image
    for i in range(0, len(images)-1):
        # intersect it with the current post-image `start`
        start = start.intersection(images[i])
        # compute post-image from the state in `start` and intersect with `images[i+1]`
        post = bddfsm.post(start).intersection(images[i+1])
        # add the input to the trace
        trace_init.append(bddfsm.pick_one_state(start).get_str_values())
        trace_init.append(bddfsm.pick_one_inputs(bddfsm.get_inputs_between_states(start, post))
                                .get_str_values())
        # forward post-image computation iteration step
        start = post

    return False, tuple(trace_init + trace)

if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "filename.smv")
    sys.exit(1)

pynusmv.init.init_nusmv()
filename = sys.argv[1]
pynusmv.glob.load_from_file(filename)
pynusmv.glob.compute_model()
type_ltl = pynusmv.prop.propTypes['LTL']
for prop in pynusmv.glob.prop_database():
    spec = prop.expr
    print(spec)
    if prop.type != type_ltl:
        print("property is not LTLSPEC, skipping")
        continue
    res = check_react_spec(spec)
    # assert(res[0] == old_check_react_spec(spec)[0])
    if res == None:
        print('Property is not a GR(1) formula, skipping')
    if res[0] == True:
        print("Property is respected")
    elif res[0] == False:
        print("Property is not respected")
        print("Counterexample:")#, res[1])
        for t in res[1]:
            print(t)
pynusmv.init.deinit_nusmv()
