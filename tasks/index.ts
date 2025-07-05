import { task } from "hardhat/config";
import { bech32 } from "bech32";

task("deploy").setAction(async (_args, hre) => {
  const TrigoDeck = await hre.ethers.getContractFactory("Trigo_Deck");
  const {prefix, words} = bech32.decode("rofl1qpe75zg7qpee95rwr95hphxyazr58qfk9yq5ngxk");
  const rawAppID = new Uint8Array(bech32.fromWords(words));
  const min_number_players = 1
  const max_number_players = 1
  const deck_size = 52;
  const trigo_deck = await  TrigoDeck.deploy(rawAppID, deck_size, min_number_players, max_number_players);
  const trigo_deck_addrs = await trigo_deck.waitForDeployment();

  console.log(`Trigo_Deck address: ${trigo_deck_addrs.target}`);
  return trigo_deck_addrs.target;
});


task("deploy-trigodeck").setAction(async (_args, hre) => {
  await hre.run("compile");

  const address = await hre.run("deploy");
});

