import argparse
import sys
from pathlib import Path

from data_shop import Database
from lark import Lark, LarkError, Token, Tree


# ======================================================================================
#                                    NLP / CHAT
# ======================================================================================
def print_tree(node: Tree | Token, depth: int = 0) -> None:
    if isinstance(node, Token):
        print(" " * depth + f"{node.type} = {node.value}")
        return
    print(" " * depth + node.data)
    for subtree in node.children:
        print_tree(subtree, depth + 1)


def process_query(parser: Lark, db: Database, query: str) -> str:
    try:
        tree = parser.parse(query.strip())
        print_tree(tree)

        query_node = tree.children[0]
        if isinstance(query_node, Token):
            return "Błąd: Niepoprawna struktura zapytania."

        item_tokens = list(query_node.find_token("ITEM"))
        if not item_tokens:
            return "Błąd: Nie rozpoznano nazwy produktu w zapytaniu."

        item_name = item_tokens[0].value.lower()

        product = db.get_product(item_name)
        if not product:
            return f"Błąd: Produkt '{item_name}' nie znajduje się w naszej bazie danych."

        if query_node.data == "price_question":
            return f"The price of {product.name} is ${product.price:.2f}."

        if query_node.data == "availability_question":
            if product.stock > 0:
                return f"Yes, {product.name} is in stock."
            return f"No, {product.name} is currently out of stock."

        if query_node.data == "stock_question":
            return f"We currently have {product.stock} unit(s) of {product.name} in stock."

        return "Błąd: Nieznana intencja zapytania."

    except LarkError as e:
        return f"Błąd parsowania gramatyki: Nie rozumiem zapytania ({e})."
    except RuntimeError as e:
        return f"Wystąpił błąd wykonania: {e}"


def run_chat_mode(grammar_path: Path, db: Database) -> None:
    if not grammar_path.is_file():
        print(f"Błąd krytyczny: Plik z gramatyką '{grammar_path}' nie istnieje.")
        sys.exit(1)

    try:
        grammar_text = grammar_path.read_text(encoding="utf-8")
        parser = Lark(grammar_text, parser="earley")
    except (LarkError, OSError) as e:
        print(f"Błąd krytyczny podczas ładowania gramatyki: {e}")
        sys.exit(1)

    print("--- Tryb Użytkownika (Chat) ---")
    print("Witaj w sklepie! Wpisz zapytanie lub 'END' aby zakończyć.\n")

    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue

            if user_input.upper() == "END":
                print("Do widzenia!")
                break

            response = process_query(parser, db, user_input)
            print(f"Odpowiedź: {response}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nPrzerwano działanie programu. Do widzenia!")
            break


# ======================================================================================
#                                 PANEL ADMINA
# ======================================================================================
def run_admin_mode(db: Database) -> None:
    print("\n==========================================")
    print("          PANEL ADMINISTRATORA            ")
    print("==========================================")

    while True:
        print("\nMENU ADMINA:")
        print("1 - Dodaj produkt")
        print("2 - Znajdź produkt")
        print("3 - Zmień produkt")
        print("4 - Usuń produkt")
        print("5 - Lista produktów")
        print("6 - Wyczyść bazę danych")
        print("0 - Wyjście z trybu admina")

        try:
            choice = input("\nWybierz opcję (0-6): ").strip()

            if choice == "1":
                name = input("Nazwa produktu: ").strip()
                if not name:
                    print("Błąd: Nazwa nie może być pusta.")
                    continue
                try:
                    price = float(input("Cena: "))
                    stock = int(input("Ilość na stanie: "))
                    if db.add_product(name, price, stock):
                        print(f"Pomyślnie dodano produkt: {name}")
                except ValueError:
                    print("Błąd: Cena musi być liczbą, a ilość liczbą całkowitą.")

            elif choice == "2":
                name = input("Szukana nazwa produktu: ").strip()
                prod = db.get_product(name)
                if prod:
                    print(f"\n[Znaleziono] Nazwa: {prod.name} | Cena: ${prod.price:.2f} | Stan: {prod.stock} szt.")
                else:
                    print(f"Brak produktu '{name}' w bazie.")

            elif choice == "3":
                name = input("Nazwa produktu do edycji: ").strip()
                prod = db.get_product(name)
                if not prod:
                    print(f"Błąd: Produkt '{name}' nie istnieje.")
                    continue

                print(f"Aktualne dane -> Cena: ${prod.price:.2f}, Stan: {prod.stock}")
                new_price_str = input("Nowa cena (Enter aby pominąć): ").strip()
                new_stock_str = input("Nowa ilość (Enter aby pominąć): ").strip()

                try:
                    new_price = float(new_price_str) if new_price_str else None
                    new_stock = int(new_stock_str) if new_stock_str else None

                    if db.update_product(name, new_price, new_stock):
                        print(f"Zaktualizowano produkt '{name}'.")
                except ValueError:
                    print("Błąd: Wprowadzono niepoprawny format liczbowy.")

            elif choice == "4":
                name = input("Nazwa produktu do usunięcia: ").strip()
                confirm = input(f"Czy na pewno chcesz usunąć '{name}'? (t/n): ").strip().lower()
                if confirm == "t" and db.delete_product(name):
                    print(f"Usunięto produkt '{name}'.")

            elif choice == "5":
                products = db.get_all_products()
                if not products:
                    print("\nBaza danych jest pusta.")
                else:
                    print("\nLISTA PRODUKTÓW W BAZIE:")
                    print("-" * 50)
                    for p in products:
                        print(f"- {p.name:<20} | Cena: ${p.price:>8.2f} | Stan: {p.stock:>4} szt.")
                    print("-" * 50)

            elif choice == "6":
                confirm = input("CZY NA PEWNO chcesz usunąć WSZYSTKIE produkty? (tak/nie): ").strip().lower()
                if confirm == "tak" and db.clear_database():
                    print("Baza danych została wyczyszczona.")

            elif choice == "0":
                print("Wyjście z panelu administratora.")
                break
            else:
                print("Niepoprawny wybór, spróbuj ponownie.")

        except (KeyboardInterrupt, EOFError):
            print("\nWyjście z trybu admina.")
            break


# ======================================================================================
#                                    MAIN
# ======================================================================================
def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Talk Shop NLP Processor")
    arg_parser.add_argument(
        "-g",
        "--grammar",
        type=str,
        default="grammar.txt",
        help="Ścieżka do pliku z gramatyką (domyślnie: grammar.txt)",
    )
    arg_parser.add_argument(
        "-a",
        "--admin",
        action="store_true",
        help="Uruchamia aplikację w trybie administratora",
    )
    args = arg_parser.parse_args()

    db = Database("sqlite:///shop.db")
    db.seed_example_data()

    if args.admin:
        run_admin_mode(db)
    else:
        grammar_path = Path(args.grammar)
        run_chat_mode(grammar_path, db)


if __name__ == "__main__":
    main()