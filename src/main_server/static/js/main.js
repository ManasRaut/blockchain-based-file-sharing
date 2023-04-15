const accounts = [];
let fileShare = {};
let contract = {};
let filesList = [];

async function requestAccounts() {
  if (typeof window === "undefined") return;
  return window.ethereum
    ?.request({ method: "eth_requestAccounts" })
    .catch((err) => console.log(err));
}

function closeUploadModal() {
  document.getElementById("uploadModal").style.display = "none";
}

function showUploadModal() {
  document.getElementById("uploadModal").style.display = "block";
}

function closeDownloadModal() {
  document.getElementById("downloadModal").style.display = "none";
}

function showDownloadModal() {
  document.getElementById("downloadModal").style.display = "block";
}

function uploadFile(e) {
  e.preventDefault();
  let formData = new FormData(e.target);
  let fileKey = formData.get("file_key");
  let file = formData.get("file");
  fetch("/add_file", {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      contract.methods
        .uploadFile(data.hash, file.name, fileKey)
        .send({ from: accounts[0] })
        .on("receipt", (r) => {
          alert("File uploaded successfully");
          getFilesList();
        });
    })
    .catch((err) => console.log(err, "Failed"));
}

function downloadFile(e) {
  e.preventDefault();
  let formData = new FormData(e.target);
  fetch("/retrieve_file", {
    method: "POST",
    body: formData,
  })
    .then((res) => {
      const reader = res.body.getReader();
      return new ReadableStream({
        start(controller) {
          return pump();
          function pump() {
            return reader.read().then(({ done, value }) => {
              // When no more data needs to be consumed, close the stream
              if (done) {
                controller.close();
                return;
              }
              // Enqueue the next data chunk into our target stream
              controller.enqueue(value);
              return pump();
            });
          }
        },
      });
    })
    .then((stream) => new Response(stream))
    .then((response) => response.blob())
    .then((blob) => {
      const file = new Blob([blob]);
      const a = document.createElement("a");
      const url = URL.createObjectURL(file);
      a.href = url;
      a.target = "_blank";
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }, 0);
    })
    .catch((err) => console.error(err));
}

async function initializeContractLocal() {
  if (window.ethereum) this.web3 = new Web3(window.ethereum);
  else if (window.web3) this.web3 = new Web3(window.web3.currentProvider);
  if (!this.web3) throw "Web3 not initialized";

  const networkId = await this.web3.eth.net.getId();
  const networkData = fileShare.networks[networkId];
  if (networkData) {
    contract = new this.web3.eth.Contract(fileShare.abi, networkData.address);
  }
  getFilesList();
}

async function getFilesList() {
  const filesCount = await contract.methods.fileCount().call();
  filesList = [];
  for (var i = filesCount; i >= 1; i--) {
    const file = await contract.methods.files(i).call();
    filesList.push({
      fileHash: file.fileHash,
      fileName: file.fileName,
      fileKey: file.fileKey,
      owner: file.owner,
    });
  }
  filesList.reverse();
  let content = "";
  filesList.forEach((f, fIndex) => {
    content += `<div class="card"> 
    <div class="card-header">
      <h4><b>Block ${fIndex}</b></h4>
    </div>
    <div class="card-body">
      <ul class="list-group list-group-flush">
        <li class="list-group-item">
          <b>File name</b> :  ${f.fileName}
        </li>
        <li class="list-group-item"><b>Owner</b> : ${f.owner}</li>
        <li class="list-group-item text text-primary"><b>Shared file</b> : ${f.fileHash}</li>               
      </ul>
    </div>   
  </div>`;
  });
  document.getElementById("block_list").innerHTML = content;
  document.getElementById("fileCounter").innerHTML = filesList.length;
}

window.addEventListener("load", async () => {
  document.getElementById("uploadForm").addEventListener("submit", (e) => uploadFile(e));
  document
    .getElementById("downloadForm")
    .addEventListener("submit", (e) => downloadFile(e));

  const res = await fetch("http://127.0.0.1:5111/static/abis/FileShare.json");
  fileShare = await res.json();

  requestAccounts().then((res) =>
    res.forEach((acc) => {
      accounts.push(acc);
      initializeContractLocal();
    })
  );
});
