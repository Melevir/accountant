import argparse
import datetime
from decimal import Decimal
import collections
from typing import Tuple, List, NamedTuple

from tinkoff_csv_parser import TinkoffCSVParser

if False:  # TYPE_CHECKING
    from typing import DefaultDict


class Transaction(NamedTuple):
    requested_at: datetime.datetime
    paid_at: datetime.date
    card_last_digits: str
    status: str
    amount_currency: Decimal
    currency: str
    amount_rub: Decimal
    category: str
    mcc_code: int
    description: str
    row_index: int


class RecurrentPayment(NamedTuple):
    description: str
    total_paid: Decimal
    last_payment_date: datetime.date


def load_and_validate_transactions_data(filepath: str) -> Tuple[List[Transaction], List[str]]:
    parser = TinkoffCSVParser(filepath, delimiter=';')
    parser()
    data = [Transaction(**r) for r in parser.cleaned_data]
    return data, parser.errors


def filter_transactions(
    raw_transactions_data: List[Transaction],
    card_last_digits: str,
) -> List[Transaction]:
    result_transactions = []
    for raw_transaction in raw_transactions_data:
        if (
            raw_transaction.amount_rub < 0
            and (
                raw_transaction.card_last_digits.endswith(card_last_digits)
                if card_last_digits else True
            )
        ):
            result_transactions.append(raw_transaction)
    return result_transactions


def is_recurrent_payments(
        description: str,
        transactions: List[Transaction],
        sure_recurrent_payments_descriptions: List[str],
) -> bool:
    if description in sure_recurrent_payments_descriptions:
        return True

    if 'monthly' in description.lower() or 'membership' in description.lower():
        return True

    total_paid_dates = sorted({t.requested_at.date() for t in transactions})[1:]
    total_paid_days = sorted({t.requested_at.day for t in transactions})

    if len(total_paid_dates) >= 3 and len(total_paid_days) == 1:  # is paid same day every month
        return True

    delta_days_in_payments = {
        (d1 - d2).days for d1, d2 in zip(total_paid_dates[1:], total_paid_dates)
    }
    delta_days_hist = collections.Counter(delta_days_in_payments).most_common()
    if (
        delta_days_in_payments
        and (
            # paid in +-day period
            max(delta_days_in_payments) - min(delta_days_in_payments) <= 2
            # 60% of payments are in same period
            or delta_days_hist[0][1] >= len(delta_days_in_payments) * .6
        )
        and len(total_paid_dates) >= 3
        and min(delta_days_in_payments) > 5
    ):
        return True
    return False


def analyze_for_recurrent_payments(
    transactions_data: List[Transaction],
    sure_recurrent_payments_descriptions: List[str],
    only_active: bool,
) -> List[RecurrentPayment]:
    grouped_by_description: DefaultDict[str, List[Transaction]] = collections.defaultdict(list)
    for transaction in transactions_data:
        grouped_by_description[transaction.description].append(transaction)

    recurrent_payments = []
    for description, transactions in grouped_by_description.items():
        if is_recurrent_payments(description, transactions, sure_recurrent_payments_descriptions):
            recurrent_payments.append(
                RecurrentPayment(
                    description=description,
                    total_paid=abs(sum(t.amount_rub for t in transactions)),  # type: ignore
                    last_payment_date=max(t.requested_at for t in transactions).date(),
                ),
            )
    if only_active:
        recurrent_payments = [
            r for r in recurrent_payments
            if (datetime.datetime.now().date() - r.last_payment_date).days <= 30
        ]
    return recurrent_payments


def print_errors(errors: List[str]) -> None:
    print('Import errors found:')  # noqa: T001
    for error in errors:
        print(f'\t{error}')  # noqa: T001


def print_recurrent_payments_info(recurrent_payments_info: List[RecurrentPayment]) -> None:
    print('Recurrent payments descriptions:')  # noqa: T001
    for recurrent_info in recurrent_payments_info:
        print(  # noqa: T001
            f'{recurrent_info.description} (total paid: {recurrent_info.total_paid}, '
            f'last paid: {recurrent_info.last_payment_date})',
        )


def parse_args() -> Tuple[str, List[str], str]:
    parser = argparse.ArgumentParser(
        description='Script that checks payments history and tries to find'
                    ' recurrent payments (subscriptions, etc).',
    )
    parser.add_argument('filepath', help='path to payments csv export file from Tinkoff')
    parser.add_argument('--sure_recurrent_payments_descriptions', default='')
    parser.add_argument('--card_last_digits')
    args = parser.parse_args()
    return (
        args.filepath,
        args.sure_recurrent_payments_descriptions.split(',') or [],
        args.card_last_digits,
    )


if __name__ == '__main__':
    filepath, sure_recurrent_payments_descriptions, card_last_digits = parse_args()
    raw_transactions_data, errors = load_and_validate_transactions_data(filepath)
    if errors:
        print_errors(errors)
        exit(1)
    transactions_data = filter_transactions(raw_transactions_data, card_last_digits)
    recurrent_payments_info = analyze_for_recurrent_payments(
        transactions_data,
        sure_recurrent_payments_descriptions,
        only_active=True,
    )
    print_recurrent_payments_info(recurrent_payments_info)
