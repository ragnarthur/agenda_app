from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Aluno
from decimal import Decimal, InvalidOperation

alunos_bp = Blueprint('alunos', __name__, url_prefix='/alunos')

@alunos_bp.route('/adicionar', methods=['GET', 'POST'])
def adicionar_aluno():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        cpf_cnpj = request.form.get('cpf_cnpj', '').strip()
        endereco = request.form.get('endereco', '').strip()
        tipo_aula = request.form.get('tipo_aula', '').strip()    # teclado, guitarra, violao
        modalidade = request.form.get('modalidade', '').strip()  # semanal, avulsa

        # Validações básicas
        campos_obrigatorios = {
            'Nome': nome,
            'CPF/CNPJ': cpf_cnpj,
            'Endereço': endereco,
            'Tipo de Aula': tipo_aula,
            'Modalidade': modalidade,
        }

        for label, valor in campos_obrigatorios.items():
            if not valor:
                flash(f"O campo '{label}' é obrigatório.", "danger")
                return redirect(url_for('alunos.adicionar_aluno'))
        
        # Validando tipo de aula
        if tipo_aula not in ['teclado', 'guitarra', 'violao']:
            flash("Tipo de aula inválido. Escolha entre teclado, guitarra ou violao.", "danger")
            return redirect(url_for('alunos.adicionar_aluno'))

        # Validando modalidade
        if modalidade not in ['semanal', 'avulsa']:
            flash("Modalidade inválida. Escolha entre semanal ou avulsa.", "danger")
            return redirect(url_for('alunos.adicionar_aluno'))

        novo_aluno = Aluno(
            nome=nome,
            cpf_cnpj=cpf_cnpj,
            endereco=endereco,
            tipo_aula=tipo_aula,
            modalidade=modalidade
        )
        db.session.add(novo_aluno)
        db.session.commit()

        flash("Aluno cadastrado com sucesso!", "success")
        return redirect(url_for('alunos.adicionar_aluno'))  # Pode redirecionar para uma lista de alunos se desejar.

    return render_template('adicionar_aluno.html')

# Nova rota API para listar alunos em JSON
@alunos_bp.route('/api/listar', methods=['GET'])
def api_listar_alunos():
    alunos = Aluno.query.all()
    alunos_data = []
    for aluno in alunos:
        alunos_data.append({
            "id": aluno.id,
            "nome": aluno.nome,
            "cpf_cnpj": aluno.cpf_cnpj,
            "endereco": aluno.endereco,
            "tipo_aula": aluno.tipo_aula,
            "modalidade": aluno.modalidade
        })

    return {"alunos": alunos_data}, 200
