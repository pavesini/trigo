# TRustless Implementation for Gambling Online


## Team

Mattia Careddu
Antonio Luca
Simone Barbanti
Marco Crotta

## Project aim and rationale

Can you trust an online gaming/gambling platform? You might but you should not
How can you be sure the game is fair? That the casino is not cheating somehow?
There are just so many ways an online gambling plaform coul cheat, too many to make 
a list.


TR.I.G.O aims to solve this problem by leveraging oasis.network Sapphire platoform

## Solution

Use Oasis TEE and Saphire to ensure no thampering happened on the deck during the game

## Future improvements
- allow multiple tables with a contract fatory
- remove the Casino all together and let the players play P2P


## Example : Black Jack 1 vs 1

- ROFL joins the game
- player joins the game
- ROFL starts the game
- ROFL gives the deck hash to the player
- ROFL gets 4 cards from the deck, gives 2 to the player, keeps to
- player asks for 1 card
- ROFL get card and passes to the player
- might repeat multiple times, or
- player stays
- ROFL computes player scores (might overflow 21)
- ROFL gets the whole remaining deck
- ROFL keeps getting cards until either beats the player or overflows 21
- ROFL passes the whole deck to player
- Player checks that the deck matches the hash received