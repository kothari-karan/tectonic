import { expect } from "chai";
import { ethers } from "hardhat";
import { loadFixture, time } from "@nomicfoundation/hardhat-toolbox/network-helpers";
import { TectonicEscrow } from "../typechain-types";

describe("TectonicEscrow", function () {
  // -------------------------------------------------------------------
  // Fixture
  // -------------------------------------------------------------------

  async function deployFixture() {
    const [admin, poster, solver, outsider] = await ethers.getSigners();

    const Factory = await ethers.getContractFactory("TectonicEscrow", admin);
    const escrow = await Factory.deploy();
    await escrow.waitForDeployment();

    const escrowId = ethers.keccak256(ethers.toUtf8Bytes("escrow-1"));
    const termsHash = ethers.keccak256(ethers.toUtf8Bytes("terms-v1"));
    const fundAmount = ethers.parseEther("1");
    const latestTime = await time.latest();
    const deadline = latestTime + 3600; // 1 hour from now

    return {
      escrow,
      admin,
      poster,
      solver,
      outsider,
      escrowId,
      termsHash,
      fundAmount,
      deadline,
    };
  }

  /**
   * Helper: create and fund an escrow using the poster signer.
   */
  async function createEscrow(
    escrow: TectonicEscrow,
    poster: any,
    escrowId: string,
    solver: string,
    termsHash: string,
    deadline: number,
    fundAmount: bigint
  ) {
    return escrow
      .connect(poster)
      .createAndFund(escrowId, solver, termsHash, deadline, {
        value: fundAmount,
      });
  }

  // -------------------------------------------------------------------
  // Happy Path
  // -------------------------------------------------------------------

  describe("Happy Path", function () {
    it("should create and fund an escrow", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      const tx = await createEscrow(
        escrow,
        poster,
        escrowId,
        solver.address,
        termsHash,
        deadline,
        fundAmount
      );

      // Verify event
      await expect(tx)
        .to.emit(escrow, "EscrowCreated")
        .withArgs(escrowId, poster.address, solver.address, fundAmount, termsHash, deadline);

      // Verify state
      const e = await escrow.getEscrow(escrowId);
      expect(e.poster).to.equal(poster.address);
      expect(e.solver).to.equal(solver.address);
      expect(e.amount).to.equal(fundAmount);
      expect(e.termsHash).to.equal(termsHash);
      expect(e.deadline).to.equal(deadline);
      expect(e.status).to.equal(1); // Funded

      // Verify contract balance
      const bal = await ethers.provider.getBalance(await escrow.getAddress());
      expect(bal).to.equal(fundAmount);
    });

    it("should allow solver to submit delivery", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      const tx = await escrow.connect(solver).submitDelivery(escrowId);

      await expect(tx).to.emit(escrow, "DeliverySubmitted").withArgs(escrowId);

      const e = await escrow.getEscrow(escrowId);
      expect(e.status).to.equal(2); // DeliverySubmitted
    });

    it("should allow poster to confirm delivery and pay solver", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      const tx = await escrow.connect(poster).confirmDelivery(escrowId);

      await expect(tx)
        .to.emit(escrow, "DeliveryConfirmed")
        .withArgs(escrowId, solver.address, fundAmount);

      // Verify solver received funds
      await expect(tx).to.changeEtherBalances(
        [solver, escrow],
        [fundAmount, -fundAmount]
      );

      const e = await escrow.getEscrow(escrowId);
      expect(e.status).to.equal(3); // Confirmed
    });

    it("full lifecycle: create -> deliver -> confirm -> verify balances", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      // Create
      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      const solverBalBefore = await ethers.provider.getBalance(solver.address);

      // Deliver
      await escrow.connect(solver).submitDelivery(escrowId);

      // Confirm
      await escrow.connect(poster).confirmDelivery(escrowId);

      // After confirmation the solver should have received the escrowed amount
      // (minus gas for submitDelivery, but we just check the contract is empty)
      const contractBal = await ethers.provider.getBalance(await escrow.getAddress());
      expect(contractBal).to.equal(0);

      const e = await escrow.getEscrow(escrowId);
      expect(e.status).to.equal(3); // Confirmed
    });
  });

  // -------------------------------------------------------------------
  // Timeout Path
  // -------------------------------------------------------------------

  describe("Timeout Path", function () {
    it("should allow poster to reclaim funds after deadline", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      // Advance time past deadline
      await time.increaseTo(deadline + 1);

      const tx = await escrow.connect(poster).claimTimeout(escrowId);

      await expect(tx)
        .to.emit(escrow, "TimeoutClaimed")
        .withArgs(escrowId, poster.address, fundAmount);

      await expect(tx).to.changeEtherBalances(
        [poster, escrow],
        [fundAmount, -fundAmount]
      );

      const e = await escrow.getEscrow(escrowId);
      expect(e.status).to.equal(6); // TimedOut
    });
  });

  // -------------------------------------------------------------------
  // Dispute Path
  // -------------------------------------------------------------------

  describe("Dispute Path", function () {
    it("poster disputes -> admin resolves to solver", async function () {
      const { escrow, admin, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      // Poster raises dispute
      const disputeTx = await escrow.connect(poster).raiseDispute(escrowId);
      await expect(disputeTx)
        .to.emit(escrow, "DisputeRaised")
        .withArgs(escrowId, poster.address);

      let e = await escrow.getEscrow(escrowId);
      expect(e.status).to.equal(4); // Disputed

      // Admin resolves to solver
      const resolveTx = await escrow.connect(admin).resolveDispute(escrowId, solver.address);

      await expect(resolveTx)
        .to.emit(escrow, "DisputeResolved")
        .withArgs(escrowId, solver.address, fundAmount);

      await expect(resolveTx).to.changeEtherBalances(
        [solver, escrow],
        [fundAmount, -fundAmount]
      );

      e = await escrow.getEscrow(escrowId);
      expect(e.status).to.equal(5); // Resolved
    });

    it("solver disputes -> admin resolves to poster", async function () {
      const { escrow, admin, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      // Solver raises dispute
      const disputeTx = await escrow.connect(solver).raiseDispute(escrowId);
      await expect(disputeTx)
        .to.emit(escrow, "DisputeRaised")
        .withArgs(escrowId, solver.address);

      // Admin resolves to poster
      const resolveTx = await escrow.connect(admin).resolveDispute(escrowId, poster.address);

      await expect(resolveTx)
        .to.emit(escrow, "DisputeResolved")
        .withArgs(escrowId, poster.address, fundAmount);

      await expect(resolveTx).to.changeEtherBalances(
        [poster, escrow],
        [fundAmount, -fundAmount]
      );

      const e = await escrow.getEscrow(escrowId);
      expect(e.status).to.equal(5); // Resolved
    });

    it("dispute -> resolve to solver -> verify payout", async function () {
      const { escrow, admin, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);
      await escrow.connect(poster).raiseDispute(escrowId);

      const resolveTx = await escrow.connect(admin).resolveDispute(escrowId, solver.address);

      await expect(resolveTx).to.changeEtherBalances(
        [solver, escrow],
        [fundAmount, -fundAmount]
      );

      const contractBal = await ethers.provider.getBalance(await escrow.getAddress());
      expect(contractBal).to.equal(0);
    });
  });

  // -------------------------------------------------------------------
  // Access Control
  // -------------------------------------------------------------------

  describe("Access Control", function () {
    it("non-poster cannot confirm delivery", async function () {
      const { escrow, poster, solver, outsider, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      await expect(
        escrow.connect(outsider).confirmDelivery(escrowId)
      ).to.be.revertedWith("Only poster can confirm delivery");

      await expect(
        escrow.connect(solver).confirmDelivery(escrowId)
      ).to.be.revertedWith("Only poster can confirm delivery");
    });

    it("non-solver cannot submit delivery", async function () {
      const { escrow, poster, solver, outsider, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      await expect(
        escrow.connect(poster).submitDelivery(escrowId)
      ).to.be.revertedWith("Only solver can submit delivery");

      await expect(
        escrow.connect(outsider).submitDelivery(escrowId)
      ).to.be.revertedWith("Only solver can submit delivery");
    });

    it("non-admin cannot resolve dispute", async function () {
      const { escrow, poster, solver, outsider, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);
      await escrow.connect(poster).raiseDispute(escrowId);

      await expect(
        escrow.connect(poster).resolveDispute(escrowId, poster.address)
      ).to.be.revertedWith("Only admin can resolve disputes");

      await expect(
        escrow.connect(solver).resolveDispute(escrowId, solver.address)
      ).to.be.revertedWith("Only admin can resolve disputes");

      await expect(
        escrow.connect(outsider).resolveDispute(escrowId, solver.address)
      ).to.be.revertedWith("Only admin can resolve disputes");
    });

    it("non-poster cannot claim timeout", async function () {
      const { escrow, poster, solver, outsider, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await time.increaseTo(deadline + 1);

      await expect(
        escrow.connect(solver).claimTimeout(escrowId)
      ).to.be.revertedWith("Only poster can claim timeout");

      await expect(
        escrow.connect(outsider).claimTimeout(escrowId)
      ).to.be.revertedWith("Only poster can claim timeout");
    });

    it("only poster or solver can raise dispute", async function () {
      const { escrow, poster, solver, outsider, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      await expect(
        escrow.connect(outsider).raiseDispute(escrowId)
      ).to.be.revertedWith("Only poster or solver can raise dispute");
    });
  });

  // -------------------------------------------------------------------
  // Edge Cases
  // -------------------------------------------------------------------

  describe("Edge Cases", function () {
    it("cannot create escrow with same ID twice", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      await expect(
        createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount)
      ).to.be.revertedWith("Escrow already exists");
    });

    it("cannot create with zero value", async function () {
      const { escrow, poster, solver, escrowId, termsHash, deadline } =
        await loadFixture(deployFixture);

      await expect(
        escrow
          .connect(poster)
          .createAndFund(escrowId, solver.address, termsHash, deadline, {
            value: 0,
          })
      ).to.be.revertedWith("Must send ETH");
    });

    it("cannot create with solver = address(0)", async function () {
      const { escrow, poster, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await expect(
        escrow
          .connect(poster)
          .createAndFund(escrowId, ethers.ZeroAddress, termsHash, deadline, {
            value: fundAmount,
          })
      ).to.be.revertedWith("Solver cannot be zero address");
    });

    it("cannot create with solver = poster (self-escrow)", async function () {
      const { escrow, poster, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await expect(
        escrow
          .connect(poster)
          .createAndFund(escrowId, poster.address, termsHash, deadline, {
            value: fundAmount,
          })
      ).to.be.revertedWith("Solver cannot be poster");
    });

    it("cannot create with past deadline", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount } =
        await loadFixture(deployFixture);

      const pastDeadline = (await time.latest()) - 100;

      await expect(
        escrow
          .connect(poster)
          .createAndFund(escrowId, solver.address, termsHash, pastDeadline, {
            value: fundAmount,
          })
      ).to.be.revertedWith("Deadline must be in the future");
    });

    it("cannot submit delivery when not in Funded status", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      // No escrow created yet (status == None)
      await expect(
        escrow.connect(solver).submitDelivery(escrowId)
      ).to.be.revertedWith("Only solver can submit delivery");

      // Create and move to DeliverySubmitted
      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      // Try again - now in DeliverySubmitted status
      await expect(
        escrow.connect(solver).submitDelivery(escrowId)
      ).to.be.revertedWith("Escrow not in Funded status");
    });

    it("cannot confirm when not in DeliverySubmitted status", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      // Still in Funded status - delivery not submitted yet
      await expect(
        escrow.connect(poster).confirmDelivery(escrowId)
      ).to.be.revertedWith("Escrow not in DeliverySubmitted status");
    });

    it("cannot dispute when not in DeliverySubmitted status", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      // Still in Funded status
      await expect(
        escrow.connect(poster).raiseDispute(escrowId)
      ).to.be.revertedWith("Escrow not in DeliverySubmitted status");
    });

    it("cannot resolve when not in Disputed status", async function () {
      const { escrow, admin, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      // Status is DeliverySubmitted, not Disputed
      await expect(
        escrow.connect(admin).resolveDispute(escrowId, solver.address)
      ).to.be.revertedWith("Escrow not in Disputed status");
    });

    it("cannot claim timeout before deadline", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);

      await expect(
        escrow.connect(poster).claimTimeout(escrowId)
      ).to.be.revertedWith("Deadline has not passed");
    });

    it("cannot claim timeout if delivery already submitted", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);

      await time.increaseTo(deadline + 1);

      // Status is now DeliverySubmitted, not Funded
      await expect(
        escrow.connect(poster).claimTimeout(escrowId)
      ).to.be.revertedWith("Escrow not in Funded status");
    });

    it("resolveDispute winner must be poster or solver", async function () {
      const { escrow, admin, poster, solver, outsider, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);
      await escrow.connect(poster).raiseDispute(escrowId);

      await expect(
        escrow.connect(admin).resolveDispute(escrowId, outsider.address)
      ).to.be.revertedWith("Winner must be poster or solver");
    });
  });

  // -------------------------------------------------------------------
  // Event Emission (comprehensive)
  // -------------------------------------------------------------------

  describe("Event Emission", function () {
    it("EscrowCreated fires with correct indexed args", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      const tx = await createEscrow(
        escrow,
        poster,
        escrowId,
        solver.address,
        termsHash,
        deadline,
        fundAmount
      );

      await expect(tx)
        .to.emit(escrow, "EscrowCreated")
        .withArgs(escrowId, poster.address, solver.address, fundAmount, termsHash, deadline);
    });

    it("DeliverySubmitted fires with correct indexed args", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      const tx = await escrow.connect(solver).submitDelivery(escrowId);

      await expect(tx).to.emit(escrow, "DeliverySubmitted").withArgs(escrowId);
    });

    it("DeliveryConfirmed fires with correct indexed args", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);
      const tx = await escrow.connect(poster).confirmDelivery(escrowId);

      await expect(tx)
        .to.emit(escrow, "DeliveryConfirmed")
        .withArgs(escrowId, solver.address, fundAmount);
    });

    it("DisputeRaised fires with correct indexed args (poster)", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);
      const tx = await escrow.connect(poster).raiseDispute(escrowId);

      await expect(tx)
        .to.emit(escrow, "DisputeRaised")
        .withArgs(escrowId, poster.address);
    });

    it("DisputeRaised fires with correct indexed args (solver)", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);
      const tx = await escrow.connect(solver).raiseDispute(escrowId);

      await expect(tx)
        .to.emit(escrow, "DisputeRaised")
        .withArgs(escrowId, solver.address);
    });

    it("DisputeResolved fires with correct indexed args", async function () {
      const { escrow, admin, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await escrow.connect(solver).submitDelivery(escrowId);
      await escrow.connect(poster).raiseDispute(escrowId);
      const tx = await escrow.connect(admin).resolveDispute(escrowId, solver.address);

      await expect(tx)
        .to.emit(escrow, "DisputeResolved")
        .withArgs(escrowId, solver.address, fundAmount);
    });

    it("TimeoutClaimed fires with correct indexed args", async function () {
      const { escrow, poster, solver, escrowId, termsHash, fundAmount, deadline } =
        await loadFixture(deployFixture);

      await createEscrow(escrow, poster, escrowId, solver.address, termsHash, deadline, fundAmount);
      await time.increaseTo(deadline + 1);
      const tx = await escrow.connect(poster).claimTimeout(escrowId);

      await expect(tx)
        .to.emit(escrow, "TimeoutClaimed")
        .withArgs(escrowId, poster.address, fundAmount);
    });
  });

  // -------------------------------------------------------------------
  // View function
  // -------------------------------------------------------------------

  describe("getEscrow", function () {
    it("returns default struct for non-existent escrow", async function () {
      const { escrow, escrowId } = await loadFixture(deployFixture);

      const e = await escrow.getEscrow(escrowId);
      expect(e.poster).to.equal(ethers.ZeroAddress);
      expect(e.solver).to.equal(ethers.ZeroAddress);
      expect(e.amount).to.equal(0);
      expect(e.status).to.equal(0); // None
    });
  });

  // -------------------------------------------------------------------
  // Admin
  // -------------------------------------------------------------------

  describe("Admin", function () {
    it("admin is set to deployer in constructor", async function () {
      const { escrow, admin } = await loadFixture(deployFixture);

      expect(await escrow.admin()).to.equal(admin.address);
    });
  });
});
