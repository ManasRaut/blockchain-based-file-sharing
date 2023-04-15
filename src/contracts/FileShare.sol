pragma solidity >=0.4.22 <0.9.0;

contract FileShare {
    string public name = "FileShare";
    uint256 public fileCount = 0;

    mapping(uint256 => File) public files;

    struct File {
        string fileHash;
        string fileName;
        string fileKey;
        address owner;
    }

    event FileUploaded(
        string fileHash,
        string fileName,
        string fileKey,
        address owner
    );

    function uploadFile(
        string memory _fileHash,
        string memory _fileName,
        string memory _fileKey
    ) public {
        require(bytes(_fileName).length > 0);
        require(msg.sender != address(0));

        fileCount++;

        files[fileCount] = File(_fileHash, _fileName, _fileKey, msg.sender);

        emit FileUploaded(_fileHash, _fileName, _fileKey, msg.sender);
    }
}
