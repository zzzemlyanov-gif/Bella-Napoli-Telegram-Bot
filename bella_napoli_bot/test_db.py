"""Focused tests for the SQLite persistence layer."""

import tempfile
import unittest
from pathlib import Path

from bella_napoli_bot.db import RestaurantDB


class RestaurantDBTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = RestaurantDB(Path(self.temp_dir.name) / "test.sqlite3")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_cart_add_adjust_and_clear(self) -> None:
        self.db.add_to_cart(101, "margherita")
        self.db.add_to_cart(101, "margherita", 2)
        cart = self.db.get_cart(101)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0]["quantity"], 3)
        self.assertEqual(cart[0]["name"], "Маргарита")

        self.db.set_cart_quantity(101, "margherita", 1)
        self.assertEqual(self.db.get_cart(101)[0]["quantity"], 1)
        self.db.clear_cart(101)
        self.assertEqual(self.db.get_cart(101), [])

    def test_order_saves_snapshot_and_clears_cart(self) -> None:
        self.db.add_to_cart(202, "tiramisu", 2)
        items = self.db.get_cart(202)
        order_id = self.db.create_order(
            user_id=202,
            username="@guest",
            customer_name="Bella Guest",
            phone="+79990000000",
            address="1 Via Roma, apartment 2",
            items=items,
            subtotal=840,
            delivery_fee=300,
        )

        orders = self.db.get_recent_orders()
        self.assertEqual(order_id, orders[0]["id"])
        self.assertEqual(orders[0]["total"], 1140)
        self.assertEqual(self.db.get_cart(202), [])

    def test_reservation_is_persisted(self) -> None:
        reservation_id = self.db.create_reservation(
            user_id=303,
            username=None,
            customer_name="Guest",
            phone="+79990000000",
            reservation_date="2026-10-20",
            reservation_time="19:30",
            guests=4,
        )

        reservation = self.db.get_recent_reservations()[0]
        self.assertEqual(reservation_id, reservation["id"])
        self.assertEqual(reservation["guests"], 4)
        self.assertEqual(reservation["reservation_time"], "19:30")

    def test_rejects_unknown_menu_item(self) -> None:
        with self.assertRaises(ValueError):
            self.db.add_to_cart(404, "not-on-menu")


if __name__ == "__main__":
    unittest.main()
