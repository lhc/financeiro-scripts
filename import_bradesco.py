import datetime
import re

from utils import post_transaction


IGNORED_ENTRIES = [
    "SALDO ANTERIOR",
    "RESGATE INVEST FACIL",
    "APLIC.INVEST FACIL",
    "TED-TRANSF ELET DISPON REMET.PAYPAL DO BRASIL SER",
]

TAG_MAP = [
    (r"TRANSFERENCIA PIX REMT: ELITON P CRUVINEL", "mensalidade"),
    (r"CONTADOR", "contador"),
    (r"Max Empresarial", "banco"),
    (r"COBRANCA ALUGUEL", "aluguel"),
    (r"SANASA\/CAMPINAS", "sanasa"),
    (r"CPFL PAULISTA", "cpfl"),
    (r"CONTA DE TELEFONE VIVO", "vivo"),
    (r"TRANSF PGTO PIX TARIFA BANCARIA", "banco"),
    (r"TARIFA BANCARIA TRANSF PGTO PIX", "banco"),
    (r"PAGTO ELETRONICO TRIBUTO", "impostos"),
]


def get_transactions(bradesco_csv):
    transactions = []
    with open(bradesco_csv, "r", encoding="iso-8859-1") as csvfile:
        for row in csvfile.readlines():
            if re.search(r"\d{2}\/\d{2}\/\d{4}", row):
                entry = row.split(";")

                entry_description = entry[1]
                if entry_description in IGNORED_ENTRIES:
                    continue
                entry_date = datetime.datetime.strptime(entry[0], "%d/%m/%Y").strftime(
                    "%Y-%m-%d"
                )

                entry_value = entry[3] if entry[3] else entry[4]
                entry_value = entry_value.replace(".", "").replace(",", ".")

                tags = None
                for regex, tag in TAG_MAP:
                    if re.search(regex, entry_description):
                        tags = tag
                        break

                if tags is None:
                    tags = input(f"Tags for {entry_description} - R${entry_value}:")
                    entry_description = (
                        input(f"Alterar '{entry_description}' para: ")
                        or entry_description
                    )

                transactions.append(
                    (
                        entry_date,
                        str(entry_value),
                        "_bradesco",
                        tags,
                        entry_description,
                    )
                )

            if row.startswith("Total"):
                # End of section that contains the entries for the month
                break

    return transactions


if __name__ == "__main__":
    transactions = get_transactions("csv/Bradesco_Junho.CSV")
    for transaction in transactions:
        post_transaction(transaction)
