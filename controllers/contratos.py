from flask import Blueprint, render_template, request, make_response, flash, redirect, url_for
from weasyprint import HTML
from decimal import Decimal, InvalidOperation

contratos_bp = Blueprint('contratos', __name__, url_prefix='/contratos')

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
        data_evento = request.form.get('data_evento', '').strip()
        horario_evento = request.form.get('horario_evento', '').strip()
        local_evento = request.form.get('local_evento', '').strip()
        detalhes_adicionais = request.form.get('detalhes_adicionais', '').strip()
        valor_total_str = request.form.get('valor_total', '').strip()
        locacao_som = request.form.get('locacao_som', '').strip()

        # Validações básicas
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
            'Data do Evento': data_evento,
            'Horário do Evento': horario_evento,
            'Local do Evento': local_evento,
            'Valor Total': valor_total_str,
            'Locação de Som': locacao_som,
        }

        # Verifica se todos os campos obrigatórios estão preenchidos
        for label, valor in campos_obrigatorios.items():
            if not valor:
                flash(f"O campo '{label}' é obrigatório.", "danger")
                return redirect(url_for('contratos.gerar_contrato'))

        # Tenta converter o valor total em Decimal
        try:
            valor_total = Decimal(valor_total_str.replace(',', '.'))
        except (InvalidOperation, ValueError):
            flash("Valor Total inválido. Use um número, por exemplo: 1500.00", "danger")
            return redirect(url_for('contratos.gerar_contrato'))

        if valor_total <= 0:
            flash("O Valor Total deve ser maior que zero.", "danger")
            return redirect(url_for('contratos.gerar_contrato'))

        # Cálculo de valores antecipados e saldo final
        # Supondo 50% de antecipação e 50% antes do evento, conforme o contrato
        valor_antecipado = valor_total * Decimal('0.5')
        saldo_final = valor_total - valor_antecipado

        # Montagem do endereço completo
        endereco = f"{rua}, {numero}, {bairro}, {cidade}-{uf}, CEP: {cep}"

        # Renderização do template HTML do contrato para gerar o PDF
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
            valor_total=f"{valor_total:.2f}",
            locacao_som=locacao_som,
            valor_antecipado=f"{valor_antecipado:.2f}",
            saldo_final=f"{saldo_final:.2f}"
        )

        pdf = HTML(string=html_content).write_pdf()

        # Retorno do PDF ao usuário
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        # Nome do arquivo com o nome do contratante (limita espaços)
        nome_pdf = f"contrato_{nome_contratante.replace(' ', '_')}.pdf"
        response.headers['Content-Disposition'] = f'attachment; filename={nome_pdf}'

        flash("Contrato gerado com sucesso!", "success")
        return response

    else:
        # Método GET: Exibe o formulário para gerar o contrato
        return render_template('gerar_contrato.html')
