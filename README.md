# Plunger

Tool helping to deal with Ethereum transactions stuck in the pool.

<https://chat.makerdao.com/channel/keeper>


## Rationale

Due to periodic Ethereum network congestion, transactions can easily get stuck in the
transaction pool for many hours if not days. _plunger_ is a tool that helps to deal
with such situations by either overriding them with zero-valued transactions with
higher gas price, or just waiting for them to clear themselves. It also allows you
to list pending transactions for manual inspection.

_plunger_ has been created as part of development of the Maker Keeper Framework.
It is essential to run each keeper from an individual address, which does not
have any pending transactions. That's why before starting each keeper, doing
a `plunger --wait 0x.....` if recommended.

If you want to discuss this tool, the best place will be the _#keeper_ channel
in Maker RocketChat, linked above.


## Installation

This project uses *Python 3.6.2*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/reverendus/plunger.git
pip3 install -r requirements.txt
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
               (--list | --wait | --override-with-zero-txs)
               address

positional arguments:
  address               Ethereum address to operate on

optional arguments:
  -h, --help            show this help message and exit
  --rpc-host RPC_HOST   JSON-RPC host (default: `localhost')
  --rpc-port RPC_PORT   JSON-RPC port (default: `8545')
  --list                List pending transactions
  --wait                Wait for the pending transactions to clear
  --override-with-zero-txs
                        Override the pending transactions with zero-value txs
```

### Listing pending transactions

**TODO This feature is not implemented yet!**

```bash
bin/plunger --list 0x0101010101010101010101010101010101010101
```

### Waiting for pending transactions to clear

If you want _plunger_ to just wait for the pending transactions from the specified address
to get processed by the network (i.e. to get mined), run it with the `--wait` argument:

```bash
bin/plunger --wait 0x0101010101010101010101010101010101010101
```

This is a completely passive mode i.e. no Ethereum transactions get sent by _plunger_
if called with `--wait`.

_Plunger_ will not terminate until all pending transactions get mined. If it for some exceptional
reason (the Ethereum node going down or some other network connectivity issues) terminates earlier
than that, it will return a non-zero return code.

### Overriding pending transactions

**TODO This feature is not implemented yet!**

If you want _plunger_ to try to override all pending transactions with a zero Wei ether transfer
but with gas cost higher than the original, run it with the `--override-with-zero-txs` argument:

```bash
bin/plunger --override-with-zero-txs 0x0101010101010101010101010101010101010101
```

_Plunger_ will send replacement transactions immediately, then it will start monitoring the
network and will not terminate until all pending transactions or their replacements get mined.
**Due to the nature of the Ethereum network, there is no guarantee which transactions will
actually get executed.** It is possible that some of the original stuck ones will actually
get through. You can also get a mix of old and new ones being mined when there is more than
one transaction pending.

If for some exceptional reason (the Ethereum node going down or some other network
connectivity issues) _plunger_ terminates before all pending transactions from the specified
address get mined, it will return a non-zero return code.

The account specified has to be unlocked for _plunger_ to be able to sign and send replacement
transactions. If it's unable to do so, it will terminate immediately with a non-zero return code.

### Gas price

By default, _plunger_ will use the default gas price suggested by the Ethereum node it is
connected to. If that gas price is lower than the one the pending transactions have used,
_pluger_ will increase it by 1 Wei.

**TODO This feature is not implemented yet!** In the future it will be possible to specify
a custom gas price or use a service like _ethgasstation_.

### Pending transactions source

By default, _plunger_ uses _etherscan.io_ to discover pending transactions. In the future
versions it will be also capable of monitoring the transaction pool of the Ethereum node
it is connected to. It will also allow configuring the source i.e. choosing whether
we want to use _etherscan.io_, local transaction pool or both.

Unfortunately, the API exposed by _etherscan.io_ does not give access to pending transactions.
Due to that, integration works by simply scraping their website.


## License

See [COPYING](https://github.com/reverendus/plunger/blob/master/COPYING) file.
