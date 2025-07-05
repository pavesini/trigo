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


w3 = Web3(Web3.HTTPProvider(sapphire.NETWORKS['sapphire-testnet']))
async_w3 = AsyncWeb3(
    AsyncWeb3.AsyncHTTPProvider(
        sapphire.NETWORKS['sapphire-testnet']
    )
)

account: LocalAccount = (
    Account.from_key(  # pylint: disable=no-value-for-parameter
        private_key="0x2a3dd9e39480211379d59d36de7a778c20b47b4f55c383ec92753d268048ee78"
    )
)
w3.middleware_onion.add(SignAndSendRawMiddlewareBuilder.build(account))


w3 = sapphire.wrap(w3, account)
async_w3 = sapphire.wrap(async_w3, account)

contract_address = "0xf3E77ab2D17Cc7C62836eB99DF851AbC83E5BEbb"
with open("BlackjackABI.json") as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)
tx_hash = trigo.constructor().transact({"gasPrice": w3.eth.gas_price})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

trigo = w3.eth.contract(
    address=tx_receipt["contractAddress"], abi=contract_abi
)


SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def map_index_to_card(index: int) -> (str, str):
    suits = index // 13
    ranks = index % 13

    return SUITS[suits], RANKS[ranks]


def ranks_to_points(ranks: list[str]) -> int:
    points = 0
    for r in ranks:
        if r.is_numeric():
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

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')


async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = trigo.functions.spin().call()
    await update.message.reply_text(f'Hello {update.effective_user.first_name}, spin {result}')

async def init(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    public_key = update.message.text.lstrip("/init")
    trigo.functions.joinGame(bytes.fromhex(public_key)).call()
    print("joined")
    trigo.functions.startGame().call()
    print("started")
    deck = trigo.functions.getDeck().call()
    print("deck")
    # Get the first 2 cards and assign to the user
    s1, r1 = map_index_to_card(deck[0])
    s2, r2 = map_index_to_card(deck[1])

    # The third card is the one assigned to the bank
    trigo.functions.incDeckState(3).call()
    
    await update.message.reply_text(f"{s1}{r1}, {s2}{r2}")


def manage_endgame() -> (str, list[(str, str)], list[(str, str)]):
    deck_state = trigo.functions.deck_state().call()
    deck = trigo.functions.getDeck().call()
    user_cards = [map_index_to_card(deck[index]) for index in range(deck_state) if index != 2]
    user_cards_ranks = [c[1] for c in user_cards]
    user_points = ranks_to_points(user_cards_ranks)
    
    table_cards = [deck[2]]
    if user_points > 21:
        # Hai perso
        trigo.functions.endGame().call()
        
        return "Hai perso", user_cards, table_cards
    
    table_points = ranks_to_points(table_cards)
    while table_points < 17:
        table_cards.append(map_index_to_card)

    trigo.functions.incDeckState(len(table_cards) - 1).call()
    trigo.functions.endGame().call()

    if table_points >= user_points:
        # Hai perso
        return "Hai perso", user_cards, table_cards
    else:
        # Hai vinto
        return "Hai vinto", user_cards, table_cards


def format_endgame_str(txt, user_cards, table_cards) -> str:
    user_cards_str = " ".join([f"{y[0]} {y[1]}" for y in user_cards])
    table_cards_str = " ".join([f"{y[0]} {y[1]}" for y in table_cards])

    return f"{txt}\nyour cards: {user_cards_str}\ntable_cards: {table_cards_str}\n"


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    deck_state = trigo.functions.deck_state().call()
    deck = trigo.functions.getDeck().call()
    s1, r1 = map_index_to_card(deck[deck_state])
    trigo.functions.incDeckState(1)
    user_cards_ranks = [map_index_to_card(deck[index])[1] for index in 0..deck_state + 1 if index != 2]
    points = ranks_to_points(user_cards_ranks)
    if points >= 21:

        txt, user_cards, table_cards = manage_endgame()
        await update.message.reply_text(format_endgame_str(txt, user_cards, table_cards))
    else:
        await update.message.reply_text(f"{s1}{r1}")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    txt, user_cards, table_cards = manage_endgame()
    await update.message.reply_text(format_endgame_str(txt, user_cards, table_cards))
    

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("spin", spin))
app.add_handler(CommandHandler("init", init))
app.add_handler(CommandHandler("draw", draw))
app.add_handler(CommandHandler("stop", stop))

app.run_polling()
