import os
import random
import json
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    send_file, flash
)
from flask_socketio import SocketIO, emit
from weasyprint import HTML
from models import Session, Comprador, Cartela # type: ignore
from sqlalchemy.orm import joinedload
from threading import Lock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secrettemplate'
socketio = SocketIO(app)

draw_lock = Lock()
draw_queue = []
drawn_set = set()
cartela_data = []
current_draw_type = 'cartela'


def init_draw():
    global draw_queue, drawn_set, cartela_data
    draw_queue = list(range(1, 76))
    random.shuffle(draw_queue)
    drawn_set = set()

    session = Session()
    cartela_data = []
    for c in session.query(Cartela).all():
        flat = {n for row in c.numbers for n in row if isinstance(n, int)}
        comprador = session.get(Comprador, c.id_comprador)
        cartela_data.append({
            'cartela_id': c.id,
            'nome': comprador.nome,
            'set': flat,
            'grid': c.numbers,
            'ganhou': False
        })
    session.close()


@socketio.on('start_draw')
def on_start_draw(data=None):
    global current_draw_type
    draw_type = data.get('tipo_sorteio') if data else 'cartela'
    current_draw_type = draw_type
    with draw_lock:
        init_draw()
    emit('draw_started')


@socketio.on('next_number')
def on_next_number():
    global draw_queue, drawn_set
    with draw_lock:
        if not draw_queue:
            emit('draw_finished')
            return
        num = draw_queue.pop(0)
        drawn_set.add(num)

    emit('draw_number', {'number': num})
    check_na_boa()
    for cd in cartela_data:
        if not cd['ganhou'] and check_win_condition(cd):
            cd['ganhou'] = True
            emit('winner', {
                'cartela_id': cd['cartela_id'],
                'nome': cd['nome'],
                'numero_ganhador': num,
                'tipo_vitoria': current_draw_type
            })
            break


def check_na_boa():
    na_boa = []
    for cd in cartela_data:
        if cd['ganhou']:
            continue

        grid = cd['grid']
        faltando = None

        if current_draw_type == 'cartela':
            restantes = cd['set'] - drawn_set
            if len(restantes) == 1:
                faltando = list(restantes)[0]

        elif current_draw_type == 'linha/coluna':
            for row in grid:
                numeros = [n for n in row if isinstance(n, int)]
                restantes = set(numeros) - drawn_set
                if len(restantes) == 1:
                    faltando = list(restantes)[0]
                    break
            for i in range(5):
                col = [grid[j][i] for j in range(5)]
                numeros = [n for n in col if isinstance(n, int)]
                restantes = set(numeros) - drawn_set
                if len(restantes) == 1:
                    faltando = list(restantes)[0]
                    break

        elif current_draw_type == 'bola':
            continue

        if faltando is not None:
            na_boa.append({
                'cartela_id': cd['cartela_id'],
                'nome': cd['nome'],
                'faltando': faltando
            })

    emit('na_boa', {'cartelas': na_boa}, broadcast=True)


def check_win_condition(cd):
    grid = list(cd['grid'])
    flat = cd['set']
    if current_draw_type == 'cartela':
        return cd['set'].issubset(drawn_set)
    elif current_draw_type == 'linha/coluna':
        for row in grid:
            if all(n in drawn_set or n == 'BINGO' for n in row):
                return True
        for col in zip(*grid):
            if all(n in drawn_set or n == 'BINGO' for n in col):
                return True
    elif current_draw_type == 'bola':
        if any(n in drawn_set for n in flat):
            return True
    return False


@socketio.on('stop_draw')
def on_stop_draw():
    global draw_queue
    with draw_lock:
        draw_queue = []
    emit('draw_stopped')


@socketio.on("verificar_informacoes")
def pegarInformacoes(data):
    session = Session()
    cartela_id = data.get("cartela_id") if data else 0

    cartela = session.query(Cartela)\
        .options(joinedload(Cartela.comprador))\
        .filter_by(id=cartela_id).first()

    comprador = cartela.comprador if cartela and cartela.comprador else None
    comprador_dict = None
    if comprador:
        comprador_dict = {
            "id": comprador.id,
            "nome": comprador.nome,
            "telefone": comprador.telefone,
            "endereco": comprador.endereco
        }
    emit("informacoes_comprador", comprador_dict)
    session.close()


def gerar_cartela():
    ranges = {
        0: list(range(1, 16)),
        1: list(range(16, 31)),
        2: list(range(31, 46)),
        3: list(range(46, 61)),
        4: list(range(61, 76)),
    }
    cols = []
    for i in range(5):
        nums = random.sample(ranges[i], 5)
        cols.append(nums)
    grid = [list(r) for r in zip(*cols)]
    grid[2][2] = 'BINGO'
    return grid


@app.route('/')
def index():
    session = Session()
    cartelas = (session
                .query(Cartela)
                .options(joinedload(Cartela.comprador))
                .all())
    session.close()
    return render_template('index.html', cartelas=cartelas)


@socketio.on("remover_todas_cartelas")
def remover_todas_cartelas():
    session = Session()
    deleted = session.query(Cartela).delete() 
    session.commit()
    session.close()
    emit("removeu_todas_cartelas",deleted)
    return


@app.route('/criar_cartela', methods=['POST'])
def criar_cartela():
    nome = request.form['nome']
    endereco = request.form['endereco']
    telefone = request.form['telefone']

    session = Session()
    comprador = session.query(Comprador)\
        .filter_by(nome=nome, telefone=telefone).first()
    if not comprador:
        comprador = Comprador(nome, telefone, endereco)
        session.add(comprador)
        session.commit()

    matrix = gerar_cartela()

    cartela = Cartela(comprador.id, matrix, '')
    session.add(cartela)
    session.commit()
    cartela_id = cartela.id

    html = render_template(
        'cartela.html',
        cartela=matrix,
        cartela_id=cartela_id,
        comprador_nome=comprador.nome 
    )

    pdf_io = BytesIO()
    HTML(string=html).write_pdf(pdf_io, stylesheets=[], presentational_hints=True)
    pdf_io.seek(0)

    os.makedirs('cartelas', exist_ok=True)
    filename = f'cartela_{comprador.id}_{cartela_id}.pdf'
    path = os.path.join('cartelas', filename)
    with open(path, 'wb') as f:
        f.write(pdf_io.read())
    pdf_io.seek(0)

    cartela.pdf_path = path
    session.commit()
    session.close()

    socketio.emit('new_cartela', {'id': cartela_id})
    flash('Cartela criada com sucesso!')
    return redirect(url_for('index'))


@app.route('/gerar_pdf_todas_cartelas')
def gerar_pdf_todas_cartelas():
    session = Session()
    cartelas = session.query(Cartela).options(joinedload(Cartela.comprador)).all()
    html_completo = ""
    for cartela in cartelas:
        html = render_template(
            'cartela.html',
            cartela=cartela.numbers,
            cartela_id=cartela.id,
            comprador_nome=cartela.comprador.nome
        )
        html_completo += f'<div style="page-break-after: always;">{html}</div>'
    session.close()

    pdf_io = BytesIO()
    HTML(string=html_completo).write_pdf(pdf_io)
    pdf_io.seek(0)

    return send_file(
        pdf_io,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='todas_cartelas.pdf'
    )


@socketio.on('connect')
def on_connect():
    emit('message', {'data': 'Conectado!'})


@app.route('/draw')
def draw_page():
    return render_template('sorteio.html')


@app.route('/view/<int:cartela_id>')
def view_cartela(cartela_id):
    session = Session()
    cartela = session.query(Cartela).get(cartela_id)
    session.close()
    return send_file(cartela.pdf_path, mimetype='application/pdf')


@app.route('/download/<int:cartela_id>')
def download(cartela_id):
    session = Session()
    cartela = session.query(Cartela).get(cartela_id)
    session.close()
    return send_file(cartela.pdf_path, as_attachment=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)