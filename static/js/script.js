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

    // Função para marcar evento como realizado
    const markAsDone = (event) => {
        const button = event.target.closest('.mark-as-done');
        if (!button) return;

        const eventId = button.getAttribute('data-event-id');
        fetch(`/realizado/${eventId}`, { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    const card = button.closest('.event-card');
                    if (card) card.remove(); // Remove o card da lista de eventos agendados
                } else {
                    console.error('Erro ao marcar como realizado');
                    alert('Não foi possível marcar o evento como realizado.');
                }
            })
            .catch(error => {
                console.error('Erro de conexão:', error);
                alert('Erro de conexão ao tentar marcar o evento como realizado.');
            });
    };

    // Função para excluir evento
    const deleteEvent = (event) => {
        const button = event.target.closest('.delete-event');
        if (!button) return;

        const eventId = button.getAttribute('data-event-id');
        fetch(`/excluir/${eventId}`, { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    const card = button.closest('.event-card');
                    if (card) card.remove(); // Remove o card da lista de eventos agendados
                } else {
                    console.error('Erro ao excluir evento');
                    alert('Não foi possível excluir o evento.');
                }
            })
            .catch(error => {
                console.error('Erro de conexão:', error);
                alert('Erro de conexão ao tentar excluir o evento.');
            });
    };

    // Adicionar eventos de clique para botões de "Realizado" e "Excluir"
    const markAsDoneButtons = document.querySelectorAll('.mark-as-done');
    markAsDoneButtons.forEach(button => {
        button.addEventListener('click', markAsDone);
    });

    const deleteEventButtons = document.querySelectorAll('.delete-event');
    deleteEventButtons.forEach(button => {
        button.addEventListener('click', deleteEvent);
    });

    // Animação de entrada para os cards
    const eventCards = document.querySelectorAll('.event-card');
    eventCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1'; // Tornar o cartão visível
            card.style.transform = 'translateY(0)'; // Remover a translação vertical
        }, index * 150); // Animação de entrada
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
