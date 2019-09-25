import json
import datetime
import base64
from ethereum import utils
from plasma_core.block import Block
from plasma_core.chain import Chain
from plasma_core.utils.transactions import get_deposit_tx, encode_utxo_id
from plasma_core.transaction import Transaction, UnsignedTransaction
from plasma_core.constants import NULL_ADDRESS
from plasma.client.client import Client

class GrandChildChain(object):

    def __init__(self, operator, utxo_contract):
        self.operator = operator
        self.utxo_contract = utxo_contract
        self.chain = Chain(self.operator)
        self.current_block = Block(number=self.chain.next_child_block)
        print("self.current_block {0}".format(self.current_block.number))

    def msgsender(self, event):
        print("msgsender {0}".format(event['args']))

    def apply_exit(self, event):
        event_args = event['args']
        utxo_id = event_args['utxoPos']
        self.chain.mark_utxo_spent(utxo_id)

    def apply_deposit(self, event):
        print("apply deposit {0}".format(event['args']))
        event_args = event['args']
        owner = event_args['depositor']
        amount = event_args['amount']
        blknum = event_args['depositBlock']

        deposit_tx = get_deposit_tx(owner, amount)
        deposit_block = Block([deposit_tx], number=blknum)
        self.chain.add_block(deposit_block)

    def apply_transaction(self, tx):
        print("spent_utxos {0}".format(self.current_block.spent_utxos))
        self.chain.validate_transaction(tx, self.current_block.spent_utxos)
        self.current_block.add_transaction(tx)
        return encode_utxo_id(self.current_block.number, len(self.current_block.transaction_set) - 1, 0)

    def submit_block(self, block):
        self.chain.add_block(block)

        # Submit state update from grand child chain to child chain
        state = []
        state.append(base64.b64encode(block.merkle.root).decode('utf-8'))

        tx = Transaction(4, 0, 0,
                         0, 0, 0,
                         utils.normalize_address(NULL_ADDRESS),
                         utils.normalize_address(self.utxo_contract), 50,
                         utils.normalize_address(NULL_ADDRESS), 0,
                         0x01, json.dumps(state))
        tx.sign1(utils.normalize_key("3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304"))

        client = Client()
        client.apply_transaction(tx)
        print("Sent state update transaction")

        self.current_block = Block(number=self.chain.next_child_block)

    def get_transaction(self, tx_id):
        return self.chain.get_transaction(tx_id)

    def get_block(self, blknum):
        return self.chain.get_block(blknum)

    def get_current_block(self):
        return self.current_block
