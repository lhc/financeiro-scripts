import csv
import datetime
import decimal
import httpx


def get_transactions(paypal_csv):
    # TODO I am unable to identify properly USD conversions
    # for now these needs to be inserted manually yet

    transactions = []
    with open(paypal_csv, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            entry_date = row["Data"]
            entry_date = datetime.datetime.strptime(entry_date, "%d/%m/%Y").strftime(
                "%Y-%m-%d"
            )
            entry_description = row["Descrição"]
            entry_currency = row["Moeda"]
            entry_value = row["Bruto "]
            entry_value = decimal.Decimal(entry_value.replace(".", "").replace(",", "."))

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
                        fr"Doação R${entry_value} - {entry_name}",
                    )
                )
                transactions.append(
                    (
                        entry_date,
                        str(entry_tax),
                        "_paypal_lhc",
                        "doacao,taxa",
                        fr"Taxa Doação R${entry_value} - {entry_name}",
                    )
                )
            elif entry_description == "Pagamento de assinaturas":
                if entry_currency == "USD":
                    continue

                mensalidades = (75, 85, 110)
                entry_type = "Mensalidade" if entry_value in mensalidades else "Contribuição"
                entry_tag = "mensalidade" if entry_type == "Mensalidade" else "contribuicao"

                transactions.append(
                    (
                        entry_date,
                        str(entry_value),
                        "_paypal_lhc",
                        entry_tag,
                        fr"{entry_type} R${entry_value} - {entry_name}",
                    )
                )
                transactions.append(
                    (
                        entry_date,
                        str(entry_tax),
                        "_paypal_lhc",
                        f"{entry_tag},taxa",
                        fr"Taxa {entry_type} R${entry_value} - {entry_name}",
                    )
                )

    return transactions


def post_transaction(transaction):
    post_url = "http://beta.lhc.rennerocha.com/new_entry"
    post_data = {
        "entry_date": transaction[0],
        "value": transaction[1],
        "account": transaction[2],
        "tags": transaction[3],
        "description": transaction[4]
    }
    print(f"Processing {post_data}.")
    response = httpx.post(post_url, json=post_data)
    print(response)


if __name__ == '__main__':
    transactions = get_transactions("Paypal_JunhoParcial.csv")
    for transaction in transactions:
        post_transaction(transaction)
