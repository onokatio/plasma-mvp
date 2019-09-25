import click
from ethereum import utils
from plasma_core.constants import NULL_ADDRESS, NULL_BYTE
from plasma_core.transaction import Transaction
from plasma_core.utils.utils import confirm_tx
from plasma_core.utils.transactions import encode_utxo_id
from plasma.client.client import Client
from plasma.client.exceptions import ChildChainServiceError


CONTEXT_SETTINGS = dict(
    help_option_names=['-h', '--help']
)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--gc', is_flag=True, help='Call grandchild chain')
@click.option('--gcnum', default=0, help='Plasma chain block number which is grand child chain contract.')
@click.pass_context
def cli(ctx, gc, gcnum):
    ctx.obj = {}
    ctx.obj['gc'] = gc
    ctx.obj['gcnum'] = gcnum
    if gc:
        ctx.obj['client'] = Client(child_chain_url="http://localhost:8547/jsonrpc")
        print("cli is now grandchild mode")
    else:
        ctx.obj = Client()


def client_call(fn, argz=(), successmessage=""):
    try:
        output = fn(*argz)
        if successmessage:
            print(successmessage)
        return output
    except ChildChainServiceError as err:
        print("Error:", err)
        print("additional details can be found from the child chain's server output")


@cli.command()
@click.argument('amount', required=True, type=int)
@click.argument('address', required=True)
@click.pass_obj
def deposit(obj, amount, address):
    client = obj['client']
    client.deposit(amount, address)
    print("Deposited {0} to {1}".format(amount, address))


@cli.command()
@click.argument('blknum1', type=int)
@click.argument('txindex1', type=int)
@click.argument('oindex1', type=int)
@click.argument('blknum2', type=int)
@click.argument('txindex2', type=int)
@click.argument('oindex2', type=int)
@click.argument('cur12', default="0x0")
@click.argument('newowner1')
@click.argument('amount1', type=int)
@click.argument('newowner2')
@click.argument('amount2', type=int)
@click.argument('key1')
@click.argument('key2', required=False)
@click.argument('contractflag', required=False)
@click.argument('state', required=False)
@click.pass_obj
def sendtx(obj,
           blknum1, txindex1, oindex1,
           blknum2, txindex2, oindex2,
           cur12,
           newowner1, amount1,
           newowner2, amount2,
           key1, key2,
           contractflag, state):
    client = obj['client']
    if cur12 == "0x0":
        cur12 = NULL_ADDRESS
    if newowner1 == "0x0":
        newowner1 = NULL_ADDRESS
    if newowner2 == "0x0":
        newowner2 = NULL_ADDRESS
    if contractflag == "0x0":
        contractflag = 0
    if state == "0x0":
        state = NULL_BYTE

    print("newowner1 {0}".format(newowner1))
    print("amount1 {0}".format(amount1))
    tx = Transaction(blknum1, txindex1, oindex1,
                     blknum2, txindex2, oindex2,
                     utils.normalize_address(cur12),
                     utils.normalize_address(newowner1), amount1,
                     utils.normalize_address(newowner2), amount2,
                     contractflag, state)

    # Sign it
    if key1:
        tx.sign1(utils.normalize_key(key1))
    if key2:
        tx.sign2(utils.normalize_key(key2))

    client_call(client.apply_transaction, [tx], "Sent transaction")


@cli.command()
@click.argument('key', required=True)
@click.pass_obj
def submitblock(obj, key):

    client = obj['client']
    # Get the current block, already decoded by client
    block = client_call(client.get_current_block)
    print("block number {0}".format(block.number))
    # Sign the block
    block.make_mutable()
    normalized_key = utils.normalize_key(key)
    block.sign(normalized_key)

    if obj['gc']:
        client_call(client.submit_block_utxo, [block,obj['gcnum']], "Submitted current block to UTXO contract")
    else:
        client_call(client.submit_block, [block], "Submitted current block")


@cli.command()
@click.argument('blknum', required=True, type=int)
@click.argument('txindex', required=True, type=int)
@click.argument('oindex', required=True, type=int)
@click.argument('key1')
@click.argument('key2', required=False)
@click.pass_obj
def withdraw(obj,
             blknum, txindex, oindex,
             key1, key2):

    client = obj['client']
    # Get the transaction's block, already decoded by client
    block = client_call(client.get_block, [blknum])

    # Create a Merkle proof
    tx = block.transaction_set[txindex]
    proof = block.merkle.create_membership_proof(tx.merkle_hash)

    # Create the confirmation signatures
    confirmSig1, confirmSig2 = b'', b''
    if key1:
        confirmSig1 = confirm_tx(tx, block.merkle.root, utils.normalize_key(key1))
    if key2:
        confirmSig2 = confirm_tx(tx, block.merkle.root, utils.normalize_key(key2))
    sigs = tx.sig1 + tx.sig2 + confirmSig1 + confirmSig2

    client.withdraw(blknum, txindex, oindex, tx, proof, sigs)
    print("Submitted withdrawal")


@cli.command()
@click.argument('owner', required=True)
@click.argument('blknum', required=True, type=int)
@click.argument('amount', required=True, type=int)
@click.pass_obj
def withdrawdeposit(obj, owner, blknum, amount):
    client = obj['client']
    deposit_pos = encode_utxo_id(blknum, 0, 0)
    client.withdraw_deposit(owner, deposit_pos, amount)
    print("Submitted withdrawal")


@cli.command()
@click.argument('account', required=True)
@click.pass_obj
def finalize_exits(obj, account):
    client = obj['client']
    client.finalize_exits(account)
    print("Submitted finalizeExits")


@cli.command()
@click.argument('blknum', required=True, type=int)
@click.argument('key', required=True)
@click.pass_obj
def confirm_sig(obj, blknum, key):
    client = obj['client']
    block = client_call(client.get_block, [blknum])
    tx = client_call(client.get_transaction, [blknum, 0])
    _key = utils.normalize_key(key)
    confirmSig = confirm_tx(tx, block.root, _key)
    print("confirm sig:", utils.encode_hex(confirmSig))


@cli.command()
@click.argument('blknum', required=True, type=int)
@click.argument('txindex', required=True, type=int)
@click.argument('oindex', required=True, type=int)
@click.argument('confirm_sig_hex', required=True)
@click.argument('account', required=True)
@click.pass_obj
def challenge_exit(obj, blknum, txindex, oindex, confirm_sig_hex, account):
    client = obj['client']
    confirmSig = utils.decode_hex(confirm_sig_hex)
    client.challenge_exit(blknum, txindex, oindex, confirmSig, account)
    print("Submitted challenge exit")


if __name__ == '__main__':
    cli()
