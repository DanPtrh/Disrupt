from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    edit_captain_name = State()
    edit_city = State()
    edit_team_name = State()
