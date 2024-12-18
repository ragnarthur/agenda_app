from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from weasyprint import HTML
from decimal import Decimal, InvalidOperation
from datetime import datetime

contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')

def formata_valor_brl(valor_decimal):
    # Converte Decimal para string no formato 1.200,59
    # 1. Converte para string com duas casas decimais padrão (1200.59)
    s = f"{valor_decimal:.2f}"
    # 2. Divide entre parte inteira e decimal
    parte_inteira, parte_decimal = s.split('.')
    # 3. Adiciona separador de milhar na parte inteira
    # Aqui usamos um método simples para milhares:
    # Inserimos pontos a cada 3 dígitos a partir da direita
    inteiro_formatado = ''
    while len(parte_inteira) > 3:
        inteiro_formatado = '.' + parte_inteira[-3:] + inteiro_formatado
        parte_inteira = parte_inteira[:-3]
    inteiro_formatado = parte_inteira + inteiro_formatado
    # 4. Reconstrói no formato brasileiro R$ X.XXX,XX
    return f"R$ {inteiro_formatado},{parte_decimal}"

@contratos_bp.route('/gerar', methods=['GET', 'POST'])
def gerar_contrato():
    if request.method == 'POST':
        # Captura dos dados do formulário
        nome_contratante = request.form.get('nome_contratante', '').strip()
        cpf_cnpj = request.form.get('documento', '').strip()
        rua = request.form.get('rua', '').strip()
        numero = request.form.get('numero', '').strip()
        bairro = request.form.get('bairro', '').strip()
        cidade = request.form.get('cidade', '').strip()
        uf = request.form.get('uf', '').strip()
        cep = request.form.get('cep', '').strip()
        telefone = request.form.get('telefone', '').strip()
        celular = request.form.get('celular', '').strip()
        tipo_evento = request.form.get('tipo_evento', '').strip()
        data_evento_str = request.form.get('data_evento', '').strip()
        horario_evento = request.form.get('horario_evento', '').strip()
        local_evento = request.form.get('local_evento', '').strip()
        detalhes_adicionais = request.form.get('detalhes_adicionais', '').strip()
        valor_total_str = request.form.get('valor_total', '').strip()
        locacao_som = request.form.get('locacao_som', '').strip()

        campos_obrigatorios = {
            'Nome do Contratante': nome_contratante,
            'CPF/CNPJ': cpf_cnpj,
            'Rua': rua,
            'Número': numero,
            'Bairro': bairro,
            'Cidade': cidade,
            'UF': uf,
            'CEP': cep,
            'Telefone': telefone,
            'Celular': celular,
            'Tipo de Evento': tipo_evento,
            'Data do Evento': data_evento_str,
            'Horário do Evento': horario_evento,
            'Local do Evento': local_evento,
            'Valor Total': valor_total_str,
            'Locação de Som': locacao_som,
        }

        for label, valor in campos_obrigatorios.items():
            if not valor:
                flash(f"O campo '{label}' é obrigatório.", "danger")
                return redirect(url_for('contratos.gerar_contrato'))

        # Formata a data do evento
        if data_evento_str:
            try:
                data_evento_date = datetime.strptime(data_evento_str, '%Y-%m-%d').date()
                data_evento = data_evento_date.strftime('%d/%m/%Y')
            except ValueError:
                data_evento = data_evento_str
        else:
            data_evento = data_evento_str

        # Ajusta valor total do formato "R$ 1.200,59" para "1200.59"
        if valor_total_str.startswith('R$ '):
            valor_total_str = valor_total_str[3:]
        valor_total_str = valor_total_str.replace('.', '').replace(',', '.')

        try:
            valor_total = Decimal(valor_total_str)
        except (InvalidOperation, ValueError):
            flash("Valor Total inválido. Use um número, por exemplo: 1500.00", "danger")
            return redirect(url_for('contratos.gerar_contrato'))

        if valor_total <= 0:
            flash("O Valor Total deve ser maior que zero.", "danger")
            return redirect(url_for('contratos.gerar_contrato'))

        valor_antecipado = valor_total * Decimal('0.5')
        saldo_final = valor_total - valor_antecipado

        endereco = f"{rua}, {numero}, {bairro}, {cidade}-{uf}, CEP: {cep}"

        # Formata valores no padrão brasileiro para o PDF
        valor_total_brl = formata_valor_brl(valor_total)
        valor_antecipado_brl = formata_valor_brl(valor_antecipado)
        saldo_final_brl = formata_valor_brl(saldo_final)

        html_content = render_template(
            'contrato_modelo.html',
            nome_contratante=nome_contratante,
            cpf_cnpj=cpf_cnpj,
            endereco=endereco,
            telefone=telefone,
            celular=celular,
            tipo_evento=tipo_evento,
            data_evento=data_evento,
            horario_evento=horario_evento,
            local_evento=local_evento,
            detalhes_adicionais=detalhes_adicionais,
            valor_total=valor_total_brl,
            locacao_som=locacao_som,
            valor_antecipado=valor_antecipado_brl,
            saldo_final=saldo_final_brl
        )

        pdf = HTML(string=html_content).write_pdf()

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        nome_pdf = f"contrato_{nome_contratante.replace(' ', '_')}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename={nome_pdf}'

        flash("Contrato gerado com sucesso!", "success")
        return response

    else:
        return render_template('gerar_contrato.html')
