from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Lista para armazenar os eventos agendados
events = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agendar', methods=['POST'])
def agendar():
    tipo = request.form['tipo']
    titulo = request.form['titulo']
    data = request.form['data']
    hora = request.form['hora']
    descricao = request.form['descricao']

    evento = {
        'tipo': tipo,
        'titulo': titulo,
        'data': data,
        'hora': hora,
        'descricao': descricao
    }

    events.append(evento)
    return redirect(url_for('schedule'))

@app.route('/schedule')
def schedule():
    return render_template('schedule.html', events=events)

if __name__ == '__main__':
    app.run(debug=True)
