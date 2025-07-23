const socket = io();

socket.on('message', data => {
  console.log(data.data);
});


// Garante que o DOM esteja carregado
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.print-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const cartelaId = btn.getAttribute('data-id');
      printCartela(cartelaId);
    });
  });
});

// Se ainda não tiver, a função printCartela:
function printCartela(cartelaId) {
  const url = `/view/${cartelaId}`;
  const printWindow = window.open(url);
  printWindow.addEventListener('load', () => {
    printWindow.focus();
    printWindow.print();
  }, { once: true });
}

function removerTodasCartelas() {
  if (window.confirm("Você tem certeza que deseja remover todas as cartelas?")) {
    socket.emit("remover_todas_cartelas");
  }
}
document.addEventListener('DOMContentLoaded', () => {
  const cardcontainer = document.getElementsByClassName("cards-container")[0];
  if (cardcontainer && cardcontainer.childElementCount <= 0) {
    const rmvButton = document.getElementById("btn-remover-todas-cartelas");
    if (rmvButton) {
      rmvButton.style.display = "none";
    }
  }
});

socket.on("removeu_todas_cartelas", deleted => {
  window.alert(`Todas as ${deleted} cartelas foram removidas.`);
  window.location.reload();
});

