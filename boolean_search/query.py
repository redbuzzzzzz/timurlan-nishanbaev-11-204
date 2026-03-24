from __future__ import annotations

import re
from dataclasses import dataclass

from .indexing import InvertedIndexData

TOKEN_PATTERN = re.compile(r"\(|\)|AND|OR|NOT|[A-Za-z]+", re.IGNORECASE)
PRECEDENCE = {"OR": 1, "AND": 2, "NOT": 3}
RIGHT_ASSOCIATIVE = {"NOT"}
OPERATORS = set(PRECEDENCE)


@dataclass(frozen=True)
class QueryResult:
    normalized_query: str
    documents: list[str]


def search_query(query: str, index_data: InvertedIndexData) -> QueryResult:
    tokens = tokenize_query(query)
    postfix = to_postfix(tokens)
    documents = evaluate_postfix(
        postfix,
        index_data.index,
        set(index_data.documents),
    )
    return QueryResult(
        normalized_query=" ".join(tokens),
        documents=sorted(documents),
    )


def tokenize_query(query: str) -> list[str]:
    tokens: list[str] = []
    position = 0

    while position < len(query):
        if query[position].isspace():
            position += 1
            continue

        match = TOKEN_PATTERN.match(query, position)
        if not match:
            snippet = query[position : position + 20]
            raise ValueError(f"Unexpected token near: {snippet!r}")

        raw_token = match.group(0)
        upper_token = raw_token.upper()

        if raw_token in {"(", ")"}:
            tokens.append(raw_token)
        elif upper_token in OPERATORS:
            tokens.append(upper_token)
        else:
            tokens.append(raw_token.lower())

        position = match.end()

    if not tokens:
        raise ValueError("Query is empty")

    validate_tokens(tokens)
    return tokens


def validate_tokens(tokens: list[str]) -> None:
    expect_operand = True
    open_parentheses = 0

    for token in tokens:
        if expect_operand:
            if token == "NOT":
                continue
            if token == "(":
                open_parentheses += 1
                continue
            if is_term(token):
                expect_operand = False
                continue
            raise ValueError(f"Unexpected token in query: {token}")

        if token in {"AND", "OR"}:
            expect_operand = True
            continue
        if token == ")":
            open_parentheses -= 1
            if open_parentheses < 0:
                raise ValueError("Unbalanced parentheses in query")
            continue
        raise ValueError(f"Unexpected token in query: {token}")

    if expect_operand:
        raise ValueError("Query cannot end with an operator")
    if open_parentheses != 0:
        raise ValueError("Unbalanced parentheses in query")


def to_postfix(tokens: list[str]) -> list[str]:
    output: list[str] = []
    stack: list[str] = []

    for token in tokens:
        if is_term(token):
            output.append(token)
            continue

        if token == "(":
            stack.append(token)
            continue

        if token == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("Unbalanced parentheses in query")
            stack.pop()
            continue

        while stack and stack[-1] in OPERATORS:
            top = stack[-1]
            current_precedence = PRECEDENCE[token]
            top_precedence = PRECEDENCE[top]
            if token in RIGHT_ASSOCIATIVE:
                should_pop = current_precedence < top_precedence
            else:
                should_pop = current_precedence <= top_precedence
            if not should_pop:
                break
            output.append(stack.pop())

        stack.append(token)

    while stack:
        top = stack.pop()
        if top in {"(", ")"}:
            raise ValueError("Unbalanced parentheses in query")
        output.append(top)

    return output


def evaluate_postfix(
    postfix_tokens: list[str],
    inverted_index: dict[str, list[str]],
    all_documents: set[str],
) -> set[str]:
    stack: list[set[str]] = []

    for token in postfix_tokens:
        if is_term(token):
            stack.append(set(inverted_index.get(token, [])))
            continue

        if token == "NOT":
            if not stack:
                raise ValueError("Invalid query")
            operand = stack.pop()
            stack.append(all_documents - operand)
            continue

        if len(stack) < 2:
            raise ValueError("Invalid query")

        right = stack.pop()
        left = stack.pop()

        if token == "AND":
            stack.append(left & right)
        elif token == "OR":
            stack.append(left | right)
        else:
            raise ValueError(f"Unknown operator: {token}")

    if len(stack) != 1:
        raise ValueError("Invalid query")

    return stack[0]


def is_term(token: str) -> bool:
    return token not in OPERATORS and token not in {"(", ")"}
