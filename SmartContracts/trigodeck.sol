// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@oasisprotocol/sapphire-contracts/contracts/Sapphire.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
    TR-ustless
    I-mplementation for
    G-ambling
    O-nline 
**/

contract Trigo_Deck {
    // Deck: array containing the deck of cards
    uint8[] private cards;

    // Amount of cards in the deck
    uint8 private   deck_lenght;
    uint8 public    dealed;
    
    uint8 public    palyers_count;
    uint8 public    max_players;
    uint8 public    min_players;

    constructor(uint[8] _decksize, uint8 _minplayers, uint8 _maxplayers ) Ownable {
        // Set deck length
        deck_lenght = _decksize;
        // Seg game players
        max_players = _maxplayers;
        min_players = _minplayers;

        // Initialize a standard 52-card deck (0–51)
        for (uint8 i = 0; i < deck_lenght; i++) {
            cards.push(i);
        }
    }



    /** User functions */
    function  joinGame() payable {
        require (palyers_count < max_players, 'max players reached');
        palyers_count ++; 
    }


    /** Game functions */
    function startGame() external onyOwner {
        require (palyers_count == max_players, 'Not enought players');
    }


    function endGame() external onyOwner {}




    /**
    * Implement the Fisher-Yates Shuffle (aka Knuth shuffle)
    * @dev Shuffles the cards in a 52-card deck.
    **/
    function shuffle() external onlyOwner{
        // Get random number from Sapphire as bytes --> hash
        bytes memory rnd = Sapphire.randomBytes(32, "trigo-deck");
        
        // MOCK: 
        // bytes memory rnd = abi.encodePacked(
        //     keccak256(abi.encodePacked(
        //         block.timestamp,
        //         block.number,
        //         msg.sender
        //     ))
        // );
    
        // hash --> uint
        uint256 rndInt = uint256(keccak256(rnd));

        // Perform 52 swaps using indInt as seed
        for (uint256 i = deck_lenght - 1; i > 0; i--) {
            // pseudo-random number generator from the seed 
            rndInt = uint256(keccak256(abi.encodePacked(rndInt, i)));
            uint256 j = rndInt % (i + 1);
            // Swap picked element with the last (non swapped) one
            (cards[i], cards[j]) = (cards[j], cards[i]);
        }

        // Start again from the first card
        dealed = 0;
    }

    // Get the hash of the shuffled deck
    function getDeckHash() external view returns (bytes32) {
        return keccak256(abi.encodePacked(cards));
    }

    // Return the whole deck
    function getDeck() external view returns (uint8[] memory) {
        return cards;
    }

    // Get the next card from the deck
    function getNextCard() external view returns(uint8){
        require (dealed < deck_lenght, "Index out of range");
        return cards[dealed++];
    }
}