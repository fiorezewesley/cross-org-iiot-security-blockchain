// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title EncryptedDataRegistry
/// @notice Registra, em blockchain, metadados de mensagens cifradas vindas do ambiente IIoT.
///         A mensagem cifrada em si (ciphertext) continua off-chain (MQTT/Storage), aqui guardamos o "rastro".
contract EncryptedDataRegistry {
    struct Record {
        uint256 id;           // ID interno incremental
        address publisher;    // quem registrou (endereço Ethereum)
        string deviceId;      // ID lógico do dispositivo (ex: "sensor_001")
        string topic;         // tópico MQTT usado (ex: "sensors/sensor_001/data")
        string abePolicy;     // política ABE aplicada (ex: "role:engineer AND level:2")
        string cipherHash;    // hash / referência do ciphertext (ex: SHA256 ou IPFS hash)
        uint256 timestamp;    // bloco.timestamp na criação
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

    /// @notice Registra um novo evento de dado cifrado.
    /// @param deviceId  Identificador lógico do dispositivo IIoT.
    /// @param topic     Tópico MQTT em que a mensagem foi publicada.
    /// @param abePolicy Política ABE usada na cifragem.
    /// @param cipherHash Hash ou referência do ciphertext (off-chain).
    /// @return id       ID interno gerado para esse registro.
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

    /// @notice Recupera um registro pelo ID interno.
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

    /// @notice Retorna o último ID inserido (útil pra saber o tamanho atual).
    function lastId() external view returns (uint256) {
        return _lastId;
    }
}
