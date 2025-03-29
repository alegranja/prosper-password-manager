document.addEventListener('DOMContentLoaded', function() {
    // Resetar senha
    const resetForm = document.getElementById('resetForm');
    if (resetForm) {
        resetForm.addEventListener('submit', resetPassword);
    }
    
    // Botão de atualizar
    const refreshButton = document.getElementById('refreshButton');
    if (refreshButton) {
        refreshButton.addEventListener('click', refreshData);
    }
    
    // Atualizar o select de fornecedores ao mudar
    const vendorSelect = document.getElementById('vendorSelect');
    if (vendorSelect) {
        vendorSelect.addEventListener('change', updateResetForm);
    }
});

function resetPassword(event) {
    event.preventDefault();
    
    const vendor = document.getElementById('vendorSelect').value;
    const password = document.getElementById('passwordInput').value;
    
    if (!vendor || !password) {
        showAlert('Por favor, preencha todos os campos', 'danger');
        return;
    }
    
    fetch('/reset-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ vendor, password }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Senha resetada com sucesso!', 'success');
            document.getElementById('passwordInput').value = '';
            refreshData();
        } else {
            showAlert(`Erro: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Erro ao comunicar com o servidor', 'danger');
    });
}

function refreshData() {
    fetch('/refresh-sheet')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('Dados atualizados com sucesso!', 'success');
                // Recarregar a página para mostrar os dados atualizados
                window.location.reload();
            } else {
                showAlert(`Erro: ${data.message}`, 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Erro ao comunicar com o servidor', 'danger');
        });
}

function updateResetForm() {
    // Função para futuras melhorias
}

function showAlert(message, type = 'info') {
    // Criar o elemento de alerta
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Adicionar ao topo do card de administração
    const cardBody = document.querySelector('.card-body');
    cardBody.insertBefore(alertDiv, cardBody.firstChild);
    
    // Remover automaticamente após 5 segundos
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}
