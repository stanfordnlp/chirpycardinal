from dataclasses import dataclass
import time
import jsonpickle
from functools import wraps
import asyncio
import logging
logger = logging.getLogger('chirpylogger')

FIGSIZE = (10, 10)  # figure size for the latency plot

MIN_DURATION = 1  # milliseconds. anything with duration shorter than this is not shown

@dataclass
class Event:
    """
    A simple dataclass to store events
    """
    begin: float
    end: float
    function_name: str

# A globally accessible list of events
event_list = []

# The name of dynamodb table where event_list should be saved
dynamodb_table_name = 'latency_log'

def log_events_to_dynamodb(conversation_id:str, session_id:str, creation_date_time: str):
    """
    Logs event_list to dynamodb table. This function should be called at the end of every turn.
    :param conversation_id:
    :param session_id:
    :param creation_date_time:
    :return:
    """
    logger.info("log_events started")
    from cobot_python_sdk.dynamodb_manager import DynamoDbManager
    logger.info("log_events ended")

def clear_events():
    """
    Clear the global event_list. Should be called at the beginning of each turn
    """
    event_list.clear()

def save_latency_plot(path: str):
    """
    Save a latency plot of the current events in event_list
    :param path: the path to save the latency plot
    """

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    fig = Figure(figsize=FIGSIZE)
    plot_latency(event_list, fig)
    canvas = FigureCanvas(fig)
    fig.savefig(path, format='png')


def get_bar_color(function_name):
    """
    Return the matplotlib color that we should use in the latency plot for this function's bar.
    See here: https://matplotlib.org/3.1.0/gallery/color/named_colors.html
    """
    if any([s in function_name for s in ['execute_and_save', 'NLPPipeline']]):
        return 'indianred'  # nlp pipeline
    if any([s in function_name for s in ['entity_link', 'link_spans', 'get_span2entcounts', 'redirect_entities',
                                         'get_ent2spancounts_pageview', 'get_docids_and_cats', 'get_contextsim',
                                         'get_entity_by_wiki_name', 'link_span_to_entity', 'make_candidate_entities_parallel']]):
        return 'limegreen'  # entity linker
    elif 'init_state' in function_name:
        return 'deepskyblue'
    elif 'get_response' in function_name:
        return 'royalblue'
    elif 'get_prompt' in function_name:
        return 'aqua'
    elif any([s in function_name for s in ['DynamoDbManager', 'UserAttributesManager', 'Handler.persist', 'Handler.__init__']]):
        return 'orange'  # dynamodb stuff
    else:
        return 'darkgrey'


def plot_latency(event_list, fig):
    """
    Create a plot of latencies
    :param event_list: List of events to plot
    :param plt: matplotlib object used to create the plot
    """
    ax = fig.add_subplot(1, 1, 1)
    fig.subplots_adjust(left=0.40)

    event_list = sorted(event_list, key=lambda event: event.begin, reverse=True)
    overall_start_time = min([event.begin for event in event_list], default=0)

    bars_to_plot = []
    for event in event_list:
        bar_to_plot = {
            'label': event.function_name,
            'color': get_bar_color(event.function_name),
            'left': (event.begin - overall_start_time)/1000000,  # milliseconds,
            'duration': (event.end - event.begin)/1000000,  # milliseconds
        }
        if bar_to_plot['duration'] > MIN_DURATION:
            bars_to_plot.append(bar_to_plot)

    rects = ax.barh(range(len(bars_to_plot)),
                    [bar['duration'] for bar in bars_to_plot],
                    left=[bar['left'] for bar in bars_to_plot],
                    tick_label=[bar['label'] for bar in bars_to_plot],
                    color=[bar['color'] for bar in bars_to_plot],
                    linewidth=1, zorder=10)
    ax.grid(zorder=0)
    ax.set_xlabel("Timeline (ms)")
    ax.set_title("System latencies")


def measure(fn=None, name=None):
    """
    A decorator to wrap a function with code to measure begin and end time
    :param fn: the function to wrap
    :return: wrapped function
    """
    @wraps(fn)
    def measured_fn(*args, **kwargs):
        begin = time.perf_counter_ns()
        result = fn(*args, **kwargs)
        end = time.perf_counter_ns()

        # Special case for catching functions run using `run_module`
        if name is not None:
            function_name = name
        else:
            function_name = fn.__qualname__
            if function_name == 'run_module':
                class_object = args[0]
                class_name = type(class_object).__name__
                if class_name == 'RemoteServiceModule':
                    class_name = class_object.module_name
                function_name = f'{class_name}.{args[1]}'
            elif function_name == 'initialize_module':
                module_class = args[0]
                class_name = module_class.__name__
                function_name = "{}.__init__".format(class_name)


        event_list.append(Event(begin=begin, end=end, function_name=function_name))
        return result
    return measured_fn

def create_measured_task(coro):
    begin = time.perf_counter_ns()
    task = asyncio.create_task(coro)
    def done_callback(fut):
        end = time.perf_counter_ns()
        function_name = coro.__qualname__
        event_list.append(Event(begin=begin, end=end, function_name=function_name))

    task.add_done_callback(done_callback)
    return task

def measured_run(main, debug=False):
    begin = time.perf_counter_ns()
    retval = asyncio.run(main, debug)
    end = time.perf_counter_ns()
    function_name = main.__qualname__
    event_list.append(Event(begin=begin, end=end, function_name=function_name))
    return retval