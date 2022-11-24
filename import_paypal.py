import csv
import datetime
import decimal
import sys
import logging

from utils import post_transaction

logger = logging.getLogger(__name__)


def get_transactions(paypal_csv, start_date):
    # TODO I am unable to identify properly USD conversions
    # for now these needs to be inserted manually yet
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

            entry_date = entry_date.strftime("%Y-%m-%d")
            entry_description = row["Descrição"]
            entry_currency = row["Moeda"]
            entry_value = row["Bruto "]
            entry_value = decimal.Decimal(
                entry_value.replace(".", "").replace(",", ".")
            )

            entry_tax = row["Tarifa "]
            entry_tax = decimal.Decimal(entry_tax.replace(".", "").replace(",", "."))

            entry_name = row["Nome"]
            if entry_description == "Retirada geral - Conta bancária":
                transactions.append(
                    (
                        entry_date,
                        str(entry_value),
                        "_paypal_lhc",
                        "transferencia",
                        "Transferência Paypal -> Conta Corrente",
                    )
                )
                transactions.append(
                    (
                        entry_date,
                        str(-1 * entry_value),
                        "_bradesco",
                        "transferencia",
                        "Transferência Paypal -> Conta Corrente",
                    )
                )
            elif entry_description == "Pagamento de doação":
                transactions.append(
                    (
                        entry_date,
                        str(entry_value),
                        "_paypal_lhc",
                        "doacao",
                        rf"Doação R${entry_value} - {entry_name}",
                    )
                )
                transactions.append(
                    (
                        entry_date,
                        str(entry_tax),
                        "_paypal_lhc",
                        "doacao,taxa",
                        rf"Taxa Doação R${entry_value} - {entry_name}",
                    )
                )
            elif entry_description == "Pagamento de assinaturas":
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

                transactions.append(
                    (
                        entry_date,
                        str(entry_value),
                        "_paypal_lhc",
                        entry_tag,
                        rf"{entry_type} R${entry_value} - {entry_name}",
                    )
                )
                transactions.append(
                    (
                        entry_date,
                        str(entry_tax),
                        "_paypal_lhc",
                        f"{entry_tag},taxa",
                        rf"Taxa {entry_type} R${entry_value} - {entry_name}",
                    )
                )

    return transactions


if __name__ == "__main__":
    start_date = sys.argv[2] if len(sys.argv) == 3 else None
    # Get CSV report from https://www.paypal.com/reports/statements/monthly
    transactions = get_transactions(sys.argv[1], start_date)
    for transaction in transactions:
        print(transaction)
        post_transaction(transaction)
