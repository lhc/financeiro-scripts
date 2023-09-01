import httpx


def post_transaction(transaction):
    post_url = "http://beta.lhc.rennerocha.com/new_entry"
    post_data = {
        "entry_date": transaction[0],
        "value": transaction[1],
        "account": transaction[2],
        "tags": transaction[3],
        "description": transaction[4],
    }
    print(f"Processing {post_data}.")
    response = httpx.post(post_url, json=post_data)
    print(response)
