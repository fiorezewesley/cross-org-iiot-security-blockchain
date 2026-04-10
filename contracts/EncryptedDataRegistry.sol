// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title EncryptedDataRegistry
/// @notice Registers the metadata of encrypted messages coming from the IIoT environment in the BC.
///         The encrypted message itself (ciphertext) remains off-chain... here I'll keep the "trace".
contract EncryptedDataRegistry {
    struct Record {
        uint256 id;           // Internal incremental ID
        address publisher;    // who registered (Ethereum address)
        string deviceId;      // Logical ID of the device (e.g., "sensor_001")
        string topic;         // MQTT topic used (e.g., "sensors/sensor_001/data")
        string abePolicy;     // ABE policy applied (e.g., "role:engineer AND level:2")
        string cipherHash;    // Hash/reference of the ciphertext (e.g., SHA256 or IPFS hash)
        uint256 timestamp;    // block.timestamp at creation
    }

    uint256 private _lastId;
    mapping(uint256 => Record) private _records;

    event RecordStored(
        uint256 indexed id,
        address indexed publisher,
        string deviceId,
        string topic,
        string abePolicy,
        string cipherHash,
        uint256 timestamp
    );

    /// @notice Registers a new encrypted data event.
    /// @param deviceId  Logical ID of the IIoT device.
    /// @param topic     MQTT topic where the message was published.
    /// @param abePolicy ABE policy used in the encryption.
    /// @param cipherHash Hash or reference of the ciphertext (off-chain).
    /// @return id       Internal ID generated for this record.
    function storeRecord(
        string calldata deviceId,
        string calldata topic,
        string calldata abePolicy,
        string calldata cipherHash
    ) external returns (uint256 id) {
        _lastId += 1;
        id = _lastId;

        Record memory rec = Record({
            id: id,
            publisher: msg.sender,
            deviceId: deviceId,
            topic: topic,
            abePolicy: abePolicy,
            cipherHash: cipherHash,
            timestamp: block.timestamp
        });

        _records[id] = rec;

        emit RecordStored(
            id,
            msg.sender,
            deviceId,
            topic,
            abePolicy,
            cipherHash,
            block.timestamp
        );
        

        return id;
    }

    /// @notice Retrieves a record by its internal ID.
    function getRecord(uint256 id)
        external
        view
        returns (
            uint256,
            address,
            string memory,
            string memory,
            string memory,
            string memory,
            uint256
        )
    {
        Record memory r = _records[id];
        require(r.id != 0, "Record not found");

        return (
            r.id,
            r.publisher,
            r.deviceId,
            r.topic,
            r.abePolicy,
            r.cipherHash,
            r.timestamp
        );
    }

    /// @notice Returns the last inserted ID (useful for knowing the current size).
    function lastId() external view returns (uint256) {
        return _lastId;
    }
}
