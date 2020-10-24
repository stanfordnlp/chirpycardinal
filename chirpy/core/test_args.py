from typing import Optional

class TestArgs:
    """
    These arguments are provided to the lambda handler and help in overriding certain probabilitistic parts
    """
    def __init__(self, selected_prompt_rg: Optional[str] = None, experiment_values: dict = {},
                 neural_chat_args: dict = {}):
        """

        @param selected_prompt_rg: if supplied, the name of the RG whose prompt should be deterministically chosen
            (if a prompt from this RG is available)
        @param experiment_values:
        """
        assert selected_prompt_rg is None or isinstance(selected_prompt_rg, str)
        assert isinstance(experiment_values, dict)
        self.selected_prompt_rg = selected_prompt_rg
        self.experiment_values = experiment_values
        self.neural_chat_args = neural_chat_args