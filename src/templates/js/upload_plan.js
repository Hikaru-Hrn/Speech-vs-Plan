(function() {
    const fileInput = document.getElementById('fileInput');
    const dropContainer = document.getElementById('dropContainer');
    const dropMessage = document.getElementById('dropMessage');
    const fileList = document.getElementById('fileList');
    const sendButton = document.querySelector('.buttons-row button:first-child');
    const backButton = document.querySelector('.buttons-row button:last-child');

    const originalText = dropMessage.textContent;
    let selectedFile = null;

    function openFileDialog() {
        fileInput.click();
    }

    dropContainer.addEventListener('click', openFileDialog);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, preventDefaults, false);
        dropContainer.addEventListener(eventName, preventDefaults, false);
    });

    dropContainer.addEventListener('dragenter', function() {
        dropContainer.classList.add('dragover');
    });

    dropContainer.addEventListener('dragover', function() {
        dropContainer.classList.add('dragover');
    });

    dropContainer.addEventListener('dragleave', function(e) {
        const related = e.relatedTarget;
        if (!dropContainer.contains(related)) {
            dropContainer.classList.remove('dragover');
        }
    });

    dropContainer.addEventListener('drop', function(e) {
        dropContainer.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Берем только первый файл
            const firstFile = files[0];
            storeFile(firstFile);
        }
    });

    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            // Берем только первый файл
            const firstFile = fileInput.files[0];
            storeFile(firstFile);
        } else {
            dropMessage.textContent = originalText;
            fileList.textContent = '';
            selectedFile = null;
        }
    });

    function storeFile(file) {
        selectedFile = file;
        fileList.textContent = 'Выбрано: ' + file.name;
        dropMessage.textContent = 'Файл готов к отправке. Нажмите "Отправить".';
        
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;

        console.log('Выбран файл:', file.name);
    }

    async function sendFiles() {
        if (!selectedFile) {
            alert('Пожалуйста, выберите файл для отправки.');
            return;
        }

        console.log('Отправка файла:', selectedFile.name);
        
        const formdata = new FormData();
        formdata.append('files', selectedFile);

        try {
            const response = await fetch('/upload-plan/save', {
                method: 'POST',
                body: formdata
            });

            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            const result = await response.json();
            console.log('Ответ от FastAPI:', result);
            alert('Файл успешно загружен!');
            
        } catch (error) {
            console.error('Ошибка при отправке:', error);
            alert('Ошибка при загрузке файла. Подробности в консоли.');
        }
    }

    sendButton.addEventListener('click', sendFiles);

    backButton.addEventListener('click', function() {
        window.history.back();
    });

    document.addEventListener('dragleave', function(e) {
        if (e.relatedTarget === null) {
            dropContainer.classList.remove('dragover');
        }
    });

})();