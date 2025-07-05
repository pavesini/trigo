import { task } from "hardhat/config";
import { bech32 } from "bech32";

task("deploy").setAction(async (_args, hre) => {
  const HeadCross = await hre.ethers.getContractFactory("Trigo_Deck");
  const {prefix, words} = bech32.decode("rofl1qrtzya9kqh67ecv5pngs0xvx5cnt8c5exuc9vfts");
  const rawAppID = new Uint8Array(bech32.fromWords(words));
  const headcross = await HeadCross.deploy(rawAppID);
  const headcrossAddr = await headcross.waitForDeployment();

  console.log(`Trigo_Deck address: ${headcrossAddr.target}`);
  return headcrossAddr.target;
});


task("deploy-trigodeck").setAction(async (_args, hre) => {
  await hre.run("compile");

  const address = await hre.run("deploy");
});
