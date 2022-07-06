# Intra-RG Standardization

Previously, each response generator defined a conversational graph based on Treelets/nodes, which were allowed to implement arbitrary python code with no separation between NLU, NLG, and writing to state. Furthermore, the navigational structure within RGs were frequently obfuscated by ad-hoc navigational hacks that differed significantly from RG to RG, making it difficult to follow & debug conversation. 

We develop a system to build new RGs that divorces the tight dependence of conversational nodes on each other by handling logic for NLU, NLG, and updating state differently. Furthermore, we migrate much of the logic over to a highly symbolic framework (using YAML) that is easier to understand, with options to fall back on Python code where the need arises. Finally, we build a strong static type checker that:
- ensures the appropriate formating of required YAML files is followed (with comprehensive syntactically and semantic checks)
- statically builds the RG conversation graph (ensuring the graph is a DAG), and reports back the number of possible paths through the RG - this will be extremely helpful for evaluating the diversity of conversation and avoid recurring navigational bugs that plagued the old format
- gives clear error logging

Our goal is to accelerate the development process for creating new RGs, improve & standardize the navigational logic, and provide a more diverse conversational flow for the user.

## God Treelet
**Final structure not fully fleshed out yet. Wait before giving full spec**
Response generators and/or the god treelet must define in Python the entry conditions for the overall RG, as the intra-RG scaffolding we will subsequently describe does not support inter-RG navigation. Do this using the existing infrastructure, i.e by defining a `get_treelet_for_entity` method or `get_trigger_response` method.

## The Supernode vs. Subnode abstraction

Rather than allowing treelets to define arbitrary response logic, we ask developers to define `supernodes` that encapsulate a high-level response category, and `subnodes` within a supernode that define the specific responses within the supernode that can be generated. This standardization of logic should make RGs much more readable and uniform. As an example, consider the following conversational graph of the `FOOD` RG:

![image](https://drive.google.com/uc?export=view&id=1yug86YRW6hRzbNnzDyWaDHblDD5EhvR4)

We can see that each node in the graph is a supernode that defines a specific part of a possible conversation on food: commenting on the user's favorite type of food, commenting on an open ended response, giving an interesting factoid about a food type, and so on. A subnode, on the other hand, defines a particular case within a supernode that would lead to a particular response and state update. For example, within the FOOD INTRODUCTORY supernode, we might have the some of the following subnodes:
- `is_ingredient`, which returns the appropriate response for when a user brings up a food that is a common ingredient to other dishes
- `best_attribute_texture`, which is triggered when we detect the user brings up a food that has a very unique and distinctive texture, and we return a comment on that texture
- `food_type_comment`, which returns the appropriate response for when the user brings up a type of food, rather than a specific dish. Additionally, this subnode might lead to the Comment on Fav Food Type supernode, whereas other subnodes might lead elsewhere
- so on...

# Structure for the Intra-RG setup
An RG implementing this setup should have the following folder structure (using FOOD as an example):
```
food
│   food_response_generator.py 
│   * other helper files for FOOD *
│   god_treelet.py (CHANGE ONCE GOD TREELET PUSHED TO SUPERCLASS/RG)
└───supernodes
│   │   __init__.py
│   └───food_introductory
│       │   __init__.py
│       │   supernode.yaml
│       │   nlu.py
│       │   nlg.yaml
│       │   nlg_helpers.py
│   └───ask_favorite_food
│       |   ...
│   └───comment_on_favorite_type
│       |   ...
... other supernode folders here ....
│   └───exit
│       │   __init__.py
│       │   supernode.yaml
│       │   nlu.py
```
As the above should indicate, each supernode has its own folder inside the `supernodes/` folder, where the supernode folder name should exactly match the actual name of the supernode. There must exist a supernode named `exit` that defines the conditions when conversation should exit the current RG. Supernodes (except for `exit`, which need only contain a `supernode.yaml` file) must contain the following files, as indicated by the figure above:
- [supernode.yaml](#Supernode-YAML-file)
- [nlu.py](#NLU-python-file)
- [nlg.yaml](#NLG-YAML-file)
- [nlg_helpers.py](#NLG-helpers-python-file)

We now provide detailed requirements for each of the above files. If these requirements seem a bit overwhelming, do not fear! A convenient script that performs comprehensive static checks to ensure the correct syntactic and semantic guidelines are followed is outlined [here](#Static-Checker). **Make sure to run the static checker frequently (especially before actually testing out the RG) and ensure all checks are passed.**

## Supernode YAML file

The `supernode.yaml` file must define the following entries in YAML format. 

##### Supernode Name
We need to define the name of the supernode in the yaml file. This name *must* match the name of the enclosing folder.
```yaml
name: food_introductory
```

##### Supernode Entry Requirements
We also need to specify the entry requirements for this supernode; in other words, what state must the current conversation have to enter this supernode? This should be specified as a list of valid entry conditions, which **must be static boolean flags**; for example:
```yaml
requirements:
  - entry_entity_is_food: False
    cur_entity_known_food: True
    exit_food: False
  - acknowledge_fav_food: True
    exit_food: False
```
The above defines two sets of entry conditions to the food introductory supernode: informally speaking, 1) either the current entity is a known food, or 2) we have just acknowledged the user's favorite food. If any entry condition of a supernode is satisfied at a particular turn of the conversation, it will be considered as a candidate for the next supernode. Multiple matching supernodes will be **chosen at random as the next supernode of the conversation**.

##### Prompt Leading Response

Suppose the conversation is currently in supernode A. As conversational logic is processed, it is determined that following the current turn, the conversation will proceed to supernode B. Chirpy will then return the response `{Supernode A's response} {Prompt leading to supernode B}`. This ensures smooth transitions between supernodes. However, Chirpy needs to know the appropriate prompt to supernode B, even though control is still with supernode A. Hence, supernode B will need to define something that looks like the following:
```yaml
prompt:
  - required:
      just_was_in_A: True
    prompt: 'Are you ready to talk about supernode B?!?'
  - required:
        just_was_in_A: False
    prompt: ''
```
The above is somewhat contrived, but specifies that B will give the prompt `Are you ready to talk about supernode B?!?` that will be tacked on to A's response, before control fully passes to B. The following are also possible if no prompt is ever required, or we should unconditionally return a prompt, or we want to fall back on python to return the appropriate prompt:
```yaml
prompt: None
#########
prompt:
  - required: None
    prompt: 'Are you ready to talk about food?'
#########
prompt:
  call_method: get_prompt_for_fav_food_type # method must be decorated - see NLG section
```

##### Subnode State Updates

We need to define the state updates that will occur depending on which subnode is activated. For example:
```yaml
subnode_state_updates:
  no_entity: # subnode name
    exit_food: True # State updates to be made following response
    needs_prompt: True
  food_type_comment:
    food_type_exists: True
  is_ingredient:
    open_ended: True
  best_attribute_texture:
    open_ended: True
  catch_all: None
```
The above YAML conveys the following logic: exit the food RG if no entity is detected, turn on the `food_type_exists` flag once we have given the response in `food_type_comment` subnode, etc. If we're in the `catch_all` subnode, don't perform any state updates. Note these state updates are crucial for navigational flow, as they will determine the next supernode the conversation will shift to (remember [this](#Supernode-Entry-Requirements)?).

##### Global Post-Supernode State Updates
In the previous section, we saw examples were there are subnode-specific state updates that need to be done. In many cases, however, there are state updates that must be done unconditionally by all subnodes in a particular supernode. For example, a particular supernode might define the following if it will always lead to the open ended supernode (among other conditions):
```yaml
global_post_supernode_state_updates:
  cur_food: cur_food_entity
  open_ended: True
  food_type_exists: False
```
And again, these updates will be performed no matter what subnode is active. **Observe that state updates can be dynamic expressions, i.e not always boolean flags.**

##### Required Exposed Variables

**This might change and not be required if we change state updates to always use the base structures `rg` and `state`. But might be required if subnodes define exposed vars differently. Hold off on a full spec for now.**

## NLU python file

Keeping with the theme of this whole design, we want to separate different components of conversational logic from each other, and we define a special `nlu.py` file meant to exclusively handle NLU for a supernode; specifically, this is where a supernode figures out which subnode to activate. NLU is typically too complicated to perform symbolically, which is why we leave this part in full Python. This file must define a method with the following signature: `def nlu_processing(rg, state, utterance, response_types)`. This method must process the user utterance, state, etc. return a dictionary of boolean flags will be used to determine the appropriate subnode. For example:
```python
def nlu_processing(rg, state, utterance, response_types):
        flags = {'has_custom_food': False, 'dont_know': False, 'response_no': False}
        cur_food_entity = state.cur_food
        cur_food = cur_food_entity.name
        if get_custom_question(cur_food) is not None:
                flags['has_custom_food'] = True
        if ResponseType.DONT_KNOW in response_types:
                flags['dont_know'] = True
        elif ResponseType.NO in response_types:
                flags['response_no'] = True
        return flags
```
The logic here is similar to how NLU was done previously to intra-rg standardization, so refer to the appropriate documentation if you need a refresher for what the state, utterance, and response_type variables represent.

## NLG YAML file

Based on the flags set in the previous section, we need to define the subnodes that actually perform the response generation. Again, we want to separate NLG from NLU, which is the reason we structure it this way. `nlg.yaml` will be a list of subnodes that define all possible response generations of this supernode, and each subnode possesses the following fields:
- `node_name` - the name of the subnode
- `entry_conditions` - a dictionary specifying the required flags (set by `nlu.py`) needed to enter this subnode
- `response` - the actual response given by this subnode. Should be formatted like a python f-string. **The f-string will have access to the variables `rg`, `state`, and all properly decorated methods of the supernode (see the next section). The f-string will not be allowed to execute arbitrary python code.**
- `expose_vars` - dynamically define variables to be exposed to supernode.yaml for post-node state updates. Also has access to `rg`, `state`, and decorated methods, but no more.

This is best illustrated by an example:
```yaml
- node_name: custom_dont_know
  entry_conditions: # set in nlu.py
    has_custom_food: True
    dont_know: True
  response: "No worries, it can be difficult to pick just one! Personally, when it comes to {get_cur_talkable_food(rg)}, I really like {get_custom_q_answer(rg)}."
  expose_vars:
    entity: rg.get_current_entity(initiated_this_turn=False)
    cur_food_entity: state.cur_food
  ```
Picture this repeated many times for each subnode in a particular supernode.

## NLG helpers python file

Notice that many of the previous sections have a mix of statically-defined (i.e hardcoded boolean flags) and dynamically-defined (i.e the f-strings in the previous section) expressions. The dynamically-defined expressions represent logic that requires Python execution, but in a highly controlled fashion. Specifically, `nlg.yaml` is a symbolic file with calls to Python functions that are required for sophisticated response generation (i.e neural prefix, regex matching, ES calls for current events info, etc.). 

To keep generation flexible but controlled, we allow all dynamic-expressions (including f-strings) access to the `rg` and `state` variables, and their associated fields, along with a specific set of helper methods. These helper methods must be defined in the `nlg_helpers.py` file and **decorated** appropriately. For example, to generate the response given in the `custom_dont_know` subnode example in the section above, we must have the following in `nlg_helpers.py`:

  
```python
from chirpy.response_generators.food.food_helpers import get_custom_question_answer
from chirpy.core.response_generator import nlg_helper

@nlg_helper
def get_custom_q_answer(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    custom_question_answer = get_custom_question_answer(state.cur_food.name)
    return custom_question_answer
    
@nlg_helper
def get_cur_talkable_food(rg):
    state, utterance, response_types = rg.get_state_utterance_response_types()
    return state.cur_food.talkable_name
```
Notice how we have added the decorator `@nlg_helper` to each method, allowing the f-string response in the `custom_dont_know` subnode to resolve correctly. `@nlg_helper` adds all decorated methods to a supernode function cache that can be used for any allowed dynamic expression defined in the YAML files of the supernode. Undecorated methods cannot be used in dynamic expressions, and will cause runtime errors.

# Static Checker

We've described a lot of rules and regulations to use the intra-RG scaffolding properly! To make it easier to follow the rules, we've built a kind of compile/static-time checker that makes a **best-effort** attempt to enforce the rules. Some of the things the checker verifies (not a comprehensive list):
- The correct folder structure
- The correct syntax for all yaml files
- requirements in `supernode.yaml` defines only static boolean expressions
- `nlu.py` declares a `nlu_processing` method with the correct signature
- There is a reasonable path through the conversational graph, and there are no cycles (you should always be able to define additional supernodes to remove cycles). It also lists & counts possible conversational paths, and visualizes the graph. **Make sure that this graph looks good - if you start running the RG and the conversation gets stuck in a cycle or makes an illegal transition, you should've caught it here**.
- Provides a list of variables that must be declared in the RG's `state.py` file

It is important to note that the static checker is **not perfect**. There are many errors that are either **impossible or highly inconvenient to check statically** (ex. improperly formatted f-string or undecorated method), and we attempt to include clear error logging in the supporting Python code that will hopefully make it easier to resolve such runtime errors. However, runtime errors without a helpful message may also be thrown; make sure all checks in the static checker pass and the convo graph looks reasonable before digging deeper.

Run the checker as follows (note name_of_supernode_to_treat_as_entrypoint could be multiple different supernodes depending on how an RG can get triggered, so run multiple times with each option if you want to generate convo paths for each - convo paths are enumerated from the specified intro node to exit):
```sh
python3 super_convo_graph_process.py --intro_node name_of_supernode_to_treat_as_entrypoint [--draw_graph]
```



