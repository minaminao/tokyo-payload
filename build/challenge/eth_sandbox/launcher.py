import hashlib
import json
import os
import random
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from uuid import UUID

import requests
from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_sandbox import get_shared_secret
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt

HTTP_PORT = os.getenv("HTTP_PORT", "8545")
PUBLIC_IP = os.getenv("PUBLIC_IP", "127.0.0.1")

CHALLENGE_ID = os.getenv("CHALLENGE_ID", "challenge")
ENV = os.getenv("ENV", "dev")
FLAG = os.getenv("FLAG", "FLAG{placeholder}")

Account.enable_unaudited_hdwallet_features()


def check_uuid(uuid) -> bool:
    try:
        UUID(uuid)
        return uuid
    except (TypeError, ValueError):
        return None


@dataclass
class Action:
    name: str
    handler: Callable[[], int]


def send_transaction(web3: Web3, tx: Dict) -> Optional[TxReceipt]:
    if "gas" not in tx:
        tx["gas"] = 10_000_000

    if "gasPrice" not in tx:
        tx["gasPrice"] = 0

    # web3.provider.make_request("anvil_impersonateAccount", [tx["from"]])
    txhash = web3.eth.send_transaction(tx)
    # web3.provider.make_request("anvil_stopImpersonatingAccount", [tx["from"]])

    while True:
        try:
            rcpt = web3.eth.get_transaction_receipt(txhash)
            break
        except TransactionNotFound:
            time.sleep(0.1)

    if rcpt.status != 1:
        raise Exception("failed to send transaction")

    return rcpt


def new_launch_instance_action(
    do_deploy: Callable[[Web3, str], str],
):
    def action() -> int:
        pow_request()

        data = requests.post(
            f"http://127.0.0.1:{HTTP_PORT}/new",
            headers={
                "Authorization": f"Bearer {get_shared_secret()}",
                "Content-Type": "application/json",
            },
        ).json()

        if data["ok"] == False:
            print(data["message"])
            return 1

        uuid = data["uuid"]
        mnemonic = data["mnemonic"]

        deployer_acct: LocalAccount = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/0")
        player_acct: LocalAccount = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/1")

        web3 = Web3(
            Web3.HTTPProvider(
                f"http://127.0.0.1:{HTTP_PORT}/{uuid}",
                request_kwargs={
                    "headers": {
                        "Authorization": f"Bearer {get_shared_secret()}",
                        "Content-Type": "application/json",
                    },
                },
            )
        )

        setup_addr = do_deploy(web3, deployer_acct.address, player_acct.address)

        with open(f"/tmp/{uuid}", "w") as f:
            f.write(
                json.dumps(
                    {
                        "uuid": uuid,
                        "mnemonic": mnemonic,
                        "address": setup_addr,
                    }
                )
            )

        print()
        print(f"your private blockchain has been deployed")
        print(f"it will automatically terminate in 30 minutes")
        print(f"here's some useful information")
        print(f"uuid:           {uuid}")
        print(f"rpc endpoint:   http://{PUBLIC_IP}:{HTTP_PORT}/{uuid}")
        print(f"private key:    {player_acct.key.hex()}")
        print(f"your address:   {player_acct.address}")
        print(f"setup contract: {setup_addr}")
        return 0

    return Action(name="launch new instance", handler=action)


def new_kill_instance_action():
    def action() -> int:
        try:
            uuid = check_uuid(input("uuid please: "))
            if not uuid:
                print("invalid uuid!")
                return 1
        except Exception as e:
            print(f"Error with UUID: {e}")
            return 1

        data = requests.post(
            f"http://127.0.0.1:{HTTP_PORT}/kill",
            headers={
                "Authorization": f"Bearer {get_shared_secret()}",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "uuid": uuid,
                }
            ),
        ).json()

        print(data["message"])
        return 1

    return Action(name="kill instance", handler=action)


def is_solved_checker(web3: Web3, addr: str) -> bool:
    result = web3.eth.call(
        {
            "to": addr,
            "data": web3.keccak(text="isSolved()")[:4],
        }
    )
    return int(result.hex(), 16) == 1


def new_get_flag_action(
    checker: Callable[[Web3, str], bool] = is_solved_checker,
):
    def action() -> int:
        try:
            uuid = check_uuid(input("uuid please: "))
            if not uuid:
                print("invalid uuid!")
                return 1
        except Exception as e:
            print(f"Error with UUID: {e}")
            return 1

        try:
            with open(f"/tmp/{uuid}", "r") as f:
                data = json.loads(f.read())
        except:
            print("bad uuid")
            return 1

        web3 = Web3(Web3.HTTPProvider(f"http://127.0.0.1:{HTTP_PORT}/{data['uuid']}"))

        try:
            if not checker(web3, data["address"]):
                print("are you sure you solved it?")
                return 1
        except Exception as e:
            print(f"Error with checker: {e}")
            return 1

        print()
        print("Congratulations! You have solve it! Here's the flag: ")
        print(FLAG)
        return 0

    return Action(name="get flag", handler=action)


def pow_request() -> bool:
    SOLVE_POW_PY_URL = "https://minaminao.github.io/tools/solve-pow.py"
    preimage_prefix = hex(random.randint(0, 1 << 64))[2:]
    BITS = 23

    print()
    print("== PoW ==")
    print(f'  sha256("{preimage_prefix}" + YOUR_INPUT) must start with {BITS} zeros in binary representation')
    print(f"  please run the following command to solve it:")
    print(f"    python3 <(curl -sSL {SOLVE_POW_PY_URL}) {preimage_prefix} {BITS}")
    print()
    your_input = input("  YOUR_INPUT = ")
    print()
    if len(your_input) > 0x100:
        print("  your_input must be less than 256 bytes")
        exit(1)

    digest = hashlib.sha256((preimage_prefix + your_input).encode()).digest()
    digest_int = int.from_bytes(digest, "big")
    print(f'  sha256("{preimage_prefix + your_input}") = {digest.hex()}')
    if digest_int < (1 << (256 - BITS)):
        print("  correct")
    else:
        print("  incorrect")
        exit(1)
    print("== END POW ==")


def run_launcher(actions: List[Action]):
    for i, action in enumerate(actions):
        print(f"{i+1} - {action.name}")

    action = int(input("action? ")) - 1
    if action < 0 or action >= len(actions):
        print("can you not")
        exit(1)

    exit(actions[action].handler())
