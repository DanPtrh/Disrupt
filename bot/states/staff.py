from aiogram.fsm.state import StatesGroup, State

class StaffSolutionsStates(StatesGroup):
    wait_city = State()
    wait_username = State()
    wait_user = State()