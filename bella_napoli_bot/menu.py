"""Меню и цены ресторана. Каталог можно изменить в этом файле."""

MENU = {
    "pizza": {
        "title": "🍕 Пицца",
        "items": [
            {
                "id": "margherita",
                "name": "Маргарита",
                "description": "Томаты, моцарелла, свежий базилик",
                "price": 690,
            },
            {
                "id": "diavola",
                "name": "Диавола",
                "description": "Острая салями, моцарелла, томаты",
                "price": 850,
            },
            {
                "id": "quattro_formaggi",
                "name": "Кватро Формаджи",
                "description": "Четыре итальянских сыра на сливочной основе",
                "price": 890,
            },
        ],
    },
    "pasta": {
        "title": "🍝 Паста",
        "items": [
            {
                "id": "carbonara",
                "name": "Карбонара",
                "description": "Гуанчале, яичный желток, пекорино, чёрный перец",
                "price": 720,
            },
            {
                "id": "bolognese",
                "name": "Тальятелле болоньезе",
                "description": "Тушёная говядина в томатном соусе рагу",
                "price": 760,
            },
            {
                "id": "pomodoro",
                "name": "Пенне аль помодоро",
                "description": "Пенне, томаты Сан-Марцано, базилик",
                "price": 590,
            },
        ],
    },
    "antipasti": {
        "title": "🥗 Закуски",
        "items": [
            {
                "id": "bruschetta",
                "name": "Брускетта с томатами",
                "description": "Поджаренный хлеб, томаты, базилик, оливковое масло",
                "price": 390,
            },
            {
                "id": "caprese",
                "name": "Салат «Капрезе»",
                "description": "Томаты, моцарелла, базилик, бальзамический соус",
                "price": 550,
            },
        ],
    },
    "dessert": {
        "title": "🍰 Десерты",
        "items": [
            {
                "id": "tiramisu",
                "name": "Тирамису",
                "description": "Савоярди с эспрессо, маскарпоне, какао",
                "price": 420,
            },
            {
                "id": "panna_cotta",
                "name": "Панна-котта",
                "description": "Ванильный сливочный десерт с ягодным соусом",
                "price": 390,
            },
        ],
    },
    "drinks": {
        "title": "🥤 Напитки",
        "items": [
            {
                "id": "lemonade",
                "name": "Домашний лимонад",
                "description": "Свежий лимон, мята, газированная вода",
                "price": 250,
            },
            {
                "id": "espresso",
                "name": "Эспрессо",
                "description": "Классический итальянский эспрессо",
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
