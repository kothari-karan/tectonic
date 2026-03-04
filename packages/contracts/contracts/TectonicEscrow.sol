// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title TectonicEscrow
 * @notice Escrow contract for the Tectonic Agent Commerce Protocol.
 *         Handles creation, delivery, confirmation, disputes, and timeouts
 *         for agent-to-agent service engagements.
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
        address requester;
        address provider;
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
        address indexed requester,
        address indexed provider,
        uint256 amount,
        bytes32 termsHash,
        uint256 deadline
    );

    event DeliverySubmitted(bytes32 indexed escrowId);

    event DeliveryConfirmed(
        bytes32 indexed escrowId,
        address indexed provider,
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
        address indexed requester,
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
     * @param escrowId    Unique identifier for this escrow.
     * @param provider    Address of the provider who will fulfil the engagement.
     * @param termsHash   Keccak-256 hash of the off-chain terms document.
     * @param deadline    Unix timestamp after which the requester may reclaim funds.
     */
    function createAndFund(
        bytes32 escrowId,
        address provider,
        bytes32 termsHash,
        uint256 deadline
    ) external payable {
        require(escrows[escrowId].status == EscrowStatus.None, "Escrow already exists");
        require(msg.value > 0, "Must send ETH");
        require(provider != address(0), "Provider cannot be zero address");
        require(provider != msg.sender, "Provider cannot be requester");
        require(deadline > block.timestamp, "Deadline must be in the future");

        escrows[escrowId] = Escrow({
            requester: msg.sender,
            provider: provider,
            amount: msg.value,
            termsHash: termsHash,
            deadline: deadline,
            status: EscrowStatus.Funded
        });

        emit EscrowCreated(escrowId, msg.sender, provider, msg.value, termsHash, deadline);
    }

    /**
     * @notice Provider marks the work as delivered.
     * @param escrowId  The escrow to update.
     */
    function submitDelivery(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.provider, "Only provider can submit delivery");
        require(e.status == EscrowStatus.Funded, "Escrow not in Funded status");

        e.status = EscrowStatus.DeliverySubmitted;

        emit DeliverySubmitted(escrowId);
    }

    /**
     * @notice Requester confirms the delivery and releases funds to the provider.
     * @param escrowId  The escrow to confirm.
     */
    function confirmDelivery(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.requester, "Only requester can confirm delivery");
        require(e.status == EscrowStatus.DeliverySubmitted, "Escrow not in DeliverySubmitted status");

        e.status = EscrowStatus.Confirmed;

        (bool success, ) = e.provider.call{value: e.amount}("");
        require(success, "Transfer to provider failed");

        emit DeliveryConfirmed(escrowId, e.provider, e.amount);
    }

    /**
     * @notice Either party raises a dispute after delivery is submitted.
     * @param escrowId  The escrow to dispute.
     */
    function raiseDispute(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(
            msg.sender == e.requester || msg.sender == e.provider,
            "Only requester or provider can raise dispute"
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
            winner == e.requester || winner == e.provider,
            "Winner must be requester or provider"
        );

        e.status = EscrowStatus.Resolved;

        (bool success, ) = winner.call{value: e.amount}("");
        require(success, "Transfer to winner failed");

        emit DisputeResolved(escrowId, winner, e.amount);
    }

    /**
     * @notice Requester reclaims funds after the deadline if no delivery was submitted.
     * @param escrowId  The escrow to reclaim.
     */
    function claimTimeout(bytes32 escrowId) external {
        Escrow storage e = escrows[escrowId];
        require(msg.sender == e.requester, "Only requester can claim timeout");
        require(e.status == EscrowStatus.Funded, "Escrow not in Funded status");
        require(block.timestamp > e.deadline, "Deadline has not passed");

        e.status = EscrowStatus.TimedOut;

        (bool success, ) = e.requester.call{value: e.amount}("");
        require(success, "Transfer to requester failed");

        emit TimeoutClaimed(escrowId, e.requester, e.amount);
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
