document.addEventListener('DOMContentLoaded', () => {
    // Função para atualizar a data e hora atuais no topo da página
    const updateDateTime = () => {
        const currentDatetimeEl = document.getElementById('current-datetime');
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
    };

    // Atualizar data e hora imediatamente e a cada minuto
    updateDateTime();
    setInterval(updateDateTime, 60000);

    // Selecionar todos os cartões de eventos
    const eventCards = document.querySelectorAll('.event-card');
    const today = new Date(); // Data atual

    // Formatar datas e aplicar destaques visuais com base na proximidade
    eventCards.forEach(card => {
        const eventDateStr = card.dataset.eventDate;
        const eventTimeStr = card.dataset.eventTime;
        const isWeekly = card.dataset.eventWeekly === 'true'; // Verificar se o evento é semanal
        const eventDate = new Date(eventDateStr);

        // Formatar data para o padrão dd/mm/yyyy
        const formattedDate = eventDate.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
        });

        const dateElement = card.querySelector('.card-text strong');
        if (dateElement) {
            dateElement.textContent = `Data: ${formattedDate} às ${eventTimeStr}`;
        }

        // Adicionar a flag "Semanal" para eventos recorrentes
        if (isWeekly) {
            const weeklyBadge = document.createElement('span');
            weeklyBadge.className = 'badge bg-info text-dark ms-2';
            weeklyBadge.textContent = 'Semanal';
            card.querySelector('.card-header').appendChild(weeklyBadge);
        }

        // Calcular diferença em dias
        const diffInDays = Math.ceil((eventDate - today) / (1000 * 60 * 60 * 24));

        // Aplicar classes com base na proximidade
        if (diffInDays > 3) {
            card.classList.add('bg-success', 'text-light'); // Verde para eventos distantes
        } else if (diffInDays <= 3 && diffInDays >= 0) {
            card.classList.add('bg-danger', 'text-light'); // Vermelho para eventos próximos
        }
    });

    // Animação de entrada dos cartões
    eventCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.opacity = '1'; // Tornar o cartão visível
            card.style.transform = 'translateY(0)'; // Remover a translação vertical
        }, index * 150); // Intervalo de 150ms entre os cartões
    });

    // Efeito ao passar o mouse nos cartões
    eventCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'scale(1.05)'; // Ampliação leve ao passar o mouse
            card.style.transition = 'transform 0.3s ease'; // Suavizar transição
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'scale(1)'; // Retornar ao tamanho original
        });
    });

    // Mostrar/ocultar opções de dias da semana para eventos recorrentes
    const repetirCheckbox = document.getElementById('repetir');
    const diasSemanaContainer = document.getElementById('dias-semana-container');

    if (repetirCheckbox) {
        repetirCheckbox.addEventListener('change', () => {
            diasSemanaContainer.style.display = repetirCheckbox.checked ? 'block' : 'none';
        });
    }

    // Lidar com exclusão de eventos no frontend
    const deleteButtons = document.querySelectorAll('.delete-event');
    deleteButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const confirmDelete = confirm('Tem certeza de que deseja excluir este evento da exibição?');
            if (confirmDelete) {
                button.closest('.event-card').remove();
            }
        });
    });

    // Lidar com marcação de eventos como realizados
    const doneButtons = document.querySelectorAll('.mark-as-done');
    doneButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const eventId = button.dataset.eventId;

            // Enviar requisição para mover evento para "realizados"
            fetch(`/realizado/${eventId}`, {
                method: 'POST',
            })
            .then(response => {
                if (response.ok) {
                    alert('Evento marcado como realizado!');
                    button.closest('.event-card').remove(); // Remover cartão da página
                } else {
                    alert('Erro ao marcar o evento como realizado. Tente novamente.');
                }
            });
        });
    });
});
