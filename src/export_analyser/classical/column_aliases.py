from __future__ import annotations

import unicodedata

COLUMN_ALIASES: dict[str, list[str]] = {
    "order_id": [
        "order id", "order number", "order_id", "name", "id", "number",
        "invoiceno", "invoice no", "invoice number", "invoice",
        "артикул товару", "артикул", "номер замовлення",
        "bestellnummer", "auftragsnummer",
        "numer zamowienia", "zamowienie",
        "commande", "numero de commande",
    ],
    "date": [
        "created at", "date", "order date", "order_date", "created", "placed",
        "invoicedate", "invoice date",
        "час оформлення", "дата", "дата замовлення",
        "bestelldatum", "datum", "erstellt am",
        "data zamowienia", "data",
        "date de commande",
    ],
    "status": [
        "financial status", "status", "order status", "state", "fulfillment status",
        "статус",
        "bestellstatus", "status der bestellung",
        "stan", "status zamowienia",
        "statut", "etat",
    ],
    "amount": [
        "total", "price", "amount", "total price", "order total", "revenue", "sum",
        "unitprice", "unit price",
        "ціна товару", "ціна", "сума", "price_uah",
        "betrag", "preis", "gesamtbetrag", "summe",
        "kwota", "cena", "wartosc", "price_pln",
        "montant", "prix",
    ],
    "channel": [
        "source", "channel", "sales channel", "origin",
        "джерело", "канал",
        "kanal", "quelle", "vertriebskanal",
        "kanal sprzedazy", "zrodlo",
        "canal",
    ],
    "product_name": [
        "lineitem name", "product", "product name", "product_name", "item", "товари",
        "description", "stockcode", "sku", "item description",
        "назва товару", "товар", "найменування",
        "produkt", "artikel", "produktname",
        "produkt", "nazwa produktu", "towar",
        "produit", "article",
    ],
    "quantity": [
        "quantity", "qty", "lineitem quantity", "count", "units",
        "кількість",
        "menge", "anzahl", "stueck",
        "ilosc",
        "quantite",
    ],
    "customer": [
        "customer", "buyer", "client", "billing name",
        "customerid", "customer id", "customer_id",
        "покупець", "клієнт",
        "kunde", "kaeufer",
        "klient", "nabywca",
        "client",
    ],
    "city": [
        "city", "town",
        "місто",
        "stadt", "ort",
        "miasto",
        "ville",
    ],
    "country": [
        "country",
        "країна",
        "land",
        "kraj",
        "pays",
    ],
    "delivery_service": [
        "delivery service", "shipping", "carrier", "shipping method",
        "служба доставки",
        "versandart", "lieferdienst",
        "sposob dostawy", "przewoznik",
        "service de livraison", "transporteur",
    ],
    "delivery_date": [
        "delivery date", "shipped at", "fulfilled at",
        "дата доставки",
        "lieferdatum",
        "data dostawy",
        "date de livraison",
    ],
    "manager": [
        "manager", "owner", "agent", "sales rep",
        "менеджер",
        "verantwortlicher",
        "opiekun",
    ],
    "email": [
        "email", "e-mail", "customer email",
        "e-mail покупця", "пошта",
        "e-mail des kunden",
    ],
    "phone": [
        "phone", "telephone", "mobile", "customer phone",
        "телефон покупця", "телефон",
        "telefon",
    ],
    "ticket_id": ["ticket id", "ticket_id", "ticket number", "case id", "тікет"],
    "subject": ["subject", "title", "topic", "тема", "betreff", "temat"],
    "created_at": ["created at", "created_at", "opened at", "received at"],
    "first_response_at": [
        "first response at", "first_response_at", "first reply", "response time",
        "час відповіді", "antwortzeit",
    ],
    "lead_name": ["lead", "lead name", "contact", "prospect", "лід", "kontakt"],
    "stage": ["stage", "pipeline stage", "deal stage", "этап", "этап угоди", "phase"],
    "stock_quantity": [
        "stock", "stock quantity", "inventory", "on hand", "quantity in stock",
        "залишок", "кількість на складі", "lagerbestand", "stan magazynowy",
    ],
}

_MANUAL_FOLD = str.maketrans({
    "ł": "l", "đ": "d", "ø": "o", "ı": "i", "ß": "ss", "æ": "ae", "œ": "oe",
})

def normalise(text: str) -> str:
    s = (text or "").strip().lower().translate(_MANUAL_FOLD)
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    out = []
    for ch in s:
        out.append(ch if ch.isalnum() else " ")
    return " ".join("".join(out).split())

_NORM_LOOKUP: dict[str, str] = {}
for _field, _aliases in COLUMN_ALIASES.items():
    for _a in _aliases:
        _NORM_LOOKUP.setdefault(normalise(_a), _field)

def lookup_exact(header: str) -> str | None:
    return _NORM_LOOKUP.get(normalise(header))

def all_standard_fields() -> list[str]:
    return list(COLUMN_ALIASES.keys())
