import pynusmv
import sys

def spec_to_bdd(model, spec):
    """
    Return the set of states of `model` satisfying `spec`, as a BDD.
    """
    bddspec = pynusmv.mc.eval_ctl_spec(model, spec)
    return bddspec

def old_check_explain_inv_spec(spec):
    ltlspec = pynusmv.prop.g(spec)
    # trace is a tuple
    res, trace = pynusmv.mc.check_explain_ltl_spec(ltlspec)
    return res, trace

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
    # retrieve model as BddFsm
    bddfsm = pynusmv.glob.prop_database().master.bddFsm
    # compute complementary of `spec`
    nspec = pynusmv.prop.not_(spec)
    # compute the set of states of `bddfsm` satisfying `nspec`, as a BDD
    bddspec = spec_to_bdd(bddfsm, nspec)
    
    # compute the set of reachable states, which is the least fixpoint of 
    # bddfsm's `post` function, starting from its initial states
    reach = bddfsm.init
    new = bddfsm.post(reach)
    while not new.equal(reach.intersection(new)):
        reach = reach.union(new.diff(reach))
        new = bddfsm.post(reach)

    # checks if the conjunction between `bddspec` and `reach` is not empty, 
    # namely, if the intersection of reachable states and states satisfying
    # nspec is not empty
    if reach.intersected(bddspec) is False:
        # bddspec * reach is empty => there does not exist a reachable state
        #                             in which `nspec` is true 
        #                          => `spec` always holds 
        #                          => `spec` is an invariant, return `True`
        return True, None

    # bddspec ∩ reach is not empty => there exists a reachable state in
    #                                 which `nspec` is true        
    #                              => `spec` is not an invariant
    
    # retrieve the set of reachable states in which `nspec` is true
    counterex = bddspec.intersection(reach)
    """
    Compute images backwards by starting from a random counterexample and
    store them in `images` list
    """
    # create new empty list
    images = list()
    # pick a counterexample pseudo-randomly
    cex = rnd_couterex = pre_rnd_counterex = bddfsm.pick_one_state_random(counterex)
    # push it into the image list 
    images.append(rnd_couterex)
    # pre-images are computed and stored until an initial state is encountered
    # fixpoint approach
    while not pre_rnd_counterex.intersected(bddfsm.init):
        rnd_couterex = pre_rnd_counterex
        pre_rnd_counterex = bddfsm.pre(rnd_couterex)
        images.insert(0,pre_rnd_counterex)

    """
    build a trace from an initial state to a counterexample by forward
    computing post-images and intersecting them with states already discovered
    by the pre-image computation 
    """ 
    # create new empty trace
    trace = list()
    # start from initial states
    start = bddfsm.init
    # for every stored pre-image
    for i in range(0, len(images)-1):
        # intersect it with the current post-image `start`
        start = start.intersection(images[i])
        # add that state to the trace
        trace.append(bddfsm.pick_one_state(start).get_str_values())
        # compute post-image from the state in `start` and intersect with `images[i+1]`
        post = bddfsm.post(start).intersection(images[i+1])
        # compute input between start and images[i+1]
        inputs = bddfsm.get_inputs_between_states(start, post)
        # add the input to the trace
        trace.append(bddfsm.pick_one_inputs(inputs).get_str_values())
        # forward post-image computation iteration step
        start = post
    # append the randomly chosen counterexample to the trace
    trace.append(cex.get_str_values())
    
    """ 
    Format the trace to tuple and then return the results
    """
    trace = tuple(trace)
    return False, trace

if len(sys.argv) != 2:
    print("Usage:", sys.argv[0], "filename.smv")
    sys.exit(1)

pynusmv.init.init_nusmv()
filename = sys.argv[1]
pynusmv.glob.load_from_file(filename)
pynusmv.glob.compute_model()
invtype = pynusmv.prop.propTypes['Invariant']
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
        
        """
        old check_explain_inv_spec method: uncomment for results comparison
        """
        # input()
        # res, trace = old_check_explain_inv_spec(spec)
        # if res == True:
        #     print("Invariant is respected")
        # else:
        #     print("Invariant is not respected")
        #     print(trace)
        # input()

    else:
        print("Property", spec, "is not an INVARSPEC, skipped.")

pynusmv.init.deinit_nusmv()