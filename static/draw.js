const socket = io();

// Mapeia números para letras do bingo
function getBingoLetter(n) {
  if (n <= 15) return 'B';
  if (n <= 30) return 'I';
  if (n <= 45) return 'N';
  if (n <= 60) return 'G';
  return 'O';
}

btnStart = document.getElementById('btn-start');
btnNext = document.getElementById('btn-next');
btnStop = document.getElementById('btn-stop');

btnStart.onclick = () => {
  tipo_sorteio = document.getElementById('tipo-sorteio-select').value;
  socket.emit('start_draw', { tipo_sorteio });
  document.getElementsByClassName('div-tipo-sorteio')[0].style.display = 'none';
  document.getElementById("na-boa-box").style.display = 'block';
  btnStart.disabled = true; // Desabilita o botão após iniciar o sorteio
  btnNext.disabled = false; // Habilita o botão de próximo número
  btnStop.disabled = false; // Habilita o botão de parar sorteio
  btnStart.classList.add("desactive");
  btnNext.classList.add("active");
  btnNext.classList.remove("desactive");
  btnStop.classList.remove("desactive");
  btnStop.classList.add("active");
};

btnNext.onclick = () => {
  socket.emit('next_number');
};

btnStop.onclick = () => {
  socket.emit('stop_draw');
  btnStart.disabled = false;
  btnNext.disabled = true;
  btnStop.disabled = true;
  btnStart.classList.remove("desactive");
  btnStart.classList.add("active");
  btnNext.classList.remove("active");
  btnNext.classList.add("desactive");
  btnStop.classList.add("desactive");
  btnStop.classList.remove("active");
};

socket.on('draw_number', ({ number }) => {
  const letter = getBingoLetter(number);
  const group = document.querySelector(`#group-${letter} .nums`);
  if (group) {
    const span = document.createElement('span');
    span.className = 'ball';
    span.textContent = number;
    group.appendChild(span);

    // Ordena os elementos após adicionar
    const allBalls = Array.from(group.querySelectorAll('.ball'));
    allBalls.sort((a, b) => parseInt(a.textContent) - parseInt(b.textContent));
    group.innerHTML = '';
    allBalls.forEach(el => group.appendChild(el));
  }

  // Mostra o número grande no centro
  const bigNumber = document.getElementById('last-number');
  if (bigNumber) {
    bigNumber.textContent = `${letter} ${number}`;
    bigNumber.style.display = 'block';
  }
});


socket.on('winner', data => {
  const winnerBox = document.getElementById('winner-box');
  winnerBox.innerHTML = `
        <div class="winner animated">
      🎉 <strong>${data.nome}</strong> venceu com a cartela <strong>#${data.cartela_id}</strong>!<br>
      <strong>Modo:</strong> ${data.tipo_vitoria.toUpperCase()}<br>
      Último número: <strong style="font-size: 2rem;">${data.numero_ganhador}</strong>
      <button id="btn-verificar-informacoes" style="background-color: var(--primary);" onclick="verificar_informacoes(${data.cartela_id})">Verificar Informações</button>
    </div>
  `;
  winnerBox.style.display = 'block';
  btnStart.classList.remove("desactive");
  btnStart.classList.add("active");
  btnNext.classList.remove("active");
  btnNext.classList.add("desactive");
  btnStop.classList.add("desactive");
  btnStop.classList.remove("active");
  socket.emit('stop_draw');
});
function verificar_informacoes(cartelaIdVencedora){
  socket.emit("verificar_informacoes", { cartela_id: cartelaIdVencedora });
  document.getElementById('comprador-modal').style.display = 'block';
}
socket.on('informacoes_comprador', comprador => {
  const cartelaIdVencedora = document.querySelector('.winner strong:nth-of-type(2)').textContent;
  document.getElementById('comprador-nome').textContent = comprador.nome || 'N/A';
  document.getElementById('comprador-endereco').textContent = comprador.endereco || 'N/A';
  document.getElementById('comprador-telefone').textContent = comprador.telefone || 'N/A';
  document.getElementById('comprador-cartela').textContent = cartelaIdVencedora || 'N/A';
});

socket.on('draw_started', () => {
  document.getElementById('last-number').style.display = 'none';
  document.getElementById('winner-box').style.display = 'none';

  // Limpa os números já sorteados
  document.querySelectorAll('.nums').forEach(div => div.innerHTML = '');
});

socket.on('draw_stopped', () => {
  document.getElementById('last-number').style.display = 'none';
  document.getElementById("na-boa-box").style.display = 'none';
  document.getElementById('btn-start').onclick = () => {
    window.location.reload();
  };
  document.getElementById('btn-start').disabled = false;
});

  socket.on('na_boa', ({ cartelas }) => {
    const naBoaBox = document.getElementById('na-boa-box');
    if (!naBoaBox) return;

    if (cartelas.length === 0) {
      naBoaBox.innerHTML = '<p>Ninguém está na boa ainda.</p>';
    } else {
      naBoaBox.innerHTML = `
        <h3>Cartelas na Boa 🎯</h3>
        <ul>
          ${cartelas.map(c => `<li><strong>${c.nome}</strong> (#${c.cartela_id}) falta o número <strong>${c.faltando}</strong></li>`).join('')}
        </ul>
      `;
    }
  });

