import os
import json
import enum
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from web3 import Web3, AsyncWeb3
from web3.middleware import SignAndSendRawMiddlewareBuilder
from eth_account import Account
from eth_account.signers.local import LocalAccount

from sapphirepy import sapphire



#*****************************************************************************#
#   INITIALIZE: Blockchain connection etc
#*****************************************************************************#


w3 = Web3(Web3.HTTPProvider(sapphire.NETWORKS['sapphire-testnet']))
# async_w3 = AsyncWeb3(
#     AsyncWeb3.AsyncHTTPProvider(
#         sapphire.NETWORKS['sapphire-testnet']
#     )
# )

account: LocalAccount = (
    Account.from_key(  # pylint: disable=no-value-for-parameter
        private_key="0x2a3dd9e39480211379d59d36de7a778c20b47b4f55c383ec92753d268048ee78"
    )
)
w3.middleware_onion.add(SignAndSendRawMiddlewareBuilder.build(account))

w3 = sapphire.wrap(w3, account)
w3.eth.default_account = account.address
# async_w3 = sapphire.wrap(async_w3, account)

contract_address = "0x58cf2A13280892872aeAf7663aCCf9D55a122aae"
with open("BlackjackABI.json") as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]



#*****************************************************************************#
#   HELPER FUNCTIONS
#*****************************************************************************#


# Turn card number into playing card
def map_index_to_card(index: int) -> (str, str):
    suits = index // 13
    ranks = index % 13

    return SUITS[suits], RANKS[ranks]



# Computes the points of the cards at hand
def ranks_to_points(ranks: list[str]) -> int:
    points = 0
    for r in ranks:
        if r.isnumeric():
            points += int(r)
        elif r == "A":
            if points + 11 > 21:
                points += 1
            else:
                points += 11
        elif r == "J" or r == "Q" or r == "K":
            points += 10
        else:
            raise ValueError("Not expecred")
    return points



def manage_endgame() -> (str, list[(str, str)], list[(str, str)]):
    deck_state = contract.functions.deck_state().call()
    deck = contract.functions.getDeck().call()
    user_cards = [map_index_to_card(deck[index]) for index in range(deck_state) if index != 2]
    user_cards_ranks = [c[1] for c in user_cards]
    user_points = ranks_to_points(user_cards_ranks)
    
    table_cards = [map_index_to_card(deck[2])]
    if user_points > 21:
        # Hai perso
        tx_hash = contract.functions.endGame().transact(
            {
                "gasPrice": w3.eth.gas_price,
                # "gas": 300_000
            }  
        )
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return "Hai perso", user_cards, table_cards
    
    table_cards_ranks = [c[1] for c in table_cards]
    table_points = ranks_to_points(table_cards_ranks)
    while table_points < 17:
        print(f"table point: {table_points}")
        print(f"table cards: {table_cards}")
        print(f"user cards: {user_cards}")

        table_cards.append(map_index_to_card(deck[len(user_cards) + len(table_cards)]))
        table_cards_ranks = [c[1] for c in table_cards]
        table_points = ranks_to_points(table_cards_ranks)

    tx_hash = contract.functions.incDeckState(len(table_cards) - 1).transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }  
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)
    tx_hash = contract.functions.endGame().transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }  
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)

    if table_points >= user_points:
        # Hai perso
        return "Hai perso", user_cards, table_cards
    else:
        # Hai vinto
        return "Hai vinto", user_cards, table_cards



# Show cards at the end of the game
def format_endgame_str(txt, user_cards, table_cards) -> str:
    user_cards_str = " ".join([f"{y[0]} {y[1]}" for y in user_cards])
    table_cards_str = " ".join([f"{y[0]} {y[1]}" for y in table_cards])

    return f"{txt}\nyour cards: {user_cards_str}\ntable_cards: {table_cards_str}\n"



#*****************************************************************************#
#   COMMAND HANDLERS FUNCTIONS
#*****************************************************************************#


# Hello, just say hello back
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')



# Start a game
async def init(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get user public key
    public_key = update.message.text.lstrip("/init")

    # Reset smart contract
    tx_hash = contract.functions.resetGame(bytes.fromhex(public_key)).transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    tx_rcp = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"joined {tx_rcp}")
    # TBD: check tx_rcp outcome (status)


    # Do joinGame transaction
    tx_hash = contract.functions.joinGame(bytes.fromhex(public_key)).transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    tx_rcp = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"joined {tx_rcp}")
    # TBD: check tx_rcp outcome (status)

    tx_hash = contract.functions.startGame().transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    tx_rcp = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"started {tx_rcp}")
    # TBD: check tx_rcp outcome (status)

    deck = contract.functions.getDeck().call()
    print(f"deck {deck}")
    # Get the first 2 cards and assign to the user
    s1, r1 = map_index_to_card(deck[0])
    s2, r2 = map_index_to_card(deck[1])

    # The third card is the one assigned to the bank
    contract.functions.incDeckState(3).transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    # Show the two cards to the user
    await update.message.reply_text(f"{s1}{r1}, {s2}{r2}")



# User asks for one more card
async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deck_state = contract.functions.deck_state().call()
    deck = contract.functions.getDeck().call()
    s1, r1 = map_index_to_card(deck[deck_state])
    tx_hash = contract.functions.incDeckState(1).transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    tx_rcp = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"started {tx_rcp}")
    # TBD: check tx_rcp outcome (status)

    user_cards_ranks = [map_index_to_card(deck[index])[1] for index in range(deck_state + 1) if index != 2]
    points = ranks_to_points(user_cards_ranks)
    if points >= 21:
        txt, user_cards, table_cards = manage_endgame()
        await update.message.reply_text(format_endgame_str(txt, user_cards, table_cards))
    else:
        await update.message.reply_text(f"{s1}{r1}")



# Stops the game
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    txt, user_cards, table_cards = manage_endgame()
    await update.message.reply_text(format_endgame_str(txt, user_cards, table_cards))
    

#*****************************************************************************#
#   COMMAND HANDLERS DEFINITION
#*****************************************************************************#
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("init", init))
app.add_handler(CommandHandler("draw", draw))
app.add_handler(CommandHandler("stop", stop))

app.run_polling()
