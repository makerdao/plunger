# Plunger

Tool helping to deal with Ethereum transactions stuck in the pool.

[![Build Status](https://travis-ci.org/makerdao/plunger.svg?branch=master)](https://travis-ci.org/makerdao/plunger)
[![codecov](https://codecov.io/gh/makerdao/plunger/branch/master/graph/badge.svg)](https://codecov.io/gh/makerdao/plunger)
[![Code Climate](https://codeclimate.com/github/makerdao/plunger/badges/gpa.svg)](https://codeclimate.com/github/makerdao/plunger)
[![Issue Count](https://codeclimate.com/github/makerdao/plunger/badges/issue_count.svg)](https://codeclimate.com/github/makerdao/plunger)

<https://chat.makerdao.com/channel/keeper>


## Rationale

Due to periodic Ethereum network congestion, transactions can easily get stuck in the
transaction pool for many hours if not days. _plunger_ is a tool that helps to deal
with such situations by either overriding them with zero-valued transactions with
higher gas price, or just waiting for them to clear themselves. It also allows you
to list pending transactions for manual inspection.

_plunger_ has been created during development of the Maker Keeper Framework.
It is essential to run each keeper from an individual address that does not
have any pending transactions. That is why before starting each keeper, doing
a `plunger --source parity_txqueue --wait 0x.....` is recommended.

If you want to discuss this tool, the best place is the _#keeper_ channel
in the Maker RocketChat, linked above.


## Installation

This project uses *Python 3.6.2*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/makerdao/plunger.git
cd plunger
./install.sh
```

### Known macOS issues

In order for the requirements to install correctly on _macOS_, please install
`openssl`, `libtool` and `pkg-config` using [Homebrew](https://brew.sh/):
```
brew install openssl libtool pkg-config
```

and set the `LDFLAGS` environment variable before you run `pip3 install -r requirements.txt`:
```
export LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" 
```


## Usage

```
usage: plunger [-h] [--rpc-host RPC_HOST] [--rpc-port RPC_PORT]
               [--gas-price GAS_PRICE] --source SOURCE
               (--list | --wait | --override-with-zero-txs)
               address

positional arguments:
  address               Ethereum address to check for pending transactions

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --gas-price GAS_PRICE
                        Gas price (in Wei) for overriding transactions
  --source SOURCE       Comma-separated list of sources to use for pending
                        transaction discovery (available: etherscan,
                        parity_txqueue)
  --list                List pending transactions
  --wait                Wait for the pending transactions to clear
  --override-with-zero-txs
                        Override the pending transactions with zero-value txs
  --eth-key ETH_KEY     Ethereum private key to use (e.g.
                        'key_file=aaa.json,pass_file=aaa.pass') for unlocking
                        account
```

### Listing pending transactions

If you want _plunger_ to only list pending transactions originating from the specified address,
call it with the `--list` argument:

```bash
bin/plunger --source etherscan,parity_txqueue --list 0x0101010101010101010101010101010101010101
```

### Waiting for pending transactions to clear

If you want _plunger_ to just wait for the pending transactions from the specified address
to get processed by the network (i.e. to get mined), run it with the `--wait` argument:

```bash
bin/plunger --source etherscan,parity_txqueue --wait 0x0101010101010101010101010101010101010101
```

This is a completely passive mode i.e. no Ethereum transactions get sent by _plunger_
if called with `--wait`.

_Plunger_ will not terminate until all pending transactions get mined. If it for some exceptional
reason (the Ethereum node going down or some other network connectivity issues) terminates earlier
than that, it will return a non-zero exit code.

### Overriding pending transactions

If you want _plunger_ to try to override all pending transactions with a zero Wei ether transfer
but with gas cost higher than the original, run it with the `--override-with-zero-txs` argument:

```bash
bin/plunger --source etherscan,parity_txqueue --override-with-zero-txs 0x0101010101010101010101010101010101010101
```

_Plunger_ will send replacement transactions immediately, then it will start monitoring the
network and will not terminate until all pending transactions or their replacements get mined.
**Due to the nature of the Ethereum network, there is no guarantee which transactions will
actually get executed.** It is possible that some of the original stuck ones will actually
get through. You can also get a mix of old and new ones being mined when there is more than
one transaction pending.

If for some exceptional reason (the Ethereum node going down or some other network
connectivity issues) _plunger_ terminates before all pending transactions from the specified
address get mined, it will return a non-zero exit code.

The account specified has to be unlocked for _plunger_ to be able to sign and send replacement
transactions; use `--eth-key` parameter to unlock the account.

### Gas price

Gas price for overriding transactions can be specified using the `--gas-price` argument.
If this argument is not present, _plunger_ will use the default gas price suggested by
the Ethereum node it is connected to.

Bear in mind that the new gas price has to be at least 10% higher than the original one,
otherwise Parity will not even accept such a replacement transaction. If it happens, _plunger_
will display an error message but will still wait for the pending transactions to get mined
as it is still possible the original one will go through. 

### Pending transactions discovery

The `--source` argument has to be used to specify how _plunger_ should discover pending transactions.
Currently it can either query _etherscan.io_ (`--source etherscan`) or look for them in the Parity
transaction queue (`--source parity_txqueue`). Bear in mind that it is a custom _Parity_ RPC endpoint
and so this latter method will not work with _geth_.

Both discovery methods can be used at the same time (`--source etherscan,parity_txqueue`).

The _etherscan.io_ integration works by scraping their website as the API exposed by them
does not give access to pending transactions.


## Testing

### Automated testing

A unit-test harness is present for testing almost all _plunger_ features. It can be run
with the `./test.sh` script, preceded by installing necessary dependencies with
`pip3 install -r requirements-dev.txt`.

### Manual testing

The following commands can be used to manually test _plunger_. The first two commands
send 1 Wei transfers with a pretty low gas price of 0.5 GWei, so they won't instantly
get mined and will very likely get stuck. The third command runs _plunger_ using the same
account, so if everything works correctly we can see these two transactions being plunged.

```
export ETH_FROM=0x001.......

seth send --async --gas-price=500000000 --value=1 -F $ETH_FROM $ETH_FROM
seth send --async --gas-price=500000000 --value=1 -F $ETH_FROM $ETH_FROM

bin/plunger --source parity_txqueue --override-with-zero-txs $ETH_FROM
```

The above snippet uses `seth` (see <https://github.com/dapphub/dapptools/tree/master/src/seth>) for sending transactions.


## License

See [COPYING](https://github.com/makerdao/plunger/blob/master/COPYING) file.
