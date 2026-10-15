# ======================================================================================
#                                    INCLUDES
# ======================================================================================
from dataclasses import dataclass

from lark import Lark, Token, Tree


# ======================================================================================
#                                     DATA MODEL
# ======================================================================================
@dataclass
class Product:
    name: str
    price: float
    stock: int


products: dict[str, Product] = {
    "monorail": Product(name="Monorail", price=1449.99, stock=30),
    "hewlett_packard": Product(name="Hewlett Packard", price=1849.99, stock=23),
    "compaq": Product(name="COMPAQ", price=2399.99, stock=8),
}


# ======================================================================================
#                                     NLP
# ======================================================================================
grammar: str = """
%import common.WS
%ignore WS

start: price_question

price_question: HOW_MUCH BE DET ITEM | HOW_MUCH BE ITEM

HOW_MUCH: "how much"
BE: "is"|"are"
DET: "the"|"a"|"any"

ITEM: /[a-z]+/

"""


def print_tree(node: Tree | Token, depth: int = 0) -> None:
    if isinstance(node, Token):
        print(" " * depth + f"{node.type} = {node.value}")
        return
    print(" " * depth + node.data)
    for subtree in node.children:
        print_tree(subtree, depth + 1)


def process_query(query: str) -> str:
    parser = Lark(grammar, parser="earley")
    tree = parser.parse(query)
    print_tree(tree)
    query_node: Tree | Token = tree.children[0]
    if isinstance(query_node, Token):
        return "ERROR"

    if query_node.data == "price_question":
        item = list(query_node.find_token("ITEM"))[0]
        price = products[item.value].price
        return f"The price of {item.value} is {price}"

    return "ERROR"


# ======================================================================================
#                                   MAIN
# ======================================================================================
def main():
    print(process_query(input()))


if __name__ == "__main__":
    main()
