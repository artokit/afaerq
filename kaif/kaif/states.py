from aiogram.dispatcher.filters.state import StatesGroup, State


class EnterAmount(StatesGroup):
    enter = State()
