from decimal import Decimal, InvalidOperation


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""
    pass


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s or not s.isalnum():
        raise ValidationError(f"Invalid symbol '{symbol}'. Must be alphanumeric, e.g. BTCUSDT.")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}.")
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}."
        )
    return t


def validate_quantity(quantity: str) -> Decimal:
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValidationError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValidationError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: str) -> Decimal:
    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValidationError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValidationError(f"Price must be greater than zero, got {p}.")
    return p


def validate_stop_price(stop_price: str) -> Decimal:
    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValidationError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValidationError(f"Stop price must be greater than zero, got {sp}.")
    return sp
