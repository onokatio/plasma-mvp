import requests
import rlp
from plasma.child_chain.child_chain import ChildChain
from plasma_core.transaction import Transaction
from plasma_core.block import Block
from .exceptions import ChildChainServiceError


class ChildChainService(object):

    def __init__(self, url):
        self.url = url
        self.methods = [func for func in dir(ChildChain) if callable(getattr(ChildChain, func)) and not func.startswith("__")]

    def send_request(self, method, args):
        payload = {
            "method": method,
            "params": args,
            "jsonrpc": "2.0",
            "id": 0,
        }
        response = requests.post(self.url, json=payload).json()
        if 'error' in response.keys():
            raise ChildChainServiceError(response["error"])

        return response["result"]

    def apply_transaction(self, transaction):
        return self.send_request("apply_transaction", [rlp.encode(transaction, Transaction).hex()])

    def apply_deposit_utxo(self, blknum, txindex, oindex, transaction, gcnum):
        return self.send_request("apply_deposit_utxo", [blknum, txindex, oindex, rlp.encode(transaction, Transaction).hex(), gcnum])

    def submit_block(self, block):
        return self.send_request("submit_block", [rlp.encode(block, Block).hex()])

    def submit_block_utxo(self, block, gcnum):
        return self.send_request("submit_block_utxo", [rlp.encode(block, Block).hex(), gcnum])

    def get_transaction(self, blknum, txindex):
        return self.send_request("get_transaction", [blknum, txindex])

    def get_current_block(self):
        return self.send_request("get_current_block", [])

    def get_block(self, blknum):
        return self.send_request("get_block", [blknum])

    def get_current_block_num(self):
        return self.send_request("get_current_block_num", [])

    def withdraw_utxo(self, blknum, txindex, oindex, tx, proof, sigs, owner, gcnum):
        return self.send_request("withdraw_utxo", [blknum, txindex, oindex, rlp.encode(tx, Transaction).hex(), proof.hex(), sigs.hex(), owner, gcnum])
