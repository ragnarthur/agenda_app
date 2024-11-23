document.addEventListener('DOMContentLoaded', () => {
    // Função para atualizar a data e hora no topo da página
    const updateDateTime = () => {
        const currentDatetimeEl = document.getElementById('current-datetime');
        if (currentDatetimeEl) {
            const now = new Date();
            const options = {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
            };
            currentDatetimeEl.textContent = now.toLocaleDateString('pt-BR', options);
        }
    };

    // Atualizar data e hora imediatamente e a cada minuto
    updateDateTime();
    setInterval(updateDateTime, 60000);

    // Função para destacar os cards com base na data
    const highlightCards = () => {
        const today = new Date();
        const eventCards = document.querySelectorAll('.event-card');

        eventCards.forEach(card => {
            const eventDateStr = card.dataset.eventDate;
            const eventDate = new Date(eventDateStr);

            // Calcula a diferença em dias
            const diffInTime = eventDate - today;
            const diffInDays = Math.ceil(diffInTime / (1000 * 60 * 60 * 24));

            // Remove classes antigas
            card.classList.remove('bg-danger', 'bg-success');

            // Adiciona classes com base na proximidade
            if (diffInDays <= 3 && diffInDays >= 0) {
                card.classList.add('bg-danger'); // Destaque para eventos próximos
            } else if (diffInDays > 3) {
                card.classList.add('bg-success'); // Neutro para eventos distantes
            }
        });
    };

    // Chamar a função para destacar os cards
    highlightCards();

    // Outras funcionalidades
    const eventCards = document.querySelectorAll('.event-card');
    eventCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1'; // Tornar o cartão visível
            card.style.transform = 'translateY(0)'; // Remover a translação vertical
        }, index * 150); // Animação de entrada
    });

    eventCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'scale(1.05)'; // Ampliação leve ao passar o mouse
            card.style.transition = 'transform 0.3s ease'; // Suavizar transição
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'scale(1)'; // Retornar ao tamanho original
        });
    });

    // Máscara para formatar valores monetários (R$)
    const applyCurrencyMask = (input) => {
        let value = input.value.replace(/\D/g, ''); // Remove caracteres não numéricos
        if (value) {
            value = (parseFloat(value) / 100).toFixed(2); // Converte para float e mantém 2 casas decimais
            value = value.replace('.', ','); // Substitui ponto por vírgula
            value = value.replace(/\B(?=(\d{3})+(?!\d))/g, '.'); // Adiciona pontos de milhar
            input.value = value;
        } else {
            input.value = ''; // Garante que o campo fica vazio se não houver valor
        }
    };

    // Selecionar todos os inputs financeiros
    const valueInputs = document.querySelectorAll('#valor_bruto, #pagamento_musicos, #locacao_som, #outros_custos');

    // Aplicar a máscara nos campos durante a digitação
    valueInputs.forEach((input) => {
        input.addEventListener('input', () => applyCurrencyMask(input));
    });

    // Garantir a formatação correta ao carregar a página (valores existentes)
    valueInputs.forEach((input) => {
        if (input.value) {
            applyCurrencyMask(input);
        }
    });
});
