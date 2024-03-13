import psycopg2
from psycopg2._psycopg import cursor
from sshtunnel import SSHTunnelForwarder


def execute_open_package(player_id: int, package_id: int, connect: cursor) -> None:
    connect.execute('SELECT open_package(%s, %s);', (player_id, package_id))

    card_ids = [1, 2, 3]

    for card_id in card_ids:
        connect.execute('SELECT "CardID", "Name", "Attack", "Health", "CategoryID" FROM "Card" '
                        'WHERE "CardID" = %s;', (card_id,))
        card_info = connect.fetchone()
        if card_info:
            print(
                f"CardID: {card_info[0]}, Name: {card_info[1]}, Attack: {card_info[2]}, Health: {card_info[3]},"
                f" CategoryID: {card_info[4]}")
        else:
            print(f"Card with ID {card_id} not found.")


def print_player_promocodes(player_id: int, connect: cursor):
    connect.execute('SELECT "Promocode"."PromocodeID", "Promocode"."Code"'
                    'FROM "Promocode"'
                    'JOIN "Player_Promo" ON "Promocode"."PromocodeID" = "Player_Promo"."PromocodeID"'
                    'WHERE "Player_Promo"."PlayerID" = %s;',
                    (player_id,))

    result = connect.fetchall()
    print(result)


def show_shop_packages(connect: cursor):
    connect.execute('SELECT "Package"."PackageID", "Package"."Name", "Package"."Cost"'
                    'FROM "Package"'
                    'JOIN "Shop" ON "Package"."PackageID" = "Shop"."PackageID";'
                    )
    result = connect.fetchall()

    print(result)


def print_wallet(player_id: int, connect: cursor):
    connect.execute('SELECT "Money"."MoneyID", "Money"."Gold", "Money"."Paper", "Money"."Gems"'
                    'FROM "Money"'
                    'JOIN "Player" ON "Money"."MoneyID" = "Player"."MoneyID"'
                    'WHERE "Player"."PlayerID" = %s;', (player_id,))
    result = connect.fetchall()
    print(result)


def print_cards_from_inventory(player_id: int, connect: cursor) -> None:
    connect.execute('SELECT "Card"."CardID", "Card"."Name", "Card"."Attack", "Card"."Health", "Card"."CategoryID"'
                    'FROM "Card"'
                    'JOIN "Deck" ON "Card"."CardID" = "Deck"."CardID"'
                    'JOIN "Inventory" ON "Deck"."DeckID" = "Inventory"."DeckID"'
                    'JOIN "Player" ON "Inventory"."InventoryID" = "Player"."InventoryID"'
                    'WHERE "Player"."PlayerID" = %s;',
                    (player_id,))

    results = connect.fetchall()

    for row in results:
        print(f"CardID: {row[0]}, Name: {row[1]}, Attack: {row[2]}, Health: {row[3]}, CategoryID: {row[4]}")


def buy_package(player_id: int, package_id: int, connect: cursor) -> None:
    connect.execute('SELECT "Gold" FROM "Money" WHERE "MoneyID" = '
                    '(SELECT "MoneyID" FROM "Player" WHERE "PlayerID" = %s);',
                    (player_id,))
    gold_balance = connect.fetchone()[0]

    if gold_balance < 100:
        print("Недостаточно Gold для покупки пакета.")
        return

    # Снимаем 100 единиц Gold
    connect.execute(
        'UPDATE "Money" SET "Gold" = "Gold" - 100 '
        'WHERE "MoneyID" = (SELECT "MoneyID" FROM "Player" WHERE "PlayerID" = %s);',
        (player_id,))

    # Добавляем пакет в Zakaz
    connect.execute('INSERT INTO "Zakaz" ("PackageID") VALUES (%s) RETURNING "ZakazID";', (package_id,))
    zakaz_id = connect.fetchone()[0]

    print(f"Пакет успешно куплен. ID Zakaz: {zakaz_id}")


def connection() -> cursor:
    try:
        with SSHTunnelForwarder(
                ('helios.se.ifmo.ru', 2222),
                ssh_username="s335134",
                ssh_password="caau#2135",
                remote_bind_address=('pg', 5432)) as server:
            server.start()
            print("server connected")

            conn = psycopg2.connect(dbname="studs",
                                    user="s335134",
                                    password="RdK6ljdUUmNJnR7T",
                                    host="127.0.0.1",
                                    port=server.local_bind_port)
            conn.autocommit = True
            curs = conn.cursor()
            print("database connected")
            return curs
    except Exception as e:
        print(f"Disconnect: {e}")
