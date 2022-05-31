from dataclasses import dataclass, field
from typing import List, Optional
from chirpy.core.response_generator.state import BaseState, BaseConditionalState, NO_UPDATE

@dataclass
class State(BaseState):
    have_prompted: bool = False
    cur_song_ent: Optional = None
    cur_singer_ent: Optional = None
    cur_song_str: Optional = None
    cur_singer_str: Optional = None
    discussed_entities: List = field(default_factory=list)
    just_used_til: bool = False
    cur_supernode: Optional = None


    ask_user_about_specific_singer: bool = False
    ask_user_about_specific_song: bool = False
    continue_after_instrument: bool = False
    entering_music_rg: bool = False
    exit_music_rg: bool = False
    get_user_fav_song: bool = False
    go_to_handoff: bool = False
    instrument_til_followup: bool = False
    music_ask_singer_respond_til: bool = False
    start_discussing_music: bool = False
    user_has_song_opinion: bool = False
    trigger_music: bool = False

    # prev_supernode_str: Optional = None

@dataclass
class ConditionalState(BaseConditionalState):
    have_prompted: bool = NO_UPDATE
    cur_song_ent: Optional = NO_UPDATE
    cur_singer_ent: Optional = NO_UPDATE
    cur_song_str: Optional = NO_UPDATE
    cur_singer_str: Optional = NO_UPDATE
    just_used_til: bool = False
    prompt_treelet: Optional[str] = NO_UPDATE
    cur_supernode: Optional = None

    ask_user_about_specific_singer: bool = False
    ask_user_about_specific_song: bool = False
    continue_after_instrument: bool = False
    entering_music_rg: bool = False
    exit_music_rg: bool = False
    get_user_fav_song: bool = False
    go_to_handoff: bool = False
    instrument_til_followup: bool = False
    music_ask_singer_respond_til: bool = False
    start_discussing_music: bool = False
    user_has_song_opinion: bool = False
    trigger_music: bool = False
    
    # prev_supernode_str: Optional = NO_UPDATE
