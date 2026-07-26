from aiogram.fsm.state import State, StatesGroup


class EnergyStates(StatesGroup):
    waiting_birth = State()
    waiting_year = State()


class MoneyStates(StatesGroup):
    waiting_birth = State()
    waiting_year = State()
