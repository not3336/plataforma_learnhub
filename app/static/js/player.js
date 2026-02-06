// Alterna a visibilidade do formulário de resposta
function toggleReplyForm(id) {
    var form = document.getElementById(id);
    if (!form) return;
    
    // Verifica se está oculto via CSS inline ou classe Bootstrap d-none
    if (form.style.display === "none" || form.classList.contains('d-none')) {
        form.style.display = "block";
        form.classList.remove('d-none');
        // Foca no textarea automaticamente para melhor UX
        const textarea = form.querySelector('textarea');
        if(textarea) textarea.focus();
    } else {
        form.style.display = "none";
    }
}

// Deleta comentário via AJAX e remove do DOM com animação
function deleteComment(commentId) {
    if (!confirm("Tem certeza que deseja excluir este comentário?")) {
        return;
    }

    fetch(`/course/comment/${commentId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const commentElement = document.getElementById(`comment-${commentId}`);
            if (commentElement) {
                // Efeito de Fade Out
                commentElement.style.transition = 'opacity 0.5s ease, margin 0.5s ease';
                commentElement.style.opacity = '0';
                commentElement.style.marginTop = '-20px'; // Colapso suave
                
                setTimeout(() => {
                    commentElement.remove();
                }, 500);
            }
        } else {
            alert("Erro ao excluir: " + (data.message || "Erro desconhecido"));
        }
    })
    .catch(err => {
        console.error("Erro:", err);
        alert("Erro de conexão.");
    });
}

document.addEventListener("DOMContentLoaded", function() {
    
    // --- LÓGICA DE PROGRESSO DO VÍDEO ---
    const video = document.getElementById("videoPlayer");
    
    if (video) {
        const lessonId = video.dataset.lessonId;
        let markedAsComplete = video.dataset.completed === 'true';
        
        video.ontimeupdate = function() {
            if (markedAsComplete) return;

            if (video.duration > 0) {
                const percentage = (video.currentTime / video.duration) * 100;
                
                // Marca como completo aos 80%
                if (percentage >= 80) {
                    markedAsComplete = true; 
                    markLessonComplete(lessonId);
                }
            }
        };
    }

    function markLessonComplete(id) {
        fetch(`/course/lesson/${id}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                // Atualiza o ícone na Sidebar (Troca classes FontAwesome e Bootstrap)
                const icon = document.getElementById(`status-icon-${id}`);
                if(icon) {
                    // Remove estado "não visto"
                    icon.className = ""; 
                    // Adiciona estado "visto" (Check verde)
                    icon.classList.add("fas", "fa-check-circle", "text-success", "fs-5");
                }
                console.log("Progresso salvo.");
            }
        })
        .catch(err => console.error("Erro ao salvar progresso:", err));
    }


    // --- LÓGICA DE COMENTÁRIOS ---

    // 1. Interceptar Envio do Formulário Principal
    const mainCommentForm = document.getElementById('comment-form');
    const commentsList = document.getElementById('comments-list');

    if (mainCommentForm) {
        mainCommentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleCommentSubmit(this, false);
        });
    }

    // 2. Interceptar Envio das Respostas (Event Delegation seria melhor, mas mantendo simples)
    // Nota: Como os formulários já existem na página, o querySelectorAll funciona.
    // Se carregar mais comentários via AJAX depois, precisaria mudar isso.
    const replyForms = document.querySelectorAll('form[action*="/reply"]');
    replyForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            handleCommentSubmit(this, true);
        });
    });

    // Função Genérica de Envio
    function handleCommentSubmit(formElement, isReply) {
        const formData = new FormData(formElement);
        const actionUrl = formElement.action;
        const submitBtn = formElement.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML; // InnerHTML caso tenha ícones

        // UI Loading
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';

        fetch(actionUrl, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                
                // HTML do Badge de Instrutor
                const badgeHtml = data.is_instructor 
                    ? `<span class="badge bg-primary ms-1">Instrutor</span>` 
                    : '';

                if (isReply) {
                    // --- INSERIR RESPOSTA (HTML Bootstrap) ---
                    const parentId = data.parent_id;
                    const replyFormContainer = document.getElementById(`reply-form-${parentId}`);
                    const parentContainer = replyFormContainer.parentElement; // A div .flex-grow-1

                    // Procura o container de respostas. Se não tiver, cria.
                    // A estrutura no HTML é: <div class="ms-4 ps-3 border-start border-3 border-light">
                    let repliesList = parentContainer.querySelector('.border-start');
                    
                    if (!repliesList) {
                        repliesList = document.createElement('div');
                        repliesList.className = 'ms-4 ps-3 border-start border-3 border-light mt-3';
                        parentContainer.appendChild(repliesList);
                    }

                    const newReplyHtml = `
                        <div class="d-flex gap-2 mb-3 mt-3 animate__animated animate__fadeIn" id="comment-${data.comment_id}">
                            <div class="flex-shrink-0">
                                <div class="rounded-circle bg-secondary bg-opacity-25 text-secondary d-flex align-items-center justify-content-center fw-bold" style="width: 30px; height: 30px; font-size: 0.8rem;">
                                    ${data.user_initial}
                                </div>
                            </div>
                            <div class="flex-grow-1">
                                <div class="bg-light p-2 rounded-3 px-3">
                                    <div class="d-flex justify-content-between">
                                        <span class="fw-bold small">
                                            ${data.user_name} ${badgeHtml}
                                        </span>
                                        <button onclick="deleteComment(${data.comment_id})" class="btn btn-link text-danger p-0 ms-2" style="font-size: 0.75rem;">
                                            <i class="fas fa-trash-alt"></i>
                                        </button>
                                    </div>
                                    <p class="mb-0 text-secondary small">${data.content}</p>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    repliesList.insertAdjacentHTML('beforeend', newReplyHtml);
                    toggleReplyForm(`reply-form-${parentId}`); // Fecha o form

                } else {
                    // --- INSERIR COMENTÁRIO PRINCIPAL (HTML Bootstrap) ---
                    // Remove msg de "nenhum comentário" se existir
                    const emptyState = commentsList.querySelector('.text-center.text-muted');
                    if(emptyState) emptyState.remove();

                    const newCommentHtml = `
                    <div class="d-flex gap-3 mb-4 animate__animated animate__fadeIn" id="comment-${data.comment_id}">
                        <div class="flex-shrink-0">
                            <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center fw-bold shadow-sm" style="width: 40px; height: 40px;">
                                ${data.user_initial}
                            </div>
                        </div>
                        
                        <div class="flex-grow-1">
                            <div class="bg-white p-3 rounded-3 shadow-sm border mb-2">
                                <div class="d-flex justify-content-between align-items-start mb-1">
                                    <div>
                                        <span class="fw-bold text-dark">${data.user_name}</span>
                                        ${badgeHtml}
                                    </div>
                                    <small class="text-muted" style="font-size: 0.75rem;">
                                        Agora mesmo
                                    </small>
                                </div>
                                <p class="mb-0 text-secondary" style="white-space: pre-wrap;">${data.content}</p>
                            </div>

                            <div class="d-flex gap-3 ms-2 mb-2">
                                <small class="text-muted fst-italic">Atualize a página para responder a este comentário.</small>
                                <button onclick="deleteComment(${data.comment_id})" class="btn btn-link text-decoration-none p-0 text-danger" style="font-size: 0.85rem;">Excluir</button>
                            </div>
                        </div>
                    </div>`;
                    
                    // Insere no topo ou no final (geralmente topo é melhor para feedback, mas aqui mantivemos o padrão append)
                    commentsList.insertAdjacentHTML('beforeend', newCommentHtml);
                }

                // Limpa textarea
                formElement.querySelector('textarea').value = '';

            } else {
                alert('Erro: ' + (data.message || 'Erro desconhecido'));
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro de conexão ao enviar comentário.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        });
    }
});