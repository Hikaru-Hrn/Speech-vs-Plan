// step_three.js - обновленная версия

(function() {
    const compareButton = document.querySelector('.compare-btn');
    const viewButton = document.querySelector('.buttons-row button:first-child');
    const downloadButton = document.querySelector('.buttons-row button:last-child');
    const readingBlock = document.querySelector('.reading_in_website');

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
    loaderText.textContent = 'Сравнение...';
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

    function showLoader() {
        loaderContainer.style.display = 'flex';
    }

    function hideLoader() {
        loaderContainer.style.display = 'none';
    }

    async function compareData() {
        showLoader();
        console.log('Начинаем сравнение...');

        try {
            const response = await fetch('/gigachat-api-request', {
                method: 'POST',
                body: null
            });

            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }
            const result = await response.json();
            console.log('Ответ от FastAPI:', result);
        } catch (error) {
            console.error('Ошибка при отправке:', error);
        } finally {
            hideLoader();
        }
    }

    function viewInBrowser() {
        if (readingBlock) {
            if (readingBlock.style.display === 'none' || readingBlock.style.display === '') {
                readingBlock.style.display = 'block';
            } else {
                readingBlock.style.display = 'none';
            }
        }
    }

    function downloadFile() {
        console.log('Загружаем файл');
        alert('Функция загрузки файла будет реализована');
    }

    if (compareButton) {
        compareButton.addEventListener('click', compareData);
    }

    if (viewButton) {
        viewButton.addEventListener('click', viewInBrowser);
    }

    if (downloadButton) {
        downloadButton.addEventListener('click', downloadFile);
    }

})();