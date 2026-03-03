// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title TectonicEscrow
 * @notice Escrow contract for the Tectonic Agent Commerce Protocol.
 *         Handles creation, delivery, confirmation, disputes, and timeouts
 *         for agent-to-agent service agreements.
 */
contract TectonicEscrow {
    // ---------------------------------------------------------------
    // Enums & Structs
    // ---------------------------------------------------------------

    enum EscrowStatus {
        None,
        Funded,
        DeliverySubmitted,
        Confirmed,
        Disputed,
        Resolved,
        TimedOut
    }

    struct Escrow {
        address poster;
        address solver;
        uint256 amount;
        bytes32 termsHash;
        uint256 deadline;
        EscrowStatus status;
    }

    // ---------------------------------------------------------------
    // State
    // ---------------------------------------------------------------

    mapping(bytes32 => Escrow) public escrows;
    address public admin;

    // ---------------------------------------------------------------
    // Events
    // ---------------------------------------------------------------

    event EscrowCreated(
        bytes32 indexed escrowId,
        address indexed poster,
        address indexed solver,
        uint256 amount,
        bytes32 termsHash,
        uint256 deadline
    );

    event DeliverySubmitted(bytes32 indexed escrowId);

    event DeliveryConfirmed(
        bytes32 indexed escrowId,
        address indexed solver,
        uint256 amount
    );

    event DisputeRaised(
        bytes32 indexed escrowId,
        address indexed raisedBy
    );

    event DisputeResolved(
        bytes32 indexed escrowId,
        address indexed winner,
        uint256 amount
    );

    event TimeoutClaimed(
        bytes32 indexed escrowId,
        address indexed poster,
        uint256 amount
    );

    // ---------------------------------------------------------------
    // Constructor
    // ---------------------------------------------------------------

    constructor() {
        admin = msg.sender;
    }

    // ---------------------------------------------------------------
    // External functions
    // ---------------------------------------------------------------

    /**
     * @notice Create a new escrow and fund it with ETH.
     * @param escrowId   Unique identifier for this escrow.
     * @param solver     Address of the solver who will fulfil the task.
     * @param termsHash  Keccak-256 hash of the off-chain terms document.
     * @param deadline   Unix timestamp after which the poster may reclaim funds.
     */
    function createAndFund(
        bytes32 escrowId,
        address solver,
        bytes32 termsHash,
        uint256 deadline
    ) external payable {
        require(escrows[escrowId].status == EscrowStatus.None, "Escrow already exists");
        require(msg.value > 0, "Must send ETH");
        require(solver != address(0), "Solver cannot be zero address");
        require(solver != msg.sender, "Solver cannot be poster");
        require(deadline > block.timestamp, "Deadline must be in the future");

        escrows[escrowId] = Escrow({
            poster: msg.sender,
            solver: solver,
            amount: msg.value,
            termsHash: termsHash,
            deadline: deadline,
            status: EscrowStatus.Funded
        });

        emit EscrowCreated(escrowId, msg.sender, solver, msg.value, termsHash, deadline);
    }

    /**
     * @notice Solver marks the work as delivered.
     * @param escrowId  The escrow to update.
     */
    function submitDelivery(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.solver, "Only solver can submit delivery");
        require(e.status == EscrowStatus.Funded, "Escrow not in Funded status");

        e.status = EscrowStatus.DeliverySubmitted;

        emit DeliverySubmitted(escrowId);
    }

    /**
     * @notice Poster confirms the delivery and releases funds to the solver.
     * @param escrowId  The escrow to confirm.
     */
    function confirmDelivery(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.poster, "Only poster can confirm delivery");
        require(e.status == EscrowStatus.DeliverySubmitted, "Escrow not in DeliverySubmitted status");

        e.status = EscrowStatus.Confirmed;

        (bool success, ) = e.solver.call{value: e.amount}("");
        require(success, "Transfer to solver failed");

        emit DeliveryConfirmed(escrowId, e.solver, e.amount);
    }

    /**
     * @notice Either party raises a dispute after delivery is submitted.
     * @param escrowId  The escrow to dispute.
     */
    function raiseDispute(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(
            msg.sender == e.poster || msg.sender == e.solver,
            "Only poster or solver can raise dispute"
        );
        require(e.status == EscrowStatus.DeliverySubmitted, "Escrow not in DeliverySubmitted status");

        e.status = EscrowStatus.Disputed;

        emit DisputeRaised(escrowId, msg.sender);
    }

    /**
     * @notice Admin resolves a dispute and sends funds to the winner.
     * @param escrowId  The escrow to resolve.
     * @param winner    Address that should receive the escrowed funds.
     */
    function resolveDispute(bytes32 escrowId, address winner) external {
        require(msg.sender == admin, "Only admin can resolve disputes");

        Escrow storage e = escrows[escrowId];
        require(e.status == EscrowStatus.Disputed, "Escrow not in Disputed status");
        require(
            winner == e.poster || winner == e.solver,
            "Winner must be poster or solver"
        );

        e.status = EscrowStatus.Resolved;

        (bool success, ) = winner.call{value: e.amount}("");
        require(success, "Transfer to winner failed");

        emit DisputeResolved(escrowId, winner, e.amount);
    }

    /**
     * @notice Poster reclaims funds after the deadline if no delivery was submitted.
     * @param escrowId  The escrow to reclaim.
     */
    function claimTimeout(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.poster, "Only poster can claim timeout");
        require(e.status == EscrowStatus.Funded, "Escrow not in Funded status");
        require(block.timestamp > e.deadline, "Deadline has not passed");

        e.status = EscrowStatus.TimedOut;

        (bool success, ) = e.poster.call{value: e.amount}("");
        require(success, "Transfer to poster failed");

        emit TimeoutClaimed(escrowId, e.poster, e.amount);
    }

    // ---------------------------------------------------------------
    // View functions
    // ---------------------------------------------------------------

    /**
     * @notice Returns the full Escrow struct for a given ID.
     * @param escrowId  The escrow to query.
     */
    function getEscrow(bytes32 escrowId) external view returns (Escrow memory) {
        return escrows[escrowId];
    }
}
