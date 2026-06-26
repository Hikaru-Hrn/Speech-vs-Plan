(function() {
            const fileInput = document.getElementById('fileInput');
            const dropContainer = document.getElementById('dropContainer');
            const dropMessage = document.getElementById('dropMessage');
            const fileList = document.getElementById('fileList');

            const originalText = dropMessage.textContent;

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
                    handleFiles(files);
                }
            });

            fileInput.addEventListener('change', function() {
                if (fileInput.files.length > 0) {
                    handleFiles(fileInput.files);
                } else {
                    dropMessage.textContent = originalText;
                    fileList.textContent = '';
                }
            });

            function handleFiles(files) {
                const fileNames = Array.from(files).map(f => f.name);
                fileList.textContent = 'Выбрано: ' + fileNames.join(', ');
                const dataTransfer = new DataTransfer();
                for (let i = 0; i < files.length; i++) {
                    dataTransfer.items.add(files[i]);
                }
                fileInput.files = dataTransfer.files;

                console.log('Загружены файлы:', fileNames);
            }

            document.addEventListener('dragleave', function(e) {
                if (e.relatedTarget === null) {
                    dropContainer.classList.remove('dragover');
                }
            });

        })();