"""SQLite persistence for carts, delivery orders, and table reservations."""

import json
import sqlite3
from pathlib import Path
from typing import Any

from .menu import ITEMS_BY_ID

DEFAULT_DB_PATH = Path(__file__).with_name("bella_napoli.sqlite3")


class RestaurantDB:
    def __init__(self, path: str | Path = DEFAULT_DB_PATH) -> None:
        self.path = str(path)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def initialize(self) -> None:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS cart_items (
                    user_id INTEGER NOT NULL,
                    item_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    PRIMARY KEY (user_id, item_id)
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    items_json TEXT NOT NULL,
                    subtotal INTEGER NOT NULL,
                    delivery_fee INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    reservation_date TEXT NOT NULL,
                    reservation_time TEXT NOT NULL,
                    guests INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def add_to_cart(self, user_id: int, item_id: str, amount: int = 1) -> None:
        if item_id not in ITEMS_BY_ID:
            raise ValueError("Unknown menu item")
        if amount < 1 or amount > 20:
            raise ValueError("Quantity must be between 1 and 20")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO cart_items (user_id, item_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, item_id)
                DO UPDATE SET quantity = MIN(cart_items.quantity + excluded.quantity, 20)
                """,
                (user_id, item_id, amount),
            )

    def set_cart_quantity(self, user_id: int, item_id: str, quantity: int) -> None:
        with self.connect() as connection:
            if quantity <= 0:
                connection.execute(
                    "DELETE FROM cart_items WHERE user_id = ? AND item_id = ?",
                    (user_id, item_id),
                )
            else:
                connection.execute(
                    """
                    UPDATE cart_items SET quantity = MIN(?, 20)
                    WHERE user_id = ? AND item_id = ?
                    """,
                    (quantity, user_id, item_id),
                )

    def get_cart(self, user_id: int) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT item_id, quantity FROM cart_items WHERE user_id = ? ORDER BY item_id",
                (user_id,),
            ).fetchall()
        return [
            {**ITEMS_BY_ID[row["item_id"]], "quantity": row["quantity"]}
            for row in rows
            if row["item_id"] in ITEMS_BY_ID
        ]

    def clear_cart(self, user_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

    def create_order(
        self,
        *,
        user_id: int,
        username: str | None,
        customer_name: str,
        phone: str,
        address: str,
        items: list[dict[str, Any]],
        subtotal: int,
        delivery_fee: int,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO orders (
                    user_id, username, customer_name, phone, address,
                    items_json, subtotal, delivery_fee, total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    customer_name,
                    phone,
                    address,
                    json.dumps(items, ensure_ascii=False),
                    subtotal,
                    delivery_fee,
                    subtotal + delivery_fee,
                ),
            )
            connection.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
            return int(cursor.lastrowid)

    def create_reservation(
        self,
        *,
        user_id: int,
        username: str | None,
        customer_name: str,
        phone: str,
        reservation_date: str,
        reservation_time: str,
        guests: int,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reservations (
                    user_id, username, customer_name, phone,
                    reservation_date, reservation_time, guests
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    username,
                    customer_name,
                    phone,
                    reservation_date,
                    reservation_time,
                    guests,
                ),
            )
            return int(cursor.lastrowid)

    def get_recent_orders(self, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def get_recent_reservations(self, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reservations ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]
