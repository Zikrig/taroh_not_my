from aiogram import Router

from handlers import about, admin, balance, day_card, energy, money, start, yes_no


def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(day_card.router)
    root.include_router(yes_no.router)
    root.include_router(energy.router)
    root.include_router(money.router)
    root.include_router(balance.router)
    root.include_router(about.router)
    root.include_router(admin.router)
    return root
