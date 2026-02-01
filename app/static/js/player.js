function toggleReplyForm(id) {
    var form = document.getElementById(id);
    if (form.style.display === "none") {
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}

function deleteComment(commentId) {
    if (!confirm("Tem certeza que deseja excluir este comentário? Esta ação não pode ser desfeita.")) {
        return;
    }

    fetch(`/course/comment/${commentId}`, { // Atenção à URL que você definiu no Python
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Remove o elemento HTML da tela suavemente
            const commentElement = document.getElementById(`comment-${commentId}`);
            if (commentElement) {
                commentElement.style.opacity = '0';
                setTimeout(() => {
                    commentElement.remove();
                }, 300); // Aguarda a animação visual antes de remover
            }
        } else {
            alert("Erro ao excluir: " + data.message);
        }
    })
    .catch(err => {
        console.error("Erro:", err);
        alert("Erro de conexão ao tentar excluir.");
    });
}

document.addEventListener("DOMContentLoaded", function() {
    const video = document.querySelector("video");
    
    if (!video) return;
    const lessonId = video.dataset.lessonId;
    let markedAsComplete = video.dataset.completed === 'true';
    
    
    video.ontimeupdate = function() {
        // Evita disparar várias vezes se já marcou
        if (markedAsComplete) return;

        // Calcula porcentagem
        if (video.duration > 0) {
            const percentage = (video.currentTime / video.duration) * 100;
            
            // Se passou de 80%
            if (percentage >= 80) {
                markedAsComplete = true; // Trava para não enviar de novo
                markLessonComplete(lessonId);
            }
        }
    };

    const mainCommentForm = document.getElementById('comment-form');
    const commentsList = document.getElementById('comments-list');
    const noCommentsMsg = document.getElementById('no-comments-msg');

    if (mainCommentForm) {
        mainCommentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleCommentSubmit(this, false);
        });
    }

    function markLessonComplete(id) {
        fetch(`/course/lesson/${id}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                // Atualiza Visualmente a Sidebar na hora
                const icon = document.getElementById(`status-icon-${id}`);
                if(icon) {
                    icon.className = "fas fa-check-circle";
                    icon.style.color = "var(--success-color)";
                }
                console.log("Aula concluída! Progresso atualizado.");
            }
        })
        .catch(err => console.error("Erro ao marcar progresso:", err));
    }
    const replyForms = document.querySelectorAll('.reply-form');
    replyForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            handleCommentSubmit(this, true);
        });
    });

    // Função Genérica para Enviar Formulário
    function handleCommentSubmit(formElement, isReply) {
        const formData = new FormData(formElement);
        const actionUrl = formElement.action;
        const submitBtn = formElement.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;

        // UI de carregamento
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando...";

        fetch(actionUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const badgeHtml = data.is_instructor 
                    ? `<span class="badge" style="background-color: var(--primary-color); color: white; font-size: 0.7rem; margin-left: 5px;">Instrutor</span>` 
                    : '';

                if (isReply) {
                    // LÓGICA PARA INSERIR RESPOSTA
                    const parentId = data.parent_id;
                    // Encontra o item de comentário pai
                    const parentContainer = document.getElementById(`reply-form-${parentId}`).parentElement;
                    
                    // Procura a lista de replies. Se não existir, cria.
                    let repliesList = parentContainer.querySelector('.replies-list');
                    if (!repliesList) {
                        repliesList = document.createElement('div');
                        repliesList.className = 'replies-list';
                        repliesList.style.cssText = "margin-left: 40px; margin-top: 15px; border-left: 2px solid #e2e8f0; padding-left: 15px; width: 100%;";
                        parentContainer.appendChild(repliesList);
                    }

                    const newReplyHtml = `
                        <div style="display: flex; gap: 10px; margin-bottom: 10px; animation: fadeIn 0.5s;">
                            <div class="comment-avatar" style="width: 30px; height: 30px; font-size: 0.8rem;">
                                ${data.user_initial}
                            </div>
                            <div>
                                <div style="font-weight: 600; font-size: 0.85rem;">
                                    ${data.user_name} ${badgeHtml}
                                </div>
                                <p style="color: var(--dark-color); font-size: 0.95rem;">${data.content}</p>
                            </div>
                        </div>
                    `;
                    repliesList.insertAdjacentHTML('beforeend', newReplyHtml);
                    
                    // Fecha o formulário de resposta
                    toggleReplyForm(`reply-form-${parentId}`);

                } else {
                    // LÓGICA PARA INSERIR COMENTÁRIO PRINCIPAL
                    if (noCommentsMsg) noCommentsMsg.style.display = 'none';

                    const newCommentHtml = `
                    <div class="comment-item" style="flex-direction: column; align-items: flex-start; gap: 0; animation: fadeIn 0.5s;">
                        <div style="display: flex; gap: 15px; width: 100%;">
                            <div class="comment-avatar">${data.user_initial}</div>
                            <div style="flex: 1;">
                                <div style="font-weight: 600; font-size: 0.9rem;">
                                    ${data.user_name} ${badgeHtml}
                                </div>
                                <div style="font-size: 0.8rem; color: var(--gray-color); margin-bottom: 5px;">
                                    ${data.created_at}
                                </div>
                                <p style="color: var(--dark-color);">${data.content}</p>
                                <small style="color: var(--gray-color);">Atualize a página para responder agora</small>
                            </div>
                        </div>
                    </div>`;
                    
                    commentsList.insertAdjacentHTML('beforeend', newCommentHtml);
                }

                // Limpa o textarea
                formElement.querySelector('textarea').value = '';

            } else {
                alert('Erro: ' + (data.message || 'Erro desconhecido'));
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro de conexão.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = originalBtnText;
        });
    }
});
