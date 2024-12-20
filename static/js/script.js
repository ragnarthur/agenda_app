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

    // Função para destacar os cards com base na proximidade da data
    const highlightCards = () => {
        const today = new Date();
        const eventCards = document.querySelectorAll('.event-card');

        eventCards.forEach(card => {
            const eventDateStr = card.dataset.eventDate; // Data no formato YYYY-MM-DD
            const eventDate = new Date(eventDateStr);

            // Calcula a diferença em dias
            const diffInTime = eventDate - today;
            const diffInDays = Math.ceil(diffInTime / (1000 * 60 * 60 * 24));

            // Remove classes de estilo de proximidade
            card.classList.remove('bg-success');

            // Adiciona a classe bg-success apenas para eventos dentro de 5 dias
            if (diffInDays <= 5 && diffInDays >= 0) {
                card.classList.add('bg-success'); // Verde para eventos próximos
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
        fetch(`/eventos/realizado/${eventId}`, { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    const card = button.closest('.event-card');
                    if (card) {
                        card.addEventListener('transitionend', () => {
                            card.remove();
                            reorganizeCards();
                        });
                        card.style.transition = 'opacity 0.5s, transform 0.5s';
                        card.style.opacity = '0';
                        card.style.transform = 'scale(0.9)';
                    }
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
        fetch(`/eventos/excluir/${eventId}`, { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    const card = button.closest('.event-card');
                    if (card) {
                        card.addEventListener('transitionend', () => {
                            card.remove();
                            reorganizeCards();
                        });
                        card.style.transition = 'opacity 0.5s, transform 0.5s';
                        card.style.opacity = '0';
                        card.style.transform = 'scale(0.9)';
                    }
                } else if (response.status === 404) {
                    alert('Evento não encontrado.');
                } else {
                    alert('Não foi possível excluir o evento.');
                }
            })
            .catch(error => {
                console.error('Erro de conexão:', error);
                alert('Erro de conexão ao tentar excluir o evento.');
            });
    };

    // Função para reorganizar os cartões após exclusão
    const reorganizeCards = () => {
        const row = document.querySelector('.row');
        if (row) {
            const cards = Array.from(row.children);
            cards.forEach((card, index) => {
                card.style.transition = 'transform 0.3s ease';
                card.style.order = index;
            });
        }
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
