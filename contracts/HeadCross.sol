pragma solidity =0.8.24;

import {Subcall} from "@oasisprotocol/sapphire-contracts/contracts/Subcall.sol";
import "@oasisprotocol/sapphire-contracts/contracts/Sapphire.sol";

contract HeadCross {
	bytes21 public roflAppID;

	constructor(bytes21 _roflAppID) {
    	roflAppID = _roflAppID;
	}
	
	function spin() external view returns (bool _result) {
		// Ensure only the authorized ROFL app can submit.
        // Subcall.roflEnsureAuthorizedOrigin(roflAppID);
				
		bytes memory rnd = Sapphire.randomBytes(32, "");
		_result = uint256(keccak256(rnd)) % 2 == 0;
	}		     	       
}
