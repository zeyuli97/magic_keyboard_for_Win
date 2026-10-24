"""Read a deliberately tiny AHK literal subset for source-contract checks.

This is not an AHK parser/interpreter and does not validate runtime behavior.
Unsupported table syntax fails explicitly instead of silently dropping values.
"""
import re


def tokens(source, starts=None):
    """Return (kind, value) tokens; starts, if given, receives each token's offset."""
    result = []

    def emit(kind, value, begin):
        result.append((kind, value))
        if starts is not None:
            starts.append(begin)

    index = 0
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if char == ";":
            end = source.find("\n", index)
            index = len(source) if end < 0 else end + 1
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end < 0:
                raise AssertionError("Unterminated source comment")
            index = end + 2
            continue
        if char in "\"'":
            begin, quote, value = index, char, ""
            index += 1
            while index < len(source) and source[index] != quote:
                if source[index] == chr(96):
                    index += 1
                    if index >= len(source):
                        raise AssertionError("Unterminated string escape")
                value += source[index]
                index += 1
            if index >= len(source):
                raise AssertionError("Unterminated source string")
            emit("string", value, begin)
            index += 1
            continue
        match = re.match(r"[A-Za-z_][A-Za-z_0-9]*", source[index:])
        if match:
            emit("name", match.group(), index)
            index += len(match.group())
            continue
        match = re.match(r"[0-9]+", source[index:])
        if match:
            emit("number", match.group(), index)
            index += len(match.group())
            continue
        operator = next((op for op in (":=", "!=", "==", "&&", "||") if source.startswith(op, index)), None)
        if operator:
            emit("symbol", operator, index)
            index += len(operator)
        else:
            emit("symbol", char, index)
            index += 1
    return result


def _end(items, start, opening, closing):
    assert items[start][1] == opening
    depth = 1
    for index in range(start + 1, len(items)):
        if items[index][0] != "symbol":
            continue
        if items[index][1] == opening:
            depth += 1
        elif items[index][1] == closing:
            depth -= 1
            if depth == 0:
                return index
    raise AssertionError("Unbalanced source block")


def function_tokens(source, name):
    # A definition's name is the first token on its line. A call can also be
    # followed by a brace, as in `if !Name(...) {`, and a commented-out copy
    # yields no tokens at all; neither may be taken for the definition.
    starts = []
    items = tokens(source, starts)
    bodies = []
    for index, item in enumerate(items[:-2]):
        if item != ("name", name) or items[index + 1][1] != "(":
            continue
        if source[source.rfind("\n", 0, starts[index]) + 1:starts[index]].strip():
            continue
        args_end = _end(items, index + 1, "(", ")")
        if args_end + 1 < len(items) and items[args_end + 1][1] == "{":
            body_end = _end(items, args_end + 1, "{", "}")
            bodies.append(items[args_end + 2:body_end])
    if len(bodies) != 1:
        raise AssertionError(("Duplicate" if bodies else "Missing") + " source function: " + name)
    return bodies[0]


class LiteralReader:
    def __init__(self, items, index=0):
        self.items, self.index = items, index

    def take(self, value=None):
        if self.index >= len(self.items):
            raise AssertionError("Unexpected end of AHK literal")
        item = self.items[self.index]
        self.index += 1
        if value is not None and item[1] != value:
            raise AssertionError(f"Expected {value!r}, found {item!r}")
        return item

    def peek(self, value):
        return self.index < len(self.items) and self.items[self.index][1] == value

    def expression(self):
        kind, value = self.take()
        if kind == "string":
            return value
        if value == "[":
            result = []
            while not self.peek("]"):
                result.append(self.expression())
                if not self.peek("]"):
                    self.take(",")
            self.take("]")
            return result
        if value == "{":
            result = {}
            while not self.peek("}"):
                key = self.take()[1]
                if key in result:
                    raise AssertionError("Duplicate object key")
                self.take(":")
                result[key] = self.expression()
                if not self.peek("}"):
                    self.take(",")
            self.take("}")
            return result
        if kind == "name" and value in ("Map", "StrSplit"):
            self.take("(")
            args = []
            while not self.peek(")"):
                args.append(self.expression())
                if not self.peek(")"):
                    self.take(",")
            self.take(")")
            if value == "StrSplit":
                if len(args) != 2 or not all(isinstance(arg, str) for arg in args) or args[1] != "|":
                    raise AssertionError("Policy StrSplit must contain two literal strings and | delimiter")
                return args[0].split("|")
            if len(args) % 2:
                raise AssertionError("Map must contain key/value pairs")
            result = {}
            for key, item in zip(args[::2], args[1::2]):
                if not isinstance(key, str) or key in result:
                    raise AssertionError("Map must have unique literal string keys")
                result[key] = item
            return result
        raise AssertionError(f"Unsupported policy expression: {(kind, value)!r}")


def return_literal(source, name):
    body = function_tokens(source, name)
    reader = LiteralReader(body)
    reader.take("return")
    result = reader.expression()
    if reader.index != len(body):
        raise AssertionError("Policy function must directly return a literal")
    return result


def static_map(body, name):
    for index in range(len(body) - 3):
        if [item[1] for item in body[index:index + 4]] == ["static", name, ":=", "Map"]:
            value = LiteralReader(body, index + 3).expression()
            if not isinstance(value, dict) or not all(isinstance(item, str) for item in value.values()):
                raise AssertionError("Handler dispatch map must contain literal string values")
            return value
    raise AssertionError("Missing handler dispatch map: " + name)


def contains(body, sequence):
    values = [item[1] for item in body]
    return any(values[index:index + len(sequence)] == sequence for index in range(len(values) - len(sequence) + 1))


def action_blocks_with_output(body):
    """Read actual if-action blocks only when they send and return success."""
    result = set()
    for index in range(len(body) - 5):
        if [item[1] for item in body[index:index + 3]] != ["if", "action", "="]:
            continue
        if body[index + 3][0] != "string" or body[index + 4][1] != "{":
            continue
        end = _end(body, index + 4, "{", "}")
        block = body[index + 5:end]
        if contains(block, ["MF_SendTap", "("]) and contains(block, ["return", "true"]):
            result.add(body[index + 3][1])
    return result
