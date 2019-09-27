from ethereum import utils
from ethereum.utils import sha3
from plasma_core.block import Block
from plasma_core.chain import Chain
from plasma_core.constants import NULL_ADDRESS
from plasma_core.transaction import Transaction
from plasma_core.utils.transactions import get_deposit_tx, encode_utxo_id
from .root_event_listener import RootEventListener


class ChildChain(object):

    def __init__(self, operator, root_chain):
        self.operator = operator
        self.root_chain = root_chain
        self.chain = Chain(self.operator)
        self.current_block = Block(number=self.chain.next_child_block)
        print("self.current_block {0}".format(self.current_block.number))
        # Listen for events
        self.event_listener = RootEventListener(root_chain, confirmations=0)
        self.event_listener.on('Deposit', self.apply_deposit)
        self.event_listener.on('ExitStarted', self.apply_exit)
        self.event_listener.on('Msgsender', self.msgsender)

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
        print("transaction applyed.")
        print("input1: ", tx.blknum1, tx.txindex1, tx.oindex1)
        print("input2: ", tx.blknum2, tx.txindex2, tx.oindex2)
        print("newowner1: ", utils.decode_hex(tx.newowner1), tx.amount1)
        print("newowner2: ", utils.decode_hex(tx.newowner2), tx.amount2)
        print("contractFlag, state: ", tx.contractFlag, tx.state)
        print("spent_utxos {0}".format(self.current_block.spent_utxos))
        self.chain.validate_transaction(tx, self.current_block.spent_utxos)
        self.current_block.add_transaction(tx)
        return encode_utxo_id(self.current_block.number, len(self.current_block.transaction_set) - 1, 0)

    def submit_block(self, block):
        self.chain.add_block(block)
        self.root_chain.transact({
            'from': self.operator
        }).submitBlock(block.merkle.root)
        self.current_block = Block(number=self.chain.next_child_block)

    def get_transaction(self, tx_id):
        return self.chain.get_transaction(tx_id)

    def get_block(self, blknum):
        return self.chain.get_block(blknum)

    def get_current_block(self):
        return self.current_block

    def withdraw_utxo(self, blknum, txindex, oindex, tx, proof, sigs, owner, gcnum):
        # TODO: check merkle proof

        state_string = self.get_block(gcnum).transaction_set[0].state
        contract_balance = self.get_block(gcnum).transaction_set[0].amount1

        tx = Transaction(gcnum, 0, 0,
                         0, 0, 0,
                         utils.normalize_address(NULL_ADDRESS),
                         utils.normalize_address("0xfd02EcEE62797e75D86BCff1642EB0844afB28c7"), 0,
                         utils.normalize_address(owner), contract_balance,
                         0x01, state_string)
        tx.sign1(utils.normalize_key("3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304"))

        self.apply_transaction(tx)
