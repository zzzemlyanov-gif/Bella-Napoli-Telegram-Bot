"""Bella Napoli restaurant ordering and reservation Telegram bot."""

import logging
import os
import re
from html import escape
from pathlib import Path
from datetime import date, datetime
from typing import Any

from dotenv import load_dotenv
from telegram import BotCommand, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

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
from bella_napoli_bot.menu import DELIVERY_FEE, ITEMS_BY_ID, MENU, money

load_dotenv()

ADDRESS, ORDER_PHONE, ORDER_CONFIRM, RES_DATE, RES_TIME, RES_GUESTS, RES_NAME, RES_PHONE = range(8)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("bella_napoli_bot")
DB = RestaurantDB(
    os.getenv("DATABASE_PATH")
    or str(Path(__file__).with_name("bella_napoli.sqlite3"))
)


def _db() -> RestaurantDB:
    """Return the process database, initialized using configured DB path."""
    return DB


def _username(update: Update) -> str | None:
    user = update.effective_user
    return f"@{user.username}" if user and user.username else None


def _valid_phone(value: str) -> bool:
    digits = re.sub(r"\D", "", value)
    return 7 <= len(digits) <= 15


def _format_cart(items: list[dict[str, Any]]) -> tuple[str, int]:
    if not items:
        return "Your cart is empty. Browse the menu to add something delicious.", 0
    lines = ["🛒 <b>Your Bella Napoli cart</b>", ""]
    subtotal = 0
    for item in items:
        line_total = item["price"] * item["quantity"]
        subtotal += line_total
        lines.append(
            f"• {item['name']} × {item['quantity']} — {money(line_total)}"
        )
    lines.extend(["", f"<b>Subtotal: {money(subtotal)}</b>"])
    return "\n".join(lines), subtotal


def _format_order_items(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"• {item['name']} × {item['quantity']} — "
        f"{money(item['price'] * item['quantity'])}"
        for item in items
    )


async def _show_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if message:
        await message.reply_text(
            "Welcome to <b>Bella Napoli</b>!\n"
            "Italian favorites, made with care. What would you like to do?",
            parse_mode="HTML",
            reply_markup=home_keyboard(),
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await _show_home(update, context)
    return ConversationHandler.END


async def cancel_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.clear()
    if update.effective_message:
        await update.effective_message.reply_text(
            "That request has been cancelled.", reply_markup=home_keyboard()
        )
    return ConversationHandler.END


async def cancel_flow_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "That request has been cancelled.", reply_markup=home_keyboard()
        )
    context.user_data.clear()
    return ConversationHandler.END


async def handle_navigation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data or ""

    if data == "home":
        context.user_data.clear()
        await query.edit_message_text(
            "Welcome to <b>Bella Napoli</b>!\n"
            "Italian favorites, made with care. What would you like to do?",
            parse_mode="HTML",
            reply_markup=home_keyboard(),
        )
    elif data == "menu":
        await query.edit_message_text(
            "<b>Bella Napoli menu</b>\nChoose a category:",
            parse_mode="HTML",
            reply_markup=categories_keyboard(),
        )
    elif data.startswith("cat:"):
        category_id = data.split(":", 1)[1]
        if category_id not in MENU:
            await query.edit_message_text("That menu category is unavailable.")
            return
        category = MENU[category_id]
        lines = [f"<b>{category['title']}</b>", ""]
        for item in category["items"]:
            lines.append(
                f"<b>{item['name']}</b> · {money(item['price'])}\n"
                f"<i>{item['description']}</i>"
            )
        await query.edit_message_text(
            "\n\n".join(lines),
            parse_mode="HTML",
            reply_markup=category_keyboard(category_id),
        )
    elif data.startswith("add:"):
        item_id = data.split(":", 1)[1]
        if item_id not in ITEMS_BY_ID or not update.effective_user:
            await query.edit_message_text("That item is no longer available.")
            return
        _db().add_to_cart(update.effective_user.id, item_id)
    elif data == "cart":
        if not update.effective_user:
            return
        items = _db().get_cart(update.effective_user.id)
        text, _ = _format_cart(items)
        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=cart_keyboard(items)
        )
    elif data.startswith("qty:"):
        if not update.effective_user:
            return
        parts = data.split(":")
        action = parts[1]
        if action == "clear":
            _db().clear_cart(update.effective_user.id)
        elif action == "noop":
            return
        else:
            item_id = parts[2] if len(parts) > 2 else ""
            cart = _db().get_cart(update.effective_user.id)
            current = next((item["quantity"] for item in cart if item["id"] == item_id), 0)
            if action == "plus" and item_id in ITEMS_BY_ID:
                _db().set_cart_quantity(update.effective_user.id, item_id, current + 1)
            elif action == "minus" and item_id in ITEMS_BY_ID:
                _db().set_cart_quantity(update.effective_user.id, item_id, current - 1)
            elif action == "remove":
                _db().set_cart_quantity(update.effective_user.id, item_id, 0)
        items = _db().get_cart(update.effective_user.id)
        text, _ = _format_cart(items)
        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=cart_keyboard(items)
        )


async def flow_navigation_fallback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.clear()
    await handle_navigation(update, context)
    return ConversationHandler.END


async def begin_delivery(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query or not update.effective_user:
        return ConversationHandler.END
    await query.answer()
    items = _db().get_cart(update.effective_user.id)
    if not items:
        await query.edit_message_text(
            "Your cart is empty. Browse the menu first.",
            reply_markup=categories_keyboard(),
        )
        return ConversationHandler.END
    context.user_data["order_items"] = items
    context.user_data.pop("flow", None)
    await query.edit_message_text(
        "Please send your full delivery address, including apartment or entrance details.",
        reply_markup=cancel_keyboard(),
    )
    return ADDRESS


async def receive_address(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.effective_message:
        return ADDRESS
    address = (update.effective_message.text or "").strip()
    if len(address) < 8 or len(address) > 300:
        await update.effective_message.reply_text(
            "Please send a complete address (8–300 characters)."
        )
        return ADDRESS
    context.user_data["delivery_address"] = address
    await update.effective_message.reply_text(
        "What phone number should the courier use to contact you?"
    )
    return ORDER_PHONE


async def receive_order_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.effective_message:
        return ORDER_PHONE
    phone = (update.effective_message.text or "").strip()
    if not _valid_phone(phone):
        await update.effective_message.reply_text(
            "Please enter a valid phone number with 7–15 digits."
        )
        return ORDER_PHONE
    context.user_data["delivery_phone"] = phone
    items = context.user_data.get("order_items", [])
    _, subtotal = _format_cart(items)
    total = subtotal + DELIVERY_FEE
    summary = (
        "<b>Confirm your delivery order</b>\n\n"
        f"{_format_order_items(items)}\n\n"
        f"Subtotal: {money(subtotal)}\n"
        f"Delivery: {money(DELIVERY_FEE)}\n"
        f"<b>Total: {money(total)}</b>\n\n"
        f"Address: {escape(context.user_data['delivery_address'])}\n"
        f"Phone: {escape(phone)}\n\n"
        "Payment is arranged with the restaurant on delivery."
    )
    await update.effective_message.reply_text(
        summary,
        parse_mode="HTML",
        reply_markup=order_confirmation_keyboard(),
    )
    return ORDER_CONFIRM


async def confirm_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    user = update.effective_user
    if not query or not user:
        return ConversationHandler.END
    await query.answer()
    if query.data == "order:cancel":
        context.user_data.clear()
        await query.edit_message_text(
            "Order cancelled. Your cart is still saved.", reply_markup=home_keyboard()
        )
        return ConversationHandler.END

    items = _db().get_cart(user.id)
    if not items:
        context.user_data.clear()
        await query.edit_message_text(
            "Your cart is empty, so no order was placed.",
            reply_markup=home_keyboard(),
        )
        return ConversationHandler.END
    _, subtotal = _format_cart(items)
    order_id = _db().create_order(
        user_id=user.id,
        username=_username(update),
        customer_name=user.full_name,
        phone=context.user_data["delivery_phone"],
        address=context.user_data["delivery_address"],
        items=items,
        subtotal=subtotal,
        delivery_fee=DELIVERY_FEE,
    )
    await query.edit_message_text(
        f"Thank you! Order <b>#{order_id}</b> has been sent to Bella Napoli. "
        "The restaurant will contact you to confirm delivery.",
        parse_mode="HTML",
        reply_markup=home_keyboard(),
    )
    await notify_admin(
        context,
        "<b>New delivery order</b>\n"
        f"Order: #{order_id}\n"
        f"Customer: {escape(user.full_name)} "
        f"({escape(_username(update) or 'no username')})\n"
        f"Phone: {escape(context.user_data['delivery_phone'])}\n"
        f"Address: {escape(context.user_data['delivery_address'])}\n\n"
        f"{_format_order_items(items)}\n\n"
        f"Subtotal: {money(subtotal)}\n"
        f"Delivery: {money(DELIVERY_FEE)}\n"
        f"<b>Total: {money(subtotal + DELIVERY_FEE)}</b>",
    )
    context.user_data.clear()
    return ConversationHandler.END


async def begin_reservation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(
        "What date would you like to visit? Please use YYYY-MM-DD "
        "(for example, 2026-10-20).",
        reply_markup=cancel_keyboard(),
    )
    return RES_DATE


async def receive_reservation_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.effective_message:
        return RES_DATE
    try:
        requested = date.fromisoformat((update.effective_message.text or "").strip())
    except ValueError:
        await update.effective_message.reply_text("Use YYYY-MM-DD, for example 2026-10-20.")
        return RES_DATE
    if requested < date.today():
        await update.effective_message.reply_text("Please choose today or a future date.")
        return RES_DATE
    context.user_data["reservation_date"] = requested.isoformat()
    await update.effective_message.reply_text(
        "What time would you like? Use 24-hour HH:MM (for example, 19:30)."
    )
    return RES_TIME


async def receive_reservation_time(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.effective_message:
        return RES_TIME
    raw_time = (update.effective_message.text or "").strip()
    try:
        parsed = datetime.strptime(raw_time, "%H:%M")
    except ValueError:
        await update.effective_message.reply_text("Please use 24-hour HH:MM, for example 19:30.")
        return RES_TIME
    context.user_data["reservation_time"] = parsed.strftime("%H:%M")
    await update.effective_message.reply_text(
        "How many guests?",
        reply_markup=reservation_guests_keyboard(),
    )
    return RES_GUESTS


async def receive_reservation_guests(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    if not query:
        return RES_GUESTS
    await query.answer()
    try:
        guests = int((query.data or "").rsplit(":", 1)[1])
    except (IndexError, ValueError):
        await query.edit_message_text("Please choose between 1 and 12 guests.")
        return RES_GUESTS
    if not 1 <= guests <= 12:
        await query.edit_message_text("Please choose between 1 and 12 guests.")
        return RES_GUESTS
    context.user_data["guests"] = guests
    await query.edit_message_text("What name should we put the reservation under?")
    return RES_NAME


async def receive_reservation_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.effective_message:
        return RES_NAME
    name = (update.effective_message.text or "").strip()
    if not 2 <= len(name) <= 100:
        await update.effective_message.reply_text("Please send a name between 2 and 100 characters.")
        return RES_NAME
    context.user_data["reservation_name"] = name
    await update.effective_message.reply_text("What phone number can we contact you on?")
    return RES_PHONE


async def receive_reservation_phone(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    if not update.effective_message or not update.effective_user:
        return RES_PHONE
    phone = (update.effective_message.text or "").strip()
    if not _valid_phone(phone):
        await update.effective_message.reply_text(
            "Please enter a valid phone number with 7–15 digits."
        )
        return RES_PHONE
    user = update.effective_user
    reservation_id = _db().create_reservation(
        user_id=user.id,
        username=_username(update),
        customer_name=context.user_data["reservation_name"],
        phone=phone,
        reservation_date=context.user_data["reservation_date"],
        reservation_time=context.user_data["reservation_time"],
        guests=context.user_data["guests"],
    )
    await update.effective_message.reply_text(
        f"Thank you! Reservation request <b>#{reservation_id}</b> has been sent "
        "to Bella Napoli. We’ll contact you to confirm.",
        parse_mode="HTML",
        reply_markup=home_keyboard(),
    )
    await notify_admin(
        context,
        "<b>New table reservation</b>\n"
        f"Request: #{reservation_id}\n"
        f"Name: {escape(context.user_data['reservation_name'])}\n"
        f"Phone: {escape(phone)}\n"
        f"Date: {context.user_data['reservation_date']}\n"
        f"Time: {context.user_data['reservation_time']}\n"
        f"Guests: {context.user_data['guests']}\n"
        f"Telegram: {_username(update) or user.id}",
    )
    context.user_data.clear()
    return ConversationHandler.END


async def notify_admin(
    context: ContextTypes.DEFAULT_TYPE, text: str
) -> None:
    admin_chat_id = os.getenv("ADMIN_CHAT_ID", "").strip()
    if not admin_chat_id:
        logger.error("ADMIN_CHAT_ID is not configured; notification was not sent")
        return
    try:
        await context.bot.send_message(
            chat_id=int(admin_chat_id), text=text, parse_mode="HTML"
        )
    except (ValueError, TelegramError):
        logger.exception("Could not send a notification to the configured admin chat")


async def admin_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user = update.effective_user
    message = update.effective_message
    configured_admin = os.getenv("ADMIN_CHAT_ID", "").strip()
    if not user or not message or not configured_admin or str(user.id) != configured_admin:
        if message:
            await message.reply_text("This command is for restaurant staff only.")
        return ConversationHandler.END

    orders = _db().get_recent_orders(5)
    reservations = _db().get_recent_reservations(5)
    lines = ["<b>Recent delivery orders</b>"]
    if not orders:
        lines.append("No orders yet.")
    for order in orders:
        lines.append(
            f"#{order['id']} · {escape(order['customer_name'])} · "
            f"{money(order['total'])} · "
            f"{order['status']} · {order['created_at']}"
        )
    lines.extend(["", "<b>Recent reservations</b>"])
    if not reservations:
        lines.append("No reservations yet.")
    for reservation in reservations:
        lines.append(
            f"#{reservation['id']} · {escape(reservation['customer_name'])} · "
            f"{reservation['reservation_date']} {reservation['reservation_time']} · "
            f"{reservation['guests']} guests · {reservation['status']}"
        )
    await message.reply_text("\n".join(lines), parse_mode="HTML")
    return ConversationHandler.END


async def set_commands(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Open the Bella Napoli menu"),
            BotCommand("menu", "Browse the restaurant menu"),
            BotCommand("cart", "View your shopping cart"),
            BotCommand("cancel", "Cancel the current request"),
            BotCommand("admin", "View recent orders and reservations"),
        ]
    )


async def show_menu_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.clear()
    if update.effective_message:
        await update.effective_message.reply_text(
            "<b>Bella Napoli menu</b>\nChoose a category:",
            parse_mode="HTML",
            reply_markup=categories_keyboard(),
        )
    return ConversationHandler.END


async def error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.error("Unhandled Telegram bot error", exc_info=context.error)


def build_application(token: str) -> Application:
    application = Application.builder().token(token).concurrent_updates(False).post_init(
        set_commands
    ).build()

    flow = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(begin_delivery, pattern=r"^flow:delivery$"),
            CallbackQueryHandler(begin_reservation, pattern=r"^flow:reserve$"),
            CommandHandler("start", start),
            CommandHandler("menu", show_menu_command),
            CommandHandler("cart", show_cart_command),
            CommandHandler("admin", admin_command),
        ],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            ORDER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_order_phone)],
            ORDER_CONFIRM: [
                CallbackQueryHandler(confirm_order, pattern=r"^order:(confirm|cancel)$")
            ],
            RES_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reservation_date)
            ],
            RES_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reservation_time)
            ],
            RES_GUESTS: [
                CallbackQueryHandler(receive_reservation_guests, pattern=r"^reserve:guests:")
            ],
            RES_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reservation_name)
            ],
            RES_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reservation_phone)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start),
            CommandHandler("menu", show_menu_command),
            CommandHandler("cart", show_cart_command),
            CommandHandler("admin", admin_command),
            CallbackQueryHandler(
                flow_navigation_fallback,
                pattern=r"^(home|menu|cart|cat:|add:|qty:)",
            ),
            CallbackQueryHandler(cancel_flow_callback, pattern=r"^(home|flow:cancel)$"),
        ],
        allow_reentry=True,
    )

    application.add_handler(flow)
    application.add_handler(
        CallbackQueryHandler(
            handle_navigation,
            pattern=r"^(home|menu|cart|cat:|add:|qty:)",
        )
    )
    application.add_error_handler(error_handler)
    return application


async def show_cart_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data.clear()
    user = update.effective_user
    message = update.effective_message
    if not user or not message:
        return ConversationHandler.END
    items = _db().get_cart(user.id)
    text, _ = _format_cart(items)
    await message.reply_text(text, parse_mode="HTML", reply_markup=cart_keyboard(items))
    return ConversationHandler.END


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    admin_chat_id = os.getenv("ADMIN_CHAT_ID", "").strip()
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is required. Add your bot token in Replit Secrets."
        )
    if not admin_chat_id:
        raise SystemExit(
            "ADMIN_CHAT_ID is required. Set it to the Telegram account ID that receives restaurant alerts."
        )
    try:
        int(admin_chat_id)
    except ValueError as error:
        raise SystemExit("ADMIN_CHAT_ID must be a numeric Telegram chat ID.") from error

    logger.info("Starting Bella Napoli Telegram bot")
    build_application(token).run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
