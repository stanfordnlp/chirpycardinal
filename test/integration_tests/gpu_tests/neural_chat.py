from test.integration_tests.integration_base import BaseIntegrationTest
from chirpy.core.test_args import TestArgs
from parameterized import parameterized
from chirpy.core.response_priority import PromptType, ResponsePriority
from chirpy.response_generators.neural_chat.state import BotLabel
from chirpy.response_generators.neural_chat.treelets.food_treelet import HAVENT_EATEN_RESPONSE

class TestNeuralChatRG(BaseIntegrationTest):
    launch_sequence = ['let\'s chat', 'my name is jamie']

    def get_test_args(self, treelet_name=None):
        return TestArgs(selected_prompt_rg='NEURAL_CHAT', neural_chat_args={'treelet': treelet_name})

    def get_neuralchat_state(self, current_state):
        """Returns the RG state for the NEURAL_CHAT RG"""
        self.assertIn('NEURAL_CHAT', current_state['response_generator_states'], "NEURAL_CHAT's state is not in the overall state")
        return current_state['response_generator_states']['NEURAL_CHAT']

    def get_neuralchat_response(self, current_state):
        self.assertIn('NEURAL_CHAT', current_state['response_results'], "NEURAL_CHAT does not have a response result in the overall state")
        return current_state['response_results']['NEURAL_CHAT']

    def get_neuralchat_prompt(self, current_state):
        self.assertIn('NEURAL_CHAT', current_state['prompt_results'], "NEURAL_CHAT does not have a prompt result in the overall state")
        return current_state['prompt_results']['NEURAL_CHAT']

    def induce_neuralchat_prompt(self, treelet_name=None, expected_priority=None):
        """Induce a needs_prompt and make sure that neural chat gave a non-NO prompt that was chosen, from the specified treelet"""
        _, current_state, response_text = self.process_utterance("you said that already", test_args=self.get_test_args(treelet_name))  # induce a needs_prompt=True
        neuralchat_promptresult = self.get_neuralchat_prompt(current_state)
        self.assertNotEqual(neuralchat_promptresult.type, PromptType.NO, "NEURAL_CHAT gave a prompt of type NO")
        if expected_priority:
            self.assertEqual(neuralchat_promptresult.type, expected_priority, f"NEURAL_CHAT gave a prompt of priority {neuralchat_promptresult.type.name} not expected_priority={expected_priority.name}")
        if treelet_name:
            self.assertEqual(neuralchat_promptresult.conditional_state.most_recent_treelet, treelet_name, f"NEURAL_CHAT gave a prompt, but it was from {neuralchat_promptresult.conditional_state.most_recent_treelet}, not the expected {treelet_name}")
        self.assertEqual(current_state['selected_prompt_rg'], 'NEURAL_CHAT', "NEURAL_CHAT gave a prompt, but it wasn't chosen")  # check that neuralchat's prompt was chosen
        return current_state, response_text

    def run_neuralchat_conv(self, treelet_name, user_utterance, min_turns, max_turns=10):
        """
        After neuralchat has already given the starter question, check that we talk for at least min_turns, asking questions
        with needs_prompt=True, then saying a non-question response with needs_prompt=False (before 10 turns)

        min_turns is how many responses we expect neural_chat to give (including any handoff response, but not including
        the starter question).
        """
        received_gpt_response = False  # track whether we've received at least one gpt response

        for turn_num in range(max_turns):
            _, current_state, response_text = self.process_utterance(user_utterance)  # keep saying user_utterance until the neuralchat conversation ends
            neuralchat_response = self.get_neuralchat_response(current_state)
            self.assertEqual(current_state['selected_response_rg'], 'NEURAL_CHAT')  # check that neuralchat's response was chosen
            self.assertEqual(neuralchat_response.priority, ResponsePriority.STRONG_CONTINUE)  # and that it's strong_continue

            neuralchat_state = self.get_neuralchat_state(current_state)
            conv_history = neuralchat_state.conv_histories[treelet_name]  # ConvHistory
            if BotLabel.GPT2ED in conv_history.used_bot_labels:
                received_gpt_response = True

            if not neuralchat_response.needs_prompt:
                self.assertLess(turn_num, max_turns - 1, f'NEURAL_CHAT talked for {max_turns} turns without ending')
            else:
                self.assertGreaterEqual(turn_num, min_turns-1, f"NEURAL_CHAT stopped talking after only {turn_num+1} responses")
                break
        self.assertTrue(received_gpt_response, f"NEURAL_CHAT didn't give any GPT2ED responses")


    def check_negnav(self):
        """
        After neuralchat has already given the starter question, give a negnav user utterance. Check that neuralchat
        quits with strong_continue and needs_prompt=True
        """
        _, current_state, response_text = self.process_utterance("change the subject")
        neuralchat_response = self.get_neuralchat_response(current_state)
        self.assertEqual(current_state['selected_response_rg'], 'NEURAL_CHAT')  # check that neuralchat's response was chosen
        self.assertEqual(neuralchat_response.priority, ResponsePriority.STRONG_CONTINUE)  # and that it's strong_continue
        self.assertTrue(neuralchat_response.needs_prompt)  # with needs_prompt=True

    @parameterized.expand([
        ('CurrentAndRecentActivitiesTreelet', "i went grocery shopping today"),
        ('FoodTreelet', "i love to cook thai curry"),
    ])
    def test_neuralchat_launchtreelets(self, treelet_name, user_utterance):
        """
        Check the launch sequence neural chat conversation.
        """
        # Check that the launch treelet starts
        _, current_state, response_text = self.init_and_first_turn()
        _, current_state, response_text = self.process_utterance("my name is jamie", test_args=self.get_test_args(treelet_name))
        neuralchat_promptresult = self.get_neuralchat_prompt(current_state)
        self.assertEqual(neuralchat_promptresult.type, PromptType.FORCE_START, "NEURAL_CHAT didn't give a FORCE_START prompt in the launch sequence")
        self.assertEqual(neuralchat_promptresult.conditional_state.most_recent_treelet, treelet_name, f"NEURAL_CHAT gave a prompt, but it was from {neuralchat_promptresult.conditional_state.most_recent_treelet}, not the expected {treelet_name}")
        self.assertEqual(current_state['selected_prompt_rg'], 'NEURAL_CHAT', "NEURAL_CHAT gave a prompt, but it wasn't chosen")  # check that neuralchat's prompt was chosen

        # Run the conversation
        self.run_neuralchat_conv(treelet_name, user_utterance, min_turns=1)  # check the emotion conversation

    def test_neuralchat_foodtreelet_haventeaten(self):
        treelet_name = 'FoodTreelet'

        # Check that the launch treelet starts
        _, current_state, response_text = self.init_and_first_turn()
        _, current_state, response_text = self.process_utterance("my name is jamie", test_args=self.get_test_args(treelet_name))
        neuralchat_promptresult = self.get_neuralchat_prompt(current_state)
        self.assertEqual(neuralchat_promptresult.type, PromptType.FORCE_START, "NEURAL_CHAT didn't give a FORCE_START prompt in the launch sequence")
        self.assertEqual(neuralchat_promptresult.conditional_state.most_recent_treelet, treelet_name, f"NEURAL_CHAT gave a prompt, but it was from {neuralchat_promptresult.conditional_state.most_recent_treelet}, not the expected {treelet_name}")
        self.assertEqual(current_state['selected_prompt_rg'], 'NEURAL_CHAT', "NEURAL_CHAT gave a prompt, but it wasn't chosen")  # check that neuralchat's prompt was chosen

        # Run the conversation
        _, current_state, response_text = self.process_utterance("i haven't had anything yet")
        neuralchat_response = self.get_neuralchat_response(current_state)
        self.assertEqual(current_state['selected_response_rg'], 'NEURAL_CHAT')  # check that neuralchat's response was chosen
        self.assertEqual(neuralchat_response.priority, ResponsePriority.STRONG_CONTINUE)  # and that it's strong_continue
        self.assertIn(HAVENT_EATEN_RESPONSE, response_text)


    @parameterized.expand([('good', 2), ('bad', 2), ('okay', 2), ('pretty good i got some work done', 1),
                           ("honestly really bad i'm feeling depressed", 1), ("okay i'm a bit tired though", 1)])
    def test_neuralchat_emotiontreelet(self, emotion_response, min_turns):
        """
        Check that neural_chat gives the emotion treelet prompt starter question, then talks for at least min_turns, asking
        questions with needs_prompt=True, then saying a non-question response with needs_prompt=False (before 10 turns)
        """
        for user_name_response in ['my name is jamie', 'no']:
            _, current_state, response_text = self.init_and_first_turn()
            _, current_state, response_text = self.process_utterance(user_name_response)  # give name or not
            _, _ = self.induce_neuralchat_prompt('EmotionsTreelet', expected_priority=PromptType.GENERIC)  # make sure neuralchat gave a force_start prompt that was chosen
            self.run_neuralchat_conv('EmotionsTreelet', emotion_response, min_turns=min_turns)  # check the emotion conversation

    def test_emotiontreelet_negnav(self):
        """Check that we exit the emotiontreelet conversation with needs_prompt=True when the user gives a negative navigational intent"""
        _, _ = self.induce_neuralchat_prompt('EmotionsTreelet', expected_priority=PromptType.GENERIC)  # make sure neuralchat gave a force_start prompt that was chosen
        self.check_negnav()  # check negnav works

    @parameterized.expand([
        ('CurrentAndRecentActivitiesTreelet', "i went grocery shopping today"),
        ('FoodTreelet', "i love to cook thai curry"),
        ('FutureActivitiesTreelet', "i'm looking forward to going out to restaurants"),
        ('GeneralActivitiesTreelet', "i've been painting a lot"),
        ('LivingSituationTreelet', "i'm living with my family right now it's tough but we support each other"),
    ])
    def test_neuralchat_othertreelets(self, treelet_name, user_utterance):
        """
        Check that neural_chat gives a generic prompt starter question, then talks for at least 2 turns, asking
        questions with needs_prompt=True, then saying a non-question response with needs_prompt=False (before 10 turns)
        """
        _, current_state, response_text = self.init_and_first_turn()  # bot asks "what's your name"?

        # Trigger a new neural chat conversation (before allowing the launch neuralchat sequence to be triggered)
        _, _ = self.induce_neuralchat_prompt(treelet_name, expected_priority=PromptType.GENERIC)

        # Check the conversation
        self.run_neuralchat_conv(treelet_name, user_utterance, min_turns=1)

    @parameterized.expand([
        'CurrentAndRecentActivitiesTreelet',
        'FoodTreelet',
        'FutureActivitiesTreelet',
        'GeneralActivitiesTreelet',
        'LivingSituationTreelet',
    ])
    def test_othertreelets_negnav(self, treelet_name):
        """Check that we exit the neural chat conversation with needs_prompt=True when the user gives a negative navigational intent"""

        _, current_state, response_text = self.init_and_first_turn()  # bot asks "what's your name"?

        # Trigger a new neural chat conversation (before allowing the launch neuralchat sequence to be triggered)
        _, _ = self.induce_neuralchat_prompt(treelet_name, expected_priority=PromptType.GENERIC)

        # Check negnav works
        self.check_negnav()

    def test_neuralchat_familytreelet_contextual_prompt_later(self):
        """
        Mention "my grandma" during an earlier conversation, then check that neural_chat later gives a CONTEXTUAL
        prompt to talk about the user's grandma.
        """
        # Mention grandma during intro sequence
        _, current_state, response_text = self.process_utterance('good thanks i\'m hanging out with my grandma')

        # Init family treelet conversation
        current_state, response_text = self.induce_neuralchat_prompt(None, expected_priority=PromptType.CONTEXTUAL)  # make sure neuralchat gave a contextual prompt that was chosen
        self.assertIn('your grandma', response_text)

        # Check the conversation
        self.run_neuralchat_conv('OlderFamilyMembersTreelet', "we like to bake together", min_turns=1)

    def test_neuralchat_familytreelet_contextual_prompt_immediate(self):
        """
        Mention "my friend" on a turn when there's needs_prompt, then check that neural_chat gives a prompt
        to talk about the user's friend, with CONTEXTUAL priority.
        """
        # Induce needs_prompt while also mentioning "my friend"
        _, current_state, response_text = self.process_utterance("my friend and i want to know if you're better than siri", test_args=self.get_test_args())  # induce a needs_prompt=True
        self.assertEqual(self.get_neuralchat_prompt(current_state).type, PromptType.CONTEXTUAL)
        self.assertEqual(current_state['selected_prompt_rg'], 'NEURAL_CHAT')  # check that neuralchat's prompt was chosen
        self.assertIn('your friend', response_text)

        # Check the conversation
        self.run_neuralchat_conv('FriendsTreelet', "we like to bake together", min_turns=1)

    def test_neuralchat_familytreelet_curtopic_prompt_immediate(self):
        """
        Say PosNav about "my brother" on a turn when there's needs_prompt, then check that neural_chat gives a prompt
        to talk about the user's brother, with CURRENT_TOPIC priority.
        """
        # Induce needs_prompt while also saying PosNav for "my brother"
        _, current_state, response_text = self.process_utterance("siri let's talk about my brother", test_args=self.get_test_args())  # induce a needs_prompt=True
        self.assertEqual(self.get_neuralchat_prompt(current_state).type, PromptType.CURRENT_TOPIC)
        self.assertEqual(current_state['selected_prompt_rg'], 'NEURAL_CHAT')  # check that neuralchat's prompt was chosen
        self.assertIn('your brother', response_text)

        # Check the conversation
        self.run_neuralchat_conv('SiblingsCousinsTreelet', "we like to bake together", min_turns=1)

    def test_neuralchat_familytreelet_forcestart_response(self):
        """
        Say PosNav about "my dog" with PosNav, then check that neural_chat gives a FORCE_START response to talk about the user's dog.
        """
        _, current_state, response_text = self.process_utterance("change the subject")  # end launch neuralchat
        _, current_state, response_text = self.process_utterance("let's talk about my dog")
        self.assertEqual(self.get_neuralchat_response(current_state).priority, ResponsePriority.FORCE_START)
        self.assertEqual(current_state['selected_response_rg'], 'NEURAL_CHAT')  # check that neuralchat's response was chosen
        self.assertIn('your dog', response_text)

        # Check the conversation
        self.run_neuralchat_conv('PetsTreelet', "we love to walk in the park", min_turns=1)

    def test_neuralchat_familytreelet_canstart_response(self):
        """
        Mention "my dog" without PosNav, then check that neural_chat gives a CAN_START response to talk about the user's dog.
        """
        _, current_state, response_text = self.process_utterance("let's talk about movies")  # end launch neuralchat by triggering something else
        _, current_state, response_text = self.process_utterance("i love my dog")
        neuralchat_response = self.get_neuralchat_response(current_state)
        self.assertEqual(neuralchat_response.priority, ResponsePriority.CAN_START)
        self.assertIn('your dog', neuralchat_response.text)