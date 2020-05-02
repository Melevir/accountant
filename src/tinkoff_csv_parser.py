from import_me.columns import Column
from import_me.parsers.csv import BaseCSVParser
from import_me.processors import (
    DateTimeProcessor, DateProcessor, DecimalProcessor, IntegerProcessor,
)


class TinkoffCSVParser(BaseCSVParser):
    columns = [
        Column(
            'requested_at', index=0, required=True,
            processor=DateTimeProcessor(['%d.%m.%Y %H:%M:%S']),
        ),
        Column('paid_at', index=1, required=False, processor=DateProcessor(['%d.%m.%Y'])),
        Column('card_last_digits', index=2, required=True),
        Column('status', index=3, required=True),
        Column('amount_currency', index=4, required=True, processor=DecimalProcessor()),
        Column('currency', index=5, required=True),
        Column('amount_rub', index=6, required=True, processor=DecimalProcessor()),
        Column('category', index=9, required=True),
        Column('mcc_code', index=10, required=False, processor=IntegerProcessor()),
        Column('description', index=11, required=True),
    ]
