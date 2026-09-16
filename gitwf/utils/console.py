"""
Console output formatting utilities.
"""


def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_table(headers: list[str], rows: list[list[str]], col_widths: list[int] = None):
    if not col_widths:
        col_widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=4)) + 2
                      for i, h in enumerate(headers)]

    header_line = "".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * sum(col_widths))
    for row in rows:
        print("".join(str(c).ljust(w) for c, w in zip(row, col_widths)))


def print_check(name: str, passed: bool, message: str):
    symbol = "PASS" if passed else "FAIL"
    print(f"  [{symbol}] {name}: {message}")


def print_key_value(data: dict, indent: int = 2):
    prefix = " " * indent
    max_key = max(len(str(k)) for k in data.keys()) if data else 0
    for k, v in data.items():
        print(f"{prefix}{str(k).ljust(max_key + 2)}{v}")
