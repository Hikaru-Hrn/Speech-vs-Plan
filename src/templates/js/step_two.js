(function() {
    const fileInput = document.getElementById('fileInput');
    const dropContainer = document.getElementById('dropContainer');
    const dropMessage = document.getElementById('dropMessage');
    const fileList = document.getElementById('fileList');
    const convertButton = document.querySelector('.buttons-row button:first-child');
    const sendButton = document.querySelector('.buttons-row button:last-child');

    const originalText = dropMessage.textContent;
    let selectedFile = null;

    const loaderContainer = document.createElement('div');
    loaderContainer.id = 'loaderContainer';
    loaderContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        flex-direction: column;
        gap: 20px;
    `;

    const svgLoader = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgLoader.setAttribute('viewBox', '0 0 100 100');
    svgLoader.setAttribute('width', '80');
    svgLoader.setAttribute('height', '80');
    svgLoader.style.cssText = `
        animation: spin 2s linear infinite;
    `;

    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', '50');
    circle.setAttribute('cy', '50');
    circle.setAttribute('r', '35');
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', '#4CAF50');
    circle.setAttribute('stroke-width', '6');
    circle.setAttribute('stroke-linecap', 'round');
    circle.setAttribute('stroke-dasharray', '220');
    circle.setAttribute('stroke-dashoffset', '220');
    circle.style.cssText = `
        animation: drawCircle 1.5s ease-in-out infinite;
    `;

    svgLoader.appendChild(circle);
    loaderContainer.appendChild(svgLoader);

    const loaderText = document.createElement('p');
    loaderText.textContent = 'Конвертирование...';
    loaderText.style.cssText = `
        color: white;
        font-size: 18px;
        font-family: 'Schiffbauer', sans-serif;
        margin: 0;
    `;
    loaderContainer.appendChild(loaderText);

    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes drawCircle {
            0% {
                stroke-dashoffset: 220;
                stroke: #4CAF50;
            }
            50% {
                stroke-dashoffset: 0;
                stroke: #8BC34A;
            }
            100% {
                stroke-dashoffset: -220;
                stroke: #4CAF50;
            }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(loaderContainer);

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
        
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        
        console.log('Выбран файл:', file.name);
    }

    function showLoader() {
        loaderContainer.style.display = 'flex';
    }

    function hideLoader() {
        loaderContainer.style.display = 'none';
    }

    async function convertFiles() {
        if (!selectedFile) {
            alert('Пожалуйста, выберите аудиофайл для конвертации.');
            return;
        }

        showLoader();

        console.log('Конвертация файла:', selectedFile.name);

        try {
            const response = await fetch('/speech-transcribe-request', {
                method: 'POST',
                body: null
            });

            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            const result = await response.json();
            console.log('Ответ от FastAPI:', result);
            alert('Файл успешно загружен!');
            if (result.redirect_url) {
                    window.location.href = result.redirect_url;
            }
            
        } catch (error) {
            console.error('Ошибка при конвертации:', error);
            alert('Произошла ошибка при конвертации');
        } finally {
            hideLoader();
        }
    }

    async function sendFiles() {
        if (!selectedFile) {
            alert('Пожалуйста, выберите аудиофайл для отправки.');
            return;
        }

        console.log('Отправка файла:', selectedFile.name);
        const formdata = new FormData();
        formdata.append('file', selectedFile);

        try {
            const response = await fetch('/save-audiofile', {
                method: 'POST',
                body: formdata
            });

            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            const result = await response.json();
            console.log('Ответ от FastAPI:', result);
        } catch (error) {
            console.error('Ошибка при отправке:', error);
        }
    }

    convertButton.addEventListener('click', convertFiles);
    sendButton.addEventListener('click', sendFiles);

    document.addEventListener('dragleave', function(e) {
        if (e.relatedTarget === null) {
            dropContainer.classList.remove('dragover');
        }
    });

})();