from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    waiting_birth = State()


class EnergyStates(StatesGroup):
    waiting_year = State()


class MoneyStates(StatesGroup):
    waiting_year = State()
