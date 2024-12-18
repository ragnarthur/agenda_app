
# Agenda Digital - Contratos Musicais

Este projeto consiste em um aplicativo web desenvolvido em **Python** e **Flask** para gerar contratos de prestação de serviços musicais de forma profissional e automatizada. Através de um formulário amigável, o usuário pode inserir todas as informações necessárias (dados do contratante, evento, valor total, etc.) e obter um contrato em formato PDF pronto para download.

## Demonstração

![Demonstração do Contrato em PDF](caminho/para/screenshot.png)

_Após preencher o formulário e clicar em "Gerar Contrato", o usuário faz o download imediato do PDF, que apresenta todos os valores formatados no padrão brasileiro (R$ 1.200,59), datas no formato DD/MM/YYYY e um layout profissional._

## Principais Funcionalidades

- **Formulário Interativo:**  
  Campos para contratante (nome, CPF/CNPJ, endereço, telefone, celular), dados do evento (tipo, data, horário, local), detalhes adicionais e valor total formatado com máscara monetária.
  
- **Validação de Campos:**  
  Todos os campos essenciais possuem validação, garantindo que não haja campos obrigatórios vazios.
  
- **Formatação de Valores Monetários:**  
  Utiliza a biblioteca **IMask.js** no front-end para formatar o valor total no padrão brasileiro com prefixo “R$”, vírgula para decimais e ponto para milhares.
  
- **Formatação de Datas:**  
  Data do evento convertida de YYYY-MM-DD (padrão input date) para DD/MM/YYYY.
  
- **Geração de PDF Profissional:**  
  Utiliza **WeasyPrint** para converter o template HTML em PDF de forma elegante e pronta para impressão.
  
- **Contratos Jurídicos e Profissionais:**  
  O contrato gerado apresenta cláusulas detalhadas sobre o objeto, pagamento, cancelamento, rescisão e foro, além de um layout moderno e tipografia refinada.

## Tecnologias Utilizadas

- **Back-end:**  
  - [Python 3](https://www.python.org/)  
  - [Flask](https://flask.palletsprojects.com/)  
  - [WeasyPrint](https://weasyprint.org/) para geração de PDFs
  
- **Front-end:**  
  - [Bootstrap 5](https://getbootstrap.com/) para layout responsivo  
  - [IMask.js](https://imask.js.org/) para máscaras de input financeiro  
  - HTML, CSS e JS puros para estrutura, estilo e interações
  
- **Outras Dependências:**  
  - [Decimal (Python)](https://docs.python.org/3/library/decimal.html) para precisão monetária  
  - [Datetime (Python)](https://docs.python.org/3/library/datetime.html) para formatação de datas

## Como Executar o Projeto Localmente

1. **Clonar o Repositório:**  
   ```bash
   git clone https://github.com/seuusuario/agenda-contratos-musicais.git
   cd agenda-contratos-musicais
   ```
