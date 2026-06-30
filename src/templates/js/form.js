let count = 0;
const addStageBtn = document.getElementById('addStageBtn');
const stagesContainer = document.getElementById('stagesContainer');

function renumberStages() {
    const stages = stagesContainer.querySelectorAll('.stage-block');
    stages.forEach((stage, index) => {
        const newNumber = index + 1;
        const title = stage.querySelector('h3');
        if (title) {
            title.textContent = `Пункт ${newNumber}`;
        }
        const inputs = stage.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            const name = input.getAttribute('name');
            if (name) {
                const newName = name.replace(/\d+$/, newNumber);
                input.setAttribute('name', newName);
            }
        });
        const deleteBtn = stage.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.setAttribute('data-stage-id', newNumber);
        }
    });
    count = stages.length;
}

addStageBtn.addEventListener('click', function(){
    count++;
    const block = document.createElement('div');
    block.className = 'stage-block';
    block.innerHTML = `
        <h3>Пункт ${count}</h3>
        <div>
            <label>Описание пункта:</label>
            <textarea name="stageDescription${count}" class="stage-textarea" placeholder="Введите описание пункта"></textarea>
        </div>
        <div class="delete-wrapper">
            <button class="delete-btn" data-stage-id="${count}">Удалить этап</button>
        </div>
    `;
    stagesContainer.appendChild(block);
    
    const deleteBtn = block.querySelector('.delete-btn');
    deleteBtn.addEventListener('click', function(e){
        const stageBlock = this.closest('.stage-block');
        if(stageBlock){
            stageBlock.remove();
            renumberStages();
        }
    });
});

document.getElementById('submitBtn').addEventListener('click', async function() {
    const stages = stagesContainer.querySelectorAll('.stage-block');
    if (stages.length === 0) {
        alert('Добавьте хотя бы один этап!');
        return;
    }
    
    const lecturePlan = [];

    stages.forEach((stage, index) => {
        const stageNum = index + 1;
        const descInput = stage.querySelector(`textarea[name="stageDescription${stageNum}"]`);

        lecturePlan.push({
            stage_number: stageNum,
            description: descInput ? descInput.value.trim() : ''
        });
    });

    const emptyDescriptions = lecturePlan.some(item => item.description === '');
    if (emptyDescriptions) {
        alert('Пожалуйста, заполните описание для всех этапов!');
        return;
    }

    try {
        const response = await fetch('/lectures/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(lecturePlan)
        });

        if (response.ok) {
            const result = await response.json();
            alert(`Успешно! ${result.message || 'План сохранен'}`);
            stagesContainer.innerHTML = '';
            count = 0;
        } else {
            const error = await response.json();
            alert(`Ошибка сервера: ${error.detail || response.status}`);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось связаться с сервером.');
    }
});

document.addEventListener('input', function(e) {
    if (e.target.classList.contains('stage-textarea')) {
        e.target.style.height = 'auto';
        e.target.style.height = e.target.scrollHeight + 'px';
    }
});