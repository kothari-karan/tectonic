import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying TectonicEscrow with account:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");

  const TectonicEscrow = await ethers.getContractFactory("TectonicEscrow");
  const escrow = await TectonicEscrow.deploy();
  await escrow.waitForDeployment();

  const deployedAddress = await escrow.getAddress();
  console.log("TectonicEscrow deployed to:", deployedAddress);
  console.log(
    "Explorer link: https://sepolia.etherscan.io/address/" + deployedAddress
  );

  // Write deployment info to deployments/sepolia.json
  const deploymentsDir = path.resolve(__dirname, "../deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  const deploymentData = {
    contract: "TectonicEscrow",
    address: deployedAddress,
    deployer: deployer.address,
    network: "sepolia",
    timestamp: new Date().toISOString(),
  };

  fs.writeFileSync(
    path.join(deploymentsDir, "sepolia.json"),
    JSON.stringify(deploymentData, null, 2)
  );

  console.log("Deployment info written to deployments/sepolia.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
