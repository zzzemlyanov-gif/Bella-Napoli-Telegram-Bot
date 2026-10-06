"""Restaurant menu and prices. Edit this file to update the catalog."""

MENU = {
    "pizza": {
        "title": "Pizza",
        "items": [
            {
                "id": "margherita",
                "name": "Margherita",
                "description": "Tomato, mozzarella, fresh basil",
                "price": 690,
            },
            {
                "id": "diavola",
                "name": "Diavola",
                "description": "Spicy salami, mozzarella, tomato",
                "price": 850,
            },
            {
                "id": "quattro_formaggi",
                "name": "Quattro Formaggi",
                "description": "Four Italian cheeses, creamy base",
                "price": 890,
            },
        ],
    },
    "pasta": {
        "title": "Pasta",
        "items": [
            {
                "id": "carbonara",
                "name": "Carbonara",
                "description": "Guanciale, egg yolk, pecorino, black pepper",
                "price": 720,
            },
            {
                "id": "bolognese",
                "name": "Tagliatelle Bolognese",
                "description": "Slow-cooked beef and tomato ragù",
                "price": 760,
            },
            {
                "id": "pomodoro",
                "name": "Penne al Pomodoro",
                "description": "Penne, San Marzano tomato, basil",
                "price": 590,
            },
        ],
    },
    "antipasti": {
        "title": "Starters",
        "items": [
            {
                "id": "bruschetta",
                "name": "Tomato Bruschetta",
                "description": "Grilled sourdough, tomato, basil, olive oil",
                "price": 390,
            },
            {
                "id": "caprese",
                "name": "Caprese Salad",
                "description": "Tomato, mozzarella, basil, balsamic",
                "price": 550,
            },
        ],
    },
    "dessert": {
        "title": "Desserts",
        "items": [
            {
                "id": "tiramisu",
                "name": "Tiramisu",
                "description": "Espresso-soaked savoiardi, mascarpone, cocoa",
                "price": 420,
            },
            {
                "id": "panna_cotta",
                "name": "Panna Cotta",
                "description": "Vanilla cream with berry sauce",
                "price": 390,
            },
        ],
    },
    "drinks": {
        "title": "Drinks",
        "items": [
            {
                "id": "lemonade",
                "name": "House Lemonade",
                "description": "Fresh lemon, mint, sparkling water",
                "price": 250,
            },
            {
                "id": "espresso",
                "name": "Espresso",
                "description": "Classic Italian espresso",
                "price": 180,
            },
        ],
    },
}

DELIVERY_FEE = 300
CURRENCY = "₽"

ITEMS_BY_ID = {
    item["id"]: {**item, "category": category_id}
    for category_id, category in MENU.items()
    for item in category["items"]
}


def money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + f" {CURRENCY}"
