import os
import json
import enum
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
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

contract_address = "0xBD108Ad4A73FC569233B122DeC8B6c2a824237F2"
with open("BlackjackABI.json") as f:
    contract_abi = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

SUITS = ["♠️", "♥️", "♦️", "♣️"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
DRAW_STOP_REPLY = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Draw", callback_data="draw")],
        [InlineKeyboardButton("Stop", callback_data="stop")]
    ]
)


#*****************************************************************************#
#   HELPER FUNCTIONS
#*****************************************************************************#

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    # Dictionary mapping callback_data to functions
    functions = {
        "draw": draw,
        "stop": stop,
    }
    
    # Call the appropriate function based on callback_data
    if query.data in functions:
        await functions[query.data](update, context)
    else:
        await query.edit_message_text("Unknown action!")


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



async def manage_endgame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    deck_state = contract.functions.deck_state().call()
    deck = contract.functions.getDeck().call()
    user_cards = [map_index_to_card(deck[index]) for index in range(deck_state) if index != 2]
    user_cards_ranks = [c[1] for c in user_cards]
    user_points = ranks_to_points(user_cards_ranks)
    
    table_cards = [map_index_to_card(deck[2])]
    if user_points > 21:
        msg = await context.bot.send_message(chat_id, text="_You busted! Ending the game\\.\\.\\._", disable_notification=True, parse_mode='MarkdownV2V2')
        tx_hash = contract.functions.endGame().transact(
            {
                "gasPrice": w3.eth.gas_price,
                # "gas": 300_000
            }  
        )
        w3.eth.wait_for_transaction_receipt(tx_hash)

        with open("templates/loose.html", "r") as f:
            await msg.edit_text(
                text=f.read(),
                parse_mode='HTML'
            )

        await context.bot.send_message(format_endgame_str(user_cards, table_cards))

        return
    
    msg = await context.bot.send_message(chat_id, text="_Drawing cards for the table\\.\\.\\._", disable_notification=True, parse_mode="MarkdownV2")

    table_cards_ranks = [c[1] for c in table_cards]
    table_points = ranks_to_points(table_cards_ranks)
    while table_points < 17:
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
        with open("templates/loose.html", "r") as f:
            await msg.edit_text(
                text=f.read(),
                parse_mode='HTML'
            )

        await context.bot.send_message(format_endgame_str(user_cards, table_cards))
    else:
        with open("templates/win.html", "r") as f:
            await msg.edit_text(
                text=f.read(),
                parse_mode='HTML'
            )

        await context.bot.send_message(format_endgame_str(user_cards, table_cards))



# Show cards at the end of the game
def format_endgame_str(user_cards, table_cards) -> str:
    user_cards_str = " | ".join([f"{y[0]} {y[1]}" for y in user_cards])
    table_cards_str = " | ".join([f"{y[0]} {y[1]}" for y in table_cards])

    return f"Your cards\n{user_cards_str}\n\nTable cards\n{table_cards_str}\n"



def format_user_cards_str(user_cards):
    return "Your cards\n" + " | ".join([f"{y[0]} {y[1]}" for y in user_cards])


#*****************************************************************************#
#   COMMAND HANDLERS FUNCTIONS
#*****************************************************************************#


# Hello, just say hello back
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')



# Start a game
async def init(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    # Get user public key
    public_key = update.message.text.lstrip("/init")

    msg = await context.bot.send_message(chat_id, "_Joining game\\.\\.\\._", disable_notification=True, parse_mode="MarkdownV2")

    # Reset smart contract
    tx_hash = contract.functions.resetGame().transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    tx_rcp = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"joined {tx_rcp}")
    # TBD: check tx_rcp outcome (status)

    await msg.edit_text(text="_Joining the game\\.\\.\\._", parse_mode="MarkdownV2")

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

    await msg.edit_text(text="_Starting the game\\.\\.\\._", parse_mode="MarkdownV2")

    tx_hash = contract.functions.startGame().transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    tx_rcp = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"started {tx_rcp}")
    # TBD: check tx_rcp outcome (status)

    await msg.edit_text(text="_Shuffling the deck\\.\\.\\._", parse_mode="MarkdownV2")

    deck = contract.functions.getDeck().call()
    print(f"deck {deck}")

    await msg.edit_text(text="_Dealing the cards\\.\\.\\._", parse_mode="MarkdownV2")
    # Get the first 2 cards and assign to the user
    card1 = map_index_to_card(deck[0])
    card2 = map_index_to_card(deck[1])

    # The third card is the one assigned to the bank
    contract.functions.incDeckState(3).transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )

    await msg.delete()

    # Show the two cards to the user
    await update.message.reply_text(
        text=format_user_cards_str([card1, card2]),
        reply_markup=DRAW_STOP_REPLY
    )



# User asks for one more card
async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id, text="_Drawing a card\\.\\.\\._", disable_notification=True, parse_mode="MarkdownV2")

    print("A01")
    deck_state = contract.functions.deck_state().call()
    print("A02")
    deck = contract.functions.getDeck().call()
    print("A03")

    tx_hash = contract.functions.incDeckState(1).transact(
        {
            "gasPrice": w3.eth.gas_price,
            # "gas": 300_000
        }
    )
    tx_rcp = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"started {tx_rcp}")

    user_cards = [map_index_to_card(deck[index]) for index in range(deck_state + 1) if index != 2]
    user_cards_ranks = [user_card[1] for user_card in user_cards]
    points = ranks_to_points(user_cards_ranks)

    await msg.edit_text(
        text=format_user_cards_str(user_cards),
        reply_markup=DRAW_STOP_REPLY
    )

    if points >= 21:
        await manage_endgame(update, context)


# Stops the game
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await manage_endgame(update, context)
    

#*****************************************************************************#
#   COMMAND HANDLERS DEFINITION
#*****************************************************************************#
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("init", init))
app.add_handler(CommandHandler("draw", draw))
app.add_handler(CommandHandler("stop", stop))

app.add_handler(CallbackQueryHandler(button_callback))

app.run_polling()
