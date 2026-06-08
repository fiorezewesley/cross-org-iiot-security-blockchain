// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract AccessPolicyRegistryV3 {
    address public owner;

    struct Device {
        string organization;
        string role;
        bool exists;
    }

    struct TopicPolicy {
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
        string subscriberId;
        string topic;
        string encryptedUserKey;
        string keyHash;
        uint256 timestamp;
        bool exists;
    }

    struct ProtectedMessage {
        uint256 messageId;
        string producerId;
        string topic;
        string ciphertextHash;
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
    mapping(string => string) public subscriberAttributes;

    mapping(uint256 => AccessRequest) public accessRequests;
    mapping(uint256 => KeyGrant) public keyGrants;
    mapping(uint256 => ProtectedMessage) public protectedMessages;
    mapping(uint256 => ConsumptionEvent) public consumptionEvents;

    uint256 public lastRequestId;
    uint256 public lastProtectedMessageId;
    uint256 public lastConsumptionEventId;

    event DeviceRegistered(string deviceId, string organization, string role);
    event SubscriberAttributesRegistered(string subscriberId, string attributes);
    event TopicPolicyRegistered(string topic, string policy);

    event AccessRequested(
        uint256 requestId,
        string subscriberId,
        string topic
    );

    event KeyGranted(
        uint256 requestId,
        string subscriberId,
        string topic,
        string keyHash
    );

    event EncryptedKeyGranted(
        uint256 requestId,
        string subscriberId,
        string topic,
        string encryptedUserKey,
        string keyHash
    );

    event ProtectedMessageStored(
        uint256 messageId,
        string producerId,
        string topic,
        string ciphertextHash
    );

    event ConsumptionEventStored(
        uint256 eventId,
        string subscriberId,
        string topic,
        bool success,
        string resultHash
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can execute this function");
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
        devices[deviceId] = Device({
            organization: organization,
            role: role,
            exists: true
        });

        emit DeviceRegistered(deviceId, organization, role);
    }

    function registerSubscriberAttributes(
        string memory subscriberId,
        string memory attributes
    ) public onlyOwner {
        require(devices[subscriberId].exists, "Subscriber device does not exist");

        subscriberAttributes[subscriberId] = attributes;

        emit SubscriberAttributesRegistered(subscriberId, attributes);
    }

    function getSubscriberAttributes(
        string memory subscriberId
    ) public view returns (string memory) {
        require(devices[subscriberId].exists, "Subscriber device does not exist");

        return subscriberAttributes[subscriberId];
    }

    function registerTopicPolicy(
        string memory topic,
        string memory policy
    ) public onlyOwner {
        topicPolicies[topic] = TopicPolicy({
            policy: policy,
            exists: true
        });

        emit TopicPolicyRegistered(topic, policy);
    }

    function getTopicPolicy(
        string memory topic
    ) public view returns (string memory) {
        require(topicPolicies[topic].exists, "Topic policy does not exist");

        return topicPolicies[topic].policy;
    }

    function requestAccess(
        string memory subscriberId,
        string memory topic
    ) public returns (uint256) {
        require(devices[subscriberId].exists, "Subscriber device does not exist");
        require(topicPolicies[topic].exists, "Topic policy does not exist");

        lastRequestId++;

        accessRequests[lastRequestId] = AccessRequest({
            requestId: lastRequestId,
            subscriberId: subscriberId,
            topic: topic,
            timestamp: block.timestamp,
            granted: false,
            exists: true
        });

        emit AccessRequested(lastRequestId, subscriberId, topic);

        return lastRequestId;
    }

    function grantKey(
        uint256 requestId,
        string memory keyHash
    ) public onlyOwner {
        require(accessRequests[requestId].exists, "Access request does not exist");
        require(!accessRequests[requestId].granted, "Access request already granted");

        AccessRequest storage req = accessRequests[requestId];

        keyGrants[requestId] = KeyGrant({
            subscriberId: req.subscriberId,
            topic: req.topic,
            encryptedUserKey: "",
            keyHash: keyHash,
            timestamp: block.timestamp,
            exists: true
        });

        req.granted = true;

        emit KeyGranted(requestId, req.subscriberId, req.topic, keyHash);
    }

    function grantEncryptedKey(
        uint256 requestId,
        string memory encryptedUserKey,
        string memory keyHash
    ) public onlyOwner {
        require(accessRequests[requestId].exists, "Access request does not exist");
        require(!accessRequests[requestId].granted, "Access request already granted");

        AccessRequest storage req = accessRequests[requestId];

        keyGrants[requestId] = KeyGrant({
            subscriberId: req.subscriberId,
            topic: req.topic,
            encryptedUserKey: encryptedUserKey,
            keyHash: keyHash,
            timestamp: block.timestamp,
            exists: true
        });

        req.granted = true;

        emit EncryptedKeyGranted(
            requestId,
            req.subscriberId,
            req.topic,
            encryptedUserKey,
            keyHash
        );
    }

    function getKeyGrant(
        uint256 requestId
    )
        public
        view
        returns (
            string memory subscriberId,
            string memory topic,
            string memory encryptedUserKey,
            string memory keyHash,
            uint256 timestamp
        )
    {
        require(keyGrants[requestId].exists, "Key grant does not exist");

        KeyGrant memory grant = keyGrants[requestId];

        return (
            grant.subscriberId,
            grant.topic,
            grant.encryptedUserKey,
            grant.keyHash,
            grant.timestamp
        );
    }

    function hasKeyGrant(
        uint256 requestId
    ) public view returns (bool) {
        return keyGrants[requestId].exists;
    }

    function getPendingAccessRequests()
        public
        view
        returns (AccessRequest[] memory)
    {
        uint256 count = 0;

        for (uint256 i = 1; i <= lastRequestId; i++) {
            if (accessRequests[i].exists && !accessRequests[i].granted) {
                count++;
            }
        }

        AccessRequest[] memory pending = new AccessRequest[](count);
        uint256 index = 0;

        for (uint256 i = 1; i <= lastRequestId; i++) {
            if (accessRequests[i].exists && !accessRequests[i].granted) {
                pending[index] = accessRequests[i];
                index++;
            }
        }

        return pending;
    }

    function storeProtectedMessage(
        string memory producerId,
        string memory topic,
        string memory ciphertextHash
    ) public returns (uint256) {
        require(devices[producerId].exists, "Producer device does not exist");
        require(topicPolicies[topic].exists, "Topic policy does not exist");

        lastProtectedMessageId++;

        protectedMessages[lastProtectedMessageId] = ProtectedMessage({
            messageId: lastProtectedMessageId,
            producerId: producerId,
            topic: topic,
            ciphertextHash: ciphertextHash,
            timestamp: block.timestamp
        });

        emit ProtectedMessageStored(
            lastProtectedMessageId,
            producerId,
            topic,
            ciphertextHash
        );

        return lastProtectedMessageId;
    }

    function storeConsumptionEvent(
        string memory subscriberId,
        string memory topic,
        bool success,
        string memory resultHash
    ) public returns (uint256) {
        require(devices[subscriberId].exists, "Subscriber device does not exist");

        lastConsumptionEventId++;

        consumptionEvents[lastConsumptionEventId] = ConsumptionEvent({
            eventId: lastConsumptionEventId,
            subscriberId: subscriberId,
            topic: topic,
            success: success,
            resultHash: resultHash,
            timestamp: block.timestamp
        });

        emit ConsumptionEventStored(
            lastConsumptionEventId,
            subscriberId,
            topic,
            success,
            resultHash
        );

        return lastConsumptionEventId;
    }
}
