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
                    <label>Название пункта:</label>
                    <input type="text" name="stageName${count}" placeholder="Введите название пункта">
                </div>
                <div>
                    <label>Длительность:</label>
                    <input type="text" name="stageTime${count}" placeholder="Введите длительность, например 12:00-12:15">
                </div>
                <div>
                    <label>Описание этапа:</label>
                    <textarea name="stageDescription${count}" placeholder="Введите описание путкта"></textarea>
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
          const nameInput = stage.querySelector(`input[name="stageName${stageNum}"]`);
          const timeInput = stage.querySelector(`input[name="stageTime${stageNum}"]`);
          const descInput = stage.querySelector(`textarea[name="stageDescription${stageNum}"]`);

          lecturePlan.push({
            stage_number: stageNum,
            name: nameInput ? nameInput.value : '',
            time: timeInput ? timeInput.value : '',
            description: descInput ? descInput.value : ''
          });
        });

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
            alert(`Успешно! ${result.message}`);
          } else {
            alert('Ошибка сервера при сохранении.');
          }
        } catch (error) {
          console.error('Ошибка:', error);
          alert('Не удалось связаться с сервером.');
        }
      });