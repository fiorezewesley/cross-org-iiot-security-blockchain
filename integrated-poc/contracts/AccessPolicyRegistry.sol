// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AccessPolicyRegistry
 * @dev Minimal smart contract for the integrated MQTT + ABE + Blockchain PoC.
 *
 * The contract does not store plaintext sensor data and does not execute
 * cryptographic operations. It only registers devices, topic policies,
 * access requests, key grants, protected message hashes, and consumption events.
 */
contract AccessPolicyRegistry {
    address public owner;

    uint256 public lastRequestId;
    uint256 public lastProtectedMessageId;
    uint256 public lastConsumptionEventId;

    struct Device {
        string deviceId;
        string organization;
        string role;
        bool exists;
    }

    struct TopicPolicy {
        string topic;
        string policy;
        bool exists;
    }

    struct AccessRequest {
        uint256 requestId;
        string subscriberId;
        string topic;
        uint256 timestamp;
        bool granted;
        bool exists;
    }

    struct KeyGrant {
        uint256 requestId;
        string subscriberId;
        string topic;
        string uskHash;
        uint256 timestamp;
        bool exists;
    }

    struct ProtectedMessage {
        uint256 messageId;
        string producerId;
        string topic;
        string ciphertextHash;
        string policy;
        uint256 timestamp;
    }

    struct ConsumptionEvent {
        uint256 eventId;
        string subscriberId;
        string topic;
        bool success;
        string resultHash;
        uint256 timestamp;
    }

    mapping(string => Device) public devices;
    mapping(string => TopicPolicy) public topicPolicies;
    mapping(uint256 => AccessRequest) public accessRequests;
    mapping(uint256 => KeyGrant) public keyGrants;
    mapping(uint256 => ProtectedMessage) public protectedMessages;
    mapping(uint256 => ConsumptionEvent) public consumptionEvents;

    event DeviceRegistered(
        string deviceId,
        string organization,
        string role,
        uint256 timestamp
    );

    event TopicPolicyRegistered(
        string topic,
        string policy,
        uint256 timestamp
    );

    event AccessRequested(
        uint256 indexed requestId,
        string subscriberId,
        string topic,
        uint256 timestamp
    );

    event KeyGranted(
        uint256 indexed requestId,
        string subscriberId,
        string topic,
        string uskHash,
        uint256 timestamp
    );

    event ProtectedMessageStored(
        uint256 indexed messageId,
        string producerId,
        string topic,
        string ciphertextHash,
        string policy,
        uint256 timestamp
    );

    event ConsumptionEventStored(
        uint256 indexed eventId,
        string subscriberId,
        string topic,
        bool success,
        string resultHash,
        uint256 timestamp
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can execute this operation");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function registerDevice(
        string memory deviceId,
        string memory organization,
        string memory role
    ) public onlyOwner {
        devices[deviceId] = Device(deviceId, organization, role, true);

        emit DeviceRegistered(
            deviceId,
            organization,
            role,
            block.timestamp
        );
    }

    function registerTopicPolicy(
        string memory topic,
        string memory policy
    ) public onlyOwner {
        topicPolicies[topic] = TopicPolicy(topic, policy, true);

        emit TopicPolicyRegistered(
            topic,
            policy,
            block.timestamp
        );
    }

    function requestAccess(
        string memory subscriberId,
        string memory topic
    ) public returns (uint256) {
        require(devices[subscriberId].exists, "Subscriber device not registered");
        require(topicPolicies[topic].exists, "Topic policy not registered");

        lastRequestId++;

        accessRequests[lastRequestId] = AccessRequest(
            lastRequestId,
            subscriberId,
            topic,
            block.timestamp,
            false,
            true
        );

        emit AccessRequested(
            lastRequestId,
            subscriberId,
            topic,
            block.timestamp
        );

        return lastRequestId;
    }

    function grantKey(
        uint256 requestId,
        string memory uskHash
    ) public onlyOwner {
        require(accessRequests[requestId].exists, "Access request not found");
        require(!accessRequests[requestId].granted, "Access request already granted");

        AccessRequest storage accessRequest = accessRequests[requestId];
        accessRequest.granted = true;

        keyGrants[requestId] = KeyGrant(
            requestId,
            accessRequest.subscriberId,
            accessRequest.topic,
            uskHash,
            block.timestamp,
            true
        );

        emit KeyGranted(
            requestId,
            accessRequest.subscriberId,
            accessRequest.topic,
            uskHash,
            block.timestamp
        );
    }

    function storeProtectedMessage(
        string memory producerId,
        string memory topic,
        string memory ciphertextHash
    ) public returns (uint256) {
        require(devices[producerId].exists, "Producer device not registered");
        require(topicPolicies[topic].exists, "Topic policy not registered");

        lastProtectedMessageId++;

        string memory policy = topicPolicies[topic].policy;

        protectedMessages[lastProtectedMessageId] = ProtectedMessage(
            lastProtectedMessageId,
            producerId,
            topic,
            ciphertextHash,
            policy,
            block.timestamp
        );

        emit ProtectedMessageStored(
            lastProtectedMessageId,
            producerId,
            topic,
            ciphertextHash,
            policy,
            block.timestamp
        );

        return lastProtectedMessageId;
    }

    function storeConsumptionEvent(
        string memory subscriberId,
        string memory topic,
        bool success,
        string memory resultHash
    ) public returns (uint256) {
        require(devices[subscriberId].exists, "Subscriber device not registered");

        lastConsumptionEventId++;

        consumptionEvents[lastConsumptionEventId] = ConsumptionEvent(
            lastConsumptionEventId,
            subscriberId,
            topic,
            success,
            resultHash,
            block.timestamp
        );

        emit ConsumptionEventStored(
            lastConsumptionEventId,
            subscriberId,
            topic,
            success,
            resultHash,
            block.timestamp
        );

        return lastConsumptionEventId;
    }

    function getTopicPolicy(
        string memory topic
    ) public view returns (string memory) {
        require(topicPolicies[topic].exists, "Topic policy not registered");
        return topicPolicies[topic].policy;
    }

    function hasKeyGrant(
        uint256 requestId
    ) public view returns (bool) {
        return keyGrants[requestId].exists;
    }

    function getKeyGrant(
        uint256 requestId
    )
        public
        view
        returns (
            string memory subscriberId,
            string memory topic,
            string memory uskHash,
            uint256 timestamp
        )
    {
        require(keyGrants[requestId].exists, "Key grant not found");

        KeyGrant memory grant = keyGrants[requestId];

        return (
            grant.subscriberId,
            grant.topic,
            grant.uskHash,
            grant.timestamp
        );
    }
}
