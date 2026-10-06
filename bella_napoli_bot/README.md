# Bella Napoli Telegram Bot

Telegram ordering and table-reservation bot built with `python-telegram-bot`.
It has no web interface. Carts, delivery orders, and reservation requests are
stored in SQLite.

## Configure

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather).
2. Add its token as the Replit Secret `TELEGRAM_BOT_TOKEN`.
3. Set `ADMIN_CHAT_ID` to the numeric Telegram user/chat ID that should receive
   order and reservation alerts. The admin should open the bot and press Start
   before the bot tries to send a notification.
4. Install dependencies from the project root:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the bot:

   ```bash
   python -m bella_napoli_bot.main
   ```

The Replit workflow runs the same command. SQLite data is saved to
`bella_napoli_bot/bella_napoli.sqlite3` by default. Set `DATABASE_PATH` to use a
different location.

## Bot features

- `/start`, `/menu`, `/cart`, and `/cancel`
- Menu categories with buttons to add food to the cart
- Quantity controls and delivery checkout
- Delivery address and phone collection with a final order confirmation
- Table reservation date, time, party size, name, and phone collection
- Admin notifications for confirmed delivery orders and reservation requests
- `/admin` for the configured admin to review the latest five orders and
  reservations

Prices and catalog entries live in `menu.py`. Prices are sample values in RUB;
update them before taking real orders. Delivery payment is arranged directly
with the restaurant. The bot records requests but does not process payments.
