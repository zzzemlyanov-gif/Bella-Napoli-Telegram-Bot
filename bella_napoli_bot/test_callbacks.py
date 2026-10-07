"""Callback button coverage and feedback tests."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from telegram.ext import CallbackQueryHandler, ConversationHandler

from bella_napoli_bot.db import RestaurantDB
from bella_napoli_bot.keyboards import (
    cancel_keyboard,
    categories_keyboard,
    category_keyboard,
    cart_keyboard,
    home_keyboard,
    order_confirmation_keyboard,
    reservation_guests_keyboard,
)
from bella_napoli_bot.main import build_application, handle_navigation
from bella_napoli_bot.menu import ITEMS_BY_ID, MENU


def _button_callback_data(markup) -> set[str]:
    return {
        button.callback_data
        for row in markup.inline_keyboard
        for button in row
        if button.callback_data is not None
    }


def _registered_callback_handlers(application) -> list[CallbackQueryHandler]:
    handlers = []
    for group in application.handlers.values():
        for handler in group:
            if isinstance(handler, CallbackQueryHandler):
                handlers.append(handler)
            if isinstance(handler, ConversationHandler):
                handlers.extend(
                    child
                    for child in [*handler.entry_points, *handler.fallbacks]
                    if isinstance(child, CallbackQueryHandler)
                )
                for state_handlers in handler.states.values():
                    handlers.extend(
                        child
                        for child in state_handlers
                        if isinstance(child, CallbackQueryHandler)
                    )
    return handlers


class CallbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.application = build_application("123:ABC")

    def test_every_keyboard_callback_matches_a_registered_handler(self) -> None:
        first_item = next(iter(ITEMS_BY_ID.values()))
        markups = [
            home_keyboard(),
            categories_keyboard(),
            *(category_keyboard(category_id) for category_id in MENU),
            cart_keyboard([{**first_item, "quantity": 1}]),
            cart_keyboard([]),
            order_confirmation_keyboard(),
            reservation_guests_keyboard(),
            cancel_keyboard(),
        ]
        callback_data = set().union(*(_button_callback_data(markup) for markup in markups))
        registered = _registered_callback_handlers(self.application)

        unmatched = {
            data
            for data in callback_data
            if not any(handler.pattern and handler.pattern.match(data) for handler in registered)
        }
        self.assertEqual(unmatched, set(), f"Callbacks without handlers: {unmatched}")

    async def test_add_to_cart_shows_the_requested_callback_notice(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            database = RestaurantDB(Path(temp_dir) / "callback-test.sqlite3")
            query = SimpleNamespace(
                data="add:margherita",
                answer=AsyncMock(),
            )
            update = SimpleNamespace(
                callback_query=query,
                effective_user=SimpleNamespace(id=777),
            )
            context = SimpleNamespace(user_data={})

            with patch("bella_napoli_bot.main._db", return_value=database):
                await handle_navigation(update, context)

            query.answer.assert_awaited_once_with("✅ Добавлено в корзину")
            self.assertEqual(database.get_cart(777)[0]["id"], "margherita")


if __name__ == "__main__":
    unittest.main()
