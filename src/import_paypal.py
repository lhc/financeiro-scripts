import csv
import datetime
import decimal
import sys
import logging
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def post_transaction(transaction):
    transaction_date = transaction.date.strftime("%Y-%m-%d")

    post_url = "http://beta.lhc.rennerocha.com/new_entry"
    post_data = {
        "entry_date": transaction_date,
        "value": str(transaction.value),
        "account": transaction.account,
        "tags": ",".join(transaction.tags),
        "description": transaction.description,
    }
    print(f"Processing {post_data}.")
    response = httpx.post(post_url, json=post_data)
    print(response)


@dataclass
class Transaction:
    date: datetime.datetime
    description: str
    value: decimal.Decimal
    tags: list[str]
    account: str


def get_transactions(paypal_csv, start_date):
    if start_date is not None:
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")

    transactions = []
    with open(paypal_csv, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            raw_entry_date = row["Data"]
            entry_date = datetime.datetime.strptime(raw_entry_date, "%d/%m/%Y")
            if start_date is not None and entry_date < start_date:
                continue

            entry_currency = row["Moeda"]
            entry_value = row["Bruto "]
            entry_value = decimal.Decimal(
                entry_value.replace(".", "").replace(",", ".")
            )
            entry_tax = row["Tarifa "]
            entry_tax = decimal.Decimal(entry_tax.replace(".", "").replace(",", "."))

            entry_type = row["Descrição"]
            entry_name = row["Nome"]
            if entry_type == "Retirada geral":
                transactions.append(Transaction(
                    date=entry_date,
                    description="Transferência Paypal -> Conta Corrente",
                    value=entry_value,
                    tags=["transferencia", ],
                    account="_paypal_lhc",
                ))
                transactions.append(Transaction(
                    date=entry_date,
                    description="Transferência Paypal -> Conta Corrente",
                    value=-1 * entry_value,
                    tags=["transferencia", ],
                    account="_bradesco",
                ))
            elif entry_type == "Pagamento de doação":
                transactions.append(Transaction(
                    date=entry_date,
                    description=rf"Doação R${entry_value} - {entry_name}",
                    value=entry_value,
                    tags=["doacao", ],
                    account="_paypal_lhc",
                ))
                transactions.append(Transaction(
                    date=entry_date,
                    description=rf"Taxa Doação R${entry_value} - {entry_name}",
                    value=entry_tax,
                    tags=["doacao", 'taxa', ],
                    account="_paypal_lhc",
                ))
            elif entry_type == "Pagamento de assinaturas":
                if entry_currency == "USD":
                    print(f"USD payment - Unable to process automatically:\n{row}")
                    continue

                mensalidades = (75, 85, 110)
                entry_type = (
                    "Mensalidade" if entry_value in mensalidades else "Contribuição"
                )
                entry_tag = (
                    "mensalidade" if entry_type == "Mensalidade" else "contribuicao"
                )

                transactions.append(Transaction(
                    date=entry_date,
                    description=rf"{entry_type} R${entry_value} - {entry_name}",
                    value=entry_tax,
                    tags=[entry_tag, 'taxa', ],
                    account="_paypal_lhc",
                ))
                transactions.append(Transaction(
                    date=entry_date,
                    description=rf"{entry_type} R${entry_value} - {entry_name}",
                    value=entry_value,
                    tags=[entry_tag, ],
                    account="_paypal_lhc",
                ))
            elif entry_type == "Conversão de moeda em geral":
                if entry_currency == "BRL":
                    # Marcio is the only payment in USD
                    transactions.append(Transaction(
                        date=entry_date,
                        description="Mensalidade LHC - USD50 - Marcio Paduan Donadio",
                        value=entry_value,
                        tags=['mensalidade', ],
                        account="_paypal_lhc",
                    ))

    return transactions


if __name__ == "__main__":
    start_date = sys.argv[2] if len(sys.argv) == 3 else None
    # Get CSV report from https://www.paypal.com/reports/statements/monthly
    transactions = get_transactions(sys.argv[1], start_date)
    for transaction in transactions:
        print(transaction)
        post_transaction(transaction)
