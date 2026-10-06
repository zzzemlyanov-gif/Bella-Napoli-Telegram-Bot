"""Inline keyboards used by the bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .menu import MENU, ITEMS_BY_ID, money


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🍽 Browse menu", callback_data="menu")],
            [
                InlineKeyboardButton("🛒 My cart", callback_data="cart"),
                InlineKeyboardButton("🚚 Delivery", callback_data="flow:delivery"),
            ],
            [InlineKeyboardButton("🪑 Reserve a table", callback_data="flow:reserve")],
        ]
    )


def categories_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(category["title"], callback_data=f"cat:{category_id}")]
        for category_id, category in MENU.items()
    ]
    rows.append([InlineKeyboardButton("↩ Main menu", callback_data="home")])
    return InlineKeyboardMarkup(rows)


def category_keyboard(category_id: str) -> InlineKeyboardMarkup:
    category = MENU[category_id]
    rows = [
        [
            InlineKeyboardButton(
                f"➕ {item['name']} · {money(item['price'])}",
                callback_data=f"add:{item['id']}",
            )
        ]
        for item in category["items"]
    ]
    rows.extend(
        [
            [InlineKeyboardButton("↩ All categories", callback_data="menu")],
            [InlineKeyboardButton("🏠 Main menu", callback_data="home")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def cart_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for item in items:
        item_id = item["id"]
        rows.append(
            [
                InlineKeyboardButton("−", callback_data=f"qty:minus:{item_id}"),
                InlineKeyboardButton(
                    str(item["quantity"]), callback_data=f"qty:noop:{item_id}"
                ),
                InlineKeyboardButton("+", callback_data=f"qty:plus:{item_id}"),
                InlineKeyboardButton("Remove", callback_data=f"qty:remove:{item_id}"),
            ]
        )
    if items:
        rows.extend(
            [
                [InlineKeyboardButton("🚚 Checkout for delivery", callback_data="flow:delivery")],
                [InlineKeyboardButton("Clear cart", callback_data="qty:clear")],
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton("🍽 Continue browsing", callback_data="menu")],
            [InlineKeyboardButton("🏠 Main menu", callback_data="home")],
        ]
    )
    return InlineKeyboardMarkup(rows)


def order_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Place order", callback_data="order:confirm")],
            [InlineKeyboardButton("Cancel", callback_data="order:cancel")],
        ]
    )


def reservation_guests_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(str(guests), callback_data=f"reserve:guests:{guests}")
                for guests in range(1, 5)
            ],
            [
                InlineKeyboardButton(str(guests), callback_data=f"reserve:guests:{guests}")
                for guests in range(5, 9)
            ],
            [
                InlineKeyboardButton("9–12", callback_data="reserve:guests:12"),
            ],
            [InlineKeyboardButton("Cancel", callback_data="flow:cancel")],
        ]
    )


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Cancel", callback_data="flow:cancel")]]
    )


def item_label(item_id: str) -> str:
    return ITEMS_BY_ID[item_id]["name"]
