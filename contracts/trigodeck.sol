// SPDX-License-Identifier: MIT
pragma solidity =0.8.24;

import {Subcall} from "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";
import "@oasisprotocol/sapphire-contracts/contracts/Sapphire.sol";
// import "@openzeppelin/contracts/access/Ownable.sol";

/**
    TR-ustless
    I-mplementation for
    G-ambling
    O-nline 
**/

contract Trigo_Deck /* is Ownable */ {

    /**************************************************************************
     * CONF and VARS
     */

    // Internal private storage
    mapping(address => bytes32) private ContractStorage;

    // Determine if contract runs in Remix/HH/Forge or Sapphire
    bool private        mock;

    // Deck: array containing the deck of cards
    uint8[] private     cards;

    // Amount of cards in the deck
    uint8 private       deck_size;
    uint8 public        deck_state;
    
    uint8 public        palyers_count;
    uint8 public        max_players;
    uint8 public        min_players;

    uint  public        hand;
    bytes32[] public    handHashes;

    uint8 public        game_stage;     // 0: initial phase, players can join
                                        // 1: game start, no join, shuffle
                                        // 2: game end 
    bytes21 public      roflAppID;      // 0x001122334455660011223344556600112233445566


    /**************************************************************************
     * EVENTS
     */
    event GameStarted();
    event GameEnded();
    event NewHand(uint hand);
    event PlayerJoined(address player);
    event DeckShuffled();
    event DeckStateUpdated(uint deck_state);
    event StorageSet(address key);

    /**************************************************************************
     * CONSTRUCTOR
     */

    constructor(bytes21 _roflAppID, uint8 _decksize, uint8 _minplayers, uint8 _maxplayers /* , address boss */ ) /* Ownable(boss) */ {
        roflAppID   = _roflAppID;
        // Set deck length
        deck_size   = _decksize;
        // Set game players
        max_players = _maxplayers;
        min_players = _minplayers;
        game_stage  = 0;

        // Are we on the Oasis or some local test etc?
        mock = bool(
            block.chainid != 23294 && // Oasis Sapphire
            block.chainid != 23295 && // Oasis Sapphire Testnet
            block.chainid != 42261 && // Oasis Emerald Testnet
            block.chainid != 42262    // Oasis Emerald
        );

        // Initialize a standard 52-card deck (0–51)
        for (uint8 i = 0; i < deck_size; i++) {
            cards.push(i);
        }
    }

 
    /**************************************************************************
     * USER FUNCTIONS
     */

    /** User Joins game */
    function  joinGame(bytes32 _publicKey) public {
        // Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        require (game_stage == 0, "Sorry your are late" );
        require (palyers_count < max_players, "Max players reached");
        require (ContractStorage[msg.sender] == bytes32(0x00), "Already playing" );
        ContractStorage[msg.sender] = _publicKey;
        palyers_count ++; 

        emit PlayerJoined(msg.sender);
    }

    /**************************************************************************
     * GAME FUNCTIONS
     */

    /** 
     * Start a new game, shuffle deck, start game
     */
    function startGame() external /* onlyOwner */ {
        require (game_stage == 0, "wrong stage for start");
        require (palyers_count >= min_players, "Not enought players");
        // Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        shuffle();
        game_stage = 1;

        emit GameStarted();
    }

    /**
     * New Hand. Shuffle deck again for the same players
     */
    function newHand(bytes32 _deckHash) external /* onlyOwner */ {
        require (game_stage == 1, "wrong stage for new hand");

        bytes32 this_hand_hash = keccak256(abi.encodePacked(cards));
        require (this_hand_hash == _deckHash, "Get the hash before");

        // Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        require (palyers_count >= min_players, "Not enought players");
        shuffle();
        hand++;
        emit NewHand(hand);
    }


    /** 
     * End the game
     */
    function endGame() external /* onlyOwner */ {
        require (game_stage == 1, "wrong stage for end");
        // Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        game_stage == 2;
        emit GameEnded();
    }


    /**************************************************************************
     * DECK FUNCTIONS
     */

    /**
     * Implement the Fisher-Yates Shuffle (aka Knuth shuffle)
     * @dev Shuffles the cards in a 52-card deck.
     */
    function shuffle() internal {
        // Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);

        // Get random number from Sapphire as bytes --> hash
        bytes memory rnd;
        
        if (mock) {
            rnd = abi.encodePacked(
                keccak256(abi.encodePacked(
                    block.timestamp,
                    block.number,
                    msg.sender
                ))
            );
        } else {
            rnd = Sapphire.randomBytes(32, "trigo-deck");
        }
    
        // hash --> uint
        uint256 rndInt = uint256(keccak256(rnd));

        // Perform 52 swaps using indInt as seeduu
        for (uint256 i = deck_size - 1; i > 0; i--) {
            // pseudo-random number generator from the seed 
            rndInt = uint256(keccak256(abi.encodePacked(rndInt, i)));
            uint256 j = rndInt % (i + 1);
            // Swap picked element with the last (non swapped) one
            (cards[i], cards[j]) = (cards[j], cards[i]);
        }

        // This shuffled deck was never read
        deck_state = 0;
        handHashes.push(keccak256(abi.encodePacked(cards)));
        emit DeckShuffled();
        emit DeckStateUpdated(deck_state); 
    }


    // Get the hash of the shuffled deck
    function getDeckHash() external  view returns (bytes32[] memory) {
        return handHashes;
    }

    // Return the whole deck
    function getDeck() external view returns (uint8[] memory) {
        // Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        require (game_stage == 1, "Start game first");
        return cards;
    }


    // Store deck_state = next card to deal to players
    function incDeckState(uint8 _amount) external /* onlyOwner */ {
        // Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);
        require (deck_state + _amount <= deck_size, "Deck size exeeded");
        deck_state+=_amount;
        emit DeckStateUpdated(deck_state);
    }


    /**************************************************************************
     * STORAGE FUNCTIONS (key-value store)
     */

    function setStorage(address _key, bytes32 _value) external /* onlyOwner */ {
        ContractStorage[_key] = _value;
        emit StorageSet(_key);
    }


    function getStorage (address _key) external view /* onlyOwner */ returns (bytes32) {
        return ContractStorage[_key];
    }
}
